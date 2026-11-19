# P284 durable operation admission — development candidate, 19 November 2026

**SOURCE CANDIDATE; runtime and independent review OPEN. REAL KEYS NO-GO;
PRODUCTION HOLD. P96 original HIGH OPEN. Qualified approvals 0/7; full-product
Windows regressions 0/3. No SEC03/04 sign-off.**

Verified initial branch `byok-c1-p284-durable-operation-bound-admission-20261119`,
HEAD `9730d810670023909aa1fc3213a4c1130ad6ffb0`, clean index/worktree, no HEAD tag.
Only worktree: `D:\Nayeon\CODEX_P284_DURABLE_OPERATION_BOUND_ADMISSION_20261119`.
Nearest reachable tag: `nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`.
The November 3 Phase 10.2 text in `.codex/CURRENT_STATE.md` is stale for this
branch. It was read and left unchanged; this candidate does not complete a
product phase or establish a new full-regression baseline.

## One owner, one final transaction

`DurableOperationAdmission` privately constructs exactly one P271
`DurableDevelopmentBridge`. It does not instantiate P283 or another P269 owner.
Its private P268 approval is issued by that same bridge's `Prepare()` and is
submitted only through that bridge's `Submit()`. There is no second effect,
credential port, lock, final-effect gate or protected-service admission path.

The path is immutable P102 metadata → fixture-specific issuer/ticket → P271 →
its P269/P268 transaction → P271 synchronous probe/durable witness → P96 managed
fixture. P271 retains its actual P282 runner binding, protective P270 DPAPI/file
writes, journal/anchor sequencing, custody and cleanup. Replace/Delete retain
P271's existing synthetic prior-Save journal provisioning. Only the fixed
`31 32 33 34` fixture marker (or acknowledged Delete) can be submitted.

P283's issuer/ticket reference discipline is carried into this separate owner:
the issuer is privately created, tickets are exact-reference registered to one
owner, and all six immutable request fields are bound. Missing/mismatched
operation, candidate, digest, acknowledgement, session/request ID or expiry is
refused. A valid P102 constructor and its syntactic claims establish **no human
consent**. Neither a caller SID nor callback result is an admission input.
Buffers are validated only; P269 constructs the actual fixture marker.

Atomic states reserve issuance and submission once. These are lifecycle latches,
not a competing final revocation gate. Revoke/Stop/Fault/Dispose continue through
P271/P268. Failed/reentrant controls and closed observations latch uncertainty.
The owner-installed P271 `TestProbe` checks that latch, submitting state, bound
expiry and independently captured actual P282 runner identity after a trusted
test adversary and before P271's own checks at every probe. In particular,
`effect-enter` runs before the existing P96 fixture effect, inside P268's gate.
No callback can authorize an effect; callbacks can only exercise/deny this
trusted test assembly. Reflection/arbitrary same-user malware isolation and
production trusted UI are not claimed.

P268 marks intent/uncertainty before effect entry. A rejection there can therefore
return RecoveryRequired with zero fixture effects. A fault after an effect never
becomes safe revocation: the inherited gate returns TooLate/RecoveryRequired.
Successful results remain StoredUnverified/RemovedUnverified. Wall-clock/token
checks are immediate observations, not physically atomic continuous OS proofs.

## Harnesses and validation actually performed

The compile-only durable harness contains **128 authored cases**, including all
three positive operations, durable terminal consistency, all-field tampering,
foreign issuer/ticket, malformed valid P102 metadata, expiry, swallowed reentrant
controls/Dispose/start/observation, concurrent submit, gate timeout, closed
witness, same-user thread impersonation at ten probe points, uncertain effects,
disposal and durable restart refusal. These cases have **not run**.
All 128 authored full P284 durable positive cases require separate qualified
permission and 129 preprovisioned roots.

Its entrypoint requires hosted Windows, non-SYSTEM/non-Kristian execution,
`P284_REVIEWED_DURABLE_RUNTIME=1`, P271 opt-in and 129 distinct pre-provisioned
P270-compatible empty disposable roots in `P284_PREPROVISIONED_ROOTS` (pipe
separated). It never creates/repairs root ACLs, provisions roots or deletes them.
P270 remains the authoritative root/handle/ACL validator. The explicit restart
negative reopens one already-used root only to require refusal. A future durable
run still invokes P270's protective file-owner/DPAPI writes and therefore needs
separate review/authorization. **No durable runtime is authorized by this task.**

The separate `P284ReadOnlyNegativeTests` entrypoint authors eight pre-witness
host-claim denials, checking unchanged P270 diagnostic stage. The draft-PR-only
workflow is configured to compile and execute only this entrypoint on hosted
x64/x86, clear the child environment, supply no durable root/positive opt-in,
pin candidate sources, verify the exact single P283 child and every inherited
Git entry/raw disk blob, and retain text-only evidence. No prior workflow is modified and
the omitted P270/P271 hazardous suites remain omitted. Admission requires an
opened/synchronize/reopened draft PR within `krismcan/Mark-LV`, the exact P284
head branch named above, base branch
`byok-c1-p283-operation-bound-admission-20261119`, and base SHA
`9730d810670023909aa1fc3213a4c1130ad6ffb0`; another repository is refused.
Checkout and Git HEAD bind the event's head SHA, not the PR merge SHA. Invalid
events or missing evidence fail closed; the upload allowlist contains only
sanitized text evidence, never executables. The workflow is authored for
independent review; **it has not run or been runtime-validated**.

Actual local execution was direct absolute Framework64/Framework
`v4.0.30319/csc.exe` compilation only, with `/warn:4 /warnaserror+ /target:exe
/debug+ /optimize- /platform:x64|x86` and absolute System, Core, Security and
ServiceProcess references. `CompileReview.ps1` was parsed, never executed,
dot-sourced or evaluated. No policy/Application Control bypass occurred.

- 18 positive builds: both architectures for P284 durable/read-only, preserved
  P283, P268, P269, P270, P271 and P282 entrypoints, plus the workflow's exact
  smaller source set; raw exits all 0.
- 24 negative builds: each architecture missing ALL or each of ten P284 required
  defines, plus explicit DEBUG+RELEASE. Raw exits all 1, genuine `error CS1029`
  with `P284_TEST_ONLY_ALL_DURABLE_FLAGS_REQUIRED`, no executable emitted.
- Compile manifest and embedded workflow PowerShell parsers: 0 errors each.
- No generated executable or Python ran; no native durable positive, token
  harness, full unittest discovery/compileall, smoke or independent validation
  is claimed. `git diff --check` and separate added-file whitespace checks pass.
- All 1,143 inherited files match HEAD's raw Git blob IDs using
  `git hash-object --no-filters --stdin-paths`; zero mismatches, unchanged index.

Compiler evidence:
`C:\Users\krist\AppData\Local\Temp\nayeon-p284-final-compile-c6d4b5c57b3e47d7b3ee0d62b04efd75`.
Each build has actual argument-array JSON, compiler log and raw exit; source
SHA-256s are recorded. `raw-exits.txt` SHA256:
`30FF1653D7372ECE561F4A62620F9C8019802B2A2497E6C67948B1DEB51D1B14`;
`source-sha256.txt` SHA256:
`EDCC454DB7CBA9B1E556F2696810853E4342BB88D59BE040B0A9D3AAAFDEDAC2`.
`rg` was unavailable; Git/Get-Content/Select-String supplied bounded reads.
One patch hunk failed to match the full guard line; no source was changed by
that failed hunk, and the explicit RELEASE guard was then applied and compiled.
Initial compilation is preserved in `nayeon-p284-direct-compile-fc7ffc12afbb4cf28f7fe70b196ffd6a`.
After self-review enlarged the new expiry-test window to avoid premature expiry
during durable writes, all 42 compiler invocations were repeated against final
bytes. Replay used argument JSON as data, directly invoking only the approved
compilers; no script evaluation. One orchestration attempt stopped before any
compiler call because its exact-case whitelist expected `C:\Windows` instead of
the recorded `C:\WINDOWS`. Diagnosis is retained in
`nayeon-p284-final-compile-81af95ef18594835b99c1eb36515be28/stop.log`;
the subsequent exact-recorded-path run above exited 0. No native test failed,
was skipped, or was weakened to obtain a runtime PASS.

## Open Failures & Prior-Issues Review — HOLD

| Issue / severity | Root cause, affected path, evidence and disposition |
| --- | --- |
| Disconnected P283/P271 owners — HIGH design hazard | P283 owns a separate in-memory P269/P268. Reusing its approval for another durable effect would split final ordering. New P284 owns only P271 and keeps that bridge's private approval. Positive/ordering/adversarial cases compiled; runtime and independent closure OPEN. |
| P96 original — HIGH OPEN | Inherited check-to-effect revocation gap. Original source/tests untouched; successor P268 alone orders this fixture's effects and controls. User reports P283/P268/P269 hosted PASS on P283 PR #203; no new runtime reproduction/closure here. HOLD. |
| Swallowed reentrant control — material inherited incident | P283 review describes a callback swallowing P268's reentry error before effect. Sticky containment retained through P271's in-gate callback; controls, start, observation, Dispose and bounded competing-thread timeout covered. P283 runtime baseline supplied by user; new durable runtime/review OPEN. |
| P270/P271 ACL-changing positive CI omission — material missing evidence | Root provisioning and protective writes require separately reviewed hosted execution. No root provisioned or positive harness executed anywhere in this task. New read-only workflow cannot close durable custody acceptance. HOLD. |
| Service identity/store/consent — HIGH boundary | Actual runner token is synthetic restriction, never protected-store custody or human consent. Protected P271 route remains denial-only; real keys/WinCred/production NO-GO. SEC03/04 OPEN. |
| P76/P216 and full-product regression evidence — unresolved inherited | Prior failures/root-cause closure not established here; no frozen test changed or finding waived. Qualified approvals 0/7 and full Windows regressions 0/3. HOLD. |

The authorized advance is additive development source plus compilation; no
material inherited failure is declared repaired or deferred as low risk. Required
next work is independent exact-source/security review, read-only workflow review
and, separately authorized, durable hosted adversarial evidence. Product/release
gate remains **HOLD**, including actual full regressions and qualified approvals.

Exactly five additions: owner, harness, compile manifest, this report and draft-PR
read-only workflow. P270–P283 and all inherited source/tests/workflows remain
unchanged. No stage/commit/tag/push/PR, other worktree, credential, WinCred,
service install, local ACL change or workbook/dashboard update. The user defers
Drive workbook/dashboard until full BYOK C1 release. Final file hashes are in
the handoff receipt; this report does not self-pin.

| Candidate file | Raw SHA256 |
| --- | --- |
| `native_c1_successor/P284DurableOperationAdmission.cs` | `FC951E6F515A1803D1405129616BCDDCBF8F3A1E93FC0BC761F72FFFF09F0951` |
| `tests/p284_durable_operation/DurableOperationAdmissionTests.cs` | `E6D91A8B95B85B22F62AE6EE206CE37C2D0C990B2016553F9C7A5D583B68E340` |
| `tests/p284_durable_operation/CompileReview.ps1` | `1B5CF9E774E7C6AFF059A2489F7A2729CB1041E7C519C47DDBF0BAAFECE783E1` |
| `.github/workflows/p284-windows-read-only-admission-review.yml` | `2FE3EC691820229BEA719D1DD7611A1944C7FA1B1D1F309F8C703F6B4B248D40` |
