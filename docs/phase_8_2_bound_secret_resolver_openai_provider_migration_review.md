# Phase 8.2 — Bound Secret Resolver & OpenAI Provider Migration

## Starting checkpoint and candidate status

7 October 2026, `C:\AI\Mark-LII`, branch `nayeon-v1`.
Starting HEAD: `e116eaaa25b34e1af6f74c6b604684b15aad2859`.
Latest sealed product: Phase 8.1, commit
`5b57221720a298477ef83ef54891c07b7126c496`, annotated tag
`nayeon-v1-secure-secret-windows-credential-storage-01`.
Historical full regression baseline: **1681/1681**; this is not a Phase 8.2 result.

Branch, HEAD, clean worktree and annotated tag target matched before editing.
AGENTS.md, CURRENT_STATE.md, Phase 8.1 review, sealed contracts/backend and
relevant provider/tests were read. The state file's unapproved restart note is
superseded by the user's explicit Phase 8.2 approval and remains untouched.
This candidate is unstaged and unsealed, pending independent host validation
and human seal review. No commit, tag, push or workbook update was performed.

## Exact production scope

- New `nayeon/secrets/resolver.py`.
- Modified `nayeon/brain/providers/openai.py`.

All other production files remain unchanged, including sealed contracts,
Windows backend, legacy store, package exports, AIService, configuration,
presentation, runtime and root MARK. No dependencies were added.

Two new deterministic suites contain 26 test methods: 13 resolver tests and
13 provider tests. SDK construction is patched; values are synthetic. Necessary
historical scope-guard maintenance was made in five Phase 7 suites, the
Windows-backend suite and one Phase 6.22 clickability freeze guard: advance the
current Phase 8 checkpoints where appropriate, permit exactly the resolver/provider
delta, exempt only the intentionally modified provider from older byte-frozen
comparisons, and require zero legacy store consumers. Existing behavioral, trust,
presentation, native ABI and cleanup assertions remain. New tests constrain the
exact provider imports and secret consumer sets.

## Least authority and privacy

Direct backend injection would grant provider code arbitrary-identifier reads,
writes, deletes and availability checks. BoundSecretResolver privately binds
one backend and one exact immutable SecretIdentifier. Its public surface is
only `identifier` and `resolve`; there is no management, enumeration or rebinding
API. Construction checks only that `get` is callable, never invoking storage
operations or probing management operations. Exact identifier types are required.

The resolver is slotted and immutable, rejects reinitialization, uses identity
equality and fixed redacted repr/str, and blocks ordinary pickle/copy/state
extraction. It does not retain resolved values. Each resolve invokes get once
with the exact bound identifier and requires an exact SecretValue result.
Sealed contract errors propagate unchanged; backends are responsible for their
contract's safe messages. Unexpected Exceptions become SecretStorageError with
`Secret resolution failed` and suppressed display chains. Wrong result types
use the same fixed message. No logging, environment, network, configuration,
provider or Windows-backend dependency is introduced in the resolver.

This interface bounds authority, not cryptographic isolation within one Python
process. Private state remains introspectable; neither memory erasure nor
protection from arbitrary code in that process is claimed.

## Provider boundary and failure behavior

OpenAIProvider requires an exact BoundSecretResolver bound to exactly
`SecretIdentifier("openai.api_key")`. Wrong identifiers raise ValueError with
`API key resolver has an invalid identifier` before any resolution. Construction
does not read a secret or create a client. Model defaults and existing unvalidated
model semantics remain unchanged.

First client use resolves once and explicitly reveals the SecretValue only at
the provider SDK boundary, passing the exact plaintext as `OpenAI(api_key=...)`.
Neither holder nor plaintext is stored on the provider. After SDK construction
succeeds, the client is cached and the provider's resolver reference becomes
None. Subsequent use reuses that client without resolving again.

Resolution failures propagate and retain resolver authority for retry without
creating a client. SDK construction Exceptions become the provider-local
OpenAIProviderInitializationError(RuntimeError), with exactly
`OpenAI provider initialization failed` and suppressed underlying display chains.
No client is cached on failure; retry resolves again. Response-generation errors
remain untranslated. Input, instructions and usage normalization are preserved.

Legacy SecretStore now has zero production consumers but remains unchanged.
WindowsCredentialBackend remains provider-neutral with zero production consumers.
Only OpenAIProvider consumes BoundSecretResolver. The provider imports safe
SecretIdentifier metadata but neither SecretBackend nor WindowsCredentialBackend.

## Explicit non-scope

No runtime/application composition, production Windows backend construction,
provider/model selection or persistence, onboarding UI, connect/test/replace/remove
workflow, environment/migration fallback, dotenv support, plaintext persistence,
secret enumeration, package export, AIService/prompt/routing change or presentation
change. No real credential or network call is used.

Native Credential Manager smoke is unnecessary: the sealed native backend and
contracts are unchanged, and this phase changes only a pure binding interface
and mocked SDK construction boundary. A real OpenAI call would not prove these
authority/retry properties and would exceed approved scope.

## Actual validation evidence

Codex could not invoke the authoritative interpreter from its sandbox and therefore
claimed only static evidence. Independent orchestration then reviewed and validated
the candidate on the authorized Windows host using:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Two test-only issues were corrected before final validation. First, the host does
not currently have the OpenAI SDK installed, so the provider suite now injects a
deterministic fake `openai` module before importing our provider; no package
installation or network workaround was used. Second, an over-restrictive resolver
test incorrectly rejected `dict`, despite the approved constructor intentionally
requiring only a callable `get` read surface. The test was corrected to match that
minimal structural contract. Full discovery then exposed one stale Phase 6.22
byte-freeze guard for `openai.py`; it was narrowly maintained to exempt only the
approved Phase 8.2 provider migration while retaining all other historical freeze
checks.

Authoritative host results after those corrections:

- dedicated Phase 8.2 resolver + provider suites: **26/26 passed**;
- combined Phase 7 foundation + all Phase 8.1/8.2 suites and guards:
  **174/174 passed**;
- affected configuration/secrets + relevant trust/orchestration suite:
  **306/306 passed**;
- full unittest discovery: **1,707/1,707 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent final scope/integrity evidence:

- exact production delta from starting HEAD is only modified
  `nayeon/brain/providers/openai.py` plus new `nayeon/secrets/resolver.py`;
- the production Python inventory is **91**; the starting/sealed Phase 8.1
  inventories each contain **90** tracked Python files, and all **89**
  pre-existing files other than the intentionally modified provider remain
  content-identical after ordinary checkout newline normalization;
- sealed `nayeon/secrets/contracts.py`,
  `nayeon/secrets/windows_credential.py` and legacy `nayeon/secrets/store.py`
  remain content-identical;
- `BoundSecretResolver` has exactly one production consumer:
  `nayeon/brain/providers/openai.py`;
- legacy `SecretStore` has **zero** production consumers;
- `WindowsCredentialBackend` has **zero** direct production consumers;
- only resolver.py imports the `SecretBackend` authority contract;
- OpenAIProvider contains no `SecretStore`, `SecretBackend`,
  `WindowsCredentialBackend` or `OPENAI_API_KEY` dependency/literal;
- resolver.py contains no Windows-backend, legacy-store, environment/config,
  provider/network or logging dependency;
- protected context/dependency files, AIService, sealed Phase 8.1 secret files
  and root legacy MARK remain unchanged;
- before human seal staging was empty; after approval exactly the twelve reviewed Phase 8.2 paths were staged.

No native Credential Manager smoke or real OpenAI network call was performed or
needed. Phase 8.1 already proved the unchanged native storage backend; Phase 8.2
is a deterministic authority-binding/provider-construction migration and is fully
covered with fake backends and a fake SDK boundary.

## Handoff

Human seal approval was received. Exactly the twelve reviewed Phase 8.2 paths were
staged with no unstaged or unrelated untracked changes. Seal-time validation of
that staged candidate repeated successfully: the dedicated resolver/provider suite
remained **26/26 passed**, the combined Phase 7 foundation + all Phase 8 suites
remained **174/174 passed**, full unittest discovery remained **1,707/1,707
passed**, and `python -m compileall -q nayeon tests` completed successfully.
`git diff --cached --check` also passes.

The prior independently validated affected configuration/secrets + relevant
trust/orchestration result remains **306/306 passed**; production code did not
change after that run.

At this review-document checkpoint no product commit, annotated tag, push, Google
Drive workbook update or `.codex/CURRENT_STATE.md` refresh had yet occurred.

Production changes remain exactly the approved pair: one new bounded resolver and
the OpenAI provider migration. Provider selection, model configuration, runtime
composition and BYOK lifecycle/onboarding remain future Phase 8 gates.
