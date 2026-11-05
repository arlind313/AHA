# THE IRISH GRAFT - PART 1 - Production Blueprint (v0.2, awaiting approval)

9:16 vertical animated graphic-novel documentary - **120 shots, 15 chapters, 35 comic pages, runtime 12:36**.
Narration: 1446 words, ~9:38 spoken at 150 wpm (77% density). The rest is breaths, comic timing and deliberate emotional holds.

## Files

| File | Phase | Contents |
|---|---|---|
| `01_narration.md` | 1 | Full first-person VO script in Conor's voice, by chapter |
| `02_master_storyboard.md` | 2 | Every shot: chapter, duration, timecode, VO, characters, composition, location, action, animation, camera, SFX, music |
| `03_comic_pages.md` + `03_comic_pages/PAGE_XX.txt` | 3 | One complete ChatGPT prompt per page (3-5 panels), required uploads, approval table |
| `04_animation_prep.md` | 4 | Per-shot 9:16 key-frame list and motion brief - use only after page approval |
| `storyboard_data.py` / `build.py` | - | Single source of truth; edit data, run `python3 production/build.py` to regenerate everything |

## Reference files

- **CONOR** - `references/conor-character-sheet.png`
- **MOTHER** - `references/mother-character-sheet.png`
- **ARLIND** - `references/arlind-character-sheet.png`
- **FLEET** - `references/fleet/ (approved CC Marbella Rentals vehicle images)`

## Character designs

- **YC** - YOUNG CONOR (2017-2019, late teens): derived from the uploaded adult Conor sheet and clearly the same person, de-aged. Same strong straight brows, deep-set eyes, straight nose, defined jaw and chin, slightly prominent ears; softer fuller cheeks, smooth young skin, at most faint fuzz on the upper lip - NO beard. Short dark-brown hair, short faded sides, textured top pushed up and forward (same silhouette as the sheet, less groomed). Lean wiry build. No extensive modern tattoos: Tattoo timeline is UNCONFIRMED: keep both arms, backs of the hands and neck covered (long sleeves, hoodie or high crew neck) so the image neither shows nor denies tattoos. Default outfit: faded navy work trousers, plain dark-grey long-sleeve work top, scuffed black safety boots.
- **C2** - CONOR (2019-2023, early twenties): the same face as the uploaded adult Conor sheet, a few years younger - short beard starting to fill in, same fade haircut, athletic but not yet heavily muscular. Tattoo timeline is UNCONFIRMED: keep both arms, backs of the hands and neck covered (long sleeves, hoodie or high crew neck) so the image neither shows nor denies tattoos. Default outfit: plain black long-sleeve top or black hoodie, dark work trousers, black boots.
- **AC** - ADULT CONOR (Marbella and Dubai, 2024-2026): exactly the man on the uploaded Conor character sheet - same face, fade haircut, full short beard, neck tattoos, tattoo sleeves on both arms, muscular build, dark wristwatch on the left wrist. Default outfit: fitted plain black t-shirt or black hoodie; sunglasses only where stated.
- **FA** - CONOR'S FATHER (fictional, consistent design - no reference exists): early fifties, stocky, weathered ruddy face, short grey-flecked dark hair receding at the temples, grey stubble, kind but serious eyes, deep crow's-feet. Always wears a navy quilted gilet over a faded blue-grey check shirt, work jeans, brown work boots.
- **MO** - CONOR'S MOTHER: use the uploaded mother comic reference sheet EXACTLY - same face, hair, build and styling. Do not invent or alter her appearance.
- **AR** - ARLIND (DigitGrow): use the uploaded Arlind comic reference sheet EXACTLY - same face, hair, build and styling. Show him clearly, face visible, never blurred or from behind.
- **EX** - BACKGROUND EXTRAS: ordinary anonymous people (customers, coworkers, team members, crowds), realistic varied ages, simple clothing, never more detailed than the main characters, faces never close to camera, never named.

## Unresolved - required confirmation items

1. Exact year Conor and Arlind first began collaborating (the story states nine years by May 2026; the website is a separate COVID-era milestone).
2. Exact timeline of Conor's tattoos. Until confirmed, pre-Marbella scenes keep arms and neck covered; Marbella onward uses the present-day sheet.
3. Currency of the first garage build cost (12,000-14,000). The figure stays out of the narration until confirmed.
4. Narrator: Conor's own voice or an AI voice.
5. Reference files to supply before page generation: mother sheet, Arlind sheet, approved fleet vehicle images (paths in README).

## Unresolved - detail-level CONFIRM flags (by shot)

- **S020** (CH02) - CONFIRM: departure port (a Holyhead arrival suggests Dublin).
- **S023** (CH02) - CONFIRM: where Conor was when the London job fell through (Holyhead assumed for the visual).
- **S025** (CH02) - CONFIRM: how the journey home was made (ferry, flight, bus).
- **S030** (CH03) - CONFIRM: start date at Castleshane Motors. No signage drawn.
- **S031** (CH03) - CONFIRM: whose cutter it was and where it was used.
- **S036** (CH04) - CONFIRM: year of the Donegal Rally breakthrough.
- **S037** (CH04) - CONFIRM: how the orders were taken (stall, walking the crowd, online).
- **S039** (CH04) - CONFIRM: Conor's age at the time (depiction assumes 18+). Pub name in VO only; no signage.
- **S044** (CH05) - CONFIRM: the period for the 10-15 sets (per week / per month).
- **S047** (CH05) - CONFIRM: Mercedes Gilmore dates and location. No star badges drawn.
- **S056** (CH06) - CONFIRM: year Conor and Arlind first began collaborating (the website is a separate milestone). CONFIRM: worked remotely by video call.
- **S060** (CH07) - CONFIRM: date of the Leeds course. Company named in VO only.
- **S064** (CH07) - CONFIRM: currency/location of the GBP 11.50/hour job.
- **S065** (CH07) - CONFIRM: which employer he left (Mercedes Gilmore by story order).
- **S071** (CH08) - CONFIRM: currency of the 12,000-14,000 build cost before adding the figure to narration.
- **S083** (CH09) - CONFIRM: month the Carrickmacross premises was secured/opened.
- **S087** (CH10) - CONFIRM: tattoos are shown from Marbella onward because the reference sheet is present-day; confirm this is acceptable for c. 2024.
- **S088** (CH10) - CONFIRM: first Marbella premises (rented unit assumed for the visual).
- **S094** (CH11) - CONFIRM: launch date and location of Level Up With CC courses. Name in VO only.
- **S099** (CH11) - Callback to S015. CONFIRM: that the LED story is part of the event talk.
- **S106** (CH12) - CONFIRM: exact year the collaboration began (nine years is stated by the story).
- **S110** (CH12) - Placed after 22 May to keep the events in chronological order. CONFIRM: event format.

## Resolved by the verified story material (v0.1 -> v0.2 audit)

- Global Tyres year, school and father's driving: 2017, attendance suffered and he was kicked out, father drove him six days a week.
- LED bulb disaster: ordered online, ~45 minutes, bulb installed backwards.
- England trip: contacted companies incl. Illest Works; ferry with ~EUR 220; slot machines; ~EUR 100 at Holyhead; London job fell through; mother arranged the journey home; food and comfort on return. Invented dialogue and the rented room were removed.
- CC Decals: started while at Castleshane Motors, Clontibret; EUR 25-30 per job; 5-8 jobs/week; EUR 150-200 extra; customers at the father's home; hedge gag.
- Donegal Rally: 60-70 orders, over EUR 2,000, all spent buying drinks at Brian Shevlin's pub.
- Learning everything: gel plates (10-15 sets, ~EUR 25 profit each), calipers, bodykits, YouTube 2-3 hours each evening, Mercedes Gilmore day job, outdoor jobs racing sunset, VCDS coding, dead batteries and jump-starts.
- COVID: WooCommerce e-commerce website built with Arlind from DigitGrow (kept separate from the start of the collaboration).
- Remapping: EK Remaps, Leeds, ~GBP 4,800, five days; GBP 11.50/hour vs ~EUR 160/hour; left employment; 4-5 remaps/week, EUR 700-800 weekly profit; several videos a day. The invented ferry trip to Leeds was removed.
- First garage: November 2021, father's land beside the home where Conor played as a child; customers from Cork, Derry, Galway, Mayo; up to ~10 hours return; long hours; ad spend pressure; customer-service challenges. The invented father-built roller-door gag was removed.
- Carrickmacross 2022: repeated landlord rejections partly due to age; premises secured, renovated; walk-ins, parts, online orders, bookings. The invented opening-day father scene was removed.
- Marbella c. 2024: starting again, sleepless nights, flyers on parked cars, considering giving up, styling business develops.
- Level Up With CC: training (ECU/remapping + business, team guidance) kept separate from motivational events; Dublin 15 Nov 2025, Cavan 27 Feb 2026, Marbella 22 May 2026, Puerto Banus yacht event 19 Sep 2026 in order.
- Mansion 22 May 2026: described as worth EUR 200 million; worldwide team together in person for the first time; Arlind shown clearly; first face-to-face meeting after nine years; no verbatim dialogue.
- CC Marbella Rentals: fleet models as supplied (X5 M Competition 850 BHP, McLaren GT, Panamera GTS, M2, Golf R), drawn only from approved assets.
- Dubai: vision and teaser only, no claimed achievements; ends on the 'Part 2: Dubai' card.
- Mother now uses her existing comic reference sheet; Arlind uses his sheet; father remains fictional; Tomas does not appear; no invented tattoo timeline (arms covered pre-Marbella).
- Civic chassis code dropped from narration and visuals - the story says 'Honda Civic 1.4 petrol'.

Status: nothing has been generated or animated. Waiting for approval of narration, storyboard and page prompts.
