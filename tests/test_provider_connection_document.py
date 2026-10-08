"""Phase 8.5 exact immutable metadata codec and dependency boundaries."""

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from typing import get_type_hints
import unittest
from unittest.mock import Mock

from nayeon.brain import connection_document as m
from nayeon.brain.connection import ProviderConnectionConfiguration as Configuration
from nayeon.secrets.contracts import SecretIdentifier


ROOT = Path(__file__).resolve().parents[1]


class StringSubclass(str):
    pass


class IntSubclass(int):
    pass


class DictSubclass(dict):
    pass


class ConfigurationSubclass(Configuration):
    pass


class DocumentSubclass(m.ProviderConnectionDocumentV1):
    pass


def configured_mapping():
    return {"schema_version": 1, "connection": {
        "provider": "openai", "model": "Model / Caf\u00e9 V1", "credential": "unmapped.credential",
    }}


class ProviderConnectionDocumentTests(unittest.TestCase):
    def test_exact_dataclass_fields_defaults_annotations_frozen_slots_and_repr(self):
        cls = m.ProviderConnectionDocumentV1
        self.assertTrue(is_dataclass(cls))
        self.assertTrue(cls.__dataclass_params__.frozen)
        self.assertFalse(cls.__dataclass_params__.repr)
        self.assertEqual(cls.__slots__, ("schema_version", "connection"))
        self.assertEqual(tuple(f.name for f in fields(cls)), cls.__slots__)
        self.assertEqual(tuple(f.default for f in fields(cls)), (1, None))
        self.assertEqual(get_type_hints(cls), {"schema_version": int, "connection": Configuration | None})
        self.assertIs(cls.__repr__, object.__repr__)
        for doc in (cls(), m.parse_provider_connection_document(configured_mapping())):
            self.assertFalse(hasattr(doc, "__dict__"))
            for name in cls.__slots__:
                with self.assertRaises(FrozenInstanceError):
                    setattr(doc, name, None)
                with self.assertRaises(FrozenInstanceError):
                    delattr(doc, name)
            self.assertNotIn("unmapped.credential", repr(doc))

    def test_schema_requires_exact_int_and_version_one(self):
        self.assertIs(type(m.PROVIDER_CONNECTION_SCHEMA_VERSION), int)
        self.assertEqual(m.PROVIDER_CONNECTION_SCHEMA_VERSION, 1)
        for bad in (True, False, IntSubclass(1), 1.0, "1", None, Mock()):
            with self.subTest(kind=type(bad).__name__):
                with self.assertRaises(TypeError):
                    m.ProviderConnectionDocumentV1(schema_version=bad)
                with self.assertRaises(TypeError):
                    m.parse_provider_connection_document({"schema_version": bad, "connection": None})
        for bad in (-1, 0, 2, 10**100):
            with self.assertRaises(ValueError):
                m.ProviderConnectionDocumentV1(schema_version=bad)
            with self.assertRaises(ValueError):
                m.parse_provider_connection_document({"schema_version": bad, "connection": None})

    def test_connection_requires_none_or_exact_configuration_retained_by_identity(self):
        config = Configuration("vendor", "Model", SecretIdentifier("unmapped.key"))
        doc = m.ProviderConnectionDocumentV1(connection=config)
        self.assertIs(doc.connection, config)
        self.assertIsNone(m.ProviderConnectionDocumentV1().connection)
        for bad in ({}, "key", object(), Mock(spec=Configuration),
                    ConfigurationSubclass("vendor", "Model", SecretIdentifier("key"))):
            with self.assertRaises(TypeError):
                m.ProviderConnectionDocumentV1(connection=bad)

    def test_top_level_requires_exact_dict_and_exact_string_keys(self):
        for bad in (None, [], (), "{}", Mock(), DictSubclass(configured_mapping())):
            with self.assertRaises(TypeError):
                m.parse_provider_connection_document(bad)
        for bad in ({StringSubclass("schema_version"): 1, "connection": None},
                    {"schema_version": 1, StringSubclass("connection"): None},
                    {"schema_version": 1, "connection": None, 7: None}):
            with self.assertRaises(TypeError):
                m.parse_provider_connection_document(bad)

    def test_missing_and_unknown_top_level_keys_are_rejected(self):
        valid = {"schema_version": 1, "connection": None}
        for key in valid:
            bad = dict(valid)
            del bad[key]
            with self.assertRaises(ValueError):
                m.parse_provider_connection_document(bad)
        for bad in ({}, {**valid, "extra": None}, {"version": 1, "connection": None}):
            with self.assertRaises(ValueError):
                m.parse_provider_connection_document(bad)

    def test_nested_requires_exact_dict_keys_and_no_missing_unknown_keys(self):
        for bad in ([], "key", Mock(), DictSubclass(configured_mapping()["connection"])):
            with self.assertRaises(TypeError):
                m.parse_provider_connection_document({"schema_version": 1, "connection": bad})
        nested = configured_mapping()["connection"]
        for key in nested:
            missing = dict(nested)
            del missing[key]
            with self.assertRaises(ValueError):
                m.parse_provider_connection_document({"schema_version": 1, "connection": missing})
            nonexact = {StringSubclass(k) if k == key else k: v for k, v in nested.items()}
            with self.assertRaises(TypeError):
                m.parse_provider_connection_document({"schema_version": 1, "connection": nonexact})
        for bad in ({}, {**nested, "secret": "synthetic"}, {**nested, 1: None}):
            with self.assertRaises((ValueError, TypeError)):
                m.parse_provider_connection_document({"schema_version": 1, "connection": bad})

    def test_null_and_configured_round_trip_canonical_order_and_safe_string(self):
        for raw in ({"schema_version": 1, "connection": None}, configured_mapping()):
            doc = m.parse_provider_connection_document(raw)
            self.assertIs(type(doc), m.ProviderConnectionDocumentV1)
            encoded = m.provider_connection_document_to_mapping(doc)
            self.assertIs(type(encoded), dict)
            self.assertEqual(tuple(encoded), ("schema_version", "connection"))
            self.assertEqual(encoded, raw)
            self.assertEqual(m.parse_provider_connection_document(encoded), doc)
            if doc.connection is not None:
                self.assertIs(type(doc.connection), Configuration)
                self.assertIs(type(doc.connection.credential), SecretIdentifier)
                self.assertIs(type(encoded["connection"]), dict)
                self.assertEqual(tuple(encoded["connection"]), ("provider", "model", "credential"))
                self.assertIs(type(encoded["connection"]["credential"]), str)
                self.assertEqual(encoded["connection"]["credential"], "unmapped.credential")

    def test_fresh_independent_mappings_and_no_mutable_input_retention(self):
        raw = configured_mapping()
        doc = m.parse_provider_connection_document(raw)
        self.assertEqual(raw, configured_mapping())
        first = m.provider_connection_document_to_mapping(doc)
        second = m.provider_connection_document_to_mapping(doc)
        self.assertIsNot(first, second)
        self.assertIsNot(first["connection"], second["connection"])
        first["connection"]["model"] = "Changed"
        raw["connection"].clear()
        raw.clear()
        self.assertEqual(m.provider_connection_document_to_mapping(doc), configured_mapping())
        self.assertEqual(second, configured_mapping())
        null = m.ProviderConnectionDocumentV1()
        self.assertIsNot(m.provider_connection_document_to_mapping(null), m.provider_connection_document_to_mapping(null))

    def test_encoding_requires_exact_document_without_coercion(self):
        for bad in (None, configured_mapping(), object(), Mock(spec=m.ProviderConnectionDocumentV1), DocumentSubclass()):
            with self.assertRaises(TypeError):
                m.provider_connection_document_to_mapping(bad)

    def test_invalid_raw_values_flow_through_sealed_contracts(self):
        cases = {
            "credential": (None, 1, b"key", StringSubclass("key"), SecretIdentifier("key"),
                           "", "Key", " key", "a/b", "x" * 129),
            "provider": (None, 1, b"vendor", StringSubclass("vendor"), "", "Vendor", "a/b", "x" * 65),
            "model": (None, 1, b"model", StringSubclass("model"), "", " model", "model ", "a\n", "x" * 129),
        }
        for field, values in cases.items():
            for value in values:
                raw = configured_mapping()
                raw["connection"][field] = value
                with self.subTest(field=field, kind=type(value).__name__):
                    with self.assertRaises((TypeError, ValueError)) as parsed:
                        m.parse_provider_connection_document(raw)
                    with self.assertRaises(type(parsed.exception)) as sealed:
                        if field == "credential":
                            SecretIdentifier(value)
                        else:
                            Configuration(raw["connection"]["provider"], raw["connection"]["model"],
                                          SecretIdentifier(raw["connection"]["credential"]))
                    self.assertEqual(str(parsed.exception), str(sealed.exception))

    def test_exact_source_import_and_call_boundary(self):
        tree = ast.parse((ROOT / "nayeon/brain/connection_document.py").read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(n, ast.ImportFrom) and n.level == 0 for n in imports))
        self.assertEqual([(n.module, [(a.name, a.asname) for a in n.names]) for n in imports], [
            ("dataclasses", [("dataclass", None)]),
            ("nayeon.brain.connection", [("ProviderConnectionConfiguration", None)]),
            ("nayeon.secrets.contracts", [("SecretIdentifier", None)]),
        ])
        self.assertEqual({ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)},
                         {"dataclass", "type", "TypeError", "ValueError", "any", "len", "_validate_mapping",
                          "ProviderConnectionConfiguration", "SecretIdentifier", "ProviderConnectionDocumentV1"})


if __name__ == "__main__":
    unittest.main()
