"""P166 diagnostic H/C/R source custody. No credential, launch or release capability."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess

from scripts.p153_windows_current_branch_security_candidate import (
    ORIGINALS, PINNED_ORIGINAL_P76_BRANCH, P140_PIN_DEFAULTS,
    _top_level_constants,
)
from scripts.p165_windows_versioned_security_review_submission import (
    EXPECTED_MODULE_COUNT, HISTORICAL_TWO_BRANCH_POSITIVES,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "bafb9760dbadb75de323f6739efd07ea945eab5b"
BRANCH = "byok-c1-p166-current-branch-positive-negative-acceptance-20261112"
P166_PATHS = frozenset({
    "scripts/p166_windows_current_branch_acceptance.py",
    "tests/test_p166_current_branch_acceptance.py",
    "docs/byok-c1-p166-versioned-current-branch-acceptance.md",
    ".github/workflows/p166-windows-current-branch-acceptance.yml",
})
EXTRA_PROTECTED = (
    "tests/phase_8_30_scope_migration.py",
    "tests/phase_8_32_scope_migration.py",
    "tests/phase_8_34_scope_migration.py",
    "tests/phase_8_36_scope_migration.py",
    "tests/phase_8_37_scope_migration.py",
    "tests/test_phase_837_scope_integrity.py",
    "scripts/p161_windows_historical_git_call_profile.py",
    "scripts/p162_windows_immutable_git_batch_candidate.py",
    "scripts/p163_windows_security_review_readiness.py",
    "scripts/p164_windows_bounded_immutable_reader_design.py",
)
PROTECTED = tuple(sorted(set(ORIGINALS + EXTRA_PROTECTED)))
HIST_TAG = "nayeon-v1-phase-10-3-synthetic-provenance-redaction-01"
HIST_TAG_OID = "ed68953eaacee301592c6349a590a17be9638be5"
HIST_TAG_COMMIT = "cacb5c320d26ffa28faf1f15a5e088029ee1453b"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class P166Refused(AssertionError):
    """Fail closed; source candidate is never an admission or consent token."""


def deny(why: str) -> None:
    raise P166Refused("P166 current-branch source refused: " + why)


def git(*args: str) -> bytes:
    # Only fixed, reviewer-defined Git argv; no shell and no provider execution.
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=25,
    )
    if result.returncode:
        deny("Git provenance operation failed")
    return result.stdout


def hex_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _ordinary_repo_file(rel: str) -> Path:
    """Reject absolute paths, aliases, traversal, symlinks and reparse nodes."""
    if (type(rel) is not str or not rel or "\\" in rel
            or rel.startswith(("/", ".")) or ":" in rel
            or "//" in rel or any(p in ("", ".", "..") for p in rel.split("/"))):
        deny("untrusted source path or alias")
    if rel not in PROTECTED:
        deny("path not in versioned protected source manifest")
    dest = ROOT
    for component in rel.split("/"):
        dest = dest / component
        try:
            meta = dest.lstat()
        except (OSError, ValueError):
            deny("missing source path")
        if dest.is_symlink() or (getattr(meta, "st_file_attributes", 0) & 0x400):
            deny("reparse or linked source path")
    if not stat.S_ISREG(dest.lstat().st_mode):
        deny("non-regular source file")
    return dest


def verify_historical_tag(expected_oid: str = HIST_TAG_OID) -> str:
    if expected_oid != HIST_TAG_OID:
        deny("substituted historical tag object pin")
    oid = git("show-ref", "--verify", "--hash", "--", "refs/tags/" + HIST_TAG).decode().strip()
    if oid != HIST_TAG_OID or git("cat-file", "-t", oid) != b"tag\n":
        deny("wrong historical annotated tag ref")
    if git("rev-parse", "--verify", "--end-of-options", oid + "^{}").decode().strip() != HIST_TAG_COMMIT:
        deny("wrong historical tag target")
    raw = git("cat-file", "tag", oid)
    if raw.split(b"\n")[:3] != [
        ("object " + HIST_TAG_COMMIT).encode(), b"type commit",
        ("tag " + HIST_TAG).encode()
    ]:
        deny("tag body or reference substitution")
    return oid


def verify_current_source(*, expected_branch: str, expected_head: str,
                          expected_ancestor: str = BASE,
                          expected_tag_oid: str = HIST_TAG_OID,
                          digest_override: dict[str, str] | None = None,
                          requested_paths: tuple[str, ...] = ()) -> dict:
    """Real current Windows checkout; no fake-success fixtures and no side effects."""
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Windows":
        deny("real hosted Windows runner required")
    if os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV" or os.environ.get("GITHUB_EVENT_NAME") != "push":
        deny("unexpected repository or event")
    if (not HEX40.fullmatch(expected_head or "")
            or expected_branch != BRANCH
            or expected_ancestor != BASE
            or expected_head != os.environ.get("GITHUB_SHA")):
        deny("wrong signed event, branch or exact P165 ancestry expectation")
    if (os.environ.get("GITHUB_REF_NAME") != expected_branch or
            git("branch", "--show-current").decode().strip() != expected_branch or
            git("rev-parse", "HEAD").decode().strip() != expected_head):
        deny("live branch or head mismatch")
    if git("merge-base", BASE, "HEAD").decode().strip() != BASE:
        deny("P165 source ancestor mismatch")
    if git("status", "--porcelain=v1"):
        deny("dirty source/index/untracked checkout")
    changes = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changes != P166_PATHS:
        deny("P166 non-additive or missing path inventory")
    for p in changes:
        if git("cat-file", "-e", BASE + ":" + p) == b"":  # git exit status proves absence only if command succeeded
            deny("P166 path unexpectedly present in P165 base")
    verify_historical_tag(expected_tag_oid)
    baseline_modules = [p for p in git("ls-tree", "-r", "--name-only", BASE, "--", "tests").decode().splitlines()
                        if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    current_modules = [p for p in git("ls-files", "tests/test_*.py").decode().splitlines()
                       if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    if (len(baseline_modules) != EXPECTED_MODULE_COUNT
            or len(current_modules) != EXPECTED_MODULE_COUNT + 1
            or set(current_modules) - set(baseline_modules) != {"tests/test_p166_current_branch_acceptance.py"}):
        deny("170 original test modules were modified or removed")
    if _top_level_constants(ROOT / "tests/phase8_byok_c1_p76_scope.py", {"BRANCH"}) != {
            "BRANCH": PINNED_ORIGINAL_P76_BRANCH}:
        deny("P76 historical wrong-branch pin modified")
    if _top_level_constants(ROOT / "nayeon/desktop_alpha/frozen_signed_byok_companion.py",
                            set(P140_PIN_DEFAULTS)) != P140_PIN_DEFAULTS:
        deny("P140 approved binaries or code integrity state changed")
    custody = []
    override = digest_override or {}
    if set(override) - set(PROTECTED):
        deny("unreviewed digest manifest path")
    for rel in PROTECTED:
        source = _ordinary_repo_file(rel).read_bytes()
        original = git("show", BASE + ":" + rel)
        current = git("show", "HEAD:" + rel)
        expected = override.get(rel, hex_sha256(original))
        if (source != original or current != original
                or hex_sha256(source) != expected
                or git("rev-parse", "HEAD:" + rel) != git("rev-parse", BASE + ":" + rel)):
            deny("source manifest, index or immutable Git object differs: " + rel)
        custody.append({"path": rel, "sha256": hex_sha256(source), "bytes": len(source)})
    for rel in requested_paths:
        _ordinary_repo_file(rel)
    if git("rev-parse", "HEAD").decode().strip() != expected_head or git("status", "--porcelain=v1"):
        deny("source changed during current-branch acceptance")
    return {
        "head": expected_head, "branch": expected_branch, "ancestor": BASE,
        "historical_annotated_tag_object": HIST_TAG_OID,
        "original_security_files_byte_preserved": custody,
        "original_test_modules": EXPECTED_MODULE_COUNT,
        "historical_original_positive_failures_unwaived": list(HISTORICAL_TWO_BRANCH_POSITIVES),
        "is_real_current_branch_git_checkout": True,
        "is_production_release_authorization": False,
    }
