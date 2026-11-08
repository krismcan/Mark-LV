# BYOK C1 P110 — Synthetic fixed pending effect in the actual service-owned monitor

Date: 8 November 2026 | OM v2.1 | **Nondeployable, synthetic-only effect-ordering test; NOT G1/G2 production completion**

## Why P110, and what is different from P109

The original frozen P49 `PendingCustodyTransaction.Apply()` suffers the reproducible P96 `StillCurrent()` / `SaveOrReplace/DeletePending` check-to-effect TOCTOU. P109 exercised only the positive decision **integer marker**, without an intervening effect call; it did not prove whether a dispatch call held the consent/revocation barrier. P110 now exercises a **fixed operation-bound synchronous synthetic effect attempt** entirely **inside the SAME existing service-owned monitor** used for stop, revoke, fault, J2 observation and terminal refusal.

There is still **no actual WinCred**: the synthetic effect is exactly a local integer increment, not a user-supplied callback, native P/Invoke, credential, provider, store or journal write. Even after an apparently successful fake effect, the new method **always returns RecoveryRequired**, because no independent durable consent/intent/terminal witness exists. This avoids falsely reporting a key as stored.

## Implementation

- In original candidate `native_c1_candidate/ServiceOwnedAdmissionBoundary.cs`, **under `#if C1_SYNTHETIC_TEST` only** add `PrepareSyntheticFixedEffectOnly(operation,destructiveAcknowledgement)` to bind SAVE/REPLACE or acknowledged DELETE with strict fixed operation shape. This is test-only shape, not human approval.
- `AttemptSyntheticFixedEffectOnly(operation,entered,release,simulateUnknownNativeResult)` acquires the same `gate` monitor and performs both synthetic `SyntheticCommitted` decision and exactly **one integer effect marker increment** before a synthetic pause. A concurrently arriving `Revoke` cannot commit during that critical section. If revoke commits **before** dispatch, zero markers and DENIED; if dispatch commits **first**, a later revoke is explicitly **too late**, not cancellation. Synthetic pause coordination is via local `ManualResetEvent` solely for deterministic test scheduling, never a production API or arbitrary effect callback.
- All synthetic effect outcomes, including a simulated native error, latch `faulted=true` and return `RecoveryRequired`. The same instance cannot silently rearm or retry; no WinCred API ever runs. `Stop` after committed or synthetic terminal-unverified phase latches recovery rather than falsely claiming no effect.
- In disabled `native_c1_candidate/CustodyService.cs`, export only *internal* synthetic test-only delegation methods and nonsecret counters, all enclosed by `#if C1_SYNTHETIC_TEST`. Ordinary candidate assembly has **NONE of the synthetic effect methods/counters** and cannot be installed, started or given an authentic approval.
- New `tests/p110_fixed_pending_effect/NativeFixedEffectAtomicityTests.cs` has 19 real native C# tests: fixed SAVE/REPLACE/DELETE operation/ack, wrong operation, one effect max, revocation-before/while/after dispatch, 60 separate two-thread dispatch/revoke races, 12 concurrent dispatch contenders, unknown effect, fault/stop, legacy gate denial and no Main. These are unprivileged and synthetic only.
- New `tests/p110_fixed_pending_effect/OrdinaryEffectSurfaceAuditTests.cs` adds 8 native **non-test** assembly reflection tests: all new fake-effect/prepare/counter entrypoints absent from both compiled service and boundary; original three release gates still hardcoded closed and ordinary source permanently denies operations.
- Original P109 21+8, P108 15, P106 23, P99 20 and crucial P96 old-race negative 15 all remain unchanged; expected focused isolated native Windows tests **19+8+21+8+15+23+20+15 = 129**.

## Important unaddressed production blockers

P110 **DOES NOT** implement G1 trusted signed elevated UI / authenticated IPC or durable explicit one-use consent. It also **DOES NOT** implement a production G2 native fixed WinCred effect-capable actor with full protected journal+HKLM intent/terminal persistence, true mutex tenure and G3 independently protected anti-rollback witness. No actual effect called, and the old P96 vulnerability remains present in frozen original P49 coordinator. A green test of synthetic effect serialisation is evidence only for **that in-memory C# monitor**, not a security-approved production credential transaction.

**Do not port the `C1_SYNTHETIC_TEST` methods as a production release.** The eventual independently reviewed actor must be a separate exclusively sealed fixed-target production effect capability, authenticated consent source, durable one-use service-owned admission record, correct original LocalSystem identity and WinCred semantics, and a narrowly approved signed test/deploy path.

Read-only verification of Kristian: Smart App Control stays on, original 17 historically modified product paths preserved. No P62 rerun, real key, provider request, service installation, live WinCred, local native unsigned exe execution, production release or master Google Drive workbook/dashboard mutation. All G0–G6 HOLD, with qualified independent security review and three complete product regressions outstanding.
