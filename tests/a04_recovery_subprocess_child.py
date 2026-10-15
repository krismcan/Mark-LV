"""A-04 ONLY: disposable Windows subprocess child, no production wiring.

The parent owns a real TemporaryDirectory and force-kills child A. This module
uses A-02 exact fake types; it intentionally does not call the A-02 factory,
whose fresh-path restriction cannot represent restart over existing evidence.
The factory remains untouched, and this difference is subject to independent
review. Never pass a real metadata location or a credential value.
"""
from contextlib import contextmanager
from pathlib import Path
from tempfile import gettempdir
from unittest import mock
import hashlib
import json
import os
import stat
import sys
import time

from nayeon.brain.onboarding_recovery import (
    RecoveryAdmissionError, TrustedOnboardingRecoveryController,
)
from nayeon.brain.onboarding_recovery_document import RecoveryState
from nayeon.brain.onboarding_recovery_store import OnboardingRecoveryJournalStore
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from tests.a02_fake_isolation_support import FakeBackend, FakeObserver, FakeMutex
from tests.test_pre_829_a02_fake_isolation import ProhibitedIO


def _require(condition, code):
    if not condition:
        raise AssertionError("A04_" + code)


def _root_path(raw):
    root = Path(raw)
    base = Path(gettempdir()).resolve()
    _require(root == root.resolve() and root.is_dir() and not root.is_symlink(),
             "INVALID_TEMP_ROOT")
    _require(root.parent == base and root.name.startswith("nayeon-a04-"),
             "NOT_PARENT_OWNED_TEST_TEMP")
    metadata = root / "provider.json"
    _require(not metadata.exists() and not metadata.is_symlink(),
             "UNEXPECTED_METADATA")
    return metadata


def _emit(payload):
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), flush=True)


def _legacy_effect_bytes(path):
    """Bounded non-reparse ledger witness; None is absence, b'' is malformed."""
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    _require(stat.S_ISREG(before.st_mode)
             and not bool(getattr(before, "st_file_attributes", 0) & 0x400)
             and 0 <= before.st_size <= len(b"A04_FAKE_EFFECT_ONCE\n"),
             "EFFECT_UNTRUSTED")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read(len(b"A04_FAKE_EFFECT_ONCE\n") + 1)
        after = path.lstat()
    _require(stat.S_ISREG(opened.st_mode) and stat.S_ISREG(after.st_mode)
             and not bool(getattr(after, "st_file_attributes", 0) & 0x400)
             and (before.st_dev, before.st_ino) ==
                 (opened.st_dev, opened.st_ino) ==
                 (after.st_dev, after.st_ino)
             and len(data) == before.st_size == after.st_size
             and len(data) <= len(b"A04_FAKE_EFFECT_ONCE\n"),
             "EFFECT_CHANGED_OR_OVERSIZE")
    return data


def _effect_append(root):
    """One durable synthetic ledger line; never an actual backend operation."""
    target = root / "fake-effects.log"
    _require(not target.is_symlink(), "EFFECT_PATH_ALIAS")
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_BINARY, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(b"A04_FAKE_EFFECT_ONCE\n")
        stream.flush()
        os.fsync(stream.fileno())
    persisted = _legacy_effect_bytes(target)
    _require(persisted == b"A04_FAKE_EFFECT_ONCE\n", "EFFECT_NOT_DURABLE")
    return hashlib.sha256(persisted).hexdigest()


class AbandonedFakeMutex(FakeMutex):
    @contextmanager
    def hold(self):
        _require(not self.active, "FAKE_MUTEX_ALREADY_ACTIVE")
        self.active = True
        self.entries += 1
        try:
            yield MutexAdmission.ABANDONED
        finally:
            self.exits += 1
            self.active = False


class ExitFailureFakeMutex(FakeMutex):
    @contextmanager
    def hold(self):
        self.active = True
        self.entries += 1
        try:
            yield MutexAdmission.HELD
        finally:
            self.exits += 1
            raise OSError("A04 synthetic native-release failure")


def _build(metadata, mode):
    fake_backend = FakeBackend()
    observer = FakeObserver(fake_backend)
    mutex = (AbandonedFakeMutex() if mode == "abandoned" else
             ExitFailureFakeMutex() if mode == "exit_failure" else
             FakeMutex())
    controller = TrustedOnboardingRecoveryController.for_path(
        metadata, availability=observer, mutex=mutex)
    _require(controller._mutex is mutex and controller._availability is observer,
             "WRONG_INJECTED_DEPENDENCIES")
    _require(not controller.ready and controller.epoch is None and
             controller.generation is None and controller._ctx is None,
             "INHERITED_AUTHORITY")
    _require(controller is TrustedOnboardingRecoveryController.for_path(metadata),
             "SAME_PROCESS_POOL_NOT_SHARED")
    return controller, fake_backend, mutex


def _journal_state(controller):
    history = controller._store.read()
    return "missing" if not history else history[-1].state.value


def _first_process(root, scenario):
    metadata = _root_path(root)
    with ProhibitedIO() as poison:
        ctl, backend, mutex = _build(metadata, "normal")
        assert backend.value is None
        if scenario in ("reconciling",):
            review = ctl.request_reconciliation()
            _require(review.journal_state is RecoveryState.UNINITIALIZED,
                     "BAD_INITIAL_REVIEW")
            # Simulate death after the actual RECONCILING append but before READY.
            original = ctl._persist
            def crash_after_reconciling(instance, state, **kwargs):
                _require(instance is ctl, "UNEXPECTED_CONTROLLER_INSTANCE")
                value = original(state, **kwargs)
                if state is RecoveryState.RECONCILING:
                    _require(_journal_state(ctl) == "reconciling",
                             "NOT_PERSISTED_RECONCILING")
                    _emit({"barrier": "RECONCILING", "pid": os.getpid()})
                    while True:
                        time.sleep(20)
                return value
            with mock.patch.object(TrustedOnboardingRecoveryController,
                                   "_persist", crash_after_reconciling):
                ctl.approve_reconciliation(
                    human_approved=True, fingerprint=review.fingerprint,
                    expected_review=review)
            raise AssertionError("A04_RECONCILING_BARRIER_NOT_REACHED")
        review = ctl.request_reconciliation()
        _require(ctl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint,
            expected_review=review), "A_RECONCILIATION_FAILED")
        _require(ctl.ready and _journal_state(ctl) == "ready",
                 "READY_NOT_PERSISTED")
        if scenario == "ready":
            barrier = "READY"
        else:
            # A-04 uses a fake evidence digest. Operation permission comes
            # solely from the real controller, never from this child program.
            permit = ctl.begin_operation(
                kind="connect", evidence_hash="e" * 64,
                epoch=ctl.epoch, generation=ctl.generation)
            _require(not ctl.ready and _journal_state(ctl) == "in_flight",
                     "INFLIGHT_NOT_PERSISTED")
            if scenario == "inflight_before":
                barrier = "IN_FLIGHT_NO_EFFECT"
            elif scenario == "inflight_after":
                _effect_append(root)
                barrier = "IN_FLIGHT_FAKE_EFFECT_PERSISTED"
            else:
                raise AssertionError("A04_UNKNOWN_A_SCENARIO")
        _require(poison.attempts == [], "PROHIBITED_IO_" + repr(poison.attempts))
        _emit({"barrier": barrier, "pid": os.getpid()})
        # Parent force-kills this process. No close(), context exit or
        # graceful cleanup on the test-owned recovery controller.
        while True:
            time.sleep(20)


def _second_process(root, scenario, fake_mutex_mode):
    metadata = _root_path(root)
    effect = root / "fake-effects.log"
    before_effect = _legacy_effect_bytes(effect)
    expected_effect = (b"A04_FAKE_EFFECT_ONCE\n"
                       if scenario == "inflight_after" else None)
    _require(before_effect == expected_effect,
             "INVALID_SYNTHETIC_EFFECT_SHAPE")
    with ProhibitedIO() as poison:
        ctl, backend, mutex = _build(metadata, fake_mutex_mode)
        initial_ready = ctl.ready
        denied = False
        try:
            ctl.begin_operation(
                kind="connect", evidence_hash="e"*64,
                epoch="0"*32, generation=0)
        except RecoveryAdmissionError:
            denied = True
        _require(denied and not ctl.ready, "STALE_DIRECT_ADMISSION")
        state_before = "unreadable"
        try:
            state_before = _journal_state(ctl)
        except Exception:
            state_before = "unreadable"
        review = None
        requested = False
        uncertain = None
        changed_epoch = None
        approved = False
        try:
            review = ctl.request_reconciliation()
            requested = True
            uncertain = review.operation_uncertain
            prior = ctl._last
            if prior is not None:
                changed_epoch = (prior.epoch != review.epoch)
                _require(changed_epoch, "EPOCH_REUSED")
            _require(not ctl.ready, "PREAPPROVAL_READY")
            _require(not ctl.approve_reconciliation(
                human_approved=True, fingerprint="0"*64,
                expected_review=review), "STALE_FINGERPRINT_ACCEPTED")
            _require(not ctl.ready, "STALE_APPROVAL_GAINED_AUTHORITY")
            if scenario == "archive":
                _require(review.archive_required, "ARCHIVE_NOT_REQUIRED")
                evidence_before_refusal = ctl._store.path.read_bytes()
                _require(not ctl.approve_reconciliation(
                    human_approved=True, fingerprint=review.fingerprint,
                    archive_acknowledged=False, expected_review=review),
                    "UNACKNOWLEDGED_ARCHIVE_ACCEPTED")
                _require(not ctl.ready and
                         ctl._store.path.read_bytes() == evidence_before_refusal
                         and not ctl._store.archive_present(),
                         "ARCHIVE_REFUSAL_CHANGED_EVIDENCE")
                review = ctl.request_reconciliation()
                _require(review.archive_required and not ctl.ready,
                         "FRESH_ARCHIVE_REVIEW_REQUIRED")
            if scenario in {"ready", "inflight_before", "inflight_after",
                            "reconciling", "marker", "marker_only", "missing",
                            "abandoned", "archive", "exit_failure"}:
                approved = ctl.approve_reconciliation(
                    human_approved=True, fingerprint=review.fingerprint,
                    archive_acknowledged=review.archive_required,
                    expected_review=review)
                _require(approved and ctl.ready, "FRESH_APPROVAL_NOT_EFFECTIVE")
        except RecoveryAdmissionError:
            _require(scenario in {"corrupt", "truncated", "conflict", "bad_reopen"},
                     "UNEXPECTED_REVIEW_ERROR")
        if scenario in {"corrupt", "truncated", "conflict", "bad_reopen"}:
            _require(not ctl.ready and not approved,
                     "CORRUPT_JOURNAL_ADMISSION")
        if scenario in {"inflight_before","inflight_after","reconciling",
                        "marker","marker_only","abandoned"}:
            _require(uncertain is True, "PRIOR_UNCERTAINTY_LOST")
        if scenario == "ready":
            _require(state_before == "ready", "READY_DID_NOT_SURVIVE")
        if scenario in {"inflight_before","inflight_after"}:
            _require(state_before == "in_flight", "FLIGHT_DID_NOT_SURVIVE")
        if scenario == "reconciling":
            _require(state_before == "reconciling", "RECONCILING_DID_NOT_SURVIVE")
        if scenario in ("marker", "marker_only"):
            _require(review.legacy_marker_present, "LEGACY_MARKER_NOT_REPORTED")
        if scenario == "abandoned":
            _require(review.operation_uncertain, "ABANDONED_NOT_UNCERTAIN")
        if scenario == "exit_failure":
            _require(ctl.ready, "PREEXIT_NOT_READY")
            try:
                ctl.close()
            except (OSError, RecoveryAdmissionError):
                pass
            _require(ctl._release_uncertain and not ctl.ready and ctl._ctx is not None,
                     "UNSAFE_RELEASE_FAILURE_STATE")
            try:
                ctl.request_reconciliation()
            except RecoveryAdmissionError:
                pass
            else:
                raise AssertionError("A04_FALSE_POSTFAILURE_READMISSION")
        elif ctl._ctx is not None:
            ctl.close()
        _require(_legacy_effect_bytes(effect) == before_effect,
                 "AUTOMATIC_EFFECT_REPLAY")
        _require(backend.calls.count("put")==0 and backend.calls.count("delete")==0,
                 "REAL_BACKEND_MUTATION")
        _require(poison.attempts == [], "PROHIBITED_IO_" + repr(poison.attempts))
        _emit({"phase":"CHILD_B","pid":os.getpid(),"initial_ready":initial_ready,
               "stale_admission_denied":denied,"prior_state":state_before,
               "review_requested":requested,"uncertain":uncertain,
               "fresh_epoch":changed_epoch,"approved":approved,
               "effect_count":1 if before_effect is not None else 0,
               "forbidden_attempt_count":len(poison.attempts)})


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ("A","B"):
        raise AssertionError("A04_REQUIRES_EXACT_TEST_ARGS")
    phase, raw_root, scenario = sys.argv[1:4]
    mode = sys.argv[4]
    if scenario not in {"ready","inflight_before","inflight_after","reconciling",
                        "marker","marker_only","missing","corrupt","truncated","conflict",
                        "abandoned","archive","exit_failure","bad_reopen"}:
        raise AssertionError("A04_INVALID_SCENARIO")
    root = Path(raw_root)
    if phase == "A":
        _require(mode == "normal","WRONG_A_MODE")
        _first_process(root, scenario if scenario in
                       {"ready","inflight_before","inflight_after","reconciling"}
                       else "ready")
    else:
        _second_process(root, scenario, mode)


if __name__ == "__main__":
    main()
