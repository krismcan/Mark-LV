"""Phase 8 C1 policy-only tests. No live/native secret or provider operations."""
import ast
import inspect
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from nayeon.brain import pending_credential_policy as p


class PendingCredentialPolicyTests(unittest.TestCase):
    def test_exhaustive_nonsecret_matrix(self):
        states = p.PendingCredentialState
        actions = p.PendingCredentialAction
        decisions = p.PendingCredentialDecision
        expected = {
            (states.ABSENT, actions.SAVE_PENDING): decisions.NEEDS_REVIEW,
            (states.ABSENT, actions.REPLACE_PENDING): decisions.DENY,
            (states.ABSENT, actions.DELETE_PENDING): decisions.DENY,
            (states.STORED_UNVERIFIED, actions.SAVE_PENDING): decisions.DENY,
            (states.STORED_UNVERIFIED, actions.REPLACE_PENDING): decisions.NEEDS_REVIEW,
            (states.STORED_UNVERIFIED, actions.DELETE_PENDING):
                decisions.NEEDS_DESTRUCTIVE_ACK,
            (states.RECOVERY_REQUIRED, actions.SAVE_PENDING): decisions.RECOVERY_BLOCKED,
            (states.RECOVERY_REQUIRED, actions.REPLACE_PENDING): decisions.RECOVERY_BLOCKED,
            (states.RECOVERY_REQUIRED, actions.DELETE_PENDING): decisions.RECOVERY_BLOCKED,
        }
        self.assertEqual(set(expected), {(s, a) for s in states for a in actions})
        self.assertEqual(p._RULES, expected)
        for (state, action), decision in expected.items():
            with self.subTest(state=state, action=action):
                result = p.assess_pending_credential_action(state, action)
                self.assertIs(type(result), p.PendingCredentialAssessment)
                self.assertIs(result.state, state)
                self.assertIs(result.action, action)
                self.assertIs(result.decision, decision)

    def test_recovery_blocks_every_action_without_a_clear_path(self):
        for action in p.PendingCredentialAction:
            with self.subTest(action=action):
                result = p.assess_pending_credential_action(
                    p.PendingCredentialState.RECOVERY_REQUIRED, action)
                self.assertIs(result.decision,
                              p.PendingCredentialDecision.RECOVERY_BLOCKED)
        self.assertFalse(any(
            member.name in {"READY", "VALID", "CONNECTED", "APPROVED", "EXECUTE",
                            "RECOVERED", "RECOVERY_CLEARED"}
            for enum_type in (p.PendingCredentialState, p.PendingCredentialDecision)
            for member in enum_type))

    def test_invalid_inputs_fail_closed_and_never_coerce(self):
        from enum import Enum
        class ForgedState(Enum):
            ABSENT = "absent"
        class ForgedAction(Enum):
            SAVE_PENDING = "save_pending"
        invalid_states = ("absent", None, True, 0, object(), ForgedState.ABSENT)
        invalid_actions = ("save_pending", None, False, 1, object(),
                           ForgedAction.SAVE_PENDING)
        for state in invalid_states:
            with self.subTest(state_type=type(state).__name__):
                with self.assertRaises(TypeError):
                    p.assess_pending_credential_action(
                        state, p.PendingCredentialAction.SAVE_PENDING)
        for action in invalid_actions:
            with self.subTest(action_type=type(action).__name__):
                with self.assertRaises(TypeError):
                    p.assess_pending_credential_action(
                        p.PendingCredentialState.ABSENT, action)

    def test_assessment_is_immutable_exact_typed_and_nonauthoritative(self):
        result = p.assess_pending_credential_action(
            p.PendingCredentialState.STORED_UNVERIFIED,
            p.PendingCredentialAction.DELETE_PENDING)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            result.decision = p.PendingCredentialDecision.DENY
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            result.token = "arbitrary"
        for field, value in (
            ("state", "absent"),
            ("action", "delete_pending"),
            ("decision", "needs_destructive_ack"),
        ):
            values = dict(state=p.PendingCredentialState.ABSENT,
                          action=p.PendingCredentialAction.DELETE_PENDING,
                          decision=p.PendingCredentialDecision.DENY)
            values[field] = value
            with self.subTest(field=field), self.assertRaises(TypeError):
                p.PendingCredentialAssessment(**values)
        self.assertEqual(len(result.__dataclass_fields__), 3)
        self.assertNotIn("token", repr(result))
        self.assertFalse(hasattr(result, "approve"))
        self.assertFalse(hasattr(result, "execute"))
        self.assertFalse(hasattr(result, "__dict__"))

    def test_source_has_no_effects_no_project_imports_no_secrets(self):
        path = Path(inspect.getfile(p))
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [node for node in ast.walk(tree)
                   if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual({node.module for node in imports
                          if isinstance(node, ast.ImportFrom)},
                         {"dataclasses", "enum"})
        self.assertEqual([n for n in imports if isinstance(n, ast.Import)], [])
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        forbidden = {"open", "eval", "exec", "print", "SecretValue",
                     "SecretBackend", "WinDLL", "WindowsCredentialBackend",
                     "BoundSecretResolver", "socket", "requests",
                     "subprocess", "getenv", "environ", "credential", "key"}
        self.assertFalse(names & forbidden)
        self.assertNotIn("openai.api_key", source)
        self.assertNotIn("OPENAI_API_KEY", source)
        self.assertNotIn("openai.pending_unverified", source)
        self.assertEqual([n.name for n in tree.body if isinstance(n, ast.FunctionDef)],
                         ["assess_pending_credential_action"])


if __name__ == "__main__":
    unittest.main()
