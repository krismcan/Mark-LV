"""P143: original Windows fake-fixture and native file tests on VERIFIED temp root.

This repairs only the disposable GitHub runner test ENVIRONMENT, not product
files, assertions or source-integrity rules. Reuses unchanged P139 opened-
HANDLE Win32 exact-case/no-reparse directory proof for a fresh owned C: root.

P142 diagnosed 20 FAIL modules / 9 TIMEOUT; four legacy fake onboarding
modules yielded 97 temporary-ownership errors, plus one original native
text-file case. Run all five original modules, unfiltered, on real Windows.
Do not claim a full-product regression; original historical failures remain.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner,
    _verify_original_handle_policy,
)

ORIGINAL_MODULES = (
    ("phase829_integrated", "tests.test_phase_829_integrated_acceptance", 53),
    ("pre829_review", "tests.test_pre_829_a01_review_identity", 18),
    ("pre829_fake", "tests.test_pre_829_a02_fake_isolation", 12),
    ("pre829_cleanup", "tests.test_pre_829_host_pending_exception_cleanup", 17),
    ("native_text", "tests.test_text_file_creation", 87),
)
_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
_MAX_SECONDS = 95


def _run(name: str, mod: str, expected: int, *, root: Path,
         fixture: Path, evidence: Path) -> bool:
    log = evidence / ("p143_" + name + ".log")
    env = os.environ.copy()
    # Fresh interpreter per module. Never mutate system TEMP or original
    # security path rules. This is already the tested P139 fixture method.
    for var in ("TMPDIR", "TEMP", "TMP"):
        env[var] = str(fixture)
    try:
        with log.open("wb") as out:
            proc = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "-v", mod],
                cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=out, stderr=subprocess.STDOUT, timeout=_MAX_SECONDS,
                check=False,
            )
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = 124
    except OSError:
        code = 125
    raw = log.read_bytes() if log.exists() else b""
    text = raw.decode("utf8", "replace")
    found = _COUNT.findall(text)
    test_count = int(found[-1]) if found else -1
    lines = text.splitlines()
    failure_ids = [
        line.split(":", 1)[1].strip().split(" (", 1)[0]
        for line in lines if line.startswith(("FAIL: ", "ERROR: "))
    ]
    failing_footer = [
        line for line in lines if line.startswith("FAILED (")
    ]
    ok = (
        code == 0 and test_count == expected
        and any(line.strip() == "OK" for line in lines)
        and not failure_ids and not failing_footer
    )
    print("P143_ORIGINAL_MODULE=" + mod, flush=True)
    print("P143_MODULE_NATIVE_EXIT=" + name + "=" + str(code), flush=True)
    print("P143_MODULE_TEST_COUNT=" + name + "=" + str(test_count), flush=True)
    print("P143_MODULE_FAULT_TEST_IDS=" + name + "=" +
          ",".join(failure_ids[:40]), flush=True)
    print("P143_MODULE_LOG_SHA256=" + name + "=" +
          hashlib.sha256(raw).hexdigest().upper(), flush=True)
    print("P143_MODULE_VERDICT=" + name + "=" +
          ("PASS" if ok else "HOLD"), flush=True)
    return ok


def main() -> int:
    _guard_runner()
    source = Path(__file__).resolve().parents[1]
    artifact = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p143-safe-fake-temp-evidence"
    artifact.mkdir(parents=True, exist_ok=True)

    # Reuse the exact P139 trusted directory namespace required by the
    # historical verified HANDLE checker, with a fresh UUID per P143 run.
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    print("P143_ORIGINAL_TEST_SOURCES=BYTE_UNMODIFIED", flush=True)
    print("P143_ORIGINAL_GUARD_ON_TEST_FIXTURE=REQUIRED_PASS", flush=True)
    print("P143_GITHUB_DEFAULT_TEMP_UNSAFE_POLICY=UNCHANGED", flush=True)
    print("P143_HOSTED_WINDOWS_NO_REAL_USER_CREDENTIALS=TRUE", flush=True)
    results = []
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P143 random owned fixture pre-existed")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        print("P143_ORIGINAL_WIN32_OPENED_HANDLE_EXACT_ROOT_POLICY=PASS", flush=True)
        for name, module, expected in ORIGINAL_MODULES:
            results.append(_run(
                name, module, expected, root=source,
                fixture=fixture, evidence=artifact,
            ))
        count = sum(results)
        print("P143_ORIGINAL_FIVE_TEST_MODULES_PASS=" + str(count), flush=True)
        print("P143_ORIGINAL_FIVE_TEST_MODULES_HOLD=" +
              str(len(results) - count), flush=True)
        print("P143_ORIGINAL_MODULE_CASES_EXPECTED=187", flush=True)
        print("P143_PRODUCTION_FILESYSTEM_SECURITY_SOURCE=UNCHANGED", flush=True)
        print("P143_P135_FULL_UNFILTERED_WINDOWS_REGRESSIONS=NOT_PASSED", flush=True)
        print("P143_SIGNED_PRODUCTION_AND_INDEPENDENT_REVIEW=NOT_DONE", flush=True)
        print("P143_BYOK_C1_USER_SCOPE_RELEASE=HOLD", flush=True)
        return 0 if len(results) == 5 and all(results) else 1
    finally:
        if created:
            # Do not follow unexpected reparse or symlink modifications.
            try:
                meta = fixture.lstat()
                if (not fixture.is_symlink()
                        and not (getattr(meta, "st_file_attributes", 0) & 0x400)
                        and str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P143_OWNED_VERIFIED_TEMP_CLEANUP=ATTEMPTED", flush=True)
                else:
                    print("P143_UNEXPECTED_ROOT_REPARSE_CLEANUP_REFUSED=HOLD",
                          flush=True)
            except Exception:
                print("P143_CLEANUP_UNCERTAIN_ON_DISPOSABLE_RUNNER=HOLD",
                      flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
