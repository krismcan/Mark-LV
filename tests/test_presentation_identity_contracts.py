"""Phase 7.1 deterministic contracts and protected-checkpoint source guards."""

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from pathlib import Path
import subprocess
import unittest

from nayeon.config import presentation as m


ROOT = Path(__file__).resolve().parents[1]
# Exact permitted Phase 8.5 + Phase 8.6 non-secret connection modules.
PHASE_8_5_DELTA = {
    "nayeon/brain/connection_document.py", "nayeon/brain/connection_persistence.py",
    "nayeon/brain/connection_service.py", "nayeon/brain/connection_bootstrap.py",
         "nayeon/brain/connection_composition.py", "nayeon/brain/connection_readiness.py",
         "nayeon/brain/connection_startup.py",
         "nayeon/brain/credential_onboarding.py",
         "nayeon/brain/credential_onboarding_composition.py",
         "nayeon/brain/connection_reconciliation.py",
         "nayeon/brain/connection_recovery_advice.py",
}
# Every sealed Phase 8.4 production file stays frozen.
CHECKPOINT = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
STARTING_HEAD = "35c0246362fbecc3df8532b63d42087b32b22646"
MODULE = "nayeon/config/presentation.py"
DOCUMENT_MODULE = "nayeon/config/document.py"
VIEW_MODULE = "nayeon/config/view.py"
CONTRACTS = (
    (m.AssistantPresentationIdentity, ("display_name", "wake_name")),
    (m.UserPresentationProfile, ("display_name",)),
    (m.PresentationPreferences, ("personality_ref", "voice_ref")),
)
STRING_FIELDS = tuple(
    (contract, name, 128 if name.endswith("_ref") else 64)
    for contract, names in CONTRACTS for name in names
)


class StringSubclass(str):
    pass


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


class PresentationContractTests(unittest.TestCase):
    def test_exact_field_order_annotations_and_defaults(self):
        for contract, names in CONTRACTS:
            with self.subTest(contract=contract.__name__):
                self.assertTrue(is_dataclass(contract))
                self.assertEqual(tuple(field.name for field in fields(contract)), names)
                for field in fields(contract):
                    expected_type = "str" if contract is m.AssistantPresentationIdentity else "str | None"
                    self.assertEqual(field.type, expected_type)
                    expected_default = "Nayeon" if contract is m.AssistantPresentationIdentity else None
                    self.assertEqual(field.default, expected_default)
                    self.assertEqual(getattr(contract(), field.name), expected_default)

    def test_frozen_slotted_hashable_value_semantics(self):
        for contract, names in CONTRACTS:
            with self.subTest(contract=contract.__name__):
                instance = contract()
                self.assertTrue(contract.__dataclass_params__.frozen)
                self.assertFalse(contract.__dataclass_params__.repr)
                self.assertEqual(contract.__slots__, names)
                self.assertFalse(hasattr(instance, "__dict__"))
                self.assertEqual(instance, contract())
                self.assertEqual(hash(instance), hash(contract()))
                self.assertEqual({instance, contract()}, {instance})
                for name in names:
                    with self.assertRaises(FrozenInstanceError):
                        setattr(instance, name, "Changed")
                    with self.assertRaises(FrozenInstanceError):
                        delattr(instance, name)
                with self.assertRaises((AttributeError, TypeError)):
                    instance.extra = "unallowed"
                changed = replace(instance, **{names[0]: "Changed"})
                self.assertNotEqual(instance, changed)
                self.assertNotEqual(getattr(instance, names[0]), "Changed")

    def test_valid_ascii_unicode_internal_spaces_and_exact_preservation(self):
        for contract, name, _ in STRING_FIELDS:
            for value in ("Alex", "나연", "Zoë", "E\u0301lodie", "Hey Nayeon", "A  B", "🌸", "Provider:Voice/Case_sensitive-v1"):
                with self.subTest(contract=contract.__name__, field=name, value=value):
                    self.assertIs(getattr(contract(**{name: value}), name), value)

    def test_unicode_code_point_length_boundaries(self):
        for contract, name, maximum in STRING_FIELDS:
            for value in ("x", "🌸" * maximum, "E\u0301" * (maximum // 2)):
                with self.subTest(contract=contract.__name__, field=name, length=len(value)):
                    self.assertEqual(getattr(contract(**{name: value}), name), value)

    def test_optional_none_and_required_none(self):
        for contract, name, _ in STRING_FIELDS:
            with self.subTest(contract=contract.__name__, field=name):
                if contract is m.AssistantPresentationIdentity:
                    with self.assertRaises(TypeError):
                        contract(**{name: None})
                else:
                    self.assertIsNone(getattr(contract(**{name: None}), name))

    def test_every_field_rejects_wrong_exact_type_without_coercion(self):
        class Coercible:
            def __str__(self):
                raise AssertionError("Must not coerce")

        for contract, name, _ in STRING_FIELDS:
            for value in (1, True, False, 1.5, b"PrivateTypeMarker", object(), StringSubclass("PrivateTypeMarker"), Coercible()):
                with self.subTest(contract=contract.__name__, field=name, value_type=type(value).__name__):
                    with self.assertRaises(TypeError) as caught:
                        contract(**{name: value})
                    self.assertNotIn("PrivateTypeMarker", str(caught.exception))

    def test_every_field_rejects_invalid_content_without_value_disclosure(self):
        marker = "PrivatePersonalRefMarker"
        for contract, name, maximum in STRING_FIELDS:
            values = ["", " ", "\u2003", " " + marker, marker + " ", "\u00a0" + marker,
                      marker + "\u2003", marker + "x" * maximum]
            values.extend(marker + chr(code) + "Tail" for code in (*range(32), 127))
            for value in values:
                with self.subTest(contract=contract.__name__, field=name, length=len(value)):
                    with self.assertRaises(ValueError) as caught:
                        contract(**{name: value})
                    message = str(caught.exception)
                    self.assertNotIn(marker, message)
                    if value.strip():
                        self.assertNotIn(value, message)

    def test_repr_inherits_object_repr_and_never_serializes_fields(self):
        for contract, names in CONTRACTS:
            values = {name: "PrivateConfigured" + name for name in names}
            instance = contract(**values)
            representation = repr(instance)
            self.assertIs(contract.__repr__, object.__repr__)
            self.assertNotIn("__repr__", contract.__dict__)
            for name, value in values.items():
                self.assertNotIn(value, representation)
                self.assertNotIn(name + "=", representation)


class PresentationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / MODULE).read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_only_dataclasses_and_future_imports(self):
        imports = [node for node in ast.walk(self.tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual(len(imports), 2)
        for node in imports:
            self.assertIsInstance(node, ast.ImportFrom)
            self.assertEqual(node.level, 0)
            self.assertIn(node.module, {"dataclasses", "__future__"})
            expected = "dataclass" if node.module == "dataclasses" else "annotations"
            self.assertEqual([(alias.name, alias.asname) for alias in node.names], [(expected, None)])

    def test_exact_public_contracts_decorators_and_no_extra_methods(self):
        classes = [node for node in self.tree.body if isinstance(node, ast.ClassDef)]
        self.assertEqual([node.name for node in classes], [contract.__name__ for contract, _ in CONTRACTS])
        for node in classes:
            self.assertEqual([ast.unparse(decorator) for decorator in node.decorator_list],
                             ["dataclass(frozen=True, slots=True, repr=False)"])
            self.assertEqual([item.name for item in node.body if isinstance(item, ast.FunctionDef)],
                             ["__post_init__"])
        helpers = [node.name for node in self.tree.body if isinstance(node, ast.FunctionDef)]
        self.assertEqual(helpers, ["_validate_string", "_validate_optional_string"])

    def test_no_io_environment_dynamic_import_or_authority_operations(self):
        # Allow only the pure validation calls present in this contract; imports
        # and exact class/method shape are guarded separately.
        calls = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                calls.add(ast.unparse(node.func))
            if isinstance(node, (ast.Dict, ast.List, ast.Set, ast.DictComp, ast.ListComp, ast.SetComp)):
                self.fail("Mutable collection in presentation contract")
            if isinstance(node, ast.Name):
                self.assertNotEqual(node.id, "Any")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for forbidden in ("permission", "policy", "authorize", "execute", "capability", "secret"):
                    self.assertNotIn(forbidden, node.name.lower())
        self.assertEqual(calls, {"dataclass", "type", "len", "value.strip", "any", "ord",
                                 "TypeError", "ValueError", "_validate_string", "_validate_optional_string"})

    def test_only_approved_document_and_view_consumers_reference_presentation(self):
        targets = {"AssistantPresentationIdentity", "UserPresentationProfile", "PresentationPreferences",
                   "presentation", "nayeon.config.presentation"}
        for path in (ROOT / "nayeon").rglob("*.py"):
            if path in (ROOT / MODULE, ROOT / DOCUMENT_MODULE, ROOT / VIEW_MODULE):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "nayeon.config.presentation", str(path))
                if isinstance(node, ast.alias):
                    self.assertNotIn(node.name, targets, str(path))
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, targets, str(path))
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, targets, str(path))

    def test_protected_checkpoint_branch_tag_and_exact_production_scope(self):
        # The protected starting checkpoint remains an ancestor across seals.
        self.assertEqual(git("merge-base", STARTING_HEAD, "HEAD").decode().strip(), STARTING_HEAD)
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), CHECKPOINT)
        changed = set(git("diff", "--name-only", CHECKPOINT, "--", "nayeon").decode().splitlines())
        untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon").decode().splitlines())
        self.assertEqual(changed | untracked, PHASE_8_5_DELTA)
        self.assertEqual(changed - PHASE_8_5_DELTA, set())
        self.assertEqual(untracked - PHASE_8_5_DELTA, set())
        # Explicit content comparison defeats Git filters/assume-unchanged flags.
        # Only ordinary checkout newline conversion is allowed.
        tracked = git("ls-tree", "-r", "--name-only", CHECKPOINT, "--", "nayeon").decode().splitlines()
        actual_sources = {path.relative_to(ROOT).as_posix() for path in (ROOT / "nayeon").rglob("*.py")}
        self.assertEqual(actual_sources, {path for path in tracked if path.endswith(".py")} | PHASE_8_5_DELTA)
        for path in tracked:
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                 git("show", CHECKPOINT + ":" + path).replace(b"\r\n", b"\n"))

    def test_legacy_config_and_package_api_untouched(self):
        for path in ("nayeon/config/config.py", "nayeon/config/__init__.py"):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                 git("show", CHECKPOINT + ":" + path).replace(b"\r\n", b"\n"))
        self.assertNotIn("Kris", self.source)
        for excluded in ("wake_word_enabled", "morning_briefing_enabled", "proactive_enabled", "settings"):
            self.assertNotIn(excluded, self.source)


if __name__ == "__main__":
    unittest.main()
