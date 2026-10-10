"""Phase 8.21 explicit read-only refresh orchestration."""
import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

from nayeon.brain import first_run_refresh as m
from nayeon.brain.connection_reconciliation import (
    ConnectionObservation, ConnectionObservationStatus,
)


class FirstRunRefreshTests(unittest.TestCase):
    def test_construction_never_observes(self):
        called=[]
        controller=m.FirstRunReadOnlyController(
            observe=lambda: (called.append(1),ConnectionObservation(
                ConnectionObservationStatus.SETUP_REQUIRED))[1])
        self.assertEqual(called,[])
        outcome=controller.refresh()
        self.assertEqual(called,[1])
        self.assertIs(outcome.status,m.FirstRunRefreshStatus.OBSERVED)
        self.assertTrue(outcome.requires_reobservation)
        self.assertFalse(outcome.summary.grants_execution_authority)

    def test_each_refresh_is_independent(self):
        items=[ConnectionObservation(ConnectionObservationStatus.SETUP_REQUIRED),
               ConnectionObservation(ConnectionObservationStatus.UNKNOWN)]
        controller=m.FirstRunReadOnlyController(observe=lambda: items.pop(0))
        x=controller.refresh();y=controller.refresh()
        self.assertNotEqual(x.summary.state,y.summary.state)
        self.assertIsNone(controller.refresh().summary)

    def test_exception_and_wrong_observation_fail_closed_without_stale_data(self):
        cases=(lambda: None,lambda: "connected",lambda: (_ for _ in ()).throw(
            RuntimeError("synthetic-sensitive")))
        for item in cases:
            with self.subTest(kind=item):
                result=m.FirstRunReadOnlyController(observe=item).refresh()
                self.assertIs(result.status,m.FirstRunRefreshStatus.UNAVAILABLE)
                self.assertIsNone(result.summary)
                self.assertNotIn("synthetic-sensitive",repr(result))

    def test_recursive_observation_blocks_without_recursion_or_retry(self):
        history=[]
        def observe():
            history.append(controller.refresh())
            return ConnectionObservation(ConnectionObservationStatus.CREDENTIAL_REQUIRED)
        controller=m.FirstRunReadOnlyController(observe=observe)
        result=controller.refresh()
        self.assertEqual(len(history),1)
        self.assertIsNone(history[0].summary)
        self.assertIs(result.status,m.FirstRunRefreshStatus.OBSERVED)

    def test_invalid_construction_and_forged_receipts(self):
        with self.assertRaises(TypeError):
            m.FirstRunReadOnlyController(observe=None)
        for wrong in ("observed",None,1):
            with self.assertRaises(TypeError):
                m.FirstRunRefresh(wrong)
        with self.assertRaises(TypeError):
            m.FirstRunRefresh(m.FirstRunRefreshStatus.OBSERVED)
        with self.assertRaises(TypeError):
            m.FirstRunRefresh(m.FirstRunRefreshStatus.UNAVAILABLE,object())
        with self.assertRaises(ValueError):
            m.FirstRunRefresh(m.FirstRunRefreshStatus.UNAVAILABLE,requires_reobservation=False)
        out=m.FirstRunReadOnlyController(observe=lambda:None).refresh()
        with self.assertRaises(FrozenInstanceError):
            out.status=m.FirstRunRefreshStatus.OBSERVED

    def test_no_effectful_primitive_or_import(self):
        imports={x.module for x in ast.walk(ast.parse(inspect.getsource(m)))
                 if isinstance(x,ast.ImportFrom)}
        self.assertEqual(imports,{"collections.abc","dataclasses","enum",
            "nayeon.brain.connection_reconciliation","nayeon.brain.first_run_summary"})
        tree=ast.parse(inspect.getsource(m))
        forbidden={"get","put","delete","save","validate","connect","reveal",
                   "test_stored","test_candidate","approve","request"}
        for call in (x.func for x in ast.walk(tree) if isinstance(x,ast.Call)):
            name=call.id if isinstance(call,ast.Name) else call.attr if isinstance(call,ast.Attribute) else None
            self.assertNotIn(name,forbidden)
