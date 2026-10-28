"""Fake-only revocation tests: count effect ATTEMPTS at the actual call entry.

No Tk objects, SDK, native credential backend or network are constructed.
The existing harness injects FakeBackend, FakeValidator, FakeMutex and a
TemporaryDirectory into the real coordinator/host/lifecycle trust path.
"""
import threading
import unittest
from unittest import mock

from nayeon.brain import onboarding_coordination as coordination
from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinatedOutcome,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.brain.onboarding_recovery_document import RecoveryState
from nayeon.desktop_alpha.first_run_connection_owner import (
    JourneyContext, JourneyRefused, TrustedFirstRunConnectionOwner,
)
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.lifecycle import BoundCredentialLifecycle
from tests.test_first_run_credential_management_window import Harness


class FakeRoot:
    def __init__(self):
        self.live = True

    def destroy(self):
        self.live = False

    def winfo_exists(self):
        return int(self.live)


class CancelledEffectTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.close)
        self.h.configure()
        self.h.reconcile()
        self.root = FakeRoot()
        self.ctx = JourneyContext(self.root, object(), object(), object(), 1)
        self.probe = lambda: True
        self.owner = TrustedFirstRunConnectionOwner(
            coordinator=self.h.coordinator, context=self.ctx,
            is_current=lambda: self.probe())
        self.addCleanup(lambda: self.owner.close(self.owner._ctx))
        self.attempts = dict(get=0, put=0, delete=0, validate=0)
        for target, name in ((self.h.backend, "get"), (self.h.backend, "put"),
                             (self.h.backend, "delete"),
                             (self.h.validator, "validate")):
            original = getattr(target, name)

            def attempt(*args, _name=name, _original=original, **kwargs):
                # Increment BEFORE consulting state or delegating to the fake.
                self.attempts[_name] += 1
                return _original(*args, **kwargs)

            patcher = mock.patch.object(target, name, new=attempt)
            patcher.start()
            self.addCleanup(patcher.stop)

    def prepare(self, operation=Op.CONNECT):
        if operation in (Op.REPLACE, Op.REMOVE, Op.TEST_STORED):
            self.h.backend.value = SecretValue("fixture-good")
            self.h.reconcile()
        self.assertTrue(self.owner.start(self.ctx))
        receipt, review = self.owner.request(self.ctx, operation)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertIsNotNone(review)
        self.assert_attempts()
        return review

    def confirm(self, review):
        candidate = (None if review.operation in (Op.REMOVE, Op.TEST_STORED)
                     else SecretValue("fixture-good"))
        return self.owner.confirm(
            self.ctx, review, candidate=candidate, explicitly_approved=True,
            acknowledged_delete=review.operation is Op.REMOVE)

    def assert_attempts(self, *, get=0, put=0, delete=0, validate=0):
        self.assertEqual(self.attempts,
                         dict(get=get, put=put, delete=delete, validate=validate))

    def assert_uncertain(self, result):
        self.assertIs(result.outcome, CoordinatedOutcome.INDETERMINATE)
        self.assertTrue(self.owner.uncertain)
        self.assertTrue(result.requires_reobservation)
        self.assertFalse(result.confirms_transaction)

    def assert_inflight(self):
        self.assertIs(self.h.controller._store.read()[-1].state,
                      RecoveryState.IN_FLIGHT)
        self.assertFalse(self.h.controller.ready)

    def test_close_before_journal_admission_prevents_all_effect_attempts(self):
        review = self.prepare()
        original = coordination.canonical_evidence_digest
        seam = []

        def close_before_admission(**kwargs):
            seam.append(True)
            self.assertFalse(self.owner.close(self.ctx))  # busy: deferred
            return original(**kwargs)

        with mock.patch.object(coordination, "canonical_evidence_digest",
                               new=close_before_admission), mock.patch.object(
                type(self.h.controller), "begin_operation",
                side_effect=AssertionError("revoked journal admission")) as admission:
            result = self.confirm(review)
        self.assertEqual(seam, [True])
        admission.assert_not_called()
        self.assert_attempts()
        self.assert_uncertain(result)

    def test_close_during_journal_admission_preserves_uncertainty(self):
        review = self.prepare()
        original = type(self.h.controller).begin_operation
        seam = []

        def admitted_then_close(controller, **kwargs):
            permit = original(controller, **kwargs)
            seam.append(True)
            self.owner.close(self.ctx)
            return permit

        with mock.patch.object(type(self.h.controller), "begin_operation",
                               new=admitted_then_close):
            result = self.confirm(review)
        self.assertEqual(seam, [True])
        self.assert_attempts()
        self.assert_uncertain(result)
        self.assert_inflight()

    def test_close_in_host_observation_prevents_lifecycle_effects(self):
        review = self.prepare()
        original = type(self.h.host)._fresh
        seam = []

        def close_during_observation(host):
            observed = original(host)
            seam.append(True)
            self.owner.close(self.ctx)
            return observed

        with mock.patch.object(type(self.h.host), "_fresh",
                               new=close_during_observation):
            result = self.confirm(review)
        self.assertEqual(seam, [True])
        self.assert_attempts()
        self.assert_uncertain(result)
        self.assert_inflight()

    def close_at_lifecycle_gate(self, operation, method, *, validations=0):
        review = self.prepare(operation)
        original = getattr(BoundCredentialLifecycle, method)
        seam = []

        def close_before_gate(lifecycle, *args, **kwargs):
            # This is BEFORE the original method's _require_live and effect;
            # the backend/validator itself never suppresses a revoked call.
            seam.append(True)
            self.assertTrue(callable(kwargs.get("_approval_live")))
            self.assertFalse(self.owner.close(self.ctx))
            return original(lifecycle, *args, **kwargs)

        with mock.patch.object(BoundCredentialLifecycle, method,
                               new=close_before_gate):
            result = self.confirm(review)
        self.assertEqual(seam, [True])
        self.assert_attempts(validate=validations)
        self.assert_uncertain(result)
        self.assert_inflight()
        self.assertFalse(self.owner.start(self.ctx))

    def test_connect_close_before_validator_attempt(self):
        self.close_at_lifecycle_gate(Op.CONNECT, "test_candidate")

    def test_replace_close_before_validator_attempt(self):
        self.close_at_lifecycle_gate(Op.REPLACE, "test_candidate")

    def test_candidate_test_close_before_validator_attempt(self):
        self.close_at_lifecycle_gate(Op.TEST_CANDIDATE, "test_candidate")

    def test_stored_test_close_before_backend_get_attempt(self):
        self.close_at_lifecycle_gate(Op.TEST_STORED, "test_stored")

    def test_remove_close_before_backend_delete_attempt(self):
        self.close_at_lifecycle_gate(Op.REMOVE, "remove")

    def revoke_during_final_lifecycle_probe(self, revoke):
        review = self.prepare(Op.REMOVE)
        original = BoundCredentialLifecycle.remove
        probes = []

        def enter_final_gate(lifecycle, *args, **kwargs):
            self.assertTrue(callable(kwargs.get("_approval_live")))

            def report_live_after_revocation():
                probes.append(True)
                # _still_owner checks controller ownership between two UI
                # probes. Revoke in its LAST probe while still returning True.
                if len(probes) == 2:
                    revoke()
                return True

            self.probe = report_live_after_revocation
            return original(lifecycle, *args, **kwargs)

        with mock.patch.object(BoundCredentialLifecycle, "remove",
                               new=enter_final_gate):
            result = self.confirm(review)
        self.assertGreaterEqual(len(probes), 2)
        self.assert_attempts()
        self.assertIsNot(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assert_inflight()

    def test_root_destroyed_during_final_lifecycle_probe_prevents_attempts(self):
        self.revoke_during_final_lifecycle_probe(self.root.destroy)

    def test_tenure_closed_during_final_lifecycle_probe_prevents_attempts(self):
        self.revoke_during_final_lifecycle_probe(
            lambda: self.h.controller.close_ui_window_owner(self.owner._owner_token))

    def test_close_during_finish_observation_never_persists_ready(self):
        review = self.prepare(Op.REMOVE)
        controller = self.h.controller
        original = type(controller).finish_operation
        observe_presence = self.h.backend.is_available
        observed = []
        finalizations = []

        def finish_with_reentrant_observation(ctrl, permit, **kwargs):
            self.assertIs(ctrl, controller)
            self.assertIs(kwargs["verified"], True)
            self.assertTrue(callable(kwargs["approval_live"]))
            inflight = ctrl._store.read()
            generation = ctrl.generation

            def close_during_presence_probe(*args):
                observed.append(True)
                self.assertFalse(self.owner.close(self.ctx))  # busy: deferred
                return observe_presence(*args)

            with mock.patch.object(self.h.backend, "is_available",
                                   new=close_during_presence_probe):
                finished = original(ctrl, permit, **kwargs)
            finalizations.append(finished)
            self.assertFalse(finished)
            self.assertFalse(ctrl._ready)
            self.assertTrue(ctrl._faulted)
            self.assertEqual(ctrl.generation, generation)
            self.assertEqual(ctrl._store.read(), inflight)
            return finished

        with mock.patch.object(type(controller), "finish_operation",
                               new=finish_with_reentrant_observation):
            result = self.confirm(review)
        self.assertTrue(observed)
        self.assertEqual(finalizations, [False])
        self.assert_attempts(delete=1)
        self.assert_uncertain(result)
        self.assert_inflight()

    def refuse_finalization_callback(self, callback):
        ctrl = self.h.controller
        permit = ctrl.begin_operation(
            kind=Op.TEST_CANDIDATE.value, evidence_hash="0" * 64,
            epoch=ctrl.epoch, generation=ctrl.generation)
        inflight = ctrl._store.read()
        generation = ctrl.generation
        observed = []
        original = type(ctrl)._observe

        def observe(controller):
            observed.append(True)
            return original(controller)

        with mock.patch.object(type(ctrl), "_observe", new=observe):
            self.assertFalse(ctrl.finish_operation(
                permit, verified=True, approval_live=callback))
        self.assertEqual(observed, [True])
        self.assertEqual(ctrl.generation, generation)
        self.assertEqual(ctrl._store.read(), inflight)
        self.assertFalse(ctrl._ready)
        self.assertTrue(ctrl._faulted)
        self.assert_attempts()

    def test_finish_callback_false_preserves_inflight(self):
        self.refuse_finalization_callback(lambda: False)

    def test_finish_callback_nontrue_preserves_inflight(self):
        self.refuse_finalization_callback(lambda: 1)

    def test_finish_callback_exception_preserves_inflight(self):
        def fail():
            raise RuntimeError("synthetic finalization failure")
        self.refuse_finalization_callback(fail)

    def test_legacy_direct_finish_receives_no_callback(self):
        receipt = self.h.coordinator.request(Op.TEST_CANDIDATE)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        original = type(self.h.controller).finish_operation
        finalized = []

        def legacy_finish(controller, permit, *, verified):
            finalized.append(verified)
            return original(controller, permit, verified=verified)

        with mock.patch.object(type(self.h.controller), "finish_operation",
                               new=legacy_finish):
            result = self.h.coordinator.approve(candidate=SecretValue("fixture-good"))
        self.assertEqual(finalized, [True])
        self.assertIs(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assertIs(self.h.controller._store.read()[-1].state, RecoveryState.READY)
        self.assert_attempts(validate=1)

    def test_connect_close_after_validation_before_put_attempt(self):
        self.close_at_lifecycle_gate(Op.CONNECT, "_put", validations=1)

    def test_replace_close_after_validation_before_put_attempt(self):
        self.close_at_lifecycle_gate(Op.REPLACE, "_put", validations=1)

    def test_close_after_delete_started_retains_inflight(self):
        review = self.prepare(Op.REMOVE)
        original = self.h.backend.delete

        def delete_then_close(*args):
            result = original(*args)  # one effect has already started
            self.owner.close(self.ctx)
            return result

        with mock.patch.object(self.h.backend, "delete", new=delete_then_close):
            result = self.confirm(review)
        self.assert_attempts(delete=1)
        self.assert_uncertain(result)
        self.assert_inflight()

    def direct_approve(self, review, **overrides):
        kwargs = dict(ticket=review._ticket, owner_token=self.owner._owner_token,
                      root=self.root, operation=review.operation,
                      candidate=SecretValue("fixture-good"))
        kwargs.update(overrides)
        return self.h.coordinator.approve_ui(**kwargs)

    def refuse_callback(self, callback):
        review = self.prepare(Op.TEST_CANDIDATE)
        result = self.direct_approve(review, journey_live=callback)
        self.assertIs(result.outcome, CoordinatedOutcome.REFUSED)
        self.assert_attempts()
        self.assertIs(self.h.controller._store.read()[-1].state, RecoveryState.READY)

    def test_optional_callback_false_refuses_before_admission(self):
        self.refuse_callback(lambda: False)

    def test_optional_callback_integer_is_not_true(self):
        self.refuse_callback(lambda: 1)

    def test_optional_callback_does_not_consult_truthiness(self):
        class HostileTruth:
            def __bool__(self):
                raise AssertionError("truthiness must not be consulted")
        self.refuse_callback(lambda: HostileTruth())

    def test_optional_callback_failure_refuses_before_admission(self):
        def fail():
            raise RuntimeError("synthetic callback failure")
        self.refuse_callback(fail)

    def test_noncallable_optional_gate_refuses(self):
        self.refuse_callback(object())

    def test_legacy_absent_callback_preserves_approved_behavior(self):
        review = self.prepare(Op.TEST_CANDIDATE)
        original = CooperativeOnboardingCoordinator._approve_pending
        delegated = []

        def legacy_delegate(coordinator, *, candidate=None):
            # Frozen older adversarial tests use this original hook signature.
            delegated.append(True)
            return original(coordinator, candidate=candidate)

        with mock.patch.object(CooperativeOnboardingCoordinator, "_approve_pending",
                               new=legacy_delegate):
            result = self.direct_approve(review)
        self.assertEqual(delegated, [True])
        self.assertIs(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assert_attempts(validate=1)

    def test_wrong_ticket_root_token_operation_never_calls_callback(self):
        review = self.prepare(Op.TEST_CANDIDATE)
        callback = mock.Mock(return_value=True)
        for override in (dict(ticket=object()), dict(root=FakeRoot()),
                         dict(owner_token="foreign"), dict(operation=Op.CONNECT)):
            with self.subTest(override=tuple(override)):
                result = self.direct_approve(review, journey_live=callback, **override)
                self.assertIs(result.outcome, CoordinatedOutcome.REFUSED)
        callback.assert_not_called()
        self.assert_attempts()
        self.assertIs(self.confirm(review).outcome, CoordinatedOutcome.COMPLETED)
        self.assert_attempts(validate=1)

    def test_stale_review_does_not_consume_successor(self):
        old = self.prepare(Op.TEST_CANDIDATE)
        self.owner.cancel(self.ctx, old)
        _, current = self.owner.request(self.ctx, Op.TEST_CANDIDATE)
        callback = mock.Mock(return_value=True)
        self.assertIs(self.direct_approve(old, journey_live=callback).outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertIs(self.confirm(old).outcome, CoordinatedOutcome.REFUSED)
        callback.assert_not_called()
        self.assert_attempts()
        self.assertIs(self.confirm(current).outcome, CoordinatedOutcome.COMPLETED)
        self.assert_attempts(validate=1)

    def intercept_approval(self, before):
        original = CooperativeOnboardingCoordinator.approve_ui

        def intercept(coordinator, **kwargs):
            before(kwargs["journey_live"])
            return original(coordinator, **kwargs)

        return mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui",
                                 new=intercept)

    def test_owner_callback_rechecks_after_reentrant_close(self):
        review = self.prepare()

        def install(callback):
            def close_but_report_live():
                self.owner.close(self.ctx)
                return True
            self.probe = close_but_report_live

        with self.intercept_approval(install):
            result = self.confirm(review)
        self.assert_attempts()
        self.assert_uncertain(result)

    def test_recursive_owner_callback_is_sticky_revocation(self):
        review = self.prepare()
        nested = []

        def install(callback):
            def reenter():
                nested.append(callback())
                return True
            self.probe = reenter

        with self.intercept_approval(install):
            result = self.confirm(review)
        self.assertTrue(nested)
        self.assertTrue(all(result is False for result in nested))
        self.assert_attempts()
        self.assertIsNot(result.outcome, CoordinatedOutcome.COMPLETED)

    def test_wrong_thread_callback_refuses_before_ui_probe(self):
        review = self.prepare()
        observed = []

        def foreign_call(callback):
            self.probe = mock.Mock(return_value=True)
            worker = threading.Thread(target=lambda: observed.append(callback()))
            worker.start()
            worker.join(5)
            self.assertFalse(worker.is_alive())
            self.probe.assert_not_called()

        with self.intercept_approval(foreign_call):
            result = self.confirm(review)
        self.assertEqual(observed, [False])
        self.assert_attempts()
        self.assertIsNot(result.outcome, CoordinatedOutcome.COMPLETED)

    def test_wrong_thread_confirm_never_enters_coordinator(self):
        review = self.prepare()
        observed = []

        def foreign_confirm():
            try:
                self.confirm(review)
            except JourneyRefused as exc:
                observed.append(str(exc))

        with mock.patch.object(CooperativeOnboardingCoordinator, "approve_ui") as approve:
            worker = threading.Thread(target=foreign_confirm)
            worker.start()
            worker.join(5)
            self.assertFalse(worker.is_alive())
        self.assertEqual(observed, ["WRONG_THREAD"])
        approve.assert_not_called()
        self.assert_attempts()

    def test_equal_context_replacement_revokes_exact_journey(self):
        review = self.prepare()

        def replace_context(callback):
            self.owner._ctx = JourneyContext(
                self.root, self.ctx.application, self.ctx.pane,
                self.ctx.journey, self.ctx.generation)
            self.assertFalse(callback())

        with self.intercept_approval(replace_context):
            result = self.confirm(review)
        self.assert_attempts()
        self.assert_uncertain(result)

    def test_reentrant_confirm_cannot_consume_approval_twice(self):
        review = self.prepare(Op.TEST_CANDIDATE)
        nested = []

        def install(callback):
            def reenter():
                nested.append(self.confirm(review).outcome)
                return True
            self.probe = reenter

        with self.intercept_approval(install):
            result = self.confirm(review)
        self.assertTrue(nested)
        self.assertTrue(all(outcome is CoordinatedOutcome.REFUSED for outcome in nested))
        self.assertIs(result.outcome, CoordinatedOutcome.COMPLETED)
        self.assert_attempts(validate=1)

    def refuse_owner_probe(self, probe):
        review = self.prepare()

        def install(callback):
            self.probe = probe

        with self.intercept_approval(install):
            result = self.confirm(review)
        self.assert_attempts()
        self.assertIsNot(result.outcome, CoordinatedOutcome.COMPLETED)

    def test_owner_probe_nontrue_cannot_authorize_effect(self):
        self.refuse_owner_probe(lambda: 1)

    def test_owner_probe_failure_cannot_authorize_effect(self):
        def fail():
            raise RuntimeError("synthetic UI probe failure")
        self.refuse_owner_probe(fail)

    def test_changed_owner_token_revokes_callback(self):
        review = self.prepare()
        original_token = self.owner._owner_token

        def replace_token(callback):
            self.owner._owner_token = "foreign"
            self.assertFalse(callback())

        try:
            with self.intercept_approval(replace_token):
                result = self.confirm(review)
        finally:
            self.owner._owner_token = original_token
        self.assert_attempts()
        self.assert_uncertain(result)

    def test_old_downstream_gate_cannot_authorize_successor(self):
        review = self.prepare(Op.TEST_CANDIDATE)
        captured = []
        original = type(self.h.host).approve_if_current

        def capture(host, *args, **kwargs):
            captured.append(kwargs["approval_live"])
            return original(host, *args, **kwargs)

        with mock.patch.object(type(self.h.host), "approve_if_current", new=capture):
            self.assertIs(self.confirm(review).outcome, CoordinatedOutcome.COMPLETED)
        self.assertEqual(len(captured), 1)
        receipt, successor = self.owner.request(self.ctx, Op.TEST_CANDIDATE)
        self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
        self.assertFalse(captured[0]())
        self.assertIs(self.confirm(successor).outcome, CoordinatedOutcome.COMPLETED)
        self.assert_attempts(validate=2)

    def test_close_during_last_ui_root_probe_before_journal_refuses_admission(self):
        review = self.prepare(Op.TEST_CANDIDATE)
        original_root = coordination._trusted_ui_root_live
        original_recovered = CooperativeOnboardingCoordinator._approve_recovered
        probes = []

        def in_recovered(coordinator, *args, **kwargs):
            def last_root_probe(root):
                probes.append(True)
                if len(probes) == 2:
                    self.assertFalse(self.owner.close(self.ctx))
                return original_root(root)

            with mock.patch.object(coordination, "_trusted_ui_root_live",
                                   new=last_root_probe):
                return original_recovered(coordinator, *args, **kwargs)

        with mock.patch.object(CooperativeOnboardingCoordinator,
                               "_approve_recovered", new=in_recovered):
            result = self.confirm(review)
        self.assertGreaterEqual(len(probes), 2)
        self.assert_attempts()
        self.assertIs(self.h.controller._store.read()[-1].state,
                      RecoveryState.READY)
        self.assert_uncertain(result)

    def test_close_during_last_ui_root_probe_before_ready_refuses_finalization(self):
        review = self.prepare(Op.TEST_CANDIDATE)
        original_root = coordination._trusted_ui_root_live
        original_finish = type(self.h.controller).finish_operation
        probes = []

        def in_finish(controller, permit, **kwargs):
            def last_root_probe(root):
                probes.append(True)
                if len(probes) == 2:
                    self.assertFalse(self.owner.close(self.ctx))
                return original_root(root)

            with mock.patch.object(coordination, "_trusted_ui_root_live",
                                   new=last_root_probe):
                return original_finish(controller, permit, **kwargs)

        with mock.patch.object(type(self.h.controller), "finish_operation",
                               new=in_finish):
            result = self.confirm(review)
        self.assertGreaterEqual(len(probes), 2)
        self.assert_attempts(validate=1)
        self.assert_uncertain(result)
        self.assert_inflight()


if __name__ == "__main__":
    unittest.main()
