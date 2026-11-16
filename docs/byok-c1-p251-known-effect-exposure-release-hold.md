# P251 known credential effect exposure and release HOLD

16 November 2026. Source-only diagnostic and unconditional release refusal.
Independent security-owner decisions and production remediation remain pending.

## Intake and scope

Initial tracked, staged and untracked status was clean. Git HEAD was exactly
`e3048ad625b8ebe6e25803ee6e01ca7c4c971877`, on branch
`byok-c1-p251-legacy-effect-release-gate-20261116`, with no tag pointing at HEAD.
The latest commit is P250. `.codex/CURRENT_STATE.md` begins with older 3 November
Phase 10.2 material and does not describe this branch. Git governs this bounded
assignment. The handoff file retains its original bytes.

The three additions are the stdlib-only tool, its effect-free tests and this note.
The author is the sole engineering writer. First independent read-only technical
review returned `P251_REVIEW=GO_DRAFT_ONLY` with three LOW findings. The bounded
remediation below awaits final independent read-only review.
This assignment is a diagnostic increment with production progression on HOLD.

## Exact inspected source evidence

Hashes below are SHA-256 of raw checkout bytes. Line numbers refer to those bytes
decoded as source. Each tool report includes observed and expected hashes,
Python import statements with lines, and the selected call/text evidence.

| Source path | SHA-256 |
| --- | --- |
| `nayeon/desktop_alpha/local_byok_launch_bridge.py` | `1fb8a889c7dcba0a83c1dbc888bd1d7deb219bcff3fc08cadeb246f61b3c71d5` |
| `nayeon/desktop_alpha/local_byok_window.py` | `8dfdfc587886471f312d39aa53bc049179a7ca2d61bc310f84ac142ba5d103e6` |
| `nayeon/brain/local_byok_user_scope.py` | `1971a3f7f90c840fb6c3dc95128ecb6cf2a5e855204d418d99144eb10f3a17b6` |
| `nayeon/secrets/windows_credential.py` | `e6443853300fb2fb4944b8c8bede2ee953719eaf7544d7338056d81491b46125` |
| `tests/p96_native_transaction_negative/PendingCustodyTransaction.cs` | `d8b8e4c6d5ea5e035b58c6ad73dd758c16640167c804ccf3305969b12bdf81ab` |
| `docs/byok-c1-p250-p96-service-owned-ordering-architecture.md` | `def6c23193a9b26ef0046e76e6d296aa75baf2dfaac603827dc0e7820cbd0b6b` |

The source relationships were read before implementation. Their concrete links
are as follows, using the path identities in the table above.

| Source and lines | Observed relationship |
| --- | --- |
| `local_byok_launch_bridge.py` 19, 90–98 | Fixed child module is `nayeon.desktop_alpha.local_byok_window`. Source mode builds `[sys.executable, "-B", "-m", _CHILD_MODULE]` and submits it to `subprocess.Popen` at 98. Frozen mode separately consults its companion gate at 81–87. The diagnostic inventories the source route. |
| `local_byok_window.py` 14–18, 219–270, 295–305 | Imports controller/factory, calls `self._controller.approve` at 243, and constructs the window with `compose_user_scope_local_byok()` at 300. Module main is an additional explicit entry. |
| `local_byok_user_scope.py` 23, 26, 130–199, 205–207 | Imports `WindowsCredentialBackend`, fixes identifier `openai.api_key`, and composes the real backend at 207. Approval calls backend delete at 175 or put at 181 under local review/mutex handling. Metadata presence checks follow. |
| `windows_credential.py` 12–16, 138–140, 161–179 | Namespace prefix is `nayeon-v1/secret/`. Backend put delegates to adapter write at 169, delete to adapter delete at 177. Lazy adapter creation at 140 leads to native setup. Direct backend calls supply an alternate entry without controller review or service-owner admission in these method bodies. |
| `windows_credential.py` 49–66, 102–124 | Adapter construction calls `_load_advapi32` at 59, whose `ctypes.WinDLL` is at 51. Native signatures bind at 63–66. Actual mutation calls are `self._dll.CredWriteW` at 113 and `self._dll.CredDeleteW` at 120. |
| `windows_credential.py` 72–100, 149–159, 181–186 | Read/presence uses `CredReadW` at 74 and releases returned buffers through `CredFree` at 91/100. These remain related confidentiality/native effects requiring future exclusion evidence. |
| `PendingCustodyTransaction.cs` 123–240, especially 203–212 | Historical approval-current and lease-ownership observations precede the separate `state.DeletePending()` at 210 or `state.SaveOrReplace(owned)` at 212. These are interface effects in a separate C# route. No Python-to-P96 call relationship was found in the inspected chain. |
| P250 design 101–129, 199–262, 313–341 | Documents the original race, outstanding SEC decisions, package/OS alternate-effect exclusion and native acceptance requirements. Its source references guided the bounded inspection. |

The backend's first-line historical docstring says “no production consumers yet”.
The controller import and factory above provide concrete contrary inventory
evidence. Local review and cooperative mutex handling do not establish future
service-only store ownership. Presence observations leave same-presence external
replacement and restart uncertainty unresolved, as the controller source states.

## Diagnostic behavior and limits

`tools/byok_c1_effect_exposure_gate.py` reads only six fixed source paths. It
imports standard-library modules, parses Python ASTs, checks scoped lexical call
sites and selected exact text lines, and compares full raw-byte snapshot pins.
Any import, sink, comment or other byte drift produces UNKNOWN/HOLD. Missing or
unreadable files, decoding/parse failures, changed known sites, oversized sources,
nonregular files and detected symlink/reparse ancestors also produce UNKNOWN/HOLD.
Matching all inspected evidence yields `KNOWN_EFFECT_EXPOSURE` with status HOLD.
Available observations may remain in an UNKNOWN report to aid review.

The CLI binds its script-derived root to this exact intended workspace path and
offers no root override. Temporary fixture roots are used only through the
internal test engine. Fixed paths and ancestor `lstat` checks reduce traversal.
Unintended-root refusal shares the common report schema, with UNKNOWN/HOLD,
both qualification/admission booleans false, empty sources/evidence/known routes,
and the refusal issue and limitations. It performs no source reads.
Concurrent path replacement, hardlinks, hostile filesystem races and modification
of the tool itself remain outside this source-only assurance.

The JSON `known_routes` field describes the reviewed route templates. Per-source
hashes, evidence and `assessment` determine whether the current snapshot matches
them. The tool performs no transitive source traversal. Uninspected dependencies,
application callbacks, frozen companion implementation, P99 native adapters,
dynamic imports, copied modules, other processes, installed packages and loaded
images require separate investigation. The report cannot establish complete
security, source authenticity, runtime reachability, loaded dependency closure,
actual credential effects, consent provenance or OS isolation.

An ordinary `--report` exits 0 when assessment is performed, including UNKNOWN.
Automation must read the JSON. `--release-admission` always returns native exit 3.
There is no GO flag or approval input. A future qualified release mechanism
requires separately approved work. This tool is an explicit refusal surface
whose use is voluntary, with no integration into product execution or CI.

## Open Failures & Prior-Issues Review

The failure-review gate and P247/P249/P250 decision records were read. The bounded
ledger retains their dispositions. P251 tests exercise only diagnostic behavior.

| Issue and severity | Root cause, affected boundary and retained evidence | Repair/review disposition |
| --- | --- | --- |
| Legacy Python alternate effects, High | Current source chain above reaches interactive-user WinCred outside a future service owner. Direct backend/native entrypoints remain available. | Diagnostic exposes source evidence. Production exclusion and separate OS store isolation await qualified review. HOLD. |
| P96 race, High | Separate approval-current, ownership and effect calls leave a revocation-to-effect gap. Original C# source is retained, with the schedule documented in P250 101–129. | Original negative harness was read as source and was not executed here. Original race remains OPEN. No production repair or independent closure. HOLD. |
| SEC-03, High missing evidence | Principal/token/profile, store/target, ACL/SDDL, durable journal/anchor/history witness, recovery and ordinary-user denial remain undecided in P250 section 4. | Qualified owner decision pending. Decisions remain 0/7 overall. HOLD. |
| SEC-04, High missing evidence | Signing, enforced loaded-image CI, authenticated IPC, genuine one-use human consent and alternate-route exclusion remain outstanding. Source hashes do not establish these properties. | Qualified owner decision and artifact/OS evidence pending. HOLD. |
| P247/P249 native execution, Material | Recorded PowerShell policy/Application Control refusals prevented runtime acceptance. Compilation and source models leave actual Windows semantics unproved. | x64 0/54 and x86 0/54 executed remain unchanged. Historical native gates retain their constraints. No bypass, unsigned binary or policy change. HOLD. |
| Original P76 failures, Material | Four authentic original FAIL methods remain unwaived. Their root causes and native closure are outside this diagnostic. Later property mappings cannot substitute for original evidence. | Preserve all four. Independent closure pending. HOLD. |
| Whole-product acceptance, High missing evidence | Qualified SEC/release decisions remain 0/7 and product regressions remain 0/3. | Focused fixture/source tests confer no production approval. REAL-KEY NO-GO and PRODUCTION RELEASE HOLD. |
| P251 first-review findings, three Low | Duplicate/scope tests could pass from hash drift alone; cross-root isolation evidence was absent; unintended-root JSON omitted common fields. Diagnostic test/report boundary only. | Added exact AST issue assertions and matching-pin duplicate/renamed/missing-sink subtests, A-to-B-to-A tests including mocked root/ancestor symlink and reparse refusal before open, and shared report construction with both-mode refusal schema tests. 27/27 native focused PASS; final independent read-only review pending. Draft review only; production HOLD. |

## Actual native validation

The installed authorized executable was
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe`, reporting
Python 3.12.10 with exit 0. Sandbox read access was denied initially. The authorized
native invocation succeeded through the normal escalation mechanism.

From this checkout the following commands were executed with that executable.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B -m unittest discover -s tests -p test_byok_c1_p251_effect_exposure_gate.py -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B tools/byok_c1_effect_exposure_gate.py --report
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B tools/byok_c1_effect_exposure_gate.py --release-admission
```

Post-remediation focused tests ran **27 tests, OK, native exit 0**, using
Python 3.12.10 and the exact `-B` commands above. The initial sandbox invocation
could not access the executable and produced no native test result; the normal
approved escalation ran the native tests successfully. Subtests also removed and
altered each of the six copied actual sources. Synthetic cases cover changed
sinks/import topology, parse/encoding errors, missing/denied/nonregular/oversized
files, mocked reparse rejection, duplicate/wrong-scope sinks, root refusal,
determinism, absent GO option, source-only parsing and both CLI exit contracts.
No production modules were imported by the diagnostic/tests.

The three added test methods prove matching-pin AST rejection of duplicate,
renamed-scope and missing sinks (with fixture pins restored by patch context),
distinct-byte A-to-B-to-A source isolation, and mocked symlink/reparse rejection
at root and ancestor followed by unchanged A assessment. No OS links were made.
The existing duplicate/scope tests now require `known_call_site_changed`.
Both unintended-root CLI modes assert the full common field set, conservative
values and no assessment, source-read or file-open calls.

Post-remediation direct report returned `KNOWN_EFFECT_EXPOSURE`, HOLD,
6 sources, 22 evidence entries, no issues, native exit 0. Direct release refusal
returned the same counts and assessment, admission false, native exit 3;
`$LASTEXITCODE` was captured immediately and propagated in both invocations.

Earlier pre-remediation invocation evidence follows: direct report returned
`KNOWN_EFFECT_EXPOSURE`, HOLD, no issues, exit 0.
Direct release admission returned the same assessment with admission false.
PowerShell initially surfaced that nonzero process as shell exit 1. A second
invocation explicitly captured `$LASTEXITCODE` as **3** and propagated exit 3.
The CLI subprocess test independently asserted native return code 3.

A separate native subprocess receipt printed
`{"native_exit": 3, "status": "HOLD", "assessment": "KNOWN_EFFECT_EXPOSURE"}`
and its asserting wrapper exited 0. Both added Python files compiled in memory
with exit 0 using `compile(path.read_bytes(), str(path), 'exec')` through Python
stdin. The first `-c` syntax-check attempt exited 1 because PowerShell stripped
string quotes from the command. Sending the same check through stdin corrected
the invocation. Source files required no repair.

`git diff --check`, tracked diff and staged diff checks were empty. Per-addition
`git diff --no-index --check -- NUL <path>` emitted no whitespace diagnostics
and returned the expected difference exit 1. Final status contained exactly the
three untracked additions, with HEAD still at the required parent.

Full product regressions and native credential/service tests remain outstanding.
Final independent read-only review of these three LOW remediations is pending.
Work remains uncommitted for that review; no commit, push or P251 core release GO.
