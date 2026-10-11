# Phase 8.28.1 — Tenure-bound trusted onboarding recovery (security maintenance)

**Date:** 11 October 2026
**Branch:** `nayeon-v1`
**Protected starting HEAD:** `2e111ce8caa903d78390926299f9fe3fc6ef4c79`
**Proposed product seal tag:** `nayeon-v1-phase-8-28-1-tenure-bound-recovery-security-01`
**Scope:** Trusted, human-owned OpenAI onboarding metadata and key-operation coordination only.
**Explicit exclusions:** No real API keys, provider calls, native secret value reads/writes by the recovery controller, computer-control authority, cross-store transaction, model-selectable recovery, external malicious filesystem writer guarantee, or claim of physical power-loss directory durability.

## Root cause

The former Phase 8.26/8.28 short-lived named-mutex + recovery-marker admission treated marker absence as normal. In the abandoned-mutex recovery branch, creation of the marker was attempted without checking for a failure to persist *any* evidence. After releasing the mutex or process restart, another cooperating process could observe no marker and admit a new operation, violating cross-process and restart safety. In-memory fixes cannot solve this; absence of persisted evidence is indistinguishable from clean start.

## Security architecture implemented

- **New tenure always begins unadmitted:** A Windows named mutex is held continuously on its acquiring thread across explicit human reconciliation and any approved work. Neither an abandoned acquisition nor historical journal READY grants admission by itself. A second process must wait and reconcile anew on ownership change.
- **Recovery state machine + bounded typed journal:** Complete checksum-framed, predecessor-linked, capacity-bounded, non-secret journal; reject malformed, duplicate, truncated, invalid-tail or unreadable evidence. Write/flush/fsync/close/reopen/reread IN_FLIGHT before any operation effect. All failures are fail-closed; never auto-retry an uncertain mutation.
- **Human reconciliation:** UI displays previous journal state, metadata, credential *presence only*, uncertain/legacy markers and archive status. A deliberate human acknowledgement and exact fingerprint are required, time-limited and generation/epoch-bound. The recovery dialog does not discard the management owner's approved mutex on close; closing the trusted management panel releases it.
- **No stale completion claim:** Metadata SAVE/CLEAR completion requires actual typed metadata reread. Credential CONNECT/REPLACE remain IN_FLIGHT/uncertain absent exact key-value verification (not attempted or claimed). REMOVE requires SUBMITTED and two independent observations of key absence; test-only methods are journalled and cannot grant credential authority.
- **Drift and observer binding:** The controller binds credential-observer identity, rejects silent observer introduction during an active tenure, rechecks the human-reviewed metadata/presence baseline before every action and refreshes it only following verified completion. Pending approvals are single-use and epoch/generation/expiry bound.
- **Journal capacity and legacy migration:** Reserve a completion slot before starting an operation; when close to journal capacity, human must separately approve preservation as a checksum-named archive before a newly reviewed checkpoint is created. Retained legacy recovery marker requires review, not automated clearing.
- **Narrow production surface:** New modules `onboarding_recovery.py`, `onboarding_recovery_document.py`, `onboarding_recovery_evidence.py`, `onboarding_recovery_store.py`, and `first_run_onboarding_recovery_window.py`; only affected two trusted hosts and two trusted Tk panels were altered. Legacy marker-approval branches removed. No model/agent tool route added.

## Verification / exact constraints

- Focused recovery tests: **62 / 62 passed; zero skips**, including fake-only journal corruption/failure/alias races, validation kinds, deterministic canonical metadata evidence, retention/rollover, stale READY, key REMOVE no-op, explicit injected mutex, real Windows Tk callback handoff, review expiry, and baseline drift.
- A genuine fake-only Windows child-process test confirmed a second process cannot acquire the retained named mutex while the first holds it. After releasing the mutex, a new process saw old READY but still required explicit reconciliation.
- Metadata host + Tk historical cases: **31 / 31 passed** after migration to fresh fake review. Credential coordination historical cases: **21 / 21 passed**. Credential management Tk cases: **20 / 20 passed**.
- Authoritative Windows host Python 3.12 `python -m unittest discover -s tests -p 'test_*.py' -q`: **2,204 / 2,204 passed, zero failures, zero skips**, twice as seal candidates. `compileall -q nayeon tests` passed.
- Historical scope migrations use exactly five approved new production modules via `tests/phase_8_28_1_scope.py`; all previous protected source blob comparisons remain exact. Independent read-only Codex Sol High review checked five prior seal baselines with **zero byte mismatches**.
- Independent security assessment: final reviewer found **no new HIGH trust-boundary bypass** but identified two **MEDIUM test-seal blockers**, the exact five-path old-phase subtraction guards and bare imports in the integration tests. Both were narrowly repaired and verified by host tests. Final exact-staged full regression and GitHub remote verification remain required before this milestone may be marked sealed.

## Explicit limitations

The named mutex protects cooperating Nayeon processes within the same Windows session, not uncooperative administrative writers, unrelated Windows sessions or hostile filesystem replacement. Journal SHA-256 detects retained corruption but not malicious rollback of a complete valid prefix without another trusted anchor. `fsync` and reread alone do not guarantee full physical power-loss/directory durability. Credential presence does not verify an API key's value, entitlement or provider connectivity. Such operations remain uncertain or require separate explicitly approved provider validation. Human review must be informed, not a programmatic confirmation.

## Seal checklist

[ ] Final review acceptance of the two corrected test-contract findings
[ ] Focused + canonical package test imports green, no skips
[ ] Exact staging inspection and staged diff check
[ ] Sole-running staged full regression, compileall, no skips/failures
[ ] Single product commit + new annotated tag; existing tags unchanged
[ ] Explicitly authorised push of branch and annotated tag; independently verify remote peeled tag and exact commit
[ ] Codex `.codex/CURRENT_STATE.md` refreshed to Phase 8.28.1
[ ] Same-ID master macro-enabled workbook updated and verified without damaging macros/16 sheets
[ ] Phase 8.29 stays blocked until all required gates have completed

**Security process note:** Historic tests were updated only where the approved Phase 8.28.1 authority contract changed; their original sealed content hashes, secret-import restrictions and behavioral fake-only safety assertions were not blanket-disabled or skipped.
