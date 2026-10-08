# Phase 8.7 — Metadata-only Connection Readiness & Explicit Startup

## Protected baseline and implementation approval

Date: 8 October 2026. Repository `C:\AI\mark-lii`, branch `nayeon-v1`.
Protected starting HEAD: `a2f27f40610aa29738e95f029c162707c0b261e8`.
Latest sealed PRODUCT milestone: Phase 8.6, annotated tag
`nayeon-v1-trusted-provider-connection-composition-bootstrap-01`,
peeled to `059b55efe945a561940f3d7bd9aa7b7d3fc6a971`.
Starting authoritative full regression baseline: **1,850 / 1,850**.
Pre-change branch/HEAD/worktree were inspected and verified clean.

User explicitly approved only a bounded implementation, new deterministic tests,
and strictly necessary narrow historical test-guard reconciliation.
**No staging, commit, tag, push, workbook update or Codex context refresh is
authorized.** This document is the unsealed human review artifact.

## Approved production delta — exactly two new modules

- `nayeon/brain/connection_readiness.py` (NEW)
- `nayeon/brain/connection_startup.py` (NEW)

There are no edits to sealed production, requirements, package exports,
legacy MARK, existing provider-connection ownership/codec/store/composition,
secret contracts, resolver, credential lifecycle/native backend, AI provider,
presentation configuration, policy or action execution.

### Metadata-only readiness

`assess_provider_connection_readiness(owner: ProviderConnectionService)`
requires an exact typed, initialized connection owner. It reads its cached
document only, enforces exact `ProviderConnectionDocumentV1` and
`ProviderConnectionConfiguration` types, and returns a fresh frozen,
slots-only, repr-suppressed `ProviderConnectionReadiness` containing only one
`ProviderConnectionReadinessStatus` enum.

The only statuses are:

- `UNCONFIGURED` — no selected connection metadata.
- `UNSUPPORTED` — selected provider is not exactly `openai` or credential
  identifier is not the exact `SecretIdentifier("openai.api_key")`.
- `READY_FOR_COMPOSITION` — metadata is eligible for the *existing* trusted
  Phase 8.6 composition gate; **no credential presence, validity, model
  availability or service usability is asserted**.

Invalid owner/service/document/configuration types or an uninitialized owner
fail closed with fixed, non-secret exceptions. No result retains the model,
provider string, identifier, source document, owner, backend, or error payload.
The status cannot authorize any action by itself and may be stale if the owner
is later changed; an executor must independently use current trust checks.

### Explicit, metadata-only startup

`startup_provider_connection(path: Path) -> ProviderConnectionStartupResult`
calls the sealed Phase 8.6 `bootstrap_provider_connection(path)` exactly once,
then assesses that initialized owner exactly once, returning a fresh,
frozen, slots-only, repr-suppressed result with the exact owner and exact
readiness value. Its sole path input is explicitly supplied by the trusted
caller; the sealed store independently requires the exact native Path class.

Missing metadata loads as an unconfigured in-memory owner without persisting
or creating directories. Invalid files propagate the sealed persistence error
without repair/fallback. Startup never creates a secret backend, resolves or
validates a key, constructs an OpenAI provider or client, or triggers an AI
request. This seam is **not** connected to any runtime, session, UI or agent.

The startup result contains a mutable process-local owner: its readiness
snapshot must be freshly reassessed after any owner mutation. It is not
appropriate as a long-lived authorization token or evidence of provider health.

## Tests and historical regression guards

Two new suites:

- `tests/test_provider_connection_readiness.py` (NEW)
- `tests/test_provider_connection_startup.py` (NEW)

They cover missing/valid/mismatched metadata, unsupported providers, exact
service and result types, uninitialized and forged inputs, safe errors,
immutability/non-disclosure, fresh independent startups, deterministic ordering,
failure propagation, absent and malformed files, no eager credential/backend/
SDK/native activity, import authority limits, and an exact **100-file Phase 8.6
production freeze** against the sealed product tag and `requirements.txt`.

Historical production-delta and consumer guard updates are constrained to
**11 existing test files**:

- `tests/test_bound_credential_lifecycle.py`
- `tests/test_openai_canonical_client.py`
- `tests/test_openai_provider_secure_secret.py`
- `tests/test_presentation_configuration_bootstrap.py`
- `tests/test_presentation_configuration_persistence.py`
- `tests/test_presentation_configuration_service.py`
- `tests/test_presentation_configuration_view.py`
- `tests/test_presentation_identity_contracts.py`
- `tests/test_provider_connection_service.py`
- `tests/test_provider_connection_composition.py`
- `tests/test_windows_credential_backend.py`

The exact production delta checks retain their frozen older source bodies and
permit only the two new Phase 8.7 modules in addition to previously approved
Phase 8.5/8.6 additions. Import consumer sets expand **only** for the new
metadata readiness and startup modules. The secret-contract import guard
allows readiness to import `SecretIdentifier` only, not `SecretBackend` or
native credential authority. Presentation/document legacy freezes stay intact.

## Engineering workflow and verification evidence

The Codex CLI 0.162.0 text-only `gpt-6.1-sol` High draft did not complete
within the established five-minute progress threshold and was stopped.
No Codex draft or repository changes resulted from that failed attempt.
Implementation was then authored directly as the exact reviewed four-file
production/test delta through Desktop Commander and validated using the
authoritative Windows host Python. No extra IDE/SDK/plugin or dependency was
installed. No real credential values or native credential operations were read.

Authoritative interpreter:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`

- New Phase 8.7 focused tests: **30 / 30 PASS**.
- Combined Phase 7–8.7 affected connection, presentation and secret-contract tests: **347 / 347 PASS**.
- Full repository regression after narrow guard reconciliation: **1,880 / 1,880 PASS**.
- Python `compileall -q nayeon tests`: **PASS**.
- `git diff --check`: **PASS**.
- Independent exact 16-path scope, Git staging, 100 old-production-file/requirements byte freeze, and new-module metadata-only import/call audit: **PASS**.

## Non-scope and residual risks

No BYOK onboarding UI, credential save/delete/validation, model availability
probe, network request, default location, environment-based path selection,
runtime startup wiring, provider auto-activation, provider/client factory,
model-selectable readiness tool, registry, live smoke or external user action.

No cross-process or concurrency-safe startup guarantee is claimed. The underlying
metadata owner explicitly requires serialized operations. A persisted valid
credential *identifier* does not establish storage availability or provider
authorization. A readiness result could become stale after a later mutation;
it is observation only, never policy authorization or substitute for Phase 8.6
composition's exact checks.

## Human seal gate

The candidate must remain unstaged and uncommitted. It cannot be tagged,
pushed, documented to the master workbook or reflected in the Codex handoff
without subsequent explicit authorization. Full regression and scoped-source
evidence must pass before presentation for seal approval.
