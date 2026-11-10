# open-katana

Katana-style kinetic motion graphics from a script, with no After Effects and no Higgsfield.

## What it does

`open-katana` turns a script into a narrated, word-synced motion graphic: extruded hero type, a comet that draws and types, blade slices that cut layouts in two, a 3D camera tunnel, glitch exits and diagrams that wire themselves. Everything is HTML + GSAP rendered by [HyperFrames](https://hyperframes.heygen.com), so the result stays editable.

The skill carries the pipeline (script → per-line voice → word timings → scene grid → scenes → sound → render → slow-motion review), a shared motion kit, a table of 15 reusable scene types, and the rules that cost time to learn. It was built by rebuilding one reference video shot for shot; that film ships as the worked example.

## Install

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install open-katana@ghost-skills
```

Or copy `skills/open-katana` into `~/.claude/skills/`.

## Requirements

- Node 22+ and `ffmpeg`; the HyperFrames CLI runs through `npx hyperframes` and its `/hyperframes` skill should be installed.
- `whisper-cli` (whisper.cpp) with a ggml model at `$WHISPER_MODEL`, for word timings.
- `OPENAI_API_KEY` for the bundled voice script, or bring your own per-line voice clips.

## Use

```text
/open-katana
Make a Katana-style motion graphic from this script
Animate this section of my explainer in the open-katana look
Recreate this motion-graphics video shot for shot
```

Give it a script with one sentence per line. It produces a HyperFrames project and an MP4.

## What's included

```text
open-katana/
├── .claude-plugin/plugin.json
├── README.md
└── skills/open-katana/
    ├── SKILL.md              # pipeline, look, kit API, scene types, rules
    ├── assets/               # kit.js + kit.css, the shared motion kit
    ├── scripts/              # setup.sh, vo.sh, layout.py, slow.sh, sfx_library.py
    ├── example/              # the full 19-scene film: index, scenes, timings, cue list
    └── reference/            # put your own reference clip here (not shipped)
```

The example's music is "Machine Paradigm" by DEgITx (CC BY 3.0); see `skills/open-katana/example/assets/CREDITS.md`.

## Author

**Aditya Pratap Singh** · [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](../../LICENSE)
