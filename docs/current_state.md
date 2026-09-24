# Nayeon v1 current state

## Checkpoint

- Branch: `nayeon-v1`.
- Current product milestone: `nayeon-v1-structured-orchestration-01`, `feat: add structured orchestration bridge`. Resolve its commit with `git rev-parse 'nayeon-v1-structured-orchestration-01^{}'`.
- Previous product milestone: `nayeon-v1-structured-execution-01` at `036b006779bb229f3435182c841c95a311b1776d`.
- Starting HEAD for this change: `a16182874fcc1c5595f8e9bb06e5a1567f567fe2` (documentation reconciliation). Historical checkpoint and validation details are retained in [engineering_log.md](engineering_log.md).
- Structured execution is now supported; legacy string execution and the existing semantic parser behavior remain supported unchanged.

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
| Structured capability | `OpenAppCapability` implements the optional `StructuredCapability` contract. It accepts only `application`, requires a non-blank string, trims surrounding whitespace, and revalidates before delegating to the existing application service. The executor validates before policy and runs structured actions through its shared trust boundary. |
| Services and support | Platform-aware application service, capability registry/discovery, environment diagnostics, non-secret configuration, environment-backed secrets, audit service, and bounded in-memory undo service exist. |

## Regression status

Validated on 2026-09-21 with the repository `.venv`, Python 3.12.10 on Windows 11 (AMD64): **141 discovered, 141 passed, 0 failures, 0 errors, 0 skipped**. Subtest cases are additional cases within these 141 test methods.

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
| `tests/test_orchestration.py` | 20 | Bridge mapping, rejected plans, unchanged executor results, local resolver-to-executor flow, and real validation/policy/confirmation with mocked launch service |

Validation commands (run from the repository root):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m nayeon.environment
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
```

All passed. Python required approved execution outside the Windows sandbox; no alternate interpreter was substituted. Focused runs for each new group also passed. Tests make no real LLM calls, network requests, credential accesses, application launches, or desktop changes. Fakes and mocks remain in memory; audit persistence uses a temporary directory. The real permission and confirmation services remain in the executor tests.

## Structured execution API and trust boundary

- Call `StructuredOrchestrationBridge(registry=registry, executor=executor).execute(plan, original_request=text)` after IntentResolver and IntentDispatcher. The bridge returns the executor's result unchanged, including denial, validation failure, or pending confirmation. It does not approve pending actions.
- Only current `open_app` capability plans with matching registry metadata and a `StructuredCapability` implementation are accepted. Unresolved, missing/stale capability, legacy-only implementation, unsupported capability, and system-control plans return `DENIED` without invoking the executor. These preparation rejections are not execution events; the bridge does not add a separate audit service.
- Mapping rule 1: if the plan contains `application`, forward only that field as a candidate, discarding all extras. Blank or non-string candidates still go to the existing capability validation and never trigger a legacy fallback.
- Mapping rule 2: otherwise, require the plan's `request` value to exactly equal the caller-supplied original request. `OpenAppCapability.arguments_from_request` reuses the legacy prefix parser to derive the same target for `open `, `launch `, or `start ` (case-insensitive after outer trimming). Unrecognized prefixes or missing/mismatched request text are rejected. No aliases such as `target` are guessed and no AI mapping is used.
- DispatchPlan carries arguments but no source field: local resolution currently emits `{"request": original_text}`, while semantic resolution preserves arbitrary model argument dictionaries. The bridge does not infer provenance from those fields; its legacy fallback requires matching original text and a deterministic launch prefix. Capability validation, permission, policy, and confirmation remain authoritative.
- Call `ActionExecutor.execute_structured(capability, StructuredCapabilityRequest(original_request, arguments))`. For OpenApp the arguments are `{"application": "Example App"}`. Dispatch remains planning-only; a caller can wrap its arguments in this request without granting them trust.
- The executor resolves authoritative capability metadata and implementation from the registry, deep-copies input, runs capability validation, and isolates the normalized result before permission/policy evaluation. Invalid input returns a failed result and an audit event without echoing validator exceptions or arguments.
- Protected actions return the existing `ConfirmationRequest`. Call `approve_and_execute_structured(token, capability=..., request=...)` to approve. Approval revalidates the candidate and compares normalized arguments, original request, registered metadata, and implementation identity against the saved snapshot. Equivalent normalized targets are the same action; changed targets, changed registration, invalid input, replay, or expired tokens cannot execute.
- `ConfirmationService` now accepts an optional opaque in-memory `binding` on creation/approval. Identity must match in addition to the existing capability/request checks. It contains no serialized arguments. This prevents redeeming a structured token through a legacy approval path, including another executor sharing the confirmation service. Legacy confirmations without a binding behave as before.
- Permission/policy are reevaluated after approval. Both paths share execution audit and undo registration. Structured validation/execution exceptions are reported without their potentially sensitive text. Pending snapshots are removed on approval/rejection; expired snapshots are pruned on subsequent structured calls.
- `execute(capability, request: str)`, `approve_and_execute(...)`, and `OpenAppCapability.execute(str)` remain supported. OS launch logic stays in `ApplicationService`; no model, dispatch, or policy code performs an OS action.

## Known gaps and limits

- The explicit open_app bridge is implemented and tested from local IntentResolver through DispatchPlan and ActionExecutor. It is not wired into the legacy UI or a new conversational session runtime. Callers still own resolution, planning, original request context, and the approval lifecycle.
- `cancel_pending` and `undo_last` remain approved dispatcher system controls but are explicitly unsupported by this first bridge. They never enter its capability execution path. Other capabilities are not generalized.
- Intent/dispatch/request wrappers still copy dictionaries only at the top level. The new executor path deep-copies validated snapshots; capability-specific validators remain responsible for accepted types and deterministic, side-effect-free normalization.
- Protocol detection checks structural conformance, not correctness of validation or undo. These tests do not certify arbitrary plugins or model output.
- No dedicated Nayeon result-verification or memory layer exists. Executor completion status is not independent proof of an OS outcome. Undo registration failure is a separately reported partial outcome after execution; undo callbacks that fail are removed from the stack rather than retried automatically.
- Structured undo retains `UndoProvider.build_undo(request: str, output)`. Reversible implementations must derive concrete undo from execution output/state; no structured undo contract was invented. OpenApp remains non-reversible.
- Pending approvals and their snapshots are process-local, and there is no new concurrency or persistence guarantee. The structured executor is intended for the existing sequential runtime, not concurrent registry mutation.
- Current validation is deterministic regression coverage, not end-to-end coverage of the legacy UI, live providers, OS application launching, all discovery/configuration paths, concurrency, or every possible malformed input. No live OS, provider, or network behavior was exercised by this milestone.

## Next architectural gap

Session-level orchestration remains: decide how a conversational runtime will retain pending structured requests, expose confirmation/rejection, and route system controls through their existing authority boundaries. That scope needs review before implementation. The deterministic local OpenApp argument mapping is now implemented; no intent contract change was required.

Independent result verification and Nayeon memory remain unimplemented and are not part of this milestone.

Keep Permission -> Policy -> Confirmation -> Execution, audit, undo, and backward compatibility intact. Read [AGENTS.md](../AGENTS.md) before further implementation.
