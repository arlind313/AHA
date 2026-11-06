// Procedural white twin-engine airliner with CC Styling livery.
// Model space: nose → +Z, up → +Y, length = 1 unit, left wing → +X.
import * as THREE from 'three';

const RED = new THREE.Color('#E30613');
const R = 0.052;           // fuselage radius
const ZN = 0.36, ZT = -0.2; // start of nose / tail taper

function radiusAt(z) {
  if (z > ZN) { const k = (z - ZN) / (0.5 - ZN); return R * Math.sqrt(Math.max(0, 1 - k * k)); }
  if (z < ZT) { const k = (ZT - z) / (ZT + 0.5); const s = k * k * (3 - 2 * k); return R * (1 - 0.86 * s); }
  return R;
}
function centerLift(z) {
  const r = radiusAt(z);
  if (z < ZT) return (R - r) * 0.9;        // tail upsweep: belly rises, roofline stays straight
  if (z > ZN) return -(R - r) * 0.28;      // slight nose droop
  return 0;
}

/** Dark-on-light variant of the supplied logo for the white fuselage (shapes untouched). */
function logoVariant(img, { fromX = 0, toX = 1, white = '#141518' } = {}) {
  const sx = Math.round(img.width * fromX), sw = Math.round(img.width * (toX - fromX));
  const c = document.createElement('canvas'); c.width = sw; c.height = img.height;
  const g = c.getContext('2d'); g.drawImage(img, sx, 0, sw, img.height, 0, 0, sw, img.height);
  if (white) {
    const d = g.getImageData(0, 0, sw, img.height), p = d.data, w = new THREE.Color(white);
    for (let i = 0; i < p.length; i += 4) {
      const isRed = p[i] > 150 && p[i + 1] < 90;
      if (!isRed) { p[i] = w.r * 255; p[i + 1] = w.g * 255; p[i + 2] = w.b * 255; }
    }
    g.putImageData(d, 0, 0);
  }
  return c;
}

function liveryTexture(logo) {
  const W = 2048, H = 4096;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  // u (x) = angle around fuselage: 0 belly, .25 left side, .5 roof, .75 right side.  v (y) = 1-(z+.5)
  const X = u => u * W, Y = z => (1 - (z + 0.5)) * H;
  const grd = g.createLinearGradient(0, 0, W, 0);
  grd.addColorStop(0, '#9da3ab'); grd.addColorStop(0.12, '#e9ebee'); grd.addColorStop(0.2, '#f6f7f9');
  grd.addColorStop(0.8, '#f6f7f9'); grd.addColorStop(0.88, '#e9ebee'); grd.addColorStop(1, '#9da3ab');
  g.fillStyle = grd; g.fillRect(0, 0, W, H);

  const circ = 2 * Math.PI * R;
  for (const side of [0.25, 0.75]) {
    const dir = side < 0.5 ? 1 : -1; // +u is "up" on the left side, "down" on the right side
    // red speed-line (cheatline) low on the fuselage, tapering towards the nose
    g.fillStyle = '#E30613';
    g.beginPath();
    const uLow = side - dir * 0.072;
    g.moveTo(X(uLow), Y(-0.43));
    g.lineTo(X(uLow + dir * 0.022), Y(-0.43));
    g.lineTo(X(uLow + dir * 0.006), Y(0.33));
    g.lineTo(X(uLow), Y(0.33));
    g.closePath(); g.fill();
    // thin dark pinstripe above it
    g.fillStyle = '#1b1c20';
    g.fillRect(Math.min(X(uLow + dir * 0.03), X(uLow + dir * 0.034)), Y(0.25), Math.abs(X(0.004)), Y(-0.38) - Y(0.25));
    // passenger windows
    const uw = side + dir * 0.045, wh = 0.011 / circ, ww = 0.0062;
    g.fillStyle = '#16181d';
    for (let z = -0.31; z < 0.3; z += 0.0128) {
      if (Math.abs(z - 0.27) < 0.01 || Math.abs(z + 0.02) < 0.012 || Math.abs(z + 0.27) < 0.01) continue; // doors
      const x0 = X(uw - wh / 2), y0 = Y(z + ww / 2);
      g.beginPath(); g.roundRect(x0, y0, X(wh), Y(-0.5 + ww) - Y(-0.5), 10); g.fill();
    }
    // door outlines
    g.strokeStyle = 'rgba(40,44,52,0.55)'; g.lineWidth = 4;
    for (const zd of [0.275, -0.02, -0.27]) {
      g.beginPath(); g.roundRect(X(side + dir * 0.052 - 0.035), Y(zd + 0.007), X(0.07), Y(-0.5) - Y(-0.486), 12); g.stroke();
    }
    // logo along the fuselage
    const L = 0.3, h = L * logo.height / logo.width; // world units
    const uc = side + dir * 0.004, zc = 0.02;
    g.save();
    g.translate(X(uc), Y(zc));
    g.rotate(dir > 0 ? Math.PI / 2 : -Math.PI / 2);
    // after rotation: text x-axis runs along the fuselage, text y-axis around it
    const lenPx = Y(-0.5) - Y(-0.5 + L), hPx = X(h / circ);
    g.drawImage(logo, -lenPx / 2, -hPx / 2, lenPx, hPx);
    g.restore();
  }
  // cockpit windscreen
  g.fillStyle = '#0f1115';
  for (const [u0, u1] of [[0.335, 0.405], [0.415, 0.485], [0.515, 0.585], [0.595, 0.665]]) {
    g.beginPath();
    g.moveTo(X(u0), Y(0.423)); g.lineTo(X(u1), Y(0.428)); g.lineTo(X(u1 - 0.004), Y(0.447)); g.lineTo(X(u0 + 0.008), Y(0.442));
    g.closePath(); g.fill();
  }
  // red nose-tip accent ring
  g.fillStyle = '#E30613'; g.fillRect(0, Y(0.5), W, Y(0.493) - Y(0.5));
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  return tex;
}

function shapeGeo(points, depth) {
  const s = new THREE.Shape(points.map(([a, b]) => new THREE.Vector2(a, b)));
  const geo = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: true, bevelThickness: depth * 0.4, bevelSize: depth * 0.35, bevelSegments: 2 });
  geo.translate(0, 0, -depth / 2);
  return geo;
}

function glowSprite(color, size) {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.18, 'rgba(255,255,255,0.75)');
  gr.addColorStop(0.45, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c);
  const m = new THREE.SpriteMaterial({ map: tex, color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
  const s = new THREE.Sprite(m); s.scale.setScalar(size); return s;
}

export function createPlane(logoImg) {
  const root = new THREE.Group();
  const body = new THREE.Group(); root.add(body);

  const darkLogo = logoVariant(logoImg);
  const whiteCC = logoVariant(logoImg, { fromX: 0, toX: 0.255, white: null });

  const white = new THREE.MeshPhysicalMaterial({ color: 0xe6e7ea, map: liveryTexture(darkLogo), roughness: 0.32, metalness: 0.05, clearcoat: 0.5, clearcoatRoughness: 0.2 });
  const wingMat = new THREE.MeshPhysicalMaterial({ color: 0xd4d8de, roughness: 0.38, metalness: 0.35, clearcoat: 0.4 });
  const redMat = new THREE.MeshPhysicalMaterial({ color: RED, roughness: 0.3, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.12 });
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x0b0c0f, roughness: 0.5, metalness: 0.6 });
  const metal = new THREE.MeshStandardMaterial({ color: 0x9aa0a8, roughness: 0.25, metalness: 0.9 });

  // fuselage
  const N = 160, pts = [];
  for (let j = 0; j <= N; j++) { const z = -0.5 + j / N; pts.push(new THREE.Vector2(Math.max(radiusAt(z), j === N ? 0 : 0.0005), z)); }
  const fus = new THREE.LatheGeometry(pts, 96);
  fus.rotateX(Math.PI / 2);
  const p = fus.attributes.position;
  for (let i = 0; i < p.count; i++) p.setY(i, p.getY(i) + centerLift(p.getZ(i)));
  fus.computeVertexNormals();
  body.add(new THREE.Mesh(fus, white));

  // wings (shape drawn in X/Z plan view, thickness along Y)
  const wingPlan = [[0.03, 0.115], [0.47, -0.135], [0.475, -0.178], [0.41, -0.18], [0.03, -0.075]];
  for (const s of [1, -1]) {
    const geo = shapeGeo(wingPlan.map(([x, z]) => [x * s, z]), 0.008);
    geo.rotateX(Math.PI / 2);
    const m = new THREE.Mesh(geo, wingMat);
    m.position.set(0, -0.03, 0); m.rotation.z = s * 0.075;
    body.add(m);
    // red winglet
    const wl = shapeGeo([[0, 0], [0.028, 0], [0.055, 0.062], [0.04, 0.064]], 0.004);
    wl.rotateY(Math.PI / 2);
    const wlm = new THREE.Mesh(wl, redMat);
    wlm.position.set(0.471 * s, 0.006, -0.143 + 0.0); wlm.rotation.z = -s * 0.12; wlm.rotation.y = 0;
    wlm.position.y = -0.03 + 0.471 * Math.tan(0.075) + 0.004;
    wlm.position.z = -0.135;
    wlm.scale.z = -1;
    m.parent.add(wlm);
    // horizontal stabiliser
    const hs = shapeGeo([[0.012, -0.36], [0.18, -0.46], [0.18, -0.49], [0.105, -0.495], [0.012, -0.455]].map(([x, z]) => [x * s, z]), 0.005);
    hs.rotateX(Math.PI / 2);
    const hm = new THREE.Mesh(hs, wingMat); hm.position.y = 0.035; hm.rotation.z = s * 0.1; body.add(hm);
    // engine nacelle
    const prof = [];
    for (let k = 0; k <= 24; k++) {
      const t = k / 24, z = -0.085 + 0.17 * t;
      let r = 0.0335 - 0.009 * Math.pow(1 - t, 2);
      if (t > 0.9) r -= (t - 0.9) * 0.05;
      prof.push(new THREE.Vector2(r, z));
    }
    const nac = new THREE.LatheGeometry(prof, 48); nac.rotateX(Math.PI / 2);
    const eng = new THREE.Group(); eng.position.set(0.175 * s, -0.062, 0.095);
    eng.add(new THREE.Mesh(nac, white));
    const lip = new THREE.Mesh(new THREE.TorusGeometry(0.0305, 0.0045, 12, 48), redMat); lip.position.z = 0.085; eng.add(lip);
    const intake = new THREE.Mesh(new THREE.CircleGeometry(0.029, 40), darkMat); intake.position.z = 0.078; eng.add(intake);
    // fan blades (spin when engines run)
    const fan = new THREE.Group(); fan.position.z = 0.08;
    for (let b = 0; b < 18; b++) {
      const bl = new THREE.Mesh(new THREE.BoxGeometry(0.0045, 0.026, 0.002), metal);
      bl.position.y = 0.014; const piv = new THREE.Group(); piv.add(bl); piv.rotation.z = b / 18 * Math.PI * 2; bl.rotation.y = 0.5;
      fan.add(piv);
    }
    const spinner = new THREE.Mesh(new THREE.ConeGeometry(0.009, 0.018, 24), metal); spinner.rotation.x = Math.PI / 2; spinner.position.z = 0.006; fan.add(spinner);
    eng.add(fan); eng.userData.fan = fan;
    const nozzle = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.021, 0.04, 32), metal); nozzle.rotation.x = Math.PI / 2; nozzle.position.z = -0.095; eng.add(nozzle);
    const glow = glowSprite(new THREE.Color(1.0, 0.55, 0.25), 0.045); glow.position.z = -0.125; eng.add(glow); eng.userData.glow = glow;
    const pylon = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.03, 0.12), wingMat); pylon.position.set(0, 0.03, -0.005); eng.add(pylon);
    body.add(eng);
    (root.userData.engines ||= []).push(eng);
  }

  // vertical fin (drawn in Z/Y side view, thickness along X)
  const fin = shapeGeo([[-0.29, 0.04], [-0.47, 0.04], [-0.515, 0.215], [-0.455, 0.215]], 0.007);
  fin.rotateY(-Math.PI / 2);
  const finMesh = new THREE.Mesh(fin, redMat); body.add(finMesh);
  // white CC mark on both sides of the fin
  const ccTex = new THREE.CanvasTexture(whiteCC); ccTex.colorSpace = THREE.SRGBColorSpace; ccTex.anisotropy = 8;
  const ccMat = new THREE.MeshPhysicalMaterial({ map: ccTex, transparent: true, roughness: 0.3, clearcoat: 1, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 });
  const ccW = 0.085, ccH = ccW * whiteCC.height / whiteCC.width;
  for (const s of [1, -1]) {
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(ccW, ccH), ccMat);
    pl.position.set(s * 0.0062, 0.135, -0.445); pl.rotation.y = s * Math.PI / 2;
    pl.rotation.z = 0; body.add(pl);
  }

  // belly fairing
  const bf = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), white);
  bf.scale.set(0.05, 0.022, 0.16); bf.position.set(0, -0.045, -0.02); body.add(bf);

  // lights
  const L = {};
  L.navL = glowSprite(new THREE.Color(1, 0.05, 0.05), 0.06); L.navL.position.set(0.47, 0.012, -0.15);
  L.navR = glowSprite(new THREE.Color(0.1, 1, 0.35), 0.06); L.navR.position.set(-0.47, 0.012, -0.15);
  L.strobeL = glowSprite(new THREE.Color(1, 1, 1), 0.13); L.strobeL.position.set(0.475, 0.012, -0.175);
  L.strobeR = glowSprite(new THREE.Color(1, 1, 1), 0.13); L.strobeR.position.set(-0.475, 0.012, -0.175);
  L.tail = glowSprite(new THREE.Color(1, 1, 1), 0.07); L.tail.position.set(0, 0.035, -0.505);
  L.beaconT = glowSprite(new THREE.Color(1, 0.08, 0.04), 0.07); L.beaconT.position.set(0, 0.056, 0.02);
  L.beaconB = glowSprite(new THREE.Color(1, 0.08, 0.04), 0.07); L.beaconB.position.set(0, -0.07, 0.0);
  L.landL = glowSprite(new THREE.Color(1, 0.95, 0.85), 0.05); L.landL.position.set(0.06, -0.04, 0.1);
  L.landR = glowSprite(new THREE.Color(1, 0.95, 0.85), 0.05); L.landR.position.set(-0.06, -0.04, 0.1);
  L.logo = new THREE.PointLight(0xffffff, 0, 0.6, 2); L.logo.position.set(0, 0.25, -0.35); // fin logo floodlight
  Object.values(L).forEach(o => body.add(o));
  root.userData.lights = L;

  root.traverse(o => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });

  /** Animate lights & engines.  on: 0..1 power, t: seconds */
  root.userData.update = (t, on) => {
    const blink = (period, phase, width) => ((((t + phase) % period) + period) % period) < width ? 1 : 0;
    const k = on * (root.userData.fade ?? 1);
    L.navL.material.opacity = L.navR.material.opacity = k;
    L.tail.material.opacity = k * 0.8;
    L.strobeL.material.opacity = L.strobeR.material.opacity = k * blink(1.1, 0, 0.07);
    L.beaconT.material.opacity = k * blink(1.0, 0.5, 0.12);
    L.beaconB.material.opacity = k * blink(1.0, 0.0, 0.12);
    L.landL.material.opacity = L.landR.material.opacity = k * 0.9;
    L.logo.intensity = k * 0.15;
    for (const e of root.userData.engines) {
      e.userData.fan.rotation.z = -t * 40 * k;
      e.userData.glow.material.opacity = 0.22 * k;
    }
  };
  // global fade (used for the aircraft's first appearance)
  const mats = new Set(); root.traverse(o => { if (o.material) mats.add(o.material); });
  for (const m of mats) m.userData.baseOpacity = m.opacity, m.userData.baseTransparent = m.transparent;
  root.userData.setOpacity = a => {
    root.visible = a > 0.001;
    for (const m of mats) {
      const tr = a < 0.999 || m.userData.baseTransparent;
      if (m.transparent !== tr) { m.transparent = tr; m.needsUpdate = true; }
      if (!m.isSpriteMaterial) m.opacity = m.userData.baseOpacity * a;
    }
    root.userData.fade = a;
  };
  return root;
}
