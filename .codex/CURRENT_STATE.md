# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.9 - Read-only Provider Credential Reconciliation and Recovery Advice
- **Latest milestone tag:** `nayeon-v1-read-only-connection-reconciliation-recovery-advice-01`
- **Full regression baseline:** **1,943 / 1,943**
- **Last updated:** 9 Oct 2026
- **Next restart point:** Phase 8.10 read-only architecture audit - trusted first-run BYOK setup orchestration and freshness-safe status presentation, partial-failure handling and explicit human authorization boundaries; implementation not approved. Read docs/formal_readiness_assessment_2026-10-09.md first: 5/19 strict phase closures and 0/12 release gates; 72% retired.

## Latest architecture invariant

Phase 8.9 adds exactly connection_reconciliation.py and connection_recovery_advice.py. observe_connection requires explicit native Path and trusted injected availability source, reloads provider metadata freshly, rejects unsupported mappings before probing secrets, checks only canonical openai.api_key presence, re-reads metadata, and returns immutable non-secret point-in-time statuses (setup required, saved key without config, missing key, validation required, unsupported, changed during observation, unknown). Double-read detects some changes but is NOT atomic and does not establish credential validity, service availability or authorization. Recovery advice is pure typed suggestion only: no mutation, automatic retry/repair, credential value read, SDK/native calls, UI or model authority. All 104 Phase 8.8 production Python modules and requirements remain frozen; Phase 8.9 27 focused, 168 affected and 1,943 full tests pass pre/post seal. Product commit ea6d50540f8e0bb759254ce29e4c68033e7334e0, annotated tag nayeon-v1-read-only-connection-reconciliation-recovery-advice-01 pushed/remotely verified. Phase 8 planned BYOK scope remains in progress; 5/19 phase exits and 0/12 release gates unchanged.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
