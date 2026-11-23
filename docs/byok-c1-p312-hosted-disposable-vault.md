# P312 actual service assembly WinCred foundation: PRODUCTION HOLD

2026-11-23. Sole source writer: Codex. Requested worktree:
`D:\Nayeon\CODEX_P312_HOSTED_WINCRED_20261123`, branch
`byok-c1-p312-service-hosted-windows-vault-20261123`. Initial Git worktree and
index were clean, HEAD `c430fafba1dc5890e59ade3f96c5cba13e5797c5` (P311),
with no tag pointing at HEAD. The old Phase 10.2 `.codex/CURRENT_STATE.md`
does not describe this checkout. Git is authoritative. The explicit five-path
scope leaves that file unchanged. No completed product phase or seal is claimed.

**Qualified production reviews 0/7; three full regressions 0/3; P96 HIGH;
P292 x86 SCM teardown UNKNOWN; REAL-KEY NO-GO; PRODUCTION RELEASE HOLD.**
This bounded implementation is explicitly requested synthetic-only containment,
not a disposition closing or deferring the unresolved production failures.

## Scope and topology

Exactly four additions and one modification:

| Path | Change |
| --- | --- |
| `src/Nayeon.ByokC1.Service/HostedDisposableWinCred.cs` | Internal test-only adapter and P312 friend declaration |
| `src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj` | Compile adapter; reference System.Web.Extensions |
| `tests/p312_product_vault/P312ProductVaultTests.cs` | Separate friend EXE referencing the actual product EXE |
| `.github/workflows/p312-windows-hosted-disposable-vault.yml` | Hosted draft-only four-cell build/test matrix |
| `docs/byok-c1-p312-hosted-disposable-vault.md` | This evidence and limitations review |

The actual .NET Framework 4.8 service EXE now contains real native protected-store
imports. This is a functional foundation, not another copied synthetic owner.
`CustodyService -> SyntheticTransactionOwner / SyntheticIngressServer` remains
unchanged; there is **no edge** from these or any other product class into the
adapter. Only `P312.ProductVault.Tests.exe -> HostedDisposableWinCred` is intended.
No constructor is public; there is no factory, pipe command, desktop/UI route,
service account admission or runtime configuration enabling this class.
The harness decodes product IL method/type/field operands across other product
types and checks source compile entries to reject adapter references. It also
checks all four private native imports and the actual product assembly reference.

Existing assembly-wide friend grants cannot be narrowed by a new C# internal
type. The constructor additionally checks the non-inlined calling assembly name
`P312.ProductVault.Tests`; no other existing friend is an intended entrypoint.
Unsigned friend names/reflection and environment strings are **not authentication**
or a security boundary against hostile code in the same process. This is an inert
test foundation, not credential authorization. Full-trust reflection could defeat
private members; no claim of resistance to such code is made.

## Native store contract

The constructor accepts only the UUID suffix, canonical nonzero lowercase UUID N;
all other strings refuse before any OS access. The private exact target prefix is
`Nayeon.P312.Disposable.`. Callers cannot supply a target, blob, API delegate,
native adapter, environment executor or production identity. Values are exclusively
the two fixed nonsecret UTF-8 synthetic constants in source. No passwords, API keys,
user input, provider calls, registry or unrelated credential enumeration is involved.

`CredReadW` collision preflight happens before any write or cleanup ownership.
An existing target refuses without blob copy, overwrite or deletion. Add repeats
absence checking under the shared writer lock, including when two instances were
constructed before either wrote. Ownership starts conservatively at attempted
`CredWriteW`; a failed write is uncertain and cannot resume effects.

The managed sequential Unicode CREDENTIALW layout is 80 bytes on x64 and 52 on
x86. Writes use CRED_TYPE_GENERIC=1 and PERSIST_SESSION=1, target-bound username,
zero flags/attributes and only a bounded unmanaged copy of the fixed bytes.
Add writes ALPHA and verifies exact readback; Replace requires ALPHA, writes BETA
and verifies exact readback; Delete requires BETA and proves absence. These checks
are synthetic store verification only, not semantic task success or service trust.
`CredFree` runs in finally for every returned pointer, including collided entries.
Managed synthetic byte arrays and allocated native buffers are cleared; bounded
native read copies used for verification are cleared before CredFree. The only
retained material strings are the fixed synthetic constants. Targets/SIDs are
metadata and never printed.

Uninitialized -> Saved -> Replaced -> Deleted is the only effect progression.
Faulted and Disposed cannot restart. Invalid state requests refuse without OS
access. A single static writer lock serializes all instances, effects, verification
and disposal. Gate, identity, native or readback uncertainty during an effect
faults the instance and attempts cleanup. Dispose deletes only an attempted,
exactly verified owned synthetic entry and proves absence; an unowned/collided
entry is never deleted. An uncertain Replace may leave either owned fixed value;
cleanup accepts either, but refuses any other data or metadata. No raw Win32 error,
blob or target is returned or logged. No finalizer performs ungated effects.

Every native effect requires the actual hosted gate and the original process SID,
with no thread impersonation and no missing/LocalSystem identity. Identity comes
from the existing service helper after hosted checks. This is the ordinary runner
principal, **not an authenticated SCM service account**. There is no cross-process
exclusive lease or atomic create-if-absent primitive in WinCred; absence checking
does not claim protection from a hostile process racing the fresh UUID. Real-key
use requires a separately approved service-owned concurrency/policy design.

## Hosted test brake and evidence

Before any WinCred P/Invoke the class requires all of:
GITHUB_ACTIONS=true, RUNNER_OS=Windows, RUNNER_ENVIRONMENT=github-hosted,
GITHUB_EVENT_NAME=pull_request, GITHUB_REPOSITORY=krismcan/Mark-LV,
GITHUB_HEAD_REF=byok-c1-p312-service-hosted-windows-vault-20261123,
GITHUB_BASE_REF=byok-c1-p311-crosslanguage-synthetic-20261123,
P312_SYNTHETIC_HOSTED_ONLY=1. Event JSON must be a regular non-reparse file under
RUNNER_TEMP, strictly less than 64 KiB, parsed with bounded JavaScriptSerializer.
The PR must be draft, source/base refs exact, root/head/base same non-fork repository
and repository ID, base SHA the exact P311 parent above. Head SHA must match the
actual checked-out local Git HEAD; Git invocation is read-only, bounded and uses
no remote. Pure predicate tests cannot substitute their environment for this path.
These strings/event files are an extra test brake and target restriction, never
production authorization. Spoofing them is not an approved way to run locally.

Pinned checkout uses exact PR head, no persisted credentials, no submodules/LFS.
Only Windows-2022 GitHub-hosted draft same-repository jobs are admitted. The brake
is set only after event validation. The workflow proves precisely the five-path
diff (4 A + 1 M), ancestry, Git regular files, disk non-reparse files, clean tree,
source/frozen-witness SHA-256 before/after and unchanged product/test binary hashes.
All unchanged product sources, P274/P270/P309/P311 witnesses and P275 inventory
are hashed. Builds use installed MSBuild/.NET 4.8 and matching installed CSC,
warnings as errors, x64/x86 Debug/Release; no downloads, restore or admin actions.
Only the friend EXE runs, with a 90-second watchdog, continuously drained stdout/
stderr and 8 KiB caps. Output is admitted only as the bounded PASS counter; raw
child diagnostics are not echoed. The service Main and SCM are never executed.
An unavailable WinCred account context fails the job; no gate may be weakened.

Tests include pure positive/negative event predicates, all wrong environment
values, non-draft/fork/wrong SHA/repository, invalid UUIDs before OS access,
actual host-gate refusal, assembly topology, real Add/ReadBack/Replace/ReadBack/
Delete/absence, existing-entry collision, late collision without deletion rights,
invalid ordering, double delete, post-dispose calls, two-thread Add serialization,
Add/dispose race, modeled uncertain-state disposal, and an actual post-Add test
brake withdrawal. The last deliberately refuses effect and cleanup, restores the
original valid brake, then proves terminal-state cleanup and target absence.
This is a controlled incident-recovery test, not a waiver of an unexpected cleanup
failure. Real token drift/impersonation and OS-fault injection remain unverified;
no account manipulation or injectable native backend is introduced for them.
`--readonly` explicitly runs no effects; the workflow uses no arguments, so native
tests cannot silently skip. Neither mode was executed on Kristian locally.

| Evidence | Current status |
| --- | --- |
| P311 cross-language baseline | User-reported hosted 10/10 x64 and 10/10 x86 PASS; inherited, not P312 evidence |
| Local CSC compile-only | Actual product project source list and referenced friend EXE compiled x64/x86 Debug/Release, warnings as errors; no EXE execution |
| Workflow embedded PowerShell | Both run blocks passed local PowerShell AST parsing; not a YAML engine or hosted execution result |
| Project and exact source scope | Project XML inspected; only the approved compile/reference entries added; five paths and empty index checked locally |
| Actual project MSBuild / runtime matrix | HOSTED PENDING; local compilation used installed CSC with the project source/reference list |
| P312 real WinCred operations and synthetic deletion | HOSTED PENDING; not executed by Codex |
| Qualified production reviews / three full regressions | 0/7 and 0/3; HOLD |

Every success requires disposal and fresh-constructor absence checks for test
targets. Normal exceptions attempt verified deletion in finally/Dispose. An
unexpected cleanup error fails with HOLD. A hard process kill, identity loss or
runner loss can prevent cleanup; no unconditional crash-cleanup guarantee exists.
Do not rerun a failed job as if it proved deletion: retain run ID, architecture,
configuration and source/binary hashes, record a cleanup incident without target/
blob disclosure, retire the disposable hosted runner/session, and obtain review.
Session persistence and runner disposal bound residual synthetic data; they are
not evidence of successful CredDeleteW. No success may be claimed for that run.

## Open Failures & Prior-Issues Review

| Issue / source | Severity and cause | Boundary / evidence / containment | Review and disposition |
| --- | --- | --- | --- |
| P96, inherited P311 review and explicit P312 instruction | HIGH, original revocation/effect race unresolved | Real effect admission can outlive revocation; no reproduction or repair claimed here. No production caller reaches this adapter. Synthetic lock does not fix authorization atomicity | Independent closure absent; production HOLD |
| P292 x86 SCM teardown, inherited P311 review | UNKNOWN root cause | Actual SCM cleanup evidence missing; ordinary hosted user process cannot establish SCM cleanup. No lifecycle/pipe/identity changes; no SCM execution | Unresolved; production HOLD |
| P275 frozen effect inventory | New native import topology, review required | Actual product now includes CredWriteW/ReadW/DeleteW/Free. Existing inventory is frozen and may reject this addition; it is not run or weakened to claim a false no-native-effects PASS | Later effect-inventory/P96 audit required before any integration; HOLD |
| Hosted WinCred context / cleanup | Unverified until native matrix runs | Missing credential store, unexpected OS errors or cleanup failure must fail; no local probe or fallback | Hosted pending; HOLD |
| Current-state mismatch | Stale cross-branch handoff | Git confirms exact requested clean P311 parent; five-path scope excludes context edit | Disclosed; no milestone-state claim |
| Qualified reviews / full regressions | Missing evidence, not inferred from synthetic tests | 0/7 reviews, 0/3 full product runs; no independent review claimed | Production HOLD |

Source dependency audit is bounded to the requested product sources, P274 layout,
brief P270 witness, P311 review/workflow and relevant tests. It is not a historical
security reassessment. P274 compile/test enforcement and frozen P275 remain intact.
The only new native path is isolated friend test -> actual assembly adapter ->
private WinCred imports after actual host and SID checks. Production Permission ->
Policy -> Confirmation -> Execution -> Verification has not been connected to it.

Next integration must preserve atomic revocation/effect ordering, authenticated
peer, explicit consent, service-owned protected-store policy, audit and verified
cleanup before any real key. No real key, user credential, provider network,
production release, seal, stage, commit, push, merge or tag is authorized here.
No workbook/dashboard update until full BYOK completion.
