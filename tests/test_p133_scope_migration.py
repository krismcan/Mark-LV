"""P133 explicit desktop navigation rescope; NEVER weakens P132 seals.

New Connection-page launcher is an intentional additive consumer entry, not
approval for native WinCred effect, arbitrary commands or provider access.
Historical P132 scope/Phase8/P76 tests remain byte-identical and are run on
their original branch/seal context, never falsely declared passing on P133.
"""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
P132 = "29c6065c3e04d7af03d97496259e113341994c49"
P133_FILES = frozenset({
    ".github/workflows/p133-windows-desktop-byok-entry.yml",
    "docs/byok-c1-p133-desktop-connection-launch-review.md",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "tests/test_p133_connection_launch.py",
    "tests/test_p133_scope_migration.py",
})
FROZEN_P132 = (
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "tests/test_local_user_scope_byok.py",
    "tests/test_p132_user_scope_migration.py",
    "nayeon/secrets/windows_credential.py",
    "nayeon/secrets/contracts.py",
    "nayeon/brain/windows_onboarding_mutex.py",
    "nayeon/desktop_alpha/__main__.py",
    "tests/phase8_byok_c1_p76_scope.py",
    "tests/test_windows_credential_backend.py",
    "tests/test_bound_credential_lifecycle.py",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
)


def _git(*args) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True,
        capture_output=True, text=True, timeout=15,
    ).stdout.strip()


class P133DesktopIntegrationMigration(unittest.TestCase):
    def test_exact_p132_ancestry_seven_changed_paths_and_clean_diff(self):
        self.assertEqual(_git("merge-base", "HEAD", P132), P132)
        changed = frozenset(_git("diff", "--name-only", P132, "HEAD").splitlines())
        self.assertEqual(changed, P133_FILES)
        result = subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--check", P132, "HEAD"],
            capture_output=True, timeout=12,
        )
        self.assertEqual(result.returncode, 0, "new desktop integration has no whitespace error")

    def test_p132_storage_ui_and_original_security_source_immutable(self):
        for name in FROZEN_P132:
            with self.subTest(name=name):
                self.assertEqual(
                    _git("rev-parse", "HEAD:" + name),
                    _git("rev-parse", P132 + ":" + name),
                    "approved P132 or original source unexpectedly changed",
                )

    def test_new_launcher_never_imports_wincred_model_or_provider(self):
        path = ROOT / "nayeon/desktop_alpha/local_byok_launch_bridge.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules = [
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        for blocked in (
            "nayeon.secrets.windows_credential",
            "nayeon.secrets.contracts",
            "nayeon.brain.credential_onboarding",
            "nayeon.brain.providers.openai_validation",
        ):
            self.assertNotIn(blocked, modules)
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("shell=True", source)
        self.assertNotIn("CredWriteW(", source)
        self.assertNotIn("backend.get(", source)
        self.assertIn("_ALLOWED_WINDOWS_ENV", source)
        self.assertIn("shell=False", source)

    def test_main_app_imports_launch_bridge_only_inside_callback(self):
        path = ROOT / "nayeon/desktop_alpha/application.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == (
                "nayeon.desktop_alpha.local_byok_launch_bridge"
            ):
                imports.append(node)
        self.assertEqual(len(imports), 1)
        methods = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_open_local_byok"
        ]
        self.assertEqual(len(methods), 1)
        self.assertIn(imports[0], list(ast.walk(methods[0])))
        self.assertNotIn("nayeon.secrets.windows_credential",
                         path.read_text(encoding="utf-8"))

    def test_connection_pane_is_only_ui_callback_without_io(self):
        pane = ROOT / "nayeon/desktop_alpha/workspace_window.py"
        text = pane.read_text(encoding="utf-8")
        self.assertIn("on_local_byok=None", text)
        self.assertIn("Open local key setup (offline, not connected)", text)
        self.assertNotIn("local_byok_launch_bridge", text)
        self.assertNotIn("WindowsCredentialBackend", text)
        self.assertNotIn("CredWriteW(", text)

    def test_default_offline_entrypoint_is_untouched(self):
        path = ROOT / "nayeon/desktop_alpha/__main__.py"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("local_byok_window", text)
        self.assertIn("--notepad", text)
        self.assertIn("from nayeon.desktop_alpha.window import main", text)

    def test_no_new_privileged_storage_or_security_bypass(self):
        for relative in (
            "nayeon/desktop_alpha/local_byok_launch_bridge.py",
            "nayeon/desktop_alpha/application.py",
            "nayeon/desktop_alpha/workspace_window.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for forbidden in (
                "CredDeleteW(", "CredWriteW(", "TPM2_NV_Increment",
                "ServiceBase.Run(", "HKLM\\", "winreg.SetValue",
            ):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
