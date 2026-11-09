"""P134 exact migration: real native CRED test ONLY on ephemeral Windows CI.

Do not rewrite historical P133/P132/P76 scope tests or original native source.
This is not production-signing approval or a test with a real API key.
"""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
P133 = "e79b8c12168cd5869cdb2d7feea6656baf4c0624"
NEW_FILES = frozenset({
    ".github/workflows/p134-windows-ephemeral-native-wincred.yml",
    "docs/byok-c1-p134-ephemeral-native-wincred-interoperability.md",
    "tests/test_p134_real_wincred_ephemeral.py",
    "tests/test_p134_scope_migration.py",
})
FROZEN = (
    "nayeon/secrets/windows_credential.py",
    "nayeon/secrets/contracts.py",
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/__main__.py",
    "tests/test_local_user_scope_byok.py",
    "tests/test_p132_user_scope_migration.py",
    "tests/test_p133_connection_launch.py",
    "tests/test_p133_scope_migration.py",
    "tests/phase8_byok_c1_p76_scope.py",
    "tests/test_windows_credential_backend.py",
    "tests/test_bound_credential_lifecycle.py",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True,
        text=True, check=True, timeout=12,
    ).stdout.strip()


class P134SyntheticNativeWinCredAdmission(unittest.TestCase):
    def test_exact_parent_and_four_added_files(self):
        self.assertEqual(_git("merge-base", "HEAD", P133), P133)
        paths = frozenset(_git("diff", "--name-only", P133, "HEAD").splitlines())
        self.assertEqual(paths, NEW_FILES)
        self.assertEqual(subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--check", P133, "HEAD"],
            capture_output=True, timeout=10,
        ).returncode, 0)

    def test_all_user_scope_product_code_historical_proofs_unchanged(self):
        for path in FROZEN:
            with self.subTest(path=path):
                self.assertEqual(
                    _git("rev-parse", "HEAD:" + path),
                    _git("rev-parse", P133 + ":" + path),
                    "P134 may only add test and evidence; no product mutation",
                )

    def test_real_wincred_test_has_strict_runner_and_random_namespace(self):
        source = (ROOT / "tests/test_p134_real_wincred_ephemeral.py").read_text(
            encoding="utf-8",
        )
        self.assertIn('P134_NATIVE_WINCRED_EPHEMERAL_AUTH', source)
        self.assertIn('GITHUB_REPOSITORY', source)
        self.assertIn('RUNNER_TEMP', source)
        self.assertIn('uuid.uuid4().hex', source)
        self.assertIn('"nayeon-v1/secret/openai.api_key"', source)
        self.assertIn('_PRODUCTION_TARGET', source)
        self.assertIn('assertFalse(self.backend.is_available(self.identifier))', source)
        self.assertIn('self.addCleanup(self._delete_owned_fixture)', source)
        self.assertNotIn('SecretIdentifier("openai.api_key")', source)

    def test_only_test_module_can_read_synthetic_native_credential(self):
        changed = _git("diff", "--name-only", P133, "HEAD").splitlines()
        self.assertFalse(any(p.startswith("nayeon/") for p in changed))
        source = (ROOT / "tests/test_p134_real_wincred_ephemeral.py").read_text(
            encoding="utf-8",
        )
        tree = ast.parse(source)
        imports = {
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertIn("nayeon.secrets.windows_credential", imports)
        self.assertNotIn("nayeon.brain.providers.openai_validation", imports)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name, ("requests", "openai", "urllib"))

    def test_default_desktop_startup_and_launcher_are_immutable(self):
        original = (ROOT / "nayeon/desktop_alpha/__main__.py").read_text()
        self.assertNotIn("test_p134_real_wincred_ephemeral", original)
        self.assertNotIn("P134_NATIVE_WINCRED_EPHEMERAL_AUTH", original)
        launcher = (
            ROOT / "nayeon/desktop_alpha/local_byok_launch_bridge.py"
        ).read_text()
        self.assertNotIn("test_p134_real_wincred_ephemeral", launcher)

    def test_native_wincdren_only_synthetic_scope_and_no_release_claim(self):
        doc = (
            ROOT / "docs/byok-c1-p134-ephemeral-native-wincred-interoperability.md"
        ).read_text()
        self.assertIn("NO real API key", doc)
        self.assertIn("Kristian", doc)
        self.assertIn("USER-SCOPED RELEASE HOLD", doc)
        self.assertIn("not a signed package", doc.lower())


if __name__ == "__main__":
    unittest.main()
