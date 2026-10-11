"""Exact governance-only AGENTS change; keep historic tag and other freezes.

Old phase snapshots still contain the original immutable AGENTS blob.
Current working AGENTS must EXACTLY match the separately approved
governance commit; any unreviewed drift remains a test failure.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APPROVED_GOVERNANCE = "02f3fb6a0de9c8871ff5ec41818853725b24226c"


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def assert_authorized_governance(test_case, historic_baseline: str) -> None:
    def normalized(value: bytes) -> bytes:
        return value.replace(b"\r\n", b"\n")
    # Immutable history from the original checkpoint remains retrievable.
    historic = normalized(_git("show", historic_baseline + ":AGENTS.md"))
    test_case.assertTrue(historic.startswith(b"# Nayeon v1 engineering instructions"))
    test_case.assertEqual(_git("cat-file", "-t", APPROVED_GOVERNANCE).strip(), b"commit")
    test_case.assertEqual(
        subprocess.call(["git", "merge-base", "--is-ancestor",
                         historic_baseline, APPROVED_GOVERNANCE], cwd=ROOT), 0)
    test_case.assertEqual(
        subprocess.call(["git", "merge-base", "--is-ancestor",
                         APPROVED_GOVERNANCE, "HEAD"], cwd=ROOT), 0)
    approved = normalized(_git("show", APPROVED_GOVERNANCE + ":AGENTS.md"))
    current = normalized((ROOT / "AGENTS.md").read_bytes())
    test_case.assertNotEqual(historic, approved,
                             "Governance exception must be an actual separately reviewed change")
    test_case.assertEqual(current, approved,
                          "AGENTS.md must equal the exact approved governance seal")
    test_case.assertIn(b"Mandatory Failure & Architectural Regression Gate", current)
