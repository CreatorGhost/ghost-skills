# 01 — Security & Access Control

Lenses 1–3. The single most common and most damaging class of AI-built-backend
bug is **missing authorization** — agents wire the happy path and skip the
ownership predicate. When authorization is the question, default to the **higher**
severity, and **escalate one level whenever the path is reachable by the LLM via
tool arguments** (prompt injection makes those arguments attacker-controlled).

---

## Lens 1 — Access control & authorization (authz, identity, tenancy)

**Catches**
- **BOLA/IDOR:** a handler queries by an id from path/body but filters only on
  that id, never on the authenticated user/tenant — `db.order.find(req.params.id)`
  with no `WHERE user_id = me`.
- **Tenant scope from the request, not the session:** `tenant_id`/`org_id` read
  from body/query/header or an **LLM tool argument** instead of the verified JWT/
  session claim — attacker (or prompt injection) sets a victim's id.
- **Broken function-level authz (BFLA):** new admin/privileged route has authN
  (logged-in) but no role check; `DELETE`/`PUT` reuses the read endpoint's lax guard.
- **Auth missing entirely:** the agent added the handler + router entry but forgot
  `Depends(get_current_user)` / middleware / `@login_required` — endpoint is public.
- **God-mode agent:** tool layer calls the DB/API with one shared admin/service
  token (e.g. `SUPABASE_SERVICE_ROLE`, `BYPASS_RLS`) regardless of who's logged in.
- **Delegation collapses to impersonation:** token exchange (or raw token reuse)
  carries only the user's `sub` with no `act` claim — no audit trail of which agent
  acted (RFC 8693).
- **JWT weaknesses:** `alg=none` accepted, HS/RS algorithm confusion, or signature
  checked but `iss`/`aud`/`exp` not validated.
- **MCP/tool-gateway confused deputy:** server accepts tokens without checking
  `aud` is itself, and/or forwards the raw user token to a downstream API (token
  passthrough — prohibited by the 2025-06 MCP spec; mandate audience binding,
  RFC 8707).
- **Unfiltered cross-tenant RAG retrieval** (cross-ref Lens 9): shared vector index,
  no per-tenant filter (OWASP LLM08).
- **RLS defined but inert:** policies exist but `SET LOCAL app.tenant_id` / `SET
  ROLE` is never issued per request, so policies pass through to all rows.

**How to scan**
- Map every new/changed route, tool handler, MCP tool, queue consumer, and
  websocket; for each confirm **both authN and authZ** run. Find handlers mounted
  before the auth middleware: `rg -n "app.use|router.use|@UseGuards|Depends\("`
  and diff against the new-endpoint list.
- Route enumeration: `@app.(get|post|put|patch|delete)`, `@router.`, `path(`/
  `urlpatterns`. For each new route ask: auth dependency? ownership/role check?
  response a typed schema or a raw model?
- BOLA: for every handler taking an id from path/body, trace the DB query; flag
  any `findUnique/find_by_id/get(pk)/findById` filtered **only** by id. Grep
  `params.id`, `path_params[`, `req.params`, `pk=`, then read the query two lines down.
- Tenant-from-request: `rg -niE "(tenant|org|account|user|customer)_?id\"?\s*[:=]\s*(req\.(body|query|params)|request\.|payload|args|tool_?args|kwargs)"` — any DB filter or authz decision keyed off request-supplied id is a finding.
- God-mode creds: `rg -niE "service_?(account|token|key)|admin_?token|SUPABASE_SERVICE_ROLE|BYPASS_RLS|set_config\('role'|GRANT ALL"`. Do tool calls use a per-request user token/RLS context or one shared privileged credential?
- JWT: `rg -niE "verify\(|decode\(|algorithms?\s*[:=]|jwt\."` — confirm an algorithm allowlist (no `none`, no HS+RS mixing) and that `audience`/`issuer`/`exp` are validated. Flag `verify=False`, `algorithms:['none']`, decode-without-verify.
- MCP/gateway: confirm inbound `aud` is checked to equal this server, and a **new** token is minted for downstream (token exchange / on-behalf-of) — not the raw token reused on the outbound `Authorization` header.
- Delegation: search `act`, `actor_token`, `on_behalf_of`, `subject_token`; confirm the exchanged token carries an `act` (agent) claim beside `sub`.
- RLS: confirm `SET LOCAL app.tenant_id` / `SET ROLE` per request and policies `ENABLE`d + `FORCE`d.

**Impact warnings**
- Object lookup with no tenant scope → *⚠ may cause cross-tenant PII/PHI disclosure
  (IDOR/BOLA, OWASP API1): any authenticated tenant reads/modifies another's records
  by changing an id — a reportable breach.*
- `tenant_id` from client/LLM input → *⚠ may cause full tenant impersonation /
  account takeover.*
- God-mode service account → *⚠ may cause any user to reach any data the agent can,
  a confused-deputy breach with no per-credential boundary.*
- `alg=none` / unverified signature → *⚠ may cause forged tokens to be accepted.*
- Token passthrough → *⚠ may cause a downstream service to grant the agent broader
  access than the user holds.*

**Example findings**
- `tools/db_client.py:14` — every agent tool calls Postgres with the
  `SUPABASE_SERVICE_ROLE` key, bypassing RLS for all users. Fix: open the
  connection with the request user's JWT and `SET LOCAL request.jwt.claims`.
- `api/routes/documents.ts:42` — `getDocument(req.body.tenantId, id)` trusts the
  tenant id from the request body (LLM-populated). Fix: use `ctx.auth.tenantId`
  from the verified token.
- `auth/jwt.js:9` — `jwt.verify(token, key, {algorithms:['HS256','RS256']})` with no
  `audience`/`issuer` enables algorithm confusion. Fix: pin one algorithm, pass
  `{audience, issuer}`.
- `mcp/gateway.go:120` — inbound user bearer token copied straight into the
  downstream `Authorization` header; `aud` never validated. Fix: validate
  `aud == this_server`, then mint a downstream token via RFC 8693 with `sub`+`act`.

**Severity** — **4:** unauthenticated reachable endpoint/tool, or any cross-tenant/
cross-user access a normal user can craft (request-supplied tenant id, missing
ownership check, RLS bypass, unfiltered cross-tenant RAG, `alg=none`, token
passthrough). **3:** real authz weakness needing a precondition or partial leak
(over-broad granted scopes, missing `aud/iss/exp` on a single-tenant issuer,
delegation with no `act` claim, tokens in logs). **2:** hygiene (scope tightening,
generous clock skew, per-tenant token encryption, per-identity rate limiting).
*Escalate one level when reachable by the LLM via tool args.*

**False positives** — intentionally public endpoints (health, login, webhooks,
OAuth callbacks); request-supplied ids used only **after** a server-side ownership
check; single-tenant/internal deployments where tenancy is out of scope;
service-to-service tokens on trusted hops where the user identity is still enforced
and propagated; authz enforced in a layer the scan didn't trace (middleware/
decorator/RLS/base query — this is a known ~78% false-positive area, so confirm the
check is absent across **all** files); HS256 for legitimate symmetric first-party
tokens within one trust boundary.

---

## Lens 2 — Injection & API security (OWASP API Top 10)

**Catches**
- **Mass assignment / overposting:** request body spread into the ORM —
  `prisma.user.update({data: req.body})`, `User(**payload.dict())`,
  `Object.assign(model, req.body)` — lets a client set `role`, `is_admin`,
  `balance`, `verified`.
- **SSRF** (esp. agent fetch/scrape tools): user/model-supplied URL into
  `requests.get`/`httpx`/`fetch`/`urllib` with no allowlist, reaching
  `169.254.169.254`, `localhost`, `file://`, `gopher://`.
- **Injection:** f-string/template SQL, Mongo `$where`/`$function`,
  `os.system`/`subprocess(shell=True)`, path traversal via `open(base+user_path)`.
- **Missing/late rate limiting** on login, password-reset, token-mint, search, and
  LLM-backed routes (the last is also a cost-DoS).
- **Unsafe deserialization:** `pickle.loads`, `yaml.load` (non-safe), `jsonpickle`,
  Node `node-serialize`/`eval` on attacker bytes.
- **Over-permissive CORS:** `Access-Control-Allow-Origin:*` **with**
  `Allow-Credentials:true`, or origin reflected from the request without an
  allowlist.
- **Excessive data exposure:** handler returns the whole ORM row (password hash,
  internal flags) instead of a response schema.

**How to scan**
- Enumerate new routes (as Lens 1). For each: auth? ownership/role? typed response?
- Mass assignment: `rg -n "req.body|request.json|\*\*payload|\*\*data|\.dict\(\)|model_dump\(\)|Object.assign|\{...req.body\}|setattr"` flowing into `.create/.update/.save/.insert` with no field allowlist (DTO, `pick()`, serializer `fields`/`read_only_fields`).
- SSRF: `rg -n "requests\.(get|post)|httpx\.|urllib.request|fetch\(|axios\.|urlopen|aiohttp"` — URL user/model-derived? validated against an allowlist **and re-checked after DNS** (rebinding)? Flag reachability of `127.0.0.1`, `169.254.169.254`, `10./172.16./192.168.`, `::1`, `file://`.
- Injection: `rg -n "f\"SELECT|\"SELECT \" \+|\.raw\(|text\(|\$where|\$function|eval\(|exec\(|os.system|subprocess.*shell=True|child_process.exec"` with interpolated user input. Parameterized queries/ORM filters are safe.
- Path traversal: `rg -n "open\(|readFile|sendFile|path.join\(|os.path.join\("` with a user segment — require `realpath`/`resolve` + `startswith(base)` and rejection of `..`/absolute.
- Deserialization: `rg -n "pickle.loads|yaml.load\(|jsonpickle|node-serialize|Marshal.load|ObjectInputStream"` on request/cookie/queue data.
- Rate limiting: `rg -n "slowapi|Limiter|@limiter.limit|express-rate-limit|Throttle"` — then confirm login/reset/token/LLM routes are covered.
- CORS: `rg -n "CORSMiddleware|allow_origins|Access-Control-Allow-Origin"` — flag `["*"]`+`allow_credentials=True` and reflected origin.
- Excessive exposure: each handler returns a response DTO (`response_model=`, serializer, `select`/`pick`), not a raw entity.

**Impact warnings**
- Mass assignment of `role`/`is_admin`/`balance` → *⚠ may cause privilege escalation.*
- SSRF reaching cloud metadata → *⚠ may cause theft of cloud credentials and full
  account compromise.*
- SQL/command injection → *⚠ may cause data exfiltration or RCE.*
- `*`+credentials CORS → *⚠ may cause a victim's session/data to leak cross-site.*
- Missing rate limit on login/LLM route → *⚠ may cause account-takeover brute force
  or a five-figure cost-DoS.*

**Example findings**
- `routes/orders.py:42` — `db.query(Order).filter(Order.id==order_id).first()` with
  no ownership check (BOLA). Fix: add `.filter(Order.user_id==current_user.id)`.
- `api/users.ts:88` — `prisma.user.update({where:{id}, data: req.body})` (mass
  assignment of `role`). Fix: `data: { name: req.body.name, bio: req.body.bio }`.
- `agents/tools/fetch_url.py:23` — `httpx.get(url)` on a model-supplied URL reaches
  `169.254.169.254` (SSRF). Fix: resolve host, reject private/link-local/loopback
  before **and** after DNS; deny non-http(s) schemes.
- `main.py:31` — `CORSMiddleware(allow_origins=['*'], allow_credentials=True)`. Fix:
  pin `allow_origins` to an explicit list; drop the wildcard when credentials are on.

**Severity** — **4:** any unauthenticated/unauthorized path to other users' data or
actions — BOLA/IDOR mutating another tenant's record, mass assignment of privilege
fields, SSRF to metadata/internal services, SQL/NoSQL/command injection, unsafe
deserialization of attacker bytes, privileged endpoint with no auth, `*`+credentials
CORS leaking a session. **3:** narrower — BFLA on non-sensitive data, missing rate
limit on login/reset/token/LLM, excessive exposure of internal-but-not-secret
fields, partially-gated path traversal. **2:** validated-by-type but missing length/
enum bounds, loose rate limit, over-broad CORS allowlist, stack traces in errors.
*Default higher when authorization is the question.*

**False positives** — intentionally public endpoints; `allow_origins:['*']` **without**
credentials on a public token-in-header API; raw SQL via `text()`/`.raw()` with bound
params; `yaml.safe_load`/`pickle` on first-party trusted data; BOLA already scoped
upstream (`current_user.orders.get(id)` or tenant-prefiltered middleware); internal
endpoints protected by mTLS/network policy/gateway; rate limiting at the gateway.

---

## Lens 3 — Secrets, supply chain & MCP trust

**Catches**
- Hardcoded keys/tokens in source/images/CI (`sk-`, `AKIA`, `ghp_`, `xoxb-`,
  bearer literals, private keys) — often AI "sample" values that are real.
- Secrets logged/echoed: `process.env`/headers printed at INFO into log aggregators.
- Unpinned/floating deps (`^`, `~`, `*`, `latest`, `git+https` with no SHA) and no
  committed lockfile (Shai-Hulud-style malicious republish surface).
- Lifecycle scripts enabled: `npm install` (not `npm ci --ignore-scripts`), no
  `ignore-scripts=true` in `.npmrc`.
- **Slopsquatted/hallucinated packages** the AI invented (USENIX 2025: ~19.7% of
  LLM-suggested packages don't exist; attackers pre-register them).
- MCP config registering untrusted/unpinned servers over `http://` or
  `npx -y <pkg>@latest`, with no version pin (rug-pull surface).
- Tool poisoning: MCP tool descriptions/results with hidden instructions
  (zero-width chars, base64, `<system>` tags) fed to the model unsanitized.
- Tokens in plaintext config/DB (not hashed); token passthrough to a downstream API.
- Insecure env fallbacks: `process.env.KEY || 'dev-key-123'` shipping a default cred.

**How to scan**
- Real scanner over **history**, not just the tree: `gitleaks detect`, `trufflehog
  filesystem . --only-verified`, and `git log -p | gitleaks detect --pipe`.
- Key shapes: `rg -n 'sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[baprs]-|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'` across src, Dockerfile, `*.yml`, `*.tf`, k8s, committed `*.env`.
- Insecure fallbacks / logged secrets: `rg -n 'process\.env\.[A-Z_]+\s*\|\|'`, `rg -n "os\.environ\.get\([^)]+,\s*['\"]"`, `rg -ni 'logger\.(info|debug).*\b(token|secret|key|password|authorization)\b'`.
- Pinning: confirm a committed lockfile; `rg -n '"[^"]+":\s*"[\^~*]|"latest"' package.json`; `rg -n '^[A-Za-z0-9_.-]+\s*([><]=?|\*|$)' requirements.txt` (no `==`).
- Lifecycle scripts: `.npmrc` has `ignore-scripts=true`; CI uses `npm ci --ignore-scripts`; `rg -n '"(pre|post)install"' package.json`.
- Hallucinated deps: list directs (`jq -r '.dependencies+.devDependencies|keys[]' package.json`) and verify each exists with real download history; watch conflations (`libA-libB`), `-sdk`/`-official` lures, digit-swaps.
- MCP config: `find . -name '.mcp.json' -o -name 'mcp.json' -o -name 'claude_desktop_config.json'`; flag `http://`, `npx -y ...@latest`/`uvx ...` with no pin, unknown remote `url`.
- Tool description → prompt: confirm zero-width/control-byte sanitization and that side-effecting tools require approval, not blind auto-execution.
- Token handling: `rg -n 'access_token|refresh_token|client_secret'` — hashed before persistence? inbound token **not** reused on outbound calls?
- Provenance: CI uses `pip install --require-hashes` / `npm ci`; Dockerfile/Actions secrets come from `${{ secrets.* }}` not hardcoded `env:`.

**Impact warnings**
- Live secret in repo/history/image → *⚠ may cause immediate credential compromise
  and unbounded billing/abuse.*
- Unpinned remote MCP server with lifecycle scripts → *⚠ may cause rug-pull RCE on
  CI/dev and tool-poisoning exfiltration.*
- Slopsquatted package name → *⚠ may cause attacker-controlled code execution once
  they register the name.*
- Token passthrough → *⚠ may cause downstream token replay.*

**Example findings**
- `src/config/openai.ts:14` — `const KEY = process.env.OPENAI_API_KEY || "sk-proj-…real"`
  ships a live key as a fallback. Fix: remove it; fail fast if unset.
- `.mcp.json:6` — `"command":"npx","args":["-y","some-mcp-tools@latest"]` runs an
  unpinned third-party MCP server with lifecycle scripts. Fix: pin a vetted version,
  run with `--ignore-scripts`, review tool descriptions for hidden instructions.
- `server/oauth.ts:142` — inbound `req.headers.authorization` forwarded verbatim to
  the downstream Notion API (token passthrough). Fix: exchange for an
  audience-scoped downstream token; never relay the client token.

**Severity** — **4:** verified live secret committed/baked into an image; token
passthrough/confused-deputy; unpinned remote MCP server with lifecycle scripts
feeding an auto-executing agent. **3:** floating ranges + no lockfile, or lifecycle
scripts enabled in CI; OAuth/MCP tokens in plaintext; a hallucinated-looking dep
needing verification; tool descriptions injected unsanitized. **2:** missing
`--require-hashes`/`npm ci` on otherwise-pinned deps; secrets read correctly but
debug-logged; non-TLS MCP only in local dev. **0–1:** example/test keys, publishable
client keys, style-only pinning nits.

**False positives** — obvious fake keys in fixtures (`sk-test-…`,
`AKIAIOSFODNN7EXAMPLE`) — verify with `--only-verified`; **publishable** client keys
(Stripe `pk_`, Firebase web `apiKey`, Sentry DSN); floating ranges in a library meant
for publishing; `latest`/unpinned MCP in throwaway local configs not loaded in prod;
env fallbacks to non-credential values (`PORT || 3000`).
