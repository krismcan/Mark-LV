# Nayeon v1 — Phase 8.31 RFC and Product Acceptance

**Title:** Trusted Offline Conversation Session and Request-Lifecycle Contract
**Date:** 16–17 October 2026
**Status:** Architecture and bounded offline product independently reviewed; product LOCALLY SEALED 17 October 2026. See final acceptance section for the controlling disposition.
**Protected baseline:** `nayeon-v1` / `8b2fecf00d48324a187d931156cfa463bbd0aa67` (Phase 8.30 docs HEAD); Phase 8.30 product `6030f9b7afacd0543912bfb4a8b4fe610ebd9632`. Both annotated 8.30 tags remain immutable.
**Readiness accounting:** five of nineteen overarching architecture phases closed; zero of twelve end-to-end release acceptance gates verified.

## 1. Why this phase

Phase 8.30 provides a single-root Tk desktop with Conversation, Presentation Settings and Connection pages, trustworthy profile read/save, and a preview-only conversation. The present Conversation `Text` widget owns its own transcript: switching pages destroys the pane and loses its messages. `PreviewOnlyController.send` returns a fixed offline notice, and there is no stable session entity or cancellation/version contract for future asynchronous replies.

8.31 should deliver a genuine local product improvement, while separating trusted user intent, untrusted conversation text, presentation and future provider responses. It is **not** a credential or real AI connection milestone.

## 2. Proposed product outcome

1. A trusted application-owned **in-memory conversation session** remains intact when navigating Conversation → Settings → Connection → Conversation and when changing presentation settings.
2. A user can submit bounded literal text as a local, explicitly **UNSENT / OFFLINE** entry and see a truthful fixed service-unavailable result. No generated reply, fake model answer or execution claim appears as real AI.
3. A user can deliberately start a fresh session or clear the current session after explicit confirmation. Old view callbacks and old confirmation objects cannot clear a successor's session.
4. The session is **ephemeral**: closing the application discards it, with visible notice. No implicit disk persistence, hidden history, telemetry, clipboard writes or online sync. Transcript export/import is deferred until separately scoped security review.
5. An isolated test-only fake request adapter exercises the complete owner → controller → view feedback path, including cancellation, out-of-order completion and the owner’s destruction. The production/default launch cannot select this fake adapter or instantiate any real SDK/provider/WinCred/action dependency.

## 3. Mandatory invariants and authority boundaries

- One Tk root, one application-owned trusted session owner, monotonically increasing session generation, exact view-identity token and exact per-submit request ticket. Sessions are never selected by model text, display names or imported profile data.
- Immutable typed entries (`source=USER | LOCAL_STATUS`, literal Unicode payload, finite size/sequence, explicit `UNSENT_OFFLINE` or `BLOCKED` state). Messages are untrusted **data only**; no HTML/Markdown commands, control sequences, interpolation, filesystem or GUI dispatch. The UI must not reinterpret strings resembling approvals, action results, prompt injection or trusted actor messages as authority.
- Preserve existing `ChatOutcome`/`ChatReply` contracts and Phase 8.30 preview-only behavior until any interface migration has a reviewed replacement invariant. The only production outcome for a valid submission is a truthful offline/non-executed result; `VERIFIED`, `EXECUTED_UNVERIFIED`, `PENDING`, or an arbitrary fake 'AI' reply must never be represented as production action evidence.
- The session owner resides above ephemeral Tk views; only current root/session/view and exact ticket may publish or mutate request lifecycle. UI destruction and reentrant navigation revoke old view authority without destroying the current session.
- No imported test support in the production import graph; no model-selected permission/policy/confirmation/execution route; no secrets, live providers, native onboarding mutex or device actions. Presentation identity changes labels only, never trust identities or authorization.
- Bound retained messages, per-message characters and aggregate bytes by fixed constants verified in implementation; reject overflow with a clear local status. Avoid silent dropping, log disclosure, unbounded recursion and Tk event-loop starvation.
- Preserve current single-writer repository rules and all historical Git tags/tests. Phase 8.30 secure presentation-profile owner is out of scope except for read-only inspection and use of published display labels.

## 4. Data and lifecycle sketch

- **`OfflineConversationSession` (new)**: one application-scoped trusted owner; private immutable tuple of bounded entries; per-session generation; monotonic entry sequence; constant-time liveness/ticket checks; explicit close/revoke. It cannot issue filesystem/network/native calls.
- **`OfflineSubmission` (new typed record)**: exact owner + session epoch + request ticket + bounded payload digest/size and state. This record is never itself a user approval or capability.
- **`OfflineWorkspaceApplication` (existing)**: creates one session after trusted startup, passes a read-only snapshot and narrow submit/new-session/clear callbacks to the Conversation pane; revokes stale view and pending UI reviews on navigation; terminal close revokes everything.
- **`ConversationWindow` (existing)**: renders literal session snapshots with honest offline status, does not own authoritative history, refuses stale callbacks, binds mapped keyboard/mouse submit and session reset confirmation to the currently active view. Screens update only after owner-confirmed state transition.
- **`PreviewOnlyController` (existing)**: remains hardwired to the no-provider/no-action route in production. A separate test-only fake adapter may be injected solely through explicit test constructors with strict effect tripwires and must not be exposed by the normal CLI.

**Not in scope:** provider key acquisition, credential validity/status probing, real OpenAI connection, asynchronous background thread, live model generation, semantic tool selection, computer action execution, voice, session import/export or persistence, multi-root Tk composition, new action permissions, changing Phase 6 click boundaries, changing storage/WinCred services.

## 5. Threat model and mandatory negative tests

| Threat / failure | Expected denial or containment |
|---|---|
| Stale Return/Send callback after page navigation | No mutation; successor view/session unchanged |
| Old clear-confirmation replay after 'New session' | Rejected by exact session generation/ticket; new history preserved |
| Reentrant `update()`/Destroy during submission or clear | Outer ticket invalidated; no late append or forged success |
| Overlong, ill-formed Unicode, delimiter, ANSI/Tk control or malicious prompt-like text | Strict literal validation/rendering; no command interpretation or exception leakage |
| Synthetic provider/WinCred/network/action import or call | Fail-fast tripwire in test; production import closure does not reach those services |
| Fake late completion after cancellation/restart | Ignored; no successor overwrite or false 'verified' result |
| Cap exhaustion or repeated submit spam | Finite bounded entries/bytes; clear refusal, stable UI and no disk growth |
| Navigation while a session confirmation is active | Confirmation revoked; no implicit clear or Save |
| Display-name/profile change | Presentation-only labels update; session owner/tickets unchanged |
| Exception from trusted rendering/callback | Fixed safe status; no phantom request completion or owner resurrection |

## 6. Acceptance gates (all mandatory)

**A1. Product UX:** real mapped Tk keyboard and mouse events submit literal text and retain the same session across all three pages; closing and reopening produces a fresh empty session with an explicit ephemeral-history explanation.

**A2. Authority:** no user text, fake reply or profile value can invoke a model, permission approval, policy, computer action, provider SDK, credentials, transcript write or terminal command; existing separately human-reviewed presentation-profile Save remains the only bounded non-secret product file write, as in 8.30. `ChatOutcome` states are accurately presented.

**A3. Lifecycle:** stale views, destroyed root, double-Submit, repeated Return, clear/restart replay, nested callbacks and delayed fake completions cannot modify a newer session; no lingering windows or worker processes.

**A4. Bounds and privacy:** exact type, Unicode and length rules; finite overall memory cap; no transcript values in logs/exceptions/telemetry; no persistent transcript artefacts; no auto-clipboard.

**A5. Integration isolation:** a real test-only fake adapter drives deterministic request transitions, including fail/retry/cancel and reentrant faults. An instrumented production startup/import/navigation/close negative control records zero attempts to reach prohibited provider, WinCred, onboarding native mutex, action, network or transcript-persistence entrypoints. Existing verified read-only presentation-profile startup is explicitly permitted and separately verified synthetic profile Save tests remain permitted, as detailed in §14.

**A6. Cross-phase nonregression:** Phase 8.30 real Windows profile Save/Readback and Phase 8.29 fake-only owner/recovery security tests remain intact. Preserve frozen Phase 6 action authority and the explicit `--notepad` route. `compileall`, targeted tests, affected Windows tests and the full authoritative `unittest` suite must all pass from `C:\AI\mark-lii` with exit code 0.

**A7. Final assurance:** independently reviewed architecture and failure ledger; independent production and test reviews issue scoped GO with no unresolved HIGH/MEDIUM; exact staged manifest, SHAs, parent and whitespace checks; Windows seal-time and postcommit full suite; annotated product and separate documentation seals only when independently cleared and explicitly authorized for push; remote branch + tag-object + peeled-target verification; same-ID Drive master update verified or formally recorded as still outstanding.

## 7. Proposed controlled source envelope (requires RFC review before implementation)

- Add `nayeon/desktop_alpha/conversation_session.py` (typed session owner; pure Python with zero I/O).
- Narrow changes to `nayeon/desktop_alpha/application.py`, `workspace_window.py` and, if essential for truthful preview outcomes, `controller.py`.
- Add focused `tests/test_phase_831_session.py`, `tests/test_phase_831_workspace.py`, `tests/test_phase_831_effect_isolation.py` and test-only fake support as needed.
- Add RFC / security review evidence and append-only failure-review notes. The only authorized historical source-guard migration envelope and exact replacement invariant are defined in §13 below. No other older source-guard edit or future-phase exemption is permitted by this RFC.

Explicitly excluded from modification: Phase 8.30 `presentation_profile_owner.py`, presentation config/persistence, old `--notepad` implementation, live provider/credential/onboarding, policy, audit, native-mutex and computer-control production modules. Any newly necessary edits require an independently reviewed scope revision and user authorisation.

## 8. Open Failures & Prior-Issues Review at proposal entry

- Phase 8.29 fake-only late-Tk-effect, alternate candidate validation and staged/committed index source-bypass defects were sealed after adversarial tests and scoped independent GO. Preserve all their tests; no live provider assurance follows.
- Phase 8.30 Windows native junction/ACL/LockFileEx/write-uncertainty and Tk stale-callback work passed scoped review and full suite. These are NOT an authorization to reuse the profile store for conversation transcripts.
- A temporary 8.30 unittest launch from the wrong working directory failed; authoritative rerun from repository root passed 2,467/2,467. Require correct working directory explicitly.
- No current confirmed unrepaired Phase 8.31-specific defect is established by this **static proposal**. Its own dependency audit, reference/code inspections, adversarial reproductions and independent review remain **OPEN**. If new HIGH/MEDIUM or unknown root cause appears: HOLD.
- The existing original Drive macro-enabled master (ID `1n0tDiBQCkPWluX6eakRiRfq57tflRW5L`) received the bounded Phase 8.30 evidence in place on 16 October 2026. Same-ID raw readback matched the prepared 178,431-byte 16-sheet XLSM byte-for-byte (SHA-256 `06ac6ebde873a760f6e939969701bc5fad4b4d7ff320ad4fdb96a9c5b7a1fe02`). No replacement master was created. Phase 8.31 work has not yet been recorded in the master.

## 9. Rollout and stop conditions

1. **G0:** Preserve Phase 8.30 verified HEAD/tag/worktree; reverify no other writer; read latest ledger and all affected source/test guard paths.
2. **G1:** Independent GPT-6.1 Sol High RFC review if available; issue written GO/HOLD. If model unavailable, use a genuine independent review alternative without claiming the unavailable model ran.
3. **G2:** Implement pure in-memory session owner and focused RED→GREEN tests; no production provider/effect imports. Keep source envelope exact.
4. **G3:** Integrate one-root conversation view and real Tk event tests under synthetic-only conditions. Repeat attack/failure review and correct before moving forward.
5. **G4:** Test-only fake completion race and side-effect tripwires; affected/cross-phase and full authoritative Windows regression; independently review final scope.
6. **G5:** Only after GO, execute exact staged/product seal, postcommit test, approved push/tag + peeled verification. Documentation seal separately if needed. Workbook reconciliation uses original ID only.

**STOP:** unexplained failed/partial suite; unauthorised staged/index changes; concurrent writer; unreviewed changed trust boundary; UI/owner effect after revocation; transcript persistence; dependency reaching real SDK/secrets/native onboarding/action; uncertain rollback; missing independent review; process stalled five minutes without meaningful progress.

**Rollback:** stop active work and preserve evidence. Revert only uncommitted 8.31 changes after independent inspection and user-approved scope; never reset or move 8.30 or older immutable Git tags. If 8.31 receives a later seal, prepare an explicit forward-fix or new rollback commit rather than rewriting history.

## 10. Decision sought

**Recommendation:** GO to independent architecture review of this bounded Phase 8.31 RFC; **HOLD implementation** until scope and threat/acceptance gates receive a documented GO. Do not run actual provider calls, real credentials, autonomous actions or production profile writes. The first implementation increment after approval is the pure-Python, immutable, application-owned offline conversation-session owner with adversarial lifecycle tests, before any UI changes.

**Document status:** Planning draft only. No Phase 8.31 source/test edits, full-suite execution, review sign-off, Git seal, GitHub push or master Drive update are claimed by this draft.
## 11. Normative identity, submission and reset state machine — repair R1

These exact contracts supersede any looser Phase 8.31 descriptions above. They are requirements, not claims of implemented behavior.

- Each application owns a unique non-exported root identity. Every Conversation view has a separate exact view identity and monotonically increasing view generation. The application-owned conversation session independently has a unique session identity, session epoch and transcript revision. A view generation is NEVER a session epoch. Session owners are never chosen by display name, untrusted message or profile value.
- Production has no asynchronous model submission. A permitted submit is a synchronous, local transaction with exactly one active request ticket. States: ISSUED -> CLAIMED -> COMMITTED, or ISSUED/CLAIMED -> REVOKED. Only the active root + originating live view + exact session identity/epoch + request ticket may claim and commit once. Before committing, strictly validate the entire literal candidate and atomically reserve two transcript entries and their complete byte costs. The accepted USER entry and truthful LOCAL_STATUS / UNSENT_OFFLINE reply must be committed as ONE immutable in-memory revision. Duplicate Return/Send, stale completion or exception cleanup may not create a second entry, mark a request executed, or erase another ticket.
- Revalidate exact root/view/session/request identity AND transcript revision after every potentially reentrant validation, fake callback, Tk call, injected dependency or exception. A rendering exception after an owner commit may display a fixed error but cannot invent or undo a logical commit. If the view disappears before the owner commit, revoke only that matching ticket and do not modify a successor. Terminal close revokes all tickets/reviews and disposes views BEFORE root destruction. Child Destroy cannot close the owning application session.
- CLEAR and NEW_SESSION require different explicit human-facing commands. The exact one-use reset-review object binds root identity, originating view identity/generation, operation enum, current session identity/epoch, reviewed transcript revision and a fresh nonce/expiry. Any message append, other transcript mutation, navigation, dismiss, timeout, or view Destroy invalidates the pending review. The owner consumes the identical active review BEFORE clearing. CLEAR empties history, increments revision and invalidates all old request tickets. NEW_SESSION also changes session identity and increments session epoch. Callback A and any A exception cleanup may revoke A only by exact object identity; neither can consume a replacement review B even when epoch/text/digest are unchanged.
- Test-owned fake completions use a private typed lifecycle ISSUED -> QUEUED -> DELIVERED, or -> CANCELLED, with at most one queue item and deterministic Tk-thread dispatch. Fake delivery must match exact root, current session, epoch, ticket and revision. Double, late, reversed, cross-session or post-Destroy completion is ignored. Fake offline outcomes cannot be presented as AI, ChatOutcome.VERIFIED, execution proof or policy approval.
- Required mapped-Tk RED/GREEN negatives: same-session reset A/B replay, A stale after NEW_SESSION B, A exception cleanup while B is current, duplicate Send/Return, navigation and externally destroyed view during submit, nested update() and status rendering, late fake completion after close, and profile display-name change without authority transfer.

## 12. Normative input, retention and rendering limits — repair R3

- Require exact str, NFC-stable candidate or explicit rejection of a candidate needing normalization; nonempty after trimming; <=512 Unicode code points AND <=2048 strictly encoded UTF-8 bytes. Deny surrogate code points, malformed UTF-8, NUL, all Unicode Cc/Cf/Cs controls, CR/LF, U+2028/U+2029, bidi directional overrides/isolates and ANSI escapes. No hidden change of submitted text. Count supplementary emoji as code points rather than UTF-16 units.
- Install Tk proposed-value validation for keyboard, paste, insert and programmatic Entry changes BEFORE copying whole input for owner admission; reject oversize proposed value without appending it. Validate again in the owner in case the widget is bypassed. Python/Tcl running hostile arbitrary same-process code is not a sandbox, so do not claim to prevent temporary memory use by unrelated malicious code. Negative tests cover supplementary characters, controls, embedded newline, paste exceeding each cap, surrogates, repeated rejection and programmatic insertion.
- Retain at most 64 entries (32 accepted user/status pairs), <=65536 aggregate UTF-8 entry payload bytes, a single active request, a single pending reset review, a single test-only queued completion and one bounded immutable display snapshot. BEFORE accepting a submission reserve TWO slots and the entire user plus fixed status cost; when full refuse without partial append, silent eviction, auto-clear or log. One trusted status label <=160 characters is replaced in place for repeated refusals; refusals do not grow transcript history.
- The authoritative owner, not a Tk Text widget, retains history. Remove existing silent 180-line UI truncation. User payloads and trusted fixed statuses must have separately styled/labelled noneditable display segments; multiline and bidi-imitation text are rejected. Presentation names only label widgets and cannot create trusted speaker/status identities. Render failures never forge operation outcomes.
- No transcript filesystem persistence, clipboard, analytics, logs, telemetry, imports, exports, provider calls, network or implicit sync. Presentation profile startup read-only load and separately human-reviewed synthetic 8.30 Save are explicitly outside the transcript ban.

## 13. Exact migration of historical scope protections — repair R2

The existing 8.30 source helper currently pins application.py and workspace_window.py, freezes controller.py, and rejects any new production module. A new source cannot be allowed merely by weakening that helper.

- Exact historical test files eligible for narrowly reviewed migration: tests/phase_8_30_scope_migration.py and tests/test_phase_830_scope_integrity.py only. New version-specific support: tests/phase_8_31_scope_migration.py and tests/test_phase_831_scope_integrity.py. The Phase 8.29 A01-A04 and index-bypass guards remain frozen. The fourteen older consumer test files that import the 8.30 helper remain unchanged by default: test_bound_credential_lifecycle.py, test_connection_reconciliation.py, test_credential_onboarding_composition.py, test_openai_canonical_client.py, test_presentation_configuration_bootstrap.py, test_presentation_configuration_document.py, test_presentation_configuration_persistence.py, test_presentation_configuration_service.py, test_presentation_configuration_view.py, test_presentation_identity_contracts.py, test_provider_connection_composition.py, test_provider_connection_service.py, test_provider_connection_startup.py, test_windows_credential_backend.py. Preserve test_phase_830_application.py and all prior acceptance suites. Any needed extra migration file must receive revised independent RFC GO before change.
- Exact production path envelope: NEW nayeon/desktop_alpha/conversation_session.py; CHANGED nayeon/desktop_alpha/application.py and nayeon/desktop_alpha/workspace_window.py; OPTIONALLY CHANGED nayeon/desktop_alpha/controller.py only if independently cleared as essential and exact existing ChatOutcome/ChatReply and Notepad semantics are preserved. No modifications to presentation_profile_owner.py, presentation_window.py, window.py, configuration/persistence, live provider, onboarding, policy, action, native Windows mutex or older immutable security sources.
- Assign reviewed exact normalized SHA-256, mode and import-closure pins to every approved new/modified production path. Full Git inventories must be checked before filtering for source paths; reject case/backslash/dot/space/colon ADS aliases, reparse ancestors and unexpected worktree/untracked/staged blobs. Keep existing historical source/tag assertions for frozen 8.30 snapshots rather than a generic future-phase exception.
- PRE-STAGE: exact protected 8.30 docs HEAD 8b2fecf00d48324a187d931156cfa463bbd0aa67, clean initial index and reviewed uncommitted sources only; enumerated HEAD/index/disk inventories. STAGED: unchanged protected parent, exact approved index/disk snapshot with pinned SHA and diff-check, staged independent GO. POSTCOMMIT: enforce exact newly authorized commit parent/tree/index/disk SHA and paths; deny rollback to any old 8.30 source after 8.31 HEAD advances. All earlier annotated tags remain immutable.
- Synthetic isolated-Git RED negatives are mandatory: unauthorized committed source, index/disk divergence, unapproved staged blob, module missing, old-source rollback, wrong parent/branch, symlink/reparse parent, case/ADS aliases, partial manifest. Preserve the actual 8.29 index-bypass and 8.30 entrypoint rollback adversarial guarantees. STOP if a genuine guard relaxation is needed, rather than bypassing or disabling an older test.

## 14. Bounded test-only composition and forbidden-effect evidence — repair R4

- Production OfflineWorkspaceApplication(root) still constructs the exact PreviewOnlyController itself and an offline-only session. No production factory/backend argument, CLI flag, environment variable, profile, wake name or message text can select test composition. Explicit --notepad remains unchanged. Never import tests.* from product modules.
- The only test-owned fake factory lives at tests/phase_831_fake_session_support.py; its FakeOfflineCompletionQueue and ProhibitedEffects counters are installed with scoped unittest.mock.patch.object inside tests/test_phase_831_effect_isolation.py and tests/test_phase_831_workspace.py BEFORE application creation. tests/test_phase_831_session.py drives pure owner state transitions with typed fake tickets. The normal application import/launch must never construct a provider SDK, WinCred backend, named onboarding mutex or device action path, including under intercepted failures.
- Patch the trusted known-folder resolver to a fresh owned temporary test root BEFORE constructing the real Tk app, as in Phase 8.30. Existing read-only presentation startup is ALLOWED and separately approved synthetic-profile Save remains ALLOWED. The zero-effect rule forbids transcript writes and unauthorized provider, credential, action, launch, network and native mutex attempts; it must NOT misclassify the legitimate presentation read path as forbidden.
- Fake completions are deterministic on the real Tk thread, never background workers. Tripwires count forbidden ATTEMPTS and separately completed effects; add a deliberate negative where a forbidden attempt raises and is swallowed, proving attempts remain observable. All mapped-Tk and fake tests use disposable data only and never real user presentation files or secrets.

## 15. Incident and prerequisite reconciliation — repair R5

| ID | Root cause and boundary | Retained proof / disposition |
| --- | --- | --- |
| 829-LATE-UI / ALT-VALIDATE | Post-destroy owner could reach fake backend or alternate validator | Fake-only RED to GREEN, Sol High scoped security GO, 2,393/2,393 full; CLOSED only for tested offline/fake boundary; retain root-reentrancy negatives |
| 829-INDEX-STAGED/COMMITTED | Working-tree/staged-only checks permitted unauthorized Git index/HEAD blobs | Full snapshot SHA and disk/index/HEAD checks; synthetic Git negatives and independent migration GO; CLOSED in 8.29 scope, new migration needs separate GO |
| 830 storage owner | Native junction, ACL, LockFileEx, stale read/write and view Destroy uncertainty | Disposable native Windows tests, independent source/security GO, 2,467/2,467 staged and postcommit; CLOSED in 8.30 scope; owner module frozen |
| 830 source-scope rollback / aliases | Source guard previously allowed staged/committed rollback and path aliases | Corrected full Git inventory and exact pins, synthetic rollback and alias tests; 8.30 scope CLOSED, 8.31 guard migration remains HOLD until separately proven |
| 830 wrong cwd | One suite launched outside repository and failed for environment reasons | Re-run from exact C:\AI\mark-lii exit 0, 2,467/2,467; environment incident CLOSED |
| 830 Drive upload | Former media-reference replacement failed | Same original Drive ID 1n0tDiBQCkPWluX6eakRiRfq57tflRW5L updated 2026-10-16T20:51:39.350Z; raw 178431-byte readback byte-identical to approved 16-sheet workbook, SHA-256 06ac6ebde873a760f6e939969701bc5fad4b4d7ff320ad4fdb96a9c5b7a1fe02; ADMIN CLOSED, local .codex addendum unsealed |
| 831-R1 through R5 | First independent Sol High RFC review detected five MEDIUM design specification gaps | Normative §§11–15 proposed for fresh independent review; PHASE_831_RFC remains HOLD; no 8.31 source/tests implemented or sealed |

The top controlling 16 October administrative paragraph of .codex/CURRENT_STATE.md supersedes only the old workbook-outstanding statement; the historical failed transfer remains intact. This revised RFC and the new admin paragraph are working-tree documentation, not a reviewed Git seal. Independent GPT-6.1 Sol High re-review must issue explicit GO on all five defects before implementation. A design GO is not implementation or release GO. No additional credentials, live providers, autonomous desktop actions, unscoped source-guard migrations or release metrics changes are permitted. Rollback must first revoke pending UI tickets and preserve unrelated work and every earlier tag.

## Phase 8.31 bounded Tk test-lifecycle amendment — 17 October 2026

**Scope amendment design gate:** Independent GPT-6.1 Sol High decision `TK_FIX_SCOPE=GO`, Windows Temp `nayeon_831_tk_scope_review_result_20261017.txt`. This explicitly extends the originally narrow test-edit envelope by **one historical test file only**, `tests/test_phase_830_workspace.py`, and the already-new `tests/test_phase_831_effect_isolation.py`. The existing 8.31 module `tests/test_phase_831_workspace.py` already has the main-thread teardown. No additional production source, historical source guard, security pin, runtime Tk or provider/action path is authorized. Prior Phase 8.30 commits, tags and their original blobs remain immutable. This amendment is a separate test-only fault-repair, not permission to weaken the old test assertions.

**Cause and RED:** Native Windows Python 3.12.10 full discovery intermittently aborted with `Tcl_AsyncDelete: async handler deleted by the wrong thread` during garbage collection inside an older pointer-observation worker. Isolated process `nayeon_831_gc_control_20261017.log` passed all 53 synthetic Tk tests but retained **19/54** weakly tracked Tk roots after test cleanup; forced worker-thread GC reproduced the same native abort. Independent module-selection control logs `nayeon_831_gc_selection_830_20261017.log` and `nayeon_831_gc_selection_effect_20261017.log` both reproduced exit `-2147483645` without their own module teardown.

**Bounded GREEN:** The three authorized test modules track their native test-created `Tk` roots by **weak reference only**. Each module-owned `tearDownModule` asserts the Python main/UI thread, runs one synchronous `gc.collect()` to finalize unreachable Tk interpreter graphs on their creation thread, rejects any surviving tracked root, and clears only its weakref list. Existing widget/app close, security assertions, fake-only tripwires and synthetic-profile isolation remain untouched. No production module imports the test cleanup and no GC suppression, exception swallowing, background worker or production routing is introduced.

**Exact RED→GREEN proof:** Repair child `nayeon_831_gc_repair_20261017.log` shows 54/54 roots retired before the harness's supplementary main-thread collection, worker GC zero, pointer 15/15 PASS and native exit 0. Two independent fresh-process combined runs in `nayeon_831_gc_repeat_1_20261017.log` and `_2_20261017.log` passed 68/68 each. Separate repaired module-selection logs `nayeon_831_gc_selection_830_repaired_20261017.log` (10/10 roots retired, 8 + 15 tests PASS) and `nayeon_831_gc_selection_effect_repaired_20261017.log` (18/18 roots retired, 19 + 15 tests PASS) both exit 0. The preceding unextended candidate had full discovery 2,565/2,565 PASS with native exit 0 and another native GC abort prior to this repair; neither result substitutes for an **authoritative full regression on the exact expanded test candidate**.

**Required closure:** Independent static security review of the exact three-file test-only repair; compile and whitespace checks, complete affected and full Windows regression with true native exit 0; full repository/source guard pre-stage/staged/postcommit checks; append-only failure ledger reconciliation and product/docs seals. Until those complete, **Phase 8.31 remains HOLD for sealing**. Limit claim to safe test-owned Tk teardown at the checked test-module boundary, not universal thread or Tcl safety.

## 17 October 2026 — Phase 8.31 completed bounded product acceptance (separate administrative docs seal pending)

**Current product authority:** commit `79f17ca5211d7e1a97ef99b83dd613885d693bef` is locally committed on branch `nayeon-v1`, direct child of protected 8.30 documentation HEAD `8b2fecf00d48324a187d931156cfa463bbd0aa67`. The annotated product tag `nayeon-v1-phase-8-31-offline-conversation-session-product-01` has local object `2db31d688c12f9a845d903a2d1db14a9d2aa7a5e`, peeling to exact product commit. Exactly 12 product/test files, independently reviewed; no documentation mixed into product commit.

**Scope and result:** a trusted per-application in-memory offline session persists between Conversation/Settings/Connection navigation, uses typed immutable bounded text/status pairs always `UNSENT_OFFLINE`, explicit confirmed NEW_SESSION/CLEAR and rejection of stale view/root/epoch/submit tickets. User text is not executed or sent. Tk rendering and keyboard/mouse admission, fake-only out-of-order completion and cancellation, and zero prohibited-effect attempts tested in temporary Windows fixtures. Real services/WinCred/keys/actions and release gates were not activated.

**Open Failures & Prior-Issues Review:** initial RFC five MEDIUM specification gaps repaired and independently reviewed `PHASE_831_RFC=GO`; owner/UI/source index and postcommit invariants independently reviewed; fake isolation MEDIUM test gaps, old AST name collision and docs-child rename-hiding deletion corrected without weakening historic guards. Test-owned Tk interpreter worker-GC native crash recovered via causal negative control (19/54 roots left alive → worker native crash), positive main-thread module collection (all roots retired), two targeted 68/68 passes and isolated 8.30 + fake-effect selections (10/10 and 18/18 root finalisation, pointer 15/15, native exit 0). Approved historical test-only scope amended solely for `tests/test_phase_830_workspace.py`; prior 8.30 tags immutable. No unresolved HIGH/MEDIUM in reviewed bounded product; limitation: no universal Tk/thread or malicious in-process attack sandbox.

**Test/seal-time evidence:** host Python 3.12 on Kristian compiled all changed modules; exact 12-file index, whitespace and parent checked. 117/117 staged and 117/117 postcommit focused PASS. Three complete authoritative final-candidate Windows suites: **2,565/2,565 pre-stage, staged and postcommit**, each native exit 0 (logs `nayeon_831_full_final_expanded_20261017.log`, `nayeon_831_full_staged_20261017.log`, `nayeon_831_full_postcommit_20261017.log`). Independent Sol High reviewed exact staged source SHA manifest, `PHASE_831_STAGED_SECURITY_REVIEW=GO`, Windows Temp `nayeon_831_staged_review_result_20261017.txt`; separate Sol High Tk static review GO. The separate documentation seal, GitHub remote branch and peeled tags, and existing same-ID macro workbook reconciliation are **not yet claimed complete by this section**.

**Formal programme classification unchanged:** Phase 8 in progress; 5/19 overarching major architecture phases and 0/12 end-to-end release acceptance gates. This is an offline-only engineering increment, not autonomous desktop agent shipping readiness, live API calls, or an installer. Proceed to next phase only under new scoped gates.
