# Phase 8.26 — Cooperative trusted onboarding coordination and recovery review

**Date:** 11 October 2026. **Protected starting HEAD:** `26b9c79e0c6fa4a39d0195353195af3b05202682`; clean `nayeon-v1`. **Prior verified regression:** 2,070/2,070.

## Approved bounded scope and acceptance

Human-approved architectural decision: an explicit, fail-closed single-writer model for Nayeon v1 personal alpha; *only cooperating processes in the same Windows logon session*. Do not claim protection against external writers, user intervention, another Windows session, credential compare-and-swap, model entitlement, cross-store rollback or transactions. A verified normal-user connected onboarding journey is a later phase.

Exact additions: `nayeon/brain/windows_onboarding_mutex.py` supplies a fixed-name Windows Local session mutex with nonblocking acquisition and abandonment detection; `nayeon/brain/onboarding_coordination.py` wraps the existing `TrustedCredentialOperationHost`, with no backend mutation calls. A private non-secret snapshot compares strict typed metadata, filesystem identity and read-only credential *availability*, never plaintext; the existing observation rejects unsupported, unknown and changed configurations.

**Execution discipline:** A human may have a pending read-only review without acquiring the mutex; an actual approve request must acquire the shared mutex, re-check the exact earlier snapshot and host eligibility, and create an exclusive non-secret in-flight marker in the trusted metadata directory before delegating to the existing host. Busy, missing, changed, unknown, or unsafe states consume the pending review and refuse execution. Marker creation is exclusive and fsynced best-effort. A prior marker, abandoned mutex, or indeterminate mutation demands manual inspection/recovery and blocks future coordinated writes. Known completion removes the marker; failed marker cleanup fails closed. A successful status still does *not* prove durability, provider entitlement, or atomicity.

**Conservative recovery limitations:** The marker can survive process crash. It must not be deleted automatically on next startup. A human should examine and reconcile current provider metadata versus credential availability and validation, and only then use a separately approved trusted recovery path. The marker itself is not an OS-enforced transaction or immutable audit record. Windows Local mutex spans a logon session, not other sessions. External actors can replace credentials without changing presence, a same-state credential ABA that this boundary cannot reliably detect. File stat changes catch many metadata ABA cases but are not a general CAS.

## Mandatory evidence

- Independent source and trust-boundary audit; reject direct secret backend usage or new model-callable operations.
- Deterministic fake-backend scenarios: pending/reject/replay, single approval, overlapping mutex busy, abandoned mutex marker, crash marker, metadata change including observed ABA, credential availability change, unsupported provider, validator/backend errors, invalid replacement with old value retained, and no plaintext output.
- Controlled live Windows mutex contention between two *test* processes, with no credentials, provider SDK, network, or Windows Credential Manager I/O.
- Full focused/affected and full regressions, compileall, staged scope, Git diff checks; seal-time and post-commit regressions must pass.
- Immutable annotated milestone tag, exact GitHub remote and peeled-tag verification, clean handoff and master same-ID macro-preserving 16-worksheet workbook update.
- Formal Build Plan Phase 8 remains IN PROGRESS, architecture phases 5/19, release gates 0/12 until independently qualifying normal-user evidence.

**Next phase (not part of this milestone):** wire coordination through a trusted, human-consent-bearing credential save/replace/delete interface. This module by itself grants no user-facing credential mutation route.

## Independent risk review — verified implementation constraints

A fresh source review identified an additional concurrent metadata mutation window *during* host execution; the coordinator now performs a second non-secret file/document identity observation before clearing the in-flight marker, with the cooperative mutex still owned. If metadata changes during a credential write or replacement, the result is RECOVERY_REQUIRED with marker retained; if metadata changes during candidate-only validation, no storage occurs and the result is CONFLICT with the marker cleared. Both have dedicated fake-backend regression tests.

The coordinator does not read or reveal credential plaintext, invoke the Windows credential native API, create a model-callable capability, grant permission, or bypass the existing host confirmation. Only the established host can invoke the bound lifecycle after the wrapper's own explicit admission. Existing Phase 6 computer-control production and guards remain unchanged. Historical exact production-file inventories were extended **only** for the two new Phase 8.26 modules, and the approved typed connection persistence reader was explicitly enumerated.

The Windows native test verifies that another Python process in the same Windows session observes the mutex as busy. It does not establish cross-session or external-writer protection. Automatic marker removal after interrupted/indeterminate mutation remains forbidden; trusted human recovery and GUI wiring are for later approved phases.

**Final test baseline, commits, tags and workbook status must be appended only after all sealing and remote verification succeed.**
