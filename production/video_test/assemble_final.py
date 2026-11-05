"""Assemble the 21s cold-open test from image-to-video clips, narration and music.

Inputs (all optional, each falls back automatically):
  inbox/clips/S001.mp4, S002.mp4, S003.mp4   -> else the animatic shot is used
  inbox/vo/S001.(wav|mp3), S002..., S003...  -> else burned-in temp subtitles
  inbox/music/music.(mp3|wav)                -> else the temp sound bed from render_animatic.py

Run from repo root: python3 production/video_test/assemble_final.py
"""
import glob
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
INBOX, OUT = os.path.join(HERE, "inbox"), os.path.join(HERE, "out")
W, H, FPS, TOTAL = 1080, 1920, 30, 21.0
SHOTS = [("S001", 0.0, 5.0, 0.3, "People see the cars, the events, the villas in Marbella."),
         ("S002", 5.0, 9.5, 5.2, "What they don't see is a tyre shop in Ireland,\na ferry to Holyhead,\nand a lot of very expensive mistakes."),
         ("S003", 14.5, 6.5, 14.8, "My name is Conor Callaghan.\nAnd this is how it started.")]
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def find(pattern):
    hits = sorted(glob.glob(os.path.join(INBOX, pattern)))
    return hits[0] if hits else None


def text_png(path, lines, font, y0, spacing=0, shadow=True, box=False, rule=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (txt, f, dy) in enumerate(lines):
        chars = list(txt)
        widths = [d.textlength(c, font=f) for c in chars]
        total = sum(widths) + spacing * (len(chars) - 1)
        x = W / 2 - total / 2
        y = y0 + dy
        if box:
            d.rectangle([x - 14, y - 6, x + total + 14, y + f.size + 8], fill=(0, 0, 0, 140))
        for c, cw in zip(chars, widths):
            if shadow:
                d.text((x + 3, y + 4), c, font=f, fill=(0, 0, 0, 160))
            d.text((x, y), c, font=f, fill=(245, 240, 228, 255))
            x += cw + spacing
    if rule:
        d.line([(W / 2 - 160, y0 + 110), (W / 2 + 160, y0 + 110)], fill=(245, 240, 228, 200), width=3)
    im.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    animatic = os.path.join(OUT, "picture.mp4")
    if not os.path.exists(animatic) or not os.path.exists(os.path.join(OUT, "temp_sound.wav")):
        subprocess.run(["python3", os.path.join(HERE, "render_animatic.py")], check=True)
    title = os.path.join(OUT, "_title.png")
    text_png(title, [("THE IRISH GRAFT", ImageFont.truetype(SERIF, 84), 0), ("PART 1", ImageFont.truetype(SERIF, 46), 130)],
             None, 770, spacing=6, rule=True)

    inputs, vf, used, fallback = [], [], [], set()
    # ---- picture: one input per shot
    for k, (sid, start, dur, _, _) in enumerate(SHOTS):
        clip = find(f"clips/{sid}.mp4")
        if clip:
            inputs += ["-i", clip]
            used.append(f"{sid}: I2V clip")
            vf.append(f"[{k}:v]trim=0:{dur},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
                      f"crop={W}:{H},setsar=1[v{k}]")
        else:
            inputs += ["-i", animatic]
            used.append(f"{sid}: animatic fallback")
            fallback.add(sid)
            vf.append(f"[{k}:v]trim={start}:{start + dur},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},setsar=1[v{k}]")
    vf.append("[v0][v1][v2]concat=n=3:v=1:a=0[pic]")
    n = len(SHOTS)
    inputs += ["-loop", "1", "-t", str(TOTAL), "-i", title]
    vf.append(f"[{n}:v]format=rgba,fade=t=in:st=16.6:d=1.2:alpha=1[ttl]")
    vf.append("[pic][ttl]overlay=0:0:enable='gte(t,16.6)'[pt]")
    last, idx = "pt", n + 1

    # ---- narration (or temp subtitles)
    vo_streams = []
    for k, (sid, _, _, at, line) in enumerate(SHOTS):
        vo = find(f"vo/{sid}.*")
        if vo:
            inputs += ["-i", vo]
            vo_streams.append(f"[{idx}:a]adelay={int(at * 1000)}|{int(at * 1000)},aformat=channel_layouts=stereo[vo{k}]")
            used.append(f"{sid}: VO {os.path.basename(vo)}")
            idx += 1
        elif sid in fallback:
            used.append(f"{sid}: subtitle already in animatic")
        else:
            png = os.path.join(OUT, f"_sub_{sid}.png")
            f = ImageFont.truetype(SANS, 40)
            text_png(png, [(ln, f, i * 54) for i, ln in enumerate(line.split("\n"))], None, 1590, shadow=False, box=True)
            inputs += ["-loop", "1", "-t", str(TOTAL), "-i", png]
            end = SHOTS[k][1] + SHOTS[k][2] - 0.3 if k < 2 else 16.4
            vf.append(f"[{last}][{idx}:v]overlay=0:0:enable='between(t,{at},{end})'[s{k}]")
            last, idx = f"s{k}", idx + 1
            used.append(f"{sid}: temp subtitle (no VO file)")

    # ---- music / sound bed
    music = find("music/music.*")
    bed = music or os.path.join(OUT, "temp_sound.wav")
    inputs += ["-i", bed]
    used.append(f"music: {os.path.basename(bed)}")
    gain = "0.45" if vo_streams else "1.0"                      # duck the bed under narration
    af = [f"[{idx}:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,volume={gain},aformat=channel_layouts=stereo[bed]"] + vo_streams
    mix_in = "[bed]" + "".join(f"[vo{k}]" for k in range(len(vo_streams)))
    af.append(f"{mix_in}amix=inputs={1 + len(vo_streams)}:normalize=0,afade=t=out:st={TOTAL - 0.8}:d=0.8[aout]")
    vf.append(f"[{last}]fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL - 0.8}:d=0.8,format=yuv420p[vout]")

    out = os.path.join(OUT, "IRISH_GRAFT_P1_COLD_OPEN_v1.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(vf + af),
           "-map", "[vout]", "-map", "[aout]", "-t", str(TOTAL), "-r", str(FPS), "-c:v", "libx264", "-crf", "18",
           "-preset", "medium", "-c:a", "aac", "-b:a", "192k", out]
    subprocess.run(cmd, check=True)
    print("\n".join(used))
    print("->", out)


if __name__ == "__main__":
    main()
