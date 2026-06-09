# 03 — Coverage Checklist

A fill-in checklist to run against **any** change before you call it tested. It is not
about a coverage *percentage* — line coverage that asserts nothing is exactly the
theater this skill kills. It's about whether the cases that actually break in
production are exercised **and asserted against the real contract**. Copy it, tick the
boxes that apply, and justify any you skip.

Mark each box: `[x]` covered · `[ ]` gap · `[N/A]` not applicable (say why).

---

## 0a. Change-type → required test layers *(do this BEFORE writing tests)*

Different change types break in different layers. Pick the row(s) that match what
you're shipping and treat the listed layers as the **floor** — anything below is
shipping unseen. Skipped layers must be **named in the PR description** (gate (i)
in `04-verification-gate.md`), never silently omitted (**Skipped Layer** smell).

| Change type | Required test layer(s) | What "real" means here |
|---|---|---|
| **Pure-logic function** (no I/O, no LLM) | unit | the actual exported function, not a copy |
| **Function that hits DB / file / external API** | unit + integration | real DB (testcontainers/dev), real or recorded API |
| **Wire-shape change** (Pydantic / TS type / JSON Schema) | unit + contract round-trip | one test serialises in service A and deserialises in service B |
| **Prompt edit** (`*.yaml`, system prompt, agent instruction) | unit + **real-LLM eval, N ≥ 3** | the real MaaS / cloud model, not a mocked LLM. Paste outputs in PR |
| **Frontend component / hook / page / route** | unit + **real-browser session** | dev server up, click the feature, screenshot/video OR a Playwright run |
| **Size / threshold / cap / quota** | unit + **measurement on realistic fixture** | a test that produces the actual byte/ms/count number and asserts headroom |
| **Security guard** (redaction, escape, auth, CSRF, rate-limit) | one test per attack-surface the comment claims to defend | fixture matches the attack scenario in the comment, not an adjacent one (**Comment-vs-Test Drift**) |
| **Schema / migration** | unit + round-trip on **old persisted rows** | a real DB migrated from an old snapshot, not a fresh schema |
| **Deployment / build config** (Dockerfile, helm, CI) | smoke test in the **shipped image** | grep the built artifact for the change; run `--version` against the image |
| **Observability change** (log field, trace tag, metric) | assert the field **appears in real output** | hit the route, scrape the log line / trace, grep for the field |

Quick gut-check: if the row says "real-browser session" and you didn't open a
browser, you haven't tested it yet — write down "UI not verified, reason: …" and
move on with eyes open. The skill prefers an honest **unverified** to a silent
**untested**.

---

## 0. Contract gate (do this first)
- [ ] I can state the **observable contract** in one line: `input → required output/effect`.
- [ ] The expected value is derived from the **spec or the real dependency**, NOT from
      my head or the code's current output (avoid *Shared Assumption*).
- [ ] The test **invokes the real shipped artifact** (exported fn / endpoint / binary),
      not a reconstruction of what it should produce (the cardinal rule).
- [ ] Every assertion checks a **value/effect**, not liveness (`200`/"no throw"/truthy).
- [ ] Each new test was **seen to go red** on the broken code (red-before-green).

## 1. Happy path
- [ ] Typical, valid input produces the **correct value** (not just "a value").
- [ ] The primary side effect actually occurred (row written, event emitted, file
      created, message sent) — asserted by reading the effect back.

## 2. Edges
- [ ] **Empty** input: `[]`, `""`, `{}`, no rows, zero items.
- [ ] **Single** element (off-by-one boundary at the bottom).
- [ ] **Many / large** input (and `N` inputs → exactly `N` outputs).
- [ ] **Null / missing / undefined** field where optional; **absent** key.
- [ ] **Zero, negative, max int, min int**, fractional where numeric.
- [ ] **Duplicate** keys/items; **unordered** input where order matters.

## 3. Negatives & error paths
- [ ] **Invalid / malformed** input is **rejected** with the right error (not silently
      coerced or defaulted).
- [ ] Each `throw`/error branch is reached and asserts the **error type + message
      contract** consumers depend on.
- [ ] The **unhappy path** of every external call: dependency returns an **error
      object** (not an exception), times out, returns partial/empty.
- [ ] Authorization/permission denial returns the right code AND **does not leak** the
      protected data.

## 4. Boundaries & limits *(a real bug hid here — an upload just over the cap)*
- [ ] For each limit (size, length, count, rate, quota, pagination): test **at the
      limit, just under, and just over**.
- [ ] Over-the-limit input is **rejected** with the correct status/error — actually
      exercised, not assumed.
- [ ] Truncation / pagination boundaries: last page, page past the end, page size of 1.
- [ ] Time boundaries: expiry exactly at `t`, just before, just after.

## 5. Encodings & i18n
- [ ] **Non-ASCII / non-Latin** input (CJK, RTL, emoji, combining marks) round-trips
      with the **correct script/encoding** in the output.
- [ ] Wrong/unexpected charset or `Content-Type` is handled, not silently mangled.
- [ ] Locale-sensitive formatting (numbers, dates, currency, collation) matches the
      spec, not the dev's locale.
- [ ] Translation/transform actually **transforms** (a no-op pass-through is a bug:
      assert the output differs in the expected way, not that it "returned something").

## 6. Concurrency & idempotency
- [ ] Same operation run **twice** (retry/double-submit) produces **one** effect, not
      two (idempotency key / unique constraint / upsert).
- [ ] Concurrent writers to shared state don't lose updates (race exercised or guarded
      by constraint/lock — assert the final value).
- [ ] Check-then-act paths (`get-or-create`, balance read-modify-write) tested under
      contention or proven atomic.
- [ ] Order-independence where claimed; ordering preserved where required.

## 7. External-dependency contract *(mocks lie — pin them to reality)*
- [ ] At least **one contract / real-I/O test** hits the real or a **faithfully
      recorded** dependency end-to-end through the actual pipeline.
- [ ] Mocks/stubs are **validated against** the recorded real interaction (re-record on
      dependency change so drift surfaces as a diff).
- [ ] The dependency's **error and rate-limit** responses are covered (429, 5xx,
      malformed body, schema change), not just its success shape.
- [ ] Schema/contract drift between producer and consumer is caught (field added/
      renamed, optionality flipped, type changed).

## 8. Silent-failure hunt
- [ ] Every swallowed error / fallback / retry path: assert the **effect of the real
      path** AND that the **failure/fallback path did NOT fire** (spy/counter == 0).
- [ ] Prefer asserting the **absence** of the error/retry signal over the presence of a
      success marker (success logs can be suppressed by log level).
- [ ] `success: false` / error body returned with a 2xx status is treated as a failure
      by the test (and ideally by the code).
- [ ] Empty result is distinguished from failed result ("no data" ≠ "the call broke").

## 9. Performance & resource caps *(behavioral, not micro-profiling)*
- [ ] No N+1 / serial-await where a batched query/`gather` is required (assert query
      count or wall-clock budget if it's part of the contract).
- [ ] Size/recursion caps fire **before** the expensive work, not after.
- [ ] Timeouts/deadlines exist and are exercised (the slow-dependency case).

## 10. State & data integrity
- [ ] Multi-write operations roll back fully on partial failure (assert no orphaned
      rows).
- [ ] Timezone/`datetime` round-trips without drift (aware vs naive); fixtures aren't
      secretly naive while prod sends UTC.
- [ ] Migrations applied/round-trip; old persisted rows still deserialize.

## 11. Shipped-artifact & telemetry gate
- [ ] The fix is present in the **built bundle / deployed image** (grepped), not just
      source (avoid *Stale Artifact*).
- [ ] Deployed version/SHA matches HEAD.
- [ ] Real-run **logs/metrics** on the affected path show **zero new errors** after the
      change.

## 12. Suite strength
- [ ] No tautology / no-assertion / silently-skipped tests in the suite for this change.
- [ ] (If available) **mutation testing** kills the mutants on the changed code — any
      surviving mutant is an untested behavior; close it.

---

### Sign-off line
> Covered: <list>. Skipped (with reason): <list>. Real-I/O/contract test:
> <which one>. Saw-red: <yes/which tests>. Shipped+telemetry verified: <yes/no>.
