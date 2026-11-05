"""Build S001 layers from plate.png: Conor matte (RGBA) and a clean background plate (Conor removed)."""
import cv2, numpy as np
from conor_s001_rig import J, BONES
img = cv2.imread('plate.png'); H, W = img.shape[:2]
mask = np.full((H, W), cv2.GC_BGD, np.uint8)
hull = cv2.convexHull(np.array(list(J.values()), np.int32))
pr = np.zeros((H, W), np.uint8); cv2.fillPoly(pr, [hull], 1); pr = cv2.dilate(pr, np.ones((61, 61), np.uint8))
mask[pr > 0] = cv2.GC_PR_BGD
cv2.fillPoly(mask, [hull], cv2.GC_PR_FGD)
for a, b in BONES:
    cv2.line(mask, J[a], J[b], cv2.GC_FGD, 26)
cv2.circle(mask, J["head"], 70, cv2.GC_FGD, -1)
cv2.ellipse(mask, (595, 700), (150, 230), 0, 0, 360, cv2.GC_FGD, -1)
cv2.ellipse(mask, (533, 1795), (74, 88), 0, 0, 360, cv2.GC_FGD, -1)      # front shoe
cv2.rectangle(mask, (452, 66), (594, 110), cv2.GC_FGD, -1)                 # sunglasses on head
cv2.ellipse(mask, (528, 118), (78, 52), 0, 0, 360, cv2.GC_FGD, -1)           # hair top
cv2.rectangle(mask, (345, 1152), (398, 1240), cv2.GC_BGD, -1)              # orange-car sliver
bgd = np.zeros((1, 65)); fgd = np.zeros((1, 65))
cv2.grabCut(img, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
fg = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
fg = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
# soft matte edge (keeps the ink outline, avoids a cut-out halo)
fg = cv2.dilate(fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))   # include ink outline + rim light
alpha = cv2.GaussianBlur(fg, (5, 5), 0)
rgba = np.dstack([img, alpha]); cv2.imwrite('conor_rgba.png', rgba)
# clean plate: remove Conor (dilated) and rebuild the background behind him
hole = cv2.dilate(fg, np.ones((11, 11), np.uint8))
cv2.ellipse(hole, (540, 1812), (95, 115), 0, 0, 360, 255, -1)
cv2.ellipse(hole, (660, 1650), (85, 95), 0, 0, 360, 255, -1)
cv2.ellipse(hole, (528, 92), (105, 62), 0, 0, 360, 255, -1)        # head top + sunglasses
small = cv2.resize(img, (W // 2, H // 2)); hs = cv2.resize(hole, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
bg_s = cv2.inpaint(small, hs, 15, cv2.INPAINT_TELEA)
bg = img.copy(); up = cv2.resize(bg_s, (W, H), interpolation=cv2.INTER_CUBIC)
bg[hole > 0] = up[hole > 0]
# above the paving: row-wise fill from the nearest real pixel outward (continues the horizontal lines of sea,
# hedge and car bodies behind the arms instead of a blurry inpaint)
upper = bg.copy()
for y in range(0, 1181):
    row = hole[y] > 0
    if not row.any():
        continue
    xs_ = np.where(row)[0]
    free = np.where(~row)[0]
    if free.size == 0:
        continue
    for x in xs_:
        if x >= 600:
            r = free[free > x]
            src_x = r[0] if r.size else free[free < x][-1]
        else:
            l = free[free < x]
            src_x = l[-1] if l.size else free[free > x][0]
        # sample a few px further out so the ink outline isn't smeared in
        off = 24 if src_x > x else -24
        upper[y, x] = img[y, int(np.clip(src_x + off, 0, W - 1))]
uz = np.zeros((H, W), np.float32); uz[:1181][hole[:1181] > 0] = 1
upper = cv2.GaussianBlur(upper, (1, 9), 0)
uz = cv2.GaussianBlur(uz, (0, 0), 3)[..., None]
bg = (bg * (1 - uz) + upper * uz).astype(np.uint8)
# below the shoulders: clone real background from the same rows beside him (outward first), keeps perspective
rows = np.arange(H)[:, None]
zone = (hole > 0) & (rows > 1180)
ys, xs = np.where(zone)
src = bg.copy()
left = xs < 600
todo = np.ones(len(xs), bool)
for k in range(4):
    for side, offs in ((~left, (110, 160, 330, 420)), (left, (-110, -160, -330, -420))):
        off = offs[k]
        sel = todo & side
        xx = xs + off
        ok = sel & (xx >= 40) & (xx < W - 40)
        ok[ok] = hole[ys[ok], xx[ok]] == 0
        src[ys[ok], xs[ok]] = img[ys[ok], xx[ok]]
        todo &= ~ok
pv = np.zeros((H, W), np.float32); pv[zone] = 1
pv = cv2.GaussianBlur(pv, (0, 0), 5)[..., None]
bg = (bg * (1 - pv) + src * pv).astype(np.uint8)
cv2.imwrite('background_clean.png', bg)
# contact shadow mask reference: feet
print('layers ok', (fg > 0).sum())
vis = np.hstack([cv2.resize(bg, (540, 960)), cv2.resize(cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR), (540, 960))])
cv2.imwrite('/tmp/claude-0/layers.png', vis)
