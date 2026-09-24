"""The bridge prepares actions; real policy and validation remain authoritative."""

from dataclasses import replace
import unittest
from unittest.mock import Mock, patch

from nayeon.agent.dispatch import DispatchKind, DispatchPlan, IntentDispatcher
from nayeon.agent.executor import ActionExecutor, ExecutionResult, ExecutionStatus
from nayeon.agent.orchestration import StructuredOrchestrationBridge
from nayeon.agent.router import TaskRouter
from nayeon.audit.service import AuditService
from nayeon.capabilities.open_app import OpenAppCapability
from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentContext, IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.policy.confirmation import ConfirmationService
from nayeon.policy.permissions import PermissionService
from nayeon.policy.service import PolicyService
from nayeon.registry import CapabilityRegistry
from nayeon.undo.service import UndoService


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        service = self.enterContext(patch("nayeon.capabilities.open_app.ApplicationService"))
        self.launch = service.return_value.launch
        self.implementation = OpenAppCapability()
        self.capability = self.implementation.capability
        self.registry = CapabilityRegistry()
        self.registry.register(self.capability, self.implementation)
        self.dispatcher = IntentDispatcher(registry=self.registry)
        self.executor = Mock(spec=ActionExecutor)
        self.executor.execute_structured.return_value = ExecutionResult(
            ExecutionStatus.EXECUTED, "open_app", "fake execution"
        )
        self.bridge = StructuredOrchestrationBridge(registry=self.registry, executor=self.executor)

    def plan(self, arguments):
        return self.dispatcher.plan(IntentResolution(
            "open_app", IntentSource.SEMANTIC, 0.95, arguments
        ))

    def assert_rejected(self, plan, original_request="open App"):
        result = self.bridge.execute(plan, original_request=original_request)
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.executor.execute_structured.assert_not_called()
        self.executor.execute.assert_not_called()
        self.launch.assert_not_called()

    def test_registered_plan_constructs_request_and_calls_executor_once(self):
        plan = self.plan({"application": " App "})
        result = self.bridge.execute(plan, original_request="please open it")
        self.assertIs(result, self.executor.execute_structured.return_value)
        self.executor.execute_structured.assert_called_once()
        capability, request = self.executor.execute_structured.call_args.args
        self.assertIs(capability, self.registry.get("open_app"))
        self.assertIsInstance(request, StructuredCapabilityRequest)
        self.assertEqual(request.original_request, "please open it")
        self.assertEqual(request.arguments, {"application": " App "})
        self.launch.assert_not_called()

    def test_semantic_extra_fields_are_not_forwarded(self):
        plan = self.plan({"application": "App", "shell": "untrusted",
                          "request": "open other", "credential": "fake-sensitive"})
        self.bridge.execute(plan, original_request="please open it")
        request = self.executor.execute_structured.call_args.args[1]
        self.assertEqual(request.arguments, {"application": "App"})
        self.assertEqual(len(plan.arguments), 4)

    def test_local_resolver_dispatch_pipeline_reuses_legacy_target(self):
        resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)))
        for text in ("open App", " LAUNCH Example App ", "start Example App"):
            with self.subTest(text=text):
                self.executor.reset_mock()
                resolved = resolver.resolve(text, context=IntentContext())
                self.assertEqual(resolved.arguments, {"request": text})
                plan = self.dispatcher.plan(resolved)
                self.bridge.execute(plan, original_request=text)
                request = self.executor.execute_structured.call_args.args[1]
                self.implementation.execute(text)
                self.assertEqual(request.arguments, {"application": self.launch.call_args.args[0]})
                self.launch.reset_mock()
                self.executor.execute_structured.assert_called_once()

    def test_local_mapping_has_no_service_side_effect(self):
        self.assertEqual(OpenAppCapability.arguments_from_request(" OPEN App "),
                         {"application": "App"})
        self.launch.assert_not_called()

    def test_unresolved_plan_does_not_execute(self):
        self.assert_rejected(DispatchPlan(DispatchKind.UNRESOLVED, None))

    def test_removed_capability_does_not_execute(self):
        plan = self.plan({"application": "App"})
        self.registry.unregister("open_app")
        self.assert_rejected(plan)

    def test_stale_metadata_does_not_execute(self):
        plan = self.plan({"application": "App"})
        self.registry.unregister("open_app")
        self.registry.register(replace(self.capability, requires_confirmation=True), self.implementation)
        self.assert_rejected(plan)

    def test_missing_plan_capability_does_not_execute(self):
        self.assert_rejected(DispatchPlan(DispatchKind.CAPABILITY, "open_app"))

    def test_legacy_only_implementation_does_not_fall_back(self):
        plan = self.plan({"application": "App"})
        legacy = Mock(spec=["execute"])
        self.registry.unregister("open_app")
        self.registry.register(self.capability, legacy)
        self.assert_rejected(plan)
        legacy.execute.assert_not_called()

    def test_system_controls_are_separate_and_unsupported(self):
        for intent in ("cancel_pending", "undo_last"):
            with self.subTest(intent=intent):
                plan = self.dispatcher.plan(IntentResolution(intent, IntentSource.LOCAL, 1))
                self.assertEqual(plan.kind, DispatchKind.SYSTEM_CONTROL)
                self.assert_rejected(plan)

    def test_other_capabilities_are_not_generalized(self):
        other = replace(self.capability, name="other")
        self.registry.register(other, self.implementation)
        self.assert_rejected(DispatchPlan(DispatchKind.CAPABILITY, "other", other))

    def test_missing_candidate_and_mismatched_legacy_text_are_rejected(self):
        for arguments in ({}, {"target": "App"}, {"request": "open another"}):
            with self.subTest(arguments=arguments):
                self.assert_rejected(self.plan(arguments))

    def test_legacy_mapping_requires_recognized_prefix(self):
        text = "please figure it out"
        self.assert_rejected(self.plan({"request": text}), original_request=text)

    def test_blank_original_request_is_rejected(self):
        self.assert_rejected(self.plan({"application": "App"}), original_request=" ")

    def test_invalid_application_never_falls_back_to_request(self):
        for value in (None, "", " ", 42):
            with self.subTest(value=value):
                self.executor.reset_mock()
                plan = self.plan({"application": value, "request": "open App"})
                self.bridge.execute(plan, original_request="open App")
                self.executor.execute_structured.assert_called_once()
                self.assertEqual(self.executor.execute_structured.call_args.args[1].arguments,
                                 {"application": value})
        self.launch.assert_not_called()

    def test_denied_confirmation_and_validation_results_return_unchanged(self):
        for status in (ExecutionStatus.DENIED, ExecutionStatus.REQUIRES_CONFIRMATION,
                       ExecutionStatus.FAILED):
            with self.subTest(status=status):
                self.executor.reset_mock()
                expected = ExecutionResult(status, "open_app", "executor result")
                self.executor.execute_structured.return_value = expected
                actual = self.bridge.execute(self.plan({"application": "App"}),
                                             original_request="open App")
                self.assertIs(actual, expected)
                self.executor.execute_structured.assert_called_once()

    def real_bridge(self):
        permissions = PermissionService(default_allowed=False)
        executor = ActionExecutor(self.registry, PolicyService(permissions),
                                  ConfirmationService(), AuditService(), UndoService())
        return StructuredOrchestrationBridge(registry=self.registry, executor=executor), permissions

    def test_real_executor_denial_prevents_launch(self):
        bridge, _ = self.real_bridge()
        result = bridge.execute(self.plan({"application": "App"}), original_request="open App")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.launch.assert_not_called()

    def test_real_executor_validation_prevents_launch(self):
        bridge, permissions = self.real_bridge()
        permissions.grant("open_app")
        result = bridge.execute(self.plan({"application": " "}), original_request="open App")
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.launch.assert_not_called()

    def test_real_executor_confirmation_defers_launch(self):
        self.registry.unregister("open_app")
        self.registry.register(replace(self.capability, requires_confirmation=True), self.implementation)
        bridge, permissions = self.real_bridge()
        permissions.grant("open_app")
        result = bridge.execute(self.plan({"application": "App"}), original_request="open App")
        self.assertEqual(result.status, ExecutionStatus.REQUIRES_CONFIRMATION)
        self.assertIsNotNone(result.confirmation_request)
        self.launch.assert_not_called()

    def test_full_local_pipeline_reaches_mocked_service_through_executor(self):
        bridge, permissions = self.real_bridge()
        permissions.grant("open_app")
        resolver = IntentResolver(local=LocalIntentInterpreter(router=TaskRouter(self.registry)))
        text = "launch Example App"
        plan = self.dispatcher.plan(resolver.resolve(text, context=IntentContext()))
        result = bridge.execute(plan, original_request=text)
        self.assertTrue(result.succeeded)
        self.launch.assert_called_once_with("Example App")

    def test_companion_api_returns_result_without_pending_for_terminal_results(self):
        for status in (ExecutionStatus.EXECUTED, ExecutionStatus.DENIED, ExecutionStatus.FAILED):
            with self.subTest(status=status):
                self.executor.reset_mock()
                result = ExecutionResult(status, "open_app", "fake result")
                self.executor.execute_structured.return_value = result
                outcome = self.bridge.execute_with_pending(
                    self.plan({"application": "App"}), original_request="open App",
                )
                self.assertIs(outcome.result, result)
                self.assertIsNone(outcome.pending)
                self.executor.execute_structured.assert_called_once()

    def test_companion_pending_snapshot_is_isolated_from_plan_and_submission(self):
        confirmation = ConfirmationService().create("open_app", "please open it")
        result = ExecutionResult(ExecutionStatus.REQUIRES_CONFIRMATION, "open_app", "pending",
                                 confirmation_request=confirmation)
        self.executor.execute_structured.return_value = result
        plan = self.plan({"application": "App", "discarded": "fake-sensitive"})
        outcome = self.bridge.execute_with_pending(plan, original_request="please open it")
        plan.arguments["application"] = "Other"
        self.executor.execute_structured.call_args.args[1].arguments["application"] = "Changed"
        self.assertIs(outcome.result, result)
        self.assertEqual(outcome.pending.request.arguments, {"application": "App"})
        self.assertEqual(outcome.pending.request.original_request, "please open it")
        self.assertEqual(outcome.pending.token, confirmation.token)
        self.assertIsNot(outcome.pending.capability, self.capability)
        self.launch.assert_not_called()

    def test_companion_rejection_has_no_pending_candidate(self):
        outcome = self.bridge.execute_with_pending(
            DispatchPlan(DispatchKind.SYSTEM_CONTROL, "cancel_pending"), original_request="cancel",
        )
        self.assertEqual(outcome.result.status, ExecutionStatus.DENIED)
        self.assertIsNone(outcome.pending)
        self.executor.execute_structured.assert_not_called()

    def test_unsnapshotable_input_fails_without_execution_or_exception_details(self):
        class Uncopyable:
            def __deepcopy__(self, memo):
                raise ValueError("fake-sensitive-value")

        result = self.bridge.execute(self.plan({"application": Uncopyable()}),
                                     original_request="open App")
        self.assertEqual(result.status, ExecutionStatus.DENIED)
        self.assertNotIn("fake-sensitive-value", result.message)
        self.executor.execute_structured.assert_not_called()
        self.launch.assert_not_called()
