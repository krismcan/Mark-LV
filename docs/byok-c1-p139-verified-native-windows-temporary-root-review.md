# Nayeon v1 — P139 Windows filesystem regression fixture-root validation

**10 November 2026 | OM v2.1 | diagnostic only | C1 USER-SCOPED RELEASE HOLD**

## Evidence-backed problem

P135 three unfiltered complete Windows product Python regressions each timed out without completing after 600 s. P136 stack snapshots showed repeated old Git history fixture traversal; no full product pass. P138 individually executed all seven native Windows filesystem ERROR tests from P135 and all three P86/P87 Connection failures:
- 7/7 genuine native temporary file/directory operations **independently returned unsafe_path**, even without any other test running; original error messages are fail-closed, no native operations silently succeeded.
- 3/3 Connection UI assertions independently failed `AssertionError: 3 != 2`, because P133 intentionally added the third explicit offline-key setup button. Historical source/test files remain UNCHANGED and old two-button assumptions require independent migration review.

P138 genuine hosted Windows job https://github.com/krismcan/Mark-LV/actions/runs/42772045285, raw per-test artifact ID 13742571060.

## P139 specific hypothesis — host default TEMP path violates strict handle-based identity

The existing `nayeon.services.filesystem` has strong Windows path controls: lexical canonical local drive, exact component spelling, no reparse/symlinks, opened-handle verified final path, no untrusted alias, and each ancestor held open without write/delete sharing. Github-hosted runner default Python `tempfile` path under `D:\a\_temp` may use a junction/reparse component, volume alias or differently cased OS-normalized name. This is a **hypothesis**, not yet verified from handle evidence. The seven failures consistently result from an ancestor/final handle `unsafe_path` check.

P139 runs those **same seven original unmodified test methods** in genuine independent Python subprocesses, but only after creating a uniquely named **owned local `C:\NayeonP139_<uuid>` directory** and verifying it with the SAME existing `fs._inspect_handle` policy on both `C:\` and the new directory. The runner must confirm exact case, no reparse point, local fixed drive `GetDriveTypeW==3`, and no unsafe-path refusal before the tests even begin. Then sets only process-local `TMPDIR`, `TEMP`, `TMP` to the verified directory for each child; no code/test assertion/Win32 validation source is changed, mocked, bypassed or patched. Tests have unique standard `tempfile.TemporaryDirectory` children. The dedicated owned C root is cleaned up, with no recursive cleanup if replaced by a reparse point.

If native tests succeed with the verified root but fail under default GitHub TEMP, the defect is fixture-environment selection, **not permission to weaken original path security**. If the new root fails the existing security guard, abort and retain the refusal. If tests still fail, preserve errors and analyze exact current Win32 identity evidence. P139 only reports real outcomes, never claims a full regression pass.

## Security limits and further release steps

This tests file creation and deletion only in a disposable GitHub-hosted Windows account, under an automatically created random directory on the local fixed test volume; no Kristian filesystem mutation, real user key, WinCred, protected HKLM/TPM, privileged service or signing certificate. It makes no changes to product files. Current C1 reduced user-scope still needs independent security review, branch-aware historical test governance, THREE complete full-product Windows regressions, legitimate publisher-signed main/companion installer, Smart App Control acceptance, and independent release.

Old privileged G0–G6 remain open; original P96 check-effect race and P124 authorship issue unchanged in frozen old paths. Do not merge/release on a diagnostic pass or update Drive master/dashboard for draft-only work.

**P139 is a secure test-root A/B probe ONLY. C1 USER-SCOPED RELEASE HOLD.**
