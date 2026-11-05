"""Adversarial inert fixtures. UNTESTED source; no production privacy proof."""
from concurrent.futures import ThreadPoolExecutor
import copy
from dataclasses import replace
import io
import logging
import pickle
import threading
import traceback
import unittest

from nayeon.perception.contracts import ObservationRequest, ObservationSource, ObservationPurpose
from nayeon.perception.permissions import SyntheticPermissionModel, SyntheticPermissionDenied, SyntheticState
from tests import phase10_3_synthetic_provenance_fixture as fixture
from tests import phase10_3_independent_redaction_oracle as oracle

_MISSING = object()


def _request(index=0):
    return ObservationRequest("CANARY_REQ_" + str(index), "CANARY_SESSION",
                              ObservationSource.SCREEN, ObservationPurpose.VERIFY_RESULT)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = fixture.SyntheticFixtureRegistry()
        self.request = _request()
        self.target = "CANARY_TARGET"
        self.operation = fixture._Handle()

    def issue(self, request=None, **kwargs):
        return self.registry._issue(self.request if request is None else request,
                                    self.target, self.operation, **kwargs)

    def verify(self, handle, **kwargs):
        return self.registry.verify(handle, self.request, self.target, self.operation, **kwargs)

    def test_exact_receipt_once_and_no_content(self):
        for index, case in enumerate(("single", "small", "limit")):
            request = _request(index)
            handle = self.issue(request, fixture_id=case)
            self.assertIs(type(handle), fixture._Handle)
            self.assertIs(self.registry.verify(handle, request, self.target, self.operation, fixture_id=case), fixture.FixtureStatus.CONSUMED)
            self.assertIs(self.registry.verify(handle, request, self.target, self.operation, fixture_id=case), fixture.FixtureStatus.DENIED)
            record = self.registry._records[handle]
            self.assertIsNone(record.scope)
            self.assertIsNone(record.proposal)
            self.assertIs(self.registry.state(handle), fixture.FixtureStatus.CONSUMED)

    def test_foreign_forged_copied_ids_recreated_and_closed(self):
        handle = self.issue()
        other = fixture.SyntheticFixtureRegistry()
        for fake in (object(), fixture._Handle(), str(handle), None, []):
            self.assertIs(self.verify(fake), fixture.FixtureStatus.DENIED)
        self.assertIs(other.verify(handle, self.request, self.target, self.operation), fixture.FixtureStatus.DENIED)
        # Matching strings and generation numbers never establish membership.
        foreign = other._issue(self.request, self.target, self.operation)
        self.assertIs(self.verify(foreign), fixture.FixtureStatus.DENIED)
        self.assertIs(self.registry.close(), fixture.FixtureStatus.CLOSED)
        self.assertIs(self.verify(handle), fixture.FixtureStatus.DENIED)
        self.assertIs(self.issue(_request(1)), fixture.FixtureStatus.DENIED)
        self.assertIs(self.registry.state(handle), fixture.FixtureStatus.INVALIDATED)
        self.assertIsNone(self.registry._records[handle].proposal)
        restarted = fixture.SyntheticFixtureRegistry()
        self.assertIs(restarted.verify(handle, self.request, self.target, self.operation), fixture.FixtureStatus.DENIED)

    def test_all_scope_mismatches_burn_owned_receipt(self):
        changes = (
            {"request": replace(self.request, request_id="OTHER")},
            {"request": replace(self.request, session_id="OTHER")},
            {"request": replace(self.request, source=ObservationSource.CAMERA)},
            {"request": replace(self.request, purpose=ObservationPurpose.DESCRIBE_CONTEXT)},
            {"target_id": "OTHER"}, {"operation": fixture._Handle()},
            {"fixture_id": "single"}, {"policy_version": 2}, {"policy_version": True},
        )
        for change in changes:
            registry = fixture.SyntheticFixtureRegistry()
            handle = registry._issue(self.request, self.target, self.operation)
            args = dict(request=self.request, target_id=self.target, operation=self.operation)
            args.update(change)
            self.assertIs(registry.verify(handle, **args), fixture.FixtureStatus.DENIED)
            self.assertIs(registry.state(handle), fixture.FixtureStatus.INVALIDATED)
            self.assertIs(registry.verify(handle, self.request, self.target, self.operation), fixture.FixtureStatus.DENIED)

    def test_replace_cancel_and_terminal_tombstones_never_revive(self):
        handle = self.issue()
        self.assertIs(self.registry.replace_source(), fixture.FixtureStatus.READY)
        self.assertIs(self.verify(handle), fixture.FixtureStatus.DENIED)
        self.assertIs(self.registry.state(handle), fixture.FixtureStatus.INVALIDATED)
        self.assertIs(self.issue(), fixture.FixtureStatus.DENIED)
        fresh = self.issue(_request(1))
        self.assertIs(self.registry.invalidate(fresh), fixture.FixtureStatus.INVALIDATED)
        self.registry.replace_source()
        self.registry.close()
        self.assertIs(self.registry.state(fresh), fixture.FixtureStatus.INVALIDATED)
        self.assertIsNone(self.registry._records[fresh].scope)
        self.assertIsNone(self.registry._records[fresh].proposal)

    def test_consumed_and_invalidated_records_both_exhaust_cap(self):
        for consume in (True, False):
            registry = fixture.SyntheticFixtureRegistry()
            handles = []
            for i in range(fixture.MAX_RECORDS):
                request = _request(i)
                handle = registry._issue(request, self.target, self.operation)
                handles.append(handle)
                result = (registry.verify(handle, request, self.target, self.operation)
                          if consume else registry.invalidate(handle))
                self.assertIs(result, fixture.FixtureStatus.CONSUMED if consume else fixture.FixtureStatus.INVALIDATED)
            registry.replace_source()
            self.assertIs(registry._issue(_request(999), self.target, self.operation), fixture.FixtureStatus.DENIED)
            self.assertEqual(len(registry._records), fixture.MAX_RECORDS)
            self.assertTrue(all(h in registry._records for h in handles))

    def test_generation_ceiling_closes_and_invalidates(self):
        handle = self.issue()
        for _ in range(fixture.MAX_GENERATION - 1):
            self.assertIs(self.registry.replace_source(), fixture.FixtureStatus.READY)
        self.assertIs(self.registry.replace_source(), fixture.FixtureStatus.CLOSED)
        self.assertIs(self.verify(handle), fixture.FixtureStatus.DENIED)
        self.assertIs(self.registry.state(handle), fixture.FixtureStatus.INVALIDATED)

    def test_oracle_refusal_is_terminal(self):
        handle = self.issue()
        original = self.registry._records[handle].proposal
        wrong = (("SAFE_A", "SAFE_A", "SAFE_B"), ("PRIVATE_MASK", "SAFE_B", "PRIVATE_MASK"))
        self.registry._records[handle].proposal = replace(original, output=wrong)
        self.assertIs(self.verify(handle), fixture.FixtureStatus.DENIED)
        self.assertIs(self.registry.state(handle), fixture.FixtureStatus.INVALIDATED)
        self.assertIsNone(self.registry._records[handle].proposal)
        self.assertIs(self.verify(handle), fixture.FixtureStatus.DENIED)

    def test_close_vs_verify_results_correlate_with_terminal_state(self):
        for _ in range(16):
            registry = fixture.SyntheticFixtureRegistry()
            handle = registry._issue(self.request, self.target, self.operation)
            barrier = threading.Barrier(2)
            def verify():
                barrier.wait()
                return registry.verify(handle, self.request, self.target, self.operation)
            def close():
                barrier.wait()
                return registry.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(verify)
                second = pool.submit(close)
                result = first.result()
                self.assertIs(second.result(), fixture.FixtureStatus.CLOSED)
            terminal = (fixture.FixtureStatus.CONSUMED if result is fixture.FixtureStatus.CONSUMED
                        else fixture.FixtureStatus.INVALIDATED)
            self.assertIn(result, (fixture.FixtureStatus.CONSUMED, fixture.FixtureStatus.DENIED))
            self.assertIs(registry.state(handle), terminal)
            self.assertIs(registry.verify(handle, self.request, self.target, self.operation), fixture.FixtureStatus.DENIED)

    def test_repr_logs_exceptions_and_serialization_do_not_contain_canaries(self):
        handle = self.issue()
        record = self.registry._records[handle]
        values = (self.registry, handle, record, record.scope, record.proposal)
        canaries = ("CANARY_REQ", "CANARY_SESSION", "CANARY_TARGET", "SECRET_A", "SECRET_B", "SAFE_A", "SAFE_B", "PRIVATE_MASK")
        stream = io.StringIO()
        logger = logging.Logger("synthetic-private-test")
        captured = []
        class Capture(logging.Handler):
            def emit(self, entry):
                captured.append(entry)
        logger.addHandler(logging.StreamHandler(stream))
        logger.addHandler(Capture())
        for value in values:
            diagnostics = [str(value), repr(value), f"{value!r}", f"{value}"]
            logger.info("%s %r", value, value)
            for serialize in (pickle.dumps, copy.copy, copy.deepcopy):
                try:
                    serialize(value)
                except TypeError as error:
                    diagnostics += [str(error), repr(error), "".join(traceback.format_exception(error))]
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                else:
                    self.fail("Synthetic serialization unexpectedly succeeded")
            try:
                try:
                    pickle.dumps(value)
                except TypeError as denied:
                    raise RuntimeError("Synthetic refusal") from denied
            except RuntimeError as chained:
                diagnostics.append("".join(traceback.format_exception(chained)))
            for diagnostic in diagnostics:
                self.assertTrue(all(token not in diagnostic for token in canaries), "Synthetic diagnostic leak")
        for entry in captured:
            self.assertTrue(all(token not in repr(entry.args) and token not in entry.getMessage()
                                and token not in entry.msg for token in canaries), "Synthetic logging leak")
        self.assertTrue(all(token not in stream.getvalue() for token in canaries), "Synthetic log leak")
        # Malformed identifiers are refused without formatting their values.
        self.assertIs(self.registry._issue(self.request, object(), self.operation), fixture.FixtureStatus.DENIED)
        self.assertIs(self.verify(handle, fixture_id="CANARY_INPUT"), fixture.FixtureStatus.DENIED)

    def test_public_operations_produce_only_fixed_status_and_no_log_arguments(self):
        handle = self.issue()
        captured = []
        class Capture(logging.Handler):
            def emit(self, entry):
                captured.append(entry)
        root = logging.getLogger()
        handler = Capture()
        root.addHandler(handler)
        try:
            results = (self.registry.state(handle), self.verify(handle),
                       self.verify(handle), self.registry.invalidate(handle),
                       self.registry.replace_source(), self.registry.close())
        finally:
            root.removeHandler(handler)
        self.assertTrue(all(type(result) is fixture.FixtureStatus for result in results))
        self.assertEqual(captured, [], "Synthetic operations emitted diagnostics")


class OracleTests(unittest.TestCase):
    def setUp(self):
        # Hand authored here as well; no generator or oracle builder involved.
        self.cells = (("SAFE_A", "SECRET_A", "SAFE_B"), ("SECRET_B", "SAFE_B", "SECRET_A"))
        self.labels = (("SAFE", "SENSITIVE", "SAFE"), ("SENSITIVE", "SAFE", "SENSITIVE"))
        self.expected = (("SAFE_A", "PRIVATE_MASK", "SAFE_B"), ("PRIVATE_MASK", "SAFE_B", "PRIVATE_MASK"))

    def verify(self, output, source=_MISSING, labels=_MISSING):
        return oracle.verify_fixture("small", self.cells if source is _MISSING else source,
                                     self.labels if labels is _MISSING else labels, output)

    def test_complete_authored_output_only(self):
        self.assertIs(self.verify(self.expected), oracle.OracleStatus.VERIFIED)
        # Single-position mutations defeat membership-only and shifted masks.
        for row in range(2):
            for col in range(3):
                for replacement in ("SAFE_A", "SAFE_B", "PRIVATE_MASK", "SECRET_A"):
                    if replacement == self.expected[row][col]:
                        continue
                    wrong = [list(r) for r in self.expected]
                    wrong[row][col] = replacement
                    self.assertIs(self.verify(tuple(tuple(r) for r in wrong)), oracle.OracleStatus.DENIED)
        for wrong in (self.expected[::-1], tuple(r[::-1] for r in self.expected),
                      tuple(r[1:] + r[:1] for r in self.expected),
                      (("PRIVATE_MASK",) * 3,) * 2, self.cells):
            self.assertIs(self.verify(wrong), oracle.OracleStatus.DENIED)

    def test_unknown_classification_and_inconsistent_source_deny_entire_fixture(self):
        for label in ("UNKNOWN", "unknown", "SAFE_A", None, 1):
            wrong = (("SAFE", label, "SAFE"), self.labels[1])
            self.assertIs(self.verify(self.expected, labels=wrong), oracle.OracleStatus.DENIED)
        self.assertIs(self.verify(self.expected, source=self.cells[::-1]), oracle.OracleStatus.DENIED)
        self.assertIs(oracle.verify_fixture("CANARY_ID", self.cells, self.labels, self.expected), oracle.OracleStatus.DENIED)

    def test_dimensions_types_incomplete_and_extra_cells(self):
        invalid = ((), [], ((),), (("SAFE_A",),) * 17, (("SAFE_A",) * 17,),
                   (self.expected[0],), self.expected + (self.expected[0],),
                   (self.expected[0][:-1], self.expected[1]),
                   (self.expected[0] + ("PRIVATE_MASK",), self.expected[1]),
                   tuple(list(r) for r in self.expected), None, b"CANARY")
        for value in invalid:
            self.assertIs(self.verify(value), oracle.OracleStatus.DENIED)
            self.assertIs(self.verify(self.expected, source=value), oracle.OracleStatus.DENIED)
            self.assertIs(self.verify(self.expected, labels=value), oracle.OracleStatus.DENIED)


class ExistingLedgerSeparationTests(unittest.TestCase):
    """Existing ledger result is only a fake lifecycle marker, never evidence."""
    def active(self, clock):
        model = SyntheticPermissionModel(fake_monotonic_ms=clock)
        request = _request()
        target = "a" * 32
        model.fake_open_session(request.session_id)
        model.fake_bind_target(request.source, target)
        policy = model.fake_policy_allow(request, target)
        approval = model.fake_user_confirm(policy, request, target, maximum_ttl_ms=10)
        grant = model.issue(approval, request, target, ttl_ms=10)
        lease = model.begin(grant, request, target)
        return model, request, target, grant, lease

    def test_revoke_cancel_replace_expiry_and_rollback_deny_completion(self):
        for action in ("revoke", "cancel", "replace", "expiry", "rollback"):
            time = [10]
            model, request, target, grant, lease = self.active(lambda: time[0])
            if action == "revoke":
                model.revoke(grant)
            elif action == "cancel":
                model.cancel(lease)
            elif action == "replace":
                model.fake_replace_target(request.source, target)
            elif action == "expiry":
                time[0] = 20  # Equality is expired.
            else:
                time[0] = 9
            with self.assertRaises(SyntheticPermissionDenied):
                model.complete(lease, request, target)

    def test_reentrant_clock_terminal_state_preserved_and_no_combined_proof(self):
        for action, terminal in (("revoke", SyntheticState.REVOKED),
                                  ("cancel", SyntheticState.CANCELLED),
                                  ("close", SyntheticState.CLOSED)):
            callback = [None]
            def clock():
                fn, callback[0] = callback[0], None
                if fn is not None:
                    fn()
                return 10
            model, request, target, grant, lease = self.active(clock)
            callback[0] = (lambda: model.revoke(grant)) if action == "revoke" else (
                (lambda: model.cancel(lease)) if action == "cancel" else model.close)
            with self.assertRaises(SyntheticPermissionDenied):
                model.complete(lease, request, target)
            self.assertIs(model.synthetic_state(grant), terminal)
        model, request, target, grant, lease = self.active(lambda: 10)
        self.assertIs(model.complete(lease, request, target), True)
        self.assertIs(model.synthetic_state(grant), SyntheticState.USED)
        # Registry origin is still absent; complete() cannot manufacture it.
        registry = fixture.SyntheticFixtureRegistry()
        self.assertIs(registry.verify(lease, request, target, fixture._Handle()), fixture.FixtureStatus.DENIED)

    def test_concurrent_ledger_close_vs_complete_correlates_result_with_state(self):
        for _ in range(16):
            model, request, target, grant, lease = self.active(lambda: 10)
            barrier = threading.Barrier(2)
            def complete():
                barrier.wait()
                try:
                    return model.complete(lease, request, target)
                except SyntheticPermissionDenied:
                    return False
            def close():
                barrier.wait()
                model.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                done = pool.submit(complete)
                closed = pool.submit(close)
                result = done.result()
                closed.result()
            self.assertIs(model.synthetic_state(grant),
                          SyntheticState.USED if result else SyntheticState.CLOSED)
            with self.assertRaises(SyntheticPermissionDenied):
                model.complete(lease, request, target)


if __name__ == "__main__":
    unittest.main()
