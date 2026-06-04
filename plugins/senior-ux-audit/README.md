# senior-ux-audit

Senior UI/UX audit of **your own project** — website, web app, or native
iOS/Android/desktop app — run from the **codebase** (and the app run locally).
Returns severity-rated findings, a scorecard, and a prioritized 30/60/90 roadmap.

## What it checks
- **Heuristics:** Nielsen's 10 usability heuristics.
- **Visual & layout:** hierarchy, typography, spacing/grid, color, consistency,
  empty/error/loading states, responsive/adaptive layout, motion.
- **Accessibility:** WCAG 2.2 AA (web) · VoiceOver/TalkBack + Dynamic Type +
  touch targets (native).
- **Performance (perceived):** Core Web Vitals (web) · startup/TTID-TTFD, jank,
  crash-free/ANR (native).
- **App-specific:** onboarding & permissions, gestures, thumb-zone, platform
  conventions (HIG/Material), mobile forms, offline.
- **Output:** severity 0–4, scorecard, P0–P3 prioritization, 30/60/90 roadmap.

## Use
Install via the marketplace (see the repo [README](../../README.md)) or copy
`skills/senior-ux-audit` into `~/.claude/skills/`. Then:

```
/senior-ux-audit
```

…or just ask: *"audit the UI/UX of this app"*, *"review my web app for
accessibility"*, *"why isn't this flow converting"*.

## Files
- `skills/senior-ux-audit/SKILL.md` — the skill.
- `skills/senior-ux-audit/references/report-template.md` — report skeleton + JSON.
