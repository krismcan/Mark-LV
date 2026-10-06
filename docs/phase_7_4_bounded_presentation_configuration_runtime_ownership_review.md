# Phase 7.4 bounded presentation configuration runtime ownership review

## Starting checkpoint and approved scope

- Date: 6 October 2026; repository: `C:\AI\Mark-LII`.
- Branch: `nayeon-v1`; starting/current HEAD:
  `78c01f7d52f956785ec659812415e9ebd8f8e8e7`.
- Latest sealed product: Phase 7.3, commit
  `1d43dcfe7405033e67c9afb4cd7108fb0da14d4e`.
- Annotated tag: `nayeon-v1-presentation-configuration-persistence-01`,
  resolving to that product commit.
- Historical full regression baseline: **1,588/1,588**. This is sealed Phase 7.3
  evidence, not a Phase 7.4 result.
- Starting branch, HEAD and clean worktree matched the requested checkpoint.
  Root instructions, current state, sealed Phase 7.1-7.3 source/tests/reviews
  were inspected before editing.

The current-state file still describes Phase 7.4 as unapproved. The explicit
user instruction approves lifecycle ownership only and supersedes that restart
note. The file remains unchanged as requested.

## Exact candidate changes

| Path | Change |
| --- | --- |
| `nayeon/config/service.py` | Sole production addition: `PresentationConfigurationService` |
| `tests/test_presentation_configuration_service.py` | 20 dedicated lifecycle, privacy and production-boundary test methods |
| `tests/test_presentation_configuration_document.py` | Permit exactly persistence and service as document consumers |
| `tests/test_presentation_configuration_persistence.py` | Permit only service as persistence consumer; advance starting HEAD, tag and exact production-addition guard |
| `tests/test_presentation_identity_contracts.py` | Freeze sealed Phase 7.3 production contents and permit exactly service as the new production addition |
| This review document | Candidate semantics and actual validation evidence |

The historical guard edits retain presentation validation, security and identity
assertions. Identity guards now freeze the Phase 7.3 product commit/tag;
persistence guards pin the Phase 7.4 starting HEAD and Phase 7.3 tag. Both permit
only `service.py` as the production addition, retaining inventory and per-file
content comparisons. The new suite compares all pre-existing production contents
against both checkpoints and protects instructions, context, script and legacy API.

## Lifecycle and failure semantics

Construction requires the exact sealed `PresentationConfigurationFileStore` type.
Subclasses, mock substitutes and coercible values are rejected with constant
`TypeError` text. Construction stores the dependency and an empty ownership slot;
it performs no filesystem I/O or load/save call. There is no default path,
environment lookup, legacy probing, singleton or package export.

`is_initialized` is a read-only boolean property derived from the owned document.
`current` is read-only and returns that exact immutable document. Before successful
initialization, `current` and `replace` raise `RuntimeError` with the fixed message
`Presentation configuration service is not initialized`. No default is synthesized
by either misuse path, and replacement performs no save.

`initialize()` calls `store.load()` on its first successful attempt. A valid loaded
document becomes current without copying or interpretation. Only a returned `None`
creates a fresh canonical schema-v1 default document in memory. Initialization
never saves or creates directories/files. A failed load propagates the sealed
persistence error, leaves the ownership slot empty and allows a later retry.
Successful initialization is cached: later calls return the same owned object and
do not reread disk, including after replacement. Corruption is never converted to
defaults. Lifecycle operations are caller-serialized; no concurrency API or lock
is introduced.

`replace(document)` requires successful initialization and the exact sealed
document type. It calls `store.save(document)` before assigning current. Failure
propagates while preserving the exact previously owned object. Success owns and
returns the exact argument. It does not mutate the prior document, merge fields,
normalize Unicode, migrate data, inject defaults or interpret provider references.
Errors use constant messages; inherited object repr does not serialize personal
values. Existing bounded persistence error sanitization remains unchanged.

## Ownership and explicit non-scope

The approved stack is `presentation.py -> document.py -> persistence.py ->
service.py`. The service directly imports only the sealed document type and store
type, plus future annotations. It is the sole approved production consumer of
persistence. No runtime/composition root consumes the service.

Presentation values remain presentation-only. Capability identity, permissions,
policy, confirmation binding, audit action identity, execution authority, trusted
object identity, secrets and Computer Control are unchanged. Permission -> Policy
-> Confirmation -> Execution -> Verification remains intact.

There is no root MARK, ConversationSession, UI, model/system-prompt or runtime
wiring; provider lookup/validation; network or secret access; Voice listening or
wake-word toggle; Proactive/event toggle; permission default; generic settings
dictionary; legacy migration/probing; package-level export; or automatic first-run
file creation. No live/native smoke is justified for this unwired owner.

Legacy `nayeon/config/config.py` stays frozen, isolated, unused and non-authoritative.
Neither `NayeonConfig` nor legacy `ConfigService` is imported, wrapped or replaced.
Its fields and personal default are not migrated or special-cased. Future migration
requires separate architecture approval.

## Validation evidence and handoff

Codex could not invoke the authoritative host interpreter from its sandbox and
therefore claimed only bounded static evidence. Independent orchestration then ran
the candidate on the authorized Windows host using:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Authoritative host results:

- dedicated Phase 7.4 service suite: **20/20 passed**;
- combined Phase 7.1-7.4 presentation/configuration suites and guards:
  **75/75 passed**;
- affected presentation/configuration plus relevant Phase 6 trust/orchestration
  suite: **207/207 passed**;
- full unittest discovery: **1,608/1,608 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent final scope/integrity evidence:

- all **85** pre-existing tracked Python production files under `nayeon/` match
  the Phase 7.4 starting HEAD; zero mismatches;
- there is no tracked production modification from the starting HEAD and the sole
  untracked production addition is `nayeon/config/service.py`;
- no unapproved production consumer of the Phase 7.3 persistence API exists;
- no production module consumes `PresentationConfigurationService`;
- no unapproved production consumer of the Phase 7.2 document API exists;
- legacy `ConfigService`/`NayeonConfig` have zero consumers outside their frozen
  legacy module;
- root legacy MARK production paths remain unchanged;
- `AGENTS.md`, `.codex/CURRENT_STATE.md`, and
  `scripts/update_codex_context.py` remain unchanged;
- staging remains empty.

The dedicated tests verify exact dependency/type rejection, zero constructor I/O,
read-only lifecycle state, first-run in-memory defaults without disk creation,
exact persisted Unicode/custom document ownership, initialization caching, retry
after load failure, fail-closed corrupt/unsupported/legacy input, exact replacement
typing, persistence-before-swap ordering, state preservation on failed save,
successful persistence/current replacement, privacy, sole persistence ownership,
absence of runtime wiring, frozen production scope and protected-file invariants.

No live/native machine smoke is justified. Phase 7.4 remains an unwired
process-local configuration owner and its real file interactions are exercised
through the already sealed file store and host temporary-filesystem tests.

Human seal approval was received. The exact six-file candidate was staged and
seal-time validation was repeated successfully: the combined Phase 7.1-7.4
presentation/configuration suite remained **75/75 passed**, full discovery remained
**1,608/1,608 passed**, and compileall completed successfully. The staging area
contains only the six reviewed Phase 7.4 paths, with no unstaged or unrelated
untracked changes. At this review-document checkpoint no product commit, tag, push,
workbook update or current-state refresh had yet occurred.
