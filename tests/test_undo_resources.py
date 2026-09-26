"""Generic ownership and abandonment checks using counters, never OS resources."""

from dataclasses import replace
from threading import Event, Thread
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.audit.service import AuditEventType, AuditService
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.service import PolicyService
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode
from nayeon.undo.contract import UndoProvider, UndoRegistration, UnregisteredResourceProvider
from nayeon.undo.service import UndoService
from nayeon.verification.contract import VerificationResult, VerificationStatus


class FakeResource:
    def __init__(self):
        self.releases = 0

    def release(self):
        self.releases += 1


class UndoResourceTests(unittest.TestCase):
    def setUp(self):
        self.undo = UndoService(max_depth=2)
        self.resource = FakeResource()
        self.callback = Mock(return_value="restored")

    def register(self, *, resource=None, callback=None):
        resource = self.resource if resource is None else resource
        return self.undo.register(capability="fake", description="Restore fake",
                                  callback=self.callback if callback is None else callback,
                                  cleanup=resource.release)

    def test_optional_cleanup_contract_and_protocol_independence(self):
        self.assertIsNone(UndoRegistration("Restore", self.callback).cleanup)
        class Releaser:
            def release_unregistered_resources(self, *, output):
                raise AssertionError("detection must not invoke")
        self.assertIsInstance(Releaser(), UnregisteredResourceProvider)
        self.assertNotIsInstance(Releaser(), UndoProvider)

    def test_invalid_cleanup_never_transfers_ownership(self):
        with self.assertRaises(TypeError):
            UndoRegistration("Restore", self.callback, cleanup=1)
        with self.assertRaises(TypeError):
            self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=1)
        self.assertEqual(self.undo.count(), 0)

    def test_registration_validation_failure_leaves_cleanup_with_caller(self):
        with self.assertRaises(ValueError):
            self.undo.register(capability=" ", description="Restore", callback=self.callback,
                               cleanup=self.resource.release)
        self.undo.close()
        self.assertEqual(self.resource.releases, 0)
        self.resource.release()  # caller explicitly disposes rejected resource
        self.assertEqual(self.resource.releases, 1)

    def test_normal_success_cleans_once_after_callback(self):
        def callback():
            self.assertEqual(self.undo.count(), 0)
            self.assertEqual(self.resource.releases, 0)
            return "restored"
        operation = self.register(callback=callback)
        result = self.undo.undo_last()
        self.assertTrue(result.success)
        self.assertEqual(result.operation_id, operation.operation_id)
        self.assertEqual(result.output, "restored")
        self.assertEqual(self.resource.releases, 1)

    def test_false_and_failure_shaped_returns_keep_success_semantics(self):
        for output in (False, None, {"success": False}, {"refused": True}):
            with self.subTest(output=output):
                resource = FakeResource()
                self.register(resource=resource, callback=lambda: output)
                result = self.undo.undo_last()
                self.assertTrue(result.success)
                self.assertIs(result.output, output)
                self.assertEqual(resource.releases, 1)

    def test_callback_exception_consumes_and_cleans_without_retry(self):
        self.callback.side_effect = ValueError("controlled refusal")
        self.register()
        result = self.undo.undo_last()
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Undo failed: controlled refusal")
        self.assertFalse(self.undo.undo_last().success)
        self.assertEqual(self.resource.releases, 1)
        self.callback.assert_called_once()

    def test_callback_interrupt_still_cleans_and_propagates(self):
        self.callback.side_effect = KeyboardInterrupt()
        self.register()
        with self.assertRaises(KeyboardInterrupt):
            self.undo.undo_last()
        self.assertEqual(self.resource.releases, 1)
        self.assertEqual(self.undo.count(), 0)

    def test_no_cleanup_remains_compatible(self):
        self.undo.register(capability="fake", description="Restore", callback=self.callback)
        self.assertTrue(self.undo.undo_last().success)
        self.assertEqual(self.undo.cleanup_failures, 0)

    def test_repeated_terminal_operations_do_not_double_cleanup(self):
        self.register()
        self.undo.undo_last()
        self.undo.undo_last()
        self.undo.clear()
        self.undo.close()
        self.undo.close()
        self.assertEqual(self.resource.releases, 1)

    def test_clear_cleans_all_without_undo_and_remains_reusable(self):
        other = FakeResource()
        self.register()
        self.register(resource=other)
        self.undo.clear()
        self.callback.assert_not_called()
        self.assertEqual((self.resource.releases, other.releases), (1, 1))
        fresh = FakeResource()
        self.register(resource=fresh)
        self.assertTrue(self.undo.undo_last().success)
        self.assertEqual(fresh.releases, 1)

    def test_clear_cleanup_failure_does_not_skip_remaining_entry(self):
        bad = Mock(side_effect=RuntimeError("fake-secret-resource"))
        self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=bad)
        self.register()
        self.undo.clear()
        self.undo.clear()
        bad.assert_called_once()
        self.assertEqual(self.resource.releases, 1)
        self.assertEqual(self.undo.cleanup_failures, 1)

    def test_eviction_cleans_oldest_and_preserves_new_registration(self):
        second, third = FakeResource(), FakeResource()
        self.register()
        self.register(resource=second)
        operation = self.register(resource=third)
        self.assertIs(self.undo.peek(), operation)
        self.assertEqual((self.resource.releases, second.releases, third.releases), (1, 0, 0))
        self.undo.clear()
        self.assertEqual((self.resource.releases, second.releases, third.releases), (1, 1, 1))

    def test_eviction_cleanup_exception_cannot_undo_new_transfer(self):
        for error in (RuntimeError("fake-secret"), KeyboardInterrupt(), SystemExit()):
            with self.subTest(error=type(error).__name__):
                service = UndoService(max_depth=1)
                bad = Mock(side_effect=error)
                service.register(capability="old", description="Old", callback=self.callback, cleanup=bad)
                new = service.register(capability="new", description="New", callback=self.callback)
                self.assertIs(service.peek(), new)
                self.assertEqual(service.cleanup_failures, 1)
                service.clear()
                bad.assert_called_once()

    def test_close_is_terminal_idempotent_and_cleans_remaining(self):
        self.register()
        self.undo.close()
        self.undo.close()
        self.undo.clear()
        self.assertEqual(self.resource.releases, 1)
        fresh = FakeResource()
        with self.assertRaisesRegex(RuntimeError, "Undo service is closed"):
            self.register(resource=fresh)
        self.assertEqual(fresh.releases, 0)  # rejected caller still owns it
        self.assertEqual(self.undo.count(), 0)
        self.callback.assert_not_called()

    def test_close_failure_does_not_skip_remaining_or_retry(self):
        bad = Mock(side_effect=ValueError("fake-secret"))
        self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=bad)
        self.register()
        self.undo.close()
        self.undo.close()
        self.assertEqual(self.resource.releases, 1)
        self.assertEqual(self.undo.cleanup_failures, 1)
        bad.assert_called_once()

    def test_cleanup_failure_preserves_callback_success(self):
        cleanup = Mock(side_effect=RuntimeError("fake-secret-resource"))
        self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=cleanup)
        result = self.undo.undo_last()
        self.assertTrue(result.success)
        self.assertEqual(result.output, "restored")
        self.assertNotIn("fake-secret", repr(result))
        self.assertEqual(self.undo.cleanup_failures, 1)

    def test_cleanup_failure_preserves_primary_callback_exception(self):
        self.callback.side_effect = ValueError("controlled refusal")
        cleanup = Mock(side_effect=RuntimeError("fake-secret-resource"))
        self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=cleanup)
        result = self.undo.undo_last()
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Undo failed: controlled refusal")
        self.assertEqual(self.undo.cleanup_failures, 1)

    def test_reentrant_close_inside_callback_does_not_close_inflight_resource(self):
        other = FakeResource()
        self.register(resource=other)
        def callback():
            self.undo.close()
            self.assertEqual(other.releases, 1)
            self.assertEqual(self.resource.releases, 0)
        self.register(callback=callback)
        self.assertTrue(self.undo.undo_last().success)
        self.assertEqual(self.resource.releases, 1)

    def test_cross_thread_close_and_clear_leave_inflight_callback_alive(self):
        started, finish = Event(), Event()
        outcomes = []
        def callback():
            started.set()
            if not finish.wait(3):
                raise AssertionError("test coordination timed out")
            return self.resource.releases
        self.register(callback=callback)
        thread = Thread(target=lambda: outcomes.append(self.undo.undo_last()))
        thread.start()
        try:
            self.assertTrue(started.wait(3))
            other = FakeResource()
            self.register(resource=other)
            self.undo.clear()
            self.undo.close()
            self.assertEqual(self.resource.releases, 0)
            self.assertEqual(other.releases, 1)
        finally:
            finish.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertTrue(outcomes[0].success)
        self.assertEqual(outcomes[0].output, 0)
        self.assertEqual(self.resource.releases, 1)

    def test_cleanup_executes_outside_history_lock(self):
        observed = Event()
        def cleanup():
            worker = Thread(target=lambda: (self.undo.count(), observed.set()))
            worker.start()
            worker.join(2)
            if not observed.is_set():
                raise RuntimeError("cleanup ran under lock")
        self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=cleanup)
        self.undo.clear()
        self.assertTrue(observed.is_set())
        self.assertEqual(self.undo.cleanup_failures, 0)

    def test_reentrant_cleanup_cannot_double_dispose_detached_entries(self):
        calls = []
        def cleanup():
            calls.append("cleanup")
            self.undo.clear()
            self.undo.close()
        self.undo.register(capability="fake", description="Restore", callback=self.callback, cleanup=cleanup)
        self.register()
        self.undo.clear()
        self.assertEqual(calls, ["cleanup"])
        self.assertEqual(self.resource.releases, 1)


class ResourceProvider:
    def __init__(self):
        self.resource = FakeResource()
        self.output = {"receipt": "opaque-fake"}
        self.execute = Mock(return_value=self.output)
        self.execute_structured = Mock(return_value=self.output)
        self.undo = Mock(return_value="restored")
        self.cleanup = Mock(side_effect=self.resource.release)
        self.build_undo = Mock(return_value=UndoRegistration("Restore fake", self.undo, self.cleanup))
        self.release_unregistered_resources = Mock(side_effect=lambda **kwargs: self.resource.release())
        self.verify_result = Mock(return_value=VerificationResult(VerificationStatus.VERIFIED, "Fake observation."))

    def validate_arguments(self, arguments):
        return dict(arguments)


class ExecutorResourceTests(unittest.TestCase):
    def setUp(self):
        self.fake = ResourceProvider()
        self.registry = CapabilityRegistry()
        self.capability = Capability("resource_example", "Fake", ExecutionMode.LOCAL, "fake", reversible=True)
        self.registry.register(self.capability, self.fake)
        self.undo = UndoService(max_depth=1)
        self.audit = AuditService()
        self.executor = ActionExecutor(self.registry, PolicyService(), ConfirmationService(), self.audit, self.undo)

    def execute(self):
        return self.executor.execute_structured(self.capability, StructuredCapabilityRequest("do fake", {}))

    def fail_audit_at(self, event):
        original = self.audit.record
        def record(kind, **kwargs):
            if kind is event:
                raise OSError("original audit error")
            return original(kind, **kwargs)
        self.enterContext(patch.object(self.audit, "record", side_effect=record))

    def assert_released_by_provider_once(self):
        self.fake.release_unregistered_resources.assert_called_once_with(output=self.fake.output)
        self.assertIs(self.fake.release_unregistered_resources.call_args.kwargs["output"], self.fake.output)
        self.fake.cleanup.assert_not_called()
        self.assertEqual(self.fake.resource.releases, 1)
        self.assertEqual(self.undo.count(), 0)

    def test_success_transfers_and_verifies_before_any_cleanup(self):
        def observe(**kwargs):
            self.assertEqual(self.undo.count(), 1)
            self.assertEqual(self.fake.resource.releases, 0)
            return VerificationResult(VerificationStatus.VERIFIED, "Fake observation.")
        self.fake.verify_result.side_effect = observe
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(result.verification.status, VerificationStatus.VERIFIED)
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual([e.event_type for e in self.audit.all()][-2:],
                         [AuditEventType.UNDO_REGISTERED, AuditEventType.VERIFICATION_OUTCOME])
        self.undo.undo_last()
        self.fake.undo.assert_called_once()
        self.fake.cleanup.assert_called_once()
        self.assertEqual(self.fake.resource.releases, 1)

    def test_legacy_execution_gets_same_ownership_guard(self):
        self.executor.execute(self.capability, "legacy fake")
        self.fake.execute.assert_called_once()
        self.fake.release_unregistered_resources.assert_not_called()
        self.undo.close()
        self.fake.cleanup.assert_called_once()

    def test_build_undo_failure_releases_once(self):
        self.fake.build_undo.side_effect = ValueError("build failed")
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertIn("undo could not be registered", result.message)
        self.assert_released_by_provider_once()

    def test_registration_failure_releases_once(self):
        with patch.object(self.undo, "register", side_effect=ValueError("reject before commit")):
            self.execute()
        self.assert_released_by_provider_once()

    def test_invalid_registration_cleanup_releases_without_transfer(self):
        # Simulate malformed trusted provider output; service validation rejects.
        registration = Mock(description="Restore", callback=self.fake.undo, cleanup=42)
        self.fake.build_undo.return_value = registration
        self.execute()
        self.assert_released_by_provider_once()

    def test_success_audit_failure_releases_returned_output(self):
        self.fail_audit_at(AuditEventType.EXECUTION_SUCCEEDED)
        with self.assertRaisesRegex(OSError, "original audit error"):
            self.execute()
        self.assert_released_by_provider_once()
        self.fake.build_undo.assert_not_called()

    def test_registration_failure_audit_exception_still_releases(self):
        self.fake.build_undo.side_effect = ValueError("build failed")
        self.fail_audit_at(AuditEventType.UNDO_REGISTRATION_FAILED)
        with self.assertRaises(OSError):
            self.execute()
        self.assert_released_by_provider_once()

    def test_closed_service_rejects_transfer_and_provider_releases(self):
        self.undo.close()
        self.execute()
        self.assert_released_by_provider_once()

    def test_evicted_cleanup_failure_still_transfers_new_ownership(self):
        old_cleanup = Mock(side_effect=RuntimeError("fake-private"))
        self.undo.register(capability="old", description="Old", callback=lambda: None, cleanup=old_cleanup)
        result = self.execute()
        self.assertNotIn("undo could not", result.message)
        self.assertEqual(self.undo.peek().capability, self.capability.name)
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual(self.undo.cleanup_failures, 1)
        self.undo.clear()
        self.assertEqual(self.fake.resource.releases, 1)
        old_cleanup.assert_called_once()

    def test_reentrant_eviction_cleanup_can_clear_new_entry_without_double_release(self):
        self.undo.register(capability="old", description="Old", callback=lambda: None,
                           cleanup=self.undo.clear)
        self.execute()
        self.assertEqual(self.undo.count(), 0)
        self.fake.cleanup.assert_called_once()
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual(self.fake.resource.releases, 1)

    def test_build_undo_interrupt_releases_returned_resource_and_propagates(self):
        self.fake.build_undo.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.execute()
        self.assert_released_by_provider_once()

    def test_later_exception_without_transfer_still_releases(self):
        self.fake.build_undo.side_effect = ValueError("build failed")
        with patch.object(self.executor._verification, "verify", side_effect=RuntimeError("unexpected")):
            with self.assertRaises(RuntimeError):
                self.execute()
        self.assert_released_by_provider_once()

    def test_post_transfer_audit_failure_leaves_undo_owned(self):
        self.fail_audit_at(AuditEventType.UNDO_REGISTERED)
        with self.assertRaises(OSError):
            self.execute()
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual(self.undo.count(), 1)
        self.undo.clear()
        self.fake.cleanup.assert_called_once()

    def test_verifier_exception_does_not_release_undo_resource(self):
        self.fake.verify_result.side_effect = ValueError("private observation")
        result = self.execute()
        self.assertEqual(result.verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(self.undo.count(), 1)
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual(self.fake.resource.releases, 0)

    def test_inconclusive_verification_does_not_remove_undo(self):
        self.fake.verify_result.return_value = VerificationResult()
        self.assertEqual(self.execute().verification.status, VerificationStatus.INDETERMINATE)
        self.assertEqual(self.undo.count(), 1)
        self.fake.release_unregistered_resources.assert_not_called()

    def test_generic_verification_service_exception_preserves_transfer(self):
        with patch.object(self.executor._verification, "verify", side_effect=RuntimeError("unexpected")):
            with self.assertRaises(RuntimeError):
                self.execute()
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual(self.undo.count(), 1)

    def test_verification_audit_failure_preserves_transfer(self):
        self.fail_audit_at(AuditEventType.VERIFICATION_OUTCOME)
        with self.assertRaises(OSError):
            self.execute()
        self.fake.release_unregistered_resources.assert_not_called()
        self.assertEqual(self.undo.count(), 1)

    def test_cleanup_hook_absent_preserves_registration_failure_behavior(self):
        del self.fake.release_unregistered_resources
        self.fake.build_undo.side_effect = ValueError("build failed")
        self.assertEqual(self.execute().status, ExecutionStatus.EXECUTED)
        self.assertEqual(self.executor.unregistered_cleanup_failures, 0)

    def test_provider_cleanup_exception_is_redacted_and_preserves_result(self):
        self.fake.build_undo.side_effect = ValueError("build failed")
        self.fake.release_unregistered_resources.side_effect = RuntimeError("fake-secret-resource")
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.EXECUTED)
        self.assertNotIn("fake-secret", repr(result) + repr(self.audit.all()))
        self.assertEqual(self.executor.unregistered_cleanup_failures, 1)
        self.fake.release_unregistered_resources.assert_called_once()

    def test_cleanup_exception_does_not_mask_original_audit_exception(self):
        self.fail_audit_at(AuditEventType.EXECUTION_SUCCEEDED)
        self.fake.release_unregistered_resources.side_effect = SystemExit("fake-secret")
        with self.assertRaisesRegex(OSError, "original audit error"):
            self.execute()
        self.assertEqual(self.executor.unregistered_cleanup_failures, 1)

    def test_execution_exception_has_no_returned_output_to_release(self):
        self.fake.execute_structured.side_effect = ValueError("execution owns its own failure")
        self.assertEqual(self.execute().status, ExecutionStatus.FAILED)
        self.fake.release_unregistered_resources.assert_not_called()
        self.fake.cleanup.assert_not_called()

    def test_permission_and_pending_paths_never_release_uncreated_output(self):
        self.capability = replace(self.capability, requires_confirmation=True)
        self.registry.unregister(self.capability.name)
        self.registry.register(self.capability, self.fake)
        result = self.execute()
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.fake.release_unregistered_resources.assert_not_called()
        self.fake.execute_structured.assert_not_called()
        self.executor.reject(result.confirmation_request.token, capability=self.capability)
        self.fake.release_unregistered_resources.assert_not_called()

    def test_nonreversible_provider_hook_releases_on_exit_without_registration(self):
        self.capability = replace(self.capability, reversible=False)
        self.registry.unregister(self.capability.name)
        self.registry.register(self.capability, self.fake)
        self.assertEqual(self.execute().status, ExecutionStatus.EXECUTED)
        self.assert_released_by_provider_once()

    def test_cleanup_uses_executing_provider_after_registry_changes(self):
        replacement = ResourceProvider()
        def execute(arguments):
            self.registry.unregister(self.capability.name)
            self.registry.register(self.capability, replacement)
            return self.fake.output
        self.fake.execute_structured.side_effect = execute
        self.fake.build_undo.side_effect = ValueError("build failed")
        self.execute()
        self.assert_released_by_provider_once()
        replacement.release_unregistered_resources.assert_not_called()
