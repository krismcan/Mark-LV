"""P251 bounded source diagnostic. Reads bytes only, always denies release.

Pins identify the reviewed parent source snapshot, without authenticating it.
No production module is imported. No recursive source discovery is performed.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat


REPO_ROOT = Path(__file__).absolute().parents[1]
INTENDED_ROOT = Path(r"D:\Nayeon\CODEX_P251_EFFECT_PATH_RELEASE_GATE_20261116")
LAUNCH = "nayeon/desktop_alpha/local_byok_launch_bridge.py"
WINDOW = "nayeon/desktop_alpha/local_byok_window.py"
CONTROLLER = "nayeon/brain/local_byok_user_scope.py"
BACKEND = "nayeon/secrets/windows_credential.py"
P96 = "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs"
P250 = "docs/byok-c1-p250-p96-service-owned-ordering-architecture.md"
SOURCE_HASHES = {
    LAUNCH: "1fb8a889c7dcba0a83c1dbc888bd1d7deb219bcff3fc08cadeb246f61b3c71d5",
    WINDOW: "8dfdfc587886471f312d39aa53bc049179a7ca2d61bc310f84ac142ba5d103e6",
    CONTROLLER: "1971a3f7f90c840fb6c3dc95128ecb6cf2a5e855204d418d99144eb10f3a17b6",
    BACKEND: "e6443853300fb2fb4944b8c8bede2ee953719eaf7544d7338056d81491b46125",
    P96: "d8b8e4c6d5ea5e035b58c6ad73dd758c16640167c804ccf3305969b12bdf81ab",
    P250: "def6c23193a9b26ef0046e76e6d296aa75baf2dfaac603827dc0e7820cbd0b6b",
}

# Exact lexical call sites inside reviewed definitions. These describe source
# relationships, never control/data-flow proof or authorization.
CALL_SITES = (
    (LAUNCH, "LocalByokLaunchBridge.launch", "subprocess.Popen", "child_process"),
    (WINDOW, "main", "compose_user_scope_local_byok", "composition"),
    (WINDOW, "LocalByokWindow.approve_from_button", "self._controller.approve", "approval_dispatch"),
    (CONTROLLER, "compose_user_scope_local_byok", "WindowsCredentialBackend", "backend_construction"),
    (CONTROLLER, "LocalByokController.approve", "self._backend.put", "save_or_replace"),
    (CONTROLLER, "LocalByokController.approve", "self._backend.delete", "remove"),
    (BACKEND, "WindowsCredentialBackend.put", "self._adapter().write", "adapter_write"),
    (BACKEND, "WindowsCredentialBackend.delete", "self._adapter().delete", "adapter_delete"),
    (BACKEND, "_Advapi32Adapter.write", "self._dll.CredWriteW", "native_credential_write"),
    (BACKEND, "_Advapi32Adapter.delete", "self._dll.CredDeleteW", "native_credential_delete"),
    (BACKEND, "WindowsCredentialBackend._adapter", "_Advapi32Adapter", "lazy_native_adapter"),
    (BACKEND, "_Advapi32Adapter.__init__", "_load_advapi32", "native_library_setup"),
    (BACKEND, "_load_advapi32", "ctypes.WinDLL", "native_library_load"),
    (BACKEND, "_Advapi32Adapter._acquire", "self._dll.CredReadW", "native_credential_read_or_presence"),
    (BACKEND, "_Advapi32Adapter.read", "self._dll.CredFree", "native_buffer_release"),
    (BACKEND, "_Advapi32Adapter.contains", "self._dll.CredFree", "native_buffer_release"),
)
TEXT_SITES = (
    (LAUNCH, '_CHILD_MODULE = "nayeon.desktop_alpha.local_byok_window"', "fixed_child_module"),
    (LAUNCH, 'command = [sys.executable, "-B", "-m", _CHILD_MODULE]', "source_child_command"),
    (CONTROLLER, '_FIXED_IDENTIFIER = SecretIdentifier("openai.api_key")', "fixed_identifier"),
    (BACKEND, '_TARGET_PREFIX = "nayeon-v1/secret/"', "user_vault_namespace"),
    (P96, "state.DeletePending();", "historical_delete_callback"),
    (P96, "state.SaveOrReplace(owned);", "historical_save_replace_callback"),
)
LIMITATIONS = (
    "Bounded known source routes only; no complete security or route inventory.",
    "Hashes identify bytes only; no source authenticity or loaded graph proof.",
    "AST/text relationships are not dynamic call, reachability or effect execution proof.",
    "Path checks reduce symlink/reparse traversal; concurrent replacement and hardlinks remain outside assurance.",
    "No independent qualification is accepted or established by this diagnostic.",
)


def _read_source(root: Path, relative: str) -> bytes:
    """Check every ancestor before a bounded, fixed-path read, without resolve."""
    path = root / relative
    for component in reversed((path, *path.parents)):
        info = component.lstat()
        reparse = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if stat.S_ISLNK(info.st_mode) or reparse:
            raise ValueError("symlink_or_reparse_path")
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("non_regular_source")
    with path.open("rb") as source:
        data = source.read(1_000_001)
    if len(data) > 1_000_000:
        raise ValueError("source_too_large")
    return data


def _ast_records(tree: ast.AST) -> tuple[list[dict], list[dict]]:
    calls = []
    imports = []

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = (*scope, node.name)
        if isinstance(node, ast.Call):
            calls.append({"scope": ".".join(scope), "call": ast.unparse(node.func), "line": node.lineno})
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append({"line": node.lineno, "statement": ast.unparse(node)})
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree, ())
    return calls, imports


def _assess(root: Path) -> dict:
    """Internal fixed-manifest engine, also exercised with temporary fixtures."""
    sources = []
    evidence = []
    issues = []
    for relative, expected in SOURCE_HASHES.items():
        record = {"path": relative, "expected_sha256": expected}
        sources.append(record)
        try:
            data = _read_source(root, relative)
            record["sha256"] = hashlib.sha256(data).hexdigest()
            record["matches_reviewed_snapshot"] = record["sha256"] == expected
            if not record["matches_reviewed_snapshot"]:
                issues.append({"path": relative, "reason": "source_hash_drift_including_possible_sink_or_import_change"})
            source = data.decode("utf-8-sig")
            calls = []
            if relative.endswith(".py"):
                calls, record["imports"] = _ast_records(ast.parse(source, filename=relative))
            for path, scope, call, effect in CALL_SITES:
                if path != relative:
                    continue
                matches = [entry for entry in calls if entry["scope"] == scope and entry["call"] == call]
                if len(matches) != 1:
                    issues.append({"path": relative, "reason": "known_call_site_changed", "site": effect})
                for entry in matches:
                    evidence.append({"path": relative, "kind": effect, **entry})
            lines = source.splitlines()
            for path, text, kind in TEXT_SITES:
                if path != relative:
                    continue
                matches = [index for index, line in enumerate(lines, 1) if line.strip() == text]
                if len(matches) != 1:
                    issues.append({"path": relative, "reason": "known_text_site_changed", "site": kind})
                for line in matches:
                    evidence.append({"path": relative, "kind": kind, "line": line})
        except (OSError, ValueError, SyntaxError, RecursionError) as error:
            # Emit no source contents or arbitrary exception messages.
            issues.append({"path": relative, "reason": type(error).__name__})
    return _report(sources, evidence, issues)


def _report(sources: list, evidence: list, issues: list) -> dict:
    """Common conservative schema, including refusals before source reads."""
    return {
        "schema": "byok-c1-p251-v1",
        "status": "HOLD",
        "assessment": "UNKNOWN" if issues else "KNOWN_EFFECT_EXPOSURE",
        "release_admitted": False,
        "independently_qualified": False,
        "sources": sources,
        "evidence": evidence,
        "issues": issues,
        "known_routes": [
            "source launcher -> local window main/factory -> controller approve -> backend put/delete -> adapter CredWriteW/CredDeleteW",
            "direct backend put/delete -> adapter native mutation (controller/service owner absent from these method bodies)",
            "P96 Apply -> state DeletePending/SaveOrReplace interface callbacks (separate historical route)",
        ] if sources else [],
        "limitations": list(LIMITATIONS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", action="store_true", help="assess evidence and emit HOLD JSON (default)")
    mode.add_argument("--release-admission", action="store_true", help="emit HOLD JSON and refuse admission")
    args = parser.parse_args(argv)
    if os.path.normcase(os.path.abspath(REPO_ROOT)) != os.path.normcase(os.path.abspath(INTENDED_ROOT)):
        report = _report([], [], [{"reason": "unintended_repository_root"}])
    else:
        report = _assess(REPO_ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 3 if args.release_admission else 0


if __name__ == "__main__":
    raise SystemExit(main())
