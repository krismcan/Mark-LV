"""P206 authentic Windows SHA-bound original Python/native effect-entry evidence.

No real provider key, no WinCred API invocation, no service startup, no signing
policy changes, no full-product regression acceptance, no admission grants.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
P205 = "94b8b457cc99c111bf444d89529ddcb861af7fd9"
BRANCH = "byok-c1-p206-unified-credential-effect-ownership-20261114"
ADDED = {
    "nayeon/brain/p206_legacy_effect_hold_candidate.py",
    "tests/test_p206_unified_effect_ownership.py",
    "scripts/p206_windows_credential_effect_ownership.py",
    "docs/byok-c1-p206-unified-effect-ownership-review.md",
    ".github/workflows/p206-windows-unified-effect-ownership.yml",
}
PRIOR_BLOBS = {
    "nayeon/secrets/windows_credential.py": "ac061e629539a070ff9a67417dc5176812f4e368",
    "nayeon/secrets/lifecycle.py": "106d443e500fc1db2f3599d6ec64dfb027f31837",
    "nayeon/brain/credential_operation_host.py": "cbb18036bace4e83d12908250977583b88d96489",
    "nayeon/brain/onboarding_coordination.py": "b97e9d710bfd9cc7a31d8ec97525b9449700c228",
    "nayeon/brain/credential_onboarding_composition.py": "f69ad6704f939cc5ae494e67b6b8ad1c43f61c64",
    "nayeon/desktop_alpha/first_run_credential_management_window.py": "66bce8c57ff86a5a99d96707e335db1d9170ab73",
    "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs": "daa927f714f07177a0d18b8ef9fb0cdb87e2f53d",
    "native_c1_candidate/CandidateCredentialEffectHold.cs": "4af8a6f1d6a35dc7f8df6968b478ab7c4db8f6fa",
}


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError("Git source-custody command returned nonzero")
    return proc.stdout.decode("utf-8", errors="strict").strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def custody() -> dict:
    if (sys.platform != "win32" or
            os.environ.get("GITHUB_ACTIONS") != "true" or
            os.environ.get("RUNNER_OS") != "Windows" or
            os.environ.get("GITHUB_EVENT_NAME") != "push" or
            os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV" or
            os.environ.get("GITHUB_REF_NAME") != BRANCH):
        raise RuntimeError("P206 requires actual hosted Windows push event")
    head = git("rev-parse", "HEAD")
    if head != os.environ.get("GITHUB_SHA"):
        raise RuntimeError("P206 source HEAD mismatches actual event")
    if git("merge-base", P205, "HEAD") != P205:
        raise RuntimeError("P206 exact P205 ancestor missing")
    if set(git("diff", "--name-only", P205, "HEAD").splitlines()) != ADDED:
        raise RuntimeError("P206 changed original production or frozen source")
    if git("status", "--porcelain=v1", "-uall"):
        raise RuntimeError("P206 working checkout modified")
    originals = {}
    for path, expected in PRIOR_BLOBS.items():
        actual = git("rev-parse", "HEAD:" + path)
        if actual != expected:
            raise RuntimeError("P206 original source blob changed " + path)
        originals[path] = {
            "git_blob": actual,
            "disk_SHA256": sha256((ROOT / path).read_bytes()),
        }
    return {"HEAD": head, "P205_ancestor": P205,
            "only_five_additive_paths": sorted(ADDED),
            "original_file_custody": originals,
            "clean": True}


def run_suite(label: str, args: list[str], target: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # No provider secrets are provided to test executables.
    for key in list(env):
        if key in ("GH_TOKEN", "GITHUB_TOKEN") or key.endswith(
                ("_API_KEY", "_SECRET", "_TOKEN")):
            env.pop(key, None)
    with target.open("wb") as output:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "-v", *args],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=output,
            stderr=subprocess.STDOUT, timeout=180, check=False,
        )
    raw = target.read_bytes()
    txt = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    footer = re.findall(r"^Ran (\d+) tests? in [0-9.]+s$", txt, re.M)
    accepted = result.returncode == 0 and bool(re.search(r"^OK\s*$", txt, re.M))
    return {"log": target.name, "SHA256": sha256(raw),
            "actual_Windows_OS_exit": result.returncode,
            "test_footer": footer, "complete_OK": accepted,
            "markers": re.findall(r"^P20[56]_[^\r\n]+", txt, re.M)}


def main() -> int:
    out = Path(os.environ.get("RUNNER_TEMP", str(ROOT))) / "nayeon-p206-effect-ownership"
    out.mkdir(parents=True, exist_ok=True)
    evidence = {
        "checkpoint": "P206",
        "H": "HOLD_LEGACY_DIRECT_EFFECT_BYPASS_RISK_OPEN",
        "C": "ISOLATED_DORMANT_FAIL_CLOSED_CANDIDATE",
        "R": "PRODUCTION_HOLD",
        "real_key_R0_R4": "NO_GO",
        "independent_GOV_SEC_REL": "OPEN",
        "full_unfiltered_Windows_product_regressions_accepted": "0/3",
        "legacy_Python_WinCred_direct_mutation": "EXISTS_NOT_SERVICE_GOVERNED",
        "native_service_admission": "DENIAL_ONLY_NO_EFFECT",
        "qualified_review": "NOT_YET_APPROVED",
    }
    ok = False
    try:
        before = custody()
        evidence["source_before"] = before
        python = run_suite(
            "P206_original_Python_and_dormant_hold",
            ["discover", "-s", "tests", "-p",
             "test_p206_unified_effect_ownership.py"],
            out / "p206_windows_original_Python_12.log",
        )
        evidence["Python"] = python
        if (not python["complete_OK"] or python["test_footer"] != ["12"]):
            raise RuntimeError("P206 original Python fake-adapter/hold tests failed")
        native = run_suite(
            "P206_original_P49_and_current_C1",
            [
                "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_02_original_full_P49_native_release_and_WinCred_denial_20_cases",
                "scripts.p205_windows_realkey_production_gate_evidence.P205NativeRealKeyAndReleaseGates.test_03_current_candidate_service_host_remains_denial_24_cases",
            ],
            out / "p206_windows_native_P49_C1_2.log",
        )
        evidence["native"] = native
        if (not native["complete_OK"] or native["test_footer"] != ["2"] or
            not any("ACTUAL_WINDOWS_NATIVE_CASES=20_OS_EXIT_0" in x for x in native["markers"]) or
            not any("ACTUAL_WINDOWS_NATIVE_CASES=24_OS_EXIT_0" in x for x in native["markers"])):
            raise RuntimeError("P206 actual native P49/C1 executable denial evidence failed")
        for label in ("p205_original_P49_20", "p205_candidate_C1_host_24"):
            logs = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p205-key-gates"
            compiler = logs / (label + "_compiler.log")
            original = logs / (label + "_native.log")
            if not compiler.is_file() or not original.is_file():
                raise RuntimeError("P206 native original compiler/executable log missing")
            evidence[label] = {
                "compiler_SHA256": sha256(compiler.read_bytes()),
                "native_execution_SHA256": sha256(original.read_bytes()),
                "actual_compiler_OS_exit": 0,
            }
        after = custody()
        evidence["source_after"] = after
        if before != after:
            raise RuntimeError("P206 original Git source custody changed during Windows tests")
        ok = True
        print("P206_ORIGINAL_PYTHON_SYNTHETIC=12_PASS", flush=True)
        print("P206_ORIGINAL_P49_20_AND_CURRENT_NATIVE_C1_24=44_PASS", flush=True)
        print("P206_LEGACY_EFFECT_BYPASS=CONFIRMED_FAKE_ONLY_PRODUCTION_RISK_OPEN", flush=True)
        print("P206_REALKEY=NO_GO|PRODUCTION=HOLD|FULL_PRODUCT_WINDOWS=0/3", flush=True)
    except BaseException as exc:
        evidence["failure"] = type(exc).__name__ + ": " + str(exc)
        print("P206_WINDOWS_EVIDENCE_HOLD=" + type(exc).__name__, flush=True)
    finally:
        evidence["isolated_P206_complete_NOT_release"] = ok
        (out / "p206_HCR_original_source_ledger.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
