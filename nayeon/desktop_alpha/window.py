"""Tkinter-only UI: no authority to launch, approve, or grant capabilities."""
import tkinter as tk
from tkinter import ttk

from nayeon.desktop_alpha.controller import ChatOutcome, ChatReply, PreviewOnlyController

_BG = "#0b1220"
_PANEL = "#152135"
_ACCENT = "#79b9ff"
_LIGHT = "#eaf1fb"
_MUTED = "#a6b8cc"

class NayeonWindow:
    def __init__(self, root: tk.Tk, *, controller=None):
        self.root = root
        self.controller = controller if controller is not None else PreviewOnlyController()
        root.title("Nayeon | Personal Alpha")
        root.geometry("760x600")
        root.minsize(530, 420)
        root.configure(bg=_BG)
        head = tk.Frame(root, bg=_BG)
        head.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(head, text="Nayeon", font=("Segoe UI", 23, "bold"),
                 bg=_BG, fg=_LIGHT).pack(side="left")
        self.mode_label = tk.Label(head, text=self.controller.mode, font=("Segoe UI", 10, "bold"),
                                   bg=_BG, fg=_ACCENT)
        self.mode_label.pack(side="right")
        tk.Label(root, text="Personal Alpha | Explicit approval for local actions",
                 font=("Segoe UI", 10), bg=_BG, fg=_MUTED).pack(anchor="w", padx=25, pady=(0, 12))
        body = tk.Frame(root, bg=_PANEL)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 13))
        self.transcript = tk.Text(body, wrap="word", state="disabled", borderwidth=0,
                                  bg=_PANEL, fg=_LIGHT, insertbackground=_LIGHT,
                                  padx=15, pady=13, font=("Segoe UI", 11))
        scrollbar = ttk.Scrollbar(body, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.transcript.pack(side="left", fill="both", expand=True)
        self.transcript.tag_configure("speaker", foreground=_ACCENT,
                                      font=("Segoe UI", 10, "bold"))
        self.line_count = 0
        self._append("Nayeon", "Offline preview is ready. No actions can execute.", "assistant")
        input_row = tk.Frame(root, bg=_BG)
        input_row.pack(fill="x", padx=22, pady=(0, 11))
        self.entry = tk.Entry(input_row, relief="flat", bg=_PANEL, fg=_LIGHT,
                              insertbackground=_LIGHT, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 8))
        self.entry.bind("<Return>", self._send)
        self.send_button = tk.Button(input_row, text="Send", command=self._send,
                                     bg=_ACCENT, fg=_BG, relief="flat", padx=18)
        self.send_button.pack(side="right", ipady=7)
        approvals = tk.Frame(root, bg=_BG)
        approvals.pack(fill="x", padx=22, pady=(0, 22))
        self.approve_button = tk.Button(approvals, text="Approve action", command=self._approve,
                                        bg="#176f53", fg="white", relief="flat", padx=15)
        self.reject_button = tk.Button(approvals, text="Reject action", command=self._reject,
                                       bg="#893f54", fg="white", relief="flat", padx=15)
        self.approve_button.pack(side="left", padx=(0, 8))
        self.reject_button.pack(side="left")
        self._sync_controls()
        self.entry.focus_set()

    def _append(self, sender, message, tag):
        self.transcript.configure(state="normal")
        self.transcript.insert("end", sender + "\n", "speaker")
        self.transcript.insert("end", message + "\n\n", tag)
        self.line_count += 1
        if self.line_count > 35:
            self.transcript.delete("1.0", "3.0")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def _sync_controls(self):
        pending = self.controller.has_pending is True
        self.approve_button.configure(state="normal" if pending else "disabled")
        self.reject_button.configure(state="normal" if pending else "disabled")
        self.send_button.configure(state="disabled" if pending else "normal")
        self.entry.configure(state="disabled" if pending else "normal")

    def _show(self, reply):
        if type(reply) is not ChatReply:
            reply = ChatReply("Could not safely display a response.", ChatOutcome.BLOCKED)
        self._append("Nayeon", reply.message, "assistant")
        self._sync_controls()

    def _send(self, _event=None):
        if self.controller.has_pending:
            return
        text = self.entry.get()
        self.entry.delete(0, "end")
        if type(text) is not str or not text.strip() or len(text) > 512:
            self._show(ChatReply("Enter a request of up to 512 characters.", ChatOutcome.BLOCKED))
            return
        self._append("You", text, "speaker")
        try:
            result = self.controller.send(text)
        except Exception:
            result = ChatReply("Request failed safely; nothing is verified.", ChatOutcome.BLOCKED)
        self._show(result)

    def _approve(self):
        if self.controller.has_pending is not True:
            return
        try:
            result = self.controller.approve()
        except Exception:
            result = ChatReply("Approval failed; nothing is verified.", ChatOutcome.BLOCKED)
        self._show(result)

    def _reject(self):
        if self.controller.has_pending is not True:
            return
        try:
            result = self.controller.reject()
        except Exception:
            result = ChatReply("Rejection failed; nothing is verified.", ChatOutcome.BLOCKED)
        self._show(result)

def main():
    """Launch only when explicitly invoked; never starts a hidden background task."""
    root = tk.Tk()
    NayeonWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
