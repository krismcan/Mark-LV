"""Phase 7.6 pure read-model behavior and sealed foundation boundaries."""

import ast
from dataclasses import FrozenInstanceError, MISSING, fields, is_dataclass
import inspect
from pathlib import Path
import subprocess
import unittest
from typing import get_type_hints

from nayeon.config import view as m
from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.config.presentation import (
    AssistantPresentationIdentity,
    UserPresentationProfile,
    PresentationPreferences,
)


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
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
         "nayeon/brain/onboarding_metadata_document.py",
         "nayeon/brain/onboarding_metadata_review.py",
         "nayeon/brain/onboarding_metadata_change_preview.py",
         "nayeon/brain/onboarding_operation_advice.py",
         "nayeon/brain/onboarding_review_session.py",
         "nayeon/brain/credential_operation_host.py",
         "nayeon/brain/first_run_summary.py",
         "nayeon/brain/first_run_refresh.py",
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py",
         "nayeon/desktop_alpha/notepad.py",
}
MODULE = "nayeon/config/view.py"
STARTING_HEAD = "35c0246362fbecc3df8532b63d42087b32b22646"
PRODUCT_COMMIT = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
CONTRACTS = (
    ("assistant", AssistantPresentationIdentity),
    ("user", UserPresentationProfile),
    ("preferences", PresentationPreferences),
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def custom_document():
    return PresentationConfigurationDocumentV1(
        assistant=AssistantPresentationIdentity("\ub098\uc5f0\U0001f338", "Hey  \ub098\uc5f0"),
        user=UserPresentationProfile("E\u0301lodie\u00a0\u212b"),
        preferences=PresentationPreferences("Opaque:Case/\u00e9", "Unknown:Voice/E\u0301"),
    )


class HostileValue:
    def __getattr__(self, name):
        raise AssertionError("No duck typing or attribute access")

    def __str__(self):
        raise AssertionError("No coercion")

    def __repr__(self):
        raise AssertionError("No value disclosure")


class PresentationViewTests(unittest.TestCase):
    def test_exact_dataclass_fields_order_types_and_required_arguments(self):
        contract = m.PresentationConfigurationView
        self.assertTrue(is_dataclass(contract))
        self.assertEqual(tuple(field.name for field in fields(contract)), tuple(name for name, _ in CONTRACTS))
        self.assertEqual(get_type_hints(contract), dict(CONTRACTS))
        for field, (_, expected) in zip(fields(contract), CONTRACTS):
            self.assertEqual(field.type, expected.__name__)
            self.assertIs(field.default, MISSING)
            self.assertIs(field.default_factory, MISSING)
        with self.assertRaises(TypeError):
            contract()

    def test_frozen_slots_repr_false_and_value_semantics(self):
        contract = m.PresentationConfigurationView
        view = m.presentation_configuration_view(custom_document())
        self.assertTrue(contract.__dataclass_params__.frozen)
        self.assertFalse(contract.__dataclass_params__.repr)
        self.assertEqual(contract.__slots__, ("assistant", "user", "preferences"))
        self.assertFalse(hasattr(view, "__dict__"))
        other = m.presentation_configuration_view(custom_document())
        self.assertEqual(view, other)
        self.assertEqual(hash(view), hash(other))
        for name, expected in CONTRACTS:
            with self.assertRaises(FrozenInstanceError):
                setattr(view, name, expected())
            with self.assertRaises(FrozenInstanceError):
                delattr(view, name)
        with self.assertRaises((AttributeError, TypeError)):
            view.extra = object()

    def test_exact_field_types_reject_subclasses_ducks_mappings_without_coercion(self):
        valid = {name: expected() for name, expected in CONTRACTS}
        for name, expected in CONTRACTS:
            subclass = type("Subclass", (expected,), {})
            duck = type("Duck", (), {field.name: getattr(expected(), field.name) for field in fields(expected)})()
            wrong_contracts = tuple(value for value in valid.values() if type(value) is not expected)
            for value in (subclass(), duck, HostileValue(), {}, None, object(), "value", 1, *wrong_contracts):
                with self.subTest(field=name, value_type=type(value).__name__):
                    arguments = dict(valid, **{name: value})
                    with self.assertRaises(TypeError):
                        m.PresentationConfigurationView(**arguments)

    def test_constructor_accepts_only_the_three_contract_values(self):
        values = {name: expected() for name, expected in CONTRACTS}
        view = m.PresentationConfigurationView(**values)
        for name, value in values.items():
            self.assertIs(getattr(view, name), value)
        for extra in ("schema_version", "path", "store", "service", "bootstrap", "document"):
            with self.assertRaises(TypeError):
                m.PresentationConfigurationView(**values, **{extra: object()})

    def test_exact_projector_signature_and_annotations(self):
        signature = inspect.signature(m.presentation_configuration_view)
        self.assertEqual(list(signature.parameters), ["document"])
        parameter = signature.parameters["document"]
        self.assertIs(parameter.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIs(parameter.default, inspect.Parameter.empty)
        self.assertEqual(parameter.annotation, "PresentationConfigurationDocumentV1")
        self.assertEqual(signature.return_annotation, "PresentationConfigurationView")
        self.assertEqual(get_type_hints(m.presentation_configuration_view), {
            "document": PresentationConfigurationDocumentV1,
            "return": m.PresentationConfigurationView,
        })
        with self.assertRaises(TypeError):
            m.presentation_configuration_view()

    def test_projector_requires_exact_document_without_duck_typing_or_coercion(self):
        subclass = type("Subclass", (PresentationConfigurationDocumentV1,), {})
        document = PresentationConfigurationDocumentV1()
        duck = type("Duck", (), {field.name: getattr(document, field.name) for field in fields(document)})()
        for value in (subclass(), duck, HostileValue(), {}, None, object(), "document", 1):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaisesRegex(TypeError, "^Document must be an exact presentation configuration document$"):
                    m.presentation_configuration_view(value)

    def test_each_projection_has_fresh_view_and_fresh_exact_nested_values(self):
        document = custom_document()
        first = m.presentation_configuration_view(document)
        second = m.presentation_configuration_view(document=document)
        self.assertIs(type(first), m.PresentationConfigurationView)
        self.assertIs(type(second), m.PresentationConfigurationView)
        self.assertIsNot(first, second)
        self.assertEqual(first, second)
        for name, expected in CONTRACTS:
            with self.subTest(field=name):
                self.assertIs(type(getattr(first, name)), expected)
                self.assertIs(type(getattr(second, name)), expected)
                self.assertIsNot(getattr(first, name), getattr(document, name))
                self.assertIsNot(getattr(second, name), getattr(document, name))
                self.assertIsNot(getattr(first, name), getattr(second, name))
                self.assertEqual(getattr(first, name), getattr(document, name))

    def test_unicode_values_preserved_exactly_without_normalization_or_lookup(self):
        view = m.presentation_configuration_view(custom_document())
        self.assertEqual(view.assistant.display_name, "\ub098\uc5f0\U0001f338")
        self.assertEqual(view.assistant.wake_name, "Hey  \ub098\uc5f0")
        self.assertEqual(view.user.display_name, "E\u0301lodie\u00a0\u212b")
        self.assertEqual(view.preferences.personality_ref, "Opaque:Case/\u00e9")
        self.assertEqual(view.preferences.voice_ref, "Unknown:Voice/E\u0301")

    def test_defaults_project_exactly(self):
        view = m.presentation_configuration_view(PresentationConfigurationDocumentV1())
        self.assertEqual(view.assistant, AssistantPresentationIdentity())
        self.assertEqual(view.user, UserPresentationProfile())
        self.assertEqual(view.preferences, PresentationPreferences())
        self.assertEqual((view.assistant.display_name, view.assistant.wake_name), ("Nayeon", "Nayeon"))
        self.assertIsNone(view.user.display_name)
        self.assertIsNone(view.preferences.personality_ref)
        self.assertIsNone(view.preferences.voice_ref)

    def test_projection_does_not_mutate_source_document_or_nested_values(self):
        document = custom_document()
        original = tuple(getattr(document, field.name) for field in fields(document))
        snapshot = custom_document()
        for _ in range(3):
            m.presentation_configuration_view(document)
        self.assertEqual(document, snapshot)
        for field, value in zip(fields(document), original):
            self.assertIs(getattr(document, field.name), value)

    def test_no_owner_metadata_write_methods_or_retained_document(self):
        document = custom_document()
        view = m.presentation_configuration_view(document)
        self.assertEqual({name for name in dir(view) if not name.startswith("_")},
                         {name for name, _ in CONTRACTS})
        for value in (view, view.assistant, view.user, view.preferences):
            self.assertFalse(hasattr(value, "__dict__"))
            for name in ("schema_version", "path", "_path", "store", "_store", "service", "bootstrap",
                         "document", "current", "replace", "save", "load", "write", "initialize"):
                self.assertFalse(hasattr(value, name), name)
            for field in fields(value):
                self.assertIsNot(getattr(value, field.name), document)

    def test_repr_does_not_disclose_any_presentation_value(self):
        document = custom_document()
        view = m.presentation_configuration_view(document)
        self.assertIs(m.PresentationConfigurationView.__repr__, object.__repr__)
        self.assertNotIn("__repr__", m.PresentationConfigurationView.__dict__)
        for name, _ in CONTRACTS:
            self.assertNotIn(name + "=", repr(view))
            for field in fields(getattr(document, name)):
                self.assertNotIn(getattr(getattr(document, name), field.name), repr(view))


class PresentationViewBoundaryTests(unittest.TestCase):
    def test_exact_imports_and_all_executable_source_nodes(self):
        tree = ast.parse((ROOT / MODULE).read_text(encoding="utf-8"))
        expected = ast.parse('''
from __future__ import annotations
from dataclasses import dataclass
from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.config.presentation import (
    AssistantPresentationIdentity, UserPresentationProfile, PresentationPreferences,
)
@dataclass(frozen=True, slots=True, repr=False)
class PresentationConfigurationView:
    assistant: AssistantPresentationIdentity
    user: UserPresentationProfile
    preferences: PresentationPreferences
    def __post_init__(self) -> None:
        if type(self.assistant) is not AssistantPresentationIdentity:
            raise TypeError("Assistant must be an exact presentation identity")
        if type(self.user) is not UserPresentationProfile:
            raise TypeError("User must be an exact presentation profile")
        if type(self.preferences) is not PresentationPreferences:
            raise TypeError("Preferences must be exact presentation preferences")
def presentation_configuration_view(
    document: PresentationConfigurationDocumentV1,
) -> PresentationConfigurationView:
    if type(document) is not PresentationConfigurationDocumentV1:
        raise TypeError("Document must be an exact presentation configuration document")
    return PresentationConfigurationView(
        assistant=AssistantPresentationIdentity(
            display_name=document.assistant.display_name,
            wake_name=document.assistant.wake_name,
        ),
        user=UserPresentationProfile(display_name=document.user.display_name),
        preferences=PresentationPreferences(
            personality_ref=document.preferences.personality_ref,
            voice_ref=document.preferences.voice_ref,
        ),
    )
''')
        # Ignore documentation only; all executable nodes, imports, calls,
        # attributes and globals must match the approved pure projector.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    self.assertIs(type(node.body[0].value.value), str)
                    del node.body[0]
        self.assertEqual(ast.dump(tree), ast.dump(expected))

    def assert_no_references(self, targets, allowed):
        for path in (ROOT / "nayeon").rglob("*.py"):
            if path.relative_to(ROOT).as_posix() in allowed:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, targets, str(path))
                    if node.module == "nayeon.config":
                        for alias in node.names:
                            self.assertNotIn("nayeon.config." + alias.name, targets, str(path))
                if isinstance(node, ast.alias):
                    self.assertNotIn(node.name, targets, str(path))
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, targets, str(path))
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, targets, str(path))

    def test_view_has_zero_production_consumers(self):
        self.assert_no_references({"view", "nayeon.config.view", "PresentationConfigurationView",
                                   "presentation_configuration_view"}, {MODULE})

    def test_view_is_only_new_document_and_presentation_consumer(self):
        self.assert_no_references({"nayeon.config.document", "PresentationConfigurationDocumentV1",
                                   "PRESENTATION_CONFIGURATION_SCHEMA_VERSION", "parse_presentation_configuration_document",
                                   "presentation_configuration_document_to_mapping"},
                                  {MODULE, "nayeon/config/document.py", "nayeon/config/persistence.py",
                                   "nayeon/config/service.py"})
        # `document` alone is a generic local name, not presentation authority.
        # Permit that lexical name only in the approved connection-document stack
        # while still scanning those modules above for every presentation-specific
        # import/type/function identifier.
        self.assert_no_references({"document"},
                                  {MODULE, "nayeon/config/document.py", "nayeon/config/persistence.py",
                                   "nayeon/config/service.py", "nayeon/brain/connection_document.py",
                                   "nayeon/brain/connection_persistence.py", "nayeon/brain/connection_service.py"})
        self.assert_no_references({"presentation", "nayeon.config.presentation", "AssistantPresentationIdentity",
                                   "UserPresentationProfile", "PresentationPreferences"},
                                  {MODULE, "nayeon/config/presentation.py", "nayeon/config/document.py"})

    def test_bootstrap_still_has_zero_production_consumers(self):
        self.assert_no_references({"bootstrap", "nayeon.config.bootstrap", "bootstrap_presentation_configuration"},
                                  {"nayeon/config/bootstrap.py"})

    def test_service_and_persistence_consumer_ownership_boundaries_unchanged(self):
        self.assert_no_references({"nayeon.config.service", "PresentationConfigurationService"},
                                  {"nayeon/config/service.py", "nayeon/config/bootstrap.py"})
        self.assert_no_references({"persistence", "nayeon.config.persistence", "PresentationConfigurationFileStore",
                                   "PresentationConfigurationPersistenceError", "MAX_PRESENTATION_CONFIGURATION_FILE_BYTES"},
                                  {"nayeon/config/persistence.py", "nayeon/config/service.py", "nayeon/config/bootstrap.py"})
        # Byte-frozen service and bootstrap retain exclusive load/save ownership
        # and the approved store-construction exception, respectively.
        for path in ("nayeon/config/service.py", "nayeon/config/bootstrap.py"):
            self.assert_content_matches(path, PRODUCT_COMMIT)

    def assert_content_matches(self, path, baseline):
        self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                         git("show", baseline + ":" + path).replace(b"\r\n", b"\n"))

    def test_starting_checkpoint_sealed_contents_and_exact_production_scope(self):
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        # The protected starting checkpoint remains an ancestor across seals.
        self.assertEqual(git("merge-base", STARTING_HEAD, "HEAD").decode().strip(), STARTING_HEAD)
        self.assertEqual(git("cat-file", "-t", TAG).decode().strip(), "tag")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), PRODUCT_COMMIT)
        for baseline in (STARTING_HEAD, PRODUCT_COMMIT):
            changed = set(git("diff", "--name-only", baseline, "--", "nayeon").decode().splitlines())
            untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon").decode().splitlines())
            self.assertEqual(changed | untracked, PHASE_8_5_DELTA)
            tracked = git("ls-tree", "-r", "--name-only", baseline, "--", "nayeon").decode().splitlines()
            actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / "nayeon").rglob("*.py")}
            self.assertEqual(actual, {path for path in tracked if path.endswith(".py")} | PHASE_8_5_DELTA)
            for path in tracked:
                with self.subTest(baseline=baseline, path=path):
                    self.assert_content_matches(path, baseline)

    def test_protected_files_legacy_root_and_package_apis_unchanged(self):
        # Codex handoff is intentionally mutable after a sealed product milestone.
        for path in ("AGENTS.md", "scripts/update_codex_context.py",
                     "nayeon/config/config.py", "nayeon/config/__init__.py", "nayeon/__init__.py",
                     "main.py", "ui.py"):
            with self.subTest(path=path):
                self.assert_content_matches(path, STARTING_HEAD)
        for directory in ("actions", "core", "dashboard", "plugins", "memory"):
            for path in git("ls-tree", "-r", "--name-only", STARTING_HEAD, "--", directory).decode().splitlines():
                with self.subTest(path=path):
                    self.assert_content_matches(path, STARTING_HEAD)

    def test_ai_semantic_model_and_internal_intent_prompt_unchanged_without_view_dependency(self):
        found = []
        for path in (ROOT / "nayeon").rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            if any(isinstance(node, ast.ClassDef) and node.name == "AISemanticModel" for node in ast.walk(tree)):
                found.append(path)
                self.assert_content_matches(path.relative_to(ROOT).as_posix(), STARTING_HEAD)
                self.assertNotIn("PresentationConfigurationView", source)
                self.assertNotIn("presentation_configuration_view", source)
                self.assertNotIn("nayeon.config.view", source)
                self.assertTrue(any(isinstance(node, ast.Constant) and isinstance(node.value, str)
                                    and node.value.startswith("You are Nayeon's semantic intent interpreter. ")
                                    for node in ast.walk(tree)))
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
