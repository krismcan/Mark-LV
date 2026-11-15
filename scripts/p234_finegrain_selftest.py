"""Standard-library P234 adversaries; no original tests or source imports."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("p234", Path(__file__).with_name("p234_windows_finegrain_diagnostic.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
TID = "tests.fake.C.test_one"


def rows(count=8):
    result = []
    for index in range(count):
        module = "tests.fake" if index < 3 else "tests.other"
        shard = int.from_bytes(hashlib.sha256(module.encode()).digest()[:4], "big") % 6
        result.append([module + ".C.test_" + str(index), module, shard])
    return result


def original(code=0):
    return {"assigned": [TID], "tests_run": 1, "original_unittest_exit": code,
            "failures": [TID] if code else [], "errors": [], "skips": [],
            "expected_failures": [], "unexpected_successes": []}


EVENTS = [{"event": event, "id": TID} for event in ("start", "stop")]
FAKE = """import json, pathlib, sys, time
out, tid, mode = sys.argv[1:]
out = pathlib.Path(out)
print('RAW-FAKE-RUNNER-' + mode, flush=True)
events = out.with_suffix('.events.jsonl')
events.write_text(json.dumps({'event':'start','id':tid})+'\\n')
if mode == 'timeout': time.sleep(30)
code = 1 if mode == 'fail' else 0
events.write_text(events.read_text()+json.dumps({'event':'stop','id':tid})+'\\n')
out.write_text(json.dumps({'assigned':[tid], 'tests_run':1,
 'original_unittest_exit':code, 'failures':[tid] if code else [],
 'errors':[], 'skips':[], 'expected_failures':[], 'unexpected_successes':[]}))
sys.exit(code)
"""


class P234Selftest(unittest.TestCase):
    def test_exact_disjoint_assignment_keeps_remainder_historical(self):
        entries = p.partition(rows(), {"tests.fake": 3}, total=8, group_size=2)
        self.assertEqual([e["group"] for e in entries if "group" in e], [0, 0, 1])
        self.assertEqual(sum(e["owner"].startswith("historical") for e in entries), 5)
        self.assertEqual(len({e["id"] for e in entries}), 8)
        self.assertEqual(entries, p.partition(rows(), {"tests.fake": 3}, total=8, group_size=2))

    def test_duplicate_missing_wrong_module_wrong_shard_fail_closed(self):
        examples = [rows()[:-1], rows()[:-1] + rows()[:1]]
        wrong = rows()
        wrong[0][2] = (wrong[0][2] + 1) % 6
        examples.append(wrong)
        wrong = rows()
        wrong[0][0] = "unittest.loader._FailedTest.bad"
        examples.append(wrong)
        for example in examples:
            with self.subTest(example=example), self.assertRaises(RuntimeError):
                p.partition(example, {"tests.fake": 3}, total=8)
        with self.assertRaises(RuntimeError):
            p.partition(rows(), {"tests.fake": 4}, total=8)

    def test_fake_runner_actual_exit_and_timeout_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for mode, expected in (("pass", 0), ("fail", 1), ("timeout", 124)):
                output = folder / (mode + ".json")
                proc = p.run_process([sys.executable, "-B", "-c", FAKE, str(output), TID, mode],
                                     folder, folder, mode, .5 if mode == "timeout" else 10)
                journal = output.with_suffix(".events.jsonl")
                events = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
                result = json.loads(output.read_bytes()) if output.exists() else None
                summary, code = p.classify(proc, result, events, TID)
                self.assertEqual(code, expected)
                self.assertEqual(proc["diagnostic_exit"], expected)
                self.assertEqual(proc["raw_log_sha256"], p.sha((folder / (mode + ".log")).read_bytes()))
                if mode == "timeout":
                    self.assertEqual(summary["completed"], [])
                    self.assertIsNone(summary["original_unittest_exit"])
                else:
                    self.assertEqual(proc["actual_process_exit"], expected)
                    self.assertEqual(summary["executed"], [TID])

    def test_failure_cannot_be_green_and_footer_exit_must_match(self):
        process = {"timed_out": False, "actual_process_exit": 1}
        self.assertEqual(p.classify(process, original(1), EVENTS, TID)[1], 1)
        with self.assertRaises(RuntimeError):
            p.classify(dict(process, actual_process_exit=0), original(1), EVENTS, TID)
        self.assertEqual(p.classify(dict(process, actual_process_exit=0), None, [], TID)[1], 125)
        self.assertEqual(p.classify({"timed_out": True, "tree_cleanup": "UNCERTAIN"},
                                    None, [], TID)[1], 125)

    def test_original_error_skip_expected_and_unexpected_success(self):
        for outcome, code in (("errors", 1), ("skips", 0), ("expected_failures", 0), ("unexpected_successes", 1)):
            result = original()
            result[outcome] = [TID]
            result["original_unittest_exit"] = code
            process = {"timed_out": False, "actual_process_exit": code}
            summary, actual = p.classify(process, result, EVENTS, TID)
            self.assertEqual(actual, code)
            self.assertEqual(summary["original_result"][outcome], [TID])

    def test_setup_blocked_is_separate_from_executed_and_never_green(self):
        result = original(1)
        result.update(tests_run=0, failures=[], errors=["setUpClass (tests.fake.C)"])
        summary, code = p.classify({"timed_out": False, "actual_process_exit": 1}, result, [], TID)
        self.assertEqual((summary["executed"], summary["completed"], summary["setup_blocked"], code),
                         ([], [], [TID], 1))
        result.update(errors=[], skips=["setUpClass (tests.fake.C)"], original_unittest_exit=0)
        self.assertEqual(p.classify({"timed_out": False, "actual_process_exit": 0}, result, [], TID)[1], 1)

    def test_duplicate_foreign_missing_stop_events_fail_closed(self):
        for events in (EVENTS + EVENTS, list(reversed(EVENTS)),
                       [{"event": "start", "id": "tests.foreign.C.test_x"}], EVENTS[:1]):
            with self.subTest(events=events), self.assertRaises(RuntimeError):
                p.classify({"timed_out": False, "actual_process_exit": 0}, original(), events, TID)

    def test_hook_audit_refuses_hooks_and_nontrivial_inheritance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tests").mkdir()
            path = root / "tests/fake.py"
            with mock.patch.dict(p.TARGETS, {"tests.fake": 1}, clear=True):
                for body in ("class C(unittest.TestCase):\n def setUpClass(cls): pass\n def test_x(self): pass\n",
                             "class C(Other):\n def test_x(self): pass\n",
                             "def load_tests(*args): pass\nclass C(unittest.TestCase):\n def test_x(self): pass\n"):
                    path.write_text(body)
                    with self.assertRaises(RuntimeError):
                        p.audit_hooks(root)
                path.write_text("class C(unittest.TestCase):\n def test_x(self): pass\n")
                self.assertEqual(p.audit_hooks(root), {"tests.fake": ["tests.fake.C.test_x"]})

    def test_receipts_refuse_tamper_and_added_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            path = folder / "manifest.json"
            path.write_bytes(b"original")
            p.receipts(folder)
            p.verify_receipts(folder)
            path.write_bytes(b"tampered")
            with self.assertRaises(RuntimeError):
                p.verify_receipts(folder)
            path.write_bytes(b"original")
            (folder / "unexpected.log").write_bytes(b"extra")
            with self.assertRaises(RuntimeError):
                p.verify_receipts(folder)

    def test_missing_aggregate_artifacts_return_failure_certificate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = argparse.Namespace(output=root / "certificate", manifest=root / "missing/manifest.json",
                                      run_id="123-1", artifacts=root)
            self.assertEqual(p.aggregate(args), 125)
            report = json.loads((args.output / "coverage-certificate.json").read_bytes())
            self.assertFalse(report["coverage_complete"])

    def test_full_fake_certificate_preserves_failure_and_refuses_false_green(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
                p.TARGETS, {"tests.fake_a": 19, "tests.fake_b": 35}, clear=True):
            root = Path(temporary)
            inventory = []
            for index in range(3629):
                module = "tests.fake_a" if index < 19 else "tests.fake_b" if index < 54 else "tests.other"
                shard = int.from_bytes(hashlib.sha256(module.encode()).digest()[:4], "big") % 6
                inventory.append([module + ".C.test_" + str(index), module, shard])
            source = {"head": p.SOURCE, "hook_free_methods": {
                module: [r[0] for r in inventory if r[1] == module] for module in p.TARGETS}}
            manifest = p.make_manifest("123-1", inventory, source)
            plan = root / "p234-plan"
            plan.mkdir()
            p.write_json(plan / "manifest.json", manifest)
            identity = p.sha(p.canonical(source))
            p.write_json(plan / "driver.json", {"driver_exit": 0, "methods_executed": 0,
                                                "source_identity_sha256": identity})
            p.receipts(plan)
            for group in range(9):
                folder = root / ("p234-group-" + str(group))
                folder.mkdir()
                p.write_json(folder / "manifest.json", manifest)
                selected = [e["id"] for e in manifest["entries"] if e.get("group") == group]
                driver = {"run_id": "123-1", "group": group, "assigned": selected,
                          "methods": [], "driver_exit": 1 if group == 0 else 0,
                          "diagnostic_collection_complete": True, "source_identity_sha256": identity}
                for index, tid in enumerate(selected):
                    code = 1 if group == 0 and index == 0 else 0
                    result = original(code)
                    result.update(assigned=[tid], failures=[tid] if code else [])
                    stem = "single-" + str(index)
                    p.write_json(folder / (stem + ".json"), result)
                    events = [{"event": event, "id": tid} for event in ("start", "stop")]
                    (folder / (stem + ".events.jsonl")).write_text(
                        "".join(json.dumps(e) + "\n" for e in events), encoding="utf8")
                    raw = folder / (stem + ".log")
                    raw.write_bytes(b"fake original output\n")
                    process = {"actual_process_exit": code, "timed_out": False,
                               "diagnostic_exit": code, "raw_log": raw.name,
                               "raw_log_sha256": p.sha(raw.read_bytes())}
                    summary, _ = p.classify(process, result, events, tid)
                    driver["methods"].append(dict(summary, process=process))
                p.write_json(folder / "driver.json", driver)
                p.receipts(folder)
            args = argparse.Namespace(output=root / "certificate", manifest=plan / "manifest.json",
                                      run_id="123-1", artifacts=root)
            self.assertEqual(p.aggregate(args), 1)
            certificate = json.loads((args.output / "coverage-certificate.json").read_bytes())
            self.assertTrue(certificate["coverage_complete"])
            self.assertEqual(len(certificate["executed"]), 54)
            self.assertEqual(len(certificate["completed"]), 54)
            self.assertEqual(certificate["historical_p233_assigned_not_executed"], 3575)
            # Even with consistent recomputed receipts, a false green driver
            # must be rejected by independently reading the original result.
            group_zero = root / "p234-group-0"
            driver = json.loads((group_zero / "driver.json").read_bytes())
            driver["driver_exit"] = 0
            p.write_json(group_zero / "driver.json", driver)
            p.receipts(group_zero)
            args.output = root / "false-green-certificate"
            self.assertEqual(p.aggregate(args), 125)


if __name__ == "__main__":
    unittest.main(verbosity=2)
