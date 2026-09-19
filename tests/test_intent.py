"""Intent models, local preference, confidence gates, and semantic authority."""

import unittest
from unittest.mock import Mock

from nayeon.agent.router import TaskRouter
from nayeon.intent.local import LocalIntentInterpreter
from nayeon.intent.model import IntentContext, IntentResolution, IntentSource
from nayeon.intent.resolver import IntentResolver
from nayeon.intent.semantic import SemanticIntentInterpreter, SemanticModelResult
from nayeon.registry import Capability, CapabilityRegistry, ExecutionMode


def resolution(intent="open_app", confidence=0.95, source=IntentSource.LOCAL):
    return IntentResolution(intent, source, confidence)


def app_registry():
    registry = CapabilityRegistry()
    registry.register(Capability(
        name="open_app", description="Test metadata only",
        execution_mode=ExecutionMode.LOCAL, service="applications",
        intent_patterns=("open ", "launch "),
    ))
    return registry


class IntentResolutionTests(unittest.TestCase):
    def test_rejects_invalid_confidence(self):
        for value in (-0.01, 1.01, float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolution(confidence=value)

    def test_accepts_confidence_endpoints(self):
        for value in (0.0, 1.0):
            with self.subTest(value=value):
                self.assertEqual(resolution(confidence=value).confidence, value)

    def test_rejects_blank_intent(self):
        for value in ("", " \t"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolution(intent=value)

    def test_properties_distinguish_understood_and_unresolved(self):
        self.assertTrue(resolution().understood)
        self.assertFalse(resolution().needs_semantic_fallback)
        missing = resolution(None, 0.0, IntentSource.NONE)
        self.assertFalse(missing.understood)
        self.assertTrue(missing.needs_semantic_fallback)
        semantic_missing = resolution(None, 0.0, IntentSource.SEMANTIC)
        self.assertFalse(semantic_missing.needs_semantic_fallback)

    def test_arguments_are_copied_at_top_level(self):
        arguments = {"target": "one"}
        result = IntentResolution("open_app", IntentSource.LOCAL, 1, arguments)
        arguments["target"] = "two"
        self.assertEqual(result.arguments, {"target": "one"})
        result.arguments["extra"] = True
        self.assertNotIn("extra", arguments)

    def test_default_arguments_are_not_shared(self):
        first, second = resolution(), resolution()
        first.arguments["target"] = "one"
        self.assertEqual(second.arguments, {})


class IntentResolverTests(unittest.TestCase):
    def setUp(self):
        self.context = IntentContext(pending_confirmation=True)
        self.local = Mock(spec=["resolve"])
        self.semantic = Mock(spec=["resolve"])
        self.local.resolve.return_value = resolution(None, 0, IntentSource.NONE)
        self.semantic.resolve.return_value = resolution(
            confidence=0.9, source=IntentSource.SEMANTIC
        )

    def resolve(self, **settings):
        return IntentResolver(
            local=self.local, semantic=self.semantic, **settings
        ).resolve("request", context=self.context)

    def test_local_threshold_is_inclusive_and_skips_semantic(self):
        self.local.resolve.return_value = resolution(confidence=0.9)
        self.assertIs(self.resolve(), self.local.resolve.return_value)
        self.semantic.resolve.assert_not_called()

    def test_low_local_confidence_falls_back_with_same_context(self):
        self.local.resolve.return_value = resolution(confidence=0.89)
        self.assertIs(self.resolve(), self.semantic.resolve.return_value)
        self.local.resolve.assert_called_once_with("request", context=self.context)
        self.semantic.resolve.assert_called_once_with("request", context=self.context)

    def test_unresolved_local_falls_back(self):
        self.assertIs(self.resolve(), self.semantic.resolve.return_value)

    def test_semantic_threshold_is_inclusive(self):
        self.semantic.resolve.return_value = resolution(
            confidence=0.85, source=IntentSource.SEMANTIC
        )
        self.assertIs(self.resolve(), self.semantic.resolve.return_value)

    def test_low_semantic_confidence_is_not_accepted(self):
        self.semantic.resolve.return_value = resolution(
            confidence=0.849, source=IntentSource.SEMANTIC
        )
        result = self.resolve()
        self.assertTrue(result.needs_semantic_fallback)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.arguments, {})

    def test_custom_thresholds_are_honored(self):
        self.local.resolve.return_value = resolution(confidence=0.91)
        self.assertIs(
            self.resolve(local_confidence_threshold=0.95),
            self.semantic.resolve.return_value,
        )
        self.assertFalse(self.resolve(semantic_confidence_threshold=0.99,
                                      local_confidence_threshold=0.95).understood)

    def test_unresolved_semantic_is_not_accepted(self):
        self.semantic.resolve.return_value = resolution(None, 1, IntentSource.NONE)
        self.assertFalse(self.resolve().understood)

    def test_no_semantic_provider_leaves_low_confidence_unresolved(self):
        self.local.resolve.return_value = resolution(confidence=0.89)
        result = IntentResolver(local=self.local).resolve("request", context=self.context)
        self.assertTrue(result.needs_semantic_fallback)

    def test_invalid_thresholds_are_rejected(self):
        for name in ("local_confidence_threshold", "semantic_confidence_threshold"):
            for value in (-0.1, 1.1, float("nan")):
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    IntentResolver(local=self.local, **{name: value})


class LocalIntentInterpreterTests(unittest.TestCase):
    def setUp(self):
        self.interpreter = LocalIntentInterpreter(router=TaskRouter(app_registry()))

    def test_registered_capability_preserves_original_request(self):
        request = "  OPEN example-app  "
        result = self.interpreter.resolve(request, context=IntentContext())
        self.assertEqual(result.intent, "open_app")
        self.assertEqual(result.source, IntentSource.LOCAL)
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.arguments, {"request": request})

    def test_unknown_request_needs_semantic_fallback(self):
        result = self.interpreter.resolve("explain this", context=IntentContext())
        self.assertTrue(result.needs_semantic_fallback)

    def test_pending_action_takes_precedence_over_undo(self):
        for request in ("undo that", "actually scratch that", "cancel that"):
            with self.subTest(request=request):
                result = self.interpreter.resolve(request, context=IntentContext(
                    pending_confirmation=True, undo_available=True
                ))
                self.assertEqual(result.intent, "cancel_pending")
                self.assertEqual(result.confidence, 1.0)

    def test_completed_action_can_be_undone(self):
        for request in ("please undo that", "scratch that"):
            with self.subTest(request=request):
                result = self.interpreter.resolve(
                    request, context=IntentContext(undo_available=True)
                )
                self.assertEqual(result.intent, "undo_last")

    def test_controls_without_relevant_context_remain_unresolved(self):
        for request in ("undo that", "cancel that", "scratch that"):
            with self.subTest(request=request):
                self.assertFalse(self.interpreter.resolve(
                    request, context=IntentContext()
                ).understood)


class SemanticAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.registry = app_registry()
        self.model = Mock(spec=["interpret"])
        self.interpreter = SemanticIntentInterpreter(
            model=self.model, registry=self.registry
        )

    def resolve(self, intent):
        self.model.interpret.return_value = SemanticModelResult(
            intent, 0.95, {"target": "example-app"}, "test interpretation"
        )
        return self.interpreter.resolve("request", context=IntentContext())

    def test_registered_intent_is_accepted_and_normalized(self):
        result = self.resolve(" open_app ")
        self.assertEqual(result.intent, "open_app")
        self.assertEqual(result.source, IntentSource.SEMANTIC)
        self.assertEqual(result.arguments, {"target": "example-app"})

    def test_system_controls_are_allowed_without_registration(self):
        for intent in ("cancel_pending", "undo_last"):
            with self.subTest(intent=intent):
                self.assertEqual(self.resolve(intent).intent, intent)

    def test_unknown_intent_is_blocked(self):
        result = self.resolve("invented_capability")
        self.assertFalse(result.understood)
        self.assertEqual(result.confidence, 0)
        self.assertEqual(result.arguments, {})

    def test_null_intent_remains_unresolved(self):
        self.assertTrue(self.resolve(None).needs_semantic_fallback)

    def test_model_receives_only_current_registry_and_system_intents(self):
        self.resolve("open_app")
        self.assertEqual(self.model.interpret.call_args.kwargs["allowed_intents"],
                         ("cancel_pending", "open_app", "undo_last"))
        self.registry.unregister("open_app")
        self.assertFalse(self.resolve("open_app").understood)
        self.assertNotIn("open_app", self.model.interpret.call_args.kwargs["allowed_intents"])
