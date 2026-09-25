"""Bounded OpenApp observation with fake waits, launches, and snapshots only."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import unittest
from unittest.mock import Mock, call, patch

from nayeon.agent.dispatch import IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.audit.service import AuditEventType
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.service import PolicyService
from nayeon.services.application_observation import (
    ApplicationDefinition, ApplicationIdentity, ApplicationObservation,
    ApplicationReadinessPolicy, ApplicationState, ProcessIdentity,
)
from nayeon.services.applications import ApplicationService, LaunchResult
from nayeon.verification.contract import VerificationStatus
from tests import test_open_app_observation as observation_tests


MATCH = (ProcessIdentity("notepad.exe", r"C:\Trusted\notepad.exe"),)
WRONG = (ProcessIdentity("notepad.exe", r"C:\Other\notepad.exe"),)
UNREADABLE = (ProcessIdentity("notepad.exe", None),)


class ReadinessPolicyTests(unittest.TestCase):
    def test_defaults_are_short_and_immutable(self):
        policy = ApplicationReadinessPolicy()
        self.assertEqual((policy.max_attempts, policy.delay_seconds), (3, 0.1))
        with self.assertRaises(FrozenInstanceError):
            policy.max_attempts = 99

    def test_invalid_attempt_bounds_are_rejected(self):
        for value in (0, -1, 4, 1000, True, 1.0, "3", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ApplicationReadinessPolicy(max_attempts=value)

    def test_invalid_delays_are_rejected(self):
        for value in (-1, 0.11, float("inf"), float("nan"), True, "0.1", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ApplicationReadinessPolicy(delay_seconds=value)

    def test_service_requires_typed_policy_and_callable_sleeper(self):
        for kwargs in ({"readiness": None}, {"readiness": {"max_attempts": 3}}, {"sleeper": None}):
            with self.subTest(kwargs=kwargs), self.assertRaises(TypeError):
                ApplicationService(**kwargs)


class OpenAppReadinessTests(unittest.TestCase):
    execute = observation_tests.OpenAppObservationTests.execute
    protected = observation_tests.OpenAppObservationTests.protected
    approve = observation_tests.OpenAppObservationTests.approve
    session = observation_tests.OpenAppObservationTests.session
    assert_unobserved = observation_tests.OpenAppObservationTests.assert_unobserved

    def setUp(self):
        observation_tests.OpenAppObservationTests.setUp(self)
        # Trusted test-host configuration; every wait still uses the injected Mock.
        self.service._readiness = ApplicationReadinessPolicy()
        self.attempt = self.enterContext(patch.object(
            self.service, "_observe_definition", wraps=self.service._observe_definition))

    def run_sequence(self, snapshots, expected, attempts, sleeps):
        self.snapshot.side_effect = snapshots
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.verification.status, expected)
        self.assertEqual(self.snapshot.call_count, attempts)
        self.assertEqual(self.sleeper.call_args_list, [call(0.1)] * sleeps)
        self.launch.assert_called_once_with("Notepad.EXE")
        self.verify.assert_called_once()
        self.observe.assert_called_once_with("Notepad.EXE")
        return result

    def assert_no_attempts(self):
        self.assert_unobserved()
        self.attempt.assert_not_called()
        self.sleeper.assert_not_called()

    def test_first_attempt_match_stops_without_sleep(self):
        self.run_sequence([MATCH], VerificationStatus.VERIFIED, 1, 0)

    def test_absent_then_match_on_second_attempt(self):
        self.run_sequence([(), MATCH], VerificationStatus.VERIFIED, 2, 1)

    def test_match_on_final_attempt(self):
        self.run_sequence([(), (), MATCH], VerificationStatus.VERIFIED, 3, 2)

    def test_absent_throughout_exhausts_inconclusively(self):
        self.run_sequence([(), (), ()], VerificationStatus.INDETERMINATE, 3, 2)

    def test_wrong_path_then_match_is_verified(self):
        self.run_sequence([WRONG, MATCH], VerificationStatus.VERIFIED, 2, 1)

    def test_only_wrong_path_candidates_preserve_narrow_negative(self):
        self.run_sequence([WRONG, WRONG, WRONG], VerificationStatus.NOT_VERIFIED, 3, 2)

    def test_mismatch_then_absence_cannot_be_negative(self):
        self.run_sequence([WRONG, (), WRONG], VerificationStatus.INDETERMINATE, 3, 2)

    def test_absence_then_mismatches_cannot_be_negative(self):
        self.run_sequence([(), WRONG, WRONG], VerificationStatus.INDETERMINATE, 3, 2)

    def test_unreadable_identity_throughout_is_inconclusive(self):
        self.run_sequence([UNREADABLE] * 3, VerificationStatus.INDETERMINATE, 3, 2)

    def test_unreadable_identity_then_match_can_verify(self):
        self.run_sequence([UNREADABLE, MATCH], VerificationStatus.VERIFIED, 2, 1)

    def test_malformed_identity_path_throughout_is_inconclusive(self):
        bad_path = (ProcessIdentity("notepad.exe", r"C:ambiguous.exe"),)
        self.run_sequence([bad_path] * 3, VerificationStatus.INDETERMINATE, 3, 2)

    def test_access_error_stops_inconclusively_without_retry(self):
        self.run_sequence([PermissionError("fake-sensitive")], VerificationStatus.INDETERMINATE, 1, 0)
        self.assertNotIn("fake-sensitive", repr(self.audit.all()))

    def test_snapshot_exception_stops_inconclusively(self):
        self.run_sequence([OSError("fake")], VerificationStatus.INDETERMINATE, 1, 0)

    def test_exception_after_mismatch_cannot_preserve_negative(self):
        self.run_sequence([WRONG, OSError("fake")], VerificationStatus.INDETERMINATE, 2, 1)

    def test_malformed_snapshot_stops_inconclusively(self):
        self.run_sequence([{"untrusted": "inventory"}], VerificationStatus.INDETERMINATE, 1, 0)

    def test_unsupported_platform_never_observes_or_waits(self):
        with patch("nayeon.services.applications.platform.system", return_value="Linux"):
            self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.attempt.assert_not_called()
        self.sleeper.assert_not_called()

    def test_unsupported_application_never_observes_or_waits(self):
        self.request = StructuredCapabilityRequest("open unknown", {"application": "unknown"})
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.attempt.assert_not_called()
        self.sleeper.assert_not_called()

    def test_missing_metadata_never_observes_or_waits(self):
        self.service._applications["notepad.exe"] = ApplicationDefinition("notepad", ("notepad.exe",))
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.attempt.assert_not_called()
        self.sleeper.assert_not_called()

    def test_malformed_observation_results_cannot_match_or_continue(self):
        valid = ApplicationObservation("Notepad.EXE", ApplicationState.OBSERVED_OPEN,
            "notepad", ("notepad.exe",), ApplicationIdentity.MATCHED)
        for observation in (None, {}, replace(valid, target="other"),
                            replace(valid, application_id="other"),
                            replace(valid, expected_process_names=("other.exe",)),
                            replace(valid, state="observed_open"), replace(valid, identity="matched"),
                            replace(valid, state=ApplicationState.OBSERVED_CLOSED)):
            with self.subTest(observation=observation):
                self.attempt.reset_mock()
                self.attempt.return_value = observation
                self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
                self.attempt.assert_called_once()
                self.sleeper.assert_not_called()

    def test_attempt_provider_exception_is_caught_and_redacted(self):
        self.attempt.side_effect = RuntimeError("fake-private")
        result = self.execute()
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn("fake-private", repr(result.verification))
        self.sleeper.assert_not_called()

    def test_sleeper_exception_stops_without_relaunch(self):
        self.snapshot.return_value = WRONG
        self.sleeper.side_effect = RuntimeError("fake-private")
        result = self.execute()
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.snapshot.assert_called_once()
        self.launch.assert_called_once()
        self.assertNotIn("fake-private", repr(result.verification))

    def test_custom_shorter_bound_limits_observations_and_sleeps(self):
        for attempts in (1, 2, 3):
            with self.subTest(attempts=attempts):
                self.service._readiness = ApplicationReadinessPolicy(attempts, 0.025)
                self.snapshot.return_value = ()
                self.snapshot.reset_mock()
                self.sleeper.reset_mock()
                self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
                self.assertEqual(self.snapshot.call_count, attempts)
                self.assertEqual(self.sleeper.call_args_list, [call(0.025)] * (attempts - 1))

    def test_zero_delay_never_calls_sleeper(self):
        self.service._readiness = ApplicationReadinessPolicy(delay_seconds=0)
        self.run_sequence([(), (), ()], VerificationStatus.INDETERMINATE, 3, 0)

    def test_one_shot_api_retains_no_wait_behavior(self):
        self.snapshot.return_value = ()
        self.assertEqual(self.service.observe("notepad").state, ApplicationState.OBSERVED_CLOSED)
        self.snapshot.assert_called_once()
        self.sleeper.assert_not_called()
        self.launch.assert_not_called()

    def test_failed_launch_has_zero_attempts(self):
        self.launch.side_effect = lambda target: LaunchResult(False, target, "fake")
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.assert_no_attempts()

    def test_launch_exception_has_zero_attempts(self):
        self.launch.side_effect = OSError("fake")
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.assert_no_attempts()

    def test_permission_denial_has_zero_attempts(self):
        self.permissions.revoke("open_app")
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.assert_no_attempts()
        self.launch.assert_not_called()

    def test_policy_denial_has_zero_attempts(self):
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions, {"open_app"}),
                                       ConfirmationService(), self.audit, self.undo)
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.assert_no_attempts()
        self.launch.assert_not_called()

    def test_confirmation_pending_has_zero_attempts(self):
        self.protected()
        self.assertEqual(self.execute().status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assert_no_attempts()
        self.launch.assert_not_called()

    def test_confirmation_approval_executes_once_then_waits(self):
        self.protected()
        pending = self.execute()
        self.assert_no_attempts()
        self.snapshot.side_effect = [(), MATCH]
        result = self.approve(pending)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.launch.assert_called_once()
        self.verify.assert_called_once()
        self.assertEqual(self.snapshot.call_count, 2)
        self.sleeper.assert_called_once_with(0.1)
        self.assertEqual(self.approve(pending).status, ExecutionStatus.DENIED)
        self.assertEqual(self.snapshot.call_count, 2)

    def test_canonical_metadata_and_policy_are_pinned_through_waits(self):
        definition = self.service._applications["notepad.exe"]
        original = deepcopy(definition)
        def change_host_configuration(delay):
            self.service._applications.clear()
            self.service._readiness = ApplicationReadinessPolicy(max_attempts=1)
        self.sleeper.side_effect = change_host_configuration
        self.run_sequence([(), (), MATCH], VerificationStatus.VERIFIED, 3, 2)
        self.assertEqual(definition, original)
        for invocation in self.attempt.call_args_list:
            self.assertEqual(invocation.args[0], "Notepad.EXE")
            self.assertIs(invocation.args[1], definition)

    def test_request_mutation_and_wording_cannot_remap_identity(self):
        self.request = StructuredCapabilityRequest("open an unrelated app", {"application": "notepad.exe"})
        self.sleeper.side_effect = lambda delay: self.request.arguments.update(application="other")
        self.snapshot.side_effect = [(), MATCH]
        with patch.object(OpenAppCapability, "_extract_target", side_effect=AssertionError("No reparse")):
            self.assertEqual(self.execute().verification.status, VerificationStatus.VERIFIED)
        self.assertEqual([c.args[0] for c in self.attempt.call_args_list], ["notepad.exe"] * 2)
        self.launch.assert_called_once_with("notepad.exe")

    def test_legacy_success_retains_receipt_and_launches_once(self):
        receipt = LaunchResult(True, "notepad", "fake")
        self.launch.side_effect = None
        self.launch.return_value = receipt
        self.snapshot.side_effect = [(), MATCH]
        result = self.executor.execute(self.capability, "open notepad")
        self.assertIs(result.output, receipt)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.launch.assert_called_once_with("notepad")
        self.verify.assert_called_once()

    def test_prior_undo_stack_untouched_by_repeated_observations(self):
        callback = Mock()
        self.undo.register(capability="prior", description="prior action", callback=callback)
        self.run_sequence([(), (), MATCH], VerificationStatus.VERIFIED, 3, 2)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()

    def test_audit_is_one_final_safe_outcome(self):
        self.run_sequence([WRONG, WRONG, WRONG], VerificationStatus.NOT_VERIFIED, 3, 2)
        self.assertEqual([e.event_type for e in self.audit.all()], [
            AuditEventType.POLICY_DECISION, AuditEventType.EXECUTION_STARTED,
            AuditEventType.EXECUTION_SUCCEEDED, AuditEventType.VERIFICATION_OUTCOME,
        ])
        self.assertEqual(self.audit.all()[-1].details, {})
        self.assertNotIn("C:\\", repr(self.audit.all()))

    def test_session_approval_does_not_reinterpret_during_waits(self):
        self.protected()
        session = self.session()
        session.request("open notepad")
        self.assert_no_attempts()
        self.snapshot.side_effect = [(), (), MATCH]
        with patch.object(IntentResolver, "resolve", side_effect=AssertionError("No resolve")), \
                patch.object(IntentDispatcher, "plan", side_effect=AssertionError("No dispatch")):
            self.assertEqual(session.approve_pending().verification.status, VerificationStatus.VERIFIED)
        self.launch.assert_called_once_with("notepad")
        self.verify.assert_called_once()
        self.assertEqual(self.snapshot.call_count, 3)
        self.assertFalse(session.has_pending)

    def test_session_cancellation_never_waits(self):
        self.protected()
        session = self.session()
        session.request("open notepad")
        session.request("cancel that")
        self.assert_no_attempts()
        self.launch.assert_not_called()
