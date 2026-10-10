"""Phase 8.20: complete, non-authorizing first-run summary tests."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest
from unittest.mock import patch

from nayeon.brain import first_run_summary as m
from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation


class FirstRunSummaryTests(unittest.TestCase):
    def test_every_state_is_bounded_and_never_authorizes_execution(self):
        for state in ConnectionObservationStatus:
            with self.subTest(state=state):
                result = m.summarize_first_run(ConnectionObservation(state))
                self.assertIs(type(result), m.FirstRunSummary)
                self.assertFalse(result.grants_execution_authority)
                self.assertTrue(result.requires_reobservation)
                self.assertNotIn(OnboardingOperation.REVIEW, result.suggested_operations)
                self.assertEqual(len(result.suggested_operations),
                                 len(set(result.suggested_operations)))
                self.assertNotIn("api_key", repr(result))

    def test_uncertain_or_unsupported_never_suggests_credential_actions(self):
        for state in (ConnectionObservationStatus.UNKNOWN,
                      ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION,
                      ConnectionObservationStatus.CHANGED_DURING_OBSERVATION):
            self.assertEqual(m.summarize_first_run(
                ConnectionObservation(state)).suggested_operations, ())

    def test_expected_first_run_safe_choices(self):
        from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
        self.assertEqual(m.summarize_first_run(ConnectionObservation(
            ConnectionObservationStatus.SETUP_REQUIRED)).suggested_operations,
            (Op.TEST_CANDIDATE, Op.CONNECT))
        self.assertEqual(m.summarize_first_run(ConnectionObservation(
            ConnectionObservationStatus.VALIDATION_REQUIRED)).suggested_operations,
            (Op.TEST_CANDIDATE, Op.TEST_STORED, Op.REPLACE, Op.REMOVE))

    def test_rejects_spoofed_inputs(self):
        for invalid in ("setup_required", None, object(),
                        ConnectionObservationStatus.SETUP_REQUIRED):
            with self.subTest(invalid=type(invalid)), self.assertRaises(TypeError):
                m.summarize_first_run(invalid)

    def test_immutable_and_no_secret_backend_imports(self):
        result=m.summarize_first_run(ConnectionObservation(
            ConnectionObservationStatus.SETUP_REQUIRED))
        with self.assertRaises(FrozenInstanceError):
            result.grants_execution_authority = True
        with self.assertRaises(ValueError):
            m.FirstRunSummary(result.state, result.recovery_step,
                              result.suggested_operations, grants_execution_authority=True)
        tree=ast.parse(inspect.getsource(m))
        imports={n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses",
            "nayeon.brain.connection_reconciliation",
            "nayeon.brain.connection_recovery_advice",
            "nayeon.brain.onboarding_operation_advice",
            "nayeon.brain.onboarding_status_view"})
        self.assertFalse(hasattr(result, "__dict__"))
        for blocked in ("nayeon.secrets", "providers", "connection_persistence"):
            self.assertFalse(any(blocked in n for n in imports))
