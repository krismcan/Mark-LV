"""Phase 8.10 pure first-run presentation tests; no secret or UI access."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

from nayeon.brain import onboarding_status_view as m
from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)
from nayeon.brain.connection_recovery_advice import (
    ConnectionRecoveryAdvice, ConnectionRecoveryStep, advise_connection_recovery,
)


class OnboardingStatusViewTests(unittest.TestCase):
    def test_every_observation_maps_to_one_nonsecret_view(self):
        self.assertEqual(len(ConnectionObservationStatus), 7)
        for status in ConnectionObservationStatus:
            with self.subTest(status=status):
                observation = ConnectionObservation(status)
                advice = advise_connection_recovery(observation)
                view = m.present_onboarding_status(observation, advice)
                self.assertIs(type(view), m.OnboardingStatusView)
                self.assertIs(type(view.state), m.OnboardingDisplayState)
                self.assertIs(view.step, advice.step)
                self.assertIs(view.must_reobserve, True)
                self.assertNotIn("connected", view.state.value)
                self.assertNotIn("key", repr(view))
                self.assertNotIn("api", repr(view))

    def test_mismatched_advice_cannot_infer_authority(self):
        obs = ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
        forged = ConnectionRecoveryAdvice(ConnectionRecoveryStep.ADD_CREDENTIAL)
        with self.assertRaisesRegex(ValueError, "does not match"):
            m.present_onboarding_status(obs, forged)

    def test_exact_input_type_boundary(self):
        obs = ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED)
        advice = advise_connection_recovery(obs)
        for bad in (None, obs.status, "setup_required", object()):
            with self.subTest(bad=type(bad)), self.assertRaises(TypeError):
                m.present_onboarding_status(bad, advice)
        for bad in (None, advice.step, "configure", object()):
            with self.subTest(bad=type(bad)), self.assertRaises(TypeError):
                m.present_onboarding_status(obs, bad)

    def test_view_is_immutable_and_cannot_claim_freshness(self):
        view = m.present_onboarding_status(
            ConnectionObservation(ConnectionObservationStatus.UNKNOWN),
            ConnectionRecoveryAdvice(ConnectionRecoveryStep.REVIEW_UNKNOWN_STATE),
        )
        with self.assertRaises(FrozenInstanceError):
            view.must_reobserve = False
        with self.assertRaises(ValueError):
            m.OnboardingStatusView(view.state, view.step, False)
        with self.assertRaises(TypeError):
            m.OnboardingStatusView("state", view.step)
        with self.assertRaises(TypeError):
            m.OnboardingStatusView(view.state, "step")
        self.assertFalse(hasattr(view, "__dict__"))

    def test_pure_import_and_call_authority(self):
        tree = ast.parse(inspect.getsource(m))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {
            "dataclasses", "enum",
            "nayeon.brain.connection_reconciliation",
            "nayeon.brain.connection_recovery_advice",
        })
        calls = {n.func.id if isinstance(n.func, ast.Name) else n.func.attr
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        for forbidden in ("is_available", "get", "put", "delete", "replace", "save",
                          "validate", "connect", "open", "bootstrap_provider_connection",
                          "WindowsCredentialBackend", "OpenAIProvider"):
            self.assertNotIn(forbidden, calls)


if __name__ == "__main__":
    unittest.main()
