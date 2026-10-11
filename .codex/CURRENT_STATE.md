# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.28 - expiring trusted metadata confirmation and cooperative save/clear with conservative recovery
- **Latest milestone tag:** `nayeon-v1-phase-8-28-trusted-metadata-confirmation-01`
- **Full regression baseline:** **2,142 / 2,142**
- **Last updated:** 11 Oct 2026
- **Next restart point:** Phase 8.29 conditional integrated first-run acceptance. Review normal-user consent, live credential/provider testing approval, packaging and release gates before attempting. No live credentials, native credential store or provider calls without explicit separate approval.

## Latest architecture invariant

Canonical OpenAI provider/model metadata save and metadata-only clear require separate expiring single-use human approval. Shared Phase 8.26 Windows-session mutex and recovery marker, pre/post typed state checks. 2142/2142 full postcommit, fake-only keys and real Windows Tk fake callbacks. No external-writer CAS, cross-store transaction or provider entitlement. Formal 5/19 phases, 0/12 gates.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
