# Nayeon v1 current state

## Checkpoint

- Branch: `nayeon-v1`.
- Current product milestone: `nayeon-v1-filesystem-read-01` (annotated), `feat: add read-only filesystem foundation`. Resolve the verified product commit with `git rev-parse 'nayeon-v1-filesystem-read-01^{}'`.
- Starting checkpoint and previous product milestone: `f75d1283d54b5c8e50b4f33a7f12caf0314e5124`, `nayeon-v1-open-app-trusted-notepad-01`; its tag remains unchanged.
- Kris reported the real-Windows OpenApp smoke test passed: execution `executed`, verification `verified`, evidence `{'application_id': 'notepad', 'state': 'observed_open', 'identity': 'matched'}`. OpenApp is the completed reference capability for current v1 scope. This report is user-provided live evidence, separate from automated tests; no OpenApp expansion was made.
- Historical checkpoint and validation details are retained in [engineering_log.md](engineering_log.md).
- `ConversationSession` owns the sequential request and pending-confirmation lifecycle for `open_app`. ActionExecutor remains the trust boundary; legacy successful execution and semantic parser behavior remain supported. The earlier approved failure-semantics change makes `LaunchResult(success=False)` a controlled failure in both execution paths, so the executor records FAILED and does not verify. Default Notepad aliases use the independently registered executable when available, as established by the preceding trusted-Notepad milestone.
- Execution completion and outcome verification remain separate result fields. OpenApp delegates bounded read-only identity observation to ApplicationService after successful execution. Missing trusted paths, unsupported observations, and inconclusive exhaustion remain INDETERMINATE. Observation never relaunches the application.

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
| Application observation | ApplicationService owns trusted identity and a bounded readiness check: at most three single-snapshot attempts, with at most two 100 ms requested waits. OpenApp delegates once and maps the final typed outcome; all generic layers remain free of timing/identity logic. |
| Read-only filesystem | ReadFileCapability accepts only a structured explicit path; FilesystemService validates Windows handles and reads bounded UTF-8. Permission and confirmation are required through the existing executor. Session/bridge execution of file reads is deliberately unsupported. |
| Services and support | Platform-aware application service, capability registry/discovery, environment diagnostics, non-secret configuration, environment-backed secrets, audit service, and bounded in-memory undo service exist. |

## Regression status

Validated on 2026-09-25 with the repository `.venv`, Python 3.12.10 on Windows 11 (AMD64): **415 discovered, 415 passed, 0 failures, 0 errors, 0 skipped**. Subtest cases are additional cases within these 415 test methods.

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
| `tests/test_open_app_identity.py` | 32 | Exact paths, normalization, multiple candidates, missing/malformed/unreadable identity, conservative mismatch, metadata/request isolation, minimal evidence, fake Windows query rights and handle cleanup |
| `tests/test_open_app_readiness.py` | 41 | Attempt/wait limits, delayed success, mixed evidence, failures, pinned metadata, fake sleeper, no relaunch, confirmation/session flow, safe single audit outcome, unchanged undo |
| `tests/test_trusted_notepad.py` | 33 | Fake App Paths precedence, exact-file validation, rejected paths, frozen launch/observation identity, fail-closed verification, trust boundaries, audit, undo, session and legacy behavior |
| `tests/test_filesystem.py` | 56 | Strict paths, fake Win32 reparse/identity failures, same-handle bounded reads, typed failures, permission/confirmation, audit privacy, structured execution, and one native self-created temporary-file read |

Validation commands (run from the repository root):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m nayeon.environment
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
```

All passed. Python required approved execution outside the Windows sandbox; no alternate interpreter was substituted. The focused filesystem suite passed all 56 tests. Tests make no real LLM calls, network requests, credential accesses, application launches, or desktop changes. Fakes and mocks remain in memory; audit persistence uses a temporary directory. One Windows test creates, reads and removes its own ordinary temporary file using the native service; no personal files or real symlinks/junctions are used. That native test is explicitly skipped on non-Windows hosts. The real permission and confirmation services remain in the executor tests.

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

- `ApplicationDefinition` remains trusted service-owned metadata: canonical identifier, explicit accepted launch targets, expected executable basenames, and optional `accepted_executable_paths`. Paths are copied into an immutable normalized tuple, and each basename must match a configured process name. Notepad is the first production application configured from an independent trust source: Windows App Paths. The sole default entry remains `notepad`, aliases `notepad` / `notepad.exe`, process `notepad.exe`. Explicit `ApplicationService(applications=...)` injection remains supported and does not consult the registry or change its legacy launch routing. Neither raw user wording nor observed processes populate the trust list.
- Path normalization is lexical and deterministic: absolute local drive-letter paths only; convert `/` to `\`, collapse duplicate separators, and use `ntpath.normpath` / `normcase` for lowercase exact comparison. Reject relative/drive-relative paths, UNC/device forms, dot/parent components, trailing-dot/space components, trailing separators, control characters, wildcards, quotes, streams/extra colons, environment references, and non-`.exe` files. No expansion, filesystem resolution, fuzzy matching, substring matching, or parent-directory acceptance occurs. Multiple explicitly accepted installation paths are supported.
- `ApplicationService.observe(target)` returns the existing minimal observation with appended `ApplicationIdentity` (MATCHED, MISMATCHED, UNKNOWN); no full paths leave the service in that result. The adapter traverses one completed Tool Help snapshot and reads paths only for exact configured name candidates using `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` and `QueryFullProcessImageNameW` with Win32 path format. Each query uses one fixed buffer and no retry. Process and snapshot handles close in finally blocks. Invalid, empty, truncated, or incomplete snapshots remain UNKNOWN. See [Microsoft's path-query contract](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew).
- A single attempt reports MATCHED when at least one candidate has the exact configured process name and normalized trusted path; other unreadable candidates do not invalidate this positive evidence. MISMATCHED requires nonempty candidates from a completed snapshot, all with readable, well-formed paths and consistent basenames, and none matching any trusted path. Otherwise identity is UNKNOWN. These rules remain service-owned; temporal aggregation is described below.
- Structured verification uses the executor's normalized `application` bound to the successful LaunchResult target. Legacy verification uses the executed receipt target without reparsing wording. Unknown receipts do not trigger observation. OpenApp only maps the service-owned identity outcome; evidence contains canonical application ID, state, and a matched/mismatched/unknown indicator. No executable paths, process inventory, command lines, or environment data are returned as verification evidence. Audit remains status-only.
- A false launch receipt raises `ApplicationLaunchError("Application launch failed.")` without exposing its service message. Launch exceptions also remain execution failures. Both stop before verification/observation. Successful launch receipts retain the requested target, including the legacy string path. ActionExecutor, VerificationService, confirmation binding, undo, and ConversationSession are unchanged by trusted Notepad configuration.

## Trusted Notepad configuration

- `services/notepad_app_paths.py` is a narrow service helper, not a general registry/discovery abstraction. At default ApplicationService construction on Windows, it reads only the default value of `Software\Microsoft\Windows\CurrentVersion\App Paths\notepad.exe`: valid HKCU first, otherwise valid HKLM, using the process's default registry view. It never merges registrations or reads the auxiliary `Path` value. See [Windows App Registration](https://learn.microsoft.com/en-us/windows/win32/shell/app-registration).
- Require REG_SZ, the existing safe absolute-path normalization above, exact basename `notepad.exe`, and a read-only `Path.is_file()` check on that exact path. No environment expansion, PATH lookup, registry enumeration, directory scan, or alternative-path search occurs. Missing/invalid/unreadable registrations or files fail safely to unavailable identity; an invalid HKCU entry permits the explicit HKLM fallback.
- One immutable resolved definition supplies both accepted executable identity and the absolute launch target for configured aliases. Windows launches that executable once with Popen; the receipt retains the caller's alias for existing verification binding. A configured launch failure never falls back to another executable and never verifies. Registry changes do not refresh an existing service instance; construct a new service to resolve again.
- Missing registration, unsupported platform, or unavailable API leaves accepted paths empty. Existing launch behavior remains available, but verification is INDETERMINATE without snapshots or waits. Only Notepad is configured this way. No installed path has been guessed or read on the developer machine during this milestone.
- `trusted_notepad_path` exposes only the selected path for explicit host diagnostics. Verification evidence and audit still omit paths and registry contents. The approved registration is configuration trust, not binary/signature authentication; file replacement, launch redirection and lexical-path differences remain limitations.

## Bounded OpenApp readiness

- The call path remains ActionExecutor -> VerificationService -> OpenAppCapability.verify_result; OpenApp now calls `ApplicationService.observe_readiness(target)` once. The existing `observe(target)` API remains a one-shot, no-wait check. Both share the same private identity observation; no additional launch or generic retry framework exists.
- Frozen `ApplicationReadinessPolicy` defaults to `max_attempts=3`, `delay_seconds=0.1`. Trusted host code can select 1-3 attempts and a finite delay from 0 through 0.1 seconds; invalid types, booleans, nonfinite numbers, and larger bounds are rejected. First observation is immediate. A positive match stops immediately; waits occur only between remaining attempts, never after the last attempt. A zero delay does not call the sleeper. Maximum requested waiting is 0.2 seconds, plus synchronous OS call time and scheduling overhead; this is not a hard wall-clock deadline.
- ApplicationService accepts an injected `sleeper`, defaulting to `time.sleep`. Tests use a Mock sleeper and fake snapshots; no real sleeping occurs. Attempt counting requires no clock, timer, scheduler, background worker, or persisted state. The immutable definition and timing settings are captured once per readiness call, so every attempt uses the same canonical identity and accepted paths without reinterpreting raw wording.
- Any trusted identity match yields VERIFIED immediately, including after earlier absence, unreadable identity, or wrong-path candidates. A wrong-path candidate does not stop the readiness check. Only MISMATCHED evidence on every configured attempt yields NOT_VERIFIED, retaining the narrow claim about observed candidates rather than claiming the intended app cannot start later. Any mix of absent/unreadable identity with mismatches exhausts to INDETERMINATE. Expiry of the attempt budget alone never proves failure.
- Unsupported platform/target or missing trusted metadata returns INDETERMINATE before any snapshot or wait. Malformed observation results, unknown/incomplete snapshots, snapshot/provider exceptions, and sleeper exceptions stop immediately with INDETERMINATE. A complete snapshot whose candidates have unreadable/access-denied/malformed paths remains inconclusive and may be checked again within the bound; exceptions from the observation adapter itself are not retried. Error text is suppressed.
- Launch remains exactly once through Permission -> Policy -> Confirmation -> Execution. Failed/denied/pending actions never enter readiness observation. Approved and legacy execution use the same post-execution verifier. One final verification result passes through the existing audit boundary; attempts add no audit events, paths, inventories, or command lines. Existing undo state is unaffected.

## Read-only filesystem foundation

- `ReadFileCapability` registers as `read_file`, service `filesystem`, LOCAL, non-reversible, no LLM, and `requires_confirmation=True`. Only `ActionExecutor.execute_structured(capability, StructuredCapabilityRequest(text, {"path": path}))` is supported, followed by the existing bound approval API. Validation requires exactly one string `path` and performs lexical work only. Execution revalidates before calling FilesystemService once. Legacy `execute(str)` raises the fixed `STRUCTURED_REQUIRED` domain failure. No local intent patterns or conversational file-reading route are advertised; session, bridge, dispatcher, resolver, executor, policy, audit and verification implementations are unchanged.
- Path rules are deliberately narrower than general Windows filename support. Require a local absolute drive-letter path shorter than 260 UTF-16 code units. Convert `/` to `\` and uppercase the drive letter only; preserve exact component case. Reject empty/duplicate/trailing separators, relative/UNC/device forms, dot/parent components, trailing dots/spaces, DOS device names (including device stems with extensions), streams/extra colons, quotes, controls, surrogate characters, wildcards/glob brackets and `%`/`$` variable forms. Never expand, trim a filename, search, substitute or infer missing components. No executable-specific helper or OpenApp behavior was changed.
- Service-owned Win32 handling uses `CreateFileW` with OPEN_EXISTING, FILE_SHARE_READ only, FILE_FLAG_OPEN_REPARSE_POINT, FILE_FLAG_BACKUP_SEMANTICS (for directory inspection), and FILE_FLAG_OPEN_NO_RECALL. No privileges are enabled. It checks only the supplied drive and exact ancestors, without enumeration: GetDriveTypeW allows fixed/removable/RAM local drives, then each explicit directory is opened with FILE_READ_ATTRIBUTES and retained until completion. The target is opened once with GENERIC_READ. Sharing conflicts fail closed; neither write nor delete sharing is granted. All acquired handles are closed through ExitStack on success or failure.
- Every opened handle is checked with GetFileType and GetFileInformationByHandle. Reject non-disk objects, wrong file/directory types, reparse attributes, offline and recall attributes. GetFinalPathNameByHandleW requests normalized DOS identity with a fixed buffer and no retry. Require the expected `\\?\` DOS prefix, remove only that API prefix, normalize drive-letter case, and compare the remaining path exactly with the requested spelling. Any different/truncated/unavailable identity is UNSAFE_PATH; no resolved target is substituted or exposed. This applies to final-component links and explicit ancestor junction/reparse handles. Conservative comparison can reject legitimate case, short-name, mount or alias paths.
- Crucially, ancestor inspection does not authorize content reading. The final opened file handle must independently pass its own type, attribute, final-path and size checks, and ReadFile consumes that same retained handle. There is no pathname reopen after validation, so a pathname check followed by opening a different object is not the security guarantee. See [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew) and [GetFinalPathNameByHandleW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew). This trusts the Windows filesystem APIs, not a hostile kernel/filesystem driver, and does not claim content-version binding from the earlier confirmation time.
- Maximum content is 64 KiB. Handle-reported sizes above the bound fail before reading. ReadFile uses a fixed 65,537-byte buffer; short reads may continue on the same handle within that byte budget, with one overflow byte detecting growth. No streaming beyond the bound, reopening, fallback or reread for verification occurs. Strict UTF-8 decoding preserves newline/BOM characters; reject decode errors and C0 controls except tab/CR/LF, plus DEL/C1 controls. This deterministic text filter is not general format detection: a byte sequence satisfying UTF-8/text rules is accepted regardless of extension. No PDF/Office/archive/image parser exists.
- Success is frozen `FileReadResult(path, text, byte_count, state="read")`; its repr omits sensitive fields. The result intentionally returns approved content to its caller. `FileReadError.failure` is a FileReadFailure enum: NOT_FOUND, ACCESS_DENIED, INVALID_TARGET, UNSAFE_PATH, TOO_LARGE, UNSUPPORTED_CONTENT, UNSUPPORTED_PLATFORM, BUSY, READ_ERROR or STRUCTURED_REQUIRED. Service exceptions have fixed messages without OS text or resolved paths. The unchanged structured executor maps raised failures to generic FAILED without retaining the typed exception in ExecutionResult; typed detail is the service/capability domain contract, not a new executor error protocol.
- Dedicated permission `read_file` is evaluated by the existing permission service, then policy, then mandatory capability confirmation; approval rechecks permission and policy. As before, PermissionService defaults to allowing unspecified names unless the host configures `default_allowed=False`; trusted hosts should use explicit grants. Confirmation remains mandatory even with that default. No capability-specific implicit grant or generic policy change was introduced. Cancellation/rejection and argument binding use existing executor APIs.
- Audit contains existing capability/status events, never path or contents. No VerificationProvider is added: the validated synchronous read is execution evidence, while the separate generic verification field remains INDETERMINATE/no-provider and is audited by status only. ReadFile is not repeated to manufacture verification evidence. No undo is registered because the capability changes no file content.

## Known gaps and limits

- `ConversationSession` exists as an explicit process-local agent API but is not yet wired into the legacy UI or a persistent host runtime. Trusted host code owns session lifetime and invokes approval/rejection entry points. Model output is never approval; executor exceptions remain the host's responsibility.
- Broader capability orchestration and session-level undo integration remain deferred. System controls stay outside the bridge's capability execution path; the session handles cancellation only.
- Intent/dispatch/request wrappers still copy dictionaries only at the top level. The new executor path deep-copies validated snapshots; capability-specific validators remain responsible for accepted types and deterministic, side-effect-free normalization.
- Protocol detection checks structural conformance, not correctness of validation or undo. These tests do not certify arbitrary plugins or model output.
- OpenApp verifies an exact trusted executable path and name, not binary content/signature, window readiness, foreground focus, or that this launch created the process. Snapshot enumeration and path reads are sequential, not atomic; startup/exit/PID-reuse races remain possible. Short-name, symlink, and reparse-point equivalence are not resolved: hosts must supply accepted lexical paths, and mismatch refers to that configured identity contract. No installation path is guessed; without a valid approved App Paths registration default Notepad remains INDETERMINATE. No Nayeon memory layer exists. Undo registration failure remains separately reported; failed undo callbacks are removed rather than retried automatically.
- Verifiers remain trusted synchronous capability code. OpenApp bounds observations and requested waits, but cannot interrupt a slow OS call and does not establish window readiness. There is no generic retry scheduler, asynchronous verification, background monitoring, or persisted evidence store.
- Structured undo retains `UndoProvider.build_undo(request: str, output)`. Reversible implementations must derive concrete undo from execution output/state; no structured undo contract was invented. OpenApp remains non-reversible.
- Pending approvals and their snapshots are process-local. The session owns at most one pending action and is explicitly sequential: no concurrency, persistence, database, cross-process recovery, or multi-session coordination guarantee. Executor binding checks still reject changed registrations. Session and bridge snapshots use deep copies; their Python objects are not a security boundary against code modifying private state.
- Filesystem scope is Windows ordinary local files only; non-Windows returns UNSUPPORTED_PLATFORM. Strict identity and restrictive sharing may reject otherwise readable files. Reparse-backed/cloud-placeholder paths are unsupported, hard links are not a content-authenticity boundary, and no allowed-root sandbox or secret-content detector is implemented. The host controls permission grants and disclosure of returned text. A bounded byte budget is not a wall-clock deadline for synchronous OS calls.
- Current validation is deterministic regression coverage plus one native temporary-file read, not end-to-end coverage of the legacy UI, live providers, OS application launching, all discovery/configuration paths, concurrency, or every possible malformed input. No provider or network behavior was exercised by this milestone. OpenApp live success is separately reported by Kris.

## Optional real-Windows manual check

Kris has reported this OpenApp check passed; the procedure is retained for optional future use and was not rerun during filesystem implementation. From the repository root in interactive PowerShell, run the block below. It reads the exact approved registration and checks the exact file, displays only the selected path, and stops without launch if no registration is usable. Type `YES` at the explicit confirmation to launch once through the normal session/executor boundary; any other response rejects. Audit stays in memory. Inspect the separate execution and verification statuses and minimal identity evidence; VERIFIED does not prove window readiness or that this launch created the process. Close Notepad manually afterward if desired; OpenApp has no undo.

```powershell
$manual = @'
from dataclasses import replace
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.services.applications import ApplicationService
from nayeon.undo.service import UndoService

service = ApplicationService()
print('Trusted Notepad executable:', service.trusted_notepad_path or 'unavailable')
if service.trusted_notepad_path is None:
    raise SystemExit('No usable registration; no launch performed.')
app = OpenAppCapability(service=service)
capability = replace(app.capability, requires_confirmation=True)
registry = CapabilityRegistry()
registry.register(capability, app)
permissions = PermissionService(default_allowed=False)
permissions.grant('open_app')
executor = ActionExecutor(registry, PolicyService(permissions), ConfirmationService(),
                          AuditService(), UndoService())
resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(registry)))
session = ConversationSession(resolver=resolver, registry=registry, executor=executor)
result = session.request('open notepad')
if result.status is ExecutionStatus.REQUIRES_CONFIRMATION:
    result = (session.approve_pending() if input('Launch Notepad once? Type YES: ') == 'YES'
              else session.reject_pending())
print('Execution:', result.status.value)
if result.verification is not None:
    print('Verification:', result.verification.status.value)
    print('Identity evidence:', result.verification.evidence)
else:
    print('Verification: not run')
'@
& .\.venv\Scripts\python.exe -c $manual
```

## Next intended milestone

Generic structured argument-mapping extension:
design a capability-owned deterministic mapping contract so the existing bridge can support read_file without embedding filesystem logic. Preserve executor validation, permission, policy, confirmation and stored-request binding. Conversational filesystem execution remains deferred until that separate milestone is approved and validated.

This is planning/state documentation only. Directory listing, writes/deletes/moves/copies, search/indexing, document parsing, memory ingestion, general retry infrastructure, asynchronous/background verification, WindowManager, vision, browser, voice, desktop UI, packaging and product onboarding remain deferred. No live application launch, process inventory or real sleep was used during this milestone's validation.

Keep Permission -> Policy -> Confirmation -> Execution, audit, undo, and backward compatibility intact. Read [AGENTS.md](../AGENTS.md) before further implementation.
