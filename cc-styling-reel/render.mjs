// Frame-accurate exporter: drives index.html?render=1 in headless Chromium, captures every
// frame at exactly t = frame / FPS, pipes PNGs into ffmpeg, then muxes the soundtrack.
//
//   node render.mjs                         → out/cc-styling-three-locations.mp4
//   node render.mjs --stills 0,1.5,4,7,10   → out/stills/*.png  (quick look-dev)
//   node render.mjs --from 120 --to 240     → partial render (frames)
//   node render.mjs --workers 2             → split frames over N browsers (multi-core)
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import { start } from './serve.mjs';
const { chromium } = createRequire(import.meta.url)('playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? a.push([v.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]) : 0, a), []));
fs.mkdirSync('out/stills', { recursive: true });
const server = await start(8093);
const URL = 'http://localhost:8093/index.html?render=1';
const launchArgs = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'];
if (process.env.CHROME_GPU) launchArgs.splice(0, 2, '--use-angle=default');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('[pageerror]', e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  await page.goto(URL);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 180000 });
  await page.evaluate(() => window.renderAt(0));
  return page;
}
const shot = async (page, t) => { await page.evaluate(t => window.renderAt(t), t); return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } }); };

const browser = await chromium.launch({ args: launchArgs });
const meta = await (async () => { const p = await openPage(browser); const m = await p.evaluate(() => window.__meta); await p.close(); return m; })();

if (args.stills) {
  const page = await openPage(browser);
  for (const t of String(args.stills).split(',').map(Number)) {
    const buf = await shot(page, t);
    fs.writeFileSync(`out/stills/t${t.toFixed(2).padStart(5, '0')}.png`, buf);
    console.log('still', t);
  }
  await browser.close(); server.close(); process.exit(0);
}

const total = Math.round(meta.DURATION * meta.FPS);
const from = Number(args.from ?? 0), to = Number(args.to ?? total);
const workers = Number(args.workers ?? 1);
const silent = 'out/_video_only.mp4';
const ranges = [];
const per = Math.ceil((to - from) / workers);
for (let w = 0; w < workers; w++) ranges.push([from + w * per, Math.min(to, from + (w + 1) * per)]);

const t0 = Date.now();
await Promise.all(ranges.map(async ([a, b], w) => {
  const page = await openPage(w === 0 ? browser : await chromium.launch({ args: launchArgs }));
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(meta.FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(meta.FPS), `out/_seg${w}.mp4`], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < b; f++) {
    const buf = await shot(page, f / meta.FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - a) % 15 === 0) {
      const el = (Date.now() - t0) / 1000;
      console.log(`[w${w}] frame ${f}/${b - 1}  ${el.toFixed(0)}s elapsed`);
    }
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}));
await browser.close(); server.close();

fs.writeFileSync('out/_segs.txt', ranges.map((_, w) => `file '_seg${w}.mp4'`).join('\n'));
const run = a => new Promise((res, rej) => spawn('ffmpeg', a, { stdio: 'inherit' }).on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
await run(['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/_segs.txt', '-c', 'copy', silent]);
const final = args.out || 'out/cc-styling-three-locations.mp4';
if (fs.existsSync('assets/soundtrack.wav') && from === 0 && to === total) {
  await run(['-y', '-loglevel', 'error', '-i', silent, '-i', 'assets/soundtrack.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest', '-movflags', '+faststart', final]);
} else {
  await run(['-y', '-loglevel', 'error', '-i', silent, '-c', 'copy', '-movflags', '+faststart', final]);
}
console.log(`done → ${final}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
