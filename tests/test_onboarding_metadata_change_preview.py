"""Phase 8.14 read-only metadata change preview security and behavior tests."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

from nayeon.brain import onboarding_metadata_change_preview as m
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.onboarding_configuration_proposal import propose_openai_configuration
from nayeon.brain.onboarding_metadata_document import compose_onboarding_metadata_document
from nayeon.brain.onboarding_status_view import present_onboarding_status, OnboardingDisplayState
from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.secrets.contracts import SecretIdentifier


def candidate(model="gpt-5.6"):
    state = ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED)
    view = present_onboarding_status(state, advise_connection_recovery(state))
    proposal = propose_openai_configuration(view, model)
    return proposal, compose_onboarding_metadata_document(proposal)


def current(provider="openai", model="gpt-5.6", key="openai.api_key"):
    return ProviderConnectionDocumentV1(connection=ProviderConnectionConfiguration(
        provider=provider, model=model, credential=SecretIdentifier(key)))


class OnboardingMetadataChangePreviewTests(unittest.TestCase):
    def test_create_from_explicit_absent_typed_snapshot(self):
        proposal, preview = candidate()
        a = m.preview_onboarding_metadata_change(proposal, preview, ProviderConnectionDocumentV1())
        b = m.preview_onboarding_metadata_change(proposal, preview, ProviderConnectionDocumentV1())
        self.assertIsNot(a, b)
        self.assertIs(a.kind, m.MetadataChangeKind.CREATE)
        self.assertIsNone(a.current_model)
        self.assertEqual((a.provider, a.proposed_model, a.credential_reference),
                         ("openai", "gpt-5.6", "openai.api_key"))
        self.assertIs(a.source_state, OnboardingDisplayState.NEEDS_SETUP)
        self.assertIs(a.requires_reobservation, True)
        self.assertIs(a.requires_explicit_confirmation, True)
        self.assertFalse(hasattr(a, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            a.kind = m.MetadataChangeKind.MODEL_CHANGE

    def test_unchanged_existing_canonical(self):
        proposal, preview = candidate()
        result = m.preview_onboarding_metadata_change(proposal, preview, current())
        self.assertIs(result.kind, m.MetadataChangeKind.UNCHANGED)
        self.assertEqual(result.current_model, "gpt-5.6")
        self.assertIs(result.requires_explicit_confirmation, True)

    def test_model_change_requires_reobservation_and_confirmation(self):
        proposal, preview = candidate("gpt-5.6")
        existing = current(model="gpt-4o-mini")
        result = m.preview_onboarding_metadata_change(proposal, preview, existing)
        self.assertIs(result.kind, m.MetadataChangeKind.MODEL_CHANGE)
        self.assertEqual(result.current_model, "gpt-4o-mini")
        self.assertEqual(result.proposed_model, "gpt-5.6")
        self.assertIs(result.requires_reobservation, True)
        self.assertEqual(existing.connection.model, "gpt-4o-mini")

    def test_unsupported_current_metadata_fails_closed(self):
        proposal, preview = candidate()
        for snapshot in (current(provider="other"), current(key="other.key"),
                         current(provider="other", key="other.key")):
            with self.subTest(snapshot=snapshot.connection.provider), self.assertRaises(ValueError):
                m.preview_onboarding_metadata_change(proposal, preview, snapshot)

    def test_requires_exact_typed_current_and_matching_proposal(self):
        proposal, preview = candidate()
        for bad in (None, object(), {}, True, "unconfigured"):
            with self.subTest(bad=type(bad)), self.assertRaises(TypeError):
                m.preview_onboarding_metadata_change(proposal, preview, bad)
        with self.assertRaises(ValueError):
            m.preview_onboarding_metadata_change(
                proposal, candidate("gpt-4o-mini")[1], ProviderConnectionDocumentV1())
        with self.assertRaises(TypeError):
            m.preview_onboarding_metadata_change(
                {}, preview, ProviderConnectionDocumentV1())

    def test_direct_dataclass_cannot_claim_authority_or_inconsistent_change(self):
        proposal, preview = candidate()
        data = dict(kind=m.MetadataChangeKind.CREATE, proposed_model="gpt-5.6",
                    current_model=None, source_state=proposal.source_state)
        for patch in ({"requires_reobservation": False},
                      {"requires_explicit_confirmation": False},
                      {"provider": "other"}, {"credential_reference": "other.key"},
                      {"kind": "create"}, {"source_state": "needs_setup"},
                      {"current_model": "gpt-4o-mini"},
                      {"kind": m.MetadataChangeKind.UNCHANGED},
                      {"kind": m.MetadataChangeKind.MODEL_CHANGE},
                      {"proposed_model": " not valid "}):
            with self.subTest(patch=patch), self.assertRaises((TypeError, ValueError)):
                m.OnboardingMetadataChangePreview(**(data | patch))

    def test_no_storage_credential_provider_or_runtime_authority(self):
        tree = ast.parse(inspect.getsource(m))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {
            "dataclasses", "enum", "nayeon.brain.connection_document",
            "nayeon.brain.onboarding_configuration_proposal",
            "nayeon.brain.onboarding_metadata_review",
            "nayeon.brain.onboarding_status_view",
        })
        calls = {n.func.id if isinstance(n.func, ast.Name) else n.func.attr
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        for forbidden in ("open", "save", "replace", "delete", "put", "connect",
                          "validate", "is_available", "get", "OpenAIProvider",
                          "WindowsCredentialBackend", "ProviderConnectionFileStore"):
            self.assertNotIn(forbidden, calls)


if __name__ == "__main__":
    unittest.main()
