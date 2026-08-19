# unslop

Cut the obvious AI tells from prose without sanding away the writer's voice.

## What it does

`unslop` edits writing for plain language, concrete claims, natural rhythm, and a voice that fits the context. It catches puffery, filler, vague attribution, canned transitions, forced lists, jargon, passive constructions, and formatting habits that make text feel machine-made.

The skill does more than delete bad phrases. It preserves meaning, varies sentence rhythm, and keeps opinions or personality when they belong in the piece.

## Install

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install unslop@ghost-skills
```

Or copy `skills/unslop` into `~/.claude/skills/`.

## Use

```text
/unslop
Make this sound like a person wrote it
Remove the AI tone from this draft
Edit this for plain, natural language
```

Paste the text or point the skill at a file. It keeps the original meaning unless you ask for a substantive rewrite.

## What's included

```text
unslop/
├── .claude-plugin/plugin.json
├── README.md
└── skills/unslop/
    └── SKILL.md
```

## Author

**Aditya Pratap Singh** · [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](../../LICENSE)
