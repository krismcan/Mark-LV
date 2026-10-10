"""Phase 8.7 explicit-path startup tests and sealed-production guard."""

import ast
from dataclasses import FrozenInstanceError
import inspect
from pathlib import Path, PurePath
import subprocess
import tempfile
import unittest
from unittest import mock

import nayeon.brain.connection_startup as m
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import (
    ProviderConnectionFileStore, ProviderConnectionPersistenceError,
)
from nayeon.brain.connection_readiness import (
    ProviderConnectionReadiness, ProviderConnectionReadinessStatus,
    ProviderConnectionReadinessError,
)
from nayeon.brain.connection_service import ProviderConnectionService
from nayeon.secrets.contracts import SecretIdentifier


class ProviderConnectionStartupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "connection.json"

    def configure(self, provider="openai", credential="openai.api_key"):
        conf = ProviderConnectionConfiguration(
            provider=provider, model="gpt-5.6",
            credential=SecretIdentifier(credential),
        )
        ProviderConnectionFileStore(self.path).save(
            ProviderConnectionDocumentV1(connection=conf)
        )

    def test_explicit_path_only_and_exact_sealed_native_path(self):
        with self.assertRaises(TypeError):
            m.startup_provider_connection()
        class DerivedPath(type(Path())):
            pass
        for invalid in (None, str(self.path), PurePath(self.path),
                        DerivedPath(self.path), object()):
            with self.subTest(value=type(invalid).__name__), self.assertRaises(TypeError):
                m.startup_provider_connection(invalid)

    def test_fresh_startup_is_unconfigured_and_does_not_write(self):
        result = m.startup_provider_connection(self.path)
        self.assertIs(type(result), m.ProviderConnectionStartupResult)
        self.assertIs(type(result.owner), ProviderConnectionService)
        self.assertTrue(result.owner.is_initialized)
        self.assertIsNone(result.owner.current.connection)
        self.assertEqual(result.readiness.status, ProviderConnectionReadinessStatus.UNCONFIGURED)
        self.assertFalse(self.path.exists())

    def test_configured_openai_status_is_only_metadata_ready(self):
        self.configure()
        before = self.path.read_bytes()
        result = m.startup_provider_connection(self.path)
        self.assertEqual(result.readiness.status,
                         ProviderConnectionReadinessStatus.READY_FOR_COMPOSITION)
        self.assertEqual(result.owner.current.connection.model, "gpt-5.6")
        self.assertEqual(self.path.read_bytes(), before)

    def test_unsupported_provider_startup(self):
        self.configure(provider="other_vendor")
        result = m.startup_provider_connection(self.path)
        self.assertEqual(result.readiness.status, ProviderConnectionReadinessStatus.UNSUPPORTED)

    def test_wrong_credential_startup(self):
        self.configure(credential="other.secret")
        result = m.startup_provider_connection(self.path)
        self.assertEqual(result.readiness.status, ProviderConnectionReadinessStatus.UNSUPPORTED)

    def test_repeat_startup_returns_distinct_owners_and_results(self):
        self.configure()
        first = m.startup_provider_connection(self.path)
        second = m.startup_provider_connection(self.path)
        self.assertIsNot(first, second)
        self.assertIsNot(first.owner, second.owner)
        self.assertIsNot(first.readiness, second.readiness)
        self.assertEqual(first.owner.current, second.owner.current)
        self.assertEqual(first.readiness.status, second.readiness.status)

    def test_result_exact_types_frozen_and_no_secret_retention(self):
        owner = ProviderConnectionService(ProviderConnectionFileStore(self.path))
        owner.initialize()
        readiness = ProviderConnectionReadiness(ProviderConnectionReadinessStatus.UNCONFIGURED)
        result = m.ProviderConnectionStartupResult(owner, readiness)
        self.assertEqual(tuple(result.__dataclass_fields__), ("owner", "readiness"))
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertIs(result.owner, owner)
        self.assertIs(result.readiness, readiness)
        self.assertNotIn("openai.api_key", repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.owner = None
        for bad in (None, object(), {}) :
            with self.subTest(value=type(bad).__name__), self.assertRaises(TypeError):
                m.ProviderConnectionStartupResult(bad, readiness)
        for bad in (None, "unconfigured", object()):
            with self.subTest(value=type(bad).__name__), self.assertRaises(TypeError):
                m.ProviderConnectionStartupResult(owner, bad)

    def test_bootstrap_then_assess_exactly_once_in_order(self):
        owner = ProviderConnectionService(ProviderConnectionFileStore(self.path))
        owner.initialize()
        readiness = ProviderConnectionReadiness(ProviderConnectionReadinessStatus.UNCONFIGURED)
        order = []
        def bootstrap(path):
            order.append(("bootstrap", path))
            return owner
        def assess(value):
            order.append(("assess", value))
            return readiness
        with mock.patch.object(m, "bootstrap_provider_connection",
                               side_effect=bootstrap) as bootstrap_mock, \
             mock.patch.object(m, "assess_provider_connection_readiness",
                               side_effect=assess) as assess_mock:
            result = m.startup_provider_connection(self.path)
        self.assertEqual(order, [("bootstrap", self.path), ("assess", owner)])
        bootstrap_mock.assert_called_once_with(self.path)
        assess_mock.assert_called_once_with(owner)
        self.assertIs(result.owner, owner)
        self.assertIs(result.readiness, readiness)

    def test_failed_bootstrap_stops_before_readiness(self):
        error = ProviderConnectionPersistenceError("Cannot read provider connection configuration")
        with mock.patch.object(m, "bootstrap_provider_connection", side_effect=error), \
             mock.patch.object(m, "assess_provider_connection_readiness") as assess:
            with self.assertRaises(ProviderConnectionPersistenceError) as caught:
                m.startup_provider_connection(self.path)
            self.assertIs(caught.exception, error)
            assess.assert_not_called()

    def test_failed_readiness_propagates_without_fallback(self):
        owner = ProviderConnectionService(ProviderConnectionFileStore(self.path))
        owner.initialize()
        error = ProviderConnectionReadinessError("Connection document has an invalid type")
        with mock.patch.object(m, "bootstrap_provider_connection", return_value=owner), \
             mock.patch.object(m, "assess_provider_connection_readiness", side_effect=error):
            with self.assertRaises(ProviderConnectionReadinessError) as caught:
                m.startup_provider_connection(self.path)
            self.assertIs(caught.exception, error)

    def test_missing_parent_is_not_created(self):
        target = self.directory / "not_created" / "connection.json"
        result = m.startup_provider_connection(target)
        self.assertEqual(result.readiness.status, ProviderConnectionReadinessStatus.UNCONFIGURED)
        self.assertFalse(target.parent.exists())

    def test_corrupt_metadata_fails_closed_without_repair(self):
        self.path.write_bytes(b"{ malformed json")
        before = self.path.read_bytes()
        with self.assertRaises(ProviderConnectionPersistenceError):
            m.startup_provider_connection(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_no_secret_backend_client_or_native_activation(self):
        self.configure()
        from nayeon.secrets.resolver import BoundSecretResolver
        from nayeon.brain.providers.openai import OpenAIProvider
        from nayeon.secrets.windows_credential import WindowsCredentialBackend
        with mock.patch.object(BoundSecretResolver, "__init__",
                               side_effect=AssertionError("secret resolution setup")), \
             mock.patch.object(OpenAIProvider, "__init__",
                               side_effect=AssertionError("provider activation")), \
             mock.patch.object(WindowsCredentialBackend, "_adapter",
                               side_effect=AssertionError("native credentials")):
            result = m.startup_provider_connection(self.path)
        self.assertEqual(result.readiness.status,
                         ProviderConnectionReadinessStatus.READY_FOR_COMPOSITION)

    def test_source_no_automatic_activation_or_ambient_configuration(self):
        tree = ast.parse(inspect.getsource(m))
        imports = []
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
            elif isinstance(node, ast.Import):
                imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.Call):
                calls.append(node.func.attr if isinstance(node.func, ast.Attribute)
                             else node.func.id if isinstance(node.func, ast.Name) else "")
        self.assertFalse(any(x.startswith((
            "nayeon.secrets", "nayeon.brain.providers",
            "nayeon.brain.connection_composition", "os", "openai",
            "nayeon.config", "nayeon.intent", "socket",
        )) for x in imports))
        for forbidden in ("get", "is_available", "resolve", "validate", "generate",
                          "getenv", "OpenAIProvider", "compose_provider_ai_service",
                          "put", "save", "replace", "clear"):
            self.assertNotIn(forbidden, calls)


class Phase87FrozenProductionScope(unittest.TestCase):
    """Freeze exact 100 Phase 8.6 production Python files plus requirements."""

    def test_all_phase86_production_frozen_two_explicit_additions_only(self):
        root = Path(__file__).resolve().parents[1]
        tag = "nayeon-v1-trusted-provider-connection-composition-bootstrap-01"
        product = "059b55efe945a561940f3d7bd9aa7b7d3fc6a971"
        delta = {"nayeon/brain/connection_readiness.py",
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
         "nayeon/desktop_alpha/first_run_status_window.py",
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py",
         "nayeon/desktop_alpha/notepad.py"}
        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root).decode().strip()
        self.assertEqual(git("branch", "--show-current"), "nayeon-v1")
        self.assertEqual(git("cat-file", "-t", tag), "tag")
        self.assertEqual(git("rev-parse", tag + "^{commit}"), product)
        tracked = set(git("ls-tree", "-r", "--name-only", tag, "--", "nayeon").splitlines())
        production = {name for name in tracked if name.endswith(".py")}
        self.assertEqual(len(production), 100)
        changed = set(filter(None, git("diff", "--name-only", tag, "--", "nayeon",
                                       "requirements.txt").splitlines()))
        untracked = set(filter(None, git("ls-files", "--others",
                                         "--exclude-standard", "--", "nayeon").splitlines()))
        self.assertEqual(changed | untracked, delta)
        self.assertFalse(changed & untracked)
        actual = {p.relative_to(root).as_posix() for p in (root / "nayeon").rglob("*.py")}
        self.assertEqual(actual, production | delta)
        for name in tracked | {"requirements.txt"}:
            with self.subTest(name=name):
                actual_bytes = (root / name).read_bytes().replace(b"\r\n", b"\n")
                sealed_bytes = subprocess.check_output(
                    ["git", "show", tag + ":" + name], cwd=root
                ).replace(b"\r\n", b"\n")
                self.assertEqual(actual_bytes, sealed_bytes)


if __name__ == "__main__":
    unittest.main()
