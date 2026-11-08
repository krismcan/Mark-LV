# BYOK C1 P112 — fixed-path protected custody observation without writable storage adapters

Date: 8 November 2026 | OM v2.1 | **Security-constrained review candidate — no authentic human consent or credentials**

## Actual material improvement over P111

P111's strict C# source allowlist excluded the original `PendingCustodyTransaction`, `PendingServiceState`, `PendingWinCredStore` and original mutex from the candidate review assembly, but **still included the original `CustodyJournalFile` and `CustodyRegistryAnchor` with write-capable `Append` and `WriteAnchor` methods.** Those methods were never called, yet their compilation gave the candidate an unnecessary protected-storage mutation capability.

P112 replaces the direct original writable journal/anchor adapters in `NativeJ2ProtectedReadOnlyPreflight` with `CandidateProtectedReadOnlySnapshot`: a **fixed-path read-only observer** with no journal or HKLM write/create APIs, no Windows Credential Manager API and no caller-supplied paths. The already-disabled candidate `CustodyService` and `ServiceOwnedAdmissionBoundary` remain unchanged. This is a genuine assembly capability reduction, not another synthetic effect counter.

The stricter review-only C# build has **3 original immutable P49 sources**: `ServiceGate.cs`, `ProtectedAcl.cs`, `CustodyLedger.cs`; and **7 candidate sources**: `CustodyService.cs`, `ServiceOwnedAdmissionBoundary.cs`, `ServiceBoundRequestIdentity.cs`, `NativeJ2ProtectedReadOnlyPreflight.cs`, `CandidateCredentialEffectHold.cs`, `IsolatedCandidateContracts.cs`, `CandidateProtectedReadOnlySnapshot.cs`. Compile with `C1_REVIEW_ISOLATED_ASSEMBLY` only, **not** `C1_SYNTHETIC_TEST`. This compiled review candidate contains **neither** original P49 storage write adapter, original pending transaction, original WinCred adapter, injectable effect/approval interfaces, original mutex, nor any native P/Invoke. No service Main, user secret, privileged effect, IPC listener, provider or key entry is included.

## Read-only trust conditions

The candidate observer short-circuits to `UNAVAILABLE` unless the **unchanged original `ServiceGate.LiveEligible()`** independently proves installed service provenance (still permanently false on all current hosts).

For future **independent review**, if admitted by a real signed verified service, it must also have a LocalSystem token; `ProtectedAcl.VerifyInstalledCustodyDirectory()` must validate ProgramData ancestry and fixed protected journal path; nonreparse parent and file, original file owner/DACL and bounded strict ASCII J2 ledger validation; file opened `FileMode.Open`, `FileAccess.Read`, `FileShare.None`; HKLM 64-bit fixed `SOFTWARE\Nayeon\BYOK-C1` with owner/access checks for both parent and child that refuse unknown ALLOW ACEs; registry opened with `OpenSubKey(..., false)` only; fixed `CustodyFaultV1` must equal `CLEAR`, fixed `CustodyAnchorV2` must be valid according to original native `CustodyLedger.Verify`. Read both stores a second time and refuse changed values. All exceptions/missing/untrusted data => `RECOVERY_REQUIRED` if a legitimately installed service ever reaches them. The current uninstalled service still reports `UNAVAILABLE` immediately. Neither a valid structural frame nor repeat agreement proves historic freshness, signed consent, credential presence or authorization.

**Unresolved G3 security caveat:** duplicate reads of file+registry are **not atomic across two stores**, the file path is verified and then opened separately (potential TOCTOU), and the original ledger's SHA-256 chain is not independently authenticated anti-rollback evidence. P112 does NOT claim that a real installed service's read is crash/rollback-safe or ready to supply effect authorization. The original OS adapter's exact read semantics were adapted for a smaller no-write compilation; independent Windows native review and real OS security tests are still required before any trust is granted.

## Tested scope and historical regressions

New `tests/p112_readonly_native_assembly/ReadOnlyCandidateAssemblyAuditTests.cs` tests the actual compiled 3+7 allowlisted candidate, verifying old original file/registry writer types ABSENT, no mutable injected effects, no P/Invoke, no candidate storage mutation methods, no synthetic effect entrypoints, uninstalled original service deny-first and J2/A2 status remaining non-authoritative. Expected **27** native cases.

The prior P111 21-case audit **intentionally verified the now-obsolete assertion that original writable file and registry adapters were PRESENT**. It must be retired from the P112 release-shape suite; do not silently rebrand an obsolete expectation as passing. Retain P111's immutable original CI evidence and keep its complete historical trace in PR #36. Independently rerun the **129 relevant native P110/P109/P108/P106/P99/P96** suites, with original 11-source P49 hash pins and the old P96 race negative comparator intact. Expected P112 focused total **27+129=156 genuine hosted Windows native cases**, provided all pass.

No Windows Smart App Control change, unsigned local host execution, installed service, consent, WinCred, credential, protected file/registry mutation, provider, GitHub release or master Drive workbook/dashboard update. Original 17 historically dirty product paths preserved. P62 original OpenAI support block not rerun. Security-relevant code remains DRAFT, cannot be merged or released before G0/G1/G2/G3/G4/G5/G6 independent review and three full product Windows regressions.

**P112 is stricter passive-observation capability isolation — BYOK C1 production HOLD.**
