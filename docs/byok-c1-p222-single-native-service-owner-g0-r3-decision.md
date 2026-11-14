# P222 — Native BYOK C1 Single-Owner Service Architecture / G0-R3 Qualified Decision

Nayeon v1 / Mark-LII · 14 November 2026 · OM v2.1

**Status: ARCHITECTURE DECISION REQUESTED, NOT RECEIVED. Engineering design evidence only.**
**All G0–G6 OPEN · R0–R4 REAL-KEY NO-GO · P0–P5 PRODUCTION HOLD.**

## 1. Proven baseline, provenance and do-not-change boundary

- Exact parent: 429694ca64b38a3957fab462d53afeddcdb298d2, P221 draft PR #146, unmerged.
- Genuine P221 Windows run: 43632484551, success. Artifact ID 14128691879, ZIP SHA-256 5ECD5536270DD9BBE8D3A90F03F1A191A2E2ACD6DE20A569002357259D401FAB.
- P221 genuine Windows native: original P96 15/15 x64 + 15/15 x86; P221 test-only 13/13 x64 + 13/13 x86; 33/33 focused Python. The historical P96 defect remains OPEN and actual product 3 full unfiltered regressions remain 0/3.
- Frozen P96 original transaction SHA-256 D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB, tests/p96_native_transaction_negative/PendingCustodyTransaction.cs.
- Frozen original ledger SHA-256 93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B, tests/p95_native_custody_preflight/CustodyLedger.cs.
- Original native_c1_candidate/CustodyService.cs SHA is the Git blob at this parent. It is denial-only, no main executable, no service installation, and OnStart always throws. ServiceOwnedAdmissionBoundary.cs refuses terminal effect and does not own a native key effect.
- P132 interactive-user Python CredWriteW/CredDeleteW remains reachable through local_byok_window.py -> local_byok_user_scope.py -> windows_credential.py; P133 local_byok_launch_bridge.py can start a separately frozen companion if an authorised binary is later issued. No installed Code Integrity proof excludes arbitrary same-user code from calling its *own* credential APIs.
- P220 ZIP review result is not runtime code or store isolation; P221 monitor is a nondeployable fake-only source comparator, not a real native effect actor.
- Original Kristian worktree D:\Nayeon\BYOK_C1_PRODUCT_20261028, branch nayeon-v1, HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, 4 modified + 13 untracked files: DO NOT EDIT, reset, stash, rebase or clean.
- All P222 changes must be isolated, additive, draft/unmerged, no service account, credential, real-key effect, policy edit, signing, secret migration, release or native machine mutation.

## 2. Proposed architecture — concrete decision to be accepted or rejected

Three processes/actors, with **only one** permitted terminal credential-effect owner after all signed approvals:

A. User-facing, separately signed human-consent UI/broker
- Authenticates actual interactive Windows user, session, live consent, operation (SAVE/REPLACE/DELETE), exact pending destination, candidate commitment, expiry, one-use nonce and deletion acknowledgement.
- A claimed bool, UI command-line argument, Python call, model request, PID, source hash, session ID, generic certificate or token provided by a client is NEVER sufficient.
- Broker must be a signed installed image, not an unverified source/frozen companion. Actual loaded-image identity, sender origin, ACL and authentication must be enforced by OS.
- No arbitrary script, plugin, dynamic loader, mutable local helper or user-writable installed directory may enter the elevated trust boundary.

B. Native service identity and authenticated IPC
- Proposed virtual service account NT SERVICE\NayeonByokCustody is a candidate ONLY, not an approved choice, installed user or proven DPAPI identity.
- Choose either a qualified least-privilege distinct service principal with documented profile, stable SID/token, restricted service SID and independent owner ACL, or a documented alternative. LocalSystem is not default; excessive authority must be justified.
- Authentic Windows named-pipe OS client/server, token impersonation, process image / signer, actual session and integrity claims are checked in service context. Prevent same-user forged broker endpoints, pipe squatting, process/image TOCTOU, duplicate operations, stale sessions and arbitrary remote calls.
- SCM service account configuration and service SID ACL are distinct concepts: security owner must approve both, rather than assuming NT SERVICE identity from a service name string.
- The service is NOT implicitly a privileged operator because it passed a CI test.

C. Single native service-owned custody/effect actor
- One sealed service-owned actor contains the only terminal WinCred (or approved protected file store) effect implementation, SAME in-process synchronization for consent consume/revoke/stop/fault and final effect dispatch, the native same-process/thread-owned OS custody mutex, independent durable journal/anchor and single terminal result.
- DO NOT wire the original unmodified P96 PendingCustodyTransaction.Apply to a production native adapter; its final StillCurrent/IsOwned check-to-effect race is confirmed in unchanged Windows negative evidence.
- DO NOT rely on P221's separate wrapper lock for real security. A separate wrapper may be bypassed by another request/effect path. The actual final effect method must be private to the same service-owned actor and the only installed effect actor.
- Fixed, typed, operation-bound pending-only calls. No generic callback or publicly passed effect interface in the final dispatch section. Never return credentials, write directly to active user targets, read active slots or validate providers inside BYOK C1.

## 3. Service-owned irreversible-effect sequence (decision proposal)

The qualified SEC-03/SEC-04 reviewer must approve the following *exact order*, error semantics and failure windows before code integration:

0. Fail-closed service start: immutable binary/signature/policy identity; low-privilege service token and profile; protected target ACL; service-private journal and independent anchor; authenticated IPC, no code in user-writable install tree; G0/SEC owners signed. If any missing, service must refuse/start blocked.
1. Broker issues cryptographically/internally authenticated request (not caller claimed) binding real session, user, operation, pending-only target, candidate, expiry, destructive acknowledgement and nonce.
2. Service verifies named-pipe peer and installed loaded-image identity, matches signed broker and session, and invokes one service-owned state machine. One-use id consumed durably BEFORE effect, with replay/rollback detection.
3. Service obtains service-owned monitor shared with revoke/stop/fault; acquires native process-shared Windows custody mutex on the SAME native execution thread; verifies authentic journal and independent anchor, expected store presence and owner identity. No arbitrary callbacks across critical section.
4. Service durably writes and exact-readback verifies independent IN_FLIGHT evidence and one-use consumption; issues the single *fixed* native pending effect exactly once, still within the service-owned linearisation tenure.
5. Service validates terminal journal/anchor and non-secret stored/absent status. A WinCred success response is NOT an API key validity or irreversible durability guarantee; results remain UNVERIFIED.
6. If effect may have happened but native result, journal, anchor, release, stop or reboot verification is uncertain, sticky RecoveryRequired; NO automatic replay/retry or alternative effect path.
7. Revoke before native dispatch commits under same monitor => zero native effects. If dispatch wins first, subsequent revoke cannot retroactively claim zero effects; must return documented TOO_LATE/RECOVERY outcome. Stop may block during a bounded effect; qualified reviewers must specify watchdog, shutdown deadline, crash isolation and emergency recovery without breaking this safety property.

The actor cannot be considered safe until OS-native fault injection validates all orderings on an approved disposable Windows VM. P221 synthetic 13-case tests only demonstrate a proposed monitor ordering under a fake interface, not OS privileges or durability.

## 4. Exact security decision table — choose; do not infer GO

| Question / ID | Candidate options | Required owner-signed answer |
|---|---|---|
| SEC-03-A | NT SERVICE virtual account; distinct low-privilege local account; other | Exact principal, platform build, SCM config, service SID type and token privileges; **UNISSUED** |
| SEC-03-B | Service-principal WinCred; service-user DPAPI-protected file; other | Actual exclusive service-owned target, user profile, reboot persistence, ACL and cross-principal denial; **UNISSUED** |
| SEC-03-C | Independent monotonic OS-backed history witness and backup/recovery | Physical storage, antirollback, corruption/restore/deletion policy; **UNISSUED** |
| SEC-04-A | Signed Windows installed image, trusted broker and full runtime dependency closure | Publisher, signer trust, image section/file identity, update/rollback, DLL/script/dynamic-code policy; **UNISSUED** |
| SEC-04-B | Authenticated OS named-pipe client/server and interactive consent | User/session/process token provenance, one-use durable consent, replay and terminal transfer; **UNISSUED** |
| SEC-04-C | Single actor effect and P96 fix acceptance | Durable IN_FLIGHT linearisation, stop/revoke/fault interleavings, uncertain effect no retry; **UNISSUED** |
| GOV-01 | Threat model, same-user attacker/admin/kernel scope | Independent security governance acceptance; **UNISSUED** |
| GOV-02 | Legacy P132 key lifecycle / no silent migration | Authorised re-enrolment, retention and explicit delete handling; **UNISSUED** |
| REL-05/06/07 | Security review / independent QA / production owner | All gates, 3 full Windows regressions and deployment/rollback release signoffs; **UNISSUED** |

Explicitly REJECT machine-scope DPAPI by itself as a cross-user secrecy barrier. Microsoft documents that with CRYPTPROTECT_LOCAL_MACHINE other users on the same machine can unprotect accessible ciphertext. User-scope DPAPI assumes correct service identity and loaded user profile and still requires physical access control and threat modelling.

Code Integrity/App Control for Business applies device-wide, not per-user. An approved WDAC/UMCI/signing policy can restrict what executes, but it does NOT itself make interactive-user WinCred unreachable or transform a source tree into a trusted loaded image. Policy must include relevant EXE/DLL/MSI/script/.NET dynamic-code cases and verify enforcement (not merely audit mode) against actual shipped binaries. The host's existing policies cannot be modified to force a pass.

## 5. Reviewer evidence acceptance and falsification

A genuine independent reviewer receipt MUST contain:
- Reviewer name, employing organisation / role, authority and independence attestation.
- Exact commit IDs, build/binary SHA-256, source artifact inventory and trusted source provenance.
- Scoped Windows edition/build, user/session token, service SID/profile, SCM identity, principal store, policy/signing publisher and Windows loaded image graph.
- Explicit signed dated GO or HOLD per SEC-03/SEC-04; tested evidence, unexplained risks, temporary exceptions, expiry and rollback conditions.
- Owner and security decision cannot be supplied by a self-authored JSON field, PR comment, another assistant-generated policy, CI pass or guessed GitHub collaborator.
- SEC-03/SEC-04 signed positive review is prerequisite to disposable **no-secret** VM deployment, which also requires separately authorised Windows administrator and owner. Production remains separately gated after that.

Falsification scenarios the reviewers must attempt:
- Same-user Python direct CredWriteW on original P132 target is NOT proof of new service isolation. Instead test same-user read/write/delete against the NEW service-owned target, and ensure OS DENIAL while original P132 user target is untouched.
- Forged broker signature file, swapped signed DLL, user-writable installation path, alternate runtime loader, user-impersonated pipe server, reused nonce, replayed session, late revoke, process crash before IN_FLIGHT/readback/after native effect, journal-only restore vs stale anchor, revoked/expired signer, service profile absent, failed system upgrade.
- If any single trust input is UNKNOWN, all gate results remain HOLD.

## 6. Operating and release disposition

No named external qualified SEC-03/SEC-04 owner, actual signer or Windows VM installation authority is known from connected PRs. None of GOV-01/02/SEC-03/SEC-04/REL-05/06/07 has signed. Do not bootstrap approval from GitHub CI.

P222 should produce a **qualified-owner decision packet** and source-bound evidence readback; do not build or install a credential-capable service before these answers are real. New implementation without a chosen OS principal/store would falsely suggest readiness. Do not conflate architecture/design completed with C1 implementation done.

Three full unfiltered native Windows product regressions remain 0/3. BYOK C2 not authorised. Real-key NO-GO. Production HOLD. No merge/tag/release. No update of original Google Drive MASTER or dashboard production release status until a real authorised release; the original macro-enabled .xlsm remains authoritative, and new copies are not replacements.

## 7. Next P223 conditional engineering work

If a qualified reviewer responds: verify identity and signoff provenance, reconcile specific SEC-03/SEC-04 decisions against exact source, and implement a wholly separate service-owned native actor under isolated review branch with no real keys and approved disposable VM. Do not modify frozen P96 original or user vault. Run focused tests first then independent security review and 3 full unfiltered product regressions.

If no qualified signer/respondent exists: the **next action is owner assignment**, not another self-approved native synthetic test. Keep BYOK C1 on implementation / production release HOLD. Avoid inventing arbitrary additional checkpoints that masquerade as security signoff.

## Official Windows references consulted

- https://learn.microsoft.com/en-us/windows/win32/services/service-user-accounts
- https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
- https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.protecteddata
- https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/feature-availability
- https://learn.microsoft.com/en-us/windows/security/threat-protection/windows-defender-application-control/select-types-of-rules-to-create
- https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/configure-windows-service-accounts-and-permissions
