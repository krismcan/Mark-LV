"""Phase 7.5 explicit-path composition and sealed production boundary guards."""

import ast
import inspect
import json
import os
from pathlib import Path, PurePath
import subprocess
import tempfile
import traceback
import unittest
from unittest.mock import Mock, patch

from nayeon.config import bootstrap as m
from nayeon.config.document import (
    PresentationConfigurationDocumentV1,
    parse_presentation_configuration_document,
    presentation_configuration_document_to_mapping,
)
from nayeon.config.persistence import (
    PresentationConfigurationFileStore,
    PresentationConfigurationPersistenceError,
)
from nayeon.config.service import PresentationConfigurationService


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
MODULE = "nayeon/config/bootstrap.py"
STARTING_HEAD = "35c0246362fbecc3df8532b63d42087b32b22646"
PRODUCT_COMMIT = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
VIEW_MODULE = "nayeon/config/view.py"
PRIVATE = "PrivateBootstrapValueMarker"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def mapping():
    return presentation_configuration_document_to_mapping(PresentationConfigurationDocumentV1())


class HostilePath:
    def __fspath__(self):
        raise AssertionError("No path coercion")

    def __str__(self):
        raise AssertionError("No string coercion")

    def __repr__(self):
        raise AssertionError("No disclosure")


class PresentationBootstrapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "presentation.json"

    def test_function_has_one_required_path_and_service_return_annotation(self):
        signature = inspect.signature(m.bootstrap_presentation_configuration)
        self.assertEqual(list(signature.parameters), ["path"])
        parameter = signature.parameters["path"]
        self.assertIs(parameter.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIs(parameter.default, inspect.Parameter.empty)
        self.assertEqual(parameter.annotation, "Path")
        self.assertEqual(signature.return_annotation, "PresentationConfigurationService")
        with self.assertRaises(TypeError):
            m.bootstrap_presentation_configuration()

    def test_one_store_one_service_one_initialize_in_order_and_exact_return(self):
        store, service = object(), Mock(spec=PresentationConfigurationService)
        service.initialize.return_value = object()
        events = []

        def construct_store(path):
            self.assertIs(path, self.path)
            events.append("store")
            return store

        def construct_service(argument):
            self.assertIs(argument, store)
            events.append("service")
            return service

        service.initialize.side_effect = lambda: events.append("initialize")
        with patch.object(m, "PresentationConfigurationFileStore", side_effect=construct_store) as make_store, \
             patch.object(m, "PresentationConfigurationService", side_effect=construct_service) as make_service:
            self.assertIs(m.bootstrap_presentation_configuration(self.path), service)
        make_store.assert_called_once_with(self.path)
        make_service.assert_called_once_with(store)
        service.initialize.assert_called_once_with()
        self.assertEqual(events, ["store", "service", "initialize"])

    def test_native_path_happy_path_returns_real_initialized_owner(self):
        service = m.bootstrap_presentation_configuration(path=self.path)
        self.assertIs(type(service), PresentationConfigurationService)
        self.assertTrue(service.is_initialized)
        self.assertIs(service.initialize(), service.current)
        self.assertEqual(service.current, PresentationConfigurationDocumentV1())

    def test_non_native_values_rejected_by_store_without_coercion_or_service(self):
        subclass = type("PathSubclass", (type(self.path),), {})
        for value in (str(self.path), b"file", PurePath("file"), HostilePath(),
                      subclass(self.path), None, object()):
            with self.subTest(value_type=type(value).__name__):
                with patch.object(m, "PresentationConfigurationFileStore",
                                  wraps=PresentationConfigurationFileStore) as store, \
                     patch.object(m, "PresentationConfigurationService") as service:
                    with self.assertRaisesRegex(TypeError, "^Path must be an exact native pathlib.Path$"):
                        m.bootstrap_presentation_configuration(value)
                    store.assert_called_once_with(value)
                    service.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_valid_custom_unicode_configuration_survives_exactly_without_write(self):
        data = mapping()
        data["assistant"] = {"display_name": "\ub098\uc5f0", "wake_name": "Hey  \ub098\uc5f0"}
        data["user"]["display_name"] = "E\u0301\U0001f338"
        data["preferences"] = {"personality_ref": "Opaque:Case/v1", "voice_ref": "Unknown:Voice/v9"}
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.path.write_bytes(raw)
        with patch.object(PresentationConfigurationFileStore, "save", side_effect=AssertionError("No save")):
            service = m.bootstrap_presentation_configuration(self.path)
        self.assertTrue(service.is_initialized)
        self.assertEqual(service.current, parse_presentation_configuration_document(data))
        self.assertEqual(presentation_configuration_document_to_mapping(service.current), data)
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_missing_file_owns_fresh_canonical_defaults_only_in_memory(self):
        with patch.object(PresentationConfigurationFileStore, "save", side_effect=AssertionError("No save")):
            first = m.bootstrap_presentation_configuration(self.path)
            second = m.bootstrap_presentation_configuration(self.path)
        self.assertTrue(first.is_initialized)
        self.assertTrue(second.is_initialized)
        self.assertEqual(presentation_configuration_document_to_mapping(first.current), {
            "schema_version": 1,
            "assistant": {"display_name": "Nayeon", "wake_name": "Nayeon"},
            "user": {"display_name": None},
            "preferences": {"personality_ref": None, "voice_ref": None},
        })
        self.assertIsNot(first, second)
        self.assertIsNot(first.current, second.current)
        self.assertIsNot(first.current.assistant, second.current.assistant)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_missing_parent_creates_no_directory_or_file(self):
        path = self.directory / "absent" / "nested" / "presentation.json"
        service = m.bootstrap_presentation_configuration(path)
        self.assertTrue(service.is_initialized)
        self.assertEqual(service.current, PresentationConfigurationDocumentV1())
        self.assertFalse(path.exists())
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_corrupt_malformed_unsupported_and_legacy_content_fail_closed(self):
        unsupported = mapping()
        unsupported["schema_version"] = 2
        malformed = mapping()
        malformed["user"]["display_name"] = {PRIVATE: PRIVATE}
        for raw in (b"{" + PRIVATE.encode(), b"\xff", b"[]", b"{}",
                    json.dumps(unsupported).encode(), json.dumps(malformed).encode(),
                    json.dumps({"assistant_name": PRIVATE, "settings": {}}).encode()):
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                with patch.object(PresentationConfigurationFileStore, "save") as save:
                    with self.assertRaises(PresentationConfigurationPersistenceError) as caught:
                        m.bootstrap_presentation_configuration(self.path)
                    save.assert_not_called()
                self.assertEqual(str(caught.exception), "Invalid or unreadable presentation configuration")
                self.assertNotIn(PRIVATE, "".join(traceback.format_exception(caught.exception)))
                self.assertEqual(self.path.read_bytes(), raw)
                self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_initialization_error_propagates_exactly_and_returns_no_service(self):
        error = PresentationConfigurationPersistenceError("Cannot read presentation configuration")
        constructed = []

        def construct(store):
            service = PresentationConfigurationService(store)
            constructed.append(service)
            return service

        with patch.object(m, "PresentationConfigurationService", side_effect=construct) as make_service, \
             patch.object(PresentationConfigurationFileStore, "load", side_effect=error) as load:
            with self.assertRaises(PresentationConfigurationPersistenceError) as caught:
                m.bootstrap_presentation_configuration(self.path)
        self.assertIs(caught.exception, error)
        make_service.assert_called_once()
        load.assert_called_once_with()
        self.assertFalse(constructed[0].is_initialized)

    def test_explicit_relative_path_forwarded_without_derivation_or_environment(self):
        path = Path("caller-selected") / ".." / "presentation.json"
        opened = []

        def open_missing(argument, *args, **kwargs):
            self.assertIs(argument, path)
            opened.append(argument)
            raise FileNotFoundError

        with patch.dict(os.environ, {}, clear=True), \
             patch("os.getenv", side_effect=AssertionError("No environment lookup")), \
             patch.object(Path, "cwd", side_effect=AssertionError("No cwd lookup")), \
             patch.object(type(path), "resolve", side_effect=AssertionError("No resolve")), \
             patch.object(type(path), "expanduser", side_effect=AssertionError("No expanduser")), \
             patch.object(type(path), "mkdir", side_effect=AssertionError("No mkdir")), \
             patch.object(type(path), "open", autospec=True, side_effect=open_missing):
            service = m.bootstrap_presentation_configuration(path)
        self.assertTrue(service.is_initialized)
        self.assertEqual(opened, [path])

    def test_legacy_neighbor_is_never_probed_or_used_for_missing_requested_path(self):
        legacy = self.directory / "config.json"
        raw = json.dumps({"assistant_name": PRIVATE, "user_name": PRIVATE}).encode()
        legacy.write_bytes(raw)
        real_open = type(self.path).open
        opened = []

        def open_requested(path, *args, **kwargs):
            self.assertIs(path, self.path)
            opened.append(path)
            return real_open(path, *args, **kwargs)

        with patch.object(type(self.path), "open", autospec=True, side_effect=open_requested):
            service = m.bootstrap_presentation_configuration(self.path)
        self.assertEqual(service.current, PresentationConfigurationDocumentV1())
        self.assertEqual(opened, [self.path])
        self.assertEqual(legacy.read_bytes(), raw)
        self.assertEqual(set(self.directory.iterdir()), {legacy})


class PresentationBootstrapBoundaryTests(unittest.TestCase):
    def test_exact_import_function_and_call_source_boundary(self):
        tree = ast.parse((ROOT / MODULE).read_text(encoding="utf-8"))
        self.assertIsInstance(tree.body[0], ast.Expr)
        self.assertIsInstance(tree.body[0].value, ast.Constant)
        self.assertIs(type(tree.body[0].value.value), str)
        expected = ast.parse('''
from __future__ import annotations
from pathlib import Path
from nayeon.config.persistence import PresentationConfigurationFileStore
from nayeon.config.service import PresentationConfigurationService
def bootstrap_presentation_configuration(path: Path) -> PresentationConfigurationService:
    store = PresentationConfigurationFileStore(path)
    service = PresentationConfigurationService(store)
    service.initialize()
    return service
''')
        function = tree.body[-1]
        self.assertIsInstance(function, ast.FunctionDef)
        self.assertIsInstance(function.body[0], ast.Expr)
        self.assertIsInstance(function.body[0].value, ast.Constant)
        self.assertIs(type(function.body[0].value.value), str)
        # Ignore only documentation: every executable node must match this seam.
        del tree.body[0]
        del function.body[0]
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

    def test_bootstrap_has_zero_production_consumers(self):
        self.assert_no_references({"bootstrap", "nayeon.config.bootstrap",
                                   "bootstrap_presentation_configuration"}, {MODULE})

    def test_bootstrap_is_sole_service_consumer(self):
        self.assert_no_references({"nayeon.config.service", "PresentationConfigurationService"},
                                  {MODULE, "nayeon/config/service.py"})

    def test_only_service_owns_persistence_with_exact_bootstrap_construction_exception(self):
        self.assert_no_references({"persistence", "nayeon.config.persistence", "PresentationConfigurationFileStore",
                                   "PresentationConfigurationPersistenceError", "MAX_PRESENTATION_CONFIGURATION_FILE_BYTES"},
                                  {MODULE, "nayeon/config/service.py", "nayeon/config/persistence.py"})
        # Bootstrap's full AST guard permits construction and initialize only;
        # sealed service contents below preserve exclusive load/save ownership.
        self.test_exact_import_function_and_call_source_boundary()

    def test_sealed_phase_8_1_contents_and_exact_phase_8_2_production_scope(self):
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
                    self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                     git("show", baseline + ":" + path).replace(b"\r\n", b"\n"))

    def test_protected_files_legacy_and_package_api_unchanged(self):
        # Codex handoff is intentionally mutable after a sealed product milestone.
        for path in ("AGENTS.md", "scripts/update_codex_context.py",
                     "nayeon/config/config.py", "nayeon/config/__init__.py", "nayeon/__init__.py"):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                 git("show", STARTING_HEAD + ":" + path).replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
