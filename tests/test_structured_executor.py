"""Structured execution uses real policy/confirmation with deterministic fakes."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.undo.contract import UndoRegistration

from nayeon.undo.service import UndoService


class StructuredFake:
    def __init__(self):
        self.execute = Mock(side_effect=AssertionError("Legacy path must not be used"))
        self.execute_structured = Mock(return_value={"completed": "example"})
        self.validate_arguments = Mock(side_effect=self.validate)
        self.restore = Mock()
        self.build_undo = Mock(return_value=UndoRegistration("Restore fake", self.restore))

    @staticmethod
    def validate(arguments):
        if set(arguments) != {"application"} or not isinstance(arguments["application"], str):
            raise ValueError("Invalid fake arguments")
        if not arguments["application"].strip():
            raise ValueError("Blank fake application")
        return {"application": arguments["application"].strip()}


class StructuredExecutorTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.fake = StructuredFake()
        self.capability = Capability("example", "Test", ExecutionMode.LOCAL, "fake")
        self.registry.register(self.capability, self.fake)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("example")
        self.policy = PolicyService(self.permissions)
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, self.policy, self.confirmation,
                                       self.audit, self.undo)
        self.request = StructuredCapabilityRequest("open requested app", {"application": " app "})

    def configure(self, **changes):
        self.capability = replace(self.capability, **changes)
        self.registry.unregister("example")
        self.registry.register(self.capability, self.fake)

    def execute(self):
        return self.executor.execute_structured(self.capability, self.request)

    def pending(self):
        self.configure(requires_confirmation=True)
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.fake.execute_structured.assert_not_called()
        return result.confirmation_request

    def approve(self, token, request=None):
        return self.executor.approve_and_execute_structured(
            token, capability=self.capability,
            request=self.request if request is None else request,
        )

    def events(self):
        return [event.event_type for event in self.audit.all()]

    def test_permitted_action_executes_validated_arguments(self):
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.fake.execute_structured.assert_called_once_with({"application": "app"})
        self.fake.execute.assert_not_called()
        self.assertEqual(self.events(), [AuditEventType.POLICY_DECISION,
                         AuditEventType.EXECUTION_STARTED, AuditEventType.EXECUTION_SUCCEEDED])

    def test_validation_precedes_permission_policy(self):
        calls = []
        self.fake.validate_arguments.side_effect = lambda args: (calls.append("validate") or args)
        with patch.object(self.policy, "evaluate", wraps=self.policy.evaluate) as evaluate:
            evaluate.side_effect = lambda capability: (
                calls.append("policy") or PolicyService(self.permissions).evaluate(capability)
            )
            self.execute()
        self.assertEqual(calls, ["validate", "policy"])

    def test_denied_permission_prevents_execution(self):
        self.permissions.revoke("example")
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()
        self.assertEqual(self.events(), [AuditEventType.POLICY_DECISION])

    def test_policy_block_prevents_execution(self):
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions, {"example"}),
                                       self.confirmation, self.audit, self.undo)
        self.assertEqual(self.execute().status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_confirmation_matching_approval_executes_once_and_replay_denied(self):
        pending = self.pending()
        self.assertTrue(self.approve(pending.token).succeeded)
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_called_once_with({"application": "app"})
        self.assertEqual(self.events()[:6], [
            AuditEventType.POLICY_DECISION, AuditEventType.CONFIRMATION_CREATED,
            AuditEventType.CONFIRMATION_APPROVED, AuditEventType.POLICY_DECISION,
            AuditEventType.EXECUTION_STARTED, AuditEventType.EXECUTION_SUCCEEDED,
        ])

    def test_changed_arguments_consume_and_reject_approval(self):
        pending = self.pending()
        changed = StructuredCapabilityRequest(self.request.original_request, {"application": "other"})
        self.assertEqual(self.approve(pending.token, changed).status, ExecutionStatus.DENIED)
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_original_request_binding_is_preserved(self):
        pending = self.pending()
        changed = StructuredCapabilityRequest("different request", self.request.arguments)
        self.assertEqual(self.approve(pending.token, changed).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_caller_mutation_does_not_change_saved_action(self):
        pending = self.pending()
        self.request.arguments["application"] = "other"
        original = StructuredCapabilityRequest("open requested app", {"application": "app"})
        self.assertTrue(self.approve(pending.token, original).succeeded)
        self.fake.execute_structured.assert_called_once_with({"application": "app"})

    def test_nested_validated_arguments_are_isolated(self):
        self.fake.validate_arguments.side_effect = deepcopy
        self.request = StructuredCapabilityRequest("nested fake", {"nested": {"value": "one"}})
        pending = self.pending()
        self.request.arguments["nested"]["value"] = "two"
        original = StructuredCapabilityRequest("nested fake", {"nested": {"value": "one"}})
        self.assertTrue(self.approve(pending.token, original).succeeded)
        self.fake.execute_structured.assert_called_once_with({"nested": {"value": "one"}})

    def test_open_app_integration_uses_mocked_service(self):
        with patch("nayeon.capabilities.open_app.ApplicationService") as service:
            implementation = OpenAppCapability()
            capability = implementation.capability
            self.registry.register(capability, implementation)
            self.permissions.grant(capability.name)
            result = self.executor.execute_structured(capability, self.request)
            self.assertTrue(result.succeeded)
            service.return_value.launch.assert_called_once_with("app")

    def test_invalid_arguments_do_not_reach_policy_or_execution(self):
        self.request.arguments["unknown"] = "value"
        with patch.object(self.policy, "evaluate", wraps=self.policy.evaluate) as evaluate:
            self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
            evaluate.assert_not_called()
        self.fake.execute_structured.assert_not_called()
        self.assertEqual(self.events(), [AuditEventType.EXECUTION_FAILED])

    def test_validation_and_execution_errors_do_not_echo_sensitive_values(self):
        secret = "fake-sensitive-value"
        self.fake.validate_arguments.side_effect = ValueError(secret)
        self.assertNotIn(secret, self.execute().message)
        self.fake.validate_arguments.side_effect = self.fake.validate
        self.fake.execute_structured.side_effect = RuntimeError(secret)
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.assertNotIn(secret, repr(self.audit.all()))
        self.assertNotIn(AuditEventType.EXECUTION_SUCCEEDED, self.events())

    def test_legacy_approval_cannot_redeem_structured_token(self):
        pending = self.pending()
        # A different executor sharing confirmation storage must also fail closed.
        other = ActionExecutor(self.registry, self.policy, self.confirmation, self.audit, self.undo)
        result = other.approve_and_execute(pending.token, capability=self.capability,
                                          request=self.request.original_request)
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        self.fake.execute.assert_not_called()
        self.fake.execute_structured.assert_not_called()

    def test_legacy_token_cannot_be_used_for_structured_action(self):
        self.configure(requires_confirmation=True)
        pending = self.executor.execute(self.capability, self.request.original_request)
        self.assertEqual(self.approve(pending.confirmation_request.token).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_revoked_permission_is_rechecked_after_approval(self):
        pending = self.pending()
        self.permissions.revoke("example")
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_changed_registration_rejects_pending_action(self):
        pending = self.pending()
        self.registry.unregister("example")
        replacement = StructuredFake()
        self.registry.register(self.capability, replacement)
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        replacement.execute_structured.assert_not_called()
        self.fake.execute_structured.assert_not_called()

    def test_caller_cannot_remove_registered_confirmation_requirement(self):
        self.configure(requires_confirmation=True)
        forged = replace(self.capability, requires_confirmation=False)
        result = self.executor.execute_structured(forged, self.request)
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.fake.execute_structured.assert_not_called()

    def test_expired_or_rejected_tokens_do_not_execute(self):
        pending = self.pending()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = pending.expires_at + timedelta(seconds=1)
            self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        pending = self.execute().confirmation_request
        self.executor.reject(pending.token, capability=self.capability)
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_missing_structured_contract_fails_without_legacy_fallback(self):
        self.registry.unregister("example")
        legacy = Mock(spec=["execute"])
        self.registry.register(self.capability, legacy)
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        legacy.execute.assert_not_called()

    def test_reversible_structured_action_requires_undo_provider(self):
        self.configure(reversible=True)
        del self.fake.build_undo
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.fake.execute_structured.assert_not_called()

    def test_invalid_changed_arguments_reject_approval(self):
        pending = self.pending()
        self.request.arguments["application"] = " "
        self.assertEqual(self.approve(pending.token).status, ExecutionStatus.DENIED)
        self.fake.execute_structured.assert_not_called()

    def test_reversible_structured_action_uses_existing_undo_contract(self):
        self.configure(reversible=True)
        result = self.execute()
        self.fake.build_undo.assert_called_once_with(
            request=self.request.original_request, output=result.output
        )
        self.assertEqual(self.events()[-1], AuditEventType.UNDO_REGISTERED)
        self.assertTrue(self.undo.undo_last().success)
        self.fake.restore.assert_called_once_with()

    def test_undo_registration_failure_stays_a_reported_partial_outcome(self):
        self.configure(reversible=True)
        self.fake.build_undo.side_effect = RuntimeError("fake-sensitive-value")
        result = self.execute()
        self.assertTrue(result.succeeded)
        self.assertIn("undo could not be registered", result.message)
        self.assertEqual(self.events()[-1], AuditEventType.UNDO_REGISTRATION_FAILED)
        self.assertNotIn("fake-sensitive-value", repr(self.audit.all()))
