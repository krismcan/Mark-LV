# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.8 - Trusted OpenAI Credential Onboarding Composition and Explicit Operations
- **Latest milestone tag:** `nayeon-v1-trusted-credential-onboarding-explicit-operations-01`
- **Full regression baseline:** **1,916 / 1,916**
- **Last updated:** 9 Oct 2026
- **Next restart point:** Phase 8.9 architecture audit - explicit credential/metadata reconciliation, failure recovery, freshness-safe status presentation and trusted onboarding integration; implementation not approved Read `docs/formal_readiness_assessment_2026-10-09.md` before planning; 5/19 formally closed phases and 0/12 verified end-user release gates. Old 72% is retired.

## Latest architecture invariant

Phase 8.8 adds credential_onboarding.py and credential_onboarding_composition.py only. Trusted caller injects SecretBackend; composition binds BoundCredentialLifecycle to exact SecretIdentifier('openai.api_key') and sealed OpenAICredentialValidator without backend, SDK or network activity on construction. Explicit is_connected, test_candidate, test_stored, connect, replace and remove delegate to sealed lifecycle; candidate is persisted only after VALID and availability recheck. INVALID/INDETERMINATE never saved; provider probe failures are INDETERMINATE, not proof of a bad key. Fixed safe errors; no public agent/UI/runtime wiring or provider-metadata coupling. 102 previous production modules and requirements byte frozen; 36 focused, 274 affected, 1916 full tests PASS at seal and postcommit. Product commit eeb85d5e85fefa6abb37cfedef6c956954b41a0b and annotated tag nayeon-v1-trusted-credential-onboarding-explicit-operations-01 pushed and remotely verified. Next architecture audit and implementation require separate approval.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
