"""P319 real offline host route with inert widgets; no Tk, files or services."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nayeon.brain import first_run_refresh as refresh
from nayeon.desktop_alpha import first_run_connection_window as host
from nayeon.desktop_alpha import first_run_status_window as panel
from nayeon.desktop_alpha.application import OfflineWorkspaceApplication


class Widget:
    """Fail on stale UI access, including access after parent destruction."""

    def __init__(self, master=None, **props):
        self.master, self.props = master, props
        self.children, self.calls, self.handlers = [], [], {}
        self.alive = self._alive = True
        if master is not None:
            master.children.append(self)

    def touch(self, name):
        if not self.alive:
            raise AssertionError("stale widget access")
        self.calls.append(name)

    def pack(self, **kwargs):
        self.touch("pack")

    def configure(self, **kwargs):
        self.touch("configure")
        self.props.update(kwargs)

    def title(self, *args):
        self.touch("title")

    def protocol(self, name, callback):
        self.touch("protocol")
        self.handlers[name] = callback

    def bind(self, name, callback, **kwargs):
        self.touch("bind")
        self.handlers[name] = callback

    def invoke(self):
        self.touch("invoke")
        if self.props.get("state") != "disabled":
            self.props["command"]()

    def winfo_exists(self):
        return self.alive

    def destroy(self):
        if not self.alive:
            return
        self.alive = self._alive = False
        for child in tuple(self.children):
            child.destroy()
        if "<Destroy>" in self.handlers:
            self.handlers["<Destroy>"](SimpleNamespace(widget=self))

    dispose = destroy


class OfflineRecoveryHostTests(unittest.TestCase):
    def setUp(self):
        # Patch every widget before invoking the existing real host route.
        for module, names in ((host.tk, ("Toplevel", "Frame", "Label", "Button")),
                              (host.ttk, ("Label", "Button"))):
            for name in names:
                self.enterContext(patch.object(module, name, Widget))
        self.app = app = OfflineWorkspaceApplication.__new__(OfflineWorkspaceApplication)
        app._creator_thread = threading.get_ident()
        app.root = Widget()
        app._connection_application = object()
        app._connection = None
        app._connection_coordinator = app._connection_test_harness = None
        app._connection_opening = app._connection_blocked = False
        app._busy = app._reply_busy = app._reply_closing = app._closed = False
        app._root_alive = True
        app._generation = 1
        app._active_view, app._active_token = Widget(app.root), object()
        app._active_view.status_label = Widget(app._active_view)
        # Only unrelated conversation/settings teardown dependencies are fake.
        # Connection opening, retirement, view navigation and close are real.
        app._revoke_conversation_view = Mock()
        app._invalidate_owner = Mock()
        app._reply_owner = Mock(has_worker=False)
        app._reply_notice = Mock()
        app._reply_release_anchor = Mock()
        app._reply_cancel = Mock()
        app._reply_views = []
        app._reply_serial = 0
        app._completion = Mock()
        app._conversation = Mock()
        app._conversation_root = object()
        app.workspace = Mock()
        self.addCleanup(app._retire_connection)

    def open(self):
        app = self.app
        app._open_connection(app._active_view, app._active_token, app._generation)
        return app._connection

    def review(self):
        window = self.open()
        window.recovery_button.invoke()
        return window, window._recovery_panel

    def assert_unavailable(self, ui):
        self.assertEqual(ui._status.props["text"], "Status unavailable")
        self.assertIn("Manual unknown-state review", ui._details.props["text"])
        self.assertIn("Recovery is unverified", ui._details.props["text"])
        self.assertIn("No credential operation is suggested", ui._details.props["text"])
        self.assertNotIn("Synthetic paired observation", ui._details.props["text"])
        self.assertEqual(ui._refresh.props["state"], "normal")

    def new_pane(self):
        app = self.app
        app._active_view, app._active_token = Widget(app.root), object()
        app._active_view.status_label = Widget(app._active_view)

    def test_existing_route_opens_once_and_never_refreshes_on_open(self):
        with patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
            window = self.open()
            self.assertIs(self.open(), window)
            self.assertIsNone(window._recovery_panel)
            observe.assert_not_called()
        self.assertIs(window.child.master, self.app.root)
        self.assertIsNone(window.owner)
        self.assertFalse(window._enabled)
        self.assertEqual(len(self.app.root.children), 2)  # pane and exact child
        for button in (window.candidate_button, window.stored_button,
                       window.confirm_button, window.cancel_button):
            self.assertEqual(button.props["state"], "disabled")

    def test_explicit_action_mounts_existing_panel_without_inventing_observation(self):
        window, ui = self.review()
        self.assertIs(type(ui), panel.FirstRunStatusWindow)
        self.assertIs(type(ui._controller), refresh.FirstRunReadOnlyController)
        self.assertTrue(ui._controller.uses_paired_synthetic_observation)
        result = ui._controller.refresh()
        self.assertIs(result.status, refresh.FirstRunRefreshStatus.UNAVAILABLE)
        self.assertIsNone(result.summary)
        self.assert_unavailable(ui)
        self.assertIs(ui._root.master, window.child)
        self.assertEqual(len(self.app.root.children), 2)
        self.assertNotIn("title", ui._root.calls)  # embedded, not another window
        self.assertIsNone(window.context)
        self.assertIsNone(window.review)

    def test_repeated_explicit_clicks_reuse_panel_and_never_progress(self):
        window, ui = self.review()
        with patch.object(ui._controller.__class__, "refresh",
                          wraps=ui._controller.refresh) as observe:
            for _ in range(3):
                window.recovery_button.invoke()
                ui._refresh.invoke()
                self.assert_unavailable(ui)
                self.assertIs(window._recovery_panel, ui)
            self.assertEqual(observe.call_count, 6)
        self.assertIsNone(window.owner)
        self.assertFalse(self.app._connection_blocked)

    def test_controller_exception_is_sanitized_and_only_next_click_retries(self):
        window, ui = self.review()
        with patch.object(refresh.FirstRunReadOnlyController, "refresh",
                          side_effect=RuntimeError("private-marker")) as observe:
            window.recovery_button.invoke()
            observe.assert_called_once_with()
        self.assert_unavailable(ui)
        self.assertNotIn("private-marker", str(ui._details.props))
        self.assertTrue(window.is_current())
        ui._refresh.invoke()
        self.assert_unavailable(ui)

    def test_malformed_result_replaces_previous_display(self):
        window, ui = self.review()
        ui._status.props["text"] = "old display"
        ui._details.props["text"] = "old details"
        with patch.object(refresh.FirstRunReadOnlyController, "refresh", return_value=object()):
            window.recovery_button.invoke()
        self.assert_unavailable(ui)
        self.assertNotIn("old", str(ui._details.props))

    def test_panel_construction_failure_retires_exact_child(self):
        window = self.open()
        with patch.object(panel, "FirstRunStatusWindow", side_effect=RuntimeError("private-marker")):
            window.recovery_button.invoke()
        self.assertFalse(window.is_current())
        self.assertFalse(window.child.alive)
        self.assertIsNone(self.app._connection)
        self.assertFalse(window._recovery_opening)
        window.review_recovery_status()
        self.assertIsNone(window._recovery_panel)

    def test_uncertain_cleanup_quarantines_existing_route(self):
        window = self.open()
        with patch.object(panel, "FirstRunStatusWindow", side_effect=RuntimeError("fixture")), \
                patch.object(window.child, "destroy", side_effect=RuntimeError("fixture")):
            window.recovery_button.invoke()
        self.assertTrue(self.app._connection_blocked)
        self.assertIs(self.open(), window)
        self.assertFalse(window.is_current())
        self.assertIsNone(window._recovery_panel)

    def test_real_view_retirement_revokes_old_panel_before_successor(self):
        first, ui = self.review()
        self.app._retire_view()
        self.new_pane()
        second, current = self.review()
        snapshot = dict(current._details.props)
        with patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
            first.review_recovery_status()
            ui.refresh_from_button()
            first.retire()
            observe.assert_not_called()
        self.assertIs(self.app._connection, second)
        self.assertTrue(second.is_current())
        self.assertEqual(current._details.props, snapshot)

    def test_real_application_close_revokes_all_saved_callbacks(self):
        window, ui = self.review()
        self.app.close()
        with patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
            window.review_recovery_status()
            ui.refresh_from_button()
            observe.assert_not_called()
        self.assertTrue(self.app._closed)
        self.assertFalse(self.app.root.alive)

    def test_real_root_destroy_handler_revokes_without_ui_access(self):
        window, ui = self.review()
        self.app.root.destroy()
        self.app._root_destroyed(SimpleNamespace(widget=self.app.root))
        with patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
            ui.refresh_from_button()
            window.review_recovery_status()
            observe.assert_not_called()
        self.assertFalse(window.is_current())
        self.assertTrue(self.app._closed)

    def test_external_exact_child_close_revokes_saved_panel_callback(self):
        window, ui = self.review()
        window._destroyed(SimpleNamespace(widget=window.status))
        self.assertTrue(window.is_current())
        window.child.handlers["WM_DELETE_WINDOW"]()
        with patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
            ui.refresh_from_button()
            window.review_recovery_status()
            observe.assert_not_called()
        self.assertIsNone(self.app._connection)

    def test_all_existing_identity_guards_also_guard_panel_refresh(self):
        window, ui = self.review()
        mutations = ((self.app, "root", Widget()),
                     (self.app, "_connection_application", object()),
                     (self.app, "_active_view", Widget()),
                     (self.app, "_active_token", object()),
                     (self.app, "_generation", 99),
                     (self.app, "_connection", object()),
                     (self.app, "_connection_blocked", True),
                     (window, "child", Widget()))
        for target, name, value in mutations:
            with self.subTest(name=name), patch.object(target, name, value), \
                    patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
                ui.refresh_from_button()
                window.review_recovery_status()
                observe.assert_not_called()

    def test_nested_panel_and_host_refresh_do_not_reenter_observer(self):
        window, ui = self.review()
        def reenter():
            ui.refresh_from_button()
            window.review_recovery_status()
            return refresh.FirstRunRefresh(refresh.FirstRunRefreshStatus.UNAVAILABLE)
        with patch.object(refresh.FirstRunReadOnlyController, "refresh", side_effect=reenter) as observe:
            ui.refresh_from_button()
            observe.assert_called_once_with()
        self.assert_unavailable(ui)

    def test_navigation_inside_refresh_discards_result_and_never_touches_dead_widgets(self):
        window, ui = self.review()
        def navigate():
            self.app._retire_view()
            return refresh.FirstRunRefresh(refresh.FirstRunRefreshStatus.UNAVAILABLE)
        with patch.object(refresh.FirstRunReadOnlyController, "refresh", side_effect=navigate), \
                patch.object(ui, "_show") as show, patch.object(ui, "_show_unavailable") as unavailable:
            window.recovery_button.invoke()
            show.assert_not_called()
            unavailable.assert_not_called()
        self.assertFalse(window.is_current())

    def test_navigation_during_status_write_stops_further_writes(self):
        window, ui = self.review()
        original = ui._status.configure
        def navigate(**kwargs):
            original(**kwargs)
            self.app._retire_view()
        with patch.object(ui._status, "configure", side_effect=navigate), \
                patch.object(ui._details, "configure") as details:
            ui.refresh_from_button()
            details.assert_not_called()
        self.assertFalse(window.is_current())

    def test_wrong_thread_refuses_before_observer_or_widgets(self):
        window, ui = self.review()
        with patch.object(host.threading, "get_ident", return_value=-1), \
                patch.object(refresh.FirstRunReadOnlyController, "refresh") as observe:
            for call in (window.review_recovery_status, ui.refresh_from_button):
                with self.assertRaisesRegex(RuntimeError, "^WRONG_THREAD$"):
                    call()
            observe.assert_not_called()

    def test_nested_panel_mount_uses_existing_host_latch(self):
        window = self.open()
        original = panel.FirstRunStatusWindow
        def mount(*args, **kwargs):
            window.review_recovery_status()
            return original(*args, **kwargs)
        with patch.object(panel, "FirstRunStatusWindow", side_effect=mount) as construct:
            window.recovery_button.invoke()
            self.assertEqual(construct.call_count, 1)
        self.assert_unavailable(window._recovery_panel)

    def test_recovery_never_queries_or_adopts_fake_harness(self):
        window = self.open()
        harness, coordinator = Mock(), Mock()
        self.app._connection_test_harness = harness
        self.app._connection_coordinator = coordinator
        window.recovery_button.invoke()
        harness.assert_not_called()
        coordinator.assert_not_called()
        self.assertEqual(harness.mock_calls, [])
        self.assertEqual(coordinator.mock_calls, [])
        self.assertIs(self.app._connection_test_harness, harness)
        self.assertIs(self.app._connection_coordinator, coordinator)
        self.assertIsNone(window.owner)
        self.assertIsNone(window.context)
        self.assert_unavailable(window._recovery_panel)

    def test_existing_partial_child_constructor_failure_remains_quarantined(self):
        with patch.object(Widget, "__init__", side_effect=RuntimeError("fixture")):
            window = self.open()
        self.assertTrue(self.app._connection_blocked)
        self.assertFalse(window.is_current())
        self.assertIs(self.open(), window)

    def test_existing_raise_after_child_creation_cleans_exact_child(self):
        original = Widget.__init__
        def fail(child, *args, **kwargs):
            original(child, *args, **kwargs)
            raise RuntimeError("fixture")
        with patch.object(Widget, "__init__", new=fail):
            self.assertIsNone(self.open())
        self.assertFalse(self.app._connection_opening)
        self.assertFalse(self.app._connection_blocked)
        self.assertFalse(self.app.root.children[-1].alive)
