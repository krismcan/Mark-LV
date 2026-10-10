"""Phase 8.15 architecture-scope audit: preserve explicitly separated surfaces."""
import ast
from pathlib import Path
import unittest

from nayeon.brain.onboarding_metadata_change_preview import (
    preview_onboarding_metadata_change,
)
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.agent.session import ConversationSession


class Phase815ThreatBoundaryTests(unittest.TestCase):
    def test_existing_onboarding_not_exposed_as_conversation_capability(self):
        for implementation in (OpenAICredentialOnboarding, ProviderConnectionService):
            self.assertFalse(hasattr(implementation, "capability"))
            self.assertFalse(hasattr(implementation, "map_intent_arguments"))
        self.assertFalse(hasattr(ConversationSession, "connect_credential"))
        self.assertFalse(hasattr(ConversationSession, "replace_credential"))
        self.assertFalse(hasattr(ConversationSession, "delete_credential"))

    def test_review_never_exposes_mutation_methods(self):
        self.assertTrue(callable(preview_onboarding_metadata_change))
        p = Path(__file__).resolve().parents[1]
        for file in (
            "nayeon/brain/onboarding_metadata_review.py",
            "nayeon/brain/onboarding_metadata_change_preview.py",
        ):
            tree = ast.parse((p / file).read_text(encoding="utf-8"))
            imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertFalse(any("credential_onboarding" in (name or "") or
                                 "connection_persistence" in (name or "") for name in imports))
            self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))

    def test_credential_storage_and_metadata_ownership_are_distinct(self):
        self.assertNotIn("SecretBackend", ProviderConnectionService.__annotations__)
        self.assertFalse(hasattr(ProviderConnectionService, "connect"))
        self.assertFalse(hasattr(OpenAICredentialOnboarding, "save_metadata"))


if __name__ == "__main__":
    unittest.main()
