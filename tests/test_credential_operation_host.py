"""Phase 8.18 trusted operations: fake secret backend only."""
import ast
import inspect
import unittest
from dataclasses import FrozenInstanceError

from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.connection_reconciliation import ConnectionObservation, ConnectionObservationStatus as Status
from nayeon.brain.onboarding_operation_advice import OnboardingOperation as Op
from nayeon.brain.onboarding_review_session import OnboardingReviewSession
from nayeon.brain import credential_operation_host as m
from nayeon.secrets.contracts import SecretIdentifier, SecretNotFoundError, SecretValue
from nayeon.secrets.lifecycle import BoundCredentialLifecycle, CredentialValidationStatus as Val


class FakeBackend:
    def __init__(self):
        self.value=None; self.puts=0; self.deletes=0; self.gets=0
    def is_available(self, key):
        assert key == SecretIdentifier("openai.api_key")
        return self.value is not None
    def put(self, key, value):
        assert key == SecretIdentifier("openai.api_key") and type(value) is SecretValue
        self.value=value; self.puts+=1
    def get(self,key):
        self.gets+=1
        if self.value is None:raise SecretNotFoundError("absent")
        return self.value
    def delete(self,key):
        self.deletes+=1
        was=self.value is not None
        self.value=None
        return was


class FakeValidator:
    def __init__(self):self.calls=0
    def validate(self,value):
        self.calls+=1
        return Val.VALID if value.reveal()=="fixture-good" else Val.INVALID


def factory(status=Status.SETUP_REQUIRED):
    b=FakeBackend();v=FakeValidator();state=[status]
    def observe():return ConnectionObservation(state[0])
    onboarding=OpenAICredentialOnboarding(
        BoundCredentialLifecycle(b,SecretIdentifier("openai.api_key"),v))
    host=m.TrustedCredentialOperationHost(
        onboarding=onboarding,observe=observe,
        review=OnboardingReviewSession(clock=lambda:10.0))
    return host,b,v,state


class TrustedCredentialHostTests(unittest.TestCase):
    def test_no_effect_before_explicit_approval_and_consumed_once(self):
        host,b,v,_=factory()
        self.assertTrue(host.request(Op.CONNECT))
        self.assertEqual((b.puts,v.calls,b.gets,b.deletes),(0,0,0,0))
        self.assertFalse(host.request(Op.CONNECT))
        receipt=host.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(receipt.outcome,m.CredentialHostOutcome.SUBMITTED)
        self.assertTrue(receipt.requires_reobservation)
        self.assertFalse(receipt.confirms_durable_storage)
        self.assertEqual((b.puts,v.calls),(1,1))
        self.assertFalse(host.has_pending)
        self.assertIsNone(host.approve(candidate=SecretValue("fixture-good")))
        self.assertEqual(b.puts,1)

    def test_reject_and_missing_candidate_cannot_mutate(self):
        host,b,v,_=factory()
        self.assertTrue(host.request(Op.CONNECT))
        self.assertIs(host.reject().outcome,m.CredentialHostOutcome.BLOCKED)
        self.assertEqual(b.puts,0)
        self.assertTrue(host.request(Op.CONNECT))
        self.assertIs(host.approve().outcome,m.CredentialHostOutcome.BLOCKED)
        self.assertEqual((b.puts,v.calls),(0,0))

    def test_state_change_before_approval_fails_closed(self):
        host,b,v,state=factory()
        self.assertTrue(host.request(Op.CONNECT))
        state[0]=Status.VALIDATION_REQUIRED
        self.assertIs(host.approve(candidate=SecretValue("fixture-good")).outcome,
                      m.CredentialHostOutcome.BLOCKED)
        self.assertEqual((b.puts,v.calls),(0,0))
        self.assertFalse(host.has_pending)

    def test_invalid_candidate_not_saved(self):
        host,b,v,_=factory()
        self.assertTrue(host.request(Op.CONNECT))
        self.assertIs(host.approve(candidate=SecretValue("fixture-bad")).outcome,
                      m.CredentialHostOutcome.INVALID)
        self.assertEqual((b.puts,v.calls),(0,1))

    def test_replace_and_explicit_remove(self):
        host,b,v,_=factory(Status.VALIDATION_REQUIRED)
        old=SecretValue("fixture-existing")
        b.value=old
        self.assertTrue(host.request(Op.REPLACE))
        self.assertIs(host.approve(candidate=SecretValue("fixture-bad")).outcome,
                      m.CredentialHostOutcome.INVALID)
        self.assertIs(b.value,old)
        self.assertTrue(host.request(Op.REPLACE))
        self.assertIs(host.approve(candidate=SecretValue("fixture-good")).outcome,
                      m.CredentialHostOutcome.SUBMITTED)
        self.assertEqual(b.puts,1)
        self.assertTrue(host.request(Op.REMOVE))
        self.assertIs(host.approve().outcome,m.CredentialHostOutcome.SUBMITTED)
        self.assertEqual(b.deletes,1)

    def test_explicit_test_candidate_or_stored_cannot_write(self):
        host,b,v,_=factory()
        self.assertTrue(host.request(Op.TEST_CANDIDATE))
        self.assertIs(host.approve(candidate=SecretValue("fixture-good")).outcome,
                      m.CredentialHostOutcome.SUBMITTED)
        self.assertEqual((b.puts,b.gets),(0,0))
        host2,b2,v2,_=factory(Status.VALIDATION_REQUIRED)
        b2.value=SecretValue("fixture-good")
        self.assertTrue(host2.request(Op.TEST_STORED))
        self.assertIs(host2.approve().outcome,m.CredentialHostOutcome.SUBMITTED)
        self.assertEqual((b2.puts,b2.gets),(0,1))

    def test_unexpected_source_or_operation_refused(self):
        host,b,v,state=factory()
        self.assertFalse(host.request("connect"))
        self.assertFalse(host.request(Op.REVIEW))
        state[0]=Status.UNKNOWN
        self.assertFalse(host.request(Op.CONNECT))
        self.assertFalse(host.has_pending)
        self.assertEqual(b.puts,0)

    def test_backend_failure_redacted(self):
        host,b,v,_=factory()
        self.assertTrue(host.request(Op.CONNECT))
        def bad_put(key,value):raise RuntimeError("fixture-secret-failure")
        b.put=bad_put
        result=host.approve(candidate=SecretValue("fixture-good"))
        self.assertIs(result.outcome,m.CredentialHostOutcome.INDETERMINATE)
        self.assertNotIn("fixture-secret",repr(result))
        self.assertNotIn("fixture-secret",str(result))

    def test_result_never_claims_durable_storage(self):
        data=dict(operation=Op.CONNECT,outcome=m.CredentialHostOutcome.SUBMITTED)
        for change in ({"confirms_durable_storage":True},
                       {"requires_reobservation":False},
                       {"outcome":"submitted"}, {"operation":"connect"}):
            with self.assertRaises((TypeError,ValueError)):
                m.CredentialHostResult(**(data|change))
        result=m.CredentialHostResult(**data)
        with self.assertRaises(FrozenInstanceError):result.outcome=m.CredentialHostOutcome.BLOCKED

    def test_secret_contract_import_cannot_expand_backend_authority(self):
        tree=ast.parse(inspect.getsource(m))
        imports=[n for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        for node in imports:
            if node.module=="nayeon.secrets.contracts":
                self.assertEqual({alias.name for alias in node.names},{"SecretValue"})
            self.assertNotIn(node.module,{"nayeon.secrets.windows_credential",
                                          "nayeon.secrets.resolver",
                                          "nayeon.secrets.store"})
        calls={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id
               for n in ast.walk(tree) if isinstance(n,ast.Call)
               and isinstance(n.func,(ast.Name,ast.Attribute))}
        for blocked in ("reveal","get","put","delete","is_available","save","open"):
            self.assertNotIn(blocked,calls)

    def test_host_has_no_candidate_storage_and_never_exposes_model_route(self):
        host,b,v,_=factory()
        self.assertFalse(hasattr(host,"__dict__"))
        self.assertFalse(hasattr(host,"capability"))
        self.assertFalse(hasattr(host,"map_intent_arguments"))
        self.assertTrue(host.request(Op.CONNECT))
        self.assertNotIn("fixture",repr(host))
        self.assertFalse(hasattr(host._TrustedCredentialOperationHost__review.pending_advice,"candidate"))


if __name__=="__main__":unittest.main()
