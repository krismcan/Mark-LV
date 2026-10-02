"""Query-only pointer acquisition using the existing desktop identity machinery."""
import ctypes
from ctypes import wintypes as W

from nayeon.services.computer_control import DesktopContext
from nayeon.services.pointer_observation import (
    PointerObservation, PointerReason as R, PointerState as S,
    _PointerEvidence, _PointerSample, _point_valid,
)
from nayeon.services.windows_desktop import WindowsDesktopAdapter, _WindowsNative, _require


class _PointerNative(_WindowsNative):
    def __init__(self):
        super().__init__()
        self.u.GetCursorPos.argtypes = [ctypes.POINTER(W.POINT)]
        self.u.GetCursorPos.restype = W.BOOL
        self.u.WindowFromPoint.argtypes = [W.POINT]
        self.u.WindowFromPoint.restype = W.HWND

    def cursor(self):
        point = W.POINT()
        _require(self.u.GetCursorPos(ctypes.byref(point)))
        return point.x, point.y

    def window_at(self, point):
        return self.u.WindowFromPoint(W.POINT(*point)) or 0

    def root(self, hwnd):
        # HWNDs are borrowed; no ownership or cleanup is acquired here.
        return _require(self.u.GetAncestor(hwnd, 2))  # GA_ROOT


def _handle(value):
    if type(value) is not int or not 0 <= value < 2 ** (ctypes.sizeof(ctypes.c_void_p) * 8):
        raise ValueError("Required native identifier unavailable.")
    return value


class WindowsPointerAdapter(WindowsDesktopAdapter):
    @staticmethod
    def _sample(native, *, point=None):
        trailing_cursor = point is not None
        if point is None:
            point = native.cursor()
        if not _point_valid(point):
            raise ValueError("Required pointer sample unavailable.")
        window = _handle(native.window_at(point))
        root = _handle(native.root(window)) if window else 0
        if window and not root:
            raise ValueError("Required root unavailable.")
        foreground = _handle(native.foreground())
        foreground_root = _handle(native.root(foreground)) if foreground else 0
        if foreground and not foreground_root:
            raise ValueError("Required foreground root unavailable.")
        identity = native.identity(root) if root else None
        foreground_identity = native.identity(foreground_root) if foreground_root else None
        # Reuse the first point only inside this acquisition. The final cursor
        # read brackets target/identity queries; drift invalidates the snapshot.
        if trailing_cursor:
            point = native.cursor()
        return _PointerSample(point, window, root, foreground_root, identity, foreground_identity)

    def observe_pointer(self):
        unavailable = PointerObservation(S.UNAVAILABLE, R.CONTEXT)
        if self._platform != "win32":
            return unavailable
        try:
            native = self._native if self._native is not None else _PointerNative()
            context = native.context()
            if type(context) is not DesktopContext or not context.valid():
                return unavailable
            started = self._clock()
        except Exception:
            return unavailable
        try:
            early = self._sample(native)
            late = self._sample(native, point=early.point)
            late_context = native.context()
            evidence = _PointerEvidence(early, late, context, late_context, started, self._clock())
            if not evidence.complete():
                return PointerObservation(S.PARTIAL, R.INCOMPLETE)
            if not evidence.consistent():
                return PointerObservation(S.PARTIAL, R.CHANGED)
            if early.root == 0:
                return PointerObservation(S.NO_TARGET, R.NO_TARGET)
            return PointerObservation(S.OBSERVED, R.CONSISTENT, evidence)
        except Exception:
            return PointerObservation(S.PARTIAL, R.INCOMPLETE)
