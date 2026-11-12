# P170 — Disposable Windows compatibility candidate: first-statement creator-thread gate and immutable governance contradiction

**12 November 2026 · OM v2.1 · REVIEW CANDIDATE ONLY · BYOK C1 PRODUCTION RELEASE HOLD**

## Exact immutable custody
- Parent P169 commit `00f397f5d397a7b6fba14ab124b71ba1d3b7a99b`, draft PR #94 open/unmerged.
- This P170 draft branch adds exactly **three new evidence-only files**: `scripts/p170_windows_disposable_guard_first_candidate.py`, this document and `.github/workflows/p170-windows-disposable-compatibility-candidate.yml`.
- No actual production or original historical test file is modified in the P170 branch. Retain 171 original-and-prior-audit test modules, 19+ security/source paths, P76/P85 exact branch/ref/tag denial, P139 native Win32 ownership and P140 empty signed/main/helper/code-integrity pins.
- Kristian original product worktree remains untouched (17 existing paths). No real API keys, credential operations, provider validation, production binaries, Git merge/tag/release or Windows policy changes.

## Observed, logically incompatible frozen original contracts

**Phase8.31 original** `tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests.test_static_production_import_closure_forbids_test_and_effect_routes` prohibits any `nayeon.brain` imports in `nayeon/desktop_alpha/workspace_window.py`, including nested on-demand imports. **P86 original** `tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests.test_no_effectful_imports_or_callbacks_in_new_method` requires the method `ConnectionWindow.show_pending_custody_advisory` to have exactly `from nayeon.brain.pending_custody_status_view import ...` inside that method. Both cannot be simultaneously satisfied as authored; rewriting import as dynamic `__import__` or moving it merely to evade static checks would bypass security intent and is **not acceptable**. Qualified independent original-test governance and new architecture need to resolve this; old historical denial stays FAIL/HOLD and P86 source-preservation stays in place.

The older WinCred original fixed secret-consumer allowlist likewise rejects newer BYOK module imports from `local_byok_user_scope.py` and `local_byok_window.py`. Do **not** auto-whitelist those imports; independent credential trust/data-flow review required.

## Testable reversible candidate — guard as first AST statement

P169 authentic native hosted Windows proved five original production methods have a **docstring** as first AST node, with `self._require_creator_thread()` as first executable node, and real-worker unbound sentinel tests refused `WRONG_THREAD` before any other field reads. The original Phase8.32 static assertion, however, requires that creator-thread guard be literally the first AST node, so original whole module has 5 recorded subtest failures.

On disposable GitHub-hosted Windows Server 2025 and CPython 3.12 only:
1. Verify exact GitHub push HEAD and exact P169 ancestry, exactly three added evidence-only paths, 171 original tests and all protected production/test security source hashes.
2. Re-authenticate archived P169 actual original Windows raw evidence artifact #13929023754, outer SHA256 `26392F4A186DAD82E9C8BD825686D6D3514D8EC7056E53C34B0923BA6C7CE9BC`, using limited `actions:read` token without forwarding it to artifact storage hosts.
3. Create **independent disposable local Git clone under GitHub Runner temp** (NEVER Kristian or tracked P170 branch). Move, in that scratch clone only, exactly the one original `self._require_creator_thread()` expression to before the docstring in `OfflineWorkspaceApplication._open_local_byok` and four `ConnectionWindow` synthetic custody methods. Require AST structural equivalence after the one swap, exactly two source files changed in scratch clone, no other changes; archive the exact diff patch and before/after SHA256.
4. In that disposable scratch clone, run **the original unchanged complete Phase8.32 14-case Windows Tk module**, **original unchanged complete P86 and P87 modules** (all existing security negatives), **original old Phase8.31 import prohibition single-case negative** (MUST remain genuine FAIL), **original WinCred unapproved-consumer negative** (MUST remain genuine FAIL) and **original P76 wrong-branch refusal negative** (MUST PASS). Use existing P139 verified owned C: temporary Windows root, bounded child native processes, exact raw stdout/stderr, native exit 0/1/124, original named failures and SHA-256, source-bound JSON ledger.
5. Destroy disposable scratch clone and verified no-reparse test root. Before-and-after custody of ORIGINAL checked-out repository must match exactly. No product source patch is committed or merged.

**Caveat:** Moving a Python docstring after the first executable guard removes normal Python `function.__doc__` metadata. This is an actual observable API compatibility change, not automatically a safe final production repair. Original security tests may pass in the candidate, but external qualified engineering/security review must decide whether metadata preservation, an alternative test-governance rule, or a revised design is required. Any overlay test PASS is diagnostic, not accepted product regression or production change.

## Release contract H/C/R

- **H historical original:** frozen Phase8.31/UI import, WinCred consumer, P76/P85 branch-contract failure records remain **HOLD**; all original tests unmodified. A disposable patched Phase8.32 candidate cannot retroactively make the original P168 Phase8.32 suite PASS.
- **C current:** P166 15/15 versioned positive/negative plus 25/25 selected original reduced-scope PASS; P170 only research overlay, no accepted full-product current-version baseline.
- **R release:** **HOLD**. Original whole-product unfiltered Windows acceptance 0/3, external qualified H/C/R governance and security signed GO not obtained, P140 actual approved main/helper/installer signer+hash pinned evidence and SAC/WDAC Code Integrity policy-owner GO absent, privileged BYOK C1 G0–G6 (P96/P124) OPEN.

The P170 checkpoint is complete **only** when its real hosted Windows source/evidence and native receipts are authenticated and reviewer packet appended. Do not hide genuine failed or timed-out negative controls. Never claim release.

**DRAFT / NOT MERGEABLE FOR PRODUCTION / BYOK C1 RELEASE HOLD.**
