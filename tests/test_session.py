"""Session lifecycle through real authority services and a mocked launch service."""

from dataclasses import fields, replace
from datetime import timedelta
from itertools import count
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.dispatch import IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionStatus
from nayeon.agent.orchestration import PendingStructuredAction
from nayeon.agent.router import TaskRouter
from nayeon.agent.session import ConversationSession
from nayeon.audit.service import AuditService
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.undo.action import UndoAction
from nayeon.undo.capability import UndoCapability
from nayeon.undo.service import UndoService


class SessionTests(unittest.TestCase):
    def setUp(self):
        service = self.enterContext(patch("nayeon.capabilities.open_app.ApplicationService"))
        self.launch = service.return_value.launch
        self.launch.return_value = "fake launch result"
        tokens = count()
        self.enterContext(patch("nayeon.policy.confirmation.secrets.token_urlsafe",
                                side_effect=lambda _: f"test-token-{next(tokens)}"))
        self.implementation = OpenAppCapability()
        self.capability = self.implementation.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.capability, self.implementation)
        self.permissions = PermissionService(default_allowed=False)
        self.permissions.grant("open_app")
        self.confirmation = ConfirmationService()
        self.undo = UndoService()
        self.executor = ActionExecutor(self.registry, PolicyService(self.permissions),
                                       self.confirmation, AuditService(), self.undo)
        self.semantic = Mock(spec=["resolve"])
        self.semantic.resolve.return_value = IntentResolution(None, IntentSource.NONE, 0)
        self.resolver = IntentResolver(
            local=LocalIntentInterpreter(router=TaskRouter(self.registry)), semantic=self.semantic,
        )
        self.session = ConversationSession(resolver=self.resolver, registry=self.registry,
                                           executor=self.executor)
        self.execute = self.enterContext(patch.object(
            self.executor, "execute_structured", wraps=self.executor.execute_structured))
        self.approve = self.enterContext(patch.object(
            self.executor, "approve_and_execute_structured",
            wraps=self.executor.approve_and_execute_structured))
        self.reject = self.enterContext(patch.object(
            self.executor, "reject", wraps=self.executor.reject))
        self.legacy = self.enterContext(patch.object(self.executor, "execute",
                                                    wraps=self.executor.execute))

    def protected(self):
        self.capability = replace(self.capability, requires_confirmation=True)
        self.registry.unregister("open_app")
        self.registry.register(self.capability, self.implementation)

    def pending(self):
        self.protected()
        result = self.session.request("open App")
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertTrue(self.session.has_pending)
        self.launch.assert_not_called()
        return result

    def semantic_intent(self, intent="open_app", **arguments):
        resolution = IntentResolution(intent, IntentSource.SEMANTIC, 0.95, arguments)
        self.semantic.resolve.return_value = resolution
        return resolution

    def test_local_request_reaches_executor_once(self):
        result = self.session.request("open App")
        self.assertTrue(result.succeeded)
        self.execute.assert_called_once()
        self.launch.assert_called_once_with("App")
        self.semantic.resolve.assert_not_called()
        self.legacy.assert_not_called()
        self.assertFalse(self.session.has_pending)

    def test_semantic_request_forwards_only_application(self):
        self.semantic_intent(application=" App ", secret="fake-sensitive", shell="untrusted")
        result = self.session.request("please bring up my application")
        self.assertTrue(result.succeeded)
        self.assertEqual(self.execute.call_args.args[1].arguments, {"application": " App "})
        self.launch.assert_called_once_with("App")
        self.semantic.resolve.assert_called_once()

    def test_unresolved_request_never_executes(self):
        self.assertEqual(self.session.request("unrecognized text").status, ExecutionStatus.DENIED)
        self.execute.assert_not_called()
        self.launch.assert_not_called()

    def test_unsupported_registered_capability_never_executes(self):
        other = replace(self.capability, name="other", intent_patterns=("other ",))
        self.registry.register(other, self.implementation)
        self.assertEqual(self.session.request("other action").status, ExecutionStatus.DENIED)
        self.execute.assert_not_called()
        self.legacy.assert_not_called()
        self.launch.assert_not_called()

    def test_blank_or_non_string_request_fails_safely(self):
        for text in ("", "   ", None, 4):
            with self.subTest(text=text):
                self.assertEqual(self.session.request(text).status, ExecutionStatus.DENIED)
        self.semantic.resolve.assert_not_called()
        self.execute.assert_not_called()

    def test_pending_retains_only_resume_candidate_and_expiry(self):
        result = self.pending()
        pending = self.session._pending
        self.assertEqual({field.name for field in fields(PendingStructuredAction)},
                         {"token", "capability", "request", "expires_at"})
        self.assertEqual(pending.token, result.confirmation_request.token)
        self.assertEqual(pending.capability, self.capability)
        self.assertEqual(pending.request.original_request, "open App")
        self.assertEqual(pending.request.arguments, {"application": "App"})
        self.assertEqual(pending.expires_at, result.confirmation_request.expires_at)
        self.assertNotIn(pending.token, repr(pending))

    def test_approval_uses_stored_request_without_resolution_or_dispatch(self):
        self.pending()
        saved = self.session._pending
        with patch.object(self.resolver, "resolve") as resolve, \
                patch.object(IntentDispatcher, "plan") as dispatch, \
                patch.object(OpenAppCapability, "arguments_from_request") as mapping:
            result = self.session.approve_pending()
        self.assertTrue(result.succeeded)
        self.approve.assert_called_once_with(saved.token, capability=saved.capability,
                                             request=saved.request)
        self.assertIs(self.approve.call_args.kwargs["request"], saved.request)
        resolve.assert_not_called()
        dispatch.assert_not_called()
        mapping.assert_not_called()
        self.execute.assert_called_once()
        self.launch.assert_called_once_with("App")
        self.assertFalse(self.session.has_pending)

    def test_request_and_approval_preserve_executor_result_identity(self):
        self.protected()
        initial, approved = [], []
        execute = self.execute._mock_wraps
        approve = self.approve._mock_wraps
        self.execute.side_effect = lambda *a, **kw: (initial.append(execute(*a, **kw)) or initial[-1])
        self.approve.side_effect = lambda *a, **kw: (approved.append(approve(*a, **kw)) or approved[-1])
        self.assertIs(self.session.request("open App"), initial[0])
        self.assertIs(self.session.approve_pending(), approved[0])

    def test_replay_approval_fails_without_executor_call(self):
        self.pending()
        self.session.approve_pending()
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.approve.assert_called_once()
        self.launch.assert_called_once_with("App")

    def test_reject_consumes_exact_token_and_clears_state(self):
        result = self.pending()
        saved = self.session._pending
        self.assertEqual(self.session.reject_pending().status, ExecutionStatus.DENIED)
        self.reject.assert_called_once_with(saved.token, capability=saved.capability)
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.executor.approve_and_execute_structured(
            result.confirmation_request.token, capability=saved.capability, request=saved.request,
        ).status, ExecutionStatus.DENIED)
        self.launch.assert_not_called()

    def test_approve_without_pending_is_safe(self):
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.approve.assert_not_called()

    def test_reject_without_pending_is_safe(self):
        self.assertEqual(self.session.reject_pending().status, ExecutionStatus.DENIED)
        self.reject.assert_not_called()

    def test_submitted_candidate_mutation_cannot_change_pending_action(self):
        self.pending()
        submitted = self.execute.call_args.args[1]
        submitted.arguments["application"] = "Other"
        self.assertTrue(self.session.approve_pending().succeeded)
        self.launch.assert_called_once_with("App")

    def test_semantic_mutation_and_extra_fields_cannot_change_pending_action(self):
        self.protected()
        resolution = self.semantic_intent(application="App", ignored={"value": "fake-secret"})
        self.session.request("please bring it up")
        resolution.arguments["application"] = "Other"
        resolution.arguments["ignored"]["value"] = "changed"
        self.assertEqual(self.session._pending.request.arguments, {"application": "App"})
        self.assertTrue(self.session.approve_pending().succeeded)
        self.launch.assert_called_once_with("App")

    def test_changed_implementation_fails_closed_and_clears_pending(self):
        self.pending()
        replacement = OpenAppCapability()
        self.registry.unregister("open_app")
        self.registry.register(self.capability, replacement)
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_removed_registration_fails_closed(self):
        self.pending()
        self.registry.unregister("open_app")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_changed_metadata_fails_closed(self):
        self.pending()
        self.registry.unregister("open_app")
        self.registry.register(replace(self.capability, requires_confirmation=False), self.implementation)
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.launch.assert_not_called()

    def test_revoked_permission_is_denied_and_clears_pending(self):
        self.pending()
        self.permissions.revoke("open_app")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_expired_approval_is_denied_and_clears_pending(self):
        result = self.pending()
        with patch("nayeon.agent.executor.datetime") as clock:
            clock.now.return_value = result.confirmation_request.expires_at + timedelta(seconds=1)
            self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_next_request_rejects_expired_pending_before_resolution(self):
        result = self.pending()
        with patch("nayeon.agent.session.datetime") as clock:
            clock.now.return_value = result.confirmation_request.expires_at + timedelta(seconds=1)
            self.session.request("unknown request")
        self.reject.assert_called_once()
        self.assertFalse(self.session.has_pending)
        self.assertFalse(self.semantic.resolve.call_args.kwargs["context"].pending_confirmation)
        self.launch.assert_not_called()

    def test_execution_failure_clears_pending(self):
        self.pending()
        self.launch.side_effect = RuntimeError("fake launch failure")
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.FAILED)
        self.assertFalse(self.session.has_pending)
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.launch.assert_called_once()

    def test_external_rejection_is_respected(self):
        result = self.pending()
        self.executor.reject(result.confirmation_request.token, capability=self.capability)
        self.assertEqual(self.session.approve_pending().status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_second_request_cannot_replace_or_execute_while_pending(self):
        self.pending()
        saved = self.session._pending
        self.assertEqual(self.session.request("open Other").status, ExecutionStatus.DENIED)
        self.assertIs(self.session._pending, saved)
        self.execute.assert_called_once()
        self.assertTrue(self.session.approve_pending().succeeded)
        self.launch.assert_called_once_with("App")

    def test_text_and_model_cannot_approve_pending_action(self):
        self.pending()
        self.semantic_intent("approve_pending")
        self.assertEqual(self.session.request("yes approve it").status, ExecutionStatus.DENIED)
        self.assertTrue(self.session.has_pending)
        self.approve.assert_not_called()
        self.launch.assert_not_called()

    def test_local_cancellation_uses_executor_and_no_bridge(self):
        self.protected()
        for text in ("cancel that", "undo that", "actually scratch that"):
            with self.subTest(text=text):
                self.session.request("open App")
                self.reject.reset_mock()
                with patch.object(self.session._bridge, "execute_with_pending") as bridge:
                    self.assertEqual(self.session.request(text).status, ExecutionStatus.DENIED)
                bridge.assert_not_called()
                self.reject.assert_called_once()
                self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_cancel_without_pending_is_safe_and_deterministic(self):
        self.semantic_intent("cancel_pending")
        first = self.session.request("cancel that")
        self.assertEqual(first, self.session.request("cancel that"))
        self.assertEqual(first.status, ExecutionStatus.DENIED)
        self.reject.assert_not_called()
        self.execute.assert_not_called()

    def test_undo_control_is_unsupported_without_direct_undo_or_execution(self):
        callback = Mock()
        self.undo.register(capability="example", description="Restore fake", callback=callback)
        routed = UndoCapability(UndoAction(self.undo))
        self.registry.register(routed.capability, routed)
        with patch.object(self.session._bridge, "execute_with_pending") as bridge:
            result = self.session.request("undo that")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertIn("not supported", result.message)
        self.assertEqual(self.undo.count(), 1)
        callback.assert_not_called()
        bridge.assert_not_called()
        self.execute.assert_not_called()
        self.legacy.assert_not_called()

    def test_denied_or_invalid_action_creates_no_pending_state(self):
        self.protected()
        self.permissions.revoke("open_app")
        self.assertEqual(self.session.request("open App").status, ExecutionStatus.DENIED)
        self.assertFalse(self.session.has_pending)
        self.semantic_intent(application=" ")
        self.assertEqual(self.session.request("please bring it up").status, ExecutionStatus.FAILED)
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_rejection_returns_executor_result_unchanged(self):
        self.pending()
        results = []
        reject = self.reject._mock_wraps
        self.reject.side_effect = lambda *a, **kw: (results.append(reject(*a, **kw)) or results[-1])
        self.assertIs(self.session.reject_pending(), results[0])
        self.assertFalse(self.session.has_pending)
        self.launch.assert_not_called()

    def test_session_isolates_pending_data_from_bridge_outcome(self):
        self.protected()
        outcomes = []
        bridge = self.session._bridge.execute_with_pending
        with patch.object(self.session._bridge, "execute_with_pending") as execute:
            execute.side_effect = lambda *a, **kw: (outcomes.append(bridge(*a, **kw)) or outcomes[-1])
            self.session.request("open App")
        outcomes[0].pending.request.arguments["application"] = "Other"
        self.assertTrue(self.session.approve_pending().succeeded)
        self.launch.assert_called_once_with("App")
