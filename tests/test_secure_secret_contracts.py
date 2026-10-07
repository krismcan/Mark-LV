"""Phase 8.1 opaque contracts; synthetic plaintext only."""

from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
import inspect
import pickle
import unittest
from typing import get_type_hints

from nayeon.secrets import contracts as m


class StringSubclass(str):
    pass


class SecureSecretContractTests(unittest.TestCase):
    def test_identifier_exact_shape(self):
        self.assertTrue(is_dataclass(m.SecretIdentifier))
        self.assertEqual([field.name for field in fields(m.SecretIdentifier)], ["value"])
        self.assertEqual(get_type_hints(m.SecretIdentifier), {"value": str})
        self.assertEqual(m.SecretIdentifier.__slots__, ("value",))
        self.assertTrue(m.SecretIdentifier.__dataclass_params__.frozen)
        identifier = m.SecretIdentifier("openai.api_key")
        self.assertFalse(hasattr(identifier, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            identifier.value = "other"
        with self.assertRaises(FrozenInstanceError):
            del identifier.value

    def test_provider_neutral_valid_identifiers_and_boundaries(self):
        for value in ("a", "0", "a" * 128, "openai.api_key", "anthropic.api_key",
                      "google.api_key", "new-provider_99.key-2", "0._-"):
            with self.subTest(value=value):
                self.assertEqual(m.SecretIdentifier(value).value, value)

    def test_identifier_invalid_syntax_is_never_normalized(self):
        for value in ("", "a" * 129, " key", "key ", "key\n", "A", "aB", ".a",
                      "_a", "-a", "a b", "a/b", "a:b", "a\x00", "é", "ａ", "١"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "^Invalid secret identifier (syntax|length)$"):
                    m.SecretIdentifier(value)

    def test_exact_native_strings_only(self):
        for contract in (m.SecretIdentifier, m.SecretValue):
            for value in (None, 1, b"synthetic", ["synthetic"], StringSubclass("synthetic")):
                with self.subTest(contract=contract, kind=type(value)):
                    with self.assertRaises(TypeError):
                        contract(value)

    def test_secret_value_preserves_original_text(self):
        for value in (" synthetic ", "\nsynthetic\t", "한글🌸E\u0301", "a\x00b", "a\ud800"):
            secret = m.SecretValue(value)
            self.assertIs(secret.reveal(), value)
            self.assertEqual(secret.reveal(), value)

    def test_secret_value_rejects_blank(self):
        for value in ("", " ", "\n\t\r", "\u2003\u00a0"):
            with self.assertRaisesRegex(ValueError, "^Secret value must not be blank$"):
                m.SecretValue(value)

    def test_secret_value_immutable_and_slotted(self):
        secret = m.SecretValue("synthetic-marker")
        self.assertFalse(hasattr(secret, "__dict__"))
        self.assertFalse(is_dataclass(secret))
        self.assertEqual(m.SecretValue.__slots__, ("__value",))
        for name in ("value", "plaintext", "_SecretValue__value", "extra"):
            with self.assertRaises(AttributeError):
                setattr(secret, name, "replacement")
            with self.assertRaises(AttributeError):
                delattr(secret, name)
        with self.assertRaises(AttributeError):
            secret.__init__("replacement")
        self.assertEqual(secret.reveal(), "synthetic-marker")

    def test_sole_public_plaintext_escape_hatch(self):
        public = {name for name in vars(m.SecretValue) if not name.startswith("_")}
        self.assertEqual(public, {"reveal"})
        self.assertEqual(get_type_hints(m.SecretValue.reveal), {"return": str})
        self.assertFalse(any(isinstance(item, property) for item in vars(m.SecretValue).values()))

    def test_fixed_redaction_and_identity_equality(self):
        first = m.SecretValue("synthetic-marker-one")
        same_text = m.SecretValue("synthetic-marker-one")
        other = m.SecretValue("synthetic-marker-two")
        for secret in (first, same_text, other):
            self.assertEqual(str(secret), "SecretValue(<redacted>)")
            self.assertEqual(repr(secret), "SecretValue(<redacted>)")
            self.assertNotIn(secret.reveal(), str(secret))
            self.assertNotIn(secret.reveal(), repr(secret))
        self.assertEqual(first, first)
        self.assertNotEqual(first, same_text)
        self.assertNotEqual(first, other)
        self.assertNotEqual(first, first.reveal())
        self.assertIs(m.SecretValue.__eq__, object.__eq__)
        self.assertIs(m.SecretValue.__hash__, object.__hash__)
        self.assertEqual(len({first, same_text, other}), 3)

    def test_no_serialization_iteration_or_conversion(self):
        secret = m.SecretValue("synthetic-marker")
        for operation in (asdict, bytes, iter, list, dict, pickle.dumps):
            with self.subTest(operation=operation):
                with self.assertRaises(TypeError):
                    operation(secret)
        for operation in (secret.__getstate__, secret.__reduce__):
            with self.assertRaises(TypeError):
                operation()
        for name in ("serialize", "to_dict", "to_mapping", "dump", "export", "__iter__", "__bytes__"):
            self.assertFalse(hasattr(secret, name))

    def test_backend_exact_narrow_protocol(self):
        self.assertTrue(m.SecretBackend._is_protocol)
        self.assertEqual({name for name in vars(m.SecretBackend) if not name.startswith("_")},
                         {"get", "put", "delete", "is_available"})
        for name, result in (("get", m.SecretValue), ("delete", bool), ("is_available", bool)):
            method = getattr(m.SecretBackend, name)
            self.assertEqual(list(inspect.signature(method).parameters), ["self", "identifier"])
            self.assertEqual(get_type_hints(method), {"identifier": m.SecretIdentifier, "return": result})
        self.assertEqual(get_type_hints(m.SecretBackend.put),
                         {"identifier": m.SecretIdentifier, "value": m.SecretValue, "return": type(None)})
        for name in ("enumerate", "list", "all", "dump", "export"):
            self.assertFalse(hasattr(m.SecretBackend, name))

    def test_new_errors_are_separate_from_legacy_contract(self):
        from nayeon.secrets.store import SecretNotFoundError as LegacyError
        self.assertIsNot(m.SecretNotFoundError, LegacyError)
        self.assertTrue(issubclass(m.SecretNotFoundError, RuntimeError))
        self.assertTrue(issubclass(m.SecretStorageError, RuntimeError))


if __name__ == "__main__":
    unittest.main()
