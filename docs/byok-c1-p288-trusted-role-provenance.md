# P288 trusted role provenance architecture candidate - 20 November 2026

**NONDEPLOYABLE / SYNTHETIC ONLY. Live architecture admission HOLD.**
Real keys NO-GO; production HOLD; qualified external approvals **0/7**;
accepted full-product regressions **0/3**. This candidate closes no security
finding, creates no live issuer and requests no milestone seal.

## Custody, scope and retrospective disposition

Initial inspection FIRST confirmed a clean worktree/index, branch
`byok-c1-p288-trusted-role-provenance-20261120`, exact inherited HEAD
`3edf7130daa41c2ac240f9a92d6745ac5a726eaa`, no tag at HEAD and 1,162 tracked
files. Its sole parent is P286 `bf96a2a5d6570da7397770445967fa2434dd9008`.
P287 draft PR #207 and passing hosted x64/x86 evidence are user-supplied
baseline facts, not fresh remote retrieval or P288 evidence.

`.codex/CURRENT_STATE.md` still describes November 3 Phase 10.2 work. Git is
authoritative for this checkout. The explicit P288 inherited-path freeze
controls: no historical context or completed P287/P286 checkpoint is edited.
This is a review candidate, not a completed product phase/context promotion.
The engineering failure gate was read before implementation. No separate
OM v2.1 text was present in the bounded tracked-path inventory; no uninspected
OM sign-off is claimed. The specified five-minute stall watchdog applies.

Exactly five additive regular files:

| Path | Purpose |
| --- | --- |
| `native_c1_successor/P288SyntheticProvenanceSequence.cs` | Isolated synthetic sequence and unconditional live refusal |
| `tests/p288_provenance/ProvenanceSequenceTests.cs` | Adversarial synthetic event/lifetime/ticket tests and unchanged P287/P286 focused suites |
| `tests/p288_provenance/HostedReview.ps1` | Hosted-only exact-source/compile/test custody, never executed locally |
| `.github/workflows/p288-windows-provenance-sequence-review.yml` | Draft-only Windows-2022 x64/x86 review preparation |
| `docs/byok-c1-p288-trusted-role-provenance.md` | Architecture audit, failure ledger, evidence and acceptance checklist |

No runtime integration, service provisioning, credential operation, provider
access, impersonation, privilege/ACL/policy mutation, workbook/dashboard update,
staging, commit, rebase, merge, amend, tag, push or workflow launch is performed.
Only this worktree and disposable local compiler receipts are written by one
implementation writer. Generated test EXEs are not run on Kristian.

## Open Failures & Prior-Issues Review

All entries reviewed 2026-11-20. References are frozen inherited source/review
documents unless explicitly labeled user-supplied. Independent acceptance of
this P288 candidate is **OPEN**, never supplied by this author's inspection.

| Issue / severity / source | Root cause, affected routes, reproduction/evidence, containment and disposition |
| --- | --- |
| Live service/client binding / HIGH architectural missing evidence; P279/P282/P287 source | SCM configuration/status and token snapshots are not a continuous executing-service capability. P287 has no authenticated live client issuer. P267/P286 development uses the current developer SID, which cannot fill both production roles. P288 adds no live issuer. Compiled tests cover role/same-SID, SCM/PID/birth/token/logon/session, handle and peer mismatches only in a private world. Runtime/independent acceptance OPEN; live admission HOLD. |
| P265 callback crash / historical HIGH development blocker; P286 review | Caller-owned event disposal could precede Framework signaling after disposed-stream End* precheck. Connect/read/write share that route. P286 moved End*/event cleanup into the completion callback, followed by monitor publication. User reports verified P286/P287 hosted results. P288 compiles and schedules the unchanged managed completion suite via unchanged P287; no old callback code is copied or edited. Fresh P288 hosted evidence pending. No production closure inferred. |
| P96 original revoke/effect race / HIGH OPEN; P267/P279 reviews | Historical final-check/effect paths lack a shared owner across alternate callers. P267's integer-only synthetic owner and P288's monitor do not repair original production routes or kernel TOCTOU. Original negative and implementations untouched; production HOLD. |
| Service account policy / HIGH OPEN; P279 review | Original LocalSystem host assumptions conflict with proposed virtual-service account policy; SEC03/04, installed image trust, profile/store ownership and rollback/custody proofs absent. No policy resolution or store work in P288. HOLD. |
| P76/P211/P216 historical acceptance / unwaived OPEN; P279/P282 reviews | Earlier modern-test failures and retired direct native Python credential-effect expectations remain unwaived. Not rerun, repaired, downgraded or hidden here. Root-cause/closure authority remains with the existing gates. HOLD. |
| P282 frozen-source/test repair history / material prior incident; narrow-repair review | A historical negative depended on a rejected P270 modification. Frozen P270 was restored and the replacement targets the P282/P271 seam. P288 does not change either route or claim independent closure. Whole inherited-tree raw-byte checks protect all affected old entrypoints. HOLD for broader admission. |
| P288 static classification mismatch / pre-runtime candidate defect, contained | Author inspection found role swapping also replaces modeled handles, so lifetime-first classification disagreed with the role-negative expectation. Structural role/identity checks now precede handle continuity checks; the exact role-swap and independent handle-replacement expectations remain. No runtime failure or closure claimed. Fresh final-source compile and hosted tests/independent review required. |
| Local tools / environment | `rg` is unavailable; Git path/search commands used instead. One initial read used a nonexistent workflow filename; corrected to the tracked path. Neither changed source nor ran tests. No compiler failure, installation or workaround inferred from these read-only tool errors. |

Disposition: **GO only for the explicitly authorized isolated synthetic candidate
and source/compiler review; HOLD for live admission, security closure, production
progression and seals.** Existing material gaps are contained by unconditional
live refusal, not deferred as low risk or treated as fixed by green compilation.
No full product regressions are run on Kristian; that explicit task restriction
controls this unsealed candidate and leaves the full-regression gate OPEN.

## Source and actor trust map

| Inspected source / actor | Observation and boundary |
| --- | --- |
| P267 `DevelopmentAtomicService.StartDevelopment` | Captures current Windows identity, rejects thread identity and service/system principals, constructs development adapter. Its fixed integer submission, worker loop, startup and disposal are development paths; Main does not dispatch SCM. Never a production role issuer. |
| P286 `DevelopmentPipeAdapter` | Current-developer SID owner/peer; its constructor really creates a development pipe, and ServeOnce uses RunAsClient. P288 never constructs the adapter or calls ServeOnce. Only its private managed Completion helper is exercised by frozen tests on hosted review. End* and completed event cleanup stay callback-owned after Framework signaling; waiter timeout cannot take event ownership. |
| P279 -> frozen P261 -> SCM/process/token | P261 configuration observation precedes SCM status, OpenProcess and OpenProcessToken. Own-process/running PID and TokenUser match are rechecked with handles retained. Handles are then closed; resulting evidence is diagnostic, all grants false. A service name/configured SID does not prove who executes P288. |
| P282 `ObserveProtectedService` | Captures its own primary token and checks no thread token, canonical service SID, session zero, SCM PID == actual PID, and token-statistics continuity. No live transferable capability, retained lifetime or pipe binding is returned. SyntheticRunnerBinding is a separate disposable-runner restriction, not a service issuer. |
| P271 `OpenProtectedService` | Calls P282 DemandProtectedStore, which observes and always throws LedgerBlocked before protected witness construction. RequireHosted/constructor binds synthetic runner separately. Neither this route nor diagnostic success can enter P288 live admission. |
| P287 boundary/fixture | Live observation always MissingTrustedLiveProvenance; demand always throws. Positive issuer is private fixed synthetic role/ACL data only. P288 never wraps or promotes it to live provenance; frozen tests retain role/issuer/ACL adversaries. |
| P288 private world | Independent fixed service/client actors, object references modeling retained handles, fixed pipe endpoint and connection, modeled peer/message observations. Only synthetic enum events/faults are accepted; no snapshot fields, strings, bool approvals, GUI or wire claims are accepted as a live issuer. |
| P288 synthetic ticket | Exact pending object, private fixture issuer, connection object and revision must all match. Forged receipts and tickets cannot change live refusal. No live consumer exists. |
| Model/GUI/callback/environment | No execution authority. Hosted flags prevent accidents only. Positive sequence/ticket use requires the original Thread object; a callback cannot inherit it. Cross-thread cancel/revoke/disconnect/expiry are terminal-only signals, never positive issuance. |

The inspected route graph is observation/test-only; no new call edge enters
P267, P271, production Nayeon, P96, a service, a provider or a secret store.
Old routes remain frozen, including separate constructor/start/restart/worker/
callback paths. P288 has no process-global registry or restart persistence.

## Windows observations that a future design could use

These are documentation-supported building blocks, **not implemented P288
issuers**. Sources were read from Microsoft Learn on 20 November 2026.

| Read-only building block | What it supplies / what remains unproved |
| --- | --- |
| SCM query/configuration and [QueryServiceStatusEx](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryservicestatusex) | Most recently reported service status; reporting may lag. PID validity depends on service state. Restrict to the reviewed own-process/running case. SCM status is not an atomic execution lease. |
| Retained process handle, [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes), executing self vs SCM comparison | Creation time plus owned process-handle lifetime can detect many substitutions. [Handles remain valid after process termination](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers); liveness must be checked separately. Neither PID nor birth-time equality alone authenticates a role. |
| [OpenProcessToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocesstoken), GetTokenInformation(TokenUser/TokenType/TokenSessionId/TokenStatistics) | Query the token attached to the retained process. Least query rights, denial and cleanup must be explicit; do not enable privileges to force access. [TOKEN_STATISTICS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_statistics) distinguishes TokenId, AuthenticationId and ModifiedId. Logon LUID and interactive session ID are separate. Token expiration time is unsupported and is not an expiry policy. |
| [GetNamedPipeClientProcessId](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid) / [GetNamedPipeClientSessionId](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientsessionid) on the exact connected server instance | Kernel-associated peer PID/session observations. No token, birth, user presence, permission, consent or connection-lifetime capability is supplied by these APIs. Opening a PID later introduces a gap; reconnect/duplication/handle transfer must be addressed. |
| [OpenThreadToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openthreadtoken) | Query ambient thread identity separately. Only explicitly established absence may support process-context use; anonymous/denied/query failure cannot fall back to process identity. No impersonation is performed in P288. |

**Key missing proof:** a connected process's primary token need not equal the
effective token used by its connecting/writing thread. Pipe PID/session plus
OpenProcessToken cannot authenticate that message security context. The documented
[ImpersonateNamedPipeClient](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-impersonatenamedpipeclient)
route concerns the last message read and changes server thread identity. It is
**not a read-only query**, is prohibited in this task, and is not invoked by
P288. A future authenticated design must separately approve its mechanism,
message framing, impersonation level, failure behavior, restoration and thread
ownership. No fallback to service identity after capture/revert failure is safe.
Choosing a different authenticated protocol also needs a new reviewed design.

Inference from these API contracts and the inspected source: no existing
kernel/SCM/process-handle/pipe-peer composition here can issue a trusted live
service-and-client capability. Repeated snapshots reduce ambiguity but do not
close unsampled ABA changes or the final observation/use gap. No user-provided
SID, SCM name, environment switch, stale PID, account display name, synthetic
issuer or P282 status can repair that absence.

The endpoint bootstrap ordering is also unresolved: peer queries require an
already created/connected pipe. Future reviewers must separately authorize
minimal endpoint creation from executing-service provenance and independently
gate every authenticated client operation. Requiring peer proof before any
endpoint exists is not a justification to bypass P287/P288 creation refusal.

## Synthetic proof step and its limits

The fixed sequence is ServiceObserved -> ConnectCompleted ->
MessageReadCompleted -> PeerAuthenticatedAfterRevert -> FinalRevalidation.
These names describe synthetic events, not OS calls or actual authentication.
All stages recheck private modeled actors/lifetimes. Only the last stage issues
an exact one-use synthetic ticket. Consumption rechecks every modeled boundary
under the same monitor, reserves the ticket and returns an enum; it performs
no action and accepts no effect callback. Every authority property remains false.

Wrong/skipped/duplicate/undefined events, forged/cross-fixture tickets, role/SID
swap, same SID, SCM/PID/birth changes, token/logon/modified/session changes,
nonprimary tokens, closed/replaced service/client/pipe handles, exited processes,
endpoint substitution, mismatched peer/message fields, ambient thread identity
and query failure permanently poison the fixture. Stop events never reset it.
No reconnect resumes a prior lease; a new fixture requires the whole sequence
and a new ticket. Receipt replay, cancellation and cross-thread transfer deny.

Fault injection latches immediately, even if fixture values are restored before
the next use. **This is a synthetic oracle assumption. No live notifications,
retained SafeHandles, authenticated peer token, OS-atomic lease, monotonic trusted
clock or revocation feed exists.** A managed monitor cannot stop external Windows
token/service/pipe changes. The cancel-before/after-consume schedules establish
only ordering of the enum result, never effects or P96 closure. Expiry is an
explicit terminal test event, not a trustworthy elapsed-time implementation.

Inherited P287 tests cover protected exact detached ACL owner/ACE comparisons,
overbroad client/server-instance rights, broad principals, missing deny ACE and
owner/protection tampering. [Windows pipe access rights](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights)
require explicit review; default ACLs or generic-write masks must not be assumed
safe. P288 creates/applies no machine ACL. P287's in-memory ACL remains detached
test data and is not accepted by the P288 sequence or any live transport.

## Hosted review contract and local validation

The proposed workflow requires a same-repository **draft** PR with exact P287
base SHA/ref and the exact P288 head ref above. It checks out the authenticated
event's immutable head SHA; the script requires HEAD == that exact SHA, one
parent == the literal P287 SHA, exactly five additions and no other delta. A
future candidate SHA is not invented before an authorized commit. Wrong base,
head, history, fork, nondraft, runner, architecture or source custody refuses.

All 1,162 inherited tree entries and raw on-disk blobs must match P287; all
1,167 final entries must match the PR tip before/after. No links/reparse paths,
untracked/ignored/staged changes or source drift are admitted. Checkout/upload
actions are pinned to immutable SHAs; permissions are contents:read only;
credentials are not persisted. No secrets, package restore, downloaded compiler,
provider or custom network call is used. Execution is restricted to disposable
Windows-2022 hosted x64/x86, three trials each. Environment flags are accident
barriers, not identity proof or a security sandbox against a malicious workflow.

The sole executable compiles new model/tests and unchanged P287 source/tests
plus unchanged P286 source/tests. Runtime invokes the complete P287 focused
harness (which invokes P286's managed completion tests), then P288 negatives.
No P286 development pipe constructor/ServeOnce, P282 live observation, P284
native pipe stress or full product suite is invoked. Compile guards require
DEBUG, isolated assembly, and each P288/P287/P286/development opt-in; RELEASE
is rejected even with DEBUG. Eight negative configurations per architecture
require raw exit 1, the named CS1029 guard and no executable. Positive builds
require raw exit 0 with warnings treated as errors. Runtime exit, exact bounded
receipt structure, architecture and case/assertion floors are mandatory.

Runtime child watchdog is 60 seconds with disposable process-tree teardown on
timeout; job watchdog is ten minutes. Eight explicitly named text receipts only
are uploaded: source-before/after hashes, compiler codes/raw-log hashes, raw
compiler exits, binary hash, runtime exit, sanitized runtime receipt and scope.
Unexpected stdout/stderr is redacted; raw compiler diagnostics and binaries
stay outside artifacts. A failure remains red/HOLD, never continue-on-error.

Final-source local Framework64/Framework compiler smoke used absolute input
paths and `/nologo /noconfig /warn:4 /warnaserror+ /target:exe`, exact
ProvenanceSequenceTests entrypoint, architecture and six required defines.
**Two positive raw exits 0; sixteen expected negative raw exits 1**, each with
the specific named CS1029 guard and no negative binary. The negative matrix is
ALL defines absent, RELEASE added to DEBUG, and each of the six defines absent,
on x64 and x86. Input SHA256 manifests match before/after. These are compiler
results, **not test passes**. Earlier compiler iterations and raw diagnostics
are preserved separately; no generated assembly or hosted script was executed.

Final compiler receipts:
`C:\Users\krist\AppData\Local\Temp\nayeon-p288-review-6d7106b3568e4168b4a0db0153df8ece\final-source`.

| Receipt | SHA256 |
| --- | --- |
| `raw-exits.txt` | `53D2A6EA876739F67FE42456A81801329F1A5699931342D70FD93CCA370E2C35` |
| `binaries.sha256` | `23D7892457D189D6FE1247632A1624FDBE275B38F6CF978D56A9890F826431DD` |
| `compile-input-before.sha256` (same content as after) | `9F535F6FCB66DF134F713E82A286B439EFDADAE5FE87B33AE9146F065048A128` |

The parent evidence directory holds full inherited raw-byte/SHA256 checks,
static receipts and the final five-file SHA256 manifest (including this doc;
no recursive self-hash). All 1,162 inherited disk blobs match HEAD; zero tracked
or index changes are permitted. Hosted script AST parsing reports zero errors;
source checks find the required workflow/ref/source controls and no model native
or effect API. These static checks do not execute adversarial workflow events.
`git diff --check` raw exit 0; per-addition `git diff --no-index --check` against
an empty file gives expected difference exit 1 with zero whitespace diagnostics.

Hosted P288 runtime **0/6**, independent source/architecture acceptance **OPEN**.
No synthetic case count is claimed as a pass before hosted execution. Three
full-product regressions remain **0/3**; production and real-key admission HOLD.

## Acceptance checklist before any real service IPC

Every item is OPEN and needs independent CTO/security acceptance; this candidate
is not an implementation approval for these later scopes.

1. Resolve/contain all relevant historical failures with qualified owners, raw
   evidence and explicit gate decisions; preserve P96 HIGH and P76/P211/P216
   blockers until actual independent closure. Refresh failure review before any
   live phase or seal, not from synthetic pass counts.
2. Specify a nonforgeable executing-service issuer: approved SCM configuration,
   actual executing self process/token, canonical service principal, installed
   image/binary trust, no ambient impersonation, handle ownership, birth/liveness,
   token/logon/session continuity and complete query/cleanup-failure behavior.
3. Specify a separately authenticated connection/message-client issuer from a
   kernel peer or approved authenticated protocol. Distinguish process primary
   token from effective connection/message token and prove intended interactive
   principal, logon/session and endpoint/service binding. Same SID, remote peer,
   anonymous/low-level impersonation, shared identities and wire claims cannot
   substitute. Identity alone grants neither user presence nor consent.
4. Solve endpoint bootstrap and instance ownership, restrictive exact ACL/rights,
   local/remote restrictions, first-instance/squatting, duplicated/inherited/closed
   handles, process exit/restart/PID reuse, service reconfiguration, reconnect,
   thread handoff and unsampled changes. Define revalidation at every use and
   an authority owner that closes the final TOCTOU gap; document what Windows
   cannot prove and fail closed rather than inventing a lease.
5. Preserve callback-owned End*/event cleanup for connect/read/write, total
   deadlines, cancellation, late completions, reentrancy limits, revocation and
   one-use replay bounds. Independently prove native lifecycle behavior on
   disposable runners, including negative schedules; no callback carries live
   role authority by association with an APM completion.
6. Independently approve any token impersonation/capture/restoration mechanism
   and failure containment. No protected work under peer impersonation or failed
   revert; no privilege adjustment or process-token fallback to force success.
7. Separately establish permission -> policy -> confirmation -> execution ->
   verification, user-present one-use consent, P96/recovery/antirollback,
   service-owned profile/DPAPI/store ACL and retained-handle custody, SEC03/04,
   secret boundaries and qualified external approvals. None follow from IPC.
8. Obtain exact-byte independent architecture/source/security review and six
   focused hosted trials with untouched P287/P286 evidence. Complete separately
   authorized affected/cross-phase and three full-product regressions before a
   seal; follow human review, exact staging, seal-time checks and explicitly
   approved Git publication. No workbook/dashboard update until all BYOK C1 is
   complete, as directed.

Recommended next review: Nayeon CTO/independent reviewer inspects these five
exact files, source/actor map, synthetic-oracle and bootstrap limitations,
event/handle/ticket adversaries, preserved callback ownership, event-head/source
guards and sanitized receipts. Only then arrange controlled hosted review.
**Live admission, credentials and production remain blocked regardless of its
synthetic result.**
