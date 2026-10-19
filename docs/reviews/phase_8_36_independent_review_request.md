# Phase 8.36 — Independent review request

**Decision needed:** independent `DESIGN_GO / HOLD` and separately `SCOPE_GO / HOLD`. Review must be based on direct current committed source, not previous assistant summaries.

This is a **draft review-only PR**. It adds documentation without changing production code, tests, Git release tags, prior seals, original Drive workbook or dashboard. **Do not merge** until the established release process explicitly authorises a product change.

## Instructions to reviewer

1. Review `docs/reviews/phase_8_36_consent_design.md`, exact Phase 8.34 parent `b0490cd9e72104a74a32dc5315cbc55bc4034676`, and the source paths in that design.
2. Challenge the **actual human gesture** assertion. A `human_clicked=True` flag is not proof; document concrete Tk source ingress and callback identity checks.
3. Challenge the provider metadata assumption. Cached metadata/READY_FOR_COMPOSITION is not a real credential, model availability or permission. Identify any path that might compose the provider or resolve secrets.
4. Challenge review-ticket authority, exact prompt bytes, changed session/pane/generation and A→B→A identical provider configuration replacement. Confirm receipt is non-authorising to future network calls/actions.
5. Reproduce or reason about Tk nested before/after-effect callbacks, Reset/Save/Cancel, physical fake worker draining, creator-thread root Destroy and exception paths.
6. Inspect historical 8.30–8.34 scope guards and previous attacker injection seams; design an **exact successor envelope** with positive control and reached-negative tamper tests, not a broad skip.
7. Confirm all communication statuses explicitly say **NO AI REQUEST SENT**, not a fabricated real provider response.
8. State **severities and specific file/line findings**, necessary changes and test canaries before source implementation. Refuse if any HIGH/MEDIUM remains.
9. Confirm full Windows release tests, exact commit/tag and original same-ID master workbook + dashboard ordering remain mandatory.

**Expected response template:** `DESIGN_GO|HOLD`, `SCOPE_GO|HOLD`, findings `[ID, severity, file:line, causal proof, required remediation]`, test canaries, exact path envelope. An unaddressed finding stops product integration.

## Current verified engineering state

Product release: Phase 8.34, commit `b0490cd9e72104a74a32dc5315cbc55bc4034676`. Phase 8.35 governance assessed/closed separately. Phase 8.36 product release **OPEN**, not staged or shipped. No provider network calls enabled. Separate Git batching proposal **HOLD**. This PR **does not grant approval** to merge or initiate live provider transmission.
