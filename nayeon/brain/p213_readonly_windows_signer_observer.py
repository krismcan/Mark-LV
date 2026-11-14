"""P213: real Windows Authenticode read-only signed service admission OBSERVER.

Cannot sign, install, launch, authorise or deploy anything. It compares an
actual Windows Authenticode result and stable-looking filesystem observation,
then ALWAYS DENIES privileged Nayeon C1 installation. A Microsoft-signed OS
binary is NOT an approved Nayeon publisher or trusted local consent broker.

File stat/hash twice is NOT equivalent to a pinned kernel-loaded image, an
open handle FileIdInfo race defence or Windows Code Integrity enforcement.
No pinned production service/helper/installer images exist yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


# Never enroll from environment or an adjacent manifest. External human
# GOV/SEC/REL + protected signed build/release decision is still absent.
_APPROVED_SERVICE_SHA256=""
_APPROVED_SERVICE_SIGNER_SHA256=""
_APPROVED_INSTALLER_SHA256=""
_APPROVED_INSTALLER_SIGNER_SHA256=""
_APPROVED_LOCAL_CONSENT_SHA256=""
_APPROVED_LOCAL_CONSENT_SIGNER_SHA256=""
_APPROVED_CODE_INTEGRITY_POLICY_SHA256=""
_APPROVED_CODE_INTEGRITY_MACHINE_GO=False

_64HEX=re.compile(r"[0-9a-f]{64}\Z")
_MAX_READONLY_FILE=32*1024*1024

# File path is passed through a single isolated env variable, never expanded
# into script source. The Windows OS supplies Authenticode/catalog verdict.
# This is a read-only inspection and NOT image-load attestation or code policy.
_SIGNATURE_SCRIPT=r"""
$ErrorActionPreference='Stop'
$p=$env:NAYEON_P213_READONLY_FILE
if([string]::IsNullOrWhiteSpace($p)){exit 11}
$s=Get-AuthenticodeSignature -LiteralPath $p -ErrorAction Stop
if($null -eq $s){exit 12}
$cert=''
if($null -ne $s.SignerCertificate){
    $cert=$s.SignerCertificate.GetCertHashString('SHA256')
}
[Console]::Out.WriteLine(([string]$s.Status)+'|'+$cert)
"""


class P213SignatureStatus(str, Enum):
    VALID = "Valid"
    NOT_SIGNED = "NotSigned"
    UNKNOWN = "Unknown"


@dataclass(frozen=True, slots=True)
class P213WindowsSignatureObservation:
    status: P213SignatureStatus
    file_sha256: str | None
    signer_cert_sha256: str | None
    stable_stat_and_bytes_observed: bool
    platform_windows: bool
    elevated_service_identity_proven: bool=False
    approved_publisher_proven: bool=False
    protected_installer_accepted: bool=False
    kernel_code_integrity_load_enforced: bool=False
    release_eligible: bool=False
    real_key_admission: bool=False

    def __post_init__(self) -> None:
        if any((self.elevated_service_identity_proven,
                self.approved_publisher_proven,
                self.protected_installer_accepted,
                self.kernel_code_integrity_load_enforced,
                self.release_eligible,self.real_key_admission)):
            raise ValueError("P213 observation cannot mint signed-service authority")


def source_pins_unissued() -> bool:
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


def _ordinary_file(path: Path) -> bool:
    try:
        if not isinstance(path,Path) or not path.is_absolute():
            return False
        meta=path.lstat()
        if not stat.S_ISREG(meta.st_mode) or path.is_symlink():
            return False
        if getattr(meta,"st_file_attributes",0)&0x400:
            return False
        return 1024 <= meta.st_size <= _MAX_READONLY_FILE
    except (OSError,ValueError):
        return False


def _file_evidence(path:Path)->tuple[int,int,int,int,str] | None:
    try:
        if not _ordinary_file(path):
            return None
        s=path.stat()
        digest=hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                chunk=stream.read(1<<20)
                if not chunk:break
                digest.update(chunk)
        return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,digest.hexdigest())
    except (OSError,ValueError):
        return None


def _powershell_probe(path:Path)->tuple[P213SignatureStatus,str | None]:
    if sys.platform!="win32":
        return (P213SignatureStatus.UNKNOWN,None)
    root=os.environ.get("SystemRoot","")
    if not root:
        return (P213SignatureStatus.UNKNOWN,None)
    host=Path(root)/"System32"/"WindowsPowerShell"/"v1.0"/"powershell.exe"
    if not _ordinary_file(host):
        return (P213SignatureStatus.UNKNOWN,None)
    permitted=frozenset({
        "SYSTEMROOT","WINDIR","PATH","TEMP","TMP","USERPROFILE",
        "APPDATA","LOCALAPPDATA",
    })
    env={k:v for k,v in os.environ.items()
         if k.upper() in permitted and type(v) is str}
    env["NAYEON_P213_READONLY_FILE"]=str(path)
    try:
        p=subprocess.run(
            [str(host),"-NoLogo","-NoProfile","-NonInteractive",
             "-Command",_SIGNATURE_SCRIPT],
            env=env,shell=False,close_fds=True,
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=20,check=False)
        if p.returncode!=0 or p.stderr or len(p.stdout)>512:
            return (P213SignatureStatus.UNKNOWN,None)
        output=p.stdout.decode("ascii","strict").strip()
        if output.count("|")!=1:
            return (P213SignatureStatus.UNKNOWN,None)
        status,thumb=output.split("|")
        if status=="Valid" and _64HEX.fullmatch(thumb.lower()) is not None:
            return (P213SignatureStatus.VALID,thumb.lower())
        if status=="NotSigned" and thumb=="":
            return (P213SignatureStatus.NOT_SIGNED,None)
    except (OSError,UnicodeError,subprocess.SubprocessError,ValueError):
        return (P213SignatureStatus.UNKNOWN,None)
    return (P213SignatureStatus.UNKNOWN,None)


def observe_readonly_windows_signer(path:Path)->P213WindowsSignatureObservation:
    """Actual OS read-only inspection; no enrolled publisher GO is possible."""
    initial=_file_evidence(path)
    if sys.platform!="win32" or initial is None:
        return P213WindowsSignatureObservation(
            P213SignatureStatus.UNKNOWN,None,None,False,sys.platform=="win32")
    status,thumb=_powershell_probe(path)
    final=_file_evidence(path)
    stable=initial==final and final is not None
    if not stable:
        return P213WindowsSignatureObservation(
            P213SignatureStatus.UNKNOWN,None,None,False,True)
    return P213WindowsSignatureObservation(
        status,initial[-1],thumb,True,True)


def system_powershell_reference()->Path | None:
    if sys.platform!="win32":
        return None
    root=os.environ.get("SystemRoot","")
    if not root:return None
    p=Path(root)/"System32"/"WindowsPowerShell"/"v1.0"/"powershell.exe"
    return p if _ordinary_file(p) else None


def is_approved_nayeon_service(_observation:P213WindowsSignatureObservation)->bool:
    """P213 has no owner-issued trust root. ALL observations must be refused."""
    return False
