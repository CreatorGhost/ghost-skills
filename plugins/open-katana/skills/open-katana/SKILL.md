---
name: open-katana
description: Katana-style kinetic motion graphics without Higgsfield — a prompt or script becomes a narrated, word-synced motion piece (extruded hero type, a comet that draws and types, blade slices that cut layouts apart, 3D camera tunnel, glitch exits, diagrams that wire themselves) built in HyperFrames (HTML + GSAP) and rendered to MP4. Use when the user says "open katana", "katana style", "like the Higgsfield Katana video", wants motion graphics "without After Effects", a kinetic-type promo, or animated segments for a YouTube explainer in this look. Also use to recreate a reference motion-graphics video shot for shot.
---

# Open Katana

A script goes in; a narrated, word-synced motion graphic comes out. Everything is HTML + GSAP rendered by HyperFrames, so it is editable afterwards. Sits on top of two other skills: `/hyperframes` (read it first for the composition contract) and `/real-sfx` for sound effects. Run `scripts/setup.sh` once: it checks the tools, downloads `/real-sfx` if it is missing, and with `--library` builds a CC0 starter sound library, because real-sfx ships none.

`example/` is a complete 54 s film made this way (19 scenes); read the scene closest to what you need before writing a new one. `assets/kit.js` + `assets/kit.css` are the shared motion kit — copy them into the project, do not rewrite them. If `reference/` holds a clip (the look was reverse-engineered from a phone recording of a laptop, screen at `crop=300:230:5:270`; third-party, so it is not shipped), look at how it does a move with `scripts/slow.sh` before guessing.

## Pipeline

1. **Script** — one sentence per line in `script.txt`. Short lines; hero beats ("Hell yes!") get their own line.
2. **Voice** — the voice is the clock. `sh scripts/vo.sh script.txt vo/clips` (OpenAI TTS, needs `OPENAI_API_KEY`; if the key is only exported in interactive shells, run it as `zsh -ic "sh …"`), or bring any per-line clips named `s01.wav…` from another voice.
3. **Timing** — `python3 scripts/layout.py script.txt vo/clips film/assets --gaps '{"1":0.5}'` writes `vo.wav` + `timing.js` (`window.VO`, word times). Needs `ffmpeg` and `whisper-cli` (whisper.cpp) with a ggml model at `$WHISPER_MODEL`. Read the printed word list: whisper may merge or split words ("15-second"), and cues index whisper's words.
4. **Grid** — choose each scene's start from the sentence starts (a scene usually starts ~0.05–0.1 s before its sentence). Write them in `assets/grid.js` (`window.GRID`) **and** as each host's `data-start` in `index.html`. Slots are 1–3.5 s; a typed prompt can run 9 s.
5. **Storyboard** — one row per sentence: what is on screen, which archetype (below), how it enters, how it leaves. Every exit is caused by something on screen and feeds the next entrance (whip left → whip in from the right; pull back → reveal; zoom through a hole → dark).
6. **Build** — `npx hyperframes init film --skip-skills --skill=hyperframes --non-interactive`, copy the kit and `example/index.html` (background, HUD, hosts, audio), then one file per scene in `compositions/`. Cues come from the voice: `const c = K.cue("s04"); const CUT = c(3, 10) + 0.04` = sentence 3, word 10, in that scene's own time.
7. **Look** — `npx hyperframes check --json`, then `npx hyperframes snapshot --at …` for every scene. A passing check does not show how it looks.
8. **Render and watch it slowly** — `npx hyperframes render . -q high -o renders/x.mp4` with the voice as the only audio, then `scripts/slow.sh renders/x.mp4 6.9 /tmp/a.jpg 20 5x5` on every slice, transition and hero beat. Fix what snaps before any sound goes on.
9. **Sound effects (the part that matters most)** — done by the `/real-sfx` skill with real recordings, from the film's own cue list:
   - Copy `example/cues.py`, edit `EVENTS` (typed: `whoosh`, `wipe`, `hit`, `thump`, `pop`, `tick`, `click`, `key`, `glitch`, `riser`, `magic`; times from the same word timings as the scenes; the time is the frame where something *starts*), run it → `docs/cues.json`.
   - `python3 <real-sfx>/scripts/from_cues.py docs/cues.json --video renders/x.mp4 --out work/cues.json --ui library`, read the `NOT mapped` line (a kind with no sound in the library stays silent), then `mix.py work/cues.json --out result/x_sfx.mp4 --voice-safe` and `critique.py`. Fix the three problems it names (usually: a hit at full level on top of a word → lower its `g` to ~0.5; heavy low end), run again, and pass on its "listen to these five moments" list.
   - No `/real-sfx`, or no library: `python3 cues.py --stem` builds a fallback stem from the sounds in `assets/sfx/`.
10. **Music — last, optional, and the person's choice.** Never pick the track yourself. Ask for theirs; if they have none, offer three candidates with a link each to listen (Openverse, `license=cc0,by`, with measured tempo and loudness) and wait for the pick. Then cut an excerpt starting on a beat, `data-volume="0.16"` under the voice, and write the attribution line into `assets/CREDITS.md`. No answer → deliver without music and say so.


Recreating a reference video: run `scripts/slow.sh` on the *reference* first, at 30 fps, around every transition. Contact sheets at 2 fps hide what a move actually does (a "slice" may be a zoom through a letter).

## The look

- Every colour is a root variable (`--ground`, `--ink`, `--lime`, `--pink`, plus `--lime-rgb` / `--pink-rgb` for the glows): a channel with its own palette overrides those and keeps the motion.
- Ground `#070c1a` with a radial lift, dot grid + stars drifting for the whole film, HUD texture (frame counter, dotted ring, corner labels).
- Hero type: Archivo Black, uppercase, extruded with a stepped `text-shadow` (`.hero.ink` pale blue, `.hero.lime`, `.hero.pink`). Two words per beat, one ink + one lime; pink only for "no / error / cost".
- Labels: JetBrains Mono 700, tracked, tiny (`.mono`). Panels: 3 px outlined rounded boxes (`.panel`, `.panel.lm`).
- Caption track top-left: words appear as spoken, the current word wears a lime chip (`example/compositions/cap.html`). No caption over hero-word scenes.
- Every scene sits in `.stage > .drift > .world`: `.drift` turns a few degrees for the whole scene (`K.drift`), `.world` takes the entrance and exit.

## Kit (`window.K`)

| Call | Does |
| --- | --- |
| `K.cue(scene)(s, w)` | time of word `w` of sentence `s`, local to the scene |
| `K.slam / through / whip / drift / draw` | hero arrival from the lens; camera pushes through; smear out sideways; slow scene turn; draw a line |
| `K.fly(tl, comet, a, b, t, d, o)` | comet flight a→b; tail stretches with speed (`hide:false` to keep it, `linger`) |
| `K.slash(tl, el, x, y, deg, t, {rev, hold, fade})` | blade of light: travels across, holds, thins away |
| `K.dup(sel)` + `K.cut(tl, sel, twin, t, {x, y, deg, d, hang, spin, part})` | slice a `.layer` in two along the blade; halves ease apart, drift, then tumble away in depth. `part:true` opens them like shutters onto the next scene |
| `K.bands(sel, n)` + `K.glitch(tl, sel, strips, t, d)` | glitch exit: horizontal bands tear sideways on a stepped clock |
| `K.burst(tl, el, t, {n, r, seed, from, arc})` | petal sparks with drag and gravity |
| `K.hit(tl, stage, t, amp)` | impact kick on the whole shot |
| `K.typer(tl, keys, lines, caret, cw, lh)` | monospace typing synced to word times; `.chip` highlights keep the glyph grid |
| `K.track(tl, keys, fn)` | piecewise driver: `fn(v)` as a pure function of the playhead (counters, physics, paths) |
| `K.split(el)` | wrap letters in spans |

## Scene archetypes (file in `example/compositions/`)

| Beat | Scene | Move |
| --- | --- | --- |
| Two-word hero | s01, s05, s14, s19 | slam + rise with sparks; exit by pushing through or pulling back |
| Word you zoom through | s02 | comet hits the "O", camera goes through its counter |
| Axes + words growing from a baseline | s03 | comet rules the lines, words rise from masks |
| App window that gets sliced | s04 | whip in, bars grow, blade, halves tumble |
| Chain of boxes that gets refused | s06 | comet wires boxes per word, links snap, ✕, stamp, glitch out |
| Brand reveal | s07 | blade crosses, wordmark is what it leaves |
| Prompt box written by the comet | s08, s10 | two strokes become the box; typing follows the voice; keyword props (ruler, letterbox, Aa, morphing shape, 3D cube); Enter floods the frame |
| Engine → checklist tree | s09 | node pops, comet runs the bus, items wire in and tick one by one |
| Full-colour type scene | s11 | lime ground, dark type, letters stretch on transforms |
| 3D tunnel | s12 | one camera `z` flown through frames at depth, settling on each word |
| The transition | s13 | cut + shutters open onto the next scene |
| Stack + counter, then sliced | s15 | rows drop per word, hours count up, blade clears it |
| Pipeline pills + count-up | s16 | pills shoot out of each other |
| Replay window | s17 | the film so far scrubbed inside a player |
| Arc from A to B | s18 | comet draws a Bezier whose head is the line's end; lands and fills the frame |

## Rules that cost time to learn

- **Nothing snaps.** A slice needs ≥0.9 s after the cut: blade holds ~0.3 s, halves drift before gravity. Give the scene's host extra `data-duration` and `z-index: 3` so the pieces fall over the start of the next scene.
- **Cloned layers need class CSS.** `K.dup`/`K.bands` strip ids, so everything inside a cut or glitched `.layer` is styled by class, and the CSS describes the *settled* state (the clone is taken before any tween). Call them first in the script.
- **Half-planes sliding along the blade reveal nothing.** Shutters open perpendicular to it.
- **`fromTo` holds its from-state from t=0**; add `immediateRender: false` only to a later tween on the same property of the same element.
- **Never put `filter` in a `back`/`elastic` tween** (negative blur); blur gets its own `power2.out` tween.
- **`filter` flattens `preserve-3d`.** Blur a 3D scene from a wrapper outside `.stage` (s12).
- **No `letterSpacing`, `width`, `left` tweens** (lint error, and they stutter): stretch type with per-letter `x`/`scaleX`.
- **Zooming through a glyph** needs its centre from the font's metrics (fontTools on the cached woff2), not DOM measurement; scale ≥60 so the counter clears the frame, and no `filter` on something scaled that far.
- **Dynamic text in a cut layer**: stack one span per value and toggle opacity, so the clone shows the last value.
- **Typed lines**: reveal with a stepped `clip-path` (monospace advance × chars); a hidden line is `inset(0 100% 0 0)` or its first chip's glow leaks.
- Scene timelines never read a clock; anything physical (sparks, falls, shake, glitch) is a pure function of time through `K.track`.
- zsh does not word-split `for x in "a b"`: use `bash -c` for loops over pairs.

## Done means

`check` ok, every scene snapshotted and looked at, the render slow-motion-reviewed at each transition, the real-sfx critique run with its scores reported as they are, loudness measured (−16 to −14 LUFS, peak ≤ −1 dBTP), and a delivery note that says what was measured rather than heard, names the moments to check by ear, and lists the credits the publisher must carry. Music is in only if the person chose it.
