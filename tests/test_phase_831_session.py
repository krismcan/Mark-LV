"""Phase 8.31 Increment A: pure in-memory session adversarial acceptance.

Synthetic Python-only tests. No Tk, provider, credentials, native mutex,
filesystem writes, network or desktop action effects are performed.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import inspect
import unittest
from unittest import mock

from nayeon.desktop_alpha import conversation_session as m


class SessionFixture(unittest.TestCase):
    def setUp(self):
        self.root = object()
        self.other_root = object()
        self.owner = m.OfflineConversationSession(self.root)
        self.view = self.owner.activate_view(self.root, object())

    def assert_refusal(self, code, call, *args, **kwargs):
        with self.assertRaises(m.SessionRefused) as caught:
            call(*args, **kwargs)
        self.assertIs(caught.exception.code, code)

    def send(self, content="Hello"):
        return self.owner.submit(self.root, self.view, content)


class AdmissionTests(SessionFixture):
    def test_initial_state_is_empty_ephemeral_and_not_closed(self):
        snap = self.owner.snapshot
        self.assertEqual(snap.entries, ())
        self.assertEqual(snap.byte_count, 0)
        self.assertFalse(snap.closed)
        self.assertEqual(snap.revision, 0)

    def test_one_submit_commits_user_and_true_offline_status_atomically(self):
        before = self.owner.snapshot
        result = self.send("Open Notepad")
        after = self.owner.snapshot
        self.assertIsNot(before, after)
        self.assertEqual(before.entries, ())
        self.assertIs(after, result.snapshot)
        self.assertIs(result.state, m.SubmissionState.COMMITTED)
        self.assertEqual(after.revision, 1)
        self.assertEqual(len(after.entries), 2)
        self.assertEqual([e.source for e in after.entries],
                         [m.EntrySource.USER, m.EntrySource.LOCAL_STATUS])
        self.assertTrue(all(e.state is m.EntryState.UNSENT_OFFLINE for e in after.entries))
        self.assertEqual(after.entries[0].payload, "Open Notepad")
        self.assertEqual(after.entries[1].payload, m.OFFLINE_STATUS)
        self.assertIn("No AI request or action", after.entries[1].payload)
        self.assertIsNone(self.owner.active_submission_state)

    def test_untrusted_root_and_foreign_view_refused(self):
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.submit,
                            self.other_root, self.view, "hello")
        alien = m.ConversationView(object(), self.view.generation)
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.submit,
                            self.root, alien, "hello")
        self.assertEqual(self.owner.snapshot.entries, ())

    def test_wrong_root_identity_type_rejected(self):
        self.assert_refusal(m.RefusalCode.AUTHORITY, m.OfflineConversationSession,
                            "wrong")
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.activate_view,
                            self.root, "wrong")

    def test_ticket_is_single_use_and_copied_data_is_not_authority(self):
        ticket = self.owner.issue_submission(self.root, self.view, "Hello")
        self.assertIs(self.owner.active_submission_state, m.SubmissionState.ISSUED)
        self.assert_refusal(m.RefusalCode.BUSY, self.owner.issue_submission,
                            self.root, self.view, "second")
        copy = replace(ticket)
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.claim_submission,
                            self.root, self.view, copy)
        self.owner.claim_submission(self.root, self.view, ticket)
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.claim_submission,
                            self.root, self.view, ticket)
        self.owner.commit_submission(self.root, self.view, ticket)
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.commit_submission,
                            self.root, self.view, ticket)
        self.assertFalse(self.owner.revoke_submission(self.root, ticket))
        self.assertEqual(len(self.owner.snapshot.entries), 2)

    def test_navigation_preserves_entries_but_revokes_old_view(self):
        self.send("alpha")
        old = self.view
        self.view = self.owner.activate_view(self.root, object())
        self.assertEqual(len(self.owner.snapshot.entries), 2)
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.submit,
                            self.root, old, "old")
        self.send("beta")
        self.assertEqual(len(self.owner.snapshot.entries), 4)
        self.assertFalse(self.owner.revoke_view(self.root, old))

    def test_revoked_pending_ticket_cannot_consume_successor(self):
        ticket_a = self.owner.issue_submission(self.root, self.view, "A")
        self.owner.claim_submission(self.root, self.view, ticket_a)
        self.assertTrue(self.owner.revoke_submission(self.root, ticket_a))
        ticket_b = self.owner.issue_submission(self.root, self.view, "B")
        self.assertFalse(self.owner.revoke_submission(self.root, ticket_a))
        self.owner.claim_submission(self.root, self.view, ticket_b)
        self.owner.commit_submission(self.root, self.view, ticket_b)
        self.assertEqual(self.owner.snapshot.entries[0].payload, "B")

    def test_render_or_caller_cannot_mutate_prior_snapshot(self):
        previous = self.owner.snapshot
        self.send("Hello")
        now = self.owner.snapshot
        self.assertEqual(previous.entries, ())
        self.assertIsInstance(now.entries, tuple)
        with self.assertRaises(FrozenInstanceError):
            now.revision = 123
        with self.assertRaises(FrozenInstanceError):
            now.entries[0].payload = "forged"


class InputBoundsTests(SessionFixture):
    def test_unicode_supplementary_at_codepoint_and_byte_cap(self):
        self.send("\U0001f642" * 512)
        self.assertEqual(len(self.owner.snapshot.entries[0].payload), 512)
        self.assertEqual(self.owner.snapshot.entries[0].byte_count, 2048)

    def test_exactly_513_codepoints_is_rejected(self):
        self.assert_refusal(m.RefusalCode.INPUT, self.send, "a" * 513)
        self.assertEqual(self.owner.snapshot.entries, ())

    def test_empty_spaces_controls_bidi_surrogate_and_decomposed_denied(self):
        bad = ["", " ", "\t", "\n", "\r", "x\nz", "x\x00z", "\x1b[0m",
               "\u202e", "\u2066", "\u200f", "\u2028", "\u2029",
               "\ud800", "\udfff", "e\u0301"]
        for text in bad:
            with self.subTest(text=ascii(text)):
                self.assert_refusal(m.RefusalCode.INPUT, self.send, text)
        self.assertEqual(self.owner.snapshot.entries, ())

    def test_normalized_accent_is_allowed(self):
        self.send("\u00e9")
        self.assertEqual(self.owner.snapshot.entries[0].payload, "\u00e9")

    def test_wrong_input_type_and_subclass_denied(self):
        class Evil(str):
            def encode(self, *a, **k):
                raise AssertionError("side effect")
        for candidate in (None, 123, Evil("hello"), b"bytes"):
            self.assert_refusal(m.RefusalCode.INPUT, self.send, candidate)

    def test_rejections_do_not_increment_revision_or_append(self):
        for _ in range(50):
            self.assert_refusal(m.RefusalCode.INPUT, self.send, "")
        self.assertEqual(self.owner.snapshot.revision, 0)
        self.assertEqual(len(self.owner.snapshot.entries), 0)

    def test_entry_count_capacity_is_finite_and_atomic(self):
        for i in range(32):
            self.send(str(i))
        old = self.owner.snapshot
        self.assertEqual(len(old.entries), 64)
        self.assert_refusal(m.RefusalCode.FULL, self.send, "extra")
        self.assertIs(self.owner.snapshot, old)
        self.assertEqual(len(self.owner.snapshot.entries), 64)
        self.assertIsNone(self.owner.active_submission_state)

    def test_byte_capacity_is_finite_and_atomic(self):
        # Each accepted 4-byte Unicode input consumes 2048 + fixed status bytes.
        for i in range(30):
            try:
                self.send("\U0001f642" * 512)
            except m.SessionRefused as e:
                self.assertIs(e.code, m.RefusalCode.FULL)
                break
        snap = self.owner.snapshot
        self.assertLessEqual(snap.byte_count, 65536)
        self.assertLessEqual(len(snap.entries), 64)
        before = snap
        self.assert_refusal(m.RefusalCode.FULL, self.send, "\U0001f642" * 512)
        self.assertIs(self.owner.snapshot, before)


class ResetAuthorityTests(SessionFixture):
    def test_clear_requires_current_exact_one_use_review(self):
        self.send("first")
        before = self.owner.snapshot
        review = self.owner.begin_reset_review(self.root, self.view,
                       m.ResetOperation.CLEAR, now_ms=10)
        copy = replace(review)
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, copy,
                            m.ResetOperation.CLEAR, now_ms=11)
        after = self.owner.confirm_reset(self.root, self.view, review,
                                         m.ResetOperation.CLEAR, now_ms=12)
        self.assertEqual(after.entries, ())
        self.assertEqual(after.revision, before.revision + 1)
        self.assertIs(after.session_identity, before.session_identity)
        self.assertEqual(after.epoch, before.epoch)
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, review,
                            m.ResetOperation.CLEAR, now_ms=13)

    def test_clear_vs_new_session_operation_does_not_alias(self):
        self.send("first")
        old = self.owner.snapshot
        review = self.owner.begin_reset_review(self.root, self.view,
                    m.ResetOperation.NEW_SESSION, now_ms=100)
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, review,
                            m.ResetOperation.CLEAR, now_ms=101)
        after = self.owner.confirm_reset(self.root, self.view, review,
                                         m.ResetOperation.NEW_SESSION, now_ms=102)
        self.assertIsNot(after.session_identity, old.session_identity)
        self.assertEqual(after.epoch, old.epoch + 1)
        self.assertEqual(after.entries, ())

    def test_same_transcript_review_A_cannot_consume_successor_B(self):
        a = self.owner.begin_reset_review(self.root, self.view,
                    m.ResetOperation.CLEAR, now_ms=10)
        b = self.owner.begin_reset_review(self.root, self.view,
                    m.ResetOperation.CLEAR, now_ms=11)
        self.assertFalse(self.owner.dismiss_reset_review(self.root, a))
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, a,
                            m.ResetOperation.CLEAR, now_ms=12)
        self.owner.confirm_reset(self.root, self.view, b,
                                 m.ResetOperation.CLEAR, now_ms=13)

    def test_new_submit_revokes_existing_reset_review(self):
        r = self.owner.begin_reset_review(self.root, self.view,
                  m.ResetOperation.CLEAR, now_ms=10)
        self.send("new message")
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, r,
                            m.ResetOperation.CLEAR, now_ms=11)
        self.assertEqual(len(self.owner.snapshot.entries), 2)

    def test_navigating_revokes_review_without_erasing_transcript(self):
        self.send("first")
        r = self.owner.begin_reset_review(self.root, self.view,
                 m.ResetOperation.CLEAR, now_ms=10)
        old = self.view
        self.view = self.owner.activate_view(self.root, object())
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, old, r, m.ResetOperation.CLEAR, now_ms=11)
        self.assertEqual(len(self.owner.snapshot.entries), 2)

    def test_reset_expiration_and_clock_regression_fail_closed(self):
        r = self.owner.begin_reset_review(self.root, self.view,
                 m.ResetOperation.CLEAR, now_ms=10)
        self.assertFalse(self.owner.expire_reset_review(self.root, self.view, r,
                                                        now_ms=11))
        self.assert_refusal(m.RefusalCode.CLOCK, self.owner.confirm_reset,
                            self.root, self.view, r,
                            m.ResetOperation.CLEAR, now_ms=9)
        self.assertTrue(self.owner.expire_reset_review(self.root, self.view, r,
                                                       now_ms=30010))
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, r,
                            m.ResetOperation.CLEAR, now_ms=30011)

    def test_root_close_refuses_further_authority(self):
        review = self.owner.begin_reset_review(self.root, self.view,
                    m.ResetOperation.CLEAR, now_ms=10)
        self.assertTrue(self.owner.close(self.root))
        self.assertFalse(self.owner.close(self.root))
        self.assertTrue(self.owner.snapshot.closed)
        self.assertEqual(self.owner.snapshot.entries, ())
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.submit,
                            self.root, self.view, "after")
        self.assert_refusal(m.RefusalCode.REVIEW, self.owner.confirm_reset,
                            self.root, self.view, review,
                            m.ResetOperation.CLEAR, now_ms=11)
        self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.close,
                            self.other_root)

    def test_stale_cleanup_cannot_revoke_new_request(self):
        a = self.owner.issue_submission(self.root, self.view, "A")
        self.owner.revoke_submission(self.root, a)
        b = self.owner.issue_submission(self.root, self.view, "B")
        self.assertFalse(self.owner.revoke_submission(self.root, a))
        self.owner.claim_submission(self.root, self.view, b)
        self.owner.commit_submission(self.root, self.view, b)
        self.assertEqual(self.owner.snapshot.entries[0].payload, "B")


class ReentrantFaultTests(SessionFixture):
    def test_navigation_during_input_validation_prevents_old_commit(self):
        original = m.validate_offline_text
        def nested(text):
            self.view = self.owner.activate_view(self.root, object())
            return original(text)
        old_view = self.view
        with mock.patch.object(m, "validate_offline_text", side_effect=nested):
            self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.issue_submission,
                                self.root, old_view, "A")
        self.assertEqual(self.owner.snapshot.entries, ())
        self.send("successor B")
        self.assertEqual(self.owner.snapshot.entries[0].payload, "successor B")

    def test_reentrant_commit_cannot_revoke_successor_request(self):
        a = self.owner.issue_submission(self.root, self.view, "A")
        old_view = self.view
        self.owner.claim_submission(self.root, old_view, a)
        original = m.validate_offline_text
        box = {}
        def nested(text):
            # A genuine navigation destroys the old owner/view and retires
            # A's busy operation; only then can fresh view B issue its ticket.
            self.view = self.owner.activate_view(self.root, object())
            with mock.patch.object(m, "validate_offline_text", original):
                box["b"] = self.owner.issue_submission(self.root, self.view, "B")
            return original(text)
        with mock.patch.object(m, "validate_offline_text", side_effect=nested):
            self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.commit_submission,
                                self.root, old_view, a)
        # A's exception cleanup must not consume successor B.
        self.assertIs(self.owner.active_submission_state, m.SubmissionState.ISSUED)
        self.owner.claim_submission(self.root, self.view, box["b"])
        self.owner.commit_submission(self.root, self.view, box["b"])
        self.assertEqual(self.owner.snapshot.entries[0].payload, "B")

    def test_validation_exception_keeps_transcript_unchanged(self):
        original = m.validate_offline_text
        with mock.patch.object(m, "validate_offline_text",
                               side_effect=RuntimeError("injected")):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                self.send("A")
        self.assertEqual(self.owner.snapshot.entries, ())
        self.assertIsNone(self.owner.active_submission_state)
        self.send("B")
        self.assertEqual(len(self.owner.snapshot.entries), 2)

    def test_close_during_commit_validation_does_not_publish(self):
        a = self.owner.issue_submission(self.root, self.view, "A")
        self.owner.claim_submission(self.root, self.view, a)
        original = m.validate_offline_text
        def nested(text):
            self.owner.close(self.root)
            return original(text)
        with mock.patch.object(m, "validate_offline_text", side_effect=nested):
            self.assert_refusal(m.RefusalCode.AUTHORITY, self.owner.commit_submission,
                                self.root, self.view, a)
        self.assertTrue(self.owner.snapshot.closed)
        self.assertEqual(self.owner.snapshot.entries, ())


if __name__ == "__main__":
    unittest.main()
