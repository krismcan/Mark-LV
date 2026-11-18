"""Read-only P275 source inventory. No product imports or native execution.

This bounded source contract is neither an OS policy nor a general Python
security analyzer. Custody of every inherited source is checked separately
by CI. A hostile same-user caller can load WinCred independently.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = "nayeon/secrets/windows_credential.py"
PARENT = "f388e69d31dbc8f1dc02230597c2b45deb5b1e60"
# Approved existing ctypes owners, NOT a permission to add effects to them.
# CI additionally proves all of these except BACKEND match the parent blob.
CTYPES_OWNERS = frozenset({
    BACKEND, "nayeon/brain/windows_onboarding_mutex.py",
    "nayeon/desktop_alpha/presentation_profile_owner.py",
    *("nayeon/services/" + name + ".py" for name in (
        "application_observation", "dpi_execution_context", "filesystem",
        "pointer_coordinates", "pointer_coordinate_contract", "pointer_effect",
        "pointer_observation", "target_validation", "ui_element_observation",
        "windows_desktop", "windows_focus", "windows_keyboard", "windows_pointer",
    )),
})
DEPENDENCIES = (
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/secrets/lifecycle.py", BACKEND,
)


def require(value: bool, reason: str) -> None:
    if not value:
        raise AssertionError("P275 source HOLD: " + reason)


def expression_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return expression_name(node.value) + "." + node.attr
    return "<computed>"


def statement_contract(method: ast.FunctionDef, expected: str) -> None:
    # Ignore docstrings/comments, retain every executable statement and alias.
    body = list(method.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    require(ast.dump(ast.Module(body=body, type_ignores=[])) ==
            ast.dump(ast.parse(expected)), method.name + " execution contract")


def check_backend(source: str) -> None:
    tree = ast.parse(source)
    # Also reject appended helper functions and monkey-patched native methods.
    # The inherited module has one docstring, three imports, nine assignments,
    # five classes and one loader function. CI binds the exact source bytes.
    require(len(tree.body) == 19, "backend top-level executable additions")
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    require(len(imports) == 3, "backend import count")
    for node in imports:
        require(all(alias.asname is None for alias in node.names), "import alias")
        if isinstance(node, ast.Import):
            require([a.name for a in node.names] == ["ctypes"], "native import")
        else:
            require(node.level == 0 and node.module in {
                "__future__", "nayeon.secrets.contracts"}, "backend dependency")
    forbidden = {
        "string_at", "wstring_at", "contents", "memmove", "memset",
        "from_buffer", "from_buffer_copy", "cast", "getattr", "setattr",
        "__getattribute__", "__dict__", "__import__", "eval", "exec",
        "globals", "locals", "vars", "import_module", "CDLL", "windll",
        "cdll", "LoadLibrary", "GetProcAddress", "CFUNCTYPE", "WINFUNCTYPE",
    }
    for node in ast.walk(tree):
        name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""
        require(name not in forbidden, "native extraction/dynamic alias: " + name)
        require(not name.startswith(("CredWrite", "CredDelete", "CredEnumerate")), "native effect")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            require(not any(word in node.value for word in (
                "CredWrite", "CredDelete", "CredEnumerate")), "native symbol string")
    adapter = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "_Advapi32Adapter")
    methods = {n.name: n for n in adapter.body if isinstance(n, ast.FunctionDef)}
    require(set(methods) == {"__init__", "read", "contains"}, "native method surface")
    require(not adapter.bases and not adapter.decorator_list, "native class indirection")
    require(len(adapter.body) == 4, "native class executable additions")
    for method in methods.values():
        require(not method.decorator_list, "native method decorator")
        for node in ast.walk(method):
            if isinstance(node, ast.Return):
                require(method.name == "contains" and isinstance(node.value, ast.Constant) and
                        type(node.value.value) is bool, "native pointer/non-boolean return")
    statement_contract(methods["read"], "raise SecretStorageError(_FAILURE)")
    statement_contract(methods["contains"], """pointer = _PCREDENTIALW()
try:
    try:
        if not self._dll.CredReadW(target, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == _ERROR_NOT_FOUND and not pointer:
                return False
            raise SecretStorageError(_FAILURE)
        if not pointer:
            raise SecretStorageError(_FAILURE)
        return True
    finally:
        if pointer:
            self._dll.CredFree(pointer)
except Exception:
    raise SecretStorageError(_FAILURE) from None
""")
    statement_contract(methods["__init__"], """try:
    self._dll = _load_advapi32()
    self._dll.CredReadW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(_PCREDENTIALW)]
    self._dll.CredReadW.restype = ctypes.c_int32
    self._dll.CredFree.argtypes = [ctypes.c_void_p]
    self._dll.CredFree.restype = None
except Exception:
    raise SecretStorageError(_FAILURE) from None
""")
    loader = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_load_advapi32")
    require(not loader.decorator_list, "loader decorator")
    statement_contract(loader, 'return ctypes.WinDLL("Advapi32.dll", use_last_error=True)')
    # No API may be resolved into a dynamic/local alias anywhere in the module.
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    loader_nodes = set(ast.walk(loader))
    setup_nodes = set(ast.walk(methods["__init__"]))
    ctypes_attributes = {
        "Structure", "c_uint32", "c_wchar_p", "POINTER", "c_ubyte",
        "WinDLL", "c_int32", "c_void_p", "byref", "get_last_error",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "ctypes":
            require(node.attr in ctypes_attributes, "unreviewed ctypes attribute")
            if node.attr == "WinDLL":
                parent = parents[node]
                require(node in loader_nodes and isinstance(parent, ast.Call) and parent.func is node,
                        "native loader alias/addition")
        if isinstance(node, ast.Name) and node.id == "ctypes":
            require(isinstance(parents[node], ast.Attribute), "ctypes module alias")
        if isinstance(node, ast.Name) and node.id == "_load_advapi32":
            require(node in setup_nodes and isinstance(parents[node], ast.Call) and
                    parents[node].func is node, "DLL acquisition alias/addition")
        if isinstance(node, ast.Attribute) and node.attr == "_dll":
            parent = parents[node]
            require(expression_name(node.value) == "self" and (
                isinstance(parent, ast.Attribute) and parent.attr in {"CredReadW", "CredFree"} or
                isinstance(node.ctx, ast.Store) and node in setup_nodes), "DLL handle alias")
        if isinstance(node, ast.Attribute) and node.attr in {"CredReadW", "CredFree"}:
            require(expression_name(node.value) == "self._dll", "foreign DLL")
            parent = parents[node]
            require((isinstance(parent, ast.Call) and parent.func is node) or
                    (isinstance(parent, ast.Attribute) and parent.attr in {"argtypes", "restype"}),
                    "native function alias")


def inspect_product(root: Path = ROOT) -> dict:
    sources = {}
    ctypes_sources = []
    calls = []
    for path in sorted((root / "nayeon").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        require(not path.is_symlink(), "source symlink")
        raw = path.read_bytes()
        source = raw.decode("utf-8-sig")
        tree = ast.parse(source, filename=relative)
        sources[relative] = hashlib.sha256(raw).hexdigest()
        if relative == BACKEND:
            check_backend(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                native = [a for a in node.names if a.name == "ctypes" or a.name.startswith("ctypes.")]
                if native:
                    require(relative in CTYPES_OWNERS and
                            all(a.name == "ctypes" and a.asname is None for a in native),
                            "unreviewed ctypes import/alias: " + relative)
                    ctypes_sources.append(relative)
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("ctypes"):
                require(relative in CTYPES_OWNERS and node.module == "ctypes" and
                        all(a.name == "wintypes" and a.asname in {None, "w", "W"} for a in node.names),
                        "unreviewed ctypes from-import/alias: " + relative)
                ctypes_sources.append(relative)
            elif isinstance(node, (ast.Name, ast.Attribute)):
                name = node.id if isinstance(node, ast.Name) else node.attr
                require(not name.startswith(("CredWrite", "CredDelete", "CredEnumerate")),
                        "product native effect reference: " + relative)
                if name.startswith("CredRead") or name == "CredFree":
                    require(relative == BACKEND and name in {"CredReadW", "CredFree"},
                            "unreviewed native reader: " + relative)
            if isinstance(node, ast.Call):
                name = expression_name(node.func)
                if name.endswith((".CredReadW", ".CredFree")):
                    calls.append({"path": relative, "line": node.lineno, "call": name})
    require(BACKEND in sources and all(path in sources for path in DEPENDENCIES), "missing product source")
    return {
        "SOURCE_NATIVE_EFFECTS": "NONE", "SOURCE_NATIVE_PLAINTEXT_RETURN": "NONE",
        "PRODUCTION": "HOLD", "REAL_KEYS": "NO-GO",
        "scope": "current product Python source; no OS isolation or deployed artifact revocation",
        "parent": PARENT, "source_sha256": sources,
        "native_presence_calls": calls, "reviewed_ctypes_owners": sorted(set(ctypes_sources)),
        "dependency_paths": list(DEPENDENCIES),
    }


if __name__ == "__main__":
    print(json.dumps(inspect_product(), sort_keys=True, indent=2))
