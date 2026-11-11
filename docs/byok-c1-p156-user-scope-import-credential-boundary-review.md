# Nayeon v1 — P156 current-user import and credential boundary assurance

**11 November 2026 | OM v2.1 | DRAFT engineering investigation | PRODUCTION RELEASE HOLD**

## Source custody

Verified P155 PR #80 is open, draft, unmerged at exact Git SHA 27e119825d7c83a891b7d80b208bf2b7709e10bc. P156 branches directly from this exact commit: byok-c1-p156-user-scope-import-credential-boundary-review-20261111. Kristian is online, no active Desktop Commander sessions, and the original product worktree retained its 17 pre-existing dirty paths. No original product files, historical tests, P76/P85 seals, P140 release gate or Code Integrity policy have been modified.

P155 original trace archive P144 is preserved (15 original HOLD modules and 30 authentic FAIL/ERROR records). A historical failing test is not a legitimate production regression pass just because a separately versioned test succeeds.

## Precise original non-P76 failures

1. Original Phase8.31 static import-closure test rejects the four later lazy UI imports into nayeon.brain.* found inside ConnectionWindow; the original P144 log contains one static FAIL and one module teardown ERROR reporting one retired fake Tk root still live.
2. Original WinCred consumer test rejects nayeon.secrets.contracts imported from the newer current-user UI/controller boundary; the separate exact-backend static import test passed in P155. The second original historical source scope test fails due to the frozen exact P76 branch, not a native WinCred defect.
3. The P145/P146 real Windows evidence demonstrated the retained fake Tk root was owned by a unittest _SubTest failure carrier and released when the result carrier dropped out of scope; this does not clear a production root leak without distinct evidence.

## Versioned P156 scope and falsifiable tests

P156 is restricted to three additive evidence-only files: this review, a diagnostic Python source/probe driver and a disposable Windows Actions workflow.

On genuine Windows-2025 Python 3.12, the runner will:

- Verify exact P155 ancestry, clean clone, only three additive audit files, no changes to original tests/product/security sources, and the unchanged P139 Win32 opened-handle local temporary root.
- Verify only four named ConnectionWindow methods lazily import exactly the two known pending-custody presentation modules and have the creator-thread guard as the first **executable** statement. A docstring is allowed as a Python docstring but the historical exact first AST assertion remains red.
- Traverse the live source's transitive imports starting at those two presentation modules and fail if they gain a direct dependency on WinCred native backend, user-scoped BYOK writer, provider SDK modules, credential lifecycle, resolver or credential-operation host.
- Verify that only the standalone current-user controller in this narrow path directly imports the existing WindowsCredentialBackend, the Tk UI only imports its typed controller/SecretValue, and the credential identifier is fixed to openai.api_key.
- In a new Windows child, import the UI/pending modules and current-user controller with attempts to invoke ctypes.WinDLL, tkinter.Tk, subprocess.Popen, socket connections and os.system made fatal. No native credential, new Tk root, process or network effect is authorised at import.
- Execute the entire unchanged tests.test_local_user_scope_byok and tests.test_p133_connection_launch modules with **fake credential/native and fake subprocess** contracts on disposable Windows; record real unittest footer, native exit, full original log SHA-256 and case count.
- Execute the exact original Phase8.31 static import-closure method, expected to FAIL, with native exit 1 and full original footer. This is expressly NOT a waived historical failure.
- Preserve all raw logs and a machine-readable honest decision ledger, including any new failures.

## Internal review and boundaries

The older import closure and historical WinCred consumer allowlist protect important trust boundaries. A versioned new proof may establish that a **narrower** current-user UX does not activate the credential store before manual action; it cannot independently approve widening previous authorisations or replacing older tests.

Prior documented P132 scope acknowledges same-user malware, in-memory Tk secret lifetime, absence of durable reconciliation, external same-user credential replacement, and the gap between displayed status and genuine provider validity. These are residual security risks and cannot be marked closed by a unit test.

No real provider token, live credential store, synthetic user credential write, production launch, protected Windows setting, signed executable, PR merge, release tag or Google Drive release ledger update is authorised in P156.

## Release hold

Full accepted full-product Windows regressions: **0/3**; qualified independent current-user security review: **NOT OBTAINED**; qualified independent historical regression-governance approval: **NOT OBTAINED**; signed and exact hash-pinned installed binaries: **NOT OBTAINED**; Smart App Control / WDAC owner GO: **FALSE**; original privileged C1 G0–G6 including P96 and P124: **OPEN**.

**P156 is a scoped defensive test and review packet only, not release approval.**


## Completed real hosted Windows test ledger

**Run:** https://github.com/krismcan/Mark-LV/actions/runs/43051612011

**Verified actual tested source SHA:** 15ebcba07e6f2a2175f900e4b7565c391590e7ab. Real Windows-2025 Python 3.12 runner exited **0** for its evidence-collection job; the signed/production-release acceptance gates have not passed. The source guard confirmed P155 exact ancestry with **only three new audit files** and unmodified original product/test/security sources.

**Original GitHub Actions archive ID:** 13869477501; archive SHA-256 74A02C78FC62CB9A65F6712975E4DBCFEB5D565970B50C26C70AF894FF50BE1C. Archive contains four native combined logs and source-bound JSON ledger. File-by-file JSON SHA-256 receipts were verified against downloaded original bytes.

| Genuine focused Windows child | Native exit | Unittest count | Status | Original combined-log SHA-256 |
| --- | ---: | ---: | --- | --- |
| Import-only adverse ctypes WinDLL / subprocess Popen / Tk root / socket / os.system probe | 0 | N/A | PASS: no import-time prohibited effect observed | DC23F1E1737D2D286C35DDF60EFB95F1042A5339363825CADE2AFBCF15AE4FEE |
| Original unchanged P132 user-scoped controller, fake WinCred and real Tk tests | 0 | 36 | PASS 36/36 | C9D4258E49599139D08936BFFD4C66CCB928601A4469F1A5C243BC88E6844E43 |
| Original unchanged P133 explicit launch, fake Popen and real Tk tests | 0 | 25 | PASS 25/25 | 27C8AD303F143E8B8BBC580BC598722A03B291D5AE6F949BC0B4BF13C75192A2 |
| Original Phase8.31 static closure and teardown (unchanged) | 1 | 1 | HOLD: static import FAIL plus Tk teardown ERROR | 560F8F43FD5CFE8586F28556DDDADAB7E153F2BC6483065F57DA6316FD4D4276 |

**Source analysis:** all four originally identified ConnectionWindow lazily imported methods have first executable creator-thread checks and only the two named presentation-boundary imports. Their recursive named source import closure contains 13 modules: connection, connection_bootstrap, connection_document, connection_persistence, connection_readiness, connection_reconciliation, connection_recovery_advice, connection_service, onboarding_status_view, pending_credential_policy, pending_custody_observation_boundary, pending_custody_status_view and secrets.contracts. No native WinCred backend, current-user writer or provider SDK dependency was detected inside that traversed named closure. Its import-time effect-denial probe succeeded.

**New residual architecture concern:** the imported pending custody status presentation module brings in wider connection service/persistence definitions transitively. The import probe proved no effect *on import*, not that future calls into that dependency closure can never reach a filesystem or mutable service capability. This is not a source-permission waiver. Independent reviewer should assess whether to split the view into a minimal immutable type-only boundary and whether the deeper imports are justified. Do not move imports simply to evade the old Phase8.31 static test.

**Verified original failure:** the original Phase8.31 exact static method again reported source = nayeon/desktop_alpha/workspace_window.py; the unchanged module teardown again reported 1 retired fake Tk root still live. P146 had attributed that observed lifetime to unittest _SubTest retention; this new narrow run does not independently retest production root lifetime. No original Phase8.31 result has been upgraded to PASS.

## Internal disposition and next checkpoint

P156 evidence-collection acceptance is complete, but no production source repair is justified by the current record. Current-user WinCred and launch paths passed 61 original functional/synthetic cases; narrow import-denial and static closure analyses also succeeded, yet the historical original code-shape constraint remains FAIL. Authoritative independent approval must distinguish current-user scope from frozen privileged/historical authorisations.

**Recommended P157:** bounded audit of the 13-module presentation dependency graph and the trust boundary between view-only import and service/persistence capabilities; consider a smallest possible product-source isolation repair only if a concrete real effect or dangerous callable reachability is demonstrated. Preserve the original user-scoped and historical negative controls and produce separate genuine Windows evidence.

Production release holds remain 0/3 complete accepted full-product Windows regressions, no qualified independent review/governance, unsigned/unpinned main/helper/installer, Code Integrity policy-owner NO GO, and privileged G0–G6 OPEN. No real key/WinCred state was used or authorised; original Drive MASTER release workbook remains unchanged.
