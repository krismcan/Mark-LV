"""P73: hostile offline C1 boundary tests; no credential operations.

This is neither a release gate nor an authority/consent proof.  It verifies
that the byte-pinned P71 pure policy and untrusted evidence codec remain
separate from any real Windows credential service or executable effect.
"""
import ast
import hashlib
from pathlib import Path
import unittest

from nayeon.brain import pending_credential_policy as policy
from nayeon.brain import pending_credential_recovery_document as evidence

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "nayeon/brain/pending_credential_policy.py":
        "747DA9F31633F0A76BD559ADF01CA9E5338154ADD4E380C3A80758BD3D18AFCD",
    "nayeon/brain/pending_credential_recovery_document.py":
        "9B4E98E2C8B39910E1D8A510F421FCB350C32D6FE2BFB6A54C4C34E1063F1DE9",
    "tests/test_pending_credential_policy.py":
        "62D33BCD5FD9AA85B0EC64419B3232755828FE1DFC21B18278848DD35EA105D0",
    "tests/test_pending_credential_recovery_document.py":
        "5DC21BBA0AF8383CD3754193191FC3ED67E3EC9C3699D98847D3CB889122EFCA",
}
SOURCE_IMPORTS = {
    "nayeon/brain/pending_credential_policy.py": {"dataclasses", "enum"},
    "nayeon/brain/pending_credential_recovery_document.py":
        {"dataclasses", "enum", "hashlib", "json", "re"},
}


class OfflineBoundaryTests(unittest.TestCase):
    def test_imported_four_files_still_match_verbatim_sha256(self):
        for rel, expected in PINS.items():
            with self.subTest(path=rel):
                self.assertEqual(
                    hashlib.sha256((ROOT / rel).read_bytes()).hexdigest().upper(),
                    expected,
                )

    def test_pure_sources_import_only_declared_standard_modules(self):
        for rel, allowed in SOURCE_IMPORTS.items():
            with self.subTest(path=rel):
                code = ast.parse((ROOT / rel).read_bytes())
                for node in ast.walk(code):
                    if isinstance(node, ast.Import):
                        for spec in node.names:
                            self.assertIn(spec.name, allowed)
                    elif isinstance(node, ast.ImportFrom):
                        self.assertEqual(node.level, 0)
                        self.assertIn(node.module, allowed)
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        self.assertNotIn(node.func.id, {
                            "open", "exec", "eval", "compile", "__import__",
                        })

    def test_recomputed_hash_history_is_still_untrusted(self):
        record = evidence.PendingEvidenceRecord(
            schema_version=1, sequence=1, epoch="a" * 32, generation=0,
            state=evidence.PendingRecordedState.IN_FLIGHT,
            previous_hash="0" * 64, operation_id="b" * 32,
            operation_kind="pending_replace", evidence_hash="c" * 64,
        )
        forged = evidence.encode_frame(record)
        self.assertEqual(evidence.decode_journal(forged), (record,))
        # A valid hash chain is an unauthenticated claim, not a state grant.
        for action in policy.PendingCredentialAction:
            with self.subTest(action=action):
                result = policy.assess_pending_credential_action(
                    policy.PendingCredentialState.RECOVERY_REQUIRED, action
                )
                self.assertIs(
                    result.decision,
                    policy.PendingCredentialDecision.RECOVERY_BLOCKED,
                )
                self.assertFalse(hasattr(result, "approve"))
                self.assertFalse(hasattr(result, "execute"))

    def test_corrupted_claim_cannot_be_interpreted_as_valid_history(self):
        record = evidence.PendingEvidenceRecord(
            schema_version=1, sequence=1, epoch="a" * 32, generation=0,
            state=evidence.PendingRecordedState.BLOCKED,
            previous_hash="0" * 64,
        )
        good = evidence.encode_frame(record)
        body = bytearray(good)
        body[-3] ^= 1
        with self.assertRaises(evidence.PendingEvidenceError):
            evidence.decode_journal(bytes(body))

    def test_no_state_or_decision_implies_ready_or_connected(self):
        for enum in (
            policy.PendingCredentialState,
            policy.PendingCredentialDecision,
            evidence.PendingRecordedState,
        ):
            for item in enum:
                self.assertFalse(any(term in item.value for term in (
                    "ready", "approved", "connected", "active", "verified_success"
                )))

    def test_recovery_claim_and_policy_never_offer_retry(self):
        for action in policy.PendingCredentialAction:
            verdict = policy.assess_pending_credential_action(
                policy.PendingCredentialState.RECOVERY_REQUIRED, action
            )
            self.assertEqual(
                verdict.decision,
                policy.PendingCredentialDecision.RECOVERY_BLOCKED,
            )


if __name__ == "__main__":
    unittest.main()
