# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.27 - trusted human-reviewed connect/replace/delete Tk interface
- **Latest milestone tag:** `nayeon-v1-phase-8-27-trusted-credential-management-ui-01`
- **Full regression baseline:** **2,111 / 2,111**
- **Last updated:** 11 Oct 2026
- **Next restart point:** Phase 8.28 trusted provider/model metadata commit, clearing and conservative recovery. Review authority and state conflict boundaries before edits; no live credentials or provider calls without separate approval.

## Latest architecture invariant

Explicit human review, separate single-use approval and destructive delete acknowledgement flow into the Phase 8.26 cooperative single-writer coordinator. Fake-only credential operations and genuine Windows Tk UI tests. Full 2111/2111; no Windows credential store, provider network, external-writer protection or cross-store transaction. Formal 5/19 phases, 0/12 release gates.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
