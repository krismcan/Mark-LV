"""P213 read-only genuine native Windows WinVerifyTrust observation.

Calls an isolated TEST-ASSEMBLY executable compiled with genuine original
P116 WinVerifyTrust (opened file handle, cache-only revocation). Does not
invoke PowerShell modules or install/sign/run a service/credential actor.

OS accept/reject is a file-policy observation, not proof of approved
Nayeon publisher, loaded image trust or intent by a human. No reviewer
signature/production installer or machine Code Integrity policy exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys


_APPROVED_SERVICE_SHA256=""
_APPROVED_SERVICE_SIGNER_SHA256=""
_APPROVED_INSTALLER_SHA256=""
_APPROVED_INSTALLER_SIGNER_SHA256=""
_APPROVED_LOCAL_CONSENT_SHA256=""
_APPROVED_LOCAL_CONSENT_SIGNER_SHA256=""
_APPROVED_CODE_INTEGRITY_POLICY_SHA256=""
_APPROVED_CODE_INTEGRITY_MACHINE_GO=False
_MAX_READONLY_FILE=32*1024*1024


class P213SignatureStatus(str, Enum):
    OS_POLICY_ACCEPTED_UNPINNED="NativePolicyAcceptedButUnpinned"
    OS_POLICY_REJECTED="NativePolicyRejected"
    UNKNOWN="Unavailable"


@dataclass(frozen=True, slots=True)
class P213WindowsSignatureObservation:
    status:P213SignatureStatus
    file_sha256:str | None
    signer_cert_sha256:str | None
    stable_stat_and_bytes_observed:bool
    platform_windows:bool
    elevated_service_identity_proven:bool=False
    approved_publisher_proven:bool=False
    protected_installer_accepted:bool=False
    kernel_code_integrity_load_enforced:bool=False
    release_eligible:bool=False
    real_key_admission:bool=False

    def __post_init__(self)->None:
        if any((self.elevated_service_identity_proven,
                self.approved_publisher_proven,
                self.protected_installer_accepted,
                self.kernel_code_integrity_load_enforced,
                self.release_eligible,self.real_key_admission)):
            raise ValueError("P213 read-only file observation cannot mint authority")


def source_pins_unissued()->bool:
    return (
        _APPROVED_SERVICE_SHA256==""
        and _APPROVED_SERVICE_SIGNER_SHA256==""
        and _APPROVED_INSTALLER_SHA256==""
        and _APPROVED_INSTALLER_SIGNER_SHA256==""
        and _APPROVED_LOCAL_CONSENT_SHA256==""
        and _APPROVED_LOCAL_CONSENT_SIGNER_SHA256==""
        and _APPROVED_CODE_INTEGRITY_POLICY_SHA256==""
        and _APPROVED_CODE_INTEGRITY_MACHINE_GO is False
    )


def _ordinary_file(path:Path)->bool:
    try:
        if not isinstance(path,Path) or not path.is_absolute():return False
        s=path.lstat()
        if not stat.S_ISREG(s.st_mode) or path.is_symlink():return False
        if getattr(s,"st_file_attributes",0)&0x400:return False
        return 1024<=s.st_size<=_MAX_READONLY_FILE
    except (OSError,ValueError):
        return False


def _file_evidence(path:Path)->tuple[int,int,int,int,str] | None:
    try:
        if not _ordinary_file(path):return None
        s=path.stat()
        h=hashlib.sha256()
        with path.open("rb") as f:
            while True:
                b=f.read(1<<20)
                if not b:break
                h.update(b)
        return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,h.hexdigest())
    except (OSError,ValueError):
        return None


def _native_wintrust_probe(path:Path)->P213SignatureStatus:
    if sys.platform!="win32":return P213SignatureStatus.UNKNOWN
    name=os.environ.get("P213_NATIVE_WINTRUST_EXE","")
    if not name:return P213SignatureStatus.UNKNOWN
    executable=Path(name)
    if not _ordinary_file(executable) or executable.suffix.lower()!=".exe":
        return P213SignatureStatus.UNKNOWN
    # Only inert path metadata to the no-effect test assembly. Environment
    # excludes arbitrary provider keys, tokens and Python import injection.
    allowed=frozenset({
      "SYSTEMROOT","WINDIR","SYSTEMDRIVE","PATH","PATHEXT","COMSPEC",
      "TEMP","TMP","USERPROFILE","HOMEDRIVE","HOMEPATH",
      "APPDATA","LOCALAPPDATA","PROGRAMDATA","PROGRAMFILES",
      "PROGRAMFILES(X86)","COMMONPROGRAMFILES","OS",
    })
    env={k:v for k,v in os.environ.items()
         if k.upper() in allowed and type(v) is str}
    try:
        p=subprocess.run([str(executable),str(path)],cwd=executable.parent,
            env=env,shell=False,close_fds=True,
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=30,check=False)
        if p.returncode!=0 or p.stderr or len(p.stdout)>512:
            return P213SignatureStatus.UNKNOWN
        lines=p.stdout.decode("ascii","strict").replace("\r\n","\n").splitlines()
        if len(lines)!=6 or lines[1:]!=[
            "P213_APPROVED_PUBLISHER=false",
            "P213_SERVICE_IMAGE_BOUND=false",
            "P213_HUMAN_CONSENT=false",
            "P213_REAL_KEY=false",
            "P213_RELEASE=false",
        ]:return P213SignatureStatus.UNKNOWN
        tag="P213_NATIVE_WINTRUST="
        if not lines[0].startswith(tag):return P213SignatureStatus.UNKNOWN
        status=lines[0][len(tag):]
        if status==P213SignatureStatus.OS_POLICY_ACCEPTED_UNPINNED.value:
            return P213SignatureStatus.OS_POLICY_ACCEPTED_UNPINNED
        if status==P213SignatureStatus.OS_POLICY_REJECTED.value:
            return P213SignatureStatus.OS_POLICY_REJECTED
    except (OSError,UnicodeError,subprocess.SubprocessError,ValueError):
        pass
    return P213SignatureStatus.UNKNOWN


def observe_readonly_windows_signer(path:Path)->P213WindowsSignatureObservation:
    """Actual native P116 OS WinVerifyTrust observed under Windows CI."""
    initial=_file_evidence(path)
    if sys.platform!="win32" or initial is None:
        return P213WindowsSignatureObservation(
            P213SignatureStatus.UNKNOWN,None,None,False,sys.platform=="win32")
    status=_native_wintrust_probe(path)
    final=_file_evidence(path)
    stable=initial==final and final is not None
    if not stable:
        return P213WindowsSignatureObservation(
            P213SignatureStatus.UNKNOWN,None,None,False,True)
    # Native P116 reports file-policy status but deliberately does NOT
    # extract/enroll a signer certificate, loaded image or local consent.
    return P213WindowsSignatureObservation(status,initial[-1],None,True,True)


def system_powershell_reference()->Path | None:
    if sys.platform!="win32":return None
    root=os.environ.get("SystemRoot","")
    if not root:return None
    path=Path(root)/"System32"/"WindowsPowerShell"/"v1.0"/"powershell.exe"
    return path if _ordinary_file(path) else None


def is_approved_nayeon_service(_observation:P213WindowsSignatureObservation)->bool:
    """Always NO: no approved service publisher, signer or machine policy."""
    return False
