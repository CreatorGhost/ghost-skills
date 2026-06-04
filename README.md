<h1 align="center">👻 ghost-skills</h1>

<p align="center">
  <strong>Installable Claude skills that punch above their weight.</strong><br>
  Senior-grade, reference-backed skills you can drop into any project — install the whole marketplace or copy one skill.
</p>

<p align="center">
  <a href="#-install">Install</a> •
  <a href="#-skills">Skills</a> •
  <a href="#-whats-inside">What's inside</a> •
  <a href="CONTRIBUTING.md">Contributing</a> •
  <a href="LICENSE">License</a>
</p>

<p align="center">
  <img alt="skills" src="https://img.shields.io/badge/skills-1-8b5cf6">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-plugin-d97757">
  <img alt="platforms" src="https://img.shields.io/badge/platforms-web%20%C2%B7%20iOS%20%C2%B7%20Android%20%C2%B7%20desktop-2563eb">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-3fb950">
</p>

---

## What is this?

`ghost-skills` is a marketplace of installable [Claude](https://claude.com/claude-code) skills. Each skill is **self-contained**, **reference-backed**, and follows the [Agent Skills](https://agentskills.io) open standard — so it works in Claude Code (CLI, desktop, IDE) and any compatible tool.

Add the marketplace once and install any skill with a single command, or copy a skill folder straight into your project.

## 🧩 Skills

| Skill | What it does | Platforms |
|-------|--------------|-----------|
| [**senior-ux-audit**](plugins/senior-ux-audit) | A principal-level UI/UX audit run from your codebase — heuristics, accessibility, performance vitals, and a severity-rated, prioritized report with a 30/60/90 roadmap. | Web · iOS · Android · Desktop |

> _More skills are on the way. See [CONTRIBUTING.md](CONTRIBUTING.md) to add one._

## 📦 Install

### Plugin marketplace (recommended)

In Claude Code:

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install senior-ux-audit@ghost-skills
```

> You can also add it from a local clone: `/plugin marketplace add /path/to/ghost-skills`.

### Single skill (no plugin system)

```bash
# personal — available in every project
cp -r plugins/senior-ux-audit/skills/senior-ux-audit ~/.claude/skills/

# or project-local
cp -r plugins/senior-ux-audit/skills/senior-ux-audit .claude/skills/
```

Then invoke with `/senior-ux-audit`, or just ask Claude to "audit the UI/UX."

## 🚀 Usage

Once installed, talk to Claude naturally:

```text
Audit the UI/UX of this app
Review my web app for accessibility (WCAG 2.2)
Why isn't this checkout flow converting?
Check the UX across all screens before launch
```

Claude reads your codebase, runs the app locally where it can, and returns a severity-rated report with a prioritized fix list.

## 📂 What's inside

```text
ghost-skills/
├── .claude-plugin/
│   └── marketplace.json              # marketplace registry
├── plugins/
│   └── senior-ux-audit/              # one plugin per skill
│       ├── .claude-plugin/plugin.json
│       ├── README.md
│       └── skills/senior-ux-audit/
│           ├── SKILL.md              # the skill
│           └── references/
│               └── report-template.md
├── CONTRIBUTING.md
└── LICENSE
```

## 🤝 Contributing

Each skill is one folder under `plugins/` plus one entry in `marketplace.json`. The full recipe is in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Author

**Aditya Pratap Singh** — [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](LICENSE)
