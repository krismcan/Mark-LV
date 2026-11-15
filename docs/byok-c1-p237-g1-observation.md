# P237: single original G1 Windows Git timing observation

15 November 2026. **DRAFT, OBSERVATION ONLY, RELEASE HOLD.** Single writer.
No hosted observation or Python test has been executed by this task. This is
an additive measurement proposal and implementation for human review, not a
timeout repair, original regression PASS, independent security approval or seal.

## Exact custody and permitted delta

Local worktree: `D:\Nayeon\CODEX_P237_G1_TRACE_20261115`; branch
`byok-c1-p237-g1-original-trace-20261115`; starting HEAD and required parent
`97dcc779ccceef9e5957fe81eec4823e89546c43`. Initially clean. Git matches the
task. `.codex/CURRENT_STATE.md` instead leads with the 3 November Phase 10.2
checkpoint; it remains unchanged because this is no completed product phase.
Local history is shallow, has no tags, and `core.autocrlf=true`; no local
historical raw-byte admission is claimed and no Git configuration was changed.

Exactly four additions, no historical edits:

- `scripts/p237_g1_git_timing_observer.py`
- `scripts/p237_g1_observer_selftest.py`
- `.github/workflows/p237-g1-original-git-timing.yml`
- `docs/byok-c1-p237-g1-observation.md`

The hosted observer admits only one immediate child of that exact parent,
with precisely these four added paths, clean including ignored files, full
history, no replace refs/grafts, HEAD equal to `GITHUB_SHA`, and the exact task
branch/repository on GitHub-hosted Windows. It compares each new disk file to
its committed raw blob and records their SHA256 values. An additional amendment
commit or unrelated change is refused. This requires Nayeon's reviewed, single
draft commit; Codex has not staged, committed or pushed anything.

The original P234 controller is authenticated against parent blob
`0c5781a28187bd5eddb5f7a3ff0d85c1a5430d6c`, and its raw disk bytes must match.
Its `SECONDS=180`, child code, imports, mocks, assertions and original test
source remain unchanged. The original P233 source is a separate full-history
checkout at `096048db17c7c1f9402dfd16a7deb31e9ebdc81d`. The unchanged P234
`verify_source` authenticates source HEAD, all tracked raw file bytes,
P233 runner SHA256, all fifteen annotated-tag pins/peels/ancestry, lifecycle
eligibility, clean source, no grafts/replacements, and `core.autocrlf=false`.
Its complete public-repository source witness is uploaded with a raw SHA256
receipt. Its repeat after the observation must produce identical bytes.

## Open Failures & Prior-Issues Review

Reviewed the mandatory engineering failure gate, P236 causal map, original
P234 controller/workflow and original G1 fixture/Phase 8.30 Git transport.
Detailed preserved receipts and cross-phase ownership analysis remain in
`docs/byok-c1-p236-original-timeout-causal-map.md`; this draft does not replace
that evidence or close its findings.

| Issue / source | Severity, reproduction and affected boundary | Cause / containment / review / disposition |
| --- | --- | --- |
| Four original P234 180-second timeouts, real run `43696205057-1` | Material regression blocker; original start-only journals, four timeout receipts | Actual per-method cause remains unknown. Measure only G1/M0; no timeout increase or repair. Independent causal review pending; HOLD. |
| Three uncertain descendant cleanups | Material containment blocker; preserved taskkill failures for G1/G3/G6 | Failure is genuine; survival/contamination unmeasured. One single on a fresh hosted runner, no retries or later singles. Nonzero taskkill/exception/already-exited root remains UNCERTAIN. HOLD. |
| Four original P76ScopeRefused failures | Material original regression; P236 traces public successor admission to original refusal | Original failures stay genuine. No branch spoof, source pin or assertion changes. HOLD. |
| Repeated immutable-history work in G1 | Observation hypothesis only; original 23 negative candidate-byte replays and authentic Git fallback | Repeated work is established by source, time distribution is unmeasured. No command/result substitution or successful-admission cache. No causal conclusion yet. |
| P231/P232 retained Tk owners | Historical harness defect documented in P233; distinct from these hook-free modules | Original P233 lifetime recovery preserved; no new owner/test adapter introduced. No causal connection asserted. |
| P96 revoke/effect race, SEC03/SEC04, unsigned service/broker | High architectural blockers; older actors and terminal/custody gaps traced in P236 | Still open. No production/service/consent/credential/policy changes or independent approval. HOLD. |
| Local Python and historical validation | Missing evidence; host Python inaccessible, no Python command on PATH, shallow Git/no tags/CRLF checkout | No install, copy, network/runtime workaround or expensive G1 run on Kristian. Synthetic/runtime validation pending. HOLD. |

**Disposition:** authorized GO only to prepare this bounded observational draft.
Product progression, release, seal, independent review and failure closure HOLD.
This is not an independent review; Nayeon's source/design review and actual host
synthetic evidence are still required before hosted execution.

## Process and measurement contract

Only original method:

```text
tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_every_candidate_source_byte_is_bound
```

The observer never imports the original test. A separate P237 worker starts
the unchanged P234 controller in `single` mode with the original source, fixed
test ID and a new external private `single-0.json`. P234 alone imports, loads,
executes and journals the original method. No discovery/full-suite/group run
occurs. The new worker implements the external wait/measurement, not a copy of
the original test. It retains the original **180-second whole-child wait**.
P234's unchanged `classify` interprets the original result and journal.

Measurements are separated:

- Standalone authentic P234 source-verification elapsed time before the single.
  This warms caches and is not the child's own preflight time.
- Actual original-child process exit, monotonic spawn duration, elapsed wait,
  deadline observation on timeout, cleanup duration and whole-child duration
  including spawn/cleanup. OS scheduling can make observation later than 180s;
  the configured wait remains exactly 180, including child verification/imports.
- Git `exit.t_abs` durations, counts, nonzero exits, incomplete process counts,
  sums and maxima grouped by a fixed safe operation whitelist. Unrecognized
  names become `OTHER`; missing names at a deadline become `UNKNOWN`.
- Original combined stdout/stderr/cleanup-log SHA256, result/journal SHA256,
  separate worker stdout/stderr SHA256 and actual worker native exit.
- Explicit `child_source_preflight_seconds=null`: **UNKNOWN**. No timing
  boundary exists inside the unchanged child. No journal polling estimate is
  mislabelled source preflight, body time or completed subtest count.

Git durations exclude Python/OS process creation and other non-Git work. Sums
can double count overlapping Git processes; they are not wall-clock fractions.
Aggregates include the child's own preflight/postflight Git work, not just its
test body. They cannot identify a specific subtest, source line, wait cause or
critical path. No optional process-tree/CPU snapshot is implemented.

## Trace2 custody, bounds and failure semantics

[Git's Trace2 specification](https://git-scm.com/docs/api-trace2.html) documents
an absolute existing directory target as one file per Git process, rather than
one shared append file. P237 creates that empty directory first and sets
`GIT_TRACE2_EVENT` only in a disposable worker environment, inherited by the
original child and its authentic Git processes. It does not modify Git argv,
transport results, mocks, global/local tracing configuration or historical code.
A separate `git version` probe must produce exactly one valid completed trace
in its own directory before the original is launched. The original source
transport inherits the environment; P234's environment filter preserves this
Trace2 variable. The preflight and postflight verification workers have no
tracing environment variable, keeping them outside the measured aggregate.

The worker environment drops inherited Git overrides/tracing, Python import
overrides, P134 authority, action inputs, and token/secret/password/API-key
variables; the parent environment is unchanged. Checkout uses no persisted
credentials; no WinCred, live key, service, provider or network API is called
by the experiment. GitHub's checkout/setup/upload actions remain normal hosted
infrastructure, with repository read permission only.

Each private directory is monitored every 0.5s: at most 20,000 regular files,
128 MiB total, and 16 MiB per file. Symlinks, reparse files and nested
directories are refused. Parsing additionally limits each event line to
256 KiB and all events to 500,000. These are sampled abort thresholds, not an
OS disk quota; writes can overshoot between samples. Reading/parsing is bounded.
Verification/probe workers have a 150s outer budget; the single worker has
270s to allow the original 180s wait plus bounded cleanup. The workflow has a
20-minute outer deadline. No unbounded retry, later original single or reuse of
existing output is supported.

Trace validation requires JSONL termination, one unique SID per file,
version/start/command/exit/atexit lifecycle, matching exit codes, finite bounded
durations and ordered exit timings. Duplicate/foreign sessions, malformed or
truncated data, a Git `git-trace2-discard` sentinel, missing traces and cap
violations are instrumentation failures. A well-formed unfinished Git process
can be counted only when the original actually timed out; it supplies no
invented completion time. A timeout always stays a timeout.

The existing taskkill fallback is used only against a still-live root created
by this observer and its descendants. Its output remains in the hashed private
log. Nonzero taskkill, exceptions, unsupported termination or an already-exited
root never become successful cleanup. `TREE_TERMINATED` means taskkill returned
zero, as in P234, not independently proved descendant quiescence. The retained
Popen root handle is used for the final root-only kill/wait. A supervisor abort
also fails closed. There are no later singles, whatever the cleanup outcome.

Raw traces, arbitrary command arguments, local paths, SIDs/PIDs, raw logs and
traceback text stay in a separate disposable runner-temp directory. They are
not uploaded or printed; there is no recursive cleanup/deletion. Public output
contains safe aggregates, a multiset of raw trace SHA256 values, original result
classification, fixed stage/error codes, native exits and hashes. The source
witness/manifest retain only public repository-relative source paths and fixed
tag names. Raw bytes cannot be recovered from uploaded hashes: deep raw-trace
forensics would need a separately reviewed retention/redaction design. No raw
forensic completeness is claimed.

Missing provenance, wrong source/controller, instrumentation errors and
incomplete results return 125. Original FAIL returns 1. A cleanly terminated
original timeout returns 124; uncertain cleanup returns 125, retaining TIMEOUT
and UNCERTAIN in the report. An otherwise valid original PASS returns **3**,
still HOLD. The workflow captures that real Windows native exit and its
combined outer log SHA256, exits nonzero and uploads public JSON with
`if: always()`. Early checkout/tool failures may have no JSON yet; the upload
step then explicitly errors rather than manufacturing an observation.

## Validation actually executed and restart point

Local PowerShell/Git checks established exact branch/parent, initial clean
state, shallow history/no tags, unchanged tracked paths and the stale context
file. `rg` is unavailable; bounded PowerShell reads were used. Checking the
authoritative host Python path was denied, and invocation was not recognized;
there was **no Python process/native test exit**. Python commands are absent
from PATH. No Python/package download, copied interpreter, privileged host
or alternate-runtime workaround was attempted.

The new selftest contains 33 synthetic test methods covering trace corruption,
lifecycle/time/identity attacks, caps, environment isolation, exact parent/delta,
real tiny synthetic-child stderr/native-exit capture, mocked 180s timeout,
cleanup failure, supervisor abort, original classification, and simulated
end-to-end PASS/HOLD, FAIL, UNCERTAIN timeout and admission/probe refusals.
These are **authored, NOT RUN**. Compile/compileall, original G1, full discovery,
hosted workflow and independent validation are **NOT RUN**. The workflow is
intentionally unavailable to an uncommitted parent checkout.

Executed final static checks: exact four-addition untracked envelope;
`git diff --exit-code 97dcc779ccceef9e5957fe81eec4823e89546c43 -- .`, empty
index, and `git diff --check` all exit 0. Each new-file
`git -c core.autocrlf=false diff --no-index --check -- NUL <path>` exits 1 for
the addition, with no whitespace errors; independent trailing-whitespace scans
find zero lines. All three embedded workflow PowerShell blocks parse without
errors using the installed PowerShell parser. This is not Python compilation,
YAML/GitHub workflow validation or runtime evidence. HEAD remains the starting
parent; no existing tracked path changed.

Nayeon's separate Kristian host check should execute only:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p237_g1_observer_selftest.py
```

Do not run the actual original G1 on Kristian. After source review and synthetic
host evidence, Nayeon can commit exactly these four paths in one reviewed child,
push the draft under their authority; the exact branch-scoped push trigger starts the single hosted observation without merging into the default branch.
This task performs none of those Git mutations. Inspect the native exit,
original result/timeout, cleanup certainty, source witness, aggregate counts and
receipts together. No result closes original P76/P96/SEC03/SEC04 holds or promotes
the full unfiltered release acceptance beyond **0/3**.

## Nayeon host-side source and runtime verification, 15 November 2026

The Codex sandbox-only validation statements above reflect its own restricted process; they are superseded where noted by Nayeon's independent host execution on Kristian. The host invoked `py -3.12 -B scripts/p237_g1_observer_selftest.py` and the **33/33 adversarial synthetic cases PASS**, original native exit **0**, ~0.565s. This suite includes the exact 180-second wait mock, generated child log/native exit, held PASS, FAIL, timeout/UNCERTAIN, first-stage provenance refusal and Git Trace2 corrupt/missing/duplicate protection. No original historical G1 test or full product regression ran on Kristian.

Nayeon separately executed real Windows Git Trace2 probes with the `GIT_TRACE2_EVENT` environment set to existing absolute host evidence directories outside the repository. Git version 2.56 wrote one per-process trace, and the P237 parser successfully reported one completed `rev-parse` with observed Git `exit.t_abs=0.042412` seconds, while excluding argv, path and SID fields. This is a timing-observer integration probe only, not a historical G1 performance result.

**Trigger correction:** the new unmerged workflow uses a `push` event **restricted exactly to branch `byok-c1-p237-g1-original-trace-20261115`**, plus an optional `workflow_dispatch` declaration. GitHub manual dispatch cannot normally start a new workflow absent from the default branch, and merging to default is forbidden. The restricted branch push is the intended first and only automatic run. The workflow and controller provenance both bind that branch and the commit SHA. It remains a diagnostic HOLD, with no service/WinCred/real-key execution and 0/3 full unfiltered regressions.

The independent host must retain exact native exit, source hash receipts and result logs after final source patch and staging. The earlier Codex statement “synthetic tests not run” refers only to Codex's sandbox and does not negate these real host results.

### Final Nayeon Windows host evidence receipt

On exact uncommitted P236 parent `97dcc779ccceef9e5957fe81eec4823e89546c43`, isolated P237 branch `byok-c1-p237-g1-original-trace-20261115`, host Python 3.12 ran the **final 33/33 synthetic suite PASS, native exit 0**, no failures, errors or skips. Raw host log `D:\Nayeon\P237_HOST_EVIDENCE_20261115\p237_host_33_selftests.log` SHA-256 `79442D791FADC8802EFCFD8E3546BE40D5C6C6EB1A5402DF53C4E440CFD2C6A3`. Test receipt `p237_host_selftests_result.json` SHA-256 `708760302BC397DE591EC41C22AF59CD98EC8EE274E9C2E84510E0A9BAA03111`. AST syntax checks for both new Python files **native exit 0**, log SHA-256 `4D48C33A29856D6DD4EA5DC7D5D8CA3CC1F464C27F0FB8F8AEB352DAEECD9432`. No historical G1 or full-suite Windows execution has yet been claimed by these receipts.
