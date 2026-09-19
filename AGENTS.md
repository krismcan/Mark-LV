# Nayeon v1 engineering instructions

## Scope and session startup

- Read the relevant architecture, implementation, and existing tests before making decisions or edits.
- Check the branch, latest commit, milestone tags, and working tree against the user's expected checkpoint. Report discrepancies; do not reset, discard, or overwrite existing work to make them match.
- The verified starting checkpoint for this document was branch `nayeon-v1`, commit `b10480f` (`feat: add structured capability contract`), tag `nayeon-v1-structured-capability-01`, with a clean working tree. This is historical context, not a requirement to reset future sessions to that commit.
- Make the smallest safe change. Do not redesign unrelated components. Preserve backward compatibility unless explicitly approved otherwise.
- Stop and ask for review before a decision materially changes the agreed architecture.
- Respect the current task's scope. Documentation-only tasks must not change application code.

## Architecture and execution boundaries

```text
MODEL decides WHAT
AGENT decides HOW
POLICY decides WHETHER
SERVICE performs IT
VERIFICATION proves RESULT
MEMORY retains appropriate context
```

- Preserve Permission -> Policy -> Confirmation -> Execution boundaries.
- Never let an LLM directly control the computer. Models may interpret natural language semantically, but resulting actions must become structured, validated, deterministic requests before side effects.
- Prefer reliable local, deterministic execution. Model output is untrusted input, not authorization or proof of success.
- Keep validation separate from execution: argument validation must not perform the capability's side effect.
- Preserve central policy evaluation, confirmation, audit, and undo paths. Do not bypass them by calling a service directly from model interpretation or dispatch planning.
- Verification must establish the actual result. An execution attempt, returned object, or model statement alone does not prove that the requested effect occurred.
- Retain only appropriate context in memory; do not store secrets there.

## Repository map and current implementation

These observations are grounded in the starting checkpoint. Reinspect the implementation as it evolves.

- `nayeon/` contains the Nayeon foundation. The root `readme.md` describes the older MARK LIII application; `main.py`, `ui.py`, `actions/`, `core/`, `dashboard/`, `plugins/`, and `memory/` remain alongside Nayeon. Do not assume the README describes completed Nayeon integration or migrate the legacy application incidentally.
- `nayeon/brain/service.py` defines the provider-independent `AIService` and `AIProvider` contract. Keep provider details behind this boundary. `brain/fake.py` provides a deterministic fake for local checks; provider adapters live in `brain/providers/`.
- `nayeon/intent/resolver.py` prefers sufficiently confident local interpretation and applies configured confidence thresholds to semantic fallback. `intent/ai_model.py` parses structured model responses; `intent/semantic.py` restricts intent names to registered capabilities plus supported system controls. Preserve these checks; intent acceptance does not validate capability-specific arguments.
- `nayeon/agent/dispatch.py` produces plans and does not execute them. `agent/controls.py` distinguishes cancellation of a pending action from undoing a completed action, with pending confirmation taking precedence for contextual reversal.
- `nayeon/registry.py` stores capability metadata and implementations. `capabilities/base.py` defines `CapabilityModule`; `capabilities/loader.py` discovers concrete subclasses that it can instantiate without arguments. Discovery catches import, construction, and duplicate-registration failures, so verify expected registrations rather than assuming discovery succeeded.
- `nayeon/capabilities/structured.py` defines the optional `StructuredCapability` protocol and `StructuredCapabilityRequest`. Request construction trims the original request and copies arguments; arguments remain untrusted. `validate_arguments` must reject invalid input with `ValueError` or `TypeError` and perform no side effects.
- Structured execution is a contract at this checkpoint, not a completed executor integration: `agent/executor.py` still calls `execute(request: str)`, and `capabilities/open_app.py` still uses that string interface. Preserve this compatibility until an explicitly scoped integration changes it. Do not treat the structured protocol as an alternate route around policy or confirmation.
- `nayeon/policy/service.py` checks permissions before policy blocks and confirmation requirements. `agent/executor.py` reevaluates policy after confirmation approval. `policy/confirmation.py` uses expiring, one-time tokens bound to the capability and exact request. Preserve these bindings and rechecks; an LLM must not approve its own action.
- `nayeon/audit/service.py` records structured events, optionally as JSONL. Keep policy, confirmation, execution, and undo-registration outcomes observable without disclosing secrets.
- Reversible capabilities must implement `UndoProvider` in `nayeon/undo/contract.py` and supply a concrete `UndoRegistration`. The executor rejects reversible metadata without this contract and reports undo-registration failure separately after execution. Do not falsely promise undo or hide partial outcomes.
- `nayeon/services/applications.py` owns platform-specific application launching. Keep OS effects in service implementations and use fakes or mocks for checks that would otherwise launch programs.
- No dedicated Nayeon verification or memory package exists at this checkpoint. The architectural responsibilities above are requirements, not claims that all layers are implemented.

## Secrets and runtime data

- Never expose or commit secrets or API keys, including in logs, audit details, fixtures, screenshots, or command output.
- `nayeon/secrets/store.py` reads environment-backed secrets. `nayeon/config/config.py` handles non-secret settings separately and defaults to `data/config.json`. Keep that separation.
- Use temporary paths and fake credentials for checks. Do not inspect real credentials or initialize live providers merely to validate documentation.
- Review staged paths explicitly. Do not rely solely on `.gitignore` to protect credentials, sessions, user memory, or runtime data; the default Nayeon `data/` directory is not listed there at this checkpoint.

## Validation and checkpoints

- Run focused tests after each change and regression tests before a checkpoint. Use deterministic fakes or mocks to avoid real model calls, desktop actions, and writes to personal data during baseline checks.
- At the starting checkpoint there are no checked-in test files or configured test runner. Standard-library discovery reports zero tests; this is a coverage gap, not a passing regression suite. Recheck available tests in future sessions and report unavailable coverage honestly.
- From the repository root, the existing Windows virtual environment supports these baseline commands:

  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover -v
  .\.venv\Scripts\python.exe -m nayeon.environment
  .\.venv\Scripts\python.exe -m compileall -q nayeon
  git diff --check
  ```

- Discovery only exercises tests if present. Environment diagnostics check platform support and report Python; compilation checks syntax. Neither proves application behavior. The documentation baseline used Python 3.12.10 on Windows 11.
- If that virtual environment is unavailable, use a verified compatible Python interpreter and report the difference. `setup.py` is an installation script that installs dependencies and Playwright browsers, not a test runner; do not run it for routine baseline validation.
- Never claim success when tests fail. Report exact commands, outcomes, skipped or missing tests, and environmental blockers. Do not declare a verified milestone while relevant failures remain unresolved.
- Make one coherent commit per verified milestone. Review the staged diff and commit only intended files. Tag meaningful verified milestones with descriptive `nayeon-v1-...` names; never move an existing milestone tag to disguise a different checkpoint.
- Keep the working tree clean at checkpoints without deleting unrelated user work. Do not push to any remote unless explicitly requested.
- At handoff, report files changed, tests and results, commit hash, git status, and discrepancies from the expected checkpoint. Stop for review when the user requests it.
