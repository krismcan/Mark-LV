"""P137 frozen-Windows UI smoke test, FAKE credential adapter only.

The compiled executable below is TEST-ONLY. It must never contain a path to
actual native CredWrite/Read/Delete: WindowsCredentialBackend(_native=Fake)
has fake methods that refuse any real operation, and test only confirms
Tk page construction, deliberate review, cancel and no automatic native IO.
"""
from __future__ import annotations

import sys
import tkinter as tk

from nayeon.brain.local_byok_user_scope import LocalByokController
from nayeon.secrets.windows_credential import WindowsCredentialBackend
from nayeon.desktop_alpha.local_byok_window import LocalByokWindow


class RejectingNative:
    def __init__(self) -> None:
        self.presences = 0
        self.mutations = 0

    def contains(self,target: str) -> bool:
        if target != "nayeon-v1/secret/openai.api_key":
            raise AssertionError("wrong fixed target")
        self.presences += 1
        return False

    def read(self,*args):
        raise AssertionError("no credential content may be read by frozen UI smoke")

    def write(self,*args):
        self.mutations += 1
        raise AssertionError("synthetic frozen smoke must never attempt a write")

    def delete(self,*args):
        self.mutations += 1
        raise AssertionError("synthetic frozen smoke must never delete")


class RefusingMutex:
    def hold(self):
        raise AssertionError("smoke cannot acquire any credential effect mutex")


def main() -> int:
    if sys.platform!="win32":
        print("P137_FROZEN_WINDOWS_ONLY=REFUSED")
        return 8
    if not getattr(sys,"frozen",False):
        print("P137_SMOKE_REQUIRES_GENUINELY_FROZEN_EXE=REFUSED")
        return 9
    import os
    if not (os.getenv("GITHUB_ACTIONS")=="true" and
            os.getenv("RUNNER_OS")=="Windows" and
            os.getenv("GITHUB_REPOSITORY")=="krismcan/Mark-LV" and
            os.getenv("P137_EPHEMERAL_PACKAGE_SMOKE")=="FAKE_STORE_ONLY"):
        print("P137_SMOKE_HOST_AUTH=REFUSED")
        return 10

    backend=RejectingNative()
    controller=LocalByokController(WindowsCredentialBackend(_native=backend),
                                  _mutex=RefusingMutex())
    if backend.presences!=0 or backend.mutations!=0:
        return 11

    root=tk.Tk()
    root.withdraw()
    try:
        window=LocalByokWindow(root,controller=controller)
        if backend.presences!=0 or backend.mutations!=0:
            raise AssertionError("window construction contacted native credentials")
        if window._entry.cget("show")!="*" or window._entry.cget("state")!="disabled":
            raise AssertionError("local key field must begin masked and disabled")
        if "No access has been made" not in window._status.cget("text"):
            raise AssertionError("initial status must not claim connected")
        window._choices[0].invoke()
        if backend.presences!=1 or backend.mutations!=0:
            raise AssertionError("human review must inspect only fake presence")
        window._reject.invoke()
        if backend.mutations!=0 or window._entry.get()!="":
            raise AssertionError("reject must clear without native credential effects")
        window.close_from_window()
        if backend.mutations!=0:
            raise AssertionError("window close must not write credentials")
    finally:
        try:root.destroy()
        except tk.TclError:pass

    print("P137_ACTUAL_FROZEN_WINDOWS_TK_UI=SMOKE_PASS")
    print("P137_FAKE_CREDENTIAL_PRESENCE_ONLY=ONE_EXPLICIT_REVIEW")
    print("P137_ACTUAL_WINCRED_OR_PROVIDER_EFFECT=NONE")
    print("P137_PRODUCTION_SIGNER_AND_SAC=NOT_VERIFIED")
    print("P137_C1_USER_SCOPE_RELEASE=HOLD")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
