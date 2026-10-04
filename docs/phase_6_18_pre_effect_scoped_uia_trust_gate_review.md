# Phase 6.18 - Pre-effect scoped UIA trust gate review

This uncommitted candidate started on `nayeon-v1` at
`18e69f8eb2590a68aa0651f264aec123b9b316a1`, with
`nayeon-v1-scoped-dpi-aware-mta-uia-observation-01` at HEAD and a clean tree.
There was no protected-checkpoint discrepancy. HEAD and tag remain unchanged.

## Scope and wiring

Production edits are confined to `nayeon/agent/executor.py` and
`nayeon/agent/pointer_binding.py`. The private executor injection seam and
invocation constructor require exact `_PointerEffectService`,
`_PointerCoordinateService`, and `_ScopedUIElementObservationService` instances
in effect mode. Neither coordinate mapping nor scoped UIA may be supplied in
read-only mode. No service is silently constructed for fake-effect tests.
The UIA service object participates in the existing identity seal, binding
rechecks, and invocation cleanup. Read-only `approve()` never observes UIA,
including when invoked on an effect-mode invocation.

Test changes are limited to deterministic service injection in the existing
effect helpers (`tests/test_pointer_binding.py`, `tests/test_pointer_effect.py`),
the historical pointer-binding file seal exception in
`tests/test_scoped_ui_element_observation.py`, and the new focused
`tests/test_pointer_uia_gate.py`. The old seal continues to cover its service
files; the new tests guard the approved pointer integration explicitly.
This document is the seventh changed/added file.

No sealed service, policy, confirmation, audit, undo, capability, intent,
runtime, verification framework, or public execution route is modified.
The new seal test compares all eight relevant service files with protected HEAD
bytes (allowing only the pre-existing Windows LF/CRLF checkout representation)
and requires an empty Git diff for each. These files were never written.

## Exact effect ordering

After exact confirmation approval and policy recheck:

1. Existing exact operation, target, action, point, service, and registration
   binding checks.
2. Existing fresh target acquisition and fresh hit eligibility at the original
   approved point, followed by the existing binding recheck.
3. Exactly one sealed Phase 6.17 `observe(operation.point)` call using the
   identical original approved `_ProposedPoint` object.
4. Local exact result/evidence checks, class-owned `__post_init__` validation,
   VERIFIED status, identical point, exact enabled `True`, and operation/binding/
   service/registration recheck. Awareness remains exact integer `2` through the
   sealed evidence invariant. Successful UIA references are discarded locally.
5. Existing `coordinate_service.normalize(operation.point)` on the original point.
6. Existing local coordinate-result, evidence, and binding validation, conservative
   receipt construction, and local INPUT construction inside the sealed effect service.
7. Existing single `_PointerEffectService._insert` / three-record SendInput batch.
8. Existing post-effect original-target observation, captured-evidence verification,
   audits, and authority cleanup.

UIA must precede coordinate normalization because Phase 6.17 performs native DPI
and UIA work. Placing it after normalization would invalidate normalization's
position as the final native desktop/state sample before insertion. The successful
UIA-to-coordinate gap contains only local validation/binding checks and local
reference disposal. There is no audit, file I/O, model call, sleep, retry, or native
read in that gap. The coordinate-to-insert path is unchanged from protected HEAD;
only local validation/construction follows the last sample. No second UIA call
occurs after normalization. Failure audits/cleanup happen on paths that cannot
continue to normalization/insertion, or after the existing effect seam returns.

## Rejection and evidence semantics

Missing, fake, or subclassed UIA service instances are rejected at construction.
Replacement with another exact instance invalidates the invocation seal. Wrong
result types, result subclasses, uninitialized/tampered results or evidence,
INDETERMINATE, wrong point identity, invalid awareness/control type/enabled values,
disabled evidence, observation exceptions, or changed operation/binding/registry/
service state return the existing NOT_ATTEMPTED receipt. They do not normalize
coordinates or insert input. Existing pre-gate policy/eligibility failures also
remain NOT_ATTEMPTED and never call UIA.

Enabled `True` is a one-way safety prerequisite only. It establishes neither
clickability nor actionability, semantic intent, intended element identity, or
task success. Every one of the sealed 41 reviewed control-type IDs is accepted
equivalently when all other prerequisites hold. Pointer binding never reads or
branches on `control_type`; its validity is enforced only by the sealed contract.

UIA evidence is local descriptive data, never reusable authority. It is not
stored on the invocation, supplied to `_PointerVerificationProvider`, retained
as post-effect evidence, exported in public `VerificationResult.evidence`, added
to audit details, or stored in memory. Existing verification claims remain
unchanged: bounded insertion and original-target sample equality leave the UI/task
result unverified. Post-observation and verification-provider code is unchanged.

## Validation actually run

All commands use the repository `.venv` **Python 3.12.10**. The initial sandbox
launch could not access the environment's base interpreter; sandbox escalation
allowed the same repository interpreter to run. No alternate Python, dependency
installation, native UIA, or live SendInput was used.

Final runs (counts are unittest methods; subtests cover additional cases):

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_pointer_uia_gate -v
```

**15/15 passed, no skips.** Covers exact fresh-target/hit/UIA/normalize/insert
ordering, final metrics sample, cardinality and point identity, read-only approval,
failure suppression, all 41 control types, malformed types/invariants, mutation
during observation and local validation, service replacement before UIA and after
normalization, constructor/executor requirements, evidence non-retention, existing
policy/eligibility gates, unchanged final insertion gap and post-effect provider,
no new executor route, and sealed service bytes.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_pointer_uia_gate tests.test_pointer_binding tests.test_pointer_coordinates tests.test_pointer_coordinate_contract tests.test_pointer_effect tests.test_pointer_hit_validation tests.test_pointer_observation tests.test_pointer_post_observation tests.test_pointer_verification tests.test_target_validation tests.test_ui_element_observation tests.test_dpi_execution_context tests.test_scoped_ui_element_observation tests.test_verification tests.test_executor tests.test_structured_executor -q
```

**395/395 passed, no skips.** Existing insertion, partial/indeterminate receipt,
post-observation, verification, audit-failure, and cleanup semantics pass with
the mandatory deterministic scoped UIA service injected.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q nayeon
git diff --check
git diff --no-index --check -- nul tests/test_pointer_uia_gate.py
git diff --no-index --check -- nul docs/phase_6_18_pre_effect_scoped_uia_trust_gate_review.md
```

**1477/1477 regression tests passed, no skips.** Compilation and tracked/untracked
whitespace checks passed. No live effect smoke was performed.

Earlier diagnostic runs found a historical raw `UIA` substring guard triggered
by new error-message wording (resolved using scoped-element wording), an incorrect
new test native-facade name, and a test byte comparison that incorrectly assumed
all checkout files used CRLF. Those local issues were corrected; no sealed service
change was needed. An intermediate affected run passed 392 tests before the final
three focused guards were added; final counts above cover the complete candidate.

## Controlled live-effect smoke

Human authorization was obtained separately for one bounded live Phase 6.18
smoke against a disposable blank Tk window. The temporary target was outside the
repository and was destroyed after the attempt.

A read-only preflight at the inert client-centre point (558, 381) showed that
the real Phase 6.17 scoped UIA path was healthy: UIA returned VERIFIED,
enabled=True, reviewed control type 50033, and retained the same exact point
object. The independent foreground/hit check returned NOT_VERIFIED, so no
effect was attempted during that preflight.

For the single authorized live attempt, the external smoke harness located the
same disposable target and derived the same client-centre point. It made one
setup-only SetForegroundWindow request before entering Nayeon's production
pointer path; Windows returned False. The unchanged production Phase 6.18 chain
then failed closed in prepare() with "Pointer binding preparation failed."
The effect seam was never reached: there was no effect audit outcome, pending
confirmations were 0, undo records were 0, and no SendInput, pointer move,
or click occurred.

No trust check was weakened, no alternate focus/click route was used, and no
second live attempt was made. This smoke therefore proves the integrated path
continues to fail closed when foreground trust is unavailable, but it does not
yet provide a successful live end-to-end UIA-gated insertion proof.
## Residual risks and handoff

Checks remain sequential point-in-time samples. UI state can change after UIA,
after target/hit validation, or between coordinate normalization and SendInput;
mutation away and back between checks is not excluded. The gate neither eliminates
TOCTOU nor provides semantic target assurance. Coordinate normalization remains
the final native desktop/state read, preserving the approved narrow timing property.

The sealed synchronous UIA provider has no hard deadline and can block the caller.
Provider failures, unavailable elements, disabled samples, cleanup/restoration
failures, or delays consuming the original-binding age window can conservatively
prevent an otherwise possible effect. No retries, polling, timeout mechanism,
worker pool, coordinate repair, or authority caching is introduced.

Handoff contains five modified tracked files and two new untracked files, with
no staged changes. No commit, tag, push, workbook update, or live effect smoke was
performed. The candidate is ready for review at unchanged protected HEAD.
