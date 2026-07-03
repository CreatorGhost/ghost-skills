# The Hinglish narration playbook — style, native authoring, QA gates

The channel ships **HINGLISH ONLY**, voiced with **Sarvam Bulbul v3, speaker `aditya`** (48 kHz, default
pace/temp — overriding temperature added hiss; lowercase speaker names).

**Since video #2 (circle area), scenes are authored NATIVELY in Hinglish** — owner's directive ("no only
english now just hindi + english mixed one"): put `SarvamService` directly in the scene, write every
`self.say(...)` in the §1 style below, keep on-screen labels English. There is NO English cut and NO
translate step. Section §2–§3 (the EN→HI transform) is **LEGACY — video #1 only**; keep it for
maintaining that video, don't use it for new ones.

## Native-authoring QA gates (run BEFORE the first TTS render — synthesis costs money)
1. **Static layout check (free):** throwaway `Scene` classes with the tricky layouts, `-ql -s`, Read the PNGs.
2. **AST audit:** parse the scene, walk every `self.say`/`chapter_title` narration arg, assert each
   contains a Devanagari char (`any('ऀ'<=c<='ॿ' for c in s)`).
3. **Independent Hindi-editor agent:** dump the numbered narration lines to a file, spawn a fresh agent as
   a native-Hindi script editor to grade each line GOOD / too-English / too-formal / awkward / MATH-ERROR
   with full replacement rewrites. On video #2 it flagged 15/55 lines — vocabulary a Class-10 kid doesn't
   know (snip, sliver, compute → काटो, पतला सा टुकड़ा, calculate), gender ("ये trick" → "आती है असली trick"),
   idiom consistency ("twenty-two BY seven", never "over"), and a real heard-aloud ambiguity: "12-inch pizza,
   radius 6" needs the "pizza size = diameter" bridge or it sounds like a mistake.

## 1. The narration STYLE — natural bilingual-YouTuber Hinglish (not a percentage)
It must sound like a real Hindi-medium teacher/YouTuber talking to students — **NOT** a translation.
The owner rejected two extremes before landing here:
- ❌ English nouns mechanically dropped into Hindi sentences → "too much English" (sounds dubbed).
- ❌ ~90% literary/शुद्ध Hindi (निशान for symbol, रफ़्तार for speed) → "too formal" (sounds like a textbook).
- ✅ **Natural code-switching that flows when spoken aloud.**

The rule:
- **English** for (a) math/technical TERMS — derivative, slope, tangent, secant, limit, function, power
  rule, rate of change, velocity, exponent, equation; (b) **every formula/number read aloud** ("f of x
  plus h, all over h", "two x", "three, two point five, two point one"); (c) **punchy rhetorical HOOKS
  spoken whole in English** — "but do you actually know what it really is?", "how fast are you going right
  now?", "that's nonsense", "that's literally your speedometer"; (d) **common loanwords Indians genuinely
  say in English** — symbol, speed, plug, answer, question, car, easy, simple, idea, point, curve, line.
- **Hindi** carries the warm explanatory/connective frame — चलो, देखो, मान लो, ये लो, आज के video के अंत तक,
  जहाँ भी कुछ change होता है... the teaching voice.
- **Do NOT over-formalize**: symbol≠निशान, speed≠रफ़्तार; keep measure/plug/answer/question English.
- "times" → **"into"** (Indian math idiom). Multiply read aloud is "into", not "times".
- **On-screen labels/headings stay English** (chapter titles, formula labels). Only the SPOKEN track is Hinglish.
- Write **Devanagari for Hindi + Latin for English terms** — Sarvam bulbul:v3 code-switches this perfectly.

## 2. LEGACY (video #1 only): the transform pipeline (`translate_hi.py`)
Generate `scene_hi.py` from `scene.py` programmatically so the visuals stay byte-identical:
1. Insert the `SarvamService` class, swap `set_speech_service(DeepgramService(...))` → `SarvamService(speaker="aditya", lang="hi-IN")`.
2. A dict `HI = { "<exact English narration>": "<Hinglish>" , ... }` (one entry per `self.say` / `chapter_title` line).
3. Regex-replace each `self.say("...")` / `self.chapter_title(label, "...")` narration arg with its Hinglish.
   Structural code (`as tracker:`, `run_time=...`) is outside the matched group and is preserved — so the
   sync fix in the source scene flows into the Hindi cut automatically.

## 3. LEGACY: ⚠️ the transform's silent bug — multi-line string literals
Narration in `scene.py` is often a **multi-line implicit concatenation**:
```python
with self.say("First sentence. "
              "Second sentence."):
```
`ast.literal_eval('"a"\n"b"')` **raises** (two statements, not one expression). If your replacer does
`ast.literal_eval(group)` in a `try/except` that returns the original on failure, those lines **silently
stay English** and the script still prints "all translated". Result: the long lines (which are exactly the
multi-line ones) play in English; only the short single-line ones translate. This shipped once.
**Fix:** wrap the captured group in parens before eval — `ast.literal_eval("(" + group + ")")` — and make
the `except` branch RECORD the failure (append to a `missed` list), never swallow it silently.

## 4. QA gates — verify BEFORE rendering (renders cost time/money)
1. **AST audit (trust this, not the script's own "all translated" message):** parse `scene_hi.py`, walk
   every `self.say` / `chapter_title` string arg, assert each contains a Devanagari char
   (`any('ऀ'<=c<='ॿ' for c in s)`). Zero English-only lines = no leak. This is independent of the buggy regex.
2. **Independent agent audit:** dump all lines (EN→HI) to a markdown file and spawn a fresh general-purpose
   agent as a native-Hindi editor to grade each line GOOD / too-English / too-formal / awkward / math-error
   with concrete rewrites. It caught a real one: "exponent एक से कम" (could be heard as "less than one",
   corrupting the power rule) → "exponent एक कम"; plus `video` gender consistency (इस video / पूरी video).
3. **Post-render proof the cache served the NEW audio (not stale):** the auto `.srt` is generated from the
   actual text rendered — grep it to confirm the fixed lines are present and old English originals are 0.
   "Cached" is keyed on the exact text, so changed lines get fresh clips; old clips just go unreferenced.

## 5. Length & timing consequence
Hindi runs **~30% longer** than English (e.g. 7:50 → ~10:05). This is why motion `run_time`s MUST bind to
`tracker.duration` (see manim-pipeline.md) — and why **chapter timestamps must be recomputed** from the
Hindi `.srt`, never copied from the English description.

## 6. Workspace hygiene
Renders pile up fast (partial-movie-files, intermediate-res renders, preview copies, logs → hundreds of MB).
Keep a clean structure: source `.py` at root; `final/` for deliverables (rename clearly: `*_english_4k.mp4`,
`*_hindi_4k.mp4`, descriptions, script); `build/` as the manim `--media_dir` holding only the regenerable
`voiceovers/` TTS cache (move it, don't delete — re-synth costs real money). Delete `build/videos`, logs,
preview copies freely. **Gotcha:** `open <same path>` twice just re-focuses QuickTime's stale window (looks
like "no audio / old version") — copy to a fresh-named file to force a reload when showing a new render.
