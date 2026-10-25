"""Phase8 BYOK fake-only trusted journey owner tests; zero real key/provider."""
import threading
import unittest

from nayeon.brain.onboarding_coordination import CoordinatedOutcome
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.secrets.contracts import SecretValue
from nayeon.desktop_alpha.first_run_connection_owner import (
    JourneyContext, JourneyRefused, TrustedFirstRunConnectionOwner,
)
from tests.test_first_run_credential_management_window import Harness


class Root:
    def __init__(self):
        self.alive = True

    def winfo_exists(self):
        return 1 if self.alive else 0


class ConnectionOwnerTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.configure()
        self.h.reconcile()
        self.addCleanup(self.h.close)
        self.root = Root()
        self.current = [True]
        self.ctx = JourneyContext(self.root, object(), object(), object(), 0)
        self.owner = TrustedFirstRunConnectionOwner(
            coordinator=self.h.coordinator,
            context=self.ctx,
            is_current=lambda: self.current[0],
        )
        self.addCleanup(lambda: self.owner.close(self.ctx))

    def effects(self):
        b, v = self.h.backend, self.h.validator
        return (b.puts, b.deletes, b.gets, v.calls)

    def test_constructor_and_explicit_start_are_no_storage_or_validation(self):
        before = self.effects()
        self.assertFalse(self.owner.closed)
        self.assertFalse(self.owner.uncertain)
        self.assertEqual(self.effects(), before)
        self.assertTrue(self.owner.start(self.ctx))
        self.assertEqual(self.effects(), before)
        self.assertFalse(self.owner.start(self.ctx))

    def test_connect_requires_explicit_review_and_approval(self):
        self.assertTrue(self.owner.start(self.ctx))
        before = self.effects()
        receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIsNotNone(review)
        self.assertEqual(self.effects(), before)
        refused = self.owner.confirm(self.ctx, review, candidate=SecretValue("fixture-good"))
        self.assertIs(refused.outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.effects(), before)
        accepted = self.owner.confirm(self.ctx, review, candidate=SecretValue("fixture-good"),
                                      explicitly_approved=True)
        self.assertIsInstance(accepted.outcome, CoordinatedOutcome)
        # Submitted is not a durable connection/storage/transaction proof.
        self.assertFalse(accepted.confirms_transaction)
        self.assertTrue(accepted.requires_reobservation)
        self.assertEqual(self.h.validator.calls, 1)
        self.assertEqual(self.h.backend.puts, 1)
        self.assertIs(self.owner.confirm(self.ctx, review, candidate=SecretValue("fixture-good"),
                                          explicitly_approved=True).outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertEqual(self.h.backend.puts, 1)

    def test_cancel_one_exact_review_and_no_effect(self):
        self.owner.start(self.ctx)
        receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIsInstance(self.owner.cancel(self.ctx, review).outcome, CoordinatedOutcome)
        self.assertIs(self.owner.cancel(self.ctx, review).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.effects(), (0, 0, 0, 0))

    def test_invalid_candidate_does_not_store(self):
        self.owner.start(self.ctx)
        _, review = self.owner.request(self.ctx, Op.CONNECT)
        response = self.owner.confirm(self.ctx, review, candidate=SecretValue("fixture-bad"),
                                      explicitly_approved=True)
        self.assertIsInstance(response.outcome, CoordinatedOutcome)
        self.assertEqual(self.h.backend.puts, 0)
        self.assertEqual(self.h.validator.calls, 1)
        self.assertFalse(response.confirms_transaction)

    def test_stale_view_liveness_fails_closed(self):
        self.owner.start(self.ctx)
        self.current[0] = False
        receipt, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertIs(receipt.outcome, CoordinatedOutcome.REFUSED)
        self.assertIsNone(review)
        self.assertEqual(self.effects(), (0, 0, 0, 0))
        self.assertTrue(self.owner.close(self.ctx))

    def test_conflicting_context_and_mutated_context_block(self):
        self.owner.start(self.ctx)
        foreign = JourneyContext(self.root, self.ctx.application, self.ctx.pane,
                                 self.ctx.journey, 0)
        self.assertFalse(self.owner.start(foreign))
        self.assertIs(self.owner.request(foreign, Op.CONNECT)[0].outcome,
                      CoordinatedOutcome.REFUSED)
        object.__setattr__(self.ctx, "generation", -1)
        self.assertIs(self.owner.request(self.ctx, Op.CONNECT)[0].outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertEqual(self.effects(), (0, 0, 0, 0))

    def test_wrong_thread_is_refused_before_dependency_touch(self):
        self.owner.start(self.ctx)
        errors = []
        def foreign():
            for fn in (lambda: self.owner.start(self.ctx),
                       lambda: self.owner.request(self.ctx, Op.CONNECT),
                       lambda: self.owner.reset(self.ctx),
                       lambda: self.owner.close(self.ctx)):
                try:
                    fn()
                except JourneyRefused as ex:
                    errors.append(str(ex))
        worker = threading.Thread(target=foreign)
        worker.start()
        worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, ["WRONG_THREAD"] * 4)
        self.assertEqual(self.effects(), (0, 0, 0, 0))

    def test_second_owner_cannot_adopt_first_approval(self):
        self.owner.start(self.ctx)
        competing = TrustedFirstRunConnectionOwner(
            coordinator=self.h.coordinator,
            context=JourneyContext(self.root, object(), object(), object(), 1),
            is_current=lambda: True,
        )
        self.assertFalse(competing.start(competing._ctx))
        self.assertTrue(competing.close(competing._ctx))
        receipt, first = self.owner.request(self.ctx, Op.CONNECT)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIsNotNone(first)
        self.assertEqual(self.h.backend.puts, 0)
        self.owner.cancel(self.ctx, first)

    def test_reentrant_close_inside_liveness_never_claims(self):
        ctx = JourneyContext(self.root, object(), object(), object(), 2)
        holder = []
        def live():
            holder[0].close(ctx)
            return True
        entrant = TrustedFirstRunConnectionOwner(coordinator=self.h.coordinator,
                                                 context=ctx, is_current=live)
        holder.append(entrant)
        self.assertFalse(entrant.start(ctx))
        self.assertTrue(entrant.closed)
        self.assertEqual(self.effects(), (0, 0, 0, 0))

    def test_close_retirement_and_stale_callback_refusal(self):
        self.owner.start(self.ctx)
        _, review = self.owner.request(self.ctx, Op.CONNECT)
        self.assertTrue(self.owner.close(self.ctx))
        self.assertTrue(self.owner.closed)
        self.assertFalse(self.owner.start(self.ctx))
        self.assertIs(self.owner.confirm(self.ctx, review, candidate=SecretValue("fixture-good"),
                                          explicitly_approved=True).outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertEqual(self.effects(), (0, 0, 0, 0))

    def test_destroyed_root_prevents_approval(self):
        self.owner.start(self.ctx)
        _, review = self.owner.request(self.ctx, Op.CONNECT)
        self.root.alive = False
        result = self.owner.confirm(self.ctx, review, candidate=SecretValue("fixture-good"),
                                    explicitly_approved=True)
        self.assertNotEqual(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assertEqual(self.h.backend.puts, 0)


    def _assert_opaque_host_refusal(self, operation):
        from unittest import mock
        from nayeon.brain.credential_operation_host import CredentialHostOutcome

        class HostileCandidate:
            def __bool__(self):
                raise AssertionError("OWNER_CONSULTED_CANDIDATE_TRUTHINESS")
            def __getattribute__(self, name):
                raise AssertionError("OWNER_CONSULTED_CANDIDATE_ATTRIBUTE")
            def __repr__(self):
                raise AssertionError("OWNER_LOGGED_CANDIDATE")
            def __str__(self):
                raise AssertionError("OWNER_STRINGIFIED_CANDIDATE")
            def __eq__(self, other):
                raise AssertionError("OWNER_COMPARED_CANDIDATE")

        if operation is Op.REPLACE:
            # The existing fake credential is test data only, not a real key.
            self.h.backend.value = SecretValue("fixture-good")
            self.h.reconcile()
        self.assertTrue(self.owner.start(self.ctx))
        before = self.effects()
        receipt, review = self.owner.request(self.ctx, operation)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIsNotNone(review)
        actual_host_results = []
        real_approve = type(self.h.host).approve
        def record_real_host(host, *args, **kwargs):
            result = real_approve(host, *args, **kwargs)
            actual_host_results.append(result)
            return result
        # Trusted host uses slots: patch its class method, not the instance.
        with mock.patch.object(type(self.h.host), "approve", new=record_real_host):
            result = self.owner.confirm(self.ctx, review,
                                        candidate=HostileCandidate(),
                                        explicitly_approved=True)
        self.assertIsNot(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assertEqual(len(actual_host_results), 1)
        self.assertIs(actual_host_results[0].outcome, CredentialHostOutcome.BLOCKED)
        self.assertEqual(self.effects(), before)
        self.assertIs(self.owner.confirm(self.ctx, review, candidate=None,
                                          explicitly_approved=True).outcome,
                      CoordinatedOutcome.REFUSED)

    def test_opaque_bad_connect_delegates_exact_type_to_trusted_host(self):
        self._assert_opaque_host_refusal(Op.CONNECT)

    def test_opaque_bad_replace_delegates_exact_type_to_trusted_host(self):
        self._assert_opaque_host_refusal(Op.REPLACE)



if __name__ == "__main__":
    unittest.main()
