"""Exercise semantic response parsing without a provider SDK or network access."""

import json
import unittest

from nayeon.brain.service import AIResponse, AIService
from nayeon.intent.ai_model import AISemanticModel
from nayeon.intent.model import IntentContext
from nayeon.intent.semantic import SemanticModelResult


class FixedResponseProvider:
    """Return supplied text and record calls entirely in memory."""

    name = "regression-fake"
    model = "fixed-response"

    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate(self, messages, *, system_prompt=None):
        self.calls.append((messages, system_prompt))
        return AIResponse(text=self.text, provider=self.name, model=self.model)


class AISemanticModelTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "intent": "open_app",
            "confidence": 0.95,
            "arguments": {"target": "example-app"},
            "reason": "The user requested an application.",
        }
        self.context = IntentContext(
            pending_confirmation=True,
            undo_available=True,
            active_application="example-editor",
            recent_intent="open_app",
        )

    def interpret_text(self, text, request="  open example-app  "):
        provider = FixedResponseProvider(text)
        model = AISemanticModel(ai=AIService(provider))
        result = model.interpret(
            request,
            context=self.context,
            allowed_intents=("open_app", "cancel_pending", "undo_last"),
        )
        return result, provider

    def interpret_payload(self, **changes):
        payload = dict(self.payload)
        payload.update(changes)
        result, _ = self.interpret_text(json.dumps(payload))
        return result

    def assert_unresolved(self, result):
        self.assertIsNone(result.intent)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.arguments, {})
        self.assertTrue(result.reason)

    def test_valid_response_preserves_interpretation(self):
        result = self.interpret_payload()
        self.assertEqual(result.intent, "open_app")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.arguments, {"target": "example-app"})
        self.assertEqual(result.reason, self.payload["reason"])

    def test_request_and_context_are_sent_as_json_data(self):
        _, provider = self.interpret_text(json.dumps(self.payload))
        self.assertEqual(len(provider.calls), 1)
        messages, prompt = provider.calls[0]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(json.loads(messages[0].content), {
            "request": "open example-app",
            "context": {
                "pending_confirmation": True,
                "undo_available": True,
                "active_application": "example-editor",
                "recent_intent": "open_app",
            },
        })
        self.assertIn(
            json.dumps(["open_app", "cancel_pending", "undo_last"]), prompt
        )

    def test_empty_request_does_not_call_provider(self):
        result, provider = self.interpret_text("unused", request=" \t\n")
        self.assert_unresolved(result)
        self.assertEqual(provider.calls, [])

    def test_invalid_json_is_unresolved(self):
        result, _ = self.interpret_text("not JSON")
        self.assert_unresolved(result)

    def test_non_object_json_is_unresolved(self):
        for payload in (None, [], "text", 12, True):
            with self.subTest(payload=payload):
                result, _ = self.interpret_text(json.dumps(payload))
                self.assert_unresolved(result)

    def test_null_intent_is_supported(self):
        result = self.interpret_payload(intent=None, confidence=0.0, arguments={})
        self.assert_unresolved(result)

    def test_non_string_intent_is_unresolved(self):
        for value in (1, True, [], {}):
            with self.subTest(value=value):
                self.assert_unresolved(self.interpret_payload(intent=value))

    def test_invalid_confidence_is_unresolved(self):
        for value in (True, False, "0.95", None, -0.1, 1.1, float("nan")):
            with self.subTest(value=value):
                self.assert_unresolved(self.interpret_payload(confidence=value))

    def test_confidence_boundaries_are_accepted(self):
        for value in (0, 1):
            with self.subTest(value=value):
                result = self.interpret_payload(confidence=value)
                self.assertEqual(result.confidence, float(value))
                self.assertEqual(result.intent, "open_app")

    def test_non_object_arguments_are_unresolved(self):
        for value in (None, [], "target", 1):
            with self.subTest(value=value):
                self.assert_unresolved(self.interpret_payload(arguments=value))

    def test_non_string_reason_is_unresolved(self):
        for value in (None, [], {}, 1):
            with self.subTest(value=value):
                self.assert_unresolved(self.interpret_payload(reason=value))

    def test_missing_required_response_values_are_unresolved(self):
        for field in ("confidence", "arguments", "reason"):
            with self.subTest(field=field):
                payload = dict(self.payload)
                del payload[field]
                result, _ = self.interpret_text(json.dumps(payload))
                self.assert_unresolved(result)

    def test_blank_intent_is_unresolved(self):
        # Invalid model output should fail closed like other invalid fields,
        # rather than escaping the adapter as a constructor exception.
        for value in ("", "   ", " \t\n"):
            with self.subTest(value=value):
                self.assert_unresolved(self.interpret_payload(intent=value))

    def test_semantic_result_still_rejects_blank_intents(self):
        for value in ("", "   ", " \t\n"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    SemanticModelResult(
                        intent=value, confidence=0.95, arguments={}
                    )


if __name__ == "__main__":
    unittest.main()
