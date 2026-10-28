"""Bounded offline Toplevel, not a production credential composition.

Only trusted test code may inject a harness. Its validate_fake_only(coordinator)
must vet backend, validator, mutex and disposable paths, and supply an opaque
synthetic candidate. Default import/open has no credential dependencies/effects.
No key entry, durable storage claim, worker, timer or nested event loop exists.
"""
import threading
import tkinter as tk
from tkinter import ttk


class FirstRunConnectionWindow:
    def __init__(self, app, pane, token, generation):
        self._creator = app._creator_thread
        self._thread()
        self.app, self.pane, self.token, self.generation = app, pane, token, generation
        self.application_identity = app._connection_application
        self.root_identity = app.root
        self.pane_identity, self.journey_identity = object(), object()
        self.child = self.owner = self.context = self.review = None
        self._bound_child = None
        self._bound_context = None
        self._harness = None
        self._alive = True
        self._retiring = self._busy = False
        self._retired = None
        self._enabled = False

    def _thread(self):
        if threading.get_ident() != self._creator:
            raise RuntimeError("WRONG_THREAD")

    def is_current(self):
        self._thread()
        # Pure identity only: never query Tk from an approval predicate.
        app = self.app
        ctx = self.context
        context_current = (ctx is self._bound_context and (ctx is None or (
            ctx.root is self.root_identity and ctx.application is self.application_identity
            and ctx.pane is self.pane_identity and ctx.journey is self.journey_identity
            and type(ctx.generation) is int and ctx.generation == self.generation)))
        return (self._alive and not self._retiring and not app._closed
                and app._root_alive and not app._reply_closing
                and app._connection is self and not app._connection_blocked
                and app._connection_application is self.application_identity
                and app.root is self.root_identity and self.child is self._bound_child
                and context_current
                and app._active_view is self.pane and self.pane._alive
                and app._active_token is self.token
                and app._generation == self.generation)

    def open(self):
        self._thread()
        if not self.is_current() or self.child is not None:
            return
        # Publish exact Python widget BEFORE __init__: raise-after-create is
        # recoverable without enumerating/destroying unrelated root children.
        self.child = tk.Toplevel.__new__(tk.Toplevel)
        self._bound_child = self.child
        try:
            tk.Toplevel.__init__(self.child, self.app.root)
        finally:
            # The native constructor can dispatch navigation before finishing.
            # Retirement may already have failed on the not-yet-created child.
            # After native construction (or partial failure), retire that same
            # exact child again; do not clear any earlier uncertainty/quarantine.
            if self._retired is not None:
                try:
                    self.child.destroy()
                except Exception:
                    self.app._connection_blocked = True
        if not self.is_current():
            self.retire()
            return
        self.child.protocol("WM_DELETE_WINDOW", self.retire)
        self.child.bind("<Destroy>", self._destroyed, add="+")
        self.child.title("Provider | Offline preview")
        self.status = ttk.Label(self.child, wraplength=480, text=(
            "Offline preview. Credential actions unavailable; no provider is connected."))
        self.status.pack(padx=20, pady=20)
        self.candidate_button = ttk.Button(self.child, text="Review fake candidate test",
            state="disabled", command=lambda: self.request("TEST_CANDIDATE"))
        self.stored_button = ttk.Button(self.child, text="Review fake stored test",
            state="disabled", command=lambda: self.request("TEST_STORED"))
        self.confirm_button = ttk.Button(self.child, text="Confirm fake validation",
            state="disabled", command=self.confirm)
        self.cancel_button = ttk.Button(self.child, text="Cancel review",
            state="disabled", command=self.cancel)
        for button in (self.candidate_button, self.stored_button,
                       self.confirm_button, self.cancel_button):
            button.pack(padx=20, pady=4)
        ttk.Button(self.child, text="Close", command=self.retire).pack(pady=12)
        harness, coordinator = self.app._connection_test_harness, self.app._connection_coordinator
        if harness is None or coordinator is None:
            return
        # This opt-in is a trusted test composition boundary, never evidence
        # inferred from coordinator class, a model response, or UI text.
        if harness.validate_fake_only(coordinator) is not True or not self.is_current():
            return
        from nayeon.desktop_alpha.first_run_connection_owner import (
            JourneyContext, TrustedFirstRunConnectionOwner)
        self.context = JourneyContext(self.app.root, self.application_identity,
            self.pane_identity, self.journey_identity, self.generation)
        self._bound_context = self.context
        self._harness = harness
        self.owner = TrustedFirstRunConnectionOwner(coordinator=coordinator,
            context=self.context, is_current=self.is_current)
        if not self.owner.start(self.context) or not self.is_current():
            self.retire()
            return
        self._enabled = True
        self._publish("Fake-only harness ready. Review and confirm are separate actions.")

    def _publish(self, text):
        self._thread()
        if not self.is_current():
            return
        self.status.configure(text=text)
        for button in (self.candidate_button, self.stored_button):
            if not self.is_current():
                return
            button.configure(state="normal" if self._enabled and self.review is None else "disabled")
        for button in (self.confirm_button, self.cancel_button):
            if not self.is_current():
                return
            button.configure(state="normal" if self.review is not None else "disabled")

    def request(self, name):
        self._thread()
        if self._busy or not self._enabled or self.review is not None or not self.is_current():
            return
        if name not in ("TEST_CANDIDATE", "TEST_STORED"):
            return
        self._busy = True
        try:
            from nayeon.brain.onboarding_operation_advice import OnboardingOperation
            _, review = self.owner.request(self.context, OnboardingOperation[name])
            if self.is_current():
                self.review = review
                self._publish("Review: fake validation only. Confirm explicitly permits the fake validator; "
                              "no real key is entered or saved." if review is not None else
                              "Fake review unavailable; no connection established.")
        except Exception:
            self.retire()
        finally:
            self._busy = False

    def confirm(self):
        self._thread()
        if self._busy or not self._enabled or self.review is None or not self.is_current():
            return
        self._busy = True
        review, self.review = self.review, None
        try:
            candidate = (self._harness.candidate
                         if review.operation.name == "TEST_CANDIDATE" else None)
            if not self.is_current():
                return
            from nayeon.brain.onboarding_coordination import (
                CoordinationReceipt, CoordinatedOutcome)
            receipt = self.owner.confirm(
                self.context, review, candidate=candidate, explicitly_approved=True)
            if type(receipt) is not CoordinationReceipt:
                self._enabled = False
                self._publish("RECOVERY_REQUIRED / INDETERMINATE: no verified result. "
                              "Further actions are blocked.")
                self.app._connection_blocked = True
            elif receipt.outcome is CoordinatedOutcome.COMPLETED:
                self._publish("Fake validation completed in the test harness only. "
                              "No durable or usable connection is claimed.")
            elif receipt.outcome is CoordinatedOutcome.REFUSED:
                self._enabled = False
                self._publish("Fake validation refused. No connection was established. "
                              "Close this preview before starting a new journey.")
            else:
                # Never misrepresent an uncertain, conflicting or unavailable
                # approval as a successful provider request or a clean retry.
                self._enabled = False
                self._publish("RECOVERY_REQUIRED / INDETERMINATE: operation was not "
                              "verified. Further actions are blocked.")
                self.app._connection_blocked = True
        except Exception:
            self.retire()
        finally:
            self._busy = False

    def cancel(self):
        self._thread()
        if self._busy or self.review is None or not self.is_current():
            return
        self._busy = True
        review, self.review = self.review, None
        try:
            self.owner.cancel(self.context, review)
            self._publish("Review cancelled; no connection established.")
        except Exception:
            self.retire()
        finally:
            self._busy = False

    def _destroyed(self, event):
        self._thread()
        if event.widget is self.child:
            self.retire(destroy=False)

    def retire(self, *, destroy=True):
        self._thread()
        if self._retiring:
            return False
        if self._retired is not None:
            return self._retired
        self._alive = False  # revoke before owner cleanup or any Tcl call
        self.review = None
        self._retiring = True
        clean = True
        try:
            if self.owner is not None:
                clean = self.owner.close(self.context) is True
            if destroy and self.child is not None and self.app._root_alive:
                try:
                    self.child.destroy()
                except Exception:
                    # __init__ may have failed before native widget creation.
                    clean = False
        except Exception:
            clean = False
        finally:
            self._retiring = False
            self._retired = clean
            if clean and self.app._connection is self:
                self.app._connection = None
            if not clean:
                self.app._connection_blocked = True
        return clean
