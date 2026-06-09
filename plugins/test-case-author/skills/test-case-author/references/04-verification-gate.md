# 04 — Verification Gate: BEFORE you say it's fixed

The single checklist that would have caught the green-but-broken-in-prod incident.
"Tests pass" is **not** a synonym for "fixed." A fix is verified only when **all
seven gates** below are green. If you can't tick one, you don't get to say "fixed" —
say "tests pass but unverified at gate N."

This gate is the spine of the whole skill: it operationalizes the three-part rule
(real artifact · content contract · seen red) and adds the production-reality checks.

---

## The seven gates

### (a) I saw the test go RED on the broken code
- The test failed **for the right reason** before the fix (or with the fix reverted/
  sabotaged), then passed after.
- A test never observed to fail proves nothing (**Never-Red**). Retrofit: revert the
  fix → run → confirm red → restore → confirm green.
- ✅ when: you can name the failing assertion and the broken behavior it reported.

### (b) The test executed the REAL artifact
- It called the **actual exported function / hit the real endpoint / ran the shipped
  binary** — not a hand-rebuilt copy of the payload/schema/SQL (**Reconstructed
  Payload**).
- ✅ when: you can point to the line that invokes the shipped symbol, and confirm the
  buggy code path actually ran (not a mock standing in for it).

### (c) It asserted the CONTENT contract, not liveness
- The assertion checks the **right value/effect**: correct number; non-English input
  returned translated in the right script; **N inputs → N outputs**; owner/tenant
  field populated; row actually persisted.
- "Returns 200 / didn't throw / returned something" does **not** count (**Liveness-
  Only**).
- ✅ when: every assertion names a semantic guarantee, and the expected value was
  derived from the **spec or the real dependency**, not your head (**Shared
  Assumption**).

### (d) At least one test hit the REAL dependency (or a faithfully recorded contract)
- One test drove **real I/O end-to-end through the actual pipeline**, or replayed a
  recorded real interaction (cassette/fixture/Pact).
- Mocks encode *your* assumptions; if the assumption is wrong the mock passes and prod
  fails (**Mock Mirrors The Bug**).
- ✅ when: you can name the contract/real-I/O test and confirm its fixture was recorded
  from (or verified against) the real dependency.

### (e) The fix is in the SHIPPED artifact, not just source
- Grep the **built bundle / deployed image / running config** for the change; confirm
  the deployed version/SHA matches HEAD (**Stale Artifact**).
- ✅ when: the change is present in the artifact that actually serves traffic — e.g.
  `grep <change> dist/…`, `docker run <image> -- cat …`, deployed `/version` == HEAD.

### (f) Production logs / telemetry show ZERO new errors
- After deploy (or on a real run), pull logs/metrics/traces for the affected path and
  confirm **no new errors/retries/fallbacks**. In the incident the exact errors sat in
  the logs all day under a green suite.
- Observing the real system beats synthetic tests; tests **complement** telemetry, they
  don't replace it.
- ✅ when: error rate, retry rate, and the relevant success metric on the affected path
  are nominal for a real window of traffic.

### (g) The failure/fallback path did NOT fire
- For any swallowed-error / fallback-to-default / retry-then-succeed path, assert the
  **failure branch did not run** (fallback counter == 0, retry count == 0, error metric
  flat) — not just that a success value came back (**Swallowed Failure**).
- Prefer asserting the **absence** of the error/retry/fallback signal over the presence
  of a success marker (a success log can be hidden by log level).
- ✅ when: a spy/metric proves the real path executed and the degraded path stayed cold.

---

## Gate scorecard (paste into your report)

```text
Verification gate — <change / feature>
(a) Saw RED on broken code .................. [ ] PASS  [ ] FAIL  → <failing assertion>
(b) Executed the REAL artifact .............. [ ] PASS  [ ] FAIL  → <invocation site>
(c) Asserted CONTENT contract ............... [ ] PASS  [ ] FAIL  → <semantic assertion>
(d) Hit REAL dependency / recorded contract . [ ] PASS  [ ] FAIL  → <which test>
(e) Fix in SHIPPED artifact ................. [ ] PASS  [ ] FAIL  → <grep/version proof>
(f) Telemetry: zero new errors .............. [ ] PASS  [ ] FAIL  → <window + metric>
(g) Failure/fallback path did NOT fire ...... [ ] PASS  [ ] FAIL  → <counter/spy>

Verdict: VERIFIED  |  TESTS PASS BUT UNVERIFIED AT GATE(S) <n…>  |  NOT VERIFIED
```

## Honesty rule
If a gate genuinely doesn't apply, mark it **N/A with a one-line reason** (e.g. "(g)
N/A — no fallback path in this function"). Never tick a gate you didn't actually
check. The whole point is that "green" was lying once before; this gate exists so it
can't lie again.
