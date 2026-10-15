"""A-04: true killed-process recovery evidence, fake-only and test-scoped.

Windows parent owns the isolated TemporaryDirectory. Child A is force-killed
without controller.close; Child B is a new Python process with fresh pools.
No real provider, key, native mutex or network operation is authorised.
"""
from pathlib import Path
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
import hashlib
import json
from queue import Empty, Queue
from threading import Thread
import os
import stat
import subprocess
import sys
import unittest

from nayeon.brain.onboarding_recovery_document import (
    RecoveryRecord, RecoveryState, encode_frame, record_hash,
)
from nayeon.brain.onboarding_recovery_store import OnboardingRecoveryJournalStore

REPO = Path(__file__).resolve().parents[1]
CHILD_MODULE = "tests.a04_recovery_subprocess_child"
EFFECT = b"A04_FAKE_EFFECT_ONCE\n"
CASES = (
    ("ready", "ready", "normal", "ready", 0, False),
    ("inflight_before", "inflight_before", "normal", "in_flight", 0, True),
    ("inflight_after", "inflight_after", "normal", "in_flight", 1, True),
    ("reconciling", "reconciling", "normal", "reconciling", 0, True),
    ("marker", "ready", "normal", "ready", 0, True),
    ("marker_only", "ready", "normal", "missing", 0, True),
    ("missing", "ready", "normal", "missing", 0, False),
    ("corrupt", "ready", "normal", "unreadable", 0, None),
    ("truncated", "ready", "normal", "unreadable", 0, None),
    ("conflict", "ready", "normal", "unreadable", 0, None),
    ("abandoned", "ready", "abandoned", "ready", 0, True),
    ("archive", "ready", "normal", "ready", 0, False),
    ("exit_failure", "ready", "exit_failure", "ready", 0, False),
    ("bad_reopen", "ready", "normal", "unreadable", 0, None),
)


def _checked_root(path: Path):
    # Parent owns only a direct, test-named system TEMP child. All mutations
    # are confined within this root; never attempt cleanup of arbitrary paths.
    from tempfile import gettempdir
    assert path.is_dir() and path.resolve() == path and not path.is_symlink()
    assert path.parent == Path(gettempdir()).resolve()
    assert path.name.startswith("nayeon-a04-")


def _directory_identity(path):
    """Parent witness for a canonical non-reparse directory, not its name."""
    info = path.lstat()
    assert path.is_dir() and not path.is_symlink()
    assert not (getattr(info, "st_file_attributes", 0) & 0x400)
    return [info.st_dev, info.st_ino]


def _bootstrap_file_identity(path):
    """Pinned regular-file identity for this disposable child launcher."""
    import stat
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or
            getattr(info, "st_file_attributes", 0) & 0x400 or
            info.st_size <= 0):
        raise AssertionError("A04_UNTRUSTED_BOOTSTRAP_FILE")
    return [info.st_dev, info.st_ino, info.st_size]


def _parent_evidence(path, limit, *, required=False):
    """Bounded regular non-reparse evidence; reject changed path/fd identity."""
    if type(limit) is not int or not 0 <= limit <= 131072:
        raise AssertionError("A04_PARENT_EVIDENCE_LIMIT")
    try:
        before = path.lstat()
    except FileNotFoundError:
        if required:
            raise AssertionError("A04_PARENT_EVIDENCE_MISSING")
        return None
    if (not stat.S_ISREG(before.st_mode) or
            bool(getattr(before, "st_file_attributes", 0) & 0x400) or
            not 0 <= before.st_size <= limit):
        raise AssertionError("A04_PARENT_EVIDENCE_UNTRUSTED")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read(limit + 1)
        after = path.lstat()
    if (not stat.S_ISREG(opened.st_mode) or
            not stat.S_ISREG(after.st_mode) or
            bool(getattr(after, "st_file_attributes", 0) & 0x400) or
            len(data) > limit or len(data) != before.st_size or
            len(data) != after.st_size or
            (before.st_dev, before.st_ino) !=
            (opened.st_dev, opened.st_ino) or
            (after.st_dev, after.st_ino) !=
            (opened.st_dev, opened.st_ino)):
        raise AssertionError("A04_PARENT_EVIDENCE_CHANGED")
    return data


def _bootstrap_pins(executable, support):
    """Parent-owned child bootstrap witness; not a generic code sandbox."""
    if not (REPO.is_dir() and REPO == REPO.resolve() and
            support == (REPO / "tests" / "a04_recovery_test_support.py") and
            support == support.resolve() and executable == executable.resolve()):
        raise AssertionError("A04_BOOTSTRAP_PARENT_PATH")
    identity = _bootstrap_file_identity(support)
    if identity[2] > 131072:
        raise AssertionError("A04_BOOTSTRAP_SUPPORT_OVERSIZE")
    return {
        "repo_path": str(REPO), "repo_id": _directory_identity(REPO),
        "support_path": str(support), "support_id": identity,
        "support_sha": hashlib.sha256(
            _parent_evidence(support, 131072, required=True)).hexdigest(),
        "python_path": str(executable),
        "python_id": _bootstrap_file_identity(executable),
    }


def _journal(path):
    return OnboardingRecoveryJournalStore(path / "provider.json.nayeon-recovery-journal")


def _archive_fixture(path):
    journal = _journal(path)
    records = journal.read()
    assert records and records[-1].state is RecoveryState.READY
    last = records[-1]
    body = bytearray(_parent_evidence(journal.path, 131072, required=True))
    # Additional nonsecret READY frames, all correctly hash-linked.
    for sequence in range(last.sequence + 1, 126):
        nxt = RecoveryRecord(
            schema_version=1, sequence=sequence, epoch=last.epoch,
            generation=last.generation, state=RecoveryState.READY,
            previous_hash=record_hash(last),
            evidence_hash=last.evidence_hash)
        body.extend(encode_frame(nxt))
        last = nxt
    assert len(body) < 131072
    with journal.path.open("wb") as f:
        assert f.write(body) == len(body)
        f.flush()
        os.fsync(f.fileno())
    assert journal.read()[-1] == last
    assert journal.archive_required(journal.read())


def _parent_fault(path, scenario):
    _checked_root(path)
    journal = _journal(path).path
    if scenario in ("marker", "marker_only"):
        marker = path / "provider.json.nayeon-onboarding-inflight"
        with marker.open("xb") as f:
            f.write(b"")
            f.flush()
            os.fsync(f.fileno())
        if scenario == "marker_only":
            journal.unlink()
    elif scenario == "missing":
        journal.unlink()
    elif scenario == "corrupt":
        journal.write_bytes(b"INVALID_SYNTHETIC_JOURNAL\n")
    elif scenario == "truncated":
        data = _parent_evidence(journal, 131072, required=True)
        assert data.endswith(b"\n")
        journal.write_bytes(data[:-7])
    elif scenario == "conflict":
        data = _parent_evidence(journal, 131072, required=True)
        first = data.splitlines(keepends=True)[0]
        with journal.open("ab") as f:
            f.write(first)  # Duplicate sequence/hash-chain; guaranteed invalid.
            f.flush()
            os.fsync(f.fileno())
    elif scenario == "archive":
        _archive_fixture(path)
    elif scenario == "bad_reopen":
        backup = path / "synthetic-journal-backup"
        assert not backup.exists()
        journal.replace(backup)
        journal.mkdir()  # A directory is not a trusted regular journal file.


def _test_child_descendants(pid, launched_after, *, details=False):
    """Fail-closed descendant snapshot bound to THIS child's start tenure.

    Win32_Process.ParentProcessId alone is insufficient after PID reuse:
    a long-lived unrelated process may reference an older, recycled PID.
    """
    if sys.platform != "win32":
        return ()
    if type(launched_after) is not datetime or launched_after.tzinfo is None:
        raise ValueError("A04_CHILD_START_IDENTITY_REQUIRED")
    command = (
        "$ErrorActionPreference='Stop'; "
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,"
        "@{Name='CreatedUtc';Expression={$_.CreationDate.ToUniversalTime().ToString('o')}} | "
        "ConvertTo-Json -Compress")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=5, check=True)
        entries = json.loads(result.stdout)
        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            raise ValueError("Unexpected Windows process snapshot")
        nodes = {int(item["ProcessId"]): item for item in entries}
        edges = {child: int(item["ParentProcessId"])
                 for child, item in nodes.items()}
        found = set()
        # Each newly accepted child's creation instant becomes the threshold
        # for ITS descendants. Comparing grandchildren only to the original
        # Python launch misattributes older processes after intermediate PID
        # reuse, and can falsely reject a genuine OS conhost leaf.
        frontier = {pid: launched_after}
        while frontier:
            next_frontier = {}
            for child, parent in edges.items():
                if parent not in frontier or child in found or child == pid:
                    continue
                raw_time = nodes[child].get("CreatedUtc")
                if type(raw_time) is not str:
                    raise ValueError("A04_DESCENDANT_CREATION_TIME_MISSING")
                created = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                if created.tzinfo is None:
                    raise ValueError("A04_DESCENDANT_CREATION_TIME_NAIVE")
                if created >= frontier[parent]:
                    next_frontier[child] = created
                # A child born before this parent's current tenure belongs
                # to an older recycled PID association, never to this tree.
            found.update(next_frontier)
            frontier = next_frontier
        # CREATE_NO_WINDOW can create exactly one OS-owned conhost.exe.
        # Do not mistake that protected Windows console host for a test child.
        system_conhost = os.path.normcase(os.path.normpath(os.path.join(
            os.environ.get("SystemRoot", r"C:\Windows"),
            "System32", "conhost.exe")))
        def exact_system_console(path):
            if type(path) is not str or not os.path.isabs(path):
                return False
            if os.path.normcase(os.path.normpath(path)) == system_conhost:
                return True
            # Win32_Process may report a different spelling for the same
            # on-disk executable. Permit ONLY an exact file-identity match.
            try:
                return os.path.samefile(path, system_conhost)
            except OSError:
                return False
        unexpected = []
        for child in found:
            item = nodes[child]
            observed_path = item.get("ExecutablePath")
            expected_console = (
                edges[child] == pid and
                str(item.get("Name", "")).casefold() == "conhost.exe" and
                exact_system_console(observed_path) and
                # Only CURRENT-TENURE descendants can disqualify this leaf.
                # An older unrelated process may retain a recycled parent
                # PID equal to this fresh Windows console host's PID.
                not any(edges[descendant] == child for descendant in found
                        if descendant != child))
            if not expected_console:
                unexpected.append(
                    (child, str(item.get("Name")), str(item.get("ExecutablePath")),
                     str(item.get("CreatedUtc")), edges[child])
                    if details else child)
        return tuple(sorted(unexpected))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        raise RuntimeError("A04_DESCENDANT_ENUMERATION_UNAVAILABLE") from exc


class _A04ChildSupervisor:
    """The shared, bounded owner of a Windows child and both pipe readers."""
    LIMIT = 4096
    FRAME_LIMIT = 2048
    _active_owners = set()

    def __init__(self, cmd, *, cwd=REPO, env=None, root=None,
                 expected_frames=1, bootstrap_fault=None):
        import threading
        if (expected_frames not in (1, 2) or
                bootstrap_fault not in (None, "repo", "support", "python")):
            raise ValueError("A04_BOUNDED_EXPECTED_FRAME_COUNT")
        self.expected_frames = expected_frames
        self.root_claim = None
        self.root = Path(root).resolve() if root is not None else None
        self.proc = None
        self.buffers = [bytearray(), bytearray()]
        self.overflow = [False, False]
        self.errors = []
        self.threads = []
        self.cleaned = False
        support = REPO / "tests" / "a04_recovery_test_support.py"
        if root is not None and len(cmd) >= 6 and Path(cmd[4]) == support:
            pins = _bootstrap_pins(Path(cmd[0]), support)
            if bootstrap_fault is not None:
                # Negative-control witness corruption only; no executable or
                # on-disk trusted file is changed.
                pins[bootstrap_fault + "_id"][1] += 1
            env = dict(os.environ if env is None else env)
            env["NAYEON_A04_BOOTSTRAP_PINS"] = json.dumps(
                pins, separators=(",", ":"))
        elif bootstrap_fault is not None:
            raise AssertionError("A04_BOOTSTRAP_FAULT_NOT_SCOPED")
        self.spawn_started_at = datetime.now(timezone.utc)
        try:
            self.proc = subprocess.Popen(
                cmd, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
                creationflags=((subprocess.CREATE_NO_WINDOW |
                                subprocess.CREATE_NEW_PROCESS_GROUP)
                               if sys.platform == "win32" else 0))
            self._active_owners.add(self)
            for i, stream in enumerate((self.proc.stdout, self.proc.stderr)):
                thread = threading.Thread(
                    target=self._read, args=(i, stream),
                    name="a04-supervisor-" + ("stdout" if i == 0 else "stderr"),
                    daemon=True)
                self.threads.append(thread)  # Own it before start() can fail.
                thread.start()
        except BaseException as original:
            try:
                self.close()
            except BaseException as cleanup:
                original.add_note("A04 init cleanup: " + repr(cleanup))
            raise

    @classmethod
    def has_unreaped(cls, root):
        return any(owner.root == root for owner in cls._active_owners)

    def _read(self, i, stream):
        try:
            while True:
                chunk = os.read(stream.fileno(), 512)
                if not chunk:
                    return
                remaining = self.LIMIT + 1 - len(self.buffers[i])
                if remaining > 0:
                    self.buffers[i].extend(chunk[:remaining])
                if len(chunk) > remaining or len(self.buffers[i]) > self.LIMIT:
                    self.overflow[i] = True
                    if self.proc is not None and self.proc.poll() is None:
                        self.proc.kill()
                    return
        except OSError as exc:
            self.errors.append(type(exc).__name__)

    def _check(self):
        if self.errors:
            raise AssertionError("A04_READER_FAILURE: " + repr(self.errors))
        if any(self.overflow):
            raise AssertionError("A04_OUTPUT_OVERFLOW")
        if self.buffers[0].count(b"\n") > self.expected_frames:
            raise AssertionError("A04_EXTRA_STDOUT_FRAMES")

    @staticmethod
    def _parse(raw):
        try:
            value = json.loads(raw.decode("utf8", "strict"))
        except (ValueError, UnicodeError) as exc:
            raise AssertionError("A04_MALFORMED_JSON") from exc
        if not isinstance(value, dict):
            raise AssertionError("A04_MALFORMED_JSON_NONOBJECT")
        return value

    def _await(self, kind, deadline):
        import time
        until = time.monotonic() + deadline
        while time.monotonic() < until:
            self._check()
            if (kind == "barrier" and
                    self.buffers[0].count(b"\n") >= self.expected_frames):
                if self.proc.poll() is not None:
                    raise AssertionError("A04_BARRIER_CHILD_EXITED")
                return
            if kind == "exit" and self.proc.poll() is not None:
                return
            if kind == "barrier" and self.proc.poll() is not None:
                self._join_readers()
                raise AssertionError(
                    "A04_BARRIER_CHILD_EXITED_BEFORE_SIGNAL"
                    + " exit=" + str(self.proc.returncode)
                    + " stderr=" + bytes(self.buffers[1])[-1000:].decode(
                        "utf8", "replace"))
            time.sleep(.01)
        raise AssertionError("A04_" + kind.upper() + "_TIMEOUT")

    def barrier(self, *, timeout=8):
        self._await("barrier", timeout)
        frames = bytes(self.buffers[0]).splitlines(keepends=True)
        if len(frames) != self.expected_frames:
            raise AssertionError("A04_BARRIER_FRAME_COUNT")
        if any(not frame.endswith(b"\n") or len(frame) > self.FRAME_LIMIT
               for frame in frames):
            raise AssertionError("A04_BARRIER_FRAME_SIZE")
        if self.expected_frames == 2:
            claim = self._parse(frames[0])
            if claim.get("kind") != "ROOT_CLAIM":
                raise AssertionError("A04_MISSING_EARLY_ROOT_CLAIM")
            self.root_claim = claim
        return self._parse(frames[-1])

    def single_message(self):
        self._check()
        data = bytes(self.buffers[0])
        if (not data.endswith(b"\n") or
                data.count(b"\n") != self.expected_frames or
                any(len(frame) > self.FRAME_LIMIT
                    for frame in data.splitlines(keepends=True))):
            raise AssertionError("A04_NOT_EXACTLY_EXPECTED_BOUNDED_FRAMES")
        if self.buffers[1]:
            raise AssertionError("A04_UNEXPECTED_CHILD_STDERR: " +
                                 bytes(self.buffers[1])[-500:].decode("utf8", "replace"))
        return self._parse(data.splitlines(keepends=True)[-1])

    def result(self, *, timeout=9):
        self._await("exit", timeout)
        self.proc.wait(timeout=4)
        self._join_readers()
        if self.proc.returncode != 0:
            raise AssertionError("A04_B_EXIT: " + str(self.proc.returncode) +
                " stderr=" + bytes(self.buffers[1])[-500:].decode("utf8", "replace"))
        return self.single_message()

    def _join_readers(self):
        failures = []
        for t in self.threads:
            if t.ident is None:
                continue  # Created but start() failed.
            try:
                t.join(timeout=2)
                if t.is_alive():
                    failures.append("reader still alive: " + t.name)
            except BaseException as exc:
                failures.append("reader join: " + repr(exc))
        if failures:
            raise RuntimeError("A04_UNJOINED_PIPE_READER: " + repr(failures))

    def close(self):
        if self.cleaned:
            return
        failures = []
        if self.proc is not None and self.root is not None:
            try:
                descendants = _test_child_descendants(
                    self.proc.pid, self.spawn_started_at, details=True)
                if descendants:
                    failures.append("unexpected child descendants: " + repr(descendants))
            except BaseException as exc:
                failures.append("descendant inspection: " + repr(exc))
        if self.proc is not None:
            if self.proc.poll() is None:
                try:
                    self.proc.kill()
                except BaseException as exc:
                    failures.append("kill: " + repr(exc))
            try:
                self.proc.wait(timeout=4)
            except BaseException as exc:
                failures.append("wait: " + repr(exc))
        try:
            self._join_readers()
        except BaseException as exc:
            failures.append("join: " + repr(exc))
        if self.proc is not None:
            for name in ("stdout", "stderr"):
                stream = getattr(self.proc, name, None)
                if stream is not None:
                    try:
                        stream.close()
                    except BaseException as exc:
                        failures.append(name + " close: " + repr(exc))
        if self.proc is not None and self.proc.poll() is None:
            failures.append("child is not reaped")
        if any(t.is_alive() for t in self.threads):
            failures.append("reader is still alive")
        if failures:
            raise RuntimeError("A04_CLEANUP_INCOMPLETE pid=" +
                               str(self.proc.pid if self.proc else None) +
                               ": " + repr(failures))
        self.cleaned = True
        self._active_owners.discard(self)

    def __enter__(self):
        return self

    def __exit__(self, kind, original, traceback):
        try:
            self.close()
        except BaseException as cleanup:
            if original is None:
                raise
            original.add_note("A04 supervisor cleanup failed: " + repr(cleanup))
        return False



def _retention_notice(root, reason):
    """Bounded parent-owned synthetic evidence receipt, never a credential log."""
    try:
        _checked_root(root)
        target = root / "a04-retained-evidence.txt"
        if target.exists() or target.is_symlink():
            return "A04_RECEIPT_ALREADY_PRESENT"
        with target.open("xb") as stream:
            payload = ("A04_RETAINED_FOR_MANUAL_REVIEW\n" +
                       reason[:256] + "\n").encode("utf8", "replace")
            assert len(payload) <= 320
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return "A04_RETENTION_RECEIPT_WRITTEN"
    except BaseException as exc:
        return "A04_RETENTION_RECEIPT_UNAVAILABLE: " + repr(exc)[:120]


def _cleanup_a04_test_root(temp, a, b):
    """Never erase evidence of an unreaped child or mask the original failure."""
    root = Path(temp.name).resolve()
    original = sys.exc_info()[1]
    if (not all(child is None or child.cleaned for child in (a, b))
            or _A04ChildSupervisor.has_unreaped(root)):
        detail = "A04_UNREAPED_CHILD_ROOT_RETAINED: " + str(root)
        detail += " [" + _retention_notice(root, detail) + "]"
        if original is not None:
            original.add_note(detail)
            return
        raise AssertionError(detail)
    try:
        temp.cleanup()
    except BaseException as cleanup:
        if original is not None:
            status = _retention_notice(root, "cleanup failure: " + repr(cleanup))
            original.add_note("A04 temporary root cleanup failed; retained=" +
                              str(root) + ": " + repr(cleanup) + " [" + status + "]")
            return
        _retention_notice(root, "cleanup failure: " + repr(cleanup))
        raise


def _run_child(phase, root, scenario, mode):
    # The legacy matrix must enter the SAME guarded, identity-pinned bootstrap
    # used by the exact-factory matrix; never launch its product imports via -m.
    import secrets
    support = REPO / "tests" / "a04_recovery_test_support.py"
    env = dict(os.environ)
    cmd = [getattr(sys, "_base_executable", sys.executable),
           "-I", "-S", "-B", str(support), "L", str(root), phase,
           secrets.token_hex(16), mode, scenario]
    return _A04ChildSupervisor(cmd, cwd=REPO, env=env, root=root)


class GenuineTwoProcessRecoveryAcceptance(unittest.TestCase):
    def test_real_process_crash_restart_matrix(self):
        if sys.platform != "win32":
            self.skipTest("Authentic Windows TerminateProcess acceptance only")
        for scenario, a_mode, b_mode, expected_state, expected_effects, uncertain in CASES:
            with self.subTest(scenario=scenario):
                temp = TemporaryDirectory(prefix="nayeon-a04-", delete=False)
                a = b = None
                try:
                    root = Path(temp.name).resolve()
                    _checked_root(root)
                    a = _run_child("A", root, a_mode, "normal")
                    with a:
                        signal = a.barrier(timeout=4)
                        self.assertEqual(signal["pid"], a.proc.pid)
                        self.assertIn(signal["barrier"],
                                      {"READY", "IN_FLIGHT_NO_EFFECT",
                                       "IN_FLIGHT_FAKE_EFFECT_PERSISTED", "RECONCILING"})
                    self.assertEqual(a.single_message(), signal,
                                     "Extra post-barrier output forbidden")
                    self.assertNotEqual(a.proc.returncode, 0)
                    self.assertEqual(signal["barrier"],
                                     {"ready":"READY","inflight_before":"IN_FLIGHT_NO_EFFECT",
                                      "inflight_after":"IN_FLIGHT_FAKE_EFFECT_PERSISTED",
                                      "reconciling":"RECONCILING"}[a_mode])
                    self.assertEqual(_journal(root).read()[-1].state.value,
                                     {"ready":"ready","inflight_before":"in_flight",
                                      "inflight_after":"in_flight",
                                      "reconciling":"reconciling"}[a_mode])
                    effect = root / "fake-effects.log"
                    observed = _parent_evidence(effect, len(EFFECT))
                    self.assertEqual(observed, EFFECT if expected_effects else None)
                    before_sha = hashlib.sha256(observed or b"").hexdigest()
                    _parent_fault(root, scenario)
                    b = _run_child("B", root, scenario, b_mode)
                    with b:
                        reply = b.result(timeout=9)
                        self.assertEqual(reply["phase"], "CHILD_B")
                        self.assertEqual(reply["pid"], b.proc.pid)
                        self.assertFalse(reply["initial_ready"])
                        self.assertTrue(reply["stale_admission_denied"])
                        self.assertEqual(reply["prior_state"], expected_state)
                        self.assertEqual(reply["effect_count"], expected_effects)
                        self.assertEqual(reply["forbidden_attempt_count"], 0)
                        self.assertEqual(reply["uncertain"], uncertain)
                        self.assertEqual(reply["review_requested"],
                                         scenario not in {"corrupt","truncated",
                                                          "conflict","bad_reopen"})
                        self.assertEqual(reply["approved"],
                                         scenario not in {"corrupt","truncated",
                                                          "conflict","bad_reopen"})
                    now = _parent_evidence(effect, len(EFFECT))
                    self.assertEqual(hashlib.sha256(now or b"").hexdigest(), before_sha)
                    self.assertEqual(now, observed, "Synthetic effect replay forbidden")
                finally:
                    _cleanup_a04_test_root(temp, a, b)


class LegacyEffectLedgerNegatives(unittest.TestCase):
    """Reject malformed ledger presence after an authentic Child A death."""

    def test_existing_empty_and_partial_ledgers_are_not_absent(self):
        if sys.platform != "win32":
            self.skipTest("Windows fake-only crash/restart acceptance")
        for invalid in (b"", b"A04_FAKE_"):
            with self.subTest(invalid=invalid):
                temp = TemporaryDirectory(prefix="nayeon-a04-", delete=False)
                a = b = None
                try:
                    root = Path(temp.name).resolve()
                    _checked_root(root)
                    a = _run_child("A", root, "ready", "normal")
                    with a:
                        barrier = a.barrier(timeout=4)
                        self.assertEqual(barrier["barrier"], "READY")
                    self.assertNotEqual(a.proc.returncode, 0)
                    effect = root / "fake-effects.log"
                    self.assertIsNone(_parent_evidence(effect, len(EFFECT)))
                    effect.write_bytes(invalid)
                    self.assertEqual(
                        _parent_evidence(effect, len(EFFECT), required=True),
                        invalid)
                    b = _run_child("B", root, "ready", "normal")
                    with self.assertRaisesRegex(
                            AssertionError,
                            r"(?s)A04_B_EXIT.*A04_INVALID_SYNTHETIC_EFFECT_SHAPE"):
                        with b:
                            b.result(timeout=9)
                    self.assertEqual(
                        _parent_evidence(effect, len(EFFECT), required=True),
                        invalid)
                    self.assertIs(_journal(root).read()[-1].state,
                                  RecoveryState.READY)
                finally:
                    _cleanup_a04_test_root(temp, a, b)


class ExactA02FactoryCrashAcceptance(unittest.TestCase):
    """Genuine exact A-02 integration across two independent Windows processes."""

    def test_exact_a02_factory_real_crash_fresh_child_b(self):
        for scenario in ("ready","before_effect","after_effect","fsync_fault",
                         "write_fault","pre_flush_fault","flush_fault",
                         "post_fsync_fault","close_report_fault",
                         "reopen_fault","readback_fault","decode_fault",
                         "abandoned_fsync_fault","release_report_fault"):
            with self.subTest(scenario=scenario):
                self._exercise(scenario)

    def _exercise(self, scenario):
        if sys.platform != "win32":
            self.skipTest("Authentic Windows TerminateProcess acceptance only")
        import secrets
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        support = REPO / "tests" / "a04_recovery_test_support.py"
        self.assertTrue(support.is_file())
        nonce = secrets.token_hex(16)
        temp = TemporaryDirectory(prefix="nayeon-a04-container-", delete=False)
        a = b = None
        try:
            outer = Path(temp.name).resolve()
            outer_id = _directory_identity(outer)
            env = {**os.environ, "TEMP":str(outer),"TMP":str(outer),
                   "TMPDIR":str(outer)}
            argv = [getattr(sys, "_base_executable", sys.executable),
                    "-I","-S","-B",str(support)]
            a = _A04ChildSupervisor(
                argv + ["A",str(outer),"-",nonce,"-",scenario],
                cwd=REPO,env=env,root=outer,expected_frames=2)
            with a:
                barrier = a.barrier(timeout=8)
                claim = a.root_claim
                self.assertIsNotNone(claim)
                self.assertEqual(claim["phase"], "A")
                self.assertEqual(claim["nonce"], nonce)
                self.assertEqual(claim["pid"], a.proc.pid)
                self.assertEqual(claim["outer_id"], outer_id)
                self.assertEqual(claim["inner"], barrier["inner"])
                self.assertEqual(claim["inner_id"], barrier["inner_id"])
                self.assertEqual(barrier["phase"], "A")
                self.assertEqual(barrier["nonce"], nonce)
                self.assertEqual(barrier["pid"], a.proc.pid)
                self.assertEqual(barrier["outer_id"], outer_id)
                self.assertEqual(barrier["barrier"], {
                    "ready":"READY","before_effect":"BEFORE_FAKE",
                    "after_effect":"AFTER_FAKE","fsync_fault":"FSYNC_FAULT",
                    "write_fault":"WRITE_FAULT","pre_flush_fault":"PRE_FLUSH_FAULT",
                    "flush_fault":"FLUSH_FAULT",
                    "post_fsync_fault":"POST_FSYNC_FAULT",
                    "close_report_fault":"CLOSE_REPORT_FAULT",
                    "reopen_fault":"REOPEN_FAULT",
                    "readback_fault":"READBACK_FAULT",
                    "decode_fault":"DECODE_FAULT",
                    "abandoned_fsync_fault":"ABANDONED_FSYNC_FAULT",
                    "release_report_fault":"RELEASE_REPORT_FAULT"}[scenario])
            self.assertEqual(a.single_message(), barrier)
            self.assertIsNotNone(a.root_claim)
            self.assertEqual(a.root_claim["phase"], "A")
            self.assertEqual(a.root_claim["nonce"], nonce)
            self.assertEqual(a.root_claim["pid"], a.proc.pid)
            self.assertEqual(a.root_claim["inner"], barrier["inner"])
            self.assertEqual(a.root_claim["outer_id"], outer_id)
            self.assertEqual(a.root_claim["inner_id"], barrier["inner_id"])
            self.assertNotEqual(a.proc.returncode, 0)
            self.assertRegex(barrier["epoch"],r"^[0-9a-f]{32}$")
            self.assertRegex(barrier["inner"],r"^nayeon-a02-[A-Za-z0-9_-]+$")
            inner = outer / barrier["inner"]
            self.assertTrue(inner.is_dir() and not inner.is_symlink())
            self.assertEqual(inner.resolve(), inner)
            self.assertEqual(inner.parent, outer)
            inner_id = _directory_identity(inner)
            self.assertEqual(barrier["inner_id"], inner_id)
            self.assertEqual(_directory_identity(outer), outer_id)
            journal = inner / "provider.json.nayeon-recovery-journal"
            raw_a_journal = _parent_evidence(journal, 131072, required=True)
            self.assertLessEqual(len(raw_a_journal), 131072)
            self.assertEqual(barrier["journal_sha"],
                             hashlib.sha256(raw_a_journal).hexdigest())
            self.assertEqual(barrier["journal_bytes"],len(raw_a_journal))
            if scenario == "pre_flush_fault" and barrier["journal_state"] == "unreadable":
                from nayeon.brain.onboarding_recovery_store import RecoveryStoreUnavailable
                with self.assertRaises(RecoveryStoreUnavailable):
                    OnboardingRecoveryJournalStore(journal).read()
                witness = json.dumps({"outer": outer_id, "inner": inner_id},
                                     separators=(",", ":"))
                b = _A04ChildSupervisor(
                    argv + ["B",str(outer),barrier["inner"],nonce,
                            barrier["epoch"],scenario,witness],
                    cwd=REPO,env=env,root=outer)
                with self.assertRaisesRegex(AssertionError, "A04_B_EXIT"):
                    with b:
                        b.result(timeout=9)
                self.assertEqual(_parent_evidence(journal, 131072, required=True),raw_a_journal)
                self.assertFalse((inner / "fake-effects.log").exists())
                return
            entries = OnboardingRecoveryJournalStore(journal).read()
            self.assertIsNotNone(entries)
            previous = (
                RecoveryState.READY if (scenario in (
                    "ready","write_fault","release_report_fault") or
                    (scenario == "pre_flush_fault" and
                     barrier["journal_state"] == "ready")) else
                RecoveryState.RECONCILING if scenario == "abandoned_fsync_fault"
                else RecoveryState.IN_FLIGHT)
            self.assertIs(entries[-1].state, previous)
            if previous is RecoveryState.IN_FLIGHT:
                self.assertEqual(entries[-1].operation_kind, "connect")
                self.assertTrue(entries[-1].operation_id)
            self.assertFalse((inner / "provider.json").exists())
            effect = inner / "fake-effects.log"
            expected = b"A04_FAKE_EFFECT_ONCE\n" if scenario=="after_effect" else b""
            self.assertEqual(_parent_evidence(effect, len(EFFECT)) or b"",expected)
            self.assertEqual({f.name for f in inner.iterdir()},
                             {journal.name}|({effect.name} if expected else set()))
            before_b_journal = _parent_evidence(journal, 131072, required=True)
            before_b_journal_sha = hashlib.sha256(before_b_journal).hexdigest()
            before_b_ledger_sha = hashlib.sha256(expected).hexdigest()
            witness = json.dumps({"outer": outer_id, "inner": inner_id},
                                 separators=(",", ":"))
            b_scenario = ("ready" if scenario == "pre_flush_fault" and
                          previous is RecoveryState.READY else scenario)
            b = _A04ChildSupervisor(
                argv + ["B",str(outer),barrier["inner"],nonce,barrier["epoch"],
                        b_scenario,witness],
                cwd=REPO,env=env,root=outer)
            with b:
                reply = b.result(timeout=9)
                self.assertEqual(reply["phase"],"B")
                self.assertEqual(reply["nonce"],nonce)
                self.assertEqual(reply["pid"],b.proc.pid)
                self.assertEqual(reply["outer_id"],outer_id)
                self.assertEqual(reply["inner_id"],inner_id)
                self.assertEqual(reply["journal_sha"],before_b_journal_sha)
                self.assertEqual(reply["ledger_sha"],before_b_ledger_sha)
                self.assertFalse(reply["initial_ready"])
                self.assertEqual(reply["journal"],previous.value)
                self.assertEqual(reply["journal_sha"],
                                 hashlib.sha256(raw_a_journal).hexdigest())
                self.assertEqual(reply["ledger_sha"],
                                 hashlib.sha256(expected).hexdigest())
                self.assertEqual(reply["uncertain"],
                                 b_scenario not in (
                                     "ready","write_fault","release_report_fault"))
                self.assertEqual(reply["effect_count"],int(scenario=="after_effect"))
                self.assertTrue(reply["fresh_epoch"])
                self.assertTrue(reply["stale_epoch_denied"])
                self.assertEqual(reply["stale_ui_denials"],3)
                self.assertEqual(reply["fresh_b_outcome"],"recovery_required")
                self.assertEqual(reply["effects"],1)
            self.assertEqual(_parent_evidence(effect, len(EFFECT)) or b"",expected)
            self.assertEqual(reply["post_journal_sha"],
                             hashlib.sha256(_parent_evidence(journal, 131072, required=True)).hexdigest())
            after_b = OnboardingRecoveryJournalStore(journal).read()
            self.assertTrue(after_b)
            self.assertIs(after_b[-1].state, RecoveryState.IN_FLIGHT)
            self.assertEqual(after_b[-1].operation_kind, "connect")
            self.assertNotEqual(after_b[-1].epoch, barrier["epoch"])
            self.assertTrue(_parent_evidence(journal, 131072, required=True).startswith(before_b_journal))
            self.assertEqual(_directory_identity(outer), outer_id)
            self.assertEqual(_directory_identity(inner), inner_id)
        finally:
            _cleanup_a04_test_root(temp, a, b)



class A04ParentEvidenceNegatives(unittest.TestCase):
    """The parent must refuse oversized, aliased and changed evidence."""

    def test_bounded_evidence_and_reparse_identity_controls(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        with TemporaryDirectory(prefix="nayeon-a04-parent-check-") as root:
            evidence = Path(root) / "synthetic-evidence"
            evidence.write_bytes(b"A04_ONLY")
            self.assertEqual(_parent_evidence(evidence, 8, required=True),
                             b"A04_ONLY")
            with self.assertRaisesRegex(AssertionError,
                                        "A04_PARENT_EVIDENCE_UNTRUSTED"):
                _parent_evidence(evidence, 7, required=True)
            with self.assertRaisesRegex(AssertionError,
                                        "A04_PARENT_EVIDENCE_MISSING"):
                _parent_evidence(Path(root) / "absent", 8, required=True)
            actual_lstat = Path.lstat
            count = [0]
            def adversarial_lstat(path, *args, **kwargs):
                info = actual_lstat(path, *args, **kwargs)
                if path != evidence:
                    return info
                count[0] += 1
                return SimpleNamespace(
                    st_mode=info.st_mode, st_dev=info.st_dev,
                    st_ino=info.st_ino + (1 if count[0] > 1 else 0),
                    st_size=info.st_size,
                    st_file_attributes=(0x400 if count[0] == 1 else 0))
            with patch.object(Path, "lstat", adversarial_lstat):
                with self.assertRaisesRegex(AssertionError,
                                            "A04_PARENT_EVIDENCE_UNTRUSTED"):
                    _parent_evidence(evidence, 8, required=True)
            count[0] = 0
            def swapped_lstat(path, *args, **kwargs):
                info = actual_lstat(path, *args, **kwargs)
                if path != evidence:
                    return info
                count[0] += 1
                return SimpleNamespace(
                    st_mode=info.st_mode, st_dev=info.st_dev,
                    st_ino=info.st_ino + (1 if count[0] > 1 else 0),
                    st_size=info.st_size, st_file_attributes=0)
            with patch.object(Path, "lstat", swapped_lstat):
                with self.assertRaisesRegex(AssertionError,
                                            "A04_PARENT_EVIDENCE_CHANGED"):
                    _parent_evidence(evidence, 8, required=True)
            self.assertEqual(evidence.read_bytes(), b"A04_ONLY")


class A04GuardedEvidenceSchema(unittest.TestCase):
    """R-class negative evidence and marker-only recovery in the guarded child."""

    def test_marker_only_and_adversarial_sidecars(self):
        if sys.platform != "win32":
            self.skipTest("Windows fake-only restart evidence")
        import secrets
        scenarios = ("marker_only", "missing", "corrupt", "truncated",
                     "bad_ledger", "empty_ledger", "partial_ledger",
                     "orphan_ledger", "marker_directory",
                     "archive_wrong_digest", "archive_only",
                     "unknown_case", "case_alias")
        support = REPO / "tests" / "a04_recovery_test_support.py"
        argv = [getattr(sys, "_base_executable", sys.executable),
                "-I", "-S", "-B", str(support)]
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                temp = TemporaryDirectory(prefix="nayeon-a04-container-",
                                          delete=False)
                a = b = None
                try:
                    outer = Path(temp.name).resolve()
                    outer_id = _directory_identity(outer)
                    nonce = secrets.token_hex(16)
                    env = {**os.environ, "TEMP": str(outer), "TMP": str(outer),
                           "TMPDIR": str(outer)}
                    a = _A04ChildSupervisor(
                        argv + ["A", str(outer), "-", nonce, "-", "ready"],
                        cwd=REPO, env=env, root=outer, expected_frames=2)
                    with a:
                        receipt = a.barrier(timeout=8)
                        self.assertEqual(a.root_claim["outer_id"], outer_id)
                        self.assertEqual(receipt["barrier"], "READY")
                    inner = outer / receipt["inner"]
                    self.assertEqual(receipt["inner_id"], _directory_identity(inner))
                    journal = inner / "provider.json.nayeon-recovery-journal"
                    marker = inner / "provider.json.nayeon-onboarding-inflight"
                    effect = inner / "fake-effects.log"
                    if scenario == "marker_only":
                        journal.unlink()
                        marker.write_bytes(b"")
                    elif scenario == "missing":
                        journal.unlink()
                    elif scenario == "corrupt":
                        journal.write_bytes(b"A04_BAD_JOURNAL\n")
                    elif scenario == "truncated":
                        journal.write_bytes(_parent_evidence(journal, 131072, required=True)[:-5])
                    elif scenario == "bad_ledger":
                        effect.write_bytes(b"A04_FAKE_EFFECT_ONCE\nEXTRA")
                    elif scenario == "empty_ledger":
                        effect.write_bytes(b"")
                    elif scenario == "partial_ledger":
                        effect.write_bytes(b"A04_FAKE_")
                    elif scenario == "orphan_ledger":
                        journal.unlink()
                        effect.write_bytes(b"A04_FAKE_EFFECT_ONCE\n")
                    elif scenario == "marker_directory":
                        marker.mkdir()
                    elif scenario in ("archive_wrong_digest", "archive_only"):
                        records = OnboardingRecoveryJournalStore(journal).read()
                        archive_hash = ("0" * 64 if scenario == "archive_wrong_digest"
                                        else record_hash(records[-1]))
                        journal.rename(inner / (journal.name + ".archive-" +
                                                archive_hash))
                    elif scenario == "unknown_case":
                        (inner / "unexpected.sidecar").write_bytes(b"")
                    elif scenario == "case_alias":
                        (inner / "Provider.JSON").write_bytes(b"")
                    original = {
                        entry.name: _parent_evidence(entry, 131072, required=True)
                        for entry in inner.iterdir() if entry.is_file()}
                    witness = json.dumps({"outer": outer_id,
                                          "inner": receipt["inner_id"]},
                                         separators=(",", ":"))
                    b_scenario = (scenario if scenario in
                                  ("marker_only", "archive_only", "missing")
                                  else "archive_only" if scenario ==
                                  "archive_wrong_digest" else "ready")
                    b = _A04ChildSupervisor(
                        argv + ["B", str(outer), receipt["inner"], nonce,
                                receipt["epoch"], b_scenario, witness],
                        cwd=REPO, env=env, root=outer)
                    if scenario in ("marker_only", "archive_only", "missing"):
                        with b:
                            answer = b.result(timeout=9)
                            self.assertEqual(answer["journal"], "uninitialized")
                            self.assertEqual(answer["uncertain"],
                                             scenario != "missing")
                            self.assertTrue(answer["fresh_epoch"])
                            self.assertTrue(answer["stale_epoch_denied"])
                            self.assertEqual(answer["stale_ui_denials"], 3)
                            self.assertEqual(answer["effects"], 1)
                        if scenario == "marker_only":
                            self.assertFalse(marker.exists())
                        for name, contents in original.items():
                            if name != marker.name:
                                self.assertEqual(_parent_evidence(inner / name, 131072, required=True),
                                                 contents, "Archive evidence changed")
                        self.assertTrue(journal.exists())
                        recovered = OnboardingRecoveryJournalStore(journal).read()
                        self.assertTrue(recovered)
                        self.assertEqual(recovered[-1].state.value, "in_flight")
                        self.assertNotEqual(recovered[-1].epoch, receipt["epoch"])
                    else:
                        rejection = {
                            "corrupt": "RecoveryStoreUnavailable",
                            "truncated": "RecoveryStoreUnavailable",
                            "bad_ledger": "A04_PROBE_UNTRUSTED_SIDECAR",
                            "empty_ledger": "A04_PROBE_PERSISTED_SYNTHETIC_EFFECT",
                            "partial_ledger": "A04_PROBE_PERSISTED_SYNTHETIC_EFFECT",
                            "orphan_ledger": "A04_PROBE_REQUIRED_EVIDENCE_MISSING",
                            "marker_directory": "A04_PROBE_UNTRUSTED_SIDECAR",
                            "archive_wrong_digest": "A04_PROBE_ARCHIVE_HASH_MISMATCH",
                            "unknown_case": "A04_PROBE_UNKNOWN_EVIDENCE_ENTRY",
                            "case_alias": "A04_PROBE_REAL_METADATA_FORBIDDEN",
                        }[scenario]
                        with self.assertRaisesRegex(
                                AssertionError,
                                r"(?s)A04_B_EXIT.*" + rejection):
                            with b:
                                b.result(timeout=9)
                        self.assertEqual(
                            {entry.name: _parent_evidence(entry, 131072, required=True)
                             for entry in inner.iterdir() if entry.is_file()},
                            original, "Refused B altered untrusted sidecar evidence")
                    self.assertEqual(_directory_identity(outer), outer_id)
                    self.assertEqual(_directory_identity(inner), receipt["inner_id"])
                finally:
                    _cleanup_a04_test_root(temp, a, b)


class A04KnownRouteIsolationNegatives(unittest.TestCase):
    """One attempted forbidden route per disposable child, real shared supervisor."""

    def test_bootstrap_identity_refuses_mismatched_witnesses(self):
        if sys.platform != "win32":
            self.skipTest("Windows child bootstrap identity")
        import secrets
        temp = TemporaryDirectory(prefix="nayeon-a04-container-", delete=False)
        child = None
        try:
            outer = Path(temp.name).resolve()
            env = {**os.environ, "TEMP":str(outer), "TMP":str(outer),
                   "TMPDIR":str(outer)}
            support = REPO / "tests" / "a04_recovery_test_support.py"
            python = getattr(sys, "_base_executable", sys.executable)
            for fault, reason in (
                ("repo", "BOOTSTRAP_REPO_IDENTITY"),
                ("support", "BOOTSTRAP_SUPPORT_IDENTITY"),
                ("python", "BOOTSTRAP_INTERPRETER_IDENTITY"),
            ):
                with self.subTest(fault=fault):
                    cmd = [python, "-I", "-S", "-B", str(support),
                           "G", str(outer), "builtin_import",
                           secrets.token_hex(16), "-", "ready"]
                    child = _A04ChildSupervisor(
                        cmd, cwd=REPO, env=env, root=outer,
                        bootstrap_fault=fault)
                    with self.assertRaisesRegex(
                            AssertionError, r"(?s)A04_B_EXIT.*A04_PROBE_" + reason):
                        with child:
                            child.result(timeout=9)
                    self.assertEqual(set(outer.iterdir()), set())
        finally:
            _cleanup_a04_test_root(temp, None, child)

    def test_known_import_io_and_loader_tripwires(self):
        if sys.platform != "win32":
            self.skipTest("Windows child-only known-route isolation")
        import secrets
        routes = ("builtin_import", "module_import", "meta_finder",
                  "socket", "connect", "server", "windll", "windll_attribute",
                  "windll_index", "cdll", "oledll",
                  "loader", "popen", "system", "exec", "native_mutex",
                  "wincred", "provider_sdk")
        temp = TemporaryDirectory(prefix="nayeon-a04-container-", delete=False)
        b = None
        try:
            outer = Path(temp.name).resolve()
            env = {**os.environ, "TEMP": str(outer), "TMP": str(outer),
                   "TMPDIR": str(outer)}
            support = REPO / "tests" / "a04_recovery_test_support.py"
            argv = [getattr(sys, "_base_executable", sys.executable),
                    "-I", "-S", "-B", str(support)]
            for route in routes:
                with self.subTest(route=route):
                    nonce = secrets.token_hex(16)
                    b = _A04ChildSupervisor(
                        argv + ["G", str(outer), route, nonce, "-", "ready"],
                        cwd=REPO, env=env, root=outer)
                    with b:
                        result = b.result(timeout=9)
                        self.assertEqual(result["phase"], "G")
                        self.assertEqual(result["guard"], route)
                        self.assertEqual(result["pid"], b.proc.pid)
                        self.assertEqual(result["nonce"], nonce)
                        self.assertEqual(result["attempts"], 1)
                    self.assertEqual(set(outer.iterdir()), set())
        finally:
            _cleanup_a04_test_root(temp, None, b)


class A04SubprocessSupervisorNegatives(unittest.TestCase):
    """Direct adversarial cases against the same shared A/B supervisor."""

    def test_pid_reuse_stale_parent_is_not_child(self):
        if sys.platform != "win32":
            self.skipTest("Windows parent-PID reuse evidence")
        from datetime import timedelta
        from unittest import mock
        launched = datetime.now(timezone.utc)
        old = (launched - timedelta(minutes=20)).isoformat()
        fresh = (launched + timedelta(seconds=1)).isoformat()
        reused = 3956
        entries = [
            {"ProcessId": reused, "ParentProcessId": 1,
             "Name": "python.exe", "ExecutablePath": "test-python",
             "CreatedUtc": launched.isoformat()},
            {"ProcessId": 16116, "ParentProcessId": reused,
             "Name": "CiscoCollabHost.exe", "ExecutablePath": "test-cisco",
             "CreatedUtc": old},
            {"ProcessId": 16118, "ParentProcessId": 16116,
             "Name": "synthetic-grandchild.exe", "ExecutablePath": "test-child",
             "CreatedUtc": fresh},
        ]
        def inspect():
            fake = subprocess.CompletedProcess(
                args=["synthetic-only"], returncode=0,
                stdout=json.dumps(entries), stderr="")
            with mock.patch.object(subprocess, "run", return_value=fake):
                return _test_child_descendants(reused, launched)
        self.assertEqual(inspect(), (),
                         "Old process must not inherit recycled parent PID")
        entries.append(
            {"ProcessId": 16120, "ParentProcessId": reused,
             "Name": "synthetic-new-child.exe", "ExecutablePath": "test-child",
             "CreatedUtc": fresh})
        self.assertEqual(inspect(), (16120,),
                         "Current-tenure unapproved child must be reported")
        del entries[-1]["CreatedUtc"]
        with self.assertRaisesRegex(
                RuntimeError, "A04_DESCENDANT_ENUMERATION_UNAVAILABLE"):
            inspect()

    def test_console_host_pid_reuse_does_not_fake_descendant(self):
        if sys.platform != "win32":
            self.skipTest("Windows console-host PID reuse evidence")
        from datetime import timedelta
        from unittest import mock
        launched = datetime.now(timezone.utc)
        old = (launched - timedelta(minutes=20)).isoformat()
        between = (launched + timedelta(seconds=1)).isoformat()
        fresh = (launched + timedelta(seconds=2)).isoformat()
        latest = (launched + timedelta(seconds=3)).isoformat()
        parent_pid, conhost_pid = 22180, 3956
        system_conhost = os.path.join(
            os.environ.get("SystemRoot", r"C:\Windows"),
            "System32", "conhost.exe")
        entries = [
            {"ProcessId": parent_pid, "ParentProcessId": 1,
             "Name": "python.exe", "ExecutablePath": "synthetic-python",
             "CreatedUtc": launched.isoformat()},
            {"ProcessId": conhost_pid, "ParentProcessId": parent_pid,
             "Name": "conhost.exe", "ExecutablePath": system_conhost,
             "CreatedUtc": fresh},
            # A process created BEFORE this console-host tenure can retain
            # its recycled ParentProcessId, but is not a current child.
            {"ProcessId": 16116, "ParentProcessId": conhost_pid,
             "Name": "CiscoCollabHost.exe", "ExecutablePath": "synthetic-cisco",
             "CreatedUtc": old},
            {"ProcessId": 16118, "ParentProcessId": 16116,
             "Name": "old-process-descendant.exe",
             "ExecutablePath": "synthetic-grandchild", "CreatedUtc": latest},
            # Newer than the ORIGINAL launch, but older than this conhost
            # process: this recycled PID must not become a descendant.
            {"ProcessId": 16122, "ParentProcessId": conhost_pid,
             "Name": "intermediate-before-conhost.exe",
             "ExecutablePath": "synthetic-intermediate", "CreatedUtc": between},
            {"ProcessId": 16124, "ParentProcessId": 16122,
             "Name": "stale-intermediate-grandchild.exe",
             "ExecutablePath": "synthetic-grandchild", "CreatedUtc": latest},
        ]
        def inspect():
            fake = subprocess.CompletedProcess(
                args=["synthetic-only"], returncode=0,
                stdout=json.dumps(entries), stderr="")
            with mock.patch.object(subprocess, "run", return_value=fake):
                return _test_child_descendants(parent_pid, launched)
        self.assertEqual(inspect(), (),
                         "Old recycled-PID child must not invalidate OS conhost")
        # This recycled-PID child was born AFTER Python launched but BEFORE
        # this particular conhost existed. It is not conhost's descendant.
        entries[2]["CreatedUtc"] = (
            launched + timedelta(milliseconds=500)).isoformat()
        self.assertEqual(inspect(), (),
                         "Intermediate PID reuse must not invent a grandchild")
        entries[2]["CreatedUtc"] = old
        entries[1]["ExecutablePath"] = system_conhost.replace(
            os.sep, os.sep + os.sep)
        self.assertEqual(inspect(), (),
                         "Canonical Windows separators must identify same OS host")
        entries[1]["ExecutablePath"] = os.path.join(
            os.environ.get("SystemRoot", r"C:\Windows"), "..",
            "Untrusted", "conhost.exe")
        self.assertEqual(inspect(), (conhost_pid,),
                         "Same process name at foreign path is not OS host")
        # An alternate path qualifies only if the OS proves exact executable
        # file identity. A name or string alias alone cannot grant exemption.
        with mock.patch.object(os.path, "samefile", return_value=True) as matched:
            self.assertEqual(inspect(), ())
            self.assertTrue(matched.called)
        with mock.patch.object(os.path, "samefile", return_value=False):
            self.assertEqual(inspect(), (conhost_pid,))
        entries[1]["ExecutablePath"] = system_conhost
        entries.append(
            {"ProcessId": 16120, "ParentProcessId": conhost_pid,
             "Name": "unexpected-new-child.exe",
             "ExecutablePath": "synthetic-new-child",
             "CreatedUtc": latest})
        self.assertEqual(set(inspect()), {conhost_pid, 16120},
                         "Real current-tenure console descendants must fail closed")

    def test_unexpected_descendant_retains_root_and_reaps_owned_child(self):
        if sys.platform != "win32":
            self.skipTest("Windows child descendant cleanup")
        from unittest.mock import patch
        temp = TemporaryDirectory(prefix="nayeon-a04-", delete=False)
        root = Path(temp.name).resolve()
        child = None
        try:
            child = _A04ChildSupervisor(
                [getattr(sys, "_base_executable", sys.executable),
                 "-I", "-S", "-B", "-c", "import time;time.sleep(6)"],
                root=root)
            self.assertIsNone(child.proc.poll())
            # Synthetic descendant witness, not a real process or an exemption.
            with patch(
                __name__ + "._test_child_descendants",
                return_value=(98765432,),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "unexpected child descendants"
                ):
                    child.close()
            self.assertFalse(child.cleaned)
            self.assertIsNotNone(child.proc.returncode,
                                 "Owned child must be reaped on failure")
            self.assertFalse(any(t.is_alive() for t in child.threads))
            with self.assertRaisesRegex(
                AssertionError, "A04_UNREAPED_CHILD_ROOT_RETAINED"
            ):
                _cleanup_a04_test_root(temp, child, None)
            self.assertTrue(root.is_dir(), "Uncertain root was erased")
            receipt = root / "a04-retained-evidence.txt"
            self.assertIn(
                b"A04_RETAINED_FOR_MANUAL_REVIEW",
                _parent_evidence(receipt, 320, required=True))
        finally:
            # After checking failure retention, a fresh real descendant
            # inspection may release this wholly test-owned synthetic root.
            if child is not None and not child.cleaned:
                child.close()
            if not _A04ChildSupervisor.has_unreaped(root):
                temp.cleanup()

    def _spawn(self, script):
        return _A04ChildSupervisor(
            [getattr(sys,"_base_executable",sys.executable),
             "-I","-S","-B","-c",script])

    def _reject(self, script, method, reason, *, timeout=.75):
        if sys.platform != "win32":
            self.skipTest("Windows process supervisor")
        child = self._spawn(script)
        with self.assertRaisesRegex(AssertionError, reason):
            with child:
                if method == "barrier":
                    child.barrier(timeout=timeout)
                else:
                    child.result(timeout=timeout)
        self.assertTrue(child.cleaned, "Incomplete supervisor cleanup")
        self.assertIsNotNone(child.proc.returncode)
        self.assertFalse(any(t.is_alive() for t in child.threads))

    def test_a_stdout_overflow(self):
        self._reject("import sys,time;sys.stdout.write('Z'*16384);"
                     "sys.stdout.flush();time.sleep(4)",
                     "barrier", "A04_OUTPUT_OVERFLOW")

    def test_a_stderr_overflow(self):
        self._reject("import sys,time;sys.stderr.write('E'*16384);"
                     "sys.stderr.flush();time.sleep(4)",
                     "barrier", "A04_OUTPUT_OVERFLOW")

    def test_a_malformed_json(self):
        self._reject("import sys,time;sys.stdout.write('not-json\\n');"
                     "sys.stdout.flush();time.sleep(4)",
                     "barrier", "A04_MALFORMED_JSON")

    def test_a_extra_frame_after_valid_barrier(self):
        if sys.platform != "win32":
            self.skipTest("Windows process supervisor")
        import time
        temp = TemporaryDirectory(prefix="nayeon-a04-ack-", delete=False)
        child = None
        try:
            outer = Path(temp.name).resolve()
            ack = outer / "parent-accepted-first-frame.ack"
            self.assertFalse(ack.exists(), "Acknowledgment must be absent")
            script = "\n".join((
                "import sys,time",
                "from pathlib import Path",
                f"ack=Path({str(ack)!r})",
                "sys.stdout.write('{\"barrier\":\"READY\"}\\n')",
                "sys.stdout.flush()",
                "until=time.monotonic()+5",
                "while not ack.is_file():",
                "    if time.monotonic() >= until: sys.exit(73)",
                "    time.sleep(.01)",
                "sys.stdout.write('{\"barrier\":\"SECOND\"}\\n')",
                "sys.stdout.flush()",
                "time.sleep(4)",
                "",
            ))
            compile(script, "<a04-ack-child>", "exec")
            child = _A04ChildSupervisor(
                [getattr(sys, "_base_executable", sys.executable),
                 "-I", "-S", "-B", "-c", script], root=outer)
            with child:
                # Early failure is outside any expected-error assertion.
                first = child.barrier(timeout=3)
                self.assertEqual(first, {"barrier": "READY"})
                self.assertEqual(bytes(child.buffers[0]).count(b"\n"), 1)
                self.assertIsNone(child.proc.poll())
                with ack.open("xb") as destination:
                    destination.write(b"A04_PARENT_ACCEPTED\n")
                    destination.flush()
                    os.fsync(destination.fileno())
                # The child cannot emit frame two until the verified ACK.
                until = time.monotonic() + 3
                while bytes(child.buffers[0]).count(b"\n") < 2:
                    self.assertIsNone(child.proc.poll(), "Child exited before second frame")
                    self.assertLess(time.monotonic(), until,
                                    "Acknowledged second frame did not arrive")
                    time.sleep(.01)
                self.assertEqual(bytes(child.buffers[0]).count(b"\n"), 2)
                child.close()
                self.assertTrue(child.cleaned, "Child must be reaped before validation")
                # Only this final validation is allowed to satisfy expected failure.
                with self.assertRaisesRegex(
                        AssertionError, r"^A04_EXTRA_STDOUT_FRAMES$"):
                    child.single_message()
            self.assertIsNotNone(child.proc.returncode)
            self.assertFalse(any(t.is_alive() for t in child.threads))
        finally:
            _cleanup_a04_test_root(temp, child, None)

    def test_b_stdout_overflow_while_alive(self):
        self._reject("import sys,time;sys.stdout.write('Z'*16384);"
                     "sys.stdout.flush();time.sleep(4)",
                     "result", "A04_OUTPUT_OVERFLOW")

    def test_b_stderr_overflow_while_alive(self):
        self._reject("import sys,time;sys.stderr.write('E'*16384);"
                     "sys.stderr.flush();time.sleep(4)",
                     "result", "A04_OUTPUT_OVERFLOW")

    def test_b_extra_frames(self):
        self._reject("import sys;sys.stdout.write('{}\\n{}\\n');"
                     "sys.stdout.flush()", "result", "A04_EXTRA_STDOUT_FRAMES")

    def test_b_malformed_json(self):
        self._reject("print('not-json')", "result", "A04_MALFORMED_JSON")

    def test_b_timeout_forced_reap(self):
        self._reject("import time;time.sleep(6)",
                     "result", "A04_EXIT_TIMEOUT", timeout=.2)

    def test_a_timeout_forced_reap(self):
        self._reject("import time;time.sleep(6)",
                     "barrier", "A04_BARRIER_TIMEOUT", timeout=.2)

    def test_thread_start_failure_reaps_launched_child(self):
        if sys.platform != "win32":
            self.skipTest("Windows process supervisor")
        from threading import Thread
        from unittest.mock import patch
        original_start = Thread.start
        before = set(_A04ChildSupervisor._active_owners)

        def fail_only_second_reader(thread):
            if thread.name == "a04-supervisor-stderr":
                raise RuntimeError("A04_INJECTED_THREAD_START_FAILURE")
            return original_start(thread)

        with patch.object(Thread, "start", fail_only_second_reader):
            with self.assertRaisesRegex(RuntimeError, "A04_INJECTED_THREAD_START_FAILURE"):
                self._spawn("import time;time.sleep(6)")
        self.assertEqual(_A04ChildSupervisor._active_owners, before,
                         "Partially created child was not reaped")

    def test_original_failure_survives_root_cleanup_error(self):
        if sys.platform != "win32":
            self.skipTest("Windows process supervisor")
        from unittest.mock import patch
        temp = TemporaryDirectory(prefix="nayeon-a04-", delete=False)
        actual_cleanup = temp.cleanup

        def fail_cleanup():
            raise OSError("A04_INJECTED_ROOT_CLEANUP_FAILURE")

        try:
            with patch.object(temp, "cleanup", fail_cleanup):
                with self.assertRaisesRegex(AssertionError, "A04_ORIGINAL_TEST_FAILURE") as captured:
                    try:
                        raise AssertionError("A04_ORIGINAL_TEST_FAILURE")
                    finally:
                        _cleanup_a04_test_root(temp, None, None)
            self.assertTrue(any("A04_INJECTED_ROOT_CLEANUP_FAILURE" in n
                                for n in getattr(captured.exception, "__notes__", [])))
        finally:
            actual_cleanup()


if __name__ == "__main__":
    unittest.main()
