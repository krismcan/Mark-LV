"""P180 Windows sealed blob transport equivalence — PROTOTYPE ONLY.

Compare unmodified real Git show SHA:path bytes against repeated fresh
Git cat-file --batch blob responses. No historical test monkeypatching,
no cache, no production verifier substitution. All seven independent
GO decisions and full-product regression 0/3 remain HOLD.

Read-only ephemeral hosted Windows run, exact Git source custody and
authenticated P179 original timed-out native case evidence. Candidate only.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
import zipfile

from scripts.p139_native_fs_verified_local_temp_root import _guard_runner
from scripts.p154_windows_authenticated_full_regression_ledger import _download_artifact

ROOT=Path(__file__).resolve().parents[1]
BASE="8e74b5c075c5bf110618c9cca6af7fdda39a56dd"
BRANCH="byok-c1-p180-sealed-blob-transport-equivalence-20261112"
NEW={
 ".github/workflows/p180-windows-sealed-blob-transport-equivalence.yml",
 "docs/byok-c1-p180-sealed-blob-transport-equivalence.md",
 "scripts/p180_windows_sealed_blob_transport_equivalence.py",
}
P179_ID=13979748295
P179_ZIP="B85BCB8B33DC979AEF805C2C7CCD4EDB1001F06B42A7A8CAFA7FDD23B9162BAB"
P179_PROFILE_SHA="7E00D86024F86A42AE9301187EAC4AC5CA8CF9C04B7BF0856F3D49D52CE19ECA"
P179_CONTROL_SHA="AA819DBBA4E5C291EF2FBFA8B34577F43622B2638051B8DDFC5F57343B21F3E4"
P179_HOTSPOT_LOG="p179_authentic_Windows_historical_seal_pin_witness.log"
P179_CONTROL_LOG="p179_authentic_Windows_original_uninstrumented_control.log"
P179_PROFILE_JSONL="p179_original_Git_invocation_profile_historical_seal_pin_witness.jsonl"
P179_LEDGER="p179_native_Windows_historical_Git_seal_profile_ledger.json"
HEX=re.compile(rb"^[0-9a-f]{40}$")
HEADER=re.compile(rb"^([0-9a-f]{40}) blob ([0-9]{1,8})\n$")
PATH_OK=re.compile(r"^((?:nayeon|tests)/[A-Za-z0-9_./-]+|scripts/[A-Za-z0-9_./-]+)$")
MAX_BLOB=2_000_000
ORIGINAL_PATHS=(
 "tests/phase_8_30_scope_migration.py",
 "tests/phase_8_34_scope_migration.py",
 "tests/phase_8_36_scope_migration.py",
 "tests/phase_8_37_scope_migration.py",
 "tests/phase8_byok_scope_migration.py",
 "tests/phase8_byok_b_scope_migration.py",
 "tests/test_phase8_byok_b_scope_integrity.py",
 "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
)
SOURCES=("9c47bac3308822e11300381017b30e913ffbc211",BASE)
REVIEWS={name:"OPEN" for name in
 ("GOV-01","GOV-02","SEC-03","SEC-04","REL-05","REL-06","REL-07")}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest().upper()

def git(*args:str)->bytes:
    return subprocess.run(["git","-C",str(ROOT),*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=35,check=True).stdout

def source_custody()->dict:
    _guard_runner()
    if (sys.platform!="win32" or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REF_NAME")!=BRANCH
        or git("rev-parse","HEAD").decode().strip()!=os.environ.get("GITHUB_SHA")
        or git("branch","--show-current").decode().strip()!=BRANCH
        or git("merge-base",BASE,"HEAD").decode().strip()!=BASE
        or git("status","--porcelain=v1").strip()):
        raise RuntimeError("P180 must run clean authenticated GitHub-hosted Windows exact push")
    changed=set(git("diff","--name-only",BASE,"HEAD").decode().splitlines())
    if changed!=NEW or any(git("ls-tree","--name-only",BASE,"--",p).strip() for p in NEW):
        raise RuntimeError("P180 only three additive diagnostic files authorized")
    if (git("rev-parse",BASE+":nayeon")!=git("rev-parse","HEAD:nayeon")
        or git("rev-parse",BASE+":tests")!=git("rev-parse","HEAD:tests")):
        raise RuntimeError("P180 original tests and product changed")
    tests=[p for p in git("ls-tree","-r","--name-only",BASE,"--","tests").decode().splitlines()
           if re.fullmatch(r"tests/test_[^/]+\.py",p)]
    if len(tests)!=171:
        raise RuntimeError("P180 old original 171 module inventory changed")
    for p in ORIGINAL_PATHS:
        if (ROOT/p).read_bytes()!=git("show",BASE+":"+p):
            raise RuntimeError("P180 original critical local security fixture drift "+p)
    if git("rev-parse","--show-object-format").decode().strip()!="sha1":
        raise RuntimeError("P180 protocol only supports Git SHA1 object format; fail closed")
    return {"authenticated_P180_head":git("rev-parse","HEAD").decode().strip(),
        "immutable_P179_parent":BASE,"only_three_new_audit_paths":sorted(NEW),
        "entire_nayeon_and_tests_subtrees_unmodified":True,
        "original_171_test_modules":171,"Git_object_format":"sha1"}

def authenticate_P179(token:str)->dict:
    if len(token)<8:raise RuntimeError("P180 ephemeral read-only artifact token required")
    raw=_download_artifact(P179_ID,P179_ZIP,token)
    if sha(raw)!=P179_ZIP:raise RuntimeError("P180 P179 ZIP SHA changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        expected={P179_PROFILE_LOG if False else P179_HOTSPOT_LOG,
                  P179_CONTROL_LOG,P179_PROFILE_JSONL,P179_LEDGER}
        if z.testzip() is not None or set(z.namelist())!=expected or len(z.namelist())!=4:
            raise RuntimeError("P180 P179 archived original Windows member CRC/inventory changed")
        p=json.loads(z.read(P179_LEDGER))
        hot=z.read(P179_HOTSPOT_LOG)
        ctrl=z.read(P179_CONTROL_LOG)
        prof=z.read(P179_PROFILE_JSONL)
        h=p.get("actual_instrumented_native_Windows_historical_hotspot",{})
        c=p.get("actual_bounded_native_Windows_control",{})
        if (p.get("checkpoint")!="P179"
            or p.get("historical_H")!="HOLD"
            or p.get("production_R")!="HOLD"
            or p.get("full_product_Windows_accepted")!="0/3"
            or p.get("GOV_SEC_REL_qualified_independent_decisions")!=REVIEWS
            or p.get("authentic_profile_evidence_captured_not_performance_fix") is not True
            or p.get("exact_source_before")!=p.get("exact_source_after")
            or p.get("exact_source_before",{}).get("P179_exact_triggered_head")!=BASE
            or h.get("disposition")!="TIMEOUT" or h.get("real_native_exit")!=124
            or h.get("unittest_count") is not None
            or h.get("complete_original_log_sha256")!=P179_PROFILE_SHA
            or h.get("profile_log_sha256")!=sha(prof)
            or c.get("disposition")!="PASS" or c.get("real_native_exit")!=0
            or c.get("complete_original_log_sha256")!=P179_CONTROL_SHA
            or sha(hot)!=P179_PROFILE_SHA or sha(ctrl)!=P179_CONTROL_SHA):
            raise RuntimeError("P180 P179 genuine original Windows logs/HCR/authentication drift")
        snapshots=[json.loads(line) for line in prof.decode("utf8").splitlines()]
        if not snapshots:
            raise RuntimeError("P180 no genuine P179 process timing observations")
        last=snapshots[-1]
        if (last.get("total_real_git_commands")!=3888
            or last.get("by_git_verb",{}).get("show",{}).get("calls")!=2391
            or last.get("by_git_verb",{}).get("cat-file",{}).get("calls")!=512
            or not any("test_each_historical_a_pin_remains_an_active_witness" in x
                       for x in hot.decode("utf8","replace").splitlines())
            or hot.count(b"Timeout (0:00:25)!")<4):
            raise RuntimeError("P180 original P179 expensive Git subprocess/historical test altered")
    return {"original_P179_artifact":P179_ID,"ZIP_SHA256":P179_ZIP,
        "original_native_130s_pin_witness_timeout_exit":124,
        "original_native_3888_real_Git_commands":3888,
        "original_native_2391_git_show_calls":2391,
        "original_original_tests_unwaived":True}

def valid_path(p:str)->bool:
    if not isinstance(p,str) or len(p)>240 or not PATH_OK.fullmatch(p):
        return False
    return (not p.startswith("/") and "\\" not in p and ":" not in p
            and not any(part in ("",".","..") or part.endswith((" ","."))
                        for part in p.split("/"))
            and all(ord(c)<128 for c in p))

def valid_oid(oid:bytes)->bool:
    return isinstance(oid,bytes) and HEX.fullmatch(oid) is not None

def validate_header(header:bytes,requested_oid:bytes)->int:
    if not valid_oid(requested_oid) or len(header)>100:
        raise ValueError("P180 request/header invalid")
    match=HEADER.fullmatch(header)
    if match is None or match.group(1)!=requested_oid:
        raise ValueError("P180 blob header OID/type/line mismatch")
    size=int(match.group(2))
    if size>MAX_BLOB:
        raise ValueError("P180 oversize blob response denied")
    return size

def verify_blob(oid:bytes,data:bytes,trailer:bytes)->bytes:
    if not valid_oid(oid) or not isinstance(data,bytes):
        raise ValueError("P180 malformed blob input denied")
    if len(data)>MAX_BLOB or trailer!=b"\n":
        raise ValueError("P180 incomplete blob/trailer denied")
    hashed=hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest().encode("ascii")
    if hashed!=oid:
        raise ValueError("P180 data/OID digest mismatch denied")
    return data

def object_at(commit:str,path:str)->tuple[bytes,bytes]:
    if not isinstance(commit,str) or not re.fullmatch(r"[0-9a-f]{40}",commit) or not valid_path(path):
        raise ValueError("P180 only exact pinned commit and safe canonical source path")
    raw=git("ls-tree",commit,"--",path)
    match=re.fullmatch(rb"100644 blob ([0-9a-f]{40})\t"+re.escape(path.encode("ascii"))+rb"\n",raw)
    if not match:
        raise ValueError("P180 exactly one ordinary regular Git blob required")
    return match.group(1),raw

class FreshGitBlobBatch:
    """One process, one independently verified response per request, NO caching."""
    def __init__(self):
        self.process=subprocess.Popen(["git","-C",str(ROOT),"cat-file","--batch"],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            cwd=ROOT)
        self.requests=0

    def read(self,oid:bytes)->bytes:
        if not valid_oid(oid):
            raise ValueError("P180 invalid OID never reaches Git child")
        p=self.process
        if p.poll() is not None or p.stdin is None or p.stdout is None:
            raise RuntimeError("P180 child not in live batch protocol state")
        p.stdin.write(oid+b"\n")
        p.stdin.flush()
        header=p.stdout.readline(110)
        size=validate_header(header,oid)
        data=bytearray()
        while len(data)<size:
            chunk=p.stdout.read(size-len(data))
            if not chunk:
                raise RuntimeError("P180 Git process truncated binary response")
            data.extend(chunk)
        trailer=p.stdout.read(1)
        verified=verify_blob(oid,bytes(data),trailer)
        self.requests+=1
        return verified

    def close(self):
        p=self.process
        if p.stdin:
            p.stdin.close()
        try:p.wait(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill();p.wait(timeout=3)
        if p.stdout:p.stdout.close()
        if p.stderr:p.stderr.close()

class P180SourceBoundAdversarialTests(unittest.TestCase):
    def test_01_regular_40_character_SHA_one_object(self):
        self.assertTrue(valid_oid(b"a"*40))
        self.assertFalse(valid_oid(b"A"*40))
        self.assertFalse(valid_oid(b"a"*39))
        self.assertFalse(valid_oid(b"a"*40+b"\n"))
        self.assertFalse(valid_oid(b"\xff"*40))

    def test_02_git_paths_reject_alias_traversal_meta_and_unicode(self):
        self.assertTrue(valid_path(ORIGINAL_PATHS[0]))
        for candidate in ("tests/../secret","tests\\x.py","tests/a//b",
                          "Tests/test.py","tests/.","tests/a.", "tests/a:alt",
                          "tests/a\nb","tests/é.py","tests/x"*100):
            with self.subTest(candidate=candidate):
                self.assertFalse(valid_path(candidate))

    def test_03_exact_binary_blob_header_rejects_mismatched_oid_and_type(self):
        oid=b"a"*40
        self.assertEqual(validate_header(oid+b" blob 5\n",oid),5)
        for header in (b"b"*40+b" blob 5\n",oid+b" tree 5\n",
                       oid+b" blob 5",oid+b" blob -1\n",oid+b" blob 2000001\n",
                       b"missing\n",oid+b" blob 5\nuntrusted"):
            with self.subTest(header=header):
                with self.assertRaises(ValueError):
                    validate_header(header,oid)

    def test_04_sha1_content_binding_and_trailer(self):
        contents=b"binary\x00contents\r\n"
        oid=hashlib.sha1(b"blob "+str(len(contents)).encode()+b"\0"+contents).hexdigest().encode()
        self.assertEqual(verify_blob(oid,contents,b"\n"),contents)
        for data,trailer in ((contents+b"tamper",b"\n"),(contents,b""),
                             (contents,b"\r"),(contents,b"\nextra")):
            with self.subTest(data=data,trailer=trailer):
                with self.assertRaises(ValueError):
                    verify_blob(oid,data,trailer)

    def test_05_actual_git_object_mode_and_immutable_source(self):
        oid,_=object_at(BASE,ORIGINAL_PATHS[0])
        self.assertTrue(valid_oid(oid))
        self.assertEqual(len(git("show",BASE+":"+ORIGINAL_PATHS[0])),
                         len((ROOT/ORIGINAL_PATHS[0]).read_bytes()))

    def test_06_exact_legacy_test_and_product_subtree_still_unmodified(self):
        self.assertEqual(git("rev-parse",BASE+":tests"),git("rev-parse","HEAD:tests"))
        self.assertEqual(git("rev-parse",BASE+":nayeon"),git("rev-parse","HEAD:nayeon"))

    def test_07_no_implicit_production_security_admission(self):
        from nayeon.desktop_alpha import frozen_signed_byok_companion as gate
        self.assertEqual(gate._APPROVED_MAIN_SHA256,"")
        self.assertEqual(gate._APPROVED_COMPANION_SHA256,"")
        self.assertEqual(gate._APPROVED_SIGNER_CERT_SHA256,"")
        self.assertFalse(gate._APPROVED_CODE_INTEGRITY_RELEASE)
        self.assertFalse(gate._release_pins_issued())

    def test_08_batch_never_caches_fresh_object_responses(self):
        oid,_=object_at(BASE,ORIGINAL_PATHS[1])
        with_batch=FreshGitBlobBatch()
        try:
            one=with_batch.read(oid)
            two=with_batch.read(oid)
            self.assertEqual(one,two)
            self.assertEqual(with_batch.requests,2)
            self.assertEqual(one,git("show",BASE+":"+ORIGINAL_PATHS[1]))
        finally:with_batch.close()

def benchmark()->dict:
    objects=[]
    for commit in SOURCES:
        for path in ORIGINAL_PATHS:
            try:oid,_=object_at(commit,path)
            except (ValueError,subprocess.CalledProcessError):continue
            objects.append((commit,path,oid))
    if len(objects)<9:
        raise RuntimeError("P180 insufficient true historical and current sealed Git objects")
    # 3 genuine independent fresh reads each: no file content is kept between
    # benchmark variants or Git requests. Compare every response to baseline.
    repeats=3
    direct_digests=[]
    baseline_start=time.monotonic()
    for rep in range(repeats):
        for commit,path,oid in objects:
            data=git("show",commit+":"+path)
            if hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest().encode()!=oid:
                raise RuntimeError("P180 original Git show raw returned unexpected object")
            direct_digests.append(sha(data))
    baseline_seconds=time.monotonic()-baseline_start
    batch=FreshGitBlobBatch()
    batch_digests=[]
    batch_start=time.monotonic()
    try:
        for rep in range(repeats):
            for commit,path,oid in objects:
                data=batch.read(oid)
                batch_digests.append(sha(data))
        requests=batch.requests
    finally:batch.close()
    batch_seconds=time.monotonic()-batch_start
    if (direct_digests!=batch_digests or requests!=len(objects)*repeats):
        raise RuntimeError("P180 unmodified Git show vs fresh batch mismatch")
    return {"real_Git_object_identifiers_per_cycle":len(objects),
        "three_real_fresh_cycles":repeats,
        "actual_original_git_show_calls":len(direct_digests),
        "actual_new_batch_requests_each_returned_and_rehashed":requests,
        "all_raw_SHA256_identical_in_original_call_order":True,
        "original_git_show_seconds":round(baseline_seconds,4),
        "candidate_Git_batch_seconds":round(batch_seconds,4),
        "candidate_to_original_elapsed_ratio":round(batch_seconds/baseline_seconds,4)
              if baseline_seconds>0 else None,
        "scope":"PROTOTYPE_READ_ONLY_SEALED_BLOB_TRANSPORT_ONLY_NOT_ACTUAL_TEST_OPTIMISATION"}

def main()->int:
    out=Path(os.environ["RUNNER_TEMP"])/"nayeon-p180-sealed-blob-equivalence"
    out.mkdir(parents=True,exist_ok=True)
    result={"checkpoint":"P180","historical_H":"HOLD",
        "current_C":"ISOLATED_PROTOTYPE_TRANSPORT_ONLY","production_R":"HOLD",
        "full_product_regression_Windows":"0/3","review_decisions":REVIEWS,
        "privileged_C1_G0_to_G6":"OPEN","production_companion_signed_CodeIntegrity_GO":False,
        "real_credentials_or_provider_network":"NOT_ATTEMPTED",
        "original_security_test_or_product_edited":False,
        "optimisation_accepted_into_product":False}
    good=False
    try:
        before=source_custody()
        result["original_source_before"]=before
        result["prior_genuine_P179_windows_archive"]=authenticate_P179(
            os.environ.get("P180_ARCHIVE_TOKEN",""))
        log=out/"p180_original_Windows_eight_adversarial_protocol_tests.log"
        env=os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"]="1"
        for k in list(env):
            if k in {"P180_ARCHIVE_TOKEN","GITHUB_TOKEN","GH_TOKEN"} or k.endswith("_API_KEY"):
                env.pop(k,None)
        with log.open("wb") as f:
            p=subprocess.run([sys.executable,"-B","-m","unittest","-v",
                "scripts.p180_windows_sealed_blob_transport_equivalence.P180SourceBoundAdversarialTests"],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,
                stderr=subprocess.STDOUT,timeout=85,check=False)
        raw=log.read_bytes()
        t=raw.decode("utf8","replace").replace("\r\n","\n")
        matches=re.findall(r"^Ran (\d+) tests? in [0-9.]+s$",t,re.M)
        result["genuine_Windows_eight_adversarial_protocol_tests"]={
            "real_process_exit":p.returncode,
            "complete_native_count":int(matches[-1]) if matches else None,
            "raw_log_sha256":sha(raw),
            "raw_log_filename":log.name,
            "failure_headings":re.findall(r"^(?:FAIL|ERROR): .+$",t,re.M)}
        if (p.returncode!=0 or matches!=["8"]
            or not re.search(r"^OK\s*$",t,re.M)):
            raise RuntimeError("P180 original native Windows eight candidate adversarial protocol tests failed")
        result["real_Git_SHA1_blob_equivalence_benchmark"]=benchmark()
        result["original_source_after"]=source_custody()
        good=(before==result["original_source_after"])
        if not good:raise RuntimeError("P180 source state drift after benchmark")
        print("P180_ACTUAL_WINDOWS_PROTOCOL_NEGATIVES=8/8|EXIT=0",flush=True)
        print("P180_ORIGINAL_UNMODIFIED_GIT_SHOW_EQUIVALENT_SHA256_EACH=" +
              str(result["real_Git_SHA1_blob_equivalence_benchmark"]["actual_original_git_show_calls"]),flush=True)
        print("P180_NATIVE_BENCHMARK="+json.dumps(result["real_Git_SHA1_blob_equivalence_benchmark"],
             sort_keys=True),flush=True)
        print("P180_PRIOR_P179_PROFILING_ARCHIVE=SHA256_AUTHENTIC",flush=True)
        print("P180_EXTERNAL_INDEPENDENT_REVIEW=SEVEN_OPEN|RELEASE=HOLD|FULL_NATIVE=0/3",flush=True)
    except Exception as exc:
        result["collector_error"]=repr(exc)
        print("P180_SOURCE_OR_WINDOWS_PROTOCOL_EVIDENCE=HOLD|"+repr(exc),flush=True)
    finally:
        result["source_bound_prototype_evidence_complete_NOT_product_recovery"]=good
        (out/"p180_authentic_Windows_sealed_blob_transport_prototype_ledger.json").write_text(
            json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
