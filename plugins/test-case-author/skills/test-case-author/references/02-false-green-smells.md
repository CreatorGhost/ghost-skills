# 02 — False-Green Smells

A catalogue of the patterns that make a test **pass while the code is broken**. For
each: the **smell**, **why it lies**, a **generalized example** (the passing-but-
useless version → the bug-catching version), and the **fix**. These are the named
failure modes from a real green-but-broken-in-prod incident, generalized into
durable, cross-stack principles. When you spot one, treat the test as *not catching
bugs* until corrected — the green tick is not evidence.

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

## Quick triage

When a suite is green but you don't trust it, scan in this order — these catch the
most green-but-broken bugs fastest:

1. **Reconstructed Payload** — does any test rebuild what the code should produce? Is
   the real exported symbol actually called?
2. **Liveness-Only** — does every assertion check a *value/effect*, or just status/
   shape/non-null?
3. **Never-Red** — was each regression test ever seen to fail on the broken code?
4. **Untested Boundary** — are limits/encodings/empties/over-the-cap covered?
5. **Mock Mirrors The Bug** — is there ≥1 contract/real-I/O test at the boundary?
6. **Swallowed Failure** — does the code hide errors, and do tests assert the failure
   path did *not* fire?
7. **Stale Artifact** — is the fix in the *shipped* build and confirmed in telemetry?
