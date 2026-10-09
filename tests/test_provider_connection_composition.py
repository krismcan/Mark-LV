"""Deterministic tests for metadata-gated, lazy AI service composition."""

import ast
import inspect
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import nayeon.brain.connection_composition as composition_module
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.brain.providers.openai import OpenAIProvider
from nayeon.brain.service import AIService
from nayeon.secrets.contracts import SecretIdentifier
from nayeon.secrets.resolver import BoundSecretResolver


class HostileBackend:
    def __getattribute__(self, name):
        raise AssertionError("Backend accessed before metadata validation")


class UnreadBackend:
    def __init__(self):
        self.get_lookups = 0
        self.get_calls = 0

    def __getattribute__(self, name):
        if name == "get":
            lookups = object.__getattribute__(self, "get_lookups")
            object.__setattr__(self, "get_lookups", lookups + 1)
        if name in {"put", "delete", "is_available"}:
            raise AssertionError("Unrelated backend capability was inspected")
        return object.__getattribute__(self, name)

    def get(self, identifier):
        self.get_calls += 1
        raise AssertionError("Composition read a secret")


class ProviderConnectionCompositionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.serial = 0

    def configuration(self, provider="openai", credential=None, model="gpt-5.6"):
        if credential is None:
            credential = SecretIdentifier("openai.api_key")
        return ProviderConnectionConfiguration(
            provider=provider, model=model, credential=credential
        )

    def initialized_service(self, config=None):
        self.serial += 1
        path = self.directory / ("connection_" + str(self.serial) + ".json")
        store = ProviderConnectionFileStore(path)
        if config is not None:
            store.save(ProviderConnectionDocumentV1(connection=config))
        service = ProviderConnectionService(store)
        service.initialize()
        return service

    def raw_document(self, connection):
        document = object.__new__(ProviderConnectionDocumentV1)
        object.__setattr__(document, "schema_version", 1)
        object.__setattr__(document, "connection", connection)
        return document

    def assert_metadata_failure(self, service, message):
        with self.assertRaises(composition_module.ConnectionCompositionError) as caught:
            composition_module.compose_provider_ai_service(service, HostileBackend())
        self.assertEqual(str(caught.exception), message)

    def test_bare_metadata_and_other_inputs_are_rejected_before_access(self):
        class HostileService:
            def __getattribute__(self, name):
                raise AssertionError("Invalid service was inspected")

        values = (
            None, object(), HostileService(), self.configuration(),
            ProviderConnectionDocumentV1(connection=self.configuration()),
        )
        for value in values:
            with self.subTest(input_type=type(value).__name__):
                with self.assertRaises(TypeError) as caught:
                    composition_module.compose_provider_ai_service(value, HostileBackend())
                self.assertEqual(
                    str(caught.exception),
                    "connection_service must be an exact ProviderConnectionService",
                )

    def test_service_subclass_is_rejected_before_state_access(self):
        class DerivedService(ProviderConnectionService):
            @property
            def is_initialized(self):
                raise AssertionError("Subclass state was inspected")

        service = DerivedService(
            ProviderConnectionFileStore(self.directory / "derived.json")
        )
        with self.assertRaises(TypeError):
            composition_module.compose_provider_ai_service(service, HostileBackend())

    def test_uninitialized_service_does_not_access_current_or_backend(self):
        service = ProviderConnectionService(
            ProviderConnectionFileStore(self.directory / "uninitialized.json")
        )
        with mock.patch.object(
            ProviderConnectionService, "current", new_callable=mock.PropertyMock,
            side_effect=AssertionError("Current accessed before initialization"),
        ) as current_mock:
            self.assert_metadata_failure(service, "Connection service is not initialized")
        current_mock.assert_not_called()

    def test_unconfigured_service_does_not_access_backend(self):
        self.assert_metadata_failure(
            self.initialized_service(), "No provider connection is configured"
        )

    def test_valid_syntax_unsupported_provider_has_fixed_safe_error(self):
        service = self.initialized_service(
            self.configuration(provider="private_provider_marker")
        )
        self.assert_metadata_failure(service, "Provider is not supported")

    def test_wrong_canonical_identifier_has_fixed_safe_error(self):
        service = self.initialized_service(
            self.configuration(credential=SecretIdentifier("private.api_key"))
        )
        self.assert_metadata_failure(service, "Credential identifier is not supported")

    def test_current_requires_exact_document_shape(self):
        class DerivedDocument(ProviderConnectionDocumentV1):
            pass

        service = self.initialized_service()
        values = (
            None, self.configuration(), {"connection": self.configuration()},
            DerivedDocument(),
        )
        for value in values:
            with self.subTest(input_type=type(value).__name__):
                with mock.patch.object(
                    ProviderConnectionService, "current", new_callable=mock.PropertyMock,
                    return_value=value,
                ):
                    self.assert_metadata_failure(
                        service, "Connection document has an invalid type"
                    )

    def test_connection_requires_exact_configuration_shape(self):
        class DerivedConfiguration(ProviderConnectionConfiguration):
            pass

        derived = object.__new__(DerivedConfiguration)
        service = self.initialized_service()
        for value in (object(), "private_configuration_marker", {}, derived):
            with self.subTest(input_type=type(value).__name__):
                with mock.patch.object(
                    ProviderConnectionService, "current", new_callable=mock.PropertyMock,
                    return_value=self.raw_document(value),
                ):
                    self.assert_metadata_failure(
                        service, "Connection configuration has an invalid type"
                    )

    def test_credential_requires_exact_identifier_shape(self):
        class DerivedIdentifier(SecretIdentifier):
            pass

        derived = object.__new__(DerivedIdentifier)
        object.__setattr__(derived, "value", "openai.api_key")
        service = self.initialized_service()
        for value in (object(), "openai.api_key", derived):
            with self.subTest(input_type=type(value).__name__):
                config = self.configuration()
                object.__setattr__(config, "credential", value)
                with mock.patch.object(
                    ProviderConnectionService, "current", new_callable=mock.PropertyMock,
                    return_value=self.raw_document(config),
                ):
                    self.assert_metadata_failure(
                        service, "Credential identifier is not supported"
                    )

    def test_success_constructs_one_lazy_chain_with_trusted_identifier(self):
        config = self.configuration()
        service = self.initialized_service(config)
        persisted_config = service.current.connection
        backend = UnreadBackend()
        with (
            mock.patch.object(
                composition_module, "BoundSecretResolver", wraps=BoundSecretResolver
            ) as resolver_factory,
            mock.patch.object(
                composition_module, "OpenAIProvider", wraps=OpenAIProvider
            ) as provider_factory,
            mock.patch.object(
                composition_module, "AIService", wraps=AIService
            ) as ai_factory,
            mock.patch.object(
                ProviderConnectionFileStore, "load", autospec=True,
                side_effect=AssertionError("Unexpected persistence read"),
            ) as load_mock,
            mock.patch.object(
                ProviderConnectionFileStore, "save", autospec=True,
                side_effect=AssertionError("Unexpected persistence write"),
            ) as save_mock,
        ):
            result = composition_module.compose_provider_ai_service(service, backend)

        self.assertIs(type(result), AIService)
        resolver_factory.assert_called_once()
        passed_backend, identifier = resolver_factory.call_args.args
        self.assertIs(passed_backend, backend)
        self.assertIs(type(identifier), SecretIdentifier)
        self.assertEqual(identifier, SecretIdentifier("openai.api_key"))
        self.assertIsNot(identifier, persisted_config.credential)
        provider_factory.assert_called_once()
        resolver = provider_factory.call_args.args[0]
        self.assertIs(type(resolver), BoundSecretResolver)
        self.assertIs(resolver.identifier, identifier)
        self.assertEqual(provider_factory.call_args.kwargs, {"model": config.model})
        ai_factory.assert_called_once()
        provider = ai_factory.call_args.args[0]
        self.assertIs(type(provider), OpenAIProvider)
        self.assertEqual(provider.name, "openai")
        self.assertEqual(provider.model, config.model)
        self.assertEqual(result.provider_name, "openai")
        self.assertEqual(result.model_name, config.model)
        self.assertEqual(backend.get_lookups, 1)
        self.assertEqual(backend.get_calls, 0)
        load_mock.assert_not_called()
        save_mock.assert_not_called()

    def test_model_text_is_passed_through_exactly(self):
        model = "modèle / exact text"
        service = self.initialized_service(self.configuration(model=model))
        backend = UnreadBackend()
        result = composition_module.compose_provider_ai_service(service, backend)
        self.assertEqual(result.model_name, model)
        self.assertEqual(result.provider_name, "openai")
        self.assertEqual(backend.get_calls, 0)

    def test_repeated_compositions_have_distinct_instances_and_backends(self):
        service = self.initialized_service(self.configuration())
        first_backend = UnreadBackend()
        second_backend = UnreadBackend()
        with (
            mock.patch.object(
                composition_module, "BoundSecretResolver", wraps=BoundSecretResolver
            ) as resolver_factory,
            mock.patch.object(
                composition_module, "AIService", wraps=AIService
            ) as ai_factory,
        ):
            first = composition_module.compose_provider_ai_service(service, first_backend)
            second = composition_module.compose_provider_ai_service(service, second_backend)
        self.assertIsNot(first, second)
        self.assertEqual(resolver_factory.call_count, 2)
        self.assertIs(resolver_factory.call_args_list[0].args[0], first_backend)
        self.assertIs(resolver_factory.call_args_list[1].args[0], second_backend)
        self.assertIsNot(
            ai_factory.call_args_list[0].args[0], ai_factory.call_args_list[1].args[0]
        )
        self.assertEqual(first_backend.get_lookups, 1)
        self.assertEqual(second_backend.get_lookups, 1)
        self.assertEqual(first_backend.get_calls, 0)
        self.assertEqual(second_backend.get_calls, 0)

    def test_composition_preserves_service_document_and_persisted_bytes(self):
        service = self.initialized_service(self.configuration())
        document = service.current
        path = self.directory / "connection_1.json"
        before = path.read_bytes()
        backend = UnreadBackend()
        composition_module.compose_provider_ai_service(service, backend)
        self.assertTrue(service.is_initialized)
        self.assertIs(service.current, document)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(backend.get_calls, 0)

    def test_backend_lookup_failure_is_safely_sanitized_by_sealed_resolver(self):
        failure = RuntimeError("private_backend_error_marker")

        class FailingBackend:
            def __getattribute__(self, name):
                if name == "get":
                    raise failure
                raise AssertionError("Unexpected backend attribute access")

        service = self.initialized_service(self.configuration())
        with self.assertRaisesRegex(TypeError, "^Backend must provide a callable get$") as caught:
            composition_module.compose_provider_ai_service(service, FailingBackend())
        self.assertNotIn("private_backend_error_marker", str(caught.exception))

    def test_invalid_backend_preserves_resolver_input_error(self):
        backend = object()
        with self.assertRaises(TypeError) as direct:
            BoundSecretResolver(backend, SecretIdentifier("openai.api_key"))
        service = self.initialized_service(self.configuration())
        with self.assertRaises(TypeError) as composed:
            composition_module.compose_provider_ai_service(service, backend)
        self.assertIs(type(composed.exception), type(direct.exception))
        self.assertEqual(str(composed.exception), str(direct.exception))

    def test_source_has_no_activation_io_or_dynamic_provider_selection(self):
        tree = ast.parse(inspect.getsource(composition_module))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
        forbidden_prefixes = (
            "nayeon.config", "nayeon.presentation", "nayeon.legacy",
            "nayeon.session", "nayeon.brain.connection_persistence",
            "os", "openai", "importlib", "requests", "httpx", "socket",
        )
        for module in imported_modules:
            self.assertFalse(
                any(module == prefix or module.startswith(prefix + ".")
                    for prefix in forbidden_prefixes),
                module,
            )
        forbidden_calls = {
            "get", "put", "delete", "is_available", "resolve", "generate",
            "load", "save", "initialize", "open", "getenv", "getattr",
            "eval", "exec", "__import__", "import_module", "OpenAI", "AsyncOpenAI",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = (node.func.id if isinstance(node.func, ast.Name)
                        else node.func.attr if isinstance(node.func, ast.Attribute)
                        else None)
                self.assertNotIn(name, forbidden_calls)



class Phase86ProductionScopeGuards(unittest.TestCase):
    """Freeze 98 Phase 8.5 modules, allowing only Phase 8.6 and 8.7 additions."""

    def test_sealed_98_unchanged_and_only_two_new_production_modules(self):
        root = Path(__file__).resolve().parents[1]
        tag = "nayeon-v1-provider-connection-ownership-persistence-01"
        sealed = "d6661f6e0ac02e881056bf98c49df20618758c79"
        delta = {
            "nayeon/brain/connection_bootstrap.py",
            "nayeon/brain/connection_composition.py",
            "nayeon/brain/connection_readiness.py",
            "nayeon/brain/connection_startup.py",
            "nayeon/brain/credential_onboarding.py",
            "nayeon/brain/credential_onboarding_composition.py",
         "nayeon/brain/connection_reconciliation.py",
         "nayeon/brain/connection_recovery_advice.py",
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
        }

        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root)

        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        self.assertEqual(git("cat-file", "-t", tag).decode().strip(), "tag")
        self.assertEqual(git("rev-parse", tag + "^{commit}").decode().strip(), sealed)
        tracked = set(git("ls-tree", "-r", "--name-only", tag, "--", "nayeon")
                      .decode().splitlines())
        existing = {path for path in tracked if path.endswith(".py")}
        self.assertEqual(len(existing), 98)
        self.assertFalse(tracked & delta)

        changed = set(git("diff", "--name-only", tag, "--", "nayeon", "requirements.txt")
                      .decode().splitlines())
        untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon")
                        .decode().splitlines())
        self.assertEqual(changed | untracked, delta)
        self.assertFalse(changed & untracked)
        actual = {path.relative_to(root).as_posix()
                  for path in (root / "nayeon").rglob("*.py")}
        self.assertEqual(actual, existing | delta)
        for path in tracked | {"requirements.txt"}:
            with self.subTest(path=path):
                on_disk = (root / path).read_bytes().replace(b"\r\n", b"\n")
                original = git("show", tag + ":" + path).replace(b"\r\n", b"\n")
                self.assertEqual(on_disk, original)

if __name__ == "__main__":
    unittest.main()
