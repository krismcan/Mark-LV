# P285 disposable hosted durable test boundary, 19 November 2026

Development-only synthetic test integration. **PRODUCTION / REAL KEYS HOLD**.
P96 original HIGH remains OPEN; P76/P211/P216 historical failures unchanged.
Qualified external approvals **0/7**, full-product Windows regressions **0/3**.
No qualified external security, human consent, protected-store custody,
real credential authorization or release qualification is established here.

Initial branch `byok-c1-p285-durable-hosted-test-boundary-20261119`, clean at
exact HEAD `9d04c3a7e304fa67ce2ca364db8111f3ae7b4bd8`, no tag at HEAD.
All 1,148 inherited files, including P270-P284 code, tests and workflows,
are frozen. `.codex/CURRENT_STATE.md` was read; its November 3 Phase 10.2
checkpoint is stale for this branch. It remains unchanged under the user's
additive-only instruction. This is no completed product phase or new regression
baseline. Parent P284 PR #204 results (x64/x86 read-only 8/8, native compiler
18 positive / 24 guards) are user-supplied historical evidence.

## Exact execution boundary

Four additions only: this report, `tests/p285_durable_hosted/HostedReview.ps1`,
`tests/p285_durable_hosted/P285HostedDurableRunner.cs`, and
`.github/workflows/p285-windows-disposable-durable-review.yml`.

The workflow admits only opened/synchronize/reopened **draft** pull requests
whose base and head repositories both equal `krismcan/Mark-LV`. That repository
is itself a fork; no `fork=false` requirement is applied. Exact base branch:
`byok-c1-p284-durable-operation-bound-admission-20261119`; exact base SHA above;
exact head branch: the P285 branch above. Checkout pins the event's actual head
SHA, never a synthetic merge. A single-parent direct child of P284 is required,
with precisely these four added paths. All inherited Git tree entries and raw
disk blob IDs must match; every disk source gets before/after SHA256 evidence.
Ignored/untracked files, links, wrong topology, drift or missing evidence refuse.
No inherited workflow is altered. Existing P284 workflow scope does not match
this P285 base branch, and is not used as a durable execution shortcut.

The Windows-2022 x64/x86 matrix invokes direct Framework64/Framework
`v4.0.30319/csc.exe` with warnings as errors. The durable build uses the exact
17-source set and ten required defines from P284's hosted workflow, selecting
`DurableOperationAdmissionTests`. P284's broader `CompileReview.ps1` has
24 inputs for its additional historical entrypoints; it is never executed.
P285 compiles separately, with only `DEBUG` and
`C1_P285_HOSTED_ROOT_REVIEW_ONLY`, selecting `P285HostedDurableRunner`.
No production feature is enabled. Both builds reject ALL/missing required
defines and DEBUG+RELEASE with their explicit CS1029 guards. Failed compile,
guard, execution, cleanup or source checks leave the job RED; no waiver occurs.

Only the P285 host is launched by CI. It requires real Windows, the hosted
runner claims, `ImageOS=win22`, and explicit
`P285_HOSTED_ROOTS_REVIEW_ONLY=1`; actual process identity must be non-SYSTEM,
non-impersonated and non-Kristian. The current user's OS temp directory must
be owned by that actual user, on a fixed drive, with no reparse ancestor.
It prepares exactly 129 distinct, previously absent direct children named
`nayeon-p270-<Guid.NewGuid().ToString("N")>`. Creation uses the proven P270
Scope pattern: DirectorySecurity, actual SID owner, protected DACL, single
Allow FullControl ACE with ContainerInherit|ObjectInherit, then
`Directory.CreateDirectory(root, acl)`. Each root is independently checked
for exact owner, protected single explicit rule, propagation shape, empty
layout and no links. No existing ACL is repaired or machine policy changed.

The CI-furnished `P285_DURABLE_EXE` must equal the absolute fixed path
`RUNNER_TEMP/p285-build-x64|x86/P284Durable.exe`; the host itself must reside
beside it as `P285Host.exe`. File and ancestor reparse checks apply. CI supplies
`P285_DURABLE_SHA256`; the host compares the executable's exact bytes twice,
including immediately before launch. No command-line arguments, arbitrary
program selection, shell execution, elevation or inherited secrets are used.

The P284 child environment is cleared, then receives only Windows runtime
paths, the same OS temp path, hosted claims, `P284_REVIEWED_DURABLE_RUNTIME=1`,
`P271_HOSTED_DISPOSABLE=1`, and `P284_PREPROVISIONED_ROOTS` containing the 129
prepared roots. P270 still validates its own actual directory/file handles,
ACL and DPAPI journal/anchor semantics. The unchanged P284 -> P271 ->
P269/P268 -> synthetic P96 fixture path remains responsible for effects;
the host adds no approval, consent, credential port or alternate service route.

P284 retains its 120-second watchdog. The host waits at most 145 seconds,
kills a timed-out child with a bounded termination wait, and records its raw
exit. CI bounds the host to 190 seconds, with a 15-minute job limit. PASS needs
raw child exit 0, all 128 fixed case names in exact order, exactly one aggregate
`P284_SYNTHETIC_ONLY=PASS CASES=128 ASSERTIONS=<positive> BITS=32|64` matching
the process architecture, no stderr and the exact inherited explicit HOLD line.
Missing, extra, duplicate, reordered or malformed output fails. Captured text
is bounded; full inherited failure exceptions are reduced to a sanitized type,
and unknown text is redacted. No SID, temp path, env dump or exception stack
is emitted by the native host. Environment claims alone cannot authenticate
GitHub hosting; the exact workflow admission/source custody provides the
operational boundary. Hostile arbitrary same-user code is not isolated.

Finally, only successfully created roots enter cleanup. Each is rechecked as
a direct GUID temp child with the original owner/DACL and no reparse point.
The entire layout must contain only regular `journal.dpapi` / `anchor.dpapi`
leaves owned by the runner. Unknown entries or links are untouched and force
HOLD. Allowed leaves are deleted individually; the empty root is deleted with
`Directory.Delete(root, false)`, never recursively. A writer that cannot be
terminated prevents cleanup and forces HOLD. Failures do not mask the original
test result; remaining state is confined to the disposable runner and must be
discarded with it. Same-user malicious replacement races are not a production
security claim. Runtime logs are written only under the fixed RUNNER_TEMP
evidence directory. Artifact paths explicitly allow text logs/exits/source
hashes/binary hash only, never executables, DPAPI blobs, custody contents or roots.

## Open Failures & Prior-Issues Review — HOLD

| Issue / severity | Root cause / affected boundary / containment / evidence / disposition |
| --- | --- |
| P96 original HIGH OPEN | Historical check-to-effect revocation gap. Original callers and source untouched. This fixture uses inherited P268 ordering through P284/P271; no claim of original repair. HOLD. |
| P283/P271 split-owner HIGH hazard | Separate final owners cannot share effect approval. No P283 owner is constructed in this host or its 17-source harness. Existing P284 single P271 owner preserved. New hosted runtime and independent review pending; HOLD. |
| Swallowed reentry / uncertain controls, material | Earlier callbacks could swallow rejection. Unchanged P284 cases exercise ten probe points, expiry, impersonation, closed witness, races and sticky uncertainty. Compiled, not run locally; no closure claimed. HOLD. |
| P270/P271 durable evidence, material missing | P284 authored 128 cases without executing them. New fixture uses the previously proven P270 root ACL creation exactly. No historical ACL investigation or privileged workaround repeated. New x64/x86 hosted execution and review remain pending; HOLD. |
| Actual-user/store/consent HIGH boundary | Runner identity and DPAPI synthetic files establish no protected service, human consent or real credential authority. No provider/WinCred/service install/account/policy/production IPC route added. HOLD. |
| P76/P211/P216 historical failures | Historical failure/root-cause/review dispositions unchanged, unwaived. No fresh reproduction or repair claimed. HOLD. |
| Full-product and external qualification missing | Full Windows regressions 0/3; qualified approvals 0/7; SEC03/04 OPEN. This isolated integration grants none. HOLD. |

The user's bounded GO authorizes this additive development test integration and
disposable hosted synthetic execution. It does not close any inherited material
finding or authorize a release, security-sensitive seal or production phase.
Independent exact-source/security review is still OPEN. No commit, tag, push,
PR creation, merge, master workbook/dashboard update, local generated EXE run,
real key, provider call, WinCred access, installation, account change, elevation,
Application Control bypass or policy change is performed by this work.

## Actual validation

Hosted P285 execution: **NOT RUN**. The 128 cases remain authored but unexecuted
in this task; future CI results must be recorded from actual runs, never inferred
from compiler success. Local validation invokes compilers only, and parses the
hosted manifest as data without executing/dot-sourcing/evaluating it.

Final C# compiler evidence: four positive x64/x86 builds, raw exits 0;
32 negative builds, raw exits 1 with the required CS1029 diagnostic and no EXE.
Each architecture has two positive builds and sixteen negative guards.
All use warning-as-error direct compiler invocations; argument-array JSON,
logs and individual raw exits are preserved in
`C:\Users\krist\AppData\Local\Temp\nayeon-p285-reviewed-compile-a3056d85967b4d46b1c9d10dbe639f06`.
`raw-exits.txt` SHA256:
`63E7BC5C8809E769EC55EC360296FF318F2F357C47F81E0860F88452519FFF0D`.

The hosted manifest parses with zero PowerShell AST errors. Offline AST literal
comparison confirms the exact 17 sources and ten defines match P284's frozen
workflow in order. One comparison initially included trailing YAML when extracting
the old PowerShell block; bounded extraction corrected that tooling error and
both blocks then parsed successfully. No manifest was executed locally.
`rg` and offline Node YAML parsers were unavailable; no tooling was installed.
Authoritative Python path access was denied; no Python/runtime workaround,
unittest discovery or compileall was attempted under the compile-only scope.

All 1,148 inherited raw disk blobs match HEAD, with zero mismatches and no
tracked/index delta. Exactly four additive paths remain unstaged/uncommitted.
`git diff --check` and explicit added-file trailing-whitespace checks pass.
Self-review hardened absent-entry checks, failed-launch cleanup and final
evidence PASS ordering; runtime adversarial validation and independent review
remain OPEN. No runtime/full-product PASS is implied.
