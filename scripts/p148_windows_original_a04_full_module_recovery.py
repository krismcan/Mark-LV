"""P148: one bounded genuine Windows run of full original A04 recovery module.

P142's original 35s per-module diagnostic timed out. This executes ALL
unchanged tests in the module, using P139's verified owned fixed C: root.
It records the real full result, native exit and raw SHA256. A successful
collection is not an original test PASS unless actual exit 0 + unittest OK.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)

P147_PARENT = "f0e34bbbccec995e5d5d5e277e582702be8b9428"
BRANCH = "byok-c1-p148-original-windows-a04-full-module-recovery-20261110"
MODULE = "tests.test_pre_829_a04_two_process_recovery"
SOURCE = "tests/test_pre_829_a04_two_process_recovery.py"
MAX_SECONDS = 195
_SECRETS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN")
_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P148 exact GitHub Windows branch required")
    root = Path(__file__).resolve().parents[1]
    source = root / SOURCE
    prior = subprocess.run(
        ["git", "-C", str(root), "show", P147_PARENT + ":" + SOURCE],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False,
    )
    if prior.returncode != 0 or source.read_bytes() != prior.stdout:
        raise RuntimeError("Original A04 historical source changed")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p148-a04-original-module"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("Unexpected pre-existing owned test fixture")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        env = os.environ.copy()
        for key in _SECRETS:
            env.pop(key, None)
        for key in ("TEMP", "TMP", "TMPDIR"):
            env[key] = str(fixture)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        print("P148_UNMODIFIED_ORIGINAL_A04_TEST_MODULE=TRUE", flush=True)
        print("P148_VERIFIED_NATIVE_OPENED_HANDLE_TEMP_ROOT=PASS", flush=True)
        print("P148_TEST_MODULE_SHA256=" + source_sha, flush=True)
        print("P148_ORIGINAL_TEST_METHOD_FILTER=NONE", flush=True)
        print("P148_CHILD_PROCESS_TESTS=DISPOSABLE_WINDOWS_ONLY", flush=True)

        log = evidence / "p148_original_A04_full_module.log"
        start = time.monotonic()
        try:
            with log.open("wb") as output:
                proc = subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "-v", MODULE],
                    cwd=root, env=env, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT,
                    timeout=MAX_SECONDS, check=False,
                )
            native = proc.returncode
        except subprocess.TimeoutExpired:
            native = 124
        except OSError:
            native = 125
        seconds = round(time.monotonic() - start, 3)
        raw = log.read_bytes() if log.exists() else b""
        data = raw.decode("utf8", "replace")
        lines = data.splitlines()
        count_hits = _COUNT.findall(data)
        count = int(count_hits[-1]) if count_hits else None
        faults = [line.split(":", 1)[1].strip()
                  for line in lines if line.startswith(("ERROR: ", "FAIL: "))]
        footer = [line for line in lines if line.startswith("FAILED (")]
        passed = (
            native == 0 and count is not None and count > 0
            and any(line.strip() == "OK" for line in lines)
            and not faults and not footer
        )
        status = "PASS" if passed else "TIMEOUT" if native == 124 else "HOLD"
        receipt = {
            "source_commit": P147_PARENT,
            "original_test_module": MODULE,
            "original_test_bytes_unchanged": True,
            "original_test_source_sha256": source_sha,
            "test_methods_filtered": False,
            "verified_native_handle_temp_root": True,
            "subprocess_max_seconds": MAX_SECONDS,
            "native_exit": native,
            "test_count_with_complete_footer": count,
            "native_result": status,
            "duration_seconds": seconds,
            "failed_test_ids": faults,
            "failed_footer": footer[-1] if footer else None,
            "raw_log_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "raw_log_bytes": len(raw),
            "P142_original_35s_timeout": "PRESERVED_AS_NEGATIVE_HISTORY",
            "reviewer_approved_full_suite_partition": False,
            "three_accepted_full_product_regressions": 0,
            "production_release_approved": False,
        }
        output = evidence / "p148_original_A04_windows_manifest.json"
        output.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf8",
        )
        print("P148_ORIGINAL_A04_NATIVE_EXIT=" + str(native), flush=True)
        print("P148_ORIGINAL_A04_RAN_TESTS=" + str(count), flush=True)
        print("P148_ORIGINAL_A04_VERDICT=" + status, flush=True)
        print("P148_ORIGINAL_A04_SECONDS=" + str(seconds), flush=True)
        print("P148_ORIGINAL_A04_FAILURE_IDS=" + str(len(faults)), flush=True)
        print("P148_ORIGINAL_A04_LOG_SHA256=" + receipt["raw_log_sha256"], flush=True)
        print("P148_QUALIFIED_INDEPENDENT_REVIEW=NOT_OBTAINED", flush=True)
        print("P148_FULL_PRODUCT_WINDOWS_TRIAD=NOT_PASSED", flush=True)
        print("P148_USER_SCOPE_C1_PRODUCTION_RELEASE=HOLD", flush=True)
        # A diagnostic collection succeeds if its genuine raw result exists.
        # Test success must be independently read from native_exit/status.
        return 0 if raw and native in (0, 1, 124, 125) else 1
    finally:
        if created:
            try:
                st = fixture.lstat()
                if (not fixture.is_symlink() and
                        not (getattr(st, "st_file_attributes", 0) & 0x400) and
                        str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P148_OWNED_DISPOSABLE_WINDOWS_ROOT_CLEANUP=ATTEMPTED",
                          flush=True)
                else:
                    print("P148_REPARSE_OR_IDENTITY_CHANGE_CLEANUP=REFUSED",
                          flush=True)
            except Exception:
                print("P148_FIXTURE_CLEANUP=UNCERTAIN_EPHEMERAL_HOSTED_RUNNER",
                      flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
