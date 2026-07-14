# Validation playbook — how to PROVE sync (not vibe it)

The rule: **never claim "it's synced" from watching or from intuition.** Prove it
against the rendered artifact. Three levels, cheapest first.

## Level 1 — Frame + line spot check (per timestamp)

Ground truth for "what should be said at time T" = the burned-in subtitle on the
frame at T.

```bash
ffmpeg -y -ss T -frames:v 1 input.mp4 -vf scale=480:-1 frame.jpg
```
Read the frame. Note the on-screen subtitle. Then check what your dialogue list
(`en.json`) has placed at T (the line whose `start ≤ T`). They should be the same
scene/line. This exposed the 22.8s mega-utterance instantly (t=15s frame showed a
new scene; audio was still 12s behind).

## Level 2 — Transcribe the OUTPUT audio (the gold standard)

This is the check that NEVER lied. Slice the rendered dub's voice track and run
STT on it; confirm the spoken English at T is the expected line.

```bash
ffmpeg -y -ss T -t 5 dub_voice.wav slice.wav
# then STT slice.wav (Deepgram/Whisper, language=en) and compare to expected line
```
Use the clean voice track (pre-mux) so music doesn't confuse the STT. This is how
every "is it really fixed?" question was settled — e.g. output at 51.5s =
"Hey, Chen. You owe two thousand years of debts…" = the recovered old-man line.

## Level 3 — Whole-video offset report

Transcribe the FULL output voice track with word timestamps, then align to your
expected line list and report each line's `|actual − expected_start|`.

- **Align GLOBALLY** (`difflib.SequenceMatcher` over the two word sequences),
  not greedily per line — greedy matching mis-locates repeated words.
- Only anchor a line's time on a **contiguous ≥3-word run** (a lone common word
  can't set it).
- Report: lines aligned, mean offset, % within 0.5s / 1s / 2s, worst offenders.
- **Targets:** 95%+ within 0.5s, 100% within 1s. Best achieved: mean 0.11–0.21s,
  100% within 1s.

### The validator lies too — distrust it

Even the difflib validator threw a false 4.8s (and earlier 16.7s) outlier on a
triple-repeated word ("stop stop stop") — it anchored an earlier lone "stop."
**When the validator flags an outlier, DISPROVE it at Level 2** (transcribe that
exact slice) before "fixing" anything. In both cases the audio was correct; the
validator was wrong. A proper fix would be forced alignment (WhisperX / aeneas),
but the Level-2 spot check is the cheap, reliable arbiter.

## Coverage validation (for the "missing line" class)

- Compare detected-speech seconds to runtime; list windows > ~3s with no detected
  speech, then Level-2 check whether each is genuine silence or a missed line.
- Compare OCR line count vs ASR line count — a large gap means ASR is dropping
  speech (OCR found 114 vs ASR 73 → ASR was missing ~1/3).

## What "done" looks like

- Level-2 spot checks at the user's complaint timestamps all match.
- Level-3: ≥95% within 0.5s, with any outlier disproven at Level 2.
- Overshoot ratio (`Σ clip_dur / video_dur`) ≈ 1.0.
- 0 clips slowed >1.15×.
