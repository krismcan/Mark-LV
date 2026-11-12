# P171 — Historical H / current C / release R cross-era security-governance acceptance matrix

**Date:** 12 November 2026  
**Programme:** Nayeon v1 / BYOK C1 · OM v2.1  
**Status:** DRAFT / QUALIFIED INDEPENDENT REVIEW REQUIRED / PRODUCTION RELEASE HOLD

## Exact P170 source custody

Derived only from verified P170 `0b1eda4aa1296274df70cb7a4fb09592707bf178`, draft PR #95 OPEN/UNMERGED. Exactly three new audit-only paths on the P171 branch: this document, an isolated Windows diagnostic runner and native Windows Actions workflow. No original product source, original test source, original 171 tracked test modules or P76/P85/P139/P140 security assumptions modified. Kristian product worktree remains on its original HEAD with pre-existing changes; no contact with production credential storage.

P170 authentic hosted Windows Server 2025 original test results [run #43205690488](https://github.com/krismcan/Mark-LV/actions/runs/43205690488), artifact #13939060361 ZIP SHA-256 `736BA1BE56C3BB533A2E27E15130135AE205745ABFFBC2EECD0E6E6E515BCCDE`:

| Original whole test module in disposable guard-first **scratch-only** candidate | Authentic P170 Windows native result |
| --- | --- |
| Phase8.32 lifecycle assurance | **14 PASS**, exit 0 |
| P86 native UI | **5 PASS / 2 FAIL**, exit 1, legacy exactly-two-button expectation |
| P87 custody observation | **17 PASS / 1 FAIL**, exit 1, same legacy two-button expectation |
| Original isolated Phase8.31 import closure | **1 FAIL + 1 Tk fixture teardown ERROR**, exit 1 |
| Original isolated WinCred secret consumer boundary | **1 FAIL**, exit 1 |
| Original P76 wrong-branch denial negative | **1 PASS**, exit 0 |

These are real original test executions, NOT a passing full historical integration suite. The P170 candidate moved exactly five `self._require_creator_thread()` calls ahead of the original function docstrings in a **disposed** scratch clone. It passed original Phase8.32 but **lost exact Python function `__doc__` metadata**.

## P171 narrow hypothesis: exact metadata restoration without deleting docstrings

In a *new*, independently disposed hosted-Windows scratch Git clone, P171 proposes a **source-level compatibility experiment only**, not a production patch:

1. Authenticate this branch's exact GitHub head/parent, exactly three new audit paths, original immutable test source and reviewed protection hashes, authentic Windows and P139 Win32 non-reparse disposable C:\ test temp.
2. Re-authenticate original prior P170 ZIP SHA-256, individual six native original test logs, source-bound reviewer ledger and source code patch before relying on them.
3. Make P170's same exact AST-controlled guard-first reorders in **only two scratch copies** of `nayeon/desktop_alpha/application.py` and `nayeon/desktop_alpha/workspace_window.py`.
4. Append after the class definitions exactly **five** literal `Class.method.__doc__ = original_docstring` assignments to restore byte-for-byte original Python docstring metadata while leaving each creator-thread guard first in method AST. Require AST equivalence to the guard-first candidate **except** the five `__doc__` assignments; confirm source SHA256 and archive exact disposable Git diff. This has import-time source effects and therefore requires independent security review before any adoption.
5. From **actual imported Python classes** in scratch, verify all five `method.__doc__` SHA256 values equal the five original source-doc SHA256 values. Also invoke all five original method implementations in real Python worker threads against the strict synthetic sentinel: each must raise `WRONG_THREAD` **before any other state read**, with exactly one guard call. An adversarial wrong-field negative must not turn green.
6. Run completely unchanged original full Phase8.32 **14-case native Windows** module, full P86 7-case original, full P87 18-case original, original isolated Phase8.31 and WinCred failure controls, and original P76 wrong-branch security-negative. Preserve all native exits, original complete `unittest` footers, error/failure IDs and raw SHA256. The old historical refusals must stay **FAIL/HOLD**, not get suppressed.
7. Delete scratch clone and P139 verified local test temp; verify original review checkout HEAD/index/product/security bytes identical before and after. No original source patch in PR, and **no release**.

### Independent-governance decision matrix

| Security requirement | Historical H | Current C | Required reviewer authority |
| --- | --- | --- | --- |
| P76/P85 exact sealed historical branch/ref source identity | Frozen tests remain truthfully HOLD outside their sealed era | Separate source-bound current candidate only | Qualified security and historical test-governance disposition; never waive original denial |
| WinCred credentials/consumer allowlist, no implicit storage/reading | Original static unauthorized importer denial remains FAIL/HOLD | Three newer user-scope imports require full provenance | Credential trust-boundary review with explicit authorization; do not broadly expand allowlist |
| Phase8.31 UI import-closure vs P86 required `nayeon.brain.pending_custody_status_view` import | Two immutable literal source-shape tests conflict | Current synthetic display is non-authoritative; neither test can be silently evaded | New versioned architecture and independent source-era governance; old FAIL retains |
| P86/P87 exactly two Connection-page buttons vs newer explicit local BYOK click control (third button) | Old 2-button test remains FAIL/HOLD | Third button cannot be removed merely to satisfy old expectation | Approval of new current UI interaction contract with security negatives |
| Phase8.32 literal first-AST-node creator guard vs earlier function docstrings | P168 original Phase8.32 5 old static failures remain true | P171 scratch only: five guard-first methods with original `__doc__` literal restored | Review of module-import metadata mutation and behavior with complete targeted native negatives |
| P139 no-reparse native Win32 temp policy | Retained unchanged | Used with genuine Windows process | Independent Windows hardening verification |
| P140 approved signed main/helper/installer and SAC/WDAC Code Integrity | No pins/approval | **Not available** | Signed software publisher and Code Integrity policy-owner GO |
| Original full-product Windows suite, three complete source-matched runs | Historic 600s/190s stalls and failures remain | Focused test receipts are not full passes | Three genuinely completed unfiltered Windows full-product runs and qualified reviewer GO |

**No alternative test wording is silently substituted for old historical tests.** A review-accepted current-generation security contract must be separately versioned with explicit provenance and adversarial negatives; it must not falsify frozen old H status.

## Mandatory release holds

- H historical: old P76/P85 exact branch, Phase8.31 import, P86/P87 button count, WinCred legacy consumer and all other frozen security failures **HOLD**.
- C current: P166 15/15 source-bound + 25/25 selected-original reduced-scope candidate only; P171 scratch experiment adds no approved product source and is not a whole-product acceptance.
- R production: **HOLD**. **0/3** complete accepted full-product native Windows triad, qualified independent security/historical regression governance GO **NOT OBTAINED**, P140 signed main/helper/installer SHA and signer/Code Integrity-policy owner GO **NOT OBTAINED**, privileged C1 G0–G6 including P96/P124 **OPEN**.

No actual API key, production WinCred CredWrite/CredDelete, provider validation, signing, protected OS modification, GitHub merge/tag/release or misleading Google Drive MASTER release workbook/dashboard mutation.

**P171 independent reviewer packet is an internal evidence package. Writing it does NOT constitute qualified independent review or production permission.**
