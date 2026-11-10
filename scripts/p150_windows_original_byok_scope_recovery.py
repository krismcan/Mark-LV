"""P150 — original BYOK-B ancestry/scope test module under genuine hosted Windows.

One COMPLETE unfiltered original historical module. Native exit and unittest
footer are authoritative; a successful diagnostic collection is never a
passing original test when the module returns failure or timeout.

No test/source edits, credential effects, provider calls or production release.
"""
from __future__ import annotations

import ast
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

BASE = "11e3f0963c9ff37469d6b4c75b2ddb5407cc9706"
BRANCH = "byok-c1-p150-windows-original-byok-scope-recovery-20261110"
MODULE = "tests.test_phase8_byok_scope_integrity"
SOURCE = "tests/test_phase8_byok_scope_integrity.py"
SUITE_CLASS = "ExactBYOKScopeTests"
MAX_SECONDS = 190
EXPECTED_ORIGINAL_METHODS = 13
COUNT = re.compile(r"Ran (\d+) tests? in [\d.]+s")
SECRET_ENV_KEYS = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)


def _original_methods(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=SOURCE)
    classes = [node for node in tree.body if
               isinstance(node, ast.ClassDef) and node.name == SUITE_CLASS]
    if len(classes) != 1:
        raise RuntimeError("Original historical BYOK suite class changed")
    methods = sorted(
        node.name for node in classes[0].body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )
    if len(methods) != EXPECTED_ORIGINAL_METHODS or len(methods) != len(set(methods)):
        raise RuntimeError("Original BYOK exact-scope method inventory drift")
    return tuple(methods)


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P150 exact disposable Windows branch identity required")
    repo = Path(__file__).resolve().parents[1]
    original = repo / SOURCE
    historic = subprocess.run(
        ["git", "-C", str(repo), "show", BASE + ":" + SOURCE],
        capture_output=True, timeout=25, check=False,
    )
    if historic.returncode != 0 or original.read_bytes() != historic.stdout:
        raise RuntimeError("P150 original historic BYOK test bytes modified")
    methods = _original_methods(original)
    original_sha = hashlib.sha256(original.read_bytes()).hexdigest().upper()
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p150-original-byok-scope"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False

    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("P150 unexpected existing test fixture root")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        print("P150_P139_EXACT_NATIVE_WIN32_OPENED_HANDLE_ROOT=PASS", flush=True)
        print("P150_ORIGINAL_BYOK_TEST_ASSERTIONS_UNCHANGED=TRUE", flush=True)
        print("P150_ORIGINAL_BYOK_METHODS_INVENTORIED=" + str(len(methods)),
              flush=True)
        print("P150_UNFILTERED_ORIGINAL_MODULE=TRUE", flush=True)
        print("P150_TEST_SOURCE_SHA256=" + original_sha, flush=True)

        env = os.environ.copy()
        for secret in SECRET_ENV_KEYS:
            env.pop(secret, None)
        for variable in ("TMP", "TEMP", "TMPDIR"):
            env[variable] = str(fixture)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        log = evidence / "p150_original_BYOK_scope_entire_module.log"
        start = time.monotonic()
        try:
            with log.open("wb") as out:
                proc = subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "-v", MODULE],
                    cwd=repo, env=env, stdin=subprocess.DEVNULL,
                    stdout=out, stderr=subprocess.STDOUT,
                    timeout=MAX_SECONDS, check=False,
                )
            native_exit = proc.returncode
        except subprocess.TimeoutExpired:
            native_exit = 124
        except OSError:
            native_exit = 125

        elapsed = round(time.monotonic() - start, 3)
        raw = log.read_bytes() if log.exists() else b""
        lines = raw.decode("utf-8", "replace").splitlines()
        test_counts = [int(found.group(1)) for line in lines
                       if (found := COUNT.search(line))]
        completed = test_counts[-1] if test_counts else None
        failure_ids = [line.split(":", 1)[1].strip()
                       for line in lines
                       if line.startswith(("FAIL: ", "ERROR: "))]
        failed_footers = [line for line in lines if line.startswith("FAILED (")]
        ok_footers = [line for line in lines if line.strip() == "OK"]
        passed = (
            native_exit == 0 and completed == len(methods)
            and len(ok_footers) > 0 and not failed_footers
            and not failure_ids
        )
        verdict = ("PASS" if passed else
                   "TIMEOUT" if native_exit == 124 else "HOLD")
        manifest = {
            "base_sha": BASE,
            "original_module": MODULE,
            "original_test_source_sha256": original_sha,
            "historical_test_bytes_unchanged": True,
            "unfiltered_test_methods": list(methods),
            "expected_original_tests": len(methods),
            "observed_final_unittest_count": completed,
            "native_exit_code": native_exit,
            "original_module_verdict": verdict,
            "seconds_elapsed": elapsed,
            "unittest_failure_or_error_ids": failure_ids,
            "unittest_failed_footer": (
                failed_footers[-1] if failed_footers else None
            ),
            "log_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "log_bytes": len(raw),
            "verified_original_native_Win32_handle_temp_root": True,
            "historical_P142_35_second_timeout": "PRESERVED",
            "current_branch_legacy_source_seals": "NOT_WAIVED",
            "independent_test_governance": "NOT_OBTAINED",
            "independent_user_scope_security_review": "NOT_OBTAINED",
            "signed_companion_and_Code_Integrity_approval": "NOT_OBTAINED",
            "three_complete_full_product_Windows_regressions": 0,
            "credential_effects_on_Kristian": False,
            "production_release": False,
        }
        (evidence / "p150_original_byok_scope_native_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("P150_ORIGINAL_MODULE_NATIVE_EXIT=" + str(native_exit), flush=True)
        print("P150_ORIGINAL_MODULE_TEST_COUNT=" + str(completed), flush=True)
        print("P150_ORIGINAL_MODULE_VERDICT=" + verdict, flush=True)
        print("P150_ORIGINAL_MODULE_SECONDS=" + str(elapsed), flush=True)
        print("P150_ORIGINAL_MODULE_FAILURE_IDS=" + str(len(failure_ids)),
              flush=True)
        print("P150_ORIGINAL_MODULE_LOG_SHA256=" + manifest["log_sha256"],
              flush=True)
        print("P150_FULL_PRODUCT_THREE_WINDOWS_REGRESSIONS=NOT_PASSED", flush=True)
        print("P150_QUALIFIED_INDEPENDENT_REVIEW_AND_SIGNER=NOT_OBTAINED",
              flush=True)
        print("P150_USER_SCOPE_BYOK_C1_RELEASE=HOLD", flush=True)
        # Tool success indicates native result COLLECTED, NOT original pass.
        return 0 if len(raw) > 0 and native_exit in (0, 1, 124, 125) else 1
    finally:
        if created:
            try:
                st = fixture.lstat()
                if (not fixture.is_symlink()
                        and not (getattr(st, "st_file_attributes", 0) & 0x400)
                        and str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P150_OWNED_TEST_TEMP_CLEANUP=ATTEMPTED", flush=True)
                else:
                    print("P150_TEMP_ROOT_REPARSE_OR_IDENTITY_DRIFT=REFUSE_CLEANUP",
                          flush=True)
            except Exception:
                print("P150_EPHEMERAL_TEMP_CLEANUP=UNCERTAIN", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
