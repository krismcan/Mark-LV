# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.4 - OpenAI Credential Validation & Canonical Client Routing
- **Latest milestone tag:** `nayeon-v1-openai-credential-validation-canonical-routing-01`
- **Full regression baseline:** **1,774 / 1,774**
- **Last updated:** 7 Oct 2026
- **Phase 7 status:** User Identity & Configuration **FOUNDATION COMPLETE**
- **Phase 8 status:** Secure Secrets & BYOK **IN PROGRESS**
- **Next restart point:** Phase 8.5 - Architecture audit for typed provider-connection ownership/persistence; scope not yet approved

## Latest architecture invariant

Phase 8.4 introduces one shared OpenAI SDK construction boundary and one provider-specific credential validator.

`nayeon/brain/providers/openai_client.py` owns canonical OpenAI API-key client construction. It:
- requires exact `SecretValue`;
- reveals the credential only inside the SDK-construction boundary;
- lazily imports the pinned OpenAI SDK at client-construction time;
- pins `https://api.openai.com/v1`;
- constructs `DefaultHttpxClient(trust_env=False, follow_redirects=False)`;
- supplies an explicit Authorization header derived from the selected Nayeon credential;
- accepts only bounded timeout/retry overrides;
- exposes no caller-selected endpoint, proxy, header, transport, organization/project or HTTP client;
- sanitizes ordinary SDK/client-construction failures to fixed `OpenAIClientConstructionError("OpenAI client construction failed")`;
- performs best-effort HTTP-client cleanup if SDK construction fails.

`OpenAIProvider` no longer imports the OpenAI SDK directly and no longer calls `.reveal()`. It delegates its exact resolved `SecretValue` to `create_openai_client`, preserving all sealed Phase 8.2 authority rules: exact `openai.api_key` resolver binding, lazy resolution, resolver retention on failed construction, client caching on success, and resolver authority release after successful construction.

`OpenAICredentialValidator` is stateless and uses the shared factory with timeout 5.0 seconds and max_retries 0. It makes exactly one `client.models.list()` call without inspecting the returned model data. Successful request + cleanup => VALID. Ordinary construction/request/cleanup failures => INDETERMINATE. INVALID is deliberately unused in this adapter because authentication-shaped failures can also represent organization membership, endpoint permission, IP allowlist or other access conditions. Process-control exceptions are not swallowed.

The validator imports only the sealed non-authority `CredentialValidationStatus` enum from `nayeon.secrets.lifecycle`; it does not consume `BoundCredentialLifecycle`, backend authority or the CredentialValidator Protocol itself.

`requirements.txt` now contains the exact active pin `openai==3.26.0`. The authoritative host was intentionally not modified to install the SDK during Phase 8.4; deterministic tests use fake SDK/client seams. Clean installs now have an explicit runtime dependency declaration.

All prior Phase 8.1-8.3 production boundaries remain frozen:
- `BoundCredentialLifecycle` production consumers: **0**
- `ProviderConnectionConfiguration` production consumers: **0**
- `BoundSecretResolver` consumer: **OpenAIProvider only**
- legacy `SecretStore` consumers: **0**
- direct `WindowsCredentialBackend` consumers: **0**
- `OpenAICredentialValidator` consumers: **0**
- `create_openai_client` consumers: exactly OpenAIProvider + OpenAICredentialValidator

Independent validation passed 42/42 focused Phase 8.4 tests, 241/241 combined Phase 7 + Phase 8 suites, 373/373 affected configuration/secrets + trust/orchestration tests, and 1,774/1,774 full regression. compileall and diff checks passed. No OpenAI SDK installation, real API key, real OpenAI request, environment mutation or native Credential Manager mutation was performed.

## Next architecture question

Phase 8.5 should define the smallest safe ownership/persistence boundary for the existing non-secret `ProviderConnectionConfiguration` contract.

The audit should decide:
1. an immutable schema/document contract for optional provider/model/credential-identifier configuration;
2. strict persistence/codec rules with bounded file size, duplicate-key rejection and atomic replace;
3. one application service that owns the current immutable connection document with persist-before-swap semantics;
4. first-run/unconfigured state, replace/clear behavior and fixed safe errors;
5. how future trusted composition verifies provider-to-credential identity independently before constructing a resolver/provider.

Preserve separation between:
- presentation/user identity configuration;
- non-secret provider connection metadata;
- secure credential lifecycle/storage;
- one-secret provider resolution;
- provider credential validation;
- runtime/application composition.

Do not add onboarding UI/read models, runtime composition, provider/model selection UX, generic settings, plaintext secret persistence, environment fallback, broad secret enumeration, additional providers or actual provider wiring until the Phase 8.5 architecture gate is explicitly approved.

## Required startup behavior

Inspect current HEAD/tag/status and read the Phase 8.4 review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
