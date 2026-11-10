# Nayeon v1 — BYOK C1 P150: original Windows BYOK scope-integrity module

**10 November 2026 | OM v2.1 | DIAGNOSTIC — PRODUCTION RELEASE HOLD**

## Starting point

Exact parent: P149 final source `11e3f0963c9ff37469d6b4c75b2ddb5407cc9706`,
draft PR #74. P149 full original Phase8.36 module completed in 58.375s:
9/11 passed, two historical exact P76 branch refusal failures, native exit 1.
P149 remains HOLD, even though it recovered the P142 35-second timeout.

P150 selects the **original 13-case `tests.test_phase8_byok_scope_integrity`
module** from the remaining seven P142 timed-out modules. Its ancient
adversarial test source contains both in-memory historical A fixture
attacks and current descendant topology positive guards. Changing their
assertions or silently choosing only passing cases would destroy the
security evidence. This checkpoint does neither.

## Genuine Windows test and source custody

An isolated P150 branch is created directly from exact P149 and adds
**only** one original-test runner, this review and one Windows Actions
workflow. GitHub CI requires precisely these three audit-only changed
paths; no original test, migration reader, P139 native handle policy,
WinCred controller, P140 frozen signed-launch NO-GO, old Git objects or
product source changes.

The driver verifies the original test file byte-for-byte against
`git show 11e3f0963c9ff37469d6b4c75b2ddb5407cc9706:` for the
test path. It uses the Python AST to inventory **exactly 13 original
test methods** in the frozen class, without invoking or selecting tests.
It runs the ENTIRE original module with
`python -B -m unittest -v tests.test_phase8_byok_scope_integrity`
on genuine disposable GitHub-hosted Windows-2025 Python 3.12,
with an independent process bounded to 190 seconds.

The child-only TEMP/TMP/TMPDIR location is a newly owned canonical
local fixed-drive C: directory which must pass P139's **unchanged
native Win32 opened-handle exact-path/no-reparse guard**. No machine
Windows configuration or signed binaries are altered. The runner
does not use a real API key, production Credential Manager target,
provider network access, private signing key, or privileged service.

Evidence includes actual child native exit (0/1/124/125), unmodified
unittest OK/FAILED footer and observed count, original test SHA-256,
full raw combined stdout/stderr SHA-256 and bytes, failed test IDs,
elapsed time and named status PASS/TIMEOUT/HOLD. Test PASS requires
exact native EXIT 0, 13/13 real final test results, genuine unittest
OK footer and no errors. A green **diagnostic collection** Action
is never a passing historical module or full-product release gate.

### Distinction from historical P135

P135's full test suite attempted three unrestricted Windows regressions
but timed out at 600s with numerous original failures and an unfinished
historical Git test. Neither P148's single 22-case A04 module pass
nor P149/P150 bounded diagnostics are substitutes for the required
three complete full-product Windows passes.

## Reviewer governance / safety release holds

Seven P142 original timeout modules remain open at P149 conclusion.
P150 will resolve only the **timeout-vs-completes** classification for
this one module, not automatically waive actual test failures. P144
fifteen original HOLD modules persist. Exact-branch seal tests remain
unaltered, and a qualified independent reviewer has not yet approved
branch-aware current-source regression governance.

P147 independent security review packet exists but has no qualified
named reviewer GO. P140 has absent immutable publisher/main/helper
binary SHA-256 pins and Code Integrity policy owner FALSE: frozen
BYOK setup launch is fail-closed and unavailable. No actual signed
main/helper/installer, Smart App Control approval, live key use,
production WinCred effect on Kristian, provider validation,
protected Windows changes, GitHub merge/tag/release or prerelease
Google Drive master/dashboard mutation is authorised.

Original privileged BYOK C1 G0–G6 remain OPEN, including historic P96
race and P124 transferred-handle gap; they are NOT represented as
solved by the reduced current-user BYOK design.

**P150 bounded original Windows regression recovery is independent
of product signing, and cannot grant production GO.**
