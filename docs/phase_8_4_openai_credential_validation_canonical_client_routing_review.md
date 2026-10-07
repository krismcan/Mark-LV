# Phase 8.4 - OpenAI Credential Validation & Canonical Client Routing

## Starting checkpoint and candidate status

7 October 2026, `C:\AI\Mark-LII`, branch `nayeon-v1`.
Starting HEAD: `e809cd70f445dc77e8eab6187dd18635b438632a`.
Latest sealed product: Phase 8.3, commit
`e59c7588f15547e4f1eb89261dbe8f89e8ef6929`, annotated tag
`nayeon-v1-bounded-credential-lifecycle-provider-connection-01`.
Historical full regression baseline: **1745/1745**, not a Phase 8.4 result.

Continuation began from the existing unstaged candidate; no clean-worktree claim
is made for this continuation. Branch, HEAD and annotated milestone target matched
the Phase 8.3 handoff before editing.
AGENTS.md, CURRENT_STATE.md, the Phase 8.3 review, secret contracts, lifecycle
validation enum, provider and relevant tests were read. The context's broader,
unapproved restart scope is superseded by the user's bounded Phase 8.4 approval.
The context file remains unchanged.

This is a **complete implementation candidate, unstaged and unsealed**, independently validated and pending human seal review. The user clarified that the validator must import
the sealed `CredentialValidationStatus` enum from `nayeon.secrets.lifecycle`.
Only that enum is imported from lifecycle; no lifecycle authority, Protocol
inheritance/registration, alternate enum or contract modification was added.
The shared factory, validator, provider migration, dependency pin, deterministic
test suites and historical guard reconciliation are written.

No commit, tag, push, staging, workbook or context update was performed.

## Exact approved production scope

- NEW `nayeon/brain/providers/openai_client.py`
- NEW `nayeon/brain/providers/openai_validation.py`
- MODIFY `nayeon/brain/providers/openai.py`
- MODIFY `requirements.txt`

All four paths constitute the actual production delta.
The dependency change adds exactly `openai==3.26.0` under a Nayeon AI/provider
comment. No unrelated dependency changes or installation were performed.

## Shared construction boundary and routing rationale

`create_openai_client` accepts only exact `SecretValue` plus optional bounded
timeout/retry inputs. Timeout requires exact int/float, excludes bool and numeric
subclasses, and must be finite and positive. Positive Python integers are finite;
they need no potentially overflowing conversion to float. Retries require exact
nonnegative int. Validation precedes SDK loading and reveal.

The secret is revealed once and the SDK is loaded lazily through a private helper
using only the public `OpenAI` and `DefaultHttpxClient` exports. Module import and
test discovery therefore do not require an installed SDK.

The dedicated HTTP client receives exactly `trust_env=False` and
`follow_redirects=False`. OpenAI receives the exact revealed API key, explicit
`https://api.openai.com/v1`, explicit `Authorization: Bearer <selected key>` and
that dedicated HTTP client. Optional timeout/retry kwargs are omitted when
unsupplied, preserving SDK defaults rather than passing None.

The explicit base URL defeats SDK ambient OPENAI_BASE_URL fallback. Disabling
HTTP environment trust prevents environment proxy/trust overrides; disabling
redirect following prevents credential routing through followed redirects.
Explicit Authorization prevents ambient OPENAI_CUSTOM_HEADERS Authorization from
superseding the selected key under the specified pinned SDK behavior. Nayeon
does not read or mutate environment variables. No caller-selected endpoint,
proxy, headers, transport, organization/project or HTTP client is accepted.
These are design requirements supplied for this phase, not claims of an actual
SDK/network integration test in this sandbox.

Ordinary construction failures yield fixed
`OpenAIClientConstructionError("OpenAI client construction failed")` with a
suppressed display chain. Failed SDK construction closes the dedicated HTTP
client once best-effort, including when SDK construction is interrupted.
Ordinary cleanup failures are contained; process-control exceptions propagate.
There is no logging, printing or module-level credential cache.

## Implemented validator boundary

`OpenAICredentialValidator` has `__slots__=()` and accepts only exact SecretValue,
rejecting other inputs before construction. It calls the shared factory once with
`timeout_seconds=5.0`, `max_retries=0`, then makes one `client.models.list()` call
without examining or iterating the response. It attempts client.close exactly
once in finally after successful construction, including request interruption.

Successful request and cleanup yield VALID. Ordinary construction/request/close
failures yield INDETERMINATE without provider messages. INVALID is deliberately
unused: authentication/401 failures can also reflect organization membership,
endpoint permission or IP allowlist restrictions. Process-control exceptions
propagate, and request interruption still attempts cleanup. No caching,
direct SDK import, backend authority or lifecycle composition is authorized.

## Provider authority invariants

OpenAIProvider now delegates the exact resolved SecretValue to the shared factory
once with no validation timeout/retry overrides. It has no direct SDK import or
reveal call. Exact BoundSecretResolver and openai.api_key identity gates,
constructor laziness, resolution on each failed construction attempt,
successful-client caching and resolver release remain intact. Ordinary factory
failures retain the resolver and yield the existing fixed initialization error.
Process-control exceptions propagate. Generate requests and usage normalization
are unchanged.

The SDK client necessarily retains authentication material. Python locals and
SDK internals can contain plaintext in process memory; no guaranteed memory
erasure or cryptographic in-process isolation is claimed.

## Tests, guards and actual validation

Written canonical-client tests use synthetic SecretValue holders and fake SDK
constructors. Provider tests patch the shared factory and preserve sealed
resolver, retry, privacy and request assertions. Necessary historical maintenance
advances seven scope suites to the supplied start and sealed Phase 8.3 product,
allows only the two approved additions and provider modification under nayeon,
and preserves content freezes for all other existing production files. The
requirements freeze is replaced by an exact pin-only delta guard, permitting only
ordinary checkout newline conversion in otherwise unchanged bytes. Production
Python inventories add exactly the two new modules; requirements is checked
separately. The lifecycle consumer guard exempts only the exact validator's
enum-only import and continues to reject new bound lifecycle authority consumers.
No actual runtime test outcome is claimed.

The new validator suite covers exact input rejection, stateless slots/signature,
exact factory arguments and call order, successful probes, uninspected responses,
ordinary construction/request/cleanup failures, authentication-shaped failures
remaining INDETERMINATE, process-control propagation at all three stages,
request interruption with cleanup, repeated fresh probes, and exact import/call
boundaries. Canonical-client and secure-provider suites were re-read after the
validator addition. Canonical tests also cover reveal failure sanitization and
exact HTTP cleanup counts during construction interruption. All dependencies
are patched factories or synthetic SDK fakes; no SDK installation is needed.

Available evidence:

Independent orchestration completed authoritative host validation with:

`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

Final candidate results:

- focused canonical-client + credential-validator + migrated-provider suites:
  **42/42 passed**;
- combined Phase 7 foundation + all Phase 8 suites and guards:
  **241/241 passed**;
- affected configuration/secrets + relevant trust/orchestration suite:
  **373/373 passed**;
- full unittest discovery: **1,774/1,774 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Independent scope/integrity evidence:

- exact approved production delta from starting HEAD is:
  modified `nayeon/brain/providers/openai.py`, new
  `nayeon/brain/providers/openai_client.py`, new
  `nayeon/brain/providers/openai_validation.py`, and modified `requirements.txt`;
- both starting HEAD and sealed Phase 8.3 product contain **93** tracked
  production Python files; all **92/92** pre-existing files other than the
  intentionally modified OpenAI provider remain content-identical after normal
  checkout newline normalization;
- production Python inventory is now **95**, exactly the prior 93 plus the two
  approved provider modules;
- sealed Phase 8.1/8.2/8.3 secret contracts, Windows backend, resolver,
  lifecycle, legacy store and provider-connection metadata remain unchanged;
- `BoundCredentialLifecycle` has **zero production consumers**;
- `ProviderConnectionConfiguration` has **zero production consumers**;
- `BoundSecretResolver` remains consumed only by
  `nayeon/brain/providers/openai.py`;
- legacy `SecretStore` has **zero production consumers**;
- `WindowsCredentialBackend` has **zero direct production consumers**;
- `OpenAICredentialValidator` itself has **zero production consumers** in this
  phase;
- `create_openai_client` is consumed exactly by OpenAIProvider and
  OpenAICredentialValidator;
- AST-exact inspection confirms openai_validation.py imports only
  `CredentialValidationStatus` from `nayeon.secrets.lifecycle`; it does not
  import BoundCredentialLifecycle or CredentialValidator authority;
- requirements contains exactly one active `openai==3.26.0` line and removing
  the three-line Nayeon dependency addition leaves the prior requirements
  content unchanged after ordinary newline normalization;
- the shared client factory pins `https://api.openai.com/v1`, passes
  `trust_env=False`, passes `follow_redirects=False`, supplies explicit
  Authorization from the selected SecretValue, performs SDK import lazily and
  contains no environment lookup;
- OpenAIProvider has no direct OpenAI SDK import and no direct `.reveal()` call;
- OpenAICredentialValidator never returns INVALID and does not catch
  BaseException;
- protected context, setup, Phase 7 config, AIService and root legacy MARK files
  remain unchanged;
- before human seal staging was empty; after approval exactly the fifteen reviewed Phase 8.4 paths were staged.

The initial audit helper produced two false-positive consumer/text findings:
it treated any import from `nayeon.secrets.lifecycle` as a BoundCredentialLifecycle
consumer and used a crude string test for the enum-only import. An AST-exact
follow-up proved the intended boundary: enum-only lifecycle import, zero bound
lifecycle consumers. These were audit-script issues, not production defects.

No SDK package installation, real API key, OpenAI network request, native
Credential Manager mutation or environment manipulation was performed. The
candidate is independently validated and remains unstaged for human seal review.


## Seal-time validation

Human seal approval was received. Exactly the fifteen reviewed Phase 8.4 paths were staged with no unstaged or unrelated untracked changes. Seal-time validation of that staged candidate repeated successfully: the focused canonical-client/validator/provider suite remained **42/42 passed**, the combined Phase 7 foundation + all Phase 8 suites remained **241/241 passed**, full unittest discovery remained **1,774/1,774 passed**, and `python -m compileall -q nayeon tests` completed successfully. `git diff --cached --check` also passes.

The prior independently validated affected configuration/secrets + relevant trust/orchestration result remains **373/373 passed**; production code did not change after that run.

At this review-document checkpoint no product commit, annotated tag, push, Google Drive workbook update or `.codex/CURRENT_STATE.md` refresh had yet occurred.

## Explicit non-scope

No connection persistence/service/document, onboarding UI/read model, runtime or
application composition, lifecycle wiring, provider/model selection, environment
fallback, alternate/custom endpoints, Azure/Bedrock/data residency/mTLS, custom
proxies/headers/query, organization/project selection, additional providers,
package exports, generic settings, Phase 7 configuration changes, audit/memory/
policy/verification changes, legacy MARK migration or setup.py changes.
Phase 8.1/8.2/8.3 contracts and native backend remain unchanged.

No real network or native smoke is authorized or needed for deterministic boundary
verification. Independent host validation is complete; human seal review remains required before any seal. The enum-import clarification and candidate implementation work are complete.
