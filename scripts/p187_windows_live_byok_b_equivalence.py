"""P187 isolated original BYOK-B live-worktree/index refusal experiments.

No production verifier replacement. Only disposable Windows fixture clones and
synthetic frozen-B seams; the original Kristian product worktree is not opened
for writing, and frozen tests/product sources are never changed.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import p186_windows_full_historical_envelope_witness as previous
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B
from tests.test_phase8_byok_b_scope_integrity import candidate

ROOT = Path(__file__).resolve().parents[1]
P186 = "9c6b40ac0e81ac22851b7eb1237b0ec9f06ac3cf"
BRANCH = "byok-c1-p187-live-byok-b-workspace-index-tamper-equivalence-20261113"
ARTIFACT = 14017997880
ARCHIVE_SHA = "D3500950814EE39C2B3FF85F4E6BC007AB4275C8EFDBF6DA034C4EB6CD3F3520"
FILES = {
    "scripts/p187_windows_live_byok_b_equivalence.py",
    "docs/byok-c1-p187-live-workspace-index-tamper-matrix.md",
    ".github/workflows/p187-windows-live-byok-b-equivalence.yml",
}
STATES = ("COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD")
REVIEWS = previous.REVIEWS
A_COMMIT = previous.A_COMMIT
B_COMMIT = previous.B_COMMIT

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args: str, cwd: Path = ROOT, timeout: int = 60) -> bytes:
    return subprocess.run(["git", "-C", str(cwd), *args], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, check=True).stdout

def source_custody() -> dict:
    if (sys.platform != "win32" or os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_OS") != "Windows"
        or os.environ.get("GITHUB_EVENT_NAME") != "push"
        or os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME") != BRANCH
        or git("rev-parse", "HEAD").decode().strip() != os.environ.get("GITHUB_SHA")
        or git("branch", "--show-current").decode().strip() != BRANCH
        or git("merge-base", P186, "HEAD").decode().strip() != P186
        or git("status", "--porcelain=v1").strip()):
        raise RuntimeError("P187 authenticated clean native Windows source required")
    diff = set(git("diff", "--name-only", P186, "HEAD").decode().splitlines())
    if diff != FILES:
        raise RuntimeError("P187 only three additive audit-only files permitted")
    for directory in ("tests", "nayeon"):
        if git("rev-parse", P186 + ":" + directory) != git("rev-parse", "HEAD:" + directory):
            raise RuntimeError("P187 frozen product or original test tree changed")
    for path in (
        "tests/phase8_byok_b_scope_migration.py",
        "tests/test_phase8_byok_b_scope_integrity.py",
        "tests/phase8_byok_scope_migration.py",
        "scripts/p182_windows_fail_closed_batch_transport.py",
        "scripts/p184_windows_fresh_historical_source_admission.py",
        "scripts/p185_windows_historical_tag_parent_seal_admission.py",
        "scripts/p186_windows_full_historical_envelope_witness.py",
    ):
        if (ROOT / path).read_bytes() != git("show", P186 + ":" + path):
            raise RuntimeError("P187 original authority or predecessor script altered: " + path)
    if len(B.CANDIDATE_SHA256) != 23 or B.ENVELOPE != set(B.CANDIDATE_SHA256):
        raise RuntimeError("P187 original sealed B envelope was changed")
    return {"source_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P186_parent":P186,"only_three_new_audit_paths":sorted(FILES),
            "unchanged_original_B_frozen_and_product":True}

def authenticate_p186(token: str) -> dict:
    if len(token) < 8:
        raise RuntimeError("P187 missing temporary original P186 artifact token")
    raw = _download_artifact(ARTIFACT, ARCHIVE_SHA, token)
    if sha(raw) != ARCHIVE_SHA:
        raise RuntimeError("P187 original P186 archive SHA-256 mismatch")
    expected = {
      "p186_exact_original_P184_branch_12_native_Windows_cases.log":
          ("12","E818DB493A7FA2022E91D12358C28E5E8D0C27663B3DCA7079C3D17F41079784"),
      "p186_exact_original_P185_branch_12_native_Windows_cases.log":
          ("12","53D6336F84518EA47EA8BE40EF36AFCE2D62BF591FDB0E2C79F680CF4C205649"),
      "p186_current_Windows_57_historical_A11_B23_and_prior_security_cases.log":
          ("57","941124EEEE42A0C71CB7FF3F3FC5F1B6DEAF2AE34BD097F19ECEF14E802281AF"),
    }
    ledger_name = "p186_historical_A11_B23_envelope_source_provenance_ledger.json"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or set(z.namelist()) != set(expected) | {ledger_name}:
            raise RuntimeError("P187 original P186 ZIP member inventory/CRC mismatch")
        for name,(n,digest) in expected.items():
            content=z.read(name)
            text=content.decode("utf8","replace").replace("\r\n","\n")
            if (sha(content)!=digest or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=[n]
                or not re.search(r"^OK\s*$",text,re.M)):
                raise RuntimeError("P187 original P186 raw native Windows source log mismatch: "+name)
        evidence=json.loads(z.read(ledger_name))
        if (evidence.get("checkpoint")!="P186" or evidence.get("historical_H")!="HOLD"
            or evidence.get("production_R")!="HOLD"
            or evidence.get("full_product_original_native_Windows")!="0/3"
            or evidence.get("qualified_external_reviewer_decisions")!=REVIEWS
            or evidence.get("source_before")!=evidence.get("source_after")
            or evidence["source_before"]["P186_source_SHA"]!=P186
            or evidence.get("original_full_BYOK_B_live_worktree_verifier_replaced") is not False):
            raise RuntimeError("P187 original P186 HOLD/custody lineage mismatch")
    return {"original_P186_artifact":ARTIFACT,"archive_SHA256":ARCHIVE_SHA,
            "original_native_Windows_3_source_counts":[12,12,57],
            "original_native_Windows_total_selected":81,
            "historical_H":"HOLD","release_R":"HOLD"}

class FullOriginalBAdmissionBoundBatch:
    """Experimental pre/post ORIGINAL complete B gate around a B blob read.

    This is NOT atomic Win32 handle admission, a proven race-free transaction,
    a replacement of the successor live Phase 10 verifier, or authorised
    production integration. No successful gate result is ever cached.
    """
    def __init__(self, *, admission=None, transport=None):
        self.admission = admission or B._assert_byok_b_historical
        self.transport = transport or previous.p182.FailClosedGitBatch(timeout_seconds=5)
        self.retired = False
        self.accepted = 0
    def close(self) -> None:
        if not self.retired:
            self.retired=True
            self.transport.close()
    def read(self,path: str) -> bytes:
        if self.retired:
            raise RuntimeError("P187 retired session cannot be reused")
        try:
            if path not in B.CANDIDATE_SHA256 or not previous.canonical_legacy_path(path):
                raise ValueError("P187 only original exact 23 canonical B source paths")
            before=self.admission()
            if before not in STATES or type(before) is not str:
                raise RuntimeError("P187 original full B admission refused")
            oid=previous.original_oid("B",path)
            payload=self.transport.read(oid)
            previous.validate_source("B",path,payload,oid)
            after=self.admission()
            if after!=before:
                raise RuntimeError("P187 original full B pre/post live admission changed")
            self.accepted+=1
            return payload
        except BaseException:
            self.close()
            raise

class FakeTransport:
    def __init__(self,raw: bytes):
        self.raw=raw
        self.closed=False
        self.reads=[]
    def read(self,oid: bytes) -> bytes:
        self.reads.append(oid)
        return self.raw
    def close(self) -> None:
        self.closed=True

class P187OriginalBSourceBoundTests(unittest.TestCase):
    def test_01_original_frozen_B_gate_and_full_manifest_are_unchanged(self):
        self.assertEqual(len(B.ENVELOPE),23)
        self.assertEqual(len(B.ADDED),7)
        self.assertEqual(len(B.MODIFIED),16)
        self.assertIsNot(B._assert_byok_b_historical,B.assert_byok_b_integrity)
        self.assertEqual(B.PARENT,A_COMMIT)
        self.assertEqual(previous.B_COMMIT,B_COMMIT)

    def test_02_original_complete_live_B_gate_wraps_both_sides_of_one_blob(self):
        path=sorted(B.ENVELOPE)[0]
        raw=previous.original_data("B",path)
        for state in STATES:
            with self.subTest(state=state), candidate(state):
                calls=[]
                def full_b():
                    calls.append("ORIGINAL_FULL_B")
                    return B._assert_byok_b_historical()
                transport=FakeTransport(raw)
                adapter=FullOriginalBAdmissionBoundBatch(admission=full_b,transport=transport)
                try:
                    self.assertEqual(adapter.read(path),raw)
                    self.assertEqual(calls,["ORIGINAL_FULL_B","ORIGINAL_FULL_B"])
                    self.assertEqual(adapter.accepted,1)
                    self.assertFalse(adapter.retired)
                    self.assertEqual(transport.reads,[previous.original_oid("B",path)])
                finally:
                    adapter.close()

    def test_03_original_B_each_of_23_disk_byte_mutations_refuses_intended_target(self):
        with candidate():
            true_disk=B._disk
            touched=[]
            for target in sorted(B.ENVELOPE):
                def corrupt(path, goal=target):
                    raw=true_disk(path)
                    if path==goal:
                        touched.append(path)
                        return raw+b" P187 targeted synthetic disk tamper"
                    return raw
                with self.subTest(target=target), mock.patch.object(B,"_disk",side_effect=corrupt):
                    transport=FakeTransport(previous.original_data("B",target))
                    adapter=FullOriginalBAdmissionBoundBatch(transport=transport)
                    with self.assertRaisesRegex(AssertionError,
                            "BYOK B candidate byte mismatch: "+re.escape(target)):
                        adapter.read(target)
                    self.assertEqual(transport.reads,[])
                    self.assertTrue(adapter.retired)
                    self.assertTrue(transport.closed)
                self.assertEqual(touched[-1],target)
            self.assertEqual(len(touched),23)
            self.assertEqual(set(touched),B.ENVELOPE)

    def test_04_original_B_live_index_ignored_untracked_branch_refusals(self):
        path=sorted(B.ENVELOPE)[0]
        target=("ls-files","--stage","-z")
        tamper=[
          (target,b"120000 "+b"a"*40+b" 0\tunapproved-link\0"),
          (("ls-files","--others","--ignored","--exclude-standard","-z"),
            b"tests/__pycache__/unexpected.pyc\0"),
          (("ls-files","--others","--exclude-standard","-z"),b"other/extra.py\0"),
        ]
        with candidate():
            true_git=B.prior._git
            for query,suffix in tamper:
                def altered(*args, query=query, suffix=suffix):
                    raw=true_git(*args)
                    return raw+suffix if args==query else raw
                with self.subTest(query=query),mock.patch.object(B.prior,"_git",side_effect=altered):
                    transport=FakeTransport(previous.original_data("B",path))
                    adapter=FullOriginalBAdmissionBoundBatch(transport=transport)
                    with self.assertRaises(AssertionError):
                        adapter.read(path)
                    self.assertEqual(transport.reads,[])
                    self.assertTrue(adapter.retired)

    def test_05_post_transport_source_admission_drift_retires_instead_of_accepting(self):
        path=sorted(B.ENVELOPE)[0]
        calls=[]
        def admission():
            calls.append("observe")
            if len(calls)==2:raise AssertionError("BYOK B source/index drift after transport")
            return "COMPLETE_UNSTAGED"
        transport=FakeTransport(previous.original_data("B",path))
        adapter=FullOriginalBAdmissionBoundBatch(admission=admission,transport=transport)
        with self.assertRaisesRegex(AssertionError,"source/index drift"):
            adapter.read(path)
        self.assertEqual(len(calls),2)
        self.assertEqual(len(transport.reads),1)
        self.assertTrue(adapter.retired)
        self.assertTrue(transport.closed)
        with self.assertRaisesRegex(RuntimeError,"retired"):
            adapter.read(path)

    def test_06_wrong_batch_payload_rejected_after_real_B_gate(self):
        path=sorted(B.ENVELOPE)[0]
        with candidate():
            raw=previous.original_data("B",path)
            transport=FakeTransport(raw+b" wrong")
            adapter=FullOriginalBAdmissionBoundBatch(transport=transport)
            with self.assertRaisesRegex(ValueError,"SHA256 seal mismatch"):
                adapter.read(path)
            self.assertTrue(adapter.retired)
            self.assertTrue(transport.closed)

    def test_07_success_is_not_reused_after_original_live_B_disk_poison(self):
        path=sorted(B.ENVELOPE)[0]
        with candidate():
            true_disk=B._disk
            transport=FakeTransport(previous.original_data("B",path))
            adapter=FullOriginalBAdmissionBoundBatch(transport=transport)
            self.assertEqual(adapter.read(path),transport.raw)
            with mock.patch.object(B,"_disk",
                 side_effect=lambda p: true_disk(p)+b"X" if p==path else true_disk(p)):
                with self.assertRaisesRegex(AssertionError,"BYOK B candidate byte mismatch"):
                    adapter.read(path)
            self.assertTrue(adapter.retired)
            self.assertEqual(len(transport.reads),1)

class P187RealWindowsDisposableWorktreeTests(unittest.TestCase):
    """Original sealed-B code + real Git/index/disk; disposable fixture only."""
    @classmethod
    def setUpClass(cls):
        if sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows":
            raise RuntimeError("P187 physical B admission requires actual Windows runner")
        cls.temporary=tempfile.TemporaryDirectory(prefix="p187-byok-b-",dir=os.environ["RUNNER_TEMP"])
        cls.path=Path(cls.temporary.name)/"historical-real-b"
        subprocess.run(["git","clone","--quiet","--no-local",str(ROOT),str(cls.path)],
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=100)
        git("config","--local","core.autocrlf","false",cwd=cls.path)
        git("checkout","--quiet","-b","nayeon-v1",A_COMMIT,cwd=cls.path)
        cls._hydrate()
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"temporary"):
            cls.temporary.cleanup()
    @classmethod
    def _hydrate(cls):
        for path in sorted(B.ENVELOPE):
            if not previous.canonical_legacy_path(path):
                raise RuntimeError("P187 illegal historical B path")
            data=git("show",B_COMMIT+":"+path,cwd=cls.path)
            if B._digest(path,data)!=B.CANDIDATE_SHA256[path]:
                raise RuntimeError("P187 original sealed B physical fixture bytes mismatch")
            output=cls.path/path
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(data)
    def run_original_gate(self):
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        env["PYTHONNOUSERSITE"]="1"
        for key in list(env):
            if key in {"P187_ARCHIVE_TOKEN","GH_TOKEN","GITHUB_TOKEN"} or key.endswith(("_API_KEY","_SECRET")):
                env.pop(key,None)
        code="from tests import phase8_byok_b_scope_migration as b; print('P187_ORIGINAL_B_ADMISSION='+b.assert_byok_b_integrity())"
        p=subprocess.run([sys.executable,"-B","-c",code],cwd=self.path,env=env,
                         stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,timeout=140,check=False)
        return p.returncode,p.stdout.decode("utf8","replace")
    def assert_original_refusal(self,reason):
        exitcode,output=self.run_original_gate()
        self.assertNotEqual(exitcode,0,"Unexpected full original B gate admission: "+output[-2500:])
        self.assertIn("AssertionError: "+reason,output,
                      "Original B refusal occurred at wrong seam: "+output[-3500:])
    def test_08_real_original_sealed_B_all_23_unstaged_sources_admitted(self):
        self.assertEqual(git("rev-parse","HEAD",cwd=self.path).decode().strip(),A_COMMIT)
        code,out=self.run_original_gate()
        self.assertEqual(code,0,out[-3500:])
        self.assertIn("P187_ORIGINAL_B_ADMISSION=COMPLETE_UNSTAGED",out)
    def test_09_real_original_B_index_partial_stage_refused(self):
        target=sorted(B.MODIFIED)[0]
        git("add","--",target,cwd=self.path)
        try:
            self.assert_original_refusal("BYOK B partial stage")
        finally:
            git("reset","-q","--",target,cwd=self.path)
    def test_10_real_original_B_mutated_disk_byte_refused_for_own_pin(self):
        target=B.SELF
        old=(self.path/target).read_bytes()
        (self.path/target).write_bytes(old+b"\n# P187 disposable target corruption\n")
        try:
            self.assert_original_refusal("BYOK B candidate byte mismatch: "+target)
        finally:
            (self.path/target).write_bytes(old)
    def test_11_real_original_B_untracked_unknown_source_refused(self):
        target=self.path/"tests"/"p187_unapproved_untracked_source.py"
        target.write_bytes(b"# disposable unknown\n")
        try:
            self.assert_original_refusal("BYOK B unexpected untracked path")
        finally:
            target.unlink()
    def test_12_real_original_B_exact_23_staged_sources_admitted(self):
        git("add","--",*sorted(B.ENVELOPE),cwd=self.path)
        try:
            code,out=self.run_original_gate()
            self.assertEqual(code,0,out[-3500:])
            self.assertIn("P187_ORIGINAL_B_ADMISSION=EXACT_STAGED",out)
        finally:
            git("reset","-q","--",*sorted(B.ENVELOPE),cwd=self.path)
    def test_13_real_original_B_exact_child_commit_source_admitted(self):
        git("reset","--hard","-q",B_COMMIT,cwd=self.path)
        try:
            code,out=self.run_original_gate()
            self.assertEqual(code,0,out[-3500:])
            self.assertIn("P187_ORIGINAL_B_ADMISSION=EXACT_CHILD",out)
        finally:
            git("reset","--hard","-q",A_COMMIT,cwd=self.path)
            self._hydrate()

def run_exact_original(root: Path, branch: str, head: str,
                       selector: str, output: Path, env:dict) -> dict:
    if (not root.is_dir() or root.resolve()==ROOT.resolve()
        or git("rev-parse","HEAD",cwd=root).decode().strip()!=head
        or git("branch","--show-current",cwd=root).decode().strip()!=branch
        or git("status","--porcelain=v1",cwd=root).strip()):
        raise RuntimeError("P187 old original branch not exact clean source: "+branch)
    return run_unittest(root,[selector],output,env,head,180)

def run_unittest(root: Path,selectors: list[str],output: Path,env:dict,
                 expected_head: str,timeout:int) -> dict:
    if git("rev-parse","HEAD",cwd=root).decode().strip()!=expected_head:
        raise RuntimeError("P187 test source identity changed")
    testenv=dict(env,GITHUB_SHA=expected_head,PYTHONDONTWRITEBYTECODE="1")
    for key in list(testenv):
        if key in {"P187_ARCHIVE_TOKEN","GH_TOKEN","GITHUB_TOKEN"} or key.endswith(("_API_KEY","_SECRET")):
            testenv.pop(key,None)
    with output.open("wb") as f:
        result=subprocess.run([sys.executable,"-B","-m","unittest","-v",*selectors],
             cwd=root,env=testenv,stdin=subprocess.DEVNULL,
             stdout=f,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    raw=output.read_bytes()
    normalized=raw.decode("utf8","replace").replace("\r\n","\n")
    count=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",normalized,re.M)
    return {"native_exit":result.returncode,"complete_unittest_count":int(count[-1]) if count else None,
            "complete_footer_OK":bool(re.search(r"^OK\s*$",normalized,re.M)),
            "log_sha256":sha(raw),"log":output.name,
            "original_named_failures":re.findall(r"^(?:FAIL|ERROR): .+$",normalized,re.M),
            "source_HEAD":expected_head}

def main() -> int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p187-live-b"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P187","historical_H":"HOLD",
            "current_C":"ISOLATED_ORIGINAL_B_FULL_LIVE_GATE_ADAPTER_AND_DISPOSABLE_WINDOWS_NEGATIVES_ONLY",
            "production_R":"HOLD","full_product_original_native_Windows":"0/3",
            "qualified_external_reviewer_decisions":REVIEWS,
            "privileged_G0_G6":"OPEN","signed_SAC_WDAC_GO":False,
            "original_production_verifier_replaced":False,
            "old_failed_P135_P175_P178_P179":"PRESERVED_UNWAIVED",
            "limitations":["not atomic Windows directory/index handles against race writers",
              "not a successful complete original BYOK B frozen test-module run",
              "not approved for original production B verifier integration",
              "not qualified external reviewer authorisation or full-product regression"]}
    ok=False
    try:
        before=source_custody()
        ledger["source_before"]=before
        ledger["original_P186_evidence"]=authenticate_p186(os.environ.get("P187_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        runs=[
          ("P184","P187_P184_ORIGINAL_ROOT","byok-c1-p184-fresh-historical-source-admission-20261112",
           "a66a5221ab74d0b7f65fd381c554f186cd6c8ed1",
           "scripts.p184_windows_fresh_historical_source_admission.P184FreshHistoricalSourceAdmissionTests"),
          ("P185","P187_P185_ORIGINAL_ROOT","byok-c1-p185-historical-tag-seal-parent-admission-20261113",
           "68b338723ba9130be071289c7662c9d68db748f4",
           "scripts.p185_windows_historical_tag_parent_seal_admission.P185HistoricalTagSealAdmissionTests"),
          ("P186","P187_P186_ORIGINAL_ROOT","byok-c1-p186-full-historical-a-b-envelope-witness-20261113",
           P186,"scripts.p186_windows_full_historical_envelope_witness.P186OriginalFullHistoricalPinEnvelopeCases"),
        ]
        ledger["authenticated_version_bound_original_tests"]={}
        for label,var,branch,head,selector in runs:
            r=run_exact_original(Path(os.environ[var]),branch,head,selector,
                  out/("p187_exact_original_"+label+"_Windows_12.log"),env)
            ledger["authenticated_version_bound_original_tests"][label]=r
            if r["native_exit"]!=0 or r["complete_unittest_count"]!=12 or not r["complete_footer_OK"]:
                raise RuntimeError("P187 original "+label+" 12-case native Windows result failed")
        current=run_unittest(ROOT,[
           "scripts.p187_windows_live_byok_b_equivalence.P187OriginalBSourceBoundTests",
           "scripts.p187_windows_live_byok_b_equivalence.P187RealWindowsDisposableWorktreeTests",
        ],out/"p187_current_real_and_synthetic_Windows_13.log",
          env,os.environ["GITHUB_SHA"],650)
        ledger["P187_current_native_Windows"]=current
        if current["native_exit"]!=0 or current["complete_unittest_count"]!=13 or not current["complete_footer_OK"]:
            raise RuntimeError("P187 13 original-gate wrapper/physical fixture cases incomplete")
        after=source_custody()
        ledger["source_after"]=after
        if before!=after:raise RuntimeError("P187 authentic original source drift")
        ok=True
        print("P187_WINDOWS_VERSION_BOUND_ORIGINAL_12_12_12=36/36_PASS|NATIVE_EXIT=0",flush=True)
        print("P187_WINDOWS_FULL_B_GATE_REAL_AND_SYNTHETIC=13/13_PASS|NATIVE_EXIT=0",flush=True)
        print("P187_SYNTHETIC_ORIGINAL_B_TARGETED_DISK_TAMPER_REFUSALS=23/23",flush=True)
        print("P187_REAL_WINDOWS_B_UNSTAGED_STAGED_CHILD=ORIGINAL_GATE_TESTED",flush=True)
        print("P187_FROZEN_TESTS_ORIGINAL_PRODUCT=UNCHANGED|EXTERNAL_REVIEW=OPEN",flush=True)
        print("P187_FULL_PRODUCT_REGRESSIONS=0/3|PRODUCTION_RELEASE=HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P187_AUTHENTIC_SOURCE_BOUND_WINDOWS_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_not_product_release"]=ok
        (out/"p187_live_original_B_workspace_index_tamper_HCR_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
