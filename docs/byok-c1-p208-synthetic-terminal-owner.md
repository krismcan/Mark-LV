# P208 — Integrated Synthetic One-Use Native Terminal Actor

14 November 2026 — BYOK C1 engineering, OM v2.1

**Parent:** P207 `5118e29aee5a02d80e329894a45d5e9c06c4c394`.
**STATUS:** Nondeployable native test-only synthetic integration. REAL KEY **NO-GO**. PRODUCTION **HOLD**.

## What is actually implemented

`native_c1_candidate/P208SyntheticTerminalOwner.cs` compiles **only under**
`#if C1_SYNTHETIC_TEST` and wraps the unchanged actual native
`CustodyService` + `ServiceOwnedAdmissionBoundary`. It does not deploy, call
`ServiceBase.Run`, create IPC, instantiate WinCred or hold any key value.
No compiler symbol, no class. Native C1 service's real effect authority
continues to return false and `OnStart` continues to throw.

The test-owner object has its own serialized terminal lock and a private
service candidate whose lock enforces the existing synthetic fixed-effect
attempt. It produces an in-process **reference-identity** review for exactly
one of `LedgerOperation.Save/Replace/Delete` with appropriate destructive
acknowledgement. One original-bound review may reach exactly one **integer**
fake-effect attempt; it consumes its review before that attempt and treats
EVERY attempted outcome as `RecoveryRequired`, including a fake success.
No retry, no rearm, no user-provided operation target, no callback, no
WinCred, no true terminal success result. Forged/cross-owner/wrong-operation
review, revocation before attempt, fault and stop all refuse or retain
reconciliation state. Replays and concurrent submissions cannot increment
the fake count twice.

This code **does not** implement trusted UI/service provenance or
authentic consent, durable protected custody, restart antirollback, actual
WinCred effects, production installation, or enforcement of the P132 Python
mutation path. A cloned test assembly may create its own test review;
this is not a cryptographic authorisation token. An in-process reference
is explicitly insufficient for R1/R2/R3.

## Source and test custody

Only five additive P208 paths were created:
- `native_c1_candidate/P208SyntheticTerminalOwner.cs`
- `native_c1_candidate/P208SyntheticTerminalOwnerTests.cs`
- `scripts/p208_windows_synthetic_terminal_owner.py`
- `docs/byok-c1-p208-synthetic-terminal-owner.md`
- `.github/workflows/p208-windows-synthetic-terminal-owner.yml`

Original frozen P49 11 native protection files, original P96 comparator,
P132 Python/UI/backend, modern Phase10/P76, existing native candidate
`ServiceOwnedAdmissionBoundary` and `CustodyService` are unchanged.
`scripts/p208_windows_synthetic_terminal_owner.py` authenticates the
actual GitHub push event, exact P207 commit ancestor, the five additive
source diff, original source pins, before/after source and clean checkout.
On a genuine Windows host it compiles **the original ten P49 dependencies
plus seven original native candidate files**, the new P208 actor and test
fixture, under `C1_SYNTHETIC_TEST`. It executes original P132 36,
P206 12, P207 14, original native P49 20, C1 host 24 and the new P208
20-case native C# executable. Genuine compiler and OS exits and raw
SHA-256 logs are archived on both failure and success.

New native test cases cover fixed target, absent token, Save/Replace/Delete,
destructive ack, invalid operation, duplicate review, forged token, foreign
owner, wrong operation, replay, revocation, fault, simulated native unknown
result, stop, two simultaneous submitted reviews, restart/new owner using
stale review, and late revocation after possible fake effect. These are
**fake integer effects**, not a claim about a real credential or durable
approval.

## Next implementation (P209)

Implement a *separate* dormant protected journal and recovery state
candidate whose fully authenticated Windows-native original source and
fresh-epoch authority survive restart under a qualified design. Do not
silently wire it to WinCred or the real user-scope process. Required
negative proof: prepared vs consumed vs uncertain state, crash after
durable intent before effect, after effect before terminal, torn writes,
ACL failure, rollback/ABA, replay/cross-epoch and no automatic retry.
Use simulated faults and disposable nonprivileged test data first.

**External approvals remain out of scope:** independent GOV-01/02,
SEC-03/04, REL-05/06/07 and G0–G6, actual Windows signed service/UI,
authenticated peer IPC, Code Integrity/WDAC/SAC policy administrator,
local explicit real-key pilot consent, P135/P175/P178/P179/PERF-P187-01
recovery, and three unfiltered full product Windows regressions (0/3).
BYOK C2 validation is not authorised. No release or Drive/dashboard
production mutation occurs on this draft branch.
