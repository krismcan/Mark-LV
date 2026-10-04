# Phase 6.20 approval-bound UIA runtime identity continuity review

## Checkpoint and scope

Protected branch: `nayeon-v1`. Protected HEAD remains
`382d44c3a944a0868c6af3350d4128e8799f8016`, tagged
`nayeon-v1-bounded-uia-runtime-identity-01` (annotated tag object
`fb8703055b245cc8067127adc767d8defa29881c`, peeling to protected HEAD).
The initial working tree matched the expected uncommitted candidate:
`nayeon/agent/pointer_binding.py` and `tests/test_pointer_uia_gate.py` modified.
The candidate was preserved and reviewed; no reset, checkout, discard, or rewrite
from scratch occurred.

Production scope remains exactly one file: `nayeon/agent/pointer_binding.py`.
The reviewed candidate already implemented the requested continuity gate. This
session changed only its new retention comment to satisfy an existing historical
source guard. It completed `tests/test_pointer_runtime_identity_continuity.py`
and this review. Existing candidate changes in `tests/test_pointer_uia_gate.py`
remain limited to intentional observation cardinality and source/scope expectations.
Historical effect harnesses already supplied deterministic `_UIAHarness` services;
no additional historical test files required edits.

## Approval and execution ordering

Preparation retains existing permission/policy evaluation, then:

1. Acquire the trusted target.
2. Validate the original proposed point against that target.
3. In effect mode only, perform exactly one scoped UIA observation of that exact
   point object. Require exact result/evidence types, valid bounded evidence,
   exact `VERIFIED` status, `enabled is True`, and unchanged services and registry
   metadata/implementation before and after observation.
4. Construct the frozen operation retaining only the observation's `runtime_id`
   tuple; include that tuple in the independent operation snapshot.
5. Create confirmation with `binding=operation`. The unchanged
   `ConfirmationService._bindings[token]` holds that exact operation object.

Effect consumption checks exact operation/component identity and snapshot,
consumes one-time confirmation with the exact operation binding, and reevaluates
policy. It then acquires a fresh target and performs fresh hit validation of the
original approved point. After successful eligibility:

1. Perform the second fresh scoped UIA observation at the original point.
2. Require exact valid `VERIFIED` evidence, `enabled is True`, and intact binding.
3. Reject locally when `evidence.runtime_id != operation.runtime_id`.
4. Discard the descriptive observation and evidence.
5. Normalize coordinates, then run the existing insertion block unchanged.

The normalization-through-insertion text is identical to protected HEAD. Coordinate
normalization remains the final native desktop read before insertion; only local
validation/construction follows it. Existing post-effect observation, verification,
and audit behavior remains unchanged.

The three-argument historical `_PointerOperation(target, action, point)` still
defaults `runtime_id` to `None`. Non-effect preparation stores `None` and performs
no UIA observation. Effect-mode operation binding requires a non-None valid tuple;
non-effect binding requires `None`. Read-only `approve` internally consumes with
`effect=False`, even for an effect-mode prepared operation: it retains historical
fresh target/hit eligibility semantics and performs no second UIA observation,
normalization, or insertion.

## Meaning and retention

Runtime ID is opaque, short-lived continuity evidence. Exact local tuple equality
allows distinct tuple objects containing the same values and rejects differing
values. The sealed Phase 6.19 validator provides exact tuple/int and length/range
validation. There is no native element comparison, SAFEARRAY reconstruction,
parsing, hashing, semantic lookup, logging, persistence, or added public route.

`enabled=True` is a safety prerequisite before confirmation and before effect
only. It does not prove clickability or authorize semantic behavior. Reviewed
control types are neither stored nor compared; different valid pre/post control
types with the same runtime tuple permit the existing effect path.

Only the tuple is retained in the private operation and its snapshot during the
invocation. Result/evidence objects are not retained. Closing clears operation,
snapshot, confirmation, and service references and removes confirmation bindings.
Audit messages, standard `VerificationResult` evidence, and the status-only
post-effect observation contain no runtime tuple. A caller-held operation remains
a private frozen, redacted, nonserializable object under the existing contract;
closing does not mutate that caller-held object.

Continuity is not semantic or durable identity. Runtime IDs may be reused, and
matching samples cannot establish stable identity between or after samples.
The existing observation-to-effect race remains; scoped/native calls have no hard
deadline. No claim of UI/task success or live desktop safety follows from fake-only
tests.

## Validation

Authoritative interpreter:
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`, Python 3.12.10.
The first Codex session could not initially resolve the installed interpreter and,
before it was stopped under the five-minute no-progress rule, downloaded the official
Python 3.12.10 embedded archive into a temporary %TEMP%\nayeon-phase620-python31210
directory and used that temporary interpreter for intermediate test runs. The human
orchestrator deleted that entire temporary directory before the resumed session.
Nothing was installed into the system or repository, and no downloaded artifact was
retained. The resumed session and all final/authoritative validation used the exact
installed interpreter above; the resumed session performed no network download.

Final commands use that executable as `PYTHON` below:

```text
PYTHON -m unittest tests.test_pointer_runtime_identity_continuity -q
PYTHON -m unittest tests.test_pointer_runtime_identity_continuity tests.test_pointer_uia_gate tests.test_pointer_binding tests.test_pointer_effect tests.test_pointer_post_observation tests.test_pointer_verification tests.test_scoped_ui_element_observation tests.test_ui_element_observation tests.test_pointer_coordinates tests.test_pointer_coordinate_contract tests.test_pointer_hit_validation tests.test_target_validation tests.test_dpi_execution_context tests.test_verification tests.test_executor tests.test_structured_executor tests.test_policy_confirmation -q
PYTHON -m unittest discover -q
PYTHON -m compileall -q nayeon tests
git diff --check
```

Final outcomes: focused **15 tests passed**; affected **387 tests passed**;
full discovery **1,507 tests passed**, with no failures, errors, or skips reported.
Compilation and tracked/untracked whitespace checks passed. Static forbidden
scans and protected scope/byte guards passed. Earlier validation exposed only test
guard issues (a comment triggering a historical guard, mixed checkout line endings,
and an annotated tag needing commit peeling); all were corrected before final runs.

The new module checks ordering, exact observation cardinality, original-point
identity, invalid/subclass/malformed/disabled/exception evidence, service and
registration mutation, exact confirmation binding, snapshot/frozen-bypass
tampering, legacy/read-only behavior, equal distinct tuples, mismatch rejection,
control-type independence, cleanup/redaction, source ordering, and production scope.
All observation and effect seams use deterministic injected fakes; native factory
guards prevent fallback to live desktop facilities in the new runtime tests.

Executor, confirmation, scoped/UIA observation services, effect, and coordinate
files match protected Git content and unchanged raw checkout SHA-256 seals. The
checkout has mixed LF/CRLF in some protected files; raw seals explicitly preserve
that existing representation independently of Git's normalized content. Only
`pointer_binding.py` differs under `nayeon/`, with no untracked production files.

No live effect or native mutation smoke was performed. No commit, tag, push, or
workbook update was made. HEAD and protected tag remain unchanged. Final working
tree intentionally contains two modified tracked files and the two new untracked
test/review files, awaiting human review.
