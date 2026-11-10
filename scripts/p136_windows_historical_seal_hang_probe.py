"""P136: bounded, read-only DIAGNOSIS of the exact P135 Windows stall.

No original test or production file is edited. We execute ONE previously
stalled historical BYOK-B integrity test with Python faulthandler stack dumps
at 10/20/30 seconds and stop after 42 seconds. This investigates time spent
in frozen historical fixture replay without treating a timeout as PASS.

Only GitHub-hosted ephemeral Windows and no real credential / provider calls.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

TARGET = (
    "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests."
    "test_missing_or_zero_candidate_pin_and_live_a_adapter_tamper_refused"
)
EMBEDDED = (
    "import faulthandler,sys,unittest; "
    "faulthandler.enable(); "
    "faulthandler.dump_traceback_later(10,repeat=True,file=sys.stderr); "
    "suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[1]); "
    "result=unittest.TextTestRunner(verbosity=2).run(suite); "
    "faulthandler.cancel_dump_traceback_later(); "
    "sys.exit(0 if result.wasSuccessful() and result.testsRun==1 else 1)"
)

def main() -> int:
    if not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Windows"
        and os.environ.get("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
        and os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("RUNNER_TEMP")
    ):
        print("P136_EPHEMERAL_WINDOWS_DIAGNOSTIC=REFUSED")
        return 4

    root = Path(__file__).resolve().parents[1]
    dest = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p136-hang-diagnostic"
    dest.mkdir(parents=True, exist_ok=True)
    log = dest / "p136_single_frozen_historical_test_stack.log"
    command = [sys.executable,"-B","-c",EMBEDDED,TARGET]
    print("P136_SINGLE_EXACT_HISTORICAL_TEST="+TARGET,flush=True)
    print("P136_OLD_TEST_CODE=FROZEN_UNMODIFIED",flush=True)
    print("P136_FAULTHANDLER_INTERVAL_SECONDS=10",flush=True)
    print("P136_NO_TEST_FILTER_OR_SECURITY_EXPECTATION_WEAKENING=TRUE",flush=True)

    timed_out=False
    try:
        with log.open("wb") as out:
            process = subprocess.run(
                command,cwd=root,stdout=out,stderr=subprocess.STDOUT,
                timeout=42,check=False,
            )
        code=process.returncode
    except subprocess.TimeoutExpired:
        code=124
        timed_out=True
    except OSError:
        code=125

    raw=log.read_bytes() if log.exists() else b""
    text=raw.decode("utf8","replace")
    digest=hashlib.sha256(raw).hexdigest().upper()
    stack_dumps=text.count("Timeout (0:00:10)!")
    print("P136_SINGLE_TEST_NATIVE_EXIT="+str(code),flush=True)
    print("P136_SINGLE_TEST_TIMED_OUT="+str(timed_out).upper(),flush=True)
    print("P136_TRACEBACK_10S_STACK_DUMPS="+str(stack_dumps),flush=True)
    print("P136_SINGLE_TEST_EVIDENCE_SHA256="+digest,flush=True)
    print("P136_SINGLE_TEST_LOG_BYTES="+str(len(raw)),flush=True)

    # Only emit NONSECRET Python stack frames from the test. No assertions,
    # credentials or arbitrary error text should leave the raw CI artifact.
    frames=[
        line.strip()
        for line in text.splitlines()
        if 'File "' in line and
        ('\\tests\\' in line.lower() or
         '/tests/' in line.lower() or
         '/subprocess.py' in line.lower() or
         '\\subprocess.py' in line.lower())
    ]
    print("P136_DIAGNOSTIC_STACK_FRAME_LINES="+str(len(frames)),flush=True)
    for item in frames[-16:]:
        print("P136_DIAGNOSTIC_STACK_FRAME="+item[:240],flush=True)

    if code==0:
        print("P136_SINGLE_HISTORICAL_TEST=PASS_STANDALONE_NOT_FULL_SUITE",flush=True)
    elif code==124:
        print("P136_SINGLE_HISTORICAL_TEST=TIMEOUT_UNRESOLVED",flush=True)
    else:
        print("P136_SINGLE_HISTORICAL_TEST=FAILED_OR_REFUSED",flush=True)
    print("P136_THREE_COMPLETE_PRODUCT_REGRESSIONS=NOT_PASSED",flush=True)
    print("P136_C1_USER_SCOPE_RELEASE=HOLD",flush=True)
    # A successful diagnostic is never a positive product-release test.
    # Retain raw evidence even if the single test fails or stalls.
    return 0 if len(raw)>0 else 1

if __name__=="__main__":
    raise SystemExit(main())
