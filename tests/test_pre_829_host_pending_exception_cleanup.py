"""Pre-8.29 Q4: fake-only regression for orphaned host review on trusted evidence faults.

No real providers, credentials, WinCred, network, or native mutex acquisition.
"""
import unittest
from unittest import mock

from nayeon.brain.onboarding_coordination import CoordinatedOutcome
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
from nayeon.secrets.contracts import SecretValue
from tests.a02_fake_isolation_support import (
    FakeBackend, FakeValidator, FakeObserver, FakeMutex, FakeTempRoot,
    compose_fake_only_onboarding,
)


class HostPendingExceptionCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = FakeTempRoot()
        self.addCleanup(self.temp.cleanup)
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.observer = FakeObserver(self.backend)
        self.mutex = FakeMutex()
        self.comp = compose_fake_only_onboarding(
            backend=self.backend, validator=self.validator,
            observer=self.observer, mutex=self.mutex,
            temp_root=self.temp, metadata_path=self.temp.path / "provider.json",
        )
        self.ctrl = self.comp.controller
        self.coord = self.comp.coordinator
        review = self.ctrl.request_reconciliation()
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint,
            expected_review=review))
        self.owner = self.ctrl.claim_ui_window_owner()
        self.assertIsInstance(self.owner, str)
        self.root = object()
        self.addCleanup(lambda: self.ctrl.close_ui_window_owner(self.owner))

    def request(self):
        receipt, ticket = self.coord.request_ui(
            OnboardingOperation.CONNECT, owner_token=self.owner,
            root=self.root)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIsNotNone(ticket)
        return ticket

    def test_evidence_digest_exception_rejects_real_host_pending(self):
        old_ticket = self.request()
        self.assertTrue(self.comp.host.has_pending)
        with mock.patch(
            "nayeon.brain.onboarding_coordination.canonical_evidence_digest",
            side_effect=RuntimeError("synthetic digest fault")
        ):
            receipt = self.coord.approve_ui(
                ticket=old_ticket, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(receipt.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertIsNone(self.coord._pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertFalse(self.comp.host.has_pending)
        self.assertFalse(self.coord.has_pending)
        self.assertTrue(self.ctrl.ready)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)
        self.assertEqual(self.validator.calls, 0)
        self.assertIsNone(self.backend.value)

        fresh_ticket = self.request()
        self.assertIsNot(old_ticket, fresh_ticket)
        stale = self.coord.approve_ui(
            ticket=old_ticket, owner_token=self.owner, root=self.root,
            operation=OnboardingOperation.CONNECT,
            candidate=SecretValue("stale-synthetic"), acknowledged=True)
        self.assertIs(stale.outcome, CoordinatedOutcome.REFUSED)
        self.assertTrue(self.comp.host.has_pending)
        self.assertIs(self.coord._ui_ticket, fresh_ticket)
        self.assertIs(self.coord.reject_ui(
            ticket=fresh_ticket, owner_token=self.owner, root=self.root,
            operation=OnboardingOperation.CONNECT).outcome,
            CoordinatedOutcome.REFUSED)
        self.assertFalse(self.comp.host.has_pending)
        self.assertEqual(self.validator.calls, 0)

    def test_unexpected_admission_exception_rejects_real_host(self):
        ticket = self.request()
        with mock.patch.object(
            type(self.ctrl), "begin_operation",
            side_effect=RuntimeError("synthetic native admission fault")
        ):
            receipt = self.coord.approve_ui(
                ticket=ticket, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(receipt.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertTrue(self.ctrl.ready)
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)

    def test_rejection_dependency_failure_remains_refused_and_orphan_blocks(self):
        ticket = self.request()
        # Inject a failure into the original host rejection dependency only:
        # no production approval function is substituted.
        with mock.patch(
            "nayeon.brain.onboarding_coordination.canonical_evidence_digest",
            side_effect=RuntimeError("synthetic digest fault")
        ), mock.patch.object(
            type(self.comp.host), "reject",
            side_effect=RuntimeError("synthetic reject fault")
        ):
            receipt = self.coord.approve_ui(
                ticket=ticket, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(receipt.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertTrue(self.comp.host.has_pending)
        refused, successor = self.coord.request_ui(
            OnboardingOperation.CONNECT, owner_token=self.owner, root=self.root)
        self.assertIs(refused.outcome, CoordinatedOutcome.REFUSED)
        self.assertIsNone(successor)
        self.assertIs(self.coord.approve(
            candidate=SecretValue("synthetic")).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self.coord.reject()
        self.assertFalse(self.comp.host.has_pending)

    def test_validator_fault_does_not_mark_unknown_effect_complete(self):
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        ticket = self.request()
        with mock.patch.object(FakeValidator, "validate",
                               side_effect=RuntimeError("synthetic validation fault")):
            result = self.coord.approve_ui(
                ticket=ticket, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(result.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.ctrl.ready)
        self.assertFalse(self.comp.host.has_pending)
        self.assertFalse(self.coord.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertTrue(self.ctrl._store.read())
        self.assertIs(self.ctrl._store.read()[-1].state, RecoveryState.IN_FLIGHT)
        self.assertNotIn("put", self.backend.calls)
        self.assertIsNone(self.backend.value)

    def test_after_fake_write_exception_remains_uncertain_no_retry(self):
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        ticket = self.request()
        original_put = FakeBackend.put
        effects = []

        def injected_post_effect(backend, identifier, value):
            original_put(backend, identifier, value)
            effects.append("effect_written")
            raise RuntimeError("synthetic post-write fault")

        with mock.patch.object(FakeBackend, "put", injected_post_effect):
            result = self.coord.approve_ui(
                ticket=ticket, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(result.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual(effects, ["effect_written"])
        self.assertEqual(self.backend.calls.count("put"), 1)
        self.assertFalse(self.ctrl.ready)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIs(self.ctrl._store.read()[-1].state, RecoveryState.IN_FLIGHT)
        refused, successor = self.coord.request_ui(
            OnboardingOperation.CONNECT, owner_token=self.owner, root=self.root)
        self.assertIs(refused.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIsNone(successor)
        self.assertEqual(self.backend.calls.count("put"), 1)

    def test_host_eligibility_exception_cleans_original_review(self):
        # An exception after IN_FLIGHT admission must not strand host A.
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        old = self.request()
        with mock.patch(
            "nayeon.brain.credential_operation_host.advise_onboarding_operation",
            side_effect=RuntimeError("synthetic eligibility error")
        ):
            receipt = self._approve(old)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(self._journal()[0], RecoveryState.IN_FLIGHT)
        self.assertFalse(self.comp.host.has_pending)
        self.assertFalse(self.coord.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self._assert_no_effect()

    def test_host_eligibility_exception_does_not_cancel_host_only_b(self):
        # Reentrant host B has a distinct ticket, never owned by A.
        from nayeon.brain import credential_operation_host as module
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        old = self.request()
        original = module.advise_onboarding_operation
        successors = []

        def replace_then_fault(*args, **kwargs):
            with mock.patch.object(module, "advise_onboarding_operation", original):
                self.comp.host.reject()
                successors.append(self.comp.host.request_candidate_validation())
            raise RuntimeError("synthetic eligibility reentrancy")

        with mock.patch.object(module, "advise_onboarding_operation",
                               side_effect=replace_then_fault):
            receipt = self._approve(old)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(self._journal()[0], RecoveryState.IN_FLIGHT)
        self.assertIsNotNone(successors[0])
        self.assertTrue(self.comp.host.has_pending)
        self.assertFalse(self.coord.has_pending)
        self._assert_no_effect()
        self.assertIsNotNone(self.comp.host.reject_candidate_validation(
            ticket=successors[0]))
        self.assertFalse(self.comp.host.has_pending)

    def test_reentrant_success_must_not_approve_unconsented_successor(self):
        # Negative security control: A approval may never be transferred to
        # newly created legacy review B by a trusted digest callback.
        import nayeon.brain.onboarding_coordination as module
        old = self.request()
        original_digest = module.canonical_evidence_digest
        issued = []

        def switch_to_b_and_return(*args, **kwargs):
            self.comp.host.reject()
            issued.append(self.coord.request(OnboardingOperation.CONNECT).outcome)
            return original_digest(*args, **kwargs)

        with mock.patch.object(module, "canonical_evidence_digest",
                               side_effect=switch_to_b_and_return):
            receipt = self._approve(old, "synthetic-A-only")
        self.assertEqual(issued, [CoordinatedOutcome.PENDING])
        self.assertNotIn(receipt.outcome, (CoordinatedOutcome.COMPLETED,))
        # B has no independent UI ticket or consent. Not even a fake write.
        self.assertEqual(self.backend.calls.count("put"), 0,
                         "Approval A was incorrectly applied to successor B")
        self.assertEqual(self.validator.calls, 0)

    def test_exception_cleanup_must_not_cancel_host_only_successor(self):
        # Candidate-validation B can exist only at the host boundary; A's
        # exception cleanup still must not take ownership of B's review.
        old = self.request()
        issued = []

        def switch_to_host_b_and_fault(*args, **kwargs):
            self.comp.host.reject()
            issued.append(self.comp.host.request_candidate_validation())
            raise RuntimeError("synthetic A digest fault")

        with mock.patch(
            "nayeon.brain.onboarding_coordination.canonical_evidence_digest",
            side_effect=switch_to_host_b_and_fault
        ):
            receipt = self._approve(old)
        self.assertIs(receipt.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertIsNotNone(issued[0])
        self.assertTrue(self.comp.host.has_pending,
                        "A cleanup cancelled B's independent host review")
        self.assertEqual(self.backend.calls.count("put"), 0)
        self.comp.host.reject()

    def test_reentrant_legacy_b_is_not_rejected_by_a_exception_cleanup(self):
        # A trusted dependency may synchronously cancel A and request B.
        # The consumed A exception path must not reject B's real host review.
        old = self.request()
        created = []

        def reenter_then_fault(*args, **kwargs):
            self.comp.host.reject()
            issued = self.coord.request(OnboardingOperation.CONNECT)
            created.append(issued.outcome)
            raise RuntimeError("synthetic evidence dependency reentered")

        with mock.patch(
            "nayeon.brain.onboarding_coordination.canonical_evidence_digest",
            side_effect=reenter_then_fault
        ):
            result = self.coord.approve_ui(
                ticket=old, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(result.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertEqual(created, [CoordinatedOutcome.PENDING])
        self.assertIsNotNone(self.coord._pending)
        self.assertTrue(self.comp.host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self.assertIs(
            self.coord.approve_ui(
                ticket=old, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True).outcome,
            CoordinatedOutcome.REFUSED)
        self.assertTrue(self.comp.host.has_pending)
        self.coord.reject()
        self.assertFalse(self.comp.host.has_pending)

    def test_recovery_admission_refusal_still_clears_host(self):
        ticket = self.request()
        from nayeon.brain.onboarding_recovery import RecoveryAdmissionError
        with mock.patch.object(
            type(self.ctrl), "begin_operation",
            side_effect=RecoveryAdmissionError("synthetic admission denied")
        ):
            receipt = self.coord.approve_ui(
                ticket=ticket, owner_token=self.owner, root=self.root,
                operation=OnboardingOperation.CONNECT,
                candidate=SecretValue("synthetic"), acknowledged=True)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertNotIn("put", self.backend.calls)
        self.assertEqual(self.validator.calls, 0)

    def _approve(self, ticket, label="synthetic-q4"):
        return self.coord.approve_ui(
            ticket=ticket, owner_token=self.owner, root=self.root,
            operation=OnboardingOperation.CONNECT,
            candidate=SecretValue(label), acknowledged=True)

    def _journal(self):
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        records = self.ctrl._store.read()
        self.assertTrue(records)
        return records[-1].state, self.ctrl.journal_path.read_bytes()

    def _assert_no_effect(self):
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)
        self.assertIsNone(self.backend.value)
        self.assertEqual(self.validator.calls, 0)

    def test_unexpected_admission_exception_clears_host_without_effect(self):
        ticket = self.request()
        from nayeon.brain.onboarding_recovery import RecoveryAdmissionError
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        state_before, journal_before = self._journal()
        self.assertIs(state_before, RecoveryState.READY)
        with mock.patch.object(type(self.ctrl), "begin_operation",
                               side_effect=RuntimeError("synthetic pre-effect fault")):
            result = self._approve(ticket)
        self.assertIs(result.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertFalse(self.comp.host.has_pending)
        self.assertFalse(self.coord.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertTrue(self.ctrl.ready)
        self.assertEqual(self._journal()[1], journal_before)
        self._assert_no_effect()

    def test_digest_failure_fresh_b_requires_own_approval(self):
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        old = self.request()
        original_journal = self._journal()[1]
        with mock.patch(
            "nayeon.brain.onboarding_coordination.canonical_evidence_digest",
            side_effect=RuntimeError("synthetic digest fault")
        ):
            self.assertIs(self._approve(old).outcome,
                          CoordinatedOutcome.UNAVAILABLE)
        self.assertEqual(self._journal()[1], original_journal)
        self._assert_no_effect()
        new = self.request()
        self.assertIsNot(old, new)
        self.assertIs(self._approve(old, "synthetic-stale").outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertIs(self.coord.reject_ui(
            ticket=old, owner_token=self.owner, root=self.root,
            operation=OnboardingOperation.CONNECT).outcome,
            CoordinatedOutcome.REFUSED)
        self.assertIs(self.coord._ui_ticket, new)
        self.assertTrue(self.comp.host.has_pending)
        self.assertIs(self._approve(new, "synthetic-independent-B").outcome,
                      CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual(self.backend.calls.count("put"), 1)
        self.assertEqual(self.validator.calls, 1)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIs(self._journal()[0], RecoveryState.IN_FLIGHT)
        self.assertIs(self._approve(old).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.backend.calls.count("put"), 1)

    def test_validator_exception_before_write_no_retry(self):
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        ticket = self.request()
        with mock.patch.object(type(self.validator), "validate",
                               side_effect=RuntimeError("synthetic validator fault")):
            receipt = self._approve(ticket)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual(self.backend.calls.count("put"), 0)
        self.assertIsNone(self.backend.value)
        self.assertIs(self._journal()[0], RecoveryState.IN_FLIGHT)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIs(self._approve(ticket).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.backend.calls.count("put"), 0)

    def test_backend_recorded_write_then_exception_no_retry(self):
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        ticket = self.request()
        def record_then_fail(backend, identifier, value):
            backend.calls.append("put")
            backend.value = value
            raise RuntimeError("synthetic post-write exception")
        with mock.patch.object(type(self.backend), "put", record_then_fail):
            receipt = self._approve(ticket)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertEqual(self.backend.calls.count("put"), 1)
        self.assertIsNotNone(self.backend.value)
        self.assertIs(self._journal()[0], RecoveryState.IN_FLIGHT)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIs(self._approve(ticket).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.backend.calls.count("put"), 1)

    def test_finalization_exception_retains_inflight_evidence(self):
        from nayeon.brain.onboarding_recovery import RecoveryAdmissionError
        from nayeon.brain.onboarding_recovery_document import RecoveryState
        ticket = self.request()
        with mock.patch.object(type(self.ctrl), "finish_operation",
                               side_effect=RecoveryAdmissionError("synthetic finish fault")):
            receipt = self._approve(ticket)
        self.assertIs(receipt.outcome, CoordinatedOutcome.RECOVERY_REQUIRED)
        self.assertIs(self._journal()[0], RecoveryState.IN_FLIGHT)
        self.assertEqual(self.backend.calls.count("put"), 1)
        self.assertFalse(self.comp.host.has_pending)
        self.assertIs(self._approve(ticket).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.backend.calls.count("put"), 1)

    def test_reject_failure_retains_unavailable_host_review(self):
        old = self.request()
        with mock.patch(
            "nayeon.brain.onboarding_coordination.canonical_evidence_digest",
            side_effect=RuntimeError("synthetic evidence error")
        ), mock.patch.object(type(self.comp.host), "reject",
                             side_effect=RuntimeError("synthetic reject error")):
            receipt = self._approve(old)
        self.assertIs(receipt.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertTrue(self.comp.host.has_pending)
        self.assertFalse(self.coord.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertIs(self._approve(old).outcome, CoordinatedOutcome.REFUSED)
        self._assert_no_effect()
        self.comp.host.reject()  # Cleanup synthetic orphan for test isolation.


if __name__ == "__main__":
    unittest.main()
