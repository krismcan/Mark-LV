"""P181 adversarial review of the *unchanged* P180 batch blob prototype.

This is an internal, source-preserving security assessment, NOT a qualified
independent review or a release. Genuine GitHub-hosted Windows Python cases
demonstrate both negative refusals and gaps in the prototype's session
failure-handling. No production verifier, frozen test or code integrity edits.
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
import unittest
from unittest import mock
import zipfile

from scripts import p180_windows_sealed_blob_transport_equivalence as candidate
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
BASE="20a3611cfcbc6c770b369120fd07c303cbb76eff"
BRANCH="byok-c1-p181-batch-transport-security-adversarial-review-20261112"
NEW={
 ".github/workflows/p181-windows-batch-transport-security-adversarial-review.yml",
 "docs/byok-c1-p181-batch-transport-security-review.md",
 "scripts/p181_windows_batch_transport_security_review.py",
}
P180_ID=13981329771
P180_ZIP_SHA="98162805A2C144B9B25E541D2A993AB8C75EA670E0EA7D6CC5FF5C9C97856056"
P180_LEDGER="p180_authentic_Windows_sealed_blob_transport_prototype_ledger.json"
P180_LOG="p180_original_Windows_eight_adversarial_protocol_tests.log"
P180_LOG_SHA="AC068ABBDC8CC73929F737D7AC87BCCE9B7F27132D46829E6CBB2352CC9B5DCA"
REVIEWS={name:"OPEN" for name in (
 "GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        check=True,timeout=35).stdout

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
        raise RuntimeError("P181 exact clean source-bound hosted Windows push required")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P181 only three newly added review files may change")
    for subtree in ("nayeon","tests"):
        if git("rev-parse",BASE+":"+subtree)!=git("rev-parse","HEAD:"+subtree):
            raise RuntimeError("P181 frozen "+subtree+" subtree changed")
    src=ROOT/"scripts/p180_windows_sealed_blob_transport_equivalence.py"
    if src.read_bytes()!=git("show",BASE+":"+src.relative_to(ROOT).as_posix()):
        raise RuntimeError("P181 original P180 prototype was edited rather than reviewed")
    original=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
              if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(original)!=171:
        raise RuntimeError("P181 frozen original 171 module inventory changed")
    return {
        "source_HEAD":git("rev-parse","HEAD").decode().strip(),
        "P180_exact_immutable_parent":BASE,
        "only_three_new_review_files":sorted(NEW),
        "all_original_nayeon_tests_and_P180_prototype_unchanged":True,
        "original_module_count":len(original),
        "original_P180_script_SHA256":sha(src.read_bytes()),
    }

def authenticate_P180(token:str)->dict:
    if len(token)<8:
        raise RuntimeError("P181 ephemeral GitHub Actions read-only archive token missing")
    raw=_download_artifact(P180_ID,P180_ZIP_SHA,token)
    if sha(raw)!=P180_ZIP_SHA:
        raise RuntimeError("P181 original P180 archive SHA256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if (z.testzip() is not None or len(z.namelist())!=2
            or set(z.namelist())!={P180_LEDGER,P180_LOG}):
            raise RuntimeError("P181 original P180 zip CRC/inventory mismatch")
        x=json.loads(z.read(P180_LEDGER))
        log=z.read(P180_LOG)
        t=log.decode("utf8","replace").replace("\r\n","\n")
        native=x.get("genuine_Windows_eight_adversarial_protocol_tests",{})
        b=x.get("real_Git_SHA1_blob_equivalence_benchmark",{})
        if (x.get("checkpoint")!="P180"
            or x.get("original_source_before")!=x.get("original_source_after")
            or x.get("original_source_before",{}).get("authenticated_P180_head")!=BASE
            or x.get("historical_H")!="HOLD" or x.get("production_R")!="HOLD"
            or x.get("full_product_regression_Windows")!="0/3"
            or x.get("review_decisions")!=REVIEWS
            or x.get("optimisation_accepted_into_product") is not False
            or x.get("source_bound_prototype_evidence_complete_NOT_product_recovery") is not True
            or native.get("complete_native_count")!=8
            or native.get("real_process_exit")!=0
            or native.get("raw_log_sha256")!=P180_LOG_SHA or sha(log)!=P180_LOG_SHA
            or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)!=["8"]
            or not re.search(r"^OK\s*$",t,re.M)
            or b.get("real_Git_object_identifiers_per_cycle")!=16
            or b.get("actual_original_git_show_calls")!=48
            or b.get("actual_new_batch_requests_each_returned_and_rehashed")!=48
            or b.get("all_raw_SHA256_identical_in_original_call_order") is not True):
            raise RuntimeError("P181 prior real P180 native 8/8 or 48/48 bytes evidence changed")
    return {
        "original_artifact_id":P180_ID,
        "authenticated_zip_SHA256":P180_ZIP_SHA,
        "authenticated_original_native_Windows_8_of_8_protocol_cases":True,
        "authenticated_original_48_of_48_Git_blob_bytes":True,
        "original_P180_prototype_not_product_optimisation":True,
    }

def _frame(oid:bytes,body:bytes,*,header:bytes|None=None,trailer:bytes=b"\n")->bytes:
    return (header if header is not None else
            oid+b" blob "+str(len(body)).encode("ascii")+b"\n")+body+trailer

class _FakeProcess:
    """Only for synthetic adversarial pipe responses; no real process changes."""
    def __init__(self,frames:bytes,code:int|None=None):
        self.stdout=io.BytesIO(frames)
        self.stdin=io.BytesIO()
        self.stderr=io.BytesIO()
        self.code=code
    def poll(self):return self.code

def _fake_batch(frames:bytes,code:int|None=None):
    b=object.__new__(candidate.FreshGitBlobBatch)
    b.process=_FakeProcess(frames,code)
    b.requests=0
    return b

def _oid(data:bytes)->bytes:
    return hashlib.sha1(
        b"blob "+str(len(data)).encode("ascii")+b"\0"+data
    ).hexdigest().encode("ascii")

class P181BatchAdversarialSecurityTests(unittest.TestCase):
    """12 original standalone tests: pass = accurately characterise P180, NOT GO."""

    def test_01_valid_synthetic_pipe_reads_original_authenticated_blob(self):
        data=b"safe\x00payload\n"
        oid=_oid(data)
        batch=_fake_batch(_frame(oid,data))
        self.assertEqual(batch.read(oid),data)
        self.assertEqual(batch.requests,1)

    def test_02_wrong_oid_from_stdout_refused_and_request_not_counted(self):
        data=b"unchanged"
        oid=_oid(data)
        batch=_fake_batch(_frame(b"a"*40,data))
        with self.assertRaisesRegex(ValueError,"OID/type/line"):
            batch.read(oid)
        self.assertEqual(batch.requests,0)

    def test_03_wrong_Git_object_type_refused_even_when_hash_matches(self):
        data=b"object-body"
        oid=_oid(data)
        invalid=oid+b" tree "+str(len(data)).encode()+b"\n"
        with self.assertRaisesRegex(ValueError,"OID/type/line"):
            _fake_batch(_frame(oid,data,header=invalid)).read(oid)

    def test_04_tampered_payload_with_valid_header_refused(self):
        orig=b"expected"
        oid=_oid(orig)
        altered=b"altered!"
        with self.assertRaisesRegex(ValueError,"digest mismatch"):
            _fake_batch(_frame(oid,altered)).read(oid)

    def test_05_short_body_fails_closed_without_good_footer(self):
        orig=b"longer than reply"
        oid=_oid(orig)
        fake=_fake_batch(oid+b" blob "+str(len(orig)).encode()+b"\n"+b"short")
        with self.assertRaises(RuntimeError):
            fake.read(oid)
        self.assertEqual(fake.requests,0)

    def test_06_malformed_or_missing_blob_terminator_refused(self):
        data=b"payload"
        oid=_oid(data)
        for suffix in (b"",b"\r",b"X"):
            with self.subTest(suffix=suffix):
                b=_fake_batch(_frame(oid,data,trailer=suffix))
                with self.assertRaises(ValueError):
                    b.read(oid)
                self.assertEqual(b.requests,0)

    def test_07_dead_child_refused_before_any_request(self):
        data=b"body"
        oid=_oid(data)
        b=_fake_batch(_frame(oid,data),code=9)
        with self.assertRaisesRegex(RuntimeError,"not in live batch"):
            b.read(oid)
        self.assertEqual(b.requests,0)

    def test_08_bad_untrusted_OID_fails_before_process_IO(self):
        b=_fake_batch(b"")
        for bad in (b"0"*39,b"F"*40,b"x"*40,b"0"*40+b"\n",b""):
            with self.subTest(oid=bad):
                with self.assertRaises(ValueError):
                    b.read(bad)
        self.assertEqual(b.process.stdin.getvalue(),b"")

    def test_09_bad_oversize_or_partial_header_refused(self):
        data=b"x"
        oid=_oid(data)
        for header in (oid+b" blob 2000001\n",oid+b" blob -1\n",
                       oid+b" blob 1",b"missing\n"):
            with self.subTest(header=header):
                b=_fake_batch(header)
                with self.assertRaises(ValueError):
                    b.read(oid)

    def test_10_current_P180_does_not_retire_session_after_protocol_fault(self):
        """Demonstrates an OPEN security gap, not a pass of the safety policy."""
        data=b"good real content"
        oid=_oid(data)
        b=_fake_batch(b"untrusted invalid header\n"+_frame(oid,data))
        with self.assertRaises(ValueError):
            b.read(oid)
        # This is an observed vulnerable behaviour, documented as HOLD:
        # a poisoned stream can be reused; product must instead kill/retire it.
        self.assertEqual(b.read(oid),data)
        self.assertEqual(b.requests,1)

    def test_11_current_P180_blocking_pipe_reads_have_no_deadline(self):
        """Detects an OPEN liveness gap without intentionally hanging CI."""
        source=inspect.getsource(candidate.FreshGitBlobBatch.read)
        self.assertIn("p.stdout.readline(110)",source)
        self.assertIn("p.stdout.read(",source)
        self.assertNotIn("timeout=",source)
        self.assertNotIn("select(",source)
        self.assertNotIn("wait(",source)

    def test_12_stale_OID_replay_and_unsafe_path_are_denied(self):
        old=b"old"
        newer=b"new"
        oid=_oid(old)
        with self.assertRaises(ValueError):
            _fake_batch(_frame(oid,newer)).read(oid)
        for path in ("tests/../secrets","tests\\evil","tests/two//names",
                     "Tests/alias","nayeon/secret:ads","tests/a."):
            with self.subTest(path=path):
                self.assertFalse(candidate.valid_path(path))

def finding_register()->dict:
    return {
        "SEC-P181-01":{
            "severity":"HIGH",
            "state":"OPEN_CONFIRMED_BY_STATIC_TEST_11",
            "risk":"P180 batch read performs blocking stdout readline/read without per-operation deadline; a stuck or malicious child can block verification indefinitely.",
            "candidate_required_fix":"Use a bounded, supervised worker or genuine process deadline with deterministic child termination; all timeouts fail closed and disallow reuse."
        },
        "SEC-P181-02":{
            "severity":"HIGH",
            "state":"OPEN_CONFIRMED_BY_SYNTHETIC_TEST_10",
            "risk":"After a malformed protocol header, P180 leaves the batch session usable; a subsequent valid response is accepted on the same already-poisoned stream.",
            "candidate_required_fix":"Retire and kill the entire session on ANY I/O, header, digest, trailer or process error; require fresh independently authenticated state."
        },
        "SEC-P181-03":{
            "severity":"HIGH",
            "state":"OPEN_SOURCE_GOVERNANCE",
            "risk":"P180 prototype resolves source commit/path and OID before repeated requests and is not integrated with every-call historical disk/index/tag/security owner verification.",
            "candidate_required_fix":"Independently prove equivalent live disk/index/HEAD, frozen tags, Windows reparse/aliases, object modes, revocation and tamper negatives on EVERY verifier invocation."
        },
        "SEC-P181-04":{
            "severity":"MEDIUM",
            "state":"OPEN_UNREVIEWED_PROCESS_TRUST",
            "risk":"Persistent Git child executable identity, cwd, environment, config, lifetime, subprocess origin and cross-process writer racing are not production-proven.",
            "candidate_required_fix":"Pin trusted Git executable and arguments, isolate config/env, verify canonical repo identity and process ownership; fail closed on drift."
        },
        "SEC-P181-05":{
            "severity":"HIGH",
            "state":"OPEN_CRYPTOGRAPHIC_POLICY_REVIEW",
            "risk":"Transport checks Git SHA1 OID and mode on narrow fixture only; actual original legacy SHA256 seals/code signing and source-era applicability are not revalidated by this performance prototype.",
            "candidate_required_fix":"Preserve and independently verify all original full raw-source SHA256 security seals, external signatures and P76/P85/P140 negative policy assertions."
        },
        "GOV-P181-06":{
            "severity":"RELEASE_BLOCKER",
            "state":"OPEN_INDEPENDENT_QUALIFIED_REVIEW_NOT_OBTAINED",
            "risk":"P180 8/8 and 48/48 stand-alone success cannot authorise replacement of any original historical verifier or 3/3 Windows full-product acceptance.",
            "candidate_required_fix":"Qualified independent reviewer signed disposition; production admission only after 3 complete unfiltered native Windows full-product passes, signer/SAC/WDAC and G0-G6 approvals."
        }
    }

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p181-transport-review"
    out.mkdir(parents=True,exist_ok=True)
    ledger={
        "checkpoint":"P181",
        "historical_H":"HOLD",
        "current_C":"ADVERSARIAL_INTERNAL_SECURITY_REVIEW_ONLY",
        "production_R":"HOLD",
        "full_product_Windows_regression_acceptance":"0/3",
        "qualified_external_reviewer":None,
        "independent_external_decisions":REVIEWS,
        "findings":finding_register(),
        "legacy_source_and_original_test_edited":False,
        "batch_transport_authorised_for_historical_verifier":False,
        "real_credential_provider_network_privileged_service":"NOT_ATTEMPTED",
        "privileged_C1_G0_to_G6":"OPEN",
    }
    good=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["authenticated_prior_original_P180_windows"]=authenticate_P180(
            os.environ.get("P181_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for key in list(env):
            if (key in ("P181_ARCHIVE_TOKEN","GITHUB_TOKEN","GH_TOKEN")
                or key.endswith("_API_KEY") or key.endswith("_SECRET")):
                env.pop(key,None)
        log=out/"p181_genuine_windows_twenty_original_and_review_tests.log"
        with log.open("wb") as f:
            run=subprocess.run(
                [sys.executable,"-B","-m","unittest","-v",
                 "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests",
                 "scripts.p181_windows_batch_transport_security_review.P181BatchAdversarialSecurityTests"],
                cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,timeout=95,check=False)
        raw=log.read_bytes()
        text=raw.decode("utf8","replace").replace("\r\n","\n")
        count=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)
        ledger["actual_unfiltered_original_P180_and_new_P181_Windows_log"]={
            "native_exit":run.returncode,
            "native_original_P180_cases":8,
            "native_P181_adversarial_case_count":12,
            "native_complete_combined_case_count":int(count[-1]) if count else None,
            "complete_raw_log_SHA256":sha(raw),
            "complete_raw_log_filename":log.name,
            "named_failure_and_error_records":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M),
        }
        if (run.returncode!=0 or count!=["20"]
            or not re.search(r"^OK\s*$",text,re.M)):
            raise RuntimeError("P181 genuine Windows original+adversarial cases did not all finish")
        ledger["source_after"]=custody()
        good=(before==ledger["source_after"])
        ledger["internal_adversarial_evidence_complete_not_a_qualified_security_signoff"]=good
        if not good:raise RuntimeError("P181 exact source changed during review")
        print("P181_REAL_WINDOWS_20_CASES=20/20_PASS|NATIVE_EXIT=0",flush=True)
        print("P181_P180_8_ORIGINAL_CASES=REEXECUTED_UNCHANGED",flush=True)
        print("P181_CURRENT_CANDIDATE_POISONED_STREAM_REUSE_GAP=DEMONSTRATED_OPEN",flush=True)
        print("P181_CURRENT_CANDIDATE_UNBOUNDED_BLOCKING_IO_GAP=DEMONSTRATED_OPEN",flush=True)
        print("P181_OPEN_SECURITY_AND_GOVERNANCE_FINDINGS="+str(len(ledger["findings"])),flush=True)
        print("P181_NATIVE_LOG_SHA256="+sha(raw),flush=True)
        print("P181_EXTERNAL_REVIEW=NOT_OBTAINED|FULL_WINDOWS=0/3|RELEASE=HOLD",flush=True)
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P181_AUTHENTIC_WINDOWS_ADVERSARIAL_REVIEW=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["internal_adversarial_evidence_complete_not_a_qualified_security_signoff"]=good
        (out/"p181_original_windows_internal_adversarial_batch_transport_review_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
