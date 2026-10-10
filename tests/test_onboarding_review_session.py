"""Phase 8.17 pending review is in-memory, one-time and non-authorizing."""
from dataclasses import FrozenInstanceError
from unittest.mock import Mock
import unittest

from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus
from nayeon.brain.onboarding_operation_advice import advise_onboarding_operation, OnboardingOperation
from nayeon.brain import onboarding_review_session as m


def advice(state=ConnectionObservationStatus.SETUP_REQUIRED, op=OnboardingOperation.CONNECT):
    return advise_onboarding_operation(ConnectionObservation(state), op)


class ReviewSessionTests(unittest.TestCase):
    def test_pending_cannot_execute_or_be_replaced(self):
        clock=Mock(return_value=10.0)
        host=m.OnboardingReviewSession(clock=clock)
        host.begin(advice())
        self.assertTrue(host.has_pending)
        self.assertIs(host.pending_advice.operation, OnboardingOperation.CONNECT)
        with self.assertRaises(RuntimeError): host.begin(advice())
        self.assertFalse(hasattr(host, "connect"))
        self.assertFalse(hasattr(host, "execute"))
        self.assertFalse(hasattr(host, "credential"))
        receipt=host.finish(human_approved=True)
        self.assertIs(receipt.decision,m.ReviewDecision.APPROVED)
        self.assertTrue(receipt.requires_reobservation)
        self.assertFalse(receipt.grants_execution_authority)
        self.assertFalse(host.has_pending)
        with self.assertRaises(RuntimeError): host.finish(human_approved=True)
        with self.assertRaises(FrozenInstanceError): receipt.decision=m.ReviewDecision.REJECTED

    def test_cancel_consumes_review(self):
        host=m.OnboardingReviewSession(clock=lambda:10.0)
        host.begin(advice())
        result=host.cancel()
        self.assertIs(result.decision,m.ReviewDecision.REJECTED)
        self.assertFalse(host.has_pending)

    def test_expired_approval_is_never_approved(self):
        clock=Mock(side_effect=[10.0,131.0])
        host=m.OnboardingReviewSession(clock=clock,timeout_seconds=120.0)
        host.begin(advice())
        self.assertIs(host.finish(human_approved=True).decision,m.ReviewDecision.EXPIRED)
        self.assertFalse(host.has_pending)

    def test_stale_or_unknown_cannot_begin(self):
        host=m.OnboardingReviewSession(clock=lambda:10.0)
        for state in (ConnectionObservationStatus.UNKNOWN,
                      ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION,
                      ConnectionObservationStatus.CHANGED_DURING_OBSERVATION):
            with self.assertRaises(ValueError):host.begin(advice(state))
        with self.assertRaises(ValueError):host.begin(advice(op=OnboardingOperation.REVIEW))
        self.assertFalse(host.has_pending)

    def test_exact_inputs_and_clock_fail_closed(self):
        for timeout in (0,-1,301,True,float('nan'),float('inf')):
            with self.assertRaises((TypeError,ValueError)):
                m.OnboardingReviewSession(timeout_seconds=timeout)
        for wrong in (None, True, {}, "connect"):
            with self.assertRaises(TypeError):m.OnboardingReviewSession(clock=lambda:10.0).begin(wrong)
        host=m.OnboardingReviewSession(clock=lambda:10.0)
        host.begin(advice())
        with self.assertRaises(TypeError):host.finish(human_approved="yes")
        self.assertTrue(host.has_pending)
        host.cancel()
        bad=m.OnboardingReviewSession(clock=lambda:float('nan'))
        with self.assertRaises(RuntimeError):bad.begin(advice())
        clock=Mock(side_effect=[10.0,RuntimeError('secret')])
        host=m.OnboardingReviewSession(clock=clock)
        host.begin(advice())
        self.assertIs(host.finish(human_approved=True).decision,m.ReviewDecision.EXPIRED)

    def test_direct_receipt_never_claims_execution_authority(self):
        data=dict(operation=OnboardingOperation.CONNECT,
                  observed=ConnectionObservationStatus.SETUP_REQUIRED,
                  decision=m.ReviewDecision.APPROVED)
        for patch in ({'grants_execution_authority':True},
                      {'requires_reobservation':False},
                      {'decision':'approved'}, {'operation':'connect'},
                      {'operation':OnboardingOperation.REVIEW}):
            with self.subTest(patch=patch), self.assertRaises((TypeError, ValueError)):
                m.CompletedOnboardingReview(**(data|patch))


if __name__=='__main__':unittest.main()
