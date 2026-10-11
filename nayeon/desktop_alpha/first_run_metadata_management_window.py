"""Phase 8.28: human-button-only trusted OpenAI metadata save/clear UI.

Metadata only. No key entry, backend, validator, provider SDK, network or model
route. A trusted parent injects one bounded metadata confirmation host.
"""
import tkinter as tk
from nayeon.desktop_alpha.first_run_onboarding_recovery_window import FirstRunOnboardingRecoveryWindow

from nayeon.brain.onboarding_metadata_commit import (
    TrustedMetadataCommitHost, MetadataCommitOutcome, MetadataCommitReceipt,
    MetadataOperation,
)


_MESSAGES = {
    MetadataCommitOutcome.VERIFIED: (
        "Metadata write verified by immediate file re-read. This does not "
        "validate any API key, model entitlement or cross-store transaction."
    ),
    MetadataCommitOutcome.REFUSED: "Metadata action refused. No new write authorised.",
    MetadataCommitOutcome.EXPIRED: "Review expired. Re-observe and review again.",
    MetadataCommitOutcome.BUSY: "Another Nayeon onboarding action is running. Review again later.",
    MetadataCommitOutcome.CONFLICT: "Metadata changed during review. Re-observe before retry.",
    MetadataCommitOutcome.RECOVERY_REQUIRED: (
        "Recovery required. A write may have changed state. Inspect the "
        "metadata and recovery marker manually; never retry automatically."
    ),
    MetadataCommitOutcome.UNAVAILABLE: "Metadata unavailable. No success claimed.",
}


class FirstRunMetadataManagementWindow:
    """Strictly separate explicit review/approve UI; no direct file operations."""

    def __init__(self, root: tk.Tk, *, host: TrustedMetadataCommitHost) -> None:
        if type(host) is not TrustedMetadataCommitHost:
            raise TypeError("Exact trusted metadata host required")
        self._root = root
        self._host = host
        self._owner_token: str | None = None
        self._closed = False
        self._operation: MetadataOperation | None = None
        self._ticket: str | None = None
        self._busy = False
        root.title("Nayeon | Provider metadata")
        root.geometry("700x420")
        root.minsize(540, 360)
        root.configure(bg="#101827")
        tk.Label(root, text="Nayeon - OpenAI metadata", bg="#101827",
                 fg="#f1f4fb", font=("Segoe UI", 17, "bold")).pack(
                     anchor="w", padx=20, pady=(18, 8))
        tk.Label(root, bg="#101827", fg="#adc1d6",
                 text="No key is read, saved, removed or tested in this panel.").pack(
                     anchor="w", padx=20)
        tk.Label(root, bg="#101827", fg="#adc1d6",
                 text="Model identifier (not an API key):").pack(
                     anchor="w", padx=20, pady=(14, 3))
        self._recovery_dialog = None
        self._recovery_button = tk.Button(
            root, text="Inspect and reconcile onboarding safety",
            command=self.open_reconciliation_from_button)
        self._recovery_button.pack(anchor="w", padx=20, pady=4)
        self._model = tk.Entry(root, width=52)
        self._model.pack(anchor="w", padx=20, pady=(0, 10))
        self._save = tk.Button(root, text="Review saving OpenAI model settings",
                               command=self.review_save_from_button)
        self._save.pack(anchor="w", padx=20, pady=3)
        self._clear = tk.Button(root, text="Review clearing provider settings ONLY",
                                command=self.review_clear_from_button)
        self._clear.pack(anchor="w", padx=20, pady=3)
        self._clear_acknowledged = tk.BooleanVar(master=root, value=False)
        self._clear_ack = tk.Checkbutton(
            root, variable=self._clear_acknowledged,
            text="I confirm: clear provider settings, but KEEP the saved API key",
            bg="#101827", fg="#f1f4fb", selectcolor="#101827")
        self._clear_ack.pack(anchor="w", padx=20, pady=(10, 6))
        self._approve = tk.Button(root, text="Approve this metadata change once",
                                  command=self.approve_from_button)
        self._approve.pack(anchor="w", padx=20, pady=3)
        self._reject = tk.Button(root, text="Reject review",
                                 command=self.reject_from_button)
        self._reject.pack(anchor="w", padx=20, pady=3)
        self._status = tk.Label(root, text="No pending metadata review",
                                bg="#101827", fg="#a5c9f7",
                                wraplength=650, justify="left")
        self._status.pack(anchor="w", padx=20, pady=(12, 8))
        root.protocol("WM_DELETE_WINDOW", self.close_from_window)
        # Bind ownership only AFTER every widget/callback is constructed;
        # a constructor failure must not strand a path-wide owner token.
        self._owner_token = self._host.claim_ui_owner()
        self._sync()

    def _sync(self) -> None:
        pending = (self._ticket is not None and self._operation is not None
                   and self._host.pending_ui_operation(ticket=self._ticket, owner=self._owner_token) is self._operation)
        self._model.configure(state="disabled" if pending or self._busy else "normal")
        self._save.configure(state="disabled" if pending or self._busy else "normal")
        self._clear.configure(state="disabled" if pending or self._busy else "normal")
        self._approve.configure(state="normal" if pending and not self._busy else "disabled")
        self._reject.configure(state="normal" if pending and not self._busy else "disabled")
        self._clear_ack.configure(
            state="normal" if pending and self._operation is MetadataOperation.CLEAR
            and not self._busy else "disabled")

    def _review(self, operation: MetadataOperation) -> None:
        if self._closed:
            return
        if self._owner_token is None or not self._host.has_ui_owner(owner=self._owner_token):
            self._owner_token = self._host.claim_ui_owner()
        if not self._host.has_ui_owner(owner=self._owner_token):
            self._status.configure(text="Another window owns this metadata session.")
            return
        if self._busy or self._host.has_pending or self._operation is not None or self._ticket is not None:
            return
        self._clear_acknowledged.set(False)
        try:
            if operation is MetadataOperation.SAVE:
                proposed, ticket = self._host.request_ui_save(self._model.get(), owner=self._owner_token)
            elif operation is MetadataOperation.CLEAR:
                proposed, ticket = self._host.request_ui_clear(owner=self._owner_token)
            else:
                return
        except Exception:
            proposed = None
        if (type(proposed) is MetadataCommitReceipt and
                proposed.outcome is MetadataCommitOutcome.PENDING and
                self._host.has_pending):
            self._operation = operation
            self._ticket = ticket
            message = (
                "Clear review pending. Tick the explicit metadata-only acknowledgement, "
                "then approve. The saved API key will NOT be removed."
                if operation is MetadataOperation.CLEAR else
                "Save review pending. Approve separately to write canonical "
                "OpenAI provider/model metadata; this does not save an API key."
            )
        else:
            self._operation = None
            self._ticket = None
            message = self._message(proposed)
        self._status.configure(text=message)
        self._sync()

    def review_save_from_button(self) -> None:
        self._review(MetadataOperation.SAVE)

    def review_clear_from_button(self) -> None:
        self._review(MetadataOperation.CLEAR)

    @staticmethod
    def _message(receipt: object) -> str:
        if type(receipt) is not MetadataCommitReceipt:
            return "Metadata unavailable. No write confirmed."
        return _MESSAGES.get(receipt.outcome, "Metadata unavailable. No write confirmed.")

    def approve_from_button(self) -> None:
        if self._closed:
            return
        if (self._busy or self._ticket is None or self._operation is None or
                not self._host.has_ui_owner(owner=self._owner_token)):
            return
        if self._host.pending_ui_operation(ticket=self._ticket, owner=self._owner_token) is not self._operation:
            self._operation = None
            self._ticket = None
            self._clear_acknowledged.set(False)
            self._status.configure(text="Review changed in another window. No action approved.")
            self._sync()
            return
        if (self._operation is MetadataOperation.CLEAR and
                self._clear_acknowledged.get() is not True):
            self._status.configure(text="Explicit metadata-only clear acknowledgement required.")
            return
        self._busy = True
        try:
            receipt = self._host.approve_ui(
                ticket=self._ticket, operation=self._operation, human_approved=True,
                clear_acknowledged=self._clear_acknowledged.get() is True,
                owner=self._owner_token)
            message = self._message(receipt)
        except Exception:
            try:
                if self._ticket is not None:
                    self._host.reject_ui(ticket=self._ticket, owner=self._owner_token)
            except Exception:
                pass
            message = "Result unavailable. Re-observe state before retry."
        finally:
            self._busy = False
            self._operation = None
            self._ticket = None
            self._clear_acknowledged.set(False)
        self._status.configure(text=message)
        self._sync()

    def reject_from_button(self) -> None:
        if self._closed or self._busy:
            return
        try:
            if self._ticket is not None:
                self._host.reject_ui(ticket=self._ticket, owner=self._owner_token)
        except Exception:
            pass
        self._ticket = None
        self._operation = None
        self._clear_acknowledged.set(False)
        self._status.configure(text="Review rejected. No metadata write requested.")
        self._sync()

    def open_reconciliation_from_button(self):
        """Only a user click opens a fresh trusted recovery review."""
        if self._closed or self._busy:
            return
        if self._owner_token is None or not self._host.has_ui_owner(owner=self._owner_token):
            self._owner_token = self._host.claim_ui_owner()
        if (self._recovery_dialog is not None and
                self._recovery_dialog._root.winfo_exists()):
            return
        self._recovery_dialog = None
        if not self._host.has_ui_owner(owner=self._owner_token):
            self._status.configure(text="Another window owns this metadata session.")
            return
        ctrl = self._host.recovery_controller
        if ctrl.ready:
            self._status.configure(text="This onboarding session is already reconciled.")
            return
        try:
            window = tk.Toplevel(self._root)
            self._recovery_dialog = FirstRunOnboardingRecoveryWindow(
                window, controller=ctrl)
        except Exception:
            self._recovery_dialog = None
            self._status.configure(text="Recovery review unavailable. Protected changes remain blocked.")

    def close_from_window(self) -> None:
        if self._closed or self._busy:
            return
        self.reject_from_button()
        self._closed = True
        if self._host.release_ui_owner(owner=self._owner_token):
            try:
                recovery = self._host.recovery_controller
                if recovery._ctx is not None:
                    recovery.close()
            except Exception:
                pass
        self._owner_token = None
        self._root.destroy()
