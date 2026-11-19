# P283 operation-bound synthetic admission candidate — 19 November 2026

**ALL SECURITY GATES HOLD. 0/7 qualified approvals; 0/3 full product regressions.
P96 original OPEN; P76/P216 failures unwaived.** Independent review and hosted
runtime evidence are outstanding. This is an uncommitted implementation candidate.

Initial and final parent: `0f22089b918f428bca8347eff31c563cf17571d2`.
Exact worktree: `D:\Nayeon\CODEX_P283_OPERATION_BOUND_ADMISSION_20261119`.
Branch: `byok-c1-p283-operation-bound-admission-20261119`.
Initial working tree/index were clean. No tag points at HEAD; nearest reachable
tag reported by Git is `nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`.
`.codex/CURRENT_STATE.md` instead describes an older Phase 10.2 candidate;
it is not this branch's authoritative baseline and was not rewritten as a
phase-completion claim. No product phase or security gate is sealed here.

## Implemented executable seam

`SyntheticOperationAdmission` privately owns one genuine P269
`ComposedDevelopmentService`, its P268 pending transaction, and only the existing
P96 in-memory fixture. The private P268 approval is never returned. There is no
P271 durable witness, protected store, production factory or production GO result.
P271/P282 were inspected as dependency-boundary context and remain unchanged.

The explicit test factory returns a fixture-specific issuer object. Only exact
issuer reference identity can issue a synthetic ticket. Constructing another
issuer or copying metadata cannot grant admission. The issued ticket is likewise
registered by reference to this owner; its fields convey no transferable grant.
Both objects are **TEST ONLY**, with no human-consent or credential meaning.
This is isolation against untrusted request inputs, not a sandbox against
arbitrary trusted test-assembly code or reflection. The factory itself is a
trusted development harness entrypoint, never an IPC/public admission API.

Issuance binds every immutable P102 field: operation, session ID, request ID,
candidate hash, exact expiry and destructive acknowledgement. For Save/Replace,
the requested marker must be exactly `31 32 33 34`, with its independently
computed SHA-256; Delete requires null marker/hash and acknowledgement. Those
checks restrict the fixture, never establish consent. No SID, trusted flag,
digest or timestamp claim is accepted as authority. The issued request is
retained privately; caller buffers never cross into P269's fixed-marker submission.

An atomic lifecycle reservation prevents a callback or competing submitter from
issuing or submitting twice. Failed issuance by the real fixture issuer closes
the session. A malformed/fabricated first submission after issuance consumes and
revokes that session. Subsequent submissions deny. Tickets and issuers do not
transfer across owners even with identical metadata. A separate fixture can
deliberately issue the same metadata only using its own newly provisioned issuer;
this is not a global persisted replay registry or restart recovery mechanism.

Submission calls the actual P269 `TestSubmit`, hence P268 `Apply`, journal/anchor
writes, custody lease, fixture effect and terminal cleanup. Revoke/stop/fault call
P269's existing controls and P268's **same** final gate. There is no new final
revocation/effect lock or effect implementation. Expiry is checked at admission
and inside the existing P268 synchronous probe, after any adversarial callback,
including `effect-enter` just before the P96 fixture effect. The clock is service
`DateTime.UtcNow`, not an injected caller clock. This is an immediate clock check,
not a claim that wall-clock reads and an effect are physically atomic.

P268 sets `MayHaveEffect` and records intent before `effect-enter`. Therefore an
expired/failed probe there reports **RecoveryRequired**, even with zero actual
P96 effects. A thrown fixture effect remains uncertain and cannot become a
successful cancellation. Nonfresh starts and stopped instances cannot restart.

Static self-review found that a malicious callback could swallow a reentrant
P268 control exception: the older adapter would otherwise resume into its
fixture effect before P268's next barrier. The additive coordinator now latches
failed control/start/disposal calls, and closed observations, before returning
to the callback; its same in-gate probe refuses continuation. P268/P269 remain
byte unchanged. This is a static finding and candidate containment, **not** a
runtime reproduction or verified closure. Adversarial callback tests cover
revoke/stop/fault, restart/disposal, observation, thrown callbacks and a separate
thread timing out on P268's 500ms gate.

## Compilation and authentic evidence

Only direct native compiler invocations ran locally. The new compile script was
parsed, not executed/dot-sourced/evaluated. No policy changes or bypass occurred.
No generated executable, Python, real SCM/token probe, protected-store or native
effect harness ran. No unexpected C# compiler failure occurred before repair;
there is no runtime red-to-green claim.

Actual compilers:

- `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe` — x64
- `C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe` — x86

Arguments: `/nologo /noconfig /warn:4 /warnaserror+ /target:exe /debug+
/optimize- /platform:x64|x86`, absolute framework references for `System.dll`,
`System.Core.dll`, `System.Security.dll`, `System.ServiceProcess.dll`; absolute
source inputs and seven defines listed in `CompileReview.ps1`. Every final
invocation's actual splatted argument array is in its `.command.json`; compiler
output and raw `$LASTEXITCODE` are in adjacent `.log`/`.exit` files.

Final evidence directory:
`C:\Users\krist\AppData\Local\Temp\nayeon-p283-exact-compile-ec56ed1ad7f44d0e8f2a29cc17c849b7`.

| Positive compilation entrypoint | x64 raw exit | x86 raw exit |
| --- | --- | --- |
| SyntheticOperationAdmissionTests | 0 | 0 |
| P268RemediationTests | 0 | 0 |
| P269ComposedServiceTests | 0 | 0 |

| Missing define negative | x64 raw exit | x86 raw exit |
| --- | --- | --- |
| ALL | 1 | 1 |
| DEBUG | 1 | 1 |
| C1_REVIEW_ISOLATED_ASSEMBLY | 1 | 1 |
| C1_P265_DEVELOPMENT_ONLY | 1 | 1 |
| C1_P267_DEVELOPMENT_ONLY | 1 | 1 |
| C1_P268_DEVELOPMENT_ONLY | 1 | 1 |
| C1_P269_DEVELOPMENT_ONLY | 1 | 1 |
| C1_P283_SYNTHETIC_OPERATION_REVIEW_ONLY | 1 | 1 |

All sixteen negatives contained `error CS1029` with
`P283_TEST_ONLY_ALL_DEVELOPMENT_FLAGS_REQUIRED` and emitted no executable.
All six positives emitted assemblies with warnings treated as errors.
Direct orchestration process exit: **0**. Compile-script parser: **0 errors**.
`git diff --check`: raw exit **0**. No tracked parent changes/index changes.

Final evidence SHA-256:

- `raw-exits.txt`: `B69BDE1F3548B5A7B184819A247D2E7D1F9FA38758D04A6B89ABDCFD42F3AA97`
- `source-sha256.txt`: `884571C0D8B665DCA1FB10EC180C4CE0BAA01B9BACD892DF05A0D8BCED8D1EF6`

Authentic tooling/evidence issues are preserved:

- Initial `rg` command returned process exit **1** because `rg` was unavailable;
  bounded `git ls-files`, `Get-Content` and `Select-String` replaced it.
- Initial successful compilation evidence is retained in Temp directory
  `nayeon-p283-compile-e8c8fd9a84724924bc1a7c313f292711`, including the earlier
  source hashes before callback containment. Its compile results do not validate
  the later source revision.
- Intermediate `nayeon-p283-final-compile-29dc45955c274a3ba7a2a596f7426a4e`
  contains valid compiler logs/exits but malformed **positive command metadata**:
  PowerShell array construction concatenated define/main/out in the JSON record.
  The actual compiler calls used separate arguments and succeeded. Those records
  were preserved, not overwritten. The final run constructs each argument
  separately, records that array, and passes that exact array to csc. Do not use
  the intermediate positive JSON files as executable command records.

## Open Failures & Prior-Issues Review — HOLD

| Issue / severity | Root cause / affected boundary / evidence | Containment / tests / review / disposition |
| --- | --- | --- |
| P96 original — material security OPEN | Historical check-to-effect revocation gap; caller-owned approval is not service-final ordering. Original evidence is unmodified. | Only actual P268/P269 successor gate used here; authored all-operation revoke/stop/fault ordering cases. Hosted run and independent review OPEN; HOLD. |
| P76/P216 — material unresolved, severity not reclassified | User reports prior failures; this task does not establish their full root cause or closure. | No historical tests changed or waived. Full affected/native regressions outstanding; HOLD. |
| P282 PR #202 RED/HOLD — material missing evidence | Omitted P270/P271 ACL-changing runtime harness; user baseline focused P282/P268/SCM results do not satisfy broader gates. | No P270/P271 harness run, restoration, waiver or workflow change here. HOLD. |
| Swallowed reentrant control — candidate static finding | P268 adapter callback may return after swallowing an error before its next barrier. Reached through new synthetic fixture callback, including alternate start/dispose/observe paths. | Sticky local containment checked inside same P268 probe; adversarial cases compiled, runtime and independent validation OPEN. HOLD. |
| Service identity/store/consent — HIGH inherited boundary | Metadata, token observation and disposable fixture identity are not authenticated human consent or protected-store custody. | No production admission, durable bridge, credential/native adapter, installation or protected path. HOLD. |
| Evidence argument metadata — tooling defect | Intermediate JSON positive arguments were concatenated; no actual failed native build. | Preserved evidence, repaired recorder and fresh exact-array 22-command compilation exit 0. Independent audit OPEN; HOLD. |

The reviewed dependency path is P102 metadata → new fixture-owned issuance →
P269 lifecycle/submission → P268 final gate → P96 managed fixture. Alternate
control, observation, disposal, concurrent submit, callback and nonfresh/restart
paths have authored tests. P271 protected/durable routes and P282 observation
remain outside this candidate's execution graph. There is no closure claim for
cross-process persistence or production service isolation.

## Remaining independent Windows work

The new executable has **49 authored cases**, none run here. It refuses normal
execution unless Windows and the explicit disposable hosted-fixture environment
are present (`GITHUB_ACTIONS=true`, `RUNNER_ENVIRONMENT=github-hosted`,
`RUNNER_OS=Windows`, `P283_HOSTED_SYNTHETIC_ONLY=1`) and refuses SYSTEM.
Environment claims only restrict test execution; they grant no production
authority. P269 uses its existing disposable denial-only pipe worker; no IPC
installation, SCM registration or durable protected-store harness is added.

After independent exact-source review, a separately authored Windows workflow
must compile/run x64 and x86 P283 plus affected P268/P269 managed harnesses,
retain exact hashes/raw outputs, and investigate any genuine failure before
progression. No workflow is supplied or edited in this task. Qualified approvals,
all three full product regressions, cross-phase review, syntax/compileall and
any security seal remain **OPEN / HOLD**. The user-supplied P282 baseline (135
negatives, P268 33 cases/341 assertions and missing-service denials) is prior
evidence, not a fresh P283 result. No smoke result or hosted success is invented.

Exactly four additions; frozen tracked source/test/history remains unchanged:

| Path | Raw SHA-256 |
| --- | --- |
| `native_c1_successor/P283SyntheticOperationAdmission.cs` | `E0359FF685B295472D36D458F6D07D01EA7D9FA4CF564104E3F1C76FE78B524A` |
| `tests/p283_operation_admission/SyntheticOperationAdmissionTests.cs` | `75345890C589D45079F2968525BB7EF127578186625B489E885676488F91E58B` |
| `tests/p283_operation_admission/CompileReview.ps1` | `64E4080C83AF0167E032A9C6E2DBB0F70C4DA28AAE7AF40E294E308F5CBD99A5` |
| `docs/byok-c1-p283-synthetic-operation-admission.md` | This report; final hash delivered separately. |

No staging, commit, push, merge, tag, PR, workflow, workbook or dashboard change.
No other worktree, real credential, WinCred/provider/camera, protected store,
principal, machine policy, Application Control or live UI-consent action.
