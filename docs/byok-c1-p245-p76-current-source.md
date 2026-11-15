# P245 — P76 historical/current-source split (candidate only)

**15 November 2026 | OM v2.1 | REAL-KEY NO-GO | PRODUCTION RELEASE HOLD**

## Exact source lineage

- Repository `krismcan/Mark-LV`; parent P244 `da9c436a177b3ec68db0eff2b610180b745bfb2b`.
- Branch `byok-c1-p245-p76-current-source-20261115`; four additive files only; no historical/product source modifications.
- Genuine original P234 Windows failure source `096048db17c7c1f9402dfd16a7deb31e9ebdc81d`.
- All four unchanged historical original failures remain **FAIL** (native exit 1): G0/M1, G0/M2, G1/M3, G6/M3. Do not reclassify as green or edit, skip or xfail original assertions.
- Original P76 `tests/phase8_byok_c1_p76_scope.py` contains an exact historical branch pin `byok-c1-p80-sealed-historical-fixture-20261106`. It rejects modern descendants before subsequent historical source checks. This is a valid security refusal.
- The original Phase10.3 public route still delegates to P76. Its frozen bytes and the BYOK-B and Phase8.34 test modules remain unchanged in this P245 proposal. Do **not** rewrite or override those historical routes.

## Candidate implementation

`scripts/p245_p76_current_source.py` defines a new separately named, read-only **C** (current-descendant) verifier. It:
- Requires a real github-hosted Windows push event for this exact P245 branch and head, exact P244 ancestor, nonshallow full-history SHA-1 repo and raw Git checkout.
- Rejects Git replacement refs and grafts in both worktree and common Git directories, dirty source, ignored/untracked files and any nonadditive modification. Inherited `GIT_*` overrides are removed, replacement objects and lazy fetch are disabled, and storage/input object formats must both be SHA-1.
- Enumerates the entire HEAD tree and every stage-0 index entry. Paths, modes and object IDs must match exactly. The complete inventory independently reconstructs Git's root tree OID. Only ordinary `H` entries with debug flags `0` are supported. A second parser validates the raw v2/v3 index checksum, entries, padding and extensions, rejecting all entry flag bits beyond pathname length. Assume-unchanged, skip-worktree, intent-to-add, unmerged stages, fsmonitor/split/sparse extensions, unsupported index versions and unknown flags fail closed.
- Independently hashes every tracked file's raw disk bytes using Git's `blob <length>\0` SHA-1 framing. Raw bytes enter the blob hash directly. Each witness also records raw SHA-256, length and filesystem identity. Root ancestors, directories and files are checked for symlink/reparse aliases, Windows path aliases, duplicate case spellings, hardlinks and identity changes during reads.
- Repeats the complete source scan and Git identity checks within each proof. The returned `P245-COMPLETE-SOURCE-V2` witness binds the complete tree/index/disk inventory, checkout identity, branch, HEAD/tree, raw historical tag identity, all four candidate files and all six original historical SHA-256 witnesses.
- Preserves the original P76 literal and six immutable P233 SHA-256 pins, with independent comparisons against the P244 source and current HEAD blobs.
- Refuses wrong host, branch, event head, parent, source digest, source alias or unapproved path.
- Produces only evidence, explicitly marking all four historical P234 failures **unwaived**. It has no service actor, WinCred operations, keys, provider calls, signed install, credential migration or production admission capability.

Source reads are limited to 2 MiB per file, 64 MiB total and 20,000 tracked paths. Each Git child has a 35-second timeout, spooled output and a 16 MiB reply acceptance limit. Unsupported paths, metadata, modes, flags, missing bytes and partial replies refuse the proof. Windows disk executable bits are represented by the authenticated Git mode.

`tests/test_p245_p76_current_source.py` retains every existing P245 test assertion and adds isolated synthetic coverage. Real Git mutations occur exclusively inside disposable repositories. Coverage includes hidden predecessor tampering under both index flags, intent-to-add and unknown flags, index mode/OID/path divergence, raw CRLF mismatch, source aliases, changing identities, malformed trees, replacement/graft/format refusals, incomplete proofs and false-green native results.

The hosted workflow invokes `--hosted-suite` with evidence outside the checkout. The runner takes a fresh complete proof before either test child, runs the original local and hosted P245 classes together with the added synthetics, then attempts another complete proof in `finally`. Canonical JSON equality includes every source identity, index flag, tree/tag field and candidate byte witness. A missing or incomplete attempt, mismatch, timeout, nonzero native exit, incorrect test count, missing unittest summary or skipped-test summary refuses candidate success.

Artifacts include `before-source.json`, `after-source.json`, both native logs, `suite-receipt.json`, the runner log and `workflow-receipt.json`. Native test exits and log SHA-256 receipts remain independent fields. A successful bracket runner exits 0. The workflow records its intentional HOLD exit separately and exits **3 on candidate PASS**. Raw checkout behavior is scoped to the checkout process through Git environment configuration. Raw disk/blob verification establishes byte equality directly.

The hosted class's cached `setUpClass` proof supports its original assertions. Workflow success additionally requires the runner's fresh complete post-suite proof and canonical comparison.

## Open Failures & Prior-Issues Review

| Issue and source | Severity and root cause | Repair and regression evidence | Review and disposition |
| --- | --- | --- | --- |
| P245 finding 1, Codex read-only review, 15 November 2026 | P2. Selected-file authentication and porcelain status omitted hidden changes to other tracked predecessors. All current-source callers inherited this incomplete source boundary. | Complete HEAD/index/raw-disk verification, zero supported index flags and alias checks. Added disposable real-Git reproductions for hidden tampering and independent Git-byte mismatches. | Implementation awaits native Windows execution and Nayeon's separate validation. HOLD. |
| P245 finding 2, same review/date | P2. Cached proof could outlive the tested source, allowing a native green suite after the last source check. The workflow lacked complete before/after binding. | Fresh complete proofs around both native suites, canonical equality and explicit attempt/exit/log receipts. Added mismatched source, incomplete/missing attempts, timeout and synthetic false-green controls. | Implementation awaits native Windows execution and Nayeon's separate validation. HOLD. |
| P245 Windows bounded-read failure, independent native run reported 15 November 2026 | Stable Windows regular files expose different `st_ctime_ns` through `Path.lstat()` and descriptor `os.fstat()`. Requiring four identical ctimes falsely refused legitimate complete proofs and intercepted hostile tests before their intended checks. The reported 47-method run exited 1 with 15 failures. | Compare dev/inode/size/mtime/nlink/mode across all four observations, ctime separately within before/final lstat and opened/after fstat, and reject reparse attributes at every observation. Retain regular-file, single-link, bounded byte count, path checks and fail-closed read errors. Five new methods cover stable cross-API ctime differences, per-API ctime changes, other metadata changes, reparse observations, byte bounds and read errors. | Native rerun and independent review pending; no PASS inferred. HOLD. |

These repairs cover the additive diagnostic and its workflow. The four original P234 failures remain FAIL/unwaived. P96 production code and release controls retain their prior dispositions.

## Limitations requiring independent decision

The proposed C contract does not by itself make any of the original four methods pass. It shows a way to test modern descendant source integrity without dishonestly calling an isolated P76 historical prototype a current-version gate.

A genuinely independent qualified governance and security reviewer must approve the following items.

1. Archival H versus current C inventory versioning and exact replacement-current positive/negative coverage.
2. Whether any existing application routing should be migrated after preserving old negative admission.
3. The full test inventory for three native unfiltered Windows regressions.

Until then, preserve all four original FAIL records and 0/3 product regressions.

Separate high-priority production blockers persist: original P96 check-to-effect/revocation race, legacy Python user-scope CredWriteW/CredDeleteW, denial-only CustodyService, SEC-03 Windows service principal/SID/ACL/storage and SEC-04 signed broker/WDAC/IPC/human consent. Qualified approvals remain 0/7. Do not change system policies, install services, enter keys, merge/tag/release, edit Google workbook/dashboard or begin earlier-phase retrospective audit.

## Validation accounting

The remediation started on clean branch `byok-c1-p245-p76-current-source-20261115`, HEAD `fcb610a15ca77907121d2bef1fdaf99c1ff79ce6`, parent `da9c436a177b3ec68db0eff2b610180b745bfb2b`. The existing `.codex/CURRENT_STATE.md` contains older Phase 10.2 status. Git and the explicit P245 assignment govern this remediation. Windows denied process command-line inspection, so other Codex processes could not be mapped to workspaces. The assignment establishes a sole P245 writer and no conflicting edit was observed.

The authoritative executable `C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe` was unavailable to this sandbox. Focused Python tests, AST compilation, compileall and hosted workflow execution have **not run** here. Read-only PowerShell/.NET checks matched the proposed NUL/index-debug grammar and raw v2 index layout/checksum against all 1,014 real index entries, with a `TREE` extension. The index matched HEAD throughout. Independent raw Git blob hashing matched all 1,010 tracked paths outside the authorized four-file edit set, and all six frozen SHA-256 pins matched. Independent tree reconstruction matched HEAD tree `2e83e2c00657463ebb9d0d0c56a131fe6cb75b4d`. Both workflow PowerShell blocks parsed and `git diff --check` passed. These checks cover the observed metadata and bytes. Native Windows filesystem identity behavior, Git flag synthetics, runner receipts and hosted checkout behavior still require execution by Nayeon.

For external focused validation, run the following through the authoritative Python 3.12 executable with bytecode disabled.

```text
-B -m unittest -v tests.test_p245_p76_current_source.P245PureNegativeTests tests.test_p245_p76_current_source.P245CompleteProofTests tests.test_p245_p76_current_source.P245SuiteReceiptTests
```

The declared inventory is 52 local tests and seven genuine hosted tests, including 42 added adversarial/receipt methods. These counts describe source inventory. The genuine hosted class requires the authenticated push event and committed clean source. Nayeon manages subsequent Git and GitHub evidence. Complete before/after proofs establish two observed source states. Continuous filesystem immutability during a test process remains outside this diagnostic contract. Independent security approval remains outstanding, qualified approvals remain 0/7, and full unfiltered Windows product regressions remain 0/3.

The prior independent native failure log was reported as `D:\Nayeon\P245_SECURITY_EVIDENCE_20261115\P245_CODEX_PATCH_NATIVE_FINAL_20261115.log`, SHA-256 `273EDE106EBEADAC1CD61C184FF8049E303DE62AE20F3B58E45087DA93FAF037`. This correction does not reclassify that failed run. The same focused command above must now execute exactly 52 methods, with no failures, errors or skips and native exit 0. The sandbox attempt to invoke the authoritative Python returned PowerShell `CommandNotFoundException`; no native correction tests or compilation ran here. The original four P234 FAIL records remain unwaived. Production HOLD and real-key NO-GO remain in effect.
