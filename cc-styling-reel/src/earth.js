// Night-side Earth: NASA Black Marble lights + Blue Marble terrain (graded to charcoal),
// NASA topography hillshade, and a baked high-res regional layer (10m coastlines, borders, towns).
import * as THREE from 'three';

export const EARTH_R = 6371; // km — 1 world unit = 1 km

const common = /* glsl */`
  float hash(vec3 p){ p = fract(p*0.3183099+0.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
  float vnoise(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z); }
  float fbm(vec3 p){ float a=0.5, s=0.0; for(int i=0;i<5;i++){ s+=a*vnoise(p); p=p*2.03+vec3(1.7,9.2,3.1); a*=0.5; } return s; }
`;

export function createEarth(tex, detailInfo) {
  const group = new THREE.Group();
  const D2R = Math.PI / 180;
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      tNight: { value: tex.night }, tDay: { value: tex.day }, tTopo: { value: tex.topo }, tWater: { value: tex.water },
      tDetail: { value: tex.detail },
      uRegion: { value: new THREE.Vector4(detailInfo.lon0 * D2R, detailInfo.lon1 * D2R, detailInfo.lat0 * D2R, detailInfo.lat1 * D2R) },
      uTopoTexel: { value: new THREE.Vector2(1 / 2048, 1 / 1024) },
      uMoon: { value: new THREE.Vector3(-0.35, 0.75, 0.55).normalize() },
      uLights: { value: 1.0 },
    },
    vertexShader: /* glsl */`
      varying vec3 vObj; varying vec3 vN; varying vec3 vV;
      void main(){ vObj = position; vec4 wp = modelMatrix*vec4(position,1.0);
        vN = normalize(mat3(modelMatrix)*normal); vV = normalize(cameraPosition - wp.xyz);
        gl_Position = projectionMatrix*viewMatrix*wp; }`,
    fragmentShader: /* glsl */`
      uniform sampler2D tNight, tDay, tTopo, tWater, tDetail; uniform vec4 uRegion; uniform vec2 uTopoTexel;
      uniform vec3 uMoon; uniform float uLights;
      varying vec3 vObj; varying vec3 vN; varying vec3 vV;
      ${common}
      const float PI = 3.141592653589793;
      void main(){
        vec3 n = normalize(vObj);
        float lat = asin(clamp(n.y,-1.0,1.0)); float lon = atan(n.x, n.z);
        vec2 uv = vec2(lon/(2.0*PI)+0.5, lat/PI+0.5);
        vec2 ruv = vec2((lon-uRegion.x)/(uRegion.y-uRegion.x), (lat-uRegion.z)/(uRegion.w-uRegion.z));
        vec2 e = min(ruv, 1.0-ruv);
        float w = smoothstep(0.0, 0.03, min(e.x, e.y));            // detail-layer weight (fades at region edge)
        vec4 det = texture2D(tDetail, clamp(ruv, 0.0, 1.0));
        float detBlur = texture2D(tDetail, clamp(ruv,0.0,1.0), 3.5).r;
        float waterLo = texture2D(tWater, uv).r;
        float deepWater = smoothstep(0.93, 1.0, texture2D(tWater, uv, 2.0).r);   // inland seas (Caspian) not in the vector land layer
        float land = mix(1.0 - waterLo, det.r * (1.0 - deepWater), w);
        float landSoft = mix(1.0 - waterLo, detBlur, w);

        // terrain: Blue Marble graded to cool charcoal + hillshade + fine grain
        vec3 day = texture2D(tDay, uv).rgb;
        float l = dot(day, vec3(0.2126,0.7152,0.0722));
        vec3 terr = mix(vec3(l), day, 0.22);
        terr = terr / (0.28 + terr) * 0.42;   // compress snow / ice highlights
        float h0 = texture2D(tTopo, uv).r;
        float hx = texture2D(tTopo, uv + vec2(uTopoTexel.x,0.0)).r - texture2D(tTopo, uv - vec2(uTopoTexel.x,0.0)).r;
        float hy = texture2D(tTopo, uv + vec2(0.0,uTopoTexel.y)).r - texture2D(tTopo, uv - vec2(0.0,uTopoTexel.y)).r;
        vec3 hn = normalize(vec3(-hx*7.0, -hy*7.0, 1.0));
        float shade = 0.62 + 0.75*max(dot(hn, normalize(vec3(-0.55,0.6,0.6))), 0.0);
        float grain = 0.82 + 0.36*fbm(n*900.0);
        vec3 landCol = (vec3(0.026,0.028,0.033) + terr*vec3(0.20,0.19,0.18)) * shade * grain;
        landCol += vec3(0.012,0.010,0.008)*h0;

        // ocean: deep navy with continental-shelf lift near coasts
        float shelf = clamp(landSoft*1.6, 0.0, 1.0)*(1.0-land);
        vec3 ocean = vec3(0.0018,0.0038,0.0095) * (0.85+0.3*fbm(n*60.0)) + vec3(0.003,0.008,0.018)*shelf;

        vec3 col = mix(ocean, landCol, land);

        // moonlight roundness
        float m = 0.55 + 0.45*max(dot(normalize(vN), uMoon), 0.0);
        col *= m;

        // city lights
        float nl = dot(texture2D(tNight, uv, 1.0).rgb, vec3(0.333));
        vec3 warm = vec3(1.0,0.56,0.2);
        float breakup = mix(1.0, 0.35 + 1.1*fbm(n*2600.0), w);
        vec3 lights = warm * pow(nl, 1.45) * mix(1.35, 0.55, w) * breakup;
        lights += vec3(1.0,0.74,0.42) * det.b * 1.6 * w;
        col += lights * uLights * (0.35 + 0.65*land);

        // country borders: faint amber hairlines (as in the reference)
        col += vec3(0.85,0.46,0.16) * det.g * 0.16 * w;
        // coastline sheen
        col += vec3(0.30,0.20,0.10) * clamp(abs(land - landSoft)*1.4,0.0,1.0) * 0.12 * w;

        // limb haze
        float fres = pow(1.0 - max(dot(normalize(vN), vV), 0.0), 3.0);
        col += vec3(0.03,0.06,0.14) * fres * 0.35;
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const earth = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R, 512, 256), mat);
  group.add(earth);

  // thin cloud shell (procedural, slow drift) — subtle, sits below the aircraft
  const cloudMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: { uTime: { value: 0 }, uOpacity: { value: 1 } },
    vertexShader: /* glsl */`varying vec3 vObj; varying vec3 vN; varying vec3 vV;
      void main(){ vObj=position; vec4 wp=modelMatrix*vec4(position,1.0); vN=normalize(mat3(modelMatrix)*normal); vV=normalize(cameraPosition-wp.xyz); gl_Position=projectionMatrix*viewMatrix*wp; }`,
    fragmentShader: /* glsl */`uniform float uTime, uOpacity; varying vec3 vObj; varying vec3 vN; varying vec3 vV;
      ${common}
      void main(){ vec3 p = vObj/6371.0;
        vec3 q = p*7.0 + vec3(uTime*0.004, 0.0, uTime*0.002);
        float warp = fbm(q*1.7);
        float d = fbm(q*2.3 + warp*1.4);
        float a = smoothstep(0.52, 0.78, d);
        a *= 0.5 + 0.5*fbm(p*60.0 + warp);
        float fres = max(dot(normalize(vN), vV), 0.0);
        vec3 c = vec3(0.085,0.095,0.115) * (0.7 + 0.5*fbm(p*30.0));
        gl_FragColor = vec4(c*0.55, a*0.26*uOpacity*smoothstep(0.0,0.25,fres));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const clouds = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R + 9, 256, 128), cloudMat);
  group.add(clouds);

  // atmosphere rim
  const atmMat = new THREE.ShaderMaterial({
    side: THREE.BackSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: /* glsl */`varying vec3 vN; varying vec3 vP; void main(){ vN=normalize(mat3(modelMatrix)*normal); vec4 wp=modelMatrix*vec4(position,1.0); vP=wp.xyz; gl_Position=projectionMatrix*viewMatrix*wp; }`,
    fragmentShader: /* glsl */`varying vec3 vN; varying vec3 vP;
      void main(){ vec3 v = normalize(cameraPosition - vP); float i = pow(clamp(0.6 + dot(vN, v), 0.0, 1.0), 7.0);
        gl_FragColor = vec4(vec3(0.20,0.38,0.85)*i*0.55, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  group.add(new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.014, 192, 96), atmMat));
  group.userData = { earthMat: mat, cloudMat };
  return group;
}
