"""Exercise the real trust boundary with side-effect-free implementations."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.undo.contract import UndoRegistration
from nayeon.undo.service import UndoService


class ReversibleFake:
    """All execution and undo effects are limited to recording mock calls."""

    def __init__(self):
        self.execute = Mock(return_value="test output")
        self.restore = Mock(return_value="restored")
        self.build_undo = Mock(return_value=UndoRegistration("Restore test", self.restore))


class ActionExecutorTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.permissions = PermissionService(default_allowed=False)
        self.policy = PolicyService(self.permissions)
        self.confirmation = ConfirmationService()
        self.audit = AuditService()
        self.undo = UndoService()
        self.executor = ActionExecutor(
            self.registry, self.policy, self.confirmation, self.audit, self.undo
        )
        self.implementation = Mock(spec=["execute"])
        self.implementation.execute.return_value = "test output"

    def register(self, *, confirmation=False, reversible=False, implementation=None):
        capability = Capability(
            "example", "In-memory test", ExecutionMode.LOCAL, "fake",
            requires_confirmation=confirmation, reversible=reversible,
        )
        self.registry.register(
            capability,
            self.implementation if implementation is None else implementation,
        )
        self.permissions.grant(capability.name)
        return capability

    def events(self):
        return [event.event_type for event in self.audit.all()]

    def pending(self):
        capability = self.register(confirmation=True)
        result = self.executor.execute(capability, "do example")
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.implementation.execute.assert_not_called()
        return capability, result.confirmation_request.token

    def test_permission_denial_prevents_confirmation_and_execution(self):
        capability = self.register(confirmation=True)
        self.permissions.revoke(capability.name)
        result = self.executor.execute(capability, "do example")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertFalse(result.succeeded)
        self.assertIsNone(result.confirmation_request)
        self.implementation.execute.assert_not_called()
        self.assertEqual(self.events(), [AuditEventType.POLICY_DECISION])
        self.assertEqual(self.undo.count(), 0)

    def test_policy_block_prevents_execution_even_with_permission(self):
        capability = self.register()
        executor = ActionExecutor(
            self.registry, PolicyService(self.permissions, {"example"}),
            self.confirmation, self.audit, self.undo,
        )
        self.assertEqual(executor.execute(capability, "do example").status, ExecutionStatus.DENIED)
        self.implementation.execute.assert_not_called()

    def test_allowed_action_executes_once_with_ordered_audit(self):
        capability = self.register()
        result = self.executor.execute(capability, "do example")
        self.assertTrue(result.succeeded)
        self.assertEqual(result.output, "test output")
        self.implementation.execute.assert_called_once_with("do example")
        self.assertEqual(self.events(), [
            AuditEventType.POLICY_DECISION, AuditEventType.EXECUTION_STARTED,
            AuditEventType.EXECUTION_SUCCEEDED,
            AuditEventType.VERIFICATION_OUTCOME,
        ])

    def test_confirmation_defers_execution_until_matching_approval(self):
        capability, token = self.pending()
        self.assertEqual(self.events(), [
            AuditEventType.POLICY_DECISION, AuditEventType.CONFIRMATION_CREATED,
        ])
        result = self.executor.approve_and_execute(token, capability=capability, request="do example")
        self.assertTrue(result.succeeded)
        self.implementation.execute.assert_called_once_with("do example")
        self.assertEqual(self.events()[2:], [
            AuditEventType.CONFIRMATION_APPROVED, AuditEventType.POLICY_DECISION,
            AuditEventType.EXECUTION_STARTED, AuditEventType.EXECUTION_SUCCEEDED,
            AuditEventType.VERIFICATION_OUTCOME,
        ])

    def test_approval_cannot_replay_execution(self):
        capability, token = self.pending()
        self.executor.approve_and_execute(token, capability=capability, request="do example")
        replay = self.executor.approve_and_execute(token, capability=capability, request="do example")
        self.assertEqual(replay.status, ExecutionStatus.DENIED)
        self.implementation.execute.assert_called_once_with("do example")
        self.assertEqual(self.events()[-1], AuditEventType.CONFIRMATION_REJECTED)

    def test_approval_for_changed_request_does_not_execute(self):
        capability, token = self.pending()
        result = self.executor.approve_and_execute(token, capability=capability, request="other request")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.implementation.execute.assert_not_called()

    def test_approval_for_different_capability_does_not_execute(self):
        _, token = self.pending()
        other = Capability("other", "Test", ExecutionMode.LOCAL, "fake", requires_confirmation=True)
        self.registry.register(other, self.implementation)
        self.permissions.grant("other")
        result = self.executor.approve_and_execute(token, capability=other, request="do example")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.implementation.execute.assert_not_called()

    def test_permission_revoked_while_pending_is_rechecked(self):
        capability, token = self.pending()
        self.permissions.revoke(capability.name)
        result = self.executor.approve_and_execute(token, capability=capability, request="do example")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertEqual(self.events()[-1], AuditEventType.POLICY_DECISION)
        self.implementation.execute.assert_not_called()

    def test_rejection_cancels_pending_execution(self):
        capability, token = self.pending()
        self.assertEqual(self.executor.reject(token, capability=capability).status, ExecutionStatus.DENIED)
        result = self.executor.approve_and_execute(token, capability=capability, request="do example")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.implementation.execute.assert_not_called()

    def test_missing_implementation_fails_without_execution(self):
        capability = self.register()
        self.registry.unregister(capability.name)
        self.registry.register(capability)
        result = self.executor.execute(capability, "do example")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.implementation.execute.assert_not_called()
        self.assertNotIn(AuditEventType.EXECUTION_STARTED, self.events())
        self.assertEqual(self.events()[-1], AuditEventType.EXECUTION_FAILED)

    def test_execution_exception_fails_without_success_or_undo(self):
        fake = ReversibleFake()
        fake.execute.side_effect = RuntimeError("test execution failure")
        capability = self.register(reversible=True, implementation=fake)
        result = self.executor.execute(capability, "do example")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertFalse(result.succeeded)
        fake.build_undo.assert_not_called()
        self.assertEqual(self.undo.count(), 0)
        self.assertNotIn(AuditEventType.EXECUTION_SUCCEEDED, self.events())
        self.assertEqual(self.events()[-1], AuditEventType.EXECUTION_FAILED)

    def test_reversible_metadata_requires_undo_provider_before_execution(self):
        capability = self.register(reversible=True)
        result = self.executor.execute(capability, "do example")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.implementation.execute.assert_not_called()
        self.assertEqual(self.audit.all()[-1].outcome, "configuration_error")
        self.assertNotIn(AuditEventType.EXECUTION_STARTED, self.events())

    def test_successful_reversible_action_registers_concrete_undo(self):
        fake = ReversibleFake()
        capability = self.register(reversible=True, implementation=fake)
        result = self.executor.execute(capability, "do example")
        self.assertTrue(result.succeeded)
        fake.build_undo.assert_called_once_with(request="do example", output="test output")
        fake.restore.assert_not_called()
        self.assertEqual(self.undo.count(), 1)
        self.assertEqual(self.events()[-2:], [AuditEventType.UNDO_REGISTERED,
                                            AuditEventType.VERIFICATION_OUTCOME])
        self.assertEqual(self.audit.all()[-2].details["operation_id"], self.undo.peek().operation_id)
        self.assertTrue(self.undo.undo_last().success)
        fake.restore.assert_called_once_with()

    def test_undo_registration_failure_reports_partial_outcome(self):
        fake = ReversibleFake()
        fake.build_undo.side_effect = RuntimeError("test registration failure")
        capability = self.register(reversible=True, implementation=fake)
        result = self.executor.execute(capability, "do example")
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.output, "test output")
        self.assertIn("undo could not be registered", result.message)
        self.assertEqual(self.undo.count(), 0)
        self.assertEqual(self.events()[-2:], [AuditEventType.UNDO_REGISTRATION_FAILED,
                                            AuditEventType.VERIFICATION_OUTCOME])
        self.assertEqual(self.audit.all()[-2].details, {"error_type": "RuntimeError"})

    def test_audit_failure_before_execution_prevents_side_effect(self):
        capability = self.register()
        with patch.object(self.audit, "record", side_effect=OSError("test audit failure")):
            with self.assertRaises(OSError):
                self.executor.execute(capability, "do example")
        self.implementation.execute.assert_not_called()


class AuditPersistenceTests(unittest.TestCase):
    def test_events_append_as_jsonl_in_temporary_directory(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "audit" / "events.jsonl"
            audit = AuditService(path)
            for outcome in ("allow", "deny"):
                audit.record(AuditEventType.POLICY_DECISION, capability="example",
                             outcome=outcome, message="test event")
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["outcome"] for row in rows], ["allow", "deny"])
            self.assertEqual([row["event_type"] for row in rows], ["policy_decision"] * 2)
            self.assertEqual([row["event_id"] for row in rows],
                             [event.event_id for event in audit.all()])
