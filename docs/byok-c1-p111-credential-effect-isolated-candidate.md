# BYOK C1 P111 — Credential-effect capability isolation in the disabled service candidate

Date: 8 November 2026 | OM v2.1 | **REVIEW-ONLY. No native credential effect, no authenticated consent. G0–G6 HOLD.**

## What is materially improved

P107–P110's native C# test projects compiled the 10 or 11 original P49 modules (including `PendingCustodyTransaction.cs`, `PendingServiceState.cs`, `PendingWinCredStore.cs`) together with the non-installable candidate service. They demonstrated that those original types always *refused* effects, but their inclusion exposed old mutable approval/effect interfaces in the same assembly. P96 has proven a post-`StillCurrent()` revocation race in that old transaction if someone later enables its effect adapters.

P111 creates a second, **explicit-allowlist C# build composition** that retains the **same existing candidate `CustodyService` and `ServiceOwnedAdmissionBoundary` source** but completely excludes the original P49 `PendingCustodyTransaction`, `PendingWinCredStore`, `PendingServiceState` and `ServiceCustodyMutex` types from the compiled candidate. No one can call or reflectively invoke their types within this assembly because the types are not present. The original P49 11-source files and historical P96 regression remain entirely unchanged and continue to be tested separately.

This is more than a runtime `bool` check: it is a source/assembly **credential-effect capability topology boundary**, verified by native .NET reflection and exact source allowlist, not only source grep.

## Exact source composition

P111 adds nondeployable `native_c1_candidate/CandidateCredentialEffectHold.cs`, whose `LegacyEffectEntryDisabled()` and `NativeMutationAdmissionPending()` are unconditional `true` and have no reset/unlock. It replaces only the **candidate's direct compile-time references** to effect-bearing original P49 classes with this permanently blocked facade in `ServiceOwnedAdmissionBoundary.cs` and `NativeJ2ProtectedReadOnlyPreflight.cs`. This allows a candidate compilation without a WinCred adapter or the old approval interface; original service guards are still independently pinned and tested using the frozen original P49 sources.

P111 also adds `native_c1_candidate/IsolatedCandidateContracts.cs` with a **status-only `CustodyOutcome` enum under `#if C1_REVIEW_ISOLATED_ASSEMBLY`**. Without this exact define, the original P49 transaction continues owning the enum in the historical native tests. The isolated build and historical regression builds must never compile BOTH enum declarations.

**Exact candidate build source allowlist (11 existing/new source paths):**

| Subset | Included |
| --- | --- |
| Original immutable P49, 5 source files | `ServiceGate.cs`, `ProtectedAcl.cs`, `CustodyLedger.cs`, `CustodyJournalFile.cs`, `CustodyRegistryAnchor.cs` |
| Actual candidate C#, 6 source files | `CustodyService.cs`, `ServiceOwnedAdmissionBoundary.cs`, `ServiceBoundRequestIdentity.cs`, `NativeJ2ProtectedReadOnlyPreflight.cs`, `CandidateCredentialEffectHold.cs`, `IsolatedCandidateContracts.cs` |

The isolated compilation is a **review-only DLL**, with NO `C1_SYNTHETIC_TEST` and NO installable service Main. A separate Windows-native audit EXE built from that exact same list plus one test driver verifies via runtime reflection that no old transaction type, old WinCred P/Invoke target, legacy approval injection, or synthetic effect method is present.

**Critical limitation:** The included original P49 `CustodyJournalFile` and `CustodyRegistryAnchor` are original trusted source and **still expose write-capable methods for protected journal and registry**. These methods are *not invoked*, and the disabled original `ServiceGate.LiveEligible()` keeps actual preflight unavailable, but this is specifically **credential effect isolation**, NOT a claim that the assembly has zero OS mutation methods or that the storage boundary is production safe. Isolating protected mutable-state adapters behind a future reviewed read-only port remains a G3 design task.

## G1 trusted human consent / G2 production dispatch requirements

No amount of source exclusion can authenticate a person. G1 still requires an independent reviewer to select and validate a signed, installed local user-interaction broker and authenticated IPC peer provenance, actual explicit human consent to a fixed pending-only operation and exact private candidate, short expiry, server-issued one-use identity, and protected durable consumed state. An account SID, claimed PID, caller digest, hardcoded yes/no flag, or UAC prompt alone is not acceptable as authenticated consent.

The real G2 successor must retire the original `PendingCustodyTransaction.Apply()` from the deployed WinCred-effect assembly; one and only one fixed-target effect capability must be held privately by a reviewed service-owned actor across a protected atomic decision and a single native attempt, under the same revocation/fault monitor and correct OS custody mutex tenure, with independently durable intent and recovery. P111 does not add that capability or grant production readiness.

## Verification plan / release hold

GitHub-hosted separate unprivileged Windows 2025 CI will run a **21-case source/assembly capability audit** in the actual isolated candidate assembly, verifying excluded types, no WinCred entrypoints, disabled original LiveEligible, terminal denial and J2 observation, and explicitly detecting the residual original journal/registry mutation capabilities. Also rerun the **129 existing native synthetic/denial and P96 legacy-race cases** as regression in a separate historical test assembly; their continued inclusion of original source is intentional for regressions, NOT a candidate build dependency. All native exits, source SHA pins and exact branch ancestry must match.

No user API key, WinCred I/O, actual protected journal/registry writes, privileged service registration, Windows policy alteration, code-signing bypass, P62 retry, GitHub merge/release, or existing product/master-workbook/dashboard mutation. Kristian's 17 historical product dirty paths must be preserved; G0/G6 independent review, G1 signed consent issuer, G2 sealed real-effect dispatch, G3 historical enrollment/antirollback and actual recovery, G4 local vault acceptance, G5 signed Smart App Control admission, 3 full Windows product regression passes and release approval are **still missing**.

**P111 is a narrower genuine capability-boundary improvement, not a finished credential manager. Production BYOK C1 HOLD.**
