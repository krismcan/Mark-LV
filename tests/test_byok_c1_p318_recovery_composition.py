"""P318 pure composition fixtures; no OS, credential, service or provider calls."""
import unittest
from dataclasses import FrozenInstanceError, replace
from unittest.mock import Mock, patch

from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)
from nayeon.brain.connection_recovery_advice import (
    ConnectionRecoveryStep, advise_connection_recovery,
)
from nayeon.brain.first_run_summary import (
    FirstRunSummary, summarize_first_run, summarize_pending_custody_first_run,
)
from nayeon.brain.onboarding_status_view import present_onboarding_status
from nayeon.brain.pending_credential_policy import (
    PendingCredentialAction, PendingCredentialDecision, PendingCredentialState,
    assess_pending_credential_action,
)
from nayeon.brain.pending_custody_status_view import present_pending_custody_advice
from nayeon.brain import first_run_refresh as refresh
from nayeon.desktop_alpha import first_run_status_window as panel
from tests.test_first_run_status_window import FakeWidget


def synthetic_view(observation, state, action):
    legacy = present_onboarding_status(
        observation, advise_connection_recovery(observation))
    return present_pending_custody_advice(
        legacy, assess_pending_credential_action(state, action))


class RecoveryCompositionTests(unittest.TestCase):
    def test_all_63_status_claim_action_combinations_require_review(self):
        count = 0
        for status in ConnectionObservationStatus:
            observation = ConnectionObservation(status)
            for state in PendingCredentialState:
                for action in PendingCredentialAction:
                    with self.subTest(status=status, claim=state, action=action):
                        count += 1
                        view = synthetic_view(observation, state, action)
                        result = summarize_pending_custody_first_run(observation, view)
                        self.assertIs(type(result), FirstRunSummary)
                        self.assertIs(result.state, view.legacy_status)
                        self.assertIs(result.recovery_step,
                                      ConnectionRecoveryStep.REVIEW_UNKNOWN_STATE)
                        self.assertEqual(result.suggested_operations, ())
                        self.assertIs(result.requires_reobservation, True)
                        self.assertIs(result.grants_execution_authority, False)
                        for field in ("authorizes_effect", "confirms_persistence",
                                      "confirms_validation", "confirms_provider_connection",
                                      "clears_recovery"):
                            self.assertIs(getattr(view, field), False)
        self.assertEqual(count, 63)

    def test_unverified_view_suppresses_previously_suggested_operations(self):
        # This reproduces the missing composition: legacy first-run advice
        # suggests operations despite a separately displayed recovery hold.
        for status in (ConnectionObservationStatus.SETUP_REQUIRED,
                       ConnectionObservationStatus.CREDENTIAL_REQUIRED,
                       ConnectionObservationStatus.UNCONFIGURED_CREDENTIAL_PRESENT,
                       ConnectionObservationStatus.VALIDATION_REQUIRED):
            observation = ConnectionObservation(status)
            self.assertTrue(summarize_first_run(observation).suggested_operations)
            for state in PendingCredentialState:
                with self.subTest(status=status, claim=state):
                    view = synthetic_view(observation, state,
                                          PendingCredentialAction.SAVE_PENDING)
                    self.assertEqual(summarize_pending_custody_first_run(
                        observation, view).suggested_operations, ())
            self.assertTrue(summarize_first_run(observation).suggested_operations)

    def test_missing_spoofed_or_cross_status_view_never_falls_back(self):
        observation = ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED)
        for invalid in (None, "recovered", object(), PendingCredentialState.ABSENT):
            with self.subTest(kind=type(invalid)), self.assertRaises(TypeError):
                summarize_pending_custody_first_run(observation, invalid)
        with self.assertRaises(TypeError):
            summarize_pending_custody_first_run(observation)
        for status in ConnectionObservationStatus:
            if status is observation.status:
                continue
            stale = synthetic_view(ConnectionObservation(status),
                                   PendingCredentialState.ABSENT,
                                   PendingCredentialAction.SAVE_PENDING)
            with self.subTest(other=status), self.assertRaises(ValueError):
                summarize_pending_custody_first_run(observation, stale)
        view = synthetic_view(observation, PendingCredentialState.RECOVERY_REQUIRED,
                              PendingCredentialAction.DELETE_PENDING)
        for invalid in (None, "setup_required", object(), observation.status):
            with self.subTest(kind=type(invalid)), self.assertRaises(TypeError):
                summarize_pending_custody_first_run(invalid, view)

    def test_repeated_claims_do_not_progress_to_recovery_or_retry(self):
        observation = ConnectionObservation(ConnectionObservationStatus.UNKNOWN)
        for state in PendingCredentialState:
            view = synthetic_view(observation, state,
                                  PendingCredentialAction.REPLACE_PENDING)
            first = summarize_pending_custody_first_run(observation, view)
            for _ in range(3):
                self.assertEqual(summarize_pending_custody_first_run(
                    observation, view), first)
            with self.assertRaises(FrozenInstanceError):
                first.grants_execution_authority = True
            with self.assertRaises(ValueError):
                replace(first, grants_execution_authority=True)
            for field in ("authorizes_effect", "confirms_persistence",
                          "confirms_validation", "confirms_provider_connection",
                          "clears_recovery"):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    replace(view, **{field: True})
            with self.assertRaises(ValueError):
                replace(view, advisory_decision=PendingCredentialDecision.NEEDS_REVIEW
                        if view.advisory_decision is not PendingCredentialDecision.NEEDS_REVIEW
                        else PendingCredentialDecision.DENY)


def synthetic_pair(status=ConnectionObservationStatus.SETUP_REQUIRED,
                   state=PendingCredentialState.RECOVERY_REQUIRED):
    observation = ConnectionObservation(status)
    return observation, synthetic_view(
        observation, state, PendingCredentialAction.SAVE_PENDING)


class PairedSyntheticPanelTests(unittest.TestCase):
    """Real controller and panel methods, entirely inert widgets and claims."""

    def create(self, observe):
        controller = refresh.FirstRunReadOnlyController(
            observe_paired_synthetic=observe)
        root = Mock()
        widgets = []

        def widget(*args, **kwargs):
            result = FakeWidget(*args, **kwargs)
            widgets.append(result)
            return result

        with patch.object(panel.tk, "Label", side_effect=widget), patch.object(
                panel.tk, "Button", side_effect=widget):
            window = panel.FirstRunStatusWindow(root, controller=controller)
        return controller, window, root, widgets

    def assert_unavailable(self, result):
        self.assertIs(result.status, refresh.FirstRunRefreshStatus.UNAVAILABLE)
        self.assertIsNone(result.summary)
        self.assertTrue(result.requires_reobservation)

    def assert_panel_unavailable(self, window):
        self.assertEqual(window._status.props["text"], "Status unavailable")
        self.assertIn("Manual unknown-state review", window._details.props["text"])
        self.assertIn("Recovery is unverified", window._details.props["text"])
        self.assertNotIn("Suggested next steps", window._details.props["text"])
        self.assertEqual(window._refresh.props["state"], "normal")

    def test_construction_is_inert_and_modes_are_explicit_and_exclusive(self):
        observe = Mock(return_value=synthetic_pair())
        controller, window, root, widgets = self.create(observe)
        observe.assert_not_called()
        self.assertTrue(controller.uses_paired_synthetic_observation)
        self.assertEqual(window._status.props["text"], "Not observed")
        self.assertEqual(sum(bool(w.props.get("command")) for w in widgets), 1)
        self.assertIs(next(w.props["command"] for w in widgets
                           if w.props.get("command")).__self__, window)
        root.after.assert_not_called()
        root.mainloop.assert_not_called()
        for args in ({}, {"observe_paired_synthetic": False},
                     {"observe": observe, "observe_paired_synthetic": observe}):
            with self.subTest(args=tuple(args)), self.assertRaises(TypeError):
                refresh.FirstRunReadOnlyController(**args)
        observe.assert_not_called()

    def test_all_paired_claims_reach_panel_as_manual_unverified_review(self):
        for status in ConnectionObservationStatus:
            for state in PendingCredentialState:
                with self.subTest(status=status, claim=state):
                    observe = Mock(return_value=synthetic_pair(status, state))
                    controller, window, root, widgets = self.create(observe)
                    result = controller.refresh()
                    self.assertIs(result.status, refresh.FirstRunRefreshStatus.OBSERVED)
                    self.assertIs(result.summary.recovery_step,
                                  ConnectionRecoveryStep.REVIEW_UNKNOWN_STATE)
                    self.assertEqual(result.summary.suggested_operations, ())
                    self.assertFalse(result.summary.grants_execution_authority)
                    window.refresh_from_button()
                    self.assertEqual(observe.call_count, 2)  # one per explicit refresh
                    self.assertEqual(window._status.props["text"],
                                     "Manual unknown-state review required")
                    self.assertIn("Recovery is unverified", window._details.props["text"])
                    self.assertIn("No credential operation is suggested",
                                  window._details.props["text"])
                    self.assertNotIn("Observed state", window._status.props["text"])
                    self.assertNotIn("Suggested next steps", window._details.props["text"])
                    self.assertEqual(window._refresh.props["state"], "normal")
                    root.after.assert_not_called()

    def test_invalid_pair_replaces_prior_panel_data_without_fallback_or_retry(self):
        good = synthetic_pair()
        mismatched = (good[0], synthetic_pair(ConnectionObservationStatus.UNKNOWN)[1])
        forged_observation = object.__new__(ConnectionObservation)
        object.__setattr__(forged_observation, "status", "setup_required")
        forged_view = replace(good[1])
        object.__setattr__(forged_view, "clears_recovery", True)
        missing_view_fields = object.__new__(type(good[1]))

        class TupleSubclass(tuple):
            pass

        invalid = (None, good[0], good[1], (), (good[0],), good + (None,),
                   list(good), TupleSubclass(good), (None, good[1]), (good[0], None),
                   (object(), good[1]), (good[0], object()), mismatched,
                   (forged_observation, good[1]), (good[0], forged_view),
                   (good[0], missing_view_fields))
        for wrong in invalid:
            with self.subTest(kind=type(wrong).__name__):
                observe = Mock(side_effect=[good, wrong])
                controller, window, _, _ = self.create(observe)
                window.refresh_from_button()
                self.assertIn("Manual", window._status.props["text"])
                with patch.object(refresh, "summarize_first_run") as legacy:
                    window.refresh_from_button()
                    legacy.assert_not_called()
                self.assertEqual(observe.call_count, 2)
                self.assert_panel_unavailable(window)
                self.assertNotIn("setup", window._details.props["text"])
                # Independent invalid result also carries no previous summary.
                self.assert_unavailable(refresh.FirstRunReadOnlyController(
                    observe_paired_synthetic=lambda: wrong).refresh())

    def test_exception_discards_previous_result_and_never_retries(self):
        observe = Mock(side_effect=[synthetic_pair(), RuntimeError("private-marker")])
        controller, window, _, _ = self.create(observe)
        window.refresh_from_button()
        window.refresh_from_button()
        self.assertEqual(observe.call_count, 2)
        self.assert_panel_unavailable(window)
        self.assertNotIn("private-marker", str(window._details.props))
        failure = Mock(side_effect=RuntimeError("private-marker"))
        self.assert_unavailable(refresh.FirstRunReadOnlyController(
            observe_paired_synthetic=failure).refresh())
        failure.assert_called_once_with()

    def test_reentrant_refresh_invalidates_outer_result_then_explicit_refresh_recovers(self):
        nested = []
        calls = []

        def observe():
            calls.append(1)
            if len(calls) == 1:
                nested.append(controller.refresh())
            return synthetic_pair()

        controller, window, _, _ = self.create(observe)
        window.refresh_from_button()
        self.assertEqual(calls, [1])
        self.assert_unavailable(nested[0])
        self.assert_panel_unavailable(window)
        # No automatic second observation; a new explicit click is required.
        window.refresh_from_button()
        self.assertEqual(calls, [1, 1])
        self.assertIn("Manual unknown-state review", window._status.props["text"])
        self.assertIn("Recovery is unverified", window._details.props["text"])

    def test_repeated_stale_claim_never_progresses_or_exposes_an_action(self):
        pair = synthetic_pair(ConnectionObservationStatus.VALIDATION_REQUIRED,
                              PendingCredentialState.ABSENT)
        observe = Mock(return_value=pair)
        controller, window, root, widgets = self.create(observe)
        # Same synthetic claim is still unverified, never freshness evidence.
        with patch("nayeon.brain.connection_reconciliation.observe_connection",
                   side_effect=AssertionError("live observation forbidden")) as live:
            for _ in range(3):
                window.refresh_from_button()
                self.assertIn("Manual unknown-state review", window._status.props["text"])
                self.assertIn("Recovery is unverified", window._details.props["text"])
            live.assert_not_called()
        self.assertEqual(observe.call_count, 3)
        self.assertEqual([w.props["text"] for w in widgets if w.props.get("command")],
                         ["Refresh status"])
        self.assertFalse(any(w.props.get("textvariable") for w in widgets))
        root.after.assert_not_called()
        root.mainloop.assert_not_called()
