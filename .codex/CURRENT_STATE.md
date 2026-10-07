# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.2 - Bound Secret Resolver & OpenAI Provider Migration
- **Latest milestone tag:** `nayeon-v1-bound-secret-resolver-openai-provider-migration-01`
- **Full regression baseline:** **1,707 / 1,707**
- **Last updated:** 7 Oct 2026
- **Phase 7 status:** User Identity & Configuration **FOUNDATION COMPLETE**
- **Phase 8 status:** Secure Secrets & BYOK **IN PROGRESS**
- **Next restart point:** Phase 8.3 - Architecture audit for bounded credential lifecycle and typed provider connection configuration; scope not yet approved

## Latest architecture invariant

Phase 8.2 introduces a least-authority `BoundSecretResolver` that privately binds one `SecretBackend` to one exact immutable `SecretIdentifier` and publicly exposes only safe identifier metadata plus resolution of that one credential. It has no public backend access, put/delete/is_available, enumeration, rebinding or arbitrary-identifier API. Unexpected backend failures are converted to a fixed safe `SecretStorageError`, and the resolver retains no resolved `SecretValue`.

`OpenAIProvider` has been migrated completely away from the legacy environment-backed `SecretStore`. It accepts only an exact `BoundSecretResolver` bound to `openai.api_key`, resolves lazily only when constructing the OpenAI client, reveals plaintext only at that SDK boundary, stores neither `SecretValue` nor plaintext itself, and releases its resolver authority after successful client creation. Provider-construction failures are surfaced only as fixed `OpenAIProviderInitializationError("OpenAI provider initialization failed")` with the underlying exception chain suppressed. On resolution or constructor failure, no client is cached and resolver authority is retained for retry.

The legacy `nayeon/secrets/store.py` remains unchanged but now has **zero production consumers**. `WindowsCredentialBackend` remains provider-neutral with **zero direct production consumers**. Only `nayeon/secrets/resolver.py` imports the `SecretBackend` authority contract, and only `nayeon/brain/providers/openai.py` consumes `BoundSecretResolver`. Secrets remain separate from presentation configuration, generic settings, prompts/model context, memory, audit/log output, capability identity and trusted action/security authority.

Independent validation passed 26/26 dedicated Phase 8.2 tests, 174/174 combined Phase 7 + Phase 8 suites, 306/306 affected configuration/secrets + trust/orchestration tests and 1,707/1,707 full regression. No native Credential Manager mutation or real OpenAI network call was required in Phase 8.2; the unchanged Phase 8.1 native backend was already proven separately.

## Next architecture question

Phase 8.3 should define the bounded credential lifecycle and typed provider-connection configuration needed for BYOK onboarding: connect/store, validate/test, replace and remove a provider credential while keeping raw secret values out of UI read models, generic settings, logs, audit details, prompts/model context and memory. It should also decide the typed non-secret provider/model connection configuration that can refer to a credential identity without exposing credential contents. Do not add onboarding UI, runtime/application composition, provider-selection UX, plaintext persistence, environment fallback, broad secret enumeration or additional provider implementations until that architecture gate is explicitly approved.

## Required startup behavior

Inspect current HEAD/tag/status and read the Phase 8.2 review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
