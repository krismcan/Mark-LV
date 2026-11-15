"""P245 read-only current-source diagnostic; never an effect or release authority.

Original P76 and historical test outcomes remain unchanged and unwaived.
This diagnostic does not replace historical admission or approve current production.
"""
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "da9c436a177b3ec68db0eff2b610180b745bfb2b"
HISTORICAL = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
BRANCH = "byok-c1-p245-p76-current-source-20261115"
HISTORICAL_P76_BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
TAG = "nayeon-v1-phase-10-3-synthetic-provenance-redaction-01"
TAG_OID = "ed68953eaacee301592c6349a590a17be9638be5"
TAG_TARGET = "cacb5c320d26ffa28faf1f15a5e088029ee1453b"
ADDED = frozenset({
    "scripts/p245_p76_current_source.py",
    "tests/test_p245_p76_current_source.py",
    ".github/workflows/p245-p76-current-source.yml",
    "docs/byok-c1-p245-p76-current-source.md",
})
FROZEN = {
    "tests/phase8_byok_c1_p76_scope.py": "1C42912D9FC550DEA56C9BA9BB70D9568F298223B5514AF8D03C1723AAAD3327",
    "tests/test_phase8_byok_b_scope_integrity.py": "65DAD89298A587D6BB5DDE5455DF4D701BB1A1FD9A7A96CECF3E647800E3AE8B",
    "tests/test_phase_834_scope_integrity.py": "8DC69EC770EA008DFF9CD13E15299A73E38044F1671FD4FE78FBE2A431CCF57A",
    "tests/phase10_3_scope_migration.py": "540A1BE7C6FF23929B17E8A2F8272083829A65C35A76D1755A5284C958AFBEFF",
    "tests/phase8_byok_b_scope_migration.py": "84CED2F31F5DAF985DE462C384ABDFE47F8B705425F8BDEFB8CF1E04E56EE010",
    "tests/phase_8_34_scope_migration.py": "59442121254B42949640161FB7DBD47E90F3E77E6045F258A1DA130B640C8D43",
}
ORIGINAL_FAILURE_IDS = (
    "tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay",
    "tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected",
    "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission",
    "tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route",
)
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class CurrentSourceRefused(AssertionError):
    """Non-privileged diagnostic refusal; never returns an admission token."""


def refuse(reason: str) -> None:
    raise CurrentSourceRefused("P245 current-source diagnostic refused: " + reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in tuple(env):
        if (key in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_CONFIG",
                    "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL", "GIT_REPLACE_REF_BASE"}
                or key.startswith(("GIT_CONFIG_", "P134_"))):
            env.pop(key, None)
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env


def git(*args: str) -> bytes:
    try:
        child = subprocess.run(
            ["git", "-C", str(ROOT), *args], shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=35, check=False, env=environment()
        )
    except (OSError, subprocess.TimeoutExpired):
        refuse("immutable Git operation unavailable")
    if child.returncode != 0:
        refuse("immutable Git operation failed")
    return child.stdout


def source_file(rel: str) -> Path:
    """Reject traversal, noncanonical path, link and Windows reparse aliases."""
    if rel not in FROZEN and rel not in ADDED:
        refuse("unapproved source path")
    if (not re.fullmatch(r"[A-Za-z0-9_./-]+", rel) or
            rel.startswith("/") or (rel.startswith(".") and not rel.startswith(".github/workflows/")) or
            "//" in rel or
            any(s in ("", ".", "..") for s in rel.split("/"))):
        refuse("noncanonical source path")
    node = ROOT
    for part in rel.split("/"):
        node = node / part
        try:
            meta = node.lstat()
        except OSError:
            refuse("source path missing")
        if node.is_symlink() or getattr(meta, "st_file_attributes", 0) & 0x400:
            refuse("linked or reparse source path")
    if not stat.S_ISREG(node.lstat().st_mode):
        refuse("nonregular source")
    return node


def historical_branch_literal(raw: bytes) -> str:
    """Read AST literal only; never execute an archived source module."""
    nodes = ast.parse(raw).body
    matches = [node.value.value for node in nodes
               if isinstance(node, ast.Assign) and len(node.targets) == 1
               and isinstance(node.targets[0], ast.Name)
               and node.targets[0].id == "BRANCH"
               and isinstance(node.value, ast.Constant)
               and isinstance(node.value.value, str)]
    if len(matches) != 1:
        refuse("missing original P76 branch literal")
    return matches[0]


def validate_event(*, branch: str, head: str, ancestor: str = BASE) -> None:
    if (os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Windows"
            or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV"
            or os.environ.get("GITHUB_EVENT_NAME") != "push"):
        refuse("genuine hosted Windows event required")
    if (branch != BRANCH or ancestor != BASE or
            not isinstance(head, str) or HEX40.fullmatch(head) is None
            or os.environ.get("GITHUB_REF_NAME") != BRANCH
            or os.environ.get("GITHUB_SHA") != head):
        refuse("unapproved current branch, ancestry or signed event head")


def validate_historical_tag(expected: str = TAG_OID) -> None:
    if expected != TAG_OID:
        refuse("altered historical tag authority")
    oid = git("show-ref", "--verify", "--hash", "--", "refs/tags/" + TAG).strip().decode()
    if oid != TAG_OID or git("cat-file", "-t", oid) != b"tag\n":
        refuse("wrong immutable annotated tag object")
    if git("rev-parse", "--verify", "--end-of-options", oid + "^{}").strip().decode() != TAG_TARGET:
        refuse("wrong original tag target")
    raw = git("cat-file", "tag", oid)
    if raw.split(b"\n")[:3] != [
        ("object " + TAG_TARGET).encode(), b"type commit", ("tag " + TAG).encode()
    ]:
        refuse("wrong raw annotated tag body")


def verify_current(*, branch: str, head: str,
                   ancestor: str = BASE,
                   digest_override: dict[str, str] | None = None) -> dict:
    """Source-preserving C diagnostic only: no imported old tests or side effects."""
    validate_event(branch=branch, head=head, ancestor=ancestor)
    if git("rev-parse", "--show-toplevel").decode().strip().casefold() != ROOT.as_posix().casefold():
        refuse("wrong checkout root")
    if (git("rev-parse", "HEAD").strip().decode() != head or
            git("branch", "--show-current").strip().decode() != branch):
        refuse("live HEAD or branch differs")
    if git("rev-parse", "--is-shallow-repository") != b"false\n":
        refuse("shallow historical source")
    if git("rev-parse", "--show-object-format") != b"sha1\n":
        refuse("unexpected Git object format")
    if git("config", "--get", "core.autocrlf").strip() != b"false":
        refuse("non-raw Windows checkout configuration")
    if git("status", "--porcelain=v1", "-uall", "--ignored=matching").strip():
        refuse("dirty, ignored or untracked source")
    if git("for-each-ref", "refs/replace").strip():
        refuse("Git object replacement refs")
    gitdir = Path(git("rev-parse", "--absolute-git-dir").strip().decode())
    if (gitdir / "info" / "grafts").exists():
        refuse("untrusted Git history grafts")
    if git("merge-base", BASE, "HEAD").strip().decode() != BASE:
        refuse("not descendant of immutable P244")
    changed = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changed != ADDED:
        refuse("unapproved historical or product edits in P245")
    for rel in sorted(ADDED):
        if git("ls-tree", "--name-only", BASE, "--", rel).strip():
            refuse("claimed additive file already existed")
        raw = source_file(rel).read_bytes()
        if git("show", "HEAD:" + rel) != raw:
            refuse("new candidate Git/disk divergence")
    overrides = digest_override or {}
    if set(overrides) - set(FROZEN):
        refuse("unapproved source override path")
    witnesses = {}
    for rel, expected in sorted(FROZEN.items()):
        historic = git("show", HISTORICAL + ":" + rel)
        baseline = git("show", BASE + ":" + rel)
        live_git = git("show", "HEAD:" + rel)
        disk = source_file(rel).read_bytes()
        if (digest(historic) != expected or disk != historic or
                baseline != historic or live_git != historic or
                digest(disk) != overrides.get(rel, expected)):
            refuse("historical source/test byte witness mismatch: " + rel)
        witnesses[rel] = expected
    if historical_branch_literal(source_file("tests/phase8_byok_c1_p76_scope.py").read_bytes()) != HISTORICAL_P76_BRANCH:
        refuse("original P76 exact branch assertion modified")
    validate_historical_tag()
    if (git("rev-parse", "HEAD").strip().decode() != head
            or git("branch", "--show-current").strip().decode() != branch
            or git("status", "--porcelain=v1", "-uall", "--ignored=matching").strip()):
        refuse("Git branch or worktree changed during source proof")
    return {
        "schema": "P245-CANDIDATE-ONLY", "candidate_source_pass": True,
        "real_key_admission": "NO-GO", "production_release": "HOLD",
        "head": head, "branch": branch, "parent": BASE,
        "original_immutable_source": HISTORICAL,
        "frozen_sha256": witnesses, "historical_P76_wrong_branch_refusal_preserved": True,
        "four_original_P234_failures_unwaived": list(ORIGINAL_FAILURE_IDS),
        "qualified_approvals": "0/7", "full_product_regressions": "0/3",
    }
