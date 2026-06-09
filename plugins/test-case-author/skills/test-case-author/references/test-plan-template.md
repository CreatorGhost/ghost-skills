# Test Plan Template

The reusable deliverable this skill emits for any change. Lead with the **contract
under test**, enumerate the **risks**, then write **red tests** that reproduce each
risk, an **edge/negative matrix**, **boundary** cases, at least one **real-dependency /
contract** test, and a **shipped-artifact + telemetry verification** with sign-off.
Markdown by default; trim sections that genuinely don't apply (mark `N/A` with a
reason — never silently drop a gate).

---

## Markdown skeleton

```markdown
# Test Plan — <change / feature / bug>
Scope: <files / endpoint / module> · Type: <unit | integration | contract | e2e>
Real shipped artifact under test: <exported fn / route / binary / built bundle>

## 1. Contract under test
- **Observable guarantee (1 line):** <input → required output/effect>
- **Expected value derived from:** <spec link | real dependency | independent calc>
  (NOT from my head or the code's current output)
- **Non-goals:** <what this plan deliberately does not cover>

## 2. Risks (what could be silently wrong)
- R1 — <risk> · likely smell: <Reconstructed Payload | Liveness-Only | Swallowed
  Failure | Mock Mirrors Bug | Untested Boundary | Stale Artifact | …>
- R2 — …

## 3. Red tests (one per risk; each MUST be seen to fail on broken code)
- T1 (→R1) — **drives:** <real symbol/endpoint> · **asserts:** <content contract>
  · **saw red:** <yes — failing assertion / how I sabotaged the fix>
- T2 (→R2) — …

## 4. Edge / negative matrix
| Case | Input | Expected (from spec) | Asserts value/effect? |
|------|-------|----------------------|-----------------------|
| empty | `[]`/`""`/`{}` | … | ☐ |
| single | one item | … | ☐ |
| many | N items | exactly N out | ☐ |
| null/missing | absent field | … | ☐ |
| invalid/malformed | … | rejected w/ <error> | ☐ |
| wrong encoding / non-Latin | CJK/RTL/emoji | correct script out | ☐ |
| dependency error object | upstream 4xx/5xx/timeout | fails loud, no default | ☐ |
| duplicate / unordered | … | … | ☐ |

## 5. Boundary & limit cases (test AT / UNDER / OVER each limit)
| Limit | just under | at | just over (must reject/handle) |
|-------|-----------|----|--------------------------------|
| size cap | ☐ | ☐ | ☐ → <status/error> |
| count / pagination | ☐ | ☐ | ☐ |
| time / expiry | ☐ | ☐ | ☐ |
| rate / quota | ☐ | ☐ | ☐ |

## 6. Real-dependency / contract test (≥ 1 required)
- **Test:** <name> · **Boundary:** <3rd-party API | DB | schema | model output | FS>
- **Mode:** real I/O e2e | recorded interaction (cassette/fixture/Pact)
- **Fixture recorded from / verified against the real dependency:** <when / how>
- **Asserts the dependency's error & rate-limit shapes too:** ☐

## 7. Silent-failure assertions
- For each swallow/fallback/retry path: assert the real path's effect **and**
  `fallback_count == 0` / `retry_count == 0` / error-metric flat.
- Prefer asserting the **absence** of the error/retry signal over a success marker.

## 8. Suite-strength check
- No tautology / no-assertion / silently-skipped tests for this change: ☐
- Mutation testing run on changed code (if available); surviving mutants closed: ☐

## 9. Shipped-artifact & telemetry verification
- Fix present in the **built bundle / deployed image** (grepped), not just source: ☐
  → <command / proof>
- Deployed version/SHA == HEAD: ☐
- Real-run **logs/metrics** on the affected path show **zero new errors**: ☐
  → <window + metric>

## 10. Verification gate (from 04-verification-gate.md)
(a) Saw RED ☐  (b) Real artifact ☐  (c) Content contract ☐  (d) Real dependency ☐
(e) Shipped artifact ☐  (f) Telemetry zero new errors ☐  (g) Failure path did NOT fire ☐

## Sign-off
> Verdict: VERIFIED | TESTS PASS BUT UNVERIFIED AT GATE(S) <n…> | NOT VERIFIED
> Covered: <list>. Skipped (reason): <list>. Real-I/O/contract test: <which>.
> Saw-red: <which tests>. Shipped+telemetry verified: <yes/no>.
```

## Rules for filling it in
- **Every test names the real symbol it drives** and the **value/effect it asserts** —
  if a row says "asserts 200/non-null", it's not done.
- **Every red test was actually seen to fail** on the broken code; record the failing
  assertion.
- **At least one row in §6 is a real/recorded dependency test.** A plan of pure mocks
  is a plan of pure assumptions.
- A box left unticked is an **open gap**, not a rounding error — list it under "Covered/
  Skipped" with a reason.
