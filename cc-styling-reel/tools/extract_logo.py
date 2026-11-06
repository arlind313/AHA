"""Lift the CC Styling logo off the dark reference background (no redesign).
Replace assets/logo.png with the original vector/PNG logo for best quality."""
import numpy as np
from PIL import Image
im = Image.open('assets/reference.png').convert('RGB').crop((200, 48, 925, 138))
im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
a = np.asarray(im).astype(np.float32)
bg = np.median(a[:12].reshape(-1, 3), axis=0)
d = np.clip((a - bg).max(axis=2), 0, None)
alpha = np.clip((d - 18) / (200 - 18), 0, 1)
red = (a[..., 0] - a[..., 1]) > 90
col = np.where(red[..., None], np.array([227, 6, 19], np.float32), np.array([255, 255, 255], np.float32))
out = np.dstack([col, alpha * 255]).astype(np.uint8)
img = Image.fromarray(out, 'RGBA')
img = img.crop(img.getbbox())
img.save('assets/logo.png'); print(img.size)
