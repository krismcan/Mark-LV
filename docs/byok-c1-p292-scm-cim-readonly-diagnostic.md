# P292-DIAG: isolated read-only SCM / CIM controls

20 November 2026. **Diagnostic candidate only. SECURITY HOLD. P292 remains
HOLD/RED, PR #212 DRAFT/UNMERGED. REAL-KEY NO-GO / PRODUCTION HOLD. Qualified
external approvals 0/7; accepted full product regressions 0/3.**

Codex is the single source writer. Nayeon is the independent CTO reviewer,
Windows evidence auditor and sole Git publisher. No staging, commit, push,
PR creation, tag, production seal or main workbook/dashboard update by Codex.
This is an explicitly authorized investigation of held failures, not forward
product-phase work or a waiver of the failure gate. No independent security
approval or hosted runtime result is asserted by this author document.

## Frozen boundary

Pre-edit checkout was clean on
`byok-c1-p292-readonly-scm-cim-diagnostic-20261120`, exact HEAD
`1083919da53f808105522dd8e11dba9fdf844fa0`, with 1,185 tracked files and no
tag at HEAD. This is the frozen THIRD P292 source. The state file still starts
with November 3 Phase 10.2 notes; Git is authoritative. That stale file is
preserved, since no product phase is completed here. No inherited source,
workflow, P96 implementation, test expectation or historical receipt changes.

Exactly four additions, all presently uncommitted:

1. `tests/p292_readonly_observer/NativeScmReadOnlyCanary.cs`
2. `tests/p292_readonly_observer/HostedReadOnlyReview.ps1`
3. `.github/workflows/p292-windows-readonly-scm-cim-diagnostic.yml`
4. `docs/byok-c1-p292-scm-cim-readonly-diagnostic.md`

The proposed same-repository DRAFT child PR must target
`byok-c1-p292-ephemeral-scm-service-witness-20261120`, whose base SHA must
remain the frozen parent above. Hosted admission requires the event head SHA
to equal the actual checkout and have precisely that one direct parent.
Both repository identities, branch names and draft status are checked twice
(workflow and script). A merge head, extra commit, changed inherited entry,
extra path or dirty/ignored source is HOLD. Checkout depth two supplies the
direct parent; there is no script fetch or history rewrite. A skipped workflow
is missing evidence, never diagnostic PASS. Nayeon must independently verify
these facts and exact final bytes before any publication.

## Open Failures & Prior-Issues Review

Sources reviewed: the engineering failure gate; frozen P292 source, workflow
and review; P291 boundary review; relevant P211/P216 acceptance records; and
the user's explicit third-run archive findings. Historical hosted findings
below are attributed to the supplied receipts, not a Codex download/re-audit
of the eighteen archives. No unavailable evidence has been invented.

| Issue / severity / source | Symptom, root cause and affected trust paths | Containment, evidence, independent review and disposition |
| --- | --- | --- |
| Original P96 HIGH OPEN; original coordinator/fixture, P291/P292 reviews | Final StillCurrent / fourth IsOwned check is separate from SAVE/REPLACE/DELETE effect; revocation can intervene. Durable effect/owner/restart custody is unproved. | Original 15-case negative and all older routes stay frozen. This diagnostic has no product imports, owner, ledger, credential or effect edge. Qualified owner/atomicity review still OPEN; HOLD. |
| P292 FIRST material startup/cleanup failure, 20 Nov, run 44739845249 | All six native create and restricted-SID configuration receipts exit 0; all six eight-second start clients time out without a native start exit. Stops return 1062, deletes 0, immediate after-absent probes 1, cleanup HOLD. Underlying SCM/service outcome is unknown. | Preserve 0/6 RED. Neither a client deadline nor deletion receipt proves mechanism failure cause or cleanup. Later samples do not rewrite this run. Independent closure OPEN; HOLD. |
| P292 SECOND material metadata failure, 20 Nov, run 44741869649 | x64 3/3 and x86 trial3 mechanism PASS. x86 trials1/2 native create0, then generic immediate metadata failure before restricted SID setup; empty result, query/rights failure and strict field mismatch cannot be separated retrospectively. Cleanup 6/6 PASS in supplied receipts. | Preserve 4/6 RED. Corrected prior review assertion: both failing archives DO contain native create0 receipts. No assumption of create failure or universal CIM delay. Independent root-cause review OPEN; HOLD. |
| P292 THIRD metadata transport/error, 20 Nov, run 44766866901 | x64 trial1 create0 then create-metadata exit11 QUERY_ERROR; cleanup PASS. x64 trial2 create0 then CIM child deadline TIMEOUT; cleanup PASS. Neither proves identity divergence; timeout alone cannot localize startup/provider/SCM contention. | Native and CIM controls below are distinct, with raw native errors and actual child exits. No error is converted to empty/PASS or retried. Root cause unknown; independent review OPEN; HOLD. |
| P292 THIRD startup/absence/cleanup, same run | x86 trial2 create0, exact create-metadata PASS, restricted-SID configuration0, then start client TIMEOUT even at 40s; native after-absent query TIMEOUT, teardown UNVERIFIED, CLEANUP HOLD. The other three trials have actual virtual-account restricted-token mechanism and cleanup PASS. | Preserve 3/6 RED. This failure includes a native query timeout and cannot be called solely a CIM delay. No local or new mutable cleanup experiment; Windows evidence auditor must reconcile original archives. HIGH unresolved cleanup evidence; HOLD. |
| Principal/configuration vs runtime identity HIGH OPEN; P99/P216/P281/P292 | LocalSystem admission and proposed virtual service account/name differ. Configured account/image is not the kernel runtime token, installed provenance or protected custody. | Native config/status and CIM equality here do not inspect any runtime token, SID or process. Original token mechanism probe remains frozen. Qualified principal/installation decision OPEN; HOLD. |
| Provenance, consent, profile/store and restart HIGH OPEN; P290/P291/P281/P282 | Account identity cannot authenticate protected client code or user-present one-use consent. Service profile, credential ownership, journal/anchor/effect and alternate recovery paths remain unresolved. | No policy, confirmation, installation, account, ACL, privilege, profile, store, registry, token, file-security or credential operation. No product dispatch. Qualified external review OPEN; HOLD. |
| P76/P211/P216 acceptance OPEN; relevant historical reviews | Original P76 four failures, P211 test02, P216 test02/test06 and historical native-effect expectations remain unwaived. | No old suite run, rewritten, skipped, weakened or represented as passing. Full product regressions remain 0/3. Acceptance owners/review OPEN; HOLD. |
| Historical P292 harness/receipt incidents; frozen P292 review | Partial-start cleanup gaps and late-child uncertainty; local relative-path csc CS1504; empty compiler-log parser attribution errors. | No repair of the original PR. Absolute compiler input, ReadAllText for empty logs, isolated read-only children and explicit unavailable-exit categories in this child. Author compile/static proof only; independent review OPEN. |
| Missing qualified decisions; GOV/SEC/REL | Seven signed approvals and three accepted complete product regressions absent. | External approvals 0/7, product regressions 0/3. No approval by proxy, waiver, real keys or production seal. HOLD. |

Disposition: **bounded diagnostic source preparation only; security, product,
P292 mechanism, original cleanup and release HOLD.** Unknown material failure
causes remain unknown. This work does not close or defer them. Nayeon review of
the four exact source files and six future hosted archives is still required.

## Competing explanations and authority proposal

Microsoft documents that [QueryServiceConfigW](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryserviceconfigw)
retrieves service configuration using SERVICE_QUERY_CONFIG. This is a direct
SCM API path. It is configuration evidence, not a claim that a running process
has that identity or that several reads are atomic. The documentation explicitly
distinguishes configured values from an already running service's configuration.

[Win32_Service](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-service)
is provided by CIMWin32; StartName and PathName map to SCM configuration fields.
The CIM cmdlet adds a PowerShell/process/provider path. An error or deadline in
that path does not identify which component caused it. A direct native timeout
is also possible and must remain visible. A successful create receipt does not
prove either subsequent observation succeeded.

The frozen P292ServiceIdentityProbe already independently imports
OpenSCManagerW, OpenServiceW, QueryServiceConfigW, QueryServiceConfig2W and
QueryServiceStatusEx, plus native process/token/restricted-SID checks. The frozen
host also uses Win32_Service and Win32_Process. This pilot is separating those
observation paths, not treating the original mechanism as CIM-only or replacing
its kernel token evidence with configured-account strings.

Microsoft's [DeleteService contract](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-deleteservice)
marks a service for deletion; removal waits for the service to stop and open
handles to close. No API atomicity, immediate visibility, unconditional provider
delay, eventual cleanup or successful runner teardown is inferred. This canary
does not exercise deletion at all.

Competing causes remain: CIM child startup/transport/provider failure; rights
failure; genuine exact config mismatch including representation differences;
SCM or runner contention; native subprocess startup/query delay; dynamic
service lifecycle/logon behavior; retained handles or marked deletion; and
hosted orchestration deadline/teardown defects. The first two third-run x64
failures involve CIM observations. The third-run x86 failure also involves
start and native absence. No single cause is established across them.

**Proposed decision, subject to qualified review:** direct read-only SCM is the
candidate source of authority for configured SCM metadata and native 1060
absence. CIM is an independent diagnostic corroborator; disagreeing results
remain mismatches/errors and HOLD. This is not an implemented replacement of
P292's CIM gates. Removing or redesigning any gate requires separate reviewed
source and evidence. Runtime identity still needs independent token/restricted
SID proof and consent/provenance/permission remain separate. No account-name
alias, case, quoting, environment expansion or path normalization may turn a
disagreement into agreement.

| Observed controls | Permitted inference / disposition |
| --- | --- |
| Native PASS, CIM ERROR/TIMEOUT | Failure reproduced in the CIM comparison path on stable controls; localize using native pre/post and subprocess receipts. Do not claim all original failures have this cause. Diagnostic HOLD. |
| Native ERROR/TIMEOUT | Native/runner path is affected too. Preserve Win32 error or unavailable exit; no substitution of CIM success. Diagnostic HOLD. |
| Both readable, exact fields/state disagree | MISMATCH including representation differences; no canonicalization acceptance. Diagnostic HOLD; investigate with independently approved private evidence if necessary. |
| All fixed controls PASS in all six jobs | Conclusive equality only for those sampled stable controls. Original dynamic lifecycle failure is unreproduced; P292 and security HOLD. |
| Missing/incomplete evidence, source drift or unexpected protocol | Infrastructure/evidence HOLD, never successful diagnostic acceptance. |

## Executable scope and output contract

All runtime is restricted to disposable GitHub-hosted Windows-2022 runners.
Workflow plus script require same-repository DRAFT event and exact source;
native code plus isolated CIM child require explicit hosted environment guards.
These environment strings are accident barriers, not hostile-runner attestation.
Locally the only checks are Git/raw hashes, static AST/source inspection and
compilation. Neither generated executable nor this script/embedded child may
run on Kristian. No Python, downloads, package restore or secret inspection.

Each of three x64 and three x86 jobs has an eight-minute job ceiling. Each job
has four fixed samples for A (EventLog), B (Schedule) and X (one random
`NayeonP292_` + twelve lowercase hex characters), with no collision retry or
creation. It performs 12 standalone native controls and 12 paired controls,
24 outcomes. A pre-existing X is MISMATCH; it is never changed. Failures are
sticky while remaining planned independent samples execute. Infrastructure or
child-join failure stops probing and keeps HOLD. There is no poll-until-pass,
backoff, dynamic retry or failure-dependent sample count.

Native imports are exactly OpenSCManagerW, OpenServiceW, QueryServiceConfigW,
QueryServiceStatusEx and CloseServiceHandle. Manager access is CONNECT (0x1),
service access QUERY_CONFIG | QUERY_STATUS (0x5), including the absent open.
Only the exact A/B mapping or strict X shape is accepted; absent PASS requires
OpenService error1060. No access broadening, privilege change or fallback.
Query buffers have layout, size, bounded pointer and UTF-16 termination checks;
all handles/memory are released and handle-close failure is ERROR. Native reads
are separately sampled, never claimed to form an atomic snapshot.

The standalone control compiles/runs for the job's actual x64 or x86 target.
A separate warning-as-error AnyCPU build of the identical source is loaded
into an isolated **x64 pwsh child on BOTH matrix architectures**. That child
performs native-before, one local Get-CimInstance Win32_Service query limited
to Name/StartName/PathName/State, then native-after. It performs no Win32_Process
or event-log query. Raw config remains in the same child process; only an
opaque native object sees it. Native before/after must be stable, CIM existence,
exact Name, exact StartName, exact PathName and exact mapped State must agree.
Separate standalone x86 vs paired x64 reads are not a direct cross-bitness
raw-field equality proof. No x86 CIM process coverage is claimed.

Source canonicalization is **field-source selection only**:
SCM lpServiceStartName -> CIM StartName; SCM lpBinaryPathName -> CIM PathName.
Strings are compared ordinally, without normalization. A formatting difference
is ACCOUNT_FORMAT or PATH_FORMAT MISMATCH, not an accepted identity alias.
State and native drift are separate categories. Multiple/zero unexpected rows
are presence mismatches; they never trigger another query in that sample.

CIM OperationTimeoutSec is 5, but the independent entire child deadline is 12s
including startup/assembly load, less than the requested 15s maximum. Standalone
native deadline is 4s. Compiler deadline is 15s; kill/join allowance is at most
2s and output drain at most 1s (CIM wait plus both allowances is at most 15s).
Script admission stops new child work at 390s; the external eight-minute
job ceiling also bounds setup, source evidence and artifact handling. Per-child
completion emits sanitized progress, well inside the five-minute OM v2.1 stall
watchdog. Loss of runner or timed-out job is missing evidence, not cleanup proof.

Native and CIM outputs contain only enums, latency classes, numeric Win32/
HRESULT/CIM status codes and actual architecture. The orchestrator adds sample
index, A/B/X, transport, raw process exit (UNAVAILABLE on deadline/launch failure),
protocol and CONTROL=PASS/ERROR/TIMEOUT/MISMATCH. It preserves complete allowlisted
receipts even if a later child stage fails. ACCESS_DENIED is counted, never
weakened. Summary ERROR/TIMEOUT/MISMATCH counts are control outcomes; NATIVE_ERROR,
CIM_ERROR and ACCESS_DENIED counts are receipt occurrences (pre/post may both
count). Unexpected stdout/stderr cannot be published as raw text or accepted.
Compiler raw diagnostics remain in private temp, represented by codes/hash/exit.

Any WMI error, mismatch, timeout, rights failure, protocol failure, source drift,
incomplete fixed plan or unexpected raw exit yields diagnostic exit1/HOLD.
Successful diagnostic exit0 requires 24/24 controls plus source/binary integrity;
it is explicitly labeled CONCLUSIVE_STABLE_CONTROLS_ONLY and P292=HOLD. Even
6/6 green archives prove no P292 dynamic mechanism acceptance.

All generated build/evidence files are under RUNNER_TEMP, with per-child temp
redirected there, module search limited to bundled PSHOME modules, no PowerShell
profile loading, and child environments cleared of inherited secrets. Source
is hashed as raw Git blobs and SHA256 before/after (1,189 files: 1,185 inherited
plus four additions); inherited tree entries are identical to the exact parent.
The two positive binary hashes are checked before/after. Persistent source,
service, machine configuration and security state have no write operation.
Git reads disable optional locks/index refresh; no Git mutation follows checkout.
Only owned diagnostic child processes may be terminated at their deadline.

Exactly six text artifacts are allowlisted: source-before.sha256,
source-after.sha256, compiler.txt, binary.sha256, controls.txt and summary.txt.
No binaries, wildcard build directories, service identifiers, paths, accounts,
SID/PID, tokens, raw CIM objects, exceptions or event-log content are uploaded.
Manifest paths are repository-relative source paths, not service configuration
or workspace/user paths. Checkout/upload use the original P292 action pins,
contents:read, no persisted Git credentials and no repository write permission.

## Local author validation, not runtime approval

Local evidence directory:
`%TEMP%\p292-diag-local-00aaa71602f348bda011c5d1316ee586`.
The pre-edit manifest verified all 1,185 disk files against raw HEAD Git blob
identities (no text filters). `inherited-before.sha256` SHA256:
`452C3FB67E8D2BCDF63DDB0239AA1AC46089BCC90CA1B089EADB42C0E6EAEA7F`.

Framework csc absolute-source builds used /noconfig, /warn:4, /warnaserror+,
/debug-, explicit System.dll and no external/product references. Raw exits:

| Build | x64 | x86 | Diagnostics / executable |
| --- | --- | --- | --- |
| DEBUG + C1_REVIEW_ISOLATED_ASSEMBLY + C1_P292_READONLY_DIAG_ONLY | 0 | 0 | None; produced only in local temp; NOT RUN |
| All defines absent | 1 | 1 | Only CS1029; no binary |
| Missing DEBUG | 1 | 1 | Only CS1029; no binary |
| Missing C1_REVIEW_ISOLATED_ASSEMBLY | 1 | 1 | Only CS1029; no binary |
| Missing C1_P292_READONLY_DIAG_ONLY | 1 | 1 | Only CS1029; no binary |
| All positive defines plus RELEASE | 1 | 1 | Only CS1029; no binary |

The separate AnyCPU bridge also compiled with raw exit0, empty compiler log,
warning-as-error; NOT RUN or loaded locally. These 13 compilations include
three positive builds and ten deliberate refusal builds, not executable tests.
Positive/negative raw logs and compiler-summary.txt are retained externally.

One author validation wrapper initially treated an added-file Git --no-index
exit1 as a whitespace failure. Root cause was difference exit semantics, not
source whitespace. The preserved corrective receipt checks raw exit1 with
zero diagnostic lines for every addition and same-file control exit0. No
product/test expectation was changed to hide that tooling error.

Outer and embedded PowerShell ASTs are parsed as data, without execution.
Embedded commands are only Get-CimInstance and Set-StrictMode. Static native
import/access review finds only the five read/close APIs above, with no token,
process, account, file, registry or security API. The host wrapper's file writes
are generated temp outputs; its process kills are bounded owned-child teardown.
No service mutation cmdlet, native service mutation API, sc.exe, remote CIM,
download, restore, credential operation, elevation or product import exists.
Static checks cannot establish provider reliability or Windows runtime behavior.
Final SHA256/AST/scope receipts accompany the source; this document deliberately
has no recursive self-pin. No full Python/product suite or compileall is run:
all inherited files are frozen and local validation is explicitly compile/static
only. Accepted product regressions remain 0/3.

Exact non-document source SHA256 pins (raw bytes):

| File | SHA256 |
| --- | --- |
| NativeScmReadOnlyCanary.cs | `2847530AFC1C5E1316C9336E44D751DB11664ABE3CD9FB0B314776C0C149B7E0` |
| HostedReadOnlyReview.ps1 | `66887DA8B3C60F21EDDF644E90DADDF8D995C5D11C39F225A49FE1761068D7F3` |
| p292-windows-readonly-scm-cim-diagnostic.yml | `58C9FAB58A3A179590AD1F5E14CC03BAB2E10BD24B1BCF66F079977239693E4E` |

Local `compiler-summary.txt` SHA256:
`3DA72C00FAEAC66A443317833E2E12149671699DD3CFC28B031F0DB329F1DD74`.
The external final four-file manifest includes this document after its last edit.

## Limits and next decision

Built-in long-lived services differ from a newly created random virtual-account
service. Samples cannot reproduce a create/start/logon/provider visibility race,
restricted-token identity, late process, retained service handle, marked deletion,
dynamic absence or teardown uncertainty. Finite pre/post reads cannot exclude
an intervening change/ABA or prove continuous custody. Installed service config
is not execution provenance, user consent, permission or production identity.

If this read-only pilot does not reproduce the original failure, preserve that
negative diagnostic result and stop. Do not loop hosted runs until green.
Any controlled mutable hosted experiment needs a separate bounded proposal,
qualified independent review and authorization, with original failure receipts,
exact native/CIM timeline, actual raw exits and fail-closed cleanup evidence.
It cannot be smuggled into this four-file read-only child or Kristian execution.

**Qualified security disposition: HOLD.** Independent Nayeon exact-source audit
and six-archive Windows review are pending. Original P292 remains DRAFT/UNMERGED,
HOLD/RED; all production and external acceptance gates remain unchanged.
