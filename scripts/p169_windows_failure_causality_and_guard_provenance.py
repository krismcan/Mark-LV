"""P169: genuine Windows originals, failure retention & thread guard provenance.

Source-preserving diagnostic, NOT a source repair, acceptance or production GO.
All original historical tests and production modules remain byte-identical.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import zipfile

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p166_windows_current_branch_acceptance import PROTECTED

ROOT = Path(__file__).resolve().parents[1]
BASE = "0f7cd007f535db108f0306c8b11d3097f2cf774e"
BRANCH = "byok-c1-p169-native-failure-causality-and-thread-guard-provenance-20261112"
NEW_PATHS = {
    "scripts/p169_windows_failure_causality_and_guard_provenance.py",
    ".github/workflows/p169-windows-failure-causality-and-guard-provenance.yml",
    "docs/byok-c1-p169-causal-regression-and-security-review.md",
}
P168_ARCHIVE = (13923308046,
                "AB3057127EF9533E0115BF9201EA2ADC120419F5E626111F5616C59EEF8ECE43")
P168_LEDGER = "p168_source_bound_original_regression_frontier.json"
P168_HASHES = {
    "tests.test_phase_831_effect_isolation":
        "9CEF59484DC9D9B914F0C9382FEB9DD491A80DE2C1EFBFE5CD034305739A5C7C",
    "tests.test_phase_832_lifecycle_assurance":
        "E3CC65952363F6031BB7D4E49374D8CC46E3CB358CE6BB6CC65E3BA09949327C",
    "tests.test_windows_credential_backend":
        "5F3B37438C0A1E5C3DBD0770F2E021CA041E7D4C52580AE1D80592BC77757EB2",
}
P168_EXPECTED_ISSUES = {
    "tests.test_phase_831_effect_isolation": (19, 2),
    "tests.test_phase_832_lifecycle_assurance": (14, 5),
    "tests.test_windows_credential_backend": (24, 2),
}
TEST831 = "tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests."
STATIC831 = "test_static_production_import_closure_forbids_test_and_effect_routes"
TESTWIN = "tests.test_windows_credential_backend."
STATICWIN = "ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused"
ORIGINAL_SCOPE_TEST_PATHS = {
    "tests/test_phase_831_effect_isolation.py",
    "tests/test_phase_832_lifecycle_assurance.py",
    "tests/test_windows_credential_backend.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
}
FOOTER = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s$", re.M)
ERROR_HEADING = re.compile(r"^(FAIL|ERROR): (.+)$", re.M)
SENSITIVE = {"GITHUB_TOKEN", "GH_TOKEN", "P169_EVIDENCE_TOKEN",
             "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
             "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}
GUARDED_METHODS = (
    ("OfflineWorkspaceApplication", "_open_local_byok", 3),
    ("ConnectionWindow", "begin_synthetic_pending_observation", 0),
    ("ConnectionWindow", "cancel_synthetic_pending_observation", 1),
    ("ConnectionWindow", "publish_synthetic_pending_observation", 2),
    ("ConnectionWindow", "show_pending_custody_advisory", 2),
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(ROOT), *args],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=25, check=True)
    return result.stdout

def custody() -> dict:
    _guard_runner()
    if not (sys.platform == "win32"
            and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_OS") == "Windows"
            and os.environ.get("GITHUB_EVENT_NAME") == "push"
            and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.environ.get("GITHUB_REF_NAME") == BRANCH
            and os.environ.get("RUNNER_TEMP")):
        raise RuntimeError("P169 requires authenticated Windows push event")
    head = git("rev-parse", "HEAD").decode().strip()
    if (head != os.environ.get("GITHUB_SHA")
            or git("branch", "--show-current").decode().strip() != BRANCH
            or git("merge-base", "HEAD", BASE).decode().strip() != BASE
            or git("status", "--porcelain=v1").strip()):
        raise RuntimeError("P169 exact HEAD / P168 ancestry or clean source mismatch")
    changed = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changed != NEW_PATHS:
        raise RuntimeError("P169 unexpected source/security/test mutation")
    if any(git("ls-tree", "--name-only", BASE, "--", p).strip() for p in changed):
        raise RuntimeError("P169 cannot replace any original source path")
    base_tests = [p for p in git("ls-tree", "-r", "--name-only", BASE, "--", "tests")
                  .decode().splitlines() if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    now_tests = [p for p in git("ls-files", "tests/test_*.py").decode().splitlines()
                 if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    if len(base_tests) != 171 or sorted(base_tests) != sorted(now_tests):
        raise RuntimeError("P169 original 171 source test modules drifted")
    protected = {}
    for p in sorted(set(PROTECTED) | ORIGINAL_SCOPE_TEST_PATHS):
        past, current, disk = (git("show", BASE + ":" + p),
                               git("show", "HEAD:" + p), (ROOT / p).read_bytes())
        if past != current or current != disk:
            raise RuntimeError("P169 frozen product/original test custody changed: " + p)
        protected[p] = sha(current)
    return {"head": head, "parent": BASE, "three_new_evidence_paths": sorted(changed),
            "unmodified_original_test_modules": len(base_tests),
            "original_protected_source_sha256": protected}

def old_evidence(token: str) -> dict:
    if len(token) < 8:
        raise RuntimeError("P169 read-only Actions token missing")
    raw = _download_artifact(P168_ARCHIVE[0], P168_ARCHIVE[1], token)
    if sha(raw) != P168_ARCHIVE[1]:
        raise RuntimeError("P168 source-bound original native archive mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise RuntimeError("P168 archived test evidence corrupted")
        expected = {P168_LEDGER} | {
            "p168_actual_" + m.replace(".", "_") + ".log" for m in P168_HASHES
        }
        if set(z.namelist()) != expected or len(z.namelist()) != len(expected):
            raise RuntimeError("P168 raw original log inventory differs")
        ledger = json.loads(z.read(P168_LEDGER))
        if (ledger.get("checkpoint") != "P168"
                or ledger.get("accepted_complete_full_product_regressions") != "0/3"
                or ledger.get("production_R") != "HOLD"):
            raise RuntimeError("P168 historical release HOLD incorrectly changed")
        prior = ledger["P168_actual_unmodified_entire_original_native_module_results"]
        for module, digest in P168_HASHES.items():
            log = z.read("p168_actual_" + module.replace(".", "_") + ".log")
            entry = prior[module]
            count, failures = P168_EXPECTED_ISSUES[module]
            text = log.decode("utf-8", "replace").replace("\r\n", "\n")
            if (sha(log) != digest or entry["archived_raw_log_sha256"] != digest
                    or entry["actual_native_exit"] != 1
                    or entry["original_unittest_count"] != count
                    or entry["actual_original_verdict"] != "HOLD"
                    or len(entry["genuine_original_named_FAIL_ERROR_records"]) != failures
                    or len(ERROR_HEADING.findall(text)) != failures
                    or not re.search(r"^FAILED \(", text, re.M)
                    or not any(int(x) == count for x, _ in FOOTER.findall(text))):
                raise RuntimeError("P168 real native test result reclassified or ungrounded")
    return {"checkpoint": "P168", "artifact_id": P168_ARCHIVE[0],
            "authenticated_original_zip_sha256": sha(raw),
            "original_three_entire_native_test_modules": [
                {"module": m, "original_native_exit": 1,
                 "original_FAIL_ERROR_record_count": P168_EXPECTED_ISSUES[m][1],
                 "original_test_count": P168_EXPECTED_ISSUES[m][0],
                 "original_raw_log_sha256": P168_HASHES[m]}
                for m in P168_HASHES
            ],
            "original_fails_unwaived": True}

def original_831_ids() -> list[str]:
    path = ROOT / "tests/test_phase_831_effect_isolation.py"
    tree = ast.parse(path.read_text(encoding="utf8"))
    cls = [node for node in tree.body if isinstance(node, ast.ClassDef)
           and node.name == "Phase831EffectIsolationTests"]
    if len(cls) != 1:
        raise RuntimeError("P169 original Tk module class identity changed")
    methods = sorted(node.name for node in cls[0].body
                     if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"))
    if len(methods) != 19 or methods.count(STATIC831) != 1:
        raise RuntimeError("P169 original Phase8.31 19-case class identity drift")
    return [TEST831 + m for m in methods]

def run_original(label: str, ids: list[str], expected: int,
                 temp: Path, evidence: Path) -> dict:
    env = os.environ.copy()
    for key in list(env):
        if key in SENSITIVE or key.endswith("_API_KEY") or key.endswith("_SECRET"):
            env.pop(key, None)
    env.update({"TEMP": str(temp), "TMP": str(temp),
                "TMPDIR": str(temp), "PYTHONDONTWRITEBYTECODE": "1"})
    log_name = "p169_native_" + label + ".log"
    start = time.monotonic()
    timed_out = False
    with (evidence/log_name).open("wb") as f:
        proc = subprocess.Popen([sys.executable, "-B", "-m", "unittest", "-v", *ids],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=f, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        try:
            native = proc.wait(timeout=90)
        except subprocess.TimeoutExpired:
            native, timed_out = 124, True
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=False, timeout=15)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    raw = (evidence/log_name).read_bytes()
    content = raw.decode("utf8", "replace").replace("\r\n", "\n")
    footer = FOOTER.findall(content)
    observed = int(footer[-1][0]) if footer else None
    named = [{"kind": kind, "name": name} for kind, name in ERROR_HEADING.findall(content)]
    good = (native == 0 and observed == expected
            and bool(re.search(r"^OK\s*$", content, re.M)))
    failed = (native == 1 and observed == expected
              and bool(re.search(r"^FAILED \(", content, re.M)))
    label_state = "PASS" if good else "HOLD" if failed else "TIMEOUT" if timed_out else "INCOMPLETE"
    print("P169_ORIGINAL_NATIVE="+label+"|EXIT="+str(native)+"|RAN="+str(observed)+
          "|STATUS="+label_state+"|FAIL_ERROR_RECORDS="+str(len(named)), flush=True)
    print("P169_RAW_LOG_SHA256="+label+"|"+sha(raw),flush=True)
    return {"label": label, "original_test_ids": ids, "expected_original_count": expected,
            "actual_native_exit": native, "complete_original_unittest_count": observed,
            "actual_original_status": label_state, "genuine_original_fail_error_records": named,
            "retired_fake_Tk_root_error_present": "retired fake Tk roots still live" in content,
            "static_import_closure_failure_present": "workspace_window.py" in content
                and "test_static_production_import_closure" in content,
            "original_raw_log_file": log_name, "original_raw_log_sha256": sha(raw),
            "original_raw_log_bytes": len(raw), "seconds": round(time.monotonic()-start,3)}

def source_guard_sequence(class_name: str, method: str) -> dict:
    path = ("nayeon/desktop_alpha/application.py"
            if class_name == "OfflineWorkspaceApplication"
            else "nayeon/desktop_alpha/workspace_window.py")
    source = ast.parse((ROOT/path).read_text(encoding="utf8"))
    matching = [node for node in source.body
                if isinstance(node, ast.ClassDef) and node.name == class_name]
    if len(matching) != 1:
        raise RuntimeError("P169 protected class source changed: " + class_name)
    methods = [node for node in matching[0].body
               if isinstance(node, ast.FunctionDef) and node.name == method]
    if len(methods) != 1:
        raise RuntimeError("P169 protected method absent: " + method)
    node = methods[0]
    if len(node.body) < 3:
        raise RuntimeError("P169 original guarded method unexpectedly truncated")
    first = node.body[0]
    second = node.body[1]
    if (not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
             and isinstance(first.value.value, str))
            or not (isinstance(second, ast.Expr)
                    and ast.unparse(second) == "self._require_creator_thread()")):
        raise RuntimeError("P169 documented-first then guard sequencing drift")
    # Explicit in-memory adversarial negative: removing/moving guard cannot
    # satisfy this recognition; never mutate original source on disk.
    mutated = ast.parse("def " + method + "(self):\n"
                        "    'synthetic docstring'\n"
                        "    self._alive = False\n"
                        "    self._require_creator_thread()\n")
    if ast.unparse(mutated.body[0].body[1]) == "self._require_creator_thread()":
        raise RuntimeError("P169 in-memory reordered negative was accidentally accepted")
    return {"source_path": path, "class": class_name, "method": method,
            "first_original_AST_node": "docstring",
            "first_executable_original_AST_node": "self._require_creator_thread()",
            "original_security_test_requires_first_AST_node": True,
            "historical_original_static_contract": "HOLD",
            "in_memory_reordered_guard_negative": "REJECTED"}

def genuine_cross_thread_unbound_guard_calls() -> list[dict]:
    from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
    from nayeon.desktop_alpha.workspace_window import ConnectionWindow
    classes = {"OfflineWorkspaceApplication": OfflineWorkspaceApplication,
               "ConnectionWindow": ConnectionWindow}
    results = []
    for class_name, method, nargs in GUARDED_METHODS:
        order = source_guard_sequence(class_name, method)
        owner = threading.get_ident()
        record = {"guard_calls": 0, "side_effect_or_other_attribute_read": 0}
        class Probe:
            def __getattribute__(self, key):
                if key == "_require_creator_thread":
                    def guard():
                        record["guard_calls"] += 1
                        if threading.get_ident() != owner:
                            raise RuntimeError("WRONG_THREAD")
                        return None
                    return guard
                record["side_effect_or_other_attribute_read"] += 1
                raise AssertionError("Original production method touched field before creator-thread guard")
        actual = getattr(classes[class_name], method)
        seen = []
        def thread_entry():
            try:
                actual(Probe(), *([None]*nargs))
                seen.append("UNSAFE_NO_WRONG_THREAD_REFUSAL")
            except RuntimeError as exc:
                seen.append(str(exc))
            except Exception as exc:
                seen.append(type(exc).__name__)
        worker = threading.Thread(target=thread_entry, name="P169-synthetic-unbound-guard")
        worker.start()
        worker.join(timeout=4)
        if worker.is_alive() or seen != ["WRONG_THREAD"] or record != {
                "guard_calls": 1, "side_effect_or_other_attribute_read": 0}:
            raise RuntimeError("P169 a guarded method failed before-effects wrong-thread refusal")
        results.append({**order, "real_worker_thread_original_unbound_method": "WRONG_THREAD",
                        "creator_guard_invocations": 1, "pre_guard_field_reads": 0,
                        "limitation": "Uses a synthetic sentinel, not live Tk widget or production process"})
    return results

APPROVED_SOURCE_CONSUMERS = {
    "nayeon/brain/connection_document.py",
    "nayeon/brain/providers/openai_client.py",
    "nayeon/brain/providers/openai_validation.py",
    "nayeon/secrets/lifecycle.py", "nayeon/brain/connection.py",
    "nayeon/secrets/contracts.py", "nayeon/secrets/windows_credential.py",
    "nayeon/secrets/resolver.py", "nayeon/brain/providers/openai.py",
    "nayeon/brain/credential_onboarding.py",
    "nayeon/brain/credential_onboarding_composition.py",
    "nayeon/brain/onboarding_metadata_document.py",
    "nayeon/brain/connection_reconciliation.py",
    "nayeon/brain/connection_composition.py",
    "nayeon/brain/connection_readiness.py",
    "nayeon/brain/credential_operation_host.py",
    "nayeon/desktop_alpha/first_run_credential_validation_window.py",
    "nayeon/desktop_alpha/first_run_credential_management_window.py",
}
WINCRED_IMPORTS = {"nayeon.secrets.contracts", "nayeon.secrets.windows_credential"}

def credential_consumer_provenance() -> dict:
    consumers = []
    for path in sorted((ROOT/"nayeon").rglob("*.py")):
        name = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in WINCRED_IMPORTS:
                consumers.append({"path": name, "import": node.module,
                                  "names": sorted(a.name for a in node.names),
                                  "old_8_3_allowlisted": name in APPROVED_SOURCE_CONSUMERS,
                                  "line": node.lineno})
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name in WINCRED_IMPORTS:
                        consumers.append({"path": name, "import": a.name, "names": ["*"],
                                          "old_8_3_allowlisted": name in APPROVED_SOURCE_CONSUMERS,
                                          "line": node.lineno})
    unauthorized = [c for c in consumers if not c["old_8_3_allowlisted"]]
    if not unauthorized:
        raise RuntimeError("P169 P168 original unapproved WinCred consumer failure does not match source")
    test_injection = ast.parse("from nayeon.secrets.windows_credential import WindowsCredentialBackend")
    if not any(isinstance(n, ast.ImportFrom) and n.module in WINCRED_IMPORTS
               for n in ast.walk(test_injection)):
        raise RuntimeError("P169 in-memory forbidden consumer negative undetected")
    return {"source_consumer_imports": consumers,
            "unapproved_under_frozen_historical_8_3_contract": unauthorized,
            "in_memory_unapproved_native_backend_import_negative": "DETECTED",
            "unapproved_does_not_imply_safe_to_allowlist": True,
            "no_production_wincred_api_called": True}

def production_import_closure() -> dict:
    path = ROOT/"nayeon/desktop_alpha/workspace_window.py"
    tree = ast.parse(path.read_text(encoding="utf8"))
    forbidden = ("tests", "socket", "subprocess", "winreg",
                 "nayeon.brain", "nayeon.actions", "nayeon.credentials")
    seen = []
    for node in ast.walk(tree):
        imports = ([] if not isinstance(node, ast.Import) else [x.name for x in node.names])
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        for name in imports:
            if any(name == x or name.startswith(x+".") for x in forbidden):
                seen.append({"original_source_path": path.relative_to(ROOT).as_posix(),
                             "line": node.lineno, "unreviewed_module_import": name})
    if not seen:
        raise RuntimeError("P169 Phase8.31 historical production import-closure failure missing")
    negative = ast.parse("from nayeon.brain.pending_custody_observation_boundary import SyntheticObservationLease")
    if not any(isinstance(n, ast.ImportFrom) and n.module.startswith("nayeon.brain.")
               for n in ast.walk(negative)):
        raise RuntimeError("P169 synthetic in-memory importer negative was not detected")
    return {"historically_disallowed_actual_imports": seen,
            "frozen_8_31_import_closure_still_HOLD": True,
            "synthetic_disallowed_import_in_memory_negative": "DETECTED",
            "review_needed_for_different_era_synthetic_observation_ui_contract": True}

def main() -> int:
    before = custody()
    old = old_evidence(os.environ.get("P169_EVIDENCE_TOKEN", ""))
    ids = original_831_ids()
    selected = [x for x in ids if not x.endswith(STATIC831)]
    if len(selected) != 18:
        raise RuntimeError("P169 original 18 selected methods incomplete")
    evidence = Path(os.environ["RUNNER_TEMP"])/"nayeon-p169-native-causal-evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    original_guard_probes = genuine_cross_thread_unbound_guard_calls()
    imports = credential_consumer_provenance()
    closure = production_import_closure()
    temp = Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P169 disposable Windows root collision")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        outcomes = {
            "phase831_all_18_other_originals": run_original(
                "phase831_all_18_other_originals", selected, 18, temp, evidence),
            "phase831_original_static_closure_alone": run_original(
                "phase831_original_static_closure_alone", [TEST831 + STATIC831], 1,
                temp, evidence),
            "wincred_20_original_fake_native_controls": run_original(
                "wincred_20_original_fake_native_controls",
                [TESTWIN+"BackendTests", TESTWIN+"NativeAdapterTests"], 20, temp, evidence),
            "wincred_original_static_consumer_refusal_alone": run_original(
                "wincred_original_static_consumer_refusal_alone",
                [TESTWIN+STATICWIN], 1, temp, evidence),
        }
    finally:
        if made:
            st = temp.lstat()
            if temp.is_symlink() or getattr(st, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P169 linked/reparse TEMP deletion refused")
            shutil.rmtree(temp)
    if custody() != before:
        raise RuntimeError("P169 source or index changed mid-run")
    other = outcomes["phase831_all_18_other_originals"]
    isolated = outcomes["phase831_original_static_closure_alone"]
    natives = outcomes["wincred_20_original_fake_native_controls"]
    old_consumer = outcomes["wincred_original_static_consumer_refusal_alone"]
    closed_controls = (other["actual_original_status"] == "PASS"
                       and not other["retired_fake_Tk_root_error_present"]
                       and natives["actual_original_status"] == "PASS")
    negative_reproduced = (
        isolated["actual_original_status"] == "HOLD"
        and isolated["static_import_closure_failure_present"]
        and old_consumer["actual_original_status"] == "HOLD"
    )
    report = {
        "checkpoint": "P169",
        "exact_current_GitHub_source_protected_sha256": before,
        "authentic_prior_P168_three_original_full_module_HOLD_evidence": old,
        "P169_genuine_unmodified_original_targeted_Windows_tests": outcomes,
        "P169_5_original_unbound_creatorthread_guard_real_worker_negative_probes": original_guard_probes,
        "P169_actual_WinCred_consumer_source_provenance": imports,
        "P169_actual_UI_production_import_closure_source_provenance": closure,
        "original_other_18_and_native_fake_20_controls_PASS": closed_controls,
        "original_static_failure_reproduced_UNWAIVED": negative_reproduced,
        "phase831_Tk_teardown_may_be_coupled_to_original_failure_retention": (
            closed_controls and negative_reproduced and
            isolated["retired_fake_Tk_root_error_present"]),
        "historical_H_full_19_case_8_31_original_module": "HOLD",
        "historical_H_full_24_case_WinCred_original_module": "HOLD",
        "historical_H_full_14_case_8_32_original_module": "HOLD",
        "current_C": "P166_REDUCED_SCOPE_CANDIDATE_ONLY",
        "production_R": "HOLD",
        "accepted_native_complete_whole_product_regressions": "0/3",
        "qualified_independent_security_and_test_governance_GO": "NOT_OBTAINED",
        "original_frozen_P76_P85_guards_and_all_failures_waived": False,
        "real_CredWrite_CredDelete_or_production_provider_communications": "NOT_ATTEMPTED",
        "signed_main_helper_installer_or_SAC_WDAC_owner_GO": "NOT_OBTAINED",
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "cautions": [
            "18-of-19 and 20-of-24 targeted original tests are diagnostics, NOT whole original module PASS",
            "Tk-root causal coupling is inferred from differential original suites; not a complete object lifetime/referrer audit",
            "Unbound original runtime method probes use synthetic owner sentinel, not actual constructed Tk widgets or OS EDR telemetry",
            "Static AST allowed-source policies are frozen era-specific security tests; never silently expand them",
            "Independent qualified reviewer must approve any revised production import, thread-guard or secret consumer policy",
        ],
    }
    (evidence/"p169_authentic_original_native_causal_source_bound_ledger.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("P169_REAL_18_ORIGINAL_OTHER_PHASE831_PASS="+str(other["actual_original_status"]=="PASS"),flush=True)
    print("P169_REAL_SINGLE_STATIC_IMPORT_FAILURE_UNWAIVED="+str(isolated["actual_original_status"]=="HOLD"),flush=True)
    print("P169_REAL_20_ORIGINAL_FAKE_NATIVE_TESTS_PASS="+str(natives["actual_original_status"]=="PASS"),flush=True)
    print("P169_REAL_STATIC_WINCRED_FAIL_UNWAIVED="+str(old_consumer["actual_original_status"]=="HOLD"),flush=True)
    print("P169_REAL_WORKER_5_ORIGINAL_PRODUCTION_UNBOUND_GUARDS=WRONG_THREAD",flush=True)
    print("P169_FROZEN_ORIGINAL_H=HOLD|CURRENT_C=REDUCED_SCOPE_ONLY|PRODUCTION_R=HOLD",flush=True)
    print("P169_COMPLETE_PRODUCT_WINDOWS_ACCEPTANCE=0/3",flush=True)
    return 0 if closed_controls and negative_reproduced else 1

if __name__ == "__main__":
    raise SystemExit(main())
