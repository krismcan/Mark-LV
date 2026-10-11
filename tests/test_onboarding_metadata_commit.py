"""Phase 8.28 metadata-only persistence and trusted Tk fake acceptance."""
from pathlib import Path
from unittest.mock import Mock, patch
import inspect
import ast
import sys
import tempfile
import tkinter as tk
import unittest

from nayeon.brain.connection_document import (
    ProviderConnectionDocumentV1, parse_provider_connection_document,
)
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.brain.onboarding_metadata_commit import (
    MetadataCommitOutcome as Outcome, MetadataCommitReceipt,
    MetadataOperation, TrustedMetadataCommitHost,
)
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from nayeon.desktop_alpha import first_run_metadata_management_window as ui
from tests.test_onboarding_coordination import FakeMutex
from tests.test_first_run_credential_management_window import (
    Widget, FakeEntry, FakeBool,
)


def canonical(model="gpt-5.6"):
    return parse_provider_connection_document({
        "schema_version": 1,
        "connection": {"provider": "openai", "model": model, "credential": "openai.api_key"},
    })


class MetadataHarness:
    def __init__(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"settings.json"
        self.mutex=FakeMutex()
        self.now=100.0
        self.host=TrustedMetadataCommitHost(
            metadata_path=self.path,mutex=self.mutex,clock=lambda:self.now,
            timeout_seconds=10.0)
        self.store=ProviderConnectionFileStore(self.path)
        self.credential=None  # Sentinel: no credential store exists in this workflow

    def close(self):
        self.temp.cleanup()


class TrustedMetadataTests(unittest.TestCase):
    def setUp(self):
        self.h=MetadataHarness()
        self.addCleanup(self.h.close)

    def test_request_save_has_zero_side_effects_then_approve_writes(self):
        self.assertIs(self.h.host.request_save("gpt-5.6").outcome,Outcome.PENDING)
        self.assertFalse(self.h.path.exists())
        self.assertFalse(self.h.host.recovery_marker_path.exists())
        self.assertEqual(self.h.mutex.entered,0)
        result=self.h.host.approve(human_approved=True)
        self.assertIs(result.outcome,Outcome.VERIFIED)
        self.assertTrue(result.requires_reobservation)
        self.assertFalse(result.grants_credential_authority)
        self.assertFalse(result.confirms_cross_store_transaction)
        self.assertEqual(self.h.store.load(),canonical())
        self.assertEqual(self.h.mutex.entered,self.h.mutex.exited)
        self.assertFalse(self.h.host.recovery_marker_path.exists())

    def test_clear_writes_null_metadata_without_removing_credential(self):
        self.h.store.save(canonical())
        unrelated_key_sentinel=object()
        self.h.credential=unrelated_key_sentinel
        self.assertIs(self.h.host.request_clear().outcome,Outcome.PENDING)
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.VERIFIED)
        self.assertEqual(self.h.store.load(),ProviderConnectionDocumentV1(connection=None))
        self.assertIs(self.h.credential,unrelated_key_sentinel)

    def test_model_change_and_idempotent_noop(self):
        self.h.store.save(canonical())
        self.assertIs(self.h.host.request_save("gpt-5.6").outcome,Outcome.REFUSED)
        self.assertIs(self.h.host.request_save("gpt-6").outcome,Outcome.PENDING)
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.VERIFIED)
        self.assertEqual(self.h.store.load(),canonical("gpt-6"))

    def test_clear_absent_and_cleared_rejected(self):
        self.assertIs(self.h.host.request_clear().outcome,Outcome.REFUSED)
        self.h.store.save(ProviderConnectionDocumentV1(connection=None))
        self.assertIs(self.h.host.request_clear().outcome,Outcome.REFUSED)

    def test_reject_and_double_approval_never_write(self):
        self.h.host.request_save("gpt-6")
        self.assertIs(self.h.host.reject().outcome,Outcome.REFUSED)
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.REFUSED)
        self.assertFalse(self.h.path.exists())
        self.assertEqual(self.h.mutex.entered,0)

    def test_expiry_consumes_approval(self):
        self.h.host.request_save("gpt-6")
        self.h.now=111.0
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.EXPIRED)
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.REFUSED)
        self.assertFalse(self.h.path.exists())

    def test_no_coercion_of_boolean_approval_and_no_write(self):
        self.h.host.request_save("gpt-6")
        self.assertIs(self.h.host.approve(human_approved=1).outcome,Outcome.REFUSED)
        self.assertFalse(self.h.path.exists())

    def test_busy_mutex_refuses_without_creating_marker(self):
        self.h.mutex.state=MutexAdmission.BUSY
        self.h.host.request_save("gpt-6")
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.BUSY)
        self.assertFalse(self.h.path.exists())
        self.assertFalse(self.h.host.recovery_marker_path.exists())

    def test_abandoned_mutex_quarantines(self):
        self.h.mutex.state=MutexAdmission.ABANDONED
        self.h.host.request_save("gpt-6")
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.RECOVERY_REQUIRED)
        self.assertFalse(self.h.path.exists())
        self.assertTrue(self.h.host.recovery_marker_path.exists())
        self.h.mutex.state=MutexAdmission.HELD
        self.assertIs(self.h.host.request_save("gpt-6").outcome,Outcome.RECOVERY_REQUIRED)

    def test_prior_marker_refuses_mutation(self):
        self.h.host.recovery_marker_path.write_text("synthetic unfinished operation")
        self.assertIs(self.h.host.request_save("gpt-6").outcome,Outcome.RECOVERY_REQUIRED)
        self.assertFalse(self.h.path.exists())

    def test_metadata_conflict_before_approval(self):
        self.h.store.save(canonical("initial"))
        self.h.host.request_save("changed")
        self.h.store.save(canonical("external"))
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.CONFLICT)
        self.assertEqual(self.h.store.load(),canonical("external"))
        self.assertFalse(self.h.host.recovery_marker_path.exists())

    def test_model_aba_conflict(self):
        self.h.store.save(canonical("initial"))
        self.h.host.request_save("changed")
        self.h.store.save(canonical("external"))
        self.h.store.save(canonical("initial"))
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.CONFLICT)
        self.assertEqual(self.h.store.load(),canonical("initial"))

    def test_malformed_and_unsupported_metadata_fails_closed(self):
        self.h.path.write_text("{ malformed")
        self.assertIs(self.h.host.request_save("gpt-6").outcome,Outcome.UNAVAILABLE)
        self.h.store.save(parse_provider_connection_document({
            "schema_version":1,
            "connection":{"provider":"other","model":"other","credential":"other.key"},
        }))
        self.assertIs(self.h.host.request_save("gpt-6").outcome,Outcome.UNAVAILABLE)
        self.assertIs(self.h.host.request_clear().outcome,Outcome.UNAVAILABLE)

    def test_rejects_invalid_model_metadata_and_unknown_type(self):
        for model in ("", " gpt-6", "gpt-6\n", "a"*129, 4, None, True,
                      "sk-proj-synthetic-not-a-key", "Bearer fake-token",
                      "ghp_syntheticnotakey"):
            self.assertIs(self.h.host.request_save(model).outcome,Outcome.REFUSED)
        self.assertFalse(self.h.host.has_pending)
        self.assertFalse(self.h.path.exists())

    def test_clock_failure_and_nonfinite_time_refuses(self):
        for invalid in (float("nan"),float("inf")):
            h=TrustedMetadataCommitHost(metadata_path=self.h.path,
                                         mutex=self.h.mutex,clock=lambda:invalid)
            self.assertIs(h.request_save("gpt-6").outcome,Outcome.UNAVAILABLE)
        self.h.host.request_save("gpt-6")
        self.h.now=float("nan")
        self.assertIs(self.h.host.approve(human_approved=True).outcome,Outcome.UNAVAILABLE)
        self.assertFalse(self.h.path.exists())

    def test_interrupted_save_keeps_marker(self):
        self.h.host.request_save("gpt-6")
        with patch.object(ProviderConnectionFileStore,"save",side_effect=OSError("synthetic crash")):
            result=self.h.host.approve(human_approved=True)
        self.assertIs(result.outcome,Outcome.RECOVERY_REQUIRED)
        self.assertTrue(self.h.host.recovery_marker_path.exists())
        self.assertIs(self.h.host.request_save("gpt-6").outcome,Outcome.RECOVERY_REQUIRED)

    def test_write_succeeds_then_error_quarantined_no_rollback(self):
        self.h.host.request_save("gpt-6")
        original=ProviderConnectionFileStore.save
        def partial(store, record):
            original(store, record)
            raise OSError("synthetic after commit")
        with patch.object(ProviderConnectionFileStore,"save",partial):
            result=self.h.host.approve(human_approved=True)
        self.assertIs(result.outcome,Outcome.RECOVERY_REQUIRED)
        self.assertEqual(self.h.store.load(),canonical("gpt-6"))
        self.assertTrue(self.h.host.recovery_marker_path.exists())

    def test_failure_to_mark_blocks_write(self):
        self.h.host.request_save("gpt-6")
        with patch.object(TrustedMetadataCommitHost,"_mark_inflight",return_value=False):
            result=self.h.host.approve(human_approved=True)
        self.assertIs(result.outcome,Outcome.RECOVERY_REQUIRED)
        self.assertFalse(self.h.path.exists())

    def test_unexpected_post_save_document_stays_quarantined(self):
        self.h.host.request_save("gpt-6")
        original=ProviderConnectionFileStore.save
        def changed(store, record):
            original(store,canonical("different"))
        with patch.object(ProviderConnectionFileStore,"save",changed):
            result=self.h.host.approve(human_approved=True)
        self.assertIs(result.outcome,Outcome.RECOVERY_REQUIRED)
        self.assertTrue(self.h.host.recovery_marker_path.exists())
        self.assertEqual(self.h.store.load(),canonical("different"))

    def test_marker_cleanup_failure_stays_quarantined(self):
        self.h.host.request_save("gpt-6")
        with patch.object(TrustedMetadataCommitHost,"_clear_marker",return_value=False):
            result=self.h.host.approve(human_approved=True)
        self.assertIs(result.outcome,Outcome.RECOVERY_REQUIRED)
        self.assertTrue(self.h.host.recovery_marker_path.exists())

    def test_exact_contract_receipts_and_constructor_validation(self):
        with self.assertRaises(ValueError):
            MetadataCommitReceipt(Outcome.VERIFIED,grants_credential_authority=True)
        with self.assertRaises(ValueError):
            MetadataCommitReceipt(Outcome.VERIFIED,confirms_cross_store_transaction=True)
        with self.assertRaises(TypeError):
            TrustedMetadataCommitHost(metadata_path=str(self.h.path))
        with self.assertRaises(ValueError):
            TrustedMetadataCommitHost(metadata_path=self.h.path,timeout_seconds=0)
        with self.assertRaises(ValueError):
            TrustedMetadataCommitHost(metadata_path=self.h.path,timeout_seconds=301)
        self.assertFalse(hasattr(self.h.host,"__dict__"))

    def test_shared_credential_coordination_marker_blocks_metadata(self):
        # The same marker name is used by both independently trusted hosts.
        from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
        from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
        from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
        from nayeon.brain.connection_reconciliation import observe_connection
        from nayeon.secrets.contracts import SecretIdentifier
        from nayeon.secrets.lifecycle import BoundCredentialLifecycle
        from tests.test_credential_operation_host import FakeBackend, FakeValidator
        backend=FakeBackend()
        bound=BoundCredentialLifecycle(backend,SecretIdentifier("openai.api_key"),
                                       FakeValidator())
        credential=CooperativeOnboardingCoordinator(
            host=TrustedCredentialOperationHost(
                onboarding=OpenAICredentialOnboarding(bound),
                observe=lambda:observe_connection(self.h.path,backend)),
            metadata_path=self.h.path,availability=backend,
            mutex=self.h.mutex)
        self.assertEqual(credential.recovery_marker_path,
                         self.h.host.recovery_marker_path)
        self.assertTrue(credential._mark_inflight())
        self.assertIs(self.h.host.request_save("gpt-6").outcome,
                      Outcome.RECOVERY_REQUIRED)
        self.assertFalse(self.h.path.exists())

    def test_import_boundary_no_credential_methods_or_model_tool(self):
        from nayeon.brain import onboarding_metadata_commit as source
        tree=ast.parse(inspect.getsource(source))
        modules={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(modules,{
            "dataclasses","enum","pathlib","collections.abc",
            "nayeon.brain.connection_document",
            "nayeon.brain.connection_persistence",
            "nayeon.brain.windows_onboarding_mutex",
        })
        names={n.func.attr for n in ast.walk(tree)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        for forbidden in ("delete","get_stored","reveal","is_available","connect",
                          "replace","remove","validate","request"):
            self.assertNotIn(forbidden,names)


class MetadataUiTests(unittest.TestCase):
    def setUp(self):
        self.h=MetadataHarness()
        self.addCleanup(self.h.close)
        self.root=Mock()
        def make(cls):
            def init(*args,**kwargs):
                return cls(*args,**kwargs)
            return init
        with patch.object(ui.tk,"Label",side_effect=make(Widget)), \
             patch.object(ui.tk,"Button",side_effect=make(Widget)), \
             patch.object(ui.tk,"Entry",side_effect=make(FakeEntry)), \
             patch.object(ui.tk,"Checkbutton",side_effect=make(Widget)), \
             patch.object(ui.tk,"BooleanVar",side_effect=FakeBool):
            self.window=ui.FirstRunMetadataManagementWindow(self.root,host=self.h.host)

    def test_construct_has_no_side_effect(self):
        self.assertFalse(self.h.path.exists())
        self.assertEqual(self.h.mutex.entered,0)
        self.assertEqual(self.window._approve.props["state"],"disabled")

    def test_ui_save_two_distinct_button_events(self):
        self.window._model.value="gpt-6"
        self.window._save.props["command"]()
        self.assertFalse(self.h.path.exists())
        self.window._approve.props["command"]()
        self.assertEqual(self.h.store.load(),canonical("gpt-6"))
        self.assertIn("not",self.window._status.props["text"].lower())
        self.assertIsNone(self.window._operation)

    def test_ui_clear_requires_additional_ack_and_does_not_touch_key(self):
        self.h.store.save(canonical())
        self.h.credential=object()
        before=self.h.credential
        self.window._clear.props["command"]()
        self.window._approve.props["command"]()
        self.assertEqual(self.h.store.load(),canonical())
        self.window._clear_acknowledged.set(True)
        self.window._approve.props["command"]()
        self.assertIs(self.h.credential,before)
        self.assertEqual(self.h.store.load(),ProviderConnectionDocumentV1(connection=None))
        self.assertFalse(self.window._clear_acknowledged.get())

    def test_ui_reject_and_close_do_not_write(self):
        self.window._model.value="gpt-6"
        self.window._save.props["command"]()
        self.window._reject.props["command"]()
        self.assertFalse(self.h.path.exists())
        self.window._save.props["command"]()
        self.window.close_from_window()
        self.root.destroy.assert_called_once()
        self.assertFalse(self.h.path.exists())

    def test_ui_expired_result_and_replay(self):
        self.window._model.value="gpt-6"
        self.window._save.props["command"]()
        self.h.now=111
        self.window._approve.props["command"]()
        self.assertFalse(self.h.path.exists())
        self.assertIn("expired",self.window._status.props["text"].lower())
        self.window._approve.props["command"]()
        self.assertEqual(self.h.mutex.entered,0)

    def test_ui_host_type_and_direct_backend_isolation(self):
        with self.assertRaises(TypeError):
            ui.FirstRunMetadataManagementWindow(Mock(),host=Mock())
        tree=ast.parse(inspect.getsource(ui))
        calls={n.func.attr for n in ast.walk(tree)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        for forbidden in ("put","delete","save","load","reveal","remove",
                          "open","system","is_available","connect"):
            self.assertNotIn(forbidden,calls)


@unittest.skipUnless(sys.platform=="win32","Actual Windows Tk only")
class WindowsTkMetadataTests(unittest.TestCase):
    def setUp(self):
        self.h=MetadataHarness()
        self.addCleanup(self.h.close)
        self.root=tk.Tk()
        self.root.withdraw()
        self.addCleanup(self._cleanup)
        self.window=ui.FirstRunMetadataManagementWindow(self.root,host=self.h.host)

    def _cleanup(self):
        try: self.root.destroy()
        except tk.TclError: pass

    def test_save_real_widgets(self):
        self.window._model.insert(0,"gpt-6")
        self.window._save.invoke()
        self.assertFalse(self.h.path.exists())
        self.window._approve.invoke()
        self.assertEqual(self.h.store.load(),canonical("gpt-6"))
        self.assertEqual(self.window._approve.cget("state"),"disabled")

    def test_clear_real_widgets_requires_ack(self):
        self.h.store.save(canonical())
        self.window._clear.invoke()
        self.window._approve.invoke()
        self.assertEqual(self.h.store.load(),canonical())
        self.window._clear_ack.invoke()
        self.window._approve.invoke()
        self.assertIsNone(self.h.store.load().connection)

if __name__=="__main__":
    unittest.main()
