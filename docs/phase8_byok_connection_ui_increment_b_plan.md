# Phase 8 — Next consumer-journey integration increment (proposal, not numbered 8.38)

Decision date: 26 October 2026. Source: original Drive master Build Plan row 13 (Secure Secrets & BYOK Onboarding) and release gates 3/4. Phase8 remains IN PROGRESS; architecture 5/19 and consumer acceptance 0/12. Increment A is sealed fake-only at commit 4110fa69849f8127a325f9a9001284cd1bd3a59c and does NOT expose a normal app connection flow. Existing reviewed gap audit: D:\\Nayeon\\Governance\\PHASE8_BYOK_GAP_AUDIT_20261024.md. This file is a bounded work proposal and not approval for higher-risk live-provider or real credential access.

## Actual missing bridge in current default path
nayeon.desktop_alpha.__main__ -> window.main -> OfflineWorkspaceApplication -> WorkspaceWindow.ConnectionWindow. ConnectionWindow is currently offline-only and offers return to Conversation. No normal-user flow opens the prior management or validation windows, and there is no production composition/factory injecting the real Windows credential backend. Existing owner in first_run_connection_owner.py is intentionally fake-only and does not have a registered UI caller.

## Proposed next coding deliverable
Add an **explicit user-triggered Connection pane action** that opens a creator-thread-owned Tk Toplevel child of the existing root (never a second Tk interpreter and never pass the root to standalone windows that can destroy it). The initial increment may use a fake-only host; if/when real backend factory or OpenAI validator is introduced, it requires a separate higher-risk consent/security gate. Root/application/pane/journey/generation must bind ownership, single-use ticket and stale-view rejection. Opening/navigation must not read native credentials or contact providers. Teardown must retire child and reject tickets, retaining recovery markers for uncertain effects.

Reference existing standalone FirstRunCredentialManagementWindow and FirstRunCredentialValidationWindow only after confirming Toplevel ownership, geometry/protocol handlers, coordinator and callback shape. No safe direct reuse is assumed. CONNECT/REPLACE with a real validator performs an OpenAI models.list request before storage: consent UI must separately disclose transmission to provider and conditional native storage. TEST_CANDIDATE requires its own validation consent. REMOVE requires explicit delete acknowledgment. Never display durable stored/usable from SUBMITTED or metadata alone; provider errors are INDETERMINATE.

## Pre-implementation safety gates
- Read and challenge actual existing app/pane lifecycle and tests, fake-only effect guards, 8.30–8.37 historical frozen migration assertions; define exact new successor scope and historical projections.
- Demonstrate negative tests for startup/navigation zero effects; wrong thread, stale root/pane/generation/replayed approval, reentrant Tk callbacks, child destroy/root close, cancellation and ambiguous completion.
- Run native Windows focused/affected historical modules, verified OM v2.1 real topology canaries before expensive suites, independent security review, and mandatory three full suites for a product release under unchanged policy.
- Explicitly label fake-only GUI wiring as engineering development, not real BYOK acceptance. Real-key storage and provider validation through default app remain separate authorised acceptance exercises.

## Decision
Proceed only with reviewed offline/fake-only user-visible flow wiring initially. Real key/provider setup and consumer gates 3/4 remain HOLD pending narrowly scoped human authority and full normal-app acceptance. Do not invent numeric Phase 8.38 requirements.
