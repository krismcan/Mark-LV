# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.21 - Explicit read-only first-run refresh
- **Latest milestone tag:** `nayeon-v1-phase-8-21-readonly-first-run-refresh-01`
- **Full regression baseline:** **2,030 / 2,030**
- **Last updated:** 10 Oct 2026
- **Next restart point:** Phase 8.22: bounded human-driven first-run status window; no live credential activation and no automatic startup

## Latest architecture invariant

One injected status observation per explicitly requested refresh; reentrant and bad reads fail closed. No secret access or mutations. 2030/2030 full regressions pre and post seal; formal 5/19 phase exits, 0/12 release gates.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
