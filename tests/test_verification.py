"""Deterministic observations distinguish execution from the requested outcome."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.dispatch import IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionResult, ExecutionStatus
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.undo.contract import UndoRegistration
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationProvider, VerificationResult, VerificationStatus
from nayeon.verification.service import VerificationService


class ObservedFake:
    def __init__(self):
        self.execute = Mock(return_value={"receipt": "fake"})
        self.execute_structured = Mock(return_value={"receipt": "fake"})
        self.verify_result = Mock(return_value=VerificationResult(
            VerificationStatus.VERIFIED, "Observed the requested fake state.",
            {"observed": True},
        ))
        self.restore = Mock()
        self.build_undo = Mock(return_value=UndoRegistration("Restore fake", self.restore))

    def validate_arguments(self, arguments):
        if not isinstance(arguments.get("application"), str) or not arguments["application"].strip():
            raise ValueError("Application required")
        return {"application": arguments["application"].strip()}


class VerificationContractTests(unittest.TestCase):
    def test_safe_default_is_indeterminate(self):
        result = ExecutionResult(ExecutionStatus.EXECUTED, "fake", "returned")
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)

    def test_invalid_status_or_reason_is_rejected(self):
        for status, reason in (("verified", "reason"), (True, "reason"),
                               (VerificationStatus.VERIFIED, " "),
                               (VerificationStatus.VERIFIED, None)):
            with self.subTest(status=status, reason=reason), self.assertRaises((TypeError, ValueError)):
                VerificationResult(status, reason)

    def test_evidence_is_copied_recursively(self):
        evidence = {"check": {"observations": [True, None, 1, 1.5, "fake"]}}
        result = VerificationResult(evidence=evidence)
        evidence["check"]["observations"].append("changed")
        self.assertEqual(result.evidence["check"]["observations"], [True, None, 1, 1.5, "fake"])

    def test_non_json_evidence_is_rejected(self):
        for evidence in ([], {"value": object()}, {"value": float("nan")},
                         {"value": float("inf")}, {"nested": {1: "value"}},
                         {"callback": lambda: None}):
            with self.subTest(evidence=evidence), self.assertRaises(TypeError):
                VerificationResult(evidence=evidence)

    def test_optional_protocol_detection_does_not_invoke_provider(self):
        provider = ObservedFake()
        self.assertIsInstance(provider, VerificationProvider)
        self.assertNotIsInstance(object(), VerificationProvider)
        provider.verify_result.assert_not_called()

    def test_coordinator_revalidates_mutated_provider_evidence(self):
        provider = ObservedFake()
        provider.verify_result.return_value.evidence["opaque"] = object()
        result = VerificationService().verify(provider, request="fake", output=None)
        self.assertEqual(result.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(result.evidence, {})


class VerificationExecutionTests(unittest.TestCase):
    def setUp(self):
        self.fake = ObservedFake()
        self.capability = Capability("open_app", "Fake observation", ExecutionMode.LOCAL,
                                     "fake", intent_patterns=("open ",))
        self.registry = CapabilityRegistry()
        self.registry.register(self.capability, self.fake)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("open_app")
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions),
                                       self.confirmation, self.audit, self.undo)
        self.request = StructuredCapabilityRequest("open App", {"application": " App "})

    def configure(self, **changes):
        self.capability = replace(self.capability, **changes)
        self.registry.unregister("open_app")
        self.registry.register(self.capability, self.fake)

    def execute(self):
        return self.executor.execute_structured(self.capability, self.request)

    def approve(self, pending):
        return self.executor.approve_and_execute_structured(
            pending.confirmation_request.token, capability=self.capability, request=self.request,
        )

    def assert_not_observed(self, result):
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.fake.verify_result.assert_not_called()
        self.assertNotIn(AuditEventType.VERIFICATION_OUTCOME,
                         [event.event_type for event in self.audit.all()])

    def test_success_with_verified_observation(self):
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(result.verification.evidence, {"observed": True})
        self.fake.execute_structured.assert_called_once_with({"application": "App"})
        self.fake.verify_result.assert_called_once()
        self.fake.execute.assert_not_called()

    def test_success_with_not_verified_observation_preserves_execution(self):
        self.fake.verify_result.return_value = VerificationResult(
            VerificationStatus.NOT_VERIFIED, "Requested fake state was absent.", {"observed": False},
        )
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.verification.status, VerificationStatus.NOT_VERIFIED)
        self.assertEqual(result.output, {"receipt": "fake"})

    def test_success_with_inconclusive_observation(self):
        self.fake.verify_result.return_value = VerificationResult(reason="No conclusive evidence.")
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)

    def test_no_provider_never_means_verified(self):
        del self.fake.verify_result
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertIn("No verification provider", result.verification.reason)

    def test_execution_failure_does_not_verify(self):
        self.fake.execute_structured.side_effect = RuntimeError("fake execution failure")
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assert_not_observed(result)

    def test_verifier_exception_is_inconclusive_and_redacted(self):
        self.fake.verify_result.side_effect = RuntimeError("fake-sensitive-value")
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertNotIn("fake-sensitive-value", repr(result))
        self.assertNotIn("fake-sensitive-value", repr(self.audit.all()))
        self.fake.execute_structured.assert_called_once()

    def test_malformed_verifier_return_is_inconclusive(self):
        for value in (None, True, {"status": "verified"}, "verified"):
            with self.subTest(value=value):
                self.fake.verify_result.return_value = value
                result = self.execute()
                self.assertTrue(result.succeeded)
                self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)

    def test_verifier_receives_exact_normalized_request_after_execution(self):
        order = []
        self.fake.execute_structured.side_effect = lambda args: (order.append("execute") or "receipt")
        expected = self.fake.verify_result.return_value

        def observe(*, request, output):
            order.append("verify")
            self.assertEqual(request.original_request, "open App")
            self.assertEqual(request.arguments, {"application": "App"})
            self.assertEqual(output, "receipt")
            return expected

        self.fake.verify_result.side_effect = observe
        self.assertEqual(self.execute().verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(order, ["execute", "verify"])

    def test_execution_and_verifier_mutations_are_isolated(self):
        # Nested arguments exercise isolation beyond OpenApp's current string schema.
        self.fake.validate_arguments = deepcopy
        self.request = StructuredCapabilityRequest("nested fake", {"nested": {"value": "original"}})
        output = {"nested": {"receipt": "original"}}
        expected = self.fake.verify_result.return_value

        def execute(arguments):
            arguments["nested"]["value"] = "execution mutation"
            self.request.arguments["nested"]["value"] = "caller mutation"
            return output

        def observe(*, request, output):
            self.assertEqual(request.arguments, {"nested": {"value": "original"}})
            request.arguments["nested"]["value"] = "observer mutation"
            output["nested"]["receipt"] = "observer mutation"
            return expected

        self.fake.execute_structured.side_effect = execute
        self.fake.verify_result.side_effect = observe
        result = self.execute()
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(result.output, {"nested": {"receipt": "original"}})
        self.assertEqual(self.request.arguments["nested"]["value"], "caller mutation")

    def test_provider_result_mutation_cannot_change_returned_evidence(self):
        provider_result = VerificationResult(VerificationStatus.VERIFIED, "Observed.",
                                              {"nested": {"seen": [True]}})
        self.fake.verify_result.return_value = provider_result
        result = self.execute()
        provider_result.evidence["nested"]["seen"].append(False)
        self.assertEqual(result.verification.evidence, {"nested": {"seen": [True]}})

    def test_uncopyable_output_is_inconclusive_not_execution_failure(self):
        class Uncopyable:
            def __deepcopy__(self, memo):
                raise ValueError("fake-sensitive-value")

        output = Uncopyable()
        self.fake.execute_structured.return_value = output
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertIs(result.output, output)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.fake.verify_result.assert_not_called()

    def test_confirmation_verifies_only_once_after_approved_execution(self):
        self.configure(requires_confirmation=True)
        pending = self.execute()
        self.assert_not_observed(pending)
        self.fake.execute_structured.assert_not_called()
        self.assertEqual(self.approve(pending).verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.approve(pending).status, ExecutionStatus.DENIED)
        self.fake.verify_result.assert_called_once()
        self.fake.execute_structured.assert_called_once()

    def test_rejected_action_does_not_verify(self):
        self.configure(requires_confirmation=True)
        pending = self.execute()
        self.executor.reject(pending.confirmation_request.token, capability=self.capability)
        self.assert_not_observed(self.approve(pending))

    def test_denied_permission_does_not_verify(self):
        self.permissions.revoke("open_app")
        self.assert_not_observed(self.execute())
        self.fake.execute_structured.assert_not_called()

    def test_revoked_permission_before_approval_does_not_verify(self):
        self.configure(requires_confirmation=True)
        pending = self.execute()
        self.permissions.revoke("open_app")
        self.assert_not_observed(self.approve(pending))

    def test_invalid_arguments_do_not_verify(self):
        self.request.arguments["application"] = " "
        self.assert_not_observed(self.execute())
        self.fake.execute_structured.assert_not_called()

    def test_expired_confirmation_does_not_verify(self):
        self.configure(requires_confirmation=True)
        pending = self.execute()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = pending.confirmation_request.expires_at + timedelta(seconds=1)
            self.assert_not_observed(self.approve(pending))

    def test_changed_registration_before_approval_does_not_verify(self):
        self.configure(requires_confirmation=True)
        pending = self.execute()
        replacement = ObservedFake()
        self.registry.unregister("open_app")
        self.registry.register(self.capability, replacement)
        self.assert_not_observed(self.approve(pending))
        replacement.verify_result.assert_not_called()

    def test_verification_uses_implementation_that_executed(self):
        replacement = ObservedFake()

        def execute(arguments):
            self.registry.unregister("open_app")
            self.registry.register(self.capability, replacement)
            return "fake output"

        self.fake.execute_structured.side_effect = execute
        self.execute()
        self.fake.verify_result.assert_called_once()
        replacement.verify_result.assert_not_called()

    def test_undo_registration_precedes_verification_and_is_preserved(self):
        self.configure(reversible=True)
        self.fake.verify_result.side_effect = RuntimeError("fake observation failure")
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(self.undo.count(), 1)
        self.assertEqual([event.event_type for event in self.audit.all()], [
            AuditEventType.POLICY_DECISION, AuditEventType.EXECUTION_STARTED,
            AuditEventType.EXECUTION_SUCCEEDED, AuditEventType.UNDO_REGISTERED,
            AuditEventType.VERIFICATION_OUTCOME,
        ])
        self.assertTrue(self.undo.undo_last().success)
        self.fake.restore.assert_called_once()

    def test_undo_registration_failure_still_verifies_without_rewriting_execution(self):
        self.configure(reversible=True)
        self.fake.build_undo.side_effect = RuntimeError("fake undo-registration failure")
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertIn("undo could not be registered", result.message)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.undo.count(), 0)
        self.assertEqual([event.event_type for event in self.audit.all()][-2:],
                         [AuditEventType.UNDO_REGISTRATION_FAILED, AuditEventType.VERIFICATION_OUTCOME])

    def test_legacy_execution_and_verification_preserve_string_request(self):
        result = self.executor.execute(self.capability, "  legacy request  ")
        self.assertTrue(result.succeeded)
        self.fake.execute.assert_called_once_with("  legacy request  ")
        self.fake.verify_result.assert_called_once_with(request="  legacy request  ",
                                                        output={"receipt": "fake"})
        self.fake.execute_structured.assert_not_called()

    def test_open_app_return_remains_unverified_without_real_observation(self):
        with patch("nayeon.capabilities.open_app.ApplicationService") as service:
            implementation = OpenAppCapability()
            self.registry.unregister("open_app")
            self.registry.register(implementation.capability, implementation)
            result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        service.return_value.launch.assert_called_once_with("App")

    def test_audit_records_status_only_not_reason_evidence_request_or_output(self):
        self.fake.verify_result.return_value = VerificationResult(
            VerificationStatus.NOT_VERIFIED, "fake-sensitive-reason", {"private": "fake-evidence"},
        )
        result = self.execute()
        event = self.audit.all()[-1]
        self.assertEqual(event.event_type, AuditEventType.VERIFICATION_OUTCOME)
        self.assertEqual(event.outcome, "not_verified")
        self.assertEqual(event.details, {})
        for value in ("fake-sensitive-reason", "fake-evidence", "open App", "receipt"):
            self.assertNotIn(value, repr(event))
        self.assertEqual(result.verification.reason, "fake-sensitive-reason")

    def session(self):
        # Session participation now opts into mapping; direct executor fakes do not need it.
        self.fake.map_intent_arguments = Mock(side_effect=OpenAppCapability(service=Mock()).map_intent_arguments)
        resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)))
        return ConversationSession(resolver=resolver, registry=self.registry, executor=self.executor)

    def test_session_approval_verifies_stored_action_without_reinterpretation(self):
        self.configure(requires_confirmation=True)
        session = self.session()
        pending = session.request("open App")
        self.assertEqual(pending.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assert_not_observed(pending)
        self.fake.map_intent_arguments.assert_called_once()
        self.fake.map_intent_arguments.side_effect = AssertionError("No remapping")
        with patch.object(IntentResolver, "resolve", side_effect=AssertionError("No reinterpretation")), \
                patch.object(IntentDispatcher, "plan", side_effect=AssertionError("No replanning")):
            result = session.approve_pending()
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.fake.verify_result.call_args.kwargs["request"].arguments,
                         {"application": "App"})
        self.assertFalse(session.has_pending)

    def test_session_cancellation_does_not_verify(self):
        self.configure(requires_confirmation=True)
        session = self.session()
        self.assertEqual(session.request("open App").status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assert_not_observed(session.request("cancel that"))
        self.assertFalse(session.has_pending)
        self.fake.execute_structured.assert_not_called()
