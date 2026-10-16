"""Phase 8.30 exact, immutable source addition authorization for historical tests.

The existing 8.29 helper is untouched. This is not a wildcard migration.
Every invocation independently verifies disk, index and HEAD, including old
production sources; absence must be evidenced by enumerated Git trees.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = "058c622a04a26a882c773533c568371c53b9b140"
OWNER = "nayeon/desktop_alpha/presentation_profile_owner.py"
OWNER_SHA256 = "c17ec6eca4637b9a28dbe51e6a3cd3481c8a631dae23c30353c39777f5c1bd38"
OWNER_MODE = "100644"
APPROVED_NEW_SHA256 = {
    OWNER: OWNER_SHA256,
    "nayeon/desktop_alpha/application.py":
        "289251bd72b35d9a0e9c840bca5e0d7eb6c4328bd28a8e9149de80076f2e6b05",
    "nayeon/desktop_alpha/workspace_window.py":
        "2730f8f610f5bb272571f06a8eb523aa7e8c4a95d1518e7365177bfe695c46d8",
    "nayeon/desktop_alpha/presentation_window.py":
        "d78ce629162ffaca652a8c7681cf3e637e49547b5c86f9a5b2ec9a98dede79ce",
}
APPROVED_MODIFIED_SHA256 = {
    "nayeon/desktop_alpha/window.py":
        "9a448db3fc793d7af7aad2cb56d10c79af90ab4cd50c2f762b230b1f1d396e92",
}
APPROVED_SOURCE_SHA256 = {**APPROVED_NEW_SHA256, **APPROVED_MODIFIED_SHA256}
CONFIG_IMPORT_ALLOW = {
    OWNER: {
        "nayeon.config.bootstrap": {"bootstrap_presentation_configuration"},
        "nayeon.config.document": {
            "PresentationConfigurationDocumentV1",
            "parse_presentation_configuration_document",
            "presentation_configuration_document_to_mapping",
        },
    },
    "nayeon/desktop_alpha/application.py": {
        "nayeon.config.document": {"PresentationConfigurationDocumentV1"},
    },
    "nayeon/desktop_alpha/presentation_window.py": {
        "nayeon.config.document": {
            "PresentationConfigurationDocumentV1",
            "parse_presentation_configuration_document",
            "presentation_configuration_document_to_mapping",
        },
        "nayeon.config.presentation": {
            "AssistantPresentationIdentity", "UserPresentationProfile",
        },
    },
    "nayeon/desktop_alpha/workspace_window.py": {},
    "nayeon/desktop_alpha/window.py": {},
}
OWNER_ALLOWED_IMPORTS = {
    "nayeon.config.bootstrap": {"bootstrap_presentation_configuration"},
    "nayeon.config.document": {
        "PresentationConfigurationDocumentV1",
        "parse_presentation_configuration_document",
        "presentation_configuration_document_to_mapping",
    },
}


def _git(*args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL, timeout=20
        )
    except (subprocess.SubprocessError, OSError):
        raise AssertionError("Unable to verify exact Git snapshot") from None


def _normal(data: bytes) -> bytes:
    if type(data) is not bytes:
        raise AssertionError("Source byte type invalid")
    return data.replace(b"\r\n", b"\n")


def _oid(data: bytes) -> str:
    norm = _normal(data)
    prefix = b"blob " + str(len(norm)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + norm).hexdigest()



def _production_git_path(path: str) -> bool:
    """Reject Windows aliases even if Git's literal path filter would miss them."""
    if type(path) is not str or not path:
        raise AssertionError("Invalid Git pathname")
    # Git's pathspec can miss a second root differing only in case. On Windows
    # backslashes and Unicode case-equivalent names must not authorize aliases.
    win = unicodedata.normalize("NFC", path.replace("\\", "/")).casefold()
    root_component = win.split("/", 1)[0].rstrip(" .")
    # Windows strips trailing ASCII dots/spaces from component lookup; their
    # Git names are different but can address the same production directory.
    if root_component == "nayeon" or root_component.startswith("nayeon:"):
        if not path.startswith("nayeon/"):
            raise AssertionError("Aliased production root")
        parts = path.split("/")
        if any(not part or part in {".", ".."} or part != part.rstrip(" .")
               or ":" in part or "\\" in part for part in parts):
            raise AssertionError("Noncanonical Windows production pathname")
        return True
    return False


def _reject_linked_parents(path: Path) -> None:
    """Check source ancestry without following any Windows reparse directory."""
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        raise AssertionError("Production source outside repository") from None
    current = ROOT
    for part in ("", *relative.parts[:-1]):
        if part:
            current = current / part
        try:
            info = current.lstat()
        except OSError:
            raise AssertionError("Production parent unavailable") from None
        if (not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or (getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))):
            raise AssertionError("Linked or reparse production parent")


def _tree(commit: str) -> dict[str, tuple[str, str]]:
    # Enumerate the FULL tree first. Literal pathspecs miss Windows aliases.
    records = _git("ls-tree", "-r", "-z", "--full-tree", commit).split(b"\0")
    tree = {}
    for item in records:
        if not item:
            continue
        try:
            meta, raw_path = item.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split(" ")
            path = raw_path.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError):
            raise AssertionError("Malformed production tree") from None
        if _production_git_path(path):
            if path in tree or kind != "blob":
                raise AssertionError("Invalid production tree entry")
            tree[path] = (mode, oid)
    return tree


def _index() -> dict[str, tuple[str, str]]:
    records = _git("ls-files", "--stage", "-z").split(b"\0")
    index = {}
    for item in records:
        if not item:
            continue
        try:
            meta, raw_path = item.split(b"\t", 1)
            mode, oid, stage = meta.decode("ascii").split(" ")
            path = raw_path.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError):
            raise AssertionError("Malformed production index") from None
        if _production_git_path(path):
            if stage != "0" or path in index:
                raise AssertionError("Unmerged or repeated source index entry")
            index[path] = (mode, oid)
    return index


def _approved_source(relative: str) -> str:
    if relative not in APPROVED_SOURCE_SHA256:
        raise AssertionError("Unlisted 8.30 source")
    path = ROOT / relative
    _reject_linked_parents(path)
    if path.is_symlink() or not path.is_file():
        raise AssertionError("Missing, linked or nonregular 8.30 source")
    disk = _normal(path.read_bytes())
    if hashlib.sha256(disk).hexdigest() != APPROVED_SOURCE_SHA256[relative]:
        raise AssertionError("Unapproved 8.30 source bytes")
    return _oid(disk)


def _approved_owner() -> str:
    return _approved_source(OWNER)


def assert_830_integrity() -> None:
    """Fail closed for an unauthorized on-disk, staged or committed source."""
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported Git object format")
    current_head = _git("rev-parse", "HEAD").decode("ascii").strip()
    if _git("branch", "--show-current").decode("utf-8").strip() != "nayeon-v1":
        raise AssertionError("Wrong production branch")
    _git("merge-base", "--is-ancestor", PROTECTED, current_head)
    baseline = _tree(PROTECTED)
    approved_new = set(APPROVED_NEW_SHA256)
    approved_modified = set(APPROVED_MODIFIED_SHA256)
    if (not baseline or approved_new & set(baseline)
            or not approved_modified <= set(baseline)):
        raise AssertionError("Protected source snapshot invalid")
    head = _tree(current_head)
    index = _index()
    approved_refs = {
        path: (OWNER_MODE, _approved_source(path))
        for path in APPROVED_SOURCE_SHA256
    }
    if set(head) - approved_new != set(baseline):
        raise AssertionError("Unauthorized committed production inventory")
    if set(index) - approved_new != set(baseline):
        raise AssertionError("Unauthorized staged production inventory")
    for path in approved_new:
        expected = approved_refs[path]
        if current_head != PROTECTED:
            # Once this milestone is committed, every required module MUST
            # be in both HEAD and index. Disk-only candidates are not a seal.
            if head.get(path) != expected:
                raise AssertionError("Missing or unapproved committed 8.30 source")
            if index.get(path) != expected:
                raise AssertionError("Missing or unapproved staged 8.30 source")
        else:
            if path in head:
                raise AssertionError("Unexpected precommit 8.30 product source")
            if path in index and index[path] != expected:
                raise AssertionError("Unapproved staged 8.30 source")
    for path, ref in baseline.items():
        if path in approved_modified:
            approved = approved_refs[path]
            if current_head == PROTECTED:
                # Only the protected pre-product checkpoint can still carry
                # the original blob in HEAD or the index during preparation.
                if head[path] != ref or index[path] not in {ref, approved}:
                    raise AssertionError("Unapproved entrypoint source change")
            elif head[path] != approved or index[path] != approved:
                # Once committed, staging an old entrypoint is a rollback,
                # not a permitted historical-source transition.
                raise AssertionError("Postcommit entrypoint rollback refused")
        elif head[path] != ref or index[path] != ref:
            raise AssertionError("Frozen committed or staged production modified")
    # An untracked candidate must be visible in the worktree; ignored .py
    # additions cannot hide just because Git excludes them from its status.
    actual_py = set()
    _reject_linked_parents(ROOT / "nayeon" / "_path_guard.py")
    for file in (ROOT / "nayeon").rglob("*.py"):
        _reject_linked_parents(file)
        rel = file.relative_to(ROOT).as_posix()
        if file.is_symlink() or not file.is_file():
            raise AssertionError("Linked or invalid production source")
        actual_py.add(rel)
    expected_py = {p for p in baseline if p.endswith(".py")} | approved_new
    if actual_py != expected_py:
        raise AssertionError("Unexpected or missing production Python source")
    # Preserve *all* protected production blobs, including two repaired 8.29
    # files, without depending on the early-return path in the 8.29 helper.
    for path, (mode, oid) in baseline.items():
        leaf = ROOT / path
        _reject_linked_parents(leaf)
        if leaf.is_symlink() or not leaf.is_file() or mode not in {"100644", "100755"}:
            raise AssertionError("Frozen production type changed")
        if path in approved_modified:
            if _approved_source(path) != approved_refs[path][1]:
                raise AssertionError("Unapproved entrypoint worktree bytes")
        elif _oid(leaf.read_bytes()) != oid:
            raise AssertionError("Frozen production worktree bytes modified")
    for path in actual_py:
        if path not in approved_new and path not in baseline:
            raise AssertionError("Unknown production module")
    # Reject extra Git-visible source objects regardless of extension.
    untracked = _git("ls-files", "--others", "--exclude-standard", "-z")
    additions = set()
    for entry in untracked.split(b"\0"):
        if entry:
            path = entry.decode("utf-8", "strict")
            if _production_git_path(path):
                additions.add(path)
    if additions - approved_new:
        raise AssertionError("Unexpected untracked production source")


def approved_830_scope(actual: set[str]) -> set[str]:
    if type(actual) is not set or any(type(x) is not str for x in actual):
        raise AssertionError("Untrusted production delta")
    assert_830_integrity()
    # A changed historic window.py is already part of some old sealed deltas.
    # Remove ONLY newly introduced 8.30 paths from those comparisons.
    return actual - set(APPROVED_NEW_SHA256)


def approved_830_files(actual: set[str]) -> set[str]:
    if type(actual) is not set or any(type(x) is not str for x in actual):
        raise AssertionError("Untrusted production inventory")
    assert_830_integrity()
    return actual - set(APPROVED_NEW_SHA256)


def _assert_exact_config_imports(relative: str) -> None:
    """Exactly approved config consumers, including their imported symbols."""
    import ast
    if relative not in CONFIG_IMPORT_ALLOW:
        raise AssertionError("Unknown presentation consumer")
    assert_830_integrity()
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    observed = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "nayeon.config" or node.module.startswith("nayeon.config."):
                if node.module not in CONFIG_IMPORT_ALLOW[relative]:
                    raise AssertionError("Forbidden configuration import")
                if node.module in observed:
                    raise AssertionError("Repeated configuration import")
                names = [alias.name for alias in node.names]
                if (set(names) != CONFIG_IMPORT_ALLOW[relative][node.module]
                        or len(names) != len(set(names))
                        or any(alias.asname for alias in node.names)):
                    raise AssertionError("Unexpected configuration import names")
                observed[node.module] = set(names)
        if isinstance(node, ast.Import):
            if any(alias.name == "nayeon.config"
                   or alias.name.startswith("nayeon.config.")
                   for alias in node.names):
                raise AssertionError("Dynamic configuration import route")
    if observed != CONFIG_IMPORT_ALLOW[relative]:
        raise AssertionError("Missing approved configuration import")


def assert_exact_owner_imports() -> None:
    _assert_exact_config_imports(OWNER)


def assert_exact_830_source_imports() -> None:
    for relative in CONFIG_IMPORT_ALLOW:
        _assert_exact_config_imports(relative)


# Retain the full 8.29 security migration. Permit only SHA-pinned 8.30
# additions plus the exact redirected old desktop main() body.
from tests.phase_8_29_lifecycle_scope_migration import (
    migrated_scope as _phase829_migrated_scope,
    assert_frozen_or_revocable as _phase829_frozen,
)


def migrated_scope(actual: set[str], *, include_onboarding: bool = False) -> set[str]:
    return _phase829_migrated_scope(
        approved_830_scope(actual), include_onboarding=include_onboarding
    )


def assert_frozen_or_revocable(testcase, path, current, baseline, *messages):
    if path in APPROVED_MODIFIED_SHA256:
        assert_830_integrity()
        if len(messages) > 1 or any(type(m) is not str for m in messages):
            raise AssertionError("Invalid frozen source assertion")
        message = messages[0] if messages else path
        expected = _normal((ROOT / path).read_bytes())
        if type(current) is str:
            current = current.encode("utf-8")
        testcase.assertEqual(_normal(current), expected, message)
        return
    return _phase829_frozen(testcase, path, current, baseline, *messages)


def owner_may_reference(path: str, targets: set[str]) -> bool:
    """Legacy test adapter: only actual, exactly pinned config consumers."""
    if type(targets) is not set or any(type(t) is not str for t in targets):
        raise AssertionError("Invalid consumer target inventory")
    if path not in CONFIG_IMPORT_ALLOW:
        return False
    symbols = set()
    for module, names in CONFIG_IMPORT_ALLOW[path].items():
        symbols.add(module)
        symbols.add(module.rsplit(".", 1)[-1])
        symbols.update(names)
    if path == "nayeon/desktop_alpha/application.py":
        # The old zero-consumer view guard treats *every* local variable named
        # view as a forbidden config.view import. The pinned composition uses
        # view only for a Tk instance; its exact import tree excludes config.view.
        symbols.add("view")
    if not targets & symbols:
        return False
    _assert_exact_config_imports(path)
    return True
