# P98 — Real disabled native service startup and composition preflight (review-only)

**2026-11-07 | Nayeon v1 BYOK C1 | OM v2.1 | RELEASE HOLD**

## Intent, measured result and important limitation

P97 proved a corrected **in-process fake-only** admission/revocation ordering model. P96 still reproduced the genuine original native service transaction race with fake effect adapters, for SAVE/REPLACE/DELETE. P98 targets an *adjacent real production boundary*: compile **byte-identical copies of actual P49 Windows native service-host and policy source** and invoke the real `CustodyService.OnStart` method *without registering or starting any SCM service*. Confirm the original, still-disabled startup and request handling refuse credential authority. It also adds an isolated, dormant `native_c1_review/DisabledServiceCompositionFence.cs` as a no-effect composition proposal for qualified review.

**The native service has not been modified.** All source copies are in the tests directory. The new proposed fence is not included by the real native service, installer, credential-entry UI, provider, IPC route or desktop product.

## Exact authentic P49 source bytes

Compared byte-for-byte using SHA256 against `D:\Nayeon\BYOK_C1_P49_PRIVILEGED_SERVICE_20261029\src`:
- `CustodyService.cs` SHA256 `49217E9018AB2437D3F2B4B2907C08946432352618EDEE065F734D88B93EC093`.
- `ServiceGate.cs` SHA256 `F65EF9F04283B6CA82D42B8D61B6B99B23262DE62E248DC575C0CEF1B3D96B8D`.
- `ProtectedAcl.cs` SHA256 `7152A0DB081EE9627B0F8E4D0D0230168FBF194752F3180DC884C694199AEC61`.
Existing P95 authentic ledger and P96 genuine coordinator source remain SHA-pinned and unchanged.

The real `ServiceGate.LiveEligible()` keeps immutable binary-approval and independently reviewed release checks *false*, even if a caller lies to the lower-level pure helper `EligibleForService`. `CustodyService.OnStart` cannot accept that caller assertion. The actual `ServiceGate.HandleUntrustedRequest` returns `UNAVAILABLE` without interpreting untrusted key-like strings.

## Genuine native Windows review tests

The x64 test assembly compiles exact service host/policy/ACL source + new standalone dormant fence. It does **not** call `ServiceBase.Run`, register SCM, install packages, grant OS privileges, open WinCred, configure ACLs, write to HKLM or access the user's keys. It invokes the real protected `OnStart` **as a method through reflection** and expects `InvalidOperationException("Custody service is unavailable")` from its original release gate. This is not starting a Windows Service.

Test cases cover actual service-name and image identity, immutable LiveEligible refusal, unknown/null/large IPC request denial, pure policy-helper negative/positive synthetic proof flags, absent signatures, and parallel real Windows threads contending on a **separate disabled refusal-only fence**. That fence owns a monitor, but **contains no effect delegate, credential adapter, journal, consent ticket or dispatch**. All decisions are `UNAVAILABLE` or `RECOVERY_REQUIRED`, and every native-effect/retry/verification/installation flag is permanently false.

**This is not P61's actual native effect-lock remedy.** The real check-to-effect race P96 exposed remains OPEN. P98 instead confirms and packages the real service-start and request refusal surfaces, reducing the risk of accidentally switching on an unsafe service while the proper independently reviewed successor is designed.

## Windows x86 policy and review holds

P97 x86 native executable was genuinely blocked on Kristian by Windows CodeIntegrity enforcement (event IDs 3077 and 3033, enterprise policy `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`). P98 intentionally does **not** execute or repackage any x86 test binary, either on Kristian or external runners. An authorized managed code-signing/test route must resolve this. The historic OpenAI P62 Desktop Commander safety-block operation remains untouched. No attempt to bypass it or the Windows signing policy is permitted.

No qualified security approval, authenticated one-use elevated consent, IPC peer trust, protected HKLM/journal persistence, pending-only native WinCred lifecycle, three complete Windows product regressions, Git release seal or same-ID Google Drive master/dashboard update.

**P98 disposition: actual-source service startup DENIAL proof; not a production-ready C1 implementation.**
