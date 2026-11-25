# P320: synthetic custody core development checkpoint

2026-11-25. Existing held P320 checkpoint resumed for bounded P96 remediation only;
no new product phase, completed milestone or release. Codex sole source writer.
Branch: `byok-c1-p320-durable-custody-core-20261124`. Exact intake HEAD:
`ca5d5218478d4d165cf61e35e5b697137e703c14`, original parent/P319 baseline:
`9679f4b4609f2c83ea61324ba88f023477ea564c`, existing draft PR239.
Intake worktree/index clean; no milestone tag points at HEAD. The original
November 24 interruption-remediation intake had three unstaged draft paths:
the service project modification, new `CustodyTransactionCore.cs`, and new
`P320TransactionCoreTests.cs`. That checkpoint isolated their compilation as
described below. This repair changes only the existing core, driver, workflow
and this document within the same six-path envelope.

**142 authored synthetic cases; repaired-source runtime/compile and independent
review PENDING. Prior hosted four shapes each 102/102 PASS are user-reported
evidence for the intake HEAD only, not this repair. P96 HIGH OPEN for actual
production closure; P292 OPEN; five historical scope conflicts; full regressions
0/3; external approvals 0/7; REAL-KEY NO-GO; production/release/seal HOLD.**

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

- the existing P320 test driver, now extended without removing an original case;
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
the current conservative outcome without another attempt. Control winning the
gate before dispatch terminates without mutation; after commitment it reports
too late only while uncertainty is absent. Reentry, gate timeout or crash
uncertainty becomes recovery HOLD.

### P96 concrete synthetic publication/commitment repair

The intake core published `uncertain` outside the monitor, separately from
`Barrier(); possible = true; attempts++`. A timeout/reentry after the barrier
could therefore precede commitment yet fail to prevent it. `Exit` and `Observe`
only converted outcome None; uncertainty after terminal publication could be
hidden behind stored/removed-unverified or a successful control result. These
are source-level counterexamples from the read-only investigation, not a
runtime reproduction or a claim that the original production P96 is repaired.

The existing core now keeps uncertainty (bit 0), possible-effect commitment
(bit 1), and terminal outcome (higher bits) in one atomic `publication` word.
The gate still owns request review, ledger strings, marker, stages and attempt
count. No second owner, model, storage adapter or effect path is introduced.

| Transition / observation | Linearization and consequence |
| --- | --- |
| Enter timeout or reentry | CAS sets the sticky Unknown bit, preserving commitment and terminal bits. It never clears, including after a terminal result. |
| Possible-effect commitment | A single CAS from zero to Committed. Unknown winning first makes that CAS fail: no commitment, attempt or marker mutation. No separate check/mark window remains. |
| Commitment winning first | MayHaveEffect stays true. A subsequent barrier may still suppress the attempt; commitment is permission for a possible synthetic effect, not evidence an attempt or mutation happened. Unknown arriving after that barrier cannot retract commitment or promise prevention. |
| Terminal publication | Finish CAS preserves both flags, retains a prior terminal result absent uncertainty, and projects RecoveryRequired whenever Unknown is present. A racing uncertainty forces CAS retry or subsequently overrides the projection. |
| Public outcome / control | Atomic publication reads determine the returned result. Unknown takes precedence over AlreadyTerminal and TooLatePossibleEffect. A control whose terminal publication races Unknown returns HoldUnknown, never Applied when Unknown precedes its final result read. |
| Snapshot | One publication read supplies outcome/commitment. Under the gate, AttemptsKnown is true. A failed Enter cannot read the gated counter: committed means AttemptsKnown=false and Attempts=0 is only a placeholder; without commitment zero is known. |

All later public outcomes after Unknown are RecoveryRequired, and later controls
are HoldUnknown. An earlier returned immutable snapshot/result remains a
historical observation at its own linearization point; later uncertainty may
conservatively downgrade it. No result is a verified effect or a lasting promise
of successful cancellation. Recovery never authorizes replay; the exact prior
ticket, a new ticket, duplicate dispatch and controls cannot clear the state.
The crash image does not persist this publication word: restart classification
can still be TerminalUnverified while the live core holds uncertainty. Neither
image classification nor terminal ledger shape verifies task success or clears
the live HOLD, and no image can construct/resume an owner.

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
| Six publication seams, each with control-timeout and observation-timeout | 12 | 36 |
| Sticky reentry after returned dispatch or control terminal result | 1 | 3 |
| Concurrent claim of the exact same memory fixture object | n/a | 1 |
| **Total across Add, Replace, Delete** | **45** | **142** |

Control-first includes pending/reviewed subchecks in each counted case; malformed
images and invalid construction similarly have multiple assertions inside a
case. The original 102 Run cases and their assertions remain. Terminal now also
requires AttemptsKnown=true; its old "strict first terminal" comment is narrowed
to stability absent new uncertainty. The reflection reader supports properties
because outcome and possible now project the atomic word instead of separate
mutable fields; existing dispatch-first expectations remain unchanged. The
driver requires exactly 142 and prints that checked count; no count is a PASS.

The six new fixed event rendezvous pause immediately before/after commitment,
immediately before/after dispatch terminal publication, and before/after control
terminal publication. The before-commit seam is AFTER the prior final barrier;
the before-terminal seam is AFTER terminal ledger verification. Thus the tests
target the actual unchecked windows. Each forces a real two-second Enter timeout
via Revoke or Observe while the owner remains paused, then checks sticky HOLD,
commitment versus exact attempts, unchanged or completed marker/ledger shape,
all later controls, consumed-ticket replay refusal and ProductionEligible=false.
After commitment but before attempt, the expected state is MayHaveEffect=true
and Attempts=0; after terminal publication, outcome must downgrade to recovery.
No original expected outcome or crash-seam count is weakened to obtain this.

The three added reentry cases each include both a completed dispatch and a
completed cancellation, preserve the earlier snapshot, then require conservative
downgrade and no replay. Concurrent fixture claim tests the existing Claim CAS:
exactly one constructor wins over the SAME object. Separate fixtures may each
have owners; no global identity, shared-storage or cross-process ownership is
claimed or added. All rendezvous are bounded events, with no injected callback.

No runtime PASS, red-to-green proof, native crash result or independent validation
is inferred from source review. Hosted timing and compile correctness for these
bytes remain unverified; synthetic concurrency cannot close production P96.

## Open Failures & Prior-Issues Review

Current bounded inputs: exact Git intake, AGENTS.md, engineering failure gate,
read-only stale context, existing P320 source/tests/workflow/review, project
Compile sets, P95 codec and P306 request owner. Prior recorded P318/P319, P315,
actual service entrypoint and P309 workflow analysis is retained as historical
context, not claimed as a new architecture survey. No broad scan, credential
inspection or local runtime reproduction.

| Issue / source | Severity, root cause and affected boundary | Evidence / containment / review / disposition |
| --- | --- | --- |
| Context write refusal / user interruption report | Governance blocker; protected write refused; filesystem cause not investigated | No retry or workaround. Stale November 3 state read only. Separate documentation completes existing checkpoint; next formal phase HOLD. |
| Draft service/test coupling / November 24 source review | Unnecessary synthetic codec, fixture and reflection hook dependency in product assembly; inclusion in csproj was the source cause | Intake HEAD already removed those Compile entries/new friend and isolated four-source synthetic executable. Prior hosted compile/synthetic PASS per user; both projects unchanged here. No production security closure. |
| P96 synthetic proof gap / current read-only investigation and user request | HIGH OPEN for actual production closure; independent uncertainty write, final commitment marker and terminal publication were not atomic | Existing synthetic core repaired with one CAS publication word; 36 timeout-boundary and 3 sticky reentry cases authored, not executed. Independent repair review and new hosted evidence pending. No original-route/cross-process closure; HOLD. |
| P292 SCM teardown / user-supplied independent historical archive reconciliation | OPEN; historical x86 teardown remains unknown | ZIP CRC and before/after manifest 18/18 verified in separate reconciliation; lifecycle 0/6,4/6,3/6; cleanup 0/6,6/6,5/6. This historical evidence is not mutable qualification. No SCM/service execution or new qualification authorized here; HOLD. |
| P264 historical scope conflict | Frozen live local_byok_window raw-byte expectation | Inherited P318/P319 source evidence, not rerun here. No hash/assertion change or waiver; HOLD. |
| P133 historical scope conflict | Historical seven-path ancestry expectation | Inherited, unchanged/unwaived; no runtime reproduction here; HOLD. |
| P134 historical scope conflict | Historical four additions and older committed-blob expectation | Inherited, unchanged/unwaived; no runtime reproduction here; HOLD. |
| P140 historical scope conflict | Historical six-path delta and sole bridge modification expectation | Inherited, unchanged/unwaived; no runtime reproduction here; HOLD. |
| Direct BYOK B historical scope conflict | Connection-child hash and historical exact-descendant pin; older projection delegates to that guard | Fifth inherited conflict documented in P319. No guard/pin/projection modification; successor compatibility and independent review remain required; HOLD. |
| P315 durability precedent | Disposable hosted-user journal/pre-native termination is not service-principal storage or post-native recovery qualification | No DPAPI, ACL, file, process-death or native fixture executes in P320. No durability/replay assurance promoted. |
| Regression and review gaps | Repair compile/runtime pending; full regressions 0/3; external approvals 0/7 | Prior four hosted shapes 102/102 each PASS apply only to intake HEAD per user. Only sole-writer source review and whitespace check here; independent repair approval and relevant regression evidence remain pending; HOLD. |

Disposition: source repair prepared within the explicit existing-P320 remediation
authorization, preserving its compilation isolation and six-path envelope.
No material finding is waived, downgraded or closed by a green source count.
Production, real-key, seal and next
formal product phase remain **HOLD / NO-GO**.

## Exact source envelope and proposed hosted workflow

Six candidate paths relative to the exact P319 baseline: **one modification and
five additions**. No historical test/workflow or guard is changed.

| Status | Path | Purpose |
| --- | --- | --- |
| M | `src/Nayeon.ByokC1.Service/Nayeon.ByokC1.Service.csproj` | Exclusion comment only; P319 production build semantics retained |
| A | `src/Nayeon.ByokC1.Service/CustodyTransactionCore.cs` | Existing synthetic-only core; atomic uncertainty/commitment/terminal repair |
| A | `tests/p320_transaction_core/P320TransactionCoreTests.cs` | Original 102 cases retained; 40 added, exact total 142 |
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
executable is run, with no arguments, expecting the driver's 142 cases per shape
(568 invocations if all four later pass, still 142 distinct authored cases).
No original service/native/IPC/Tk tests or full discovery run is selected.

Each build has a 90-second deadline, the synthetic child 120 seconds, bounded
kill/wait and output draining, 24 KiB per-stream diagnostics and an eight-minute
job limit. The child limit increased from 60 seconds because 36 new cases each
exercise the unchanged two-second Enter timeout (72 seconds before other work).
No wait/deadline expiry is accepted as a PASS. The P309 pattern retains failure
on diagnostic truncation. Build/log files are confined to hosted RUNNER_TEMP;
source remains clean.
Normal future checkout uses network; this task performs no network operation.
No service binary execution, storage/profile/secret operation, native credential
operation, IPC, provider access or enabling effect is part of the new test route.
This is a source-reviewed fixed composition, not a general runtime sandbox.

## Local verification and pending handoff

Local validation for this repair is **source review and git diff --check only**;
source/Git reads and authorized edits are not runtime evidence. No compiler,
interpreter, build, tests or product runtime was executed locally.
Workflow syntax/build/runtime correctness for the repair is
pending hosted execution. No tooling was downloaded/installed, no permission
or sandbox changed, and no protected context write was attempted. No staging,
commit, tag, push, merge, hosted dispatch, workbook or dashboard update occurred.

The November 24 preparation recorded clean tracked and new-file whitespace
checks; that is historical source hygiene only. On November 25, repair source
review traced CAS order, result projections, commitment/attempt separation,
sticky uncertainty, replay refusal, fixed rendezvous ordering and the exact
142-case Run expansion. `git diff --check` exited 0 without diagnostics.
Exactly four paths differ from intake HEAD, all inside the existing six-path
envelope; both project files and `.codex/CURRENT_STATE.md` have no diff. No
runtime, red-to-green or independent-review approval is inferred. Disposition
remains HOLD pending those missing forms of evidence; no formal-phase GO.

The next action is human source review of these unstaged changes within the
existing checkpoint. Any later publication and hosted execution require their
own authorized process; no network, dispatch or publication is performed here.
Independent source/security review, affected/cross-phase assurance, all three
full regressions, resolution of the five historical conflicts and the context
blocker remain outstanding. Real-key NO-GO and production/release HOLD persist.
