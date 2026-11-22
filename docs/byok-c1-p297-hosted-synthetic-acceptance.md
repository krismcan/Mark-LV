# BYOK C1 P297 hosted synthetic acceptance review

22 November 2026. Bounded documentation only; Codex is the sole writer.
Disposition: **HOLD; P297 hosted results PENDING**.
This review grants no runtime, real-key, service or production authority.

## Custody and four-path scope

User-supplied HEAD / fixed P296 parent: `4501090`, full identity
`45010901a7d1bd28fff03c83449c23d596c18bbd`; not rechecked with Git here.
The exact inherited baseline is **1,204 files**. No inherited edits are allowed.
P297 comprises exactly these four additions:

1. `.github/workflows/p297-hosted-synthetic-review.yml`
2. `docs/byok-c1-p297-hosted-synthetic-acceptance.md`
3. `tests/p297_hosted_synthetic/HostedReview.ps1`
4. `tests/p297_hosted_synthetic/P297SyntheticEntry.cs`

The three previously authored untracked files are preserved byte-for-byte.
Only this document is created in this turn; no SCM command or Git mutation.
No tests, compilation, launch, network, secrets or service operation occurs.
No local execution is authorized: the prior Application Control refusal stands.
There is no alternate launcher, bypass, retry or local qualification claim.

## Bounded CI admission and proposed evidence

CI is limited to a same-repository **draft pull request** in `krismcan/Mark-LV`.
Head branch: `byok-c1-p297-hosted-synthetic-evidence-20261122`.
Base branch: `byok-c1-p296-launch-custody-diagnostic-20261122`.
The base SHA must equal the full fixed P296 parent above.
Checkout selects the PR head SHA; a moving merge ref is not the reviewed input.
Workflow events are opened, synchronize, reopened and converted_to_draft.
The matrix is `windows-2022`, **x64/x86, two trials each**, four jobs total.
Each job has an eight-minute timeout; fail-fast is disabled.
Token permissions are `contents: read`; checkout persists no credentials.
Checkout disables submodules/LFS and uses fetch-depth 3.
Pinned actions are checkout `11bd71901bbe5b1630ceea73d27597364c9af683`
and upload-artifact `ea165f8d65b6e75b540449e92b4886f43607fa02`.
Artifacts retain summary and before/after source manifests for 14 days.
This workflow description is not approval to open a PR, push or invoke CI.

The runner independently checks GitHub-hosted Windows/win22, 64-bit PowerShell,
repository/owner, draft PR event, branch identities, matrix and working paths.
It accepts no arguments and rejects reparse paths and source escape.
Environment labels are defense in depth; local spoofing is not authorization.
The reviewed contract calls for fixed Framework v4.0.30319 compilers:
`C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe` for x64 and
`C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe` for x86.
The fixed synthetic entry/selftest must run only under separately approved CI.
**56 authored tests** are the declared synthetic inventory, not passing results.
Compiler selection, selftest execution and all four trial outcomes remain PENDING.

## Source and raw-byte acceptance

P296 implementation SHA256 pin:
`9EA16EEA4765BD10E7C2C47DB9C8BCD1100F37971DA7F3F2D584735D000BD48D`.
P296 test SHA256 pin:
`B3D8FBA3B5A16EBC2BD2FB6AF09C3463E28314583B71D287B38FDB2DA6FE3C01`.
These refer respectively to the two `tests/p296_launch_custody/` source files.
Git raw-byte custody uses the blob header plus exact file bytes for blob identity,
with SHA256 manifests before/after; text-normalized equality is insufficient.
The visible reader uses exclusive access, bounded reads and terminal failures.
A clean exact tree and unchanged 1,204 inherited files are acceptance conditions.
All four added paths must match the reviewed P297 head; no fifth path is admitted.
Equal hashes prove byte equality at observation, not execution or OS provenance.
They do not prove protected installation, file-object continuity or SCM custody.

## Failure ledger and separated outcomes

| Open issue | Preserved evidence and disposition |
| --- | --- |
| P292 first/second runs | 0/6 then 4/6; original causes remain open, HOLD. |
| P292 original third run | Run 44766866901: overall **3/6**, not repaired by P297. |
| Third run x64 trial 1 | Metadata **raw11**; independent **CLEANUP PASS**; HOLD. |
| Third run x64 trial 2 | Metadata **TIMEOUT**, **RAW_EXIT=UNAVAILABLE**; CLEANUP PASS; HOLD. |
| Third run x86 trial 2 | Start TIMEOUT/unavailable; stop **1062**, delete **0**; absence TIMEOUT/unavailable, **CLEANUP HOLD**. |
| x86 deletion | Deletion/absence remains unverified; persistence is not established. |
| P294 | Reported 6/6 was **static-only**, not service/runtime acceptance. |
| Launch disagreement | Prior Application Control refusal versus reported author success; custody/root cause unresolved. |
| P96 | **HIGH OPEN**; owner check/effect atomicity across older routes remains unproved. |
| P76/P211/P216 | Historical failures and alternate native-effect reachability remain unwaived. |
| Approvals/regressions | Qualified approvals **0/7**; accepted full regressions **0/3**. |

Raw signed child exit, unavailable exit, runner status and teardown are separate.
Keep raw11, timeout/unavailable, stop1062 and delete0 exactly as observed.
Successful teardown cannot erase launch, metadata, deadline or nonzero-exit faults.
Delete0/stop1062 do not independently establish absence or successful launch.
No synthetic fixture is an authentic reproduction or closure of these incidents.

## Design limits, watchdog and rollback

Event/job-based stream drain and retained-child handling are design mechanisms.
They require independent evidence for both stream EOFs, bounded collection,
retained identity, child exit, disposal and descendant/teardown completion.
A retained child must not become a PID-only reacquisition or guessed kill target.
Job/process labels and receipt ordering provide **no authentic SCM proof**.
Synthetic success cannot establish principal, service start, deletion or absence.
The runner's visible total budget is 360,000ms; CI supplies an outer job timeout.
Managed/event waits and cooperative budgets are not independent OS supervision.
A watchdog firing is failure evidence, never proof that teardown completed.
Preserve exact raw exit and cleanup receipts even when collection itself fails.

Rollback means stop admission, preserve artifacts and retain the fixed P296 base.
No rollback, deletion, service stop, process kill or Git operation is authorized here.
Any future runtime attempt requires separate scope and independent launch/cleanup
review; unexplained failures, missing receipts or custody drift remain HOLD.
Do not weaken tests, retry away failures or infer approval from a green matrix.

## Review boundary and restart

Reading was limited to the first 150 lines of P296 review, P297 runner and workflow.
The C# entry and later runner code were not inspected or executed in this turn.
Fixed compiler/selftest and lifecycle claims above are acceptance requirements;
this bounded review does not independently verify their complete implementation.
P297 hosted evidence remains **PENDING**; independent acceptance remains open.
**P96 HIGH; real-key and production HOLD; approvals 0/7; regressions 0/3.**
No milestone, seal, release, context refresh or workbook completion is asserted.
**No master workbook update until BYOK C1 is complete.**
