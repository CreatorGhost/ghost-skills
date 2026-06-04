---
name: agentic-ai-backend-audit
description: >-
  Senior adversarial audit of an AI-agent-built and/or agentic/LLM backend, run
  AFTER an agent finishes a feature — when lint, types, and tests pass but the
  code hasn't been reviewed by a senior engineer. 18 lenses across security &
  access control, prompt & agent safety, data protection & leakage (PII/PHI,
  RAG/embedding/log/cross-tenant leakage), reliability, observability/evals/
  governance, and AI-authorship hygiene. Every finding names the issue, cites
  file:line, warns "this may cause <impact>", and rates severity 0–4, ending in
  a Ship / Fix-then-ship / Block verdict. Use after building a backend feature
  with AI, before opening a PR, or when the user says "audit the change", "any
  bugs in this", "review my diff", "is this safe to push", "check for security
  issues", "is this leaking data", or "what did I miss".
when_to_use: >-
  After an AI agent (or human) finishes a backend feature and lint/type-check/
  tests pass — pre-push and pre-PR adversarial review. Especially for backends
  that build or run LLM/agent/RAG/tool-calling systems, handle PII/PHI, are
  multi-tenant, or expose APIs. Trigger on "audit", "review my diff", "is this
  safe to push", "security review", "is this leaking data", "what did I miss".
metadata:
  author: Aditya Pratap Singh
  version: 2.0.0
---

# Agentic-AI Backend Audit

A principal engineer's adversarial review of a backend change, run **after** an
AI agent has finished. Lint, types, and unit tests already passed — this skill
catches the failure classes those tools don't see, with a bias toward the bugs
AI-built and agentic backends ship most: missing authorization, data leakage,
prompt-injection escape, excessive agency, silent failures, and runaway cost.

> **Audit perspective.** You are flagging issues, not building features. For every
> finding: **name** it, cite **file:line**, **warn** what it may cause ("⚠ this
> may cause cross-tenant PII disclosure"), give a one-line **fix**, and assign a
> **severity 0–4**. End with a verdict. Read-only — propose fixes only as an
> explicit next step.

## When to use
Run after **every** AI-agent-built backend change, before pushing or opening a PR.
Trigger phrases: *"audit the change"*, *"any bugs in this"*, *"review my diff"*,
*"is this safe to push"*, *"is this leaking data"*, *"security review"*, *"what
did I miss"*.

## Inputs
1. **The diff (primary).** `git diff --cached` if anything is staged, else
   `git diff main..HEAD` plus untracked files. Scope the audit to the change.
2. **The surrounding files.** Read every changed file in full and 1–2 callers of
   any new function — diffs hide the context the lenses need.
3. **Tests as intent, not proof.** Read them to learn what the code *means* to do;
   assume the tests can be wrong (AI often writes the test to match the bug).

## How to run
1. **Scope.** `git diff --name-only` (staged, else `main..HEAD`). State the scope
   and the platform shape in one line (plain CRUD? LLM/agent? RAG? multi-tenant?
   handles PII/PHI?) — this decides which lenses are load-bearing.
2. **Read every changed file in full**, plus key callers.
3. **Run the lenses.** Work category by category (below). One lens at a time
   produces sharper findings than a single combined sweep. Skip a lens only when
   it provably can't apply (e.g. no LLM/agent code → the agent-safety lenses are
   N/A; say so).
4. **Rate every finding** 0–4 and attach the impact warning.
5. **Triage pre-existing.** A real bug you find while reading code the diff
   *touched* but didn't *introduce* goes under "Out of scope" — flag, don't make
   the author own it.
6. **Report** using `references/report-template.md`; end with the verdict.

### Optional: run lenses in parallel via subagents
If the host supports subagents (Claude Code's `Agent` tool, a multi-agent
harness), spawn one subagent per category (or per lens) with the same scope brief
plus the relevant reference file, then synthesise. Independent passes beat one
agent that anchors on its first finding.

## The 18 lenses
Each lens lives in a category reference with its concrete **detection checks
(grep patterns + code smells)**, **impact warnings**, **example findings**,
**severity guidance**, and **false-positives to suppress**. Load the reference
for the category you're scanning.

**A. Security & access control** — `references/01-security-access.md`
1. **Access control & authorization** — BOLA/IDOR, broken function-level authz,
   auth missing on new routes, agent acting-as / delegation, JWT verification,
   multi-tenant isolation, RLS.
2. **Injection & API security** — OWASP API Top 10: SQL/NoSQL/command/path
   injection, SSRF (incl. agent fetch tools), mass assignment, unsafe
   deserialization, CORS, rate limiting, excessive data exposure.
3. **Secrets & supply chain** — hardcoded/logged secrets, unpinned deps &
   lockfiles, lifecycle scripts, slopsquatted packages, MCP-server trust & token
   passthrough.

**B. Prompt & agent safety** *(agentic/LLM systems)* — `references/02-prompt-agent-safety.md`
4. **Prompt injection & system-prompt leakage** — direct + indirect (RAG/tool
   output), escaping & instruction hierarchy, Jinja SSTI, output-side prompt/
   secret leakage.
5. **Excessive agency & tool safety** — permissions-in-code-not-prompt, tool
   allowlist, least-privilege creds, read/write split, HITL on irreversible
   actions, loop/budget caps, kill switch, tool-arg validation.
6. **Content filtering & output safety** — input + output moderation, jailbreak
   detection, fail-closed guardrails, streaming enforcement, insecure output
   handling (markdown/HTML exfil).
7. **Memory & RAG integrity** — memory poisoning, write provenance/TTL,
   retrieval grounding/citation, data/instruction boundary on retrieved chunks.

**C. Data protection & leakage** *(your widest risk surface)* — `references/03-data-protection-leakage.md`
8. **PII/PHI handling** — detect/minimize/redact **before** the LLM, logs,
   traces, and embeddings; retention/TTL; right-to-erasure fan-out;
   BAA/data-residency; fail-closed detectors.
9. **Data-leakage vectors** — the nine channels: RAG/retrieval, embeddings/
   vector-store, logs/traces/observability, errors/stack-traces/debug, LLM
   output, cross-tenant isolation, cache/session, prompt/context history, and
   third-party/tool egress.

**D. Reliability & correctness** — `references/04-reliability-correctness.md`
10. **Agent runtime resilience** — bounded + classified retries, idempotent
    writes + saga rollback, timeouts/deadlines, loop/step caps, circuit
    breakers, pool exhaustion.
11. **Resource-exhaustion ordering** — caps placed *after* the expensive op,
    unbounded recursion/payloads, missing `max_length`.
12. **Silent failures** — swallowed exceptions, fallback-as-success,
    `{success:false}`+HTTP 200, empty-as-happy-path, streaming/async
    invisibility, uninstrumented caches.
13. **Schema / contract / state drift** — type/DB/wire mismatch, naive vs aware
    datetimes, transactions & partial-failure rollback, single-writer races,
    missing migrations, worker-global state, SDK version drift.
14. **Cost & token controls** — per-request/session budgets, unbounded loops,
    context growth, prompt-cache hygiene, semantic-cache correctness, model
    routing.

**E. Observability, evals & governance** — `references/05-observability-evals-governance.md`
15. **Observability & tracing** — per-step spans (OTel GenAI), per-call token/
    cost attribution, redaction before export, error/failure taxonomy, context
    propagation.
16. **Evals & non-determinism** — golden + adversarial + regression suites,
    trajectory (not output-only) checks, sound LLM-as-judge, N-run pass-rate, a
    CI gate that actually blocks, production→eval loop.
17. **Compliance & governance** — immutable/tamper-evident audit trail of agent
    actions, enforced human-oversight gates, kill switch, retention, data
    residency, model card (EU AI Act / SOC2 / ISO 42001).

**F. AI-authorship hygiene** — `references/06-ai-code-smells.md`
18. **AI code smells & artefact leakage** — hallucinated packages/APIs,
    happy-path bias, check-then-act races, N+1/serial-await, missing-await, fake
    placeholder secrets, and `CLAUDE.md`/plan-file/co-author/contributor-name
    leakage.

## Severity scale (every finding)
| Sev | Label | Meaning | Examples |
|-----|-------|---------|----------|
| **4** | Blocker | Production-breaking, security hole, data loss/leak | BOLA returns another tenant's row; secret reaches the LLM/logs; RAG query with no tenant filter; non-idempotent charge under retry; prompt-injection → tool execution |
| **3** | High | Real bug, likely to bite next sprint | silent failure in the streaming path; missing rate limit on login/LLM route; redaction mis-ordered; schema drift breaking a client; no eval coverage on a changed prompt |
| **2** | Medium | Worth fixing before merge, not urgent | broad `except` could be narrower; coarse moderation thresholds; DB enum for churning values; missing kill switch (redeploy to stop) |
| **1** | Nit | Style/convention, no behaviour impact | naming, robotic prose, magic-number retry count |
| **0** | Cleared / strength | False positive caught in review, or a control done right | "checked X — fine because Y"; "tenant filter correctly derived from JWT" |

Optionally weight by **frequency × persistence** (how often a path is hit, how
stuck it leaves the user) to rank the riskiest issues first. Record strengths and
cleared false positives too — a balanced audit is credible.

## Output & verdict
Use `references/report-template.md`: findings grouped by severity, each with the
lens, `file:line`, the impact warning, and a one-line fix; an "Out of scope
(pre-existing)" section; and a one-line verdict:
- **Ship it.** — no findings, or only sev-1 nits.
- **Fix then ship.** — sev 2–3 findings; list them.
- **Block.** — any sev-4; list each with its one-line fix.

The verdict is what the reader sees first; everything above is the receipts.

## False-positive discipline
Each lens reference lists its common false positives — apply them. The biggest
recurring traps: authorization enforced in a layer the static scan didn't trace
(middleware/decorator/RLS/base query); single-tenant deployments where
cross-tenant findings don't apply; redaction/guardrails enforced at a gateway/
proxy rather than in app code; and placeholder secrets in test fixtures. Confirm
the control is **truly absent across all files** before reporting a sev-4.

## What this skill does NOT cover
- **Algorithmic correctness / business logic** — use a TDD/property-testing skill.
- **Deep performance profiling** — use a profiling skill (this flags obvious
  N+1/serial-await, not micro-optimization).
- **Frontend, a11y, visual design** — use `senior-ux-audit`.
- **Infra/IaC & cloud posture** beyond what the diff touches — flag, hand off.
