"""P183: genuine native Windows historical-policy equivalence gap and reviewer gate.

SOURCE-PRESERVING AUDIT. Reauthenticate P182 native 32/32 evidence, rerun
the original 32 cases + 12 new security-scope differential cases + 1
frozen historical BYOK B source-self witness. The test deliberately
proves where the P182 isolated OID-only transport is NOT historical
security-admission equivalent. Never treat gap-detection as approval,
alter original test/product code, or claim external review occurred.
"""
from __future__ import annotations

import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
import zipfile

from scripts import p180_windows_sealed_blob_transport_equivalence as p180
from scripts import p181_windows_batch_transport_security_review as p181
from scripts import p182_windows_fail_closed_batch_transport as p182
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
BASE="653cae658e057878a1c010a8dba486cc7f00cb5b"
BRANCH="byok-c1-p183-historical-security-equivalence-gate-20261112"
NEW={
 ".github/workflows/p183-windows-historical-security-equivalence.yml",
 "docs/byok-c1-p183-historical-security-equivalence-review.md",
 "scripts/p183_windows_historical_security_equivalence.py",
}
P182_ID=13986804363
P182_ZIP="F70932E5F47630F0C8E9E31388D9A82221A1B4CF99AC73ED9F6CCECE213664DC"
P182_LOG="p182_genuine_native_Windows_original_32_adversarial_cases.log"
P182_LOG_SHA="263E442E53D243D48CA89FB185E00EB0E4CC7A429150E97B04E7F70EB32A69B9"
P182_LEDGER="p182_source_preserving_Windows_fail_closed_batch_candidate_ledger.json"
REVIEWS={k:"OPEN" for k in
 ("GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}
LEGACY_SOURCE_PATHS=(
 "tests/phase_8_30_scope_migration.py",
 "tests/phase_8_34_scope_migration.py",
 "tests/phase_8_36_scope_migration.py",
 "tests/phase_8_37_scope_migration.py",
 "tests/phase8_byok_scope_migration.py",
 "tests/phase8_byok_b_scope_migration.py",
 "tests/test_phase8_byok_b_scope_integrity.py",
 "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
)
ISSUES={
 "TRANSPORT-P181-01":{
   "finding":"bounded Git batch read and compulsory termination on timeout",
   "candidate_tested":"YES_ISOLATED_P182",
   "original_history_equivalent":"NOT_CLAIMED",
   "external_security_decision":"OPEN",
 },
 "TRANSPORT-P181-02":{
   "finding":"protocol failure poisons and irreversibly retires session",
   "candidate_tested":"YES_ISOLATED_P182",
   "original_history_equivalent":"NOT_CLAIMED",
   "external_security_decision":"OPEN",
 },
 "HIST-01":{
   "finding":"per-request full original sealed commit/path/branch/index/HEAD and source authority",
   "candidate_tested":"NO_OID_ONLY_TRANSPORT",
   "original_history_equivalent":"NOT_ESTABLISHED",
   "external_security_decision":"OPEN",
 },
 "HIST-02":{
   "finding":"original entire immutable tag ancestry, Git tree, mode and SHA256 seal check on EVERY invocation",
   "candidate_tested":"NO_ORIGINAL_SEAL_EXECUTION",
   "original_history_equivalent":"NOT_ESTABLISHED",
   "external_security_decision":"OPEN",
 },
 "HIST-03":{
   "finding":"Win32 symlink/reparse/Unicode-case/ADS/parent replacement and racing writer denial",
   "candidate_tested":"NO_FULL_ORIGINAL_WIN32_POLICY",
   "original_history_equivalent":"NOT_ESTABLISHED",
   "external_security_decision":"OPEN",
 },
 "HIST-04":{
   "finding":"Git executable signature/caller origin, environment, lifecycle, privilege and peer admission",
   "candidate_tested":"PARTIAL_ENV_ONLY",
   "original_history_equivalent":"NOT_ESTABLISHED",
   "external_security_decision":"OPEN",
 },
 "REL-05":{
   "finding":"signed main/helper/installer/cert and WDAC/SAC policy owner GO",
   "candidate_tested":"NOT_APPLICABLE",
   "original_history_equivalent":"NOT_ESTABLISHED",
   "external_security_decision":"OPEN",
 },
 "REL-06":{
   "finding":"three complete unchanged full-product native Windows regressions and original historical FAIL dispositions",
   "candidate_tested":"NO",
   "original_history_equivalent":"ZERO_OF_THREE",
   "external_security_decision":"OPEN",
 },
 "REL-07":{
   "finding":"privileged C1 G0-G6, OS named-pipe peer/writer identity and release security GO",
   "candidate_tested":"NO",
   "original_history_equivalent":"NOT_ESTABLISHED",
   "external_security_decision":"OPEN",
 }
}

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=35,check=True).stdout

def custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P183 source-bound genuine clean Windows branch only")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P183 exactly three new reviewer-only additions required")
    for part in ("tests","nayeon"):
        if git("rev-parse",BASE+":"+part)!=git("rev-parse","HEAD:"+part):
            raise RuntimeError("P183 entire original historical test/product tree modified")
    for name in (
        "scripts/p180_windows_sealed_blob_transport_equivalence.py",
        "scripts/p181_windows_batch_transport_security_review.py",
        "scripts/p182_windows_fail_closed_batch_transport.py",
        *LEGACY_SOURCE_PATHS,
    ):
        if (ROOT/name).read_bytes()!=git("show",BASE+":"+name):
            raise RuntimeError("P183 historical or isolated baseline source changed "+name)
    mods=[v for v in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
          if re.fullmatch(r"tests/test_[^/]+\.py",v)]
    if len(mods)!=171:
        raise RuntimeError("P183 original 171 test modules changed")
    return {
        "exact_P183_HEAD":git("rev-parse","HEAD").decode().strip(),
        "exact_original_P182_parent":BASE,
        "exact_three_added_evidence_only_paths":sorted(NEW),
        "entire_product_and_frozen_test_source_unchanged":True,
        "P180_P181_P182_original_candidate_sources_unchanged":True,
        "frozen_tracked_original_test_modules":171,
        "original_historical_source_SHA256":{k:sha((ROOT/k).read_bytes()) for k in LEGACY_SOURCE_PATHS},
    }

def authenticate_P182(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P183 read-only ephemeral GitHub token unavailable")
    raw=_download_artifact(P182_ID,P182_ZIP,token)
    if sha(raw)!=P182_ZIP:
        raise RuntimeError("P183 original P182 hosted Windows ZIP SHA256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if (z.testzip() is not None or len(z.namelist())!=2
            or set(z.namelist())!={P182_LOG,P182_LEDGER}):
            raise RuntimeError("P183 original P182 artifact ZIP CRC/member identity mismatch")
        data=json.loads(z.read(P182_LEDGER))
        native=data.get("genuine_Windows_combined_native_result",{})
        logfile=z.read(P182_LOG)
        txt=logfile.decode("utf8","replace").replace("\r\n","\n")
        if (data.get("checkpoint")!="P182"
            or data.get("source_before")!=data.get("source_after")
            or data.get("source_before",{}).get("head")!=BASE
            or data.get("historical_H")!="HOLD"
            or data.get("production_R")!="HOLD"
            or data.get("accepted_complete_full_product_Windows_runs")!="0/3"
            or data.get("external_qualified_independent_security_decisions")!=REVIEWS
            or data.get("diagnostic_evidence_complete_not_a_release_security_approval") is not True
            or data.get("historical_security_verifier_modified") is not False
            or native.get("real_complete_unittest_count")!=32
            or native.get("real_process_exit")!=0
            or native.get("original_complete_native_log_SHA256")!=P182_LOG_SHA
            or sha(logfile)!=P182_LOG_SHA
            or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["32"]
            or not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P183 original P182 32/32 Windows native log or H/C/R state drift")
    return {
        "original_P182_artifact_ID":P182_ID,"authenticated_ZIP_SHA256":P182_ZIP,
        "original_native_32_of_32_combined_candidate_cases":"PASS",
        "native_original_full_product_Windows_acceptance":"0/3",
        "independent_qualified_security_review":"OPEN",
    }


class P183HistoricalEquivalenceAdversarialCases(unittest.TestCase):
    """A PASS identifies accurately which security controls remain OUTSIDE the transport."""

    def test_01_unmodified_legacy_seal_sources_are_git_tracked(self):
        for path in LEGACY_SOURCE_PATHS:
            with self.subTest(path=path):
                self.assertEqual((ROOT/path).read_bytes(),git("show",BASE+":"+path))

    def test_02_original_B_integrity_gate_is_not_called_by_OID_only_candidate(self):
        source=inspect.getsource(p182.FailClosedGitBatch.read)
        self.assertIn("old.verify_blob",source)
        self.assertNotIn("assert_byok_b_integrity",source)
        self.assertNotIn("_parent_tree",source)
        self.assertNotIn("git(\"show\"",source)
        self.assertNotIn("object_at(",source)

    def test_03_candidate_read_has_no_originating_commit_or_canonical_path_argument(self):
        params=inspect.signature(p182.FailClosedGitBatch.read).parameters
        self.assertEqual(tuple(params),("self","oid"))
        self.assertEqual(ISSUES["HIST-01"]["original_history_equivalent"],"NOT_ESTABLISHED")

    def test_04_actual_legacy_source_blobs_are_different_and_individually_identified(self):
        left,right=LEGACY_SOURCE_PATHS[4:6]
        a,_=p180.object_at(BASE,left)
        b,_=p180.object_at(BASE,right)
        self.assertNotEqual(a,b)
        self.assertEqual(p180.valid_oid(a),True)
        self.assertEqual(p180.valid_oid(b),True)
        self.assertNotEqual(git("show",BASE+":"+left),git("show",BASE+":"+right))

    def test_05_candidate_accepts_valid_Git_object_by_OID_without_historical_policy_context(self):
        # This is deliberately a GAP proof, NOT permission for integrating
        # into the sealed historical verifier.
        src="tests/phase8_byok_b_scope_migration.py"
        oid,_=p180.object_at(BASE,src)
        subject=p182.FailClosedGitBatch(timeout_seconds=4)
        try:
            self.assertEqual(subject.read(oid),git("show",BASE+":"+src))
        finally:
            subject.close()
        self.assertEqual(ISSUES["HIST-01"]["candidate_tested"],"NO_OID_ONLY_TRANSPORT")

    def test_06_stale_or_tampered_payload_cannot_be_accepted_as_original_OID(self):
        source=b"historical trusted source"
        oid=p182._blob_oid(source)
        tampered=source+b"tamper"
        p=p182._FakePipeProcess(p182._frame(oid,tampered))
        s=p182.FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):
            s.read(oid)
        self.assertTrue(s.retired)
        self.assertTrue(p.killed)

    def test_07_original_legacy_branch_and_tree_logic_retained_but_not_integrated(self):
        orig=(ROOT/"tests/phase8_byok_b_scope_migration.py").read_text(encoding="utf8")
        self.assertIn("assert_byok_b_integrity",orig)
        self.assertIn("_parent_tree",orig)
        self.assertIn("PARENT",orig)
        new=inspect.getsource(p182.FailClosedGitBatch)
        self.assertNotIn("assert_byok_b_integrity",new)
        self.assertEqual(ISSUES["HIST-02"]["original_history_equivalent"],"NOT_ESTABLISHED")

    def test_08_original_windows_alias_and_reparse_policy_not_waived(self):
        orig=(ROOT/"tests/phase_8_30_scope_migration.py").read_text(encoding="utf8")
        self.assertIn("_reject_linked_parents",orig)
        self.assertIn("_production_git_path",orig)
        for bad in ("tests/../other","tests\\evil","Tests/alias","nayeon/a:ads"):
            self.assertFalse(p180.valid_path(bad))
        self.assertEqual(ISSUES["HIST-03"]["original_history_equivalent"],"NOT_ESTABLISHED")

    def test_09_candidate_does_not_issue_code_integrity_or_signer_GO(self):
        from nayeon.desktop_alpha import frozen_signed_byok_companion as old_policy
        self.assertEqual(old_policy._APPROVED_MAIN_SHA256,"")
        self.assertEqual(old_policy._APPROVED_COMPANION_SHA256,"")
        self.assertEqual(old_policy._APPROVED_SIGNER_CERT_SHA256,"")
        self.assertFalse(old_policy._APPROVED_CODE_INTEGRITY_RELEASE)
        self.assertEqual(ISSUES["REL-05"]["external_security_decision"],"OPEN")

    def test_10_candidate_deadline_and_retirement_are_transport_only(self):
        fake=p182._FakePipeProcess(stalled=True)
        b=p182.FailClosedGitBatch(process=fake,timeout_seconds=0.04)
        t=time.monotonic()
        with self.assertRaises(TimeoutError):
            b.read(b"a"*40)
        self.assertLess(time.monotonic()-t,1)
        self.assertTrue(fake.killed)
        self.assertTrue(b.retired)
        self.assertEqual(ISSUES["TRANSPORT-P181-01"]["candidate_tested"],"YES_ISOLATED_P182")

    def test_11_no_Full_Windows_3_of_3_and_privileged_G0_through_G6(self):
        self.assertEqual(ISSUES["REL-06"]["original_history_equivalent"],"ZERO_OF_THREE")
        self.assertEqual(ISSUES["REL-07"]["candidate_tested"],"NO")
        self.assertEqual(set(REVIEWS),{"GOV-01","GOV-02","SEC-03","SEC-04",
                                      "REL-05","REL-06","REL-07"})

    def test_12_all_nine_reviewer_risks_have_open_disposition(self):
        self.assertEqual(len(ISSUES),9)
        self.assertTrue(all(v["external_security_decision"]=="OPEN" for v in ISSUES.values()))
        self.assertEqual(sum(v["candidate_tested"]=="YES_ISOLATED_P182" for v in ISSUES.values()),2)
        self.assertTrue(all(v["original_history_equivalent"]!="GO" for v in ISSUES.values()))


def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p183-historical-equivalence"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P183","historical_H":"HOLD",
        "current_C":"REVIEW_PREPARATION_AND_EQUIVALENCE_GAP_ONLY",
        "production_R":"HOLD","accepted_complete_full_product_native_Windows":"0/3",
        "qualified_independent_security_review":"NOT_REQUESTED_NOT_SIGNED",
        "independent_external_decisions":REVIEWS,
        "historical_original_security_assertions_waived":False,
        "original_P135_3x600s_timeouts":"UNWAIVED",
        "original_P175_five_historical_failing_cases":"UNWAIVED",
        "original_P178_BYOK_B_165s_timeout_and_two_FAIL":"UNWAIVED",
        "original_P179_pin_witness_130s_timeout":"UNWAIVED",
        "privileged_C1_G0_G6":"OPEN","signed_main_helper_installer_certificate_GO":False,
        "transport_security_candidate_integrated_into_original_verifier":False,
        "reviewer_scope_matrix":ISSUES,
    }
    accepted=False
    try:
        before=custody()
        ledger["exact_source_before"]=before
        ledger["authenticated_genuine_P182_windows_log"]=authenticate_P182(
            os.environ.get("P183_EVIDENCE_TOKEN",""))
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for key in list(env):
            if (key in {"P183_EVIDENCE_TOKEN","GITHUB_TOKEN","GH_TOKEN"}
                or key.endswith("_SECRET") or key.endswith("_API_KEY")):
                env.pop(key,None)
        log=out/"p183_original_genuine_Windows_45_regression_and_review_cases.log"
        selectors=[
           "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests",
           "scripts.p181_windows_batch_transport_security_review.P181BatchAdversarialSecurityTests",
           "scripts.p182_windows_fail_closed_batch_transport.P182FailClosedBatchSecurityCases",
           "scripts.p183_windows_historical_security_equivalence.P183HistoricalEquivalenceAdversarialCases",
           "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_self_canonicalization_only_zeros_own_single_literal",
        ]
        with log.open("wb") as f:
            native=subprocess.run(
                [sys.executable,"-B","-m","unittest","-v",*selectors],
                stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                env=env,cwd=ROOT,timeout=120,check=False)
        raw=log.read_bytes()
        text=raw.decode("utf8","replace").replace("\r\n","\n")
        footer=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)
        ledger["authentic_original_Windows_tests"]={
            "source_selectors":selectors,
            "original_P180_tests":8,
            "original_P181_tests":12,
            "original_P182_tests":12,
            "P183_new_gap_discovery_tests":12,
            "original_frozen_BYOK_B_self_control":1,
            "complete_native_case_count":int(footer[-1]) if footer else None,
            "native_exit":native.returncode,
            "raw_log_SHA256":sha(raw),
            "raw_log_filename":log.name,
            "original_fail_and_error_records":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M),
        }
        if native.returncode!=0 or footer!=["45"] or not re.search(r"^OK\s*$",text,re.M):
            raise RuntimeError("P183 original Windows 45-case negative/equivalence review suite not all complete")
        ledger["exact_source_after"]=custody()
        accepted=(before==ledger["exact_source_after"])
        if not accepted:raise RuntimeError("P183 source changed between before and after native review")
        print("P183_ACTUAL_WINDOWS_NATIVE_EQUIVALENCE_GAP_TESTS=45/45_PASS|EXIT=0",flush=True)
        print("P183_REAL_ORIGINAL_BYOK_B_CONTROL=1/1_PASS",flush=True)
        print("P183_P182_TRANSPORT_MITIGATION_ISOLATED=2|ORIGINAL_HISTORICAL_EQUIVALENCE=NOT_ESTABLISHED",flush=True)
        print("P183_UNRESOLVED_HISTORICAL_SECURITY_AND_RELEASE_REVIEW_ROWS=7",flush=True)
        print("P183_REVIEWER_DECISIONS_QUALIFIED_EXTERNAL=SEVEN_OPEN|NO_SIGNOFF",flush=True)
        print("P183_NATIVE_LOG_SHA256="+sha(raw),flush=True)
        print("P183_FULL_NATIVE_PRODUCT_WINDOWS=0/3|PRODUCTION_R=HOLD",flush=True)
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P183_EQUIVALENCE_REVIEW_AND_WINDOWS_NATIVE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["source_bound_reviewer_packet_generated_not_qualified_security_signoff"]=accepted
        (out/"p183_historical_security_equivalence_reviewer_decision_packet.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if accepted else 1

if __name__=="__main__":
    raise SystemExit(main())
