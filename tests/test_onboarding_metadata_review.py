"""Phase 8.13 independent pure human review contract tests."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

from nayeon.brain import onboarding_metadata_review as review
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.onboarding_configuration_proposal import propose_openai_configuration
from nayeon.brain.onboarding_metadata_document import compose_onboarding_metadata_document
from nayeon.brain.onboarding_status_view import present_onboarding_status, OnboardingDisplayState
from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus
from nayeon.brain.connection_recovery_advice import advise_connection_recovery


def fixture():
    observation = ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED)
    status = present_onboarding_status(observation, advise_connection_recovery(observation))
    proposal = propose_openai_configuration(status, "gpt-5.6")
    return proposal, compose_onboarding_metadata_document(proposal)


class OnboardingMetadataReviewTests(unittest.TestCase):
    def test_fresh_canonical_nonsecret_review(self):
        proposal, document = fixture()
        a = review.present_onboarding_metadata_review(proposal, document)
        b = review.present_onboarding_metadata_review(proposal, document)
        self.assertIsNot(a, b)
        self.assertEqual((a.provider, a.model, a.credential_reference),
                         ("openai", "gpt-5.6", "openai.api_key"))
        self.assertIs(a.source_state, OnboardingDisplayState.NEEDS_SETUP)
        self.assertIs(a.requires_reobservation, True)
        self.assertIs(a.requires_explicit_confirmation, True)
        self.assertFalse(hasattr(a, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            a.model = "other"

    def test_reject_nonexact_proposal_and_document(self):
        proposal, document = fixture()
        for wrong in (None, "openai", {}, object(), True):
            with self.subTest(wrong=type(wrong)), self.assertRaises(TypeError):
                review.present_onboarding_metadata_review(wrong, document)
            with self.subTest(doc=type(wrong)), self.assertRaises(TypeError):
                review.present_onboarding_metadata_review(proposal, wrong)

    def test_reject_absent_or_mismatched_document(self):
        proposal, doc = fixture()
        with self.assertRaises(ValueError):
            review.present_onboarding_metadata_review(proposal, ProviderConnectionDocumentV1())
        different = propose_openai_configuration(
            present_onboarding_status(
                ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED),
                advise_connection_recovery(ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED))
            ), "gpt-4o-mini"
        )
        with self.assertRaises(ValueError):
            review.present_onboarding_metadata_review(different, doc)

    def test_fail_closed_review_contract(self):
        proposal, document = fixture()
        item = review.present_onboarding_metadata_review(proposal, document)
        for changed in (
            {"provider": "other"},
            {"credential_reference": "other"},
            {"requires_reobservation": False},
            {"requires_explicit_confirmation": False},
            {"source_state": "needs_setup"},
        ):
            data = dict(provider=item.provider, model=item.model,
                        credential_reference=item.credential_reference,
                        source_state=item.source_state)
            data.update(changed)
            with self.subTest(changed=changed), self.assertRaises((ValueError, TypeError)):
                review.OnboardingMetadataReview(**data)

    def test_no_io_credential_or_runtime_import(self):
        source = inspect.getsource(review)
        tree = ast.parse(source)
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertEqual(imports, {
            "dataclasses",
            "nayeon.brain.connection_document",
            "nayeon.brain.onboarding_configuration_proposal",
            "nayeon.brain.onboarding_metadata_document",
            "nayeon.brain.onboarding_status_view",
        })
        calls = {node.func.id if isinstance(node.func, ast.Name) else node.func.attr
                 for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, (ast.Name, ast.Attribute))}
        for banned in ("open", "save", "replace", "delete", "put",
                       "connect", "validate", "is_available", "OpenAIProvider"):
            self.assertNotIn(banned, calls)


if __name__ == "__main__":
    unittest.main()
