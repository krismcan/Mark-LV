"""P182 — bounded, fail-closed batch-Git transport EXPERIMENT, not product integration.

Separate source-preserving candidate fixes P181 SEC-P181-01/02 at the
TRANSPORT PROTOTYPE level ONLY: each request has a deadline; any invalid
request, pipe error, corrupt frame, stalled child, digest mismatch or process
exit irrevocably retires that process. No historical verifier, product, or
original security test source is changed. Full product/release gates HOLD.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock
import zipfile

from scripts import p180_windows_sealed_blob_transport_equivalence as old
from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
BASE="0e4cd7065eb2ebd0d3eb247813b52c0fcd75cb00"
BRANCH="byok-c1-p182-fail-closed-batch-transport-candidate-20261112"
NEW={
 ".github/workflows/p182-windows-fail-closed-batch-transport.yml",
 "docs/byok-c1-p182-fail-closed-git-batch-transport.md",
 "scripts/p182_windows_fail_closed_batch_transport.py",
}
P181_ID=13987327101
P181_ZIP="E64841054B845A7B2012BA33B48A36F6376BCB191F4F2AD9474C5685118869D4"
P181_LOG="p181_genuine_windows_twenty_original_and_review_tests.log"
P181_LOG_SHA="9676B56328DF0272172335F627B6ACD47A6C658AB626E9B1CFC2880666EC73B9"
P181_LEDGER="p181_original_windows_internal_adversarial_batch_transport_review_ledger.json"
REVIEWS={n:"OPEN" for n in
 ("GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          check=True,timeout=30).stdout

def custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("status","--porcelain=v1").strip()
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE):
        raise RuntimeError("P182 requires clean authenticated exact hosted Windows source")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P182 three additive audit candidate paths only")
    for sub in ("nayeon","tests"):
        if git("rev-parse",BASE+":"+sub)!=git("rev-parse","HEAD:"+sub):
            raise RuntimeError("P182 original product or frozen historical tests altered")
    for path in ("scripts/p180_windows_sealed_blob_transport_equivalence.py",
                 "scripts/p181_windows_batch_transport_security_review.py"):
        if (ROOT/path).read_bytes()!=git("show",BASE+":"+path):
            raise RuntimeError("P182 original P180/P181 source changed instead of isolated candidate")
    paths=[s for s in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
           if re.fullmatch(r"tests/test_[^/]+\.py",s)]
    if len(paths)!=171:raise RuntimeError("P182 original test module count drift")
    return {"head":git("rev-parse","HEAD").decode().strip(),
            "source_parent":BASE,"additive_paths":sorted(NEW),
            "product_original_tests_and_old_prototypes_unchanged":True,
            "original_modules":171}

def authenticate_P181(token:str)->dict:
    if len(token)<8:raise RuntimeError("P182 no ephemeral read-only artifact token")
    raw=_download_artifact(P181_ID,P181_ZIP,token)
    if sha(raw)!=P181_ZIP:
        raise RuntimeError("P182 authentic P181 original Windows archive changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if (z.testzip() is not None or len(z.namelist())!=2
            or set(z.namelist())!={P181_LOG,P181_LEDGER}):
            raise RuntimeError("P182 P181 original Windows ZIP member CRC drift")
        ledger=json.loads(z.read(P181_LEDGER))
        log=z.read(P181_LOG)
        t=log.decode("utf8","replace").replace("\r\n","\n")
        native=ledger.get("actual_unfiltered_original_P180_and_new_P181_Windows_log",{})
        findings=ledger.get("findings",{})
        if (ledger.get("checkpoint")!="P181"
            or ledger.get("source_before")!=ledger.get("source_after")
            or ledger.get("source_before",{}).get("source_HEAD")!=BASE
            or ledger.get("historical_H")!="HOLD"
            or ledger.get("production_R")!="HOLD"
            or ledger.get("full_product_Windows_regression_acceptance")!="0/3"
            or ledger.get("independent_external_decisions")!=REVIEWS
            or ledger.get("internal_adversarial_evidence_complete_not_a_qualified_security_signoff") is not True
            or native.get("native_exit")!=0
            or native.get("native_complete_combined_case_count")!=20
            or native.get("complete_raw_log_SHA256")!=P181_LOG_SHA
            or sha(log)!=P181_LOG_SHA
            or re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)!=["20"]
            or not re.search(r"^OK\s*$",t,re.M)
            or findings.get("SEC-P181-01",{}).get("severity")!="HIGH"
            or findings.get("SEC-P181-02",{}).get("severity")!="HIGH"
            or len(findings)!=6):
            raise RuntimeError("P182 original 20-case P181 reviewer finding or log custody drift")
    return {"original_P181_artifact":P181_ID,
            "ZIP_SHA256":P181_ZIP,"original_true_native_windows_P180_P181_cases":20,
            "OPEN_P181_high_severity_liveness_and_reuse_findings":2,
            "all_six_P181_governance_findings_unwaived":True}


class FailClosedGitBatch:
    """Per-request bounded worker; original Git object bytes rehashed each time.

    This candidate is not wired into old security verifiers. It imposes
    single-flight read serialization, no cache and one irreversible
    retirement path for EVERY failed request. The worker is a daemon
    only to keep a compromised synthetic pipe from blocking shutdown;
    after a deadline the child is killed before any new request can run.
    """
    def __init__(self,*,timeout_seconds:float=3.0,process=None):
        if not isinstance(timeout_seconds,(int,float)) or not (0.02<=timeout_seconds<=20):
            raise ValueError("P182 bounded positive deadline required")
        self.deadline=float(timeout_seconds)
        self._lock=threading.Lock()
        self._retired=False
        self._reason=None
        self._requests=0
        self._thread=None
        self.process=process
        if self.process is None:
            executable=shutil.which("git")
            if not executable or not Path(executable).is_file():
                raise RuntimeError("P182 Git executable not resolvable")
            env=os.environ.copy()
            for key in list(env):
                if key in {"GIT_CONFIG_COUNT","GIT_CONFIG_PARAMETERS","GIT_CONFIG_KEY_0",
                           "GIT_CONFIG_VALUE_0","GIT_DIR","GIT_WORK_TREE",
                           "GIT_INDEX_FILE","GIT_OBJECT_DIRECTORY","GIT_ALTERNATE_OBJECT_DIRECTORIES"}:
                    env.pop(key,None)
            env["GIT_CONFIG_NOSYSTEM"]="1"
            env["GIT_CONFIG_GLOBAL"]="NUL" if os.name=="nt" else os.devnull
            self.process=subprocess.Popen(
                [str(Path(executable).resolve()),"-C",str(ROOT),"cat-file","--batch"],
                cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))

    @property
    def retired(self)->bool:return self._retired

    @property
    def completed_requests(self)->int:return self._requests

    def _retire(self,why:str)->None:
        """Irreversible, idempotent best-effort kill. Never reuse a bad pipe."""
        if self._retired:return
        self._retired=True
        self._reason=why
        p=self.process
        if p is None:return
        try:p.kill()
        except (OSError,ProcessLookupError,AttributeError):pass
        try:p.wait(timeout=1.0)
        except (subprocess.TimeoutExpired,OSError,AttributeError):pass
        worker=self._thread
        if worker is not None and worker.is_alive():
            worker.join(timeout=0.25)
        # Never let a pipe close block a timed-out worker; that thread is
        # daemon and the parent retains an irrevocably poisoned session.
        if worker is None or not worker.is_alive():
            for name in ("stdin","stdout","stderr"):
                f=getattr(p,name,None)
                if f is not None:
                    try:f.close()
                    except (OSError,ValueError):pass

    def close(self)->None:
        with self._lock:
            self._retire("CLOSED")

    def read(self,oid:bytes)->bytes:
        with self._lock:
            if self._retired:
                raise RuntimeError("P182 retired Git batch session cannot be reused")
            if not old.valid_oid(oid):
                self._retire("INVALID_REQUEST")
                raise ValueError("P182 invalid object ID and entire session retired")
            p=self.process
            if p is None or p.poll() is not None or p.stdin is None or p.stdout is None:
                self._retire("CHILD_NOT_RUNNING")
                raise RuntimeError("P182 child not running; session retired")
            result=queue.Queue(maxsize=1)
            def worker():
                try:
                    # Entire write + read + hash operation subject to ONE
                    # elapsed deadline, not a per-chunk budget reset.
                    p.stdin.write(oid+b"\n")
                    p.stdin.flush()
                    header=p.stdout.readline(110)
                    n=old.validate_header(header,oid)
                    data=bytearray()
                    while len(data)<n:
                        chunk=p.stdout.read(n-len(data))
                        if not chunk:
                            raise RuntimeError("P182 truncated Git blob body")
                        data.extend(chunk)
                    trailer=p.stdout.read(1)
                    payload=old.verify_blob(oid,bytes(data),trailer)
                    result.put(("OK",payload))
                except BaseException as error:
                    result.put(("ERROR",error))
            t=threading.Thread(target=worker,name="P182-Bounded-Git-Object-Read",daemon=True)
            self._thread=t
            t.start()
            t.join(timeout=self.deadline)
            if t.is_alive():
                self._retire("TIMEOUT")
                raise TimeoutError("P182 Git batch response deadline exceeded; child retired")
            try:kind,value=result.get_nowait()
            except queue.Empty:
                self._retire("MISSING_WORKER_RESULT")
                raise RuntimeError("P182 Git worker returned without verified result")
            if kind!="OK":
                self._retire("PROTOCOL_OR_IO_ERROR")
                raise RuntimeError("P182 Git batch protocol failure; child retired") from value
            if p.poll() is not None:
                self._retire("UNEXPECTED_CHILD_EXIT")
                raise RuntimeError("P182 batch child exited during verification")
            self._requests+=1
            return value


class _FakeStalledRead:
    def __init__(self,released:threading.Event):
        self.event=released
    def readline(self,n:int=-1)->bytes:
        self.event.wait(timeout=5)
        return b""
    def read(self,n:int=-1)->bytes:
        self.event.wait(timeout=5)
        return b""
    def close(self)->None:pass

class _FakePipeProcess:
    """Synthetic protocol input only; never launched on Kristian/live product."""
    def __init__(self,frames:bytes=b"",stalled:bool=False,exitcode=None):
        self.killed=False
        self.code=exitcode
        self.released=threading.Event()
        self.stdin=io.BytesIO()
        self.stdout=_FakeStalledRead(self.released) if stalled else io.BytesIO(frames)
        self.stderr=io.BytesIO()
    def poll(self):return self.code
    def kill(self):
        self.killed=True
        self.code=-9
        self.released.set()
    def wait(self,timeout=None):
        return self.code

def _blob_oid(body:bytes)->bytes:
    return hashlib.sha1(b"blob "+str(len(body)).encode("ascii")+b"\0"+body).hexdigest().encode()

def _frame(oid:bytes,body:bytes,*,header:bytes|None=None,trailer:bytes=b"\n")->bytes:
    return (header if header is not None else
            oid+b" blob "+str(len(body)).encode("ascii")+b"\n")+body+trailer


class P182FailClosedBatchSecurityCases(unittest.TestCase):
    """12 original candidate tests: true result is experimental only."""
    def test_01_verified_response_round_trip_no_cache(self):
        data=b"original\x00byte\xff\n"
        oid=_blob_oid(data)
        p=_FakePipeProcess(_frame(oid,data)+_frame(oid,data))
        b=FailClosedGitBatch(process=p)
        try:
            self.assertEqual(b.read(oid),data)
            self.assertEqual(b.read(oid),data)
            self.assertEqual(b.completed_requests,2)
            self.assertFalse(b.retired)
        finally:b.close()
        self.assertTrue(b.retired)
        self.assertTrue(p.killed)

    def test_02_bad_header_fails_and_entire_session_retired(self):
        data=b"original"
        oid=_blob_oid(data)
        p=_FakePipeProcess(b"not-a-Git-header\n"+_frame(oid,data))
        b=FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):b.read(oid)
        self.assertTrue(p.killed)
        self.assertTrue(b.retired)
        with self.assertRaises(RuntimeError):b.read(oid)

    def test_03_wrong_object_type_retires_process(self):
        data=b"body"
        oid=_blob_oid(data)
        p=_FakePipeProcess(_frame(oid,data,header=oid+b" tree 4\n"))
        b=FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):b.read(oid)
        self.assertTrue(p.killed)
        self.assertEqual(b.completed_requests,0)

    def test_04_modified_content_rejected_and_session_poisoned(self):
        data=b"trusted"
        oid=_blob_oid(data)
        p=_FakePipeProcess(_frame(oid,b"mutated"))
        b=FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):b.read(oid)
        self.assertTrue(b.retired)
        self.assertTrue(p.killed)

    def test_05_truncated_body_rejected(self):
        data=b"full original body"
        oid=_blob_oid(data)
        p=_FakePipeProcess(oid+b" blob "+str(len(data)).encode()+b"\n"+b"short")
        b=FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):b.read(oid)
        self.assertTrue(b.retired)

    def test_06_invalid_terminator_retires(self):
        data=b"body"
        oid=_blob_oid(data)
        for trailer in (b"",b"\r",b"X"):
            with self.subTest(trailer=trailer):
                p=_FakePipeProcess(_frame(oid,data,trailer=trailer))
                b=FailClosedGitBatch(process=p)
                with self.assertRaises(RuntimeError):b.read(oid)
                self.assertTrue(p.killed)

    def test_07_dead_child_never_authorises_stale_bytes(self):
        data=b"body"
        oid=_blob_oid(data)
        p=_FakePipeProcess(_frame(oid,data),exitcode=9)
        b=FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):b.read(oid)
        self.assertTrue(b.retired)
        self.assertEqual(b.completed_requests,0)

    def test_08_bad_untrusted_request_kills_session_without_write(self):
        p=_FakePipeProcess()
        b=FailClosedGitBatch(process=p)
        with self.assertRaises(ValueError):b.read(b"Z"*40)
        self.assertTrue(b.retired)
        self.assertTrue(p.stdin.closed)  # invalid OID retired before any write
        with self.assertRaises(RuntimeError):b.read(b"a"*40)

    def test_09_stalled_pipe_deadline_enforced_and_child_killed(self):
        p=_FakePipeProcess(stalled=True)
        b=FailClosedGitBatch(timeout_seconds=0.05,process=p)
        start=time.monotonic()
        with self.assertRaises(TimeoutError):b.read(b"a"*40)
        elapsed=time.monotonic()-start
        self.assertLess(elapsed,1.0)
        self.assertTrue(p.killed)
        self.assertTrue(b.retired)
        with self.assertRaises(RuntimeError):b.read(b"a"*40)

    def test_10_no_deadline_change_or_resurrection_after_close(self):
        p=_FakePipeProcess()
        b=FailClosedGitBatch(timeout_seconds=0.05,process=p)
        b.close()
        b.close()
        self.assertTrue(p.killed)
        with self.assertRaises(RuntimeError):b.read(b"a"*40)
        for bad in (-1,0,0.001,21):
            with self.subTest(deadline=bad):
                with self.assertRaises(ValueError):
                    FailClosedGitBatch(timeout_seconds=bad,process=_FakePipeProcess())

    def test_11_cross_response_mixup_poisoned_after_wrong_oid(self):
        a=b"first"
        bdata=b"second"
        a_oid=_blob_oid(a)
        b_oid=_blob_oid(bdata)
        p=_FakePipeProcess(_frame(b_oid,bdata)+_frame(a_oid,a))
        subject=FailClosedGitBatch(process=p)
        with self.assertRaises(RuntimeError):subject.read(a_oid)
        self.assertTrue(subject.retired)
        with self.assertRaises(RuntimeError):subject.read(b_oid)

    def test_12_real_read_only_git_OID_payload_sha_equivalent(self):
        source="tests/phase8_byok_b_scope_migration.py"
        oid,_=old.object_at(BASE,source)
        b=FailClosedGitBatch(timeout_seconds=3)
        try:
            self.assertEqual(b.read(oid),git("show",BASE+":"+source))
            self.assertEqual(b.read(oid),git("show",BASE+":"+source))
            self.assertEqual(b.completed_requests,2)
        finally:b.close()


def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p182-fail-closed-transport"
    out.mkdir(parents=True,exist_ok=True)
    ledger={"checkpoint":"P182","historical_H":"HOLD",
        "current_C":"ISOLATED_BOUNDED_TRANSPORT_CANDIDATE_ONLY",
        "production_R":"HOLD","accepted_complete_full_product_Windows_runs":"0/3",
        "external_qualified_independent_security_decisions":REVIEWS,
        "privileged_C1_G0_to_G6":"OPEN","signed_code_integrity_GO":False,
        "P181_old_safety_findings_status":"OPEN_AWAITING_QUALIFIED_REVIEW",
        "historical_security_verifier_modified":False,
        "actual_product_integration_or_real_credentials":"NOT_ATTEMPTED"}
    good=False
    try:
        before=custody()
        ledger["source_before"]=before
        ledger["prior_authentic_original_P181_windows"]=authenticate_P181(
            os.environ.get("P182_ARCHIVE_TOKEN",""))
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for k in list(env):
            if (k in {"P182_ARCHIVE_TOKEN","GH_TOKEN","GITHUB_TOKEN"}
                or k.endswith("_API_KEY") or k.endswith("_SECRET")):
                env.pop(k,None)
        log=out/"p182_genuine_native_Windows_original_32_adversarial_cases.log"
        with log.open("wb") as f:
            run=subprocess.run(
                [sys.executable,"-B","-m","unittest","-v",
                 "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests",
                 "scripts.p181_windows_batch_transport_security_review.P181BatchAdversarialSecurityTests",
                 "scripts.p182_windows_fail_closed_batch_transport.P182FailClosedBatchSecurityCases"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                stdout=f,stderr=subprocess.STDOUT,timeout=95,check=False)
        raw=log.read_bytes()
        text=raw.decode("utf8","replace").replace("\r\n","\n")
        counts=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",text,re.M)
        ledger["genuine_Windows_combined_native_result"]={
            "real_process_exit":run.returncode,
            "original_P180_tests":8,"original_P181_tests":12,
            "new_P182_isolated_candidate_tests":12,
            "real_complete_unittest_count":int(counts[-1]) if counts else None,
            "original_complete_native_log_SHA256":sha(raw),
            "log_name":log.name,
            "named_FAIL_ERROR":re.findall(r"^(?:FAIL|ERROR): .+$",text,re.M)}
        if (run.returncode!=0 or counts!=["32"]
            or not re.search(r"^OK\s*$",text,re.M)):
            raise RuntimeError("P182 original plus candidate adversarial native Windows cases HOLD")
        ledger["source_after"]=custody()
        good=ledger["source_after"]==before
        if not good:raise RuntimeError("P182 original source custody drift")
        print("P182_TRUE_WINDOWS_32_NATIVE_CASES=32/32_PASS|OS_EXIT=0",flush=True)
        print("P182_NEW_CANDIDATE_BAD_HEADER_SESSION=RETIRED",flush=True)
        print("P182_NEW_CANDIDATE_STALLED_READ=TIMED_OUT_AND_PROCESS_KILLED",flush=True)
        print("P182_P180_P181_ORIGINAL_20_CASES=UNMODIFIED_AND_REEXECUTED",flush=True)
        print("P182_NATIVE_LOG_SHA256="+sha(raw),flush=True)
        print("P182_QUALIFIED_EXTERNAL_REVIEW=OPEN|FULL_NATIVE=0/3|RELEASE=HOLD",flush=True)
    except Exception as exc:
        ledger["collector_failure"]=repr(exc)
        print("P182_AUTHENTIC_NATIVE_SECURITY_CANDIDATE=HOLD|"+repr(exc),flush=True)
    finally:
        ledger["diagnostic_evidence_complete_not_a_release_security_approval"]=good
        (out/"p182_source_preserving_Windows_fail_closed_batch_candidate_ledger.json").write_text(
            json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
