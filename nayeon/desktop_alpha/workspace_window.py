"""Offline workspace widgets; navigation is supplied by the trusted application."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk

from nayeon.desktop_alpha.offline_request_review import (
    DISCLOSURE, ReviewContext, ReviewRefused, ReviewState,
    OfflineRequestReviewOwner,
)

from nayeon.desktop_alpha.conversation_session import (
    EntrySource, ResetOperation, SessionRefused, SessionSnapshot,
    validate_offline_text,
)
from nayeon.desktop_alpha.reply_contracts import ERROR_TEXT, SIMULATED_TEXT


REPLY_WAITING = "SIMULATED REPLY / NO AI REQUEST: Local preview running."
REPLY_DRAINING = "SIMULATED REPLY / NO AI REQUEST: Display cancelled; worker draining."
REPLY_CANCELLED = "SIMULATED REPLY / NO AI REQUEST: Display cancelled. No action occurred."
REPLY_HOLD = "SIMULATED REPLY / NO AI REQUEST: Retirement required. Use Retry Close / Retire."
REPLY_MESSAGES = frozenset((ERROR_TEXT, SIMULATED_TEXT, REPLY_WAITING,
                            REPLY_DRAINING, REPLY_CANCELLED, REPLY_HOLD))


class WorkspaceWindow(ttk.Frame):
    def __init__(self, root, *, on_conversation, on_settings, on_connection,
                 on_reply_retire=None):
        self._creator_thread = threading.get_ident()
        self._reply_root = root
        self._reply_poll_token = self._reply_poll_handle = None
        self._reply_poll_busy = self._reply_poll_poisoned = False
        self._reply_poll_registering = False
        self._reply_poll_callback = self._reply_poll_fault = None
        super().__init__(root, padding=24, style="Offline.TFrame")
        style = ttk.Style(root)
        style.configure("Offline.TFrame", background="#f3f6fb")
        style.configure("Offline.TLabel", background="#f3f6fb", foreground="#24364b")
        style.configure("Title.Offline.TLabel", font=("Segoe UI", 23, "bold"))
        style.configure("Heading.Offline.TLabel", font=("Segoe UI", 15, "bold"))
        style.configure("Muted.Offline.TLabel", foreground="#53677d")
        style.configure("Badge.Offline.TLabel", foreground="#205c91",
                        font=("Segoe UI", 10, "bold"))
        self.pack(fill="both", expand=True)
        header = ttk.Frame(self, style="Offline.TFrame")
        header.pack(fill="x")
        self.name_label = ttk.Label(header, text="Nayeon", style="Title.Offline.TLabel")
        self.name_label.pack(side="left")
        ttk.Label(header, text="OFFLINE PREVIEW", style="Badge.Offline.TLabel").pack(
            side="right")
        ttk.Label(self, text="A quiet workspace for local preview and presentation preferences.",
                  style="Muted.Offline.TLabel").pack(anchor="w", pady=(4, 5))
        self.profile_status = ttk.Label(self, text="Checking local presentation (read-only)…",
                                        wraplength=700, style="Muted.Offline.TLabel")
        self.profile_status.pack(anchor="w", pady=(0, 16))
        navigation = ttk.Frame(self, style="Offline.TFrame")
        navigation.pack(fill="x", pady=(0, 20))
        self.navigation_buttons = []
        for name, label, command in (
            ("conversation", "Conversation", on_conversation),
            ("settings", "Presentation Settings", on_settings),
            ("connection", "Connection", on_connection),
        ):
            button = ttk.Button(navigation, name=name, text=label, command=lambda callback=command: self._dispatch(callback),
                                takefocus=True)
            button.pack(side="left", padx=(0, 10))
            button.bind("<Return>", lambda event, callback=command: self._return(callback))
            self.navigation_buttons.append(button)
        self.content = ttk.Frame(self, style="Offline.TFrame")
        self.content.pack(fill="both", expand=True)
        if on_reply_retire is not None:
            self.reply_retire_button = ttk.Button(
                self, text="Retry Close / Retire", command=lambda: self._dispatch(on_reply_retire))
            self.reply_retire_button.pack(anchor="w", pady=(8, 0))

    def start_reply_poll(self, callback, on_fault) -> bool:
        self._require_creator_thread()
        # Trusted root-owned 50ms pump. Unknown registration is never retried.
        if (self._reply_poll_poisoned or self._reply_poll_busy
                or self._reply_poll_token is not None):
            return False
        self._reply_poll_callback, self._reply_poll_fault = callback, on_fault
        self._reply_poll_token = object()
        return self._register_reply_poll(self._reply_poll_token)

    def _reply_poll_failed(self):
        self._require_creator_thread()
        # Revoke BEFORE invoking any callback; retain poison even without handle.
        self._reply_poll_token = None
        self._reply_poll_poisoned = True
        fault = self._reply_poll_fault
        if fault is not None:
            fault()

    def _register_reply_poll(self, token):
        self._require_creator_thread()
        self._reply_poll_busy = self._reply_poll_registering = True
        try:
            handle = self._reply_root.after(50, self._run_reply_poll, token)
            # A nested close/destroy/dispatch can revoke registration in flight.
            # Keep the one returned exact handle for explicit retirement only.
            self._reply_poll_handle = handle
            if self._reply_poll_token is not token or self._reply_poll_poisoned:
                self._reply_poll_failed()
                return False
            return True
        except Exception:
            self._reply_poll_failed()
            return False
        finally:
            self._reply_poll_busy = self._reply_poll_registering = False

    def _run_reply_poll(self, token):
        self._require_creator_thread()
        if token is not self._reply_poll_token:
            return
        if self._reply_poll_busy:
            self._reply_poll_failed()
            return
        # The exact pending callback is now executing, not cancellable.
        self._reply_poll_handle = None
        self._reply_poll_busy = True
        try:
            again = self._reply_poll_callback()
        except Exception:
            self._reply_poll_failed()
            return
        finally:
            self._reply_poll_busy = False
        if self._reply_poll_token is not token or self._reply_poll_poisoned:
            return
        if again:
            self._register_reply_poll(token)
        else:
            self._reply_poll_token = None

    def stop_reply_poll(self) -> bool:
        self._require_creator_thread()
        self._reply_poll_token = None  # revoke before the Tcl cancellation seam
        if self._reply_poll_busy:
            if self._reply_poll_registering:
                self._reply_poll_failed()
                return False
            # A dispatched poll has no pending handle. Revoke its continuation.
            return not self._reply_poll_poisoned
        handle, self._reply_poll_handle = self._reply_poll_handle, None
        if handle is None:
            return not self._reply_poll_poisoned
        self._reply_poll_busy = True
        try:
            self._reply_root.after_cancel(handle)
            return True
        except Exception:
            self._reply_poll_failed()
            return False
        finally:
            self._reply_poll_busy = False

    def reply_poll_destroyed(self, *, root=False):
        self._require_creator_thread()
        # Destroy event path: Python only, even for a foreign native destroy.
        if self._reply_poll_token is not None or self._reply_poll_busy:
            self._reply_poll_poisoned = True
        self._reply_poll_token = None
        if root:
            self._reply_poll_handle = None

    def _require_creator_thread(self) -> None:
        if threading.get_ident() != self._creator_thread:
            raise RuntimeError("WRONG_THREAD")

    def _dispatch(self, callback, *args):
        self._require_creator_thread()
        return callback(*args)

    def _return(self, callback):
        self._require_creator_thread()
        callback()
        return "break"

    def set_busy(self, busy: bool) -> None:
        self._require_creator_thread()
        for button in self.navigation_buttons:
            button.configure(state="disabled" if busy else "normal")

    def publish_name(self, name: str) -> None:
        self._require_creator_thread()
        self.name_label.configure(text=name)

    def publish_profile_status(self, status: str) -> None:
        self._require_creator_thread()
        self.profile_status.configure(text=status)


class WorkspacePane(ttk.Frame):
    """A destroyed pane can be checked without querying the dead Tcl interpreter."""

    def __init__(self, parent, *, name, on_destroy):
        self._creator_thread = threading.get_ident()
        super().__init__(parent, name=name, style="Offline.TFrame")
        self._alive = True
        self._on_destroy = on_destroy
        self.bind("<Destroy>", self._destroyed, add="+")

    def _require_creator_thread(self) -> None:
        if threading.get_ident() != self._creator_thread:
            raise RuntimeError("WRONG_THREAD")

    def _dispatch(self, callback, *args):
        self._require_creator_thread()
        return callback(*args)

    def _return(self, callback):
        self._require_creator_thread()
        callback()
        return "break"

    def _destroyed(self, event):
        self._require_creator_thread()
        if event.widget is self and self._alive:
            self._alive = False
            self._on_destroy()

    def exists(self) -> bool:
        self._require_creator_thread()
        if not self._alive:
            return False
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def dispose(self) -> None:
        self._require_creator_thread()
        if WorkspacePane.exists(self):
            self.destroy()

    def destroy(self) -> None:
        self._require_creator_thread()
        if not self._alive:
            return
        self._alive = False
        self._on_destroy()
        super().destroy()


class ConversationWindow(WorkspacePane):
    def __init__(self, parent, *, on_send, on_reset, is_current,
                 on_destroy, assistant_name: str, user_name: str,
                 on_cancel_simulation=None, on_before_destroy=None,
                 on_reply=None, on_cancel_reply=None, on_request_snapshot=None):
        super().__init__(parent, name="conversation_view", on_destroy=on_destroy)
        self._request_snapshot = on_request_snapshot
        self._request_root = object()
        self._request_pane = object()
        self._request_owner = OfflineRequestReviewOwner(self._request_root)
        self._request_context = self._request_prompt = self._request_ticket = None
        self._request_serial = 0
        self._request_busy = self._request_pending_clear = False
        # Explicit owner-thread destroy may retire a known timer BEFORE Tk
        # deletes its registered Tcl callback command. Destroy event bindings
        # remain Python-only, including unexpected native destruction.
        self._on_before_destroy = on_before_destroy
        self._on_send = on_send
        self._is_current = is_current
        self._assistant_name, self._user_name = assistant_name, user_name
        self._sending = False
        self._reply_invalidating = self._reply_hidden = False
        self._reply_invalidation_version = 0
        self._reset_review = None
        self._reset_confirm = self._reset_dismiss = None
        ttk.Label(self, text="Conversation", style="Heading.Offline.TLabel").pack(anchor="w")
        ttk.Label(self, text="OFFLINE PREVIEW · Closing this window discards session history. No AI or actions.",
                  style="Muted.Offline.TLabel").pack(anchor="w", pady=(6, 14))
        transcript_row = ttk.Frame(self)
        transcript_row.pack(fill="both", expand=True)
        self.transcript = tk.Text(transcript_row, name="transcript", wrap="word",
                                  state="disabled", background="#ffffff", foreground="#24364b",
                                  relief="flat", padx=16, pady=14, height=10,
                                  font=("Segoe UI", 11), takefocus=True)
        scrollbar = ttk.Scrollbar(transcript_row, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.transcript.pack(side="left", fill="both", expand=True)
        # Even if a nested Tk dispatch occurs during owner-only render, reject
        # user keyboard/paste/cut/clear edits on this output-only surface.
        for event_name in ("<KeyPress>", "<<Paste>>", "<<Cut>>", "<<Clear>>"):
            self.transcript.bind(event_name, self._block_edit)
        self.transcript.tag_configure("USER", foreground="#24364b")
        self.transcript.tag_configure("LOCAL_STATUS", foreground="#205c91",
                                      font=("Segoe UI", 10, "bold"))
        row = ttk.Frame(self, style="Offline.TFrame")
        row.pack(fill="x", pady=(14, 0))
        self.entry = ttk.Entry(row, name="message", font=("Segoe UI", 11),
                               validate="all",
                               validatecommand=(self.register(self._proposed), "%P"))
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        self.send_button = ttk.Button(row, name="send", text="Save offline", command=self._send)
        self.send_button.pack(side="right", ipady=4)
        self.entry.bind("<Return>", self._send)
        self.send_button.bind("<Return>", self._send)
        self.status = ttk.Label(self, wraplength=680, style="Muted.Offline.TLabel",
                                text="Offline session only. No AI request or action was performed.")
        self.status.pack(anchor="w", pady=6)
        self.reply_status = ttk.Label(self, text="SIMULATED REPLY / NO AI REQUEST",
                                      wraplength=680, style="Badge.Offline.TLabel")
        self.reply_status.pack(anchor="w", pady=6)
        request_row = ttk.Frame(self, style="Offline.TFrame")
        request_row.pack(fill="x", pady=(4, 4))
        request_ready = "normal" if on_request_snapshot is not None else "disabled"
        self.request_review_button = ttk.Button(request_row, text="Review offline prompt",
            state=request_ready, command=self._begin_request_review)
        self.request_confirm_button = ttk.Button(request_row, text="Confirm offline review",
            state="disabled", command=self._confirm_request_review)
        self.request_cancel_button = ttk.Button(request_row, text="Cancel review",
            state=request_ready, command=self._cancel_request_review)
        for button in (self.request_review_button, self.request_confirm_button,
                       self.request_cancel_button):
            button.pack(side="left", padx=(0, 7))
        self.request_disclosure = ttk.Label(self, text="", wraplength=680,
            style="Muted.Offline.TLabel")
        self.request_disclosure.pack(anchor="w", pady=(1, 3))
        self.request_status = ttk.Label(self, text="No AI request or action was performed.",
            wraplength=680, style="Badge.Offline.TLabel")
        self.request_status.pack(anchor="w", pady=(0, 5))
        if on_reply is not None:
            self.reply_button = ttk.Button(self, text="Simulate reply (no AI)",
                command=lambda: self._dispatch(on_reply))
            self.reply_button.pack(anchor="w")
        if on_cancel_reply is not None:
            self.cancel_reply_button = ttk.Button(self, text="Cancel reply preview",
                command=lambda: self._dispatch(on_cancel_reply))
            self.cancel_reply_button.pack(anchor="w")
        if on_cancel_simulation is not None:
            self.cancel_simulation_button = ttk.Button(
                self, text="Cancel local simulation",
                command=lambda: self._dispatch(on_cancel_simulation))
            self.cancel_simulation_button.pack(anchor="w", pady=(0, 6))
        reset_row = ttk.Frame(self, style="Offline.TFrame")
        reset_row.pack(fill="x")
        self.clear_button = ttk.Button(reset_row, text="Review Clear", command=lambda: self._dispatch(on_reset, ResetOperation.CLEAR))
        self.new_session_button = ttk.Button(reset_row, text="Review New Session", command=lambda: self._dispatch(on_reset, ResetOperation.NEW_SESSION))
        self.confirm_button = ttk.Button(reset_row, text="Confirm reset", state="disabled", command=self._confirm_reset)
        self.dismiss_button = ttk.Button(reset_row, text="Dismiss", state="disabled", command=self._dismiss_reset)
        for button in (self.clear_button, self.new_session_button, self.confirm_button, self.dismiss_button):
            button.pack(side="left", padx=(0, 8))
            button.bind("<Return>", lambda event, b=button: self._return(b.invoke))
        self.reset_status = ttk.Label(self, text="", wraplength=680, style="Badge.Offline.TLabel")
        self.reset_status.pack(anchor="w", pady=6)

    def _request_now(self):
        self._require_creator_thread()
        return time.monotonic_ns() // 1_000_000

    def _request_pure_current(self, context, serial, state):
        # No Tcl calls: this predicate can run AFTER final widget observation.
        return (self._alive and self._request_context is context
                and self._request_serial == serial
                and not self._request_pending_clear
                and self._request_owner.state is state)

    def _cancel_request_review(self):
        self._require_creator_thread()
        self._request_serial += 1
        self._request_context = self._request_prompt = self._request_ticket = None
        self._request_owner.abort()
        if self._request_busy:
            self._request_pending_clear = True
            return False
        self._request_busy = True
        self._request_pending_clear = False
        failed = False
        try:
            if self._alive:
                # Clear the old success receipt FIRST. A later button or
                # disclosure fault cannot leave stale success visible.
                # Each surface has independent best-effort hidden fallback.
                for widget, options in (
                    (self.request_status,
                     {"text": "No AI request or action was performed."}),
                    (self.request_confirm_button, {"state": "disabled"}),
                    (self.request_disclosure, {"text": ""})):
                    try:
                        widget.configure(**options)
                    except (tk.TclError, RuntimeError):
                        failed = True
                        try:
                            widget.pack_forget()
                        except (tk.TclError, RuntimeError):
                            pass
        finally:
            self._request_busy = False
        if failed:
            self._request_pending_clear = True
        return not failed and not self._request_pending_clear

    def _begin_request_review(self):
        self._require_creator_thread()
        if self._request_snapshot is None or not self._alive or self._request_busy:
            return False
        self._request_serial += 1
        self._request_owner.abort()
        self._request_context = self._request_prompt = self._request_ticket = None
        self._request_owner.reset()
        self._request_busy = True
        serial = self._request_serial
        complete = False
        try:
            self.request_confirm_button.configure(state="disabled")
            if not self._is_current() or self._request_pending_clear:
                return False
            snapshot = self._request_snapshot()
            if type(snapshot) is not SessionSnapshot or snapshot.closed:
                return False
            prompt = self.entry.get()
            context = ReviewContext(self._request_root, self._request_pane,
                snapshot.session_identity, serial, snapshot.epoch, snapshot.revision)
            preview = self._request_owner.offer(context, prompt, self._request_now())
            self._request_context, self._request_prompt = context, prompt
            complete = self._publish_request_review(
                context, prompt, snapshot, serial, preview)
            return complete
        except (ReviewRefused, tk.TclError, RuntimeError, ValueError):
            return False
        finally:
            self._request_busy = False
            if not complete or self._request_pending_clear:
                self._cancel_request_review()

    def _publish_request_review(self, context, prompt, snapshot, serial, preview):
        display = "PROPOSED PROMPT (NOT SENT): " + preview.prompt + "\n" + DISCLOSURE
        self.request_disclosure.configure(text=display)
        if not self._request_pure_current(context, serial, ReviewState.PREVIEW):
            return False
        if self.request_disclosure.cget("text") != display:
            return False
        self.request_status.configure(
            text="Review the prompt above. Nothing will be sent.")
        if not self._request_pure_current(context, serial, ReviewState.PREVIEW):
            return False
        self._request_owner.begin_enable(context, prompt, self._request_now())
        self.request_confirm_button.configure(state="normal")
        # All potentially reentrant Tcl-backed checks precede final instate.
        if not self._is_current() or self.entry.get() != prompt:
            return False
        if self.request_disclosure.cget("text") != display:
            return False
        if self._request_snapshot() is not snapshot:
            return False
        if not self.request_confirm_button.winfo_exists():
            return False
        if not self._request_pure_current(context, serial, ReviewState.ENABLING):
            return False
        # LAST TCL SEAM. No widget queries or yielding between this and arm.
        enabled = self.request_confirm_button.instate(("!disabled",))
        if not enabled or not self._request_pure_current(
                context, serial, ReviewState.ENABLING):
            return False
        self._request_ticket = self._request_owner.arm_after_last_tk(
            context, prompt, self._request_now())
        return True

    def _confirm_request_review(self):
        self._require_creator_thread()
        if self._request_busy:
            self._cancel_request_review()  # Reentrant before/after Tcl effects.
            return False
        context, prompt, ticket = (
            self._request_context, self._request_prompt, self._request_ticket)
        if not self._alive or context is None or ticket is None:
            return False
        self._request_busy = True
        serial = self._request_serial
        complete = False
        try:
            if not self._is_current() or self.entry.get() != prompt:
                return False
            snapshot = self._request_snapshot()
            if (type(snapshot) is not SessionSnapshot or snapshot.closed
                    or snapshot.session_identity is not context.session
                    or snapshot.epoch != context.epoch
                    or snapshot.revision != context.revision
                    or not self._request_pure_current(
                        context, serial, ReviewState.ARMED)):
                return False
            receipt = self._request_owner.confirm(
                ticket, context, prompt, self._request_now())
            self._request_ticket = None
            self.request_confirm_button.configure(state="disabled")
            self.request_disclosure.configure(text="")
            if not self._request_pure_current(
                    context, serial, ReviewState.IDLE):
                return False
            self.request_status.configure(text=receipt.status)
            complete = self._request_pure_current(
                context, serial, ReviewState.IDLE)
            return complete
        except (ReviewRefused, tk.TclError, RuntimeError, ValueError):
            return False
        finally:
            self._request_busy = False
            if not complete or self._request_pending_clear:
                self._cancel_request_review()

    def exists(self) -> bool:
        self._require_creator_thread()
        if not super().exists():
            return False
        try:
            return all(widget.winfo_exists() for widget in
                       (self.entry, self.send_button, self.transcript))
        except tk.TclError:
            return False

    def focus_initial(self) -> None:
        self._require_creator_thread()
        self.entry.focus_set()

    def _proposed(self, candidate):
        self._require_creator_thread()
        if candidate == "":
            return True
        try:
            validate_offline_text(candidate)
            return True
        except (SessionRefused, UnicodeError):
            return False

    def show_status(self, text):
        self._require_creator_thread()
        if len(text) > 160:
            raise ValueError("Status exceeds display bound")
        if self._is_current():
            self.status.configure(text=text)

    def show_simulation_status(self, text, eligible):
        self._require_creator_thread()
        if len(text) > 160:
            raise ValueError("Status exceeds display bound")
        # View-current may dispatch nested application callbacks. Recheck exact
        # completion authority AFTER that seam, immediately before the widget.
        if self._is_current() and eligible():
            self.status.configure(text=text)

    def invalidate_reply_preview(self):
        self._require_creator_thread()
        if self._reply_invalidating:
            return False
        self._reply_invalidating = True
        try:
            try:
                self.reply_status.configure(text="")
            except Exception:
                # Independent, bounded fallback. Once attempted, this pane can
                # never publish another preview or remap this label.
                self._reply_hidden = True
                self.reply_status.pack_forget()
            self._reply_invalidation_version += 1
            return True
        finally:
            self._reply_invalidating = False

    def show_reply_status(self, text, eligible):
        self._require_creator_thread()
        if type(text) is not str or text not in REPLY_MESSAGES:
            raise ValueError("REPLY_DISPLAY")
        # Literal fixed text only; never the transcript or offline status.
        if (self._is_current() and eligible()
                and not self._reply_invalidating and not self._reply_hidden):
            self.reply_status.configure(text=text)

    def show_reply_retirement_status(self, text, eligible):
        self._require_creator_thread()
        if type(text) is not str or text not in (REPLY_DRAINING, REPLY_HOLD, REPLY_CANCELLED):
            raise ValueError("REPLY_DISPLAY")
        # Closing has already revoked the ordinary view gate. Only a fixed
        # retirement notice can use the application's exact Python identity
        # probe; no reply or transcript is allowed through this ingress.
        if (self._alive and eligible()
                and not self._reply_invalidating and not self._reply_hidden):
            self.reply_status.configure(text=text)

    def render(self, snapshot):
        self._require_creator_thread()
        self._cancel_request_review()
        # The bounded immutable owner snapshot is authoritative; never evict.
        if not self._is_current():
            return
        try:
            self.transcript.configure(state="normal")
            if not self._is_current():
                return
            self.transcript.delete("1.0", "end")
            for entry in snapshot.entries:
                if not self._is_current():
                    return
                label = "USER" if entry.source is EntrySource.USER else "LOCAL_STATUS / UNSENT_OFFLINE"
                self.transcript.insert("end", label + "\n" + entry.payload + "\n\n", entry.source.value)
        finally:
            if self._is_current():
                self.transcript.configure(state="disabled")

    def _block_edit(self, _event=None):
        self._require_creator_thread()
        return "break"

    def show_reset(self, review, confirm, dismiss):
        self._require_creator_thread()
        self._cancel_request_review()
        prior = self._reset_review
        self.clear_reset(prior)
        if not self._is_current() or self._reset_review is not None:
            return
        # Publish identity and Python callbacks before any partial Tk update.
        self._reset_review = review
        self._reset_confirm, self._reset_dismiss = confirm, dismiss
        self.reset_status.configure(text="Review " + review.operation.value +
            ": discard all session history? Valid for 30 seconds. Expired confirmation is refused; select Review again.")
        if self._is_current() and self._reset_review is review:
            self.confirm_button.configure(state="normal")
        if self._is_current() and self._reset_review is review:
            self.dismiss_button.configure(state="normal")

    def clear_reset(self, review=None):
        self._require_creator_thread()
        if review is not None and self._reset_review is not review:
            return
        self._reset_review = None
        self._reset_confirm = self._reset_dismiss = None
        failure = None
        for widget, options in ((self.confirm_button, {"state": "disabled"}),
                                (self.dismiss_button, {"state": "disabled"}),
                                (self.reset_status, {"text": ""})):
            # A configure can dispatch a successor. Never disable or erase B.
            if not self._is_current() or self._reset_review is not None:
                break
            try:
                widget.configure(**options)
            except Exception as error:
                if failure is None:
                    failure = error
        if failure is not None:
            raise failure

    def destroy(self) -> None:
        self._require_creator_thread()
        before = self._on_before_destroy
        if self._alive and before is not None:
            if before() is False:
                return
        self._on_before_destroy = None
        self._reset_review = None
        self._reset_confirm = self._reset_dismiss = None
        super().destroy()

    def _destroyed(self, event):
        self._require_creator_thread()
        if event.widget is self:
            self._request_serial += 1
            self._request_context = self._request_prompt = self._request_ticket = None
            self._request_owner.close()
            self._reset_review = None
            self._reset_confirm = self._reset_dismiss = None
        super()._destroyed(event)

    def _confirm_reset(self):
        self._require_creator_thread()
        callback = self._reset_confirm
        if callback is not None and self._is_current():
            callback()

    def _dismiss_reset(self):
        self._require_creator_thread()
        callback = self._reset_dismiss
        if callback is not None and self._is_current():
            callback()

    def _send(self, _event=None):
        self._require_creator_thread()
        if self._sending:
            return "break"
        # Set the reentrancy gate BEFORE the first Tcl-backed current/view
        # check and BEFORE cancellation's three potentially nested configures.
        self._sending = True
        try:
            if not self._is_current():
                return "break"
            original_prompt = self.entry.get()
            if self._cancel_request_review() is not True:
                return "break"
            # A nested callback may change the entry or navigate despite the
            # send gate; never send a successor prompt on the same gesture.
            if not self._is_current() or self.entry.get() != original_prompt:
                return "break"
            self._on_send()
        finally:
            self._sending = False
        return "break"


class ConnectionWindow(WorkspacePane):
    def __init__(self, parent, *, on_destroy, on_conversation):
        super().__init__(parent, name="connection_view", on_destroy=on_destroy)
        ttk.Label(self, text="Connection", style="Heading.Offline.TLabel").pack(anchor="w")
        ttk.Label(self, text="Not observed; connection operations unavailable in this prototype",
                  wraplength=580, style="Offline.TLabel").pack(anchor="w", pady=(18, 24))
        self.back_button = ttk.Button(self, name="back", text="Back to Conversation",
                                      command=lambda: self._dispatch(on_conversation))
        self.back_button.pack(anchor="w")
        self.back_button.bind("<Return>", lambda event: self._return(on_conversation))

    def focus_initial(self) -> None:
        self._require_creator_thread()
        self.back_button.focus_set()
