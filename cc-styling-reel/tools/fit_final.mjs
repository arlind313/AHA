// Searches final-shot camera params so the pins sit in the intended composition.
import { createRequire } from 'node:module';
import { start } from '../serve.mjs';
const { chromium } = createRequire(import.meta.url)('playwright');
const s = await start(8097);
const b = await chromium.launch({ args: ['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto('http://localhost:8097/index.html?render=1');
await p.waitForFunction(() => window.__ready === true, null, { timeout: 180000 });
const goal = { ireland: [330, 470], marbella: [215, 820], dubai: [835, 1035] };
const res = await p.evaluate((goal) => {
  let best = null, cur = { lat: 33.5, lon: 21, dist: 13500, az: -45, el: 60 };
  const err = o => { const r = window.__projectFinal(o); let e = 0; for (const k in goal) { if (!r[k][2]) e += 1e7; e += (r[k][0] - goal[k][0]) ** 2 + (r[k][1] - goal[k][1]) ** 2; } return [e, r]; };
  let [be, br] = err(cur); best = { ...cur };
  const step = { lat: 3, lon: 3, dist: 1500, az: 10, el: 6 };
  for (let it = 0; it < 4000; it++) {
    const scale = 1 - it / 4400;
    const c = { ...best };
    for (const k in step) c[k] += (Math.random() * 2 - 1) * step[k] * scale;
    c.el = Math.min(80, Math.max(35, c.el));
    const [e, r] = err(c);
    if (e < be) { be = e; br = r; best = c; }
  }
  return { best, be, br };
}, goal);
console.log(JSON.stringify(res));
await b.close(); s.close();
