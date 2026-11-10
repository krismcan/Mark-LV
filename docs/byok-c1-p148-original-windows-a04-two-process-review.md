# Nayeon v1 — BYOK C1 P148: genuine unfiltered original A04 recovery module

**10 November 2026 | OM v2.1 | Full original MODULE test recovery, NOT full product | RELEASE HOLD**

## Exact starting point

P147 exact HEAD `f0e34bbbccec995e5d5d5e277e582702be8b9428`, draft PR #72.
P147 Windows verified 13 protected original source/test files unchanged from
P146, plus fail-closed P140 signed companion policy. P142 diagnostic of the 83
original modules after the P135 stall recorded 9 original module timeouts with
a 35-second per-module cap. One outstanding historical test is
`tests.test_pre_829_a04_two_process_recovery`; it executes genuine
two-process A04 *synthetic*, disposable Windows recovery scenarios and OS
process supervision, not the privileged BYOK production writer.

## Single real Windows intervention

Use a completely isolated P148 branch, exactly 3 new files: this report,
a hosted Windows workflow, and one test runner. No original A04 source, test,
protected pipeline, WinCred, P139 Win32 file-handle guard, P140 signing gate,
or historical security tests change.

On disposable GitHub Windows-2025 Python 3.12, verify exact P147 branch
ancestry and `git diff` exactly 3 additive paths; verify original A04 source
bytes against `git show` of exact P147. Create a unique owned canonical local
C-drive TEMP root and require **UNCHANGED P139 original Win32 opened-handle
no-reparse fixed-drive exact-case verification** before use. Never change
machine-wide temp variables or disable filesystem security.

Run **the entire original A04 unittest MODULE** in one fresh Python 3.12
child process: no filtering of methods, no old assertion modifications,
no skips/xfails. A single bounded **195s** run (vs P142's 35s cap) distinguishes
an expensive but completing A04 source test from genuine stuck/failed cases.
Do not restart a healthy run. Keep genuine unmodified test log, final result
footer if any, native exit (0, 1, 124 or 125), elapsed time, test count,
failed test identities, full log and original source SHA256 in a manifest.
Record genuine module verdict PASS only with exit 0 and complete unittest OK.
A successful diagnostic CI **collection** means only the original result
was collected and retained, **not** that the original test or product passed.

No real credentials/provider calls, production WinCred on Kristian, signer,
SAC changes or code-signing action. Any test process termination is confined
to its own synthetic disposable Windows child process, and native exit 124
or failure remains an explicit HOLD.

## Required next security/release decisions

Even a passing A04 module recovers at most ONE of P142's nine timed-out
original modules. The remaining expensive historical scope/seal cases
require bounded authenticated evidence and reviewer approved branch-aware
current-source migration, without removing old tests. Historical P144
15-module holds, P135 true unfiltered product regression failures and
three incomplete full runs remain negative evidence. P140 embedded
signer/parent/helper SHA pins absent and Code Integrity owner GO FALSE.
Independent qualified user-scope security review and three complete accepted
Windows full-product regressions not obtained. Original privileged C1 G0–G6
remain separate and OPEN.

No production release, GitHub tag/merge or pre-release Google Drive MASTER
workbook/dashboard update is authorised.

**P148 = source-safe original full-MODULE recovery investigation, never
release authorisation.**
