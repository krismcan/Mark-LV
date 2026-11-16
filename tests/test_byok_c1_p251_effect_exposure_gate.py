"""Effect-free source/fixture tests. Production modules are never imported."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).absolute().parents[1]
SCRIPT = ROOT / "tools/byok_c1_effect_exposure_gate.py"
SPEC = importlib.util.spec_from_file_location("p251_diagnostic", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class CheckoutTests(unittest.TestCase):
    def test_exact_affirmative_exposure(self):
        report = gate._assess(ROOT)
        self.assertEqual(report["assessment"], "KNOWN_EFFECT_EXPOSURE")
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["status"], "HOLD")
        self.assertFalse(report["release_admitted"])
        sites = {(item["path"], item["kind"]): item["line"] for item in report["evidence"]}
        self.assertEqual(sites[gate.BACKEND, "native_credential_write"], 113)
        self.assertEqual(sites[gate.BACKEND, "native_credential_delete"], 120)
        self.assertEqual(sites[gate.CONTROLLER, "save_or_replace"], 181)
        self.assertEqual(sites[gate.CONTROLLER, "remove"], 175)
        self.assertEqual(sites[gate.P96, "historical_delete_callback"], 210)
        self.assertEqual(sites[gate.P96, "historical_save_replace_callback"], 212)
        self.assertTrue(all(item["matches_reviewed_snapshot"] for item in report["sources"]))
        self.assertEqual(len(report["evidence"]), len(gate.CALL_SITES) + len(gate.TEXT_SITES))

    def test_import_relationships(self):
        sources = {item["path"]: item for item in gate._assess(ROOT)["sources"]}
        imports = [item["statement"] for item in sources[gate.CONTROLLER]["imports"]]
        self.assertIn("from nayeon.secrets.windows_credential import WindowsCredentialBackend", imports)
        imports = [item["statement"] for item in sources[gate.WINDOW]["imports"]]
        self.assertTrue(any("from nayeon.brain.local_byok_user_scope import" in item for item in imports))

    def test_deterministic(self):
        self.assertEqual(gate._assess(ROOT), gate._assess(ROOT))

    def test_report_cli(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--report"],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["assessment"], "KNOWN_EFFECT_EXPOSURE")
        self.assertEqual(json.loads(result.stdout)["status"], "HOLD")

    def test_release_cli(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--release-admission"],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(json.loads(result.stdout)["release_admitted"])

    def test_no_product_imports(self):
        before = set(sys.modules)
        gate._assess(ROOT)
        self.assertFalse(any(name == "nayeon" or name.startswith("nayeon.")
                             for name in set(sys.modules) - before))


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        # Non-executable fixture source deliberately raises if ever imported.
        self.relative = "fixture/actor.py"
        self.source = ('raise RuntimeError("fixture must never execute")\n'
                       'from fixture.native import Native\n'
                       'class Actor:\n'
                       '    def mutate(self):\n'
                       '        self.native.CredWriteW()\n')
        self.path = self.root / self.relative
        self.path.parent.mkdir()
        self.path.write_bytes(self.source.encode())
        self.addCleanup(patch.stopall)
        patch.object(gate, "SOURCE_HASHES", {
            self.relative: hashlib.sha256(self.source.encode()).hexdigest(),
        }).start()
        patch.object(gate, "CALL_SITES", (
            (self.relative, "Actor.mutate", "self.native.CredWriteW", "fixture_write"),
        )).start()
        patch.object(gate, "TEXT_SITES", ()).start()

    def unknown(self):
        report = gate._assess(self.root)
        self.assertEqual(report["status"], "HOLD")
        self.assertEqual(report["assessment"], "UNKNOWN")
        self.assertFalse(report["release_admitted"])
        self.assertTrue(report["issues"])
        return report

    def test_synthetic_source_is_only_parsed(self):
        report = gate._assess(self.root)
        self.assertEqual(report["assessment"], "KNOWN_EFFECT_EXPOSURE")
        self.assertEqual(report["evidence"][0]["line"], 5)

    def test_missing(self):
        self.path.unlink()
        self.unknown()

    def test_parse_failure(self):
        self.path.write_text("def invalid(\n", encoding="utf-8")
        report = self.unknown()
        self.assertIn("SyntaxError", [item["reason"] for item in report["issues"]])

    def test_altered_sink(self):
        self.path.write_text(self.source.replace("CredWriteW", "CredDeleteW"), encoding="utf-8")
        report = self.unknown()
        self.assertEqual(report["evidence"], [])

    def test_import_topology_drift(self):
        self.path.write_text(self.source.replace("fixture.native", "fixture.other"), encoding="utf-8")
        self.unknown()

    def test_added_dynamic_import(self):
        self.path.write_text(self.source + '__import__("other")\n', encoding="utf-8")
        self.unknown()

    def test_comment_drift_also_unknown(self):
        self.path.write_text(self.source + "# changed\n", encoding="utf-8")
        self.unknown()

    def test_duplicate_sink(self):
        self.path.write_text(self.source + "        self.native.CredWriteW()\n", encoding="utf-8")
        report = self.unknown()
        self.assertIn("known_call_site_changed", [item["reason"] for item in report["issues"]])

    def test_wrong_scope(self):
        self.path.write_text(self.source.replace("def mutate", "def other"), encoding="utf-8")
        report = self.unknown()
        self.assertIn("known_call_site_changed", [item["reason"] for item in report["issues"]])

    def test_ast_rejects_changed_sites_with_matching_fixture_pins(self):
        original_pins = gate.SOURCE_HASHES.copy()
        for label, source, count in (
            ("duplicate", self.source + "        self.native.CredWriteW()\n", 2),
            ("renamed_scope", self.source.replace("def mutate", "def other"), 0),
            ("missing_sink", self.source.replace("self.native.CredWriteW()", "pass"), 0),
        ):
            with self.subTest(case=label):
                data = source.encode()
                self.path.write_bytes(data)
                with patch.object(gate, "SOURCE_HASHES", {
                    self.relative: hashlib.sha256(data).hexdigest(),
                }):
                    report = self.unknown()
                self.assertEqual(gate.SOURCE_HASHES, original_pins)
                self.assertTrue(report["sources"][0]["matches_reviewed_snapshot"])
                self.assertEqual(report["issues"], [{
                    "path": self.relative, "reason": "known_call_site_changed", "site": "fixture_write",
                }])
                self.assertEqual(len(report["evidence"]), count)

    def test_cross_root_a_b_a_isolation(self):
        before = gate._assess(self.root)
        with tempfile.TemporaryDirectory() as directory:
            other_root = Path(directory)
            other_path = other_root / self.relative
            other_path.parent.mkdir()
            other_path.write_bytes(self.source.replace("CredWriteW", "CredDeleteW").encode())
            report = gate._assess(other_root)
            self.assertEqual(report["assessment"], "UNKNOWN")
            self.assertEqual(report["evidence"], [])
            self.assertNotEqual(report["sources"][0]["sha256"], before["sources"][0]["sha256"])
            self.assertIn("known_call_site_changed", [item["reason"] for item in report["issues"]])
        self.assertEqual(gate._assess(self.root), before)

    def test_cross_root_reparse_and_symlink_refused_before_read(self):
        before = gate._assess(self.root)
        real_lstat = Path.lstat
        with tempfile.TemporaryDirectory() as directory:
            other_root = Path(directory)
            for component in (other_root, other_root.parent):
                for mode, attributes in ((0o120777, 0), (0, 0x400)):
                    with self.subTest(component=component, mode=mode):
                        class LinkInfo:
                            st_mode = mode
                            st_file_attributes = attributes

                        def linked(path):
                            return LinkInfo() if path == component else real_lstat(path)

                        with patch.object(Path, "lstat", linked), patch.object(Path, "open") as opened:
                            report = gate._assess(other_root)
                            opened.assert_not_called()
                        self.assertEqual(report["assessment"], "UNKNOWN")
                        self.assertEqual(report["evidence"], [])
                        self.assertNotIn("sha256", report["sources"][0])
                        self.assertEqual(report["issues"], [{"path": self.relative, "reason": "ValueError"}])
                        self.assertEqual(gate._assess(self.root), before)

    def test_invalid_encoding(self):
        self.path.write_bytes(b"\xff")
        self.unknown()

    def test_directory_instead_of_file(self):
        self.path.unlink()
        self.path.mkdir()
        self.unknown()

    def test_read_denied(self):
        with patch.object(gate, "_read_source", side_effect=PermissionError):
            self.unknown()

    def test_reparse_rejected_before_open(self):
        real_lstat = Path.lstat

        class ReparseInfo:
            st_mode = 0
            st_file_attributes = 0x400

        def reparse(path):
            return ReparseInfo() if path == self.path.parent else real_lstat(path)

        with patch.object(Path, "lstat", reparse), patch.object(Path, "open") as opened:
            self.unknown()
            opened.assert_not_called()

    def test_oversized_source(self):
        self.path.write_bytes(b"#" * 1_000_001)
        self.unknown()

    def test_unknown_report_exit_zero_release_exit_three(self):
        self.path.unlink()
        with patch.object(gate, "REPO_ROOT", self.root), patch.object(gate, "INTENDED_ROOT", self.root):
            for args, expected in ((["--report"], 0), (["--release-admission"], 3)):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(gate.main(args), expected)
                self.assertEqual(json.loads(output.getvalue())["assessment"], "UNKNOWN")

    def test_unintended_root_refused(self):
        expected_fields = set(gate._assess(self.root))
        with patch.object(gate, "REPO_ROOT", self.root), patch.object(gate, "_assess") as assess, \
                patch.object(gate, "_read_source") as read_source, patch.object(Path, "open") as opened:
            for args, expected in ((["--report"], 0), (["--release-admission"], 3)):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(gate.main(args), expected)
                report = json.loads(output.getvalue())
                self.assertEqual(set(report), expected_fields)
                self.assertEqual(report["schema"], "byok-c1-p251-v1")
                self.assertEqual(report["assessment"], "UNKNOWN")
                self.assertEqual(report["status"], "HOLD")
                self.assertFalse(report["release_admitted"])
                self.assertFalse(report["independently_qualified"])
                for field in ("sources", "evidence", "known_routes"):
                    self.assertEqual(report[field], [])
                self.assertEqual(report["issues"], [{"reason": "unintended_repository_root"}])
                self.assertEqual(report["limitations"], list(gate.LIMITATIONS))
            assess.assert_not_called()
            read_source.assert_not_called()
            opened.assert_not_called()

    def test_no_go_option(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            gate.main(["--grant-go"])
        self.assertEqual(error.exception.code, 2)


class CheckoutMutationTests(unittest.TestCase):
    def test_each_exact_source_missing_or_altered_holds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in gate.SOURCE_HASHES:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            self.assertEqual(gate._assess(root)["assessment"], "KNOWN_EFFECT_EXPOSURE")
            for relative in gate.SOURCE_HASHES:
                with self.subTest(path=relative):
                    target = root / relative
                    original = target.read_bytes()
                    target.unlink()
                    self.assertEqual(gate._assess(root)["assessment"], "UNKNOWN")
                    target.write_bytes(original + b"\n")
                    report = gate._assess(root)
                    self.assertEqual(report["assessment"], "UNKNOWN")
                    self.assertEqual(report["status"], "HOLD")
                    target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
