"""P198: genuine Windows source admission -> external consumer byte custody review.

Non-privileged static Python hash-only consumer, disposable synthetic source.
Never exec/eval/unpickle/source-import the validated bytes. A digest printed by a
test child is neither signed executor identity nor production admission.
"""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, sys, zipfile
from pathlib import Path
from scripts import p197_windows_volume_journal_continuity_review as previous
from scripts import p194_windows_prebound_source_fileid_authority as p194
from scripts import p190_windows_handle_bound_source_probe as win
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B
import unittest

ROOT=Path(__file__).resolve().parents[1]
P197="d881936573813d8cd76107cbe67e1297b983d5bf"
BRANCH="byok-c1-p198-source-byte-handoff-toctou-20261114"
NEW={
    "scripts/p198_windows_source_byte_handoff_toctou_review.py",
    "docs/byok-c1-p198-source-byte-handoff-toctou-security-review.md",
    ".github/workflows/p198-windows-source-byte-handoff.yml",
}
ARTIFACT=14071452154
ZIP_SHA="91A22E87BBBAB407EC1EDD83AE59AD923F6D33A0D70026A31AA63FB1B7FE3CE0"
LOG_NAME="p197_original_and_volume_native_Windows_40.log"
LOG_SHA="92B884C4E0178A0E369DAD3E6F8971E9BE4824B021EFD5AA5290797400985787"
LEDGER_NAME="p197_volume_journal_source_HCR_ledger.json"
LEDGER_SHA="D9F75760A140DA961CA624BC9638B509DDE496DB51ABB552DBC4454B834A8D13"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*args:str)->bytes:return p194.git(*args)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    prior=git("merge-base",P197,"HEAD").decode().strip()
    changed=set(git("diff","--name-only",P197,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or
        git("branch","--show-current").decode().strip()!=BRANCH or
        prior!=P197 or changed!=NEW or dirty):
        raise RuntimeError("P198 genuine hosted Windows source custody denied: "+
            json.dumps({"head":head,"ancestor":prior,"files":sorted(changed),
                        "dirty":dirty[:500]}))
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P197+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P198 prior product or immutable tests modified")
    for path in ("scripts/p195_windows_durable_root_authority_aba_review.py",
                 "scripts/p196_windows_usn_aba_source_witness.py",
                 "scripts/p197_windows_volume_journal_continuity_review.py"):
        if git("show",P197+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P198 prior Windows security witness changed: "+path)
    return {"P198_HEAD":head,"exact_P197_parent":P197,
            "three_new_audit_paths":sorted(NEW),
            "prior_original_negative_assertions_product_tests_preserved":True}

def authenticate_original_p197(token:str)->dict:
    if len(token)<8:raise RuntimeError("P198 predecessor Windows artifact token missing")
    data=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(data)!=ZIP_SHA:raise RuntimeError("P198 predecessor original P197 ZIP SHA invalid")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P198 original P197 ZIP inventory/CRC mismatch")
        raw=z.read(LOG_NAME);record=z.read(LEDGER_NAME)
        if sha(raw)!=LOG_SHA or sha(record)!=LEDGER_SHA:
            raise RuntimeError("P198 P197 authenticated raw member digests changed")
        txt=raw.decode("utf8","replace").replace("\r\n","\n")
        for marker in ("P197_REAL_ADS_ABA=USN_FILE_DENIAL_PRESERVED",
                       "P197_REAL_HARDLINK_ABA=USN_FILE_DENIAL_PRESERVED",
                       "P197_SYNTHETIC_JOURNAL_RESET_ID_CHANGE=FAIL_CLOSED",
                       "P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP",
                       "P195_HARDLINK_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP"):
            if marker not in txt:
                raise RuntimeError("P198 historical Windows evidence marker missing: "+marker)
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["40"] or
            not re.search(r"^OK\s*$",txt,re.M)):
            raise RuntimeError("P198 original P197 native footer invalid")
        led=json.loads(record);n=led.get("current_P197_native",{})
        if (led.get("checkpoint")!="P197" or led.get("historical_H")!="HOLD" or
            led.get("production_R")!="HOLD" or
            led.get("unfiltered_full_product_native_Windows_regressions")!="0/3" or
            led.get("source_before")!=led.get("source_after") or
            led.get("source_before",{}).get("P197_HEAD")!=P197 or
            n.get("actual_OS_exit")!=0 or n.get("raw_log_SHA256")!=LOG_SHA or
            n.get("test_footer")!=["40"] or not n.get("complete_OK") or
            led.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P198 predecessor P197 source and H/C/R unverified")
    return {"authenticated_original_P197_artifact":ARTIFACT,
            "ZIP_SHA256":ZIP_SHA,"selected_predecessor_Windows_cases":"40/40",
            "original_admission_vs_USN_refusal":"PRESERVED",
            "full_product_regressions":"0/3","production":"HOLD"}

# Executed in a separate low-privilege standard Python process. It hashes bytes,
# never interprets the bytes as Python code or runs executable source.
CHILD_HASH_ONLY=r"""
import hashlib, json, re, sys
mode=sys.argv[1]
expect=sys.argv[2] if len(sys.argv)>2 else ""
limit=1048576
try:
    if mode=="stdin":
        data=sys.stdin.buffer.read(limit+1)
    elif mode=="path":
        with open(sys.argv[3],"rb") as f: data=f.read(limit+1)
    else:
        print(json.dumps({"status":"INVALID_CONSUMER_MODE","source":mode}))
        sys.exit(8)
    actual=hashlib.sha256(data).hexdigest()
    if len(data)>limit:
        status="TOO_LARGE"
    elif not re.fullmatch(r"[0-9a-f]{64}",expect):
        status="MISSING_OR_MALFORMED_EXPECTED_DIGEST"
    elif actual!=expect:
        status="SOURCE_DIGEST_MISMATCH"
    else:
        status="MATCHES_CALLER_SUPPLIED_SHA_ONLY"
    print(json.dumps({"status":status,"source":mode,"sha256":actual,
                      "byte_count":len(data)}))
    sys.exit(0 if status=="MATCHES_CALLER_SUPPLIED_SHA_ONLY" else 8)
except Exception as e:
    print(json.dumps({"status":"CHILD_IO_EXCEPTION","class":type(e).__name__}))
    sys.exit(9)
"""

CHILD_SWAP_ONLY=r"""
import os, pathlib, sys, json
source=pathlib.Path(sys.argv[1])
replacement=source.parent/"p198-disposable-post-validation-source"
replacement.write_bytes(b"P198-POST-VALIDATION-UNTRUSTED-SOURCE-NOT-ORIGINAL")
os.replace(replacement,source)
print(json.dumps({"status":"EXTERNAL_PROCESS_SWAPPED_DISPOSABLE_SOURCE",
                  "bytes":source.stat().st_size}))
"""

class P198NativeByteCustodyReview(previous.P197NativeContinuityReview):
    """Preserves 40 source-bound previous tests, adds 10 true Windows process tests."""

    @staticmethod
    def _child_env():
        env=os.environ.copy()
        for key in list(env):
            if (key in ("GH_TOKEN","GITHUB_TOKEN","P198_ARCHIVE_TOKEN") or
                key.endswith(("_API_KEY","_SECRET"))):
                env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        return env

    def _consume(self,mode:str,expected:str,data:bytes|None=None,path:Path|None=None):
        if mode not in ("stdin","path"):raise AssertionError("invalid lab mode")
        if mode=="path":
            if path is None or not path.is_relative_to(self.root):
                raise AssertionError("P198 lab path must be disposable source fixture")
        args=[sys.executable,"-I","-B","-c",CHILD_HASH_ONLY,mode,expected]
        if mode=="path":args.append(str(path))
        p=subprocess.run(args,input=data if mode=="stdin" else None,
            stdin=None if mode=="stdin" else subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=self.root,
            env=self._child_env(),timeout=15,check=False)
        if p.returncode not in (0,8):
            self.fail("P198 static child unexpectedly failed with exit "+
                str(p.returncode)+": "+p.stderr.decode("utf8","replace")[-700:])
        try: result=json.loads(p.stdout.decode("utf8","strict"))
        except (ValueError,UnicodeError) as e:
            self.fail("P198 child returned non-JSON status: "+repr(e))
        self.assertEqual(result.get("source"),mode)
        self.assertIn(result.get("status"),(
            "MATCHES_CALLER_SUPPLIED_SHA_ONLY","SOURCE_DIGEST_MISMATCH",
            "MISSING_OR_MALFORMED_EXPECTED_DIGEST","TOO_LARGE"))
        self.assertEqual(p.returncode==0,result["status"]=="MATCHES_CALLER_SUPPLIED_SHA_ONLY")
        return result,p.returncode

    def _external_replace(self):
        # Only the per-test disposable source root, never any repository path.
        self.assertTrue(self.source.is_relative_to(self.root))
        p=subprocess.run([sys.executable,"-I","-B","-c",CHILD_SWAP_ONLY,str(self.source)],
            cwd=self.root,env=self._child_env(),stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
        self.assertEqual(p.returncode,0,p.stderr.decode("utf8","replace")[-700:])
        result=json.loads(p.stdout.decode("utf8","strict"))
        self.assertEqual(result["status"],"EXTERNAL_PROCESS_SWAPPED_DISPOSABLE_SOURCE")
        self.assertNotEqual(self.source.read_bytes(),self.sealed)
        print("P198_EXTERNAL_PROCESS_POST_VALIDATION_OS_REPLACE=ALLOWED",flush=True)

    @staticmethod
    def _digest(data):return hashlib.sha256(data).hexdigest()

    def test_41_validated_original_bytes_to_new_process_by_stdin(self):
        approved=self.new_reader().read(B.SELF)
        self.assertEqual(approved,self.sealed)
        r,code=self._consume("stdin",self._digest(self.sealed),data=approved)
        self.assertEqual(code,0)
        self.assertEqual(r["sha256"],self._digest(self.sealed))
        self.assertEqual(r["byte_count"],len(self.sealed))
        print("P198_GENUINE_WINDOWS_PROCESS_STDIN_VALIDATED_SOURCE=SHA_MATCH",flush=True)

    def test_42_later_path_reopen_after_external_replace_sees_different_bytes(self):
        approved=self.new_reader().read(B.SELF)
        self.assertEqual(approved,self.sealed)
        self._external_replace()
        untrusted,code=self._consume("path",self._digest(approved),path=self.source)
        self.assertEqual(code,8)
        self.assertEqual(untrusted["status"],"SOURCE_DIGEST_MISMATCH")
        self.assertNotEqual(untrusted["sha256"],self._digest(approved))
        print("P198_POST_VALIDATION_PATH_REOPEN_TRUSTED_DIGEST=REFUSED",flush=True)

    def test_43_prevalidated_bytes_survive_external_path_replacement(self):
        approved=self.new_reader().read(B.SELF)
        self._external_replace()
        r,code=self._consume("stdin",self._digest(self.sealed),data=approved)
        self.assertEqual(code,0)
        self.assertEqual(r["sha256"],self._digest(self.sealed))
        print("P198_PREVALIDATED_STDIN_AFTER_DISPOSABLE_PATH_SWAP=UNCHANGED_BYTES",flush=True)

    def test_44_caller_replaces_expected_digest_and_path_consumer_accepts(self):
        approved=self.new_reader().read(B.SELF)
        self._external_replace()
        untrusted=self.source.read_bytes()
        self.assertNotEqual(untrusted,approved)
        r,code=self._consume("path",self._digest(untrusted),path=self.source)
        self.assertEqual(code,0)
        self.assertEqual(r["sha256"],self._digest(untrusted))
        print("P198_CALLER_SUPPLIED_HASH_WITH_SWAPPED_SOURCE=UNSAFE_ACCEPTANCE",flush=True)

    def test_45_single_byte_tamper_during_stdin_transfer_refused(self):
        approved=self.new_reader().read(B.SELF)
        altered=approved[:-1]+bytes([approved[-1]^1])
        r,code=self._consume("stdin",self._digest(approved),data=altered)
        self.assertEqual(code,8)
        self.assertEqual(r["status"],"SOURCE_DIGEST_MISMATCH")
        print("P198_STDIN_BYTE_TAMPER=REFUSED",flush=True)

    def test_46_truncated_stdin_transfer_refused(self):
        approved=self.new_reader().read(B.SELF)
        self.assertGreater(len(approved),2)
        r,code=self._consume("stdin",self._digest(approved),data=approved[:-2])
        self.assertEqual(code,8)
        self.assertEqual(r["status"],"SOURCE_DIGEST_MISMATCH")
        print("P198_STDIN_TRUNCATION=REFUSED",flush=True)

    def test_47_missing_trusted_expected_digest_refused(self):
        approved=self.new_reader().read(B.SELF)
        for expected in ("","deadbeef","Z"*64):
            r,code=self._consume("stdin",expected,data=approved)
            self.assertEqual(code,8)
            self.assertEqual(r["status"],"MISSING_OR_MALFORMED_EXPECTED_DIGEST")
        print("P198_MISSING_EXPECTED_TRUSTED_SHA=REFUSED",flush=True)

    def test_48_oversized_untrusted_stream_refused_even_if_digest_matches(self):
        data=b"X"*(1048576+1)
        r,code=self._consume("stdin",self._digest(data),data=data)
        self.assertEqual(code,8)
        self.assertEqual(r["status"],"TOO_LARGE")
        print("P198_UNBOUNDED_STREAM=REFUSED",flush=True)

    def test_49_two_separate_processes_receive_same_authenticated_bytes(self):
        approved=self.new_reader().read(B.SELF)
        a,acode=self._consume("stdin",self._digest(self.sealed),data=approved)
        b,bcode=self._consume("stdin",self._digest(self.sealed),data=approved)
        self.assertEqual((acode,bcode),(0,0))
        self.assertEqual((a["sha256"],a["byte_count"]),(b["sha256"],b["byte_count"]))
        print("P198_TWO_SEPARATE_CONSUMERS_SAME_STDIN_SOURCE=OBSERVED_ONLY",flush=True)

    def test_50_new_source_admission_after_external_replace_refuses_FileId(self):
        approved=self.new_reader().read(B.SELF)
        self.assertEqual(approved,self.sealed)
        self._external_replace()
        with self.assertRaisesRegex(win.SourceDenied,
                "PINNED_SOURCE_LEAF_FILEID_MISMATCH"):
            self.new_reader().read(B.SELF)
        print("P198_POST_REPLACE_REVALIDATION_ORIGINAL_FILEID=REFUSED",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p198-handoff-review"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P198","historical_H":"HOLD",
            "current_C":"ISOLATED_VALIDATED_BYTE_HANDOFF_VS_UNSAFE_PATH_REOPEN",
            "production_R":"HOLD","full_unfiltered_native_Windows_product_regressions":"0/3",
            "qualified_external_reviews":p194.REVIEWS,
            "privileged_G0_G6":"OPEN",
            "original_historical_full_BYOK_B_ADS_gap":"UNPATCHED",
            "P195_original_ADS_hardlink_ABA_unprotected":"AUTHENTICATED_PREVIOUS",
            "P196_P197_file_USN_journal_gaps":"EXPERIMENTAL_ONLY",
            "genuine_trusted_loader_or_execution_attestation":"NOT_IMPLEMENTED",
            "safe_cross_process_handle_transfer_or_signed_binary_loader":"NOT_IMPLEMENTED",
            "independent_pre_enrolment_durable_epoch":"NOT_ESTABLISHED",
            "production_current_Phase10_source_to_execution_gate":"NOT_INTEGRATED",
            "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["original_authenticated_P197"]=authenticate_original_p197(
            os.environ.get("P198_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if (k in ("GITHUB_TOKEN","GH_TOKEN","P198_ARCHIVE_TOKEN") or
                k.endswith(("_SECRET","_API_KEY"))):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p198_native_Windows_admission_consumer_50.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                   "scripts.p198_windows_source_byte_handoff_toctou_review.P198NativeByteCustodyReview"],
                   cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                   timeout=260,check=False)
        raw=log.read_bytes();txt=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"^P198_[^\r\n]+",txt,re.M)
        ledger["current_P198_native"]={
            "raw_log":log.name,"raw_log_SHA256":sha(raw),"actual_OS_exit":p.returncode,
            "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",txt,re.M)),"events":events,
            "original_negative_test_failures_in_log":re.findall(r"^(?:FAIL|ERROR): .+$",txt,re.M)}
        if (p.returncode!=0 or ledger["current_P198_native"]["test_footer"]!=["50"] or
            not ledger["current_P198_native"]["complete_OK"]):
            raise RuntimeError("P198 genuine Windows selected 50 tests failed; retain raw log and HOLD")
        for marker in ("P198_GENUINE_WINDOWS_PROCESS_STDIN_VALIDATED_SOURCE=SHA_MATCH",
                       "P198_POST_VALIDATION_PATH_REOPEN_TRUSTED_DIGEST=REFUSED",
                       "P198_PREVALIDATED_STDIN_AFTER_DISPOSABLE_PATH_SWAP=UNCHANGED_BYTES",
                       "P198_CALLER_SUPPLIED_HASH_WITH_SWAPPED_SOURCE=UNSAFE_ACCEPTANCE",
                       "P198_STDIN_BYTE_TAMPER=REFUSED",
                       "P198_STDIN_TRUNCATION=REFUSED",
                       "P198_POST_REPLACE_REVALIDATION_ORIGINAL_FILEID=REFUSED"):
            if marker not in events:
                raise RuntimeError("P198 required physical Windows witness absent: "+marker)
        after=custody();ledger["source_after"]=after
        if before!=after:raise RuntimeError("P198 genuine source changed across test")
        complete=True
        print("P198_ORIGINAL_P197_ZIP_AND_SELECTED_40_WINDOWS=AUTHENTICATED",flush=True)
        print("P198_GENUINE_WINDOWS_SELECTED_SOURCE_AND_CONSUMER=50/50_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P198_POST_READ_REOPEN_ATTACK=DEMONSTRATED|STILL_NOT_TRUSTED_EXECUTION",flush=True)
        print("P198_FULL_PRODUCT_NATIVE_WINDOWS=0/3|EXTERNAL_REVIEWS_OPEN|RELEASE_HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P198_HANDOFF_SOURCE_REVIEW=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p198_source_consumer_HCR_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1

if __name__=="__main__":raise SystemExit(main())
