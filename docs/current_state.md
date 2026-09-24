# Nayeon v1 current state

## Checkpoint

- Branch: `nayeon-v1`.
- Current product milestone: `nayeon-v1-open-app-observation-01` (annotated), `feat: add open app observation verification`. Resolve the verified product commit with `git rev-parse 'nayeon-v1-open-app-observation-01^{}'`.
- Current follow-up: focused OpenApp hardening after the observation milestone; typed launch failure and conservative immediate-absence mapping. The product milestone tag remains unchanged.
- Previous product milestone: `nayeon-v1-result-verification-01` at `86529b8d4a980b9334c31ceddd14924a08ca0005`.
- Historical checkpoint and validation details are retained in [engineering_log.md](engineering_log.md).
- `ConversationSession` owns the sequential request and pending-confirmation lifecycle for `open_app`. ActionExecutor remains the trust boundary; legacy successful execution and semantic parser behavior remain supported. The approved compatibility change is limited to failed OpenApp launches: a returned `LaunchResult(success=False)` now raises a controlled failure in both execution paths, so the executor records FAILED and does not verify.
- Execution completion and outcome verification remain separate result fields. OpenApp now delegates read-only observation to ApplicationService for explicitly configured Windows process identities. Unsupported or unreliable observations remain INDETERMINATE.

## Architecture stage

Nayeon is a modular foundation alongside the legacy MARK application. The governing responsibilities remain:

```text
MODEL decides WHAT
AGENT decides HOW
POLICY decides WHETHER
SERVICE performs IT
VERIFICATION proves RESULT
MEMORY retains appropriate context
```

| Layer | Implemented state |
| --- | --- |
| Trust and execution | Permission checks feed policy; the executor applies policy, defers protected actions to confirmation, checks one-time capability/request-bound tokens, reevaluates policy after approval, and records audit events. Reversible actions require `UndoProvider` and register concrete undo callbacks. |
| Intent | Validated intent models; deterministic local routing and contextual cancel/undo controls; local-first resolution; configured local and semantic confidence gates; semantic authority limited to the registry and approved system controls. |
| AI parsing | Provider-independent AI service and semantic response adapter. Malformed response fields, including blank intents, return unresolved results. The result model's non-empty-intent invariant remains enforced. |
| Dispatch | `IntentDispatcher` maps resolved intents to registered capabilities or approved system controls and leaves unsupported intents unresolved. Planning does not execute actions. |
| Orchestration | `StructuredOrchestrationBridge` maps an `open_app` DispatchPlan into a StructuredCapabilityRequest and calls ActionExecutor exactly once. It calls no model, capability execution method, or OS service itself. Other capabilities and system controls are explicitly unsupported. |
| Session | `ConversationSession` coordinates resolver, dispatcher, bridge, and executor; retains at most one isolated pending action; exposes explicit approval/rejection; and routes `cancel_pending` through executor rejection. `undo_last` is explicitly unsupported by this session. |
| Structured capability | `OpenAppCapability` implements the optional `StructuredCapability` contract. It accepts only `application`, requires a non-blank string, trims surrounding whitespace, and revalidates before delegating to the existing application service. The executor validates before policy and runs structured actions through its shared trust boundary. |
| Verification | After execution and undo registration, ActionExecutor calls VerificationService with the implementation that executed. Optional `VerificationProvider.verify_result` owns domain observation; `ExecutionResult.verification` carries a separate status, reason, and copied JSON evidence. No provider means INDETERMINATE. A status-only audit event follows existing events. |
| Application observation | ApplicationService owns exact observation metadata and a single Windows Tool Help process snapshot. OpenApp maps typed service observations into the existing verification result; executor, VerificationService, session, policy, and intent code contain no new OS reads. |
| Services and support | Platform-aware application service, capability registry/discovery, environment diagnostics, non-secret configuration, environment-backed secrets, audit service, and bounded in-memory undo service exist. |

## Regression status

Validated on 2026-09-24 with the repository `.venv`, Python 3.12.10 on Windows 11 (AMD64): **253 discovered, 253 passed, 0 failures, 0 errors, 0 skipped**. Subtest cases are additional cases within these 253 test methods.

| Test module | Tests | Coverage |
| --- | ---: | --- |
| `tests/test_ai_semantic_model.py` | 14 | Retained deterministic parser tests, blank-intent fix, and result invariant |
| `tests/test_intent.py` | 25 | Intent model, local-first resolution, confidence, local interpretation, semantic authority |
| `tests/test_dispatch_structured.py` | 11 | Dispatch planning, argument isolation, structured request and protocol detection |
| `tests/test_policy_confirmation.py` | 17 | Permission/policy precedence, confirmation binding, replay, rejection, expiry, opaque action identity |
| `tests/test_undo.py` | 8 | Bounded LIFO undo, callback failures, registration validation, provider contract |
| `tests/test_executor.py` | 16 | Real policy/confirmation boundary with fake implementations, audit outcomes, undo integration, temporary JSONL persistence |
| `tests/test_open_app_structured.py` | 7 | Strict application arguments, no side effect during validation, mocked service delegation, legacy compatibility |
| `tests/test_structured_executor.py` | 23 | Structured validation/policy/confirmation/execution, snapshot isolation, legacy-token separation, replay, expiry, audit redaction, undo, mocked OpenApp integration |
| `tests/test_orchestration.py` | 24 | Bridge mapping, rejected plans, unchanged executor results, isolated pending snapshots, local resolver-to-executor flow, and real validation/policy/confirmation with mocked launch service |
| `tests/test_session.py` | 30 | Local/semantic request lifecycle, exact stored approval, rejection/cancellation, mutation isolation, registration/permission changes, expiry, replay, and unsupported undo with no side effects |
| `tests/test_verification.py` | 32 | Result/protocol validation, three outcome states, unavailable/failed observers, normalized-request and evidence isolation, confirmation timing, undo, legacy execution, unchanged session approval/cancellation, and status-only audit |
| `tests/test_application_observation.py` | 18 | Exact metadata, unknown/unsupported targets, complete versus incomplete snapshots, mocked Windows enumeration, handle cleanup, safe minimal observations |
| `tests/test_open_app_observation.py` | 28 | Positive/inconclusive observations, typed failed launches, real trust boundaries with mocked OS/service calls, canonical identity, legacy compatibility, session approval/cancellation, audit safety |

Validation commands (run from the repository root):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m nayeon.environment
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
```

All passed. Python required approved execution outside the Windows sandbox; no alternate interpreter was substituted. Focused runs for each new group also passed. Tests make no real LLM calls, network requests, credential accesses, application launches, or desktop changes. Fakes and mocks remain in memory; audit persistence uses a temporary directory. The real permission and confirmation services remain in the executor tests.

## Session lifecycle

`ConversationSession` owns the request lifecycle across IntentResolver -> IntentDispatcher -> StructuredOrchestrationBridge -> ActionExecutor -> pending confirmation -> trusted approval/rejection.

- Construct `ConversationSession(resolver=resolver, registry=registry, executor=executor)`. It constructs its dispatcher and bridge with that registry and executor. These are trusted application dependencies; the session does not expose approval methods as model tools.
- `request(text)` validates non-blank text, resolves with session-owned pending context, dispatches, and submits capability plans to the bridge. Only `open_app` is supported. It returns the bridge/executor result unchanged; unresolved and unsupported requests are safely denied.
- While confirmation is pending, another action is denied without replacing or executing the pending action. Requests can still resolve to `cancel_pending`. Text, including model-produced approval intent names, cannot invoke `approve_pending()`.
- The bridge's companion `execute_with_pending(...)` returns `OrchestrationResult(result, pending)`. Its existing `execute(...)` result-only API remains supported. The pending candidate contains only the token, copied capability metadata, a copied mapped StructuredCapabilityRequest (original text and application argument), and expiry time. It retains no plan, semantic extras, implementation, or conversational history. This candidate is not authorization: validated normalization, action binding, and the authoritative snapshot remain in ActionExecutor.
- `approve_pending()` consumes session state and calls `ActionExecutor.approve_and_execute_structured(...)` exactly once with the saved candidate. It does not resolve, dispatch, remap, or accept replacement arguments. Executor revalidation, registration checks, token binding, and permission/policy rechecks remain authoritative. Its result is returned unchanged; denial, mismatch, expiry, execution failure, and success all clear session state. Replay or approval without pending state is denied locally.
- `reject_pending()` clears session state and calls the executor's existing `reject(...)` with the exact saved token/capability. It returns that result unchanged without executing a capability. Rejection without pending state is safely denied. Expiry is also cleaned through executor rejection before the next text request; there is no background timer. `has_pending` reports retained local state until the next operation.
- `cancel_pending` uses `reject_pending()`. Existing contextual controls retain precedence: local undo/scratch-that wording cancels a pending action. With no pending action, unresolved cancellation or an explicit cancel control returns a deterministic denial.
- `undo_last` remains a system-control plan and is denied explicitly by the session; it never becomes a StructuredCapabilityRequest. Existing routed undo is `UndoCapability -> UndoAction -> UndoService` through legacy ActionExecutor execution. Supporting that path, including possible legacy confirmation, is deferred; this session never calls UndoAction or UndoService directly and supplies no undo-availability context. Other capabilities are not generalized.

## Structured orchestration and execution trust boundary

- Call `StructuredOrchestrationBridge(registry=registry, executor=executor).execute(plan, original_request=text)` after IntentResolver and IntentDispatcher. The bridge returns the executor's result unchanged, including denial, validation failure, or pending confirmation. It does not approve pending actions.
- Only current `open_app` capability plans with matching registry metadata and a `StructuredCapability` implementation are accepted. Unresolved, missing/stale capability, legacy-only implementation, unsupported capability, and system-control plans return `DENIED` without invoking the executor. These preparation rejections are not execution events; the bridge does not add a separate audit service.
- Mapping rule 1: if the plan contains `application`, forward only that field as a candidate, discarding all extras. Blank or non-string candidates still go to the existing capability validation and never trigger a legacy fallback.
- Mapping rule 2: otherwise, require the plan's `request` value to exactly equal the caller-supplied original request. `OpenAppCapability.arguments_from_request` reuses the legacy prefix parser to derive the same target for `open `, `launch `, or `start ` (case-insensitive after outer trimming). Unrecognized prefixes or missing/mismatched request text are rejected. No aliases such as `target` are guessed and no AI mapping is used.
- DispatchPlan carries arguments but no source field: local resolution currently emits `{"request": original_text}`, while semantic resolution preserves arbitrary model argument dictionaries. The bridge does not infer provenance from those fields; its local argument mapping requires matching original text and a deterministic launch prefix. No legacy execution fallback occurs. Capability validation, permission, policy, and confirmation remain authoritative.
- Call `ActionExecutor.execute_structured(capability, StructuredCapabilityRequest(original_request, arguments))`. For OpenApp the arguments are `{"application": "Example App"}`. Dispatch remains planning-only; a caller can wrap its arguments in this request without granting them trust.
- The executor resolves authoritative capability metadata and implementation from the registry, deep-copies input, runs capability validation, and isolates the normalized result before permission/policy evaluation. Invalid input returns a failed result and an audit event without echoing validator exceptions or arguments.
- Protected actions return the existing `ConfirmationRequest`. Call `approve_and_execute_structured(token, capability=..., request=...)` to approve. Approval revalidates the candidate and compares normalized arguments, original request, registered metadata, and implementation identity against the saved snapshot. Equivalent normalized targets are the same action; changed targets, changed registration, invalid input, replay, or expired tokens cannot execute.
- `ConfirmationService` now accepts an optional opaque in-memory `binding` on creation/approval. Identity must match in addition to the existing capability/request checks. It contains no serialized arguments. This prevents redeeming a structured token through a legacy approval path, including another executor sharing the confirmation service. Legacy confirmations without a binding behave as before.
- Permission/policy are reevaluated after approval. Both paths share execution audit and undo registration. Structured validation/execution exceptions are reported without their potentially sensitive text. Pending snapshots are removed on approval/rejection; expired snapshots are pruned on subsequent structured calls.
- `execute(capability, request: str)`, `approve_and_execute(...)`, and `OpenAppCapability.execute(str)` remain supported. OS launch logic stays in `ApplicationService`; no model, dispatch, or policy code performs an OS action.

## Result verification semantics

- `ExecutionResult.status` and `succeeded` retain their execution-only meanings. EXECUTED means the capability returned without an execution exception, not that its domain outcome occurred. The executor does not reinterpret arbitrary output flags. OpenApp now translates its own `LaunchResult.success=False` into a typed ApplicationLaunchError (a RuntimeError subclass), preserving ApplicationService's existing return contract and keeping domain failure handling out of the executor.
- The appended `verification` field defaults to `VerificationResult(INDETERMINATE, "Outcome has not been verified.")`, preserving existing constructor arguments. FAILED, DENIED, and REQUIRES_CONFIRMATION results do not run verification. Approved actions verify only after their exact stored action executes; replay, cancellation, expiry, and denied approvals do not invoke a verifier.
- VERIFIED means a capability-owned check reports the requested outcome established. NOT_VERIFIED means a check reports the requested outcome was not established. INDETERMINATE means observation is unavailable or inconclusive, including missing providers, verifier exceptions, invalid results, or input/output isolation failure. None of these states changes execution history, output, undo registration, or execution status.
- `VerificationProvider` is an optional runtime-checkable protocol, following the UndoProvider pattern. Its keyword-only `verify_result(request=..., output=...)` receives a deep copy of the normalized StructuredCapabilityRequest associated with the executed action, or the unchanged legacy string, plus a deep copy of output. It may inspect evidence or use service-owned observation; it must not repeat the original action, perform another action, or call a model. Session, dispatch, policy, and planning acquire no verification authority.
- `VerificationService` copies and revalidates provider results. Evidence is limited to recursively copied plain JSON data with finite numbers and string dictionary keys. Providers must supply concise non-secret reasons and safe evidence; JSON validation cannot prove confidentiality or the truth of a provider's claim. Exception text is suppressed. Python protocol detection is not a sandbox for untrusted plugins.
- Verification runs synchronously after successful execution and any undo-registration outcome, using the same implementation object that executed. It is observational and does not automatically retry, undo, or compensate. The appended `VERIFICATION_OUTCOME` audit event records the status only, including unavailable verification; arguments, output, provider reason, and evidence are not logged. Existing execution/undo event order is preserved. Audit persistence errors retain the existing propagation behavior.

## OpenApp observation

- `ApplicationDefinition` is trusted service-owned observation metadata: canonical identifier, explicit accepted launch targets, and optional expected executable basenames. It does not alter launch routing. The only default entry is identifier `notepad`, targets `notepad` / `notepad.exe`, and expected process `notepad.exe`. Matching is exact and case-insensitive, never fuzzy. Paths and arbitrary targets do not inherit this mapping by basename. Hosts may explicitly supply definitions through `ApplicationService(applications=...)` and inject that service into OpenApp; no external catalogue is loaded.
- `ApplicationService.observe(target)` returns `ApplicationObservation(target, state, application_id, expected_process_names)`. Known targets on Windows use one `CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)` and traverse it with Process32FirstW/Process32NextW. Normal completion is required before presence or snapshot absence is reported; snapshot absence alone does not establish a negative launch outcome. Invalid, empty, truncated, or incomplete reads are UNKNOWN, and snapshot handles are closed. There are no subprocess launches, process mutations, polling loops, retries, or background tasks in observation. API reference: [Microsoft Tool Help](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-process32firstw).
- OBSERVED_OPEN maps to VERIFIED only when a configured executable name exists in the completed snapshot. OBSERVED_CLOSED records only snapshot absence and maps to INDETERMINATE after a successful launch: the snapshot cannot distinguish delayed startup from failure. OpenApp currently has no trustworthy negative launch criterion and does not emit NOT_VERIFIED. UNKNOWN, unsupported platform/target, missing metadata, exceptions, malformed observations, or mismatched target evidence map to INDETERMINATE. Failure to observe is never negative evidence.
- Structured verification uses the executor's normalized `application` and requires it to match the successful LaunchResult target. Legacy verification uses the executed target in that receipt, without reparsing original wording. Unknown receipts do not trigger observation. The capability emits only canonical application ID, configured executable names, and observed state as evidence; it never returns a process inventory, command lines, or environment data. The existing audit event still stores status only.
- A false launch receipt now raises `ApplicationLaunchError("Application launch failed.")` without exposing its service message. Launch exceptions also remain execution failures. Both stop before verification/observation. Successful launch receipts remain unchanged, including the legacy string path. ApplicationService's launch implementation, ActionExecutor, VerificationService, confirmation binding, undo, and ConversationSession were not changed for this milestone.

## Known gaps and limits

- `ConversationSession` exists as an explicit process-local agent API but is not yet wired into the legacy UI or a persistent host runtime. Trusted host code owns session lifetime and invokes approval/rejection entry points. Model output is never approval; executor exceptions remain the host's responsibility.
- Broader capability orchestration and session-level undo integration remain deferred. System controls stay outside the bridge's capability execution path; the session handles cancellation only.
- Intent/dispatch/request wrappers still copy dictionaries only at the top level. The new executor path deep-copies validated snapshots; capability-specific validators remain responsible for accepted types and deterministic, side-effect-free normalization.
- Protocol detection checks structural conformance, not correctness of validation or undo. These tests do not certify arbitrary plugins or model output.
- OpenApp verification establishes only configured executable-name presence at the snapshot instant. It does not prove a visible/ready window, foreground focus, that this launch created the process, or executable binary/path authenticity. Same-name processes can satisfy this narrow criterion; startup and exit races remain possible. Other applications/platforms lack default observation metadata. No Nayeon memory layer exists. Undo registration failure remains a separately reported partial outcome after execution; undo callbacks that fail are removed from the stack rather than retried automatically.
- Verifiers are trusted synchronous capability code: this foundation adds no observation timeout, retry scheduler, asynchronous verification, or persisted evidence store. Provider-specific truth, privacy, observation permissions, and bounded observation behavior require review when a real provider is introduced.
- Structured undo retains `UndoProvider.build_undo(request: str, output)`. Reversible implementations must derive concrete undo from execution output/state; no structured undo contract was invented. OpenApp remains non-reversible.
- Pending approvals and their snapshots are process-local. The session owns at most one pending action and is explicitly sequential: no concurrency, persistence, database, cross-process recovery, or multi-session coordination guarantee. Executor binding checks still reject changed registrations. Session and bridge snapshots use deep copies; their Python objects are not a security boundary against code modifying private state.
- Current validation is deterministic regression coverage, not end-to-end coverage of the legacy UI, live providers, OS application launching, all discovery/configuration paths, concurrency, or every possible malformed input. No live OS, provider, or network behavior was exercised by this milestone.

## Next intended architectural milestone

Application identity hardening:
define optional trusted executable-path identity for the existing observed application and a service-owned read-only check that distinguishes same-name processes. Preserve INDETERMINATE for inaccessible or ambiguous identity; keep deterministic tests and the existing trust boundary.

This is planning/state documentation only. Polling/retries, asynchronous verification, WindowManager, vision/perception, other capability verification, and independent memory remain deferred. No live application was launched or OS process inventory inspected during this milestone's validation.

Keep Permission -> Policy -> Confirmation -> Execution, audit, undo, and backward compatibility intact. Read [AGENTS.md](../AGENTS.md) before further implementation.
