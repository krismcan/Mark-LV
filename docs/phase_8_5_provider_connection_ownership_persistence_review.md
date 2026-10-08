# Phase 8.5 - Typed Provider Connection Ownership & Persistence

## Starting checkpoint and candidate status

7 October 2026, `C:\AI\Mark-LII`, branch `nayeon-v1`.
Starting HEAD: `35c0246362fbecc3df8532b63d42087b32b22646`.
Latest sealed product: Phase 8.4 - OpenAI Credential Validation & Canonical
Client Routing, commit `94e0c2896c8df87421c80edcfc4fd3de48fd8ac7`, annotated tag
`nayeon-v1-openai-credential-validation-canonical-routing-01`.
Historical full regression baseline: **1774/1774**, not a Phase 8.5 result.

The branch, HEAD, clean worktree and annotated tag target matched the supplied
start before editing. AGENTS.md, CURRENT_STATE.md, the Phase 8.4 review, current
connection/identifier contracts and Phase 7 document/persistence/service patterns
were read. CURRENT_STATE.md still describes Phase 8.5 as awaiting scope approval;
the user's explicit approval supersedes that restart note. The file is unchanged.

This is an **unstaged, unsealed implementation candidate**. Authoritative runtime validation is complete; independent human seal review remains pending. No staging, commit, tag,
push, workbook update or context update was performed.

## Exact production scope

Exactly three NEW modules:

- `nayeon/brain/connection_document.py`
- `nayeon/brain/connection_persistence.py`
- `nayeon/brain/connection_service.py`

No existing production file changes. All 95 pre-existing production Python files
and requirements remain content-identical to starting HEAD and the sealed Phase
8.4 product after ordinary checkout newline normalization.

Provider connection metadata has its own typed ownership boundary. Presentation
identity/preferences have different meaning and subsystem ownership; they never
select credentials, authorize provider use or become a generic settings object.
The Phase 7 implementation is a reviewed pattern only, with no imports or reuse of
its configuration documents/services. Secure credential storage/lifecycle,
one-secret resolution, provider validation and application composition remain
separate and unchanged.

## Document and strict codec

`PROVIDER_CONNECTION_SCHEMA_VERSION = 1` and the frozen, slotted, repr-disabled
`ProviderConnectionDocumentV1` define fields in order: `schema_version`, then
`connection`. Version requires exact built-in int equal to 1. Connection requires
None or exact sealed `ProviderConnectionConfiguration`. No coercion, mutation or
normalization occurs.

Unconfigured means a real versioned document with `connection: null`:

```json
{"schema_version":1,"connection":null}
```

Configured means one provider/model/safe credential identifier:

```json
{"schema_version":1,"connection":{"provider":"vendor","model":"Model V1","credential":"unmapped.key"}}
```

Both mapping levels require exact built-in dicts, exact str keys and exactly the
specified keys. Missing/unknown content and unsupported versions are rejected;
there is no migration or defaulting. Raw credential metadata constructs an exact
SecretIdentifier; provider/model syntax and types remain governed by the sealed
connection contract. Mutable input mappings are not retained. Encoding accepts
only the exact document and returns fresh canonical built-in mappings, using only
`credential.value`, never a secret value or secret API.

## Bounded persistence and filesystem ownership

The store requires the exact native concrete pathlib.Path type. The caller owns
the explicit path and filesystem permissions. No default location, environment
lookup, directory creation, permission mutation, migration or locking exists.

Binary load reads at most **16385 bytes** for the **16 KiB (16384-byte)** file bound.
Missing files return None. Strict UTF-8 and JSON decoding reject malformed data,
duplicate keys at any level, NaN/Infinity, invalid types/schema and recursion errors.
Opening failures and invalid/unreadable content have separate fixed safe messages
with suppressed display chains. Paths, data, provider/model and credential
metadata are not included in public errors.

Save rejects non-exact documents with TypeError before I/O. Canonical compact JSON
uses literal UTF-8 (`ensure_ascii=False`), `allow_nan=False` and separators without
extra whitespace. The byte bound is checked before temporary file creation.
NamedTemporaryFile uses the destination parent and `delete=False`; write, flush,
file fsync and close precede exactly one os.replace into the caller's destination.
Temporary unlink is best effort and does not mask failure or undo a successful
replace. Ordinary filesystem/encoding/value/type errors use a fixed safe message.
Process-control exceptions are not swallowed.

Same-directory atomic replacement is the file update guarantee. No locking is
provided; concurrent saves are last-writer-wins. There is no power-loss directory
fsync durability claim. Callers must provide an existing destination parent and
appropriate access permissions.

## One process-local owner

`ProviderConnectionService` accepts only the exact store type and has slots
`_store`, `_current`. None means not initialized, distinct from an initialized
document whose connection is null. Access/mutation before initialization raises
the fixed RuntimeError. Construction performs no I/O.

Initialization loads once on first success, uses an in-memory null document for a
missing file without saving, and caches that exact immutable object. Repeated
initialization does no store work. Load failures leave the service uninitialized
and retryable.

Replace requires exact ProviderConnectionConfiguration, creates a new document,
saves it once and swaps the current reference only after success. Clear follows
the same ordering with a new null document. Save failure preserves the old current
object by identity. **Clear persists null; it does not delete the file.** Repeated
clear persists a new null document each time. Callers serialize lifecycle
operations; no concurrent-operation API is introduced.

There is one active connection only in v1. Metadata is not authorization or proof.
This service neither enforces provider-to-credential identity nor constructs
resolvers/providers/validators. Future trusted composition must independently
verify that mapping before granting bounded credential resolution authority.

## Deterministic tests and historical guard maintenance

Written focused suites contain **47 test methods** (including scope guards):

- document: 11; exact immutable shape/types, strict mappings, safe identifier
  encoding, round trips, input isolation and exact pure imports/calls;
- persistence: 20; native Path gate, missing/valid/invalid files, UTF-8, duplicate
  keys/constants, byte bounds, bounded read, safe errors, write/fsync/close/replace
  ordering, cleanup/failure isolation and exact dependency boundaries;
- service: 16; lazy retryable initialization, identity caching, pre-I/O type gates,
  persist-before-swap, failure preservation, repeated clear and scope/consumer guards.

Tests use synthetic metadata, temporary directories and patched file/store seams.
They do not instantiate live credential backends, call providers or use networks.

Necessary maintenance is restricted to ten historical test files. Eight scope
suites now pin the supplied start/sealed Phase 8.4 checkpoint, permit exactly the
three additions and freeze every existing production file, including the OpenAI
provider formerly exempted during Phase 8.4. The requirements guard retains the
exact OpenAI pin assertion and now freezes all requirements against both current
checkpoints. The lifecycle consumer assertion admits only document/service as
connection-configuration consumers. The Windows secret guard retains its previous
approved consumers and permits only the new document addition.

Two further narrow changes handle newly legitimate metadata use: the secure
OpenAI provider suite adds the document as an exact SecretIdentifier-only consumer;
the presentation document guard permits the local name `document` only in the
three approved connection modules. Presentation imports, aliases, symbols and
reflective strings remain forbidden. New suites assert exact imports/calls.
Every existing trust/privacy/routing assertion remains in place; no production
authority or composition exemption was added.

## Actual validation evidence

Independent orchestration completed authoritative host validation with:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Final candidate results:

- dedicated Phase 8.5 document/persistence/service suites: **47/47 passed**;
- combined Phase 7 foundation + all Phase 8 suites and guards: **288/288 passed**;
- affected configuration/secrets + relevant trust/orchestration suite: **420/420 passed**;
- full unittest discovery: **1,821/1,821 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent scope/integrity evidence:

- exact production delta from starting HEAD is only the three new approved modules:
  `connection_document.py`, `connection_persistence.py`, and `connection_service.py`;
- both starting HEAD and sealed Phase 8.4 product contain **95** tracked production
  Python files and all **95/95** remain content-identical after ordinary checkout
  newline normalization;
- production Python inventory is now **98**, exactly the prior 95 plus the three
  approved additions;
- `requirements.txt` is unchanged against both checkpoints;
- `ProviderConnectionConfiguration` production consumers are exactly
  `connection_document.py` and `connection_service.py`;
- `ProviderConnectionDocumentV1` consumers are exactly persistence + service;
- `ProviderConnectionFileStore` consumer is exactly the service;
- `ProviderConnectionService` has **zero production consumers** in this phase;
- `BoundCredentialLifecycle` consumers remain **0**;
- `BoundSecretResolver` remains consumed only by OpenAIProvider;
- legacy `SecretStore`, direct `WindowsCredentialBackend`, and
  `OpenAICredentialValidator` consumers remain **0**;
- AST import inspection confirms the document imports only dataclass machinery,
  `ProviderConnectionConfiguration`, and safe `SecretIdentifier` metadata;
  persistence imports only stdlib filesystem/JSON utilities plus the document
  codec; service imports only the connection contract, document, and dedicated
  file store;
- schema version is fixed at 1, file bound is 16 KiB, save uses file fsync plus
  same-directory `os.replace`, and clear persists a null document rather than
  deleting the file;
- sealed Phase 8.1-8.4 production files, Phase 7 configuration, requirements,
  context/instruction files, setup and legacy MARK remain unchanged;
- staging remains empty.

The first combined host run exposed one historical Phase 7 guard issue, not a
production defect: the presentation-view freeze treated the generic local variable
name `document` as presentation authority in every future module. The guard was
narrowly corrected so all presentation-specific imports/types/functions remain
forbidden in the new connection stack while the ordinary lexical name `document`
is permitted there. The previously failing guard passed in isolation, and the
complete 288/288, 420/420 and 1,821/1,821 suites subsequently passed. No production
code changed for this correction.

A crude final text scan also matched the word `runtime` in the service docstring
phrase “no runtime wiring”; AST import inspection confirms there is no runtime
import or authority. This was an audit-text false positive only.

No credential backend, OpenAI SDK, network request, environment mutation or native
Credential Manager operation was used or needed. The candidate is independently
validated and remains unstaged for human seal review.

## Explicit non-scope

No bootstrap/default path/path ownership, UI/read model/onboarding, runtime or
application composition, provider factory, provider-to-credential mapping check,
BoundSecretResolver construction, lifecycle/validator wiring, provider/model
selector UX, multiple simultaneous connection registry, schema migration,
directory creation, locking/concurrency API, environment fallback, generic settings,
presentation reuse/modification or secret persistence.

No modifications to connection.py, OpenAI provider/client/validator, AIService,
secrets, config, runtime/session/agent/intent/capability/policy/audit/verification/
memory, package exports, requirements, setup, AGENTS.md, CURRENT_STATE.md, context
script or legacy MARK. No credentials were inspected. No native/network smoke,
workbook update, staging, commit, tag or push.

## Seal-time staging guard reconciliation (8 October 2026)

With the user-approved exact 17-path staging complete, the first focused
seal-time run found one test-only scope-guard failure: the new Phase 8.5 guard
required all three new production files to remain untracked and HEAD to remain
at the starting checkpoint. Correct staging made those files index additions.
The guard in `tests/test_provider_connection_service.py` was narrowly reconciled
within the existing reviewed path: it now requires the exact three-path union
of changed and untracked production files with no overlap, and supports either
the starting HEAD or its direct one-commit sealed descendant. All 95 prior
production files remain explicitly frozen; no production code was modified.

The corrected candidate was restaged and passed authoritative host seal-time
validation: **47/47** focused, **288/288** combined Phase 7+8, **470/470**
expanded affected/trust-path, and **1,821/1,821** full unittest discovery.
`python -m compileall -q nayeon tests` and `git diff --cached --check` also
passed. The approved production delta remains exactly three new non-secret
connection modules; the stage remains exactly the 17 approved review paths.
This note records the local seal-time correction and does not authorize a push,
context refresh, or master-workbook update.
