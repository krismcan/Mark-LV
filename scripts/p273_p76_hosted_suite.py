"""Disposable Windows-only runner; raw streams and complete source brackets.

Receipts are exclusive, outside the checkout. No original expensive methods
are rerun. Their four FAIL anchors come from the authenticated P252 report.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

from scripts import p273_p76_current_admission as candidate
from scripts import p245_p76_current_source as source

TEST_MODULE = "tests.test_p273_p76_current_admission"
TEST_COUNT = 11


def qualifies(receipt: dict, before: dict | None, after: dict | None) -> bool:
    """Receipt conjunction only; source witnesses come from the actual callable."""
    return (before is not None and after is not None
            and before.get("result") == "AUTHENTICATED_CURRENT_SOURCE_EVIDENCE"
            and before.get("complete_scans") == 2
            and before.get("historical_parent_count") == candidate.PARENT_COUNT
            and len(before.get("complete_source", {}).get("disk", {})) == candidate.PARENT_COUNT + len(candidate.ADDED)
            and candidate.canonical(before) == candidate.canonical(after)
            and receipt.get("native_exit") == 0 and receipt.get("timeout") is False
            and receipt.get("process_reaped") is True and receipt.get("unittest_complete") is True
            and receipt.get("expected_tests") == TEST_COUNT
            and receipt.get("before_attempted") is True and receipt.get("after_attempted") is True
            and "error_type" not in receipt and "after_error_type" not in receipt)


def save(path: Path, value: dict) -> None:
    with path.open("xb") as stream:
        stream.write(candidate.canonical(value) + b"\n")


def stream_receipt(path: Path) -> dict:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": digest}


def run(output: Path) -> int:
    candidate.require_domain(source.ROOT, hosted=True)
    bits = struct.calcsize("P") * 8
    expected_arch = os.environ.get("P273_ARCH")
    if (expected_arch, bits) not in {("x64", 64), ("x86", 32)}:
        candidate.refuse("Python architecture differs from hosted matrix")
    output = output.absolute()
    # Check the existing parent before exclusive directory creation.
    source.checked_node(output.parent)
    if output == source.ROOT or source.ROOT in output.parents:
        candidate.refuse("evidence directory must be outside checkout")
    output.mkdir(exist_ok=False)
    source.checked_node(output)
    receipt = {"schema": "P273-HOSTED-SUITE-V1", "source_candidate_tests_pass": False,
               "python": sys.version, "executable": sys.executable, "bits": bits,
               "native_exit": None, "timeout": False, "before_attempted": False,
               "after_attempted": False, "process_reaped": False,
               "original_four_FAIL": "UNWAIVED; anchored P252 evidence, not rerun",
               "P76_governance": "HOLD", "P96_production": "HOLD",
               "real_keys": "NO-GO", "full_product_accepted_native_regressions": "0/3"}
    before = after = child = None
    try:
        receipt["before_attempted"] = True
        before = candidate.prove_authenticated_current_source(source.ROOT)
        save(output / "before-source.json", before)
        # Anchor every original FAIL hash and exact method ID in actual,
        # parent-preserved P252 bytes, rather than a freely invented receipt.
        report, _ = source.raw_source("docs/byok-c1-p252-original-p76-current-native-reconciliation.md")
        for anchor in candidate.ORIGINAL_FAIL_STDERR:
            if anchor.encode() not in report:
                candidate.refuse("P252 original FAIL anchor absent")
        for method in source.ORIGINAL_FAILURE_IDS:
            if method.encode() not in report:
                candidate.refuse("P252 original method identity absent")
        receipt["original_evidence"] = {
            "report_sha256": source.digest(report),
            "stderr_sha256": list(candidate.ORIGINAL_FAIL_STDERR),
            "methods": list(source.ORIGINAL_FAILURE_IDS), "native_exits": [1, 1, 1, 1],
            "receipt_sha256": "427ccddc4191292926d7986998cdd2651122c5f2c89738cbb5d2c6e0a8238a28",
            "raw_artifacts_read_here": False}
        test_raw, _ = source.raw_source("tests/test_p273_p76_current_admission.py")
        parsed = ast.parse(test_raw)
        count = sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
                    for cls in parsed.body if isinstance(cls, ast.ClassDef) for node in cls.body)
        if count != TEST_COUNT:
            candidate.refuse("unexpected focused suite inventory")
        receipt["expected_tests"] = count
        command = [sys.executable, "-B", "-m", "unittest", "-v", TEST_MODULE]
        # Keep only Windows basics and required source-domain/architecture
        # fields. No provider/credential environment is forwarded or printed.
        allowed = {"COMSPEC", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH",
                   "PATHEXT", "SYSTEMDRIVE", "GITHUB_ACTIONS", "RUNNER_OS",
                   "RUNNER_ENVIRONMENT", "GITHUB_REPOSITORY", "GITHUB_EVENT_NAME",
                   "GITHUB_REF", "GITHUB_REF_NAME", "GITHUB_WORKSPACE", "GITHUB_SHA",
                   "GITHUB_EVENT_PATH", "P273_ARCH"}
        env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
        env.update(candidate.READ_ONLY_GIT_ENV)
        start = last_progress = time.monotonic()
        observed_size = 0
        with (output / "stdout.raw").open("xb") as stdout, (output / "stderr.raw").open("xb") as stderr:
            child = subprocess.Popen(command, cwd=source.ROOT, stdin=subprocess.DEVNULL,
                                     stdout=stdout, stderr=stderr, shell=False, env=env)
            receipt["child_pid"] = child.pid
            while child.poll() is None:
                now = time.monotonic()
                size = (output / "stderr.raw").stat().st_size + (output / "stdout.raw").stat().st_size
                if size != observed_size:
                    observed_size, last_progress = size, now
                    print("P273 native suite progress: raw stream bytes=" + str(size), flush=True)
                if now - last_progress > 240 or now - start > 900:
                    receipt["timeout"] = True
                    child.kill()
                    break
                time.sleep(1)
            receipt["native_exit"] = child.wait(timeout=15)
            receipt["process_reaped"] = True
        receipt["seconds"] = time.monotonic() - start
        receipt["stdout"] = stream_receipt(output / "stdout.raw")
        receipt["stderr"] = stream_receipt(output / "stderr.raw")
        with (output / "stderr.raw").open("rb") as stream:
            raw = stream.read(source.MAX_GIT_BYTES + 1)
        receipt["unittest_complete"] = (
            len(raw) <= source.MAX_GIT_BYTES and source.suite_log_complete(raw, count)
            and receipt["stdout"]["bytes"] == 0)
    except Exception as error:
        receipt["error_type"] = type(error).__name__
        # Domain messages contain source paths only; arbitrary exception text
        # is excluded from public artifacts.
        if isinstance(error, (candidate.CurrentAdmissionRefused, source.CurrentSourceRefused)):
            receipt["source_refusal"] = str(error)
    finally:
        # Reap the direct unittest child on every exceptional path, before
        # observing the final source. Git children are synchronous read-only
        # operations; no descendant census or OS sandbox claim is made.
        if child is not None:
            try:
                if child.poll() is None:
                    child.kill()
                receipt["native_exit"] = child.wait(timeout=15)
                receipt["process_reaped"] = True
            except (OSError, subprocess.TimeoutExpired) as error:
                receipt["cleanup_error_type"] = type(error).__name__
                receipt["process_reaped"] = False
        for label in ("stdout", "stderr"):
            path = output / (label + ".raw")
            if path.exists():
                receipt[label] = stream_receipt(path)
        receipt["after_attempted"] = True
        try:
            after = candidate.prove_authenticated_current_source(source.ROOT)
            save(output / "after-source.json", after)
        except Exception as error:
            receipt["after_error_type"] = type(error).__name__
        if before is not None and after is not None:
            receipt["complete_source_equal"] = candidate.canonical(before) == candidate.canonical(after)
            receipt["before_sha256"] = source.digest(candidate.canonical(before))
            receipt["after_sha256"] = source.digest(candidate.canonical(after))
        receipt["source_candidate_tests_pass"] = qualifies(receipt, before, after)
        save(output / "receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if receipt["source_candidate_tests_pass"] else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        candidate.refuse("external evidence directory argument required")
    sys.exit(run(Path(sys.argv[1])))
