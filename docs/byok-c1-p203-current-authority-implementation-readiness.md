# BYOK C1 — P203 Current Production Authority Map and Implementation Readiness Contract

**14 November 2026 | OM v2.1 | H/C/R: HOLD / isolated source-specific readiness engineering / HOLD**

## Evidence-backed canonical parent

P202 final exact commit fb6814fad38fb021576ee3aa7ee01558ea4f3cb5; P202 draft PR #127 remains open/unmerged. Final authentic native Windows Actions run 43583091821 on this exact commit, original artifact 14108109712. ZIP SHA-256 49C9B967377948C36F05ACBF916EB77142AA3A7BECA18F6B81140621F312CA51. Raw p202_real_Windows_fixed_owner_original_B_8.log SHA FB2C1AADC286AD0748AAA93CF8A05DA064528F37E9183F98A7BC59B14632C405 and p202_fixed_owner_Phase10_boundary_HCR_ledger.json SHA C78EC56DDF029DC4EF9C82719B82C71FDBDEFD744E34D2BC0F9F95CA8147E1D0. Two entries with valid CRC, 8/8 selected real native Windows tests and original OS exit 0, source_before==source_after, H/R HOLD, actual full-product Windows regressions accepted 0/3.

## Authority graph — authoritative *public* source route

The active public BYOK source-admission route in current reviewed source files is:

1. tests/phase8_byok_b_scope_migration.py: PUBLIC assert_byok_b_integrity -> tests.phase10_perception_scope_migration.assert_phase10_integrity. The sealed original-B legacy implementation is kept privately as _assert_byok_b_historical and is NOT the current public authority.
2. tests/phase10_perception_scope_migration.py: PUBLIC assert_phase10_integrity -> tests.phase10_2_privacy_scope_migration.assert_phase10_2_privacy_integrity. The complete Phase 10.1 historical assertion is private.
3. tests/phase10_2_privacy_scope_migration.py: PUBLIC assert_phase10_2_privacy_integrity -> tests.phase10_3_scope_migration.assert_phase10_3_integrity; historical Phase 10.2 guard is private.
4. tests/phase10_3_scope_migration.py: PUBLIC assert_phase10_3_integrity -> tests.phase8_byok_c1_p76_scope.assert_p76_offline_integrity. Historical sealed Phase 10.3 guard is private.
5. tests/phase8_byok_c1_p76_scope.py: terminal branch-bound original **offline C1 prototype**. It admits only its exact sealed source parent/branch context, not a mutable P203 audit PR branch; it is NOT privileged service/effect authority. Do not treat a P76 gate success as provider key admission or production deployment permission.

**Current native trusted-effects direction** is independent of that Python public source route: native_c1_candidate/ServiceOwnedAdmissionBoundary.cs and native_c1_candidate/CustodyService.cs are **denial-only, nondeployable candidates**. Explicit RefuseRequest/RefuseBoundRequest functions have no trusted UI consent issuer or native credential effect dispatch. P104 identifies original P49 legacy security issues and explicit G1-G6 architecture decisions. An attacker can impersonate Python script output even if the interpreter Authenticode signature is Valid (P199/P200 unsafe controls).

**P201/P202 remediation candidates**: nayeon/brain/byok_b_ntfs_physical_admission_candidate.py and nayeon/brain/byok_b_fixed_owner_bridge_candidate.py are dormant. They block historical B named ADS in a genuine historical Git fixture, but are NOT connected to the live Phase 10/P76 public route, are NOT atomic across 23 source files, and are NOT signed executable/IPC trust boundaries. Historical original private full B ADS vulnerability remains unpatched.

## Readiness categories — never conflate design with actual effect admission

| Stage | Current verdict | What is authorised |
|---|---|---|
| Read-only source exploration, threat model, isolated draft branches | READY | Nonprivileged bounded static and synthetic work, source-pinned Windows tests and evidence |
| Develop denial-only G0 integration seam in isolated branch | READY FOR CANDIDATE ENGINEERING | Must preserve original source and frozen tests; no merge/activation |
| Production architecture **design acceptance** | **NOT READY** | Requires qualified independent reviewer for exact OS signing, IPC, source trust, rollout, durability and all G0–G6 |
| Live source admission including current Phase 10/P76 and original B ADS remediation | **NOT READY** | Must bind correct modern authority; demonstrate coherent source/volume/race-safe custody without historic fallback |
| Native Windows Credential Manager Save/Replace/Delete with real key | **NOT READY / PROHIBITED** | Only after signed installed trusted consent/effect host, independent consent owner, durable nonreplay protection and security GO |
| BYOK C1 release | **PRODUCTION HOLD** | Three full unfiltered native Windows product regressions, security GO, no unwaived original failures, coordinated release evidence |
| BYOK C2 real provider validation | SEPARATE FUTURE GATE | New explicit consent and API key entered only in secure local trusted UI |

## Dependency-ordered concrete implementation work, without repeated routine approvals

**C1-IMP-01 (G0, independent source owner):** choose the exact current Phase 10/P76 source and release manifest for the *new production candidate*, not the original legacy sealed B branch. Define immutable source root/ancestor/leaf FileId, ADS/hardlink/reparse/journal/volume checks as a source-set transaction rather than P201 sequential snapshots. Treat the signed loader, signer/rollback root and USN metadata as separately scoped trust authorities. No old gate downgrade. Add in isolated source; test genuine current Windows product context.

**C1-IMP-02 (G1, service and trusted UI origin):** qualified Windows security reviewer to choose independent signer/trust anchor, approved signed UI and service binaries, signed load path, endpoint SDDL, token/impersonation, elevation/interactive consent ceremony, anti-spoof exact sender process *and executable content* identity. A same-user SID, PID, a signed interpreter, a caller SHA or nonce alone is insufficient. Until qualified review, only denial-only code may be written.

**C1-IMP-03 (G2, one terminal actor):** nondeployable successor C# service-owned terminal actor; privately held candidate bytes/operation, one-use approval consumption, serial revocation/fault/stop, same-thread custody mutex and one native effect capability. Preserve P49 original denial, P96 race negative; no old PendingCustodyTransaction.Apply or public effect callback. At this stage use synthetic test-only adapter without WinCred mutations.

**C1-IMP-04 (G3, durability):** independently protected enrollment/rollback witness, journal+HKLM anchor consistency, one-use consumed record durable before native dispatch, crash/timeout/partial write and restart matrix, sticky recovery and **never automatic effect retry**. Do not turn old faulted startup state or legacy disable flags off to simulate success.

**C1-IMP-05 (G4/G5, signing and actual Windows host):** review approved installer, main/helper/service signature and Code Integrity/WDAC/SAC policy including device x86 host. No bypass of Kristian machine execution restrictions; use an administrator-approved signing/install policy.

**C1-IMP-06 (G6, product acceptance):** unwaived P135, P175, P178, P179 and PERF-P187-01 failures/timeouts repaired with real native execution, all historical P195–P202 unsafe negatives retained, three **complete, unfiltered** accepted Windows product regressions (currently 0/3), and qualified independent GOV-01, GOV-02, SEC-03, SEC-04, REL-05, REL-06, REL-07 decisions all documented with exact source SHA and disposition.

**Only after all required G0–G6 GO:** controlled consent/key entry locally into the secure Windows trusted UI, no API keys through chat, and any actual release: update/readback existing same-ID Google Drive MASTER workbook **before** dashboard. No release reporting or file reconciliation during isolated tests.

## P203 deterministic native Windows audit and source custody

On actual windows-2025 runner, authenticate original P202 artifact ZIP, exact original log/ledger hashes and source/H/R; compare exact P202 parent to P203 Git HEAD, only 3 new audit paths and no modifications to existing tests, nayeon or native_c1_candidate. Static AST analysis verifies **all 4 current public route edges**, the private historical B boundary and P76 terminal offline gate; real nonprivileged source invocation on the unrelated P203 audit branch must **REFUSE**, with no fallback. Native C# candidate source denies effect admission. These tests intentionally do NOT count as full-product Windows regressions, independent security review or a production release GO.

**H/C/R remains HOLD / truthful implementation readiness and current authority mapping / HOLD.** No real keys, Credential Manager writes, privileged host install, live provider calls, trusted signer enrollment, PR merge/tag/release, or production Drive/dashboard update. This document is an engineering decision matrix, NOT qualified independent review.
