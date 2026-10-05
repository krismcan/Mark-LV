# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 7.2 - Strict Versioned Presentation Configuration Document & Pure Schema Codec
- **Latest milestone tag:** `nayeon-v1-presentation-configuration-document-01`
- **Full regression baseline:** **1,563 / 1,563**
- **Last updated:** 5 Oct 2026
- **Next restart point:** Phase 7.3 - Architecture audit for a bounded configuration persistence/migration boundary; scope not yet approved

## Latest architecture invariant

PresentationConfigurationDocumentV1 is the sealed presentation-scoped schema-v1 aggregate: exact built-in mappings and keys only, no coercion, fresh canonical encoding, and no presentation value may alter capability identity, policy, permissions, confirmation, audit identity, execution authority, trusted object identity, or secrets; persistence, migration, and runtime wiring remain unapproved.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
