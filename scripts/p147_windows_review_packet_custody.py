"""P147 independent-review packet custody audit, NOT independent review.

Verify original historic tests / current BYOK source are EXACTLY unchanged from P146,
record raw SHA256 and explicit historical failure inventory, and prove the
P140 frozen-launch release pins still deny execution. No production execution,
network credentials, key entry, old-test filtering or skipped security tests.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = "a215b4b23063092ed6087dd4581d50b2b53cde1a"
BRANCH = "byok-c1-p147-user-scope-regression-governance-packet-20261110"
AUDIT_PATHS = {
    ".github/workflows/p147-windows-governance-source-custody.yml",
    "docs/byok-c1-p147-user-scope-independent-security-review.md",
    "scripts/p147_windows_review_packet_custody.py",
}
PRODUCT = (
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
    "nayeon/secrets/windows_credential.py",
    "scripts/p139_native_fs_verified_local_temp_root.py",
)
HISTORICAL = (
    "tests/test_phase8_byok_b_scope_integrity.py",
    "tests/test_phase8_byok_c1_p76_scope.py",
    "tests/test_phase8_byok_c1_p77_historical_compat.py",
    "tests/test_phase8_byok_c1_p85_scope.py",
    "tests/test_phase_831_effect_isolation.py",
    "tests/test_phase_832_lifecycle_assurance.py",
    "tests/test_windows_credential_backend.py",
)
HISTORIC_MODULE_HOLDS = (
    "tests.test_phase8_byok_c1_p76_scope",
    "tests.test_phase8_byok_c1_p77_historical_compat",
    "tests.test_phase8_byok_c1_p85_scope",
    "tests.test_phase_831_effect_isolation",
    "tests.test_phase_832_lifecycle_assurance",
    "tests.test_presentation_configuration_document",
    "tests.test_presentation_configuration_bootstrap",
    "tests.test_presentation_configuration_persistence",
    "tests.test_presentation_configuration_service",
    "tests.test_presentation_identity_contracts",
    "tests.test_provider_connection_composition",
    "tests.test_provider_connection_startup",
    "tests.test_presentation_configuration_view",
    "tests.test_provider_connection_service",
    "tests.test_windows_credential_backend",
)
HISTORIC_MODULE_TIMEOUTS = (
    "tests.test_phase8_byok_scope_integrity",
    "tests.test_phase_830_scope_integrity",
    "tests.test_phase_831_scope_integrity",
    "tests.test_phase_832_scope_integrity",
    "tests.test_phase_833_scope_integrity",
    "tests.test_phase_834_scope_integrity",
    "tests.test_phase_836_scope_integrity",
    "tests.test_phase_837_scope_integrity",
    "tests.test_pre_829_a04_two_process_recovery",
)
PIN_DEFAULTS = {
    "_APPROVED_MAIN_SHA256": "",
    "_APPROVED_COMPANION_SHA256": "",
    "_APPROVED_SIGNER_CERT_SHA256": "",
    "_APPROVED_CODE_INTEGRITY_RELEASE": False,
}


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        timeout=25, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Git read-only source custody operation failed")
    return result.stdout


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("GITHUB_REF_NAME") == BRANCH
        and os.environ.get("RUNNER_TEMP")
    ):
        print("P147_HOSTED_DISPOSABLE_WINDOWS_ONLY=REFUSED", flush=True)
        return 4

    root = Path(__file__).resolve().parents[1]
    actual_head = _git(root, "rev-parse", "HEAD").decode().strip()
    expected_head = os.environ.get("GITHUB_SHA")
    if actual_head != expected_head:
        raise RuntimeError("Repository HEAD differs from exact CI commit")
    if _git(root, "merge-base", "HEAD", BASE).decode().strip() != BASE:
        raise RuntimeError("Missing exact P146 parent ancestry")
    if _git(root, "status", "--porcelain=v1").strip():
        raise RuntimeError("Source worktree has unreviewed changes")
    actual_diff = {
        value.strip().replace("\\", "/")
        for value in _git(root, "diff", "--name-only", BASE, "HEAD").decode().splitlines()
        if value.strip()
    }
    if actual_diff != AUDIT_PATHS:
        raise RuntimeError("Unapproved product, test, or audit path modification")
    _git(root, "diff", "--check", BASE, "HEAD")

    source_custody = []
    for path in PRODUCT + HISTORICAL:
        current = (root / path).read_bytes()
        p146 = _git(root, "show", BASE + ":" + path)
        if current != p146:
            raise RuntimeError("P146 immutable source/test custody mismatch: " + path)
        source_custody.append({
            "path": path, "sha256": _sha(current),
            "bytes": len(current), "unchanged_from_exact_P146": True,
        })

    signed_source = (root / "nayeon/desktop_alpha/frozen_signed_byok_companion.py")
    tree = ast.parse(signed_source.read_text(encoding="utf8"))
    assigned = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in PIN_DEFAULTS:
                    assigned[target.id] = ast.literal_eval(node.value)
    if assigned != PIN_DEFAULTS:
        raise RuntimeError("P140 immutable frozen-launch security HOLD changed")
    if len(HISTORIC_MODULE_HOLDS) != 15 or len(HISTORIC_MODULE_TIMEOUTS) != 9:
        raise RuntimeError("Historical original module audit counts drift")
    for name in HISTORIC_MODULE_HOLDS + HISTORIC_MODULE_TIMEOUTS:
        if not (root / (name.replace(".", "/") + ".py")).is_file():
            raise RuntimeError("Missing original historical module: " + name)

    output_dir = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p147-review-custody"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_head": actual_head,
        "frozen_base": BASE,
        "status": "AUDIT_PASS_ONLY__PRODUCTION_RELEASE_HOLD",
        "all_original_tests_and_product_source_unchanged": True,
        "source_custody": source_custody,
        "source_custody_paths": len(source_custody),
        "signed_release_pins": "EMPTY_AND_CODE_INTEGRITY_POLICY_FALSE",
        "P144_original_module_holds": list(HISTORIC_MODULE_HOLDS),
        "P142_original_module_timeouts": list(HISTORIC_MODULE_TIMEOUTS),
        "P135_full_product_regressions": "3_INCOMPLETE",
        "P146_original_static_closure_test": "NATIVE_EXIT_1__STILL_FAILS",
        "P146_unittest_root_observation":
            "FAILURE_RESULT_REF_OWNS_TK_ROOT_UNTIL_RESULT_RELEASE",
        "P141_three_scoped_windows_triad": "3_PASS__NOT_FULL_PRODUCT",
        "independent_reviewer": None,
        "security_review_decision": "NOT_OBTAINED",
        "regression_suite_governance_decision": "NOT_OBTAINED",
        "original_privileged_service_gates": "G0_G6_OPEN",
        "signed_main_and_companion_images": "NOT_AUTHORISED",
        "Smart_App_Control_policy_owner_GO": False,
        "real_credentials_or_production_WinCred_effect": False,
        "release_approved": False,
        "approved_external_branch_waivers": [],
        "genuine_full_product_regression_passes": 0,
    }
    manifest_path = output_dir / "p147_review_custody_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf8",
    )
    digest = _sha(manifest_path.read_bytes())
    print("P147_EXACT_P146_PARENT_AND_ONLY_THREE_AUDIT_FILES=PASS", flush=True)
    print("P147_FROZEN_SOURCE_AND_HISTORICAL_TEST_PATHS_VERIFIED=" +
          str(len(source_custody)), flush=True)
    print("P147_SIGNED_FROZEN_LAUNCH_PINS_EMPTY_POLICY_FALSE=PASS", flush=True)
    print("P147_ORIGINAL_MODULE_HOLDS=15", flush=True)
    print("P147_ORIGINAL_MODULE_TIMEOUTS=9", flush=True)
    print("P147_MANIFEST_SHA256=" + digest, flush=True)
    print("P147_INDEPENDENT_SECURITY_AND_REGRESSION_REVIEW=NOT_OBTAINED", flush=True)
    print("P147_FULL_PRODUCT_NATIVE_WINDOWS_TRIAD=NOT_PASSED", flush=True)
    print("P147_BYOK_C1_USER_SCOPE_RELEASE=HOLD", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
