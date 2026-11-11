"""P159: six genuinely uncompleted P142 scope-test modules, longer native Windows runs.

These are original historical test modules, invoked unchanged and unfiltered.
A green *collector* records their authentic PASS/HOLD/TIMEOUT; it cannot
classify failures as passes or declare full-product production admission.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
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

BASE = "cb8c1980346ec7d36d7a5de6e764204cf9c2f30b"
BRANCH = "byok-c1-p159-windows-six-scope-timeout-recovery-20261111"
ROOT = Path(__file__).resolve().parents[1]
P154_LEDGER_ARTIFACT = 13860513004
P142_EVIDENCE_ARTIFACT = 13787854664
EXPECTED_CURRENT_TRACKED_TEST_MODULES = 170   # Original P154 169 + new P158 successor.
MAX_MODULE_SECONDS = 110
MAX_WORKERS = 3
# Fully authenticated P154 original 169-module ledger, sourced from P142 real
# GitHub Windows original 35-sec TIMEOUTs. Reject any source drift.
ORIGINAL = (
    ("tests.test_phase_830_scope_integrity",
     "433A34A48AF83DE3353B2F08ED9EC6B710806E01EC0BE096B082ABD6272C946F",
     "C5B702DE353015E2C97DB53BDFFCDBD19EDF9DBC4F43DD388E588BC5B934916B"),
    ("tests.test_phase_831_scope_integrity",
     "41E23E31D06F699129BD274A29DE103A1917C7E1754B3B0EDDA9658BE15AD20C",
     "18EC84F749BEAAA1F33357B72ACBABCD99F708A4F7C285111AAFCC0CA049D8E5"),
    ("tests.test_phase_832_scope_integrity",
     "0A25F898CCB374B63B6CD68B0A3488C6F0D8656EC6EA6BAE1FD225CABCF9A689",
     "5C13E44C5AB662AB0F6FAFF0079B12EA387F726676D966FE8C1A0998856EB74E"),
    ("tests.test_phase_833_scope_integrity",
     "8BDEECC1D14FFDCFFA2B05B7E3E7409B00E0F211DB5810FEFB9EC96865A7531D",
     "209190AB8E220456B4C51FAEEAC9C95CF1760FC1E9A8B432387C064DE1BB8CEB"),
    ("tests.test_phase_834_scope_integrity",
     "8DC69EC770EA008DFF9CD13E15299A73E38044F1671FD4FE78FBE2A431CCF57A",
     "B0E52AB6100EEFBB023A2BF5F26CE8A13F476AEE6EDA43932D955D056E65D2C5"),
    ("tests.test_phase_837_scope_integrity",
     "A95A967BA892FECADF0811B38C51AE61CD268159766A91B1DC448CF4B1B5C426",
     "D3C241A55047561DABDC94797EAB118BB024BFF22EB02B0E9DA2D4D244830B95"),
)
ENV_TO_REMOVE = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "NAYEON_INTERNAL_SECRET",
    "P159_DOWNLOAD_TOKEN",
)
RAN = re.compile(r"^Ran (\d+) tests? in [0-9.]+s$", re.M)
OK = re.compile(r"^OK(?:\s*)$", re.M)
FAILED = re.compile(r"^FAILED \(([^)]+)\)(?:\s*)$", re.M)
FAILURE_HEAD = re.compile(r"^(FAIL|ERROR): (.+?)(?:\s*\(.*)?$", re.M)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=25, check=True,
    )
    return result.stdout.decode("utf8", "replace").strip()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _verify_original_source():
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P159 exact hosted Windows branch expected")
    if os.environ.get("RUNNER_OS") != "Windows" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("P159 actual GitHub Windows only")
    source_sha = _git("rev-parse", "HEAD")
    if source_sha != os.environ.get("GITHUB_SHA") or _git("merge-base",BASE,"HEAD") != BASE:
        raise RuntimeError("P159 exact P158 ancestry or HEAD mismatch")
    inventory = [
        line for line in _git("ls-files", "tests/test_*.py").splitlines()
        if line.startswith("tests/test_") and line.endswith(".py")
    ]
    if len(inventory) != EXPECTED_CURRENT_TRACKED_TEST_MODULES:
        raise RuntimeError("P159 current inventory drift: " + str(len(inventory)))
    if "tests/test_p158_versioned_connection_ui_contract.py" not in inventory:
        raise RuntimeError("P159 expected P158 positive successor missing")
    for module,source_hash,p142_log in ORIGINAL:
        path = "tests/"+module.split(".")[-1]+".py"
        raw = (ROOT/path).read_bytes()
        if _sha(raw)!=source_hash:
            raise RuntimeError("P159 historical P154 source SHA drift: "+module)
        if _git("rev-parse","HEAD:"+path)!=_git("rev-parse",BASE+":"+path):
            raise RuntimeError("P159 old test blob was altered: "+module)
        if len(p142_log)!=64:
            raise RuntimeError("P159 original evidence digest missing")
    if _git("status","--porcelain=v1"):
        raise RuntimeError("P159 source not clean")
    print("P159_EXACT_P158_SOURCE_AND_170_MODULE_INVENTORY=PASS",flush=True)
    print("P159_SIX_ORIGINAL_P154_SOURCE_SHA256_PINS=PASS",flush=True)
    return source_sha


def _run(row, *, temp: Path, out: Path):
    module,source_sha,p142_sha = row
    name = module.removeprefix("tests.")
    child_dir = temp/name
    child_dir.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for k in ENV_TO_REMOVE:
        env.pop(k,None)
    env.update({
        "TEMP":str(child_dir),"TMP":str(child_dir),"TMPDIR":str(child_dir),
        "PYTHONDONTWRITEBYTECODE":"1",
    })
    log_path = out/(name+".log")
    cmd = [sys.executable,"-B","-m","unittest","-v",module]
    start=time.monotonic()
    native_exit = None
    timeout_reached=False
    try:
        with log_path.open("wb") as stream:
            process = subprocess.Popen(
                cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            try:
                native_exit=process.wait(timeout=MAX_MODULE_SECONDS)
            except subprocess.TimeoutExpired:
                timeout_reached=True
                native_exit=124
                # The entire tree (including nested read-only git.exe children)
                # exists only on disposable GitHub-hosted Windows and is explicitly
                # terminated at this verified per-module cap. Never do this on Kristian.
                subprocess.run(
                    ["taskkill","/PID",str(process.pid),"/T","/F"],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,timeout=15,check=False,
                )
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=4)
    except (OSError, subprocess.TimeoutExpired) as exc:
        native_exit = 125
        with log_path.open("ab") as stream:
            stream.write(("\nP159_DIAGNOSTIC_PROCESS_ERROR_TYPE="+type(exc).__name__+"\n").encode())
    raw = log_path.read_bytes() if log_path.exists() else b""
    text=raw.decode("utf8","replace").replace("\r\n","\n")
    count_list=RAN.findall(text)
    actual_count=int(count_list[-1]) if count_list else None
    failed=FAILED.findall(text)
    complete=actual_count is not None and (bool(OK.search(text)) or bool(failed))
    errors=[{"kind":kind,"original_test":name} for kind,name in FAILURE_HEAD.findall(text)]
    if native_exit==0 and complete and bool(OK.search(text)) and not errors:
        state="PASS"
    elif native_exit==124 and timeout_reached:
        state="TIMEOUT"
    else:
        state="HOLD"
    result={
        "module":module, "source_sha256":source_sha,
        "p142_original_35s_status":"TIMEOUT",
        "p142_original_log_sha256":p142_sha,
        "p142_original_evidence_artifact_id":P142_EVIDENCE_ARTIFACT,
        "real_windows_timeout_limit_seconds":MAX_MODULE_SECONDS,
        "native_exit":native_exit,
        "elapsed_seconds":round(time.monotonic()-start,3),
        "actual_unittest_count":actual_count,
        "complete_unittest_footer":bool(complete),
        "failed_footer":failed[-1] if failed else None,
        "original_failure_error_records":errors,
        "log_sha256":_sha(raw),"log_bytes":len(raw),
        "raw_log_name":log_path.name,"disposition":state,
        "original_source_unmodified":True,
    }
    print(
        "P159_MODULE="+module+"|NATIVE_EXIT="+str(native_exit)+
        "|UNFILTERED_COUNT="+str(actual_count)+
        "|OUTCOME="+state+"|SECONDS="+str(result["elapsed_seconds"])+
        "|LOG_SHA256="+result["log_sha256"],flush=True
    )
    return result


def main():
    _guard_runner()
    head=_verify_original_source()
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p159-six-original-scope-timeout-recovery"
    out.mkdir(parents=True,exist_ok=True)
    root=Path("C:\\NayeonP139_"+uuid.uuid4().hex)
    made=False
    rows=[]
    try:
        if root.exists() or root.is_symlink():
            raise RuntimeError("P159 temp root preexisted")
        os.mkdir(root)
        made=True
        _verify_original_handle_policy(str(root))
        print("P159_P139_ORIGINAL_OPENED_NATIVE_HANDLE_LOCAL_TEMP_POLICY=PASS",flush=True)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            work={pool.submit(_run,entry,temp=root,out=out):entry[0] for entry in ORIGINAL}
            for done in as_completed(work):
                rows.append(done.result())
    finally:
        if made:
            stat=root.lstat()
            if root.is_symlink() or getattr(stat,"st_file_attributes",0)&0x400:
                raise RuntimeError("P159 unsafe cleanup target; fail closed")
            shutil.rmtree(root)
    expected={r[0] for r in ORIGINAL}
    seen={r["module"] for r in rows}
    if len(rows)!=len(ORIGINAL) or seen!=expected:
        raise RuntimeError("P159 partial or duplicate module outcome")
    if _git("status","--porcelain=v1"):
        raise RuntimeError("P159 historical product tree mutated during tests")
    counts={k:sum(r["disposition"]==k for r in rows) for k in ("PASS","HOLD","TIMEOUT")}
    summary={
        "checkpoint":"P159","exact_source_head":head,
        "exact_P158_parent":BASE,
        "current_tracked_module_inventory":EXPECTED_CURRENT_TRACKED_TEST_MODULES,
        "p154_original_unfiltered_inventory":169,
        "p154_source_artifact_id":P154_LEDGER_ARTIFACT,
        "p142_original_evidence_artifact_id":P142_EVIDENCE_ARTIFACT,
        "original_35s_timeout_modules":6,
        "longer_focused_module_cap_seconds":MAX_MODULE_SECONDS,
        "test_module_dispositions":sorted(rows,key=lambda r:r["module"]),
        "summary":counts,
        "original_historical_test_code_modified":False,
        "historical_security_test_failure_waivers":False,
        "original_P135_complete_full_product_windows_passes":0,
        "original_P150_historic_BYOK_190s_timeout":"OPEN",
        "qualified_independent_security_governance_review":"NOT_OBTAINED",
        "three_accepted_complete_full_product_regressions":"0/3",
        "privileged_BYOK_C1_G0_to_G6":"OPEN",
        "production_release":"HOLD",
        "collector_success_is_not_full_product_regression_pass":True,
    }
    (out/"p159_six_windows_scope_module_recovery_ledger.json").write_text(
        json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf8"
    )
    print("P159_REAL_ORIGINAL_DISPOSITIONS="+json.dumps(counts,sort_keys=True),flush=True)
    print("P159_FROZEN_HISTORICAL_SECURITY_NEGATIVES=UNWAIVED",flush=True)
    print("P159_FULL_PRODUCT_ACCEPTED_WINDOWS_TRIAD=0/3",flush=True)
    print("P159_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
