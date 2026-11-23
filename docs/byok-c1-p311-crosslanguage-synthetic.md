# P311 real Python to real C# owner denial — PRODUCTION RELEASE HOLD

2026-11-23. Codex is the sole source writer. This is an unsealed, unmerged
draft candidate in `D:\Nayeon\CODEX_P311_CROSSLANGUAGE_20261123`, branch
`byok-c1-p311-crosslanguage-synthetic-20261123`, based on exact P310
`97e1f57d0e5dbd1f96228615d13598a3de775409`. Initial Git worktree/index were
clean; no tag pointed at HEAD. `.codex/CURRENT_STATE.md` describes older
Phase 10.2 work and is stale for this checkout. Git is authoritative; the
explicit four-addition scope leaves the context file unchanged.

**Qualified independent production approvals 0/7; full product regressions
0/3; P96 HIGH revocation/effect race; P292 x86 SCM cleanup UNKNOWN;
REAL-KEY NO-GO; PRODUCTION RELEASE HOLD.** No test output supplies production
authorization. No staging, commit, tag, push or merge is included.

## Bounded implementation

Exactly four new files: this review, the P311 workflow, the Python unittest
module and `tests/p311_crosslanguage/P311CrossLanguageHarness.cs`. All product
code, P309/P310 implementations/tests/workflows and P275 inventory remain
unchanged. There is no service clone, alternative owner or replacement ingress.

The standalone harness is compiled as `P309.ProductService.Tests.exe`, using
the existing friend declaration in the actual product assembly. It constructs
the real internal `SyntheticTransactionOwner` and
`SyntheticIngressServer(owner, testEndpoint)`. Before owner construction or OS
access, it requires precisely a canonical nonzero lower-case UUID N under
`P309.Disposable.` and a closed expectation enum spelling. Product names,
remote paths, zero UUIDs, arbitrary paths and other arguments are rejected.
It never invokes the product entrypoint or SCM lifecycle.

The harness emits one `READY` synchronization marker only after actual OS pipe
creation, with an active owner and pending accept. This marker is test process
synchronization, never a client authorization result. Request completion must
arrive within four seconds. Denial requires `Refused == false` and
`ActiveDenied`; malformed input requires `Refused == true` and `Faulted`.
The successful buffered denial remains alive while the client reads it. A
bounded stdin `DONE` handshake permits disposal only after client completion.
Final bounded output is `DENIED`, `REFUSED` or `IDLE_DISPOSED`; errors exit
nonzero without exception details. Idle testing waits 3.6 seconds, requires
pending accept/ActiveDenied/epoch 1, then disposes and verifies Stopped.

The Python parent accepts only an absolute canonical existing harness path
under resolved `RUNNER_TEMP`, with the exact friend assembly filename.
Each scenario creates a fresh UUID endpoint internally. The Python client
also validates the canonical endpoint before native access. No arbitrary
user-selected pipe is accepted. Source guards forbid the product endpoint
family in both new test sources and exercise invalid endpoints before native
imports. The only patch to P310 is test-scoped `patch.object(requester,
"_PIPE", disposable_path)`; its real `NativeSyntheticRequester.request()`
method, frame generation, native I/O and result handling run unchanged.
The exact denial must yield `UNTRUSTED_HOLD`, never READY or authority.

The other clients use test-only `_winapi`, anonymous SQOS, message mode and
overlapped I/O with a two-second shared completion deadline. Cancelled I/O
retains its buffers until drained. Since kernel drain can exceed a software
budget, the parent isolates the client in a disposable Python subprocess and
kills/waits on hangs. Both harness and client share a ten-second scenario
deadline; READY has a three-second bound. Cleanup kills remaining children and
waits up to two seconds per child. Each stdout/stderr stream is continuously
drained with at most 4 KiB retained; diagnostics never echo child bytes on
failure. Expected output and zero exit status are checked exactly.

| Real Windows scenario | Client observation | Actual owner/harness expectation |
| --- | --- | --- |
| Unmodified P310 Add, 13 bytes | UNTRUSTED_HOLD | ActiveDenied, DENIED |
| Typed Replace, 13 bytes | Exact fixed denial | ActiveDenied, DENIED |
| Typed Delete, 13 bytes | Exact fixed denial | ActiveDenied, DENIED |
| Malformed magic, 13 bytes | Closure/zero bytes, no denial | Faulted, REFUSED |
| Zero RequestId, 13 bytes | Closure/zero bytes, no denial | Faulted, REFUSED |
| Invalid operation, 13 bytes | Closure/zero bytes, no denial | Faulted, REFUSED |
| Oversized single 256-byte message | Closure/zero bytes, no denial | Faulted, REFUSED |
| No client for 3.6 seconds | No client I/O | ActiveDenied until safe disposal, Stopped |

The existing protected owner-SID ACL is used unchanged under the ordinary
Windows runner user token. Python and harness share that user SID. This
tests cross-language framing, actual ingress/owner denial and disposal. It
does **not** test Windows SCM/virtual service identity, desktop-to-service
access, qualified client or server authenticity, explicit consent, protected
storage or user keys. No ACL is broadened and no credential API, DPAPI,
provider, product pipe, network or service installation is used.

## Hosted workflow and evidence ledger

The workflow accepts only a GitHub-hosted Windows-2022 same-repository draft
PR from the exact P311 branch onto the exact P310 branch/SHA above. Pinned
checkout uses exact PR head SHA without stored credentials. It requires
exactly four regular-file additions, clean Git before/after and frozen source
comparison against P310. SHA-256 witnesses include all service project inputs,
the P310 requester/UI/tests, P309 tests and P275 inventory/tests.

Separate x64/x86 jobs require installed matching Python 3.12 and installed
MSBuild/C# compilers; absence fails, with no downloads or restores. MSBuild
builds the unchanged .NET Framework 4.8 product in runner temp. The harness
references that actual binary; an adjacent product copy must have identical
SHA-256 for CLR resolution. Only test processes execute. Each Python command
has a 75-second outer limit (the interpreter identity probe has ten seconds).
The P275 inventory is required. Process exits, bounded logs, architecture,
source/product/harness hashes and clean source are checked. Python optimization
is explicitly disabled and verified; no P311 test assertion is suppressed.

| Evidence | Status and limit |
| --- | --- |
| P310 hosted run 45183407736, draft PR #229 open/unmerged | User-reported SUCCESS: Python 3.12 x64+x86, P310 45/45, P308 34/34, inherited 77/77 each (312 executions); P275 PASS. Inherited evidence, not independently fetched or a P311 result |
| Codex local installed C# compiler, x64 and x86 | PASS, compile-only: actual unchanged product sources plus harness, warnings as errors, separate friend assembly reference; neither executable run |
| Local compiler invocation diagnostic | Initial relative forward-slash harness source argument was misparsed by legacy csc (CS1504). Repaired orchestration uses resolved absolute source path, matching workflow; both architectures compiled successfully. No product defect or source waiver |
| Workflow embedded PowerShell AST | Two run blocks parsed successfully locally; this does not prove YAML or hosted execution |
| Final local source boundary | PASS: exactly four untracked additions, inherited tracked files unchanged, empty index, exact P310 HEAD retained; strict UTF-8/no BOM, final newlines, no trailing whitespace and git diff --check passed |
| Authoritative local Python | Access denied at the supplied installed Python path. No alternate interpreter, install, download or access workaround used |
| P311 native runtime / hosted execution | NOT RUN by Codex; eight real scenarios plus two boundary tests prepared, no PASS inferred from compilation |
| Full discovery, compileall, affected regressions and independent source/security review | NOT RUN / pending host orchestration. 0/3 full product regressions; 0/7 independent production approvals |

## Open Failures & Prior-Issues Review

The retrospective was bounded to AGENTS.md, the failure gate, P309/P310
sources/tests/workflows and their latest reviews. Dependency trace:
Python request -> real OS pipe -> P309 parser -> owner.Observe -> typed
SyntheticTransactionRequest -> owner.Deny -> fixed denial -> untrusted Python
result. No action, credential or lower-level effect route is added. There is
no broad historical audit or assertion of cross-process production closure.

| Issue / source / date | Severity and root cause / impacted boundary | Reproduction, containment, tests and repair | Independent review / disposition |
| --- | --- | --- | --- |
| Missing cross-language coverage / task, 2026-11-23 | Functional evidence gap: independent Python and C# tests did not join actual implementations | Eight disposable scenarios prepared using actual product binary; runtime reproduction/results pending | Pending; source work authorized, acceptance HOLD |
| P96 / inherited P309/P310 reviews | HIGH revocation/effect race; original caller/restart closure not established | No repair or reproduction claimed; denial-only metadata has no effect port | No closure, production HOLD |
| P292 / inherited P309/P310 reviews | x86 SCM cleanup UNKNOWN; root cause unresolved | Ordinary-user disposable IPC cannot reproduce or qualify SCM; no SCM action | No downgrade or closure; HOLD |
| P308 loader/PIPE_NOWAIT issues / P310 review | Material effect ownership and transfer-proof failures in earlier routes | Frozen P310 uses lazy _winapi, exact overlapped transfer and bounded completion; P275 inventory retained | Inherited containment only; no new production qualification |
| P310 encoding/timer defects / P310 review and task | Test harness UTF-8 decoding and x86 timer-resolution assumptions | Inherited strict encoding repair and stronger delayed fixture unchanged; user reports latest hosted success | No P311 timing waiver; independent qualification pending |
| Local Python / this session | Environment access denial, not a product failure | Static review and installed C# compile-only; host runtime remains required | Runtime HOLD; no bypass |

Disposition: **GO only for the explicitly authorized four-file disposable test
source preparation. HOLD for runtime acceptance, security seals and production
progression.** Unknown roots and missing security evidence remain open; no
low-risk deferral, finding downgrade or production approval is asserted.

Next step is host execution and independent review of these exact sources.
The next production dependency remains qualified bidirectional peer
authenticity and explicit consent/service-owned protected storage, under a
separate authorization/security gate. Preserve Permission -> Policy ->
Confirmation -> Execution -> Verification. Do not update the main Drive
workbook or dashboard until BYOK C1 is complete. REAL-KEY NO-GO and
PRODUCTION RELEASE HOLD remain in force.
