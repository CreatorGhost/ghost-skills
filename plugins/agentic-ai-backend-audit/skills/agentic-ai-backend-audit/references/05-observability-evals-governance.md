# 05 — Observability, Evals & Governance

Lenses 15–17. Agentic systems are non-deterministic and multi-step: the same input
takes different paths. Without per-step traces you can't debug; without evals you can't
tell a smart agent from a regressed one; without an immutable audit trail and enforced
oversight you fail an auditor or a regulator. **Note: redaction of secrets/PII in traces
and logs is also a leakage finding — cross-ref `03 §9.3`.**

---

## Lens 15 — Observability & tracing (OpenTelemetry GenAI)

**Catches**
- **Untraced runs:** tool calls, retrieval, and sub-agent hops inside one opaque span
  (or none) — a multi-step failure can't be localized.
- **Token/cost only at the aggregate level**, never per LLM call — a cost spike can't be
  attributed to a prompt/tool/model.
- **Raw prompts/tool-args/docs/completions written verbatim to spans/logs** with no
  redaction (a GDPR liability and a credential leak — cross-ref 03 §9.3).
- **No prompt/tool/model versioning** on spans — a quality regression can't be tied to a
  build.
- **Errors collapsed to a generic 500** with no `span.set_status(ERROR)`/
  `record_exception`/`error.type`/failure-category — failure dashboards are blind.
- **Broken trace-context propagation** across async/await, background tasks, queues, and
  HTTP to tool services — the run fragments into disconnected traces.
- **Streaming spans ended at first-token** — output token count and `finish_reason`
  missing.
- **Sampling drops the spans you most need** (errors sampled out), or content capture left
  globally on in prod (PII firehose).

**How to scan** — a tracer exists in the loop/dispatch/retrieval: `rg -n 'start_as_current_span|@observe|langfuse|opentelemetry|@traceable|openllmetry|logfire'`. OTel GenAI
conventions, not bespoke names: `rg -n 'gen_ai\.(operation|request.model|usage.input_tokens|usage.output_tokens|tool.name|conversation.id|response.finish_reasons)'`. Per-span token/cost:
each LLM call reads `response.usage`/`usage_metadata` and writes it on the span. Unredacted
content reaching traces (cross-ref 03 §9.3): `set_attribute(...messages|prompt`, and the
content-capture switch (`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, `capture_content`, Langfuse `mask=`). Versioning: a `prompt_version`/hash attribute and a pinned
`gen_ai.request.model`. Error handling on each LLM/tool span (`set_status(ERROR)` +
`record_exception` + `error.type`). Context propagation across `create_task`/`gather`/
`BackgroundTasks`/Celery/outbound HTTP. Streaming spans ended in a `finally` after the stream
drains. Retrieval/RAG steps as their own spans. A stable `gen_ai.conversation.id` on every
span.

**Impact warnings** — *⚠ An untraced run may cause incidents that can't be localized or
reproduced. Raw secrets/PII in spans/logs may cause a compliance breach and a credential
leak to the trace backend. No per-span cost may cause an un-attributable spend spike.*

**Example findings**
- `agents/chat/agent.py:88` — the whole loop runs inside one `start_as_current_span('chat')`;
  the per-tool dispatch and retrieval emit no child spans. Fix: wrap each tool in an
  `execute_tool {gen_ai.tool.name}` span and each retrieval in its own span.
- `agents/chat/llm.py:54` — `resp = client.messages.create(...)` never reads `resp.usage`,
  so no span carries token counts. Fix: set `gen_ai.usage.input_tokens`/`output_tokens` (+
  `cache_read`) from `resp.usage`.

**Severity** — **4:** raw secrets/PII written to spans/logs with no redaction (also a 03 §9.3
leak), or content capture forced on in prod with no masking. **3:** untraceable run (no
per-step spans, no per-call cost attribution, errors that never set span status, broken
context propagation). **2:** bespoke (non-OTel-GenAI) attributes, unversioned prompt/model,
streaming spans ending early, head-based sampling that can drop failed runs. **1:** missing
`conversation.id`, span-naming convention.

**False positives** — a thin internal tool/script with no agent loop (full GenAI tracing is
overkill); content capture ON in a dev/test config block; vendor auto-instrumentation
(Langfuse `@observe`, OpenLLMetry) that already emits GenAI spans without explicit
`set_attribute` (verify the library is wired); bespoke names mapped to OTel by a processor;
documented head-sampling paired with always-on error sampling; debug-level content logging
off in prod.

---

## Lens 16 — Evals, regression & non-determinism

**Catches**
- **No eval suite at all:** agent/prompt/tool code shipped with only unit tests that **mock
  the LLM** — every assertion is on the mock, not the model.
- **Final-output-only evals:** checks the last message but never the **trajectory** (which
  tools, with what args, in what order) — 20–40% of agent failures live there.
- **Non-determinism faked away:** tests pin `temperature=0`/a seed and treat the agent as
  deterministic (it isn't across providers/versions); or a flaky LLM test is **retried until
  green**, hiding brittleness.
- **LLM-as-judge with no guardrails:** never calibrated against human labels, no rubric, the
  judge is the same model that generated the output (self-preference), or fixed-order A/B
  (position bias), or rewards verbosity.
- **Pass/fail on a single run** instead of N runs with a pass-rate threshold.
- **No version-controlled golden dataset** (evals live only in a SaaS dashboard) — no
  diffable regression baseline.
- **Missing adversarial/red-team suite** (prompt-injection, jailbreak, tool-abuse,
  PII-exfil) for an agent that calls tools on untrusted input.
- **CI gate that doesn't gate:** `continue-on-error`, no threshold, runs only on a schedule
  (never on the PR that changed the prompt), or writes a report nobody reads.
- **No production-trace-to-eval loop:** real failures never sampled back into the golden set.

**How to scan** — eval surface: `rg -l 'promptfooconfig|deepeval|ragas|langsmith|braintrust|GEval|assert_test'` + an `evals/`/`tests/evals/` dir. **If the diff changes a prompt/agent/tool
but touches no eval file, that's the headline finding.** LLM exercised not mocked: `rg -n
'mock.*(openai|anthropic|llm)|MagicMock|nock|msw' tests/ evals/`. Determinism: `temperature=0`
commented "deterministic" / exact-string `==` on raw output; look for repeated-run averaging /
pass-rate threshold instead. Trajectory: `rg -n 'tool_calls|assert.*called_with|trajectory|
intermediate_steps|expectedToolCalls'` — output-only on a tool-calling agent is a blind spot.
Judge: a written rubric, a **different** judge model, randomized pairwise order, and a
calibration artifact (judge-vs-human agreement). Golden set in-repo (`*.jsonl`/`cases/`).
Adversarial: `rg -ni 'inject|jailbreak|red.?team|exfiltrat|prompt.?leak'`. CI gate: open
`.github/workflows/*.yml` — no `continue-on-error`, runs `on: pull_request` for prompt/agent
paths, enforces a threshold. Production-to-eval loop. Model + cost pinned (no floating
`gpt-4o`/`claude-latest`). Flaky-test laundering (`@retry|rerun|pytest-rerunfailures` near LLM
tests).

**Impact warnings** — *⚠ Zero eval coverage on a changed prompt may cause silent quality
regressions to ship. A CI "gate" that can't fail may cause regressions to merge through a
green pipeline. A missing adversarial suite on a tool-calling agent may cause a security
regression (a new injection path) to go uncaught.*

**Example findings**
- `agents/support/router.py:88` + `tests/test_router.py:20` — the triage agent calls
  `escalate_to_human`/`refund` but the only test asserts `'sorry' in resp.text`; a wrong-tool/
  wrong-amount refund passes. Fix: assert the expected `tool_calls` (name + args) on the
  trajectory.
- `.github/workflows/evals.yml:19` — eval step has `continue-on-error: true` and runs only
  `on: schedule`, so a PR rewriting the system prompt merges without evals. Fix: trigger on
  `pull_request` for prompt/agent paths, drop `continue-on-error`, add a `--fail-on` pass-rate
  threshold over N runs.

**Severity** — **4:** a prompt/agent/tool change with ZERO eval coverage of model behavior;
a CI gate that cannot fail; an entirely absent adversarial suite for an agent calling tools on
untrusted input. **3:** final-output-only on a tool-calling agent; LLM-as-judge with no rubric/
calibration/anti-bias; single-run pass/fail; no production→eval loop. **2:** golden set only in
SaaS; floating eval model; no online/drift eval; flaky-test laundering; no eval cost budget.
**1:** eval naming/organization, slightly loose thresholds.

**False positives** — pure-deterministic backend with no LLM/agent code; unit tests mocking the
LLM to test surrounding plumbing (only flag mocking in the **eval** itself); `temperature=0` in
a structural smoke test (JSON/schema validity); a small repo's single committed JSONL; exact-
match on extractive/classification tasks; nightly eval **as a supplement** to a PR-time gate; an
absent online eval at most sev 2 for internal/low-traffic tools.

---

## Lens 17 — Compliance & governance (EU AI Act, SOC2, audit trails, oversight)

**Catches**
- **Agent decisions/tool actions not logged**, or only to ephemeral stdout — no durable,
  queryable who/what/why/when (EU AI Act Art.12 record-keeping, SOC2 CC7 fail).
- **Mutable audit logs:** a regular table with UPDATE/DELETE grants, no hash chain, no WORM —
  the agent's own service account can rewrite history.
- **No correlation/trace id** propagated across LLM→tool→downstream — a single decision can't
  be reconstructed.
- **Decorative human-in-the-loop:** high-impact actions (payments, deletes, emails, prod
  writes) execute without a **blocking** approval; `requireApproval` defaults false / is
  bypassable (Art.14 oversight).
- **No kill switch:** no flag/breaker/toggle to halt the agent — "human-in-command" is
  impossible without a deploy.
- **Raw PII in immutable logs** → an unsatisfiable GDPR Art.17 erasure obligation.
- **Wrong retention:** logs purged before the AI-Act 6-month minimum, or PII kept past the
  GDPR limit with no documented TTL.
- **No per-decision provenance:** logs don't capture model id/version, system-prompt version,
  policy version, tool-schema version — a past decision can't be tied to its config.
- **Unpinned data residency:** LLM/vector-DB/storage default to US/"global" with no SCC/DPF
  basis for EU personal data.
- **Self-logging gap:** the audit-write path swallows failures (best-effort `try/except pass`)
  — actions succeed while their audit record silently fails.

**How to scan** — durable + append-only audit sink: `rg -i 'audit.?log|action_log|decision_log'`
going to a WORM/hash-chained/immutable store, not just `logger.info`. Tamper-evidence:
`rg -i 'prev_?hash|hash_chain|merkle|hmac|object_lock|WORM'`. Mutability: `rg -i 'GRANT (UPDATE|DELETE).*audit'` and bucket policies — writers should be INSERT-only. Correlation id propagated
to every LLM/tool/downstream call. Approval gates that **block**: `rg -i 'require.?approval|HITL|
needs_review|pending_approval'` — each high-impact tool gated behind a **persisted server-side**
approval, not a client flag / `approved=True` default. Kill switch (`kill.?switch|circuit.?breaker|FEATURE_.*AGENT|emergency.?stop`). PII redaction in the log path. Retention config `>= 6
months` for AI-Act logs, bounded for PII. Per-decision provenance (`model_version`, `prompt_version`, `policy_version`). Residency (`region|AZURE_OPENAI_ENDPOINT|VERTEX_LOCATION`). Governance
docs (`MODEL_CARD`, `DPIA`, risk-tier). Audit-write swallowed failures.

**Impact warnings** — *⚠ High-impact actions with no enforced oversight or kill switch may
cause irreversible autonomous actions a human couldn't stop (Art.14). A mutable/absent audit
trail may cause an un-reconstructable incident and a failed audit. Raw PII in immutable logs may
cause an unsatisfiable erasure obligation. An audit write that fails silently may cause a
real-world action with no record.*

**Example findings**
- `services/agent/tools.py:142` — `execute_refund()` runs the Stripe call with `auto_approve=True` default — every agent refund bypasses oversight (Art.14). Fix: route high-impact tools
  through a server-side approval queue that blocks until a human record persists.
- `db/migrations/0007_audit.sql:12` — `audit_events` is a plain table and `app_role` holds
  UPDATE+DELETE; no `prev_hash`. Fix: make it INSERT-only (revoke UPDATE/DELETE) and add a
  hash-chain (`entry_hash = sha256(payload || prev_hash)`).
- `telemetry/trace.py:54` — the audit insert is wrapped in `try/except: pass`, so the tool
  action commits with no record. Fix: fail closed — block or durably queue the record.

**Severity** — **4:** high-impact autonomous actions with no enforced oversight gate or no kill
switch; an audit trail that doesn't exist or is fully mutable by the agent's own service
account; actions that succeed while their audit record silently fails. **3:** audit log not
tamper-evident or lacking per-decision provenance; raw PII in immutable logs (unsatisfiable
erasure); retention below the 6-month minimum or unbounded PII; unpinned residency for EU
personal data. **2:** missing/incomplete model card/risk-tier; correlation id not propagated to
all calls; retention configured but undocumented. *Rises one level when the system is plausibly
EU-AI-Act high-risk (Annex III) or processes special-category data.*

**False positives** — `console.log`/`print` for dev where a durable sink also exists; normal
mutable application/operational logs (only the **decision/action** trail needs immutability);
read-only/low-impact tools (search/get/list) that don't need approval; a managed logging service
with object-lock/immutable retention (don't insist on hand-rolled Merkle trees); pseudonymized
PII referenced by request id; a purely non-high-risk internal tool with no personal data and no
EU nexus; provider default region already in-EEA or non-personal data.
