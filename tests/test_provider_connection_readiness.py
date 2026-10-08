"""Phase 8.7 metadata-only readiness tests: no secret or SDK authority."""

import ast
from dataclasses import FrozenInstanceError
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import nayeon.brain.connection_readiness as m
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.secrets.contracts import SecretIdentifier


class ProviderConnectionReadinessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "connection.json"

    def config(self, provider="openai", credential="openai.api_key", model="gpt-5.6"):
        return ProviderConnectionConfiguration(
            provider=provider, model=model, credential=SecretIdentifier(credential)
        )

    def owner(self, config=None):
        store = ProviderConnectionFileStore(self.path)
        if config is not None:
            store.save(ProviderConnectionDocumentV1(connection=config))
        owner = ProviderConnectionService(store)
        owner.initialize()
        return owner

    def assess(self, owner):
        return m.assess_provider_connection_readiness(owner).status

    def test_enum_exact_stable_nonsecret_values(self):
        self.assertEqual(
            [(s.name, s.value) for s in m.ProviderConnectionReadinessStatus],
            [
                ("UNCONFIGURED", "unconfigured"),
                ("UNSUPPORTED", "unsupported"),
                ("READY_FOR_COMPOSITION", "ready_for_composition"),
            ],
        )

    def test_readiness_record_exact_status_only_and_immutable(self):
        status = m.ProviderConnectionReadinessStatus.UNCONFIGURED
        result = m.ProviderConnectionReadiness(status)
        self.assertIs(type(result), m.ProviderConnectionReadiness)
        self.assertEqual(tuple(result.__dataclass_fields__), ("status",))
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertNotIn("openai.api_key", repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.status = m.ProviderConnectionReadinessStatus.UNSUPPORTED
        for bad in (None, "unconfigured", 0, object()):
            with self.subTest(type=type(bad).__name__), self.assertRaises(TypeError):
                m.ProviderConnectionReadiness(bad)

    def test_not_configured_when_owner_initialized_without_file(self):
        owner = self.owner()
        self.assertTrue(owner.is_initialized)
        self.assertEqual(self.assess(owner), m.ProviderConnectionReadinessStatus.UNCONFIGURED)
        self.assertFalse(self.path.exists())

    def test_configured_openai_metadata_is_only_ready_for_composition(self):
        owner = self.owner(self.config())
        self.assertEqual(
            self.assess(owner), m.ProviderConnectionReadinessStatus.READY_FOR_COMPOSITION
        )
        self.assertEqual(owner.current.connection.model, "gpt-5.6")

    def test_model_text_not_reported_or_probed(self):
        owner = self.owner(self.config(model="Private Model / Synthetic"))
        result = m.assess_provider_connection_readiness(owner)
        self.assertEqual(result.status, m.ProviderConnectionReadinessStatus.READY_FOR_COMPOSITION)
        self.assertEqual(tuple(result.__dataclass_fields__), ("status",))
        self.assertNotIn("Private Model", repr(result))
        self.assertNotIn("openai.api_key", repr(result))

    def test_unsupported_provider_is_not_ready(self):
        self.assertEqual(self.assess(self.owner(self.config(provider="vendor"))),
                         m.ProviderConnectionReadinessStatus.UNSUPPORTED)

    def test_mismatched_credential_is_not_ready(self):
        self.assertEqual(self.assess(self.owner(self.config(credential="other.api_key"))),
                         m.ProviderConnectionReadinessStatus.UNSUPPORTED)

    def test_unsupported_metadata_is_not_echoed_in_status(self):
        owner = self.owner(self.config(provider="private_vendor_marker",
                                       credential="private.credential_marker",
                                       model="Private Model Marker"))
        result = m.assess_provider_connection_readiness(owner)
        self.assertEqual(result.status, m.ProviderConnectionReadinessStatus.UNSUPPORTED)
        for marker in ("private_vendor_marker", "private.credential_marker",
                       "Private Model Marker"):
            self.assertNotIn(marker, repr(result))

    def test_exact_service_type_required_without_dereference(self):
        class Hostile:
            def __getattribute__(self, name):
                raise AssertionError("Untrusted object was inspected")
        for invalid in (None, object(), Hostile()):
            with self.subTest(value=type(invalid).__name__), self.assertRaisesRegex(
                    TypeError, "exact provider connection service"):
                m.assess_provider_connection_readiness(invalid)
        derived = type("DerivedService", (ProviderConnectionService,), {})
        with self.assertRaises(TypeError):
            m.assess_provider_connection_readiness(
                derived(ProviderConnectionFileStore(self.path))
            )

    def test_uninitialized_owner_rejected_without_current_access(self):
        owner = ProviderConnectionService(ProviderConnectionFileStore(self.path))
        with mock.patch.object(ProviderConnectionService, "current",
                               new_callable=mock.PropertyMock,
                               side_effect=AssertionError("current called")) as current:
            with self.assertRaisesRegex(m.ProviderConnectionReadinessError,
                                        "^Connection owner is not initialized$"):
                m.assess_provider_connection_readiness(owner)
            current.assert_not_called()

    def test_forged_document_rejected_fail_closed(self):
        owner = self.owner()
        for value in (None, {}, self.config(), object()):
            with self.subTest(value=type(value).__name__), mock.patch.object(
                ProviderConnectionService, "current",
                new_callable=mock.PropertyMock, return_value=value,
            ):
                with self.assertRaisesRegex(m.ProviderConnectionReadinessError,
                                            "^Connection document has an invalid type$"):
                    self.assess(owner)

    def test_forged_configuration_rejected_fail_closed(self):
        owner = self.owner()
        for value in ({}, "private_marker", object()):
            connection_document = ProviderConnectionDocumentV1()
            object.__setattr__(connection_document, "connection", value)
            with self.subTest(value=type(value).__name__), mock.patch.object(
                ProviderConnectionService, "current",
                new_callable=mock.PropertyMock, return_value=connection_document,
            ):
                with self.assertRaisesRegex(m.ProviderConnectionReadinessError,
                                            "^Connection configuration has an invalid type$"):
                    self.assess(owner)

    def test_forged_identifier_is_unsupported(self):
        owner = self.owner(self.config())
        connection_document = owner.current
        conf = connection_document.connection
        object.__setattr__(conf, "credential", "openai.api_key")
        self.assertEqual(self.assess(owner), m.ProviderConnectionReadinessStatus.UNSUPPORTED)

    def test_pure_cached_assessment_no_additional_disk_or_activation(self):
        owner = self.owner(self.config())
        original = self.path.read_bytes()
        with mock.patch.object(ProviderConnectionFileStore, "load",
                               side_effect=AssertionError("unwanted load")) as load, \
             mock.patch.object(ProviderConnectionFileStore, "save",
                               side_effect=AssertionError("unwanted save")) as save:
            first = m.assess_provider_connection_readiness(owner)
            second = m.assess_provider_connection_readiness(owner)
            self.assertIsNot(first, second)
            self.assertIs(first.status, second.status)
            load.assert_not_called()
            save.assert_not_called()
        self.assertEqual(self.path.read_bytes(), original)

    def test_source_has_no_secret_probe_provider_activation_or_ambient_path(self):
        tree = ast.parse(inspect.getsource(m))
        modules = []
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                modules.append(node.module or "")
            elif isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                calls.append(node.func.attr if isinstance(node.func, ast.Attribute)
                             else node.func.id if isinstance(node.func, ast.Name) else "")
        self.assertFalse(any(name.startswith((
            "nayeon.brain.providers", "nayeon.brain.connection_composition",
            "nayeon.secrets.resolver", "nayeon.secrets.lifecycle",
            "nayeon.secrets.windows_credential", "os", "openai", "socket"
        )) for name in modules))
        for prohibited in ("get", "is_available", "resolve", "validate", "generate",
                           "put", "save", "load", "getenv", "OpenAIProvider"):
            self.assertNotIn(prohibited, calls)


if __name__ == "__main__":
    unittest.main()
