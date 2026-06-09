# 05 — Case Studies (sanitized)

Four generalized, domain-neutral war-stories. Each is a real *shape* of failure,
abstracted away from any specific app, language, or product. Read them as cautionary
patterns: in every one, the suite was **green** while the behavior was **wrong**, and
in every one a single principle from this skill would have turned the test red.

Each case: **Setup → What shipped → Why the suite stayed green → The smell → The test
that would have caught it → Lesson.**

---

## Case A — The Reconstructed Schema (the green-but-broken day)

**Setup.** A service builds a request to a downstream provider and sends it. A required
parameter tells the provider how to process the input.

**What shipped.** The request-builder omitted (or mis-set) that parameter. Every real
call to the provider came back unprocessed — the feature was **100% broken for a full
day**.

**Why the suite stayed green.** The "test" **rebuilt the request payload by hand inside
the test** — and built it *correctly*, including the parameter. It asserted on its own
dict. The real `build_request()` was **never called**, so its bug was invisible.

**The smell.** *Reconstructed Payload* + *Liveness-Only* (a sibling test only checked
`status == 200`, which the provider returns even for an unprocessed input).

**The test that would have caught it.**
```text
req = service.build_request(input)        # the REAL builder, not a copy
assert req["process_mode"] == "expected"  # the param the shipped code dropped → RED
# end-to-end:
out = service.run(non_default_input)
assert out.was_processed and out.value == spec_expected_value   # content contract
```

**Lesson.** Invoke the real artifact and assert the **content** contract. The day-long
outage was sitting in the server logs the whole time — telemetry (gate f) would also
have caught it immediately.

---

## Case B — The Retry That Masked a Dropped Parameter

**Setup.** A client calls a flaky upstream and retries on failure. A recent change
dropped a field from the outbound call, which the upstream rejects with a 4xx.

**What shipped.** The first attempt failed (bad request), the retry logic kicked in,
and on a later attempt a **cached/default** response was returned and treated as
success. Users silently got stale/default data.

**Why the suite stayed green.** The test asserted only the **happy return value**,
which the fallback supplied. It never asserted that the *primary* call succeeded or
that the retry/fallback path stayed cold.

**The smell.** *Swallowed Failure* (retry-then-succeed) + *Liveness-Only*.

**The test that would have caught it.**
```text
with spy(client.fallback) as fb, spy(client.retry) as rt:
    result = client.fetch(args)
assert result == recorded_primary_value   # the real path's value
assert rt.calls == 0                       # retry did NOT fire
assert fb.calls == 0                       # fallback did NOT fire
```

**Lesson.** When code retries or falls back, assert the **effect of the real path** AND
that the **failure path did not fire**. Assert the *absence* of the retry/fallback
signal, not just the presence of a value.

---

## Case C — The Swallowed Exception → Silent Wrong Output

**Setup.** A transform parses an upstream response and extracts a field. The parse is
wrapped in `try/except` that, on error, returns an empty/default object so the request
"never fails."

**What shipped.** The upstream changed its response shape. The parse threw, the
`except` swallowed it, and the function returned the **default** — a confident,
valid-looking, **wrong** answer. No error surfaced anywhere.

**Why the suite stayed green.** Tests fed the *old* shape (via a mock that mirrored the
dev's mental model), so the parse never threw in tests. The error branch — the one that
actually ran in prod — was never exercised. A hard failure had been turned into silent
wrong output.

**The smell.** *Mock Mirrors The Bug* + *Swallowed Failure* + *Untested Boundary*
(the new/malformed shape was never tested).

**The test that would have caught it.**
```text
# contract test against the REAL/recorded upstream shape
resp = recorded_real_response()           # captured from the actual dependency
out = transform(resp)
assert out.field == expected_from_spec    # real shape, correct extraction
# negative: malformed input must FAIL LOUD, not default-and-continue
with expect_error(ParseError):
    transform(malformed_response)
assert default_counter == 0               # the default path did not fire
```

**Lesson.** A `try/except`-to-default converts crashes into invisible corruption. Pin
the mock to a recorded real response (gate d), test the malformed/changed shape, and
assert the swallow-path **never runs** (gate g).

---

## Case D — The Size Limit Nobody Tested

**Setup.** An endpoint accepts uploads with a maximum size. The size check exists in
the code.

**What shipped.** The cap was off by a factor (or applied after a transform that
inflated the payload), so any upload **just over the real-world size** was rejected —
or worse, accepted and then truncated, corrupting data. Typical small test files were
fine.

**Why the suite stayed green.** Every test used a **small** file (well under the cap).
The boundary — at, just under, just over — was never exercised. The happy path passed
forever while real users with real (large) files failed every time.

**The smell.** *Untested Boundary / Limit*.

**The test that would have caught it.**
```text
assert upload(file_just_under_cap).accepted          # boundary − 1
assert upload(file_at_cap).accepted                  # boundary
assert upload(file_just_over_cap).rejected_with(413) # boundary + 1  → RED
assert stored_bytes(file_at_cap) == file_at_cap.size # not truncated (content contract)
```

**Lesson.** For **every** limit, test **at / under / over**. The over-the-limit case
is where the real bug lives, and it's the case a happy-path suite never writes.

---

## The through-line

In all four, the green tick proved only that *a test ran* — not that the *feature
works*. Each was caught by one principle:

| Case | Failing principle | The fix in one line |
|------|-------------------|---------------------|
| A | Test a copy, not the artifact; assert liveness | Call the real builder; assert the content contract |
| B | Retry masks the failure | Assert the real path's value + retry/fallback did not fire |
| C | Mock mirrors a stale shape; swallow hides the error | Contract-test the real shape; assert malformed fails loud |
| D | Boundary never exercised | Test at / under / over every limit |

A test's only job is to **fail when the behavior is wrong**. If it can't fail, it's a
lie — no matter how green the suite.
