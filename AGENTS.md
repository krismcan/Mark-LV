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

## Mandatory Failure & Architectural Regression Gate

**Before each new phase and before security-sensitive seals**, review recent failures,
previous incident reports, regressions, security-review findings, blockers, retries,
workarounds, and historical assumptions that could affect the new scope. Follow
[docs/engineering_failure_review_gate.md](docs/engineering_failure_review_gate.md).

- Maintain a bounded **Open Failures & Prior-Issues Review** with severity, root
  cause, reproduced evidence, impacted callers/trust boundaries, repair, tests,
  independent review and explicit GO/HOLD disposition.
- **STOP** forward phase work for unresolved material failures, unknown root
  causes, failed regressions, or security-sensitive missing evidence. Do not
  proceed merely because other tests passed; a green suite is not proof of
  cross-phase architectural safety.
- Trace architectural failures through all relevant older entrypoints and
  alternate routes, shared objects, windows, processes and restarts. Add
  adversarial tests reproducing the original failure, then verify the fix.
- Never skip/weaken tests, downgrade findings, mask exceptions, or approve
  risky deferrals to force a milestone seal. Any genuinely low-risk deferral
  needs documented evidence and the user's explicit approval.
- If there is no meaningful progress for **five minutes**, inspect the live
  process/logs immediately and stop or pivot when stuck. Preserve checkpoints.
- Repeat focused, affected, cross-phase and full regression suites plus
  independent review after a material repair. Keep earlier product tags
  immutable; only GO after verified closure and documentation.

## Phase workflow

Retrospective failure gate (GO/HOLD) -> architecture/dependency audit -> approved bounded implementation -> independent validation and adversarial regression -> justified smoke -> human seal review -> exact staging -> seal-time regression -> milestone commit -> annotated tag -> approved push -> remote verification -> master workbook update.

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

## Operating Model v2.1 — current engineering governance (26 October 2026)

The independently reviewed host policy at D:\\Nayeon\\Governance\\NAYEON_OPERATING_MODEL_V2_1_20261025.md SUPPLEMENTS (not replaces) v2 and this repository's existing fail-closed architecture, approvals, tests and exact Git seals. It does not grant real-key/provider permissions, weaken Windows controls, activate the PRC or authorise fewer mandatory full native Windows regression gates. Conflicts, incomplete review and unsupported evidence mean HOLD.

Before any >15-minute release regression, map changed production files, tests, historical migration readers, frozen hashes and the actual Git topology (COMPLETE_UNSTAGED, EXACT_STAGED, EXACT_CHILD). Run the entire affected historical modules and negative canaries for every applicable state; a negative must reject the forbidden effect, not simply match a message from the wrong Git state. At each stage/commit transition rerun state-specific manifest/index/tree/hash, unknown/ignored-path, ancestor/tag and relevant guard canaries BEFORE the next full suite. Capture actual native exit codes, complete test counts and log hashes; never reuse results after changing tracked bytes, pins or expectations.

Use exactly one writer and no duplicate tests. Watch meaningful CPU/log progress; a long-running historical integrity test is not automatically stalled after five silent minutes. Investigate genuine failure narrowly, reproduce RED then GREEN, independently review and preserve the original failing evidence. Release helper scripts and GitHub destination require independent review; reject forged success markers, stale approvals, unsafe push rewrites or unpinned remote refs. For now retain ALL THREE existing authoritative full native Windows regression gates (pre-stage, exact-stage, exact-child); any reduction requires separate human governance approval, demonstrated risk equivalence and enforceable fail-closed policy.

After genuine remote commit + annotated tag verification, update ONLY the original same-ID macro-enabled 16-sheet Drive workbook, verify exact revision/download, THEN publish and read back the actual served GitHub Pages dashboard. No release closure from local files, a GitHub commit alone or a pending Pages deploy. State fake-only engineering GO and real consumer BYOK acceptance independently; gates 3/4 stay unverified until approved end-to-end app tests. The current v2.1 document is reviewed HOST GOVERNANCE; repository-level procedures are tracked but mandatory state-specific *machine* admission and PRC enforcement remain PENDING. The unapproved auxiliary canary was withheld following independent MEDIUM findings. See docs/om_v21_repo_adoption.md for honest governance status.
