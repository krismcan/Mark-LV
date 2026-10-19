# Phase 8.36 — v0.5 final-Tk-seam amendment

**Design review only.** Authoritative amendment to v0.4's step 4–5. The first four paragraphs of v0.4 still define intent and constraints; where the ordering conflicts, this amendment is controlling. The protected product remains Phase 8.34. This is not an implementation or merge approval.

## One remaining v0.4 finding

Independent Codex reviewed commit c2381b7eb63d6ac9aabb51103fdb3c9939b07779 and gave **SCOPE_GO** to exactly 19 paths, but **DESIGN_HOLD** for an enabled-state observation that could become stale after a subsequent Tcl liveness/prompt read.

## Corrected admission sequence

The current review owner remains **UNARMED**, with the Confirm button disabled, throughout rendering, enabling, and all subsequent Tk queries.

1. Render and verify the full literal no-send disclosure.
2. Enable Confirm; if a nested callback occurs or the command raises, revoke.
3. Still UNARMED, complete **all** necessary potentially reentrant Tk reads. That includes root/pane existence, current-view checks, current entry text, disclosure widget text and any other application helper that calls Tk. After each read, check current identity, session and poisoned state. On uncertainty, revoke.
4. As the **last and final Tk operation**, call the bound current Confirm widget's enabled-state query. Its result must report enabled. Reentrant Cancel, Reset, Destroy or Confirm during the query poisons the proposal.
5. **After that query, perform only Python-only, callback-free exact identity and poison checks, immediately followed by a pure one-use ticket arm.** No Tk calls, event-loop yields, `_current()`, `view.exists()`, `winfo_exists()`, `entry.get()`, `cget()`, user callbacks or UI publications between the final enabled observation and the pure arm. No caller-provided boolean counts as proof of widget state.
6. A separate, later valid Confirm consumes the ticket before UI publication; existing session invalidation and zero-transmission restrictions still apply.

## Required new negative test

The last potentially reentrant Tk liveness or prompt query should be instrumented to disable Confirm silently while returning the expected text/identity. Under v0.5, the **subsequent final enabled-state query sees the disabled button** and must refuse to arm. A second test must assert via an instrumented Tk call ledger that the enabled-state observation is the **last Tcl operation** preceding the pure ticket-arm transition. Retain v0.4's normal-return-but-disabled Configure, nested confirmation, and disclosure-fault canaries.

## Scope and gates

No change to the exact 19 allowed source/test/doc paths in v0.4; specifically preserve **SCOPE_GO** for those paths only. No live model calls, secrets, external transmission or desktop actions. No user-visible feature has yet been integrated. Request independent **DESIGN_GO/HOLD** for this exact corrected ordering and confirmation of unchanged **SCOPE_GO**. All established staged/full Windows regressions, independent source review, immutable tag and original same-ID workbook/dashboard publication requirements remain mandatory.
