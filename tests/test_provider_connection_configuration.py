"""Phase 8.3 non-secret connection metadata contract and import guards."""

import ast
from dataclasses import fields, FrozenInstanceError, is_dataclass
from pathlib import Path
from typing import get_type_hints
import unittest
from unittest.mock import Mock

from nayeon.brain.connection import ProviderConnectionConfiguration as Configuration
from nayeon.secrets.contracts import SecretIdentifier


class StringSubclass(str):
    pass


class IdentifierSubclass(SecretIdentifier):
    pass


class ConnectionConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.identifier = SecretIdentifier("unmapped.credential")

    def test_frozen_slotted_exact_dataclass_fields_and_annotations(self):
        self.assertTrue(is_dataclass(Configuration))
        self.assertTrue(Configuration.__dataclass_params__.frozen)
        self.assertEqual(Configuration.__slots__, ("provider", "model", "credential"))
        self.assertEqual(tuple(f.name for f in fields(Configuration)), Configuration.__slots__)
        self.assertEqual(Configuration.__annotations__, {"provider": str, "model": str, "credential": SecretIdentifier})
        self.assertEqual(get_type_hints(Configuration), Configuration.__annotations__)
        config = Configuration("openai", "gpt-5.6", self.identifier)
        self.assertFalse(hasattr(config, "__dict__"))
        self.assertIs(config.credential, self.identifier)
        for name in Configuration.__slots__:
            with self.assertRaises(FrozenInstanceError):
                setattr(config, name, None)
            with self.assertRaises(FrozenInstanceError):
                delattr(config, name)

    def test_provider_exact_native_type_without_coercion(self):
        for bad in (StringSubclass("openai"), None, 1, b"openai", Mock()):
            with self.assertRaises(TypeError):
                Configuration(bad, "model", self.identifier)

    def test_provider_length_and_canonical_ascii_syntax(self):
        for valid in ("a", "0", "a" * 64, "9._-z", "vendor.example_name-1"):
            self.assertEqual(Configuration(valid, "model", self.identifier).provider, valid)
        for bad in ("", "a" * 65, "OpenAI", " openai", "openai ", ".vendor", "_vendor", "-vendor",
                    "a/b", "a:b", "a b", "a\n", "é", "aé", "Ａ", "a\x00", "a\u200b"):
            with self.subTest(provider=repr(bad)):
                with self.assertRaises(ValueError):
                    Configuration(bad, "model", self.identifier)

    def test_model_exact_type_and_length(self):
        for bad in (StringSubclass("model"), None, 1, b"model", Mock()):
            with self.assertRaises(TypeError):
                Configuration("vendor", bad, self.identifier)
        for valid in ("x", "x" * 128):
            self.assertEqual(Configuration("vendor", valid, self.identifier).model, valid)
        for bad in ("", "x" * 129):
            with self.assertRaises(ValueError):
                Configuration("vendor", bad, self.identifier)

    def test_model_rejects_edge_whitespace_control_and_nonprintable(self):
        for bad in (" model", "model ", "\tmodel", "model\n", "\u00a0model", "model\u3000", " "):
            with self.assertRaises(ValueError):
                Configuration("vendor", bad, self.identifier)
        for code in (*range(32), 127, 128, 159, 0x200b, 0x2028, 0x2029, 0xd800):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    Configuration("vendor", "a" + chr(code) + "b", self.identifier)

    def test_model_preserves_generic_printable_text_and_provider_neutrality(self):
        for provider, model in (("openai", "gpt-5.6"), ("anthropic", "claude-sonnet-4"),
                                ("google", "models/gemini-2.5-pro"), ("new_vendor", "模型 café / V2: beta")):
            config = Configuration(provider, model, self.identifier)
            self.assertEqual((config.provider, config.model), (provider, model))
            # Deliberately unrelated identifier: metadata grants no binding authority.
            self.assertIs(config.credential, self.identifier)

    def test_credential_exact_identifier_no_coercion(self):
        for bad in (IdentifierSubclass("key"), "key", None, Mock(value="key"), {"value": "key"}):
            with self.assertRaises(TypeError):
                Configuration("vendor", "model", bad)

    def test_safe_metadata_equality_hash(self):
        first = Configuration("vendor", "model", self.identifier)
        second = Configuration("vendor", "model", SecretIdentifier(self.identifier.value))
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(len({first, second}), 1)
        for other in (Configuration("other", "model", self.identifier),
                      Configuration("vendor", "other", self.identifier),
                      Configuration("vendor", "model", SecretIdentifier("other"))):
            self.assertNotEqual(first, other)

    def test_no_authority_persistence_or_service_surface(self):
        config = Configuration("vendor", "model", self.identifier)
        self.assertEqual({n for n in dir(config) if not n.startswith("_")}, {"provider", "model", "credential"})
        for name in ("resolve", "get", "connect", "test", "test_candidate", "test_stored", "remove", "replace",
                     "save", "load", "encode", "decode", "bootstrap", "backend", "validator"):
            self.assertFalse(hasattr(config, name))

    def test_exact_source_import_boundary(self):
        path = Path(__file__).resolve().parents[1] / "nayeon/brain/connection.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(n, ast.ImportFrom) and n.level == 0 for n in imports))
        self.assertEqual([(n.module, [a.name for a in n.names]) for n in imports],
                         [("dataclasses", ["dataclass"]), ("nayeon.secrets.contracts", ["SecretIdentifier"])])
        forbidden = {"SecretValue", "SecretBackend", "BoundSecretResolver", "BoundCredentialLifecycle",
                     "WindowsCredentialBackend", "SecretStore", "OpenAIProvider", "print", "open", "eval", "exec",
                     "__import__", "environ", "getenv", "resolve", "get", "connect", "remove", "save", "load"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.Attribute)):
                self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr, forbidden)


if __name__ == "__main__":
    unittest.main()
