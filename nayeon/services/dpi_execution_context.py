"""Private short-lived current-thread DPI scope and coordinate certification."""
import ctypes
from ctypes import wintypes as W
from dataclasses import dataclass
import sys
import threading

from nayeon.services.computer_control import _Redacted
from nayeon.services.pointer_coordinate_contract import (
    _PhysicalCoordinateContractService, _PhysicalCoordinateResult,
    _awareness, _point_snapshot,
)
from nayeon.verification.contract import VerificationStatus

__all__ = ()
_DEFAULT_PLATFORM = object()
_PMV2 = W.HANDLE(-4).value
_POINTER_BITS = ctypes.sizeof(W.HANDLE) * 8


class _LocalOnly(_Redacted):
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise TypeError("Private DPI scope cannot be serialized or copied.")

    def __copy__(self):
        raise TypeError("Private DPI scope cannot be serialized or copied.")

    def __deepcopy__(self, memo):
        raise TypeError("Private DPI scope cannot be serialized or copied.")


def _context(value):
    if type(value) is not int:
        raise TypeError("Exact private context required.")
    if value == 0 or not -(2 ** (_POINTER_BITS - 1)) <= value < 2 ** _POINTER_BITS:
        raise ValueError("Non-null pointer-sized context required.")
    return value


@dataclass(frozen=True, slots=True, repr=False)
class _ScopedDpiResult(_LocalOnly):
    completed: bool = False
    value: object = None

    def __post_init__(self):
        if type(self) is not _ScopedDpiResult or type(self.completed) is not bool:
            raise TypeError("Exact private scoped result required.")
        if not self.completed and self.value is not None:
            raise ValueError("Incomplete scope carries no callback value.")


class _DpiExecutionNative(_LocalOnly):
    """Five current-thread context APIs; constructed only by the owning worker."""
    __slots__ = ("_get", "_awareness", "_valid", "_equal", "_set")

    def __init__(self):
        if sys.platform != "win32":
            raise OSError("Windows DPI scope unavailable.")
        dll = ctypes.WinDLL("user32")
        self._get = dll.GetThreadDpiAwarenessContext
        self._awareness = dll.GetAwarenessFromDpiAwarenessContext
        self._valid = dll.IsValidDpiAwarenessContext
        self._equal = dll.AreDpiAwarenessContextsEqual
        self._set = dll.SetThreadDpiAwarenessContext
        for function, arguments, result in (
            (self._get, [], W.HANDLE),
            (self._awareness, [W.HANDLE], ctypes.c_int),
            (self._valid, [W.HANDLE], W.BOOL),
            (self._equal, [W.HANDLE, W.HANDLE], W.BOOL),
            (self._set, [W.HANDLE], W.HANDLE),
        ):
            function.argtypes = arguments
            function.restype = result

    def context(self):
        return self._get()

    def awareness(self, context):
        return self._awareness(context)

    def valid(self, context):
        return bool(self._valid(context))

    def equal(self, first, second):
        return bool(self._equal(first, second))

    def set_context(self, context):
        return self._set(context)


class _ScopedDpiExecutionContext(_LocalOnly):
    """One joined owned worker per run; factories are private trusted test seams.

    Native handles remain inside the worker. Completion means the callback ran
    under the checked scope and restoration passed; it proves no callback effect.
    A join has no hard native deadline. No native exception detail is published.
    """
    __slots__ = ("_native_factory", "_platform")

    def __init__(self, *, native_factory=None, platform=_DEFAULT_PLATFORM):
        self._native_factory = _DpiExecutionNative if native_factory is None else native_factory
        self._platform = sys.platform if platform is _DEFAULT_PLATFORM else platform

    def run(self, callback):
        unknown = _ScopedDpiResult()
        try:
            if type(self._platform) is not str or self._platform != "win32" or not callable(callback):
                return unknown
            completed = []

            def task():
                native = None
                prior = None
                prior_awareness = None
                restore_needed = False
                clean = True
                value = None
                try:
                    native = self._native_factory()
                    prior = _context(native.context())
                    prior_awareness = _awareness(native.awareness(prior))
                    if native.valid(_PMV2) is not True:
                        raise ValueError("Reviewed target unavailable.")
                    # Once a setter is attempted, even an exception may conceal
                    # a changed context. Restore once conservatively, never retry.
                    restore_needed = True
                    returned = _context(native.set_context(_PMV2))
                    if native.equal(returned, prior) is not True:
                        raise ValueError("Prior context mismatch.")
                    current = _context(native.context())
                    if (native.equal(current, _PMV2) is not True
                            or _awareness(native.awareness(current)) != 2):
                        raise ValueError("Scoped context mismatch.")
                    value = callback()
                except BaseException:
                    clean = False
                finally:
                    if restore_needed:
                        try:
                            old = _context(native.set_context(prior))
                            if native.equal(old, _PMV2) is not True:
                                raise ValueError("Restore return mismatch.")
                            restored = _context(native.context())
                            if (native.equal(restored, prior) is not True
                                    or _awareness(native.awareness(restored)) != prior_awareness):
                                raise ValueError("Restored context mismatch.")
                        except BaseException:
                            clean = False
                    if clean:
                        completed.append(_ScopedDpiResult(True, value))

            thread = threading.Thread(target=task, daemon=False)
            thread.start()
            thread.join()
            if thread.is_alive() or len(completed) != 1:
                return unknown
            return completed[0]
        except BaseException:
            return unknown


class _ScopedPhysicalCoordinateService(_LocalOnly):
    """Return existing same-point certification only after a clean joined scope."""
    __slots__ = ("_scope", "_contract_factory")

    def __init__(self, *, scope=None, contract_factory=None):
        self._scope = _ScopedDpiExecutionContext() if scope is None else scope
        self._contract_factory = (
            _PhysicalCoordinateContractService if contract_factory is None else contract_factory)

    def certify(self, point):
        unknown = _PhysicalCoordinateResult()
        try:
            coordinates = _point_snapshot(point)

            def certify_on_worker():
                if _point_snapshot(point) != coordinates:
                    raise ValueError("Point changed before certification.")
                return self._contract_factory().certify(point)

            scoped = self._scope.run(certify_on_worker)
            if type(scoped) is not _ScopedDpiResult:
                return unknown
            _ScopedDpiResult.__post_init__(scoped)
            if not scoped.completed or _point_snapshot(point) != coordinates:
                return unknown
            result = scoped.value
            if type(result) is not _PhysicalCoordinateResult:
                return unknown
            _PhysicalCoordinateResult.__post_init__(result)
            if (result.status is not VerificationStatus.VERIFIED
                    or result.evidence.point is not point
                    or _point_snapshot(point) != coordinates):
                return unknown
            return result
        except BaseException:
            return unknown
