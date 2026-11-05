"""Build all production documents from storyboard_data.py.

Usage: python3 production/build.py
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import storyboard_data as D  # noqa: E402

WPS = 2.5   # documentary narration pace: 150 words per minute
PAD = 0.8   # breath between lines
MIN_DUR = 3.0
VERSION = "v0.4"

CH = {c[0]: dict(id=c[0], title=c[1], period=c[2], grade=c[3], music=c[4]) for c in D.CHAPTERS}
NAMES = {"KC": "Child Conor (flashback)", "YC": "Young Conor", "C2": "Conor (early 20s)", "AC": "Adult Conor", "FA": "Father",
         "MO": "Mother", "AR": "Arlind", "EX": "Extras"}


def words(t):
    return len(t.split())


def mmss(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


# --------------------------------------------------------------------------- ids, durations, timecodes
tags = {}
for n, s in enumerate(D.SHOTS, 1):
    s["id"] = f"S{n:03d}"
    if s["tag"]:
        assert s["tag"] not in tags, f"duplicate tag {s['tag']}"
        tags[s["tag"]] = s["id"]
for s in D.SHOTS:
    for k in ("comp", "act", "anim", "cam", "sfx", "note", "mus", "loc"):
        s[k] = re.sub(r"\{(\w+)\}", lambda m: tags[m.group(1)], s[k])
    s["speak"] = words(s["vo"]) / WPS
    if s["dur"] is None:
        assert s["vo"], f"{s['id']} has no VO and no explicit dur"
        s["dur"] = max(MIN_DUR, math.ceil((s["speak"] + PAD + s["hold"]) * 2) / 2)  # round up to 0.5s
    assert s["dur"] >= s["speak"], f"{s['id']} too short for its VO"
t = 0.0
for s in D.SHOTS:
    s["start"] = t
    t += s["dur"]
TOTAL = t
TW = sum(words(s["vo"]) for s in D.SHOTS)
SPOKEN = TW / WPS


def fmt_dur(d):
    return f"{d:g}s"


# --------------------------------------------------------------------------- automatic pagination (3-5 panels, per chapter)
def split(n):
    if n <= 5:
        return [n]
    for fours in range(n // 4, -1, -1):
        rest = n - 4 * fours
        if rest % 3 == 0:
            return [4] * fours + [3] * (rest // 3)
    return [4] * (n // 4 - 1) + [5]  # e.g. n where only a 5 fits


PAGES = []
for cid in CH:
    shots = [s for s in D.SHOTS if s["ch"] == cid]
    i = 0
    for size in split(len(shots)):
        PAGES.append(shots[i:i + size])
        i += size
for n, page in enumerate(PAGES, 1):
    for s in page:
        s["page"] = n

# --------------------------------------------------------------------------- 01 narration
out = [f"# THE IRISH GRAFT - PART 1  ({VERSION})", "## 01 - Full Narration (Conor, first person)", "",
       "Natural documentary pace (~150 words per minute). Shot IDs in brackets let the VO be recorded line by line",
       "and dropped onto the timeline. Lines marked * touch a detail still to CONFIRM (see README).", ""]
for cid, c in CH.items():
    shots = [s for s in D.SHOTS if s["ch"] == cid]
    out += [f"### {cid} - {c['title']}  ({c['period']})",
            f"_Runtime {mmss(sum(s['dur'] for s in shots))} - {sum(words(s['vo']) for s in shots)} words_", ""]
    for s in shots:
        flag = " *" if "CONFIRM" in s["note"] else ""
        line = s["vo"] if s["vo"] else "_(no narration - picture, music and sound)_"
        out.append(f"[{s['id']}] {line}{flag}  ")
    out.append("")
out += ["---", f"**Total narration:** {TW} words, ~{mmss(SPOKEN)} spoken, inside a picture runtime of **{mmss(TOTAL)}** "
        f"({SPOKEN / TOTAL:.0%} narration density).", ""]
open(os.path.join(HERE, "01_narration.md"), "w").write("\n".join(out))

# --------------------------------------------------------------------------- 02 storyboard
out = [f"# THE IRISH GRAFT - PART 1  ({VERSION})", "## 02 - Master Storyboard", "",
       f"{len(D.SHOTS)} shots - {len(CH)} chapters - total runtime **{mmss(TOTAL)}**.", "",
       "Durations are calculated from the narration (150 wpm) plus a 0.8s breath; emotional and comic beats carry a",
       "deliberate extra hold, listed per shot.", "",
       "| Chapter | Title | Period | Shots | Runtime |", "|---|---|---|---|---|"]
for cid, c in CH.items():
    shots = [s for s in D.SHOTS if s["ch"] == cid]
    out.append(f"| {cid} | {c['title']} | {c['period']} | {shots[0]['id']}-{shots[-1]['id']} ({len(shots)}) | "
               f"{mmss(sum(s['dur'] for s in shots))} |")
out.append("")
for cid, c in CH.items():
    out += ["---", f"## {cid} - {c['title']}", f"**Period:** {c['period']}  ", f"**Colour grade:** {c['grade']}  ",
            f"**Music direction:** {c['music']}", ""]
    for s in (s for s in D.SHOTS if s["ch"] == cid):
        hold = f", incl. {s['hold']:g}s hold" if s["hold"] else ""
        vo = f'"{s["vo"]}"' if s["vo"] else "(none)"
        out += [f"### {s['id']} - {cid} - {fmt_dur(s['dur'])}{hold}  (TC {mmss(s['start'])}-{mmss(s['start'] + s['dur'])}, page {s['page']:02d})",
                f"- **Voice-over:** {vo}",
                f"- **Characters:** {', '.join(NAMES[c] for c in s['chars'])}",
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
LAYOUT = {
    3: ("LAYOUT: landscape 3:2 page (1536x1024). Three equal tall vertical panels side by side, read left to right, each "
        "framed as a 9:16 vertical film shot.", ["LEFT", "CENTRE", "RIGHT"]),
    4: ("LAYOUT: portrait 2:3 page (1024x1536). Four equal panels in a 2x2 grid, read left-to-right then top-to-bottom. "
        "Keep each panel's key action inside a central vertical 9:16 safe area.",
        ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-LEFT", "BOTTOM-RIGHT"]),
    5: ("LAYOUT: portrait 2:3 page (1024x1536). Five panels: two equal panels across the top row, three equal panels "
        "across the bottom row, read left-to-right then top-to-bottom. Keep each panel's key action inside a central "
        "vertical safe area.", ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-LEFT", "BOTTOM-CENTRE", "BOTTOM-RIGHT"]),
}
BORDER = " Thin black panel borders, slim white gutters, white page margin."
for f in os.listdir(os.path.join(HERE, "03_comic_pages")):
    if f.startswith("PAGE_"):
        os.remove(os.path.join(HERE, "03_comic_pages", f))


REF_LABEL = {D.REFERENCES["CONOR"]: "Conor comic character sheet",
             D.REFERENCES["MOTHER"]: "Conor's mother comic character sheet",
             D.REFERENCES["ARLIND"]: "Arlind comic character sheet",
             D.REFERENCES["FLEET"]: "approved CC Marbella Rentals fleet vehicle images (if attached)"}


def refs_for(codes, shots):
    r = []
    if {"KC", "YC", "C2", "AC"} & set(codes):
        r.append(D.REFERENCES["CONOR"])
    if "MO" in codes:
        r.append(D.REFERENCES["MOTHER"])
    if "AR" in codes:
        r.append(D.REFERENCES["ARLIND"])
    if any(s["ch"] in ("CH00", "CH13") and ("fleet" in s["comp"].lower() or "rental" in s["comp"].lower()) for s in shots):
        r.append(D.REFERENCES["FLEET"])
    return r


index = [f"# THE IRISH GRAFT - PART 1  ({VERSION})", "## 03 - Comic Storyboard Pages (ChatGPT image prompts)", "",
         "How to generate each page in ChatGPT:",
         "1. Upload the reference files listed for that page (and, for consistency, the last approved page of the same era).",
         "2. Paste the page prompt exactly as written (each prompt is complete on its own).",
         "3. If a face drifts, reply: \"Keep everything the same but match the faces exactly to the uploaded sheets\" rather than regenerating from scratch.",
         "4. Save as `PAGE_XX.png` and tick it off in the approval table at the end.", "",
         "Pages are planning assets, not final frames. Final 9:16 frames are prepared in 04_animation_prep.md after approval.", "",
         "**Generation order:** only Page 01 is cleared for generation (see `05_page_tests/PAGE_01_PACKAGE.md`). Each later page is released one at a time after the previous page is approved.", ""]
for n, shots in enumerate(PAGES, 1):
    chs = list(dict.fromkeys(s["ch"] for s in shots))
    codes = list(dict.fromkeys(c for s in shots for c in s["chars"]))
    refs = refs_for(codes, shots)
    layout, pos = LAYOUT[len(shots)]
    text = " ".join(s["comp"] + s["act"] for s in shots)
    p = [f"Create ONE cinematic graphic-novel storyboard page for the animated documentary 'The Irish Graft - Part 1' "
         f"({' / '.join(CH[c]['title'] for c in chs)}, {' / '.join(CH[c]['period'] for c in chs)}).",
         "", "STYLE: " + D.STYLE, "", layout + BORDER, "",
         "COLOUR GRADE: " + " ".join(CH[c]["grade"] for c in chs), "",
         "REFERENCE IMAGES ATTACHED (in upload order): " + ("; ".join(f"Image {i} - {REF_LABEL[r]}" for i, r in enumerate(refs, 1)) if refs else "none needed for this page") +
         ". The comic character sheets are the ONLY identity references. Do not redesign anyone.", "",
         "CHARACTERS ON THIS PAGE (keep identical in every panel):"]
    p += ["- " + D.CHARACTERS[c] for c in codes]
    if "Civic" in text:
        p.append("- " + D.CAR_CIVIC)
    if "father's car" in text.lower():
        p.append("- " + D.FATHER_CAR)
    if "hedge" in text.lower():
        p.append("- " + D.HEDGE)
    if D.REFERENCES["FLEET"] in refs:
        p.append("- " + D.FLEET)
    p.append("")
    for k, s in enumerate(shots):
        p.append(f"PANEL {k + 1} ({pos[k]}): {s['comp']} Key moment: {s['act']} Setting: {s['loc']}."
                 + (f" COMPOSITION: {s['frame']}" if s['frame'] else ""))
    p += ["", D.RULES]
    prompt = "\n".join(p)
    fname = f"PAGE_{n:02d}.txt"
    open(os.path.join(HERE, "03_comic_pages", fname), "w").write(prompt + "\n")
    index += ["---", f"### PAGE {n:02d} - {shots[0]['id']}-{shots[-1]['id']} - {len(shots)} panels - "
              f"{', '.join(CH[c]['title'] for c in chs)}",
              f"File: `03_comic_pages/{fname}`  ", f"Upload: {', '.join(refs) if refs else '-'}", "",
              "```", prompt, "```", ""]
index += ["---", "## Page approval table", "",
          "| Page | Shots | Faces match sheets | Era/age correct | No text/logos | Approved |", "|---|---|---|---|---|---|"]
for n, shots in enumerate(PAGES, 1):
    index.append(f"| {n:02d} | {shots[0]['id']}-{shots[-1]['id']} | ☐ | ☐ | ☐ | ☐ |")
open(os.path.join(HERE, "03_comic_pages.md"), "w").write("\n".join(index) + "\n")

# --------------------------------------------------------------------------- 04 animation prep
REUSE = {tags["old_key"]: f"Frame-match {tags['key_fob']} (same hand position and framing) for the match cut.",
         tags["workshop"]: "Use Preview 01 (once approved) as reference.",
         tags["civic_reveal"]: "Use Preview 02 (once approved) as reference.",
         tags["led"]: "Use Preview 03 (once approved) as reference."}
for s in D.SHOTS:
    if s["note"].startswith("Reuse"):
        REUSE[s["id"]] = s["note"]
TWO_KF = ("turns", "jumps", "stands", "walks", "hug", "opens", "raises", "lifts", "rises", "closes", "drops", "wipes",
          "stirs", "stops", "pats", "tears", "rotates", "shuts", "hands it", "lowers")


def keyframes(s):
    return 2 if any(w in s["act"].lower() for w in TWO_KF) else 1


out = [f"# THE IRISH GRAFT - PART 1  ({VERSION})", "## 04 - Animation Preparation (USE ONLY AFTER PAGE APPROVAL)", "",
       "Every shot gets its own full-screen 9:16 key frame (1080x1920 minimum), generated fresh using the approved comic",
       "page panel as the layout reference - not cropped from the page, which is too low resolution.", "",
       "**Motion principle:** movement comes from the characters and environment (hands, heads, breath, weather,",
       "vehicles, light), animated with image-to-video from a START frame and, where the pose changes, an END frame.",
       "Camera moves are small and motivated, never a slow zoom standing in for animation.", "",
       "**Layer split:** where marked, generate background / character / foreground separately so parallax and weather",
       "can be added in the edit without warping faces.", "",
       "**Frame prompt template:** `[STYLE] Single full-bleed 9:16 vertical frame, 1080x1920, no panel borders. "
       "[CHARACTER LOCKS + reference sheets] [Composition] [START pose] Setting: [Location]. [COLOUR GRADE] [RULES]` - "
       "for the END frame, swap in the end pose.", "",
       "| Shot | Page | Dur | Key frames | Start -> end pose | Animated movement | Camera | Layers | Notes |",
       "|---|---|---|---|---|---|---|---|---|"]
for s in D.SHOTS:
    kf = keyframes(s)
    layers = "BG + char + FG" if ("rain" in s["anim"].lower() or "track" in s["cam"].lower()
                                  or "dolly" in s["cam"].lower()) else "single"
    pose = s["act"] if kf == 2 else "Hold pose; secondary motion only"
    out.append(f"| {s['id']} | {s['page']:02d} | {fmt_dur(s['dur'])} | {kf} | {pose} | {s['anim']} | {s['cam']} | "
               f"{layers} | {REUSE.get(s['id'], '')} |")
KF_TOTAL = sum(keyframes(s) for s in D.SHOTS)
out += ["", f"**Totals:** {len(D.SHOTS)} shots, {KF_TOTAL} key frames to generate, runtime {mmss(TOTAL)}.", ""]
open(os.path.join(HERE, "04_animation_prep.md"), "w").write("\n".join(out))

# --------------------------------------------------------------------------- README
RESOLVED = [
    "Global Tyres year, school and father's driving: 2017, attendance suffered and he was kicked out, father drove him six days a week.",
    "LED bulb disaster: ordered online, ~45 minutes, bulb installed backwards.",
    "England trip: contacted companies incl. Illest Works; ferry with ~EUR 220; slot machines; ~EUR 100 at Holyhead; London job fell through; mother arranged the journey home; food and comfort on return. Invented dialogue and the rented room were removed.",
    "CC Decals: started while at Castleshane Motors, Clontibret; EUR 25-30 per job; 5-8 jobs/week; EUR 150-200 extra; customers at the father's home; hedge gag.",
    "Donegal Rally: 60-70 orders, over EUR 2,000, all spent buying drinks at Brian Shevlin's pub.",
    "Learning everything: gel plates (10-15 sets, ~EUR 25 profit each), calipers, bodykits, YouTube 2-3 hours each evening, Mercedes Gilmore day job, outdoor jobs racing sunset, VCDS coding, dead batteries and jump-starts.",
    "COVID: WooCommerce e-commerce website built with Arlind from DigitGrow (kept separate from the start of the collaboration).",
    "Remapping: EK Remaps, Leeds, ~GBP 4,800, five days; GBP 11.50/hour vs ~EUR 160/hour; left employment; 4-5 remaps/week, EUR 700-800 weekly profit; several videos a day. The invented ferry trip to Leeds was removed.",
    "First garage: November 2021, father's land beside the home where Conor played as a child; customers from Cork, Derry, Galway, Mayo; up to ~10 hours return; long hours; ad spend pressure; customer-service challenges. The invented father-built roller-door gag was removed.",
    "Carrickmacross 2022: repeated landlord rejections partly due to age; premises secured, renovated; walk-ins, parts, online orders, bookings. The invented opening-day father scene was removed.",
    "Marbella c. 2024: starting again, sleepless nights, flyers on parked cars, considering giving up, styling business develops.",
    "Level Up With CC: training (ECU/remapping + business, team guidance) kept separate from motivational events; Dublin 15 Nov 2025, Cavan 27 Feb 2026, Marbella 22 May 2026, Puerto Banus yacht event 19 Sep 2026 in order.",
    "Mansion 22 May 2026: described as worth EUR 200 million; worldwide team together in person for the first time; Arlind shown clearly; first face-to-face meeting after nine years; no verbatim dialogue.",
    "CC Marbella Rentals: fleet models as supplied (X5 M Competition 850 BHP, McLaren GT, Panamera GTS, M2, Golf R), drawn only from approved assets.",
    "Dubai: vision and teaser only, no claimed achievements; ends on the 'Part 2: Dubai' card.",
    "Mother now uses her existing comic reference sheet; Arlind uses his sheet; father remains fictional; Tomas does not appear; no invented tattoo timeline (arms covered pre-Marbella).",
    "Civic chassis code dropped from narration and visuals - the story says 'Honda Civic 1.4 petrol'.",
    "v0.3: homecoming corrected - mother arranged the return and waited at Dublin Port with crisps, chocolate and rolls (invented family-kitchen scene removed; 'how he got home' flag resolved).",
    "v0.3: 'Every euro I earned, I saved' replaced with wording about saving towards the first car.",
    "v0.3: COVID chapter expanded (driveway work -> online products, website build with Arlind, listings, photos, enquiries, orders); 2020 not presented as the start of the collaboration.",
    "v0.3: first-garage chapter expanded (childhood ground -> business ground match dissolve, silent father beat, no dialogue).",
    "v0.4: engine-start thumbs-up marked optional; website kept separate from the (unstated) collaboration start; childhood flashback + match cut replaces the ghost effect; first meeting shown without an assumed handshake/hug (S120 line revised); closing line flagged for Conor's final approval; premium art-direction added to every page prompt.",
    "v0.4: S121 floating cloud memories replaced by a clean hard-cut memory montage reusing the approved Global Tyres, ferry and hedge frames (2.0/1.5/1.5/1.5/1.0s, sound bridge).",
    "v0.3: Marbella expanded to ~70s; mansion scene refocused on the team and Arlind with a scripted musical pause; mansion value kept to one line.",
]
rd = [f"# THE IRISH GRAFT - PART 1 - Production Blueprint ({VERSION}, awaiting approval)", "",
      f"9:16 vertical animated graphic-novel documentary - **{len(D.SHOTS)} shots, {len(CH)} chapters, "
      f"{len(PAGES)} comic pages, runtime {mmss(TOTAL)}**.",
      f"Narration: {TW} words, ~{mmss(SPOKEN)} spoken at 150 wpm ({SPOKEN / TOTAL:.0%} density). The rest is breaths, "
      "comic timing and deliberate emotional holds.", "",
      "## Files", "",
      "| File | Phase | Contents |", "|---|---|---|",
      "| `01_narration.md` | 1 | Full first-person VO script in Conor's voice, by chapter |",
      "| `02_master_storyboard.md` | 2 | Every shot: chapter, duration, timecode, VO, characters, composition, location, action, animation, camera, SFX, music |",
      "| `03_comic_pages.md` + `03_comic_pages/PAGE_XX.txt` | 3 | One complete ChatGPT prompt per page (3-5 panels), required uploads, approval table |",
      "| `04_animation_prep.md` | 4 | Per-shot 9:16 key-frame list and motion brief - use only after page approval |",
      "| `05_page_tests/PAGE_01_PACKAGE.md` | 3 | Page 01 visual quality test: shots, prompt, references, 9:16 framing, consistency and frame-separation plan |",
      "| `storyboard_data.py` / `build.py` | - | Single source of truth; edit data, run `python3 production/build.py` to regenerate everything |", "",
      "## Reference files", ""]
rd += [f"- **{k}** - `{v}`" for k, v in D.REFERENCES.items()]
rd += ["", "## Character designs", ""]
rd += [f"- **{k}** - {v}" for k, v in D.CHARACTERS.items()]
rd += ["", "## Unresolved - required confirmation items", ""]
rd += [f"{i}. {q}" for i, q in enumerate(D.OPEN_QUESTIONS, 1)]
rd += ["", "## Unresolved - detail-level CONFIRM flags (by shot)", ""]
rd += [f"- **{s['id']}** ({s['ch']}) - {s['note']}" for s in D.SHOTS if "CONFIRM" in s["note"]]
rd += ["", "## Resolved by the verified story material (audit v0.1 -> v0.3)", ""]
rd += [f"- {r}" for r in RESOLVED]
rd += ["", "Status: nothing has been generated or animated. Waiting for approval of narration, storyboard and page prompts.", ""]
open(os.path.join(HERE, "README.md"), "w").write("\n".join(rd))

N_CONFIRM = sum("CONFIRM" in s["note"] for s in D.SHOTS)
print(f"OK {VERSION}: {len(CH)} chapters, {len(D.SHOTS)} shots, {len(PAGES)} pages "
      f"(sizes {[len(p) for p in PAGES]}), runtime {mmss(TOTAL)}, narration {TW} words (~{mmss(SPOKEN)}, "
      f"{SPOKEN / TOTAL:.0%}), {KF_TOTAL} key frames, {N_CONFIRM} shot-level CONFIRM flags")

# --------------------------------------------------------------------------- page quality-test packages
TEST_PAGES = [1]  # pages cleared for generation; add the next page only after approval
os.makedirs(os.path.join(HERE, "05_page_tests"), exist_ok=True)
for n in TEST_PAGES:
    shots = PAGES[n - 1]
    codes = list(dict.fromkeys(c for s in shots for c in s["chars"]))
    refs = refs_for(codes, shots)
    prompt = open(os.path.join(HERE, "03_comic_pages", f"PAGE_{n:02d}.txt")).read().strip()
    layout_n = len(shots)
    o = [f"# THE IRISH GRAFT - PART 1  ({VERSION})", f"## PAGE {n:02d} - Visual Quality Test",
         "", "Status: **ready to generate - awaiting approval of the result before Page "
         f"{n + 1:02d} is prepared.**", "",
         f"Chapter: {', '.join(dict.fromkeys(CH[s['ch']]['title'] for s in shots))} - shots {shots[0]['id']}-{shots[-1]['id']} "
         f"- {layout_n} panels - {mmss(sum(s['dur'] for s in shots))} of screen time.", "",
         "### 1. Required references (upload in this order, in one message with the prompt)", ""]
    for i, r in enumerate(refs, 1):
        o.append(f"{i}. `{r}`")
    o += ["", "If the fleet images are not ready yet, generate without them: the prompt tells the model to keep the cars "
          "as soft, unbadged background shapes. Regenerate panel 1 later with the approved fleet images.", "",
          "### 2. Shot descriptions", ""]
    for k, s in enumerate(shots, 1):
        vo = f'"{s["vo"]}"' if s["vo"] else "(none)"
        o += [f"**Panel {k} - {s['id']}** ({fmt_dur(s['dur'])}, TC {mmss(s['start'])}-{mmss(s['start'] + s['dur'])})", "",
              f"- Voice-over: {vo}",
              f"- Characters: {', '.join(NAMES[c] for c in s['chars'])}",
              f"- Composition: {s['comp']}",
              f"- Intended 9:16 composition: {s['frame'] or 'see composition'}",
              f"- Action: {s['act']}",
              f"- Location / period: {s['loc']}",
              f"- Camera: {s['cam']}",
              f"- Sound: {s['sfx']}",
              f"- Music: {s['mus'] or CH[s['ch']]['music']}"]
        if s["note"]:
            o.append(f"- Note: {s['note']}")
        o.append("")
    o += ["### 3. The prompt (paste exactly)", "", "```", prompt, "```", "",
          "### 4. Keeping the characters consistent", "",
          "- Start a **fresh ChatGPT conversation** for the test page so no earlier images influence it.",
          "- Upload the reference files first, then paste the prompt in the same message.",
          "- Judge the face first. If Conor drifts, do not re-roll from scratch; reply: *\"Keep the layout, lighting and "
          "colours exactly the same. Correct only Conor's face to match the uploaded character sheet: brows, deep-set "
          "eyes, nose, jaw, ears, beard line and fade haircut.\"*",
          "- Fix one problem per follow-up message (face, then hands, then any stray text). Several fixes at once "
          "usually makes the whole page drift.",
          "- Young Conor's hand (panel 3) must show no tattoos and a covered wrist; adult Conor's hand (panel 2) must "
          "show his sleeve tattoos and the watch.",
          "- Once approved, this page becomes the **style anchor**: upload it alongside the character sheet for every "
          "later page, so line weight, colour and shading stay identical.", "",
          "### 5. Separating the panels into animation-ready frames", "",
          "The page is a planning asset. Each panel is regenerated as its own full-resolution frame, using the approved "
          "page as the layout and style reference; panels are never cropped from the page (too low resolution, and the "
          "borders and gutters would show).", "",
          "**Frame size.** ChatGPT's tallest output is usually 2:3 (1024x1536), not 9:16. Generate each frame at "
          "1024x1536 with the action kept inside the centre 864x1536 strip, crop to that strip (exactly 9:16), then "
          "upscale x1.25 to 1080x1920 (or x2.5 to 2160x3840 for a 4K master). If your tool offers native 9:16, use it "
          "and skip the crop.", "",
          "**Frame prompt per panel:** `Using the attached approved Page 01 as the style and layout reference, create a "
          "single full-bleed vertical frame of PANEL <n> only - no borders, no other panels. <panel text from section 3>`", "",
          "| Panel | Shot | Key frames to generate | Layers | Motion (character/environment) | Camera | Match/continuity |",
          "|---|---|---|---|---|---|---|"]
    plans = {
        0: ("2: START (mid-stride, left foot forward, 3 m away) and END (closer, right foot forward, a step nearer camera)",
            "BG plate (villa, sea, sky, cars) + Conor cut-out", "Walk cycle, fob swing, glints sliding across car paint, palm fronds, heat shimmer",
            "Backward dolly matched to his walk; parallax between car row and villa from the layer split", "Fob carried in the left (watch) hand to set up panel 2"),
        1: ("1 (hand mid-turn) + optional END (fob rotated ~30 degrees)", "Single frame; bokeh can be a separate soft layer",
            "Fingers rotate the fob; tendons move; bokeh drifts", "Locked off with a tiny handheld float",
            "Defines the match-cut anchor: record the fob's exact X/Y position and angle"),
        2: ("2: START (hand open, key resting on palm) and END (hand closed around key)", "Single frame + separate rain-on-glass overlay",
            "Fingers close; rain runs down glass; breath fog blooms", "Locked off",
            "Key centred at the same X/Y and angle as panel 2's fob, so the cut lands on the same spot; title card added in edit"),
    }
    for k, s in enumerate(shots):
        kf, layers, motion, cam, match = plans.get(k, ("1", "single", s["anim"], s["cam"], ""))
        o.append(f"| {k + 1} | {s['id']} | {kf} | {layers} | {motion} | {cam} | {match} |")
    o += ["", "Movement is animated from these key frames with image-to-video (start/end frames), so motion comes from the "
          "subject and environment, not from zooming into a still.", "",
          "### 6. Approval checklist for Page 01", "",
          "- [ ] Reads as a premium hand-inked graphic novel (line variation, spot blacks, hatching), not glossy AI art",
          "- [ ] Adult Conor matches the sheet: face, beard, haircut, tattoos, watch",
          "- [ ] Panel 3 hand reads as younger, untattooed, wrist covered",
          "- [ ] Key in panel 3 sits where the fob sits in panel 2 (match cut works)",
          "- [ ] Each panel holds up as a 9:16 shot on its own",
          "- [ ] Warm Marbella grade (panels 1-2) vs cold Irish grade (panel 3) clearly contrasted",
          "- [ ] No text, logos, badges, plates or watermarks",
          "- [ ] Hands anatomically correct (five fingers, natural grip)", ""]
    open(os.path.join(HERE, "05_page_tests", f"PAGE_{n:02d}_PACKAGE.md"), "w").write("\n".join(o))
print(f"Page test packages written: {TEST_PAGES}")
