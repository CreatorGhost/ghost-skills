# Models, tools & pricing (2026)

Recommendations from head-to-head testing + research on Mandarin drama/anime
audio. Verify current prices at the vendor before quoting — these move.

## Speech-to-text (STT)

| Option | Notes | Word timestamps | Pricing (pay-go) |
|---|---|---|---|
| **Deepgram nova-3** (chosen) | Current model; big claimed Mandarin WER gain over nova-2. Multilingual for zh. | yes | ~$0.0092/min prerecorded (multilingual), ~$0.0058/min streaming |
| Deepgram nova-2 | Older; dropped 7s of speech on the test clip. | yes | ~$0.0043/min prerecorded |
| ElevenLabs Scribe v2 | Strongest-evidenced Mandarin commercial claim; word+diarization | yes | ~$0.22/hr |
| FunASR Paraformer-zh / SenseVoice | Best open-source CER, non-autoregressive (no hallucination loop); local | char-level | free (self-host) |
| gpt-4o-transcribe / Google Chirp 3 | **No word timestamps → disqualified for dubbing** | no | — |

- **The real win is METHOD, not model:** dual-pass (mix + demucs vocal stem) +
  union-merge catches speech any single pass drops. nova-3 vs nova-2 is a modest
  incremental upgrade at trivial extra cost (~$0.0015 per 5-min video).
- **Diarization is weak on anime/stylized voices** (~2× DER, an open research
  problem per 2025-26 papers). Treat auto-diarization as assistive; keep a
  pitch-based gender override (librosa.pyin MODE on the isolated vocal stem — MODE,
  not median, to dodge octave-doubling).

## Subtitle OCR (the accuracy breakthrough for subtitled video)

- **RapidOCR (`rapidocr-onnxruntime`)** — PP-OCR models via ONNX runtime, NO
  paddlepaddle (which is broken/painful on macOS arm64). Cross-platform. ~$0.
- Pipeline: center-bottom crop → OCR → watermark filter → frame-diff dedup.
- >95% char accuracy on clean drama hardsubs; frame-accurate timing.
- Alternatives: PaddleOCR PP-OCRv5 (more accurate, install pain), macOS Vision
  (fast, Mac-only), VLM per-unique-line (gpt-4o-mini/Gemini Flash, pennies, good
  as a low-confidence arbitration pass, weak as primary).

## Text-to-speech (TTS)

| Option | Speed/duration control | Notes | Pricing |
|---|---|---|---|
| **Deepgram Aura-2** (chosen) | `speed` 0.7–1.5 (Early Access) | Natural narrator voices (Odysseus ★). ~4.5 syllables/sec — calibrate. | ~$0.030/1k chars |
| OpenAI gpt-4o-mini-tts | `instructions` ("speak quickly"), imprecise | Needed for acted-emotion (per-line style tags) | cheap |
| ElevenLabs | `speed` 0.7–1.2 | Degrades at extremes | pricier |
| Azure Speech | SSML `<mstts:audioduration>` = exact target ms | Only major engine with true target-duration TTS — cleanest for dubbing | — |
| F5-TTS (open) | duration is a generation input | Local option | free |

- Duration control order (pro practice): isometric translation FIRST (get the
  length right in words), TTS native speed SECOND (small), post-stretch LAST and
  LEAST. Accept ±10–20%; beyond that, rewrite the line, don't stretch.

## LLM for translation / narration

- **gpt-5-mini** — cheaper than gpt-4o AND better first-person POV than gpt-5-nano
  (which just literal-translates). Good default. gpt-4o-mini also fine for dubbing.
- **gpt-5.x param quirk:** use `max_completion_tokens` + `reasoning_effort='low'`,
  and DO NOT send `temperature`. Branch your chat wrapper by model family. Give
  reasoning models generous max tokens — reasoning tokens eat the budget and a low
  cap yields truncated/empty JSON.
- Groq `openai/gpt-oss-120b` (OpenAI-compatible) is a zero-cost fallback for
  translation; free tier caps request size (~8k TPM → keep max_tokens ~2000).

## Supporting tools

- **demucs** — vocal/music separation (two-stems=vocals). GPU/MPS accelerated.
- **PySceneDetect** (`scenedetect` + `opencv-python-headless`) — scene cuts for
  recap-mode beat boundaries.
- **ffmpeg** — the workhorse: extract, `atempo` (pitch-preserving stretch — use
  this, NOT librosa), `sidechaincompress` + `loudnorm` for mux, frame extraction.
- **static-ffmpeg** — bundle ffmpeg cross-platform without a PATH dependency.
- Silero VAD — VAD-vs-ASR diff to auto-flag coverage holes (useful for
  subtitle-free video; redundant when OCR gives complete coverage).
