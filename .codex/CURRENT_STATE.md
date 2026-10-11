# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.28.1 — tenure-bound trusted onboarding recovery and cross-phase security closure
- **Latest milestone tag:** `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01`
- **Latest locally sealed maintenance:** Pre-8.29 fake-only native cleanup exceptions and reentrant real-Tk approval-destruction regression hardening (no production modifications; not pushed)
- **Latest local maintenance tag:** `nayeon-v1-pre-8-29-final-fault-injection-maintenance-01`
- **Latest local maintenance commit:** `6cb0e702cab9532c8fc1a46491182b8c9c30feda` (annotated tag; remote push NOT authorised)
- **Full regression baseline:** **2,256 / 2,256** (staged seal-time and isolated postcommit; Windows Python 3.12)
- **Last updated:** 11 Oct 2026
- **Next restart point:** Pre-8.29 shutdown/mutex maintenance is pushed: remote branch db8f5ce224f4677f4bc5050939a943c2a7142a08 and peeled annotated tag 28b417fe1c97cdcb7f5907ecc0db92e7d3ac6622 independently verified. Same-ID master Drive workbook 1n0tDiBQCkPWluX6eakRiRfq57tflRW5L updated in place; preserve 5/19 planned phase and 0/12 release-gate readiness figures. Completed LOCAL test hardening: seven new tests passed, 82 affected passed, independent read-only Codex Sol High CLEAR, 2,256/2,256 staged and postcommit full passed. Commit 6cb0e702cab9532c8fc1a46491182b8c9c30feda is locally annotated-tagged and UNPUSHED. Previous shutdown/mutex repair at 28b417f remains remotely tagged/verified under branch db8f5ce; same-ID master workbook was updated for that prior seal. Do not push this new maintenance tag/branch without separate explicit approval. Phase 8.29 remains HOLD and requires new GO/HOLD + user authorisation. No live providers or credentials. Phase 8.29 remains HOLD; do not push or start new phase without fresh approval. No real providers/credentials; five-phase batches require per-phase gates.

## Latest architecture invariant

Trusted named mutex held for the entire fresh human-reconciled session; historical READY never grants admission. Bounded nonsecret write-ahead journal must persist/read back IN_FLIGHT before a sensitive effect. Metadata requires typed poststate verification; CONNECT/REPLACE remain uncertain without exact key readback. Candidate-only validation uses one-use operation-bound tickets and cannot execute another window CONNECT/REPLACE. Observer conflicts cannot poison an unowned controller. Full postcommit 2223/2223, zero failures/skips, fake-only Windows acceptance; no real credentials/providers. Metadata UI now requires exact one-use window owner/review ticket/operation/CLEAR consent and path-pooled ownership across hosts; closed callbacks cannot reclaim. Current AGENTS is pinned to exact separately approved governance commit 02f3fb6; prior tags preserved. Pre-8.29 maintenance postcommit 2233/2233 tests, independent review CLEAR. Further recovery-child consent hardening ensures wrong fingerprint rejection cannot consume another tenure and destroyed Tk callbacks are inert. Prior tagged recovery-child maintenance 4363fd8 was remotely verified at 2235/2235. Maintenance commit 28b417f and annotated tag remotely verified; 2249/2249 staged and isolated postcommit regressions. Exact root-destruction cleanup and owner-scoped release prevent stranded/transferred tenures; uncertain Win32 mutex release stays latched. Same-ID master Drive workbook updated. Final adversarial test-only hardening independently reviewed CLEAR, with 7/7 new tests, 82/82 affected, and 2256/2256 staged plus isolated postcommit regressions. Latest local maintenance tag at 6cb0e70 remains unpushed; previous shutdown/mutex tag at 28b417f and origin/nayeon-v1 db8f5ce are remotely verified. Phase 8 and its 12 release gates remain open. Phase 8 formal closure and 12 release gates remain open.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

Before proposing or starting Phase 8.29 or any future product phase, complete the mandatory **Open Failures & Prior-Issues Review** and record explicit GO/HOLD according to `docs/engineering_failure_review_gate.md`. Include material historical failures, earlier workarounds, architectural dependencies and alternate trusted call paths, even when prior full regressions passed. Resolve material findings, add reproducing tests, independently review and repeat affected/full tests before advancing.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
