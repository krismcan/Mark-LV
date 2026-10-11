# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.28.1 — tenure-bound trusted onboarding recovery and cross-phase security closure
- **Latest milestone tag:** `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01`
- **Latest sealed security maintenance:** Pre-8.29 recovery-dialog callback isolation after metadata-owner/governance security maintenance
- **Latest maintenance tag:** `nayeon-v1-pre-8-29-recovery-dialog-lifecycle-maintenance-01`
- **Verified maintenance product commit:** `4363fd8db28188e61533049058f20a45bd70319a`
- **Full regression baseline:** **2,235 / 2,235**
- **Last updated:** 11 Oct 2026
- **Next restart point:** Pre-8.29 metadata owner/governance issues and the stale recovery-child callback have been separately sealed and independently reviewed. Full regression 2,235/2,235. Before Phase 8.29 complete a FRESH mandatory failure-ledger GO/HOLD review, preserve separate scope approvals and do not use live providers or credentials without explicit consent. Five-phase batches require per-phase gates.

## Latest architecture invariant

Trusted named mutex held for the entire fresh human-reconciled session; historical READY never grants admission. Bounded nonsecret write-ahead journal must persist/read back IN_FLIGHT before a sensitive effect. Metadata requires typed poststate verification; CONNECT/REPLACE remain uncertain without exact key readback. Candidate-only validation uses one-use operation-bound tickets and cannot execute another window CONNECT/REPLACE. Observer conflicts cannot poison an unowned controller. Full postcommit 2223/2223, zero failures/skips, fake-only Windows acceptance; no real credentials/providers. Metadata UI now requires exact one-use window owner/review ticket/operation/CLEAR consent and path-pooled ownership across hosts; closed callbacks cannot reclaim. Current AGENTS is pinned to exact separately approved governance commit 02f3fb6; prior tags preserved. Pre-8.29 maintenance postcommit 2233/2233 tests, independent review CLEAR. Further recovery-child consent hardening ensures wrong fingerprint rejection cannot consume another tenure and destroyed Tk callbacks are inert. New tagged maintenance commit 4363fd8; remote verified; staged and postcommit 2235/2235; independent read-only review CLEAR. Phase 8 formal closure and 12 release gates remain open.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

Before proposing or starting Phase 8.29 or any future product phase, complete the mandatory **Open Failures & Prior-Issues Review** and record explicit GO/HOLD according to `docs/engineering_failure_review_gate.md`. Include material historical failures, earlier workarounds, architectural dependencies and alternate trusted call paths, even when prior full regressions passed. Resolve material findings, add reproducing tests, independently review and repeat affected/full tests before advancing.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
