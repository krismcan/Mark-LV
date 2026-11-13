"""P195 isolated signed fixture authority/restart and native Windows ABA review.
TEST ONLY: ephemeral Ed25519 signer and an independently supplied TEST verifier;
neither enrolment nor epoch persistence is production-trusted. Do not touch BYOK.
"""
from __future__ import annotations
import base64, hashlib, io, json, os, re, subprocess, sys, zipfile
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts import p194_windows_prebound_source_fileid_authority as previous
from scripts import p191_windows_cross_process_source_race_witness as cross
from scripts import p190_windows_handle_bound_source_probe as win
from scripts import p188_windows_physical_source_alias_race_witness as aliases
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B
import unittest

ROOT=Path(__file__).resolve().parents[1]
P194="6f9d6c4316522dec0b5f586bb8d3d9ab5eef9b2b"
BRANCH="byok-c1-p195-authenticated-durable-source-root-aba-20261113"
NEW={".github/workflows/p195-windows-authenticated-root-aba.yml",
     "docs/byok-c1-p195-authenticated-durable-source-root-aba-security-review.md",
     "scripts/p195_windows_durable_root_authority_aba_review.py"}
ARTIFACT=14058754070
ZIP_SHA="1E3CD354F2C0970E57212F7B99556FAE8F7159AB1043164750358F39558147C8"
EXPECTED={"P189":("4","3AC69369FC0CEF282705ABB2FAFADB1F106FB013E4640DEB0DCEF3E61FA96385"),
          "P190":("10","2F7E349C24BD1BFE56F5BFFCFDD20B6A8614074EC90F96B7E340059C1721D0E2"),
          "P191":("10","E7E2362A83A36D4EA436739FB76E69583DC5749F59484E7BF39668581547F02A"),
          "P192":("12","2182516ADABE47866A9D910EF5A29B1498B110ECC106286EBC3819397DD9E40B"),
          "P193":("14","A56EF655DEF38870CB84C1E54016D3E6CDD09E19666F9F8A480D41D3755F88E4"),
          "P194":("14","E9A8F19A1A06E8D65D62F94A8AD61775D46A22B1FC92138ED26A2B94FB59E463")}
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def git(*args): return previous.git(*args)
def custody():
    if (sys.platform!="win32" or os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA") or
        git("branch","--show-current").decode().strip()!=BRANCH or
        git("merge-base",P194,"HEAD").decode().strip()!=P194 or
        git("status","--porcelain=v1").strip() or
        set(git("diff","--name-only",P194,"HEAD").decode().splitlines())!=NEW):
        raise RuntimeError("P195 exact clean hosted Windows P194 descendant and three audit-only files required")
    for directory in ("tests","nayeon"):
        if git("rev-parse",P194+":"+directory)!=git("rev-parse","HEAD:"+directory):
            raise RuntimeError("P195 historical product or frozen tests changed")
    if git("show",P194+":scripts/p194_windows_prebound_source_fileid_authority.py") != (
           ROOT/"scripts/p194_windows_prebound_source_fileid_authority.py").read_bytes():
        raise RuntimeError("P195 prior original source witness changed")
    return {"P195_HEAD":git("rev-parse","HEAD").decode().strip(),
            "exact_P194_parent":P194,"three_additive_files":sorted(NEW),
            "original_product_and_tests_preserved":True}
def authenticate_archive(token):
    if len(token)<8: raise RuntimeError("missing authenticated prior ZIP access")
    data=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(data)!=ZIP_SHA: raise RuntimeError("P194 original ZIP SHA wrong")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=set(z.namelist())
        if z.testzip() is not None or len(names)!=7 or \
           "p194_prebound_source_root_FileId_HCR_ledger.json" not in names:
            raise RuntimeError("P194 ZIP seven members/CRC invalid")
        ledger=json.loads(z.read("p194_prebound_source_root_FileId_HCR_ledger.json"))
        for era,(count,digest) in EXPECTED.items():
            candidates=[n for n in names if n.endswith(".log") and
                        (n.startswith("p194_current_") if era=="P194" else "_"+era+"_" in n)]
            if len(candidates)!=1: raise RuntimeError("missing original "+era+" log")
            log=z.read(candidates[0]); text=log.decode("utf8","replace").replace("\r\n","\n")
            if sha(log)!=digest or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=[count] or \
               not re.search(r"^OK\s*$",text,re.M):
                raise RuntimeError("P194 original "+era+" source-specific log/exit mismatch")
            info=(ledger.get("current_P194_native") if era=="P194" else
                  ledger.get("original_source_era_native",{}).get(era))
            if info is None or info.get("actual_OS_exit")!=0 or info.get("raw_log_SHA256")!=digest:
                raise RuntimeError("P194 original "+era+" OS custody mismatch")
        if ledger.get("checkpoint")!="P194" or ledger.get("historical_H")!="HOLD" or \
           ledger.get("production_R")!="HOLD" or \
           ledger.get("complete_native_full_product_regressions")!="0/3" or \
           ledger.get("source_before")!=ledger.get("source_after") or \
           ledger.get("source_before",{}).get("P194_HEAD")!=P194 or \
           ledger.get("P189_original_full_historical_B_ADS_gap")!="CONFIRMED_UNPATCHED":
            raise RuntimeError("P194 H/C/R historical negative source evidence invalid")
    return {"P194_original_ZIP_SHA256":ZIP_SHA,"P194_selected_native_Windows":"64/64",
            "P194_evidence_artifact":ARTIFACT,"full_product":"0/3","release":"HOLD"}
def canonical(v): return json.dumps(v,sort_keys=True,separators=(",",":")).encode("utf8")
def snap(v): return [v[0],v[1].hex(),v[2],v[3]]
def payload(a,root,epoch=7):
    return {"format":"P195-EPHEMERAL-LAB-ONLY-v1","epoch":epoch,
            "release_commit":P194,"root_path":str(root.resolve()),
            "source":a.source_path,"source_sha":a.source_sha,
            "root":snap(a.root_snapshot),"parent":snap(a.tests_snapshot),
            "leaf_volume":a.leaf_volume,"leaf_id":a.leaf_fileid.hex()}
def signed(p,key):
    return canonical({"payload":p,
                      "signature":base64.b64encode(key.sign(canonical(p))).decode("ascii")})
def snapshot(v):
    if not isinstance(v,list) or len(v)!=4: raise win.SourceDenied("SIGNED_SNAPSHOT_INVALID")
    try: b=bytes.fromhex(v[1])
    except (TypeError,ValueError) as e: raise win.SourceDenied("SIGNED_FILEID_INVALID") from e
    if len(b)!=16: raise win.SourceDenied("SIGNED_FILEID_LENGTH_INVALID")
    return (v[0],b,v[2],v[3])
def load(record,root,public,minimum_epoch):
    if public is None or type(minimum_epoch) is not int or minimum_epoch<1:
        raise win.SourceDenied("MISSING_INDEPENDENT_KEY_OR_EPOCH_FLOOR")
    try:
        raw=record.read_bytes()
        if len(raw)>16384: raise ValueError("oversize")
        o=json.loads(raw); p=o["payload"]
        public.verify(base64.b64decode(o["signature"],validate=True),canonical(p))
    except (OSError,KeyError,ValueError,TypeError,InvalidSignature) as e:
        raise win.SourceDenied("SIGNATURE_OR_RECORD_UNVERIFIABLE") from e
    if (p.get("format")!="P195-EPHEMERAL-LAB-ONLY-v1" or
        p.get("root_path")!=str(root.resolve()) or p.get("release_commit")!=P194 or
        p.get("source")!=B.SELF or p.get("source_sha")!=B.CANDIDATE_SHA256[B.SELF] or
        type(p.get("epoch")) is not int or p["epoch"]<minimum_epoch):
        raise win.SourceDenied("SIGNED_CLAIM_INVALID_OR_ROLLBACK")
    try:
        leaf=bytes.fromhex(p["leaf_id"])
        if len(leaf)!=16: raise ValueError("wrong leaf")
        anchor=previous.SyntheticPreboundFileIds(snapshot(p["root"]),snapshot(p["parent"]),
                                                  p["leaf_volume"],leaf,p["source"],p["source_sha"])
    except (KeyError,ValueError,TypeError) as e:
        raise win.SourceDenied("SIGNED_PHYSICAL_FILEID_INVALID") from e
    return previous.PreboundWin32SourceReader(root,anchor)
class P195NativeWindowsReview(previous.P194PreboundTrueWindowsSecurityCases):
    """Inherits 14 P194 fixture cases unchanged; adds 8 independent review cases."""
    def setUp(self):
        super().setUp()
        self.signer=Ed25519PrivateKey.generate() # no real signing credential
        self.public=self.signer.public_key()     # trusted input ONLY in fixture
        self.record=self.root/"p195-authority-record.json"
        self.record.write_bytes(signed(payload(self.anchor,self.root),self.signer))
    def signed_reader(self,floor=7,public=None):
        return load(self.record,self.root,self.public if public is None else public,floor)
    def test_15_signed_record_reloaded_after_new_reader_simulated_restart(self):
        self.assertEqual(self.signed_reader().read(B.SELF),self.sealed)
        self.assertEqual(self.signed_reader().read(B.SELF),self.sealed)
        print("P195_SIGNED_SIMULATED_RESTART=ADMITTED_LAB_ONLY",flush=True)
    def test_16_substituted_authority_before_enrolment_wrong_signer_refused(self):
        self.record.write_bytes(signed(payload(self.anchor,self.root),Ed25519PrivateKey.generate()))
        with self.assertRaisesRegex(win.SourceDenied,"SIGNATURE_OR_RECORD_UNVERIFIABLE"):
            self.signed_reader()
        print("P195_UNTRUSTED_PRE_ENROLMENT_SIGNER=REFUSED",flush=True)
    def test_17_replayed_valid_old_signer_epoch_requires_external_floor(self):
        self.record.write_bytes(signed(payload(self.anchor,self.root,6),self.signer))
        with self.assertRaisesRegex(win.SourceDenied,"SIGNED_CLAIM_INVALID_OR_ROLLBACK"):
            self.signed_reader(7)
        self.assertEqual(self.signed_reader(6).read(B.SELF),self.sealed)
        print("P195_ROLLBACK=ONLY_REFUSED_WITH_TRUSTED_EXTERNAL_EPOCH",flush=True)
    def test_18_partial_and_corrupt_authority_fail_closed(self):
        self.record.with_suffix(".pending").write_bytes(b"{incomplete")
        self.assertEqual(self.signed_reader().read(B.SELF),self.sealed)
        self.record.write_bytes(b"{incomplete")
        with self.assertRaisesRegex(win.SourceDenied,"SIGNATURE_OR_RECORD_UNVERIFIABLE"):
            self.signed_reader()
    def test_19_signed_wrong_git_release_commit_denied(self):
        p=payload(self.anchor,self.root)
        p["release_commit"]=previous.P193
        self.record.write_bytes(signed(p,self.signer))
        with self.assertRaisesRegex(win.SourceDenied,"SIGNED_CLAIM_INVALID_OR_ROLLBACK"):
            self.signed_reader()
    def test_20_synthetic_independent_anchor_missing_fails_closed(self):
        with self.assertRaisesRegex(win.SourceDenied,"MISSING_INDEPENDENT_KEY_OR_EPOCH_FLOOR"):
            load(self.record,self.root,None,7)
        with self.assertRaisesRegex(win.SourceDenied,"MISSING_INDEPENDENT_KEY_OR_EPOCH_FLOOR"):
            self.signed_reader(floor=None)
    def _remove_other_process(self,path):
        code=("import os,sys,json\ntry:\n os.unlink(sys.argv[1]);"
              " print(json.dumps({'removed':True,'winerror':None}))\n"
              "except OSError as e:\n print(json.dumps({'removed':False,'winerror':getattr(e,'winerror',None)}))")
        p=subprocess.run([sys.executable,"-B","-c",code,str(path)],cwd=self.root,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
        self.assertEqual(p.returncode,0,p.stderr.decode("utf8","replace"))
        return json.loads(p.stdout)
    def test_21_ADS_add_then_remove_other_process_between_snapshots(self):
        obs=[]
        stream=str(self.source)+":p191_cross_process_stream"
        def attack(_):
            self.assertTrue(self.child("create_ads",self.source)["succeeded"])
            self.assertIn(":p191_cross_process_stream:$DATA",aliases.Win32SourceInspectionCandidate.streams(self.source))
            obs.append(self._remove_other_process(stream))
            print("P195_NATIVE_ADS_ADD=OS_ALLOWED|DELETE="+str(obs[-1]),flush=True)
        try:
            try: result=self.signed_reader().read(B.SELF,on_open=attack)
            except win.SourceDenied:
                if not obs or obs[-1]["removed"]: raise
                print("P195_ADS_REMOVE_REFUSED=ABA_UNPROVEN",flush=True)
            else:
                self.assertTrue(obs[-1]["removed"])
                self.assertEqual(result,self.sealed)
                print("P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP",flush=True)
        finally:
            if ":p191_cross_process_stream:$DATA" in aliases.Win32SourceInspectionCandidate.streams(self.source):
                os.unlink(stream)
    def test_22_hardlink_add_then_remove_other_process_between_snapshots(self):
        obs=[]
        link=self.root/"p195-linked-synthetic-leaf"
        def attack(_):
            self.assertTrue(self.child("create_hardlink",self.source,link)["succeeded"])
            self.assertTrue(link.exists())
            obs.append(self._remove_other_process(link))
            print("P195_NATIVE_HARDLINK_ADD=OS_ALLOWED|DELETE="+str(obs[-1]),flush=True)
        try:
            try: result=self.signed_reader().read(B.SELF,on_open=attack)
            except win.SourceDenied:
                if not obs or obs[-1]["removed"]: raise
                print("P195_LINK_REMOVE_REFUSED=ABA_UNPROVEN",flush=True)
            else:
                self.assertTrue(obs[-1]["removed"])
                self.assertEqual(result,self.sealed)
                print("P195_HARDLINK_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP",flush=True)
        finally:
            link.unlink(missing_ok=True)

def main():
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p195-native-review"
    out.mkdir(parents=True,exist_ok=True)
    result={"checkpoint":"P195","historical_H":"HOLD","current_C":"ISOLATED_SYNTHETIC_SIGNED_AUTHORITY_ABA_REVIEW",
            "production_R":"HOLD","full_product_native_Windows_regressions":"0/3",
            "external_reviews":previous.REVIEWS,"privileged_G0_G6":"OPEN",
            "original_historical_B_ADS_gap":"CONFIRMED_UNPATCHED",
            "independent_pre_enrolment_and_durable_rollback_authority":"NOT_ESTABLISHED",
            "ADS_hardlink_ABA_atomic_exclusion":"NOT_ESTABLISHED",
            "Git_index_tree_HEAD_current_Phase10_integrated":"NO"}
    done=False
    try:
        before=custody();result["source_before"]=before
        result["original_P194"]=authenticate_archive(os.environ.get("P195_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if k in ("GH_TOKEN","GITHUB_TOKEN","P195_ARCHIVE_TOKEN") or k.endswith(("_SECRET","_API_KEY")):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p195_native_Windows_22_security_cases.log"
        with log.open("wb") as f:
            proc=subprocess.run([sys.executable,"-B","-m","unittest","-v",
               "scripts.p195_windows_durable_root_authority_aba_review.P195NativeWindowsReview"],
               cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
               timeout=180,check=False)
        raw=log.read_bytes(); txt=raw.decode("utf8","replace").replace("\r\n","\n")
        result["current_native"]={"OS_exit":proc.returncode,"raw_log":log.name,
          "raw_log_SHA256":sha(raw),"expected_cases":22,
          "footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
          "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),
          "ABA_physical_OS_events":re.findall(r"P195_[^\r\n]+",txt)}
        if proc.returncode or result["current_native"]["footer"]!=["22"] or not result["current_native"]["complete_OK"]:
            raise RuntimeError("P195 native Windows selected security suite failed")
        for mark in ("P195_NATIVE_ADS_ADD=OS_ALLOWED","P195_NATIVE_HARDLINK_ADD=OS_ALLOWED",
                     "P195_ROLLBACK=ONLY_REFUSED_WITH_TRUSTED_EXTERNAL_EPOCH"):
            if not any(mark in e for e in result["current_native"]["ABA_physical_OS_events"]):
                raise RuntimeError("P195 required genuine Windows outcome missing: "+mark)
        after=custody(); result["source_after"]=after
        if before!=after: raise RuntimeError("P195 source custody drift")
        done=True
        print("P195_AUTHENTIC_ORIGINAL_P194=64/64_PREVIOUS_SELECTED_WINDOWS_ONLY",flush=True)
        print("P195_CURRENT_NATIVE_WINDOWS=22/22_SELECTED_TESTS_ONLY",flush=True)
        print("P195_TRUST_ROOT_ABA_ROLLBACK_PHASE10_EXTERNAL_REVIEWS=OPEN|RELEASE=HOLD",flush=True)
    except BaseException as exc:
        result["collector_error"]=repr(exc)
        print("P195_NATIVE_SECURITY_REVIEW=HOLD|"+repr(exc),flush=True)
    finally:
        result["experimental_checkpoint_complete_NOT_product_release"]=done
        (out/"p195_source_authority_ABA_HCR_ledger.json").write_text(
            json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if done else 1
if __name__=="__main__": raise SystemExit(main())
