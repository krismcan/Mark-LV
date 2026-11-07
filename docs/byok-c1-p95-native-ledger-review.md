# P95 — Native custody-ledger exact-source review baseline (C1 HOLD)

**Scope:** One SHA-pinned, byte-identical copy of the original disabled P49 native C# custody ledger plus a *separate* no-authority readout and executable Windows tests. **No production C1 service entrypoint or credential API is connected.**

## Why this matters

The existing disabled native service implements the C# `CustodyLedger` journal/anchor structural codec. Earlier P93 subprocess crash tests used the Python *pending evidence document* codec, which is a different format. Those tests should not be represented as proof of the C# production-target ledger. P95 supplies the genuine historic C# implementation to GitHub reviewers and Windows runner tests, without altering it.

**Exact provenance:** `D:\Nayeon\BYOK_C1_P49_PRIVILEGED_SERVICE_20261029\src\CustodyLedger.cs` -> `tests/p95_native_custody_preflight/CustodyLedger.cs`. SHA-256 of original and imported file: `93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B`. The imported copy is **for review/testing, not part of a deployed native service**.

## In-scope compiled C# proof

The genuine ledger has a pure structural codec for `J2` journal frames and `A2` anchor digests. It can construct canonical nonsecret journal strings, but **does not persist evidence or authenticate custody**. Added `NativeLedgerPreflight.InspectUntrustedInputs` returns a fixed structural classification and explicitly has **no effect permit, no recovery clearance, no credential verification and no retry permission** on any input. Its boolean trust arguments are untrusted fixtures, NOT independently verified service principals or OS-protected anchors.

The native Windows test executable uses only deterministic dummy nonce strings (a/b/c/d/f repeated hex), with cases for initial, SAVE, REPLACE, DELETE, IN_FLIGHT, terminal, illegal transitions, stale/corrupt/missing anchors, unexpected pending presence, missing journal, invalid format, forgery and valid-prefix truncation.

**Specifically unproven:** The original disabled WinCred adapter, protected NTFS ACL/registry storage, separate fault marker, enrolled service identity, named mutex, durable write ordering, authenticated elevated consent, operation/candidate/session binding, installation, power-loss safety and actual native dispatch. None is invoked by these tests. The generated `J2` strings/anchor checksums are NOT authority, and all currently open P80–P95 source candidates require qualified independent review.

## Non-negotiable controls

- Do **not** modify or silently replace the original P49 `CustodyLedger.cs`; compare exact SHA-256 before and after import. GitHub CI pins imported bytes to the original hash.
- Do **not** wire this test copy or `NativeLedgerPreflight` into the live service, ordinary assistant, key entry UI, IPC, provider or WinCred.
- Do **not** weaken `ServiceGate.LiveEligible`, `PendingServiceState.LegacyEffectEntryDisabled`, `PendingWinCredStore.NativeMutationAdmissionPending`, or the historical P85 source restriction.
- Do **not** reconstruct/rerun the original P62 refused Desktop Commander operation. No real key or privileged operation.
- Separate qualified Windows native security reviewer must sign off actual service admission architecture (P94), OS-protected persistent recovery and consent provenance. GitHub CI is not a reviewer.
- C1 release remains HOLD until trusted implementation, three complete native Windows product regressions and signed-off release. Only then update the original same-ID Google Drive master and afterwards dashboard.

**P95 expected disposition:** source/custody codec evidence suitable for reviewer handoff; **no production GO**.
