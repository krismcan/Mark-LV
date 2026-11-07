# P102 — Immutable Service-Bound Request Metadata (Disabled C1 Candidate)

**Date:** 7 November 2026 | **Nayeon v1** | **OM v2.1**
**Disposition:** Review-only native host input hardening, genuine Windows x64 native tests; **NO AUTHENTICATED CONSENT, NO P61 REPAIR, BYOK C1 PRODUCTION HOLD.**

## Problem and concrete scope

P96 proved that the original native C# `PendingCustodyTransaction` can call a **fake** pending credential effect after fake approval was revoked between its last `StillCurrent` check and effect dispatch. That source defect remains OPEN and production WinCred stays physically disabled. P97 established a separate test-only corrected monitor; P99 compiled all original source units and their three independent denial gates; P101 integrated a refusal-only service-owned admission object with a separately modified, non-deployable `CustodyService` candidate.

P102 hardens the **actual P101 service-owned host candidate** with a new `native_c1_candidate/ServiceBoundRequestIdentity.cs`, an immutable C# structural identity. The existing P101 host and `ServiceOwnedAdmissionBoundary` are changed to expose a metadata-only `RefuseBoundPendingOperation` path, which always returns DENIED or RECOVERY_REQUIRED.

**Six source/review paths relative to P101:** two modified candidate C# files (`CustodyService.cs`, `ServiceOwnedAdmissionBoundary.cs`), one new immutable C# request type (`ServiceBoundRequestIdentity.cs`), one new native Windows C# test harness (`tests/p102_service_bound_request/ServiceBoundRequestTests.cs`), this review note, and one additive x64 GitHub Actions workflow.

## Request identity and ownership rules

`ServiceBoundRequestIdentity` has exactly six immutable `readonly` C# fields:
- Exactly one original `LedgerOperation`: SAVE, REPLACE or DELETE
- Exactly 32 lowercase hexadecimal characters for a nonsecret session identifier
- Exactly 32 lowercase hexadecimal characters for a nonsecret request identifier
- Exactly 64 lowercase hexadecimal characters for an untrusted candidate SHA-256 **claim** for SAVE/REPLACE; null for DELETE
- UTC expiry ticks in the valid .NET DateTime range
- Destructive acknowledgement: required for DELETE, forbidden for SAVE/REPLACE

The constructor rejects malformed shape and conflicting operations. It logs no user input and stringification redacts all fields. A digest supplied by the caller is **NOT proof** that the candidate was obtained securely or accepted by a user. It should never be used as a password surrogate, authentication token, or stable secret identifier. The C# host has no API key bytes and no native credential adapter entrypoint.

The service-owned boundary reads its own `DateTime.UtcNow.Ticks` to refuse expired or overly long claims (more than five minutes in the future). Clock sanity is not authentication. Under the same monitor already used for stop/revocation/fault/refusal, a bounded set of at most **128 nonsecret session/request identifiers** detects duplicate structural submissions. It does not accept requests and cannot grant permission. A duplicate is refused, not rearmed; a saturated set refuses new submissions without letting an unauthenticated client force a global fault latch. A true Windows service must instead rely on a trusted one-use issuance/consumption store, DoS resistance and authenticated IPC, which **do not exist yet** and need qualified external review.

## Tested production boundaries and warnings

- The P101 candidate's original metadata-only `RefusePendingOperation` is preserved and remains an unconditional denial.
- The new `RefuseBoundPendingOperation` is also an unconditional denial, even with an exactly shaped future-expiry claim. There is no permission-flipping code path, caller-provided approval callback, dispatched effect delegate, or WinCred API.
- Original P49 `ServiceGate.LiveEligible()` remains false; `PendingServiceState.LegacyEffectEntryDisabled()` and `PendingWinCredStore.NativeMutationAdmissionPending()` remain true. All original P49 and P99 C# sources are unchanged.
- Actual service installation, credential UI, elevated consent issuer, OS-authenticated named pipes, durable journal/HKLM anchoring, Windows Credential Manager, provider validation and real protected recovery remain **out of scope**.
- P61 HIGH user-consent provenance/IPC and MEDIUM real source race remain **OPEN**, requiring qualified independent Windows native security signoff. The structural request type must **never** be accepted as a trusted consent authority.
- Windows x86 execution was legitimately blocked in P97 by enterprise CodeIntegrity policy (events 3077/3033); do not bypass it. P102 is deliberately x64-only on Kristian and GitHub CI.
- Original OpenAI Support P62 platform refused operation, P85 historical source gate, and unreviewed historical fixture-migration gates remain untouched. No real keys or privileged operations.

## Verification plan and release disposition

Compile P102 against **10 unchanged genuine P49 native C# source units**, the P101 review-only host and denial boundary, and the new immutable request. Exercise malformed/bound/replayed/expired/duplicate/nonsecret-window requests, 8 real concurrent Windows threads, 128-record bound, host revocation/fault/stop, and all three original native denial switches. Re-run the 24 P101 host tests and the 20 P99 unchanged native tests; keep P96 negative and P97 corrected fake-only comparators. Run the affected Python3.12/3.14 Windows suites. Native CI must authenticate the exact source and all original 11 P49 SHA256 pins.

**Security proof deliberately NOT claimed:** This does not implement actual one-use elevated consent (G1), a real service-owned lock over WinCred dispatch (G2), durable protected recovery (G3), authorized signing (G5), or qualified independent GO/full regressions (G6). C1 production remains **HOLD**. Do not merge/install/enter real keys.
