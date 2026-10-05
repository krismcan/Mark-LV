# Phase 7.2 strict versioned presentation configuration document review

## Candidate and protected baseline

- Branch: `nayeon-v1`.
- Starting and current HEAD: `ae1a1ca290b389d9f300c6f8e9f6c076f09ef2af`.
- Sealed Phase 7.1 tag: `nayeon-v1-presentation-identity-contracts-01`, resolving
  to `0527a0201fad1bd284d03292a43d6b3365c16af3`.
- Historical full regression baseline: **1,547/1,547** from the completed Phase
  7.1 handoff. This is not a Phase 7.2 test result.
- Initial working tree contained only the expected untracked production candidate
  `nayeon/config/document.py`. Git and `.codex/CURRENT_STATE.md` agree about the
  latest completed product phase and next restart point.

## Approved implementation

`nayeon/config/document.py` is the only production addition/change. Its imports
are future annotations, standard-library `dataclass`/`field`, and the three
sealed Phase 7.1 presentation contracts. It adds:

- `PRESENTATION_CONFIGURATION_SCHEMA_VERSION = 1`;
- `PresentationConfigurationDocumentV1`, with `frozen=True`, `slots=True`, and
  `repr=False`;
- `parse_presentation_configuration_document(data)`;
- `presentation_configuration_document_to_mapping(document)`;
- one private exact-mapping validation helper.

The document fields in order are `schema_version`, `assistant`, `user`, and
`preferences`. Schema version defaults to the constant. Composed values use
independent default factories and must be exact instances of the respective
Phase 7.1 contracts. Equality/hash semantics are ordinary immutable dataclass
semantics; inherited object repr does not serialize configured values.

The canonical mapping has exactly these keys and nested keys:

| Section | Exact keys |
| --- | --- |
| Root | `schema_version`, `assistant`, `user`, `preferences` |
| `assistant` | `display_name`, `wake_name` |
| `user` | `display_name` |
| `preferences` | `personality_ref`, `voice_ref` |

Parsing accepts only exact built-in dictionaries with exact built-in string
keys. Missing/unknown keys fail, including replacement keys at unchanged mapping
length. Dictionary subclasses, general mappings, string subclasses and integer
subclasses fail. Schema version must be exact built-in `int` equal to 1; booleans,
floats and strings are not coerced. Wrong types raise `TypeError`; invalid shape,
unsupported version and invalid string content raise `ValueError`. No error
includes a rejected value or unknown key name. No coercion, normalization, default
insertion for missing keys, provider interpretation or migration occurs.

String validation is delegated to unchanged Phase 7.1 contracts: required
assistant names, optional user name and opaque preference references retain their
exact length, whitespace, control-character and Unicode rules. Defaults remain
`Nayeon` for both assistant names and `None` for user/personality/voice values.

Parsing neither mutates nor retains mutable input mappings. Encoding requires
an exact document instance and returns a fresh root dictionary and fresh nested
dictionaries in canonical field order on every call. Valid immutable strings
are preserved exactly; round trips preserve document value semantics.

## Scope and security separation

There is no JSON, file I/O, persistence, runtime wiring, environment access,
network access, migration, generic settings object, secret handling, permission
default, Voice listening toggle or Proactive/event behavior. Presentation names
and opaque references do not affect capability identity, policy, permissions,
confirmation, audit identity, trusted object identity or execution authority.
Permission -> Policy -> Confirmation -> Execution -> Verification remains intact.

Legacy `ConfigService`, `nayeon/config/config.py`, `nayeon/config/__init__.py` and
`nayeon/config/presentation.py` are unchanged. No package-level exports were added.
No existing production consumer imports the document. No Phase 6 test or
Computer Control implementation changed; all frozen authority surfaces remain
protected by their existing guards.

## Narrow historical test maintenance

Only `tests/test_presentation_identity_contracts.py` was maintained. Its historical
Phase 6 candidate HEAD/content expectations conflicted with the already sealed
Phase 7.1 implementation and the approved document consumer. The guard now pins
the sealed Phase 7.1 tag/content baseline and this candidate's exact starting
HEAD. Its production delta and source inventory permit exactly `document.py`.
The presentation-consumer exclusion permits only `presentation.py` itself and
that exact document path. Every pre-existing production file, including the
three protected configuration files, is compared against sealed content, allowing
only checkout CRLF/LF conversion. Arbitrary future production additions or
consumers remain rejected. Existing presentation validation/identity guards
remain intact. This maintenance is entirely test-only.

## Tests and validation evidence

`tests/test_presentation_configuration_document.py` contains **16 test methods**
with subtests covering document shape/defaults, immutability and value semantics,
exact composed types, version rejection, every mapping/key/leaf validation level,
privacy and hostile conversion objects, inherited string boundaries, Unicode
preservation, mutation isolation, canonical ordering, fresh mappings, round trips,
encoder input rejection, non-disclosing repr and pure dependency/call boundaries.
A production scan rejects all other consumers of the new document API.

Codex GPT-6.1 Sol / Medium prepared the bounded production/test/review candidate.
Its workspace sandbox could not invoke the authorized host interpreter, and it did
not download/install/copy Python or packages and did not use a network workaround.

Authoritative independent Windows-host validation then used:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`.

Final host results:

- dedicated Phase 7.2 suite: **16/16 passed**;
- affected Phase 7/config/core/trust-boundary suite: **162/162 passed**;
- full unittest discovery: **1,563/1,563 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Final integrity/scope evidence:

- all **83** pre-existing tracked production files under `nayeon/` match the
  starting housekeeping checkpoint `ae1a1ca290b389d9f300c6f8e9f6c076f09ef2af`;
- production delta is exactly the new untracked `nayeon/config/document.py`;
- no other production module imports or references the new document API;
- `nayeon/config/presentation.py`, legacy `nayeon/config/config.py`, and
  `nayeon/config/__init__.py` remain unchanged;
- `AGENTS.md`, `.codex/CURRENT_STATE.md`, and `scripts/update_codex_context.py`
  remain unchanged during implementation;
- only `tests/test_presentation_identity_contracts.py` received narrow historical
  guard maintenance, permitting exactly `document.py` as the approved consumer and
  Phase 7.2 production addition;
- Phase 6 Computer Control tests/production were untouched;
- no staging, commit, tag, push, workbook update, or Codex current-state refresh
  has occurred for Phase 7.2.

No live/native smoke is justified: the codec is pure, performs no I/O, and is not
wired into runtime. The candidate is independently validated and ready for human
seal review.
