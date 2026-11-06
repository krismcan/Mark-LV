"""P71: fail-closed predecessor compatibility in an offline-only C1 candidate.

This test does not supply a successor admission guard, credential permit, service,
native mutation, network operation or release approval. It must fail if the
sealed predecessor verifier starts accepting a different C1 work branch.
"""
import unittest
from tests import phase10_3_scope_migration as prior


class OfflineC1PredecessorRefusalTests(unittest.TestCase):
    def test_sealed_phase10_3_admission_denies_offline_successor_branch(self):
        self.assertEqual(prior.BRANCH,
                         "phase10-3-synthetic-provenance-redaction-20261104")
        with self.assertRaisesRegex(AssertionError, "Phase10 wrong exact branch"):
            prior.assert_phase10_3_integrity()

    def test_predecessor_remains_bound_to_original_parent(self):
        self.assertEqual(prior.PARENT,
                         "4aff3459ee127b0a7a124073aac2a9317e467301")
        self.assertEqual(prior.BRANCH,
                         "phase10-3-synthetic-provenance-redaction-20261104")


if __name__ == "__main__":
    unittest.main()
