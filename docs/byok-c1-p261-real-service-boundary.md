# P261 real Windows SCM identity admission evidence

17 November 2026. OM v2.1. Sole Codex implementation writer. Review-only,
nondeployable, five additive paths, unstaged. **Engineering acceptance HOLD,
x64 execution BLOCKED, security and production HOLD.**

## Intake and dependency boundary

Work root `D:\Nayeon\CODEX_P261_REAL_SERVICE_BOUNDARY_20261117`, branch
`byok-c1-p261-real-service-boundary-20261117`, clean parent
`0e1171cdf6c542c08a087b8cd7f1fd1b86baec83` from P260 draft PR #182.
There is no tag at HEAD. Nearest ancestor tag is
`nayeon-v1-phase-10-3-synthetic-provenance-redaction-01`.
The current-state file describes older Phase 10.2 work. Git governs this intake.
This bounded BYOK C1 prerequisite continues the existing held work.

The five additions are `native_c1_candidate/P261ScmReadOnlyAdmission.cs`,
`tests/p261_scm_readonly/ScmReadOnlyTests.cs`,
`tests/test_byok_c1_p261_scm_readonly.py`, this note and
`.github/workflows/p261-windows-scm-readonly.yml`.

Both compiler paths reference the actual frozen `ServiceGate.ServiceName`.
Only four C# sources compile, comprising the new observer and harness plus
original `tests/p99_original_native_c1_denial/ServiceGate.cs` and its single
`ProtectedAcl.cs` dependency. Execution uses the constant only. The historical
`LiveEligible` and ACL-check methods have no call site in the new observer or
harness. The candidate service continues to bind its name to that same constant.
The new observer has no deployed service entrypoint. Both new C# files require
`C1_REVIEW_ISOLATED_ASSEMBLY` at compile time.

## Open Failures & Prior-Issues Review

Reviewed AGENTS.md, the engineering failure gate, current-state mismatch,
P216 RFC, P215 principal observer, original service gate and ACL dependency,
candidate service, P250 architecture, P258 containment and P259/P260 evidence.
The affected chain reaches original/native candidate hosts, proposed service
principal/store ownership and independent Python same-user credential routes.
Cross-process, cross-token, loaded-image and restart isolation remain open.

| Issue / severity / disposition | Root cause, reproduction and affected boundary | Repair or containment, validation and independent review |
| --- | --- | --- |
| P261-IDENTITY / HIGH / OPEN / HOLD | Frozen `ServiceGate.ServiceName` is `NayeonV1ByokCustody`. Candidate `CustodyService.ServiceName` uses that constant. P216 proposes `NT SERVICE\NayeonByokCustody`, omitting `V1`. Under virtual-account semantics these describe different service identities. | Direct constant reference prevents new observer drift. Source test pins both historical sources and reproduces the naming mismatch. Native parser rejects the P216 name and LocalSystem. Qualified SEC-03/04 decision, reviewed principal choice and production repair remain OPEN. Independent review pending. |
| P261-LOCAL_SYSTEM_GATE / HIGH / OPEN / HOLD | Frozen `tests/p99_original_native_c1_denial/ServiceGate.cs` requires `accountIsLocalSystem=true` in `ServiceGate.EligibleForService` through `if (!accountIsLocalSystem || ...)`. `ServiceGate.LiveEligible` passes OS identity truth from `WindowsIdentity.GetCurrent()` and `WellKnownSidType.LocalSystemSid`. P216 proposes a dedicated least-privilege Windows virtual service account with restricted service SID and explicitly avoids LocalSystem as the default. Even correcting the proposed account spelling would leave that virtual account unable to satisfy the original startup gate. | The existing candidate `CustodyService.OnStart` calls the frozen gate and always throws, including after a hypothetical successful gate check. It has no `Main` entrypoint. The existing source test records the separate gate contradiction. SEC-03/04 QUALIFIED DECISION PENDING. No author-selected service account or production repair is approved. Installation, native effect and release remain HOLD. Independent review of this correction and runtime evidence remain pending. |
| P96 / HIGH / OPEN / HOLD | Final approval/lease checks and later external effects permit post-check revocation interleaving. Original negative coordinator and driver retain that reproduction. | Original bytes and assertions retained. P260 synthetic results PASS as supplied at intake. Service isolation and original production repair remain OPEN. |
| Same-SID native WinCred / HIGH / OPEN / HOLD | An in-process denial cannot establish a separate OS principal/store boundary against another same-user native route. P216/P250 enumerate original native/backend routes. | P258 default UI/backend containment evidence retains its scope. This observer has only SCM read rights. OS cross-token/store isolation, profile, ACL, signed-image and restart evidence remain pending. |
| SEC-03/04 / HIGH missing evidence / HOLD | Qualified principal/store and policy-owner decisions, genuine consent/IPC, loaded-code identity and durable recovery lack source-bound qualified evidence. | Qualified approvals 0/7. Every evidence object has constant-false approval, owner, credential, effect and real-key properties. Independent GOV/SEC decisions remain unissued. |
| P76 / P251 / P258 / material / HOLD | Original P76 four failing methods, original P251 failure and P258 nine selected inherited failures remain unwaived in prior records. | Preserved historical sources. P261 focused results supply no closure. Full native whole-product regressions 0/3. |
| P260 CI input failure / material historical finding | Relative Framework compiler inputs resolved at the repository root and produced CS1504. | New workflow resolves four literal input paths before both negative and positive builds. Both author positive builds return raw exit 0. New hosted execution and independent review pending. |
| P261 x64 launch / material missing evidence / BLOCKED | Ordinary `Start-Process` failed with Application Control policy blocking the compiled x64 executable before execution. This shares the policy-sensitive native execution boundary documented for P247. | Preserve the refusal. x64 has zero executed cases. Ordinary x86 launch separately succeeded, then was repeated with a retained process handle for a genuine raw exit receipt. Policy remains authoritative. Independent x64 host/CI execution pending. |
| Author Python validation / missing evidence / HOLD | Read-only probe of the authoritative host Python path returned Access denied. | Seven new Python source tests and preserved P259/P260 source suites await Nayeon's host runner. Independent source and runtime review pending. |

Disposition is **GO for the explicitly authorized additive read-only investigation
and denial authoring only**. Acceptance, security, real-key and release remain
**HOLD**. Both the literal name mismatch and the LocalSystem/virtual-account
gate contradiction remain HIGH OPEN architecture blockers. SEC-03/04 remains
QUALIFIED DECISION PENDING. The read-only observer supplies no startup eligibility.

## Windows contract and observed data

For an independently chosen virtual account, Microsoft's account format derives
from the literal SCM service name. The P216 proposal requires a qualified
principal decision and source-bound correction. This component derives a
comparison value from the frozen name solely to detect inconsistency. It grants
no account selection or principal approval. [Microsoft CreateServiceW](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-createservicew)

The native calls use local `OpenSCManagerW(null, null, SC_MANAGER_CONNECT)` and
`OpenServiceW` with `SERVICE_QUERY_CONFIG` on the frozen constant. A successful
open leads to a size query and bounded allocation of at most 8,192 bytes for
`QueryServiceConfigW`. The decoder validates the header size, account pointer
range, alignment and in-buffer UTF-16 terminator. It compares the account in
place, retains only equality and discards native storage in `finally`. Other
configuration pointers, including the image path, are never dereferenced or
reported. The success call's bytes-needed output is unused, following its
documented failure-only meaning. [Microsoft QueryServiceConfigW](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryserviceconfigw)

`QueryServiceConfig2W` at `SERVICE_CONFIG_SERVICE_SID_INFO` reads the actual
four-byte `SERVICE_SID_INFO.dwServiceSidType`. The evidence retains that queried
policy field only when obtained. Types 0 and 1 are mismatches, 3 is restricted,
and any other value is malformed. A changing or oversized response fails closed
without retries. Both allocations and SCM handles are released in `finally`.
Cleanup refusal downgrades observation to Unverified. [Microsoft QueryServiceConfig2W](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-queryserviceconfig2w), [Microsoft SERVICE_SID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info)

Results are Missing, Denied, Mismatch, Unverified, UnsupportedOs,
MalformedBuffer or ConfigObserved. Matching configured account and restricted
policy produce ConfigObserved with all authority properties false. Configuration
queries provide a time-bounded observation. Effective process token, service
owner signature, running-image identity, coherent configuration across changes,
profile and store isolation require separate evidence.

The component has exactly five P/Invoke declarations covering SCM open/query
and handle cleanup. The claimant entrypoint discards account and approval
claims, then invokes the same real OS observer. Evidence contains coarse status,
nonsecret booleans and the queried service-SID policy DWORD. Account, SID strings,
service image path, system error text and credential material have no output
path. All credential and effect authority properties return false.

## Native harness and source contracts

The harness executes the real local SCM observer and ten claimant combinations,
including claimed qualified approval, the P216 proposal, the source-derived
account, LocalSystem, arbitrary text and null. Every result must reject authority.
An unexpected installed service, access refusal, unsupported OS, malformed
response, query failure or changing observation yields engineering HOLD with
exit 2. Exit 0 requires the exact service to be missing on every observation.
Assertions fail with exit 1 and coarse output.

Parser-only checks cover x64/x86 header layout, correct/case-varied account,
P216/LocalSystem/spoof mismatches, empty account, null/short/oversized buffers,
null/header/pre-buffer/end/unaligned pointers, missing terminator and valid or
malformed service-SID policy values. These allocated parser fixtures exercise
decoder rejection. Real SCM evidence comes from the separate OS calls.

Seven Python tests read source bytes only. They pin original identity and P216
mismatch, deny additional native APIs and grant properties, check cleanup and
real-observer harness wiring, verify the workflow and exercise eight native
plus nine workflow negative mutations. Literal hashes bind both new C# sources,
the compiled historical dependencies, candidate service/boundary/P215, original
P95/P96, P259 comparator/driver/tests, P260 tests and P216 RFC. The workflow also
pins the Python checker itself.

## Author validation receipts

These are author checks on 17 November 2026. Nayeon's independent evidence
remains pending. The subsequent technical review disposition is recorded below.

| Check | Observed result |
| --- | --- |
| Framework64 v4.0.30319 `csc.exe`, `/platform:x64`, isolated flag | Raw compiler exit 0 |
| Framework v4.0.30319 `csc.exe`, `/platform:x86`, isolated flag | Raw compiler exit 0 |
| No-flag compiler guard, both architectures | Raw compiler exit 1, exactly two CS1029 diagnostics naming `P261_REVIEW_ONLY_NONDEPLOYABLE` |
| Ordinary x64 native launch | Application Control BLOCKED before execution, raw process exit unavailable |
| Ordinary x86 native launch, confirmed handle-retained repeat | Raw process exit 0, 32-bit receipt, parser negatives PASS, real SCM Missing, claims and service-store authority REJECT |
| Actual configured-account/SID query on installed target | Pending, exact target missing during x86 execution |
| Authoritative Python source suites | Access denied at interpreter probe, unexecuted |
| Workflow PowerShell syntax | Four run blocks parsed successfully with Windows PowerShell parser after substituting the architecture expression |
| Raw source manifest | 16/16 workflow source hashes matched after author compilation/execution |
| Historical tracked source and index | Preserved, additions unstaged |
| Hosted Windows CI, correction review, full product native regressions | Pending, 0/3 full native product regressions, qualified approvals 0/7 |

Author compiler/runtime artifacts are local temporary evidence under
`C:\Users\krist\AppData\Local\Temp\nayeon-p261-author-20261117`.
The first x86 launch produced expected text but lacked a captured process exit.
The confirmed repeat retained `Process.Handle` before waiting and recorded
`Process.ExitCode=0`. The confirmed text receipt has SHA-256
`42E8C99C25AF848E3D1EC8693BB8BE93F766186EF006A83216AE05C8E628D715`.
The confirmed exit file has SHA-256
`13BF7B3039C63BF5A50491FA3CFD8EB4E699D1BA1436315AEF9CBE5711530354`.
Both guard logs have SHA-256
`6FF975A251937CEDE0D3AC920E40812C0B4CEE543A115F941111BBB323AA7EBB`.

The subsequent independent technical review returned
`P261_FINAL_REVIEW=GO_DRAFT_ONLY_CI_PENDING`, with no new HIGH/MEDIUM findings
and a LOW documentation deficiency for the omitted existing gate contradiction.
This correction records that second HIGH OPEN issue separately. Validation
conclusion remains **HOLD**, with SEC-03/04 QUALIFIED DECISION PENDING,
authoritative Python validation and hosted CI pending. Draft-only review status
grants no service-account choice, installation, native effect or release approval.

New C# raw hashes are
`FBBC4AAF4B65D6C4B49DD0EE8B99C391A2E4AC08E1E6454CD10AF26C68804193`
for the observer and
`F1755BDEBF1B1E44ABA6E47B5A4A4DC9BC36FF39D31A4CCE6C796A3716613A3B`
for the harness. The frozen service gate remains
`F65EF9F04283B6CA82D42B8D61B6B99B23262DE62E248DC575C0CEF1B3D96B8D`.
All other before/after pins are in the Python and workflow manifests.

## Independent host and draft-PR acceptance

Nayeon independently reviews the five additions and runs the authoritative
Python source contracts, including preserved P259 and P260. Example focused run
from the exact work root follows. Each module's native exit must be preserved.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B -m unittest discover -s tests -p test_byok_c1_p261_scm_readonly.py -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B -m unittest discover -s tests -p test_byok_c1_p259_owned_pending_transaction.py -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -I -B -m unittest discover -s tests -p test_byok_c1_p260_actual_contention.py -v
```

Both architecture builds use the workflow's four absolute-path inputs, negative
compile guard, ordinary process launch, retained process handle, 60-second
deadline and exact receipt validation. Any policy refusal is BLOCKED evidence.
Independent review must inspect all failure branches, native structure layout,
pointer bounds, constant binding and permanent denial. Then a separate Codex
review and valid GitHub draft PR can proceed in the user-specified order.

The authored workflow targets the fixed P260 branch and literal base SHA. It
requires a draft from the exact P261 branch in the same repository, checks out
the event's exact PR head, requires five additive paths, and hashes sources
before and after execution. Windows x64/x86 jobs independently preserve Python,
compiler and real native process exits. Missing-service receipt inventory and
pointer width must match exactly. Unexpected target presence yields HOLD.
Actions are commit-pinned, repository permission is read-only, persisted checkout
credentials are disabled and uploads whitelist text log/exit/JSON files.
Hosted evidence awaits authorised source publication after the independent gates.

The service identity choice, installed configuration, profiles, ACLs, signing,
store operations, OS cross-token testing and real-key eligibility remain open
qualified dependencies. This authoring checkpoint performs zero service
installation/modification, credential effects or provider calls. Git staging,
commit, push, release seal and Drive changes remain unperformed.
