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
