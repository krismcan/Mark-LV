# Phase 8.36 — Consent-bound model-ready conversation (DESIGN REVIEW ONLY)

**Date:** 19 October 2026  
**Status:** `DESIGN_HOLD` until independent design and scope GO. **Do not merge this draft PR.**  
**Protected parent:** `b0490cd9e72104a74a32dc5315cbc55bc4034676` (the immutable Phase 8.34 product release).  
**Release semantics:** Phase 8.36 is not a live-provider release, and this branch contains documentation only.

## Goal

Create a bounded, visible **Review AI request** flow in Nayeon's desktop conversation UI as a prerequisite for later human-consented AI transmission. Users must see the exact proposed prompt, provider/model metadata and an explicit disclosure. Confirm in this first increment produces only a deterministic **reviewed offline; no request sent** status. Existing Save Offline / Simulate Reply keep their original meanings. No arbitrary model output can become an action, credential access or permission.

This is intentionally a **zero-network implementation scope**, not a release claim that Nayeon can already answer with real AI. A future live request path needs separate explicit transmission consent, provider setup validation, bounded network lifecycle and security review.

## Existing sealed boundaries (review these source paths)

- `nayeon/desktop_alpha/application.py`: creator-thread Tk trust ingress; pane, view token, generation and session epoch/revision; Save, Reset, reply cancellation, teardown.
- `nayeon/desktop_alpha/workspace_window.py`: actual conversation widgets, fake-only reply preview and Tk scheduler lifetime.
- `nayeon/desktop_alpha/conversation_session.py`: ephemeral `UNSENT_OFFLINE` conversation history; never silently send saved history.
- `nayeon/desktop_alpha/reply_owner.py`, `reply_worker.py`, `reply_contracts.py`: immutable exact fake reply worker and historical safety guards. No live provider allowed into this path.
- `nayeon/brain/connection_service.py`, `connection_document.py`, `connection_readiness.py`: cached non-secret provider metadata; `READY_FOR_COMPOSITION` proves **metadata eligibility only**, not a live credential, available model or consent.
- `nayeon/brain/service.py`, `connection_composition.py`, `providers/openai.py`: existing provider-neutral interface and lazy OpenAI provider; must **never** be called by this review-only increment.

## Proposed owner and one-use review contract

1. **Review button** is the explicit human-initiated creator-thread ingress. Ordinary offline Save is not review and cannot create a review ticket.
2. The trusted root-level owner creates a bounded, NFC-validated exact-prompt proposal. Current pane/root/generation/session/epoch/revision, and **exact cached provider-document identity**, are bound to the pending one-use ticket.
3. Show the exact proposed prompt, provider/model metadata and a disclosure that **nothing is sent**. This UI does not attest that a credential exists or the named model is remotely supported.
4. Creator-thread **Confirm reviewed request (offline)** consumes the current ticket before any callback or Tk render, then rechecks the exact context, prompt, current metadata document identity, provider/model, expiry, worker-idle state and current owner. It produces a fixed non-authorising receipt and **zero outbound bytes**. Receipts must be impossible to reuse as future network permission.
5. Cancel, Reset, navigation, root Destroy, model/config change, expiry or uncertain Tk scheduling/reentrancy revoke the ticket **before** further effects. Never publish A's status over successor session B.
6. On any uncertainty, fail closed with a fixed local status; no SDK call, HTTP, secret resolution, persistent transcript or action. The existing fake worker lifecycle remains separately owned and cannot be bypassed.

**Privacy:** Reviews display only the current bounded prompt, not automatic conversation history. No key, resolver, backend, Tk reference or callable is admitted into a worker. No prompt logged to product persistent storage. A later separately reviewed live transmission must clearly disclose what leaves the machine.

## Design risks that require explicit reviewer GO/HOLD

| Canary | Attack or failure | Required fail-closed result |
|---|---|---|
| C01 | Edit the prompt after review | Old ticket refused |
| C02 | Reset/new session/navigate to new pane while A pending | A revoked; cannot authorise B |
| C03 | Provider model/config changes A→B→A with same display text | Exact cached document identity mismatch rejects A |
| C04 | Duplicate/copy/foreign owner ticket | No execution; exactly one decision |
| C05 | Nested Tk confirm, Save, Reset or cancellation callback | Consume before callback; stale status never overwrites successor |
| C06 | Expiry, non-monotonic clock, worker still active/draining/poisoned | No new review admission |
| C07 | Uninitialised, unsupported, forged or missing connection metadata | Fixed status, no secrets/SDK/network/disk rereads |
| C08 | Control chars, surrogates, non-NFC, overlong Unicode prompt | Match sealed Phase 8.34 validator and reject invalid |
| C09 | Child pane/root Destroy during preview or confirmation | Creator-only; no orphaned Tcl work |
| C10 | Tk before/after-effect exception and nested close | Revoked; no stale view publication |
| C11 | Ordinary Save, Reset or Simulate Reply | Never implicitly sends/reviews data |
| C12 | Historical tamper of Git tag/tree/index/worktree or read-injection seam | Existing 8.30–8.34 guards still reach and refuse attack |
| C13 | Any implementation accidentally invokes `AIService.generate`, SDK, WinCred, HTTP | Test tripwire fails the milestone |
| C14 | Receipts forwarded into an action executor | No such route exists; deny authority |
| C15 | Future attempted live request cancellation/remote timeouts | **Deferred** — requires separate live transport design and review |

## Candidate feasibility, not release validation

An off-repository synthetic Windows research prototype (not in this branch) passed:
- **170/170** selected existing reply/credential/readiness/offline-session/onboarding baseline tests;
- **19/19** pure consent tests;
- **15/15** native Tk UI and callback-order tests, including a discovered/fixed stale-status publication defect;
- **20/20** cached provider-document identity tests, covering metadata A→B→A and zero secret/disk/network calls;
- **1,129/1,129** original Phase 8.34 prompt-validation equivalence cases.
Pure/Tk/parity suites passed three fresh-process cycles after final proof-of-concept changes; they are **not** the 3 authoritative full Windows release regressions. No sensitive local test paths or user configuration are part of this PR.

## Tentative exact scope (not yet authorised)

First increment, after `DESIGN_GO` + `SCOPE_GO`: one pure root-owned consent review module with tests; then a separate bounded Tk wiring change to application and workspace. The exact list of tests and historical scope-migration adapters must be independently established; neither broad allowlists nor modification of historical tags are permitted.

## Required product release gates, unchanged

Independent `DESIGN_GO` and `SCOPE_GO` (no unresolved HIGH/MEDIUM) → bounded source/tests → focused/native adversarial tests → independent SOURCE/TEST/STAGED GO → exact SHA/staging/whitespace verification → **three full Windows pre-stage, staged, postcommit regressions** → immutable product commit+annotated tag → non-force GitHub push and remote verification → same original macro-enabled master workbook update/readback → sanitised public dashboard update.

The Phase 8.35 experimental Git-batch transport remains a separate **HOLD**, never part of Phase 8.36 scope.
