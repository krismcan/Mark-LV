"""Phase 8.25: fake-only trusted Tk entry and manual candidate validation."""
import ast
import inspect
import unittest
from unittest.mock import Mock, patch

from nayeon.brain.connection_reconciliation import ConnectionObservationStatus as State
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Operation
from nayeon.brain.credential_operation_host import CredentialHostOutcome
from nayeon.desktop_alpha import first_run_credential_validation_window as m
from tests.test_credential_operation_host import factory


class FakeWidget:
    def __init__(self, *args, **kwargs):
        self.props = dict(kwargs)
    def pack(self, *args, **kwargs):
        pass
    def configure(self, **kwargs):
        self.props.update(kwargs)


class FakeEntry(FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = ""
        self.bindings = {}
        self.gets = 0
    def bind(self, sequence, callback):
        self.bindings[sequence] = callback
    def get(self):
        self.gets += 1
        return self.value
    def delete(self, first, last):
        # Model real Tk: a disabled Entry silently refuses deletion.
        if self.props.get("state") != "disabled":
            self.value = ""


class CandidateEntryTests(unittest.TestCase):
    def build(self, state=State.SETUP_REQUIRED):
        host, backend, validator, change = factory(state)
        root = Mock()
        labels, buttons, entries = [], [], []
        def label(*a, **kw):
            w = FakeWidget(*a, **kw)
            labels.append(w)
            return w
        def button(*a, **kw):
            w = FakeWidget(*a, **kw)
            buttons.append(w)
            return w
        def entry(*a, **kw):
            w = FakeEntry(*a, **kw)
            entries.append(w)
            return w
        with patch.object(m.tk, "Label", side_effect=label), patch.object(
                m.tk, "Button", side_effect=button), patch.object(
                m.tk, "Entry", side_effect=entry):
            panel = m.FirstRunCredentialValidationWindow(root, host=host)
        self.assertEqual(len(entries), 1)
        return panel, host, backend, validator, change, root, buttons

    def test_construction_has_no_operations_or_probe(self):
        panel, host, b, v, state, root, buttons = self.build()
        self.assertFalse(host.has_pending)
        self.assertEqual((b.gets,b.puts,b.deletes,v.calls), (0,0,0,0))
        self.assertEqual(panel._entry.gets, 0)
        self.assertEqual(panel._entry.props["show"], "*")
        self.assertFalse(panel._entry.props["exportselection"])
        self.assertEqual(panel._entry.props["state"], "disabled")
        self.assertEqual(len(buttons), 3)
        root.protocol.assert_called_once()

    def test_copy_cut_event_bindings_refuse(self):
        panel, *_ = self.build()
        for sequence in ("<<Copy>>", "<<Cut>>", "<Control-c>", "<Control-x>"):
            self.assertEqual(panel._entry.bindings[sequence](None), "break")

    def test_validation_requires_two_deliberate_clicks_and_never_saves(self):
        panel, host, b, v, state, root, buttons = self.build()
        self.assertIsNone(panel.approve_from_button())
        self.assertEqual(v.calls,0)
        buttons[0].props["command"]()
        self.assertTrue(host.has_pending)
        self.assertEqual(panel._approve.props["state"], "normal")
        self.assertEqual(panel._request.props["state"], "disabled")
        self.assertEqual(v.calls,0)
        panel._entry.value = "fixture-good"
        buttons[1].props["command"]()
        self.assertFalse(host.has_pending)
        self.assertEqual(v.calls,1)
        self.assertEqual((b.puts,b.deletes,b.gets),(0,0,0))
        self.assertEqual(panel._entry.value,"")
        self.assertIn("not saved",panel._status.props["text"].lower())
        panel.approve_from_button()
        self.assertEqual(v.calls,1)

    def test_invalid_candidate_never_persists_or_displays_marker(self):
        panel, host, b, v, *_ = self.build()
        panel.request_from_button()
        panel._entry.value = "fixture-unsafe-marker"
        panel.approve_from_button()
        self.assertEqual((b.puts,b.deletes,b.gets,v.calls),(0,0,0,1))
        self.assertNotIn("fixture-unsafe-marker",str(panel._status.props))
        self.assertEqual(panel._entry.value,"")
        self.assertIn("rejected",panel._status.props["text"])

    def test_blank_candidate_consumes_review_without_validator_call(self):
        panel, host, b, v, *_ = self.build()
        panel.request_from_button()
        panel.approve_from_button()
        self.assertFalse(host.has_pending)
        self.assertEqual((b.puts,v.calls),(0,0))
        self.assertIn("unavailable",panel._status.props["text"])

    def test_reject_clears_without_validation(self):
        panel, host, b, v, *_ = self.build()
        panel.request_from_button()
        panel._entry.value="fixture-good"
        panel._reject.props["command"]()
        self.assertFalse(host.has_pending)
        self.assertEqual(panel._entry.value,"")
        self.assertEqual(v.calls,0)
        panel.approve_from_button()
        self.assertEqual(v.calls,0)

    def test_window_close_rejects_and_does_not_validate(self):
        panel, host, b, v, change, root, _ = self.build()
        panel.request_from_button()
        panel._entry.value="fixture-good"
        panel.close_from_window()
        self.assertFalse(host.has_pending)
        self.assertEqual(v.calls,0)
        self.assertEqual(panel._entry.value,"")
        root.destroy.assert_called_once()

    def test_unsupported_unknown_changed_fail_closed(self):
        for state in (State.UNKNOWN,State.UNSUPPORTED_CONFIGURATION,
                      State.CHANGED_DURING_OBSERVATION):
            with self.subTest(state=state):
                panel, host, b, v, *_ = self.build(state)
                panel.request_from_button()
                self.assertFalse(host.has_pending)
                self.assertEqual(panel._entry.props["state"],"disabled")
                self.assertIn("unavailable",panel._status.props["text"])
                self.assertEqual((b.puts,b.gets,v.calls),(0,0,0))

    def test_state_change_between_clicks_blocks_validation(self):
        panel, host, b, v, state, *_ = self.build()
        panel.request_from_button()
        state[0]=State.VALIDATION_REQUIRED
        panel._entry.value="fixture-good"
        panel.approve_from_button()
        self.assertEqual((b.puts,v.calls),(0,0))
        self.assertIn("blocked",panel._status.props["text"])

    def test_unavailable_validator_is_redacted(self):
        panel, host, b, v, *_ = self.build()
        def fail(secret):
            raise RuntimeError("sensitive-test-sentinel")
        v.validate = fail
        panel.request_from_button()
        panel._entry.value="sensitive-test-sentinel"
        panel.approve_from_button()
        self.assertNotIn("sensitive-test-sentinel",str(panel._status.props))
        self.assertIn("inconclusive",panel._status.props["text"])
        self.assertEqual(b.puts,0)

    def test_duplicate_request_does_not_overwrite_pending(self):
        panel, host, b, v, *_=self.build()
        panel.request_from_button()
        panel.request_from_button()
        self.assertTrue(host.has_pending)
        self.assertEqual(v.calls,0)
        panel.reject_from_button()

    def test_requires_exact_host(self):
        with self.assertRaises(TypeError):
            m.FirstRunCredentialValidationWindow(Mock(),host=Mock())

    def test_ui_isolated_from_storage_and_model_routes(self):
        tree=ast.parse(inspect.getsource(m))
        imports={node.module for node in ast.walk(tree)
                 if isinstance(node,ast.ImportFrom)}
        self.assertEqual(imports,{
            "nayeon.brain.credential_operation_host",
            "nayeon.brain.onboarding_operation_advice",
            "nayeon.secrets.contracts",
        })
        called={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id
                for n in ast.walk(tree) if isinstance(n,ast.Call)
                and isinstance(n.func,(ast.Attribute,ast.Name))}
        for blocked in ("reveal","put","get_stored","connect",
                        "replace","remove","Popen","eval","exec"):
            self.assertNotIn(blocked,called)
        # Only Tk Entry.delete is allowed: it clears the visible field,
        # and must not mask an accidental credential backend delete.
        deletions=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
                   and isinstance(n.func,ast.Attribute) and n.func.attr=="delete"]
        self.assertEqual(len(deletions),1)
        self.assertTrue(all(ast.unparse(n.func.value)=="self._entry"
                            for n in deletions))
        self.assertIn("approve_candidate_validation",called)
        self.assertNotIn("approve",called)
        self.assertNotIn("WindowsCredentialBackend",called)


if __name__ == "__main__":
    unittest.main()


class SharedHostAdversarialTests(CandidateEntryTests):
    def test_other_review_window_connect_cannot_execute_from_validation_panel(self):
        panel, host, b, v, *_ = self.build()
        self.assertTrue(host.request(Operation.CONNECT))
        panel._entry.value = "fixture-good"
        panel.approve_from_button()
        self.assertEqual((b.puts,b.deletes,v.calls),(0,0,0))
        self.assertTrue(host.has_pending)
        panel.reject_from_button()
        self.assertTrue(host.has_pending, "Validation UI must not reject another window's review")
        self.assertEqual(b.puts,0)

    def test_other_window_replace_cannot_adopt_validation_ticket(self):
        panel, host, b, v, state, *_ = self.build(State.VALIDATION_REQUIRED)
        from nayeon.secrets.contracts import SecretValue
        b.value = SecretValue("fixture-existing")
        self.assertTrue(host.request(Operation.REPLACE))
        panel._entry.value = "fixture-good"
        panel.approve_from_button()
        self.assertEqual((b.puts,b.deletes,v.calls),(0,0,0))
        self.assertTrue(host.has_pending)

    def test_review_cancelled_then_replaced_with_connect_cannot_reuse_ticket(self):
        panel, host, b, v, *_ = self.build()
        panel.request_from_button()
        old_token = panel._validation_ticket
        self.assertIsInstance(old_token,str)
        host.reject()
        self.assertTrue(host.request(Operation.CONNECT))
        panel._entry.value = "fixture-good"
        panel.approve_from_button()
        self.assertEqual((b.puts,b.deletes,v.calls),(0,0,0))
        self.assertTrue(host.has_pending)

    def test_other_window_candidate_test_cannot_be_approved_without_own_ticket(self):
        panel, host, b, v, *_ = self.build()
        self.assertTrue(host.request(Operation.TEST_CANDIDATE))
        panel._entry.value="fixture-good"
        panel.approve_from_button()
        self.assertEqual((v.calls,b.puts,b.deletes),(0,0,0))
        self.assertTrue(host.has_pending)
