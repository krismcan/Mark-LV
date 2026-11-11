"""P153 current-branch reviewer-CANDIDATE test contract; no historical waiver.

Only *named, unchanged* original negative and reduced current-user-scope tests
are executed on disposable GitHub-hosted Windows. A genuine candidate PASS is
not historical P76 positive admission, full-product regression or security GO.
"""
from __future__ import annotations

import ast
from collections import OrderedDict
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

BASE = "0342125898215f194782809d1e9103d71b0c118a"
BRANCH = "byok-c1-p153-current-branch-security-governance-candidate-20261111"
PINNED_ORIGINAL_P76_BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
P140_PIN_DEFAULTS = {
    "_APPROVED_MAIN_SHA256": "",
    "_APPROVED_COMPANION_SHA256": "",
    "_APPROVED_SIGNER_CERT_SHA256": "",
    "_APPROVED_CODE_INTEGRITY_RELEASE": False,
}
TEST_CLASSES = OrderedDict((
    ("historical_P76_negative_only", (
        "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests",
        (
            "test_exact_phase10_3_seal_and_manifest",
            "test_source_verifier_is_pure_and_has_no_credential_effects",
            "test_wrong_branch_refused_before_other_work",
            "test_wrong_annotated_tag_ref_refused",
            "test_unknown_untracked_path_refused",
            "test_wrong_commit_parent_refused",
            "test_old_sealed_live_body_still_rejects_successor_branch",
        ),
    )),
    ("reduced_user_scope_credential_consent", (
        "tests.test_local_user_scope_byok.LocalOfflineControllerTests",
        (
            "test_constructor_and_factory_do_not_touch_native_credential_manager",
            "test_begin_save_never_mutates_or_validates",
            "test_duplicate_pending_review_and_cancel_are_one_use",
            "test_explicit_confirmation_required_before_write",
            "test_write_then_exception_is_unknown_and_never_auto_retried",
            "test_delete_requires_both_confirmations_and_never_reads_key",
            "test_slot_presence_change_before_effect_is_denied",
            "test_source_has_no_provider_network_or_automatic_key_read",
        ),
    )),
    ("manual_source_launch_boundary", (
        "tests.test_p133_connection_launch.LaunchBridgeTests",
        (
            "test_manual_launch_uses_fixed_module_never_shell_or_key_argument",
            "test_construction_is_not_a_process_or_credential_operation",
            "test_frozen_binary_requires_separately_reviewed_launcher",
            "test_local_child_environment_whitelists_no_provider_secrets",
        ),
    )),
    ("signed_frozen_companion_fail_closed", (
        "tests.test_p140_frozen_signed_companion.FrozenSignedCompanionGateTests",
        (
            "test_production_release_pins_are_deliberately_absent",
            "test_no_code_integrity_policy_owner_approval",
            "test_empty_main_pin_refused",
            "test_empty_companion_pin_refused",
            "test_source_mode_never_admits_frozen_companion",
            "test_frozen_launch_default_never_spawns_unapproved_companion",
        ),
    )),
))
# Exact baseline source under review (product, frozen P76, original tests).
ORIGINALS = (
    "tests/phase8_byok_c1_p76_scope.py",
    "tests/test_phase8_byok_c1_p76_scope.py",
    "nayeon/brain/local_byok_user_scope.py",
    "tests/test_local_user_scope_byok.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "tests/test_p133_connection_launch.py",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
    "tests/test_p140_frozen_signed_companion.py",
    "scripts/p139_native_fs_verified_local_temp_root.py",
)
EXCLUDED_HISTORICAL_BRANCH_POSITIVES = (
    "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests."
    "test_new_public_and_private_gate_agree",
    "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests."
    "test_five_public_routes_use_same_source_proof",
)
COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
SECRET_ENV = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True,
        stdin=subprocess.DEVNULL, check=False, timeout=25,
    )
    if result.returncode != 0:
        raise RuntimeError("P153 original Git provenance request failed")
    return result.stdout


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _top_level_constants(path: Path, names: set[str]) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    constants: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    if target.id in constants:
                        raise RuntimeError("Duplicate source release/branch constant")
                    constants[target.id] = ast.literal_eval(node.value)
    return constants


def _inventory_exact_tests(repo: Path) -> list[dict]:
    groups = []
    for label, (klass, names) in TEST_CLASSES.items():
        prefix, _, class_name = klass.rpartition(".")
        source = repo / (prefix.replace(".", "/") + ".py")
        tree = ast.parse(source.read_text(encoding="utf8"), filename=str(source))
        classes = [
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ]
        if len(classes) != 1:
            raise RuntimeError("Current scope original test class missing: " + klass)
        actual = {
            node.name for node in classes[0].body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        }
        if len(names) != len(set(names)) or not set(names).issubset(actual):
            raise RuntimeError("Original current-scope test method inventory drift")
        groups.append({
            "group": label, "original_class": klass,
            "selected_original_method_ids": [klass + "." + name for name in names],
            "number_selected": len(names),
            "all_original_methods_in_class": len(actual),
        })
    if sum(g["number_selected"] for g in groups) != 25:
        raise RuntimeError("P153 candidate original test count drift")
    return groups


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P153 disposable hosted Windows branch mismatch")
    root = Path(__file__).resolve().parents[1]
    if _git(root, "branch", "--show-current").decode("ascii").strip() != BRANCH:
        raise RuntimeError("P153 actual Git branch mismatch")
    current = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    if current != os.environ.get("GITHUB_SHA"):
        raise RuntimeError("P153 source SHA differs from triggering event")
    if _git(root, "merge-base", "HEAD", BASE).decode("ascii").strip() != BASE:
        raise RuntimeError("P153 missing exact P152 parent")
    if _git(root, "status", "--porcelain=v1").strip():
        raise RuntimeError("P153 unapproved worktree difference")

    custody = []
    for path in ORIGINALS:
        current_bytes = (root / path).read_bytes()
        if current_bytes != _git(root, "show", BASE + ":" + path):
            raise RuntimeError("Original security/product/test source mutated: " + path)
        custody.append({
            "path": path,
            "sha256": _digest(current_bytes),
            "bytes": len(current_bytes),
            "exact_P152_bytes_preserved": True,
        })

    gate = _top_level_constants(root / ORIGINALS[0], {"BRANCH"})
    if gate != {"BRANCH": PINNED_ORIGINAL_P76_BRANCH}:
        raise RuntimeError("The original P76 exact branch restriction changed")
    frozen = _top_level_constants(
        root / "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
        set(P140_PIN_DEFAULTS),
    )
    if frozen != P140_PIN_DEFAULTS:
        raise RuntimeError("P140 fail-closed source release policy changed")
    groups = _inventory_exact_tests(root)

    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p153-current-branch-review"
    evidence.mkdir(parents=True, exist_ok=True)
    safe_root = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    try:
        if safe_root.exists() or safe_root.is_symlink():
            raise RuntimeError("P153 test-root identity collision")
        os.mkdir(safe_root)
        created = True
        _verify_original_handle_policy(str(safe_root))
        env = os.environ.copy()
        for key in SECRET_ENV:
            env.pop(key, None)
        for key in ("TEMP", "TMP", "TMPDIR"):
            env[key] = str(safe_root)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        ids = [
            test for g in groups for test in g["selected_original_method_ids"]
        ]
        raw_log = evidence / "p153_25_original_current_scope_candidate_tests.log"
        started = time.monotonic()
        try:
            with raw_log.open("wb") as stream:
                proc = subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "-v", *ids],
                    cwd=root, env=env, stdin=subprocess.DEVNULL,
                    stdout=stream, stderr=subprocess.STDOUT,
                    check=False, timeout=115,
                )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
        except OSError:
            exit_code = 125
        elapsed = round(time.monotonic() - started, 3)
        data = raw_log.read_bytes() if raw_log.exists() else b""
        lines = data.decode("utf8", "replace").splitlines()
        counts = [int(m.group(1)) for line in lines
                  if (m := COUNT.search(line))]
        observed = counts[-1] if counts else None
        failed = [
            line.partition(":")[2].strip() for line in lines
            if line.startswith(("FAIL: ", "ERROR: "))
        ]
        failed_footers = [
            line for line in lines if line.startswith("FAILED (")
        ]
        passed = (
            exit_code == 0 and observed == len(ids)
            and any(line.strip() == "OK" for line in lines)
            and not failed and not failed_footers
        )
        verdict = ("PASS" if passed else "TIMEOUT" if exit_code == 124
                   else "HOLD")
        manifest = {
            "exact_P152_predecessor": BASE,
            "current_commit": current,
            "disposable_windows_only": True,
            "historical_P76_branch_pin_unchanged": PINNED_ORIGINAL_P76_BRANCH,
            "original_P76_branch_positive_test_ids_preserved_but_not_run": (
                EXCLUDED_HISTORICAL_BRANCH_POSITIVES
            ),
            "original_historical_P76_full_suite_last_actual_result": (
                "P152_NATIVE_EXIT_1__8_PASS_2_FAIL"
            ),
            "candidate_scope": (
                "NAMED_SOURCE_PRESERVING_NEGATIVE_CURRENT_USER_TESTS_ONLY"
            ),
            "historical_scope_tests_waived_or_reclassified": False,
            "source_custody": custody,
            "tested_original_method_groups": groups,
            "expected_original_candidate_tests": len(ids),
            "native_unittest_observed_count": observed,
            "native_exit": exit_code,
            "candidate_test_verdict_only": verdict,
            "duration_seconds": elapsed,
            "original_failed_test_ids": failed,
            "original_failed_footer": (
                failed_footers[-1] if failed_footers else None
            ),
            "raw_log_sha256": _digest(data),
            "raw_log_bytes": len(data),
            "verified_original_win32_native_handle_safe_temp_root": True,
            "signed_release_main_companion_and_cert_pins": "EMPTY",
            "code_integrity_owner_policy_approval": False,
            "qualified_independent_test_inventory_decision": "NOT_OBTAINED",
            "qualified_independent_user_scope_security_review": "NOT_OBTAINED",
            "full_product_windows_three_accepted_regressions": 0,
            "original_privileged_C1_G0_to_G6": "OPEN",
            "production_release": "HOLD",
            "real_credential_or_provider_effect": False,
        }
        (evidence / "p153_current_branch_candidate_governance.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf8",
        )
        print("P153_FROZEN_P76_EXACT_BRANCH_GUARD_SOURCE=UNCHANGED", flush=True)
        print("P153_ORIGINAL_SOURCE_CUSTODY_FILES=" + str(len(custody)),
              flush=True)
        print("P153_P139_ORIGINAL_NATIVE_HANDLE_ROOT=PASS", flush=True)
        print("P153_P140_SIGNED_FROZEN_RELEASE_POLICY=STILL_DENIED", flush=True)
        print("P153_CURRENT_BRANCH_CANDIDATE_TESTS=" + str(len(ids)),
              flush=True)
        print("P153_ORIGINAL_CANDIDATE_NATIVE_EXIT=" + str(exit_code),
              flush=True)
        print("P153_ORIGINAL_CANDIDATE_RAN=" + str(observed), flush=True)
        print("P153_ORIGINAL_CANDIDATE_VERDICT=" + verdict, flush=True)
        print("P153_ORIGINAL_CANDIDATE_SECONDS=" + str(elapsed), flush=True)
        print("P153_ORIGINAL_CANDIDATE_FAIL_IDS=" + str(len(failed)),
              flush=True)
        print("P153_ORIGINAL_CANDIDATE_RAW_LOG_SHA256=" + _digest(data),
              flush=True)
        print("P153_OLD_P76_FULL_SUITE=UNCHANGED_HOLD_NOT_WAIVED", flush=True)
        print("P153_INDEPENDENT_REVIEWER_AND_REGRESSION_SCOPE_GO=NOT_OBTAINED",
              flush=True)
        print("P153_THREE_ACCEPTED_FULL_PRODUCT_WINDOWS_REGRESSIONS=NOT_PASSED",
              flush=True)
        print("P153_BYOK_C1_USER_SCOPE_PRODUCTION_RELEASE=HOLD", flush=True)
        return 0 if data and exit_code in (0, 1, 124, 125) else 1
    finally:
        if created:
            try:
                st = safe_root.lstat()
                if (not safe_root.is_symlink()
                        and not (getattr(st, "st_file_attributes", 0) & 0x400)
                        and str(safe_root).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(safe_root)
                    print("P153_OWNED_EPHEMERAL_TEMP_CLEANUP=ATTEMPTED",
                          flush=True)
                else:
                    print("P153_UNTRUSTED_REPARSE_CLEANUP_REFUSED", flush=True)
            except Exception:
                print("P153_EPHEMERAL_TEMP_CLEANUP=UNCERTAIN", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
