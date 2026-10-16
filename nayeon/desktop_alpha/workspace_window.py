"""Offline workspace widgets; navigation is supplied by the trusted application."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from nayeon.desktop_alpha.controller import ChatReply, PreviewOnlyController


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
    def __init__(self, parent, *, controller: PreviewOnlyController, is_current,
                 on_destroy, assistant_name: str, user_name: str):
        super().__init__(parent, name="conversation_view", on_destroy=on_destroy)
        if type(controller) is not PreviewOnlyController:
            raise TypeError("Offline preview controller required")
        self._controller = controller
        self._is_current = is_current
        self._assistant_name, self._user_name = assistant_name, user_name
        self._sending = False
        ttk.Label(self, text="Conversation", style="Heading.Offline.TLabel").pack(anchor="w")
        ttk.Label(self, text="OFFLINE PREVIEW · Messages stay local. No actions can execute.",
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
        row = ttk.Frame(self, style="Offline.TFrame")
        row.pack(fill="x", pady=(14, 0))
        self.entry = ttk.Entry(row, name="message", font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        self.send_button = ttk.Button(row, name="send", text="Send preview", command=self._send)
        self.send_button.pack(side="right", ipady=4)
        self.entry.bind("<Return>", self._send)
        self.send_button.bind("<Return>", self._send)
        self._append(self._assistant_name, "Offline preview is ready. No actions can execute.")

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

    def _append(self, sender, message):
        self.transcript.configure(state="normal")
        self.transcript.insert("end", sender + "\n" + message + "\n\n")
        if int(self.transcript.index("end-1c").split(".")[0]) > 180:
            self.transcript.delete("1.0", "25.0")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def _send(self, _event=None):
        if self._sending or not self._is_current():
            return "break"
        self._sending = True
        try:
            self.entry.configure(state="disabled")
            self.send_button.configure(state="disabled")
            message = self.entry.get()
            if not message.strip() or len(message) > 512:
                self._append(self._assistant_name, "Enter a request of up to 512 characters.")
                return "break"
            message.encode("utf-8")
            self.entry.configure(state="normal")
            self.entry.delete(0, "end")
            self.entry.configure(state="disabled")
            self._append(self._user_name, message)
            reply = self._controller.send(message)
            if self._is_current():
                text = reply.message if type(reply) is ChatReply else "Preview unavailable."
                self._append(self._assistant_name, text)
        except Exception:
            if self._is_current():
                self._append(self._assistant_name, "Preview unavailable. No result is verified.")
        finally:
            self._sending = False
            if self._is_current():
                self.entry.configure(state="normal")
                self.send_button.configure(state="normal")
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
