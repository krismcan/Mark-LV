"""Phase 8.23: synthetic Tk buttons; no credential mutation or acceptance."""
import ast
import inspect
import unittest
from unittest.mock import Mock, patch

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus as State,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Operation
from nayeon.desktop_alpha import first_run_review_window as m
from tests.test_credential_operation_host import factory


class Widget:
    def __init__(self, *args, **kwargs):
        self.props = dict(kwargs)
    def pack(self, *args, **kwargs):
        pass
    def configure(self, **kwargs):
        self.props.update(kwargs)


class ReviewPanelTests(unittest.TestCase):
    def build(self, status=State.SETUP_REQUIRED):
        host, backend, validator, state = factory(status)
        root = Mock()
        widgets = []
        def create(*args, **kwargs):
            widget = Widget(*args, **kwargs)
            widgets.append(widget)
            return widget
        with patch.object(m.tk, "Label", side_effect=create), patch.object(
                m.tk, "Button", side_effect=create):
            panel = m.FirstRunReviewWindow(root, host=host)
        return panel, host, backend, validator, widgets

    def test_construct_does_not_observe_or_validate(self):
        panel, host, backend, validator, widgets = self.build()
        self.assertFalse(host.has_pending)
        self.assertEqual((backend.puts, backend.gets, backend.deletes, validator.calls),(0,0,0,0))
        self.assertEqual(len([w for w in widgets if w.props.get("command")]), 6)
        self.assertFalse(hasattr(panel, "approve_from_button"))

    def test_only_button_request_and_cancel_do_not_mutate(self):
        panel, host, backend, validator, widgets = self.build()
        panel.propose_from_button(Operation.CONNECT)
        self.assertTrue(host.has_pending)
        self.assertTrue(all(w.props["state"]=="disabled" for w in panel._options))
        self.assertEqual(panel._reject.props["state"], "normal")
        self.assertIn("Execution is not available", panel._status.props["text"])
        panel.reject_from_button()
        self.assertFalse(host.has_pending)
        self.assertEqual((backend.puts,backend.gets,backend.deletes,validator.calls),(0,0,0,0))
        self.assertEqual(panel._reject.props["state"],"disabled")

    def test_unknown_and_unsupported_states_fail_closed(self):
        for state in (State.UNKNOWN,State.UNSUPPORTED_CONFIGURATION,State.CHANGED_DURING_OBSERVATION):
            with self.subTest(state=state):
                panel,host,backend,validator,_=self.build(state)
                panel.propose_from_button(Operation.CONNECT)
                self.assertFalse(host.has_pending)
                self.assertIn("unavailable",panel._status.props["text"])
                self.assertEqual(backend.puts,0)

    def test_rejected_review_does_not_have_action_receipt(self):
        panel,host,b,v,_=self.build()
        panel.propose_from_button(Operation.CONNECT)
        panel.propose_from_button(Operation.REPLACE)
        self.assertTrue(host.has_pending)
        self.assertIn("existing",panel._status.props["text"])
        panel.reject_from_button()
        self.assertIsNone(host.approve())
        self.assertEqual(b.puts,0)

    def test_reject_input_type_without_calling_host(self):
        panel,host,b,v,_=self.build()
        for invalid in ("connect",None,object(),Operation.REVIEW):
            panel.propose_from_button(invalid)
            self.assertFalse(host.has_pending)
        self.assertEqual(b.puts,0)

    def test_ui_has_no_credential_or_approve_import_or_calls(self):
        tree=ast.parse(inspect.getsource(m))
        imports={n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {
            "nayeon.brain.credential_operation_host",
            "nayeon.brain.onboarding_operation_advice",
        })
        called={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id
                for n in ast.walk(tree) if isinstance(n,ast.Call)
                and isinstance(n.func,(ast.Attribute,ast.Name))}
        for forbidden in ("approve","connect","replace","remove","test_stored",
                          "reveal","get","put","delete","SecretValue","Popen"):
            self.assertNotIn(forbidden, called)

if __name__=="__main__":
    unittest.main()
