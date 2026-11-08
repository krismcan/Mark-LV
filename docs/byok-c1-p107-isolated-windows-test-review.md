# BYOK C1 P107 — Authorised isolated Windows-native synthetic regression

Date: 8 November 2026 | Operating model: OM v2.1 | **DEVELOPMENT-ONLY, NO NATIVE CUSTODY EFFECTS**

## Explicit development-environment decision

After confirming Kristian's Windows 11 Smart App Control (VerifiedAndReputableDesktop) rejects unsigned test binaries, the user approved separating native synthetic development tests from protected-host acceptance. P107 uses **GitHub-hosted ephemeral Windows 2025 runner** for tightly scoped and source-pinned **unprivileged synthetic tests**. Kristian's Smart App Control stays enabled and P106's original blocked test executable must **not** be retried on Kristian. This is **not** a route around production policy acceptance; it is a separate authorised test environment with different trust boundaries.

## Exact canonical parent, scope, and isolation

Base: P106 draft PR #31, exact source `3cb73013aa063e0e0732f7e07c2d7e0020934b2d`. P107 may add exactly **two files**, this review document and a GitHub Actions workflow. Source SHA-256 pins cover all **11 unmodified P49 native C# units** and all **five P106 native candidate/test-driver files**. No source change, permissive test flag, OS policy change, WinCred adapter change, Main, installer, service registration, credentials, provider or real user identity is included.

New workflow: `.github/workflows/p107-isolated-native-synthetic.yml`, push-triggered only on this P107 branch. `permissions: contents: read`, `windows-2025`, native x64 .NET Framework compiler, `RUNNER_TEMP` executable outputs, explicit runner-not-LocalSystem check, source anti-mutation and disabled-effect gates.

### Allowed native execution in ephemeral CI

1. Compile and execute the **original unchanged P106 23-case native C# test Main** with ten original P49 dependency files and P106's four disabled candidate modules. The test confirms original service not eligible, no installed `ServiceBase.Run`, native J2/A2 structural status never grants authority, IN_FLIGHT fault disposition, stop/fault/revoke thread safety, denial replies, and the actual P49 registry adapter rejects a non-LocalSystem caller **before any protected HKLM read**. The test never supplies a real key or installs a Windows service.
2. Compile and execute the original unchanged **P99 20-case denial-only test Main** with all 11 original P49 source files. Native WinCred Save/Delete methods are invoked **only on the permanent original deny-first guards**, with a one-byte deliberately invalid synthetic payload, and must refuse *before P/Invoke*. No provider or real credential is used.
3. Fail on nonzero native process exit, missing exact PASS counts, any denied process launch, compiler diagnostics, altered pinned source, LocalSystem host, source scope drift, unexpectedly enabled release guards or unverified runner.

### What a green CI run proves — and does not

A successful result means these precisely pinned native **synthetic refusal/preflight tests executed on the isolated hosted Windows runner**. It does **not** mean the original P106 executable passed on Kristian; that run remains denied with **0/23** executed. It is not a test of protected installed service tokens/ACLS, OS-enforced App Control acceptance, real durable journal+HKLM enrollment, real credentials, cross-process consent/effect atomicity, Crash recovery, production signing, or comprehensive three-regression product acceptance. No independent qualified reviewer is simulated.

## Standing holds

- Original P61 consent-to-effect race OPEN; no service-owned trusted G1 approval/IPC issuer or G2 dispatch.
- Actual G3 protected history and independent anti-rollback/fault witness not approved.
- Real pending-only WinCred/G4 prohibited; G5 trusted publisher signing and Smart App Control device acceptance not resolved. Kristian configuration unchanged.
- Original P62 OpenAI platform safety-block operation still not rerun; P85 frozen original sources and 17 historical product changes preserved.
- Qualified G0/G6 independent review and **three full Windows product regressions** not yet performed. No production C1 merge, seal, release, or original Google Drive master workbook/dashboard update.

**If isolated CI has a test failure, preserve authentic failure evidence and repair source/test separately only if needed; never weaken assertions to manufacture a pass. BYOK C1 PRODUCTION RELEASE HOLD. No API key required.**
