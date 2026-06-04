# 👻 ghost-skills

A collection of installable [Claude](https://claude.com/claude-code) skills.
Each skill is self-contained, reference-backed, and works in Claude Code (CLI,
desktop, IDE) — install the whole marketplace or copy a single skill into your
project.

## Skills

| Skill | What it does |
|-------|--------------|
| [`senior-ux-audit`](plugins/senior-ux-audit) | Senior UI/UX audit of your own website or app (web · iOS · Android · desktop) from the codebase — heuristics, WCAG 2.2 / native a11y, performance vitals, severity-rated findings, and a prioritized 30/60/90 roadmap. |

_More skills coming — see [CONTRIBUTING.md](CONTRIBUTING.md) to add one._

## Install

### Option A — Plugin marketplace (recommended)
In Claude Code:

```
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install senior-ux-audit@ghost-skills
```

> Replace `CreatorGhost/ghost-skills` with the GitHub `owner/repo` you push
> this to. You can also add it from a local path:
> `/plugin marketplace add /absolute/path/to/ghost-skills`.

### Option B — Copy a single skill (no plugin system)
Copy the skill folder into your personal or project skills directory:

```bash
# personal (all projects)
cp -r plugins/senior-ux-audit/skills/senior-ux-audit ~/.claude/skills/

# or project-local
cp -r plugins/senior-ux-audit/skills/senior-ux-audit .claude/skills/
```

Then invoke it with `/senior-ux-audit`, or just ask Claude to "audit the UI/UX".

## Repository layout

```
ghost-skills/
├── .claude-plugin/marketplace.json     # marketplace registry
└── plugins/
    └── senior-ux-audit/                # one plugin per skill
        ├── .claude-plugin/plugin.json
        ├── README.md
        └── skills/senior-ux-audit/
            ├── SKILL.md                # the skill
            └── references/             # appendices loaded on demand
```

## License
[MIT](LICENSE).
