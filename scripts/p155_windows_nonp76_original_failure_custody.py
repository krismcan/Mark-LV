"""P155 evidence-only: authenticated P144 raw failures and focused real Windows tests.

No original assertions, product security source, P76/P85 gates or WinCred state
are altered. A collector success never means that historical tests passed.
"""
from __future__ import annotations
import ast
from concurrent.futures import ThreadPoolExecutor
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
import types
import uuid
import zipfile
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner, _verify_original_handle_policy
from scripts.p154_windows_authenticated_full_regression_ledger import ARCHIVES, _download_artifact, _sha

BASE = "2103ccc658f0cea474ec8f5bc945eacb664771cd"
BRANCH = "byok-c1-p155-non-p76-security-lifecycle-recovery-20261111"
FOCUS = (
    "tests.test_phase_832_lifecycle_assurance.Phase832StaticContractTests.test_every_direct_owned_method_has_first_pure_thread_gate",
    "tests.test_windows_credential_backend.ScopeGuards.test_exact_import_boundaries_and_no_forbidden_native_calls",
    "tests.test_windows_credential_backend.ScopeGuards.test_only_approved_secret_consumers_and_legacy_store_unused",
)
SECRETS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GITHUB_TOKEN",
           "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
           "P155_EVIDENCE_TOKEN")
COUNT = re.compile(r"^Ran (\d+) tests? in [0-9.]+s$", re.MULTILINE)

def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, stdin=subprocess.DEVNULL,
                       timeout=30, check=True)
    return p.stdout.decode("utf8", "replace").strip()

def original_p144(output, token):
    artifact, digest = ARCHIVES["p144"]
    raw_zip = _download_artifact(artifact, digest, token)
    if _sha(raw_zip) != digest:
        raise RuntimeError("Original P144 archive mismatch")
    results = []
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zipfile_obj:
        manifest = json.loads(zipfile_obj.read("p144_original_residual_manifest.json"))
        if len(manifest["results"]) != 15 or manifest["summary"] != {
            "PASS": 0, "HOLD": 15, "TIMEOUT": 0
        }:
            raise RuntimeError("Original 15-module P144 inventory drift")
        for item in manifest["results"]:
            module = item["module"]
            name = "p144_" + module.replace(".", "_") + ".log"
            blob = zipfile_obj.read(name)
            if (_sha(blob) != item["log_sha256"] or
                len(blob) != item["log_bytes"] or
                item["native_exit"] != 1 or item["status"] != "HOLD"):
                raise RuntimeError("Original P144 module custody invalid: " + module)
            failures = [line.split(":", 1)[1].strip().split(" (", 1)[0]
                        for line in blob.decode("utf8", "replace").splitlines()
                        if line.startswith(("FAIL: ", "ERROR: "))]
            if failures != item["failure_ids"]:
                raise RuntimeError("Original P144 failure IDs drift: " + module)
            (output / name).write_bytes(blob)
            results.append({"module": module, "original_failure_ids": failures,
                            "original_log_sha256": _sha(blob),
                            "original_native_exit": 1, "original_test_count": item["completed_unittest_count"],
                            "original_log_name": name, "artifact_id": artifact,
                            "disposition": "HOLD_UNRESOLVED_UNTIL_TRACE_REVIEW"})
    if sum(len(x["original_failure_ids"]) for x in results) != 30:
        raise RuntimeError("P144 source failed 30 original case inventory")
    print("P155_ORIGINAL_P144_LOGS_AUTHENTICATED=15", flush=True)
    print("P155_ORIGINAL_UNWAIVED_FAILURE_ERROR_RECORDS=30", flush=True)
    return results

def adverse_thread():
    from nayeon.desktop_alpha import application, workspace_window, presentation_window
    classes = (application.OfflineWorkspaceApplication, workspace_window.WorkspaceWindow,
               workspace_window.WorkspacePane, workspace_window.ConversationWindow,
               workspace_window.ConnectionWindow, presentation_window.PresentationWindow)
    methods, prior_docstrings = 0, []
    for cls in classes:
        tree = ast.parse(inspect.getsource(cls))
        for node in tree.body[0].body:
            if not isinstance(node, ast.FunctionDef) or node.name in ("__init__", "_require_creator_thread"):
                continue
            body = list(node.body)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                prior_docstrings.append(cls.__name__ + "." + node.name)
                body = body[1:]
            if not body or not isinstance(body[0], ast.Expr) or ast.unparse(body[0]) != "self._require_creator_thread()":
                raise RuntimeError("True first-executable thread guard missing: " + cls.__name__ + "." + node.name)
            methods += 1
    main_id = threading.get_ident()
    cases = (
        (application.OfflineWorkspaceApplication, "_open_local_byok", (None, None, None)),
        (workspace_window.ConnectionWindow, "begin_synthetic_pending_observation", ()),
        (workspace_window.ConnectionWindow, "cancel_synthetic_pending_observation", (None,)),
        (workspace_window.ConnectionWindow, "publish_synthetic_pending_observation", (None, None)),
        (workspace_window.ConnectionWindow, "show_pending_custody_advisory", (None, None)),
    )
    negatives = []
    for cls, name, args in cases:
        fake = types.SimpleNamespace(_creator_thread=main_id)
        fake._require_creator_thread = types.MethodType(cls._require_creator_thread, fake)
        def worker():
            try:
                getattr(cls, name)(fake, *args)
            except RuntimeError as error:
                return str(error)
            except BaseException as error:
                return "UNEXPECTED_" + type(error).__name__
            return "UNEXPECTED_ACCEPT"
        with ThreadPoolExecutor(max_workers=1) as pool:
            observed = pool.submit(worker).result(timeout=15)
        if observed != "WRONG_THREAD":
            raise RuntimeError("Source method did not refuse foreign thread: " + name)
        negatives.append({"method": cls.__name__ + "." + name, "rejected": observed})
    print("P155_FIRST_EXECUTABLE_THREAD_GATE_METHOD_COUNT=" + str(methods), flush=True)
    print("P155_5_REAL_METHOD_FOREIGN_THREAD_REFUSALS=5", flush=True)
    return {"methods_gated_after_optional_docstring": methods,
            "methods_with_docstring_before_guard": prior_docstrings,
            "foreign_thread_refusals": negatives}

def run_case(repo, temp, output, target, index):
    env = os.environ.copy()
    for key in SECRETS:
        env.pop(key, None)
    for name in ("TMP", "TEMP", "TMPDIR"):
        env[name] = str(temp)
    log_name = "p155_original_focused_case_" + str(index) + ".log"
    path = output / log_name
    begin = time.monotonic()
    try:
        with path.open("wb") as out:
            p = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", target],
                               cwd=repo, env=env, stdin=subprocess.DEVNULL,
                               stdout=out, stderr=subprocess.STDOUT, timeout=65)
        native = p.returncode
    except subprocess.TimeoutExpired:
        native = 124
    except OSError:
        native = 125
    raw = path.read_bytes() if path.exists() else b""
    decoded = raw.decode("utf8", "replace")
    counts = COUNT.findall(decoded)
    complete = len(counts) == 1 and int(counts[0]) == 1 and native in (0, 1)
    status = "PASS" if complete and native == 0 and re.search(r"^OK\s*$", decoded, re.M) else "HOLD" if complete else "INCOMPLETE"
    r = {"original_test": target, "native_exit": native, "original_unittest_count": int(counts[0]) if counts else None,
         "status": status, "full_log": log_name, "sha256": _sha(raw),
         "seconds": round(time.monotonic() - begin, 3),
         "failure_headings": [line for line in decoded.splitlines() if line.startswith(("FAIL: ", "ERROR: "))]}
    print("P155_ORIGINAL_TEST="+target+"|EXIT="+str(native)+"|"+status+"|SHA256="+r["sha256"], flush=True)
    return r

def main():
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("Exact P155 isolated branch required")
    repo = Path(__file__).resolve().parents[1]
    head = git(repo, "rev-parse", "HEAD")
    if head != os.environ.get("GITHUB_SHA") or git(repo, "merge-base", BASE, "HEAD") != BASE:
        raise RuntimeError("Original P154 SHA ancestry or event SHA mismatch")
    output = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p155-authenticated-nonp76"
    output.mkdir(parents=True, exist_ok=True)
    token = os.environ.pop("P155_EVIDENCE_TOKEN", "")
    if not token:
        raise RuntimeError("P155 read-only historical evidence token missing")
    originals = original_p144(output, token)
    del token
    thread = adverse_thread()
    temp = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P155 local fixture already exists")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        focus = [run_case(repo, temp, output, item, index)
                 for index, item in enumerate(FOCUS, start=1)]
    finally:
        if made:
            stat = temp.lstat()
            if temp.is_symlink() or (getattr(stat, "st_file_attributes", 0) & 0x400):
                raise RuntimeError("P155 temp fixture reparse cleanup refused")
            shutil.rmtree(temp)
    payload = {"checkpoint": "P155", "p154_parent": BASE, "source_head": head,
               "original_p144_results": originals, "source_and_thread_negatives": thread,
               "focused_original_tests": focus, "source_modified": False,
               "production_keys_or_WinCred_used": False,
               "full_product_windows_regressions_passed": 0,
               "qualified_independent_reviewer_approved": False,
               "privileged_g0_g6": "OPEN", "production_release": "HOLD"}
    (output / "p155_original_failure_and_native_windows_evidence.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print("P155_COLLECTOR_GO_IS_NOT_ORIGINAL_TEST_PASS=TRUE", flush=True)
    print("P155_RELEASE_HOLD=TRUE", flush=True)
    return 0 if len(focus) == 3 and all(x["status"] != "INCOMPLETE" for x in focus) else 1

if __name__ == "__main__":
    raise SystemExit(main())
