# Phase 8.9 — Read-only Provider/Credential Reconciliation and Recovery Advice

**Date:** 9 October 2026
**Branch:** `nayeon-v1`
**Protected HEAD:** `2eebd60907bb083c8a42190841875f5718b52979`
**Protected product tag:** `nayeon-v1-trusted-credential-onboarding-explicit-operations-01`
(peels to `eeb85d5e85fefa6abb37cfedef6c956954b41a0b`).
**Starting full regression:** 1,916 / 1,916 PASS.

The user explicitly approved two new read-only production modules, deterministic
fake-backend tests, and narrowly reconciled historical test allowlists.
**No staging, commit, tag, push, master workbook update, or Codex context refresh
without a separate seal approval.**

## Candidate production design

### `nayeon/brain/connection_reconciliation.py`

- `observe_connection(path: Path, availability: CredentialAvailability)` is
  trusted-caller-initiated. The caller must pass an **exact native `Path`**
  and a read-only source exposing callable `is_available`.
- Always loads connection metadata freshly through
  `bootstrap_provider_connection(path)`, instead of using an existing cached
  `ProviderConnectionService`.
- Uses the sealed pure `assess_provider_connection_readiness` for canonical
  provider and credential-identifier gates.
- If metadata is unsupported, re-reads metadata but does **not** probe the key.
- If metadata is unconfigured or canonically OpenAI, probes **only**
  `SecretIdentifier("openai.api_key")` via `is_available` once.
  It does not use `get`, `SecretValue`, validation, provider SDK, or writes.
- Re-reads metadata with another fresh owner after the availability check,
  comparing the *entire immutable document* and readiness status. If they
  differ, returns `CHANGED_DURING_OBSERVATION`.
- Load, parse, backend, unsupported result type or recheck errors produce
  `UNKNOWN`. No paths, models, secret identifiers, provider responses or
  secret values are exposed in the immutable result.
- Results: `SETUP_REQUIRED`, `UNCONFIGURED_CREDENTIAL_PRESENT`,
  `CREDENTIAL_REQUIRED`, `VALIDATION_REQUIRED`,
  `UNSUPPORTED_CONFIGURATION`, `CHANGED_DURING_OBSERVATION`, `UNKNOWN`.
- `VALIDATION_REQUIRED` means **credential present at an observation point**,
  not provider authentication success, model entitlement, durable availability,
  successful AI generation or permission to use the key.

### `nayeon/brain/connection_recovery_advice.py`

- Pure `advise_connection_recovery(ConnectionObservation)` maps each exact
  observed status to a frozen enum advisory step. There are no backend,
  credential, path, file, network, execution or mutation imports.
- All recommendations are **human-facing suggestions only**. They do not
  perform, authorize, retry, schedule or roll back any operation.
- The saved key is never automatically deleted when metadata is unconfigured.
  Unsupported provider metadata never authorizes key inspection.

## Concurrency and failure limits

- Two metadata reads can detect changes **between their observations** but
  cannot guarantee a coherent global snapshot or detect A→B→A changes.
- One availability check is a point-in-time observation, not a locked read.
  The key can change immediately before/after that check or between reads.
- File-store atomic replace only protects one metadata file write. The current
  file store has no shared lock, compare-and-swap or cross-store transaction.
  `BoundCredentialLifecycle` also lacks CAS and rollback. Phase 8.9 does not
  add either.
- A return of `UNKNOWN` or `CHANGED_DURING_OBSERVATION` fails closed;
  never use such results to trigger mutation, automatic retry or success claims.
- No normal-user UI, model-callable capability, background polling, runtime
  startup wiring, automatic reconciliation, vendor validation or access to
  Windows Credential Manager was added.

## Testing and scope protection

New deterministic suites:

- `tests/test_connection_reconciliation.py`: null/missing metadata, both
  key-presence states, canonical provider key gate, unsupported provider/key,
  corrupt metadata, read/backend errors, invalid return types, metadata
  changes during availability checks, unauthorized callable imports,
  non-disclosure, exact typed results, and **Phase 8.8 sealed-product freeze**.
- `tests/test_connection_recovery_advice.py`: exhaustive seven-state mapping,
  immutability, pure import/call scope, no automatic retry, no secret surface.

Exactly **13 existing guard tests** are proposed for narrow historical
allowlist updates, preserving prior frozen production and direct/native secret
authority prohibitions.

**Frozen baseline:** all 104 previously sealed Phase 8.8 production Python
files and `requirements.txt` remain byte-identical; only the two new
production modules are allowed. Unmodified protected roots include
`AGENTS.md`, `.codex/CURRENT_STATE.md`, `main.py` and legacy MARK code.

## Test evidence

- Focused Phase 8.9 tests: **27/27 PASS**.
- Affected trust-path/security tests: **168/168 PASS**.
- Full `unittest discover`: **1,943/1,943 PASS**.
- Python `compileall`: **PASS**.
- Independent exact-scope/import/read-only/freeze audit: **PASS**.

Authoritative host Python:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

## Next gate

Obtain explicit human approval for the exact staging/scope review, seal-time
full regression, one local product commit and annotated milestone tag.
Remote push, master workbook and Codex context require separate approvals.

**Current state:** implementation candidate, **NOT SEALED**.
