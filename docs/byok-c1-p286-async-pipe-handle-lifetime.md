# P286 async pipe handle lifetime successor — 19 November 2026

TEST ONLY / NONDEPLOYABLE / UNREVIEWED / runtime HOLD. Production and real keys
remain HOLD. This is an additive repair candidate, not a sealed product phase.

Initial Git custody: branch
`byok-c1-p286-async-pipe-handle-lifetime-20261119`, HEAD
`52ff1f041afc06a48c41c92aac8ef404d71cc0cb`, clean index/worktree, 1,152 tracked
files, no milestone tag at HEAD. Parent P285 PR #205 is draft and unmerged
(user-supplied status). `.codex/CURRENT_STATE.md` describes older Phase 10.2
work and disagrees with this Git checkpoint. It remains frozen: the explicit
P286 envelope prohibits modifying any inherited file. No new phase or seal is
claimed and no historical context entry is promoted.

## Open Failures & Prior-Issues Review

| Issue / severity | Evidence, boundary, cause, repair and disposition |
| --- | --- |
| P265/P285 asynchronous callback crash / HIGH development reliability blocker | User-supplied actual hosted x86 run **44620851229**, artifact **14577033024**: 76 of 128 P284 cases completed, then unhandled `System.ObjectDisposedException`. Other 128/128 runs do not waive this RED history. The six reported frames are below. P265 caller-side event disposal can precede Framework signaling when concurrent pipe disposal makes `EndWaitForConnection` reject the stream before waiting/closing its event. Read/write have the same caller ownership pattern. New P286 callback ownership addresses all three routes. Source/compile checks only; deterministic runtime tests and three hosted trials per architecture are prepared but NOT RUN. Independent review OPEN; defect closure HOLD. |
| P285 TEMP parent-owner assumption / material hosted blocker | Parent review records x64/x86 run 44608891668 failing at `temp-owner`. Parent repair stopped authorizing the existing OS TEMP owner and retained exact actual-user ownership/protected single-ACE checks on each disposable child. P286 reuses that frozen P285 host verbatim. No new parent ACL assumption or edit. P286 runtime evidence remains OPEN. |
| P96 original / HIGH OPEN | No P286 repair or waiver; production security gate HOLD. |
| P76 / P211 / P216 historical issues / unwaived | This bounded lifetime repair grants no closure, credential authority or external acceptance. No new severity or root-cause claim for these historical issues. |
| Local compiler orchestration error / tooling, corrected | First inline local command combined `/define`, `/main` and `/out` into one argument through PowerShell expression precedence. Raw exit 1, CS2029/CS0017, no EXE. The command JSON/log and RED receipt remain in the first temp evidence directory. Corrected direct argument-array construction passed; no source or test assertion was weakened. |
| Local whitespace wrapper / tooling, corrected | A wrapper initially treated the expected `git diff --no-index --check` difference exit 1 as failure despite empty diagnostics. The corrected check accepts only 0/1 with zero diagnostics and separately rejects trailing whitespace. No source change was needed. Wrapper RED receipt is preserved in the final review evidence directory. |

Reported crash stack, preserved in order:

```text
System.Runtime.InteropServices.SafeHandle.DangerousAddRef
System.StubHelpers.StubHelpers.SafeHandleAddRef
Microsoft.Win32.Win32Native.SetEvent
System.Threading.EventWaitHandle.Set
System.IO.Pipes.NamedPipeServerStream.AsyncWaitForConnectionCallback
System.Threading._IOCompletionCallback.PerformIOCompletionCallback
```

This report does not claim independent artifact retrieval or a local native
reproduction. The observed crash/call path is supplied verified evidence; early
event-owner disposal is the source-supported explanation being repaired.

## Design and bounded source delta

`native_c1_successor/P286SafeDevelopmentPipeAdapter.cs` provides the same internal
`Nayeon.ByokC1.P265Development` types **instead of** P265, never alongside P265.
It requires DEBUG and `C1_P286_ASYNC_PIPE_REVIEW_ONLY`, explicitly rejects RELEASE
even with DEBUG, and retains the original P265 opt-in. It adds no Main, production
composition, credential effect adapter or service installation path.

The actual caller chain remains P284 -> P282/P271 -> P270/P269/P268/P267 -> the
same P265Development type identities, now supplied by P286 in the review build.
Connect, every partial header/body/delivery read, and the denial reply write all
use one completion helper. Other original entrypoints still compile against
their frozen source unless the review compilation explicitly substitutes P286.

Each Begin operation receives a private completion callback. The serving thread
waits on a managed monitor with the original total deadline. It never obtains or
disposes the pending operation's event. Callback entry establishes that Framework
signaling has finished. The callback obtains the completed event, calls its End
operation exactly once, and disposes that event on success or exception. This
also handles the disposed-stream precheck that can make EndWaitForConnection
throw before closing its event. Double Dispose after a successful End is safe.

Only after End/cleanup finishes does the callback publish its result or captured
exception under the monitor and pulse the waiter. Exceptions are transferred
with ExceptionDispatchInfo; they do not escape on the IO completion thread.
Active waiters rethrow them through the original denial mapping. Timeout cancels
the stream outside the monitor and preserves Timeout; a late callback still owns
End and cleanup, without changing the already returned denial into success.

The ordering is supported by Microsoft's Framework reference source:
[NamedPipeServerStream callback and EndWaitForConnection](https://github.com/microsoft/referencesource/blob/main/System.Core/System/IO/Pipes/Pipe.cs)
signals before invoking the user callback; its End prechecks can reject a closed
stream before event cleanup.
[PipeStream read/write completion and End operations](https://github.com/microsoft/referencesource/blob/main/System.Core/System/IO/Pipes/PipeStream.cs)
use the same signal-before-user-callback ordering, with End responsible for
overlapped cleanup. This is a Framework-specific review design, not a universal
claim about arbitrary APM implementations.

Resource bound: one operation is outstanding per serving adapter. A timed-out
adapter is permanently closed and cannot enqueue another operation. No worker,
registered wait, polling loop, finalizer-only event workaround, global pending
list or retained handle cache is introduced. Completed/cancelled callbacks close
events deterministically; native read/write overlapped cleanup remains in End.
An OS that never delivers cancellation completion remains outside an in-process
guarantee; the disposable process watchdog and runner teardown bound that case.
No unbounded cleanup wait is added to ServeOnce.

Explicit diff review (`git diff --no-index`): only four regions differ after LF
normalization: the three-line P286 guard; Wait/ReadExact and the new helper;
connect Begin/wait/End ownership; write Begin/wait/End ownership. Everything
outside those regions compares exactly, with a frame-length mutation canary
confirming rejection. Identity capture/revert, SID/DACL checks, frame parsing,
denial bytes, replay/capacity, timeout limits, denial/evidence fields, public
visibility and Dispose remain text-identical. Original SHA256:
`CC4065A40E8F7C8DD296EE913533E5AA611EDD2BBBE0D830DA8196A74A440636`.
Successor SHA256:
`15D05B5F577DFD25BDD0551CE37480D10C62FFC7BC034784E781E242B72A0AF9`.

## Prepared regression boundary

Exactly five additions are permitted: this document, the successor, the focused
C# test, its hosted manifest, and the P286 workflow. All 1,152 inherited Git tree
entries and raw disk blobs must match P285. There is no legacy test migration,
waiver, skipped assertion, P270/P283 rebuild or inherited workflow modification.

The focused tests pin frozen P265 bytes, prove its three premature caller-owned
event scopes exist, compare all non-async source, and reject a semantic tamper.
Managed fakes deterministically model the original disposed-event Set failure,
late callbacks after deadline, synchronous completion before waiting, successful
and failing End, event closure on disposed/IO failures, 256 completed lifetimes,
and a stalled End that must not publish early or lose its event on timeout.
These tests are compiled locally and execute only in the hosted workflow.

The workflow admits only a same-repository DRAFT pull_request, exact P285 base
branch/SHA above and exact P286 head branch. No `fork == false` condition,
pull_request_target, secret, write permission or mutable action reference is used.
Checkout uses immutable `11bd71901bbe5b1630ceea73d27597364c9af683`, the PR head SHA,
full history and no persisted credentials. Six independent Windows-2022 jobs
cover x64/x86 times trials 1/2/3, without fail-fast or retries. Every job checks
the fixed candidate SHA, bounded linear ancestry, exact five-path additive delta,
unchanged inherited tree/disk and all candidate disk hashes before/after.

AST literal comparison confirms P285's exact 17-source harness list in order
with only P286 replacing P265, its ten defines retained plus the P286 opt-in,
and unchanged P285 host source/defines. All original P267/P268/P269/P270/P271/
P282/P284 sources and the P284 128-case assertions remain intact. No P283 source
is added to this hosted durable harness.

The unchanged P285 host creates/checks/cleans exactly 129 disposable protected
current-user roots per trial and validates the existing fixed synthetic candidate
identities. It validates the child executable SHA before launch and the exact
128 ordered PASS lines, assertion aggregate, architecture and HOLD line. Native
child watchdog: 145 seconds; orchestration host watchdog: 190 seconds; focused
fake watchdog: 30 seconds; outer job: 15 minutes. Known-root cleanup stays wholly
inside the unchanged host. Failed termination requires disposable runner teardown;
no external recursive root deletion is added. Any RED remains RED. Sanitized
text receipts retain raw compiler, native child and host exits plus the bounded
exception type/six stack methods. Artifact paths are an explicit text allowlist;
no binary is uploaded. P285 build/evidence directory names are retained because
the frozen host requires them; independent jobs isolate every trial.

## Actual local evidence and remaining gates

Direct Framework64/Framework v4.0.30319 csc only, `/warn:4 /warnaserror+`:
eight positive builds returned raw exit 0 (P284 substituted harness, P285 host,
P286 focused test and original P265 test source for both architectures).
Twenty-six negative harness builds returned raw exit 1, exact CS1029 and no EXE:
ALL, RELEASE with DEBUG, missing DEBUG, and each inherited/P286 opt-in omitted.
Missing P286 and release/debug guards are checked explicitly. No generated EXE,
manifest, PowerShell policy bypass or native pipe test ran locally.

Initial command-error evidence:
`C:\Users\krist\AppData\Local\Temp\nayeon-p286-compile-cdbeeecba22a4b0d94382dee8f3ec142`.
Successful compile/negative evidence (before the final deterministic original-race
model was added to the focused test):
`C:\Users\krist\AppData\Local\Temp\nayeon-p286-compile-fd76a3a2d8724be88aa54b52a7783901`.
`raw-exits.txt` SHA256:
`F7C3A9C79A869C55663E652E4B4815F130E63BF4FF22F0143806136A25F2692D`.
Final focused recompilation (two raw exits 0) and eight unchanged P285 host-guard
negatives (raw exits 1, exact CS1029, no EXE) are retained in:
`C:\Users\krist\AppData\Local\Temp\nayeon-p286-final-review-9ac21c155d054291b8a80ca5376ff9a2`.
Final `raw-exits.txt` SHA256:
`87FD27F15EF025E5347C0D2508318BB048C72A290F6E50AA5395298F027350E4`.
Final `binaries.sha256` SHA256:
`6C40F325E8BFCAA508170E72C28CD90E5BA1C15D3E6396D4A3EB5D2DC1C1BD27`.
Final focused binary hashes (not executed or uploaded): x64
`46677BEC765ED045D6C3E1F3739075666ED7C723F53C2AD95D187C0C09F6B212`, x86
`72C1CA9256489094BBB89329D6265BFC80A8F3EEFA93AA61FD1FD1548EB734D7`.
The unchanged successor's P284 harness binary hashes from the main compilation:
x64 `54F72224E8CB1149D6EC323B542E08F9A77D0DCD9711AC59EE97195AB26F3C10`,
x86 `614895FDFF68CF2E73098301C486F1949298DDD498016C9B2319A3CB13CCB1A1`.
Earlier binaries/logs remain historical evidence, not final-source runtime
acceptance. Total local invocations: ten positive exits 0 (including focused
recompilation), 34 expected negative exits 1, and one preserved tooling RED.

The inherited P265 test compilation establishes source compatibility only. Its
original DLL IL audit has a frozen call allowlist without Monitor, Func or
ExceptionDispatchInfo, so that original audit is not claimed to pass on a P286
DLL. It remains unchanged for the original P265 assembly; no old runtime result
or waiver is asserted. P286 source/ownership tests and the unchanged P284 hosted
harness provide the new review boundary, still awaiting independent approval.

PowerShell hosted manifest AST parses with zero errors; the exact source/define
substitution and bounded normalized source-diff/canary checks passed as local
static checks. Authoritative Python path access is denied in this sandbox; no
Python installation, package, network workaround, unittest discovery or compileall
is claimed. No runtime/full-product PASS is inferred from compilation.

Final local custody verified **1,152/1,152 inherited raw disk blobs** against
HEAD, zero tracked/index changes, and exactly the five authorized untracked
additions. `git diff --check` and explicit added-file whitespace checks passed.
Final manifest AST errors: zero. The final review directory also contains
`custody-static.txt` SHA256
`AB0C904C486358A7FED8BB825D78374352379C70B63A24EA5C13F804EFDDDA3E`
and `p265-p286.diff.txt` SHA256
`050F2274DD6B52833D573FA30588678353306FCDE4D2202683C8191C41DD398C`.
`source-sha256.txt` records all five final files (including this document);
it is regenerated after the final documentation write.

Independent Nayeon source/security review and all six hosted runtime trials remain
OPEN. Their candidate SHA, raw native exits, 128-case aggregates, cleanup and text
receipt hashes must be reviewed before defect closure. Scheduling/publication is
not performed here: user explicitly prohibited commit, push and PR creation.
Approvals **0/7**, full regressions **0/3**, P96 original **HIGH OPEN**,
P76/P211/P216 **unwaived**. No qualified SEC03/04 or real-credential signoff.
Workbook/dashboard deferred. Production and real keys **HOLD**.
