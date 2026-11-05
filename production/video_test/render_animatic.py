"""Animatic v1 for THE IRISH GRAFT - PART 1, cold open (S001-S003), 21s, 1080x1920, 30fps.

This is a TIMING ANIMATIC built from the approved Page 01 panels: it adds rain, light, glint, shimmer and
handheld motion, a temp sound bed, temp subtitles and the title card. It does NOT contain real character
animation (no walk cycle, no finger movement) - that requires an image-to-video model (see I2V_KIT.md).

Run from repo root: python3 production/video_test/render_animatic.py
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
T1, T2, TOTAL = 5.0, 14.5, 21.0          # S001 0-5s, S002 5-14.5s, S003 14.5-21s (matches storyboard v0.4)
SR = 48000
rng = np.random.default_rng(7)

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SUBS = [(0.3, 4.8, "People see the cars, the events, the villas in Marbella."),
        (5.2, 14.2, "What they don't see is a tyre shop in Ireland,\na ferry to Holyhead,\nand a lot of very expensive mistakes."),
        (14.8, 16.4, "My name is Conor Callaghan.\nAnd this is how it started.")]


def load(name, scale=1.08):
    im = Image.open(os.path.join(HERE, "frames", f"{name}_9x16.png")).convert("RGB")
    big = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS)  # headroom for camera float
    return np.asarray(big).astype(np.float32)


P1, P2, P3 = load("p1"), load("p2"), load("p3")


def view(img, zoom, dx, dy, rot=0.0):
    """Crop a W x H window from the oversized plate with zoom/offset (small motivated camera move)."""
    h, w, _ = img.shape
    cw, ch = W / zoom * (w / (W * 1.08)), H / zoom * (h / (H * 1.08))
    cx, cy = w / 2 + dx, h / 2 + dy
    pil = Image.fromarray(img.astype(np.uint8))
    if rot:
        pil = pil.rotate(rot, resample=Image.BICUBIC, center=(cx, cy))
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
    return np.asarray(pil.crop(box).resize((W, H), Image.BILINEAR)).astype(np.float32)


def radial(cx, cy, r, shape=(H, W)):
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** 2


# ---- shot 1: heat shimmer on pavement, glint sweeping across cars, walk-cadence bob
YY = np.arange(H)[:, None]
shimmer_mask = np.clip((YY - 1250) / 400, 0, 1)


def shot1(t):
    u = t / T1
    bob = 6 * math.sin(2 * math.pi * t / 1.1)            # step cadence
    img = view(P1, 1.0 + 0.03 * u, 0, -10 + bob)
    # heat shimmer: horizontal row displacement on the lower frame
    off = (3 * np.sin(YY / 9.0 + t * 7) * shimmer_mask).astype(int)[:, 0]
    rows = np.arange(W)[None, :] + off[:, None]
    img = img[np.arange(H)[:, None], np.clip(rows, 0, W - 1)]
    # specular glint travelling along the car row
    gx = -200 + 1500 * u
    glint = radial(gx, 1150 - 0.25 * gx, 260) * 0.55
    img += glint[..., None] * np.array([255, 210, 150])
    # warm light breathing
    img *= 1.0 + 0.025 * math.sin(t * 1.7)
    return img


# ---- shot 2: bokeh drift, fob glint pulse, hand micro-float
BOKEH = [(rng.uniform(0, W), rng.uniform(0, 900), rng.uniform(40, 110), rng.uniform(-14, 14)) for _ in range(14)]


def shot2(t):
    lt = t - T1
    img = view(P2, 1.02 + 0.012 * math.sin(lt * 0.6), 4 * math.sin(lt * 0.9), 3 * math.sin(lt * 1.3),
               rot=0.6 * math.sin(lt * 0.5))
    add = np.zeros((H, W), np.float32)
    for (x, y, r, vx) in BOKEH:
        add += radial((x + vx * lt) % W, y + 6 * math.sin(lt + x), r) * 0.18
    img += add[..., None] * np.array([255, 170, 90])
    star = radial(560, 360, 90) * (0.35 + 0.35 * max(0, math.sin(lt * 2.2)))
    img += star[..., None] * np.array([255, 235, 200])
    return img


# ---- shot 3: rain on glass, breath fog, cold flicker
DROPS = [dict(x=rng.uniform(0, W), y=rng.uniform(-H, H), v=rng.uniform(250, 900), l=rng.uniform(40, 160),
              w=rng.uniform(1.5, 4.0)) for _ in range(90)]


def shot3(t):
    lt = t - T2
    img = view(P3, 1.0 + 0.008 * lt, 0, 0)
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    for dr in DROPS:
        y = (dr["y"] + dr["v"] * lt) % (H + 200) - 100
        x = dr["x"] + 6 * math.sin(y / 120)
        d.line([(x, y - dr["l"]), (x, y)], fill=150, width=int(dr["w"]))
        d.ellipse([x - dr["w"] * 1.6, y - dr["w"] * 1.6, x + dr["w"] * 1.6, y + dr["w"] * 1.6], fill=210)
    rain = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    img = img * (1 - 0.35 * rain[..., None]) + rain[..., None] * np.array([215, 225, 235]) * 0.35
    fog = radial(560, 1100, 700) * 0.28 * max(0, math.sin(min(lt / 2.4, 1) * math.pi))
    img = img * (1 - fog[..., None]) + fog[..., None] * 235
    img *= 1.0 - 0.02 * (rng.random() > 0.93)
    return img


def overlay_text(img, t):
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil, "RGBA")
    # temp subtitles (VO placeholder)
    f = ImageFont.truetype(SANS, 40)
    for a, b, txt in SUBS:
        if a <= t <= b:
            alpha = int(255 * min(1, (t - a) / 0.3, (b - t) / 0.3))
            for i, line in enumerate(txt.split("\n")):
                tw = d.textlength(line, font=f)
                y = 1590 + i * 54
                d.rectangle([W / 2 - tw / 2 - 14, y - 6, W / 2 + tw / 2 + 14, y + 48], fill=(0, 0, 0, int(alpha * 0.55)))
                d.text((W / 2 - tw / 2, y), line, font=f, fill=(255, 255, 255, alpha))
    # title card over S003
    if t >= 16.6:
        a = min(1, (t - 16.6) / 1.2)
        ft, fs = ImageFont.truetype(SERIF, 84), ImageFont.truetype(SERIF, 46)
        for txt, font, y, sp in (("THE IRISH GRAFT", ft, 770, 6), ("PART 1", fs, 900, 16)):
            chars = list(txt)
            widths = [d.textlength(c, font=font) for c in chars]
            total = sum(widths) + sp * (len(chars) - 1)
            x = W / 2 - total / 2
            for c, cw in zip(chars, widths):
                d.text((x + 3, y + 4), c, font=font, fill=(0, 0, 0, int(160 * a)))
                d.text((x, y), c, font=font, fill=(245, 240, 228, int(255 * a)))
                x += cw + sp
        d.line([(W / 2 - 160, 880), (W / 2 + 160, 880)], fill=(245, 240, 228, int(200 * a)), width=3)
    # animatic bug
    fb = ImageFont.truetype(SANS, 26)
    d.text((28, 26), "ANIMATIC v1 - temp sound, no VO, no character animation", font=fb, fill=(255, 255, 255, 150))
    return pil


def render_video(path):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        t = i / FPS
        img = shot1(t) if t < T1 else shot2(t) if t < T2 else shot3(t)
        # fade in from black / out to black
        img *= min(1, t / 0.6) * min(1, (TOTAL - t) / 0.8)
        ff.stdin.write(overlay_text(img, t).tobytes())
    ff.stdin.close()
    ff.wait()


# ---------------------------------------------------------------- temp sound bed
def tone(f, dur, decay, harm=(1, .5, .25, .12)):
    t = np.arange(int(dur * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * f * (k + 1) * t) for k, a in enumerate(harm))
    return s * np.exp(-t / decay) * np.clip(t / 0.005, 0, 1)


def render_audio(path):
    n = int(TOTAL * SR)
    t = np.arange(n) / SR
    L = np.zeros(n)
    # warm pad (A minor add9), 0 - T2, slow swell, hard cut at the match cut
    pad = sum(np.sin(2 * np.pi * f * t + p) for f, p in ((110, 0), (164.8, 1), (220, 2), (261.6, .5), (329.6, 1.5), (493.9, .3)))
    pad *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t)) * np.clip(t / 2.5, 0, 1) * (t < T2) * 0.035
    L += pad
    # city / sea bed (filtered noise) before the cut
    noise = rng.normal(0, 1, n)
    sea = np.convolve(noise, np.ones(400) / 400, mode="same") * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * t))
    L += sea * (t < T2) * 0.25
    # footsteps in S001 (soft thumps on the step cadence)
    for k in np.arange(0.35, T1, 0.55):
        i = int(k * SR)
        th = tone(70, 0.18, 0.04, harm=(1, .3)) * 0.35
        L[i:i + len(th)] += th[:n - i]
    # key jingle in S002
    for k in (6.1, 6.25, 6.33, 9.8, 9.9):
        i = int(k * SR)
        for f in (3150, 4420, 5900):
            j = tone(f, 0.25, 0.05, harm=(1,)) * 0.05
            L[i:i + len(j)] += j[:n - i]
    # rain + wind after the cut
    rain = noise - np.convolve(noise, np.ones(8) / 8, mode="same")
    L += rain * (t >= T2) * 0.16
    wind = np.convolve(rng.normal(0, 1, n), np.ones(1200) / 1200, mode="same") * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t + 1))
    L += wind * (t >= T2) * 1.4
    for k in rng.uniform(T2, TOTAL, 140):                         # individual drops on the glass
        i = int(k * SR)
        dp = tone(rng.uniform(1800, 3200), 0.03, 0.006, harm=(1,)) * 0.04
        L[i:i + len(dp)] += dp[:n - i]
    # piano notes: the match cut and the title
    for k, f, g in ((T2, 220.0, .22), (16.6, 329.6, .16), (17.4, 261.6, .12)):
        i = int(k * SR)
        p = tone(f, 4.0, 1.4) * g
        L[i:i + len(p)] += p[:n - i]
    L *= np.clip((TOTAL - t) / 0.8, 0, 1)
    L = L / max(1e-6, np.abs(L).max()) * 0.8
    R = np.roll(L, 24)                                              # slight stereo width
    pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    render_audio(os.path.join(out, "temp_sound.wav"))
    render_video(os.path.join(out, "picture.mp4"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(out, "picture.mp4"), "-i",
                    os.path.join(out, "temp_sound.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    os.path.join(out, "IRISH_GRAFT_P1_COLD_OPEN_ANIMATIC_v1.mp4")], check=True)
    print("done")
