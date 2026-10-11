"""Phase 8.26: fake-only admission, conflict, recovery, and Windows mutex tests."""
from contextlib import contextmanager
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import observe_connection
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost, CredentialHostOutcome
from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinatedOutcome, CoordinationReceipt,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.secrets.contracts import SecretIdentifier, SecretValue
from nayeon.secrets.lifecycle import BoundCredentialLifecycle
from nayeon.brain.windows_onboarding_mutex import WindowsOnboardingMutex, MutexAdmission
from nayeon.brain.onboarding_recovery import RecoveryAdmissionError
from nayeon.brain.onboarding_recovery_document import RecoveryState
from nayeon.brain.onboarding_recovery_store import OnboardingRecoveryJournalStore, RecoveryStoreUnavailable
from tests.test_credential_operation_host import FakeBackend, FakeValidator


class FakeMutex:
    def __init__(self, state=MutexAdmission.HELD):
        self.state=state
        self.entered=0
        self.exited=0
        self.active=False
    @contextmanager
    def hold(self):
        if self.active:
            yield MutexAdmission.BUSY
            return
        self.entered+=1
        self.active=True
        try:
            yield self.state
        finally:
            self.exited+=1
            self.active=False


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path=Path(directory.name)/"provider.json"
        self.backend=FakeBackend()
        self.validator=FakeValidator()
        self.mutex=FakeMutex()
        self.observer=lambda: observe_connection(self.path,self.backend)
        self.host=TrustedCredentialOperationHost(
            onboarding=OpenAICredentialOnboarding(BoundCredentialLifecycle(
                self.backend,SecretIdentifier("openai.api_key"),self.validator)),
            observe=self.observer,
        )
        self.coordinator=CooperativeOnboardingCoordinator(
            host=self.host, metadata_path=self.path,
            availability=self.backend, mutex=self.mutex,
        )
        self.controller=self.coordinator.recovery_controller
        self.addCleanup(lambda: self.controller.close() if self.controller._ctx is not None else None)
        self.reconcile()

    def reconcile(self):
        if self.controller._ctx is not None:
            self.controller.close()
        r=self.controller.request_reconciliation()
        assert self.controller.approve_reconciliation(
            human_approved=True, fingerprint=r.fingerprint)

    def configure(self, model="gpt-5.6", provider="openai"):
        ProviderConnectionFileStore(self.path).save(
            ProviderConnectionDocumentV1(connection=ProviderConnectionConfiguration(
                provider,model,SecretIdentifier("openai.api_key"))))

    def test_request_only_is_not_execution(self):
        r=self.coordinator.request(Op.CONNECT)
        self.assertIs(r.outcome,CoordinatedOutcome.PENDING)
        self.assertTrue(self.coordinator.has_pending)
        self.assertFalse(self.coordinator.recovery_marker_path.exists())
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))
        self.assertEqual(self.mutex.entered,1)
        self.coordinator.reject()
        self.assertFalse(self.coordinator.has_pending)

    def test_cooperative_connect_locks_one_approval(self):
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,CoordinatedOutcome.PENDING)
        receipt=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(receipt.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(receipt.host_outcome,CredentialHostOutcome.SUBMITTED)
        self.assertTrue(receipt.requires_reobservation)
        self.assertFalse(receipt.confirms_transaction)
        self.assertEqual((self.mutex.entered,self.mutex.exited),(1,0))
        self.assertEqual(self.mutex.entered,1)
        self.assertFalse(self.coordinator.recovery_marker_path.exists())
        self.assertEqual((self.backend.puts,self.validator.calls),(1,1))
        self.assertIs(self.coordinator.approve().outcome,CoordinatedOutcome.REFUSED)
        self.assertEqual(self.backend.puts,1)

    def test_request_denied_unsupported_and_no_key_probe(self):
        self.configure(provider="unsupported")
        old=self.backend.value
        result=self.coordinator.request(Op.CONNECT)
        self.assertIs(result.outcome,CoordinatedOutcome.REFUSED)
        self.assertEqual(self.backend.puts,0)
        self.assertIs(self.backend.value,old)

    def test_metadata_change_and_aba_rejected_without_mutation(self):
        self.configure("original")
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,CoordinatedOutcome.PENDING)
        self.configure("changed")
        self.configure("original")
        receipt=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(receipt.outcome,CoordinatedOutcome.CONFLICT)
        self.assertFalse(self.host.has_pending)
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))
        self.assertFalse(self.coordinator.recovery_marker_path.exists())

    def test_credential_presence_change_before_approval(self):
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,CoordinatedOutcome.PENDING)
        self.backend.value=SecretValue("someone-else")
        self.assertIs(self.coordinator.approve(candidate=SecretValue("fixture-good")).outcome,
                      CoordinatedOutcome.CONFLICT)
        self.assertEqual(self.backend.puts,0)

    def test_busy_mutex_is_fail_closed_and_review_consumed(self):
        self.controller.close()
        self.mutex.state=MutexAdmission.BUSY
        with self.assertRaises(RecoveryAdmissionError):
            self.controller.request_reconciliation()
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,
                      CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.host.has_pending)
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))
        self.assertFalse(self.coordinator.recovery_marker_path.exists())

    def test_abandoned_mutex_quarantines_future_operations(self):
        self.controller.close()
        self.mutex.state=MutexAdmission.ABANDONED
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,
                      CoordinatedOutcome.RECOVERY_REQUIRED)
        review=self.controller.request_reconciliation()
        self.assertTrue(review.operation_uncertain)
        self.assertFalse(self.controller.ready)
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,
                      CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))

    def test_prior_crash_marker_blocks_without_storage_effect(self):
        self.coordinator.recovery_marker_path.write_text("prior interrupted operation")
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,
                      CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.host.has_pending)
        self.assertEqual(self.backend.puts,0)

    def test_indeterminate_write_leaves_marker(self):
        self.coordinator.request(Op.CONNECT)
        def fail_put(*a):
            raise RuntimeError("secret-shaped-backend-error")
        self.backend.put=fail_put
        r=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(r.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(r.host_outcome,CredentialHostOutcome.INDETERMINATE)
        self.assertIs(self.controller._store.read()[-1].state,
                      RecoveryState.IN_FLIGHT)
        self.assertNotIn("secret-shaped",str(r))

    def test_invalid_replacement_preserves_original_and_clears_marker(self):
        self.configure()
        original=SecretValue("old-key")
        self.backend.value=original
        self.reconcile()
        self.assertIs(self.coordinator.request(Op.REPLACE).outcome,CoordinatedOutcome.PENDING)
        r=self.coordinator.approve(candidate=SecretValue("fixture-bad"))
        self.assertIs(r.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(r.host_outcome,CredentialHostOutcome.INVALID)
        self.assertIs(self.backend.value,original)
        self.assertFalse(self.coordinator.recovery_marker_path.exists())

    def test_rejected_review_never_acquires_mutex_or_creates_marker(self):
        self.coordinator.request(Op.CONNECT)
        r=self.coordinator.reject()
        self.assertIs(r.outcome,CoordinatedOutcome.REFUSED)
        self.assertEqual(self.mutex.entered,1)
        self.assertFalse(self.coordinator.recovery_marker_path.exists())
        self.assertIs(self.coordinator.approve().outcome,CoordinatedOutcome.REFUSED)

    def test_probe_exception_refuses_and_never_leaks(self):
        def fail(*a):
            raise RuntimeError("sensitive-not-for-UI")
        self.backend.is_available=fail
        result=self.coordinator.request(Op.CONNECT)
        self.assertIs(result.outcome,CoordinatedOutcome.UNAVAILABLE)
        self.assertNotIn("sensitive",str(result))
        self.assertFalse(self.host.has_pending)

    def test_nonsecret_receipt_never_claims_transaction(self):
        with self.assertRaises(ValueError):
            CoordinationReceipt(CoordinatedOutcome.COMPLETED,confirms_transaction=True)
        with self.assertRaises(ValueError):
            CoordinationReceipt(CoordinatedOutcome.COMPLETED,requires_reobservation=False)
        self.assertFalse(hasattr(self.coordinator,"__dict__"))

    def test_mutex_is_held_during_effect_and_released_afterward(self):
        original_put=self.backend.put
        def assert_owned(*args):
            self.assertTrue(self.mutex.active)
            return original_put(*args)
        self.backend.put=assert_owned
        self.coordinator.request(Op.CONNECT)
        receipt=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(receipt.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertTrue(self.mutex.active)

    def test_metadata_corruption_blocks_without_backend_mutation(self):
        self.path.write_text("not-json")
        result=self.coordinator.request(Op.CONNECT)
        self.assertIs(result.outcome,CoordinatedOutcome.UNAVAILABLE)
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))

    def test_failed_marker_creation_blocks_before_host_approval(self):
        from unittest.mock import patch
        self.coordinator.request(Op.CONNECT)
        with patch.object(OnboardingRecoveryJournalStore,"append",
                          side_effect=RecoveryStoreUnavailable("synthetic preflight failed")):
            receipt=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(receipt.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))
        self.assertFalse(self.host.has_pending)

    def test_mutex_unavailable_prevents_mutation(self):
        self.controller.close()
        self.mutex.state=MutexAdmission.UNAVAILABLE
        with self.assertRaises(RecoveryAdmissionError):
            self.controller.request_reconciliation()
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,
                      CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual((self.backend.puts,self.validator.calls),(0,0))

    def test_unverified_connect_preserves_recovery_evidence(self):
        # A SUBMITTED key has no independently proved exact-value readback.
        self.assertIs(self.coordinator.request(Op.CONNECT).outcome,CoordinatedOutcome.PENDING)
        receipt=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(receipt.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(self.controller._store.read()[-1].state,
                      RecoveryState.IN_FLIGHT)
        self.assertEqual(self.backend.puts,1)
        self.assertFalse(self.controller.ready)

    def test_metadata_changed_during_credential_write_requires_recovery(self):
        self.configure("original")
        original_put=self.backend.put
        def competing_put(*args):
            original_put(*args)
            self.configure("changed-during-write")
        self.backend.put=competing_put
        self.reconcile()
        self.coordinator.request(Op.CONNECT)
        r=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(r.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(self.controller._store.read()[-1].state,
                      RecoveryState.IN_FLIGHT)
        self.assertEqual(self.backend.puts,1)

    def test_metadata_changed_during_validation_rejects_result_not_storage(self):
        self.configure("original")
        original=self.validator.validate
        def competing_validation(value):
            self.configure("changed-during-validation")
            return original(value)
        self.validator.validate=competing_validation
        self.reconcile()
        self.coordinator.request(Op.TEST_CANDIDATE)
        r=self.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(r.outcome,CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(self.controller._store.read()[-1].state,RecoveryState.IN_FLIGHT)
        self.assertEqual(self.backend.puts,0)


@unittest.skipUnless(sys.platform=="win32","Windows native mutex only")
class ActualWindowsMutexTests(unittest.TestCase):
    def test_local_mutex_exclusion_and_release(self):
        mutex=WindowsOnboardingMutex()
        with mutex.hold() as held:
            self.assertIs(held,MutexAdmission.HELD)
            with WindowsOnboardingMutex().hold() as second:
                self.assertIs(second,MutexAdmission.BUSY)
            # A child process independently observes the same named mutex.
            child=(
                "from nayeon.brain.windows_onboarding_mutex import WindowsOnboardingMutex\n"
                "with WindowsOnboardingMutex().hold() as state:\n"
                "    print(state.value)\n"
            )
            result=subprocess.run(
                [sys.executable,"-c",child],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True,text=True,timeout=10,check=True)
            self.assertEqual(result.stdout.strip(),"busy")
        with WindowsOnboardingMutex().hold() as free:
            self.assertIs(free,MutexAdmission.HELD)


if __name__=="__main__":
    unittest.main()
