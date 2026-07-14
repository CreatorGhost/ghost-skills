# Pipeline architecture — stage by stage

The dubbing engine is a series of cached stages. Cache every stage to disk so
re-runs skip finished work (STT, translation, TTS clips, separation are all
expensive). Below is the recommended design with the concrete patterns that
worked.

## Stage 0 — audio + (optional) source separation

- Extract 16 kHz mono WAV for ASR: `ffmpeg -i in.mp4 -ac 1 -ar 16000 -vn a.wav`.
- **demucs** two-stem split (`--two-stems=vocals`) gives `vocals.wav` (speech) and
  `no_vocals.wav` (music/SFX). Used two ways:
  - vocal stem → a second ASR pass (recovers speech-over-music the mix drops).
  - `no_vocals` → the background bed at mux time (optional).
- demucs is slow on CPU; it uses GPU/MPS when available. Cache the output.

## Stage 1 — DIALOGUE SOURCE (the make-or-break decision)

### 1a. Burned-in subtitle OCR  (BEST when subtitles exist)

Short-drama / manhua / donghua videos have hardcoded, perfectly-timed subtitles.
They are a ground-truth script. Extract them:

- Sample frames every ~0.3s (`cv2.VideoCapture` + `CAP_PROP_POS_MSEC`).
- Crop the **center-bottom band** (e.g. rows 0.80–0.99, cols 0.10–0.90) — this
  isolates the dialogue subtitle and EXCLUDES the right-side channel watermark.
- OCR with **RapidOCR** (`rapidocr-onnxruntime` — ONNX PP-OCR models, no
  paddlepaddle install pain, works macOS arm64 + Windows).
- Keep the **widest** high-confidence CJK box (the subtitle is the biggest text);
  drop boxes matching a watermark regex (`@`, channel name, etc.).
- Dedup consecutive frames by similarity (`difflib.SequenceMatcher ratio > 0.7`):
  same text → extend `end`; different → close the record, open a new one; keep the
  longest reading seen for that line.
- Output `[{zh, start, end, speaker:0}]`, cached to `ocr_subs.json`.

Result on the reference video: **114 clean lines** vs 73 from ASR, frame-accurate,
recovered lines ASR had dropped entirely. This is the single biggest accuracy
lever. OCR runs ~900 frame-reads for a 5-min video (~2–4 min CPU); a future
optimization is a frame-diff pre-filter so you only OCR on change (research says
~60–100 real OCR calls suffice).

### 1b. ASR fallback (no subtitles) — max-recall dual pass

Never trust one ASR pass. Deepgram **nova-3** (`language=zh`, utterances +
word-level timestamps + smart_format), run on **both** the full mix AND the demucs
vocal stem, then **union-merge**: keep all mix utterances, and add any stem
utterance whose time window is <50% covered by the mix (borrow the nearest mix
utterance's speaker id). The stem pass recovered a 7-second line the mix dropped.

Then **split long utterances into sub-lines** using word timestamps — otherwise a
20s+ monologue plays as one block over many scenes:
- break when the pause between words > ~0.4s OR the sub-line reaches ~5s;
- never cut a sub-line shorter than ~1.2s (avoids fragmenting fast speech);
- Chinese words join with no space.

### `dialogue(source)` dispatcher

`source="ocr"` → try OCR; if it yields < ~5 lines or errors, fall back to ASR.
Single-voice dub uses this. Multi-voice (per-character) stays on diarized ASR
because OCR has no speaker labels.

## Stage 2 — TRANSLATE (isometric / length-controlled)

The goal: English whose SPOKEN duration ≈ the source line's slot, so it fits with
little/no time-stretch. This is "isometric MT" (Amazon/IWSLT dubbing research).

- **Budget in SYLLABLES, not words or seconds.** Syllables predict English TTS
  duration far better. `budget = min(slot, gap_to_next_line) × SYL_PER_SEC`, where
  `SYL_PER_SEC ≈ 4.5` for Deepgram Aura (calibrate once per voice: synthesize a
  known text, measure syllables/sec).
- Prompt: "write English about N syllables (±10%); count syllables before
  answering; faithful, colloquial, match tone; rephrase freely but never invent
  plot."
- **VERIFY pass** (never trust the model's self-count): recount syllables in Python
  (vowel-group estimate is fine), and for any line > ~1.15× its budget, do ONE
  rewrite call ("shorten to at most N syllables"). This kills over-generation at
  the source, so the fit stage barely has to compress.
- Batch ~20 lines/call; self-heal JSON parse failures by recursively splitting the
  batch. gpt-5-mini or gpt-4o-mini both work well and are cheap.

## Stage 3 + 4 — TTS and the FIT policy (the anti-"slow voice" rule)

- Generate each line at **natural speed** (no speed param games).
- Place each clip at `int(line.start × sr)` on a zeroed timeline (absolute
  placement → no cumulative drift is even possible).
- **Fit policy — the core numbers:**
  - `avail = next_line.start − this_line.start` (room before the next line).
  - If `clip_dur ≤ avail`: **leave it at natural speed.** Any leftover is silence
    (invisible). **DO NOT slow it to fill** — that was the dragged-voice bug.
  - If `clip_dur > avail`: speed up (ffmpeg `atempo = clip_dur/avail`), capped at
    ~1.5× (research: >1.5× sounds rushed). Isometric translation should make this
    rare. Beyond the cap, prefer rewriting the line shorter over chipmunk audio.
  - HARD RULE: atempo factor ≥ 1.0 for dubbing (only speed up, never slow).
- Do NOT trim leading silence off TTS clips — `silenceremove` over-trims some
  clips and regressed sync badly (max drift 0.5s → 17s). The uniform ~0.5s TTS
  lead-in is imperceptible.
- Use **ffmpeg atempo** (chain for factors outside 0.5–2.0), never librosa.

## Stage 5 — MUX

- Voice-only: overlay the voice track, `loudnorm` to −16 LUFS.
- With music: `sidechaincompress` (music ducks under the voice) + `loudnorm`.
  Original BGM/SFX is OPTIONAL — if separation is imperfect or it muddies clarity,
  ship voice-only. Accuracy/clarity beats ambience.

## Recap / first-person NARRATION mode (a different product)

Not a line-for-line dub — a single narrator retells the story over the footage.
Different rules:
- Tie narration to **scene cuts** (PySceneDetect) merged into ~12–24s beats so a
  visual cut = a narration boundary; generate per beat with a WORD budget sized to
  the beat, hard-trim overshoot, carry a rolling "story so far" recap for
  continuity, place each beat's audio at its timestamp.
- Style formula (reverse-engineered from top recap channels): first-person present
  tense, cold-open hook, short punchy sentences, concrete names/numbers, dramatic
  irony, cliffhanger beats. Force ENGLISH explicitly or the model may echo the
  source language.
- Fill gaps with a mild ffmpeg-atempo stretch capped ~1.25× (this mode CAN stretch
  a little to fill, unlike the dub).
