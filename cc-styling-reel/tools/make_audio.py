"""Original soundtrack + sound design for the reel, synthesised from scratch (no samples,
no third-party music) → assets/soundtrack.wav (48 kHz stereo, 20 s). Royalty-free by construction.
Cue times mirror src/timeline.js."""
import numpy as np
from scipy import signal
SR = 48000; DUR = 20.0; N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)
T = dict(irelandPin=0.95, lightsOn=1.75, takeoff=2.55, marbellaPin=5.95, orbit=6.2, legB=8.0,
         dubaiPin=12.35, flyby=14.35, line1=15.55, line2=16.3, logo=17.25)

def env(a, b, attack=0.01, release=0.3, curve=1.0):
    e = np.clip((t - a) / max(attack, 1e-4), 0, 1) * np.clip((b - t) / max(release, 1e-4), 0, 1)
    return e ** curve
def add(x, gain=1.0, pan=0.0):
    global L, R
    L += x * gain * np.sqrt(0.5 * (1 - pan)); R += x * gain * np.sqrt(0.5 * (1 + pan))
def lp(x, fc, order=2): return signal.sosfilt(signal.butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2): return signal.sosfilt(signal.butter(order, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, order=2): return signal.sosfilt(signal.butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)
def saw(f, harmonics=24, detune=0.0):
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(f * (1 + detune), t.shape)) / SR
    return sum(((-1) ** (k + 1)) * np.sin(k * ph) / k for k in range(1, harmonics + 1)) * 0.6
def sine(f): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(f, t.shape)) / SR)
def sweep_noise(t0, t1, f0, f1, q=0.5, seed=0):
    """band-passed noise whose centre frequency glides f0→f1 (smooth STFT-domain mask, click-free)."""
    i0, i1 = int(t0 * SR), min(N, int(t1 * SR))
    n = np.random.default_rng(seed).standard_normal(i1 - i0 + 4096)
    f, fr, Z = signal.stft(n, SR, nperseg=2048, noverlap=1536)
    k = np.clip(fr / max(1e-6, (i1 - i0) / SR), 0, 1)
    fc = f0 * (f1 / f0) ** k
    lf = np.log(np.maximum(f, 1.0))[:, None]
    mask = np.exp(-0.5 * ((lf - np.log(fc)[None, :]) / (0.25 + q)) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=2048, noverlap=1536)
    out = np.zeros(N); seg = y[:i1 - i0]; out[i0:i0 + seg.size] = seg / (np.abs(seg).max() + 1e-9) * 0.5
    return out
def note(name):
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'Bb': 1, 'B': 2}
    n, o = name[:-1], int(name[-1]); return 440 * 2 ** ((names[n] + 12 * (o - 4)) / 12)

# ── score: D minor, 120 bpm ──────────────────────────────────
chords = [(0.0, ['D3', 'A3', 'F4', 'A4']), (4.0, ['Bb2', 'F3', 'D4', 'F4']), (8.0, ['G2', 'D3', 'Bb3', 'D4']),
          (10.2, ['A2', 'E3', 'A3', 'C#4']), (12.35, ['D2', 'A2', 'F3', 'A3', 'D4']), (14.35, ['Bb1', 'F2', 'D3', 'F3', 'A3']),
          (16.3, ['D2', 'A2', 'D3', 'F3', 'A3', 'E4']), (20.5, [])]
pad = np.zeros(N)
for (c0, notes), (c1, _) in zip(chords[:-1], chords[1:]):
    seg = env(c0 - 0.15, c1 + 0.4, attack=0.6 if c0 < 12 else 0.08, release=0.7)
    for nn in notes:
        f = note(nn)
        pad += seg * (saw(f, 18, -0.0035) + saw(f, 18, 0.0041)) * 0.5
cut = 500 + 2600 * np.clip((t - 6) / 10.3, 0, 1) ** 1.5
pad_f = np.zeros(N)
for s in range(0, N, 2400):  # slowly opening filter
    e = min(N, s + 2400); pad_f[s:e] = lp(pad[max(0, s - 2400):e], float(cut[s]), 2)[-(e - s):]
swell = 0.2 + 0.8 * np.clip(t / 2.0, 0, 1)
swell *= 0.75 + 0.25 * np.clip((t - 8) / 4.35, 0, 1) + 0.35 * (t > T['line2'])
add(pad_f * swell, 0.085, -0.25); add(np.roll(pad_f, 900) * swell, 0.085, 0.25)

# sub drone
drone = (sine(note('D1')) * 0.8 + sine(note('D2')) * 0.35) * env(0, 20.2, 2.2, 1.8)
add(drone, 0.16)
# airy atmosphere
air = lp(hp(rng.standard_normal(N), 900), 5000) * env(0, 9, 1.5, 3.0)
add(air, 0.02, -0.4); add(np.roll(air, 3000), 0.02, 0.4)

# pulse bass (8ths, gets 16ths after Dubai), plus toms
bpm = 120; beat = 60 / bpm
def pluck(at, f, dur=0.22, gain=1.0):
    e = np.where(t >= at, np.exp(-(t - at) / (dur * 0.35)), 0) * (t < at + dur * 2)
    return lp(saw(f, 10), 900) * e * gain
bass = np.zeros(N)
roots = [(3.0, 'D2'), (4.0, 'Bb1'), (8.0, 'G1'), (10.2, 'A1'), (12.35, 'D2'), (14.35, 'Bb1'), (16.3, 'D2'), (19.0, None)]
for (r0, rn), (r1, _) in zip(roots[:-1], roots[1:]):
    if rn is None: continue
    step = beat / 2 if r0 < 12.35 else beat / 4
    x = r0
    while x < r1 - 1e-6:
        g = 0.35 if r0 < 8 else 0.6 + 0.4 * (x - 8) / 8
        if r0 >= 16.3: g *= np.exp(-(x - 16.3) / 1.6)
        bass += pluck(x, note(rn), 0.25, g)
        x += step
add(bass, 0.22)
def tom(at, f=70, gain=1.0):
    e = np.where(t >= at, np.exp(-(t - at) / 0.18), 0) * (t < at + 0.8)
    pitch = f * (1 + 0.9 * np.exp(-np.clip(t - at, 0, None) / 0.03))
    return (sine(pitch) * e + lp(rng.standard_normal(N), 1800) * e * 0.25 * np.exp(-np.clip(t - at, 0, None) / 0.03)) * gain
for k, x in enumerate(np.arange(8.0, 12.3, beat)):
    add(tom(x, 62, 0.5 + 0.5 * k / 9), 0.28, -0.2 if k % 2 else 0.2)
for x in np.arange(12.35 + beat, 16.2, beat):
    add(tom(x, 58, 0.8), 0.26)
for x in [11.6, 11.85, 12.1, 12.225]:
    add(tom(x, 80, 0.9), 0.25)

# ── sound design ─────────────────────────────────────────────
def impact(at, size=1.0, sub=48):
    tt = np.clip(t - at, 0, None); on = t >= at
    boom = sine(sub * (1 + 1.5 * np.exp(-tt / 0.05))) * np.exp(-tt / (0.55 * size)) * on
    crack = hp(rng.standard_normal(N), 2500) * np.exp(-tt / 0.04) * on
    body = lp(rng.standard_normal(N), 400) * np.exp(-tt / (0.25 * size)) * on
    return boom * 1.0 + crack * 0.18 * size + body * 0.5
def bell(at, f, gain=1.0, decay=1.4):
    tt = np.clip(t - at, 0, None); on = t >= at
    return sum(sine(f * m) * np.exp(-tt / (decay / m ** 0.5)) * a for m, a in [(1, 1), (2.76, 0.35), (5.4, 0.12)]) * on * gain
# Ireland pin: soft ping
add(bell(T['irelandPin'], note('A5'), 0.5), 0.12, -0.3)
add(impact(T['irelandPin'], 0.4, 55), 0.12)
# engines: spool-up whine + turbine roar
spool = sine(400 + 2400 * np.clip((t - T['lightsOn']) / 1.6, 0, 1) ** 0.7) * env(T['lightsOn'], 5.0, 0.6, 2.0)
add(spool, 0.025, 0.2)
roar = sweep_noise(T['lightsOn'], 9.0, 250, 900, 0.8, seed=3) * env(T['lightsOn'] + 0.3, 9.0, 1.3, 3.5)
add(roar, 0.25, -0.1); add(np.roll(roar, 400), 0.25, 0.1)
rumble = lp(rng.standard_normal(N), 140) * env(T['takeoff'], 6.5, 0.6, 2.5)
add(rumble, 0.5)
# whooshes
for at, d, f0, f1, g, pan in [(2.9, 1.1, 300, 3500, 0.5, -0.5), (6.2, 1.6, 2500, 400, 0.35, 0.5), (7.95, 1.1, 250, 4200, 0.55, -0.3),
                              (11.0, 1.35, 300, 6000, 0.35, 0.0), (14.0, 1.2, 4000, 300, 0.4, 0.3)]:
    w = sweep_noise(at, at + d, f0, f1, 0.35, seed=int(at * 10)) * np.sin(np.pi * np.clip((t - at) / d, 0, 1)) ** 2
    add(w, g, pan)
# Marbella: controlled cinematic impact
add(impact(T['marbellaPin'], 0.9, 46), 0.42)
add(bell(T['marbellaPin'], note('D5'), 0.4, 2.0), 0.1, 0.3)
# riser into Dubai
riser = sweep_noise(10.2, T['dubaiPin'], 400, 9000, 0.25, seed=11) * np.clip((t - 10.2) / (T['dubaiPin'] - 10.2), 0, 1) ** 2 * (t < T['dubaiPin'])
add(riser, 0.55)
# Dubai: powerful bass impact
add(impact(T['dubaiPin'], 1.8, 38), 0.75)
add(bell(T['dubaiPin'], note('A5'), 0.5, 2.6), 0.08)
# flyby: jet pass with doppler + pan
fb = T['flyby']; k = np.clip((t - fb) / 1.8, 0, 1)
jet = sweep_noise(fb, fb + 1.8, 1800, 500, 0.9, seed=21) * np.sin(np.pi * k) ** 1.5
whine = sine(1500 - 700 * k) * np.sin(np.pi * k) ** 2 * (t >= fb) * (t < fb + 1.8)
for s_ in range(2):
    pan = -0.9 + 1.8 * k
    add(jet * (1 - pan) / 2 if s_ == 0 else 0, 0.0)
L += (jet * 0.55 + whine * 0.03) * np.sqrt(np.clip((1 - (-0.9 + 1.8 * k)) / 2, 0, 1))
R += (jet * 0.55 + whine * 0.03) * np.sqrt(np.clip((1 + (-0.9 + 1.8 * k)) / 2, 0, 1))
# tagline hits + climax
add(impact(T['line1'], 1.0, 50), 0.4)
add(impact(T['line2'], 2.2, 36), 0.85)
cym = hp(rng.standard_normal(N), 5000) * np.exp(-np.clip(t - T['line2'], 0, None) / 1.6) * (t >= T['line2'])
add(cym, 0.06, -0.2); add(np.roll(cym, 700), 0.06, 0.2)
# logo shimmer
for i, nn in enumerate(['D6', 'A6', 'E6', 'D7']):
    add(bell(T['logo'] + i * 0.09, note(nn), 0.35, 1.8), 0.05, -0.3 + 0.2 * i)

# ── reverb, master ───────────────────────────────────────────
ir_t = np.arange(int(SR * 2.8)) / SR
irL = rng.standard_normal(ir_t.size) * np.exp(-ir_t / 0.75); irR = rng.standard_normal(ir_t.size) * np.exp(-ir_t / 0.75)
irL = lp(irL, 6000); irR = lp(irR, 6000)
wetL = signal.fftconvolve(L, irL)[:N]; wetR = signal.fftconvolve(R, irR)[:N]
wetL *= 0.22 / (np.abs(wetL).max() / max(1e-9, np.abs(L).max())); wetR *= 0.22 / (np.abs(wetR).max() / max(1e-9, np.abs(R).max()))
L, R = L + wetL, R + wetR
L, R = hp(L, 25), hp(R, 25)
fade = np.clip((DUR - t) / 0.6, 0, 1); L *= fade; R *= fade
mx = np.stack([L, R], 1); mx = np.tanh(mx / np.abs(mx).max() * 1.6) / np.tanh(1.6) * 0.89
from scipy.io import wavfile
wavfile.write('assets/soundtrack_raw.wav', SR, (mx * 32767).astype(np.int16))
print('ok', mx.shape)
