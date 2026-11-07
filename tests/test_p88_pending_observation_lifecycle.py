"""P88 genuine Tk adversarial evidence; no real observer or credential effects.

P87 was an author-written safe synthetic boundary. This increment hardens
display lease object identity and P84/P87 publication sequencing. These are
application lifecycle rules, not native custody authentication.
"""
import tkinter as tk
import unittest
from unittest import mock

from nayeon.brain.pending_custody_observation_boundary import (
    CustodyObservationKind, SyntheticCustodyObservation, SyntheticObservationLease,
)
from nayeon.brain.pending_credential_policy import PendingCredentialState
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication
from tests.test_p86_live_pending_status_integration import trusted_synthetic_views


class P88SyntheticPublicationHardeningTests(unittest.TestCase):
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
        if getattr(self, "app", None) is not None:
            try:
                self.app.close()
            except tk.TclError:
                pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def obs(self):
        return SyntheticCustodyObservation(CustodyObservationKind.RECOVERY_HOLD)

    def p84(self):
        return trusted_synthetic_views(PendingCredentialState.ABSENT)

    def test_copied_lease_with_identical_fields_refused_before_tk(self):
        lease = self.view.begin_synthetic_pending_observation()
        replica = SyntheticObservationLease(lease.owner, lease.generation)
        self.assertEqual(replica, lease)
        self.assertIsNot(replica, lease)
        with mock.patch.object(self.view.pending_custody_label, "configure",
                               side_effect=AssertionError("FORGED_TK_ACCESS")):
            self.assertFalse(self.view.publish_synthetic_pending_observation(replica, self.obs()))
            self.assertFalse(self.view.cancel_synthetic_pending_observation(replica))
        self.assertTrue(self.view.publish_synthetic_pending_observation(lease, self.obs()))

    def test_corrupted_original_lease_fields_refuse_publish_then_can_replace(self):
        lease = self.view.begin_synthetic_pending_observation()
        object.__setattr__(lease, "generation", lease.generation + 100)
        self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        new = self.view.begin_synthetic_pending_observation()
        self.assertIsNot(new, lease)
        self.assertTrue(self.view.publish_synthetic_pending_observation(new, self.obs()))

    def test_explicit_p84_advisory_supersedes_pending_synthetic(self):
        lease = self.view.begin_synthetic_pending_observation()
        legacy, assessment = self.p84()
        self.assertTrue(self.view.show_pending_custody_advisory(legacy, assessment))
        self.assertIn("NO PENDING EVIDENCE ASSERTED", self.view.pending_custody_label.cget("text"))
        self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        self.assertIsNone(self.view._synthetic_pending_lease)

    def test_bad_p84_advisory_supersedes_with_unavailable_not_prior_pending(self):
        lease = self.view.begin_synthetic_pending_observation()
        legacy, _ = self.p84()
        self.assertFalse(self.view.show_pending_custody_advisory(legacy, "fixture-secret"))
        message = self.view.pending_custody_label.cget("text")
        self.assertIn("STATUS UNAVAILABLE", message)
        self.assertNotIn("fixture-secret", message)
        self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))

    def test_p84_advisory_cannot_reenter_during_synthetic_tk_write(self):
        lease = self.view.begin_synthetic_pending_observation()
        legacy, advice = self.p84()
        real = self.view.pending_custody_label.configure
        reentered = []
        def configure(*args, **kwargs):
            reentered.append(self.view.show_pending_custody_advisory(legacy, advice))
            return real(*args, **kwargs)
        with mock.patch.object(self.view.pending_custody_label, "configure",
                               side_effect=configure):
            self.assertTrue(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        self.assertEqual(reentered, [False])
        self.assertIn("SYNTHETIC TEST ONLY", self.view.pending_custody_label.cget("text"))

    def test_cancel_unexpected_tk_exception_revokes_owner(self):
        lease = self.view.begin_synthetic_pending_observation()
        with mock.patch.object(self.view.pending_custody_label, "configure",
                               side_effect=RuntimeError("fixture-secret")):
            self.assertFalse(self.view.cancel_synthetic_pending_observation(lease))
        self.assertIsNone(self.view._synthetic_pending_lease)
        self.assertIsNone(self.view._synthetic_pending_owner)
        self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))

    def test_publish_unexpected_tk_exception_restores_default_fail_closed(self):
        lease = self.view.begin_synthetic_pending_observation()
        with mock.patch.object(self.view.pending_custody_label, "configure",
                               side_effect=[RuntimeError("fixture-secret"), None]):
            self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        self.assertIsNone(self.view._synthetic_pending_lease)
        self.assertIn("NOT OBSERVED", self.view.pending_custody_label.cget("text"))
        self.assertNotIn("fixture-secret", self.view.pending_custody_label.cget("text"))
        self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))

    def test_repeated_tk_failures_dont_authorize_replay(self):
        lease = self.view.begin_synthetic_pending_observation()
        with mock.patch.object(self.view.pending_custody_label, "configure",
                               side_effect=RuntimeError("fixture-secret")):
            self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        self.assertIsNone(self.view._synthetic_pending_lease)
        self.assertFalse(self.view.cancel_synthetic_pending_observation(lease))
        self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        new = self.view.begin_synthetic_pending_observation()
        self.assertTrue(self.view.publish_synthetic_pending_observation(new, self.obs()))

    def test_navigation_refuses_copied_or_original_lease(self):
        lease = self.view.begin_synthetic_pending_observation()
        copy = SyntheticObservationLease(lease.owner, lease.generation)
        old = self.view
        self.app.show_conversation()
        self.app.show_connection()
        target = self.app._active_view
        fresh = target.begin_synthetic_pending_observation()
        for candidate in (lease, copy):
            self.assertFalse(old.publish_synthetic_pending_observation(candidate, self.obs()))
            self.assertFalse(target.publish_synthetic_pending_observation(candidate, self.obs()))
        self.assertTrue(target.publish_synthetic_pending_observation(fresh, self.obs()))

    def test_no_implicit_native_backend_or_credentials(self):
        lease = self.view.begin_synthetic_pending_observation()
        legacy, advice = self.p84()
        with mock.patch.object(self.app, "_open_connection",
                               side_effect=AssertionError("CREDENTIAL_OPERATION")):
            self.assertTrue(self.view.show_pending_custody_advisory(legacy, advice))
            self.assertFalse(self.view.publish_synthetic_pending_observation(lease, self.obs()))
        self.assertIsNone(self.app._connection)
        self.assertIsNone(self.app._connection_coordinator)


if __name__ == "__main__":
    unittest.main()
