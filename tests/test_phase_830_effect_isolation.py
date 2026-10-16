"""Phase 8.30 explicit-launch effect isolation, in a separate host process.

The child patches the native profile resolver to a test-owned LocalAppData
directory before composing the workspace. No real profile path is consulted.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest


_CHILD = r'''
import importlib.abc
import os
import socket
import subprocess
import sys
from unittest import mock

import tkinter as tk
from tests.test_phase_830_application import Phase830ProductionAdmissionTests

fixture = Phase830ProductionAdmissionTests(
    methodName="test_construction_and_missing_load_create_nothing")
fixture.setUp()
original_tk = tk.Tk
roots = []
hits = []
blocked = (
    "openai", "anthropic", "nayeon.brain", "nayeon.secrets",
    "nayeon.capabilities", "nayeon.policy",
    "nayeon.services.applications", "nayeon.services.application_observation",
)

class DenyImport(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == prefix or fullname.startswith(prefix + ".")
               for prefix in blocked):
            hits.append("import:" + fullname)
            raise AssertionError("BLOCKED_SIDE_EFFECT_IMPORT")
        return None

def denied(route, *args, **kwargs):
    hits.append(route)
    raise AssertionError("BLOCKED_SIDE_EFFECT")

def factory():
    root = original_tk()
    root.withdraw()
    roots.append(root)
    def bounded_mainloop():
        shell = root.winfo_children()[0]
        assert shell.winfo_name() != "notepad"
        shell.navigation_buttons[2].invoke()
        assert shell.content.winfo_children()[0].winfo_name() == "connection_view"
        shell.navigation_buttons[0].invoke()
        shell.navigation_buttons[1].invoke()
        settings = shell.content.winfo_children()[0]
        assert settings.winfo_name() == "presentation_view"
        assert not fixture.app_dir.exists()
        settings.assistant_name.set("Isolated Synthetic")
        settings.review_button.invoke()
        assert not fixture.app_dir.exists()
        settings.save_button.invoke()
        assert fixture.profile_leaf.exists()
        assert shell.name_label.cget("text") == "Isolated Synthetic"
        shell.navigation_buttons[0].invoke()
        root.destroy()
    root.mainloop = bounded_mainloop
    return root

try:
    finder = DenyImport()
    sys.meta_path.insert(0, finder)
    with (mock.patch.object(tk, "Tk", factory),
          mock.patch.object(subprocess, "Popen",
                            side_effect=lambda *a, **kw: denied("process", *a, **kw)),
          mock.patch.object(socket, "socket",
                            side_effect=lambda *a, **kw: denied("socket", *a, **kw)),
          mock.patch.object(socket, "create_connection",
                            side_effect=lambda *a, **kw: denied("network", *a, **kw))):
        from nayeon.desktop_alpha import window
        window.main()
        # A deliberately swallowed blocked call MUST still fail isolation.
        negative = os.environ.get("NAYEON_830_TRIPWIRE_NEGATIVE", "")
        if negative:
            try:
                if negative == "process":
                    subprocess.Popen(["synthetic-never-launched"])
                elif negative == "socket":
                    socket.socket()
                elif negative == "network":
                    socket.create_connection(("127.0.0.1", 1))
                elif negative == "import":
                    import importlib
                    importlib.import_module("nayeon.secrets.__synthetic_probe__")
                else:
                    raise AssertionError("Invalid negative-control selector")
            except AssertionError:
                pass
    assert not hits, "TRIPWIRE_HIT:" + ",".join(hits)
    assert len(roots) == 1
    try:
        still_exists = roots[0].winfo_exists()
    except tk.TclError:
        still_exists = False
    assert not still_exists
    assert all(module not in sys.modules for module in blocked)
    print("ISOLATED_OFFLINE_EFFECT_TRIPWIRE_PASS")
finally:
    fixture.doCleanups()
'''


@unittest.skipUnless(os.name == "nt", "Native Windows isolation required")
class Phase830EffectIsolationTests(unittest.TestCase):
    def test_default_entrypoint_has_no_backend_or_action_effect_route(self):
        result = subprocess.run(
            [sys.executable, "-c", _CHILD], capture_output=True, text=True,
            timeout=25,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ISOLATED_OFFLINE_EFFECT_TRIPWIRE_PASS", result.stdout)

    def test_swallowed_effect_attempts_are_recorded_and_refused(self):
        for kind in ("process", "socket", "network", "import"):
            with self.subTest(kind=kind):
                result = subprocess.run(
                    [sys.executable, "-c", _CHILD],
                    capture_output=True, text=True, timeout=25,
                    env={**os.environ,
                         "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
                         "NAYEON_830_TRIPWIRE_NEGATIVE": kind},
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("TRIPWIRE_HIT", result.stderr)
                self.assertNotIn("ISOLATED_OFFLINE_EFFECT_TRIPWIRE_PASS",
                                 result.stdout)


if __name__ == "__main__":
    unittest.main()
