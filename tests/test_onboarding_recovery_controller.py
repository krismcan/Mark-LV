"""Fake-only tenure-bound recovery controller trust tests."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from nayeon.brain.onboarding_recovery import (
    TrustedOnboardingRecoveryController, RecoveryAdmissionError,
)
from nayeon.brain.onboarding_recovery_document import RecoveryState
from nayeon.brain.windows_onboarding_mutex import MutexAdmission


class FakeMutex:
    def __init__(self, state=MutexAdmission.HELD):
        self.state = state
        self.entered = False

    @contextmanager
    def hold(self):
        if self.entered:
            yield MutexAdmission.BUSY
            return
        self.entered = True
        try:
            yield self.state
        finally:
            self.entered = False


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.metadata = Path(self.temp.name) / "metadata.json"
        self.mutex = FakeMutex()
        self.controller = TrustedOnboardingRecoveryController(
            self.metadata, mutex=self.mutex)
        self.addCleanup(self._close_safely)

    def _close_safely(self):
        if self.controller._ctx is not None:
            self.controller.close()

    def reconcile(self):
        proposal = self.controller.request_reconciliation()
        self.assertFalse(self.controller.ready)
        self.assertTrue(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=proposal.fingerprint))
        self.assertTrue(self.controller.ready)
        return proposal

    def test_explicit_reconciliation_required_even_without_journal(self):
        with self.assertRaises(RecoveryAdmissionError):
            self.controller.begin_operation(kind="save_metadata",
                evidence_hash="a"*64, epoch="", generation=0)
        proposal = self.controller.request_reconciliation()
        self.assertEqual(proposal.journal_state, RecoveryState.UNINITIALIZED)
        self.assertFalse(self.controller.ready)
        self.assertTrue(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=proposal.fingerprint))

    def test_successful_preflight_and_verification_only(self):
        self.reconcile()
        permit = self.controller.begin_operation(
            kind="save_metadata", evidence_hash="b" * 64,
            epoch=self.controller.epoch, generation=self.controller.generation)
        self.assertFalse(self.controller.ready)
        self.assertEqual(self.controller._store.read()[-1].state,
                         RecoveryState.IN_FLIGHT)
        self.assertTrue(self.controller.finish_operation(permit, verified=True))
        self.assertTrue(self.controller.ready)
        self.assertEqual(self.controller._store.read()[-1].state,
                         RecoveryState.READY)

    def test_uncertain_effect_quarantines_current_tenure(self):
        self.reconcile()
        permit = self.controller.begin_operation(
            kind="replace", evidence_hash="c" * 64,
            epoch=self.controller.epoch, generation=self.controller.generation)
        self.assertFalse(self.controller.finish_operation(permit, verified=False))
        self.assertFalse(self.controller.ready)
        with self.assertRaises(RecoveryAdmissionError):
            self.controller.begin_operation(kind="remove",
                evidence_hash="b"*64, epoch=permit.epoch, generation=permit.generation)

    def test_old_ready_after_new_tenure_does_not_authorise(self):
        self.reconcile()
        self.controller.close()
        another = TrustedOnboardingRecoveryController(
            self.metadata, mutex=FakeMutex())
        self.assertFalse(another.ready)
        with self.assertRaises(RecoveryAdmissionError):
            another.begin_operation(kind="clear_metadata",
                evidence_hash="d" * 64, epoch="", generation=0)
        second = another.request_reconciliation()
        self.assertEqual(second.journal_state, RecoveryState.READY)
        self.assertFalse(another.ready)
        another.close()

    def test_abandoned_and_unpersistable_quarantine_requires_human_reconciliation(self):
        self.reconcile()
        self.controller.close()
        abandoned = TrustedOnboardingRecoveryController(
            self.metadata, mutex=FakeMutex(MutexAdmission.ABANDONED))
        self.assertFalse(abandoned.ready)
        review = abandoned.request_reconciliation()
        self.assertTrue(review.operation_uncertain)
        self.assertFalse(abandoned.ready)
        abandoned.close()
        other = TrustedOnboardingRecoveryController(self.metadata, mutex=FakeMutex())
        self.assertFalse(other.ready)
        other_review = other.request_reconciliation()
        self.assertEqual(other_review.journal_state, RecoveryState.READY)
        self.assertFalse(other.ready)
        other.close()

    def test_reject_review_does_not_grant_authority(self):
        proposal = self.controller.request_reconciliation()
        self.assertFalse(self.controller.approve_reconciliation(
            human_approved=False, fingerprint=proposal.fingerprint))
        self.assertFalse(self.controller.ready)

    def test_controller_cache_shares_host_instance(self):
        x = TrustedOnboardingRecoveryController.for_path(self.metadata)
        y = TrustedOnboardingRecoveryController.for_path(self.metadata)
        self.assertIs(x, y)


if __name__ == "__main__":
    unittest.main()


class RecoveryArchiveCapacityTests(unittest.TestCase):
    def setUp(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from nayeon.brain.onboarding_recovery import TrustedOnboardingRecoveryController
        from nayeon.brain.onboarding_recovery_document import (
            RecoveryRecord, RecoveryState, GENESIS_HASH, record_hash,
            MAX_RECORDS,
        )
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "metadata.json"
        self.controller = TrustedOnboardingRecoveryController(self.path, mutex=FakeMutex())
        self.addCleanup(self.cleanup_controller)
        self.record_class = RecoveryRecord
        self.record_hash = record_hash
        self.GENESIS_HASH = GENESIS_HASH
        self.MAX_RECORDS = MAX_RECORDS

    def cleanup_controller(self):
        if self.controller._ctx is not None:
            self.controller.close()

    def fill_journal(self, count):
        last = None
        for i in range(1, count + 1):
            rec = self.record_class(
                schema_version=1, sequence=i, epoch="a"*32,
                generation=0, state=RecoveryState.READY,
                previous_hash=self.GENESIS_HASH if last is None else self.record_hash(last),
                evidence_hash="f"*64)
            self.controller._store.append(rec, create=last is None)
            last = rec
        return last

    def test_human_archive_required_and_preserves_prior_evidence(self):
        self.fill_journal(self.MAX_RECORDS - 3)
        review = self.controller.request_reconciliation()
        self.assertTrue(review.archive_required)
        self.assertFalse(review.archive_present)
        self.assertFalse(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        self.assertFalse(self.controller.ready)
        again = self.controller.request_reconciliation()
        self.assertTrue(self.controller.approve_reconciliation(
            human_approved=True, fingerprint=again.fingerprint,
            archive_acknowledged=True))
        self.assertTrue(self.controller.ready)
        self.assertEqual(len(self.controller._store.read()), 2)
        self.assertTrue(self.controller._store.archive_present())
        self.assertEqual(self.controller._store.read()[-1].state, RecoveryState.READY)

    def test_capacity_reserved_before_in_flight(self):
        from nayeon.brain.onboarding_recovery_store import RecoveryStoreUnavailable
        last = self.fill_journal(self.MAX_RECORDS - 1)
        in_flight = self.record_class(
            schema_version=1, sequence=self.MAX_RECORDS, epoch="a"*32,
            generation=0, state=RecoveryState.IN_FLIGHT,
            previous_hash=self.record_hash(last), operation_id="a"*32,
            operation_kind="save_metadata", evidence_hash="b"*64)
        with self.assertRaises(RecoveryStoreUnavailable):
            self.controller._store.append(in_flight)
        self.assertEqual(self.controller._store.read()[-1].state, RecoveryState.READY)

    def test_archive_then_new_checkpoint_failure_remains_unavailable(self):
        from unittest.mock import patch
        self.fill_journal(self.MAX_RECORDS - 3)
        review = self.controller.request_reconciliation()
        with patch("nayeon.brain.onboarding_recovery_store.os.fsync",
                   side_effect=OSError("synthetic after-archive failure")):
            self.assertFalse(self.controller.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint,
                archive_acknowledged=True))
        self.assertFalse(self.controller.ready)
        self.controller.close()
        fresh = TrustedOnboardingRecoveryController(self.path, mutex=FakeMutex())
        self.assertFalse(fresh.ready)
        r = fresh.request_reconciliation()
        self.assertTrue(r.archive_present)
        self.assertTrue(r.operation_uncertain)
        self.assertFalse(fresh.ready)
        fresh.close()


class ReconciledBaselineBindingTests(unittest.TestCase):
    def test_metadata_change_after_reconciliation_revokes_admission(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from nayeon.brain.connection_document import parse_provider_connection_document
        from nayeon.brain.connection_persistence import ProviderConnectionFileStore
        from nayeon.brain.onboarding_recovery import TrustedOnboardingRecoveryController, RecoveryAdmissionError
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        with TemporaryDirectory() as temp:
            path = Path(temp) / "metadata.json"
            ctrl = TrustedOnboardingRecoveryController(path, mutex=FakeMutex())
            try:
                reviewed = ctrl.request_reconciliation()
                self.assertTrue(ctrl.approve_reconciliation(
                    human_approved=True, fingerprint=reviewed.fingerprint))
                ProviderConnectionFileStore(path).save(
                    parse_provider_connection_document({
                        "schema_version": 1,
                        "connection": {
                            "provider":"openai","model":"gpt-6",
                            "credential":"openai.api_key"
                        }
                    }))
                with self.assertRaises(RecoveryAdmissionError):
                    ctrl.begin_operation(kind="clear_metadata",
                        evidence_hash="f"*64,epoch=ctrl.epoch,
                        generation=ctrl.generation)
                self.assertFalse(ctrl.ready)
                self.assertEqual(ctrl._store.read()[-1].state, RecoveryState.READY)
            finally:
                if ctrl._ctx is not None:
                    ctrl.close()


class UnownedObserverConflictRecoveryTests(unittest.TestCase):
    def test_conflicting_observer_before_acquisition_does_not_poison_owner(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from nayeon.brain.onboarding_recovery import (
            TrustedOnboardingRecoveryController, RecoveryAdmissionError,
        )
        from tests.test_credential_operation_host import FakeBackend
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"metadata.json"
            first=FakeBackend()
            ctrl=TrustedOnboardingRecoveryController.for_path(
                path,availability=first,mutex=FakeMutex())
            with self.assertRaises(RecoveryAdmissionError):
                TrustedOnboardingRecoveryController.for_path(
                    path,availability=FakeBackend(),mutex=ctrl._mutex)
            self.assertFalse(ctrl._faulted)
            self.assertIsNone(ctrl._ctx)
            review=ctrl.request_reconciliation()
            self.assertFalse(ctrl.ready)
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            self.assertTrue(ctrl.ready)
            ctrl.close()

    def test_conflicting_observer_after_ownership_still_invalidates_admission(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from nayeon.brain.onboarding_recovery import (
            TrustedOnboardingRecoveryController, RecoveryAdmissionError,
        )
        from tests.test_credential_operation_host import FakeBackend
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"metadata.json"
            ctrl=TrustedOnboardingRecoveryController.for_path(
                path,availability=FakeBackend(),mutex=FakeMutex())
            review=ctrl.request_reconciliation()
            self.assertTrue(ctrl.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
            with self.assertRaises(RecoveryAdmissionError):
                TrustedOnboardingRecoveryController.for_path(
                    path,availability=FakeBackend(),mutex=ctrl._mutex)
            self.assertFalse(ctrl.ready)
            ctrl.close()
