# 03 — Data Protection & Leakage

Lenses 8–9 — the widest risk surface in an agentic-AI backend. Sensitive data
(PII/PHI, secrets, cross-tenant records, internal/system info) leaves the trust
boundary the moment it enters a prompt, an embedding, a log/trace, an error, a
cache, or an outbound tool call. **A vector store is not a security boundary; an
embedding is invertible; an LLM response is an exfiltration channel.**

For every leak finding: name the channel, cite `file:line`, warn **⚠ "this may
cause <impact>"**, give the one-line fix, and rate severity. The combination
**secret-or-PII × external/broad-access sink** is what pushes a finding to sev-4.

---

## Lens 8 — PII/PHI handling (redaction before LLM, logs, traces, embeddings)

**Catches**
- Raw user input / DB rows interpolated into a prompt with **no scrubbing** — name,
  email, SSN, MRN, DOB, card leave your boundary to the provider on every call.
- **Redaction in the wrong order:** scrubbing runs *after* the LLM call (or only
  before the DB write) — the unredacted text already reached the model and the trace.
- **Detector mis-scoped:** runs on the user turn only, missing the system prompt,
  retrieved RAG chunks, tool results, and model output (all four surfaces must be
  covered).
- **Detector fails open:** `try: anonymize() except: pass` forwards raw PII on any
  detector error.
- **Over-collection:** dumping a whole user record into context when the task needs
  one field (`model_dump()`, `SELECT *`, `json.dumps(user)`) — GDPR Art.5(1)(c).
- **No BAA / wrong region:** PHI sent to a provider with no BAA (raw OpenAI vs Azure
  OpenAI/Bedrock) or outside the residency boundary.
- **Invertible embeddings:** PHI/PII embedded and stored unencrypted, with no TTL,
  excluded from deletion.
- **No erasure fan-out:** deleting the user row but leaving PII in prompt logs, the
  trace store, the embedding index, the semantic cache, and analytics.

**How to scan**
- Map every LLM egress and confirm a scrub **before** the call (not after): `rg -n 'messages=|chat.completions.create|\.invoke\(|\.ainvoke\(|HumanMessage\(|bedrock.*invoke_model|anthropic.*messages.create'`. If you find `presidio`/`anonymize`/`redact_pii`/`deidentify`, confirm it runs before **both** the call and the trace/log emit.
- Detector covers all four surfaces (user input, system prompt, RAG/tool context, model output). Check the RAG retrieval and tool-result handlers for a redact call.
- Fail-closed: find the redactor's `except` — on error it must raise/block, not return the original text.
- Minimization: `rg -n 'model_dump\(\)|dict\(row\)|SELECT \*|json.dumps\(user|\.__dict__'` flowing into a prompt — flag whole-object dumps; recommend an allowlist projection.
- Provider/region: raw `openai.OpenAI()` vs `AzureOpenAI`/Bedrock; a BAA endpoint + region pin (`region_name`, `azure_endpoint`) when PHI is in scope.
- Embeddings: `rg -n 'embeddings.create|embed_documents|add_texts|from_documents'` — redacted before embedding? encrypted at rest? TTL + deletion keyed by user/doc?
- Erasure path: `rg -n 'delete_user|gdpr|right_to_erasure|rtbf|purge|anonymize_user'` — fans out to logs, trace store, vector `delete(filter=)`, cache, analytics — not just the row.
- Detector quality: regex-only misses names/addresses/MRNs; confirm an NER detector (Presidio/spaCy) backs it, with PHI identifiers (MRN, NPI, insurance IDs) when HIPAA applies.

**Impact warnings**
- Unredacted PII/PHI to a provider/trace store/logs → *⚠ may cause an unconsented
  cross-border transfer and a HIPAA/GDPR breach on every request.*
- PHI to a provider with no BAA → *⚠ may cause a HIPAA violation with mandatory
  notification and fines.*
- Erasure path misses a derivative store → *⚠ may cause an unsatisfiable
  right-to-erasure obligation (data lives on in embeddings/traces).*
- Detector fails open → *⚠ may cause raw PII to silently reach the model on any
  detector error.*

**Example findings**
- `agents/chat/service.py:88` — `content: f"Customer: {user.model_dump()}"` dumps the
  full user row (email, phone, DOB) into the prompt and Langfuse. Fix: project an
  allowlist and run Presidio `anonymize` before the call.
- `api/users/delete.py:41` — `delete_user()` removes the SQL row but never calls
  `vector_index.delete(filter={user_id})`, leaving invertible PII embeddings live.
  Fix: fan deletion out to the vector store, trace store, and semantic cache.
- `agents/pii.py:17` — `try: text = anonymize(text) except Exception: pass` fails open.
  Fix: on detector failure, raise/block instead of forwarding the original text.

**Severity** — **4:** unredacted PII/PHI leaves the boundary to a provider/third-party
trace store/logs on a normal path; PHI to a no-BAA provider or wrong region; detector
fails open. **3:** redaction mis-ordered or single-surface; invertible PII embeddings
unencrypted or excluded from deletion; erasure misses one store. **2:** no TTL on a
store holding prompts/PII; whole-object dumps where data is internal-only; regex-only
detection on low-sensitivity data. **1:** retention longer than needed but bounded;
over-masking.

**False positives** — synthetic/test fixtures or public identifiers; redaction "missing"
on a dev/`DEBUG`-only log that never ships; PII to a provider under a signed BAA/DPA
with zero-retention terms (verify the config); hashed/tokenized pseudonymous ids;
embeddings of non-personal corpora; a truly ephemeral per-request context wiped at
end of turn.

---

## Lens 9 — Data-leakage vectors (nine channels)

Walk each channel. The recurring root cause across all nine is **scope/identity
omitted** — a filter, a tenant key, a redaction step, or an allowlist that the AI
skipped because it optimized for the happy path.

### 9.1 RAG / retrieval leakage
- **Leaks via:** vector query with no tenant/ACL `filter`/`namespace` on a shared
  index; tenant id from request body/LLM args (IDOR into the retriever);
  **post-filter** instead of pre-filter; a secondary path (admin/debug/eval endpoint,
  BM25/re-ranker/parent-doc/background job) missing the filter; over-broad `top_k`;
  secrets/PII in indexed chunks; citation exposing internal absolute paths; an
  LLM-generated filter as the sole authz; stale embeddings after revocation.
- **Scan:** `rg -n 'similarity_search|as_retriever|\.query\(|\.search\(|vectorstore'` — each needs a `filter=`/`namespace=` **bound to the authenticated identity**; trace the tenant id to the session/JWT, not request/LLM input; check pre- vs post-filter; verify every retrieval entrypoint (`rg -n 'BM25|rerank|ParentDocument|MultiQuery|/admin|/debug|/eval'`); flag raw `metadata['source']` absolute paths returned to the user.
- *⚠ Missing tenant filter on a shared index may cause cross-tenant disclosure on
  every query (a reportable breach, zero attacker sophistication). Tenant id from
  request/LLM args may cause horizontal IDOR / mass data takeover. Citations exposing
  internal paths may cause infrastructure disclosure and document enumeration.*
- **Sev 4:** no tenant filter, tenant from client/LLM input, or post-filter only.
  **3:** filter bypassable on a secondary path or LLM-generated filter as sole authz.
  **2:** over-broad `top_k`, path-leaking citations, stale-after-revocation.
- **FP:** single-tenant app; filter injected centrally in a base retriever/wrapper;
  per-tenant physical isolation (namespace/index from session); genuinely public KB;
  `source` mapped to a sanitized title/signed URL.

### 9.2 Embeddings & vector-store leakage
- **Leaks via:** one shared index with no per-tenant namespace; namespace from client
  input; raw PII/secrets stored in the vector **payload/metadata** returned on every
  match; **embedding inversion** (vec2text/ALGEN reconstruct 50–90% of source text)
  on unencrypted vectors or an exposed embedding endpoint; deletion that orphans
  vectors (no cascade → GDPR Art.17 fail); soft-delete with one query path missing the
  exclusion filter; an untenanted embedding cache; unencrypted backups; a shared-key
  data-plane endpoint allowing bulk scroll/enumeration.
- **Scan:** `rg -rEn '\.(query|search|similarity_search)\('` for a `namespace=` + server-derived tenant `filter=`; `rg -rEn 'upsert|add_documents|insert_vectors'` for a redaction step before embedding; inspect `metadata=`/`payload=` for `email|ssn|phone|dob|mrn|api_key|token|full_text`; audit the delete path for a vector-store `delete(ids=…)` in the same flow; check embedding-cache keys include tenant; confirm encryption-at-rest + per-tenant keys, not one global `PINECONE_API_KEY`.
- *⚠ A query with no namespace/tenant pre-filter may cause cross-tenant disclosure to
  every user. Raw PII in metadata may cause a single benign query to exfiltrate
  identifiable records. An exposed embedding endpoint may cause inversion back to the
  original sensitive text. DB-delete-without-vector-delete may cause erased data to
  keep surfacing.*
- **Sev 4:** cross-tenant reachable (no namespace + no tenant pre-filter, namespace
  from client, shared-key bulk endpoint), or raw secrets/PHI embedded & cross-tenant
  returnable. **3:** PII/raw text in metadata returned to users/LLM; orphan-vector
  erasure failure; soft-delete gap; untenanted cache; unencrypted backups. **2:**
  inversion exposure where vectors are same-tenant-only but unencrypted; scores/IDs/
  paths echoed.
- **FP:** single-tenant; client-supplied tenant re-derived server-side; post-filter as
  belt-and-suspenders atop a correct pre-filter; non-sensitive public corpus;
  per-tenant cache instance; already-public/tokenized data.

### 9.3 Logs / traces / observability leakage
- **Leaks via:** OTel/auto-instrumentors opted **into** content capture
  (`gen_ai.content.prompt`); LLM-trace decorators (`@traceable`, `@observe`, Langfuse,
  Traceloop, Phoenix) with **no `mask=`**; tool args/results & RAG chunks in spans;
  full request/response body logging (morgan/pino, request-logging filters);
  `Authorization`/cookies/API keys logged; Sentry/Datadog `send_default_pii=True` with
  no `before_send`; whole-object dumps (`json.dumps(user)`); conversation history
  persisted unredacted with no TTL/tenant scope; prod traces copied into eval/fine-tune
  datasets.
- **Scan:** `rg -n "(logger|log|console)\.(debug|info|warn|error)\(.*(prompt|messages|completion|request|body|input|output)"`; `rg -n 'set_attribute|gen_ai\.(prompt|completion|content)|OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT|TRACELOOP_TRACE_CONTENT'` set true; trace decorators **without** a mask (`rg -n 'mask=|hide_inputs|before_send'`); `rg -ni 'authorization|bearer |api[_-]?key|set-cookie' ` inside log statements; Sentry init for `send_default_pii=True`; prod `LOG_LEVEL`/`setLevel.*DEBUG`.
- *⚠ Full prompts/completions in OTel spans or LLM traces may cause unconsented
  cross-border transfer and a HIPAA/GDPR breach to a SaaS outside the app's authz.
  Bearer tokens/API keys in logs may cause account takeover by anyone with log-read
  access. send_default_pii may cause silent secret/PHI exfiltration on every
  exception.*
- **Sev 4:** plaintext secrets/tokens in logs/traces, OR PII/PHI/full prompts exported
  to a third-party trace/APM with no masking, OR cross-tenant data in a shared log/
  trace store. **3:** PII/history logged unredacted to an internal-only sink with broad
  access; raw PII in span names. **2:** object-dump/DEBUG-level logging that leaks only
  when enabled; no centralized+tested redaction. **1:** verbose internal info (stack/
  SQL without data). **0:** metadata-only (ids, token counts, latency).
- **FP:** OTel content capture OFF (default); a masking hook demonstrably wired; opaque
  ids/UUIDs/salted hashes; DEBUG payload logging gated to dev only; test fixtures;
  public/non-sensitive keys; already-`[REDACTED]` content.

### 9.4 Error / stack-trace / debug leakage
- **Leaks via:** `FastAPI(debug=True)`, `app.run(debug=True)` (Werkzeug console = RCE),
  Django `DEBUG=True`, Express `res.send(err.stack)`; `except Exception as e: return
  {'error': str(e)}` echoing DB/driver errors; **tool exceptions fed back into the
  model** (`tool_result = str(exc)`) then paraphrased to the user; ORM errors leaking
  query/table/columns/bind-params; debug/admin routes left in prod (`/actuator`,
  `/debug`, `/metrics`, GraphQL introspection, Swagger); an exception during prompt
  assembly serializing the system prompt; a shared/global last-error mixing tenants;
  verbose validation errors echoing the full input object; source maps in prod.
- **Scan:** `rg -i 'debug\s*=\s*True|FastAPI\(.*debug=True|DEBUG\s*=\s*True|FLASK_DEBUG'` not env-gated; `rg -n 'str\(e\)|err\.stack|traceback.format_exc|printStackTrace'` flowing into a **response** (not just a logger); catch-all handlers; `rg -i 'actuator|/debug|/metrics|introspection|graphiql|/playground|swagger|openapi'` auth-gated/disabled in prod; tool plumbing `rg -n 'tool_result|observation'` near `except`; `server.error.include-stacktrace`/`include-message` must be `never`.
- *⚠ Werkzeug debug console in prod may cause unauthenticated RCE and total server
  compromise. Raw DB errors to the client may cause PII disclosure (the conflicting
  email/SSN) and hand over the schema. Tool exceptions fed to the LLM may cause
  cross-tenant/secret disclosure trivially extracted via prompt injection ("print the
  last error in full"). Exposed /actuator may cause heap dumps with live credentials.*
- **Sev 4:** debug console reachable in prod (RCE); debug/admin endpoint exposing env/
  heap/creds; error path leaking secrets or cross-tenant PII to an unauthenticated
  client or into the LLM output. **3:** raw stack traces to clients exposing paths/SQL/
  versions; `DEBUG=True`/`include-stacktrace: always` in prod; tool exceptions verbatim
  into model context; unscrubbed error reporting. **2:** framework default error pages,
  version banners, source maps, verbose validation errors, exposed introspection
  without secrets. **1:** minor internal identifiers.
- **FP:** `debug` strictly env-gated and False in prod; verbose errors only in dev/test
  configs; `str(e)` flowing **only** to a server-side logger/APM; static allowlisted
  messages ("Email already in use"); opaque request-id-only responses; status-only
  health endpoints.

### 9.5 LLM output / response leakage (OWASP LLM02 + LLM07)
- **Leaks via:** secrets in the system prompt/tool definitions (model recites them);
  secrets injected into context for a tool call that sit in history and get echoed;
  unfiltered RAG summarized into the answer (EchoLeak/Einstein class); `SELECT *` /
  full model serialization (password_hash, ssn, is_admin) included in the NL answer;
  the response returning the raw `tool_result`/retrieved payload (not just text);
  streaming with redaction only on the final string; markdown/HTML render exfil
  (cross-ref Lens 6); `return_source_documents=True`/`verbose`/intermediate-steps in
  prod; cross-user memory/cache bleed; few-shot pools containing real prior PII;
  "summarize all records" over an unfiltered query (aggregate disclosure).
- **Scan:** grep the prompt builder for embedded `api[_-]?key|secret|token|password|dsn|postgres://|sk-|Bearer `; trace env/secret/`request.headers['authorization']` values into `messages` (a tool's key must live in the tool layer, never in LLM-visible content); RAG calls for a server-derived tenant filter; DB results for `SELECT *`/`.model_dump()` without `exclude=` before reaching the model/client; the response boundary for a server-side redaction/output-validation step (per-chunk on streaming); markdown render (`dangerouslySetInnerHTML`, `v-html`, `marked(`) for URL allowlisting; `verbose=True`/`return_source_documents=True`/`return_intermediate_steps=True` env-gated off; cache/memory keys include `user_id`/`tenant_id`.
- *⚠ A secret in the prompt may cause full credential disclosure to any user who asks
  the model to repeat its instructions (LLM07). An unfiltered RAG query may cause
  cross-tenant PII to be summarized into another customer's answer. `SELECT *` into the
  model may cause internal fields (password_hash, margin, is_admin) to be read off the
  NL answer (BOPLA). Markdown render of model output may cause zero-click exfiltration.*
- **Sev 4:** live secret in prompt/context reachable in output (LLM07); RAG/DB feeding
  the model with no tenant filter (cross-tenant summarization); markdown/HTML render
  with unsanitized model URLs; fields/rows across an authz boundary (BOPLA). **3:**
  `SELECT *`/full serialization of internal-but-not-credential fields; raw exception/
  SQL relayed through the model; streaming redaction only on the final string;
  `return_source_documents`/verbose on a prod path. **2:** cache/memory key missing
  identity (currently single-tenant); over-broad response schema; incomplete redaction
  list.
- **FP:** an internal-looking field that is the caller's **own** data scoped by RLS;
  `tokenizer`/`token_count` matched by a secret grep; `verbose` behind a prod-off
  `DEBUG` gate; an "instructions" string with only behavioral rules and public info;
  single-tenant/public corpus; final-only redaction on a **non-streaming** endpoint;
  mock secrets in test files.

### 9.6 Cross-tenant / multi-tenant isolation leakage
- **Leaks via:** ORM/SQL lookup by id/PK with no `tenant_id`/`org_id` in the WHERE
  (IDOR/BOLA); tenant scope from request not session; RAG with no namespace/metadata
  filter; multi-hop/graph/re-rank crossing the boundary unfiltered; agent memory keyed
  only by `conversation_id`; **shared module-level/global state** (a `current_tenant`,
  cache dict, singleton client) set per-request and reused across concurrent requests;
  agent under a broad service account; tools fetching model-supplied ids with no tenant
  check; object-storage keys built from raw user input; cache keys omitting tenant;
  background jobs/webhooks iterating all rows; list/export/admin endpoints with no
  org filter; missing DB RLS.
- **Scan:** `rg -n 'find_by\(|findById|get_object_or_404|filter\(id=|findUnique\(\{\s*where:\s*\{\s*id'` and confirm a tenant predicate in the same query; `rg -niE '(tenant|org|account|workspace)_id'` traced to auth context, not `req.body`/query/header; RAG calls for a server-set `namespace=`/`filter=` re-applied on every downstream hop; **shared mutable state**: `rg -n '^[A-Za-z_]+ *= *(\[\]|\{\}|dict\(|list\()'`, `global `, `@lru_cache`, `current_tenant`, `app.state.` holding per-request data (use `contextvars`/request scope instead); agent creds for a global admin/service token; cache keys for a tenant segment; migrations for `CREATE POLICY`/`ENABLE ROW LEVEL SECURITY` + per-request `set_config('app...`.
- *⚠ Object lookup with no tenant scope may cause IDOR/BOLA cross-tenant disclosure
  (OWASP API1 #1). Tenant id from a client field may cause full tenant impersonation.
  RAG with no tenant filter may cause another tenant's docs in the answer (research:
  up to ~95% of benign queries leak in a shared corpus). Shared global tenant context
  may cause non-deterministic cross-tenant bleed under load — extremely hard to
  reproduce.*
- **Sev 4:** a concrete cross-tenant path to PII/PHI/secrets/financial data reachable
  by a normal authenticated tenant (no tenant scope, tenant from client, RAG/tool with
  no filter, global state proven to bleed). **3:** isolation depends on one fragile
  layer (app filter but no RLS; filter at vector search but not a downstream hop; broad
  service credential currently constrained). **2:** secondary surfaces leak metadata
  (cache key missing tenant on low-sensitivity values; predictable sequential ids but
  the query is scoped; cross-tenant analytics counts). **1/0:** RLS off but every query
  correctly scoped and tested.
- **FP:** single-tenant; lookups scoped by a shared base query/manager/`TenantScopedQuerySet`; request `tenant_id` re-validated against the session; RLS enforcing the predicate at the engine; genuinely global reference data; immutable stateless module-level clients.

### 9.7 Cache & session leakage
- **Leaks via:** semantic/response cache keyed by prompt only (no tenant/user); a
  process-global singleton/Memory object holding the previous request's context; a CDN
  caching authenticated responses (missing `Cache-Control: private, no-store`);
  **web-cache deception** (auth route via `/account/avatar.css`); vLLM/TGI prefix/KV-cache
  shared across tenants (prompt timing side channel); session fixation (no
  `regenerate()` after login, CWE-384); too-broad cookie `Domain`; idempotency/dedup
  cache returning another user's stored response; shared streaming/SSE buffers.
- **Scan:** `rg -n 'cache_key|make_key|hash\('` — keys must include `user_id`/`tenant_id` (flag `hash(prompt)`, `hash(messages)`); semantic-cache libs (`GPTCache|semantic_cache|redisvl`) need a metadata/tenant filter on read **and** write; process-global mutable state and singletons storing `self.(user|tenant|history)`; `rg -n 'Cache-Control|s-maxage|public'` — authed/PII responses must be `private, no-store` with `Vary: Authorization, Cookie`; session lifecycle `rg -n 'regenerate|cycle_key|invalidate|rotate'` near login; session tokens read from query/path; prefix-cache flags in self-hosted inference.
- *⚠ A cache keyed without tenant may cause one customer's cached PII answer to be
  served to another. An authenticated response cached `public` at the CDN may cause
  mass disclosure of account data and session/CSRF tokens → account takeover. A
  process-global holding prior context may cause silent cross-user contamination under
  concurrency, no attacker required. No session regeneration after login may cause
  session fixation/hijacking.*
- **Sev 4:** cache/session serves real PII/PHI/secrets/tokens to other users or enables
  takeover (cache keyed without tenant returning another's data, authed response cached
  `public`, web-cache deception exposing tokens, no session-ID rotation). **3:**
  cross-user leakage of non-credential sensitive data under specific timing/concurrency;
  shared-singleton context bleed. **2:** leakage of less-sensitive internal info; missing
  `Vary`/headers where caching doesn't happen today. **1/0:** correctly keyed/scoped.
- **FP:** cache keyed by prompt but holding strictly non-sensitive tenant-independent
  data; immutable/stateless global singletons; `@lru_cache` on a pure function where
  identity is already an argument; truly public assets cached `public`; per-request
  objects only *looking* global; single-tenant cookie scope; client `tenant_id` used
  only as a label with the real filter derived from the session.

### 9.8 Prompt / context / history leakage
- **Leaks via:** secrets/full user records interpolated into the system prompt;
  appending the entire (or another) conversation history with no per-turn re-scoping
  (a global `messages = []`, mutable default arg, shared `ConversationBufferMemory`);
  memory recall with no tenant pre-filter (MEXTRA/MINJA class); RAG ranked by relevance
  not authorization; oversized context (whole row/document/tool JSON); tool results fed
  back verbatim; **redaction on output but not input context**; cross-conversation
  cache/KV-cache with no tenant salt (PROMPTPEEK class); few-shot pools embedding prior
  users' PII; full assembled prompt logged/traced; multi-tenant prompt templates loading
  tenant data by a client-supplied id.
- **Scan:** `rg -n "(system_prompt|prompt|messages|content)\s*=.*(api[_-]?key|secret|token|password|os\.environ|settings\.|getenv)"`; whole-object dumps into context (`{user}`, `.dict()`, `model_dump()`) vs an allowlist; memory/vector queries for a server-derived `filter=`/`namespace=`; history scoping (`ConversationBufferMemory`, `messages.append`, `history +=`) keyed per session/user and **instantiated per-request** (flag module-level/global state, mutable default args, app-lifetime singletons); redaction wrapping `assemble_context()`/retrieved docs/tool results **before** the call (not only the response); cache keys for a per-tenant salt.
- *⚠ A secret interpolated into a prompt may cause credential disclosure to the provider
  and the prompt logs → backend takeover. Memory/RAG recall with no per-user filter may
  cause another user's PII/PHI in the current conversation. Carrying another
  conversation's history may cause cross-session data leakage. No input-side redaction
  may cause raw PII to reach the model and provider telemetry even when the visible
  output looks clean.*
- **Sev 4:** cross-tenant/cross-user sensitive data provably reaches the model context
  and/or the wrong user (memory/RAG/history with no tenant scope, tenant from client,
  live secret in a logged/provider-bound prompt) in normal flow. **3:** isolation
  depends on one un-enforced check (most call sites scoped but one path misses it;
  redaction on output not input). **2:** over-broad context with no current cross-tenant
  crossing; internal/system-prompt info without regulated PII. **1:** in-tenant prompt
  logging that should be redacted; missing cache salt where tenants don't share a cache.
  *Escalate one level if data is PHI/financial or the leak is silent.*
- **FP:** constant strings (app name, role text, public docs); request id re-validated
  against the session; history keyed by authenticated user in a per-request store;
  centralized redaction chokepoint even if call sites look raw; prompt logging behind a
  prod-off debug flag to a tenant-isolated sink; test/fixture PII; single-tenant.

### 9.9 Egress / third-party / tool-call leakage
- **Leaks via:** whole-model dumps (`json.dumps(user.model_dump())`) into a prompt or a
  tool-call argument sent to an external provider/MCP server with no field allowlist;
  outbound HTTP/webhook/MCP calls to non-allowlisted domains (prompt-injection-driven
  exfil); Slack/Teams/email callbacks built from DB rows; observability exporters
  shipping raw prompts/tool-args (the vendor becomes an un-DPA'd processor);
  training/fine-tune/eval pipelines ingesting raw prod data (PII baked into weights);
  a consumer endpoint with **no zero-data-retention/no-train flag and no DPA/BAA**;
  secrets passed as tool args "so the agent can call the API"; error payloads forwarded
  to an LLM/webhook; RAG over-fetch sending unauthorized chunks to the model; redaction
  on the final answer but **not** on intermediate tool-call args / streamed deltas.
- **Scan:** enumerate egress — `rg -n 'requests.post|httpx.(post|stream)|aiohttp|fetch\(|axios|webhook|OpenAI\(|anthropic|bedrock.*invoke_model|chat.completions.create|messages.create'`; for each prompt/tool-arg build, trace the content source and flag `.model_dump()`/`.dict()`/`JSON.stringify(obj)` of a PII model; a redaction/DLP step **before** egress covering tool args + logs (`rg -n 'redact|scrub|sanitize|deidentify|presidio|dlp'`); a destination allowlist (`allowlist|allowed_hosts|urlparse|hostname in`); ZDR/retention posture (`store=|data_retention|zero.?data|no.?train|base_url=|AZURE_OPENAI`); secrets into prompts/tool args; the same `redact()` applied to **every** egress (webhook, background job, tool wrapper, error reporter, eval logger) — redaction on one path and not the parallel ones is the most common real gap.
- *⚠ A whole-model dump into a prompt/tool arg may cause PII/PHI disclosure to a third
  party with no DPA/BAA (GDPR Art.28/44, HIPAA) on a single request. No destination
  allowlist on MCP/tool/webhook calls may cause one-shot exfiltration to an
  attacker-controlled domain via prompt injection. A provider with no ZDR/DPA may cause
  every prompt to be retained or trained on — irreversible. Redaction only on the final
  answer may cause leakage through intermediate tool-call args.*
- **Sev 4:** real exploitable egress of PII/PHI/secrets/cross-tenant data on a live path
  (whole-model dump to a no-DPA/ZDR provider; outbound/MCP/webhook to a non-allowlisted
  destination from model output/config; secret in a prompt/tool arg; raw prod data into
  a fine-tune set). **3:** redaction on the main path but missing on a secondary egress;
  RAG over-fetch; full prompts to an observability vendor with a DPA but no scrubbing;
  missing allowlist where targets are currently internal but unvalidated. **2:**
  over-broad field selection with one non-sensitive extra; ZDR set but DPA unverified;
  prompt-length/token-count metadata logging. **1:** redaction naming nits. **0:** dump
  of a non-sensitive model, or destination hardcoded to a same-tenant internal service
  behind the allowlist.
- **FP:** dump to an internal-only service behind the allowlist (same trust boundary);
  prompts/tool-args to a self-hosted in-VPC sink; `tokenizer`/`token_count`/`bearer`-typed
  names matched by a secret grep; a `.model_dump()` of a non-sensitive DTO; ZDR enforced
  at the org/account level (documented in infra/DPA); redaction at a gateway/proxy
  (LiteLLM/Cloudflare AI Gateway/sidecar); a hardcoded outbound URL to a vetted vendor.

---

## Reporting leakage findings
Lead each with the channel and the impact warning, e.g.:
> **⚠ Sev 4 — Cross-tenant RAG leakage** · `rag/retriever.py:31` ·
> `vectorstore.similarity_search(query, k=8)` has no tenant filter on a shared index.
> **This may cause** another tenant's confidential documents to be summarized into the
> answer (reportable breach, GDPR/HIPAA). **Fix:** pass
> `filter={'tenant_id': session.tenant_id}` derived from the verified session.
