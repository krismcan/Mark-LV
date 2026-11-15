# P250: P96 service-owned atomic ordering architecture and qualified security decision package

15 November 2026. **DESIGN ONLY; SOURCE-PRESERVING; NOT AN INSTALLED DESIGN.**

**P250_ARCHITECTURE_DRAFT_READY** means ready for independent decision review only.
Implementation, runtime acceptance and release remain **HOLD**. P96 is **OPEN**.
P76 has **4 authentic original FAIL methods, unwaived**. P247 runtime remains
**x64 0/54 executed and x86 0/54 executed**. SEC-03/SEC-04 are pending; qualified
approvals **0/7**; unfiltered whole-product regressions **0/3**; **REAL-KEY NO-GO**;
**PRODUCTION RELEASE HOLD**. An author-written review is not qualified independent
security approval. No approval checkbox is completed by this document.

## 1. Verified source identity, inventory and limits

Read-only Git inspection observed this exact isolated workspace:
`D:\Nayeon\CODEX_P250_P96_SERVICE_ORDERING_ARCH_20261115`, branch
`byok-c1-p250-p96-service-owned-ordering-20261115`. Initial status, including all
untracked paths, was empty; tracked and staged diffs were empty. No unexpected
addition was present. The single-parent chain and tree identities were:

| Checkpoint | Commit | Tree |
| --- | --- | --- |
| Initial HEAD, P249 | `4bbc62d949bb325e8da08ff5ee981f4a457a7cc4` | `f9c8cec024959a2ff78704741673583f74cdefcf` |
| Its parent, P248 | `3c4c8ce29cb95698926d3dc21db592014db4b143` | `4f19e57707ff1edaa16acbb3cc09deb8a5862853` |
| P248 parent, P247 | `39dbb445fc08a1ef03c73f4a13c6f344be8dfa07` | `a82d9fab598fb5565eb42c13d3101455c11bf760` |

P247's parent is P245 `e49810c0cc0982f73fb2d7f84ba516ab006f75a5`.
No tag points at P249, P248 or P247 in the local Git view. No history or tag is
changed. `.codex/CURRENT_STATE.md` starts with 3 November Phase 10.2 material,
which does not describe this branch. Git and this explicit bounded assignment
govern this checkpoint; the stale handoff remains untouched. This is not a new
product phase, retrospective audit, security seal or context-refresh operation.

These SHA-256 values were observed from current raw file bytes using read-only
hashing. They identify inspected files, not installed images, runtime provenance,
authenticity, or proof of execution. Paths below are relative to the checkout.

| File | Observed SHA-256 |
| --- | --- |
| `tests/p96_native_transaction_negative/PendingCustodyTransaction.cs` | `D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB` |
| `tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs` | `2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F` |
| `tests/p247_effect_free_service_ordering/EffectFreeServiceOrdering.cs` | `CB58CA6ED389817EA4F1BCF0C23DD51C244808CB54AE83DF83FBC36DCABC6C88` |
| `tests/p247_effect_free_service_ordering/OrderingTests.cs` | `3BF159595FC04A772151D3620E732014A7F1BB5BB3AE5A158A4CDF26C82D5450` |
| `docs/byok-c1-p247-effect-free-service-ordering-decision.md` | `BED85F19D37ABD66B87B2639D9595F88944F6B7C29669F0AD71CA683ACC80B80` |
| `docs/byok-c1-p249-effect-free-runtime-authorization-decision.md` | `20A881D86C72040DC0EBDB52A051CCA1A12E8A497C7638837EE4DABF744D2557` |
| `nayeon/brain/local_byok_user_scope.py` | `1971A3F7F90C840FB6C3DC95128ECB6CF2A5E855204D418D99144EB10F3A17B6` |
| `nayeon/secrets/windows_credential.py` | `E6443853300FB2FB4944B8C8BEDE2EE953719EAF7544D7338056D81491B46125` |
| `nayeon/desktop_alpha/local_byok_window.py` | `8DFDFC587886471F312D39AA53BC049179A7CA2D61BC310F84AC142BA5D103E6` |
| `nayeon/desktop_alpha/local_byok_launch_bridge.py` | `1FB8A889C7DCBA0A83C1DBC888BD1D7DEB219BCFF3FC08CADEB246F61B3C71D5` |
| `nayeon/desktop_alpha/application.py` | `51F834E8A771039C9A94EB81C5D0D32DF61D080B14B421AF27AA25378BAA22B8` |
| `native_c1_candidate/CustodyService.cs` | `876E3006BA26966BE93BA033C97779B6FBB41E8656869A462535B1CF4B12D95E` |
| `native_c1_candidate/ServiceOwnedAdmissionBoundary.cs` | `1FA108C18F228F83FE4BBDE0F682025BD23E864B23DDC24EA4D4F70F27382DD5` |
| `tests/p99_original_native_c1_denial/PendingWinCredStore.cs` | `4051A48F3062A737D0D9CE212DB9B302C2C22D5ECA2893CE27B35C740A72B93C` |
| `tests/p99_original_native_c1_denial/PendingServiceState.cs` | `B194EE6809BEB84502D9CF509D44237E1A2C24D3905F3764DC4DCA425BAB793E` |
| `tests/p99_original_native_c1_denial/CustodyService.cs` | `49217E9018AB2437D3F2B4B2907C08946432352618EDEE065F734D88B93EC093` |

### Factual call flow and effect entrypoints

Line references describe the unchanged intake source, not future code.

| Source / function / lines | Verified source behavior and boundary |
| --- | --- |
| P96 `PendingCustodyTransaction.Apply`, 123-240; `ConsumeApproval` 109; `ApprovalCurrent` 116; `Persist` 76 | One-use instance claim, private candidate snapshot, approval consumption/current checks, separate lease acquisition, journal/anchor checks, intent persistence, final current/ownership predicate, effect interface invocation, terminal persistence and lease completion. Interfaces are dependencies, not authenticated installed owners. |
| Same file, 191-204 then 209-212 | Pre-intent and post-intent approval checks precede `lease.IsOwned`; `DeletePending` or `SaveOrReplace` follows. No shared revocation/dispatch linearization is supplied by those calls. These are the two P96 effect callback entrypoints. |
| P96 harness `P96ApprovalFixture.StillCurrent` 20 / `Revoke` 25; `P96GuardFixture.P96LeaseFixture.IsOwned` 100-123; `P96StateFixture.SaveOrReplace` 59 / `DeletePending` 69; `P96NegativeProof.Main` 168 | Final ownership getter injects and joins a separate revoker thread at check four. Effects are integer markers only. Main declares 15 negative/baseline cases. Source assertions describing reproduction are not newly executed evidence. |
| P99 original-copy `PendingServiceState.LegacyEffectEntryDisabled`, 94-109 | Literal true denies both effect forwarding methods before `pending.SaveOrReplace/DeletePending`. |
| P99 original-copy `PendingWinCredStore.NativeMutationAdmissionPending`, 193-200, 253-260; native declarations 72-83 | Literal true denies mutation; dormant `SaveOrReplace` calls `CredWrite`, and `DeletePending` calls `CredDelete`, bound to `CredWriteW/CredDeleteW`. No generic target; fixed pending target differs from Python's target. Comments mentioning LocalSystem are historical assumptions, not P250 selection. |
| P99 original-copy `CustodyService.OnStart` 17, `OnStop` 25, `Main` 30; `LiveEligible` 56-77 in `tests/p99_original_native_c1_denial/ServiceGate.cs` | Startup relies on disabled service gate, whose eligibility call supplies two literal false release prerequisites; stop has no work in the incomplete chassis; historical Main exists. It is distinct from the nondeployable candidate below. No service was started or gate tested here. |
| Candidate `CustodyService.RefusePendingOperation/RefuseBoundPendingOperation`, `OnStart/OnStop`; `ServiceOwnedAdmissionBoundary` | Production requests remain denial-only. Candidate start additionally throws unconditionally, stop publishes to its admission fence; native-effect, consent and release properties are literal false. Conditional synthetic methods are not production effects. Candidate has no Main/installer. |
| P247 `OrderingOwner.Restart` 48, `Prepare` 54, `DispatchDecision` 72, `Publish` 94, `ObserveSyntheticRecoveryOnly` 111 | One private monitor protects model metadata. Dispatch sets `MayHaveEffect` and recovery; it invokes no effect and returns no authority. Restart always holds recovery. |
| P247 `OrderingTests.Main` 36, `OnThread` 27, `Pair` 172 | 54 loop-expanded source cases per architecture: 18 forced winner orders, 15 uncertainty, 9 category/replay, 7 restart and 5 standalone. Threads/reflection belong to the driver. No OS store/service/CI/custody behavior is established. |
| Python `LocalByokController.approve` 130-199; factory 205-207 | Local review consumption, RLock and cooperative onboarding mutex, metadata presence check, backend `delete` at 175 or `put` at 181, post-presence check. Restart loses uncertainty; same-presence external replacement is expressly undetected. |
| Python `_Advapi32Adapter.write` 102-117, `delete` 119-124; `WindowsCredentialBackend.put` 161-172, `delete` 174-179 | Direct `CredWriteW` at 113 and `CredDeleteW` at 120. Backend construction is lazy; `put/delete` have no native service-owner requirement. `get` 149 and `is_available` 181 are separate read/presence paths, also needing exclusion from protected custody. |
| UI `approve_from_button` 219-270, `main` 295-305; launcher `launch` 56-118; application 656-662 | Manual UI calls controller approval; module main constructs production backend through factory. Source launcher uses fixed Python module child; Connection callback invokes launcher. Frozen branch refuses absent separate companion admission and has no Python fallback there. Source mode remains a separate route. |

The backend docstring saying "no production consumers yet" is not an authority
inventory: the actual controller import and composition above are present.
Read-only tracked-source searches found the direct Python calls above and native
P99 declarations; string matches in guards/review inventories are not extra native
effects. No dynamic-load absence or installed-package closure is inferred.

Bounded related references inspected: [P96 negative finding](byok-c1-p96-native-transaction-race-negative.md),
[P103 peer identity limits](byok-c1-p103-windows-local-ipc-provenance.md),
[P104 admission design](byok-c1-p104-production-admission-architecture.md),
[P221 original race review](byok-c1-p221-original-p96-native-gate-linearization-review.md),
[P222 qualified response fields](byok-c1-p222-independent-security-owner-response-form.md),
[P247 model decision](byok-c1-p247-effect-free-service-ordering-decision.md), and
[P249 authorization decision](byok-c1-p249-effect-free-runtime-authorization-decision.md).
`nayeon/brain/p216_service_store_decision.py` explicitly describes its inventory
as non-authoritative and static scanning as unable to exclude dynamic routes.

No network was accessed. P249 draft authorization PR #171 is user-supplied
context, not fetched/verified approval. P249 records script-policy and Windows
Application Control refusals; compilation receipts cannot substitute for runtime.
No code, test, compiler, repository script, workload executable, service, signing,
credential API or provider was run here. Only source/Git/hash/text inspection and
document scope/formatting checks occurred. No original external P49 checkout or
live credentials were accessed. All runtime claims remain historical reports or
unexecuted acceptance obligations, explicitly separated from this inspection.

## 2. Original race schedule and trust boundaries

The deterministic original-source schedule is:

| Order | Coordinator / competing revoker | Consequence |
| --- | --- | --- |
| 1 | Consume approval, observe current approval, acquire separate custody lease | Neither observation is a terminal-effect permit. |
| 2 | Verify prior records; check approval and ownership; persist IN_FLIGHT pair | Intent does not make revocation atomic with dispatch. |
| 3 | Final `ApprovalCurrent` at 203 returns true | Last consent observation completes. |
| 4 | Fourth `IsOwned` at 204 runs fixture's separate thread; `Revoke` sets Current false and joins; getter returns true | Revocation wins before callback invocation; custody ownership remains a separate fact. |
| 5 | Old coordinator calls `SaveOrReplace` or `DeletePending` | Fake effect marker increments after revoke; old terminal path can report Stored/RemovedUnverified. A negative-test PASS means flaw reproduction, not repair. |

This is a source-established schedule implemented by the retained negative
harness; it was not rerun in P250. It establishes the interface race, not a real
credential effect. Another final check merely moves the gap. A P247 monitor only
orders mutations on that model object: Python, another service instance, a stale
process, impersonated threads and direct native callers never enter it. A named
mutex used cooperatively by one Python route does not constrain arbitrary OS calls.

| Boundary | Proposed trust rule; current evidence limit |
| --- | --- |
| Normal UI / model / agent | Untrusted requests and presentation only; no approval boolean, digest or model text authorizes effects. Preserve Permission -> Policy -> Confirmation -> Execution -> Verification. |
| Local IPC | Hostile framing, replay, disconnect and impersonation boundary; actual OS peer token is necessary evidence, not app identity or human intent. |
| Signed consent broker | Separate qualified identity and genuine human ceremony; signing and UAC alone do not prove consent. Broker cannot own store mutations. |
| SCM service | Sole proposed effect owner, with private ordering, bounded requests and lifecycle authority; service name or SCM status is not proof of loaded code or effective token. |
| Principal / protected store | Actual process and thread token, profile and OS ACLs determine access. User WinCred and service WinCred must never be conflated by equal target text. |
| Journal / independent anchor / enrollment witness | Protected persistent identity and monotonic history, not self-authenticating hashes; separate writes and rollback domains must be proved. |
| Loaded signed code | Whole dependency graph, code loading and update/rename boundary under enforced CI/UMCI; a source hash or signed outer EXE is insufficient. |
| Legacy Python / tests / CLI | Separate effect authority today; excluded from approved production artifact and denied protected-store access by OS isolation. A service monitor cannot police it. |

## 3. Normative proposed single private owner

Subject to independent SEC-03/04 decisions, one native service-private owner MUST
serialize **Revoke, Stop, Fault, Prepare/Admission and Dispatch** through one
ordering boundary. No public effect method, caller-supplied callback, transferable
permit or "check then call backend" composition is acceptable. Admission validation
performs no effect. Only the owner invokes a fixed, non-extensible storage operation
within its continuous custody tenure. Loaded code capable of bypassing this owner
must be excluded by package, process protection and CI policy.

Candidate execution discipline: one dedicated custody thread holds the reviewed
cross-process custody lock for its admitted lifetime; other service ingress,
SCM stop, revoke and watchdog notifications publish through the same private
ordering gate. The custody thread enters that gate for every state change and
for the final dispatch commitment and direct fixed native submission. No permit
escapes the gate and no untrusted delegate runs there. Release occurs only after
the gate closes admission and records terminal/fault status. Proposed lock order
is lifetime OS custody tenure, then private ordering gate, then bounded protected
store/journal access. IPC and UI locks never nest into this order. Exact timeout,
thread-affinity, queue fairness and native blocking behavior require review.

The production ordering boundary MUST be explicitly nonreentrant. Same-thread
reentry into ANY owner mutation or trusted helper path MUST be refused before
the nested attempt reserves an ID, mutates state, dispatches or performs an effect.
This includes recursive callbacks and reentry into Revoke, Stop, Fault, Prepare/
Admission or Dispatch, including an entrusted helper invoked from within the gate.
A reentrant monitor alone does not satisfy this requirement. Rejection MUST NOT
produce a nested effect or operation receipt, or convert MAY_HAVE_EFFECT into
clean cancellation. Any uncertainty MUST close admission and fault the owner into
RecoveryRequired through the outer owner path without recursive mutation;
MAY_HAVE_EFFECT remains sticky. This is a proposed design requirement, not an
installed or tested fix. P247's separate model reentrancy tests are not native
service evidence.

Revocation semantics MUST name the linearized event, not imply that arrival at a
pipe or SCM callback instantly cancels work. A revoke/stop/fault is acknowledged
as accepted only after the owner records its order. If it wins before Dispatch,
that operation has no effect submission. Fault still means RecoveryRequired,
not proof that earlier history was effect-free. If Dispatch wins, the owner
irreversibly records **MAY_HAVE_EFFECT** and latches **RecoveryRequired** before
any native call. Later revoke/stop/fault reports **TOO_LATE / MAY_HAVE_EFFECT**;
it cannot claim clean cancellation, success, absence or safe retry.

Holding a gate through native submission may delay lifecycle publication. An
out-of-process watchdog/SCM kill or machine fault cannot participate atomically:
the durable pre-effect intent therefore governs recovery. A watchdog MUST NOT
force-release a mutex and restart an effect owner. Stop acknowledgment, timeout
and uncertain termination require explicit platform decisions and fail-closed
receipts; bounded liveness is not assumed from monitor use.

Prepare binds a service-generated request ID to immutable operation, exact fixed
target/store identity, private candidate identity, caller/broker OS identity,
consent issuer, session and operation generation, protocol version and expiry.
IDs are reserved before delegated processing; mismatched categories and refused
well-formed attempts consume their reservation. No eviction may reauthorize an
old ID; capacity exhaustion denies. Durable consumed/revoked/reserved identities
must survive reconnect/restart. A new connection does not mint a new consent;
stale generations, changed payload/target, duplicate dispatch and consent reuse
are denied. A new process generation cannot erase operation history. Candidate
digests must not expose low-entropy secret material in logs or public journals;
the protected binding mechanism is a SEC-03/04 decision.

In-memory total order is NOT a transaction with Windows Credential Manager or
DPAPI/files. A crash can occur after intent but before submission, during native
execution, after effect but before receipt, or between terminal stores. At-most-one
authorized submission is the proposed safety target, not exactly-once physical
effect. Any unresolvable crash window remains recovery-only without retry.

## 4. Qualified effect-owner decisions: SEC-03 and SEC-04

No principal, ACL, storage mechanism, signer or pipe is installed/approved here.

| Decision | Alternatives / mandatory independent resolution |
| --- | --- |
| Exact service identity (SEC-03) | Choose and record literal SCM logon principal, account SID, restricted service SID and SID type, token restrictions/privileges, logon rights, profile loading and reboot behavior. P216's `NT SERVICE\NayeonByokCustody` is a proposal only. **No default LocalSystem**; an alternative requiring it needs explicit necessity and threat acceptance. |
| Windows Credential Manager | Service-principal-owned vault and fixed new target only if actual profile, effective token, reboot persistence and ordinary-user isolation are proved. `LOCAL_MACHINE` persistence in the Python adapter does not establish service ownership or a machine-global vault. Never inherit the interactive user's WinCred store. |
| Protected DPAPI file | User-scoped protection under the distinct approved service token, protected file/directory plus separate anchor and journal; prove decryptability after legitimate restart and denial to other users. Machine-scope DPAPI is not acceptable cross-user confidentiality. ACLs remain necessary; encryption alone does not exclude deletion/rollback. |
| ACL design (SEC-03) | Exact SDDL/owner/inheritance for installed images/parents, store, journal, independent anchor/history witness, lock and pipe; permitted installer/recovery rights; no ordinary-user mutation or handle leakage. Literal descriptors await selected account and qualified review. Reparse, hardlink, backup/restore and update paths are in scope. |
| Impersonation | Peer observation may use tightly scoped impersonation; MUST revert and verify effective thread/process service identity before protected access. No effect/journal work while impersonating a client. Revert failure faults owner and stops dispatch. Decide privilege removal and audit policy. |
| Signed broker/service/installer (SEC-04) | Named qualified publisher, signing-key custody, trust chain/revocation/expiry and full dependency manifests; enforced Code Integrity/UMCI covering EXE/DLL/.NET/script and dynamic/native loading. Reject wrong signer, unsigned dependency, substituted path/file ID and update downgrade. Hashes and source scanning alone are not loaded-code enforcement. |
| Authenticated named pipe | Explicit server and client OS token/session/integrity checks, protected endpoint, remote rejection, server spoof/squatting defense and channel binding. Resolve same-user malicious client and process-ID reuse with actual retained OS identity and approved loaded-image evidence. Claimed PID/SID or same-user match never grants consent. |
| One-use human consent | Trusted broker ceremony bound to operation, exact target, private candidate, request ID, service epoch/generation, user/session, version, trusted expiry and destructive acknowledgment. Service-owned consumption/revocation is durable. No bearer approval, boolean, UI name, arbitrary digest or reconnect renews authority. Clock rollback/reboot invalidates ambiguous expiry. |
| Durable recovery / antirollback | Select genuinely independent monotonic witness and enrollment/recovery authority, backup/restore model, account/profile loss, uninstall and re-enrollment handling. Matching rolled-back journal+anchor is not proof of current history. If a suitable rollback root cannot be justified, admission stays HOLD. |

No silent read, copy, migration, reuse or deletion of existing interactive-user
credentials is permitted. Any future migration requires separate user and security
decisions. Administrator/kernel compromise, backup authority and policy-owner
power require a named threat-model decision; do not claim local ACLs defeat every
administrator or whole-VM rollback.

## 5. Mandatory effect-ENTRYPOINT EXCLUSION

The successor production package MUST NOT retain valid alternate production
effects in `local_byok_user_scope.py` or `windows_credential.py`. A wrapper,
monitor, disabled menu, fake backend, source allowlist or "private" Python name
does not remove direct import/native authority. Both package exclusion and an
independent OS protection boundary for the new service store are mandatory.

| Known route / caller inventory | Required exclusion and negative evidence |
| --- | --- |
| `application.py` Connection callback -> `LocalByokLaunchBridge.launch` -> source child module | Approved production artifact has no launch/import fallback to the old child. Exercise source/frozen/CLI and reconnect paths against final artifact; record refusal before old effect route. |
| `local_byok_window.main` / module `__main__` -> factory -> `LocalByokController.approve` | Old manual window/controller is not a production credential actor. Prove old module/CLI absent or unreachable in signed artifact and old source process denied the new store by OS identity. |
| Direct import `WindowsCredentialBackend().put/delete`; `_adapter` -> `_Advapi32Adapter.write/delete`; direct `_load_advapi32` / ctypes native call | These bypass controller and service monitor. Package/dependency closure must exclude backend/native helper loading; raw native callers under ordinary tokens must still lack new store custody. Import denial alone cannot prove OS isolation. Include `get/is_available` and raw read attempts in confidentiality tests. |
| Native old `PendingCustodyTransaction` -> state interface; P99 `PendingServiceState` -> `PendingWinCredStore.SaveOrReplace/DeletePending` -> native APIs | Preserve original denial guards and historical files; exclude legacy effect composition from successor signed assembly. No toggling old switches to create the new actor. Test alternate same-assembly and older artifact callers against selected OS boundary. |
| `tests/test_windows_credential_backend.py`, `test_local_user_scope_byok.py`, `test_p206_unified_effect_ownership.py`, `test_p207_user_scope_native_consent_review.py`; `scripts/p137_frozen_byok_fake_tk_smoke.py` | Known direct constructor/adapter/fake routes. Keep test/development assemblies and scripts outside production trust graph; a `_native` fake argument is not production authentication. Do not execute them in P250. |
| `tests/test_p134_real_wincred_ephemeral.py` | Known genuine native test route: backend construction and `put/delete` with ephemeral synthetic namespace under explicit hosted-runner conditions. It is not ordinary regression permission on Kristian or proof of service isolation. Exclude from production artifact and require separate authorized VM successor test scope. |
| `tests/test_provider_connection_startup.py`, `tests/a04_recovery_test_support.py`, `tests/test_pre_829_a02_fake_isolation.py` | Backend imports/native-loader mocking or interception demonstrate test/import surfaces, not a new production owner. Final dependency inventory must account for them without crediting mocks as OS denial. |
| P211 quarantine, P216 inventory, P220 artifact closure; static references in migration/security tests/scripts | These inspect source/artifacts or assert refusal; textual mentions are not native callers. They cannot enforce OS isolation. Dynamic import, DLL injection, arbitrary interpreter/CLI, copied backend and stale installed binaries remain adversarial routes to test. |

This is the known tracked-source route inventory from bounded textual search and
the inspected call chains, not proof of all runtime-loaded callers. A future
qualified reviewer must reconcile a full source/import/CLI/test/build manifest,
transitive dependencies, frozen resources, test defines, installed files, loaded
images and every native credential binding. Unexplained route or dynamic loading
means HOLD. Older user vault data remains in a separate namespace and retention
policy; it must never be accepted as the successor's protected service state.

**Proof plan only, no code edited or VM launched:** after independent environment
and SEC decisions, copy exact hash-bound source/artifact into an approved disposable
Windows VM without real keys, network/provider or shared host secrets. First
inspect the signed package/dependency manifest and enforced CI policy. Then use
separately approved synthetic non-secret fixtures and test identities, with exact
token/profile evidence, to attempt new-store read/write/delete from the old UI,
source CLI, direct backend, copied native caller, same-user malicious process,
another user, stale service and unsigned/wrong-signer process. Test load refusal
and OS store denial separately. A same-named user-vault write can succeed in its
own unrelated vault; it must neither mutate nor be read as the service vault.
Capture actual OS errors, before/after service-store identity and protected
metadata, CI events, process/image identity, native exits and cleanup receipts.
Mocks or a monitor counter cannot satisfy these negative tests. No real keys or
credential effects are authorized by this plan; any later synthetic OS mutations
require their own explicit environment, target and cleanup authorization.

## 6. Candidate lifecycle, durable sequencing and recovery

Names below are prose states, not deployable types or effect APIs. Recovery is a
sticky safety barrier; ordinary operations never clear it.

| State / event | Proposed ordered behavior / next state |
| --- | --- |
| Boot, restart, missing/claimed-clean history | UNAVAILABLE / RecoveryRequired. Authenticate installed identity, lock tenure, enrollment and current durable witness before any separately approved READY decision. Never trust a caller's clean claim. |
| Qualified enrollment/recovery decision | May establish a new admitted epoch only through distinct reviewed authority and durable witness transaction. Does not revive prior consent or operation IDs. This mechanism remains undecided. |
| READY + valid admission | Reserve ID, freeze operation/generation and protected candidate binding; PREPARED only after authenticated consent and policy prerequisites. Shape validation alone grants nothing. |
| PREPARED + revoke/stop first | Consume/invalidate pending consent, persist cancellation if trustworthy, close that operation; CANCELLED_BEFORE_DISPATCH. Zero submission for that operation only. Stop closes all admission. Persistence uncertainty -> recovery. |
| Any pre-dispatch state + fault/unknown history | RecoveryRequired, close admission, no new dispatch; do not infer earlier effects absent. |
| PREPARED + dispatch sequence | Under continuous custody and owner order, persist consumed approval plus IN_FLIGHT intent with identity/sequence; flush, verify independent anchor/witness advancement and exact readback. Recheck current owner state/expiry within same boundary. Any partial failure -> recovery without dispatch. |
| Durable intent + final Dispatch wins | Atomically set in-memory MAY_HAVE_EFFECT and RecoveryRequired, consume dispatch attempt, directly submit at most one fixed operation under private owner boundary. Never return a permit for later external invocation. |
| MAY_HAVE_EFFECT + stop/revoke/fault/disconnect | Retain MAY_HAVE_EFFECT and RecoveryRequired; TOO_LATE/unknown outcome. No clean cancel, reset, retry, rollback-as-success or implicit recovery. Disconnect does not erase custody. |
| Native return / receipt | Record result as unverified/unknown until operation-specific physical storage evidence and durable terminal pair/witness verification. Presence alone is not exact-value, durability or provider validation. |
| Terminal metadata verified | TERMINAL_UNVERIFIED records what was proved; does not clear recovery or admit another effect in this initial conservative design. Any later return to READY requires a separately approved verification/recovery decision. |
| Crash, abandoned lock, failed release, service kill, profile loss or uncertain termination | RecoveryRequired across restart. Do not replay IN_FLIGHT or assume no effect from missing terminal. Evidence inspection never repairs history. |

Each protected intent must bind machine/install enrollment identity, selected
service principal/store, approved loaded-code/version identity, epoch and operation
generation, durable sequence/request ID, operation/target, private candidate binding,
consent issuer/session/expiry/consumption and predecessor record/witness identity.
No secret plaintext or public secret-derived fingerprint belongs in audit evidence.
Record integrity/authentication and protected storage handles need SEC-03 choices.

The journal transaction boundary is a recoverable protocol, not a cross-store ACID
claim. Journal, separate anchor and independent history witness require specified
compare/prior-identity checks, write/flush/readback ordering and torn-write handling.
Crash between any pair must deny. The native effect is outside that durable
transaction, so both "intent with no call" and "effect with no terminal receipt"
are deliberately indistinguishable without independently justified recovery evidence.
Do not undo/delete a possibly stored credential as an automatic compensation.

Cross-process lock identity, protected namespace/DACL, service-thread ownership,
abandonment detection and release-to-fault publication MUST cover all service
instances and epochs, including stale processes and multiple Windows sessions.
An in-memory singleton is insufficient. Retained OS handles and epoch fencing
must prevent stale owners from continuing; a durable number alone cannot fence
an old process that still holds effective store authority. If quiescence or
exclusion cannot be proved, do not start a new owner. Startup needs a protected
crash/dirty marker before READY; absence or rollback cannot mean clean enrollment.

Separate anchor files/registry values in one rollback domain are not independent
antirollback. SEC-03 must define witness monotonicity, reset authority, backup,
VM snapshot/clone, disk restore, uninstall, OS reinstall and account/profile loss
scope. Restoring all local data can defeat local hash chains. No hardware/external
root is assumed installed. No credible witness or recovery identity means HOLD.

## 7. Tests and evidence acceptance matrix (not executed)

Every native receipt must bind source and artifact hashes, actual loaded identity,
environment/policy/VM identity, operator, timestamp, precise inputs, raw stdout/stderr,
actual native exit/error, independent reconciliation and protected custody retention.
Record failed/blocked attempts without substitution. No real keys/provider calls.

| Acceptance area | Synthetic/model evidence | Required later Windows-native / independent evidence |
| --- | --- | --- |
| Winner order: Save/Replace/Delete x Revoke/Stop/Fault | P247 18 forced orders, source only here | Deterministic barriers on actual successor: lifecycle wins -> zero native submissions; dispatch wins -> one at most and MAY_HAVE_EFFECT/recovery. Trace original P96 route too; no sleep-based race inference. |
| Reentry/concurrent duplicate | P247 source assertions | Actual private owner and bounded ingress under concurrency; no callback bypass, double dispatch, lock inversion or ID eviction reauthorization. |
| Adversarial recursive reentry denial | P247's separate model reentrancy tests are not native service evidence; this production requirement is not installed or tested | Force same-thread recursive callbacks into every owner mutation (Revoke/Stop/Fault/Prepare/Admission/Dispatch) and trusted helper path, including an entrusted helper invoked within the gate. Prove denial before nested ID reservation, state mutation, dispatch or effect, with no nested mutation, effect or operation receipt. Preserve MAY_HAVE_EFFECT and forbid clean cancellation; uncertainty must fault/recover through the outer owner path. |
| Duplicate/replay/generation | P247 finite in-memory reservation model | Cross-session/process/reconnect/reboot replay, altered category/target/candidate/version, old consent, queue saturation and stale generation all denied durably. |
| Start/restart/crash | P247 restart always recovery; no durable mechanism | Every intent/anchor/witness/native/terminal boundary crash, missing/claimed-clean/torn history, first install, dirty marker, profile loss, uninstall/reinstall and abandoned lock. No ordinary Save bootstrap. |
| Stop/fault/service failure | P247 enum publication only | Real SCM callbacks, blocked native call, watchdog/kill, release failure and uncertain termination; exact event acknowledgments, no restart until old owner excluded. Never clean cancellation after commitment. |
| Cross-user token/ACL | None | Actual account, restricted SID, privileges, process/thread token, ACL/ancestor/object handle proof; same-user/other-user/impersonated denial, service store/profile persistence over reboot. |
| Signer/Code Integrity | Compile guards/source scan only | Real approved signing chain, enforced CI/UMCI loaded graph, wrong signer/unsigned dependency/script/reflection/dynamic-load attempts, substitution/file-ID/rename races, revoked signer/update downgrade. |
| IPC / impersonation | P103 historical peer observation is not consent | Authenticated server and client tokens/session/integrity, squatting/remote/malformed clients, same-user spoof, PID reuse, handle transfer, failed revert; no protected work under client token. |
| Consent | Model IDs/category are not human consent | Trusted ceremony, exact operation/candidate/target/session/epoch/expiry, delete acknowledgment, revoke/clock rollback, consumed-state crash, malicious UI and reconnect replay. |
| Alternate effects | Textual known-route inventory only | Section 5 production package/load exclusion plus independent OS new-store denial from old Python/backend/raw native/stale binaries. Verify old user vault cannot satisfy service custody. |
| Durable recovery/antirollback | P247 uncertainty always holds | Torn journal/anchor, paired rollback, witness loss/rollback, VM clone/restore, disk full, ACL drift, failed flush/readback and native unknown result. No automatic replay, re-enrollment or silent migration. |
| Physical result | No effects in P247 | Separately authorized synthetic OS storage validation specific to chosen store; distinguish submission, durable receipt, actual result and provider validity. No real-key smoke. |

P247 has **0/54 x64 and 0/54 x86 runtime executions** due Application Control
and PowerShell policy blocks. Its 54 cases are loop-expanded, not distinct methods;
one future dual-architecture pass needs 108 architecture-specific case executions.
P249 authorization remains unissued; no policy bypass, alternate loader or signing
workaround is permitted. Synthetic model PASS, even if later obtained, cannot
close P96 or any native row above. Repeats do not increase unique case coverage.

## 8. Source-preserving future phases, only after independent decisions

This is a plan, not permission to implement. Keep all historical files and sealed
tags immutable. New scope requires a separately approved bounded successor.

1. Obtain authenticated independent SEC-03/04 decisions, threat-model scope,
   storage/recovery design, named owners and explicit disposable-VM authorization.
   Resolve original P96 ownership and alternate routes before designing effects.
2. Design the selected service owner, exact principal/token/profile and store,
   journal/anchor/witness identities, lock lifetime, crash protocol and recovery
   authority. Review these together; unresolved durable atomicity stays HOLD.
3. Establish reviewed signed installer/broker/service and enforced loaded-code
   CI/UMCI gate, full manifest and update/rollback policy before any effect-capable
   binary is admitted. Do not weaken current host policy.
4. Implement separately scoped authenticated IPC and operation-bound one-use
   human consent, first in denial-only form; independently test same-user hostile
   clients and impersonation restoration before composing protected storage.
5. Implement reviewed journal/effect dispatch boundary with fixed private owner,
   revoke/stop/fault total order, epoch fencing and durable consumed intent.
   Prove deterministic zero-submission/dispatch-first outcomes; no generic adapter
   permit returned to an external caller.
6. Exclude original Python effects, source CLI and legacy native composition from
   the signed production package; separately establish OS store isolation. Preserve
   original source as historical evidence rather than editing its denial guards.
7. Run authorized automated adverse Windows-native tests with synthetic non-secret
   fixtures only: forced schedules, crash/reboot, cross-user/ACL, signer/IPC/consent,
   old-route exclusion and durable recovery. Use exact identity and cleanup receipts.
8. Obtain qualified independent source/security/evidence review. Repair material
   findings in separately approved scope and repeat affected/adversarial evidence.
   Preserve all original four P76 FAIL methods and account for their genuine closure
   without skips, weaker assertions, substitute properties or waivers.
9. Only after approved integrated scope and relevant failures close, complete
   **3 unfiltered authoritative Windows whole-product regressions**, appropriate to
   the approved pre-stage/staged/immediate-child workflow. This plan performs none
   and authorizes no staging, commit, tag, push or seal. Human seal review remains
   separate; real-key/production authorization is not implied by synthetic evidence.

Stop safely on missing owner/approval, unexpected source/Git/artifact/loaded identity,
unknown root cause, material regression, missing OS exclusion, stale owner, uncertain
native outcome/termination, storage mismatch or policy refusal. Close admission,
preserve uncertainty and evidence, avoid retry/compensation and retain checkpoints.
For an authorized later workload stuck five minutes, inspect identified process/logs
immediately and stop/pivot under its approved bounded termination plan; never bypass
App Control or use broad process kills. No implementation begins in P250.

## 9. Risk register and qualified decision request

This is a bounded current decision package, not a previous-phase retrospective
audit. Missing evidence remains visible; no historical failure is waived.

| Risk / severity | Cause and impacted callers | Required decision/evidence / current disposition |
| --- | --- | --- |
| P96 check-to-effect race / High | Separate approval/ownership probes and effect callbacks; original coordinator and alternate effects | Independent native architecture/security review of one actual private owner plus deterministic original/successor evidence. OPEN / HOLD. |
| Alternate Python/native authority / High | Imports, CLI, old UI and raw native APIs bypass service monitor | Signed package closure, CI graph and independent OS store-isolation negatives. Unimplemented / HOLD. |
| Principal/store confusion / High | User vault, service vault, impersonation, profile loss; inherited LocalSystem assumptions | SEC-03 exact principal, restricted SID, ACL/SDDL and selected store/reboot receipts. Pending / HOLD. |
| Forged consent/IPC/loaded code / High | Same-user token is not trusted app or human intent; unsigned dependencies/stale images | SEC-04 signed graph, enforced CI/UMCI, actual OS peers, ceremony and durable one-use bindings. Pending / HOLD. |
| Crash/rollback/duplicate effect / High | Independent durable writes and native effect lack shared transaction; stale process remains authoritative | Protected monotonic witness, recovery protocol, cross-process fencing, crash matrix; no exactly-once claim. Pending / HOLD. |
| Lifecycle starvation / High | Native call can block gate, SCM/kill not atomic with dispatch | Platform owner approves bounded stop/watchdog/termination semantics and receipts; uncertainty never becomes clean cancel. Pending / HOLD. |
| P247 evidence overclaim / Material | Compile success/54 source cases mistaken for execution or production proof | Environment owner authorization and independent x64/x86 receipts per P249, then separate native acceptance. Runtime 0/54 each / HOLD. |
| P76 regression substitution / Material | Later property assertions mistaken for original method closure | Preserve 4 authentic original FAIL methods, reproduce/repair only in approved scope with original evidence and independent review. Unwaived / HOLD. |
| False milestone/release assurance / High | Author draft or PR treated as qualified sign-off | Named independent decisions, approvals 0/7 and product regressions 0/3 remain explicit. REAL-KEY NO-GO / PRODUCTION RELEASE HOLD. |

| Requested qualified owner | Concrete reviewable output expected | Current status |
| --- | --- | --- |
| SEC-03 Windows service/principal/store security owner | Signed source-bound decision selecting exact account/SID/token/profile, ACLs, store option, journal/anchor/witness, rollback limits and recovery/migration policy; permitted VM scope and required OS evidence | NOT ISSUED |
| SEC-04 Windows signing/CI/IPC/consent security owner | Signed source-bound decision on publisher and loaded graph, CI policy, broker/peer/human consent, private owner boundary and exclusion evidence; explicit rejection/conditions where unresolved | NOT ISSUED |
| GOV-01 independent threat-model owner | Same-user, cross-user, admin/kernel, backup/VM rollback threat assumptions and residual risks accepted only within named scope | NOT ISSUED |
| GOV-02 retention/recovery owner | Existing user-vault retention, no silent migration, deletion/re-enrollment authority and privacy constraints | NOT ISSUED |
| REL-05 independent security reviewer | Exact final source/artifact and adversarial evidence acceptance after implementation; trace older/alternate callers and all material repairs | NOT ISSUED |
| REL-06 independent Windows validation owner | Three complete unfiltered product regression receipts; actual native exits, source topology and original failures accounted for | 0/3 |
| REL-07 production install/change/rollback owner | Separate installation/update/rollback and production acceptance with exact scope; no promotion from model or design review | NOT ISSUED |

Each decision needs actual named person/organization, role and authority,
independence/conflicts, source/artifact identities, environment, date/expiry,
revocation route, evidence location and a signed GO/HOLD/REJECTED disposition.
Roles above are requests, not appointments. The environment/platform/App Control
owner must additionally authorize any future disposable VM execution chain;
P249 draft PR #171 grants none. A limited synthetic trial GO cannot approve real
keys, product progression or production. A Codex-authored assessment cannot fill
these independent fields.

## P250 source/format review disposition

Only this additive document is in scope. Original C#, Python, scripts, tests,
P245/P247/P248/P249, historical files and `.codex/CURRENT_STATE.md` remain unchanged.
Review consists of source/reference/hash inspection and Git status/diff whitespace
checks, including an explicit untracked-file whitespace check. No runtime result,
independent approval, source repair, stage/commit/tag/push/PR or sign-off is claimed.
No Drive workbook/dashboard update or previous-phase retrospective audit occurred.

**P250_ARCHITECTURE_DRAFT_READY; implementation and qualified decisions HOLD.**
Precise outstanding gaps are SEC-03 principal/store/ACL/recovery selection,
SEC-04 signing/CI/IPC/consent/owner approval, actual package and OS effect exclusion,
durable witness/fencing/physical-result evidence, authorized P247 runtime evidence,
original P96 closure, four unwaived original P76 failures, qualified approvals
**0/7** and product regressions **0/3**. **REAL-KEY NO-GO; PRODUCTION RELEASE HOLD.**
