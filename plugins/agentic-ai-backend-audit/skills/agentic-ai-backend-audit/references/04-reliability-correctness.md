# 04 — Reliability & Correctness

Lenses 10–14. AI agents optimize for the happy path: they wire the call, not the
failure. These lenses catch the bugs that pass lint + tests but corrupt data,
double-charge, run cold, or bill five figures in production. *Escalate one level
whenever the affected path handles money, auth, permissions, or writes/deletes.*

---

## Lens 10 — Agent runtime resilience

**Catches**
- **Non-idempotent writes under retry:** `POST /charge`, `create_order`, `INSERT`, or
  an MCP write in a retry loop with no `Idempotency-Key`, or a key minted **inside** the
  retry body (`uuid4()` per attempt) — double charges / duplicate rows.
- **Blind retries:** one `for attempt in range(n)` / `@retry` that retries 4xx/auth/
  schema errors that can never succeed, instead of classifying transient (408/429/5xx/
  timeout → backoff) vs permanent (4xx/auth/schema → re-plan/escalate).
- **Missing/unbounded timeouts:** `httpx`/`requests`/LLM-SDK/DB/tool calls with no
  `timeout=`, so one hung upstream pins a worker; or inner timeout ≥ outer so the deadline
  never trips.
- **Uncapped agent loops:** `while True` / `while not done` ReAct loop with no
  `max_iterations`/`max_steps` — re-plans until the request times out.
- **No token/cost budget** per turn/session — a stuck loop racks up spend silently.
- **Retry storm:** constant or pure-exponential backoff with no jitter/cap, retries
  layered at multiple levels, hammering a recovering endpoint.
- **No circuit breaker** on a known-down model/tool/DB — every request waits the full
  timeout.
- **Pool/semaphore exhaustion:** per-request `httpx.Client`/`create_engine` instead of a
  shared pool; `asyncio.gather`/`Promise.all` over an unbounded list with no concurrency
  limit.
- **Multi-step writes with no saga/compensation:** `create_order` then `charge_card`
  with no rollback path → orphaned state; or non-idempotent compensations.
- **Fallback that swallows or shares the failure domain:** returns empty/None as
  success, or the fallback model sits behind the same provider.

**How to scan**
- Boundaries: `rg -n 'httpx|aiohttp|requests\.|openai|anthropic|await client|session.execute|cursor.execute|call_tool'` — each needs a `timeout=`/`request_timeout`/`statement_timeout`.
- Retry sites: `rg -n '@retry|tenacity|for attempt in range|while True|backoff|max_retries'` — verify max attempts, error **classification**, jitter, and a cap. A retry wrapping a write or retrying 4xx/auth = blocker.
- Idempotency: for retriable writes (`\.post(`, `INSERT`, `charge`, `transfer`, `send_`), look for `Idempotency-Key`/unique-constraint upsert; the key must be **stable across retries** (derived from `turn_id`/`request_id`), not `uuid4()` minted in the retry body.
- Agent loop: `rg -n 'while True|max_iterations|max_steps|recursion_limit'` — a hard step cap AND a defined terminal action. (LangGraph default `recursion_limit=25` — don't rely on it blindly.)
- Budget: `rg -n 'max_tokens|token_budget|usage.total_tokens|budget'` — cumulative accounting across the loop with a stop, not just `max_tokens` per call.
- Backoff math: `2 ** attempt` with no `random()`/jitter or no `min(..., cap)` = storm risk; constant `sleep(1)` synchronizes the fleet.
- Circuit breaker: `rg -n 'circuit|breaker|pybreaker|failure_threshold|opossum'` on critical external deps.
- Pooling: per-request client/engine creation inside handlers; fan-out without `Semaphore`/`p-limit`.
- Compensation: any 2+ writes in one logical op need a rollback path; compensations must be idempotent.

**Impact warnings**
- Non-idempotent write under retry → *⚠ may cause duplicate charges/orders on a
  timed-out-but-succeeded attempt.*
- Uncapped loop / no budget → *⚠ may cause a runaway five-figure bill (the $47K/11-day
  pattern).*
- No timeout at a hot path → *⚠ may cause one hung upstream to pin all workers (outage).*
- Multi-step write with no compensation → *⚠ may cause orphaned/partial state and a
  paid-but-unfulfilled order.*

**Example findings**
- `payments/checkout.py:88` — `for _ in range(3): httpx.post('/charge', json=body)` with
  no idempotency key. Fix: stable `Idempotency-Key` from `turn_id`+`tool_name`; retry
  only transient statuses.
- `agents/runtime.py:142` — `while True:` ReAct loop with no step cap; ~8k tokens/turn
  on repeated tool errors. Fix: cap `max_steps` and return a partial result + error.
- `clients/search.py:17` — `httpx.AsyncClient()` constructed per request exhausts the
  pool under load. Fix: one app-scoped client injected.

**Severity** — **4:** non-idempotent write reachable under retry with no stable key;
uncapped loop / missing budget that can run to timeout; a hot-path call with no timeout
that can pin all workers. **3:** unclassified retries (storm + waste); no jitter/cap on a
shared dep; missing breaker on a known-flaky critical dep; unbounded fan-out; multi-step
writes with no compensation. **2:** timeouts present but not layered into a deadline; weak
fallback signal; untuned breaker; non-idempotent compensation. **1:** magic-number retry
counts, missing `Retry-After`.

**False positives** — idempotency not required on GET/HEAD/idempotent PUT/DELETE-by-id;
`while True` event/queue/accept loops that *should* run forever; `max_tokens` per call
(only flag missing **cumulative** budget); outermost broad `except` that logs+alerts+
degrades; per-request clients in scripts/serverless cold-start; no breaker on low-volume
non-critical paths.

---

## Lens 11 — Resource-exhaustion ordering

**Catches** — size caps / rate limits placed **after** the expensive operation they
guard (the cap fires too late; CPU/memory already spent); unbounded recursion on
user-controlled payloads; missing `max_length`/`max_items` on Pydantic fields that hit
the LLM context window or a vector store; per-request work that should be cached/pooled;
per-request token refresh; `while True` retries with no backoff.

**How to scan** — find every size check (`if size > MAX`, `enforce_size_limit`,
`HTTPException(413)`, `Field(max_length=)`), then walk **backwards**: what runs before
it (recursion, allocation, a full dict walk, a JSON parse of an unbounded string)? If
user-controlled input drives an expensive op **before** any cap fires, flag. Check
Pydantic fields hitting the LLM/vector store for `max_length`/`max_items`. Per-request
`creds.refresh()`/`get_token()` in the handler instead of a cached background-refreshing
wrapper.

**Impact warnings** — *⚠ A cap after the expensive op may cause a cheap-to-ship,
expensive-to-process payload to exhaust CPU/memory before the guard fires (cost-DoS).*

**Example** — `agents/chat/page_context.py:142` — `redact_secrets(ctx)` walks the full
nested dict before `enforce_size_limit` runs; a deeply nested payload bypasses the cap.
Fix: add a pre-redaction guard on `len(json.dumps(ctx.model_dump()).encode())`.

**Severity** — **4:** user-controlled input drives an unbounded expensive op before any
cap (DoS reachable). **3:** missing `max_length` on a field hitting the context/vector
store; per-request token refresh under load. **2:** cap present but generous; cacheable
per-request work uncached. **1:** ordering nit with bounded input.

**False positives** — bounded input that can't realistically exhaust resources; caps
enforced at a gateway/ingress; expensive ops on trusted internal-only input.

---

## Lens 12 — Silent failures (async / streaming / agent code)

**Catches**
- `except Exception: pass` / `catch {}` / `.catch(() => null)` swallowing a real failure
  and proceeding on a default/None/empty value with no log/metric/re-raise.
- **Fallback-as-success:** primary LLM/tool/retrieval call fails, code returns a
  degraded model/cached/canned answer as a first-class success (no degraded flag/metric).
- **`{success: false}` / error body returned with HTTP 200** — monitors and the agent
  loop treat it as healthy.
- **Exceptions inside async generators / SSE after headers flush:** status already 200,
  the stream just ends; client sees truncation as completion.
- **`gather(..., return_exceptions=True)` / `allSettled()`** where the exception objects
  are never inspected — partial failures silently dropped.
- **Empty-array/null as a valid happy path:** RAG returns 0 docs, a tool returns `[]` —
  code answers confidently instead of surfacing "no data / retrieval failed".
- **Uninstrumented caches:** get/set with no hit/miss/error metric; write failures
  swallowed so the system silently runs cold or serves stale.
- **Fire-and-forget tasks:** `create_task`/unawaited promises whose exceptions vanish.
- **Retry/breaker exhaustion returning a default** instead of raising.
- **LLM-output parse failures coerced to `{}`** — a malformed response becomes a
  valid-looking but wrong action.

**How to scan** — `rg -rnE 'except (Exception|BaseException)?\s*:'` then check each for a
bare `pass`/`continue`/`return None|[]|{}` or log-only with no re-raise; JS:
`rg -rnE 'catch\s*\([^)]*\)\s*\{\s*\}'` and `\.catch\(` for `() => null/[]`. Fallback-as-
success: `fallback|degraded|or \[\]|\?\? \[\]|\|\| \{\}` near LLM/tool/retrieval calls —
confirm a degraded flag is set. HTTP 200 + error body: response builders returning
`success: false`/`"error"` without a non-2xx. Streaming: `StreamingResponse|yield|text/
event-stream` — generator wrapped to emit a terminal `event: error` sentinel.
`return_exceptions=True|allSettled\(|gather\(` — results iterated for exceptions. Fire-
and-forget: `create_task\(|ensure_future\(|Thread\(target=` with a done-callback/`.catch`.
RAG empty handling; cache hit/miss/error counters; LLM-output `json.loads`/`model_validate`
parse failures route to a repair/error path. Logging quality: an `except` whose only
output is `logger.debug`/`print` is effectively silent — flag. Dev-mode loudness: degraded
paths with no branch to hard-fail/warn in dev.

**Impact warnings** — *⚠ A swallowed failure or fallback-as-success may cause wrong/empty/
stale data to reach users or feed a bad result into the agent's decision loop while
reporting success (HTTP 200, no metric) — corrupting output invisibly to monitoring.*

**Example findings**
- `routers/chat.py:88` — SSE generator with no try/except; an exception after the first
  `yield` ends the stream with HTTP 200 and a partial answer. Fix: wrap the loop, on
  except `yield {'event':'error',...}` + a terminal sentinel the client checks.
- `agents/tools/web_search.py:54` — `except Exception: return []` turns timeouts into an
  empty result the agent reads as "no results found". Fix: catch specific errors,
  increment a `tool_error` counter, return a typed error the loop distinguishes from
  empty success.
- `api/handlers.py:47` — failure branch returns `{'success': False}` with default 200.
  Fix: set `status_code=502` and surface to the caller's error path.

**Severity** — **4:** swallowed failure / fallback-as-success returning wrong/empty/stale
data to users or into an agent's decision loop while reporting success (RAG failure
answered confidently, tool error as `[]`, mid-stream exception as a complete answer,
all-retries-exhausted returning a default). **3:** failures logged but not metered/
alerted; partial-failure drops in `gather`/`allSettled`; fire-and-forget with no handler;
uninstrumented caches. **2:** missing dev/staging loud-mode on a path that *is* metered in
prod; log-level-too-low; degraded path lacking a caller-facing flag. *Escalate one level
on money/auth/permissions/write paths.*

**False positives** — genuine best-effort paths (analytics, telemetry, cache warming)
**that are logged/metered and comment-justified**; tool-error-as-string-to-model when the
loop is explicitly designed to let the model recover **and** it's also metered; empty array
genuinely meaning "zero results" where code distinguishes it from "failed";
`gather(return_exceptions=True)` where results **are** inspected; tracked degraded-mode
fallback surfaced to the caller; outermost request-boundary `except` that logs full
traceback + metric + returns a non-2xx.

---

## Lens 13 — Schema / contract / state drift & data integrity

**Catches**
- **Naive-vs-aware datetime:** a Pydantic field typed `datetime.datetime` (not
  `AwareDatetime`/`UtcDatetime`) accepts both `...` and `...Z`; naive test fixtures hide
  it; the client sends UTC and the stored/compared value shifts. (Pydantic v2 coerces
  aware to a `TzInfo(UTC)` that fails `== timezone.utc`.)
- **Field-set drift:** a field added to the Pydantic model but not the TS/Zod/OpenAPI
  counterpart, or `Optional` on one side and required on the other. (FastAPI+Pydantic v2
  emits separate input/output schemas when defaults exist → generated-client drift.)
- **Missing migration** for an ORM column change (or a hand-edited one that doesn't
  match) → next deploy throws `column does not exist`.
- **No transaction boundary** around a multi-write use case; or an external side effect
  interleaved between DB writes with no rollback.
- **Commit-then-side-effect** that loses idempotency (row committed, then the external
  call fails or fires twice on retry, no outbox/idempotency key).
- **Second writer to a single-writer table** → lost-update race (no `FOR UPDATE`,
  optimistic version, or constraint).
- **Module-level mutable global as shared state** across uvicorn/gunicorn workers
  (`_cache = {}`, `defaultdict`) — each worker gets its own copy; inconsistent under
  multi-worker.
- **SDK version drift** from training-data pattern-matching (`result_type`→`output_type`,
  `OpenAIModel`→`OpenAIChatModel`, `openai.ChatCompletion.create`→`client.chat.completions.create`, v1 `@validator`→v2 `@field_validator`) — import resolves, call throws.
- **DB enum for churning values** (status/action labels) → a migration on every change.
- **JSON/JSONB read without re-validation** — old rows under a prior schema deserialized
  into the new model, silently dropping/mis-typing fields.

**How to scan** — datetime: `rg` changed models for `: datetime`/`datetime.datetime` not
`AwareDatetime`/`UtcDatetime`/`DateTime(timezone=True)`; check fixtures for naive
datetimes. Field-set: locate each changed `BaseModel`'s TS/Zod/OpenAPI counterpart and
diff names/optionality/defaults; check `separate_input_output_schemas`. Migration: every
changed `Column`/`mapped_column`/Prisma field has a file under `migrations/versions/`;
best signal is `alembic check` (1.18+) / `prisma migrate diff` is empty. Transaction:
`rg -n 'session.commit\(\)'` and walk back — >1 mutation or an external call between writes
with no enclosing `with session.begin():`. Commit/side-effect ordering: after-commit
external calls need an outbox/idempotency key. Single-writer: build the per-table writer
set; a new writer needs `with_for_update()`/optimistic version/unique constraint.
Worker-globals: module-scope `= {}`/`= []`/`defaultdict` mutated per request under
`--workers`/`WEB_CONCURRENCY > 1` → push to Redis/DB. SDK drift: pin each external SDK call
against the installed version. Enum churn; JSON read safety (`model_validate(row.data)` +
a backfill).

**Impact warnings** — *⚠ A partial-failure path with no rollback may cause inconsistent
rows; commit-then-charge may double-charge on retry; a new second writer may cause a
lost-update race; a missing migration may 500 the deploy; a worker-shared global may cause
inconsistent reads under load.*

**Example findings**
- `app/schemas/event.py:47` — `captured_at: datetime` is naive; the client sends `...Z`
  and fixtures are naive, so the tz drift is invisible in CI but shifts stored values.
  Fix: type it `AwareDatetime` and reject naive input.
- `app/services/orders.py:88` — `session.add(order); session.commit(); stripe.Charge.create(...)` — a Stripe timeout leaves a paid-looking order with no charge; a retry double-charges. Fix: `async with session.begin():` + an outbox row + idempotency key.
- `app/core/cache.py:12` — module-level `_rate_limit = {}` mutated per request under
  `gunicorn --workers 4` (limit effectively 4×). Fix: move counters to Redis `INCR`/`EXPIRE`.
- `agent/runner.py:31` — `Agent(model, result_type=Plan)` but `pydantic-ai==0.0.14`
  renamed it `output_type`; lint passes, call raises. Fix: `output_type=Plan`.

**Severity** — **4:** data loss/corruption reachable (partial-failure with no rollback,
commit-then-charge double-charge, lost-update race, missing migration that 500s the
deploy). **3:** datetime drift corrupting timestamps; field-set/optionality drift breaking
a generated client; mutable global as shared state under confirmed multi-worker; SDK call
that throws at runtime. **2:** DB enum for churning values; JSON read without re-validation
on stable shapes; cosmetic default drift. **1:** stylistic divergence.

**False positives** — naive datetimes in pure-internal/batch code that never crosses a tz
boundary; immutable module-level globals (constants, compiled regexes, configured-once
client, `@lru_cache` on a pure function); single-worker/serverless-concurrency-1 deploys;
FastAPI separate input/output schemas when the codegen handles both; `alembic check` noise
from dialect reflection; a second writer already serialized by a unique constraint/advisory
lock/optimistic version.

---

## Lens 14 — Cost & token controls

**Catches** — unbounded agent loops feeding LLM calls (`max_iterations=None`, `while True`
with no cap/deadline/budget — the $47K runaway); no `max_tokens` (output) and no input
ceiling; **self-enforced** budgets a buggy/jailbroken agent can skip (not a gateway that
physically returns 402/429); unbounded context growth (`messages.append` every turn with no
summarization/window); prompt/schema bloat and stale RAG chunks on every call;
**prompt-cache breakage** (timestamps/UUIDs/non-deterministic JSON ordering in the
cacheable prefix); **semantic-cache correctness bugs** (caching user-specific/time-sensitive
responses with no/wrong TTL, or keying on a raw multi-turn fragment so unrelated queries
collide — a security + cost bug); no model routing (flagship for classification/extraction/
formatting); no batching; no per-key spend attribution/circuit breaker; uncapped retry/
reflection loops re-sending full context.

**How to scan** — `rg -n 'while True|max_iterations\s*=\s*None|recursion_limit'` — every
tool-calling loop needs an iteration cap AND a cumulative-token/cost budget checked
**before** each call; `rg -n 'messages.create|chat.completions.create|\.invoke\('` for a
missing `max_tokens`; the budget check must **raise/return before** the API call, not log
after; gateway enforcement (`base_url` → LiteLLM/Portkey/Helicone with per-key limits);
context growth (`messages.append|history.append` with no window/summarization); prompt-cache
hygiene (`cache_control` prefix static; volatile data after it; `json.dumps(..., sort_keys=True)`); semantic-cache eligibility (exclude user-specific/time-sensitive, per-content-type
TTL, key = context-rewritten standalone query, similarity floor); model routing (flagship
hardcoded everywhere); batching (`client.batches`/async gather on bulk jobs); retry/
reflection caps.

**Impact warnings** — *⚠ An unbounded loop with no token/cost budget may cause a runaway
five-figure bill. A semantic cache that can serve one user's stateful/PII data (cart, order,
account) to another may cause both a cost bug and a cross-user data leak.*

**Example findings**
- `agents/research_runner.py:88` — `while not final_answer:` with no cap/deadline/budget.
  Fix: `for step in range(MAX_STEPS):` + `if session_tokens > TOKEN_BUDGET: raise BudgetExceeded` before each call.
- `cache/semantic.py:30` — responses cached on the raw last user message with a flat 24h
  TTL, including order-status replies. Fix: exclude stateful tools (TTL=0), rewrite to a
  standalone query before embedding, set per-content-type TTLs, namespace by user.
- `router.py:55` — every intent-classification call uses `gpt-5-pro`. Fix: route
  classification to a Haiku/nano-class SLM.

**Severity** — **4:** unbounded loop / retry chain with no cap AND no budget reachable in
prod, or self-enforced-only budgets a buggy agent skips; a semantic cache that can serve one
user's stateful/PII data to another. **3:** missing `max_tokens`/input ceiling; append-only
context with no compaction; broken prompt-cache prefix; no spend attribution/breaker. **2:**
no model routing on trivial tasks; no batching; prompt/schema bloat. **1:** missing
dashboards where hard caps already exist.

**False positives** — a loop with no explicit cap where the gateway hard-enforces a per-
session budget (verify the gateway); `max_tokens` absent on a grammar-bounded structured
output; caching user data when the key is namespaced by user/tenant; flagship model on
genuinely hard reasoning; append-only history on short hard-bounded conversations; full-
context resend inherent to stateless chat APIs (the finding is the missing compaction on
long horizons).
