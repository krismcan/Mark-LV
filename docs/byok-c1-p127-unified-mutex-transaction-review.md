# BYOK C1 P127 — Unified service-shaped review transaction, OS mutex and synthetic stage ordering

9 November 2026 | OM v2.1 | direct exact P126 parent `012271da8d57e468be5116a10ab6c82bd8b29812`

## Scope: unifies existing proof components but DOES NOT promote them

P109/P110 proved a service-owned **single in-process monitor** with one fake fixed-effect integer, but no interprocess native custody lease. P126 proved **real Windows named interprocess Mutex** acquisition, contention and abandoned-owner recovery in a separate synthetic actor; it did not model P49's staged intent/terminal transaction alongside the effect. P127 combines **the same lock for Revoke/Stop/Fault and fixed fake attempt**, **the same-thread full Windows Mutex tenure**, and **in-memory integer-only intent/attempt/terminal stages** in a NEW compile-gated isolated review source. It does not modify or enable P49/P96, candidate P109/P110 or P126.

`WindowsG2UnifiedReviewTransaction` refuses compilation unless BOTH `C1_REVIEW_ISOLATED_ASSEMBLY` and `C1_SYNTHETIC_TEST` are defined; accepts only `Local\\Nayeon-C1-P127-<32 lower hex>` ephemeral test-named Mutex. No production protected Mutex ACL, service identity, LocalSystem, authentic consent or real WinCred effect. It accepts only exact SAVE, REPLACE or acknowledged DELETE operation shape and offers no user-supplied callback/credential path.

Under ONE private monitor:
1. Strict one-use operation preparation; Revoke/Stop/Fault use the SAME monitor.
2. Acquire genuine Windows named Mutex `WaitOne(0)` on the exact executing thread. On contention or `AbandonedMutexException`, deny with sticky `RecoveryRequired` and **zero intent/effect integers**, correctly releasing abandoned ownership.
3. Stage a fake `SyntheticInFlight` intent as **one integer increment**. This is NOT written to protected storage, file, HKLM or audit witness; the old P49 `CustodyLedger.AppendIntent` and `IProtectedPendingState` are NOT called.
4. Increment exactly one second local integer as a FIXED synthetic effect marker. This does not invoke any native credential API, key, callback or storage.
5. On apparent completion, increment one synthetic terminal marker. On simulated unknown effect or failed terminal, leave intent/effect but NO terminal. **Every attempted outcome is `RecoveryRequired` even when all three integers exist**, because neither G1 consent nor G3 durable proof exists.
6. Release the owned Windows OS Mutex on that same thread. A later revoke cannot retroactively claim that a possible attempt was cancelled. No positive authority, retry or rearm exists.

## Hosted Windows negative and concurrency tests

25 new C# native x64 unprivileged cases: invalid and noncanonical protected-looking Mutex names, no real trust, valid synthetic SAVE/REPLACE/acknowledged DELETE, malformed operations and acknowledgements, mismatched operation, pre-intent fault, unknown fake effect, terminal witness failure, replay/no rearm, pre-revocation/stop/fault zero integers, 12-thread one-effect attempt, post-dispatch revoke too late, external genuine Windows child holding the named mutex, abandoned child ownership on process exit, external process probing busy/free during the attempt, fresh instance of the SAME mutex loses all in-memory 'journal' markers (a **G3 deficiency explicitly reproduced**), three-stage outcome never success, original P49/P112 actual effect exclusions.

The preserved previous **357** focused native cases include real P126 interprocess proof, P125/P124 transferred Windows handle attacks, and original P96 **15 fake-only tests that must still reproduce the frozen legacy revocation-to-effect race**. Target **382 = 25 new + 357 previous** actual named hosted Windows cases. Run only under genuine hosted unprivileged Windows, NEVER unsigned native binary on Kristian. Existing frozen original P49 SHA pins and candidate effect-exclusion gates must remain byte-identical. EXACT P127 source diff scope is 4 added review files.

### Critical G3 negative

The actor does not implement **durable** intent or terminal storage and cannot distinguish a fresh instance after prior possibly attempted fake effect. A new instance starts from `Empty` and has no history. This is a **negative finding**: it proves the need for an independently protected and verified G3 journal+anchor+historical enrollment witness, startup recovery policy and cross-process admission rules. No test output may convert 'synthetic intent' or 'synthetic terminal' into a claim of protected persistence.

## Qualified independent security review packet — unresolved decisions

G0 qualified native Windows independent reviewer MUST evaluate prior P119 20-item threat matrix and P124 transferred-pipe-handle authorship failure. G1 requires approved signed installed consent broker, service-owned signer pin, verified live loaded-image identity, authenticated local IPC and defensible genuine human exact-operation presence with durable one-use permission. G2 requires one **separately security-reviewed production fixed-target native actor** that uses the actual service-owned consent revocation lock and native mutex throughout correct protected intent/real WinCred effect/terminal sequence. G3 requires proved protected file + HKLM anchor/antirollback and independent enrollment/recovery authority, atomic error semantics for crash at every stage. G4 real pending-only WinCred test with explicit separate consent and privileged environment. G5 signed release binaries accepted by Kristian Smart App Control. G6 three full Windows product regressions, external release approvals and Google Drive master workbook FIRST then dashboard reconciliation.

All source is DRAFT/review-only and no qualified independent review has been obtained or simulated. No real key, privileged service, registry/WinCred/journal effect, signed consent UI, Kristian unsigned exe, Smart App Control bypass, P62 blocked rerun, GitHub merge/release or non-release Drive master/dashboard edit.

**P127 production gates G0–G6 remain OPEN. BYOK C1 PRODUCTION RELEASE HOLD.**
