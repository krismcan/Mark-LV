"""Deterministic tests for explicit provider connection bootstrap."""

import ast
import inspect
from pathlib import Path, PurePath
import tempfile
import unittest
from unittest import mock

import nayeon.brain.connection_bootstrap as bootstrap_module
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.secrets.contracts import SecretIdentifier


class ProviderConnectionBootstrapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "connection.json"

    def configuration(self):
        return ProviderConnectionConfiguration(
            provider="openai",
            model="exact model text",
            credential=SecretIdentifier("openai.api_key"),
        )

    def test_explicit_path_is_required(self):
        with self.assertRaises(TypeError):
            bootstrap_module.bootstrap_provider_connection()

    def test_nonexact_native_paths_are_rejected(self):
        class DerivedPath(type(Path())):
            pass

        invalid_paths = (
            None,
            str(self.path),
            PurePath(self.path),
            DerivedPath(self.path),
        )
        for path in invalid_paths:
            with self.subTest(input_type=type(path).__name__):
                with self.assertRaises(TypeError):
                    bootstrap_module.bootstrap_provider_connection(path)
        self.assertFalse(self.path.exists())

    def test_missing_file_initializes_without_creating_it(self):
        service = bootstrap_module.bootstrap_provider_connection(self.path)
        self.assertIs(type(service), ProviderConnectionService)
        self.assertTrue(service.is_initialized)
        self.assertIs(type(service.current), ProviderConnectionDocumentV1)
        self.assertIsNone(service.current.connection)
        self.assertFalse(self.path.exists())

    def test_persisted_null_document_does_not_activate_a_provider(self):
        document = ProviderConnectionDocumentV1()
        ProviderConnectionFileStore(self.path).save(document)
        before = self.path.read_bytes()
        service = bootstrap_module.bootstrap_provider_connection(self.path)
        self.assertTrue(service.is_initialized)
        self.assertEqual(service.current, document)
        self.assertIsNone(service.current.connection)
        self.assertEqual(self.path.read_bytes(), before)

    def test_saved_configuration_is_loaded_without_rewriting(self):
        document = ProviderConnectionDocumentV1(connection=self.configuration())
        ProviderConnectionFileStore(self.path).save(document)
        before = self.path.read_bytes()
        service = bootstrap_module.bootstrap_provider_connection(self.path)
        self.assertEqual(service.current, document)
        self.assertIs(type(service.current.connection), ProviderConnectionConfiguration)
        self.assertEqual(service.current.connection.model, "exact model text")
        self.assertIs(service.current, service.current)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_parent_directory_is_not_created(self):
        path = self.directory / "absent" / "connection.json"
        service = bootstrap_module.bootstrap_provider_connection(path)
        self.assertTrue(service.is_initialized)
        self.assertIsNone(service.current.connection)
        self.assertFalse(path.parent.exists())

    def test_calls_return_distinct_services_and_null_documents(self):
        first = bootstrap_module.bootstrap_provider_connection(self.path)
        second = bootstrap_module.bootstrap_provider_connection(self.path)
        self.assertIsNot(first, second)
        self.assertIsNot(first.current, second.current)
        self.assertIsNone(first.current.connection)
        self.assertIsNone(second.current.connection)

    def test_construction_initialization_and_load_order(self):
        events = []
        stores = []
        services = []
        original_initialize = ProviderConnectionService.initialize

        def create_store(path):
            events.append("store")
            self.assertIs(path, self.path)
            store = ProviderConnectionFileStore(path)
            stores.append(store)
            return store

        def create_service(store):
            events.append("service")
            self.assertIs(store, stores[0])
            service = ProviderConnectionService(store)
            self.assertFalse(service.is_initialized)
            services.append(service)
            return service

        def initialize(service):
            events.append("initialize")
            self.assertIs(service, services[0])
            return original_initialize(service)

        def load(store):
            events.append("load")
            self.assertIs(store, stores[0])
            self.assertFalse(services[0].is_initialized)
            return None

        with (
            mock.patch.object(
                bootstrap_module, "ProviderConnectionFileStore", side_effect=create_store
            ) as store_factory,
            mock.patch.object(
                bootstrap_module, "ProviderConnectionService", side_effect=create_service
            ) as service_factory,
            mock.patch.object(
                ProviderConnectionService, "initialize", autospec=True,
                side_effect=initialize,
            ) as initialize_mock,
            mock.patch.object(
                ProviderConnectionFileStore, "load", autospec=True, side_effect=load
            ) as load_mock,
        ):
            result = bootstrap_module.bootstrap_provider_connection(self.path)

        self.assertEqual(events, ["store", "service", "initialize", "load"])
        self.assertIs(result, services[0])
        self.assertTrue(result.is_initialized)
        store_factory.assert_called_once_with(self.path)
        service_factory.assert_called_once_with(stores[0])
        initialize_mock.assert_called_once_with(result)
        load_mock.assert_called_once_with(stores[0])

    def test_loaded_document_identity_is_preserved_and_load_occurs_once(self):
        document = ProviderConnectionDocumentV1(connection=self.configuration())
        with mock.patch.object(
            ProviderConnectionFileStore, "load", autospec=True, return_value=document
        ) as load_mock:
            service = bootstrap_module.bootstrap_provider_connection(self.path)
            self.assertIs(service.current, document)
            self.assertIs(service.current, document)
        self.assertEqual(load_mock.call_count, 1)
        self.assertIs(type(load_mock.call_args.args[0]), ProviderConnectionFileStore)
        self.assertFalse(self.path.exists())

    def test_malformed_json_fails_without_exposing_document_contents(self):
        marker = "bootstrap_private_payload_marker"
        payload = '{"schema_version":1,"connection":{"private":"' + marker
        self.path.write_text(payload, encoding="utf-8")
        with self.assertRaises(Exception) as caught:
            bootstrap_module.bootstrap_provider_connection(self.path)
        self.assertNotIn(marker, str(caught.exception))
        self.assertNotIn(marker, repr(caught.exception))
        self.assertEqual(self.path.read_text(encoding="utf-8"), payload)

    def test_load_failure_is_propagated_without_writing(self):
        failure = RuntimeError("Connection metadata could not be loaded")
        with (
            mock.patch.object(
                ProviderConnectionFileStore, "load", autospec=True, side_effect=failure
            ) as load_mock,
            mock.patch.object(
                ProviderConnectionFileStore, "save", autospec=True,
                side_effect=AssertionError("Unexpected persistence write"),
            ) as save_mock,
        ):
            with self.assertRaises(RuntimeError) as caught:
                bootstrap_module.bootstrap_provider_connection(self.path)
        self.assertIs(caught.exception, failure)
        self.assertEqual(load_mock.call_count, 1)
        save_mock.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_source_keeps_bootstrap_explicit_and_metadata_only(self):
        tree = ast.parse(inspect.getsource(bootstrap_module))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
        forbidden_prefixes = (
            "nayeon.secrets", "nayeon.brain.providers", "nayeon.brain.service",
            "nayeon.config", "nayeon.presentation", "nayeon.legacy",
            "nayeon.session", "os", "openai",
        )
        for module in imported_modules:
            self.assertFalse(
                any(module == prefix or module.startswith(prefix + ".")
                    for prefix in forbidden_prefixes),
                module,
            )
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        function = next(node for node in functions
                        if node.name == "bootstrap_provider_connection")
        self.assertEqual([arg.arg for arg in function.args.args], ["path"])
        self.assertFalse(function.args.defaults)
        self.assertIsNone(function.args.vararg)
        self.assertIsNone(function.args.kwarg)
        forbidden_calls = {
            "getenv", "mkdir", "resolve", "generate", "save", "put", "delete",
            "is_available", "eval", "exec", "__import__",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = (node.func.id if isinstance(node.func, ast.Name)
                        else node.func.attr if isinstance(node.func, ast.Attribute)
                        else None)
                self.assertNotIn(name, forbidden_calls)


if __name__ == "__main__":
    unittest.main()
