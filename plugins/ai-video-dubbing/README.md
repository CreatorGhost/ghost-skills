# ai-video-dubbing

A senior, reference-backed skill for building and debugging **AI video dubbing /
recap pipelines** — turning a foreign-language video into a translated voiceover
that lands on the right moment on screen. Battle-tested on Chinese short-drama /
漫剧 / manhua / donghua → English (and Hindi) for faceless YouTube.

## The core insight

The AI parts — speech-to-text, translation, text-to-speech — are commodity APIs.
**The hard, load-bearing problem is timing: getting the pieces to agree on *when*.**
This skill encodes the architecture and the debugging discipline that actually
solve it, learned by shipping a real dubber and fighting sync for days.

## What's inside

- **`SKILL.md`** — the sync-first playbook: the winning architecture, the failure-mode
  map, the validation methodology, the environment gotchas.
- **`references/01-pipeline-architecture.md`** — every stage with concrete patterns:
  subtitle OCR, dual-pass ASR, isometric translation, the no-slow fit policy, mux,
  and recap/narration mode.
- **`references/02-sync-failure-modes.md`** — the full catalogue of sync bugs with the
  real root causes and the numbers that prove them.
- **`references/03-validation-playbook.md`** — how to PROVE sync (frame check +
  transcribe-the-output + whole-video offset report), and why to distrust your own
  validator.
- **`references/04-models-tools-pricing.md`** — STT / TTS / OCR / LLM choices, pricing,
  and tradeoffs.
- **`references/05-engineering-lessons.md`** — the transferable meta-lessons (measure
  don't guess, the bug is upstream, change the data source, be willing to revert).

## When it triggers

Building a dub/recap tool, or ANY sync complaint: "audio is drifting," "voice is
behind the visuals," "the line is missing/silent," "the voice sounds slow and
dragged," "narration doesn't match the scene."

## The one rule

Measure and validate against the **actual rendered artifact** — extract the video
frame at time T and transcribe the OUTPUT audio at time T. Never trust intuition,
and never even trust your own validator without disproving its outliers directly.
