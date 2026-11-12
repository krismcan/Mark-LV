"""P177 — Qualified reviewer intake evidence consolidation (NOT approval).

Runs ONLY in an authenticated hosted Windows push for an isolated 3-file
audit-only branch. Re-downloads, hashes, parses and authenticates the complete
P174/P175/P176 real native evidence. Produces immutable H/C/R review questions,
genuine independent Windows 9-test contract log and negative release posture.
No product edits, frozen test waivers, credentials, or production release.
"""
from __future__ import annotations

import ast
import hashlib
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

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from scripts.p175_windows_current_source_security_candidate import authenticate_p174_archive
from scripts.p176_windows_adversarial_current_policy import (
    authenticate_p175, GROUPS as P175_GROUPS, REVIEWS,
)

ROOT=Path(__file__).resolve().parents[1]
BRANCH="byok-c1-p177-qualified-review-evidence-consolidation-20261112"
P176="ea77c8115c68520a08d3f259f994354cfa1d0601"
P175="381abcf4976dd01736bb542533c837e9afa66a56"
P174="98437f4c4e8a09b507bc998a2829bafcc430f8a7"
P173="b04af8858dbaab6d164352832c6757db0ec1681c"
P140="9c47bac3308822e11300381017b30e913ffbc211"
NEW={
    "scripts/p177_windows_qualified_review_evidence_packet.py",
    "docs/byok-c1-p177-qualified-independent-review-submission.md",
    ".github/workflows/p177-windows-qualified-review-evidence.yml",
}
PRIOR_DIFF={
    (P173,P174):{
        ".github/workflows/p174-windows-sealed-era-scope-governance.yml",
        "docs/byok-c1-p174-sealed-era-scope-governance-decision-ledger.md",
        "scripts/p174_windows_sealed_era_scope_governance.py",
    },
    (P174,P175):{
        ".github/workflows/p175-windows-current-source-security-candidate.yml",
        "docs/byok-c1-p175-versioned-current-candidate-security-review.md",
        "scripts/p175_windows_current_source_security_candidate.py",
    },
    (P175,P176):{
        ".github/workflows/p176-windows-adversarial-current-policy.yml",
        "docs/byok-c1-p176-adversarial-current-policy-review.md",
        "scripts/p176_windows_adversarial_current_policy.py",
    },
}
P176_ARTIFACT=13959548133
P176_ZIP_SHA="A8E0F8B030C5B8579CAB97A5EA2D6B3C64C74C4E5EA49D5C35D539179C983D7B"
P174_ARTIFACT=13957432345
P175_ARTIFACT=13959541839
P174_ZIP_SHA="D91607E9076A488F32023D257F106F0FB70A4AC5D408B38A870AC68F6E1A2853"
P175_ZIP_SHA="14D1D41E81E9CD1466C2D58244AE55B2C1C54A64D52BF398D79B381202D569BD"
P176_LOG="p176_actual_original_windows_adversarial_candidate_11.log"
P176_LEDGER="p176_authenticated_adversarial_security_governance_ledger.json"
FOOTER=re.compile(r"^Ran (\d+) tests? in [0-9.]+s$",re.M)
FAILS=re.compile(r"^(FAIL|ERROR): (.+)$",re.M)
REVIEW_SCOPE={
    "GOV-01":{
        "authority":"Independent frozen historical-test and source-era governance reviewer",
        "question":"Determine authentic P140 six-path baseline applicability on P173+ and the Phase8.31 vs P86 UI-import contradiction without rewriting original test predicates",
        "evidence":"P174 original P140 6/6 PASS vs later P173 original 5 PASS / 1 FAIL; P175 original Phase8.31 import test FAIL",
        "required_to_close":"Named accountable reviewer, signed versioned applicability determination and original H FAIL disposition; separately reviewed successor acceptance only",
    },
    "GOV-02":{
        "authority":"Independent UI security / human-presence reviewer",
        "question":"Adjudicate P133 explicit offline third button vs old P86/P87 exact two-button assertions",
        "evidence":"P175 genuine P133 original 25/25 PASS, live Tk 1/1 PASS, original P86 2 FAIL and P87 1 FAIL",
        "required_to_close":"Documented explicit user-click authority, no implicit launch/effects, test-version transition decision without old-test waiver",
    },
    "SEC-03":{
        "authority":"Independent secret-dataflow / Windows Credential Manager security reviewer",
        "question":"Approve or reject the exact three additional new local-user credential import edges and rogue-import negatives",
        "evidence":"P175 original fake-native WinCred 20/20 PASS; old fixed-consumer original FAIL; P176 current 11/11 adversarial PASS",
        "required_to_close":"Approved exact source/data-flow manifest, trust boundary and denial coverage; no broadened historical allowlist",
    },
    "SEC-04":{
        "authority":"Qualified independent Python/Tk creator-thread and import-time security reviewer",
        "question":"Decide whether P171 scratch-only first-AST guard and docstring restoration are acceptable as a later product proposal",
        "evidence":"Earlier P171 diagnostic evidence is referenced but NOT reauthenticated by P177; no product change in P174-P177",
        "required_to_close":"Independent source review of P171 native original lifecycle, worker-thread negatives, __doc__ integrity and safe import-time behaviour",
    },
    "REL-05":{
        "authority":"Windows publisher signer and SAC/WDAC Code Integrity policy owner",
        "question":"Provide signed and pinned installed main/helper/installer and genuine image-load policy acceptance",
        "evidence":"P140 real source has empty approved parent/helper/signer cert pins and Code Integrity release false; P175/P176 negatives confirm fail-closed",
        "required_to_close":"Actual signed binary and cert SHA, verified Authenticode, protected install, independent SAC/WDAC image-load attestation and owner GO",
    },
    "REL-06":{
        "authority":"Independent full-product native Windows QA/release owner",
        "question":"Resolve original P135 full-product three native 600-second timeout results, then execute three unfiltered full regressions",
        "evidence":"P174-P176 were focused native diagnostics only, not any accepted complete full-product regressions",
        "required_to_close":"Three complete native source-matched full-product Windows regressions, genuine exit codes, entire logs and SHA256, independently reviewed",
    },
    "REL-07":{
        "authority":"Independent privileged service and C1 security owner",
        "question":"Close genuine G0-G6 admission controls including P96 race and P124 pipe writer provenance before privileged service",
        "evidence":"No privileged service, real user key, provider validation or native Credential Manager effects in P174-P177",
        "required_to_close":"Named independent security owner acceptance of all G0-G6 and human custody; no service enablement by current user-scope diagnostics",
    },
}
SENSITIVE={"GITHUB_TOKEN","GH_TOKEN","P177_REVIEW_TOKEN","OPENAI_API_KEY",
           "AZURE_OPENAI_API_KEY","ANTHROPIC_API_KEY","ACTIONS_RUNTIME_TOKEN",
           "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40,check=True).stdout

def source_custody()->dict:
    _guard_runner()
    if (sys.platform!="win32"
        or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P177 must run on authenticated clean GitHub-hosted Windows push")
    expected={(P176,git("rev-parse","HEAD").decode().strip()):NEW,**PRIOR_DIFF}
    prior=[P173,P174,P175,P176]
    for parent,child in zip(prior,prior[1:]):
        if git("merge-base",parent,child).decode().strip()!=parent:
            raise RuntimeError("P177 unverified immutable historical provenance")
    head=git("rev-parse","HEAD").decode().strip()
    if (git("merge-base",P176,head).decode().strip()!=P176
        or git("rev-parse",P176+":nayeon")!=git("rev-parse","HEAD:nayeon")
        or git("rev-parse",P176+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P177 parent mismatch or product/tests modified")
    for (parent,child),paths in expected.items():
        diff=set(git("diff","--name-only",parent,child).decode().splitlines())
        if diff!=paths or any(git("ls-tree","--name-only",parent,"--",p).strip() for p in diff):
            raise RuntimeError("P177 old or new diff contains non-additive source: "+parent)
        if (git("rev-parse",parent+":nayeon")!=git("rev-parse",child+":nayeon")
            or git("rev-parse",parent+":tests")!=git("rev-parse",child+":tests")):
            raise RuntimeError("P177 product/test tree mutated across source era")
    protected=("tests/test_p140_scope_migration.py",
               "tests/test_p140_frozen_signed_companion.py",
               "tests/test_phase8_byok_c1_p76_scope.py",
               "tests/test_windows_credential_backend.py",
               "nayeon/brain/local_byok_user_scope.py",
               "nayeon/desktop_alpha/local_byok_window.py",
               "nayeon/desktop_alpha/frozen_signed_byok_companion.py")
    for p in protected:
        raw=git("show","HEAD:"+p)
        if raw!=git("show",P176+":"+p) or raw!=(ROOT/p).read_bytes():
            raise RuntimeError("P177 protected source not original Git blob: "+p)
    for p in protected[:2]:
        if git("rev-parse",P140+":"+p)!=git("rev-parse","HEAD:"+p):
            raise RuntimeError("P177 original frozen P140 test blob mismatch")
    tests=[p for p in git("ls-tree","-r","--name-only",P176,"--","tests").decode().splitlines()
           if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(tests)!=171:
        raise RuntimeError("P177 171 original tests inventory drift")
    return {"P177_exact_head":head,"P176_parent":P176,
            "authenticated_prior_chain":prior,
            "three_additive_P177_audit_only_paths":sorted(NEW),
            "all_4_consecutive_audit_only_source_diffs_preserved":True,
            "original_nayeon_and_tests_subtrees_bit_identical":True,
            "original_frozen_P140_test_blobs_preserved":True,
            "original_test_module_inventory":171}

def read_frozen_release_pins()->dict:
    p=ROOT/"nayeon/desktop_alpha/frozen_signed_byok_companion.py"
    tree=ast.parse(p.read_text(encoding="utf8"),filename=str(p))
    names={"_APPROVED_MAIN_SHA256","_APPROVED_COMPANION_SHA256",
           "_APPROVED_SIGNER_CERT_SHA256","_APPROVED_CODE_INTEGRITY_RELEASE"}
    found={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in names:
                    if target.id in found:
                        raise RuntimeError("P177 duplicate frozen launch approval literal")
                    found[target.id]=ast.literal_eval(node.value)
    if found!={n:("" if n!="_APPROVED_CODE_INTEGRITY_RELEASE" else False) for n in names}:
        raise RuntimeError("P177 actual frozen signed-launch source no longer HOLD")
    return found

def authenticate_p176(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P177 read-only archive token required")
    raw=_download_artifact(P176_ARTIFACT,P176_ZIP_SHA,token)
    if sha(raw)!=P176_ZIP_SHA:
        raise RuntimeError("P177 P176 original archived ZIP SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or z.namelist() not in (
                [P176_LOG,P176_LEDGER],[P176_LEDGER,P176_LOG]):
            raise RuntimeError("P177 P176 ZIP CRC or exact 2-member inventory mismatch")
        original=z.read(P176_LOG)
        ledger=json.loads(z.read(P176_LEDGER))
        rendered=original.decode("utf8","replace").replace("\r\n","\n")
        matches=FOOTER.findall(rendered)
        issues=FAILS.findall(rendered)
        native=ledger.get("actual_Windows_p176_candidate",{})
        custody=ledger.get("exact_source_custody",{})
        if (ledger.get("checkpoint")!="P176"
            or custody.get("authentic_P176_head")!=P176
            or ledger.get("source_custody_after")!=custody
            or ledger.get("independent_review")!=REVIEWS
            or ledger.get("historical_H")!="HOLD"
            or ledger.get("current_C")!="ADVERSARIAL_CANDIDATE_ONLY"
            or ledger.get("release_R")!="HOLD"
            or ledger.get("full_product_accepted_Windows")!="0/3"
            or ledger.get("real_key_or_native_credentials")!="NOT_ATTEMPTED"
            or len(matches)!=1 or int(matches[0])!=11
            or issues or not re.search(r"^OK\s*$",rendered,re.M)
            or native.get("original_count")!=11 or native.get("native_exit")!=0
            or native.get("original_raw_log")!=P176_LOG
            or native.get("named_FAIL_ERROR")!=[]
            or native.get("SHA256")!=sha(original)):
            raise RuntimeError("P177 P176 genuine native 11/11 evidence or release hold changed")
        if ledger.get("prior_P175_original_Windows_archive",{}).get(
            "verified_ZIP_SHA256")!=P175_ZIP_SHA:
            raise RuntimeError("P177 P176 original P175 authenticated prior archive link missing")
    return {"P176_artifact_ID":P176_ARTIFACT,"P176_archive_sha256":sha(raw),
            "genuine_Windows_11_case_native_count":11,"actual_native_exit":0,
            "complete_stdout_stderr_SHA256":sha(original),
            "actual_unfiltered_native_FAIL_ERROR":[],
            "P175_prior_archive_chain_in_P176":"VERIFIED"}

def collected_contracts(sources:dict)->dict:
    p174=sources["P174"]
    p175=sources["P175"]
    p176=sources["P176"]
    older=p174["authenticated_four_unchanged_original_Windows_source_era_runs"]
    expected={
        "P140_original_P140_scope_migration_6":("PASS",6,0),
        "P140_original_P140_frozen_signed_companion_24":("PASS",24,0),
        "P173_original_P140_scope_migration_6":("HOLD",6,1),
        "P173_original_P140_frozen_signed_companion_24":("PASS",24,0),
    }
    if set(older)!=set(expected):
        raise RuntimeError("P177 four source-era original runs missing")
    for name,(status,count,exit_code) in expected.items():
        row=older[name]
        if (row["original_status"]!=status or row["count"]!=count
            or row["native_exit"]!=exit_code):
            raise RuntimeError("P177 P174 historical P140 native outcome altered")
    if not any("test_exact_p139_ancestry_and_approved_six_path_change" in e["name"]
               for e in older["P173_original_P140_scope_migration_6"]["named_fail_errors"]):
        raise RuntimeError("P177 authentic original P173 historical FAIL was waived")
    groups=p175["original_nine_unfiltered_Windows_log_groups"]
    if set(groups)!=set(P175_GROUPS):
        raise RuntimeError("P177 P175 targeted groups changed")
    pass_count=sum(row["count"] for row in groups.values() if row["status"]=="PASS")
    hold_count=sum(row["count"] for row in groups.values() if row["status"]=="HOLD")
    fail_records=sum(len(row["actual_named_FAIL_ERROR"]) for row in groups.values()
                     if row["status"]=="HOLD")
    if pass_count!=55 or hold_count!=5 or fail_records!=6:
        raise RuntimeError("P177 P175 H/C count and failure inventory drift")
    if (p176["genuine_Windows_11_case_native_count"]!=11
        or p176["actual_native_exit"]!=0):
        raise RuntimeError("P177 P176 original adversarial native count not genuine")
    return {"P174_historical_P140_vs_descendant_complete_original_4_groups":older,
            "P175_9_authentic_native_targeted_groups":groups,
            "P175_55_pass_and_5_genuine_historical_hold":{
                "actual_passed_native_cases":pass_count,
                "original_cases_executed_with_HOLD":hold_count,
                "native_fail_error_records_retained":fail_records},
            "P176_11_complete_native_adversarial_pass":{
                "count":11,"native_exit":0,"raw_SHA256":p176["complete_stdout_stderr_SHA256"]}}

def review_rows()->dict:
    if set(REVIEW_SCOPE)!=set(REVIEWS) or len(REVIEW_SCOPE)!=7:
        raise RuntimeError("P177 seven independent review decisions incomplete")
    return {name:dict(spec,decision="OPEN",reviewer_identity=None,
                      signed_attestation=None,accepted_security_GO=False,
                      must_not_infer_authority_from_Windows_runner=True)
            for name,spec in REVIEW_SCOPE.items()}

def release_diagnostic_admissible(packet:dict)->bool:
    """A *documentation-only* necessary-condition test, never release authority."""
    rows=packet.get("independent_qualified_review_decisions",{})
    pins=packet.get("authentic_P140_frozen_signed_release_source_pins",{})
    if (set(rows)!=set(REVIEW_SCOPE) or
        any(x.get("decision")!="SIGNED_APPROVED" or
            x.get("signed_attestation") is None or
            x.get("accepted_security_GO") is not True for x in rows.values())
        or packet.get("accepted_complete_full_product_Windows_regressions")!="3/3"
        or pins.get("_APPROVED_CODE_INTEGRITY_RELEASE") is not True
        or not all(isinstance(pins.get(n),str) and
                    re.fullmatch(r"[a-f0-9]{64}",pins[n]) for n in (
           "_APPROVED_MAIN_SHA256","_APPROVED_COMPANION_SHA256",
           "_APPROVED_SIGNER_CERT_SHA256"))
        or packet.get("privileged_C1_G0_to_G6")!="INDEPENDENTLY_APPROVED"):
        return False
    return True

class P177NativeReviewerPacketContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(Path(os.environ["P177_PACKET_PATH"]).read_text(encoding="utf8"))

    def test_01_exact_source_chain_and_no_product_writes(self):
        s=self.data["source_custody_before"]
        self.assertEqual(s["P176_parent"],P176)
        self.assertEqual(s["original_test_module_inventory"],171)
        self.assertTrue(s["original_nayeon_and_tests_subtrees_bit_identical"])
        self.assertEqual(set(s["three_additive_P177_audit_only_paths"]),NEW)

    def test_02_all_three_authentic_original_archive_sha256_receipts(self):
        receipts=self.data["authenticated_original_Windows_archives"]
        self.assertEqual(receipts["P174"]["P174_ZIP_SHA256"],P174_ZIP_SHA)
        self.assertEqual(receipts["P175"]["verified_ZIP_SHA256"],P175_ZIP_SHA)
        self.assertEqual(receipts["P176"]["P176_archive_sha256"],P176_ZIP_SHA)

    def test_03_historical_p140_scope_pass_and_descendant_fail_unwaived(self):
        rows=self.data["authentic_historical_and_current_native_outcomes"][
            "P174_historical_P140_vs_descendant_complete_original_4_groups"]
        self.assertEqual(rows["P140_original_P140_scope_migration_6"]["original_status"],"PASS")
        self.assertEqual(rows["P173_original_P140_scope_migration_6"]["original_status"],"HOLD")
        self.assertEqual(rows["P173_original_P140_scope_migration_6"]["native_exit"],1)

    def test_04_original_five_historical_HOLD_distinct_from_passed_cases(self):
        rows=self.data["authentic_historical_and_current_native_outcomes"][
            "P175_55_pass_and_5_genuine_historical_hold"]
        self.assertEqual(rows["actual_passed_native_cases"],55)
        self.assertEqual(rows["original_cases_executed_with_HOLD"],5)
        self.assertEqual(rows["native_fail_error_records_retained"],6)

    def test_05_current_adversarial_eleven_genuine_native_cases(self):
        p=self.data["authentic_historical_and_current_native_outcomes"][
            "P176_11_complete_native_adversarial_pass"]
        self.assertEqual(p["count"],11)
        self.assertEqual(p["native_exit"],0)

    def test_06_all_seven_qualified_reviewers_missing_signed_GO(self):
        rows=self.data["independent_qualified_review_decisions"]
        self.assertEqual(set(rows),set(REVIEW_SCOPE))
        self.assertTrue(all(x["decision"]=="OPEN" and
                            x["signed_attestation"] is None and
                            not x["accepted_security_GO"] for x in rows.values()))

    def test_07_real_source_signing_and_Code_Integrity_release_still_refused(self):
        pins=self.data["authentic_P140_frozen_signed_release_source_pins"]
        self.assertEqual(pins["_APPROVED_MAIN_SHA256"],"")
        self.assertEqual(pins["_APPROVED_COMPANION_SHA256"],"")
        self.assertEqual(pins["_APPROVED_SIGNER_CERT_SHA256"],"")
        self.assertIs(pins["_APPROVED_CODE_INTEGRITY_RELEASE"],False)

    def test_08_production_gate_and_full_original_regression_remain_HOLD(self):
        d=self.data
        self.assertEqual(d["historical_H"],"HOLD")
        self.assertEqual(d["current_C"],"SOURCE_BOUND_FOCUSED_DIAGNOSTIC_PENDING_QUALIFIED_REVIEW")
        self.assertEqual(d["production_R"],"HOLD")
        self.assertEqual(d["accepted_complete_full_product_Windows_regressions"],"0/3")
        self.assertEqual(d["privileged_C1_G0_to_G6"],"OPEN")
        self.assertFalse(release_diagnostic_admissible(d))

    def test_09_in_memory_single_fake_GO_cannot_bypass_remainder(self):
        d=json.loads(json.dumps(self.data))
        r=d["independent_qualified_review_decisions"]["SEC-03"]
        r["decision"]="SIGNED_APPROVED"
        r["signed_attestation"]="synthetic_not_a_real_signoff"
        r["accepted_security_GO"]=True
        self.assertFalse(release_diagnostic_admissible(d))
        d["accepted_complete_full_product_Windows_regressions"]="3/3"
        self.assertFalse(release_diagnostic_admissible(d))

def main()->int:
    evidence=Path(os.environ["RUNNER_TEMP"])/"nayeon-p177-qualified-review-submission"
    evidence.mkdir(parents=True,exist_ok=True)
    packet={"checkpoint":"P177","evidence":"COLLECTED_NOT_APPROVED",
            "historical_H":"HOLD",
            "current_C":"SOURCE_BOUND_FOCUSED_DIAGNOSTIC_PENDING_QUALIFIED_REVIEW",
            "production_R":"HOLD",
            "accepted_complete_full_product_Windows_regressions":"0/3",
            "privileged_C1_G0_to_G6":"OPEN",
            "historic_P135_3x600_second_full_product_timeouts":"PRESERVED_UNWAIVED",
            "real_API_key_CredRead_CredWrite_CredDelete_or_provider":"NOT_ATTEMPTED",
            "actual_signed_installer_or_SAC_WDAC_owner_GO":"NOT_OBTAINED",
            "no_independent_qualified_reviewer_signed_GO":True,
            "no_merge_tag_shipment_or_Google_Drive_release_status_change":True}
    result=1
    try:
        before=source_custody()
        packet["source_custody_before"]=before
        token=os.environ.get("P177_REVIEW_TOKEN","")
        p174=authenticate_p174_archive(token)
        p175=authenticate_p175(token)
        p176=authenticate_p176(token)
        sources={"P174":p174,"P175":p175,"P176":p176}
        packet["authenticated_original_Windows_archives"]=sources
        packet["authentic_historical_and_current_native_outcomes"]=collected_contracts(sources)
        packet["independent_qualified_review_decisions"]=review_rows()
        packet["authentic_P140_frozen_signed_release_source_pins"]=read_frozen_release_pins()
        if release_diagnostic_admissible(packet):
            raise RuntimeError("P177 apparent production approval fabricated")
        # Store a reviewer-readable file; preserve report even if the native
        # contract process fails, but never claim successful packet then.
        packet_path=evidence/"p177_source_bound_qualified_independent_review_packet.json"
        packet_path.write_text(json.dumps(packet,sort_keys=True,indent=2)+"\n",encoding="utf8")
        env=os.environ.copy()
        for k in list(env):
            if k in SENSITIVE or k.endswith("_API_KEY") or k.endswith("_SECRET"):
                env.pop(k,None)
        env.update({"P177_PACKET_PATH":str(packet_path),
                    "PYTHONDONTWRITEBYTECODE":"1"})
        log=evidence/"p177_real_Windows_nine_case_review_contract.log"
        with log.open("wb") as f:
            try:
                p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                    "scripts.p177_windows_qualified_review_evidence_packet.P177NativeReviewerPacketContract"],
                    cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                    stderr=subprocess.STDOUT,timeout=100,check=False)
                exit_code=p.returncode
            except subprocess.TimeoutExpired:
                exit_code=124
        raw=log.read_bytes()
        body=raw.decode("utf8","replace").replace("\r\n","\n")
        foot=FOOTER.findall(body)
        count=int(foot[-1]) if foot else None
        failures=FAILS.findall(body)
        packet["P177_actual_original_Windows_review_contract"]={
            "original_case_count":count,"native_exit":exit_code,
            "named_FAIL_ERROR":[{"kind":k,"original_id":name} for k,name in failures],
            "genuine_stdout_stderr_filename":log.name,
            "raw_log_SHA256":sha(raw)}
        packet["source_custody_after"]=source_custody()
        success=(count==9 and exit_code==0 and not failures
                 and re.search(r"^OK\s*$",body,re.M) is not None
                 and before==packet["source_custody_after"])
        packet["review_submission_packet_prepared_but_not_sent"]=success
        if not success:
            raise RuntimeError("P177 actual nine-case native Windows original review contract incomplete")
        print("P177_3_PRIOR_WINDOWS_ARCHIVES_SHA256_AUTHENTICATED=YES",flush=True)
        print("P177_P174_HISTORICAL_ORIGINAL_P140_6_PASS_P173_5_PASS_1_FAIL=RETAINED",flush=True)
        print("P177_P175_55_CURRENT_PASS_AND_5_HISTORICAL_HOLD=UNWAIVED",flush=True)
        print("P177_P176_CURRENT_ADVERSARIAL_NATIVE_11_PASS=VERIFIED",flush=True)
        print("P177_WINDOWS_REVIEW_CONTRACT="+str(count)+"/9|EXIT="+str(exit_code)+
              "|RAW_LOG_SHA256="+sha(raw),flush=True)
        print("P177_7_INDEPENDENT_QUALIFIED_REVIEW_DECISIONS=OPEN",flush=True)
        print("P177_REVIEW_PACKET=PREPARED_NOT_SUBMITTED_TO_EXTERNAL_REVIEWERS",flush=True)
        print("P177_PRODUCTION_R=HOLD|FULL_PRODUCT_ACCEPTED_WINDOWS=0/3",flush=True)
        result=0
    except Exception as exc:
        packet["collector_failure"]=repr(exc)
        packet["review_submission_packet_prepared_but_not_sent"]=False
        print("P177_SOURCE_OR_ARCHIVE_OR_NATIVE_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        (evidence/"p177_source_bound_qualified_independent_review_packet.json").write_text(
            json.dumps(packet,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return result

if __name__=="__main__":
    raise SystemExit(main())
