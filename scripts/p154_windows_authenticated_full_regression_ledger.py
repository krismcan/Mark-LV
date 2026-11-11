"""P154: read-only, SHA256-pinned historical Windows regression ledger.

Downloads seven exact historical *GitHub Actions* artifacts using the ephemeral
current repository actions:read token, verifies every archive SHA256 and
original per-module full-log SHA256, reconciles 169 modules and 83 P142
post-stall modules against P143/P144/P148/P149/P150 actual evidence.

This is an original-source reviewer inventory, NEVER independent review,
a new whole-product test execution, a historical failure waiver or release GO.
No provider secrets, production WinCred, signing or protected host operations.
"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import urllib.error
import urllib.parse
import zipfile

BASE = "08eb591a6a414f0a9eddbf309327475c99a18752"
BRANCH = "byok-c1-p154-authenticated-full-product-regression-ledger-20261111"
API = "https://api.github.com/repos/krismcan/Mark-LV/actions/artifacts/"
ARCHIVES = {
    "p135": (13721186316, "AA179E18E3AA39FC3254A6C44D8654FFE93685DD792D84BA1E79049A96F86856"),
    "p142": (13787854664, "1525E5779F015101DF3FEE3A71739D383DAD75DF6579CA47F7CFDAEEDCB2B9C1"),
    "p143": (13788724995, "74AD38F57E4A29346BA2DFD1F191781CA25CA6BFC186AE71DFB38BCBFE0651EE"),
    "p144": (13804256598, "4D62B64CB9872601AF271B8D47DE1CE7B76468E9013F0A9A8417CF9DC79C41E3"),
    "p148": (13807736953, "A7BE0131798C5E734CD0D7BBBAB6AF3DF6B4522271390FD9C90B9D07506A238B"),
    "p149": (13808993133, "917D8964CA36EB1E3161495BFC72A17A88E6CBC66E3492433DB419D38DEF68CC"),
    "p150": (13810925078, "BD308A9CA778569F7FF63AF6B695B9DB5D1C59B311DE51D562352D534144801C"),
}
EXPECTED_P135_RAW_TEST_LINES = {"ok": 1637, "FAIL": 37, "ERROR": 7}
P135_LOG = "31F844EE8C29B9886885303DF983FFA7C0452C2A671866400A9768535C6DD113"
P135_RUN = 42717686606
P142_MODULES = 83
TOTAL_MODULES = 169
P142_STALL_MODULE = "tests/test_phase8_byok_b_scope_integrity.py"
P143_RECOVERED = {
    "p143_native_text.log": ("tests.test_text_file_creation", 87),
    "p143_phase829_integrated.log": ("tests.test_phase_829_integrated_acceptance", 53),
    "p143_pre829_cleanup.log": ("tests.test_pre_829_host_pending_exception_cleanup", 17),
    "p143_pre829_fake.log": ("tests.test_pre_829_a02_fake_isolation", 12),
    "p143_pre829_review.log": ("tests.test_pre_829_a01_review_identity", 18),
}
P76_HISTORICAL_BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
P140_FROZEN_PINS = {
    "_APPROVED_MAIN_SHA256": "",
    "_APPROVED_COMPANION_SHA256": "",
    "_APPROVED_SIGNER_CERT_SHA256": "",
    "_APPROVED_CODE_INTEGRITY_RELEASE": False,
}
SUITE = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
P135_NATIVE_LINE = re.compile(r"^test_[^\r\n]+ \.\.\. (ok|FAIL|ERROR)$")
MAX_ARCHIVE_BYTES = 2_000_000


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _git(root: Path, *args: str) -> bytes:
    call = subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=25, check=False,
    )
    if call.returncode:
        raise RuntimeError("P154 local read-only Git ancestry or inventory failed")
    return call.stdout


def _source_literals(path: Path, allowed: set[str]) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for lhs in node.targets:
            if isinstance(lhs, ast.Name) and lhs.id in allowed:
                if lhs.id in values:
                    raise RuntimeError("P154 duplicate source security-policy literal")
                values[lhs.id] = ast.literal_eval(node.value)
    return values


def _download_artifact(id: int, expected_sha: str, token: str) -> bytes:
    req = urllib.request.Request(
        API + str(id) + "/zip",
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "Nayeon-P154-ReadOnly-Historical-Audit",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    # GitHub Actions uses an HTTPS 302 to an artifact blob host. Never
    # allow urllib's default redirect to forward the bearer token.
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, url):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=40) as stream:
            if stream.status != 200:
                raise RuntimeError("Unexpected GitHub artifact API response")
            data = stream.read(MAX_ARCHIVE_BYTES + 1)
    except urllib.error.HTTPError as response:
        if response.code not in (302, 303, 307):
            raise RuntimeError("GitHub Actions artifact retrieval not authorized") from None
        location = response.headers.get("Location", "")
        target = urllib.parse.urlparse(location)
        host = (target.hostname or "").lower()
        if (
            target.scheme != "https"
            or not host
            or not (
                host.endswith(".blob.core.windows.net")
                or host.endswith(".actions.githubusercontent.com")
                or host.endswith(".githubusercontent.com")
            )
        ):
            raise RuntimeError("Untrusted GitHub artifact redirect destination")
        # Artifact storage request has NO Authorization header.
        safe = urllib.request.Request(
            location, headers={"User-Agent": "Nayeon-P154-Artifact-SHA256-Audit"}
        )
        with opener.open(safe, timeout=40) as stream:
            if stream.status != 200:
                raise RuntimeError("Untrusted artifact storage response")
            data = stream.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES or _sha(data) != expected_sha:
        raise RuntimeError("Historical GitHub Actions archived evidence SHA256 mismatch")
    return data


def _open_archive(data: bytes) -> zipfile.ZipFile:
    z = zipfile.ZipFile(io.BytesIO(data), "r")
    if z.testzip() is not None:
        raise RuntimeError("Historical GitHub Actions archive member CRC failure")
    names = z.namelist()
    if len(names) != len(set(names)) or any(
        name.startswith("/") or ".." in Path(name).parts for name in names
    ):
        raise RuntimeError("Ambiguous or unsafe historical archive member names")
    return z


def _json_from_archive(z: zipfile.ZipFile, name: str) -> dict:
    return json.loads(z.read(name))


def _full_unittest_footer(text: str, expected: int, success: bool) -> bool:
    counts = SUITE.findall(text)
    if not counts or int(counts[-1]) != expected:
        return False
    ending = text.splitlines()
    return (
        any(line.strip() == "OK" for line in ending)
        if success else
        any(line.startswith("FAILED (") for line in ending)
    )


def _classify_raw_failures(raw: str) -> list[str]:
    markers = {
        "EXACT_P76_BRANCH_DENIAL": "wrong exact P76 prototype branch",
        "EXACT_P85_BRANCH_DENIAL": "wrong exact P85 review branch",
        "STATIC_FIRST_THREAD_GATE_MISMATCH": "'self._require_creator_thread()'",
        "STATIC_IMPORT_CLOSURE_MISMATCH": "unexpectedly found in",
        "RETIRED_FAKE_TK_ROOT": "retired fake Tk roots still live",
        "LEGACY_CAUSAL_REFUSAL_MISMATCH": "does not match \"P76 offline source refused",
    }
    return [name for name, fragment in markers.items() if fragment in raw]


def main() -> int:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("GITHUB_REF_NAME") == BRANCH
        and os.environ.get("RUNNER_TEMP")
    ):
        raise RuntimeError("P154 authentic disposable GitHub Windows runner required")
    token = os.environ.get("P154_READ_ONLY_GITHUB_ARTIFACT_TOKEN", "")
    if len(token) < 8:
        raise RuntimeError("P154 ephemeral repository actions:read evidence token missing")
    root = Path(__file__).resolve().parents[1]
    head = _git(root, "rev-parse", "HEAD").decode().strip()
    if head != os.environ.get("GITHUB_SHA"):
        raise RuntimeError("P154 source HEAD differs from GitHub CI event")
    if _git(root, "merge-base", "HEAD", BASE).decode().strip() != BASE:
        raise RuntimeError("P154 exact P153 ancestry missing")
    if _git(root, "status", "--porcelain=v1").strip():
        raise RuntimeError("P154 source checkout dirty")

    # Recompute all current original tracked module paths from Git, not
    # P142/P144 hand-authored counts; original tests remain byte-identical.
    source_paths = [
        x for x in _git(root, "ls-files", "--", "tests/test_*.py")
        .decode().splitlines() if x
    ]
    source_paths = sorted(p.replace("\\", "/") for p in source_paths)
    if len(source_paths) != TOTAL_MODULES or len(set(source_paths)) != TOTAL_MODULES:
        raise RuntimeError("P154 exact original 169-module test inventory drift")
    if source_paths[85] != P142_STALL_MODULE:
        raise RuntimeError("P154 original P135 stalled module index changed")
    suffix = [path.replace("/", ".")[:-3] for path in source_paths[86:]]
    if len(suffix) != P142_MODULES:
        raise RuntimeError("P154 exact P142 83-module suffix drift")
    if _source_literals(
        root / "tests/phase8_byok_c1_p76_scope.py", {"BRANCH"}
    ) != {"BRANCH": P76_HISTORICAL_BRANCH}:
        raise RuntimeError("P154 historical exact P76 branch guard changed")
    if _source_literals(
        root / "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
        set(P140_FROZEN_PINS),
    ) != P140_FROZEN_PINS:
        raise RuntimeError("P154 unapproved signed binary or Code Integrity policy drift")

    archives = {}
    zips = {}
    for label, (artifact_id, expected_sha) in ARCHIVES.items():
        raw = _download_artifact(artifact_id, expected_sha, token)
        archives[label] = {
            "run_artifact_id": artifact_id, "archive_sha256": _sha(raw),
            "archive_bytes": len(raw), "authenticated_with": "ephemeral_actions_read",
        }
        zips[label] = _open_archive(raw)
        print("P154_VERIFIED_PRIOR_WINDOWS_ARCHIVE=" + label +
              "|ID=" + str(artifact_id) + "|SHA256=" + _sha(raw), flush=True)

    p135 = zips["p135"]
    raw_passes = []
    for i in range(1, 4):
        name = f"p135_full_python_discovery_pass_{i}.log"
        raw = p135.read(name)
        if _sha(raw) != P135_LOG:
            raise RuntimeError("Original P135 raw Windows discovery log SHA mismatch")
        lines = raw.decode("utf8", "replace").splitlines()
        categories = Counter(
            match.group(1) for line in lines
            if (match := P135_NATIVE_LINE.fullmatch(line))
        )
        if dict(categories) != EXPECTED_P135_RAW_TEST_LINES:
            raise RuntimeError("Authentic P135 native per-test outcome inventory drift")
        if any(SUITE.search(line) for line in lines):
            raise RuntimeError("P135 has a complete footer contrary to prior evidence")
        if "test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused" not in lines[-1]:
            raise RuntimeError("P135 historical exactly stalled original case changed")
        raw_passes.append({
            "pass_number": i,
            "prior_github_actions_native_exit": 124,
            "complete_unittest_footer": False,
            "completed_test_outcomes": sum(categories.values()),
            "completed_native_status_counts": dict(categories),
            "raw_log_sha256": _sha(raw),
            "previous_github_run_id": P135_RUN,
            "prior_native_exit_source": "GitHub Actions job 129503338552",
        })

    p142 = _json_from_archive(
        zips["p142"], "p142_inventory_diagnostic_manifest.json"
    )
    if (
        p142["source_modules"] != TOTAL_MODULES
        or p142["unreached_modules"] != P142_MODULES
        or p142["completed_modules"] != P142_MODULES
        or (p142["pass_modules"], p142["hold_modules"], p142["timeout_modules"])
        != (54, 20, 9)
    ):
        raise RuntimeError("P142 actual original diagnostic summary drift")
    p142_rows = {r["module"]: r for r in p142["results"]}
    if len(p142_rows) != P142_MODULES or set(p142_rows) != set(suffix):
        raise RuntimeError("P142 exact raw 83-module suffix differs from current original Git source")
    for module, record in p142_rows.items():
        zname = "p142_" + module.replace(".", "_") + ".log"
        raw = zips["p142"].read(zname)
        if _sha(raw) != record["log_sha256"] or len(raw) != record["log_bytes"]:
            raise RuntimeError("P142 original raw module log does not match signed SHA receipt")
        if record["status"] == "PASS":
            if record["exit"] != 0 or not _full_unittest_footer(
                raw.decode("utf8", "replace"), record["count"], True
            ):
                raise RuntimeError("P142 actual original PASS status is not substantiated")
        elif record["status"] == "TIMEOUT":
            if record["exit"] != 124:
                raise RuntimeError("P142 original TIMEOUT not native timeout")
        elif record["status"] != "HOLD":
            raise RuntimeError("P142 unknown original outcome category")

    p143_updates = {}
    native_p143_cases = 0
    for filename, (module, count) in P143_RECOVERED.items():
        data = zips["p143"].read(filename)
        if p142_rows[module]["status"] != "HOLD":
            raise RuntimeError("P143 reclassified a module not original P142 HOLD")
        if not _full_unittest_footer(data.decode("utf8", "replace"), count, True):
            raise RuntimeError("P143 original safe TEMP module lacks genuine complete PASS")
        p143_updates[module] = {
            "latest_original_module_status": "PASS",
            "source_evidence_checkpoint": "P143",
            "observed_count": count, "original_log_sha256": _sha(data),
            "evidence_artifact_id": ARCHIVES["p143"][0],
            "change_from_P142": "HOLD_TO_PASS_ON_VERIFIED_NATIVE_HANDLE_TEMP",
        }
        native_p143_cases += count
    if len(p143_updates) != 5 or native_p143_cases != 187:
        raise RuntimeError("P143 original five-module 187-case evidence drift")

    p144 = _json_from_archive(
        zips["p144"], "p144_original_residual_manifest.json"
    )
    if len(p144["results"]) != 15 or p144["summary"] != {
        "PASS": 0, "HOLD": 15, "TIMEOUT": 0
    }:
        raise RuntimeError("P144 actual original 15-module Windows residuals drift")
    p144_updates = {}
    p144_flags = Counter()
    p144_total_original_fail_records = 0
    for record in p144["results"]:
        module = record["module"]
        raw = zips["p144"].read("p144_" + module.replace(".", "_") + ".log")
        text = raw.decode("utf8", "replace")
        if (
            module not in p142_rows or p142_rows[module]["status"] != "HOLD"
            or module in p143_updates or record["status"] != "HOLD"
            or record["native_exit"] != 1
            or _sha(raw) != record["log_sha256"]
            or len(raw) != record["log_bytes"]
            or not _full_unittest_footer(
                text, record["completed_unittest_count"], False
            )
        ):
            raise RuntimeError("P144 original failing Windows module log is not authenticated")
        # Original headings, not P142's known CRLF-malformed diagnostic
        # regex, establish 30 actual FAIL/ERROR records across 15 modules.
        raw_names = [
            x for x in text.splitlines()
            if x.startswith(("FAIL: ", "ERROR: "))
        ]
        if len(raw_names) != len(record["failure_ids"]):
            raise RuntimeError("P144 original failure heading/count mismatch")
        flags = _classify_raw_failures(text)
        p144_flags.update(flags)
        p144_total_original_fail_records += len(raw_names)
        p144_updates[module] = {
            "latest_original_module_status": "HOLD",
            "source_evidence_checkpoint": "P144",
            "observed_count": record["completed_unittest_count"],
            "original_failure_or_error_ids": record["failure_ids"],
            "original_failed_footer": record["failed_footer"],
            "failure_signature_flags_nonexclusive": flags,
            "original_log_sha256": _sha(raw),
            "evidence_artifact_id": ARCHIVES["p144"][0],
        }
    if len(p144_updates) != 15 or set(p143_updates) & set(p144_updates):
        raise RuntimeError("P143/P144 original residual split not disjoint")

    recent = {}
    for label, jsonname, logname in (
        ("p148", "p148_original_A04_windows_manifest.json",
         "p148_original_A04_full_module.log"),
        ("p149", "p149_phase836_original_module_manifest.json",
         "p149_original_phase836_full_module.log"),
        ("p150", "p150_original_byok_scope_native_manifest.json",
         "p150_original_BYOK_scope_entire_module.log"),
    ):
        manifest = _json_from_archive(zips[label], jsonname)
        raw = zips[label].read(logname)
        sha_field = "log_sha256" if label == "p150" else "raw_log_sha256"
        if _sha(raw) != manifest[sha_field]:
            raise RuntimeError(label + " original native log SHA receipt mismatch")
        recent[label] = (manifest, raw.decode("utf8", "replace"))
    m148, r148 = recent["p148"]
    m149, r149 = recent["p149"]
    m150, r150 = recent["p150"]
    if not (
        m148["native_exit"] == 0
        and m148["native_result"] == "PASS"
        and m148["test_count_with_complete_footer"] == 22
        and _full_unittest_footer(r148, 22, True)
        and p142_rows[m148["original_test_module"]]["status"] == "TIMEOUT"
    ):
        raise RuntimeError("P148 complete A04 22-case native recovery not substantiated")
    if not (
        m149["native_exit_code"] == 1
        and m149["status"] == "HOLD"
        and m149["observed_unittest_count"] == 11
        and _full_unittest_footer(r149, 11, False)
        and p142_rows[m149["original_module"]]["status"] == "TIMEOUT"
    ):
        raise RuntimeError("P149 original Phase8.36 real module FAIL not substantiated")
    if not (
        m150["native_exit_code"] == 124
        and m150["original_module_verdict"] == "TIMEOUT"
        and m150["observed_final_unittest_count"] is None
        and not SUITE.search(r150)
        and p142_rows[m150["original_module"]]["status"] == "TIMEOUT"
    ):
        raise RuntimeError("P150 original BYOK module prolonged native timeout not substantiated")

    updates = {
        **p143_updates, **p144_updates,
        m148["original_test_module"]: {
            "latest_original_module_status": "PASS",
            "source_evidence_checkpoint": "P148",
            "observed_count": 22,
            "original_log_sha256": _sha(zips["p148"].read(
                "p148_original_A04_full_module.log")),
            "evidence_artifact_id": ARCHIVES["p148"][0],
            "change_from_P142": "TIMEOUT_TO_PASS_AFTER_68_SECONDS",
        },
        m149["original_module"]: {
            "latest_original_module_status": "HOLD",
            "source_evidence_checkpoint": "P149",
            "observed_count": 11,
            "original_failed_footer": m149["unittest_failed_footer"],
            "original_failure_or_error_ids": m149["unittest_failed_ids"],
            "original_log_sha256": m149["raw_log_sha256"],
            "evidence_artifact_id": ARCHIVES["p149"][0],
            "change_from_P142": "TIMEOUT_TO_COMPLETE_WITH_TWO_FAILURES",
        },
        m150["original_module"]: {
            "latest_original_module_status": "TIMEOUT",
            "source_evidence_checkpoint": "P150",
            "observed_count": None,
            "original_log_sha256": m150["log_sha256"],
            "evidence_artifact_id": ARCHIVES["p150"][0],
            "change_from_P142": "35_SECOND_TIMEOUT_TO_190_SECOND_TIMEOUT",
        },
    }
    if len(updates) != 23:
        raise RuntimeError("P154 unexpected number of distinct original module recovery rows")
    if p144_total_original_fail_records != 30:
        raise RuntimeError("P144 actual historical 30 FAIL/ERROR heading count drift")

    current_suffix = []
    for module in suffix:
        p142_record = p142_rows[module]
        info = {
            "module": module,
            "p142_original_status": p142_record["status"],
            "p142_original_native_exit": p142_record["exit"],
            "p142_original_log_sha256": p142_record["log_sha256"],
            "p142_original_artifact_id": ARCHIVES["p142"][0],
        }
        if module in updates:
            info.update(updates[module])
        else:
            info.update({
                "latest_original_module_status": p142_record["status"],
                "source_evidence_checkpoint": "P142",
                "evidence_artifact_id": ARCHIVES["p142"][0],
            })
        current_suffix.append(info)
    latest_counts = Counter(
        r["latest_original_module_status"] for r in current_suffix
    )
    if dict(latest_counts) != {"PASS": 60, "HOLD": 16, "TIMEOUT": 7}:
        raise RuntimeError("P154 genuine original 83 suffix module reconciliation failed")
    outstanding = [
        r["module"] for r in current_suffix
        if r["latest_original_module_status"] != "PASS"
    ]
    if len(outstanding) != 23:
        raise RuntimeError("P154 original still-blocked suffix count drift")
    prefix = source_paths[:86]
    complete_inventory = [
        {
            "source_path": path,
            "source_sha256": _sha((root / path).read_bytes()),
            "module": path.replace("/", ".")[:-3],
            "evidence_scope": (
                "P135_UNFINISHED_FULL_DISCOVERY_PREFIX__NO_COMPLETED_PASS"
                if i < 86 else "P142_83_MODULE_SUFFIX_WITH_LATER_NATIVE_DIAGNOSTICS"
            ),
            "last_known_original_module_evidence": (
                next(r for r in current_suffix
                     if r["module"] == path.replace("/", ".")[:-3])
                if i >= 86 else None
            ),
        }
        for i, path in enumerate(source_paths)
    ]
    if len(complete_inventory) != TOTAL_MODULES or len(prefix) != 86:
        raise RuntimeError("P154 original full-product module ledger incomplete")
    output = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p154-evidence-reconciliation"
    output.mkdir(parents=True, exist_ok=True)
    receipt = {
        "checkpoint": "P154",
        "exact_P153_source_parent": BASE,
        "audited_git_head": head,
        "audit_platform": "GENUINE_EPHEMERAL_WINDOWS_2025_PYTHON_312",
        "source_original_tests_modified": False,
        "original_historical_p76_exact_branch": P76_HISTORICAL_BRANCH,
        "frozen_P140_signed_main_helper_signer_pins": "EMPTY",
        "frozen_P140_code_integrity_owner_approval": False,
        "artifacts_authenticated_by_sha256": archives,
        "p135_original_three_native_full_discovery_attempts": raw_passes,
        "p135_original_attempts_with_completed_full_suite": 0,
        "p142_original_83_suffix_counts": {"PASS": 54, "HOLD": 20, "TIMEOUT": 9},
        "p143_original_recovered_holds": 5,
        "p143_original_native_cases_genuinely_passed": native_p143_cases,
        "p144_original_15_retested_holds": 15,
        "p144_original_failure_and_error_record_count": p144_total_original_fail_records,
        "p144_raw_failure_log_signatures_nonexclusive": dict(p144_flags),
        "p148_original_A04_22_case_module_genuine_pass": True,
        "p149_original_836_genuine_failed_module": True,
        "p150_original_BYOK_genuine_190_second_timeout": True,
        "post_recovery_original_83_suffix_counts": dict(latest_counts),
        "post_recovery_original_83_suffix_outstanding": outstanding,
        "original_169_module_source_inventory": complete_inventory,
        "original_169_module_source_inventory_total": TOTAL_MODULES,
        "pre_stall_prefix_modules_not_cleared_by_complete_regression": 86,
        "remaining_83_suffix_modules_not_cleared": 23,
        "tests_called_in_P154": 0,
        "historical_test_failure_or_seal_waivers_authorized": 0,
        "independent_qualified_security_reviewer": None,
        "independent_legacy_regression_governance_decision": "NOT_OBTAINED",
        "three_complete_full_product_native_windows_regressions": 0,
        "signed_main_helper_installer_pinned_publisher": "NOT_OBTAINED",
        "Smart_App_Control_WDAC_policy_owner_GO": False,
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "user_scoped_C1_production_release": "HOLD",
        "user_credentials_or_production_Kristian_WinCred_effects": False,
        "original_Drive_master_and_dashboard_updated": False,
    }
    manifest = output / "p154_authenticated_original_169_module_regression_ledger.json"
    manifest.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf8"
    )
    print("P154_GENUINE_PRIOR_WINDOWS_ARTIFACT_ARCHIVES_SHA256_VERIFIED=7", flush=True)
    print("P154_ORIGINAL_169_SOURCE_TEST_MODULES_INVENTORIED=169", flush=True)
    print("P154_P135_COMPLETE_FULL_WINDOWS_PASSES=0", flush=True)
    print("P154_P142_ORIGINAL_POST_STALL=54_PASS_20_HOLD_9_TIMEOUT", flush=True)
    print("P154_AUTHENTICATED_POST_RECOVERY_SUFFIX=60_PASS_16_HOLD_7_TIMEOUT",
          flush=True)
    print("P154_P144_AUTHENTIC_ORIGINAL_FAIL_ERROR_HEADINGS=30", flush=True)
    print("P154_ORIGINAL_83_SUFFIX_NOT_CLEARED=23", flush=True)
    print("P154_PRESTALL_ORIGINAL_86_NOT_CLEARED_BY_COMPLETE_FULL_REGRESSION=86",
          flush=True)
    print("P154_FULL_PRODUCT_WINDOWS_TRIAD=0_COMPLETE", flush=True)
    print("P154_INDEPENDENT_REGRESSION_AND_SECURITY_REVIEW=NOT_OBTAINED",
          flush=True)
    print("P154_SIGNED_PRODUCTION_AND_SAC_WDAC_GO=NOT_OBTAINED", flush=True)
    print("P154_USER_SCOPE_C1_PRODUCTION_RELEASE=HOLD", flush=True)
    print("P154_REGRESSION_LEDGER_SHA256=" + _sha(manifest.read_bytes()),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
