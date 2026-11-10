"""P138 bounded real Windows triage of 10 P135 functional ERROR/FAIL test IDs.

No old assertion is edited, disabled, ignored, or marked PASS. This diagnostic
executes exactly the seven genuine temporary-file/directory native ERROR
cases and three Connection-page interface-contract failures in individual
fresh Python processes on a disposable GitHub Windows machine.

Only test-owned filesystem temp fixtures; no real BYOK key, WinCred,
protected registry, signing or privileged service.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

_CASES = (
    ("fs_create_dir", "tests.test_directory_creation.NativeDirectoryCreationTests.test_only_self_owned_single_child_directory"),
    ("fs_delete_dir", "tests.test_directory_deletion.NativeDirectoryDeletionTests.test_owned_native_success_and_child_races_with_exact_handle_lifetime"),
    ("fs_list_dir", "tests.test_directory_listing.TemporaryWindowsDirectoryTests.test_lists_only_self_created_temporary_directory"),
    ("fs_copy_file", "tests.test_file_copy.NativeCopyTests.test_owned_binary_copy_no_overwrite_and_source_change_after_execution"),
    ("fs_create_file", "tests.test_file_creation.NativeCreationTests.test_creates_only_one_self_owned_empty_temporary_file"),
    ("fs_delete_file", "tests.test_file_deletion.NativeDeletionTests.test_owned_fixture_real_binding_disposition_close_and_absence"),
    ("fs_read_file", "tests.test_filesystem.TemporaryWindowsFileTests.test_reads_only_created_temporary_file_through_native_handles"),
    ("p86_button_count", "tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests.test_live_connection_page_default_is_explicitly_unobserved"),
    ("p86_button_count_advisory", "tests.test_p86_live_pending_status_integration.P86ActualConnectionViewTests.test_no_credential_action_and_no_implicit_refresh"),
    ("p87_button_count", "tests.test_p87_readonly_custody_observation.P87ActualConnectionTests.test_production_default_remains_not_observed_without_any_session"),
)
_RESULT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
_ALLOWED = re.compile(r"\A(?:fs_[a-z_]+|p86_[a-z_]+|p87_[a-z_]+)\Z")

def main()->int:
    if not (
        sys.platform=="win32" and
        os.environ.get("GITHUB_ACTIONS")=="true" and
        os.environ.get("RUNNER_OS")=="Windows" and
        os.environ.get("GITHUB_REPOSITORY")=="krismcan/Mark-LV" and
        os.environ.get("GITHUB_EVENT_NAME")=="push" and
        os.environ.get("RUNNER_TEMP")
    ):
        print("P138_EPHEMERAL_WINDOWS_TRIAGE_REQUIRED=REFUSED",flush=True)
        return 4

    root=Path(__file__).resolve().parents[1]
    output_dir=Path(os.environ["RUNNER_TEMP"])/"nayeon-p138-regression-triage"
    output_dir.mkdir(parents=True,exist_ok=True)
    statuses={}
    print("P138_EXACT_HISTORICAL_ERROR_AND_FAIL_CASES="+str(len(_CASES)),flush=True)
    print("P138_ORIGINAL_ASSERTIONS=UNCHANGED_NO_SKIPS",flush=True)
    print("P138_NO_PRODUCTION_KEY_OR_WIN_CREDENTIAL_EFFECTS=TRUE",flush=True)
    for label,test_id in _CASES:
        if not _ALLOWED.fullmatch(label):
            raise AssertionError("Unknown diagnostic label")
        log=output_dir/(label+".log")
        timed_out=False
        try:
            with log.open("wb") as sink:
                result=subprocess.run(
                    [sys.executable,"-B","-m","unittest","-v",test_id],
                    cwd=root,stdout=sink,stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,timeout=50,check=False,
                )
            code=result.returncode
        except subprocess.TimeoutExpired:
            code=124
            timed_out=True
        except OSError:
            code=125
        raw=log.read_bytes() if log.exists() else b""
        output=raw.decode("utf-8","replace")
        match=_RESULT.findall(output)
        count=int(match[-1]) if match else -1
        success=(code==0 and count==1 and "OK" in output and not timed_out)
        status="PASS_IN_ISOLATION" if success else (
            "TIMEOUT" if timed_out else "FAILED_IN_ISOLATION"
        )
        statuses[label]=status
        exceptions=[line.strip().split(":",1)[0].strip()
                    for line in output.splitlines()
                    if re.match(r"^\s*(?:AssertionError|OSError|PermissionError|"
                       r"FileNotFoundError|AttributeError|TypeError|ValueError|"
                       r"RuntimeError|NotImplementedError|NameError|ImportError|"
                       r"WindowsError):",line)]
        exception_type=exceptions[-1] if exceptions else "UNCLASSIFIED"
        print("P138_CASE="+label,flush=True)
        print("P138_CASE_STATUS="+label+"="+status,flush=True)
        print("P138_CASE_NATIVE_EXIT="+label+"="+str(code),flush=True)
        print("P138_CASE_TEST_COUNT="+label+"="+str(count),flush=True)
        print("P138_CASE_EXCEPTION_CLASS="+label+"="+exception_type,flush=True)
        print("P138_CASE_LOG_SHA256="+label+"="+hashlib.sha256(raw).hexdigest().upper(),flush=True)
    print("P138_CASES_REPRODUCED_FAILED="+str(sum(v=="FAILED_IN_ISOLATION" for v in statuses.values())),flush=True)
    print("P138_CASES_PASSED_IN_ISOLATION="+str(sum(v=="PASS_IN_ISOLATION" for v in statuses.values())),flush=True)
    print("P138_CASES_TIMED_OUT="+str(sum(v=="TIMEOUT" for v in statuses.values())),flush=True)
    print("P138_FULL_PRODUCT_WINDOWS_TRIAD=STILL_HOLD",flush=True)
    print("P138_INDEPENDENT_REVIEW_AND_SIGNED_LAUNCH=NOT_APPROVED",flush=True)
    print("P138_C1_USER_SCOPE_RELEASE=HOLD",flush=True)
    return 0 if len(statuses)==len(_CASES) else 1

if __name__=="__main__":
    raise SystemExit(main())
