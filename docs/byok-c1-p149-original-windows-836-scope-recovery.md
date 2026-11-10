# Nayeon v1 / BYOK C1 — P149 original Phase8.36 Windows source-integrity recovery

**10 November 2026 | OM v2.1 | ORIGINAL HISTORICAL TESTS UNCHANGED | RELEASE HOLD**

## Exact baseline and tested hypothesis

P148 completed unchanged native A04 two-process original Windows recovery module,
22/22 pass in 68.266 seconds under the P139 exact Win32 native-handle-verified
owned C: temporary directory. It was previously timed out by P142's 35-second
diagnostic cap. That does **not** establish that the other eight outstanding
P142 historical scope-integrity module timeouts are safe or only cost-related.

P149 starts directly at exact P148 `a08bcb2b459da5edab673333f0e45be52a24230c`
(draft PR #73) in an isolated branch, then executes one representative smaller
original scope-integrity module `tests.test_phase_836_scope_integrity`
with 12 original test methods, unfiltered, in one fresh disposable
GitHub-hosted Windows-2025 Python 3.12 interpreter. Its prior P142 evidence was
TIMEOUT at 35 seconds, not a full executed module.

## Source restrictions and Windows evidence

Exactly THREE additive audit-only paths: this doc, one driver, one CI workflow.
Require unchanged source bytes against `git show` P148. Never change
original Phase8.36 tests/guard, old Git seals, P139 Win32 security source,
P140 signed companion NO-GO, WinCred or user-scoped BYOK product code.

Use only hosted disposable Windows. Create a fresh named random user-owned C:
temporary directory, require P139's existing original Win32 opened-handle
strict path identity/no reparse/fixed-drive approval before use. Child
`TMPDIR/TEMP/TMP` changes are test-fixture-only, not global host policy.
Strip obvious API key and GitHub token environment values. Do not
use real production credentials, network providers, unsigned binaries on
Kristian or privileged Windows mutations.

Run `python -B -m unittest -v tests.test_phase_836_scope_integrity`
without filtering any original test method, with a 170-second hard bound.
Capture native exit 0, 1, 124 or 125; full original combined stdout/stderr;
actual final unittest count/OK/FAILED footer; original test source SHA256;
complete raw log SHA256 and byte count; exact failure IDs; duration and
an explicit PASS/TIMEOUT/HOLD JSON manifest. Native PASS requires exit
zero, all 12 original tests and a complete OK footer. Diagnostic collection
CI SUCCESS is **not** a test pass when native status is FAIL/TIMEOUT.

If this remains costly, record truthful negative evidence. Do not execute
all eight expensive histories concurrently or silently exclude frozen tests.
Independent governance must still rule on an admissible branch-aware
historic/source-seal regression plan and the three complete current-product
Windows regression gates.

## Hard security holds

Original privileged C1 G0–G6 remain OPEN; P96 revocation race and P124
transferred handle authorship unremedied. P140 no publisher-signed pinned
desktop/helper or authorised trusted installer and Smart App Control owner GO.
P147 independent reduced current-user WinCred security/governance review
is still **NOT OBTAINED**. P135 three whole-product Windows regressions
all incomplete, P144 15 historical original module failures still open;
remaining P142 historical suite timeouts not assumed clear.

No actual API key, production WinCred on Kristian, provider validation,
protected registry/TPM, signed release, unsigned Kristian execution, SAC
bypass, GitHub merge/tag/release or pre-release Drive workbook/dashboard
changes are authorised.

**P149 = bounded ORIGINAL module evidence, not release clearance.**
