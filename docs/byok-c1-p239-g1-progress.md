# P239 bounded G1 incremental progress witness

15 November 2026. **INSTRUMENTED DIAGNOSTIC SUCCESSOR; UNEXECUTED; HOLD.**
This is source preparation for Nayeon's independent validation/publication.
No batching success, performance improvement, historical regression PASS,
independent SEC03/SEC04 review or production admission is claimed. Full
unfiltered regressions remain **0/3**.

## Checkout and retained evidence

Only `D:\Nayeon\CODEX_P239_G1_PROGRESS_20261115` was used for repository writes,
on `byok-c1-p239-g1-bounded-progress-20261115`. Starting Git HEAD is exactly
`6093f499f7824188603488c11e350c69140efab4`, P238 draft PR #163; the initial
working tree/index were clean and no HEAD milestone tag was present. Local
history is shallow and `core.autocrlf=true`. `.codex/CURRENT_STATE.md` still
leads with 3 November Phase 10.2; Git is authoritative for this task. That
file remains unchanged because no product phase is completed here.

Exactly four additive paths: this document,
`scripts/p239_g1_progress_observer.py`, `scripts/p239_g1_progress_selftest.py`,
and `.github/workflows/p239-g1-bounded-progress.yml`. No original test,
historical pin, service/credential source, original/P234-P238 workspace,
release tag, workbook or dashboard was changed. No staging/commit/push.

User-supplied genuine P238 evidence:
[Windows run 43706340298](https://github.com/krismcan/Mark-LV/actions/runs/43706340298),
artifact `14158691903`, digest
`77D04B2611FFBE7C22E58C9BF6C36C2FB40138B64A156FC9FEEAB228AB8CE820`.
The instrumented method started and timed out at the original 180-second
deadline; diagnostic exit 124, `JOB_EMPTY_CONFIRMED`, original method incomplete.
There was source-before evidence and a start event, but no completed metrics or
unittest footer. Hosted synthetic tests were 33/33 PASS and the source guard
passed. Those facts **do not establish batching success or a speedup**. P237's
unchanged original also timed out at 180 seconds with UNCERTAIN cleanup. These
run facts are supplied anchors, not artifacts re-downloaded/authenticated here.

## Source boundary and call path

P239 loads the exact raw P238 helper only when SHA256 equals
`9F481C75764415FB4F829B3229D4989DAF574B01EA7AA82241747A7CF4FF0EB7`.
It compiles/executes those same checked bytes without text normalization or
import-time rereading. Local raw `git show HEAD:...` independently matched this
pin using .NET SHA256. The local CRLF working file instead hashes to
`64AD3FB5502D78DB51E77E53B5997FA78994B42229F0D8F66AFABB38D0FEF622`.
The loader deliberately refuses that disk representation; it has no fallback.
Neither P238's guard/constants nor an older source guard is monkeypatched.

P239's separate hosted guard requires the exact push branch/repository/host,
GITHUB_SHA=HEAD, full SHA1 history, raw LF checkout, clean tracked/index/untracked/
ignored inventory, no graft/replace refs, exactly one parent (P238), and exactly
four regular 100644 additions with committed bytes equal to disk. It also checks
the pinned P238 raw bytes and unchanged P234 blob/disk identity. Subsequent or
merge commits and extra/modified paths fail closed. Synthetic fake-Git guard
tests are explicitly not real source admission.

The separate child uses unchanged P238 `MANIFEST`, `Batch`, `verify_frame`,
`bootstrap`, `Job`, original P234 loader/classifier and source verifier. Before
interception, P234 authenticates full original P233 source
`096048db17c7c1f9402dfd16a7deb31e9ebdc81d`, raw tracked bytes, historical seals
and hook-free inventory. Original B raw tree authentication and 23 individual
native show witnesses are unchanged. Each intercepted B read still obtains a
fresh frame with the original 20-second bound, OID/SHA1, original normalized
pin, delimiter/size and exact original-show byte checks. No new cached result,
fallback transport, assertion or pin is introduced. A held PASS still requires
positive reads for all exact 23 manifest paths and reconciled final counters.

Only the exact P238 fixed-B `check_output` signature is intercepted; all other
calls delegate with their original arguments, bytes and exceptions. Aggregate
delegated counters describe **completed attempts**, including native errors,
with fixed show/cat-file/ls-tree/other categories. `other` includes unmatched
check_output calls and is not a claim that each is Git. Preflight uses native
Git outside interception; its cost is visible through stage timestamps, not
included in the instrumented delegated-call totals.

The suite loads the original single G1 with `unittest.TestLoader` /
`loadTestsFromName` and runs the original stdlib `TextTestRunner`. A small
subclass of P234 `JournalResult` overrides **only** `addSubTest`, calls super
first, then counts the callback. A private journal mirror observes original
start/stop records only after their original flush. `test_begun` means the
original unittest start callback was journaled; it does not locate the first
body instruction. A completed subtest callback is not whole-method success:
in G1 the final `hits == [target]` assertion occurs AFTER the subtest context.
Failing callbacks count as completions plus failures; skipped subtests use
addSkip and do not increment addSubTest counters. The inherited result retains
every failure/error/skip, and no observation substitutes for its outcome.

## Incremental witness and limits

The child exclusively creates one private append-only, unbuffered JSONL file
inside disposable GitHub-hosted RUNNER_TEMP. Each line is flushed. It contains
only schema 239, a fresh run/source/helper/parent binding digest, sequence,
fixed stage, monotonic seconds since the parent's pre-spawn origin, and fixed
nonnegative counters. No paths, argv, test parameters, secrets or PIDs occur.
The binding distinguishes stale/foreign runs; it is not a signature or a new
source authority. Raw authentication remains the independent source guards.

Stages are child_started -> source_verified -> baseline_verified ->
preflight_complete -> test_begun -> running samples -> test_finished ->
postflight_complete. Samples occur every 32 validated reads, every 32 completed
delegated attempts, and every completed subtest callback. No per-Git-command
logging or command timing is added. Counts between samples are lower bounds;
an in-flight call or unfinished subtest can be absent from the last snapshot.
There is no heartbeat during a blocking operation. Stage timestamps can narrow
where time was spent but do not identify an exact blocked native instruction.

Limits: 4,096 events, 2 MiB total, 2,048 bytes per line, bounded integer counters,
at most 4,096 validated reads and 23 subtest callbacks. The writer checks bounds
before appending and refuses reuse/truncation of an existing witness. A short
write can leave a torn final record; that is explicitly incomplete evidence.

After owned-process quiescence, the read-only parent parser hashes the complete
bounded raw file, accepts newline-terminated records sequentially and stops at
the first invalid record. It rejects duplicates (including JSON keys), missing
sequences, foreign bindings, regressions, impossible stages/count relations,
nonfinite clocks and resource overflows. A torn trailing line is never accepted,
even if its JSON is syntactically complete. The valid prefix's stage/counters
remain available with `records_valid=false`; completeness and PASS claims fail
closed. A valid but unfinished prefix has `observation_complete=false`. The
latest sample timestamp and first accepted timestamp for each fixed stage are
exported as samples, never as a completed test duration. Missing stages have
null timestamps; this exposes preflight boundaries without uploading raw events.
Missing/oversized/unreadable data cannot establish progress. Resource refusal
may leave no accepted prefix; the fixed receipt marks unavailable oversize data.

The separate supervisor retains P238's Win32 Job limits: kill-on-close, no
breakaway, 32 active processes and 1 GiB aggregate memory. It assigns the root
before a one-byte handshake enables source/Git work. The unchanged **180-second
whole-child budget starts before spawn**, includes setup, original execution
and child postflight, and polls every 0.1 second. It is not a hard real-time
scheduler guarantee. No timeout is increased. Each batch exchange remains 20
seconds; original delegated call bounds remain unchanged. Cleanup has the same
separate bounded five-second Job-empty query/root waits. A clean root with
residual descendants is instrumentation failure even if later cleanup succeeds.
Query, assignment, termination or handle failures cannot prove quiescence.

The child performs unchanged source post-verification on completion. After
confirmed Job emptiness, the parent also runs the original read-only P233
verifier, including on timeout, comparing against source-before when available.
This parent postflight is outside the terminated child's budget, never an
extension for its test. Missing source-before is reported as unavailable.

Public artifacts contain only explicit fixed-schema JSON files: source guard
hashes in fixed addition order, synthetic counts, candidate process/outcome,
progress prefix metrics and SHA256 receipts of fixed private evidence filenames.
Raw progress, original events, stdout/stderr, source maps and tracebacks are
never uploaded. Hashes allow comparison while private files exist; they do not
make disposed raw logs retrievable or independently reproduce a parse afterward.

Original P234/P238 classification remains authoritative for the instrumented
test outcome: failure stays exit 1; TIMEOUT is 124 only with verified containment
and usable observation/source evidence, otherwise 125; infrastructure/missing/
invalid evidence is 125. A zero-progress timeout preserves TIMEOUT and the
original classifier's 124/125 separately, while missing witness/source evidence
forces final diagnostic 125. A validated candidate-only PASS is always **HOLD 3**,
never zero. Observation completeness never upgrades any test outcome. Source or
observation errors retain a classified failure as failure/exit 1; they can
withhold a positive/timeout diagnostic classification. Recorded candidate exits,
classifier exits and final evidence exits remain separately visible.

## Open Failures & Prior-Issues Review

Reviewed the mandatory failure gate; P234 source verifier, result semantics and
controller; P236 original timeout/call-path map; P238 helper, tests, workflow and
review. Alternate original Git operations continue through native delegation;
no production permission/policy/confirmation/service route is added.

| Issue / evidence | Severity, cause and impacted boundary | Containment / tests / independent review / disposition |
| --- | --- | --- |
| P238 supplied run above | Material diagnostic gap: start without final metrics at 180s; where time was spent unknown. Job empty is not test completion. | Incremental prefix witness proposed; torn/missing/foreign/cap/count/clock adversaries authored, unexecuted. Independent validation pending; HOLD. |
| P237 G1 and other three original timeouts | Material regression/containment blockers; original timeouts reproduced historically, individual causes not all known; P237 cleanup uncertain. | No new original execution, timeout extension or causal closure. Exact budget and descendant adversaries retained; HOLD. |
| Four P76 wrong-branch historical failures | Material original regression; P236 traces exact-branch refusal through older successor routes. | No branch spoofing, assertion/pin changes or historical PASS claim; HOLD. |
| P96 service revoke/effect race | High security issue across old coordinator/alternate native actors; terminal-check/effect serialization not repaired here. | No service/credential edits or live effects; no new reproduction or closure claim; HOLD. |
| SEC03/04 and service authority | High architecture blockers; qualified independent decisions absent. | No installation/signing/credentials/providers/production admission; independent review missing; HOLD. |
| P238 transport/source/Job assumptions | Material trust path; its supplied 33/33 hosted synthetic/source GO does not prove G1 equivalence/performance. | Exact helper pin, original 23-blob semantics, all inherited tests plus new synthetic guard/result/parser/supervisor cases retained. Native rerun and independent source review pending; HOLD. |
| Local validation | Missing runtime evidence: interpreter inaccessible, shallow history, CRLF disk fails the raw helper pin. | No install/copy/network workaround, source guard weakening or raw source conversion. Host execution of exact LF review bytes required; HOLD. |

Disposition: authorized bounded diagnostic source work only. No release gate,
failure waiver, product phase progression, independent sign-off or seal.

## Validation and next safe steps

Executed locally: branch/HEAD/clean-index/tag checks; relevant bounded source
inspection; raw Git P238 helper SHA256 check; unchanged tracked/index checks;
new-file whitespace/static scope checks; PowerShell parsing of all four workflow
run blocks (zero errors). An initial block-extraction regex incorrectly consumed
the whole workflow; correcting that inspection regex produced the four valid
block parses, without changing workflow semantics. This is not YAML validation.

The authoritative host Python invocation was unavailable, and python/py/python3
were absent from PATH. Python syntax/AST, synthetic tests, compileall, original
G1, candidate G1, native Job containment, hosted workflow, affected/cross-phase/
full regressions and independent security review **were not executed here**.
There are **32 new authored synthetic tests plus the unchanged 33 inherited
P238 tests (65 total planned)**; no new runtime PASS is claimed. No G1 was run
on Kristian. Final full regression status remains **0/3**.

Nayeon should independently review the exact four-file delta and authenticate
an LF source view in an isolated review checkout. Do not normalize or bypass
the P238 pin to run this CRLF local view. On those exact reviewed raw bytes:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p239_g1_progress_selftest.py
```

Perform host syntax/compile checks with pyc directed to private temporary data;
record actual native exits and raw hashes. Do not run observe or original G1
on Kristian. After independent review and passing synthetic/native containment
evidence, Nayeon alone can publish the exact one-child/four-addition successor.
Its branch-specific push workflow checks source first, runs synthetic tests
before exactly one hosted G1 candidate, and always attempts fixed-JSON artifact
upload on failure. Inspect real timeout/outcome, Job quiescence, source equality,
last safe stage/time/counts, completeness flags and raw receipts together. Even
a complete observation and candidate PASS leave every C1 release hold open.

## Nayeon independent host evidence reconciliation — 15 November 2026

Following Codex's additive implementation, Nayeon executed focused Windows Python 3.12 tests from an isolated LF-preserving validation-only copy under `D:\Nayeon\P239_HOST_EVIDENCE_20261115\validation_only_lf`, leaving the Codex worktree unchanged. The P238 helper, inherited P238 selftests and original P234 controller came directly from the exact parent Git blobs. Its required P238 helper raw SHA256 `9F481C75764415FB4F829B3229D4989DAF574B01EA7AA82241747A7CF4FF0EB7` matched before execution; the active working tree's CRLF copy was never used to bypass the pin.

**Actual Windows native exit 0: 65/65 focused synthetic adversarial tests PASS; zero failures, errors or skips.** They comprise 33 original P238 synthetic tests and 32 new P239 progress-witness tests. Kristian host test log `D:\Nayeon\P239_HOST_EVIDENCE_20261115\p239_host_synthetic_final.log` SHA256 `D7C5F0BF03181811494B5DD248EC72719914B3B3509563989315FCC021142190`. Structured receipt `p239_host_synthetic_final.json` SHA256 `A963B5030AAAE5E7AC4D4EEE183B2D3DA949BBAA979364C5A77B91C7953D0313`. Both new Python files passed independent AST syntax parsing with native exit 0 and log SHA256 `ABC6629ABA01DB12B83F3C29C7DB6BF7F57AA7AB644F7C2FAB8E46CFEE2D4C41`.

The Codex implementation session was ended under the five-minute OM v2.1 watchdog **after all four files and static scope review were complete**, with no source resets or rewrites. These host results supersede Codex's sandbox-only statement that Python tests had not run.

No original G1, full-product regression, real credential, signed service, service effect or WinCred operation ran on Kristian. These are diagnostic harness tests only. **Real-key NO-GO, production HOLD, independent SEC03/SEC04 approval outstanding, full unfiltered regressions 0/3.**
