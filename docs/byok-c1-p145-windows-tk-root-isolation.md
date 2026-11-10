# Nayeon BYOK C1 — P145 Windows Tk root-lifetime failure isolation

**10 November 2026 | OM v2.1 | P145 DIAGNOSTIC ONLY | USER-SCOPED RELEASE HOLD**

## Verified starting point

Exact P144 GitHub baseline: `4c4c8ef05f831e957023ef98d67661818f5e5eac`, draft PR #69.
P144 original Windows 15-module audit genuinely completed under unchanged verified
P139 native path-handle policy with 15 HOLD, 0 PASS, 0 TIMEOUT. The 19-test
Phase8.31 original module alone emitted 1 static import closure FAIL and
1 Tk cleanup ERROR: "1 retired fake Tk roots still live". Both original
assertions are frozen. Do not silently classify teardown ERROR as historical seal.

## P145 diagnostic design

A disposable Windows-2025 runner only. Exactly three additive files:
this audit, a diagnostic workflow and one driver. No production, historical
test, P139 file-handle security verifier or P140 signed launcher modified.
Inventory all 19 originally defined Phase8.31 tests using standard unittest
loader; each test executes via original `python -B -m unittest -v <exact test>`
in its own fresh Windows Python process. This differentiates root retention
that arises from one test case versus test-to-test accumulation. Every child
inherits only a fresh handle-verified owned C: temporary directory in its
TEMP/TMP/TMPDIR; original P139 Win32 reparse and exact-case checks are never
changed. Tokens and provider environment keys are stripped from child env.

Each module runs every original setup, cleanup, tearDownModule and assertion.
Native exit codes, genuine unittest result footers, original test IDs,
root-lifetime error matches, complete stdout+stderr SHA-256 and byte lengths
are recorded. Each original method is capped at 55 seconds and at most 3
concurrent Windows child interpreters execute. Any HOLD/TIMEOUT remains HOLD
and no test is skipped or patched. Diagnostic GitHub Action SUCCESS means
collection of all original 19 independent method dispositions only; it does
**not** establish 19 tests passing or three full product regressions.

If one method retains a Tk root, examine its cleanup owner graph and propose
a small production-only fix with source-safe tests; if no isolated method
retains one but the 19-method module does, diagnose cross-test interactions
in an intact source-preserving full-module run. Never rewrite historical
assertions to force acceptance. The separate Phase8.31 AST import closure
is independently governed as source/branch migration.

## Open release holds

Original P135 full product regression triad never completed. Nine P142 historical
module timeouts and P144 remaining historical seal/actual UI findings remain.
P140 signed companion has deliberately empty signer, image SHA and Code
Integrity owner policy approval, so production frozen launch must refuse.
Independent qualified user-scope Windows security review and branch-aware
immutable historical regression governance not obtained. Original privileged
G0–G6, including P96 revocation race and P124 transferred-handle author gap,
remain OPEN. No real key, provider calls, production WinCred on Kristian,
privileged service or HKLM/TPM change, unsigned executable on Kristian,
SAC bypass, GitHub production release or Drive release-record change.
