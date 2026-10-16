"""Opt-in B2a fake-only Tk harness; import creates no GUI or services.

Caller owns the B1 fixture/temp directory. No automatic event loop, observation,
reconciliation or admission. Empirical event dispatch remains a host B2b check.
"""


class SimulatedFirstRun:
    """One status root and at most one explicitly navigated management child."""

    def __init__(self, fixture):
        self._fixture = fixture
        self._root = self._status = None
        self._credential_button = self._metadata_button = self._refresh_button = None
        self._child = self._manager = None
        self._closed_manager = None
        self._blocked = self._finished = self._launched = False
        self._transition = False
        self._failure_type = None

    @property
    def failure_type(self):
        """Nonsecret category of the last refused Tk callback, if any."""
        return self._failure_type

    @property
    def root(self):
        return self._root

    @property
    def status_window(self):
        return self._status

    @property
    def credential_button(self):
        return self._credential_button

    @property
    def metadata_button(self):
        return self._metadata_button

    @property
    def refresh_button(self):
        return self._refresh_button

    @property
    def owned_child(self):
        """Last owned Toplevel, retained through closure for host assertions."""
        return self._child

    @property
    def owned_manager(self):
        return self._manager

    def launch(self):
        """Explicitly create one Tk; never allocate or substitute a fixture."""
        from tests.phase_829_integrated_support import IntegratedComposition

        if self._launched or self._finished:
            raise RuntimeError("Simulation cannot be relaunched")
        if type(self._fixture) is not IntegratedComposition:
            raise TypeError("Exact B1 IntegratedComposition required")
        self._fixture.check_unstarted()
        self._fixture.check_bindings()

        import tkinter as tk
        from nayeon.desktop_alpha.first_run_status_window import FirstRunStatusWindow

        self._launched = True
        root = self._root = tk.Tk()
        try:
            root.withdraw()
            self._status = FirstRunStatusWindow(root, controller=self._fixture.status)
            # Public Tk APIs only; no production panel internals are modified.
            refresh, = (widget for widget in root.winfo_children()
                        if isinstance(widget, tk.Button)
                        and widget.cget("text") == "Refresh status")
            self._refresh_button = refresh
            refresh.configure(command=self._refresh)
            self._credential_button = tk.Button(
                root, name="credential_navigation", text="Manage fake credential",
                command=lambda: self._dispatch_navigation("credential"))
            self._metadata_button = tk.Button(
                root, name="metadata_navigation", text="Manage fake metadata",
                command=lambda: self._dispatch_navigation("metadata"))
            for button in (self._credential_button, self._metadata_button):
                button.pack(anchor="w", padx=20, pady=3)
            root.geometry("620x480")
            root.protocol("WM_DELETE_WINDOW", self.finish)
            self._fixture.check_unstarted()
            root.deiconify()
        except Exception:
            self._blocked = True
            root.destroy()
            raise
        return self

    def _check_event(self, button):
        if (self._blocked or self._finished or not self._launched
                or button is None or not button.winfo_ismapped()):
            raise RuntimeError("Mapped simulation control required")
        try:
            self._fixture.check_bindings()
        except Exception:
            self._blocked = True
            raise

    def _refresh(self):
        self._check_event(self._refresh_button)
        self._status.refresh_from_button()

    def _authority_clear(self):
        """Read-only cross-host release evidence; never reset shared state."""
        fixture = self._fixture
        ctrl = fixture.controller
        coord = fixture.credential.coordinator
        return (all(value is None for value in (
                    ctrl._ctx, ctrl._owner, ctrl._ui_window_owner, ctrl._active,
                    ctrl._review, ctrl._epoch, coord._pending, coord._operation,
                    coord._ui_ticket, fixture.metadata_host._ui_owner,
                    fixture.metadata_host._pending, fixture.metadata_host._ui_ticket))
                and not ctrl._release_uncertain and not ctrl._ready
                and not fixture.mutex.active
                and fixture.mutex.entries == fixture.mutex.exits
                and not fixture.credential.host.has_pending)

    def _closed_child(self):
        manager = self._manager
        return (manager is None or (
            self._closed_manager is manager
            and manager._closed and not manager._busy and not manager._close_deferred
            and manager._owner_token is None
            and not self._child.winfo_exists()))

    def _dispatch_navigation(self, kind):
        """Ignore unmapped/closed Tk events before entering trusted navigation."""
        if self._blocked or self._finished or not self._launched:
            return
        button = (self._credential_button if kind == "credential"
                  else self._metadata_button if kind == "metadata" else None)
        if button is None:
            return
        try:
            if not button.winfo_ismapped():
                return
        except Exception:
            return
        if self._transition:
            self._blocked = True
            return
        self._transition = True
        try:
            self._navigate(kind)
        except Exception as exc:
            self._blocked = True
            self._failure_type = type(exc).__name__
        finally:
            self._transition = False

    def _navigate(self, kind):
        import tkinter as tk
        from nayeon.desktop_alpha.first_run_credential_management_window import (
            FirstRunCredentialManagementWindow,
        )
        from nayeon.desktop_alpha.first_run_metadata_management_window import (
            FirstRunMetadataManagementWindow,
        )

        if kind == "credential":
            button = self._credential_button
        elif kind == "metadata":
            button = self._metadata_button
        else:
            raise ValueError("Unknown simulation navigation")
        self._check_event(button)
        # Never close a prior manager just to satisfy a navigation request.
        if not self._closed_child() or not self._authority_clear():
            raise RuntimeError("Prior owner must complete its own close first")
        child = tk.Toplevel(master=self._root)
        try:
            child.withdraw()
            if kind == "credential":
                manager = FirstRunCredentialManagementWindow(
                    root=child, coordinator=self._fixture.credential.coordinator)
                owns = self._fixture.controller.is_ui_window_owner(manager._owner_token)
            else:
                manager = FirstRunMetadataManagementWindow(
                    root=child, host=self._fixture.metadata_host)
                owns = self._fixture.metadata_host.has_ui_owner(owner=manager._owner_token)
            if not owns or self._blocked:
                raise RuntimeError("Management child lost exclusive ownership")
            self._fixture.check_bindings()
            self._child, self._manager = child, manager
            self._closed_manager = None
            child.protocol("WM_DELETE_WINDOW", self.close_current)
            child.deiconify()
        except Exception:
            self._blocked = True
            # Only this attempted child is destroyed. Its existing exact-owner
            # Destroy handler cannot release a competing manager's owner.
            try:
                child.withdraw()
            finally:
                child.destroy()
            raise

    def close_current(self):
        """Explicit exact-manager close; successful return is handover evidence."""
        if self._transition:
            self._blocked = True
            raise RuntimeError("Management transition still in progress")
        manager = self._manager
        if manager is None:
            return
        manager.close_from_window()
        if (not manager._closed or manager._busy or manager._close_deferred
                or manager._owner_token is not None
                or self._child.winfo_exists() or not self._authority_clear()):
            raise RuntimeError("Management close incomplete; handover refused")
        self._closed_manager = manager

    def finish(self):
        """Close only our manager; retain root on busy/uncertain cleanup.

        No global controller close, pool mutation, temp cleanup or reconcile.
        """
        if self._transition:
            self._blocked = True
            raise RuntimeError("Cannot finish during management transition")
        if self._finished:
            return
        if not self._launched or self._root is None:
            self._finished = True
            return
        self.close_current()
        if not self._closed_child() or not self._authority_clear():
            raise RuntimeError("Simulation cleanup incomplete; root retained")
        self._root.destroy()
        self._finished = True

    close = finish


def launch(fixture):
    """Explicit test entrypoint; returns without starting a Tk event loop."""
    return SimulatedFirstRun(fixture).launch()
