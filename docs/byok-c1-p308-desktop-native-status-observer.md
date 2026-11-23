# P308 corrective candidate: desktop native status observation — HOLD

2026-11-23. Codex is the sole source writer in
`D:\Nayeon\CODEX_P308_DESKTOP_STATUS_20261123`. Branch:
`byok-c1-p308-desktop-native-status-observer-20261123`. Git HEAD matches the
required baseline `ed3ff04649573dfb84ffb70782aa8096394a308e`; the first attempt's
uncommitted candidate was preserved and corrected in place. This document is
the fifth authorized path. `.codex/CURRENT_STATE.md` describes older Phase 10.2
work and does not match this worktree's current task; it remains unchanged.

This is an uncommitted corrective source candidate, not a verified milestone.
Qualified approvals **0/7**, full regressions **0/3**, **REAL-KEY NO-GO**.
P96 HIGH and P292 x86 teardown with unknown root cause remain security HOLDs.
No staging, commit, tag, merge, push, publication or workbook update is included.

## Corrected transport and authority boundary

Only an explicit Observe button starts one worker. Import, window construction,
normal startup, Refresh and close do not observe a pipe. Existing Refresh still
uses the presence-only controller; observation has no controller, submission,
key-inspection, mutation, provider or SCM route. Existing disabled mutation
controls and the explicit offline controller contract remain unchanged.

The product observer imports standard-library `_winapi` inside `observe` only
after its Windows check. There is no new dependency or native credential API.
The frozen P275 inventory and its approved native-loader owners are unchanged;
the observer contains no `ctypes` import or use. This is a separately reviewed
nonsecret pipe transport, not an exemption from the P275 credential-effect guard.

The endpoint remains the constant local
`\\.\pipe\NayeonV1ByokCustody.Status.v1`, with no public endpoint or payload
parameter. One CreateFile attempt uses `FILE_FLAG_OVERLAPPED | 0x00100000`;
`0x00100000` is SECURITY_SQOS_PRESENT and SECURITY_ANONYMOUS is zero. The fixed
access is read/write, OPEN_EXISTING, no inherited handle. Anonymous SQOS prevents
the server impersonating the interactive client; it does not attest the server.
See Microsoft's [CreateFile security flags](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

The client sets PIPE_READMODE_MESSAGE alone. It never selects PIPE_NOWAIT.
Both WriteFile and ReadFile actually use overlapped objects. Pending operations
wait on their own events with the remaining shared 0.75-second request budget.
Immediate completions still require a successful overlapped result. A short
write, unexpected start/completion status, failed wait, timeout, or deadline race
refuses. Exactly four bytes `C1S1` must be written; the sole accepted reply is
`C1|NOT_AUTHORIZED|HOLD|NO_CREDENTIALS`. The read buffer has one extra byte;
ERROR_MORE_DATA, partial, empty, oversized and malformed replies refuse without
a continuation read. There are no transport loops, reconnects or retries.

This replaces a material Windows semantic error: PIPE_NOWAIT message writes can
return success without transferring bytes. Overlapped I/O instead requires an
overlapped handle and a real operation/event. References:
[Microsoft pipe modes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-type-read-and-wait-modes),
[Microsoft overlapped pipe I/O](https://learn.microsoft.com/en-us/windows/win32/ipc/synchronous-and-overlapped-input-and-output).

Zero-size PeekNamedPipe checks reject unsolicited data before the query and
already queued extra data after the reply. These snapshots cannot exclude a
later malicious frame or identify the peer. Even an unrelated server returning
the exact reply yields only **UNTRUSTED_HOLD**. All failures yield **UNAVAILABLE**;
there is no trusted, ready, allowed or grant result. Endpoint bytes never bypass
Permission -> Policy -> Confirmation -> Execution -> Verification.

On failure with an outstanding overlapped object, cancellation is attempted and
GetOverlappedResult(True) drains it before closing the pipe or releasing its
buffer. A cancellation/completion race never promotes the result. Cleanup errors
remain unavailable. `_winapi` owns and releases overlapped event handles; the
observer closes the pipe once. API shapes and ownership were checked against
[CPython 3.12 `_winapi` source](https://github.com/python/cpython/blob/3.12/Modules/_winapi.c).

Draining OS-owned memory safely is distinct from the bounded request event
waits: a pathological kernel call or cancellation drain can stall the worker.
The source does not claim hard preemption of a Windows call. The UI therefore
has an independent monotonic 1.5-second deadline, enforced at its next 25-ms Tk
poll. Missing or late results display unavailable and polling stops. If that
worker is still alive, observation is permanently disabled for that window,
including after late completion. A still-alive worker with an already posted
result also latches disabled; it cannot overlap a replacement. Each request has
its own queue. Workers never touch Tk, and stale queues cannot feed later probes.
Closing cancels the pending callback and makes late results inert. Tk scheduling
itself requires a responsive UI event loop; no synchronous worker join runs there.

The unchanged P305 server retains a successful reply until owner disposal and
accepts only one connection/query per lifetime. An interactive desktop user is
normally excluded by its service-only ACL. This candidate adds no service
installation, ACL change, restart policy, credential access or peer attestation.

## Open Failures & Prior-Issues Review

The mandatory failure gate was read. The relevant dependency review covered the
actual observer, UI button/poll/close routes, default presence-only composition,
frozen P275 inventory/tests and retained P305 server lifetime. Older or alternate
credential paths were not exercised against live credentials. Corrective source
work is authorized; forward product progression and a security seal remain HOLD.

| Issue / source / date | Severity and root cause | Impact and corrective source | Evidence, independent review and disposition |
| --- | --- | --- | --- |
| A: corrective restart review, 2026-11-23 | Material: new product native-loader import violates frozen P275 owner inventory | Observer now imports `_winapi` only inside explicit Windows observation; P275 stays byte-identical | Prior candidate import reproduced by source inspection. New source-boundary and inherited inventory tests prepared; no runtime or independent final-source result. HOLD pending verification |
| B: corrective restart review and Microsoft semantics, 2026-11-23 | Material: synchronous PIPE_NOWAIT mocks did not prove real message transfer | Real overlapped write/read, exact transferred count, message framing, request deadline and cancellation/drain; no grant result | Seven real disposable OS test cases plus immediate/pending, short-write, truncation, extra-frame, timeout and race injection prepared. Not executed here. HOLD pending native evidence |
| C: corrective restart review, 2026-11-23 | Material: empty worker queue previously rescheduled forever; further attempts could accumulate stalled threads | UI deadline, permanent alive-worker latch, per-request queue and inert close/late result | Ten UI cases include timeout, late response, missing result, duplicate clicks and close. Not executed here; independent review pending. HOLD |
| P96, inherited user security HOLD | HIGH; original root cause and cross-entrypoint closure not established here | No credential-owner changes or closure claim | Original incident evidence, repairs and qualified review still required. HOLD |
| P292, inherited user security HOLD | x86 teardown root cause unknown; not downgraded | No teardown repair or qualification claim | Optional x86 hosted Python checks cannot close this finding. HOLD |
| Python access in this sandbox, 2026-11-23 | Validation environment blocker: authoritative executable cannot be invoked | No installation, copied runtime, network workaround or host execution was attempted | PowerShell reports the exact host path is not recognized. Runtime validation delegated to independent host orchestration. HOLD |

## Tests, CI and evidence limits

The new test module declares **34 tests**: 15 mocked transport negatives and
contract cases, 10 UI lifecycle cases, seven real Windows-pipe integration cases,
and two source-boundary cases. This is a source inventory, **not 34 passes**.
Unchanged affected modules declare **77 tests**: local-user scope 36, P258 23,
P275 18. The combined focused/affected source inventory is **111 test methods**;
subtests and the standalone P275 inventory are not additional method counts.

Each real OS case creates a UUID endpoint under `P308.Disposable.` in a child
process under the test user's token. Only the private endpoint constant is
patched for that child. The server uses actual `_winapi.CreateNamedPipe`, one
local first-instance message pipe, actual overlapped connection/read/write and
asserts it received exactly four bytes. Cases cover exact fixed denial, malformed,
partial, oversized, absent server, stalled real read and server stop. The exact
case intentionally uses an untrusted test peer and can only return UNTRUSTED_HOLD.
The server has bounded waits and cleanup; each parent gives its child ten seconds
and kills/waits on timeout. No test creates a server at the product name. The
stalled case must spend at least 0.65 seconds in the real client exchange and
return unavailable; normal client completion/cleanup must finish within two
seconds. A blocked drain is a failing child deadline, never a passed test.
OS cases are explicitly skipped off Windows; that is not Windows evidence.

The new Windows-2022 workflow retains the inherited UI/P258/P275 suites and runs
the unchanged P275 product inventory explicitly. It uses already installed
Python 3.12 x64 and additionally x86 when present, with no downloads or packages.
Absent x86 is reported as NOT_TESTED. Exact draft-PR head/base/branch/same-repo,
five-path diff, clean index/worktree, ancestry and before/after source SHA/hash
checks remain in place. The frozen inventory script is included in hash witnesses.
Each Python process has a 60-second deadline; the job has six minutes. This
workflow was edited locally, not triggered or published by this task.

Local results: **0 runtime tests executed**. The authoritative
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe` command was
unavailable in the sandbox. Focused P275 execution, Python parsing/compileall,
34 new tests, 77 inherited tests, real OS behavior and full discovery remain
unverified. Static source review and Git whitespace/scope checks are not runtime
substitutes. Known test risk is unexecuted platform behavior and timing under
Windows scheduling; no assertion was weakened to obtain a pass. BOMs introduced
by PowerShell file writing were removed before final static review so the AST
source test can read plain UTF-8. Final static checks passed: exact five-path
scope, unchanged baseline HEAD, empty index, frozen P275 script/test equal to
HEAD, `git diff --check`, plain UTF-8 and no trailing whitespace in all five
paths. Both workflow PowerShell run blocks parsed successfully with the local
PowerShell parser; this is not YAML execution or hosted CI evidence.

Independent host orchestration should first run, with that installed Python and
bytecode disabled: `scripts/p275_product_effect_entrypoint_inventory.py`, then
`-m unittest -v tests.test_byok_c1_p308_native_status_observer`, then
`-m unittest -v tests.test_local_user_scope_byok tests.test_byok_c1_p258_legacy_effect_containment tests.test_byok_c1_p275_native_effect_retirement`.
Preserve source hashes and test totals. Compile with an external temporary
PYTHONPYCACHEPREFIX, and perform the required broader regressions only under the
existing gate/orchestration. No full-regression credit or qualified approval is
claimed. A failing frozen P275 test or OS child is a STOP, not grounds to edit the
guard. P96/P292, approvals 0/7, full regressions 0/3 and REAL-KEY NO-GO remain HOLD.
