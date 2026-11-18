# P276 current product package refusal classification repair

18 November 2026, OM v2.1. **Unstaged repair candidate; production HOLD,
real keys NO-GO, complete unfiltered Windows product regressions 0/3.**
Independent review and hosted runtime evidence are pending. Draft publication
and any later commit belong to Nayeon; this writer stops before commit.
No PR has been created or merged by this work.

## Authoritative baseline and scope

Initial Git inspection found the requested clean branch
`byok-c1-p276-p211-current-package-refusal-20261118`, HEAD
`0492f955dda7fe2f03d93d46caedee7329ea89ed` (P275), empty index delta,
and no tag pointing at HEAD. The isolated directory is
`D:\Nayeon\CODEX_P276_P211_PACKAGE_REFUSAL_20261118`.
`AGENTS.md` and `docs/engineering_failure_review_gate.md` were read.
`.codex/CURRENT_STATE.md` describes earlier Phase 10 work, conflicts with this
Git baseline and is preserved under the explicit four-path scope. No next
product phase, completed-product context refresh or milestone seal is claimed.

Exactly one inherited product file changes:

- `nayeon/brain/p211_high_assurance_package_quarantine.py`

Exactly three paths are added:

- `tests/test_byok_c1_p276_current_package_refusal.py`
- `.github/workflows/p276-windows-package-refusal-current.yml`
- `docs/byok-c1-p276-current-package-refusal.md`

Git contains 1,113 inherited regular blobs; all **1,112 other inherited
blobs**, including every historical test and all P275 files, remain unchanged.
The prospective one-child review commit contains 1,116 regular blobs. Local
work remains at the parent with an untouched index; the one-child gate is for
Nayeon's later draft publication, not evidence that a child exists now.
No other source, historical review, action pin, milestone tag, workbook or
dashboard changes. No staging, commit, tag, push or publication by Codex.

Frozen P275 backend SHA-256:
`9FFB136A73E4277B966FAE025A3962123433745B6BA8907AB3B8C4137F4A21B3`.
Original P211 test source SHA-256:
`83DA4CDEE75408740079D3BBF9D2747756F7E56A309A83B24842246B489F6E6B`.
Original P216 test source SHA-256:
`FF077BB4959A0EB5D33D95397649C772F395FE89143C5A8643589E5CB9B4A1F5`.

## Root cause and intended semantics

P275 removed callable `_Advapi32Adapter.write/delete`, their native
`CredWriteW/CredDeleteW` bindings/calls and native plaintext extraction/raw
pointer return. It retained presence-only read/free and an inert denial-only
`read` compatibility method. The public default get/put/delete remain denied.
This repair does not restore any of those retired effects.

P211's original `high_assurance_legacy_risk_present` requires a conjunction:
native write/delete source, P132 controller construction/effect call sites,
and P133 fixed Python child launcher. Its native-effect component is now
accurately **false**, making the historical triple false. Before this repair,
executable package plans therefore fell through to `UNRECOGNISED_PAYLOAD`.
They still received **NO RELEASE**; no production-release allow occurred.

The separately named `source_mode_runtime_risk_present` property requires
the existing P132 factory/controller put/delete source witness and P133 fixed
Python child witness. It does not depend on retired native adapter methods.
The original predicates and historical triple retain their existing semantics.
P258's call sites use `_mutation_backend.put/delete`; the inherited bounded
text predicates still recognise their `_backend.put/delete` suffixes. This
is source evidence for a known executable route, not proof that the default
controller can perform a credential mutation.

Dependency trace reviewed: workspace/application entry -> launch bridge ->
fixed source Python child -> local BYOK window ->
`compose_user_scope_local_byok()` -> `LocalByokController` ->
`WindowsCredentialBackend`. Default mutation binding is absent; the separate
fake-injection route and controller call sites remain in source. Lifecycle,
UI, backend, service and all alternate entrypoints are unchanged. Historical
copies, running children and restarts are not revoked by source classification.

Plan shape/canonical names, case collisions and source readability are checked
before executable classification. After reading the fixed sources, all seven
`.py` files must pass `ast.parse` and `compile(tree, path, "exec")` in memory.
No reviewed module is executed or imported. Syntax, NUL, value, type, Unicode
or compilation rejection makes `exact_legacy_source_readable` false and
returns `SOURCE_UNPROVEN` immediately after canonical path validation, before
any payload classification. Valid backend/controller ASTs remain the actual
inputs to their existing predicates. `CustodyService.cs` stays text-only:
this check does not parse C# as Python or verify C# syntax/compilation.
The executable branch now accepts either
the historical triple or the current runtime-route predicate. Known source
directories and Python/compiled/DLL/EXE/archive/wheel/installer/PowerShell
payloads retain the specific `LEGACY_EFFECT_PATH` refusal; Python-window,
batch, command, VBScript, JavaScript and shell suffixes are also classified.

| Intake/source condition | Refusal / authority |
| --- | --- |
| Current source-mode code, unsigned EXE, script, extension or mixed approved README plus code | `LEGACY_EFFECT_PATH`; all authority false |
| Required source absent/unreadable, invalid UTF-8, or any fixed Python source failing parse/AST compilation (including NUL) | `SOURCE_UNPROVEN`; all authority false |
| Invalid plan type/size or empty plan | `INVALID_PLAN`; all authority false |
| Traversal, drive/ADS, noncanonical name, alias or case collision | `UNTRUSTED_PATH`; all authority false |
| Sole exact `P211_QUARANTINE_README.txt` | `ABSENT_RELEASE_AUTHORITY`; all authority false |
| Unknown `README.md` | `UNRECOGNISED_PAYLOAD`; all authority false |
| Copied factory removed as in original test18; launcher removed/changed | Known-route evidence absent, executable remains `UNRECOGNISED_PAYLOAD`; all authority false |
| Copied backend, controller, launcher or any other reviewed Python file malformed | Readability false; `SOURCE_UNPROVEN`, never generic payload classification |
| Forged signer, policy approval or filled companion pins | Cannot mint any authority |

`LEGACY_EFFECT_PATH` means an **untrusted legacy executable route**. It is
not evidence that retired native credential effects are reachable after P275.
Missing or changed known-route evidence is not proof of safe isolation.
`exact_legacy_source_readable` requires readable fixed source and successful
parse/AST compilation of its seven Python files. It supplies no source
approval, hash identity, signed-image provenance, real-key authorization or
OS trusted-code proof. C# validity remains unverified by this source check.

The five release/credential/signing/isolation/real-key booleans remain
permanently false; frozen receipts reject positive construction. The policy
imports no ctypes, subprocess or credential implementation and performs no
native call, package build, install, signing, release or secret operation.
Validation does not execute a package. Model output never supplies authority.

**Same-user alternate Advapi32 access remains a real OS threat.** Hostile
same-SID Python, older copies, object replacement and independent native
callers are not isolated by this detector, Python flags or source hashes.
Presence cannot detect same-presence replacement/ABA. This repair establishes
no trusted consent, protected service store, OS isolation or deployed-copy
revocation across windows/processes/restarts.

## Source-only tests and hosted evidence contract

The new suite contains 12 tests, including actual current witness semantics,
route/suffix/mixed-manifest classification, read-only nonapproval, missing and
tampered source (all seven fixed Python files each receive syntax, NUL and
parse-valid-but-compile-invalid mutations in test04), exact original test18
valid-syntax factory mutation, independently removed
put/delete call sites, changed launcher/module, forged approvals/pins, invalid
paths and plans, all five immutable authority fields, and three policy mutants
(removed current branch, constant-false risk, constant-true risk).
Mutants execute only isolated copies of the pure deny-only detector; original
modules/tests are never replaced. Temporary source trees are text-only copies.
Tests require the exact backend hash and preserved P275 executable-AST
contract: no native mutation/plaintext return/pointer escape. These are
bounded source contracts, not a general Python sandbox or OS guarantee.

The workflow uses the exact three action commit pins inherited from P275.
It admits only a same-repository **draft** `pull_request` in `krismcan/Mark-LV`,
from the exact P276 branch to
`byok-c1-p275-retire-legacy-python-native-effects-20261118`, with base SHA
`0492f955dda7fe2f03d93d46caedee7329ea89ed`, a single direct child, four exact
changed paths (1 modified + 3 added), regular modes and a clean checkout.
It checks the actual event JSON as well as job conditions. These are custody
controls, not an independent attestation of the runner or release authority.

The matrix is GitHub-hosted Windows 2022, x64/x86 CPython **3.12.8**. Hosted
runtime verifies platform, interpreter version and pointer width. Before tests,
it records every candidate raw disk Git blob and SHA-256, compares all 1,112
immutable inherited blobs with P275 and checks the backend literal hash.
Final source SHA-256 readback and clean-status checks detect test side effects.
The complete 1,116-path source manifest includes inherited and added paths.

Hosted CPython parses/AST-compiles P211, P276 tests, P275 tests/inventory and
the backend without executing their module bodies in that parser process.
Separate subprocesses run P276's 12 tests, the preserved P275 18 fake tests,
the preserved read-only P275 source inventory, and current witness/sample
refusal receipts. Count/waiver checks supplement authentic focused exits.
These focused tests must be GREEN for narrow repair validation. They neither
substitute for original acceptance nor count as full product regressions.
No native backend is imported/executed by the P276 source tests or receipt;
P275's own unchanged tests bind deterministic fake DLLs and guard real loading.

The **original unchanged P211 22 tests run in a separate historical step**,
even after a focused failure if custody and Python setup succeeded. Original
`test_02_actual_python_wincred_effect_proven_source_reachable` must genuinely
FAIL because the retired native-effect predicate remains false. Its authentic
unittest exit **1** remains unwaived, making the workflow **RED/HOLD**.
The other 21 outcomes are PENDING, not preclaimed. Diagnostic JSON reports
whether all 22 ran and test02 actually failed; an import/infrastructure failure
is not evidence of that assertion. Unexpected raw green also requires HOLD
investigation; the raw result is preserved rather than converted into PASS.
No original test edit, monkey-patch, skip, xfail, expected-failure waiver,
`continue-on-error`, exit coercion or synthesized acceptance is used.

Each child process writes raw binary stdout/stderr and its native return code
to separate files. Final evidence SHA-256s cover every stdout/stderr/exit,
parser result, inventory, witness/sample receipt, diagnostics and complete
source manifest. Artifacts are text only, retained even on failure. Display
decoding never changes the raw log files. No real WinCred effects, provider,
credential material, service installer, C# execution or OS security change
runs locally or hosted. P134/P274 real-native harnesses are not invoked.
P216/old adapter are not rerun by this workflow; their prior RED stays open.

## Open Failures & Prior-Issues Review

Reviewed the engineering failure gate, P275 review/source/fake tests/inventory/
workflow, P211 implementation/original 22 tests/review, P132 controller/P133
launcher, backend, P216 source tests and service/store decision record. The
counts below are **user-reported P275 hosted results**, not newly reproduced
local or P276 hosted evidence. This explicitly authorized bounded regression
repair does not advance a product phase or waive a security-sensitive gate.

| Issue, source/date | Severity, cause and impacted trust paths | Evidence / repair / tests | Independent review and disposition |
| --- | --- | --- | --- |
| Malformed fixed Python misclassified, independent P276 security finding, 2026-11-18 | Material fail-closed classification defect: caught backend/controller parse failures kept readability true; five other Python files were never parsed. Existing test04 encoded the wrong generic refusal. All package-plan callers shared this source witness. | Compile all seven parsed ASTs in memory; specified parse/compile exceptions mark source unproven. Extend test04 with 21 source-copy cases plus source-before-classification and path-validation precedence assertions. No payload execution. | Finding supplied as independently confirmed; corrective source edit complete, hosted adversarial/runtime evidence and independent rereview PENDING; HOLD. |
| P211 specific refusal regression at P275, 2026-11-18 | MEDIUM classification defect: executable branch coupled to retired direct native triple; packaging intake remains deny-only. P132/P133 runtime source still present. | Source reproduction confirmed. User reports original P211 14 FAIL of 22 at P275. Add independent current-route property/branch and source-only adversarial mutants. P276 runtime pending. | Nayeon review pending; narrow repair candidate only, HOLD. |
| Original P211 test02, P211/P275 | Material historical contract conflict: assertion positively requires retired native writes/deletes. Restoring it would defeat P275 retirement. | Original source/hash unchanged; genuinely false predicate retained. Separate original 22-test run must preserve raw exit 1 and authentic failure. No waiver; remaining outcomes pending. | UNWAIVED HOLD, even if focused tests pass. |
| P275 current fake controls, reported 2026-11-18 | Source-hardening evidence is bounded to fakes/current source, not deployment or service authorization. | User reports 18 + 20 + 12 + 28 PASS per architecture. Preserve all; rerun original current 18 plus P276 in hosted workflow. Not a full-suite credit. | Original source unchanged; P276 hosted evidence and independent review pending. |
| Old native adapter/P216 expectations, P275 reported results | Material historical failures: retired native read/write/delete requirements and direct-effect source assumptions. Shared backend and source witnesses affected. | User reports old adapter 2 FAIL + 5 ERROR and P216 2 FAIL. All originals immutable; no fabricated closure or native runtime restoration. Optional reruns omitted here. | Unwaived HOLD; no acceptance credit from other green tests. |
| P76 original four failures, P273/P275 review | Material governance/current-branch failures remain separate from successor source admission. | No P76 code/tests or history changed. Actual prior failures retained; no unfiltered suite run. | OPEN, HOLD. |
| P96 original race, P275 review | HIGH: original approval/revocation can race terminal effect ownership. Synthetic successors do not repair the production comparator. | Original P96/P268/P274 bytes preserved by complete custody. No race repair or new live experiment in P276. | OPEN, HOLD. |
| Service/store identity and ownership, P216/P275 | HIGH: LocalSystem vs `NT SERVICE\NayeonByokCustody` unresolved; qualified SEC03/SEC04/GOV owners and source-bound decisions absent. | Preserve service/store source. No account, ACL, DPAPI migration, installer, signing or OS policy changes. Qualified signer, authenticated consent/IPC and independent protected antirollback evidence missing. | External owner decisions absent; HOLD. |
| Same-user alternate effects, old artifacts and process/restart routes | HIGH residual OS threat: independent Advapi32 calls, injected objects, old binaries/children and same-presence replacement remain outside detector authority. | Trace and limit claims documented; no capability fabrication, credential enumeration, cleanup/migration or OS isolation claim. | No closure; production HOLD, real keys NO-GO. |
| Stale context / inaccessible Kristian interpreter, 2026-11-18 | Environment/evidence gap: state disagrees with Git; approved Python executable metadata access denied. | Preserve state; no bypass, alternative interpreter, download, package install/copy or network workaround. Static work only locally; native Python parser/tests hosted only. | Runtime and independent review pending, HOLD. |

## Local validation and handoff

Local static checks: all 1,113 index entries still equal HEAD, all 1,112 other
inherited files match raw Git blob SHA-1 framing, backend and historical test
SHA-256s match the pins above. All four workflow PowerShell blocks parse and
compile without executing; all three action pins exactly match P275.
`git diff --check` and all four paths' whitespace checks are clean. Exact
1-modified/3-added scope and the 12 new test methods were checked. These
are PowerShell/static custody results, **not Python
parser/AST, unittest or runtime evidence**. Approved interpreter metadata access
returned access denied; no Python executable was invoked and no workaround
was attempted. Hosted logs/native exits and independent review are PENDING.

Next: Nayeon independently reviews this exact unstaged four-path candidate,
owns any later one-child commit and same-repository draft PR, then inspects
both architectures' complete source receipts, focused GREEN and authentic
historical RED/HOLD logs. Investigate every actual result; do not assert the
expected 21 other P211 successes before execution. No full unfiltered product
regression credit: **0/3**. Draft remains unmerged; **production HOLD; real
keys NO-GO**. No Drive master workbook or dashboard update until C1 is fully
done. **STOP BEFORE COMMIT.**
