"""P258 default read-only Windows-user BYOK status (OFFLINE, no provider probe).

Run explicitly: python -m nayeon.desktop_alpha.local_byok_window
The normal offline assistant startup remains untouched. On import or launch,
there is no Windows Credential Manager access until a person clicks Refresh.
Default mutation controls are disabled pending a trusted service-only owner.
No saved credential is read back into this window.
"""

from __future__ import annotations

import sys
import queue
import threading
import time
import tkinter as tk

from nayeon.desktop_alpha.byok_native_service_observer import (
    NativeServiceObserver, NativeStatus,
)
from nayeon.desktop_alpha.byok_native_synthetic_request import (
    NativeSyntheticRequester, SyntheticRequestStatus,
)

from nayeon.brain.local_byok_user_scope import (
    LocalByokController, LocalByokOperation, LocalByokOutcome,
    LocalByokPresence, compose_user_scope_local_byok,
)
from nayeon.secrets.contracts import SecretValue


_READ_ONLY_TEXT = (
    "READ-ONLY STATUS: waiting for a qualified trusted Windows service-only "
    "credential owner. Save, replace and delete are unavailable. "
    "Refresh checks slot presence only; no stored key is shown."
)


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
        self._observing = False
        self._observer_disabled = False
        self._observation_worker = None
        self._observation_deadline = 0.0
        self._observation_after = None
        self._observation_results = queue.Queue(maxsize=1)
        self._synthetic_attempted = False
        self._synthetic_pending = False
        self._synthetic_worker = None
        self._synthetic_deadline = 0.0
        self._synthetic_after = None
        self._synthetic_results = None

        root.title("Nayeon | Local Windows BYOK (" + (
            "offline setup" if controller.mutation_available else "read-only status"
        ) + ")")
        root.geometry("700x700")
        root.minsize(610, 670)
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
        self._mode_notice = tk.Label(
            root, text=(
                "OFFLINE SETUP: no provider connection or validation, "
                "and no key is saved on launch. A stored slot is not a usable connection."
                if controller.mutation_available else _READ_ONLY_TEXT
            ),
            bg="#101827", fg="#f2d5a2", wraplength=640, justify="left",
        )
        self._mode_notice.pack(anchor="w", padx=22, pady=(6, 14))

        self._refresh = tk.Button(
            root, text="Refresh local slot presence (never show key)",
            command=self.refresh_from_button,
        )
        self._refresh.pack(anchor="w", padx=22, pady=(0, 9))
        self._observe = tk.Button(
            root, text="Observe native custody service status (read-only)",
            command=self.observe_native_from_button,
        )
        self._observe.pack(anchor="w", padx=22, pady=(0, 5))
        self._native_status = tk.Label(
            root, text="not observed; release HOLD", bg="#101827",
            fg="#f2d5a2", wraplength=640, justify="left",
        )
        self._native_status.pack(anchor="w", padx=22, pady=(0, 9))
        self._synthetic = tk.Button(
            root, text="Test synthetic service denial (no key)",
            command=self.synthetic_request_from_button,
        )
        self._synthetic.pack(anchor="w", padx=22, pady=(0, 5))
        self._synthetic_status = tk.Label(
            root, text="not requested; release HOLD", bg="#101827",
            fg="#f2d5a2", wraplength=640, justify="left",
        )
        self._synthetic_status.pack(anchor="w", padx=22, pady=(0, 9))
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
        if not self._controller.mutation_available:
            self._entry.configure(state="disabled")

    def _sync(self) -> None:
        if not self._live():
            return
        if not self._controller.mutation_available:
            for widget in (*self._choices, self._entry, self._confirm,
                           self._delete_ack, self._approve, self._reject):
                widget.configure(state="disabled")
            self._refresh.configure(state="disabled" if self._busy else "normal")
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

    def observe_native_from_button(self) -> None:
        if not self._live() or self._observing or self._observer_disabled:
            return
        self._observing = True
        self._observation_deadline = time.monotonic() + 1.5
        # Each request owns its queue. A late worker cannot feed a later probe.
        self._observation_results = queue.Queue(maxsize=1)
        self._observe.configure(state="disabled")
        self._native_status.configure(text="Observing read-only status; release HOLD; no keys or approval.")
        results = self._observation_results

        def worker():
            # Worker never touches Tk, controller, keys, or mutation state.
            try:
                result = NativeServiceObserver().observe()
            except Exception:
                result = NativeStatus.UNAVAILABLE
            results.put_nowait(result)

        try:
            self._observation_worker = threading.Thread(target=worker, daemon=True)
            self._observation_worker.start()
        except Exception:
            results.put_nowait(NativeStatus.UNAVAILABLE)
        self._observation_after = self._root.after(25, self._poll_native_observation)

    def _poll_native_observation(self) -> None:
        self._observation_after = None
        if not self._live() or not self._observing:
            return
        result = NativeStatus.UNAVAILABLE
        if time.monotonic() < self._observation_deadline:
            try:
                result = self._observation_results.get_nowait()
            except queue.Empty:
                self._observation_after = self._root.after(25, self._poll_native_observation)
                return
        # A posted result cannot start a replacement while its worker is alive.
        # A timeout permanently latches this window if native cleanup stalls.
        if self._observation_worker is not None and self._observation_worker.is_alive():
            self._observer_disabled = True
        self._observing = False
        self._native_status.configure(text=(
            "UNTRUSTED_HOLD: fixed denial observed; response is untrusted; peer is not attested. "
            "No recovery state is verified. Release HOLD; no keys or approval. "
            "Do not enter or retry credentials. Seek qualified service recovery review."
            if result is NativeStatus.UNTRUSTED_HOLD else
            "Native status unavailable; cause unknown. No recovery state is verified. "
            "Release HOLD; no keys or approval. Do not enter or retry credentials. "
            "Seek qualified service recovery review."
        ))
        self._observe.configure(state="disabled" if self._observer_disabled else "normal")

    def synthetic_request_from_button(self) -> None:
        if not self._live() or self._synthetic_attempted:
            return
        # The service accepts one connection per lifetime. Never retry in this
        # window, including unavailable, start failure, timeout or late cleanup.
        self._synthetic_attempted = True
        self._synthetic_pending = True
        self._synthetic_deadline = time.monotonic() + 1.5
        self._synthetic_results = queue.Queue(maxsize=1)
        self._synthetic.configure(state="disabled")
        self._synthetic_status.configure(text="Testing synthetic denial; release HOLD; no keys or approval.")
        results = self._synthetic_results

        def worker():
            try:
                result = NativeSyntheticRequester().request()
            except Exception:
                result = SyntheticRequestStatus.UNAVAILABLE
            results.put_nowait(result)

        try:
            self._synthetic_worker = threading.Thread(target=worker, daemon=True)
            self._synthetic_worker.start()
        except Exception:
            results.put_nowait(SyntheticRequestStatus.UNAVAILABLE)
        self._synthetic_after = self._root.after(25, self._poll_synthetic_request)

    def _poll_synthetic_request(self) -> None:
        self._synthetic_after = None
        if not self._live() or not self._synthetic_pending:
            return
        result = SyntheticRequestStatus.UNAVAILABLE
        if time.monotonic() < self._synthetic_deadline:
            try:
                result = self._synthetic_results.get_nowait()
            except queue.Empty:
                self._synthetic_after = self._root.after(25, self._poll_synthetic_request)
                return
        self._synthetic_pending = False
        self._synthetic_results = None  # Late worker retains only its old queue.
        self._synthetic_status.configure(text=(
            "UNTRUSTED_HOLD: synthetic denial received; response is untrusted; peer is not attested. "
            "No recovery state is verified. Release HOLD; no keys or approval. "
            "Do not enter or retry credentials. Seek qualified service recovery review."
            if result is SyntheticRequestStatus.UNTRUSTED_HOLD else
            "Synthetic request UNAVAILABLE; cause unknown. No recovery state is verified. "
            "Release HOLD; no keys or approval. Do not enter or retry credentials. "
            "Seek qualified service recovery review."
        ))

    def review_from_button(self, operation: LocalByokOperation) -> None:
        if not self._controller.mutation_available:
            return
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
        if not self._controller.mutation_available:
            return
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
        self._synthetic_pending = False
        self._synthetic_results = None
        if self._synthetic_after is not None:
            self._root.after_cancel(self._synthetic_after)
            self._synthetic_after = None
        self._observing = False
        if self._observation_after is not None:
            self._root.after_cancel(self._observation_after)
            self._observation_after = None
        try:
            self._root.destroy()
        except (tk.TclError, AttributeError):
            pass


def main() -> None:
    """Both fixed source child and manual module use the presence-only factory."""
    if sys.platform != "win32":
        raise SystemExit("Local BYOK Windows setup is available only on Windows.")
    root = tk.Tk()
    LocalByokWindow(root, controller=compose_user_scope_local_byok())
    root.mainloop()


if __name__ == "__main__":
    main()
