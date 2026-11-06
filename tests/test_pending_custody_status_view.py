"""P84 read-only production presentation seam: NO real credential effects."""
import ast
import inspect
import unittest
from dataclasses import FrozenInstanceError

from nayeon.brain import pending_custody_status_view as m
from nayeon.brain.onboarding_status_view import (
    OnboardingDisplayState, present_onboarding_status,
)
from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.brain.pending_credential_policy import (
    PendingCredentialAction, PendingCredentialState,
    PendingCredentialDecision, PendingCredentialAssessment,
    assess_pending_credential_action,
)


def legacy(status):
    observation = ConnectionObservation(status)
    return present_onboarding_status(observation,
                                    advise_connection_recovery(observation))


class PendingCustodyProjectionTests(unittest.TestCase):
    def test_all_63_legacy_pending_action_combinations_are_nonauthoritative(self):
        observed_count = 0
        for old in ConnectionObservationStatus:
            old_view = legacy(old)
            for state in PendingCredentialState:
                for action in PendingCredentialAction:
                    observed_count += 1
                    with self.subTest(old=old, state=state, action=action):
                        advice = assess_pending_credential_action(state, action)
                        projected = m.present_pending_custody_advice(old_view, advice)
                        self.assertIs(projected.legacy_status, old_view.state)
                        self.assertIs(projected.proposed_action, action)
                        self.assertIs(projected.advisory_decision, advice.decision)
                        self.assertIs(projected.must_reobserve, True)
                        for forbidden in ("authorizes_effect", "confirms_persistence",
                                          "confirms_validation", "confirms_provider_connection",
                                          "clears_recovery"):
                            self.assertIs(getattr(projected, forbidden), False)
                        if state is PendingCredentialState.RECOVERY_REQUIRED:
                            self.assertIs(projected.pending_display,
                                          m.PendingCustodyDisplay.RECOVERY_HOLD)
                            self.assertIs(advice.decision,
                                          PendingCredentialDecision.RECOVERY_BLOCKED)
                        elif state is PendingCredentialState.STORED_UNVERIFIED:
                            self.assertIs(projected.pending_display,
                                          m.PendingCustodyDisplay.UNVERIFIED_PENDING_CLAIM)
                        else:
                            self.assertIs(projected.pending_display,
                                          m.PendingCustodyDisplay.NO_PENDING_EVIDENCE_ASSERTED)
        self.assertEqual(observed_count, 63)

    def test_stored_legacy_status_does_not_promote_pending_evidence(self):
        from nayeon.brain.connection_reconciliation import ConnectionObservationStatus as L
        view = legacy(L.UNCONFIGURED_CREDENTIAL_PRESENT)
        assessment = assess_pending_credential_action(
            PendingCredentialState.ABSENT, PendingCredentialAction.SAVE_PENDING)
        display = m.present_pending_custody_advice(view, assessment)
        self.assertIs(display.legacy_status, OnboardingDisplayState.SAVED_KEY_NEEDS_REVIEW)
        self.assertIs(display.pending_display,
                      m.PendingCustodyDisplay.NO_PENDING_EVIDENCE_ASSERTED)
        self.assertIs(display.confirms_provider_connection, False)

    def test_exact_types_refuse_forged_status_and_assessments(self):
        view = legacy(ConnectionObservationStatus.UNKNOWN)
        advice = assess_pending_credential_action(
            PendingCredentialState.RECOVERY_REQUIRED, PendingCredentialAction.DELETE_PENDING)
        for fake in (None, "unknown", view.state, object()):
            with self.subTest(legacy=type(fake).__name__), self.assertRaises(TypeError):
                m.present_pending_custody_advice(fake, advice)
        for fake in (None, "recovery_required", advice.decision, object()):
            with self.subTest(advice=type(fake).__name__), self.assertRaises(TypeError):
                m.present_pending_custody_advice(view, fake)

    def test_forged_inconsistent_advisory_cannot_be_displayed_as_approved(self):
        status = legacy(ConnectionObservationStatus.UNKNOWN)
        cases = (
            (PendingCredentialState.ABSENT, PendingCredentialAction.DELETE_PENDING,
             PendingCredentialDecision.NEEDS_REVIEW),
            (PendingCredentialState.RECOVERY_REQUIRED, PendingCredentialAction.SAVE_PENDING,
             PendingCredentialDecision.NEEDS_REVIEW),
            (PendingCredentialState.STORED_UNVERIFIED,
             PendingCredentialAction.DELETE_PENDING,
             PendingCredentialDecision.NEEDS_REVIEW),
        )
        for state, action, forged in cases:
            with self.subTest(state=state, action=action):
                invalid = PendingCredentialAssessment(state, action, forged)
                with self.assertRaisesRegex(ValueError, "canonical matrix"):
                    m.present_pending_custody_advice(status, invalid)

    def test_result_is_frozen_cannot_be_forced_to_authorized(self):
        view = legacy(ConnectionObservationStatus.UNKNOWN)
        advice = assess_pending_credential_action(
            PendingCredentialState.STORED_UNVERIFIED, PendingCredentialAction.REPLACE_PENDING)
        display = m.present_pending_custody_advice(view, advice)
        for prop in ("authorizes_effect", "confirms_persistence", "confirms_validation",
                     "confirms_provider_connection", "clears_recovery"):
            with self.subTest(prop=prop), self.assertRaises((FrozenInstanceError, AttributeError)):
                setattr(display, prop, True)
        with self.assertRaises(ValueError):
            m.PendingCustodyStatusView(view.state, m.PendingCustodyDisplay.RECOVERY_HOLD,
                                      advice.action, advice.decision, authorizes_effect=True)
        with self.assertRaisesRegex(ValueError, "contradicts canonical policy"):
            m.PendingCustodyStatusView(
                view.state, m.PendingCustodyDisplay.RECOVERY_HOLD,
                PendingCredentialAction.SAVE_PENDING,
                PendingCredentialDecision.NEEDS_REVIEW)
        self.assertFalse(hasattr(display, "__dict__"))
        self.assertNotIn("api_key", repr(display))
        self.assertNotIn("pending_save", repr(display))

    def test_module_has_pure_allowlisted_imports_and_no_effectful_entrypoints(self):
        tree = ast.parse(inspect.getsource(m))
        modules = {node.module for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom)}
        self.assertEqual(modules, {
            "dataclasses", "enum", "nayeon.brain.onboarding_status_view",
            "nayeon.brain.pending_credential_policy",
        })
        self.assertFalse(any(isinstance(node, ast.Import) for node in ast.walk(tree)))
        calls = {n.func.id if isinstance(n.func, ast.Name) else n.func.attr
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        self.assertFalse(calls & {
            "connect", "save", "replace", "delete", "remove", "open",
            "validate", "get", "put", "execute", "WinDLL", "subprocess",
            "WindowsCredentialBackend", "compose_provider_ai_service", "eval", "exec",
        })


if __name__ == "__main__":
    unittest.main()
