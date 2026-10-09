# Phase 8.11 — Pure Canonical OpenAI Configuration Proposal

**Scope:** `onboarding_configuration_proposal.py` and its deterministic
tests. The proposal carries a validated model string, fixed `openai` provider
identity, a provenance *display state*, and the requirement to reobserve.

This phase introduces **no** `ProviderConnectionService.replace` call,
provider SDK, config/credential file I/O, credential read/write, real provider
model check, UI or agent authority. A syntactically valid model name is not
evidence of model entitlement. Only explicit later permissioned operations
could persist metadata, after a separate fresh observation.
