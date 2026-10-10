"""Phase 8.22: explicitly refreshed, read-only first-run desktop panel.

The panel is a presentation surface only. No automatic observation on startup,
secret fields, action buttons, model access or credential operations exist.
A trusted parent can mount it with a separately constructed controller.
"""
import tkinter as tk

from nayeon.brain.first_run_refresh import (
    FirstRunReadOnlyController, FirstRunRefresh, FirstRunRefreshStatus,
)


class FirstRunStatusWindow:
    """Small Tk first-run status panel; all effects require a human Refresh click."""

    def __init__(self, root: tk.Tk, *, controller: FirstRunReadOnlyController):
        if type(controller) is not FirstRunReadOnlyController:
            raise TypeError("Exact read-only first-run controller required")
        self._controller = controller
        self._root = root
        root.title("Nayeon | First-run connection review")
        root.geometry("620x360")
        root.minsize(480, 290)
        root.configure(bg="#101827")
        tk.Label(root, text="Nayeon · Connection review",
                 bg="#101827", fg="#f1f4fb",
                 font=("Segoe UI", 18, "bold")).pack(padx=20, pady=(20, 8), anchor="w")
        tk.Label(root, text="Status only. No keys are read or changed on launch.",
                 bg="#101827", fg="#adc1d6",
                 font=("Segoe UI", 10)).pack(padx=20, anchor="w")
        self._status = tk.Label(root, text="Not observed",
                                bg="#101827", fg="#9ac8ff",
                                font=("Segoe UI", 12, "bold"),
                                wraplength=550, justify="left")
        self._status.pack(padx=20, pady=(18, 10), anchor="w")
        self._details = tk.Label(root, text="Click Refresh status to request one read-only observation.",
                                 bg="#101827", fg="#bfcde0",
                                 font=("Segoe UI", 10),
                                 wraplength=550, justify="left")
        self._details.pack(padx=20, anchor="w")
        self._refresh = tk.Button(root, text="Refresh status",
                                  command=self.refresh_from_button,
                                  bg="#79b9ff", fg="#101827", relief="flat",
                                  padx=18, pady=8)
        self._refresh.pack(padx=20, pady=(22, 14), anchor="w")
        tk.Label(root, text="Credential management and validation are not available in this panel.",
                 bg="#101827", fg="#adc1d6",
                 font=("Segoe UI", 9), wraplength=550,
                 justify="left").pack(padx=20, anchor="w")

    def refresh_from_button(self):
        """The sole UI callback. Never forwards arbitrary text to a capability."""
        self._refresh.configure(state="disabled")
        try:
            result = self._controller.refresh()
            self._show(result)
        except Exception:
            self._status.configure(text="Status unavailable")
            self._details.configure(text="No current status is verified. Try a new explicit refresh.")
        finally:
            self._refresh.configure(state="normal")

    def _show(self, result: FirstRunRefresh):
        if type(result) is not FirstRunRefresh or result.status is not FirstRunRefreshStatus.OBSERVED:
            self._status.configure(text="Status unavailable")
            self._details.configure(text="No current status is verified. Try a new explicit refresh.")
            return
        summary = result.summary
        self._status.configure(text="Observed state: " + " ".join(summary.state.value.split("_")))
        suggested = ", ".join(" ".join(op.value.split("_")) for op in summary.suggested_operations)
        message = ("Suggested next steps: " + suggested if suggested
                   else "No credential operation is suggested for this state.")
        self._details.configure(text=message + " This is not authorization or validation.")
