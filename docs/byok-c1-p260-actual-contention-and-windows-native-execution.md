# P260 actual gate contention and Windows-native execution

17 November 2026. OM v2.1. Defensive tests only. Sole Codex writer. **REVIEW-ONLY /
NONDEPLOYABLE. CI recovery is UNCOMMITTED. Security and production release HOLD.**

## Intake and bounded change

Work root is `D:\Nayeon\CODEX_P260_P96_CONTENTION_WINCIRUN_20261117`, branch
`byok-c1-p260-p96-contention-ci-20261117`. Intake was clean at exact HEAD
`f9833383177e4c76f7997ad6041434c52c401c05`, with no tag at HEAD. Nearest ancestor
tag is `nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`.
`.codex/CURRENT_STATE.md` records older Phase 10.2 work. Git governs this review.
Only the four user-approved P260 paths are changed.

The CI-recovery intake is clean HEAD `ec086aba61324b287c21c85c807b057bba2ebf8f`
on that same branch, with P259 parent `f9833383177e4c76f7997ad6041434c52c401c05`
and existing draft PR #182. No tag points at the recovery intake HEAD. The state
file remains historical. This recovery changes exactly the workflow, P260 Python
source checker and this document. The P259 C# driver and all pinned C# source
bytes are preserved. The cumulative P259-base-to-PR-head scope stays four paths.

`EffectFirst` retains all 49 P259 cases. While the effect is paused inside the
private gate, it observes the publisher worker's `ThreadState.WaitSleepJoin`
with a bounded liveness/deadline check. `publicationWaiting` establishes arrival.
The thread-state check establishes blocking. An independent event,
`publicationReturned`, is set immediately after `Publish()` returns, before
assertions or `Read()`. The test asserts zero dispatch attempts and both return
and observation incomplete before releasing dispatch. This catches a premature
publication return followed by a blocked `Read()`. Existing post-release ordering,
one-use, recovery and cleanup checks remain active. The interrupted-admission
case reuses the same worker-state observer before interrupting.

The new Python module reads source bytes only. It checks the wait/return ordering,
original Main case-registration digest, frozen source pins and bounded CI
constraints. Thirty in-memory negative mutations exercise missing/false waits,
missing/delayed return evidence, disconnected pause, changed case count, unsafe
workflow triggers/permissions, altered pins, fabricated exits, changed receipts,
extra compiled authority, policy bypass and unsafe artifact paths. The eight
recovery mutations also reject relative source arrays, wildcard path resolution,
relative guard arguments, either relative positive-build branch, a direct relative
positive-build splat and a changed fail-closed error preference. These lexical
checks supplement native execution evidence.

## Open Failures & Prior-Issues Review

Reviewed the engineering failure gate, P259 review/owner/driver/source contracts,
original P96 fake proof and P250 architecture/security holds. The affected paths
are the original approval/lease/effect sequence, P259 private integer dispatch
and publisher observation. Cross-instance/process/restart authority stays open.

| Issue / severity | Cause, evidence and impacted boundary | P260 disposition |
| --- | --- | --- |
| P260 first CI compile failure / material | User-supplied evidence from genuine Actions run #44078871950 on 17 November 2026 reports both x64 and x86 failed at compile guards. `none-compile.log` reports CS1504 for both comparator source basenames resolved at the repository root. Relative forward-slash paths reached Framework `csc.exe`. Both positive-build routes shared that assumption. | Resolve each exact allowlisted source with literal canonical Windows paths before any compiler call. Eight in-memory mutations added. Host Python, both compilers, independent review and corrected CI evidence pending. Recovery acceptance HOLD. |
| P259 evidence gap / material | Contender event precedes gate entry. Completion after `Read()` can conceal an early `Publish()` return. | Strengthened driver plus negative source tests. Windows execution and independent review pending. HOLD for acceptance. |
| P96 race / HIGH | Original final approval and ownership checks precede a separate fake effect. Original proof reproduces Save/Replace/Delete after revoke. | Preserve original bytes and negative assertions. A proof PASS records reproduction. Production repair OPEN / HOLD. |
| SEC-03/04 / HIGH missing evidence | Service principal/store, consent, IPC, loaded-code identity, durable recovery and alternate effect exclusion lack qualified evidence. | Qualified approvals remain 0/7. Security HOLD. |
| Original regression failures / material | Four original P76 FAIL methods, original P251 FAIL and inherited P258 failures remain unwaived. | Targeted CI supplies no closure. Whole-product regressions remain 0/3. HOLD. |
| P247 native execution / material missing evidence | Application Control and PowerShell policy blocked execution. | Existing x64 0/54 and x86 0/54 record preserved. Policy refusal stops execution. HOLD. |

**GO for the user-authorized three-file CI recovery only within the existing
four-path P260 scope. Security, production and release HOLD. Independent review pending.**

## First GitHub Actions run and bounded recovery

Genuine run #44078871950 failed on both x64 and x86 at the compile guard step.
The user-supplied run evidence records successful source checkout, exact head and
source pins, P260 Python source contracts 5/5 and P259 Python source contracts 4/4
before that failure. The uploaded x64 `none-compile.log` contains these diagnostics.

```text
error CS1504: Source file 'd:\a\Mark-LV\Mark-LV\P259OwnedPendingTransaction.cs' could not be opened (The system cannot find the file specified).
error CS1504: Source file 'd:\a\Mark-LV\Mark-LV\OwnedPendingTransactionTests.cs' could not be opened (The system cannot find the file specified).
```

Framework `csc.exe` received relative forward-slash source arguments and resolved
their basenames at the repository root. The guard step failed before the original
P96 or P259 positive build and runtime loops. **No C# execution is credited to this
run on either architecture.** The two CS1504 diagnostics provide no CS1029 guard
acceptance. All three negative builds still require compiler failure, no output
DLL, exactly two CS1029 diagnostics and the explicit NONDEPLOYABLE guard message.
Both positive builds still require raw compiler exit zero before execution.

Immediately after the fixed `$original` and `$comparator` relative allowlists,
the recovery maps every authorized entry through
`(Resolve-Path -LiteralPath $_).Path` in the checked-out repository, producing
`$originalNative` and `$comparatorNative`. `$ErrorActionPreference = 'Stop'`
makes a missing source terminate the step before compiler invocation. Each of
the three guard builds splats `@comparatorNative`. The positive-build loop
selects `$comparatorNative` or `$originalNative` into `$sources` and splats
`@sources`. The compiler receives canonical absolute Windows source paths for
all five builds. The source checker requires this resolution immediately after
the exact allowlists, before guard compilation, plus the fail-closed preference
and canonical argument flow through both compiler call sites.

Nayeon independently runs the updated host Python contracts, x64/x86 compiler
guards and fake-only execution, and code review before pushing the correction
to existing draft PR #182. Recovery authoring leaves all three edits unstaged.

## Review-only Windows CI

The workflow triggers solely on `pull_request` targeting
`byok-c1-p259-p96-owned-effect-ordering-20261117`. It checks out the event's exact
head with read-only repository permission and persisted credentials disabled.
The base SHA must equal the intake HEAD, that base must be an ancestor, and the
complete base-to-head path set must equal the four approved paths. A moved base
fails closed and requires a fresh source-bound review.

Each Windows x64/x86 job verifies raw SHA-256 pins for all five compiled C#
sources and the preserved candidate service/boundary. Both P259 source flags
are required. No-flag and single-flag compilations must produce both explicit
CS1029 guard rejections. The original P96 ledger/coordinator/fake driver compile
into one executable. The P259 owner/driver compile separately with both review
flags. Native compilation and child exit values are captured immediately and
retained with stdout/stderr. Runtime acceptance requires raw exit zero, exact
receipts and case counts, P259 pointer width, original P96 race reproduction,
`P96_SECURITY_FINDING=OPEN` and production HOLD. Each child has a 60-second
deadline. Only its identified process is stopped on timeout. Evidence upload
runs on failure as well as success, whitelisting only separate `*.log`, `*.exit`
and `*.json` globs in the architecture-specific runner temporary folder.
No compiled executable or DLL uploads are permitted. Final pin and clean-tree
checks detect source mutation during execution.

An ordinarily permitted Windows process launch is required. A policy denial or
timeout is failed/blocked evidence. No policy change, alternate loader, credential
operation, provider call, installation or production execution is authorized.
Passing dual-architecture CI would establish 49 P259 and 15 original P96 fake-only
case executions per architecture. It grants no security sign-off or release.

## Validation status

Initial author checks covered exact Git intake, preserved source hashes,
PowerShell run-block AST parsing, bounded source inspection and whitespace/scope
checks. First-run CI source-only results above apply to the original submitted
source. Recovery static checks passed for all three PowerShell run-block ASTs,
all seven raw source pins, exact three-file unstaged scope and `git diff --check`.
The recovery's authoritative host Python access probe returned Access
denied in this sandbox. Updated Python tests and native C# compilation/execution
remain unexecuted locally. Corrected CI has yet to run. P259 runtime evidence
remains **0/49 x64 and 0/49 x86** for this candidate. Original P96 runtime evidence
from this CI remains **0/15 x64 and 0/15 x86**. Independent review,
affected/cross-phase and full authoritative product regressions remain pending.
Recovery authoring performs no staging, commit, push, tag, seal, new PR, workbook
or dashboard update. Original P96 HIGH, SEC-03/04, qualified approvals 0/7,
original regression failures, whole-product regressions 0/3, real-key NO-GO and
production/release HOLD remain in force.
