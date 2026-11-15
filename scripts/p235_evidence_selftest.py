"""Synthetic stdlib P235 adversaries. No product tests, providers or credentials."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile


spec = importlib.util.spec_from_file_location(
    "p235", Path(__file__).with_name("p235_windows_evidence_reconcile.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def process(files, stem, code=0, timeout=False, cleanup="NOT_NEEDED"):
    files[stem + ".log"] = b"synthetic original process output\n"
    return {"actual_process_exit": code, "timed_out": timeout,
            "diagnostic_exit": 124 if timeout else code, "tree_cleanup": cleanup,
            "raw_log": stem + ".log", "raw_log_sha256": p.sha(files[stem + ".log"])}


def pack(path, files):
    files = dict(files)
    # Match native P234 Windows text-mode receipt line endings.
    files["SHA256SUMS.txt"] = "".join(
        p.sha(files[name]) + "  " + name + "\r\n" for name in sorted(files)
        if name != "SHA256SUMS.txt").encode("ascii")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)


def unpack(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist() if name != "SHA256SUMS.txt"}


def edit_json(path, name, edit):
    files = unpack(path)
    value = json.loads(files[name])
    edit(value)
    files[name] = p.canonical(value)
    pack(path, files)


def make_fixture(root, modes=None):
    """Independent synthetic receipts with real 3629/54/3575 cardinalities."""
    modes = modes or {}
    entries, hooks = [], {}
    for module, count in p.TARGETS.items():
        hooks[module] = []
        for index in range(count):
            tid = module + ".Synthetic.test_" + str(index).zfill(4)
            hooks[module].append(tid)
            entries.append({"id": tid, "module": module, "owner": "p234_single",
                            "group": (len(entries) // 6)})
    for index in range(3575):
        entries.append({"id": "tests.synthetic.Other.test_" + str(index).zfill(4),
                        "module": "tests.synthetic", "owner": "historical_p233_not_executed_by_p234"})
    for entry in entries:
        entry["historical_p233_shard"] = int.from_bytes(
            hashlib.sha256(entry["module"].encode()).digest()[:4], "big") % 6
    source = {"head": p.TEST_SOURCE, "hook_free_methods": hooks,
              "raw_tracked_sha256": {p.P233: p.P233_SHA},
              "historical_tags": {"synthetic-" + str(i): [format(i, "040x"), format(i + 1, "040x")]
                                  for i in range(15)}}
    identity = p.sha(p.canonical(source))
    inventory = [[entry["id"], entry["module"], entry["historical_p233_shard"]] for entry in entries]
    manifest = {"schema": "P234-v1", "run_id": p.RUN_ID, "source": source,
                "inventory_order_sha256": p.sha(("\n".join(e["id"] for e in entries) + "\n").encode()),
                "discovered": 3629, "p234_assigned": 54, "p233_assigned_not_run": 3575,
                "group_size": 6, "groups": 9, "entries": entries, "release": p.RELEASE}
    manifest_raw = p.canonical(manifest)

    def base_files():
        return {"manifest.json": manifest_raw, "discovery.json": p.canonical(inventory)}

    files = base_files()
    plan = {"release": p.RELEASE, "driver_exit": 0, "diagnostic_collection_complete": True,
            "source_identity_sha256": identity, "discovery_process": process(files, "discovery"),
            "run_id": p.RUN_ID, "manifest_sha256": p.sha(manifest_raw), "methods_executed": 0,
            "status": "INVENTORY_ONLY_NOT_A_TEST_PASS"}
    files["driver.json"] = p.canonical(plan)
    pack(root / "p234-plan-1.zip", files)
    all_methods, all_codes = [], []
    for group in range(9):
        files = base_files()
        selected = [e["id"] for e in entries if e.get("group") == group]
        driver = {"release": p.RELEASE, "run_id": p.RUN_ID, "group": group,
                  "source_identity_sha256": identity, "manifest_sha256": p.sha(manifest_raw),
                  "discovery_process": process(files, "discovery"), "assigned": selected, "methods": []}
        codes = []
        for index, tid in enumerate(selected):
            mode = modes.get((group, index), "PASS")
            stem = "single-" + str(index)
            timed_out = mode.startswith("TIMEOUT")
            incomplete = mode in {"INTERRUPTED", "INFRASTRUCTURE_ERROR"}
            blocked = mode == "SETUP_BLOCKED"
            started = not blocked and mode != "INFRASTRUCTURE_ERROR"
            completed = started and not timed_out and not incomplete
            original = 1 if mode in {"FAILURE", "ERROR", "SETUP_BLOCKED", "UNEXPECTED_SUCCESS"} else 0
            proc = process(files, stem, 1 if timed_out or incomplete else original,
                           timed_out, "UNCERTAIN" if mode == "TIMEOUT_UNCERTAIN" else
                           "TREE_TERMINATED" if timed_out else "NOT_NEEDED")
            files[stem + "-process.json"] = p.canonical(proc)
            events = [{"event": "start", "id": tid}] if started else []
            if completed:
                events.append({"event": "stop", "id": tid})
            files[stem + ".events.jsonl"] = b"".join(json.dumps(e).encode() + b"\r\n" for e in events)
            summary = {"assigned": [tid], "executed": [tid] if started else [],
                       "completed": [tid] if completed else [], "setup_blocked": [],
                       "original_unittest_exit": None, "status": "INCOMPLETE", "process": proc}
            if timed_out:
                summary["status"] = "TIMEOUT"
                code = 125 if mode == "TIMEOUT_UNCERTAIN" else 124
            elif incomplete:
                code = 125
            else:
                result = {"assigned": [tid], "tests_run": int(started), "original_unittest_exit": original,
                          "failures": [tid] if mode == "FAILURE" else [],
                          "errors": ["setUpClass (" + tid.rsplit(".", 1)[0] + ")"] if blocked else
                                    [tid] if mode == "ERROR" else [],
                          "skips": [tid] if mode == "SKIP" else [],
                          "expected_failures": [tid] if mode == "EXPECTED_FAILURE" else [],
                          "unexpected_successes": [tid] if mode == "UNEXPECTED_SUCCESS" else []}
                files[stem + ".json"] = p.canonical(result)
                summary.update(original_result=result, original_unittest_exit=original,
                               setup_blocked=[tid] if blocked else [],
                               status="FAIL_OR_ERROR" if original and not blocked else mode)
                code = 1 if original or blocked else 0
            driver["methods"].append(summary)
            codes.append(code)
        driver["driver_exit"] = max(codes)
        driver["diagnostic_collection_complete"] = all(
            m["status"] not in {"TIMEOUT", "INCOMPLETE"} for m in driver["methods"])
        for field in ("executed", "completed", "setup_blocked"):
            driver[field] = [tid for m in driver["methods"] for tid in m[field]]
        all_methods.extend(driver["methods"])
        all_codes.extend(codes)
        files["driver.json"] = p.canonical(driver)
        pack(root / ("p234-group-" + str(group) + "-1.zip"), files)
    assigned = [tid for m in all_methods for tid in m["assigned"]]
    certificate = {"release": p.RELEASE, "driver_exit": max(all_codes), "coverage_complete": True,
                   "run_id": p.RUN_ID, "discovered": 3629, "assigned": assigned,
                   "historical_p233_assigned_not_executed": 3575,
                   "manifest_sha256": p.sha(manifest_raw), "methods": all_methods,
                   "diagnostic_collection_complete": all(
                       m["status"] not in {"TIMEOUT", "INCOMPLETE"} for m in all_methods)}
    for field in ("executed", "completed", "setup_blocked"):
        certificate[field] = [tid for m in all_methods for tid in m[field]]
    certificate["unexecuted"] = sorted(set(assigned) - set(certificate["executed"]))
    certificate["uncompleted"] = sorted(set(assigned) - set(certificate["completed"]))
    pack(root / "p234-certificate-HOLD-1.zip", {"coverage-certificate.json": p.canonical(certificate)})


class P235Selftest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        make_fixture(self.root)

    def assert_evidence_error(self):
        report = p.reconcile(self.root)
        self.assertEqual(report["reconciler_exit"], 125)
        self.assertFalse(report["evidence_consistent"])
        self.assertEqual(report["release_gate"], "HOLD")
        self.assertFalse(report["release_gate_passed"])
        return report

    def test_consistent_green_synthetic_still_release_hold_full_inventory(self):
        report = p.reconcile(self.root)
        self.assertTrue(report["evidence_consistent"])
        self.assertEqual(report["reconciler_exit"], 1)
        self.assertEqual(report["original_driver_exit"], 0)
        self.assertEqual(report["outcome_counts"], {"PASS": 54})
        self.assertEqual(len(report["discovery_classification"]), 3629)
        self.assertEqual(sum(e["p235_execution_classification"] == "RETAINED_NOT_EXECUTED"
                             for e in report["discovery_classification"]), 3575)
        self.assertFalse(report["full_provenance_approved"])
        self.assertFalse(report["release_gate_passed"])
        self.assertEqual(report["full_product_regressions"], "0/3")

    def test_genuine_shape_46_pass_4_bad_4_timeout_three_uncertain(self):
        modes = {(0, 1): "ERROR", (0, 2): "ERROR", (1, 3): "ERROR", (6, 3): "ERROR",
                 (1, 0): "TIMEOUT_UNCERTAIN", (2, 3): "TIMEOUT",
                 (3, 0): "TIMEOUT_UNCERTAIN", (6, 5): "TIMEOUT_UNCERTAIN"}
        make_fixture(self.root, modes)
        report = p.reconcile(self.root)
        self.assertTrue(report["evidence_consistent"])
        self.assertEqual(report["original_status_counts"], {"PASS": 46, "FAIL_OR_ERROR": 4, "TIMEOUT": 4})
        self.assertEqual(report["original_driver_exit"], 125)
        self.assertEqual(report["reconciler_exit"], 125)
        self.assertTrue(report["coverage_complete"])
        self.assertFalse(report["diagnostic_collection_complete"])
        self.assertEqual((len(report["unexecuted"]), len(report["uncompleted"])), (0, 4))
        self.assertIn("PROCESS_TREE_CLEANUP_UNCERTAIN", report["unresolved_holds"])

    def test_distinct_original_failure_error_and_setup_block(self):
        make_fixture(self.root, {(0, 0): "FAILURE", (0, 1): "ERROR", (0, 2): "SETUP_BLOCKED",
                                 (0, 3): "SKIP", (0, 4): "EXPECTED_FAILURE", (0, 5): "UNEXPECTED_SUCCESS"})
        report = p.reconcile(self.root)
        self.assertTrue(report["evidence_consistent"])
        self.assertEqual(report["reconciler_exit"], 1)
        self.assertEqual([m["outcome"] for m in report["methods"][:6]],
                         ["FAILURE", "ERROR", "SETUP_BLOCKED", "SKIP", "EXPECTED_FAILURE", "UNEXPECTED_SUCCESS"])
        self.assertEqual(len(report["setup_blocked"]), 1)

    def test_interruption_and_infrastructure_preserve_125(self):
        make_fixture(self.root, {(0, 0): "INTERRUPTED", (0, 1): "INFRASTRUCTURE_ERROR"})
        report = p.reconcile(self.root)
        self.assertTrue(report["evidence_consistent"])
        self.assertEqual(report["reconciler_exit"], 125)
        self.assertEqual([m["outcome"] for m in report["methods"][:2]],
                         ["INTERRUPTED", "INFRASTRUCTURE_ERROR"])

    def test_terminated_timeout_preserves_124_and_hold(self):
        make_fixture(self.root, {(0, 0): "TIMEOUT"})
        report = p.reconcile(self.root)
        self.assertTrue(report["evidence_consistent"])
        self.assertEqual(report["reconciler_exit"], 124)
        self.assertIn("TIMEOUT_ROOT_CAUSES_OPEN", report["unresolved_holds"])

    def test_missing_group_and_ambiguous_certificate(self):
        path = self.root / "p234-group-8-1.zip"
        raw = path.read_bytes()
        path.unlink()
        self.assert_evidence_error()
        path.write_bytes(raw)
        (self.root / "p234-certificate-HOLD.zip").write_bytes(
            (self.root / "p234-certificate-HOLD-1.zip").read_bytes())
        self.assert_evidence_error()

    def test_certificate_without_attempt_suffix(self):
        (self.root / "p234-certificate-HOLD-1.zip").rename(self.root / "p234-certificate-HOLD.zip")
        self.assertTrue(p.reconcile(self.root)["evidence_consistent"])

    def test_wrong_run_and_source_role(self):
        self.assertEqual(p.reconcile(self.root, "999-1")["reconciler_exit"], 125)
        edit_json(self.root / "p234-plan-1.zip", "manifest.json",
                  lambda value: value["source"].update(head=p.CONTROLLER))
        self.assert_evidence_error()

    def test_duplicate_discovery_or_wrong_shard_or_group(self):
        path = self.root / "p234-plan-1.zip"
        original = unpack(path)
        edits = [lambda m: m["entries"].__setitem__(1, copy.deepcopy(m["entries"][0])),
                 lambda m: m["entries"][0].update(historical_p233_shard=99),
                 lambda m: m["entries"][0].update(group=8),
                 lambda m: m["source"].update(hook_free_methods={})]
        for edit in edits:
            with self.subTest(edit=edit):
                pack(path, original)
                edit_json(path, "manifest.json", edit)
                self.assert_evidence_error()

    def test_group_manifest_or_assignment_or_certificate_coverage_mismatch(self):
        group = self.root / "p234-group-0-1.zip"
        original = unpack(group)
        for name, edit in [("manifest.json", lambda m: m.update(run_id="999-1")),
                           ("driver.json", lambda d: d["assigned"].reverse())]:
            pack(group, original)
            edit_json(group, name, edit)
            self.assert_evidence_error()
        pack(group, original)
        edit_json(self.root / "p234-certificate-HOLD-1.zip", "coverage-certificate.json",
                  lambda c: c["completed"].pop())
        self.assert_evidence_error()

    def test_false_green_driver_cannot_override_original_failure(self):
        make_fixture(self.root, {(0, 0): "FAILURE"})
        edit_json(self.root / "p234-group-0-1.zip", "driver.json", lambda d: d.update(driver_exit=0))
        self.assert_evidence_error()

    def test_separate_process_receipt_exit_log_and_journal_tampering(self):
        path = self.root / "p234-group-0-1.zip"
        original = unpack(path)
        for name, raw in [("single-0.log", b"changed log"),
                          ("single-0.events.jsonl", b'{"event":"stop","id":"foreign"}\n')]:
            files = dict(original)
            files[name] = raw
            pack(path, files)  # Rehashed attacker-controlled internal receipts.
            self.assert_evidence_error()
        for edit in [lambda proc: proc.update(actual_process_exit=1),
                     lambda proc: proc.update(timed_out=1),
                     lambda proc: proc.update(tree_cleanup="UNCERTAIN")]:
            pack(path, original)
            edit_json(path, "single-0-process.json", edit)
            self.assert_evidence_error()

    def test_original_footer_tamper_and_duplicate_json_key(self):
        path = self.root / "p234-group-0-1.zip"
        original = unpack(path)
        edit_json(path, "single-0.json", lambda r: r.update(original_unittest_exit=1))
        self.assert_evidence_error()
        original["single-0.json"] = b'{"assigned":[],"assigned":[]}'
        pack(path, original)
        self.assert_evidence_error()

    def test_discovery_and_source_witness_hash_tamper(self):
        path = self.root / "p234-plan-1.zip"
        original = unpack(path)
        edit_json(path, "discovery.json", lambda rows: rows.reverse())
        self.assert_evidence_error()
        pack(path, original)
        edit_json(path, "manifest.json", lambda m: m["source"]["raw_tracked_sha256"].update(
            {p.P233: "0" * 64}))
        self.assert_evidence_error()

    def test_lifecycle_duplicates_missing_stop_and_setup_skip(self):
        tid = "tests.synthetic.C.test_one"
        proc = {"timed_out": False, "actual_process_exit": 0}
        result = {"assigned": [tid], "tests_run": 1, "original_unittest_exit": 0,
                  "failures": [], "errors": [], "skips": [], "expected_failures": [],
                  "unexpected_successes": []}
        start = {"event": "start", "id": tid}
        stop = {"event": "stop", "id": tid}
        for events in ([start, start], [stop, start], [start], [start, stop, start, stop]):
            with self.subTest(events=events), self.assertRaises(p.EvidenceError):
                p.classify(proc, result, events, tid)
        result.update(tests_run=0, skips=["setUpClass (tests.synthetic.C)"])
        summary, code, outcome = p.classify(proc, result, [], tid)
        self.assertEqual((summary["executed"], code, outcome), ([], 1, "SETUP_BLOCKED"))
        result.update(tests_run=1, skips=[], failures=[tid], errors=[tid], original_unittest_exit=1)
        _, code, outcome = p.classify(dict(proc, actual_process_exit=1), result, [start, stop], tid)
        self.assertEqual((code, outcome), (1, "FAILURE_AND_ERROR"))

    def test_receipt_tamper_missing_and_extra_inventory(self):
        path = self.root / "p234-plan-1.zip"
        original = unpack(path)
        for mutation in ("tamper", "missing", "extra"):
            with zipfile.ZipFile(path, "w") as archive:
                for name, raw in original.items():
                    archive.writestr(name, raw)
                if mutation != "missing":
                    archive.writestr("SHA256SUMS.txt", b"wrong")
                if mutation == "extra":
                    archive.writestr("unexpected.txt", b"extra")
            self.assert_evidence_error()

    def test_unsafe_zip_names_duplicates_symlink_and_compression_bomb(self):
        path = self.root / "p234-plan-1.zip"
        for name in ("../driver.json", "/driver.json", "C:/driver.json", "x\\driver.json",
                     "driver.json:stream", "folder/driver.json", "DRIVER.JSON", "driver.json\x00hidden"):
            with self.subTest(name=name), zipfile.ZipFile(path, "w") as archive:
                archive.writestr(name, b"bad")
            self.assert_evidence_error()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("driver.json", b"one")
                archive.writestr("driver.json", b"two")
        self.assert_evidence_error()
        info = zipfile.ZipInfo("driver.json")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(info, b"target")
        self.assert_evidence_error()
        pack(path, {"driver.json": b"A" * (1024 * 1024)})
        self.assert_evidence_error()

    def test_explicit_bounds_and_malformed_archive(self):
        path = self.root / "p234-plan-1.zip"
        for bound, value in (("MAX_ZIP", 10), ("MAX_MEMBER", 10), ("MAX_TOTAL", 10), ("MAX_MEMBERS", 1)):
            with self.subTest(bound=bound), mock.patch.object(p, bound, value):
                self.assert_evidence_error()
        path.write_bytes(b"corrupt ZIP")
        self.assert_evidence_error()

    def test_json_depth_and_nonfinite_values_rejected(self):
        for raw in (b"[" * 65 + b"0" + b"]" * 65, b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaises(p.EvidenceError):
                p.parse_json(raw)

    def test_optional_digests_missing_malformed_matching_and_mismatching(self):
        for raw in (None, b"invalid", b'[]', b'{"p234-plan-1.zip":"bad"}'):
            with self.subTest(raw=raw):
                report = p.reconcile(self.root, metadata_raw=raw)
                self.assertTrue(report["evidence_consistent"])
                self.assertFalse(report["full_provenance_approved"])
        digests = {path.name: "sha256:" + p.sha(path.read_bytes()).lower() for path in self.root.glob("*.zip")}
        report = p.reconcile(self.root, metadata_raw=p.canonical(digests))
        self.assertEqual(set(report["github_zip_digest_status"].values()), {"MATCH"})
        self.assertFalse(report["full_provenance_approved"])
        digests["p234-plan-1.zip"] = "0" * 64
        report = p.reconcile(self.root, metadata_raw=p.canonical(digests))
        self.assertFalse(report["evidence_consistent"])
        self.assertEqual(report["reconciler_exit"], 125)

    def test_cli_actual_exit_report_and_input_bytes_preserved(self):
        before = {path.name: p.sha(path.read_bytes()) for path in self.root.glob("*.zip")}
        output = self.root / "report.json"
        result = subprocess.run([sys.executable, "-B", str(Path(p.__file__)),
                                 "--artifacts", str(self.root), "--output", str(output)],
                                capture_output=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(output.read_bytes())
        self.assertTrue(report["evidence_consistent"])
        self.assertFalse(report["release_gate_passed"])
        self.assertFalse(output.stat().st_mode & stat.S_IWRITE)
        self.assertEqual(before, {path.name: p.sha(path.read_bytes()) for path in self.root.glob("*.zip")})
        saved = output.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(p.main(["--artifacts", str(self.root), "--output", str(output)]), 125)
        self.assertEqual(output.read_bytes(), saved)

    def test_cli_missing_input_writes_failed_report(self):
        output = self.root / "failed.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(p.main(["--artifacts", str(self.root / "missing"),
                                     "--output", str(output)]), 125)
        self.assertFalse(json.loads(output.read_bytes())["evidence_consistent"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
