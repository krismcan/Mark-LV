# P99 — Full original P49 native custody service compilation and denial-gate proof

**7 November 2026 · Nayeon v1 · OM v2.1 · SECURITY/RELEASE HOLD**

## Purpose

P96 established the actual unmodified P49 C# transaction coordinator's check-to-effect consent-revocation flaw using fake adapters. P97 modelled a corrected single-lock admission design in a separate disabled C# test component. P98 compiled and exercised the original P49 service startup/gate/ACL code separately. **P99 now compiles all ELEVEN original, unmodified P49 native C# service source files together**, including real pending-state composition, actual native WinCred P/Invoke declarations, protected journal/registry-anchor classes, OS mutex and native transaction coordinator, under a deliberately non-service x64 test executable. This is a **source-linkage and deny-gate proof**, not a native integration/release and not a fix of P96's vulnerability.

## Exact source provenance and scope

All eleven `*.cs` source files are copied **byte for byte** from `D:\Nayeon\BYOK_C1_P49_PRIVILEGED_SERVICE_20261029\src` to `tests/p99_original_native_c1_denial/`. Original/copy SHA-256 hashes are pinned in `D:\Nayeon\Support_Evidence\OpenAI_18729810\P99_ORIGINAL_FULL_NATIVE_11_SOURCE_SHA256_20261107.csv` (receipt SHA-256 `3177076C672475646664253BF7FC51C6662F1C404ED2E8427B91F0AD1C1A5DA6`). No original P49 file is edited. No `BYOK_TEST` symbol is defined, no release-guard source, P85 historical source integrity test or P62 historic blocked payload is changed.

The native source inventory is `CustodyJournalFile`, `CustodyLedger`, `CustodyRegistryAnchor`, `CustodyService`, `PendingCustodyTransaction`, `PendingServiceState`, `PendingWinCredStore`, `ProtectedAcl`, `RecoveryReader`, `ServiceCustodyMutex`, `ServiceGate`.

A separately added `FullOriginalNativeDenialTests.cs` chooses the test-only `/main:P99FullOriginalNativeDenialTests` entrypoint, **not `CustodyService.Main`**. Test assembly contains the original native API declarations but cannot act as a Windows service, never calls `ServiceBase.Run`, and neither installs nor starts any SCM service.

## What the authentic-source tests establish

- **Real service startup gate:** `ServiceGate.LiveEligible() == false`; original `CustodyService.OnStart`, invoked *only as a protected method through reflection*, throws `Custody service is unavailable`. A hypothetical all-true test-helper call never changes this real immutable denial.
- **Real protected-state boundary:** `PendingServiceState.ForInstalledService()` throws before constructing any protected journal/anchor/WinCred composition. The original `LegacyEffectEntryDisabled()` returns **true**.
- **Real pending-only WinCred boundary:** `PendingWinCredStore.NativeMutationAdmissionPending()` returns **true**. Calling `SaveOrReplace` or `DeletePending` on a disposable local adapter instance returns `LedgerBlocked` at the **first method guard** before any P/Invoke, native allocations or credential effects. No key-shaped bytes are supplied (a one-byte invalid test marker only).
- **Real legacy state entry refusal:** To exercise the original state method's first guard without invoking its private installed-service constructor, the harness creates an *uninitialised managed object* using `FormatterServices.GetUninitializedObject`, then invokes `SaveOrReplace`/`DeletePending` **only after independently confirming all three denial switches**. Their first guard refuses without accessing any null native dependency. This is a deliberately artificial negative test, not an installation/recovery proof.
- **Old coordinator is present but intentionally NOT invoked.** Its P61 consent-to-effect gap remains confirmed OPEN by P96. No caller-generated approval is accepted by production and no key/provider operations occur in this test.
- The target `PendingWinCredStore.FixedTarget` remains a non-caller-modifiable pending-only constant. This code review does not verify whether LocalSystem vault persistence works; real provider validation belongs to C2.

Tests compile/runs using genuine native Windows .NET Framework x64 C# on Kristian; GitHub CI runs the same source hash checks and tests on independent Windows x64 runners (Python3.12/3.14 jobs), alongside P96 original negative comparator, P97 disabled correction and affected existing Python tests.

## Policy and release holds

**Do not attempt P99 x86 runtime tests**: P97's x86 executable was refused by Kristian's Windows Code Integrity enterprise signing policy, genuine event IDs 3077/3033. This is distinct from the historic OpenAI Support P62 platform refusal. No policy/guard bypass, unsigned x86 repackaging, elevated alternate execution or new key handling is permitted.

All copies remain **test-only and uninstalled**; they are not approved as a deployable privileged service. Native credential operations are guarded on real original source, but those literal guards do not constitute a reviewed, trustworthy admission implementation. Independent Windows service/WinCred/ACL/IPC security review is mandatory before any real credentials, installer, protected persistent journal/anchor, authenticated elevated consent or service-side effect. The P61 MEDIUM consent-to-effect defect, P61 HIGH consent origin/IPC, x86 enterprise signing hold and three complete product regressions remain blockers.

**P99 is a full-original-source compile and fail-closed interface verification candidate. BYOK C1 remains on production HOLD.**
