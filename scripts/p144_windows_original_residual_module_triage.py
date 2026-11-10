"""P144: bounded re-run of 15 original P142 failing modules on verified Windows C: root.

DIAGNOSTIC ONLY. Do not alter old tests or product security code. A green
collection job means every original module has an authentic disposition,
NOT a passing full-product regression or security-release approval.
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
    _guard_runner,
    _verify_original_handle_policy,
)

P143_EXACT_HEAD = "3e4075afa119b7cecf14dc349ac620661cb36403"
ORIGINAL_P142_HOLDS_NOT_IN_P143 = (
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
EXPECTED_MODULES = 15
MAX_MODULE_SECONDS = 80
WORKERS = 3
COUNT = re.compile(r"Ran (\d+) tests? in [\d.]+s")
SECRET_ENV = {
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
}


def _run_original(module: str, repo: Path, fixture: Path, evidence: Path) -> dict:
    path = evidence / ("p144_" + module.replace(".", "_") + ".log")
    env = os.environ.copy()
    for key in SECRET_ENV:
        env.pop(key, None)
    for key in ("TMPDIR", "TEMP", "TMP"):
        env[key] = str(fixture)
    start = time.monotonic()
    try:
        with path.open("wb") as output:
            proc = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "-v", module],
                cwd=repo, env=env, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT,
                timeout=MAX_MODULE_SECONDS, check=False,
            )
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = 124
    except OSError:
        code = 125
    raw = path.read_bytes() if path.exists() else b""
    lines = raw.decode("utf-8", "replace").splitlines()
    counts = [int(match.group(1)) for line in lines
              if (match := COUNT.search(line))]
    error_names = [line.split(":", 1)[1].strip().split(" (", 1)[0]
                   for line in lines if line.startswith(("FAIL: ", "ERROR: "))]
    footer = [line for line in lines if line.startswith("FAILED (")]
    ok = (code == 0 and bool(counts) and
          any(line.strip() == "OK" for line in lines) and
          not error_names and not footer)
    status = "PASS" if ok else "TIMEOUT" if code == 124 else "HOLD"
    result = {
        "module": module,
        "native_exit": code,
        "completed_unittest_count": counts[-1] if counts else None,
        "status": status,
        "failure_ids": error_names,
        "failed_footer": footer[-1] if footer else None,
        "duration_seconds": round(time.monotonic() - start, 3),
        "log_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "log_bytes": len(raw),
    }
    print("P144_ORIGINAL_MODULE=" + module +
          "|STATUS=" + status + "|EXIT=" + str(code) +
          "|COUNT=" + str(result["completed_unittest_count"]) +
          "|FAILURE_IDS=" + str(len(error_names)) +
          "|SHA256=" + result["log_sha256"], flush=True)
    return result


def main() -> int:
    _guard_runner()
    if (os.environ.get("GITHUB_REF_NAME") !=
            "byok-c1-p144-original-windows-residual-holds-20261110"):
        raise RuntimeError("P144 hosted Windows branch identity required")
    if len(ORIGINAL_P142_HOLDS_NOT_IN_P143) != EXPECTED_MODULES:
        raise RuntimeError("Original P142 residual inventory drift")
    if len(set(ORIGINAL_P142_HOLDS_NOT_IN_P143)) != EXPECTED_MODULES:
        raise RuntimeError("Duplicate original test module")
    repo = Path(__file__).resolve().parents[1]
    for mod in ORIGINAL_P142_HOLDS_NOT_IN_P143:
        if not (repo / (mod.replace(".", "/") + ".py")).is_file():
            raise RuntimeError("Missing historical test module: " + mod)
    evidence = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p144-original-residual-evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    fixture = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    created = False
    results: list[dict] = []
    try:
        if fixture.exists() or fixture.is_symlink():
            raise RuntimeError("Random fixed-root temp path unexpectedly exists")
        os.mkdir(fixture)
        created = True
        _verify_original_handle_policy(str(fixture))
        print("P144_UNCHANGED_WIN32_HANDLE_POLICY=PASS", flush=True)
        print("P144_FULL_ORIGINAL_MODULE_METHODS_UNFILTERED=TRUE", flush=True)
        print("P144_HISTORICAL_SOURCE_AND_ASSERTIONS=UNCHANGED", flush=True)
        print("P144_REAL_KEYS_AND_PRODUCTION_CREDENTIAL_EFFECTS=FORBIDDEN", flush=True)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = {
                executor.submit(_run_original, mod, repo, fixture, evidence): mod
                for mod in ORIGINAL_P142_HOLDS_NOT_IN_P143
            }
            for future in as_completed(futures):
                mod = futures[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append({
                        "module": mod, "native_exit": 125, "status": "HOLD",
                        "completed_unittest_count": None,
                        "failure_ids": [],
                        "failed_footer": "Runner error: " + type(exc).__name__,
                        "duration_seconds": None, "log_sha256": None,
                        "log_bytes": 0,
                    })
                    print("P144_MODULE_RUNNER_EXCEPTION=" + mod +
                          ":" + type(exc).__name__, flush=True)
        results.sort(key=lambda r: r["module"])
        counts = {s: sum(r["status"] == s for r in results)
                  for s in ("PASS", "HOLD", "TIMEOUT")}
        manifest = {
            "exact_base_commit": P143_EXACT_HEAD,
            "release_approved": False,
            "diagnostic_only": True,
            "verified_original_opened_handle_temp_root": True,
            "original_historical_assertions_modified": False,
            "original_p142_holds_in_scope": EXPECTED_MODULES,
            "outstanding_p142_separate_timeouts": 9,
            "results": results,
            "summary": counts,
        }
        (evidence / "p144_original_residual_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        print("P144_COMPLETED_MODULE_ROWS=" + str(len(results)), flush=True)
        for key, value in counts.items():
            print("P144_MODULES_" + key + "=" + str(value), flush=True)
        print("P144_P135_THREE_FULL_UNFILTERED_REGRESSIONS=NOT_PASSED", flush=True)
        print("P144_INDEPENDENT_GOVERNANCE_AND_SIGNED_RELEASE=HOLD", flush=True)
        print("P144_BYOK_C1_USER_SCOPE_RELEASE=HOLD", flush=True)
        # Collection success is not test acceptance; all HOLD rows remain HOLD.
        return 0 if len(results) == EXPECTED_MODULES else 1
    finally:
        if created:
            try:
                st = fixture.lstat()
                if (not fixture.is_symlink() and
                        not (getattr(st, "st_file_attributes", 0) & 0x400) and
                        str(fixture).startswith("C:\\NayeonP139_")):
                    shutil.rmtree(fixture)
                    print("P144_EPHEMERAL_TEST_ROOT_CLEANUP=ATTEMPTED", flush=True)
                else:
                    print("P144_UNEXPECTED_FIXTURE_REPARSE_CLEANUP_REFUSED", flush=True)
            except Exception:
                print("P144_FIXTURE_CLEANUP_UNCERTAIN_HOSTED_RUNNER", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
