"""Phase 8.27: real UI callback ownership, fake-only storage, no network."""
import ast
import inspect
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import observe_connection
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinatedOutcome,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.secrets.contracts import SecretIdentifier, SecretValue
from nayeon.secrets.lifecycle import BoundCredentialLifecycle
from nayeon.desktop_alpha import first_run_credential_management_window as m
from tests.test_credential_operation_host import FakeBackend, FakeValidator
from tests.test_onboarding_coordination import FakeMutex
from nayeon.brain.windows_onboarding_mutex import MutexAdmission


class Harness:
    def __init__(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"provider.json"
        self.backend=FakeBackend()
        self.validator=FakeValidator()
        self.mutex=FakeMutex()
        self.host=TrustedCredentialOperationHost(
            onboarding=OpenAICredentialOnboarding(BoundCredentialLifecycle(
                self.backend,SecretIdentifier("openai.api_key"),self.validator)),
            observe=lambda:observe_connection(self.path,self.backend))
        self.coordinator=CooperativeOnboardingCoordinator(
            host=self.host,metadata_path=self.path,availability=self.backend,
            mutex=self.mutex)
        self.controller=self.coordinator.recovery_controller
        self.reconcile()

    def reconcile(self):
        if self.controller._ctx is not None:
            self.controller.close()
        review=self.controller.request_reconciliation()
        assert self.controller.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint)

    def configure(self):
        ProviderConnectionFileStore(self.path).save(
            ProviderConnectionDocumentV1(connection=ProviderConnectionConfiguration(
                "openai","gpt-5.6",SecretIdentifier("openai.api_key"))))

    def close(self):
        if self.controller._ctx is not None:
            self.controller.close()
        self.temp.cleanup()


class Widget:
    def __init__(self,*a,**kw):
        self.props=dict(kw)
        self.bindings={}
    def pack(self,*a,**kw):
        pass
    def configure(self,**kw):
        self.props.update(kw)
    def bind(self,sequence,callback):
        self.bindings[sequence]=callback


class FakeEntry(Widget):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.value=""
        self.reads=0
    def delete(self,start,end):
        if self.props.get("state")!="disabled":
            self.value=""
    def get(self):
        self.reads+=1
        return self.value


class FakeBool:
    def __init__(self,*a,**kw):
        self.value=kw.get("value",False)
    def set(self,value):
        self.value=value
    def get(self):
        return self.value


class ManagementUITests(unittest.TestCase):
    def setUp(self):
        self.h=Harness()
        self.addCleanup(self.h.close)
        self.widgets=[]
        self.root=Mock()
        def make(cls):
            def constructor(*a,**kw):
                w=cls(*a,**kw)
                self.widgets.append(w)
                return w
            return constructor
        with patch.object(m.tk,"Label",side_effect=make(Widget)),\
             patch.object(m.tk,"Button",side_effect=make(Widget)),\
             patch.object(m.tk,"Entry",side_effect=make(FakeEntry)),\
             patch.object(m.tk,"Checkbutton",side_effect=make(Widget)),\
             patch.object(m.tk,"BooleanVar",side_effect=FakeBool):
            self.ui=m.FirstRunCredentialManagementWindow(
                self.root,coordinator=self.h.coordinator)

    def review(self,operation):
        self.ui.request_from_button(operation)
        self.assertIs(self.ui._operation,operation)
        self.assertTrue(self.h.coordinator.has_pending)

    def test_constructor_zero_io_and_masked_disabled(self):
        self.assertIsNone(self.ui._operation)
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual(self.ui._entry.props["show"],"*")
        self.assertIs(self.ui._entry.props["exportselection"],False)
        self.assertEqual(self.ui._entry.props["state"],"disabled")
        self.assertEqual(self.ui._approve.props["state"],"disabled")
        self.assertEqual((self.h.backend.puts,self.h.backend.deletes,
                          self.h.backend.gets,self.h.validator.calls),(0,0,0,0))
        self.assertEqual(self.h.mutex.entered,1)
        self.root.protocol.assert_called_once()

    def test_connect_requires_two_clicks_and_masks_key(self):
        self.review(Op.CONNECT)
        self.assertEqual(self.ui._entry.props["state"],"normal")
        self.assertFalse(self.h.coordinator.recovery_marker_path.exists())
        self.ui._entry.value="fixture-good"
        self.ui._approve.props["command"]()
        self.assertEqual(self.h.backend.puts,1)
        self.assertEqual(self.h.validator.calls,1)
        self.assertEqual(self.ui._entry.value,"")
        self.assertIn("recovery required",self.ui._status.props["text"].lower())
        self.assertEqual((self.h.mutex.entered,self.h.mutex.exited),(1,0))
        self.assertFalse(self.h.coordinator.has_pending)
        self.ui.approve_from_button()
        self.assertEqual(self.h.backend.puts,1)

    def test_replace_invalid_preserves_previous_key(self):
        self.h.configure()
        original=SecretValue("original-key")
        self.h.backend.value=original
        self.h.reconcile()
        self.review(Op.REPLACE)
        self.ui._entry.value="fixture-bad"
        self.ui.approve_from_button()
        self.assertIs(self.h.backend.value,original)
        self.assertEqual(self.h.backend.puts,0)
        self.assertEqual(self.h.validator.calls,1)
        self.assertIn("recovery required",self.ui._status.props["text"].lower())
        self.assertEqual(self.ui._entry.value,"")

    def test_replace_valid_does_not_claim_durability(self):
        self.h.configure()
        original=SecretValue("old")
        self.h.backend.value=original
        self.h.reconcile()
        self.review(Op.REPLACE)
        self.ui._entry.value="fixture-good"
        self.ui.approve_from_button()
        self.assertEqual(self.h.backend.puts,1)
        self.assertIsNot(self.h.backend.value,original)
        self.assertIn("recovery required",self.ui._status.props["text"].lower())
        self.assertFalse(self.h.coordinator.recovery_marker_path.exists())

    def test_remove_requires_explicit_acknowledgement(self):
        self.h.configure()
        self.h.backend.value=SecretValue("old")
        self.h.reconcile()
        self.review(Op.REMOVE)
        self.assertEqual(self.ui._entry.props["state"],"disabled")
        self.assertEqual(self.ui._delete_ack.props["state"],"normal")
        self.ui.approve_from_button()
        self.assertEqual(self.h.backend.deletes,0)
        self.assertTrue(self.h.coordinator.has_pending)
        self.assertIn("requires explicit acknowledgement",self.ui._status.props["text"])
        self.ui._acknowledged.set(True)
        self.ui._approve.props["command"]()
        self.assertEqual(self.h.backend.deletes,1)
        self.assertIsNone(self.h.backend.value)
        self.assertFalse(self.ui._acknowledged.get())
        self.assertIn("not confirmed",self.ui._status.props["text"].lower())
        self.ui.approve_from_button()
        self.assertEqual(self.h.backend.deletes,1)

    def test_candidate_never_read_during_delete(self):
        self.h.configure()
        self.h.backend.value=SecretValue("old")
        self.h.reconcile()
        self.review(Op.REMOVE)
        self.ui._entry.value="would-be-sensitive"
        self.ui._acknowledged.set(True)
        before=self.ui._entry.reads
        self.ui.approve_from_button()
        self.assertEqual(self.ui._entry.reads,before)
        self.assertEqual(self.ui._entry.value,"")
        self.assertEqual(self.h.backend.deletes,1)

    def test_reject_clears_and_does_not_run_backend(self):
        self.review(Op.CONNECT)
        self.ui._entry.value="fixture-good"
        self.ui._reject.props["command"]()
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual(self.ui._entry.value,"")
        self.assertEqual((self.h.backend.puts,self.h.validator.calls),(0,0))
        self.assertEqual(self.h.mutex.entered,1)

    def test_close_consumes_review_and_clears(self):
        self.review(Op.CONNECT)
        self.ui._entry.value="fixture-good"
        self.ui.close_from_window()
        self.root.destroy.assert_called_once()
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual(self.ui._entry.value,"")
        self.assertEqual(self.h.validator.calls,0)

    def test_blank_credential_consumes_review_without_effect(self):
        self.review(Op.CONNECT)
        self.ui.approve_from_button()
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual((self.h.backend.puts,self.h.validator.calls),(0,0))
        self.assertIn("unavailable",self.ui._status.props["text"].lower())

    def test_concurrent_busy_consumes_review_no_write(self):
        # BUSY is detected when beginning a new trusted tenure, not at approve.
        self.h.controller.close()
        self.h.mutex.state=MutexAdmission.BUSY
        self.ui.request_from_button(Op.CONNECT)
        self.ui._entry.value="fixture-good"
        self.ui.approve_from_button()
        self.assertEqual(self.h.backend.puts,0)
        self.assertEqual(self.h.validator.calls,0)
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertIn("recovery required",self.ui._status.props["text"].lower())

    def test_recovery_marker_blocks_review(self):
        self.h.coordinator.recovery_marker_path.write_text("synthetic-marker")
        self.ui.request_from_button(Op.CONNECT)
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertIn("recovery required",self.ui._status.props["text"].lower())
        self.assertEqual((self.h.backend.puts,self.h.validator.calls),(0,0))

    def test_state_conflict_never_runs_validator(self):
        self.review(Op.CONNECT)
        self.h.backend.value=SecretValue("other")
        self.ui._entry.value="fixture-good"
        self.ui.approve_from_button()
        self.assertEqual((self.h.backend.puts,self.h.validator.calls),(0,0))
        self.assertIn("state changed",self.ui._status.props["text"].lower())

    def test_remove_without_stored_key_cannot_be_reviewed(self):
        self.ui.request_from_button(Op.REMOVE)
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual(self.h.backend.deletes,0)
        self.assertIsNone(self.ui._operation)

    def test_delete_acknowledgement_cannot_carry_into_another_review(self):
        self.h.configure()
        self.h.backend.value=SecretValue("old")
        self.h.reconcile()
        self.review(Op.REMOVE)
        self.ui._acknowledged.set(True)
        self.ui.reject_from_button()
        self.assertFalse(self.ui._acknowledged.get())
        self.review(Op.REPLACE)
        self.assertFalse(self.ui._acknowledged.get())
        self.ui.reject_from_button()

    def test_duplicate_review_attempt_refused_without_replacing(self):
        self.review(Op.CONNECT)
        self.ui.request_from_button(Op.REMOVE)
        self.assertIs(self.ui._operation,Op.CONNECT)
        self.assertTrue(self.h.coordinator.has_pending)

    def test_candidate_copy_cut_cancelled(self):
        for sequence in ("<<Copy>>","<<Cut>>","<Control-c>","<Control-x>"):
            self.assertEqual(self.ui._entry.bindings[sequence](None),"break")

    def test_bound_type_and_restricted_imports(self):
        with self.assertRaises(TypeError):
            m.FirstRunCredentialManagementWindow(Mock(),coordinator=Mock())
        tree=ast.parse(inspect.getsource(m))
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(imports,{
            "nayeon.brain.onboarding_coordination",
            "nayeon.brain.onboarding_operation_advice",
            "nayeon.brain.credential_operation_host",
            "nayeon.secrets.contracts",
            "nayeon.desktop_alpha.first_run_onboarding_recovery_window",
        })
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        attrs={n.func.attr for n in calls if isinstance(n.func,ast.Attribute)}
        for forbidden in ("reveal","put","is_available","connect","replace","remove",
                          "Popen","system","get_stored","load","save"):
            self.assertNotIn(forbidden,attrs)
        deletion=[n for n in calls if isinstance(n.func,ast.Attribute)
                  and n.func.attr=="delete"]
        self.assertEqual(len(deletion),1)
        self.assertEqual(ast.unparse(deletion[0].func.value),"self._entry")
        self.assertNotIn("WindowsCredentialBackend",inspect.getsource(m))


@unittest.skipUnless(sys.platform=="win32","Actual Windows Tk only")
class WindowsRealTkManagementTests(unittest.TestCase):
    def setUp(self):
        self.h=Harness()
        self.addCleanup(self.h.close)
        self.root=tk.Tk()
        self.root.withdraw()
        self.addCleanup(self._cleanup_root)
        self.ui=m.FirstRunCredentialManagementWindow(
            self.root,coordinator=self.h.coordinator)

    def _cleanup_root(self):
        try:
            self.root.destroy()
        except tk.TclError:
            # Close-window test already destroyed the Tk interpreter.
            pass

    def test_real_tk_connect_approve_and_clear(self):
        self.assertEqual(self.ui._entry.cget("show"),"*")
        self.ui._choices[0].invoke()
        self.assertTrue(self.h.coordinator.has_pending)
        self.ui._entry.insert(0,"fixture-good")
        self.ui._approve.invoke()
        self.assertEqual(self.h.backend.puts,1)
        self.assertEqual(self.ui._entry.get(),"")
        self.assertEqual(self.ui._entry.cget("state"),"disabled")
        self.assertEqual(self.h.backend.deletes,0)

    def test_real_tk_delete_requires_own_acknowledgement(self):
        self.h.configure()
        self.h.backend.value=SecretValue("old")
        self.h.reconcile()
        self.ui._choices[2].invoke()
        self.ui._approve.invoke()
        self.assertEqual(self.h.backend.deletes,0)
        self.ui._delete_ack.invoke()
        self.ui._approve.invoke()
        self.assertEqual(self.h.backend.deletes,1)
        self.assertEqual(self.h.backend.puts,0)

    def test_real_tk_close_rejects_without_any_operation(self):
        self.ui._choices[0].invoke()
        self.ui.close_from_window()
        self.assertFalse(self.h.coordinator.has_pending)
        self.assertEqual(self.h.validator.calls,0)


if __name__=="__main__":
    unittest.main()
