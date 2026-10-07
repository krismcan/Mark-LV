# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.1 - Secure Secret Contract & Windows Credential Storage Foundation
- **Latest milestone tag:** `nayeon-v1-secure-secret-windows-credential-storage-01`
- **Full regression baseline:** **1,681 / 1,681**
- **Last updated:** 7 Oct 2026
- **Phase 7 status:** User Identity & Configuration **FOUNDATION COMPLETE**
- **Phase 8 status:** Secure Secrets & BYOK **IN PROGRESS**
- **Next restart point:** Phase 8.2 - Architecture audit for bounded secret ownership/resolution and OpenAI provider migration; scope not yet approved

## Latest architecture invariant

Phase 8.1 adds a provider-neutral secure-secret foundation without changing any existing production consumer. `SecretIdentifier` is safe metadata, `SecretValue` is an opaque redacted holder with one explicit plaintext reveal boundary, and `SecretBackend` exposes only exact get/put/delete/is_available operations. `WindowsCredentialBackend` stores only Nayeon-namespaced Generic Credentials under `nayeon-v1/secret/<identifier>` using Windows Credential Manager with local-machine persistence for the current Windows user, strict UTF-8 blobs, the 2,560-byte limit, fixed safe error messages, no enumeration and no arbitrary-target API.

The existing environment-backed `nayeon/secrets/store.py` and `OpenAIProvider` remain frozen and unchanged; OpenAIProvider remains the sole production consumer of the legacy SecretStore. The new contracts/backend have no production consumers yet. Secrets remain separate from presentation configuration, generic settings, prompts/model context, memory, audit/log output, capability identity and trusted action/security authority.

Independent validation passed 36/36 dedicated Phase 8.1 tests, 148/148 Phase 7 + Phase 8.1 suites, 280/280 affected configuration/secrets + trust/orchestration tests and 1,681/1,681 full regression. A controlled disposable native Windows Credential Manager smoke passed absent -> put -> available -> exact Unicode round-trip -> delete -> absent, with cleanup confirmed and no real provider credential used.

## Next architecture question

Phase 8.2 should define the smallest secure ownership/resolution boundary that allows provider code to obtain one exact secret while preventing UI, model, memory, audit and generic runtime components from receiving raw secret authority. It should also decide the bounded migration of `OpenAIProvider` away from the legacy environment `SecretStore` without introducing provider selection, onboarding UI, plaintext persistence, environment fallback, or broad secret enumeration. Scope is not yet approved.

## Required startup behavior

Inspect current HEAD/tag/status and read the Phase 8.1 review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
