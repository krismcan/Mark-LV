"""Phase 8.12 pure metadata-document composition tests."""
import ast
import inspect
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from nayeon.brain import onboarding_metadata_document as m
from nayeon.brain.onboarding_configuration_proposal import propose_openai_configuration
from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus
from nayeon.brain.connection_recovery_advice import advise_connection_recovery
from nayeon.brain.onboarding_status_view import present_onboarding_status
from nayeon.brain.connection_document import ProviderConnectionDocumentV1, provider_connection_document_to_mapping
from nayeon.brain.connection_persistence import ProviderConnectionFileStore


def valid_proposal():
    observation=ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED)
    display=present_onboarding_status(observation,advise_connection_recovery(observation))
    return propose_openai_configuration(display,"gpt-5.6")


class OnboardingMetadataDocumentTests(unittest.TestCase):
    def test_canonical_openai_document(self):
        doc=m.compose_onboarding_metadata_document(valid_proposal())
        self.assertIs(type(doc),ProviderConnectionDocumentV1)
        self.assertEqual(doc.connection.provider,"openai")
        self.assertEqual(doc.connection.model,"gpt-5.6")
        self.assertEqual(doc.connection.credential.value,"openai.api_key")
        self.assertEqual(provider_connection_document_to_mapping(doc),{
          "schema_version":1,
          "connection":{"provider":"openai","model":"gpt-5.6","credential":"openai.api_key"},
        })

    def test_fresh_objects_and_no_storage_activity(self):
        proposal=valid_proposal()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"metadata.json"
            with mock.patch.object(ProviderConnectionFileStore,"save",
                                    side_effect=AssertionError("Forbidden write")):
                first=m.compose_onboarding_metadata_document(proposal)
                second=m.compose_onboarding_metadata_document(proposal)
            self.assertIsNot(first,second)
            self.assertIsNot(first.connection,second.connection)
            self.assertFalse(path.exists())

    def test_exact_input_gate(self):
        for invalid in (None,"gpt-5.6",object(),{},True):
            with self.subTest(value=type(invalid)),self.assertRaises(TypeError):
                m.compose_onboarding_metadata_document(invalid)

    def test_no_write_or_credential_backend_import(self):
        tree=ast.parse(inspect.getsource(m))
        imported={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(imported,{
           "nayeon.brain.connection",
           "nayeon.brain.connection_document",
           "nayeon.brain.onboarding_configuration_proposal",
           "nayeon.secrets.contracts",
        })
        calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr
               for n in ast.walk(tree) if isinstance(n,ast.Call)
               and isinstance(n.func,(ast.Name,ast.Attribute))}
        for forbidden in ("open","save","put","delete","get","replace","connect",
                          "validate","is_available","OpenAIProvider","WindowsCredentialBackend"):
            self.assertNotIn(forbidden,calls)


if __name__ == "__main__":
    unittest.main()
