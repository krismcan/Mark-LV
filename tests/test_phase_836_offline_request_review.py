"""Phase 8.36 A: pure OFFLINE admission, replay, expiry and authority tests."""
from __future__ import annotations

import threading
import unittest
from dataclasses import FrozenInstanceError, replace
from unittest import mock

from nayeon.desktop_alpha.offline_request_review import (
    DISCLOSURE, MAX_CLOCK_MS, REVIEW_TTL_MS, RECEIPT_TEXT,
    OfflineRequestReviewOwner, OfflineReviewPreview, OfflineReviewReceipt,
    ReviewContext, ReviewRefused, ReviewState, ReviewTicket,
)


class OfflineRequestReviewTests(unittest.TestCase):
    def setUp(self):
        self.root = object()
        self.pane = object()
        self.session = object()
        self.ctx = ReviewContext(self.root, self.pane, self.session, 2, 3, 4)
        self.owner = OfflineRequestReviewOwner(self.root)
        self.prompt = "Hello Nayeon"

    def offer(self, now=100):
        return self.owner.offer(self.ctx, self.prompt, now)

    def prepare(self):
        preview = self.offer()
        self.owner.begin_enable(self.ctx, self.prompt, 101)
        ticket = self.owner.arm_after_last_tk(self.ctx, self.prompt, 102)
        return preview, ticket

    def test_complete_offline_non_authorizing_receipt(self):
        preview, ticket = self.prepare()
        self.assertIs(type(preview), OfflineReviewPreview)
        self.assertEqual(preview.prompt, self.prompt)
        self.assertEqual(preview.disclosure, DISCLOSURE)
        self.assertIn("NO AI REQUEST", DISCLOSURE)
        receipt = self.owner.confirm(ticket, self.ctx, self.prompt, 103)
        self.assertEqual(receipt.status, RECEIPT_TEXT)
        self.assertFalse(receipt.permits_network)
        self.assertFalse(receipt.permits_action)
        self.assertFalse(receipt.permits_persistence)
        self.assertIs(self.owner.state, ReviewState.IDLE)

    def test_one_use_ticket_replay(self):
        _, ticket = self.prepare()
        self.owner.confirm(ticket, self.ctx, self.prompt, 103)
        with self.assertRaises(ReviewRefused):
            self.owner.confirm(ticket, self.ctx, self.prompt, 104)

    def test_confirm_before_enable_poison(self):
        self.offer()
        with self.assertRaisesRegex(ReviewRefused, "CONFIRM_BEFORE_ARM"):
            self.owner.confirm(ReviewTicket(), self.ctx, self.prompt, 101)
        self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_confirm_during_enable_poison_no_late_arm(self):
        self.offer()
        self.owner.begin_enable(self.ctx, self.prompt, 101)
        with self.assertRaisesRegex(ReviewRefused, "CONFIRM_BEFORE_ARM"):
            self.owner.confirm(None, self.ctx, self.prompt, 101)
        with self.assertRaises(ReviewRefused):
            self.owner.arm_after_last_tk(self.ctx, self.prompt, 102)

    def test_cannot_arm_without_starting_enable(self):
        self.offer()
        with self.assertRaisesRegex(ReviewRefused, "NOT_ENABLING"):
            self.owner.arm_after_last_tk(self.ctx, self.prompt, 101)

    def test_bogus_or_copied_ticket_refused(self):
        _, ticket = self.prepare()
        for counterfeit in (ReviewTicket(), None, object(), False):
            with self.subTest(type=type(counterfeit).__name__), self.assertRaises(ReviewRefused):
                self.owner.confirm(counterfeit, self.ctx, self.prompt, 103)
        self.assertIs(self.owner.state, ReviewState.ARMED)
        self.assertIs(type(ticket), ReviewTicket)

    def test_stale_prompt_at_arm_poison(self):
        self.offer()
        self.owner.begin_enable(self.ctx, self.prompt, 101)
        with self.assertRaisesRegex(ReviewRefused, "STALE_REVIEW"):
            self.owner.arm_after_last_tk(self.ctx, "changed", 102)
        self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_stale_prompt_at_confirm_poison(self):
        _, ticket = self.prepare()
        with self.assertRaisesRegex(ReviewRefused, "STALE_REVIEW"):
            self.owner.confirm(ticket, self.ctx, "changed", 103)
        self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_copied_identical_context_refused(self):
        _, ticket = self.prepare()
        clone = replace(self.ctx)
        self.assertIsNot(clone, self.ctx)
        with self.assertRaisesRegex(ReviewRefused, "STALE_REVIEW"):
            self.owner.confirm(ticket, clone, self.prompt, 103)

    def test_wrong_root_or_context_denied(self):
        cases = (
            ReviewContext(object(), self.pane, self.session, 2, 3, 4),
            ReviewContext(self.root, object(), self.session, 2, 3, 4),
            ReviewContext(self.root, self.pane, object(), 2, 3, 4),
            ReviewContext(self.root, self.pane, self.session, 9, 3, 4),
            ReviewContext(self.root, self.pane, self.session, 2, 9, 4),
            ReviewContext(self.root, self.pane, self.session, 2, 3, 9),
        )
        for ctx in cases:
            owner = OfflineRequestReviewOwner(self.root)
            with self.subTest(context=ctx.generation), self.assertRaises(ReviewRefused):
                owner.offer(ctx, self.prompt, 10) if ctx.root is not self.root else (
                    owner.offer(self.ctx, self.prompt, 10),
                    owner.begin_enable(ctx, self.prompt, 11),
                )

    def test_bool_and_foreign_mutable_context_refused(self):
        for candidate in (None, {}, object(), ReviewContext(self.root, [], self.session, 1, 2, 3),
                          ReviewContext(self.root, self.pane, self.session, True, 2, 3)):
            owner = OfflineRequestReviewOwner(self.root)
            with self.subTest(type=type(candidate).__name__), self.assertRaises(ReviewRefused):
                owner.offer(candidate, self.prompt, 100)

    def test_frozen_snapshots(self):
        preview = self.offer()
        with self.assertRaises(FrozenInstanceError):
            preview.prompt = "bad"
        with self.assertRaises(FrozenInstanceError):
            self.ctx.epoch = 4

    def test_no_history_storage(self):
        _, ticket = self.prepare()
        self.owner.confirm(ticket, self.ctx, self.prompt, 103)
        self.assertIsNone(self.owner._prompt)
        self.assertIsNone(self.owner._ticket)
        self.assertIsNone(self.owner._context)

    def test_refuses_second_inflight_review(self):
        self.offer()
        with self.assertRaisesRegex(ReviewRefused, "BUSY"):
            self.offer(101)

    def test_reset_clears_poison_then_new_review(self):
        self.offer()
        self.owner.abort()
        self.assertIs(self.owner.state, ReviewState.POISONED)
        self.owner.reset()
        self.assertIs(self.owner.state, ReviewState.IDLE)
        self.assertEqual(self.offer(101).prompt, self.prompt)

    def test_abort_revokes_armed_ticket(self):
        _, ticket = self.prepare()
        self.owner.abort()
        with self.assertRaises(ReviewRefused):
            self.owner.confirm(ticket, self.ctx, self.prompt, 103)

    def test_close_terminal(self):
        _, ticket = self.prepare()
        self.owner.close()
        self.assertIs(self.owner.state, ReviewState.CLOSED)
        with self.assertRaises(ReviewRefused):
            self.owner.reset()
        with self.assertRaises(ReviewRefused):
            self.owner.confirm(ticket, self.ctx, self.prompt, 103)

    def test_expiry_exact_deadline_refused(self):
        self.offer()
        with self.assertRaisesRegex(ReviewRefused, "STALE_REVIEW"):
            self.owner.begin_enable(self.ctx, self.prompt, 100 + REVIEW_TTL_MS)

    def test_expiry_after_arm_refused(self):
        _, ticket = self.prepare()
        with self.assertRaisesRegex(ReviewRefused, "STALE_REVIEW"):
            self.owner.confirm(ticket, self.ctx, self.prompt, 100 + REVIEW_TTL_MS)

    def test_monotonic_clock_rollback_poison(self):
        self.offer(200)
        with self.assertRaisesRegex(ReviewRefused, "CLOCK"):
            self.owner.begin_enable(self.ctx, self.prompt, 199)
        self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_no_boolean_or_overflow_clock(self):
        for bad in (True, -1, MAX_CLOCK_MS + 1, None, 1.5):
            owner = OfflineRequestReviewOwner(self.root)
            with self.subTest(bad=bad), self.assertRaises(ReviewRefused):
                owner.offer(self.ctx, self.prompt, bad)
        owner = OfflineRequestReviewOwner(self.root)
        with self.assertRaisesRegex(ReviewRefused, "CLOCK"):
            owner.offer(self.ctx, self.prompt, MAX_CLOCK_MS)

    def test_malformed_prompt_refused(self):
        samples = ("", "   ", "a" * 513, "e\u0301", "hello\n", "hello\r",
                   "hello\t", "hello\u2028", "\ud800", "\u200b")
        for text in samples:
            owner = OfflineRequestReviewOwner(self.root)
            with self.subTest(value=ascii(text)), self.assertRaisesRegex(ReviewRefused, "PROMPT"):
                owner.offer(self.ctx, text, 100)
        for bad in (None, 42, True, [], {}, object()):
            owner = OfflineRequestReviewOwner(self.root)
            with self.subTest(type=type(bad).__name__), self.assertRaises(ReviewRefused):
                owner.offer(self.ctx, bad, 100)

    def test_valid_512_unicode_and_2048_bytes(self):
        long = "😊" * 512
        preview = self.owner.offer(self.ctx, long, 100)
        self.assertEqual(preview.prompt, long)
        self.assertEqual(len(long.encode("utf-8")), 2048)

    def test_wrong_thread_refuses_without_mutation(self):
        results = []
        def run():
            try:
                self.owner.offer(self.ctx, self.prompt, 100)
            except ReviewRefused as e:
                results.append(str(e))
        t = threading.Thread(target=run)
        t.start()
        t.join(3)
        self.assertFalse(t.is_alive())
        self.assertEqual(results, ["WRONG_THREAD"])
        self.assertIs(self.owner.state, ReviewState.IDLE)

    def test_no_retained_callback_or_writable_capabilities(self):
        self.assertFalse(hasattr(self.owner, "__dict__"))
        for forbidden in ("_provider", "_service", "_store", "_resolver",
                          "_callback", "_widget", "_path", "_client"):
            self.assertFalse(hasattr(self.owner, forbidden))
        with mock.patch("socket.socket", side_effect=AssertionError("network")):
            _, ticket = self.prepare()
            self.assertFalse(self.owner.confirm(ticket, self.ctx, self.prompt, 103).permits_network)

    def test_receipt_cannot_forge_network_authority(self):
        for altered in (
            {"permits_network": True}, {"permits_action": True},
            {"permits_persistence": True}, {"status": "SENT"},
        ):
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                OfflineReviewReceipt(**altered)


if __name__ == "__main__":
    unittest.main()
