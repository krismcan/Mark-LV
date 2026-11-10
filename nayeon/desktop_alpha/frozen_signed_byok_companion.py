"""P140 — fail-closed installed Windows SIGNED companion selection.

The P133 source-only launcher remains unchanged in its safety properties.
For a FROZEN desktop, a separate local BYOK executable is never launched
without *embedded release-time pins* for BOTH parent and helper binaries,
a common independently approved publisher certificate, and Windows
Authenticode validation. No release signing authority/pins have been issued:
the immutable defaults below are empty. Consequently the production
frozen path currently ALWAYS REFUSES. Merely copying a bundled .exe next
to the desktop never makes it trusted.

This is an architecture and non-operational admission gate, NOT a
replacement for a qualified reviewer, code signing, WDAC/SAC inspection,
TOCTOU-resistant installed-file controls or actual user presence.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


# Deliberately NEVER populated by environment, adjacent configuration files
# or runtime model instructions. Must be set only in a separately reviewed,
# publisher-signed immutable release tree after authorising the signer,
# complete installer and Windows Code Integrity policy. P140 stays blocked.
_APPROVED_MAIN_SHA256 = ""
_APPROVED_COMPANION_SHA256 = ""
_APPROVED_SIGNER_CERT_SHA256 = ""
_APPROVED_CODE_INTEGRITY_RELEASE = False

_FIXED_COMPANION = "NayeonLocalByokOffline.exe"
_64_LOWER_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MAX_EXE_BYTES = 128 * 1024 * 1024

# No environment values are ever interpolated into PowerShell commands.
# Signature verification is read-only and reports only fixed public fields.
# This is NOT a signed output or defence against untrusted script host.
_SIGNATURE_PROBE_SCRIPT = r"""
$ErrorActionPreference='Stop'
$p=$env:NAYEON_P140_SIGNATURE_FILE
if([string]::IsNullOrWhiteSpace($p)) {exit 6}
$s=Get-AuthenticodeSignature -LiteralPath $p
if($null -eq $s -or $s.Status -ne 'Valid' -or
   $null -eq $s.SignerCertificate) {exit 7}
$hash=$s.SignerCertificate.GetCertHashString('SHA256')
if($hash -notmatch '^[A-Fa-f0-9]{64}$') {exit 8}
[Console]::Out.WriteLine($hash.ToLowerInvariant())
"""


def _release_pins_issued() -> bool:
    return (
        _APPROVED_CODE_INTEGRITY_RELEASE is True
        and all(
            type(value) is str and _64_LOWER_HEX.fullmatch(value) is not None
            for value in (
                _APPROVED_MAIN_SHA256,
                _APPROVED_COMPANION_SHA256,
                _APPROVED_SIGNER_CERT_SHA256,
            )
        )
    )


def _ordinary_executable(path: Path) -> bool:
    """Require a directly opened local regular file, not a reparse point.

    This check alone does not defeat rename/replacement races; release
    policy must separately enforce signed image identity at load time.
    """
    try:
        meta = path.lstat()
    except (OSError, ValueError):
        return False
    if not stat.S_ISREG(meta.st_mode) or path.is_symlink():
        return False
    if getattr(meta, "st_file_attributes", 0) & 0x400:
        return False
    if meta.st_size < 1024 or meta.st_size > _MAX_EXE_BYTES:
        return False
    return True


def _hex_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        return digest.hexdigest()
    except (OSError, ValueError):
        return None


def _trusted_authenticode_signer(path: Path) -> str | None:
    """Ask the Windows OS for Authenticode status; no shell expansion.

    This *inspection* is not an official signature/release decision.
    On real release the policy owner also must independently attest that
    Smart App Control / WDAC enforces these signed images upon load.
    """
    if sys.platform != "win32":
        return None
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    if type(system_root) is not str or not Path(system_root).is_absolute():
        return None
    host = (Path(system_root) / "System32" / "WindowsPowerShell"
            / "v1.0" / "powershell.exe")
    if not _ordinary_executable(host):
        return None

    # Avoid inheriting provider API keys and arbitrary Python execution vars.
    allowed = ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP",
               "USERPROFILE", "APPDATA", "LOCALAPPDATA")
    env = {
        key: value for key, value in os.environ.items()
        if key.upper() in {p.upper() for p in allowed}
        and type(value) is str
    }
    env["NAYEON_P140_SIGNATURE_FILE"] = str(path)
    try:
        result = subprocess.run(
            [str(host), "-NoLogo", "-NoProfile", "-NonInteractive",
             "-Command", _SIGNATURE_PROBE_SCRIPT],
            capture_output=True, text=True, shell=False,
            stdin=subprocess.DEVNULL, close_fds=True,
            timeout=12, env=env, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    signature = result.stdout.strip().lower()
    if (result.returncode != 0
            or _64_LOWER_HEX.fullmatch(signature) is None):
        return None
    return signature


def approved_frozen_local_byok_companion() -> Path | None:
    """Return *only* a fully pinned signed sidecar, else no launch path.

    This must never be used as the only security control. System App
    Control or WDAC must authenticate the image at actual process launch.
    P140 has NO release authority, so this returns None in all real runs.
    """
    if (sys.platform != "win32"
            or getattr(sys, "frozen", False) is not True
            or not _release_pins_issued()):
        return None
    try:
        exe = Path(sys.executable)
        if not exe.is_absolute() or exe.name.lower() != "nayeondesktop.exe":
            return None
        folder = exe.parent
        # A local writable junction or substituted parent is outside this
        # provisional trust model and must refuse.
        if folder.is_symlink() or (
            getattr(folder.lstat(), "st_file_attributes", 0) & 0x400
        ):
            return None
        companion = folder / _FIXED_COMPANION
        if not _ordinary_executable(exe) or not _ordinary_executable(companion):
            return None
        if _hex_sha256(exe) != _APPROVED_MAIN_SHA256:
            return None
        if _hex_sha256(companion) != _APPROVED_COMPANION_SHA256:
            return None
        if _trusted_authenticode_signer(exe) != _APPROVED_SIGNER_CERT_SHA256:
            return None
        if _trusted_authenticode_signer(companion) != _APPROVED_SIGNER_CERT_SHA256:
            return None
        return companion
    except (OSError, RuntimeError, ValueError):
        return None
