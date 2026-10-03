"""Private bounded UIA sample; descriptive evidence only, no execution route."""
import ctypes
from dataclasses import dataclass
import sys
import threading

from nayeon.services.computer_control import _Redacted
from nayeon.services.pointer_hit_validation import _ProposedPoint
from nayeon.verification.contract import VerificationStatus

__all__ = ()

# UIA_ButtonControlTypeId through UIA_AppBarControlTypeId, explicitly reviewed.
_CONTROL_TYPES = frozenset((
    50000, 50001, 50002, 50003, 50004, 50005, 50006, 50007, 50008, 50009,
    50010, 50011, 50012, 50013, 50014, 50015, 50016, 50017, 50018, 50019,
    50020, 50021, 50022, 50023, 50024, 50025, 50026, 50027, 50028, 50029,
    50030, 50031, 50032, 50033, 50034, 50035, 50036, 50037, 50038, 50039,
    50040,
))


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private UIA state cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private UIA state cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private UIA state cannot be serialized or copied.")


def _point_snapshot(point):
    if type(point) is not _ProposedPoint:
        raise TypeError("Exact private point required.")
    _ProposedPoint.__post_init__(point)
    return point.x, point.y


def _sample_valid(control_type, enabled):
    if type(control_type) is not int or control_type not in _CONTROL_TYPES:
        raise ValueError("Reviewed exact control type required.")
    if type(enabled) is not bool:
        raise TypeError("Exact enabled state required.")


@dataclass(frozen=True, slots=True, repr=False)
class _UIElementEvidence(_LocalOnly):
    point: _ProposedPoint
    control_type: int
    enabled: bool

    def __post_init__(self):
        if type(self) is not _UIElementEvidence:
            raise TypeError("Exact private evidence required.")
        _point_snapshot(self.point)
        _sample_valid(self.control_type, self.enabled)


@dataclass(frozen=True, slots=True, repr=False)
class _UIElementResult(_LocalOnly):
    status: VerificationStatus = VerificationStatus.INDETERMINATE
    evidence: _UIElementEvidence | None = None

    def __post_init__(self):
        if type(self) is not _UIElementResult or type(self.status) is not VerificationStatus:
            raise TypeError("Exact private result required.")
        if self.status is VerificationStatus.VERIFIED:
            if type(self.evidence) is not _UIElementEvidence:
                raise TypeError("Complete private evidence required.")
            _UIElementEvidence.__post_init__(self.evidence)
        elif self.status is not VerificationStatus.INDETERMINATE or self.evidence is not None:
            raise ValueError("Unavailable sample must carry no evidence.")


class _GUID(ctypes.Structure):
    _fields_ = [("a", ctypes.c_uint32), ("b", ctypes.c_uint16),
                ("c", ctypes.c_uint16), ("d", ctypes.c_ubyte * 8)]


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int32), ("y", ctypes.c_int32)]


# CLSID_CUIAutomation / IID_IUIAutomation. No type-library generation/import.
_CLSID = _GUID(0xff48dba4, 0x60ef, 0x4201,
               (ctypes.c_ubyte * 8)(0xaa, 0x87, 0x54, 0x10, 0x3e, 0xef, 0x59, 0x4e))
_IID = _GUID(0x30cbe57d, 0xd9d0, 0x452a,
             (ctypes.c_ubyte * 8)(0xab, 0x13, 0x7a, 0xc5, 0xac, 0x48, 0x25, 0xee))


class _UIANative(_LocalOnly):
    """One owning MTA thread; only the four required COM vtable slots bound.

    IUIAutomation: ElementFromPoint=7. IUIAutomationElement:
    CurrentControlType=21, CurrentIsEnabled=28. IUnknown: Release=2.
    HRESULT is signed 32-bit; enabled is Windows BOOL, not VARIANT_BOOL.
    """
    __slots__ = ("_owner", "_ole", "_initialized", "_automation", "_element")

    def __init__(self):
        if sys.platform != "win32" or not hasattr(ctypes, "WINFUNCTYPE"):
            raise OSError("Private UIA support unavailable.")
        self._owner = threading.get_ident()
        self._initialized = False
        self._automation = ctypes.c_void_p()
        self._element = ctypes.c_void_p()
        self._ole = ctypes.WinDLL("ole32")
        self._ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self._ole.CoInitializeEx.restype = ctypes.c_int32
        self._ole.CoCreateInstance.argtypes = [ctypes.POINTER(_GUID), ctypes.c_void_p,
            ctypes.c_uint32, ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)]
        self._ole.CoCreateInstance.restype = ctypes.c_int32
        self._ole.CoUninitialize.argtypes = []
        self._ole.CoUninitialize.restype = None

    def _owned(self):
        if threading.get_ident() != self._owner:
            raise RuntimeError("Private UIA ownership unavailable.")

    @staticmethod
    def _ok(hr):
        if type(hr) is not int or hr != 0:
            raise OSError("Private UIA operation unavailable.")

    def _method(self, pointer, slot, result, *arguments):
        self._owned()
        if not self._initialized or not pointer.value:
            raise OSError("Private UIA reference unavailable.")
        table = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        return ctypes.WINFUNCTYPE(result, ctypes.c_void_p, *arguments)(table[slot])

    def initialize(self):
        self._owned()
        hr = self._ole.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED; no window/message loop.
        if type(hr) is not int or hr not in (0, 1):
            raise OSError("Private UIA initialization unavailable.")
        self._initialized = True  # S_FALSE also requires CoUninitialize.

    def activate(self):
        self._owned()
        self._ok(self._ole.CoCreateInstance(ctypes.byref(_CLSID), None, 1,
                 ctypes.byref(_IID), ctypes.byref(self._automation)))  # CLSCTX_INPROC_SERVER
        if not self._automation.value:
            raise OSError("Private UIA activation unavailable.")

    def element_from_point(self, x, y):
        method = self._method(self._automation, 7, ctypes.c_int32,
                             _POINT, ctypes.POINTER(ctypes.c_void_p))
        self._ok(method(self._automation, _POINT(x, y), ctypes.byref(self._element)))
        if not self._element.value:
            raise OSError("Private UIA element unavailable.")

    def control_type(self):
        value = ctypes.c_int32()
        method = self._method(self._element, 21, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32))
        self._ok(method(self._element, ctypes.byref(value)))
        return value.value

    def is_enabled(self):
        value = ctypes.c_int32()
        method = self._method(self._element, 28, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32))
        self._ok(method(self._element, ctypes.byref(value)))
        if value.value not in (0, 1):
            raise ValueError("Private UIA boolean unavailable.")
        return value.value == 1

    def _release(self, pointer):
        self._owned()
        if pointer.value:
            method = self._method(pointer, 2, ctypes.c_uint32)
            address = pointer.value
            pointer.value = None  # Never retry a Release, even if it raises.
            method(address)

    def release_element(self):
        self._release(self._element)

    def release_automation(self):
        self._release(self._automation)

    def uninitialize(self):
        self._owned()
        if self._initialized:
            self._initialized = False
            self._ole.CoUninitialize()


class _MTAWorker(_LocalOnly):
    __slots__ = ()

    def run(self, task):
        thread = threading.Thread(target=task, daemon=False)
        thread.start()
        thread.join()  # Cardinality bounded, no hard native deadline.
        if thread.is_alive():
            raise RuntimeError("Private UIA worker incomplete.")


_DEFAULT_PLATFORM = object()


class _UIElementObservationService(_LocalOnly):
    """VERIFIED means only a complete validated bounded UIA sample.

    No intended-control identity, actionability, clickability, visibility,
    semantic match, action result, or task success is established.
    Factories and worker injection are private trusted deterministic test seams.
    """
    __slots__ = ("_native_factory", "_worker_factory", "_platform")

    def __init__(self, *, native_factory=None, worker_factory=None, platform=_DEFAULT_PLATFORM):
        self._native_factory = _UIANative if native_factory is None else native_factory
        self._worker_factory = _MTAWorker if worker_factory is None else worker_factory
        self._platform = sys.platform if platform is _DEFAULT_PLATFORM else platform

    def observe(self, point):
        unknown = _UIElementResult()
        try:
            if type(self._platform) is not str or self._platform != "win32":
                return unknown
            coordinates = _point_snapshot(point)  # Before worker/native construction.
            completed = []  # Only primitive samples cross the joined worker boundary.

            def task():
                native = None
                sample = None
                clean = True
                try:
                    native = self._native_factory()
                    native.initialize()
                    native.activate()
                    native.element_from_point(*coordinates)
                    control_type = native.control_type()
                    enabled = native.is_enabled()
                    _sample_valid(control_type, enabled)
                    sample = (control_type, enabled)
                except BaseException:
                    clean = False  # No native detail escapes the owning thread.
                finally:
                    if native is not None:
                        for name in ("release_element", "release_automation", "uninitialize"):
                            try:
                                getattr(native, name)()
                            except BaseException:
                                clean = False
                    if clean and sample is not None:
                        completed.append(sample)

            self._worker_factory().run(task)
            if len(completed) != 1 or _point_snapshot(point) != coordinates:
                return unknown
            control_type, enabled = completed[0]
            evidence = _UIElementEvidence(point, control_type, enabled)
            result = _UIElementResult(VerificationStatus.VERIFIED, evidence)
            _UIElementResult.__post_init__(result)
            if evidence.point is not point or _point_snapshot(point) != coordinates:
                return unknown
            return result
        except BaseException:
            return unknown
