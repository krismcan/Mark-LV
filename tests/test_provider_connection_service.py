"""Phase 8.5 lazy ownership, persist-before-swap and exact production scope."""

import ast
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from nayeon.brain.connection import ProviderConnectionConfiguration as Configuration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1 as Document
from nayeon.brain.connection_persistence import ProviderConnectionFileStore as Store
from nayeon.brain.connection_persistence import ProviderConnectionPersistenceError as PersistenceError
from nayeon.brain.connection_service import ProviderConnectionService as Service
from nayeon.secrets.contracts import SecretIdentifier


ROOT = Path(__file__).resolve().parents[1]
START = "35c0246362fbecc3df8532b63d42087b32b22646"
SEALED = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
DELTA = {"nayeon/brain/connection_document.py", "nayeon/brain/connection_persistence.py",
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
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py"}
NOT_INITIALIZED = "Provider connection service is not initialized"


def configuration():
    # Mismatched provider/identifier is deliberate: metadata does not authorize use.
    return Configuration("vendor", "Model Caf\u00e9", SecretIdentifier("unmapped.key"))


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class ProviderConnectionServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "connection.json"
        self.store = Store(self.path)
        self.service = Service(self.store)

    def test_constructor_exact_store_without_coercion_or_io(self):
        subclass = type("StoreSubclass", (Store,), {})
        for bad in (None, {}, self.path, object(), Mock(spec=Store), subclass(self.path)):
            with self.assertRaises(TypeError):
                Service(bad)
        with self.assertRaises(TypeError):
            Service()
        with patch.object(Store, "load", side_effect=AssertionError("No load")), \
             patch.object(Store, "save", side_effect=AssertionError("No save")), \
             patch.object(type(self.path), "open", side_effect=AssertionError("No open")):
            self.assertIs(Service(self.store).is_initialized, False)
        self.assertEqual(Service.__slots__, ("_store", "_current"))
        self.assertFalse(hasattr(self.service, "__dict__"))

    def test_uninitialized_current_and_mutations_use_fixed_error_without_io(self):
        self.assertIs(self.service.is_initialized, False)
        with patch.object(Store, "load") as load, patch.object(Store, "save") as save:
            for operation in (lambda: self.service.current, lambda: self.service.replace(configuration()),
                              lambda: self.service.replace(None), self.service.clear):
                with self.assertRaisesRegex(RuntimeError, "^" + NOT_INITIALIZED + "$"):
                    operation()
            load.assert_not_called()
            save.assert_not_called()
        for name in ("current", "is_initialized"):
            with self.assertRaises(AttributeError):
                setattr(self.service, name, None)
            with self.assertRaises(AttributeError):
                delattr(self.service, name)

    def test_missing_file_loads_once_defaults_without_save_and_caches_identity(self):
        with patch.object(Store, "load", autospec=True, return_value=None) as load, \
             patch.object(Store, "save") as save:
            first = self.service.initialize()
            self.assertIs(type(first), Document)
            self.assertIsNone(first.connection)
            self.assertEqual(first, Document())
            self.assertIs(self.service.current, first)
            self.assertIs(self.service.is_initialized, True)
            for _ in range(3):
                self.assertIs(self.service.initialize(), first)
            load.assert_called_once_with(self.store)
            save.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [])
        self.assertIsNot(Service(self.store).initialize(), first)

    def test_loaded_null_or_configured_document_cached_by_identity(self):
        for doc in (Document(), Document(connection=configuration())):
            service = Service(self.store)
            with patch.object(Store, "load", return_value=doc) as load, patch.object(Store, "save") as save:
                self.assertIs(service.initialize(), doc)
                self.assertIs(service.current, doc)
                self.assertIs(service.initialize(), doc)
                load.assert_called_once_with()
                save.assert_not_called()

    def test_load_failure_remains_uninitialized_and_retryable(self):
        error = PersistenceError("Cannot read provider connection configuration")
        doc = Document(connection=configuration())
        with patch.object(Store, "load", side_effect=[error, doc]) as load, patch.object(Store, "save") as save:
            with self.assertRaises(PersistenceError) as caught:
                self.service.initialize()
            self.assertIs(caught.exception, error)
            self.assertIs(self.service.is_initialized, False)
            with self.assertRaisesRegex(RuntimeError, "^" + NOT_INITIALIZED + "$"):
                _ = self.service.current
            self.assertIs(self.service.initialize(), doc)
            self.assertIs(self.service.initialize(), doc)
            self.assertEqual(load.call_count, 2)
            save.assert_not_called()

    def test_replace_exact_configuration_gate_precedes_save(self):
        original = self.service.initialize()
        subclass = type("ConfigurationSubclass", (Configuration,), {})
        for bad in (None, {}, Document(), object(), Mock(spec=Configuration),
                    subclass("vendor", "Model", SecretIdentifier("key"))):
            with patch.object(Store, "save") as save:
                with self.assertRaises(TypeError):
                    self.service.replace(bad)
                save.assert_not_called()
            self.assertIs(self.service.current, original)

    def test_replace_constructs_new_document_saves_once_before_swap(self):
        original = self.service.initialize()
        config = configuration()
        saved = []

        def save(store, doc):
            self.assertIs(store, self.store)
            self.assertIs(type(doc), Document)
            self.assertIs(doc.connection, config)
            self.assertIs(self.service.current, original)
            saved.append(doc)

        with patch.object(Store, "save", autospec=True, side_effect=save) as mocked:
            new = self.service.replace(config)
            mocked.assert_called_once_with(self.store, new)
        self.assertIs(new, saved[0])
        self.assertIs(self.service.current, new)
        self.assertIsNot(new, original)
        self.assertIsNone(original.connection)
        with patch.object(Store, "load", side_effect=AssertionError("No reread")):
            self.assertIs(self.service.initialize(), new)

    def test_replace_save_failure_preserves_old_identity_and_allows_retry(self):
        original = self.service.initialize()
        config = configuration()
        error = PersistenceError("Cannot save provider connection configuration")
        with patch.object(Store, "save", side_effect=[error, None]) as save:
            with self.assertRaises(PersistenceError) as caught:
                self.service.replace(config)
            self.assertIs(caught.exception, error)
            self.assertIs(self.service.current, original)
            self.assertIs(self.service.initialize(), original)
            new = self.service.replace(config)
            self.assertIs(new.connection, config)
            self.assertIs(self.service.current, new)
            self.assertEqual(save.call_count, 2)

    def test_clear_saves_new_null_each_time_before_swap_without_unlink(self):
        self.service.initialize()
        prior = self.service.replace(configuration())
        for _ in range(3):
            def save(store, doc):
                self.assertIs(self.service.current, prior)
                self.assertIsNone(doc.connection)
                self.assertIs(type(doc), Document)

            with patch.object(Store, "save", autospec=True, side_effect=save) as mocked, \
                 patch.object(type(self.path), "unlink", side_effect=AssertionError("No deletion")):
                new = self.service.clear()
                mocked.assert_called_once_with(self.store, new)
            self.assertIs(self.service.current, new)
            self.assertIsNot(new, prior)
            prior = new

    def test_clear_save_failure_preserves_old_current_identity(self):
        self.service.initialize()
        for original in (self.service.replace(configuration()), Document()):
            with patch.object(Store, "load", return_value=original):
                service = Service(self.store)
                service.initialize()
            error = PersistenceError("Cannot save provider connection configuration")
            with patch.object(Store, "save", side_effect=error) as save:
                with self.assertRaises(PersistenceError) as caught:
                    service.clear()
                self.assertIs(caught.exception, error)
                save.assert_called_once()
                self.assertIsNone(save.call_args.args[0].connection)
            self.assertIs(service.current, original)
            self.assertIs(service.initialize(), original)

    def test_real_disk_clear_persists_null_and_failed_replace_preserves_disk_and_memory(self):
        self.service.initialize()
        old = self.service.replace(configuration())
        before = self.path.read_bytes()
        with patch("nayeon.brain.connection_persistence.os.replace", side_effect=OSError("synthetic")):
            with self.assertRaises(PersistenceError):
                self.service.clear()
        self.assertIs(self.service.current, old)
        self.assertEqual(self.path.read_bytes(), before)
        cleared = self.service.clear()
        self.assertTrue(self.path.is_file())
        self.assertEqual(self.path.read_bytes(), b'{"schema_version":1,"connection":null}')
        self.assertEqual(self.store.load(), cleared)
        self.assertEqual(set(self.directory.iterdir()), {self.path})

    def test_missing_parent_init_no_creation_and_mutation_failure_no_swap(self):
        absent = self.directory / "absent" / "file.json"
        service = Service(Store(absent))
        original = service.initialize()
        self.assertIsNone(original.connection)
        for operation in (lambda: service.replace(configuration()), service.clear):
            with self.assertRaises(PersistenceError):
                operation()
            self.assertIs(service.current, original)
            self.assertFalse(absent.parent.exists())

    def test_source_exact_imports_api_and_calls_no_path_or_composition(self):
        tree = ast.parse((ROOT / "nayeon/brain/connection_service.py").read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(n, ast.ImportFrom) and n.level == 0 for n in imports))
        self.assertEqual([(n.module, [(a.name, a.asname) for a in n.names]) for n in imports], [
            ("nayeon.brain.connection", [("ProviderConnectionConfiguration", None)]),
            ("nayeon.brain.connection_document", [("ProviderConnectionDocumentV1", None)]),
            ("nayeon.brain.connection_persistence", [("ProviderConnectionFileStore", None)]),
        ])
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        self.assertEqual([n.name for n in cls.body if isinstance(n, ast.FunctionDef)],
                         ["__init__", "is_initialized", "current", "initialize", "replace", "clear"])
        self.assertEqual({ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)},
                         {"type", "TypeError", "RuntimeError", "ProviderConnectionDocumentV1",
                          "self._store.load", "self._store.save"})
        self.assertFalse(any(isinstance(n, (ast.Try, ast.Dict, ast.AsyncFunctionDef)) for n in ast.walk(tree)))
        self.assertIs(Service.__repr__, object.__repr__)


class Phase85ScopeGuards(unittest.TestCase):
    def test_checkpoint_three_new_modules_and_all_95_existing_production_files_frozen(self):
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        # The protected Phase 8.5 start must remain in HEAD ancestry across maintenance commits.
        self.assertEqual(git("merge-base", START, "HEAD").decode().strip(), START)
        self.assertEqual(git("cat-file", "-t", TAG).decode().strip(), "tag")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), SEALED)
        for checkpoint in (START, SEALED):
            tracked = set(git("ls-tree", "-r", "--name-only", checkpoint, "--", "nayeon").decode().splitlines())
            production = {p for p in tracked if p.endswith(".py")}
            self.assertEqual(len(production), 95)
            self.assertFalse(tracked & DELTA)
            changed = set(git("diff", "--name-only", checkpoint, "--", "nayeon", "requirements.txt").decode().splitlines())
            untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon").decode().splitlines())
            # Accept pre-staged, staged and committed forms of the exact delta.
            self.assertEqual(changed | untracked, DELTA)
            self.assertFalse(changed & untracked)
            actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "nayeon").rglob("*.py")}
            self.assertEqual(actual, production | DELTA)
            for path in tracked | {"requirements.txt"}:
                with self.subTest(checkpoint=checkpoint, path=path):
                    self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                     git("show", checkpoint + ":" + path).replace(b"\r\n", b"\n"))

    def test_exact_metadata_consumers_and_only_approved_composition(self):
        targets = {
            "nayeon.brain.connection": "ProviderConnectionConfiguration",
            "nayeon.brain.connection_document": "ProviderConnectionDocumentV1",
            "nayeon.brain.connection_persistence": "ProviderConnectionFileStore",
            "nayeon.brain.connection_service": "ProviderConnectionService",
        }
        consumers = {symbol: set() for symbol in targets.values()}
        for path in (ROOT / "nayeon").rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    for module, symbol in targets.items():
                        if node.module == module or symbol in {a.name for a in node.names}:
                            consumers[symbol].add(relative)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in targets:
                            consumers[targets[alias.name]].add(relative)
        self.assertEqual(consumers, {
            "ProviderConnectionConfiguration": {
                "nayeon/brain/connection_document.py", "nayeon/brain/connection_service.py",
                "nayeon/brain/connection_composition.py",
                "nayeon/brain/connection_readiness.py",
                "nayeon/brain/onboarding_metadata_document.py"},
            "ProviderConnectionDocumentV1": {
                "nayeon/brain/connection_persistence.py", "nayeon/brain/connection_service.py",
                "nayeon/brain/connection_composition.py",
                "nayeon/brain/connection_readiness.py",
                "nayeon/brain/onboarding_metadata_document.py",
                "nayeon/brain/onboarding_metadata_review.py",
                "nayeon/brain/onboarding_metadata_change_preview.py"},
            "ProviderConnectionFileStore": {
                "nayeon/brain/connection_service.py", "nayeon/brain/connection_bootstrap.py"},
            "ProviderConnectionService": {
                "nayeon/brain/connection_bootstrap.py", "nayeon/brain/connection_composition.py",
                "nayeon/brain/connection_readiness.py", "nayeon/brain/connection_startup.py"},
        })

    def test_context_setup_instructions_and_root_legacy_frozen(self):
        # The post-seal Codex handoff is mutable; instruction/script/legacy roots remain frozen.
        protected = {"AGENTS.md", "scripts/update_codex_context.py",
                     "setup.py", "main.py", "ui.py"}
        for directory in ("actions", "core", "dashboard", "plugins", "memory"):
            protected.update(git("ls-tree", "-r", "--name-only", START, "--", directory).decode().splitlines())
        for path in protected:
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                             git("show", START + ":" + path).replace(b"\r\n", b"\n"), path)


if __name__ == "__main__":
    unittest.main()
