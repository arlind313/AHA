"""Build all production documents from storyboard_data.py.

Usage: python3 production/build.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import storyboard_data as D  # noqa: E402

WPS = 2.5  # comfortable documentary narration pace (150 wpm)
CH = {c[0]: dict(id=c[0], title=c[1], period=c[2], grade=c[3], music=c[4]) for c in D.CHAPTERS}
SHOT = {s["id"]: s for s in D.SHOTS}


def words(t):
    return len(t.split())


def mmss(sec):
    return f"{int(sec // 60)}:{int(round(sec % 60)):02d}"


def chars_text(codes):
    names = {"YC": "Young Conor", "C2": "Conor (early 20s)", "AC": "Adult Conor", "FA": "Father",
             "MO": "Mother", "AR": "Arlind", "EX": "Extras"}
    return ", ".join(names[c] for c in codes)


def needs_civic(s):
    return "Civic" in s["comp"] + s["act"]


def needs_father_car(s):
    return "father's car" in s["comp"].lower()


# --------------------------------------------------------------------------- timing
problems = []
start = 0.0
for s in D.SHOTS:
    s["start"] = start
    start += s["dur"]
    need = words(s["vo"]) / WPS
    if s["vo"] and need > s["dur"] - 0.5:
        problems.append(f"{s['id']}: {words(s['vo'])} words needs {need:.1f}s but shot is {s['dur']}s")
TOTAL = start
if problems:
    print("TIMING PROBLEMS:\n" + "\n".join(problems))
    sys.exit(1)

assert sorted(sum(D.PAGES, [])) == sorted(SHOT), "every shot must be on exactly one page"

# --------------------------------------------------------------------------- 01 narration
out = ["# THE IRISH GRAFT - PART 1", "## 01 - Full Narration (Conor, first person)", "",
       "Read at a natural documentary pace (~150 words per minute). Shot IDs are shown in brackets so the VO can be",
       "recorded line by line and dropped onto the timeline. Lines marked * contain details to CONFIRM (see README).", ""]
tw = 0
for cid, c in CH.items():
    shots = [s for s in D.SHOTS if s["ch"] == cid]
    dur = sum(s["dur"] for s in shots)
    w = sum(words(s["vo"]) for s in shots)
    tw += w
    out += [f"### {cid} - {c['title']}  ({c['period']})", f"_Runtime {mmss(dur)} - {w} words_", ""]
    for s in shots:
        flag = " *" if s["note"].startswith("CONFIRM") or "CONFIRM" in s["note"] else ""
        line = s["vo"] if s["vo"] else "_(no narration - music / sound only)_"
        out.append(f"[{s['id']}] {line}{flag}  ")
    out.append("")
out += ["---", f"**Total narration:** {tw} words (~{mmss(tw / WPS)} spoken) inside a picture runtime of **{mmss(TOTAL)}**.", ""]
open(os.path.join(HERE, "01_narration.md"), "w").write("\n".join(out))

# --------------------------------------------------------------------------- 02 storyboard
out = ["# THE IRISH GRAFT - PART 1", "## 02 - Master Storyboard", "",
       f"{len(D.SHOTS)} shots - {len(CH)} chapters - total runtime **{mmss(TOTAL)}** (target 12:00-14:00).", "",
       "| Chapter | Title | Period | Shots | Runtime |", "|---|---|---|---|---|"]
for cid, c in CH.items():
    shots = [s for s in D.SHOTS if s["ch"] == cid]
    out.append(f"| {cid} | {c['title']} | {c['period']} | {shots[0]['id']}-{shots[-1]['id']} ({len(shots)}) | {mmss(sum(s['dur'] for s in shots))} |")
out.append("")
for cid, c in CH.items():
    out += ["---", f"## {cid} - {c['title']}", f"**Period:** {c['period']}  ", f"**Colour grade:** {c['grade']}  ",
            f"**Music direction:** {c['music']}", ""]
    for s in (s for s in D.SHOTS if s["ch"] == cid):
        out += [f"### {s['id']} - {cid} - {s['dur']}s  (TC {mmss(s['start'])}-{mmss(s['start'] + s['dur'])})",
                f"- **Voice-over:** {('\"' + s['vo'] + '\"') if s['vo'] else '(none)'}",
                f"- **Characters:** {chars_text(s['chars'])}",
                f"- **Composition:** {s['comp']}",
                f"- **Location & period:** {s['loc']}",
                f"- **Character action:** {s['act']}",
                f"- **Animation:** {s['anim']}",
                f"- **Camera:** {s['cam']}",
                f"- **Sound effects:** {s['sfx']}",
                f"- **Music:** {s['mus'] or 'Chapter cue continues.'}"]
        if s["note"]:
            out.append(f"- **Note:** {s['note']}")
        out.append("")
open(os.path.join(HERE, "02_master_storyboard.md"), "w").write("\n".join(out))

# --------------------------------------------------------------------------- 03 comic pages
LAYOUT3 = ("LAYOUT: landscape 3:2 page (1536x1024). Three equal tall vertical panels side by side, read left to right, "
           "each panel framed as a 9:16 vertical film shot. Thin black panel borders, slim white gutters, white page margin.")
LAYOUT4 = ("LAYOUT: portrait 2:3 page (1024x1536). Four equal panels in a 2x2 grid, read left-to-right then top-to-bottom. "
           "Keep each panel's key action inside a central vertical 9:16 safe area. Thin black panel borders, slim white gutters, white page margin.")
POS3 = ["LEFT", "CENTRE", "RIGHT"]
POS4 = ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-LEFT", "BOTTOM-RIGHT"]

index = ["# THE IRISH GRAFT - PART 1", "## 03 - Comic Storyboard Pages (ChatGPT image prompts)", "",
         "How to generate each page in ChatGPT:",
         "1. Upload `references/conor-character-sheet.png` (plus any approved earlier page or frame of the same era as a second reference).",
         "2. Paste the page prompt exactly as written below (each prompt is complete on its own).",
         "3. If a face drifts, reply: \"Keep everything the same but match Conor's face exactly to the uploaded sheet\" rather than regenerating from scratch.",
         "4. Save as `PAGE_XX.png` and tick it off in the approval table at the end.", "",
         "Pages are planning assets, not final frames. Final 9:16 frames are prepared in 04_animation_prep.md after approval.", ""]
for n, ids in enumerate(D.PAGES, 1):
    shots = [SHOT[i] for i in ids]
    chs = sorted({s["ch"] for s in shots})
    codes = []
    for s in shots:
        for c in s["chars"]:
            if c not in codes:
                codes.append(c)
    layout, pos = (LAYOUT3, POS3) if len(ids) == 3 else (LAYOUT4, POS4)
    p = [f"Create ONE cinematic graphic-novel storyboard page for the animated documentary 'The Irish Graft - Part 1' "
         f"({' / '.join(CH[c]['title'] for c in chs)}, {' / '.join(CH[c]['period'] for c in chs)}).",
         "", "STYLE: " + D.STYLE, "", layout, "",
         "COLOUR GRADE: " + " ".join(CH[c]["grade"] for c in chs), "",
         "IDENTITY: the uploaded comic character sheet is the ONLY face reference for Conor. Do not redesign him.", "",
         "CHARACTERS ON THIS PAGE (keep identical in every panel):"]
    p += ["- " + D.CHARACTERS[c] for c in codes]
    if any(needs_civic(s) for s in shots):
        p.append("- " + D.CAR_CIVIC)
    if any(needs_father_car(s) for s in shots):
        p.append("- " + D.FATHER_CAR)
    p.append("")
    for k, s in enumerate(shots):
        p.append(f"PANEL {k + 1} ({pos[k]}): {s['comp']} Action frozen at its key moment: {s['act']} Setting: {s['loc']}.")
    p += ["", D.RULES]
    prompt = "\n".join(p)
    fname = f"PAGE_{n:02d}.txt"
    open(os.path.join(HERE, "03_comic_pages", fname), "w").write(prompt + "\n")
    index += ["---", f"### PAGE {n:02d} - shots {ids[0]}-{ids[-1]} - {len(ids)} panels - {', '.join(CH[c]['title'] for c in chs)}",
              f"File: `03_comic_pages/{fname}`", "", "```", prompt, "```", ""]
index += ["---", "## Page approval table", "", "| Page | Shots | Faces consistent | Era/age correct | No text/logos | Approved |", "|---|---|---|---|---|---|"]
for n, ids in enumerate(D.PAGES, 1):
    index.append(f"| {n:02d} | {ids[0]}-{ids[-1]} | ☐ | ☐ | ☐ | ☐ |")
open(os.path.join(HERE, "03_comic_pages.md"), "w").write("\n".join(index) + "\n")

# --------------------------------------------------------------------------- 04 animation prep
REUSE = {"S003": "Frame-match S002 (same hand position and framing) for the match cut.",
         "S007": "Use Preview 01 (once approved) as reference.", "S010": "Use Preview 02 (once approved) as reference.",
         "S013": "Use Preview 03 (once approved) as reference.", "S051": "Mirror the framing of S016.",
         "S089": "Re-use the approved S010 frame; add a warm vignette in compositing."}
page_of = {i: n for n, ids in enumerate(D.PAGES, 1) for i in ids}
out = ["# THE IRISH GRAFT - PART 1", "## 04 - Animation Preparation (USE ONLY AFTER PAGE APPROVAL)", "",
       "Every shot gets its own full-screen 9:16 key frame (1080x1920 minimum), generated fresh using the approved comic page",
       "panel as the layout reference - not cropped from the page, which is too low resolution.", "",
       "**Motion principle:** movement comes from the characters and environment (hands, heads, breath, weather, vehicles,",
       "light), animated with image-to-video using a START frame and, where the action changes pose, an END frame.",
       "Camera moves are small and motivated, never a slow zoom standing in for animation.", "",
       "**Layer split for compositing:** generate BG / character / FG elements separately only where marked, so parallax",
       "and weather can be added in the edit without warping faces.", "",
       "**Frame prompt template:** `[STYLE] Single full-bleed 9:16 vertical frame, 1080x1920, no panel borders. [CHARACTER LOCKS] "
       "[Composition] [Action - START pose] Setting: [Location]. [COLOUR GRADE] [RULES]` - for the END frame, swap in the end pose.", "",
       "| Shot | Page | Dur | Key frames | Start pose -> End pose | Animated movement | Camera | Layers | Notes |",
       "|---|---|---|---|---|---|---|---|---|"]
two_kf_words = ("turns", "jumps", "stands", "walks", "hug", "opens", "raises", "lifts", "rises", "closes", "drops", "wipes", "jolts", "stops", "pats", "tears")
for s in D.SHOTS:
    kf = 2 if any(w in s["act"].lower() for w in two_kf_words) else 1
    layers = "BG + char + FG" if ("rain" in s["anim"].lower() or "track" in s["cam"].lower() or "dolly" in s["cam"].lower()) else "single"
    pose = s["act"] if kf == 2 else "Hold pose with secondary motion"
    out.append(f"| {s['id']} | {page_of[s['id']]:02d} | {s['dur']}s | {kf} | {pose} | {s['anim']} | {s['cam']} | {layers} | {REUSE.get(s['id'], '')} |")
out += ["", f"**Totals:** {len(D.SHOTS)} shots, {sum(2 if any(w in s['act'].lower() for w in two_kf_words) else 1 for s in D.SHOTS)} key frames to generate, runtime {mmss(TOTAL)}.", ""]
open(os.path.join(HERE, "04_animation_prep.md"), "w").write("\n".join(out))

print(f"OK: {len(D.SHOTS)} shots, {len(D.PAGES)} pages, runtime {mmss(TOTAL)}, narration {tw} words (~{mmss(tw / WPS)})")

# --------------------------------------------------------------------------- README
rd = ["# THE IRISH GRAFT - PART 1 - Production Blueprint (DRAFT v0.1, awaiting approval)", "",
      f"9:16 vertical animated graphic-novel documentary - **{len(D.SHOTS)} shots, {len(CH)} chapters, {len(D.PAGES)} comic pages, runtime {mmss(TOTAL)}**.",
      f"Narration: {tw} words (~{mmss(tw / WPS)} spoken at 150 wpm); the rest is deliberate music/sound beats.", "",
      "## Files", "",
      "| File | Phase | Contents |", "|---|---|---|",
      "| `01_narration.md` | 1 | Full first-person VO script in Conor's voice, by chapter |",
      "| `02_master_storyboard.md` | 2 | Every shot: chapter, duration, timecode, VO, characters, composition, location, action, animation, camera, SFX, music |",
      "| `03_comic_pages.md` + `03_comic_pages/PAGE_XX.txt` | 3 | One complete ChatGPT image prompt per comic page (3-4 panels each) + approval table |",
      "| `04_animation_prep.md` | 4 | Per-shot 9:16 key-frame list and motion brief - use only after page approval |",
      "| `storyboard_data.py` / `build.py` | - | Single source of truth; edit data, run `python3 production/build.py` to regenerate everything |", "",
      "## Character designs", ""]
rd += [f"- **{k}** - {v}" for k, v in D.CHARACTERS.items()]
rd += ["", "## Open questions (please answer before page generation)", ""]
rd += [f"{i}. {q}" for i, q in enumerate(D.OPEN_QUESTIONS, 1)]
rd += ["", "## Shots flagged CONFIRM", ""]
rd += [f"- **{s['id']}** - {s['note']}" for s in D.SHOTS if "CONFIRM" in s["note"]]
rd += ["", "Status: nothing has been generated or animated. Waiting for approval of narration, storyboard and page prompts.", ""]
open(os.path.join(HERE, "README.md"), "w").write("\n".join(rd))
