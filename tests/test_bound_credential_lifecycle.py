"""Deterministic Phase 8.3 lifecycle privacy, ordering and authority tests."""

import ast
import copy
from enum import Enum
import inspect
from pathlib import Path
import pickle
import subprocess
import traceback
from typing import get_type_hints
import unittest
from unittest.mock import Mock, call

from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)
from nayeon.secrets.lifecycle import (
    BoundCredentialLifecycle, CredentialLifecycleStateError,
    CredentialValidationStatus as Status, CredentialValidator,
)


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
         "nayeon/brain/onboarding_operation_advice.py",
         "nayeon/brain/onboarding_review_session.py",
         "nayeon/brain/credential_operation_host.py",
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py",
         "nayeon/desktop_alpha/notepad.py"}
FAILURE = "Credential lifecycle operation failed"


class IdentifierSubclass(SecretIdentifier):
    pass


class ValueSubclass(SecretValue):
    pass


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.identifier = SecretIdentifier("synthetic.private_key")
        self.value = SecretValue("synthetic-sensitive-marker")
        self.backend = Mock(spec=["get", "put", "delete", "is_available"])
        self.validator = Mock(spec=["validate"])
        self.validator.validate.return_value = Status.VALID
        self.lifecycle = BoundCredentialLifecycle(self.backend, self.identifier, self.validator)
        self.events = Mock()
        self.events.attach_mock(self.backend, "backend")
        self.events.attach_mock(self.validator, "validator")

    def test_enum_and_narrow_protocol(self):
        self.assertTrue(issubclass(Status, Enum))
        self.assertFalse(issubclass(Status, (str, int)))
        self.assertEqual({k: v.value for k, v in Status.__members__.items()},
                         {"VALID": "valid", "INVALID": "invalid", "INDETERMINATE": "indeterminate"})
        self.assertTrue(CredentialValidator._is_protocol)
        self.assertEqual({n for n in vars(CredentialValidator) if not n.startswith("_")}, {"validate"})
        self.assertEqual(list(inspect.signature(CredentialValidator.validate).parameters), ["self", "value"])
        self.assertEqual(get_type_hints(CredentialValidator.validate),
                         {"value": SecretValue, "return": Status})
        self.assertTrue(issubclass(CredentialLifecycleStateError, RuntimeError))

    def test_shape_identity_redaction_and_immutability(self):
        self.assertEqual(BoundCredentialLifecycle.__slots__, ("__backend", "__identifier", "__validator"))
        self.assertFalse(hasattr(self.lifecycle, "__dict__"))
        self.assertEqual({n for n in dir(self.lifecycle) if not n.startswith("_")},
                         {"identifier", "is_connected", "test_candidate", "test_stored", "connect", "replace", "remove"})
        self.assertIs(self.lifecycle.identifier, self.identifier)
        self.assertEqual(repr(self.lifecycle), "BoundCredentialLifecycle(<redacted>)")
        self.assertEqual(str(self.lifecycle), repr(self.lifecycle))
        other = BoundCredentialLifecycle(self.backend, self.identifier, self.validator)
        self.assertIs(BoundCredentialLifecycle.__eq__, object.__eq__)
        self.assertIs(BoundCredentialLifecycle.__hash__, object.__hash__)
        self.assertEqual(len({self.lifecycle, other}), 2)
        for name in ("identifier", "backend", "validator", "extra", *("_BoundCredentialLifecycle" + s for s in BoundCredentialLifecycle.__slots__)):
            with self.assertRaises(AttributeError):
                setattr(self.lifecycle, name, None)
            with self.assertRaises(AttributeError):
                delattr(self.lifecycle, name)
        with self.assertRaises(AttributeError):
            self.lifecycle.__init__(self.backend, self.identifier, self.validator)
        self.assertEqual(self.events.mock_calls, [])

    def test_serialization_and_state_extraction_blocked(self):
        for operation in (pickle.dumps, copy.copy, copy.deepcopy):
            with self.assertRaises(TypeError):
                operation(self.lifecycle)
        for operation in (self.lifecycle.__getstate__, self.lifecycle.__reduce__):
            with self.assertRaises(TypeError):
                operation()
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.assertRaises(TypeError):
                pickle.dumps(self.lifecycle, protocol=protocol)

    def test_constructor_exact_identifier_and_zero_calls(self):
        for bad in (IdentifierSubclass("key"), "key", None, Mock(value="key")):
            with self.assertRaises(TypeError):
                BoundCredentialLifecycle(self.backend, bad, self.validator)
        self.assertEqual(self.events.mock_calls, [])

    def test_structural_constructor_requires_each_callable_without_invocation(self):
        for name in ("get", "put", "delete", "is_available"):
            backend = Mock(spec=["get", "put", "delete", "is_available"])
            setattr(backend, name, None)
            with self.assertRaises(TypeError):
                BoundCredentialLifecycle(backend, self.identifier, self.validator)
            self.assertEqual(backend.mock_calls, [])
        for bad in (None, object(), Mock(validate=1)):
            with self.assertRaises(TypeError):
                BoundCredentialLifecycle(self.backend, self.identifier, bad)
        class StructuralBackend:
            def get(self, identifier):
                raise AssertionError("constructor must not call")
            put = delete = is_available = get
        class StructuralValidator:
            def validate(self, value):
                raise AssertionError("constructor must not call")
        BoundCredentialLifecycle(StructuralBackend(), self.identifier, StructuralValidator())
        self.assertEqual(self.events.mock_calls, [])

    def test_constructor_attribute_failures_sanitized(self):
        class Hostile:
            def __getattribute__(self, name):
                raise RuntimeError("synthetic-sensitive-marker")
        for args in ((Hostile(), self.identifier, self.validator),
                     (self.backend, self.identifier, Hostile())):
            try:
                BoundCredentialLifecycle(*args)
            except TypeError as error:
                self.assertTrue(error.__suppress_context__)
                self.assertNotIn("synthetic-sensitive-marker", traceback.format_exc())
            else:
                self.fail("expected sanitized rejection")

    def test_exact_value_before_any_calls(self):
        for operation in (self.lifecycle.test_candidate, self.lifecycle.connect, self.lifecycle.replace):
            for bad in (ValueSubclass("synthetic"), "synthetic", None, Mock(reveal=lambda: "synthetic")):
                with self.assertRaises(TypeError):
                    operation(bad)
        self.assertEqual(self.events.mock_calls, [])

    def test_candidate_preserves_status_one_validator_zero_backend(self):
        for status in Status:
            self.events.reset_mock()
            self.validator.validate.return_value = status
            self.assertIs(self.lifecycle.test_candidate(self.value), status)
            self.assertEqual(self.events.mock_calls, [call.validator.validate(self.value)])
            self.assertIs(self.validator.validate.call_args.args[0], self.value)

    def test_validator_exceptions_become_indeterminate(self):
        errors = (RuntimeError, SecretNotFoundError, SecretStorageError)
        for operation, available in ((self.lifecycle.test_candidate, None),
                                     (self.lifecycle.test_stored, None),
                                     (self.lifecycle.connect, False), (self.lifecycle.replace, True)):
            for exception in errors:
                self.events.reset_mock()
                self.backend.is_available.return_value = available
                self.backend.get.return_value = self.value
                self.validator.validate.side_effect = exception("synthetic-sensitive-marker")
                result = operation() if operation == self.lifecycle.test_stored else operation(self.value)
                self.assertIs(result, Status.INDETERMINATE)
                self.validator.validate.assert_called_once_with(self.value)
                self.backend.put.assert_not_called()
                self.backend.delete.assert_not_called()
                self.assertNotIn("synthetic-sensitive-marker", repr(result))
        self.validator.validate.side_effect = None

    def test_process_control_exceptions_are_not_swallowed(self):
        for exception in (KeyboardInterrupt, SystemExit):
            self.events.reset_mock()
            self.validator.validate.side_effect = exception("stop")
            with self.assertRaises(exception):
                self.lifecycle.test_candidate(self.value)
            self.assertEqual(self.events.mock_calls, [call.validator.validate(self.value)])
        self.validator.validate.side_effect = None

    def test_wrong_validator_result_becomes_indeterminate(self):
        for operation, available in ((self.lifecycle.test_candidate, None), (self.lifecycle.test_stored, None),
                                     (self.lifecycle.connect, False), (self.lifecycle.replace, True)):
            for bad in (None, True, "valid", 1, object()):
                self.events.reset_mock()
                self.backend.is_available.side_effect = None
                self.backend.is_available.return_value = available
                self.backend.get.side_effect = None
                self.backend.get.return_value = self.value
                self.validator.validate.side_effect = None
                self.validator.validate.return_value = bad
                result = operation() if operation == self.lifecycle.test_stored else operation(self.value)
                self.assertIs(result, Status.INDETERMINATE)
                self.validator.validate.assert_called_once_with(self.value)
                self.backend.put.assert_not_called()
                self.backend.delete.assert_not_called()

    def test_is_connected_one_availability_exact_bool(self):
        for result in (True, False):
            self.events.reset_mock()
            self.backend.is_available.return_value = result
            self.assertIs(self.lifecycle.is_connected(), result)
            self.assertEqual(self.events.mock_calls, [call.backend.is_available(self.identifier)])
            self.assertIs(self.backend.is_available.call_args.args[0], self.identifier)

    def test_availability_and_delete_reject_non_bool(self):
        for bad in (1, 0, None, "true", object()):
            for operation, backend_method in ((self.lifecycle.is_connected, self.backend.is_available),
                                              (self.lifecycle.remove, self.backend.delete)):
                self.events.reset_mock()
                self.backend.is_available.side_effect = None
                backend_method.return_value = bad
                with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                    operation()
                backend_method.assert_called_once_with(self.identifier)
                self.assertEqual(len(self.events.mock_calls), 1)
            for operation, available in ((self.lifecycle.connect, False), (self.lifecycle.replace, True)):
                for results in ([bad], [available, bad]):
                    self.events.reset_mock()
                    self.backend.is_available.side_effect = results
                    with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                        operation(self.value)
                    self.backend.put.assert_not_called()
                    self.backend.delete.assert_not_called()
                    self.backend.get.assert_not_called()
        self.backend.is_available.side_effect = None

    def test_stored_exact_get_then_validate_and_no_secret_return(self):
        for status in Status:
            self.events.reset_mock()
            self.backend.get.return_value = self.value
            self.validator.validate.return_value = status
            self.assertIs(self.lifecycle.test_stored(), status)
            self.assertEqual(self.events.mock_calls,
                             [call.backend.get(self.identifier), call.validator.validate(self.value)])
            self.assertIs(self.validator.validate.call_args.args[0], self.value)

    def test_stored_contract_errors_propagate_without_validator(self):
        for error in (SecretNotFoundError("Secret is not available"), SecretStorageError("Secret storage operation failed")):
            self.events.reset_mock()
            self.backend.get.side_effect = error
            with self.assertRaises(type(error)) as caught:
                self.lifecycle.test_stored()
            self.assertIs(caught.exception, error)
            self.assertEqual(self.events.mock_calls, [call.backend.get(self.identifier)])

    def test_stored_wrong_value_rejected_before_validator(self):
        for bad in (ValueSubclass("synthetic"), None, "synthetic", Mock()):
            self.events.reset_mock()
            self.backend.get.return_value = bad
            with self.assertRaisesRegex(SecretStorageError, "^" + FAILURE + "$"):
                self.lifecycle.test_stored()
            self.assertEqual(self.events.mock_calls, [call.backend.get(self.identifier)])

    def test_connect_and_replace_preconditions_before_validation(self):
        for operation, available, message in (
            (self.lifecycle.connect, True, "Credential is already connected"),
            (self.lifecycle.replace, False, "Credential is not connected"),
        ):
            self.events.reset_mock()
            self.backend.is_available.return_value = available
            with self.assertRaisesRegex(CredentialLifecycleStateError, "^" + message + "$"):
                operation(self.value)
            self.assertEqual(self.events.mock_calls, [call.backend.is_available(self.identifier)])

    def test_invalid_and_indeterminate_connect_replace_do_not_write_or_recheck(self):
        for operation, available in ((self.lifecycle.connect, False), (self.lifecycle.replace, True)):
            for status in (Status.INVALID, Status.INDETERMINATE):
                self.events.reset_mock()
                self.backend.is_available.return_value = available
                self.validator.validate.return_value = status
                self.assertIs(operation(self.value), status)
                self.assertEqual(self.events.mock_calls,
                                 [call.backend.is_available(self.identifier), call.validator.validate(self.value)])

    def test_valid_connect_replace_order_same_value_no_get_delete_readback(self):
        for operation, available in ((self.lifecycle.connect, False), (self.lifecycle.replace, True)):
            self.events.reset_mock()
            self.backend.is_available.side_effect = [available, available]
            self.assertIs(operation(self.value), Status.VALID)
            self.assertEqual(self.events.mock_calls, [call.backend.is_available(self.identifier),
                call.validator.validate(self.value), call.backend.is_available(self.identifier),
                call.backend.put(self.identifier, self.value)])
            self.assertIs(self.backend.put.call_args.args[0], self.identifier)
            self.assertIs(self.backend.put.call_args.args[1], self.value)

    def test_connect_replace_state_change_prevents_put(self):
        for operation, states in ((self.lifecycle.connect, [False, True]), (self.lifecycle.replace, [True, False])):
            self.events.reset_mock()
            self.backend.is_available.side_effect = states
            with self.assertRaisesRegex(CredentialLifecycleStateError, "^Credential state changed$"):
                operation(self.value)
            self.assertEqual(self.events.mock_calls, [call.backend.is_available(self.identifier),
                call.validator.validate(self.value), call.backend.is_available(self.identifier)])

    def test_replace_preserves_old_value_through_validation(self):
        old = SecretValue("synthetic-old")
        state = [old]
        def validate(candidate):
            self.assertIs(state[0], old)
            self.assertIs(candidate, self.value)
            return Status.VALID
        def put(identifier, candidate):
            self.assertIs(state[0], old)
            state[0] = candidate
        self.backend.is_available.return_value = True
        self.validator.validate.side_effect = validate
        self.backend.put.side_effect = put
        self.assertIs(self.lifecycle.replace(self.value), Status.VALID)
        self.assertIs(state[0], self.value)
        self.backend.get.assert_not_called()
        self.backend.delete.assert_not_called()

    def test_remove_one_delete_no_probe(self):
        for result in (False, True):
            self.events.reset_mock()
            self.backend.delete.return_value = result
            self.assertIs(self.lifecycle.remove(), result)
            self.assertEqual(self.events.mock_calls, [call.backend.delete(self.identifier)])

    def test_backend_errors_at_each_stage_safe_contract_or_sanitized(self):
        scenarios = ((self.lifecycle.is_connected, "is_available", None),
                     (self.lifecycle.test_stored, "get", None), (self.lifecycle.remove, "delete", None),
                     (self.lifecycle.connect, "is_available", []),
                     (self.lifecycle.replace, "is_available", []),
                     (self.lifecycle.connect, "is_available", [False]),
                     (self.lifecycle.replace, "is_available", [True]),
                     (self.lifecycle.connect, "put", [False, False]),
                     (self.lifecycle.replace, "put", [True, True]))
        for operation, method, prefix in scenarios:
            for error in (SecretStorageError("Secret storage operation failed"),
                          RuntimeError("synthetic-sensitive-marker"), SecretNotFoundError("Secret is not available")):
                self.backend.reset_mock(return_value=True, side_effect=True)
                self.validator.reset_mock(return_value=True, side_effect=True)
                self.validator.validate.return_value = Status.VALID
                if method == "is_available" and prefix is not None:
                    self.backend.is_available.side_effect = prefix + [error]
                else:
                    getattr(self.backend, method).side_effect = error
                    if prefix is not None:
                        self.backend.is_available.side_effect = prefix
                try:
                    if operation in (self.lifecycle.connect, self.lifecycle.replace):
                        operation(self.value)
                    else:
                        operation()
                except (SecretStorageError, SecretNotFoundError) as caught:
                    if isinstance(error, SecretStorageError) or (method == "get" and isinstance(error, SecretNotFoundError)):
                        self.assertIs(caught, error)
                    else:
                        self.assertIs(type(caught), SecretStorageError)
                        self.assertEqual(str(caught), FAILURE)
                        self.assertTrue(caught.__suppress_context__)
                        self.assertIsNone(caught.__cause__)
                        self.assertNotIn("synthetic-sensitive-marker", traceback.format_exc())
                    if method != "delete":
                        self.backend.delete.assert_not_called()
                    if method != "get":
                        self.backend.get.assert_not_called()
                    if method == "put":
                        self.backend.put.assert_called_once_with(self.identifier, self.value)
                    else:
                        self.backend.put.assert_not_called()
                else:
                    self.fail("expected backend failure")

    def test_no_candidate_or_stored_value_cache(self):
        first, second = SecretValue("synthetic-one"), SecretValue("synthetic-two")
        self.backend.get.side_effect = [first, second]
        self.lifecycle.test_stored()
        self.lifecycle.test_stored()
        self.lifecycle.test_candidate(self.value)
        self.assertEqual(self.validator.validate.call_args_list, [call(first), call(second), call(self.value)])
        for slot, expected in zip(BoundCredentialLifecycle.__slots__,
                                  (self.backend, self.identifier, self.validator)):
            self.assertIs(getattr(self.lifecycle, "_BoundCredentialLifecycle" + slot), expected)
            self.assertNotIsInstance(expected, SecretValue)

    def test_source_import_boundary_no_plaintext_or_side_channels(self):
        tree = ast.parse((ROOT / "nayeon/secrets/lifecycle.py").read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertEqual([(n.module, [a.name for a in n.names]) for n in imports], [
            ("enum", ["Enum"]), ("typing", ["Protocol"]),
            ("nayeon.secrets.contracts", ["SecretBackend", "SecretIdentifier", "SecretNotFoundError", "SecretStorageError", "SecretValue"]),
        ])
        for n in ast.walk(tree):
            if isinstance(n, (ast.Name, ast.Attribute)):
                self.assertNotIn(n.id if isinstance(n, ast.Name) else n.attr,
                    {"reveal", "print", "open", "eval", "exec", "__import__", "environ", "getenv"})


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class Phase83ScopeGuards(unittest.TestCase):
    def test_exact_new_production_delta_and_every_preexisting_file_frozen(self):
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        # The protected starting checkpoint remains an ancestor across seals.
        self.assertEqual(git("merge-base", START, "HEAD").decode().strip(), START)
        self.assertEqual(git("cat-file", "-t", TAG).decode().strip(), "tag")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), SEALED)
        for baseline in (START, SEALED):
            tracked = set(git("ls-tree", "-r", "--name-only", baseline, "--", "nayeon").decode().splitlines())
            self.assertEqual(tracked & DELTA, set())
            changed = set(git("diff", "--name-only", baseline, "--", "nayeon").decode().splitlines())
            untracked = set(git("ls-files", "--others", "--exclude-standard", "--", "nayeon").decode().splitlines())
            self.assertEqual(changed | untracked, DELTA)
            actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "nayeon").rglob("*.py")}
            self.assertEqual(actual, {p for p in tracked if p.endswith(".py")} | DELTA)
            for path in tracked:
                with self.subTest(baseline=baseline, path=path):
                    self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                                     git("show", baseline + ":" + path).replace(b"\r\n", b"\n"))

    def test_protected_context_dependencies_and_legacy_frozen(self):
        # The post-seal Codex handoff is intentionally refreshed; freeze instructions and script.
        paths = {"AGENTS.md", "scripts/update_codex_context.py",
                 "setup.py", "main.py", "ui.py"}
        for directory in ("actions", "core", "dashboard", "plugins", "memory"):
            paths.update(git("ls-tree", "-r", "--name-only", START, "--", directory).decode().splitlines())
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
                             git("show", START + ":" + path).replace(b"\r\n", b"\n"), path)

    def test_exact_consumers_and_zero_new_composition(self):
        targets = {"nayeon.secrets.lifecycle": "BoundCredentialLifecycle",
                   "nayeon.brain.connection": "ProviderConnectionConfiguration",
                   "nayeon.secrets.resolver": "BoundSecretResolver",
                   "nayeon.secrets.store": "SecretStore",
                   "nayeon.secrets.windows_credential": "WindowsCredentialBackend"}
        consumers = {name: set() for name in targets.values()}
        backend_consumers = set()
        for path in (ROOT / "nayeon").rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    names = {a.name for a in node.names}
                    for module, symbol in targets.items():
                        if node.module == module or symbol in names:
                            # Exact enum-only imports do not grant lifecycle authority.
                            # Phase 8.18's host may classify a delegated result,
                            # but may not import BoundCredentialLifecycle itself.
                            if (module == "nayeon.secrets.lifecycle"
                                    and node.module == module
                                    and relative in {
                                        "nayeon/brain/providers/openai_validation.py",
                                        "nayeon/brain/credential_operation_host.py",
                                    }
                                    and names == {"CredentialValidationStatus"}):
                                continue
                            consumers[symbol].add(relative)
                    if "SecretBackend" in names:
                        backend_consumers.add(relative)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in targets:
                            consumers[targets[alias.name]].add(relative)
        self.assertEqual(consumers, {"BoundCredentialLifecycle": {
            "nayeon/brain/credential_onboarding.py",
            "nayeon/brain/credential_onboarding_composition.py"}, "ProviderConnectionConfiguration": {
            "nayeon/brain/connection_document.py", "nayeon/brain/connection_service.py",
            "nayeon/brain/connection_composition.py",
            "nayeon/brain/connection_readiness.py",
            "nayeon/brain/onboarding_metadata_document.py"},
            "BoundSecretResolver": {"nayeon/brain/providers/openai.py",
                                    "nayeon/brain/connection_composition.py"},
            "SecretStore": set(), "WindowsCredentialBackend": set()})
        self.assertEqual(backend_consumers, {"nayeon/secrets/resolver.py",
                                             "nayeon/secrets/lifecycle.py",
                                             "nayeon/brain/connection_composition.py",
                                             "nayeon/brain/credential_onboarding_composition.py"})


if __name__ == "__main__":
    unittest.main()
