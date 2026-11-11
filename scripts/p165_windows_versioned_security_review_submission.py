"""P165 authentic Windows versioned regression evidence and external-review submission.

This is a READ-ONLY governance collector, not an approval authority.
Run all TEN original historical P76 methods *unmodified* on a descendant
branch, preserving genuine old-branch failures, AND the 25 exact unchanged
current-user safety methods. Independently classify those different scopes,
record genuine native exit/footer/hash, and fail CLOSED for production.
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
from scripts.p153_windows_current_branch_security_candidate import (
    ORIGINALS, PINNED_ORIGINAL_P76_BRANCH, P140_PIN_DEFAULTS,
    TEST_CLASSES, _top_level_constants,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "4c669d68b832f885331f7e63e3d9e18af9d3a7ff"
BRANCH = "byok-c1-p165-versioned-regression-security-review-submission-20261111"
EXPECTED_MODULE_COUNT = 170
EXPECTED_P76_METHODS = 10
EXPECTED_CURRENT_SECURITY_METHODS = 25
RAN = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)
OK = re.compile(r"^OK\s*$", re.M)
FAILED = re.compile(r"^FAILED \(([^)]*)\)\s*$", re.M)
HEADING = re.compile(r"^(FAIL|ERROR): ([^\r\n]+)", re.M)
CREDENTIAL_ENV = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "NAYEON_INTERNAL_SECRET", "P165_SECRET",
)
HISTORICAL_TWO_BRANCH_POSITIVES = (
    "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_new_public_and_private_gate_agree",
    "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests.test_five_public_routes_use_same_source_proof",
)
PREVIOUS_EVIDENCE = (
    {"checkpoint": "P161", "actual_windows_run": 43087207943,
     "artifact_id": 13886812899,
     "archive_sha256": "19B490809F819932D32519B014A2F5ECDC84253F1960B8B1D6B644542C5D02C5",
     "authoritative_commit": "fe26dc1aeda0422c9aaadee63edae4f2b583fa81",
     "bounded_finding": "1 original Phase8.37 hot method PASS / 2470 Git calls / 93.892 seconds Git"},
    {"checkpoint": "P162", "actual_windows_run": 43089354076,
     "artifact_id": 13887973012,
     "archive_sha256": "93AD0988AB1ED94D5DABD68462CBA23AAD31A3F132AC369CF6C2AF2D19AD226F",
     "authoritative_commit": "9c2422eb920d8b478520fca7de4bf974bf7c92c6",
     "bounded_finding": "95 original vs batch immutable Git blob comparisons MATCH; 9 corrupted replies rejected"},
    {"checkpoint": "P163", "actual_windows_run": 43090896372,
     "artifact_id": 13888034604,
     "archive_sha256": "383E24B67A2BACFC9C0EEC713045897CE3314EEBB2E3386676DDB04E5B269D5B",
     "authoritative_commit": "51ecaa8eaf2e3f092d1006cf2ffba4f402c1de87",
     "bounded_finding": "25 original current-user negative methods PASS, 16 candidate corrupt replies REJECT"},
    {"checkpoint": "P164", "actual_windows_run": 43105642826,
     "artifact_id": 13894685552,
     "archive_sha256": "A4D16B1B789380CD015D3FA02D454AE969B1CF839673E54CA0C0CA590802AF5F",
     "authoritative_commit": BASE,
     "bounded_finding": "19 immutable Git source matches; 7 pre-IPC denials; 2 valid and 9 invalid real Windows pipe scenarios"},
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str, allow_failure=False) -> bytes:
    p = subprocess.run(
        ["git", "-C", str(ROOT), *args], check=not allow_failure,
        capture_output=True, timeout=25, stdin=subprocess.DEVNULL,
    )
    return p.stdout


def source_guard():
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P165 exact disposable Windows source branch required")
    head = git("rev-parse", "HEAD").decode().strip()
    current_branch = git("branch", "--show-current").decode().strip()
    if head != os.environ.get("GITHUB_SHA") or current_branch != BRANCH:
        raise RuntimeError("P165 actual source SHA or branch differs from hosted event")
    if git("merge-base", BASE, head).decode().strip() != BASE:
        raise RuntimeError("P165 exact verified P164 predecessor not present")
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P165 source checkout dirty")
    testmodules = [x for x in git("ls-files", "tests/test_*.py").decode().splitlines()
                   if x.startswith("tests/test_") and x.endswith(".py")]
    if len(testmodules) != EXPECTED_MODULE_COUNT:
        raise RuntimeError("P165 historical/current test module inventory drift")
    protected = sorted(set(tuple(ORIGINALS) + (
        "tests/phase_8_30_scope_migration.py",
        "tests/phase_8_32_scope_migration.py",
        "tests/phase_8_34_scope_migration.py",
        "tests/phase_8_36_scope_migration.py",
        "tests/phase_8_37_scope_migration.py",
        "tests/test_phase_837_scope_integrity.py",
        "scripts/p161_windows_historical_git_call_profile.py",
        "scripts/p162_windows_immutable_git_batch_candidate.py",
        "scripts/p163_windows_security_review_readiness.py",
        "scripts/p164_windows_bounded_immutable_reader_design.py",
    )))
    custody = []
    for path in protected:
        if git("rev-parse", "HEAD:" + path) != git("rev-parse", BASE + ":" + path):
            raise RuntimeError("P165 original test/security/signed source mutated: " + path)
        custody.append({
            "source_path": path,
            "actual_source_sha256": sha((ROOT/path).read_bytes()),
            "exact_P164_blob_identity_preserved": True,
        })
    gate = _top_level_constants(
        ROOT / "tests/phase8_byok_c1_p76_scope.py", {"BRANCH"}
    )
    if gate != {"BRANCH": PINNED_ORIGINAL_P76_BRANCH}:
        raise RuntimeError("P165 historical P76 original exact branch pin changed")
    signed = _top_level_constants(
        ROOT / "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
        set(P140_PIN_DEFAULTS),
    )
    if signed != P140_PIN_DEFAULTS:
        raise RuntimeError("P165 P140 real release signer/policy default no-go changed")
    # No new optimiser imported into source or original tests.
    for directory in ("nayeon", "tests"):
        found = subprocess.run(
            ["git", "-C", str(ROOT), "grep", "-l", "-F",
             "p165_windows_versioned_security_review_submission", BASE, "--", directory],
            capture_output=True, timeout=25,
            stdin=subprocess.DEVNULL, check=False,
        )
        if found.returncode not in (0, 1) or found.stdout:
            raise RuntimeError("P165 review collector integrated into product/original tests")
    print("P165_VERIFIED_P164_SOURCE_AND_170_TRACKED_TEST_MODULES=PASS", flush=True)
    print("P165_EXACT_HISTORIC_P76_AND_P140_DEFAULT_RELEASE_NO_GO=PASS", flush=True)
    print("P165_ORIGINAL_SOURCE_CUSTODY_BLOB_COUNT=" + str(len(custody)), flush=True)
    return head, custody


def original_test_inventory():
    path = ROOT / "tests/test_phase8_byok_c1_p76_scope.py"
    code = ast.parse(path.read_bytes(), filename=str(path))
    cls = [n for n in code.body if isinstance(n, ast.ClassDef) and
           n.name == "P76OfflineRoutingTests"]
    if len(cls) != 1:
        raise RuntimeError("P165 exact original historical P76 test class missing")
    names = [n.name for n in cls[0].body if isinstance(n, ast.FunctionDef)
             and n.name.startswith("test_")]
    if len(names) != EXPECTED_P76_METHODS or len(names) != len(set(names)):
        raise RuntimeError("P165 original P76 whole test-module inventory drift")
    exact_p76 = [
        "tests.test_phase8_byok_c1_p76_scope.P76OfflineRoutingTests." + name
        for name in names
    ]
    if not set(HISTORICAL_TWO_BRANCH_POSITIVES).issubset(set(exact_p76)):
        raise RuntimeError("P165 legacy P76 positive old-branch test inventory drift")

    original_current = []
    groups = []
    for label, (class_path, selected) in TEST_CLASSES.items():
        package, class_name = class_path.rsplit(".", 1)
        source = ROOT / (package.replace(".", "/") + ".py")
        syntax = ast.parse(source.read_bytes(), filename=str(source))
        classes = [n for n in syntax.body if isinstance(n, ast.ClassDef)
                   and n.name == class_name]
        if len(classes) != 1:
            raise RuntimeError("P165 original reduced security class drift")
        available = {n.name for n in classes[0].body
                     if isinstance(n, ast.FunctionDef) and
                     n.name.startswith("test_")}
        if len(set(selected)) != len(selected) or not set(selected).issubset(available):
            raise RuntimeError("P165 current-user original security method drift")
        tests = [class_path + "." + name for name in selected]
        groups.append({"source": label, "exact_original_test_ids": tests})
        original_current.extend(tests)
    if len(original_current) != EXPECTED_CURRENT_SECURITY_METHODS or len(set(original_current)) != len(original_current):
        raise RuntimeError("P165 25 original reduced current-user method count drift")
    print("P165_EXACT_ORIGINAL_TEST_INVENTORY=P76_10_CURRENT_SECURITY_25", flush=True)
    return exact_p76, original_current, groups


def run_unmodified_tests(label, ids, temp, out, cap=90):
    path = out / ("p165_native_" + label + "_original_unittest.log")
    env = os.environ.copy()
    for var in CREDENTIAL_ENV:
        env.pop(var, None)
    env.update({
        "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    started = time.monotonic()
    timedout = False
    with path.open("wb") as output:
        child = subprocess.Popen(
            [sys.executable, "-B", "-m", "unittest", "-v", *ids],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        try:
            native = child.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            timedout = True
            native = 124
            subprocess.run(
                ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=15, check=False,
            )
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    seconds = round(time.monotonic() - started, 3)
    raw = path.read_bytes()
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    matches = RAN.findall(text)
    count = int(matches[-1]) if matches else None
    issue_names = [{"outcome": kind, "original_test": case}
                   for kind, case in HEADING.findall(text)]
    footer_success = bool(OK.search(text))
    footer_failure = FAILED.findall(text)
    complete = count == len(ids) and (footer_success or bool(footer_failure))
    verdict = ("PASS" if native == 0 and complete and footer_success and not issue_names
               else "TIMEOUT" if native == 124 and timedout
               else "HOLD")
    entry = {
        "scope": label,
        "original_method_count_expected": len(ids),
        "native_unittest_count_observed": count,
        "genuine_full_unittest_footer": bool(complete),
        "native_windows_exit_code": native,
        "elapsed_seconds": seconds,
        "verdict_unmodified": verdict,
        "original_fail_error_identifiers": issue_names,
        "original_failed_footer": footer_failure[-1] if footer_failure else None,
        "unmodified_original_test_log": path.name,
        "original_stdout_stderr_sha256": sha(raw),
        "original_stdout_stderr_bytes": len(raw),
    }
    print("P165_NATIVE_ORIGINAL_SCOPE=" + label + "|EXIT=" + str(native)
          + "|RAN=" + str(count) + "|VERDICT=" + verdict
          + "|SECONDS=" + str(seconds), flush=True)
    for item in issue_names:
        print("P165_ORIGINAL_FAIL_ERROR=" + label + "|" +
              item["outcome"] + "|" + item["original_test"], flush=True)
    print("P165_NATIVE_LOG_SHA256=" + label + "|" + sha(raw), flush=True)
    return entry


RELEASE_REQUIREMENTS = (
    "three_complete_source_bound_full_product_windows_regressions",
    "qualified_external_independent_security_signed_go",
    "reviewed_current_branch_versioned_security_contract",
    "old_original_historical_P76_P85_failures_remain_unchanged_and_accounted_for",
    "original_historical_negative_adversaries_verified_without_test_waivers",
    "production_main_helper_installer_exact_signed_binary_pins",
    "smart_app_control_WDAC_policy_owner_signed_go",
    "privileged_C1_G0_to_G6_independently_accepted",
    "real_key_use_explicit_local_human_consent_after_release",
    "no_unresolved_original_product_security_HOLDS",
)


def evaluate_review_matrix(flags):
    if set(flags) != set(RELEASE_REQUIREMENTS) or any(type(v) is not bool for v in flags.values()):
        raise RuntimeError("P165 review decision matrix incomplete or invalid")
    pending = [name for name in RELEASE_REQUIREMENTS if not flags[name]]
    # Review matrix is a diagnostic. It is not a production authorization
    # action even when a hypothetical input indicates no outstanding items.
    return {"outstanding_review_items": pending,
            "evidence_satisfies_all_conditions": not pending,
            "is_production_launch_authorization": False}


def main():
    head, custody = source_guard()
    p76_ids, reduced_ids, groups = original_test_inventory()
    evidence_root = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p165-original-versioned-security-review-submission"
    evidence_root.mkdir(parents=True, exist_ok=True)
    temp = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P165 owned Windows TEMP collision")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        print("P165_ORIGINAL_P139_WIN32_OPEN_HANDLE_NO_REPARSE_POLICY=PASS", flush=True)

        historical = run_unmodified_tests("historical_P76_full_10",
                                          p76_ids, temp, evidence_root)
        reduced = run_unmodified_tests("current_user_25_selected",
                                       reduced_ids, temp, evidence_root)
    finally:
        if made:
            stat = temp.lstat()
            if temp.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P165 unsafe disposable TEMP removal refused")
            shutil.rmtree(temp)
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P165 original source mutated during genuine test run")

    flags = {name: False for name in RELEASE_REQUIREMENTS}
    # Original historical negatives are preserved unchanged and verified via
    # source-bound hashes and the genuine P76 full suite, but not all P85
    # historical tests were rerun here; this complete governance item stays false.
    matrix = evaluate_review_matrix(flags)
    if matrix["evidence_satisfies_all_conditions"]:
        raise RuntimeError("P165 unexpectedly admitted forbidden production release")
    # Changing any single condition to satisfied may NEVER release the hold.
    counterfactuals = []
    for name in RELEASE_REQUIREMENTS:
        altered = dict(flags)
        altered[name] = True
        state = evaluate_review_matrix(altered)
        if state["evidence_satisfies_all_conditions"] or state["is_production_launch_authorization"]:
            raise RuntimeError("P165 single positive flag incorrectly cleared all security holds")
        counterfactuals.append(name)
    if len(counterfactuals) != len(RELEASE_REQUIREMENTS):
        raise RuntimeError("P165 review matrix false-release tests incomplete")
    print("P165_VERSIONED_REVIEW_MATRIX_SINGLE_FLAG_FALSE_GO_REJECTIONS=" +
          str(len(counterfactuals)), flush=True)

    report = {
        "checkpoint": "P165",
        "exact_head": head,
        "verified_exact_parent_p164": BASE,
        "historical_original_P76_frozen_branch": PINNED_ORIGINAL_P76_BRANCH,
        "P76_original_full_suite": historical,
        "original_P76_two_positive_branch_specific_method_ids":
            list(HISTORICAL_TWO_BRANCH_POSITIVES),
        "original_25_current_user_unchanged_methods": reduced,
        "original_current_user_method_groups": groups,
        "historical_P76_POSITIVE_method_outcomes_did_not_get_waived": True,
        "reviewer_provenance_original_unchanged_source_sha256": custody,
        "previous_P161_to_P164_actual_windows_evidence": PREVIOUS_EVIDENCE,
        "versioned_review_contract_historical_scope":
            "historical P76 P80-only original full suite remains actual native HOLD if successor branch; do not recast as passing",
        "versioned_review_contract_current_branch":
            "25 named original current-user safety methods are a separate explicitly reduced subset; not a replacement for P76 positives or full-product suite",
        "versioned_review_contract_future_acceptance":
            "requires independently approved fresh-current-branch positive and negative contract preserving original historical branch refusal; no old tests edited",
        "production_review_requirements": flags,
        "review_matrix_present_unmet_requirements":
            matrix["outstanding_review_items"],
        "review_matrix_one_flag_false_go_refusals": counterfactuals,
        "named_qualified_external_reviewer_identity": "NOT OBTAINED",
        "independent_reviewer_dated_signed_go": "NOT OBTAINED",
        "review_submitted_to_an_external_person": False,
        "original_security_test_product_or_optimiser_integrated": False,
        "accepted_unfiltered_complete_windows_product_regressions": "0/3",
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "frozen_signed_main_helper_installer_cert_pins": "NOT OBTAINED",
        "code_integrity_release_owner_go": False,
        "production_release": "HOLD",
    }
    output = evidence_root / "p165_actual_windows_versioned_security_review_ledger.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("P165_ACTUAL_FULL_HISTORICAL_P76=" + historical["verdict_unmodified"], flush=True)
    print("P165_ACTUAL_REDUCED_CURRENT_USER_ORIGINAL_25=" + reduced["verdict_unmodified"], flush=True)
    print("P165_EXTERNAL_REVIEWER_SUBMISSION=PREPARED_NOT_SENT", flush=True)
    print("P165_QUALIFIED_INDEPENDENT_GO=NOT_OBTAINED", flush=True)
    print("P165_FULL_PRODUCT_WINDOWS_TRIAD=0/3", flush=True)
    print("P165_PRODUCTION_RELEASE=HOLD", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
