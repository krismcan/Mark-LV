# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.14 - Pure Canonical OpenAI Onboarding Metadata Change Preview
- **Latest milestone tag:** `nayeon-v1-pure-openai-onboarding-metadata-change-preview-01`
- **Full regression baseline:** **1,970 / 1,970**
- **Last updated:** 9 Oct 2026
- **Next restart point:** Phase 8.14 closed; the authorized 8.10-8.14 series is complete. Next product phase requires explicit scope/approval, beginning with fresh architecture audit; no automatic credential or persistence authority.

## Latest architecture invariant

Phase 8.14 introduces one pure immutable change-preview module: exact typed proposal and matching metadata preview are compared against a caller-supplied exact typed current connection document. CREATE/UNCHANGED/MODEL_CHANGE are informative only; unsupported current metadata is refused. No reads, writes, SDK, credentials, real consent, or model-selectable route. Reobserve and explicitly authorize in a future trusted host flow. 110/110 affected security tests and 1,970/1,970 pre/post-commit full regressions pass; product annotated tag pushed and peeled verified. Five authorized engineering phases 8.10-8.14 are closed, but strict readiness remains 5/19 planned phase exits and 0/12 end-user release gates.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
