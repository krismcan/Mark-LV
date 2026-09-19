"""Dispatch plans and optional structured contracts do not execute actions."""

import unittest
from unittest.mock import Mock

from nayeon.agent.dispatch import DispatchKind, IntentDispatcher
from nayeon.capabilities.structured import StructuredCapability, StructuredCapabilityRequest
from nayeon.intent.model import IntentResolution, IntentSource
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode


class IntentDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.capability = Capability("example", "Test", ExecutionMode.LOCAL, "fake")
        self.implementation = Mock(spec=["execute"])
        self.registry.register(self.capability, self.implementation)
        self.dispatcher = IntentDispatcher(registry=self.registry)

    def plan(self, intent, **kwargs):
        return self.dispatcher.plan(IntentResolution(
            intent, IntentSource.LOCAL, 1.0, **kwargs
        ))

    def test_registered_capability_is_planned_without_execution(self):
        plan = self.plan(" example ")
        self.assertEqual(plan.kind, DispatchKind.CAPABILITY)
        self.assertTrue(plan.ready)
        self.assertIs(plan.capability, self.capability)
        self.implementation.execute.assert_not_called()

    def test_approved_system_controls_are_planned(self):
        for intent in ("cancel_pending", "undo_last"):
            with self.subTest(intent=intent):
                plan = self.plan(intent)
                self.assertEqual(plan.kind, DispatchKind.SYSTEM_CONTROL)
                self.assertTrue(plan.ready)
                self.assertIsNone(plan.capability)

    def test_unresolved_intent_preserves_reason(self):
        plan = self.plan(None, reason="unclear request")
        self.assertEqual(plan.kind, DispatchKind.UNRESOLVED)
        self.assertFalse(plan.ready)
        self.assertEqual(plan.reason, "unclear request")

    def test_unregistered_capability_is_blocked(self):
        plan = self.plan("unknown")
        self.assertEqual(plan.kind, DispatchKind.UNRESOLVED)
        self.assertFalse(plan.ready)
        self.assertIsNone(plan.capability)
        self.implementation.execute.assert_not_called()

    def test_plan_isolates_top_level_arguments_from_resolution(self):
        result = IntentResolution("example", IntentSource.LOCAL, 1, {"target": "one"})
        plan = self.dispatcher.plan(result)
        result.arguments["target"] = "two"
        self.assertEqual(plan.arguments, {"target": "one"})
        plan.arguments["extra"] = True
        self.assertNotIn("extra", result.arguments)


class StructuredCapabilityTests(unittest.TestCase):
    def test_request_trims_original_text(self):
        self.assertEqual(StructuredCapabilityRequest(" request ").original_request, "request")

    def test_request_rejects_blank_text(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                StructuredCapabilityRequest(text)

    def test_request_copies_top_level_arguments(self):
        arguments = {"target": "one"}
        request = StructuredCapabilityRequest("request", arguments)
        arguments["target"] = "two"
        self.assertEqual(request.arguments, {"target": "one"})
        request.arguments["extra"] = True
        self.assertNotIn("extra", arguments)

    def test_default_argument_dictionaries_are_independent(self):
        first = StructuredCapabilityRequest("one")
        second = StructuredCapabilityRequest("two")
        first.arguments["target"] = "one"
        self.assertEqual(second.arguments, {})

    def test_protocol_accepts_complete_structural_implementation(self):
        class Complete:
            def validate_arguments(self, arguments):
                raise AssertionError("Protocol detection must not invoke validation")

            def execute_structured(self, arguments):
                raise AssertionError("Protocol detection must not execute")

        self.assertIsInstance(Complete(), StructuredCapability)

    def test_protocol_rejects_incomplete_and_legacy_implementations(self):
        class ValidationOnly:
            def validate_arguments(self, arguments):
                return dict(arguments)

        class ExecutionOnly:
            def execute_structured(self, arguments):
                return None

        class Legacy:
            def execute(self, request):
                return None

        for implementation in (ValidationOnly(), ExecutionOnly(), Legacy(), object()):
            with self.subTest(implementation=type(implementation).__name__):
                self.assertNotIsInstance(implementation, StructuredCapability)
