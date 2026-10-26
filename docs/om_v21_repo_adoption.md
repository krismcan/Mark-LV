# OM v2.1 — Tracked procedures, review disposition, and next enforcement boundary

Status: **DRAFT GOVERNANCE INTEGRATION, NOT RELEASED** (26 October 2026). Isolated descendant of BYOK Increment A SHA `4110fa69849f8127a325f9a9001284cd1bd3a59c`; original product branch, historical tags and operating model v2 are protected.

## Adopted procedural guidance
- `AGENTS.md` and `docs/engineering_failure_review_gate.md` now reference the independently reviewed host OM v2.1 while preserving all prior v2 policy, STOP precedence, exact provenance and three mandatory native Windows full-suite gates.
- Require an independently challenged impact-and-topology census before expensive testing; run real COMPLETE_UNSTAGED, EXACT_STAGED and EXACT_CHILD historical guards, manifest checks, source bytes and negative cases before each respective full suite; investigate targeted failures before repeats.
- Permit only one writer, exact logs and native exit codes. GitHub commit/annotated tag verification must precede original same-ID 16-tab macro-enabled Google Drive workbook readback, then independently served public dashboard verification. Release evidence must distinguish fake-only engineering from genuine consumer BYOK acceptance.

## Independent adversarial review result
Initial independent review of proposed `scripts/om_v21_state_canary.py` and its 13 Windows-green tests returned HOLD with four MEDIUM findings: (1) tracked `assume-unchanged` source outside manifest could change invisibly, (2) child test stdout could forge `Ran...OK` and exit 0, (3) arbitrary interpreter/environment/import origin was unpinned, and (4) source, Git refs and evidence were not reverified after tests. The helper and test module are REMOVED from the proposed merge diff, rather than weakened, waived or promoted. Historical draft commit retaining the rejected code is an unmerged PR record, NOT an approved release artifact.

## Explicit remaining work
OM v2.1 is in use as a reviewed planning/preflight policy and proposed tracked procedure. There is **NO machine-enforced independent preflight admission**, authenticated external reviewer/witness, production PRC, authorised regression reduction, or newly approved provider/credential capability. The existing exact phase integrity tests and three authoritative complete Windows regressions still govern all releases. Any future executable enforcement must separately resolve the four MEDIUM findings and demonstrate real-state adversarial coverage before reintroduction.

## BYOK continuing scope
Within EXISTING Phase 8 only, the next planned user-observable task is explicitly user-triggered Connection-pane to same-root Tk Toplevel child, with fake-only injected coordinator and conservative states initially. This plan does not authorise native secret storage, real provider requests or acceptance of gates 3/4. See `docs/phase8_byok_connection_ui_increment_b_plan.md`.

Do not claim policy adoption or BYOK consumer acceptance fully shipped while this draft is unmerged/unreleased; formal architecture remains 5/19, acceptance 0/12.