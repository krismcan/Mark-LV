"""Phase 8.8 trusted composition tests: no real credentials or network calls."""

import ast
import inspect
import unittest
from unittest import mock

from nayeon.brain import credential_onboarding_composition as m
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.secrets.contracts import SecretIdentifier, SecretValue
from nayeon.secrets.lifecycle import CredentialValidationStatus


class FakeBackend:
    def __init__(self):
        self.values = {}
        self.calls = []
    def get(self, identifier):
        self.calls.append(("get", identifier))
        return self.values[identifier]
    def put(self, identifier, value):
        self.calls.append(("put", identifier))
        self.values[identifier] = value
    def delete(self, identifier):
        self.calls.append(("delete", identifier))
        return self.values.pop(identifier, None) is not None
    def is_available(self, identifier):
        self.calls.append(("is_available", identifier))
        return identifier in self.values


class FakeValidator:
    def __init__(self):
        self.calls = []
    def validate(self, value):
        self.calls.append(value)
        return CredentialValidationStatus.VALID


class CredentialOnboardingCompositionTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.validator = FakeValidator()

    def compose(self):
        with mock.patch.object(m, "OpenAICredentialValidator", return_value=self.validator) as factory:
            owner = m.compose_openai_credential_onboarding(self.backend)
        factory.assert_called_once_with()
        return owner

    def test_construction_has_no_storage_or_validator_calls(self):
        owner = self.compose()
        self.assertIs(type(owner), OpenAICredentialOnboarding)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, [])

    def test_binding_exact_openai_key_not_user_supplied_identifier(self):
        owner = self.compose()
        self.assertIs(owner.connect(SecretValue("fake-test-key")), CredentialValidationStatus.VALID)
        self.assertEqual({identifier for _, identifier in self.backend.calls},
                         {SecretIdentifier("openai.api_key")})

    def test_no_ambient_backend_or_untrusted_identifier_arguments(self):
        with self.assertRaises(TypeError):
            m.compose_openai_credential_onboarding()
        with self.assertRaises(TypeError):
            m.compose_openai_credential_onboarding(self.backend, SecretIdentifier("other.key"))
        with self.assertRaises(TypeError):
            m.compose_openai_credential_onboarding(self.backend, model="gpt-5.6")
        self.assertEqual(self.backend.calls, [])

    def test_missing_backend_capability_fail_closed(self):
        for invalid in (None, object(), 0, {"is_available": True}):
            with self.subTest(type=type(invalid).__name__):
                with mock.patch.object(m, "OpenAICredentialValidator", return_value=self.validator):
                    with self.assertRaises(TypeError):
                        m.compose_openai_credential_onboarding(invalid)

    def test_no_lifecycle_mutation_before_explicit_action(self):
        owner = self.compose()
        self.assertNotIn(SecretIdentifier("openai.api_key"), self.backend.values)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, [])
        self.assertIs(owner.is_connected(), False)
        self.assertEqual(self.backend.calls[0][0], "is_available")
        self.assertEqual(self.validator.calls, [])

    def test_fresh_independent_compositions(self):
        first = self.compose()
        second = self.compose()
        self.assertIsNot(first, second)
        self.assertEqual(self.backend.calls, [])
        self.assertNotIn("fake-test-key", repr(first))

    def test_creation_validator_failure_does_not_read_backend(self):
        with mock.patch.object(m, "OpenAICredentialValidator",
                               side_effect=RuntimeError("fake construction failed")):
            with self.assertRaisesRegex(RuntimeError, "fake construction failed"):
                m.compose_openai_credential_onboarding(self.backend)
        self.assertEqual(self.backend.calls, [])

    def test_no_sdk_client_or_native_api_imported(self):
        source = inspect.getsource(m)
        tree = ast.parse(source)
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imported, {
            "nayeon.brain.credential_onboarding",
            "nayeon.brain.providers.openai_validation",
            "nayeon.secrets.contracts",
            "nayeon.secrets.lifecycle",
        })
        for forbidden in ("WindowsCredentialBackend", "OpenAIProvider",
                          "create_openai_client", "load_openai_sdk", "getenv",
                          "ProviderConnectionService", "ProviderConnectionFileStore",
                          "compose_provider_ai_service", "SecretValue(", ".get("):
            self.assertNotIn(forbidden, source)

    def test_canonical_identity_bound_before_any_storage_activity(self):
        owner = self.compose()
        candidate = SecretValue("fake-test-key")
        owner.test_candidate(candidate)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, [candidate])

    def test_constructor_forged_validator_contract_fail_closed(self):
        with mock.patch.object(m, "OpenAICredentialValidator", return_value=object()):
            with self.assertRaises(TypeError):
                m.compose_openai_credential_onboarding(self.backend)
        self.assertEqual(self.backend.calls, [])


class Phase88FrozenProductionScope(unittest.TestCase):
    """Preserve every sealed Phase 8.7 production byte; allow two new modules."""

    def test_exact_phase87_production_and_requirements_frozen(self):
        from pathlib import Path
        import subprocess

        root = Path(__file__).resolve().parents[1]
        tag = "nayeon-v1-provider-connection-readiness-explicit-startup-01"
        sealed = "cadb399970a6c6bf9e1f937d033b5a7d60010c4d"
        delta = {
            "nayeon/brain/credential_onboarding.py",
            "nayeon/brain/credential_onboarding_composition.py",
            "nayeon/brain/connection_reconciliation.py",
            "nayeon/brain/connection_recovery_advice.py",
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
         "nayeon/brain/onboarding_metadata_document.py",
         "nayeon/brain/onboarding_metadata_review.py",
         "nayeon/brain/onboarding_metadata_change_preview.py",
         "nayeon/brain/onboarding_operation_advice.py",
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py",
         "nayeon/desktop_alpha/notepad.py",
        }

        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root).decode().strip()

        self.assertEqual(git("branch", "--show-current"), "nayeon-v1")
        self.assertEqual(git("cat-file", "-t", tag), "tag")
        self.assertEqual(git("rev-parse", tag + "^{commit}"), sealed)
        tracked = set(git("ls-tree", "-r", "--name-only", tag, "--", "nayeon").splitlines())
        production = {name for name in tracked if name.endswith(".py")}
        self.assertEqual(len(production), 102)
        current = {p.relative_to(root).as_posix()
                   for p in (root / "nayeon").rglob("*.py")}
        self.assertEqual(current, production | delta)
        changed = set(filter(None, git("diff", "--name-only", tag,
                                       "--", "nayeon", "requirements.txt").splitlines()))
        untracked = set(filter(None, git("ls-files", "--others",
                                         "--exclude-standard", "--", "nayeon").splitlines()))
        self.assertEqual(changed | untracked, delta)
        self.assertFalse(changed & untracked)
        for name in tracked | {"requirements.txt"}:
            with self.subTest(path=name):
                current_bytes = (root / name).read_bytes().replace(b"\r\n", b"\n")
                sealed_bytes = subprocess.check_output(
                    ["git", "show", tag + ":" + name], cwd=root
                ).replace(b"\r\n", b"\n")
                self.assertEqual(current_bytes, sealed_bytes)


if __name__ == "__main__":
    unittest.main()
