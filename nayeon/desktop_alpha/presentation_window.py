"""Presentation widgets and pure typed drafts, without storage authority."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from nayeon.config.document import (
    PresentationConfigurationDocumentV1,
    parse_presentation_configuration_document,
    presentation_configuration_document_to_mapping,
)
from nayeon.config.presentation import AssistantPresentationIdentity, UserPresentationProfile


class PresentationWindow(ttk.Frame):
    def __init__(self, parent, *, on_change, on_review, on_save, on_cancel, on_destroy):
        self._creator_thread = threading.get_ident()
        super().__init__(parent, name="presentation_view", style="Offline.TFrame")
        self._alive = True
        self._loading = False
        self._document = None
        self.revision = 0
        self._on_change, self._on_destroy = on_change, on_destroy
        self.bind("<Destroy>", self._destroyed, add="+")
        ttk.Label(self, text="Presentation Settings", style="Heading.Offline.TLabel").pack(
            anchor="w")
        ttk.Label(self, text="Names affect presentation only. Review first, then explicitly Save.",
                  wraplength=580, style="Muted.Offline.TLabel").pack(anchor="w", pady=(6, 16))
        form = ttk.Frame(self, style="Offline.TFrame")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self.assistant_name = tk.StringVar(master=self)
        self.wake_name = tk.StringVar(master=self)
        self.user_name = tk.StringVar(master=self)
        self.entries = []
        for index, (name, label, variable) in enumerate((
            ("assistant_name", "Assistant display name", self.assistant_name),
            ("wake_name", "Wake name", self.wake_name),
            ("user_name", "Your display name (optional)", self.user_name),
        )):
            ttk.Label(form, text=label, style="Offline.TLabel").grid(
                row=index, column=0, sticky="w", padx=(0, 18), pady=7)
            entry = ttk.Entry(form, name=name, textvariable=variable)
            entry.grid(row=index, column=1, sticky="ew", ipady=4, pady=7)
            self.entries.append(entry)
        self.status_label = ttk.Label(self, text="Loading presentation preferences…",
                                      wraplength=580, style="Muted.Offline.TLabel")
        self.status_label.pack(anchor="w", pady=(16, 10))
        self.summary_label = ttk.Label(self, text="No pending review.", wraplength=580,
                                       justify="left", style="Offline.TLabel")
        self.summary_label.pack(anchor="w", fill="x", pady=(0, 18))
        buttons = ttk.Frame(self, style="Offline.TFrame")
        buttons.pack(anchor="w")
        self.review_button = ttk.Button(buttons, name="review", text="Review changes",
                                        command=lambda: self._dispatch(on_review), state="disabled")
        self.save_button = ttk.Button(buttons, name="save", text="Save reviewed changes",
                                      command=lambda: self._dispatch(on_save), state="disabled")
        self.cancel_button = ttk.Button(buttons, name="cancel", text="Cancel", command=lambda: self._dispatch(on_cancel))
        for button, callback in ((self.review_button, on_review),
                                 (self.save_button, on_save), (self.cancel_button, on_cancel)):
            button.pack(side="left", padx=(0, 10))
            button.bind("<Return>", lambda event, command=callback: self._return(command))
        self._traces = [(variable, variable.trace_add("write", self._changed))
                        for variable in (self.assistant_name, self.wake_name, self.user_name)]
        self.set_controls(editable=False)

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
            self._document = None
            self.revision += 1
            self._on_destroy()

    def exists(self) -> bool:
        self._require_creator_thread()
        if not self._alive:
            return False
        try:
            return bool(self.winfo_exists()) and all(widget.winfo_exists() for widget in
                (*self.entries, self.review_button, self.save_button, self.cancel_button,
                 self.status_label, self.summary_label))
        except tk.TclError:
            return False

    def dispose(self) -> None:
        self._require_creator_thread()
        self.destroy()

    def destroy(self) -> None:
        self._require_creator_thread()
        if not self._alive:
            return
        self._alive = False
        self._document = None
        self.revision += 1
        self._on_destroy()
        # Remove traces before destroying managed widgets; no delayed callbacks.
        for variable, trace in self._traces:
            try:
                variable.trace_remove("write", trace)
            except tk.TclError:
                pass
        self._traces.clear()
        super().destroy()

    def _changed(self, *_):
        self._require_creator_thread()
        if not self._alive or self._loading:
            return
        self.revision += 1
        self._on_change()

    def load_document(self, document: PresentationConfigurationDocumentV1, *, present: bool):
        self._require_creator_thread()
        if type(document) is not PresentationConfigurationDocumentV1:
            raise TypeError("Exact presentation document required")
        self._document = document
        self._loading = True
        try:
            self.assistant_name.set(document.assistant.display_name)
            self.wake_name.set(document.assistant.wake_name)
            self.user_name.set(document.user.display_name or "")
        finally:
            self._loading = False
        self.revision += 1
        self.status_label.configure(text="Profile loaded. Review before saving." if present else
                                    "Default values; not saved. Review before saving.")
        self.set_controls(editable=True)

    def build_draft(self) -> PresentationConfigurationDocumentV1:
        self._require_creator_thread()
        if self._document is None:
            raise ValueError("No editable presentation document")
        assistant_name, wake_name, user_name = (
            self.assistant_name.get(), self.wake_name.get(), self.user_name.get())
        draft = PresentationConfigurationDocumentV1(
            schema_version=self._document.schema_version,
            assistant=AssistantPresentationIdentity(display_name=assistant_name, wake_name=wake_name),
            user=UserPresentationProfile(display_name=None if user_name == "" else user_name),
            preferences=self._document.preferences,
        )
        # Use the existing pure validator and reject unencodable display text.
        validated = parse_presentation_configuration_document(
            presentation_configuration_document_to_mapping(draft))
        for text in (assistant_name, wake_name, user_name):
            text.encode("utf-8")
        return validated

    def clear_review(self) -> None:
        self._require_creator_thread()
        self.summary_label.configure(text="No pending review. Review again after editing.")
        self.save_button.configure(state="disabled")

    def show_review(self, document: PresentationConfigurationDocumentV1) -> None:
        self._require_creator_thread()
        self.summary_label.configure(text=(
            "Pending changes (not saved)\n"
            f"Assistant: {document.assistant.display_name}\n"
            f"Wake name: {document.assistant.wake_name}\n"
            f"Your display name: {document.user.display_name or '(not set)'}"))
        self.status_label.configure(text="Review this frozen draft, then press Save to persist it.")

    def set_controls(self, *, editable: bool, reviewed: bool = False, busy: bool = False):
        self._require_creator_thread()
        for entry in self.entries:
            entry.configure(state="normal" if editable and not busy else "disabled")
        self.review_button.configure(state="normal" if editable and not busy else "disabled")
        self.save_button.configure(state="normal" if editable and reviewed and not busy else "disabled")
        self.cancel_button.configure(state="disabled" if busy else "normal")

    def show_status(self, text: str) -> None:
        self._require_creator_thread()
        self.status_label.configure(text=text)

    def focus_initial(self) -> None:
        self._require_creator_thread()
        (self.entries[0] if self._document is not None else self.cancel_button).focus_set()
