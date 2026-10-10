"""Phase 8.16 pure operation eligibility; every observation and intent."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

from nayeon.brain import onboarding_operation_advice as m
from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)


class OperationAdviceTests(unittest.TestCase):
    def test_all_observation_operation_pairs_are_exhaustive(self):
        for operation in m.OnboardingOperation:
            for status in ConnectionObservationStatus:
                with self.subTest(operation=operation, status=status):
                    item=m.advise_onboarding_operation(ConnectionObservation(status), operation)
                    expected=(m.OperationEligibility.SUGGESTED if status in m._ALLOWED[operation]
                              else m.OperationEligibility.BLOCKED)
                    self.assertIs(item.eligibility, expected)
                    self.assertIs(item.requires_fresh_state, True)
                    self.assertIs(item.requires_real_human_intent, True)
                    self.assertFalse(hasattr(item,'__dict__'))

    def test_unknown_changed_unsupported_are_not_mutation_candidates(self):
        for status in (ConnectionObservationStatus.UNKNOWN,
                       ConnectionObservationStatus.CHANGED_DURING_OBSERVATION,
                       ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION):
            for op in (m.OnboardingOperation.CONNECT,m.OnboardingOperation.REPLACE,
                       m.OnboardingOperation.REMOVE,m.OnboardingOperation.TEST_CANDIDATE,
                       m.OnboardingOperation.TEST_STORED):
                self.assertIs(m.advise_onboarding_operation(
                    ConnectionObservation(status), op).eligibility, m.OperationEligibility.BLOCKED)

    def test_never_claims_authority_when_directly_constructed(self):
        item=m.advise_onboarding_operation(
            ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED),
            m.OnboardingOperation.CONNECT)
        with self.assertRaises(FrozenInstanceError):
            item.requires_real_human_intent=False
        data=dict(operation=item.operation, observed=item.observed, eligibility=item.eligibility)
        for patch in ({"requires_real_human_intent": False},
                      {"requires_fresh_state": False},
                      {"eligibility": m.OperationEligibility.BLOCKED},
                      {"observed": ConnectionObservationStatus.UNKNOWN},
                      {"operation": "connect"}):
            with self.subTest(patch=patch),self.assertRaises((TypeError, ValueError)):
                m.OnboardingOperationAdvice(**(data | patch))

    def test_exact_inputs_and_no_effect_imports(self):
        status=ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED)
        for wrong in (None,{},True,"setup_required",object()):
            with self.assertRaises(TypeError):
                m.advise_onboarding_operation(wrong,m.OnboardingOperation.CONNECT)
            with self.assertRaises(TypeError):
                m.advise_onboarding_operation(status,wrong)
        imports={n.module for n in ast.walk(ast.parse(inspect.getsource(m)))
                 if isinstance(n,ast.ImportFrom)}
        self.assertEqual(imports,{"dataclasses","enum",
                                  "nayeon.brain.connection_reconciliation"})
        calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr
               for n in ast.walk(ast.parse(inspect.getsource(m)))
               if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))}
        for banned in ("get","put","delete","is_available","connect",
                       "test_stored","test_candidate","replace","save","open"):
            self.assertNotIn(banned,calls)


if __name__=="__main__":
    unittest.main()
