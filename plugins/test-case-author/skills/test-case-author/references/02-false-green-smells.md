# 02 — False-Green Smells

A catalogue of **16 patterns** that make a test (or whole PR) **pass while the code
is broken**. For each: the **smell**, **why it lies**, a **generalized example**
(the passing-but-useless version → the bug-catching version), and the **fix**.
These are the named failure modes from real green-but-broken-in-prod incidents,
generalized into durable, cross-stack principles. When you spot one, treat the
test as *not catching bugs* until corrected — the green tick is not evidence.

The first 11 are about the test itself; **12–16** are about the *envelope around
the test*: the layer that wasn't tested at all, the prompt that was never run
against a real model, the UI that was never opened in a browser, the comment that
doesn't match the test fixture, and the empirical claim with no measurement
behind it. They are the ones that catch shipping-without-actually-testing.

---

## 1. Reconstructed Payload *(the cardinal sin)*

**Smell.** The test hand-builds the artifact the code is supposed to produce — the
request body, payload, schema, SQL, serialized message, config — and builds it
**correctly**, then asserts on its own copy. The function/endpoint under test is
never executed.

**Why it lies.** You wrote a second, correct implementation and tested *that*. The
shipped code can build the artifact completely wrong and the suite never notices,
because the buggy code path never runs.

**Generalized example.**
```text
# LIES — never calls the code that ships
def test_translation_request():
    payload = {"q": text, "source": "auto", "target": "en"}   # rebuilt by the test
    assert payload["target"] == "en"                           # asserts the test's own dict

# CATCHES — invokes the real builder, asserts what it produced
def test_translation_request():
    req = translator.build_request(text)     # the actual exported function
    assert req["target"] == "en"             # shipped code forgot this → RED
```

**Fix.** Import and call the real exported symbol / hit the real route / run the
real binary. Assert on the object *the code produced*, not one you typed. If you're
re-typing the structure the code owns, stop.

---

## 2. Liveness-Only Assertion

**Smell.** The assertion checks that *something happened*, not that the *right thing*
happened: `status == 200`, "did not throw", "returned non-null/truthy", "response
length > 0", "the array is not empty".

**Why it lies.** The wire being up says nothing about correctness. A handler can
return `200` with an empty body, the wrong language, a default value, or another
user's data. "Didn't throw" is satisfied by a function that silently returns garbage.

**Generalized example.**
```text
# LIES
resp = api.translate("Bonjour")
assert resp.status == 200
assert resp.body is not None

# CATCHES — assert the semantic contract
resp = api.translate("Bonjour")
assert resp.status == 200
assert resp.text == "Hello"                 # correct value
assert detect_script(resp.text) == "Latin" # right script/encoding
assert resp.source_lang == "fr"            # field populated correctly
```

**Fix.** Assert the actual guarantee: the value is correct; a non-English input
comes back translated in the right script; N inputs → N outputs; the owner/tenant
field is populated; the row was persisted. Status/shape checks are a *precondition*,
never the whole assertion.

---

## 3. Never-Red

**Smell.** The test was written *after* the fix and **never observed to fail** on the
broken code. It's assumed to guard the bug.

**Why it lies.** A test you never saw go red might assert the wrong thing, target the
wrong path, or be silently skipped — and pass anyway. Green tells you the test ran,
not that it *can* fail.

**Generalized example.** A regression test added alongside a fix asserts
`result.count == 3`, but the function already returned `3` for an unrelated reason;
the actual bug was in `result.items[2].owner`. The test is green on both broken and
fixed code → it guards nothing.

**Fix.** Red-before-green. Revert or sabotage the fix, run the test, **confirm it
fails for the right reason**, restore the fix, confirm green. For TDD, write the
failing test first. A test that can't be shown to fail is not a test.

---

## 4. Swallowed Failure

**Smell.** The code under test hides errors — `try/catch` that continues,
fallback-to-default, retry-then-succeed, `.catch(() => [])`, `except: pass` — and the
test only checks the happy return value.

**Why it lies.** The failure path produces a *plausible* value (empty list, default,
stale cache, canned answer), so the happy-path assertion passes while the real
operation silently failed. A success *log* can also be suppressed by log level, so
"saw the success line" is not proof either.

**Generalized example.**
```text
# Code: on error, quietly falls back
def get_rate():
    try:    return live_rate()
    except: return 1.0          # silent default

# LIES — passes whether or not live_rate() blew up
assert get_rate() > 0

# CATCHES — assert the effect AND that the fallback did NOT fire
with no_fallback_allowed():            # spy/flag on the fallback branch
    rate = get_rate()
assert rate == recorded_live_rate      # real value, not the default
assert fallback_counter.value == 0     # the failure path did not run
```

**Fix.** Assert the *effect* of the real path, and **assert the failure/fallback path
did NOT fire** (spy the fallback branch, assert a retry counter is 0, assert the
error metric didn't increment). Prefer asserting the **absence** of the
error/retry/fallback signal over the presence of a success marker.

---

## 5. Mock Mirrors The Bug

**Smell.** A mock/stub returns what *you think* the dependency returns. Your mental
model is wrong, so the mock and the code agree — and both are wrong.

**Why it lies.** Doubles encode *your* assumptions about the boundary. If the real
API returns `{ "data": {...} }` but your mock returns `{...}`, the code that reads
`resp.data` passes against the mock and crashes in prod (or vice versa). The mock
can also drift after the dependency changes.

**Generalized example.** Mock the payment API to return `{"status": "ok"}`. The real
API returns `{"result": {"status": "succeeded"}}`. Code reads `resp["status"]` →
green against the mock, `KeyError`/wrong-branch in prod.

**Fix.** Add at least one **contract test** against the real or a faithfully recorded
interaction (VCR cassette, captured fixture, Pact). Re-record when the dependency
changes so drift shows up as a diff. Mock for breadth; contract-test for truth.

---

## 6. Untested Boundary / Limit

**Smell.** Only typical inputs are tested. Size caps, off-by-one counts, encodings,
empty/oversized/malformed inputs, and limits are never exercised.

**Why it lies.** Reality diverges from your mental model precisely at the edges. A
real bug: an upload **just over a size cap** that was never tested — the happy-path
test (small file) passes forever while every real (large) upload fails.

**Generalized example.**
```text
# Only the comfortable case is tested
assert upload(small_file).ok

# Missing — the boundary that actually breaks in prod
assert upload(file_at_limit).ok
assert upload(file_over_limit).rejected_with(413)   # never tested → ships broken
```

**Fix.** For every limit, test **at, just under, and just over** it. Add empty,
single, max, over-max, wrong-encoding, malformed, and off-by-one cases. See
`references/03-coverage-checklist.md`.

---

## 7. Shared Assumption (test and code share the same wrong head)

**Smell.** The expected value in the test is derived from the same (wrong) mental
model that produced the bug — often literally pasted from the code's own output.

**Why it lies.** If the code computes `0.1 + 0.2 == 0.30000000000000004` and you copy
that into the assertion, the test enshrines the bug as "correct." Test and code agree
because they share an author and an error.

**Generalized example.** A date-formatting bug emits `2026-13-01` (month overflow);
the dev copies actual output into the expected value. Test green, dates wrong.

**Fix.** Derive the expectation from the **spec or the real dependency**, not from
your head or the code's current output. For math, compute the expected value by an
independent method. For formats, cite the standard. **Don't let the test and the code
share the same wrong assumption.**

---

## 8. Stale Artifact

**Smell.** The fix is confirmed *in source*, but the running system serves an old
**built bundle / deployed image / cached layer**. Source-level tests pass; prod runs
yesterday's code.

**Why it lies.** Source ≠ shipped. A successful unit test on `src/` says nothing about
the minified bundle, the Docker image actually deployed, a CDN-cached asset, or a
lambda that wasn't re-published.

**Generalized example.** A header fix lands in `src/api.ts`; tests green; the
production bundle `dist/api.[hash].js` still contains the old header because the build
step was skipped in the deploy.

**Fix.** **Grep the shipped artifact** for the change: search the built bundle /
deployed image / running config, not just source. Confirm the deployed version/SHA
matches HEAD. Then check telemetry (smell ties into the verification gate).

---

## 9. Implementation-Coupled

**Smell.** The test asserts internals — private method calls, call counts, field
order, a specific SQL string — rather than observable behavior. Or it mocks the very
internal that contains the bug.

**Why it lies.** Two failure directions: (a) a harmless refactor turns it red (noise →
the suite gets ignored), and (b) by mocking the internal, the real bug in that
internal slips through untested.

**Generalized example.** `assert repo.save.call_count == 1` passes while the saved
*row* is wrong. Or mocking the query builder hides that the builder emits invalid SQL.

**Fix.** Assert the observable outcome through the **public entry point** (the
persisted row, the response body, the emitted event). Combine with the cardinal rule:
the public entry point must be the *real shipped* one.

---

## 10. Tautology / Vacuous Test

**Smell.** A test with no real assertion: `assert x == x`, `assert true`, a test body
that only sets up and never asserts, a permanently `skip`/`pending`/`xfail` test, or
an assertion inside a callback that never runs.

**Why it lies.** It contributes a green tick and coverage while verifying nothing. A
skipped test looks like protection but guards nothing.

**Generalized example.**
```text
it("formats the date")   # body: const d = format(x);  — no expect() at all
it.skip("rejects oversized upload", ...)   # quietly disabled, still "in the suite"
```

**Fix.** Every test asserts a real, **independently-derived** expectation. Ban
no-assertion tests and silently-skipped tests in CI (most runners can fail on empty
assertions / report skips). Mutation testing surfaces these as surviving mutants.

---

## 11. Frozen-Time / Nondeterminism Mask *(supporting smell)*

**Smell.** Flaky tests are "fixed" by loosening assertions, adding sleeps, retrying
until green, or over-freezing time/randomness so the real timing/ordering bug is
hidden.

**Why it lies.** The bug (race, tz handling, ordering) is real; the test was changed
to stop reporting it. Retry-until-green is the test-side twin of Swallowed Failure.

**Fix.** Make the *system* deterministic (inject the clock, control the seed, await
real signals instead of sleeping), then assert the exact value. If a test is flaky
because the code is racy, that's a bug to fix, not an assertion to soften.

---

## 12. Skipped Layer *(silent layer skip)*

**Smell.** The change crosses N pipeline layers — e.g. a frontend hook → API client
→ wire shape → backend route → service → DB — but the tests cover M < N of them.
The skipped layers are never named in the PR description; the green tick implies
"tested" when it actually means "tested *somewhere*".

**Why it lies.** Each layer has its own failure modes. A function can be perfectly
unit-tested while its caller integrates it wrong, the wire shape it produces doesn't
match what the consumer expects, or the dev server never started so the UI is
shipped unseen. The unit-test green says nothing about the layers that were never
exercised.

**Generalized example.**
```text
# A change adds a new field to a request body.
# Backend: Pydantic model has a unit test confirming the field validates.    ✅
# Frontend: TS interface has a build error if the field is wrong.            ✅
# Wire:    no test round-trips a real request through the route.             ❌ silent skip
#
# The field name was mis-cased (page_context vs pageContext).
# Backend unit test green. Frontend types green. Every real call broken.
```

**Fix.** For every change, enumerate the layers it crosses (logic, wiring, wire
shape, dependency I/O, UI, deployment) and tick each. Any layer that genuinely
can't be exercised in this PR must be **declared skipped with a reason** in the PR
description — never silently omitted. See the **change-type → required-layers
matrix** in `references/03-coverage-checklist.md` and gate **(h)** in
`references/04-verification-gate.md`.

---

## 13. Prompt-Without-Eval

**Smell.** A prompt file (`*.yaml`, `*.txt`, a `system_prompt` string, an agent
instruction block) is edited. The surrounding tests mock the LLM call. No real
model was invoked with the new prompt before the change shipped.

**Why it lies.** A prompt **is code** — it instructs the model to behave a specific
way. Mocked tests prove the orchestration around the LLM works; they prove **nothing**
about whether the model actually follows the new instructions. Prompt regressions
(model ignores a rule, hallucinates a new shape, leaks a value the prompt said to
redact, stops calling a required tool) are exactly the bugs a mocked suite can never
catch.

**Generalized example.**
```text
# system_prompt is updated to add:
#   "Treat fields whose value is `***` as redacted secrets.
#    Never echo them back to the user."
#
# All unit tests mock the LLM response → green.
# Real production model ignores the instruction ~30% of the time and
# echoes the redacted token. No test could have caught this without a
# real-model call.
```

**Fix.** For any prompt edit, run the change against the **real model** on at least
3 canonical cases (a golden question, the exact case the change targets, and at
least one adversarial input). Paste the model's outputs into the PR description.
If no eval rig exists in the repo, mark the change **prompt behaviour unverified**
— a flag a reviewer can accept or reject. A prompt PR with no real-model evidence
is not "tested".

---

## 14. UI-Without-Browser

**Smell.** A frontend component, hook, page, route, or stylesheet is changed. The
change ships without anyone starting the dev server, running an E2E test, or
recording a screenshot/video of the new behaviour. The "tests pass" tick covers a
render tree or a typed interface — not a rendered page in a real browser.

**Why it lies.** Unit-rendered components don't catch hydration mismatches, SSR
warnings, layout collisions, accessibility regressions, focus traps, animation
glitches, or the way the change interacts with router/state/animation under
concurrent rendering. Type-checks don't catch any of those either.

**Generalized example.**
```text
# A hook is swapped from useLayoutEffect to useEffect to avoid an SSR warning.
#   - TypeScript compiles cleanly       ✅
#   - Component render test passes      ✅
#   - No browser was opened             ❌
#
# The original useLayoutEffect was guarding against state writes from
# aborted concurrent renders. The new useEffect timing introduces a
# zombie registration when the parent unmounts mid-transition.
# Never reproduced; never caught.
```

**Fix.** For any UI/frontend change, either (a) start the dev server, click through
the changed feature, and attach a screenshot or short video to the PR, or (b) run a
Playwright/Cypress test that drives the change in a real browser. If neither is
possible in the current environment, mark the change **UI not verified in this PR
because <reason>** in the PR description — explicit, not silent. A reviewer can
accept that disclosure; they can't accept what they don't know about.

---

## 15. Comment-vs-Test Drift

**Smell.** A code comment / docstring claims the function defends against scenario
X — "DoS guard against pathological nested dicts", "prompt-injection defense via
XML escape", "rate-limits hot tenants", "constant-time string compare to prevent
timing attacks". The test that's supposed to prove it exercises a **different**
scenario that happens to cross the same threshold incidentally.

**Why it lies.** Tests pass for the wrong reason. The promised defense was never
proven; only an adjacent property was checked. When the actual attack/condition
hits, the code may or may not behave as the comment claims — but the test had no
way to know. Worse, the comment now reads as evidence ("we have a test for this")
when it isn't.

**Generalized example.**
```text
# Code comment:
#   "DoS guard against pathological nested dicts so a payload like
#    {a: {a: {a: ...}}} can't burn CPU in the redactor before the
#    byte-size cap would have caught it."

# Implementation:
def enforce(ctx):
    if len(json.dumps(ctx)) > RAW_MAX: raise HTTP(413)

# Test:
def test_rejects_oversized_payload():
    ctx = {"blob": "x" * (RAW_MAX + 1)}   # WIDE, not deep
    with pytest.raises(HTTP) as e: enforce(ctx)
    assert e.value.status == 413           # green for the wrong reason

# A 31 KiB deeply-nested payload (under the byte cap) still reaches the
# redactor — the exact scenario the comment claimed was prevented.
```

**Fix.** Read every "defends against X" / "guards Y" / "prevents Z" comment in the
changed code. Map each claim to a test whose **fixture matches the scenario
described** — not an adjacent one. If the comment says "deeply nested", the fixture
is deeply nested. If the comment says "injection", the fixture contains an
injection payload. If the test and the comment disagree, one of them is wrong;
update whichever is wrong.

---

## 16. Claim Without Measurement

**Smell.** A PR comment, design doc, or code comment makes an empirical claim —
"this fits in ~1 KiB", "the request takes 30 ms", "we never hit the cap in
practice", "users don't load more than 20 of these" — without a measurement script,
fixture, or telemetry query that produces the number.

**Why it lies.** The claim is asserted with the authority of a measurement but is
actually an estimate from intuition. Reviewers (and future-you) read it as evidence;
it isn't. Worse, if the number is wrong, no one will catch the gap because there
is no test that would surface a regression.

**Generalized example.**
```text
# PR description:
#   "Introducing a 16 KiB size cap on the page-context block.
#    The pilot page projection serializes to under 1 KiB, so we have
#    plenty of headroom."
#
# Reality: nobody measured. The number was eyeballed from counting fields.
# Six weeks later a new field is added that pushes the projection past
# 4 KiB; nobody notices until a different page blows the cap.
```

**Fix.** Every empirical claim needs either:
- (a) a test/script committed alongside the claim that **produces the number**
  (e.g. `test_projection_serializes_under_1kib` or a `measure.py` whose output
  is pasted into the PR), or
- (b) an explicit `[estimated, not measured]` tag on the claim so reviewers know
  they're reading a guess.

A bare number without one of those is not allowed to stand. The skill should treat
unmeasured claims in a PR description the same way it treats Liveness-Only
assertions: a green-looking signal that proves nothing.

---

## Quick triage

When a suite is green but you don't trust it, scan in this order — these catch the
most green-but-broken bugs fastest:

1. **Reconstructed Payload** — does any test rebuild what the code should produce? Is
   the real exported symbol actually called?
2. **Liveness-Only** — does every assertion check a *value/effect*, or just status/
   shape/non-null?
3. **Never-Red** — was each regression test ever seen to fail on the broken code?
4. **Skipped Layer** — does the change cross more layers than the tests cover? Is
   any skipped layer declared in the PR?
5. **Untested Boundary** — are limits/encodings/empties/over-the-cap covered?
6. **Comment-vs-Test Drift** — does the test fixture actually match the scenario the
   code comment claims to defend?
7. **Mock Mirrors The Bug** — is there ≥1 contract/real-I/O test at the boundary?
8. **Swallowed Failure** — does the code hide errors, and do tests assert the failure
   path did *not* fire?
9. **Prompt-Without-Eval** — did a prompt change? Was the real model invoked?
10. **UI-Without-Browser** — did UI change? Was the dev server / a browser ever opened?
11. **Claim Without Measurement** — does any empirical claim in the PR have a number
    backed by a script/fixture/telemetry?
12. **Stale Artifact** — is the fix in the *shipped* build and confirmed in telemetry?
