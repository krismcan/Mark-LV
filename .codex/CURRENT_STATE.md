# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 7.5 - Bounded Presentation Configuration Bootstrap Composition
- **Latest milestone tag:** `nayeon-v1-presentation-configuration-bootstrap-composition-01`
- **Full regression baseline:** **1,625 / 1,625**
- **Last updated:** 7 Oct 2026
- **Next restart point:** Phase 7.6 - Architecture audit for a bounded presentation-configuration consumer boundary / read-only presentation view; scope not yet approved

## Latest architecture invariant

Presentation configuration now has a strict dependency-ordered stack: immutable presentation contracts -> strict schema-v1 document -> bounded explicit-Path file store -> process-local configuration owner -> one tiny explicit-path bootstrap composition seam. The bootstrap constructs exactly one store and one service, initializes once, and returns that initialized service; it derives no path, has no production consumer, and introduces no runtime/container authority. Persistence load/save ownership remains in the service layer. Legacy ConfigService, trusted action identity, permissions/policy, secrets, Voice/Proactive behavior, model/runtime wiring and root MARK remain outside the boundary.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
