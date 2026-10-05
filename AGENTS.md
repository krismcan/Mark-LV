# Nayeon v1 engineering instructions

## Start here

- Read `.codex/CURRENT_STATE.md` for the latest completed phase, regression baseline, and restart point.
- Inspect branch, HEAD, milestone tags, and working tree before editing. Git is authoritative; report any mismatch with the state file.
- Read only the implementation/tests/latest phase review relevant to the task. Do not rely on the legacy root README as current Nayeon status.
- Never reset, discard, overwrite, or hide unrelated user work to force a checkpoint match.

## Architecture contract

```text
MODEL decides WHAT
AGENT decides HOW
POLICY decides WHETHER
SERVICE performs IT
VERIFICATION proves RESULT
MEMORY retains appropriate context
```

- Model output is untrusted input, never authorization or proof.
- Preserve Permission -> Policy -> Confirmation -> Execution -> Verification.
- Never give an LLM direct machine authority. Semantic interpretation must become typed, bounded, deterministic requests before side effects.
- Validation must not perform the action.
- Do not bypass policy, confirmation, audit, undo/resource cleanup, or verification by calling lower-level services from interpretation/dispatch.
- Make the smallest safe change and stop for human review before material architecture/scope changes, destructive/live actions, credentials, or established seal gates.

## Repository boundaries

- `nayeon/` is the Nayeon v1 implementation.
- Root-level `main.py`, `ui.py`, `actions/`, `core/`, `dashboard/`, `plugins/`, and `memory/` are legacy MARK code; do not migrate them incidentally.
- `docs/phase_*_review.md` contains detailed milestone evidence.
- `.codex/CURRENT_STATE.md` is the concise current Codex handoff.
- Respect the approved production scope for each phase.

## Frozen Computer Control v1 boundary

Computer Control v1 is a completed bounded foundation.

Public surface:
- foreground observation;
- pointer observation;
- identity-bound focus;
- bounded keyboard text.

The single-left-click path remains a trusted private primitive. Do not expose generic/raw coordinate click authority without a new approved architecture phase.

Preserve the Phase 6 trust invariants: approved point authority, fresh target/hit/UIA evidence, Runtime-ID continuity, enabled/clickable prerequisites, final coordinate normalization before bounded insertion, and reviewed SendInput boundaries.

Semantic/visual targeting, public click, right/double click, drag/drop, scroll/wheel, autonomous GUI sequences, and semantic task-success understanding are deferred to later Vision/Perception/Autonomy work.

Historical Phase 6 tests should freeze these authority surfaces, not all future `nayeon/` growth or future HEADs.

## Presentation identity / configuration boundary

Current presentation contracts are in `nayeon/config/presentation.py`.

- Assistant defaults to display/wake name `Nayeon`, but users may rename it.
- User display name defaults to `None`.
- Personality/voice references are presentation preferences only.

Presentation identity must never alter capability identity, permission/policy decisions, confirmation binding, audit action identity, execution authority, trusted object identity, or secrets.

Legacy `nayeon/config/config.py` is intentionally isolated and is not authoritative Phase 7 configuration unless an approved migration phase changes that.

Do not create a generic settings God object. Permission defaults, secrets, Voice listening behavior, and Proactive/event behavior require explicit subsystem ownership.

## Secrets

- Never expose or commit keys, credentials, tokens, or private user data.
- Keep secrets separate from non-secret configuration.
- Do not inspect live credentials merely to validate code.
- Prefer deterministic fakes/mocks and temporary data.

## Validation

Authoritative host Python:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Codex sandbox may be unable to access it. If blocked:
- do not download/install/copy Python or packages;
- do not use a network workaround;
- perform bounded static work and leave authoritative runtime validation to host orchestration.

For milestones run focused tests, relevant affected/trust-path tests, full `unittest` discovery, `python -m compileall -q nayeon tests`, and `git diff --check`.

Never claim a verified milestone while relevant failures remain unresolved.

## Phase workflow

Architecture audit -> approved bounded implementation -> independent validation -> justified smoke -> human seal review -> exact staging -> seal-time regression -> milestone commit -> annotated tag -> approved push -> remote verification -> master workbook update.

### Mandatory Codex context refresh

Before starting the next product phase, refresh `.codex/CURRENT_STATE.md` for the phase just completed using `scripts/update_codex_context.py` or an equivalent exact edit.

Record only:
- latest completed product phase;
- milestone tag;
- full regression baseline;
- next restart point;
- one concise current architecture invariant;
- date.

Detailed history belongs in Git, phase review docs, and the master workbook.

## Git discipline

- Keep sealed checkpoints clean.
- Review staged paths before committing.
- One coherent commit per verified product milestone.
- Never move an existing milestone tag.
- Do not push without user approval.
