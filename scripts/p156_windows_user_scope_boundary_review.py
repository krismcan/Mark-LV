"""P156 isolated user-scope import/credential trust-boundary Windows diagnostic.

Evidence only. Preserve exact original historical failures and source seals.
No production credential store, real API key, provider call, or binary launch.
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

BASE = "27e119825d7c83a891b7d80b208bf2b7709e10bc"
BRANCH = "byok-c1-p156-user-scope-import-credential-boundary-review-20261111"
ROOT = Path(__file__).resolve().parents[1]
SAFE_IMPORTS = (
    "nayeon.brain.pending_custody_observation_boundary",
    "nayeon.brain.pending_custody_status_view",
)
LAZY_METHODS = {
    "begin_synthetic_pending_observation",
    "cancel_synthetic_pending_observation",
    "publish_synthetic_pending_observation",
    "show_pending_custody_advisory",
}
FOCUS = (
    ("p132_fake_wincred_and_tk", "tests.test_local_user_scope_byok", True),
    ("p133_manual_launch_fake_subprocess", "tests.test_p133_connection_launch", True),
    ("original_p831_static_import_closure", (
        "tests.test_phase_831_effect_isolation.Phase831EffectIsolationTests."
        "test_static_production_import_closure_forbids_test_and_effect_routes"
    ), False),
)
COUNTS = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.MULTILINE)
SENSITIVE_ENV = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GH_TOKEN",
    "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "P156_ARTIFACT_TOKEN",
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True,
        stdin=subprocess.DEVNULL, timeout=20, check=True,
    )
    return result.stdout.decode("utf8", "replace").strip()


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf8"), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def _live_module_file(module: str) -> Path | None:
    if not module.startswith("nayeon."):
        return None
    name = ROOT / (module.replace(".", "/") + ".py")
    return name if name.is_file() else None


def _source_boundary():
    source = ROOT / "nayeon/desktop_alpha/workspace_window.py"
    tree = ast.parse(source.read_text(encoding="utf8"))
    connect = next(
        cls for cls in tree.body
        if isinstance(cls, ast.ClassDef) and cls.name == "ConnectionWindow"
    )
    lazy = {}
    for item in connect.body:
        if not isinstance(item, ast.FunctionDef) or item.name not in LAZY_METHODS:
            continue
        body = list(item.body)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            body = body[1:]
        if not (body and isinstance(body[0], ast.Expr)
                and ast.unparse(body[0]) == "self._require_creator_thread()"):
            raise RuntimeError("P156 native UI boundary lacks first executable thread gate")
        lazy[item.name] = sorted({
            node.module for node in ast.walk(item)
            if isinstance(node, ast.ImportFrom) and node.module.startswith("nayeon.brain.")
        })
    if set(lazy) != LAZY_METHODS:
        raise RuntimeError("P156 ConnectionWindow lazy-import method inventory drift")
    actual = set().union(*(set(vals) for vals in lazy.values()))
    if actual != set(SAFE_IMPORTS):
        raise RuntimeError("P156 unexpected direct brain import in UI")
    all_imports = _imports(source)
    for module in all_imports:
        if module.startswith("nayeon.brain.") and module not in SAFE_IMPORTS:
            raise RuntimeError("P156 uncontrolled desktop brain import")
    visited = {}
    stack = list(SAFE_IMPORTS)
    while stack:
        module = stack.pop()
        if module in visited:
            continue
        path = _live_module_file(module)
        if path is None:
            raise RuntimeError("P156 missing transitively imported named product module")
        dependencies = sorted(_imports(path))
        visited[module] = dependencies
        for dep in dependencies:
            if (dep == "nayeon.secrets.windows_credential"
                or dep.startswith("nayeon.brain.providers")
                or dep == "nayeon.brain.local_byok_user_scope"
                or dep == "nayeon.secrets.lifecycle"
                or dep == "nayeon.secrets.resolver"
                or dep == "nayeon.brain.credential_operation_host"):
                raise RuntimeError("P156 UI read-only branch reaches native credential/provider authority")
            if dep.startswith("nayeon.") and _live_module_file(dep) is not None:
                stack.append(dep)
    print("P156_UI_FOUR_EXACT_LAZY_IMPORT_METHODS=PASS", flush=True)
    print("P156_READ_ONLY_TRANSITIVE_IMPORT_CLOSURE_MODULES="+str(len(visited)), flush=True)

    controller = ROOT / "nayeon/brain/local_byok_user_scope.py"
    window = ROOT / "nayeon/desktop_alpha/local_byok_window.py"
    cimports = _imports(controller)
    wimports = _imports(window)
    if "nayeon.secrets.windows_credential" not in cimports:
        raise RuntimeError("P156 trusted controller source contract changed")
    if ("nayeon.secrets.windows_credential" in wimports
        or "nayeon.secrets.resolver" in wimports
        or "nayeon.brain.providers.openai_validation" in wimports):
        raise RuntimeError("P156 user UI gained forbidden native/provider direct import")
    if ("nayeon.secrets.contracts" not in wimports
        or "nayeon.brain.local_byok_user_scope" not in wimports):
        raise RuntimeError("P156 user UI typed-controller contract changed")
    ctree = ast.parse(controller.read_text(encoding="utf8"))
    fixed = [node for node in ctree.body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == "_FIXED_IDENTIFIER"
                     for target in node.targets)]
    if len(fixed) != 1 or not isinstance(fixed[0].value, ast.Call):
        raise RuntimeError("P156 exact fixed credential target not demonstrable")
    args = fixed[0].value.args
    if len(args) != 1 or not isinstance(args[0], ast.Constant) or args[0].value != "openai.api_key":
        raise RuntimeError("P156 fixed target changed")
    if "backend.get(" in controller.read_text(encoding="utf8"):
        raise RuntimeError("P156 local controller unexpectedly fetches plaintext")
    print("P156_FIXED_SLOT_AND_SEPARATE_TYPED_UI_CONTRACT=PASS", flush=True)
    return {"four_lazy_methods":lazy, "transitive_read_only_dependency_modules":visited,
            "fixed_slot":"openai.api_key", "controller_explicit_backend_import":True,
            "ui_no_direct_backend_import":True}


IMPORT_PROBE = r"""
import ctypes, importlib, os, socket, subprocess, tkinter
from unittest import mock
def forbidden(*a, **k):
    raise AssertionError("P156 forbidden import-time native or network/process effect")
with (mock.patch.object(ctypes, "WinDLL", side_effect=forbidden),
      mock.patch.object(subprocess, "Popen", side_effect=forbidden),
      mock.patch.object(socket.socket, "connect", side_effect=forbidden),
      mock.patch.object(socket, "create_connection", side_effect=forbidden),
      mock.patch.object(os, "system", side_effect=forbidden),
      mock.patch.object(tkinter, "Tk", side_effect=forbidden)):
    for mod in (
        "nayeon.desktop_alpha.workspace_window",
        "nayeon.brain.pending_custody_observation_boundary",
        "nayeon.brain.pending_custody_status_view",
        "nayeon.brain.local_byok_user_scope",
        "nayeon.desktop_alpha.local_byok_window",
    ):
        importlib.import_module(mod)
print("P156_IMPORT_TIME_NO_PROCESS_NETWORK_TK_ROOT_OR_NATIVE_WINCRED_EFFECT=PASS")
"""


def _run(label, argv, temp, output, *, expect_pass: bool):
    env = os.environ.copy()
    for key in SENSITIVE_ENV:
        env.pop(key, None)
    for key in ("TEMP", "TMP", "TMPDIR"):
        env[key] = str(temp)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    target = output / (label + ".log")
    start = time.monotonic()
    try:
        with target.open("wb") as stream:
            p = subprocess.run(
                argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, timeout=80,
                check=False,
            )
        native_exit = p.returncode
    except subprocess.TimeoutExpired:
        native_exit = 124
    except OSError:
        native_exit = 125
    raw = target.read_bytes() if target.exists() else b""
    text = raw.decode("utf8", "replace").replace("\r\n", "\n")
    matches = COUNTS.findall(text)
    count = int(matches[-1]) if matches else None
    ok_footer = bool(re.search(r"^OK\s*$", text, re.M))
    failed_footer = bool(re.search(r"^FAILED \(", text, re.M))
    passed = (
        native_exit == 0 and
        (ok_footer if label != "import_time_no_effect" else
         "P156_IMPORT_TIME_NO_PROCESS_NETWORK_TK_ROOT_OR_NATIVE_WINCRED_EFFECT=PASS" in text)
    )
    if not expect_pass:
        # The unchanged Phase8.31 original test is meant to remain an honest fail;
        # P156 never changes its assertion or reports it as recovered.
        passed = native_exit == 1 and failed_footer and count == 1
    record = {
        "label":label, "native_exit":native_exit, "unittest_count":count,
        "sha256":hashlib.sha256(raw).hexdigest().upper(),
        "duration_seconds":round(time.monotonic()-start,3),
        "complete_footer":ok_footer or failed_footer,
        "failure_ids":[line for line in text.splitlines() if line.startswith(("FAIL: ","ERROR: "))],
        "expected_disposition_met":passed, "original_historical_failed":not expect_pass,
        "log_file":target.name,
    }
    print("P156_CASE="+label+"|EXIT="+str(native_exit)+"|COUNT="+str(count)
          +"|EXPECTED_MET="+str(passed)+"|SHA256="+record["sha256"], flush=True)
    return record


def main() -> int:
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P156 expected exact isolated hosted branch")
    head = _git("rev-parse", "HEAD")
    if head != os.environ.get("GITHUB_SHA") or _git("merge-base", BASE, "HEAD") != BASE:
        raise RuntimeError("P156 source SHA not descendant of exact P155 checkpoint")
    output = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p156-scope-boundary-evidence"
    output.mkdir(parents=True, exist_ok=True)
    structure = _source_boundary()
    temp = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P156 owned temp unexpectedly exists")
        os.mkdir(temp)
        made = True
        _verify_original_handle_policy(str(temp))
        results = [_run(
            "import_time_no_effect", [sys.executable, "-B", "-c", IMPORT_PROBE],
            temp, output, expect_pass=True
        )]
        for label, module, required in FOCUS:
            results.append(_run(
                label, [sys.executable, "-B", "-m", "unittest", "-v", module],
                temp, output, expect_pass=required
            ))
    finally:
        if made:
            st = temp.lstat()
            if temp.is_symlink() or getattr(st, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("P156 reparse-temp cleanup refused")
            shutil.rmtree(temp)

    result = {
        "checkpoint":"P156", "source_sha":head, "exact_P155_parent":BASE,
        "platform":"REAL_GITHUB_HOSTED_WINDOWS_2025_PYTHON_312",
        "source_boundary":structure, "native_focused_cases":results,
        "historical_8_31_test_modified":False,
        "historic_source_or_security_tests_modified":False,
        "original_phase831_original_test_was_recovered":False,
        "independent_governance_approved":False,
        "independent_security_reviewer_approved":False,
        "full_product_accepted_windows_triads":0,
        "privileged_c1_g0_to_g6":"OPEN",
        "production_release":"HOLD",
    }
    (output / "p156_windows_user_scope_boundary_ledger.json").write_text(
        json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf8"
    )
    print("P156_ORIGINAL_HISTORICAL_SECURITY_TESTS_UNMODIFIED=TRUE", flush=True)
    print("P156_FULL_PRODUCT_WINDOWS_REGRESSIONS_PASSED=0", flush=True)
    print("P156_PRODUCTION_RELEASE=HOLD", flush=True)
    return 0 if len(results)==4 and all(row["expected_disposition_met"] for row in results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
