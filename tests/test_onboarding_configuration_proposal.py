"""Phase 8.11 strict pure OpenAI model proposal tests."""
import ast
import inspect
import unittest
from dataclasses import FrozenInstanceError

from nayeon.brain import onboarding_configuration_proposal as m
from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.brain.onboarding_status_view import present_onboarding_status, OnboardingDisplayState


def view(status: ConnectionObservationStatus):
    obs=ConnectionObservation(status)
    return present_onboarding_status(obs, advise_connection_recovery(obs))


class OnboardingConfigurationProposalTests(unittest.TestCase):
    def test_eligible_states_and_canonical_provider(self):
        for state in (
            ConnectionObservationStatus.SETUP_REQUIRED,
            ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT,
            ConnectionObservationStatus.CREDENTIAL_REQUIRED,
            ConnectionObservationStatus.VALIDATION_REQUIRED,
        ):
            with self.subTest(state=state):
                result=m.propose_openai_configuration(view(state),"gpt-5.6")
                self.assertEqual(result.provider,"openai")
                self.assertEqual(result.model,"gpt-5.6")
                self.assertTrue(result.requires_new_observation)
                self.assertIs(type(result),m.OpenAIConfigurationProposal)
                self.assertFalse(hasattr(result,"__dict__"))

    def test_unknown_changed_and_unsupported_refused(self):
        for state in (
            ConnectionObservationStatus.UNKNOWN,
            ConnectionObservationStatus.CHANGED_DURING_OBSERVATION,
            ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION,
        ):
            with self.subTest(state=state),self.assertRaises(ValueError):
                m.propose_openai_configuration(view(state),"gpt-5.6")

    def test_model_name_strict_before_any_effect(self):
        v=view(ConnectionObservationStatus.SETUP_REQUIRED)
        for name in ("", " ", " gpt-5.6", "gpt-5.6 ", "\nmodel", "a"*129, None, 17, False, object()):
            with self.subTest(name=type(name)),self.assertRaises(ValueError):
                m.propose_openai_configuration(v,name)
        self.assertEqual(m.propose_openai_configuration(v,"gpt-5.6-mini").model,"gpt-5.6-mini")

    def test_exact_source_view_required(self):
        for invalid in ("needs_setup",None,object(),{}):
            with self.assertRaises(TypeError):
                m.propose_openai_configuration(invalid,"gpt-5.6")

    def test_cannot_replace_provider_or_clear_reobserve(self):
        p=m.propose_openai_configuration(view(ConnectionObservationStatus.NEEDS_SETUP if hasattr(ConnectionObservationStatus,'NEEDS_SETUP') else ConnectionObservationStatus.SETUP_REQUIRED),"gpt-5.6")
        with self.assertRaises(FrozenInstanceError):p.provider="other"
        with self.assertRaises(ValueError):
            m.OpenAIConfigurationProposal("gpt-5.6",p.source_state,"other")
        with self.assertRaises(ValueError):
            m.OpenAIConfigurationProposal("gpt-5.6",p.source_state,"openai",False)

    def test_source_has_only_pure_presentation_dependency(self):
        tree=ast.parse(inspect.getsource(m))
        imported={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(imported,{"dataclasses","nayeon.brain.onboarding_status_view"})
        calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr for n in ast.walk(tree)
               if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))}
        for forbidden in ("open","get","put","delete","is_available","validate","save","clear","connect","replace"):
            self.assertNotIn(forbidden,calls)


if __name__ == "__main__":
    unittest.main()
