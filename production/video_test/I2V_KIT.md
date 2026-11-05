# THE IRISH GRAFT - PART 1 · Cold Open (S001-S003) · Image-to-Video Kit

This kit produces the real animated 21-second test in about 30-60 minutes. You make 3 short clips and 1 voice track in
outside tools, put them in the `inbox/` folders, and I assemble the final MP4 here (or you run `assemble_final.py`).

The start frames are already cropped to 9:16 (1080x1920) from the approved Page 01:

| Shot | Start frame | Length needed | Generate |
|---|---|---|---|
| S001 | `frames/p1_9x16.png` | 5.0s | 5s clip |
| S002 | `frames/p2_9x16.png` | 9.5s | 10s clip |
| S003 | `frames/p3_9x16.png` | 6.5s | 10s clip (trimmed) |

## 1. Animate the three shots (pick ONE tool and use it for all three)

Recommended, fastest: **Kling** (2.x, image-to-video, "Professional" mode) or **Google Veo 3** (Gemini app / Flow / AI
Studio, image-to-video). **Runway Gen-4** also works. Use 9:16, the highest quality setting, and **turn generated audio
off** (sound is added in the edit).

Paste the prompt that matches the frame. Each one asks for subject motion, not a zoom.

**S001 - `p1_9x16.png` - 5s**
```
Keep the exact hand-inked graphic-novel illustration style, colours and line work of the image. The man walks naturally
toward the camera along the row of parked cars: steady confident stride, arms swinging slightly, the key fob in his left
hand. Palm fronds sway gently in a warm breeze, sunlight glints slide across the car paintwork, faint heat shimmer above
the paving. Camera slowly dollies backward at his walking pace. His face, beard, haircut and tattoos stay exactly the
same in every frame. No morphing, no new people, no text.
```
Negative (if the tool has it): `morphing face, extra limbs, warped hands, flicker, text, logos, camera zoom only, 3D render, photoreal`

**S002 - `p2_9x16.png` - 10s**
```
Keep the exact hand-inked graphic-novel illustration style of the image. Extreme close-up of the tattooed hand: the thumb
slowly rubs across the key fob, then the fingers turn the fob a little in the hand; tendons move under the skin, the
watch catches the light. The warm sunset bokeh behind drifts softly. Locked-off camera with a very slight handheld float.
The hand keeps five fingers and the same tattoos throughout. No text, no logo on the fob.
```

**S003 - `p3_9x16.png` - 10s**
```
Keep the exact hand-inked graphic-novel illustration style of the image. Close-up of a young man's hand in a black
ribbed sleeve holding an old car key in front of a rainy window: the fingers slowly close around the key. Raindrops run
down the glass, a soft fog of breath blooms on the window and fades. Cold grey Irish daylight. Locked-off camera. Hand
keeps five fingers, no tattoos, no text.
```

Tips: generate 2-3 variations of each and keep the best. If the face drifts in S001, regenerate rather than accept it -
Conor's likeness is the priority. Download as MP4 and save as:
`inbox/clips/S001.mp4`, `inbox/clips/S002.mp4`, `inbox/clips/S003.mp4`.

**Match cut:** in S002 the fob ends centre-left; in S003 the key starts upper-right. For this test I hide the jump with a
hard cut on the piano note. For the final film, the S003 frame will be regenerated with the key in the fob's position.

## 2. Narration (Irish-accented English)

Recommended: **ElevenLabs** (Text to Speech, an Irish male voice from the Voice Library, e.g. search "Irish male
narrator"; model *Eleven Multilingual v2*; Stability ~45, Similarity ~75, Style ~15). If Conor records it himself,
even better: a phone in a quiet room, 30 cm from the mouth, is enough for this test.

Generate each line separately and save as WAV or MP3:

| File | Line | Must fit in |
|---|---|---|
| `inbox/vo/S001` | People see the cars, the events, the villas in Marbella. | 4.5s |
| `inbox/vo/S002` | What they don't see is a tyre shop in Ireland, a ferry to Holyhead, and a lot of very expensive mistakes. | 9.0s |
| `inbox/vo/S003` | My name is Conor Callaghan. And this is how it started. | 5.5s |

Delivery note for the voice: relaxed, warm, conversational, like telling a mate the story; a small smile on "very
expensive mistakes"; a beat of pause before "And this is how it started."

## 3. Music (optional - a temp score is already built in)

Any royalty-free cue works. Prompt for Suno / Udio / ElevenLabs Music:
```
Cinematic documentary underscore, 21 seconds, 70 bpm. 0-14s: warm low synth pad and distant felt piano, Mediterranean
sunset, hopeful but restrained. At 14.5s the music cuts to near-silence: only soft rain and one felt-piano note. 16.5s:
two more gentle piano notes as a title appears. No vocals, no drums.
```
Save as `inbox/music/music.mp3`. Without it, the assembler uses the temp sound bed (pad, footsteps, key jingle, rain,
wind and piano notes).

## 4. Assembly

Send me the files (upload them in chat) and I will assemble, check and return the final MP4 - or run it yourself:
```
python3 production/video_test/assemble_final.py
```
Output: `production/video_test/out/IRISH_GRAFT_P1_COLD_OPEN_v1.mp4` (1080x1920, 30fps, 21s, H.264 + AAC), with the
title "THE IRISH GRAFT - PART 1" over S003 and the VO placed on the storyboard timecodes (0:00.3 / 0:05.2 / 0:14.8).
Missing pieces fall back automatically: no clip -> animatic shot, no VO -> subtitles, no music -> temp score.
