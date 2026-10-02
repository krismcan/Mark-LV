"""One bounded Unicode SendInput call; only the saved foreground target is eligible."""
import ctypes
from ctypes import wintypes as W

from nayeon.services.keyboard_text import TextInputState, _valid_text_binding, validate_text
from nayeon.services.window_focus import FocusState
from nayeon.services.windows_focus import WindowsFocusAdapter
from nayeon.services.windows_desktop import WindowsDesktopAdapter, _WindowsNative


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", W.WORD), ("wScan", W.WORD), ("dwFlags", W.DWORD),
                ("time", W.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _MOUSEINPUT(ctypes.Structure):
    # Required union padding/alignment for the native INPUT ABI; never emitted.
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("mouseData", W.DWORD),
                ("dwFlags", W.DWORD), ("time", W.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", W.DWORD), ("wParamL", W.WORD), ("wParamH", W.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT), ("hi", _HARDWAREINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", W.DWORD), ("data", _INPUTUNION)]


def _unicode_events(text):
    validate_text(text)
    encoded = text.encode("utf-16-le")
    units = [int.from_bytes(encoded[i:i + 2], "little") for i in range(0, len(encoded), 2)]
    events = (_INPUT * (2 * len(units)))()
    for i, unit in enumerate(units):
        for offset, flags in ((0, 0x0004), (1, 0x0004 | 0x0002)):
            event = events[2 * i + offset]
            event.type = 1  # INPUT_KEYBOARD
            event.ki = _KEYBDINPUT(0, unit, flags, 0, 0)
    return events


class _KeyboardNative(_WindowsNative):
    def __init__(self):
        super().__init__()
        self.u.SendInput.argtypes = [W.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
        self.u.SendInput.restype = W.UINT

    def inject(self, events):
        return self.u.SendInput(len(events), events, ctypes.sizeof(_INPUT))


class WindowsKeyboardAdapter(WindowsDesktopAdapter):
    def _keyboard_native(self):
        if self._platform != "win32":
            raise ValueError("Supported keyboard context unavailable.")
        return self._native if self._native is not None else _KeyboardNative()

    @staticmethod
    def _observe(native, binding):
        # Reuse Phase 6.2 context/identity bracketing without its focus mutation.
        state = WindowsFocusAdapter._observe(native, binding.target)
        if state is FocusState.FOCUSED:
            # Closest foreground sample to SendInput, after owned query cleanup.
            foreground = native.foreground()
            if type(foreground) is not int or foreground < 0:
                return TextInputState.INCONCLUSIVE
            return (TextInputState.TYPED if foreground == binding.target.identity.hwnd
                    else TextInputState.TARGET_CHANGED)  # Eligibility only.
        if state in (FocusState.NOT_FOCUSED, FocusState.TARGET_CHANGED):
            return TextInputState.TARGET_CHANGED
        return TextInputState.INCONCLUSIVE

    def type_text(self, binding):
        if not _valid_text_binding(binding):
            return TextInputState.INCONCLUSIVE
        try:
            events = _unicode_events(binding.text)
            native = self._keyboard_native()
            state = self._observe(native, binding)
            if state is not TextInputState.TYPED:
                return state
            # One call only. Exceptions/invalid counts are uncertain, even if
            # the call mutated the stream. Never retry or release keys afterward.
            inserted = None
            try:
                inserted = native.inject(events)
            except Exception:
                pass
            post = self._observe(native, binding)
            if post is not TextInputState.TYPED:
                return post
            if type(inserted) is not int or not 0 <= inserted <= len(events):
                return TextInputState.INCONCLUSIVE
            if inserted == len(events):
                return TextInputState.TYPED
            return TextInputState.PARTIAL if inserted else TextInputState.NOT_TYPED
        except Exception:
            return TextInputState.INCONCLUSIVE

    def observe_target(self, binding):
        if not _valid_text_binding(binding):
            return TextInputState.INCONCLUSIVE
        try:
            return self._observe(self._keyboard_native(), binding)
        except Exception:
            return TextInputState.INCONCLUSIVE
