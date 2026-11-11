"""P152 read-only P76 historical branch-contract evidence on genuine hosted Windows.

Preserves the original P76 gate, original P76 tests, downstream production
code, P139 strict native Win32 handle policy and P140 signed frozen launch.
Two real children: direct actual-branch P76 refusal; entire unchanged
historical P76 unittest module. Neither may create production release GO.
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

BASE = "6d393b78c349bc07d9110e15f222e26f1dbe05f7"
BRANCH = "byok-c1-p152-p76-historical-branch-governance-20261111"
ORIGINAL_PINNED_BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
GATE = "tests/phase8_byok_c1_p76_scope.py"
TEST = "tests/test_phase8_byok_c1_p76_scope.py"
MODULE = "tests.test_phase8_byok_c1_p76_scope"
ORIGINAL_TEST_CLASS = "P76OfflineRoutingTests"
DIRECT = (
    "from tests.phase8_byok_c1_p76_scope "
    "import assert_p76_offline_integrity; "
    "print(assert_p76_offline_integrity())"
)
_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
_SECRET_ENV = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL, timeout=25, check=False,
    )
    if proc.returncode:
        raise RuntimeError("P152 read-only Git provenance request failed")
    return proc.stdout


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _source_pin(gate: Path) -> str:
    """Read the immutable original branch constant without executing it."""
    parsed = ast.parse(gate.read_text(encoding="utf-8"), filename=str(gate))
    assignments = [
        n for n in parsed.body if isinstance(n, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "BRANCH"
                for target in n.targets)
    ]
    if len(assignments) != 1:
        raise RuntimeError("Historical P76 branch pin is not a unique source literal")
    branch = ast.literal_eval(assignments[0].value)
    if type(branch) is not str or branch != ORIGINAL_PINNED_BRANCH:
        raise RuntimeError("Original P76 frozen branch identity changed")
    return branch


def _original_case_count(test: Path) -> int:
    parsed = ast.parse(test.read_text(encoding="utf-8"), filename=str(test))
    classes = [
        n for n in parsed.body
        if isinstance(n, ast.ClassDef) and n.name == ORIGINAL_TEST_CLASS
    ]
    if len(classes) != 1:
        raise RuntimeError("Historical P76 original test class changed")
    cases = [n.name for n in classes[0].body
             if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    if len(cases) != 10 or len(set(cases)) != len(cases):
        raise RuntimeError("Historical P76 original test inventory drift")
    return len(cases)


def _run_child(repo: Path, env: dict[str, str], out: Path,
               args: list[str], timeout: int) -> dict:
    began = time.monotonic()
    try:
        with out.open("wb") as stream:
            result = subprocess.run(
                [sys.executable, "-B", *args],
                cwd=repo, env=env, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT,
                check=False, timeout=timeout,
            )
        native = result.returncode
    except subprocess.TimeoutExpired:
        native = 124
    except OSError:
        native = 125
    raw = out.read_bytes() if out.is_file() else b""
    return {
        "native_exit": native,
        "duration_seconds": round(time.monotonic() - began, 3),
        "raw_log_sha256": _sha(raw),
        "raw_log_bytes": len(raw),
        "log_lines": raw.decode("utf-8", "replace").splitlines(),
    }


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P152 exact hosted Windows branch required")
    repo = Path(__file__).resolve().parents[1]
    if _git(repo, "branch", "--show-current").decode("ascii").strip() != BRANCH:
        raise RuntimeError("P152 source worktree branch does not match audit")
    if _git(repo, "merge-base", "HEAD", BASE).decode("ascii").strip() != BASE:
        raise RuntimeError("P152 exact P151 ancestor not preserved")
    source_custody = []
    for name in (GATE, TEST):
        current = (repo / name).read_bytes()
        if current != _git(repo, "show", BASE + ":" + name):
            raise RuntimeError("P152 historical gate or test source modified: " + name)
        source_custody.append({
            "file": name, "sha256": _sha(current), "bytes": len(current),
            "unchanged_from_exact_P151": True,
        })
    original_pin = _source_pin(repo / GATE)
    case_count = _original_case_count(repo / TEST)
    if original_pin == BRANCH:
        raise RuntimeError("Invalid diagnostic: current branch is original P76 branch")

    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p152-original-p76"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("Unexpected existing P152 test fixture path")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        env = os.environ.copy()
        for name in _SECRET_ENV:
            env.pop(name, None)
        for name in ("TMP", "TEMP", "TMPDIR"):
            env[name] = str(fixture)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        print("P152_P151_SOURCE_AND_ORIGINAL_P76_TESTS_UNCHANGED=PASS", flush=True)
        print("P152_P139_ORIGINAL_NATIVE_HANDLE_ROOT_VERIFIER=PASS", flush=True)
        print("P152_ORIGINAL_P76_BRANCH_LITERAL=" + original_pin, flush=True)
        print("P152_ACTUAL_CURRENT_BRANCH=" + BRANCH, flush=True)
        print("P152_HISTORICAL_TESTS_EXPECTED=" + str(case_count), flush=True)

        # Execute the genuine guard with real Git branch metadata. No patching
        # mocks, tests, manifests, branch names or authentication results.
        direct = _run_child(
            repo, env, evidence / "p152_actual_branch_original_P76_refusal.log",
            ["-c", DIRECT], timeout=25,
        )
        direct_refused = (
            direct["native_exit"] == 1 and
            any("P76 offline source refused: wrong exact P76 prototype branch"
                in line for line in direct["log_lines"])
        )

        # All historical tests (including expected original current-branch
        # positive-admission failures) execute with their unchanged assertions.
        suite = _run_child(
            repo, env, evidence / "p152_original_P76_full_module.log",
            ["-m", "unittest", "-v", MODULE], timeout=110,
        )
        counts = [int(m.group(1)) for line in suite["log_lines"]
                  if (m := _COUNT.search(line))]
        observed_cases = counts[-1] if counts else None
        failed_ids = [
            line.split(":", 1)[1].strip() for line in suite["log_lines"]
            if line.startswith(("FAIL: ", "ERROR: "))
        ]
        failed_footers = [
            line for line in suite["log_lines"] if line.startswith("FAILED (")
        ]
        native_pass = (
            suite["native_exit"] == 0
            and observed_cases == case_count
            and any(line.strip() == "OK" for line in suite["log_lines"])
            and not failed_ids and not failed_footers
        )
        module_verdict = (
            "PASS" if native_pass
            else "TIMEOUT" if suite["native_exit"] == 124 else "HOLD"
        )

        receipt = {
            "exact_P151_base": BASE,
            "current_head": _git(repo, "rev-parse", "HEAD").decode("ascii").strip(),
            "actual_current_branch": BRANCH,
            "unmodified_original_P76_branch_pin": original_pin,
            "historical_contract": "EXACT_HISTORICAL_BRANCH_ONLY",
            "source_custody": source_custody,
            "source_or_historical_tests_modified": False,
            "direct_current_branch_refusal": {
                "actual_guard_executed_unmodified_with_real_git": True,
                "native_exit": direct["native_exit"],
                "expected_negative_observed": direct_refused,
                "duration_seconds": direct["duration_seconds"],
                "raw_log_sha256": direct["raw_log_sha256"],
                "raw_log_bytes": direct["raw_log_bytes"],
            },
            "full_original_P76_module": {
                "entire_module_executed_unfiltered": True,
                "expected_original_methods": case_count,
                "observed_full_unittest_footer_count": observed_cases,
                "native_exit": suite["native_exit"],
                "verdict": module_verdict,
                "duration_seconds": suite["duration_seconds"],
                "failed_original_test_ids": failed_ids,
                "failed_original_test_footer": (
                    failed_footers[-1] if failed_footers else None
                ),
                "raw_log_sha256": suite["raw_log_sha256"],
                "raw_log_bytes": suite["raw_log_bytes"],
            },
            "historical_refusals_waived": False,
            "original_full_product_regression_incomplete": True,
            "full_product_windows_regression_triad_passes": 0,
            "qualified_external_test_governance": "NOT_OBTAINED",
            "qualified_external_security_review": "NOT_OBTAINED",
            "publisher_signing_and_code_integrity_policy_GO": "NOT_OBTAINED",
            "original_privileged_G0_to_G6": "OPEN",
            "user_scope_BYOK_C1_release": "HOLD",
            "real_keys_or_Kristian_credential_effects": False,
        }
        (evidence / "p152_original_P76_branch_governance_manifest.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("P152_ACTUAL_P76_GUARD_NATIVE_EXIT=" + str(direct["native_exit"]),
              flush=True)
        print("P152_ACTUAL_BRANCH_DENIAL_GENUINE=" + str(direct_refused),
              flush=True)
        print("P152_ACTUAL_BRANCH_DENIAL_LOG_SHA256=" +
              direct["raw_log_sha256"], flush=True)
        print("P152_ORIGINAL_FULL_P76_MODULE_EXIT=" + str(suite["native_exit"]),
              flush=True)
        print("P152_ORIGINAL_FULL_P76_MODULE_CASES=" + str(observed_cases),
              flush=True)
        print("P152_ORIGINAL_FULL_P76_MODULE_STATUS=" + module_verdict,
              flush=True)
        print("P152_ORIGINAL_FULL_P76_MODULE_FAILED_TEST_IDS=" +
              str(len(failed_ids)), flush=True)
        print("P152_ORIGINAL_FULL_P76_MODULE_LOG_SHA256=" +
              suite["raw_log_sha256"], flush=True)
        print("P152_EXTERNAL_REVIEW_AND_HISTORIC_SUITE_GOVERNANCE=NOT_OBTAINED",
              flush=True)
        print("P152_FULL_PRODUCT_WINDOWS_TRIAD=NOT_PASSED", flush=True)
        print("P152_USER_SCOPE_BYOK_C1_RELEASE=HOLD", flush=True)
        # A TRUE exact-branch security denial is mandatory; the original
        # historical suite is NOT allowed to pass by mock or waiver.
        return 0 if (
            direct_refused and
            suite["native_exit"] in (0, 1, 124, 125) and
            suite["raw_log_bytes"] > 0
        ) else 1
    finally:
        if created:
            try:
                st = fixture.lstat()
                if (not fixture.is_symlink()
                        and not (getattr(st, "st_file_attributes", 0) & 0x400)
                        and str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P152_EPHEMERAL_OWNED_ROOT_CLEANUP=ATTEMPTED",
                          flush=True)
                else:
                    print("P152_UNTRUSTED_REPARSE_CLEANUP=REFUSED", flush=True)
            except Exception:
                print("P152_EPHEMERAL_TEMP_ROOT_CLEANUP=UNCERTAIN", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
