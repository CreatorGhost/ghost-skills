# 06 — AI Code Smells & Authorship Hygiene

Lens 18. The defect fingerprint an LLM agent leaves when it writes a backend feature.
These reproduce across prompts because the model pattern-matches on training data that
optimized for a working demo, not a hostile production. *Escalate one level whenever the
smell sits on an auth, billing, or PII path.*

---

## Lens 18 — AI code smells & artefact leakage

**Catches**
- **Hallucinated packages (slopsquatting risk):** a new import/dependency resolving to no
  real registry entry, or a name 1 edit-distance from a real one (`python-dateutils`,
  `requests-oauth`). USENIX 2025: 19.7% of LLM-suggested packages don't exist; 43%
  reproduce across prompts, so attackers pre-register them.
- **Hallucinated API surface:** a method/kwarg/enum that looks plausible but isn't in the
  installed version (`client.chat.create(...)` vs `client.chat.completions.create`,
  `result.output_text` vs `.content`). Tests pass because the call path is mocked.
- **Happy-path bias:** mishandles empty list, `None`, `0`, negative, single-element,
  duplicate key, unicode, and "the external call returned an error object, not an
  exception" — no branch for the failure shape.
- **Check-then-act / TOCTOU races:** `if not exists(x): create(x)`, `get-or-create`,
  read-modify-write of a counter/balance, `if cache_miss: compute; set` — with no lock,
  `SELECT ... FOR UPDATE`, unique constraint, or atomic upsert.
- **Perf anti-patterns copied from training data:** N+1 (ORM access inside a loop),
  `await` inside a `for` loop where `gather`/`Promise.all` was correct, missing
  `select_related`/`JOIN`, fetch-whole-table-then-filter, `LIMIT`-less queries.
- **Missing-await / floating promise:** an `async` function called without `await` — the
  result is a coroutine/Promise; null-checks pass, errors never surface, ordering breaks.
  Especially in fire-and-forget logging/metrics paths.
- **Fabricated config/secret placeholders shipped as real:** `API_KEY = 'your-api-key-here'`,
  `sk-...`, `https://api.example.com`, `localhost:5432` as prod, a surviving
  `# TODO: replace before prod`.
- **AI-tooling artefact leakage:** `CLAUDE.md`, `.claude/`, `*-plan.md`,
  `implementation-plan.md`, `scratchpad.md`, `Co-Authored-By: Claude/AI`, "Generated with
  Claude Code" tells.
- **Robotic authorship prose:** "Here's the implementation", "This function is responsible
  for", emoji-bulleted summaries, three-part "Created X. Added Y. Updated Z." that reads
  like a chat reply.
- **Hardcoded contributor identity rot:** `# per Arindam's review`, `TODO(mohit)`,
  `author='John Doe'`, fake `@example.com` emails.

**How to scan**
- **Verify every NEW dependency exists.** Diff the manifest
  (`git diff -- package.json requirements*.txt pyproject.toml go.mod`); for each added
  name run `npm view <pkg> version` / `pip index versions <pkg>` (or confirm the lockfile
  resolved it). No registry hit = hallucinated = sev 4. Also grep imports for packages
  absent from the manifest.
- **Pin every NEW SDK call against the INSTALLED version.** `pip show <lib>` / `npm ls <lib>`,
  then confirm the called method/kwarg exists in **that** version. Watch churn: openai
  `ChatCompletion.create`→`chat.completions.create`, pydantic v1 `.dict()`→v2 `.model_dump()`,
  pydantic-ai `result_type`→`output_type`.
- **Happy-path bias** per new function: what does it do on `[]`, `None`, `0`, a missing key,
  and an upstream **error object** (not a raised exception)? Grep `[0]`/`.first()`/`next(`
  without an emptiness guard; `response.json()['key']` without `.get`/`try`.
- **Check-then-act races:** `rg -n 'if not .*exists|get_or_create|\.count\(\).*== 0|balance .*[-+]=|cache.get\(.*\)\n.*cache.set'` — each needs a unique constraint, `ON CONFLICT`/upsert,
  `FOR UPDATE`, or a lock. Bare = sev 3–4 on money/auth/idempotency paths.
- **N+1 / serial-await:** ORM calls inside loops (`for .*:\n.*\.(get|filter|query|find)\(`),
  `for .*:\n.*await ` — recommend a single JOIN/`IN` query or `gather`/`Promise.all` with
  bounded concurrency.
- **Floating promises / missing await:** JS `@typescript-eslint/no-floating-promises`,
  CodeQL `js/missing-await`; Python: calls to known `async def` functions without
  `await`/`create_task`/`gather` — look hard at logging/metrics/notify.
- **Placeholder/fake values as real:** `rg -n 'your-api-key|api-key-here|changeme|REPLACE_ME|TODO.*prod|example\.com|localhost'` in non-test files; live-looking secret shapes.
- **AI artefacts:** `git status --short` and `git diff --cached --name-only` for `CLAUDE.md`,
  `.claude/`, `*-plan.md`, `scratchpad*`; `git log -1 --format=%B | rg -iE 'co-authored-by.*(claude|ai|gpt|copilot)|generated (with|by).*(claude|ai)'`.
- **Robotic prose / name rot:** `rg -iE "Here'?s the|is responsible for|In summary|I'?ve (added|created)|TODO\([a-z]+\)|per .*'s (review|comment)|author\s*=\s*['\"]"`; cross-check names against `git shortlog -sne`/CODEOWNERS (fetched dynamically, never hardcode the list).

**Impact warnings**
- Hallucinated package → *⚠ may cause attacker-controlled code execution once they register
  the name (slopsquatting supply-chain).*
- Hallucinated API on a money/auth path → *⚠ may cause a runtime crash or data corruption on
  the first real call.*
- Check-then-act on a balance → *⚠ may cause a double-spend race under concurrency.*
- Live-looking placeholder secret → *⚠ may cause a broken/leaked credential to ship as prod
  config.*

**Example findings**
- `services/billing.py:88` — `import stripe_helpers` resolves to no PyPI package (nearest
  real is `stripe`); tests mock it. Fix: use the real `stripe` SDK and delete the fabricated
  import. *(sev 4 — supply-chain)*
- `agents/llm.py:42` — `client.chat.create(...)`; `openai==1.x` exposes
  `client.chat.completions.create`. AttributeError on first real call. Fix: correct the call.
  *(sev 4)*
- `api/wallet.py:67` — `bal = get_balance(uid); set_balance(uid, bal - amt)` (read-modify-
  write, no lock) double-spends under concurrency. Fix: `UPDATE wallets SET balance = balance
  - :amt WHERE id=:uid AND balance >= :amt` in one statement and check rowcount. *(sev 4)*
- `routes/orders.py:120` — `for o in orders: o.customer = db.get(Customer, o.cust_id)` (N+1,
  101 queries for 100 orders). Fix: one `WHERE cust_id IN (...)` / `select_related`. *(sev 3)*
- repo root — `implementation-plan.md` and a `Co-Authored-By: Claude` line in HEAD's commit
  are staged. Fix: delete the plan file (gitignore) and amend the trailer out. *(sev 2; sev 3
  if the team strips AI attribution by policy)*

**Severity** — **4:** a hallucinated package name an attacker can register; a hallucinated API
on a money/auth/data path that throws or corrupts on first call; a check-then-act race on
balances/idempotency/uniqueness; a live-looking placeholder secret shipped as prod config.
**3:** N+1/serial-await perf cliff; missing-await dropping a side effect; happy-path bias
mishandling empty/null on a user-facing path; AI artefact leakage when the team strips AI
attribution by policy. **2:** non-prod placeholders, robotic prose, plan/scratch files in the
tree, hardcoded contributor names — cosmetic unless compliance/IP optics matter. **1:**
stylistic AI tells in comments. *Escalate one level on an auth/billing/PII path.*

**False positives** — a "nonexistent" package that is a private/internal/monorepo-workspace or
git/URL dependency (check the lockfile/workspace/private registry); an API matching a **newer**
SDK than your memory (verify against the lockfile-pinned version); placeholders in test
fixtures/`README`/`.env.example`/seed scripts; `localhost`/`example.com` in tests/compose/dev
defaults behind an env check; serial `await` where each iteration genuinely depends on the
previous; robotic prose in auto-generated files (OpenAPI clients, protobuf stubs, migrations);
`Co-Authored-By`/`CLAUDE.md` when the team's policy explicitly permits AI attribution (then
informational, not a defect).
