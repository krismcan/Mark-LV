# Phase 7.5 bounded presentation configuration bootstrap composition review

## Starting checkpoint and approved scope

- Date: 6 October 2026; repository: `C:\AI\Mark-LII`.
- Branch: `nayeon-v1`; starting/current HEAD:
  `c6c3d7436cc39470ee9d23e0e5c7fed05c3e0afd`.
- Latest sealed product: Phase 7.4, commit
  `1cf34c9ad0ab02e86c859f4539afda5d265bfa81`.
- Annotated tag: `nayeon-v1-presentation-configuration-runtime-ownership-01`,
  resolving to that product commit.
- Historical full regression baseline: **1,608/1,608** from sealed Phase 7.4;
  this is not a Phase 7.5 validation result.
- Starting branch, HEAD and clean worktree matched the requested checkpoint.
  Root instructions, current state, relevant Phase 7.1-7.4 sources, tests and
  reviews were inspected before editing.

The state file still describes Phase 7.5 scope as unapproved. The explicit user
instruction approves this bounded bootstrap composition and supersedes that
restart note. The state file remains unchanged as requested.

## Exact candidate changes

| Path | Change |
| --- | --- |
| `nayeon/config/bootstrap.py` | Sole production addition; one explicit-path composition function |
| `tests/test_presentation_configuration_bootstrap.py` | 17 dedicated behavior and boundary test methods |
| `tests/test_presentation_configuration_service.py` | Freeze sealed Phase 7.4 contents and permit exactly bootstrap composition |
| `tests/test_presentation_configuration_persistence.py` | Advance checkpoint/scope guard; allow bootstrap's required store construction reference |
| `tests/test_presentation_identity_contracts.py` | Freeze sealed Phase 7.4 contents and permit exactly bootstrap as the production addition |
| This review document | Approved semantics, boundaries and actual evidence |

No existing production file changes. The Phase 7.2 document test needs no
maintenance: bootstrap does not import or reference document contracts.
Historical guard maintenance preserves identity/security/runtime assertions,
per-file content comparisons, exact inventory and protected-file checks.

## Composition semantics and caller-owned path

The approved stack is `presentation.py -> document.py -> persistence.py ->
service.py -> bootstrap.py`. The only public composition function is:

```python
bootstrap_presentation_configuration(path: Path) -> PresentationConfigurationService
```

It constructs exactly one `PresentationConfigurationFileStore(path)`, constructs
exactly one `PresentationConfigurationService` using that exact store, calls
that service's `initialize()` exactly once and returns that exact service.
The initialization return value is not substituted for the owner.

The caller supplies the path; there is no default. The exact argument is forwarded
without conversion or derivation. The sealed store enforces the exact native
concrete Path type and rejects strings, path-like values, pure paths and subclasses
without coercion. Bootstrap duplicates no validation. Relative paths remain
explicit caller choices. There is no project-root/cwd lookup, environment lookup,
app-data/XDG/home/registry lookup, normalization, resolve, expanduser, directory
creation or fallback destination.

Initialization behavior is inherited unchanged. Valid persisted schema-v1 content
becomes the service's owned document without interpretation or Unicode
normalization. Missing files, including missing parents, yield fresh canonical
defaults in memory only, without save/file/directory creation. Corrupt, malformed,
unsupported or legacy-shaped content fails closed through the unchanged bounded
persistence error. Bootstrap catches/translates no error and returns no service
after initialization failure. There is no repair or legacy fallback.

## Consumer and ownership boundaries

Bootstrap imports only future annotations, `pathlib.Path`, the sealed store and
the sealed service. It has no singleton/global state, container/runtime class,
registry, generic injection framework or post-return persistence ownership.
The returned service remains the owner.

Bootstrap is the sole approved new production consumer of
`PresentationConfigurationService`. No production module consumes bootstrap.
Document consumers remain exactly persistence and service; presentation consumers
remain confined to the sealed document boundary.

The required store import/construction in bootstrap is a narrow composition
exception to the historical persistence-reference prohibition. Only service owns
and calls store `load`/`save`; bootstrap does not perform persistence operations
directly. The dedicated exact AST guard fixes all executable bootstrap nodes,
including precisely the three approved calls, so this exception permits no wider
persistence API consumption. Sealed service contents are compared to both the
Phase 7.4 product commit and the Phase 7.5 starting HEAD.

## Explicit non-scope and legacy disposition

There is no full Nayeon Runtime, ApplicationContainer/ServiceContainer/
DependencyContainer, composition of other subsystems, root MARK integration,
ConversationSession integration, intent/dispatcher/orchestration/executor wiring,
UI wiring, model/system-prompt injection, provider selection/validation, capability
or registry integration, network, secrets, memory, Voice/wake-word behavior,
Proactive/event behavior, generic settings, or package export.

Presentation remains presentation-only. Capability identity, permission/policy
decisions, confirmation binding, audit action identity, execution authority and
trusted object identity remain unchanged. Permission -> Policy -> Confirmation ->
Execution -> Verification and the frozen Computer Control authority surfaces
remain intact.

Legacy `nayeon/config/config.py` remains frozen, isolated, unused and
non-authoritative. No legacy ConfigService/NayeonConfig import, probing,
migration, fallback, repair or deletion is added. Package APIs, `AGENTS.md`,
`.codex/CURRENT_STATE.md` and `scripts/update_codex_context.py` remain unchanged.

## Actual validation evidence

Codex could not invoke the authoritative interpreter from its sandbox and therefore
claimed only bounded static evidence. Independent orchestration then ran the
candidate on the authorized Windows host with:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Authoritative host results:

- dedicated Phase 7.5 bootstrap suite: **17/17 passed**;
- combined Phase 7.1-7.5 presentation/configuration suites and guards:
  **92/92 passed**;
- affected presentation/configuration plus relevant Phase 6 trust/orchestration
  suite: **224/224 passed**;
- full unittest discovery: **1,625/1,625 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent final scope/integrity evidence:

- all **86/86** pre-existing tracked Python production files under `nayeon/`
  match both the Phase 7.5 starting HEAD and the sealed Phase 7.4 product commit;
  zero mismatches;
- there is no tracked production modification and the sole untracked production
  addition is `nayeon/config/bootstrap.py`; production Python inventory is **87**;
- bootstrap has zero production consumers;
- no production module other than bootstrap consumes
  `PresentationConfigurationService`; sealed service remains unchanged;
- bootstrap may construct the sealed `PresentationConfigurationFileStore`, while
  the exact bootstrap AST and unchanged service preserve presentation-store
  `load`/`save` ownership in the service layer;
- document consumers remain confined to document, persistence and service;
- legacy `ConfigService`/`NayeonConfig` remain isolated in their unchanged legacy
  module and are not imported by the new composition seam;
- root legacy MARK paths, package init files, `AGENTS.md`,
  `.codex/CURRENT_STATE.md`, and `scripts/update_codex_context.py` remain unchanged;
- before human seal staging was empty; after approval exactly the six reviewed Phase 7.5 paths were staged.

The dedicated tests verify the exact one-function composition shape, one store /
one service / one initialize call order, exact argument and returned-owner identity,
native Path behavior with no coercion, valid Unicode preservation, missing-file
in-memory defaults without file/directory creation, fail-closed malformed,
unsupported and legacy-shaped input, unchanged error propagation, explicit
relative-path forwarding without environment/default-path derivation, no legacy
neighbor probing, zero bootstrap consumers, the sole service-consumer boundary,
sealed persistence/document ownership, frozen production contents, and protected
files.

No live/native machine smoke is justified. Phase 7.5 adds no OS action, provider,
network, runtime consumer or machine-control behavior; real configuration-file
semantics are exercised through host temporary-filesystem tests over the already
sealed persistence/service layers.

## Handoff

Human seal approval was received. Exactly the six reviewed Phase 7.5 paths were
staged with no unstaged or unrelated untracked changes. Seal-time validation of
that staged candidate repeated successfully: the combined Phase 7.1-7.5
presentation/configuration suite remained **92/92 passed**, full unittest discovery
remained **1,625/1,625 passed**, and `python -m compileall -q nayeon tests`
completed successfully. `git diff --cached --check` also passes.

At this review-document checkpoint no product commit, annotated tag, push, workbook
update or `.codex/CURRENT_STATE.md` refresh had yet occurred.
