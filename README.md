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
  <img alt="skills" src="https://img.shields.io/badge/skills-2-8b5cf6">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-plugin-d97757">
  <img alt="platforms" src="https://img.shields.io/badge/platforms-web%20%C2%B7%20iOS%20%C2%B7%20Android%20%C2%B7%20desktop-2563eb">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-3fb950">
</p>

---

## What is this?

`ghost-skills` is a marketplace of installable [Claude](https://claude.com/claude-code) skills. Each skill is **self-contained**, **reference-backed**, and follows the [Agent Skills](https://agentskills.io) open standard — so it works in Claude Code (CLI, desktop, IDE) and any compatible tool.

Add the marketplace once and install any skill with a single command, or copy a skill folder straight into your project.

## 🧩 Skills

| Skill | What it does |
|-------|--------------|
| [**senior-ux-audit**](plugins/senior-ux-audit) | A principal-level UI/UX audit (web · iOS · Android · desktop) from your codebase — heuristics, accessibility, performance vitals, and a severity-rated, prioritized report with a 30/60/90 roadmap. |
| [**agentic-ai-backend-audit**](plugins/agentic-ai-backend-audit) | A senior adversarial audit of an AI-agent-built / agentic backend — 18 lenses across access control, prompt & agent safety, PII & data leakage, reliability, observability/evals/governance, and AI code smells. Severity-rated, `file:line`-cited, ends in a Ship/Fix/Block verdict. |

> _More skills are on the way. See [CONTRIBUTING.md](CONTRIBUTING.md) to add one._

## 📦 Install

Pick whichever fits your setup.

### 1. npx — installs to every AI agent on your machine

Works with [SkillFish](https://github.com/knoxgraeme/skillfish) or [Vercel `skills`](https://github.com/vercel-labs/skills). One command detects the agents on your system (Claude Code, Cursor, Copilot, …) and installs the skill into each:

```bash
npx skillfish add CreatorGhost/ghost-skills
# or
npx skills add CreatorGhost/ghost-skills
```

List what the repo offers, or target one skill directly:

```bash
npx skills add CreatorGhost/ghost-skills --list
npx skills add https://github.com/CreatorGhost/ghost-skills/tree/main/plugins/senior-ux-audit/skills/senior-ux-audit
```

### 2. Claude Code plugin marketplace

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install senior-ux-audit@ghost-skills
```

> Or from a local clone: `/plugin marketplace add /path/to/ghost-skills`.

### 3. Manual copy

```bash
cp -r plugins/senior-ux-audit/skills/senior-ux-audit ~/.claude/skills/   # all projects
cp -r plugins/senior-ux-audit/skills/senior-ux-audit .claude/skills/     # this project only
```

## 🚀 Invoke & use

**Invoke it** — directly, or in plain language (Claude auto-loads it from the description):

```text
/senior-ux-audit                          # explicit
Audit the UI/UX of this app               # natural language
Review my web app for accessibility (WCAG 2.2)
Why isn't this checkout flow converting?
Check the UX across all screens before launch
```

Claude reads your codebase, runs the app locally where it can, and returns a severity-rated report with a prioritized fix list.

### ✅ Best practices

- **Run from the project root** so the skill reads your real components, styles, and routes — it audits the codebase, not a guess.
- **Start your app first** (`npm run dev`, a simulator, etc.). A running app lets it verify contrast, focus order, responsive reflow, and loading/empty/error states that code alone can't show.
- **Name the platform and depth** — e.g. *"deep audit of the iOS app"* vs *"quick scan of the landing page."* Deep audit (default) covers everything; quick scan is faster and narrower.
- **Point it at the flows that matter** — *"focus on onboarding and checkout."* Findings are ranked by the business impact of the flow they sit in.
- **Give context for sharper findings** — who the users are (jobs-to-be-done) and what you're optimizing for (conversion, retention, accessibility).
- **Ask for the output you want** — a Markdown report (default) or the JSON variant for importing into a dashboard or tickets.
- **Run it before launch and after building several screens** to catch consistency drift across the app.
- **It's read-only** — it reports findings; ask it to *fix* them as a separate, explicit step.

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
