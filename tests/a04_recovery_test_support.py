"""A-04 test-only genuine two-process A-02 composition/restart probe.

Run as a child of the approved parent-owned temporary-directory test only.
The Child B construction below is explicitly NOT an A-02 factory admission.
No production code imports this module. No real credentials or native mutex.
"""
import builtins
import ctypes
import importlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import stat
import hashlib
import subprocess
import sys
import tempfile
import time

_ALLOWED_ROOT = re.compile(r"^nayeon-a02-[A-Za-z0-9_-]+$")
_FORBIDDEN = frozenset({"openai", "httpx", "requests", "win32cred", "keyring"})


def _require(ok, label):
    if not ok:
        raise AssertionError("A04_PROBE_" + label)


def _checked_outer(path):
    outer = Path(path)
    _require(outer.is_absolute() and outer == outer.resolve()
             and outer.is_dir() and not outer.is_symlink()
             and outer.name.startswith("nayeon-a04-container-"), "OUTER_ROOT")
    _require(Path(tempfile.gettempdir()).resolve() == outer, "TEMP_REDIRECT")
    return outer


def _checked_inner(outer, name):
    _require(type(name) is str and _ALLOWED_ROOT.fullmatch(name) is not None,
             "INNER_NAME")
    inner = outer / name
    _require(inner.is_dir() and not inner.is_symlink()
             and inner.resolve() == inner and inner.parent == outer,
             "INNER_ROOT")
    _require(not bool(getattr(inner.lstat(), "st_file_attributes", 0) & 0x400),
             "INNER_REPARSE")
    metadata = inner / "provider.json"
    _require(not metadata.exists() and not metadata.is_symlink(),
             "REAL_METADATA_FORBIDDEN")
    return inner, metadata


def _identity(path):
    """Bounded identity of one existing, non-reparse test-owned directory."""
    info = path.lstat()
    _require(path.is_dir() and not path.is_symlink() and
             not bool(getattr(info, "st_file_attributes", 0) & 0x400),
             "ROOT_IDENTITY_UNTRUSTED")
    return [info.st_dev, info.st_ino]


def _bootstrap_file_id(path):
    """Regular non-reparse file identity, checked before product imports."""
    info = path.lstat()
    _require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
             and not bool(getattr(info, "st_file_attributes", 0) & 0x400)
             and info.st_size > 0, "BOOTSTRAP_FILE_UNTRUSTED")
    return [info.st_dev, info.st_ino, info.st_size]


def _checked_bootstrap(repository):
    """Validate exact parent-pinned interpreter, repo and support witness."""
    raw = os.environ.get("NAYEON_A04_BOOTSTRAP_PINS")
    _require(type(raw) is str and len(raw) <= 1024,
             "BOOTSTRAP_PINS_MISSING_OR_OVERSIZE")
    try:
        pins = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise AssertionError("A04_PROBE_BOOTSTRAP_PINS_UNREADABLE") from exc
    _require(type(pins) is dict and set(pins) == {
        "repo_path", "repo_id", "support_path", "support_id",
        "support_sha", "python_path", "python_id"}, "BOOTSTRAP_PIN_SCHEMA")
    support = Path(__file__).resolve()
    executable = Path(sys.executable).resolve()
    _require(repository == repository.resolve()
             and pins["repo_path"] == str(repository)
             and pins["repo_id"] == _identity(repository),
             "BOOTSTRAP_REPO_IDENTITY")
    _require(pins["support_path"] == str(support)
             and pins["support_id"] == _bootstrap_file_id(support)
             and support.parent == repository / "tests"
             and pins["support_id"][2] <= 131072
             and pins["support_sha"] ==
                 hashlib.sha256(support.read_bytes()).hexdigest(),
             "BOOTSTRAP_SUPPORT_IDENTITY")
    _require(pins["python_path"] == str(executable)
             and pins["python_id"] == _bootstrap_file_id(executable),
             "BOOTSTRAP_INTERPRETER_IDENTITY")


def _emit_claim(payload, inner):
    """Exact synthetic bytes and decode state accompany every A checkpoint."""
    from nayeon.brain.onboarding_recovery_document import (
        decode_journal, RecoveryEvidenceError)
    outer = inner.parent
    journal = inner / "provider.json.nayeon-recovery-journal"
    raw = _bounded_regular(journal, 131072)
    state = "missing"
    if raw is not None:
        try:
            records = decode_journal(raw)
            state = records[-1].state.value if records else "missing"
        except (RecoveryEvidenceError, ValueError, TypeError):
            state = "unreadable"
    ledger = _bounded_regular(inner / "fake-effects.log",
                              len(b"A04_FAKE_EFFECT_ONCE\n"))
    payload.update(
        outer_id=_identity(outer), inner_id=_identity(inner),
        journal_sha=hashlib.sha256(raw or b"").hexdigest(),
        journal_bytes=len(raw or b""), journal_state=state,
        ledger_sha=hashlib.sha256(ledger or b"").hexdigest())
    print(json.dumps(payload, separators=(",", ":")), flush=True)


def _bounded_regular(path, limit, *, required=False):
    """Read one exact synthetic sidecar with lstat/fd identity and size bounds."""
    try:
        before = path.lstat()
    except FileNotFoundError:
        _require(not required, "REQUIRED_EVIDENCE_MISSING")
        return None
    _require(stat.S_ISREG(before.st_mode)
             and not bool(getattr(before, "st_file_attributes", 0) & 0x400)
             and 0 <= before.st_size <= limit, "UNTRUSTED_SIDECAR")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read(limit + 1)
        after = path.lstat()
    _require(len(data) <= limit and
             (before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino) ==
             (after.st_dev, after.st_ino) and
             stat.S_ISREG(after.st_mode) and len(data) == after.st_size,
             "SIDECAR_CHANGED_OR_OVERSIZE")
    return data


def _b_evidence(inner, journal, *, expected_effect, scenario):
    """Exact R-class evidence schema; journal bytes never grant authority."""
    from nayeon.brain.onboarding_recovery_document import decode_journal, record_hash
    marker = inner / "provider.json.nayeon-onboarding-inflight"
    ledger = inner / "fake-effects.log"
    names = [entry.name for entry in inner.iterdir()]
    _require(len(names) == len(set(name.casefold() for name in names)),
             "DUPLICATE_EVIDENCE_CASEFOLD")
    archive_prefix = journal.name + ".archive-"
    archives = [inner / name for name in names if name.startswith(archive_prefix)]
    _require(len(archives) <= 1, "MULTIPLE_ARCHIVES")
    allowed = {journal.name, marker.name, ledger.name}
    allowed.update(p.name for p in archives)
    _require(set(names).issubset(allowed), "UNKNOWN_EVIDENCE_ENTRY")
    raw = _bounded_regular(journal, 131072,
                           required=(scenario not in ("marker_only", "archive_only",
                                                      "missing")))
    effects = _bounded_regular(ledger, len(b"A04_FAKE_EFFECT_ONCE\n"))
    _require((effects is None if expected_effect == b"" else
              effects == expected_effect), "PERSISTED_SYNTHETIC_EFFECT")
    marker_bytes = _bounded_regular(marker, 80)
    _require(marker_bytes in (None, b"",
             b"Nayeon v1 onboarding operation needs review if interrupted.\n"),
             "INVALID_MARKER")
    if scenario != "marker_only":
        _require(marker_bytes is None, "UNEXPECTED_MARKER")
    else:
        _require(raw is None and marker_bytes is not None and effects is None,
                 "MARKER_ONLY_SCHEMA")
    _require(bool(archives) == (scenario == "archive_only"),
             "ARCHIVE_SCENARIO_MISMATCH")
    if scenario in ("missing", "archive_only"):
        _require(raw is None and effects is None and marker_bytes is None,
                 "ABSENT_JOURNAL_SCHEMA")
    if archives:
        archived = _bounded_regular(archives[0], 131072, required=True)
        _require(len(archives[0].name) == len(archive_prefix) + 64,
                 "ARCHIVE_SUFFIX_LENGTH")
        records = decode_journal(archived)
        _require(records and archives[0].name ==
                 archive_prefix + record_hash(records[-1]),
                 "ARCHIVE_HASH_MISMATCH")
    return raw, hashlib.sha256(raw or b"").hexdigest(), hashlib.sha256(effects or b"").hexdigest()


def _install_early_guards():
    """Known child-only entrypoints before ANY product or A-02 imports.

    Deliberately not a universal interpreter/OS sandbox. A forbidden attempt
    is always recorded and fails closed; no live provider path is exercised.
    """
    attempts = []
    original_import = builtins.__import__
    original_import_module = importlib.import_module

    def forbidden(name):
        return type(name) is str and name.split(".", 1)[0] in _FORBIDDEN

    def reject_import():
        attempts.append("forbidden_import")
        raise AssertionError("A04_FORBIDDEN_IMPORT")

    def checked_import(name, *args, **kwargs):
        if forbidden(name):
            reject_import()
        return original_import(name, *args, **kwargs)

    def checked_import_module(name, package=None):
        if forbidden(name):
            reject_import()
        return original_import_module(name, package)

    class ForbiddenFinder:
        def find_spec(self, fullname, path=None, target=None):
            if forbidden(fullname):
                reject_import()
            return None

    def deny(label):
        def blocked(*args, **kwargs):
            attempts.append(label)
            raise AssertionError("A04_FORBIDDEN_" + label)
        return blocked

    builtins.__import__ = checked_import
    importlib.import_module = checked_import_module
    sys.meta_path.insert(0, ForbiddenFinder())
    socket.socket = deny("socket")
    socket.create_connection = deny("network")
    socket.create_server = deny("network")
    ctypes.WinDLL = deny("native")
    ctypes.CDLL = deny("native")
    ctypes.OleDLL = deny("native")
    ctypes.LibraryLoader.LoadLibrary = deny("native")

    class BlockedWindll:
        def __getattr__(self, name):
            return deny("native")()

        def __getitem__(self, name):
            return deny("native")()

    if hasattr(ctypes, "windll"):
        ctypes.windll = BlockedWindll()
    subprocess.Popen = deny("process")
    os.system = deny("process")
    for name in ("startfile", "spawnl", "spawnle", "spawnv", "spawnve",
                 "spawnlp", "spawnlpe", "spawnvp", "spawnvpe",
                 "execl", "execle", "execv", "execve",
                 "execlp", "execlpe", "execvp", "execvpe"):
        if hasattr(os, name):
            setattr(os, name, deny("process"))
    return attempts, deny


def _finish_guards(attempts, deny):
    """Guard known production loader entrypoints before composing fakes."""
    from nayeon.brain.windows_onboarding_mutex import WindowsOnboardingMutex
    from nayeon.secrets import windows_credential
    from nayeon.brain.providers import openai_client
    WindowsOnboardingMutex.hold = deny("native_mutex")
    windows_credential._load_advapi32 = deny("wincred")
    openai_client._load_openai_sdk = deny("provider_sdk")
    _require(not attempts, "FORBIDDEN_IMPORT_DURING_BOOTSTRAP")


def _exercise_guard_negative(name, attempts, nonce):
    """One expected block per throwaway child; no permitted-case counter reset."""
    from nayeon.brain.windows_onboarding_mutex import WindowsOnboardingMutex
    from nayeon.secrets import windows_credential
    from nayeon.brain.providers import openai_client
    routes = {
        "builtin_import": (lambda: __import__("openai"), "forbidden_import"),
        "module_import": (lambda: importlib.import_module("httpx"), "forbidden_import"),
        "meta_finder": (lambda: importlib.util.find_spec("requests"), "forbidden_import"),
        "socket": (lambda: socket.socket(), "socket"),
        "connect": (lambda: socket.create_connection(("127.0.0.1", 1)), "network"),
        "server": (lambda: socket.create_server(("127.0.0.1", 0)), "network"),
        "windll": (lambda: ctypes.WinDLL("a04-no-real-library"), "native"),
        "windll_attribute": (lambda: ctypes.windll.kernel32, "native"),
        "windll_index": (lambda: ctypes.windll["kernel32"], "native"),
        "cdll": (lambda: ctypes.CDLL("a04-no-real-library"), "native"),
        "oledll": (lambda: ctypes.OleDLL("a04-no-real-library"), "native"),
        "loader": (lambda: ctypes.LibraryLoader.LoadLibrary(
            ctypes.windll, "a04-no-real-library"), "native"),
        "popen": (lambda: subprocess.Popen(["a04-no-process"]), "process"),
        "system": (lambda: os.system("a04-no-command"), "process"),
        "exec": (lambda: os.execv("a04-no-process", ["a04-no-process"]), "process"),
        "native_mutex": (lambda: WindowsOnboardingMutex.hold(None), "native_mutex"),
        "wincred": (lambda: windows_credential._load_advapi32(), "wincred"),
        "provider_sdk": (lambda: openai_client._load_openai_sdk(), "provider_sdk"),
    }
    _require(name in routes, "NEGATIVE_ROUTE_NOT_ALLOWLISTED")
    action, expected = routes[name]
    _require(not attempts, "NEGATIVE_PREEXISTING_ATTEMPT")
    try:
        action()
    except AssertionError as error:
        _require(str(error) == "A04_FORBIDDEN_" + (
            "IMPORT" if expected == "forbidden_import" else expected),
            "WRONG_NEGATIVE_GUARD_ERROR")
    else:
        raise AssertionError("A04_NEGATIVE_GUARD_NOT_TRIGGERED")
    _require(attempts == [expected], "NEGATIVE_GUARD_COUNT")
    print(json.dumps({"phase": "G", "nonce": nonce, "pid": os.getpid(),
                      "guard": name, "attempts": 1},
                     separators=(",", ":")), flush=True)


def _compose_restarted(metadata):
    """Bounded B-only fake topology; intentionally NOT the sealed A-02 factory."""
    from nayeon.brain.connection_reconciliation import observe_connection
    from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
    from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
    from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
    from nayeon.secrets.contracts import SecretIdentifier
    from nayeon.secrets.lifecycle import BoundCredentialLifecycle
    from tests.a02_fake_isolation_support import (
        FakeBackend, FakeValidator, FakeObserver, FakeMutex,
    )
    backend, validator, mutex = FakeBackend(), FakeValidator(), FakeMutex()
    observer = FakeObserver(backend)
    lifecycle = BoundCredentialLifecycle(
        backend, SecretIdentifier("openai.api_key"), validator)
    onboarding = OpenAICredentialOnboarding(lifecycle)
    host = TrustedCredentialOperationHost(
        onboarding=onboarding,
        observe=lambda: observe_connection(metadata, observer),
    )
    coordinator = CooperativeOnboardingCoordinator(
        host=host, metadata_path=metadata, availability=observer, mutex=mutex)
    ctl = coordinator.recovery_controller
    _require(ctl._availability is observer and ctl._mutex is mutex,
             "RECONSTRUCTED_DEPENDENCIES")
    _require(not ctl.ready and ctl.epoch is None and ctl._ctx is None,
             "RECONSTRUCTED_INHERITED_AUTHORITY")
    return ctl, backend, observer, coordinator


def _trusted_journal_fault_case(comp, ctl, backend, coordinator, ticket,
                                owner, root, candidate, nonce, scenario, attempts):
    """Test-only failure of the exact fake journal at a documented append seam."""
    from nayeon.brain.onboarding_coordination import CoordinatedOutcome
    from nayeon.brain.onboarding_recovery_document import (
        RecoveryState, RecoveryEvidenceError)
    from nayeon.brain import onboarding_recovery_store as recovery_store_module
    from nayeon.brain.onboarding_recovery_store import (
        OnboardingRecoveryJournalStore, RecoveryStoreUnavailable)
    failure = []
    store = ctl._store
    journal = store.path
    _require(journal.is_file(), "JOURNAL_PATH_REQUIRED")
    old_open = os.fdopen
    old_fsync = os.fsync
    old_read = OnboardingRecoveryJournalStore._read
    old_checked = OnboardingRecoveryJournalStore._open_checked
    old_decode = recovery_store_module.decode_journal

    class ScopedJournalWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def write(self, data):
            if scenario == "write_fault":
                _require(not failure, "DUPLICATE_WRITE_FAULT")
                failure.append("write")
                raise OSError("A04 synthetic journal write failure")
            return self.stream.write(data)

        def flush(self):
            if scenario == "pre_flush_fault" and not failure:
                failure.append("pre_flush")
                # with-block cleanup may subsequently flush the buffered data;
                # the fault is NOT proof that no journal bytes were written.
                raise OSError("A04 synthetic post-write pre-flush fault")
            result = self.stream.flush()
            if scenario == "flush_fault":
                _require(not failure, "DUPLICATE_FLUSH_FAULT")
                failure.append("flush")
                raise OSError("A04 synthetic journal flush report")
            return result

        def fileno(self):
            return self.stream.fileno()

        def __exit__(self, *exc):
            result = self.stream.__exit__(*exc)
            if scenario == "close_report_fault" and not failure:
                failure.append("close_report")
                raise OSError("A04 synthetic journal close report")
            return result

    def targeted_fdopen(fd, mode="r", *args, **kwargs):
        stream = old_open(fd, mode, *args, **kwargs)
        if mode != "wb":
            return stream
        info = os.fstat(fd)
        expected = journal.lstat()
        if ((info.st_dev, info.st_ino) !=
                (expected.st_dev, expected.st_ino)):
            return stream
        caller = sys._getframe(1)
        _require(caller.f_code is OnboardingRecoveryJournalStore.append.__code__
                 and caller.f_locals.get("self") is store,
                 "JOURNAL_WRITER_OUTSIDE_EXACT_APPEND")
        _require(not failure, "REPEATED_JOURNAL_WRITER_FAULT")
        return ScopedJournalWriter(stream)

    def exact_post_fsync(fd):
        observed = os.fstat(fd)
        expected = journal.lstat()
        if ((observed.st_dev, observed.st_ino) ==
                (expected.st_dev, expected.st_ino)):
            caller = sys._getframe(1)
            _require(caller.f_code is OnboardingRecoveryJournalStore.append.__code__
                     and caller.f_locals.get("self") is store,
                     "JOURNAL_FSYNC_OUTSIDE_EXACT_APPEND")
            _require(not failure, "DUPLICATE_POST_FSYNC_FAULT")
            old_fsync(fd)
            failure.append("post_fsync")
            # The exact journal descriptor was fsynced, but the context
            # has not yet reported a successful close/readback.
            raise OSError("A04 synthetic post-fsync pre-close fault")
        return old_fsync(fd)

    reads = []
    def targeted_read(self):
        if self is store:
            reads.append(True)
            if scenario == "readback_fault" and len(reads) == 2:
                _require(not failure, "DUPLICATE_READBACK_FAULT")
                failure.append("readback")
                raise OSError("A04 synthetic journal readback failure")
        return old_read(self)

    opens = []
    def targeted_checked(self, *, create, write):
        if self is store and not write:
            opens.append(True)
            if scenario == "reopen_fault" and len(opens) == 2:
                _require(not failure, "DUPLICATE_REOPEN_FAULT")
                failure.append("reopen")
                raise OSError("A04 synthetic journal reopen failure")
        return old_checked(self, create=create, write=write)
    def _inside_append():
        caller = sys._getframe(2)
        return caller.f_code is OnboardingRecoveryJournalStore.append.__code__

    def exact_read(self):
        if self is store and _inside_append():
            reads.append(True)
            if scenario == "readback_fault" and len(reads) == 2:
                _require(not failure, "DUPLICATE_READBACK_FAULT")
                failure.append("readback")
                raise OSError("A04 synthetic journal readback failure")
        return old_read(self)

    def exact_checked(self, *, create, write):
        caller = sys._getframe(1)
        grandparent = caller.f_back
        if (self is store and not write and grandparent is not None
                and grandparent.f_code is OnboardingRecoveryJournalStore.append.__code__):
            opens.append(True)
            if scenario == "reopen_fault" and len(opens) == 2:
                _require(not failure, "DUPLICATE_REOPEN_FAULT")
                failure.append("reopen")
                raise OSError("A04 synthetic journal reopen failure")
        return old_checked(self, create=create, write=write)

    decode_reads = []
    def exact_decode(data):
        reader = sys._getframe(1)
        append = reader.f_back
        if (reader.f_code is old_read.__code__
                and reader.f_locals.get("self") is store
                and append is not None
                and append.f_code is OnboardingRecoveryJournalStore.append.__code__
                and append.f_locals.get("self") is store):
            decode_reads.append(True)
            if len(decode_reads) == 2:
                _require(not failure, "DUPLICATE_DECODE_FAULT")
                # Exercise the real decoder on synthetic malformed bytes, but
                # preserve the actual post-fsync journal unchanged on disk.
                try:
                    old_decode(b"A04_INVALID_POST_CLOSE_READBACK_FRAME")
                except RecoveryEvidenceError:
                    failure.append("decode")
                    raise
                raise AssertionError("A04_BAD_FRAME_DECODER_NOT_REJECTED")
        return old_decode(data)

    if scenario in ("write_fault", "pre_flush_fault", "flush_fault",
                    "close_report_fault"):
        os.fdopen = targeted_fdopen
    elif scenario == "post_fsync_fault":
        os.fsync = exact_post_fsync
    elif scenario == "readback_fault":
        OnboardingRecoveryJournalStore._read = exact_read
    elif scenario == "decode_fault":
        recovery_store_module.decode_journal = exact_decode
    elif scenario == "reopen_fault":
        OnboardingRecoveryJournalStore._open_checked = exact_checked
    else:
        raise AssertionError("A04_UNAPPROVED_FAULT_SCENARIO")
    try:
        result = coordinator.approve_ui(
            ticket=ticket, owner_token=owner, root=root,
            operation=__import__("nayeon.brain.onboarding_operation_advice",
                                 fromlist=["OnboardingOperation"]).OnboardingOperation.CONNECT,
            candidate=candidate)
    finally:
        os.fdopen = old_open
        os.fsync = old_fsync
        OnboardingRecoveryJournalStore._read = old_read
        OnboardingRecoveryJournalStore._open_checked = old_checked
        recovery_store_module.decode_journal = old_decode
    _require(len(failure)==1, "JOURNAL_FAULT_NOT_EXERCISED_EXACTLY_ONCE")
    _require(result.outcome is CoordinatedOutcome.RECOVERY_REQUIRED,
             "JOURNAL_FAULT_FALSE_SUCCESS")
    _require(not ctl.ready and ctl._faulted, "JOURNAL_FAULT_NOT_LATCHED")
    _require(backend.value is None and
             not any(call in ("put", "delete") for call in backend.calls),
             "JOURNAL_FAULT_EXECUTED_FAKE_EFFECT")
    _require(not attempts, "JOURNAL_FAULT_FORBIDDEN_IO")
    try:
        history = store.read()
    except RecoveryStoreUnavailable:
        history = None
    if scenario == "pre_flush_fault":
        # Context cleanup may flush zero, partial or all bytes; report what
        # actually survived. Invalid bytes are denial, never a false READY.
        _require(history is None or history[-1].state in
                 (RecoveryState.READY, RecoveryState.IN_FLIGHT),
                 "PRE_FLUSH_UNEXPECTED_JOURNAL")
    else:
        expected = (RecoveryState.READY if scenario == "write_fault"
                    else RecoveryState.IN_FLIGHT)
        _require(history and history[-1].state is expected,
                 "JOURNAL_FAULT_UNEXPECTED_EVIDENCE")
    _require(not (journal.parent / "fake-effects.log").exists(),
             "JOURNAL_FAULT_EFFECT_LEDGER")
    _emit_claim({"phase":"A","nonce":nonce,"pid":os.getpid(),
                 "inner":journal.parent.name,
                 "epoch":history[-1].epoch if history else ctl._epoch,
                 "generation":history[-1].generation if history else ctl._generation,
                 "barrier":scenario.upper()}, journal.parent)
    while True:
        time.sleep(15)


def _trusted_fake_mutex_uncertainty_case(
        comp, ctl, backend, nonce, scenario, attempts):
    """Exact A-02 fake-mutex context interception; never a native Windows test."""
    from contextlib import _GeneratorContextManager, contextmanager
    from nayeon.brain.onboarding_recovery import (
        RecoveryAdmissionError, TrustedOnboardingRecoveryController)
    from nayeon.brain.onboarding_recovery_document import RecoveryState
    from nayeon.brain.windows_onboarding_mutex import MutexAdmission
    from tests.a02_fake_isolation_support import (
        FakeBackend, FakeObserver, FakeMutex)
    _require(scenario in ("abandoned_fsync_fault", "release_report_fault"),
             "UNEXPECTED_MUTEX_SCENARIO")
    descriptor = FakeMutex.__dict__["hold"]
    original_enter = _GeneratorContextManager.__enter__
    original_exit = _GeneratorContextManager.__exit__
    entered = []
    released = []
    registered = []
    exited = []

    def scoped_enter(ctx):
        targeted = (
            getattr(ctx, "func", None) is descriptor.__wrapped__ and
            getattr(ctx, "args", None) == (comp.mutex,) and
            getattr(ctx, "kwds", None) == {})
        if targeted:
            _require(not entered, "DUPLICATE_FAKE_MUTEX_CONTEXT")
            entered.append(ctx)
            registered.append(ctx)
        outcome = original_enter(ctx)
        if targeted and scenario == "abandoned_fsync_fault":
            _require(outcome is MutexAdmission.HELD, "ABANDONED_FROM_NONHELD")
            return MutexAdmission.ABANDONED
        return outcome

    def scoped_exit(ctx, *exc):
        targeted_exit = any(item is ctx for item in registered)
        result = original_exit(ctx, *exc)
        if targeted_exit:
            _require(not any(item is ctx for item in exited),
                     "DUPLICATE_ORIGINAL_MUTEX_EXIT")
            exited.append(ctx)
            registered.remove(ctx)
        if (scenario == "release_report_fault" and entered and
                ctx is entered[0]):
            _require(not released, "DUPLICATE_RELEASE_REPORT")
            released.append(ctx)
            raise OSError("A04 synthetic post-release reporting uncertainty")
        return result

    _GeneratorContextManager.__enter__ = scoped_enter
    _GeneratorContextManager.__exit__ = scoped_exit
    try:
        # Non-target context and reentrant BUSY are never mistaken for the
        # exact A-02 controller mutex context.
        foreign = FakeMutex()
        with foreign.hold() as first:
            _require(first is MutexAdmission.HELD, "FAKE_MUTEX_HELD_CONTROL")
            with foreign.hold() as busy:
                _require(busy is MutexAdmission.BUSY,
                         "FAKE_MUTEX_BUSY_CONTROL")
        _require(foreign.entries == 1 and foreign.exits == 1
                 and not foreign.active and
                 not entered and not registered and not exited,
                 "NON_TARGET_MUTEX_CONTEXT_INTERCEPTED")

        class UnavailableFakeMutex(FakeMutex):
            @contextmanager
            def hold(self):
                yield MutexAdmission.UNAVAILABLE

        spare_path = comp.metadata_path.parent / "a04-unavailable-control.json"
        _require(not spare_path.exists() and not spare_path.is_symlink(),
                 "UNAVAILABLE_CONTROL_PATH")
        unavailable_backend = FakeBackend()
        unavailable_mutex = UnavailableFakeMutex()
        spare_ctl = TrustedOnboardingRecoveryController.for_path(
            spare_path, availability=FakeObserver(unavailable_backend),
            mutex=unavailable_mutex)
        try:
            spare_ctl.request_reconciliation()
        except RecoveryAdmissionError:
            pass
        else:
            raise AssertionError("A04_UNAVAILABLE_MUTEX_ADMITTED")
        _require(spare_ctl._ctx is None and spare_ctl._epoch is None
                 and not spare_ctl.ready and unavailable_backend.value is None
                 and not spare_path.exists()
                 and not any(p.name.startswith(spare_path.name)
                             for p in spare_path.parent.iterdir())
                 and not entered and not registered and not exited,
                 "UNAVAILABLE_CONTROL_GAINED_AUTHORITY")

        review = ctl.request_reconciliation()
        _require(len(entered) == 1 and registered == entered
                 and not exited and ctl._ctx is entered[0] and
                 comp.mutex.entries == 1, "EXACT_A02_MUTEX_ENTER")
        if scenario == "abandoned_fsync_fault":
            _require(review.operation_uncertain and not ctl.ready,
                     "ABANDONED_WAS_ADMITTED")
            original_fsync = os.fsync
            faults = []
            journal = ctl._store.path

            def fail_exact_journal_fsync(fd):
                if journal.exists():
                    observed, expected = os.fstat(fd), journal.lstat()
                    if ((observed.st_dev, observed.st_ino) ==
                            (expected.st_dev, expected.st_ino)):
                        caller = sys._getframe(1)
                        _require(caller.f_code is type(ctl._store).append.__code__
                                 and caller.f_locals.get("self") is ctl._store,
                                 "ABANDONED_FSYNC_OUTSIDE_EXACT_APPEND")
                        _require(not faults, "DUPLICATE_ABANDONED_FSYNC")
                        faults.append(True)
                        raise OSError("A04 synthetic abandoned journal fsync failure")
                return original_fsync(fd)

            os.fsync = fail_exact_journal_fsync
            try:
                approved = ctl.approve_reconciliation(
                    human_approved=True, fingerprint=review.fingerprint,
                    expected_review=review)
            finally:
                os.fsync = original_fsync
            _require(approved is False and faults == [True] and
                     not ctl.ready and ctl._faulted,
                     "ABANDONED_PERSISTENCE_GAINED_AUTHORITY")
            history = ctl._store.read()
            _require(history and history[-1].state is RecoveryState.RECONCILING,
                     "ABANDONED_FAILED_APPEND_EVIDENCE")
            _require(not released and registered == entered and not exited,
                     "ABANDONED_RELEASE_INJECTED")
            barrier = "ABANDONED_FSYNC_FAULT"
        else:
            _require(ctl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint,
                expected_review=review) and ctl.ready,
                "RELEASE_BASELINE_NOT_READY")
            try:
                ctl.close()
            except OSError:
                pass
            else:
                raise AssertionError("A04_RELEASE_REPORT_NOT_INJECTED")
            _require(released == entered and exited == entered
                     and not registered and
                     ctl._release_uncertain and not ctl.ready and
                     ctl._ctx is entered[0] and
                     comp.mutex.exits == 1 and not comp.mutex.active,
                     "RELEASE_UNCERTAINTY_NOT_LATCHED")
            try:
                ctl.request_reconciliation()
            except RecoveryAdmissionError:
                pass
            else:
                raise AssertionError("A04_RELEASE_FALSE_READMISSION")
            history = ctl._store.read()
            _require(history and history[-1].state is RecoveryState.READY,
                     "RELEASE_PRESERVED_JOURNAL")
            barrier = "RELEASE_REPORT_FAULT"
        _require(FakeMutex.__dict__["hold"] is descriptor and
                 backend.value is None and
                 not any(x in backend.calls for x in ("put", "delete")) and
                 not attempts, "MUTEX_TEST_ESCAPED_FAKE_ONLY")
        _emit_claim({"phase":"A", "nonce":nonce, "pid":os.getpid(),
                     "inner":comp.metadata_path.parent.name,
                     "epoch":review.epoch, "generation":review.generation,
                     "barrier":barrier}, comp.metadata_path.parent)
        while True:
            time.sleep(15)
    finally:
        _GeneratorContextManager.__enter__ = original_enter
        _GeneratorContextManager.__exit__ = original_exit


def _trusted_fake_effect_checkpoint(comp, ctl, backend, nonce, scenario, attempts):
    """Test-only trace of the original fake backend inside trusted UI approval."""
    from nayeon.brain.onboarding_operation_advice import OnboardingOperation
    from nayeon.brain.onboarding_coordination import (
        CooperativeOnboardingCoordinator, CoordinatedOutcome)
    from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
    from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
    from nayeon.secrets.lifecycle import BoundCredentialLifecycle
    from nayeon.brain.onboarding_recovery_document import RecoveryState
    from nayeon.secrets.contracts import SecretIdentifier, SecretValue

    owner = ctl.claim_ui_window_owner()
    _require(type(owner) is str and bool(owner), "UI_OWNER")
    root = object()
    coordinator = comp.coordinator
    receipt, ticket = coordinator.request_ui(
        OnboardingOperation.CONNECT, owner_token=owner, root=root)
    _require(receipt.outcome is CoordinatedOutcome.PENDING and ticket is not None,
             "TRUSTED_UI_REVIEW_NOT_ISSUED")
    candidate = SecretValue("synthetic-a04-fake-only")
    original_code = type(backend).put.__code__
    onboarding = comp.host._TrustedCredentialOperationHost__onboarding
    lifecycle = onboarding._OpenAICredentialOnboarding__lifecycle
    _require(type(onboarding) is OpenAICredentialOnboarding
             and type(lifecycle) is BoundCredentialLifecycle
             and lifecycle._BoundCredentialLifecycle__backend is backend
             and comp.coordinator._host is comp.host,
             "EXACT_TRUSTED_FAKE_DEPENDENCIES")
    expected_stack = (
        (BoundCredentialLifecycle._put.__code__, lifecycle),
        (BoundCredentialLifecycle.connect.__code__, lifecycle),
        (OpenAICredentialOnboarding._call.__code__, onboarding),
        (OpenAICredentialOnboarding.connect.__code__, onboarding),
        (TrustedCredentialOperationHost.approve.__code__, comp.host),
        (CooperativeOnboardingCoordinator._approve_recovered.__code__, coordinator),
        (CooperativeOnboardingCoordinator._approve_pending.__code__, coordinator),
        (CooperativeOnboardingCoordinator.approve_ui.__code__, coordinator),
    )
    observed_frame = [None]

    def barrier(label):
        _require(not attempts, "FORBIDDEN_IO_BEFORE_EFFECT_BARRIER")
        history = ctl._store.read()
        last = history[-1] if history else None
        _require(last is not None and last.state is RecoveryState.IN_FLIGHT
                 and ctl._active is not None
                 and last.operation_id == ctl._active.operation_id
                 and last.operation_kind == ctl._active.kind == "connect"
                 and last.epoch == ctl._active.epoch == ctl._epoch
                 and last.generation == ctl._active.generation == ctl._generation
                 and not ctl.ready and ctl.epoch is None
                 and ctl.generation is None and ctl._ctx is not None,
                 "TRUSTED_INFLIGHT_EVIDENCE")
        ledger = comp.metadata_path.parent / "fake-effects.log"
        if label == "AFTER_FAKE":
            _require(backend.value is candidate and backend.calls.count("put") == 1
                     and backend.calls.count("delete") == 0,
                     "ORIGINAL_FAKE_PUT")
            with ledger.open("xb") as stream:
                stream.write(b"A04_FAKE_EFFECT_ONCE\n")
                stream.flush()
                os.fsync(stream.fileno())
            _require(ledger.read_bytes() == b"A04_FAKE_EFFECT_ONCE\n",
                     "EFFECT_READBACK")
        else:
            _require(backend.value is None and not ledger.exists()
                     and backend.calls.count("put") == 0
                     and backend.calls.count("delete") == 0, "PRE_EFFECT_STATE")
        _require(coordinator._ui_ticket is ticket, "TRUSTED_UI_TICKET")
        _emit_claim({"phase":"A","nonce":nonce,"pid":os.getpid(),
                     "inner":comp.metadata_path.parent.name,
                     "epoch":last.epoch,"generation":last.generation,
                     "barrier":label}, comp.metadata_path.parent)
        while True:
            time.sleep(15)

    def tracer(frame, event, arg):
        if frame.f_code is original_code and frame.f_locals.get("self") is backend:
            if event == "call":
                ancestors = []
                current = frame.f_back
                while current is not None:
                    ancestors.append(current)
                    current = current.f_back
                matched = 0
                for ancestor in ancestors:
                    if (matched < len(expected_stack) and
                            ancestor.f_code is expected_stack[matched][0] and
                            ancestor.f_locals.get("self") is expected_stack[matched][1]):
                        matched += 1
                _require(matched == len(expected_stack), "TRUSTED_STACK_IDENTITY")
                observed_frame[0] = frame
                if scenario == "before_effect":
                    barrier("BEFORE_FAKE")
                return tracer
            if event == "exception" and observed_frame[0] is frame:
                raise AssertionError("A04_UNEXPECTED_FAKE_BACKEND_EXCEPTION")
            if event == "return" and observed_frame[0] is frame:
                _require(scenario == "after_effect", "UNEXPECTED_PUT_RETURN")
                barrier("AFTER_FAKE")
        return None

    # Negative control exercises the ORIGINAL tracer against a direct call.
    trace_before_negative = sys.gettrace()
    try:
        sys.settrace(tracer)
        try:
            backend.put(SecretIdentifier("openai.api_key"), candidate)
        except AssertionError as exc:
            _require(str(exc) == "A04_PROBE_TRUSTED_STACK_IDENTITY",
                     "DIRECT_BACKEND_NOT_BLOCKED_BY_STACK_GUARD")
        else:
            raise AssertionError("A04_DIRECT_BACKEND_ESCAPE")
    finally:
        sys.settrace(trace_before_negative)
    _require(backend.value is None and backend.calls.count("put") == 0,
             "DIRECT_BACKEND_NEGATIVE_MUTATED")
    if scenario == "fsync_fault":
        original_fsync = os.fsync
        injected = []
        target = ctl._store.path
        def fail_exact_test_journal(fd):
            observed = os.fstat(fd)
            expected = target.stat()
            if (observed.st_dev, observed.st_ino) == (expected.st_dev, expected.st_ino):
                caller = sys._getframe(1)
                _require(caller.f_code is type(ctl._store).append.__code__
                         and caller.f_locals.get("self") is ctl._store,
                         "EFFECT_FSYNC_OUTSIDE_EXACT_APPEND")
                _require(not injected, "REPEATED_FSYNC_FAULT")
                injected.append(True)
                raise OSError("A04 synthetic journal fsync uncertainty")
            return original_fsync(fd)
        os.fsync = fail_exact_test_journal
        try:
            response = coordinator.approve_ui(
                ticket=ticket, owner_token=owner, root=root,
                operation=OnboardingOperation.CONNECT, candidate=candidate)
        finally:
            os.fsync = original_fsync
        _require(injected == [True], "FSYNC_INJECTION_NOT_REACHED")
        _require(response.outcome is CoordinatedOutcome.RECOVERY_REQUIRED,
                 "FSYNC_FAILURE_FALSE_APPROVAL")
        _require(not ctl.ready and ctl._faulted, "FSYNC_FAILURE_NOT_LATCHED")
        _require(backend.value is None and backend.calls.count("put") == 0
                 and backend.calls.count("delete") == 0,
                 "FSYNC_FAILURE_RAN_EFFECT")
        _require(not attempts, "FSYNC_FAILURE_FORBIDDEN_IO")
        history = ctl._store.read()
        last = history[-1] if history else None
        _require(last is not None and last.state is RecoveryState.IN_FLIGHT
                 and last.operation_kind == "connect", "FSYNC_JOURNAL_VISIBLE")
        _require(not (comp.metadata_path.parent / "fake-effects.log").exists(),
                 "FSYNC_FAULT_EFFECT_LEDGER")
        _emit_claim({"phase":"A","nonce":nonce,"pid":os.getpid(),
                     "inner":comp.metadata_path.parent.name,
                     "epoch":last.epoch,"generation":last.generation,
                     "barrier":"FSYNC_FAULT"}, comp.metadata_path.parent)
        while True:
            time.sleep(15)

    if scenario in ("write_fault", "pre_flush_fault", "flush_fault",
                    "post_fsync_fault", "close_report_fault",
                    "reopen_fault", "readback_fault", "decode_fault"):
        _trusted_journal_fault_case(
            comp, ctl, backend, coordinator, ticket, owner, root,
            candidate, nonce, scenario, attempts)
    previous = sys.gettrace()
    try:
        sys.settrace(tracer)
        coordinator.approve_ui(ticket=ticket, owner_token=owner, root=root,
                               operation=OnboardingOperation.CONNECT, candidate=candidate)
    finally:
        sys.settrace(previous)
    raise AssertionError("A04_TRUSTED_EFFECT_BARRIER_NOT_REACHED")


def run(phase, raw_outer, name, nonce, prior_epoch, scenario='ready', raw_identity=None):
    _require(sys.platform == "win32", "WINDOWS_ONLY")
    if phase == "L":
        # Legacy cases use a direct disposable system-TEMP child rather than
        # an A-02-owned nested root; they still require the guarded bootstrap.
        legacy_root = Path(raw_outer)
        _require(legacy_root.is_absolute() and legacy_root.is_dir() and
                 legacy_root == legacy_root.resolve() and
                 legacy_root.parent == Path(tempfile.gettempdir()).resolve() and
                 legacy_root.name.startswith("nayeon-a04-") and
                 not legacy_root.is_symlink() and
                 not (getattr(legacy_root.lstat(), "st_file_attributes", 0)
                      & 0x400), "LEGACY_ROOT")
    else:
        outer = _checked_outer(raw_outer)
    _require(type(nonce) is str and len(nonce) == 32
             and re.fullmatch(r"[0-9a-f]{32}", nonce), "IPC_NONCE")
    if phase == "L":
        # Standard-library ssl and asyncio define subclasses of socket.socket
        # and subprocess.Popen at import time. Preload those class definitions
        # before installing the child-only constructor deny guards.
        import ssl
        import asyncio
    attempts, deny = _install_early_guards()
    # No project or A-02 imports have occurred before the known-route guards.
    repository = Path(__file__).resolve().parents[1]
    _require(repository.is_dir(), "REPOSITORY")
    _checked_bootstrap(repository)
    if str(repository) not in sys.path:
        sys.path.insert(0, str(repository))
    from nayeon.brain.onboarding_recovery_document import RecoveryState
    from nayeon.brain.onboarding_recovery import (
        TrustedOnboardingRecoveryController, RecoveryAdmissionError)
    from tests.a02_fake_isolation_support import (
        FakeBackend, FakeValidator, FakeObserver, FakeMutex,
        FakeTempRoot, compose_fake_only_onboarding)
    _finish_guards(attempts, deny)
    if phase == "L":
        _require(name in ("A", "B") and
                 prior_epoch in ("normal", "abandoned", "exit_failure") and
                 raw_identity is None and not attempts,
                 "LEGACY_BOOTSTRAP_SCOPE")
        import runpy
        legacy = repository / "tests" / "a04_recovery_subprocess_child.py"
        _require(legacy.parent == repository / "tests" and
                 legacy == legacy.resolve() and
                 0 < _bootstrap_file_id(legacy)[2] <= 131072,
                 "LEGACY_SCRIPT_IDENTITY")
        saved_argv = sys.argv
        try:
            sys.argv = [str(legacy), name, str(legacy_root),
                        scenario, prior_epoch]
            # Legacy product imports now occur inside the guarded, pinned
            # interpreter, not during an unguarded module startup.
            runpy.run_path(str(legacy), run_name="__main__")
        finally:
            sys.argv = saved_argv
        _require(not attempts, "LEGACY_FORBIDDEN_IO")
        return
    if phase == "G":
        _require(prior_epoch == "-" and scenario == "ready",
                 "NEGATIVE_ARGS")
        _exercise_guard_negative(name, attempts, nonce)
        return
    if phase == "A":
        _require(name == "-", "A_ARG")
        # The exact sealed A-02 class creates and owns this inner root.
        owner = FakeTempRoot()
        inner, metadata = _checked_inner(outer, owner.path.name)
        backend, validator, mutex = FakeBackend(), FakeValidator(), FakeMutex()
        observer = FakeObserver(backend)
        comp = compose_fake_only_onboarding(
            backend=backend, validator=validator, observer=observer, mutex=mutex,
            temp_root=owner, metadata_path=metadata)
        ctl = comp.controller
        _require(comp.coordinator.recovery_controller is ctl, "TRUSTED_HOST")
        # Separate, pre-operation root claim before any crash/fault barrier.
        _emit_claim({"phase":"A", "kind":"ROOT_CLAIM",
                     "nonce":nonce, "pid":os.getpid(), "inner":inner.name}, inner)
        if scenario in ("abandoned_fsync_fault", "release_report_fault"):
            _trusted_fake_mutex_uncertainty_case(
                comp, ctl, backend, nonce, scenario, attempts)
        review = ctl.request_reconciliation()
        _require(review.journal_state is RecoveryState.UNINITIALIZED,
                 "FIRST_REVIEW_STATE")
        _require(ctl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint,
            expected_review=review), "FIRST_RECONCILIATION")
        _require(ctl.ready and ctl._store.read()[-1].state is RecoveryState.READY,
                 "DURABLE_READY")
        _require(
            TrustedOnboardingRecoveryController.for_path(metadata) is ctl,
            "ACTIVE_POOL_IDENTITY")
        if scenario in ("before_effect", "after_effect", "fsync_fault",
                        "write_fault", "pre_flush_fault", "flush_fault",
                        "post_fsync_fault", "close_report_fault",
                        "reopen_fault", "readback_fault", "decode_fault"):
            _trusted_fake_effect_checkpoint(comp, ctl, backend, nonce, scenario, attempts)
        _require(not any(x in backend.calls for x in ("put", "delete")),
                 "UNEXPECTED_FAKE_EFFECT")
        _require(not attempts, "FORBIDDEN_IO")
        _emit_claim({"phase": "A", "nonce": nonce, "barrier": "READY",
                     "pid": os.getpid(), "inner": inner.name,
                     "epoch": ctl.epoch, "generation": ctl.generation}, inner)
        # Parent uses Windows TerminateProcess. Do not close the controller
        # or owner; their lifetime is deliberately cut short.
        while True:
            time.sleep(15)
    if phase != "B":
        raise AssertionError("A04_BAD_PHASE")
    inner, metadata = _checked_inner(outer, name)
    _require(type(raw_identity) is str and len(raw_identity) <= 160,
             "B_PARENT_IDENTITY_REQUIRED")
    try:
        witness = json.loads(raw_identity)
    except (ValueError, TypeError) as exc:
        raise AssertionError("A04_INVALID_PARENT_IDENTITY") from exc
    _require(type(witness) is dict and set(witness) == {"outer", "inner"}
             and witness["outer"] == _identity(outer)
             and witness["inner"] == _identity(inner),
             "B_PATH_IDENTITY_MISMATCH")
    journal = metadata.with_name(metadata.name + ".nayeon-recovery-journal")
    _require(scenario in ("ready","before_effect","after_effect","fsync_fault",
                          "write_fault","pre_flush_fault","flush_fault",
                          "post_fsync_fault","close_report_fault",
                          "reopen_fault","readback_fault","decode_fault",
                          "abandoned_fsync_fault","release_report_fault",
                          "marker_only","archive_only","missing"), "SCENARIO")
    effect = inner / "fake-effects.log"
    expected_effect = b"A04_FAKE_EFFECT_ONCE\n" if scenario == "after_effect" else b""
    initial_journal, journal_sha, ledger_sha = _b_evidence(
        inner, journal, expected_effect=expected_effect, scenario=scenario)
    ctl, backend, observer, coordinator = _compose_restarted(metadata)
    initially_ready = ctl.ready
    history = ctl._store.read()
    previous = (
        RecoveryState.UNINITIALIZED if scenario in (
            "marker_only", "archive_only", "missing") else
        RecoveryState.READY if scenario in (
            "ready", "write_fault", "release_report_fault") else
        RecoveryState.RECONCILING if scenario == "abandoned_fsync_fault" else
        RecoveryState.IN_FLIGHT)
    if scenario in ("marker_only", "archive_only", "missing"):
        _require(history is None and initial_journal is None,
                 "B_UNINITIALIZED_JOURNAL_NOT_ABSENT")
    else:
        _require(history and history[-1].state is previous,
                 "B_HISTORY_WRONG_STATE")
        _require(_bounded_regular(journal, 131072, required=True) == initial_journal,
                 "B_JOURNAL_BYTES_CHANGED")
    review = ctl.request_reconciliation()
    _require(review.journal_state is previous
             and review.epoch != prior_epoch
             and not ctl.ready, "B_HISTORICAL_AUTHORITY")
    if scenario not in ("ready", "write_fault", "release_report_fault",
                        "missing"):
        _require(review.operation_uncertain, "B_INTERRUPTED_EFFECT_NOT_UNCERTAIN")
    else:
        _require(not review.operation_uncertain, "B_CLEAN_REVIEW_FALSE_UNCERTAINTY")
    if scenario == "marker_only":
        _require(review.legacy_marker_present, "B_MARKER_ONLY_REVIEW_REQUIRED")
    if scenario == "archive_only":
        _require(review.archive_present and review.operation_uncertain
                 and not review.archive_required,
                 "B_ARCHIVE_ONLY_REVIEW_REQUIRED")
    _require(ctl.approve_reconciliation(
        human_approved=True, fingerprint=review.fingerprint,
        expected_review=review), "B_FRESH_HUMAN_RECONCILIATION")
    _require(ctl.ready and ctl.epoch != prior_epoch, "B_NEW_EPOCH")
    _require(ctl.generation == review.generation, "FRESH_GENERATION_NOT_BOUND")
    fresh_generation = ctl.generation
    denied = False
    try:
        ctl.begin_operation(kind="connect", evidence_hash="e" * 64,
                            epoch=prior_epoch, generation=fresh_generation)
    except RecoveryAdmissionError:
        denied = True
    _require(denied and ctl.ready, "STALE_EPOCH_ACCEPTED")
    from dataclasses import replace
    from nayeon.brain.onboarding_recovery import RecoveryPermit
    ready_journal = _bounded_regular(journal, 131072, required=True)
    stale_ready_permit = RecoveryPermit(prior_epoch, fresh_generation,
                                        "0" * 32, "connect")
    try:
        ctl.finish_operation(stale_ready_permit, verified=True)
    except RecoveryAdmissionError:
        pass
    else:
        raise AssertionError("A04_STALE_PERMIT_ACCEPTED_WHILE_READY")
    _require(ctl.ready and ctl.generation == fresh_generation and
             ctl._active is None and
             _bounded_regular(journal, 131072, required=True) == ready_journal and
             not any(x in backend.calls for x in ("put", "delete")),
             "STALE_READY_PERMIT_CHANGED_B")
    _require(not any(x in backend.calls for x in ("put", "delete")),
             "REPLAYED_FAKE_EFFECT")
    _require((effect.read_bytes() if effect.exists() else b"")==expected_effect,
             "SYNTHETIC_EFFECT_REPLAYED")

    # A's Python ticket cannot cross processes: these are explicitly
    # reconstructed stale lookalikes, never a claim of authentic A-ticket IPC.
    from dataclasses import replace
    from nayeon.brain.onboarding_operation_advice import OnboardingOperation
    from nayeon.brain.onboarding_coordination import CoordinatedOutcome
    from nayeon.secrets.contracts import SecretValue
    fresh_epoch = ctl.epoch
    b_owner = ctl.claim_ui_window_owner()
    _require(type(b_owner) is str and bool(b_owner), "B_OWNER_NOT_CLAIMED")
    b_root = object()
    pending, b_ticket = coordinator.request_ui(
        OnboardingOperation.CONNECT, owner_token=b_owner, root=b_root)
    _require(pending.outcome is CoordinatedOutcome.PENDING
             and b_ticket is not None and coordinator.has_pending,
             "B_NEW_UI_REVIEW_NOT_PENDING")
    old_epoch_ticket = replace(b_ticket, epoch=prior_epoch)
    old_owner = "0" * len(b_owner)
    stale_attempts = (
        (old_epoch_ticket, b_owner, b_root),
        (b_ticket, old_owner, b_root),
        (b_ticket, b_owner, object()),
    )
    for candidate_ticket, candidate_owner, candidate_root in stale_attempts:
        attempted = coordinator.approve_ui(
            ticket=candidate_ticket, owner_token=candidate_owner,
            root=candidate_root, operation=OnboardingOperation.CONNECT,
            candidate=SecretValue("synthetic-a04-stale-denied"))
        _require(attempted.outcome is CoordinatedOutcome.REFUSED,
                 "STALE_UI_APPROVAL_ACCEPTED")
        rejected = coordinator.reject_ui(
            ticket=candidate_ticket, owner_token=candidate_owner,
            root=candidate_root, operation=OnboardingOperation.CONNECT)
        _require(rejected.outcome is CoordinatedOutcome.REFUSED,
                 "STALE_UI_REJECTION_ACCEPTED")
        _require(coordinator._ui_ticket is b_ticket and
                 coordinator.has_pending and
                 coordinator.is_current_ui_ticket(
                     ticket=b_ticket, owner_token=b_owner, root=b_root,
                     operation=OnboardingOperation.CONNECT),
                 "STALE_UI_CHANGED_NEW_PENDING")
    _require(coordinator.approve(
        candidate=SecretValue("synthetic-a04-raw-denied")
    ).outcome is CoordinatedOutcome.REFUSED,
             "RAW_APPROVAL_STOLE_B_TICKET")
    _require(coordinator.reject().outcome is CoordinatedOutcome.REFUSED
             and coordinator._ui_ticket is b_ticket and coordinator.has_pending,
             "RAW_REJECTION_STOLE_B_TICKET")
    _require(backend.value is None and backend.calls.count("put") == 0,
             "STALE_UI_RAN_FAKE_EFFECT")
    _require((effect.read_bytes() if effect.exists() else b"") == expected_effect,
             "STALE_UI_ALTERED_A_LEDGER")

    # A distinct, simulated B-human approval is an intentionally NEW fake
    # effect. CONNECT remains recovery-required without exact readback proof.
    b_candidate = SecretValue("synthetic-a04-fresh-b-only")
    permit_denials = []
    active_ui_denials = []
    def verify_stale_permit_during_real_pending_effect(frame, event, arg):
        if (event == "call" and
                frame.f_code is type(backend).put.__code__ and
                frame.f_locals.get("self") is backend):
            _require(not permit_denials and ctl._active is not None,
                     "B_PERMIT_PROBE_NOT_IN_FLIGHT")
            original_permit = ctl._active
            journal_before = _bounded_regular(journal, 131072, required=True)
            calls_before = tuple(backend.calls)
            try:
                ctl.begin_operation(
                    kind="connect", evidence_hash="e" * 64,
                    epoch=prior_epoch, generation=fresh_generation)
            except RecoveryAdmissionError:
                permit_denials.append("old_epoch_inflight")
            else:
                raise AssertionError("A04_STALE_EPOCH_ADMITTED_DURING_B_EFFECT")
            _require(ctl._active is original_permit and
                     _bounded_regular(journal, 131072, required=True)
                     == journal_before and tuple(backend.calls) == calls_before,
                     "STALE_EPOCH_CHANGED_B_INFLIGHT")
            old_permit_witness = replace(original_permit, epoch=prior_epoch)
            try:
                ctl.finish_operation(old_permit_witness, verified=True)
            except RecoveryAdmissionError:
                permit_denials.append("old_permit")
            else:
                raise AssertionError("A04_STALE_PERMIT_FINISHED_B_OPERATION")
            _require(ctl._active is original_permit and
                     _bounded_regular(journal, 131072, required=True)
                     == journal_before and tuple(backend.calls) == calls_before and
                     ctl._store.read()[-1].state is RecoveryState.IN_FLIGHT,
                     "STALE_PERMIT_CHANGED_B_OPERATION")
            # A's reconstructed UI lookalike and stale owner are refused
            # again DURING B's actual in-flight fake callback.
            _require(coordinator._ui_ticket is b_ticket,
                     "B_INFLIGHT_UI_TICKET_WAS_STOLEN")
            attempt = coordinator.approve_ui(
                ticket=old_epoch_ticket, owner_token=b_owner, root=b_root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic-a04-active-stale-denied"))
            _require(attempt.outcome is CoordinatedOutcome.REFUSED,
                     "ACTIVE_STALE_UI_APPROVAL_ACCEPTED")
            active_ui_denials.append("approve")
            attempt = coordinator.reject_ui(
                ticket=old_epoch_ticket, owner_token=b_owner, root=b_root,
                operation=OnboardingOperation.CONNECT)
            _require(attempt.outcome is CoordinatedOutcome.REFUSED,
                     "ACTIVE_STALE_UI_REJECTION_ACCEPTED")
            active_ui_denials.append("reject")
            attempt, ticket = coordinator.request_ui(
                OnboardingOperation.CONNECT,
                owner_token=old_owner, root=b_root)
            _require(attempt.outcome is CoordinatedOutcome.REFUSED and
                     ticket is None, "ACTIVE_STALE_OWNER_REQUEST_ACCEPTED")
            active_ui_denials.append("request")
            _require(coordinator._ui_ticket is b_ticket and
                     ctl._active is original_permit and
                     _bounded_regular(journal, 131072, required=True)
                     == journal_before and tuple(backend.calls) == calls_before,
                     "ACTIVE_STALE_UI_CHANGED_B_AUTHORITY")
        return verify_stale_permit_during_real_pending_effect
    prior_trace = sys.gettrace()
    try:
        sys.settrace(verify_stale_permit_during_real_pending_effect)
        b_result = coordinator.approve_ui(
            ticket=b_ticket, owner_token=b_owner, root=b_root,
            operation=OnboardingOperation.CONNECT, candidate=b_candidate)
    finally:
        sys.settrace(prior_trace)
    _require(permit_denials == ["old_epoch_inflight", "old_permit"] and
             active_ui_denials == ["approve", "reject", "request"],
             "B_STALE_AUTHORITY_NEGATIVES_NOT_EXERCISED")
    _require(b_result.outcome is CoordinatedOutcome.RECOVERY_REQUIRED,
             "B_CONNECT_FALSELY_VERIFIED")
    _require(backend.calls.count("put") == 1 and
             backend.calls.count("delete") == 0 and
             backend.value is b_candidate and not coordinator.has_pending,
             "B_NEW_INDEPENDENT_FAKE_EFFECT")
    _require((_bounded_regular(effect, len(b"A04_FAKE_EFFECT_ONCE\n")) or b"")
             == expected_effect, "B_NEW_APPROVAL_ALTERED_A_LEDGER")
    post_journal = _bounded_regular(journal, 131072, required=True)
    post_history = ctl._store.read()
    _require(post_history and post_history[-1].state is RecoveryState.IN_FLIGHT
             and post_history[-1].epoch != prior_epoch,
             "B_POST_EFFECT_JOURNAL_UNVERIFIED")
    _require(not ctl.ready and not coordinator.has_pending,
             "B_POST_EFFECT_STALE_AUTHORITY")
    ctl.close()
    _require(not attempts, "FORBIDDEN_IO")
    print(json.dumps({"phase": "B", "nonce": nonce, "pid": os.getpid(),
                      "outer_id": _identity(outer), "inner_id": _identity(inner),
                      "journal_sha": journal_sha, "ledger_sha": ledger_sha,
                      "post_journal_sha":hashlib.sha256(post_journal).hexdigest(),
                      "initial_ready": initially_ready,
                      "journal": review.journal_state.value,
                      "uncertain": review.operation_uncertain,
                      "effect_count": 1 if expected_effect else 0,
                      "fresh_epoch": fresh_epoch != prior_epoch,
                      "stale_epoch_denied": denied,
                      "stale_ui_denials":len(stale_attempts),
                      "fresh_b_outcome":b_result.outcome.value,
                      "effects":backend.calls.count("put")},
                     separators=(",", ":")), flush=True)


if __name__ == "__main__":
    _require(len(sys.argv) in (6, 7, 8), "ARGS")
    run(*sys.argv[1:])
