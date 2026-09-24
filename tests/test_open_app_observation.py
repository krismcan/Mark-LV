"""Real OpenApp/trust boundaries with fake launch and fake process observation."""

from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from nayeon.agent.dispatch import IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities.open_app import ApplicationLaunchError, OpenAppCapability
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.services.application_observation import ApplicationObservation, ApplicationState
from nayeon.services.applications import ApplicationService, LaunchResult
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationStatus


class OpenAppObservationTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nayeon.services.applications.platform.system", return_value="Windows"))
        self.snapshot = self.enterContext(patch("nayeon.services.applications.windows_process_names",
                                               return_value=frozenset({"notepad.exe", "unrelated.exe"})))
        self.service = ApplicationService()
        self.launch = self.enterContext(patch.object(self.service, "launch",
            side_effect=lambda target: LaunchResult(True, target, "Fake launch receipt")))
        self.observe = self.enterContext(patch.object(self.service, "observe", wraps=self.service.observe))
        self.app = OpenAppCapability(service=self.service)
        self.verify = self.enterContext(patch.object(self.app, "verify_result", wraps=self.app.verify_result))
        self.capability = self.app.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.capability, self.app)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("open_app")
        self.policy = PolicyService(self.permissions)
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, ConfirmationService(), self.audit, self.undo)
        self.request = StructuredCapabilityRequest("please open my editor", {"application": " Notepad.EXE "})

    def execute(self):
        return self.executor.execute_structured(self.capability, self.request)

    def protected(self):
        self.capability = replace(self.capability, requires_confirmation=True)
        self.registry.unregister("open_app")
        self.registry.register(self.capability, self.app)

    def approve(self, pending):
        return self.executor.approve_and_execute_structured(
            pending.confirmation_request.token, capability=self.capability, request=self.request,
        )

    def assert_unobserved(self):
        self.verify.assert_not_called()
        self.observe.assert_not_called()
        self.snapshot.assert_not_called()
        self.assertNotIn(AuditEventType.VERIFICATION_OUTCOME,
                         [event.event_type for event in self.audit.all()])

    def test_successful_launch_with_positive_observation_is_verified(self):
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(result.verification.evidence, {"application_id": "notepad",
            "state": "observed_open", "expected_process_names": ["notepad.exe"]})
        self.launch.assert_called_once_with("Notepad.EXE")
        self.snapshot.assert_called_once_with()

    def test_successful_launch_with_immediate_absence_is_indeterminate(self):
        self.snapshot.return_value = frozenset({"system", "unrelated.exe"})
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.snapshot.assert_called_once_with()
        self.assertEqual(self.audit.all()[-1].outcome, "indeterminate")
        self.assertEqual(self.undo.count(), 0)

    def test_failed_receipt_raises_typed_error_in_both_capability_paths(self):
        self.launch.side_effect = lambda target: LaunchResult(False, target, "fake-sensitive-error")
        for execute in (lambda: self.app.execute("open notepad"),
                        lambda: self.app.execute_structured({"application": "notepad"})):
            with self.subTest(execute=execute):
                with self.assertRaises(ApplicationLaunchError) as caught:
                    execute()
                self.assertEqual(str(caught.exception), "Application launch failed.")
        self.assert_unobserved()

    def test_legacy_immediate_absence_is_indeterminate(self):
        self.snapshot.return_value = frozenset({"unrelated.exe"})
        result = self.executor.execute(self.capability, "open notepad")
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.snapshot.assert_called_once_with()

    def test_approved_launch_with_immediate_absence_is_indeterminate(self):
        self.protected()
        pending = self.execute()
        self.assert_unobserved()
        self.snapshot.return_value = frozenset({"unrelated.exe"})
        result = self.approve(pending)
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.launch.assert_called_once()
        self.snapshot.assert_called_once_with()

    def test_unknown_observation_is_indeterminate(self):
        self.snapshot.return_value = None
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_unsupported_target_has_no_process_inference(self):
        self.request = StructuredCapabilityRequest("open my editor", {"application": "my notepad"})
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.snapshot.assert_not_called()

    def test_unsupported_platform_is_indeterminate(self):
        with patch("nayeon.services.applications.platform.system", return_value="Darwin"):
            self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.snapshot.assert_not_called()

    def test_observation_exception_is_indeterminate_and_redacted(self):
        self.observe.side_effect = RuntimeError("fake-private-inventory")
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn("fake-private-inventory", repr(result.verification))
        self.assertNotIn("fake-private-inventory", repr(self.audit.all()))

    def test_malformed_observation_is_indeterminate(self):
        for observation in (None, True, {"state": "observed_open"},
                            ApplicationObservation("Notepad.EXE", "observed_open", "notepad", ("notepad.exe",)),
                            ApplicationObservation("other", ApplicationState.OBSERVED_OPEN, "notepad", ("notepad.exe",))):
            with self.subTest(observation=observation):
                self.observe.return_value = observation
                self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_missing_or_unsafe_observation_metadata_is_indeterminate(self):
        for identity, names in ((None, ()), ("notepad", ()), ("../unsafe", ("notepad.exe",)),
                                ("notepad", ("*.exe",))):
            with self.subTest(identity=identity, names=names):
                self.observe.return_value = ApplicationObservation(
                    "Notepad.EXE", ApplicationState.OBSERVED_CLOSED, identity, names,
                )
                self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_missing_observation_provider_is_indeterminate(self):
        self.observe.side_effect = AttributeError("No observation implementation")
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)

    def test_failed_launch_is_failed_without_verification(self):
        self.launch.side_effect = lambda target: LaunchResult(False, target, "fake-sensitive-error")
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assert_unobserved()
        self.assertEqual([event.event_type for event in self.audit.all()], [
            AuditEventType.POLICY_DECISION, AuditEventType.EXECUTION_STARTED, AuditEventType.EXECUTION_FAILED,
        ])
        self.assertNotIn("fake-sensitive-error", repr(self.audit.all()))

    def test_launch_exception_is_failed_without_verification(self):
        self.launch.side_effect = OSError("fake launch error")
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.assert_unobserved()

    def test_service_os_launch_failure_reaches_executor_as_failed(self):
        self.launch.side_effect = lambda target: ApplicationService.launch(self.service, target)
        with patch("nayeon.services.applications.Path.exists", return_value=False), \
                patch("nayeon.services.applications.subprocess.Popen", side_effect=OSError("fake failure")):
            self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.assert_unobserved()

    def test_service_successful_launch_behavior_remains_compatible(self):
        self.launch.side_effect = lambda target: ApplicationService.launch(self.service, target)
        with patch("nayeon.services.applications.Path.exists", return_value=False), \
                patch("nayeon.services.applications.subprocess.Popen") as popen:
            result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertIsInstance(result.output, LaunchResult)
        self.assertTrue(result.output.success)
        self.assertEqual(popen.call_args.args, (["Notepad.EXE"],))
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)

    def test_denied_permission_does_not_verify(self):
        self.permissions.revoke("open_app")
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.launch.assert_not_called()
        self.assert_unobserved()

    def test_policy_block_does_not_verify(self):
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions, {"open_app"}),
                                       ConfirmationService(), self.audit, self.undo)
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.assert_unobserved()

    def test_pending_confirmation_does_not_verify(self):
        self.protected()
        self.assertEqual(self.execute().status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.launch.assert_not_called()
        self.assert_unobserved()

    def test_approved_confirmation_launches_then_observes_once(self):
        self.protected()
        pending = self.execute()
        order = []
        self.launch.side_effect = lambda target: (order.append("launch") or LaunchResult(True, target, "fake"))
        original_observe = self.observe._mock_wraps
        self.observe.side_effect = lambda target: (order.append("observe") or original_observe(target))
        self.assertEqual(self.approve(pending).verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(order, ["launch", "observe"])
        self.assertEqual(self.approve(pending).status, ExecutionStatus.DENIED)
        self.observe.assert_called_once()

    def test_normalized_identity_used_without_reparsing_and_without_mutation(self):
        original = deepcopy(self.request)
        with patch.object(OpenAppCapability, "_extract_target", side_effect=AssertionError("No reparse")):
            result = self.execute()
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.observe.assert_called_once_with("Notepad.EXE")
        self.assertEqual(self.request, original)

    def test_mismatched_launch_receipt_does_not_observe(self):
        self.launch.side_effect = lambda target: LaunchResult(True, "other", "fake receipt")
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.observe.assert_not_called()

    def test_unknown_launch_output_is_indeterminate_without_observation(self):
        self.launch.side_effect = None
        self.launch.return_value = object()
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.observe.assert_not_called()

    def test_audit_preserves_order_without_inventory_or_evidence(self):
        self.execute()
        self.assertEqual([event.event_type for event in self.audit.all()], [
            AuditEventType.POLICY_DECISION, AuditEventType.EXECUTION_STARTED,
            AuditEventType.EXECUTION_SUCCEEDED, AuditEventType.VERIFICATION_OUTCOME,
        ])
        event = self.audit.all()[-1]
        self.assertEqual(event.outcome, "verified")
        self.assertEqual(event.details, {})
        self.assertNotIn("unrelated.exe", repr(self.audit.all()))
        self.assertNotIn("please open my editor", repr(self.audit.all()))
        self.assertEqual(self.undo.count(), 0)

    def test_legacy_success_preserves_receipt_and_uses_executed_target(self):
        receipt = LaunchResult(True, "notepad", "fake")
        self.launch.side_effect = None
        self.launch.return_value = receipt
        result = self.executor.execute(self.capability, "launch notepad")
        self.assertTrue(result.succeeded)
        self.assertIs(result.output, receipt)
        self.observe.assert_called_once_with("notepad")
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)

    def test_legacy_failed_launch_now_fails_without_verification(self):
        self.launch.side_effect = lambda target: LaunchResult(False, target, "fake-sensitive")
        result = self.executor.execute(self.capability, "open notepad")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assert_unobserved()
        self.assertNotIn("fake-sensitive", repr(result))

    def session(self):
        resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)))
        return ConversationSession(resolver=resolver, registry=self.registry, executor=self.executor)

    def test_session_approval_keeps_exact_stored_request(self):
        self.protected()
        session = self.session()
        session.request("open notepad")
        self.assert_unobserved()
        with patch.object(IntentResolver, "resolve", side_effect=AssertionError("No reinterpretation")), \
                patch.object(IntentDispatcher, "plan", side_effect=AssertionError("No replan")):
            self.assertEqual(session.approve_pending().verification.status, VerificationStatus.VERIFIED)
        self.observe.assert_called_once_with("notepad")
        self.assertFalse(session.has_pending)

    def test_session_cancel_does_not_observe(self):
        self.protected()
        session = self.session()
        session.request("open notepad")
        self.assertEqual(session.request("cancel that").status, ExecutionStatus.DENIED)
        self.assertFalse(session.has_pending)
        self.assert_unobserved()
