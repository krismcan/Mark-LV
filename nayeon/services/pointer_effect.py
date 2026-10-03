"""Private bounded Windows input insertion; no target or approval authority."""
import ctypes
from dataclasses import dataclass
from enum import Enum
import sys

from nayeon.services.pointer_coordinates import _CoordinateEvidence, _LocalOnly

__all__ = ()


class _EffectStatus(Enum):
    NOT_ATTEMPTED = "not_attempted"
    INSERTED = "inserted"
    PARTIAL = "partial"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True, repr=False)
class _PointerEffectReceipt(_LocalOnly):
    """API insertion only. Never proof of delivery or semantic UI success."""
    status: _EffectStatus = _EffectStatus.NOT_ATTEMPTED
    attempted: bool = False
    inserted: int | None = None

    def __post_init__(self):
        if (type(self) is not _PointerEffectReceipt
                or type(self.status) is not _EffectStatus
                or type(self.attempted) is not bool):
            raise TypeError("Exact private effect receipt required.")
        if self.inserted is not None and (
                type(self.inserted) is not int or not 0 <= self.inserted <= 3):
            raise ValueError("Invalid native insertion count.")
        expected = (
            _EffectStatus.NOT_ATTEMPTED if not self.attempted
            else _EffectStatus.INSERTED if self.inserted == 3
            else _EffectStatus.PARTIAL if self.inserted in (1, 2)
            else _EffectStatus.INDETERMINATE
        )
        if self.status is not expected or (not self.attempted and self.inserted is not None):
            raise ValueError("Inconsistent effect receipt.")


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_int32), ("dy", ctypes.c_int32),
        ("mouseData", ctypes.c_uint32), ("dwFlags", ctypes.c_uint32),
        ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUTUNION(ctypes.Union):
    # MOUSEINPUT is the largest INPUT union member on both Windows ABIs.
    # No keyboard/hardware construction or alternate effect is provided.
    _fields_ = [("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("data", _INPUTUNION)]


def _records(evidence):
    if type(evidence) is not _CoordinateEvidence:
        raise TypeError("Exact private coordinate evidence required.")
    evidence.__post_init__()
    if (ctypes.sizeof(ctypes.c_void_p) not in (4, 8)
            or ctypes.sizeof(_INPUT) != (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)):
        raise ValueError("Unsupported Windows input layout.")
    records = (_INPUT * 3)()  # All unused fields and union padding start at zero.
    records[0].data.mi.dx = evidence.normalized_x
    records[0].data.mi.dy = evidence.normalized_y
    for record, flags in zip(records, (0x0001 | 0x8000 | 0x4000, 0x0002, 0x0004)):
        record.type = 0  # INPUT_MOUSE
        record.data.mi.dwFlags = flags
    return records


@dataclass(frozen=True, slots=True, repr=False, init=False)
class _PointerEffectNative(_LocalOnly):
    _send: object

    def __init__(self):
        if type(self) is not _PointerEffectNative:
            raise TypeError("Exact private native facade required.")
        if sys.platform != "win32":
            raise OSError("Windows pointer insertion unavailable.")
        object.__setattr__(self, "_send", ctypes.WinDLL("user32").SendInput)
        self._send.argtypes = [ctypes.c_uint32, ctypes.POINTER(_INPUT), ctypes.c_int]
        self._send.restype = ctypes.c_uint32

    def _send_input(self, count, records, size):
        return self._send(count, records, size)


@dataclass(frozen=True, slots=True, repr=False, init=False)
class _PointerEffectService(_LocalOnly):
    """Trusted injected seam; one batch, one call, never a retry or cleanup input."""
    _native: object
    _platform: str

    def __init__(self, *, native=None, platform=None):
        if type(self) is not _PointerEffectService:
            raise TypeError("Exact private effect service required.")
        object.__setattr__(self, "_native", native)
        object.__setattr__(self, "_platform", sys.platform if platform is None else platform)

    def _insert(self, evidence):
        try:
            if (type(self) is not _PointerEffectService
                    or type(self._platform) is not str or self._platform != "win32"):
                return _PointerEffectReceipt()
            records = _records(evidence)
            native = self._native if self._native is not None else _PointerEffectNative()
        except Exception:
            return _PointerEffectReceipt()
        try:
            inserted = native._send_input(3, records, ctypes.sizeof(_INPUT))
            if type(inserted) is not int or not 0 <= inserted <= 3:
                inserted = None
        except Exception:
            inserted = None
        status = (_EffectStatus.INSERTED if inserted == 3 else
                  _EffectStatus.PARTIAL if inserted in (1, 2) else
                  _EffectStatus.INDETERMINATE)
        return _PointerEffectReceipt(status, True, inserted)
