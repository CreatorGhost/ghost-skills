<h1 align="center">🎬 math-explainer-video</h1>

<p align="center">
  <strong>3Blue1Brown-style math explainer videos, end to end, with Manim.</strong><br>
  A real channel's battle-tested pipeline: script → animate → TTS-sync → critique → 4K → thumbnail.
</p>

<p align="center">
  <a href="../../README.md">ghost-skills</a> •
  <a href="#install">Install</a> •
  <a href="skills/math-explainer-video/SKILL.md">SKILL.md</a> •
  <a href="skills/math-explainer-video/references/production-playbook.md">Production playbook</a>
</p>

<p align="center">
  <img alt="engine" src="https://img.shields.io/badge/Manim-Community%20Edition-2563eb">
  <img alt="voice" src="https://img.shields.io/badge/TTS-Sarvam%20%C2%B7%20Deepgram-3fb950">
  <img alt="output" src="https://img.shields.io/badge/output-4K%2060fps%20%2B%20chapters%20%2B%20music-8b5cf6">
</p>

---

## What is this?

A skill that turns Claude into the production crew for a math (or physics) explainer channel. It captures a **real, shipping YouTube pipeline** — not a toy demo — including every hard-won lesson: the manim gotchas that hang renders, the TTS sync rule that survives any narration length, the QA gates that run *before* you spend money on synthesis, and the frame-reading critique loop that separates polished video from AI slop.

## The pipeline it teaches

1. **Topic gate** — present ranked candidates from a curriculum, get an explicit go *before* any paid step.
2. **Scene authoring** — `VoiceoverScene` + `MovingCameraScene`, per-sentence narration sync, motion `run_time` bound to narration duration, a mascot with strict usage rules.
3. **Free pre-render QA** — static layout frames (no TTS), an AST audit of every narration line, and an independent editor-agent review of the script.
4. **Smoke render → frame critique** — extract frames, tile them 4-up, actually read them; fix overlaps/clipping; the stale-animation-cache trap and its fix.
5. **4K render, music, chapters** — audible music bed verified by *subtraction*, chapter timestamps recomputed from the shipping render's `.srt`.
6. **Title research + thumbnail** — scrape real YouTube results instead of guessing; a locked thumbnail recipe with gpt-image-2.

## What's inside

- `SKILL.md` — the build loop, cost gates, and the 10 gotchas that cost real hours
- `references/production-playbook.md` — process discipline, standing directives, full error log, do/don't
- `references/manim-pipeline.md` — exact commands, sync rules, reusable geometry recipes
- `references/hindi-hinglish-cut.md` — natural bilingual narration style + pre-render QA gates
- `references/pedagogy-and-strategy.md` — the script structure that lands, research-backed
- `references/mascot-root.md`, `references/lucid-science-thumbnail-style.md`, `references/curriculum.md`
- `assets/scene_template.py`, `assets/root_buddy.py`, `scripts/build_helpers.sh`, `scripts/sarvam_service.py`

## Install

```bash
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install math-explainer-video@ghost-skills
```

Then just ask: *"make a video on why sin²+cos²=1"* — the skill handles the rest.

## Requirements

- Python venv with `manim` + `manim-voiceover`, `ffmpeg`, LaTeX (for `MathTex`)
- TTS API key in env: `SARVAM_API_KEY` (Hindi/Hinglish) or `DEEPGRAM_API_KEY` (English)
- `OPENAI_API_KEY` for thumbnails (gpt-image-2), optional Apify for title research
