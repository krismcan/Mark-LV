# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.3 - Bounded Credential Lifecycle & Typed Provider Connection Configuration
- **Latest milestone tag:** `nayeon-v1-bounded-credential-lifecycle-provider-connection-01`
- **Full regression baseline:** **1,745 / 1,745**
- **Last updated:** 7 Oct 2026
- **Phase 7 status:** User Identity & Configuration **FOUNDATION COMPLETE**
- **Phase 8 status:** Secure Secrets & BYOK **IN PROGRESS**
- **Next restart point:** Phase 8.4 - Architecture audit for provider credential validation adapter plus typed connection-configuration ownership/persistence; scope not yet approved

## Latest architecture invariant

Phase 8.3 adds two new provider-neutral contracts without modifying any prior production file.

`BoundCredentialLifecycle` permanently binds one `SecretBackend`, one exact immutable `SecretIdentifier`, and one `CredentialValidator`. Its public surface is limited to safe identifier metadata plus `is_connected()`, `test_candidate()`, `test_stored()`, `connect()`, `replace()`, and `remove()`. It exposes no plaintext read/resolve/get/reveal/export path, no enumeration, no rebinding, and no public backend/validator authority. Candidate validation happens before any write; connect and replace both recheck presence state before storing. Replace never deletes or reads the old credential before validating the candidate. The backend has no compare-and-swap primitive, so an external actor can still race between the final presence check and put; no atomicity or rollback claim is made.

Credential validation is tri-state: VALID, INVALID, or INDETERMINATE. Ordinary validator exceptions, including secret-contract errors, are contained as INDETERMINATE with no exception text exposed. Process-control exceptions such as KeyboardInterrupt/SystemExit are deliberately not swallowed. Backend storage errors retain their sealed safe semantics; unexpected backend exceptions become a fixed `SecretStorageError("Credential lifecycle operation failed")`.

`ProviderConnectionConfiguration` is immutable, slotted, strictly typed NON-SECRET metadata only: provider identifier, model identifier, and exact `SecretIdentifier` credential reference. It grants no secret-resolution or lifecycle authority and does not enforce provider-to-credential identity mapping. Future trusted composition must independently verify that mapping before constructing a resolver/provider.

The Phase 8.1/8.2 secret contracts, Windows backend, bounded resolver, OpenAI provider migration, legacy environment SecretStore, AIService, Phase 7 presentation/configuration subsystem, runtime and security authority paths remain unchanged. `BoundCredentialLifecycle` and `ProviderConnectionConfiguration` currently have **zero production consumers**. `BoundSecretResolver` is still consumed only by `OpenAIProvider`; legacy `SecretStore` and direct `WindowsCredentialBackend` each have zero production consumers.

Independent validation passed 38/38 dedicated Phase 8.3 tests, 212/212 combined Phase 7 + Phase 8 suites, 344/344 affected configuration/secrets + trust/orchestration tests, and 1,745/1,745 full regression. No native Credential Manager mutation or provider network call was required because this phase adds only deterministic lifecycle/configuration contracts over the already sealed storage boundary.

## Next architecture question

Phase 8.4 should decide the smallest safe production boundary for:
1. an OpenAI-specific credential validation adapter that implements the provider-neutral `CredentialValidator` contract without leaking provider/network error content; and
2. ownership/persistence of `ProviderConnectionConfiguration` as non-secret application metadata.

The architecture should preserve separation between:
- raw secret storage/lifecycle,
- one-secret provider resolution,
- provider credential validation,
- non-secret provider/model/credential-reference configuration,
- presentation configuration,
- runtime/application composition.

Do not add onboarding UI, provider/model selection UX, generic settings, plaintext secret persistence, environment fallback, broad secret enumeration, additional provider implementations, or runtime wiring until the Phase 8.4 architecture gate is explicitly approved.

## Required startup behavior

Inspect current HEAD/tag/status and read the Phase 8.3 review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
