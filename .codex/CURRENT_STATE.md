# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.28.1 — tenure-bound trusted onboarding recovery and cross-phase security closure
- **Latest milestone tag:** `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01`
- **Full regression baseline:** **2,223 / 2,223**
- **Last updated:** 11 Oct 2026
- **Next restart point:** Phase 8.29 remains gated on same-ID master workbook update and renewed explicit scope approval before any live credentials/provider calls. Conduct conditional integrated first-run acceptance with separate consent.

## Latest architecture invariant

Trusted named mutex held for the entire fresh human-reconciled session; historical READY never grants admission. Bounded nonsecret write-ahead journal must persist/read back IN_FLIGHT before a sensitive effect. Metadata requires typed poststate verification; CONNECT/REPLACE remain uncertain without exact key readback. Candidate-only validation uses one-use operation-bound tickets and cannot execute another window CONNECT/REPLACE. Observer conflicts cannot poison an unowned controller. Full postcommit 2223/2223, zero failures/skips, fake-only Windows acceptance; no real credentials/providers. Phase 8 formal closure and 12 release gates remain open.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
