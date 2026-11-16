"""Synthetic source bytes only. No product imports or native API calls."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import byok_c1_p255_effect_boundary as probe


# These strings are parsed, never imported or executed. The leading raise
# makes accidental fixture execution fail before any synthetic call site.
FIXTURES = {
    probe.p251.LAUNCH: '''raise RuntimeError("source fixture executed")
class LocalByokLaunchBridge:
    def launch(self):
        subprocess.Popen()
''',
    probe.p251.WINDOW: '''raise RuntimeError("source fixture executed")
def main():
    compose_user_scope_local_byok()
class LocalByokWindow:
    def approve_from_button(self):
        self._controller.approve()
''',
    probe.p251.CONTROLLER: '''raise RuntimeError("source fixture executed")
def compose_user_scope_local_byok():
    WindowsCredentialBackend()
class LocalByokController:
    def approve(self):
        self._backend.put()
        self._backend.delete()
''',
    probe.p251.BACKEND: '''raise RuntimeError("source fixture executed")
def _load_advapi32():
    ctypes.WinDLL()
class _Advapi32Adapter:
    def __init__(self):
        _load_advapi32()
    def write(self):
        self._dll.CredWriteW()
    def delete(self):
        self._dll.CredDeleteW()
class WindowsCredentialBackend:
    def _adapter(self):
        _Advapi32Adapter()
    def put(self):
        self._adapter().write()
    def delete(self):
        self._adapter().delete()
''',
}


class SyntheticBoundaryTests(unittest.TestCase):
    def setUp(self):
        # Keep temporary bytes within the authorized workspace.
        temporary = tempfile.TemporaryDirectory(dir=probe.ROOT)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative, source in FIXTURES.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.encode("utf-8"))
        kinds = {kind for route in probe.ROUTE_SITES.values() for kind in route}
        self.enterContext(patch.object(probe.p251, "SOURCE_HASHES", {
            relative: hashlib.sha256(source.encode("utf-8")).hexdigest()
            for relative, source in FIXTURES.items()
        }))
        self.enterContext(patch.object(probe.p251, "CALL_SITES", tuple(
            site for site in probe.p251.CALL_SITES if site[3] in kinds
        )))
        self.enterContext(patch.object(probe.p251, "TEXT_SITES", ()))

    def check_blocked(self, expected="UNKNOWN"):
        report = probe.assess(self.root)
        self.assertEqual(report["assessment"], expected)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["effect_owner_exclusivity"], "NOT_ESTABLISHED")
        for field in ("release_admitted", "real_key_admitted", "independently_approved"):
            self.assertIs(report[field], False)
        return report

    def change_backend(self, old, new, *, repin=False):
        path = self.root / probe.p251.BACKEND
        raw = FIXTURES[probe.p251.BACKEND].replace(old, new).encode("utf-8")
        path.write_bytes(raw)
        if repin:
            # Trusted synthetic seam isolates AST behavior from byte drift.
            probe.p251.SOURCE_HASHES[probe.p251.BACKEND] = hashlib.sha256(raw).hexdigest()

    def test_exact_direct_native_and_wrapper_routes_are_open_and_blocked(self):
        report = self.check_blocked("OPEN")
        self.assertEqual(report["issues"], [])
        self.assertEqual({route["route"] for route in report["routes"]}, set(probe.ROUTE_SITES))
        self.assertTrue(all(route["status"] == "OPEN" and route["sites"] for route in report["routes"]))
        sites = {entry["kind"]: entry for entry in report["evidence"]}
        self.assertEqual(sites["native_credential_write"]["call"], "self._dll.CredWriteW")
        self.assertEqual(sites["native_credential_delete"]["call"], "self._dll.CredDeleteW")
        self.assertEqual(sites["adapter_write"]["scope"], "WindowsCredentialBackend.put")
        self.assertEqual(sites["save_or_replace"]["scope"], "LocalByokController.approve")

    def test_alias_cannot_satisfy_direct_site_even_with_matching_fixture_pin(self):
        self.change_backend("self._dll.CredWriteW()", "writer = self._dll.CredWriteW\n        writer()", repin=True)
        report = self.check_blocked()
        self.assertTrue(all(source["matches_reviewed_snapshot"] for source in report["sources"]))
        self.assertIn({"reason": "unresolved_route_site", "site": "native_credential_write"}, report["issues"])

    def test_dynamic_lookup_is_unknown_even_with_matching_fixture_pin(self):
        self.change_backend("self._dll.CredWriteW()", 'getattr(self._dll, "CredWriteW")()', repin=True)
        self.assertTrue(self.check_blocked()["issues"])

    def test_safe_read_path_never_passes_or_proves_exclusion(self):
        self.change_backend("self._dll.CredWriteW()", "self._dll.CredReadW()", repin=True)
        self.assertTrue(self.check_blocked()["issues"])

    def test_comments_and_strings_do_not_satisfy_native_call(self):
        self.change_backend("self._dll.CredWriteW()", '"self._dll.CredWriteW()"\n        # self._dll.CredWriteW()', repin=True)
        report = self.check_blocked()
        self.assertFalse(any(site["kind"] == "native_credential_write" for site in report["evidence"]))

    def test_duplicate_and_wrong_scope_are_unknown_with_matching_pins(self):
        for old, new in (
            ("self._dll.CredWriteW()", "self._dll.CredWriteW()\n        self._dll.CredWriteW()"),
            ("def write(self)", "def renamed(self)"),
        ):
            with self.subTest(new=new):
                self.change_backend(old, new, repin=True)
                self.assertTrue(self.check_blocked()["issues"])

    def test_added_unresolved_code_is_unknown_without_repinning(self):
        self.change_backend("self._dll.CredWriteW()", 'self._dll.CredWriteW()\n        __import__("unknown")')
        report = self.check_blocked()
        self.assertIn("source_hash_drift_including_possible_sink_or_import_change", {issue["reason"] for issue in report["issues"]})

    def test_empty_manifest_and_removed_obligations_cannot_manufacture_open(self):
        with patch.object(probe.p251, "SOURCE_HASHES", {}), patch.object(probe.p251, "CALL_SITES", ()):
            self.assertTrue(self.check_blocked()["issues"])

    def test_no_mutation_fixture_has_no_open_route(self):
        for relative in FIXTURES:
            raw = b"def metadata_only():\n    return None\n"
            (self.root / relative).write_bytes(raw)
            probe.p251.SOURCE_HASHES[relative] = hashlib.sha256(raw).hexdigest()
        report = self.check_blocked()
        self.assertEqual(report["evidence"], [])
        self.assertTrue(all(route["status"] == "UNKNOWN" for route in report["routes"]))

    def test_missing_syntax_encoding_and_size_fail_closed(self):
        path = self.root / probe.p251.BACKEND
        for raw in (None, b"def broken(\n", b"\xff", b"#" * 1_000_001):
            with self.subTest(raw_kind=None if raw is None else len(raw)):
                if raw is None:
                    path.unlink()
                else:
                    path.write_bytes(raw)
                self.assertTrue(self.check_blocked()["issues"])

    def test_read_denied_is_unknown(self):
        with patch.object(probe.p251, "_read_source", side_effect=PermissionError):
            self.assertTrue(self.check_blocked()["issues"])

    def test_mocked_reparse_is_refused_before_file_open(self):
        real_lstat = Path.lstat

        class ReparseInfo:
            st_mode = 0
            st_file_attributes = 0x400

        def lstat(path):
            return ReparseInfo() if path == self.root else real_lstat(path)

        with patch.object(Path, "lstat", lstat), patch.object(Path, "open") as opened:
            self.assertTrue(self.check_blocked()["issues"])
            opened.assert_not_called()

    def test_a_b_a_source_observations_are_fresh_and_deterministic(self):
        before = probe.assess(self.root)
        path = self.root / probe.p251.BACKEND
        original = path.read_bytes()
        self.change_backend("self._dll.CredWriteW()", "pass")
        self.check_blocked()
        path.write_bytes(original)
        self.assertEqual(probe.assess(self.root), before)
        self.assertEqual(probe.assess(self.root), before)

    def test_assessment_imports_no_product_modules(self):
        before = set(sys.modules)
        self.check_blocked("OPEN")
        self.assertFalse(any(name == "nayeon" or name.startswith("nayeon.") for name in set(sys.modules) - before))

    def test_cli_blocks_both_open_and_unknown(self):
        with patch.object(probe, "ROOT", self.root), patch.object(probe, "INTENDED_ROOT", self.root):
            for expected in ("OPEN", "UNKNOWN"):
                if expected == "UNKNOWN":
                    self.change_backend("self._dll.CredWriteW()", "pass")
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(probe.main([]), 3)
                report = json.loads(output.getvalue())
                self.assertEqual(report["assessment"], expected)
                self.assertEqual(report["status"], "BLOCKED")

    def test_wrong_root_blocks_before_assessment(self):
        with patch.object(probe, "ROOT", self.root), patch.object(probe, "assess") as assessed:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(probe.main([]), 3)
            assessed.assert_not_called()
            report = json.loads(output.getvalue())
            self.assertEqual(report["assessment"], "UNKNOWN")
            self.assertEqual(report["issues"], [{"reason": "unintended_repository_root"}])
            self.assertEqual(report["sources"], [])

    def test_no_root_or_approval_override(self):
        for args in (["--root", str(self.root)], ["--grant-go"], ["--release-admission"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    probe.main(args)
                self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
