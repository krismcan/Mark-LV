"""Phase 8.24: synthetic, full-stack GUI review acceptance and exit audit.

Uses actual sealed Tk window callbacks, refresh/reconciliation, host, review,
lifecycle and temp metadata. Only fake backend/validator; no real secrets.
"""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.connection_reconciliation import observe_connection
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
from nayeon.brain.first_run_refresh import FirstRunReadOnlyController
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Operation
from nayeon.brain.onboarding_review_session import OnboardingReviewSession
from nayeon.secrets.contracts import SecretValue
from nayeon.secrets.lifecycle import BoundCredentialLifecycle
from nayeon.desktop_alpha import first_run_review_window, first_run_status_window
from tests.test_phase_8_19_integrated_onboarding import (
    FakeBackend, FakeValidator, KEY,
)


class FakeWidget:
    def __init__(self, *args, **kw):
        self.props=dict(kw)
    def pack(self,*args,**kw):
        pass
    def configure(self,**kw):
        self.props.update(kw)


class VisualReviewAcceptanceTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"provider.json"
        self.store=ProviderConnectionFileStore(self.path)
        self.backend=FakeBackend()
        self.validator=FakeValidator()
        self.clock=[10.0]
        self.observer=lambda:observe_connection(self.path,self.backend)
        self.host=TrustedCredentialOperationHost(
            onboarding=OpenAICredentialOnboarding(BoundCredentialLifecycle(
                self.backend,KEY,self.validator)),
            observe=self.observer,
            review=OnboardingReviewSession(clock=lambda:self.clock[0],timeout_seconds=3.0),
        )
        self.readonly=FirstRunReadOnlyController(observe=self.observer)

    def widget_window(self, window_cls, **kwargs):
        root=Mock()
        buttons=[]
        def widget(*args,**kw):
            w=FakeWidget(*args,**kw)
            if "command" in kw:buttons.append(w)
            return w
        with patch.object(window_cls.__module__ == first_run_review_window.__name__
                          and first_run_review_window.tk or first_run_status_window.tk,
                          "Label", side_effect=widget), patch.object(
                          first_run_review_window.tk,"Button",side_effect=widget):
            screen=window_cls(root,**kwargs)
        return screen,buttons

    def review_panel(self):
        return self.widget_window(first_run_review_window.FirstRunReviewWindow,
                                  host=self.host)

    def status_panel(self):
        return self.widget_window(first_run_status_window.FirstRunStatusWindow,
                                  controller=self.readonly)

    def configure(self, provider="openai", model="gpt-5.6"):
        self.store.save(ProviderConnectionDocumentV1(connection=
            ProviderConnectionConfiguration(provider,model,KEY)))

    def assert_no_operations(self):
        self.assertEqual((self.backend.gets,self.backend.puts,self.backend.deletes,
                          self.validator.calls),(0,0,0,0))

    def test_two_windows_do_not_observe_on_creation(self):
        self.status_panel()
        self.review_panel()
        self.assertEqual(self.backend.probes,0)
        self.assert_no_operations()

    def test_status_requires_explicit_click_and_shows_no_secret(self):
        status,buttons=self.status_panel()
        self.assertEqual(self.backend.probes,0)
        buttons[0].props["command"]()
        self.assertEqual(self.backend.probes,1)
        self.assertIn("needs setup",status._status.props["text"])
        self.assertNotIn("api_key",str(status._details.props))
        self.assert_no_operations()

    def test_review_button_routes_only_to_pending_host(self):
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        self.assertTrue(self.host.has_pending)
        self.assertTrue(all(w.props["state"]=="disabled" for w in screen._options))
        self.assertEqual(self.backend.probes,1)
        self.assert_no_operations()

    def test_cancel_from_real_widget_callback(self):
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        screen._reject.props["command"]()
        self.assertFalse(self.host.has_pending)
        self.assertIn("rejected",screen._status.props["text"])
        self.assert_no_operations()

    def test_invalid_state_blocks_review_without_key_probe(self):
        self.configure(provider="unsupported")
        screen,buttons=self.review_panel()
        buttons[4].props["command"]()
        self.assertFalse(self.host.has_pending)
        self.assertEqual(self.backend.probes,0)
        self.assert_no_operations()

    def test_changed_during_refresh_fails_closed(self):
        self.configure(model="first")
        self.backend.on_probe=lambda:self.configure(model="second")
        status,buttons=self.status_panel()
        buttons[0].props["command"]()
        self.assertIn("observation changed",status._status.props["text"])
        self.assert_no_operations()

    def test_unknown_backend_failure_blocks_review_without_echo(self):
        self.backend.fail_probe=True
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        self.assertFalse(self.host.has_pending)
        self.assertNotIn("synthetic-sensitive",str(screen._status.props))
        self.assert_no_operations()

    def test_stale_credential_does_not_trigger_operation(self):
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        self.backend.value=SecretValue("synthetic-not-live-key")
        screen._reject.props["command"]()
        self.assert_no_operations()
        self.assertIsNotNone(self.backend.value)

    def test_expired_review_cancel_never_executes(self):
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        self.clock[0]=15.0
        screen._reject.props["command"]()
        self.assertFalse(self.host.has_pending)
        self.assert_no_operations()

    def test_repeated_rejection_cannot_invoke_backend(self):
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        screen._reject.props["command"]()
        screen.reject_from_button()
        self.assertFalse(self.host.has_pending)
        self.assert_no_operations()

    def test_metadata_not_mutated_by_review_only(self):
        self.configure()
        old=self.path.read_bytes()
        screen,buttons=self.review_panel()
        buttons[2].props["command"]()
        screen._reject.props["command"]()
        self.assertEqual(self.path.read_bytes(),old)
        self.assert_no_operations()

    def test_live_consent_remains_unimplemented_and_no_gui_approve(self):
        screen,_=self.review_panel()
        self.assertFalse(hasattr(screen,"approve_from_button"))
        self.assertFalse(any("approve" in str(w.props.get("text","")).lower()
                             for w in screen._options))
        self.assert_no_operations()
