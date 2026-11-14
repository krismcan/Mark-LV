"""P202: fixed-owner historical BYOK-B gate bridge, dormant isolated candidate.

Not the production gate. This design forbids test-injected full-gate callbacks
in its public entrypoint, but subprocess interpreter/working-tree identity is
NOT OS-attested. There is no signed custom loader, verified session IPC, atomic
23-file snapshot or protected trust root. No credential or privilege use.
"""
from __future__ import annotations
from dataclasses import dataclass
import os, re, subprocess, sys
from pathlib import Path
from nayeon.brain.byok_b_ntfs_physical_admission_candidate import (
    PhysicalBAdmission, PhysicalAdmissionDenied,
    assert_isolated_original_b_with_ntfs_physical_guard,
)

FIXED_HISTORICAL_GATE_CODE = (
    "from tests import phase8_byok_b_scope_migration as b; "
    "print('P202_ORIGINAL_B_GATE_STATE='+b.assert_byok_b_integrity())"
)
STATE_LINE=re.compile(r"P202_ORIGINAL_B_GATE_STATE=(COMPLETE_UNSTAGED|EXACT_STAGED|EXACT_CHILD)\Z")

def parse_original_gate_response(code:int, text:str)->str:
    if type(code) is not int or code!=0:
        raise PhysicalAdmissionDenied("P202_ORIGINAL_GATE_NATIVE_EXIT_NONZERO")
    if type(text) is not str or len(text)>4096:
        raise PhysicalAdmissionDenied("P202_GATE_OUTPUT_MALFORMED_OR_OVERSIZE")
    # Accept exactly one native Windows CRLF or exact LF; never accept
    # duplicate lines, mixed newlines, trailing output or a bare CR.
    if text.endswith("\r\n") and text.count("\r\n")==1:
        content=text[:-2]
    elif text.endswith("\n") and "\r" not in text and text.count("\n")==1:
        content=text[:-1]
    else:
        raise PhysicalAdmissionDenied("P202_GATE_OUTPUT_UNEXPECTED_FRAMING")
    if "\r" in content or "\n" in content:
        raise PhysicalAdmissionDenied("P202_GATE_OUTPUT_UNEXPECTED_FRAMING")
    m=STATE_LINE.fullmatch(content)
    if m is None:
        raise PhysicalAdmissionDenied("P202_GATE_OUTPUT_NOT_EXACT_OR_AMBIGUOUS")
    return m.group(1)

@dataclass(frozen=True)
class FixedOwnerLabAdmission:
    historical_state:str
    physically_admitted_sources:int
    source_paths:tuple[str,...]
    integration_status:str="ISOLATED_P202_OWNER_BRIDGE_NOT_PHASE10"

class FixedHistoricalBGateOwner:
    """Original source-branch gate subprocess with a fixed command and cwd.

    The only purpose of this unprivileged adapter is to remove a caller-
    supplied gate callback from the *new* candidate entrypoint. The external
    Python interpreter and imported source are still untrusted if the host
    or source root is compromised. Do not use in production.
    """
    def __init__(self, root:Path):
        if os.name!="nt" or sys.platform!="win32":
            raise PhysicalAdmissionDenied("P202_NATIVE_WINDOWS_REQUIRED")
        if not isinstance(root,Path) or not root.is_absolute():
            raise PhysicalAdmissionDenied("P202_ABSOLUTE_ORIGINAL_ROOT_REQUIRED")
        runner=os.environ.get("RUNNER_TEMP")
        if not runner or not root.resolve().is_relative_to(Path(runner).resolve()):
            raise PhysicalAdmissionDenied("P202_ONLY_SELF_OWNED_WINDOWS_RUNNER_ROOT")
        self.root=root.resolve()

    def _native_git(self,*args:str)->str:
        proc=subprocess.run(["git","-C",str(self.root),*args],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=25,check=False)
        if proc.returncode!=0:
            raise PhysicalAdmissionDenied("P202_ORIGINAL_B_GIT_IDENTITY_UNAVAILABLE")
        return proc.stdout.decode("ascii","strict").strip()

    def _assert_legacy_branch(self)->None:
        from tests import phase8_byok_b_scope_migration as B
        if (self._native_git("rev-parse","HEAD") != B.PARENT or
            self._native_git("branch","--show-current")!="nayeon-v1"):
            raise PhysicalAdmissionDenied("P202_ORIGINAL_A_PARENT_OR_BRANCH_MISMATCH")
        # B candidate is exact original frozen 23-pin manifest; the inherited
        # P201 gate also independently checks all original 23 sealed digests.
        if len(B.CANDIDATE_SHA256)!=23:
            raise PhysicalAdmissionDenied("P202_HISTORICAL_B_PIN_COUNT_CHANGED")

    def __call__(self)->str:
        self._assert_legacy_branch()
        env=os.environ.copy()
        for key in list(env):
            if (key in {"GITHUB_TOKEN","GH_TOKEN","P202_ARCHIVE_TOKEN",
                        "P201_ARCHIVE_TOKEN"} or
                key.endswith(("_API_KEY","_SECRET"))):
                env.pop(key,None)
        env.pop("PYTHONPATH",None)
        env["PYTHONDONTWRITEBYTECODE"]="1"
        env["PYTHONNOUSERSITE"]="1"
        try:
            proc=subprocess.run(
                [sys.executable,"-B","-c",FIXED_HISTORICAL_GATE_CODE],
                cwd=self.root,env=env,stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                timeout=100,check=False)
        except (subprocess.TimeoutExpired,OSError) as exc:
            raise PhysicalAdmissionDenied("P202_FIXED_FULL_GATE_PROCESS_UNAVAILABLE") from exc
        if proc.returncode!=0:
            raise PhysicalAdmissionDenied("P202_FIXED_FULL_ORIGINAL_B_GATE_DENIED")
        try:
            state=parse_original_gate_response(proc.returncode,
                     proc.stdout.decode("utf8","strict"))
        except UnicodeError as exc:
            raise PhysicalAdmissionDenied("P202_FIXED_GATE_OUTPUT_NOT_UTF8") from exc
        self._assert_legacy_branch()
        return state

def admit_isolated_fixed_owner_original_b(root:Path)->FixedOwnerLabAdmission:
    """No user-supplied historical_gate parameter. Not Phase 10 public gate."""
    gate=FixedHistoricalBGateOwner(root)
    try:
        result=assert_isolated_original_b_with_ntfs_physical_guard(
            gate.root,historical_gate=gate)
    except PhysicalAdmissionDenied:
        raise
    except BaseException as exc:
        raise PhysicalAdmissionDenied("P202_NO_FALLBACK_ON_BRIDGE_ERROR") from exc
    if type(result) is not PhysicalBAdmission or result.admitted_source_count!=23:
        raise PhysicalAdmissionDenied("P202_23_PIN_CUSTODY_RESULT_INVALID")
    gate._assert_legacy_branch()
    return FixedOwnerLabAdmission(
        historical_state=result.historical_gate_state,
        physically_admitted_sources=result.admitted_source_count,
        source_paths=result.original_b_pins,
    )
