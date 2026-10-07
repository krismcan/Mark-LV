"""Deterministic Phase 8.2 resolver authority and privacy tests."""

import ast
import copy
from pathlib import Path
import pickle
import traceback
import unittest
from unittest.mock import Mock

from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)
from nayeon.secrets.resolver import BoundSecretResolver


class IdentifierSubclass(SecretIdentifier):
    pass


class ValueSubclass(SecretValue):
    pass


class BoundSecretResolverTests(unittest.TestCase):
    def setUp(self):
        self.identifier = SecretIdentifier("private.identifier")
        self.backend = Mock()
        self.backend.get.return_value = SecretValue("synthetic-marker")
        self.resolver = BoundSecretResolver(self.backend, self.identifier)

    def test_exact_public_slotted_private_shape(self):
        self.assertEqual(BoundSecretResolver.__slots__, ("__backend", "__identifier"))
        self.assertFalse(hasattr(self.resolver, "__dict__"))
        self.assertEqual({name for name in dir(self.resolver) if not name.startswith("_")},
                         {"identifier", "resolve"})
        self.assertIs(self.resolver.identifier, self.identifier)
        for name in ("backend", "put", "delete", "is_available", "rebind", "with_identifier",
                     "resolve_for", "enumerate", "export"):
            self.assertFalse(hasattr(self.resolver, name))

    def test_immutable_including_reinitialization(self):
        for name in ("identifier", "backend", "extra", "_BoundSecretResolver__backend",
                     "_BoundSecretResolver__identifier"):
            with self.assertRaises(AttributeError):
                setattr(self.resolver, name, None)
            with self.assertRaises(AttributeError):
                delattr(self.resolver, name)
        with self.assertRaises(AttributeError):
            self.resolver.__init__(Mock(), SecretIdentifier("replacement"))
        self.assertIs(self.resolver.identifier, self.identifier)
        self.backend.assert_not_called()
        self.assertEqual(self.backend.mock_calls, [])

    def test_exact_identifier_without_coercion(self):
        for invalid in (IdentifierSubclass("key"), Mock(value="key"), {"value": "key"},
                        "key", None):
            with self.subTest(kind=type(invalid)):
                with self.assertRaisesRegex(TypeError, "^Identifier must be an exact SecretIdentifier$"):
                    BoundSecretResolver(self.backend, invalid)
        self.assertEqual(self.backend.mock_calls, [])

    def test_constructor_only_requires_callable_get_and_never_calls_backend(self):
        class ReadOnly:
            def get(self, identifier):
                raise AssertionError("must not read")
        BoundSecretResolver(ReadOnly(), self.identifier)
        self.assertEqual(self.backend.mock_calls, [])
        for invalid in (None, object(), type("Invalid", (), {"get": 1})()):
            with self.assertRaisesRegex(TypeError, "^Backend must provide a callable get$"):
                BoundSecretResolver(invalid, self.identifier)

    def test_backend_attribute_failure_is_sanitized(self):
        class Hostile:
            @property
            def get(self):
                raise RuntimeError("synthetic-private-detail")
        try:
            BoundSecretResolver(Hostile(), self.identifier)
        except TypeError as error:
            self.assertTrue(error.__suppress_context__)
            self.assertNotIn("synthetic-private-detail", traceback.format_exc())
        else:
            self.fail("expected rejection")

    def test_get_once_exact_identifier_and_exact_result(self):
        result = self.resolver.resolve()
        self.backend.get.assert_called_once_with(self.identifier)
        self.assertIs(self.backend.get.call_args.args[0], self.identifier)
        self.assertIs(result, self.backend.get.return_value)
        self.assertEqual(self.backend.mock_calls, [("get", (self.identifier,), {})])

    def test_no_value_cache(self):
        first, second = SecretValue("synthetic-one"), SecretValue("synthetic-two")
        self.backend.get.side_effect = [first, second]
        self.assertIs(self.resolver.resolve(), first)
        self.assertIs(self.resolver.resolve(), second)
        self.assertEqual(self.backend.get.call_count, 2)
        for slot in ("_BoundSecretResolver__backend", "_BoundSecretResolver__identifier"):
            self.assertNotIsInstance(getattr(self.resolver, slot), SecretValue)

    def test_contract_errors_propagate_unchanged(self):
        for error in (SecretNotFoundError("Secret is not available"),
                      SecretStorageError("Secret storage operation failed")):
            self.backend.get.reset_mock()
            self.backend.get.side_effect = error
            with self.assertRaises(type(error)) as caught:
                self.resolver.resolve()
            self.assertIs(caught.exception, error)
            self.backend.get.assert_called_once_with(self.identifier)

    def test_unexpected_error_fixed_message_suppressed_chain(self):
        self.backend.get.side_effect = RuntimeError("synthetic-private-detail")
        try:
            self.resolver.resolve()
        except SecretStorageError as error:
            self.assertEqual(str(error), "Secret resolution failed")
            self.assertIsNone(error.__cause__)
            self.assertTrue(error.__suppress_context__)
            self.assertNotIn("synthetic-private-detail", traceback.format_exc())
        else:
            self.fail("expected sanitized failure")
        self.backend.get.assert_called_once_with(self.identifier)

    def test_wrong_result_exact_type_rejection(self):
        for invalid in (None, "synthetic-marker", {}, Mock(), ValueSubclass("synthetic")):
            self.backend.get.return_value = invalid
            with self.assertRaisesRegex(SecretStorageError, "^Secret resolution failed$"):
                self.resolver.resolve()

    def test_fixed_repr_str_identity_equality_and_hash(self):
        other = BoundSecretResolver(self.backend, self.identifier)
        for resolver in (self.resolver, other):
            self.assertEqual(str(resolver), "BoundSecretResolver(<redacted>)")
            self.assertEqual(repr(resolver), "BoundSecretResolver(<redacted>)")
        self.assertIs(BoundSecretResolver.__eq__, object.__eq__)
        self.assertIs(BoundSecretResolver.__hash__, object.__hash__)
        self.assertEqual(self.resolver, self.resolver)
        self.assertNotEqual(self.resolver, other)
        self.assertEqual(len({self.resolver, other}), 2)

    def test_ordinary_serialization_and_state_extraction_blocked(self):
        for operation in (pickle.dumps, copy.copy, copy.deepcopy):
            with self.assertRaisesRegex(TypeError, "^Secret resolver cannot be serialized$"):
                operation(self.resolver)
        for operation in (self.resolver.__getstate__, self.resolver.__reduce__):
            with self.assertRaises(TypeError):
                operation()
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.assertRaises(TypeError):
                pickle.dumps(self.resolver, protocol=protocol)

    def test_source_import_boundary(self):
        path = Path(__file__).resolve().parents[1] / "nayeon/secrets/resolver.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual(len(imports), 2)
        for node in imports:
            self.assertIsInstance(node, ast.ImportFrom)
            self.assertEqual(node.level, 0)
            self.assertIn(node.module, {"__future__", "nayeon.secrets.contracts"})
        forbidden = {"print", "open", "eval", "exec", "__import__", "put", "delete",
                     "is_available", "getenv", "environ"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.Attribute)):
                self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr, forbidden)


if __name__ == "__main__":
    unittest.main()
