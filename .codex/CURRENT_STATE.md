# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.17 - Single Pending Host-owned Human Onboarding Review
- **Latest milestone tag:** `nayeon-v1-phase-8-17-host-review-session-01`
- **Full regression baseline:** **1,998 / 1,998**
- **Last updated:** 10 Oct 2026
- **Next restart point:** Phase 8.18: strictly bounded trusted-operation host adapter injected with an exact credential lifecycle and a fresh state observer, fake-backend tests only. Do not create model-callable credential routes, ambient key lookup, cross-store atomic claims or real user approval.

## Latest architecture invariant

Phase 8.17 adds one host-only, single-use in-memory review state machine; approvals, rejection and expiry are in-process events, retain no credential candidate, and yield non-authorizing receipts. 48 focused and 1998 full pre/post tests pass. Formal readiness remains 5/19 and 0/12.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
