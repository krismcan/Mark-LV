"""P87 adversarial Windows/Tk tests: synthetic presentation, no custody I/O."""
import ast
import inspect
import threading
import tkinter as tk
import unittest
from unittest import mock

from nayeon.brain.pending_custody_observation_boundary import (
    CustodyObservationKind, CustodyObservationOrigin, SyntheticCustodyObservation,
    SyntheticObservationLease, synthetic_observation_message,
)
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from nayeon.desktop_alpha import workspace_window


class P87PureBoundaryTests(unittest.TestCase):
    def test_all_five_states_are_bounded_and_explicitly_synthetic(self):
        for kind in CustodyObservationKind:
            with self.subTest(kind=kind):
                obs = SyntheticCustodyObservation(kind)
                message = synthetic_observation_message(obs)
                self.assertIn("SYNTHETIC TEST ONLY", message)
                self.assertIn("BYOK C1", message)
                self.assertLess(len(message), 260)
                self.assertNotIn("fixture-secret", message)
                self.assertFalse(obs.authorizes_effect)
                self.assertFalse(obs.confirms_persistence)
                self.assertFalse(obs.confirms_validation)
                self.assertFalse(obs.confirms_connection)
                self.assertFalse(obs.clears_recovery)

    def test_unavailable_and_absence_are_not_assumed_equivalent(self):
        a = synthetic_observation_message(SyntheticCustodyObservation(
            CustodyObservationKind.NOT_OBSERVED))
        b = synthetic_observation_message(SyntheticCustodyObservation(
            CustodyObservationKind.UNAVAILABLE))
        c = synthetic_observation_message(SyntheticCustodyObservation(
            CustodyObservationKind.NO_PENDING_EVIDENCE_ASSERTED))
        self.assertIn("NOT OBSERVED", a)
        self.assertIn("STATUS UNAVAILABLE", b)
        self.assertIn("NOT proof of absence", c)
        self.assertNotEqual(a, b)

    def test_no_arbitrary_text_field_or_authority_grant(self):
        with self.assertRaises(TypeError):
            SyntheticCustodyObservation("fixture-secret")
        with self.assertRaises(TypeError):
            SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD,
                                        secret="fixture-secret")
        with self.assertRaises(ValueError):
            SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD,
                                        authorizes_effect=True)
        with self.assertRaises(ValueError):
            SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD,
                                        clears_recovery=True)
        with self.assertRaises(ValueError):
            SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD,
                                        origin="trusted-native")
        with self.assertRaises(TypeError):
            synthetic_observation_message(object())
        with self.assertRaises(TypeError):
            SyntheticObservationLease("forged-owner", 1)
        self.assertNotIn("RECOVERY_HOLD", repr(SyntheticCustodyObservation(
            CustodyObservationKind.RECOVERY_HOLD)))

    def test_mutated_frozen_instance_is_revalidated(self):
        obs = SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD)
        object.__setattr__(obs, "kind", "fixture-secret")
        with self.assertRaises(TypeError):
            synthetic_observation_message(obs)

    def test_source_imports_no_effectful_backend(self):
        import nayeon.brain.pending_custody_observation_boundary as module
        imports = {n.module for n in ast.walk(ast.parse(inspect.getsource(module)))
                   if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "enum"})
        for banned in ("winreg", "ctypes", "socket", "requests", "subprocess",
                       "tkinter", "pending_credential_mutation"):
            self.assertNotIn(banned, inspect.getsource(module))


class P87ActualConnectionTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.cleanup)
        with mock.patch.object(OfflineWorkspaceApplication,
                               "_bootstrap_readonly_presentation"):
            self.app = OfflineWorkspaceApplication(self.root)
        self.app.show_connection()
        self.view = self.app._active_view

    def cleanup(self):
        try:
            self.app.close()
        except tk.TclError:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _observation(self, kind=CustodyObservationKind.RECOVERY_HOLD):
        return SyntheticCustodyObservation(kind)

    def test_production_default_remains_not_observed_without_any_session(self):
        self.assertIn("NOT OBSERVED", self.view.pending_custody_label.cget("text"))
        self.assertIsNone(self.view._synthetic_pending_owner)
        self.assertIsNone(self.app._connection)
        self.assertEqual(len([w for w in self.view.winfo_children()
                              if isinstance(w, workspace_window.ttk.Button)]), 2)

    def test_explicit_lease_renders_only_fixed_synthetic_messages(self):
        for kind in CustodyObservationKind:
            with self.subTest(kind=kind):
                lease = self.view.begin_synthetic_pending_observation()
                self.assertTrue(self.view.publish_synthetic_pending_observation(
                    lease, self._observation(kind)))
                label = self.view.pending_custody_label.cget("text")
                self.assertEqual(label, synthetic_observation_message(
                    self._observation(kind)))
                self.assertIn("SYNTHETIC TEST ONLY", label)
                self.assertIsNone(self.view._synthetic_pending_owner)

    def test_replay_is_refused_with_no_second_tk_update(self):
        lease = self.view.begin_synthetic_pending_observation()
        self.assertTrue(self.view.publish_synthetic_pending_observation(
            lease, self._observation()))
        with mock.patch.object(self.view.pending_custody_label, "configure",
                               side_effect=AssertionError("REPLAY_TK_ACCESS")):
            self.assertFalse(self.view.publish_synthetic_pending_observation(
                lease, self._observation()))

    def test_wrong_owner_generation_and_lease_type_refused(self):
        lease = self.view.begin_synthetic_pending_observation()
        wrong_owner = SyntheticObservationLease(object(), lease.generation)
        wrong_generation = SyntheticObservationLease(lease.owner, lease.generation + 1)
        for forged in (wrong_owner, wrong_generation, None, (lease.owner, lease.generation)):
            with self.subTest(forged=type(forged)):
                self.assertFalse(self.view.publish_synthetic_pending_observation(
                    forged, self._observation()))
        self.assertTrue(self.view.publish_synthetic_pending_observation(
            lease, self._observation()))

    def test_new_generation_blocks_stale_response_and_stale_cancel(self):
        old = self.view.begin_synthetic_pending_observation()
        newer = self.view.begin_synthetic_pending_observation()
        self.assertFalse(self.view.cancel_synthetic_pending_observation(old))
        self.assertFalse(self.view.publish_synthetic_pending_observation(
            old, self._observation()))
        self.assertTrue(self.view.publish_synthetic_pending_observation(
            newer, self._observation()))

    def test_forged_observation_fail_closed_without_secret_reflection(self):
        for bad in (None, "fixture-secret", object()):
            lease = self.view.begin_synthetic_pending_observation()
            self.assertFalse(self.view.publish_synthetic_pending_observation(
                lease, bad))
            message = self.view.pending_custody_label.cget("text")
            self.assertIn("STATUS UNAVAILABLE", message)
            self.assertNotIn("fixture-secret", message)

    def test_cancel_restores_unknown_and_refuses_late_response(self):
        lease = self.view.begin_synthetic_pending_observation()
        self.assertTrue(self.view.cancel_synthetic_pending_observation(lease))
        self.assertIn("NOT OBSERVED", self.view.pending_custody_label.cget("text"))
        self.assertFalse(self.view.publish_synthetic_pending_observation(
            lease, self._observation()))
        self.assertFalse(self.view.cancel_synthetic_pending_observation(lease))

    def test_cross_view_owner_refused(self):
        old = self.view
        old_lease = old.begin_synthetic_pending_observation()
        self.app.show_conversation()
        self.app.show_connection()
        newer = self.app._active_view
        newer_lease = newer.begin_synthetic_pending_observation()
        self.assertFalse(newer.publish_synthetic_pending_observation(
            old_lease, self._observation()))
        self.assertFalse(old.publish_synthetic_pending_observation(
            old_lease, self._observation()))
        self.assertTrue(newer.publish_synthetic_pending_observation(
            newer_lease, self._observation()))

    def test_wrong_thread_refused_before_tk_for_all_entrypoints(self):
        lease = self.view.begin_synthetic_pending_observation()
        errors = []
        def worker():
            for call in (
                lambda: self.view.begin_synthetic_pending_observation(),
                lambda: self.view.cancel_synthetic_pending_observation(lease),
                lambda: self.view.publish_synthetic_pending_observation(
                    lease, self._observation()),
            ):
                try:
                    call()
                except RuntimeError as error:
                    errors.append(str(error))
        t = threading.Thread(target=worker)
        t.start()
        t.join(5)
        self.assertFalse(t.is_alive())
        self.assertEqual(errors, ["WRONG_THREAD"] * 3)

    def test_reentrant_publication_is_refused_and_lease_consumed(self):
        lease = self.view.begin_synthetic_pending_observation()
        real_configure = self.view.pending_custody_label.configure
        nested = []
        def reentrant(*args, **kwargs):
            nested.append(self.view.publish_synthetic_pending_observation(
                lease, self._observation()))
            return real_configure(*args, **kwargs)
        with mock.patch.object(self.view.pending_custody_label,
                               "configure", side_effect=reentrant):
            self.assertTrue(self.view.publish_synthetic_pending_observation(
                lease, self._observation()))
        self.assertEqual(nested, [False])
        self.assertFalse(self.view.publish_synthetic_pending_observation(
            lease, self._observation()))

    def test_cancel_during_configure_revokes_and_restores_unknown(self):
        lease = self.view.begin_synthetic_pending_observation()
        real_configure = self.view.pending_custody_label.configure
        cancelled = []
        def cancel_during(*args, **kwargs):
            if not cancelled:
                cancelled.append(self.view.cancel_synthetic_pending_observation(
                    lease))
            return real_configure(*args, **kwargs)
        with mock.patch.object(self.view.pending_custody_label,
                               "configure", side_effect=cancel_during):
            self.assertFalse(self.view.publish_synthetic_pending_observation(
                lease, self._observation()))
        self.assertEqual(cancelled, [True])
        self.assertIn("NOT OBSERVED", self.view.pending_custody_label.cget("text"))

    def test_destroy_during_configure_does_not_publish_success(self):
        lease = self.view.begin_synthetic_pending_observation()
        real_configure = self.view.pending_custody_label.configure
        def destroy_during(*args, **kwargs):
            result = real_configure(*args, **kwargs)
            self.app.show_conversation()
            return result
        with mock.patch.object(self.view.pending_custody_label,
                               "configure", side_effect=destroy_during):
            self.assertFalse(self.view.publish_synthetic_pending_observation(
                lease, self._observation()))
        self.assertFalse(self.view._alive)

    def test_no_credential_or_provider_effects(self):
        lease = self.view.begin_synthetic_pending_observation()
        with mock.patch.object(self.app, "_open_connection",
                               side_effect=AssertionError("CREDENTIAL_EFFECT")), \
             mock.patch("subprocess.Popen",
                        side_effect=AssertionError("PROCESS_EFFECT")), \
             mock.patch("os.system", side_effect=AssertionError("OS_EFFECT")):
            self.assertTrue(self.view.publish_synthetic_pending_observation(
                lease, self._observation()))
        self.assertIsNone(self.app._connection)
        self.assertIsNone(self.app._connection_coordinator)
        self.assertIsNone(self.app._connection_test_harness)


if __name__ == "__main__":
    unittest.main()
