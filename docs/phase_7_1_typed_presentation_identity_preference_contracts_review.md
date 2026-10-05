# Phase 7.1 typed presentation identity and preference contracts review

## Protected starting checkpoint

- Repository: `C:\AI\Mark-LII`; branch: `nayeon-v1`.
- Commit: `59d6b341ffe67b86e7f0555e50be074ecfd31f4a`.
- Tag: `nayeon-v1-bounded-computer-control-v1-closure-01`.
- Protected Phase 6.23 regression baseline: **1,533/1,533**, independently
  recorded for that checkpoint; this is historical evidence, not a Phase 7.1 result.
- Branch, HEAD, tag and clean starting working tree matched exactly.

## Presentation boundary

Presentation identity names an assistant for display/conversation and potential
future wake-name presentation/behaviour. It does not identify a trusted actor,
action, capability, process, window, pointer target, file or application. The
explicit name `AssistantPresentationIdentity` preserves that distinction.

The new module imports only `dataclass` from standard-library `dataclasses` and
future annotations. It has three dataclasses and two private, pure validation
helpers. No existing production module references it. Capability registry names,
permission/policy decisions, confirmation binding, audit action identity,
execution authority, object identity and secrets/provider credentials are
unchanged. Permission -> Policy -> Confirmation -> Execution remains untouched.

## Exact contracts

| Contract | Fields in declaration order | Defaults |
| --- | --- | --- |
| `AssistantPresentationIdentity` | `display_name: str`, `wake_name: str` | `"Nayeon"`, `"Nayeon"` |
| `UserPresentationProfile` | `display_name: str \| None` | `None` |
| `PresentationPreferences` | `personality_ref: str \| None`, `voice_ref: str \| None` | `None`, `None` |

All three use `@dataclass(frozen=True, slots=True, repr=False)`. They have explicit
annotations, no mutable fields, no instance `__dict__`, and ordinary immutable
dataclass equality/hash semantics. Their inherited object repr contains no field
serialization or configured values. No custom repr or serialization is provided.
There is no aggregate/document/schema or package-level export; that is deferred
to Phase 7.2.

## Validation and privacy

Validation occurs deterministically in `__post_init__`. Required names accept
only exact built-in `str`, with 1..64 Unicode code points. The optional user name
accepts `None` or the same name validation. Preference references accept `None`
or exact built-in `str` with 1..128 Unicode code points.

Every string must equal its own `strip()` and must exclude characters whose
ordinal is below 32 or exactly 127. Empty values, surrounding whitespace and
ASCII controls are rejected. Internal spaces and otherwise valid Unicode are
preserved exactly, including case and decomposed Unicode. No coercion, case
folding, normalization or provider semantics parsing occurs. Wrong types,
including `str` subclasses, raise `TypeError`; invalid content/length raises
`ValueError`. Error messages contain no rejected value.

## Legacy and excluded ownership

The NEW user contract has no hard-coded personal default: `display_name=None`.
This removes the personal default from the new contract design only. Legacy
`nayeon/config/config.py`, including its existing `user_name="Kris"`, remains
content-identical to the protected checkpoint. `NayeonConfig`/`ConfigService`
are intentionally untouched and unwired; the new module does not import, wrap,
deprecate or migrate them. `nayeon/config/__init__.py` is also unchanged.

`wake_word_enabled`, proactive and morning-briefing switches are behavioural
controls and belong outside this presentation-only contract phase. Permission
defaults govern authority and also belong outside it. No arbitrary settings
dictionary is carried forward.

There is no persistence, runtime wiring, migration, I/O, environment access,
lock, network access, secret, provider credential, permission change, UI, Voice
or Proactive behaviour. Voice/personality values are opaque references only.
No live/native smoke is required because nothing is wired into runtime and no
effectful service is changed.

## Tests prepared

`tests/test_presentation_identity_contracts.py` adds **14 test methods**, using
subtests across every string field and validation category:

- Exact field order, annotations/defaults; frozen/slotted/no-dict shape;
  equality/hashability, mutation/deletion rejection, and independent replacement.
- ASCII/Unicode/internal spaces, exact preservation, code-point length boundaries,
  optional `None` and required-name rejection of `None`.
- Every field rejects int/bool/float/bytes/object/str-subclass and an object whose
  string conversion would fail, with `TypeError` and no coercion.
- Every field rejects empty/whitespace-only/surrounding-whitespace/overlong values
  and every ordinal 0..31 plus DEL, with `ValueError` and value-free messages.
- Configured display/wake/personality/voice values absent from inherited object
  repr; no field serialization or custom repr.
- AST guards for imports, exact classes/decorators/methods, pure-call allowlist,
  no mutable collections/Any, and no authority-related methods or I/O APIs.
- No production references/imports to the presentation contracts; exact protected
  HEAD/branch/tag and sole added production path; per-file checkpoint content
  comparison, including legacy config/package API, allowing checkout CRLF/LF only.

## Validation results

Codex GPT-6.1 Sol / Medium prepared the bounded contract module, dedicated tests
and initial review. Its workspace sandbox could not access the authorized host
interpreter, so no alternate runtime was downloaded, installed or copied and no
network workaround was used.

Authoritative validation was then performed independently on the Windows host with
`C:\\Users\\krist\\AppData\\Local\\Python\\pythoncore-3.12-64\\python.exe`
(Python 3.12.10).

Host validation exposed historical Phase 6 source-guard assumptions rather than
production failures. Four Phase 6 test files were maintained so their guards continue
to protect the frozen Computer Control authority surfaces while allowing unrelated
future subsystems and HEAD advancement:

- `tests/test_computer_control_v1_freeze.py`: now freezes the explicit Computer
  Control files/authority graph and historical tags instead of all future `nayeon/`
  production forever;
- `tests/test_pointer_clickability_execution_gate.py`: untracked-file guard narrowed
  to protected action surfaces;
- `tests/test_pointer_runtime_identity_continuity.py`: historical milestone tags are
  pinned without requiring current HEAD to remain Phase 6.22; untracked guard narrowed
  to protected action surfaces;
- `tests/test_pointer_uia_gate.py`: untracked-file guard narrowed to agent/services
  pointer implementation surfaces.

These are test-only maintenance changes. No pre-existing production file changed.

Seal-time validation after staging exposed the staged-file form of the same historical
assumption in three pointer guards: their `git diff` pathspecs still covered all of
`nayeon/`. Those pathspecs were narrowed to the protected agent/services authority
surfaces, then the tests were restaged and rerun. This does not weaken Computer Control
protection; the Phase 6.23 freeze guard separately protects the explicit capability and
pointer authority graph.

Final authoritative results:

- dedicated Phase 7.1 contract suite: **14/14 passed**;
- combined Phase 6 freeze + Phase 7.1 contracts after initial guard maintenance:
  **22/22 passed**;
- focused presentation + maintained Phase 6 pointer guards: **63/63 passed**;
- affected config/core/trust-boundary suite: **187/187 passed**;
- full unittest discovery: **1,547/1,547 passed**;
- seal-time staged candidate: **63/63 focused** and **1,547/1,547 full passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Final scope/integrity evidence:

- `nayeon/config/presentation.py` is the **only** production addition/change;
- all **82 pre-existing tracked production files** from the Phase 6.23 checkpoint
  remain content-identical (checkout CRLF/LF normalization only);
- legacy `nayeon/config/config.py` and `nayeon/config/__init__.py` remain unchanged;
- no existing production module imports or references the new contracts;
- the new module imports only future annotations and standard-library `dataclass`;
- no registry/policy/permission/confirmation/audit/executor/capability/service/secret
  dependency is introduced;
- no persistence, environment, network, filesystem or lock API is present;
- the Phase 6 Computer Control frozen trust surface remains guarded while unrelated
  future subsystem files are permitted.

No live/native smoke was required or performed because the contracts are not wired
into runtime and have no side effect.

## Handoff

The candidate contains one new production contract module, its dedicated test/review,
and four historical Phase 6 guard-maintenance edits described above. The protected
Phase 6.23 HEAD/tag remains unchanged during candidate validation and all pre-existing
production files are unchanged. Nothing is staged. No commit, tag, push or workbook
update was made. Independent host validation is complete; the candidate is ready for
human seal review.
