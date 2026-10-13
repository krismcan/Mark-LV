"""A-01: adversarial fake-only Windows Tk credential consent origin tests.

Only the approved A-02 fake-composition fixture; never real providers or WinCred.
"""
import tkinter as tk
import unittest
from unittest import mock

from nayeon.brain.onboarding_coordination import CoordinatedOutcome
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.secrets.contracts import SecretValue, SecretIdentifier
from nayeon.brain.connection import ProviderConnectionConfiguration
from nayeon.brain.connection_document import ProviderConnectionDocumentV1
from nayeon.brain.connection_persistence import ProviderConnectionFileStore
from nayeon.desktop_alpha.first_run_credential_management_window import (
    FirstRunCredentialManagementWindow,
)
from tests.a02_fake_isolation_support import (
    FakeBackend, FakeValidator, FakeObserver, FakeMutex, FakeTempRoot,
    compose_fake_only_onboarding,
)


@unittest.skipUnless(__import__("sys").platform == "win32",
                     "Real Windows Tk required")
class A01ExactReviewTicketTests(unittest.TestCase):
    def setUp(self):
        self.temp = FakeTempRoot()
        self.addCleanup(self.temp.cleanup)
        self.backend = FakeBackend()
        self.validator = FakeValidator()
        self.observer = FakeObserver(self.backend)
        self.mutex = FakeMutex()
        self.composed = compose_fake_only_onboarding(
            backend=self.backend, validator=self.validator,
            observer=self.observer, mutex=self.mutex,
            temp_root=self.temp, metadata_path=self.temp.path / "provider.json",
        )
        self.coord = self.composed.coordinator
        self.ctrl = self.composed.controller
        self.addCleanup(lambda: self.ctrl.close() if self.ctrl._ctx is not None else None)
        review = self.ctrl.request_reconciliation()
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=review.fingerprint,
            expected_review=review))
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self._destroy_root)
        self.ui = FirstRunCredentialManagementWindow(
            self.root, coordinator=self.coord)

    def _destroy_root(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _begin(self, operation=Op.CONNECT):
        self.ui.request_from_button(operation)
        self.assertIs(self.ui._operation, operation)
        self.assertTrue(self.coord.has_pending)
        ticket = self.ui._ticket
        self.assertIsNotNone(ticket)
        return ticket

    def _no_effect(self):
        self.assertIsNone(self.backend.value)
        self.assertEqual(self.validator.calls, 0)
        self.assertNotIn("put", self.backend.calls)
        self.assertNotIn("delete", self.backend.calls)

    def test_red_raw_legacy_approve_and_reject_cannot_consume_ui_review(self):
        ticket = self._begin()
        self.assertIs(self.coord.approve(candidate=SecretValue("synthetic")).outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertIs(self.coord.reject().outcome, CoordinatedOutcome.REFUSED)
        self.assertIs(self.ui._ticket, ticket)
        self.assertTrue(self.coord.has_pending)
        self._no_effect()
        self.ui._entry.insert(0, "synthetic")
        self.ui._approve.invoke()
        self.assertFalse(self.coord.has_pending)
        self.assertEqual(self.validator.calls, 1)

    def test_red_same_operation_successor_does_not_approve_or_reject_from_a(self):
        old = self._begin(Op.CONNECT)
        owner = self.ui._owner_token
        self.assertIs(self.coord.reject_ui(ticket=old, owner_token=owner,
                                            root=self.root, operation=Op.CONNECT).outcome,
                      CoordinatedOutcome.REFUSED)
        self.assertFalse(self.coord.has_pending)
        # B has the SAME operation, but a different review instance.
        result, fresh = self.coord.request_ui(Op.CONNECT, owner_token=owner,
                                                   root=self.root)
        self.assertIs(result.outcome, CoordinatedOutcome.PENDING)
        self.assertIsNot(old, fresh)
        self.assertTrue(self.coord.has_pending)
        self.ui._entry.insert(0, "synthetic")
        self.ui._approve.invoke()
        self.assertIs(self.coord._ui_ticket, fresh)
        self.assertTrue(self.coord.has_pending)
        self._no_effect()
        # An old reject callback must leave the successor pending as well.
        self.ui.reject_from_button()
        self.assertIs(self.coord._ui_ticket, fresh)
        self.assertTrue(self.coord.has_pending)
        self._no_effect()

    def test_red_wrong_owner_operation_foreign_and_duplicate_tickets_inert(self):
        ticket = self._begin(Op.CONNECT)
        owner = self.ui._owner_token
        for bad in (
            dict(ticket=object(), owner_token=owner, root=self.root,
                 operation=Op.CONNECT),
            dict(ticket=ticket, owner_token="other-owner", root=self.root,
                 operation=Op.CONNECT),
            dict(ticket=ticket, owner_token=owner, root=self.root,
                 operation=Op.REPLACE),
            dict(ticket=ticket, owner_token=owner, root=object(),
                 operation=Op.CONNECT),
        ):
            self.assertIs(self.coord.approve_ui(
                candidate=SecretValue("synthetic"), **bad).outcome,
                CoordinatedOutcome.REFUSED)
            self.assertIs(self.coord._ui_ticket, ticket)
            self._no_effect()
        self.assertIs(self.coord.reject_ui(
            ticket=object(), owner_token=owner,
            root=self.root, operation=Op.CONNECT).outcome,
            CoordinatedOutcome.REFUSED)
        self.assertIs(self.coord._ui_ticket, ticket)
        self.ui._entry.insert(0, "synthetic")
        self.ui._approve.invoke()
        self.assertFalse(self.coord.has_pending)
        self.assertIs(self.coord.approve_ui(
            ticket=ticket, owner_token=owner, root=self.root,
            operation=Op.CONNECT, candidate=SecretValue("synthetic")).outcome, CoordinatedOutcome.REFUSED)
        self.assertEqual(self.validator.calls, 1)

    def test_red_expired_ticket_does_not_mutate(self):
        ticket = self._begin()
        with mock.patch("nayeon.brain.onboarding_coordination.time.monotonic",
                        return_value=ticket.expires_at + 1):
            self.ui._entry.insert(0, "synthetic")
            self.ui._approve.invoke()
        self._no_effect()
        # Expired consent is refused; the exact stale review is then cleaned
        # up so no pending host operation is stranded without a UI ticket.
        self.assertFalse(self.coord.has_pending)
        self.assertFalse(self.coord._host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertIsNone(self.ui._ticket)
        self.assertFalse(self.ctrl._faulted)

    def test_red_failed_ticket_clock_and_randomness_leave_no_review(self):
        self.ui.close_from_window()
        self.root = tk.Tk()
        self.root.withdraw()
        self.ui = FirstRunCredentialManagementWindow(
            self.root, coordinator=self.coord)
        for module_patch in (
            mock.patch("nayeon.brain.onboarding_coordination.secrets.token_bytes",
                       side_effect=RuntimeError("rng failure")),
            mock.patch("nayeon.brain.onboarding_coordination.time.monotonic",
                       side_effect=RuntimeError("clock failure")),
        ):
            with module_patch:
                self.ui.request_from_button(Op.CONNECT)
            self.assertFalse(self.coord.has_pending)
            self.assertIsNone(self.coord._ui_ticket)
            self._no_effect()

    def test_red_real_tk_destroy_during_request_keeps_no_approval(self):
        original = type(self.coord).request_ui
        child = self.ui

        def destroy_during_request(coordinator, operation, *, owner_token, root):
            response = original(coordinator, operation, owner_token=owner_token,
                                root=root)
            child._root.destroy()
            return response

        with mock.patch.object(type(self.coord), "request_ui",
                               autospec=True, side_effect=destroy_during_request):
            self.ui._choices[0].invoke()
        self.assertTrue(self.ui._closed)
        self.assertFalse(self.coord.has_pending)
        self._no_effect()

    def test_red_real_tk_destroy_during_candidate_read_inert(self):
        ticket = self._begin()
        original = self.ui._entry.get

        def destroy_on_read():
            value = original()
            self.root.destroy()
            return value

        self.ui._entry.insert(0, "synthetic")
        with mock.patch.object(self.ui._entry, "get",
                               side_effect=destroy_on_read):
            self.ui.approve_from_button()
        self._no_effect()
        self.assertTrue(self.ui._closed)
        self.assertFalse(self.coord.has_pending)
        self.assertIsNotNone(ticket)

    def test_red_second_window_cannot_steal_owner_review(self):
        self._begin()
        second_root = tk.Toplevel(self.root)
        second = FirstRunCredentialManagementWindow(
            second_root, coordinator=self.coord)
        second._choices[0].invoke()
        self.assertFalse(second._owns_token())
        self.assertTrue(self.coord.has_pending)
        second._approve.invoke()
        second.close_from_window()
        self.assertTrue(self.coord.has_pending)
        self._no_effect()

    def test_interrupted_delegated_approval_cleans_only_unconsumed_a(self):
        original = self._begin(Op.CONNECT)
        self.ui._entry.insert(0, "synthetic")
        with mock.patch.object(type(self.coord), "_approve_pending",
                               autospec=True,
                               side_effect=RuntimeError("synthetic interrupted consent")):
            self.ui._approve.invoke()
        self.assertFalse(self.coord.has_pending)
        self.assertFalse(self.coord._host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertIsNone(self.ui._ticket)
        self.assertIsNotNone(original)
        self._no_effect()

    def test_interrupted_a_cannot_cancel_reentrant_same_operation_b(self):
        old = self._begin(Op.CONNECT)
        owner = self.ui._owner_token
        successor = []

        def reentrant_replacement(coord, *, candidate=None):
            self.assertIs(coord, self.coord)
            self.assertIs(coord._ui_ticket, old)
            self.assertIs(coord.reject_ui(
                ticket=old, owner_token=owner,
                root=self.root, operation=Op.CONNECT).outcome,
                CoordinatedOutcome.REFUSED)
            receipt, fresh = coord.request_ui(
                Op.CONNECT, owner_token=owner, root=self.root)
            self.assertIs(receipt.outcome, CoordinatedOutcome.PENDING)
            self.assertIsNot(fresh, old)
            successor.append(fresh)
            raise RuntimeError("synthetic old callback failure after successor")

        self.ui._entry.insert(0, "synthetic")
        with mock.patch.object(type(self.coord), "_approve_pending",
                               autospec=True, side_effect=reentrant_replacement):
            self.ui._approve.invoke()
        self.assertEqual(len(successor), 1)
        self.assertIs(self.coord._ui_ticket, successor[0])
        self.assertTrue(self.coord.has_pending)
        self.assertTrue(self.coord._host.has_pending)
        self.ui.reject_from_button()  # Old A callback has no B ticket.
        self.assertIs(self.coord._ui_ticket, successor[0])
        self.assertTrue(self.coord.has_pending)
        self._no_effect()
        # MEDIUM RED: B belongs to the actual closing owner/root. Owner
        # teardown must cancel B without letting A's stale callback do it.
        self.ui.close_from_window()
        self.assertFalse(self.coord.has_pending)
        self.assertFalse(self.coord._host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertIsNone(self.ctrl._ui_window_owner)
        self._no_effect()

    def _reentrant_issuance_replacement(self, dependency, *, raise_in_hook=True):
        owner = self.ui._owner_token
        successor = []
        from nayeon.brain import onboarding_coordination as module

        original = (module.time.monotonic if dependency == "clock"
                    else module.secrets.token_bytes)

        def replace_a(*args, **kwargs):
            # A was requested but no ticket has been issued yet.
            self.assertIsNone(self.coord._ui_ticket)
            self.assertTrue(self.coord.has_pending)
            self.assertIs(self.coord.reject().outcome, CoordinatedOutcome.REFUSED)
            replacement = self.coord.request(Op.CONNECT)  # Same operation B.
            self.assertIs(replacement.outcome, CoordinatedOutcome.PENDING)
            successor.append(self.coord._pending)
            if raise_in_hook:
                raise RuntimeError("synthetic issuance dependency failure")
            return original(*args, **kwargs)

        target = ("nayeon.brain.onboarding_coordination.time.monotonic"
                  if dependency == "clock" else
                  "nayeon.brain.onboarding_coordination.secrets.token_bytes")
        with mock.patch(target, side_effect=replace_a):
            result, issued = self.coord.request_ui(
                Op.CONNECT, owner_token=owner, root=self.root)
        self.assertIs(result.outcome, CoordinatedOutcome.UNAVAILABLE)
        self.assertIsNone(issued)
        self.assertEqual(len(successor), 1)
        self.assertIs(self.coord._pending, successor[0])
        self.assertTrue(self.coord.has_pending)
        self.assertTrue(self.coord._host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self._no_effect()
        self.assertIs(self.coord.reject().outcome, CoordinatedOutcome.REFUSED)
        self.assertFalse(self.coord.has_pending)

    def test_red_reentrant_clock_failure_cannot_cancel_successor(self):
        self._reentrant_issuance_replacement("clock")

    def test_red_reentrant_rng_failure_cannot_cancel_successor(self):
        self._reentrant_issuance_replacement("rng")

    def test_red_reentrant_clock_return_cannot_ticket_successor_as_a(self):
        self._reentrant_issuance_replacement("clock", raise_in_hook=False)

    def test_red_owner_root_destroy_cleans_reentrant_b_not_during_a_callback(self):
        old = self._begin(Op.CONNECT)
        owner = self.ui._owner_token
        successor = []

        def reentrant_replacement(coord, *, candidate=None):
            self.assertIs(coord.reject_ui(
                ticket=old, owner_token=owner, root=self.root,
                operation=Op.CONNECT).outcome, CoordinatedOutcome.REFUSED)
            result, fresh = coord.request_ui(
                Op.CONNECT, owner_token=owner, root=self.root)
            self.assertIs(result.outcome, CoordinatedOutcome.PENDING)
            successor.append(fresh)
            raise RuntimeError("old A interrupted after B review")

        self.ui._entry.insert(0, "synthetic")
        with mock.patch.object(type(self.coord), "_approve_pending",
                               autospec=True, side_effect=reentrant_replacement):
            self.ui._approve.invoke()
        self.assertIs(self.coord._ui_ticket, successor[0])
        self._no_effect()
        self.root.destroy()  # Actual Tk root destruction, not WM_DELETE_WINDOW.
        self.assertFalse(self.coord.has_pending)
        self.assertFalse(self.coord._host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self.assertIsNone(self.ctrl._ui_window_owner)
        self._no_effect()

    def _approval_clock_swap_a_for_b(self, *, raises=False, use_tk=False):
        """Adversarial approval-time dependency swaps same-operation review A.

        Every permit for B must require B's own consent. A's synthetic value
        must not reach B's fake validator or backend, even if clock returns a
        numerically valid time or raises after reentrant substitution.
        """
        from nayeon.brain import onboarding_coordination as module

        ticket_a = self._begin(Op.CONNECT)
        owner = self.ui._owner_token
        original_clock = module.time.monotonic
        seen = []
        successor = []
        candidate = SecretValue("A-only-synthetic-do-not-log")

        def swap_on_expiry_clock():
            if seen:
                return original_clock()
            seen.append("A-clock-called")
            self.assertIs(self.coord._ui_ticket, ticket_a)
            self.assertIs(self.coord.reject_ui(
                ticket=ticket_a, owner_token=owner,
                root=self.root, operation=Op.CONNECT).outcome,
                CoordinatedOutcome.REFUSED)
            result, ticket_b = self.coord.request_ui(
                Op.CONNECT, owner_token=owner, root=self.root)
            self.assertIs(result.outcome, CoordinatedOutcome.PENDING)
            self.assertIsNot(ticket_b, ticket_a)
            successor.append(ticket_b)
            self.assertIs(self.coord._ui_ticket, ticket_b)
            if raises:
                raise RuntimeError("synthetic A expiry clock fault after B issued")
            return ticket_a.issued + 0.01

        if use_tk:
            self.ui._entry.insert(0, "A-only-synthetic-do-not-log")
        with mock.patch.object(module.time, "monotonic",
                               side_effect=swap_on_expiry_clock):
            if use_tk:
                self.ui._approve.invoke()
                receipt = None
            else:
                receipt = self.coord.approve_ui(
                    ticket=ticket_a, owner_token=owner, root=self.root,
                    operation=Op.CONNECT, candidate=candidate)
        self.assertEqual(seen, ["A-clock-called"])
        self.assertEqual(len(successor), 1)
        if receipt is not None:
            self.assertIs(receipt.outcome, CoordinatedOutcome.REFUSED)
        self.assertIs(self.coord._ui_ticket, successor[0])
        self.assertTrue(self.coord.has_pending)
        self.assertTrue(self.coord._host.has_pending)
        self.assertIs(self.coord._operation, Op.CONNECT)
        self._no_effect()
        # The actual owner can explicitly close and revoke B, whereas the
        # old approval A's callback may never reject B on its own.
        self.ui.close_from_window()
        self.assertFalse(self.coord.has_pending)
        self.assertFalse(self.coord._host.has_pending)
        self.assertIsNone(self.coord._ui_ticket)
        self._no_effect()

    def test_red_approval_clock_return_must_not_authorise_same_operation_b(self):
        self._approval_clock_swap_a_for_b(raises=False, use_tk=False)

    def test_red_approval_clock_raise_must_not_consume_same_operation_b(self):
        self._approval_clock_swap_a_for_b(raises=True, use_tk=False)

    def test_red_real_tk_approval_clock_reentry_cannot_authorise_b(self):
        self._approval_clock_swap_a_for_b(raises=False, use_tk=True)

    def test_red_remove_requires_coordinator_level_acknowledgement(self):
        # Synthetic pre-existing key, never native storage.
        self.backend.value = SecretValue("synthetic-old")
        ProviderConnectionFileStore(self.composed.metadata_path).save(
            ProviderConnectionDocumentV1(
                connection=ProviderConnectionConfiguration(
                    "openai", "gpt-5.6", SecretIdentifier("openai.api_key"))))
        # The original READY baseline was (unconfigured, absent). Changing
        # metadata and synthetic presence invalidates that trust evidence:
        # a REMOVE operation must never execute under the stale baseline.
        self.assertNotEqual(self.ctrl._baseline, self.ctrl._observe())
        self.ctrl.close()
        fresh_review = self.ctrl.request_reconciliation()
        self.assertTrue(self.ctrl.approve_reconciliation(
            human_approved=True, fingerprint=fresh_review.fingerprint,
            expected_review=fresh_review))
        self.assertEqual(self.ctrl._baseline, self.ctrl._observe())
        ticket = self._begin(Op.REMOVE)
        owner = self.ui._owner_token
        self.assertIs(self.coord.approve_ui(
            ticket=ticket, owner_token=owner, root=self.root,
            operation=Op.REMOVE, acknowledged=False).outcome, CoordinatedOutcome.REFUSED)
        self.assertIsNotNone(self.backend.value)
        self.assertTrue(self.coord.has_pending)
        self.ui._acknowledged.set(True)
        self.ui._approve.invoke()
        self.assertIsNone(self.backend.value)
        self.assertEqual(self.backend.calls.count("delete"), 1)


if __name__ == "__main__":
    unittest.main()
