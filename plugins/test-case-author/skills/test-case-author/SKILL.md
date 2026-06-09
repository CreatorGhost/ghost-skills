---
name: test-case-author
description: >-
  Write test cases that ACTUALLY CATCH BUGS — not tests that go green while the
  shipped feature is 100% broken in production. Language- and framework-agnostic.
  Teaches the senior discipline behind a real green-but-broken incident: test the
  REAL artifact (invoke the actual exported function / hit the real endpoint /
  run the shipped binary, never a hand-rebuilt copy of the payload/schema/SQL the
  code is supposed to produce); assert the behavior/content CONTRACT (the value is
  correct, N inputs → N outputs, the field is populated, the script/encoding is
  right), not liveness ("returns 200", "didn't throw"); prove RED before green;
  hunt SILENT failures (swallowed catch, fallback-to-default, retry-and-succeed);
  contract-test the BOUNDARY you don't control (third-party APIs, schemas,
  encodings, model output, size limits); and verify the fix is in the SHIPPED
  build and the production logs. Use when asked to "write tests", "add test
  cases", "write unit/integration/e2e tests", "how should I test this", "did I
  test this right", "why didn't the tests catch this", "the tests pass but it's
  still broken", "is this tested", "make sure this is covered", "TDD", or "write a
  test plan".
when_to_use: >-
  Whenever writing, reviewing, or planning tests for any change in any language or
  framework — unit, integration, contract, or end-to-end; doing TDD; building a
  test plan; closing a coverage gap; or debugging a green-suite-but-broken-feature
  ("why didn't the tests catch this", "tests pass but it's still broken", "is this
  actually tested", "did I test this right", "make sure this is covered").
metadata:
  author: Aditya Pratap Singh
  version: 1.0.0
---

# Test Case Author — tests that actually catch bugs

Write tests whose **only job is to fail when the behavior is wrong**. This skill
encodes a hard-won lesson: a full test suite was **green** while the shipped
feature was **100% broken in production for a day** — because the tests validated
a hand-rebuilt copy of the code instead of the code, and asserted *liveness*
("got a response") instead of the *content contract* ("the response is correct").

> **Philosophy.** A test that cannot fail is a lie. Every test must (1) execute
> the **real shipped artifact**, (2) assert the **semantic contract** (the right
> value/effect), and (3) have been **seen to go red** on the broken code. If any
> of the three is missing, the green tick is theater — it proves the test ran,
> not that the feature works.

## When to use
- Writing tests for a change: *"write tests", "add test cases", "write unit /
  integration / e2e tests", "cover this", "TDD this"*.
- Sanity-checking existing tests: *"did I test this right", "is this actually
  tested", "is this covered", "review my tests"*.
- The damning case: *"the tests pass but it's still broken", "why didn't the
  tests catch this", "green in CI, broken in prod"*.
- Producing a test plan for a feature or risky area.

## The cardinal rule
**Test the real artifact, never a reimplementation.** If you find yourself
re-typing the request body, the schema, the SQL, the JSON, or the algorithm that
the code under test is *supposed* to produce, **stop** — you are testing your own
correct copy while the shipped code builds it wrong, and the function under test
never even runs. Import and call the actual exported symbol; hit the real route;
execute the real binary; read the real built bundle.

## Workflow — for any change, in any stack
1. **Understand the contract.** What is the observable guarantee? Derive the
   expected value from the **spec or the real dependency**, never from your own
   head (the same head that may have written the bug — see *Shared Assumption*).
   Write it down: input → required output/effect.
2. **Classify the change against the layer matrix.** Use the
   *Change-type → required-layers* matrix at the top of
   `references/03-coverage-checklist.md`. UI change? a real browser is required.
   Prompt edit? a real-model eval is required. Wire-shape change? a round-trip
   contract test is required. Any layer you can't exercise in this PR must be
   **declared unverified** in the PR description (avoid *Skipped Layer*).
3. **Write a RED test that reproduces the risk.** Before (or without) the fix,
   run it and **watch it fail for the right reason**. A test you never saw fail
   on the broken code proves nothing — it may assert the wrong thing and pass
   anyway. (Kent Beck: red → green → refactor.)
4. **Drive the real artifact.** Call the actual exported function / real endpoint
   / shipped binary with real (or faithfully recorded) inputs. No reconstructed
   payloads, schemas, or SQL.
5. **Assert the content contract, not liveness.** Assert the *value/effect*: the
   number is right; a non-English input comes back translated in the right
   script; N inputs produce N outputs; the owner/tenant field is populated; the
   row was actually written. "200 / didn't throw / returned something" is not an
   assertion.
6. **Match the test fixture to the comment.** Read every "defends against X" /
   "guards Y" / "prevents Z" claim in the changed code. The test fixture must
   exercise **the exact scenario the comment names** — not an adjacent one that
   happens to cross the same threshold (avoid *Comment-vs-Test Drift*).
7. **Cover the edges, boundaries, and negatives.** Empty, null, single, huge,
   over-the-limit, wrong-language/encoding, malformed, off-by-one counts,
   duplicate, timeout, the unhappy path. Use `references/03-coverage-checklist.md`.
8. **Add at least one real-I/O / contract test at the boundary you don't
   control.** Third-party API, DB, schema, encoding, model output, file/size cap.
   Mocks encode *your* assumptions; if the assumption is wrong, the mock passes
   and prod fails. Use a contract test against the real or a recorded interaction.
9. **Hunt the silent failure.** If the code swallows errors, falls back to a
   default, or retries-then-succeeds, assert the **effect** AND assert the
   **failure/fallback path did NOT fire**. Don't assert only a success marker —
   a success log can be suppressed by log level; assert the *absence* of the
   error/retry/fallback path.
10. **Back every empirical claim with a measurement.** Numbers in the PR
    description ("fits in 1 KiB", "30 ms", "20 items") need a committed script
    or test that produces them, or an explicit `[estimated, not measured]` tag
    (avoid *Claim Without Measurement*).
11. **Verify in the SHIPPED artifact + telemetry.** Confirm the fix is in the
    built bundle / deployed image (grep it), not just in source. Then pull
    real-run **logs/metrics** and assert **zero new errors**. Production telemetry
    is the highest-signal test; synthetic tests complement it, never replace it.

Then run the **verification gate** (`references/04-verification-gate.md`) before
you say "fixed."

## FALSE-GREEN smell list (memorize these)
A test can be green for all the wrong reasons. **16 smells**, fully detailed in
`references/02-false-green-smells.md`. The first 11 are about the test itself;
**12–16** are about the envelope around the test — the layer that wasn't tested,
the prompt that was never run against a real model, the UI that was never opened,
the comment that doesn't match the test fixture, the claim with no measurement.

| Smell | The lie | One-line fix |
|-------|---------|-------------|
| **Reconstructed Payload** | Test rebuilds the request/schema/SQL itself (correctly) — the shipped code builds it wrong but never runs. | Invoke the real exported function/endpoint; assert on what *it* produced. |
| **Liveness-Only Assertion** | Asserts `200` / "no exception" / "truthy" — proves the wire is up, not the answer is right. | Assert the actual value/effect/content contract. |
| **Never-Red** | Test was written after the fix and never seen to fail on broken code. | Revert the fix (or break it), watch the test go red, then restore. |
| **Swallowed Failure** | `try/catch` continues, fallback returns a default, retry hides the error — happy return looks fine. | Assert the effect *and* that the failure/fallback path did not fire. |
| **Mock Mirrors The Bug** | The mock returns what you *think* the dependency returns; reality differs. | One contract test against the real/recorded dependency. |
| **Untested Boundary/Limit** | Size caps, encodings, schemas, off-by-one never exercised. | Add the boundary/negative case (esp. over-the-limit). |
| **Shared Assumption** | Test and code derive the expected value from the same wrong mental model. | Pin the expectation to the spec or the real dependency. |
| **Stale Artifact** | Source is fixed; the deployed bundle/image is old. | Grep the built/deployed artifact for the change. |
| **Implementation-Coupled** | Test asserts internals; refactor breaks it OR a real bug slips through a mocked internal. | Test observable behavior through the public entry point. |
| **Tautology / Vacuous** | `assert x == x`, no-op, or a test with no assertion / a skipped/`pending` test. | Assert a real, derived expectation; ban empty/skipped tests in CI. |
| **Frozen-Time / Nondeterminism Mask** | Flaky tests "fixed" by sleeps/retries/looser asserts; the real race/tz/order bug is just hidden. | Inject the clock/seed/signal; assert the exact value. |
| **Skipped Layer** | Change crosses N layers; tests cover M < N. The silent gap is invisible. | Tick every required layer in the change-type matrix; declare the rest. |
| **Prompt-Without-Eval** | A prompt file was edited; only mocked LLMs ran. The model's actual behaviour is unknown. | Run the real model on ≥3 canonical cases; paste outputs in the PR. |
| **UI-Without-Browser** | A component/hook/page changed; nobody started the dev server. | Open the dev server + click the feature, or run a Playwright test. |
| **Comment-vs-Test Drift** | Code comment promises defense against scenario X; the test exercises scenario Y. | Match the test fixture to the exact scenario named in the comment. |
| **Claim Without Measurement** | "Fits in 1 KiB", "30 ms", "20 items" — asserted with the authority of a measurement but never measured. | Commit a script that produces the number, or tag the claim `[estimated]`. |

If any smell is present, treat the test as **not catching bugs** until it's
fixed — regardless of the green tick.

## References (load for depth)
- `references/01-principles.md` — the testing pyramid; behavior-vs-implementation;
  test-double taxonomy (stub/mock/fake/spy) and when each lies; contract testing;
  red-green-refactor; mutation testing ("test your tests"); Hyrum's Law; the
  cardinal rule.
- `references/02-false-green-smells.md` — the **16-smell** anti-pattern catalogue.
  Smells 1–11 cover bad tests; 12–16 cover the envelope around the test (skipped
  layer, prompt without eval, UI without browser, comment-vs-test drift, claim
  without measurement).
- `references/03-coverage-checklist.md` — a fill-in checklist for any change.
  Leads with the **change-type → required-layers matrix** (pure logic / I/O /
  prompt / UI / wire shape / size cap / security guard / schema migration /
  deployment / observability) and what "real" means for each.
- `references/04-verification-gate.md` — the **nine-gate** "BEFORE you say it's
  fixed" checklist: saw red → real artifact → content contract → real dependency
  once → shipped build → telemetry → failure-path did-not-fire → **required
  layers exercised** → **skipped layers/claims declared**.
- `references/05-case-studies.md` — sanitized war-stories of each smell.
- `references/test-plan-template.md` — the reusable template the skill emits.

## What this skill does NOT do
- It does not pick a framework or runner for you — it works with whatever you
  have (xUnit-family, pytest, Jest/Vitest, Go `testing`, RSpec, JUnit, etc.).
- It is not a coverage-percentage chaser — line coverage that asserts nothing is
  the very theater this skill exists to kill. Use mutation testing to judge a
  suite's real strength.
- It does not replace production observability — it makes tests worthy of being
  *complementary* to it.
