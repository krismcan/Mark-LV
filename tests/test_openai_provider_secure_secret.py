"""Sealed provider authority tests: patched factory only, no network."""

import ast
import inspect
import os
from pathlib import Path
from types import SimpleNamespace
import traceback
import unittest
from unittest.mock import Mock, patch

from nayeon.brain.providers import openai as m
from nayeon.brain.service import AIMessage
from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)
from nayeon.secrets.resolver import BoundSecretResolver


class ResolverSubclass(BoundSecretResolver):
    pass


class OpenAIProviderSecureSecretTests(unittest.TestCase):
    def setUp(self):
        self.plaintext = " synthetic-credential-\u2603 "
        self.secret = SecretValue(self.plaintext)
        self.backend = Mock()
        self.backend.get.return_value = self.secret
        self.resolver = BoundSecretResolver(self.backend, SecretIdentifier("openai.api_key"))
        self.sdk_patch = patch.object(m, "create_openai_client")
        self.sdk = self.sdk_patch.start()
        self.addCleanup(self.sdk_patch.stop)

    def provider(self, **kwargs):
        return m.OpenAIProvider(self.resolver, **kwargs)

    def test_required_api_default_and_unchanged_model_semantics(self):
        signature = inspect.signature(m.OpenAIProvider)
        self.assertEqual(list(signature.parameters), ["api_key", "model"])
        self.assertIs(signature.parameters["api_key"].default, inspect.Parameter.empty)
        self.assertIs(signature.parameters["model"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(self.provider().model, "gpt-5.6")
        arbitrary = object()
        self.assertIs(self.provider(model=arbitrary).model, arbitrary)

    def test_exact_resolver_required(self):
        for invalid in (self.backend, Mock(identifier=SecretIdentifier("openai.api_key")),
                        ResolverSubclass(self.backend, SecretIdentifier("openai.api_key")),
                        {}, None):
            with self.assertRaisesRegex(TypeError, "^API key must be an exact BoundSecretResolver$"):
                m.OpenAIProvider(invalid)
        self.assertEqual(self.backend.mock_calls, [])
        self.sdk.assert_not_called()

    def test_wrong_identifier_rejected_before_resolving(self):
        resolver = BoundSecretResolver(self.backend, SecretIdentifier("other.api_key"))
        with patch.object(BoundSecretResolver, "resolve", side_effect=AssertionError("no read")):
            with self.assertRaisesRegex(ValueError, "^API key resolver has an invalid identifier$"):
                m.OpenAIProvider(resolver)
        self.assertEqual(self.backend.mock_calls, [])
        self.sdk.assert_not_called()

    def test_constructor_no_resolution_or_client(self):
        provider = self.provider()
        self.assertIs(provider._api_key, self.resolver)
        self.assertIsNone(provider._client)
        self.assertEqual(self.backend.mock_calls, [])
        self.sdk.assert_not_called()

    def test_lazy_exact_holder_client_caching_and_authority_release(self):
        provider = self.provider()
        with patch.object(BoundSecretResolver, "resolve", autospec=True,
                          return_value=self.secret) as resolve, \
             patch.object(SecretValue, "reveal", side_effect=AssertionError("provider must not reveal")):
            self.assertIs(provider._get_client(), self.sdk.return_value)
            resolve.assert_called_once_with(self.resolver)
            self.sdk.assert_called_once_with(self.secret)
            self.assertIs(self.sdk.call_args.args[0], self.secret)
            self.assertIsNone(provider._api_key)
            self.assertIs(provider._get_client(), self.sdk.return_value)
            resolve.assert_called_once()
        self.sdk.assert_called_once()
        self.assertEqual(set(vars(provider)), {"_api_key", "_client", "_model"})
        for value in vars(provider).values():
            self.assertIsNot(value, self.secret)
            self.assertIsNot(value, self.plaintext)
            self.assertIsNot(value, self.resolver)
            self.assertIsNot(value, self.backend)

    def test_missing_and_storage_errors_retain_authority_for_retry(self):
        for error in (SecretNotFoundError("Secret is not available"),
                      SecretStorageError("Secret storage operation failed")):
            provider = self.provider()
            self.backend.get.reset_mock()
            self.sdk.reset_mock()
            self.backend.get.side_effect = [error, self.secret]
            with self.assertRaises(type(error)) as caught:
                provider._get_client()
            self.assertIs(caught.exception, error)
            self.assertIsNone(provider._client)
            self.assertIs(provider._api_key, self.resolver)
            self.sdk.assert_not_called()
            self.assertIs(provider._get_client(), self.sdk.return_value)
            self.assertEqual(self.backend.get.call_count, 2)
            self.assertIsNone(provider._api_key)

    def test_client_failure_sanitized_and_retry_resolves_again(self):
        provider = self.provider()
        self.sdk.side_effect = RuntimeError("synthetic-private-detail " + self.plaintext)
        try:
            provider._get_client()
        except m.OpenAIProviderInitializationError as error:
            self.assertIsInstance(error, RuntimeError)
            self.assertEqual(str(error), "OpenAI provider initialization failed")
            self.assertIsNone(error.__cause__)
            self.assertTrue(error.__suppress_context__)
            formatted = traceback.format_exc()
            self.assertNotIn(self.plaintext, formatted)
            self.assertNotIn("synthetic-private-detail", formatted)
        else:
            self.fail("expected sanitized failure")
        self.assertIsNone(provider._client)
        self.assertIs(provider._api_key, self.resolver)
        self.backend.get.assert_called_once_with(self.resolver.identifier)
        self.sdk.side_effect = None
        self.assertIs(provider._get_client(), self.sdk.return_value)
        self.assertEqual(self.backend.get.call_count, 2)
        self.assertIsNone(provider._api_key)

    def test_construction_process_control_propagates_and_retains_resolver(self):
        for error_type in (KeyboardInterrupt, SystemExit):
            provider = self.provider()
            error = error_type()
            self.sdk.side_effect = error
            with self.assertRaises(error_type) as caught:
                provider._get_client()
            self.assertIs(caught.exception, error)
            self.assertIs(provider._api_key, self.resolver)
            self.assertIsNone(provider._client)

    def test_generate_preserves_input_usage_normalization_and_cached_client(self):
        provider = self.provider(model="synthetic-model")
        response = SimpleNamespace(output_text="synthetic-answer", usage=SimpleNamespace(
            input_tokens=3, output_tokens=4, total_tokens=7))
        create = self.sdk.return_value.responses.create
        create.return_value = response
        messages = [AIMessage("user", "hello"), AIMessage("assistant", "prior")]
        answer = provider.generate(messages, system_prompt="synthetic-instructions")
        create.assert_called_once_with(model="synthetic-model", input=[
            {"role": "user", "content": "hello"}, {"role": "assistant", "content": "prior"}],
            instructions="synthetic-instructions")
        self.assertEqual((answer.text, answer.provider, answer.model),
                         ("synthetic-answer", "openai", "synthetic-model"))
        self.assertEqual(answer.usage, {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7})
        self.backend.get.assert_called_once_with(self.resolver.identifier)
        response.usage = None
        for prompt in (None, ""):
            create.reset_mock()
            self.assertEqual(provider.generate(messages, system_prompt=prompt).usage, {})
            self.assertNotIn("instructions", create.call_args.kwargs)
        self.backend.get.assert_called_once()
        self.sdk.assert_called_once_with(self.secret)

    def test_empty_messages_fail_before_secret_or_sdk(self):
        with self.assertRaisesRegex(ValueError, "^At least one message is required\\.$"):
            self.provider().generate([])
        self.backend.get.assert_not_called()
        self.sdk.assert_not_called()

    def test_generation_errors_remain_untranslated(self):
        error = RuntimeError("synthetic-response-error")
        self.sdk.return_value.responses.create.side_effect = error
        provider = self.provider()
        with self.assertRaises(RuntimeError) as caught:
            provider.generate([AIMessage("user", "hello")])
        self.assertIs(caught.exception, error)
        self.assertIs(provider._client, self.sdk.return_value)
        self.assertIsNone(provider._api_key)

    def test_provider_does_not_access_environment(self):
        with patch.object(os, "getenv", side_effect=AssertionError("no environment")), \
             patch.dict(os.environ, {}, clear=True):
            self.provider()._get_client()
        self.sdk.assert_called_once_with(self.secret)

    def test_production_import_and_consumer_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        resolver_consumers, store_consumers, backend_consumers, contract_consumers = set(), set(), set(), set()
        for path in (root / "nayeon").rglob("*.py"):
            relative = path.relative_to(root).as_posix()
            source = path.read_text(encoding="utf-8")
            if relative != "nayeon/secrets/store.py":
                self.assertNotIn("OPENAI_API_KEY", source)
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imported = {alias.name for alias in node.names}
                    module = node.module or ""
                    if module == "nayeon.secrets.resolver" or "BoundSecretResolver" in imported:
                        resolver_consumers.add(relative)
                    if module == "nayeon.secrets.store" or "SecretStore" in imported:
                        store_consumers.add(relative)
                    if module == "nayeon.secrets.windows_credential" or "WindowsCredentialBackend" in imported:
                        backend_consumers.add(relative)
                    if module == "nayeon.secrets.contracts":
                        if relative == "nayeon/brain/connection_document.py":
                            self.assertEqual(imported, {"SecretIdentifier"})
                        contract_consumers.add(relative)
                    if relative == "nayeon/brain/providers/openai.py":
                        self.assertFalse(imported & {"SecretStore", "SecretBackend", "WindowsCredentialBackend"})
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "nayeon.secrets.resolver":
                            resolver_consumers.add(relative)
                        if alias.name == "nayeon.secrets.store":
                            store_consumers.add(relative)
                        if alias.name == "nayeon.secrets.windows_credential":
                            backend_consumers.add(relative)
                        if alias.name == "nayeon.secrets.contracts":
                            contract_consumers.add(relative)
        self.assertEqual(resolver_consumers, {"nayeon/brain/providers/openai.py",
                                              "nayeon/brain/connection_composition.py"})
        self.assertEqual(store_consumers, set())
        self.assertEqual(backend_consumers, set())
        self.assertEqual(contract_consumers, {"nayeon/secrets/windows_credential.py",
                         "nayeon/secrets/resolver.py", "nayeon/brain/providers/openai.py",
                         "nayeon/secrets/lifecycle.py", "nayeon/brain/connection.py",
                         "nayeon/brain/connection_document.py",
                         "nayeon/brain/providers/openai_client.py",
                         "nayeon/brain/providers/openai_validation.py",
                         "nayeon/brain/connection_composition.py",
                         "nayeon/brain/connection_readiness.py"})

    def test_provider_exact_imports_and_no_environment_operations(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / "nayeon/brain/providers/openai.py").read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports))
        self.assertEqual([(node.module, [alias.name for alias in node.names]) for node in imports], [
            ("__future__", ["annotations"]), ("typing", ["Any"]), ("nayeon.brain.providers.openai_client", ["create_openai_client"]),
            ("nayeon.brain.service", ["AIMessage", "AIResponse"]),
            ("nayeon.secrets.contracts", ["SecretIdentifier"]),
            ("nayeon.secrets.resolver", ["BoundSecretResolver"]),
        ])
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.Attribute)):
                self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr,
                                 {"environ", "getenv", "SecretStore", "SecretBackend",
                                  "WindowsCredentialBackend", "__import__", "eval", "exec", "reveal"})


if __name__ == "__main__":
    unittest.main()
