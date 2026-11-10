"""P146: demonstrate whether unittest subTest failure retention owns a retired Tk root.

Runs the ORIGINAL unchanged failing Phase8.31 method in a native Windows child,
then independently probes Python unittest's *reporting references* without
altering the historical test source, product, security controls or test verdict.

This is diagnostic evidence only, NOT a passing original regression.
"""
from __future__ import annotations

import gc
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner,
    _verify_original_handle_policy,
)

P145_SHA = "7dc6e5377b2e9c4c2533c4a7dc99a262267d02aa"
BRANCH = "byok-c1-p146-windows-unittest-subtest-root-ownership-20261110"
MODULE = "tests.test_phase_831_effect_isolation"
TEST_ID = (
    MODULE + ".Phase831EffectIsolationTests."
    "test_static_production_import_closure_forbids_test_and_effect_routes"
)
MAX_CHILD_SECONDS = 55
SECRET_VARIABLES = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)


def _probe_original_using_real_unittest():
    """Return ONLY a weak reference, serializable facts and the original transcript.

    We do not edit unittest.TestResult or replace tearDownModule. Retaining
    result.failures inside this scope is intentional: the original module
    teardown sees the same ordinary unittest failure/result ownership.
    """
    original = importlib.import_module(MODULE)
    suite = unittest.defaultTestLoader.loadTestsFromName(TEST_ID)
    output = io.StringIO()
    runner = unittest.TextTestRunner(stream=output, verbosity=2)
    result = runner.run(suite)  # Includes ORIGINAL source + original tearDownModule.
    transcript = output.getvalue()

    roots = tuple(original._retired_tk_roots)
    weak_root = roots[0] if len(roots) == 1 else None
    root = weak_root() if weak_root is not None else None
    failure_carriers = []
    for carrier, _traceback_text in result.failures:
        case = getattr(carrier, "test_case", carrier)
        failure_carriers.append({
            "carrier_type": type(carrier).__name__,
            "test_case_type": type(case).__name__,
            "subtest_owns_original_case": (
                getattr(carrier, "test_case", None) is case
            ),
            "case_holds_retired_root": (
                root is not None and getattr(case, "root", None) is root
            ),
        })
    destroyed = None
    if root is not None:
        try:
            destroyed = not bool(root.winfo_exists())
        except Exception:
            destroyed = None
    facts = {
        "original_method_unchanged": True,
        "original_unittest_success_before_result_release": result.wasSuccessful(),
        "original_tests_run": result.testsRun,
        "original_failure_count": len(result.failures),
        "original_teardown_error_count": len(result.errors),
        "original_teardown_error_is_retired_tk_root": any(
            "retired fake Tk roots still live" in text
            for _test, text in result.errors
        ),
        "retired_weakref_count": len(roots),
        "retired_root_alive_during_unittest_result_ownership": root is not None,
        "destroyed_tk_widget_tree": destroyed,
        "failure_carriers": failure_carriers,
        "isolation_mode": "original_test_and_original_module_teardown_unmodified",
    }
    return weak_root, facts, transcript


def _worker() -> int:
    _guard_runner()
    weak_root, facts, transcript = _probe_original_using_real_unittest()
    # The TestResult and its _SubTest references were scoped inside the
    # preceding function; they are now eligible for GC without suppressing
    # the earlier genuine failing unittest outcome.
    gc.collect()
    facts["retired_root_alive_after_unittest_result_release"] = (
        weak_root is not None and weak_root() is not None
    )
    facts["original_unittest_transcript_sha256"] = (
        hashlib.sha256(transcript.encode("utf8")).hexdigest().upper()
    )
    print(json.dumps(facts, sort_keys=True))
    # Worker success means we collected observations, NOT original test PASS.
    return 0


def _run_child(argv, *, repo: Path, env: dict, out: Path) -> dict:
    try:
        with out.open("wb") as stream:
            proc = subprocess.run(
                argv, cwd=repo, env=env, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT,
                check=False, timeout=MAX_CHILD_SECONDS,
            )
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    except OSError:
        exit_code = 125
    raw = out.read_bytes() if out.exists() else b""
    return {
        "native_exit": exit_code,
        "log_bytes": len(raw),
        "log_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "text": raw.decode("utf8", "replace"),
    }


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P146 exact hosted Windows branch identity required")
    repo = Path(__file__).resolve().parents[1]
    if not (repo / "tests/test_phase_831_effect_isolation.py").is_file():
        raise RuntimeError("Original historical test absent")
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p146-unittest-root-owner"
    evidence.mkdir(parents=True, exist_ok=True)
    temp = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("Unexpected pre-existing temp root")
        os.mkdir(temp)
        created = True
        _verify_original_handle_policy(str(temp))
        env = os.environ.copy()
        for key in SECRET_VARIABLES:
            env.pop(key, None)
        env.update({key: str(temp) for key in ("TMP", "TEMP", "TMPDIR")})
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        print("P146_P139_UNCHANGED_NATIVE_HANDLE_GUARD=PASS", flush=True)
        print("P146_ORIGINAL_HISTORIC_TEST_ASSERTIONS=UNMODIFIED", flush=True)
        print("P146_NO_REAL_API_KEYS_OR_PRODUCTION_WINCRED_EFFECTS=TRUE", flush=True)

        original = _run_child(
            [sys.executable, "-B", "-m", "unittest", "-v", TEST_ID],
            repo=repo, env=env, out=evidence / "p146_original_unmodified_test.log",
        )
        diagnostic = _run_child(
            [sys.executable, "-B", "-m", __package__ +
             ".p146_windows_unittest_subtest_root_owner", "--probe"],
            repo=repo, env=env, out=evidence / "p146_unittest_owner_probe.log",
        )
        original_fails = (
            original["native_exit"] == 1
            and "FAILED (failures=1, errors=1)" in original["text"]
            and "retired fake Tk roots still live" in original["text"]
            and "workspace_window.py" in original["text"]
        )
        observations = None
        if diagnostic["native_exit"] == 0:
            try:
                observations = json.loads(diagnostic["text"].strip().splitlines()[-1])
            except (ValueError, IndexError, TypeError):
                observations = None
        case_owned_root = bool(
            observations and any(
                f["case_holds_retired_root"] and
                f["subtest_owns_original_case"]
                for f in observations["failure_carriers"]
            )
        )
        release_cleared_root = bool(
            observations and
            observations["retired_root_alive_during_unittest_result_ownership"] and
            not observations["retired_root_alive_after_unittest_result_release"]
        )
        manifest = {
            "base_commit": P145_SHA,
            "release_approved": False,
            "original_test_baseline_still_failed": original_fails,
            "original_native_exit": original["native_exit"],
            "original_log_sha256": original["log_sha256"],
            "probe_native_exit": diagnostic["native_exit"],
            "probe_log_sha256": diagnostic["log_sha256"],
            "unittest_failure_object_holds_root": case_owned_root,
            "root_released_with_test_result": release_cleared_root,
            "observations": observations,
            "classification": (
                "UNittest_failure_subtest_retention_explains_teardown_survivor"
                if original_fails and case_owned_root and release_cleared_root
                else "ROOT_LIFETIME_NOT_YET_EXPLAINED"
            ),
            "historical_static_import_assertion": "STILL_FAILING",
            "full_product_three_windows_regressions": "UNPASSED",
            "signed_local_companion_and_independent_reviewer": "HOLD",
            "production_credential_effect": "NONE",
        }
        (evidence / "p146_unittest_root_owner_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf8"
        )
        for field in ("original_test_baseline_still_failed",
                      "unittest_failure_object_holds_root",
                      "root_released_with_test_result", "classification"):
            print("P146_" + field.upper() + "=" + str(manifest[field]), flush=True)
        print("P146_ORIGINAL_NATIVE_EXIT=" + str(original["native_exit"]), flush=True)
        print("P146_PROBE_NATIVE_EXIT=" + str(diagnostic["native_exit"]), flush=True)
        print("P146_ORIGINAL_LOG_SHA256=" + original["log_sha256"], flush=True)
        print("P146_PROBE_LOG_SHA256=" + diagnostic["log_sha256"], flush=True)
        print("P146_HISTORICAL_STATIC_ASSERTION=HOLD", flush=True)
        print("P146_SIGNING_INDEPENDENT_REVIEW_AND_FULL_PRODUCT_REGRESSIONS=HOLD", flush=True)
        print("P146_USER_SCOPE_C1_RELEASE=HOLD", flush=True)
        # A successful CI observation is never a passing original test.
        return 0 if original_fails and observations is not None else 1
    finally:
        if created:
            try:
                st = temp.lstat()
                if (not temp.is_symlink() and
                        not (getattr(st, "st_file_attributes", 0) & 0x400) and
                        str(temp).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(temp)
                    print("P146_VERIFIED_DISPOSABLE_TEMP_CLEANUP=ATTEMPTED", flush=True)
                else:
                    print("P146_UNEXPECTED_ROOT_REPARSE_CLEANUP=REFUSED", flush=True)
            except Exception:
                print("P146_DISPOSABLE_TEMP_CLEANUP=UNCERTAIN", flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--probe"]:
        raise SystemExit(_worker())
    if sys.argv[1:]:
        raise SystemExit("Unexpected P146 arguments")
    raise SystemExit(main())
