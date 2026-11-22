# P306 synthetic service transaction — BUILD FIRST / production HOLD

2026-11-22. Sole source writer; isolated branch
`byok-c1-p306-synthetic-service-transaction-20261122`, verified clean starting
HEAD `efbd05757b364c9bebda079dec6131867d04b79d`. No tag points at that HEAD.
`.codex/CURRENT_STATE.md` describes an older unrelated checkpoint; Git is
authoritative. It remains byte-identical under the explicit P306 path restriction.

## Actual product composition

The .NET Framework 4.8 service project compiles the new internal
`SyntheticTransactionOwner`. `CustodyService` owns it as a private member,
constructed only after both existing executing-identity verifications and
BeginStart, before status IPC. No IPC dispatch or external transaction API is
added. P304 readiness, permission denials, identity checks, and P305 status
bytes, endpoint, ACL, client and server sources are retained.

This is a transaction admission/cancellation skeleton with **no effect stage**.
Add/Replace/Delete are explicit enum values, not interpreted commands. Immutable
request metadata contains only owner GUID, epoch, nonzero increasing unsigned
request identity and operation kind. No payload is marshalled, accepted or stored.
Results retain immutable nonsecret metadata and disposition; Allowed always
returns false. There is no grant value, configurable policy, injected callback,
effect adapter, credential API, provider, persistence or queued work. Even valid
synthetic input terminally denies. Adding an execution path requires a separate
approved design; this class has no dormant authority to enable.

One lock linearizes Deny, Cancel, observation and terminal lifecycle changes.
Valid metadata reserves its request identity before returning Denied or Cancelled.
Cancel consumes an identity just as denial does; it cannot undo a completed denial
or reopen work. Duplicate and lower identities return Replay, including attempts
with a different operation. Invalid operation, null/zero request, wrong owner and
stale epoch refuse without consuming the valid owner's identity. Owner closure
takes precedence over every kind of input. These are denial reasons, not grants.

Replay tracking uses one unsigned high-water mark, with fixed memory and no
eviction or arithmetic increment. Callers must serialize increasing identities;
out-of-order requests intentionally deny as Replay. The maximum value exhausts
that lifetime's fresh identities and cannot wrap. No unbounded GUID history is
retained. A new owner has a new GUID, rejects old requests and grants nothing.
The GUID is correlation metadata, never authentication or a capability.

Epoch 1/ActiveDenied becomes epoch 2 on the first Stop, Shutdown, Fault or Dispose.
There is no restart or later epoch. The first terminal cause is retained until
Dispose promotes state to Disposed; repeated/conflicting closure never advances
the epoch again. Old result objects remain immutable historical observations.
Service Stop/Shutdown/Dispose cancel before pipe cleanup. Startup catch faults
the owner before cleanup; even a pipe timeout cannot leave it active. Both
managed and non-managed Dispose paths cancel metadata ownership. No cancellation
tokens, callback registrations, workers or handles are added by P306.

## Open Failures & Prior-Issues Review

**GO only for the explicitly authorized effect-free source build. Production
HOLD; real-key NO-GO.** No historical finding is repaired or waived here.

| Issue / severity / source | Root cause, affected boundary and reproduced evidence | Containment, tests, review and disposition |
| --- | --- | --- |
| Retained P96 HIGH; inherited P304/P305 reviews, reviewed 2026-11-22 | Historical post-check revocation/effect race. No historical implementation imported, called, modified or inspected for this task. No new reproduction or closure evidence. | P306 has no effect stage or callback; serialized terminal denial/cancellation tests added. Independent review pending. Original HIGH remains open; real custody HOLD. |
| Retained P292 HIGH / teardown uncertainty; inherited P304/P305 reviews | x86 teardown/deletion-absence evidence remains UNKNOWN. Restricted token observation does not prove protected-store ownership, approved principal or qualified SEC03/04. No reproduction claimed. | No P292 dependency, SCM installation, privilege or store operation. No teardown remediation claim. Qualified review still required; HOLD. |
| Historical P304 source-evidence defect / material assurance issue; P304 review | First hosted run tested merge HEAD rather than exact product source HEAD. Old passing count cannot authenticate new source. | Dedicated workflow checks same-repo draft PR, exact base ref/SHA, head ref/SHA and exact head checkout; source and product hashes before/after. P306 hosted proof pending; assurance HOLD. |
| Historical packaging/tool failures; P304/P305 reviews | Relative legacy compiler paths and checkout PowerShell property assumptions caused earlier failures. No new product failure inferred. | Absolute test compiler paths; installed tools only. Local compile succeeds. No package acquisition or retry workaround. Project targeting pack absent locally; hosted MSBuild pending. |
| Runtime, security and full-regression evidence missing / release blocker | Compile/static evidence cannot establish Windows race outcomes, SCM identity custody or architectural safety. | P306 and inherited P305/P304 hosted tests prepared. Independent approvals **0/7**; full regressions **0/3**. SEC03/04 audit deferred until functional build; production HOLD. |

Dependency audit: service identity validation → private metadata owner, alongside
unchanged status IPC and lifecycle coordinator. Status IPC has no transaction
route. Legacy credential owners, UI, stores, other processes, windows and restart
recovery are not reachable from P306. Internal friend visibility supports tests
of the actual assembly; it is not an OS security boundary or authorization.
Unknown legacy root causes remain held outside this effect-free scope. A new
material defect in the affected paths requires STOP and an exact finding.

## Tests, workflow and evidence

New tests reference the separately compiled actual product assembly; no copied
transaction implementation. They cover all operations, malformed metadata,
invalid enum extremes, zero/max identities, cross-owner and stale-epoch requests,
monotonic replay, immutable snapshots, invalid-input sequence poisoning, duplicate
deny/cancel races, all four terminal causes, concurrent disposal, invalid floods
and new-owner rejection of old requests. Each race has bounded waits. Reflection
tests insert only this effect-free owner into an **unstarted** service object to
check real Stop/Shutdown/Fault/Dispose wiring, including Dispose(false). The
startup-negative uses invalid arguments to refuse before native identity checks.
These fixtures do not attest successful service startup or bypass identity to
execute anything. The constructor is checked to have no pre-identity owner.

Dedicated hosted Windows workflow builds x86/x64 Debug/Release, runs P306 plus
unchanged P305/P304 affected tests against that same product assembly, logs input
SHA256 and product hash, rejects mutation, and checks HEAD/index/worktree before
and after. Each test executable has a 30-second deadline, each job eight minutes.
Only test executables run; the service executable is loaded as a referenced
assembly. No SCM dispatch/installation occurs. P305's affected suite uses ordinary
runner-owned temporary pipes; it adds no credential operations. P304's unchanged
negative Main tests first establish an OS context where dispatch must refuse.
Workflow publication/execution is not authorized or performed by this task.

Local compile-only: installed Framework64 v4.0.30319 csc, warnings as errors,
all four architecture/configuration combinations, actual product plus three
referencing test executables (16 successful compilations). Outputs:
`C:\Users\krist\AppData\Local\Temp\nayeon-p306-final-compile-48a6d338cb52455da5e25108f31dfca2`.
This final compile includes Dispose(false) cancellation and test coverage.
Project XML parsing, exact explicit compile-item inventory, both workflow
PowerShell blocks' AST parsing, tracked `git diff --check` and new-file whitespace
checks pass. These static checks do not claim hosted YAML execution or runtime
results. Final scope check confirms only the six authorized candidate files
differ; all other inherited tracked files, including P304/P305 tests and
CURRENT_STATE, remain byte-identical. Index remains unchanged and empty of changes.
No binary ran on Kristian. The v4.8 targeting pack and MSBuild command are absent
locally, so this is syntax/reference evidence against installed runtime assemblies,
not a verified project build or runtime PASS. No downloads or installations.

No staging, commit, push, tag, merge, workbook or dashboard update. Candidate
remains unsealed. Next: human review and separately authorized exact-head hosted
validation, then qualified independent review; real keys remain NO-GO.
