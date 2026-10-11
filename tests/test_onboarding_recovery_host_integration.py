"""Production-default hosts exercised with fake mutex and local temporary metadata.

These tests do not access the native key store, provider or live credentials.
"""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from nayeon.brain.onboarding_metadata_commit import (
    TrustedMetadataCommitHost, MetadataCommitOutcome,
)
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from nayeon.brain.onboarding_recovery import TrustedOnboardingRecoveryController
from nayeon.brain.onboarding_recovery_document import RecoveryState


class FakeWindowsMutex:
    outcome = MutexAdmission.HELD
    def __init__(self):
        self.active = False
    @contextmanager
    def hold(self):
        if self.active:
            yield MutexAdmission.BUSY
            return
        self.active = True
        try:
            yield self.outcome
        finally:
            self.active = False


class ProductionMetadataRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "settings.json"
        self.mutex_factory = patch(
            "nayeon.brain.onboarding_recovery.WindowsOnboardingMutex",
            FakeWindowsMutex)
        self.mutex_factory.start()
        self.addCleanup(self.mutex_factory.stop)
        self.host = TrustedMetadataCommitHost(metadata_path=self.path)
        self.ctrl = self.host.recovery_controller
        self.addCleanup(self.close_controller)

    def close_controller(self):
        if self.ctrl._ctx is not None:
            self.ctrl.close()

    def human_reconcile(self):
        review = self.ctrl.request_reconciliation()
        self.assertFalse(self.ctrl.ready)
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))

    def test_default_host_denies_request_before_reconciliation(self):
        self.assertEqual(self.host.request_save("gpt-6").outcome,
                         MetadataCommitOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.path.exists())

    def test_production_default_save_requires_preflight_and_verifies(self):
        self.human_reconcile()
        self.assertEqual(self.host.request_save("gpt-6").outcome,
                         MetadataCommitOutcome.PENDING)
        self.assertEqual(self.host.approve(human_approved=True).outcome,
                         MetadataCommitOutcome.VERIFIED)
        self.assertTrue(self.path.exists())
        self.assertTrue(self.ctrl.ready)

    def test_failed_preflight_blocks_actual_metadata_effect(self):
        self.human_reconcile()
        self.assertEqual(self.host.request_save("gpt-6").outcome,
                         MetadataCommitOutcome.PENDING)
        with patch("nayeon.brain.onboarding_recovery_store.os.fsync",
                   side_effect=PermissionError("synthetic unavailable")):
            self.assertEqual(self.host.approve(human_approved=True).outcome,
                             MetadataCommitOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.path.exists())
        self.assertFalse(self.ctrl.ready)

    def test_persisted_ready_cannot_authorize_reconstructed_default_host(self):
        self.human_reconcile()
        self.ctrl.close()
        new_host = TrustedMetadataCommitHost(metadata_path=self.path)
        self.assertEqual(new_host.request_save("gpt-6").outcome,
                         MetadataCommitOutcome.RECOVERY_REQUIRED)
        review = new_host.recovery_controller.request_reconciliation()
        self.assertEqual(review.journal_state.value, "ready")
        self.assertFalse(new_host.recovery_controller.ready)


if __name__ == "__main__":
    unittest.main()


class ProductionCredentialRecoveryTests(unittest.TestCase):
    def setUp(self):
        from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
        from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
        from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
        from nayeon.secrets.contracts import SecretIdentifier
        from nayeon.secrets.lifecycle import BoundCredentialLifecycle
        from nayeon.brain.connection_reconciliation import observe_connection
        from tests.test_credential_operation_host import FakeBackend, FakeValidator
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "credential-provider.json"
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.fake_windows = patch(
            "nayeon.brain.onboarding_recovery.WindowsOnboardingMutex", FakeWindowsMutex)
        self.fake_windows.start()
        self.addCleanup(self.fake_windows.stop)
        lifecycle = BoundCredentialLifecycle(
            self.backend, SecretIdentifier("openai.api_key"), self.validator)
        self.host = TrustedCredentialOperationHost(
            onboarding=OpenAICredentialOnboarding(lifecycle),
            observe=lambda: observe_connection(self.path, self.backend))
        self.coordinator = CooperativeOnboardingCoordinator(
            host=self.host, metadata_path=self.path, availability=self.backend)
        self.ctrl = self.coordinator.recovery_controller
        self.addCleanup(self.close_controller)

    def close_controller(self):
        if self.ctrl._ctx is not None:
            self.ctrl.close()

    def test_key_connect_denied_before_reconciliation(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
        from nayeon.brain.onboarding_coordination import CoordinatedOutcome
        self.assertEqual(self.coordinator.request(Op.CONNECT).outcome,
                         CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual(self.backend.puts, 0)

    def test_key_connect_is_never_claimed_verified_without_readback(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
        from nayeon.brain.onboarding_coordination import CoordinatedOutcome
        from nayeon.secrets.contracts import SecretValue
        review = self.ctrl.request_reconciliation()
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        self.assertEqual(self.coordinator.request(Op.CONNECT).outcome,
                         CoordinatedOutcome.PENDING)
        result = self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertEqual(result.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.ctrl.ready)
        self.assertEqual(self.ctrl._store.read()[-1].state, RecoveryState.IN_FLIGHT)
        self.assertEqual(self.backend.puts, 1)


class InjectedMutexRecoveryGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "injected.json"

    def test_injected_abandoned_metadata_mutex_does_not_bypass_review(self):
        mutex = FakeWindowsMutex()
        mutex.outcome = MutexAdmission.ABANDONED
        host = TrustedMetadataCommitHost(metadata_path=self.path, mutex=mutex)
        self.assertIsNotNone(host.recovery_controller)
        self.assertEqual(host.request_save("gpt-6").outcome,
                         MetadataCommitOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.path.exists())
        review = host.recovery_controller.request_reconciliation()
        self.assertTrue(review.operation_uncertain)
        with patch("nayeon.brain.onboarding_recovery_store.os.fsync",
                   side_effect=OSError("forced cannot write recovery record")):
            self.assertFalse(host.recovery_controller.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint))
        self.assertFalse(host.recovery_controller.ready)
        host.recovery_controller.close()
        restarted = TrustedMetadataCommitHost(metadata_path=self.path,
                                              mutex=mutex)
        self.assertEqual(restarted.request_save("gpt-6").outcome,
                         MetadataCommitOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.path.exists())

    def test_conflicting_availability_observer_after_review_revokes_authority(self):
        from tests.test_credential_operation_host import FakeBackend
        first = FakeBackend()
        second = FakeBackend()
        mutex = FakeWindowsMutex()
        controller = TrustedOnboardingRecoveryController.for_path(
            self.path, availability=first, mutex=mutex)
        self.addCleanup(lambda: controller.close() if controller._ctx is not None else None)
        review = controller.request_reconciliation()
        self.assertTrue(controller.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        with self.assertRaises(Exception):
            TrustedOnboardingRecoveryController.for_path(
                self.path, availability=second, mutex=mutex)
        self.assertFalse(controller.ready)

    def test_metadata_first_observer_added_after_ready_forces_new_review(self):
        from tests.test_credential_operation_host import FakeBackend
        ctrl = TrustedOnboardingRecoveryController.for_path(
            self.path, mutex=FakeWindowsMutex())
        self.addCleanup(lambda: ctrl.close() if ctrl._ctx is not None else None)
        r = ctrl.request_reconciliation()
        self.assertTrue(ctrl.approve_reconciliation(
            human_approved=True, fingerprint=r.fingerprint))
        with self.assertRaises(Exception):
            TrustedOnboardingRecoveryController.for_path(
                self.path, availability=FakeBackend())
        self.assertFalse(ctrl.ready)


class CredentialDeleteEvidenceGuardTests(ProductionCredentialRecoveryTests):
    def test_injected_mutex_never_skips_recovery(self):
        from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator, CoordinatedOutcome
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        other_path = self.path.with_name("injected-credential.json")
        ctrl = CooperativeOnboardingCoordinator(
            host=self.host, metadata_path=other_path,
            availability=self.backend, mutex=FakeWindowsMutex())
        self.assertIsNotNone(ctrl.recovery_controller)
        self.assertEqual(ctrl.request(OnboardingOperation.CONNECT).outcome,
                         CoordinatedOutcome.RECOVERY_REQUIRED)

    def test_remove_no_op_cannot_restore_ready(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation
        from nayeon.brain.onboarding_coordination import CoordinatedOutcome
        from nayeon.secrets.contracts import SecretValue
        self.backend.value = SecretValue("fixture-good")
        mutex = self.ctrl._mutex
        review = self.ctrl.request_reconciliation()
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        self.assertEqual(self.coordinator.request(OnboardingOperation.REMOVE).outcome,
                         CoordinatedOutcome.PENDING)
        # A buggy backend claims completion while leaving the key present.
        with patch.object(self.backend, "delete", return_value=True):
            receipt = self.coordinator.approve()
        self.assertEqual(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.ctrl.ready)
        self.assertEqual(self.ctrl._store.read()[-1].state, RecoveryState.IN_FLIGHT)
        self.assertTrue(self.backend.is_available(
            __import__("nayeon.secrets.contracts",fromlist=["SecretIdentifier"]).SecretIdentifier("openai.api_key")))


class CredentialNonmutatingReviewTests(ProductionCredentialRecoveryTests):
    def test_candidate_validation_uses_recognized_journal_kind(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
        from nayeon.brain.onboarding_coordination import CoordinatedOutcome
        from nayeon.secrets.contracts import SecretValue
        review = self.ctrl.request_reconciliation()
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint))
        result = self.coordinator.request(Op.TEST_CANDIDATE)
        self.assertEqual(result.outcome, CoordinatedOutcome.PENDING)
        approved = self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertEqual(approved.outcome, CoordinatedOutcome.COMPLETED)
        self.assertTrue(self.ctrl.ready)
        self.assertEqual(self.backend.puts, 0)
        self.assertEqual(self.backend.deletes, 0)
        self.assertEqual(self.ctrl._store.read()[-1].state, RecoveryState.READY)
