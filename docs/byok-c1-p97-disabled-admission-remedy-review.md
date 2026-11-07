# P97 — Disabled Native Admission Ordering Remedy: Security Review Candidate

**Date:** 7 November 2026 | **Release disposition:** DRAFT / NO CREDENTIAL EFFECT / C1 PRODUCTION HOLD.

## 1. Exactly what P97 changes

A **new, test-only, disabled C# coordinator** `tests/p97_disabled_admission_remedy/DisabledNativeAdmissionCoordinator.cs` with disposable Windows multithreaded test harness `DisabledAdmissionRaceTests.cs`. It is NOT wired into the real P49 service, WinCred adapter, IPC, key-entry UI, provider, assistant product, or production release. No real credential or key value is ever read, written, replaced or deleted.

P97 uses the existing authentic P95 custody-ledger C# codec to build a nonsecret **in-memory** journal/anchor fixture. This is NOT a durable file, protected Windows anchor, authenticated observation, release-admission service, or authoritative credential custody. All caller-supplied fake identities are synthetic fixed-format session/candidate labels. There is no protected service OS identity, elevated approval source or native mutex implementation.

## 2. What was demonstrated and what was not

P96 reproduced the **unmodified original P49 `PendingCustodyTransaction.Apply` check-to-effect consent race** in real compiled C# by revoking fake consent between the final `StillCurrent` and fake `SaveOrReplace` / `DeletePending` interface call. For SAVE, REPLACE and DELETE the original still calls the fake effect after a committed revocation. P96 remains an **OPEN security finding** and the original native source is unchanged.

The separate new P97 model uses **one non-reentrant service-model-owned monitor** to serialise fake consent revocation and fault publication against the exact one-at-most **fake** dispatch marker. In the new model:
- Revocation/fault committed under that monitor **before** dispatch => zero possible attempts and recovery-only state.
- Dispatch entering that monitor first => one possible effect marker; a concurrent revocation/fault waits to commit until after the fake dispatch leaves its critical section. It cannot claim cancellation of an already possible effect.
- All three fake operations, SAVE/REPLACE/DELETE, respect these rules.
- Immutable service-model-owned copies of synthetic operation/session/candidate IDs, creator-thread enforcement for fake user/dispatch actions, duplicate approval/refusal and reentry guards prevent test fixture cross-binding.
- Actual C# `CustodyLedger` is exercised for fake `IN_FLIGHT` construction and exact readback. Any corrupt fake anchor or unexpected ledger exception latches fake recovery-only. Even a fake successful terminal stays `ClosedUnverified`; `CredentialVerified`, `NativeEffectPermitted`, `ProductionEligible`, `RetryAllowed` are **always false**.
- A failed fake result, fault, restart after fake intent/dispatch and failed terminal readback never silently rearm.
- No arbitrary effect delegate/callback is injected or invoked inside the admission lock. The only in-lock effect is an integer increment, and the optional `ManualResetEventSlim` barriers are **strictly disposable test hooks**.

**Limit:** This fixes ordering within the disabled in-process model only, not within the actual service. The real P61 MEDIUM security defect remains OPEN until the production coordinator and authorized WinCred effect are separately reviewed and implemented with the same guarantees. The P61 HIGH consent provenance/IPC issue is also OPEN.

## 3. Real Windows development evidence on Kristian

- Windows .NET Framework C# x64 built with compiler native exit 0 and **zero warnings**. Final new model 40/40 native x64 tests PASS, exit 0. Fifteen further complete x64 runs: **600 passing case executions**, zero failed runs (40 distinct tests).
- Windows .NET Framework C# x86 compiler created the executable with zero diagnostics. **Its execution was refused by Kristian's Windows Application Control policy**, so no x86 PASS is claimed. Genuine Windows Code Integrity `Microsoft-Windows-CodeIntegrity/Operational` events **3077 and 3033** at 2026-11-07 14:16:31 identify the exact P97 x86 test binary and enterprise signing requirements. Exact policy identifier: `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`. Read-only evidence at `D:\Nayeon\Support_Evidence\OpenAI_18729810\P97_WINDOWS_CODE_INTEGRITY_X86_BLOCK_20261107.md`. **NO retry, alternate execution path, policy change, rename, wrapping or third-party workaround was attempted.** The x86 test requires a properly approved signed/managed testing route; it is **BLOCKED / UNVERIFIED**.
- Existing affected P93/P91/P88/P87/P86/P84/Connection Python suite: **210/210 PASS** Python3.12 and Python3.14 native Windows exit 0, no skips. An initial Python invocation with `$ErrorActionPreference='Stop'` was interrupted by Windows PowerShell treating unittest's normal stderr summary as a terminating `NativeCommandError`; that invocation produced no usable test result and was rerun normally. Final authentic exit 0, 210/210 PASS for each version. Do not conflate PowerShell stream decoration with a test failure.

## 4. Intentional CI restriction

P97 GitHub CI validates the original P96 race negative proof and P97 corrective **fake-only x64** evidence, plus Python3.12/3.14 affected suites. It does **not** attempt the local blocked x86 executable or claim x86 verification. External GitHub runners do not grant permission to bypass Kristian's App Control enterprise signing policy.

## 5. Remaining mandatory admission/release gates

- Independent qualified native Windows security reviewer must approve P80/P85 historic source, P94 architecture and real service-owned native consent-to-effect logic. The authors' tests and GitHub-hosted CI do not constitute independent security review.
- Trusted elevated local UI, authenticated peer and one-use operation/candidate/session/expiry consent, protection from malicious same-user clients and explicit revocation ownership are not implemented.
- Service-owned non-reentrant native dispatch with protected mutex ordering, durable authenticated `IN_FLIGHT` journal + trusted HKLM anchor, sticky recovery fault and exactly one pending-only WinCred mutation are not implemented. No real keys until an independently approved secure local entry mechanism.
- Windows Code Integrity x86 execution hold requires authorized enterprise-signing/test route, **not a bypass**.
- Three complete native Windows product regressions, independent security GO, release source sealing and readback remain outstanding. Then update the original same-ID Google Drive master workbook first, followed by dashboard.

**Keep literal `ServiceGate.LiveEligible()` release proofs false, `PendingServiceState.LegacyEffectEntryDisabled()` true, `PendingWinCredStore.NativeMutationAdmissionPending()` true, the P85 historical exact-source guard and original P62 OpenAI platform restriction unchanged.**

**P97 expected status:** test-only corrected lock specification verified on x64, x86 explicitly blocked, production C1 security finding OPEN / RELEASE HOLD.
