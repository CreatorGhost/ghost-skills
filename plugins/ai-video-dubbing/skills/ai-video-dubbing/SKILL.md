---
name: ai-video-dubbing
description: >-
  Build or debug an AI video DUBBING / RECAP pipeline — a foreign-language video
  turned into a translated voiceover that lands on the right moment on screen.
  Battle-tested on Chinese short-drama / 漫剧 / manhua / donghua → English (and
  Hindi) for faceless YouTube. Use whenever the task is: dub or recap a video,
  translate speech and re-voice it, or FIX audio-video sync — "audio is drifting",
  "voice is behind the visuals", "the line is missing / silent", "the voice sounds
  slow and dragged", "it's out of sync", "narration doesn't match the scene". The
  core insight, learned the hard way: the AI (STT/translate/TTS) is the easy part;
  getting the pieces to agree on WHEN is the whole game. Encodes the winning
  architecture (burned-in SUBTITLE OCR as ground-truth timing → isometric
  translation with syllable budgets → timestamp-anchored TTS with a NO-SLOW fit
  policy → mux), the ASR dual-pass (full mix + demucs vocal stem) coverage fix,
  the catalogue of sync failure modes with numeric limits, and the validation
  methodology that never lies (extract the frame + transcribe the OUTPUT audio).
  Also covers recap/first-person narration mode. Read this BEFORE writing any
  transcribe→translate→TTS→mux code or debugging a sync complaint.
---

# AI Video Dubbing & Recap — the sync-first playbook

You are building or fixing a pipeline that takes a video in language A and
produces a video with a language-B voiceover that **lands on the right scene at
the right time**. Everything here was learned by shipping a Chinese short-drama →
English dubber and fighting sync for real. The APIs (speech-to-text, translate,
text-to-speech) are commodities. **The hard, load-bearing problem is timing.**

## The one principle that governs everything

> **Measure and validate against the actual rendered artifact — never your
> intuition, and never even your own validator.** Every guess-based fix in this
> project failed or regressed. Every data-based fix worked. The only ground truth
> that never lied was: extract the video frame at time T, and transcribe the
> OUTPUT audio at time T, and compare.

If you take nothing else: before claiming "it's synced," prove it (see
`references/03-validation-playbook.md`). Before "fixing" a sync bug, measure where
the audio actually is vs. where it should be.

## When to use this skill

- Building a dub/recap tool (STT/OCR → translate → TTS → mux).
- ANY sync complaint: audio behind/ahead of video, missing/late lines, robotic
  slow voice, narration describing the wrong scene.
- Choosing STT/TTS/OCR/LLM models for a dubbing pipeline (pricing in
  `references/04-models-tools-pricing.md`).

## The winning architecture (use this by default)

For videos that have **burned-in subtitles** (Chinese short-dramas always do),
the subtitles are a *perfect ground-truth script with frame-accurate timing*.
Use them. This single decision eliminated the entire class of "did we detect it /
is it in the right place" bugs.

```
1. DIALOGUE SOURCE (pick best available):
   a. Burned-in subtitle OCR  ← BEST: exact text + frame-accurate timing
      RapidOCR on the CENTER-bottom band, watermark-filtered, frame-diff dedup
      -> [{zh, start, end}]
   b. ASR fallback (no subs): Deepgram nova-3, DUAL-PASS on full mix AND the
      demucs vocal stem, union-merged (stem recovers speech-over-music the mix
      drops). Word-level timestamps. Split long (>~6s) utterances into sub-lines.
2. TRANSLATE — isometric: per-line SYLLABLE budget sized to the AVAILABLE window
   (gap to next line), then a VERIFY pass that recounts syllables and rewrites
   over-long lines shorter. Syllables predict spoken duration; words/seconds don't.
3. TTS — generate at NATURAL speed. Place each clip at its exact timestamp.
4. FIT — NEVER slow a clip to fill a slot (that is the "dragged voice"). Only
   speed up (mildly, cap ~1.5x) when a clip would collide with the next line;
   otherwise leave a short silence (invisible to viewers).
5. MUX — voice over the footage. Original music/SFX is OPTIONAL (demucs
   sidechain-duck) — drop it freely if it muddies the voice.
```

Full stage-by-stage detail + the exact code patterns: `references/01-pipeline-architecture.md`.

## The sync failure-mode map (what actually goes wrong)

Read `references/02-sync-failure-modes.md` for the full catalogue with numbers.
The greatest hits:

| Symptom | Real root cause (NOT what it looks like) | Fix |
|---|---|---|
| Audio 10–20s behind video, drifts | STT grouped a scene into ONE 20s+ "utterance"; the whole block is placed at the scene start | Split utterances into short sub-lines on word-gap / max-length using word timestamps |
| A line is silent / missing | STT never detected that speech (speech-over-music) — no placement can fix undetected audio | Dual-pass ASR (mix + demucs vocal stem), or better: subtitle OCR |
| Voice sounds slow / robotic / dragged | Time-stretching short clips to "fill gaps" | NEVER slow to fill; natural speed + brief silence; only speed up to avoid collision |
| "Few-second gaps in wording" | English is more concise than source; slot under-filled | Isometric translation (fill the slot by budget) — but never at the cost of #3 |
| Narration races ahead / lags within a block | 3× over-generation (asked for "N sentences" not words) | Word/syllable budget = duration × rate, with a HARD count-and-trim pass |

## The validation playbook (how you PROVE it)

Never trust "it looks synced." Do this (`references/03-validation-playbook.md`):

1. **Frame check** — `ffmpeg -ss T -frames:v 1 in.mp4 f.jpg`, read the frame,
   note the on-screen (burned-in) subtitle = ground truth for time T.
2. **Output-audio check** — slice the rendered dub at T and transcribe it; confirm
   the spoken English matches the line whose slot covers T.
3. **Whole-video** — transcribe the full output with word timestamps, GLOBAL-align
   (difflib, not greedy) to your expected line list, report each line's
   |actual − expected| offset. Target: 95%+ within 0.5s, 100% within 1s.
   Caveat: even this validator throws false positives on repeated short words
   ("stop stop stop") — when it flags an outlier, DISPROVE it by transcribing that
   exact slice before "fixing" anything.

## Hard-won engineering lessons (the transferable part)

Full write-up: `references/05-engineering-lessons.md`. In one screen:

1. **Measure before you fix.** Guessing produced only regressions.
2. **The bug is upstream of where it hurts.** A "sync" symptom was really
   segmentation, then detection, then the data source.
3. **Research the domain before engineering it.** "How do the pros do this"
   (they cut video to the script; budget words; never slow to fill) reframed the
   whole build in one pass.
4. **Change the data source, not just the algorithm.** The biggest accuracy win
   was reading the subtitles that were on screen the whole time — not a bigger model.
5. **Be willing to revert.** Two "improvements" (fill-the-gap, leading-silence
   trim) made it worse. Undoing them was progress.
6. **Cheap model + right architecture > big model.** gpt-5-mini beat gpt-4o here;
   the wins were structural.
7. **Distrust your own tools.** The sync validator had false positives; only the
   raw output transcription settled truth.

## Environment gotchas (save hours)

- **librosa time-stretch is broken** in many envs (numpy/numba binary mismatch).
  Use **ffmpeg `atempo`** for all pitch-preserving stretch — never librosa.
- **PaddleOCR is painful on macOS arm64.** Use **`rapidocr-onnxruntime`** (same
  PP-OCR models via ONNX, no paddle dependency) for cross-platform.
- **gpt-5.x models** need `max_completion_tokens` + `reasoning_effort` and reject
  `temperature` — branch your chat wrapper by model family.
- **Deepgram diarization / anime speaker-ID is weak** (~2× DER on stylized voices,
  an unsolved research problem) — keep a pitch-based gender override as a backstop.

Reference index:
- `references/01-pipeline-architecture.md` — every stage, code patterns, params
- `references/02-sync-failure-modes.md` — full failure catalogue with numbers
- `references/03-validation-playbook.md` — the prove-it methodology + validator
- `references/04-models-tools-pricing.md` — STT/TTS/OCR/LLM choices + pricing
- `references/05-engineering-lessons.md` — the meta-lessons, long form
