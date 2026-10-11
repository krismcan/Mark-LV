# Nayeon v1 — Pre-8.29 Security Maintenance: Shared Metadata Review Ownership & Governance Regression

**Date:** 11 October 2026
**Starting protected HEAD:** `02f3fb6a0de9c8871ff5ec41818853725b24226c`
**Branch:** `nayeon-v1`
**Previous immutable Phase 8.28.1 annotated product tag:** `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01` => `3cf53d0844af753468f26452f87b70b541bc0b9c`.
**Review scope:** Separate pre-8.29 security maintenance, no new AI capability, no model route, no real credentials/providers, no new access authority.
**Seal state:** UNSEALED until independent review and exact staged regression.

## Pre-phase failure ledger

### F1 — Confirmed medium: wrong-window metadata CLEAR without approval

Root cause: `FirstRunMetadataManagementWindow` stored only an operation enum, while shared `TrustedMetadataCommitHost` stored a mutable process-local pending operation with no originating window/review token. A stale SAVE window could approve a CLEAR review created by another window without that other window's explicit CLEAR acknowledgement.

Prior fake-only Windows Tk demonstration in `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_metadata_crosswindow_fake_probe.py`: A SAVE; B callback cancels A (despite disabled B button); B creates CLEAR without checkbox; A approves; host reported VERIFIED and metadata was erased. **The B reject callback was invoked programmatically**, not by clicking its disabled button; this is a trusted shared-host composition risk, not evidence of a normal end-user exploitation path in the current offline launcher.

Repair:
- Trusted metadata host adds a process-local exact UI ownership token, a separate one-time operation-review ticket, ownership-scoped SAVE/CLEAR request, exact owner/ticket/operation approval, mandatory CLEAR acknowledgement, replay/foreign cancellation denial and no direct `approve()` while a UI ticket is outstanding.
- The recovery controller now enforces **one UI owner across all host objects sharing the canonical metadata path**. Closing a nonowner window cannot revoke another host's mutex tenure. A closed UI panel enters a terminal closed state so stale callbacks cannot reclaim owner tokens. Ownership is claimed only after widgets are fully built, so a constructor failure does not strand the global owner. Following owner closure, another window may claim ownership only after independent fresh human reconciliation.
- Existing legacy direct host review API remains trusted/internal and covered by earlier frozen tests; it is not an agent/model surface. No native credential operations added.

Fake-only adversarial `tests/test_pre_829_metadata_review_ownership.py` adds ten real Windows Tk cases: foreign cancel/clear, non-owner close, stale token and wrong operation, CLEAR consent, owner handover, two host instances with shared recovery controller. Earlier 31 metadata host/GUI tests stay green. Security audit additionally rejected cross-host foreign close and stale-closed-callback behavior; both have targeted regression tests.

### F2 — Confirmed medium: seven historical AGENTS.md frozen-byte guards after authorised governance update

Root cause: older phase tests required root `AGENTS.md` to equal the earliest sealed Git blob, while the explicitly approved failure-review policy was later committed at `02f3fb6...`. That was an intentional governance-only change, not a production-code regression. Seven older frozen tests failed without this narrower updated contract.

Repair: `tests/governance_seal_contract.py` asserts the original historical seal is an ancestor of the authorised governance commit, the authorisation commit is an ancestor of current HEAD, current `AGENTS.md` equals the **exact `02f3fb6...` Git blob** (normalised CRLF), and it includes the mandatory failure-review rule. Precisely seven previously affected test methods invoke this in place of only their `AGENTS.md` comparison. All other archived file and source-hash protections remain unchanged.

## Verification

- Direct original attack replay after F1 patch: old wrong-window CLEAR fails, and the metadata remains configured.
- Fake-only targeted suite: 41/41 shared metadata/UI tests passed.
- Python 3.12 `compileall -q nayeon tests` succeeded.
- Full working-tree `python -m unittest discover -s tests -p test_*.py -q`: **2,233 / 2,233 tests passed, 0 failed, 0 skipped** (diagnostic log: `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_maintenance_full_diagnostic1.log`).
- Independent read-only security/test-contract review: initial HOLD (2 MEDIUM cross-host lifecycle gaps), both remediated; second read-only Sol High review CLEAR within scoped boundary. Evidence `C:\Users\krist\AppData\Local\Temp\nayeon_pre829_maintenance_independent_review_result.txt`.
- Exact stage-time and post-commit regressions: PENDING.
- Old annotated tag must remain immutable. GitHub remote push, independently peeled tag and workbook update: PENDING.

## GO/HOLD policy

This packet permits **repair and verification only**. **Phase 8.29 and five-phase consecutive implementation remain blocked** until the repair has a reviewed, verified independent local and remote seal and a renewed failure-retrospective GO. Real credentials, native secret mutation, provider network calls and release gates still require separate human consent.

## Independent review finding / re-review closure required

First independent Codex Sol High review found two additional MEDIUM gaps: (a) two metadata host instances shared one pooled recovery controller but closing the second host could revoke the first owner's mutex tenure; (b) an already closed Tk panel could reclaim a new owner token through a retained callback. Both were repaired at the pooled controller/UI lifecycle level. Extended fake-only Windows Tk tests now cover foreign-host close, closed callback, exact ticket with wrong owner, and widget-construction failure. Separate read-only re-review **CLEAR**, with no material findings in cross-host and closed-widget fixes. Authoritative complete working-tree regression after remediation: **2,233/2,233**, no errors, failures or skips. The separate exact staged full regression and seal remain required before GO.
