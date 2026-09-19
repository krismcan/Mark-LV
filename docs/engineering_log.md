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
