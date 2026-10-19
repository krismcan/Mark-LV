# Phase 8.36 — OFFLINE prompt review: minimal integration contract (v0.4)

**Decision sought:** independent DESIGN_GO/HOLD and SCOPE_GO/HOLD on exact sealed Phase 8.34 parent `b0490cd9e72104a74a32dc5315cbc55bc4034676`. **This draft is NOT production or release approval.** Supersedes design v0.3 on this review branch. 19 October 2026.

## Purpose, value and non-goals

One additional **usable Nayeon desktop action**: from the existing Conversation pane, the user selects *Review offline prompt*, sees exactly what would hypothetically be submitted plus a prominently visible "**OFFLINE REVIEW ONLY — NO AI REQUEST, CREDENTIAL ACCESS, OR ACTION**" disclosure, then selects *Confirm offline review*. The app displays a fixed **non-authorising** confirmation receipt. Existing *Save offline*, *Simulate reply*, *Review Clear*, *Review New Session* and navigation remain unchanged. No actual AI request, provider readiness claim, transmission, credential lookup, change to offline history, action authority or implied future send approval. No arbitrary model-ready transcript replay.

**Deliberate scope reduction resolving v0.3 latent-capability finding:** Phase 8.36 has **NO provider/model metadata extraction at all**. Show a literal "MODEL NOT CONNECTED — OFFLINE PREVIEW ONLY". Do not construct, import on a new path, capture or retain `ProviderConnectionService`, `ProviderConnectionFileStore`, `BoundSecretResolver`, `AIService`, `OpenAIProvider`, `compose_provider_ai_service`, filesystem/secret providers, network clients or an observer/callback pointing to those. Do not place one on `OfflineWorkspaceApplication`. Explicit text and simple opaque identity only. A future independently reviewed *live* phase must separately solve external-writer A→B→A freshness and real outbound approval; the 8.36 receipt gives **zero** send authority.

## Full creator-owned protocol; resolve v0.3 widget-state P2 without unsafe proof

The existing `OfflineWorkspaceApplication` owns the unique Tk root and current conversation pane/generation/session. Its new offline review controller uses pure in-memory owner state and exact non-secret prompt data, plus opaque identity. There is only one creator-thread writer. No callback based on caller-supplied `human_clicked=True`. Exact bound Review/Confirm buttons and commands may be invoked programmatically within the process: never claim cryptographic proof of physical human presence. A stale, copied, foreign or direct owner confirmation fails if its generation/callback/ticket does not match.

0. **Admission:** only the currently bound *Review offline prompt* command for the current active conversation pane, creator thread and exact generation may initiate a new proposal. `reply_owner` must report no outstanding worker, drain, poison or reply transaction; any concurrent Cancel, Reset, navigation or root Destroy revokes proposal A. Prompt must be 1–512 NFC codepoints and <=2048 UTF-8 bytes with no Unicode control/format/surrogates; no secret store or provider call.
1. **UNARMED:** Confirm widget begins DISABLED. Owner records current opaque root/pane/session/generation and canonical prompt snapshot and absolute deadline from actual monotonic clock (`time.monotonic_ns() // 1_000_000`, 30,000-ms TTL; validate clock monotonicity using injected clock in tests). No ticket exists. Any Confirm attempt before arming **poisons** A. No Tk or user callbacks inside pure owner state transitions.
2. **Complete render:** publish exact prompt with the literal offline non-transmission disclosure, then verify entire published text, current pane/root, entry value, no stale/cancel/Reset/Destroy and owner UNARMED **after every potentially reentrant Tcl call**. A failed/partial/before-or-after-effect render revokes A.
3. **Enable seam (still UNARMED):** issue `ttk.Button.configure(state="normal")`; a nested Confirm or Reset/Cancel always poisons/revokes. A normal return from Configure is **NOT** evidence the button is enabled.
4. **Separate post-enable Tk observation:** after Configure returns, still UNARMED, call the exact current Confirm button's `instate(("!disabled",))` (or equivalent verified Tk state query) and check the returned result. The observation is **reentrant and untrusted until revalidation**. **Explicit negative canary:** an instrumented normal-return Configure that silently leaves or resets the button to DISABLED must fail and never arm. A missing/destroyed widget or Tcl exception fails closed.
5. **Final pure revalidation, then PURE ARM:** after the Tk observation has returned, recheck root/pane/session/generation, prompt, clock, disclosure identity, receipt freshness, no poison or pending navigation/reset; ensure the exact verified widget is still the bound current Confirm (using opaque object identity and cached generation, NOT another Tcl query inside pure arm). The trusted creator-thread controller now passes the single current verified observation identity into a **separate callback-free, Tk-free, side-effect-free** pure transition; that transition issues a fresh single-use ticket. It must **not** invoke Tk to "verify state" and must never accept a public caller-supplied boolean as widget-state proof. No Tcl, callback or result publication occurs during arm. Because all Tk operations are serial on the creator thread, no further Tk seam runs between the final pure validation and arming. Reentrant state changes during prior Tcl work poison the proposal.
6. **Later distinct Confirm:** exact bound Confirm callback, creator thread and current ticket are required. Consume the ticket and revoke A **before** any potentially reentrant publication. Recheck prompt and context. Return the **fixed offline-only non-authorising receipt**. Guard before/after status/disable/clear Tcl effects so A cannot overwrite B after nested Reset, Cancel, navigation or Destroy. Repeated/foreign/copy/expired Confirm fails, no worker, action, secret or network path.
7. **Invalidation:** cancel, changed text, Reset, new session, navigation, destroyed pane/root, clock jump/expiry and uncertain Tcl state always deny the old proposal. Any safely recovered UI state is explicitly local and never a send permission.

## Eliminate v0.3 retained writable service graph issue

The tested product's existing `ConversationWindow` contains callbacks that close over `OfflineWorkspaceApplication`, so simply limiting a new owner's constructor arguments to primitives is NOT a sufficient graph boundary. **Do not inject or retain a provider/store/secret service at the application or widget composition layer in this milestone.** The only optional metadata label is the constant literal "MODEL NOT CONNECTED — OFFLINE PREVIEW ONLY"; do not read any cached connection metadata. Review owner accepts exact primitive/frozen types; refuse `ProviderConnectionService`, `ProviderConnectionFileStore`, arbitrary callable/closure, resolver, SDK client, writable wrapper and mutable metadata. No late dynamic provider factories captured by callbacks.

The negative graph test must start at the root-owned new Review and Confirm callable entries AND the retained `ConversationWindow` callbacks, traverse Python closure cells, `functools.partial` captures, bound `__self__`, callable object fields and relevant container/object fields with an explicit finite budget, and fail if any provider/store/resolver/composer/network/writable-provider capability is reachable. Do not claim this proof is an arbitrary same-process sandbox. The pre-existing presentation-profile Save remains separate and untouched; this scope contains no new persistence. A test that injects a `ProviderConnectionService` onto the actual application or into a captured wrapper before review must fail before arm. Do not inspect credentials.

## Exact changed-file allowlist — independent SCOPE decision required

All paths relative to protected repo root. No wildcard, incidental rename, broad legacy migration, existing tag rewrite, permission bypass or extra dependency. A SCOPE_GO must explicitly approve each increment envelope. If testing demonstrates another necessary changed path, **HOLD** and amend/rereview before editing.

**Increment A — pure owner (new only, 2 files):**
- `nayeon/desktop_alpha/offline_request_review.py` (NEW)
- `tests/test_phase_836_offline_request_review.py` (NEW)

**Increment B — actual Tk/product composition (2 modified, 2 new; 4 files):**
- `nayeon/desktop_alpha/application.py` (MODIFY)
- `nayeon/desktop_alpha/workspace_window.py` (MODIFY)
- `tests/test_phase_836_tk_request_review.py` (NEW)
- `tests/test_phase_836_application_review.py` (NEW)

**Increment C — required exact successor Git scope/migration, evidence and administration (2 new tests, 9 existing tracked modified, 2 new docs; 13 files):**
- `tests/phase_8_36_scope_migration.py` (NEW)
- `tests/test_phase_836_scope_integrity.py` (NEW)
- `tests/phase_8_30_scope_migration.py` (MODIFY)
- `tests/phase_8_34_scope_migration.py` (MODIFY)
- `tests/test_phase_830_scope_integrity.py` (MODIFY)
- `tests/test_phase_831_scope_integrity.py` (MODIFY)
- `tests/test_phase_832_scope_integrity.py` (MODIFY)
- `tests/test_phase_833_scope_integrity.py` (MODIFY)
- `tests/test_phase_834_scope_integrity.py` (MODIFY)
- `.codex/CURRENT_STATE.md` (MODIFY)
- `docs/pre_829_shutdown_ownership_failure_ledger.md` (MODIFY)
- `docs/phase_8_36_offline_request_review_rfc.md` (NEW)
- `docs/phase_8_36_offline_request_review_review.md` (NEW)

**Total proposed envelope: exactly 19 distinct paths**, with A/B/C separate preflights. The five old integrity consumers may require targeted test-contract migration because they pin source ancestry; preserve exact old sealed tags/commits/alias and index/disk attack insertion hooks. Never weaken a security test to allow a new source. Earlier legacy root folders, `reply_owner.py`, `reply_worker.py`, `conversation_session.py`, `connection_service.py`, `connection_persistence.py`, `connection_composition.py`, `service.py`, `providers/`, `secrets/`, original nonisolated user work, package manifest, all existing tags and prior milestone docs are EXCLUDED and MUST remain unmodified. No scope guard code work before actual independent SCOPE_GO.

## Acceptance negatives & release gates

A01: Confirm invoked synchronously before/after preview rendering; refuse, no late arm.
A02: Confirm injected before/after `configure(state="normal")`; refuse and poison.
A03: **Configure returns normally but button state remains DISABLED**; actual post-enable Tk query must fail and not arm.
A04: `instate` query itself dispatches Reset/Cancel/Destroy or raises; refuse and no stale A.
A05: Direct/foreign/stale/copy/replayed/expired/off-thread ticket/callback; refuse and do not consume successor B.
A06: Exact prompt changes/NFC invalid/reset/reply worker not retired; refuse.
A07: Metadata/store/provider injection via closure/bound method/partial or app attribute; causal graph walk detects, refuse.
A08: Provider composition, OpenAIProvider, BoundSecretResolver, SDK, socket, filesystem writer and network call tripwires; zero invocations.
A09: Confirm status widget `configure` before/after-effect nested Reset/Cancel; B wins, old A no success.
A10: Ordinary offline Save/Simulate Reply/Reset and pane/root Destroy unchanged, no leaked Tk/worker.
A11: Historical frozen Git/tag/staged-index/alias/tamper-injection suites retain their original reachable refusal.
A12: Non-authorizing receipt cannot be used to send, execute, persist or alter conversation history.

**Mandatory review chain:** independent DESIGN_GO and exact pathwise SCOPE_GO; then per-increment SOURCE/TEST_GO with native focused/affected Windows tests; full Windows `unittest` pre-stage, staged and postcommit 3 times under the established release discipline (Phase 8.34 three such runs cost ~208 minutes); compileall, whitespace, read-only single-writer exact head/index guard review; immutable annotated tag and nonforce GitHub push; update original existing same-ID 16-sheet Google Drive workbook and read back; then publish sanitised dashboard. Unresolved material HIGH/MEDIUM remains HOLD.

**Source truth:** annotated Phase 8.34 tag object `b503ce088ee4a787990534ea862be2936fa55767` peels to protected `b0490cd9e72104a74a32dc5315cbc55bc4034676`. Historical PRESEAL text in old documents is historical and needs separate evidence reconciliation, not fabricated missing-tag proof. No real credentials, external model requests or desktop actions.

**Current state:** v0.4 design-only proposal, not yet signed off. Off-repo v0.3 research 22/22 tests per run x3, 1,129/1,129 prompt parity x3; those DO NOT prove this modified design or release. PR remains DRAFT/UNMERGED; protected product unchanged.
