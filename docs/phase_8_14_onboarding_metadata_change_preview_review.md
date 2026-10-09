# Phase 8.14 - Pure canonical OpenAI metadata change preview

## Architecture decision
Add only `nayeon/brain/onboarding_metadata_change_preview.py`: a pure,
non-secret comparison of an exact Phase 8.11 proposal plus matching Phase 8.12
preview against an **explicit caller-supplied** exact typed
`ProviderConnectionDocumentV1` snapshot.

The function delegates proposal/preview validation to the sealed Phase 8.13
metadata review and distinguishes only `CREATE`, `UNCHANGED` and
`MODEL_CHANGE`. Existing metadata for other providers or other credential
references is refused instead of proposing an overwrite. The returned
`OnboardingMetadataChangePreview` is frozen, slotted and fail-closed with
`requires_reobservation=True` and `requires_explicit_confirmation=True`.

## Critical trust boundary
The supplied snapshot is not proof of freshness. A diff, even UNCHANGED, is
not permission to save, activate a provider, access secrets, or bypass real
human confirmation. A trusted future host flow must independently reobserve
state, verify permissions, obtain real consent, and enforce its own atomicity
and operation-specific security boundaries.

## Excluded
No UI integration, filesystem writes, credential retrieval/validation,
environment fallback, SDK/client construction, provider operations, key storage,
background retry, automatic provider activation or model-selectable route.

## Acceptance evidence
Exact input and canonical mismatch rejection, unsafe current-configuration
refusal, all three diff kinds, immutable/authority-gated output, no I/O or
SDK imports, affected historical scope reconciliations, deterministic focused,
affected and full regression, clean staged scope, annotated local seal, post-
seal test and remote Git ref verification. Formal end-user readiness remains
5/19 planned exits and 0/12 verified release gates unless new evidence
establishes an actual gate closure.
