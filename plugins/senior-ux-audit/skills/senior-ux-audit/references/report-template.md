# Report Template

Use this for the audit deliverable. Markdown by default; JSON when machine-readable
output is requested.

## Markdown skeleton

```markdown
# UI/UX Audit — <Project> (<Web | iOS | Android | Desktop>)
Date · Depth (quick scan | deep audit) · Scope audited · Tools used

## Executive summary
- Overall grade: <A–F or 0–100>
- Top 3 risks (severity 3–4): …
- Top 3 quick wins (high impact / low effort): …
- Verdict: <one line — what's hurting the product and what to fix first>

## Scope & method
- Platform · JTBD (1–3) · Macro bet · Flows & views audited · Viewports/devices
- Not verified / out of scope (e.g. screen-reader pass, real-user performance)

## Scorecard
| Category | Grade | Notes |
|----------|-------|-------|
| Visual hierarchy | … | … |
| Typography | … | … |
| Spacing & layout | … | … |
| Color & contrast | … | … |
| Navigation & IA | … | … |
| Affordance & feedback | … | … |
| Consistency | … | … |
| Empty/error/loading states | … | … |
| Accessibility | … | … |
| Performance | … | … |
| (App) onboarding/gestures/platform | … | … |
| Composite | … | … |

## Findings
Grouped by category, ordered by severity. Each finding:
- **<Title>** — Sev <0–4> · <view × viewport/device>
  - Principle: <Nielsen #N / WCAG x.x.x / vital>
  - Evidence: <screenshot ref / code ref / measured value>
  - Recommendation: <action + expected impact + named pattern>

## Per-view notes (deep audit)
One short block per key view × viewport with its specific issues.

## Prioritized roadmap
| # | Finding | Sev | Impact | Effort | Tier | Window |
|---|---------|-----|--------|--------|------|--------|
| 1 | … | 4 | High | Low | P0 | 30d |

- **30 days** — quick wins (consistency, validation, states).
- **60 days** — structural (design system, IA, navigation).
- **90 days** — foundational (accessibility, performance, measurement).
```

## JSON variant

```json
{
  "title": "UI/UX Audit — <Project>",
  "platform": "web | ios | android | desktop | cross-platform",
  "date": "YYYY-MM-DD",
  "depth": "quick-scan | deep-audit",
  "grade": "A-F or 0-100",
  "jtbd": [
    { "user": "", "situation": "", "motivation": "", "outcome": "" }
  ],
  "macro_bet": "velocity | efficiency | accuracy | innovation",
  "scorecard": [
    { "category": "Visual hierarchy", "grade": "", "notes": "" }
  ],
  "findings": [
    {
      "id": "F1",
      "title": "",
      "category": "",
      "severity": 0,
      "location": "view × viewport/device",
      "principle": "Nielsen #N | WCAG x.x.x | LCP/INP/CLS | app-vital",
      "evidence": "",
      "recommendation": "",
      "status": "confirmed | needs-verification"
    }
  ],
  "roadmap": [
    { "finding_id": "F1", "impact": "high|med|low", "effort": "high|med|low", "tier": "P0|P1|P2|P3", "window": "30d|60d|90d" }
  ],
  "not_verified": []
}
```
