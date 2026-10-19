# Phase 8.36 — Offline Prompt Review (release-candidate RFC)

Status: **LOCAL CANDIDATE, UNSEALED; no live AI**. Reviewed architecture: design v0.5; independently reviewed source A and B. Sealed parent `b0490cd9e72104a74a32dc5315cbc55bc4034676`. Do not claim GitHub product release without exact seal.

## User-visible change

The existing Conversation window adds "Review offline prompt", "Confirm offline review" and "Cancel review". The disclosed prompt is never sent. The fixed result is `REVIEWED OFFLINE - NO AI REQUEST OR ACTION WAS SENT.` and carries no provider, network, filesystem, action or future transmission permission. There is no model connection, no credential resolution and no network call in this feature. Existing offline Save, simulated reply, reset and navigation remain distinct.

## Boundary

The pure owner has only primitive exact prompt, opaque root/pane/session identity, generation/epoch/revision and monotonic (30-second) deadline. App only supplies immutable current `SessionSnapshot` while the physical worker/reply owner is idle. Review UI final enabled-state observation is **the last Tcl seam** before pure creator-thread arming. Nested callback, changed prompt, reset, navigation, destroy, worker admission, expiry and uncertain Tk publishing state poison the proposal. Confirmation consumes a one-use ticket *before* effects; nested cancellation wins; stale success is cleared or hidden independently if cleanup widget operations fail.

The owner does not prove a hardware-originated human gesture against arbitrary malicious code in the same Python process. Review ticket is not real outbound authorisation. Future live AI phase needs separately reviewed provider-store freshness, human consent for transmission and credentials/adapters.

## Exact scope

Eight NEW and eleven MODIFIED paths specified in `tests/phase_8_36_scope_migration.py` and previously reviewed design PR #1. Historical 8.34 annotated tag, exact sealed full tree, prior source bytes and earlier fault injection gates remain immutable. A standalone candidate on the sealed parent may be `COMPLETE_UNSTAGED`, `EXACT_STAGED` or `EXACT_CHILD` only if every candidate byte and Git delta matches its pinned manifest. No manual bypass or wildcard.

## Required release gates

Independent Increment C source/security review, historical guard tests and original affected/focused native Windows tests; three authoritative full Windows regressions pre-stage/staged/postcommit, exact Git staging and code/tag verification, nonforce GitHub push, original same-ID Google Drive workbook update/readback and sanitised dashboard. Stop on any failed check. Do not merge review PRs as a shortcut.
