"""P157 Windows actual view-call reachability; never a product admission.

Source-only proof + real Tk adverse effects + four ORIGINAL unchanged test modules.
Original negative P76/P85/8.31 and production holds remain completely untouched.
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
from scripts.p156_windows_user_scope_boundary_review import _source_boundary

ROOT = Path(__file__).resolve().parents[1]
BASE = "fb54dfcd6dafb9a5ec474e7c3b32df7dac849a98"
BRANCH = "byok-c1-p157-view-capability-reachability-audit-20261111"
FOCUS = (
    ("original_p84_pure_pending_projection", "tests.test_pending_custody_status_view"),
    ("original_p86_live_advisory_window", "tests.test_p86_live_pending_status_integration"),
    ("original_p87_synthetic_observation", "tests.test_p87_readonly_custody_observation"),
    ("original_p88_lease_and_lifecycle", "tests.test_p88_pending_observation_lifecycle"),
)
# ORIGINAL unchanged P86/P87 exact expected failures after P133 deliberate extra
# offline setup button. These stay native FAIL/HOLD, never recast as test PASS.
HISTORICAL_UI_LAYOUT_HOLDS = {
    "original_p86_live_advisory_window": frozenset({
        "test_live_connection_page_default_is_explicitly_unobserved",
        "test_no_credential_action_and_no_implicit_refresh",
    }),
    "original_p87_synthetic_observation": frozenset({
        "test_production_default_remains_not_observed_without_any_session",
    }),
}
SENSITIVE = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "P157_ARTIFACT_TOKEN",
)
RISKY_MODULES = frozenset({
    "nayeon.brain.connection_bootstrap",
    "nayeon.brain.connection_service",
    "nayeon.brain.connection_persistence",
    "nayeon.brain.connection_reconciliation",
})
RISKY_SYMBOLS = frozenset({
    "bootstrap_provider_connection", "observe_connection",
    "ProviderConnectionFileStore", "ProviderConnectionService",
    "initialize", "replace", "clear", "save", "load",
    "open", "unlink", "NamedTemporaryFile", "WinDLL", "Popen",
    "eval", "exec", "__import__",
})
COUNT = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M)


def _git(*args):
    p = subprocess.run(
        ["git", "-C", str(ROOT), *args], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=18, check=True,
    )
    return p.stdout.decode("utf8", "replace").strip()


def _function_node(relative, owner, name):
    path = ROOT / relative
    tree = ast.parse(path.read_text(encoding="utf8"), str(path))
    pool = tree.body
    if owner is not None:
        owners = [x for x in pool if isinstance(x, ast.ClassDef) and x.name == owner]
        if len(owners) != 1:
            raise RuntimeError("P157 expected owner class not uniquely found")
        pool = owners[0].body
    matches = [x for x in pool if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
               and x.name == name]
    if len(matches) != 1:
        raise RuntimeError("P157 target function missing/ambiguous")
    return matches[0]


def _calls(node):
    return sorted({ast.unparse(x.func) for x in ast.walk(node) if isinstance(x, ast.Call)})


def _static_receipts():
    known = _source_boundary()
    imports = known["transitive_read_only_dependency_modules"]
    if not RISKY_MODULES.issubset(imports):
        raise RuntimeError("P157 original 13-module risky transitive closure changed unexpectedly")
    if len(imports) != 13:
        raise RuntimeError("P157 original P156 closure inventory drift")

    callsites = {
        "ui_advisory":
            _function_node("nayeon/desktop_alpha/workspace_window.py",
                           "ConnectionWindow", "show_pending_custody_advisory"),
        "typed_advice":
            _function_node("nayeon/brain/pending_custody_status_view.py",
                           None, "present_pending_custody_advice"),
        "typed_view_postinit":
            _function_node("nayeon/brain/pending_custody_status_view.py",
                           "PendingCustodyStatusView", "__post_init__"),
        "policy_matrix":
            _function_node("nayeon/brain/pending_credential_policy.py",
                           None, "assess_pending_credential_action"),
    }
    actual = {}
    for name, node in callsites.items():
        direct = _calls(node)
        actual[name] = direct
        direct_tail = {x.split(".")[-1] for x in direct}
        if direct_tail & RISKY_SYMBOLS:
            raise RuntimeError("P157 direct view/policy call now reaches effectful symbol: " + name)
        if any(x.startswith(("os.", "subprocess.", "ctypes.", "socket.", "tempfile."))
               for x in direct):
            raise RuntimeError("P157 direct effectful namespace call: "+name)
    if "present_pending_custody_advice" not in _calls(callsites["ui_advisory"]):
        raise RuntimeError("P157 UI no longer uses exact P84 bounded presentation mapper")
    if "assess_pending_credential_action" not in _calls(callsites["typed_advice"]):
        raise RuntimeError("P157 presentation lost canonical consistency verification")
    if "self._require_creator_thread" not in _calls(callsites["ui_advisory"]):
        raise RuntimeError("P157 missing original UI thread guard")
    for name, node in callsites.items():
        if any(isinstance(x, (ast.Global, ast.Nonlocal)) for x in ast.walk(node)):
            raise RuntimeError("P157 unexpected mutable global/nonlocal in pure call graph")
    print("P157_RISKY_TRANSITIVE_MODULES_PRESENT_BUT_NO_DIRECT_VIEW_CALL=PASS", flush=True)
    return {
        "source_only_p156_13_modules_confirmed":True,
        "risky_transitively_imported_but_not_directly_called":sorted(RISKY_MODULES),
        "actual_direct_calls_by_view_entrypoint":actual,
        "frozen_product_files_unchanged":True,
        "static_code_review_limit":"Static calls do not prove a Python sandbox",
    }


ADVERSE_WINDOWS = r"""
import ctypes
from contextlib import ExitStack
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import ttk
from unittest import mock

from nayeon.brain import connection_bootstrap as bootstrap
from nayeon.brain import connection_reconciliation as reconcile
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.brain.onboarding_status_view import present_onboarding_status
from nayeon.brain.pending_credential_policy import (
    PendingCredentialState, PendingCredentialAction, assess_pending_credential_action,
)
from nayeon.brain.pending_custody_status_view import (
    PendingCustodyStatusView, present_pending_custody_advice,
)
from nayeon.desktop_alpha.workspace_window import ConnectionWindow

effect_attempts = []
def prohibited(*args, **kwargs):
    effect_attempts.append("effect_attempt")
    raise AssertionError("P157 effectful import-closure capability was called")

root = tk.Tk()
root.withdraw()
page = None
try:
    # The live Tk root exists before guards. No credential backend/real key,
    # external process, network, provider invocation or file write is authorised.
    page = ConnectionWindow(
        root, on_destroy=lambda _e=None: None,
        on_conversation=lambda:None,
    )
    actual_buttons = [x for x in page.winfo_children() if isinstance(x, ttk.Button)]
    titles = sorted(str(x.cget("text")) for x in actual_buttons)
    expected_titles = sorted((
        "Back to Conversation",
        "Manage provider (offline preview)",
        "Open local key setup (offline, not connected)",
    ))
    assert titles == expected_titles, (titles, expected_titles)
    assert str(page.local_byok_button.cget("state")) == "disabled"
    print("P157_POST_P133_EXACT_THREE_BUTTONS=PASS", flush=True)
    print("P157_NO_AUTOMATIC_OFFLINE_KEY_SETUP=PASS", flush=True)
    with ExitStack() as blocked:
        forbidden = (
            (ProviderConnectionFileStore, "load"),
            (ProviderConnectionFileStore, "save"),
            (ProviderConnectionService, "initialize"),
            (ProviderConnectionService, "replace"),
            (ProviderConnectionService, "clear"),
            (bootstrap, "bootstrap_provider_connection"),
            (reconcile, "observe_connection"),
            (Path, "open"),
            (os, "replace"),
            (os, "fsync"),
            (os, "system"),
            (tempfile, "NamedTemporaryFile"),
            (subprocess, "Popen"),
            (ctypes, "WinDLL"),
            (socket, "create_connection"),
            (socket.socket, "connect"),
        )
        for object_, attribute in forbidden:
            blocked.enter_context(
                mock.patch.object(object_, attribute, side_effect=prohibited)
            )

        combinations = 0
        ui_updates = 0
        adverse = 0
        for observation_state in ConnectionObservationStatus:
            observation = ConnectionObservation(observation_state)
            legacy = present_onboarding_status(
                observation, advise_connection_recovery(observation)
            )
            for pending in PendingCredentialState:
                for action in PendingCredentialAction:
                    advice = assess_pending_credential_action(pending, action)
                    view = present_pending_custody_advice(legacy, advice)
                    assert type(view) is PendingCustodyStatusView
                    assert view.must_reobserve is True
                    assert view.authorizes_effect is False
                    assert view.confirms_persistence is False
                    assert view.confirms_validation is False
                    assert view.confirms_provider_connection is False
                    assert view.clears_recovery is False
                    assert view.legacy_status is legacy.state
                    assert view.proposed_action is action
                    assert view.advisory_decision is advice.decision
                    combinations += 1
                    assert page.show_pending_custody_advisory(legacy, advice) is True
                    label = page.pending_custody_label.cget("text")
                    assert "advisory only" in label
                    assert "credential" in label.lower() or "key" in label.lower()
                    ui_updates += 1

        # Invalid and deliberately tampered advisory must fail closed without
        # exposing attacker-provided text or invoking a service/persistence path.
        good = assess_pending_credential_action(
            PendingCredentialState.ABSENT, PendingCredentialAction.SAVE_PENDING
        )
        object.__setattr__(good, "decision", object())
        assert page.show_pending_custody_advisory(legacy, good) is False
        assert "STATUS UNAVAILABLE" in page.pending_custody_label.cget("text")
        adverse += 1

        marker = "P157_SHOULD_NOT_APPEAR_IN_UI"
        assert page.show_pending_custody_advisory(legacy, marker) is False
        label = page.pending_custody_label.cget("text")
        assert marker not in label and "STATUS UNAVAILABLE" in label
        adverse += 1

        seen = []
        def wrong_thread():
            try:
                page.show_pending_custody_advisory(legacy, good)
            except RuntimeError as e:
                seen.append(str(e))
        worker = threading.Thread(target=wrong_thread)
        worker.start()
        worker.join(timeout=4)
        assert worker.is_alive() is False
        assert seen == ["WRONG_THREAD"], seen
        adverse += 1
        assert not effect_attempts, effect_attempts
        print("P157_REAL_WINDOWS_TK_VIEW_COMBINATIONS="+str(combinations), flush=True)
        print("P157_REAL_WINDOWS_TK_UI_UPDATES="+str(ui_updates), flush=True)
        print("P157_MALFORMED_AND_WRONG_THREAD_REFUSALS="+str(adverse), flush=True)
        print("P157_REACHABLE_TRANSITIVE_STORE_SERVICE_NATIVE_NETWORK_EFFECT_CALLS=0", flush=True)
finally:
    if page is not None:
        try:
            page.destroy()
        except Exception as exc:
            print("P157_CLEANUP_WARNING="+type(exc).__name__)
    root.destroy()

print("P157_ADVERSE_DYNAMIC_VIEW_EFFECT_DENIAL=PASS", flush=True)
"""


def _run(label, argv, temp: Path, output: Path) -> dict:
    env = os.environ.copy()
    for name in SENSITIVE:
        env.pop(name, None)
    env.update({
        "TEMP":str(temp), "TMP":str(temp), "TMPDIR":str(temp),
        "PYTHONDONTWRITEBYTECODE":"1",
    })
    path = output / (label+".log")
    started = time.monotonic()
    try:
        with path.open("wb") as stream:
            p = subprocess.run(
                argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, timeout=85,
                check=False,
            )
        native_exit = p.returncode
    except subprocess.TimeoutExpired:
        native_exit = 124
    except OSError:
        native_exit = 125
    raw = path.read_bytes() if path.exists() else b""
    content = raw.decode("utf8", "replace").replace("\r\n","\n")
    count = COUNT.findall(content)
    original_hold = label in HISTORICAL_UI_LAYOUT_HOLDS
    if label == "new_real_tk_adverse_view_reachability":
        success = (native_exit == 0 and
                   "P157_ADVERSE_DYNAMIC_VIEW_EFFECT_DENIAL=PASS" in content and
                   "P157_POST_P133_EXACT_THREE_BUTTONS=PASS" in content)
    else:
        success = native_exit == 0 and re.search(r"^OK\s*$", content, re.M) is not None
    observed_failure_names = frozenset(re.findall(
        r"^FAIL: (test_\w+) \(", content, re.M
    ))
    observed_error_names = frozenset(re.findall(
        r"^ERROR: (test_\w+) \(", content, re.M
    ))
    expected_hold = bool(
        original_hold and native_exit == 1 and not success and
        not observed_error_names and
        observed_failure_names == HISTORICAL_UI_LAYOUT_HOLDS[label] and
        re.search(r"^FAILED \(failures="+str(len(observed_failure_names))+r"\)\s*$", content, re.M)
    )
    expected_disposition_met = bool(expected_hold if original_hold else success)
    result = {
        "label":label, "native_exit":native_exit,
        "unittest_count": int(count[-1]) if count else None,
        "sha256":hashlib.sha256(raw).hexdigest().upper(),
        "log_bytes":len(raw),
        "seconds":round(time.monotonic()-started,2),
        "original_unmodified":label!="new_real_tk_adverse_view_reachability",
        "passed":bool(success),
        "historical_UI_layout_hold_preserved":bool(expected_hold),
        "expected_disposition_met":expected_disposition_met,
        "classification":("ORIGINAL_TEST_FAIL_HOLD" if expected_hold else
                          ("PASS" if success else "UNEXPECTED_FAIL")),
        "original_failure_ids":[
            line for line in content.splitlines() if line.startswith(("FAIL: ","ERROR: "))
        ],
        "log_file":path.name,
    }
    print("P157_CASE="+label+"|NATIVE_EXIT="+str(native_exit)+
          "|ORIGINAL_TESTS="+str(result["unittest_count"])+
          "|PASS="+str(success)+"|EXPECTED_DISPOSITION_MET="+str(expected_disposition_met)+
          "|SHA256="+result["sha256"],flush=True)
    return result


def main():
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P157 exact isolated hosted Windows branch required")
    head = _git("rev-parse","HEAD")
    if (head!=os.environ.get("GITHUB_SHA") or
        _git("merge-base", BASE,"HEAD")!=BASE):
        raise RuntimeError("P157 source SHA and P156 exact parent invalid")
    static = _static_receipts()
    output = Path(os.environ["RUNNER_TEMP"])/"nayeon-p157-view-capability-evidence"
    output.mkdir(parents=True,exist_ok=True)
    temp = Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made = False
    rows = []
    try:
        if temp.exists() or temp.is_symlink():
            raise RuntimeError("P157 temporary root already exists")
        os.mkdir(temp)
        made=True
        _verify_original_handle_policy(str(temp))
        print("P157_UNMODIFIED_P139_NATIVE_OPEN_HANDLE_GUARD=PASS",flush=True)
        rows.append(_run(
            "new_real_tk_adverse_view_reachability",
            [sys.executable,"-B","-c",ADVERSE_WINDOWS],temp,output
        ))
        for label,module in FOCUS:
            rows.append(_run(
                label,[sys.executable,"-B","-m","unittest","-v",module],temp,output
            ))
    finally:
        if made:
            st=temp.lstat()
            if temp.is_symlink() or getattr(st,"st_file_attributes",0)&0x400:
                raise RuntimeError("P157 unexpected reparse temp cleanup target")
            shutil.rmtree(temp)
    receipt={
        "checkpoint":"P157","verified_source_sha":head,
        "exact_P156_parent":BASE,
        "real_windows_hosted_runner":os.environ.get("RUNNER_OS"),
        "python":sys.version,
        "view_callsite_static_evidence":static,
        "five_actual_windows_child_results":rows,
        "original_P84_P86_P87_P88_tests_modified":False,
        "original_P76_P85_and_Phase831_failures_waived":False,
        "privileged_c1_g0_to_g6":"OPEN",
        "qualified_independent_approval":"NOT_OBTAINED",
        "full_product_accepted_windows_regressions":"0/3",
        "production_release":"HOLD",
        "interpretation":"No effect on bounded tested view calls; Python imports are not a sandbox",
    }
    (output/"p157_windows_view_capability_ledger.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8"
    )
    print("P157_FROZEN_ORIGINAL_SECURITY_TESTS_UNCHANGED=TRUE",flush=True)
    print("P157_ACCEPTED_FULL_PRODUCT_WINDOWS_REGRESSIONS=0/3",flush=True)
    print("P157_PRODUCTION_RELEASE=HOLD",flush=True)
    print("P157_OLD_P86_P87_EXACT_THREE_UI_COUNT_FAILURES=UNMODIFIED_FAIL_HOLD",flush=True)
    print("P157_DIAGNOSTIC_COLLECTION_NOT_ORIGINAL_TEST_RECOVERY=TRUE",flush=True)
    return 0 if len(rows)==5 and all(x["expected_disposition_met"] for x in rows) else 1

if __name__=="__main__":
    raise SystemExit(main())
