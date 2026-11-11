"""P162: evaluate unmodified immutable Git blob reads with a long-lived Git batch child.

PROTOTYPE ONLY: never imported by product or historic test/security admission.
Compares byte-for-byte with real original git show, verifies every pinned 8.36
SHA256, probes adversarial corrupted replies, and records genuine Windows times.
No cached mutable refs, source edits, test rewrites, or release authorisation.
"""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[1]
BASE = "fe26dc1aeda0422c9aaadee63edae4f2b583fa81"
BRANCH = "byok-c1-p162-immutable-git-batch-read-candidate-20261111"
ITERATIONS = 5
EXPECTED_TEST_MODULES = 170
EXPECTED_PATHS = 19
MAX_SOURCE_BYTES = 2_000_000
DENIED_ENV = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "NAYEON_INTERNAL_SECRET",
    "P162_PROVIDER_KEY",
)
BLOB_HEADER = re.compile(rb"([a-f0-9]{40}) blob ([0-9]+)\n\Z")
TREE_REC = re.compile(rb"(100644) blob ([a-f0-9]{40})\Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha1_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def git(args, *, env=None, timeout=25) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, env=env, capture_output=True,
        stdin=subprocess.DEVNULL, timeout=timeout, check=True,
    )
    return result.stdout


def check_checkout():
    _guard_runner()
    if (os.environ.get("GITHUB_REF_NAME") != BRANCH
        or os.environ.get("RUNNER_OS") != "Windows"
        or os.environ.get("GITHUB_ACTIONS") != "true"):
        raise RuntimeError("P162 exact disposable hosted Windows source required")
    head = git(["rev-parse", "HEAD"]).decode().strip()
    if head != os.environ.get("GITHUB_SHA") or git(["merge-base", BASE, "HEAD"]).decode().strip() != BASE:
        raise RuntimeError("P162 exact P161 ancestry/source HEAD mismatch")
    if git(["status", "--porcelain=v1"]):
        raise RuntimeError("P162 checkout dirty")
    tracked = [x for x in git(["ls-files", "tests/test_*.py"]).decode().splitlines()
               if x.startswith("tests/test_") and x.endswith(".py")]
    if len(tracked) != EXPECTED_TEST_MODULES:
        raise RuntimeError("P162 source test inventory drift")
    original_paths = (
        "tests/phase_8_30_scope_migration.py",
        "tests/phase_8_32_scope_migration.py",
        "tests/phase_8_34_scope_migration.py",
        "tests/phase_8_36_scope_migration.py",
        "tests/phase_8_37_scope_migration.py",
        "tests/test_phase_837_scope_integrity.py",
        "tests/test_phase8_byok_c1_p76_scope.py",
        "scripts/p139_native_fs_verified_local_temp_root.py",
        "nayeon/secrets/windows_credential.py",
    )
    for p in original_paths:
        if git(["rev-parse", "HEAD:" + p]) != git(["rev-parse", BASE + ":" + p]):
            raise RuntimeError("P162 immutable historical source/security blob changed: " + p)
    print("P162_P161_EXACT_PARENT_170_MODULE_SOURCE_INVENTORY=PASS", flush=True)
    print("P162_NINE_ORIGINAL_GIT_SECURITY_WIN_CRED_SOURCE_BLOBS_UNCHANGED=PASS", flush=True)
    return head


def read_tree(commit: str, pins: dict[str, str], env):
    raw = git(["ls-tree", "-r", "-z", "--full-tree", commit], env=env)
    entries = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        if b"\t" not in record:
            raise RuntimeError("P162 malformed genuine Git tree record")
        meta, bpath = record.split(b"\t", 1)
        m = TREE_REC.fullmatch(meta)
        if bpath.decode("utf8", "strict") in pins:
            if not m:
                raise RuntimeError("P162 pinned historical path is not a 100644 blob")
            path = bpath.decode("utf8", "strict")
            if path in entries:
                raise RuntimeError("P162 duplicate historical path in Git tree")
            entries[path] = m[2].decode("ascii")
    if set(entries) != set(pins) or len(entries) != EXPECTED_PATHS:
        raise RuntimeError("P162 immutable 8.36 path inventory incomplete")
    return entries, sha256(raw)


def verify_blob(path, oid, raw_header, data, delimiter, expected_oid, pins, legacy_digest):
    if path not in pins or oid != expected_oid:
        raise ValueError("P162 unknown path or frozen Git blob object")
    if type(raw_header) is not bytes or not BLOB_HEADER.fullmatch(raw_header):
        raise ValueError("P162 malformed Git batch object header")
    m = BLOB_HEADER.fullmatch(raw_header)
    if m[1].decode("ascii") != oid:
        raise ValueError("P162 Git batch object identity drift")
    length = int(m[2])
    if length > MAX_SOURCE_BYTES or len(data) != length or delimiter != b"\n":
        raise ValueError("P162 Git batch object framing violation")
    if sha1_blob(data) != oid:
        raise ValueError("P162 Git batch bytes differ from object identity")
    if legacy_digest(path, data) != pins[path]:
        raise ValueError("P162 original historical normalized SHA256 pin mismatch")
    return data


def negative_contracts(path, oid, data, expected, pins, legacy_digest):
    correct = f"{oid} blob {len(data)}\n".encode()
    checks = [
        ("wrong_oid", path, oid, b"0"*40 + correct[40:], data, b"\n", expected),
        ("wrong_type", path, oid, correct.replace(b" blob ", b" tree "), data, b"\n", expected),
        ("changed_body", path, oid, correct, bytes([data[0] ^ 1]) + data[1:], b"\n", expected),
        ("wrong_length", path, oid, f"{oid} blob {len(data)+1}\n".encode(), data, b"\n", expected),
        ("truncated_body", path, oid, correct, data[:-1], b"\n", expected),
        ("missing_separator", path, oid, correct, data, b"x", expected),
        ("untrusted_path", "nayeon/untrusted.py", oid, correct, data, b"\n", expected),
        ("different_expected_oid", path, oid, correct, data, b"\n", "1" * 40),
        ("invalid_header", path, oid, b"not-git\n", data, b"\n", expected),
    ]
    for name, p, req, header, body, delim, exp in checks:
        try:
            verify_blob(p, req, header, body, delim, exp, pins, legacy_digest)
        except ValueError:
            pass
        else:
            raise RuntimeError("P162 corruption/adversarial probe incorrectly accepted: " + name)
    return len(checks)


def read_batch(proc, path, oid, expected, pins, legacy_digest):
    if proc.poll() is not None:
        raise RuntimeError("P162 actual Git batch process terminated prematurely")
    proc.stdin.write(oid.encode("ascii") + b"\n")
    proc.stdin.flush()
    hdr = proc.stdout.readline()
    match = BLOB_HEADER.fullmatch(hdr)
    if match is None:
        raise RuntimeError("P162 actual Git returned malformed batch header")
    size = int(match[2])
    if size > MAX_SOURCE_BYTES:
        raise RuntimeError("P162 Git batch object exceeds safety budget")
    data = proc.stdout.read(size)
    delim = proc.stdout.read(1)
    return verify_blob(path, oid, hdr, data, delim, expected, pins, legacy_digest)


def main():
    head = check_checkout()
    from tests import phase_8_37_scope_migration as scope
    pins = dict(scope.prior.CANDIDATE_SHA256)
    protected = scope.PROTECTED
    if (len(pins) != EXPECTED_PATHS or protected != "a12565b9be070684e1d7d801ded4833d13121f94"
        or git(["rev-parse", "--show-object-format"]).strip() != b"sha1"):
        raise RuntimeError("P162 immutable source manifest/object format changed")
    output = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p162-frozen-immutable-git-batch-candidate"
    output.mkdir(parents=True, exist_ok=True)
    root = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    try:
        if root.exists() or root.is_symlink():
            raise RuntimeError("P162 disposable temp root preexists")
        os.mkdir(root)
        made = True
        _verify_original_handle_policy(str(root))
        print("P162_UNCHANGED_P139_NATIVE_WIN32_FILE_HANDLE=PASS", flush=True)
        child_temp = root / "git_benchmark"
        child_temp.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        for name in DENIED_ENV:
            env.pop(name, None)
        env.update({"TEMP": str(child_temp), "TMP": str(child_temp), "TMPDIR": str(child_temp),
                    "PYTHONDONTWRITEBYTECODE": "1"})
        objects, tree_sha = read_tree(protected, pins, env)
        paths = sorted(pins)
        legacy = scope.prior._digest
        # The baseline must call actual Git show for EVERY observed object;
        # no immutable-object memo/cache is used even in the baseline.
        baseline = {}
        samples = []
        baseline_start = time.perf_counter()
        for iteration in range(ITERATIONS):
            for path in paths:
                t0 = time.perf_counter()
                data = git(["show", protected + ":" + path], env=env)
                t1 = time.perf_counter()
                oid = objects[path]
                verify_blob(path, oid, f"{oid} blob {len(data)}\n".encode(),
                            data, b"\n", oid, pins, legacy)
                baseline[path] = (len(data), sha256(data))
                samples.append(round((t1-t0)*1000,3))
        baseline_seconds = time.perf_counter() - baseline_start
        # First run tamper/refusal diagnostics entirely IN MEMORY, with no
        # writes to source/Git refs/index, or replacement of original readers.
        first = paths[0]
        first_data = git(["show", protected + ":" + first], env=env)
        negatives = negative_contracts(first, objects[first], first_data,
                                       objects[first], pins, legacy)
        # Persistent Git object reader is a CANDIDATE for immutable objects
        # only. Current-branch refs, HEAD, tags, worktree and index never go
        # through this reader. Every request verifies both object oid and pin.
        t0 = time.perf_counter()
        proc = subprocess.Popen(
            ["git", "cat-file", "--batch"], cwd=ROOT, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        query_times = []
        comparisons = 0
        try:
            for iteration in range(ITERATIONS):
                for path in paths:
                    ts = time.perf_counter()
                    data = read_batch(proc, path, objects[path], objects[path], pins, legacy)
                    if (len(data), sha256(data)) != baseline[path]:
                        raise RuntimeError("P162 original Git show vs batch raw-byte inequality")
                    query_times.append(round((time.perf_counter() - ts)*1000,3))
                    comparisons += 1
            batch_seconds = time.perf_counter()-t0
        finally:
            if proc.stdin is not None:
                proc.stdin.close()
            try:
                end_code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                end_code = proc.wait(timeout=5)
            if proc.stdout is not None:
                proc.stdout.close()
        if end_code != 0:
            raise RuntimeError("P162 real Git cat-file --batch nonzero exit")
        if comparisons != EXPECTED_PATHS*ITERATIONS:
            raise RuntimeError("P162 original-vs-candidate comparison count invalid")
        if git(["status", "--porcelain=v1"]):
            raise RuntimeError("P162 benchmark unexpectedly changed original product source")
        result = {
            "checkpoint": "P162",
            "tested_exact_head_sha": head,
            "exact_parent_P161": BASE,
            "original_legacy_P161_case_native_result": "PASS at 95.75 sec; 2470 Git calls",
            "candidate_scope": "IMMUTABLE fixed commit+blob Git objects ONLY, never mutable refs/index/HEAD/tags/worktree",
            "historical_8_36_protected_commit": protected,
            "tracked_current_test_module_files": EXPECTED_TEST_MODULES,
            "literal_historical_sha256_pins": EXPECTED_PATHS,
            "real_original_git_show_calls": comparisons,
            "real_batch_git_blob_queries": comparisons,
            "exact_raw_byte_comparisons": comparisons,
            "in_memory_adversarial_negative_probes": negatives,
            "original_8_36_git_tree_raw_sha256": tree_sha,
            "original_separate_git_show_seconds": round(baseline_seconds, 5),
            "proposed_immutable_git_batch_seconds": round(batch_seconds, 5),
            "measured_speed_ratio_baseline_over_candidate": round(baseline_seconds/batch_seconds,3) if batch_seconds>0 else None,
            "original_show_single_query_median_ms": sorted(samples)[len(samples)//2],
            "candidate_batch_single_query_median_ms": sorted(query_times)[len(query_times)//2],
            "baseline_bytes_sha256_by_path": {p: baseline[p][1] for p in paths},
            "original_source_security_test_bytes_changed": False,
            "test_harness_or_product_integration": "NOT IMPLEMENTED, CANDIDATE EVALUATION ONLY",
            "original_P76_P85_exact_branch_refusal": "UNMODIFIED",
            "external_qualified_security_and_test_governance": "NOT OBTAINED",
            "accepted_complete_full_product_windows_regressions": "0/3",
            "privileged_C1_G0_to_G6": "OPEN",
            "production_release": "HOLD",
        }
        (output / "p162_immutable_git_batch_candidate_windows_ledger.json").write_text(
            json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf8",
        )
        print("P162_ORIGINAL_IMMUTABLE_GIT_SHOW="+str(comparisons)+"|SECONDS="+str(result["original_separate_git_show_seconds"]), flush=True)
        print("P162_REAL_IMMUTABLE_GIT_BATCH="+str(comparisons)+"|SECONDS="+str(result["proposed_immutable_git_batch_seconds"]), flush=True)
        print("P162_BYTE_IDENTICAL_SOURCE_SHA256_PINNED_COMPARISONS="+str(comparisons), flush=True)
        print("P162_ADVERSARIAL_NEGATIVE_PROBES_REJECTED="+str(negatives), flush=True)
        print("P162_MEASURED_IMMUTABLE_ONLY_SPEED_RATIO="+str(result["measured_speed_ratio_baseline_over_candidate"]), flush=True)
        print("P162_HISTORICAL_SECURITY_TESTS_NOT_PATCHED_OR_WAIVED=PASS", flush=True)
        print("P162_CANDIDATE_IS_NOT_APPROVED_FOR_TRUST_ADMISSION=TRUE", flush=True)
        print("P162_ACCEPTED_FULL_WINDOWS_PRODUCT_TRIAD=0/3", flush=True)
        print("P162_PRODUCTION_RELEASE=HOLD", flush=True)
        return 0
    finally:
        if made:
            stat = root.lstat()
            if root.is_symlink() or getattr(stat,"st_file_attributes",0)&0x400:
                raise RuntimeError("P162 refuse unsafe test directory cleanup")
            shutil.rmtree(root)


if __name__ == "__main__":
    raise SystemExit(main())
