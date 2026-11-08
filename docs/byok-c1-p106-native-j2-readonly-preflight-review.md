# BYOK C1 P106 — Real-source native J2 read-only preflight (nondeployable; execution blocked)

Date: 8 November 2026 | OM v2.1 | **P106 CANDIDATE / NO NATIVE RUNTIME ACCEPTANCE / PRODUCTION HOLD**

## Exact source lineage

Parent: P105 review branch `byok-c1-p105-native-j2-recovery-compat-20261108`, exact commit `3813e9a8f5b3a5d899371b5192d1039586ae8ec3`.

This increment adds `native_c1_candidate/NativeJ2ProtectedReadOnlyPreflight.cs` and tests, and edits only the existing P101/P102 candidate `CustodyService.cs` and `ServiceOwnedAdmissionBoundary.cs` to expose an **internal** read-only preflight. The entire original P49 set of 11 C# source files stays byte-pinned and unchanged. No executable `Main`, installer, SCM listener, IPC trust, WinCred mutation, key input or provider activation was introduced.

### Actual source integration

- The disabled candidate `CustodyService.ObserveNativeJ2CustodyReadOnly()` delegates to the preexisting service-owned admission monitor. Stop/revoke/fault are serialised against observation; fault always means recovery-required.
- New `NativeJ2ProtectedReadOnlyPreflight.ObserveInstalledService()` uses **only the original** `CustodyJournalFile.ForInstalledService()`, `CustodyRegistryAnchor.ReadAnchor()/RecoveryFaulted()`, `ProtectedAcl.VerifyInstalledCustodyDirectory()`, and `CustodyLedger.Verify()`. It never invokes the legacy J1 reader.
- The original `ServiceGate.LiveEligible()` is FALSE, so current Kristian/CI calls short-circuit before any protected OS read. It cannot be made eligible by changing a test flag. Both original native mutation-denial gates also must remain TRUE.
- If a future independent reviewer permits a real installed service, these source methods would perform **read-only** protected J2 journal/anchor inspection with exact reread. They contain no WinCred calls and no native effect path, and no separate anti-rollback witness or real pending-presence validation yet.
- Returned nonsecret structural state is named `JournalClaimsStoredUnverified` / `JournalClaimsAbsentUnverified` to prevent claiming actual key presence; `IN_FLIGHT`, unknown phase, absent evidence or read inconsistency must mean `RECOVERY_REQUIRED`. No result grants trusted consent, effect permission, retry, or production release.

## Genuine local Windows outcome

The source **compiled cleanly** against ten unchanged original P49 dependency C# units plus the disabled candidate service-host/boundary/identity. An initial x64 test executable was built successfully (native C# compiler exit 0, zero diagnostics) but was **blocked before startup** by Kristian's Windows Code Integrity `VerifiedAndReputableDesktop` policy. A PowerShell wrapper inherited a stale `$LASTEXITCODE=0` after an `ApplicationFailedException`; that code is NOT an executable success result, and **ZERO P106 runtime cases ran**.

The source was then amended only to make `IN_FLIGHT` always recovery-required and structurally committed statuses explicitly nonauthoritative. This final source was **compiled only** to a non-executable x64 DLL as a static typecheck, compiler exit 0, zero diagnostics. No further P106 test executable launch or OS policy workaround took place. See the separate sanitised original Windows Code Integrity event receipt.

## Explicit reviewer decisions before any runtime activity

1. G0: independent provenance, exact-source hashes, freeze prior P49 source and 17 original product workspace dirty paths; no P85 override.
2. G1: trusted local elevated human approval issuer and signed UI provenance, authenticated IPC; the new source has neither.
3. G2: real service-owned native dispatch linearisation and P61 revocation/dispatch race repair; this read-only method does not attempt effects.
4. G3: protected journal+HKLM evidence enrollment, independent rollback witness, protected start/fault recovery and freshness, correct J2 schema; structurally consistent J2 alone is NOT a trusted or ready credential state.
5. G4: WinCred fixed pending namespace and authorized LocalSystem context remain untouched and disabled.
6. G5: obtain authorised Windows App Control policy owner written GO/signing/test route for this test before further native runtime execution on Kristian or any alternate environment.
7. G6: qualified independent native Windows security review and full 3x product regressions, release seals and original Google Drive workbook/dashboard update only after actual approved production release.

**Do not infer runtime acceptance from compilation, a test source listing or externally executed older P105 tests. BYOK C1 production release HOLD. No API key required.**
