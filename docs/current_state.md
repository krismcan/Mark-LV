# Nayeon v1 current state

## Checkpoint

- Branch: `nayeon-v1`.
- Verified production/source checkpoint entering this milestone: `5043529ed474003b6f8bec965631cfe76624d154`, `fix: handle blank semantic model intents safely`.
- Previous annotated milestone: `nayeon-v1-semantic-blank-intent-fix-01` (points to that commit).
- Regression-baseline milestone: `nayeon-v1-regression-baseline-01`, commit message `test: establish Nayeon regression baseline`. Its exact commit is the dereferenced tag: `git rev-parse 'nayeon-v1-regression-baseline-01^{}'`. This avoids embedding a self-referential commit hash in the commit's own document.
- This milestone adds tests and documentation only. Production behavior and the existing semantic parser tests are unchanged.

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
| Structured capability | Optional runtime-checkable `StructuredCapability` contract separates argument validation from execution. `StructuredCapabilityRequest` normalizes request text and copies the argument mapping. This contract is not yet integrated into the executor. |
| Services and support | Platform-aware application service, capability registry/discovery, environment diagnostics, non-secret configuration, environment-backed secrets, audit service, and bounded in-memory undo service exist. |

## Regression status

Validated on 2026-09-19 with the repository `.venv`, Python 3.12.10 on Windows 11 (AMD64): **89 discovered, 89 passed, 0 failures, 0 errors, 0 skipped**. Subtest cases are additional cases within these 89 test methods.

| Test module | Tests | Coverage |
| --- | ---: | --- |
| `tests/test_ai_semantic_model.py` | 14 | Retained deterministic parser tests, blank-intent fix, and result invariant |
| `tests/test_intent.py` | 25 | Intent model, local-first resolution, confidence, local interpretation, semantic authority |
| `tests/test_dispatch_structured.py` | 11 | Dispatch planning, argument isolation, structured request and protocol detection |
| `tests/test_policy_confirmation.py` | 15 | Permission/policy precedence, confirmation binding, replay, rejection, expiry |
| `tests/test_undo.py` | 8 | Bounded LIFO undo, callback failures, registration validation, provider contract |
| `tests/test_executor.py` | 16 | Real policy/confirmation boundary with fake implementations, audit outcomes, undo integration, temporary JSONL persistence |

Validation commands (run from the repository root):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m nayeon.environment
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
```

All passed. Python required approved execution outside the Windows sandbox; no alternate interpreter was substituted. Focused runs for each new group also passed. Tests make no real LLM calls, network requests, credential accesses, application launches, or desktop changes. Fakes and mocks remain in memory; audit persistence uses a temporary directory. The real permission and confirmation services remain in the executor tests.

## Known gaps and limits

- `OpenAppCapability` and `ActionExecutor` still use `execute(request: str)`. Structured dispatch arguments do not yet flow through validation, policy, confirmation, and execution end to end.
- Argument isolation is a top-level dictionary copy, not deep immutability. Capability-specific argument validation is still required; accepted intent names and confidence do not prove arguments are safe.
- Protocol detection checks structural conformance, not correctness of validation or undo. These tests do not certify arbitrary plugins or model output.
- No dedicated Nayeon result-verification or memory layer exists. Executor completion status is not independent proof of an OS outcome. Undo registration failure is a separately reported partial outcome after execution; undo callbacks that fail are removed from the stack rather than retried automatically.
- This is a deterministic foundation baseline, not end-to-end coverage of the legacy UI, live providers, OS application launching, all discovery/configuration paths, concurrency, or every possible malformed input. No new production defect was exposed by this suite.
- The supplied resume SHA contained a typo. The actual starting SHA above was verified against both HEAD and the annotated blank-intent-fix tag; the branch and clean-tree expectations matched.

## Next intended product milestone

Structured execution integration:
migrate OpenAppCapability to validated structured arguments while preserving the legacy execute(str) path, then integrate structured execution through the existing ActionExecutor trust boundary.

Keep Permission -> Policy -> Confirmation -> Execution, audit, undo, and backward compatibility intact. Read [AGENTS.md](../AGENTS.md) before implementation. This baseline milestone does not implement the next milestone.
