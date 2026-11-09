"""P132 authorised-scope migration for a deliberately NEW user WinCred consumer.

This does NOT modify, ignore, weaken or falsely execute historical Phase 8
and P76 exact-branch seal tests. Those guards are intended for their pinned
historical branches and cannot bless a new consumer on P132. Instead P132
requires an explicit exact changed-path inventory, immutable original files,
a fixed WinCred slot, restricted imports, and no new model/provider access.
"""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
P131 = "18a12701e00dda8205c3b6b6a5f333115ff15b0e"
P132_PATHS = frozenset({
    ".github/workflows/p132-windows-user-scope-byok.yml",
    "docs/byok-c1-p132-user-scoped-offline-first-release.md",
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "tests/test_local_user_scope_byok.py",
    "tests/test_p132_user_scope_migration.py",
})
ORIGINAL_GUARDS = (
    "tests/test_windows_credential_backend.py",
    "tests/test_bound_credential_lifecycle.py",
    "tests/phase8_byok_c1_p76_scope.py",
    "tests/phase8_byok_c1_p85_scope.py",
)
ORIGINAL_SOURCES = (
    "nayeon/secrets/windows_credential.py",
    "nayeon/secrets/contracts.py",
    "nayeon/secrets/lifecycle.py",
    "nayeon/brain/windows_onboarding_mutex.py",
    "nayeon/desktop_alpha/__main__.py",
    "nayeon/desktop_alpha/first_run_credential_management_window.py",
    "nayeon/brain/credential_operation_host.py",
)


def _git(*args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True,
        text=True, check=True, timeout=12,
    )
    return process.stdout.strip()


class P132ExplicitConsumerMigration(unittest.TestCase):
    def test_direct_p131_ancestry_and_exact_six_new_paths(self):
        self.assertEqual(_git("merge-base", "HEAD", P131), P131)
        changed = frozenset(_git("diff", "--name-only", P131, "HEAD").splitlines())
        self.assertEqual(changed, P132_PATHS)
        result = subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--check", P131, "HEAD"],
            capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, "no whitespace/source drift")

    def test_old_branch_frozen_guards_and_native_backend_unchanged(self):
        for relative in ORIGINAL_GUARDS + ORIGINAL_SOURCES:
            with self.subTest(file=relative):
                self.assertEqual(
                    _git("rev-parse", "HEAD:" + relative),
                    _git("rev-parse", P131 + ":" + relative),
                    "historical source or sealed scope guard changed",
                )

    def test_only_one_new_controller_has_direct_secret_backend_import(self):
        controller = ROOT / "nayeon/brain/local_byok_user_scope.py"
        interface = ROOT / "nayeon/desktop_alpha/local_byok_window.py"
        ctree = ast.parse(controller.read_text(encoding="utf-8"))
        itree = ast.parse(interface.read_text(encoding="utf-8"))
        imports = {
            node.module for node in ast.walk(ctree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertIn("nayeon.secrets.windows_credential", imports)
        self.assertIn("nayeon.secrets.contracts", imports)
        ui_imports = {
            node.module for node in ast.walk(itree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("nayeon.secrets.windows_credential", ui_imports)
        self.assertNotIn("nayeon.brain.providers.openai_validation", ui_imports)
        self.assertIn("nayeon.brain.local_byok_user_scope", ui_imports)
        self.assertIn("nayeon.secrets.contracts", ui_imports)

    def test_no_new_direct_credential_references_outside_approved_files(self):
        changed = _git("diff", "--name-only", P131, "HEAD").splitlines()
        actual = [
            path for path in changed
            if path.startswith("nayeon/") and path.endswith(".py")
        ]
        self.assertEqual(
            actual, [
                "nayeon/brain/local_byok_user_scope.py",
                "nayeon/desktop_alpha/local_byok_window.py",
            ],
        )
        for relative in actual:
            text = (ROOT / relative).read_text(encoding="utf-8")
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, {
                        "nayeon.brain.providers.openai_validation",
                        "nayeon.secrets.resolver",
                    })
                if isinstance(node, ast.Import):
                    for name in node.names:
                        self.assertNotIn(name.name, {
                            "requests", "urllib", "socket", "openai",
                        })
            self.assertNotIn("backend.get(", text)
            self.assertNotIn("CredWriteW(", text)
            self.assertNotIn("CredDeleteW(", text)

    def test_no_automatic_default_setup_or_provider_validation(self):
        entry = (ROOT / "nayeon/desktop_alpha/__main__.py").read_text()
        self.assertNotIn("local_byok", entry)
        self.assertIn("--notepad", entry)
        source = (
            ROOT / "nayeon/desktop_alpha/local_byok_window.py"
        ).read_text()
        self.assertIn('if __name__ == "__main__"', source)
        self.assertIn("sys.platform != \"win32\"", source)
        self.assertIn("Review save new key", source)
        self.assertIn("Approve selected operation once", source)
        self.assertNotIn("OpenAICredentialValidator", source)


if __name__ == "__main__":
    unittest.main()
