"""P199: nonprivileged synthetic consumer identity and nonce-bound byte handoff review.

LAB ONLY: ephemeral signature on a fixture manifest, observed Windows child PID
and executable path, actual hash-only stdin consumer. NOT Authenticode trust,
trusted code execution, authenticated IPC or a product admission patch.
"""
from __future__ import annotations
import base64, ctypes, hashlib, io, json, os, re, secrets, subprocess, sys, zipfile
from ctypes import wintypes
from pathlib import Path
import unittest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts import p198_windows_source_byte_handoff_toctou_review as previous
from scripts import p194_windows_prebound_source_fileid_authority as p194
from scripts import p190_windows_handle_bound_source_probe as win
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P198="9b80021a5a3a5b49c54dcc150d0a5f7f0fff4a83"
BRANCH="byok-c1-p199-consumer-provenance-challenge-handoff-20261114"
NEW={"scripts/p199_windows_consumer_identity_handoff_review.py",
     "docs/byok-c1-p199-consumer-identity-signed-loader-security-review.md",
     ".github/workflows/p199-windows-consumer-provenance.yml"}
ARTIFACT=14103539000
ZIP_SHA="E11281D520BB5D161A69589152BDAC523BDDEE27DA13BF1D4DDC9E3C39D59696"
LOG_NAME="p198_native_Windows_admission_consumer_50.log"
LOG_SHA="B76CE4269ED0CCDCAE166920DB051D96F2F8461F2453DCB059CD84DD811A98EE"
LEDGER_NAME="p198_source_consumer_HCR_ledger.json"
LEDGER_SHA="4B3A6375210430969C3222D5CB1565D24E5142CBBEFAC06375504BAB1502FE0D"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest().upper()
def git(*a:str)->bytes:return p194.git(*a)
def canonical(obj)->bytes:return json.dumps(obj,sort_keys=True,separators=(",",":")).encode("utf8")

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    ancestor=git("merge-base",P198,"HEAD").decode().strip()
    changed=set(git("diff","--name-only",P198,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or git("branch","--show-current").decode().strip()!=BRANCH or
        ancestor!=P198 or changed!=NEW or dirty):
        raise RuntimeError("P199 original Git Windows source custody mismatch: "+
            json.dumps({"head":head,"ancestor":ancestor,"changed":sorted(changed),"dirty":dirty[:300]}))
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P198+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P199 original protected product/security tests changed")
    for path in ("scripts/p195_windows_durable_root_authority_aba_review.py",
                 "scripts/p196_windows_usn_aba_source_witness.py",
                 "scripts/p197_windows_volume_journal_continuity_review.py",
                 "scripts/p198_windows_source_byte_handoff_toctou_review.py"):
        if git("show",P198+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P199 original negative Windows witness rewritten "+path)
    return {"P199_HEAD":head,"exact_P198_parent":P198,
            "three_new_audit_only_paths":sorted(NEW),
            "original_product_frozen_tests_all_prior_negative_witnesses_preserved":True}

def authenticate_original_p198(token:str)->dict:
    if len(token)<8:raise RuntimeError("P199 predecessor authentic ZIP access unavailable")
    data=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(data)!=ZIP_SHA:raise RuntimeError("P199 original P198 ZIP SHA invalid")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P199 original P198 ZIP CRC/member inventory invalid")
        log=z.read(LOG_NAME);rawledger=z.read(LEDGER_NAME)
        if sha(log)!=LOG_SHA or sha(rawledger)!=LEDGER_SHA:
            raise RuntimeError("P199 source-authentic P198 member SHA invalid")
        txt=log.decode("utf8","replace").replace("\r\n","\n")
        for marker in ("P198_CALLER_SUPPLIED_HASH_WITH_SWAPPED_SOURCE=UNSAFE_ACCEPTANCE",
                       "P198_POST_VALIDATION_PATH_REOPEN_TRUSTED_DIGEST=REFUSED",
                       "P198_PREVALIDATED_STDIN_AFTER_DISPOSABLE_PATH_SWAP=UNCHANGED_BYTES",
                       "P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP"):
            if marker not in txt:
                raise RuntimeError("P199 original P198 negative security witness absent: "+marker)
        if re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",txt,re.M)!=["50"] or \
           not re.search(r"^OK\s*$",txt,re.M):
            raise RuntimeError("P199 original P198 full source-specific 50 test footer absent")
        record=json.loads(rawledger);p=record.get("current_P198_native",{})
        if (record.get("checkpoint")!="P198" or record.get("historical_H")!="HOLD" or
            record.get("production_R")!="HOLD" or
            record.get("full_unfiltered_native_Windows_product_regressions")!="0/3" or
            record.get("source_before")!=record.get("source_after") or
            record.get("source_before",{}).get("P198_HEAD")!=P198 or
            p.get("actual_OS_exit")!=0 or p.get("raw_log_SHA256")!=LOG_SHA or
            p.get("test_footer")!=["50"] or not p.get("complete_OK") or
            record.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P199 predecessor original H/C/R or exact native source invalid")
    return {"P198_original_artifact":ARTIFACT,"original_ZIP_SHA256":ZIP_SHA,
            "original_50_selected_Windows_cases":"50/50",
            "prior_unsafe_path_substitution":"AUTHENTICATED_NEGATIVE",
            "full_product":"0/3","production":"HOLD"}

# The child is constant and never loads or runs admitted bytes as code.
# Protocol is deliberately limited to one JSON frame and one JSON acknowledgement.
CHILD_HASH_ONLY=r"""
import base64, hashlib, json, os, sys
MAX_DATA=1048576
def reply(status,nonce="",actual="",size=0):
    print(json.dumps({"protocol":"P199-LAB-HASH-ONLY","status":status,
      "nonce":nonce,"digest":actual,"size":size,"pid":os.getpid(),
      "ppid":os.getppid()},sort_keys=True),flush=True)
try:
    line=sys.stdin.buffer.readline(1450000)
    if not line.endswith(b"\n") or len(line)>1450000:
        reply("BAD_FRAME");sys.exit(9)
    o=json.loads(line.decode("utf8","strict"))
    if not isinstance(o,dict) or set(o)!={"nonce","payload"}:
        reply("BAD_FRAME");sys.exit(9)
    nonce=o["nonce"]
    if not isinstance(nonce,str) or len(nonce)!=32 or any(c not in "0123456789abcdef" for c in nonce):
        reply("BAD_NONCE");sys.exit(9)
    data=base64.b64decode(o["payload"],validate=True)
    if len(data)>MAX_DATA:
        reply("OVERSIZE",nonce,size=len(data));sys.exit(9)
    reply("OBSERVED_UNTRUSTED_HASH",nonce,hashlib.sha256(data).hexdigest().upper(),len(data))
except Exception:
    reply("MALFORMED_FRAME")
    sys.exit(9)
"""

# Intentional adversarial fixture: a different -c script in the SAME python.exe
# makes a credible PID/parent/nonce/hash response without reading payload.
CHILD_SPOOF=r"""
import json,os,sys
o=json.loads(sys.stdin.buffer.readline().decode("utf8"))
print(json.dumps({"protocol":"P199-LAB-HASH-ONLY","status":"OBSERVED_UNTRUSTED_HASH",
 "nonce":o["nonce"],"digest":o["asserted_digest"],"size":o["asserted_size"],
 "pid":os.getpid(),"ppid":os.getppid()},sort_keys=True),flush=True)
"""

def fixture_manifest(interpreter:Path,code:str,approved:bytes)->dict:
    return {"format":"P199-EPHEMERAL-LAB-ONLY-v1","parent_commit":P198,
      "epoch":7,"audience":"P199-NONPRIVILEGED-HASH-ONLY",
      "script_sha256":sha(code.encode("utf8")),
      "interpreter_sha256":sha(interpreter.read_bytes()),
      "interpreter_path":os.path.normcase(os.path.abspath(interpreter)),
      "approved_source_sha256":sha(approved)}

def signed_record(payload:dict,signer:Ed25519PrivateKey)->bytes:
    return canonical({"payload":payload,
      "signature":base64.b64encode(signer.sign(canonical(payload))).decode("ascii")})

def verify_record(blob:bytes,public,interpreter:Path,expected_code:str,approved:bytes,floor:int=7):
    if public is None or floor is None:
        raise win.SourceDenied("NO_INDEPENDENT_TRUSTED_SIGNER_OR_EPOCH")
    try:
        outer=json.loads(blob)
        if set(outer)!={"payload","signature"}:raise ValueError("fields")
        payload=outer["payload"]
        public.verify(base64.b64decode(outer["signature"],validate=True),canonical(payload))
    except (ValueError,TypeError,KeyError,InvalidSignature) as exc:
        raise win.SourceDenied("LAB_SIGNED_CONSUMER_MANIFEST_INVALID") from exc
    if (type(payload.get("epoch")) is not int or payload["epoch"]<floor or
        payload!=fixture_manifest(interpreter,expected_code,approved)):
        raise win.SourceDenied("LAB_CONSUMER_SOURCE_RELEASE_OR_EPOCH_MISMATCH")
    return payload

def observed_image(pid:int)->str:
    if sys.platform!="win32":raise win.SourceDenied("P199_REAL_WINDOWS_ONLY")
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.OpenProcess.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    k.CloseHandle.restype=wintypes.BOOL
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,
        wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    k.QueryFullProcessImageNameW.restype=wintypes.BOOL
    h=k.OpenProcess(0x1000,False,pid)
    if not h:raise win.SourceDenied("OBSERVED_CONSUMER_OS_PROCESS_UNAVAILABLE_"+str(ctypes.get_last_error()))
    try:
        buff=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(buff))
        if not k.QueryFullProcessImageNameW(h,0,buff,ctypes.byref(size)):
            raise win.SourceDenied("OS_CONSUMER_IMAGE_QUERY_FAILED_"+str(ctypes.get_last_error()))
        return os.path.normcase(os.path.abspath(buff.value))
    finally:k.CloseHandle(h)

def require_image(actual:str,expected:str):
    if os.path.normcase(os.path.abspath(actual))!=os.path.normcase(os.path.abspath(expected)):
        raise win.SourceDenied("OBSERVED_CONSUMER_EXECUTABLE_NOT_EXPECTED")

def authenticate_ack(ack:dict,proc_pid:int,nonce:str,approved_sha:str,approved_len:int,
                     parent_pid:int,seen:set)->dict:
    if (not isinstance(ack,dict) or ack.get("protocol")!="P199-LAB-HASH-ONLY" or
        ack.get("status")!="OBSERVED_UNTRUSTED_HASH" or
        ack.get("pid")!=proc_pid or ack.get("ppid")!=parent_pid):
        raise win.SourceDenied("CONSUMER_ACK_PID_PARENT_OR_PROTOCOL_INVALID")
    if ack.get("nonce")!=nonce or nonce in seen:
        raise win.SourceDenied("CONSUMER_NONCE_MISMATCH_OR_REPLAY")
    if ack.get("digest")!=approved_sha or ack.get("size")!=approved_len:
        raise win.SourceDenied("CONSUMER_PAYLOAD_DIGEST_OR_LENGTH_MISMATCH")
    seen.add(nonce)
    # These fields authenticate only a lab observation, not actual executed script.
    return {"observed_os_pid":proc_pid,"nonce_fresh":True,
            "source_digest_matches":True,"not_production_attestation":True}

class P199NativeConsumerProvenanceReview(previous.P198NativeByteCustodyReview):
    """Preserves 50 historical source tests, adds 10 nonprivileged Windows cases."""
    def setUp(self):
        super().setUp()
        self.lab_signer=Ed25519PrivateKey.generate()
        self.lab_public=self.lab_signer.public_key()
        self.used_sessions=set()
        self.image=Path(sys.executable)
        self.manifest=signed_record(fixture_manifest(self.image,CHILD_HASH_ONLY,self.sealed),
                                    self.lab_signer)
    def prelaunch(self,blob=None,public=None,expected_code=CHILD_HASH_ONLY,floor=7):
        return verify_record(self.manifest if blob is None else blob,
            self.lab_public if public is None else public,self.image,
            expected_code,self.sealed,floor)

    def child_env(self):
        env=self._child_env()
        env.pop("P199_ARCHIVE_TOKEN",None)
        return env

    def run_child(self,code:str,frame:dict|bytes,observed_sha:str|None=None):
        if isinstance(frame,dict):raw=canonical(frame)+b"\n"
        else:raw=frame
        p=subprocess.Popen([sys.executable,"-I","-B","-u","-c",code],
            cwd=self.root,env=self.child_env(),stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            # Real native Windows running-image observation BEFORE sending stdin.
            actual=observed_image(p.pid)
            require_image(actual,str(self.image))
            out,err=p.communicate(input=raw,timeout=15)
        except BaseException:
            p.kill();p.communicate()
            raise
        if p.returncode not in (0,9):
            self.fail("P199 lab child OS exit unexpected "+str(p.returncode)+
                      " stderr="+err.decode("utf8","replace")[-300:])
        try:ack=json.loads(out.decode("utf8","strict").strip())
        except (UnicodeError,ValueError) as exc:
            raise win.SourceDenied("CONSUMER_ACK_NOT_CANONICAL_JSON") from exc
        return ack,p.returncode,p.pid,actual

    def admitted(self,data=None,code=CHILD_HASH_ONLY,claimed=None):
        self.prelaunch()
        source=self.new_reader().read(B.SELF) if data is None else data
        nonce=secrets.token_hex(16)
        frame={"nonce":nonce,"payload":base64.b64encode(source).decode("ascii")}
        if code==CHILD_SPOOF:
            frame["asserted_digest"]=sha(self.sealed)
            frame["asserted_size"]=len(self.sealed)
        ack,rc,pid,actual=self.run_child(code,frame)
        return ack,rc,pid,actual,nonce

    def test_51_real_windows_process_image_nonce_and_original_byte_handoff(self):
        self.prelaunch()
        ack,rc,pid,image,nonce=self.admitted()
        self.assertEqual(rc,0)
        self.assertEqual(image,os.path.normcase(os.path.abspath(self.image)))
        self.assertTrue(authenticate_ack(ack,pid,nonce,sha(self.sealed),len(self.sealed),
                                         os.getpid(),self.used_sessions))
        print("P199_REAL_WINDOWS_PID_EXECUTABLE_IMAGE_NONCE_ORIGINAL_BYTES=LAB_MATCH",flush=True)

    def test_52_altered_consumer_script_sha_manifest_denied_prelaunch(self):
        with self.assertRaisesRegex(win.SourceDenied,"LAB_CONSUMER_SOURCE_RELEASE_OR_EPOCH_MISMATCH"):
            self.prelaunch(expected_code=CHILD_HASH_ONLY+" # modified")
        print("P199_TAMPERED_STATIC_CONSUMER_SOURCE_MANIFEST=REFUSED",flush=True)

    def test_53_forged_signer_identity_denied_prelaunch(self):
        fake=signed_record(fixture_manifest(self.image,CHILD_HASH_ONLY,self.sealed),
                           Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(win.SourceDenied,"LAB_SIGNED_CONSUMER_MANIFEST_INVALID"):
            self.prelaunch(blob=fake)
        print("P199_WRONG_EPHEMERAL_LAB_SIGNER=REFUSED",flush=True)

    def test_54_signed_wrong_release_and_rollback_need_trusted_external_floor(self):
        payload=fixture_manifest(self.image,CHILD_HASH_ONLY,self.sealed)
        payload["parent_commit"]="other-unsigned-release"
        with self.assertRaisesRegex(win.SourceDenied,"LAB_CONSUMER_SOURCE_RELEASE_OR_EPOCH_MISMATCH"):
            self.prelaunch(blob=signed_record(payload,self.lab_signer))
        payload=fixture_manifest(self.image,CHILD_HASH_ONLY,self.sealed)
        payload["epoch"]=6
        with self.assertRaisesRegex(win.SourceDenied,"LAB_CONSUMER_SOURCE_RELEASE_OR_EPOCH_MISMATCH"):
            self.prelaunch(blob=signed_record(payload,self.lab_signer))
        with self.assertRaisesRegex(win.SourceDenied,"NO_INDEPENDENT_TRUSTED_SIGNER_OR_EPOCH"):
            verify_record(self.manifest,None,self.image,CHILD_HASH_ONLY,self.sealed,7)
        print("P199_SYNTHETIC_RELEASE_AND_ROLLBACK_WITH_EXTERNAL_FLOOR=REFUSED",flush=True)

    def test_55_actual_windows_image_refuses_wrong_expected_executable(self):
        self.prelaunch()
        ack,rc,pid,image,nonce=self.admitted()
        self.assertEqual(rc,0)
        with self.assertRaisesRegex(win.SourceDenied,"OBSERVED_CONSUMER_EXECUTABLE_NOT_EXPECTED"):
            require_image(image,str(self.image)+".malicious")
        print("P199_OS_PROCESS_IMAGE_MISMATCH=REFUSED",flush=True)

    def test_56_forged_child_pid_or_parent_pid_refused(self):
        ack,rc,pid,image,nonce=self.admitted()
        self.assertEqual(rc,0)
        for field in ("pid","ppid"):
            forged=dict(ack);forged[field]=int(forged[field])+1
            with self.assertRaisesRegex(win.SourceDenied,"CONSUMER_ACK_PID_PARENT_OR_PROTOCOL_INVALID"):
                authenticate_ack(forged,pid,nonce,sha(self.sealed),len(self.sealed),
                                 os.getpid(),self.used_sessions)
        print("P199_FORGED_PROCESS_PID_OR_PARENT_CLAIM=REFUSED",flush=True)

    def test_57_previous_accepted_nonce_reply_cannot_be_replayed(self):
        ack,rc,pid,image,nonce=self.admitted()
        self.assertEqual(rc,0)
        authenticate_ack(ack,pid,nonce,sha(self.sealed),len(self.sealed),
                         os.getpid(),self.used_sessions)
        with self.assertRaisesRegex(win.SourceDenied,"CONSUMER_NONCE_MISMATCH_OR_REPLAY"):
            authenticate_ack(ack,pid,nonce,sha(self.sealed),len(self.sealed),
                             os.getpid(),self.used_sessions)
        print("P199_SAME_SESSION_NONCE_ACK_REPLAY=REFUSED_WITH_MEMORY_ONLY",flush=True)

    def test_58_altered_content_on_new_process_still_fails_original_digest(self):
        approved=self.new_reader().read(B.SELF)
        tampered=approved[:-1]+bytes([approved[-1]^1])
        ack,rc,pid,image,nonce=self.admitted(data=tampered)
        self.assertEqual(rc,0)
        with self.assertRaisesRegex(win.SourceDenied,"CONSUMER_PAYLOAD_DIGEST_OR_LENGTH_MISMATCH"):
            authenticate_ack(ack,pid,nonce,sha(self.sealed),len(self.sealed),
                             os.getpid(),self.used_sessions)
        print("P199_CROSS_PROCESS_TAMPERED_SOURCE_WITH_PINNED_DIGEST=REFUSED",flush=True)

    def test_59_oversize_and_malformed_json_frames_fail_closed(self):
        for frame in (b"not-json\n",
                      canonical({"nonce":"bad","payload":"@@@"})+b"\n",
                      canonical({"nonce":secrets.token_hex(16),
                                 "payload":base64.b64encode(b"X"*1048577).decode("ascii")})+b"\n"):
            ack,rc,pid,image=self.run_child(CHILD_HASH_ONLY,frame)
            self.assertEqual(rc,9)
            self.assertIn(ack["status"],("MALFORMED_FRAME","BAD_NONCE","OVERSIZE","BAD_FRAME"))
        print("P199_MALFORMED_OR_OVERSIZED_FRAMED_CONSUMER_INPUT=FAIL_CLOSED",flush=True)

    def test_60_unauthenticated_injected_code_can_spoof_PID_image_nonce_digest(self):
        self.prelaunch()
        # Deliberately launch different -c bytes after verifying intended manifest.
        # OS image is still same interpreter, all self-attested fields look right.
        ack,rc,pid,image,nonce=self.admitted(code=CHILD_SPOOF)
        self.assertEqual(rc,0)
        accepted=authenticate_ack(ack,pid,nonce,sha(self.sealed),len(self.sealed),
                                  os.getpid(),self.used_sessions)
        self.assertTrue(accepted["source_digest_matches"])
        self.assertNotEqual(sha(CHILD_SPOOF.encode("utf8")),
                            fixture_manifest(self.image,CHILD_HASH_ONLY,self.sealed)["script_sha256"])
        print("P199_UNPINNED_SCRIPT_WITH_SAME_PROCESS_IMAGE=UNSAFE_SELF_ATTESTED_ACCEPTANCE",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p199-provenance"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P199","historical_H":"HOLD",
       "current_C":"ISOLATED_EPHEMERAL_MANIFEST_AND_UNTRUSTED_CHILD_ACK_EXPERIMENT",
       "production_R":"HOLD","full_unfiltered_native_Windows_product_regressions":"0/3",
       "qualified_independent_reviews":p194.REVIEWS,"privileged_G0_G6":"OPEN",
       "original_private_full_BYOK_B_ADS_gap":"CONFIRMED_UNPATCHED",
       "P198_source_to_consumer_path_substitution":"PRESERVED_UNSAFE",
       "original_P195_file_ADS_hardlink_ABA":"PRESERVED_UNSAFE",
       "actual_Windows_Authenticode_signed_custom_loader":"NOT_IMPLEMENTED",
       "independently_trusted_signer_root_epoch":"NOT_ESTABLISHED",
       "nonce_replay_persistence":"IN_MEMORY_LAB_ONLY",
       "process_binary_script_binding":"UNPROVEN_SPOOF_ACCEPTANCE_EXPECTED",
       "authenticated_secure_IPC_or_privileged_trusted_loader":"NOT_IMPLEMENTED",
       "current_23_B_original_and_Phase10_full_gate":"NOT_INTEGRATED",
       "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        prior=custody();ledger["source_before"]=prior
        ledger["original_authenticated_P198"]=authenticate_original_p198(
              os.environ.get("P199_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for key in list(env):
            if (key in ("GITHUB_TOKEN","GH_TOKEN","P199_ARCHIVE_TOKEN") or
                key.endswith(("_SECRET","_API_KEY"))):
                env.pop(key,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p199_native_Windows_consumer_provenance_60.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                "scripts.p199_windows_consumer_identity_handoff_review.P199NativeConsumerProvenanceReview"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=260,check=False)
        raw=log.read_bytes();body=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"^P199_[^\r\n]+",body,re.M)
        ledger["current_P199_native"]={
            "raw_log":log.name,"raw_log_SHA256":sha(raw),"actual_OS_exit":p.returncode,
            "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",body,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",body,re.M)),
            "events":events}
        if (p.returncode!=0 or ledger["current_P199_native"]["test_footer"]!=["60"] or
            not ledger["current_P199_native"]["complete_OK"]):
            raise RuntimeError("P199 source-bound native Windows 60-case review failed; preserve actual log")
        for marker in ("P199_REAL_WINDOWS_PID_EXECUTABLE_IMAGE_NONCE_ORIGINAL_BYTES=LAB_MATCH",
                       "P199_WRONG_EPHEMERAL_LAB_SIGNER=REFUSED",
                       "P199_TAMPERED_STATIC_CONSUMER_SOURCE_MANIFEST=REFUSED",
                       "P199_FORGED_PROCESS_PID_OR_PARENT_CLAIM=REFUSED",
                       "P199_SAME_SESSION_NONCE_ACK_REPLAY=REFUSED_WITH_MEMORY_ONLY",
                       "P199_CROSS_PROCESS_TAMPERED_SOURCE_WITH_PINNED_DIGEST=REFUSED",
                       "P199_UNPINNED_SCRIPT_WITH_SAME_PROCESS_IMAGE=UNSAFE_SELF_ATTESTED_ACCEPTANCE"):
            if marker not in events:
                raise RuntimeError("P199 required honest source-bound Windows marker absent: "+marker)
        after=custody();ledger["source_after"]=after
        if prior!=after:raise RuntimeError("P199 original frozen Git changed mid-run")
        complete=True
        print("P199_AUTHENTIC_ORIGINAL_P198_ZIP_AND_50_NATIVE_WINDOWS=VERIFIED",flush=True)
        print("P199_SELECTED_REAL_WINDOWS_PROCESS_AND_EPHEMERAL_SIGNATURE=60/60_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P199_SAME_SIGNED_INTERPRETER_DIFFERENT_INLINE_CODE=SPOOFED_NOT_PRODUCTION_TRUST",flush=True)
        print("P199_FULL_PRODUCT_NATIVE_WINDOWS=0/3|QUALIFIED_REVIEWS_OPEN|RELEASE_HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P199_CONSUMER_PROVENANCE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p199_process_provenance_HCR_ledger.json").write_text(
            json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1
if __name__=="__main__":raise SystemExit(main())
