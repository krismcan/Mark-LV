"""Deterministic end-to-end Notepad Alpha trust-path tests; absolutely no OS launch."""
import ast
import inspect
import unittest
from unittest.mock import Mock

from nayeon.desktop_alpha.controller import ChatOutcome
from nayeon.desktop_alpha import notepad as alpha
from nayeon.services.applications import LaunchResult
from nayeon.services.application_observation import (
    ApplicationObservation, ApplicationIdentity, ApplicationState,
)


class NotepadAlphaTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock(spec=["trusted_notepad_path", "launch", "observe_readiness"])
        self.service.trusted_notepad_path = r"C:\Trusted\notepad.exe"
        self.service.launch.return_value = LaunchResult(True, "notepad", "test-only")
        self.service.observe_readiness.return_value = ApplicationObservation(
            "notepad", ApplicationState.OBSERVED_OPEN, "notepad",
            ("notepad.exe",), ApplicationIdentity.MATCHED)
        self.controller = alpha.build_notepad_controller(application_service=self.service)

    def request(self):
        result = self.controller.send("open notepad")
        self.assertIs(result.outcome, ChatOutcome.PENDING)
        self.assertTrue(self.controller.has_pending)
        self.service.launch.assert_not_called()
        self.service.observe_readiness.assert_not_called()
        return result

    def test_request_requires_explicit_click_and_verifies_correct_identity(self):
        pending = self.request()
        self.assertNotIn("token", pending.message)
        result = self.controller.approve()
        self.assertIs(result.outcome, ChatOutcome.VERIFIED)
        self.assertFalse(self.controller.has_pending)
        self.service.launch.assert_called_once_with("notepad")
        self.service.observe_readiness.assert_called_once_with("notepad")
        self.assertIs(self.controller.approve().outcome, ChatOutcome.BLOCKED)
        self.service.launch.assert_called_once()

    def test_rejection_cancels_without_launch_and_cannot_replay(self):
        self.request()
        reply = self.controller.reject()
        self.assertIs(reply.outcome, ChatOutcome.BLOCKED)
        self.assertFalse(self.controller.has_pending)
        self.assertIs(self.controller.approve().outcome, ChatOutcome.BLOCKED)
        self.service.launch.assert_not_called()

    def test_only_exact_local_command_accepted(self):
        for text in ("open calculator", "open notepad.exe", "launch notepad",
                     "open notepad & calc", "open notepad\ncmd", "please open notepad",
                     "approve", "", "a" * 513, 17, None):
            with self.subTest(text=text):
                reply = self.controller.send(text)
                self.assertIs(reply.outcome, ChatOutcome.BLOCKED)
                self.assertFalse(self.controller.has_pending)
        self.service.launch.assert_not_called()

    def test_pending_blocks_second_request_and_never_implies_approval(self):
        self.request()
        self.assertIs(self.controller.send("open notepad").outcome, ChatOutcome.BLOCKED)
        self.service.launch.assert_not_called()
        self.controller.reject()

    def test_missing_trusted_path_refuses_to_prepare_or_launch(self):
        self.service.trusted_notepad_path = None
        reply = self.controller.send("open notepad")
        self.assertIs(reply.outcome, ChatOutcome.BLOCKED)
        self.assertFalse(self.controller.has_pending)
        self.service.launch.assert_not_called()

    def test_removed_path_during_pending_cancels_before_execution(self):
        self.request()
        self.service.trusted_notepad_path = None
        self.assertIs(self.controller.approve().outcome, ChatOutcome.BLOCKED)
        self.assertFalse(self.controller.has_pending)
        self.service.launch.assert_not_called()

    def test_failed_receipt_never_becomes_verified(self):
        self.service.launch.return_value = LaunchResult(False, "notepad", "test-failure-secret")
        self.request()
        result = self.controller.approve()
        self.assertIs(result.outcome, ChatOutcome.BLOCKED)
        self.assertNotIn("test-failure-secret", result.message)
        self.service.observe_readiness.assert_not_called()

    def test_unmatched_or_unavailable_identity_is_not_verified(self):
        for state, identity in (
            (ApplicationState.OBSERVED_OPEN, ApplicationIdentity.MISMATCHED),
            (ApplicationState.OBSERVED_OPEN, ApplicationIdentity.UNKNOWN),
            (ApplicationState.UNKNOWN, ApplicationIdentity.UNKNOWN),
            (ApplicationState.OBSERVED_CLOSED, ApplicationIdentity.UNKNOWN),
        ):
            with self.subTest(state=state, identity=identity):
                self.service.reset_mock()
                self.service.observe_readiness.return_value = ApplicationObservation(
                    "notepad", state, "notepad", ("notepad.exe",), identity)
                self.request()
                self.assertIs(self.controller.approve().outcome, ChatOutcome.EXECUTED_UNVERIFIED)
                self.assertFalse(self.controller.has_pending)

    def test_no_llm_and_exclusive_permission_scope(self):
        self.assertIsNone(self.controller._session._resolver._semantic)
        reg = self.controller._session._dispatcher._registry
        self.assertEqual([x.name for x in reg.all()], ["open_app"])
        perm = self.controller._session._executor._policy._permissions
        self.assertFalse(perm.check("delete_file").allowed)
        self.assertTrue(perm.check("open_app").allowed)
        self.assertTrue(reg.get("open_app").requires_confirmation)

    def test_controller_does_not_replay_approval_or_launch_directly(self):
        tree = ast.parse(inspect.getsource(alpha))
        modules = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn("subprocess", modules)
        calls = [n.func.attr for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertNotIn("Popen", calls)
        self.assertNotIn("startfile", calls)
        self.assertNotIn("execute_structured", calls)
        self.assertNotIn("approve_and_execute_structured", calls)


if __name__ == "__main__":
    unittest.main()
