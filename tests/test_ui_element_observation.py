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


# Phase 6.19: fake COM vtable and OleAut32 only; no native activation.
class RuntimeIdTests(unittest.TestCase):
    def facade(self, *, values=(-2147483648, -1, 0, 2147483647), lower=-7,
               upper=None, dim=1, vt=3, hr=0, null=False, fail=None, raises=False):
        import ctypes as C
        from unittest.mock import patch
        dlls = [Mock(), Mock()]
        with patch.object(m.ctypes, 'WinDLL', side_effect=dlls):
            native = m._UIANative()
        automation = dlls[1]
        calls = []
        def record(name, result=0):
            calls.append(name)
            if fail == name:
                if raises: raise RuntimeError('PRIVATE_NATIVE_DETAIL')
                return -1 if name != 'dim' else 0
            return result
        def get(this, out):
            calls.append('get')
            C.cast(out, C.POINTER(C.c_void_p))[0] = None if null else 9876
            return hr
        callback = C.WINFUNCTYPE(C.c_int32, C.c_void_p, C.POINTER(C.c_void_p))(get)
        table = (C.c_void_p * 29)()
        table[4] = C.cast(callback, C.c_void_p).value
        element = C.pointer(C.cast(table, C.POINTER(C.c_void_p)))
        native._element = C.cast(element, C.c_void_p)
        native._initialized = True
        def output(name, out, value):
            status = record(name)
            if status == 0: out._obj.value = value
            return status
        automation.SafeArrayGetDim.side_effect = lambda array: record('dim', dim)
        automation.SafeArrayGetVartype.side_effect = lambda array, out: output('vt', out, vt)
        automation.SafeArrayGetLBound.side_effect = lambda array, dimension, out: output('lower', out, lower)
        automation.SafeArrayGetUBound.side_effect = lambda array, dimension, out: output(
            'upper', out, lower + len(values) - 1 if upper is None else upper)
        def item(array, index, out):
            return output('item', out, values[index._obj.value - lower])
        automation.SafeArrayGetElement.side_effect = item
        automation.SafeArrayDestroy.side_effect = lambda array: record('destroy')
        return native, automation, calls, (callback, table, element), dlls

    def test_slot_four_once_signed_values_order_cleanup_no_pointer(self):
        import ctypes as C
        from unittest.mock import patch
        native, dll, calls, keep, _ = self.facade()
        with patch.object(m._UIANative, '_method', autospec=True,
                          side_effect=m._UIANative._method) as method:
            result = native.runtime_id()
        method.assert_called_once_with(native, native._element, 4, C.c_int32, C.POINTER(C.c_void_p))
        self.assertIs(type(result), tuple)
        self.assertEqual(result, (-2147483648, -1, 0, 2147483647))
        self.assertTrue(all(type(v) is int for v in result))
        self.assertEqual(calls, ['get', 'dim', 'vt', 'lower', 'upper', 'item', 'item', 'item', 'item', 'destroy'])
        dll.SafeArrayDestroy.assert_called_once_with(9876)
        self.assertFalse(hasattr(native, '_runtime_id'))

    def test_explicit_oleaut_abi(self):
        import ctypes as C
        native, dll, calls, keep, _ = self.facade()
        expected = {
            'SafeArrayGetDim': ([C.c_void_p], C.c_uint32),
            'SafeArrayGetVartype': ([C.c_void_p, C.POINTER(C.c_uint16)], C.c_int32),
            'SafeArrayGetLBound': ([C.c_void_p, C.c_uint32, C.POINTER(C.c_int32)], C.c_int32),
            'SafeArrayGetUBound': ([C.c_void_p, C.c_uint32, C.POINTER(C.c_int32)], C.c_int32),
            'SafeArrayGetElement': ([C.c_void_p, C.POINTER(C.c_int32), C.c_void_p], C.c_int32),
            'SafeArrayDestroy': ([C.c_void_p], C.c_int32),
        }
        for name, (args, result) in expected.items():
            self.assertEqual(getattr(dll, name).argtypes, args)
            self.assertIs(getattr(dll, name).restype, result)
        self.assertEqual(native.MAX_RUNTIME_ID_INTS, 64)
        self.assertEqual(calls, [])

    def test_null_and_hresult_partial_array(self):
        for kwargs in ({'null': True}, {'hr': -1}, {'hr': 1}, {'hr': -1, 'null': True}):
            native, dll, calls, keep, _ = self.facade(**kwargs)
            with self.assertRaisesRegex(OSError, '^Private runtime sample unavailable.$'):
                native.runtime_id()
            self.assertEqual(calls, ['get'] + ([] if kwargs.get('null') else ['destroy']))

    def test_dimensions_vartype_bounds_reject_before_items(self):
        for kwargs in ({'dim': 0}, {'dim': 2}, {'dim': True}, {'dim': Int(1)},
                       {'vt': 2}, {'vt': 0}, {'values': ()}, {'values': tuple(range(65))},
                       {'lower': 7, 'upper': 6}, {'lower': -(2**31), 'upper': 2**31-1},
                       {'lower': 2**31-1, 'upper': 2**31}, {'lower': -(2**31)-1, 'upper': 0}):
            with self.subTest(kwargs=kwargs):
                native, dll, calls, keep, _ = self.facade(**kwargs)
                with self.assertRaises(OSError): native.runtime_id()
                self.assertNotIn('item', calls)
                self.assertEqual(calls.count('destroy'), 1)

    def test_all_safearray_failures_and_exceptions_destroy_once(self):
        for fail in ('dim', 'vt', 'lower', 'upper', 'item', 'destroy'):
            for raises in (False, True):
                native, dll, calls, keep, _ = self.facade(fail=fail, raises=raises)
                with self.assertRaises(OSError) as caught: native.runtime_id()
                self.assertNotIn('PRIVATE_NATIVE_DETAIL', str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)
                self.assertEqual(calls.count('destroy'), 1)
                self.assertEqual(calls.count(fail), 1)

    def test_maximum_length_and_extreme_valid_bounds(self):
        for lower in (-(2**31), 2**31-64):
            native, dll, calls, keep, _ = self.facade(values=tuple(range(64)), lower=lower)
            self.assertEqual(native.runtime_id(), tuple(range(64)))
            self.assertEqual(calls.count('item'), 64)
            self.assertEqual(calls.count('destroy'), 1)

    def test_owner_thread_and_missing_retained_element(self):
        native, dll, calls, keep, _ = self.facade()
        errors = []
        def wrong_thread():
            try: native.runtime_id()
            except OSError as error: errors.append(str(error))
        thread = threading.Thread(target=wrong_thread)
        thread.start(); thread.join()
        self.assertEqual(errors, ['Private runtime sample unavailable.'])
        self.assertEqual(calls, [])
        native._element.value = None
        with self.assertRaises(OSError): native.runtime_id()
        self.assertEqual(calls, [])

    def test_partial_array_on_call_exception_and_late_item_failure(self):
        from unittest.mock import patch
        native, dll, calls, keep, _ = self.facade()
        def partial(this, out):
            out._obj.value = 9876
            raise RuntimeError('PRIVATE_NATIVE_DETAIL')
        with patch.object(m._UIANative, '_method', return_value=partial):
            with self.assertRaises(OSError): native.runtime_id()
        self.assertEqual(calls, ['destroy'])
        native, dll, calls, keep, _ = self.facade()
        original = dll.SafeArrayGetElement.side_effect
        def late(array, index, out):
            if index._obj.value == -5:
                calls.append('item'); return -1
            return original(array, index, out)
        dll.SafeArrayGetElement.side_effect = late
        with self.assertRaises(OSError): native.runtime_id()
        self.assertEqual(calls.count('item'), 3)
        self.assertEqual(calls.count('destroy'), 1)

    def test_phase_6_14_ast_unchanged_except_native_facade(self):
        import ast, subprocess
        root = Path(__file__).resolve().parents[1]
        path = 'nayeon/services/ui_element_observation.py'
        baseline = subprocess.check_output(['git', 'show',
            'f3742615f79da1be2cf34ce9c207b42bd9456245:' + path], cwd=root).decode()
        def without_native(source):
            tree = ast.parse(source)
            tree.body = [node for node in tree.body if not
                (isinstance(node, ast.ClassDef) and node.name == '_UIANative')]
            return ast.dump(tree)
        self.assertEqual(without_native(Path(m.__file__).read_text()), without_native(baseline))


if __name__ == "__main__":
    unittest.main()
