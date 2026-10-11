# Pre-8.29 recovery-dialog stale callback security maintenance

Date: 11 October 2026
Branch: `nayeon-v1`
Protected starting HEAD: `c2b68c023443edbc2becfd3a1d5d2efc09cbc149`
Previous immutable maintenance tag: `nayeon-v1-pre-8-29-metadata-owner-maintenance-01` => `e3e5e9605dbb3b09452994a9d042b4b5e0edf34e`.

## Confirmed additional medium trust-boundary finding

After two different trusted metadata windows use a pooled `TrustedOnboardingRecoveryController`, a stale Python reference to a destroyed recovery-dialog child could invoke its old reject callback. Before this correction, `approve_reconciliation()` consumed the controller's current pending review BEFORE comparing its exact fingerprint, so a stale A callback could cancel B's newer reconciliation. This requires programmatic invocation of a callback for a destroyed widget, not a normal visible Tk click; it nevertheless violates the cross-window trusted-UI lifecycle contract.

## Bounded repair

- `nayeon/brain/onboarding_recovery.py`: verify the exact current fingerprint and exact human-decision type **before** clearing the pending review; a wrong-epoch/stale reject never consumes the current owner's review. Correctly bound rejection still consumes its own review without granting admission. Existing journal/marker preflight, expiry and fail-closed authority checks are retained.
- `nayeon/desktop_alpha/first_run_onboarding_recovery_window.py`: a terminal `_closed` marker and real Tk liveness check gate all review/approval/rejection callbacks. Parent-destroyed dialog callbacks are inert; an intentional child close cannot revoke a current owner unexpectedly.
- `tests/test_pre_829_recovery_child_lifecycle.py`: real Windows Tk, fake-only tests for destroyed child reference surviving parent closure, B's fresh review and B's subsequent admission, stale wrong-fingerprint rejection and correct owned rejection.

## Validation

- Focused recovery child/controller/UI tests: 16/16 passed immediately after the code patch.
- Focused Windows Tk child plus legacy metadata host tests: 36/36 passed; no skips.
- Windows Python 3.12 full regression after patch: **2,235/2,235 passed, 0 failures, 0 skips**; `compileall -q nayeon tests` passed.
- Independent read-only Codex Sol High static re-review: **CLEAR (no HIGH/MEDIUM findings in this narrow patch)**. Reviewer examined fingerprint consumption order, tenure epoch/generation, destroyed widget callback isolation, archived journal behavior and previous permissions. It did not execute tests; authoritative tests ran separately on Windows.
- Final staging, committed regression, tag, remote peeled-tag verification, handoff and same-ID workbook update are separate seal gates, and their results must be recorded only after execution.

## Security limits and phase gate

No real API key, provider network call, native Windows Credential Manager mutation, additional model-selected capability or release acceptance occurred. Windows named-mutex guarantees are confined to the established cooperating-process/session model. Formal release gates remain open. Phase 8.29 and the five-phase implementation batch remain **HOLD** until this maintenance fix is independently sealed and the pre-phase failure ledger has an explicit GO.

## Verified separate maintenance seal (11 October 2026)

- Product maintenance commit: 4363fd8db28188e61533049058f20a45bd70319a.
- Annotated tag: nayeon-v1-pre-8-29-recovery-dialog-lifecycle-maintenance-01.
- GitHub origin/nayeon-v1 and remote peeled tag independently verified at that exact commit after atomic push.
- Previous maintenance tag remains at e3e5e9605dbb3b09452994a9d042b4b5e0edf34e; prior product tags unchanged.
- Real Windows Python 3.12 staged and postcommit regressions: 2,235/2,235 passed, 0 failures, 0 skips.
- Independent Codex Sol High read-only security review CLEAR on the stale-dialog consent isolation. No provider calls or real credentials.
- Phase 8.29 remains not started; a fresh pre-phase GO/HOLD audit is mandatory.
