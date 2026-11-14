# P221 — Original P96 Native Coordinator: Review-Only Revoke / Terminal-Effect Linearisation

Nayeon v1 / Mark-LII · BYOK C1 · 14 November 2026 · OM v2.1

**STATUS: ISOLATED ORIGINAL-SOURCE WINDOWS REVIEW EXPERIMENT; NOT A DEPLOYABLE P96 FIX.**
**G0–G6 OPEN · R0–R4 REAL-KEY NO-GO · P0–P5 PRODUCTION HOLD.**

## 1. Proven baseline and source custody

- P220 exact parent: af9e593a8dc460d1ee651f373f05cd4cbd622ad6. P220 draft PR #145, open and unmerged on P221 intake.
- P220 genuine Windows run 43624295624, success. Artifact 14125746262, ZIP SHA-256 FE1FE8744D819C94041E991F55828EDB44A706B5E33A10C488A46FA94202BC79. P220 15/15 actual ZIP source tests and 18/18 original P216 tests pass, no full product suite.
- P219 original P96 genuine Windows x64/x86 negative from unchanged original source: 15/15 per architecture, security flaw reproduced (not fixed). Original Windows run 43621333751, artifact 14124112661, archive SHA-256 51328FB8D54BAB1FB4D5D4E0792AC4C954CC4837B28AB0B7DCFD6DA5D64FE0EA.
- **Frozen P96 coordinator SHA-256:** D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB. Exact file tests/p96_native_transaction_negative/PendingCustodyTransaction.cs.
- **Frozen ledger SHA-256:** 93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B. Exact file tests/p95_native_custody_preflight/CustodyLedger.cs.
- Original P96 fake harness tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs, original native_c1_candidate/CustodyService.cs and ServiceOwnedAdmissionBoundary.cs remain entirely unchanged.
- P221 strictly additive paths: native_c1_g2_review/P221OriginalP96ReviewLinearizer.cs, tests/p221_native_original_p96_linearization/P221OriginalP96LinearizerTests.cs, this document, and a Windows-hosted evidence workflow. No signed installer, user UI, service account, protected store or real source mutation.

## 2. Original vulnerability and limitation of this experiment

Original PendingCustodyTransaction.Apply calls ITrustedPendingApproval.StillCurrent and then IContinuousCustodyLease.IsOwned before calling the IProtectedPendingState fake SaveOrReplace/DeletePending interface. Those are separate observations and are not serialized with the approval owner’s revoke transition. The unmodified P96 negative driver injects a completed separate-thread revocation between final approval and fake effect for Save/Replace/Delete: the old coordinator proceeds to a fake effect after revoke. **That original security design flaw remains OPEN.**

P221's new P221OriginalP96ReviewLinearizer is **not a replacement for PendingCustodyTransaction and not a production service**. It is a non-deployable, compile-guarded C# experimental wrapper that composes the actual original P96 coordinator and original P96 in-memory fake fixtures:
- Two compilation defines (C1_REVIEW_ISOLATED_ASSEMBLY and C1_SYNTHETIC_TEST) are required to build. A production/no-flags compilation must fail via explicit #error.
- The only operation is a fixed test-only fake SAVE with P96Fixture.Dummy: four deterministic non-secret bytes; not a caller-supplied credential, target, delegate or effect capability.
- One C# private monitor (gate) protects wrapper-attempt consumption and wrapper-owned Revoke/Stop/Fault through the complete old fake-only Apply call. Revoke before Apply enters its monitor yields zero fake effects; if Apply obtained the gate first, Revoke cannot **commit** before the old fake effect finishes. A revocation attempt waiting for the gate is not represented as already committed.
- An optional ManualResetEvent test hook can pause while the monitor is held. The concurrent revoker uses a separate Windows thread and cannot mark revoke committed until the test releases fake Apply.
- The original old Apply's StoredUnverified result is always downrated by this review wrapper to RecoveryRequired; any attempted work latches recovery, no automatic retry. This is not actual durable recovery or a valid key result.
- Real WinCred, Windows user DPAPI, service identity, trusted UI session, signed installed broker, native IPC, OS custody mutex, protected journal/anchor and restart/recovery **are absent**. The wrapper accepts only fake test fixtures; it cannot be linked to a credential port.
- **Critical limitation:** this proof assumes all revoke/stop/fault paths go through the wrapper's monitor. Any alternate original approval owner, direct native effect adapter or separately accessible Python WinCred path bypasses it. It is *not* the actual native_c1_candidate/CustodyService admission monitor and cannot satisfy G0/R3 or P96 production remediation.

The main security value: a source-linked positive experimental ordering comparator can now run alongside the unchanged P96 negative proof. This gives a concrete acceptance shape for future actual service-owned actor design, without pretending an integer-only fake passes security review.

## 3. Genuine Windows test plan

On a disposable GitHub-hosted Windows runner only (never Kristian):
1. Verify exact P220 ancestor commit and exactly four additive P221 paths. Verify original service, P96, P95, P132/P133 source and P220 package tests are untouched.
2. Disable automatic CRLF materialisation *within the hosted checkout only* to compare original true Git blob SHA-256 of P96 coordinator/ledger. Capture protected source SHA-256 before/after.
3. Compile original unchanged P96 negative proof on native Windows .NET Framework x64 and x86, each 15 original cases proving fake effects after revoke. Preserve actual compilers and exe native process exit 0, raw logs and hashes. **Do not interpret this test success as remediation.**
4. Attempt to compile the P221 linearizer with the two safety flags absent; require nonzero compiler exit and the actual explicit #error text. This is a test of *test-only* build exclusion, not a Windows Code Integrity policy test.
5. Compile the P221 wrapper/tests with both synthetic/review flags plus the byte-identical original P96 source, ledger and original fake harness. Run 13 native cases x64 and x86. Positive ordering cases include revoke-first/stop-first/fault-first with zero effects; one-use, no retry; fake effect-uncertain and journal-fault recovery; and three separate Windows-thread attempts to revoke/stop/fault mid-gate.
6. Run original 18 P216 source-path security negatives. All windows native process statuses, no-key status, source SHA-256 and original failure logs are archived. Source changes in any frozen file cause failure.

**Success means only** the above native review cases passed with the original sources. It does NOT mean actual service-side gate, credential store, signed loaded image, owner-dependent DPAPI, nonce-bound user consent, durable IN_FLIGHT, rollback witness, actual native adapter or P96 real effect security has been implemented.

## 4. Required real P96 production successor (no approval yet)

Actual native service implementation must have one service-owned terminal mutation critical section across actual **trusted consent consumption**, **Revoke/Stop/Fault publication**, durable verified **IN_FLIGHT**, and its **single exact native pending effect**. The old coordinator’s caller-provided ITrustedPendingApproval and separately owned effect adapter are insufficient. The new contract must define a linearisation point (if revoke commits before effect, effect count zero; after effect begins, state is uncertain/recovery-required until durable terminal verification), fixed effects with no arbitrary callback under lock, process-owned true Windows custody mutex, authentication of user/session and loaded signed broker image, restricted service identity/store, no alternate actor, source manifest and OS Code Integrity. A long-held monitor during a blocking effect may delay Stop and requires a qualified design for timeouts, watchdog, crash, reboot, and durable recovery. The actual runtime must not allow another principal to set/recover/retry the same target.

Original P132/P133 interactive-user route remains reachable in the repository. A signed high-assurance installer must exclude that legacy effect implementation, and actual OS principal/ACL access tests must prove the new store is isolated from original same-user code. No automatic migration, read, delete or re-enrolment of existing user WinCred targets.

## 5. Qualified independent authority still absent

GOV-01 independent threat governance, GOV-02 legacy/key lifecycle, SEC-03 Windows service principal/DPAPI/WinCred/protected store, SEC-04 Windows Code Integrity/signing/IPC/consent and race remediation, REL-05 release security, REL-06 full Windows independent QA, REL-07 production owner: **0/7 actually signed source-bound decisions**. No named qualified reviewer in PR #145 or approved signer, test VM, service installer or production release. An assistant-authored threat model, synthetic proof and GitHub-hosted Windows success are not independent approval.

**Next P222:** integrate written independent SEC-03/SEC-04 decisions into an actual source-bound native CustodyService successor plan; only after approval conduct a controlled *separately owned disposable Windows VM* synthetic principal/store trial. If independent authority remains missing, carry explicit G0/R3 HOLD and continue only nonprivileged source-design/provenance work. Do not install a service or touch keys on Kristian.

**G0–G6 OPEN · R0–R4 NO-GO · P0–P5 HOLD · external approvals 0/7 · full unfiltered whole-product Windows regressions 0/3 · BYOK C2 NOT AUTHORISED.**

Kristian's original local HEAD e3612279cb972e68e2487702183d5bf5b8f6c4a1, branch nayeon-v1, four modified and thirteen untracked paths must remain undisturbed. Original Google Drive MASTER macro-enabled .xlsm remains authoritative; no release, so do not increment production or create a replacement workbook/dashboard.
