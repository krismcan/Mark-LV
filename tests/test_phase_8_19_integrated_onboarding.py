"""Phase 8.19: integrated simulated human credential onboarding acceptance.

Fake backend and validator only. No real key store, live API, model, GUI or
production credential path. Validate the actual sealed orchestration seams.
"""
import tempfile
from pathlib import Path
import unittest

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import (
    ConnectionObservationStatus as State, observe_connection,
)
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.credential_operation_host import (
    CredentialHostOutcome as Outcome, TrustedCredentialOperationHost,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.brain.onboarding_review_session import OnboardingReviewSession
from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretValue,
)
from nayeon.secrets.lifecycle import BoundCredentialLifecycle, CredentialValidationStatus


KEY = SecretIdentifier("openai.api_key")
GOOD = "synthetic-valid-fixture-not-an-api-key"


class FakeBackend:
    def __init__(self):
        self.value = None
        self.probes = 0
        self.gets = 0
        self.puts = 0
        self.deletes = 0
        self.on_probe = None
        self.fail_put = False
        self.fail_probe = False

    def is_available(self, identifier):
        assert identifier == KEY
        self.probes += 1
        if self.fail_probe:
            raise RuntimeError("synthetic-sensitive-backend-error")
        if self.on_probe is not None:
            self.on_probe()
        return self.value is not None

    def get(self, identifier):
        assert identifier == KEY
        self.gets += 1
        if self.value is None:
            raise SecretNotFoundError("fixture only")
        return self.value

    def put(self, identifier, value):
        assert identifier == KEY and type(value) is SecretValue
        if self.fail_put:
            raise RuntimeError("synthetic-sensitive-backend-error")
        self.puts += 1
        self.value = value

    def delete(self, identifier):
        assert identifier == KEY
        self.deletes += 1
        present = self.value is not None
        self.value = None
        return present


class FakeValidator:
    def __init__(self):
        self.calls = 0

    def validate(self, value):
        self.calls += 1
        return (CredentialValidationStatus.VALID
                if type(value) is SecretValue and value.reveal() == GOOD
                else CredentialValidationStatus.INVALID)


class IntegratedOnboardingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "provider-connection.json"
        self.store = ProviderConnectionFileStore(self.path)
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.clock = [10.0]
        lifecycle = BoundCredentialLifecycle(self.backend, KEY, self.validator)
        onboarding = OpenAICredentialOnboarding(lifecycle)
        review = OnboardingReviewSession(clock=lambda: self.clock[0], timeout_seconds=3.0)
        self.host = TrustedCredentialOperationHost(
            onboarding=onboarding,
            observe=lambda: observe_connection(self.path, self.backend),
            review=review,
        )

    def configure(self, provider="openai", model="gpt-5.6", key=KEY):
        self.store.save(ProviderConnectionDocumentV1(
            connection=ProviderConnectionConfiguration(provider, model, key)))

    def state(self):
        return observe_connection(self.path, self.backend).status

    def test_setup_connect_then_metadata_stays_separate(self):
        self.assertEqual(self.state(), State.SETUP_REQUIRED)
        self.assertTrue(self.host.request(Op.CONNECT))
        self.assertEqual((self.backend.puts, self.validator.calls), (0, 0))
        response = self.host.approve(candidate=SecretValue(GOOD))
        self.assertIs(response.outcome, Outcome.SUBMITTED)
        self.assertFalse(response.confirms_durable_storage)
        self.assertEqual((self.backend.puts, self.validator.calls), (1, 1))
        self.assertEqual(self.state(), State.UNCONFIGURED_CREDENTIAL_PRESENT)
        self.assertFalse(self.path.exists())
        self.assertIsNone(self.host.approve(candidate=SecretValue(GOOD)))

    def test_explicit_metadata_connection_replace_test_remove(self):
        self.configure()
        before = self.path.read_bytes()
        self.assertEqual(self.state(), State.CREDENTIAL_REQUIRED)
        self.assertTrue(self.host.request(Op.CONNECT))
        self.assertIs(self.host.approve(candidate=SecretValue(GOOD)).outcome,
                      Outcome.SUBMITTED)
        self.assertEqual(self.state(), State.VALIDATION_REQUIRED)
        self.assertTrue(self.host.request(Op.TEST_STORED))
        self.assertIs(self.host.approve().outcome, Outcome.SUBMITTED)
        old = self.backend.value
        self.assertTrue(self.host.request(Op.REPLACE))
        self.assertIs(self.host.approve(candidate=SecretValue("wrong")).outcome,
                      Outcome.INVALID)
        self.assertIs(self.backend.value, old)
        self.assertTrue(self.host.request(Op.REPLACE))
        self.assertIs(self.host.approve(candidate=SecretValue(GOOD)).outcome,
                      Outcome.SUBMITTED)
        self.assertTrue(self.host.request(Op.REMOVE))
        self.assertIs(self.host.approve().outcome, Outcome.SUBMITTED)
        self.assertEqual(self.state(), State.CREDENTIAL_REQUIRED)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.backend.deletes, 1)

    def test_reject_and_expiry_cannot_mutate(self):
        self.assertTrue(self.host.request(Op.CONNECT))
        self.assertIs(self.host.reject().outcome, Outcome.BLOCKED)
        self.assertEqual(self.backend.puts, 0)
        self.assertTrue(self.host.request(Op.CONNECT))
        self.clock[0] = 14.0
        self.assertIs(self.host.approve(candidate=SecretValue(GOOD)).outcome,
                      Outcome.BLOCKED)
        self.assertEqual((self.backend.puts, self.validator.calls), (0, 0))

    def test_invalid_candidate_never_persisted(self):
        self.assertTrue(self.host.request(Op.CONNECT))
        result = self.host.approve(candidate=SecretValue("synthetic-invalid"))
        self.assertIs(result.outcome, Outcome.INVALID)
        self.assertEqual((self.backend.puts, self.validator.calls), (0, 1))
        self.assertEqual(self.state(), State.SETUP_REQUIRED)

    def test_unexpected_credential_before_approval_is_blocked(self):
        self.assertTrue(self.host.request(Op.CONNECT))
        self.backend.value = SecretValue("synthetic-external-change")
        self.assertIs(self.host.approve(candidate=SecretValue(GOOD)).outcome,
                      Outcome.BLOCKED)
        self.assertEqual(self.backend.puts, 0)
        self.assertEqual(self.state(), State.UNCONFIGURED_CREDENTIAL_PRESENT)

    def test_unsupported_metadata_never_probes_or_mutates_key(self):
        self.configure(provider="another-provider")
        self.assertEqual(self.state(), State.UNSUPPORTED_CONFIGURATION)
        self.assertEqual(self.backend.probes, 0)
        self.assertFalse(self.host.request(Op.CONNECT))
        self.assertFalse(self.host.request(Op.REMOVE))
        self.assertEqual((self.backend.probes, self.backend.puts, self.backend.deletes),
                         (0, 0, 0))

    def test_changed_during_observation_blocks_operation(self):
        self.configure(model="model-a")
        self.backend.on_probe = lambda: self.configure(model="model-b")
        self.assertEqual(self.state(), State.CHANGED_DURING_OBSERVATION)
        # The probe above changed the fixture. Restore A so the host itself
        # observes a fresh A -> B change, rather than the settled B state.
        self.configure(model="model-a")
        self.assertFalse(self.host.request(Op.CONNECT))
        self.assertFalse(self.host.has_pending)
        self.assertEqual(self.backend.puts, 0)

    def test_probe_failure_blocks_and_cannot_leak_details(self):
        self.backend.fail_probe = True
        self.assertEqual(self.state(), State.UNKNOWN)
        self.assertFalse(self.host.request(Op.CONNECT))
        self.assertEqual(self.backend.puts, 0)

    def test_write_failure_is_indeterminate_without_secret_echo(self):
        self.backend.fail_put = True
        self.assertTrue(self.host.request(Op.CONNECT))
        result = self.host.approve(candidate=SecretValue(GOOD))
        self.assertIs(result.outcome, Outcome.INDETERMINATE)
        self.assertFalse(result.confirms_durable_storage)
        self.assertNotIn("synthetic-sensitive", repr(result))
        self.assertNotIn(GOOD, repr(self.host))
        self.assertEqual((self.backend.puts, self.backend.gets), (0, 0))

    def test_candidate_test_does_not_save_or_create_metadata(self):
        self.assertTrue(self.host.request(Op.TEST_CANDIDATE))
        self.assertIs(self.host.approve(candidate=SecretValue(GOOD)).outcome,
                      Outcome.SUBMITTED)
        self.assertEqual((self.backend.puts, self.backend.gets), (0, 0))
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
