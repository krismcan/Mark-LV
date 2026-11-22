"""Read-only current-source evidence for future hosted Windows PR review.

No product imports, native invocation, real key, or whole-system isolation.
Qualified approvals remain 0/7; full product regressions remain 0/3.
Run: python -I -B scripts/p298_current_effect_boundary_audit.py
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
INVENTORY = "scripts/p275_product_effect_entrypoint_inventory.py"
BACKEND = "nayeon/secrets/windows_credential.py"
CONTROLLER = "nayeon/brain/local_byok_user_scope.py"
NATIVE = "native_c1_successor/P274EphemeralWinCredEffect.cs"
# Exact decoded source, with universal newlines for Windows checkout support.
# Any other source change requires renewed review; these are not artifact pins.
PINS = {
    INVENTORY: "48e7cc20c83b984b80c25a2fa4217baaf84a94f45618518c26eebd14e7125ee7",
    BACKEND: "9ffb136a73e4277b966fae025a3962123433745b6ba8907ab3b8c4137f4a21b3",
    CONTROLLER: "24b8457f219f02d3ea47fe59df2f1e860f01db3bb6a83531307da0656759ffe4",
    NATIVE: "6e1ec6d964c9686768d08206bbc404d0964ca50d1497235491c22c47e7d02ece",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError("P298 source HOLD: " + reason)


def body(node):
    statements = list(node.body)
    if (statements and isinstance(statements[0], ast.Expr)
            and isinstance(statements[0].value, ast.Constant)
            and isinstance(statements[0].value.value, str)):
        statements = statements[1:]
    return statements


def contract(statements, expected: str) -> None:
    require(ast.dump(ast.Module(body=statements, type_ignores=[])) ==
            ast.dump(ast.parse(expected)), "AST execution contract")


def named(nodes, kind, name):
    matches = [n for n in nodes if isinstance(n, kind) and n.name == name]
    require(len(matches) == 1, "missing/duplicate " + name)
    return matches[0]


def check_python_sources(backend: str, controller: str) -> None:
    """Pure AST checks: strings only; never import or execute product source."""
    from scripts.p275_product_effect_entrypoint_inventory import check_backend

    check_backend(backend)  # Native surface is exactly CredReadW/CredFree.
    tree = ast.parse(backend)
    cls = named(tree.body, ast.ClassDef, "WindowsCredentialBackend")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    contract(body(methods["__init__"]), """self._native = _native
self._injected_read_adapter = _native
""")
    contract(body(methods["_injected_mutation_adapter"]), """
if self._native is None or isinstance(self._native, _Advapi32Adapter):
    return None
return self._native
""")
    contract(body(methods["get"])[:3], """target = self._target(identifier)
adapter = self._injected_read_adapter
if adapter is None:
    raise SecretStorageError(_FAILURE)
""")
    contract(body(methods["put"])[:4], """target = self._target(identifier)
if type(value) is not SecretValue:
    raise TypeError("Value must be an exact SecretValue")
adapter = self._injected_mutation_adapter()
if adapter is None:
    raise SecretStorageError(_FAILURE)
""")
    contract(body(methods["delete"])[:3], """target = self._target(identifier)
adapter = self._injected_mutation_adapter()
if adapter is None:
    raise SecretStorageError(_FAILURE)
""")
    tree = ast.parse(controller)
    cls = named(tree.body, ast.ClassDef, "LocalByokController")
    init = named(cls.body, ast.FunctionDef, "__init__")
    contract(body(init)[:3], """
if type(backend) is not WindowsCredentialBackend:
    raise TypeError("Exact user-account Windows credential backend required")
self._backend = backend
self._mutation_backend = backend if backend._injected_mutation_adapter() is not None else None
""")
    for name, expected in (
        ("begin", "if self._mutation_backend is None:\n    return None"),
        ("approve", "if self._mutation_backend is None:\n"
         "    self._pending = None\n    return LocalByokOutcome.REFUSED"),
    ):
        method = named(cls.body, ast.FunctionDef, name)
        first = body(method)[0]
        require(isinstance(first, ast.With) and len(first.items) == 1,
                name + " early lock")
        require(ast.dump(first.items[0].context_expr) ==
                ast.dump(ast.parse("self._gate", mode="eval").body), name + " lock")
        contract(first.body[:1], expected)
    factory = named(tree.body, ast.FunctionDef, "compose_user_scope_local_byok")
    contract(body(factory), "return LocalByokController(WindowsCredentialBackend())")


def check_red_mutations(backend: str, controller: str) -> None:
    mutations = (
        (backend.replace("CredReadW", "CredWriteW"), controller),
        (backend.replace("if self._native is None or isinstance(self._native, _Advapi32Adapter):",
                         "if False:"), controller),
        (backend, controller.replace("if self._mutation_backend is None:", "if False:")),
    )
    for altered_backend, altered_controller in mutations:
        require((altered_backend, altered_controller) != (backend, controller),
                "red mutation was not applied")
        try:
            check_python_sources(altered_backend, altered_controller)
        except AssertionError:
            continue
        raise AssertionError("P298 source HOLD: AST accepted red mutation")


def main() -> None:
    sources = {}
    for relative, expected in PINS.items():
        path = ROOT / relative
        require(not any(p.is_symlink() for p in (path, *path.parents)), "source symlink")
        source = path.read_text(encoding="utf-8-sig")
        require(hashlib.sha256(source.encode("utf-8")).hexdigest() == expected,
                "reviewed source hash: " + relative)
        sources[relative] = source
    # Import only the pinned read-only auditor, never the product/native code.
    from scripts.p275_product_effect_entrypoint_inventory import inspect_product

    inspect_product(ROOT)  # Reuse the full inherited product-wide AST review.
    check_python_sources(sources[BACKEND], sources[CONTROLLER])
    check_red_mutations(sources[BACKEND], sources[CONTROLLER])
    guards = """#if !DEBUG
#error P274_NO_RELEASE_BUILD
#endif
#if !C1_P268_DEVELOPMENT_ONLY
#error P274_REQUIRES_P268_DEVELOPMENT_ONLY
#endif
#if !C1_P274_EPHEMERAL_WINCRED_ONLY
#error P274_EPHEMERAL_OPT_IN_REQUIRED
#endif
"""
    require(sources[NATIVE].startswith(guards), "native development-only guards")
    # The full C# hash also rejects guard removal, else branches and additions.
    print("P298_EFFECT_BOUNDARY_AUDIT=PASS PRODUCT_RELEASE=HOLD")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("P298_EFFECT_BOUNDARY_AUDIT=FAIL PRODUCT_RELEASE=HOLD", file=sys.stderr)
        raise SystemExit(1) from None
