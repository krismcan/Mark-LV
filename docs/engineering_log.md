# Nayeon v1 engineering log

## Evidence and dating

This record is derived from Git commits, changed paths, annotated milestone tags, current code, and the checked-in tests. Dates below are Git author dates (`git log --format=%as`), not inferred deployment or execution dates. Historical tags whose annotations say "verified" are recorded as historical verification claims; their original test transcripts are not present in the repository and were not reconstructed as facts. No historical live-provider checks were rerun for this baseline.

Reproduce the source inventory with:

```powershell
git log --reverse --format="%h|%as|%s" --name-only -- nayeon AGENTS.md tests docs
git for-each-ref 'refs/tags/nayeon*' --format="%(refname:short)|%(*objectname:short)|%(contents:subject)"
```

## Foundation history

| Author date | Commit(s), in history order | Repository change / milestone evidence |
| --- | --- | --- |
| 2026-09-13 | `64b515d`, `f11c163`, `1823e40` | Environment foundation, non-secret configuration service, and environment-backed secrets service. |
| 2026-09-14 | `8395adb`, `c76ac07`, `580ffac` | AI service and fake provider, OpenAI adapter, then Responses provider correction. |
| 2026-09-14 | `9995f60`, `46a0593`, `84cf9d6` | Task routing, capability registry, and registry integration with the router. |
| 2026-09-14 | `eec2d73`, `07d53c7` | Self-describing capability contract and discovery loader. |
| 2026-09-14 | `b28bea2`, `9052d4c`, `ac4c575` | Application service, open-app implementation, and retained executable capability implementations. `nayeon-v1-local-action-01` points to `ac4c575`. |
| 2026-09-14 | `2f7abcf`, `88f4c47` | Policy service and policy-protected executor. Tag: `nayeon-v1-policy-executor-01` at `88f4c47`. |
| 2026-09-15 | `31068f8`, `f79b47e` | Secure confirmation and executor integration. Tags: `nayeon-v1-confirmation-01`, `nayeon-v1-confirmation-executor-01`, respectively. |
| 2026-09-15 | `577e471`, `e3ca01a` | Permission service and permission enforcement through policy. Tag: `nayeon-v1-permissions-01` at `e3ca01a`. |
| 2026-09-15 | `6795fe7` | Structured audit service. Tag: `nayeon-v1-audit-01`. |
| 2026-09-16 | `cd35d09` | Executor audit integration. Tag: `nayeon-v1-audit-executor-01`. |
| 2026-09-16 | `db96331`, `292e2ab`, `ac45883` | Undo service, undo provider contract, and executor undo integration. Tags: `nayeon-v1-undo-01` at `db96331`, `nayeon-v1-undo-executor-01` at `ac45883`. |
| 2026-09-16 | `ab38168`, `4d6255b` | Undo action and routed undo capability. Tag: `nayeon-v1-routed-undo-01` at `4d6255b`. |
| 2026-09-17 | `1758a04` | Contextual conversational controls. Tag: `nayeon-v1-conversation-controls-01`. |
| 2026-09-17 | `0615682`, `ec7ec06`, `8ef4a52` | Intent model, resolver orchestration, and local interpreter. Tags: `nayeon-v1-intent-model-01`, `nayeon-v1-intent-resolver-01`, `nayeon-v1-local-intent-01`, respectively. |
| 2026-09-17 | `136d8d3`, `58ea673` | Semantic confidence threshold and semantic authority validation. Tags: `nayeon-v1-semantic-confidence-01`, `nayeon-v1-semantic-validation-01`, respectively. |
| 2026-09-18 | `e3bf98d` | AI semantic model adapter. Both `nayeon-v1-ai-semantic-adapter-01` and `nayeon-v1-real-semantic-01` point here. The latter's annotation claims real GPT-5.6 interpretation verification; this is tag evidence only, not a live-provider result reproduced here. |
| 2026-09-18 | `5f3412a` | Intent dispatch planning. Tag: `nayeon-v1-dispatch-plan-01`. |
| 2026-09-18 | `b10480f` | Optional structured capability contract. Tag: `nayeon-v1-structured-capability-01`. The executor remains on its legacy string interface. |
| 2026-09-19 | `0debb38` | Root `AGENTS.md` captures architecture, engineering rules, and the then-missing permanent test suite. |
| 2026-09-19 | `5043529` | Parser guard now converts blank semantic intents to unresolved results without weakening `SemanticModelResult`. Adds the discoverable test package and 14 parser regression tests. Tag: `nayeon-v1-semantic-blank-intent-fix-01`; its annotation records 14 passing tests, compilation, and diff checks. |

## 2026-09-19: permanent regression baseline

Milestone: `nayeon-v1-regression-baseline-01` (annotated). Commit message: `test: establish Nayeon regression baseline`. Resolve its exact commit with `git rev-parse 'nayeon-v1-regression-baseline-01^{}'`.

Started from the clean `nayeon-v1` checkpoint at `5043529ed474003b6f8bec965631cfe76624d154`, confirmed against the blank-intent-fix tag. The supplied resume hash had an extra character; no checkout or history change was needed.

Retained the 14 semantic parser tests unchanged and added 75 tests across intent models/resolution/authority, local interpretation, dispatch, structured contracts, permissions/policy, confirmation, undo, and executor trust boundaries. Tests use deterministic fake implementations, mocks, a controlled clock for expiry cases, and temporary paths for audit persistence. No production files changed.

Validation on the repository virtual environment (Python 3.12.10, Windows 11 AMD64):

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_intent tests.test_dispatch_structured` | 36 passed; initial sandbox launch was blocked, then approved execution succeeded. |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_policy_confirmation tests.test_undo` | 23 passed. |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_executor` | 16 passed. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 89 discovered, 89 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Platform and Python diagnostics passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` | Passed; staged additions also checked with `git diff --cached --check`. |

Python validation used approved execution outside the sandbox after the repository interpreter was blocked. No alternative interpreter or live provider was used. Full added-file diffs were reviewed before committing. No new production defect was exposed. These tests establish deterministic foundation coverage, not OS-effect verification or complete application coverage.

The next product milestone is recorded in [current_state.md](current_state.md): structured execution integration for OpenAppCapability while preserving `execute(str)`, followed by integration through the existing ActionExecutor trust boundary. It is not part of this regression-baseline change.

## 2026-09-20: structured capability execution

Milestone: `nayeon-v1-structured-execution-01` (annotated). Commit message: `feat: integrate structured capability execution`. Resolve the milestone commit with `git rev-parse 'nayeon-v1-structured-execution-01^{}'`.

Started from clean branch `nayeon-v1`, commit `60bf9bdb8c3ef4339e8a0f445bcfbbb900b9a7e6`, confirmed against the regression-baseline tag. The requested `services/application.py` path was found as `services/applications.py`.

OpenApp now validates exactly one `application` argument, rejects missing/unknown keys and non-string/blank targets, trims surrounding whitespace, and revalidates before calling the existing service. Its legacy `execute(str)` path is retained.

ActionExecutor adds explicit structured execute and approval entry points while sharing the existing permission/policy, execution, audit, and undo flow. Validation precedes policy. Isolated normalized snapshots bind pending actions to the original request, registered metadata, and implementation. Matching approval rechecks permission/policy; changed arguments, invalid input, changed registration, replay, expiry, and cross-path token use fail closed. ConfirmationService adds an optional opaque identity binding so legacy approval cannot redeem a structured action token, even through a different executor sharing the service. No structured arguments are serialized into confirmation bindings or audit records; structured validator/execution exception text is suppressed.

Added 7 mocked OpenApp tests, 23 structured executor tests, and 2 confirmation binding tests. The original 89-test baseline remains green. Focused validation ran 63 tests successfully, then the complete suite discovered and passed **121 tests, 0 failures, 0 errors, 0 skipped**. Tests use fakes/mocks and temporary audit paths; no real applications, providers, credentials, or network calls were used.

Validation on Python 3.12.10 / Windows 11 AMD64 using the repository `.venv`:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_open_app_structured tests.test_structured_executor tests.test_executor tests.test_policy_confirmation` | 63 passed after approved execution outside the sandbox; initial sandbox interpreter launch was blocked. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 121 passed. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Platform and Python diagnostics passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit. |

Full diff reviewed before commit. No broader architecture change was required. Remaining limits: explicit structured API rather than automatic intent orchestration, process-local sequential confirmation state, legacy undo contract, and no independent verification of OS outcomes or new memory layer. See [current_state.md](current_state.md) for the API and trust-boundary details.

## 2026-09-21: structured orchestration bridge

Milestone: `nayeon-v1-structured-orchestration-01` (annotated). Commit message: `feat: add structured orchestration bridge`. Resolve the milestone commit with `git rev-parse 'nayeon-v1-structured-orchestration-01^{}'`.

Started from clean branch `nayeon-v1`, HEAD `a16182874fcc1c5595f8e9bb06e5a1567f567fe2`. The existing annotated structured-execution milestone remained at `036b006779bb229f3435182c841c95a311b1776d`.

Inspection established that local OpenApp resolution emits `{"request": original_text}`, not a structured application target. Semantic resolution preserves model-produced arguments, and DispatchPlan copies those arguments without retaining IntentSource. A deterministic mapper was therefore needed, but no intent contract redesign was necessary.

Added a dedicated `StructuredOrchestrationBridge` in the agent layer for open_app only. It accepts DispatchPlan plus original text, checks current registry metadata and the structured implementation contract, constructs StructuredCapabilityRequest, and delegates once to ActionExecutor. It returns executor results unchanged; it neither calls a model nor executes a capability/service directly. Unresolved/stale/unregistered/unsupported plans are denied. Approved system controls remain dispatcher controls and are explicitly unsupported by this bridge rather than disguised as capabilities.

Mapping forwards only `application` when present, even if its value is invalid (the executor/capability then rejects it). All other model fields are discarded. Without `application`, the legacy `request` field must match the caller's original text exactly, and the text must have a recognized open/launch/start prefix. The new side-effect-free `OpenAppCapability.arguments_from_request` helper reuses its existing prefix parser. No `target` alias, arbitrary model dictionary, or AI conversion is introduced. Existing legacy execution and executor trust boundaries are unchanged.

Added 20 deterministic orchestration tests covering mapping, no direct execution, result preservation, rejection cases, real executor validation/permission/confirmation, and the full local resolver-to-mocked-service path. No real OS launch, network, provider, or credential access occurred.

Validation with the repository virtual environment, Python 3.12.10 / Windows 11 AMD64:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_orchestration tests.test_open_app_structured` | 27 passed; initial sandbox interpreter launch was blocked, then approved external execution succeeded. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 141 discovered, 141 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Platform and Python diagnostics passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit. |

Full diff reviewed before commit. No wider redesign or production defect was exposed. Remaining architectural gap: conversational session ownership of pending structured requests, approval/rejection, and system controls; the bridge is an explicit API, not UI integration. Independent verification and memory remain out of scope. Historical entries above are preserved.

## 2026-09-24: session orchestration foundation

Milestone: `nayeon-v1-session-orchestration-01` (annotated). Commit message: `feat: add session orchestration foundation`. Resolve the milestone commit with `git rev-parse 'nayeon-v1-session-orchestration-01^{}'`.

Started from clean branch `nayeon-v1`, HEAD `77ff6d962dc1531ede1010b1fc674ec06e801b0f`. The preceding structured-orchestration tag targets `e1945b494752b3a4ed87b42130e4e3636345357d`; that milestone and its tag are unchanged.

Inspection found that the bridge returned ExecutionResult containing a ConfirmationRequest (token, capability name, original text, timestamps), but no structured arguments. Structured approval requires token, Capability metadata, and StructuredCapabilityRequest; rebuilding that request from later model output would be unsafe. A small companion bridge API, `execute_with_pending`, now returns the unchanged result plus an isolated mapped candidate only when confirmation is required. Existing `execute` remains result-only. The candidate is captured before submission; it does not replace the executor's normalized snapshot or authority checks. Failure to copy a candidate is denied before submission without disclosing exception details.

Added `ConversationSession` in the agent layer. `request(text)` owns resolution, dispatch, bridge submission, and one pending action. Pending data is limited to token, copied capability metadata, copied original request/application arguments, and expiry. Approval submits that exact candidate to `approve_and_execute_structured` once, with no interpretation, dispatch, or reconstruction. Rejection/cancellation uses executor rejection. Terminal approval outcomes clear local state; replay and missing pending state fail safely. A second action cannot replace a pending action. Expired state is rejected before the next text request, or denied by the executor on approval.

The existing local control resolver maps undo/scratch-that to cancellation when confirmation is pending. The session supplies that context and handles `cancel_pending` outside capability execution. Inspection also found the existing routed undo path through legacy `UndoCapability`, `UndoAction`, and `UndoService`. This milestone leaves session `undo_last` explicitly unsupported rather than introducing a second legacy-confirmation lifecycle or bypassing that path. No system control becomes a structured capability request; the session does not call capabilities, services, or OS actions directly.

Added 30 session tests and 4 bridge companion-API tests, with real permission/confirmation/executor boundaries, fake semantic resolution, mocked application service, mutation attempts, registration changes, permission revocation, expiry, replay, and cancellation. Existing tests remain green. No live LLM, provider, credentials, network, desktop launch, or personal files were accessed.

Validation using the repository `.venv`, Python 3.12.10 / Windows 11 AMD64:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_session tests.test_orchestration tests.test_structured_executor` | Final focused run: 77 passed. Initial sandbox interpreter launch was blocked; approved external execution succeeded. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 175 discovered, 175 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Platform and Python diagnostics passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit. |

Complete diff reviewed before commit. No pre-existing production defect or checkpoint discrepancy was found. The session is a process-local, sequential API with no persistence or UI integration; trusted host code owns its lifetime and approval entry points. Broader capability orchestration, session undo, existing string-based structured undo, and host exception handling remain limitations. The next architectural gap is independent result verification; memory remains later. No verification or memory layer was implemented, and historical entries above are preserved.

## 2026-09-24: result verification foundation

Milestone: `nayeon-v1-result-verification-01` (annotated). Commit message: `feat: add result verification foundation`. Resolve the feature commit with `git rev-parse 'nayeon-v1-result-verification-01^{}'`.

Started from clean branch `nayeon-v1`, HEAD `a564c4747a20727e90261b26bf370e65b99f4e88`. Confirmed the session milestone tag targets `49c275d388d0a56d9c1a686d15ed9d6ca200864d`. The existing 175-test baseline was retained; prior tags and historical entries were not changed.

Inspection found a single ExecutionResult shared by legacy/structured execution and session passthrough, optional UndoProvider detection, isolated normalized structured snapshots, and audit events already ordered through execution and undo registration. The smallest integration was an appended verification field and optional capability-owned verification protocol, coordinated by the existing executor after execution. No session redesign, competing executor, changed token identity, or relocated OS side effect was needed.

Added VerificationStatus (VERIFIED, NOT_VERIFIED, INDETERMINATE), VerificationResult, VerificationProvider, and VerificationService. Execution status/succeeded remain execution-only; absent observers never imply a verified real-world outcome. The same implementation that executed receives isolated normalized structured request/output, or the original legacy string. Provider results are copied and revalidated; evidence must be plain JSON data. Missing providers, exceptions, invalid results, or isolation failure safely yield INDETERMINATE without changing execution history. Provider reasons/evidence must be non-secret; structural validation cannot certify their privacy or truth.

Consolidated only the executor's successful return paths to preserve existing undo messages and registration outcomes before verification. Verification cannot run on failed, denied, rejected, cancelled, expired, or still-pending actions. The new VERIFICATION_OUTCOME event is appended after existing execution/undo events and records status only, never provider text, arguments, output, or evidence. Existing audit persistence failure propagation remains unchanged. OpenApp itself is unchanged and has no verifier: a launch return is not proof of an observed application state.

Added 32 deterministic tests for all result states, safe defaults, invalid data, provider errors, copy isolation, normalized inputs, approval/replay/expiry/registration checks, unchanged undo, legacy execution, session approval without reinterpretation, cancellation, and safe audit content. Existing executor tests were adjusted only to expect the appended audit event, preserving their prior sequence assertions. No live model, credentials, network, or desktop actions were used.

Validation with the repository `.venv`, Python 3.12.10 / Windows 11 AMD64:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_verification tests.test_executor tests.test_structured_executor tests.test_session` | 101 passed. Sandbox interpreter launch was blocked; approved execution outside the sandbox succeeded. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 207 discovered, 207 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Platform and Python diagnostics passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit. |

Full diff reviewed for trust-boundary changes. No checkpoint discrepancy or broader redesign was required. Deferred: the first production observation provider, observation deadlines/permissions, asynchronous checks, persistence, broader orchestration, session undo, and memory. Recommended smallest next milestone: define an OpenApp observation contract for a narrow supported outcome, then implement service-owned read-only checking with deterministic fake evidence; ambiguous identities remain INDETERMINATE. No further milestone was implemented here and nothing was pushed.

## 2026-09-24: OpenApp observation foundation

Milestone: `nayeon-v1-open-app-observation-01` (annotated). Commit message: `feat: add open app observation verification`. Resolve the feature commit with `git rev-parse 'nayeon-v1-open-app-observation-01^{}'`.

Started from clean `nayeon-v1`, HEAD `86529b8d4a980b9334c31ceddd14924a08ca0005`, matching the annotated result-verification milestone. Inspection found no Nayeon application catalogue or process abstraction. Platform metadata only identified the OS. A mock diagnostic also confirmed that LaunchResult(success=False) previously produced EXECUTED and entered verification because OpenApp returned it normally. Work stopped for review; the user explicitly approved changing failed OpenApp launches in both structured and legacy paths to controlled execution failures. No suitable existing domain execution exception was found; built-in RuntimeError is sufficient, with a fixed message and no raw service error.

Added service-owned ApplicationDefinition, ApplicationObservation, and ApplicationState. Optional exact process metadata is immutable/copied and explicitly supplied by trusted code; the sole default identity is Notepad (`notepad` / `notepad.exe` -> `notepad.exe`). Unknown targets never infer process identities. ApplicationService.observe uses one read-only Windows Tool Help snapshot behind the service layer, without launching a helper or application. Complete enumeration permits exact positive/negative name evidence; invalid/empty/incomplete snapshots remain UNKNOWN. Handles are released, and process inventory never crosses the service boundary.

OpenApp now implements the existing VerificationProvider method. It uses the normalized structured target bound to a successful launch receipt, or the executed receipt target for legacy calls, and never reparses wording. OBSERVED_OPEN maps to VERIFIED, OBSERVED_CLOSED to NOT_VERIFIED, and unavailable/unsupported/malformed/ambiguous/error evidence to INDETERMINATE. Only canonical ID, configured process names, and state are returned as evidence; audit remains status-only. Reported launch failures now raise before verification. ApplicationService launch behavior, generic executor/coordinator, confirmation identity, undo, and session logic are unchanged.

Added 43 permanent deterministic tests (18 service/native-adapter tests and 25 capability/lifecycle tests), retaining all 207 existing tests unchanged. OS enumeration and launch APIs are mocked; no real application, network, credentials, or process inventory was accessed. The first focused run found case-sensitive validation of `.EXE` in new metadata; this was corrected and all subsequent validation passed.

Validation with the repository `.venv`, Python 3.12.10 / Windows 11 AMD64:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_application_observation tests.test_open_app_observation tests.test_open_app_structured tests.test_verification` | Final focused run: 82 passed. Sandbox interpreter launch was blocked; approved execution outside the sandbox succeeded. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 250 discovered, 250 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Platform and Python diagnostics passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit. |

Complete diff reviewed for architecture leakage. The observation criterion is configured executable-name presence at a snapshot instant, not window readiness, launch causation, or binary/path authenticity. Same-name processes and startup/exit races remain limitations. Recommended smallest next milestone is optional trusted executable-path identity hardening for the existing observed application. Polling, retries, asynchronous verification, WindowManager, vision/perception, other capability verification, and memory remain deferred. No further milestone was implemented and nothing was pushed.

## 2026-09-24: Focused OpenApp post-milestone hardening

Reviewed the two requested concerns from clean `nayeon-v1` at `3419166f7f34930dc6772be6ab652f283ae27dbf`. The annotated `nayeon-v1-open-app-observation-01` tag remains on that feature commit; this correction creates no new milestone tag.

No reusable capability/domain execution exception exists. ActionExecutor catches Exception and does not require RuntimeError. Added the narrow ApplicationLaunchError in the OpenApp capability, following the existing typed RuntimeError-subclass convention used by the unrelated SecretNotFoundError. Failed receipts still produce a fixed, non-sensitive error in both legacy and structured paths, reach FAILED through the unchanged executor, and never run verification.

A complete immediate snapshot cannot distinguish delayed startup from a failed launch. OpenApp therefore maps OBSERVED_CLOSED to INDETERMINATE, preserving snapshot evidence without claiming a trustworthy negative outcome. Exact configured presence remains VERIFIED; unsupported, missing, malformed, and failed observations remain INDETERMINATE. The service enum is retained for compatibility and documented as snapshot state only. No polling, sleeps, retries, timeout machinery, asynchronous work, or other architecture changes were added.

Adjusted the immediate-absence regression and added three tests covering typed failures in both capability paths, legacy absence, and confirmation-approved absence. Existing audit, undo, session, and generic verification coverage remains intact. Validation using the repository virtual environment (approved outside the sandbox after its interpreter launch was blocked):

- `.\.venv\Scripts\python.exe -m unittest -v tests.test_open_app_observation tests.test_application_observation`: 46 passed.
- `.\.venv\Scripts\python.exe -m unittest discover -v`: 253 discovered, 253 passed, 0 failures, 0 errors, 0 skipped.
- `.\.venv\Scripts\python.exe -m nayeon.environment`: Windows 11 AMD64 / Python 3.12.10 diagnostics passed.
- `.\.venv\Scripts\python.exe -m compileall -q nayeon`: passed.
- `git diff --check` and `git diff --cached --check`: passed before commit; complete diff reviewed.

Current-state documentation was corrected; historical milestone descriptions above are retained as history. No live launch or process enumeration was performed by tests. Nothing was pushed; work stops for review without starting another milestone.

## 2026-09-24: OpenApp identity hardening foundation

Milestone: `nayeon-v1-open-app-identity-01` (annotated). Commit message: `feat: harden open app verification identity`. Resolve the feature commit with `git rev-parse 'nayeon-v1-open-app-identity-01^{}'`.

Confirmed clean `nayeon-v1` at `ddce706e79f0f9434e9ebf424542b574a4617e61`; `git show --stat HEAD` confirmed exactly the two production files, one test file, and two documentation files in the preceding hardening commit. The observation tag remains at `3419166f7f34930dc6772be6ab652f283ae27dbf`. Reran the unchanged baseline: 253 discovered/passed, no failures/errors/skips. Read repository instructions, both state documents, observation/service/capability code, verification contracts, tests, environment abstractions, and audit integration; reported the proposed service-owned design before edits.

Extended ApplicationDefinition with optional copied `accepted_executable_paths`. No real installation path is established in this repository, so the existing Notepad names/aliases remain the sole default entry without a guessed path. Trusted host definitions can provide exact paths; missing metadata is INDETERMINATE without observation. Path normalization accepts absolute local drive-letter paths, converts separators, collapses duplicate separators, and lowercases using ntpath. It rejects ambiguous relative/device/UNC/dot-component/trailing-dot-space forms, streams, wildcards, environment references, controls, and non-executable paths. No filesystem lookup, environment expansion, raw-request inference, or registry catalogue was introduced.

The service-owned Windows adapter traverses one Tool Help snapshot and opens only exact name candidates with PROCESS_QUERY_LIMITED_INFORMATION. QueryFullProcessImageNameW reads each image path once using a fixed buffer; finally blocks close handles. The name-only helper remains for compatibility but cannot establish identity. ProcessIdentity objects and full paths remain internal to services. ApplicationObservation appends an ApplicationIdentity outcome; OpenApp maps it to the unchanged verification contract with canonical ID/state/identity-indicator evidence only. Audit remains status-only.

An exact name plus accepted normalized path yields VERIFIED. Nonempty candidates with readable, valid, consistent paths all outside the accepted set yield NOT_VERIFIED for the observed identities, not proof of permanent launch failure. Without a positive match, any unreadable/malformed/inconsistent identity makes the result INDETERMINATE. Single-snapshot absence remains INDETERMINATE. The typed launch error, successful legacy launch contract, permission/policy/confirmation, audit, undo, session, dispatcher, and generic verification/executor remain unchanged. No model, sleeps, polling, retries, asynchronous tasks, process mutation, or broader capability work was added.

Retained all 253 existing test methods, updating only two observation modules' fixtures to supply trusted paths and fake identity records. Added 32 permanent identity tests for positive/mismatch/inconclusive outcomes, normalization/rejections, multiple candidates, missing metadata, untrusted wording, safe evidence, isolation, query-only rights, buffer failure, and handle cleanup. All process APIs and launches were mocked; no real process enumeration, applications, credentials, model, or network calls occurred in tests.

Validation using repository `.venv`, Python 3.12.10 / Windows 11 AMD64 (approved execution outside the sandbox after interpreter launch was blocked):

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_application_observation tests.test_open_app_observation` | 46 existing focused tests passed with updated fixtures. |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_open_app_identity tests.test_application_observation tests.test_open_app_observation` | 78 passed. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 285 discovered, 285 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit; full diff reviewed. |

Remaining limits: exact lexical path identity is not signature/content authenticity, alias/reparse equivalence, launch attribution, or window readiness. Snapshot and path queries are not atomic. Recommended next small milestone is designing a bounded synchronous observation budget and temporal outcome criteria; no waiting/polling implementation was started. Window readiness, vision, memory, and other capabilities remain deferred. Existing tags are unchanged; nothing was pushed and work stops for human review.

## 2026-09-25: Bounded OpenApp observation timing

Milestone: `nayeon-v1-open-app-readiness-01` (annotated). Commit message: `feat: add bounded open app readiness verification`. Resolve the feature commit with `git rev-parse 'nayeon-v1-open-app-readiness-01^{}'`.

Started from clean `nayeon-v1` at `5870f636c7070ba4d2a23b02099a113af7c5ce22`, matching the annotated identity milestone. Reproduced the 285-test baseline with no failures/errors/skips. Inspection confirmed one verifier invocation after execution/undo handling, one ApplicationService observation, and no reusable injected sleeper/clock in Nayeon; confirmation tests patch datetime locally. Reported the service-local design before editing. No STOP condition or checkpoint discrepancy applied.

Added frozen ApplicationReadinessPolicy with defaults and hard limits of three attempts and 0.1 seconds between attempts. Trusted callers may shorten the count/delay; invalid/nonfinite values and booleans are rejected. ApplicationService accepts an injected sleeper (production default time.sleep); tests use Mock. No clock is needed because the bound counts attempts. Requested waits total at most 0.2 seconds; synchronous OS-call and scheduling time are not capped.

OpenApp now delegates once to `ApplicationService.observe_readiness`. The existing one-shot `observe` API remains and shares the unchanged identity-inspection body. Readiness pins the immutable definition and timing settings once, observes immediately, waits only between remaining attempts, and stops immediately on any trusted match. It never launches, resolves intent, remaps arguments, or writes audit events. Generic executor/verification/session/dispatch/policy and launch implementation are unchanged.

Absence and unreadable candidate identity can continue within the bound. Unsupported targets/platforms or missing metadata return INDETERMINATE without snapshots/waits. Malformed observation results, incomplete snapshots, observation exceptions, and sleeper exceptions stop inconclusively with suppressed error text. A first wrong-path observation does not stop the check: only trustworthy mismatches on every configured attempt preserve the existing narrow NOT_VERIFIED claim about observed candidates. Mixed absence/unreadable evidence and mismatches end INDETERMINATE; elapsed waits never establish a negative outcome. A later trusted match overrides earlier inconclusive or candidate-mismatch evidence.

Retained the 285 test methods, adapting the existing OpenApp observation fixture to the new delegation method with an injected fake sleeper and one-attempt policy. Added 41 tests for default/shorter bounds, first/second/final matches, no extra waits, mixed evidence, malformed/error paths, pinned metadata/settings, no re-launch, permission/policy/confirmation, audit, undo, session, and legacy behavior. First new-suite run had one test setup error calling nonexistent PolicyService.block; corrected the fixture to use the existing blocked-capabilities constructor, without changing policy production code. All subsequent validation passed. Tests perform no real sleeps, process inspection, application launches, network, credentials, or model calls.

Validation using repository `.venv`, Python 3.12.10 / Windows 11 AMD64 (approved outside the sandbox after interpreter launch was blocked):

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_open_app_identity tests.test_application_observation tests.test_open_app_observation` | 78 existing focused tests passed. |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_open_app_readiness tests.test_open_app_identity tests.test_application_observation tests.test_open_app_observation` | 119 passed. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 326 discovered, 326 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit; full diff reviewed. |

Remaining limits: no OS-call deadline, window-readiness proof, launch attribution, async/background verification, general retry infrastructure, WindowManager, vision, memory, or other capability verification. Recommended next small milestone is explicit validated trusted metadata configuration for one application, without automatic discovery. No workbook update or remote push; existing tags remain unchanged and work stops for human review.

## 2026-09-25: Trusted Notepad App Paths configuration

Milestone: `nayeon-v1-open-app-trusted-notepad-01` (annotated). Commit message: `feat: configure trusted notepad identity`. Resolve the feature commit with `git rev-parse 'nayeon-v1-open-app-trusted-notepad-01^{}'`.

Started from clean `nayeon-v1` at `86d9e9102916f69ea065cff45975e5c4f5fc4863`, matching the readiness milestone. The user approved Windows App Paths as the independent trust source after the earlier inspection stopped rather than guess an installed path. Inspection found no existing Nayeon registry abstraction. Reported the narrow service-local helper, precedence, validation and exact-file check before implementation; no STOP condition applied.

Default ApplicationService construction resolves only the default REG_SZ value of the exact Notepad App Paths key, using valid HKCU first or valid HKLM otherwise, in the process's default registry view. Existing lexical normalization rejects unsafe paths; exact basename notepad.exe and exact-file is_file are required. No auxiliary Path value, registry enumeration, filesystem search, PATH resolution or process-derived trust is used. The immutable ApplicationDefinition supplies both the configured absolute launch target and accepted executable identity. Canonical aliases and process name remain unchanged; receipt targets preserve existing request binding. Explicit definition injection remains supported without registry access or changed launch routing.

Missing/unreadable/invalid registrations leave trusted identity unavailable: existing launching remains compatible, verification stays INDETERMINATE without observation. A configured exact-target launch failure does not fall back and does not verify. Readiness, identity outcome semantics, generic executor/verification/session, permission/policy/confirmation, audit and undo contracts are unchanged. Only Notepad is configured. No real registration or installation path was inspected; no live launch or process query was performed. The current-state document includes an optional interactive manual check through the normal session boundary, requiring explicit confirmation.

Retained all 326 existing tests, making the empty-identity fixture explicitly inject name-only metadata to prevent real registry access. Added 33 permanent tests with fake registry/default-value reads, exact-file checks, launches, snapshots and sleepers. The first new test run exposed a fixture naming collision between fake Windows registry and capability registry (one failure, two errors); renamed the fake fixture without production changes. Subsequent focused and complete validation passed.

Validation with repository `.venv`, Python 3.12.10 / Windows 11 AMD64, approved outside the sandbox after interpreter startup was blocked:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_trusted_notepad tests.test_open_app_identity tests.test_open_app_readiness tests.test_application_observation tests.test_open_app_observation` | 152 passed. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 359 discovered, 359 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit; full diff reviewed. |

Registration trust is not binary authenticity; lexical identity, redirection, startup races, window readiness and launch attribution limits remain. Configuration is fixed for the service lifetime. The smallest recommended next milestone is opt-in real-Windows Notepad smoke validation, not further implementation. No workbook changes or push; previous tags remain unchanged. Stop for human review.

## 2026-09-25: Read-only filesystem foundation

Milestone: `nayeon-v1-filesystem-read-01` (annotated). Commit message: `feat: add read-only filesystem foundation`. Resolve the feature commit with `git rev-parse 'nayeon-v1-filesystem-read-01^{}'`.

Started from clean `nayeon-v1` at `f75d1283d54b5c8e50b4f33a7f12caf0314e5124`; the annotated trusted-Notepad tag resolves there and is unchanged. Reproduced all 359 baseline tests before editing. Kris reported a successful real-Windows OpenApp check: execution executed, verification verified, evidence `{'application_id': 'notepad', 'state': 'observed_open', 'identity': 'matched'}`. This is user-reported live validation, not an agent-run test; no exact test timestamp was supplied. OpenApp is accepted as the reference capability for current v1 scope and was not expanded.

Initial inspection stopped without edits because reparse-aware file opening had no existing contract and the bridge explicitly supported only open_app. The user approved structured-executor-only filesystem execution, deferring conversation/bridge integration, and approved a narrow service-owned Win32 helper with decisive identity validation and reading on the same handle. No generic layers or parallel request protocol were introduced.

Added ReadFileCapability and FilesystemService. The capability accepts only a StructuredCapabilityRequest path, validates lexically with no IO, requires dedicated read_file permission and confirmation through unchanged policy/executor services, and rejects legacy string execution. Strict path rules reject ambiguity, devices, UNC, traversal, variables, globs and streams; slash/drive-letter normalization preserves component case. Requests are limited to fewer than 260 UTF-16 units. A service-owned 64 KiB content limit and strict UTF-8/control filter bound the first text-only implementation.

Windows opens use CreateFileW OPEN_EXISTING, read access, FILE_SHARE_READ only, OPEN_REPARSE_POINT, BACKUP_SEMANTICS and OPEN_NO_RECALL. Explicit ancestor handles are inspected and retained without enumeration. The file opens once; GetFileType, GetFileInformationByHandle and normalized DOS GetFinalPathNameByHandleW must establish an ordinary, non-reparse, non-offline/non-recall object with exact requested path spelling. Case/short-name/redirected/unavailable identities fail closed. Only then does bounded ReadFile consume that same handle, with no reopen or fallback. All handles close on exit. Same-handle validation is authoritative, not a pathname precheck. No privileges are enabled or shell/external tools invoked.

Success returns a frozen path/text/byte-count/read-state result. Domain failures are typed, fixed-message FileReadError outcomes; the existing executor records FAILED and suppresses exception details. No new generic error transport was added. No VerificationProvider or second read is used: separate generic verification stays INDETERMINATE/no-provider after successful execution. Existing audit records capability/status only. PermissionService's existing default-allow behavior is unchanged; hosts can require explicit grants, and read_file always requires confirmation under its registered metadata.

Added 56 tests covering lexical validation, fake Win32 identity/redirection/reparse/error paths, handle cleanup, byte limits/growth, UTF-8/control rejection, registration, permission/policy/confirmation, snapshot binding, cancellation/replay, privacy, failure propagation and structured executor integration. One native Windows test creates and reads only its own temporary ordinary file; reparse scenarios are entirely simulated, requiring no admin rights or real links. All 359 previous tests remain unchanged and green. No production defect or further STOP condition was encountered.

Validation with repository `.venv`, Python 3.12.10 / Windows 11 AMD64, approved execution outside the sandbox:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_filesystem` | 56 passed. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 415 discovered, 415 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit; complete diff reviewed. |

Limitations: Windows/local ordinary text files only, conservative path spelling and sharing, no cloud/reparse support, no allowed-root sandbox or content secrecy classifier, no confirmation-time content-version binding, no generic structured failure transport, no synchronous OS-call deadline. ConversationSession and StructuredOrchestrationBridge remain unchanged and reject read-file execution. The smallest next milestone is a generic capability-owned argument-mapping extension design, preserving the executor boundary; no implementation of it was started. Listing, mutation, search, parsing, memory, vision/browser/voice/UI, packaging and onboarding are deferred. No workbook update or push; stop for human review.

## 2026-09-25: Generic capability argument mapping foundation

Milestone: `nayeon-v1-capability-argument-mapping-01` (annotated). Commit message: `feat: add generic capability argument mapping`. Resolve the feature commit with `git rev-parse 'nayeon-v1-capability-argument-mapping-01^{}'`.

Started from clean `nayeon-v1` at `6e7b61476f30833750a1cfc2ddfb3ad5f33cfda7`, matching the annotated filesystem-read milestone. Reproduced the unchanged 415-test baseline. The preceding design inspection made no edits; the user approved the optional mapping contract and conservative rejection of uncopyable non-JSON extras before implementation.

Kris reported both prior real-Windows smoke checks successful. OpenApp executed and verified with matched Notepad identity. Direct structured ReadFile initially required confirmation, then executed with state read, 34 bytes, separate verification indeterminate and zero undo entries; the temporary smoke files were removed. These are user-performed results without supplied exact timestamps, not tests repeated by this agent or evidence of a live conversational read.

Added independent runtime-checkable IntentArgumentMapper with `map_intent_arguments(arguments: Mapping[str, Any], *, original_request: str) -> dict[str, Any]`. StructuredCapability retains exactly its previous execution/validation requirements. Registry and discovery are unchanged. A mapper is trusted implementation code required to be deterministic, side-effect free and safe on untrusted candidates; method-presence detection does not establish plugin trust. It performs no service/OS/model calls, authorization or full argument validation.

The generic bridge now requires both protocols and delegates mapping without imports, allowlists or fields specific to OpenApp/filesystem. It copies incoming arguments, checks dict output, copies mapped candidates, builds the existing request itself, saves isolated pending snapshots and rechecks current metadata/implementation after preparation. Missing mapper, exceptions, invalid returns, copy failures or changed binding deny preparation with fixed non-sensitive reasons and no execution/legacy fallback. Normalized validation and policy/confirmation remain in the unchanged executor.

OpenApp's existing explicit application precedence, extra-field discard, exact original-request fallback match and open/launch/start parsing moved into its mapper; its validation/execution/legacy APIs and all application service/trust behavior remain intact. ReadFile uses explicit path precedence or exact original-text match plus only the read-file prefix; invalid explicit values still reach authoritative validation. Its new intent pattern uses existing local routing. No filesystem path semantics or IO entered the bridge. FilesystemService and its handle-security behavior are unchanged.

ConversationSession runtime is unchanged (docstring corrected). Mapping occurs once during preparation; approval submits the stored request without resolution, dispatch, mapping or parsing. Permission/policy rechecks, changed-registration rejection, token expiry/replay, cancellation, audit privacy, undo and separate verification semantics are preserved. ReadFile has zero service calls before approval or on cancellation, one after approval, and INDETERMINATE/no-provider verification without rereading.

Added 33 deterministic mapping tests, including a synthetic third capability, mapperless direct execution, input/output isolation, registration changes during preparation and ReadFile's full session lifecycle. Updated two former OpenApp-only bridge expectations to the approved optional-mapper behavior. The first full run discovered 448 tests with one failure: a synthetic verification-session fixture lacked the now-required mapper, so it never reached confirmation. Updated that session-only fake to use real OpenApp mapping, strengthened pending assertions and added a no-remapping guard; no verification production change was needed. All subsequent tests passed. Existing test methods were retained. New tests use fake services, no personal files, real applications, models or network. The full baseline retains its previously approved self-created native temporary-file test.

Validation using repository `.venv`, Python 3.12.10 / Windows 11 AMD64, approved outside the sandbox:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_dispatch_structured tests.test_orchestration tests.test_open_app_structured tests.test_filesystem tests.test_session tests.test_argument_mapping` | 161 passed: 11 contract, 24 bridge, 7 OpenApp structured, 56 filesystem, 30 session, 33 mapping. |
| `.\.venv\Scripts\python.exe -m unittest -v tests.test_verification tests.test_argument_mapping` | 65 passed. |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 448 discovered, 448 passed, 0 failures, 0 errors, 0 skipped. |
| `.\.venv\Scripts\python.exe -m nayeon.environment` | Passed. |
| `.\.venv\Scripts\python.exe -m compileall -q nayeon` | Passed. |
| `git diff --check` and `git diff --cached --check` | Passed before commit; complete diff reviewed. |

Compatibility limit: copying the entire input can reject an uncopyable discarded extra that old OpenApp preparation ignored; this was explicitly approved. Preparation messages are generic, and preparation denial retains the existing no-execution-audit behavior. Mapping does not add concurrency, plugin isolation, a planner or new system controls. The smallest next milestone is opt-in live conversational ReadFile approval/cancellation validation on a user-created temporary file. Filesystem expansion, computer control, identity/configuration, BYOK, memory, vision/browser/voice/UI, installer, commercial backend and compliance automation remain deferred. Previous tags remain unchanged; no workbook update or push. Stop for human review.
