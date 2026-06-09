<h1 align="center">🧪 test-case-author</h1>

<p align="center">
  <strong>Tests that actually catch bugs — not tests that go green while the feature is broken in prod.</strong><br>
  Born from a real incident: a full suite was green for a day while the shipped feature was 100% broken.
</p>

<p align="center">
  <a href="../../README.md">ghost-skills</a> •
  <a href="#install">Install</a> •
  <a href="skills/test-case-author/SKILL.md">SKILL.md</a> •
  <a href="#false-green-smells">Smells</a> •
  <a href="skills/test-case-author/references/test-plan-template.md">Test plan template</a>
</p>

<p align="center">
  <img alt="agnostic" src="https://img.shields.io/badge/language-agnostic-2563eb">
  <img alt="discipline" src="https://img.shields.io/badge/red%E2%86%92green%E2%86%92refactor-TDD-8b5cf6">
  <img alt="gate" src="https://img.shields.io/badge/verification-9%20gates-d97757">
  <img alt="smells" src="https://img.shields.io/badge/false--green%20smells-16-3fb950">
</p>

---

## What is this?

A skill that teaches Claude to write **test cases that fail when the behavior is
wrong** — and refuses to call a change "fixed" until that's proven. It's built on a
hard lesson: a test suite stayed **green** while the shipped feature was **100% broken
in production for a day**, because the tests validated a *hand-rebuilt copy* of the code
instead of the code, and asserted *liveness* ("got a 200") instead of the *content
contract* ("the answer is correct").

> **Philosophy.** A test that cannot fail is a lie. Every test must (1) execute the
> **real shipped artifact**, (2) assert the **semantic contract**, and (3) have been
> **seen to go red** on the broken code.

Language- and framework-agnostic: works with pytest, Jest/Vitest, Go `testing`, JUnit,
RSpec, xUnit — whatever you have.

## What it teaches

- **Test the real artifact** — invoke the actual exported function / real endpoint /
  shipped binary, never a reimplementation of the payload/schema/SQL.
- **Assert the content contract, not liveness** — the value is correct, N inputs → N
  outputs, the field is populated, the right script/encoding — not "returns 200".
- **Red before green** — a test you never saw fail proves nothing.
- **Hunt silent failures** — swallowed `catch`, fallback-to-default, retry-then-succeed;
  assert the failure path did *not* fire.
- **Contract-test the boundary you don't control** — third-party APIs, schemas,
  encodings, model output, size limits; mocks encode *your* assumptions.
- **Cover edges, negatives & limits** — empty, oversized (over-the-cap!), wrong-encoding,
  malformed, off-by-one, the unhappy path.
- **Verify in the shipped artifact + telemetry** — grep the built bundle/image; pull
  production logs and assert zero new errors.

## False-green smells

The named anti-patterns that make a suite green while the code is broken — each with why
it lies and the fix, in `skills/test-case-author/references/02-false-green-smells.md`.
Smells **1–11** cover bad tests; **12–16** cover the envelope around the test (silent
layer skips, prompts shipped without an LLM eval, UI shipped without a browser,
comments that don't match the test fixture, claims with no measurement).

| Smell | The lie |
|-------|---------|
| **Reconstructed Payload** | Test rebuilds what the code should produce — the buggy code never runs |
| **Liveness-Only Assertion** | "200 / didn't throw / truthy" — proves the wire is up, not the answer |
| **Never-Red** | Written after the fix, never seen to fail on broken code |
| **Swallowed Failure** | catch/fallback/retry hides the error; happy return looks fine |
| **Mock Mirrors The Bug** | The mock returns what you *think* the dependency does |
| **Untested Boundary/Limit** | Size caps, encodings, off-by-one never exercised |
| **Shared Assumption** | Test and code derive the expected value from the same wrong head |
| **Stale Artifact** | Source is fixed; the deployed bundle/image is old |
| **Implementation-Coupled** | Asserts internals; refactor breaks it or a real bug slips through |
| **Tautology / Vacuous** | No real assertion, or a silently-skipped test |
| **Nondeterminism Mask** | Flaky test "fixed" by loosening assertions / retry-until-green |
| **Skipped Layer** | Change crosses N layers; tests cover M < N; the gap is silent |
| **Prompt-Without-Eval** | Prompt file edited; mocked LLMs ran; real model never invoked |
| **UI-Without-Browser** | Component/hook/page changed; dev server never started |
| **Comment-vs-Test Drift** | Comment promises defense against X; test fixture exercises Y |
| **Claim Without Measurement** | "Fits in 1 KiB / 30 ms / 20 items" — asserted, never measured |

## Install

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install test-case-author@ghost-skills
```

…or copy `skills/test-case-author` into `~/.claude/skills/`.

## Use

```text
/test-case-author                     # explicit
write tests for this change           # natural
how should I test this?               # natural
why didn't the tests catch this?      # natural
the tests pass but it's still broken  # natural
did I test this right?                # natural
```

## How it works

```text
1.  Contract   — state input → required output/effect (from the spec, not your head)
2.  Classify   — map the change to required test layers (UI? prompt? wire shape? cap?)
3.  Red test   — reproduce the risk; watch it FAIL on the broken code
4.  Real       — drive the actual exported fn / endpoint / binary
5.  Assert     — the content contract, not liveness
6.  Match      — test fixture matches the EXACT scenario the code comment names
7.  Edges      — empty, over-the-limit, wrong-encoding, malformed, the unhappy path
8.  Boundary   — ≥1 real-I/O / contract test where reality diverges from your model
9.  Measure    — every empirical claim in the PR has a committed script / number
10. Verify     — fix is in the SHIPPED build + production logs show zero new errors
```

## What's included

```text
test-case-author/
├── .claude-plugin/plugin.json
├── README.md
└── skills/test-case-author/
    ├── SKILL.md                          # orchestrator: philosophy, workflow, smell list
    └── references/
        ├── 01-principles.md              # pyramid, doubles, contract testing, mutation, Hyrum's Law
        ├── 02-false-green-smells.md      # the anti-pattern catalogue
        ├── 03-coverage-checklist.md      # fill-in checklist for any change
        ├── 04-verification-gate.md       # "before you say it's fixed" — 7 gates
        ├── 05-case-studies.md            # sanitized war-stories
        └── test-plan-template.md         # the reusable emitted template
```

## Author

**Aditya Pratap Singh** — [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](../../LICENSE)
