"""Phase 8.23: human-initiated credential-operation review without execution.

Trusted parent injects an exact host. The panel can ONLY request or cancel a
non-secret pending review. Approval and candidate entry do not exist here.
"""
import tkinter as tk

from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
from nayeon.brain.onboarding_operation_advice import OnboardingOperation

_CHOICES = (
    (OnboardingOperation.TEST_CANDIDATE, "Review candidate validation"),
    (OnboardingOperation.TEST_STORED, "Review stored-key validation"),
    (OnboardingOperation.CONNECT, "Review connecting key"),
    (OnboardingOperation.REPLACE, "Review replacing key"),
    (OnboardingOperation.REMOVE, "Review deleting key"),
)


class FirstRunReviewWindow:
    """Only user buttons propose/cancel. No accept/approve/mutation callback."""

    def __init__(self, root: tk.Tk, *, host: TrustedCredentialOperationHost):
        if type(host) is not TrustedCredentialOperationHost:
            raise TypeError("An exact trusted host is required")
        self._host = host
        root.title("Nayeon | Credential operation review")
        root.geometry("650x490")
        root.minsize(520, 390)
        root.configure(bg="#101827")
        tk.Label(root, text="Nayeon - Credential review",
                 bg="#101827", fg="#f1f4fb",
                 font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=20, pady=(20, 8))
        tk.Label(root, text="Review only. No key entry, validation or operation approval.",
                 bg="#101827", fg="#adc1d6").pack(anchor="w", padx=20)
        self._status = tk.Label(root, text="No pending review",
                                bg="#101827", fg="#a5c9f7",
                                wraplength=600, justify="left")
        self._status.pack(anchor="w", padx=20, pady=(16, 12))
        self._options = []
        for operation, label in _CHOICES:
            button = tk.Button(root, text=label,
                               command=lambda chosen=operation: self.propose_from_button(chosen),
                               bg="#24384f", fg="#ffffff", relief="flat", padx=12, pady=7)
            button.pack(anchor="w", padx=20, pady=3)
            self._options.append(button)
        self._reject = tk.Button(root, text="Reject pending review",
                                 command=self.reject_from_button,
                                 bg="#863d51", fg="#ffffff", relief="flat",
                                 padx=12, pady=7)
        self._reject.pack(anchor="w", padx=20, pady=(14, 4))
        self._sync()

    def _sync(self):
        pending = self._host.has_pending is True
        for button in self._options:
            button.configure(state="disabled" if pending else "normal")
        self._reject.configure(state="normal" if pending else "disabled")

    def propose_from_button(self, operation: OnboardingOperation):
        if type(operation) is not OnboardingOperation or operation is OnboardingOperation.REVIEW:
            self._status.configure(text="Unsupported request. No operation started.")
            self._sync()
            return
        if self._host.has_pending:
            self._status.configure(text="Resolve the existing review first.")
            self._sync()
            return
        try:
            queued = self._host.request(operation)
            message = ("Review pending: " + " ".join(operation.value.split("_")) +
                       ". Execution is not available in this panel."
                       if queued is True and self._host.has_pending else
                       "Review unavailable. No operation started.")
        except Exception:
            message = "Review unavailable. No operation started."
        self._status.configure(text=message)
        self._sync()

    def reject_from_button(self):
        if not self._host.has_pending:
            return
        try:
            self._host.reject()
            message = "Review rejected. No operation submitted."
        except Exception:
            message = "Review could not be rejected safely."
        self._status.configure(text=message)
        self._sync()
