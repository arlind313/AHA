# CC STYLING — Three Locations. One Vision.

A 20-second, 9:16 (1080 × 1920, 30 fps) cinematic Instagram Reel. A CC Styling jet flies
**Ireland → Marbella → Dubai** across a 3D night-side Earth, then the camera pulls back to all three
locations and the tagline lands.

The final MP4 is rendered by this project: `out/cc-styling-three-locations.mp4`.
Everything is code, so you can retime, recolour or re-render any part.

## Quick start

```bash
npm install
npx playwright install chromium      # one-time, only needed for exporting

npm run preview                      # → http://localhost:8080  (Play with sound, scrub, space = play/pause)
npm run render                       # → out/cc-styling-three-locations.mp4  (H.264 + AAC 320k, faststart)
npm run stills                       # → out/stills/*.png  quick look-dev frames
```

Requirements: Node 18+, ffmpeg on PATH; Python 3 with numpy and scipy only if you regenerate the soundtrack.

`render.mjs` captures every frame at exactly `t = frame / 30`, so the output never drops frames,
whatever the machine's speed. It runs Chromium's software WebGL (SwiftShader) by default, so results
are identical everywhere. Set `CHROME_GPU=1` to use your GPU instead.
Use `--workers N` to split frames across N browsers.

## Timeline (edit `src/timeline.js`)

| Time | Beat |
|---|---|
| 0.0–3.0 | Europe at night, push in to Ireland · pin pulse · **IRELAND / WHERE IT ALL BEGAN** · aircraft fades in, lights & engines start, rolls out |
| 3.0–8.0 | Chase flight south; red route draws behind the aircraft · **MARBELLA / THE EXPANSION** · banked turn with a camera orbit around the jet |
| 8.0–14.0 | Accelerating chase across the Mediterranean and Middle East · riser · **DUBAI / THE NEXT CHAPTER** · shockwave ring and Burj Khalifa silhouette |
| 14.0–20.0 | Pull back to all three pins and the full route · aircraft fly-by in the foreground · **THREE LOCATIONS. / ONE VISION.** · logo and IRELAND • MARBELLA • DUBAI |

The aircraft really flies the route. Its position is a great-circle path Dublin → Marbella → Dubai,
with a rounded turn over Marbella. Speed is driven by Hermite keys, and pitch and bank come from the
path itself. The camera follows it; the motion is not faked with zooms on a flat image.

## Project structure

```
index.html          typography, overlay layer (pins, titles, Burj, final lockup), preview controls
src/timeline.js     every cue time + location coordinates
src/main.js         flight path, camera choreography, route lines, markers, render loop
src/earth.js        globe shader (night lights, terrain, borders, coastline), clouds, atmosphere
src/plane.js        procedural airliner + livery (logo on fuselage, red tail with CC mark, nav/strobe lights)
render.mjs          frame-accurate exporter → ffmpeg
tools/bake.html     builds assets/detail.png (10m coastline mask, borders, crisp city lights)
tools/make_audio.py synthesises the soundtrack (score + SFX), loudness-normalised to about -14 LUFS
tools/fit_final.mjs solves the final camera so the three pins sit in the intended composition
```

## Brand assets

- `assets/logo.png` is lifted directly from your reference artwork (background keyed out; shapes and
  colours untouched). **For the sharpest result, replace it with your original logo file** (transparent PNG,
  white + #E30613) and re-render.
- On the white fuselage the logo's white parts are drawn in near-black, the standard light-background
  version. The tail fin carries the white "CC" mark on red.
- Brand red is `#E30613` throughout. The font is Montserrat (OFL), bundled in `assets/fonts`.

## Sources and licences

- Earth imagery: NASA Black Marble (city lights), Blue Marble (terrain) and topography/water masks, all public domain,
  via the `three-globe` package examples.
- Coastlines and borders: Natural Earth (public domain), via `world-atlas`. Town positions: GeoNames (CC-BY),
  via `cities.json`.
- Soundtrack: synthesised from scratch by `tools/make_audio.py`, with no samples or third-party music, so it is
  royalty-free. To use a licensed track instead, drop it in as `assets/soundtrack.wav` (20 s) and re-run
  `npm run render`. The hit points are 0.95 s, 5.95 s, 12.35 s (Dubai), 15.55 s and 16.3 s (climax).
