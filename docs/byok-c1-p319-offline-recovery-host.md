# BYOK C1 P319: offline first-run host recovery review

2026-11-24. OM v2.1; Codex sole source writer. Exact parent:
`6f8d1ff279038e5cb43d3205e1bca3823aef9e10`. Branch:
`byok-c1-p319-offline-recovery-host-20261124`. Intake worktree clean;
no milestone tag at HEAD. Git supersedes the stale cross-branch
`.codex/CURRENT_STATE.md`; its historical bytes are preserved. This is the
expressly requested consolidated source follow-up, not a new architecture
phase or completed milestone. Context refresh remains necessary before a
separately approved next product phase; no completed phase/tag is invented here.

User-supplied inherited evidence: P318 hosted **33/33 PASS**, run
`45461402123`; P317 **68/68 PASS**. Neither result was independently fetched
or rerun. P319 runtime and independent review are **PENDING**.
**Full regressions 0/3; P96 HIGH OPEN; P292 UNKNOWN; production/release HOLD.**

## Actual product route and bounded implementation

The existing route is `OfflineWorkspaceApplication.show_connection` ->
`ConnectionWindow.manage_button` -> `_open_connection` ->
`FirstRunConnectionWindow.open`. The separate local-key route is
`ConnectionWindow.local_byok_button` -> `_open_local_byok` ->
`LocalByokLaunchBridge` -> `local_byok_window`. P317 already supplies honest
unavailable/untrusted guidance in that separate process; its fixed status
reply is not qualified custody evidence. This package changes only the
existing offline-preview child route. Application routing, Connection-page
buttons, separate-process bridge, native observer/requester and service stay
unchanged. No real GUI was mounted or interacted with during this task.

Inside the existing child, **Review offline recovery status** lazily mounts
the existing `FirstRunStatusWindow` in a child Frame and explicitly refreshes
it through the exact P318 `FirstRunReadOnlyController` paired contract.
Opening the Connection page or preview creates no controller/panel and makes
no observation. Subsequent review clicks and the panel's Refresh status button
each request one explicit refresh. There is no timer, worker, auto refresh,
re-observation schedule, new operation, new recovery model or authority path.

No qualified product observer exists on this route. Its fixed callback returns
`None`, never a fabricated `ConnectionObservation`, custody view, absent marker
or paired synthetic claim. P318 therefore returns UNAVAILABLE without summary.
The panel displays **Status unavailable**, **Manual unknown-state review
required**, **Recovery is unverified**, and no suggested credential operation.
Even repeated refresh cannot become observed custody, readiness or recovery
clearance. The fake credential harness is not an observation source. No journal
bytes, local profile, service status or fixed denial is converted into evidence.

The panel's optional embedded layout and trusted lifecycle predicate preserve
standalone defaults. The host supplies its existing `is_current` predicate,
including creator thread, application/root, exact child/context, pane/journey,
token, generation, liveness and quarantine checks. No identity is replaced.
Refresh checks currency before observer/UI access and after callback/widget
seams; reentrant UI refresh is refused. Old callbacks cannot deliver to a
successor or touch retired widgets. P318 controller recursion/validation is
unchanged. Partial mounting failure uses the existing exact-child retirement;
uncertain destruction retains the existing quarantine. No automatic remount or
cleanup bypass exists. Fake validation review/confirmation/owner logic is intact.

## Exact changed paths

Two modifications and three additions; five paths total:

- `nayeon/desktop_alpha/first_run_connection_window.py` (M): two panel-state
  fields, explicit review button and lazy bounded handler; existing identities,
  owner/approval/effect and retirement logic retained.
- `nayeon/desktop_alpha/first_run_status_window.py` (M): optional embedding,
  lifecycle checks and refresh reentrancy guard; existing presentation contract.
- `tests/test_byok_c1_p319_offline_recovery_host.py` (A): 20 deterministic
  fake-widget cases using real `_open_connection`, child/panel/controller,
  `_retire_view`, root-destroy handler and application close. Unrelated
  conversation/settings teardown dependencies are inert mocks.
- `.github/workflows/p319-windows-offline-recovery-host.yml` (A): draft-only
  hosted fake validation source, not published or executed here.
- `docs/byok-c1-p319-offline-recovery-host.md` (A): this review, dependency map
  and pending-validation record.

All existing tests/workflows, fake harness, owner, application/workspace,
controller, models, native transport and service sources are unchanged.

## Open Failures & Prior-Issues Review

Bounded inputs: engineering failure gate; stale current context and exact Git
intake; P313-P318 reviews; direct host/panel/controller/summary and relevant
tests; actual service startup, journal, denial owner/pipe and desktop transport
source; direct references to the two changed UI paths. No unrelated historical
scan or runtime reproduction was attempted under the source-only restriction.

| Issue | Severity / cause / affected boundary | Evidence, containment, review and disposition |
| --- | --- | --- |
| P96 original control/effect race | HIGH OPEN; original last-current check and independent revocation/effect ordering lack qualified production closure across processes/restarts | P313 monitor and P314/P315 disposable witnesses do not close the original production finding. No repair or independent approval claimed; HOLD. |
| P292 SCM teardown | UNKNOWN; x86 teardown root cause/qualification still unproved | No SCM invocation or lifecycle execution here. Source/fake tests cannot qualify it; HOLD. |
| Missing product recovery consumer | P318 paired controller/panel had no live offline host mounting; inventing a pair would falsely claim observation | Existing explicit child now consumes P318, with missing evidence -> unavailable/manual review. Twenty authored host tests; runtime and independent review pending. No qualified observer gained. |
| Stale/reentrant UI delivery | A retired pane/child or nested callback could otherwise touch dead UI or a successor | Same host identity predicate at refresh/write seams; real navigation/close methods with inert widgets, nested callbacks, replacement identities, foreign-thread simulation, construction and cleanup failures covered in authored tests. Verification pending. |
| P318/P317 inherited results | Focused synthetic evidence only, not full regression or qualified custody | Supplied 33/33 and 68/68 retained as inherited evidence; not rerun or promoted. |
| Older P264/P133/P134/P140 conflicts | Known historical current-source freeze/exact-scope expectations: P264 whole `local_byok_window.py` hash; P133 seven-path ancestry; P134 four additions/old blob; P140 six-path/sole bridge modification | P317/P318 already record these source conflicts. Unchanged, unwaived; not newly executed failures. Full compatibility remains HOLD. |
| Direct BYOK B historical guard | `tests/phase8_byok_b_scope_migration.py` pins this live connection child to `865fa15854591f151b2a6c17ef392636a0ea9950441c531b463c931e72bc1b32` and an older exact descendant. `phase_8_30_scope_migration._project...` delegates admission to that guard | P319 intentionally changes that UI source. Exact historical admission cannot be claimed for this candidate. No pin, assertion, test or projection is weakened. Successor compatibility review remains required before full milestone qualification. |
| Assurance evidence | Full product regressions 0/3; independent security approvals remain 0/7 in P313-P318 records | Source inspection/whitespace only here. P319 focused tests, hosted execution, independent review, native lifecycle and full-suite validation pending; production/release HOLD. |

Disposition: only the expressly authorized offline source package is prepared.
No material finding is downgraded, waived or declared repaired by these UI
changes. The failure gate remains HOLD for production, seal and forward
authority-bearing integration. Deterministic tests are authored evidence
obligations, not reproduced PASS results.

## Remaining functional dependency map

These are implemented source components versus missing **composed production
functionality**, not claims that every historical prototype is absent.

| Dependency | Already implemented in inspected source / P313-P318 | Absent or unqualified in the actual product path |
| --- | --- | --- |
| Service identity and protected storage | `CustodyService.VerifyExecutingIdentity` checks restricted product virtual-account primary token/session zero/no impersonation. P313 nested hosted owner serializes opaque approval and fixed synthetic Add. `DurableIntentJournal` has hosted-user DPAPI, SID-only protected ACL, pinned handles, flush/readback. P316 `ServiceRecoveryBoundary` adds conservative fixed-profile marker inspection before owners/pipes. | Qualified provisioned service profile/store, protected production custody under the service principal, signing/code-integrity deployment and operational lifecycle assurance. Hosted CurrentUser DPAPI is not service custody; attribute absence is not provenance or antirollback. P292 remains UNKNOWN. |
| Durable transaction | P314 persists IN_FLIGHT before fixed hosted native Add under the owner gate. P315 kills a separate child after pre-native durable readback and proves conservative reopen/no replay in its disposable experiment. P316 refuses startup uncertainty. | Production journal writer composed with real service operations, authenticated approval, durable terminal outcomes, restart/recovery policy and audit/cleanup across all crash points. `SyntheticTransactionOwner` is an in-memory denial owner; the hosted journal is not wired into its actual OnStart path. Post-native crash, rollback and exactly-once semantics remain unqualified; P96 HIGH OPEN. |
| Authenticated IPC | Actual `StatusPipeServer` and `SyntheticIngressServer` expose fixed bounded denial-only exchanges with owner-SID protected DACLs, no impersonation, deadlines and disposal. `StatusPipeClient`, `byok_native_service_observer.py` and `byok_native_synthetic_request.py` classify replies as untrusted HOLD/unavailable. | Qualified desktop-to-service peer attestation, freshness/session/review identity binding and human-consent-bound production transaction protocol. Fixed bytes and endpoint ACLs do not authenticate a recovery claim. Existing denial ingress has no credential operation dispatcher. |
| End-to-end integration | Explicit desktop routes and existing fake owner/lifecycle are present. P317 honest separate-process text; P318 pure paired summary/controller/panel suppresses operations; P319 mounts that panel in the actual offline host on explicit action. | Qualified read-only service recovery observation reaching the host, then separately approved production consent/transaction wiring and end-to-end crash/navigation/service-restart validation. No real recovery observer, production READY transition or release authority is added here. |

Propose three larger, separately designed/reviewed build packages rather than
further presentation micro-checkpoints:

1. **Service custody and durable transaction:** provision and qualify the service
   principal/profile/protected store and deployment identity; compose the durable
   state machine, approval/effect linearization, audit and conservative recovery;
   reproduce/close P96 and qualify P292. Include the full crash-point matrix and
   independent adversarial review as one acceptance package.
2. **Authenticated desktop/service protocol:** bind attested peer, session,
   freshness and exact one-use human review to bounded typed requests and a
   qualified read-only recovery response. Include adversarial peer/replay,
   cancellation and deadline/handle lifetime validation. Depends on package 1's
   identity and durable contracts; no readiness inferred from fixed denial.
3. **Product integration and release assurance:** connect the qualified observer
   to this explicit offline host, then separately authorized operations through
   Permission -> Policy -> Confirmation -> Execution -> Verification. Cover
   first run, unavailable/uncertain state, navigation/close, service restart and
   cleanup end to end; reconcile historical compatibility without weakening
   guards; independent review and all three authoritative full regressions.

These are proposals only. No service, storage, IPC, credential, profile,
provider, sandbox or authority work in those packages is authorized/performed
by this source task. Presentation identity never changes capability identity.

## Draft hosted validation and local limits

The authored workflow mirrors P318: Windows-2022, same-repository draft PR,
repository `krismcan/Mark-LV` ID `1402212689`, exact P319 head ref above, exact
base `byok-c1-p318-recovery-presentation-20261124` at the parent SHA above.
SHA-pinned checkout uses event head and no persisted credentials. Exact
two-M/three-A delta, base ancestry, input hashes, HEAD and clean Git checks
apply before/after. Only later normal checkout may use the network.

It locates installed Python 3.12 x64 on the hosted runner, failing without
downloads/install/setup. Five-minute job, 90-second child, bounded kill/wait
and output-drain handling are inherited. Seven explicit fake/pure classes
select the 20 new host cases plus the same six P318 selected classes (33
tests), expecting exactly **53 tests**, no skips. Native-Tk connection tests
are preserved and hashed, not selected. No discovery, compileall, real window,
service build, native test or IPC operation is included.

Real Tk creation, native loaders, credential module, `_winapi`, network,
subprocess and filesystem mutation are guarded; metadata load/save and profile
bootstrap are tripwires. Selected host tests replace only widget and unrelated
teardown dependencies with inert fakes. Guarded operations fail the run even
if an application catches their exception. These guards bound this selected
test composition; they are not a general Python security sandbox.

Local verification is source inspection and **git diff --check only**, including
new-file `--no-index --check` checks against `/dev/null`. No interpreter path
was accessed/probed/executed; no test, parser, compilation or real GUI ran.
Workflow source has not been syntax/runtime validated. No network request,
service, credential, IPC, profile/provider operation, sandbox change, staging,
commit, tag, push, merge, workbook or dashboard update occurred. Independent
validation and all full regressions remain pending. No P319 PASS or milestone
seal is claimed.
