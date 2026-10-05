# Phase 6.23 bounded Computer Control v1 closure review

## Protected checkpoint and scope

- Repository: `C:\AI\Mark-LII`; branch: `nayeon-v1`.
- Protected Phase 6.22 commit: `797ed334f4256d2e05de6605d7ceb9f4bd96a57e`.
- Tag: `nayeon-v1-fresh-uia-clickability-execution-gate-01`.
- Protected full regression baseline: **1,525/1,525**, independently recorded
  for Phase 6.22. This is historical evidence, not a Phase 6.23 test result.
- Starting branch, HEAD, tag and clean working tree matched exactly.

This phase closes and freezes the existing trusted bounded foundation. It adds
tests and this review only, with no runtime behavior or production change. All
82 tracked files under `nayeon/` match the protected Git content hashes, and
there are no untracked production files reported by Git. No closure violation
was found by source inspection; runtime validation remains pending.

## Public Computer Control v1 surface

| Capability | Implementation | Contract |
| --- | --- | --- |
| `observe_foreground_window` | `ObserveForegroundWindowCapability` | One bounded foreground observation |
| `observe_pointer` | `ObservePointerCapability` | One bounded pointer observation |
| `focus_window` | `FocusWindowCapability` | Focus bound to the window identity prepared before human confirmation |
| `type_text` | `TypeTextCapability` | Bounded plain keyboard text into the exact approved foreground window |

These classes live in the corresponding modules under `nayeon/capabilities/`.
Observation is read-only. Focus and text require confirmation. These are the
Computer Control surface, not the complete product capability inventory;
application and filesystem capabilities remain outside this table.

## Trusted private pointer primitive

`ActionExecutor._pointer_invocation` is a private context manager with **zero
production references/callers outside its definition**. It constructs the private
`_PointerInvocation` locally, yields it lexically, and closes it in `finally`.
It does not save invocation authority on the executor. Pointer binding exports
nothing (`__all__ = ()`). No public wrapper or capability route reaches it.

Only `nayeon/agent/executor.py` and `nayeon/agent/pointer_binding.py` import
`nayeon.services.pointer_effect`. Only pointer binding calls the effect service's
`_insert`. Raw pointer SendInput binding and use remain confined to
`nayeon/services/pointer_effect.py`. Capability modules import neither pointer
binding, pointer effect, coordinate normalization, nor scoped UIA pointer internals.

Within the private primitive, the exact human-approved point remains the sole
execution coordinate. `_PointerOperation` contains exactly `target`, `action`,
`point`, and `runtime_id`. Clickability is fresh execution evidence only, never
operation or confirmation state. Provider GetClickablePoint coordinates are
discarded by the observation layer and absent from pointer binding; they cannot
replace, reconstruct or redirect the approved point.

The existing trust order remains: exact one-time approval, policy reevaluation,
operation/service/registration continuity, fresh target identity/context equality,
fresh hit validation, fresh scoped UIA evidence at the approved point, exact
evidence/type/point checks, enabled True, exact runtime tuple continuity, fresh
clickable True, discard the descriptive sample, normalize `operation.point`,
and bounded insertion. The normalization-through-insertion block and its helper
paths remain checkpoint-identical. Coordinate normalization remains the final
native desktop read before insertion; this phase adds no native/API call in that gap.

Permission -> Policy -> Confirmation -> Execution, audit, and verification
boundaries remain intact. Model interpretation supplies neither authorization
nor success evidence. The private pointer effect is non-reversible; no undo is
promised. Bounded insertion and post-effect identity observations do not prove
semantic UI/task completion.

Keyboard SendInput in `nayeon/services/windows_keyboard.py` is a separate,
already-protected Unicode text path, not a pointer bypass. Its mouse structure
exists for INPUT union ABI layout; emitted events have `INPUT_KEYBOARD` type 1.
The freeze explicitly permits this independent path and pins its source.

## Deliberately deferred surface and residual limits

There is no public generic click capability or arbitrary caller/model-supplied
pixel click authority. A raw coordinate cannot establish what the user intends
to activate. The private bounded primitive therefore supplies no public click route.

Semantic UI target selection and visual target discovery require explicitly
designed future Vision/Perception evidence and trust integration. They must not
be introduced through the raw pointer layer. Also deferred are right click,
double click, drag/drop, scroll/wheel, autonomous GUI action sequences, and
semantic UI/task success claims. A future approved architecture phase may
intentionally revise the freeze guards with review and new evidence.

Residual limitations remain Windows TOCTOU between sequential samples and
insertion, provider false negatives, no exact-pixel clickability proof, no semantic
intent proof, and no UI/task success proof. A fresh provider-defined clickable
point's existence does not prove clickability at the exact approved point.
Further pointer/UIA checks cannot eliminate TOCTOU and could disturb the protected
final normalization/read-to-insertion order. Closure deliberately adds no further
pointer safety mechanism.

## Freeze coverage

`tests/test_computer_control_v1_freeze.py` contains eight deterministic tests:

1. Exact candidate HEAD/branch/tag, empty production diff, no untracked production
   files, and individual tracked-file content equality (checkout CRLF/LF allowed).
2. Every production capability Python module: AST identifiers, imports, reflective
   accesses and routing metadata exclude private pointer authority and deferred
   features, without treating comments or descriptive prose as executable authority.
3. Exactly one private context-manager definition on ActionExecutor, zero production
   invocation references, restricted private class users, no exports, unchanged executor.
4. Normal and exceptional lexical exit clear authority and retain no invocation on
   the executor, using existing deterministic fake target/hit services.
5. Exact reviewed importers, insertion and native pointer boundary; separate
   keyboard allowance, protected keyboard source and keyboard-only emitted type.
6. Unchanged pointer binding, exact operation fields, execution-only clickability,
   approved-point normalization and no provider clickable-point API/coordinate path.
7. Exact final normalization/insertion block plus unchanged effect/coordinate helpers,
   preventing a new API read from hiding in that protected path.
8. Four expected public classes and metadata with inert injected services, and
   Computer Control metadata scope without excluding unrelated product capabilities.

These are candidate guards pinned to the protected Phase 6.22 HEAD, not permission
to commit or automatically rebase their checkpoint. Existing Phase 6.22 behavioral
tests remain responsible for fresh vetoes and precise fake-native execution ordering.

## Validation results

Codex GPT-6.1 Sol / Medium performed the initial static closure audit and prepared
the freeze guards/review. Its workspace sandbox could not execute the authorized
host interpreter (`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`):
`Test-Path` was denied and direct execution was unavailable. It did not download,
install or copy Python/packages and did not use a network workaround.

Authoritative runtime validation was then performed independently on the Windows host
with the installed Python 3.12.10 interpreter.

Independent validation initially exposed two **test-only guard defects**, not
production architecture failures:

1. The new AST guard incorrectly expected `_PointerInvocation` to appear as a
   production reference inside `pointer_binding.py`; it is the class definition there.
   The guard was corrected to prove exactly one class definition in pointer binding
   and exactly one production reference/import in the executor.
2. The historical Phase 6.20/6.22 continuity guard still pinned current HEAD to the
   Phase 6.21 commit. Its current-HEAD assertion was updated to the sealed Phase 6.22
   checkpoint while preserving the original Phase 6.20 tag/authority baseline.

Neither correction touched production code.

Final authoritative results:

- dedicated Phase 6.23 freeze tests: **8/8 passed**;
- focused freeze + historical continuity set: **23/23 passed**;
- affected Computer Control/pointer/UIA/DPI/policy/verification/executor/orchestration
  suite: **676/676 passed**;
- full unittest discovery: **1,533/1,533 passed**;
- `python -m compileall -q nayeon tests`: **PASS**;
- `git diff --check`: **PASS**.

Final static/integrity evidence:

- all **82 tracked production files** under `nayeon/` match the protected Phase 6.22
  checkpoint content;
- `git diff 797ed334f4256d2e05de6605d7ceb9f4bd96a57e -- nayeon` is empty;
- no untracked production file exists under `nayeon/`;
- `_pointer_invocation` has zero production call sites outside its definition;
- `_PointerInvocation` is defined only in pointer binding and referenced/imported only
  by the executor;
- pointer-effect importers remain exactly executor and pointer binding;
- `_PointerEffectService._insert` is called only by pointer binding;
- raw pointer SendInput remains confined to pointer_effect.py;
- keyboard SendInput remains the separately protected keyboard-only path;
- no Computer Control capability exposes click/drag/scroll/raw pointer authority;
- the exact approved point and Phase 6.22 normalization-through-insertion path remain
  checkpoint-identical.

No live effect or native smoke was required or performed because Phase 6.23 adds no
runtime behavior and changes no production code.

## Host validation commands

The independent host validation used the installed interpreter from the repository
root to run the dedicated freeze module, the affected Computer Control/trust-path
suites, full unittest discovery, compileall and Git diff/scope checks. The exact final
counts and outcomes are recorded above.

## Handoff

Candidate changes are test/documentation only: the new freeze test module, this review
document, and one historical continuity-test checkpoint maintenance edit. No file under
`nayeon/` changed. Nothing is staged; protected HEAD remains Phase 6.22. No commit,
tag, push or workbook update was made. Independent host validation is complete and the
candidate is ready for human seal review. Any future material change to the frozen
Computer Control v1 boundary requires an explicitly approved architecture phase.
