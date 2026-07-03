# Production Playbook — the hard-won process (read before building from scratch)

This is the distilled wisdom from building Video #1 ("What Is a Derivative?") end to end. It exists so a
fresh session performs as well or better without re-learning by trial and error. SKILL.md has the build
loop and manim gotchas; this file has the **process discipline, the standing directives, the error log,
and the do/don't list.** The channel identity (name, mascot, palette) is intentionally NOT the point here —
the *method* is.

## 0. The prime directive: VERIFY, don't assert
The #1 thing that wasted the user's time was saying "done / fixed / verified" without proof. Every visual
or audio claim must be backed by reading the actual rendered artifact:
- **Frames:** `ffmpeg -ss <t> -i <file> -frames:v 1 f.png` then **Read f.png**. Tile several timestamps
  (`hstack`/`vstack`) to check motion, not just a resting pose.
- **Match to a reference:** composite your output next to the user's reference image and Read the pair —
  don't nudge blindly. (Eye-SIZE mismatch went unseen for several rounds until I did a side-by-side.)
- **Audio present?** subtract the no-music render from the final; the leftover IS the bed. `volumedetect`
  on the final is masked by the voice.
- **Duration unchanged?** after any edit that must not touch audio (e.g. the mascot), confirm the total
  seconds are identical so music + chapter timestamps stay valid.
- It is YOU (Claude) reading the images. Don't claim a sub-model "can't see" — just read them.

## 1. Standing user directives (preferences that persisted across the whole build)
- **SUGGEST ≠ BUILD.** When the owner asks for a suggestion/plan, deliver the ranked options + ONE
  recommendation and STOP — production (TTS, images, 4K) starts only after he explicitly confirms a
  named topic. Violated once (video #2 was built off a "suggest" request); he was rightly furious.
- **On any mid-build interruption: stop renders FIRST, re-read the whole message.** Look for premise
  changes, not just the surface correction (the "Hindi-only" interruption also said "I asked you to
  *suggest*" — the second half was missed and the build wrongly continued).
- **Format:** complete lessons, 6–15 min, length set by the TOPIC (owner's ruling 2026-07-03). Core idea:
  explain the concept PROPERLY — "every inch", EASY. No padding to reach a number, no cutting corners.
  Not 3-min gems, not 3-hr one-shots.
- **The Hindi (Hinglish) cut is the real deliverable — and since Video #2 it is the ONLY deliverable.**
  On Video #2 (circle area) the owner rejected building an English cut at all ("no only english now just
  hindi + english mixed one"): author the scene NATIVELY in Hinglish (Sarvam service in the scene, no
  translate_hi.py step), verify layout with free TTS-less static frames + the narration-audit agent BEFORE
  the first TTS render. Voice = **Sarvam Bulbul v3, speaker `aditya`**, 48 kHz, **default pace & temp**
  (overriding temperature added a hiss; overriding pace was rejected — leave both default).
- **Hinglish = natural bilingual code-switching, NOT a fixed %** and NOT literary Hindi. Full rules in
  `hindi-hinglish-cut.md`. (Took 3 iterations: "too much English" → "too formal" → natural.)
- **Music must be AUDIBLE** (~0.28), not a subliminal 0.10.
- **Mascot appears ONLY for questions/headlines, and leaves the instant an equation/graph draws.** Keep it
  moving (blink + hop + glance) while on screen. Never over the math. Never change total duration.
- **Keep it simple / don't over-engineer.** The user pushed back hard on a deep nested folder tree — collapse
  to the flat convention (§3). Don't narrate long option menus; act, then report briefly.
- **Research, don't guess** for anything audience-facing (titles): scrape real data with Apify.
- **API keys** (`$SARVAM_API_KEY`, `$DEEPGRAM_API_KEY`, `$OPENAI_API_KEY`) — keep them in your shell
  env (e.g. `~/.zshenv`); read from env, NEVER hardcode in committed files, and rotate any key that ever
  lands in a chat transcript or log.

## 2. The error log — bugs that cost real time (don't rediscover these)
| Symptom | Root cause | Fix |
|---|---|---|
| Render "hangs" ~forever | Deepgram **WAV** header says ~6 h duration | request **MP3** (`encoding=mp3&bit_rate=48000`) |
| Sarvam voice hisses / "greasy" | overriding `temperature` (and low sample rate) | default temp, **48000 Hz**, default pace |
| "All translated" but video plays English | `translate_hi.py` `ast.literal_eval` throws on **multi-line** `self.say("a"\n"b")`; `except` returned English silently | wrap group in parens before eval; make `except` RECORD the miss; **AST-audit** that every line has Devanagari |
| Motion ends ~3 s before the words (Hindi) | hardcoded `run_time` (tuned to shorter English audio) | bind travelling motion to `tracker.duration` |
| "Where's the music?" | bed at 0.10 ≈ −38 dB, masked by −21 dB voice | mix at ~0.28; verify by subtraction |
| "You didn't change it" / "no audio" / blank | QuickTime showed a **cached** frame of the same filename | hand over a freshly-named file or a static PNG |
| Reflex/near-full-circle angle | `Angle()` draws the reflex | use `Arc(start_angle, angle)` |
| Kept mobjects silently fade on wipe | scene holds submobjects, not the VGroup | build keep-set from `get_family()` |
| Thumbnail text garbled | image model can't spell **Devanagari** | keep in-image text English/symbols; add Hindi later; overlay wordmarks yourself with Pillow |
| Layout fix "didn't apply" on re-render | manim served a **stale cached partial movie file** (false cache hit on a repositioned MathTex) | re-render with `--disable_caching` (voiceover cache is separate — no TTS cost); verify the exact frame again |

## 3. Folder convention (the SIMPLE one the user chose — don't re-elaborate it)
Top level: `src/`, `curriculum/`, `Math/`, `Physics/`.
- **`src/`** = everything technical, FLAT — one **`<topic>_scene.py` per video** (e.g. `circle_scene.py`;
  video #1 predates the convention as `scene.py`/`scene_hi.py`), plus `root_buddy.py`, `sarvam_tts.py`,
  `build_helpers.sh`, legacy `translate_hi.py`; `src/assets/` (logo, avatar, banner, watermark, music,
  channel_description, thumbnail_style_guide); `src/build/` (regenerable TTS cache + renders).
- **`Math/<Topic Name>/`** (or `Physics/…`) = deliverables ONLY: the video mp4(s), `thumbnail.png`, and ONE
  `README.md` (title + description + tags). No wavs, no source, no metadata sprawl.
- Renders use `--media_dir src/build`; `root_buddy.py` sits next to the scene so the import resolves.

## 4. Asset generation (gpt-image-2 — proven)
`POST https://api.openai.com/v1/images/generations`, `{"model":"gpt-image-2","prompt":...,"size":"1536x1024","n":1}`,
Bearer `$OPENAI_API_KEY`, response `data[0].b64_json`. gpt-image-2 beat gpt-image-1 and DALL·E here.
- **Thumbnail:** clean, NO channel name (name lives on logo/avatar). Crop 3:2→16:9 (`crop=1536:864,scale=1280:720`).
- **Logo/banner:** the model can render clean English wordmarks, OR overlay text yourself with Pillow
  (Arial Bold, 2px shadow) for exact consistency. Use the profile-pic (icon only) small; the full name
  needs room (banner/logo). Full recipe: `lucid-science-thumbnail-style.md`.

## 5. Title research (Apify — proven step, do it every time)
`streamers/youtube-scraper`, input `{"searchQueries":[...],"maxResults":~22,"sortingOrder":"views"}`, then
`get-dataset-items` sorted desc on `viewCount`. Read titles + views + subs to find what over/under-performs.
Findings for Indian calculus audience (2026): the `(HINDI | हिंदी)` tag overperforms massively; "Differentiation"
and `अवकलन` out-pull "Derivative"; physics framing widens reach; the intuition angle ("…kya hota hai?",
"…समझो in N min", "essence of") wins the concept lane (don't fight 3-hour one-shots on raw views).

## 6. Do / Don't (quick reference)
**DO:** read frames before claiming anything · build English first then transform to Hindi · cache audio
(re-renders are free) · bind motion to `tracker.duration` · mix music audibly & verify by subtraction ·
research titles with real data · keep the folder flat · hand over freshly-named files · save learnings to
this skill after each session.
**DON'T:** start ANY production spend off a "suggest" request — recommend, then WAIT for the owner's go ·
keep rendering through a mid-build interruption (stop, re-read the whole message, confirm) ·
trust "all translated" without an AST audit · reuse chapter timestamps from a different render (recompute
from the shipping render's .srt) · put the channel name on the thumbnail · override Sarvam temp/pace ·
use music at 0.10 · let the mascot sit over equations or change the video's duration · re-open the same
filename and trust what QuickTime shows · over-engineer folders or narrate long option lists — act and
report briefly.
