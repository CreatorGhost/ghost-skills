# 01 — Principles: what a test is *for*

A test exists to **fail when the behavior is wrong**. Everything below serves that
one job. If a practice doesn't increase the chance a real bug turns the suite red,
it's decoration. These principles are language- and framework-agnostic; examples
use pseudocode plus a couple of concrete stacks, never one.

---

## The cardinal rule — test the real artifact

**Invoke the actual exported function, the real endpoint, or the shipped binary.
Never test a reimplementation of it.**

The fatal failure mode: the test *rebuilds* the thing the code is supposed to
produce — the request body, the payload, the schema, the SQL, the serialized
message — and builds it **correctly**, then asserts on that. The shipped code
builds it **wrong**, but the code under test is never executed. The suite is
green; production is broken.

```text
# WRONG — tests a copy the app never sends
def test_request():
    body = {"model": "x", "input": text, "lang": "auto"}   # hand-built here
    assert body["lang"] == "auto"                           # asserts your own dict

# RIGHT — tests what the code actually builds
def test_request():
    req = client.build_request(text)        # the real exported function
    assert req.body["lang"] == "auto"        # asserts what SHIPS
```

Heuristic: **if you are re-typing the data/structure/algorithm the code is
responsible for producing, stop** — you have written a second, correct
implementation and are testing *that*. Drive the real one.

---

## The testing pyramid — and what each layer is actually for

Mike Cohn's pyramid (later refined by Martin Fowler): **many fast unit tests, fewer
integration tests, fewest end-to-end tests.** The shape is about *feedback speed and
stability*, not a quota.

| Layer | Scope | Catches | Lies when… |
|-------|-------|---------|-----------|
| **Unit** | One function/module, dependencies doubled | Logic, branches, edge cases | the double encodes a wrong assumption (mock mirrors the bug); the unit isn't the real shipped path |
| **Integration** | Several real components wired together (real DB, real serializer) | Wiring, schema/contract drift, transactions, config | the boundary it spans is still mocked at the critical edge |
| **End-to-end / system** | The whole pipeline through the real entry point | "Does the actual product do the thing?" | slow/flaky, so it's skipped — and that's exactly where the green-but-broken bug hid |

The incident's lesson: a pyramid made entirely of unit tests with mocked
boundaries can be 100% green while the feature is 100% broken. **At least one test
must drive real I/O end-to-end through the actual pipeline.** The pyramid says
"fewest," not "zero." (Some teams prefer the "testing trophy" — heavier on
integration — for I/O-bound apps; the principle is the same: cover the real seams.)

---

## Behavior, not implementation — balanced against the cardinal rule

Test the **observable contract**, not the internal mechanics, so the suite
survives refactors yet still catches real breakage.

- **Implementation-coupled (brittle + blind):** asserts private method calls,
  internal field order, the number of times a helper ran. A refactor reddens it
  for no reason; worse, a *mocked* internal lets a real bug slip past.
- **Behavioral (durable + sharp):** asserts what a caller can observe — return
  value, persisted row, emitted event, HTTP response body, file written.

The balance with the cardinal rule: **drive the public entry point** (behavior),
but make sure that entry point is the *real shipped one* (artifact). Behavior +
real-artifact together = a test that's both refactor-proof and bug-catching.

---

## Test-double taxonomy — and exactly when each one lies

(Per Gerard Meszaros / Martin Fowler's "Mocks Aren't Stubs".)

| Double | What it is | Legit use | How it lies |
|--------|-----------|-----------|-------------|
| **Dummy** | Filler passed but unused | Satisfy a signature | — |
| **Stub** | Returns canned answers | Drive a code path | Canned answer ≠ what the real dependency returns → **Mock Mirrors The Bug** |
| **Spy** | A stub that records calls | Assert an interaction happened | Verifying the call ≠ verifying the *effect*; over-specifies implementation |
| **Mock** | Pre-programmed with expectations, fails if not met | Verify protocol with a collaborator | Verifies *your* expected protocol — if your model of the collaborator is wrong, it passes while prod fails |
| **Fake** | Working but simplified (in-memory DB) | Fast integration-ish tests | The fake's behavior diverges from prod (SQLite vs Postgres semantics, JSON ordering, tz handling) |

**The universal failure mode of all doubles: they encode YOUR assumptions about
the boundary.** If the assumption is wrong, every test built on the double is green
and production is red. Doubles are necessary for speed and isolation — but they
must be *validated* against reality by a contract test (below). Never mock the unit
you're actually testing; mock its collaborators only.

---

## Contract testing — pin your assumptions to reality

A **contract test** verifies that the boundary you don't control behaves the way
your doubles assume. Two flavors:

- **Recorded interaction** (e.g. VCR-style cassettes, golden fixtures): capture a
  real request/response from the dependency once, replay it deterministically.
  Re-record when the dependency changes so drift surfaces as a diff.
- **Consumer-driven contracts** (e.g. Pact): the consumer publishes the shape it
  needs; the provider's CI verifies it still honors that shape. Breaks the build
  on the provider side *before* it breaks your prod.

Rule: **the same assumption that a mock encodes must be checked by at least one
contract or real-I/O test.** Mock for breadth and speed; contract-test for truth.

---

## Red → Green → Refactor (Kent Beck, TDD)

1. **Red:** write a failing test that states the desired behavior. *Run it and
   watch it fail for the right reason.*
2. **Green:** write the minimum code to pass.
3. **Refactor:** clean up with the test as a safety net.

Even when not doing strict TDD, the **red step is non-negotiable**: a test written
*after* a fix that you never saw fail on the broken code is worthless — it may
assert the wrong thing and pass regardless (**Never-Red**). To retrofit: revert or
sabotage the fix, confirm red, restore, confirm green.

---

## Mutation testing — test your tests

Coverage tells you a line *ran*; it says nothing about whether an assertion would
have *caught* a change. **Mutation testing** (Stryker, PIT, mutmut, `cargo-mutants`,
`go-mutesting`) deliberately injects bugs ("mutants" — flip `>` to `>=`, drop a
line, negate a condition) and reruns the suite. A **surviving mutant** is a bug your
tests can't catch — a hole. Mutation score is a far better signal of suite strength
than line coverage, and it directly exposes Liveness-Only and Tautology smells.

---

## Hyrum's Law — your real contract is wider than you think

> "With a sufficient number of users of an API, it does not matter what you promise
> in the contract: all observable behaviors of your system will be depended on by
> somebody." — Hyrum Wright

Implication for tests: the behaviors users *actually* depend on (ordering,
whitespace, error message text, timing, encoding) are part of the de-facto
contract. Test the observable behaviors that matter to consumers — and when you
*intend* to change one, a good test forces you to acknowledge it (a red test is the
system telling you a contract just moved).

---

## Testing in production / observability — the highest-signal test

Synthetic tests are a model of reality; **production telemetry is reality.** Logs,
metrics, traces, and error trackers observe the real system under real inputs and
real dependencies — exactly where synthetic assumptions break. In the incident, the
precise errors sat in the server logs all day while the suite stayed green.

- **Before declaring "fixed," read real-run logs/metrics and assert zero new
  errors** on the affected path.
- Tests **complement** observability; they never replace it. A suite that's green
  while error-rate dashboards are red means the suite is testing the wrong thing.
- Verify the fix is in the **shipped artifact** (built bundle, deployed image), not
  just in source — deploys go stale (**Stale Artifact**).

---

## The three-part gate (memorize)

Every test must satisfy all three or it's theater:

1. **Real artifact** — it executes the shipped code/endpoint/binary, not a copy.
2. **Content contract** — it asserts the right value/effect, not liveness.
3. **Seen red** — it has been observed to fail on the broken code.

Miss #1 → you tested your own correct copy. Miss #2 → you proved the wire is up.
Miss #3 → you don't know the test can fail at all.
