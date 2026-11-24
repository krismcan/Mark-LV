# P320: synthetic custody core development checkpoint

2026-11-24. Existing P320 candidate resumed for interruption remediation only;
no new product phase, completed milestone or release. Codex sole source writer.
Branch: `byok-c1-p320-durable-custody-core-20261124`. Git HEAD and authoritative
P319 source baseline: `9679f4b4609f2c83ea61324ba88f023477ea564c`.
No milestone tag points at HEAD. Intake had exactly three unstaged draft paths:
the service project modification, new `CustodyTransactionCore.cs`, and new
`P320TransactionCoreTests.cs`. Their source intent is preserved with the build
isolation correction below; the existing test file is unchanged.

**102 authored synthetic cases; runtime/compile and independent review PENDING.
P96 HIGH OPEN; P292 UNKNOWN; five historical scope conflicts; full regressions
0/3; REAL-KEY NO-GO; production/release/seal HOLD.**

## Protected context interruption and restart boundary

The previous Codex turn correctly stopped when a write to
`.codex/CURRENT_STATE.md` was denied. That refusal is user-supplied incident
evidence; it was not reproduced or retried. The file still describes the
November 3 Phase 10.2 historical repair, rather than this P319/P320 Git lineage.
Git is authoritative for this development checkpoint. The stale file remains
unchanged, with no write, rename, replacement, permission change or workaround.
This review is separate P320 evidence, not a substitute context-file refresh.

AGENTS.md requires context refresh **before starting the next product phase**.
The user's explicit instruction authorizes completion of this already-started
P320 source checkpoint only. The unresolved refusal and stale context are an
explicit **blocker for any next formal product phase**. No new phase or seal
may be inferred from this record or from later green focused tests. A future
authorized process must resolve the context requirement without circumventing
the protected-file refusal; no such process is invoked here.

## Source review and compilation isolation

The intake service project compiled both the new core and linked
`tests/p95_native_custody_preflight/CustodyLedger.cs` into the real service.
The core mixed memory fixtures, synthetic crash selection and reflection-set
rendezvous fields with an `InternalsVisibleTo("P320.TransactionCore.Tests")`
declaration. Having no production caller is insufficient reason to ship those
test dependencies and hooks in a production assembly. No production need for
that dependency was found in the inspected startup/denial route.

The correction removes both added Compile entries and the new friend
declaration. The service project retains only an exclusion comment; its P319
Compile set, references, startup object, build guards and configuration remain
the same. The new `tests/p320_transaction_core/P320.Synthetic.csproj` compiles
exactly four source files into a separate executable:

- the unchanged P320 test driver;
- the draft core (including sealed memory fixture, crash image and rendezvous);
- the unchanged P306 `SyntheticTransactionOwner.cs`, supplying its existing
  immutable request/enums in this separate assembly;
- the unchanged P95 codec, linked only into the synthetic compilation.

There is no product assembly/project reference, native adapter, durable file
writer, pipe, service host or profile component in this synthetic executable.
The P306 file's historical friend declarations remain unchanged; no new friend
relationship is needed because tests and core now share the synthetic assembly.
Reflection accesses its own private core state and fixed synchronization fields.
Those fields remain test-only and do not enter the service binary. Reflection
and source-envelope checks are testing mechanisms, not a security sandbox or
evidence of production authority isolation against arbitrary modified code.

The actual inspected path remains `CustodyService.OnStart` -> executing identity
checks -> `ServiceRecoveryBoundary.RequireDenialOnlyStart` -> lifecycle start ->
`SyntheticTransactionOwner` and denial ingress/status pipes. The actual request
route calls `transactions.Deny`; ingress also calls `owner.Deny`, checks Allowed
false and emits fixed denial. No production route instantiates this new core.
OnStop/shutdown/fault, service identity, recovery checks, historical hosted
adapters and all prior permission/policy/confirmation boundaries are unchanged.
The service is compiled only by the proposed workflow and never executed there.

## Bounded core semantics and limits

The source models one request, one owner, a sealed one-use memory fixture and
one nonreentrant monitor shared by review, control, intent, fixed integer
mutation and terminal recording. There is no injected effect callback or
arbitrary storage port. Request owner, epoch, ID and operation are checked on
review and dispatch; an opaque owner-specific review object is consumed before
the intent sequence. It represents synthetic review, never human consent,
permission, policy or authenticated approval. Invalid identity/ticket or wrong
precondition terminates without a synthetic attempt. Duplicate dispatch returns
the existing outcome without another attempt. Control winning the gate before
dispatch terminates without mutation; after possible effect it reports too late.
Reentry, gate timeout or crash uncertainty becomes recovery HOLD.

Intent and anchor are strings verified by the existing bounded codec. The
deterministic nonce binds metadata through SHA-256; neither hashes nor an
anchor authenticate custody or prevent rollback. `IntentDurable` is a named
memory-model checkpoint, not persistence, flush, OS identity or physical
durability evidence. The only effect is assigning a fixed marker integer.
Stored/removed outcomes remain explicitly unverified and ProductionEligible is
always false. The recovery flag stays set after a successful synthetic sequence.

Crash injection is a fixed enum at ten seams. It throws into conservative
recovery handling; no process is killed. Images contain only ledger strings,
request metadata and that integer. Restart assessment is read-only, rejects
malformed/mismatched images and returns initial-unqualified, in-flight or
terminal-unverified classifications. It cannot resume, retry, replay, clear
recovery, authenticate absence or create another owner from an image. A seeded
present fixture has no persisted request witness; before-intent crash assessment
therefore conservatively classifies that image as malformed, as the test expects.
This does not close P315 post-native crash gaps or qualify service restarts.

The review traced constructor/fixture ownership, review identity, dispatch,
control, snapshots, uncertainty barriers and restart parsing against the tests
and P95 codec, then checked actual service startup and denial callers. No
real-store or authority-bearing repair is attempted. Broad exception handling
in constructor/dispatch only produces recovery HOLD; it does not count as
verified cleanup, diagnostics, production fault policy or universal safety.

## Authored cases and missing evidence

The existing driver counts `Run` invocations, not individual Check assertions:

| Cases | Per operation | Total |
| --- | ---: | ---: |
| Lifecycle and opposite-state precondition | 2 | 6 |
| Nine altered identity forms, each at review and dispatch | 9 | 27 |
| Four controls, each control-first and dispatch-first | 8 | 24 |
| Ten crash seams | 10 | 30 |
| Duplicate dispatch, duplicate review and review/cancel races | 3 | 9 |
| Malformed restart, fixture ownership/invalid construction, foreign review, reentry, timeout, invalid control | n/a | 6 |
| **Total across Add, Replace, Delete** | **32** | **102** |

Control-first includes pending/reviewed subchecks in each counted case; malformed
images and invalid construction similarly have multiple assertions inside a
case. The count remains 102, not a larger count of combinations/assertions. The
driver requires exactly 102 and exits nonzero on assertion/worker failure. No
runtime PASS, red-to-green proof, native crash result or independent validation
is inferred from source review. Hosted timing and compile correctness remain
unverified; synthetic concurrency cannot close original cross-process P96.

## Open Failures & Prior-Issues Review

Bounded inputs: Git intake, AGENTS.md, engineering failure gate, stale context,
P318/P319 review, P315 limitations, existing P320 drafts, P95 codec, P306 request
owner, actual service startup/recovery/denial entrypoints and P309/P319 workflow
patterns. No broad scan, credential inspection or local reproduction.

| Issue / source | Severity, root cause and affected boundary | Evidence / containment / review / disposition |
| --- | --- | --- |
| Context write refusal / user interruption report | Governance blocker; protected write refused; filesystem cause not investigated | No retry or workaround. Stale November 3 state read only. Separate documentation completes existing checkpoint; next formal phase HOLD. |
| Draft service/test coupling / this source review | Unnecessary synthetic codec, fixture and reflection hook dependency in product assembly; inclusion in csproj was the source cause | Removed product Compile entries/new friend, isolated four-source synthetic executable. Build topology inspection only; hosted compile and independent review pending. Not a production security closure. |
| P96 original race / inherited P319 record | HIGH OPEN; original last-current/control/effect ordering lacks qualified closure across processes and restarts | New memory monitor is a separate prototype, not original-route repair. No reproduced production closure; HOLD. |
| P292 SCM teardown / inherited P319 record | UNKNOWN; x86 teardown root cause and lifecycle qualification remain unproved | No SCM or service execution here or in new tests. Compile does not qualify lifecycle; HOLD. |
| P264 historical scope conflict | Frozen live local_byok_window raw-byte expectation | Inherited P318/P319 source evidence, not rerun here. No hash/assertion change or waiver; HOLD. |
| P133 historical scope conflict | Historical seven-path ancestry expectation | Inherited, unchanged/unwaived; no runtime reproduction here; HOLD. |
| P134 historical scope conflict | Historical four additions and older committed-blob expectation | Inherited, unchanged/unwaived; no runtime reproduction here; HOLD. |
| P140 historical scope conflict | Historical six-path delta and sole bridge modification expectation | Inherited, unchanged/unwaived; no runtime reproduction here; HOLD. |
| Direct BYOK B historical scope conflict | Connection-child hash and historical exact-descendant pin; older projection delegates to that guard | Fifth inherited conflict documented in P319. No guard/pin/projection modification; successor compatibility and independent review remain required; HOLD. |
| P315 durability precedent | Disposable hosted-user journal/pre-native termination is not service-principal storage or post-native recovery qualification | No DPAPI, ACL, file, process-death or native fixture executes in P320. No durability/replay assurance promoted. |
| Regression and review gaps | Compile/runtime pending; full regressions 0/3; independent security approval not obtained | Only sole-writer source review and whitespace check in this task. Relevant focused/affected/cross-phase and full evidence remain pending; HOLD. |

Disposition: source checkpoint prepared within the explicit interruption-remediation
authorization. The original three drafts are retained, with synthetic compilation
isolation and separate workflow/review additions. No material finding is waived,
downgraded or closed by a green source count. Production, real-key, seal and next
formal product phase remain **HOLD / NO-GO**.

## Exact source envelope and proposed hosted workflow

Six candidate paths relative to the exact P319 baseline: **one modification and
five additions**. No historical test/workflow or guard is changed.

| Status | Path | Purpose |
| --- | --- | --- |
| M | `src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj` | Exclusion comment only; P319 production build semantics retained |
| A | `src/Nayeon.ByokC1.Service/CustodyTransactionCore.cs` | Existing draft, synthetic-only; remove new friend and correct compilation comments |
| A | `tests/p320_transaction_core/P320TransactionCoreTests.cs` | Existing unchanged 102-case driver |
| A | `tests/p320_transaction_core/P320.Synthetic.csproj` | Dedicated four-source test compilation |
| A | `.github/workflows/p320-windows-synthetic-custody-core.yml` | Separate draft hosted compile/synthetic workflow |
| A | `docs/byok-c1-p320-synthetic-custody-core.md` | This source review, incident and pending-evidence record |

The authored workflow accepts only same-repository draft pull_request events in
`krismcan/Mark-LV`, repository ID `1402212689`, head ref above, base ref
`byok-c1-p319-offline-recovery-host-20261124` at the full P319 SHA above.
It uses Windows-2022 github-hosted runners, read-only contents permission and
SHA-pinned checkout of the event head without persisted credentials, submodules
or LFS. No dispatch, schedule, push trigger or pull_request_target is added.
Exact six-path A/M delta, ancestor, regular source modes, input SHA-256 hashes,
HEAD and clean index/worktree (including ignored files) are checked. It compares
the product project to the P319 witness allowing only the exact exclusion
comment/newline representation, and requires exact product/synthetic Compile
sets. Sources and artifacts are checked again after execution.

Four matrix shapes are authored: x64/x86, Debug/Release, .NET Framework 4.8.
Only installed Visual Studio MSBuild/framework targeting tools are used; missing
tools fail HOLD, with no install/download/restore or local interpreter fallback.
The actual service project is compile-only. The separate synthetic project
links the four explicit sources without a product reference. Only its test
executable is run, with no arguments, expecting the driver's 102 cases per shape
(408 invocations if all four later pass, still 102 distinct authored cases).
No original service/native/IPC/Tk tests or full discovery run is selected.

Each build has a 90-second deadline, the synthetic child 60 seconds, bounded
kill/wait and output draining, 24 KiB per-stream diagnostics and an eight-minute
job limit. The P309 process pattern is retained with truncation now failing
HOLD. Build/log files are confined to hosted RUNNER_TEMP; source remains clean.
Normal future checkout uses network; this task performs no network operation.
No service binary execution, storage/profile/secret operation, native credential
operation, IPC, provider access or enabling effect is part of the new test route.
This is a source-reviewed fixed composition, not a general runtime sandbox.

## Local verification and pending handoff

Local validation is **git diff --check only**, including new-file no-index
whitespace checks against `/dev/null`; source/Git reads and authorized edits are
not runtime evidence. No compiler, parser, interpreter, tests or product code
was accessed/executed locally. Workflow syntax/build/runtime correctness is
pending hosted execution. No tooling was downloaded/installed, no permission
or sandbox changed, and no protected context write was attempted. No staging,
commit, tag, push, merge, hosted dispatch, workbook or dashboard update occurred.

Whitespace outcome: tracked `git diff --check` exited 0 without diagnostics.
All five added files were checked separately with
`git diff --no-index --check -- /dev/null <path>`; each exited 1 for the
new-file difference without whitespace diagnostics. This is source hygiene
only, with no runtime or independent-review approval.

The next action is human source review of this exact six-path checkpoint and,
if separately published through the authorized process, hosted compile and
synthetic evidence on the exact event head. No publication is performed here.
Independent source/security review, affected/cross-phase assurance, all three
full regressions, resolution of the five historical conflicts and the context
blocker remain outstanding. Real-key NO-GO and production/release HOLD persist.
