"""P164 bounded Git blob-reader integration-design PROTOTYPE, no product integration.

Genuine Windows lifecycle, malformed Git protocol, typed fixed-OID request, own-child
termination and real pinned-object byte equivalence. NOT security admission:
original P76/P85, P139, P140, current WinCred, original test suites untouched.
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
import threading
import time
import uuid

from scripts.p139_native_fs_verified_local_temp_root import (
    _guard_runner, _verify_original_handle_policy,
)
from scripts.p162_windows_immutable_git_batch_candidate import (
    BLOB_HEADER, MAX_SOURCE_BYTES, read_tree, sha1_blob, verify_blob,
)
from scripts.p153_windows_current_branch_security_candidate import (
    ORIGINALS, PINNED_ORIGINAL_P76_BRANCH, P140_PIN_DEFAULTS, _top_level_constants,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "51ecaa8eaf2e3f092d1006cf2ffba4f402c1de87"
BRANCH = "byok-c1-p164-bounded-immutable-object-reader-design-20261111"
COMMIT = "a12565b9be070684e1d7d801ded4833d13121f94"
EXPECTED_MODULES = 170
EXPECTED_PATHS = 19
SECRET_ENV = (
    "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "NAYEON_INTERNAL_SECRET",
    "P164_SECRET",
)


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def git(*args):
    child = subprocess.run(
        ["git", "-C", str(ROOT), *args], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25, check=True,
    )
    return child.stdout


def require_source():
    _guard_runner()
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("P164 exact hosted Windows branch required")
    head = git("rev-parse", "HEAD").decode().strip()
    if head != os.environ.get("GITHUB_SHA") or git("merge-base", BASE, head).decode().strip() != BASE:
        raise RuntimeError("P164 exact P163 source/head ancestry mismatch")
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P164 source not clean")
    tracked = [x for x in git("ls-files", "tests/test_*.py").decode().splitlines()
               if x.startswith("tests/test_") and x.endswith(".py")]
    if len(tracked) != EXPECTED_MODULES:
        raise RuntimeError("P164 original current test inventory changed")
    protected = tuple(ORIGINALS) + (
        "tests/phase_8_30_scope_migration.py",
        "tests/phase_8_32_scope_migration.py",
        "tests/phase_8_34_scope_migration.py",
        "tests/phase_8_36_scope_migration.py",
        "tests/phase_8_37_scope_migration.py",
        "tests/test_phase_837_scope_integrity.py",
        "scripts/p162_windows_immutable_git_batch_candidate.py",
        "scripts/p163_windows_security_review_readiness.py",
    )
    for path in sorted(set(protected)):
        if git("rev-parse", "HEAD:" + path) != git("rev-parse", BASE + ":" + path):
            raise RuntimeError("P164 historical security source blob modified: " + path)
    gate = _top_level_constants(ROOT / "tests/phase8_byok_c1_p76_scope.py", {"BRANCH"})
    if gate != {"BRANCH": PINNED_ORIGINAL_P76_BRANCH}:
        raise RuntimeError("P164 original P76 exact branch security gate altered")
    p140 = _top_level_constants(
        ROOT / "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
        set(P140_PIN_DEFAULTS),
    )
    if p140 != P140_PIN_DEFAULTS:
        raise RuntimeError("P164 P140 original security policy no-go altered")
    for ns in ("nayeon", "tests"):
        result = subprocess.run(
            ["git", "-C", str(ROOT), "grep", "-l", "-F",
             "p164_windows_bounded_immutable_reader_design", BASE, "--", ns],
            capture_output=True, stdin=subprocess.DEVNULL, timeout=25, check=False,
        )
        if result.returncode not in (0, 1) or result.stdout:
            raise RuntimeError("P164 candidate integrated into protected product/tests")
    print("P164_P163_EXACT_SHA_ORIGINAL_SECURITY_FILES_AND_170_MODULES=PASS", flush=True)
    print("P164_P76_P85_ORIGINAL_AND_P140_SIGNER_POLICY_REMAIN_FAIL_CLOSED=PASS", flush=True)
    return head, len(set(protected))


class BoundedCandidateSession:
    """Diagnostic only. No mutable Git refs accepted or cached.

    All requests are bound to a pre-verified OID/path map. A single outstanding
    call is permitted; failures irrevocably retire the test-owned child.
    Blocking Windows pipe calls are contained by an external request deadline.
    """

    def __init__(self, argv, *, env, objects, pins, legacy_digest):
        self.proc = subprocess.Popen(
            argv, cwd=ROOT, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            bufsize=0, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        self.objects = dict(objects)
        self.pins = dict(pins)
        self.legacy_digest = legacy_digest
        self.lock = threading.Lock()
        self.retired = False
        self.requests = 0
        self.failed = False

    def _retire(self):
        if self.retired:
            return
        self.retired = True
        proc = self.proc
        if proc.poll() is None:
            proc.kill()  # ONLY own disposable hosted Windows test child
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=4)
        if proc.stdin:
            proc.stdin.close()
        if proc.stdout:
            proc.stdout.close()

    def close(self):
        self._retire()

    def _read_one(self, path, oid):
        self.proc.stdin.write(oid.encode("ascii") + b"\n")
        self.proc.stdin.flush()
        hdr = self.proc.stdout.readline()
        matched = BLOB_HEADER.fullmatch(hdr)
        if matched is None:
            raise ValueError("P164 malformed actual candidate stream header")
        length = int(matched[2])
        if length > MAX_SOURCE_BYTES:
            raise ValueError("P164 oversized object must be refused before reading")
        chunks = []
        remaining = length
        while remaining:
            chunk = self.proc.stdout.read(remaining)
            if not chunk:
                raise ValueError("P164 truncated Windows native child pipe")
            chunks.append(chunk)
            remaining -= len(chunk)
        trailer = self.proc.stdout.read(1)
        return verify_blob(
            path, oid, hdr, b"".join(chunks), trailer, self.objects[path],
            self.pins, self.legacy_digest,
        )

    def request(self, path, oid, *, deadline=3.0):
        if self.retired:
            raise RuntimeError("P164 terminal session cannot be reused")
        if (type(path) is not str or path not in self.pins or
            type(oid) is not str or oid != self.objects.get(path)):
            raise ValueError("P164 immutable literal path and OID binding required")
        if deadline <= 0 or deadline > 5:
            raise ValueError("P164 bounded request deadline required")
        if not self.lock.acquire(blocking=False):
            raise RuntimeError("P164 refuses concurrent use of one pipe/session")
        try:
            if self.retired:
                raise RuntimeError("P164 terminal session cannot be reused")
            holder = {}
            def worker():
                try:
                    holder["value"] = self._read_one(path, oid)
                except BaseException as exc:
                    holder["failure"] = exc
            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            thread.join(deadline)
            if thread.is_alive():
                self.failed = True
                self._retire()
                thread.join(3)
                if thread.is_alive():
                    raise RuntimeError("P164 failed to terminate owned blocked pipe")
                raise TimeoutError("P164 bounded Git object request timed out and child retired")
            if "failure" in holder:
                self.failed = True
                self._retire()
                raise holder["failure"]
            if "value" not in holder:
                self.failed = True
                self._retire()
                raise RuntimeError("P164 missing candidate response")
            self.requests += 1
            return holder["value"]
        finally:
            self.lock.release()


def fixture_main(mode, oid, path):
    """Disposable synthetic Git wire responder. Never alters the actual repo."""
    if mode not in {
        "good", "split", "wrong_oid", "wrong_type", "oversize",
        "bad_blob", "truncated", "eof", "hang_header", "hang_body",
        "wrong_delimiter",
    }:
        return 19
    if len(oid) != 40 or not re.fullmatch("[0-9a-f]{40}", oid):
        return 20
    from tests import phase_8_37_scope_migration as scope
    if path not in scope.prior.CANDIDATE_SHA256:
        return 21
    request = sys.stdin.buffer.readline()
    if request != (oid + "\n").encode("ascii"):
        return 22
    if mode == "eof":
        return 0
    if mode == "hang_header":
        time.sleep(30)
        return 0
    data = git("show", COMMIT + ":" + path)
    good_oid = sha1_blob(data)
    if good_oid != oid:
        return 23
    header = f"{good_oid} blob {len(data)}\n".encode()
    if mode == "wrong_oid":
        header = (b"0" * 40) + header[40:]
    elif mode == "wrong_type":
        header = header.replace(b" blob ", b" tree ")
    elif mode == "oversize":
        header = f"{good_oid} blob {MAX_SOURCE_BYTES + 1}\n".encode()
    elif mode == "bad_blob":
        data = bytes([data[0] ^ 1]) + data[1:]
    elif mode == "truncated":
        data = data[:-2]
    elif mode == "hang_body":
        sys.stdout.buffer.write(header + data[:2])
        sys.stdout.buffer.flush()
        time.sleep(30)
        return 0
    delimiter = b"x" if mode == "wrong_delimiter" else b"\n"
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.flush()
    if mode == "split":
        # Intentionally exercise partial Windows anonymous pipe reads.
        for offset in range(0, len(data), 347):
            sys.stdout.buffer.write(data[offset:offset + 347])
            sys.stdout.buffer.flush()
            time.sleep(0.001)
    else:
        sys.stdout.buffer.write(data)
    sys.stdout.buffer.write(delimiter)
    sys.stdout.buffer.flush()
    return 0


def _run_candidate_test(env, objects, pins, legacy, path, oid, mode, expected):
    argv = [
        sys.executable, "-B", "-m",
        "scripts.p164_windows_bounded_immutable_reader_design",
        "--fixture", mode, oid, path,
    ]
    session = BoundedCandidateSession(
        argv, env=env, objects=objects, pins=pins, legacy_digest=legacy,
    )
    t0 = time.monotonic()
    try:
        if expected == "PASS":
            value = session.request(path, oid, deadline=3)
            original = git("show", COMMIT + ":" + path)
            if value != original:
                raise RuntimeError("P164 synthetic correct read not exactly original Git bytes")
            actual = "PASS"
        else:
            try:
                session.request(path, oid, deadline=1.1)
            except (ValueError, TimeoutError, RuntimeError, BrokenPipeError, OSError) as exc:
                if not session.retired or not session.failed:
                    raise RuntimeError("P164 failing protocol did not retire its owned child")
                try:
                    session.request(path, oid, deadline=0.1)
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError("P164 failed session illegally reused")
                actual = "REJECT"
            else:
                raise RuntimeError("P164 accepted malicious or failed Git protocol: " + mode)
        return {
            "scenario": mode, "status": actual,
            "owned_child_retired": expected != "PASS" and session.retired,
            "elapsed_seconds": round(time.monotonic() - t0, 3),
        }
    finally:
        session.close()


def main():
    head, custody_count = require_source()
    from tests import phase_8_37_scope_migration as scope
    if scope.PROTECTED != COMMIT or len(scope.prior.CANDIDATE_SHA256) != EXPECTED_PATHS:
        raise RuntimeError("P164 exact 19-source frozen protected commit changed")
    pins = dict(scope.prior.CANDIDATE_SHA256)
    objects, tree_hash = read_tree(COMMIT, pins, env=None)
    if len(objects) != EXPECTED_PATHS or set(objects) != set(pins):
        raise RuntimeError("P164 original fixed Git tree+pin inventory missing")
    out = Path(os.environ["RUNNER_TEMP"]) / "nayeon-p164-bounded-git-protocol-review"
    out.mkdir(parents=True, exist_ok=True)
    safe = Path("C:\\NayeonP139_" + uuid.uuid4().hex)
    made = False
    cases = []
    origin_bytes = []
    try:
        if safe.exists() or safe.is_symlink():
            raise RuntimeError("P164 native owned temp root preexists")
        os.mkdir(safe)
        made = True
        _verify_original_handle_policy(str(safe))
        print("P164_P139_UNCHANGED_WIN32_OPEN_HANDLE_TEMP_POLICY=PASS", flush=True)
        env = os.environ.copy()
        for name in SECRET_ENV:
            env.pop(name, None)
        env.update({
            "TEMP": str(safe), "TMP": str(safe), "TMPDIR": str(safe),
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        path = sorted(pins)[0]
        oid = objects[path]
        # One genuine long-lived Git process retrieves every historical source
        # object in its fixed protected tree, with no mutable refs or cached pins.
        t0 = time.monotonic()
        real = BoundedCandidateSession(
            ["git", "cat-file", "--batch"], env=env, objects=objects,
            pins=pins, legacy_digest=scope.prior._digest,
        )
        try:
            # Invalid request must be refused BEFORE any IPC into this session.
            forbidden = [
                ("unknown_path", "nayeon/foreign.py", oid),
                ("case_alias", path.upper(), oid),
                ("backslash_alias", path.replace("/", "\\"), oid),
                ("parent_traversal", "../" + path, oid),
                ("wrong_source_oid", path, "1" * 40),
                ("missing_source_oid", path, ""),
                ("mutable_ref_expression", path, "HEAD"),
            ]
            rejections = []
            for name, p, o in forbidden:
                before = real.requests
                try:
                    real.request(p, o)
                except ValueError:
                    if real.requests != before or real.retired:
                        raise RuntimeError("P164 invalid path/OID altered real Git session")
                    rejections.append(name)
                else:
                    raise RuntimeError("P164 admitted untrusted mutable/alias request: " + name)
            for p in sorted(pins):
                raw = real.request(p, objects[p])
                original = git("show", COMMIT + ":" + p)
                if raw != original:
                    raise RuntimeError("P164 real persistent Git batch diverged from original show")
                origin_bytes.append({"path":p,"sha256":digest(raw),"bytes":len(raw)})
            if real.requests != EXPECTED_PATHS:
                raise RuntimeError("P164 expected each of 19 immutable object queries")
        finally:
            real.close()
        elapsed_real = round(time.monotonic() - t0,3)
        modes = (
            ("good","PASS"), ("split","PASS"),
            ("wrong_oid","REJECT"), ("wrong_type","REJECT"),
            ("oversize","REJECT"), ("bad_blob","REJECT"),
            ("truncated","REJECT"), ("eof","REJECT"),
            ("hang_header","REJECT"), ("hang_body","REJECT"),
            ("wrong_delimiter","REJECT"),
        )
        for mode,expected in modes:
            observed = _run_candidate_test(
                env, objects, pins, scope.prior._digest,
                path, oid, mode, expected,
            )
            if observed["status"] != expected:
                raise RuntimeError("P164 native Windows candidate scenario drift: " + mode)
            cases.append(observed)
            print("P164_NATIVE_PROTOCOL_CASE="+mode+"|RESULT="+observed["status"]+
                  "|SECONDS="+str(observed["elapsed_seconds"]),flush=True)
    finally:
        if made:
            st = safe.lstat()
            if safe.is_symlink() or getattr(st, "st_file_attributes",0) & 0x400:
                raise RuntimeError("P164 unsafe Win32 temp reparse teardown refused")
            shutil.rmtree(safe)
    if git("status", "--porcelain=v1"):
        raise RuntimeError("P164 original Git source changed during diagnostics")
    results = {
        "checkpoint": "P164",
        "tested_exact_sha": head,
        "verified_exact_parent_p163": BASE,
        "original_secure_source_git_blobs_verified_unchanged": custody_count,
        "current_tracked_unittest_inventory": EXPECTED_MODULES,
        "historical_frozen_commit": COMMIT,
        "original_fixed_git_tree_sha256": tree_hash,
        "original_exact_path_specific_sha256_pins": EXPECTED_PATHS,
        "real_persistent_git_object_queries": len(origin_bytes),
        "raw_original_git_show_byte_identical_responses": len(origin_bytes),
        "pinned_source_sha256_ledger": origin_bytes,
        "real_19_blob_roundtrip_seconds_including_original_shows": elapsed_real,
        "before_IPC_mutable_ref_or_alias_refusals": rejections,
        "all_before_IPC_refusal_count": len(rejections),
        "fake_native_windows_pipe_protocol_cases": cases,
        "valid_synthetic_native_pipe_responses": sum(x["status"]=="PASS" for x in cases),
        "invalid_or_timeout_synthetic_pipe_responses_rejected": sum(x["status"]=="REJECT" for x in cases),
        "original_historical_P76_P85_security_negatives_waived": False,
        "prototype_installed_in_original_tests_or_product": False,
        "production_Git_process_integration": "NO_GO",
        "new_original_full_product_windows_regression_passes": 0,
        "accepted_complete_windows_product_regression_triads": "0/3",
        "independent_qualified_reviewer_signature": "NOT OBTAINED",
        "privileged_BYOK_C1_G0_to_G6": "OPEN",
        "production_release": "HOLD",
        "collector_success_not_security_or_production_GO": True,
    }
    ledger = out / "p164_actual_windows_bounded_immutable_protocol_ledger.json"
    ledger.write_text(json.dumps(results,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("P164_REAL_FIXED_GIT_BLOB_BYTE_EQUIVALENCE="+str(len(origin_bytes))+"/"+str(EXPECTED_PATHS),flush=True)
    print("P164_PRE_IPC_MUTABLE_REF_ALIAS_REJECTIONS="+str(len(rejections)),flush=True)
    print("P164_FAKE_NATIVE_PIPE_VALID="+str(results["valid_synthetic_native_pipe_responses"]),flush=True)
    print("P164_FAKE_NATIVE_PIPE_NEGATIVE_AND_TIMEOUT_REJECTIONS="+str(results["invalid_or_timeout_synthetic_pipe_responses_rejected"]),flush=True)
    print("P164_ORIGINAL_SECURITY_SOURCE_AND_GATES=UNMODIFIED",flush=True)
    print("P164_FULL_PRODUCT_REGRESSION_TRIAD=0/3",flush=True)
    print("P164_INDEPENDENT_EXTERNAL_GO=NOT_OBTAINED",flush=True)
    print("P164_PRODUCTION_RELEASE=HOLD",flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--fixture":
        raise SystemExit(fixture_main(sys.argv[2],sys.argv[3],sys.argv[4]))
    raise SystemExit(main())
