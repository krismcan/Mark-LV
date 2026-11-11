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
