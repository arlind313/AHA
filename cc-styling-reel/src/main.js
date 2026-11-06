import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Line2 } from 'three/addons/lines/Line2.js';
import { LineGeometry } from 'three/addons/lines/LineGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { createEarth, EARTH_R } from './earth.js';
import { createPlane } from './plane.js';
import { T, LOCATIONS, WIDTH, HEIGHT, DURATION, FPS } from './timeline.js';

const params = new URLSearchParams(location.search);
const RENDER = params.has('render');
const D2R = Math.PI / 180;

// ── helpers ───────────────────────────────────────────────────
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const sstep = x => x * x * (3 - 2 * x);
const smoother = x => x * x * x * (x * (x * 6 - 15) + 10);
const easeOutExpo = x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x);
const easeOutCubic = x => 1 - Math.pow(1 - x, 3);
const easeInOutCubic = x => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const angLerp = (a, b, t) => { let d = ((b - a + 540) % 360) - 180; return a + d * t; };

function unitFromGeo(lat, lon) {
  const la = lat * D2R, lo = lon * D2R;
  return new THREE.Vector3(Math.cos(la) * Math.sin(lo), Math.sin(la), Math.cos(la) * Math.cos(lo));
}
const geo = (lat, lon, alt = 0) => unitFromGeo(lat, lon).multiplyScalar(EARTH_R + alt);
function slerpUnit(a, b, f) {
  const om = a.angleTo(b); if (om < 1e-9) return a.clone();
  const s = Math.sin(om);
  return a.clone().multiplyScalar(Math.sin((1 - f) * om) / s).add(b.clone().multiplyScalar(Math.sin(f * om) / s));
}
function localFrame(p) {
  const up = p.clone().normalize();
  const east = new THREE.Vector3(0, 1, 0).cross(up).normalize();
  const north = up.clone().cross(east).normalize();
  return { up, east, north };
}
function headingOf(pos, dir) {
  const { east, north } = localFrame(pos);
  return Math.atan2(dir.dot(east), dir.dot(north)) / D2R;
}

// ── flight path: Dublin → (banked turn over Marbella) → Dubai ──
const U = { D: unitFromGeo(LOCATIONS.ireland.lat, LOCATIONS.ireland.lon), M: unitFromGeo(LOCATIONS.marbella.lat, LOCATIONS.marbella.lon), X: unitFromGeo(LOCATIONS.dubai.lat, LOCATIONS.dubai.lon) };
const path = (() => {
  const turn = 110 / EARTH_R; // start/finish the turn 110 km either side of Marbella
  const P1 = slerpUnit(U.M, U.D, turn / U.M.angleTo(U.D));
  const P2 = slerpUnit(U.M, U.X, turn / U.M.angleTo(U.X));
  const pts = [];
  const nA = 600, nC = 120, nB = 1400;
  for (let i = 0; i <= nA; i++) pts.push(slerpUnit(U.D, P1, i / nA));
  for (let i = 1; i <= nC; i++) {
    const f = i / nC;
    pts.push(P1.clone().multiplyScalar((1 - f) ** 2).add(U.M.clone().multiplyScalar(2 * (1 - f) * f)).add(P2.clone().multiplyScalar(f * f)).normalize());
  }
  for (let i = 1; i <= nB; i++) pts.push(slerpUnit(P2, U.X, i / nB));
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + pts[i].angleTo(pts[i - 1]) * EARTH_R);
  const total = cum[cum.length - 1];
  const sM = cum[nA] + (cum[nA + nC] - cum[nA]) / 2;
  return { pts, cum, total, sM, sTurn0: cum[nA], sTurn1: cum[nA + nC] };
})();
function unitAt(s) {
  s = clamp(s, 0, path.total);
  let lo = 0, hi = path.cum.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (path.cum[m] <= s) lo = m; else hi = m; }
  const f = (s - path.cum[lo]) / Math.max(1e-6, path.cum[hi] - path.cum[lo]);
  return path.pts[lo].clone().lerp(path.pts[hi], f).normalize();
}
// altitude (km) along the route — cinematic scale, not literal
const ALT_KEYS = [[0, 45], [520, 120], [path.sM - 520, 115], [path.sM, 62], [path.sM + 650, 135], [path.total - 1100, 135], [path.total, 10]];
function altAt(s) {
  if (s <= ALT_KEYS[0][0]) return ALT_KEYS[0][1];
  for (let i = 1; i < ALT_KEYS.length; i++) if (s <= ALT_KEYS[i][0]) {
    const [s0, a0] = ALT_KEYS[i - 1], [s1, a1] = ALT_KEYS[i];
    return lerp(a0, a1, smoother((s - s0) / (s1 - s0)));
  }
  return ALT_KEYS[ALT_KEYS.length - 1][1];
}
const posAt = s => unitAt(s).multiplyScalar(EARTH_R + altAt(s));
// distance travelled vs time — Hermite keys (t, s, ds/dt)
const S_KEYS = [
  { t: T.takeoff, s: 0, v: 0 },
  { t: 6.35, s: path.sM - 70, v: 170 },
  { t: 7.95, s: path.sM + 170, v: 190 },
  { t: 13.35, s: path.total - 25, v: 110 },
  { t: T.arriveDubai, s: path.total, v: 0 },
];
function sAt(t) {
  if (t <= S_KEYS[0].t) return 0;
  for (let i = 1; i < S_KEYS.length; i++) if (t <= S_KEYS[i].t) {
    const a = S_KEYS[i - 1], b = S_KEYS[i], h = b.t - a.t, x = (t - a.t) / h;
    const h00 = 2 * x ** 3 - 3 * x ** 2 + 1, h10 = x ** 3 - 2 * x ** 2 + x, h01 = -2 * x ** 3 + 3 * x ** 2, h11 = x ** 3 - x ** 2;
    return h00 * a.s + h10 * h * a.v + h01 * b.s + h11 * h * b.v;
  }
  return path.total;
}
function planeState(t) {
  const s = sAt(t), ds = 6;
  const pos = posAt(s);
  const sa = clamp(s - ds, 0, path.total), sb = clamp(s + ds, 0, path.total);
  const fwd = posAt(sb).sub(posAt(sa === sb ? sa - ds : sa)).normalize();
  const hd = headingOf(pos, fwd);
  // bank from rate of turn
  const e = 0.05, h0 = headingOf(posAt(sAt(t - e)), posAt(sAt(t - e) + ds).sub(posAt(sAt(t - e) - ds)));
  const h1 = headingOf(posAt(sAt(t + e)), posAt(sAt(t + e) + ds).sub(posAt(sAt(t + e) - ds)));
  const turnRate = (((h1 - h0 + 540) % 360) - 180) / (2 * e);
  const bank = clamp(turnRate * 0.55, -38, 38) * D2R * clamp((s - 1) / 50);
  return { s, pos, fwd, heading: hd, bank };
}
function orientFromBasis(fwd, upHint, roll = 0) {
  const x = upHint.clone().cross(fwd).normalize();
  const y = fwd.clone().cross(x).normalize();
  const m = new THREE.Matrix4().makeBasis(x, y, fwd);
  const q = new THREE.Quaternion().setFromRotationMatrix(m);
  return q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), roll));
}

// ── camera choreography ───────────────────────────────────────
const PLANE_LEN = 80; // km (cinematic scale)
const H = { ire: geo(LOCATIONS.ireland.lat, LOCATIONS.ireland.lon), mar: geo(LOCATIONS.marbella.lat, LOCATIONS.marbella.lon), dxb: geo(LOCATIONS.dubai.lat, LOCATIONS.dubai.lon) };
const FINAL = { lat: Number(params.get('flat') || 28.2), lon: Number(params.get('flon') || 30.6), dist: Number(params.get('fdist') || 20700), az: Number(params.get('faz') || -12), el: Number(params.get('fel') || 78) };
const WIDE_TARGET = geo(FINAL.lat, FINAL.lon);

const shots = [
  { // 0 — Europe at night → push in to Ireland
    t0: 0, t1: 2.45,
    f: t => {
      const k = easeInOutCubic(prog(t, 0, 2.2));
      return { target: geo(lerp(48.5, LOCATIONS.ireland.lat - 0.25, k), lerp(9, LOCATIONS.ireland.lon, k)), dist: Math.exp(lerp(Math.log(6800), Math.log(1050), k)), az: lerp(-8, 6, k), el: lerp(68, 52, k), lift: 0 };
    },
  },
  { // 1 — chase out of Ireland towards Spain
    t0: 2.45, t1: 6.1,
    f: (t, P) => {
      const k = easeInOutCubic(prog(t, 2.45, 4.1));
      return { target: P.pos, dist: lerp(560, 330, k), az: P.heading - lerp(10, 32, k), el: lerp(44, 30, k), lift: 18 };
    },
  },
  { // 2 — orbit around the aircraft over Marbella
    t0: 6.1, t1: 8.05,
    f: (t, P) => {
      const k = easeInOutCubic(prog(t, T.orbitStart - 0.1, T.orbitEnd));
      return { target: P.pos, dist: lerp(330, 270, Math.sin(k * Math.PI)) , az: P.heading - lerp(32, 112, k), el: lerp(30, 33, k) + 3 * Math.sin(k * Math.PI), lift: 14 };
    },
  },
  { // 3 — accelerating chase across the Mediterranean & Middle East
    t0: 8.05, t1: 12.25,
    f: (t, P) => {
      const k = easeInOutCubic(prog(t, 8.0, 10.2));
      return { target: P.pos, dist: lerp(290, 400, k), az: P.heading - lerp(112, 58, k), el: lerp(33, 27, k), lift: 22 };
    },
  },
  { // 4 — Dubai reveal
    t0: 12.25, t1: 14.0,
    f: (t, P) => {
      const k = easeInOutCubic(prog(t, 12.0, 13.9));
      const tgt = P.pos.clone().lerp(H.dxb, k * 0.85);
      return { target: tgt, dist: lerp(400, 900, k), az: lerp(P.heading - 58, 52, k), el: lerp(27, 30, k), lift: lerp(22, 60, k) };
    },
  },
  { // 5 — pull back: all three locations
    t0: 14.0, t1: 99,
    f: t => {
      const k = easeInOutCubic(prog(t, 14.0, 16.4));
      const drift = prog(t, 16.4, 20);
      const tgt = H.dxb.clone().lerp(WIDE_TARGET, k);
      return { target: tgt, dist: Math.exp(lerp(Math.log(900), Math.log(FINAL.dist), k)) * (1 - 0.03 * drift), az: lerp(52, FINAL.az, k) + drift * 2, el: lerp(30, FINAL.el, k), lift: 0 };
    },
  },
];
const XFADE = { 1: 0.9, 2: 0.6, 3: 0.7, 4: 0.9, 5: 0 };
function blendPose(a, b, k) {
  return { target: a.target.clone().lerp(b.target, k), dist: Math.exp(lerp(Math.log(a.dist), Math.log(b.dist), k)), az: angLerp(a.az, b.az, k), el: lerp(a.el, b.el, k), lift: lerp(a.lift, b.lift, k) };
}
function cameraPose(t, P) {
  let i = shots.findIndex(s => t >= s.t0 && t < s.t1); if (i < 0) i = shots.length - 1;
  let pose = shots[i].f(t, P);
  const xf = XFADE[i];
  if (i > 0 && xf && t < shots[i].t0 + xf) {
    const prev = shots[i - 1].f(t, P);
    pose = blendPose(prev, pose, smoother(prog(t, shots[i].t0, shots[i].t0 + xf)));
  }
  return pose;
}
function applyPose(cam, pose) {
  const { up, east, north } = localFrame(pose.target);
  const h = north.clone().multiplyScalar(Math.cos(pose.az * D2R)).add(east.clone().multiplyScalar(Math.sin(pose.az * D2R)));
  const el = pose.el * D2R;
  const look = pose.target.clone().add(up.clone().multiplyScalar(pose.lift));
  cam.position.copy(look).sub(h.clone().multiplyScalar(pose.dist * Math.cos(el))).add(up.clone().multiplyScalar(pose.dist * Math.sin(el)));
  cam.up.copy(up);
  cam.lookAt(look);
  cam.near = clamp(pose.dist * 0.02, 1, 60); cam.far = pose.dist + EARTH_R * 2.5;
  cam.updateProjectionMatrix();
  cam.updateMatrixWorld(true);
}

// ── boot ──────────────────────────────────────────────────────
const stage = document.getElementById('stage');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(WIDTH, HEIGHT, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
stage.prepend(renderer.domElement);
renderer.domElement.id = 'gl';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x02040a);
const camera = new THREE.PerspectiveCamera(38, WIDTH / HEIGHT, 1, 50000);
scene.add(camera);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.3;

const moon = new THREE.DirectionalLight(0xdfe8ff, 1.35); scene.add(moon); scene.add(moon.target);
const rim = new THREE.DirectionalLight(0xffb36b, 0.7); scene.add(rim); scene.add(rim.target);
const hemi = new THREE.HemisphereLight(0x3a4c70, 0x5a3412, 0.45); scene.add(hemi);

const loader = new THREE.TextureLoader();
const loadTex = (u, srgb) => new Promise(r => loader.load(u, t => { if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; r(t); }));
const loadImg = u => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = u; });

const [night, day, topo, water, detail, detailInfo, logoImg] = await Promise.all([
  loadTex('assets/earth-night.jpg', true), loadTex('assets/earth-blue-marble.jpg', true), loadTex('assets/earth-topology.png'),
  loadTex('assets/earth-water.png'), loadTex('assets/detail.png'), fetch('assets/detail.json').then(r => r.json()), loadImg('assets/logo.png'),
  document.fonts.load('900 italic 100px Montserrat'), document.fonts.load('800 italic 100px Montserrat'), document.fonts.load('600 40px Montserrat'), document.fonts.load('500 40px Montserrat'),
]);
detail.generateMipmaps = true; detail.minFilter = THREE.LinearMipmapLinearFilter;

const earth = createEarth({ night, day, topo, water, detail }, detailInfo);
scene.add(earth);

const plane = createPlane(logoImg);
plane.scale.setScalar(PLANE_LEN);
scene.add(plane);
const flyby = createPlane(logoImg);
camera.add(flyby);

// route lines
const ROUTE_N = 1600;
const routePos = [];
for (let i = 0; i <= ROUTE_N; i++) { const p = posAt(path.total * i / ROUTE_N); routePos.push(p.x, p.y, p.z); }
function makeLine(width, color, opacity, additive) {
  const g = new LineGeometry(); g.setPositions(routePos);
  const m = new LineMaterial({ color, linewidth: width, transparent: true, opacity, depthWrite: !additive, blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending, worldUnits: false });
  m.resolution.set(WIDTH, HEIGHT);
  const l = new Line2(g, m); l.computeLineDistances(); l.frustumCulled = false; scene.add(l); return l;
}
const routeGlow = makeLine(16, 0xe30613, 0.22, true);
const routeCore = makeLine(3.6, 0xff3b2a, 1.0, false);
const routeHot = makeLine(1.4, 0xffd2c8, 0.85, true);

// ground pulse rings at each location
function makeRings(p) {
  const g = new THREE.Group();
  const { up, east, north } = localFrame(p);
  g.position.copy(p.clone().add(up.clone().multiplyScalar(2)));
  g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(east, north, up));
  const rings = [];
  for (let i = 0; i < 3; i++) {
    const m = new THREE.Mesh(new THREE.RingGeometry(0.86, 1, 96), new THREE.MeshBasicMaterial({ color: 0xff2414, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    g.add(m); rings.push(m);
  }
  const disc = new THREE.Mesh(new THREE.CircleGeometry(1, 64), new THREE.MeshBasicMaterial({ color: 0xff3020, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  g.add(disc);
  scene.add(g);
  return { g, rings, disc, p };
}
const ringSets = { ireland: makeRings(H.ire), marbella: makeRings(H.mar), dubai: makeRings(H.dxb) };

// composer
const rt = new THREE.WebGLRenderTarget(WIDTH, HEIGHT, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(1); composer.setSize(WIDTH, HEIGHT);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(WIDTH, HEIGHT), 0.42, 0.5, 0.88);
composer.addPass(bloom);
composer.addPass(new OutputPass());

// ── DOM overlay refs ──────────────────────────────────────────
const $ = id => document.getElementById(id);
const pins = { ireland: $('pin-ireland'), marbella: $('pin-marbella'), dubai: $('pin-dubai') };
const labels = { ireland: $('lab-ireland'), marbella: $('lab-marbella'), dubai: $('lab-dubai') };
const card = { el: $('card'), idx: $('card-idx'), name: $('card-name'), rule: $('card-rule'), sub: $('card-sub') };
const burj = $('burj');

function project(p) {
  const v = p.clone().project(camera);
  const toCam = camera.position.clone().sub(p);
  const visible = toCam.dot(p.clone().normalize()) > 0 && v.z < 1;
  return { x: (v.x + 1) / 2 * WIDTH, y: (1 - v.y) / 2 * HEIGHT, visible };
}

const CARDS = [
  { key: 'ireland', i: '01', tin: T.irelandTitleIn, tout: T.irelandTitleOut },
  { key: 'marbella', i: '02', tin: T.marbellaTitleIn, tout: T.marbellaTitleOut },
  { key: 'dubai', i: '03', tin: T.dubaiTitleIn, tout: T.dubaiTitleOut },
];
function updateCard(t) {
  const c = CARDS.find(c => t >= c.tin - 0.01 && t < c.tout + 0.45);
  if (!c) { card.el.style.opacity = 0; return; }
  const L = LOCATIONS[c.key];
  if (card.name.textContent !== L.name) { card.name.textContent = L.name; card.sub.textContent = L.sub; card.idx.innerHTML = `<b>${c.i}</b><span>/ 03</span>`; }
  const a = easeOutExpo(prog(t, c.tin, c.tin + 0.75));
  const b = easeOutExpo(prog(t, c.tin + 0.18, c.tin + 0.95));
  const r = easeOutCubic(prog(t, c.tin + 0.05, c.tin + 0.6));
  const o = 1 - easeInOutCubic(prog(t, c.tout, c.tout + 0.4));
  card.el.style.opacity = o;
  card.el.style.transform = `translateY(${-24 * (1 - o)}px)`;
  card.name.style.clipPath = `inset(-20% ${100 - a * 100}% -20% 0)`;
  card.name.style.transform = `translateX(${(1 - a) * -26}px)`;
  card.rule.style.transform = `skewX(-20deg) scaleX(${r})`;
  card.sub.style.opacity = b; card.sub.style.letterSpacing = `${lerp(0.62, 0.42, b)}em`;
  card.idx.style.opacity = r;
}

const LABEL_POS = { ireland: [34, -40], marbella: [-110, 22], dubai: [-60, 24] };
function updateMarkers(t, camDist) {
  const pinT = { ireland: T.irelandPin, marbella: T.marbellaPin, dubai: T.dubaiPin };
  for (const k of Object.keys(pins)) {
    const pr = project(ringSets[k].p);
    const a = prog(t, pinT[k], pinT[k] + 0.55);
    const pop = a <= 0 ? 0 : 1 + 0.18 * Math.sin(a * Math.PI) * (1 - a) * 2.2;
    const wide = smoother(prog(t, T.pullBack, T.pullBack + 2.2));
    const size = lerp(1, 0.72, wide);
    const el = pins[k];
    el.style.opacity = pr.visible ? sstep(clamp(a * 2.5)) : 0;
    el.style.transform = `translate(${pr.x}px, ${pr.y}px) scale(${pop * size})`;
    // label (final wide shot)
    const la = smoother(prog(t, T.mapLabels + (k === 'marbella' ? 0.15 : k === 'dubai' ? 0.3 : 0), T.mapLabels + 0.8 + (k === 'marbella' ? 0.15 : k === 'dubai' ? 0.3 : 0)));
    const lb = labels[k]; const [ox, oy] = LABEL_POS[k];
    lb.style.opacity = pr.visible ? la : 0;
    lb.style.transform = `translate(${pr.x + ox}px, ${pr.y + oy + (1 - la) * 14}px)`;
    // ground rings: scale with camera distance so they read at every zoom
    const R = ringSets[k];
    const base = clamp(camDist * 0.04, 10, 380) * (k === 'dubai' ? 1.15 : 1);
    R.rings.forEach((m, i) => {
      const life = t - pinT[k] - i * 0.42;
      if (life < 0) { m.material.opacity = 0; return; }
      const ph = (life % 1.6) / 1.6;
      const burst = k === 'dubai' && i === 0 && life < 1.6 ? 1.0 : 0; // one larger shockwave on the Dubai reveal
      m.scale.setScalar(base * (0.25 + ph * (1.3 + burst * 2.2)));
      m.material.opacity = Math.pow(1 - ph, 1.6) * 0.75;
    });
    R.disc.scale.setScalar(base * 0.22);
    R.disc.material.opacity = clamp(a * 2) * 0.55;
  }
}

function updateBurj(t) {
  const a = smoother(prog(t, T.burjIn, T.burjIn + 0.9)) * (1 - smoother(prog(t, T.burjOut - 0.4, T.burjOut)));
  const pr = project(H.dxb);
  burj.style.opacity = pr.visible ? a * 0.6 : 0;
  burj.style.transform = `translate(${pr.x + 46}px, ${pr.y + 6}px) translate(0, -100%) scaleY(${lerp(0.94, 1, a)})`;
  $('burj-tip').style.opacity = ((t * 1.3) % 1) < 0.5 ? 1 : 0.25;
}

function updateFinal(t) {
  const scrim = smoother(prog(t, 14.6, 15.8));
  $('scrim').style.opacity = scrim;
  const l1 = easeOutExpo(prog(t, T.line1, T.line1 + 0.9));
  $('line1').style.clipPath = `inset(-30% ${100 - l1 * 100}% -30% 0)`;
  $('line1').style.transform = `translateX(-50%) scale(${lerp(1.06, 1, l1)})`;
  $('line1').style.opacity = clamp(l1 * 3);
  const l2 = easeOutExpo(prog(t, T.line2, T.line2 + 0.9));
  $('line2').style.clipPath = `inset(-30% ${100 - l2 * 100}% -30% 0)`;
  $('line2').style.transform = `translateX(-50%) scale(${lerp(1.08, 1, l2)})`;
  $('line2').style.opacity = clamp(l2 * 3);
  const glow = Math.exp(-Math.pow((t - T.line2 - 0.45) / 0.5, 2));
  $('line2').style.textShadow = `0 0 ${18 + 30 * glow}px rgba(227,6,19,${0.35 + 0.35 * glow})`;
  const lg = easeOutExpo(prog(t, T.logo, T.logo + 1.1));
  $('logo').style.clipPath = `inset(-10% ${100 - lg * 100}% -10% 0)`;
  $('logo').style.opacity = clamp(lg * 2.5);
  const ll = easeOutCubic(prog(t, T.locationsLine, T.locationsLine + 1.0));
  $('locline').style.opacity = ll;
  $('locline').style.letterSpacing = `${lerp(0.55, 0.32, ll)}em`;
  $('topscrim').style.opacity = smoother(prog(t, T.logo - 0.4, T.logo + 0.6));
}

// opening fade-in + vignette
function updateGlobalFx(t) {
  $('fade').style.opacity = 1 - smoother(prog(t, 0, 0.6));
}

const tmpV = new THREE.Vector3();
function setFlyby(t) {
  const k = prog(t, T.flybyStart, T.flybyEnd);
  flyby.visible = k > 0 && k < 1;
  if (!flyby.visible) return;
  const d = 2600;
  const vh = Math.tan(camera.fov * D2R / 2) * d, vw = vh * camera.aspect;
  const e = lerp(0, 1, k * 0.86 + 0.14 * smoother(k));
  const p0 = new THREE.Vector3(-1.9 * vw, -0.78 * vh, -d * 1.05), p1 = new THREE.Vector3(1.9 * vw, 0.28 * vh, -d * 0.85);
  flyby.position.copy(p0).lerp(p1, e);
  const fwd = p1.clone().sub(p0).normalize().add(new THREE.Vector3(0, 0, 0.18)).normalize();
  const upH = new THREE.Vector3(0, Math.cos(0.75), Math.sin(0.75));
  flyby.quaternion.copy(orientFromBasis(fwd, upH, 0.22));
  flyby.scale.setScalar(vw * 1.15);
  flyby.userData.update(t, 1);
}

// ── frame renderer (deterministic: everything is a pure function of t) ──
function renderAt(t) {
  const P = planeState(t);
  // aircraft
  const upHint = P.pos.clone().normalize();
  plane.position.copy(P.pos);
  plane.quaternion.copy(orientFromBasis(P.fwd, upHint, P.bank));
  const power = smoother(prog(t, T.lightsOn, T.lightsOn + 0.5));
  plane.userData.update(t, power);
  plane.userData.setOpacity(smoother(prog(t, T.planeAppear, T.planeAppear + 0.7)));
  plane.visible = t < T.pullBack + 1.2;
  const fadeMain = 1 - prog(t, T.pullBack, T.pullBack + 1.2);
  plane.scale.setScalar(PLANE_LEN * Math.max(0.001, fadeMain));

  const pose = cameraPose(t, P);
  applyPose(camera, pose);
  setFlyby(t);

  // key light: high & to the side of camera (moonlight), warm rim from below/behind
  const camR = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const camU = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  const camF = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  moon.target.position.copy(P.pos); moon.position.copy(P.pos).add(camR.clone().multiplyScalar(-0.6).add(camU.clone().multiplyScalar(1.0)).add(camF.clone().multiplyScalar(-0.5)).multiplyScalar(500));
  rim.target.position.copy(P.pos); rim.position.copy(P.pos).add(camR.clone().multiplyScalar(0.8).add(camU.clone().multiplyScalar(-0.4)).add(camF.clone().multiplyScalar(1.0)).multiplyScalar(500));

  // route reveal follows the aircraft exactly
  const n = Math.floor(clamp(P.s / path.total) * ROUTE_N);
  for (const l of [routeGlow, routeCore, routeHot]) { l.geometry.instanceCount = n; l.visible = n > 0; }

  earth.userData.cloudMat.uniforms.uTime.value = t;
  earth.userData.cloudMat.uniforms.uOpacity.value = smoother(prog(pose.dist, 900, 3500)) * (1 - 0.5 * smoother(prog(t, 14, 16)));

  updateMarkers(t, pose.dist);
  updateCard(t);
  updateBurj(t);
  updateFinal(t);
  updateGlobalFx(t);
  composer.render();
}

window.renderAt = renderAt;
// look-dev helper: where do the three pins land in the final frame for a given final-camera setup?
window.__projectFinal = o => {
  Object.assign(FINAL, o); WIDE_TARGET.copy(geo(FINAL.lat, FINAL.lon));
  const P = planeState(19.5); applyPose(camera, cameraPose(19.5, P));
  return Object.fromEntries(Object.entries(ringSets).map(([k, r]) => { const q = project(r.p); return [k, [q.x, q.y, q.visible]]; }));
};
window.__meta = { FPS, DURATION, WIDTH, HEIGHT };
window.__ready = true;

// ── interactive preview ───────────────────────────────────────
if (!RENDER) {
  document.body.classList.add('preview');
  const audio = $('audio'), scrub = $('scrub'), btn = $('play'), tc = $('tc');
  let playing = false, t0 = performance.now(), tStart = Number(params.get('t') || 0);
  const now = () => playing ? (audio.duration ? audio.currentTime : tStart + (performance.now() - t0) / 1000) : tStart;
  btn.onclick = () => {
    playing = !playing; btn.textContent = playing ? '❚❚ Pause' : '▶ Play with sound';
    if (playing) { if (tStart >= DURATION - 0.05) tStart = 0; audio.currentTime = tStart; audio.play().catch(() => {}); t0 = performance.now(); }
    else { tStart = now(); audio.pause(); }
  };
  scrub.oninput = () => { tStart = Number(scrub.value); if (playing) { audio.currentTime = tStart; t0 = performance.now(); } };
  window.addEventListener('keydown', e => { if (e.code === 'Space') { e.preventDefault(); btn.click(); } });
  const fit = () => { const s = Math.min((innerHeight - 70) / HEIGHT, innerWidth / WIDTH); stage.style.transform = `scale(${s})`; $('wrap').style.width = WIDTH * s + 'px'; $('wrap').style.height = HEIGHT * s + 'px'; };
  addEventListener('resize', fit); fit();
  const loop = () => {
    let t = now();
    if (t >= DURATION) { t = DURATION - 1 / FPS; if (playing) btn.click(); tStart = 0; }
    renderAt(t); scrub.value = t; tc.textContent = t.toFixed(2) + 's';
    requestAnimationFrame(loop);
  };
  loop();
}
