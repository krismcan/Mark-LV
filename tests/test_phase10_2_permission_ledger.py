"""Phase 10.2 fake-only permission state machine: negative/security tests."""
import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import pickle
import threading
import unittest

from nayeon.perception.contracts import (
    ObservationRequest, ObservationSource, ObservationPurpose, RedactionClaim,
    ObservationCandidate, AssessmentCode, assess_observation,
)
from nayeon.perception.permissions import (
    MAX_SYNTHETIC_TTL_MS, SyntheticPermissionDenied,
    SyntheticPermissionModel, SyntheticState,
)

TARGET = "a" * 32
OTHER = "b" * 32


class FakeClock:
    def __init__(self, now=1000):
        self.value = now

    def __call__(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class SyntheticPermissionTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.model = SyntheticPermissionModel(fake_monotonic_ms=self.clock)
        self.request = ObservationRequest(
            "req-001", "session-001",
            ObservationSource.SCREEN, ObservationPurpose.VERIFY_RESULT)
        self.model.fake_open_session(self.request.session_id)
        self.model.fake_bind_target(self.request.source, TARGET)

    def approval(self, request=None, target=TARGET, max_ttl=250):
        req = self.request if request is None else request
        policy = self.model.fake_policy_allow(req, target)
        return self.model.fake_user_confirm(
            policy, req, target, maximum_ttl_ms=max_ttl)

    def issue(self, ttl=100, request=None, target=TARGET, max_ttl=250):
        req = self.request if request is None else request
        return self.model.issue(
            self.approval(req, target, max_ttl), req, target, ttl_ms=ttl)

    def test_one_use_success_is_fake_marker_not_capture(self):
        handle = self.issue()
        self.assertEqual(self.model.synthetic_state(handle), SyntheticState.ISSUED)
        lease = self.model.begin(handle, self.request, TARGET)
        self.assertTrue(self.model.validate_active(lease, self.request, TARGET))
        self.assertTrue(self.model.complete(lease, self.request, TARGET))
        self.assertEqual(self.model.synthetic_state(handle), SyntheticState.USED)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.begin(handle, self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(lease, self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.issue()

    def test_request_alone_and_forged_handles_do_not_grant(self):
        bogus = object()
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(bogus, self.request, TARGET, ttl_ms=50)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.begin(bogus, self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.validate_active(bogus, self.request, TARGET)
        other = SyntheticPermissionModel(fake_monotonic_ms=self.clock)
        h = self.issue()
        with self.assertRaises(SyntheticPermissionDenied):
            other.begin(h, self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            other.synthetic_state(h)

    def test_wrong_session_request_source_purpose_target_all_denied(self):
        handle = self.issue()
        wrong = (
            replace(self.request, session_id="session-002"),
            replace(self.request, request_id="req-002"),
            replace(self.request, source=ObservationSource.CAMERA),
            replace(self.request, purpose=ObservationPurpose.DESCRIBE_CONTEXT),
        )
        for request in wrong:
            with self.subTest(request=request), self.assertRaises(SyntheticPermissionDenied):
                self.model.begin(handle, request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.begin(handle, self.request, OTHER)
        self.assertEqual(self.model.synthetic_state(handle), SyntheticState.ISSUED)
        lease = self.model.begin(handle, self.request, TARGET)
        for request in wrong:
            with self.subTest(request=request), self.assertRaises(SyntheticPermissionDenied):
                self.model.complete(lease, request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(lease, self.request, OTHER)
        self.assertTrue(self.model.complete(lease, self.request, TARGET))

    def test_fake_policy_approval_is_burned_on_wrong_scope(self):
        approve = self.approval()
        wrong = replace(self.request, purpose=ObservationPurpose.DESCRIBE_CONTEXT)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, wrong, TARGET, ttl_ms=50)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, self.request, TARGET, ttl_ms=50)
        approve = self.approval()
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, self.request, OTHER, ttl_ms=50)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, self.request, TARGET, ttl_ms=50)

    def test_fake_confirmation_consumes_exact_fake_policy_once(self):
        policy = self.model.fake_policy_allow(self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.fake_user_confirm(
                policy, replace(self.request, request_id="wrong"),
                TARGET, maximum_ttl_ms=100)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.fake_user_confirm(
                policy, self.request, TARGET, maximum_ttl_ms=100)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.fake_user_confirm(
                object(), self.request, TARGET, maximum_ttl_ms=100)

    def test_ttl_bounds_and_approval_ceiling(self):
        for i, bad in enumerate((0, -1, True, False, 1.0, None,
                                  MAX_SYNTHETIC_TTL_MS + 1)):
            with self.subTest(ttl=bad):
                request = replace(self.request, request_id=f"req-bad-ttl-{i}")
                approve = self.approval(request)
                with self.assertRaises(SyntheticPermissionDenied):
                    self.model.issue(approve, request, TARGET, ttl_ms=bad)
        approve = self.approval(max_ttl=70)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, self.request, TARGET, ttl_ms=71)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, self.request, TARGET, ttl_ms=70)
        # A valid scoped approval reserves the request ID even when its TTL
        # is later rejected. A new request ID is mandatory.
        with self.assertRaises(SyntheticPermissionDenied):
            self.issue(ttl=70)
        fresh = replace(self.request, request_id="req-new")
        self.assertEqual(self.model.synthetic_state(self.issue(ttl=70, request=fresh)), SyntheticState.ISSUED)

    def test_expiry_equality_and_no_replay_active(self):
        h = self.issue(ttl=100)
        self.clock.value = 1099
        l = self.model.begin(h, self.request, TARGET)
        self.clock.value = 1100
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(l, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.EXPIRED)
        self.assertFalse(self.model.revoke(h))
        with self.assertRaises(SyntheticPermissionDenied):
            self.issue()

    def test_expiry_before_begin(self):
        h = self.issue(ttl=5)
        self.clock.value = 1005
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.begin(h, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.EXPIRED)

    def test_clock_rollback_closes_entire_model(self):
        h = self.issue()
        self.clock.value = 1001
        l = self.model.begin(h, self.request, TARGET)
        self.clock.value = 1000
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.validate_active(l, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.CLOSED)
        with self.assertRaises(SyntheticPermissionDenied):
            self.issue()

    def test_invalid_clock_and_exception_close(self):
        for bad in (True, -1, 1.0, None, "1001", 2**53, RuntimeError("secret-window-title")):
            with self.subTest(bad=repr(bad)):
                clock = FakeClock()
                m = SyntheticPermissionModel(fake_monotonic_ms=clock)
                m.fake_open_session("S1")
                m.fake_bind_target(ObservationSource.SCREEN, TARGET)
                q = replace(self.request, session_id="S1")
                p = m.fake_policy_allow(q, TARGET)
                event = m.fake_user_confirm(p, q, TARGET, maximum_ttl_ms=10)
                clock.value = bad
                with self.assertRaises(SyntheticPermissionDenied) as cm:
                    m.issue(event, q, TARGET, ttl_ms=5)
                self.assertNotIn("secret-window-title", str(cm.exception))
                with self.assertRaises(SyntheticPermissionDenied):
                    m.fake_policy_allow(q, TARGET)

    def test_session_reopen_original_id_invalidates_lease(self):
        h = self.issue()
        l = self.model.begin(h, self.request, TARGET)
        self.model.fake_end_session("session-001")
        self.model.fake_open_session("session-001")
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(l, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.CANCELLED)

    def test_target_replacement_original_id_invalidates_lease(self):
        h = self.issue()
        l = self.model.begin(h, self.request, TARGET)
        self.model.fake_replace_target(ObservationSource.SCREEN, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(l, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.CANCELLED)

    def test_approval_epoch_stale_after_target_swap_and_session_change(self):
        approval = self.approval()
        self.model.fake_replace_target(ObservationSource.SCREEN, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approval, self.request, TARGET, ttl_ms=50)
        approval = self.approval()
        self.model.fake_end_session("session-001")
        self.model.fake_open_session("session-001")
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approval, self.request, TARGET, ttl_ms=50)

    def test_cancellation_fault_and_close_terminal(self):
        h = self.issue()
        l = self.model.begin(h, self.request, TARGET)
        self.assertTrue(self.model.cancel(l))
        self.assertFalse(self.model.cancel(l))
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(l, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.CANCELLED)
        self.model.close()
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.fake_open_session("new")

    def test_restart_has_no_persistence_or_authority(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        reboot = SyntheticPermissionModel(fake_monotonic_ms=self.clock)
        reboot.fake_open_session("session-001")
        reboot.fake_bind_target(ObservationSource.SCREEN, TARGET)
        for handle in (h, lease):
            with self.subTest(handle=type(handle).__name__), self.assertRaises(SyntheticPermissionDenied):
                reboot.begin(handle, self.request, TARGET)
        self.model.close()
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.CLOSED)

    def test_handles_do_not_repr_ids_or_pickle(self):
        h = self.issue()
        self.assertNotIn("req-001", repr(h))
        self.assertNotIn("session-001", repr(h))
        self.assertNotIn(TARGET, repr(h))
        with self.assertRaises(TypeError):
            pickle.dumps(h)
        with self.assertRaises(SyntheticPermissionDenied) as cm:
            self.model.begin(h, self.request, OTHER)
        self.assertEqual(str(cm.exception), "Synthetic permission refused")

    def test_concurrent_begin_one_winner(self):
        h = self.issue()
        barrier = threading.Barrier(8)
        def attempt(_):
            barrier.wait(timeout=3)
            try:
                return self.model.begin(h, self.request, TARGET)
            except SyntheticPermissionDenied:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            leases = list(pool.map(attempt, range(8)))
        self.assertEqual(sum(x is not None for x in leases), 1)

    def test_concurrent_duplicate_approval_single_issue(self):
        approve = self.approval()
        barrier = threading.Barrier(8)
        def attempt(_):
            barrier.wait(timeout=3)
            try:
                return self.model.issue(approve, self.request, TARGET, ttl_ms=50)
            except SyntheticPermissionDenied:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            grants = list(pool.map(attempt, range(8)))
        self.assertEqual(sum(x is not None for x in grants), 1)

    def test_revoke_between_prevalidation_and_final_completion_denies(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        self.model.validate_active(lease, self.request, TARGET)
        self.assertTrue(self.model.revoke(h))
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(lease, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.REVOKED)

    def test_concurrent_revoke_and_complete_serialization(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        barrier = threading.Barrier(2)
        def finish():
            barrier.wait(timeout=3)
            try:
                return self.model.complete(lease, self.request, TARGET)
            except SyntheticPermissionDenied:
                return False
        def revoke():
            barrier.wait(timeout=3)
            return self.model.revoke(h)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(finish)
            b = pool.submit(revoke)
            completed, revoked = a.result(), b.result()
        self.assertNotEqual(completed, revoked)
        self.assertIn(self.model.synthetic_state(h), (SyntheticState.USED, SyntheticState.REVOKED))
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(lease, self.request, TARGET)

    def test_phase10_1_candidate_never_consents_or_grants(self):
        evidence = ObservationCandidate(
            "obs-1", self.request.request_id, self.request.session_id,
            ObservationSource.SCREEN, ObservationPurpose.VERIFY_RESULT,
            1000, "f" * 64, RedactionClaim.REDACTED, 1920, 1080)
        outcome = assess_observation(self.request, evidence, now_ms=1001)
        self.assertEqual(outcome.code, AssessmentCode.CANDIDATE)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(outcome, self.request, TARGET, ttl_ms=10)

    def test_replay_same_request_id_in_new_session_denied(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        self.assertTrue(self.model.complete(lease, self.request, TARGET))
        self.model.fake_open_session("session-new")
        other = replace(self.request, session_id="session-new")
        with self.assertRaises(SyntheticPermissionDenied):
            self.issue(request=other)

    def test_reentrant_clock_cannot_issue_duplicate_request(self):
        two = self.approval()
        one = self.approval()
        outcomes = []
        flag = [False]
        def reenter():
            if not flag[0]:
                flag[0] = True
                try:
                    outcomes.append(self.model.issue(
                        two, self.request, TARGET, ttl_ms=30))
                except SyntheticPermissionDenied:
                    outcomes.append(None)
            return 1000
        self.clock.__dict__["fallback"] = 1000
        self.model._clock = reenter  # Synthetic fixture hostile callback
        outer = self.model.issue(one, self.request, TARGET, ttl_ms=30)
        self.assertIsNone(outcomes[0])
        self.assertEqual(self.model.synthetic_state(outer), SyntheticState.ISSUED)

    def test_clock_callback_close_or_target_swap_aborts_outer_issue(self):
        for transition in ("close", "target"):
            with self.subTest(transition=transition):
                m = SyntheticPermissionModel(fake_monotonic_ms=lambda: 1000)
                m.fake_open_session("session-001")
                m.fake_bind_target(ObservationSource.SCREEN, TARGET)
                policy = m.fake_policy_allow(self.request, TARGET)
                ev = m.fake_user_confirm(policy, self.request, TARGET,
                                         maximum_ttl_ms=50)
                def disrupt():
                    if transition == "close":
                        m.close()
                    else:
                        m.fake_replace_target(ObservationSource.SCREEN, TARGET)
                    return 1000
                m._clock = disrupt
                with self.assertRaises(SyntheticPermissionDenied):
                    m.issue(ev, self.request, TARGET, ttl_ms=20)
                self.assertEqual(len(m._grants), 0)

    def test_duplicate_valid_approvals_one_request_one_winner(self):
        events = [self.approval(), self.approval()]
        barrier = threading.Barrier(2)
        def issue(event):
            barrier.wait(timeout=3)
            try:
                return self.model.issue(event, self.request, TARGET, ttl_ms=10)
            except SyntheticPermissionDenied:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            granted = list(pool.map(issue, events))
        self.assertEqual(sum(h is not None for h in granted), 1)

    def test_cross_registry_approval_and_lease_rejected_at_consumer(self):
        fake = SyntheticPermissionModel(fake_monotonic_ms=self.clock)
        fake.fake_open_session("session-001")
        fake.fake_bind_target(ObservationSource.SCREEN, TARGET)
        policy = fake.fake_policy_allow(self.request, TARGET)
        approve = fake.fake_user_confirm(
            policy, self.request, TARGET, maximum_ttl_ms=100)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(approve, self.request, TARGET, ttl_ms=50)
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        for operation in (fake.validate_active, fake.complete):
            with self.subTest(op=operation.__name__), self.assertRaises(SyntheticPermissionDenied):
                operation(lease, self.request, TARGET)

    def test_fake_approval_cross_source_purpose_and_session_scope(self):
        approve = self.approval()
        mismatches = [
            replace(self.request, source=ObservationSource.CAMERA),
            replace(self.request, purpose=ObservationPurpose.DESCRIBE_CONTEXT),
            replace(self.request, session_id="different"),
            replace(self.request, request_id="different"),
        ]
        for altered in mismatches:
            approve = self.approval()
            with self.subTest(req=altered), self.assertRaises(SyntheticPermissionDenied):
                self.model.issue(approve, altered, TARGET, ttl_ms=25)
        # Valid scope and request have not been reserved by forged attempts.
        self.assertEqual(self.model.synthetic_state(self.issue(ttl=25)), SyntheticState.ISSUED)

    def test_issue_does_not_reuse_id_after_failed_valid_approval(self):
        event = self.approval(max_ttl=10)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.issue(event, self.request, TARGET, ttl_ms=11)
        with self.assertRaises(SyntheticPermissionDenied):
            self.issue(ttl=10)

    def test_invalid_confirmation_event_does_not_mint_permission(self):
        for event in (None, True, False, "fake", object()):
            with self.subTest(event=repr(event)), self.assertRaises(SyntheticPermissionDenied):
                self.model.fake_user_confirm(
                    event, self.request, TARGET, maximum_ttl_ms=10)

    def test_concurrent_completion_exactly_once(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        barrier = threading.Barrier(2)
        def complete(_):
            barrier.wait(timeout=3)
            try:
                return self.model.complete(lease, self.request, TARGET)
            except SyntheticPermissionDenied:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcome = list(pool.map(complete, range(2)))
        self.assertEqual(sorted(outcome), [False, True])

    def test_begin_revoke_race_is_linearizable(self):
        h = self.issue()
        barrier = threading.Barrier(2)
        def begin():
            barrier.wait(timeout=3)
            try:
                return self.model.begin(h, self.request, TARGET)
            except SyntheticPermissionDenied:
                return None
        def revoke():
            barrier.wait(timeout=3)
            return self.model.revoke(h)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result_begin = pool.submit(begin)
            result_revoke = pool.submit(revoke)
            lease, revoked = result_begin.result(), result_revoke.result()
        self.assertTrue(revoked)
        if lease is not None:
            with self.assertRaises(SyntheticPermissionDenied):
                self.model.complete(lease, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.REVOKED)

    def test_close_completion_race_has_no_reusable_grant(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        barrier = threading.Barrier(2)
        def finish():
            barrier.wait(timeout=3)
            try:
                return self.model.complete(lease, self.request, TARGET)
            except SyntheticPermissionDenied:
                return False
        def close():
            barrier.wait(timeout=3)
            self.model.close()
            return True
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(finish)
            b=pool.submit(close)
            completed, closed = a.result(), b.result()
        self.assertTrue(closed)
        self.assertIn(self.model.synthetic_state(h), (SyntheticState.USED, SyntheticState.CLOSED))
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(lease, self.request, TARGET)

    def test_session_termination_race_vs_completion(self):
        h = self.issue()
        lease = self.model.begin(h, self.request, TARGET)
        barrier = threading.Barrier(2)
        def finish():
            barrier.wait(timeout=3)
            try:
                return self.model.complete(lease, self.request, TARGET)
            except SyntheticPermissionDenied:
                return False
        def end():
            barrier.wait(timeout=3)
            self.model.fake_end_session("session-001")
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(finish)
            b=pool.submit(end)
            completed=a.result()
            b.result()
        self.assertEqual(self.model.synthetic_state(h),
                         SyntheticState.USED if completed else SyntheticState.CANCELLED)

    def test_orphan_active_expires_after_synthetic_pause(self):
        h = self.issue(ttl=100)
        lease = self.model.begin(h, self.request, TARGET)
        self.clock.value += 100
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.validate_active(lease, self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.complete(lease, self.request, TARGET)
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.EXPIRED)

    def test_clock_failure_invalidates_multiple_outstanding_grants(self):
        h = self.issue(ttl=200)
        request2 = replace(self.request, request_id="req-second")
        h2 = self.issue(request=request2, ttl=200)
        lease = self.model.begin(h, self.request, TARGET)
        self.clock.value = ValueError("PRIVATE-SECRET")
        with self.assertRaises(SyntheticPermissionDenied) as failure:
            self.model.validate_active(lease, self.request, TARGET)
        self.assertNotIn("PRIVATE-SECRET", str(failure.exception))
        self.assertEqual(self.model.synthetic_state(h), SyntheticState.CLOSED)
        self.assertEqual(self.model.synthetic_state(h2), SyntheticState.CLOSED)

    def test_monotonic_expiry_addition_overflow_closes(self):
        clock = FakeClock(2**53 - 7)
        model = SyntheticPermissionModel(fake_monotonic_ms=clock)
        model.fake_open_session(self.request.session_id)
        model.fake_bind_target(ObservationSource.SCREEN, TARGET)
        p = model.fake_policy_allow(self.request, TARGET)
        a = model.fake_user_confirm(p, self.request, TARGET, maximum_ttl_ms=20)
        with self.assertRaises(SyntheticPermissionDenied):
            model.issue(a, self.request, TARGET, ttl_ms=20)
        with self.assertRaises(SyntheticPermissionDenied):
            model.fake_policy_allow(self.request, TARGET)

    def test_bounded_fake_registry_capacity_without_tombstone_eviction(self):
        for i in range(256):
            self.model.fake_policy_allow(self.request, TARGET)
        with self.assertRaises(SyntheticPermissionDenied):
            self.model.fake_policy_allow(self.request, TARGET)
        self.assertEqual(len(self.model._policy), 256)
        self.model.close()
        self.assertEqual(len(self.model._policy), 0)

    def test_clock_callback_cannot_overwrite_terminal_state(self):
        for terminal in ("revoke", "cancel", "close"):
            for initially_active in (False, True):
                with self.subTest(terminal=terminal, initially_active=initially_active):
                    clock = FakeClock()
                    m = SyntheticPermissionModel(fake_monotonic_ms=clock)
                    m.fake_open_session(self.request.session_id)
                    m.fake_bind_target(self.request.source, TARGET)
                    policy = m.fake_policy_allow(self.request, TARGET)
                    approval = m.fake_user_confirm(
                        policy, self.request, TARGET, maximum_ttl_ms=100)
                    h = m.issue(approval, self.request, TARGET, ttl_ms=100)
                    if initially_active:
                        m.begin(h, self.request, TARGET)
                    first = [True]
                    def disrupt():
                        if first[0]:
                            first[0] = False
                            if terminal == "revoke":
                                m.revoke(h)
                            elif terminal == "cancel":
                                m.cancel(h)
                            else:
                                m.close()
                        return 1100
                    m._clock = disrupt
                    expected = {
                        "revoke": SyntheticState.REVOKED,
                        "cancel": SyntheticState.CANCELLED,
                        "close": SyntheticState.CLOSED,
                    }[terminal]
                    self.assertEqual(m.synthetic_state(h), expected)
                    self.assertEqual(m.synthetic_state(h), expected)

    def test_new_approval_replay_denied_after_all_terminal_states(self):
        for terminal in ("used", "revoked", "cancelled", "expired"):
            with self.subTest(terminal=terminal):
                clock = FakeClock()
                m = SyntheticPermissionModel(fake_monotonic_ms=clock)
                m.fake_open_session(self.request.session_id)
                m.fake_bind_target(self.request.source, TARGET)
                def approval():
                    policy = m.fake_policy_allow(self.request, TARGET)
                    return m.fake_user_confirm(
                        policy, self.request, TARGET, maximum_ttl_ms=100)
                h = m.issue(approval(), self.request, TARGET, ttl_ms=100)
                if terminal == "used":
                    lease = m.begin(h, self.request, TARGET)
                    m.complete(lease, self.request, TARGET)
                elif terminal == "revoked":
                    self.assertTrue(m.revoke(h))
                elif terminal == "cancelled":
                    self.assertTrue(m.cancel(h))
                else:
                    clock.value=1100
                    self.assertEqual(m.synthetic_state(h), SyntheticState.EXPIRED)
                with self.assertRaises(SyntheticPermissionDenied):
                    m.issue(approval(), self.request, TARGET, ttl_ms=40)

    def test_import_contracts_no_os_capture_network_provider_file_writes(self):
        root = Path(__file__).resolve().parents[1] / "nayeon" / "perception"
        text = (root / "permissions.py").read_text(encoding="utf-8")
        imports = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                imports.update(item.name for item in node.names)
            if isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertEqual(imports, {
            "__future__", "dataclasses", "enum", "re", "threading", "time",
            "typing", "contracts"})
        forbidden_direct = {"open", "exec", "eval", "compile", "__import__"}
        forbidden_methods = {
            "write_text", "write_bytes", "unlink", "mkdir", "rmdir", "remove",
            "write", "send", "recv", "connect", "popen", "start", "capture",
        }
        def unsafe_calls(source):
            findings = set()
            for node in ast.walk(ast.parse(source)):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_direct:
                    findings.add(node.func.id)
                if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_methods:
                    findings.add(node.func.attr)
            return findings
        self.assertEqual(unsafe_calls(text), set())
        # Causal negative and safe-positive: identifier substrings don't prove
        # filesystem/network access, but actual AST calls do.
        self.assertEqual(unsafe_calls("def t(x):\n    x._must_open()\n    return x._issued_requests.get('a')\n"), set())
        self.assertEqual(unsafe_calls("def t():\n    open('secret', 'w')\n"), {"open"})
        self.assertEqual(unsafe_calls("def t(p):\n    p.write_bytes(b'x')\n"), {"write_bytes"})


if __name__ == "__main__":
    unittest.main()
