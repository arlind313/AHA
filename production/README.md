# THE IRISH GRAFT - PART 1 - Production Blueprint (DRAFT v0.1, awaiting approval)

9:16 vertical animated graphic-novel documentary - **96 shots, 14 chapters, 25 comic pages, runtime 13:16**.
Narration: 1374 words (~9:10 spoken at 150 wpm); the rest is deliberate music/sound beats.

## Files

| File | Phase | Contents |
|---|---|---|
| `01_narration.md` | 1 | Full first-person VO script in Conor's voice, by chapter |
| `02_master_storyboard.md` | 2 | Every shot: chapter, duration, timecode, VO, characters, composition, location, action, animation, camera, SFX, music |
| `03_comic_pages.md` + `03_comic_pages/PAGE_XX.txt` | 3 | One complete ChatGPT image prompt per comic page (3-4 panels each) + approval table |
| `04_animation_prep.md` | 4 | Per-shot 9:16 key-frame list and motion brief - use only after page approval |
| `storyboard_data.py` / `build.py` | - | Single source of truth; edit data, run `python3 production/build.py` to regenerate everything |

## Character designs

- **YC** - YOUNG CONOR (2017-2018, age 16-18): clearly the same person as the tattooed man on the uploaded sheet, de-aged. Same strong straight brows, deep-set eyes, straight nose, defined jaw and chin, slightly prominent ears; softer fuller cheeks, smooth teenage skin, at most faint fuzz on the upper lip - NO beard. Short dark-brown hair, short faded sides, textured top pushed up and forward (same silhouette as the sheet, less groomed). Lean wiry teenage build. NO TATTOOS anywhere, no watch, no jewellery. Default outfit: faded navy work trousers, plain dark-grey long-sleeve work top with sleeves pushed up, scuffed black safety boots.
- **C2** - CONOR (2019-2022, early twenties): the same face as the uploaded sheet, a few years younger than it - short trimmed beard starting to fill in, same fade haircut, athletic but not yet heavily muscular. Tattoos: NONE yet (see production note). Default outfit: plain black t-shirt or black hoodie, dark work trousers, black boots.
- **AC** - ADULT CONOR (2023-2026): exactly the tattooed man on the uploaded character sheet - same face, fade haircut, full short beard, neck tattoos, full tattoo sleeves on both arms, muscular build, dark wristwatch on the left wrist. Default outfit: fitted plain black t-shirt or black hoodie; sunglasses only where stated.
- **FA** - CONOR'S FATHER (fictional, consistent design): early fifties, stocky, weathered ruddy face, short grey-flecked dark hair receding at the temples, grey stubble, kind but serious eyes, deep crow's-feet. Always wears a navy quilted gilet over a faded blue-grey check shirt, work jeans, brown work boots.
- **MO** - CONOR'S MOTHER (fictional, consistent design): late forties, warm open face, shoulder-length chestnut-brown hair loosely tied back, light freckles, kind tired eyes. Wears a soft oatmeal knit cardigan over a plain top.
- **AR** - ARLIND (DigitGrow web partner): REFERENCE SHEET NOT YET SUPPLIED - until it is, show him only from behind, in soft focus, or as a small video-call tile where the face is not detailed. Neutral smart-casual clothing.
- **EX** - BACKGROUND EXTRAS: ordinary unnamed people, realistic varied ages, simple clothing, never more detailed than the main characters, faces never close to camera.

## Open questions (please answer before page generation)

1. The full written story was not attached - this draft is built only from the chapter outline. Please send it so every CONFIRM flag can be resolved.
2. Arlind: a comic reference sheet is needed before shots S044, S084, S085 and S086 can be generated. Until then he is shown softly or from behind.
3. Nine years: the 22 May 2026 meeting implies working together since 2017, but the website is dated to COVID (2020). When did Conor and Arlind first work together?
4. Tattoo timeline: the design shows no tattoos through 2022 and the full sleeves from Marbella (2023). When did they actually appear?
5. Car code: the European 7th-gen Civic 1.4 petrol is normally the EP1 (EP2 = 1.6, EP3 = Type R). Visuals are identical; confirm what is said in narration (narration currently just says '1.4 petrol').
6. Donegal Rally money and the pub: confirm the sequence and that Conor was 18+ at the time.
7. Mother and father: fictional designs are used. Confirm you're happy for the mother to appear (only the father was mentioned in the brief).
8. Narration voice: confirm whether Conor will record the VO himself or whether a voice actor / AI voice is used.

## Shots flagged CONFIRM

- **S004** - CONFIRM: age (16 or 17), and whether he worked weekends, after school, or full-time at Global Tyres. Business name will be heard in narration only; no signage drawn.
- **S005** - CONFIRM: father's car (design uses a generic dark-green estate).
- **S008** - CONFIRM: school uniform colour.
- **S013** - CONFIRM what actually went wrong with the LED bulbs.
- **S015** - CONFIRM: type of job, city in England, and ferry route (e.g. Dublin-Holyhead).
- **S017** - CONFIRM how the job fell through.
- **S018** - CONFIRM: where he stayed.
- **S020** - CONFIRM: mother's reaction and words (paraphrased, no direct quote).
- **S023** - CONFIRM: vinyl cutter and bedroom workspace.
- **S025** - CONFIRM: sold at car meets.
- **S026** - CONFIRM: year of the Donegal Rally and how he sold (stall, walking the crowd).
- **S028** - CONFIRM: that the rally money was spent in the pub, and that Conor was of legal drinking age (18) at the time.
- **S031** - CONFIRM: types of bodykit work, and whether 'borrowed sheds' is accurate.
- **S033** - CONFIRM: year CC Decals became CC Styling.
- **S034** - CONFIRM: dealership location, start date, and his role there. No star badges drawn.
- **S038** - CONFIRM: real example of a coding mistake (keep generic otherwise).
- **S044** - CONFIRM: when Conor and Arlind first started working together (the 2026 scene says nine years, i.e. 2017; the website is 2020). Arlind reference sheet needed.
- **S045** - CONFIRM: what products launched on the website first.
- **S050** - CONFIRM: date of the Leeds course, and that he went after (not during) lockdown. No legible station signage.
- **S051** - CONFIRM: travelled by ferry (callback works only if true; otherwise use a plane window).
- **S053** - CONFIRM: whether he still owned the Civic at this time.
- **S056** - CONFIRM: parents' reaction.
- **S058** - CONFIRM: building type (new build, converted shed or barn).
- **S059** - CONFIRM: father helped build/fit out the garage.
- **S063** - CONFIRM: nature of the financial pressure.
- **S066** - CONFIRM: shop opening date; shop sign added in edit if wanted.
- **S067** - CONFIRM: team size in 2022. Staff remain unnamed extras.
- **S070** - CONFIRM: year he moved to Marbella, and when his tattoos appeared (design switches to the full-sleeve adult look here).
- **S072** - CONFIRM: specific setbacks in Marbella.
- **S075** - CONFIRM: what the Spanish business offered first (remapping, styling, detailing).
- **S078** - CONFIRM: start date and location of Level Up With CC.
- **S082** - CONFIRM: event name/purpose.
- **S085** - CONFIRM: 'nine years' and the exact start of the partnership.
- **S090** - CONFIRM: fleet makes/models (kept generic and unbadged unless you specify).
- **S093** - CONFIRM: timing of the move/expansion to Dubai.

Status: nothing has been generated or animated. Waiting for approval of narration, storyboard and page prompts.
