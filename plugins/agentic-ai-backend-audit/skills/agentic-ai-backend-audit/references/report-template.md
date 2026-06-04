# Report Template

The deliverable. Lead with the verdict, group findings by severity, and make every
finding a one-liner an engineer can act on. Markdown by default; JSON when machine-readable.

## Markdown skeleton

```markdown
# Backend Audit — <feature / branch>
Scope: <files / diff range> · Shape: <CRUD | LLM/agent | RAG | multi-tenant | handles PII/PHI>
Lenses run: <list, or "all 18"> · Lenses N/A: <list with one-line reason>

## Verdict
**Block.** — 2 blockers (F1, F3). / **Fix then ship.** — 4 high/medium. / **Ship it.** — nits only.

## Blockers (severity 4)
- **<lens>: <one-line issue>** — `file:line`
  ⚠ This may cause <impact>.  **Fix:** <one line>.

## High (severity 3)
- **<lens>: <one-line issue>** — `file:line` · ⚠ <impact> · **Fix:** <one line>.

## Medium (severity 2)
- ...

## Nits (severity 1)
- ...

## Strengths / cleared (severity 0)
- <control done right, or false positive checked and cleared, with the reason>.

## Out of scope (pre-existing — flag, don't fix in this PR)
- `file:line` — <issue> (predates the diff).

## Not verified
- <checks that need a runtime/manual pass: screen-reader-equivalent, real-user perf, etc.>
```

## Per-finding rules
- **Name the lens** (e.g. "Cross-tenant RAG leakage", "Excessive agency").
- **Cite `file:line`** verbatim — a finding without a location is an opinion; drop or downgrade it.
- **One impact warning** ("⚠ this may cause …") — the consequence, not a restatement of the issue.
- **One-line fix** as an action, not a vague verb. ("Add `filter={'tenant_id': session.tenant_id}`",
  not "improve the query".)
- **Severity 0–4** per the rubric in `SKILL.md`. Optionally annotate `(freq×persistence: high)`.
- Mark anything you couldn't verify at runtime `needs-verification`.

## JSON variant

```json
{
  "title": "Backend Audit — <feature/branch>",
  "scope": "<files / diff range>",
  "shape": ["llm-agent", "rag", "multi-tenant", "pii"],
  "lenses_run": ["1","2","3","..."],
  "lenses_na": [{"lens": "6", "reason": "no LLM output path"}],
  "verdict": "block | fix-then-ship | ship",
  "findings": [
    {
      "id": "F1",
      "lens": "9.6 cross-tenant isolation",
      "title": "Order lookup missing tenant scope (BOLA)",
      "severity": 4,
      "location": "repositories/order_repo.py:42",
      "impact": "Any authenticated tenant can read another tenant's orders by changing the id (reportable breach).",
      "fix": "Add AND org_id = :ctx.org_id using org_id from the auth context.",
      "status": "confirmed",
      "freq_persistence": "high"
    }
  ],
  "out_of_scope": [
    {"location": "auth/jwt.py:9", "issue": "missing aud check (pre-existing)"}
  ],
  "not_verified": ["screen-reader pass", "real-user p75 latency"]
}
```
