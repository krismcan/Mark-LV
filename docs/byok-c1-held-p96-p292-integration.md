# Held P96/P292 source integration — 25 November 2026

This is the single consolidated held-failure remediation assignment, not a new
product phase, release, seal or closure. Exact intake HEAD:
`2b4a10b483ca37505d4f0b20c7121bcd0f568c57`; branch
`byok-c1-p96-p292-closure-20261125`. Intake index/worktree were clean; no tag
pointed at HEAD. No context-file access or update was attempted. The previously
reported context refusal/staleness remains a blocker to the next formal phase.

**P96 HIGH OPEN; P292 OPEN; qualified approvals 0/7; accepted full regressions
0/3; real-key NO-GO; production/release HOLD.** This source is uncompiled and
unexecuted. Independent source review and runtime evidence remain outstanding.

## Open Failures & Prior-Issues Review

| Issue / severity / source | Root cause, affected routes, evidence and disposition |
| --- | --- |
| P96 / HIGH / original negative fixture and P250/P268/P269 reviews | Separate approval/lease checks and effect entry admit post-check revocation. Frozen original expected-vulnerable P96 remains unchanged. Older P99/candidate, Python backend/controller and service paths remain distinct; an in-process metadata gate cannot enforce cross-process store exclusion. Shared production ordering is integrated below, but no native actor, authenticated consent or store custody is admitted. Independent repair acceptance absent: OPEN/HOLD. |
| P320 publication race / HIGH / P320 repair | Timeout/reentry uncertainty previously raced commitment/terminal publication. User supplies repaired hosted run **45629399704**, four compile/test shapes, **142/142 each, 568 executions**, for the exact parent. Those results are inherited evidence, not validation of this extraction. Original 142-case driver remains byte-identical; rerun required. |
| P292 / HIGH / supplied original raw evidence | User verified all **18 original ZIP CRCs** and before/after manifest equality. Lifecycle **0/6, 4/6, 3/6**; cleanup **0/6, 6/6, 5/6**. Third x86t2 start and after-absent both TIMEOUT with raw exits unavailable; stop1062/delete0 do not prove absence. Root causes remain unresolved. No artifact retrieval or native reproduction here; OPEN/HOLD. |
| P294/P295/P296 / HIGH missing qualification | Dispatcher-first source is compile/static evidence only. P294 binary-sharing ambiguity and P295 Application Control author/independent launch disagreement remain unresolved. P296 provides bounded memory receipts/drain source, not an independent OS supervisor. No bypass, migration or retest; HOLD. |
| Historical failures / material / inherited P320 ledger | P76 four failures, P211 test02, P216 test02/test06, five historical scope conflicts (P264/P133/P134/P140/direct BYOK B), alternate entrypoints and regression gaps remain unwaived. No historical expectation, source pin or workflow is changed. Full acceptance 0/3. |
| Governance and context / material | SEC03/04 and the other five qualified decisions remain absent. The context refusal is not retried or worked around. Sole-author static review is not independent review. No next formal phase: HOLD. |
| Author tooling / bounded environment failure | `rg` is unavailable; a preliminary read used an incorrect core path. Canonical tracked source was then located with Git and read directly. No installation, interpreter, permission change or refusal workaround. Neither incident is product validation. |

**Failure gate: HOLD.** Bounded remediation source work is authorized by the
current instruction; no material failure is waived or accepted as low risk.

## Concrete P96 integration

`AtomicCustodyPublication.cs` contains the existing P320 CAS algorithm and its
outcome enum, extracted without changing the bit layout, commitment CAS or
terminal/uncertainty precedence. The synthetic core delegates publication to
that class; its gate, crash seams, fixture, codec, mutation and tests remain in
the isolated synthetic compilation. There is one publication implementation.

The real service project now compiles only the extracted nonsecret class and
`DenialOnlyRecoveryAdmission.cs` in addition to its prior production sources.
It still excludes `CustodyTransactionCore.cs` and the P95 codec. No fixture,
reflection rendezvous, crash enum, new friend assembly, injected effect,
privileged launcher, journal writer or execution adapter enters production.

The existing actual route is now:

1. `CustodyService.OnStart`: unchanged executing-identity checks, then unchanged
   read-only profile/leaf inspection and second identity verification.
2. That boundary returns a one-use **denial-only** recovery observation. Only
   MissingLeaf can be claimed once; null, reuse, Unknown, InFlight,
   TerminalUnverified, Malformed and invalid values hold.
3. The service constructs its existing `SyntheticTransactionOwner` with that
   observation, before constructing its existing ingress/status pipes.
4. `Deny`/`Cancel` validate the existing immutable owner/epoch/request/operation
   identity and reserve the existing monotonically increasing high-water ID
   under the same nonreentrant, bounded owner gate. The most recent request
   retains a terminal publication using the shared implementation. No queue or
   history is introduced. Invalid identities do not consume the sequence.
5. Stop/shutdown/fault/disposal retire that owner through the same gate and
   shared publication implementation before existing pipe cleanup. Timeout or
   reentry atomically makes owner uncertainty sticky. Failed retirement throws
   so existing service failure/cleanup handling sees it. Later retirement,
   malformed input, replay or a fresh request cannot clear HOLD.

All result authority remains literal false, with zero attempts and no possible
effect in this denial-only owner. RecoveryHeld is a conservative effective
admission state, not proof that a blocked thread was killed. Earlier immutable
denial snapshots remain historical snapshots; later observation reports HOLD.
The default owner constructor is retained for historical denial-only callers;
it reports Unqualified recovery admission and has no effect authority.

The one-use observation enforces exclusive claim **of that object in this
process**. It does not authenticate a caller, pin storage or exclude a second
process/service. MissingLeaf is neither durable-intent proof nor clearance of
previous uncertainty. There is no restore/resume/retry/clear API.

The explicit durable-intent contract currently admits **no durable operation**.
Before any future possible-effect route, SEC03/04 must qualify the single real
owner, immutable operation/target/consent binding, retained storage/anchor
identity, durable intent flush plus independent readback, restart/rollback
admission and exclusive native tenure. Intent and native commitment must share
the reviewed owner/control ordering; uncertain effect must never retry. The
existing hosted `DurableIntentJournal` is not connected as a production issuer.
That portion stops here for those exact missing qualified architecture and
store/consent decisions, rather than adding a substitute actor or fixture.

Permission -> Policy -> Confirmation -> Execution -> Verification, executing
identity, fixed IPC denial, approval, installed-image and real-key gates remain
in force. The model receives no capability from these metadata objects.

## Focused source tests and hosted preparation

The new driver selects the **actual production source files**, not another
transaction model: atomic publication, recovery observation and existing owner.
Its 47 authored cases cover all three operations, four retirement causes,
retirement/denial/cancellation contention, identity/replay/wrap boundaries,
one-use concurrent ownership, conservative restart categories, and seven
reentry plus seven actual gate-timeout routes. It also checks the shared
commitment/uncertainty/terminal ordering directly. Test reflection and thread
coordination remain in the test driver. No service, IPC, store, credential,
native effect, process launcher or filesystem implementation is linked there.

The new draft workflow is separate from every frozen historical workflow. It
requires the exact parent, exact same-repository draft branches/repository ID,
one direct child, exactly these 13 paths, regular raw source custody, identical
before/after manifests, clean checkout and explicit compilation-source sets.
It uses only installed MSBuild, without restore/download, for x64/x86 and
Debug/Release. Product compilation is **compile-only**; only the P320 memory
driver (142) and shared denial driver (47) may run. The bounded runner is copied
from P320 and adds a fixed compiler/test executable allowlist. Child deadlines,
diagnostic caps and job deadline remain; this is CI containment, not qualified
Windows lifecycle supervision. No SCM, credentials, native fixture, service
entrypoint or historical workflow is invoked. There is no manual dispatch.

If all four shapes later pass, that is 756 focused case executions, still
189 distinct authored cases and no whole-product regression acceptance. The
prior 568 executions cannot be added as validation of changed source. This
assignment performs **zero local builds/tests and zero hosted submissions**.

## Minimum P292 exact-source qualification and migration requirements

Reuse the existing witness and these sources. The raw SHA256 values below
identify this inspected checkout; they do not authenticate historical ZIPs or
installed/running images. P292/P294/P295/P296 remain unchanged. The product
service is a separate stricter identity/denial route, not equivalent to a
successful disposable P294 witness.

| Source | Raw SHA256 |
| --- | --- |
| `tests/p292_service_principal/HostedReview.ps1` | `5CAE59AA706911A09D8ADEF5F58824BFFE940CDA90F2FCEFBA076044BADDFB20` |
| `tests/p292_service_principal/P292DisposableService.cs` | `B226DD10506640F90D49E5EE0C27DB3D22DC21B759138469B94A7CC3E520F665` |
| `tests/p294_dispatcher_first/P294DispatcherFirstDisposableService.cs` | `2B7D87F8770BED1B21C756DE0344D34C5A87584D800AF58A430B9864CB1B81FC` |
| `tests/p294_dispatcher_first/HostedStaticReview.ps1` | `149E984BA434612A168D069856F2F143777792107561D161C6F3BA31E957532A` |
| `tests/p295_runtime_preflight/P295PreflightContract.cs` | `5BE876B0A5631D37656BCA9C0E68CBA7310E07AF5F0D82AAE6F275026CDA4180` |
| `tests/p296_launch_custody/P296LaunchCustodyDiagnostic.cs` | `9EA16EEA4765BD10E7C2C47DB9C8BCD1100F37971DA7F3F2D584735D000BD48D` |
| `src/Nayeon.ByokC1.Service/CustodyService.cs` (this candidate) | `5A685173AF7C8B83BB6EACF5BDE6374F480C63EB76181BD7B753359808478960` |

The [P294 migration gate](byok-c1-p294-dispatcher-first-security-review.md)
requires: “Before **any** hosted SCM-mutating retest, Nayeon and qualified
external OS launch/teardown security owners must approve exact-source migration
and security test equivalence.” That approval is absent, and the user expressly
withholds native retest authorization. No original harness/guard/pin is edited.

The minimum external qualification package for that existing witness is:

| Required decision / receipt | Acceptance requirement; missing evidence stays HOLD |
| --- | --- |
| Exact-source migration and equivalence | Nayeon plus independent Windows launch/teardown owners bind reviewed commit, complete source set, dependencies, binary hash and protected image identity. Approve only moving identity lookup into dispatcher-owned synchronous OnStart, keeping service-mode/virtual-account, mismatch, exception, impersonation and LocalSystem negatives. Bind production process-token/no-impersonation/restricted-identity differences explicitly; witness success cannot approve product custody. |
| Launch qualification | Resolve P295 Application Control disagreement through its approved route; no alternate launcher or policy exception. Authenticate retained PID + birth + image + actual handle; distinguish dispatcher registration, OnStart entry, successful lookup/disposal, callback completion, framework return and independently observed RUNNING. An exit0 or success flag alone is insufficient. |
| Deadline and drain migration | P292 Child uses unbounded ReadToEndAsync retention and post-exit GetResult without an independent drain deadline. Its frozen harness cannot be silently repaired. P296's bounded collector can be reused only with an independently qualified external supervisor covering launch, reads, disposal, descendants and host death. Its cancellation cannot guarantee interruption of Framework ReadAsync/Dispose. No new supervisor/launcher is implemented here. |
| Principal and image | Independent kernel token observations twice, actual restricted-SID list/privileges, exact virtual-account binding, loaded-image/file identity and protected installation/ACL evidence. Resolve binary-sharing ambiguity; equal hashes are not file-object custody. No live credential/profile qualification is implied. |
| Raw outcome and failure receipts | Per architecture/trial and child, retain collector identity, monotonic sequence/deadlines, source/binary binding, raw signed exit or explicit UNAVAILABLE, start/observer failures and both stream dispositions. Preserve raw11, timeout and cleanup as separate facts; later cleanup success never erases earlier failure. Reuse P295 evidence requirements and P296 receipt ordering; synthetic labels cannot admit live evidence. |
| Teardown on every exit path | Native STOPPED and closed SCM handles, deletion response, independently bounded native and CIM post-delete absence, retained process exit/raw exit, both EOF/disposals and late-child/descendant absence. Include partial start and observer failure. Delete0/stop1062 do not prove absence. Missing native absence or after-absent TIMEOUT remains cleanup HOLD; no persistence claim is invented. |
| Qualified authority and runtime scope | Authenticate named GOV01/GOV02/SEC03/SEC04/REL05/REL06/REL07 decisions using the [existing response form](byok-c1-p222-independent-security-owner-response-form.md). SEC03 owns principal/store/recovery; SEC04 owns signed single actor/consent/IPC; OS launch/teardown owners and Nayeon must approve exact witness migration and test equivalence. Separate explicit disposable-runtime authorization remains required. Current decisions 0/7, full regressions 0/3. |

No newly proven defect in the existing nonprivileged P295/P296 helper warrants
changing its frozen source under this assignment. The demonstrated P292 Child
limitations require the gated witness migration above. More synthetic receipt
models would not supply the missing launch/absence evidence, so none is added.

## Exact handoff and validation limits

Thirteen paths: six modifications (service, owner, recovery boundary, product
project, synthetic core and synthetic project) and seven additions (two shared
production components, driver/project/hosted script, workflow and this review).
No staging, commit, tag, push, merge, workbook/dashboard or permission change.

Static source/XML/PowerShell parsing, compile-input inspection, raw frozen-file
comparison and whitespace checks are the only author validation. No C# compile,
test execution, SCM, installed application, local interpreter/build, credentials,
provider/network or hosted workflow was run. Independent review is **pending**.
Do not interpret authored tests, static checks or the prior parent run as a
verified integrated repair.

Actual static results: hosted-script AST **0 parse errors**; all three project
XML files parse and every explicit compile input exists; **10/10** selected
frozen raw disk blobs equal HEAD (both P96 sources, original P320 driver,
P292 harness/service, P294 candidate/static harness, P295/P296 contracts and
original P320 workflow). Directory diffs for the frozen witness/receipt sources
and original workflow are empty. `git diff --check` exits **0**; all seven
additions have **0 trailing-whitespace lines**. The two extracted production
files have no native, codec, callback or synchronization-hook matches in the
bounded surface scan. These checks do not prove C# syntax/runtime safety.
The index remains empty. HEAD and tags are unchanged. Nearest local milestone
description is `nayeon-v1-phase-10-3-synthetic-provenance-redaction-01-693-g2b4a10b`;
this development assignment does not create or move a milestone.

Final candidate raw SHA256s (the review's own digest is deliberately omitted):

| Path | Raw SHA256 |
| --- | --- |
| `src/Nayeon.ByokC1.Service/AtomicCustodyPublication.cs` | `8EB4E35E120AAC0D0BA53D9112359611EA120CE9B28D01555187FDA21B762A9C` |
| `src/Nayeon.ByokC1.Service/DenialOnlyRecoveryAdmission.cs` | `78B537B753EBF14DE94321738ACEDEB9C201BE1E50300D4DD0DCAA1AFAED7B6C` |
| `src/Nayeon.ByokC1.Service/SyntheticTransactionOwner.cs` | `5EFF0E126BE287320F6B9786F28CF622D3F5D0368663D9021C591C28A7174DDD` |
| `src/Nayeon.ByokC1.Service/CustodyService.cs` | `5A685173AF7C8B83BB6EACF5BDE6374F480C63EB76181BD7B753359808478960` |
| `src/Nayeon.ByokC1.Service/ServiceRecoveryBoundary.cs` | `E276B40876037CF4B481AE57727BDEF9AFE5D998D1BB1641D3AA858B038C6797` |
| `src/Nayeon.ByokC1.Service/CustodyTransactionCore.cs` | `973F8E486FAE515C163743254C6C12B09C3E1482E6569EEC595541223A2BC687` |
| `src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj` | `0974348DE7060F31179BC9086734451AD078D131236364BCABEBA2F2E9F237A4` |
| `tests/p320_transaction_core/P320.Synthetic.csproj` | `E150E51083D89CC317B3EA2FFD096998AFAAA57F772C545AC89B87D85487546A` |
| `tests/held_failure_service_ordering/HeldFailureServiceOrderingTests.cs` | `27EDC468BC1D8D0FBD06EEE2A03A53AE29068D7404FF439DFCF92DBC0D92DFFF` |
| `tests/held_failure_service_ordering/HeldFailure.ServiceOrdering.csproj` | `6AB0B6723DE070A6D438DE49597F5635079255159F1AC5BE6B945FD7A226754C` |
| `tests/held_failure_service_ordering/HostedDraftReview.ps1` | `6DAF8CDCC38BD409003AFD3E03582876589E0605703DCA408BB9276440D5519A` |
| `.github/workflows/held-failure-service-ordering.yml` | `87C1F241AF7A85F4CCB6BEE15D1974D196A08529C39702B47497F2D89B65ECAB` |

P96 and P292 remain **OPEN**. Real keys **NO-GO**; production **HOLD**; approvals
**0/7**; full regressions **0/3**. The protected context requirement is unresolved,
so no next formal phase is admitted.
