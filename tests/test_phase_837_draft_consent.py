"""Pure adversarial draft consent tests; no Tk interpreter or effects."""
from dataclasses import FrozenInstanceError, replace
import threading
import unittest

from nayeon.desktop_alpha.offline_draft_consent import (
    DraftTicket, OfflineDraftConsentOwner,
)
from nayeon.desktop_alpha.offline_request_draft import (
    DISCLOSURE, OfflineRequestDraft, RECEIPT_TEXT,
)
from nayeon.desktop_alpha.offline_request_review import (
    MAX_CLOCK_MS, OfflineRequestReviewOwner, ReviewContext, ReviewRefused,
    ReviewState, ReviewTicket,
)


class DraftConsentTests(unittest.TestCase):
    def setUp(self):
        self.root = object()
        self.ctx = ReviewContext(self.root, object(), object(), 1, 2, 3)
        self.owner = OfflineDraftConsentOwner(self.root)

    def offer(self, now=100):
        return self.owner.offer(self.ctx, "openai", "example-model", "literal prompt", now)

    def arm(self, now=100):
        draft = self.offer(now)
        self.owner.begin_enable(self.ctx, draft, now + 1)
        ticket = self.owner.arm_after_last_tk(self.ctx, draft, now + 2)
        return draft, ticket

    def confirm(self, ticket, **changes):
        args = dict(ctx=self.ctx, provider="openai", model="example-model",
                    prompt="literal prompt", now_ms=103)
        args.update(changes)
        return self.owner.confirm(ticket, **args)

    def test_exact_immutable_non_authorizing_receipt_and_one_use(self):
        draft, ticket = self.arm()
        self.assertIs(type(ticket), DraftTicket)
        self.assertIsNot(type(ticket), ReviewTicket)
        receipt = self.confirm(ticket)
        self.assertIs(receipt.draft, draft)
        self.assertEqual(receipt.status, RECEIPT_TEXT)
        self.assertEqual(receipt.disclosure, DISCLOSURE)
        for field in ("permits_network", "permits_action", "permits_persistence"):
            self.assertIs(getattr(receipt, field), False)
        with self.assertRaises(FrozenInstanceError):
            receipt.draft = draft
        with self.assertRaises(ReviewRefused):
            self.confirm(ticket)

    def test_model_provider_prompt_and_exact_context_bound(self):
        for change in (dict(model="different"), dict(provider="OPENAI"),
                       dict(prompt="other"), dict(model=None),
                       dict(ctx=replace(self.ctx)),
                       dict(ctx=replace(self.ctx, root=object())),
                       dict(ctx=replace(self.ctx, pane=object())),
                       dict(ctx=replace(self.ctx, session=object())),
                       dict(ctx=replace(self.ctx, generation=2)),
                       dict(ctx=replace(self.ctx, epoch=3)),
                       dict(ctx=replace(self.ctx, revision=4))):
            with self.subTest(change=tuple(change)):
                self.owner = OfflineDraftConsentOwner(self.root)
                _, ticket = self.arm()
                with self.assertRaises(ReviewRefused):
                    self.confirm(ticket, **change)
                self.assertIs(self.owner.state, ReviewState.POISONED)
                with self.assertRaises(ReviewRefused):
                    self.confirm(ticket)

    def test_counterfeit_foreign_prompt_ticket_and_copied_ticket_cancel(self):
        prompt_owner = OfflineRequestReviewOwner(self.root)
        prompt_owner.offer(self.ctx, "literal prompt", 100)
        prompt_owner.begin_enable(self.ctx, "literal prompt", 101)
        prompt_ticket = prompt_owner.arm_after_last_tk(self.ctx, "literal prompt", 102)
        for wrong in (DraftTicket(), ReviewTicket(), prompt_ticket, None, object()):
            self.owner = OfflineDraftConsentOwner(self.root)
            _, ticket = self.arm()
            with self.assertRaises(ReviewRefused):
                self.confirm(wrong)
            with self.assertRaises(ReviewRefused):
                self.confirm(ticket)
        self.assertIs(prompt_owner.state, ReviewState.ARMED)

    def test_elapsed_thirty_seconds_and_clock_refusal(self):
        for now in (30_100, 30_101, 99, True, -1, MAX_CLOCK_MS + 1):
            self.owner = OfflineDraftConsentOwner(self.root)
            _, ticket = self.arm()
            with self.assertRaises(ReviewRefused):
                self.confirm(ticket, now_ms=now)
            self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_offer_deadline_does_not_restart_at_enable(self):
        draft = self.offer()
        self.owner.begin_enable(self.ctx, draft, 30_099)
        with self.assertRaises(ReviewRefused):
            self.owner.arm_after_last_tk(self.ctx, draft, 30_100)

    def test_cloned_draft_cannot_arm(self):
        draft = self.offer()
        self.owner.begin_enable(self.ctx, draft, 101)
        clone = OfflineRequestDraft(draft.provider, draft.model, draft.prompt)
        with self.assertRaises(ReviewRefused):
            self.owner.arm_after_last_tk(self.ctx, clone, 102)
        self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_confirm_before_or_during_enable_revokes(self):
        for enable in (False, True):
            self.owner = OfflineDraftConsentOwner(self.root)
            draft = self.offer()
            if enable:
                self.owner.begin_enable(self.ctx, draft, 101)
            with self.assertRaises(ReviewRefused):
                self.confirm(DraftTicket())
            with self.assertRaises(ReviewRefused):
                self.owner.arm_after_last_tk(self.ctx, draft, 102)

    def test_cancel_reset_close_and_successor_replay(self):
        _, old = self.arm()
        self.owner.abort()
        with self.assertRaises(ReviewRefused):
            self.confirm(old)
        self.owner.reset()
        _, successor = self.arm(now=104)
        self.assertIsNot(successor, old)
        with self.assertRaises(ReviewRefused):
            self.confirm(old, now_ms=107)
        self.owner.close()
        with self.assertRaises(ReviewRefused):
            self.owner.reset()
        self.assertIs(self.owner.state, ReviewState.CLOSED)

    def test_cross_owner_ticket_never_transfers(self):
        _, ticket = self.arm()
        other = OfflineDraftConsentOwner(self.root)
        draft = other.offer(self.ctx, "openai", "example-model", "literal prompt", 100)
        other.begin_enable(self.ctx, draft, 101)
        other.arm_after_last_tk(self.ctx, draft, 102)
        with self.assertRaises(ReviewRefused):
            other.confirm(ticket, self.ctx, "openai", "example-model", "literal prompt", 103)
        self.assertIs(self.owner.state, ReviewState.ARMED)

    def test_untrusted_values_do_not_invoke_hooks(self):
        class Hostile:
            def __eq__(self, other):
                raise AssertionError("untrusted equality")
            def __str__(self):
                raise AssertionError("untrusted conversion")
        for field in ("provider", "model", "prompt"):
            self.owner = OfflineDraftConsentOwner(self.root)
            _, ticket = self.arm()
            with self.assertRaises(ReviewRefused):
                self.confirm(ticket, **{field: Hostile()})

    def test_invalid_offer_is_fixed_refusal_and_not_armed(self):
        for provider, model, prompt in (("", "example", "hello"),
                                       ("openai", "a/b", "hello"),
                                       ("openai", "x" * 81, "hello"),
                                       ("openai", "example", "")):
            self.owner.reset()
            with self.assertRaises(ReviewRefused):
                self.owner.offer(self.ctx, provider, model, prompt, 100)
            self.assertIs(self.owner.state, ReviewState.POISONED)

    def test_foreign_thread_refuses_before_mutating_any_owned_state(self):
        draft, ticket = self.arm()
        operations = (
            lambda: self.owner.state, self.owner.abort, self.owner.reset,
            self.owner.close, self.offer,
            lambda: self.owner.begin_enable(self.ctx, draft, 103),
            lambda: self.owner.arm_after_last_tk(self.ctx, draft, 103),
            lambda: self.confirm(ticket),
        )
        failures = []
        def foreign():
            for operation in operations:
                try:
                    operation()
                except ReviewRefused as error:
                    failures.append(str(error))
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(failures, ["WRONG_THREAD"] * len(operations))
        self.assertIs(self.owner.state, ReviewState.ARMED)
        self.assertEqual(self.confirm(ticket).status, RECEIPT_TEXT)


if __name__ == "__main__":
    unittest.main()
