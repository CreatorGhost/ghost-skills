# Sync failure-mode catalogue

Each entry: the symptom the user reports, what it *looks* like, the *real* root
cause, the fix, and the measurement that proves it. All numbers are from the real
build (Chinese short-drama, 278s test clip).

## 1. Audio drifts 10–20s behind the video

- **Looks like:** an audio-placement bug; "the voice is behind."
- **Real cause:** the STT grouped a whole scene into ONE 20+ second "utterance."
  A single 22.8s English block was placed at the scene start, so while the visuals
  cut through 3–4 shots, the audio was still on the first line. Drift, not delay.
- **Prove it:** measure per-block `audio_seconds / video_window_seconds`. It was
  **846s of audio for a 278s video (3×)**; one line was **22.8s**.
- **Fix:** split utterances into short sub-lines using word-level timestamps (break
  on word-gap > 0.4s or length > 5s). Longest line dropped 22.8s → 5.7s.

## 2. A line is silent / missing (the "old man on the bed" bug)

- **Looks like:** a gap or a dropped clip.
- **Real cause:** the ASR **never detected the speech** (a quiet/older voice under
  music). Between 49.9s and 56.8s the recognizer returned nothing. No placement or
  alignment algorithm can fix undetected audio.
- **Prove it:** dump the raw ASR words for the window; confirm the hole.
- **Fix, in order of power:**
  1. Run ASR on the **demucs vocal stem** too, union-merge (recovered the line at
     52.0s on the stem where the mix had nothing).
  2. Upgrade model (nova-2 → nova-3).
  3. **Best:** read the burned-in subtitle (OCR) — it's always present and perfectly
     timed; recovered the FULL line 小陈啊2000年的情债要还啊 that ASR had clipped to 陈.

## 3. Voice sounds slow / robotic / dragged

- **Looks like:** bad TTS voice quality.
- **Real cause:** you time-stretched (slowed) short clips to "fill" their slots.
  **31 of 60 clips were slowed >1.15×.** Slowing pitch-preserved audio smears
  pauses and plosives → "dragged."
- **Prove it:** count clips where `fit_duration / raw_duration > 1.15`.
- **Fix:** NEVER slow to fill. Natural speed + trailing silence. Only ever speed
  UP (to avoid colliding with the next line), capped ~1.5×. Result: 0 slowed clips.

## 4. "A few seconds of gaps in the wording"

- **Real cause:** English is more concise than the source, under-filling the slot;
  and the fill cap was too low to close it.
- **Fix that WORKS:** isometric translation — size the English to the slot by
  syllable budget so it naturally fills the time. Fix that FAILED: raising the
  slow-down cap (caused failure mode #3 — do not do this).
- **Lesson:** small gaps are acceptable; a dragged voice is not. When goals
  conflict (fill vs. natural), pick natural.

## 5. Narration (recap) races ahead or lags within a block

- **Real cause:** the LLM ignores "write N seconds" and "write N sentences"
  budgets. Asking for a sentence count produced **3× too much** audio; the block
  then over/under-ran its window.
- **Fix:** budget in **words/syllables = duration × rate**, and add a HARD
  programmatic count-and-trim pass (never trust the model's self-report). For the
  recap mode also anchor each beat to a real scene cut so a visual cut = a
  narration boundary.

## 6. Regressions I caused (cautionary)

- **Leading-silence trim** (`ffmpeg silenceremove`) to shave the ~0.5s TTS lead:
  over-trimmed some clips, blew max drift from 0.5s → 17s. **Reverted.** The
  uniform lead is imperceptible; don't touch it.
- **Fill-the-gap translation + higher slow cap:** made the voice slow (#3) with
  zero sync improvement. **Reverted.**
- Meta-lesson: two of my "improvements" were regressions caught only by
  measurement. Reverting was progress.

## Diagnostic quick-reference

- Per-line: `slot = end − start`, `avail = next.start − start`, `clip_dur` (probe
  the wav). Compression needed = `clip_dur / avail`.
- Whole-video overshoot = `Σ clip_dur / video_dur`. Target ≈ 1.0. 3× = failure #1/#5.
- Coverage: total detected speech seconds vs. runtime; big silent windows that
  aren't genuinely silent = failure #2.
