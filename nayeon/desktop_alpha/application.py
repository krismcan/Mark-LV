"""Trusted single-root composition for the bounded offline workspace.

Profile admission is lazy: only explicit Settings entry constructs an owner and
loads an edit. Only the separate Save callback may issue and consume its review.
No profile destination, model, connection or action service is composed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import tkinter as tk

from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.desktop_alpha.controller import PreviewOnlyController
from nayeon.desktop_alpha.presentation_window import PresentationWindow
from nayeon.desktop_alpha.workspace_window import (
    ConnectionWindow, ConversationWindow, WorkspaceWindow,
)


class _Page(Enum):
    CONVERSATION = "conversation"
    SETTINGS = "settings"
    CONNECTION = "connection"


@dataclass(frozen=True, slots=True, repr=False)
class _PendingDraft:
    view: PresentationWindow
    token: object
    generation: int
    revision: int
    document: PresentationConfigurationDocumentV1


class OfflineWorkspaceApplication:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.controller = PreviewOnlyController()
        self._root_alive = True
        self._closed = False
        self._busy = False
        self._operation_token = None
        self._generation = 0
        self._active_token = None
        self._active_view = None
        self._profile_owner = None
        self._owner_active = False
        self._edit = None
        self._pending = None
        self._published_document = PresentationConfigurationDocumentV1()
        root.title("Nayeon | Offline Preview")
        root.geometry("860x680")
        root.minsize(680, 600)
        root.configure(background="#f3f6fb")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Destroy>", self._root_destroyed, add="+")
        self.workspace = WorkspaceWindow(
            root, on_conversation=self.show_conversation, on_settings=self.show_settings,
            on_connection=self.show_connection)
        self._bootstrap_readonly_presentation()
        self.show_conversation()

    def _bootstrap_readonly_presentation(self) -> None:
        """On explicit startup, read exactly the profile, with no Save authority.

        An invalid existing profile is visibly unavailable, never treated as an
        empty one and never automatically repaired or overwritten.
        """
        owner = None
        try:
            from nayeon.desktop_alpha.presentation_profile_owner import (
                create_production_presentation_profile_owner,
            )
            owner = create_production_presentation_profile_owner(
                owner_is_current=self._root_exists)
            edit = owner.load_for_edit()
            document, present = edit.document, edit.snapshot.present
            owner.invalidate()
            owner = None
            if not self._root_exists():
                return
            if present:
                self._published_document = document
                self.workspace.publish_name(document.assistant.display_name)
                self.root.title(document.assistant.display_name + " | Offline Preview")
                self.workspace.publish_profile_status(
                    "Verified saved presentation loaded (read-only).")
            else:
                self.workspace.publish_profile_status(
                    "Default presentation in use; no local profile has been saved.")
        except Exception:
            if self._root_exists():
                self.workspace.publish_profile_status(
                    "Presentation profile unavailable; existing storage was not changed. "
                    "Settings Save will require a fresh valid load.")
        finally:
            if owner is not None:
                try:
                    owner.invalidate()
                except Exception:
                    pass

    def _root_exists(self) -> bool:
        if self._closed or not self._root_alive:
            return False
        try:
            return bool(self.root.winfo_exists())
        except tk.TclError:
            return False

    def _current(self, view, token, generation) -> bool:
        # Identity is checked before any Tk access; stale callbacks cannot even
        # query a destroyed interpreter or disturb a successor's owner.
        return (not self._closed and self._root_alive
                and self._active_view is view and self._active_token is token
                and self._generation == generation and self._root_exists()
                and view.exists())

    def _owner_current(self, view, token, generation) -> bool:
        return self._owner_active and self._current(view, token, generation)

    def _invalidate_owner(self) -> bool:
        self._owner_active = False
        self._edit = self._pending = None
        owner, self._profile_owner = self._profile_owner, None
        if owner is not None:
            try:
                owner.invalidate()
            except Exception:
                # Independent view/token revocation already denies all further
                # effects even if this trusted cleanup dependency refuses.
                return False
        return True

    def _interrupt_operation(self) -> None:
        # A nested callback never starts a second operation. Revoke the outer
        # operation too, so a caught reentrant event cannot restore consent.
        self._operation_token = None
        self._invalidate_owner()

    def _retire_view(self) -> None:
        view = self._active_view
        self._active_view = self._active_token = None
        self._operation_token = None
        self._generation += 1
        self._invalidate_owner()
        if view is not None and self._root_exists():
            view.dispose()

    def _view_destroyed(self, view, token, generation) -> None:
        # Destroy handlers perform only Python-side revocation, never Tk calls.
        if (self._active_view is view and self._active_token is token
                and self._generation == generation):
            self._active_view = self._active_token = None
            self._operation_token = None
            self._generation += 1
            self._invalidate_owner()

    def _root_destroyed(self, event) -> None:
        if event.widget is self.root:
            self._root_alive = False
            self._closed = True
            self._active_view = self._active_token = None
            self._operation_token = None
            self._generation += 1
            self._invalidate_owner()

    def close(self) -> None:
        if self._closed:
            return
        was_alive = self._root_exists()
        # Revoke before widget destruction dispatches any Destroy bindings.
        self._closed = True
        self._root_alive = False
        view, self._active_view = self._active_view, None
        self._active_token = self._operation_token = None
        self._generation += 1
        self._invalidate_owner()
        if was_alive:
            try:
                if view is not None:
                    view.dispose()
            finally:
                try:
                    self.root.destroy()
                except tk.TclError:
                    pass

    def show_conversation(self) -> None:
        self._show(_Page.CONVERSATION)

    def show_settings(self) -> None:
        self._show(_Page.SETTINGS)

    def show_connection(self) -> None:
        self._show(_Page.CONNECTION)

    def _show(self, page: _Page) -> None:
        if not self._root_exists():
            return
        if self._busy:
            self._interrupt_operation()
            return
        self._busy = True
        try:
            self.workspace.set_busy(True)
            self._retire_view()
            if not self._root_exists():
                return
            token, generation = object(), self._generation
            if page is _Page.CONVERSATION:
                view = ConversationWindow(
                    self.workspace.content, controller=self.controller,
                    assistant_name=self._published_document.assistant.display_name,
                    user_name=self._published_document.user.display_name or "You",
                    is_current=lambda: self._current(view, token, generation),
                    on_destroy=lambda: self._view_destroyed(view, token, generation))
            elif page is _Page.CONNECTION:
                view = ConnectionWindow(
                    self.workspace.content,
                    on_destroy=lambda: self._view_destroyed(view, token, generation),
                    on_conversation=lambda: self._cancel(view, token, generation))
            elif page is _Page.SETTINGS:
                view = PresentationWindow(
                    self.workspace.content,
                    on_change=lambda: self._changed(view, token, generation),
                    on_review=lambda: self._review(view, token, generation),
                    on_save=lambda: self._save(view, token, generation),
                    on_cancel=lambda: self._cancel(view, token, generation),
                    on_destroy=lambda: self._view_destroyed(view, token, generation))
            else:
                raise ValueError("Unsupported offline page")
            self._active_view, self._active_token = view, token
            view.pack(fill="both", expand=True)
            if page is _Page.SETTINGS:
                self._load_settings(view, token, generation)
            if self._current(view, token, generation):
                view.focus_initial()
        finally:
            self._busy = False
            if self._root_exists():
                self.workspace.set_busy(False)

    def _load_settings(self, view, token, generation) -> None:
        try:
            from nayeon.desktop_alpha.presentation_profile_owner import (
                create_production_presentation_profile_owner,
            )
            self._owner_active = True
            owner = create_production_presentation_profile_owner(
                owner_is_current=lambda: self._owner_current(view, token, generation))
            self._profile_owner = owner
            edit = owner.load_for_edit()
            if not self._owner_current(view, token, generation):
                owner.invalidate()
                raise ValueError("Settings load revoked")
            self._edit = edit
            view.load_document(edit.document, present=edit.snapshot.present)
            if self._edit is not edit or not self._owner_current(view, token, generation):
                raise ValueError("Settings load revoked")
        except Exception:
            self._invalidate_owner()
            if self._current(view, token, generation):
                view.set_controls(editable=False)
                view.show_status("Presentation settings unavailable. Save is disabled. "
                                 "Return to Conversation or reopen Settings to try a fresh load.")

    def _cancel(self, view, token, generation) -> None:
        if self._current(view, token, generation):
            self.show_conversation()

    def _changed(self, view, token, generation) -> None:
        if not self._current(view, token, generation):
            return
        self._pending = None
        if self._busy:
            self._interrupt_operation()
            return
        view.clear_review()
        view.set_controls(editable=self._edit is not None)
        if self._edit is not None:
            view.show_status("Changes are not saved. Review again before Save.")

    def _review(self, view, token, generation) -> None:
        if not self._current(view, token, generation):
            return
        if self._busy:
            self._interrupt_operation()
            return
        if self._edit is None or not self._owner_active:
            return
        self._busy = True
        self._pending = None
        edit, revision = self._edit, view.revision
        try:
            self.workspace.set_busy(True)
            view.set_controls(editable=False, busy=True)
            draft = view.build_draft()
            if (not self._owner_current(view, token, generation)
                    or self._edit is not edit or view.revision != revision):
                return
            view.show_review(draft)
            if (self._owner_current(view, token, generation)
                    and self._edit is edit and view.revision == revision):
                self._pending = _PendingDraft(view, token, generation, revision, draft)
        except Exception:
            if self._current(view, token, generation):
                view.clear_review()
                view.show_status("Use names of 1–64 characters without surrounding spaces or "
                                 "control characters. Your display name may be blank.")
        finally:
            self._busy = False
            if self._root_exists():
                self.workspace.set_busy(False)
            if self._current(view, token, generation):
                editable = self._edit is edit and self._owner_active
                view.set_controls(editable=editable, reviewed=self._pending is not None)
                if not editable:
                    view.clear_review()
                    view.show_status("This edit has expired. Reopen Settings to load and review again.")

    def _save(self, view, token, generation) -> None:
        if not self._current(view, token, generation):
            return
        if self._busy:
            self._interrupt_operation()
            return
        pending, edit, owner = self._pending, self._edit, self._profile_owner
        if (pending is None or edit is None or owner is None or not self._owner_active
                or pending.view is not view or pending.token is not token
                or pending.generation != generation or pending.revision != view.revision):
            return
        self._busy = True
        save_token = object()
        self._operation_token = save_token
        verified = None
        message = "Save refused. Reopen Settings to load and review again."
        try:
            self.workspace.set_busy(True)
            view.set_controls(editable=False, busy=True)
            if (view.build_draft() != pending.document
                    or not self._owner_current(view, token, generation)
                    or self._pending is not pending or self._edit is not edit
                    or view.revision != pending.revision):
                return
            # Consume the UI review before any trusted transaction boundary.
            self._pending = None
            review = owner.review_save(edit, pending.document)
            if (not self._owner_current(view, token, generation)
                    or self._edit is not edit or view.revision != pending.revision):
                return
            result = owner.save(review)
            if (self._owner_current(view, token, generation)
                    and self._edit is edit and view.revision == pending.revision
                    and self._operation_token is save_token
                    and type(result) is PresentationConfigurationDocumentV1
                    and result == pending.document):
                verified = result
            else:
                message = "Storage may have changed; unverified. Reopen Settings before any new Save."
        except Exception as error:
            # Only fixed public text crosses into Tk; never str/repr(error).
            from nayeon.desktop_alpha.presentation_profile_owner import (
                ProfileBusy, ProfileConflict, ProfileUnverified,
            )
            if isinstance(error, ProfileUnverified):
                message = "Storage may have changed; unverified. Reopen Settings before any new Save."
            elif isinstance(error, ProfileConflict):
                message = "Profile changed elsewhere; reload before saving. Reopen Settings."
            elif isinstance(error, ProfileBusy):
                message = "Profile is busy. Reopen Settings and review again before saving."
        finally:
            if not self._invalidate_owner():
                verified = None
                message = "Storage may have changed; unverified. Reopen Settings before any new Save."
            if self._current(view, token, generation):
                view.clear_review()
            if self._current(view, token, generation):
                view.set_controls(editable=False)
            if self._current(view, token, generation):
                if verified is not None and self._operation_token is save_token:
                    # The owner returned after independent readback AND release.
                    # A newly selected view never receives the old one's result.
                    self.root.title(verified.assistant.display_name + " | Offline Preview")
                    if (self._current(view, token, generation)
                            and self._operation_token is save_token):
                        self.workspace.publish_name(verified.assistant.display_name)
                    if (self._current(view, token, generation)
                            and self._operation_token is save_token):
                        self._published_document = verified
                        self.workspace.publish_profile_status(
                            "Verified saved presentation loaded (read-only).")
                        view.show_status("Saved and verified. Reopen Settings for a new edit.")
                else:
                    view.show_status(message)
            if self._operation_token is save_token:
                self._operation_token = None
            self._busy = False
            if self._root_exists():
                self.workspace.set_busy(False)


def main() -> None:
    """Explicit launch only: one root, one event loop, no background work."""
    root = tk.Tk()
    application = None
    try:
        application = OfflineWorkspaceApplication(root)
        root.mainloop()
    finally:
        if application is not None:
            application.close()
        else:
            try:
                root.destroy()
            except tk.TclError:
                pass
