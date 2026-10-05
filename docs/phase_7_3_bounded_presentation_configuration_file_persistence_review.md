# Phase 7.3 bounded presentation configuration file persistence review

## Starting checkpoint and authorization

- Date: 5 October 2026; repository: `C:\AI\Mark-LII`.
- Branch: `nayeon-v1`.
- Starting/current HEAD: `cc4e9147cf2222dcd7bd1c7c29f3eb6a3643aea2`.
- Latest sealed product: Phase 7.2, product commit
  `9b210b6e7fb4d355a10dcd29d3f480fd4062f71c`.
- Annotated tag: `nayeon-v1-presentation-configuration-document-01`, peeled to
  that product commit. The tag was inspected and not modified.
- Historical full regression baseline: **1,563/1,563**. This is recorded Phase
  7.2 evidence, not a result obtained for this candidate.
- Initial worktree was clean and the branch/HEAD matched the requested checkpoint.
  `AGENTS.md`, `.codex/CURRENT_STATE.md`, the sealed Phase 7.1/7.2 contracts,
  relevant tests and reviews were read before implementation.

The state file correctly records Phase 7.2 as completed and still describes Phase
7.3 scope as unapproved. The explicit implementation request authorizes bounded
file persistence only. The state file remains unchanged as instructed.

## Exact candidate changes

| Path | Change |
| --- | --- |
| `nayeon/config/persistence.py` | Sole new production module: bounded file store, persistence error, size constant and two private JSON hooks |
| `tests/test_presentation_configuration_persistence.py` | 25 dedicated test methods with subtests and temporary fixtures |
| `tests/test_presentation_configuration_document.py` | Consumer guard excludes exactly the approved persistence module in addition to the document itself; test renamed to describe the updated boundary |
| This review document | Candidate semantics and actual validation evidence |

All other Phase 7.2 protections remain unchanged. No existing production file
was modified. There are no package-level exports.

## Persistence semantics

`PresentationConfigurationFileStore(path)` requires an explicit exact native
concrete `pathlib.Path` type (`WindowsPath` on Windows, `PosixPath` on POSIX).
`Path()` is a factory for that type; checking `type(value) is Path` would reject
ordinary native paths. Strings, other path-like objects, pure paths and subclasses
are rejected without coercion. Relative paths are explicit caller choices; there
is no implicit project/global/legacy path. Construction performs no file I/O.
The caller owns filesystem path selection and access permissions.

`load()` returns `None` only when opening the requested file raises
`FileNotFoundError`, including an absent parent directory. Other access failures
raise `PresentationConfigurationPersistenceError`. It opens in binary read mode
and reads at most **65,537 bytes**. A result above **65,536 bytes** is rejected
before UTF-8 decoding or JSON parsing. JSON whitespace padding counts toward the
byte limit. Content at exactly the limit is allowed if otherwise valid.

Decoding uses strict UTF-8. JSON object-pair hooks reject duplicate keys at every
nesting level, including differently escaped spellings of the same key. A
constant hook rejects NaN, Infinity and -Infinity. Malformed JSON, invalid UTF-8,
excessive nesting and all schema failures are errors. The unchanged Phase 7.2
parser handles exact shapes/keys/types, string constraints and supported version.
No defaults replace invalid persisted content. Load creates no directories or
files and performs no write, replacement or cleanup.

`save(document)` rejects non-exact documents with `TypeError` before filesystem
I/O. It calls the sealed canonical encoder, serializes compact deterministic JSON
in canonical field order with `ensure_ascii=False` and `allow_nan=False`, and
encodes UTF-8. It checks the byte limit before creating a temporary file.
Presentation strings that the sealed contracts accept but that cannot encode as
UTF-8 (for example lone surrogates) fail explicitly before file I/O; they are not
normalized or coerced.

The temporary file is securely created by standard-library `NamedTemporaryFile`
in the destination's parent directory, with `delete=False`. Save writes all
serialized bytes, flushes, calls `os.fsync`, and closes the temporary file before
`os.replace`. The destination is never opened for truncation. Failures before or
during replacement leave an existing valid destination intact. A `finally` block
attempts temporary-file removal; cleanup `OSError` is suppressed to preserve the
original sanitized error. Cleanup is best effort if the filesystem refuses it.
Parents must already exist. There is no locking; concurrent saves are last-writer
wins. Directory fsync/power-loss directory durability, metadata preservation and
filesystem access-policy management are outside this adapter's contract.

Persisted-content and filesystem failures use a small persistence-specific error
surface with fixed generic messages. Exception chaining is suppressed so normal
formatted tracebacks do not show decoder contents or filesystem filenames.
Programmer misuse remains `TypeError` for the public path/document contracts.
No rejected value, unknown key or file content is interpolated into messages.

## Ownership and explicit non-scope

Production dependencies are only standard-library future annotations, `json`,
`os`, `pathlib`, `tempfile`, and the sealed `nayeon.config.document` API.
There is no legacy `NayeonConfig`/`ConfigService` dependency and no access to
`data/config.json`. Migration and runtime wiring are explicitly deferred.

Presentation identity remains presentation-only. This module introduces no
capability identity, policy, permission, confirmation, audit identity, execution
authority, trusted object identity, secrets, provider interpretation, network
access, Voice listening toggles, Proactive/event toggles, permission defaults,
arbitrary settings dictionary or generic configuration owner. Computer Control
and Permission -> Policy -> Confirmation -> Execution -> Verification are untouched.

`presentation.py`, `document.py`, legacy `config.py`, configuration package exports,
all runtime/trust paths, `AGENTS.md`, `.codex/CURRENT_STATE.md` and
`scripts/update_codex_context.py` remain unchanged. No live/native smoke is
justified for this unwired adapter; tests use temporary paths and synthetic data.

## Prepared tests and actual validation evidence

The dedicated tests cover exact explicit path/document contracts, missing files,
default and non-default Unicode round trips, canonical encoder use/order and
deterministic bytes, literal UTF-8, malformed JSON/invalid UTF-8, duplicate keys
at root and each nested section, escaped duplicates, non-standard constants,
excessive nesting, invalid schema roots/sections/keys/types/versions, exact size
boundary and bounded read, read-only behavior, access errors, same-directory
atomic replacement and write/flush/fsync/close/replace ordering. Fault injection
covers temporary creation, partial write, flush, close, fsync, replace and cleanup
failures, preserving the prior valid file and cleaning temporary files when
possible. Tests also cover unencodable strings, private messages/tracebacks,
production dependency and consumer boundaries, exact checkpoint/content/inventory,
and protected instructions/context/script integrity.

Validation actually obtained in the Codex sandbox:

- Authorized interpreter invocation at
  `C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe --version`
  failed because the executable was unavailable to this environment.
- No Python/packages were installed, downloaded or copied; no network workaround
  or alternate runtime was used.
- Git checkpoint/tag/initial clean worktree checks: matched.
- `git diff --check`: passed for tracked changes.
- Explicit trailing-whitespace scans of candidate source/test/review paths: passed.
- Git blob comparison using checkout filters: **84/84** pre-existing tracked
  production files match the starting checkpoint; zero mismatches.
- Protected instruction/context/script blob comparisons: unchanged.
- Text scan of other production sources for persistence API/module identifiers:
  zero matches. Stronger AST guards are prepared for host execution.
- Staging area: empty; HEAD unchanged.

Independent authoritative Windows-host validation then used:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`.

The first dedicated Phase 7.3 host run exposed one test-only mock defect in
`test_read_is_bounded_to_limit_plus_one_bytes`: the mock asserted against the
context-manager return object rather than the object returned by `Path.open()`.
The production implementation already performed the required bounded
`read(65537)`. The test was corrected within the approved candidate-test scope;
no production code changed.

Host validation also reproduced the previously identified historical Phase 7.1
guard conflict exactly: its checkpoint assertion still expected the old
`ae1a1ca...` housekeeping HEAD. Human approval was obtained for narrow test-only
maintenance to that guard. It now protects the sealed Phase 7.2 product commit and
tag, pins this Phase 7.3 starting HEAD, permits exactly
`nayeon/config/persistence.py` as the new production addition, and byte-compares
all pre-existing production sources against the sealed Phase 7.2 product state.
All presentation/security/action-identity assertions remain intact.

Exact staging for the human-approved seal then exposed a second test-only guard
assumption in the dedicated Phase 7.3 suite: the production-scope test expected
`persistence.py` to remain untracked. Once correctly staged, Git reported it as
a tracked diff from the starting checkpoint. The guard was tightened to accept
the approved module in either staged/tracked-diff or untracked form while still
requiring the combined production delta to be exactly
`nayeon/config/persistence.py`. No production code changed. The staged
presentation/config guard set and full regression were rerun successfully.

Final authoritative host results:

- dedicated Phase 7.3 suite: **25/25 passed**;
- combined Phase 7.1/7.2/7.3 presentation/config guards: **55/55 passed**;
- affected config/core/trust-boundary suite: **187/187 passed**;
- full unittest discovery: **1,588/1,588 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Final integrity/scope evidence:

- all **84** pre-existing tracked Python production files under `nayeon/` match
  the Phase 7.3 starting checkpoint; zero mismatches;
- the combined production delta from the starting checkpoint is exactly
  `nayeon/config/persistence.py`; at seal time it is staged with no other
  production delta;
- no other production source consumes the persistence API;
- `persistence.py` has zero legacy `ConfigService`/`NayeonConfig` or
  `data/config.json` dependencies;
- `AGENTS.md`, `.codex/CURRENT_STATE.md`, and
  `scripts/update_codex_context.py` remain unchanged;
- the staging area contains exactly the five reviewed Phase 7.3 paths, with no
  unstaged or unrelated untracked changes;
- `git diff --cached --check` passes for the exact staged candidate.

No live/native smoke is justified: the adapter is deliberately unwired and all
I/O behavior is exercised against bounded temporary filesystem fixtures.

## Seal-time handoff

Human seal approval was received after independent validation. The exact reviewed
five-file candidate was staged and seal-time regression repeated successfully.
At this review-document checkpoint no product commit, tag, push, workbook update,
or Codex current-state refresh had yet occurred.
