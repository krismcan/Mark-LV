"""Phase 8.31 exact source migration, preserving 8.29/8.30 seals.

This is a version-specific security transition, NEVER a wildcard exception.
The original 8.30 helper retains its historical implementation. Current source
admission uses the full protected 8.30 product tree as its immutable baseline;
only two exact modified files and one exact new offline owner can differ.
All Git HEAD/index/untracked trees are enumerated before filtering pathnames.
"""
from __future__ import annotations

import ast
import hashlib

from tests import phase_8_30_scope_migration as prior

ROOT = prior.ROOT
PRODUCT_830 = "6030f9b7afacd0543912bfb4a8b4fe610ebd9632"
PARENT_831 = "8b2fecf00d48324a187d931156cfa463bbd0aa67"
PRODUCT_COMMIT_831 = "79f17ca5211d7e1a97ef99b83dd613885d693bef"
DOC_COMMIT_831 = "c40ab89e0a749d9579583eb4dce93cf508d7ef0f"
MAINTENANCE_FILES = {
    "tests/test_phase_830_scope_integrity.py",
    "tests/phase_8_31_scope_migration.py",
    "tests/test_phase_831_scope_integrity.py",
    ".codex/CURRENT_STATE.md",
    "docs/pre_829_shutdown_ownership_failure_ledger.md",
}
NEW = {
    "nayeon/desktop_alpha/conversation_session.py":
        "cddffbba99b557381a415f2a13c861069c41b8694dfbdcdf0b77a0ab552ffa92",
}
MODIFIED = {
    "nayeon/desktop_alpha/application.py":
        "d520d14f98a7e96480c8f975c93ba43026b77eb72655dfdafd78666cf72d8c71",
    "nayeon/desktop_alpha/workspace_window.py":
        "93ee3396291cdd80a57754fbf3bd8382233d6ebd166102ead6004cb5af712376",
}
ALL_831 = {**NEW, **MODIFIED}
OWNER_MODE = "100644"


def _read_git(*args: str) -> bytes:
    # Retain the original helper's mockable, bounded exact Git reader.
    return prior._git(*args)


def _sha(contents: bytes) -> str:
    return hashlib.sha256(prior._normal(contents)).hexdigest()


def _blob(contents: bytes) -> str:
    return prior._oid(contents)


def _disk(path: str) -> bytes:
    candidate = ROOT / path
    prior._reject_linked_parents(candidate)
    if candidate.is_symlink() or not candidate.is_file():
        raise AssertionError("Missing, linked or nonregular 8.31 source")
    return prior._normal(candidate.read_bytes())


def _no_unsafe_imports(path: str, data: bytes) -> None:
    try:
        tree = ast.parse(data.decode("utf-8", "strict"), filename=path)
    except (UnicodeError, SyntaxError):
        raise AssertionError("Invalid 8.31 Python syntax") from None
    prohibited = (
        "nayeon.brain", "nayeon.actions", "nayeon.providers",
        "nayeon.provider", "nayeon.credentials", "nayeon.credential",
        "nayeon.security", "nayeon.policy", "tests",
        "subprocess", "socket", "ctypes", "winreg",
    )
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        if any(name == bad or name.startswith(bad + ".")
               for bad in prohibited for name in names):
            raise AssertionError("Forbidden 8.31 source import")
    if path in NEW:
        allowed = {"__future__", "dataclasses", "enum", "unicodedata"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            if any(name not in allowed for name in names):
                raise AssertionError("Unknown pure session owner import")


def assert_831_integrity() -> None:
    if _read_git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported Git object format")
    head_ref = _read_git("rev-parse", "HEAD").decode("ascii").strip()
    if _read_git("branch", "--show-current").decode("utf-8").strip() != "nayeon-v1":
        raise AssertionError("Wrong production branch")
    _read_git("merge-base", "--is-ancestor", PARENT_831, head_ref)
    first_product = None
    maintenance_head = None
    docs_head = head_ref
    if head_ref != PARENT_831:
        # The FIRST product commit must directly descend from the sealed 8.30
        # documentation HEAD. Permit exactly ONE later docs-only reconciliation
        # commit, never an intervening product, merge or arbitrary descendant.
        current = _read_git("rev-list", "--parents", "-n", "1", head_ref
                            ).decode("ascii").split()
        if len(current) != 2 or current[0] != head_ref:
            raise AssertionError("8.31 wrong immediate product parent")
        if current[1] == DOC_COMMIT_831:
            # One reviewed TEST/LEDGER repair after immutable product/docs.
            maintenance_head = head_ref
            docs_head = DOC_COMMIT_831
            doc_parents = _read_git(
                "rev-list", "--parents", "-n", "1", docs_head
            ).decode("ascii").split()
            if doc_parents != [DOC_COMMIT_831, PRODUCT_COMMIT_831]:
                raise AssertionError("8.31 maintenance wrong docs parent")
            raw = _read_git("diff", "--no-renames", "--raw", "-z",
                            docs_head, maintenance_head)
            records = raw.split(b"\0")
            if records and records[-1] == b"":
                records.pop()
            if len(records) != 2 * len(MAINTENANCE_FILES):
                raise AssertionError("Unapproved 8.31 maintenance scope")
            seen_maintenance = set()
            for meta, path_bytes in zip(records[::2], records[1::2]):
                fields = meta.split()
                path = path_bytes.decode("utf-8", "strict")
                if (len(fields) != 5 or fields[0] != b":100644"
                        or fields[1] != b"100644" or fields[4] != b"M"
                        or path not in MAINTENANCE_FILES
                        or path in seen_maintenance):
                    raise AssertionError("Unapproved 8.31 maintenance scope")
                _read_git("cat-file", "-e", docs_head + ":" + path)
                _read_git("cat-file", "-e", maintenance_head + ":" + path)
                seen_maintenance.add(path)
            if seen_maintenance != MAINTENANCE_FILES:
                raise AssertionError("Incomplete 8.31 maintenance scope")
            current = doc_parents
        if current[1] == PARENT_831:
            first_product = docs_head
        else:
            first_product = current[1]
            # Refuse unrelated descendants BEFORE consulting their document
            # delta or any potentially forged production inventory.
            first_parents = _read_git(
                "rev-list", "--parents", "-n", "1", first_product
            ).decode("ascii").split()
            if (len(first_parents) != 2 or first_parents[0] != first_product
                    or first_parents[1] != PARENT_831):
                raise AssertionError("8.31 wrong immediate product parent")
            allowed_documentation = {
                ".codex/CURRENT_STATE.md",
                "docs/phase_8_31_offline_conversation_session_rfc.md",
                "docs/phase_8_31_offline_conversation_session_review.md",
                "docs/pre_829_shutdown_ownership_failure_ledger.md",
            }
            raw = _read_git("diff", "--no-renames", "--name-only", "-z", first_product, docs_head)
            changed = [name.decode("utf-8", "strict")
                       for name in raw.split(b"\0") if name]
            if (not changed or len(changed) != len(set(changed))
                    or not set(changed) <= allowed_documentation):
                raise AssertionError("Unapproved 8.31 documentation-only descendant")
            for filename in changed:
                # Historical evidence must not disappear in a doc-only seal.
                _read_git("cat-file", "-e", docs_head + ":" + filename)
            # The exact previously reviewed production tree is retained.
            if prior._tree(first_product) != prior._tree(docs_head):
                raise AssertionError("Documentation descendant modified production")
            if maintenance_head is not None and prior._tree(docs_head) != prior._tree(maintenance_head):
                raise AssertionError("Maintenance descendant modified production")
        parents = _read_git("rev-list", "--parents", "-n", "1", first_product
                            ).decode("ascii").split()
        if (len(parents) != 2 or parents[0] != first_product
                or parents[1] != PARENT_831):
            raise AssertionError("8.31 wrong immediate product parent")
    # Preserve chronological frozen source trees from 8.29 to 8.30:
    base = prior._tree(prior.PROTECTED)
    sealed = prior._tree(PRODUCT_830)
    if set(sealed) != set(base) | set(prior.APPROVED_NEW_SHA256):
        raise AssertionError("Missing or unapproved committed 8.30 source")
    for path, ref in base.items():
        if path not in prior.APPROVED_MODIFIED_SHA256 and sealed.get(path) != ref:
            raise AssertionError("Frozen historical 8.29 source changed")
    # The original exact 8.30 blobs and published SHA pins remain immutable
    # even though two UI working-tree files now carry reviewed 8.31 hashes.
    for path, expected in prior.APPROVED_SOURCE_SHA256.items():
        if path not in sealed or sealed[path][0] != OWNER_MODE:
            raise AssertionError("Missing or unapproved committed 8.30 source")
        content = _read_git("show", PRODUCT_830 + ":" + path)
        if _sha(content) != expected:
            raise AssertionError("Unapproved 8.30 source bytes")
        if sealed[path][1] != _blob(content):
            raise AssertionError("Missing or unapproved committed 8.30 source")

    # Enumerate complete HEAD and index before filtering, so Windows aliases
    # cannot hide behind Git pathspec and stale index/committed blobs fail.
    head = prior._tree(head_ref)
    index = prior._index()
    precommit = head_ref == PARENT_831
    expected_paths = set(sealed) | set(NEW)
    if set(head) != (set(sealed) if precommit else expected_paths):
        raise AssertionError("Unauthorized committed production inventory")
    if set(index) - set(sealed) - set(NEW) or set(sealed) - set(index):
        raise AssertionError("Unauthorized staged production inventory")

    accepted_831 = {path: (OWNER_MODE, _blob(_disk(path))) for path in ALL_831}
    for path in ALL_831:
        content = _disk(path)
        if _sha(content) != ALL_831[path]:
            raise AssertionError("Unapproved 8.31 source bytes")
        _no_unsafe_imports(path, content)

    # Preparation permits ALL three old index blobs; staging permits ONLY
    # the complete three-file reviewed manifest, never a partial hybrid.
    if precommit:
        modified_staged = {path for path in MODIFIED
                           if index.get(path) != sealed[path]}
        new_staged = set(NEW) & set(index)
        if modified_staged or new_staged:
            if (modified_staged != set(MODIFIED) or new_staged != set(NEW)
                    or any(index.get(path) != accepted_831[path] for path in ALL_831)):
                raise AssertionError("Partial 8.31 staged production snapshot refused")
    # First validate frozen HEAD/index modes and bytes, including the original
    # 8.30 profile owner, presentation view, entrypoint and 8.29 source.
    for path, sealed_ref in sealed.items():
        head_ref_entry = head.get(path)
        index_ref_entry = index.get(path)
        if path in MODIFIED:
            approved = accepted_831[path]
            if precommit:
                if head_ref_entry != sealed_ref:
                    raise AssertionError("Missing or unapproved committed 8.30 source")
                if index_ref_entry not in (sealed_ref, approved):
                    raise AssertionError("Unapproved staged 8.30 source")
            elif head_ref_entry != approved or index_ref_entry != approved:
                raise AssertionError("8.31 staged/committed rollback refused")
        else:
            if head_ref_entry != sealed_ref or index_ref_entry != sealed_ref:
                if path == "nayeon/desktop_alpha/window.py":
                    raise AssertionError("Postcommit entrypoint rollback refused")
                raise AssertionError("Frozen committed or staged production modified")
            if _blob(_disk(path)) != sealed_ref[1]:
                raise AssertionError("Frozen production worktree bytes modified")

    for path in NEW:
        approved = accepted_831[path]
        if precommit:
            if path in head:
                raise AssertionError("Unauthorized precommit 8.31 source")
            if path in index and index[path] != approved:
                raise AssertionError("Unapproved staged 8.31 source")
        elif head.get(path) != approved or index.get(path) != approved:
            raise AssertionError("8.31 new-source committed/index rollback refused")

    actual_python = set()
    prior._reject_linked_parents(ROOT / "nayeon" / "_phase_831_guard.py")
    for candidate in (ROOT / "nayeon").rglob("*.py"):
        prior._reject_linked_parents(candidate)
        relative = candidate.relative_to(ROOT).as_posix()
        if candidate.is_symlink() or not candidate.is_file():
            raise AssertionError("Invalid or linked production source")
        actual_python.add(relative)
    expected_python = {path for path in sealed if path.endswith(".py")} | set(NEW)
    if actual_python != expected_python:
        raise AssertionError("Missing or unexpected production Python source")
    untracked = _read_git("ls-files", "--others", "--exclude-standard", "-z")
    for raw in untracked.split(b"\0"):
        if raw:
            relative = raw.decode("utf-8", "strict")
            if prior._production_git_path(relative) and relative not in NEW:
                raise AssertionError("Unauthorized untracked production source")
    # Keep the exact sealed old config import interface checks.
    # Those consumers are preserved and do not gain a provider/credential route.
