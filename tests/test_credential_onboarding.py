"""Phase 8.8 deterministic operation tests; fake storage and fake validation only."""

import ast
import inspect
import pickle
import unittest

from nayeon.brain import credential_onboarding as m
from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretStorageError, SecretValue,
)
from nayeon.secrets.lifecycle import BoundCredentialLifecycle, CredentialValidationStatus


ID = SecretIdentifier("openai.api_key")
SECRET = "fake-test-key-never-real"
VALID = CredentialValidationStatus.VALID
INVALID = CredentialValidationStatus.INVALID
UNKNOWN = CredentialValidationStatus.INDETERMINATE


class FakeBackend:
    def __init__(self):
        self.saved = {}
        self.calls = []
        self.failure = None
        self.after_check = None

    def _check(self, operation):
        self.calls.append(operation)
        if self.failure == operation:
            raise SecretStorageError("DO-NOT-LEAK-BACKEND-DETAIL")
        if self.after_check is not None:
            self.after_check(operation, self)

    def is_available(self, identifier):
        self._check("is_available")
        return identifier in self.saved

    def get(self, identifier):
        self._check("get")
        if identifier not in self.saved:
            raise SecretNotFoundError("DO-NOT-LEAK-MISSING-SECRET")
        return self.saved[identifier]

    def put(self, identifier, value):
        self._check("put")
        self.saved[identifier] = value

    def delete(self, identifier):
        self._check("delete")
        return self.saved.pop(identifier, None) is not None


class FakeValidator:
    def __init__(self, result=VALID):
        self.result = result
        self.calls = []

    def validate(self, value):
        self.calls.append(value)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


class CredentialOnboardingOperationsTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.lifecycle = BoundCredentialLifecycle(self.backend, ID, self.validator)
        self.onboarding = m.OpenAICredentialOnboarding(self.lifecycle)
        self.candidate = SecretValue(SECRET)

    def test_no_operation_during_construction(self):
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, [])
        self.assertEqual(repr(self.onboarding), "OpenAICredentialOnboarding(<redacted>)")
        self.assertEqual(str(self.onboarding), repr(self.onboarding))

    def test_connect_saves_only_after_successful_validation_and_recheck(self):
        self.assertIs(self.onboarding.connect(self.candidate), VALID)
        self.assertEqual(self.backend.calls, ["is_available", "is_available", "put"])
        self.assertEqual(self.validator.calls, [self.candidate])
        self.assertIs(self.backend.saved[ID], self.candidate)

    def test_connect_invalid_does_not_persist(self):
        self.validator.result = INVALID
        self.assertIs(self.onboarding.connect(self.candidate), INVALID)
        self.assertEqual(self.backend.calls, ["is_available"])
        self.assertEqual(self.backend.saved, {})

    def test_connect_indeterminate_does_not_persist(self):
        self.validator.result = UNKNOWN
        self.assertIs(self.onboarding.connect(self.candidate), UNKNOWN)
        self.assertEqual(self.backend.saved, {})

    def test_validator_exception_is_indeterminate(self):
        self.validator.result = RuntimeError("DO-NOT-LEAK-VALIDATOR-DETAIL")
        self.assertIs(self.onboarding.connect(self.candidate), UNKNOWN)
        self.assertEqual(self.backend.saved, {})

    def test_validator_returns_unexpected_type_indeterminate(self):
        self.validator.result = True
        self.assertIs(self.onboarding.connect(self.candidate), UNKNOWN)
        self.assertEqual(self.backend.saved, {})

    def test_connect_already_connected_rejected_no_validation_or_write(self):
        self.backend.saved[ID] = SecretValue("old-test-key")
        with self.assertRaisesRegex(m.CredentialOnboardingStateError,
                                   "^Credential operation is not permitted in the current state$"):
            self.onboarding.connect(self.candidate)
        self.assertEqual(self.validator.calls, [])
        self.assertIsNot(self.backend.saved[ID], self.candidate)

    def test_replace_valid_only_swaps_after_recheck(self):
        old = SecretValue("old-test-key")
        self.backend.saved[ID] = old
        self.assertIs(self.onboarding.replace(self.candidate), VALID)
        self.assertIs(self.backend.saved[ID], self.candidate)
        self.assertEqual(self.backend.calls, ["is_available", "is_available", "put"])

    def test_replace_invalid_keeps_old(self):
        old = SecretValue("old-test-key")
        self.backend.saved[ID] = old
        self.validator.result = INVALID
        self.assertIs(self.onboarding.replace(self.candidate), INVALID)
        self.assertIs(self.backend.saved[ID], old)
        self.assertEqual(self.backend.calls, ["is_available"])

    def test_replace_indeterminate_keeps_old(self):
        old = SecretValue("old-test-key")
        self.backend.saved[ID] = old
        self.validator.result = UNKNOWN
        self.assertIs(self.onboarding.replace(self.candidate), UNKNOWN)
        self.assertIs(self.backend.saved[ID], old)

    def test_replace_absent_rejected_without_validation(self):
        with self.assertRaises(m.CredentialOnboardingStateError):
            self.onboarding.replace(self.candidate)
        self.assertEqual(self.validator.calls, [])
        self.assertEqual(self.backend.calls, ["is_available"])

    def test_connect_race_state_changed_no_write(self):
        def modify(operation, backend):
            if operation == "is_available" and backend.calls.count("is_available") == 2:
                backend.saved[ID] = SecretValue("other-writer")
        self.backend.after_check = modify
        with self.assertRaises(m.CredentialOnboardingStateError):
            self.onboarding.connect(self.candidate)
        self.assertNotIn("put", self.backend.calls)

    def test_replace_race_state_changed_no_write(self):
        self.backend.saved[ID] = SecretValue("old-test-key")
        def modify(operation, backend):
            if operation == "is_available" and backend.calls.count("is_available") == 2:
                del backend.saved[ID]
        self.backend.after_check = modify
        with self.assertRaises(m.CredentialOnboardingStateError):
            self.onboarding.replace(self.candidate)
        self.assertNotIn("put", self.backend.calls)

    def test_explicit_test_candidate_does_not_touch_storage(self):
        self.assertIs(self.onboarding.test_candidate(self.candidate), VALID)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, [self.candidate])

    def test_test_stored_reads_only_fixed_identifier(self):
        self.backend.saved[ID] = self.candidate
        self.assertIs(self.onboarding.test_stored(), VALID)
        self.assertEqual(self.backend.calls, ["get"])
        self.assertEqual(self.validator.calls, [self.candidate])

    def test_test_stored_missing_is_fixed_safe_error(self):
        with self.assertRaisesRegex(SecretNotFoundError, "^Credential is not available$"):
            self.onboarding.test_stored()
        self.assertEqual(self.backend.calls, ["get"])

    def test_is_connected_explicit_storage_check_only(self):
        self.assertIs(self.onboarding.is_connected(), False)
        self.backend.saved[ID] = self.candidate
        self.assertIs(self.onboarding.is_connected(), True)
        self.assertEqual(self.validator.calls, [])

    def test_remove_deletes_only_fixed_key(self):
        other = SecretIdentifier("other.credential")
        self.backend.saved[ID] = self.candidate
        untouched = SecretValue("not-deleted")
        self.backend.saved[other] = untouched
        self.assertIs(self.onboarding.remove(), True)
        self.assertIs(self.backend.saved[other], untouched)
        self.assertNotIn(ID, self.backend.saved)
        self.assertEqual(self.backend.calls, ["delete"])
        self.assertIs(self.onboarding.remove(), False)

    def test_backend_error_sanitized_connect(self):
        self.backend.failure = "is_available"
        with self.assertRaisesRegex(SecretStorageError, "^Credential storage operation failed$"):
            self.onboarding.connect(self.candidate)

    def test_backend_error_sanitized_replace_and_test(self):
        self.backend.saved[ID] = self.candidate
        for op, mode in (("put", "replace"), ("get", "test_stored"),
                         ("delete", "remove"), ("is_available", "is_connected")):
            with self.subTest(op=op, mode=mode):
                self.backend.failure = op
                with self.assertRaisesRegex(SecretStorageError,
                                            "^Credential storage operation failed$"):
                    if mode == "replace":
                        self.onboarding.replace(self.candidate)
                    else:
                        getattr(self.onboarding, mode)()
                self.assertNotIn("DO-NOT-LEAK", repr(self.onboarding))

    def test_exact_value_type_before_storage_or_validator(self):
        for method in ("connect", "replace", "test_candidate"):
            for invalid in (SECRET, None, object(), True):
                with self.subTest(method=method, value=type(invalid)), self.assertRaises(TypeError):
                    getattr(self.onboarding, method)(invalid)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.validator.calls, [])

    def test_wrong_bound_identifier_rejected_without_storage(self):
        alien = BoundCredentialLifecycle(self.backend, SecretIdentifier("alien.key"), self.validator)
        with self.assertRaisesRegex(ValueError, "not supported"):
            m.OpenAICredentialOnboarding(alien)
        with self.assertRaises(TypeError):
            m.OpenAICredentialOnboarding(object())
        self.assertEqual(self.backend.calls, [])

    def test_result_redacted_immutable_and_not_serializable(self):
        with self.assertRaises(AttributeError):
            self.onboarding.extra = self.candidate
        with self.assertRaises(AttributeError):
            del self.onboarding._OpenAICredentialOnboarding__lifecycle
        with self.assertRaises(TypeError):
            pickle.dumps(self.onboarding)
        self.assertNotIn(SECRET, repr(self.onboarding))

    def test_internal_dispatch_rejects_unlisted_operation(self):
        with self.assertRaisesRegex(ValueError, "^Unsupported onboarding operation$"):
            self.onboarding._call("export")
        self.assertEqual(self.backend.calls, [])

    def test_source_no_native_backend_import_or_provider_activation(self):
        tree = ast.parse(inspect.getsource(m))
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imported, {"nayeon.secrets.contracts", "nayeon.secrets.lifecycle"})
        source = inspect.getsource(m)
        for forbidden in ("WindowsCredentialBackend", "OpenAICredentialValidator",
                          "OpenAIProvider", "ProviderConnectionFileStore",
                          "compose_provider_ai_service", "create_openai_client",
                          "requests", "httpx", "getenv"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
