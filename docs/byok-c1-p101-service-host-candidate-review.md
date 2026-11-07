# P101 — Disabled native-service host admission wiring candidate (C1 HOLD)

**Date:** 7 November 2026 | **Programme:** Nayeon v1 BYOK C1 | **Operating model:** OM v2.1

## 1. Source identity and distinction from P97–P100

P99 linked **all 11 exact original disabled P49 C# native service files** and verified their three independent release/effect denial switches. P100 formalised the seven independent external security-review gates; no independent reviewer has signed off. P101 introduces a **direct C# Windows-service-host composition candidate** using the actual P49 type dependencies. It is **not** another standalone replacement for the real transaction coordinator, and it must never be released or installed.

This PR adds `native_c1_candidate/CustodyService.cs`, a **separately modified review copy** of the actual original P49 `CustodyService` host. The P99 copy of the genuine original `CustodyService.cs` and all other original P49 source copies remain immutable, with exact SHA-256 pins. The candidate substitutes **only the host type** when compiling a test assembly with the **other 10 original unmodified native C# source units**.

The candidate host includes a private `ServiceOwnedAdmissionBoundary` object and exposes a review-only metadata (operation, candidate length, delete acknowledgment) method `RefusePendingOperation`; no credential bytes can be passed to this method. `OnStop` revokes and stops the same private actor. `OnStart` retains `ServiceGate.LiveEligible()` denial and has a second mandatory literal denial even if that legacy gate were mistakenly changed. The candidate has **NO `Main` method** and cannot be executed as a Windows service on its own.

## 2. Actual functionality and why this is not an unlocked native service

The service-owned object has a single nonreentrant lock for all entrypoints: `RefuseRequest`, `Revoke`, `MarkFault`, and `Stop`. It owns admission state, not an injected `ITrustedPendingApproval` callback. It considers bounded synthetic request **metadata only**, verifies the original three literal release/effect guards, and **unconditionally refuses** every request. Faulted requests return `RecoveryRequired`; no request can return `StoredUnverified` or `RemovedUnverified`. There is no native dispatch entrypoint, IPC endpoint, real consent issuer, secret candidate bytes, service installer, protected persistence, credential API call or provider request.

This is a **concrete host-integration / fail-closed composition candidate**, and is deliberately more limited than a real native consent-to-effect repair. It does **not** demonstrate locking across an actual WinCred dispatch. The P96 genuine legacy coordinator race remains OPEN; P97 demonstrates only a separate in-process fake dispatch design; P98–P99 established original source refusal. Real G1–G3 security review/implementation are required before any true native effect becomes admissible.

## 3. Test method and restrictions

- Compile the **other 10 original P49 C# service files** from `tests/p99_original_native_c1_denial` alongside `native_c1_candidate/{CustodyService,ServiceOwnedAdmissionBoundary,ServiceHostAdmissionTests}.cs`. Do **not** include both original and candidate service hosts in one assembly: that would create a duplicate `CustodyService` class.
- Choose `/main:P101ServiceHostAdmissionTests` as a test-only executable. NEVER execute `ServiceBase.Run`, install the service or call the original protected native WinCred adapter.
- Native tests exercise actual linked service types, startup refusal, no static service entrypoint, SAVE/REPLACE/DELETE denial, malformed metadata, 8 concurrent worker threads/one revoker, concurrent fault/stop, 1000 sequential refusals, permanent fault/recovery and the actual P49 installed-state refusal. All are no-authority tests.
- Preserve original byte-for-byte P99 copies and run original P99 20-case baseline test as an independent comparison. P96 actual-source fake-only negative proof must continue to reproduce original flaw; P97 disabled corrective model tests must remain separate.
- No Windows x86 execution: Kristian's P97 x86 was legitimately blocked by enterprise Code Integrity events 3077/3033. P101 x64-only CI and local test results **do not** imply x86 acceptance or permission to work around policy.
- No P62 historical refused operation reproduction or workaround; this is a different, safe, disabled service-host review diff.

## 4. Explicit remaining G0–G6 review gates

See `D:\Nayeon\BYOK_C1_P100_QUALIFIED_NATIVE_SECURITY_REVIEW_DOSSIER_20261107.md` and [P100 GitHub review request](https://github.com/krismcan/Mark-LV/pull/24#issuecomment-6709413936).

**G0:** Original source-chain/integrity review (including P85 source guard).
**G1:** Real elevated one-use local consent with authenticated IPC and exact user/session/operation/candidate/expiry binding. **Not implemented.**
**G2:** Real native service-owned *effect* dispatch and revocation in one approved lock, with protected OS mutex ordering and no caller-injected callbacks. **Not implemented. P101 intentionally has NO effect dispatch.**
**G3:** Protected disk journal, HKLM anchor, enrolment witness, persistent fault, durable interruption/restart recovery and native rollback prevention. **Not implemented in trusted production integration.**
**G4:** Reviewed fixed-target pending-only Windows Credential Manager adapter with real local data handling, synthetic tested first. **Existing real adapter remains disabled.**
**G5:** Approved enterprise signing and installed Windows x86 testing on Kristian, no policy bypass. **Blocked/unresolved.**
**G6:** Independent security GO, three complete native Windows product regressions with native logs/hashes, sealed Git release and original same-ID Google Drive master readback/update followed by dashboard. **Not achieved.**

**Disposition:** A review-ready, non-deployable Windows service-host admission composition candidate, not a production fix, not a production install or credential manager. BYOK C1 RELEASE HOLD. No real key required.
