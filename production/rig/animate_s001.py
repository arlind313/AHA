"""S001 proof of concept: code-driven 2D character animation of adult Conor walking toward camera in Marbella.

Method (all free / local):
  - Layers: Conor RGBA matte + clean background plate (build_layers.py).
  - Rig: hand-placed skeleton (conor_s001_rig.py) with joints + bone mid-points as deformation handles.
  - Deformation: rigid Moving-Least-Squares image warping (Schaefer et al. 2006) driven per frame by a procedural
    walk cycle (contact -> passing -> opposite contact -> passing): alternating legs with knee lift, pelvis sway
    and tilt, body bob, counter-rotating shoulders, opposite arm swing, head lag/tilt, shirt following the hips.
  - Environment: palm fronds swaying, travelling glints on the cars, heat shimmer, contact shadows, backward dolly
    parallax of the background, warm light breathing, film grain.

Usage: python3 animate_s001.py [seconds]      -> out/S001_walk_poc.mp4 (1080x1920, 24 fps)
"""
import math
import os
import subprocess
import sys
import wave

import cv2
import numpy as np

from conor_s001_rig import J, BONES

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 24
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
T = 1.1                      # seconds per full walk cycle (two steps)
GRID = 8                     # MLS evaluation grid (px)
ALPHA = 1.6                  # MLS locality

CON = cv2.imread(os.path.join(HERE, "conor_rgba.png"), cv2.IMREAD_UNCHANGED).astype(np.float32)
# background = original artwork everywhere outside Conor's rest silhouette (+4px for his ink outline);
# the rebuilt plate is only used where his limbs move away from where they were drawn
_clean = cv2.imread(os.path.join(HERE, "background_clean.png")).astype(np.float32)
_orig = cv2.imread(os.path.join(HERE, "plate.png")).astype(np.float32)
_rest = cv2.GaussianBlur(cv2.dilate((CON[..., 3] > 20).astype(np.uint8) * 255, np.ones((9, 9), np.uint8)), (7, 7), 0)
_rest = (_rest.astype(np.float32) / 255.0)[..., None]
BG = _orig * (1 - _rest) + _clean * _rest
rng = np.random.default_rng(3)

# ---------------------------------------------------------------- handles: joints + bone mid/third points
REST = dict(J)

# ---------------------------------------------------------------- walk cycle
def pose_at(t):
    ph = 2 * math.pi * t / T
    s = (1 - math.cos(ph)) / 2            # 0 = artwork pose (L leg forward), 1 = opposite contact
    D = 150.0                              # vertical foot separation front/back
    liftL = max(0.0, -math.sin(ph))        # L leg swings forward during second half
    liftR = max(0.0, math.sin(ph))         # R leg swings forward during first half
    bob = -12 * abs(math.sin(ph))          # body highest at passing
    sway = -9 * math.cos(ph)               # weight over stance leg
    tilt = 6 * math.cos(ph)                # pelvis tilt (swing-leg hip drops)
    d = {k: [0.0, 0.0] for k in J}

    def add(k, dx, dy):
        d[k][0] += dx
        d[k][1] += dy

    # legs
    add("an_L", 4 * s, -D * s - 22 * liftL); add("ft_L", 6 * s, -D * s - 30 * liftL)
    add("kn_L", 3 * s, -0.45 * D * s - 26 * liftL)
    add("an_R", -4 * s, D * s - 22 * liftR); add("ft_R", -6 * s, D * s - 30 * liftR)
    add("kn_R", -3 * s, 0.45 * D * s - 26 * liftR)
    # pelvis
    add("hip_L", sway, bob * 0.8 + tilt); add("hip_R", sway, bob * 0.8 - tilt); add("waist", sway, bob * 0.85)
    # torso, shoulders counter-rotate against the pelvis
    for k in ("chest", "neck"):
        add(k, sway * 0.3, bob)
    add("sh_L", sway * 0.2, bob - 0.8 * tilt); add("sh_R", sway * 0.2, bob + 0.8 * tilt)
    # arms: opposite to legs (R arm forward in the artwork, L arm forward at s=1); follow the shoulders
    for side, fw in (("L", s), ("R", 1 - s)):
        sk = "sh_" + side
        base = (d[sk][0], d[sk][1])
        sign = -1 if side == "L" else 1
        add("el_" + side, base[0], base[1] + 10 * (fw - .5))
        add("wr_" + side, base[0] + sign * 2 * (fw - .5), base[1] + 26 * (fw - .5))
        add("hd_" + side, base[0] + sign * 3 * (fw - .5), base[1] + 34 * (fw - .5))
    # head: follows the neck with a slight lag and a small tilt
    lag = -10 * abs(math.sin(ph - 0.35))
    for k, g in (("chin", 1.0), ("head", 1.0), ("crown", 1.0)):
        add(k, sway * 0.5 + (2.5 if k == "crown" else 1.2) * math.sin(ph + 0.4), lag)
    return {k: (REST[k][0] + d[k][0], REST[k][1] + d[k][1]) for k in J}, ph, s


# ---------------------------------------------------------------- layers + rigid MLS (backward mapping)
# Conor is split into three cut-out layers, each deformed only by its own skeleton chain:
#   TORSO (head, torso, arms, hips)  - drawn last (in front of the thighs)
#   LEG_L / LEG_R                    - depth order swaps at the passing pose (feet side by side)
YYc, XXc = np.mgrid[0:H, 0:W].astype(np.float32)
SPLIT_X = 600.0                                   # line between the legs (crotch -> feet gap)
leg_zone = np.clip((YYc - 1040) / 40, 0, 1)        # legs fully opaque from y=1080 ...
torso_keep = 1 - np.clip((YYc - 1100) / 60, 0, 1)   # ... torso fades out over them (1100-1160): no see-through seam
side_L = np.clip((SPLIT_X + 4 - XXc) / 3 + 0.5, 0, 1)   # 8px opaque overlap between the legs
side_R = np.clip((XXc - (SPLIT_X - 4)) / 3 + 0.5, 0, 1)
A = CON[..., 3] / 255.0
LAYERS = {
    "torso": np.dstack([CON[..., :3], 255 * A * torso_keep]),
    "leg_L": np.dstack([CON[..., :3], 255 * A * leg_zone * side_L]),
    "leg_R": np.dstack([CON[..., :3], 255 * A * leg_zone * side_R]),
}
CHAINS = {
    "torso": (["crown", "head", "chin", "neck", "chest", "waist", "sh_L", "el_L", "wr_L", "hd_L", "sh_R", "el_R",
               "wr_R", "hd_R", "hip_L", "hip_R"], (232, 1016, 16, 1256)),
    "leg_L": (["waist", "hip_L", "kn_L", "an_L", "ft_L"], (360, 744, 960, 1912)),
    "leg_R": (["waist", "hip_R", "kn_R", "an_R", "ft_R"], (480, 864, 960, 1912)),
}
_names = set(J)


def chain_points(pose, keys):
    pts = [pose[k] for k in keys]
    for a, b in BONES:
        if a in keys and b in keys:
            for f in (1 / 3, 2 / 3):
                pts.append((pose[a][0] * (1 - f) + pose[b][0] * f, pose[a][1] * (1 - f) + pose[b][1] * f))
    return np.array(pts, np.float64)


GRIDS = {}
for name, (keys, (x0, x1, y0, y1)) in CHAINS.items():
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1, GRID), np.arange(y0, y1 + 1, GRID))
    GRIDS[name] = (gx, gy, (gx + 1j * gy).ravel(), chain_points(REST, keys))


def mls_inverse(V, shape, q_def, p_rest):
    """Rigid MLS: map output points v (deformed space) back to source (rest) coordinates."""
    Pq = q_def[:, 0] + 1j * q_def[:, 1]
    Pp = p_rest[:, 0] + 1j * p_rest[:, 1]
    w = 1.0 / (np.abs(V[:, None] - Pq[None, :]) ** 2 + 1e-6) ** ALPHA
    ws = w.sum(1)
    qs = (w * Pq).sum(1) / ws
    ps = (w * Pp).sum(1) / ws
    m = (w * np.conj(Pq[None, :] - qs[:, None]) * (Pp[None, :] - ps[:, None])).sum(1)
    vv = V - qs
    f = m * vv
    out = np.abs(vv) * f / (np.abs(f) + 1e-9) + ps
    return out.real.reshape(shape).astype(np.float32), out.imag.reshape(shape).astype(np.float32)


def warp_layer(name, pose):
    keys, (x0, x1, y0, y1) = CHAINS[name]
    gx, gy, V, p_rest = GRIDS[name]
    sx, sy = mls_inverse(V, gx.shape, chain_points(pose, keys), p_rest)
    mx = np.full((H, W), -1.0, np.float32)
    my = np.full((H, W), -1.0, np.float32)
    mx[y0:y1 + 1, x0:x1 + 1] = cv2.resize(sx, (x1 - x0 + 1, y1 - y0 + 1), interpolation=cv2.INTER_LINEAR)
    my[y0:y1 + 1, x0:x1 + 1] = cv2.resize(sy, (x1 - x0 + 1, y1 - y0 + 1), interpolation=cv2.INTER_LINEAR)
    return cv2.remap(LAYERS[name], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def over(dst, layer):
    a = layer[..., 3:4] / 255.0
    return dst * (1 - a) + layer[..., :3] * a


# ---------------------------------------------------------------- environment
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
palm_L = np.clip(1 - np.hypot(XX - 60, YY - 40) / 520, 0, 1) ** 1.5 * (YY < 560)
palm_R = np.clip(1 - np.hypot(XX - 1030, YY - 60) / 380, 0, 1) ** 1.5 * (YY < 380)
pave = np.clip((YY - 1350) / 500, 0, 1)
gray = cv2.cvtColor(BG.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
cars = (((XX < 340) & (YY > 640) & (YY < 1500)) | ((XX > 770) & (YY > 680) & (YY < 1110))).astype(np.float32)
glint_mask = cars * np.clip((gray - 0.35) * 2.2, 0, 1)


def background(t):
    # backward dolly: background slowly recedes (scale 1.035 -> 1.0) around the vanishing area
    sc = 1.075 - 0.035 * (t / DUR)
    cx, cy = 600, 760
    mx = (XX - cx) / sc + cx
    my = (YY - cy) / sc + cy
    # palm fronds sway (two frequencies, falls off toward the trunks)
    mx += palm_L * (7 * np.sin(1.3 * t + YY / 90) + 3 * np.sin(2.9 * t + XX / 60))
    my += palm_L * 3 * np.sin(1.1 * t + XX / 80)
    mx += palm_R * (6 * np.sin(1.5 * t + 1 + YY / 70) + 2.5 * np.sin(3.3 * t + XX / 50))
    # heat shimmer on the paving
    mx += pave * 1.6 * np.sin(YY / 7 + t * 9)
    img = cv2.remap(BG, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # travelling specular glints on the cars
    band = np.exp(-((XX + 0.55 * YY - (-300 + 1700 * ((t * 0.32) % 1.4))) / 70) ** 2)
    band2 = np.exp(-((XX - 0.4 * YY - (200 + 1300 * ((t * 0.27 + 0.5) % 1.5))) / 55) ** 2)
    gl = cv2.remap(glint_mask, mx, my, cv2.INTER_LINEAR) * (band + 0.7 * band2)
    img += gl[..., None] * np.array([150, 205, 255], np.float32) * 0.9
    return img


def contact_shadows(img, pose, s, ph):
    sh = np.zeros((H, W), np.float32)
    for side, planted in (("L", 1 - s), ("R", s)):
        fx, fy = pose["ft_" + side]
        a = 0.18 + 0.32 * planted
        cv2.ellipse(sh, (int(fx), int(fy + 12)), (int(70 + 20 * planted), 16), 0, 0, 360, a, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 9)
    return img * (1 - sh[..., None])


VIG = (1 - 0.28 * np.clip(np.hypot((XX - W / 2) / W, (YY - H / 2) / H) * 1.6 - 0.3, 0, 1) ** 1.6)[..., None]


def frame(t):
    pose, ph, s = pose_at(t)
    img = background(t)
    img = contact_shadows(img, pose, s, ph)
    rim = 1.0 + 0.04 * math.sin(t * 1.7)          # subtle rim light breathing (sun behind camera-right)
    order = ["leg_R", "leg_L"] if s < 0.5 else ["leg_L", "leg_R"]   # front leg drawn last
    for name in order + ["torso"]:
        lay = warp_layer(name, pose)
        lay[..., :3] *= rim
        img = over(img, lay)
    img *= (1.0 + 0.02 * math.sin(t * 1.3)) * VIG
    img += rng.normal(0, 2.2, (H, W, 1)).astype(np.float32)      # film grain
    return np.clip(img, 0, 255).astype(np.uint8)


def audio(path):
    sr = 48000
    n = int(DUR * sr)
    t = np.arange(n) / sr
    noise = rng.normal(0, 1, n)
    sea = np.convolve(noise, np.ones(500) / 500, mode="same") * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * t)) * 0.35
    pad = sum(np.sin(2 * np.pi * f * t + p) for f, p in ((110, 0), (164.8, 1), (220, 2), (329.6, 1.5))) * 0.03
    pad *= np.clip(t / 1.5, 0, 1)
    sig = sea + pad
    # footsteps exactly on foot contacts (phase 0 and pi -> every T/2)
    k = 0.0
    while k < DUR:
        i = int(k * sr)
        tt = np.arange(int(0.16 * sr)) / sr
        step = (np.sin(2 * np.pi * 85 * tt) * 0.6 + rng.normal(0, 0.4, len(tt))) * np.exp(-tt / 0.035) * 0.35
        sig[i:i + len(step)] += step[:n - i]
        k += T / 2
    sig *= np.clip((DUR - t) / 0.4, 0, 1)
    sig = sig / np.abs(sig).max() * 0.8
    pcm = (np.stack([sig, np.roll(sig, 20)], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    pic = os.path.join(out, "_s001_pic.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", pic], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    wav = os.path.join(out, "_s001.wav")
    audio(wav)
    final = os.path.join(out, "S001_walk_poc.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", final], check=True)
    print(final)
