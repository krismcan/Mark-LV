"""P216 Windows store-principal architecture source/effect inventory negatives.

Static source tracking is not production Code Integrity and cannot prove the
absence of dynamic P/Invoke, process memory scraping, or uncontrolled same-user
native calls. All effects, review decisions, key migration and GO stay denied.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import tempfile
import unittest

from nayeon.brain.p216_service_store_decision import (
    CANDIDATE_SERVICE_ACCOUNT,CANDIDATE_STORE_CRYPTO,
    CANDIDATE_OS_BOUNDARY,CANDIDATE_MACHINE_DPAPI_AS_IS,
    G0_R3_UNRESOLVED,KNOWN_DIRECT_EFFECT,KNOWN_CONSUMER,KNOWN_LAUNCHER,
    P216ReviewStatus,P216StoreReview,
    authorize_cross_principal_user_vault_migration,
    proposed_service_store_admission,review_proposed_service_store,
)

ROOT=Path(__file__).resolve().parents[1]


def _tracked()->tuple[str,...]:
    raw=subprocess.run(["git","ls-files","-z","--","nayeon","core"],
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=30,check=True)
    if raw.stderr:raise RuntimeError("tracked source inventory unavailable")
    paths=raw.stdout.decode("utf8").strip("\x00").split("\x00")
    return tuple(p for p in paths if p.endswith(".py"))


class P216ServiceStoreChoiceAndSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths=_tracked()
        cls.receipt=review_proposed_service_store(ROOT,cls.paths)
        if cls.receipt.status is not P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION:
            raise RuntimeError("P216 cannot claim legitimate legacy source witness")

    def test_01_actual_git_tracked_inventory_is_nonempty(self):
        self.assertGreater(self.receipt.parsed_tracked_python,10)
        self.assertEqual(self.receipt.parsed_tracked_python,len(self.paths))

    def test_02_p132_live_Python_direct_WinCred_effect_still_reachable(self):
        self.assertTrue(self.receipt.direct_effect_source_reachable)

    def test_03_exact_original_P132_controller_effect_route_still_reachable(self):
        self.assertTrue(self.receipt.local_user_controller_reachable)

    def test_04_original_P133_child_launcher_reachable(self):
        self.assertTrue(self.receipt.source_launcher_reachable)

    def test_05_current_native_C1_service_is_only_refusal(self):
        self.assertTrue(self.receipt.original_native_C1_host_denial_only)

    def test_06_actual_native_credential_adapter_appears_in_scan(self):
        a=[f for f in self.receipt.findings if f.path==KNOWN_DIRECT_EFFECT]
        self.assertEqual(len(a),1)
        self.assertTrue(a[0].wincred_native_adapter)

    def test_07_real_P132_backend_constructor_import_appears(self):
        a=[f for f in self.receipt.findings if f.path==KNOWN_CONSUMER]
        self.assertEqual(len(a),1)
        self.assertTrue(a[0].wincred_backend_import)

    def test_08_known_launcher_and_original_source_are_in_actual_git(self):
        self.assertTrue({KNOWN_LAUNCHER,KNOWN_DIRECT_EFFECT,KNOWN_CONSUMER}
                        .issubset(set(self.paths)))

    def test_09_absent_tracked_effect_source_is_UNPROVEN(self):
        reduced=tuple(p for p in self.paths if p!=KNOWN_DIRECT_EFFECT)
        r=review_proposed_service_store(ROOT,reduced)
        self.assertEqual(r.status,P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)
        self.assertFalse(r.release_eligible)

    def test_10_untrusted_traversal_windows_ads_or_absolute_path_is_UNPROVEN(self):
        for extra in ("../outside.py","nayeon/secrets/x.py:bad",
                      "/nayeon/secrets/copy.py",
                      "nayeon\\secrets\\windows_credential.py"):
            with self.subTest(extra=extra):
                r=review_proposed_service_store(ROOT,self.paths+(extra,))
                self.assertEqual(r.status,P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)

    def test_11_casefold_alias_source_is_UNPROVEN(self):
        r=review_proposed_service_store(
            ROOT,self.paths+(KNOWN_DIRECT_EFFECT.upper(),))
        self.assertEqual(r.status,P216ReviewStatus.TRACKED_SOURCE_UNPROVEN)

    def test_12_untracked_root_with_all_source_missing_is_UNPROVEN(self):
        with tempfile.TemporaryDirectory(prefix="p216-source-") as d:
            r=review_proposed_service_store(Path(d),self.paths)
            self.assertEqual(r.status,P216ReviewStatus.SOURCE_UNPROVEN)

    def test_13_no_external_service_selection_written_as_GO(self):
        self.assertEqual(CANDIDATE_SERVICE_ACCOUNT,
                         r"NT SERVICE\NayeonByokCustody")
        self.assertIn("User-scoped DPAPI",CANDIDATE_STORE_CRYPTO)
        self.assertIn("Service-SID",CANDIDATE_OS_BOUNDARY)
        self.assertIn("REJECT",CANDIDATE_MACHINE_DPAPI_AS_IS)

    def test_14_all_independent_G0_R3_signoffs_missing(self):
        self.assertGreaterEqual(len(G0_R3_UNRESOLVED),10)
        self.assertEqual(self.receipt.outstanding_external_decisions,
                         G0_R3_UNRESOLVED)

    def test_15_forged_reviewer_admin_WDAC_claims_cannot_mint_authority(self):
        self.assertFalse(proposed_service_store_admission(
            self.receipt,G0="GO",R3="GO",reviewer="self",
            signed_installer=True,wdac=True,all_gates=True))
        self.assertFalse(self.receipt.real_key_admissible)
        self.assertFalse(self.receipt.release_eligible)

    def test_16_migration_approval_claim_and_matching_user_can_never_migrate(self):
        self.assertFalse(authorize_cross_principal_user_vault_migration(
            self.receipt,user_confirmed=True,admin_approved=True,
            matching_current_user=True,signer=True))
        self.assertFalse(self.receipt.user_scope_key_migration_authorized)

    def test_17_protected_store_receipt_cannot_be_forged_positive(self):
        with self.assertRaises(ValueError):
            P216StoreReview(
                P216ReviewStatus.SOURCE_RISK_REQUIRES_OWNER_DECISION,
                3,True,True,True,True,tuple(),G0_R3_UNRESOLVED,
                protected_service_store_installed=True)

    def test_18_review_receipt_is_immutable_and_does_not_claim_OS_isolation(self):
        with self.assertRaises(FrozenInstanceError):
            self.receipt.release_eligible=True
        self.assertFalse(self.receipt.legacy_route_isolated_by_OS)
        self.assertFalse(self.receipt.machine_code_integrity_approved)
        self.assertFalse(self.receipt.trusted_user_presence_proven)


if __name__=="__main__":
    unittest.main()
