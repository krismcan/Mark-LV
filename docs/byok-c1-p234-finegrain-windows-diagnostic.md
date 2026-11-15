# P234: bounded original Windows regression isolation (unverified candidate)

Date: 2026-11-15. Authorized isolated checkout:
`D:\Nayeon\CODEX_P234_READONLY_20261115`, branch
`byok-c1-p234-codex-windows-finegrain-20261115`, exact clean starting HEAD
`096048db17c7c1f9402dfd16a7deb31e9ebdc81d`.
No product phase, security seal, historical repair, release or waiver is claimed.

## Open Failures & Prior-Issues Review

| Issue / source | Severity, cause and affected boundary | Containment / evidence / disposition |
|---|---|---|
| P233 shard 0/3, user task 2026-11-15 | Material diagnostic blocker: each timed out at 720s; individual slow/failing methods and root cause remain unknown. | Target only 19 BYOK B plus 35 Phase8.34 methods. Per-method 180s bound and raw evidence. Root cause unresolved; product progression HOLD. |
| P233 driver classification, inspected P231/P232/P233 `parent` | Material reporting ambiguity: `complete` means collected footer and matching exit, even with original FAIL/ERROR; driver can return 0. | P234 separates collection completeness, original exit and driver exit. Original FAIL/ERROR/unexpected success returns nonzero; synthetic adversaries provided, runtime validation pending. No change to historical reporting. |
| P231/P232 retained Tk cases, inspected P233 `worker` | Material historical harness lifetime defect: extra `items`/`selected` owners retained completed cases through module teardown. | No such lists during execution. Singles use a stdlib suite as sole extra case owner; discovery process exits before workers. P233 file remains hash-pinned. No Tk tests split or executed by P234. |
| Historical Git authentication, local inspection | Material missing evidence: isolated clone is shallow and has no tags. Context file contains older Phase10.2 status inconsistent with this Git checkpoint. | No historical tests run locally. Hosted source must be a separate full-history/tag checkout at the exact source commit, with raw byte verification. Missing/forged tags refuse admission. Context and historical files remain unchanged. |
| Independent review / Windows evidence | Open: no independent review or original Windows run of this candidate. | Implementation candidate only. Independent review pending; three full unfiltered release regressions **0/3**. |

GO only for this explicitly authorized additive diagnostic implementation.
HOLD for product progression, failure closure, security/release gates and seals.
The latest relevant implementation is P231 -> P232 -> P233, inspected together
with their P233 workflow and `docs/engineering_failure_review_gate.md`.

## Scope and lifecycle

Exactly four new files: external harness, standalone stdlib selftest, workflow,
this document. No historical test, fixture, owner, source pin, production code,
Git branch/ref, configuration or context-file edits. No staging, commits, tags,
pushes, PRs, workbook/dashboard changes or original checkout access.

Only these exact modules may receive single-method subprocesses:

- `tests/test_phase8_byok_b_scope_integrity.py`: 19 methods.
- `tests/test_phase_834_scope_integrity.py`: 35 methods.

Inspection found direct `unittest.TestCase` classes with no setup, teardown or
`load_tests` hooks. Both an AST check and runtime class/module check enforce this
condition. No hook is skipped or replaced. Normal stdlib method fixtures, subtests,
failure/error/skip/expected-failure semantics and verbose output remain active.
Each single starts a fresh process, so module imports and immutable fixture caches
are cold; this is a diagnostic isolation difference, never equivalence to a full
original-process regression. Other modules retain P233 module-affine assignments.

These two modules need no P139 temp/C# fixture setup. P234 does not compile native
fixtures, set P134 WinCred authority, use credentials/providers, install/start a
service, sign anything or perform a production/release operation. It executes
only unchanged historical scope-integrity tests in disposable hosted Windows.
The original authorization/policy/confirmation/execution/verification paths are
not modified. Historical failures are preserved without a successor/source waiver.

## Source identity and inventory

Controller checkout and authentic tested checkout are siblings. The workflow
uses `windows-2025`, CPython 3.12, full history/tags, disabled persistent checkout
credentials and `core.autocrlf=false` before source materialization. No P234 file
is copied into the authentic root. The actual test CWD/HEAD remains exactly
`096048db17c7c1f9402dfd16a7deb31e9ebdc81d`.

Admission requires hosted Windows, correct repository, a clean source including
ignored files, no replace refs/grafts, complete history and every tracked raw
file matching its immutable Git blob. It records SHA256 for all tracked source,
including the unchanged P233 script:
`4B29DE93CBA11971A00AF00F2C6E62D27B287FF53CBF5B08E905311258301FCB`.
Fifteen annotated historical tag refs must match literal object/peel pins from
authenticated scope-migration sources, be present as commits and be ancestors
of P233. These are historical object-authenticity checks, not signing claims.
Source identity is checked before/after discovery, each single and each group.

An external child calls unchanged P233 `discover()` with original unittest
discovery order. Any partial discovery, `_FailedTest`, duplicate ID, wrong count,
module mismatch or wrong P233 shard refuses planning. Exactly 3,629 unique IDs
are required. The manifest contains each ID once with its historical P233 shard:
54 receive P234 single ownership; 3,575 remain explicitly assigned to historical
P233 workload and **are not run by this workflow**. P233 itself is not launched
as a regression runner. Every group independently rediscovers and reconstructs
the same canonical manifest, bound to `github.run_id-github.run_attempt`.

## Execution, exits and coverage

Nine matrix groups of six singles, at most three groups concurrent, with
`fail-fast: false`. Each single has a 180-second bound. A timed-out process tree
is terminated using its newly created PID; diagnostic timeout is 124, while the
actual OS process return code is recorded separately. No original unittest exit
is invented when no footer exists. A fresh evidence directory is mandatory.

Raw merged stdout/stderr, flush-on-callback start/stop JSONL, original unittest
outcomes and footer, actual process return code, parent driver status and SHA256
receipts are retained. Reports distinguish discovered, assigned, executed,
completed, setup-blocked, unexecuted and uncompleted IDs. `startTest` means unittest
execution began (including instance setup); `stopTest` means it returned. Completion
does not mean success. Class/module setup errors/skips before method start are
reported as setup-blocked; import/admission failures and missing evidence remain
infrastructure/incomplete evidence, not inferred setup failures.

Driver 0 requires a successful original unittest exit and internally consistent
complete evidence for every assigned single. An ordinary original skip remains
SKIP, not PASS. Original failures/errors/unexpected successes or setup blocks
return 1; timeout returns 124 (uncertain process cleanup escalates driver to 125);
identity/manifest/evidence/infrastructure failure
returns 125. A group can truthfully report collection complete while returning 1.
Inventory planning can be green with zero executed methods and labels that fact.

An always-run reconciliation job verifies receipts and identical manifests,
requires all nine groups, reclassifies every result and journal, rejects false
green group drivers and produces an exact-once 54-method coverage certificate.
Missing or inconsistent artifacts fail closed. Complete assignment coverage does
not imply all methods executed/completed/passed; those fields remain separate.
Artifacts use attempt-specific names and are retained for 14 days. SHA256 receipts establish artifact consistency,
not an independent signature or external attestation.

## Validation and limitations

The synthetic stdlib selftest uses fake IDs and real fake runner processes. It
covers disjoint assignment, missing/duplicate/foreign IDs, old shard assignments,
ordinary FAIL/ERROR/skip/expected/unexpected outcomes, setup blocks, missing footer,
exit mismatch, partial/foreign/duplicate lifecycle events, timeout 124, hook refusal,
receipt tampering and absent aggregation artifacts. It imports no historical
test module and grants no native capability. The workflow compiles both new Python
files and runs the selftest before authentic discovery.

Local authoritative Python invocation was unavailable through the sandbox.
Host orchestration on Kristian was attempted for the selftest, but automatic
approval review rejected the process call: approval policy is `never`. No Python,
package or network workaround was used. Runtime selftest and py_compile results
are therefore **unverified** here. Local `git diff --check` and whitespace checks
of the four new paths found no errors. All **978** original tracked files were
individually hashed using Git's raw blob construction: **zero mismatches** with
HEAD. Original method-definition counts are 19 and 35, with no lifecycle-hook
definitions found. The workflow has not been run.

Example host commands, when separately available:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -B scripts/p234_finegrain_selftest.py
# Compile to a host temporary cfile outside the tested source, using py_compile.compile(..., doraise=True).
git diff --check
```

No claim that 3,629 original tests ran, no complete original-suite PASS, and no
claim that this diagnostic advances any mandatory release regression. Existing
historical failures and timeout root causes remain unwaived. Independent review
and all three full unfiltered release regressions remain open: **0/3**.

## Post-Codex host validation (authoritative local evidence, 15 November 2026)

After the Codex session finished, Nayeon used the authorised Kristian Desktop Commander host (not the restricted Codex sandbox) to run `py.exe -3.12 -B -m scripts.p234_finegrain_selftest` from the isolated P234 clone. **11/11 synthetic harness tests passed, native process exit 0**, runtime approximately 1.605 seconds. The original captured Python stderr log is `D:\Nayeon\P234_HOST_EVIDENCE_20261115\stderr.log`, SHA-256 `7EE73A8651A10FF5ABF6278CAF5150A35DA5901BDAF083472FB27FC450ED7F3D`. Python 3.12 in-memory AST parsing of both new scripts PASS. Existing tracked source diff remains empty and original HEAD remains `096048db17c7c1f9402dfd16a7deb31e9ebdc81d`. This host result supersedes the earlier Codex-sandbox-only statement that local tests could not run. It does not establish full historical Git authentication, actual P234 hosted single-method results, independent security approval or any full product regression; the release hold remains.
