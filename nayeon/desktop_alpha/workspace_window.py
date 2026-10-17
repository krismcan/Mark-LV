"""Offline workspace widgets; navigation is supplied by the trusted application."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from nayeon.desktop_alpha.conversation_session import (
    EntrySource, ResetOperation, SessionRefused, validate_offline_text,
)


class WorkspaceWindow(ttk.Frame):
    def __init__(self, root, *, on_conversation, on_settings, on_connection):
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
            button = ttk.Button(navigation, name=name, text=label, command=command,
                                takefocus=True)
            button.pack(side="left", padx=(0, 10))
            button.bind("<Return>", lambda event, callback=command: (callback(), "break")[1])
            self.navigation_buttons.append(button)
        self.content = ttk.Frame(self, style="Offline.TFrame")
        self.content.pack(fill="both", expand=True)

    def set_busy(self, busy: bool) -> None:
        for button in self.navigation_buttons:
            button.configure(state="disabled" if busy else "normal")

    def publish_name(self, name: str) -> None:
        self.name_label.configure(text=name)

    def publish_profile_status(self, status: str) -> None:
        self.profile_status.configure(text=status)


class WorkspacePane(ttk.Frame):
    """A destroyed pane can be checked without querying the dead Tcl interpreter."""

    def __init__(self, parent, *, name, on_destroy):
        super().__init__(parent, name=name, style="Offline.TFrame")
        self._alive = True
        self._on_destroy = on_destroy
        self.bind("<Destroy>", self._destroyed, add="+")

    def _destroyed(self, event):
        if event.widget is self and self._alive:
            self._alive = False
            self._on_destroy()

    def exists(self) -> bool:
        if not self._alive:
            return False
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def dispose(self) -> None:
        if WorkspacePane.exists(self):
            self.destroy()

    def destroy(self) -> None:
        if not self._alive:
            return
        self._alive = False
        self._on_destroy()
        super().destroy()


class ConversationWindow(WorkspacePane):
    def __init__(self, parent, *, on_send, on_reset, is_current,
                 on_destroy, assistant_name: str, user_name: str):
        super().__init__(parent, name="conversation_view", on_destroy=on_destroy)
        self._on_send = on_send
        self._is_current = is_current
        self._assistant_name, self._user_name = assistant_name, user_name
        self._sending = False
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
            self.transcript.bind(event_name, lambda event: "break")
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
        reset_row = ttk.Frame(self, style="Offline.TFrame")
        reset_row.pack(fill="x")
        self.clear_button = ttk.Button(reset_row, text="Review Clear", command=lambda: on_reset(ResetOperation.CLEAR))
        self.new_session_button = ttk.Button(reset_row, text="Review New Session", command=lambda: on_reset(ResetOperation.NEW_SESSION))
        self.confirm_button = ttk.Button(reset_row, text="Confirm reset", state="disabled", command=self._confirm_reset)
        self.dismiss_button = ttk.Button(reset_row, text="Dismiss", state="disabled", command=self._dismiss_reset)
        for button in (self.clear_button, self.new_session_button, self.confirm_button, self.dismiss_button):
            button.pack(side="left", padx=(0, 8))
            button.bind("<Return>", lambda event, b=button: (b.invoke(), "break")[1])
        self.reset_status = ttk.Label(self, text="", wraplength=680, style="Badge.Offline.TLabel")
        self.reset_status.pack(anchor="w", pady=6)

    def exists(self) -> bool:
        if not super().exists():
            return False
        try:
            return all(widget.winfo_exists() for widget in
                       (self.entry, self.send_button, self.transcript))
        except tk.TclError:
            return False

    def focus_initial(self) -> None:
        self.entry.focus_set()

    @staticmethod
    def _proposed(candidate):
        if candidate == "":
            return True
        try:
            validate_offline_text(candidate)
            return True
        except (SessionRefused, UnicodeError):
            return False

    def show_status(self, text):
        if len(text) > 160:
            raise ValueError("Status exceeds display bound")
        if self._is_current():
            self.status.configure(text=text)

    def render(self, snapshot):
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

    def show_reset(self, review, confirm, dismiss):
        self.clear_reset()
        if not self._is_current():
            return
        self._reset_review = review
        self._reset_confirm, self._reset_dismiss = confirm, dismiss
        self.reset_status.configure(text="Review " + review.operation.value + ": discard all session history? Expires in 30 seconds.")
        if self._is_current() and self._reset_review is review:
            self.confirm_button.configure(state="normal")
        if self._is_current() and self._reset_review is review:
            self.dismiss_button.configure(state="normal")

    def clear_reset(self, review=None):
        if review is not None and self._reset_review is not review:
            return
        self._reset_review = None
        self._reset_confirm = self._reset_dismiss = None
        for widget in (self.confirm_button, self.dismiss_button):
            if not self._is_current():
                return
            widget.configure(state="disabled")
        if self._is_current():
            self.reset_status.configure(text="")

    def _confirm_reset(self):
        callback = self._reset_confirm
        if callback is not None and self._is_current():
            callback()

    def _dismiss_reset(self):
        callback = self._reset_dismiss
        if callback is not None and self._is_current():
            callback()

    def _send(self, _event=None):
        if self._sending or not self._is_current():
            return "break"
        self._sending = True
        try:
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
                                      command=on_conversation)
        self.back_button.pack(anchor="w")
        self.back_button.bind("<Return>", lambda event: (on_conversation(), "break")[1])

    def focus_initial(self) -> None:
        self.back_button.focus_set()
