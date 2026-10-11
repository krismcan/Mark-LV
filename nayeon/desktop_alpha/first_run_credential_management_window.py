"""Phase 8.27: trusted Tk key management with explicit human operation approval.

This panel receives an exact trusted coordinator. It cannot create a credential
backend, select a key namespace, or invoke credential mutation directly.
Only human-owned Tk review/approve/reject callbacks can submit CONNECT, REPLACE
or REMOVE through the Phase 8.26 cooperative single-writer boundary.

All provider/credential services must be injected by a trusted composition.
Tests use fake backends and validators; real provider calls require separate
explicit consent. Tk masking and deletion are best effort, not secure erasure.
"""
import tkinter as tk
from nayeon.desktop_alpha.first_run_onboarding_recovery_window import FirstRunOnboardingRecoveryWindow

from nayeon.brain.onboarding_coordination import (
    CooperativeOnboardingCoordinator, CoordinationReceipt, CoordinatedOutcome,
)
from nayeon.brain.onboarding_operation_advice import OnboardingOperation
from nayeon.brain.credential_operation_host import CredentialHostOutcome
from nayeon.secrets.contracts import SecretValue


_ACTIONS = (
    (OnboardingOperation.CONNECT, "Review connecting a new key"),
    (OnboardingOperation.REPLACE, "Review replacing the stored key"),
    (OnboardingOperation.REMOVE, "Review deleting the stored key"),
)
_NEEDS_CANDIDATE = frozenset({
    OnboardingOperation.CONNECT, OnboardingOperation.REPLACE,
})
_REASON = {
    CoordinatedOutcome.REFUSED: "Operation refused. No new action was authorised.",
    CoordinatedOutcome.BUSY: "Another Nayeon process is operating. Nothing submitted. Review again later.",
    CoordinatedOutcome.CONFLICT: "State changed. No clean completion can be claimed. Refresh and review again.",
    CoordinatedOutcome.RECOVERY_REQUIRED: (
        "Recovery required. An operation may have changed state. "
        "Do not retry or remove the recovery marker without human reconciliation."
    ),
    CoordinatedOutcome.UNAVAILABLE: (
        "Operation unavailable. Inspect current credential state and recovery marker "
        "before any further attempt."
    ),
    CoordinatedOutcome.INDETERMINATE: (
        "Outcome is inconclusive. Reconcile current state before further actions."
    ),
}
_COMPLETE = {
    CredentialHostOutcome.SUBMITTED: (
        "Operation submitted. Storage durability and final credential state are not "
        "confirmed. Refresh and independently re-observe."
    ),
    CredentialHostOutcome.INVALID: (
        "Candidate validation failed. No credential change was authorised."
    ),
    CredentialHostOutcome.INDETERMINATE: (
        "Credential result is indeterminate. Reconcile state before retrying."
    ),
    CredentialHostOutcome.NOT_APPLIED: (
        "Operation was not applied. Re-observe current credential state."
    ),
    CredentialHostOutcome.BLOCKED: (
        "Approval blocked or expired. No successful operation is claimed."
    ),
}


class FirstRunCredentialManagementWindow:
    """Manual, single-use trusted UI bridge; no direct backend/store methods."""

    def __init__(self, root: tk.Tk, *, coordinator: CooperativeOnboardingCoordinator):
        if type(coordinator) is not CooperativeOnboardingCoordinator:
            raise TypeError("Exact trusted onboarding coordinator required")
        self._root = root
        self._coordinator = coordinator
        self._operation: OnboardingOperation | None = None
        self._busy = False
        self._closed = False
        self._close_deferred = False
        self._owner_token: str | None = None

        root.title("Nayeon | Manage OpenAI credential")
        root.geometry("680x520")
        root.minsize(560, 420)
        root.configure(bg="#101827")
        tk.Label(root, text="Nayeon - Credential management", bg="#101827",
                 fg="#f1f4fb", font=("Segoe UI", 17, "bold")).pack(
                     anchor="w", padx=20, pady=(18, 8))
        tk.Label(root, bg="#101827", fg="#adc1d6",
                 text="Nothing is saved, replaced, deleted or validated on launch.").pack(
                     anchor="w", padx=20)
        tk.Label(root, bg="#101827", fg="#adc1d6",
                 text="Select one review action. Approval is a separate deliberate step.").pack(
                     anchor="w", padx=20, pady=(6, 12))
        self._recovery_dialog = None
        self._recovery_button = tk.Button(
            root, text="Inspect and reconcile onboarding safety",
            command=self.open_reconciliation_from_button)
        self._recovery_button.pack(anchor="w", padx=20, pady=4)
        self._choices = []
        for operation, label in _ACTIONS:
            button = tk.Button(root, text=label,
                               command=lambda chosen=operation:
                                   self.request_from_button(chosen))
            button.pack(anchor="w", padx=20, pady=3)
            self._choices.append(button)
        tk.Label(root, text="Candidate key (required only for connect or replace)",
                 bg="#101827", fg="#adc1d6").pack(
                     anchor="w", padx=20, pady=(12, 4))
        self._entry = tk.Entry(root, show="*", exportselection=False, width=60)
        self._entry.pack(anchor="w", padx=20)
        for sequence in ("<<Copy>>", "<<Cut>>", "<Control-c>", "<Control-x>",
                         "<Control-C>", "<Control-X>"):
            self._entry.bind(sequence, self._prevent_copy)
        self._acknowledged = tk.BooleanVar(master=root, value=False)
        self._delete_ack = tk.Checkbutton(
            root, variable=self._acknowledged,
            text="I understand that deleting the stored key is destructive",
            bg="#101827", fg="#f1f4fb", selectcolor="#101827",
        )
        self._delete_ack.pack(anchor="w", padx=20, pady=(12, 6))
        self._approve = tk.Button(root, text="Approve selected operation once",
                                  command=self.approve_from_button)
        self._approve.pack(anchor="w", padx=20, pady=3)
        self._reject = tk.Button(root, text="Reject and clear",
                                 command=self.reject_from_button)
        self._reject.pack(anchor="w", padx=20, pady=3)
        self._status = tk.Label(
            root, text="No pending review", bg="#101827", fg="#a5c9f7",
            wraplength=630, justify="left",
        )
        self._status.pack(anchor="w", padx=20, pady=(12, 8))
        root.protocol("WM_DELETE_WINDOW", self.close_from_window)
        root.bind("<Destroy>", self._on_destroy, add="+")
        self._sync()
        # Constructor failure must not strand a path-pooled UI owner token.
        self._owner_token = self._coordinator.recovery_controller.claim_ui_window_owner()

    def _live_window(self) -> bool:
        if self._closed:
            return False
        try:
            return bool(self._root.winfo_exists())
        except (tk.TclError, AttributeError):
            return False

    def _owns_token(self) -> bool:
        """Owner identity remains meaningful after root destruction."""
        return self._coordinator.recovery_controller.is_ui_window_owner(self._owner_token)

    def _on_destroy(self, event) -> None:
        if event.widget is self._root:
            self._teardown()

    def _release_owned(self) -> None:
        # Never touch Tk in this path. Reject only the exact owning panel's
        # pending operation; foreign callers must not cancel another review.
        if self._owns_token():
            try:
                self._coordinator.reject()
            except Exception:
                pass
            try:
                self._coordinator.recovery_controller.close_ui_window_owner(self._owner_token)
            except Exception:
                # Native uncertainty remains fail-closed in the controller.
                pass
        self._owner_token = None
        self._operation = None
        self._close_deferred = False

    def _teardown(self) -> None:
        if self._closed and not self._close_deferred:
            return
        self._closed = True
        if self._busy:
            self._close_deferred = True
            return
        self._release_owned()

    def _finish_deferred_close(self) -> None:
        if self._close_deferred and not self._busy:
            self._release_owned()

    def _has_owner(self) -> bool:
        return self._live_window() and self._owns_token()

    def _claim_owner(self) -> bool:
        if not self._live_window():
            return False
        if not self._has_owner():
            self._owner_token = self._coordinator.recovery_controller.claim_ui_window_owner()
        return self._has_owner()

    @staticmethod
    def _prevent_copy(event):
        return "break"

    def _clear(self):
        # Disabled Tk.Entry cannot be deleted: temporarily enable, then clear.
        self._entry.configure(state="normal")
        self._entry.delete(0, tk.END)

    def _sync(self):
        if not self._live_window():
            return
        pending = self._coordinator.has_pending is True and self._operation is not None
        for button in self._choices:
            button.configure(state="disabled" if pending or self._busy else "normal")
        self._approve.configure(state="normal" if pending and not self._busy else "disabled")
        self._reject.configure(state="normal" if pending and not self._busy else "disabled")
        accepts_key = pending and self._operation in _NEEDS_CANDIDATE
        self._entry.configure(state="normal" if accepts_key and not self._busy else "disabled")
        self._delete_ack.configure(state="normal" if pending and
                                   self._operation is OnboardingOperation.REMOVE
                                   and not self._busy else "disabled")

    def request_from_button(self, operation: OnboardingOperation):
        if not self._live_window():
            return
        if not self._claim_owner():
            self._status.configure(text="Another window owns onboarding recovery.")
            return
        if (self._busy or self._coordinator.has_pending or self._operation is not None
                or type(operation) is not OnboardingOperation
                or operation not in {a for a, _ in _ACTIONS}):
            return
        self._clear()
        self._acknowledged.set(False)
        try:
            result = self._coordinator.request(operation)
        except Exception:
            result = None
        if (type(result) is CoordinationReceipt
                and result.outcome is CoordinatedOutcome.PENDING
                and self._coordinator.has_pending):
            self._operation = operation
            message = (
                "Delete review pending. Tick the explicit deletion acknowledgement, "
                "then approve once. No key has been deleted."
                if operation is OnboardingOperation.REMOVE
                else "Review pending. Enter a key and approve once. "
                     "No key has been saved or replaced."
            )
        else:
            self._operation = None
            message = self._message(result)
        self._status.configure(text=message)
        self._sync()

    @staticmethod
    def _message(result):
        if type(result) is not CoordinationReceipt:
            return "Operation unavailable. No successful result is claimed."
        if result.outcome is CoordinatedOutcome.COMPLETED:
            return _COMPLETE.get(result.host_outcome,
                                 "Result requires reconciliation.")
        return _REASON.get(result.outcome, "Operation unavailable. No success is claimed.")

    def approve_from_button(self):
        if not self._has_owner():
            return
        operation = self._operation
        if self._busy or not self._coordinator.has_pending or operation is None:
            return
        if (operation is OnboardingOperation.REMOVE
                and self._acknowledged.get() is not True):
            self._status.configure(
                text="Deletion approval requires explicit acknowledgement. Nothing submitted.")
            return
        self._busy = True
        raw = None
        candidate = None
        try:
            if operation in _NEEDS_CANDIDATE:
                raw = self._entry.get()
                self._clear()
                if type(raw) is not str:
                    raise ValueError("Invalid candidate")
                candidate = SecretValue(raw)
                raw = None
                result = self._coordinator.approve(candidate=candidate)
            else:
                self._clear()
                result = self._coordinator.approve()
            message = self._message(result)
        except Exception:
            try:
                self._coordinator.reject()
            except Exception:
                pass
            message = "Operation unavailable. Reconcile current state before retrying."
        finally:
            raw = None
            candidate = None
            if self._live_window():
                try:
                    self._clear()
                    self._acknowledged.set(False)
                except tk.TclError:
                    pass
            self._operation = None
            self._busy = False
            self._finish_deferred_close()
        if not self._live_window():
            return
        self._status.configure(text=message)
        self._sync()

    def reject_from_button(self):
        if not self._has_owner() or self._busy:
            return
        try:
            self._coordinator.reject()
        except Exception:
            pass
        self._clear()
        self._acknowledged.set(False)
        self._operation = None
        self._status.configure(text="Review rejected. Candidate cleared. Nothing submitted.")
        self._sync()

    def open_reconciliation_from_button(self):
        """Only an owning, live human window may open a recovery review."""
        if not self._live_window() or self._busy:
            return
        if not self._claim_owner():
            self._status.configure(text="Another window owns onboarding recovery.")
            return
        if (self._recovery_dialog is not None and
                self._recovery_dialog._root.winfo_exists()):
            return
        self._recovery_dialog = None
        ctrl = self._coordinator.recovery_controller
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

    def close_from_window(self):
        if self._closed or self._busy:
            return
        # Scrub the visible candidate before releasing the owner. External
        # destroyed-root cleanup cannot touch the already-dead entry.
        if self._live_window():
            try:
                self._clear()
                self._acknowledged.set(False)
            except (tk.TclError, AttributeError):
                pass
        self._teardown()
        try:
            if self._root.winfo_exists():
                self._root.destroy()
        except (tk.TclError, AttributeError):
            # Test-only fake roots do not expose winfo_exists.
            pass
