# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.26 - cooperative onboarding lock, state conflict detection and manual recovery marker
- **Latest milestone tag:** `nayeon-v1-phase-8-26-cooperative-onboarding-coordination-01`
- **Full regression baseline:** **2,091 / 2,091**
- **Last updated:** 11 Oct 2026
- **Next restart point:** Phase 8.27 trusted human-approved credential save replace delete UI, subject to new bounded scope audit. Do not use live credentials or real provider calls without separate consent. Phase 8 and all release gates remain open.

## Latest architecture invariant

Cooperating Nayeon Windows-session processes share one Local named mutex for execution; pre- and post-effect metadata identity observations fail closed; interrupted or indeterminate writes retain non-secret recovery marker. No external-writer exclusion, credential CAS, cross-store atomicity, key reads or model-authority route. 2091/2091 full postcommit; formal phases 5/19, gates 0/12.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
