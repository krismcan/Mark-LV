"""Phase 6.23 candidate freeze: deterministic inspection, no live native effects.

These guards deliberately pin the uncommitted closure candidate to Phase 6.22.
A future explicitly approved architecture phase may intentionally update them;
generic or semantic clicking must not silently extend Computer Control v1.
"""
import ast
import importlib
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = "797ed334f4256d2e05de6605d7ceb9f4bd96a57e"
TAG = "nayeon-v1-fresh-uia-clickability-execution-gate-01"
CLOSURE = "59d6b341ffe67b86e7f0555e50be074ecfd31f4a"
CLOSURE_TAG = "nayeon-v1-bounded-computer-control-v1-closure-01"
PROTECTED_FILES = (
    "nayeon/agent/executor.py", "nayeon/agent/pointer_binding.py",
    "nayeon/capabilities/observe_foreground_window.py",
    "nayeon/capabilities/observe_pointer.py", "nayeon/capabilities/focus_window.py",
    "nayeon/capabilities/type_text.py", "nayeon/services/computer_control.py",
    "nayeon/services/window_focus.py", "nayeon/services/windows_focus.py",
    "nayeon/services/keyboard_text.py", "nayeon/services/windows_keyboard.py",
    "nayeon/services/pointer_observation.py", "nayeon/services/windows_pointer.py",
    "nayeon/services/target_validation.py", "nayeon/services/pointer_hit_validation.py",
    "nayeon/services/pointer_coordinate_contract.py", "nayeon/services/pointer_coordinates.py",
    "nayeon/services/pointer_effect.py", "nayeon/services/dpi_execution_context.py",
    "nayeon/services/ui_element_observation.py",
    "nayeon/services/scoped_ui_element_observation.py",
)
EXECUTOR = "nayeon/agent/executor.py"
BINDING = "nayeon/agent/pointer_binding.py"
EFFECT = "nayeon/services/pointer_effect.py"
KEYBOARD = "nayeon/services/windows_keyboard.py"
PUBLIC = {
    "observe_foreground_window": "ObserveForegroundWindowCapability",
    "observe_pointer": "ObservePointerCapability",
    "focus_window": "FocusWindowCapability",
    "type_text": "TypeTextCapability",
}
PRIVATE_MODULES = {
    "nayeon.agent.pointer_binding", "nayeon.services.pointer_effect",
    "nayeon.services.pointer_coordinates",
    "nayeon.services.scoped_ui_element_observation",
    "nayeon.services.windows_scoped_ui_element",
}
DEFERRED_WORDS = {"click", "drag", "drop", "scroll", "wheel"}
AUTHORITY = {
    "_PointerInvocation", "_pointer_invocation", "_PointerEffectService",
    "_PointerEffectNative", "_PointerOperation", "_PointerAction",
    "_ProposedPoint", "_PointerCoordinateService", "_execute_effect",
    "_insert", "SendInput", "SetCursorPos", "mouse_event",
}


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def baseline(path):
    return git("show", CHECKPOINT + ":" + path).decode("utf-8").replace("\r\n", "\n")


def symbols(tree):
    """Code identifiers only: comments, descriptions and docstrings are excluded."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name
        elif isinstance(node, ast.alias):
            yield node.name
            if node.asname:
                yield node.asname


def words(value):
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return set(re.findall(r"[a-z]+", value.lower()))


def imports(path, tree):
    """Resolve ordinary absolute/relative imports, including from-package forms."""
    package = path[:-3].replace("/", ".").split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = package[:len(package) - node.level + 1] if node.level else []
            module = ".".join(prefix + ([node.module] if node.module else []))
            yield module
            yield from (module + "." + alias.name for alias in node.names)


class ComputerControlV1FreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trees = {
            path.relative_to(ROOT).as_posix(): ast.parse(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "nayeon").rglob("*.py"))
        }

    def test_phase6_closure_tags_and_computer_control_files_remain_frozen(self):
        # HEAD may advance after Phase 6.23. Freeze the Computer Control trust
        # surface and historical milestones, not unrelated future subsystems.
        self.assertEqual(git("branch", "--show-current").decode().strip(), "nayeon-v1")
        self.assertEqual(git("rev-parse", TAG + "^{commit}").decode().strip(), CHECKPOINT)
        self.assertEqual(git("rev-parse", CLOSURE_TAG + "^{commit}").decode().strip(), CLOSURE)
        for path in PROTECTED_FILES:
            with self.subTest(path=path):
                current = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
                protected = git("show", CHECKPOINT + ":" + path).replace(b"\r\n", b"\n")
                self.assertEqual(current, protected)


    def test_every_capability_module_excludes_pointer_authority_and_deferred_surface(self):
        for path, tree in self.trees.items():
            if not path.startswith("nayeon/capabilities/"):
                continue
            with self.subTest(path=path):
                self.assertFalse(words(Path(path).stem) & DEFERRED_WORDS)
                self.assertFalse(set(symbols(tree)) & AUTHORITY)
                for symbol in symbols(tree):
                    self.assertFalse(words(symbol) & DEFERRED_WORDS, symbol)
                for module in imports(path, tree):
                    self.assertFalse(any(module == private or module.startswith(private + ".")
                                         for private in PRIVATE_MODULES), module)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    # Catch reflective authority access without rejecting prose.
                    if isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "__import__"}:
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                self.assertNotIn(arg.value, AUTHORITY)
                                self.assertFalse(any(private in arg.value for private in PRIVATE_MODULES))
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                self.assertFalse(any(private in arg.value for private in PRIVATE_MODULES))
                    # Inspect routing metadata, not harmless descriptions/docstrings.
                    if isinstance(node.func, ast.Name) and node.func.id == "Capability":
                        for keyword in node.keywords:
                            if keyword.arg in {"name", "service", "metadata", "intent_patterns"}:
                                for value in ast.walk(keyword.value):
                                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                                        self.assertFalse(words(value.value) & DEFERRED_WORDS, value.value)

    def test_private_method_has_no_production_reference_or_public_wrapper(self):
        definitions = []
        invocation_classes = []
        invocation_users = set()
        for path, tree in self.trees.items():
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_pointer_invocation":
                    definitions.append((path, node))
                if isinstance(node, ast.ClassDef) and node.name == "_PointerInvocation":
                    invocation_classes.append(path)
                if isinstance(node, ast.Name) and node.id == "_PointerInvocation":
                    invocation_users.add(path)
                if isinstance(node, ast.alias) and node.name == "_PointerInvocation":
                    invocation_users.add(path)
                if isinstance(node, ast.Name):
                    self.assertNotEqual(node.id, "_pointer_invocation", path)
                if isinstance(node, ast.Attribute):
                    self.assertNotEqual(node.attr, "_pointer_invocation", path)
                if isinstance(node, ast.Constant) and node.value == "_pointer_invocation":
                    self.fail("Reflective production invocation reference: " + path)
        self.assertEqual([path for path, _ in definitions], [EXECUTOR])
        method = definitions[0][1]
        executor = next(node for node in self.trees[EXECUTOR].body
                        if isinstance(node, ast.ClassDef) and node.name == "ActionExecutor")
        self.assertIn(method, executor.body)
        self.assertEqual([ast.unparse(item) for item in method.decorator_list], ["contextmanager"])
        self.assertEqual(invocation_classes, [BINDING])
        self.assertEqual(invocation_users, {EXECUTOR})
        self.assertEqual(source(EXECUTOR), baseline(EXECUTOR))
        self.assertIn("finally:\n            invocation.close()", ast.get_source_segment(source(EXECUTOR), method))
        binding = self.trees[BINDING]
        exports = next(node for node in binding.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets))
        self.assertEqual(ast.literal_eval(exports.value), ())

    def test_lexical_exit_does_not_retain_invocation_or_authority(self):
        # Reuse reviewed fake target/hit services: no Windows/native fallback.
        from tests.test_pointer_binding import PointerBindingTests
        for exceptional in (False, True):
            with self.subTest(exceptional=exceptional):
                fixture = PointerBindingTests()
                fixture.setUp()
                before = dict(vars(fixture.executor))
                class LexicalExit(Exception):
                    pass
                try:
                    with fixture.invocation() as invocation:
                        fixture.prepare(invocation)
                        if exceptional:
                            raise LexicalExit()
                except LexicalExit:
                    pass
                fixture.assert_cleared(invocation)
                self.assertEqual(vars(fixture.executor), before)
                self.assertFalse(any(value is invocation for value in vars(fixture.executor).values()))

    def test_pointer_effect_import_insertion_and_native_boundaries(self):
        importers, inserters, senders, native_senders = set(), set(), set(), set()
        for path, tree in self.trees.items():
            if "nayeon.services.pointer_effect" in set(imports(path, tree)):
                importers.add(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "_insert":
                        inserters.add(path)
                    if node.func.attr == "_send_input":
                        senders.add(path)
                if isinstance(node, ast.Attribute) and node.attr in {"SendInput", "mouse_event", "SetCursorPos"}:
                    native_senders.add(path)
                if isinstance(node, ast.Constant) and node.value in {"SendInput", "mouse_event", "SetCursorPos"}:
                    native_senders.add(path)
        self.assertEqual(importers, {EXECUTOR, BINDING})
        self.assertEqual(inserters, {BINDING})
        self.assertEqual(senders, {EFFECT})
        # Keyboard SendInput is separate authority, never a pointer bypass.
        self.assertEqual(native_senders, {EFFECT, KEYBOARD})
        self.assertEqual(source(EFFECT), baseline(EFFECT))
        self.assertEqual(source(KEYBOARD), baseline(KEYBOARD))
        keyboard = self.trees[KEYBOARD]
        events = next(node for node in keyboard.body if isinstance(node, ast.FunctionDef)
                      and node.name == "_unicode_events")
        event_types = [node.value.value for node in ast.walk(events)
                       if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                       and any(isinstance(target, ast.Attribute) and target.attr == "type" for target in node.targets)]
        self.assertEqual(event_types, [1])  # INPUT_KEYBOARD, not INPUT_MOUSE.

    def test_approved_point_and_execution_only_clickability_structure(self):
        text = source(BINDING)
        self.assertEqual(text, baseline(BINDING))
        tree = self.trees[BINDING]
        operation = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                         and node.name == "_PointerOperation")
        self.assertEqual([node.target.id for node in operation.body if isinstance(node, ast.AnnAssign)],
                         ["target", "action", "point", "runtime_id"])
        invocation = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                          and node.name == "_PointerInvocation")
        prepare = next(node for node in invocation.body if isinstance(node, ast.FunctionDef)
                       and node.name == "prepare")
        self.assertNotIn("clickable", set(symbols(prepare)))
        reads = [node for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "clickable"]
        self.assertEqual(len(reads), 1)
        self.assertIn("if evidence.clickable is not True:\n                    return unknown", text)
        normalizers = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Attribute) and node.func.attr == "normalize"]
        self.assertEqual(len(normalizers), 1)
        self.assertEqual([ast.unparse(arg) for arg in normalizers[0].args], ["operation.point"])
        self.assertNotIn("GetClickablePoint", set(symbols(tree)))
        self.assertNotIn("GetClickablePoint", text)

    def test_final_normalization_through_insertion_gap_is_checkpoint_identical(self):
        text, protected = source(BINDING), baseline(BINDING)
        start = "                mapped = self._coordinate_service.normalize(operation.point)"
        end = "            else:\n                completed = eligibility"
        for content in (text, protected):
            self.assertEqual(content.count(start), 1)
            self.assertEqual(content.count(end), 1)
        self.assertEqual(text[text.index(start):text.index(end)],
                         protected[protected.index(start):protected.index(end)])
        # Also pin insertion's transitive local/native path: new API reads cannot
        # hide in a helper while leaving the lexical block unchanged.
        for path in (EFFECT, "nayeon/services/pointer_coordinates.py"):
            self.assertEqual(source(path), baseline(path))

    def test_existing_public_computer_control_classes_and_metadata(self):
        # Inject inert services; inspect metadata without preparation/execution.
        for name, class_name in PUBLIC.items():
            with self.subTest(capability=name):
                module = importlib.import_module("nayeon.capabilities." + name)
                implementation = getattr(module, class_name)(service=object())
                metadata = implementation.capability
                self.assertEqual(metadata.name, name)
                self.assertEqual(metadata.service, "computer_control")
                self.assertFalse(metadata.requires_llm)
                self.assertFalse(metadata.reversible)
                self.assertEqual(metadata.requires_confirmation, name in {"focus_window", "type_text"})
        # This assertion scopes only Computer Control; other product capabilities
        # (files, applications, etc.) remain allowed.
        computer_control_names = set()
        for path, tree in self.trees.items():
            if not path.startswith("nayeon/capabilities/"):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Capability":
                    keywords = {item.arg: item.value for item in node.keywords}
                    service = keywords.get("service")
                    if isinstance(service, ast.Constant) and service.value == "computer_control":
                        computer_control_names.add(ast.literal_eval(keywords["name"]))
        self.assertEqual(computer_control_names, set(PUBLIC))


if __name__ == "__main__":
    unittest.main()
