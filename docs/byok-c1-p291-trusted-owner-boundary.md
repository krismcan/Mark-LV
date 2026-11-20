# P291: native observation cannot issue a development effect permission

20 November 2026. **NONDEPLOYABLE / TEST_ONLY. Runtime acceptance and independent
review OPEN. REAL-KEY NO-GO. PRODUCTION HOLD.** Original P96 HIGH remains OPEN;
qualified external approvals **0/7**, accepted full Windows product regressions
**0/3**. OM v2.1 as supplied in the engineering instructions; no external
approval is inferred. Codex is the sole implementation writer; Nayeon owns
independent CTO review, Git publication and native evidence coordination.

## Exact custody and scope

Initial branch: `byok-c1-p291-shared-revocation-effect-owner-20261120`.
Clean frozen HEAD: `3451352b57ef50dcc757580b43625af759712b79` (P290;
user identifies draft PR 210). No milestone tag points at HEAD. All **1,175**
tracked raw disk blobs matched their Git object IDs before work.
`.codex/CURRENT_STATE.md` still begins with historical November 3 Phase 10.2
notes. Git and this exact authorized scope control this isolated experiment;
the state file is unchanged. This is not a completed product phase, new
regression baseline or security seal.

Exactly five additions, with every inherited implementation, test and workflow
unchanged:

- `native_c1_successor/P291DevelopmentAdmissionSeam.cs`
- `tests/p291_boundary/P291BoundaryTests.cs`
- `tests/p291_boundary/HostedReview.ps1`
- `.github/workflows/p291-windows-boundary-review.yml`
- `docs/byok-c1-p291-trusted-owner-boundary.md`

Nothing is staged, committed, pushed, tagged, merged or published by Codex.
No PR is opened and no hosted job is launched here. No master Google workbook
or dashboard update is permitted until full BYOK C1 completion.

## New property and limits

P268 already implements the real in-memory P95 ledger and P96 effect interfaces
under one development owner. P269 already composes that owner with the actual
P267/P265 disposable Windows pipe host. Their 33 and 23 cases are reused as
separate unchanged executable suites. P291 does not replace either owner,
duplicate their implementations, add another ordering lock or claim their
separate locks are a cross-subsystem transaction.

The new seam privately owns a real `ComposedDevelopmentService`. Its only
nonprivate declared method, `RefusePeer(observation, request, borrowedTicket)`,
returns a denial enum. It makes **zero calls**, including zero `TestPrepare`,
effect, observation, callback or parser calls. It does not dereference, cache
or serialize peer objects. No method returns an approval or the host. Its sole
constructor is private. The companion test partial class contains only private
fixture operations and the hosted entrypoint. Every P291 file requires DEBUG,
absence of RELEASE, isolated assembly and explicit P291 opt-in, plus all frozen
P265/P267/P268/P269 development symbols.

The new hosted assertions add a boundary property beyond P269's existing
wire-denial/order tests: even a genuine native diagnostic receipt or a borrowed
genuine in-process development approval cannot cause the peer seam to invoke
preparation or dispatch. A compiled-IL whitelist allows only the Framework
compiler's constant-denial return sequence; any call, host field access,
allocation or alternate route in that method fails. Surface reflection rejects
any nonprivate preparation helper or host escape added to this class.
Adversarial callbacks throw if evaluated. These checks are experiments on this
assembly's exact code, **not** a CLR sandbox, protection against reflection or
arbitrary hostile code already executing inside the fixture assembly. Frozen
P268/P269 internal test methods still exist and are not production APIs.

The unchanged P290 diagnostic executes **separately** first on the disposable
runner. Only after its raw exit 0, exact identification/last-read/reversion
receipt, six captures and denial threshold are checked does orchestration write
its actual stdout to a temporary receipt file. P291 consumes those bytes as
untrusted peer data. A receipt SHA256 binds the bridge in `runtime.log`; the
before/after source and executable hashes bind the originating program.
No copied or hand-created positive native receipt is used. Forged receipt text
is explicitly a negative peer case. P290 token handles and private observations
never leave P290; **P291 does not claim a live token transfer, message-to-effect
transaction, independent client issuer, application authentication or consent**.

P291 also sends a real fixed frame to P269's actual Windows denial worker.
That frozen P265 worker requires its existing impersonation-level client mode;
the separate P290 program proves identification-level observations. No change
to those native contracts is made. The wire and peer seam are separate refusal
routes, not a newly implemented IPC dispatcher. PID, claimed SID, pipe name,
token-shaped values, fixed marker, arbitrary request objects, replay, constructed
approval and borrowed genuine tickets all remain data. SID equality is never
called application authentication. The runner's privilege level is unverified.

## Hosted tests and exact evidence contract

P291 has **11 top-level cases**: one constructor/surface/IL check; three
unprepared native-receipt/wire/refusal cases (SAVE, REPLACE, DELETE); six
boundary/control-order cases (SAVE/Revoke, REPLACE/Stop, DELETE/Fault, each
control-first and effect-first); and one cross-host borrowed-ticket case.
The unchanged P269 suite retains the complete 18 operation/control/order
combinations and five other cases; P268 retains all 33 meaningful adversaries.

Before any positive fixture preparation, the refusal cases require zero
journal writes, anchor writes, effect submissions, fixture effects and raw
approval consumption. A subsequent successful private fixture `TestPrepare`
proves peer attempts did not occupy its one-use preparation slot. The only
positive controls use P269 `TestPrepare`/`TestSubmit` in private fixture code,
the frozen literal four-byte marker `31 32 33 34` (null for DELETE), and actual
P268 in-memory ledger/effect interfaces. **TEST_ONLY, NOT real consent.**

Control-first cases require zero fake effects after Revoke/Stop/Fault. In
effect-first cases the actual P268 effect interface is held by a bounded event;
a separate peer thread must finish refusals within 200ms while that gate remains
held. Thus refusal cannot silently consult `TestPrepare` behind the effect gate.
Control publishes P269's admission closure before waiting for P268. Release then
requires TooLate, one fake effect, disposed lease, sticky MAY_HAVE_EFFECT and
RecoveryRequired, no replay and a joined worker. Event release is in finally;
threads are background and bounded. This timing check deliberately fails rather
than treating a slow/blocked refusal as a successful security result. Existing
P268/P269 tests retain the full ledger, reentry, timeout and failure proof.

The original P96 executable runs separately, unchanged: 15 cases must reproduce
the original final-StillCurrent / final-IsOwned / effect race for SAVE, REPLACE
and DELETE. Its successful negative-test receipt means **STILL-VULNERABLE
original**, not production closure. P291 never constructs that old coordinator
on its new effect path; original source supplies frozen interface/fixture types.

Workflow constraints: same-repository `krismcan/Mark-LV` draft `pull_request`,
exact P290 base branch and parent above, exact P291 head branch, checkout of
actual event PR head SHA, one direct single-parent child, exactly five added
paths and 1,175 identical inherited tree entries/raw blobs. Candidate total is
1,180 regular blobs. Disk raw hashes must match Git with filters disabled, and
SHA256 for every source is recorded before/after. Dirty/ignored files, links,
unexpected tree modes, output collisions or source drift cause HOLD.

Pinned checkout `11bd71901bbe5b1630ceea73d27597364c9af683` and upload
`ea165f8d65b6e75b540449e92b4886f43607fa02`; read-only contents permission,
no persisted credentials; Windows-2022, **3 x64 + 3 x86** independent trials,
10-minute job limit. No download, restore, Python setup, provider or secret.
Framework warning-as-error compiler uses explicit references and `/main` for
each of the five executables despite inherited multiple entrypoints. Every
missing P291 symbol, ALL and RELEASE configuration must fail with only CS1029
and the P291 guard, exit 1, no binary. P290 guard matrix is also preserved.
Each executable has a 60-second child deadline, ordinary hidden-window launch,
cleared allowlisted environment, no retry, bounded process-tree teardown.
No SCM registration/installation, service dispatcher, credential, WinCred,
DPAPI, account, policy, privilege or real-key operation is introduced or run.

Exactly eight allowlisted text evidence files are uploaded:
`source-before.sha256`, `source-after.sha256`, `compiler.log`,
`compiler-exits.txt`, `test-binary.sha256`, `runtime.exit`, `runtime.log`,
`scope.log`. They contain raw compiler/runtime exits, diagnostic codes/raw-log
hashes, expected guard labels, exact successful nonidentifying receipts and
source/binary hashes. No binaries or identity data are uploaded. Unexpected
runtime output is retained only in disposable build custody and represented by
hashes/HOLD; raw nonzero exits are still recorded. Failed launch has unavailable
exit and NO_RETRY. A timeout is a failure, never a skip or pass.

## Open Failures & Prior-Issues Review

Reviewed before implementation: failure gate, P268/P269 report and actual
sources/tests, P290 report/native diagnostic/harness, original P96 report and
negative source. P281 principal/store decision and relevant P216 RFC were also
read for the unresolved deployment boundaries. Prior runtime reports remain
historical; user reports six P290 hosted passes, not independently retrieved
or rerun by Codex. No low-risk waiver is proposed.

| Issue / source / severity | Cause, affected callers and evidence | Containment, repair/test, independent review and disposition |
| --- | --- | --- |
| P96 original HIGH OPEN | Final approval check and effect lack common revocation owner; original SAVE/REPLACE/DELETE can effect after revoke during fourth lease probe | Frozen 15-case negative retained separately; P268 repair is development-only. Qualified production owner/effect proof absent. Independent closure OPEN; HOLD. |
| Identity-to-permission confusion HIGH OPEN; P290/P269 | Same-user OS token, exact pipe read, PID/SID/name or borrowed fields cannot distinguish protected client code/user-present consent; all prospective peer admission callers affected | New constant-refusal seam plus native receipt, borrowed-ticket, hostile callback, zero-ledger/effect and held-gate tests; no positive peer route. Hosted runtime/reviewer OPEN; independent issuer NO-GO. |
| Separate P267 transport/P268 owner locks HIGH production gap; P269 | Worker can fail after admission observation; transport closure and local fake transaction have independent ordering | Preserve all locks and admission latch, no atomic cross-owner claim. Existing 23 cases plus new contention checks; common production transaction/issuer design absent. HOLD. |
| Journal/anchor/effect/restart uncertainty HIGH; P268/P96 | Separate writes and possible effect are not one durable transaction; alternate recovery/restart callers need protected custody | Existing 33 cases retain InFlight, non-reentry, cleanup, bounded control and sticky uncertainty proof. No native store or cross-process recovery added. Qualified review/evidence OPEN; HOLD. |
| P269 prior hosted SafeHandle failure, material historical harness defect | Async wait handle was disposed before EndRead; traffic helper affected | Frozen repair retains handle through EndRead with timeout cancellation. P291 preserves this lifetime ordering; old 23 cases rerun hosted. No local native replay; independent current runtime OPEN. |
| P265/P285 completion/event disposal incident, historical HIGH; P290 review | Framework async completion signaling can race caller-owned event disposal on shared connect/read/write paths | P286's callback-owned cleanup repair is a separate successor, not composed into frozen P269/P265. Do not claim its assurance transfers here. P291 does not repair frozen transport; six fresh hosted trials must fail closed on any crash/cleanup failure. No production claim or waiver; qualified transport disposition remains OPEN/HOLD. |
| Installed service principal/SCM image signer/ACL/profile HIGH OPEN; P281/P216 | Frozen NayeonV1ByokCustody LocalSystem gate conflicts with proposed virtual account/name; no installed protected principal/image/profile evidence | No gate, account or SCM change; SEC03/SEC04 qualified owner must resolve exact principal and installation contract. Protected DPAPI/WinCred store/cross-process recovery absent. HOLD. |
| ncalrpc + protected broker HIGH missing design; P290 | Account authentication does not authenticate installed client or user presence; same-user hostile/delegated processes remain | CONDITIONAL selected architecture only, requiring independently protected same-user client and consent broker. No custom signature, SID issuer or RPC implementation invented. Independent qualified design OPEN; HOLD. |
| P76/P211/P216 unwaived acceptance debt | Original P76 four failures, P211 test02, P216 test02/test06 and historical native effect expectations remain unresolved | No old source/test modified, skipped or recast as passing. Qualified acceptance owners retain closure; HOLD. |
| External/product evidence HIGH missing | Focused host diagnostics cannot replace GOV01/02, SEC03/04, REL05/06/07 or full Windows product suites | Approvals 0/7; full product regressions 0/3. Independent Nayeon/external review OPEN. REAL-KEY NO-GO / PRODUCTION HOLD. |
| Stale context, bounded custody mismatch | Historical Phase 10 state does not describe this P290 parent | Exact branch/HEAD/clean/raw hashes verified. State left frozen; no product-phase completion or baseline promotion. Nayeon review OPEN. |
| Local tooling failures, contained | `rg` unavailable (CommandNotFoundException); first compile argument array incorrectly joined /main and /out, CS1555 exit 1 before source validation | Switched to Git inventory/Select-String; corrected parenthesized compiler arguments. Raw failed log/exit preserved at temp path below; no downloads, bypass or EXE execution. Final matrix required below. |
| Final local wrapper parse failure, contained | A PowerShell foreach statement was piped without an enclosing expression; EmptyPipeElement parser exit 1 occurred before any compiler call | Tool transcript retains raw parser error; changed only local wrapper to collect hashes in an array. Corrected final matrix succeeded. No repository source or hosted-script change needed. |
| Static integration corrections, contained pre-runtime source defects | Copied workflow name replacement altered base filter; proposed Identification wire would fail frozen P265's Impersonation-only observation contract | Corrected only new workflow/client mode. P290 remains separate Identification diagnostic. Exact branch static witnesses and final compile repeated; runtime still OPEN. |

**Disposition: GO only for the explicitly authorized additive, nondeployable
source candidate and compile/static review; HOLD for runtime acceptance,
independent security closure, product phase advancement and release.** The
material open findings are contained by refusal and by no production call edge;
they are not waived or declared repaired. Five-minute meaningful-progress
watchdog applies; all local compiler calls completed within seconds and the
first failure was inspected immediately. No native process was launched.

## Local validation and handoff

Only Git/read-only source, PowerShell AST/static checks and Framework C# compile
smoke are authorized on Kristian. The hosted script was parsed as data, never
executed or dot-sourced locally. No Python, generated EXE, pipe worker, SCM,
credential/provider or real-key operation was run. Full unittest discovery,
compileall and three full product regressions are not claimed or substituted
with compile receipts.

Initial failed compiler custody:
`%TEMP%\p291-compile-20261120-122014` (CS1555, raw exit 1).
First corrected matrix:
`%TEMP%\p291-compile-20261120-122045` (ten positive exit 0; eighteen deliberate
P291 negatives exit 1 / CS1029). Later integration edits require final compiler
and static receipts recorded below. These are author checks, not independent
approval. Nayeon must review the exact final five additions and genuine hosted
evidence after independently publishing the single-child draft. Do not execute
`HostedReview.ps1` or any generated program locally.

Final code compilation evidence:
`%TEMP%\p291-final-compile-20261120-122528`. Both x64 and x86 compiled original
P96, unchanged P268 tests, unchanged P269 tests, unchanged separate P290 and
new P291: **10 positive builds, raw exit 0, no diagnostic codes**. The full
P291 missing-symbol/ALL/RELEASE matrix and P290 missing-symbol/ALL/RELEASE matrix
produced **28 expected failures, raw exit 1, only CS1029**, with the required
guard and no executable output. Individual raw compiler `.log`/`.exit` files
and `source.sha256` are retained. `summary.log` SHA256:
`880BE964E239B7DA0EBF59891CDC3106467AD35C79A474A95B087FE4F7C5674D`.
No generated executable was loaded or executed.

Static receipts: `%TEMP%\p291-static-20261120-122427`: hosted PowerShell AST,
exact workflow/topology witnesses, constant refusal source surface, all 1,175
raw inherited blob hashes, exactly five untracked additions, zero tracked or
index edits and whitespace PASS. Its full source manifest predates this final
documentation receipt append; final five-file manifest is refreshed at handoff.
`git diff --check` and added-file no-index whitespace checks both apply.

Final code/workflow raw SHA256 pins (the document is deliberately not self-pinned):

| Path | SHA256 |
| --- | --- |
| `native_c1_successor/P291DevelopmentAdmissionSeam.cs` | `DEEED5BE520825AD22BC50E7B8B2F530E966776991A21E003AB9B508D0D49E26` |
| `tests/p291_boundary/P291BoundaryTests.cs` | `7D58893C7565C1E52CCF02700F2A6DCAD35E6D524CAA5278402B102781308E85` |
| `tests/p291_boundary/HostedReview.ps1` | `B2C17EC4926A0B9E64168CD97551B7956D5E7AF7129868F2286EA8B1BD116307` |
| `.github/workflows/p291-windows-boundary-review.yml` | `22C07A1F3FE9F5D3C1914629B45C043E8C2D9B24B53A3866A04898AA4A4E23A1` |

**Author validation complete for source/static/compiler scope only. Hosted
P291 runs: 0/6; runtime IL/concurrency/wire assertions NOT RUN. Independent
source/CTO verdict: OPEN. Production issuer: NO-GO.** No green runtime or
product regression receipt is inferred from these local checks.

## P292 required qualified review and proof

P292 must begin with qualified Windows security review of the **hosted service
and protected client/consent-broker design**, including same-user adversary,
delegated handles, code/update identity, per-call ncalrpc authorization,
operation/candidate/session/epoch/expiry-bound one-use consent and rejection of
borrowed/replayed proofs. Source-bound GOV/SEC/REL decisions must identify the
reviewed commit and approved principal. If independent protected issuer
provenance cannot be demonstrated, record NO-GO; another synthetic issuer or
SID/name/signature snapshot is not an acceptable substitute.

Separately require the actual P96 successor effect-owner proof: one trusted
non-reentrant owner for issue, revoke/stop/fault, one-use admission, durable
InFlight pair, continuous custody and final effect dispatch for every
SAVE/REPLACE/DELETE/alternate route. Revoke winning must mean zero effects;
dispatch winning must remain TooLate with sticky MAY_HAVE_EFFECT/recovery across
fault, process crash and restart. Trace older dispatch/recovery callers and
cross-process state, not only the new host. Retain the original expected-failing
security proof as STILL-VULNERABLE until qualified production closure exists.

P292 review does not itself authorize installation or native credential tests.
Any future controlled service/principal/store experiment needs its own bounded
authorization and qualified design, with exact SCM image signing, service ACL,
profile, LocalSystem-versus-virtual-account resolution, SEC03/SEC04,
DPAPI/WinCred protected-store isolation and durable cross-process recovery.
P291 supplies none of those authorities. Production and real keys remain held.
