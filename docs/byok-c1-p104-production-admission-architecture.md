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

## 7. Release disposition and invariants

This P104 branch is **documentation-only**, with no new executable application code, native Windows API execution, IPC service, credentials, keys, source gate toggles, production effect, signer workaround or release. The 11 frozen original native files, three independent denial guards, old P96 finding, historical P85/P62 restrictions and original product worktree must stay intact. Neither author-written tests nor this design document is an independent expert approval.

**P104 DESIGN REVIEW CANDIDATE ONLY. G0–G6 HOLD. BYOK C1 PRODUCTION RELEASE HOLD. NO API KEY REQUIRED.**
