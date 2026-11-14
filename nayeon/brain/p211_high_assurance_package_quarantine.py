"""P211 nondeployable high-assurance package *isolation* preflight.

The current repo has REAL Python CredWrite/Delete capability (P132/P133).
No genuine high-assurance signer, installer, kernel-enforced source isolation,
trusted service or security review exists. This module is a fail-closed
packaging INTAKE CANDIDATE, not a runtime security monitor or production
release gate. It never imports original credential modules or shells out.
All release decisions are permanently DENIED. A source-name allowlist or
Python flag cannot isolate an attacker running as the same Windows user.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


_FIXED_LEGACY_FILES = (
    "nayeon/secrets/windows_credential.py",
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "nayeon/desktop_alpha/local_byok_window.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
    "native_c1_candidate/CustodyService.cs",
)
# Review-only text has no interpreter, executable, runtime, code or secret.
# Never broaden this into a product allowlist: a future authoritatively
# signed service/installer requires a separately security-reviewed policy.
_REVIEW_ONLY_EXACT = frozenset({"P211_QUARANTINE_README.txt"})
_MAX_PLAN_ENTRIES = 128


class P211Refusal(str, Enum):
    INVALID_PLAN = "INVALID_PLAN"
    UNTRUSTED_PATH = "UNTRUSTED_PATH"
    UNRECOGNISED_PAYLOAD = "UNRECOGNISED_PAYLOAD"
    LEGACY_EFFECT_PATH = "LEGACY_EFFECT_PATH"
    SOURCE_UNPROVEN = "SOURCE_UNPROVEN"
    ABSENT_RELEASE_AUTHORITY = "ABSENT_RELEASE_AUTHORITY"


@dataclass(frozen=True, slots=True)
class P211SourceWitness:
    exact_legacy_source_readable: bool
    python_direct_native_credential_effect: bool
    p132_product_constructor_and_effect: bool
    p133_source_mode_launcher: bool
    frozen_companion_pins_absent: bool
    native_c1_service_denial_only: bool

    @property
    def high_assurance_legacy_risk_present(self) -> bool:
        return (
            self.python_direct_native_credential_effect
            and self.p132_product_constructor_and_effect
            and self.p133_source_mode_launcher
        )


@dataclass(frozen=True, slots=True)
class P211PackageRefusalReceipt:
    reason: P211Refusal
    manifest_entries: int
    source_witness: P211SourceWitness | None
    release_eligible: bool = False
    credential_mutation_authorised: bool = False
    signed_installer_authorised: bool = False
    trusted_runtime_isolation_proven: bool = False
    real_key_pilot_authorised: bool = False

    def __post_init__(self) -> None:
        # Impossible to construct an artificial positive release receipt.
        if any((
            self.release_eligible,
            self.credential_mutation_authorised,
            self.signed_installer_authorised,
            self.trusted_runtime_isolation_proven,
            self.real_key_pilot_authorised,
        )):
            raise ValueError("P211 package authority cannot be minted")


def _source(root: Path, relative: str) -> str | None:
    """Read exact source only when each source path and its parents are ordinary.

    This is a defensive review check, NOT a Windows FileId/volume root binding
    or proof against a path substitution race. Production must use prebound
    handles and a machine-enforced image/installer authority.
    """
    try:
        if not isinstance(root, Path) or not root.is_absolute():
            return None
        current = root
        if current.is_symlink() or not current.is_dir():
            return None
        for part in relative.split("/"):
            current = current / part
            if current.is_symlink():
                return None
            if getattr(current.lstat(), "st_file_attributes", 0) & 0x400:
                return None
        if not current.is_file() or current.stat().st_size > 128 * 1024:
            return None
        return current.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return None


def _has_class_method(tree: ast.AST, classname: str, method: str) -> bool:
    return any(
        isinstance(n, ast.ClassDef) and n.name == classname
        and any(isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))
                and c.name == method for c in n.body)
        for n in getattr(tree, "body", ())
    )


def _factory_constructs(tree: ast.AST) -> bool:
    return any(
        isinstance(n, ast.FunctionDef)
        and n.name == "compose_user_scope_local_byok"
        and any(isinstance(a, ast.Call) and isinstance(a.func, ast.Name)
                and a.func.id == "WindowsCredentialBackend"
                for a in ast.walk(n))
        for n in getattr(tree, "body", ())
    )


def _method_calls(tree: ast.AST, method: str, member: str) -> bool:
    for node in ast.walk(tree):
        if (isinstance(node, ast.FunctionDef) and node.name == method
            and any(isinstance(a, ast.Call)
                    and isinstance(a.func, ast.Attribute)
                    and a.func.attr == member
                    and isinstance(a.func.value, ast.Attribute)
                    and a.func.value.attr == "_backend"
                    for a in ast.walk(node))):
            return True
    return False


def inspect_current_source_tree(root: Path) -> P211SourceWitness:
    """Return source-derived risk evidence; missing/changed source is NOT safe."""
    raw = {path: _source(root, path) for path in _FIXED_LEGACY_FILES}
    present = all(text is not None for text in raw.values())
    try:
        backend = ast.parse(raw["nayeon/secrets/windows_credential.py"] or "")
        user = ast.parse(raw["nayeon/brain/local_byok_user_scope.py"] or "")
    except (SyntaxError, ValueError):
        backend = ast.parse("")
        user = ast.parse("")
    original = raw["nayeon/secrets/windows_credential.py"] or ""
    scope = raw["nayeon/brain/local_byok_user_scope.py"] or ""
    launch = raw["nayeon/desktop_alpha/local_byok_launch_bridge.py"] or ""
    frozen = raw["nayeon/desktop_alpha/frozen_signed_byok_companion.py"] or ""
    native = raw["native_c1_candidate/CustodyService.cs"] or ""
    # A negative signal due to tampering/missing source is SOURCE_UNPROVEN,
    # never evidence that legacy effects were successfully removed.
    direct = (
        _has_class_method(backend, "_Advapi32Adapter", "write")
        and _has_class_method(backend, "_Advapi32Adapter", "delete")
        and _has_class_method(backend, "WindowsCredentialBackend", "put")
        and _has_class_method(backend, "WindowsCredentialBackend", "delete")
        and ".CredWriteW" in original and ".CredDeleteW" in original
    )
    reachable = (
        _factory_constructs(user)
        and _has_class_method(user, "LocalByokController", "approve")
        and "_backend.put(_FIXED_IDENTIFIER, candidate)" in scope
        and "_backend.delete(_FIXED_IDENTIFIER)" in scope
    )
    launcher = (
        "nayeon.desktop_alpha.local_byok_window" in launch
        and 'command = [sys.executable, "-B", "-m", _CHILD_MODULE]' in launch
    )
    pins = (
        '_APPROVED_MAIN_SHA256 = ""' in frozen
        and '_APPROVED_COMPANION_SHA256 = ""' in frozen
        and '_APPROVED_SIGNER_CERT_SHA256 = ""' in frozen
        and "_APPROVED_CODE_INTEGRITY_RELEASE = False" in frozen
    )
    held = (
        'throw new InvalidOperationException("Custody service is unavailable")' in native
        and "ServiceBase.Run(" not in native
    )
    return P211SourceWitness(present,direct,reachable,launcher,pins,held)


def _canonical_plan_name(name: object) -> bool:
    if type(name) is not str or not 1 <= len(name) <= 190:
        return False
    if name != name.strip() or "\\" in name or ":" in name:
        return False
    if name.startswith("/") or name.endswith("/") or "//" in name:
        return False
    parts = name.split("/")
    if any(
        not part or part in (".", "..")
        or part[-1] in (".", " ")
        or any(ord(c) < 33 or ord(c) == 127 for c in part)
        for part in parts
    ):
        return False
    return True


def review_high_assurance_package_plan(
    root: Path, entries: Iterable[str], *, claimed_signer: object = None,
    claimed_policy_approval: object = None,
) -> P211PackageRefusalReceipt:
    """Deterministic DENY-only intake. Does not build, copy or run payloads.

    The claimed signer/approval fields are intentionally ignored. No caller
    input, package manifest, certificate text or environment override can
    create trusted release authority. The actual OS signed installer, machine
    CI policy and qualified reviewer are absent, and cannot be simulated.
    """
    if type(entries) not in (tuple, list):
        return P211PackageRefusalReceipt(P211Refusal.INVALID_PLAN, 0, None)
    names = list(entries)
    if not names or len(names) > _MAX_PLAN_ENTRIES:
        return P211PackageRefusalReceipt(P211Refusal.INVALID_PLAN, len(names), None)
    if any(not _canonical_plan_name(n) for n in names):
        return P211PackageRefusalReceipt(P211Refusal.UNTRUSTED_PATH,len(names),None)
    if len({n.casefold() for n in names}) != len(names):
        return P211PackageRefusalReceipt(P211Refusal.UNTRUSTED_PATH,len(names),None)
    source = inspect_current_source_tree(root)
    if not source.exact_legacy_source_readable:
        return P211PackageRefusalReceipt(P211Refusal.SOURCE_UNPROVEN,len(names),source)
    if source.high_assurance_legacy_risk_present and any(
        n.casefold().startswith((
            "nayeon/","native_c1_candidate/","core/",
            "tests/","scripts/","build/","dist/"
        )) or n.casefold().endswith((".py",".pyc",".pyd",".dll",".exe",
                                    ".zip",".whl",".msi",".msix",".ps1"))
        for n in names
    ):
        return P211PackageRefusalReceipt(P211Refusal.LEGACY_EFFECT_PATH,len(names),source)
    if any(n not in _REVIEW_ONLY_EXACT for n in names):
        return P211PackageRefusalReceipt(P211Refusal.UNRECOGNISED_PAYLOAD,len(names),source)
    return P211PackageRefusalReceipt(
        P211Refusal.ABSENT_RELEASE_AUTHORITY,len(names),source
    )
