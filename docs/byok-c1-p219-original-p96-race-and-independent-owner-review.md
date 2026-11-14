# P219 — Qualified Windows G0/R3 Owner Response Intake & Source-Specific P96 Native Effect-Retirement Proof

Nayeon v1 / Mark-LII · BYOK C1 · OM v2.1 · 14 November 2026

**Engineering packet only. Independent Windows G0/R3 decision: NOT RECEIVED. G0–G6 OPEN · R0–R4 REAL-KEY NO-GO · P0–P5 PRODUCTION HOLD.**

## Exact source and evidence lineage

- Repository: krismcan/Mark-LV.
- **P219 parent (must be exact):** f16f5c2cd5ce6c6f58ace2bad053a7e98f59da1c (P218 draft PR #143).
- P218 genuine Windows run: 43619829199. Artifact 14122999208, archive SHA-256 A06F6853FC7CD9BD72EE42659432402BD0E0A703D4606EC77274425CF6C2FB86. Focused P216 source cases 18/18 passed, Windows preflight exit 0.
- P216 selected security tests: 267/267 (historical; not a complete product regression).
- P219 is strictly **two additive files**: this source-bound review packet and a new isolated Windows workflow. It must not edit any P96/P132/P133/P216–P218 source, native C1 host, original runtime or review-only security controls.
- Original Kristian authoritative worktree: D:\Nayeon\BYOK_C1_PRODUCT_20261028; branch nayeon-v1; HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1; 4 modified and 13 untracked entries preserved. Read-only use only.

## Precisely known P96 source-to-effect bug: not a service deployment

Historical original native source: tests/p96_native_transaction_negative/PendingCustodyTransaction.cs (byte SHA-256 D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB). It is the byte-unchanged original disabled P49 coordinator, copied to the original P96 negative proof. Actual adjacent ledger tests/p95_native_custody_preflight/CustodyLedger.cs has original SHA-256 93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B.

The real old method is PendingCustodyTransaction.Apply:
1. Consumes approval, acquires IContinuousCustodyLease, observes journal/anchor, validates expected state.
2. Calls ApprovalCurrent (ITrustedPendingApproval.StillCurrent) and then lease.IsOwned as separate probes while constructing/persisting IN_FLIGHT intent.
3. After final approval probe and custody check, calls IProtectedPendingState.DeletePending or SaveOrReplace without one common service-owned critical section serializing approval revocation/fault and the **final terminal effect**.
4. P96 negative harness NativeTransactionRaceProof.cs injects consent revocation from a *different thread* during the fourth lease.IsOwned getter after the last StillCurrent check, before fake effect. Save/Replace/Delete each show the fake effect was invoked after revocation. A passing P96 native test **reproduces a flaw**, not remediation.
5. Actual old production CredWrite/CredDelete, service registration, trusted consent, connected IPC and protected target are separately held/absent. Never claim an actual Windows credential operation occurred from this fake test.

Current review native host:
- native_c1_candidate/CustodyService.cs has no Main/ServiceBase.Run, OnStart throws and RefuseUnreviewedTerminalEffect delegates only to ServiceOwnedAdmissionBoundary.
- native_c1_candidate/ServiceOwnedAdmissionBoundary.cs serializes refusal with revoke/stop/fault; it has no real native credential effect.
- native_c1_candidate/CandidateCredentialEffectHold.cs keeps original legacy and native effect gates true.
- native_c1_candidate/P208SyntheticTerminalOwner.cs and native_c1_g2_review/WindowsG2UnifiedReviewTransaction.cs demonstrate synthetic integer-only serialized effects but are **not** a deployed trusted effect owner, identity, grant, signer, service store or antirollback.
- P132 interactive Python local_byok_window.py → local_byok_user_scope.py LocalByokController.approve → windows_credential.py WindowsCredentialBackend.put/delete → native CredWriteW/CredDeleteW remains reachable independently of the native denial-only service; P133 local_byok_launch_bridge.py can launch a separate same-user child. The old user vault is **not** service-owned.

### Specific production successor acceptance before any effect-capable implementation

A qualified Windows security/platform owner must bind the successor to exact source commit, installed and signed binary set, authentic least-privilege service token, restricted service SID, DPAPI profile availability, protected ACL/target and a policy-approved Code Integrity identity. It must **not** reuse the original P96 Apply as the real effect dispatch or treat a source flag as OS isolation.

The next approved native source work must connect the **actual** CustodyService ownership and admission to a separately signed native service effect actor; no new detached fake effect gate. Acceptance will require:
- Trusted interactive consent issuer and authenticated installed broker with exact user/session/logon, live loaded-image/WinTrust identity and authenticated named-pipe client/server peer binding.
- Exact one-use operation, target, candidate and immutable consent/version binding; durable consume before effect, no replay.
- A service-private shared lock/linearization point across consent revoke/stop/fault, journal in-flight proof and final native single effect dispatch, with actual original P96 regression proving **zero effects if revoke wins** and terminal uncertain/no retry if effect wins and completion is ambiguous.
- Exact native process-owned OS custody mutex tenure, protected service-only storage and independent monotonic rollback anchor, OS restart/profile and disaster recovery tests.
- A separate high-assurance installer that excludes all direct Python WinCred effects, source interpreters and P133 launches; actual cross-principal negative attempts must prove new service target cannot be reached by original-user code.
- Protected signed installation / entire executable and DLL load graph, Code Integrity policy owner approval, tested update and rollback path; never relax an existing Kristian CI/WDAC/SAC block to pass.
- Never automatically migrate, decrypt, impersonate, copy, delete or export old P132 current-user credentials. Only future explicit re-enrolment under separately approved R0–R4.

## Qualified independent decision intake (genuinely missing)

| Gate | Required *real* approving function | Exact requested verdict and scope | Status |
|---|---|---|---|
| GOV-01 | Independent security governance | Signed G0 threat model and adversary boundary | UNISSUED |
| GOV-02 | Credential lifecycle owner | Separate target, re-enrolment, backup, restore, delete | UNISSUED |
| SEC-03 | Windows service identity and protected store authority | Actual virtual account/LocalSystem selection, SID/token/profile, user DPAPI/WinCred/native store and cross-user denial plan | UNISSUED |
| SEC-04 | Windows Code Integrity, signing, broker and IPC security authority | Exact policy, installer/signature/loaded binary authority, authenticated pipe/consent and P96 fix acceptance | UNISSUED |
| REL-05 | Independent release security assessor | G0–G6 and R0–R4 positive source-bound security audit after implementation | UNISSUED |
| REL-06 | Independent Windows QA | Three unfiltered full-product Windows regressions with exits and logs | UNISSUED |
| REL-07 | Authorised production/deployment owner | P0–P5 merge/install/tag/release authorisation | UNISSUED |

No reviewer can be nominated merely from a GitHub username or an assistant-written review. The connected PR #143 had no requested reviewer or submitted qualified independent approval at P219 intake. A real approval requires verified independent organisation/role, explicit authority, scoped source and binary hashes, OS and policy build, threat model, alternatives and residual risks, signed dated **GO or HOLD**, plus independent security evidence. Github CI pass alone means only the scoped tests passed. **Genuine external approval is an explicit blocker.**

## Exact P219 real Windows negative evidence plan

On an isolated Windows GitHub runner only, with no credential access or privileged service registration:
- Validate the exact parent and that P219 changed precisely this document and the new workflow.
- Hash original native P96 coordinator and ledger; refuse any drift from the two historical SHA-256 pins.
- Confirm NativeTransactionRaceProof.cs is unchanged against P218 and references no WinCred/PInvoke/registry/test adapter that could touch real keys.
- Compile original native C# coordinator + ledger + fake-only negative harness under both x64 and x86 .NET Framework compilers, no service executable, no privileged installer, no connected IPC, no API keys.
- Execute each architecture's exact 15-case negative harness, preserve raw original OS compiler/process exit codes and logs. Require markers P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=15, P96_NATIVE_ACTUAL_COORDINATOR_TESTS_FAILED=0, P96_LEGACY_POST_CHECK_REVOCATION_RACE=REPRODUCED_IN_FAKE_ONLY, P96_REAL_NATIVE_EFFECTS=NONE, P96_C1_PRODUCTION_RELEASE=HOLD.
- Record actual P216 original 18 focused source cases as a separate regression, and SHA-256 all original logs/binaries/hash-pinned source, preserve failed runs.
- Affirm this native negative evidence DOES NOT mean the bug is fixed; no real service effect/DPAPI profile/Code Integrity policy can be granted by it.

## Decisions before any controlled test VM

The separate disposable/no-secret service-account trial is not yet authorised. Required first: named SEC-03/SEC-04 security and Windows signing/policy owner, signed source-specific test scope, selected Windows edition/build, dedicated snapshotted owner-approved VM (NOT Kristian), precise installed signer and service token/store choice, backup/recovery, test-only fake data and documented stop/revert procedure. The seven reviews are still absent; therefore no privileged account creation, service installation, WinCred read/write/delete, real API key, signing policy change, user credential migration, provider probe, release merge or production tag. The previous OpenAI Support case is unrelated to signing/Windows security authorisation.

## Next P220 engineering action

**External owner decision intake plus precise native CustodyService source-change plan for P96 closure.** If SEC-03/SEC-04 remain unavailable, continue only safe unprivileged source-linked analysis, original native negative regressions and qualified reviewer referral; do not interpret additional tests as substitutes for trust-root approval.

**G0–G6 OPEN · R0–R4 NO-GO · P0–P5 HOLD · seven independent decisions 0/7 · complete unfiltered Windows product regressions 0/3 · BYOK C2 not authorised.**
