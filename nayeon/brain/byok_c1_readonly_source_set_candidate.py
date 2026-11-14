"""P204 isolated read-only exact-byte Windows source-set observation candidate.

NO admission capability, trusted signer, manifest authority, atomic snapshot,
service dispatch, credential operations, or public Phase10 integration.
The caller's pin map is UNTRUSTED unless separately authenticated. A verified
set returned here only describes one sequence of independently inspected files.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import sys
from types import MappingProxyType
from typing import Mapping

class SourceSetRefused(RuntimeError):pass

@dataclass(frozen=True)
class SourceObservation:
    relative_path:str
    data:bytes
    sha256:str
    volume:int
    fileid:bytes
    # Does not grant a one-use authority or preserve an open handle.
    trust_status:str="OBSERVED_WITH_UNTRUSTED_CALLER_PIN_NOT_ADMITTED"

@dataclass(frozen=True)
class SourceSetObservation:
    items:tuple[SourceObservation,...]
    trust_status:str="NONATOMIC_SEQUENTIAL_READ_ONLY_OBSERVATION_NOT_ADMISSION"

def _canonical_source_path(path:str)->bool:
    if type(path) is not str or len(path)>256 or not path or path[0] in (".","/","\\"):
        return False
    if "\\" in path or ":" in path or "//" in path or "\x00" in path:
        return False
    bits=path.split("/")
    return len(bits)>1 and all(
        p not in ("",".","..") and re.fullmatch(r"[A-Za-z0-9._-]+",p)
        for p in bits
    )

class WindowsReadOnlySourceSetProbe:
    """P190 HANDLE physical observations, no release/consent or snapshot GO.

    This class does not authenticate caller-provided pins. There is no source
    root trust enrollment or code execution. Each file handle is exclusive
    only during its own read. All handles close before returning observations.
    A future trusted service MUST independently authenticate the pin manifest,
    root, ancestors, source set identity, epoch and executable consumer.
    """
    def __init__(self,root:Path,max_single_bytes:int=1048576,max_total_bytes:int=2097152):
        if os.name!="nt" or sys.platform!="win32":
            raise SourceSetRefused("P204_GENUINE_WINDOWS_ONLY")
        if not isinstance(root,Path) or not root.is_absolute():
            raise SourceSetRefused("P204_ABSOLUTE_ROOT_REQUIRED")
        if (type(max_single_bytes) is not int or type(max_total_bytes) is not int or
            max_single_bytes<1 or max_single_bytes>1048576 or
            max_total_bytes<max_single_bytes or max_total_bytes>2097152):
            raise SourceSetRefused("P204_SOURCE_BOUNDS_INVALID")
        from scripts.p190_windows_handle_bound_source_probe import Win32HandleBoundSourceProbe
        self.root=root
        self.max_total_bytes=max_total_bytes
        self.probe=Win32HandleBoundSourceProbe(root,max_bytes=max_single_bytes)

    def inspect_untrusted_pin_set(self,pins:Mapping[str,str])->SourceSetObservation:
        if not isinstance(pins,Mapping) or type(pins) is dict and len(pins)>23:
            raise SourceSetRefused("P204_SOURCE_MANIFEST_INVALID")
        try:
            rows=list(pins.items())
        except Exception as exc:
            raise SourceSetRefused("P204_UNREADABLE_PIN_MAP") from exc
        if not 1<=len(rows)<=23:
            raise SourceSetRefused("P204_REQUIRES_BOUNDED_EXACT_SOURCE_INVENTORY")
        if any(not _canonical_source_path(k) or
               type(v) is not str or not re.fullmatch(r"[A-F0-9]{64}",v)
               for k,v in rows):
            raise SourceSetRefused("P204_NONCANONICAL_PATH_OR_PIN")
        if len(set(k for k,_ in rows))!=len(rows):
            raise SourceSetRefused("P204_DUPLICATE_PATH")
        observed=[]
        total=0
        for relative,expected in sorted(rows):
            full=self.root.joinpath(*relative.split("/"))
            h=None
            try:
                before=self.probe._parent_identity(full)
                h=self.probe._open(full)
                identity=self.probe._handle_identity(h,full)
                data=self.probe._read_handle(h)
                after=self.probe._handle_identity(h,full)
                if identity!=after or before!=self.probe._parent_identity(full):
                    raise SourceSetRefused("P204_PATH_PARENT_OR_FILEID_DRIFT")
                if hashlib.sha256(data).hexdigest().upper()!=expected:
                    raise SourceSetRefused("P204_ORIGINAL_PIN_MISMATCH")
                total+=len(data)
                if total>self.max_total_bytes:
                    raise SourceSetRefused("P204_SOURCE_SET_TOTAL_SIZE_LIMIT")
                observed.append(SourceObservation(relative,data,expected,identity[0],identity[1]))
            except SourceSetRefused:
                raise
            except BaseException as exc:
                raise SourceSetRefused("P204_WIN32_PHYSICAL_SOURCE_REFUSED:"+
                    type(exc).__name__+":"+str(exc)[:160]) from exc
            finally:
                if h is not None:self.probe.api.CloseHandle(h)
        return SourceSetObservation(tuple(observed))
