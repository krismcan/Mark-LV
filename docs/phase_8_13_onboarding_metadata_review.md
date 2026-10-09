# Phase 8.13 — Pure human metadata review projection

## Architecture
Provide one frozen, slotted, non-secret read-only review of a Phase 8.11 OpenAI
proposal paired with the exact matching Phase 8.12 canonical metadata preview.
Inputs are exact trusted types. The renderer independently regenerates the
canonical document from the proposal and refuses any mismatched or absent
connection. It returns provider, model, canonical non-secret identifier, original
display state, and mandatory reobservation / explicit confirmation flags.

## Non-scope
No GUI, credential value, key store, filesystem change, provider SDK/client,
connection service replacement, permission grant, persistence authorization,
real consent capture, background retry, or model-selectable action. Review
data remains forgeable and stale; it **cannot** be used as proof of consent or
as permission to persist metadata. Future trusted host workflows must
reobserve current state, authenticate human intent and independently authorize.

## Acceptance
Exact type and mismatch rejection; immutable fresh objects; no I/O or SDK
imports; focused, affected-trust and full deterministic regressions; independent
Git diff and tag review; no changes to sealed production modules.
