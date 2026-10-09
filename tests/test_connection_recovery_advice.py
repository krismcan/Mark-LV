"""Phase 8.9 pure non-executable recovery advice."""

import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

from nayeon.brain import connection_recovery_advice as m
from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)


class ConnectionRecoveryAdviceTests(unittest.TestCase):
    def test_every_status_has_one_exact_recovery_suggestion(self):
        expected = {
            "SETUP_REQUIRED": "CONFIGURE_PROVIDER",
            "UNCONFIGURED_CREDENTIAL_PRESENT": "REVIEW_SAVED_CREDENTIAL",
            "CREDENTIAL_REQUIRED": "ADD_CREDENTIAL",
            "VALIDATION_REQUIRED": "REQUEST_EXPLICIT_VALIDATION",
            "UNSUPPORTED_CONFIGURATION": "REVIEW_UNSUPPORTED_CONFIG",
            "CHANGED_DURING_OBSERVATION": "REOBSERVE",
            "UNKNOWN": "REVIEW_UNKNOWN_STATE",
        }
        self.assertEqual(set(expected), {s.name for s in ConnectionObservationStatus})
        for name, step in expected.items():
            with self.subTest(status=name):
                obs = ConnectionObservation(ConnectionObservationStatus[name])
                advice = m.advise_connection_recovery(obs)
                self.assertIs(type(advice), m.ConnectionRecoveryAdvice)
                self.assertIs(advice.step, m.ConnectionRecoveryStep[step])

    def test_unknown_does_not_trigger_retry_automatically(self):
        advice = m.advise_connection_recovery(
            ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
        )
        self.assertEqual(advice.step.value, "review_unknown_state")
        self.assertFalse(hasattr(advice, "execute"))
        self.assertFalse(hasattr(advice, "perform"))

    def test_observations_and_advice_are_immutable_exact_types(self):
        result = m.ConnectionRecoveryAdvice(m.ConnectionRecoveryStep.REOBSERVE)
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertEqual(tuple(result.__dataclass_fields__), ("step",))
        with self.assertRaises(FrozenInstanceError):
            result.step = m.ConnectionRecoveryStep.ADD_CREDENTIAL
        for bad in (None, "reobserve", 1):
            with self.assertRaises(TypeError):
                m.ConnectionRecoveryAdvice(bad)
        for bad in (None, {}, "unknown", object()):
            with self.assertRaises(TypeError):
                m.advise_connection_recovery(bad)
        derived = type("DerivedObservation", (ConnectionObservation,), {})
        with self.assertRaises(TypeError):
            m.advise_connection_recovery(
                derived(ConnectionObservationStatus.UNKNOWN)
            )

    def test_source_pure_no_imported_credential_or_filesystem_capabilities(self):
        tree = ast.parse(inspect.getsource(m))
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imported, {"dataclasses", "enum",
                                   "nayeon.brain.connection_reconciliation"})
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        for forbidden in ("get", "put", "delete", "save", "clear", "connect",
                          "replace", "is_available", "open", "read_text", "read_bytes",
                          "bootstrap_provider_connection", "validate",
                          "OpenAIProvider", "WindowsCredentialBackend",
                          "getenv", "sleep", "create_task"):
            self.assertNotIn(forbidden, calls)

    def test_no_hidden_auto_recovery_or_sensitive_data_in_advice(self):
        for status in ConnectionObservationStatus:
            advice = m.advise_connection_recovery(ConnectionObservation(status))
            self.assertIs(type(advice.step.value), str)
            self.assertNotIn("openai.api_key", repr(advice))
            self.assertNotIn("SECRET", repr(advice))
            self.assertFalse(any(hasattr(advice, name) for name in
                                 ("path", "model", "provider", "credential",
                                  "backend", "owner", "secret")))


if __name__ == "__main__":
    unittest.main()
