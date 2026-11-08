# BYOK C1 P108 — Terminal-denial boundary source increment and legacy G2 race comparator

Date: 8 November 2026 | OM v2.1 | **Source-level guard ONLY — REAL G2 DISPATCH FIX NOT IMPLEMENTED**

## Why P108 is necessary

The original unchanged P49 `PendingCustodyTransaction.Apply` accepts injected `ITrustedPendingApproval` and calls `StillCurrent` separately from `state.SaveOrReplace/DeletePending`. P96 ALREADY reproduced the race for SAVE, REPLACE and DELETE using its original byte-identical coordinator, separately revoking on a synthetic thread between consent check and a fake effect. P108 does **NOT** write another duplicate P96 fake exploit or claim the old route is safe.

The P101/102/106 native candidate host is explicitly non-installable, never calls the P49 transaction, and has no key/native effect. P108 **strengthens that same integrated candidate host**, not the real disabled original P49 service.

## P108 changes — strict review-only service boundary

- In `native_c1_candidate/ServiceOwnedAdmissionBoundary.cs`, introduce `RefuseUnreviewedTerminalEffect()` **under the preexisting single service-owned monitor**. It is serial with `Revoke`, `Stop`, `MarkFault` and the P106 read-only custody observation. It accepts no caller-supplied approval, candidate bytes, callback or WinCred adapter and **always denies**. It records an unprivileged, non-secret refusal count and observation flag only; neither is authority.
- Introduce `RefuseUncertainTerminalIntent()`, also inside the **same monitor**, which permanently marks `faulted=true` and returns `RecoveryRequired`. A subsequent stop, revoke, untrusted request or read-only observation cannot turn that fault into an effect permit or success. This candidate has no means to clear faults or auto-retry.
- In `native_c1_candidate/CustodyService.cs`, expose **internal** zero-argument delegating refusal methods; never a real `Main`, native listener, installer, WinCred effect, recipient callback, mutable `bool approved`, accepted client-supplied digest, key, provider or service start.
- Add 15 native C# focused tests under `tests/p108_native_terminal_denial` against the original **10 unchanged P49 dependencies** and real P101–P108 non-installable service host. Tests exercise terminal denial, stop/revoke/fault state ordering, terminal uncertainty, actual original three native release holds, endpoint shape, 12-thread contention, and absence of old injected coordinator/approval/state in the candidate service.
- The original 11 P49 C# files, P96 test and proof, P106 23-case tests, P99 20-case tests and P107 isolated CI remain **byte-for-byte unchanged**.

## Native execution and acceptance

Run P108's **15** denial-only candidate tests on isolated GitHub-hosted Windows runner, plus the unchanged **P106 23**, **P99 20**, and crucial original **P96 15** negative cases as a historical comparator. A passing P96 test means it **still reproduces the legacy flaw**, NOT that it passes G2. Total expected focused native cases **73**. Verify exact sources by SHA-256, native C# exits, exact pass markers, no app-control changes, and no privileged credentials.

P108 adds one terminal **refusal** method to prevent mistakenly treating syntactic consent as a service effect permit, but it **does NOT** implement the required G1 trusted elevated consent issuer, service-owned one-use durable grant, G2 irreversible dispatch linearisation, G3 protected enrollment/rollback authority, actual native WinCred effects, or trusted signed production service. It cannot prove cancellation ordering around a real effect because there is NO effect path. Those are independent review/implementation items, not passable by making the method return `true`.

## Mandatory final disposition

No original P61/P49 coordinator modification. No enabling `ServiceGate.LiveEligible`, `PendingServiceState.LegacyEffectEntryDisabled`, or `PendingWinCredStore.NativeMutationAdmissionPending`. No `BYOK_TEST` assembly unlock, native credentials, provider, API key, privileged service, signing workaround or re-run of blocked executable on Kristian.

Protected Kristian Smart App Control remains **On**. 17 original product dirty paths preserved. No qualified independent G0/G6 security review yet, no 3x complete product regressions and no production release/Google Drive master-dashboard update.

**P108 is a guarded source increment, not G2 remediation completion. G0–G6 production release HOLD.**
