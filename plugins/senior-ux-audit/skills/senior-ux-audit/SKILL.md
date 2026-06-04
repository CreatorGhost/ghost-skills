---
name: senior-ux-audit
description: >-
  Senior UI/UX audit of a website, web app, or native iOS/Android/desktop app,
  run from the codebase and the app running locally.
  Heuristic evaluation (Nielsen's 10), accessibility (WCAG 2.2 for web,
  VoiceOver/TalkBack + HIG/Material for native), performance (Core Web Vitals for
  web, startup/jank/crash vitals for native), visual hierarchy, responsive/
  adaptive layout, navigation & IA, forms, and conversion friction — returned as
  severity-rated findings, a scorecard, and a prioritized 30/60/90 roadmap. Use
  when asked to audit/review UI or UX, run a design/usability/accessibility
  review, check a site or app for issues, evaluate visual design or
  responsiveness, find UX problems, or "review the UI", "audit the design",
  "review my app", "is this accessible", "why isn't this converting".
when_to_use: >-
  Any UI/UX audit, design review, usability review, accessibility review,
  heuristic evaluation, responsive/adaptive check, conversion/UX audit, or
  mobile-app review, on web or native.
metadata:
  author: Aditya Pratap Singh
  version: 1.0.0
---

# Senior UI/UX Audit (Web + App)

Audit a project's UI/UX from its **codebase** and the app run **locally**, then
return a severity-rated, prioritized report. Covers websites, web apps, and
native iOS / Android / desktop apps.

## When to use
- Review or audit a UI / UX, design, or visual style.
- Accessibility review, heuristic evaluation, usability review.
- Responsive / adaptive layout check across viewports and devices.
- Conversion / friction audit of a key flow.
- "Something feels off" about an interface; checking cohesion across screens.

## Inputs
1. **Codebase (primary).** Read pages/components/styles/routes (web) or
   screens/navigation (SwiftUI/UIKit, Compose/XML, Flutter, React Native).
   Map routes/screens and the design system before judging anything.
2. **App run locally (recommended).** Your dev server on `localhost` or your app
   in a simulator, to confirm what the code renders. Playwright MCP may drive
   your localhost (`browser_navigate`, `browser_snapshot`,
   `browser_take_screenshot`, `browser_resize`, `browser_press_key`,
   `browser_evaluate`).
3. **Screenshots / Figma (fallback).** Mark runtime checks (keyboard/gesture,
   performance, live contrast, screen reader) `needs-verification`.

## Pick a depth
- **Quick scan:** 1–3 key views, 1 mobile + 1 desktop viewport, ~5–10 findings.
- **Deep audit (default for "full site/app"):** all categories, full page/screen
  set + key flows, all viewports/devices, scorecard + roadmap.

State the depth and platform in one line before starting.

## Platform routing
Audit the shared categories everywhere; overlay the platform column.

| Platform | Accessibility | Performance | Conventions |
|----------|---------------|-------------|-------------|
| Web / web app | WCAG 2.2 AA | Core Web Vitals (LCP/INP/CLS) | Responsive, browser norms |
| iOS native | VoiceOver + WCAG baseline | Cold start, TTID/TTFD, 60fps, crash-free | Apple HIG |
| Android native | TalkBack + WCAG baseline | Startup, jank, ANR, crash-free | Material Design |
| Desktop / Electron | Platform a11y APIs | Launch + responsiveness | OS HIG |
| Cross-platform (RN/Flutter) | Both native trees | Both | Per-OS + token consistency |

## Viewports & devices
- **Web (W×H):** 375×812 · 428×926 · 768×1024 · 1024×768 · 1280×800 · 1440×900 ·
  1920×1080. Always test *through* breakpoints (768, 1024), not just at them.
- **Native:** small phone, large phone, tablet — each in portrait + landscape,
  light + dark, and largest Dynamic Type / font scale.

## Audit process
1. **Scope** — platform, goal, users (JTBD), macro bet, critical flows, page/
   screen set (include empty / error / loading / offline states).
2. **Capture** — read the code, render locally, screenshot each view × viewport/
   device, walk each critical flow. Name evidence `view__state`.
3. **Evaluate** — score each category below against Nielsen's 10 + the platform
   accessibility and performance checks.
4. **Rate** — assign 0–4 severity to every finding (and note strengths).
5. **Prioritize** — severity × business impact → P0–P3 and a 30/60/90 roadmap.
6. **Report** — assemble the deliverable (`references/report-template.md`).

## Align to the macro bet
Judge whether an unconventional pattern is a defect or an intentional bet.

| Bet | Wins by | Audit lens |
|-----|---------|-----------|
| Velocity | Shipping faster | Reuse patterns; flag reinvention |
| Efficiency | Less waste | Design-system consistency, fewer states |
| Accuracy | Being right | Stronger validation, feedback, instrumentation |
| Innovation | New value | Allow novel patterns if they still pass usability |

Write 1–3 **jobs-to-be-done** and judge every finding against them:
*"As a [user] in [situation], I want [motivation] so I can [outcome]."*

## Nielsen's 10 heuristics (cite on findings)
1. Visibility of system status. 2. Match to the real world. 3. User control &
freedom (exits, undo, predictable back). 4. Consistency & standards (platform
conventions). 5. Error prevention. 6. Recognition over recall. 7. Flexibility &
efficiency (accelerators). 8. Aesthetic & minimalist design. 9. Help users
recognize, diagnose & recover from errors. 10. Help & documentation.

---

## Evaluation categories — shared (web + app)
For each issue: name the category, location (view × viewport/device), heuristic
violated, evidence, severity, recommendation.

**1. Visual hierarchy.**
- *Issues:* no single focal point; primary action not dominant; weak heading/body
  distinction; competing elements; broken reading flow.
- *Terminology:* focal point, visual weight, reading flow (Z/F), scannability,
  information scent, dominance/subordination.

**2. Typography.**
- *Issues:* inconsistent type scale; weak weight contrast; line length too long/
  short; tight leading; body text too small (<16px web / <17pt iOS); orphans.
- *Terminology:* typographic scale, measure, leading, tracking, Dynamic Type.

**3. Spacing & layout.**
- *Issues:* inconsistent spacing (no 8-pt grid); broken vertical rhythm; uneven
  gutters; overcrowding or dead zones; misalignment.
- *Terminology:* 8-pt grid, vertical rhythm, gutter, breathing room, density.

**4. Grid & alignment.**
- *Issues:* elements off-grid; inconsistent column spans; poor edge/optical
  alignment; uneven container widths; misaligned labels/inputs.
- *Terminology:* grid system, column structure, edge/optical alignment, baseline.

**5. Color & contrast.**
- *Issues:* incoherent palette; accent overuse; inconsistent semantic color;
  color as sole meaning; low contrast (see Accessibility).
- *Terminology:* color weight, semantic color, 60-30-10, contrast ratio.

**6. Navigation & wayfinding.**
- *Issues:* no current-location indicator; >7±2 top-level items; inconsistent
  placement; vague/technical labels; hidden search; unpredictable behavior.
- *Terminology:* information scent, wayfinding, active state, progressive disclosure.

**7. Affordance & interaction.**
- *Issues:* buttons don't look pressable; links look like text; unclear input
  boundaries; weak primary/secondary distinction; small hit areas.
- *Terminology:* affordance, signifier, perceived affordance, hit/tap target.

**8. Feedback states.**
- *Issues:* missing hover (web), focus, active/pressed, disabled, loading,
  selected states; no feedback on action.
- *Terminology:* state coverage, focus ring, pressed state, micro-feedback.

**9. Dialogs & modals.**
- *Issues:* mispositioned; missing backdrop; no focus trap; background scroll not
  locked; no close/escape/back; jarring transitions.
- *Terminology:* focus trap, scroll lock, overlay, dismiss affordance.

**10. Consistency (cross-screen).**
- *Issues:* same component styled differently; multiple spacing scales; varied
  typography per role; hard-coded values instead of tokens.
- *Terminology:* design-system adherence, visual language unity, token coverage.

**11. Empty & error states.**
- *Issues:* blank empty screens; no next-action guidance; generic errors; no
  recovery path; no first-run guidance.
- *Terminology:* zero-data state, blank slate, graceful degradation, error recovery.

**12. Loading experiences.**
- *Issues:* no loading indication; content jumps on load; spinner where a skeleton
  fits; no progress for long ops; poor perceived performance.
- *Terminology:* skeleton, perceived performance, optimistic UI, layout shift.

**13. Information architecture.**
- *Issues:* poor grouping; unclear labels; high cognitive load; illogical order;
  missing section headers.
- *Terminology:* chunking, cognitive load, mental model, taxonomy.

**14. Microinteractions & motion.**
- *Issues:* missing transition feedback; inconsistent timing/easing; jarring state
  changes; excessive/distracting motion; ignores reduced-motion.
- *Terminology:* easing curve, duration, choreography, motion hierarchy.

**15. Large-viewport / adaptive layout.**
- *Issues:* content stretches to unreadable widths; no max-width; oversized dead
  zones; hierarchy collapses at scale; stretched phone layout on tablet.
- *Terminology:* max-width constraint, content container, adaptive vs responsive.

## Evaluation categories — app-specific
**16. Onboarding & permissions.**
- *Issues:* long first-run (>5 screens); value unclear; not skippable; all
  permissions requested at launch with no reason; ungraceful denial.
- *Terminology:* progressive onboarding, just-in-time permission, value moment,
  D1/D7/D30 retention.

**17. Gestures & touch targets.**
- *Issues:* targets <44pt (iOS) / <48dp (Android); <8dp spacing; gesture conflicts
  with system; critical actions hidden behind gesture-only.
- *Terminology:* tap target, gesture conflict, discoverability, fat-finger error.

**18. Thumb zone & one-handed use.**
- *Issues:* primary actions out of thumb reach; destructive actions in easy reach;
  no bottom-anchored primary nav.
- *Terminology:* thumb zone, reachability, ergonomics, bottom navigation.

**19. Platform-convention conformance.**
- *Issues:* custom chrome replacing native nav; back behavior breaks OS norm; iOS
  patterns pasted on Android (or vice versa).
- *Terminology:* platform fidelity, native pattern, HIG/Material conformance.

**20. Forms & input on small screens.**
- *Issues:* multi-column; wrong keyboard type; no autofill/autocomplete;
  validation that wipes entered data; vanishing labels; wrong pickers.
- *Terminology:* keyboard type (inputmode), autofill, inline validation, data
  preservation.

**21. Offline & connectivity.**
- *Issues:* no offline indication; ungraceful connection loss; no caching; actions
  lost instead of queued.
- *Terminology:* offline-first, optimistic queueing, sync state.

---

## Accessibility
A11y findings are usually severity 3–4 (they exclude users). Automated tools catch
~20–40%; always add the manual passes. Cite the exact criterion or rule.

### Web — WCAG 2.2 AA (high-yield)
- **Contrast:** text ≥ 4.5:1, large text ≥ 3:1 (1.4.3); non-text/UI ≥ 3:1 (1.4.11).
- **Keyboard:** all operable, no traps (2.1.1/2.1.2); logical focus order (2.4.3);
  visible focus (2.4.7); focus not obscured (2.4.11, new in 2.2).
- **Targets:** ≥ 24×24 CSS px (2.5.8, new); drag has a pointer alternative (2.5.7).
- **Structure:** semantic headings/landmarks/labels (1.3.1); name/role/value on
  custom controls (4.1.2); status messages announced (4.1.3).
- **Content:** meaningful `alt` (1.1.1); color not sole meaning (1.4.1); reflow at
  320px / 200% zoom (1.4.10); skip link (2.4.1).
- **Forms:** error identification + suggestion (3.3.1/3.3.3); no redundant entry
  (3.3.7, new); accessible auth, allow paste (3.3.8, new).
- *Manual passes:* keyboard traversal, screen-reader spot-check, zoom/reflow,
  contrast probe, reduced-motion.

### Native — iOS & Android
- **Names/roles/states** on every control (icon-only buttons too): iOS
  `accessibilityLabel` + traits; Android `contentDescription` + role/state.
- **Reading/focus order** logical for VoiceOver / TalkBack.
- **Text scaling:** Dynamic Type (iOS) / `sp` + font scale (Android); no clipping
  at the largest size.
- **Targets:** ≥ 44×44 pt (iOS) / ≥ 48×48 dp (Android), ≥ 8dp apart.
- **Contrast** as WCAG above; **color not sole meaning**; **Reduce Motion**
  respected; **gestures have alternatives**.
- *Manual passes:* VoiceOver/TalkBack walk of each screen + flow; largest-text
  check; platform scanner (Accessibility Inspector / Accessibility Scanner) then
  verify flags; dark-mode check.

## Performance (perceived UX)
### Web — Core Web Vitals (good thresholds, p75)
- **LCP** ≤ 2.5s (loading) · **INP** ≤ 200ms (responsiveness) · **CLS** ≤ 0.1
  (visual stability). Flag layout shift, slow first content, sluggish interactions.

### Native — app vitals
- **Startup:** cold ideally < 500ms, treat ≥ 5s as bad; warm ≥ 2s, hot ≥ 1.5s as
  bad. Track **TTID** (first frame) and **TTFD** (interactive).
- **Smoothness:** 60fps (16.7ms/frame); flag **jank** (missed frame deadlines),
  especially on scroll.
- **Stability:** crash-free users > 99%, crash-free sessions > 99.95%; ANR rate
  low (Android bad-behavior ≈ 0.47% overall).
- **Both:** prefer skeletons over spinners; avoid layout shift when data arrives.

## Severity scale (every finding)
| Sev | Label | Meaning |
|-----|-------|---------|
| 4 | Critical | Blocks a task, loses data, or excludes users. Fix before release. |
| 3 | Major | Serious friction/confusion; hurts conversion or trust. High priority. |
| 2 | Minor | Real issue with a workaround. Low priority. |
| 1 | Cosmetic | Polish; fix if time allows. |
| 0 | Strength | What works well — record these too. |

Optionally weight by **frequency × persistence** (how often hit, how stuck it
leaves the user) to surface the riskiest issues.

## Prioritization → roadmap
- Rank by **severity × business impact** (impact of the flow it sits in), then by
  effort. Plot impact × effort; the high-impact/low-effort quadrant is your quick
  wins.
- Tier: **P0** (critical, or major in a revenue-critical flow) → fix now ·
  **P1** (major in high-traffic) → this sprint · **P2** (minor) → backlog ·
  **P3** (cosmetic/edge) → monitor.
- Sequence into **30 / 60 / 90 days**: quick wins → structural fixes (design-system,
  IA, navigation) → foundational (accessibility, performance, measurement).

## Recommendation format
Write fixes as actions tied to a problem and an expected impact.
- **Good:** "Replace the email-field error with one that states the required
  format; validate inline so data isn't lost." / "Constrain article body to
  ~70ch max-width on ≥1440px."
- **Avoid:** "Improve error messages." / "Fix the spacing." / "Add `padding:16px`."
  (No raw CSS, no vague verbs.)

## Output
Default to a Markdown report using **`references/report-template.md`**: executive
summary → scope/method → scorecard → findings (grouped by category, each with
location, severity, principle, evidence, recommendation) → per-view notes (deep
audits) → prioritized 30/60/90 roadmap. Offer the JSON variant in that file when
machine-readable output is wanted.

## Notes
- Cite the basis of each finding (heuristic number, WCAG criterion, vital
  threshold), and match the requested depth.
- If a check can't be verified at runtime (screen reader, real-user performance),
  mark it `needs-verification`.
- Simulate error / empty / slow / offline states non-destructively (route
  interception or mocks) rather than triggering them for real.
