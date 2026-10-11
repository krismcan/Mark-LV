"""Phase 8.25: explicitly consented candidate validation from a trusted Tk host.

This isolated panel can ONLY request and approve TEST_CANDIDATE. It never
constructs a credential backend, writes a secret, selects a provider, or
permits model-originated approval. A real validator may contact a provider
only after a deliberate human button click; tests must inject fakes.

Tk masking and clearing are best-effort UI protections, not Python-memory
erasure, OS clipboard isolation, or strong process-boundary security.
"""
import tkinter as tk

from nayeon.brain.credential_operation_host import (
    CredentialHostOutcome, CredentialHostResult, TrustedCredentialOperationHost,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
from nayeon.secrets.contracts import SecretValue


_MESSAGES = {
    CredentialHostOutcome.SUBMITTED: "Validation returned valid. Credential was not saved.",
    CredentialHostOutcome.INVALID: "Validation rejected the candidate. Credential was not saved.",
    CredentialHostOutcome.INDETERMINATE: "Validation inconclusive. Credential was not saved.",
    CredentialHostOutcome.NOT_APPLIED: "Validation not applied.",
    CredentialHostOutcome.BLOCKED: "Validation blocked or review expired. No credential saved.",
}


class FirstRunCredentialValidationWindow:
    """Host-owned, manual test-only entry surface; no storage operations."""

    def __init__(self, root: tk.Tk, *, host: TrustedCredentialOperationHost):
        if type(host) is not TrustedCredentialOperationHost:
            raise TypeError("An exact trusted credential operation host is required")
        self._root = root
        self._host = host
        self._busy = False
        root.title("Nayeon | Validate a candidate credential")
        root.geometry("630x360")
        root.minsize(490, 290)
        root.configure(bg="#101827")
        tk.Label(root, text="Nayeon - Candidate validation", bg="#101827",
                 fg="#f1f4fb", font=("Segoe UI", 17, "bold")).pack(
                     anchor="w", padx=20, pady=(20, 8))
        tk.Label(root,
                 text="Validation is optional. No key is tested or saved on launch.",
                 bg="#101827", fg="#adc1d6").pack(anchor="w", padx=20)
        tk.Label(root, text="Enter credential only after selecting Review validation.",
                 bg="#101827", fg="#adc1d6").pack(anchor="w", padx=20, pady=(14, 4))
        self._entry = tk.Entry(root, show="*", exportselection=False, width=52)
        self._entry.pack(anchor="w", padx=20, pady=(0, 12))
        # Prevent ordinary copy/cut shortcuts for this field; this does not
        # guarantee clipboard isolation against a malicious local process.
        for sequence in ("<<Copy>>", "<<Cut>>", "<Control-c>", "<Control-x>",
                         "<Control-C>", "<Control-X>"):
            self._entry.bind(sequence, self._prevent_copy)
        self._status = tk.Label(root, text="No review pending", bg="#101827",
                                fg="#a5c9f7", wraplength=575, justify="left")
        self._status.pack(anchor="w", padx=20, pady=(0, 12))
        self._request = tk.Button(root, text="Review validation",
                                  command=self.request_from_button)
        self._request.pack(anchor="w", padx=20, pady=3)
        self._approve = tk.Button(root, text="Approve one validation",
                                  command=self.approve_from_button)
        self._approve.pack(anchor="w", padx=20, pady=3)
        self._reject = tk.Button(root, text="Reject and clear",
                                 command=self.reject_from_button)
        self._reject.pack(anchor="w", padx=20, pady=3)
        root.protocol("WM_DELETE_WINDOW", self.close_from_window)
        self._sync()

    @staticmethod
    def _prevent_copy(event):
        return "break"

    def _clear(self):
        # Tk refuses Entry.delete when disabled; briefly enable before clearing.
        # Callbacks run synchronously on Tk's owning thread.
        self._entry.configure(state="normal")
        self._entry.delete(0, tk.END)

    def _sync(self):
        pending = self._host.has_pending is True
        self._request.configure(state="disabled" if pending or self._busy else "normal")
        self._approve.configure(state="normal" if pending and not self._busy else "disabled")
        self._reject.configure(state="normal" if pending and not self._busy else "disabled")
        self._entry.configure(state="normal" if pending and not self._busy else "disabled")

    def request_from_button(self):
        if self._busy or self._host.has_pending:
            return
        self._clear()
        try:
            proposed = self._host.request(OnboardingOperation.TEST_CANDIDATE)
        except Exception:
            proposed = False
        self._status.configure(
            text=("Review pending. Enter a candidate, then approve validation. "
                  "No credential will be saved."
                  if proposed is True and self._host.has_pending
                  else "Validation review unavailable. No provider request started."))
        self._sync()

    def approve_from_button(self):
        if self._busy or not self._host.has_pending:
            return
        self._busy = True
        candidate = None
        raw = None
        try:
            raw = self._entry.get()
            self._clear()
            if type(raw) is not str:
                raise ValueError("Invalid credential input")
            candidate = SecretValue(raw)
            raw = None
            result = self._host.approve(candidate=candidate)
            message = (_MESSAGES[result.outcome]
                       if type(result) is CredentialHostResult
                       and result.operation is OnboardingOperation.TEST_CANDIDATE
                       else "Validation result unavailable. No credential saved.")
        except Exception:
            # If candidate construction or callback failed, consume any review.
            try:
                self._host.reject()
            except Exception:
                pass
            message = "Validation unavailable. No credential saved."
        finally:
            raw = None
            candidate = None
            try:
                self._clear()
            except Exception:
                pass
            self._busy = False
        self._status.configure(text=message)
        self._sync()

    def reject_from_button(self):
        if self._busy:
            return
        try:
            if self._host.has_pending:
                self._host.reject()
        except Exception:
            pass
        self._clear()
        self._status.configure(text="Review rejected. Entry cleared. No validation performed.")
        self._sync()

    def close_from_window(self):
        if self._busy:
            return
        self.reject_from_button()
        self._root.destroy()
