# Phase 8.6 — Trusted Provider Connection Composition & Explicit Bootstrap

## Starting checkpoint, approval and current candidate state

8 October 2026, repository `C:\AI\mark-lii`, branch `nayeon-v1`.
Protected starting HEAD: `a1b12832407748b6aa401f2efe3e8e9899ad9741`.
Latest completed product phase: Phase 8.5, annotated tag
`nayeon-v1-provider-connection-ownership-persistence-01`, peeled product
commit `d6661f6e0ac02e881056bf98c49df20618758c79`.
Starting full regression baseline: **1,821/1,821**, not a Phase 8.6 result.

The user explicitly approved bounded Phase 8.6 implementation and independent
validation but withheld authorization for the human seal, staging, commit, tag,
push, context refresh and workbook update. The baseline branch/HEAD/worktree
were verified clean before implementation. Current source changes are deliberately
unstaged and unsealed.

## Exact approved production implementation — two new modules only

- NEW `nayeon/brain/connection_bootstrap.py`
- NEW `nayeon/brain/connection_composition.py`

No existing production file was edited. The original **98** production Python
files and `requirements.txt` are protected against the Phase 8.5 product tag
by a dedicated new Git/content scope test. The only permitted production
additions are these two files, bringing the candidate Python inventory to 100.

### Explicit connection bootstrap

`bootstrap_provider_connection(path: Path) -> ProviderConnectionService`
constructs the sealed `ProviderConnectionFileStore` from the exact
caller-provided native concrete Path, then a new `ProviderConnectionService`,
invokes `initialize()` once and returns the initialized owner. It introduces
no default/home/env path, directory creation, path permission mutation,
singleton, provider activation, credential backend, resolver or network request.

A missing document yields the sealed in-memory unconfigured connection,
without writing a file. File and schema errors use the existing persistence
boundary; the new bootstrap performs no error rewrites or fallback.

### Fail-closed trusted AI composition

`compose_provider_ai_service(connection_service: ProviderConnectionService,
backend: SecretBackend) -> AIService` is a caller-invoked seam, not a
model-selectable route. It enforces these requirements **before touching the
backend or constructing a resolver/provider**:

1. exact `ProviderConnectionService` type;
2. initialized owner with exact `ProviderConnectionDocumentV1`;
3. active exact `ProviderConnectionConfiguration`, not `None`;
4. provider string exactly `openai`;
5. credential exactly `SecretIdentifier("openai.api_key")`.

Missing, malformed, unsupported and mismatched metadata produce fixed,
credential-free local error messages. No arbitrary provider registry, endpoint
or credential ID can be selected from persisted metadata.

After metadata gating, composition constructs an exact
`BoundSecretResolver(backend, SecretIdentifier("openai.api_key"))` using the
**trusted constant** (not the serialized identifier), passes it to the already
sealed `OpenAIProvider` together with the configured model text unchanged,
then wraps the provider in `AIService`. The sealed resolver checks that the
backend exposes a callable `get` method during construction; it does **not**
invoke the credential read. The provider/client remain lazy until a future
trusted caller invokes generation. Composition neither saves metadata nor
performs credential validation, secret reads, native storage operations or
network requests.

The backend itself is a trusted caller-injected dependency; the service
does not grant authority merely because metadata is persisted. Plaintext
secrecy inside Python/provider SDK memory is not claimed. A configuration's
model text is syntactically validated by the sealed contract, but availability
and authorization of that model remain unproven until provider execution.

## Deterministic test implementation and reconciled historical guards

Two new suites:
- NEW `tests/test_provider_connection_bootstrap.py`
- NEW `tests/test_provider_connection_composition.py`

The new suites contain **29 tests** including an exact freeze against all 98
sealed Phase 8.5 production files and unchanged requirements. Synthetic
documents, temp directories, mocked provider factories and fake/hostile
backends test exact type gates, unsupported provider, wrong credential,
unconfigured/uninitialized owner, trust-check-before-backend-access ordering,
lazy composition, exact model pass-through, safe errors, explicit file path,
load/initialization behavior and no eager activation. They never inspect a live
credential or invoke SDK/native/network functions.

Necessary historical test-only reconciliation is restricted to these ten paths:

- `tests/test_bound_credential_lifecycle.py`
- `tests/test_openai_canonical_client.py`
- `tests/test_openai_provider_secure_secret.py`
- `tests/test_presentation_configuration_bootstrap.py`
- `tests/test_presentation_configuration_persistence.py`
- `tests/test_presentation_configuration_service.py`
- `tests/test_presentation_configuration_view.py`
- `tests/test_presentation_identity_contracts.py`
- `tests/test_provider_connection_service.py`
- `tests/test_windows_credential_backend.py`

Historical exact source-delta tests now permit only the prior Phase 8.5 three
modules plus Phase 8.6's two new paths. Consumer sets allow exactly the new
composition/bootstrap imports of connection contracts and the least-authority
resolver; no lifecycle-management authority or Windows native backend consumer
is authorized. The separate OpenAI secure-secret consumer guard permits only
the explicit new composition import. Presentation/legacy freezes and original
metadata/secret producer content checks remain in place.

An existing presentation-layer lexical guard treats any bare local identifier
`document` as presentation authority. Rather than weakening that guard, the
new composition uses the local name `connection_document` while preserving
identical behavior.

## Engineering execution and independent validation

The existing Codex Windows CLI's restricted tool execution failed with
`helper_unknown_error: setup refresh had errors`. No code was produced by
that failed direct execution session. Codex GPT-6.1 Sol / High instead generated
the four new file contents in a **text-only, no-tools** session outside the
repository. Each file was independently allowlist-checked and AST-parsed
before Desktop Commander wrote it to the approved path. Minor invalid test
fixtures were corrected against the sealed model string and resolver error
contracts, without editing protected production code.

Authoritative independent validation uses
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`.

Verified results so far:

- Phase 8.6 focused bootstrap + composition + production freeze: **29/29 PASS**.
- Combined Phase 7+8 configuration/secrets/connection suite: **317/317 PASS**.
- Expanded affected/trust/orchestration suite: **499/499 PASS**.
- Full repository `unittest` discovery: **1,850/1,850 PASS**.
- `python -m compileall -q nayeon tests`: **PASS**.
- `git diff --check`: **PASS** in the final authoritative run.

The first full discovery before historical reconciliation had **15 historical
scope/consumer guard failures** out of 1,849 tests; no new production behavior
failure. Narrow corrections resolved those issues and the subsequent full
discovery passed **1,849/1,849**. After adding the one 98-file freeze guard,
the final test count is **1,850**. Final authoritative discovery passed
**1,850/1,850**, together with `compileall` and `git diff --check`.

## Explicit non-scope and seal gate

No changes to the sealed provider, secret contracts, secret resolver,
credential lifecycle, native backend, Phase 7 presentation configuration,
Phase 8.5 persisted document/service, AIService, package exports, requirements,
runtime/session/agent policy/confirmation/audit/verification, memory, UI,
legacy MARK or the root instruction and Codex context files.

No provider model availability check; no credential presence check or validator
request; no native Credential Manager manipulation; no OpenAI SDK/network smoke;
no automatic activation or switching; no BYOK onboarding UI; no alternate
providers, endpoints, secrets, registry or default config location.

The human seal requires separate approval after final independent validation,
exact path review and documented limitations. There must be no staging, commit,
tag, push, workbook update or Codex context refresh before that approval.
