# Phase 8.12 — Pure typed canonical connection-document preview

`compose_onboarding_metadata_document(OpenAIConfigurationProposal)`
builds exactly one new immutable schema-v1 `ProviderConnectionDocumentV1`
containing provider `openai`, the selected syntactically validated model,
and the non-secret canonical `openai.api_key` reference.

No credential data, config file writes, provider construction, user
confirmation, entitlement checks, or runtime/UI path. A preview does not
authorize `ProviderConnectionService.replace`; a trusted future flow must
freshly recheck all state and secure real consent.

Test plan: strict type, canonical codec, fresh instances, no storage writes,
import/source authority guard and full regression.
