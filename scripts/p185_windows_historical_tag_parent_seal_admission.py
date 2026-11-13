"""P185: narrowly bounded historical annotated-tag/parent-seal admission.

An ISOLATED read-only prototype. No frozen source/test replacement, no claims
of full BYOK B historical envelope admission or production independent GO.
Authenticates original P184 hosted Windows evidence and replays untouched
preceding 57 native cases plus 12 new historical tag/ancestry canaries.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
import zipfile

from scripts import p180_windows_sealed_blob_transport_equivalence as p180
from scripts import p182_windows_fail_closed_batch_transport as p182
from scripts import p184_windows_fresh_historical_source_admission as p184
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as legacy_b
from tests import phase8_byok_scope_migration as legacy_a

ROOT=Path(__file__).resolve().parents[1]
BASE="a66a5221ab74d0b7f65fd381c554f186cd6c8ed1"
BRANCH="byok-c1-p185-historical-tag-seal-parent-admission-20261113"
NEW={
 ".github/workflows/p185-windows-historical-tag-parent-seal-admission.yml",
 "docs/byok-c1-p185-historical-tag-parent-seal-admission.md",
 "scripts/p185_windows_historical_tag_parent_seal_admission.py",
}
P184_ID=13991643573
P184_ZIP="98F49A33B184E1FE67F4FA99EEE2B14814DDD515219E2312E441A0197640BECD"
P184_LOG="p184_genuine_native_Windows_historical_source_admission_57_cases.log"
P184_LOG_SHA="1E3785DB99F365B37FAE5DAD7E5E03C31F99E39A0447A57B2CDA8265C3BE4E8C"
P184_LEDGER="p184_narrow_double_fresh_source_admission_review_ledger.json"
REVIEWS={x:"OPEN" for x in (
 "GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}

# These are original, static historical BYOK B seal values, not inferred
# from the current P185 Git branch or any mutable current working tree.
HIST_PARENT="4110fa69849f8127a325f9a9001284cd1bd3a59c"
HIST_PARENT_TREE="747f172144794d687251545ca923d5ebb5b1551b"
HIST_PARENT_PARENT="87208af710bac90c440f2e0851854318b22e9b88"
HIST_TAG="nayeon-v1-phase8-byok-first-run-owner-fake-only-01"
HIST_TAG_OBJECT="7496961c83de9607402dcdabff25917674d6688a"
PINNED_PATHS={
 "tests/phase_8_30_scope_migration.py":"23d5b1a0a9e4f83ffd870f6b72693bb8878c85f94d8d7c142ca2a57fa0aeb218",
 "tests/phase_8_37_scope_migration.py":"79cbfffb932aea28321f017b76d26185774747a3d30cc0a7455530b6d01188cd",
}
P184_HEAD_PATH="tests/phase8_byok_b_scope_migration.py"
HEX40=re.compile(r"^[0-9a-f]{40}$")

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(
        ["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=35).stdout

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
        raise RuntimeError("P185 exact clean authenticated GitHub-hosted Windows source required")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",n).strip() for n in NEW):
        raise RuntimeError("P185 only three new audit-only file paths allowed")
    for sub in ("nayeon","tests"):
        if git("rev-parse",BASE+":"+sub)!=git("rev-parse","HEAD:"+sub):
            raise RuntimeError("P185 entire original security/product subtree changed")
    immutable=(
        "scripts/p180_windows_sealed_blob_transport_equivalence.py",
        "scripts/p181_windows_batch_transport_security_review.py",
        "scripts/p182_windows_fail_closed_batch_transport.py",
        "scripts/p183_windows_historical_security_equivalence.py",
        "scripts/p184_windows_fresh_historical_source_admission.py",
        "tests/phase8_byok_b_scope_migration.py",
        "tests/phase8_byok_scope_migration.py",
        *PINNED_PATHS,
    )
    for p in immutable:
        if (ROOT/p).read_bytes()!=git("show",BASE+":"+p):
            raise RuntimeError("P185 historical candidate/frozen source changed "+p)
    modules=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
             if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(modules)!=171:raise RuntimeError("P185 original 171 tracked modules changed")
    if (legacy_b.PARENT!=HIST_PARENT or legacy_b.PARENT_TREE!=HIST_PARENT_TREE
        or legacy_b.PARENT_TAG!=HIST_TAG or legacy_b.PARENT_TAG_OBJECT!=HIST_TAG_OBJECT
        or legacy_b.PARENT_PARENT!=HIST_PARENT_PARENT
        or {p:legacy_a.CANDIDATE_SHA256[p] for p in PINNED_PATHS}!=PINNED_PATHS):
        raise RuntimeError("P185 frozen historical B/A tag, tree and source pin drift")
    return {
       "exact_P185_HEAD":git("rev-parse","HEAD").decode().strip(),
       "P184_immutable_parent":BASE,
       "only_three_additive_audit_paths":sorted(NEW),
       "original_tests_product_and_all_prior_candidates_unchanged":True,
       "original_test_modules":171,
       "original_historical_B_parent_tag_tree_and_two_A_SHA256_pins":True,
    }

def authenticate_P184(token:str)->dict:
    if len(token)<8:raise RuntimeError("P185 missing ephemeral read-only GitHub archive token")
    raw=_download_artifact(P184_ID,P184_ZIP,token)
    if sha(raw)!=P184_ZIP:raise RuntimeError("P185 original P184 archive SHA256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if (z.testzip() is not None or len(z.namelist())!=2
            or set(z.namelist())!={P184_LOG,P184_LEDGER}):
            raise RuntimeError("P185 original P184 ZIP members or CRC invalid")
        p=json.loads(z.read(P184_LEDGER))
        native=p.get("authentic_native_Windows_evidence",{})
        log=z.read(P184_LOG)
        text=log.decode("utf8","replace").replace("\r\n","\n")
        if (p.get("checkpoint")!="P184"
            or p.get("exact_source_before")!=p.get("exact_source_after")
            or p.get("exact_source_before",{}).get("exact_P184_HEAD")!=BASE
            or p.get("historical_H")!="HOLD" or p.get("production_R")!="HOLD"
            or p.get("full_product_native_Windows_regressions")!="0/3"
            or p.get("seven_qualified_external_decisions")!=REVIEWS
            or p.get("historical_verifier_currently_using_batch_candidate") is not False
            or p.get("source_bound_narrow_contract_test_evidence_complete_not_a_qualified_release") is not True
            or native.get("complete_original_unittest_case_count")!=57
            or native.get("native_exit")!=0
            or native.get("raw_log_SHA256")!=P184_LOG_SHA or sha(log)!=P184_LOG_SHA
            or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=["57"]
            or not re.search(r"^OK\s*$",text,re.M)):
            raise RuntimeError("P185 source-bound P184 original 57/57 Windows evidence drift")
    return {"P184_original_artifact_id":P184_ID,"ZIP_SHA256":P184_ZIP,
            "original_native_selected_57_of_57_Windows":"PASS",
            "qualified_external_security_review":"NOT_OBTAINED",
            "full_product_accepted_regressions":"0/3"}

@dataclass(frozen=True)
class HistoricalSealSnapshot:
    head: str
    branch: str
    parent: str
    parent_tree: str
    parent_parent: str
    tag: str
    tag_object: str
    peeled_parent: str
    tag_type: str
    commit_type: str
    parent_line: str
    path: str
    mode: str
    blob_oid: bytes
    source_SHA256: str
    repo_root_ok: bool=True

def path_guard(path:str):
    if not isinstance(path,str) or path not in PINNED_PATHS or not p180.valid_path(path):
        raise ValueError("P185 only two immutable original sealed A parent source paths allowed")

def observe_historical(path:str)->HistoricalSealSnapshot:
    path_guard(path)
    head=git("rev-parse","HEAD").decode("ascii").strip()
    branch=git("branch","--show-current").decode("utf8").strip()
    root=git("rev-parse","--show-toplevel").decode("utf8").strip()
    if git("rev-parse","--show-object-format").strip()!=b"sha1":
        raise ValueError("P185 original SHA1 Git object format required")
    tag_oid=git("show-ref","--verify","--hash","--","refs/tags/"+HIST_TAG).decode("ascii").strip()
    tag_type=git("cat-file","-t",HIST_TAG_OBJECT).decode("ascii").strip()
    parent_type=git("cat-file","-t",HIST_PARENT).decode("ascii").strip()
    peeled=git("rev-parse","--verify","--end-of-options",HIST_TAG_OBJECT+"^{}").decode("ascii").strip()
    tree=git("rev-parse",HIST_PARENT+"^{tree}").decode("ascii").strip()
    parent_line=git("rev-list","--parents","-n","1",HIST_PARENT).decode("ascii").strip()
    tree_record=git("ls-tree","--full-tree","-z",HIST_PARENT,"--",path)
    match=re.fullmatch(rb"100644 blob ([0-9a-f]{40})\t"+
                       re.escape(path.encode("ascii"))+rb"\0",tree_record)
    if match is None:raise ValueError("P185 historical tree entry not a unique regular blob")
    blob_oid=match.group(1)
    # History's SHA256 pin is immutable source data, not a newly learned
    # current source approval. The returned full blob is verified separately.
    return HistoricalSealSnapshot(
        head=head,branch=branch,parent=HIST_PARENT,
        parent_tree=tree,parent_parent=HIST_PARENT_PARENT,
        tag=HIST_TAG,tag_object=tag_oid,peeled_parent=peeled,
        tag_type=tag_type,commit_type=parent_type,parent_line=parent_line,
        path=path,mode="100644",blob_oid=blob_oid,
        source_SHA256=PINNED_PATHS[path],
        repo_root_ok=(os.path.normcase(os.path.abspath(root))==
                      os.path.normcase(os.path.abspath(str(ROOT)))),
    )

class TaggedParentSealedRead:
    """No approved historic seal caching. Double-observe each parent blob.

    Does not substitute for original B whole-envelope/file-system/index
    verifier. Historical SHA256 pins are A manifest values for exact A files.
    """
    def __init__(self,expected_head:str,*,observe=None,transport=None):
        if not isinstance(expected_head,str) or not HEX40.fullmatch(expected_head):
            raise ValueError("P185 full source HEAD SHA required")
        self.expected_head=expected_head
        self.observe=observe or observe_historical
        self.transport=transport or p182.FailClosedGitBatch(timeout_seconds=5)
        self.retired=False
        self.accepted=0

    def close(self):
        self.retired=True
        self.transport.close()

    def require(self,s:HistoricalSealSnapshot,path:str):
        if (not isinstance(s,HistoricalSealSnapshot)
            or s.head!=self.expected_head or s.branch!=BRANCH
            or s.parent!=HIST_PARENT or s.parent_tree!=HIST_PARENT_TREE
            or s.parent_parent!=HIST_PARENT_PARENT
            or s.tag!=HIST_TAG or s.tag_object!=HIST_TAG_OBJECT
            or s.peeled_parent!=HIST_PARENT
            or s.tag_type!="tag" or s.commit_type!="commit"
            or s.parent_line!=HIST_PARENT+" "+HIST_PARENT_PARENT
            or s.path!=path or s.mode!="100644"
            or not p180.valid_oid(s.blob_oid)
            or s.source_SHA256!=PINNED_PATHS[path]
            or not s.repo_root_ok):
            raise RuntimeError("P185 historical annotated tag/tree/ancestry/source admission refused")

    def read(self,path:str)->bytes:
        if self.retired:
            raise RuntimeError("P185 historical admission session permanently retired")
        try:
            path_guard(path)
            before=self.observe(path)
            self.require(before,path)
            data=self.transport.read(before.blob_oid)
            if (type(data) is not bytes
                or legacy_a._digest(path,data).upper()!=PINNED_PATHS[path].upper()):
                raise RuntimeError("P185 historic A SHA256 seal bytes mismatch")
            after=self.observe(path)
            self.require(after,path)
            if before!=after:
                raise RuntimeError("P185 historical tagged parent source changed during read")
            self.accepted+=1
            return data
        except BaseException:
            self.close()
            raise

class _RecordedTransport:
    def __init__(self,data:bytes):
        self.data=data
        self.closed=False
        self.oids=[]
    def read(self,oid:bytes)->bytes:
        if self.closed:raise RuntimeError("P185 transport poisoned")
        self.oids.append(oid)
        return self.data
    def close(self):self.closed=True

class P185HistoricalTagSealAdmissionTests(unittest.TestCase):
    """12 separate scoped tests; detection success DOES NOT mean product GO."""
    def setUp(self):
        self.path="tests/phase_8_30_scope_migration.py"
        self.head=git("rev-parse","HEAD").decode("ascii").strip()
        self.raw=git("show",HIST_PARENT+":"+self.path)
        self.assertEqual(legacy_a._digest(self.path,self.raw),PINNED_PATHS[self.path])
        self.blob=hashlib.sha1(
            b"blob "+str(len(self.raw)).encode()+b"\0"+self.raw
        ).hexdigest().encode()
        self.valid=HistoricalSealSnapshot(
            head=self.head,branch=BRANCH,parent=HIST_PARENT,
            parent_tree=HIST_PARENT_TREE,parent_parent=HIST_PARENT_PARENT,
            tag=HIST_TAG,tag_object=HIST_TAG_OBJECT,peeled_parent=HIST_PARENT,
            tag_type="tag",commit_type="commit",
            parent_line=HIST_PARENT+" "+HIST_PARENT_PARENT,
            path=self.path,mode="100644",blob_oid=self.blob,
            source_SHA256=PINNED_PATHS[self.path])

    def make(self,snapshots,*,data=None):
        values=list(snapshots)
        observed=[]
        def observer(path):
            observed.append(path)
            return values.pop(0)
        t=_RecordedTransport(self.raw if data is None else data)
        subject=TaggedParentSealedRead(self.head,observe=observer,transport=t)
        return subject,t,observed

    def test_01_double_observation_repeated_every_read_without_admission_cache(self):
        a,t,observed=self.make([self.valid]*4)
        self.assertEqual(a.read(self.path),self.raw)
        self.assertEqual(a.read(self.path),self.raw)
        self.assertEqual(observed,[self.path]*4)
        self.assertEqual(len(t.oids),2)
        self.assertEqual(a.accepted,2)
        a.close()

    def test_02_tag_oid_changed_before_read_refused_without_transport_IO(self):
        a,t,_=self.make([replace(self.valid,tag_object="a"*40)])
        with self.assertRaises(RuntimeError):a.read(self.path)
        self.assertTrue(a.retired)
        self.assertEqual(t.oids,[])

    def test_03_tag_changes_after_read_refused_and_poisoned(self):
        a,t,ob=self.make([self.valid,replace(self.valid,tag_object="a"*40)])
        with self.assertRaises(RuntimeError):a.read(self.path)
        self.assertEqual(ob,[self.path]*2)
        self.assertTrue(t.closed)
        self.assertEqual(a.accepted,0)
        with self.assertRaises(RuntimeError):a.read(self.path)

    def test_04_wrong_parent_tree_and_ancestry_denied(self):
        for mutation in ({"parent_tree":"a"*40},{"parent_parent":"a"*40},
                         {"parent_line":HIST_PARENT+" "+"a"*40}):
            with self.subTest(mutation=mutation):
                a,t,_=self.make([replace(self.valid,**mutation)])
                with self.assertRaises(RuntimeError):a.read(self.path)
                self.assertEqual(t.oids,[])

    def test_05_peeled_commit_or_tag_object_type_swap_denied(self):
        for mutation in ({"peeled_parent":"a"*40},{"tag_type":"commit"},
                         {"commit_type":"tree"}):
            with self.subTest(mutation=mutation):
                a,t,_=self.make([replace(self.valid,**mutation)])
                with self.assertRaises(RuntimeError):a.read(self.path)
                self.assertTrue(a.retired)

    def test_06_wrong_parent_path_mode_or_original_blob_refused(self):
        for mutation in ({"path":"tests/phase_8_37_scope_migration.py"},
                         {"mode":"120000"},{"blob_oid":b"a"*40}):
            with self.subTest(mutation=mutation):
                a,t,_=self.make([replace(self.valid,**mutation)])
                with self.assertRaises(RuntimeError):a.read(self.path)
                self.assertEqual(t.oids,[])

    def test_07_untrusted_source_branch_HEAD_and_repo_root_refused(self):
        for mutation in ({"head":"a"*40},{"branch":"nayeon-v1"},
                         {"repo_root_ok":False}):
            with self.subTest(mutation=mutation):
                a,t,_=self.make([replace(self.valid,**mutation)])
                with self.assertRaises(RuntimeError):a.read(self.path)
                self.assertTrue(t.closed)

    def test_08_old_historical_SHA256_rejects_tampered_full_blob(self):
        a,t,_=self.make([self.valid,self.valid],data=self.raw+b"tamper")
        with self.assertRaisesRegex(RuntimeError,"SHA256 seal"):a.read(self.path)
        self.assertTrue(a.retired)
        self.assertEqual(a.accepted,0)

    def test_09_unallowlisted_alias_and_ADS_never_reach_Git(self):
        for path in ("Tests/phase_8_30_scope_migration.py","tests/../secret",
                     "tests\\phase_8_30_scope_migration.py",
                     "tests/phase_8_30_scope_migration.py:ads",
                     P184_HEAD_PATH):
            with self.subTest(path=path):
                a,t,obs=self.make([])
                with self.assertRaises(ValueError):a.read(path)
                self.assertEqual(t.oids,[])
                self.assertEqual(obs,[])

    def test_10_actual_git_annotated_tag_parent_and_tree_pins_match(self):
        actual=observe_historical(self.path)
        subject,t,_=self.make([actual,actual])
        self.assertEqual(subject.read(self.path),self.raw)
        self.assertEqual(t.oids,[actual.blob_oid])
        self.assertEqual(actual.parent_tree,HIST_PARENT_TREE)
        subject.close()

    def test_11_real_git_bounded_historical_parent_blob_for_both_pinned_sources(self):
        subject=TaggedParentSealedRead(self.head)
        try:
            for path in PINNED_PATHS:
                original=git("show",HIST_PARENT+":"+path)
                self.assertEqual(subject.read(path),original)
                self.assertEqual(legacy_a._digest(path,original),PINNED_PATHS[path])
            self.assertEqual(subject.accepted,len(PINNED_PATHS))
        finally:subject.close()

    def test_12_original_full_B_envelope_remains_unmodified_and_NOT_claimed(self):
        self.assertEqual(legacy_b.PARENT,HIST_PARENT)
        self.assertEqual(legacy_b.PARENT_TREE,HIST_PARENT_TREE)
        self.assertEqual(legacy_b.PARENT_TAG_OBJECT,HIST_TAG_OBJECT)
        self.assertEqual(legacy_b.PARENT_PARENT,HIST_PARENT_PARENT)
        self.assertEqual(set(REVIEWS),
                         {"GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07"})
        self.assertEqual(len(legacy_b.ENVELOPE),23)
        self.assertTrue(hasattr(legacy_b,"assert_byok_b_integrity"))
        self.assertNotIn("assert_byok_b_integrity",TaggedParentSealedRead.read.__code__.co_names)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p185-historical-tag-parent"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
      "checkpoint":"P185","historical_H":"HOLD",
      "current_C":"ISOLATED_TAGGED_PARENT_BLOB_PROOF_ONLY",
      "production_R":"HOLD","full_product_native_Windows_regressions":"0/3",
      "seven_qualified_external_decisions":REVIEWS,
      "privileged_C1_G0_G6":"OPEN","signed_main_helper_installer_certificate_GO":False,
      "all_original_source_seals_and_tests_unchanged":True,
      "P135_3x600s_original_full_discovery_TIMEOUT":"UNWAIVED",
      "P175_five_source_era_failing_cases":"UNWAIVED",
      "P178_original_B_module_165s_TIMEOUT_two_FAIL":"UNWAIVED",
      "P179_original_pin_witness_130s_TIMEOUT":"UNWAIVED",
      "historical_B_full_23_file_verifier_replaced_or_bypassed":False,
      "tagged_parent_candidate_no_qualified_independent_approval":True,
      "candidate_scope":"two A-parent historical blobs, fixed SHA256, tag/tree/parent double observed",
      "not_proved":[
          "entire historical B 23-file source and disk/index/unstaged admission",
          "complete historical chain of all earlier frozen source/tags",
          "Win32 atomic inode handle and racing parent writer rejection",
          "trusted Git executable signature and privileged IPC source identity",
          "actual full original legacy negative suite completion",
          "three consecutive original unfiltered product Windows regressions",
          "independent qualified security and installer/WDAC/SAC production GO",
      ],
    }
    good=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["authenticated_P184_Windows_baseline"]=authenticate_P184(
            os.environ.get("P185_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for key in list(env):
            if key in {"P185_ARCHIVE_TOKEN","GITHUB_TOKEN","GH_TOKEN"} or key.endswith(("_API_KEY","_SECRET")):
                env.pop(key,None)
        selectors=[
          "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests",
          "scripts.p181_windows_batch_transport_security_review.P181BatchAdversarialSecurityTests",
          "scripts.p182_windows_fail_closed_batch_transport.P182FailClosedBatchSecurityCases",
          "scripts.p183_windows_historical_security_equivalence.P183HistoricalEquivalenceAdversarialCases",
          "scripts.p184_windows_fresh_historical_source_admission.P184FreshHistoricalSourceAdmissionTests",
          "scripts.p185_windows_historical_tag_parent_seal_admission.P185HistoricalTagSealAdmissionTests",
          "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_self_canonicalization_only_zeros_own_single_literal",
        ]
        log=out/"p185_authentic_Windows_69_historical_tag_parent_and_original_security_cases.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",*selectors],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=140,check=False)
        raw=log.read_bytes()
        t=raw.decode("utf8","replace").replace("\r\n","\n")
        count=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)
        ledger["genuine_Windows_native_result"]={
            "original_P180_cases":8,"original_P181_cases":12,
            "original_P182_cases":12,"original_P183_cases":12,
            "original_P184_cases":12,"new_P185_adversarial_cases":12,
            "original_frozen_BYOK_B_control":1,
            "complete_unittest_count":int(count[-1]) if count else None,
            "native_exit":p.returncode,"original_complete_raw_log_SHA256":sha(raw),
            "log_filename":log.name,
            "original_named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",t,re.M),
        }
        if p.returncode!=0 or count!=["69"] or not re.search(r"^OK\s*$",t,re.M):
            raise RuntimeError("P185 genuine original Windows 69-case narrow security evidence not all complete")
        ledger["source_after"]=custody()
        good=(before==ledger["source_after"])
        if not good:raise RuntimeError("P185 original source drift after real native execution")
        print("P185_NATIVE_WINDOWS_ORIGINAL_SECURITY_AND_TAG_CASES=69/69_PASS|EXIT=0",flush=True)
        print("P185_ORIGINAL_P180_P181_P182_P183_P184_TESTS=56_UNMODIFIED",flush=True)
        print("P185_ORIGINAL_BYOK_B_FROZEN_SELF_CONTROL=1_PASS",flush=True)
        print("P185_ANNOTATED_TAG_PARENT_TREE_ANCESTRY_AND_A_SOURCE_SHA256=DOUBLE_OBSERVED",flush=True)
        print("P185_FRESH_PARENT_READ_POST_TAG_TAMPER=REJECTED_BY_ISOLATED_CANDIDATE",flush=True)
        print("P185_ENTIRE_ORIGINAL_B_23FILE_SECURITY_VERIFIER=UNMODIFIED_AND_NOT_REPLACED",flush=True)
        print("P185_RAW_WINDOWS_LOG_SHA256="+sha(raw),flush=True)
        print("P185_EXTERNAL_QUALIFIED_REVIEW=7_OPEN|FULL_PRODUCT_NATIVE=0/3|RELEASE=HOLD",flush=True)
    except Exception as exc:
        ledger["collector_error"]=repr(exc)
        print("P185_WINDOWS_SOURCE_TAG_SEAL_ADMISSION=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["original_source_authenticated_narrow_historical_parent_tag_evidence_complete_not_release"]=good
        (out/"p185_source_preserving_historical_tag_parent_seal_review_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
