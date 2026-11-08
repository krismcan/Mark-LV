# BYOK C1 P109 — Same-actor terminal one-use ordering, test-only decision linearization

Date: 8 November 2026 | Operating model OM v2.1 | **NOT A PRODUCTION DISPATCH FIX / NOT A CONSENT ISSUER**

## Rationale: genuine G2 work, not another disconnected fake

Original SHA-pinned P49 C# `PendingCustodyTransaction.Apply()` still has the P96-proven check-to-effect TOCTOU for SAVE/REPLACE/DELETE. The old effect-capable interface is not safe to enable. P108 placed a permanent terminal refusal under the real candidate service-owned monitor, but did not exercise a *positive decision point*. P109 adds a candidate **single-owner one-use decision-state transition** under that SAME monitor and integrates revocation/fault/stop into its state machine. This can test mutual exclusion and truthful late-revocation semantics before designing real trusted consent and a native WinCred effect.

It does **NOT** perform a native effect or prove future effect/consent atomicity. A synthetically committed integer is not a valid approval, a key write, an anti-rollback witness, or a safe dispatch permit.

## Exact code and build separation

- Starting base: P108 `c02c87631b7a1d9eb99c37e6d90d737c5cf6254c`. Exact original 11 P49 C# source units remain untouched, including `PendingCustodyTransaction.cs` and all three immutable production-denial gates. P96's negative test coordinator also remains exact original SHA.
- `native_c1_candidate/ServiceOwnedAdmissionBoundary.cs`: privately held `TerminalDecisionPhase` with `Unavailable`, `SyntheticPrepared`, `SyntheticCommitted`, `SyntheticTerminalUnverified`, `Revoked`, `RecoveryRequired`. All state writes use the original service-owned `lock(gate)` used by `Revoke()`, `Stop()`, `MarkFault()`, P106 J2 observation and P108 refusal. `Revoke` before commit denies decision; after commit it may record that revocation is **too late** (never claims effect cancellation). Stop after possible commit latches recovery, not cancellation. Fault and unknown intent latch recovery and never rearm.
- **Crucial build restriction:** `PrepareSyntheticOnly()`, `CommitSyntheticDecisionOnly()`, `FinishSyntheticTerminalUnverified()` and marker getters are enclosed in `#if C1_SYNTHETIC_TEST`, in BOTH the nondeployable `CustodyService` and internal `ServiceOwnedAdmissionBoundary`. The ordinary production-intended compilation has **no** methods capable of preparing or committing even a synthetic decision. No native credential adapter is referenced or invoked by those methods. A named synthetic-only integer counter is the only thing a positive decision changes.
- `tests/p109_native_oneuse_linearization/NativeOneUseLinearizationTests.cs`: 21 synthetic test cases; explicitly refuses to compile without `C1_SYNTHETIC_TEST`, run only on a separate unprivileged GitHub-hosted Windows runner. Tests include 80 real 2-thread commit-vs-revoke races and 12-thread single-winner contention, no rearm, stop/fault/unknown intent and post-commit too-late cancellation.
- `tests/p109_native_oneuse_linearization/OrdinaryAssemblyAuditTests.cs`: 8 separate native tests compiled WITHOUT any test define. Uses compiled reflection to prove all 3 positive synthetic methods and readback getters are **absent** from both candidate host and internal boundary; original release gates and permanent refusal remain.
- Original 15-case P108, 23-case P106, 20-case P99, and original 15-case P96 **legacy race negative comparator** continue unmodified. Expected focused native cases: **21 + 8 + 15 + 23 + 20 + 15 = 102**. P96 passing means the old G2 bug **STILL EXISTS**, not fixed.

## Explicit source-to-production non-promotion guard

All actual production release gates remain hardcoded closed: `ServiceGate.LiveEligible() == false`, `PendingServiceState.LegacyEffectEntryDisabled() == true`, `PendingWinCredStore.NativeMutationAdmissionPending() == true`. Candidate service remains non-installable (no `Main`, no installer or IPC listener). Original privileged WinCred and protected evidence adapters are NOT used by the new decision marker. Even in an incorrectly test-defined assembly, all three original release gates remain closed.

The target production design requires genuine G1 independently authenticated elevated human intent (not a same-user SID or caller-provided digest), service-owned durable one-use consumed approval, uniquely bound request/operation, independently protected custody journal+HKLM/antirollback witness, original real native mutex tenure, and a separately reviewed **single effect-capable private service actor** that holds the same revocation authority through the irreversible decision and exactly one native WinCred attempt. A decision marker alone cannot be repurposed as a permit; the positive synthetic methods MUST NOT ship, and a release build must have a separate source/security review.

## Windows test environment

Use isolated ephemeral GitHub Windows runner as expressly approved by the user for unprivileged synthetic tests, read-only source token and original raw SHA256 pins. Compile and run both synthetic-defined test executable and ordinary no-define audit, plus original P108/P106/P99/P96 native suites. Capture genuine native compiler/exe exit codes and complete logs. **Do not run unsigned binaries on Kristian**, disable Smart App Control, route secrets through CI, install any privileged service, invoke WinCred, bypass any safety block or attempt a production release.

P109 branch MUST remain draft/unmerged pending qualified independent external review. No actual LocalSystem credential or provider effects. All 17 historic product modifications preserved. No three complete product regressions, no Google Drive master XLSM/dashboard updates until actual authorised release.

**G0–G6 HOLD; P109 is a verifiable source-level sequencing increment, not production BYOK C1 completion.**
