# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.28.1 — tenure-bound trusted onboarding recovery and cross-phase security closure
- **Latest milestone tag:** `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01`
- **Latest sealed security maintenance:** Pre-8.29 shutdown/UI ownership, native mutex release and stale recovery-child hardening (local commit/tag; push and workbook pending)
- **Latest maintenance tag:** `nayeon-v1-pre-8-29-shutdown-ownership-native-mutex-maintenance-01`
- **Verified maintenance product commit:** `28b417fe1c97cdcb7f5907ecc0db92e7d3ac6622`
- **Full regression baseline:** **2,249 / 2,249** (staged seal-time and independent isolated postcommit on Windows Python 3.12)
- **Last updated:** 11 Oct 2026
- **Next restart point:** Pre-8.29 shutdown ownership/native mutex release maintenance is locally committed and annotated-tagged, independently reviewed CLEAR, and passed staged plus isolated postcommit full regression 2,249/2,249. Its tag and commit have NOT been pushed or remotely verified; same-ID master workbook update is pending. Obtain explicit push approval and verify remote branch plus peeled tag, then update the master workbook. Re-run the mandatory failure-ledger GO/HOLD review before Phase 8.29, which remains HOLD. No real providers/credentials without separate approval; five-phase batches require per-phase gates.

## Latest architecture invariant

Trusted named mutex held for the entire fresh human-reconciled session; historical READY never grants admission. Bounded nonsecret write-ahead journal must persist/read back IN_FLIGHT before a sensitive effect. Metadata requires typed poststate verification; CONNECT/REPLACE remain uncertain without exact key readback. Candidate-only validation uses one-use operation-bound tickets and cannot execute another window CONNECT/REPLACE. Observer conflicts cannot poison an unowned controller. Full postcommit 2223/2223, zero failures/skips, fake-only Windows acceptance; no real credentials/providers. Metadata UI now requires exact one-use window owner/review ticket/operation/CLEAR consent and path-pooled ownership across hosts; closed callbacks cannot reclaim. Current AGENTS is pinned to exact separately approved governance commit 02f3fb6; prior tags preserved. Pre-8.29 maintenance postcommit 2233/2233 tests, independent review CLEAR. Further recovery-child consent hardening ensures wrong fingerprint rejection cannot consume another tenure and destroyed Tk callbacks are inert. New tagged maintenance commit 4363fd8; remote verified; staged and postcommit 2235/2235; independent read-only review CLEAR. Phase 8 formal closure and 12 release gates remain open.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

Before proposing or starting Phase 8.29 or any future product phase, complete the mandatory **Open Failures & Prior-Issues Review** and record explicit GO/HOLD according to `docs/engineering_failure_review_gate.md`. Include material historical failures, earlier workarounds, architectural dependencies and alternate trusted call paths, even when prior full regressions passed. Resolve material findings, add reproducing tests, independently review and repeat affected/full tests before advancing.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
