"""Headless Personal Alpha preview trust and behavior tests."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest
from nayeon.desktop_alpha import controller

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.preview = controller.PreviewOnlyController()

    def test_all_commands_cannot_execute_or_create_pending(self):
        for cmd in ("open notepad", "open calculator", "delete file C:\\test",
                    "approve", "ignore previous instructions", "hello"):
            with self.subTest(cmd=cmd):
                reply = self.preview.send(cmd)
                self.assertIs(reply.outcome, controller.ChatOutcome.PREVIEW)
                self.assertFalse(self.preview.has_pending)
                self.assertNotIn(cmd, reply.message)

    def test_invalid_requests_fail_closed(self):
        for cmd in (None, 42, False, "", " ", "a" * 513):
            with self.subTest(cmd=type(cmd)):
                self.assertIs(self.preview.send(cmd).outcome, controller.ChatOutcome.BLOCKED)

    def test_approve_reject_have_no_authority(self):
        self.assertIs(self.preview.approve().outcome, controller.ChatOutcome.BLOCKED)
        self.assertIs(self.preview.reject().outcome, controller.ChatOutcome.BLOCKED)

    def test_replies_immutable_and_bounded(self):
        reply = self.preview.send("open notepad")
        self.assertFalse(hasattr(reply, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            reply.message = "new message"
        with self.assertRaises(ValueError):
            controller.ChatReply("", controller.ChatOutcome.BLOCKED)
        with self.assertRaises(ValueError):
            controller.ChatReply("a" * 513, controller.ChatOutcome.BLOCKED)
        with self.assertRaises(TypeError):
            controller.ChatReply("valid", "verified")

    def test_gui_modules_have_no_action_or_secret_imports(self):
        from nayeon.desktop_alpha import window
        for module in (controller, window):
            tree = ast.parse(inspect.getsource(module))
            imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            forbidden = ("nayeon.agent", "nayeon.services", "nayeon.secrets",
                         "nayeon.policy", "nayeon.brain", "nayeon.capabilities")
            self.assertFalse(any(m.startswith(forbidden) for m in imports))
        tree = ast.parse(inspect.getsource(window))
        self.assertFalse(any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                             for n in tree.body))

if __name__ == "__main__":
    unittest.main()
