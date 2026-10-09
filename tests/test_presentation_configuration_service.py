"""Phase 7.4 lifecycle, exact ownership, privacy and frozen scope guards."""

import ast
import json
from pathlib import Path
import subprocess
import tempfile
import traceback
import unittest
from unittest.mock import Mock, patch

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
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
}
MODULE = "nayeon/config/service.py"
BOOTSTRAP_MODULE = "nayeon/config/bootstrap.py"
VIEW_MODULE = "nayeon/config/view.py"
STARTING_HEAD = "35c0246362fbecc3df8532b63d42087b32b22646"
PRODUCT_COMMIT = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
PRIVATE = "PrivatePersonalValueMarker"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def custom_document():
    data = presentation_configuration_document_to_mapping(PresentationConfigurationDocumentV1())
    data["assistant"] = {"display_name": "\ub098\uc5f0", "wake_name": "Hey  \ub098\uc5f0"}
    data["user"]["display_name"] = PRIVATE + "E\u0301"
    data["preferences"] = {"personality_ref": "Opaque:Case/v1", "voice_ref": "Unknown:Voice/v9"}
    return parse_presentation_configuration_document(data)


class HostileValue:
    def __str__(self):
        raise AssertionError("Must not coerce")

    def __repr__(self):
        raise AssertionError("Must not disclose")


class PresentationServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "presentation.json"
        self.store = PresentationConfigurationFileStore(self.path)
        self.service = PresentationConfigurationService(self.store)

    def test_constructor_requires_exact_explicit_store_without_coercion(self):
        subclass = type("StoreSubclass", (PresentationConfigurationFileStore,), {})
        for value in (None, {}, self.path, object(), HostileValue(), subclass(self.path),
                      Mock(spec=PresentationConfigurationFileStore)):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(TypeError) as caught:
                    PresentationConfigurationService(value)
                self.assertNotIn(PRIVATE, str(caught.exception))
        with self.assertRaises(TypeError):
            PresentationConfigurationService()

    def test_constructor_does_no_io_or_store_operations(self):
        with patch.object(PresentationConfigurationFileStore, "load", side_effect=AssertionError("No load")), \
             patch.object(PresentationConfigurationFileStore, "save", side_effect=AssertionError("No save")), \
             patch.object(type(self.path), "open", side_effect=AssertionError("No open")):
            service = PresentationConfigurationService(self.store)
            self.assertIs(service.is_initialized, False)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_current_before_initialization_fails_and_properties_are_read_only(self):
        self.assertIs(self.service.is_initialized, False)
        with self.assertRaisesRegex(RuntimeError, "^Presentation configuration service is not initialized$"):
            _ = self.service.current
        for name in ("current", "is_initialized"):
            with self.assertRaises(AttributeError):
                setattr(self.service, name, PresentationConfigurationDocumentV1())
            with self.assertRaises(AttributeError):
                delattr(self.service, name)

    def test_replace_before_initialization_fails_without_save(self):
        with patch.object(PresentationConfigurationFileStore, "save") as save:
            for value in (custom_document(), HostileValue()):
                with self.assertRaises(RuntimeError):
                    self.service.replace(value)
            save.assert_not_called()
        self.assertIs(self.service.is_initialized, False)

    def test_missing_file_initializes_fresh_canonical_default_without_save(self):
        with patch.object(PresentationConfigurationFileStore, "load", autospec=True,
                          return_value=None) as load, \
             patch.object(PresentationConfigurationFileStore, "save") as save:
            first = self.service.initialize()
            load.assert_called_once_with(self.store)
            save.assert_not_called()
        self.assertIs(type(first), PresentationConfigurationDocumentV1)
        self.assertEqual(first, PresentationConfigurationDocumentV1())
        self.assertIs(self.service.current, first)
        self.assertIs(self.service.is_initialized, True)
        second = PresentationConfigurationService(self.store).initialize()
        self.assertIsNot(first, second)
        self.assertIsNot(first.assistant, second.assistant)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_missing_parent_initialization_creates_no_directory_or_file(self):
        absent = self.directory / "absent" / "presentation.json"
        service = PresentationConfigurationService(PresentationConfigurationFileStore(absent))
        self.assertEqual(service.initialize(), PresentationConfigurationDocumentV1())
        self.assertFalse(absent.exists())
        self.assertFalse(absent.parent.exists())

    def test_valid_custom_unicode_document_loads_exactly_without_writes(self):
        document = custom_document()
        self.store.save(document)
        before = self.path.read_bytes()
        real_load = PresentationConfigurationFileStore.load
        loaded = []

        def load(store):
            result = real_load(store)
            loaded.append(result)
            return result

        with patch.object(PresentationConfigurationFileStore, "load", autospec=True, side_effect=load) as mocked, \
             patch.object(PresentationConfigurationFileStore, "save", side_effect=AssertionError("No save")):
            current = self.service.initialize()
            self.assertIs(current, loaded[0])
            self.assertEqual(current, document)
            mocked.assert_called_once_with(self.store)
        self.assertEqual(self.path.read_bytes(), before)

    def test_repeated_initialization_returns_owned_document_without_reread(self):
        document = custom_document()
        with patch.object(PresentationConfigurationFileStore, "load", return_value=document) as load:
            self.assertIs(self.service.initialize(), document)
            for _ in range(3):
                self.assertIs(self.service.initialize(), document)
            load.assert_called_once_with()
        self.path.write_bytes(b"corrupt")
        self.assertIs(self.service.initialize(), document)

    def test_load_failure_leaves_uninitialized_and_retry_can_succeed(self):
        error = PresentationConfigurationPersistenceError("Cannot read presentation configuration")
        document = custom_document()
        with patch.object(PresentationConfigurationFileStore, "load", side_effect=[error, document]) as load:
            with self.assertRaises(PresentationConfigurationPersistenceError) as caught:
                self.service.initialize()
            self.assertIs(caught.exception, error)
            self.assertIs(self.service.is_initialized, False)
            with self.assertRaises(RuntimeError):
                _ = self.service.current
            self.assertIs(self.service.initialize(), document)
            self.assertIs(self.service.initialize(), document)
            self.assertEqual(load.call_count, 2)

    def test_corrupt_unsupported_and_legacy_documents_fail_closed_without_migration(self):
        unsupported = presentation_configuration_document_to_mapping(PresentationConfigurationDocumentV1())
        unsupported["schema_version"] = 2
        legacy = {"assistant_name": PRIVATE, "user_name": PRIVATE, "settings": {}}
        for raw in (b"{" + PRIVATE.encode(), json.dumps(unsupported).encode(), json.dumps(legacy).encode()):
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                service = PresentationConfigurationService(self.store)
                with patch.object(PresentationConfigurationFileStore, "save") as save:
                    with self.assertRaises(PresentationConfigurationPersistenceError) as caught:
                        service.initialize()
                    save.assert_not_called()
                self.assertIs(service.is_initialized, False)
                with self.assertRaises(RuntimeError):
                    _ = service.current
                self.assertEqual(self.path.read_bytes(), raw)
                self.assert_private(caught.exception)

    def test_replace_requires_exact_document_before_save(self):
        original = self.service.initialize()
        subclass = type("DocumentSubclass", (PresentationConfigurationDocumentV1,), {})
        with patch.object(PresentationConfigurationFileStore, "save") as save:
            for value in (None, {}, presentation_configuration_document_to_mapping(custom_document()),
                          object(), HostileValue(), subclass()):
                with self.assertRaises(TypeError) as caught:
                    self.service.replace(value)
                self.assert_private(caught.exception)
                self.assertIs(self.service.current, original)
            save.assert_not_called()

    def test_save_precedes_swap_and_success_owns_exact_argument(self):
        original = self.service.initialize()
        document = custom_document()

        def save(store, value):
            self.assertIs(store, self.store)
            self.assertIs(value, document)
            self.assertIs(self.service.current, original)
            self.assertIs(self.service.is_initialized, True)

        with patch.object(PresentationConfigurationFileStore, "save", autospec=True, side_effect=save) as mocked:
            self.assertIs(self.service.replace(document), document)
            mocked.assert_called_once_with(self.store, document)
        self.assertIs(self.service.current, document)
        with patch.object(PresentationConfigurationFileStore, "load", side_effect=AssertionError("No reread")):
            self.assertIs(self.service.initialize(), document)
        self.assertEqual(original, PresentationConfigurationDocumentV1())

    def test_failed_save_preserves_exact_previous_current_and_can_retry(self):
        original = self.service.initialize()
        document = custom_document()
        error = PresentationConfigurationPersistenceError("Cannot save presentation configuration")
        with patch.object(PresentationConfigurationFileStore, "save", side_effect=[error, None]) as save:
            with self.assertRaises(PresentationConfigurationPersistenceError) as caught:
                self.service.replace(document)
            self.assertIs(caught.exception, error)
            self.assertIs(self.service.current, original)
            self.assertIs(self.service.initialize(), original)
            self.assertIs(self.service.is_initialized, True)
            self.assertIs(self.service.replace(document), document)
            self.assertEqual(save.call_count, 2)

    def test_successful_replacement_persists_without_normalization_merge_or_mutation(self):
        original = custom_document()
        self.store.save(original)
        owned = self.service.initialize()
        before = presentation_configuration_document_to_mapping(owned)
        new = PresentationConfigurationDocumentV1()
        self.assertIs(self.service.replace(new), new)
        self.assertIs(self.service.current, new)
        self.assertEqual(self.store.load(), new)
        self.assertEqual(json.loads(self.path.read_bytes()), presentation_configuration_document_to_mapping(new))
        self.assertEqual(presentation_configuration_document_to_mapping(owned), before)
        self.assertEqual(owned, original)
        custom = custom_document()
        self.service.replace(custom)
        self.assertIs(self.service.current, custom)
        self.assertEqual(self.store.load(), custom)

    def test_real_failed_save_preserves_disk_and_memory_without_disclosing_values(self):
        self.store.save(PresentationConfigurationDocumentV1())
        original = self.service.initialize()
        before = self.path.read_bytes()
        with patch("nayeon.config.persistence.os.replace", side_effect=OSError(PRIVATE)):
            with self.assertRaises(PresentationConfigurationPersistenceError) as caught:
                self.service.replace(custom_document())
        self.assert_private(caught.exception)
        self.assertIs(self.service.current, original)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(set(self.directory.iterdir()), {self.path})

    def assert_private(self, error):
        for text in (str(error), repr(error), "".join(traceback.format_exception(error))):
            self.assertNotIn(PRIVATE, text)

    def test_service_repr_and_lifecycle_errors_do_not_disclose_values(self):
        self.assertIs(PresentationConfigurationService.__repr__, object.__repr__)
        self.store.save(custom_document())
        for operation in (lambda: self.service.current, lambda: self.service.replace(custom_document())):
            with self.assertRaises(RuntimeError) as caught:
                operation()
            self.assert_private(caught.exception)
        self.service.initialize()
        self.assertNotIn(PRIVATE, repr(self.service))
        self.assertNotIn(PRIVATE, repr(self.service.current))


class PresentationServiceBoundaryTests(unittest.TestCase):
    def test_exact_imports_api_and_calls_exclude_legacy_runtime_and_authority(self):
        tree = ast.parse((ROOT / MODULE).read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(node, ast.ImportFrom) and node.level == 0 for node in imports))
        self.assertEqual([(node.module, [(a.name, a.asname) for a in node.names]) for node in imports], [
            ("__future__", [("annotations", None)]),
            ("nayeon.config.document", [("PresentationConfigurationDocumentV1", None)]),
            ("nayeon.config.persistence", [("PresentationConfigurationFileStore", None)]),
        ])
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        self.assertEqual([node.name for node in classes], ["PresentationConfigurationService"])
        self.assertEqual([node.name for node in classes[0].body if isinstance(node, ast.FunctionDef)],
                         ["__init__", "is_initialized", "current", "initialize", "replace"])
        self.assertEqual({ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)},
                         {"type", "TypeError", "RuntimeError", "self._store.load", "self._store.save",
                          "PresentationConfigurationDocumentV1"})
        self.assertFalse(any(isinstance(node, (ast.Try, ast.Dict, ast.AsyncFunctionDef)) for node in ast.walk(tree)))

    def test_only_service_owns_persistence_and_only_bootstrap_composes_service(self):
        targets = {"persistence", "nayeon.config.persistence", "PresentationConfigurationFileStore",
                   "PresentationConfigurationPersistenceError", "MAX_PRESENTATION_CONFIGURATION_FILE_BYTES",
                   "nayeon.config.service", "PresentationConfigurationService"}
        for path in (ROOT / "nayeon").rglob("*.py"):
            # The Phase 7.5 exact-source guard bounds bootstrap to construction.
            if path in (ROOT / MODULE, ROOT / "nayeon/config/persistence.py", ROOT / BOOTSTRAP_MODULE):
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, targets, str(path))
                if isinstance(node, ast.alias):
                    self.assertNotIn(node.name, targets, str(path))
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, targets, str(path))
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, targets, str(path))

    def test_exact_starting_checkpoint_sealed_baseline_and_production_scope(self):
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        # The protected starting checkpoint remains an ancestor across seals.
        self.assertEqual(git("merge-base", STARTING_HEAD, "HEAD").decode().strip(), STARTING_HEAD)
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

    def test_protected_instructions_context_script_and_legacy_unchanged(self):
        # Codex handoff is intentionally mutable after a sealed product milestone.
        for path in ("AGENTS.md", "scripts/update_codex_context.py",
                     "nayeon/config/config.py", "nayeon/config/__init__.py"):
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                             git("show", STARTING_HEAD + ":" + path).replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
