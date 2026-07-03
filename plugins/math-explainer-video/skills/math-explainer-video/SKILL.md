---
name: math-explainer-video
description: >-
  Build 3Blue1Brown-style visual, intuition-first MATH (and physics) explainer videos with Manim —
  the complete, battle-tested pipeline behind the CBSE/ICSE math YouTube channel: Hinglish-native
  narration (Sarvam aditya), per-sentence voiceover sync, the render→frame-critique→fix loop, music,
  chapter markers, and all the manim gotchas that cost real hours to discover. Use this WHENEVER the
  user wants to create, script, animate, render, edit, or plan a math or physics explainer video, a
  "why does this work" concept video, a Manim animation, or work on the math video channel — even if
  they just say "make a video on [topic]", name a CBSE/NCERT chapter, or ask for a visual proof. Also
  use it for curriculum/launch planning for the channel. It exists so we never re-do the research:
  skip straight to building.
---

# Math Explainer Video (3Blue1Brown-style, for Indian boards)

This is the captured playbook for a real, working pipeline. A pilot video (the trig identity
`sin²θ + cos²θ = 1`) was built, polished over many iterations, and a full CBSE Class 9–12 curriculum
was mapped. **Read this first, then go build — don't re-research.**

## What "good" means here (the format)
- **Complete visual lessons, 6–15 min — length set by the TOPIC, not a quota** (owner's ruling,
  2026-07-03). The core idea is to explain the concept PROPERLY: every inch, step by step, in plain
  language — meaning → first-principles derivation → worked example(s) → the general rule by pattern →
  real-world meaning → common confusions. A small topic that's fully explained in 7 minutes ships at
  7 minutes; don't pad to hit a number, don't cut corners to shrink one. Still WHY-first and fully
  visual. The market is saturated with 2-hour lecture marathons (Dear Sir 17M) and tight 3-min gems
  (3b1b); the open lane is the **complete-yet-visual 6–15 min lesson** a student can learn the whole
  topic from.
- **Strategy: CBSE-first, ICSE tagged-along, math-first.** CBSE/NCERT is ~10× the audience, the
  national standard, and the only path to a Hindi audience. The math is ~90% board-agnostic, so one
  video serves both boards — tag the CBSE chapter in the title, list ICSE chapters in the description.
- See `references/pedagogy-and-strategy.md` for the full strategy, the market gap, and monetization.

## The toolchain (already proven on this machine)
- **Manim Community Edition** (`pip install manim`) — **NOT** `3b1b/manim` (that's ManimGL, Grant's
  personal fork; different API, undocumented breaking changes). Grant's repo `github.com/3b1b/videos`
  is reference-only: mine his *techniques*, never copy his code.
- **manim-voiceover** for narration sync. **Production voice = Sarvam Bulbul v3, speaker `aditya`**
  (owner's locked choice) — scenes are authored natively in Hinglish with `SarvamService`. Deepgram is
  legacy/English-drafts only.
- **ffmpeg** for music mixing. **LaTeX** (MacTeX/BasicTeX) required for `MathTex` — put
  `/Library/TeX/texbin` on `PATH` when rendering.
- Project lives at `~/code/maths` (venv at `.venv`), flat layout: all source in
  `src/` (one `<topic>_scene.py` per video), deliverables in `Math/<Topic>/`. Built so far:
  `src/scene.py`+`scene_hi.py` (derivative, video #1), `src/circle_scene.py` (circle area, video #2).
  Curriculum: `curriculum/` (257 lessons + launch plan).

## ⚠️ The gotchas that cost hours — internalize these before writing code
1. **Deepgram TTS: request MP3, never WAV.** `encoding=mp3&bit_rate=48000`. Its streamed *WAV* writes a
   bogus ~2 GB data-chunk length in the header → mutagen (what manim-voiceover trusts) reads it as
   **~6 hours** → the render *hangs forever*. This single bug looked like a "7-minute hang." MP3 is correct.
2. **The channel ships HINGLISH-ONLY, voiced by Sarvam Bulbul v3, speaker `aditya`** (48 kHz, default
   pace/temp — never override temp/pace). Since video #2, scenes are authored NATIVELY in Hinglish (no
   English cut, no translate step); Deepgram (no Hindi support) is legacy for English drafts only. The
   narration style rules + the QA gates that run BEFORE any paid render:
   **`references/hindi-hinglish-cut.md`** (read it before writing narration).
3. **`always_redraw` mobjects can't be animated directly** — the updater overwrites every frame. To
   *highlight* a side, flash a static copy (`ShowPassingFlash`). To *morph* one into another, build
   static copies, `ReplacementTransform`, then swap to `always_redraw` at the same parameter value.
4. **`wipe()`/keep across chapters must use `get_family()`** — the scene holds the *submobjects*, not the
   VGroup, so `if m in (vgroup,)` never matches and your triangle silently fades. Keep the family set.
5. **`MovingCameraScene` + `VoiceoverScene` compose fine**: `class X(VoiceoverScene, MovingCameraScene)`.
   `self.camera.frame.save_state()` once; zoom with `self.camera.frame.animate.scale(f).move_to(m)`;
   `Restore(self.camera.frame)` to reset between chapters.
6. **`Angle(...)` can draw the reflex angle** (looks like a near-full circle). Use an `Arc` with explicit
   `start_angle`/`angle` instead.
7. **Loop music with the `aloop` filter, not `-stream_loop` on a WAV** (raw WAV seams throw "Invalid PCM
   packet" glitches — harmless, but re-encode the WAV once to silence them). `amix ... normalize=0` so
   narration stays full. **Volume ≈ 0.25–0.28, NOT 0.10.** 0.10 lands ~17 dB under the loud Hindi voice =
   the user literally can't hear it ("where's the music?"). Aim bed ~8–10 dB under the voice mean. **Verify
   with subtraction (FINAL − no-music render), not `volumedetect` of the final** — the voice masks it.
8. **Moving animations must bind `run_time` to `tracker.duration`, never hardcode it.** A hardcoded
   `run_time` front-loads the motion, then sits still for the rest of the clip — fine in the language you
   tuned, but the longer Hindi audio (~30% longer) slides the words 2-3 s past the finished motion. Capture
   `with self.say(...) as tracker:` and use `run_time=tracker.duration` (apportioned) for travelling things
   (ValueTracker slides, camera moves, dots/lines moving). One-shot accents (Write/Indicate/Flash) may keep
   a fixed `run_time`. Author it in the SOURCE scene so every language is synced at once. (See manim-pipeline.md.)
9. **VERIFY BY READING ACTUAL FRAMES — never claim "done/verified" from an assertion.** The single most
   repeated mistake this project: saying "it's fixed" after eyeballing one frame or trusting the player.
   Extract frames from the RENDERED file with ffmpeg and Read them; tile several timestamps to check motion;
   for a visual match, composite your output next to the user's reference image and Read that. It IS you
   (Claude) reading the images, not a sub-model.
10. **QuickTime caches — `open`-ing the same path twice shows a STALE frame** (looks like "no audio" / "same
    as before" / a blank). Always hand over a **freshly-named** copy, or open a **static PNG** (immune to
    player cache). Many "you didn't change it" complaints were really this.

Full technical detail, exact commands, and the reusable code: **`references/manim-pipeline.md`**.
The end-to-end process, standing user directives, the full error log, and the do/don't list:
**`references/production-playbook.md`** — read it before starting a video from scratch.

## The build loop (per video) — the FULL pipeline, end to end

⚠️ **STEP 0 — CONFIRM THE TOPIC WITH THE OWNER. NON-NEGOTIABLE.** When asked to "suggest" or plan,
the deliverable IS the suggestion: present the top 3–5 candidates from `curriculum/` with the why
(demand / gap / JEE / visual-fit), give ONE recommendation, then **STOP and wait for an explicit go on
a named topic**. Production was once started off a "suggest" request and the owner was rightly furious.
**Cost gates** — none of these may run before the topic is confirmed: Sarvam TTS on new text (~₹25–30
per video), gpt-image-2 calls, any 4K render (hours). Same rule mid-build: if the owner interrupts,
STOP renders first, re-read the whole interruption for premise changes (not just the surface
correction), and confirm before resuming.

1. **Topic confirmed** → note the slate position and the next-video tease for the outro.
2. **Write the scene NATIVELY in Hinglish** (`src/<topic>_scene.py`) — copy `assets/scene_template.py`
   (bundles `SarvamService`, `VoiceoverScene`+`MovingCameraScene`, helpers). Chapters; each beat one
   short `with self.say(...)` line (drift-free per-sentence sync); narration per
   `references/hindi-hinglish-cut.md` style; **on-screen labels stay English**. Bind moving `run_time`s
   to `tracker.duration` (gotcha #8). Add the **Root mascot** for the intro + questions/headlines only
   (`assets/root_buddy.py` + `references/mascot-root.md`).
3. **FREE pre-render QA (before any TTS spend):** (a) static layout check — throwaway `Scene` classes
   with the tricky layouts, rendered `-ql -s` (no TTS), **Read the PNGs**; (b) AST audit — every
   `say`/`chapter_title` narration arg contains Devanagari; (c) **independent Hindi-editor agent audit**
   of all narration lines (grades GOOD / too-English / too-formal / awkward / MATH-ERROR with rewrites —
   it catches heard-aloud ambiguities like "12-inch… radius 6" needing the size=diameter bridge).
   Apply fixes, THEN synthesize.
4. **Smoke-render** `-ql --media_dir build` (set `SARVAM_API_KEY`, texbin PATH). Audio is **cached** →
   re-renders free.
5. **Critique loop (the bottleneck):** extract frames (tile 4-up with `mev_grid`), **Read them**
   (gotcha #9), fix overlaps/off-screen/clipping/dead-air, re-render until clean. If a fix doesn't
   show up in the re-render, it's the stale animation cache → `--disable_caching` (see manim-pipeline.md).
6. **4K render** `-qk`. **Mix music** (Grant's Etude @ ~0.28, gotcha #7) + **compute chapters from the
   4K `.srt`** (timestamps shift 1–2 s between resolutions — always use the shipping render's srt).
7. **Title — RESEARCH IT with Apify, don't guess.** Scrape real YouTube results for the topic in India
   (`streamers/youtube-scraper`, sort by views) and read what wins. Findings that held: the **`(HINDI | हिंदी)`
   tag overperforms hugely**; **"Differentiation"/`अवकलन` out-pull "Derivative"** in Hindi titles; **physics
   framing widens reach**; the **intuition angle** ("kya hota hai?", "समझो in X min", "essence of") beats
   competing with 3-hour one-shots. Optionally scrape top-video comments for the exact pain phrases students use.
8. **Thumbnail + brand assets via gpt-image-2** (`$OPENAI_API_KEY`, `/v1/images/generations`). Thumbnail =
   the topic visual left + a huge hook (`dy/dx = ?`) right + Root peeking bottom-right; **NO channel name on
   the thumbnail** (the name lives on the logo/avatar). Follow `references/lucid-science-thumbnail-style.md`.
   Crop 3:2 → 16:9 (1280×720). Read the result to verify text/spelling.
9. **Package** into the folder convention (see production-playbook.md): topic folder gets ONLY the video(s),
   `thumbnail.png`, and ONE `README.md` (title + description + tags). All code/assets live in `src/`.
10. Open it, get human feedback, iterate. **Verify every claim by reading frames, not asserting.**

## Scripting & pedagogy (what makes it land, not just render)
The winning "why" structure (reverse-engineered from the top-performing intuition videos):
**validated-confusion hook** ("you were told to memorize this — nobody told you why") → **anchor to
something familiar** (e.g. "just like π is the same for every circle…") → **let the viewer discover it,
then name it** → **concrete numbers before the abstraction** → **real-world payoff / a board-exam
application** → **forward hook + soft subscribe**. Plus: **spoken word = shown word** (the on-screen
label matches the narration at that instant), **spoken chapter lead-ins** (never silent cuts), and
**flowing morph transitions** (the triangle *becomes* the circle — 3b1b's signature; the object
persists and transforms rather than fading to black). Details + research citations:
`references/pedagogy-and-strategy.md`.

## Where everything is
- `references/production-playbook.md` — **the end-to-end process + standing user directives + full error log + do/don't. Read this first when starting fresh.**
- `assets/scene_template.py` — copy this to start a new video (self-contained, all helpers).
- `scripts/build_helpers.sh` — render / extract-frames / mix-music / chapters / description helpers.
- `references/manim-pipeline.md` — toolchain, exact commands, every gotcha (incl. the `tracker.duration` sync rule), scene patterns, the morph + side-flash recipes.
- `references/hindi-hinglish-cut.md` — **the Hinglish narration playbook**: Sarvam/aditya, the natural-Hinglish style rules, native authoring (the default since video #2), the AST + independent-agent QA gates, workspace hygiene. (The EN→HI transform section is legacy, video #1 only.)
- `references/mascot-root.md` + `assets/root_buddy.py` — **"Root"**, the channel mascot (√ with eyes): design, the reveal, and the RULE (show only for questions/headlines, slide off the instant equations/graphs draw), animated without touching audio.
- `references/pedagogy-and-strategy.md` — script structure, the research findings, CBSE strategy, the market gap.
- `references/curriculum.md` — the 257-lesson map + the 12-video launch plan + how it was generated (a Workflow fan-out, one agent per class).
