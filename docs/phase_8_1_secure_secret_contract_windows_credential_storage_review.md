# Phase 8.1 secure secret contract and Windows credential storage review

## Starting checkpoint and candidate status

- Date: 7 October 2026; repository: `C:\AI\Mark-LII`.
- Branch: `nayeon-v1`; starting/current HEAD:
  `e50a0e24289d9ab4452ad9e34c8bee1408db851a`.
- Latest sealed product: Phase 7.6, Bounded Presentation Read Model & Phase 7
  Foundation Closure, commit `a39d06409e1a602c0fd0cfa605aac89e24505aab`.
- Annotated tag: `nayeon-v1-presentation-read-model-foundation-closure-01`,
  verified to resolve to that product commit.
- Supplied sealed full regression baseline: **1645/1645**. This is historical
  evidence, not a Phase 8.1 execution result.
- Branch, HEAD and clean worktree matched the requested start before editing.
  Root `AGENTS.md`, `.codex/CURRENT_STATE.md`, the Phase 7.6 review, existing
  SecretStore/OpenAIProvider and relevant historical guards were inspected.

The state file still describes Phase 8 as unapproved. The user's explicit bounded
Phase 8.1 approval supersedes that restart note; the state file is untouched.
This is an unsealed candidate for independent validation and human review.

## Exact scope

Exactly two new production modules:

- `nayeon/secrets/contracts.py`: provider-neutral identifier, opaque secret value,
  new error classes and narrow storage Protocol.
- `nayeon/secrets/windows_credential.py`: fixed-namespace backend and private
  ctypes Advapi32 adapter.

New deterministic suites are `tests/test_secure_secret_contracts.py` (12 test
methods) and `tests/test_windows_credential_backend.py` (24 test methods).
The latter includes fake backend/native-pointer lifecycle and source-scope guards.
All test credential values are synthetic.

Only necessary historical test maintenance was made in the presentation identity,
persistence, service, bootstrap and view suites: advance the starting HEAD and
protected product/tag to Phase 7.6, allow exactly the two approved additions, and
retain all existing per-file content, security, consumer and runtime assertions.
The bootstrap scope-test name now describes the current protected milestone.
No presentation consumer allowlist was expanded.

No existing production file or package export changes. Old environment-backed
`nayeon/secrets/store.py` and `OpenAIProvider` remain frozen; OpenAIProvider remains
the sole production importer of that store. The new backend has zero production
consumers. The new contracts are consumed only by the new backend, with zero
consumers elsewhere in production. No migration, provider/model selection,
onboarding, UI, runtime/session composition, prompts, memory, audit, generic
settings, authority pipeline or root MARK changes are included.

## Contract semantics and redaction

`SecretIdentifier` is a frozen/slotted dataclass with one required field,
`value: str`. Only exact native strings pass. Length is 1..128; the first character
is lowercase ASCII a-z or 0-9, and remaining characters additionally permit `.`,
`_` and `-`. Whitespace, uppercase, Unicode syntax, coercion and normalization
are rejected. Identifiers are safe metadata, with no provider allowlist.

`SecretValue` is a manually immutable, slotted, non-dataclass holder. It rejects
non-native strings and empty/whitespace-only text, and otherwise retains the
original string exactly, including surrounding whitespace, Unicode and NULs.
It has no public plaintext field/property or instance dictionary. Its only public
method is `reveal() -> str`; repr and str always return
`SecretValue(<redacted>)`. Equality/hash are inherited identity operations.
Assignment, deletion and reinitialization fail. There are no iteration, bytes,
mapping, export or dataclass-asdict helpers. Pickle reduction and inherited
slot-state extraction are explicitly blocked with fixed-message rejection hooks.

Redaction is an accidental-display boundary, not cryptographic memory protection.
Python strings, UTF-8 buffers and eventual provider SDK use necessarily create
plaintext in process memory. Private attributes remain introspectable; guaranteed
zeroization or protection from code executing in the same process is not claimed.
The native write adapter clears its own ctypes buffer in a finally block, without
claiming that every Python copy is erased.

`SecretBackend` exposes exactly `get`, `put`, `delete`, and `is_available` with the
approved typed signatures. New `SecretNotFoundError` and `SecretStorageError`
are RuntimeError subclasses distinct from the legacy store error. Downstream use
in this backend has only fixed safe messages.

## Windows mapping and native ownership

Targets are exactly `nayeon-v1/secret/` + the exact identifier value. Fixed internal
metadata is `CRED_TYPE_GENERIC = 1`, `CRED_PERSIST_LOCAL_MACHINE = 2` and username
`nayeon-v1`. These constants never derive from presentation names, user names,
environment, configuration, providers or models. LOCAL_MACHINE persistence means
the credential persists for the same Windows user on this computer, not a
machine-wide shared credential. Generic blobs are application-defined; this
application uses strict UTF-8. The maximum blob size is **2560 bytes**.
These choices follow the [Windows CREDENTIALW contract](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw).

Construction performs no credential operation or native setup. Import creates
ctypes declarations only; `WinDLL` is accessed lazily on the first real operation.
Unavailable DLL/platform/API setup fails closed. The private injected adapter seam
lets tests run without loading the real DLL. No dependency was added.

The native adapter declares the complete CREDENTIALW and credential-attribute
layouts using Windows-width integers, FILETIME and typed pointers, plus explicit
argtypes/restype for CredReadW, CredWriteW, CredDeleteW and CredFree.
Successful reads have one finally-block owner that calls CredFree exactly once.
Read copies exactly CredentialBlobSize bytes before release and rejects invalid
sizes/null blob pointers. Presence obtains/frees the credential pointer without
dereferencing it or copying/decoding its blob. See Microsoft's
[CredReadW ownership contract](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credreadw)
and [CredFree](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credfree).

- `get`: missing native credential becomes new-contract SecretNotFoundError with
  `Secret is not available`. Strict UTF-8 decode errors, blank values, malformed
  blobs and other failures become SecretStorageError with
  `Secret storage operation failed`.
- `put`: exact SecretValue required; reveal/UTF-8 encoding preserves text exactly.
  Oversized blobs fail before adapter setup/write. Same-target replacement uses
  ordinary [CredWriteW semantics](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew)
  with zero flags and the fixed metadata.
- `delete`: successful deletion returns True; ERROR_NOT_FOUND (1168) returns
  False; other errors become the fixed SecretStorageError.
- `is_available`: native presence only; missing returns False, present returns
  True even when the blob would be unreadable, and other failures raise the fixed
  SecretStorageError. It never constructs SecretValue.

All public operations require exact SecretIdentifier; put also requires exact
SecretValue. Invalid argument types fail before native access with fixed TypeError
messages. Native error strings, targets and values are never included in public
exception messages; underlying exception display chains are suppressed. There is
no FormatError, enumeration, public arbitrary-target operation, environment
fallback, file persistence, config lookup, logging, printing or network/provider
call.

## Actual validation and independent host evidence

Codex could not invoke the authoritative interpreter from its sandbox and therefore
claimed only static evidence. Independent orchestration reviewed the candidate,
removed one duplicated `SecretValue.__getstate__` definition found during review,
and then ran the final candidate on the authorized Windows host using:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Authoritative host results:

- dedicated Phase 8.1 secret-contract + Windows-backend suites: **36/36 passed**;
- combined Phase 7.1-7.6 foundation + Phase 8.1 suites/guards: **148/148 passed**;
- affected configuration/secrets plus relevant trust/orchestration suite:
  **280/280 passed**;
- full unittest discovery: **1,681/1,681 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent scope/integrity evidence:

- all **88/88** pre-existing tracked Python production files under `nayeon/`
  match both the Phase 8.1 starting HEAD and sealed Phase 7.6 product commit
  after checkout newline normalization; zero mismatches;
- production Python inventory is **90**, with exactly two new production files:
  `nayeon/secrets/contracts.py` and `nayeon/secrets/windows_credential.py`;
- there are zero production consumers of the new secret contracts/backend outside
  those two new modules;
- the old environment-backed `SecretStore` remains unchanged and its sole
  production consumer remains `OpenAIProvider`;
- no forbidden config, presentation, environment-variable, provider/model, runtime,
  memory, logging, CredEnumerate or FormatError dependency appears in the new modules;
- `AGENTS.md`, `.codex/CURRENT_STATE.md`, dependency files, old secret store,
  OpenAI provider/AI service, package init files and root legacy MARK remain unchanged;
- before human seal staging was empty; after approval exactly the ten reviewed Phase 8.1 paths were staged.

### Controlled native Windows Credential Manager smoke

After source review and deterministic test validation, independent orchestration
performed one bounded native smoke using a randomly named disposable identifier in
the fixed `nayeon-v1/secret/` namespace and a synthetic Unicode value. No real API
key, personal credential, environment secret or provider call was used.

The observed sequence was:

- credential initially absent: **True**;
- available after `put`: **True**;
- exact UTF-8/Unicode `get` round-trip matched: **True**;
- `delete` reported an existing credential removed: **True**;
- credential absent after deletion: **True**.

The smoke used `finally` cleanup and the explicit post-delete absence check passed.
No disposable smoke credential remained according to the backend's native presence
check.

The 36 deterministic tests cover exact contract shape/types, identifier syntax,
plaintext redaction and serialization rejection, exact UTF-8 preservation, byte
limits, missing/failure mapping, no enumeration, presence-only reads, fake native
ABI/resource ownership, exact CredRead/CredWrite/CredDelete metadata, CredFree
ownership, write-buffer cleanup, import safety, zero consumers, frozen prior
production, protected dependencies and unchanged legacy/provider boundaries.

## Handoff

Human seal approval was received. Exactly the ten reviewed Phase 8.1 paths were
staged with no unstaged or unrelated untracked changes. Seal-time validation of
that staged candidate repeated successfully: the combined Phase 7 foundation +
Phase 8.1 suite remained **148/148 passed**, full unittest discovery remained
**1,681/1,681 passed**, `python -m compileall -q nayeon tests` completed
successfully, and `git diff --cached --check` passes.

The earlier controlled disposable Windows Credential Manager smoke remains valid
for the same production candidate: absent -> put -> available -> exact Unicode
round-trip -> delete -> absent, with all checks true and cleanup confirmed.

At this review-document checkpoint no product commit, annotated tag, push, Google
Drive workbook update or `.codex/CURRENT_STATE.md` refresh had yet occurred.

The existing environment-backed SecretStore and OpenAIProvider intentionally remain
unchanged. Provider migration, secret-service ownership/resolution, provider/model
configuration and BYOK onboarding remain future Phase 8 gates.
