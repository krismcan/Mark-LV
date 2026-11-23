# P310 desktop synthetic no-key request — PRODUCTION HOLD

2026-11-23. Sole source writer: Codex. Worktree:
`D:\Nayeon\CODEX_P310_DESKTOP_REQUEST_20261123`. Initial Git inspection found
clean branch `byok-c1-p310-desktop-synthetic-request-20261123` at exact P309
parent `adff32e2978c7dd21fb3c10f9a8805e555d5c41f`, with no tag at HEAD.
Git is authoritative. AGENTS.md, the mandatory failure gate, P308 observer/UI
and tests, and P309 ingress source/tests/review were inspected. The existing
`.codex/CURRENT_STATE.md` describes older Phase 10.2 work and is stale for this
checkout; the explicitly authorized five-path scope leaves it unchanged.

**Qualified approvals 0/7. Full product regressions 0/3. REAL-KEY NO-GO.
PRODUCTION HOLD.** This is an uncommitted, unmerged draft source candidate for
independent CTO review, not a sealed milestone or a published GitHub draft PR.
No staging, commit, tag, push, merge, service installation, ACL change, admin
action, network access, credential access or workbook/dashboard update occurred.

## Implemented architecture and security boundary

`NativeSyntheticRequester` has no constructor effects or arguments and exposes
only `request(self)`. Its enum contains exactly `UNAVAILABLE` and
`UNTRUSTED_HOLD`. The private endpoint is fixed to
`\\.\pipe\NayeonV1ByokCustody.SyntheticDenied.v1`, matching the actual P309
C# `SyntheticIngressServer` endpoint. This is separate from P308 status IPC.
There is no endpoint, operation, payload, key, provider, target or credential
input, and no native credential import. Import/construction does not open IPC.
Standard-library `_winapi` is imported inside explicit `request()` only after
the Windows platform check, as in P308. The P275 inventory is unchanged.

Each explicit request draws eight bytes from `os.urandom`, interprets a
little-endian unsigned 64-bit ID, and packs exactly
`struct.pack('<4sQB', b'C1T1', request_id, 1)`. Zero or unusable randomness fails
closed without opening a pipe; there is no fixed-ID fallback or retry. Only
synthetic Add (byte 1) is sent. UI Save/Replace/Delete selection and key entry
are never consulted. The ID is transport metadata, not authorization or a
secret, and is not logged or persisted by this requester.

The one local `CreateFile` uses read/write access, OPEN_EXISTING, no sharing
or inheritance, `FILE_FLAG_OVERLAPPED | SECURITY_SQOS_PRESENT` with
`SECURITY_ANONYMOUS` (zero). Anonymous SQOS prevents server impersonation of
the client; it does not authenticate the server. The handle uses message read
mode without PIPE_NOWAIT. There is no wait-for-server, reconnect or retry.
One overlapped WriteFile must transfer exactly 13 bytes. One overlapped
ReadFile uses a buffer one byte larger than the expected reply and requires
both the exact transferred length and exact bytes
`C1|DENIED|HOLD|NO_CREDENTIALS`. Short/empty/oversized/malformed data,
ERROR_MORE_DATA, unexpected completion status and failed waits refuse.
PeekNamedPipe snapshots before writing and after reading refuse unsolicited
or already queued extra data. They cannot attest peer identity or exclude
later traffic; a perfect counterfeit response still yields only UNTRUSTED_HOLD.
No result means READY, allowed, consent, authentication or credential authority.

A single monotonic 0.75-second budget covers randomness, opening, mode/peek,
write and read completion, and result admission. Pending I/O waits on its own
event using the remaining budget rounded down to milliseconds. Immediate I/O
also requires GetOverlappedResult success. Completion/deadline races and a
close consuming the deadline refuse. Pending operations are cancelled and
drained with GetOverlappedResult(True) before releasing OS-owned buffers or
closing the pipe. Cancellation/drain/close exceptions fail closed; the
overlapped object owns its event. This is not hard preemption of Windows calls:
a pathological kernel call or safe cancellation drain can outlive the request
budget. The UI has a separate deadline and never joins a worker on Tk.

The new independent button is **Test synthetic service denial (no key)**,
with one adjacent HOLD label. Only this button starts its daemon worker.
The button permanently disables on its first attempt, even after success,
unavailable, worker-start failure, timeout or late completion. This respects
P309's one connection/request per service lifetime without automatic retries.
The worker captures a per-request queue and never touches Tk, the controller,
review, confirmation or key entry. Tk polls every 25 ms against its own
1.5-second monotonic budget; at expiry it displays UNAVAILABLE/HOLD, drops the
queue and stops polling. Late results cannot revise the label or start work.
Closing cancels both the new pending callback and the unchanged P308 callback,
drops the synthetic queue, and makes late results inert. The UI budget requires
a responsive Tk event loop; it does not promise scheduler preemption.

Existing P308 observation methods, Refresh, mutation handlers, default
presence-only composition and disabled credential controls retain their
behavior. Normal startup, Refresh, Observe, review, approval and close never
start a synthetic request. Presentation of a denial grants nothing in
Permission -> Policy -> Confirmation -> Execution -> Verification.

The P309 service-only owner-SID ACL remains unchanged. An ordinary desktop
token may be denied access; UNAVAILABLE is expected. No actual product pipe
was contacted in this task. Disposable Python peers test transport semantics,
not the C# service, its DACL, SCM lifecycle, peer qualification or consent.
User-reported P309 dedicated hosted x86/x64 Debug/Release **4/4 PASS** is
inherited focused development evidence, not a new P310 result or approval.

## Open Failures & Prior-Issues Review

The bounded dependency audit covered P308 button/poll/close isolation, P309
13-byte framing and one-connection lifetime, default controller/entry routes,
P275's frozen native-effect boundary, and imported test fixtures. No older
credential authority was enabled. Corrective synthetic source work is within
the user's explicit request; forward qualification, production and security
seals remain HOLD. No low-risk deferral or finding downgrade is claimed.

| Issue / source / date | Severity, root cause and affected boundary | Containment / repair and reproduced evidence | Independent review / disposition |
| --- | --- | --- | --- |
| P96 inherited incident / 2026-11-23 task | HIGH revocation/effect race; original cross-entrypoint closure evidence not established here | No credential effects, lifecycle repair or closure claim; original incident/repair evidence still required across callers/processes/restarts | Pending; HOLD |
| P292 inherited incident / 2026-11-23 task | x86 SCM UNKNOWN; root cause remains unknown | No SCM action or teardown change. Optional x86 Python IPC tests cannot qualify SCM | Pending; HOLD |
| P308 corrective review A / inherited review | Material prior native-loader addition conflicted with P275 ownership | New requester mirrors lazy standard-library `_winapi`; no ctypes/native credential loader. Frozen inventory/source pins and AST guards passed in the independent focused host suites; P275 inventory exit 0, SOURCE_NATIVE_EFFECTS NONE | Qualified review pending; HOLD |
| P308 corrective review B / inherited review | Material PIPE_NOWAIT write-success assumption did not prove transfer | Real overlapped write/read, exact lengths, shared deadline and cancellation/drain. Mock faults and ten genuine disposable OS cases prepared | All ten genuine disposable OS cases independently passed in the latest 45/45 host run; focused evidence only; HOLD |
| P308 corrective review C / inherited review | Material missing queue timeout permitted indefinite polling and stalled-worker accumulation | P310 uses independent deadline, per-request queue, permanent first-attempt latch and inert late/closed results. Ten fake-Tk tests prepared | Ten fake-Tk tests passed in the independent 45/45 host run; Codex sandbox runtime blocked; HOLD |
| P309 one-connection service lifetime / source audit | Compatibility constraint; a retry cannot establish additional service authority | UI never retries; requester opens only once. Observe remains separate. No C# or ACL changes | Final source review pending; HOLD |
| Local Python access / 2026-11-23 | Environment blocker; authoritative installed executable is access-denied in sandbox | Get-Item denied access; bounded Process.Start version probe independently returned Access is denied before Python started. No runtime workaround or alternate Python used | Codex sandbox runtime blocked; independent host evidence below; HOLD |

## Test source and evidence limits

The new module declares **45 test methods**, all independently passed on the Windows host: 20 mocked requester
tests, ten fake-Tk tests, ten real Windows disposable-pipe tests and five
AST/frozen-boundary tests. Mock cases cover lazy import, off-Windows refusal,
exact frame/SQOS, immediate/pending I/O, malformed/short/oversized frames,
extra/unsolicited data, start/completion/wait errors, every transport exception
stage, RNG failure, zero ID, deadline races including close, cancellation,
drain, and exact Add IDs across separate draws. UI tests cover click isolation,
no controller/key/confirmation reads, permanent disable on every outcome,
Observe/Refresh isolation, timeout, worker-start failure, missing/stale results,
still-alive workers and close with both polls pending.

OS tests use `sys.executable -B -m tests.test_byok_c1_p310_native_synthetic_request
--pipe-child ...` in bounded ten-second child processes. Each endpoint is
`\\.\pipe\P310.Disposable.` plus a canonical nonzero UUID; child validation
rejects product, remote, zero and noncanonical endpoints before any open.
Only the child's private endpoint constant is patched. A genuine local,
first-instance message pipe under the test user's token must receive one
13-byte `C1T1`/positive-ID/Add message. Cases are exact denial, counterfeit
exact denial, malformed, truncated, oversized, extra message, absent endpoint,
delayed response, stalled read and disconnect. The delayed response waits
0.15 seconds and remains untrusted; the stalled case leaves a real pending read
and requires at least 0.65 seconds elapsed. Client completion/cleanup must
finish within two seconds. Parent timeout kills/waits for a stuck child and
fails. Extra-message scheduling waits until both actual OS writes complete
before allowing the client read, making the Peek rejection deterministic.
These tests neither create nor connect to the product endpoint. Off-Windows
skips are explicit and do not count as Windows evidence.

AST guards constrain requester imports, lazy native import, public interface,
native calls, frame/randomness/deadline constants and lack of loops; negative
tampering must fail. Frozen LF-normalized SHA-256 witnesses bind P275 inventory
and tests, P308 observer and P309 ingress. Existing UI methods are compared to
the exact P309 parent's AST; only synthetic initialization/close additions are
excluded from that comparison. Guards supplement review; they are not a
sandbox against a hostile same-user Python process.

The new Windows-2022 workflow requires an exact same-repo DRAFT PR, base ref
`byok-c1-p309-native-synthetic-request-ingress-20261123`, base SHA
`adff32e2978c7dd21fb3c10f9a8805e555d5c41f`, and exact P310 head ref. Checkout
uses the PR head SHA. It checks ancestry, exactly four additions plus the UI
modification, clean index/worktree before and after, and input SHA-256
witnesses. It uses installed Python 3.12 x64 plus x86 when available; absent
x86 is explicitly NOT_TESTED, and absent x64 fails. There is no runtime install
or download. Each Python run is bounded to 75 seconds with captured stdout,
stderr, exit and timeout diagnostics; the job maximum is eight minutes.
It runs the unchanged P275 inventory, P310 tests, inherited P308 tests,
local-user-scope/P258/P275 tests and `compileall -q nayeon tests` with caches
outside the checkout. Unit suites globally block missed real credential DLL
loader calls while their own fakes remain scoped. No hosted job was triggered.

Precise local evidence on 2026-11-23:

- Initial branch/HEAD matched the requested clean P309 parent; index empty.
- Authoritative executable:
  `C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`.
  A no-window Process.Start probe, limited to ten seconds, attempted
  `-B -c "import sys; print(sys.version); assert sys.version_info[:2] == (3, 12)"`.
  It failed before launch: `Exception calling "Start" with "1" argument(s):
  "Access is denied"`; orchestration exit 1. No test process started.
- **Codex sandbox runtime tests executed: 0.** The sandbox access denial above
  remains true; no alternate executable or workaround was used.
- **Independent host evidence (Nayeon, outside the Codex sandbox):** installed
  Windows Python 3.12.10 ran the earlier P310 source snapshot (historical encoding diagnostic): **43/44 PASS,
  one FAIL**. All nine then-current genuine disposable Win32 pipe child cases
  passed: exact, counterfeit, extra, malformed, oversize, partial, absent,
  stalled and stop. No real keys or production pipe were used.
- The sole failure was
  `SourceBoundaryTests.test_existing_ui_methods_frozen_ast_and_only_button_calls_new_handler`:
  the Git-baseline subprocess used Windows default text decoding, corrupting
  the genuine UTF-8 middle dot and failing frozen AST equality. This test
  harness encoding error is corrected with `encoding="utf-8", errors="strict"`;
  the full AST equality assertion is preserved. It was not a product-behavior
  failure or an assertion/expectation defect.
- **Verified independent host P310 result after the strict UTF-8 repair:
  45/45 PASS in 3.142 seconds, exit 0** (`Ran 45 tests in 3.142s OK`).
  Direct Desktop Commander used installed Windows Python 3.12.10 with `-B`
  and `PYTHONDONTWRITEBYTECODE=1`. Requester/UI/test source hashes were
  unchanged before versus after execution. All ten genuine disposable random
  Windows pipe cases passed: absent, delayed, exact, extra, malformed,
  oversize, partial, stop, stalled and counterfeit. No production pipe, SCM
  or real keys were contacted. This is focused local evidence, not hosted
  acceptance, a full product regression or qualified approval.
- The unchanged inherited P308/local-user-scope/P258/P275 suite independently
  passed **111/111**, 3.407 seconds, exit 0. The frozen P275 native-effect
  inventory independently exited 0 and reported `SOURCE_NATIVE_EFFECTS NONE`,
  `REAL_KEYS NO-GO`, `PRODUCTION HOLD`. These are focused host results, not
  full product regressions or qualified approvals.
- Workflow PowerShell AST parsing passed **2/2 blocks**. This checks embedded
  PowerShell syntax, not YAML execution, Python execution or hosted CI behavior.
- Final static checks PASS: exact five-path scope, empty index, unchanged
  branch/parent, `git diff --check`, valid UTF-8 without BOM or trailing
  whitespace, and final newlines in all five paths. P275 inventory/tests, P308
  observer/tests, P309 ingress, AGENTS.md and `.codex/CURRENT_STATE.md` match
  their parent Git blobs. These checks provide no runtime or approval credit.
- An initial encoding-check command falsely reported a BOM because .NET's
  culture-sensitive StartsWith comparison treated U+FEFF as ignorable. Direct
  byte checks confirmed there was no BOM; the corrected byte-based check
  passed all five paths. No source rewrite was needed for that false positive.

No full `unittest` discovery or full-product regression was run. Independent
qualified source/security reviews remain required; any failure is a STOP requiring diagnosis, repair and fresh
review. All **0/7 approvals, 0/3 full product regressions, P96 HIGH, P292 x86 SCM
UNKNOWN, REAL-KEY NO-GO and PRODUCTION HOLD** remain unchanged.

## Next bounded restart point

Review this exact five-path draft and retain the independently verified focused
host results without upgrading their assurance. Hosted acceptance, qualified
reviews and all three full product regressions remain open. The next architecture work is
qualified peer authentication and consent/credential service integration,
under separate approval. No endpoint reply supplies that qualification.
