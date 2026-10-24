"""Trusted single-root composition for the bounded offline workspace.

Profile admission is lazy: only explicit Settings entry constructs an owner and
loads an edit. Only the separate Save callback may issue and consume its review.
No profile destination, model, connection or action service is composed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import tkinter as tk
import time
import threading

from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.desktop_alpha.controller import PreviewOnlyController
from nayeon.desktop_alpha.conversation_session import (
    OfflineConversationSession, ResetOperation, SessionRefused,
)
from nayeon.desktop_alpha.presentation_window import PresentationWindow
from nayeon.desktop_alpha.offline_completion_admission import (
    CANCELLED, UNAVAILABLE, WAITING, DelayedOfflineCompletion,
)
from nayeon.desktop_alpha.workspace_window import (
    ConnectionWindow, ConversationWindow, WorkspaceWindow,
    REPLY_CANCELLED, REPLY_DRAINING, REPLY_HOLD, REPLY_WAITING,
)
from nayeon.desktop_alpha.reply_contracts import (
    DEADLINE_MS, ERROR_TEXT, ReplyContext, ReplyRefused, ReplyState,
)
from nayeon.desktop_alpha.reply_owner import ReplyOwner


# A physical worker must never become the last owner of an interpreter graph.
# This creator-thread registry survives timer loss, view revocation and mainloop
# unwind. Only positively observed physical retirement permits removal.
_REPLY_LIFETIMES = {}


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


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class _ReplyBinding:
    view: ConversationWindow
    token: object
    generation: int
    context: ReplyContext
    snapshot: object
    deadline: int
    serial: int


class OfflineWorkspaceApplication:
    def __init__(self, root: tk.Tk):
        self._creator_thread = threading.get_ident()
        self.root = root
        self.controller = PreviewOnlyController()
        self._conversation_root = object()
        self._conversation = OfflineConversationSession(self._conversation_root)
        self._completion = DelayedOfflineCompletion(root)
        self._reply_owner = ReplyOwner(self._conversation_root)
        self._reply_context = self._reply_binding = self._reply_ticket = None
        self._reply_serial = 0
        self._reply_busy = self._reply_closing = False
        self._reply_destroy_save = None
        self._reply_navigation = None
        self._reply_invalidation = None
        self._reply_graph = None
        # Disposed panes can still own Python/Tcl variable cycles. Keep the
        # managed graph on its creator through this root's lifetime, including
        # panes retired before the first worker (not just the current timer).
        self._reply_views = []
        self._conversation_view = None
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
            on_connection=self.show_connection, on_reply_retire=self.retry_reply_retirement)
        self._bootstrap_readonly_presentation()
        self.show_conversation()

    def _bootstrap_readonly_presentation(self) -> None:
        self._require_creator_thread()
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
        self._require_creator_thread()
        if self._closed or not self._root_alive:
            return False
        try:
            return bool(self.root.winfo_exists())
        except tk.TclError:
            return False

    def _current(self, view, token, generation) -> bool:
        self._require_creator_thread()
        # Identity is checked before any Tk access; stale callbacks cannot even
        # query a destroyed interpreter or disturb a successor's owner.
        return (not self._closed and not self._reply_closing and self._root_alive
                and self._active_view is view and self._active_token is token
                and self._generation == generation and self._root_exists()
                and view.exists())

    def _owner_current(self, view, token, generation) -> bool:
        self._require_creator_thread()
        return self._owner_active and self._current(view, token, generation)

    def _invalidate_owner(self) -> bool:
        self._require_creator_thread()
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
        self._require_creator_thread()
        # A nested callback never starts a second operation. Revoke the outer
        # operation too, so a caught reentrant event cannot restore consent.
        self._operation_token = None
        self._revoke_conversation_view()
        self._invalidate_owner()

    def _require_creator_thread(self) -> None:
        if threading.get_ident() != self._creator_thread:
            raise RuntimeError("WRONG_THREAD")

    def _reply_notice(self, text):
        self._require_creator_thread()
        view, token, generation = self._active_view, self._active_token, self._generation
        serial = self._reply_serial
        if not isinstance(view, ConversationWindow) or not self._root_alive:
            return
        def eligible():
            self._require_creator_thread()
            # Closing permits only the fixed draining/HOLD notice. Do not use
            # _current here, whose deliberate close gate prevents new work.
            current = (self._active_view is view and self._active_token is token
                       and self._generation == generation and self._root_alive)
            return current and self._reply_serial == serial
        try:
            if self._reply_closing:
                view.show_reply_retirement_status(text, eligible)
            else:
                view.show_reply_status(text, eligible)
        except Exception:
            self._reply_owner.poison()

    def _reply_cancel(self):
        self._require_creator_thread()
        self._reply_serial += 1  # also revokes a result already consumed by poll
        self._reply_owner.cancel(self._reply_ticket)

    def _reply_schedule_fault(self):
        self._require_creator_thread()
        self._reply_serial += 1
        self._reply_owner.poison()
        self._reply_notice(REPLY_HOLD)

    def _reply_pure_current(self, binding, serial, *, allow_poison=False):
        self._require_creator_thread()
        now = self._conversation_now()
        return (self._reply_binding is binding and self._reply_context is binding.context
                and self._reply_serial == serial == binding.serial and not self._reply_closing
                and (allow_poison or not self._reply_owner.poisoned) and not self._closed
                and self._root_alive and self._active_view is binding.view
                and self._active_token is binding.token
                and self._generation == binding.generation
                and self._conversation.snapshot is binding.snapshot
                and not binding.snapshot.closed
                and binding.context.root_identity is self._conversation_root
                and binding.context.view_identity is binding.token
                and binding.context.generation == binding.generation
                and binding.context.session_identity is binding.snapshot.session_identity
                and binding.context.epoch == binding.snapshot.epoch
                and now < binding.deadline)

    def _reply_eligible(self, binding, serial, *, allow_poison=False):
        self._require_creator_thread()
        # _current calls Tk and may dispatch nested callbacks. Check all pure
        # identities AGAIN after it returns, immediately before literal display.
        return (self._reply_pure_current(binding, serial, allow_poison=allow_poison)
                and self._current(binding.view, binding.token, binding.generation)
                and self._reply_pure_current(binding, serial, allow_poison=allow_poison))

    def _conversation_reply(self, view, token, generation):
        self._require_creator_thread()
        if (self._reply_busy or self._busy or self._reply_closing
                or self._reply_owner.has_worker or self._reply_owner.poisoned):
            return
        # REENTRANT Tk admission: revoke an outstanding offline review
        # BEFORE reply admission can create a physical worker. This is
        # creator-thread / owner-only and defers Tcl if review is publishing.
        if isinstance(view, ConversationWindow):
            view._cancel_request_review()
        self._reply_busy = True
        try:
            snapshot = self._conversation.snapshot
            admission_serial = self._reply_serial
            if (not self._current(view, token, generation)
                    or self._reply_serial != admission_serial
                    or self._reply_navigation is not None
                    or self._conversation.snapshot is not snapshot):
                return
            candidate = view.entry.get()
            if (not self._current(view, token, generation)
                    or self._reply_serial != admission_serial
                    or self._reply_navigation is not None
                    or self._conversation.snapshot is not snapshot):
                return
            context = ReplyContext(self._conversation_root, token, generation,
                                   snapshot.session_identity, snapshot.epoch)
            if not self._reply_owner.bind_context(context):
                return
            self._reply_context = context
            self._reply_serial += 1
            serial = self._reply_serial
            now = self._conversation_now()
            binding = _ReplyBinding(view, token, generation, context, snapshot,
                                    now + DEADLINE_MS, serial)
            self._reply_binding = binding
            if not self._reply_eligible(binding, serial):
                return
            # Publish the lifetime anchor BEFORE Thread.start, including its
            # raise-after-effect path. The worker captures none of this graph.
            self._reply_graph = (self.root, self, self.workspace, view)
            _REPLY_LIFETIMES[id(self)] = self
            self._reply_ticket = self._reply_owner.start(
                candidate, context=context, now_ms=now, human_requested=True)
            if not self._reply_eligible(binding, serial):
                self._reply_cancel()
            else:
                view.show_reply_status(REPLY_WAITING,
                    lambda: self._reply_eligible(binding, serial))
            if self._reply_owner.has_worker and not self._reply_owner.poisoned:
                if not self.workspace.start_reply_poll(self._reply_poll, self._reply_schedule_fault):
                    self._reply_schedule_fault()
        except ReplyRefused:
            self._reply_notice(ERROR_TEXT)
        except Exception:
            self._reply_schedule_fault()
        finally:
            self._reply_busy = False
            self._reply_flush_invalidation()
            if not self._reply_owner.has_worker:
                self._reply_finish_deferred()
            self._reply_release_anchor()

    def _conversation_cancel_reply(self, view, token, generation):
        self._require_creator_thread()
        if (not self._closed and self._root_alive and self._active_view is view
                and self._active_token is token and self._generation == generation):
            self._reply_cancel()
            if self._reply_busy:
                self._reply_queue_invalidation(view, token, generation)
                return  # revoke the outer publication; never recurse into Tcl
            previous_busy = self._busy
            self._busy = self._reply_busy = True
            try:
                if not view.invalidate_reply_preview():
                    raise RuntimeError("REPLY_PREVIEW_INVALIDATION_FAILED")
                self._reply_notice(REPLY_DRAINING if self._reply_owner.has_worker else REPLY_CANCELLED)
            except Exception:
                self._reply_owner.poison()
                raise RuntimeError("REPLY_PREVIEW_INVALIDATION_FAILED") from None
            finally:
                self._busy = previous_busy
                self._reply_busy = False
                self._reply_flush_invalidation()
                self._reply_finish_deferred()
                self._reply_release_anchor()

    def _reply_queue_invalidation(self, view, token, generation, review=None):
        self._require_creator_thread()
        pending = self._reply_invalidation
        if (review is None and pending is not None and pending[0] is view
                and pending[1] is token and pending[2] == generation):
            review = pending[5]
        self._reply_invalidation = (view, token, generation, self._reply_serial,
                                    view._reply_invalidation_version, review)

    def _reply_flush_invalidation(self):
        self._require_creator_thread()
        if self._reply_busy:
            return
        pending, self._reply_invalidation = self._reply_invalidation, None
        if pending is None:
            return
        view, token, generation, serial, version, review = pending
        # Pure identity checks: a stale callback never clears a successor.
        if (self._closed or not self._root_alive or self._active_view is not view
                or self._active_token is not token or self._generation != generation
                or self._reply_serial != serial):
            return
        previous_busy = self._busy
        self._busy = self._reply_busy = True
        cleared = False
        try:
            # An enclosing Reset/Cancel may already have cleared this preview.
            if (view._reply_invalidation_version == version
                    and not view.invalidate_reply_preview()):
                raise RuntimeError("REPLY_PREVIEW_INVALIDATION_FAILED")
            cleared = True
            if review is not None:
                self._cleanup_reset(view, token, generation, review)
                self._reset_status(view, token, generation,
                    "Reset interrupted. Select Review again and confirm.")
        except Exception:
            self._reply_owner.poison()
            raise RuntimeError("REPLY_PREVIEW_INVALIDATION_FAILED") from None
        finally:
            self._busy = previous_busy
            self._reply_busy = False
            # Nested revocations of the same clear are satisfied by its result.
            if cleared:
                self._reply_flush_invalidation()
            else:
                # A failed clear/hide is HOLD, never an automatic retry loop.
                nested = self._reply_invalidation
                if (nested is not None and nested[0] is view
                        and nested[1] is token and nested[2] == generation):
                    self._reply_invalidation = None

    def _before_conversation_destroy(self, view, token, generation):
        self._require_creator_thread()
        if (self._active_view is not view or self._active_token is not token
                or self._generation != generation):
            return True
        previous = self._reply_busy
        worker_free = not self._reply_owner.has_worker
        self._reply_cancel()
        if self._reply_owner.has_worker:
            self._reply_notice(REPLY_DRAINING)
            return False
        # Serialize the last native-disposal seam against reentrant admission.
        previous_save = self._reply_destroy_save
        # The sealed completion cancel seam permits one nested offline Save,
        # but never reply admission or Save inside an earlier publication.
        self._reply_destroy_save = (
            (view, token, generation, self._conversation, self._conversation_view,
             self._conversation_root)
            if (not previous and worker_free and self._active_view is view
                and self._active_token is token and self._generation == generation)
            else None)
        self._reply_busy = True
        try:
            self._completion.cancel()
        finally:
            self._reply_destroy_save = previous_save
            self._reply_busy = previous
            if not previous:
                self._reply_flush_invalidation()
        return True

    def _reply_release_anchor(self):
        self._require_creator_thread()
        if not self._reply_owner.has_worker and not self._reply_busy:
            self._reply_graph = None
            _REPLY_LIFETIMES.pop(id(self), None)
            if (self._reply_binding is not None
                    and self._reply_binding.snapshot is not self._conversation.snapshot):
                # Reset/close discard owner-retained history. A cancelled
                # in-flight snapshot is needed only until physical retirement.
                self._reply_binding = self._reply_context = None

    def _reply_poll(self):
        self._require_creator_thread()
        if self._reply_busy:
            self._reply_schedule_fault()
            return False
        self._reply_busy = True
        binding, serial = self._reply_binding, self._reply_serial
        try:
            result = self._reply_owner.poll(self._reply_ticket,
                context=self._reply_context, now_ms=self._conversation_now())
            # poll consumes the owner ticket and joins BEFORE any UI seam.
            if not self._reply_owner.has_worker:
                self._reply_ticket = None
                failed = result is None
                if binding is not None and self._reply_eligible(binding, serial, allow_poison=failed):
                    binding.view.show_reply_status(ERROR_TEXT if result is None else result.text,
                        lambda: self._reply_eligible(binding, serial, allow_poison=failed))
                elif binding is self._reply_binding:
                    self._reply_notice(REPLY_CANCELLED)
            elif (self._reply_owner.state is ReplyState.DRAINING
                  and binding is not None and serial == binding.serial):
                self._reply_cancel()
                self._reply_notice(REPLY_DRAINING)
        except Exception:
            self._reply_schedule_fault()
        finally:
            self._reply_busy = False
            self._reply_flush_invalidation()
        if not self._reply_owner.has_worker:
            self._reply_finish_deferred()
            self._reply_release_anchor()
            return False
        return not self._reply_owner.poisoned

    def retry_reply_retirement(self):
        self._require_creator_thread()
        # Explicit nonblocking ingress; never guesses handles or starts a timer.
        if self._reply_busy:
            return False
        self._reply_busy = True
        try:
            self._reply_cancel()
            self.workspace.stop_reply_poll()
            retired = self._reply_owner.retire(now_ms=self._conversation_now())
        finally:
            self._reply_busy = False
            self._reply_flush_invalidation()
        if retired:
            self._reply_ticket = None
            self._reply_finish_deferred()
            self._reply_release_anchor()
        else:
            self._reply_notice(REPLY_HOLD)
        return retired

    def _reply_finish_deferred(self):
        self._require_creator_thread()
        if self._reply_owner.has_worker:
            return
        if self._reply_closing:
            if self._closed:
                # An externally destroyed root has no remaining Tcl ingress.
                self._reply_owner.destroy()
                self._reply_views.clear()
            else:
                self.close()
            return
        intent, self._reply_navigation = self._reply_navigation, None
        if intent is not None:
            view, token, generation, page = intent
            if (self._active_view is view and self._active_token is token
                    and self._generation == generation and not self._closed):
                self._show(page)

    def _revoke_conversation_view(self, *, clear_ui=True) -> None:
        self._require_creator_thread()
        if clear_ui:
            self._completion.cancel()
        ui, token, generation = self._active_view, self._active_token, self._generation
        review = ui._reset_review if isinstance(ui, ConversationWindow) else None
        view, self._conversation_view = self._conversation_view, None
        if view is not None:
            self._conversation.revoke_view(self._conversation_root, view)
        if clear_ui and review is not None:
            self._cleanup_reset(ui, token, generation, review)

    def _retire_view(self) -> None:
        self._require_creator_thread()
        self._revoke_conversation_view()
        view = self._active_view
        self._active_view = self._active_token = None
        self._operation_token = None
        self._generation += 1
        self._invalidate_owner()
        if view is not None and self._root_exists():
            view.dispose()

    def _view_destroyed(self, view, token, generation) -> None:
        self._require_creator_thread()
        # Destroy handlers perform only Python-side revocation, never Tk calls.
        if (self._active_view is view and self._active_token is token
                and self._generation == generation):
            self._reply_cancel()
            if self._reply_owner.has_worker:
                self._reply_owner.poison()
                self.workspace.reply_poll_destroyed()
            self._reply_navigation = None
            self._completion.pane_destroyed()
            self._revoke_conversation_view(clear_ui=False)
            self._active_view = self._active_token = None
            self._operation_token = None
            self._generation += 1
            self._invalidate_owner()

    def _root_destroyed(self, event) -> None:
        self._require_creator_thread()
        if event.widget is self.root:
            self._reply_serial += 1
            self._reply_closing = True
            self._reply_navigation = None
            self._reply_owner.request_close()
            self.workspace.reply_poll_destroyed(root=True)
            self._completion.destroyed()
            self._conversation.close(self._conversation_root)
            self._conversation_view = None
            self._root_alive = False
            self._closed = True
            self._active_view = self._active_token = None
            self._operation_token = None
            self._generation += 1
            self._invalidate_owner()

    def close(self) -> None:
        self._require_creator_thread()
        if self._closed and not self._reply_owner.has_worker:
            return
        # Block admission and revoke delivery BEFORE any UI/Tcl seam.
        self._reply_closing = True
        self._reply_navigation = None
        self._reply_serial += 1
        self._reply_owner.request_close()
        self._reply_notice(REPLY_DRAINING if self._reply_owner.has_worker else REPLY_CANCELLED)
        self._completion.cancel()
        if self._reply_owner.has_worker or self._reply_busy:
            return  # preserve graph and native view until actual join/retirement
        self.workspace.stop_reply_poll()
        self._reply_owner.destroy()
        was_alive = self._root_exists()
        self._completion.cancel()
        self._completion.destroyed()
        self._conversation.close(self._conversation_root)
        self._conversation_view = None
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
        self._reply_views.clear()
        self._reply_release_anchor()

    def show_conversation(self) -> None:
        self._require_creator_thread()
        self._show(_Page.CONVERSATION)

    def show_settings(self) -> None:
        self._require_creator_thread()
        self._show(_Page.SETTINGS)

    def show_connection(self) -> None:
        self._require_creator_thread()
        self._show(_Page.CONNECTION)

    def _show(self, page: _Page) -> None:
        self._require_creator_thread()
        origin_view, origin_token, origin_generation = (
            self._active_view, self._active_token, self._generation)
        if self._reply_closing or self._closed or not self._root_alive:
            return
        if self._reply_owner.has_worker or self._reply_busy:
            self._reply_navigation = (origin_view, origin_token, origin_generation, page)
            self._reply_cancel()
            self._reply_notice(REPLY_DRAINING)
            return
        if not self._root_exists():
            return
        # A reentrant liveness query must not apply A's navigation to B.
        if (self._active_view is not origin_view or self._active_token is not origin_token
                or self._generation != origin_generation):
            return
        if self._reply_owner.has_worker or self._reply_busy:
            self._reply_navigation = (self._active_view, self._active_token,
                                      self._generation, page)
            self._reply_cancel()
            self._reply_notice(REPLY_DRAINING)
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
                    self.workspace.content,
                    assistant_name=self._published_document.assistant.display_name,
                    user_name=self._published_document.user.display_name or "You",
                    on_send=lambda: self._conversation_send(view, token, generation),
                    on_cancel_simulation=lambda: self._conversation_cancel_simulation(
                        view, token, generation),
                    on_reply=lambda: self._conversation_reply(view, token, generation),
                    on_cancel_reply=lambda: self._conversation_cancel_reply(view, token, generation),
                    on_before_destroy=lambda: self._before_conversation_destroy(
                        view, token, generation),
                    on_request_snapshot=lambda: self._request_review_snapshot(
                        view, token, generation),
                    on_reset=lambda operation: self._conversation_review(
                        view, token, generation, operation),
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
            self._reply_views.append(view)
            self._active_view, self._active_token = view, token
            if page is _Page.CONVERSATION:
                self._conversation_view = self._conversation.activate_view(
                    self._conversation_root, object())
            view.pack(fill="both", expand=True)
            if page is _Page.CONVERSATION and self._current(view, token, generation):
                view.render(self._conversation.snapshot)
            if page is _Page.SETTINGS:
                self._load_settings(view, token, generation)
            if self._current(view, token, generation):
                view.focus_initial()
        finally:
            self._busy = False
            if self._root_exists():
                self.workspace.set_busy(False)

    def _request_review_snapshot(self, view, token, generation):
        self._require_creator_thread()
        # No I/O; only current immutable session data when the worker is idle.
        conversation = self._conversation
        snapshot = conversation.snapshot
        conversation_view, conversation_root = self._conversation_view, self._conversation_root
        tk_root = self.root

        def eligible():
            # Python only: repeat AFTER _current's potentially reentrant Tcl.
            return (not self._busy and not self._reply_busy and not self._reply_closing
                    and not self._reply_owner.has_worker and self._reply_ticket is None
                    and not self._closed and self._root_alive
                    and self._active_view is view and self._active_token is token
                    and self._generation == generation
                    and conversation_view is not None
                    and self._conversation_view is conversation_view
                    and self._conversation_root is conversation_root and self.root is tk_root
                    and self._conversation is conversation
                    and conversation.snapshot is snapshot and not snapshot.closed)
        if (not eligible() or not self._current(view, token, generation)
                or not eligible()):
            return None
        return snapshot

    def _conversation_current(self, view, token, generation, authority) -> bool:
        self._require_creator_thread()
        return (authority is not None and self._conversation_view is authority
                and self._current(view, token, generation))

    def _reset_status(self, view, token, generation, text) -> None:
        self._require_creator_thread()
        if self._current(view, token, generation):
            try:
                view.show_status(text)
            except (tk.TclError, RuntimeError):
                # Status is best effort after authority has already been revoked.
                # Never retry a commit or claim a successful display.
                pass

    def _cleanup_reset(self, view, token, generation, review) -> bool:
        self._require_creator_thread()
        if review is None:
            return True
        # The sealed owner only dismisses this exact instance, never successor B.
        self._conversation.dismiss_reset_review(self._conversation_root, review)
        if self._current(view, token, generation):
            try:
                view.clear_reset(review)
            except Exception:
                self._reset_status(view, token, generation,
                    "Reset controls unavailable. Reopen Conversation. No AI request or action was performed.")
                return False
        return True

    def _conversation_send(self, view, token, generation) -> None:
        self._require_creator_thread()
        destroy_save = self._reply_destroy_save
        safe_destroy_save = (
            self._reply_busy and destroy_save is not None
            and destroy_save[0] is view and destroy_save[1] is token
            and destroy_save[2] == generation
            and destroy_save[3] is self._conversation
            and destroy_save[4] is self._conversation_view
            and destroy_save[5] is self._conversation_root
            and self._conversation_view is not None
            and self._active_view is view and self._active_token is token
            and self._generation == generation and not self._closed
            and self._root_alive and not self._reply_closing
            and not self._reply_owner.has_worker)
        if self._reply_busy and not safe_destroy_save:
            # A publication may have passed its final eligibility check. Never
            # commit a successor or recurse into Tcl before that effect unwinds.
            if (not self._closed and self._root_alive and self._active_view is view
                    and self._active_token is token and self._generation == generation):
                self._reply_cancel()
                self._reply_queue_invalidation(view, token, generation)
            return
        if safe_destroy_save:
            self._reply_destroy_save = None  # one use, only in this cancel seam
        if not self._current(view, token, generation):
            return
        if self._busy:
            self._interrupt_operation()
            return
        authority = self._conversation_view
        if authority is None:
            return
        conversation, root = self._conversation, self._conversation_root
        before = conversation.snapshot
        reply_owner = self._reply_owner
        self._busy = True
        ticket = None
        completion_attempted = False
        prior = view._reset_review
        current = lambda: self._conversation_current(view, token, generation, authority)
        try:
            candidate = view.entry.get()
            if not current():
                return
            ticket = conversation.issue_submission(root, authority, candidate)
            if not current():
                return
            conversation.claim_submission(root, authority, ticket)
            self._reply_cancel()
            serial = self._reply_serial
            # A valid claimed Save must clear/hide A BEFORE committing B. A
            # double fault leaves A authoritative and poisons reply admission.
            # Invalid input never reaches this invalidation boundary.
            self._reply_queue_invalidation(view, token, generation)
            if safe_destroy_save:
                # _busy now independently blocks nested reply admission. Let
                # the normal invalidator own _reply_busy during its Tk effect.
                self._reply_busy = False
            try:
                self._reply_flush_invalidation()
            finally:
                if safe_destroy_save:
                    self._reply_busy = True
            # current() itself can reenter Tk. Recheck exact pure identities
            # after it returns, with no further UI seam before owner commit.
            if (not current() or self._conversation is not conversation
                    or self._conversation_root is not root
                    or self._reply_owner is not reply_owner
                    or self._conversation_view is not authority
                    or self._active_view is not view or self._active_token is not token
                    or self._generation != generation or self._closed
                    or not self._root_alive or self._reply_closing
                    or conversation.snapshot is not before
                    or self._reply_serial != serial
                    or self._reply_navigation is not None):
                return
            result = conversation.commit_submission(root, authority, ticket)
            if self._reply_binding is not None:
                self._reply_notice(REPLY_DRAINING if self._reply_owner.has_worker else REPLY_CANCELLED)
            self._completion.cancel()
            self._reply_release_anchor()
            # Only an accepted commit invalidates the pending review. Rejected
            # text/capacity leaves transcript and review untouched.
            if not current():
                return
            if prior is not None:
                cleaned = self._cleanup_reset(view, token, generation, prior)
            else:
                # No prior review means no authority to clear a review that
                # may have appeared during a reentrant display/owner seam.
                view.clear_reset(object())
                cleaned = True
            if not current() or not cleaned:
                return
            view.entry.delete(0, "end")
            if current():
                view.render(result.snapshot)
            if current():
                # Preserve the synchronous offline-save display boundary and
                # its historical fault tests before requesting any simulation.
                view.show_status("Saved in this session only. No AI request or action was performed.")
                if not current():
                    return
                snapshot = result.snapshot
                def completion_current():
                    self._require_creator_thread()
                    return current() and self._conversation.snapshot is snapshot
                completion_attempted = True
                admitted = self._completion.start(
                    result, pane=token, generation=generation,
                    read_snapshot=lambda: self._conversation.snapshot,
                    current=completion_current,
                    render=lambda text, eligible: view.show_simulation_status(
                        text, lambda: completion_current() and eligible()))
                if completion_current() and self._completion.is_pending_for(snapshot):
                    view.show_simulation_status(WAITING,
                        lambda: completion_current() and self._completion.is_pending_for(snapshot))
                elif completion_current() and not admitted:
                    view.show_simulation_status(UNAVAILABLE, completion_current)
        except SessionRefused as error:
            if current():
                self._reset_status(view, token, generation, error.code.value)
        except Exception:
            if completion_attempted:
                self._completion.publication_failed()
            if current():
                self._reset_status(view, token, generation,
                    "Display unavailable. No AI request or action was performed. Reopen Conversation.")
        finally:
            if ticket is not None:
                conversation.revoke_submission(root, ticket)
            self._busy = False

    def _conversation_cancel_simulation(self, view, token, generation) -> None:
        self._require_creator_thread()
        if not self._current(view, token, generation):
            return
        snapshot = self._conversation.snapshot
        self._completion.cancel()
        def eligible():
            return (self._current(view, token, generation)
                    and self._conversation.snapshot is snapshot
                    and not self._completion.is_pending_for(snapshot))
        if eligible():
            try:
                # Recheck the captured cancellation after the view-current seam;
                # a nested Send may already own the successor status and timer.
                view.show_simulation_status(CANCELLED, eligible)
            except (tk.TclError, RuntimeError):
                # A cancellation cannot silently leave a stale WAITING status.
                # Fail closed only for A when it is still current; a reentrant
                # successor or destroyed root must retain its own authority.
                if eligible():
                    self._completion.publication_failed()
                raise RuntimeError("CANCEL_STATUS_PUBLICATION_FAILED") from None

    def _conversation_now(self) -> int:
        self._require_creator_thread()
        return time.monotonic_ns() // 1_000_000

    def _conversation_review(self, view, token, generation, operation) -> None:
        self._require_creator_thread()
        if not self._current(view, token, generation):
            return
        if self._busy:
            self._interrupt_operation()
            return
        authority = self._conversation_view
        if authority is None:
            return
        self._busy = True
        review = None
        prior = view._reset_review
        current = lambda: self._conversation_current(view, token, generation, authority)
        try:
            if not self._cleanup_reset(view, token, generation, prior) or not current():
                return
            # A reentrant cleanup may have published a successor. Do not replace it.
            if view._reset_review is not None:
                return
            review = self._conversation.begin_reset_review(
                self._conversation_root, authority, operation, now_ms=self._conversation_now())
            if not current():
                self._cleanup_reset(view, token, generation, review)
                return
            view.show_reset(
                review,
                lambda: self._conversation_reset(view, token, generation, authority, review, True),
                lambda: self._conversation_reset(view, token, generation, authority, review, False))
            # There is deliberately no Tk expiry callback. Only the owner may
            # decide at Confirm whether the exact 30-second deadline has passed.
        except Exception:
            self._cleanup_reset(view, token, generation, review if review is not None else prior)
            if current():
                self._reset_status(view, token, generation,
                    "Reset expired or unavailable. Select Review again.")
        finally:
            self._busy = False

    def _conversation_reset(self, view, token, generation, authority, review, confirm) -> None:
        self._require_creator_thread()
        current = lambda: self._conversation_current(view, token, generation, authority)
        if not current():
            return
        if view._reset_review is not review:
            return
        if self._reply_busy:
            # Never spend a confirmation inside an unfinished publication (or
            # another Reset). Revoke now, clear after it unwinds, and require
            # a fresh human review rather than replaying this confirmation.
            self._reply_cancel()
            self._conversation.dismiss_reset_review(self._conversation_root, review)
            self._reply_queue_invalidation(view, token, generation, review)
            return
        if self._busy:
            self._interrupt_operation()
            return
        self._busy = True
        previous_reply_busy = self._reply_busy
        self._reply_busy = True
        try:
            if confirm:
                # Revoke and clear any newer local draft before reset can
                # commit. Reset-control cleanup can fail and skip render().
                # A retained NO_SEND receipt must never outlive its session.
                if not view._cancel_draft():
                    return
                before = self._conversation.snapshot
                self._reply_cancel()
                serial = self._reply_serial
                # Clear/hide the old preview BEFORE the authoritative commit.
                # A status notice alone is best effort and cannot establish this.
                try:
                    if not view.invalidate_reply_preview():
                        raise RuntimeError("REPLY_PREVIEW_INVALIDATION_FAILED")
                except Exception:
                    self._reply_owner.poison()
                    raise RuntimeError("REPLY_PREVIEW_INVALIDATION_FAILED") from None
                now = self._conversation_now()
                if (not current() or self._conversation_view is not authority
                        or self._conversation.snapshot is not before
                        or self._reply_serial != serial):
                    return
                snapshot = self._conversation.confirm_reset(
                    self._conversation_root, authority, review, review.operation,
                    now_ms=now)
                if self._reply_binding is not None:
                    self._reply_notice(REPLY_DRAINING if self._reply_owner.has_worker else REPLY_CANCELLED)
                self._completion.cancel()
                self._reply_release_anchor()
                cleaned = self._cleanup_reset(view, token, generation, review)
                if current() and cleaned:
                    view.render(snapshot)
                if current() and cleaned:
                    view.show_status("Session history cleared locally. No AI request or action was performed.")
            else:
                self._cleanup_reset(view, token, generation, review)
        except SessionRefused:
            self._cleanup_reset(view, token, generation, review)
            if current() and view._reset_review is None:
                self._reset_status(view, token, generation,
                    "Reset expired or unavailable. Select Review again.")
        except Exception:
            self._cleanup_reset(view, token, generation, review)
            if current() and view._reset_review is None:
                self._reset_status(view, token, generation,
                    "Display unavailable. Reopen Conversation to inspect session history.")
        finally:
            self._busy = False
            self._reply_busy = previous_reply_busy
            if not self._reply_busy:
                self._reply_flush_invalidation()
                self._reply_finish_deferred()
                self._reply_release_anchor()

    def _load_settings(self, view, token, generation) -> None:
        self._require_creator_thread()
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
        self._require_creator_thread()
        if self._current(view, token, generation):
            self.show_conversation()

    def _changed(self, view, token, generation) -> None:
        self._require_creator_thread()
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
        self._require_creator_thread()
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
        self._require_creator_thread()
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
    """Explicit launch; main-loop owner retains Tk through physical retirement."""
    root = tk.Tk()
    application = None
    try:
        application = OfflineWorkspaceApplication(root)
        root.mainloop()
    finally:
        if application is not None:
            # No Tk callback sleeps or blocking worker join. Each explicit
            # creator-thread probe is bounded and nonblocking. If retirement
            # stays uncertain, this process remains in shutdown HOLD with a
            # strong root/application anchor; it never claims clean shutdown.
            try:
                application.close()
            finally:
                while application._reply_owner.has_worker:
                    application.retry_reply_retirement()
                    if application._reply_owner.has_worker:
                        time.sleep(0.05)
                application.close()
        else:
            try:
                root.destroy()
            except tk.TclError:
                pass
