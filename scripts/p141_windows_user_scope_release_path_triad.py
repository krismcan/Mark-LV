"""P141 — three *scoped* release-path Windows regressions, not G6 full passes.

Runs unchanged current-user BYOK functional tests, unchanged P140 frozen
signed-launch NO-GO tests, real ephemeral synthetic-only WinCred and the
SEVEN untouched native filesystem regression tests under the existing
P139 independently handle-verified C: temporary root.

The P135 FULL, unfiltered suite timed out 3x after 37 FAIL + 7 ERROR;
historical exact-branch seal tests are NOT run here and remain OPEN.
This is deliberate, explicit scope isolation, NOT a full-suite replacement
or authorization to store a real credential.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys


# Exact substantive release-path classes. Every source test remains immutable.
# Historical Phase8/P76/Phase10 or P132-140 exact-branch scope tests are NOT
# eligible to be called 'current branch passing' without new reviewer approval.
_CURRENT_USER_RELEASE_CLASSES = (
    "tests.test_p140_frozen_signed_companion.FrozenSignedCompanionGateTests",
    "tests.test_p133_connection_launch.LaunchBridgeTests",
    "tests.test_p133_connection_launch.ConnectionPageTkLaunchTests",
    "tests.test_local_user_scope_byok.LocalOfflineControllerTests",
    "tests.test_local_user_scope_byok.WindowsUserScopeNativeMutexTests",
    "tests.test_local_user_scope_byok.WindowsLocalByokRealTkTests",
    "tests.test_p134_real_wincred_ephemeral.GenuineEphemeralWinCredTests",
    "tests.test_windows_credential_backend.BackendTests",
    "tests.test_windows_credential_backend.NativeAdapterTests",
    "tests.test_first_run_credential_management_window.ManagementUITests",
    "tests.test_first_run_credential_management_window.WindowsRealTkManagementTests",
    "tests.test_credential_operation_host.TrustedCredentialHostTests",
    "tests.test_bound_credential_lifecycle.LifecycleTests",
    "tests.test_first_run_connection_application.ApplicationTests",
)

_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
_PASS_END = re.compile(r"^OK\s*$", re.MULTILINE)


def _windows_ci() -> bool:
    return (
        sys.platform == "win32"
        and os.getenv("GITHUB_ACTIONS") == "true"
        and os.getenv("RUNNER_OS") == "Windows"
        and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.getenv("GITHUB_EVENT_NAME") == "push"
        and os.getenv("RUNNER_TEMP")
        and os.getenv("P134_NATIVE_WINCRED_EPHEMERAL_AUTH")
        == "EPHEMERAL_GITHUB_WINDOWS_ONLY"
    )


def _run_bounded(command: list[str], *, root: Path, log: Path,
                 timeout: int) -> tuple[int, int, str, bool]:
    try:
        with log.open("wb") as f:
            result = subprocess.run(
                command, cwd=root, stdout=f, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, timeout=timeout, check=False,
            )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    except OSError:
        exit_code = 125
    raw = log.read_bytes() if log.exists() else b""
    content = raw.decode("utf8", "replace")
    match = _COUNT.findall(content)
    count = int(match[-1]) if match else -1
    hash_value = hashlib.sha256(raw).hexdigest().upper()
    ok = exit_code == 0 and count > 0 and bool(_PASS_END.search(content))
    return exit_code, count, hash_value, ok


def main() -> int:
    if not _windows_ci():
        print("P141_DISPOSABLE_GITHUB_WINDOWS_ONLY=REFUSED", flush=True)
        return 4

    root = Path(__file__).resolve().parents[1]
    temp = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p141-user-scope-triad"
    temp.mkdir(parents=True, exist_ok=True)

    print("P141_WINDOWS_RUNS=3", flush=True)
    print("P141_ORIGINAL_PRODUCT_TEST_FILES=IMMUTABLE", flush=True)
    print("P141_REAL_WINCRED=EPHEMERAL_RANDOM_NONKEY_ONLY", flush=True)
    print("P141_NATIVE_FILESYSTEM=UNCHANGED_P139_VERIFIED_LOCAL_HANDLE_ROOT", flush=True)
    print("P141_P135_UNFILTERED_FULL_SUITE_37_FAIL_7_ERROR=UNRESOLVED", flush=True)
    print("P141_P86_P87_OLD_TWO_BUTTON_EXPECTATIONS=UNRESOLVED", flush=True)
    print("P141_ORIGINAL_HISTORICAL_BRANCH_SEALS=NOT_RUN_NOT_CLAIMED_PASS", flush=True)

    class_counts: list[int] = []
    success = True
    for iteration in range(1, 4):
        # The P134 suite's own native WinCred test gate and UUID isolation
        # always stay enabled. No actual OpenAI slot or real key touched.
        log = temp / f"p141_release_path_functional_run_{iteration}.log"
        command = [
            sys.executable, "-B", "-m", "unittest", "-v",
            *_CURRENT_USER_RELEASE_CLASSES,
        ]
        exit_code, count, digest, ok = _run_bounded(
            command, root=root, log=log, timeout=155,
        )
        class_counts.append(count)
        if count < 100 or not ok:
            success = False
        print(f"P141_PASS_{iteration}_FUNCTIONAL_NATIVE_EXIT={exit_code}", flush=True)
        print(f"P141_PASS_{iteration}_FUNCTIONAL_TEST_COUNT={count}", flush=True)
        print(f"P141_PASS_{iteration}_FUNCTIONAL_LOG_SHA256={digest}", flush=True)
        print(f"P141_PASS_{iteration}_FUNCTIONAL_VERDICT={'PASS' if ok else 'HOLD'}", flush=True)

        # P139 repeats each of the exact original 7 Win32 filesystem
        # test cases, with fresh owned local C: handle-verified test fixture.
        # Not a modification of the original security policy or tests.
        fslog = temp / f"p141_original_native_fs_run_{iteration}.log"
        fs_exit, fs_count, fs_digest, fs_raw_ok = _run_bounded(
            [sys.executable, "-B", "-m",
             "scripts.p139_native_fs_verified_local_temp_root"],
            root=root, log=fslog, timeout=180,
        )
        fs_text = fslog.read_text(encoding="utf8", errors="replace")
        fs_ok = (
            fs_exit == 0
            and "P139_ORIGINAL_NATIVE_FILESYSTEM_CASES_PASS=7" in fs_text
            and "P139_ORIGINAL_NATIVE_FILESYSTEM_CASES_HOLD=0" in fs_text
            and "P139_SOURCE_AND_SECURITY_POLICY_UNMODIFIED=TRUE" in fs_text
        )
        if not fs_ok:
            success = False
        print(f"P141_PASS_{iteration}_ORIGINAL_FS_NATIVE_EXIT={fs_exit}", flush=True)
        print(f"P141_PASS_{iteration}_ORIGINAL_FS_SEVEN_VERDICT="
              f"{'PASS' if fs_ok else 'HOLD'}", flush=True)
        print(f"P141_PASS_{iteration}_ORIGINAL_FS_LOG_SHA256={fs_digest}", flush=True)

    stable = len(set(class_counts)) == 1 and class_counts[0] >= 100
    print("P141_SAME_CURRENT_USER_TEST_COUNT_ALL_THREE="
          + ("TRUE" if stable else "FALSE"), flush=True)
    print("P141_THREE_SCOPED_RELEASE_PATH_WINDOWS_REGRESSIONS="
          + ("PASS" if success and stable else "HOLD"), flush=True)

    # This is deliberately NEVER set to PASS: old historical seal failures,
    # full-product discovery timeout and independent code-signing remain.
    print("P141_THREE_FULL_UNFILTERED_WINDOWS_PRODUCT_REGRESSIONS=NOT_PASSED", flush=True)
    print("P141_INDEPENDENT_SECURITY_AND_BRANCH_GOVERNANCE_SIGNOFF=NOT_RECEIVED", flush=True)
    print("P141_SIGNED_NAYEON_AND_SMART_APP_CONTROL=NOT_APPROVED", flush=True)
    print("P141_USER_SCOPE_RELEASE=HOLD", flush=True)
    return 0 if success and stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
