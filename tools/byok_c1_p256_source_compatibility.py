"""P256 current-version source diagnostic. Every result blocks acceptance.

Windows CPython 3.12, isolated and bytecode-disabled invocation required:
python -I -B tools/byok_c1_p256_source_compatibility.py
Only the exact uncommitted P256 checkout at the authorized P255 base is admitted.
"""

from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import types


ROOT = Path(__file__).absolute().parents[1]
INTENDED_ROOT = Path(r"D:\Nayeon\CODEX_P256_PACKAGE_EFFECT_EXCLUSION_20261116")
BRANCH = "refs/heads/byok-c1-p256-package-effect-exclusion-20261116"
BASE = "a459bbec668c314819041de3fdc2e5d7c1914f6d"
PARENT = "4e2a605f6e8a7b079c9430dbf18461c2b2795a77"
TREE = "f2f05eb455148d85ad27c13e9798eb8377ef8731"
P251_COMMIT = "6e2717f13da253fddbb3c9cbcfdf55e124d6f8ac"
COMMON_DIR = Path(r"D:\Nayeon\P243_FULL_HISTORY_G1_20261115\.git")
GIT_DIR = COMMON_DIR / "worktrees/CODEX_P256_PACKAGE_EFFECT_EXCLUSION_20261116"
GIT = Path(r"C:\Program Files\Git\cmd\git.exe")
HELPER_PINS = {
    "tools/byok_c1_effect_exposure_gate.py":
        "990117324c727662d2909c96b73c135c7278baf69c242f312bdf24782d96330b",
    "tools/byok_c1_p255_effect_boundary.py":
        "f5701e051d1f6c35e5d2261060f2aa1c8f0a3f86dcc92754fe33847f6fec320d",
}
ADDITIONS = (
    "tools/byok_c1_p256_source_compatibility.py",
    "tests/test_byok_c1_p256_source_compatibility.py",
    "docs/byok-c1-p256-current-source-compatibility.md",
)
BLOCKED_EXIT = 3
LIMITATIONS = (
    "Source diagnostic only. Effect-owner exclusivity and production-package exclusion remain unproved.",
    "Trusted Windows interpreter, stdlib, Git executable and local Git administration are prerequisites.",
    "A quiescent checkout is required. Repeated sampling cannot exclude hostile replacement races or ABA changes.",
    "Exact draft topology only. Staging, child commits, relocation and alternate Git administration require separately reviewed versioning.",
    "Git object identity and raw hashes supply no signing-owner decision, authenticated provenance or OS isolation.",
    "Original P251 CLI contract remains separately unmatched. Original P76 failures and P96 remain OPEN.",
)


class Refusal(ValueError):
    """A bounded reason safe for machine-readable output."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise Refusal(reason)


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def _plain_path(path: Path) -> None:
    for component in reversed((path, *path.parents)):
        info = component.lstat()
        _require(not stat.S_ISLNK(info.st_mode)
                 and not getattr(info, "st_file_attributes", 0) & 0x400,
                 "symlink_or_reparse_path")


def _read(path: Path) -> bytes:
    _plain_path(path)
    info = path.lstat()
    _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "nonregular_or_hardlinked_file")
    _require(info.st_size <= 1_000_000, "oversized_file")
    with path.open("rb") as source:
        raw = source.read(1_000_001)
    _require(len(raw) <= 1_000_000, "oversized_file")
    return raw


def _runtime_issues() -> list[dict]:
    issues = []
    if os.name != "nt" or sys.version_info[:2] != (3, 12):
        issues.append({"reason": "requires_windows_cpython_312"})
    if sys.implementation.name != "cpython" or not sys.flags.isolated or not sys.dont_write_bytecode:
        issues.append({"reason": "requires_isolated_bytecode_disabled_interpreter"})
    if any(name.upper().startswith("GIT_") or name.upper() in (
        "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT",
    ) for name in os.environ):
        issues.append({"reason": "unsafe_environment_override"})
    return issues


def _git(root: Path, *args: str) -> bytes:
    # Fixed executable, argv-only, local read commands. Disable lazy fetching,
    # replacement objects, fsmonitor execution and optional index writes.
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith("GIT_")}
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
    })
    result = subprocess.run(
        [str(GIT), "--no-replace-objects", "-c", "core.fsmonitor=false",
         "-c", "core.untrackedCache=false", "-C", str(root), *args],
        env=environment, capture_output=True, timeout=30, check=False,
    )
    _require(result.returncode == 0, "git_command_failed")
    _require(len(result.stdout) <= 4_000_000, "oversized_git_reply")
    return result.stdout


def _line(root: Path, *args: str) -> str:
    raw = _git(root, *args)
    _require(raw.endswith(b"\n") and raw.count(b"\n") == 1 and b"\0" not in raw,
             "ambiguous_git_reply")
    return raw[:-1].decode("utf-8", errors="strict")


def _inventory(raw: bytes, *, index: bool) -> dict[str, tuple[str, str]]:
    _require(bool(raw) and raw.endswith(b"\0"), "incomplete_git_inventory")
    records = {}
    folded = set()
    for item in raw[:-1].split(b"\0"):
        header, name = item.split(b"\t", 1)
        path = name.decode("utf-8", errors="strict")
        parts = PurePosixPath(path).parts
        _require(bool(parts) and "/".join(parts) == path and not path.startswith("/")
                 and all(part not in (".", "..") and ":" not in part
                         and "\\" not in part and not part.endswith((".", " "))
                         for part in parts), "unsafe_inventory_path")
        mode, middle, last = header.decode("ascii").split(" ")
        kind, oid = (last, middle) if index else (middle, last)
        _require(mode == "100644" and kind == ("0" if index else "blob")
                 and len(oid) == 40 and all(char in "0123456789abcdef" for char in oid),
                 "unsupported_git_entry")
        _require(path.casefold() not in folded, "duplicate_or_aliased_git_path")
        folded.add(path.casefold())
        records[path] = (mode, oid)
    return records


def _snapshot(root: Path) -> dict:
    _require(_same_path(root, INTENDED_ROOT), "unintended_repository_root")
    _plain_path(root)
    _plain_path(GIT_DIR)
    _plain_path(COMMON_DIR)
    pointer = _read(root / ".git").decode("utf-8").splitlines()
    _require(len(pointer) == 1 and pointer[0].startswith("gitdir: ")
             and _same_path(Path(pointer[0][8:]), GIT_DIR), "worktree_pointer_mismatch")
    _require(_same_path(Path(_read(GIT_DIR / "gitdir").decode("utf-8").strip()), root / ".git"),
             "worktree_backpointer_mismatch")
    common = _read(GIT_DIR / "commondir").decode("utf-8").strip()
    _require(_same_path(GIT_DIR / common, COMMON_DIR), "common_directory_mismatch")
    _require(_read(GIT_DIR / "HEAD") == ("ref: " + BRANCH + "\n").encode("ascii"),
             "worktree_head_mismatch")
    for arguments, expected in (
        (("symbolic-ref", "-q", "HEAD"), BRANCH),
        (("show-ref", "--verify", "--hash", BRANCH), BASE),
        (("rev-parse", "--verify", "HEAD^{commit}"), BASE),
        (("rev-parse", "--verify", "HEAD^{tree}"), TREE),
        (("rev-list", "--parents", "-n", "1", "HEAD"), BASE + " " + PARENT),
        (("rev-parse", "--is-shallow-repository"), "false"),
        (("rev-parse", "--show-object-format"), "sha1"),
    ):
        _require(_line(root, *arguments) == expected, "git_identity_or_ancestry_mismatch")
    for arguments, expected in (
        (("rev-parse", "--show-toplevel"), root),
        (("rev-parse", "--absolute-git-dir"), GIT_DIR),
        (("rev-parse", "--path-format=absolute", "--git-common-dir"), COMMON_DIR),
    ):
        _require(_same_path(Path(_line(root, *arguments)), expected), "git_source_root_mismatch")
    _require(not _git(root, "for-each-ref", "--format=%(refname)", "refs/replace/"),
             "replacement_refs_present")
    _require(not (COMMON_DIR / "info/grafts").exists(), "grafts_present")
    _git(root, "merge-base", "--is-ancestor", P251_COMMIT, BASE)
    worktrees = _git(root, "worktree", "list", "--porcelain", "-z").split(b"\0\0")
    registrations = [entry.split(b"\0") for entry in worktrees if entry]
    matches = [entry for entry in registrations if entry and entry[0].startswith(b"worktree ")
               and _same_path(Path(entry[0][9:].decode("utf-8")), root)]
    _require(len(matches) == 1 and matches[0] == [
        b"worktree " + str(root).replace("\\", "/").encode("utf-8"),
        b"HEAD " + BASE.encode("ascii"), b"branch " + BRANCH.encode("ascii"),
    ], "worktree_registration_mismatch")
    tree = _inventory(_git(root, "ls-tree", "-r", "-z", BASE), index=False)
    index = _inventory(_git(root, "ls-files", "--stage", "-z"), index=True)
    _require(index == tree, "index_tree_mismatch")
    # Do not trust status, assume-unchanged, skip-worktree, or clean filters.
    disk = hashlib.sha256()
    helpers = {}
    for relative, (_, expected) in sorted(tree.items()):
        raw = _read(root / relative)
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        _require(oid == expected, "tracked_disk_blob_mismatch")
        digest = hashlib.sha256(raw).hexdigest()
        disk.update(relative.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
        if relative in HELPER_PINS:
            _require(digest == HELPER_PINS[relative], "diagnostic_helper_pin_drift")
            helpers[relative] = raw
    _require(set(helpers) == set(HELPER_PINS), "missing_diagnostic_helper")
    # No exclude rules are supplied, so ignored files are included too.
    # ls-files avoids status/diff clean filters and external diff programs.
    untracked = _git(root, "ls-files", "--others", "-z")
    _require(untracked.endswith(b"\0"), "unexpected_untracked_files")
    _require(set(untracked[:-1].split(b"\0")) == {name.encode("ascii") for name in ADDITIONS}
             and len(untracked[:-1].split(b"\0")) == len(ADDITIONS), "unexpected_untracked_files")
    additions = {name: hashlib.sha256(_read(root / name)).hexdigest() for name in ADDITIONS}
    return {
        "root": str(root), "git_dir": str(GIT_DIR), "common_dir": str(COMMON_DIR),
        "branch": BRANCH, "head": BASE, "parent": PARENT, "tree": TREE,
        "p251_ancestor": P251_COMMIT, "tracked_file_count": len(tree),
        "raw_tracked_manifest_sha256": disk.hexdigest(), "additions_sha256": additions,
        "helpers": helpers,
    }


def _source_report(root: Path, helpers: dict[str, bytes]) -> dict:
    """Execute only the two verified diagnostic snapshots, never product code.

    Bind P255's single project import to the verified P251 module locally.
    Neither sys.path nor sys.modules is changed, including during unit discovery.
    """
    _require(set(helpers) == set(HELPER_PINS), "invalid_verified_helper_snapshot")
    for relative, expected in HELPER_PINS.items():
        _require(hashlib.sha256(helpers[relative]).hexdigest() == expected,
                 "invalid_verified_helper_snapshot")
    p251_path, p255_path = HELPER_PINS
    p251 = types.ModuleType("p256_verified_p251")
    p251.__file__ = str(root / p251_path)
    exec(compile(helpers[p251_path], p251.__file__, "exec"), p251.__dict__)
    package = types.ModuleType("tools")
    package.byok_c1_effect_exposure_gate = p251

    def diagnostic_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "tools" and fromlist == ("byok_c1_effect_exposure_gate",) and level == 0:
            return package
        return builtins.__import__(name, globals, locals, fromlist, level)

    p255 = types.ModuleType("p256_verified_p255")
    p255.__file__ = str(root / p255_path)
    p255.__dict__["__builtins__"] = dict(vars(builtins), __import__=diagnostic_import)
    exec(compile(helpers[p255_path], p255.__file__, "exec"), p255.__dict__)
    return p255.assess(root)


def assess(root: Path) -> dict:
    """Internal synthetic seam. The CLI has no root or admission override."""
    report = {
        "schema": "byok-c1-p256-v1", "status": "BLOCKED", "assessment": "UNKNOWN",
        "source_context_admitted": False, "release_admitted": False, "real_key_admitted": False,
        "independently_approved": False, "effect_owner_exclusivity": "NOT_ESTABLISHED",
        "source_context": {}, "sources": [], "evidence": [], "routes": [],
        "original_p251_contract": "SEPARATE_UNMATCHED_HISTORICAL_ROOT",
        "issues": _runtime_issues(), "limitations": list(LIMITATIONS),
    }
    if report["issues"]:
        return report
    try:
        before = _snapshot(root)
        observed = _source_report(root, before["helpers"])
        after = _snapshot(root)
        _require(before == after, "source_context_changed_during_assessment")
        report["source_context"] = {key: value for key, value in before.items() if key != "helpers"}
        for field in ("sources", "evidence", "routes"):
            report[field] = observed[field]
        report["limitations"].extend(observed["limitations"])
        report["issues"].extend(observed["issues"])
        _require(observed["assessment"] == "OPEN" and not observed["issues"],
                 "unresolved_p251_p255_source_evidence")
        report["source_context_admitted"] = True
        report["assessment"] = "OPEN"
    except Refusal as error:
        report["issues"].append({"reason": str(error)})
    except (OSError, ValueError, SyntaxError, RecursionError, subprocess.SubprocessError) as error:
        report["issues"].append({"reason": type(error).__name__})
    return report


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(assess(ROOT), indent=2, sort_keys=True))
    return BLOCKED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
