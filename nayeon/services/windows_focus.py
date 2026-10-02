"""One normal Win32 foreground attempt; no retries or foreground workarounds."""
from ctypes import wintypes as W

from nayeon.services.computer_control import DesktopContext, WindowIdentity
from nayeon.services.window_focus import FocusState, _valid_focus_binding
from nayeon.services.windows_desktop import WindowsDesktopAdapter, _WindowsNative


class _FocusNative(_WindowsNative):
    def __init__(self):
        super().__init__()
        self.u.SetForegroundWindow.argtypes = [W.HWND]
        self.u.SetForegroundWindow.restype = W.BOOL

    def focus(self, hwnd):
        return bool(self.u.SetForegroundWindow(hwnd))


class WindowsFocusAdapter(WindowsDesktopAdapter):
    def _focus_native(self):
        if self._platform != "win32":
            raise ValueError("Supported focus context unavailable.")
        return self._native if self._native is not None else _FocusNative()

    @staticmethod
    def _target_state(native, binding):
        context = native.context()
        identity = native.identity(binding.identity.hwnd)
        late_context = native.context()
        if (type(context) is not DesktopContext or type(late_context) is not DesktopContext
                or type(identity) is not WindowIdentity):
            return FocusState.INCONCLUSIVE
        if (context != binding.context or late_context != binding.context
                or identity != binding.identity or not identity.valid(context)):
            return FocusState.TARGET_CHANGED
        return FocusState.FOCUSED

    @classmethod
    def _observe(cls, native, binding):
        # Recheck the target even when another window is foreground; do not
        # conflate same-process windows or rely on the HWND sample alone.
        state = cls._target_state(native, binding)
        foreground = native.foreground()
        late = cls._target_state(native, binding)
        if state is not FocusState.FOCUSED:
            return state
        if late is not FocusState.FOCUSED:
            return late
        if type(foreground) is not int or foreground < 0:
            return FocusState.INCONCLUSIVE
        return FocusState.FOCUSED if foreground == binding.identity.hwnd else FocusState.NOT_FOCUSED

    def focus_window(self, binding):
        if not _valid_focus_binding(binding):
            return FocusState.INCONCLUSIVE
        try:
            native = self._focus_native()
            state = self._target_state(native, binding)
            if state is not FocusState.FOCUSED:
                return state
            # Exactly one attempt. A native exception may follow a mutation;
            # still sample afterward, but never upgrade uncertain acknowledgement.
            acknowledged = False
            try:
                acknowledged = native.focus(binding.identity.hwnd) is True
            except Exception:
                pass
            state = self._observe(native, binding)
            if state is FocusState.FOCUSED and not acknowledged:
                return FocusState.NOT_FOCUSED
            return state
        except Exception:
            return FocusState.INCONCLUSIVE

    def observe_focus(self, binding):
        if not _valid_focus_binding(binding):
            return FocusState.INCONCLUSIVE
        try:
            return self._observe(self._focus_native(), binding)
        except Exception:
            return FocusState.INCONCLUSIVE
