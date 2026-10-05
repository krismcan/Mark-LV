# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 7.1 - Typed Presentation Identity & Preference Contracts
- **Latest milestone tag:** `nayeon-v1-presentation-identity-contracts-01`
- **Full regression baseline:** **1,547 / 1,547**
- **Last updated:** 5 Oct 2026
- **Next restart point:** Phase 7.2 - Versioned Strict Presentation Configuration Document & Pure Schema Codec

## Current subsystem status

- Trusted Core / orchestration foundation: established and protected.
- OpenApp reference: complete.
- Filesystem v1: complete.
- Computer Control v1 foundation: **complete and frozen** at the Phase 6 trust contract.
- User Identity / Configuration: Phase 7.1 complete; presentation contracts exist but are not persisted or wired into runtime yet.
- Memory, Voice, Vision, Browser, Proactive/Events, Desktop UI, Packaging: later roadmap work.

## Latest architecture invariant

Presentation identity is not trusted security/action identity.

`AssistantPresentationIdentity` defaults to **Nayeon** for display and wake name, but users may rename it. A rename must not change capability identity, permission/policy decisions, confirmation binding, audit action identity, execution authority, or trusted object identity.

Legacy `nayeon/config/config.py` is intentionally isolated and is not the authoritative Phase 7 model.

## Phase 7.2 direction

Design a strict, versioned, non-secret presentation configuration document and pure mapping codec.

Expected direction:
- schema version 1;
- compose the Phase 7.1 presentation contracts;
- exact-key / no-coercion parsing;
- reject unknown, missing, malformed, or unsupported-version documents;
- pure mapping -> typed document and typed document -> fresh canonical mapping;
- no file I/O or JSON persistence yet;
- no migration yet;
- no permission defaults, secrets, Voice listening toggles, Proactive toggles, or arbitrary settings dictionary;
- legacy ConfigService remains untouched until a separately approved migration/persistence phase.

## Close-out rule

When the next product phase is sealed, update this file as part of that phase close-out using `scripts/update_codex_context.py` (or an equivalent exact edit) before the next Codex implementation session.
