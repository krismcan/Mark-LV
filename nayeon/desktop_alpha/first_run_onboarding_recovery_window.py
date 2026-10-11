"""Phase 8.28.1 explicit trusted human recovery UI (no model route).

This panel performs a separate review and deliberate acknowledgement. It never
contacts a provider, mutates a credential, or treats journal READY as authority.
A trusted application composition supplies the exact shared controller.
"""
import tkinter as tk

from nayeon.brain.onboarding_recovery import (
    RecoveryReview, TrustedOnboardingRecoveryController,
)


class FirstRunOnboardingRecoveryWindow:
    def __init__(self, root: tk.Tk, *, controller: TrustedOnboardingRecoveryController):
        if type(controller) is not TrustedOnboardingRecoveryController:
            raise TypeError("Exact trusted recovery controller required")
        self._root = root
        self._controller = controller
        self._review: RecoveryReview | None = None
        self._closed = False
        root.title("Nayeon | Trusted onboarding reconciliation")
        root.geometry("740x490")
        root.configure(bg="#101827")
        tk.Label(root, text="Nayeon — onboarding reconciliation", fg="#f1f4fb",
                 bg="#101827", font=("Segoe UI", 17, "bold")).pack(
                     anchor="w", padx=20, pady=(18, 9))
        tk.Label(root, text="No credential, provider test or metadata change occurs here.",
                 fg="#adc1d6", bg="#101827").pack(anchor="w", padx=20)
        self._review_button = tk.Button(root, text="Inspect recovery state",
                                        command=self.review_from_button)
        self._review_button.pack(anchor="w", padx=20, pady=(16, 9))
        self._evidence = tk.Label(root, bg="#101827", fg="#adc1d6",
                                  justify="left", wraplength=690,
                                  text="No recovery evidence reviewed.")
        self._evidence.pack(anchor="w", padx=20, pady=5)
        self._ack = tk.BooleanVar(master=root, value=False)
        self._ack_button = tk.Checkbutton(
            root, variable=self._ack,
            text=("I inspected this installation, current metadata and any "
                  "uncertain operation. I accept this observable baseline. "
                  "Credential presence does not prove key correctness."),
            bg="#101827", fg="#f1f4fb", selectcolor="#101827",
            wraplength=670, justify="left")
        self._ack_button.pack(anchor="w", padx=20, pady=(12, 8))
        self._archive_ack = tk.BooleanVar(master=root, value=False)
        self._archive_button = tk.Checkbutton(
            root, variable=self._archive_ack,
            text=("I approve preserving the complete journal as an archive "
                  "and beginning a newly reviewed checkpoint (when required)."),
            bg="#101827", fg="#f1f4fb", selectcolor="#101827",
            wraplength=670, justify="left")
        self._archive_button.pack(anchor="w", padx=20, pady=(2, 6))
        self._approve = tk.Button(root, text="Confirm this reconciliation once",
                                  command=self.approve_from_button)
        self._approve.pack(anchor="w", padx=20, pady=4)
        self._reject = tk.Button(root, text="Reject review",
                                 command=self.reject_from_button)
        self._reject.pack(anchor="w", padx=20, pady=4)
        self._status = tk.Label(root, bg="#101827", fg="#a5c9f7",
                                wraplength=690, justify="left",
                                text="Admission blocked until this review is completed.")
        self._status.pack(anchor="w", padx=20, pady=10)
        root.protocol("WM_DELETE_WINDOW", self.close_from_window)
        self._sync()

    def _alive(self) -> bool:
        if self._closed:
            return False
        try:
            return self._root.winfo_exists() is True or self._root.winfo_exists() == 1
        except (tk.TclError, AttributeError):
            return False

    def _sync(self):
        if not self._alive():
            return
        pending = self._review is not None
        ready = self._controller.ready
        self._review_button.configure(state="disabled" if pending or ready else "normal")
        self._approve.configure(state="normal" if pending else "disabled")
        self._reject.configure(state="normal" if pending else "disabled")
        self._ack_button.configure(state="normal" if pending else "disabled")
        self._archive_button.configure(
            state="normal" if pending and self._review.archive_required else "disabled")

    def review_from_button(self):
        if not self._alive():
            return
        if self._review is not None or self._controller.ready:
            return
        self._ack.set(False)
        self._archive_ack.set(False)
        try:
            review = self._controller.request_reconciliation()
        except Exception:
            self._status.configure(text="Reconciliation unavailable. Protected operations remain blocked.")
            self._sync()
            return
        self._review = review
        summary = (
            f"Previous journal state: {review.journal_state.value}\n"
            f"Provider: {review.provider or 'not configured'}\n"
            f"Model: {review.model or 'not configured'}\n"
            f"Credential reference: {review.credential_reference or 'none'}\n"
            f"Credential presence: {review.credential_presence} (not key validation)\n"
            f"Legacy marker: {'present' if review.legacy_marker_present else 'absent'}\n"
            f"Earlier archive: {'present' if review.archive_present else 'none detected'}\n"
            f"Archive needed now: {'YES — extra acknowledgement required' if review.archive_required else 'no'}\n"
            f"Uncertain operation: {'YES — inspect before accepting' if review.operation_uncertain else 'none detected'}"
        )
        self._evidence.configure(text=summary)
        self._status.configure(text="Review the evidence, then deliberately acknowledge or reject.")
        self._sync()

    def approve_from_button(self):
        if not self._alive():
            return
        review = self._review
        if review is None:
            return
        if self._ack.get() is not True:
            self._status.configure(text="Explicit evidence acknowledgement is required.")
            return
        if review.archive_required and self._archive_ack.get() is not True:
            self._status.configure(text="Journal archive requires separate acknowledgement.")
            return
        self._review = None
        self._ack.set(False)
        archived_ok = self._archive_ack.get()
        self._archive_ack.set(False)
        try:
            approved = self._controller.approve_reconciliation(
                human_approved=True, fingerprint=review.fingerprint,
                archive_acknowledged=archived_ok)
        except Exception:
            approved = False
        self._status.configure(text=(
            "Fresh trusted admission established for this continuously owned mutex tenure."
            if approved else
            "Reconciliation not verified. All protected operations remain blocked."
        ))
        self._sync()

    def reject_from_button(self):
        if not self._alive():
            return
        review = self._review
        self._review = None
        self._ack.set(False)
        self._archive_ack.set(False)
        if review is not None:
            try:
                self._controller.approve_reconciliation(
                    human_approved=False, fingerprint=review.fingerprint)
            except Exception:
                pass
        self._status.configure(text="Review rejected. No admission granted.")
        self._sync()

    def close_from_window(self):
        if not self._alive():
            self._closed = True
            self._review = None
            return
        self.reject_from_button()
        self._closed = True
        # A reconciled tenure belongs to the management host, not this dialog.
        # Closing the review window must not revoke the owner's admission.
        if not self._controller.ready:
            try:
                if self._controller._ctx is not None:
                    self._controller.close()
            except Exception:
                pass
        self._root.destroy()
