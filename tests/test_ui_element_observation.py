"""Phase 6.14 deterministic fake-only tests."""
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, replace
import json, pickle, threading, unittest
from pathlib import Path
from unittest.mock import Mock
from nayeon.services import ui_element_observation as m
from nayeon.services.pointer_hit_validation import _ProposedPoint as Point
from nayeon.verification.contract import VerificationStatus as V

class Int(int): pass

class FakeNative:
    def __init__(self, control_type=50000, enabled=True, fail=None):
        self.ct, self.enabled, self.fail, self.calls = control_type, enabled, fail, []
    def _c(self,n,v=None):
        self.calls.append(n)
        if self.fail==n: raise OSError("secret")
        return v
    def initialize(self): return self._c("initialize")
    def activate(self): return self._c("activate")
    def element_from_point(self,x,y):
        self.calls.append(("element_from_point",x,y))
        if self.fail=="element_from_point": raise OSError("secret")
    def control_type(self): return self._c("control_type",self.ct)
    def is_enabled(self): return self._c("is_enabled",self.enabled)
    def release_element(self): return self._c("release_element")
    def release_automation(self): return self._c("release_automation")
    def uninitialize(self): return self._c("uninitialize")

class Worker:
    def __init__(self, before=False, after=False): self.before,self.after=before,after
    def run(self,task):
        if self.before: raise RuntimeError("secret")
        task()
        if self.after: raise RuntimeError("secret")

class Tests(unittest.TestCase):
    def obs(self,n=None,w=None,p=(17,-23),platform="win32"):
        n=n or FakeNative(); w=w or Worker(); nf=Mock(return_value=n); wf=Mock(return_value=w)
        r=m._UIElementObservationService(native_factory=nf,worker_factory=wf,platform=platform).observe(Point(*p))
        return r,n,nf,wf
    def test_verified_order_and_cardinality(self):
        r,n,nf,wf=self.obs()
        self.assertIs(r.status,V.VERIFIED); self.assertEqual((r.evidence.point.x,r.evidence.point.y),(17,-23))
        self.assertEqual((r.evidence.control_type,r.evidence.enabled),(50000,True))
        self.assertEqual(n.calls,["initialize","activate",("element_from_point",17,-23),"control_type","is_enabled","release_element","release_automation","uninitialize"])
        nf.assert_called_once_with(); wf.assert_called_once_with()
    def test_every_native_failure_indeterminate_cleanup_once(self):
        stages=("initialize","activate","element_from_point","control_type","is_enabled","release_element","release_automation","uninitialize")
        for stage in stages:
            n=FakeNative(fail=stage); r=self.obs(n=n)[0]
            self.assertIs(r.status,V.INDETERMINATE); self.assertIsNone(r.evidence)
            names=[x[0] if isinstance(x,tuple) else x for x in n.calls]
            self.assertEqual(names.count(stage),1)
            for c in ("release_element","release_automation","uninitialize"): self.assertEqual(names.count(c),1)
            self.assertNotIn("secret",repr(r))
    def test_never_not_verified(self):
        for fail in (None,"initialize","activate","element_from_point","control_type","is_enabled","release_element","release_automation","uninitialize"):
            self.assertIsNot(self.obs(n=FakeNative(fail=fail))[0].status,V.NOT_VERIFIED)
    def test_worker_failure(self):
        for w in (Worker(before=True),Worker(after=True)):
            self.assertIs(self.obs(w=w)[0].status,V.INDETERMINATE)
    def test_bad_input_before_factories(self):
        class Sub(Point): pass
        nf,wf=Mock(),Mock(); s=m._UIElementObservationService(native_factory=nf,worker_factory=wf,platform="win32")
        for p in (None,(0,0),True,Sub(0,0)): self.assertIs(s.observe(p).status,V.INDETERMINATE)
        nf.assert_not_called(); wf.assert_not_called()
    def test_tampered_input(self):
        for field in ("x","y"):
            for bad in (True,Int(0),1.0,None,2**31,-(2**31)-1):
                p=Point(0,0); object.__setattr__(p,field,bad); nf,wf=Mock(),Mock()
                r=m._UIElementObservationService(native_factory=nf,worker_factory=wf,platform="win32").observe(p)
                self.assertIs(r.status,V.INDETERMINATE); nf.assert_not_called(); wf.assert_not_called()
    def test_contract_values(self):
        for ct in (50000,50020,50040): self.assertIs(self.obs(n=FakeNative(control_type=ct))[0].status,V.VERIFIED)
        for ct in (49999,50041,True,Int(50000),50000.0,None):
            self.assertIs(self.obs(n=FakeNative(control_type=ct))[0].status,V.INDETERMINATE)
        for e in (True,False): self.assertIs(self.obs(n=FakeNative(enabled=e))[0].status,V.VERIFIED)
        for e in (0,1,Int(1),1.0,None): self.assertIs(self.obs(n=FakeNative(enabled=e))[0].status,V.INDETERMINATE)
    def test_platform_fail_closed(self):
        for p in ("linux","darwin","",True,None):
            nf,wf=Mock(),Mock(); r=m._UIElementObservationService(native_factory=nf,worker_factory=wf,platform=p).observe(Point(0,0))
            self.assertIs(r.status,V.INDETERMINATE); nf.assert_not_called(); wf.assert_not_called()
    def test_invariants(self):
        e=m._UIElementEvidence(Point(0,0),50000,True)
        for args in (("verified",e),(V.VERIFIED,None),(V.NOT_VERIFIED,None),(V.INDETERMINATE,e)):
            with self.assertRaises((TypeError,ValueError)): m._UIElementResult(*args)
        with self.assertRaises((TypeError,ValueError)): replace(e,control_type=50041)
        with self.assertRaises((TypeError,ValueError)): replace(e,enabled=1)
    def test_subclasses(self):
        class E(m._UIElementEvidence): pass
        class R(m._UIElementResult): pass
        with self.assertRaises(TypeError): E(Point(0,0),50000,True)
        with self.assertRaises(TypeError): R()
    def test_privacy(self):
        r=self.obs()[0]
        for v in (r,r.evidence,r.evidence.point,m._UIElementResult()):
            self.assertFalse(hasattr(v,"__dict__")); self.assertEqual(repr(v),type(v).__name__+"(<private>)")
            for op in (copy,deepcopy,pickle.dumps,json.dumps):
                with self.assertRaises(TypeError): op(v)
        with self.assertRaises(FrozenInstanceError): r.evidence.enabled=False
    def test_source_guards(self):
        source=Path(m.__file__).read_text()
        self.assertEqual(m.__all__,())
        for x in ("pywinauto","pyautogui","SendInput","SetCursorPos","screenshot","OCR","InvokePattern","SetValue","ValuePattern","TreeWalker","FindFirst","FindAll","AuditService","UndoService","StructuredCapability","IntentDispatcher"):
            self.assertNotIn(x,source)
        self.assertEqual({x for x in vars(m._UIElementObservationService) if not x.startswith("_")},{"observe"})

if __name__=="__main__": unittest.main()
