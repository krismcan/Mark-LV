# Phase 8.36 independent design and scope rereview (v0.3)

**Requested:** separate independent `DESIGN_GO/HOLD` and `SCOPE_GO/HOLD` on the amended `docs/reviews/phase_8_36_consent_design.md`, against exact sealed Phase 8.34 parent. This is a **draft docs-only PR**; no source/tests have been integrated or product release approved. **Do not merge.**

## First Codex code-review findings addressed in DESIGN, not yet signed off

1. **P1 Git seal concern:** Exact remote Git API refs demonstrate annotated tag object `b503ce088ee4a787990534ea862be2936fa55767` exists and peels to protected HEAD `b0490cd9e72104a74a32dc5315cbc55bc4034676`. Historical 8.34 committed review docs/tag message contain stale PRESEAL notes; separately verify postcommit evidence rather than infer tag absence. No historical Git objects are changed.
2. **P1 external writer A→B→A:** Synthetic Windows repro confirmed cached A remains identical after a *different store owner* writes B→A on disk. v0.3 expressly narrows prototype guarantee to **cached informational metadata only**, never remote freshness, eligibility for live transmission or proven user consent. Future live phase requires separately reviewed shared multi-writer revision/lock/equivalent mutation detection. If unsupported, HOLD send.
3. **P1 latent provider authority:** v0.3 bans lazy composer, `AIService`, OpenAI provider/resolver/client, SDK loader, secret handling, socket/network and actions even **before generate()**. Add construction and reachability tripwires.
4. **P2 disclosure-before-confirm:** v0.3 mandates distinct UNARMED/presentation/ARMED phases and a fresh single-use ticket only after complete visible disclosure and final eligibility check; nested Confirm mid-render always refuses.
5. **P2 human callback:** v0.3 specifies exact root-owned current widget/callback ingress and explicitly rejects any claim that `human_clicked=True` or Tk `.invoke()` proves a physical human against same-process compromise. First increment is OFFLINE only; future live consent needs its own reviewed authority.

## Recheck obligations

- Read current committed `application.py`, `workspace_window.py`, all relevant provider/connection sources and Phase 8.30–8.34 history/source/tag/index/disk guard source directly. Do not rely on our summary.
- For each finding, report `OPEN/CLOSED/NEEDS_EVIDENCE`, severity, exact file/line, causal problem, required design changes and negative tests.
- Confirm exact changed-file envelope for a first **pure no-network** increment vs separate actual native Tk integration; do not allow wildcard historical scope migration.
- Decide if an offline user-visible review without real send is sufficient milestone value. Do not sign off consumer release or model connection just from an informational review.
- If no unresolved HIGH/MEDIUM and all new invariants are adequate, issue `DESIGN_GO`; separately define `SCOPE_GO` or HOLD. Otherwise clearly HOLD.

External off-repository research tests: 170 baseline; 65 combined candidate; 1,129 prompt equivalence; a deliberate stale-cache A→B→A repro. These are **not published production tests**, not a security review and not three full Windows release gates.

**Protected branch remains at Phase 8.34**; Phase 8.36 product OPEN, proposed batching from 8.35 HOLD, no live AI/credential/network effects.

## Second Codex rereview findings on v0.2 — explicitly addressed in v0.3 design only

- **P2 enable-seam race:** v0.3 says enable the Tk Confirm widget **while the owner is UNARMED**. Any nested Confirm call during enable poisons the preview. Only after `configure(state=normal)` has returned and a final state check passes may the creator thread perform **callback-free pure arming**. Direct test must synchronously invoke the stored Confirm callback from the `configure` enable seam and demonstrate refusal plus no late arm.
- **P2 writable metadata graph:** v0.3 removes `ProviderConnectionService` and `ProviderConnectionFileStore` and any closure-backed observer from the review owner/renderer. A trusted external composition seam extracts **immutable informational display values only** and hands those strict values to the review. The owner must not even indirectly retain file-write authority. Direct graph-reachability test supplies service/store/writable wrapper and refuses. Future transmission needs a separate full review and freshness solution.
- The old synthetic A→B→A on-disk reproduction is not a solved freshness claim; the first increment only displays a potentially stale advisory snapshot. Its receipt is explicitly **non-authorising**.

**Please rereview the precise v0.3 design changes** and return distinct DESIGN_GO/HOLD and SCOPE_GO/HOLD. No user-facing feature is yet integrated or approved by this doc. All historical/protected regressions and original same-ID workbook/dashboard gates remain untouched.
