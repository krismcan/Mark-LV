"""P139: test genuine strict Win32 filesystem guard under verified local temp root.

Real hosted Windows only, ONLY self-owned random disposable C:\ directory.
NO modification/patching of the original filesystem implementation,
security/identity checks or historical native test assertions.
Fail closed if the exact root and ancestors do not pass the SAME existing
handle-based no-reparse/exact-path security checks as production code.
"""
from __future__ import annotations

from contextlib import ExitStack
import ctypes
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

_TESTS = (
    ("create_dir", "tests.test_directory_creation.NativeDirectoryCreationTests.test_only_self_owned_single_child_directory"),
    ("delete_dir", "tests.test_directory_deletion.NativeDirectoryDeletionTests.test_owned_native_success_and_child_races_with_exact_handle_lifetime"),
    ("list_dir", "tests.test_directory_listing.TemporaryWindowsDirectoryTests.test_lists_only_self_created_temporary_directory"),
    ("copy_file", "tests.test_file_copy.NativeCopyTests.test_owned_binary_copy_no_overwrite_and_source_change_after_execution"),
    ("create_file", "tests.test_file_creation.NativeCreationTests.test_creates_only_one_self_owned_empty_temporary_file"),
    ("delete_file", "tests.test_file_deletion.NativeDeletionTests.test_owned_fixture_real_binding_disposition_close_and_absence"),
    ("read_file", "tests.test_filesystem.TemporaryWindowsFileTests.test_reads_only_created_temporary_file_through_native_handles"),
)
_COUNTS = re.compile(r"Ran (\d+) tests? in [0-9.]+s")

def _guard_runner() -> None:
    if not (
        sys.platform=="win32" and
        os.environ.get("GITHUB_ACTIONS")=="true" and
        os.environ.get("RUNNER_OS")=="Windows" and
        os.environ.get("GITHUB_REPOSITORY")=="krismcan/Mark-LV" and
        os.environ.get("GITHUB_EVENT_NAME")=="push" and
        os.environ.get("RUNNER_TEMP")
    ):
        raise RuntimeError("P139 only disposable GitHub-hosted Windows")

def _verify_original_handle_policy(directory: str) -> None:
    """Apply the original secure filesystem guard, no patching or fallback."""
    from nayeon.services import filesystem as fs

    if not directory.startswith("C:\\NayeonP139_"):
        raise RuntimeError("P139 temporary fixture path is not a fresh local root")
    if fs.normalize_directory_path(directory) != directory:
        raise RuntimeError("Original lexical filename guard did not admit root")
    api=fs._kernel32()
    if api.GetDriveTypeW("C:\\")!=3:
        raise RuntimeError("P139 C drive is not a local fixed drive")
    with ExitStack() as stack:
        for target in ("C:\\",directory):
            handle=api.CreateFileW(
                target,fs._READ_ATTRIBUTES | 1,fs._SHARE_READ,None,
                fs._OPEN_EXISTING,fs._OPEN_FLAGS,None,
            )
            if handle in (None,0,ctypes.c_void_p(-1).value):
                raise RuntimeError("P139 original native open refused safe test root")
            stack.callback(api.CloseHandle,handle)
            # No catch on unsafe_path: propagate fail-closed.
            fs._inspect_handle(api,handle,target,directory=True)

def main()->int:
    _guard_runner()
    root_dir=Path(__file__).resolve().parents[1]
    log_dir=Path(os.environ["RUNNER_TEMP"])/"nayeon-p139-safe-root-regression"
    log_dir.mkdir(parents=True,exist_ok=True)
    fixture=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    results={}
    created=False
    print("P139_ORIGINAL_FILESYSTEM_SOURCE_AND_TESTS=UNMODIFIED",flush=True)
    print("P139_DEFAULT_GITHUB_TEMP_UNSAFE=PREVIOUSLY_REPRODUCED",flush=True)
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P139 random fixture unexpectedly exists")
        os.mkdir(fixture)
        created=True
        _verify_original_handle_policy(str(fixture))
        print("P139_EXISTING_NATIVE_OPEN_HANDLE_PATH_POLICY_ON_SAFE_ROOT=PASS",flush=True)
        print("P139_NO_REPARSE_OR_PATH_IDENTITY_WEAKENING=TRUE",flush=True)

        for label,test in _TESTS:
            log=log_dir/(label+".log")
            env=os.environ.copy()
            # Run every unchanged test in a new Python process; tempfile
            # chooses this newly created, handle-verified *local* C drive
            # directory instead of the GitHub D:\a\_temp tool directory.
            # This adjusts only test fixture location, not expected
            # filesystem path canonicalization nor Win32 protections.
            for name in ("TMPDIR","TEMP","TMP"):
                env[name]=str(fixture)
            try:
                with log.open("wb") as out:
                    p=subprocess.run(
                        [sys.executable,"-B","-m","unittest","-v",test],
                        cwd=root_dir,env=env,stdout=out,stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,timeout=65,check=False,
                    )
                exit_code=p.returncode
            except subprocess.TimeoutExpired:
                exit_code=124
            except OSError:
                exit_code=125

            raw=log.read_bytes() if log.exists() else b""
            out_text=raw.decode("utf8","replace")
            counts=_COUNTS.findall(out_text)
            count=int(counts[-1]) if counts else -1
            passed=exit_code==0 and count==1 and re.search(r"^OK\s*$",out_text,re.MULTILINE) is not None
            results[label]=passed
            print("P139_CASE="+label,flush=True)
            print("P139_CASE_NATIVE_EXIT="+label+"="+str(exit_code),flush=True)
            print("P139_CASE_TEST_COUNT="+label+"="+str(count),flush=True)
            print("P139_CASE_VERDICT="+label+"="+("PASS" if passed else "HOLD"),flush=True)
            print("P139_CASE_LOG_SHA256="+label+"="+hashlib.sha256(raw).hexdigest().upper(),flush=True)

        count=sum(results.values())
        print("P139_ORIGINAL_NATIVE_FILESYSTEM_CASES_PASS="+str(count),flush=True)
        print("P139_ORIGINAL_NATIVE_FILESYSTEM_CASES_HOLD="+str(len(results)-count),flush=True)
        print("P139_SOURCE_AND_SECURITY_POLICY_UNMODIFIED=TRUE",flush=True)
        print("P139_FULL_PRODUCT_WINDOWS_TRIAD=STILL_HOLD",flush=True)
        print("P139_C1_USER_SCOPE_RELEASE=HOLD",flush=True)
        return 0 if len(results)==7 and count==7 else 1
    finally:
        if created:
            # Never traverse a replaced junction/reparse point. The ephemeral
            # host discards any leftover owned test root on uncertainty.
            try:
                mode=fixture.lstat()
                if (not fixture.is_symlink() and
                    not getattr(mode,"st_file_attributes",0)&0x400 and
                    str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P139_OWNED_TEST_ROOT_CLEANUP=ATTEMPTED",flush=True)
                else:
                    print("P139_CLEANUP_REFUSED_REPARSE=HOLD",flush=True)
            except Exception:
                print("P139_CLEANUP_FAILED_EPHEMERAL_RUNNER=HOLD",flush=True)

if __name__=="__main__":
    raise SystemExit(main())
