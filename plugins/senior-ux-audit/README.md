<h1 align="center">🔍 senior-ux-audit</h1>

<p align="center">
  <strong>A principal-level UI/UX audit — for web <em>and</em> native apps.</strong><br>
  Runs from your codebase, returns severity-rated findings, a scorecard, and a 30/60/90 roadmap.
</p>

<p align="center">
  <a href="../../README.md">ghost-skills</a> •
  <a href="#install">Install</a> •
  <a href="skills/senior-ux-audit/SKILL.md">SKILL.md</a> •
  <a href="skills/senior-ux-audit/references/report-template.md">Report template</a>
</p>

<p align="center">
  <img alt="platforms" src="https://img.shields.io/badge/web%20%C2%B7%20iOS%20%C2%B7%20Android%20%C2%B7%20desktop-supported-2563eb">
  <img alt="standards" src="https://img.shields.io/badge/WCAG-2.2%20AA-3fb950">
  <img alt="heuristics" src="https://img.shields.io/badge/Nielsen-10%20heuristics-8b5cf6">
</p>

---

## What is this?

A skill that gives Claude the ability to run a structured, senior-grade UI/UX audit of a project from its **codebase** (and the app running **locally**). It produces an evidence-based report — not scattered opinions — that a team can act on this quarter.

## What it checks

- **Heuristics** — Nielsen's 10 usability heuristics.
- **Visual & layout** — hierarchy, typography, spacing/grid, color, consistency, empty/error/loading states, responsive & adaptive layout, motion.
- **Accessibility** — WCAG 2.2 AA (web) · VoiceOver/TalkBack, Dynamic Type, touch targets (native).
- **Performance** — Core Web Vitals: LCP/INP/CLS (web) · startup, jank, crash-free/ANR (native).
- **App-specific** — onboarding & permissions, gestures, thumb-zone, platform conventions (HIG / Material), mobile forms, offline.
- **Output** — severity 0–4 scoring, a scorecard, P0–P3 prioritization, and a 30/60/90 roadmap (Markdown or JSON).

## Install

Via the marketplace (see the [repo README](../../README.md)):

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install senior-ux-audit@ghost-skills
```

…or copy `skills/senior-ux-audit` into `~/.claude/skills/`.

## Usage

```text
/senior-ux-audit
```

…or just ask:

```text
Audit the UI/UX of this app
Review my web app for accessibility
Why isn't this flow converting?
```

## How it works

```text
1. Scope      — platform, users (JTBD), macro bet, flows, screen set
2. Capture    — read the code, run locally, screenshot each view × viewport
3. Evaluate   — heuristics + 21 dimensions + a11y + performance
4. Rate       — severity 0–4 on every finding (and strengths)
5. Prioritize — severity × business impact → P0–P3
6. Report     — exec summary → scorecard → findings → 30/60/90 roadmap
```

## What's included

```text
senior-ux-audit/
├── .claude-plugin/plugin.json
├── README.md
└── skills/senior-ux-audit/
    ├── SKILL.md                      # the skill
    └── references/
        └── report-template.md        # report skeleton + JSON schema
```

## Author

**Aditya Pratap Singh** — [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](../../LICENSE)
