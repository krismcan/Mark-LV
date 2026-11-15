# P235 offline evidence reconciliation candidate

Date 2026-11-15. Product and qualified-release disposition **HOLD**.
Independent source/security review and authoritative runtime validation remain open.

## Scope and checkpoint

Authorized workspace `D:\Nayeon\CODEX_P235_EVIDENCE_RECOVERY_20261115`, branch
`byok-c1-p235-codex-evidence-recovery-20261115`, starting HEAD
`bc02f95f9dd241c5dace3129e918324e55dd6ee6`.
Git inspection confirmed the branch and HEAD, shallow history, and an empty local
tag inventory. `.codex/CURRENT_STATE.md` starts with older Phase 10.2 candidate
status that conflicts with this checkpoint. Git and the explicit P235 task govern
this bounded work. The pre-existing untracked `docs/p235_codex_task.md` is preserved.

Three additions implement the authorized offline recovery scope.

- `scripts/p235_windows_evidence_reconcile.py` provides the standalone CLI.
- `scripts/p235_evidence_selftest.py` contains 22 synthetic test methods.
- This document records the evidence contract, failure gate and validation limits.

The review covered the P234 runner, its synthetic tests, workflow and phase
document, the current context, repository instructions and engineering failure
gate. Implementation stays within new P235 files. Historical tests, security
assertions, source pins, manifests, workflows, context and Git refs are preserved.
The reconciler imports standard-library modules only. It reads supplied artifacts
and writes one new report. It has no source execution, extraction, subprocess,
network, provider, credential, policy, confirmation or production-effect route.
Synthetic self-tests launch this new CLI with fake data to check its real exit.

## Open Failures & Prior-Issues Review

The run findings below come from the user's 2026-11-15 authenticated-run summary.
Genuine downloaded ZIPs have not been supplied to or reconciled in this checkout.
Synthetic reproduction checks reporting behavior. Runtime execution of those
checks and independent review remain pending.

| Issue and evidence | Severity, root cause and affected boundary | Containment, test obligation and disposition |
|---|---|---|
| Four P234 original failures, group/index 0/1, 0/2, 1/3, 6/3 | Medium historical/current-topology incompatibility. User reports `P76ScopeRefused` for the wrong exact P76 prototype branch. Affects historical scope admission and interpretation of original test results. Complete repair scope remains unapproved. | Preserve negative tests and original nonzero results. Synthetic failure/error and false-green-driver adversaries cover reporting only. Independent repair review open. HOLD. |
| Four P234 diagnostic timeouts, group/index 1/0, 2/3, 3/0, 6/5 | Medium diagnostic incompleteness. Diagnostic exits 124. Timeout root causes remain unresolved. Cleanup is UNCERTAIN at 1/0, 3/0 and 6/5, TREE_TERMINATED at 2/3. Affects original-process completion and process-tree assurance. | Preserve timeout and actual OS exits separately. Synthetic 124/125, interrupted and missing-footer cases provided. No retry, cleanup action or waiver performed. HOLD. |
| P233/P234 collection versus success reporting | Medium reporting ambiguity. Assignment coverage can be complete while original results fail or remain unfinished. | Reconstruct original receipts, every group driver and the certificate. A non-PASS outcome adds an unresolved hold. Full 3629/54/3575 synthetic inventory provided. Independent validation open. HOLD for release. |
| P231/P232 lifetime and P233 recovery history, as reviewed in P234 documentation | Medium historical case-ownership issue with retained Tk cases. Affects teardown and reliability of diagnostic interpretation across process lifetime. P235 has no test execution route. | Preserve P233 ownership/source witness and keep all 3575 other methods retained-not-executed. No claim of a new lifetime repair or full regression. HOLD for broader closure. |
| P96 revocation/effect race, SEC-03 ownership, SEC-04 broker | High provisional triage for material open security issues from the user task. Detailed causes and closure evidence are unavailable in this evidence-only scope. Affects production authorization/effect ownership. | Explicit unconditional release holds in every report. Independent security review remains open. No production repair or waiver. HOLD. |
| ZIP and JSON evidence trust | High input threat. Receipts can be forged together with their data, and hostile archives can consume resources or alias paths. | Bounded in-memory reads, flat member allowlists, duplicate/path/type rejection, independent receipt reclassification and exact certificate comparison. Synthetic adversaries supplied. External authenticity still requires independent evidence. HOLD for provenance approval. |
| Local runtime availability | Medium validation blocker. Authoritative host Python cannot be resolved/executed through this sandbox. | Launch attempted and failed before Python started. Static work only thereafter. Independent host validation remains required. HOLD. |

GO applies only to the explicitly authorized additive implementation. Material
failure closure, product progression, security seals and release remain HOLD.
No low-risk deferral or waiver has been requested or granted.

## Identities and genuine run context

The user identifies P234 Actions run **43696205057**, attempt **1**, draft PR
**159**, with controller commit `bc02f95f9dd241c5dace3129e918324e55dd6ee6`.
The inspected P234 runner's `SOURCE` and workflow authentic checkout are
`096048db17c7c1f9402dfd16a7deb31e9ebdc81d`, the unchanged P233 test source.
Manifest `source.head` must match that tested-source identity. The report exposes
both expected identities. ZIP contents contain no independent controller-commit
attestation, so P235 cannot authenticate the controller commit from these files.

User-reported genuine discovery contains 3629 unique methods, with 54 singles
in nine groups of six and 3575 retained under P233. All nine jobs completed.
The 54 outcomes were 46 PASS, four FAIL_OR_ERROR and four TIMEOUT, with zero
unexecuted and four uncompleted methods. Certificate coverage was complete,
diagnostic collection was incomplete, and aggregate driver exit was 125.
Full-product regressions remain **0/3**. These facts are supplied context.
The synthetic genuine-shape fixture checks the same cardinalities and hold
conditions using generated IDs and fake receipt bytes.

## CLI

Run using an available authoritative Python 3.12 interpreter from this workspace.
The artifact directory must contain these eleven flat downloaded ZIP files.

```text
p234-plan-1.zip
p234-group-0-1.zip ... p234-group-8-1.zip
p234-certificate-HOLD-1.zip
```

`p234-certificate-HOLD.zip` is also accepted. Exactly one certificate variant
must exist. Having both is ambiguous and returns 125. Each ZIP contains the
original flat P234 output files including `SHA256SUMS.txt`. Nested wrapper
directories are rejected. Other directory files are ignored.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p235_windows_evidence_reconcile.py --artifacts .\downloads --output .\p235-report.json
```

Default expected run identity is `43696205057-1`. `--run-id` may explicitly
select another numeric run with attempt 1 and the same fixed tested source.
Artifact naming for other attempts is outside this CLI contract.
An explicit expected run establishes the comparison target. Caller input
does not authenticate that a download actually came from GitHub.

Optional `--github-digests .\github-digests.json` accepts a JSON object mapping
exact ZIP filenames to GitHub ZIP digest strings, either 64 hexadecimal characters
or `sha256:` followed by 64 hexadecimal characters. Missing fields, missing digest
values, malformed values and malformed JSON produce `UNAVAILABLE_OR_MALFORMED`.
They do not impose a fictitious mandatory GitHub digest format on an absent value.
A well-formed differing digest yields `MISMATCH` and evidence error 125.
A matching digest yields `MATCH`. Every report retains the locally computed
ZIP SHA256 values. An unreadable or oversized metadata file is an input error.
The CLI exits 125 if it cannot read an explicitly supplied metadata file.

The output path must be new and its parent must already exist. Creation is
exclusive. Existing files and symlinks at that path are refused. The completed
JSON report receives the platform's read-only file flag. The owner can change
that flag later. It provides no signature, tamper-proof storage or authority.
Output/permission failures return 125, and a failed write can leave a partial
report. Consumers must check process exit and valid JSON before using a report.
The reconciler preserves input artifact bytes and performs no action described
inside those artifacts.

| Exit | Meaning |
|---|---|
| 1 | Consistent diagnostic evidence with an original failure/setup block, or a wholly green diagnostic whose qualified release remains HOLD. |
| 124 | Consistent timeout evidence with TREE_TERMINATED cleanup, while release remains HOLD. |
| 125 | Evidence/infrastructure error, interrupted original receipt, uncertain tree cleanup, or another reconstructed P234 driver 125. Check `evidence_consistent` and the error fields. |
| 2 | Command-line syntax error from argparse. |

There is no exit 0 release approval route. `original_driver_exit` preserves the
independently reconstructed P234 driver result once all evidence checks succeed.
`reconciler_exit` additionally reflects the unconditional qualified-release hold.
Exit 125 with `evidence_consistent=true` can faithfully preserve a P234 uncertainty.

## Validation contract

1. Each input ZIP is a regular non-reparse file, read once with a 32 MiB cap.
   Before ZipInfo allocation, the end record must describe a single-disk archive
   with at most 64 members and at most 64 KiB of central-directory metadata.
   ZIP64, appended data and inconsistent directory layouts are refused.
2. Every member must have an exact role-specific flat ASCII name. Traversal,
   absolute/drive/UNC/alternate-stream names, wrappers, NUL aliases, duplicates,
   symlinks, directory attributes and encryption are refused. Only stored and
   deflated compression is supported. Each expanded member is capped at 8 MiB,
   each archive at 32 MiB expanded, and compression ratio at 200. CRC checks
   remain active. Conservative bounds can reject unusually large legitimate logs.
3. `SHA256SUMS.txt` must cover every other member exactly once in P234 sorted
   order, using uppercase SHA256. LF and native Windows CRLF are supported.
   Missing, changed and extra receipt entries are rejected.
4. JSON is decoded as UTF-8 data with duplicate-key and nonfinite-literal refusal,
   a nesting bound of 64 and member-size bounds. No pickle, eval, dynamic source
   imports, object construction hooks from input or deserialization callbacks
   supplied by input are used. Typed integer/Boolean checks prevent equality
   aliases such as `true` being treated as exit 1.
5. The canonical manifest must reproduce all 3629 unique IDs, original order hash,
   deterministic P233 module shards, exact 19/35 eligible counts, sequential
   nine-by-six assignment, hook-audit IDs and 3575 retained owners. Source witness
   paths and SHA256/tag witness shapes are checked. P233's reviewed fixed script
   SHA256 is enforced. Source identity hashes are recomputed from canonical bytes.
6. Plan and all groups must contain matching original discovery rows, a matching
   successful discovery process/log receipt, identical manifest bytes and bound
   source/manifest/run identities. Planning remains inventory-only with zero tests.
7. Every method's standalone `single-N-process.json` must match its driver's
   process object, exact raw log name/hash, diagnostic exit and cleanup state.
   Original result JSON, callback journal and actual process exit reconstruct the
   P234 summary independently. Failure, error, combined failure/error, unexpected
   success, skip, expected failure, timeout, interruption, setup block and
   infrastructure absence retain distinct report classifications. An original
   footer cannot make a timed-out process green. Unsupported or contradictory
   receipts become evidence errors.
8. Group driver exits, collection completeness, executed/completed/setup-blocked
   IDs and the entire aggregate certificate are compared against reconstruction.
   Exact certificate coverage includes methods, receipts, assigned/executed/
   completed/setup-blocked/unexecuted/uncompleted IDs, retained count, run identity,
   manifest hash and aggregate exit. Coverage completeness and success remain
   separate fields. Every full-discovery entry is retained in the JSON report,
   including each of the 3575 `RETAINED_NOT_EXECUTED` entries.

## Security limitations and next gate

Internal receipts and matching source identity hashes establish consistency among
supplied bytes. Attackers can fabricate an entire internally consistent bundle.
Source witness hashes and fifteen tag object/peel pairs are self-reported. P235
does not fetch Git objects, compare the complete source witness map against an
independent immutable checkout, verify GitHub job identities or authenticate an
artifact signature. ZIP digest metadata is caller-supplied and optional. Even all
MATCH values leave `full_provenance_approved=false` and
`independent_evidence_verified=false`. The synthetic source deliberately contains
fake tag witnesses to exercise this distinction.

Raw logs are digest-bound opaque evidence. P235 does not infer a P76 causal repair
from text or trust log text as authorization. A missing original footer receives
an interrupted/infrastructure classification using the process and journal.
Unresolved original test failures and timeout causes remain open. The report's
unconditional P96, SEC-03, SEC-04, independent review and 0/3 regression holds
cannot be cleared through artifact contents, CLI flags, successful diagnostics
or external digest claims. Historical P76 negative tests remain preserved.

Next gate is Nayeon's independent source/security review, authoritative host
execution of the focused synthetic suite and syntax checks, followed by offline
reconciliation of independently obtained genuine artifacts. Authenticate controller
and tested-source identities and artifact origin through independent evidence.
Resolve material failures and timeout/cleanup uncertainty through separately
approved work before any release consideration. All three full-product regression
obligations remain open. This additive candidate has no production-readiness claim.

## Local validation record

- The self-test command was attempted with authoritative host Python and
  `-B scripts/p235_evidence_selftest.py`. PowerShell process exit **1** reported
  `CommandNotFoundException` before Python started. There is no Python/test-suite
  exit code and no executed/passed self-test count. Earlier executable access
  inspection also reported access denied. No interpreter or package was installed,
  copied or obtained through a network/host workaround.
- The 22 synthetic methods are authored for green-held evidence, genuine-shape
  counts, exact full inventory, original classifications, process/log/result/journal
  mismatches, false-green drivers, discovery/source/certificate mismatches,
  hostile ZIPs, bounds, duplicate/deep JSON, optional ZIP digests, CLI exit 1,
  read-only report creation, input preservation and existing-output refusal.
  Their assertions remain unverified until host execution.
- `git diff --check` returned **0** during implementation. Because additions are
  untracked, a separate final scan checked all three new files for trailing
  whitespace and conflict markers and returned **0**, with zero findings.
  `git diff --exit-code HEAD` and `git diff --cached --exit-code` both returned
  **0**. Final status contains these three additions and the preserved pre-existing
  task file. A workspace search found zero P234 ZIP artifacts.
  Additional per-file `git diff --no-index --check` invocations returned **1**
  for the new-file comparisons and emitted only LF-to-CRLF working-copy warnings.
  Runtime, compileall and historical/full regressions
  have not run in this sandbox. No source/release GO is inferred.

Host validation commands follow. Run from the authorized P235 workspace.

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p235_evidence_selftest.py
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B -c "import ast,pathlib; [ast.parse(pathlib.Path(p).read_bytes()) for p in ('scripts/p235_windows_evidence_reconcile.py','scripts/p235_evidence_selftest.py')]"
git diff --check
```

Record native exit codes, suite totals and independent findings before changing
the validation disposition. Preserve earlier evidence and rerun focused checks
after any material repair. This task performs no staging, commit, push, merge,
tag, deployment, workbook update or real-credential action.


## 15 November 2026 — subsequent Nayeon host verification (supersedes sandbox-only validation limits above)

The earlier Codex sandbox could not resolve its hard-coded Python path and did not have the genuine ZIP evidence. That historical failed invocation is preserved above. Nayeon independently completed host-side validation afterwards, without changing historical product code or test assertions.

- Verified clean P235 source parent `bc02f95f9dd241c5dace3129e918324e55dd6ee6` on isolated `byok-c1-p235-codex-evidence-recovery-20261115`.
- Host Python 3.12 `py -3.12 -B scripts/p235_evidence_selftest.py -v`: **22/22 PASS**, native exit **0**, 16.375 seconds. Evidence log: `D:\Nayeon\P235_HOST_EVIDENCE_20261115\p235_host_selftest_v2.log`, SHA-256 `963A2198920B3944323F7A0B03659AF21C011209F250DFEF0AE2E59F1C15879B`. AST syntax checks for both scripts: **exit 0**, log `p235_ast_v2.log`, SHA-256 `3D5FFD57EBC7668C7D8FA44677099AB771BC0D969516B3F6F8FEBA5B44978AEC`.
- First host wrapper attempt failed prematurely because PowerShell `ErrorActionPreference=Stop` treated normal `unittest -v` stderr as a terminating shell error. It did not establish a Python test failure. The corrected wrapper completed and retained its own SHA256-backed output.
- Nayeon directly retrieved all **11 actual P234 run #43696205057 artifact ZIP files** from the GitHub connector to `D:\Nayeon\P235_HOST_EVIDENCE_20261115\p234_artifacts`. No archived input was extracted or changed by the reconciler.
- Ran `py -3.12 -B scripts/p235_windows_evidence_reconcile.py --artifacts <evidence-artifact-directory> --output <new-host-evidence-report>` on those actual Windows artifacts. **Native exit 125 (correct HOLD)**; **evidence_consistent=true**, no evidence errors, coverage complete, diagnostic collection incomplete, independently reconstructed original driver exit 125. Actual counts **3629 discovered / 54 assigned / 3575 retained**, original method outcomes **46 PASS / 4 FAILURE / 4 TIMEOUT**, matching P234.
- Genuine report `D:\Nayeon\P235_HOST_EVIDENCE_20261115\p235_real_p234_report_first.json` SHA-256 `C46ABB551E885EB31C4CDC0B05D46B3B2B931F5E5D7BF6BD915AA02317DAE3FE`. Standard-output log SHA-256 `F9FA665F5FEA82C91166FDAD51889A4E8CFA7D5B87607A0EB59064531C168E6C`. Original 11 ZIP files retained under host evidence directory.
- The genuine result continues to list `ORIGINAL_NON_PASS_RESULTS_UNWAIVED`, `TIMEOUT_ROOT_CAUSES_OPEN`, `PROCESS_TREE_CLEANUP_UNCERTAIN`, `P96_REVOCATION_EFFECT_RACE_OPEN`, `SEC_03_OWNERSHIP_OPEN`, `SEC_04_BROKER_OPEN`, independent review open and **0/3 full unfiltered regressions**. The hosted P234 certificate remains HOLD, not a release pass.

This host-side verification supersedes only the earlier **unexecuted-tests / genuine-ZIPs-unavailable** statements; it does not elevate the candidate into a qualified independent security review, cryptographically authenticated GitHub provenance or production admission. **P235 diagnostic candidate reviewed for exact additive scope only. BYOK C1 release HOLD.**
