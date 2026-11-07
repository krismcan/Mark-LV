"""P90 offline, review-only source snapshot gate. NO C1 production GO.

The expected P90 head must come from an external, reviewer-pinned GitHub SHA.
This deliberately does not modify, import, weaken, or impersonate the P85 gate.
A passing result authenticates only a specific clean Git checkout snapshot,
NOT secure credential custody, consent, independent review, or release authority.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess

BRANCH = "byok-c1-p90-review-source-admission-20261107"
P88 = "b3f2a7570abe147696eda3650e5706d8d7fa1ec4"
P88_TREE = "cf6cde6491f30572f50ad3d4ba424eea2740d183"
CHAIN = (
    ("24da07345c67566d2e79f442aabfba36a1ebddb4",
     "cacb5c320d26ffa28faf1f15a5e088029ee1453b"),
    ("c53b761ea4329ef395a0126097a5949d9a9947a5",
     "24da07345c67566d2e79f442aabfba36a1ebddb4"),
    ("ad1b635e4c56c3a7eb939b3dc7e5059095f0e06a",
     "c53b761ea4329ef395a0126097a5949d9a9947a5"),
    ("ff1e6ad30a21fc0912b3f13fb1a10e2f873ef980",
     "ad1b635e4c56c3a7eb939b3dc7e5059095f0e06a"),
    ("0d44b53ade8a2e97e10b7568a7d25d099152e416",
     "ff1e6ad30a21fc0912b3f13fb1a10e2f873ef980"),
    (P88, "0d44b53ade8a2e97e10b7568a7d25d099152e416"),
)
ADDED = frozenset({
    ".github/workflows/p90-review-source-admission.yml",
    "tests/p90_review_source_admission.py",
    "tests/test_p90_review_source_admission.py",
})
HASH = re.compile(r"[a-f0-9]{40}\Z")


class ReviewHold(AssertionError):
    """Fail closed; do not mistake source inventory for release approval."""


def demand(condition: bool, why: str) -> None:
    if not condition:
        raise ReviewHold(why)


def git(root: pathlib.Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
    )
    if result.returncode != 0:
        raise ReviewHold("Git source-proof operation failed: " + args[0])
    return result.stdout


def txt(root: pathlib.Path, *args: str) -> str:
    return git(root, *args).decode("utf-8", "strict").strip()


def tree(root: pathlib.Path, commit: str) -> dict[str, tuple[str, str, str]]:
    records: dict[str, tuple[str, str, str]] = {}
    for item in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
        if not item:
            continue
        metadata, rawpath = item.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        path = rawpath.decode("utf-8", "strict")
        demand(path not in records, "duplicate tree path")
        records[path] = mode, kind, oid
    return records


def index(root: pathlib.Path) -> dict[str, tuple[str, str, str]]:
    records = {}
    for item in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not item:
            continue
        metadata, rawpath = item.split(b"\t", 1)
        mode, oid, stage = metadata.decode("ascii").split()
        path = rawpath.decode("utf-8", "strict")
        demand(path not in records and stage == "0", "unmerged index or path collision")
        records[path] = (mode, "blob", oid)
    return records


def snapshot(root: pathlib.Path, expected_head: str) -> tuple:
    # Head is provided by the external reviewer / GitHub workflow, not chosen
    # from the local working tree to obtain an automatic PASS.
    demand(bool(HASH.fullmatch(expected_head)), "missing or invalid external SHA pin")
    demand(root.is_dir(), "review checkout missing")
    top = txt(root, "rev-parse", "--show-toplevel")
    demand(pathlib.Path(top).resolve() == root.resolve(), "wrong worktree root")
    demand(txt(root, "branch", "--show-current") == BRANCH, "unreviewed branch")
    demand(txt(root, "rev-parse", "HEAD") == expected_head, "HEAD differs from external pin")
    demand(txt(root, "rev-list", "--parents", "-n", "1", "HEAD") ==
           expected_head + " " + P88, "not exact one-parent P88 child")
    demand(txt(root, "rev-parse", P88 + "^{tree}") == P88_TREE,
           "P88 parent tree differs from reviewed baseline")
    for child, parent in CHAIN:
        demand(txt(root, "rev-list", "--parents", "-n", "1", child) ==
               child + " " + parent, "reviewed ancestor chain changed")
    original = tree(root, P88)
    candidate = tree(root, "HEAD")
    demand(set(candidate) - set(original) == ADDED, "unapproved source addition")
    demand(not set(original) - set(candidate), "historical file removed")
    demand(all(candidate[path] == record for path, record in original.items()),
           "historical source changed or deleted")
    demand(all(candidate[path][0:2] == ("100644", "blob") for path in ADDED),
           "P90 source type/mode differs")
    demand(sorted(txt(root, "diff-tree", "--no-commit-id", "--name-only",
                      "--no-renames", "-r", "HEAD").splitlines()) == sorted(ADDED),
           "P90 changed path scope mismatch")
    demand(index(root) == candidate, "Git index differs from committed source")
    demand(not git(root, "status", "--porcelain=v1", "--untracked-files=all"),
           "dirty/untracked source checkout")
    # Disk-hash all review additions against their exact Git blob IDs.
    # All other tracked file bytes are checked by Git's full-worktree status.
    for path in ADDED:
        digest = txt(root, "hash-object", "--", path)
        demand(digest == candidate[path][2], "live review file differs from Git blob")
    # An immutable readout, not a successful source-authority admission ticket.
    return (
        txt(root, "rev-parse", "HEAD"),
        txt(root, "rev-parse", "HEAD^{tree}"),
        tuple(sorted(candidate.items())),
        tuple(sorted(index(root).items())),
        git(root, "status", "--porcelain=v1", "--untracked-files=all"),
    )


def assert_review_source_snapshot(root: pathlib.Path, expected_head: str) -> str:
    first = snapshot(pathlib.Path(root), expected_head)
    second = snapshot(pathlib.Path(root), expected_head)
    demand(first == second, "source/ref/index changed during review")
    return "EXACT_REVIEW_SNAPSHOT_ONLY__PRODUCTION_HOLD"


def main() -> None:
    parser = argparse.ArgumentParser(description="P90 read-only source review (HOLD)")
    parser.add_argument("--worktree", required=True, type=pathlib.Path)
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    result = assert_review_source_snapshot(args.worktree, args.expected_head)
    print("P90_SOURCE_REVIEW=" + result)
    print("P90_INDEPENDENT_SECURITY_GO=NOT_RECEIVED")
    print("P90_NATIVE_CUSTODY=NOT_OBSERVED")
    print("P90_C1_PRODUCTION_RELEASE=HOLD")


if __name__ == "__main__":
    main()
