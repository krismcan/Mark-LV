# P307 service-owned synthetic denial — production HOLD

Date: 2026-11-23. Source parent: `bb55b1facb9f5d6e4f068c57165f3059e181af81`.
Branch: `byok-c1-p307-service-owned-denial-port-20261123`.
This is an uncommitted, synthetic-only implementation candidate, not a seal.
The branch and pristine starting worktree matched the requested parent. The
existing `.codex/CURRENT_STATE.md` describes older Phase 10.2 work and is not
the P307 source authority; it is unchanged under this five-path scope.

## Bounded change

The actual `CustodyService` now owns internal typed `RefuseSyntheticRequest`
and `CancelSyntheticRequest` handlers. Both hold its existing private lifecycle
lock for the complete gate and owner call, serializing with startup, stop,
shutdown and both disposal paths. Only `!terminal`, coordinator state
`ActiveDenied`, and a non-null transaction owner permit forwarding to the
existing owner's `Deny` or `Cancel` method. Every result has `Allowed == false`.

A refused service gate constructs an inert `OwnerTerminated` result retaining
the input request, with empty owner identity, epoch zero and `Stopped` as a
sentinel. These fields do not report the actual owner's lifecycle. Refusal
does not observe, cancel, deny, reserve an ID in, or otherwise mutate the owner.
When the service gate passes but the owner is already closed, the unchanged
P306 owner returns its own terminal result and identity. No owner is created
by either handler. P306 sequencing, validation and termination semantics are
unchanged; its only source addition is the P307 friend-test assembly attribute.
P304/P305 lifecycle, identity checks, status IPC and all prior tests are unchanged.

There is no payload/effect port, credential access, WinCred, DPAPI, provider,
new IPC, SCM action, or installed service execution added by this change.

## Test and CI boundary

`P307.ProductService.Tests` references the actual compiled product executable;
it does not compile a substitute owner or service into the tests. Reflection
composes effect-free metadata in an **UNSTARTED** service. Its synthetic
`ActiveDenied` fixture is never evidence of valid OS startup or authorization.
The sole `OnStart` test route supplies invalid arguments, which refuse before
the service handle or native identity checks, matching the inherited P306
negative-test approach.

Coverage includes Created, Starting, Stopped, Faulted, Disposed, absent owner,
terminal flag independent of coordinator state, unknown enum states, and
closed owners. Refused service gates are checked for unchanged coordinator,
terminal flag, owner identity/epoch/state and sequence high-water mark, followed
by a valid owner probe proving the refused maximum ID was not consumed.
The active fixture exercises malformed metadata, each operation, duplicate
IDs across both handlers and operations, monotonic replay, saturation, stale
epochs and foreign owner identities. Bounded races cover stop, shutdown,
managed/non-managed disposal and early startup refusal, including forced
closure while contenders wait on the actual private lifecycle lock, duplicate
contenders and concurrent repeated closures. Waits are bounded; CI adds a
30-second process deadline and bounded cleanup.

The new workflow copies/adapts P306, uses GitHub-hosted Windows 2022 only and
the x86/x64 × Debug/Release matrix. It requires a same-repository draft PR
from this P307 branch to `byok-c1-p306-synthetic-service-transaction-20261122`
at exact base SHA `bb55b1facb9f5d6e4f068c57165f3059e181af81`, checks out the
exact PR head SHA with a pinned checkout action and no persisted credentials,
and checks ancestry, the exact five-path change scope and checkout identity.
It builds the actual .NET Framework
4.8 project with warnings as errors. Only hosted CI runs P307 and unchanged
P306/P305/P304 tests. It records source SHA, input SHA-256 hashes, product
SHA-256, per-test checks/exit status and post-run source SHA/hash stability.
The synthetic-only and hosted-runner guards precede execution. Inherited
P304's negative OS-context proof remains required before its Main-refusal test.
No SCM or real-key test is authorized.

## Open Failures & Prior-Issues Review

| Issue | Severity / known evidence | Root cause and affected boundary | Repair / evidence / review | Disposition |
| --- | --- | --- | --- | --- |
| Prior P96 | HIGH, carried forward from the supplied task; not re-reproduced in this bounded compile-only task | Historical root cause and affected callers are not established by the targeted P307 files | No closure or independent approval claimed; original incident evidence and cross-entrypoint review still required | HOLD |
| Prior P292 | Unresolved, severity not independently established here | Historical root cause, alternate routes and restart implications remain unverified here | No repair or closure claimed; original findings, adversarial reproduction and independent review still required | HOLD |
| P307 service ownership gap | Baseline source has private owner composition/closure but no typed service denial/cancellation handlers | Calling owner methods alone does not prove service lifecycle admission | Handlers now gate and forward under the actual service lock; new adversarial test source prepared; runtime evidence pending hosted CI | Candidate implementation only; production HOLD |

The user authorized this bounded implementation while requesting that unresolved
history remain visible. This is no finding downgrade, deferral approval, failure
closure, phase GO or security seal. Unknown historical causes and missing runtime
evidence continue to block production advancement. No broad historical scan or
independent review was performed or represented as complete.

## Validation and acceptance status

On KRISTIAN, all **20 compile-only invocations passed, exit 0**, using the
installed architecture-specific Framework/Framework64 `v4.0.30319/csc.exe`
compilers at warning level 4 with `/warnaserror+`. Each of x86/x64 ×
Debug/Release compiled the product from the unchanged project's exact five
source entries, then P307 and unchanged P306/P305/P304 test assemblies against
that actual product executable. Debug/release optimization, symbols and
constants were selected explicitly. No generated product or test executable
was invoked. No compiler or package was installed or downloaded.

The standard .NET Framework 4.8 reference-assembly path is absent on this host.
These local checks use the installed framework compiler/references, not an
authoritative .NET 4.8 project/MSBuild validation. The hosted workflow must
still perform the actual v4.8 project build and execute the tests. Compiling
tests does not verify their assertions.

Compile logs, output hashes and the aggregate record are retained outside the
worktree at
`C:\Users\krist\AppData\Local\Temp\nayeon-p307-compile-dead620db1d54e3d87723b053c450429`.
`compile-evidence.txt` SHA-256:
`F3126775CE45C3BB8723FC3C03CE1854F0BDD25BF81F5F90AA0884D258FC8D65`.

Static checks passed: both workflow PowerShell run blocks parsed with zero AST
errors (2/2); project XML parsed and retained target `v4.8` and warnings-as-errors;
all eight protected project/lifecycle/IPC/P304-P306 test/P306 workflow Git blobs
matched the parent; only the exact five authorized paths changed; index empty;
branch and HEAD unchanged; `git diff --check` plus the three untracked-file
whitespace checks emitted no diagnostics. The initial new-file check wrapper
mistook `git diff --no-index --check`'s difference exit 1 for a whitespace
failure; the corrected wrapper accepts that exit only with no diagnostics.
This was a validation-wrapper issue, not a source failure or waived check.

- Independent approvals: **0/7**.
- Full regressions: **0/3**.
- Hosted P307/P306/P305/P304 runtime matrix: **not run in this task**.
- **REAL-KEY NO-GO. Production HOLD.**
- No stage, commit, push, PR, tag, merge or workbook update authorized or performed.
