# Phase 8.3 - Bounded Credential Lifecycle & Typed Provider Connection Configuration

## Starting checkpoint and candidate status

7 October 2026, `C:\AI\Mark-LII`, branch `nayeon-v1`.
Starting HEAD: `09d576adcfc25cbf08ea62b558ccc16c0edc5012`.
Latest sealed product: Phase 8.2, commit
`d620dd6fb67bfed24f5c33b4f3aa9583f3d7f418`, annotated tag
`nayeon-v1-bound-secret-resolver-openai-provider-migration-01`.
Historical full regression baseline: **1707/1707**; this is not a Phase 8.3 result.

Branch, HEAD, clean worktree and annotated milestone tag target matched before
editing. AGENTS.md, CURRENT_STATE.md, Phase 8.2 review, sealed secret contracts,
Windows backend, resolver and relevant tests were read. The context file's
unapproved Phase 8.3 restart note is superseded by explicit user approval and
remains untouched.

This is an unstaged, unsealed implementation candidate, pending independent host
validation and human review. No commit, tag, push, workbook or context update was
performed.

## Exact production scope

Exactly two new production modules:

- `nayeon/secrets/lifecycle.py`
- `nayeon/brain/connection.py`

Every pre-existing production file is unchanged. There are no package exports,
dependencies, runtime consumers or application composition changes.

Two new deterministic suites contain **38 test methods** across lifecycle behavior/privacy,
scope guards and connection metadata. They use synthetic values and structural
fake backends/validators, with no native storage or network implementations.

Necessary historical maintenance affects seven existing test files: the five
Phase 7 presentation scope suites, Windows-backend scope suite, and Phase 8.2
provider consumer guard. Checkpoints advance to the supplied Phase 8.3 start and
sealed Phase 8.2 product; the only permitted production delta is the two new
modules. Earlier provider byte-freeze exemptions are removed: the provider is
now frozen along with every other pre-existing production file. The contract
consumer set adds exactly lifecycle.py and connection.py. Existing provider
migration, privacy, native ABI, cleanup, presentation and trust assertions remain.
The historical Phase 6 guard needs no further maintenance because these new
modules do not change its existing protected paths.

## Bound lifecycle authority and privacy

A generic secret-management service would grant arbitrary-identifier writes,
deletes and reads. BoundCredentialLifecycle permanently binds one backend, one
exact immutable SecretIdentifier and one validator. Its public surface is only
identifier metadata and is_connected, test_candidate, test_stored, connect,
replace and remove. There is no plaintext read/resolve/get/reveal/export API,
enumeration, rebinding, public backend or validator property.

Construction accepts structural provider-neutral dependencies, requiring callable
get/put/delete/is_available and validate methods without invoking them. Exact
SecretIdentifier and public SecretValue arguments are required, with no coercion
or subclasses. The lifecycle is slotted, immutable including reinitialization,
uses object identity equality/hash, has fixed redacted repr/str, and blocks
ordinary pickle/copy/state extraction. It retains only its three dependencies,
never a candidate, stored value or validation result. Backend/validator code can
retain its own inputs; no claim is made about those external implementations.

This is a least-authority application boundary, not cryptographic isolation
inside one Python process. Private state remains introspectable. Neither memory
erasure nor isolation from arbitrary in-process code is claimed.

## Tri-state validation and failure handling

CredentialValidationStatus is an Enum, not a str/int subclass, with exactly
VALID/INVALID/INDETERMINATE and stable values valid/invalid/indeterminate.
CredentialValidator is a narrow Protocol with validate(SecretValue) returning
that exact enum. No concrete provider/network validator is implemented.

test_candidate calls validate exactly once with the exact candidate, without
backend calls. Ordinary validator exceptions, including SecretStorageError and
SecretNotFoundError, become INDETERMINATE; wrong return types do too. Process-control
exceptions such as KeyboardInterrupt/SystemExit are deliberately not swallowed.
No validator exception text escapes. test_stored performs
one get, requires an exact SecretValue, and passes that holder to validation once
without returning plaintext or the holder. Backend missing/storage contract
errors from get propagate unchanged and prevent validation.

is_connected performs one availability call without reading or decoding. remove
performs one delete without a prior read or availability probe. Both require
exact bool results. Backend SecretStorageError propagates unchanged; unexpected
backend Exceptions become SecretStorageError with the fixed message
`Credential lifecycle operation failed` and suppressed display chains. Invalid
backend result types use the same safe message. SecretNotFoundError is only
propagated unchanged for get; it is sanitized as an unexpected error elsewhere.
There is no logging or printing.

## Connect and replace ordering and race limit

connect first checks absence; an existing credential raises the fixed state error
`Credential is already connected` before validation. INVALID/INDETERMINATE return
without writing. VALID triggers a second availability check; newly present state
raises `Credential state changed`. Continued absence permits exactly one put
with the same candidate holder and bound identifier, returning VALID.

replace first requires presence; absence raises `Credential is not connected`
before validation. The existing credential stays untouched through validation.
INVALID/INDETERMINATE perform no write/delete. VALID triggers a second presence
check; absence raises `Credential state changed`. Continued presence permits
one put with the same candidate holder. There is no delete-before-put, old-value
read, rollback or readback.

These rechecks detect state changes during validation. SecretBackend has no
compare-and-swap, so an external writer can still race between the final check
and put for connect or replace. No atomicity, rollback or protection against
external replacement races is claimed.

## Non-secret connection metadata

ProviderConnectionConfiguration is a frozen, slotted dataclass with fields in
order: provider: str, model: str, credential: SecretIdentifier. Its only imports
are dataclass and SecretIdentifier. All fields are safe non-secret metadata;
normal dataclass equality/hash apply.

Provider is an exact native string of length 1..64 using canonical lowercase
ASCII identifier syntax. Model is an exact native string of length 1..128 with
no edge whitespace or nonprintable/control characters; otherwise exact printable
text is preserved, including generic paths, punctuation and Unicode. Neither
field is normalized or constrained by a provider/model allowlist. Credential
requires an exact SecretIdentifier.

The configuration has zero resolution or management authority. It does not
enforce provider-to-credential identity mapping: future trusted composition must
establish that separately. It owns no persistence, codec, service, bootstrap,
read model, environment lookup or network behavior.

## Explicit non-scope and smoke justification

No actual provider validator, OpenAI API/network call, native Credential Manager
smoke/mutation, persistence, lifecycle service/global registry, runtime/session/
application composition, provider/model selection UX, BYOK onboarding UI,
package exports, additional providers, environment fallback/dotenv, plaintext
persistence, generic settings, presentation changes, audit/logging/memory
integration or legacy-store deletion. All Phase 8.1/8.2 production modules,
policy/confirmation/execution/verification paths, root MARK, requirements/setup
and protected context remain unchanged.

Native Credential Manager smoke is unnecessary: the sealed Phase 8.1 native
backend is unchanged. Real provider validation/network smoke is outside this
phase and would not prove the deterministic call ordering, authority limits or
exception containment. Fake dependencies directly exercise those properties.

## Actual validation evidence

Codex could not invoke the authoritative interpreter from its sandbox and therefore
claimed only static evidence. Independent orchestration reviewed the candidate and
made one security-tightening refinement before host validation: validator failures
remain mapped to INDETERMINATE for ordinary Exception subclasses, but
KeyboardInterrupt/SystemExit are no longer swallowed as credential-test results.
A focused test was added for that process-control behavior. One test-harness state
initialization issue introduced while splitting that coverage was then corrected;
production behavior was unaffected.

Authoritative validation ran on the authorized Windows host with:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Final candidate results:

- dedicated Phase 8.3 lifecycle + connection suites: **38/38 passed**;
- combined Phase 7 foundation + all Phase 8 suites and guards: **212/212 passed**;
- affected configuration/secrets + relevant trust/orchestration suite:
  **344/344 passed**;
- full unittest discovery: **1,745/1,745 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent final scope/integrity evidence:

- exact production delta from starting HEAD is only new
  `nayeon/secrets/lifecycle.py` and new `nayeon/brain/connection.py`;
- both starting HEAD and the sealed Phase 8.2 product contain **91** tracked
  production Python files; all **91/91** remain content-identical after ordinary
  checkout newline normalization;
- production Python inventory is now **93**, exactly the prior 91 plus the two
  approved additions;
- `BoundCredentialLifecycle` has **zero production consumers**;
- `ProviderConnectionConfiguration` has **zero production consumers**;
- `BoundSecretResolver` consumer set remains exactly
  `nayeon/brain/providers/openai.py`;
- legacy `SecretStore` has **zero production consumers**;
- `WindowsCredentialBackend` has **zero direct production consumers**;
- connection.py imports only dataclass machinery plus `SecretIdentifier` and
  contains no SecretValue or secret-resolution/management authority;
- lifecycle.py imports only Enum/Protocol plus the sealed provider-neutral secret
  contracts; it imports no Windows backend, resolver, legacy store, provider,
  environment/config, network or logging dependency;
- lifecycle validation does not catch `BaseException`;
- sealed Phase 8.1/8.2 production modules, AIService, Phase 7 config, protected
  context/dependency files and root legacy MARK remain unchanged;
- before human seal staging was empty; after approval exactly the twelve reviewed Phase 8.3 paths were staged.

No native Credential Manager smoke or real provider/network call was performed or
needed. Phase 8.1 already proved the unchanged native backend, while Phase 8.3
adds only deterministic lifecycle/config contracts with fake dependencies.

## Handoff

Human seal approval was received. Exactly the twelve reviewed Phase 8.3 paths were
staged with no unstaged or unrelated untracked changes. Seal-time validation of
that staged candidate repeated successfully: the dedicated lifecycle/connection
suite remained **38/38 passed**, the combined Phase 7 foundation + all Phase 8
suites remained **212/212 passed**, full unittest discovery remained
**1,745/1,745 passed**, and `python -m compileall -q nayeon tests` completed
successfully. `git diff --cached --check` also passes.

The prior independently validated affected configuration/secrets + relevant
trust/orchestration result remains **344/344 passed**; production code did not
change after that run.

At this review-document checkpoint no product commit, annotated tag, push, Google
Drive workbook update or `.codex/CURRENT_STATE.md` refresh had yet occurred.

Production scope remains exactly the two approved new modules. Actual provider
credential validation, connection persistence/ownership, runtime composition and
BYOK onboarding remain future Phase 8 gates.
