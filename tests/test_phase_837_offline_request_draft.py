"""Increment A pure data tests; no provider, Tk or real effects."""
import ast
from dataclasses import FrozenInstanceError, fields
import inspect
import json
from pathlib import Path
import unittest

from nayeon.desktop_alpha import offline_request_draft as module
from nayeon.desktop_alpha.conversation_session import (
    MAX_INPUT_CODE_POINTS, MAX_INPUT_UTF8_BYTES, SessionRefused,
)
from nayeon.desktop_alpha.offline_request_draft import (
    DISCLOSURE, OfflineDraftReceipt, OfflineRequestDraft,
)


class HostileText(str):
    def __eq__(self, other):
        raise AssertionError("untrusted equality called")

    def __str__(self):
        raise AssertionError("untrusted conversion called")


class HostileSource:
    def __getattribute__(self, name):
        raise AssertionError("untrusted source accessed")


class OfflineRequestDraftTests(unittest.TestCase):
    def draft(self, **changes):
        values = dict(provider="openai", model="gpt-example_1.0", prompt="Hello")
        values.update(changes)
        return OfflineRequestDraft(**values)

    def test_valid_ascii_model_boundaries(self):
        for model in ("a", "A0._-", "x" * 80,
                      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"):
            with self.subTest(model=model):
                self.assertEqual(self.draft(model=model).model, model)

    def test_provider_exact_type_and_literal(self):
        for value in (None, 1, True, b"openai", "", "OpenAI", "OPENAI",
                      "openai ", " openai", "openai/", "openai\n",
                      "openаi", "openai\u202e", HostileText("openai")):
            with self.subTest(value=type(value)):
                with self.assertRaisesRegex(ValueError, "^DRAFT_PROVIDER$"):
                    self.draft(provider=value)

    def test_model_rejects_non_allowlisted_values(self):
        for value in (None, 1, True, b"a", "", "x" * 81, "a b", " a", "a ",
                      "a/b", "a\\b", "a:b", "a@b", "a\"b", "a\tb", "a\nb",
                      "a\x00b", "a\x7fb", "é", "а", "全", "😀", "a\u00a0b",
                      "a\u200bb", "a\u202eb", "a\u2066b", "a\ud800b",
                      HostileText("valid")):
            with self.subTest(value=type(value)):
                with self.assertRaisesRegex(ValueError, "^DRAFT_MODEL$"):
                    self.draft(model=value)
        for code in range(33):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    self.draft(model="a" + chr(code))

    def test_prompt_uses_existing_bounds_and_unicode_rules(self):
        for value in (None, 1, True, b"hi", [], {}, HostileText("hi"), "", "  ",
                      "x" * (MAX_INPUT_CODE_POINTS + 1), "e\u0301", "a\n", "a\r",
                      "a\t", "a\x00", "a\x7f", "a\u202e", "a\u2066",
                      "a\u2028", "a\u2029", "a\ud800"):
            with self.subTest(value=type(value)):
                with self.assertRaises(SessionRefused):
                    self.draft(prompt=value)
        prompt = "😀" * MAX_INPUT_CODE_POINTS
        self.assertEqual(len(prompt.encode("utf-8")), MAX_INPUT_UTF8_BYTES)
        self.assertEqual(json.loads(self.draft(prompt=prompt).to_json())
                         ["input"][0]["content"], prompt)

    def test_prompt_literal_preserved_and_json_escaped(self):
        prompt = '  café 😀 "model": "other", "tools": [{}] \\  '
        draft = self.draft(prompt=prompt)
        self.assertEqual(json.loads(draft.to_json()), {
            "model": draft.model, "input": [{"role": "user", "content": prompt}],
        })
        self.assertEqual(draft.prompt, prompt)
        self.assertTrue(draft.to_json().isascii())

    def test_exact_payload_cardinality_order_and_determinism(self):
        draft = self.draft()
        expected = ('{"model":"gpt-example_1.0",'
                    '"input":[{"role":"user","content":"Hello"}]}')
        self.assertEqual(draft.to_json(), expected)
        self.assertEqual(draft.to_json(), expected)
        payload = json.loads(expected)
        self.assertEqual(list(payload), ["model", "input"])
        self.assertEqual(len(payload["input"]), 1)
        self.assertEqual(list(payload["input"][0]), ["role", "content"])

    def test_draft_and_receipt_immutable_without_writable_graph(self):
        draft = self.draft()
        receipt = OfflineDraftReceipt(draft)
        for obj in (draft, receipt):
            self.assertFalse(hasattr(obj, "__dict__"))
            for item in fields(obj):
                with self.assertRaises(FrozenInstanceError):
                    setattr(obj, item.name, None)
                with self.assertRaises(FrozenInstanceError):
                    delattr(obj, item.name)
        payload = json.loads(draft.to_json())
        payload["input"][0]["content"] = "changed"
        self.assertEqual(json.loads(draft.to_json())["input"][0]["content"], "Hello")

    def test_strict_unbound_encoder_source_and_no_conversion_hooks(self):
        for source in (None, {}, "text", HostileSource()):
            with self.assertRaisesRegex(ValueError, "^DRAFT_SOURCE$"):
                OfflineRequestDraft.to_json(source)
            with self.assertRaisesRegex(ValueError, "^DRAFT_SOURCE$"):
                OfflineDraftReceipt(source)
        class Derived(OfflineRequestDraft):
            pass
        with self.assertRaisesRegex(ValueError, "^DRAFT_SOURCE$"):
            Derived("openai", "a", "hi")
        with self.assertRaisesRegex(ValueError, "^DRAFT_SOURCE$"):
            OfflineRequestDraft.to_json(object.__new__(Derived))
        forged = object.__new__(OfflineRequestDraft)
        object.__setattr__(forged, "provider", HostileText("openai"))
        object.__setattr__(forged, "model", "a")
        object.__setattr__(forged, "prompt", "hi")
        with self.assertRaisesRegex(ValueError, "^DRAFT_PROVIDER$"):
            OfflineRequestDraft.to_json(forged)
        with self.assertRaisesRegex(ValueError, "^DRAFT_PROVIDER$"):
            OfflineDraftReceipt(forged)

    def test_extra_fields_cannot_enter_constructor_or_payload(self):
        for name in ("token", "credentials", "tools", "transcript", "identity",
                     "headers", "instructions", "permits_network"):
            with self.subTest(name=name):
                with self.assertRaises(TypeError):
                    self.draft(**{name: "untrusted"})

    def test_receipt_and_output_never_confer_future_permission(self):
        draft = self.draft()
        receipt = OfflineDraftReceipt(draft)
        self.assertIs(receipt.draft, draft)
        self.assertEqual(receipt.status, "NO REQUEST WAS SENT")
        self.assertEqual(receipt.disclosure, DISCLOSURE)
        self.assertEqual(DISCLOSURE,
                         "LOCAL REQUEST DRAFT — MODEL AVAILABILITY UNCHECKED — NOTHING SENT")
        for name in ("permits_network", "permits_action", "permits_persistence"):
            self.assertIs(getattr(receipt, name), False)
            with self.assertRaises(TypeError):
                OfflineDraftReceipt(draft, **{name: True})
        self.assertEqual([item.name for item in fields(draft)],
                         ["provider", "model", "prompt"])
        with self.assertRaises(TypeError):
            self.draft(token="future consent")
        self.assertNotIn("Hello", repr(draft))
        self.assertNotIn("Hello", repr(receipt))

    def test_source_import_and_callable_surface_is_pure(self):
        tree = ast.parse(inspect.getsource(module))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {
                    "open", "exec", "eval", "compile", "__import__", "getattr",
                })
        self.assertEqual(imports, {
            "__future__", "dataclasses", "json",
            "nayeon.desktop_alpha.conversation_session",
        })
        self.assertEqual({name for name, value in vars(module).items()
                          if inspect.isfunction(value) and value.__module__ == module.__name__},
                         {"_validate"})
        self.assertEqual({node.name for node in tree.body if isinstance(node, ast.ClassDef)},
                         {"OfflineRequestDraft", "OfflineDraftReceipt"})
        methods = {
            node.name: {child.name for child in node.body
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))}
            for node in tree.body if isinstance(node, ast.ClassDef)
        }
        self.assertEqual(methods, {
            "OfflineRequestDraft": {"__post_init__", "to_json"},
            "OfflineDraftReceipt": {"__post_init__"},
        })
        # The one existing pure dependency imports only standard data utilities.
        dependency = Path(module.__file__).with_name("conversation_session.py")
        dependency_tree = ast.parse(dependency.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(dependency_tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        self.assertEqual(names, {"__future__", "dataclasses", "enum", "unicodedata"})


if __name__ == "__main__":
    unittest.main()
