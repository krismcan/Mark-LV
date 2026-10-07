"""Credential probes use synthetic values and a fake canonical factory only."""

import ast
import inspect
import unittest
from unittest.mock import Mock, call, patch

from nayeon.brain.providers import openai_validation as m
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.lifecycle import CredentialValidationStatus as Status


class SecretSubclass(SecretValue):
    pass


class UninspectableResult:
    def __bool__(self):
        raise AssertionError("no result inspection")

    def __iter__(self):
        raise AssertionError("no result iteration")

    def __getattribute__(self, name):
        raise AssertionError("no result attributes")


class OpenAICredentialValidatorTests(unittest.TestCase):
    def setUp(self):
        self.secret = SecretValue(" synthetic-key-\u2603 ")
        self.validator = m.OpenAICredentialValidator()
        self.client = Mock()
        factory_patch = patch.object(m, "create_openai_client", return_value=self.client)
        self.factory = factory_patch.start()
        self.addCleanup(factory_patch.stop)

    def assert_probe(self):
        self.factory.assert_called_once_with(self.secret, timeout_seconds=5.0, max_retries=0)
        self.assertIs(self.factory.call_args.args[0], self.secret)
        self.client.models.list.assert_called_once_with()
        self.client.close.assert_called_once_with()
        self.assertEqual(self.client.mock_calls, [call.models.list(), call.close()])

    def test_stateless_slots_and_exact_signature(self):
        self.assertEqual(m.OpenAICredentialValidator.__slots__, ())
        self.assertFalse(hasattr(self.validator, "__dict__"))
        with self.assertRaises(AttributeError):
            self.validator.secret = self.secret
        self.assertEqual(list(inspect.signature(m.OpenAICredentialValidator).parameters), [])
        signature = inspect.signature(m.OpenAICredentialValidator.validate)
        self.assertEqual(list(signature.parameters), ["self", "value"])
        self.assertIs(signature.parameters["value"].annotation, SecretValue)
        self.assertIs(signature.return_annotation, Status)

    def test_exact_secret_input_rejected_before_any_action(self):
        duck = Mock(reveal=Mock(side_effect=AssertionError("no reveal")))
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            for value in (None, "synthetic", {}, 1, duck, SecretSubclass("synthetic")):
                with self.subTest(value=type(value)), self.assertRaisesRegex(
                    TypeError, "^Value must be an exact SecretValue$"
                ):
                    self.validator.validate(value)
            reveal.assert_not_called()
        duck.reveal.assert_not_called()
        self.factory.assert_not_called()
        self.assertEqual(self.client.mock_calls, [])

    def test_success_is_valid_without_direct_reveal(self):
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")):
            self.assertIs(self.validator.validate(self.secret), Status.VALID)
        self.assert_probe()

    def test_response_is_not_inspected_or_iterated(self):
        for result in (None, False, [], UninspectableResult()):
            with self.subTest(result_type=type(result)):
                self.factory.reset_mock()
                self.client.reset_mock()
                self.client.models.list.side_effect = lambda result=result: result
                self.assertIs(self.validator.validate(self.secret), Status.VALID)
                self.assert_probe()

    def test_construction_failures_are_indeterminate_without_client_actions(self):
        for error in (m.OpenAIClientConstructionError("synthetic-private"),
                      RuntimeError("synthetic-private"), TypeError("synthetic-private")):
            with self.subTest(error_type=type(error)):
                self.factory.reset_mock()
                self.factory.side_effect = error
                self.assertIs(self.validator.validate(self.secret), Status.INDETERMINATE)
                self.factory.assert_called_once_with(self.secret, timeout_seconds=5.0, max_retries=0)
                self.assertEqual(self.client.mock_calls, [])

    def test_request_failures_including_auth_never_return_invalid(self):
        for error in (RuntimeError("401 synthetic-private"), PermissionError("403 synthetic-private"),
                      TimeoutError("synthetic-private"), ConnectionError("synthetic-private"),
                      ValueError("synthetic-private")):
            with self.subTest(error_type=type(error)):
                self.factory.reset_mock()
                self.client.reset_mock()
                self.client.models.list.side_effect = error
                self.assertIs(self.validator.validate(self.secret), Status.INDETERMINATE)
                self.assert_probe()

    def test_ordinary_close_failure_is_indeterminate_after_success_or_failure(self):
        for request_error in (None, RuntimeError("synthetic-private")):
            with self.subTest(request_error=request_error):
                self.factory.reset_mock()
                self.client.reset_mock()
                self.client.models.list.side_effect = request_error
                self.client.close.side_effect = RuntimeError("synthetic-private")
                self.assertIs(self.validator.validate(self.secret), Status.INDETERMINATE)
                self.assert_probe()

    def test_construction_process_control_propagates(self):
        for error_type in (KeyboardInterrupt, SystemExit):
            error = error_type()
            self.factory.reset_mock()
            self.factory.side_effect = error
            with self.subTest(error_type=error_type), self.assertRaises(error_type) as caught:
                self.validator.validate(self.secret)
            self.assertIs(caught.exception, error)
            self.factory.assert_called_once_with(self.secret, timeout_seconds=5.0, max_retries=0)
            self.assertEqual(self.client.mock_calls, [])

    def test_request_process_control_propagates_with_exactly_one_cleanup(self):
        for error_type in (KeyboardInterrupt, SystemExit):
            for close_error in (None, RuntimeError("synthetic-private")):
                with self.subTest(error_type=error_type, close_error=close_error):
                    self.factory.reset_mock()
                    self.client.reset_mock()
                    error = error_type()
                    self.client.models.list.side_effect = error
                    self.client.close.side_effect = close_error
                    with self.assertRaises(error_type) as caught:
                        self.validator.validate(self.secret)
                    self.assertIs(caught.exception, error)
                    self.assert_probe()

    def test_close_process_control_propagates(self):
        for error_type in (KeyboardInterrupt, SystemExit):
            for request_error in (None, RuntimeError("synthetic-private")):
                with self.subTest(error_type=error_type, request_error=request_error):
                    self.factory.reset_mock()
                    self.client.reset_mock()
                    error = error_type()
                    self.client.models.list.side_effect = request_error
                    self.client.close.side_effect = error
                    with self.assertRaises(error_type) as caught:
                        self.validator.validate(self.secret)
                    self.assertIs(caught.exception, error)
                    self.assert_probe()

    def test_repeated_calls_construct_probe_and_close_fresh_without_cache(self):
        other = Mock()
        self.factory.side_effect = [self.client, other]
        for unused in range(2):
            self.assertIs(self.validator.validate(self.secret), Status.VALID)
        self.assertEqual(self.factory.call_args_list, [
            call(self.secret, timeout_seconds=5.0, max_retries=0),
            call(self.secret, timeout_seconds=5.0, max_retries=0),
        ])
        for client in (self.client, other):
            self.assertEqual(client.mock_calls, [call.models.list(), call.close()])
        self.assertFalse(hasattr(self.validator, "__dict__"))
        self.assertNotIn("synthetic-key", repr(self.validator))
        self.assertNotIn("synthetic-key", str(self.validator))

    def test_exact_imports_and_bounded_operations(self):
        tree = ast.parse(inspect.getsource(m))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(isinstance(n, ast.ImportFrom) and n.level == 0 for n in imports))
        self.assertEqual([(n.module, [(a.name, a.asname) for a in n.names]) for n in imports], [
            ("nayeon.secrets.lifecycle", [("CredentialValidationStatus", None)]),
            ("nayeon.secrets.contracts", [("SecretValue", None)]),
            ("nayeon.brain.providers.openai_client", [
                ("create_openai_client", None), ("OpenAIClientConstructionError", None)]),
        ])
        self.assertEqual([n.name for n in tree.body if isinstance(n, ast.ClassDef)],
                         ["OpenAICredentialValidator"])
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertCountEqual(calls, ["type", "TypeError", "create_openai_client",
                                      "client.models.list", "client.close"])
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.Attribute)):
                self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr,
                    {"INVALID", "BaseException", "reveal", "print", "logging", "open",
                     "getattr", "setattr", "__import__", "eval", "exec", "environ", "getenv"})


if __name__ == "__main__":
    unittest.main()
