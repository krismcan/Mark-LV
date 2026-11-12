"""P184 source-bound fresh read admission proof, NOT production verifier.

This isolated audit-only candidate wraps the P182 bounded Git blob transport
with live, double-observed HEAD/branch/index/tree/disk SHA256 admission for
two explicitly pinned historical source files. Mocked pre/post drift tests
never alter source. These narrow guards do NOT establish full historic seal,
tags, Windows race/peer, signatures or user-scoped production release.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import unittest
import zipfile

from scripts import p180_windows_sealed_blob_transport_equivalence as p180
from scripts import p182_windows_fail_closed_batch_transport as p182
from scripts import p183_windows_historical_security_equivalence as p183
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
BASE="c450307d414aae3fe87b7c027a151073e9de2a08"
BRANCH="byok-c1-p184-fresh-historical-source-admission-20261112"
NEW={
 ".github/workflows/p184-windows-fresh-historical-source-admission.yml",
 "docs/byok-c1-p184-fresh-historical-source-admission.md",
 "scripts/p184_windows_fresh_historical_source_admission.py",
}
P183_ID=13987763174
P183_ZIP="F51ADF001521A7D1CFC4C4228C030519FE2BA98D2862EB2EEEC3CB8F236D8DCD"
P183_LOG="p183_original_genuine_Windows_45_regression_and_review_cases.log"
P183_LOG_SHA="D1D504877CCC61FE2DA571EF27E52C6B4950363FE80DA9115A1F0912D6DDC3F4"
P183_LEDGER="p183_historical_security_equivalence_reviewer_decision_packet.json"
REVIEWS={x:"OPEN" for x in (
 "GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}
PINNED={
 "tests/phase8_byok_b_scope_migration.py":"84CED2F31F5DAF985DE462C384ABDFE47F8B705425F8BDEFB8CF1E04E56EE010",
 "tests/phase_8_30_scope_migration.py":"F9AA8C8DF0144C83BAA4EDC8CC8D5F99CE5221C8C1263B13378FEAEB87060487",
}
HEX40=re.compile(r"[0-9a-f]{40}\Z")
HEX64=re.compile(r"[A-F0-9]{64}\Z")
STAGE=re.compile(rb"^100644 ([0-9a-f]{40}) 0\t([a-zA-Z0-9_./-]+)\n$")

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(
        ["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,
        timeout=35).stdout

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
        raise RuntimeError("P184 requires clean authenticated actual Windows exact source")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",path).strip()
                          for path in NEW):
        raise RuntimeError("P184 only three new read-only experimental paths allowed")
    for sub in ("tests","nayeon"):
        if git("rev-parse",BASE+":"+sub)!=git("rev-parse","HEAD:"+sub):
            raise RuntimeError("P184 entire historical tests or product source mutated")
    for p in (
        "scripts/p180_windows_sealed_blob_transport_equivalence.py",
        "scripts/p181_windows_batch_transport_security_review.py",
        "scripts/p182_windows_fail_closed_batch_transport.py",
        "scripts/p183_windows_historical_security_equivalence.py",
        *PINNED,
    ):
        if (ROOT/p).read_bytes()!=git("show",BASE+":"+p):
            raise RuntimeError("P184 original audited candidate/historical file changed: "+p)
    for p,digest in PINNED.items():
        if sha((ROOT/p).read_bytes())!=digest:
            raise RuntimeError("P184 literal trusted P183 source SHA256 mismatch: "+p)
    modules=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
             if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(modules)!=171:
        raise RuntimeError("P184 original 171 tracked historical module custody changed")
    return {
      "exact_P184_HEAD":git("rev-parse","HEAD").decode().strip(),
      "exact_P183_source_parent":BASE,
      "only_three_additive_review_paths":sorted(NEW),
      "original_product_test_and_previous_candidate_trees_unchanged":True,
      "frozen_original_test_module_count":len(modules),
      "P183_source_SHA256_pins":PINNED,
    }

def authenticate_P183(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P184 missing read-only ephemeral GitHub archive token")
    raw=_download_artifact(P183_ID,P183_ZIP,token)
    if sha(raw)!=P183_ZIP:
        raise RuntimeError("P184 prior P183 true native Windows archive SHA256 changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if (z.testzip() is not None or len(z.namelist())!=2
            or set(z.namelist())!={P183_LOG,P183_LEDGER}):
            raise RuntimeError("P184 authentic P183 archive members or CRC drift")
        prior=json.loads(z.read(P183_LEDGER))
        native=prior.get("authentic_original_Windows_tests",{})
        log=z.read(P183_LOG)
        t=log.decode("utf8","replace").replace("\r\n","\n")
        if (prior.get("checkpoint")!="P183"
            or prior.get("exact_source_before")!=prior.get("exact_source_after")
            or prior.get("exact_source_before",{}).get("exact_P183_HEAD")!=BASE
            or prior.get("historical_H")!="HOLD"
            or prior.get("production_R")!="HOLD"
            or prior.get("accepted_complete_full_product_native_Windows")!="0/3"
            or prior.get("independent_external_decisions")!=REVIEWS
            or prior.get("source_bound_reviewer_packet_generated_not_qualified_security_signoff") is not True
            or prior.get("transport_security_candidate_integrated_into_original_verifier") is not False
            or len(prior.get("reviewer_scope_matrix",{}))!=9
            or native.get("complete_native_case_count")!=45
            or native.get("native_exit")!=0
            or native.get("raw_log_SHA256")!=P183_LOG_SHA
            or sha(log)!=P183_LOG_SHA
            or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)!=["45"]
            or not re.search(r"^OK\s*$",t,re.M)):
            raise RuntimeError("P184 prior real P183 45-case receipt or governance drift")
    return {
     "P183_authenticated_original_artifact":P183_ID,"ZIP_SHA256":P183_ZIP,
     "original_real_45_of_45_Windows_cases":"PASS",
     "nine_row_historical_security_equivalence_matrix":"REMAINED_OPEN",
     "qualified_governance_or_production_signoff":"NOT_OBTAINED",
    }


@dataclass(frozen=True)
class FreshSnapshot:
    head: str
    branch: str
    oid: bytes
    index_oid: bytes
    source_sha256: str
    kind: str="100644"
    index_stage: int=0
    no_reparse: bool=True
    repo_root_ok: bool=True

def _path_canonical(path:str)->None:
    if not p180.valid_path(path) or path not in PINNED:
        raise ValueError("P184 only exact approved historical canonical source paths")

def _no_reparse(path:str)->bool:
    # lstat, not stat: never follow junctions/symlinks on the source ancestry.
    current=ROOT
    relative=Path(path)
    for component in ("",*relative.parts):
        if component:
            current=current/component
        info=current.lstat()
        if stat.S_ISLNK(info.st_mode):
            return False
        if getattr(info,"st_file_attributes",0)&getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0x400):
            return False
    return True

def real_snapshot(path:str)->FreshSnapshot:
    _path_canonical(path)
    head=git("rev-parse","HEAD").decode("ascii").strip()
    branch=git("branch","--show-current").decode("utf8").strip()
    actual_root=git("rev-parse","--show-toplevel").decode("utf8").strip()
    root_ok=(os.path.normcase(os.path.abspath(actual_root))
             ==os.path.normcase(os.path.abspath(str(ROOT))))
    if git("rev-parse","--show-object-format").strip()!=b"sha1":
        raise ValueError("P184 no SHA1 Git repo trust")
    full=git("ls-tree","--full-tree","-z",head,"--",path)
    match=re.fullmatch(
        rb"100644 blob ([0-9a-f]{40})\t"+re.escape(path.encode("ascii"))+rb"\0",
        full,
    )
    if match is None:
        raise ValueError("P184 ordinary Git HEAD tree entry missing/malformed")
    stage=git("ls-files","--stage","--",path)
    index=re.fullmatch(
        rb"100644 ([0-9a-f]{40}) 0\t"+re.escape(path.encode("ascii"))+rb"\n",
        stage,
    )
    if index is None:
        raise ValueError("P184 single clean normal stage-0 Git index entry required")
    if not _no_reparse(path):
        raise ValueError("P184 source linked/reparse path denied")
    data=(ROOT/path).read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest().encode()
    if blob!=match.group(1):
        raise ValueError("P184 real disk source differs from original HEAD blob")
    return FreshSnapshot(
        head=head,branch=branch,oid=match.group(1),index_oid=index.group(1),
        source_sha256=sha(data),no_reparse=True,repo_root_ok=root_ok,
    )

class FreshSourceAdmittedBatch:
    """Each request: new pre/post Git+disk snapshots, no approval cache.

    A narrow contract under review. Does not execute legacy B's entire tag,
    ancestor and SHA256 envelope gate or claim every historical assertion.
    """
    def __init__(self,commit:str,branch:str,*,transport=None,snapshot=None):
        if (not isinstance(commit,str) or not HEX40.fullmatch(commit)
            or not isinstance(branch,str) or branch!=BRANCH):
            raise ValueError("P184 exact source commit and branch mandatory")
        self._head=commit
        self._branch=branch
        self._snapshot=snapshot or real_snapshot
        self._transport=transport or p182.FailClosedGitBatch(timeout_seconds=4)
        self._retired=False
        self._accepted=0

    @property
    def retired(self)->bool:return self._retired

    @property
    def accepted_requests(self)->int:return self._accepted

    def close(self):
        self._retired=True
        self._transport.close()

    def _require(self,s:FreshSnapshot,path:str,pin:str)->None:
        if not isinstance(s,FreshSnapshot):
            raise RuntimeError("P184 unauthenticated source observation type")
        if (s.head!=self._head or s.branch!=self._branch
            or not isinstance(s.oid,bytes) or not p180.valid_oid(s.oid)
            or s.oid!=s.index_oid
            or s.kind!="100644" or s.index_stage!=0
            or s.source_sha256!=pin
            or not s.no_reparse or not s.repo_root_ok):
            raise RuntimeError("P184 live source/commit/index/branch/disk security admission refused")

    def read(self,path:str)->bytes:
        if self._retired:
            raise RuntimeError("P184 source-admission session permanently closed")
        try:
            _path_canonical(path)
            pin=PINNED[path]
            # Exact newly sampled source authority before and after each blob:
            before=self._snapshot(path)
            self._require(before,path,pin)
            data=self._transport.read(before.oid)
            if not isinstance(data,bytes) or sha(data)!=pin:
                raise RuntimeError("P184 returned source SHA256 differs from pinned authority")
            after=self._snapshot(path)
            self._require(after,path,pin)
            if after!=before:
                raise RuntimeError("P184 concurrent change between fresh pre/post sources")
            self._accepted+=1
            return data
        except BaseException:
            self.close()
            raise


class _RecordedTransport:
    def __init__(self,payload:bytes):
        self.payload=payload
        self.oids=[]
        self.closed=False
    def read(self,oid:bytes)->bytes:
        if self.closed:raise RuntimeError("transport already retired")
        self.oids.append(oid)
        return self.payload
    def close(self):self.closed=True


class P184FreshHistoricalSourceAdmissionTests(unittest.TestCase):
    """12 new native Windows original-source-bound narrow-contract tests."""

    def setUp(self):
        self.path="tests/phase8_byok_b_scope_migration.py"
        self.data=(ROOT/self.path).read_bytes()
        self.assertEqual(sha(self.data),PINNED[self.path])
        self.oid=hashlib.sha1(b"blob "+str(len(self.data)).encode()+b"\0"+self.data).hexdigest().encode()
        self.clean=FreshSnapshot(
            head=git("rev-parse","HEAD").decode().strip(),branch=BRANCH,
            oid=self.oid,index_oid=self.oid,source_sha256=sha(self.data),
        )

    def exercise(self,snapshots,*,data=None,path=None):
        values=list(snapshots)
        used=[]
        def observe(p):
            used.append(p)
            return values.pop(0)
        t=_RecordedTransport(self.data if data is None else data)
        gate=FreshSourceAdmittedBatch(self.clean.head,BRANCH,transport=t,snapshot=observe)
        return gate,t,used

    def test_01_clean_unchanged_source_reobserved_before_and_after_every_request(self):
        g,t,calls=self.exercise([self.clean]*4)
        self.assertEqual(g.read(self.path),self.data)
        self.assertEqual(g.read(self.path),self.data)
        self.assertEqual(len(calls),4)
        self.assertEqual(len(t.oids),2)
        self.assertEqual(g.accepted_requests,2)
        g.close()

    def test_02_HEAD_swap_before_request_denied_without_Git_blob_read(self):
        wrong=replace(self.clean,head="a"*40)
        g,t,_=self.exercise([wrong])
        with self.assertRaises(RuntimeError):g.read(self.path)
        self.assertTrue(g.retired)
        self.assertEqual(t.oids,[])

    def test_03_HEAD_swap_after_Git_response_denied_and_session_retired(self):
        wrong=replace(self.clean,head="a"*40)
        g,t,calls=self.exercise([self.clean,wrong])
        with self.assertRaises(RuntimeError):g.read(self.path)
        self.assertTrue(t.closed)
        self.assertEqual(len(t.oids),1)
        self.assertEqual(len(calls),2)
        self.assertEqual(g.accepted_requests,0)

    def test_04_index_only_tamper_denied(self):
        wrong=replace(self.clean,index_oid=b"a"*40)
        g,t,_=self.exercise([wrong])
        with self.assertRaises(RuntimeError):g.read(self.path)
        self.assertEqual(t.oids,[])

    def test_05_disk_digest_tamper_denied_even_if_old_blob_OID_is_unchanged(self):
        wrong=replace(self.clean,source_sha256="A"*64)
        g,t,_=self.exercise([wrong])
        with self.assertRaises(RuntimeError):g.read(self.path)
        self.assertEqual(t.oids,[])

    def test_06_wrong_branch_revoked(self):
        wrong=replace(self.clean,branch="nayeon-v1")
        g,t,_=self.exercise([wrong])
        with self.assertRaises(RuntimeError):g.read(self.path)
        self.assertTrue(g.retired)

    def test_07_reparse_parent_and_untrusted_repository_root_denied(self):
        for kwargs in ({"no_reparse":False},{"repo_root_ok":False}):
            with self.subTest(kwargs=kwargs):
                g,t,_=self.exercise([replace(self.clean,**kwargs)])
                with self.assertRaises(RuntimeError):g.read(self.path)
                self.assertEqual(t.oids,[])

    def test_08_wrong_regular_file_mode_or_index_stage_denied(self):
        for kwargs in ({"kind":"120000"},{"index_stage":1}):
            with self.subTest(kwargs=kwargs):
                g,t,_=self.exercise([replace(self.clean,**kwargs)])
                with self.assertRaises(RuntimeError):g.read(self.path)
                self.assertEqual(t.oids,[])

    def test_09_invalid_path_alias_traversal_and_ads_denied_before_observation(self):
        for path in ("Tests/phase8_byok_b_scope_migration.py","tests/../secret",
                     "tests\\phase8_byok_b_scope_migration.py",
                     "tests/phase8_byok_b_scope_migration.py:ads",
                     "nayeon/desktop_alpha/frozen_signed_byok_companion.py"):
            with self.subTest(path=path):
                g,t,calls=self.exercise([])
                with self.assertRaises(ValueError):g.read(path)
                self.assertTrue(g.retired)
                self.assertEqual(t.oids,[])
                self.assertEqual(calls,[])

    def test_10_corrupted_batch_payload_denied_even_with_matching_snapshots(self):
        g,t,_=self.exercise([self.clean,self.clean],data=self.data+b"changed")
        with self.assertRaises(RuntimeError):g.read(self.path)
        self.assertTrue(g.retired)
        self.assertEqual(g.accepted_requests,0)

    def test_11_real_fresh_HEAD_index_disk_and_transport_match_for_two_historical_sources(self):
        expected=git("rev-parse","HEAD").decode().strip()
        g=FreshSourceAdmittedBatch(expected,BRANCH)
        try:
            for path in PINNED:
                actual=g.read(path)
                self.assertEqual(sha(actual),PINNED[path])
                self.assertEqual(actual,git("show",expected+":"+path))
            self.assertEqual(g.accepted_requests,len(PINNED))
        finally:g.close()

    def test_12_original_frozen_B_authority_and_external_review_remain_UNAPPROVED(self):
        source=(ROOT/"tests/phase8_byok_b_scope_migration.py").read_text(encoding="utf8")
        for required in ("_parent_tree","assert_byok_b_integrity","CANDIDATE_SHA256",
                         "PARENT_TAG_OBJECT","_disk","_raw_delta"):
            self.assertIn(required,source)
        # New contract intentionally does not invoke the full historical B gate.
        self.assertNotIn("assert_byok_b_integrity",FreshSourceAdmittedBatch.read.__code__.co_names)
        self.assertEqual(set(REVIEWS),{"GOV-01","GOV-02","SEC-03","SEC-04",
                                      "REL-05","REL-06","REL-07"})


def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p184-fresh-source-admission"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
       "checkpoint":"P184","historical_H":"HOLD",
       "current_C":"NARROW_DOUBLE_FRESH_HISTORICAL_SOURCE_CONTRACT_PROTOTYPE_ONLY",
       "production_R":"HOLD","full_product_native_Windows_regressions":"0/3",
       "seven_qualified_external_decisions":REVIEWS,
       "privileged_C1_G0_G6":"OPEN","signed_Windows_CodeIntegrity_GO":False,
       "all_original_historical_security_test_assertions_preserved":True,
       "original_P135_three_600s_full_product_timeouts":"UNWAIVED",
       "original_P175_five_source_era_failures":"UNWAIVED",
       "original_P178_BYOK_B_module_165s_timeout_and_two_FAIL":"UNWAIVED",
       "original_P179_pin_witness_130s_timeout":"UNWAIVED",
       "original_frozen_test_modules_modified":False,
       "historical_verifier_currently_using_batch_candidate":False,
       "new_source_admission_P184_not_complete_historical_B_policy":True,
       "review_risks_after_prototype":{
          "bounded_batch_deadline_and_poisoning":"ISOLATED_P182_TESTED",
          "two_pre_post_fresh_HEAD_branch_index_disk_Source_SHA256":"ISOLATED_P184_TESTED",
          "full_parent_annotated_tags_tree_ancestry_and_B_manifest":"NOT_ESTABLISHED",
          "all_Win32_reparse_alias_racing_writers":"NOT_ESTABLISHED",
          "signed_Git_process_identity_and_privileged_peer":"NOT_ESTABLISHED",
          "all_original_negative_security_tests_in_product":"NOT_ESTABLISHED",
          "qualified_independent_review":"NOT_OBTAINED",
          "three_full_native_product_regressions":"0/3",
       },
    }
    complete=False
    try:
        before=custody()
        ledger["exact_source_before"]=before
        ledger["authenticated_original_P183_native_Windows"]=authenticate_P183(
            os.environ.get("P184_EVIDENCE_TOKEN",""))
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for key in list(env):
            if (key in {"P184_EVIDENCE_TOKEN","GH_TOKEN","GITHUB_TOKEN"}
                or key.endswith("_API_KEY") or key.endswith("_SECRET")):
                env.pop(key,None)
        selectors=[
          "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests",
          "scripts.p181_windows_batch_transport_security_review.P181BatchAdversarialSecurityTests",
          "scripts.p182_windows_fail_closed_batch_transport.P182FailClosedBatchSecurityCases",
          "scripts.p183_windows_historical_security_equivalence.P183HistoricalEquivalenceAdversarialCases",
          "scripts.p184_windows_fresh_historical_source_admission.P184FreshHistoricalSourceAdmissionTests",
          "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_self_canonicalization_only_zeros_own_single_literal",
        ]
        log=out/"p184_genuine_native_Windows_historical_source_admission_57_cases.log"
        with log.open("wb") as f:
            run=subprocess.run([sys.executable,"-B","-m","unittest","-v",*selectors],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=120,check=False)
        raw=log.read_bytes()
        t=raw.decode("utf8","replace").replace("\r\n","\n")
        footer=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)
        ledger["authentic_native_Windows_evidence"]={
          "selectors":selectors,
          "original_P180_cases":8,"original_P181_cases":12,
          "original_P182_cases":12,"original_P183_cases":12,
          "original_frozen_BYOK_B_control":1,"new_P184_cases":12,
          "complete_original_unittest_case_count":int(footer[-1]) if footer else None,
          "native_exit":run.returncode,
          "raw_log_SHA256":sha(raw),"raw_log_name":log.name,
          "actual_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",t,re.M),
        }
        if run.returncode!=0 or footer!=["57"] or not re.search(r"^OK\s*$",t,re.M):
            raise RuntimeError("P184 actual Windows historical source-admission suite incomplete")
        ledger["exact_source_after"]=custody()
        complete=(before==ledger["exact_source_after"])
        if not complete:raise RuntimeError("P184 authenticated original source drift after real tests")
        print("P184_ACTUAL_NATIVE_WINDOWS_TESTS=57/57_PASS|EXIT=0",flush=True)
        print("P184_ORIGINAL_P180_P181_P182_P183_TESTS=44_UNMODIFIED",flush=True)
        print("P184_ORIGINAL_FROZEN_BYOK_B_CONTROL=1/1_PASS",flush=True)
        print("P184_TWO_REAL_FRESH_SOURCE_READS=HEAD_INDEX_DISK_SHA256_VERIFIED",flush=True)
        print("P184_POST_READ_DRIFT_AND_TAMPER=REJECTED_BY_ISOLATED_CANDIDATE",flush=True)
        print("P184_WIDER_HISTORICAL_TAG_ANCESTRY_WIN32_GOVERNANCE=NOT_ESTABLISHED",flush=True)
        print("P184_RAW_NATIVE_SHA256="+sha(raw),flush=True)
        print("P184_PRODUCTION_RELEASE=HOLD|FULL_NATIVE=0/3|7_QUALIFIED_DECISIONS=OPEN",flush=True)
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P184_AUTHENTIC_SOURCE_ADMISSION_CANDIDATE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["source_bound_narrow_contract_test_evidence_complete_not_a_qualified_release"]=complete
        (out/"p184_narrow_double_fresh_source_admission_review_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":
    raise SystemExit(main())
