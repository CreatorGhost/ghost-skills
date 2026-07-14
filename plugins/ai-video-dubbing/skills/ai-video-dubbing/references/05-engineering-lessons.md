# Engineering lessons — the transferable part

These generalize well beyond dubbing. They are the real reason this skill exists:
so the next build skips the detours.

## 1. Measure before you fix; validate against the real artifact

Every guess-based change here failed or regressed. Every data-based change worked.
"The English is too short so there are gaps" was a plausible story that led to a
wrong fix. The truth only appeared when I measured `Σ audio / video = 3×` and saw
one 22.8s line. Then: extract the frame, transcribe the OUTPUT, compare. That loop
never lied. Intuition and even the custom validator did.

## 2. The bug is upstream of where it hurts

The symptom was "audio out of sync." The chain of real causes, each discovered
only after fixing the previous:
- placement? no →
- **segmentation** (mega-utterances) →
- **detection** (ASR missing speech entirely) →
- **the data source** (should be reading the subtitles, not the audio).
Fixing the visible layer repeatedly failed because the cause was one layer up.

## 3. Research the domain before engineering it

Before rebuilding, I researched "how do faceless recap/dub creators actually do
this." The findings reframed everything in one pass: pros CUT VIDEO to the script
(not the reverse); budget length in words/syllables (LLMs ignore "N seconds");
NEVER slow audio to fill (that's the dragged voice); size to the slot before TTS.
An afternoon of research replaced days of trial-and-error.

## 4. Change the data source, not just the algorithm

The single biggest accuracy jump was not a better model or a cleverer placement
algorithm — it was noticing the **burned-in subtitles that were on screen the
whole time** and reading them with OCR. Perfect text, frame-accurate timing, zero
coverage holes. When an algorithm keeps fighting bad inputs, look for a better
input.

## 5. Be willing to revert

Two "improvements" made things worse and were reverted:
- filling gaps by over-writing translations + raising the slow cap → dragged voice;
- trimming leading TTS silence → over-trimmed, drift 0.5s → 17s.
Reverting was progress. Measurement is what made reverting an obvious call rather
than an ego hit.

## 6. Cheap model + right architecture beats a bigger model

gpt-5-mini beat gpt-4o for this task; the wins were structural (word budgets,
sub-line splitting, dual-pass ASR, OCR source), not from spending more on
inference. Spend the effort on the pipeline shape, not the model tier.

## 7. Distrust your own tools

The sync validator itself had false positives (mis-locating repeated words),
producing scary 16.7s / 4.8s "drift" numbers that were provably wrong. A test that
can be wrong must itself be validated. When a tool flags a problem, confirm the
problem exists by an independent, more-direct method before acting.

## 8. Honesty in reporting

When asked "are you SURE it's correct?", the right answer was: "for the points I
directly transcribed, yes; across the whole video my validator says 96% but it has
known false positives, so here's the direct proof." Report what you actually
verified vs. what you assume. Over-claiming sync you haven't proven wastes
everyone's time when it's wrong on screen.

## The debugging loop that worked (reusable)

1. Reproduce with a concrete artifact (a timestamp + a screenshot).
2. Measure the relevant quantity (offset, overshoot ratio, coverage).
3. Form ONE hypothesis about the root cause; check it's upstream, not the symptom.
4. Make the smallest change; re-measure.
5. If it didn't improve the number, REVERT — don't stack fixes.
6. Prove the win against the rendered output, not intuition.
