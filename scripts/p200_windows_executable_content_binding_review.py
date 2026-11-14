"""P200: executable script CONTENT binding vs signed interpreter path identity.

ISOLATED WINDOWS LAB ONLY. All executable script fixtures below are static,
harmless, self-owned scripts in disposable hosted Windows C: test directories.
No real product, credentials, production loader, signer, or policy changed.
"""
from __future__ import annotations
import base64, hashlib, io, json, os, re, subprocess, sys, zipfile
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts import p199_windows_consumer_identity_handoff_review as previous
from scripts import p194_windows_prebound_source_fileid_authority as p194
from scripts import p190_windows_handle_bound_source_probe as win
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact
from tests import phase8_byok_b_scope_migration as B

ROOT=Path(__file__).resolve().parents[1]
P199="c42ecd83b5277acf5cd42b22fa140600665b0943"
BRANCH="byok-c1-p200-executable-content-binding-loader-20261114"
NEW={"scripts/p200_windows_executable_content_binding_review.py",
     "docs/byok-c1-p200-executable-content-binding-loader-security-review.md",
     ".github/workflows/p200-windows-executable-content-binding.yml"}
ARTIFACT=14104875946
ZIP_SHA="AD3A76B216956A8FE7D17C82C608FACE0AC7798FA4A2145FC463BF62B7859A1F"
LOG_NAME="p199_native_Windows_consumer_provenance_60.log"
LOG_SHA="C8F558B663E437E85D5FC552242B8E35C8DD66C24E80644F54F4819B6ACBF4FD"
LEDGER_NAME="p199_process_provenance_HCR_ledger.json"
LEDGER_SHA="DFE38D4138074ED41637B8BA67B90BB42148A20761B79BD1E99A8A08BC003691"

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest().upper()
def git(*args:str)->bytes:return p194.git(*args)
def canonical(o)->bytes:return previous.canonical(o)

def custody()->dict:
    head=git("rev-parse","HEAD").decode().strip()
    ancestor=git("merge-base",P199,"HEAD").decode().strip()
    changed=set(git("diff","--name-only",P199,"HEAD").decode().splitlines())
    dirty=git("status","--porcelain=v1").decode().strip()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true" or
        os.environ.get("RUNNER_OS")!="Windows" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV" or
        os.environ.get("GITHUB_REF_NAME")!=BRANCH or
        os.environ.get("GITHUB_SHA")!=head or
        git("branch","--show-current").decode().strip()!=BRANCH or
        ancestor!=P199 or changed!=NEW or dirty):
        raise RuntimeError("P200 authentic hosted Windows source custody denied: "+
           json.dumps({"head":head,"ancestor":ancestor,"changed":sorted(changed),"dirty":dirty[:300]}))
    for subtree in ("tests","nayeon"):
        if git("rev-parse",P199+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P200 original production or historical security tests changed")
    for path in (
        "scripts/p195_windows_durable_root_authority_aba_review.py",
        "scripts/p196_windows_usn_aba_source_witness.py",
        "scripts/p197_windows_volume_journal_continuity_review.py",
        "scripts/p198_windows_source_byte_handoff_toctou_review.py",
        "scripts/p199_windows_consumer_identity_handoff_review.py",
    ):
        if git("show",P199+":"+path)!=(ROOT/path).read_bytes():
            raise RuntimeError("P200 prior native Windows negative security witness changed: "+path)
    return {"P200_HEAD":head,"exact_P199_parent":P199,
            "only_three_additive_audit_paths":sorted(NEW),
            "original_product_and_prior_security_negative_assertions_preserved":True}

def authenticate_p199(token:str)->dict:
    if len(token)<8:raise RuntimeError("P200 original predecessor artifact access missing")
    data=_download_artifact(ARTIFACT,ZIP_SHA,token)
    if sha(data)!=ZIP_SHA:raise RuntimeError("P200 predecessor original ZIP SHA invalid")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or set(z.namelist())!={LOG_NAME,LEDGER_NAME}:
            raise RuntimeError("P200 P199 genuine Windows ZIP inventory/CRC invalid")
        log=z.read(LOG_NAME);ledger_raw=z.read(LEDGER_NAME)
        if sha(log)!=LOG_SHA or sha(ledger_raw)!=LEDGER_SHA:
            raise RuntimeError("P200 predecessor native Windows log/HCR member SHA mismatch")
        text=log.decode("utf8","replace").replace("\r\n","\n")
        required=("P199_REAL_WINDOWS_PID_EXECUTABLE_IMAGE_NONCE_ORIGINAL_BYTES=LAB_MATCH",
                  "P199_UNPINNED_SCRIPT_WITH_SAME_PROCESS_IMAGE=UNSAFE_SELF_ATTESTED_ACCEPTANCE",
                  "P198_CALLER_SUPPLIED_HASH_WITH_SWAPPED_SOURCE=UNSAFE_ACCEPTANCE",
                  "P195_ADS_ADD_REMOVE_ABA=ADMITTED_TWO_SNAPSHOT_GAP")
        if any(marker not in text for marker in required):
            raise RuntimeError("P200 original historical Windows unsafe control missing")
        if (re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)!=["60"] or
            not re.search(r"^OK\s*$",text,re.M)):
            raise RuntimeError("P200 predecessor native 60 test OK footer invalid")
        record=json.loads(ledger_raw);native=record.get("current_P199_native",{})
        if (record.get("checkpoint")!="P199" or
            record.get("historical_H")!="HOLD" or record.get("production_R")!="HOLD" or
            record.get("full_unfiltered_native_Windows_product_regressions")!="0/3" or
            record.get("source_before")!=record.get("source_after") or
            record.get("source_before",{}).get("P199_HEAD")!=P199 or
            native.get("actual_OS_exit")!=0 or native.get("raw_log_SHA256")!=LOG_SHA or
            native.get("test_footer")!=["60"] or not native.get("complete_OK") or
            record.get("experimental_checkpoint_complete_NOT_product_release") is not True):
            raise RuntimeError("P200 authenticated predecessor P199 HCR/source invalid")
    return {"original_P199_native_artifact":ARTIFACT,"ZIP_SHA256":ZIP_SHA,
            "selected_real_Windows_60":"AUTHENTICATED",
            "P199_same_interpreter_spoof":"PRESERVED_UNSAFE",
            "full_product_regressions":"0/3","release":"HOLD"}

# Fixed, small, benign audit-owned Python script fixtures. These are never
# untrusted user code, credential operations, imports from project, or loaders.
APPROVED_CODE=r"""
import base64,hashlib,json,os,sys
line=sys.stdin.buffer.readline(1500000)
data=base64.b64decode(line.strip(),validate=True)
print(json.dumps({"marker":"P200_LAB_APPROVED_SCRIPT",
 "sha256":hashlib.sha256(data).hexdigest().upper(),
 "length":len(data),"pid":os.getpid()}),flush=True)
"""
ALTERNATE_CODE=r"""
import base64,hashlib,json,os,sys
line=sys.stdin.buffer.readline(1500000)
data=base64.b64decode(line.strip(),validate=True)
print(json.dumps({"marker":"P200_LAB_REPLACED_SCRIPT_EXECUTED",
 "sha256":hashlib.sha256(data).hexdigest().upper(),
 "length":len(data),"pid":os.getpid()}),flush=True)
"""
# Negative fixture deliberately ignores delivered source, and reads claimant-
# controlled expected hash/length from benign env instead of hashing any bytes.
SPOOF_CODE=r"""
import json,os,sys
sys.stdin.buffer.readline(1500000)
print(json.dumps({"marker":"P200_LAB_APPROVED_SCRIPT",
 "sha256":os.environ["P200_LAB_CLAIMED_SHA256"],
 "length":int(os.environ["P200_LAB_CLAIMED_LENGTH"]),
 "pid":os.getpid()}),flush=True)
"""
CHILD_REPLACE_ONLY=r"""
import base64,json,os,pathlib,sys
target=pathlib.Path(sys.argv[1])
replacement=target.with_name("p200-self-owned-atomic-replacement")
replacement.write_bytes(base64.b64decode(sys.argv[2],validate=True))
os.replace(replacement,target)
print(json.dumps({"status":"P200_DISPOSABLE_SCRIPT_REPLACED",
                  "size":target.stat().st_size}),flush=True)
"""

def payload(code:str,image:Path,source:bytes,script_path:Path)->dict:
    return {"format":"P200-EPHEMERAL-EXEC-CONTENT-LAB-v1",
            "release_commit":P199,"epoch":11,
            "audience":"P200-NONPRIVILEGED-DISPOSABLE-SCRIPT-ONLY",
            "intended_script_sha256":sha(code.encode("utf8")),
            "intended_script_path":str(script_path),
            "interpreter_path":os.path.normcase(os.path.abspath(image)),
            "interpreter_sha256":sha(image.read_bytes()),
            "source_sha256":sha(source)}

def signed(p:dict,signer:Ed25519PrivateKey)->bytes:
    return previous.signed_record(p,signer)

def verify_manifest(raw:bytes,public,expected:dict,minimum_epoch:int=11)->dict:
    if public is None or minimum_epoch is None:
        raise win.SourceDenied("P200_INDEPENDENT_SIGNER_OR_EPOCH_ABSENT")
    try:
        o=json.loads(raw)
        if type(o) is not dict or set(o)!={"payload","signature"}:raise ValueError("fields")
        p=o["payload"]
        if type(p) is not dict:raise ValueError("payload type")
        public.verify(base64.b64decode(o["signature"],validate=True),canonical(p))
    except (ValueError,TypeError,KeyError,InvalidSignature,UnicodeError) as exc:
        raise win.SourceDenied("P200_LAB_SIGNED_CONTENT_MANIFEST_INVALID") from exc
    if (type(p.get("epoch")) is not int or p["epoch"]<minimum_epoch or p!=expected):
        raise win.SourceDenied("P200_SIGNED_SCRIPT_SOURCE_OR_RELEASE_MISMATCH")
    return p

class P200NativeExecutableContentBinding(previous.P199NativeConsumerProvenanceReview):
    """Inherits 60 genuine P194–P199 tests; adds 10 Windows code identity cases."""
    def setUp(self):
        super().setUp()
        self.script=self.root/"p200-disposable-exec-content.py"
        self.script.write_bytes(APPROVED_CODE.encode("utf8"))
        self.claim=payload(APPROVED_CODE,self.image,self.sealed,self.script)
        self.record=signed(self.claim,self.lab_signer)

    def verify_lab(self,blob=None,public=None,minimum_epoch=11):
        trusted=self.lab_public if public is None else public
        return verify_manifest(self.record if blob is None else blob,
                               trusted,self.claim,minimum_epoch)

    def guard_path(self):
        self.verify_lab()
        if not self.script.is_relative_to(self.root):
            raise win.SourceDenied("P200_SCRIPT_OUTSIDE_DISPOSABLE_ROOT")
        if sha(self.script.read_bytes())!=self.claim["intended_script_sha256"]:
            raise win.SourceDenied("P200_SCRIPT_PATH_BYTES_NOT_RELEASE_PIN")
        return True

    def swap(self,code:str):
        if code not in (ALTERNATE_CODE,SPOOF_CODE):
            raise RuntimeError("P200 only permitted static benign negative script fixtures")
        if not self.script.is_relative_to(self.root):
            raise RuntimeError("P200 source outside disposable test root")
        p=subprocess.run([sys.executable,"-I","-B","-c",CHILD_REPLACE_ONLY,
                  str(self.script),base64.b64encode(code.encode("utf8")).decode("ascii")],
                  cwd=self.root,env=self.child_env(),stdin=subprocess.DEVNULL,
                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
        if p.returncode!=0:
            self.fail("P200 native Windows external script replacer failed: "+
                      p.stderr.decode("utf8","replace")[-500:])
        result=json.loads(p.stdout.decode("utf8","strict"))
        self.assertEqual(result["status"],"P200_DISPOSABLE_SCRIPT_REPLACED")
        self.assertEqual(self.script.read_bytes(),code.encode("utf8"))
        print("P200_ACTUAL_SECOND_WINDOWS_PROCESS_ATOMIC_TEST_SCRIPT_SWAP=SUCCEEDED",flush=True)

    def run_script(self,*,script_path:Path|None=None,inline_code:str|None=None,data:bytes|None=None):
        if (script_path is None)==(inline_code is None):
            raise AssertionError("P200 one content source required")
        if script_path is not None and (script_path!=self.script or
                                        not script_path.is_relative_to(self.root)):
            raise AssertionError("P200 only disposable fixture Python path allowed")
        args=[sys.executable,"-I","-B","-u"]
        args+=["-c",inline_code] if inline_code is not None else [str(script_path)]
        env=self.child_env()
        env["P200_LAB_CLAIMED_SHA256"]=sha(self.sealed)
        env["P200_LAB_CLAIMED_LENGTH"]=str(len(self.sealed))
        p=subprocess.Popen(args,cwd=self.root,env=env,stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            # Actual hosted Windows process executable observation before data.
            actual=previous.observed_image(p.pid)
            previous.require_image(actual,str(self.image))
            source=self.sealed if data is None else data
            out,err=p.communicate(input=base64.b64encode(source)+b"\n",timeout=15)
        except BaseException:
            p.kill();p.communicate()
            raise
        self.assertEqual(p.returncode,0,
                  "P200 benign native child failed: "+err.decode("utf8","replace")[-350:])
        try:ack=json.loads(out.decode("utf8","strict").strip())
        except (UnicodeError,ValueError) as exc:
            raise win.SourceDenied("P200_ACTUAL_CHILD_DID_NOT_RETURN_JSON") from exc
        self.assertEqual(ack.get("pid"),p.pid)
        return ack,actual

    def test_61_real_native_windows_file_script_original_content_admitted_in_lab(self):
        self.assertTrue(self.guard_path())
        source=self.new_reader().read(B.SELF)
        self.assertEqual(source,self.sealed)
        ack,image=self.run_script(script_path=self.script,data=source)
        self.assertEqual(ack["marker"],"P200_LAB_APPROVED_SCRIPT")
        self.assertEqual(ack["sha256"],sha(self.sealed))
        self.assertEqual(ack["length"],len(self.sealed))
        self.assertEqual(image,os.path.normcase(os.path.abspath(self.image)))
        print("P200_REAL_WINDOWS_EXACT_APPROVED_TEST_SCRIPT_AND_SOURCE=LAB_OBSERVED",flush=True)

    def test_62_actual_second_process_replaces_validated_script_before_child_load(self):
        self.assertTrue(self.guard_path())
        self.swap(ALTERNATE_CODE)
        ack,image=self.run_script(script_path=self.script)
        self.assertEqual(ack["marker"],"P200_LAB_REPLACED_SCRIPT_EXECUTED")
        self.assertEqual(ack["sha256"],sha(self.sealed))
        self.assertNotEqual(sha(self.script.read_bytes()),self.claim["intended_script_sha256"])
        print("P200_AFTER_PREVALIDATION_SCRIPT_PATH_SWAP=OS_EXECUTED_WRONG_CONTENT_UNSAFE",flush=True)

    def test_63_revalidation_after_disposable_script_replace_fails_closed(self):
        self.swap(ALTERNATE_CODE)
        with self.assertRaisesRegex(win.SourceDenied,"P200_SCRIPT_PATH_BYTES_NOT_RELEASE_PIN"):
            self.guard_path()
        print("P200_UPDATED_SCRIPT_BYTES_AT_NEW_PRELAUNCH_GUARD=REFUSED",flush=True)

    def test_64_pinned_original_inline_bytes_survive_disposable_path_replacement(self):
        self.assertTrue(self.guard_path())
        self.swap(ALTERNATE_CODE)
        self.verify_lab()
        # The test producer chooses exact original static code bytes after
        # signature validation. This is NOT OS-backed execution code attestation.
        self.assertEqual(sha(APPROVED_CODE.encode()),self.claim["intended_script_sha256"])
        ack,image=self.run_script(inline_code=APPROVED_CODE)
        self.assertEqual(ack["marker"],"P200_LAB_APPROVED_SCRIPT")
        self.assertEqual(ack["sha256"],sha(self.sealed))
        print("P200_PINNED_INLINE_SCRIPT_BYTES_DESPITE_FILE_PATH_SWAP=LAB_ONLY",flush=True)

    def test_65_signed_different_static_code_digest_refused(self):
        tampered=dict(self.claim)
        tampered["intended_script_sha256"]=sha(ALTERNATE_CODE.encode("utf8"))
        with self.assertRaisesRegex(win.SourceDenied,"P200_SIGNED_SCRIPT_SOURCE_OR_RELEASE_MISMATCH"):
            self.verify_lab(blob=signed(tampered,self.lab_signer))
        print("P200_SIGNED_ALTERNATE_SCRIPT_DIGEST=REFUSED",flush=True)

    def test_66_forged_ephemeral_signer_denied_before_launch(self):
        fake=signed(self.claim,Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(win.SourceDenied,"P200_LAB_SIGNED_CONTENT_MANIFEST_INVALID"):
            self.verify_lab(blob=fake)
        print("P200_FOREIGN_EPHEMERAL_SIGNER=REFUSED",flush=True)

    def test_67_signed_wrong_release_and_epoch_below_floor_refused(self):
        for changes in ({"release_commit":"not-original-P199"},
                        {"epoch":10}):
            tampered={**self.claim,**changes}
            with self.assertRaisesRegex(win.SourceDenied,"P200_SIGNED_SCRIPT_SOURCE_OR_RELEASE_MISMATCH"):
                self.verify_lab(blob=signed(tampered,self.lab_signer))
        print("P200_SIGNED_OTHER_RELEASE_OR_OLD_SYNTHETIC_EPOCH=REFUSED",flush=True)

    def test_68_missing_trusted_signer_or_epoch_refused(self):
        for public,floor in ((None,11),(self.lab_public,None)):
            with self.assertRaisesRegex(win.SourceDenied,"P200_INDEPENDENT_SIGNER_OR_EPOCH_ABSENT"):
                verify_manifest(self.record,public,self.claim,floor)
        print("P200_MISSING_INDEPENDENT_TRUST_ANCHOR_OR_FLOOR=FAIL_CLOSED",flush=True)

    def test_69_signed_wrong_source_and_corrupt_manifest_refused(self):
        tampered=dict(self.claim)
        tampered["source_sha256"]=sha(b"substituted-content")
        with self.assertRaisesRegex(win.SourceDenied,"P200_SIGNED_SCRIPT_SOURCE_OR_RELEASE_MISMATCH"):
            self.verify_lab(blob=signed(tampered,self.lab_signer))
        with self.assertRaisesRegex(win.SourceDenied,"P200_LAB_SIGNED_CONTENT_MANIFEST_INVALID"):
            self.verify_lab(blob=b'{"payload":')
        print("P200_WRONG_SIGNED_DATA_DIGEST_OR_CORRUPT_RECORD=REFUSED",flush=True)

    def test_70_fake_script_self_reports_expected_hash_without_hashing_source(self):
        self.assertTrue(self.guard_path())
        self.swap(SPOOF_CODE)
        ack,image=self.run_script(script_path=self.script)
        self.assertEqual(ack["marker"],"P200_LAB_APPROVED_SCRIPT")
        self.assertEqual(ack["sha256"],sha(self.sealed))
        self.assertEqual(ack["length"],len(self.sealed))
        self.assertNotEqual(sha(self.script.read_bytes()),
                            self.claim["intended_script_sha256"])
        print("P200_DIFFERENT_OS_EXECUTED_SCRIPT_FAKED_APPROVED_RECEIPT=UNSAFE_SELF_ATTESTATION",flush=True)

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p200-executable-content"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P200","historical_H":"HOLD",
            "current_C":"ISOLATED_TEST_SCRIPT_CONTENT_PIN_VS_POST_VALIDATION_EXECUTION_TOCTOU",
            "production_R":"HOLD","unfiltered_genuine_Windows_full_product_regressions":"0/3",
            "qualified_independent_reviews":p194.REVIEWS,"privileged_G0_G6":"OPEN",
            "original_full_private_BYOK_B_named_ADS_gap":"CONFIRMED_UNPATCHED",
            "P195_ABA_P198_path_reopen_P199_interpreter_spoof":"PRESERVED_UNSAFE_NEGATIVES",
            "genuine_production_trusted_signed_loader":"NOT_IMPLEMENTED",
            "actual_executed_code_identity_signed_attestation":"NOT_ESTABLISHED",
            "original_B_23_pin_and_Phase10_product_code":"NOT_INTEGRATED",
            "native_signed_main_helper_installer_CodeIntegrity_WDAC_SAC":"NO_GO",
            "signed_fixture_root_and_rollback_floor":"SYNTHETIC_ONLY",
            "original_P135_P175_P178_P179_PERF_P187_01":"UNWAIVED"}
    complete=False
    try:
        before=custody();ledger["source_before"]=before
        ledger["authentic_original_P199"]=authenticate_p199(
              os.environ.get("P200_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        for k in list(env):
            if (k in ("GH_TOKEN","GITHUB_TOKEN","P200_ARCHIVE_TOKEN") or
                k.endswith(("_API_KEY","_SECRET"))):
                env.pop(k,None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        log=out/"p200_real_Windows_executable_content_70_selected.log"
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                    "scripts.p200_windows_executable_content_binding_review.P200NativeExecutableContentBinding"],
                    cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                    stdout=f,stderr=subprocess.STDOUT,timeout=280,check=False)
        raw=log.read_bytes();text=raw.decode("utf8","replace").replace("\r\n","\n")
        events=re.findall(r"^P200_[^\r\n]+",text,re.M)
        ledger["current_P200_native"]={
            "raw_log":log.name,"raw_log_SHA256":sha(raw),"actual_OS_exit":p.returncode,
            "test_footer":re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M),
            "complete_OK":bool(re.search(r"^OK\s*$",text,re.M)),
            "events":events}
        if (p.returncode!=0 or ledger["current_P200_native"]["test_footer"]!=["70"] or
            not ledger["current_P200_native"]["complete_OK"]):
            raise RuntimeError("P200 original security and Windows execution selected tests failed; retain logs")
        for marker in (
            "P200_REAL_WINDOWS_EXACT_APPROVED_TEST_SCRIPT_AND_SOURCE=LAB_OBSERVED",
            "P200_AFTER_PREVALIDATION_SCRIPT_PATH_SWAP=OS_EXECUTED_WRONG_CONTENT_UNSAFE",
            "P200_UPDATED_SCRIPT_BYTES_AT_NEW_PRELAUNCH_GUARD=REFUSED",
            "P200_PINNED_INLINE_SCRIPT_BYTES_DESPITE_FILE_PATH_SWAP=LAB_ONLY",
            "P200_SIGNED_ALTERNATE_SCRIPT_DIGEST=REFUSED",
            "P200_FOREIGN_EPHEMERAL_SIGNER=REFUSED",
            "P200_SIGNED_OTHER_RELEASE_OR_OLD_SYNTHETIC_EPOCH=REFUSED",
            "P200_MISSING_INDEPENDENT_TRUST_ANCHOR_OR_FLOOR=FAIL_CLOSED",
            "P200_WRONG_SIGNED_DATA_DIGEST_OR_CORRUPT_RECORD=REFUSED",
            "P200_DIFFERENT_OS_EXECUTED_SCRIPT_FAKED_APPROVED_RECEIPT=UNSAFE_SELF_ATTESTATION",
        ):
            if marker not in events:
                raise RuntimeError("P200 exact real Windows security marker absent: "+marker)
        after=custody();ledger["source_after"]=after
        if before!=after:raise RuntimeError("P200 original source changed during Windows lab")
        complete=True
        print("P200_ORIGINAL_P199_AUTHENTIC_ZIP_AND_60_SELECTED_WINDOWS=VERIFIED",flush=True)
        print("P200_REAL_NATIVE_WINDOWS_EXEC_CONTENT_SECURITY=70/70_PASS_NOT_FULL_PRODUCT",flush=True)
        print("P200_PATH_SCRIPT_POST_ADMISSION_SWAP_AND_SELF_ATTESTATION=UNSAFE_EXECUTION_CONTENT",flush=True)
        print("P200_ORIGINAL_BYOK_B_ADS_GAP=UNPATCHED|FULL_PRODUCT_NATIVE_WINDOWS=0/3|RELEASE_HOLD",flush=True)
    except BaseException as exc:
        ledger["collector_error"]=repr(exc)
        print("P200_NATIVE_EXECUTABLE_CONTENT=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["experimental_checkpoint_complete_NOT_product_release"]=complete
        (out/"p200_executable_content_HCR_ledger.json").write_text(
             json.dumps(ledger,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if complete else 1
if __name__=="__main__":raise SystemExit(main())
