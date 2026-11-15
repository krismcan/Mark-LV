"""P244 synthetic proofs plus all 122 P243 focused tests. No original method run."""
from __future__ import annotations

import argparse
import ast
import copy
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

import p244_three_timeout_immutable_runner as p

ROOT = Path(__file__).resolve().parents[1]
MODULES = p.load_dependencies(ROOT)  # Authenticate inherited bytes before imports.
import p243_g1_older_seal_batch_selftest as prior

H = MODULES["p238_g1_immutable_batch_candidate"]
ORIGINAL = MODULES["p234_windows_finegrain_diagnostic"]
RUN = "1" * 32
PRIOR_CLASSES = (
    prior.inherited_batch.CandidateTests, prior.inherited_progress.ProgressTests,
    prior.inherited_equality.WitnessTests, prior.inherited_equality.GuardTests,
    prior.SourceProofTests, prior.TransportTests, prior.LifecycleTests,
)


def completed(case, callbacks=None, failed=0):
    events = []
    counts = p.zeros()

    def emit(stage):
        events.append(dict(counts, schema=244, binding=p.binding(RUN, case),
                           seq=len(events) + 1, stage=stage, seconds=len(events) / 100))

    for stage in p.STAGES[:5]:
        emit(stage)
    counts["validated_reads"] = 1
    for index in range(p.case_spec(case)[2] if callbacks is None else callbacks):
        counts["subtests_completed"] += 1
        counts["subtests_failed"] += int(index < failed)
        emit("running")
    emit("test_finished")
    emit("postflight_complete")
    return events


def encode(events):
    return b"".join(json.dumps(event, sort_keys=True).encode() + b"\n" for event in events)


def process(code=0):
    return {"tree_cleanup": "JOB_EMPTY_CONFIRMED", "aborted": False,
            "timed_out": False, "actual_process_exit": code,
            "residual_descendants_after_root_exit": False}


def result(case, **changes):
    value = {"assigned": [p.case_spec(case)[0]], "tests_run": 1,
             "original_unittest_exit": 0, "failures": [], "errors": [],
             "skips": [], "expected_failures": [], "unexpected_successes": []}
    value.update(changes)
    return value


def journal(case):
    return [{"event": event, "id": p.case_spec(case)[0]} for event in ("start", "stop")]


class CaseTests(unittest.TestCase):
    def test_three_exact_original_ids_and_reviewed_counts(self):
        self.assertEqual(tuple(p.CASES), ("g2", "g3", "g6"))
        self.assertEqual([p.case_spec(case)[2:] for case in p.CASES],
                         [(24, 24, 0), (24, 24, 0), (20, 40, 1)])
        expected = (
            "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests."
            "test_raw_git_rename_status_blob_modes_counts_and_worktree_refused",
            "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests."
            "test_unknown_ignored_alias_and_index_flags_refused_in_every_state",
            "tests.test_phase_834_scope_integrity.Phase834CandidateTests."
            "test_stale_each_candidate_pin_and_disk_mutation_after_positive",
        )
        self.assertEqual(tuple(spec[0] for spec in p.CASES.values()), expected)

    def test_unknown_alias_type_and_original_test_id_are_not_case_values(self):
        for value in (None, True, 2, "G2", "g1", "g2 ", "g2,g3", p.case_spec("g2")[0]):
            with self.subTest(value=value), self.assertRaisesRegex(RuntimeError, "CASE_ENUM"):
                p.case_spec(value)

    def test_case_table_is_immutable(self):
        with self.assertRaises(TypeError):
            p.CASES["g2"] = p.case_spec("g3")

    def test_selected_method_is_bound_to_frozen_bytes_and_hook_free_inventory(self):
        for case in p.CASES:
            test_id, name = p.case_spec(case)[:2]
            raw = (ROOT / "tests" / (name + ".py")).read_bytes()
            proof = p.selected_method(raw, case)
            self.assertEqual(proof["test_id"], test_id)
            self.assertEqual(proof["source_sha256"], p.sha(raw))
            witness = {"hook_free_methods": {"synthetic": [test_id]}}
            self.assertEqual(p.source_selection(ROOT, case, witness), proof)
            with self.assertRaisesRegex(RuntimeError, "METHOD_SOURCE_PIN"):
                p.selected_method(raw + b"tamper", case)
            with self.assertRaisesRegex(RuntimeError, "ORIGINAL_HOOK_FREE_SELECTION"):
                p.source_selection(ROOT, case, {"hook_free_methods": {}})

    def test_new_834_source_pin_and_inherited_p243_pins(self):
        self.assertEqual(p.SOURCE_PINS["test_phase_834_scope_integrity"],
                         "8dc69ec770ea008dff9cd13e15299a73e38044f1671fd4fe78fbe2a431ccf57a")
        self.assertEqual(p.DEPENDENCIES["p243_g1_older_seal_batch"],
                         "ea4d66242bf41fbae970f51e904805d7ebe1a1b9fc1d36e03d8c67e45dee8d30")
        self.assertEqual(p.PARENT, "c733cd29d82c5264fe64532f14c73f41c186c277")

    def test_all_131_rows_and_transport_implementation_retained(self):
        old = prior.p
        self.assertEqual(p.ROWS, old.ROWS)
        self.assertEqual(p.SPECS, old.SPECS)
        raws = {name: (ROOT / "tests" / (name + ".py")).read_bytes()
                for name in p.SOURCE_PINS}
        manifest, _, _ = p.derive_sources(raws)
        self.assertEqual(len(manifest), 131)
        self.assertEqual(dict(manifest),
                         {query: (oid, pin) for query, oid, pin in old.ROWS})
        old_tree = ast.parse((ROOT / "scripts/p243_g1_older_seal_batch.py").read_bytes())
        new_tree = ast.parse((ROOT / "scripts/p244_three_timeout_immutable_runner.py").read_bytes())
        for name in ("intercept_query", "transport", "Batch", "verify_frame", "preflight",
                     "authenticate_seals", "object_oid", "result_class", "JournalMirror"):
            before = next(node for node in old_tree.body if getattr(node, "name", None) == name)
            after = next(node for node in new_tree.body if getattr(node, "name", None) == name)
            self.assertEqual(ast.dump(before), ast.dump(after), name)

    def test_four_additions_exact_parent_and_modified_files_refused(self):
        rows = ["A\t" + path for path in p.ADDITIONS]
        p.check_delta([p.PARENT], rows)
        for parents, delta in (([prior.p.PARENT], rows), ([p.PARENT], rows[:-1]),
                               ([p.PARENT], rows + ["M\ttests/original.py"]),
                               ([p.PARENT], [row.replace("A\t", "M\t") for row in rows])):
            with self.assertRaises(RuntimeError):
                p.check_delta(parents, delta)

    def test_all_122_inherited_tests_are_selected(self):
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                                   for cls in PRIOR_CLASSES)
        self.assertEqual(suite.countTestCases(), 122)


class ProgressTests(unittest.TestCase):
    def test_exact_case_callbacks_complete_with_candidate_hold(self):
        for case in p.CASES:
            witness = p.parse_progress(encode(completed(case)), RUN, case)
            self.assertTrue(witness["records_valid"])
            self.assertTrue(witness["observation_complete"])
            self.assertEqual(p.evidence_exit(3, witness, True, case), 3)

    def test_g6_20_callbacks_are_40_negative_assertions_and_one_positive(self):
        witness = p.parse_progress(encode(completed("g6")), RUN, "g6")
        self.assertEqual(witness["safe_counts"]["subtests_completed"], 20)
        self.assertEqual(p.case_spec("g6")[3:], (40, 1))
        self.assertEqual(p.evidence_exit(3, witness, True, "g6"), 3)
        self.assertEqual(p.evidence_exit(3, witness, True, "g2"), 125)

    def test_missing_callback_refuses_candidate_pass_for_every_case(self):
        for case in p.CASES:
            for count in (0, p.case_spec(case)[2] - 1):
                witness = p.parse_progress(encode(completed(case, count)), RUN, case)
                self.assertTrue(witness["records_valid"])
                self.assertEqual(p.evidence_exit(3, witness, True, case), 125)

    def test_extra_callbacks_refused_for_every_case(self):
        for case in p.CASES:
            witness = p.parse_progress(encode(completed(case, p.case_spec(case)[2] + 1)), RUN, case)
            self.assertFalse(witness["records_valid"])
            self.assertEqual(p.evidence_exit(3, witness, True, case), 125)

    def test_failed_subtest_never_proves_candidate_pass(self):
        for case in p.CASES:
            witness = p.parse_progress(encode(completed(case, failed=1)), RUN, case)
            self.assertTrue(witness["records_valid"])
            self.assertEqual(p.evidence_exit(3, witness, True, case), 125)
            self.assertEqual(p.evidence_exit(1, witness, True, case), 1)

    def test_same_count_g2_g3_cannot_exchange_progress(self):
        self.assertNotEqual(p.binding(RUN, "g2"), p.binding(RUN, "g3"))
        witness = p.parse_progress(encode(completed("g2")), RUN, "g3")
        self.assertFalse(witness["records_valid"])

    def test_foreign_run_torn_duplicate_and_regressing_counters_refused(self):
        for case in p.CASES:
            events = completed(case)
            regressed = copy.deepcopy(events)
            regressed[6]["subtests_completed"] = 0
            raw = encode(events)
            for changed, run in ((raw, "2" * 32), (raw + b"torn", RUN),
                                 (encode(events[:6] + [events[5]] + events[6:]), RUN),
                                 (encode(regressed), RUN),
                                 (raw.replace(b'"schema": 244', b'"schema": 243'), RUN)):
                self.assertFalse(p.parse_progress(changed, run, case)["records_valid"])

    def test_original_failure_preserved_when_progress_missing_or_source_changed(self):
        for case in p.CASES:
            witness = p.parse_progress(b"", RUN, case)
            self.assertEqual(p.evidence_exit(1, witness, False, case), 1)
            self.assertEqual(p.evidence_exit(3, witness, False, case), 125)
            good = p.parse_progress(encode(completed(case)), RUN, case)
            self.assertEqual(p.evidence_exit(3, good, False, case), 125)
            self.assertEqual(p.evidence_exit(124, good, True, case), 124)

    def test_zero_immutable_reads_cannot_prove_candidate_pass(self):
        for case in p.CASES:
            events = completed(case)
            for event in events:
                event["validated_reads"] = 0
            witness = p.parse_progress(encode(events), RUN, case)
            self.assertTrue(witness["records_valid"])
            self.assertEqual(p.evidence_exit(3, witness, True, case), 125)


class OutcomeTests(unittest.TestCase):
    def test_original_classifier_used_with_exact_selected_method(self):
        for case in p.CASES:
            summary, code = p.classify(process(), result(case), journal(case), ORIGINAL, case)
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["assigned"], [p.case_spec(case)[0]])
            self.assertEqual(code, 3)

    def test_skip_expected_failure_and_unexpected_success_remain_held(self):
        for case in p.CASES:
            test_id = p.case_spec(case)[0]
            for changes, native, expected in (({"skips": [test_id]}, 0, 125),
                                              ({"expected_failures": [test_id]}, 0, 125),
                                              ({"unexpected_successes": [test_id],
                                                "original_unittest_exit": 1}, 1, 1)):
                self.assertEqual(p.classify(process(native), result(case, **changes),
                                            journal(case), ORIGINAL, case)[1], expected)

    def test_failure_after_all_g6_callbacks_is_original_failure(self):
        # Executes only a local synthetic method through the original result
        # superclass. The original P233 methods are never imported or run here.
        for fail_after_callbacks in (False, True):
            class Synthetic(unittest.TestCase):
                def test_synthetic(self):
                    for _ in range(20):
                        with self.subTest():
                            self.assertFalse(False)
                        self.assertFalse(False)  # Outside the subtest callback.
                    self.assertTrue(True)
                    if fail_after_callbacks:
                        self.fail("synthetic disk mutation assertion failure")

            with tempfile.TemporaryDirectory(prefix="p244-synthetic-") as directory:
                path = Path(directory) / "progress.jsonl"
                progress = p.Progress(path, RUN, time.monotonic(), "g6")
                for stage in p.STAGES[:4]:
                    progress.emit(stage)
                progress.counts["validated_reads"] = 1
                cls = p.result_class(ORIGINAL, progress)
                stream = io.StringIO()
                synthetic = Synthetic("test_synthetic")
                cls.journal = p.JournalMirror(stream, progress, synthetic.id())
                outcome = unittest.TextTestRunner(stream=io.StringIO(), resultclass=cls).run(
                    unittest.TestSuite([synthetic]))
                progress.emit("postflight_complete")
                progress.close()
                witness = p.parse_progress(path.read_bytes(), RUN, "g6")
            self.assertTrue(witness["records_valid"])
            self.assertEqual(witness["safe_counts"]["subtests_completed"], 20)
            self.assertEqual(witness["safe_counts"]["subtests_failed"], 0)
            native = 0 if outcome.wasSuccessful() else 1
            value = result("g6", original_unittest_exit=native,
                           failures=[p.case_spec("g6")[0]] if native else [])
            classified = p.classify(process(native), value, journal("g6"), ORIGINAL, "g6")[1]
            self.assertEqual(p.evidence_exit(classified, witness, True, "g6"),
                             1 if fail_after_callbacks else 3)

    def test_g2_g3_foreign_assignment_and_journal_refused(self):
        for assigned, events in ((result("g3"), journal("g2")),
                                 (result("g2"), journal("g3"))):
            with self.assertRaises(RuntimeError):
                p.classify(process(), assigned, events, ORIGINAL, "g2")

    def test_timeout_aborted_and_uncertain_cleanup_remain_held(self):
        for case in p.CASES:
            timed_out = dict(process(), timed_out=True)
            self.assertEqual(p.classify(timed_out, None, [], ORIGINAL, case)[1], 124)
            for changes in ({"tree_cleanup": "UNCERTAIN"}, {"aborted": True},
                            {"residual_descendants_after_root_exit": True}):
                self.assertEqual(p.classify(dict(process(), **changes), None, [],
                                            ORIGINAL, case)[1], 125)

    def test_selected_case_is_passed_to_child_with_exact_180_second_budget(self):
        for case in p.CASES:
            with tempfile.TemporaryDirectory(prefix="p244-synthetic-") as directory:
                fake, job = prior.inherited_batch.FakeProcess(), mock.Mock()
                job.active.side_effect = [1, 1, 0, 0]
                with mock.patch.object(p.subprocess, "Popen", return_value=fake) as spawn, \
                        mock.patch.object(p.time, "monotonic", side_effect=[0, 180, 181, 181, 182]):
                    record = p.contained(Path(directory), Path(directory), RUN, H, case,
                                         job_factory=lambda: job)
                command = spawn.call_args.args[0]
                self.assertEqual(command[-2:], ["--case", case])
                self.assertEqual(Path(command[2]).name, "p244_three_timeout_immutable_runner.py")
                self.assertTrue(record["timed_out"])
                self.assertEqual(record["configured_whole_child_seconds"], 180)
                self.assertEqual(record["tree_cleanup"], "JOB_EMPTY_CONFIRMED")
                job.terminate.assert_called_once()
            for seconds in (179, 181, 180.0, True):
                with self.assertRaisesRegex(RuntimeError, "ORIGINAL_BUDGET"):
                    p.contained(Path(), Path(), RUN, H, case, seconds=seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    inherited = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                                   for cls in PRIOR_CLASSES)
    inherited_count = inherited.countTestCases()
    p.require(inherited_count == 122, "ALL_122_INHERITED_TESTS")
    own = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                            for cls in (CaseTests, ProgressTests, OutcomeTests))
    own_count = own.countTestCases()
    outcome = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([inherited, own]))
    good = (outcome.wasSuccessful() and outcome.testsRun == inherited_count + own_count
            and not outcome.skipped and not outcome.expectedFailures)
    if args.report:
        H.write(args.report, {"schema": 244, "scope": "SYNTHETIC ONLY",
                             "inherited_selected": inherited_count, "p244_selected": own_count,
                             "run": outcome.testsRun, "failures": len(outcome.failures),
                             "errors": len(outcome.errors), "skips": len(outcome.skipped),
                             "pass": good, "release": "HOLD", "original_method_executed": False})
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
