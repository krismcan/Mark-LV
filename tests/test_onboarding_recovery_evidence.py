"""Reproducible, secret-free Phase 8.28.1 recovery fingerprints."""
import unittest

from nayeon.brain.connection_document import parse_provider_connection_document
from nayeon.brain.onboarding_recovery_evidence import canonical_evidence_digest
from nayeon.brain.onboarding_recovery_document import (
    GENESIS_HASH, RecoveryRecord, RecoveryState, encode_frame, decode_journal,
)


def metadata(model):
    return parse_provider_connection_document({
        "schema_version": 1,
        "connection": {"provider": "openai", "model": model,
                       "credential": "openai.api_key"},
    })


class CanonicalEvidenceTests(unittest.TestCase):
    def test_digest_stable_across_distinct_objects(self):
        a = metadata("gpt-6")
        b = metadata("gpt-6")
        self.assertIsNot(a, b)
        args = dict(kind="save_metadata", identity=(1, 2, 3, 4, 5))
        self.assertEqual(
            canonical_evidence_digest(before=a, after=None, **args),
            canonical_evidence_digest(before=b, after=None, **args))

    def test_changed_model_identity_and_kind_change_digest(self):
        args = dict(kind="save_metadata", before=None, after=metadata("gpt-6"),
                    identity=(1, 2, 3, 4, 5))
        expected = canonical_evidence_digest(**args)
        self.assertNotEqual(expected, canonical_evidence_digest(
            **{**args, "after": metadata("gpt-5.6")}))
        self.assertNotEqual(expected, canonical_evidence_digest(
            **{**args, "identity": (1, 2, 3, 4, 6)}))
        self.assertNotEqual(expected, canonical_evidence_digest(
            **{**args, "kind": "clear_metadata"}))

    def test_all_intended_review_test_operations_have_codec_entry(self):
        from nayeon.brain.onboarding_recovery_evidence import canonical_evidence_digest
        for kind in ("review", "test_candidate", "test_stored"):
            fingerprint = canonical_evidence_digest(
                kind=kind, before=None, after=None, identity=None,
                observation="setup_required")
            r=RecoveryRecord(
                schema_version=1, sequence=1, epoch="a"*32, generation=0,
                state=RecoveryState.IN_FLIGHT, previous_hash=GENESIS_HASH,
                operation_id="c"*32, operation_kind=kind,
                evidence_hash=fingerprint)
            self.assertEqual(decode_journal(encode_frame(r)), (r,))

    def test_no_secret_or_untrusted_observation_encoded(self):
        with self.assertRaises(ValueError):
            canonical_evidence_digest(kind="save_metadata", before=None,
                                      after=None, identity=None,
                                      observation="sk-this-is-not-allowed")
        with self.assertRaises(TypeError):
            canonical_evidence_digest(kind="save_metadata", before=None,
                                      after=None, identity=("a",), observation=None)


if __name__ == "__main__":
    unittest.main()
