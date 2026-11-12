# P169 — Source-preserving causal isolation of Phase8.31 Tk teardown, first-statement thread guards, WinCred importer provenance

**12 November 2026 · OM v2.1 · P169 DIAGNOSTIC / INDEPENDENT SECURITY REVIEW REQUIRED / PRODUCTION RELEASE HOLD**

## Exact verified custody

P169 branches from the **verified P168** SHA `0f7cd007f535db108f0306c8b11d3097f2cf774e`; the P168 PR #93 is DRAFT, OPEN and UNMERGED. The P169 branch adds **exactly three new evidence-only files**, no modifications to any original tests or product/security/source. Preserve 171 original-plus-additive Python test modules, original 19+ protected source and test paths, immutable historical branch/ref/tag assertions (P76/P85), P139 native Win32 no-reparse disposition and P140 blank signed binary/Code Integrity pins. No edits to Kristian's original 17 dirty paths.

## Why this checkpoint

P168 executed the entire, unchanged original Phase8.31 effect-isolation module (19 tests: **1 genuine FAIL + 1 genuine ERROR**), Phase8.32 lifecycle (14 tests: **5 genuine subtest FAIL**) and Windows Credential Manager backend (24 tests: **2 genuine FAIL**). All three original modules remain HOLD.

A first hypothesis is that the Phase8.31 original static test failure retains its unittest TestCase object (and `self.root`) in `TestResult.failures`; therefore the module's post-suite `tearDownModule` weakref GC assertion may report one extra `retired fake Tk roots still live` secondary to the retained failing TestCase. **This is a hypothesis, not a waiver or settled object-lifetime proof.** We must distinguish an independent UI leak from failed unittest record retention before changing cleanup behavior.

P169 reauthenticates the exact genuine P168 [artifact #13923308046](https://github.com/krismcan/Mark-LV/actions/runs/43174433126/artifacts/13923308046) (ZIP SHA-256 `AB3057127EF9533E0115BF9201EA2ADC120419F5E626111F5616C59EEF8ECE43`) and original native three module logs including every FAIL/ERROR heading. No prior failures are overwritten.

## Four real Windows original-test diagnostic groups

On Windows Server 2025, Python 3.12, original P139 verified Win32 C: temp, source matched to exact P168 ancestor, run **unchanged original unittest functions in their existing source**, with real exit/status/footer and unedited raw stdout/stderr SHA256:

1. **Original 18 Phase8.31 tests other than the already genuinely failing production-import static assertion**, in one genuine `unittest -v` process with original module teardown still invoked. If all 18 PASS with no Tk-root survivor, this is strong differential evidence the teardown ERROR in the full 19-test original is related to keeping the failed TestCase alive. The complete original 19-case module stays FAIL/HOLD regardless.
2. **Original exact Phase8.31 failing static-closure method alone**, with unchanged `tearDownModule` and no fixture modifications. Expect actual original failure to remain, and record whether the single-case TestResult still produces the Tk-root ERROR.
3. **All 20 original backend and native-adapter WinCred tests**, unchanged, using their pre-existing synthetic/fake Win32 test adapter. This is not a production CredWrite and does not override the full 24-test original WinCred module HOLD.
4. **The original WinCred unapproved consumer static test alone**, unchanged and expected to fail, with exact original import consumer detection preserved.

**Collector may only green on actual completed original 18/18 + 20/20 PASS, AND both single old failing original methods genuinely remain unwaived HOLD.** This diagnostic gate does not mark their historical entire modules green. Capture each native exit 0/1/124, full real raw stderr/stdout and source-bound result ledger; no synthetic replacement of original tests.

## Five guarded production entrypoints — actual worker-thread negative, no Tk launch

For original `OfflineWorkspaceApplication._open_local_byok`, `ConnectionWindow.begin_synthetic_pending_observation`, `cancel_synthetic_pending_observation`, `publish_synthetic_pending_observation`, `show_pending_custody_advisory`:

- AST from original product files: each method has a docstring first and `self._require_creator_thread()` as the **first executable statement**, in violation of the frozen original Phase8.32 first-*AST* statement contract. Do not rewrite originals or lower the historical test threshold without security governance.
- Call each exact original unbound method from a **real native Python worker thread** against a synthetic sentinel owner that refuses all attribute access before its owner-thread gate. Require exactly one gate invocation, `WRONG_THREAD` before any field read or effect.
- In-memory adversarial AST statement-order negative is rejected.
- This is proof of fail-closed sequencing on **these synthetic owner instances only**: NOT proof of real Tk GUI construction, live entire product thread behavior, kernel instrumentation or qualified security GO.

## WinCred and production UI import provenance

Read the current authentic production Python AST, enumerate exact imported modules, imported names, paths and line numbers. Compare old Phase8.3 fixed consumer policy to **source actual** and identify every currently unapproved import for reviewer. The original WinCred test remains FAIL, with **no blanket allowlist expansion or actual credential I/O**. Detect in-memory injected native backend import negative.

The old Phase8.31 static source-closure forbids any `nayeon.brain` import from `workspace_window.py`; the later synthetic custody observation interface currently uses `nayeon.brain.pending_custody_observation_boundary` within guarded on-demand methods. Report exact location, do NOT silently change production source, disable synthetic custody boundary or conceal the historical FAIL. Detect in-memory disallowed importer negative.

## Decisions and next actions

**Historical H:** original Phase8.31 full 19, Phase8.32 full 14, WinCred full 24 and P76/P85 exact era historical branch cases are still genuine HOLD.

**Current C:** P166 15 source-bound versioned tests + 25 selected original current-user-scope tests passed in a reduced candidate only. P169's differential original tests and entry guard probes neither constitute a full original module pass nor approve production.

**Production R:** HOLD, **0/3** accepted complete native full-product Windows regressions, no qualified independent security/test-governance signed review, no P140 actual signed main/helper/installer hash or SAC/WDAC Code Integrity policy-owner GO, privileged C1 G0–G6 OPEN. No real keys, provider network validation, production credential operations, privileged Windows changes, GitHub merge/release/tag or misleading Drive MASTER workbook/dashboard release-status update.

### Conditional P170 repair decision

- If 18 original Phase8.31 controls pass without Tk weakref survivor while isolated original failure reproduces both original headings, document *probable failed-TestCase result-retention* and request qualified independent review before proposing teardown or source adjustment; avoid treating it as independent leak.
- If guard negatives pass, propose **preserving actual first-executable creator-thread enforcement** and seek governance disposition for the frozen earlier AST-first assertion, rather than rewriting old security controls or falsely claiming the UI is safe.
- For WinCred and UI import closure, demand evidence of actual consumer provenance, minimal import-boundary adaptation and negative tests before any approved production source patch. No unreviewed allowlist exceptions.

**P169 is diagnostic only; BYOK C1 user-scope production RELEASE HOLD.**
