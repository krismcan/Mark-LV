"""Phase 8.31 private fake-only lifecycle/effect fixture. No product import."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from unittest import mock


class FakeDeliveryState(Enum):
    QUEUED = "QUEUED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, eq=False, repr=False)
class FakeReceipt:
    ticket: object
    view: object
    session_identity: object
    epoch: int
    revision: int
    nonce: object


class FakeOfflineCompletionQueue:
    """One synthetic queued ticket; no provider, storage, executor or worker."""

    def __init__(self, tkroot, owner, root_identity, effects=None):
        self._tkroot, self._owner, self._root = tkroot, owner, root_identity
        self._effects = effects
        self._entry = None
        self._after_id = None
        self._state = None
        self.delivery_attempts = 0
        self.deliveries = 0
        self.callback_errors = []

    @property
    def state(self):
        return self._state

    def issue(self, view, text: str) -> FakeReceipt:
        if self._entry is not None:
            raise RuntimeError("Fake queue already owns a request")
        ticket = self._owner.issue_submission(self._root, view, text)
        snapshot = self._owner.snapshot
        receipt = FakeReceipt(ticket, view, snapshot.session_identity,
                              snapshot.epoch, snapshot.revision, object())
        self._entry = receipt
        self._state = FakeDeliveryState.QUEUED
        try:
            after_id = self._tkroot.after_idle(lambda: self._deliver_idle(receipt))
            if self._entry is receipt:
                self._after_id = after_id
            else:
                self._tkroot.after_cancel(after_id)
        except BaseException:
            if self._entry is receipt:
                self._entry = None
                self._after_id = None
                self._state = FakeDeliveryState.CANCELLED
            self._owner.revoke_submission(self._root, ticket)
            raise
        return receipt

    def _deliver_idle(self, receipt):
        # The callback's Tcl command is executing: never cancel it as though
        # it were still a pending scheduled script.
        if receipt is self._entry:
            self._after_id = None
        try:
            self.deliver(receipt)
        except BaseException as exc:
            self.callback_errors.append(type(exc).__name__)
            raise

    def _matching(self, receipt) -> bool:
        from nayeon.desktop_alpha.conversation_session import SubmissionState
        snapshot = self._owner.snapshot
        active = self._owner._active  # Private, test-owned synthetic harness only.
        return (receipt is self._entry and self._state is FakeDeliveryState.QUEUED
                and snapshot.session_identity is receipt.session_identity
                and snapshot.epoch == receipt.epoch
                and snapshot.revision == receipt.revision
                and not snapshot.closed
                and self._owner._view is receipt.view
                and active is not None and active.ticket is receipt.ticket
                and active.state is SubmissionState.ISSUED)

    def _retire_exact(self, receipt, *, cancel_schedule: bool):
        if receipt is not self._entry:
            return False
        pending, self._after_id = self._after_id, None
        self._entry = None  # Revoke exact A before any possibly reentrant Tk op.
        self._state = FakeDeliveryState.CANCELLED
        try:
            if cancel_schedule and pending is not None:
                self._tkroot.after_cancel(pending)
        finally:
            # A's cleanup never revokes successor B.
            self._owner.revoke_submission(self._root, receipt.ticket)
        return True

    def deliver(self, receipt: FakeReceipt) -> bool:
        self.delivery_attempts += 1
        if receipt is not self._entry or self._state is not FakeDeliveryState.QUEUED:
            return False
        was_current = self._matching(receipt)
        pending, self._after_id = self._after_id, None
        self._entry = None
        self._state = FakeDeliveryState.CANCELLED
        try:
            if pending is not None:
                self._tkroot.after_cancel(pending)
            if not was_current:
                return False
            from nayeon.desktop_alpha.conversation_session import (
                EntryState, SubmissionState, SessionRefused,
            )
            try:
                self._owner.claim_submission(self._root, receipt.view, receipt.ticket)
                committed = self._owner.commit_submission(
                    self._root, receipt.view, receipt.ticket)
            except SessionRefused:
                return False
            if (committed.state is not SubmissionState.COMMITTED
                    or any(x.state is not EntryState.UNSENT_OFFLINE
                           for x in committed.snapshot.entries)):
                raise AssertionError("Fake completion cannot prove execution")
            self._state = FakeDeliveryState.DELIVERED
            self.deliveries += 1
            if self._effects is not None:
                self._effects.fake_completions += 1
            return True
        finally:
            # Includes failed after_cancel, claim or commit. No active orphan.
            self._owner.revoke_submission(self._root, receipt.ticket)

    def cancel(self, receipt: FakeReceipt) -> bool:
        if receipt is not self._entry or self._state is not FakeDeliveryState.QUEUED:
            return False
        return self._retire_exact(receipt, cancel_schedule=True)

    def detach_schedule_for_terminal_close(self, receipt: FakeReceipt) -> bool:
        """Test-only Tk script cleanup WITHOUT revoking the owner ticket."""
        if receipt is not self._entry:
            return False
        pending, self._after_id = self._after_id, None
        if pending is not None:
            self._tkroot.after_cancel(pending)
        return True


class ProhibitedEffects:
    """Fail on forbidden attempts; distinguish never-completed real effects."""
    def __init__(self):
        self.counts = {}
        self.completed = {}
        self.fake_completions = 0

    def deny(self, category: str):
        def blocked(*args, **kwargs):
            self.counts[category] = self.counts.get(category, 0) + 1
            raise AssertionError("Prohibited phase 8.31 effect attempt")
        return blocked

    def observe(self, category: str, action):
        """Canary spy: proves attempted and completed effects are distinct."""
        def observed(*args, **kwargs):
            self.counts[category] = self.counts.get(category, 0) + 1
            value = action(*args, **kwargs)
            self.completed[category] = self.completed.get(category, 0) + 1
            return value
        return observed

    def patchers(self):
        import builtins
        import io
        import logging
        import os
        from pathlib import Path
        import socket
        import subprocess
        import tkinter
        import webbrowser

        real_import = builtins.__import__
        real_open = builtins.open
        real_io_open = io.open
        real_os_open = os.open
        def safe_open(original):
            def guarded(file, *args, **kwargs):
                mode = args[0] if args else kwargs.get("mode", "r")
                if type(mode) is not str or any(c in mode for c in "wax+"):
                    return self.deny("file-open-write")()
                return original(file, *args, **kwargs)
            return guarded
        def guarded_os_open(file, flags, *args, **kwargs):
            mutation = (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC
                        | os.O_APPEND | os.O_EXCL)
            if type(flags) is not int or flags & mutation:
                return self.deny("file-open-write")()
            return real_os_open(file, flags, *args, **kwargs)
        banned = ("openai", "win32cred", "keyring", "nayeon.brain",
                  "nayeon.actions", "nayeon.credential", "nayeon.credentials",
                  "nayeon.providers", "nayeon.provider", "nayeon.policy")
        def guarded_import(name, *args, **kwargs):
            if any(name == prefix or name.startswith(prefix + ".") for prefix in banned):
                return self.deny("forbidden-import")(name)
            return real_import(name, *args, **kwargs)
        patchers = [
            mock.patch.object(builtins, "__import__", guarded_import),
            mock.patch.object(builtins, "open", safe_open(real_open)),
            mock.patch.object(io, "open", safe_open(real_io_open)),
            mock.patch.object(os, "open", guarded_os_open),
            mock.patch.object(subprocess, "Popen", self.deny("process")),
            mock.patch.object(os, "system", self.deny("command")),
            mock.patch.object(socket, "socket", self.deny("network")),
            mock.patch.object(webbrowser, "open", self.deny("browser")),
            mock.patch.object(Path, "write_bytes", self.deny("file-write")),
            mock.patch.object(Path, "write_text", self.deny("file-write")),
            mock.patch.object(os, "replace", self.deny("replace")),
            mock.patch.object(os, "remove", self.deny("remove")),
            mock.patch.object(os, "unlink", self.deny("remove")),
            mock.patch.object(os, "rename", self.deny("replace")),
            mock.patch.object(os, "mkdir", self.deny("file-create")),
            mock.patch.object(os, "makedirs", self.deny("file-create")),
            mock.patch.object(Path, "mkdir", self.deny("file-create")),
            mock.patch.object(Path, "touch", self.deny("file-create")),
            mock.patch.object(tkinter.Misc, "clipboard_append", self.deny("clipboard")),
            mock.patch.object(tkinter.Misc, "clipboard_clear", self.deny("clipboard")),
            mock.patch.object(tkinter.Misc, "clipboard_get", self.deny("clipboard")),
            mock.patch.object(logging.Logger, "_log", self.deny("logging")),
        ]
        if hasattr(os, "startfile"):
            patchers.append(mock.patch.object(os, "startfile", self.deny("process")))
        return tuple(patchers)

    def native_patchers(self):
        """Test-owned wrappers around the exact already-reviewed profile seam.

        Read admission remains permitted. Any Save / native create intent must
        be visible as an attempt, even if a caller catches the denial.
        """
        from nayeon.desktop_alpha import presentation_profile_owner as owner
        original = owner.ProductionPresentationProfileOwner._admit_storage
        def guarded_admission(instance, native, generation, *, create):
            if create:
                return self.deny("native-profile-create")()
            return original(instance, native, generation, create=False)
        return (
            mock.patch.object(owner.ProductionPresentationProfileOwner,
                              "_admit_storage", guarded_admission),
            mock.patch.object(owner._PresentationProfileTransaction,
                              "save", self.deny("profile-save")),
        )

    def assert_clean(self):
        if self.counts or self.completed:
            raise AssertionError("Forbidden effect attempted or completed")
