"""P140 explicit frozen launcher scope migration — old historical seals untouched.

Unlike P132/P133/P134/P76 exact-branch tests, P140 is intentionally a
different later product branch. It explicitly authenticates the SIX changed
paths, unchanged native credential backend/old UI/test files and immutable
review/signing no-GO defaults; never claims historic seals ran on P140.
"""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE="052cf4f076d5f2c6e170593cab473d0c8eab7c3a"
FILES=frozenset({
    ".github/workflows/p140-windows-frozen-signed-companion-gate.yml",
    "docs/byok-c1-p140-signed-frozen-companion-release-review.md",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "tests/test_p140_frozen_signed_companion.py",
    "tests/test_p140_scope_migration.py",
})
FROZEN=(
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/__main__.py",
    "nayeon/secrets/windows_credential.py",
    "nayeon/secrets/contracts.py",
    "nayeon/brain/windows_onboarding_mutex.py",
    "tests/test_local_user_scope_byok.py",
    "tests/test_p133_connection_launch.py",
    "tests/test_p134_real_wincred_ephemeral.py",
    "tests/test_p134_scope_migration.py",
    "tests/phase8_byok_c1_p76_scope.py",
    "tests/test_windows_credential_backend.py",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs",
)

def _git(*args):
    return subprocess.run(
        ["git","-C",str(ROOT),*args],capture_output=True,
        text=True,check=True,timeout=12,
    ).stdout.strip()

class P140FrozenSignedLaunchMigration(unittest.TestCase):
    def test_exact_p139_ancestry_and_approved_six_path_change(self):
        self.assertEqual(_git("merge-base","HEAD",BASE),BASE)
        paths=frozenset(_git("diff","--name-only",BASE,"HEAD").splitlines())
        self.assertEqual(paths,FILES)
        self.assertEqual(subprocess.run(
            ["git","-C",str(ROOT),"diff","--check",BASE,"HEAD"],
            capture_output=True,timeout=10,
        ).returncode,0)

    def test_old_credential_source_and_historical_guards_untouched(self):
        for path in FROZEN:
            with self.subTest(path=path):
                self.assertEqual(
                    _git("rev-parse","HEAD:"+path),
                    _git("rev-parse",BASE+":"+path),
                )

    def test_only_one_existing_product_launch_bridge_changed(self):
        source=_git("diff","--name-status",BASE,"HEAD").splitlines()
        self.assertIn("M\tnayeon/desktop_alpha/local_byok_launch_bridge.py",source)
        self.assertEqual(
            [line for line in source if line.startswith("M\t")],
            ["M\tnayeon/desktop_alpha/local_byok_launch_bridge.py"],
        )

    def test_freeze_gate_no_issuer_or_binary_approval_material(self):
        from nayeon.desktop_alpha import frozen_signed_byok_companion as gate
        self.assertEqual(gate._APPROVED_MAIN_SHA256,"")
        self.assertEqual(gate._APPROVED_COMPANION_SHA256,"")
        self.assertEqual(gate._APPROVED_SIGNER_CERT_SHA256,"")
        self.assertFalse(gate._APPROVED_CODE_INTEGRITY_RELEASE)
        self.assertFalse(gate._release_pins_issued())

    def test_frozen_gate_has_no_key_provider_or_native_credential_access(self):
        for path in (
            "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
            "nayeon/desktop_alpha/local_byok_launch_bridge.py",
        ):
            text=(ROOT/path).read_text(encoding="utf8")
            tree=ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):
                    self.assertNotIn(node.module,{
                        "nayeon.secrets.windows_credential",
                        "nayeon.secrets.contracts",
                        "nayeon.brain.providers.openai_validation",
                    })
            for prohibited in (
                "CredWriteW(", "CredReadW(", "CredDeleteW(",
                "backend.get(", "TPM2_NV_Increment", "HKLM\\",
                "shell=True", "requests.",
            ):
                self.assertNotIn(prohibited,text)

    def test_normal_offline_startup_still_does_not_call_companion(self):
        text=(ROOT/"nayeon/desktop_alpha/__main__.py").read_text()
        self.assertNotIn("frozen_signed_byok_companion",text)
        self.assertNotIn("local_byok_window",text)
        self.assertIn("--notepad",text)

if __name__=="__main__":
    unittest.main()
