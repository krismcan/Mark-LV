"""P186: original sealed A(11) and B(23) blob pin-envelope witness, HOLD.

Native Windows, source-preserving, separate exact source identities for
branch-specific P184 and P185 originals. Test all 34 immutable historical
file pins and 34 targeted tamper refusals using genuine Git-backed bytes,
never modify frozen production verifiers, Git history or Kristian's worktree.

This verifies *historical object + static SHA256 pin parity*; it is NOT
equivalent to original 8.30...BYOK-B full disk/index/branch/Win32 admission.
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
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_scope_migration as A
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
BASE="68b338723ba9130be071289c7662c9d68db748f4"
BRANCH="byok-c1-p186-full-historical-a-b-envelope-witness-20261113"
NEW={
 ".github/workflows/p186-windows-full-historical-envelope-witness.yml",
 "docs/byok-c1-p186-historical-A11-B23-envelope-witness.md",
 "scripts/p186_windows_full_historical_envelope_witness.py",
}
A_COMMIT="4110fa69849f8127a325f9a9001284cd1bd3a59c"
A_TREE="747f172144794d687251545ca923d5ebb5b1551b"
A_PARENT="87208af710bac90c440f2e0851854318b22e9b88"
A_TAG="nayeon-v1-phase8-byok-first-run-owner-fake-only-01"
A_TAG_OBJECT="7496961c83de9607402dcdabff25917674d6688a"
B_COMMIT="e3612279cb972e68e2487702183d5bf5b8f6c4a1"
B_TREE="99624a766e864addf5d096bb1a907c85d11401dc"
REVIEWS={k:"OPEN" for k in
 ("GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}
P184_REF="byok-c1-p184-fresh-historical-source-admission-20261112"
P184_HEAD="a66a5221ab74d0b7f65fd381c554f186cd6c8ed1"
P185_REF="byok-c1-p185-historical-tag-seal-parent-admission-20261113"
P185_ID=13997207555
P185_ZIP_SHA="81A985B84CE819AE1254FB01E51051F727C7966E3B64447E2C228FCEEF52AC3C"
P185_P184_LOG="p185_exact_original_P184_branch_Windows_12_cases.log"
P185_P184_LOG_SHA="9009A6C295D83A425BB4E049C4A5E0A8BEDB6E926B4216DB417F3571BF1BA612"
P185_CUR_LOG="p185_authentic_Windows_57_current_source_historical_tag_and_security_cases.log"
P185_CUR_LOG_SHA="6AD2CCB4C31FCC1D37022EECBFBC7D8319DA197C2307C9F1C7596FBB43771669"
P185_LEDGER="p185_source_preserving_historical_tag_parent_seal_review_ledger.json"
SOURCES={"A":(A_COMMIT,A.CANDIDATE_SHA256,A._digest),
         "B":(B_COMMIT,B.CANDIDATE_SHA256,B._digest)}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args:str, root:Path=ROOT)->bytes:
    return subprocess.run(
        ["git","-C",str(root),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        check=True,timeout=35).stdout

def demand_original_baseline()->None:
    if (A.PARENT!=A_PARENT or
        B.PARENT!=A_COMMIT or B.PARENT_TREE!=A_TREE or
        B.PARENT_PARENT!=A_PARENT or B.PARENT_TAG!=A_TAG
        or B.PARENT_TAG_OBJECT!=A_TAG_OBJECT
        or len(A.CANDIDATE_SHA256)!=11 or A.ENVELOPE!=set(A.CANDIDATE_SHA256)
        or len(B.CANDIDATE_SHA256)!=23 or B.ENVELOPE!=set(B.CANDIDATE_SHA256)
        or B.SELF!="tests/phase8_byok_b_scope_migration.py"):
        raise RuntimeError("P186 original immutable historical source manifest shifted")
    if (any(not re.fullmatch(r"[a-f0-9]{64}",p) or p=="0"*64
            for m in (A.CANDIDATE_SHA256,B.CANDIDATE_SHA256) for p in m.values())):
        raise RuntimeError("P186 frozen SHA256 pins missing")
    if set(A.CANDIDATE_SHA256)==set(B.CANDIDATE_SHA256):
        raise RuntimeError("P186 A11 and B23 must be distinct manifest scopes")

def custody()->dict:
    _guard_runner()
    demand_original_baseline()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P186 exact clean authentic native Windows source required")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P186 only three new review-only files may be added")
    for part in ("tests","nayeon"):
        if git("rev-parse",BASE+":"+part)!=git("rev-parse","HEAD:"+part):
            raise RuntimeError("P186 original frozen historical and product source changed")
    for path in [
        "scripts/p180_windows_sealed_blob_transport_equivalence.py",
        "scripts/p181_windows_batch_transport_security_review.py",
        "scripts/p182_windows_fail_closed_batch_transport.py",
        "scripts/p183_windows_historical_security_equivalence.py",
        "scripts/p184_windows_fresh_historical_source_admission.py",
        "scripts/p185_windows_historical_tag_parent_seal_admission.py",
        "tests/phase8_byok_scope_migration.py",
        "tests/phase8_byok_b_scope_migration.py",
    ]:
        if (ROOT/path).read_bytes()!=git("show",BASE+":"+path):
            raise RuntimeError("P186 historical source/old reviewer prototype modified: "+path)
    mods=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
          if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(mods)!=171:
        raise RuntimeError("P186 frozen 171 test modules shifted")
    return {
      "P186_source_SHA":git("rev-parse","HEAD").decode().strip(),
      "exact_P185_parent":BASE,"only_three_added_paths":sorted(NEW),
      "product_tests_P180_to_P185_prototypes_untouched":True,
      "original_frozen_test_modules":171,"immutable_A_manifest_count":11,
      "immutable_B_manifest_count":23,
    }

def authenticate_P185(token:str)->dict:
    if len(token)<8:raise RuntimeError("P186 ephemeral artifact token missing")
    raw=_download_artifact(P185_ID,P185_ZIP_SHA,token)
    if sha(raw)!=P185_ZIP_SHA:raise RuntimeError("P186 P185 authentic ZIP digest changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if (z.testzip() is not None or len(z.namelist())!=3
            or set(z.namelist())!={P185_P184_LOG,P185_CUR_LOG,P185_LEDGER}):
            raise RuntimeError("P186 P185 original 3-member ZIP/CRC changed")
        x=json.loads(z.read(P185_LEDGER))
        p184=z.read(P185_P184_LOG)
        current=z.read(P185_CUR_LOG)
        a=x.get("original_P184_native_Windows_exact_source_12_cases",{})
        b=x.get("genuine_Windows_native_result",{})
        if (x.get("checkpoint")!="P185" or x.get("source_before")!=x.get("source_after")
            or x.get("source_before",{}).get("exact_P185_HEAD")!=BASE
            or x.get("historical_H")!="HOLD" or x.get("production_R")!="HOLD"
            or x.get("full_product_native_Windows_regressions")!="0/3"
            or x.get("seven_qualified_external_decisions")!=REVIEWS
            or x.get("historical_B_full_23_file_verifier_replaced_or_bypassed") is not False
            or x.get("original_source_authenticated_narrow_historical_parent_tag_evidence_complete_not_release") is not True
            or a.get("source_HEAD")!=P184_HEAD
            or a.get("original_frozen_P184_tests")!=12
            or a.get("complete_unittest_count")!=12 or a.get("native_exit")!=0
            or a.get("complete_raw_log_SHA256")!=P185_P184_LOG_SHA
            or b.get("complete_current_branch_unittest_count")!=57 or b.get("native_exit")!=0
            or b.get("aggregate_two_exact_source_branches_genuine_native_tests")!=69
            or b.get("original_complete_raw_log_SHA256")!=P185_CUR_LOG_SHA
            or sha(p184)!=P185_P184_LOG_SHA or sha(current)!=P185_CUR_LOG_SHA):
            raise RuntimeError("P186 original P185 source-separated 12+57 Windows log/governance drift")
        for name,rawlog,n in ((P185_P184_LOG,p184,"12"),(P185_CUR_LOG,current,"57")):
            text=rawlog.decode("utf8","replace").replace("\r\n","\n")
            if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=[n]
                or not re.search(r"^OK\s*$",text,re.M)):
                raise RuntimeError("P186 P185 authentic original full footer altered "+name)
    return {"authentic_P185_artifact":P185_ID,"ZIP_SHA256":P185_ZIP_SHA,
            "prior_native_Windows_P184_at_exact_HEAD":12,
            "prior_native_Windows_P185_current":57,
            "sum_two_true_source_identities":69,"qualified_external_signoff":"OPEN"}

def original_chain()->tuple[str,...]:
    # Historical Git chain; no authority is learned from the mutable current
    # branch except its exact source identity, asserted in custody.
    return (
      git("rev-parse","HEAD").decode().strip(),
      git("branch","--show-current").decode().strip(),
      git("rev-parse","--show-object-format").decode().strip(),
      git("show-ref","--verify","--hash","--","refs/tags/"+A_TAG).decode().strip(),
      git("cat-file","-t",A_TAG_OBJECT).decode().strip(),
      git("rev-parse","--verify","--end-of-options",A_TAG_OBJECT+"^{}").decode().strip(),
      git("rev-parse",A_COMMIT+"^{tree}").decode().strip(),
      git("rev-list","--parents","-n","1",A_COMMIT).decode().strip(),
      git("rev-parse",B_COMMIT+"^{tree}").decode().strip(),
      git("rev-list","--parents","-n","1",B_COMMIT).decode().strip(),
    )

def demand_chain(chain:tuple[str,...])->None:
    expected=(
      os.environ["GITHUB_SHA"],BRANCH,"sha1",A_TAG_OBJECT,"tag",
      A_COMMIT,A_TREE,A_COMMIT+" "+A_PARENT,
      B_TREE,B_COMMIT+" "+A_COMMIT,
    )
    if chain!=expected:
        raise RuntimeError("P186 original exact A/B tagged parent/HEAD/tree ancestry admission refused")

def original_data(envelope:str,path:str)->bytes:
    commit,manifest,_=SOURCES[envelope]
    if path not in manifest:
        raise ValueError("P186 unknown original pinned historical path")
    if not p180.valid_path(path):
        raise ValueError("P186 noncanonical original path denied")
    return git("show",commit+":"+path)

def original_oid(envelope:str,path:str)->bytes:
    commit,manifest,_=SOURCES[envelope]
    if path not in manifest or not p180.valid_path(path):
        raise ValueError("P186 unapproved pinned source path")
    record=git("ls-tree","--full-tree","-z",commit,"--",path)
    m=re.fullmatch(rb"100644 blob ([0-9a-f]{40})\t"+
                   re.escape(path.encode("ascii"))+rb"\0",record)
    if m is None:raise RuntimeError("P186 historical parent source not regular 100644 blob")
    return m.group(1)

def validate_source(envelope:str,path:str,payload:bytes,oid:bytes)->None:
    _,manifest,digest=SOURCES[envelope]
    if (path not in manifest or not p180.valid_path(path)
        or not isinstance(payload,bytes) or not p180.valid_oid(oid)):
        raise ValueError("P186 malformed original source verification")
    if digest(path,payload)!=manifest[path]:
        raise ValueError("P186 original literal historical SHA256 seal mismatch: "+path)
    hashed=hashlib.sha1(b"blob "+str(len(payload)).encode()+b"\0"+payload).hexdigest().encode()
    if hashed!=oid:
        raise ValueError("P186 historical Git blob OID/content mismatch")

@dataclass(frozen=True)
class EnvelopeReceipt:
    A: int
    B: int
    source_SHA256s: dict[str,str]
    pre_post_chain_same: bool

class HistoricalAandBEnvelopeWitness:
    """Experimental envelope witness; not the original live B verifier.

    Re-evaluates historical tagged ancestry once BEFORE/AFTER entire envelope
    and every source blob's immutable SHA256 seal and Git mode+OID; no
    production trust is cached. Does NOT check current disk/index/Win32 races.
    """
    def __init__(self,*,observe=None,transport=None):
        self.observe=observe or original_chain
        self.transport=transport or p182.FailClosedGitBatch(timeout_seconds=7)
        self.retired=False
        self.accepted=0
    def close(self):
        self.retired=True
        self.transport.close()
    def read_one(self,envelope:str,path:str)->bytes:
        if self.retired:
            raise RuntimeError("P186 retired envelope source probe")
        try:
            if envelope not in SOURCES or path not in SOURCES[envelope][1]:
                raise ValueError("P186 original envelope/path not allowlisted")
            oid=original_oid(envelope,path)
            raw=self.transport.read(oid)
            validate_source(envelope,path,raw,oid)
            return raw
        except BaseException:
            self.close()
            raise
    def read_envelope(self,envelopes=("A","B"))->EnvelopeReceipt:
        if self.retired:raise RuntimeError("P186 retired historical envelope probe")
        try:
            before=self.observe()
            demand_chain(before)
            hashes={}
            counts={"A":0,"B":0}
            for name in envelopes:
                if name not in SOURCES:
                    raise ValueError("P186 unknown historical envelope")
                for path in sorted(SOURCES[name][1]):
                    payload=self.read_one(name,path)
                    # Cross-check an independent, true git show read; do not
                    # trust either an OID alone or an in-memory fixture.
                    if payload!=original_data(name,path):
                        raise RuntimeError("P186 independently fetched original source bytes mismatch")
                    hashes[name+":"+path]=sha(payload)
                    counts[name]+=1
            after=self.observe()
            demand_chain(after)
            if before!=after:
                raise RuntimeError("P186 historical tag/head/tree parent drift during manifest")
            self.accepted+=1
            return EnvelopeReceipt(counts["A"],counts["B"],hashes,True)
        except BaseException:
            self.close()
            raise

class _MockTransport:
    def __init__(self,data:bytes):
        self.data=data
        self.closed=False
        self.reads=[]
    def read(self,oid:bytes)->bytes:
        if self.closed:raise RuntimeError("P186 poisoned pipe reused")
        self.reads.append(oid)
        return self.data
    def close(self):self.closed=True

class P186OriginalFullHistoricalPinEnvelopeCases(unittest.TestCase):
    """12 negative/positive methods; 34 full-blob and 34 targeted witnesses."""
    def test_01_exact_A11_B23_manifest_origins_and_immutable_frozen_source(self):
        demand_original_baseline()
        self.assertEqual(len(A.CANDIDATE_SHA256),11)
        self.assertEqual(len(B.CANDIDATE_SHA256),23)
        self.assertNotEqual(A.CANDIDATE_SHA256,B.CANDIDATE_SHA256)
        self.assertEqual(A.SELF,"tests/phase8_byok_scope_migration.py")
        self.assertEqual(B.SELF,"tests/phase8_byok_b_scope_migration.py")
        self.assertTrue(A.SELF in A.CANDIDATE_SHA256 and B.SELF in B.CANDIDATE_SHA256)

    def test_02_historical_A_B_tag_trees_and_linear_parent_commit_chain(self):
        demand_chain(original_chain())
        self.assertEqual(git("cat-file","-t",A_COMMIT),b"commit\n")
        self.assertEqual(git("cat-file","-t",B_COMMIT),b"commit\n")

    def test_03_all_original_A11_pins_live_Git_blob_vs_bounded_batch(self):
        w=HistoricalAandBEnvelopeWitness()
        try:
            receipt=w.read_envelope(("A",))
            self.assertEqual((receipt.A,receipt.B),(11,0))
            self.assertEqual(len(receipt.source_SHA256s),11)
        finally:w.close()

    def test_04_all_original_B23_pins_live_Git_blob_vs_bounded_batch(self):
        w=HistoricalAandBEnvelopeWitness()
        try:
            receipt=w.read_envelope(("B",))
            self.assertEqual((receipt.A,receipt.B),(0,23))
            self.assertEqual(len(receipt.source_SHA256s),23)
        finally:w.close()

    def test_05_each_of_34_original_historical_file_pins_rejects_its_own_tamper(self):
        refused=[]
        for name in ("A","B"):
            for path in sorted(SOURCES[name][1]):
                original=original_data(name,path)
                oid=original_oid(name,path)
                validate_source(name,path,original,oid)
                with self.subTest(envelope=name,target=path):
                    with self.assertRaisesRegex(ValueError,"SHA256 seal mismatch"):
                        validate_source(name,path,original+b" P186 negative canary",oid)
                refused.append(name+":"+path)
        self.assertEqual(len(refused),34)
        self.assertEqual(len(set(refused)),34)

    def test_06_wrong_historical_git_oid_and_file_type_are_rejected(self):
        for name in ("A","B"):
            path=next(iter(sorted(SOURCES[name][1])))
            raw=original_data(name,path)
            oid=original_oid(name,path)
            with self.subTest(name=name,kind="oid"):
                with self.assertRaisesRegex(ValueError,"OID/content mismatch"):
                    validate_source(name,path,raw,b"a"*40)
            self.assertEqual(len(oid),40)

    def test_07_original_A_and_B_self_canonicalization_seals_remain_distinct(self):
        for name,gate in (("A",A),("B",B)):
            path=gate.SELF
            raw=original_data(name,path)
            self.assertEqual(gate._digest(path,raw),gate.CANDIDATE_SHA256[path])
            self.assertEqual(len(gate.SELF_PIN.findall(raw)),1)

    def test_08_forged_annotated_tag_commit_or_parent_tree_is_rejected(self):
        original=original_chain()
        demand_chain(original)
        for index,bad in ((3,"a"*40),(4,"commit"),(5,"a"*40),
                          (6,"a"*40),(7,A_COMMIT+" "+"a"*40),
                          (8,"a"*40),(9,B_COMMIT+" "+"a"*40)):
            with self.subTest(index=index):
                changed=list(original)
                changed[index]=bad
                with self.assertRaises(RuntimeError):
                    demand_chain(tuple(changed))

    def test_09_post_envelope_source_tag_change_poison_session(self):
        real=original_chain()
        mutated=list(real);mutated[3]="a"*40
        observations=iter([real,tuple(mutated)])
        w=HistoricalAandBEnvelopeWitness(observe=lambda:next(observations))
        try:
            with self.assertRaisesRegex(RuntimeError,"admission refused"):
                w.read_envelope(("A",))
            self.assertTrue(w.retired)
        finally:w.close()

    def test_10_path_alias_and_wrong_historical_epoch_refused(self):
        for name,path in (
            ("A","tests/../other"),
            ("B","tests\\phase8_byok_b_scope_migration.py"),
            ("A","tests/phase8_byok_b_scope_migration.py"),
            ("B","tests/phase8_byok_scope_migration.py:stream"),
            ("Z","tests/phase8_byok_scope_migration.py"),
        ):
            with self.subTest(name=name,path=path):
                w=HistoricalAandBEnvelopeWitness()
                with self.assertRaises(ValueError):
                    w.read_one(name,path)
                self.assertTrue(w.retired)

    def test_11_bounded_batch_source_refuses_pinned_legacy_blob_tamper(self):
        name="A"
        path=next(iter(sorted(A.CANDIDATE_SHA256)))
        original=original_data(name,path)
        fake=_MockTransport(original+b" tampered")
        w=HistoricalAandBEnvelopeWitness(transport=fake)
        with self.assertRaises(ValueError):
            w.read_one(name,path)
        self.assertTrue(w.retired)
        self.assertTrue(fake.closed)
        self.assertEqual(len(fake.reads),1)

    def test_12_full_original_live_ByokB_disk_index_and_security_GO_still_OPEN(self):
        source=(ROOT/"tests/phase8_byok_b_scope_migration.py").read_text(encoding="utf8")
        for method in ("_parent_tree","_raw_delta","_index_flags","_disk",
                       "assert_byok_b_integrity","_canonical_paths","ENVELOPE"):
            self.assertIn(method,source)
        self.assertEqual(len(B.ENVELOPE),23)
        self.assertEqual(set(REVIEWS),{"GOV-01","GOV-02","SEC-03","SEC-04",
                                      "REL-05","REL-06","REL-07"})
        self.assertFalse(hasattr(HistoricalAandBEnvelopeWitness,"assert_byok_b_integrity"))

def run_exact_prior(original_root:Path,expected_head:str,expected_branch:str,
                    selector:str,output:Path,env:dict)->dict:
    root=original_root.resolve()
    if root==ROOT or not root.is_dir():
        raise RuntimeError("P186 missing independent original historical source clone")
    if (git("rev-parse","HEAD",root=root).decode().strip()!=expected_head
        or git("branch","--show-current",root=root).decode().strip()!=expected_branch
        or git("status","--porcelain=v1",root=root).strip()
        or git("rev-parse","HEAD:tests",root=root)!=git("rev-parse",BASE+":tests")
        or git("rev-parse","HEAD:nayeon",root=root)!=git("rev-parse",BASE+":nayeon")):
        raise RuntimeError("P186 exact original branch and immutable source not authenticated")
    with output.open("wb") as f:
        process=subprocess.run([sys.executable,"-B","-m","unittest","-v",selector],
            cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=f,
            stderr=subprocess.STDOUT,timeout=110,check=False)
    raw=output.read_bytes()
    t=raw.decode("utf8","replace").replace("\r\n","\n")
    counts=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)
    if (process.returncode!=0 or counts!=["12"]
        or not re.search(r"^OK\s*$",t,re.M)):
        raise RuntimeError("P186 exact original source tests incomplete for "+expected_branch)
    return {
       "head":expected_head,"branch":expected_branch,
       "original_source_unmodified_tests":12,
       "complete_native_test_count":12,
       "real_OS_exit":process.returncode,
       "complete_raw_log_SHA256":sha(raw),"log_filename":output.name,
       "original_named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",t,re.M),
    }

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p186-historical-envelope"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P186","historical_H":"HOLD",
        "current_C":"ISOLATED_ORIGINAL_A11_B23_BLOB_ENVELOPE_WITNESS_ONLY",
        "production_R":"HOLD","full_product_original_native_Windows":"0/3",
        "qualified_external_reviewer_decisions":REVIEWS,
        "privileged_C1_G0_G6":"OPEN","signed_main_helper_installer_cert_and_WDAC_SAC_GO":False,
        "original_full_BYOK_B_live_worktree_verifier_replaced":False,
        "original_source_ERA_8_30_to_B_tests_modified":False,
        "original_P135_three_full_600sec_timeouts":"UNWAIVED",
        "original_P175_five_old_failures":"UNWAIVED",
        "original_P178_165sec_B_module_timeout_two_FAIL":"UNWAIVED",
        "original_P179_130sec_historical_pin_witness_timeout":"UNWAIVED",
        "original_full_envelope_witness_limits":[
            "does not call the complete original B real current worktree/index/disk/admission verifier",
            "does not prove a secure atomic Windows file/reparse/parent writer race boundary",
            "does not satisfy all older source-era chain and negative canaries",
            "does not prove faster full suite performance, reviewer GO or product integration",
        ],
    }
    good=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["authenticated_original_P185_windows"]=authenticate_P185(
             os.environ.get("P186_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for k in list(env):
            if k in {"P186_ARCHIVE_TOKEN","GH_TOKEN","GITHUB_TOKEN"} or k.endswith(("_API_KEY","_SECRET")):
                env.pop(k,None)
        originals=[
          ("P184",P184_REF,P184_HEAD,
           "scripts.p184_windows_fresh_historical_source_admission.P184FreshHistoricalSourceAdmissionTests",
           "p186_exact_original_P184_branch_12_native_Windows_cases.log",
           "P186_ORIGINAL_P184_CLONE_ROOT"),
          ("P185",P185_REF,BASE,
           "scripts.p185_windows_historical_tag_parent_seal_admission.P185HistoricalTagSealAdmissionTests",
           "p186_exact_original_P185_branch_12_native_Windows_cases.log",
           "P186_ORIGINAL_P185_CLONE_ROOT"),
        ]
        ledger["original_unchanged_branch_specific_test_runs"]={}
        for label,branch,head,selector,logname,envname in originals:
            path=os.environ.get(envname,"")
            if not path:raise RuntimeError("P186 missing exact historical original clone "+label)
            ledger["original_unchanged_branch_specific_test_runs"][label]=run_exact_prior(
                Path(path),head,branch,selector,out/logname,env)
        selectors=[
           "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests",
           "scripts.p181_windows_batch_transport_security_review.P181BatchAdversarialSecurityTests",
           "scripts.p182_windows_fail_closed_batch_transport.P182FailClosedBatchSecurityCases",
           "scripts.p183_windows_historical_security_equivalence.P183HistoricalEquivalenceAdversarialCases",
           "scripts.p186_windows_full_historical_envelope_witness.P186OriginalFullHistoricalPinEnvelopeCases",
           "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_self_canonicalization_only_zeros_own_single_literal",
        ]
        rawlog=out/"p186_current_Windows_57_historical_A11_B23_and_prior_security_cases.log"
        with rawlog.open("wb") as f:
            run=subprocess.run([sys.executable,"-B","-m","unittest","-v",*selectors],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=190,check=False)
        raw=rawlog.read_bytes()
        t=raw.decode("utf8","replace").replace("\r\n","\n")
        count=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)
        ledger["current_P186_native_Windows"]={
             "original_P180_cases":8,"original_P181_cases":12,
             "original_P182_cases":12,"original_P183_cases":12,
             "new_P186_cases":12,"original_frozen_B_self_control":1,
             "full_unittest_count":int(count[-1]) if count else None,
             "native_OS_exit":run.returncode,"complete_raw_log_SHA256":sha(raw),
             "raw_log_name":rawlog.name,
             "original_named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",t,re.M),
             "real_original_A_static_SHA256_pin_checks":11,
             "real_original_B_static_SHA256_pin_checks":23,
             "targeted_original_individual_A_B_tamper_refusals":34,
        }
        if run.returncode!=0 or count!=["57"] or not re.search(r"^OK\s*$",t,re.M):
            raise RuntimeError("P186 original A11/B23 Windows 57-case evidence incomplete")
        ledger["source_after"]=custody()
        good=(before==ledger["source_after"])
        if not good:raise RuntimeError("P186 source identity drift during actual native tests")
        print("P186_WINDOWS_ORIGINAL_P184_12=12/12_PASS|NATIVE_EXIT=0",flush=True)
        print("P186_WINDOWS_ORIGINAL_P185_12=12/12_PASS|NATIVE_EXIT=0",flush=True)
        print("P186_WINDOWS_CURRENT_ORIGINAL_AND_NEW_57=57/57_PASS|NATIVE_EXIT=0",flush=True)
        print("P186_TOTAL_THREE_EXACT_SOURCE_IDENTITIES=81/81_TESTS_PASS",flush=True)
        print("P186_LIVE_SEALED_A_PINS=11/11|SEALED_B_PINS=23/23|STATIC_SHA256_AND_REAL_GIT_BYTES",flush=True)
        print("P186_TARGETED_BYTE_TAMPER_CANARIES=34/34_REFUSED",flush=True)
        print("P186_FULL_ORIGINAL_LIVE_B_SECURITY_GATE=NOT_REPLACED_AND_NOT_APPROVED",flush=True)
        print("P186_CURRENT_RAW_LOG_SHA256="+sha(raw),flush=True)
        print("P186_P184_ORIGINAL_RAW_LOG_SHA256="+ledger["original_unchanged_branch_specific_test_runs"]["P184"]["complete_raw_log_SHA256"],flush=True)
        print("P186_P185_ORIGINAL_RAW_LOG_SHA256="+ledger["original_unchanged_branch_specific_test_runs"]["P185"]["complete_raw_log_SHA256"],flush=True)
        print("P186_QUALIFIED_EXTERNAL_REVIEW=7_OPEN|FULL_PRODUCT_NATIVE=0/3|RELEASE=HOLD",flush=True)
    except Exception as exc:
        ledger["collector_error"]=repr(exc)
        print("P186_SEALED_A11_B23_WINDOWS_WITNESS=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["authenticated_narrow_historical_envelope_witness_evidence_complete_NOT_product_release"]=good
        (out/"p186_historical_A11_B23_envelope_source_provenance_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
