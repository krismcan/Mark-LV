# BYOK C1 P104 — Production admission, consent-to-effect and recovery architecture (review request)

Date: 7 November 2026 | OM v2.1 | Disposition: DESIGN-ONLY, NOT IMPLEMENTED, G0–G6 HOLD

Canonical starting source: P103 draft PR #27, commit b27f4103bc4607c5ad54b8bf26a8f286b77f646b (sole child of P102 d0989ea0e814ffe2537cd9f3a168bc744e5af13c). P103 is a genuine current-user Windows pipe peer-identity denial experiment, NOT trusted elevated consent. Its duplicate PR #28 was closed unmerged and must not be reincorporated. This P104 document adds no executable source, service installation, credential, permission or release switch. It is a decision package for a qualified external Windows-native security reviewer, not a self-approval.

## 1. Verified starting facts and exact source-change targets

| Current code | Observed contract/problem | Proposed change after qualified approval |
| --- | --- | --- |
| Original P49 CustodyService.cs: OnStart, Main | Disabled service chassis; no authenticated listener; LiveEligible is false | Separately reviewed installed service host, authenticated local IPC and service-owned admission actor. Do NOT wire this old host to effects now |
| Original ServiceGate.cs: LiveEligible, HandleUntrustedRequest | Binary and manifest proof hardcoded false; untrusted request returns unavailable | Independent signed code/install provenance and release attestation required. No boolean flip as an implementation |
| P102 native_c1_candidate/ServiceBoundRequestIdentity.cs | Immutable operation/session/request/claimed digest/expiry; all claims untrusted | Request parser only. New service-computed candidate binding and service-issued, non-transferable, one-use approval record required |
| P103 native_c1_candidate/DisposablePipePeerEvidence.cs | Real named-pipe RunAsClient SID can identify a same-user peer; forged trusted-UI marker is denied | Do not promote this test pipe or SID equality into LocalSystem trust. Reviewer must select signed UI provenance and OS-authenticated IPC design |
| P102 native_c1_candidate/ServiceOwnedAdmissionBoundary.cs | Service-private lock, structural duplicate refusal, fault and stop; no actual native dispatch | Replace denial-only candidate with reviewed single-owner terminal admission/dispatch state machine; preserve denial until approved |
| Original PendingCustodyTransaction.cs: Apply (~125–223, especially final ApprovalCurrent and effect ~191–212) | ApprovalCurrent is not jointly serialized with revocation and subsequent native effect; P96 shows deterministic fake-effect race | Retire old effect admission. Move final consent, revocation, fault, intent durability and dispatch into successor service-owned actor; DO NOT enable old Apply |
| Original ServiceCustodyMutex.cs: Acquire/Tenure (~73–205) | Same-thread named Windows mutex with sticky-fault logic, but separate from consent authority | Integrate a single-thread custody tenure with the actor and specify/verify lock ordering and failure publication |
| Original PendingServiceState.cs: ForInstalledService, LegacyEffectEntryDisabled | Protected state entry disabled, no trusted consent/dispatch | Keep true until successor reviewed; avoid exposing SaveOrReplace/DeletePending as generally callable internal effect routes |
| Original PendingWinCredStore.cs: NativeMutationAdmissionPending and CredWrite/CredDelete | Fixed pending target and disabled native adapter; LocalSystem persistence unverified | Review only after G1–G3; single sealed adapter call from actor, synthetic data first. Keep guard true meanwhile |
| Original CustodyLedger.cs: AppendIntent, AppendTerminal, Verify | Bounded append-only structural SHA-256 chain, not cryptographic authentication | Treat as nonsecret format; require genuinely protected enrollment, independent rollback/fault witness, durable consume and no automatic retry |
| Original CustodyJournalFile.cs: Append | Exclusive write-through append and Flush(true), protected directory preflight; not atomic with HKLM | Independent flush/readback/fault evidence and crash injection; no file-only success inference |
| Original CustodyRegistryAnchor.cs: WriteAnchor, RecoveryFaulted, RegFlushKey | Protected registry anchor/fault state; missing marker is fail-closed | Reviewer must prove principal/ACL/ancestor/install/reboot and rollback assumptions; cannot treat paired hashes as an authenticated witness |
| Original ProtectedAcl.cs, RecoveryReader.cs | Read-only protection and metadata preflight | Extend only with reviewed exact installed-service security model, not relaxed ACLs or automatic state initialization |

Frozen original 11 P49 C# units, original P85 historical source-integrity gate, P62 platform refusal evidence, Kristian's Windows x86 enterprise Code Integrity refusal and the original product worktree with 17 preexisting changes are outside the permitted edit scope.

## 2. G1 — trusted consent and authenticated local IPC: authority design to review

1. Security principals are explicit: a machine-protected, reviewed signed service binary; a separate approved local user-interaction broker with independently proven code origin; and an untrusted normal client. A Windows account SID alone does not distinguish the intended UI from another same-user process (P103 result). PID, a caller-provided string, digest, a self-declared elevation bit, or a one-byte 'trusted UI' marker cannot constitute authorization.
2. All inbound fields are parsed as untrusted, length-limited, versioned, with fixed operation enum and fixed pending target. No network listener, arbitrary credential target, provider-side validation, caller-chosen file root or executable path. Reviewer chooses and proves appropriate Windows local IPC peer verification and channel protection, including impersonation policy, install/signer provenance, session isolation, token privilege/elevation checks and malicious same-user process threat.
3. A genuine trusted, explicit local UI action must bind the exact SAVE/REPLACE/DELETE operation, the intended pending-only target, service-derived digest of the exact candidate bytes privately held for one attempt (not the caller's P102 SHA-256 claim), user/session, server-generated request ID, short trusted expiry and DELETE acknowledgement. No secrets or transferable bearer approvals in logs, PRs, telemetry, the untrusted app or persistent evidence.
4. Only the reviewed trusted service/consent issuer may create an authoritative record. Persist one-use consumed/revoked state in a protected namespace before any native dispatch, including across process crashes and restarts. If consumed-state durability is uncertain, enter RECOVERY_REQUIRED; never recreate, auto-rearm or reuse an unverified ticket. Metadata-only in-memory HashSet from P102 is NOT this store.
5. Reviewer must decide how the signed local approval UI is genuinely authenticated and protected against a malicious same-user process. Do not pretend Windows SID match, UAC alone, pipe ACL alone or author-signed test binaries proves user intent. Until that review outcome, G1 remains HIGH/HOLD and there is no real consent issuance.

## 3. G2 — exact dispatch linearization and locking contract

Proposed terminal actor states: UNAVAILABLE; READY (only after all independent gates); REQUEST_PENDING; APPROVAL_ATTESTED; ONE_USE_CONSUMED; INTENT_DURABLE; DISPATCH_COMMITTED; TERMINAL_DURABLE; REVOKED; RECOVERY_REQUIRED. These are architectural names, not implemented types. Denial remains the only possible effect in current code.

- One service-owned actor owns immutable operation, privately held exact candidate bytes, a trusted approval record, revocation/fault/stop, durable ticket consumption and the **only** route to one fixed native pending WinCred effect attempt. Client code, UI code and any generic callback must not run inside the terminal service monitor.
- Proposed global lock order for independent review: service actor monitor -> ServiceCustodyMutex manager gate/native tenure -> protected custody state. No other code path may acquire the actor monitor while holding the custody manager lock. Native mutex acquisition must be non-waiting/fail-closed and on the same thread that releases it; explicitly test that a native callback cannot reenter and that Monitor's C# reentrancy never permits a second in-flight dispatch. Reject parallel requests, not queue an unbounded backlog.
- Within the single actor critical section and same-thread custody tenure, revalidate trusted consumed approval and exact service-owned candidate; verify protected history; durably append and anchor the IN_FLIGHT intent; read back both; then make one explicit irreversible DISPATCH_COMMITTED decision and at most one synchronous native pending-only effect call. Do not release actor authority between final permission check and dispatch. An actual effect may have happened once a dispatch attempt is committed, even if the native call returns an error or its result is unknown.
- Revocation/fault/stop that **commits under the actor authority before DISPATCH_COMMITTED** denies native effect: zero attempts. Once DISPATCH_COMMITTED wins, later revocation is too late; UI MUST NOT say 'cancelled' or 'no key stored'. Return pending/unknown until terminal durability is verified. Never automatically retry on uncertain effect.
- After the native single attempt, write and independently verify a terminal journal+anchor record, mark tenure terminal only after both readbacks, and release OS mutex under the same thread. Errors at any point after protected custody begins produce sticky RECOVERY_REQUIRED. If native mutex release is uncertain, retain fault and disallow next tenure. No old PendingCustodyTransaction.Apply, caller-supplied StillCurrent callback or mutable test effect delegate may be used as production permission.
- This is a proposed synchronous critical-section design, not proof. The reviewer must analyze monitor reentrancy, possible blocking IO, lock inversion, service stop during dispatch, thread interruption, process termination, native API uncertainty and cross-process races **before** code is written or gates enabled.

## 4. G3 — durable journal, anchor, replay and fault crash matrix

Two separately durable stores (journal file and HKLM anchor) do not form an atomic transaction. Even exact SHA matches are structural unless the OS namespace and independent enrollment/rollback authority are proved. The installed LocalSystem principal, file/registry owners, inherited ACEs, ProgramData ancestor permissions, registry views, service image signature, per-machine enrollment witness, fault-marker transitions, platform shutdown semantics and reboot persistence need independent evidence.

| Failure point | Minimum permitted post-restart disposition |
| --- | --- |
| No verified enrollment or either protected store absent | UNAVAILABLE/RECOVERY_REQUIRED; never silently create a new initial ledger |
| Approval consumed, but durable one-use record unknown/missing | RECOVERY_REQUIRED; never reuse old approval or infer no effect |
| Intent journal append fails or anchor flush/readback mismatches | RECOVERY_REQUIRED; no native dispatch |
| Both intent records durable but before native effect | RECOVERY_REQUIRED after restart, including when effect possibly not attempted; no automatic retry |
| Native WinCred invocation returns error, times out or process dies around call | RECOVERY_REQUIRED; possible effect cannot be rolled back or automatically retried |
| Terminal journal appended but anchor update/readback fails | RECOVERY_REQUIRED; no success assertion |
| Journal/anchor terminal verified, but OS mutex release or protected fault state is uncertain | RECOVERY_REQUIRED; no next tenure |
| Stale/rolled-back paired records, corrupt/truncated history, replay, missing fault marker, or physical pending-presence mismatch | RECOVERY_REQUIRED; independent manual authorized recovery only |
| Fully witnessed terminal records, verified single native return, OS tenure released, no fault | At most STORED_UNVERIFIED/REMOVED_UNVERIFIED; never provider validation or actual durability guarantee |

Manual recovery must be a separately designed signed/admin-reviewed workflow with independent historical evidence; this design does not add any reset, reenrollment, repair, retry, or reconciliation operation. Audit logs must record no secret, digest claim, raw SID, reusable token or sensitive IPC payload.

## 5. Dependency-ordered implementation and evidence gates

A. Independent reviewer and Windows signing/security administrator first agree a concrete trusted UI provenance scheme, exact IPC principal/SDDL and channel authentication, signed release manifest/install path, service identity, threat model and G0 historical source admission. Record reviewer identity, line-specific verdict, fixed SHAs and authority boundary. Do not appoint a reviewer based merely on GitHub contributor access.

B. Only after design approval, implement a **non-deployable successor integrated into the actual candidate host and original protected-state interfaces**: trusted consent lifecycle, durable one-use consumption, terminal actor, native mutex integration, sticky recovery. No P49 gate changes, real keys, service installation or WinCred effects at this stage. Tests must target the integrated source, not a new disconnected fake-only model.

C. With controlled fault injection, prove revocation wins => zero native calls; dispatch wins => at most one; fault/stop/reentrant attempt => no extra effect; journal/HKLM mismatch, failed flush, crash at every boundary and restart => sticky recovery without retry. Verify original P96 negative comparator STILL reproduces legacy bug, and new successor tests do not use the old Apply route. Preserve native exits, original hashes, source readback and P85 strict source test.

D. After genuine G1–G3 reviewer GO and G4 pending-only source review, authorized signed test path may exercise one synthetic LocalSystem fixed-target WinCred attempt and persistence/error semantics. Windows x86 remains blocked until security administrator provides approved signing path; do not repackage or bypass the existing policy.

E. Final G0–G6 implementation GO; three complete native Windows product regressions; clean seal/CI/readback; production release; original same-ID Google Drive master workbook update and readback **before** dashboard update; only then direct user to enter a real API key locally. C2 provider validation is separate.

## 6. Questions requiring external written decisions

1. Who is the actual qualified Windows native security reviewer, with independent affiliation, GitHub identity, source scope, and explicit G0–G6 verdict? None assigned now.
2. What is the *authenticated* trusted local UI provenance and explicit user-consent ceremony beyond a same-user SID or UAC assumption? How does the service bind actual candidate bytes without leaking secret material?
3. Does the proposed actor monitor -> custody-manager lock order hold for all actual code, exceptions, OS calls, stop/fault and recovery entrypoints? Show counterexamples.
4. What protected durable witness prevents replay, paired journal+HKLM rollback, phantom initial enrollment, and an uncertain native mutation being silently retried?
5. Which signed/managed Windows x86 test execution path is approved by the machine's policy owner? No alternate path or policy bypass is permitted.
6. What are the exact staged acceptance proofs and source hashes before any real WinCred/native privileged effect is eligible?

## 7. Follow-on source review findings: capability topology, service startup, and impersonation (8 November 2026)

This section is a **source-specific refinement**; not a native effect permission. It corrects any interpretation that a shared monitor, a successful SID observation or toggling old guards could make the original host production ready.

### A. Effect capability isolation (G2/G4)

- Original `IProtectedPendingState` in `PendingCustodyTransaction.cs` exposes `SaveOrReplace(byte[])` and `DeletePending()` alongside read-only metadata and journal operations. Its concrete `PendingServiceState.cs` forwards those calls to `PendingWinCredStore`, while the old transaction accepts an injected `ITrustedPendingApproval` and checks `StillCurrent()` separately from effect dispatch. Therefore simply flipping `ServiceGate.LiveEligible`, `PendingServiceState.LegacyEffectEntryDisabled` or `PendingWinCredStore.NativeMutationAdmissionPending` would expose the P96 race and preserve overly broad effect capabilities.
- **Required proposed successor:** separate read-only custody observation and journal operations from sealed native-effect capability. The **only** effect-capable dependency must be held privately by one service-owned terminal dispatch actor after trusted consent/revocation/fault/intent checks, with static analysis proving no other path, reflective entry, IPC route or legacy transaction can invoke it. Do **not** wire `PendingCustodyTransaction.Apply()` into an installed service; retire the original coordinator from the future deployed effect assembly after independent migration review. A `bool` or assertion at call-site is not a capability boundary.
- **Acceptance counterexamples:** alternate same-assembly caller invoking `PendingServiceState.SaveOrReplace` directly; reflective invocation of an internal method; legacy coordinator with caller-defined approval; second service actor instantiated after a fault; duplicated dispatch capability across threads. Each must fail at the architecture/API boundary, not only when the original three denial flags happen to remain true.

### B. Startup admission cannot be enabled by ordinary code change (G2/G3/G5)

- Original `ServiceCustodyMutex.cs` starts with `faulted=true` and its only synthetic unarm method is behind `#if BYOK_TEST`. Production has no reviewed startup reconciliation that can attest to a fault-free same-machine, same-credential-vault session. `CustodyRegistryAnchor.RecoveryFaulted()` defaults to faulted when the protected fault marker is absent or non-CLEAR, and no recovery-authorized installation/enrollment action is currently part of the original 11-source service host. Original `PendingCustodyTransaction.Apply()` additionally refuses when either journal or anchor is absent.
- **Required proposed successor:** a separately reviewed installer/enrollment authority, protected independent witness and explicit **manual recovery authorization** must precede any path to READY. Device reboot, process crash, lost/stale journal, anchor or mutex ownership uncertainty must deny automatically. Never implement an unconditional `faulted=false`, `CLEAR`, state reset or auto-bootstrap to move past this prerequisite.
- **Acceptance counterexamples:** first ordinary SAVE on a fresh machine; reinstall after losing anchor; replay old protected-looking journal+anchor; crash after native attempted but before terminal metadata; delayed dispose or wrong-thread native mutex release. None may create a new approvable custody session automatically.

### C. The LocalSystem-vs-client impersonation boundary is security-critical (G1/G4)

- In Windows `.NET`, `NamedPipeServerStream.RunAsClient` impersonates the *connected client on the executing server thread*. This can be useful for peer identity inspection but is not signed UI provenance; the P103 experiment correctly grants no approval. Native WinCred calls from an impersonated service thread could run under the **client's** account context rather than the intended LocalSystem vault. A future privileged custody service must separate transient peer identification from the protected service-owned storage operation, and independently verify its effective security context before any protected-state access.
- Microsoft documents `CRED_PERSIST_LOCAL_MACHINE` as persistent **for subsequent logon sessions of the same user on the machine**, not a machine-global credential shared across user principals. Therefore testing a user-profile credential does not validate LocalSystem custody or persistence. The fixed pending target, native error semantics, LocalSystem environment/profile and a reboot must be verified on an authorized signed test path before claiming G4 approval.
- A pipe's reported client PID (`GetNamedPipeClientProcessId`) or a matching SID is useful diagnostic identity, **not** independent proof of intended approved UI binary or human consent; a malicious same-user client and TOCTOU around process identity remain in scope. No caller-provided PID, SID, digest, marker or UI name can mint the one-use service authorization.
- **Acceptance counterexamples:** request uses forged 'trusted UI' marker; same-user untrusted process connects; service mistakenly calls WinCred while impersonating; client disconnects/reconnects to reuse request; user-vault credential is misreported as LocalSystem pending credential. All must fail closed without provider connection or real key.

Official Microsoft references (consulted for this refinement):
- Client impersonation: https://learn.microsoft.com/en-us/windows/win32/secauthz/client-impersonation
- NamedPipeServerStream.RunAsClient semantics: https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.namedpipeserverstream.runasclient
- CREDENTIALW and CRED_PERSIST_LOCAL_MACHINE scope: https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw
- GetNamedPipeClientProcessId provides a process identifier, not approval: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid

This refinement changes **no executable files** and is NOT a substitute for qualified independent native Windows code review. All original G0–G6 HOLD decisions remain.

## 8. Existing Python C1 surfaces are not an approval issuer (8 November 2026 source reconciliation)

The original C1 product workspace at `D:\\Nayeon\\BYOK_C1_PRODUCT_20261028` contains **17 pre-existing historical modified/untracked paths**. These were inspected read-only; they were **not** imported into this review branch, reset or released.

- `nayeon/brain/pending_credential_policy.py`: frozen `PendingCredentialAssessment` and an explicit advisory decision matrix with `NEEDS_REVIEW`, `NEEDS_DESTRUCTIVE_ACK`, `DENY`, `RECOVERY_BLOCKED`. No decision is a service-issued one-use authorisation or evidence that a Windows user consented. **Reject** any mapping from `NEEDS_REVIEW` to permission to call `PendingServiceState.SaveOrReplace` or `PendingWinCredStore`.
- `nayeon/brain/pending_credential_recovery_document.py`: bounded, untrusted structural `PendingEvidenceRecord` codec and SHA-256 chain. This is **not** a protected LocalSystem journal, HKLM rollback anchor, independent enrolled witness or persistent consumed-approval store. **Reject** reuse of structural hashes as an authenticated recovery authority.
- `nayeon/desktop_alpha/first_run_connection_owner.py`: `TrustedFirstRunConnectionOwner` is a creator-thread local coordinator wrapper in a **fake-first** desktop onboarding flow. Its module documentation explicitly states that the default desktop application does not import/instantiate it, and it never supplies elevated Windows native service identity, protected WinCred custody or trusted UI provenance. Despite the class name, **it is not** `ITrustedPendingApproval`, authenticated IPC or the reviewed local elevated consent ceremony.

**Concrete integration constraint:** Any future native G1 consent issuer must be a separately reviewed Windows service/UI trust composition with signed-origin provenance, explicit human consent and one-use durable service authority. The Python policy and connection UI may only render advisory status *after* an authenticated, privacy-preserving native response exists; no Python callback, local object identity, metadata SHA, client claim or self-named `Trusted` class may mint authorisation.

**Acceptance review:** Prove that neither a fake-first Python `NEEDS_REVIEW` decision nor a replayed `PendingEvidenceRecord` can obtain `READY`, `APPROVED` or a native WinCred attempt, and that the default application remains disconnected from unreviewed native custody. Do this within actual source-specific integrated acceptance tests only after the qualified G1/G2/G3 reviewer has agreed on the trust design. No new synthetic model is needed here.

G0 historical migration/source admission remains independent: these 17 workspace paths cannot simply be copied, force-added or merged into a release branch without review.

## 9. Release disposition and invariants

This P104 branch is **documentation-only**, with no new executable application code, native Windows API execution, IPC service, credentials, keys, source gate toggles, production effect, signer workaround or release. The 11 frozen original native files, three independent denial guards, old P96 finding, historical P85/P62 restrictions and original product worktree must stay intact. Neither author-written tests nor this design document is an independent expert approval.

**P104 DESIGN REVIEW CANDIDATE ONLY. G0–G6 HOLD. BYOK C1 PRODUCTION RELEASE HOLD. NO API KEY REQUIRED.**
