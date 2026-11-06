import sys, glob
from PIL import Image, ImageDraw
files = sys.argv[2:] or sorted(glob.glob('out/stills/*.png'))
w = 540; h = 960
sheet = Image.new('RGB', (w * len(files), h + 30), 'black')
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((w, h))
    sheet.paste(im, (i * w, 30)); ImageDraw.Draw(sheet).text((i * w + 10, 8), f.split('/')[-1], fill='white')
sheet.save(sys.argv[1])
