# Phase 8.34 RFC v0.2 — Owned fake reply lifecycle before connected AI

Date: 18 October 2026. Status: DESIGN CANDIDATE / INDEPENDENT REVIEW REQUIRED.
Protected parent: `1a972d1d292597239c938d53437218c536b5bf3f`, branch `nayeon-v1`.
Latest immutable annotated seal: `nayeon-v1-phase-8-33-offline-delayed-completion-01`, object `0b5bb13d0ea8847ead6e05d4cd12af57a891d5a0`.
Current 8.33 authoritative host baseline: 2,683/2,683 PASS, native exit 0, no Tcl warning. No new tests executed for 8.34. Design review on 18 Oct returned HOLD on immediate live-provider integration with two HIGH design gaps and three MEDIUM design gaps. This proposal closes those gaps in *design*, not yet in implementation or verification.

## Purpose and staged product strategy

Deliver a fake-only, user-triggered, distinguishable reply transport and strict request owner as the necessary first increment of secure interactive AI conversation. Retain all sealed offline behavior. After this 8.34 mechanism passes independent design/source/native lifecycle and release gates, a separately scoped next phase may integrate actual BYOK provider calls, user consent and network configuration. Do not represent fake text as an actual AI response. No live secret, network provider, action executor, policy escalation, storage or background initiative is authorised in 8.34.

This phased decision is security-driven: the proposed direct live provider slice cannot be safely accepted until the worker/Tk lifetime and transmission-consent HIGHs are independently closed with evidence. Do not relabel Phase 8.34 as actual live AI availability.

## Architectural invariants

MODEL decides WHAT; AGENT decides HOW; POLICY decides WHETHER; SERVICE performs IT; VERIFICATION proves RESULT; MEMORY retains appropriate context. Model/provider text is data, never a permission, tool command, action outcome or verification receipt. Maintain permission -> policy -> confirmation -> execution -> verification for future actions. No model-to-execution route in this phase.

The sealed `OfflineConversationSession`, `DelayedOfflineCompletion`, offline Save/Cancel/Reset, Settings and identity remain frozen in authority and semantics. Existing `LOCAL_STATUS / UNSENT_OFFLINE` entries never become provider replies. Fake reply belongs to a separate preview-only ephemeral panel and carries explicit `SIMULATED REPLY / NO AI REQUEST` labelling, with no durable session history.

## Owned request contract

One app root owns one reply bridge. Its creator thread performs all admission, configuration, state transitions, timer registration/cancellation, physical worker observation, rendering, and teardown. Every owned Python callback checks `threading.get_ident` as its first operation, before Tk or owner state. Neither a copied ticket nor a numeric request ID proves authority.

A request is admitted only following an explicit human button press, from exactly the current view/token/generation/session epoch, with a bounded immutable prompt and a one-use unforgeable object-identity ticket. Enforce the existing input limits (512 codepoints, 2,048 UTF-8 bytes), zero unexpected control chars, and one active request. Request and reply are separate typed records. The later real provider phase must add a one-use human review/confirm binding exact prompt, provider/model, transmission disclosure and request limits; offline Save remains distinct and cannot serve as this consent.

Worker receives only exact typed immutable request data, a cancellation event and a capacity-one mailbox. The production worker and deterministic fake responder must be *exact reviewed module-level functions*, not arbitrary injected callables, subclasses, bound methods, callable instances, closures or dynamic plugins. Reject alternate worker/responder identity before creating a thread; controlled tests exercise the same exact module entrypoint with immutable synthetic request values and explicit external test-owned synchronization. Neither request data nor the thread target may contain a Tk object, bound UI method, root, pane, session owner, closure, provider credentials, provider service, network capability or action executor. This is a bounded direct-capture contract, not proof about arbitrary process-wide global or cyclic reachability. The module-level worker emits zero or one typed result into the capacity-one mailbox. Reentrant worker activation and duplicate result publication fail closed.

Worker must never perform Tk, call `after`, `event_generate`, widgets or UI liveness checks. After cancellation it cannot publish a trusted status. Fake reply contents are constant, clearly marked and never derived by transforming user text into a pretend AI answer. Worker exceptions produce only fixed bounded error categories with no exception text.

## Lifetime, cancellation, and delivery

The bridge owns at most one physical worker, a capacity-one result mailbox and one root-owned poll timer at a reviewed fixed interval (candidate 50 ms). Its creator-thread lifetime anchor owns strong references to the root, application, workspace, current/retiring pane and all interpreter-associated managed widget graphs *independently of any poll callback*. The anchor outlives the physical worker and is held by the main-loop owner through all exceptional exits. States: IDLE -> RUNNING -> DRAINING (cancel/expiry/navigation/fault) or CLOSING (close request) -> RETIRED (worker observed exited and joined, mailbox drained) -> DESTROYED (only then native widget/root destruction). POISONED is an orthogonal *admission block*, never authority to release an active lifetime anchor. Start is a single serialized transaction; uncertain scheduling, cancellation or startup poisons future worker admission. No replacement worker while a previous worker is alive or has unconsumed completion; no forceful thread termination.

Cancel, reset, navigation, close and expiry revoke the exact ticket *before* signalling the cancellation event. Navigation and pane replacement are deferred during RUNNING/DRAINING/CLOSING until the worker reaches RETIRED; cancelled requests remain visibly draining. Close-request and final native destruction are separate operations. UI statuses say cancellation prevents local display, not that remote execution stopped (only fake work exists in 8.34). A request deadline (candidate 30 seconds) revokes delivery, never physical lifetime. Poll callback never blocks on a live thread. After `is_alive` is false, the creator thread performs a nonblocking join, drains zero-or-one mailbox result without blocking, rejects malformed/foreign/duplicate output, discards cancelled/expired output, clears the physical slot and only then permits re-admission or final close. An empty mailbox after exit is a valid failure status, not a reason to wait or replay.

**Native Tk lifetime HIGH closure obligation:** the creator-thread lifetime anchor retains the entire Tk interpreter/managed widget graph for the worker's *actual* physical lifetime, independently of timer callbacks and the active pane. In RUNNING/DRAINING/CLOSING, requested close must not dispose the current pane, destroy the root or release this anchor. A routine close remains responsive while its owned poll is trustworthy. If timer registration/cancel/dispatch becomes uncertain, mark POISONED and retain the anchor; creator-thread explicit Retry Close / Retire ingress checks physical worker state without creating an untrusted replacement poll. If the Tk event loop exits exceptionally, `main()` must keep a strong application/root anchor in its `finally` block, perform creator-thread bounded join probes until the physical worker retires, and only then destroy the root; if it does not retire, do not release/destruct the graph, declare shutdown incomplete/HOLD and retain process ownership until external controlled termination. No worker-side destroy, daemon-detach, orphan-worker assumption or automatic new timer after uncertainty. A production fake responder performs deterministic finite work; injected native tests intentionally hold completion until released to prove retention through cancellation, navigation, polling failure, and `main()` unwind. Force worker-GC adversarial runs, weakref graph-survivor assertions and late/duplicate results. Any nonterminating worker remains a formal future-live-release blocker.

Consume result/ticket authority before any reentrant UI seam; recheck exact root/pane/generation/epoch/request/deadline and typed result identity after each reentrant boundary immediately before literal display. Never retry an uncertain result, forward response text into dispatcher, modify an unrelated pane, or call a model-selected action. Render only literal bounded text, no rich HTML/links/markup.

## Isolation and prohibitions

Startup defaults to existing offline workspace and never automatically spawns a worker. The fake responder is constructed only through explicit trusted injection for 8.34 testing / explicitly labelled simulated preview. No production `tests` import. The worktree may not load or probe credentials, authenticate provider, alter Connection metadata, write memory, contact network, open or automate applications, persist transcript, or start streaming.

All exception strings, request tickets, root identities, paths, headers and credentials are excluded from UI/log text. Review fake-only tripwires must prove zero provider/SDK/secret/credential/WinCred/HTTP/filesystem-side-effect/action invocations.

## Bounded 20-path source proposal (subject to independent scope review)

ADD:
- `nayeon/desktop_alpha/reply_contracts.py`
- `nayeon/desktop_alpha/reply_owner.py`
- `nayeon/desktop_alpha/reply_worker.py`
- `tests/test_phase_834_reply_owner.py`
- `tests/test_phase_834_reply_worker.py`
- `tests/test_phase_834_tk_reply.py`
- `tests/phase_8_34_scope_migration.py`
- `tests/test_phase_834_scope_integrity.py`
- `docs/phase_8_34_text_reply_rfc.md`
- `docs/phase_8_34_text_reply_review.md`

MODIFY:
- `nayeon/desktop_alpha/application.py`
- `nayeon/desktop_alpha/workspace_window.py`
- `tests/phase_8_30_scope_migration.py`
- `tests/phase_8_33_scope_migration.py`
- `tests/test_phase_830_scope_integrity.py`
- `tests/test_phase_831_scope_integrity.py`
- `tests/test_phase_832_scope_integrity.py`
- `tests/test_phase_833_scope_integrity.py`
- `.codex/CURRENT_STATE.md`
- `docs/pre_829_shutdown_ownership_failure_ledger.md`

This envelope does not authorise arbitrary descendant history, wildcard paths, relaxed test assertions, or mutable pin bypass. Validate static plus raw Git HEAD/index/disk/modes/aliases/historical tag objects; exact descendant once, allow no further child. Historical guard positive and adversarial negative fixtures must remain reachable and prove the original causal rejection. Any additional path requires independent scope amendment before edits.

## Open Failures & Prior-Issues Review

- 831-TK-ASYNCDELETE: earlier native worker-GC Tcl retirement crash; HIGH relevance to any new worker. Not closed for a new physical worker by the 8.33 timer-only test. New forced GC and native lifetime adversarial tests mandatory. OPEN FOR 8.34 DESIGN/TEST.
- 833-M05: scheduler registration/cancellation uncertainty and stale callbacks. Retain fail-closed poisoned admission, exact physical handle and no replacement after uncertain native registration. Open new-scheduler review; sealed 8.33 remains unchanged.
- 833 cancellation-publication Tcl fault: controlled 8.33 repair passed 2,683 tests, but new callbacks require their own fault-injection and original failure assertions. OPEN FOR NEW PATH.
- 833-M06, 833-SCOPE-01: historical guard projection/index/disk bypass near misses. Must implement exact successor, verify positive/causal attacks, don't disable predecessors. OPEN FOR 8.34 MIGRATION.
- Provider readiness metadata-only contract: cannot act as consent; no provider activation in 8.34. Future live phase requires verified configuration ownership and separate transmission consent. DEFERRED OUTSIDE FAKE SCOPE, NOT WAIVED.
- Test suite duration rose to 2,217.653s for 2,683 tests; independently profile resource usage before any process-level test parallelism. No removal of mandatory release gates.

## Acceptance sequence

1. Independent GPT-6.1 Sol High RFC review with no unresolved HIGH/MEDIUM within fake-only 8.34 scope; separate exact-SCOPE_GO.
2. Implement only approved scope in isolated LF checkout. Preserve strict single writer.
3. Fake-only focused + affected, native direct Tk, isolated child worker-GC, permission/effect tripwires, all historical guard tests. Reproduce failure scenarios before claiming repairs.
4. Independent source, test-diff, staged-diff security reviews; exact SHA-pinned 20-path manifest; compileall; git diff --check.
5. Three required full native Windows unittest runs (prestage, staged, postcommit), all exit 0 and **zero Tcl warnings**, with no skipped/weakend tests and five-minute progress watchdog.
6. Exact reviewed staging; immutable product commit and annotated tag; non-force push and independent GitHub remote refs verification.
7. **Separate post-seal administrative operations, outside the 20-path product Git manifest:** append evidence to the same original 16-sheet Drive workbook ID `1n0tDiBQCkPWluX6eakRiRfq57tflRW5L` and verify readback. In the independent `krismcan/nayeon-v1-dashboard` repository, update exactly `data/snapshot.json`, `data/snapshot.js`, `app.js` if needed for source consistency, and `index.html` for the cache version; this dashboard repository has its own separately reviewed path scope and deployment verification. No dashboard file is admitted into the Nayeon product repository. Never alter historical 8.33 seal.
8. Phase 8.34 release claim **only:** a deterministic fake-only response owner with real Windows worker/Tk lifecycle proof; not actual AI chat, BYOK consumer release, or any of 12 end-user acceptance gates.

NO-GO on any unresolved security finding, impossible worker graph-retention proof, failed native test, contamination of offline owner, unapproved scope migration, stale refs or unverifiable release evidence.
