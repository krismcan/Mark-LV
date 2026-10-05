"""Phase 7.2 pure codec, privacy and bounded production dependency guards."""

import ast
from collections import UserDict
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
import unittest

from nayeon.config import document as m
from nayeon.config.presentation import (
    AssistantPresentationIdentity, UserPresentationProfile, PresentationPreferences,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "nayeon/config/document.py"


class DictSubclass(dict):
    pass


class StringSubclass(str):
    pass


class IntSubclass(int):
    pass


class HostileValue:
    def __str__(self):
        raise AssertionError("No coercion or disclosure")

    def __repr__(self):
        raise AssertionError("No coercion or disclosure")


def mapping():
    return {
        "schema_version": 1,
        "assistant": {"display_name": "Nayeon", "wake_name": "Nayeon"},
        "user": {"display_name": None},
        "preferences": {"personality_ref": None, "voice_ref": None},
    }


class PresentationDocumentTests(unittest.TestCase):
    def test_schema_shape_defaults_and_exact_annotations(self):
        self.assertIs(type(m.PRESENTATION_CONFIGURATION_SCHEMA_VERSION), int)
        self.assertEqual(m.PRESENTATION_CONFIGURATION_SCHEMA_VERSION, 1)
        contract = m.PresentationConfigurationDocumentV1
        self.assertEqual([(f.name, f.type) for f in fields(contract)], [
            ("schema_version", "int"), ("assistant", "AssistantPresentationIdentity"),
            ("user", "UserPresentationProfile"), ("preferences", "PresentationPreferences"),
        ])
        first, second = contract(), contract()
        self.assertEqual(m.presentation_configuration_document_to_mapping(first), mapping())
        for name in ("assistant", "user", "preferences"):
            self.assertIsNot(getattr(first, name), getattr(second, name))

    def test_frozen_slots_hash_equality_and_replacement(self):
        contract = m.PresentationConfigurationDocumentV1
        document = contract()
        self.assertTrue(contract.__dataclass_params__.frozen)
        self.assertFalse(contract.__dataclass_params__.repr)
        self.assertEqual(contract.__slots__, ("schema_version", "assistant", "user", "preferences"))
        self.assertFalse(hasattr(document, "__dict__"))
        self.assertEqual({document, contract()}, {document})
        for name in contract.__slots__:
            with self.assertRaises(FrozenInstanceError):
                setattr(document, name, None)
            with self.assertRaises(FrozenInstanceError):
                delattr(document, name)
        with self.assertRaises((AttributeError, TypeError)):
            document.extra = 1
        changed = replace(document, assistant=AssistantPresentationIdentity("Renamed", "Hey Renamed"))
        self.assertNotEqual(changed, document)
        self.assertEqual(document.assistant.display_name, "Nayeon")

    def test_constructor_requires_exact_composed_contracts(self):
        for name, contract in (("assistant", AssistantPresentationIdentity),
                               ("user", UserPresentationProfile),
                               ("preferences", PresentationPreferences)):
            subclass = type("Subclass", (contract,), {})
            for value in (None, {}, object(), HostileValue(), subclass()):
                with self.subTest(field=name, value_type=type(value).__name__):
                    with self.assertRaises(TypeError):
                        m.PresentationConfigurationDocumentV1(**{name: value})

    def test_version_exact_type_and_unsupported_values(self):
        for version, error in ((True, TypeError), (False, TypeError), (1.0, TypeError),
                               ("1", TypeError), (None, TypeError), (IntSubclass(1), TypeError),
                               (HostileValue(), TypeError), (0, ValueError), (-1, ValueError),
                               (2, ValueError), (10**100, ValueError)):
            with self.subTest(version_type=type(version).__name__, error=error.__name__):
                data = mapping()
                data["schema_version"] = version
                with self.assertRaises(error):
                    m.parse_presentation_configuration_document(data)
                with self.assertRaises(error):
                    m.PresentationConfigurationDocumentV1(schema_version=version)

    def test_every_section_requires_exact_dict(self):
        for section in (None, "assistant", "user", "preferences"):
            original = mapping() if section is None else mapping()[section]
            for value in (None, [], (), object(), HostileValue(), UserDict(original), DictSubclass(original)):
                data = mapping()
                if section is None:
                    data = value
                else:
                    data[section] = value
                with self.subTest(section=section, value_type=type(value).__name__):
                    with self.assertRaises(TypeError):
                        m.parse_presentation_configuration_document(data)

    def test_missing_extra_and_replaced_keys_at_every_level(self):
        marker = "PrivateUnknownKeyMarker"
        for section in (None, "assistant", "user", "preferences"):
            keys = tuple(mapping() if section is None else mapping()[section])
            for key in keys:
                for mode in ("missing", "extra", "replaced"):
                    data = mapping()
                    target = data if section is None else data[section]
                    if mode != "extra":
                        del target[key]
                    if mode != "missing":
                        target[marker] = "PrivateRejectedValueMarker"
                    with self.subTest(section=section, key=key, mode=mode):
                        with self.assertRaises(ValueError) as caught:
                            m.parse_presentation_configuration_document(data)
                        self.assertNotIn(marker, str(caught.exception))
                        self.assertNotIn("PrivateRejectedValueMarker", str(caught.exception))

    def test_non_exact_key_types_at_every_level(self):
        for section in (None, "assistant", "user", "preferences"):
            for key in (1, None, ("private",), StringSubclass("PrivateKeyMarker"), HostileValue()):
                data = mapping()
                target = data if section is None else data[section]
                target[key] = None
                with self.subTest(section=section, key_type=type(key).__name__):
                    with self.assertRaises(TypeError) as caught:
                        m.parse_presentation_configuration_document(data)
                    self.assertNotIn("PrivateKeyMarker", str(caught.exception))
            # An equal str-subclass key replacing an expected key also fails.
            data = mapping()
            target = data if section is None else data[section]
            key = next(iter(target))
            value = target.pop(key)
            target[StringSubclass(key)] = value
            with self.assertRaises(TypeError):
                m.parse_presentation_configuration_document(data)

    def test_every_leaf_rejects_wrong_types_without_coercion(self):
        for section, key in self.leaves():
            for value in (True, 1, 1.0, b"PrivateMarker", [], {}, StringSubclass("PrivateMarker"), HostileValue()):
                data = mapping()
                data[section][key] = value
                with self.subTest(section=section, key=key, value_type=type(value).__name__):
                    with self.assertRaises(TypeError) as caught:
                        m.parse_presentation_configuration_document(data)
                    self.assertNotIn("PrivateMarker", str(caught.exception))

    @staticmethod
    def leaves():
        return (("assistant", "display_name"), ("assistant", "wake_name"),
                ("user", "display_name"), ("preferences", "personality_ref"),
                ("preferences", "voice_ref"))

    def test_every_leaf_inherits_length_whitespace_and_control_validation(self):
        for section, key in self.leaves():
            maximum = 128 if section == "preferences" else 64
            values = ["", " ", "\u2003", " PrivateMarker", "PrivateMarker\u00a0", "x" * (maximum + 1)]
            values.extend("PrivateMarker" + chr(code) for code in (*range(32), 127))
            for value in values:
                data = mapping()
                data[section][key] = value
                with self.subTest(section=section, key=key, length=len(value)):
                    with self.assertRaises(ValueError) as caught:
                        m.parse_presentation_configuration_document(data)
                    self.assertNotIn("PrivateMarker", str(caught.exception))

    def test_optional_none_required_none_and_unicode_boundaries(self):
        for section, key in self.leaves():
            data = mapping()
            data[section][key] = None
            if section == "assistant":
                with self.assertRaises(TypeError):
                    m.parse_presentation_configuration_document(data)
            else:
                self.assertEqual(m.presentation_configuration_document_to_mapping(
                    m.parse_presentation_configuration_document(data)), data)
            maximum = 128 if section == "preferences" else 64
            for value in ("x", "\U0001f338" * maximum, "E\u0301", "Hey  Nayeon", "Provider:Voice/Case-v1"):
                data = mapping()
                data[section][key] = value
                encoded = m.presentation_configuration_document_to_mapping(m.parse_presentation_configuration_document(data))
                self.assertEqual(encoded, data)
                self.assertIs(encoded[section][key], value)

    def test_parser_does_not_mutate_or_retain_input_mappings(self):
        data, expected = mapping(), mapping()
        document = m.parse_presentation_configuration_document(data)
        self.assertEqual(data, expected)
        for section in ("assistant", "user", "preferences"):
            data[section].clear()
        data.clear()
        self.assertEqual(m.presentation_configuration_document_to_mapping(document), expected)

    def test_encoder_returns_fresh_canonical_mappings_and_round_trips(self):
        data = mapping()
        data["assistant"] = {"wake_name": "Hey Nova", "display_name": "Nova"}
        data["user"]["display_name"] = "Alex"
        data["preferences"] = {"voice_ref": "Voice:Case", "personality_ref": "Calm"}
        document = m.parse_presentation_configuration_document(dict(reversed(tuple(data.items()))))
        first = m.presentation_configuration_document_to_mapping(document)
        second = m.presentation_configuration_document_to_mapping(document)
        self.assertEqual(first, data)
        self.assertEqual(tuple(first), ("schema_version", "assistant", "user", "preferences"))
        self.assertEqual(tuple(first["assistant"]), ("display_name", "wake_name"))
        self.assertEqual(tuple(first["user"]), ("display_name",))
        self.assertEqual(tuple(first["preferences"]), ("personality_ref", "voice_ref"))
        self.assertIsNot(first, second)
        for section in ("assistant", "user", "preferences"):
            self.assertIs(type(first[section]), dict)
            self.assertIsNot(first[section], second[section])
            first[section].clear()
        first.clear()
        self.assertEqual(m.parse_presentation_configuration_document(second), document)
        self.assertEqual(m.presentation_configuration_document_to_mapping(document), second)

    def test_encoder_rejects_non_exact_documents(self):
        subclass = type("Subclass", (m.PresentationConfigurationDocumentV1,), {})
        for value in (None, mapping(), object(), HostileValue(), subclass()):
            with self.assertRaises(TypeError):
                m.presentation_configuration_document_to_mapping(value)

    def test_repr_does_not_disclose_configured_values(self):
        data = mapping()
        for section, key in self.leaves():
            data[section][key] = "Private" + key
        document = m.parse_presentation_configuration_document(data)
        self.assertIs(type(document).__repr__, object.__repr__)
        for section, key in self.leaves():
            self.assertNotIn(data[section][key], repr(document))


class PresentationDocumentBoundaryTests(unittest.TestCase):
    def test_imports_and_calls_are_pure_and_bounded(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports))
        self.assertEqual([(node.module, [(a.name, a.asname) for a in node.names]) for node in imports], [
            ("__future__", [("annotations", None)]),
            ("dataclasses", [("dataclass", None), ("field", None)]),
            ("nayeon.config.presentation", [("AssistantPresentationIdentity", None),
             ("UserPresentationProfile", None), ("PresentationPreferences", None)]),
        ])
        self.assertEqual({ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}, {
            "dataclass", "field", "type", "TypeError", "ValueError", "any", "len", "_validate_mapping",
            "PresentationConfigurationDocumentV1", "AssistantPresentationIdentity",
            "UserPresentationProfile", "PresentationPreferences",
        })
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.ClassDef)],
                         ["PresentationConfigurationDocumentV1"])
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.FunctionDef)],
                         ["_validate_mapping", "parse_presentation_configuration_document",
                          "presentation_configuration_document_to_mapping"])

    def test_no_other_production_consumer_of_document(self):
        targets = {"document", "nayeon.config.document", "PresentationConfigurationDocumentV1",
                   "PRESENTATION_CONFIGURATION_SCHEMA_VERSION", "parse_presentation_configuration_document",
                   "presentation_configuration_document_to_mapping"}
        for path in (ROOT / "nayeon").rglob("*.py"):
            if path == MODULE:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, targets, str(path))
                if isinstance(node, ast.alias):
                    self.assertNotIn(node.name, targets, str(path))
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, targets, str(path))
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, targets, str(path))


if __name__ == "__main__":
    unittest.main()
