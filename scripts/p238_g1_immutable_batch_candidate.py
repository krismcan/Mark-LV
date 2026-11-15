"""P238 INSTRUMENTED CANDIDATE. One unchanged G1 body; never release GO.

External controller, stdlib only. Fixed sealed-B blob shows only; no cached
admission or mutable Git substitutions. Raw evidence stays private on runner.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import re
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

PARENT = "f66358de30fcb451e660e500df6a7843c6bbf0a6"
SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
B = "e3612279cb972e68e2487702183d5bf5b8f6c4a1"
B_TREE = "99624a766e864addf5d096bb1a907c85d11401dc"
BRANCH = "byok-c1-p238-g1-immutable-batch-equivalence-20261115"
TEST = "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_every_candidate_source_byte_is_bound"
ADDITIONS = (
    ".github/workflows/p238-g1-immutable-batch-candidate.yml",
    "docs/byok-c1-p238-g1-immutable-batch-candidate.md",
    "scripts/p238_g1_immutable_batch_candidate.py",
    "scripts/p238_g1_batch_selftest.py",
)
SECONDS = 180
READ_SECONDS = 20
MAX_BLOB = 2_000_000
MAX_LOG = 4 * 1024 * 1024
MAX_READS = 4096
HEADER = re.compile(rb"([0-9a-f]{40}) blob (0|[1-9][0-9]{0,6})\n\Z")
MANIFEST = {
    ".codex/CURRENT_STATE.md": ("d7134c7d36a528bd3ed28c26ab55380874ce049c", "ecb30dd2d59a33cc34ea79b0c9f5350fe10c2bb4e43cac2b3d07e8dad3cdba65"),
    "docs/phase8_first_run_connection_ui_design.md": ("23cb60cefb9bc3b84bfb8a1f36257b6b946781fc", "04b37aee29abbfb350e80ccec65458556adaa4e1d3b3878d50597105a5098327"),
    "nayeon/brain/onboarding_coordination.py": ("b97e9d710bfd9cc7a31d8ec97525b9449700c228", "af479aa7597e036b84a5f21644182ea3bae2ba584d4c310c070aafb70ffddf15"),
    "nayeon/brain/onboarding_recovery.py": ("952eff66c91723a54086b41f8e5d384b8af5d593", "dbb2963de50326422c08ce0d46fec5920b6548d1210e0772429ea36c6d4a0738"),
    "nayeon/desktop_alpha/application.py": ("0062db49ce2be95c8359427707c91c741658354c", "af9bb617b67e56d2a71ae796af0f0846670303d0e192187a0ed6706127f73a82"),
    "nayeon/desktop_alpha/first_run_connection_owner.py": ("3273ce4c1681936ce7ae9a5e90d99a565acf6a82", "d3fb11f2c0095bb4e98d2a5339bb04f1ba73b286159083d32e6ccd07c2ee3e04"),
    "nayeon/desktop_alpha/first_run_connection_window.py": ("3e092bfe7651947a13583b8bfbef7b3a9ef5364d", "865fa15854591f151b2a6c17ef392636a0ea9950441c531b463c931e72bc1b32"),
    "nayeon/desktop_alpha/workspace_window.py": ("3aa881499d017b23cd55dd77e5e26c3638105365", "b7e78df7b0a786c0b4c5b19ec3a91f003f0995e496069e718c7389ff5871111c"),
    "tests/phase_8_30_scope_migration.py": ("6bc8987ff889d62e5675e937c489fdc63add8a97", "7fab9ace158264bdbf1c40838218576314649249ae8c89ecb5b52522c81562f3"),
    "tests/phase_8_37_scope_migration.py": ("3da61b15c74375775ca35605aed812c3b8c9e8da", "3f0ef3592754734e1050e5ce57aef50ce48de4b768019d72f6590ea3f73ddcaa"),
    "tests/phase8_byok_b_scope_migration.py": ("78733fe16623be018161e272286cf06afe820484", "7aa013c3400b4032087ad6f769d5ce0cb727d628586bb4f4cc4fdbca5c6f246c"),
    "tests/phase8_byok_scope_migration.py": ("f4d9f4f136afe09a622e1c2c0904c65f8790f06b", "7eaa989e141e17c7303ede283b3a979dc77680fa5b74d86a75dc8233ea4324b1"),
    "tests/test_first_run_connection_application.py": ("43066f07b2c5d19b667b3118890ee96454858795", "3c32da2c334dbda0acfe6911aee200d27648d4d71fb08ba5c665acfac11d2849"),
    "tests/test_first_run_connection_cancelled_effect.py": ("e6c111ee6c7184941e52d71535a590464e965d84", "26aa5cd65647316e9878b3ac2a0f89e739823923bee20cc0c9a0ce54c02c375a"),
    "tests/test_first_run_connection_effect_isolation.py": ("3ce94f67395f3370da412a85985b7a9b93c03dcc", "26b78138366ee6ec4cb8115c36e03d4dfa90a541ff5b9b3505a7f59c244cada7"),
    "tests/test_first_run_connection_window.py": ("fafa0f58c1d51fb3bffc067e59747de3af8cba91", "5c1fce9f76ba1d255ba3f4432da9ccef5edeb16717d3bf3709f512c3a8554757"),
    "tests/test_phase_832_scope_integrity.py": ("755c4c1f72f66cfd93b43bc41ca5e1c9f8f31eb9", "cc3d83397be376cce1fd1a005483e6576dea111da276a048685caf787d4058c8"),
    "tests/test_phase_833_scope_integrity.py": ("fe57747bb9bfda87d2bba4814ab29875d58be537", "4bdcd395b00a4d4e3ffd104ff17cc923f75075c20e457a090c045754700b5590"),
    "tests/test_phase_834_scope_integrity.py": ("373b5bd37faa6cc61c9211fc82e77ca34c41fa56", "142d05496a0a0d75a9d5a078b9e5144b4ab56821fd329b126903bd80e1a0e754"),
    "tests/test_phase_836_scope_integrity.py": ("1e00e9befc55ed68637dbf5bf6b0ef3954a1831f", "6ecb8d3ac9e970ef42d12855f81f406961cb82fcd71ef8bc26ed7e10ca822b8a"),
    "tests/test_phase_837_scope_integrity.py": ("78de2d5eb51d7640168be88b92112ed84662032c", "827678f7e01e8fe92b56045189fa7f97e363987b688c638bfcedb1abd99767e7"),
    "tests/test_phase8_byok_b_scope_integrity.py": ("6091cd5b37118bdf451deccbe1575e6c4dc824b0", "149cdf40c30ef4183ae41e6775d3a1950e09bb47d849eae1e90fa5b8b80e784a"),
    "tests/test_phase8_byok_scope_integrity.py": ("f8fc35f81f901bf10e0d7a916473769b6ffc8c1a", "5c369d3a04e5254b2205049b44ea3ef661ff32870d20ce14d8f26cf2ca143cc3"),
}


def require(ok, code):
    if not ok:
        raise RuntimeError(code)  # fixed codes only, never exception/path disclosure


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", "utf8")


def read(path, limit=MAX_LOG):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not getattr(info, "st_file_attributes", 0) & 0x400, "NONREGULAR")
    require(info.st_size <= limit, "FILE_CAP")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "FILE_CAP")
    return raw


def environment():
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if (upper.startswith(("GIT_", "P134_", "ACTIONS_", "INPUT_"))
                or any(x in upper for x in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))
                or upper in {"PYTHONPATH", "PYTHONHOME", "SSH_AUTH_SOCK", "SSH_AGENT_PID"}):
            del env[key]
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], env=environment(),
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=45, check=True).stdout


def load_original():
    path = Path(__file__).with_name("p234_windows_finegrain_diagnostic.py")
    spec = importlib.util.spec_from_file_location("p238_unchanged_p234", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.SOURCE == SOURCE and module.SECONDS == SECONDS, "P234_CONSTANTS")
    return module


def check_delta(parents, rows):
    require(parents == [PARENT], "EXACT_PARENT")
    require(sorted(rows) == sorted("A\t" + p for p in ADDITIONS), "EXACT_ADDITIONS")


def provenance(root):
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.getenv("GITHUB_EVENT_NAME") == "push"
            and os.getenv("GITHUB_REF_NAME") == BRANCH, "HOST_IDENTITY")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    require(head == os.getenv("GITHUB_SHA"), "HEAD")
    require(git(root, "rev-parse", "--is-shallow-repository") == b"false\n", "SHALLOW")
    require(git(root, "rev-parse", "--show-object-format") == b"sha1\n", "OBJECT_FORMAT")
    require(not git(root, "status", "--porcelain=v1", "-uall", "--ignored=matching"), "DIRTY")
    require(not git(root, "for-each-ref", "refs/replace"), "REPLACE")
    objdir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    require(not (objdir / "info/grafts").exists(), "GRAFT")
    check_delta(git(root, "rev-list", "--parents", "-n", "1", head).decode().split()[1:],
                git(root, "diff-tree", "--no-commit-id", "--name-status", "-r", "--no-renames",
                    PARENT, head).decode().splitlines())
    hashes = {}
    for path in ADDITIONS:
        raw = read(root / path)
        require(raw == git(root, "show", head + ":" + path), "CONTROLLER_BYTES")
        hashes[path] = sha(raw)
    require(git(root, "rev-parse", "HEAD:scripts/p234_windows_finegrain_diagnostic.py").strip()
            == b"0c5781a28187bd5eddb5f7a3ff0d85c1a5430d6c", "P234_BLOB")
    require(read(root / "scripts/p234_windows_finegrain_diagnostic.py") == git(
        root, "show", "HEAD:scripts/p234_windows_finegrain_diagnostic.py"), "P234_DISK")
    return {"head": head, "parent": PARENT, "raw_sha256": hashes}


def intercept_path(args, kwargs, root):
    # Match only the exact original Phase8.30 call signature. Even near matches
    # delegate; no generic Git wrapper, cwd alias, optional flag or timeout rewrite.
    if (len(args) != 1 or type(args[0]) is not list or len(args[0]) != 3
            or any(type(x) is not str for x in args[0])
            or args[0][:2] != ["git", "show"]
            or set(kwargs) != {"cwd", "stderr", "timeout"}
            or kwargs["cwd"] != root or kwargs["stderr"] != subprocess.DEVNULL
            or type(kwargs["timeout"]) is not int or kwargs["timeout"] != READ_SECONDS):
        return None
    prefix = B + ":"
    query = args[0][2]
    path = query[len(prefix):] if query.startswith(prefix) else None
    return path if path in MANIFEST else None


def verify_frame(path, header, raw, delimiter, originals, digest):
    require(path in MANIFEST, "PATH")
    oid, pin = MANIFEST[path]
    match = HEADER.fullmatch(header) if type(header) is bytes else None
    require(match is not None and match[1].decode("ascii") == oid, "HEADER_IDENTITY")
    size = int(match[2])
    require(type(raw) is bytes and size <= MAX_BLOB and len(raw) == size
            and delimiter == b"\n", "FRAME")
    require(blob(raw) == oid, "BLOB_IDENTITY")
    require(digest(path, raw) == pin, "ORIGINAL_NORMALIZED_PIN")
    require(path in originals and raw == originals[path], "ORIGINAL_SHOW_BYTES")
    return raw


def frame(stream):
    header = stream.readline(128)
    match = HEADER.fullmatch(header)
    require(match is not None, "BATCH_HEADER")
    size = int(match[2])
    require(size <= MAX_BLOB, "BATCH_CAP")
    pieces = []
    left = size
    while left:
        part = stream.read(left)
        require(part and len(part) <= left, "PARTIAL_FRAME")
        pieces.append(part)
        left -= len(part)
    return header, b"".join(pieces), stream.read(1)


def accept_reply(ticket, received):
    sequence, data = received
    require(sequence == ticket and data is not None, "STALE_OR_FAILED_EXCHANGE")
    return data


class Batch:
    """One fresh pipe exchange per call; a failed/late exchange poisons reader."""
    def __init__(self, root, originals, digest):
        self.originals, self.digest = originals, digest
        self.sequence = 0
        self.poisoned = False
        self.proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                                     env=environment(), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)

    def get(self, path):
        require(not self.poisoned and path in MANIFEST and self.sequence < MAX_READS, "BATCH_STATE")
        self.sequence += 1
        ticket = self.sequence
        reply = queue.Queue(maxsize=1)

        def exchange():
            try:
                require(self.proc.poll() is None, "BATCH_EXIT")
                request = (MANIFEST[path][0] + "\n").encode("ascii")
                require(self.proc.stdin.write(request) == len(request), "SHORT_WRITE")
                self.proc.stdin.flush()
                reply.put((ticket, frame(self.proc.stdout)))
            except Exception:
                reply.put((ticket, None))

        worker = threading.Thread(target=exchange, daemon=True)
        worker.start()
        try:
            data = accept_reply(ticket, reply.get(timeout=READ_SECONDS))
            # No shared result store; validate fresh response on every invocation.
            return verify_frame(path, *data, self.originals, self.digest)
        except Exception:
            self.poisoned = True
            raise

    def close(self):
        # Never flush/close a pipe that may still be blocked before killing Git.
        if self.poisoned and self.proc.poll() is None:
            self.proc.kill()
        if not self.poisoned:
            self.proc.stdin.close()
        try:
            code = self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=3)
            self.poisoned = True
            code = self.proc.returncode
        self.proc.stdout.close()
        if not self.proc.stdin.closed:
            self.proc.stdin.close()
        require(code == 0 and not self.poisoned, "BATCH_CLEAN_EXIT")


def transport(root, batch, original, counts):
    def limited(*args, **kwargs):
        path = intercept_path(args, kwargs, root)
        if path is None:
            counts["delegated_calls"] += 1
            return original(*args, **kwargs)  # native bytes, errors and negative exits unchanged
        raw = batch.get(path)
        counts["fresh_validated_reads"] += 1
        by_path = counts.setdefault("reads_by_path", {})
        by_path[path] = by_path.get(path, 0) + 1
        return raw
    return limited


def bootstrap(root):
    from tests import phase8_byok_b_scope_migration as gate
    from tests import phase10_perception_scope_migration as successor
    require(gate.ROOT == root and successor.PARENT == B and successor.PARENT_TREE == B_TREE,
            "SOURCE_ROOT_OR_B")
    require(set(gate.ENVELOPE) == set(MANIFEST) and gate.CANDIDATE_SHA256
            == {p: v[1] for p, v in MANIFEST.items()}, "FIXED_ORIGINAL_PINS")
    # Original uninstrumented seal/tag/commit/tree/pin authentication. This is
    # immutable fixture provenance only, NEVER a remembered admission success.
    tree = successor._baseline()
    originals = {}
    for path, (oid, _) in MANIFEST.items():
        require(tree.get(path) == ("100644", oid), "FIXED_TREE_BLOB")
        raw = git(root, "show", B + ":" + path)
        verify_frame(path, f"{oid} blob {len(raw)}\n".encode("ascii"), raw, b"\n",
                     {path: raw}, gate._digest)
        originals[path] = raw  # comparison witness only, NEVER served to caller
    return originals, gate._digest


class Job:
    """Win32 Job Object: assign before handshake; all descendants remain owned."""
    def __init__(self):
        require(sys.platform == "win32", "WINDOWS_JOB_REQUIRED")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        k = self.k
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                              ctypes.c_void_p, wintypes.DWORD]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
        k.QueryInformationJobObject.restype = wintypes.BOOL
        k.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.TerminateJobObject.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL

        class Basic(ctypes.Structure):
            _fields_ = [("per_process", ctypes.c_longlong), ("per_job", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("min_ws", ctypes.c_size_t),
                        ("max_ws", ctypes.c_size_t), ("active_limit", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]

        self.handle = k.CreateJobObjectW(None, None)
        require(self.handle, "JOB_CREATE")
        limits = Extended()
        limits.basic.flags = 0x2000 | 0x8 | 0x200  # kill-on-close, active limit, job memory
        limits.basic.active_limit = 32
        limits.job_memory = 1024 * 1024 * 1024
        try:
            require(k.SetInformationJobObject(self.handle, 9, ctypes.byref(limits),
                                              ctypes.sizeof(limits)), "JOB_LIMITS")
        except Exception:
            k.CloseHandle(self.handle)
            raise

    def assign(self, proc):
        require(self.k.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(proc._handle))),
                "JOB_ASSIGN")

    def active(self):
        class Accounting(ctypes.Structure):
            _fields_ = [(n, ctypes.c_longlong) for n in ("user", "kernel", "period_user", "period_kernel")] + [
                (n, wintypes.DWORD) for n in ("faults", "total", "active", "terminated")]
        info = Accounting()
        require(self.k.QueryInformationJobObject(self.handle, 1, ctypes.byref(info),
                                                 ctypes.sizeof(info), None), "JOB_QUERY")
        return info.active

    def terminate(self):
        require(self.k.TerminateJobObject(self.handle, 125), "JOB_TERMINATE")

    def close(self):
        require(self.k.CloseHandle(self.handle), "JOB_CLOSE")


def contained(source, private, seconds=SECONDS, job_factory=Job):
    """180s starts at spawn, includes handshake, verification/import/body/postflight."""
    require(seconds == SECONDS, "ORIGINAL_BUDGET")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "_child",
               "--source", str(source), "--output", str(private)]
    record = {"timed_out": False, "tree_cleanup": "UNCERTAIN", "aborted": False,
              "residual_descendants_after_root_exit": False,
              "configured_whole_child_seconds": SECONDS, "actual_process_exit": None}
    proc = None
    job = job_factory()
    began = time.monotonic()
    try:
        with (private / "candidate.log").open("wb") as sink:
            proc = subprocess.Popen(command, cwd=source, env=environment(), stdin=subprocess.PIPE,
                                    stdout=sink, stderr=subprocess.STDOUT)
            job.assign(proc)
            require(job.active() == 1, "JOB_HANDSHAKE")
            proc.stdin.write(b"!")
            proc.stdin.close()
            while proc.poll() is None:
                if time.monotonic() - began >= seconds:
                    record["timed_out"] = True
                    break
                require((private / "candidate.log").stat().st_size <= MAX_LOG, "LOG_CAP")
                time.sleep(0.1)
    except Exception:
        record["aborted"] = True
    finally:
        try:
            # A clean root exit with live descendants is a diagnostic failure,
            # even if those descendants can later be terminated successfully.
            active_before_cleanup = job.active()
            if (active_before_cleanup and proc is not None and proc.poll() is not None
                    and not record["timed_out"]):
                record["residual_descendants_after_root_exit"] = True
            if active_before_cleanup:
                job.terminate()
            end = time.monotonic() + 5
            while job.active() and time.monotonic() < end:
                time.sleep(0.05)
            if job.active() == 0:
                record["tree_cleanup"] = "JOB_EMPTY_CONFIRMED"
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()  # retained root handle only; assignment failure cannot launch Git
                proc.wait(timeout=5)
                record["actual_process_exit"] = proc.returncode
        except Exception:
            record["tree_cleanup"] = "UNCERTAIN"
        finally:
            try:
                job.close()
            except Exception:
                record["tree_cleanup"] = "UNCERTAIN"
            # Even a failed job query/assignment retains a bounded root handle.
            if proc is not None and record["actual_process_exit"] is None:
                try:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=5)
                    record["actual_process_exit"] = proc.returncode
                except Exception:
                    record["tree_cleanup"] = "UNCERTAIN"
        record["elapsed_seconds_including_cleanup"] = round(time.monotonic() - began, 3)
    return record


def child(source, private):
    require(sys.stdin.buffer.read(1) == b"!", "SUPERVISOR_HANDSHAKE")
    original = load_original()
    before = original.verify_source(source)
    write(private / "source-before.json", before)
    sys.path.insert(0, str(source))
    originals, digest = bootstrap(source)
    counts = {"fresh_validated_reads": 0, "delegated_calls": 0}
    batch = Batch(source, originals, digest)
    result = None
    try:
        with mock.patch.object(subprocess, "check_output",
                               transport(source, batch, subprocess.check_output, counts)):
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromName(TEST)
            require(not loader.errors and suite.countTestCases() == 1, "ONE_G1_ONLY")
            with (private / "events.jsonl").open("w", encoding="utf8") as journal:
                original.JournalResult.journal = journal
                result = unittest.TextTestRunner(verbosity=2, resultclass=original.JournalResult).run(suite)
    finally:
        # Persist the actual test outcome even if batch teardown then fails.
        # Infrastructure failure can withhold evidence; it cannot erase a FAIL.
        if result is not None:
            code = 0 if result.wasSuccessful() else 1
            status = {"assigned": [TEST], "tests_run": result.testsRun, "original_unittest_exit": code,
                      "failures": [t.id() for t, _ in result.failures],
                      "errors": [t.id() for t, _ in result.errors],
                      "skips": [t.id() for t, _ in result.skipped],
                      "expected_failures": [t.id() for t in result.expectedFailures],
                      "unexpected_successes": [t.id() for t in result.unexpectedSuccesses]}
            write(private / "result.json", status)
        try:
            batch.close()
        finally:
            write(private / "metrics.json", dict(counts, baseline_real_git_show_calls=23,
                  manifest={p: {"git_blob": v[0], "original_normalized_sha256": v[1],
                                "original_show_raw_sha256": sha(originals[p])} for p, v in MANIFEST.items()}))
    require(counts["fresh_validated_reads"] > 0, "NO_INTERCEPTION")
    require(original.verify_source(source) == before, "SOURCE_CHANGED")
    write(private / "verified.json", {"before_after_equal": True})
    return code


def classify(process, result, events, original):
    if (process["tree_cleanup"] != "JOB_EMPTY_CONFIRMED" or process["aborted"]
            or process.get("residual_descendants_after_root_exit", False)):
        return {"status": "TIMEOUT" if process["timed_out"] else "INSTRUMENTATION_ERROR"}, 125
    # Preserve original P234 outcome rules, including timeout, negative exits,
    # skips and unexpected successes. Rename only the surrounding evidence mode.
    summary, code = original.classify(process, result, events, TEST)
    if code:
        return summary, code
    return summary, 3 if summary["status"] == "PASS" else 125


def observe(source, output):
    root = Path(__file__).resolve().parents[1]
    source = source.resolve(strict=True)
    output = output.resolve()
    require(not output.is_relative_to(root) and not output.is_relative_to(source)
            and not root.is_relative_to(source) and not source.is_relative_to(root), "PATH_SEPARATION")
    output.mkdir(exist_ok=False)
    report = {"scope": "INSTRUMENTED CANDIDATE", "test_body_unchanged": True,
              "original_git_transport_instrumented": True, "source": SOURCE,
              "test_id": TEST, "release": "HOLD", "full_unfiltered_regressions": "0/3",
              "independent_SEC03_SEC04": "MISSING", "exit": 125,
              "p237_comparator": {"run": "43704008072", "status": "TIMEOUT",
                  "observer_exit": 125, "git_sessions": 4154, "show": 2524, "cat_file": 560,
                  "sum_git_t_abs_approx_seconds": 105.883,
                  "max_completed_git_t_abs_upper_seconds": 0.085,
                  "provenance": "USER_SUPPLIED; NOT_REEXECUTED_OR_REAUTHENTICATED_HERE"}}
    try:
        controller = provenance(root)
        report["controller"] = controller
        runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
        private = Path(tempfile.mkdtemp(prefix="p238-private-", dir=runner_temp)).resolve()
        require(not private.is_relative_to(root) and not private.is_relative_to(source)
                and not output.is_relative_to(private), "PRIVATE_SEPARATION")
        process = contained(source, private)
        report["process"] = process
        original = load_original()
        result = json.loads(read(private / "result.json")) if (private / "result.json").exists() else None
        if result is not None:
            report["recorded_candidate_unittest_exit"] = result["original_unittest_exit"]
        events = [json.loads(x) for x in read(private / "events.jsonl").splitlines()] if (
            private / "events.jsonl").exists() else []
        summary, code = classify(process, result, events, original)
        report["candidate_result"] = summary
        report["exit"] = code
        if code == 3:
            require(json.loads(read(private / "verified.json")) == {"before_after_equal": True}, "POSTVERIFY")
            metrics = json.loads(read(private / "metrics.json"))
            require(0 < metrics["fresh_validated_reads"] <= MAX_READS, "READ_COUNT")
            require(set(metrics["reads_by_path"]) == set(MANIFEST)
                    and all(type(n) is int and n > 0 for n in metrics["reads_by_path"].values())
                    and sum(metrics["reads_by_path"].values()) == metrics["fresh_validated_reads"],
                    "EXACT_PATH_COVERAGE")
            report["metrics"] = metrics
            witness = read(private / "source-before.json")
            (output / "source-witness.json").write_bytes(witness)
        # Raw stdout, tracebacks, argv and user paths stay private. Only hashes
        # and fixed public schema leave runner temp; no recursive raw upload.
        report["raw_private_sha256"] = {p.name: sha(read(p)) for p in private.iterdir()}
        require(provenance(root) == controller, "CONTROLLER_CHANGED")
    except Exception:
        report.update(exit=125, error="SOURCE_CONTAINMENT_INSTRUMENTATION_OR_RESULT_REFUSED")
    finally:
        write(output / "candidate.json", report)
        write(output / "receipts.json", {p.name: sha(read(p)) for p in output.iterdir()
                                        if p.name != "receipts.json"})
        print("P238_INSTRUMENTED_CANDIDATE_EXIT=" + str(report["exit"]) + "|ALL_C1_GATES_HOLD")
    return report["exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("guard", "observe", "_child"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "guard":
        write(args.output / "controller-guard.json", provenance(Path(__file__).resolve().parents[1]))
        return 0  # source guard only, no candidate or release result
    if args.mode == "_child":
        return child(args.source.resolve(strict=True), args.output.resolve(strict=True))
    return observe(args.source, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
