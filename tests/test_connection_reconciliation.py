"""Phase 8.9 read-only provider/key reconciliation, deterministic only."""

import ast
from dataclasses import FrozenInstanceError
import inspect
from pathlib import Path, PurePath
import subprocess
import tempfile
import unittest
from unittest import mock

from nayeon.brain import connection_reconciliation as m
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.secrets.contracts import SecretIdentifier


OPENAI = SecretIdentifier("openai.api_key")
S = m.ConnectionObservationStatus


class FakeAvailability:
    def __init__(self, answer=False, error=None, on_check=None):
        self.answer = answer
        self.error = error
        self.on_check = on_check
        self.calls = []

    def is_available(self, identifier):
        self.calls.append(identifier)
        if self.on_check:
            self.on_check()
        if self.error:
            raise self.error
        return self.answer


class ConnectionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "connection.json"
        self.backend = FakeAvailability()

    def save(self, provider="openai", model="test-model", key="openai.api_key"):
        configuration = ProviderConnectionConfiguration(
            provider, model, SecretIdentifier(key),
        )
        ProviderConnectionFileStore(self.path).save(
            ProviderConnectionDocumentV1(connection=configuration)
        )

    def test_unconfigured_without_key_does_not_create_metadata_or_parent(self):
        self.assertEqual(m.observe_connection(self.path, self.backend).status, S.SETUP_REQUIRED)
        self.assertFalse(self.path.exists())
        self.assertEqual(self.backend.calls, [OPENAI])
        absent = self.path.parent / "absent" / "config.json"
        self.assertEqual(m.observe_connection(absent, self.backend).status, S.SETUP_REQUIRED)
        self.assertFalse(absent.parent.exists())

    def test_unconfigured_key_present_kept_for_review(self):
        self.backend.answer = True
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.UNCONFIGURED_CREDENTIAL_PRESENT)
        self.assertEqual(self.backend.calls, [OPENAI])

    def test_explicit_null_configuration_and_key(self):
        ProviderConnectionFileStore(self.path).save(ProviderConnectionDocumentV1())
        before = self.path.read_bytes()
        self.backend.answer = True
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.UNCONFIGURED_CREDENTIAL_PRESENT)
        self.assertEqual(self.path.read_bytes(), before)

    def test_supported_configuration_missing_key(self):
        self.save()
        before = self.path.read_bytes()
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.CREDENTIAL_REQUIRED)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.backend.calls, [OPENAI])

    def test_supported_and_credential_available_means_validation_required(self):
        self.save()
        self.backend.answer = True
        observation = m.observe_connection(self.path, self.backend)
        self.assertEqual(observation.status, S.VALIDATION_REQUIRED)
        self.assertNotIn("connected", observation.status.value)
        self.assertEqual(self.backend.calls, [OPENAI])

    def test_unsupported_provider_no_key_lookup(self):
        self.save(provider="other")
        self.backend = FakeAvailability(error=RuntimeError("MUST NOT CALL"))
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.UNSUPPORTED_CONFIGURATION)
        self.assertEqual(self.backend.calls, [])

    def test_unsupported_credential_no_key_lookup(self):
        self.save(key="wrong.secret")
        self.backend = FakeAvailability(error=RuntimeError("MUST NOT CALL"))
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.UNSUPPORTED_CONFIGURATION)
        self.assertEqual(self.backend.calls, [])

    def test_unsupported_credential_or_provider_change_detected_without_key_lookup(self):
        self.save(provider="other")
        native = m.bootstrap_provider_connection
        reads = []
        def bootstrap(path):
            reads.append(True)
            if len(reads) == 2:
                self.save(provider="third_party")
            return native(path)
        with mock.patch.object(m, "bootstrap_provider_connection", side_effect=bootstrap):
            result = m.observe_connection(self.path, self.backend)
        self.assertEqual(result.status, S.CHANGED_DURING_OBSERVATION)
        self.assertEqual(self.backend.calls, [])

    def test_config_changes_during_availability_check_fail_closed(self):
        self.save()
        self.backend.on_check = lambda: self.save(model="changed-model")
        self.backend.answer = True
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.CHANGED_DURING_OBSERVATION)

    def test_config_cleared_during_availability_check_fail_closed(self):
        self.save()
        self.backend.on_check = lambda: ProviderConnectionFileStore(self.path).save(
            ProviderConnectionDocumentV1()
        )
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.CHANGED_DURING_OBSERVATION)

    def test_config_changes_provider_during_availability_check_fail_closed(self):
        self.save()
        self.backend.on_check = lambda: self.save(provider="elsewhere")
        self.assertEqual(m.observe_connection(self.path, self.backend).status,
                         S.CHANGED_DURING_OBSERVATION)

    def test_config_load_failure_is_unknown_and_skips_credential_probe(self):
        self.path.write_bytes(b'not json')
        before = self.path.read_bytes()
        self.assertEqual(m.observe_connection(self.path, self.backend).status, S.UNKNOWN)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.path.read_bytes(), before)

    def test_first_read_error_is_unknown_safe(self):
        with mock.patch.object(m, "bootstrap_provider_connection",
                               side_effect=OSError("PRIVATE-PATH-DETAIL")):
            observation = m.observe_connection(self.path, self.backend)
        self.assertEqual(observation.status, S.UNKNOWN)
        self.assertNotIn("PRIVATE-PATH", repr(observation))
        self.assertEqual(self.backend.calls, [])

    def test_second_read_error_is_unknown_without_metadata_repair(self):
        self.save()
        original = m.bootstrap_provider_connection
        calls = []
        def read(path):
            calls.append(1)
            if len(calls) == 2:
                raise OSError("PRIVATE-PATH-DETAIL")
            return original(path)
        with mock.patch.object(m, "bootstrap_provider_connection", side_effect=read):
            result = m.observe_connection(self.path, self.backend)
        self.assertEqual(result.status, S.UNKNOWN)
        self.assertEqual(self.backend.calls, [OPENAI])

    def test_storage_failure_unknown_no_fallback(self):
        self.save()
        self.backend.error = RuntimeError("SENSITIVE-STORAGE-PATH")
        self.assertEqual(m.observe_connection(self.path, self.backend).status, S.UNKNOWN)
        self.assertEqual(self.backend.calls, [OPENAI])

    def test_invalid_backend_return_is_unknown(self):
        self.save()
        for invalid in (None, 1, "yes", object()):
            with self.subTest(value=type(invalid).__name__):
                backend = FakeAvailability(answer=invalid)
                self.assertEqual(m.observe_connection(self.path, backend).status, S.UNKNOWN)

    def test_malformed_path_and_backend_rejected_before_io(self):
        class DerivedPath(type(Path())):
            pass
        for bad in (str(self.path), None, PurePath(self.path), DerivedPath(self.path)):
            with self.subTest(value=type(bad).__name__), self.assertRaises(TypeError):
                m.observe_connection(bad, self.backend)
        for bad in (object(), None, {}):
            with self.subTest(source=type(bad).__name__), self.assertRaises(TypeError):
                m.observe_connection(self.path, bad)
        self.assertEqual(self.backend.calls, [])
        self.assertFalse(self.path.exists())

    def test_hostile_backend_property_rejected_without_io(self):
        class Hostile:
            @property
            def is_available(self):
                raise ValueError("SENSITIVE")
        with self.assertRaisesRegex(TypeError, "Availability source must provide is_available"):
            m.observe_connection(self.path, Hostile())
        self.assertFalse(self.path.exists())

    def test_no_secret_get_put_delete_validation_even_with_supplied_backend(self):
        self.save()
        class Guard(FakeAvailability):
            def get(self, *_): raise AssertionError("forbidden get")
            def put(self, *_): raise AssertionError("forbidden put")
            def delete(self, *_): raise AssertionError("forbidden delete")
            def validate(self, *_): raise AssertionError("forbidden validate")
        backend = Guard(answer=True)
        self.assertEqual(m.observe_connection(self.path, backend).status, S.VALIDATION_REQUIRED)
        self.assertEqual(backend.calls, [OPENAI])

    def test_result_exact_immutable_non_secret_type(self):
        result = m.ConnectionObservation(S.UNKNOWN)
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertEqual(tuple(result.__dataclass_fields__), ("status",))
        self.assertIs(type(result.status), S)
        with self.assertRaises(FrozenInstanceError):
            result.status = S.SETUP_REQUIRED
        for bad in ("unknown", None, object()):
            with self.assertRaises(TypeError):
                m.ConnectionObservation(bad)

    def test_import_and_call_source_read_only_contract(self):
        tree = ast.parse(inspect.getsource(m))
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(modules, {"dataclasses", "enum", "pathlib", "typing",
            "nayeon.brain.connection_bootstrap", "nayeon.brain.connection_readiness",
            "nayeon.secrets.contracts"})
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        for forbidden in ("open", "get", "put", "delete", "replace", "save",
                          "clear", "test_stored", "test_candidate", "validate",
                          "OpenAIProvider", "WindowsCredentialBackend", "getenv",
                          "resolve", "load_openai_sdk"):
            self.assertNotIn(forbidden, calls)
        self.assertIn("is_available", calls)


class Phase89ProductionFreeze(unittest.TestCase):
    def test_all_phase88_sealed_production_and_requirements_preserved(self):
        root = Path(__file__).resolve().parents[1]
        tag = "nayeon-v1-trusted-credential-onboarding-explicit-operations-01"
        sealed = "eeb85d5e85fefa6abb37cfedef6c956954b41a0b"
        delta = {"nayeon/brain/connection_reconciliation.py",
                 "nayeon/brain/connection_recovery_advice.py",
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
         "nayeon/brain/onboarding_metadata_document.py",
         "nayeon/brain/onboarding_metadata_review.py"}
        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root).decode().strip()
        self.assertEqual(git("branch", "--show-current"), "nayeon-v1")
        self.assertEqual(git("cat-file", "-t", tag), "tag")
        self.assertEqual(git("rev-parse", tag + "^{commit}"), sealed)
        previous = set(git("ls-tree", "-r", "--name-only", tag, "--", "nayeon").splitlines())
        production = {x for x in previous if x.endswith(".py")}
        self.assertEqual(len(production), 104)
        actual = {p.relative_to(root).as_posix() for p in (root / "nayeon").rglob("*.py")}
        self.assertEqual(actual, production | delta)
        diff = set(filter(None, git("diff", "--name-only", tag,
                                    "--", "nayeon", "requirements.txt").splitlines()))
        untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard",
                                         "--", "nayeon").splitlines()))
        self.assertEqual(diff | untracked, delta)
        for name in previous | {"requirements.txt"}:
            with self.subTest(file=name):
                contents = (root / name).read_bytes().replace(b"\r\n", b"\n")
                previous_contents = subprocess.check_output(
                    ["git", "show", tag + ":" + name], cwd=root
                ).replace(b"\r\n", b"\n")
                self.assertEqual(contents, previous_contents)


if __name__ == "__main__":
    unittest.main()
