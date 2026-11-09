"""P132 manual Windows-user local BYOK window (OFFLINE, no provider probe).

Run explicitly: python -m nayeon.desktop_alpha.local_byok_window
The normal offline assistant startup remains untouched. On import or launch,
there is no Windows Credential Manager access until a person clicks Refresh
or a Review button. No saved credential is read back into this window.
"""

from __future__ import annotations

import sys
import tkinter as tk

from nayeon.brain.local_byok_user_scope import (
    LocalByokController, LocalByokOperation, LocalByokOutcome,
    LocalByokPresence, compose_user_scope_local_byok,
)
from nayeon.secrets.contracts import SecretValue


_PRESENCE_TEXT = {
    LocalByokPresence.NOT_STORED:
        "No OpenAI credential slot detected for this Windows user.",
    LocalByokPresence.PRESENT_UNVALIDATED:
        "A key is present in this Windows user's Credential Manager. It has NOT been validated.",
    LocalByokPresence.UNAVAILABLE:
        "Windows credential status is unavailable; no saved key was read.",
    LocalByokPresence.RECONCILIATION_REQUIRED:
        "Prior outcome is uncertain. Inspect Windows Credential Manager before any retry.",
}

_OUTCOME_TEXT = {
    LocalByokOutcome.SUBMITTED_UNVALIDATED:
        "Submitted to Windows Credential Manager. A slot exists, but key content and provider validity are NOT confirmed.",
    LocalByokOutcome.SUBMITTED_REMOVAL:
        "Windows reported deletion and slot absence. Reopen and inspect the current user credential state.",
    LocalByokOutcome.REFUSED:
        "Approval refused or incomplete. No operation was submitted.",
    LocalByokOutcome.CONFLICT:
        "Credential slot presence changed since review. No operation was submitted. Refresh before retrying.",
    LocalByokOutcome.BUSY:
        "Another cooperating Nayeon process is busy. No operation was submitted.",
    LocalByokOutcome.RECONCILIATION_REQUIRED:
        "Outcome uncertain. The credential may have changed. Do not retry without manual reconciliation.",
}

_CHOICES = (
    (LocalByokOperation.SAVE, "Review save new key"),
    (LocalByokOperation.REPLACE, "Review replace existing key"),
    (LocalByokOperation.REMOVE, "Review delete existing key"),
)


class LocalByokWindow:
    """UI-only facade; exact local controller injected by trusted entry."""

    def __init__(self, root: tk.Tk, *, controller: LocalByokController):
        if type(controller) is not LocalByokController:
            raise TypeError("Exact trusted local BYOK controller required")
        self._root = root
        self._controller = controller
        self._review = None
        self._busy = False
        self._closed = False

        root.title("Nayeon | Local Windows BYOK (offline setup)")
        root.geometry("700x555")
        root.minsize(610, 510)
        root.configure(bg="#101827")
        tk.Label(
            root, text="OpenAI key · Local Windows storage", bg="#101827",
            fg="#eef4fc", font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", padx=22, pady=(18, 8))
        tk.Label(
            root, text=("Only your current Windows account's Credential Manager. "
                        "This does not install a privileged service."),
            bg="#101827", fg="#c9d7e6", wraplength=640, justify="left",
        ).pack(anchor="w", padx=22)
        tk.Label(
            root, text=("OFFLINE SETUP: no provider connection or validation, "
                        "and no key is saved on launch. A stored slot is not a usable connection."),
            bg="#101827", fg="#f2d5a2", wraplength=640, justify="left",
        ).pack(anchor="w", padx=22, pady=(6, 14))

        self._refresh = tk.Button(
            root, text="Refresh local slot presence (never show key)",
            command=self.refresh_from_button,
        )
        self._refresh.pack(anchor="w", padx=22, pady=(0, 9))
        self._choices = []
        for operation, title in _CHOICES:
            button = tk.Button(
                root, text=title, command=lambda chosen=operation:
                    self.review_from_button(chosen),
            )
            button.pack(anchor="w", padx=22, pady=3)
            self._choices.append(button)

        tk.Label(
            root, text="Candidate key (only for Save or Replace)",
            bg="#101827", fg="#c9d7e6",
        ).pack(anchor="w", padx=22, pady=(12, 4))
        self._entry = tk.Entry(root, show="*", exportselection=False, width=60)
        self._entry.pack(anchor="w", padx=22)
        for event in (
            "<<Copy>>", "<<Cut>>", "<Control-c>", "<Control-x>",
            "<Control-C>", "<Control-X>",
        ):
            self._entry.bind(event, self._prevent_copy)

        self._confirmed = tk.BooleanVar(master=root, value=False)
        self._confirm = tk.Checkbutton(
            root, variable=self._confirmed, bg="#101827", fg="#eef4fc",
            selectcolor="#101827",
            text="I approve this one local operation without provider validation",
        )
        self._confirm.pack(anchor="w", padx=22, pady=(12, 3))
        self._delete_checked = tk.BooleanVar(master=root, value=False)
        self._delete_ack = tk.Checkbutton(
            root, variable=self._delete_checked, bg="#101827", fg="#eef4fc",
            selectcolor="#101827",
            text="I understand deletion of my stored key is destructive",
        )
        self._delete_ack.pack(anchor="w", padx=22, pady=(3, 8))

        self._approve = tk.Button(
            root, text="Approve selected operation once",
            command=self.approve_from_button,
        )
        self._approve.pack(anchor="w", padx=22, pady=3)
        self._reject = tk.Button(
            root, text="Reject and clear", command=self.reject_from_button,
        )
        self._reject.pack(anchor="w", padx=22, pady=3)
        self._status = tk.Label(
            root, text="No access has been made to Credential Manager.",
            bg="#101827", fg="#a5c9f7", justify="left", wraplength=650,
        )
        self._status.pack(anchor="w", padx=22, pady=(13, 5))

        root.protocol("WM_DELETE_WINDOW", self.close_from_window)
        self._sync()

    @staticmethod
    def _prevent_copy(_event):
        return "break"

    def _live(self) -> bool:
        if self._closed:
            return False
        try:
            return bool(self._root.winfo_exists())
        except (tk.TclError, AttributeError):
            return False

    def _clear(self) -> None:
        # Tk disabled Entry cannot be deleted without a temporary enable.
        self._entry.configure(state="normal")
        self._entry.delete(0, tk.END)

    def _sync(self) -> None:
        if not self._live():
            return
        pending = self._review is not None
        for button in self._choices:
            button.configure(state="disabled" if pending or self._busy else "normal")
        self._refresh.configure(state="disabled" if pending or self._busy else "normal")
        self._approve.configure(state="normal" if pending and not self._busy else "disabled")
        self._reject.configure(state="normal" if pending and not self._busy else "disabled")
        accepts_key = pending and self._review.operation in (
            LocalByokOperation.SAVE, LocalByokOperation.REPLACE,
        )
        self._entry.configure(state="normal" if accepts_key and not self._busy else "disabled")
        self._confirm.configure(state="normal" if pending and not self._busy else "disabled")
        self._delete_ack.configure(
            state="normal" if pending and not self._busy
            and self._review.operation is LocalByokOperation.REMOVE else "disabled",
        )

    def refresh_from_button(self) -> None:
        if not self._live() or self._busy or self._review is not None:
            return
        status = self._controller.inspect_presence()
        if self._live():
            self._status.configure(
                text=_PRESENCE_TEXT.get(
                    status, "Status unavailable; do not assume a key exists.",
                ),
            )

    def review_from_button(self, operation: LocalByokOperation) -> None:
        if (not self._live() or self._busy or self._review is not None
                or type(operation) is not LocalByokOperation):
            return
        self._clear()
        self._confirmed.set(False)
        self._delete_checked.set(False)
        try:
            review = self._controller.begin(operation)
        except Exception:
            review = None
        if not self._live():
            if review is not None:
                self._controller.reject(review)
            return
        self._review = review
        if review is None:
            message = "Operation not available in current slot state. No key was changed."
        elif operation is LocalByokOperation.REMOVE:
            message = ("Review DELETE. Tick both confirmations and click Approve once. "
                       "Nothing has been deleted yet.")
        else:
            message = ("Review " + operation.value.upper() +
                       ". Enter a key, tick confirmation, and click Approve once. "
                       "No provider connection will be attempted.")
        self._status.configure(text=message)
        self._sync()

    def approve_from_button(self) -> None:
        if not self._live() or self._review is None or self._busy:
            return
        review = self._review
        if self._confirmed.get() is not True:
            self._status.configure(text="Explicit confirmation is required. Nothing submitted.")
            return
        if (review.operation is LocalByokOperation.REMOVE
                and self._delete_checked.get() is not True):
            self._status.configure(text="Deletion acknowledgement required. Nothing submitted.")
            return
        candidate = None
        raw = None
        self._busy = True
        try:
            if review.operation in (LocalByokOperation.SAVE, LocalByokOperation.REPLACE):
                raw = self._entry.get()
                self._clear()
                candidate = SecretValue(raw)
                raw = None
            else:
                self._clear()
            if not self._live():
                raise RuntimeError("Window no longer live")
            outcome = self._controller.approve(
                review, confirmed=True, candidate=candidate,
                deletion_acknowledged=(
                    self._delete_checked.get() is True
                    if review.operation is LocalByokOperation.REMOVE else False
                ),
            )
            message = _OUTCOME_TEXT.get(
                outcome, "Unrecognised response. Reconcile before retrying.",
            )
        except Exception:
            self._controller.reject(review)
            message = "Request unavailable. No successful outcome is claimed."
        finally:
            raw = None
            candidate = None
            if self._live():
                try:
                    self._clear()
                    self._confirmed.set(False)
                    self._delete_checked.set(False)
                except tk.TclError:
                    pass
            self._review = None
            self._busy = False
        if self._live():
            self._status.configure(text=message)
            self._sync()

    def reject_from_button(self) -> None:
        if not self._live() or self._busy:
            return
        if self._review is not None:
            self._controller.reject(self._review)
        self._review = None
        self._clear()
        self._confirmed.set(False)
        self._delete_checked.set(False)
        self._status.configure(text="Review rejected and candidate entry cleared.")
        self._sync()

    def close_from_window(self) -> None:
        if self._closed or self._busy:
            return
        self.reject_from_button()
        self._closed = True
        try:
            self._root.destroy()
        except (tk.TclError, AttributeError):
            pass


def main() -> None:
    """Explicit manual launch only; no default app/startup integration."""
    if sys.platform != "win32":
        raise SystemExit("Local BYOK Windows setup is available only on Windows.")
    root = tk.Tk()
    LocalByokWindow(root, controller=compose_user_scope_local_byok())
    root.mainloop()


if __name__ == "__main__":
    main()
