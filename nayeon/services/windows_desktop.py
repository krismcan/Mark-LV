"""One read-only Win32 acquisition. No titles, input, retries, or focus changes."""
import ctypes
from ctypes import wintypes as W
import sys
from time import perf_counter_ns

from nayeon.services.computer_control import (
    DesktopContext, ForegroundEvidence, ForegroundObservation, ForegroundState,
    ObservationReason, WindowIdentity, WindowState,
)


class _ReadFailure(Exception):
    """Private, fixed failure; never retain native error text."""


def _require(value):
    if not value:
        raise _ReadFailure("Required native evidence unavailable.")
    return value


class _WindowsNative:
    """Small query-only facade. Owned resources end within their acquisition method."""
    def __init__(self):
        self.u = ctypes.WinDLL("user32", use_last_error=True)
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.w = ctypes.WinDLL("wtsapi32", use_last_error=True)
        P = ctypes.POINTER
        signatures = {
            self.u: {
                "GetForegroundWindow": ([], W.HWND), "IsWindow": ([W.HWND], W.BOOL),
                "GetWindowThreadProcessId": ([W.HWND, P(W.DWORD)], W.DWORD),
                "GetAncestor": ([W.HWND, W.UINT], W.HWND),
                "GetClassNameW": ([W.HWND, W.LPWSTR, ctypes.c_int], ctypes.c_int),
                "IsWindowVisible": ([W.HWND], W.BOOL), "IsIconic": ([W.HWND], W.BOOL),
                "IsZoomed": ([W.HWND], W.BOOL),
                "GetWindowRect": ([W.HWND, P(W.RECT)], W.BOOL),
                "GetClientRect": ([W.HWND, P(W.RECT)], W.BOOL),
                "ClientToScreen": ([W.HWND, P(W.POINT)], W.BOOL),
                "MonitorFromWindow": ([W.HWND, W.DWORD], W.HANDLE),
                "OpenInputDesktop": ([W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
                "CloseDesktop": ([W.HANDLE], W.BOOL),
                "GetThreadDesktop": ([W.DWORD], W.HANDLE),
                "GetProcessWindowStation": ([], W.HANDLE),
                "GetUserObjectInformationW": ([W.HANDLE, ctypes.c_int, W.LPVOID,
                                                W.DWORD, P(W.DWORD)], W.BOOL),
            },
            self.k: {
                "GetCurrentProcessId": ([], W.DWORD), "GetCurrentThreadId": ([], W.DWORD),
                "ProcessIdToSessionId": ([W.DWORD, P(W.DWORD)], W.BOOL),
                "OpenProcess": ([W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
                "CloseHandle": ([W.HANDLE], W.BOOL),
                "GetProcessTimes": ([W.HANDLE] + [P(W.FILETIME)] * 4, W.BOOL),
                "QueryFullProcessImageNameW": ([W.HANDLE, W.DWORD, W.LPWSTR, P(W.DWORD)], W.BOOL),
                "GetExitCodeProcess": ([W.HANDLE, P(W.DWORD)], W.BOOL),
            },
            self.w: {
                "WTSQuerySessionInformationW": ([W.HANDLE, W.DWORD, ctypes.c_int,
                                                 P(W.LPVOID), P(W.DWORD)], W.BOOL),
                "WTSFreeMemory": ([W.LPVOID], None),
            },
        }
        for dll, entries in signatures.items():
            for name, (args, result) in entries.items():
                function = getattr(dll, name)
                function.argtypes, function.restype = args, result
        # DPI is optional state. Older/limited contexts need not implement it.
        for name, args, result in (
            ("GetDpiForWindow", [W.HWND], W.UINT),
            ("GetWindowDpiAwarenessContext", [W.HWND], W.HANDLE),
            ("GetThreadDpiAwarenessContext", [], W.HANDLE),
            ("GetAwarenessFromDpiAwarenessContext", [W.HANDLE], ctypes.c_int),
        ):
            function = getattr(self.u, name, None)
            if function is not None:
                function.argtypes, function.restype = args, result

    def _name(self, handle):
        _require(handle)
        buffer = ctypes.create_unicode_buffer(512)
        needed = W.DWORD()
        _require(self.u.GetUserObjectInformationW(handle, 2, buffer,
                                                  ctypes.sizeof(buffer), ctypes.byref(needed)))
        _require(0 < needed.value <= ctypes.sizeof(buffer) and buffer.value)
        return buffer.value

    def _session(self, pid):
        session = W.DWORD()
        _require(self.k.ProcessIdToSessionId(pid, ctypes.byref(session)))
        return session.value

    def _active(self, session):
        pointer, size = W.LPVOID(), W.DWORD()
        try:
            _require(self.w.WTSQuerySessionInformationW(
                None, session, 8, ctypes.byref(pointer), ctypes.byref(size)))
            _require(pointer.value and size.value == ctypes.sizeof(ctypes.c_int))
            return ctypes.cast(pointer, ctypes.POINTER(ctypes.c_int)).contents.value == 0
        finally:
            if pointer.value:
                self.w.WTSFreeMemory(pointer)

    def context(self):
        session = self._session(self.k.GetCurrentProcessId())
        desktop = _require(self.u.OpenInputDesktop(0, False, 1))  # DESKTOP_READOBJECTS
        try:
            return DesktopContext(session, self._name(desktop),
                                  self._name(self.u.GetThreadDesktop(self.k.GetCurrentThreadId())),
                                  self._name(self.u.GetProcessWindowStation()), self._active(session))
        finally:
            _require(self.u.CloseDesktop(desktop))

    def foreground(self):
        return self.u.GetForegroundWindow() or 0

    def _process(self, pid):
        handle = _require(self.k.OpenProcess(0x1000, False, pid))
        try:
            creation, exit_time, kernel, user = (W.FILETIME() for _ in range(4))
            _require(self.k.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                           ctypes.byref(kernel), ctypes.byref(user)))
            created = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            _require(created)
            image = ctypes.create_unicode_buffer(32768)
            size = W.DWORD(len(image))
            _require(self.k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)))
            _require(0 < size.value < len(image) and len(image.value) == size.value)
            status = W.DWORD()
            _require(self.k.GetExitCodeProcess(handle, ctypes.byref(status)))
            _require(status.value == 259)  # STILL_ACTIVE; a dead process is incomplete evidence.
            return created, image.value
        finally:
            _require(self.k.CloseHandle(handle))

    def identity(self, hwnd):
        _require(self.u.IsWindow(hwnd))
        pid = W.DWORD()
        tid = _require(self.u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)))
        _require(pid.value)
        root = _require(self.u.GetAncestor(hwnd, 2))  # GA_ROOT
        _require(root == hwnd)
        created, image = self._process(pid.value)
        session = self._session(pid.value)
        name = ctypes.create_unicode_buffer(256)
        length = self.u.GetClassNameW(hwnd, name, len(name))
        _require(0 < length < len(name) - 1 and len(name.value) == length)
        desktop = self._name(self.u.GetThreadDesktop(tid))  # Borrowed; never CloseDesktop.
        return WindowIdentity(hwnd, pid.value, tid, created, image, name.value, root, session, desktop)

    def _optional(self, function):
        try:
            return function()
        except Exception:
            return None

    def _rect(self, hwnd, function):
        rect = W.RECT()
        _require(function(hwnd, ctypes.byref(rect)))
        _require(rect.right >= rect.left and rect.bottom >= rect.top)
        return rect.left, rect.top, rect.right, rect.bottom

    def _origin(self, hwnd):
        point = W.POINT(0, 0)
        _require(self.u.ClientToScreen(hwnd, ctypes.byref(point)))
        return point.x, point.y

    def _awareness(self, context):
        _require(context)
        value = self.u.GetAwarenessFromDpiAwarenessContext(context)
        _require(value in (0, 1, 2))
        return value

    def state(self, hwnd):
        # Geometry is API-coordinate snapshot data, not physical click authority.
        return WindowState(
            visible=bool(self.u.IsWindowVisible(hwnd)), iconic=bool(self.u.IsIconic(hwnd)),
            maximized=bool(self.u.IsZoomed(hwnd)),
            window_rect=self._optional(lambda: self._rect(hwnd, self.u.GetWindowRect)),
            client_rect=self._optional(lambda: self._rect(hwnd, self.u.GetClientRect)),
            client_origin=self._optional(lambda: self._origin(hwnd)),
            monitor=self._optional(lambda: self.u.MonitorFromWindow(hwnd, 0) or None),
            dpi=self._optional(lambda: self.u.GetDpiForWindow(hwnd) or None),
            window_awareness=self._optional(lambda: self._awareness(
                self.u.GetWindowDpiAwarenessContext(hwnd))),
            observer_awareness=self._optional(lambda: self._awareness(
                self.u.GetThreadDpiAwarenessContext())),
        )


class WindowsDesktopAdapter:
    """Sample consistency, never continuous lifetime or durable authority.

    Native calls are synchronous; bounded here means a fixed call sequence,
    not a guaranteed OS deadline. All owned handles are closed before return.
    """
    def __init__(self, *, native=None, platform=None, clock=perf_counter_ns):
        self._native = native
        self._platform = sys.platform if platform is None else platform
        self._clock = clock

    def observe_foreground_window(self) -> ForegroundObservation:
        unavailable = ForegroundObservation(ForegroundState.UNAVAILABLE, ObservationReason.CONTEXT)
        if self._platform != "win32":
            return unavailable
        try:
            native = self._native if self._native is not None else _WindowsNative()
            context = native.context()
            if type(context) is not DesktopContext or not context.valid():
                return unavailable
            started = self._clock()
        except Exception:
            return unavailable
        try:
            h1 = native.foreground()
            if not h1:
                return ForegroundObservation(ForegroundState.NO_FOREGROUND, ObservationReason.NO_FOREGROUND)
            early = native.identity(h1)
            if (type(h1) is not int or type(early) is not WindowIdentity
                    or early.hwnd != h1 or not early.valid(context)):
                raise _ReadFailure()
            state = native.state(h1)
            late_context = native.context()
            h2 = native.foreground()
            if h1 != h2:
                return ForegroundObservation(ForegroundState.PARTIAL, ObservationReason.CHANGED)
            late = native.identity(h1)
            ended = self._clock()
            evidence = ForegroundEvidence(early, late, context, late_context, state, started, ended)
            if not evidence.complete():
                raise _ReadFailure()
            if not evidence.consistent():
                return ForegroundObservation(ForegroundState.PARTIAL, ObservationReason.CONTRADICTORY)
            return ForegroundObservation(ForegroundState.OBSERVED, ObservationReason.CONSISTENT, evidence)
        except Exception:
            return ForegroundObservation(ForegroundState.PARTIAL, ObservationReason.INCOMPLETE)
