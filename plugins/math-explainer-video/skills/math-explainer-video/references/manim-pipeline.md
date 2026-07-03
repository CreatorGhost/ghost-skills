# Manim pipeline — toolchain, commands, gotchas, recipes

## Environment setup (one time)
```bash
cd ~/code/maths
python3 -m venv .venv
.venv/bin/pip install manim manim-voiceover openpyxl
# LaTeX (MathTex) must exist; on macOS it's MacTeX/BasicTeX at /Library/TeX/texbin
which latex dvisvgm    # if missing: brew install --cask mactex-no-gui (or basictex)
which ffmpeg           # required for audio mux
```
Always prepend texbin to PATH when rendering so `MathTex` works:
`PATH="/Library/TeX/texbin:$PATH" .venv/bin/manim ...`

## Rendering
```bash
export DEEPGRAM_API_KEY=...        # user supplies; never hardcode in committed files
# smoke test (fast, 480p15) — validate layout + sync, audio is cached so this is cheap:
PATH="/Library/TeX/texbin:$PATH" .venv/bin/manim -ql --media_dir out scene.py SceneName
# final (1080p60):
PATH="/Library/TeX/texbin:$PATH" .venv/bin/manim -qh --media_dir out scene.py SceneName
```
manim-voiceover auto-embeds the narration audio into the MP4 **and** auto-generates a `.srt`
(captions for free) under `out/videos/scene/<res>/`.

## The frame-critique loop (the real quality bottleneck)
LLM-authored manim *compiles* easily but *looks right* rarely on the first try (text/formula
overlap, off-screen elements, clipping, dead air during long narration). So always:
```bash
VID=out/videos/scene/480p15/SceneName.mp4
ffmpeg -nostdin -loglevel error -ss <seconds> -i "$VID" -frames:v 1 frame.png -y
```
Then **Read the PNG**, diagnose, fix the scene, re-render. Repeat until clean. This loop is
non-optional and is where most of the iterations go. Real bugs caught this way on the pilot:
reflex angle arc, label/“ground” overlaps, font-60 climax clipping off-screen edge, dead-air when
an animation finished long before its narration, a stray subtitle that never faded.

## The Deepgram voiceover service (reusable, drop-in)
Custom `manim_voiceover` SpeechService. **MP3, not WAV** (WAV header → 6h duration → infinite hang).
Reads key from `$DEEPGRAM_API_KEY`. Results are cached by manim-voiceover, so re-renders cost nothing.
```python
import json, os, urllib.request
from pathlib import Path
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService, initialize_speech_service, path_to_string

class DeepgramService(SpeechService):
    def __init__(self, model="aura-2-thalia-en", api_key=None, **kwargs):
        initialize_speech_service(self, kwargs)
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY", "")

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        if cache_dir is None:
            cache_dir = self.cache_dir
        input_text = remove_bookmarks(text)
        input_data = {"input_text": input_text, "service": "deepgram", "model": self.model, "encoding": "mp3"}
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio_path = (self.get_audio_basename(input_data) + ".mp3") if path is None else path_to_string(path)
        url = "https://api.deepgram.com/v1/speak?model=%s&encoding=mp3&bit_rate=48000" % self.model
        req = urllib.request.Request(
            url, data=json.dumps({"text": input_text}).encode("utf-8"), method="POST",
            headers={"Authorization": "Token %s" % self.api_key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio = resp.read()
        with open(str(Path(cache_dir) / audio_path), "wb") as f:
            f.write(audio)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}
```
Good Deepgram voices: `aura-2-thalia-en` (clear female), `aura-2-andromeda-en`, `aura-2-apollo-en` (male).
**Hindi → use Sarvam, not Deepgram** (Deepgram has no Hindi). `scripts/sarvam_service.py` bundles a
ready `SarvamService` for manim-voiceover (Bulbul v3, native Hinglish code-switching — English math
terms like "sin theta" stay correctly English inside Hindi). Set `SARVAM_API_KEY`; `lang="hi-IN"`;
**speaker names are lowercase** v3 voices (male: `aditya`, `vijay`, `shubh`, `amit`, `varun`, `kabir`,
`soham`, `rahul`, `ashutosh`, `manan`, `anand`, `tarun`; female: `anushka`, `priya`, `ritu`, ...).
Run it standalone to A/B voices: `SARVAM_API_KEY=... python3 scripts/sarvam_service.py <voice>`.
~₹30/10K chars (≈ ₹0.7 / sample). ElevenLabs is the fallback if you want a specific cloned voice.

## Sync: per-sentence, not per-word
`VoiceoverScene` holds each `with self.voiceover(text=...)` block until that line's audio finishes —
so **one short sentence per beat** = drift-free sync with the visuals (no manual timing math). Word-exact
sync (`<bookmark>` + `wait_until_bookmark`) needs Whisper transcription of the audio — heavy and fragile;
prefer splitting into more, shorter beats instead.

## ⚠️ MOTION run_times MUST bind to `tracker.duration` — never hardcode them (hard-won)
The block holds until the audio finishes, but a `self.play(...)` with a **hardcoded `run_time`** runs at
the *start* of the block and then sits still for the rest of the clip. That's invisible in the language you
tuned it in — but the instant the clip length changes (a **Hindi cut is ~30% longer** than the English),
the motion finishes seconds before the words that describe it. Symptom the user reported: "the point moves,
then the voice catches up 2-3 seconds later," on exactly the moving shots (secant sliding, tangent dot
travelling). Fix = make the *motion* span its own clip, so it's always moving while narrated, in any language:
```python
with self.say("...slide Q slowly toward P...") as tracker:        # capture the tracker
    self.play(h.animate.set_value(1.0), run_time=tracker.duration * 0.45)
    self.play(h.animate.set_value(0.45), run_time=tracker.duration * 0.45)
with self.say("...until it kisses the curve...") as tracker:
    self.play(h.animate.set_value(0.06), run_time=max(2.0, tracker.duration - 1.0))
    self.play(Flash(P), run_time=1.0)                              # punctuation lands on the last beat
```
Rule of thumb: **continuous motion → `run_time=tracker.duration` (apportioned across the plays in the block).
One-shot accents (Write/Indicate/Flash/Circumscribe) can keep a fixed `run_time`** — they read fine finishing
early. Only the *travelling* things (ValueTracker slides, camera moves, a dot/line moving) must track duration.
Author in the source scene so it's correct for every language at once.

## Free static layout check — BEFORE the first TTS render
LLM-authored layouts fail in predictable ways (clipping, overlap); catch them for ₹0 by rendering the
tricky compositions as still frames with no voiceover. Make a throwaway `layout_test.py` with plain
`Scene` classes that `self.add(...)` each risky layout at its final state, then:
```bash
PATH="/Library/TeX/texbin:$PATH" .venv/bin/manim -ql -s --media_dir build layout_test.py A B C
```
`-s` renders just the last frame of each scene into `build/images/layout_test/*.png` — **Read them**.
On video #2 this caught a bottom-edge label clip and an ambiguous height label before a single TTS call.
Delete the file after the smoke render is verified.

## Manim CE gotchas (the ones that bite)
- **Stale animation cache: a layout fix that "didn't apply".** Manim's partial-movie-file cache can serve
  a false hit after you reposition a mobject — the re-render shows the OLD frame and you'll think the edit
  failed. If a verified code fix doesn't appear in the re-rendered frame, re-render with
  `--disable_caching` (the manim-voiceover TTS cache is separate — no re-synthesis cost) and re-check the
  exact frame. Cost video #2 a full extra render to diagnose.
- `always_redraw(...)` objects regenerate every frame → you **cannot** `self.play(obj.animate...)` them.
  Highlight = flash a static copy: `self.play(ShowPassingFlash(Line(p1,p2,color=C,stroke_width=11), time_width=0.7))`.
  Morph = make static copies, `ReplacementTransform(old, new)`, then `self.remove(...)` and `self.add(always_redraw(...))`
  at the same parameter value (seamless swap), then animate the tracker.
- Keep mobjects across a `wipe`: build the keep-set from `get_family()`:
  ```python
  def wipe(self, *keep):
      keepset = set()
      for k in keep: keepset.update(k.get_family())
      for m in self.mobjects:
          if m not in keepset: m.clear_updaters()
      gone = [m for m in self.mobjects if m not in keepset]
      if gone: self.play(*[FadeOut(m) for m in gone], run_time=0.6)
  ```
- Camera: `class Scene(VoiceoverScene, MovingCameraScene)`; `self.camera.frame.save_state()` at start;
  zoom `self.play(self.camera.frame.animate.scale(0.6).move_to(target))`; reset `self.play(Restore(self.camera.frame))`.
- Use `Arc(radius, start_angle, angle, arc_center=...)` for angles, not `Angle(...)` (which may draw the reflex).
- Background: `config.background_color = "#0e0e12"` (soft near-black; 3b1b feel, easier than pure #000).
- Colors already = 3b1b's palette in CE: `GREEN`(#83C167), `BLUE`(#58C4DD), `YELLOW`. Keep semantics
  consistent (e.g. green=opposite/height/sin, blue=adjacent/base/cos, yellow=hypotenuse/L).
- Equation column: center it (e.g. `move_to([2.5,1.6,0])`), don't `to_edge(RIGHT)` then drop a bigger
  `font_size` MathTex on top — it clips off the right edge.

## Circle-geometry recipes (proven in video #2 — reuse, don't re-derive)
- **True rim unroll** (circle rim → straight line, arc length constant): pin the arc's bottom to an
  anchor, shrink the angle while growing the radius so `R·θ = L` stays fixed:
  ```python
  L, th = TAU * R, ValueTracker(TAU)
  arc = always_redraw(lambda: Arc(radius=L/th.get_value(),
        start_angle=-PI/2 - th.get_value()/2, angle=th.get_value(),
        arc_center=anchor + UP * (L/th.get_value()), color=YELLOW))
  # play th -> ~0.025 bound to tracker.duration; then swap in a static Line of length L
  ```
- **Pizza-wedge interleave** (circle → near-rectangle): wedge `k` of `n` is a `Sector(radius=R,
  angle=TAU/n)`; even wedges apex-down on baseline `y` (`start_angle=PI/2 - PI/n`, apex at
  `x0 + (k//2)*w`), odd wedges apex-up on the top line (`start_angle=-PI/2 - PI/n`, arc_center at
  `[x0 + w/2 + (k//2)*w, y+R]`), where `w = 2R·sin(PI/n)` and `x0 = -(n-1)w/4` centers the row. Row
  width ≈ πR, height R. `Transform` each circle-sector to its row twin (tracker-bound); refine
  8→16→32 with `ReplacementTransform(group, group)`; finish into a `Rectangle(width=PI*R, height=R)`.
- **Onion-ring unroll** (circle → triangle): N stroke-only concentric circles → horizontal `Line`s of
  length `2π·r_i` stacked so ring `i` sits at height `(Rmax - r_i)` above the base — a centered
  staircase; overlay `Polygon` triangle (base `2πR`, height `R`). `ReplacementTransform` ring→strip
  with lag. Keep the stack height = R on screen so ½·base·height reads honestly.

## Background music
3b1b's music (Vincent Rubinetti) is free for educational videos. Direct WAV downloads:
`https://www.vincentrubinetti.com/audio/3blue1brown/` (e.g. "...06 Grant's Etude.wav"). Loop with the
`aloop` filter (NOT `-stream_loop` on WAV → PCM seam glitches), low volume, fades, then mix:
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VID"); FO=$(python3 -c "print(round($DUR-3,2))")
ffmpeg -nostdin -i music.wav -filter_complex \
 "[0:a]aloop=loop=-1:size=4200000,atrim=0:${DUR},volume=0.28,afade=t=in:st=0:d=2.5,afade=t=out:st=${FO}:d=3[m]" \
 -map "[m]" -c:a pcm_s16le bed.wav -y
ffmpeg -nostdin -i "$VID" -i bed.wav -filter_complex \
 "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k final.mp4 -y
```
**Volume must match the narration loudness — 0.10 is TOO QUIET and ships inaudible music.** The Hindi
aditya voice mixes at ~-21 dB mean; a 0.09-0.10 bed lands at ~-38 dB (17 dB down = the user literally
can't hear it: "where's the music?"). Aim for the **bed ~8-10 dB under the voice mean** → bed ≈ -29 to
-31 dB → **`volume` ≈ 0.25-0.28** for this voice. Set the bed volume relative to the actual voice level,
don't trust the 0.10 default.
**Verify with subtraction, NOT `volumedetect` of the final** — the voice dominates the mean, so a final
with music and one without look identical (both ≈ -21 dB). Subtract the no-music render from the final;
the leftover IS the bed, and it should read ≈ your target (~-29 dB) at several timestamps (confirms the
loop filled the whole video, not just the start):
```bash
ffmpeg -ss 300 -t 20 -i FINAL.mp4 -ss 300 -t 20 -i RAW_nomusic.mp4 -filter_complex \
 "[1:a]aeval='-val(0)|-val(1)':c=same[inv];[0:a][inv]amix=inputs=2:duration=shortest:normalize=0[d]" \
 -map "[d]" /tmp/d.wav -y && ffmpeg -i /tmp/d.wav -af volumedetect -f null - 2>&1 | grep mean_volume
```
Also: the 3b1b WAVs can carry a corrupt trailing packet ("Invalid PCM packet") — harmless (the bed still
builds full-length), but re-encode once (`ffmpeg -i etude.wav -c:a pcm_s16le clean.wav`) to silence the noise.

## Chapter markers (YouTube)
Generate from the auto `.srt`: find the first cue of each chapter's spoken lead-in, take its start time
(first chapter must be `0:00`). See `scripts/build_helpers.sh` for the parser.
