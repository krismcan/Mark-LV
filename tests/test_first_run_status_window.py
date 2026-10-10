"""Phase 8.22: fake Tk widgets, explicit human refresh only."""
import ast
import inspect
import unittest
from unittest.mock import Mock,patch

from nayeon.brain.connection_reconciliation import ConnectionObservation,ConnectionObservationStatus
from nayeon.brain.first_run_refresh import FirstRunReadOnlyController
from nayeon.desktop_alpha import first_run_status_window as m


class FakeWidget:
    def __init__(self,*args,**kwargs):
        self.props=kwargs
        self.calls=[]
    def pack(self,*a,**k):
        self.calls.append(("pack",a,k))
    def configure(self,**k):
        self.props.update(k)
        self.calls.append(("configure",k))


class FirstRunStatusWindowTests(unittest.TestCase):
    def create(self,observe):
        root=Mock()
        created=[]
        def widget(*a,**kw):
            obj=FakeWidget(*a,**kw)
            created.append(obj)
            return obj
        with patch.object(m.tk,"Label",side_effect=widget),patch.object(m.tk,"Button",side_effect=widget):
            ui=m.FirstRunStatusWindow(root,controller=FirstRunReadOnlyController(observe=observe))
        return ui,root,created

    def test_no_observation_or_mutation_at_construction(self):
        called=[]
        ui,root,widgets=self.create(lambda:called.append(1))
        self.assertEqual(called,[])
        self.assertEqual(root.title.call_args.args,("Nayeon | First-run connection review",))
        self.assertEqual(ui._status.props["text"],"Not observed")
        self.assertEqual(ui._refresh.props["text"],"Refresh status")
        self.assertEqual(sum(1 for x in widgets if x.props.get("command")),1)

    def test_refresh_observes_once_and_no_secret_is_displayed(self):
        calls=[]
        ui,_,_=self.create(lambda:(calls.append(1),ConnectionObservation(
             ConnectionObservationStatus.SETUP_REQUIRED))[1])
        ui.refresh_from_button()
        self.assertEqual(calls,[1])
        self.assertIn("needs setup",ui._status.props["text"])
        self.assertIn("Suggested",ui._details.props["text"])
        self.assertNotIn("api_key",str(ui._details.props))
        self.assertEqual(ui._refresh.props["state"],"normal")

    def test_unsupported_or_unknown_never_claims_connected(self):
        for state in (ConnectionObservationStatus.UNKNOWN,
                      ConnectionObservationStatus.UNSUPPORTED_CONFIGURATION):
            with self.subTest(state=state):
                ui,_,_=self.create(lambda:ConnectionObservation(state))
                ui.refresh_from_button()
                self.assertIn("No credential operation",ui._details.props["text"])
                self.assertNotIn("connected",ui._status.props["text"])

    def test_errors_are_fixed_and_refresh_button_recovers(self):
        ui,_,_=self.create(lambda:(_ for _ in ()).throw(RuntimeError("private-marker")))
        ui.refresh_from_button()
        self.assertEqual(ui._status.props["text"],"Status unavailable")
        self.assertNotIn("private-marker",str(ui._details.props))
        self.assertEqual(ui._refresh.props["state"],"normal")

    def test_controller_type_is_exact(self):
        with self.assertRaises(TypeError):
            m.FirstRunStatusWindow(Mock(),controller=None)

    def test_scope_has_no_credential_mutation_or_startup(self):
        tree=ast.parse(inspect.getsource(m))
        imports={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
        self.assertEqual(imports,{"nayeon.brain.first_run_refresh"})
        self.assertFalse(any(isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)
                             for x in tree.body))
        calls={x.func.id if isinstance(x.func,ast.Name) else x.func.attr
               for x in ast.walk(tree) if isinstance(x,ast.Call)
               and isinstance(x.func,(ast.Name,ast.Attribute))}
        for bad in ("put","get","delete","reveal","test_stored","connect","replace",
                    "approve","Popen","save","startfile"):
            self.assertNotIn(bad,calls)
