"""Explicit C source evidence; no historical routing or effect authority.

P245's ROOT is derived from its __file__, not its historical branch constant.
Only its root-agnostic readers/parsers are reused, without rebinding globals.
Its verify_current and P248's root-bound source_snapshot remain unchanged.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

from scripts import p245_p76_current_source as source

PARENT = "67ce360667f51aad5891535120ab311907312371"
PARENT_TREE = "42f697e506e5d4d02ad4ab2472faca464e310079"
PARENT_PARENT = "bff6895f5f0b4f086f0c4ed97f5f46a44f8d2762"
PARENT_COUNT = 1099
BRANCH = "byok-c1-p273-current-p76-admission-20261118"
BASE_BRANCH = "byok-c1-p272-os-bound-custody-admission-20261118"
REPOSITORY = "krismcan/Mark-LV"
MAX_EVENT_BYTES = 2 * 1024 * 1024
LOCAL_ROOT = "D:/Nayeon/CODEX_P273_CURRENT_P76_ADMISSION_20261118"
ADDED = frozenset({
    "scripts/p273_p76_current_admission.py",
    "scripts/p273_p76_hosted_suite.py",
    "tests/test_p273_p76_current_admission.py",
    ".github/workflows/p273-p76-current-admission.yml",
    "docs/byok-c1-p273-p76-current-admission.md",
})
READ_ONLY_GIT_ENV = {
    "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1",
}
# Anchors from the immutable P252 report, not newly executed P273 outcomes.
ORIGINAL_FAIL_STDERR = (
    "4bacba451bbf19133d5934ddf1a519b71819845ad0d74a508cd8e1fbb59c2ac2",
    "7fbe64e9b84a2cdcd0441d71c0880d9d08a1e8683a64479070d56fab07a5af10",
    "8b026718a739c4dde3e3aeb41d7f3f3e2dca4487a1f3898612abd35da492e258",
    "4a1340f25821e937fb9158d6c4e353e5fafba126e7ccecb44e9b10d9a8ef5ff2",
)


class CurrentAdmissionRefused(AssertionError):
    """HOLD; never a credential, product or security admission result."""


def refuse(reason: str) -> None:
    raise CurrentAdmissionRefused("P273 current source HOLD: " + reason)


def canonical(proof: dict) -> bytes:
    return json.dumps(proof, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def object_oid(kind: str, raw: bytes) -> str:
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode()
                        + b"\0" + raw).hexdigest()


def validate_commit(oid: str, raw: bytes, tree: str, parents: list[str]) -> None:
    headers, separator, _ = raw.partition(b"\n\n")
    lines = headers.split(b"\n")
    if (not separator or object_oid("commit", raw) != oid
            or [line for line in lines if line.startswith(b"tree ")]
            != [b"tree " + tree.encode()]
            or [line for line in lines if line.startswith(b"parent ")]
            != [b"parent " + parent.encode() for parent in parents]):
        refuse("raw commit hash/tree/exact parents differ")


def parse_parent_tree(raw: bytes) -> dict:
    if not raw.endswith(b"\0"):
        refuse("incomplete parent inventory")
    entries = {}
    for record in raw[:-1].split(b"\0"):
        match = re.fullmatch(rb"(100644|100755) blob ([0-9a-f]{40})\t([A-Za-z0-9_./-]+)", record)
        if match is None:
            refuse("unsupported parent entry")
        rel = match[3].decode("ascii")
        source.canonical_path(rel)
        if rel in entries:
            refuse("duplicate parent entry")
        entries[rel] = [match[1].decode(), match[2].decode()]
    if len(entries) != PARENT_COUNT or source.tree_oid(entries) != PARENT_TREE:
        refuse("incomplete or altered pinned P272 parent tree")
    return entries


def validate_child(head: str, raw: bytes, delta: bytes, tree: dict, parent: dict) -> None:
    """Pure parser contract; caller obtains every input from actual Git."""
    validate_commit(head, raw, source.tree_oid(tree), [PARENT])
    if (set(tree) != set(parent) | ADDED or set(parent) & ADDED
            or any(tree.get(rel) != entry for rel, entry in parent.items())):
        refuse("child must retain every parent byte and add exactly five paths")
    expected = bytearray()
    for rel in sorted(ADDED):
        mode, oid = tree[rel]
        if mode != "100644" or source.HEX40.fullmatch(oid) is None:
            refuse("candidate addition must be regular 100644")
        expected.extend(b":000000 100644 " + b"0" * 40 + b" " + oid.encode()
                        + b" A\0" + rel.encode() + b"\0")
    if bytes(expected) != delta:
        refuse("exact raw add-only child delta differs")


def parse_pull_request_event(raw: bytes, *, repository: str, ref: str, head: str) -> dict:
    """Pure, bounded payload parser; synthetic inputs grant no hosted admission.

    Only required fields are projected: real GitHub payloads have other fields.
    Duplicate keys and nonfinite JSON numbers refuse throughout the payload.
    PR numbers must be exact integers in the positive signed 32-bit range.
    """
    if (type(raw) is not bytes or not 0 < len(raw) <= MAX_EVENT_BYTES
            or type(repository) is not str or repository != REPOSITORY
            or type(ref) is not str or type(head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", head) is None):
        refuse("invalid pull_request parser input")

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                refuse("duplicate pull_request JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        refuse("nonfinite pull_request JSON number")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            refuse("nonfinite pull_request JSON number")
        return number

    try:
        event = json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs,
                           parse_constant=nonfinite, parse_float=finite_float)
    except (UnicodeError, ValueError, RecursionError):
        refuse("malformed pull_request JSON")

    def obj(container, key):
        if type(container) is not dict or type(container.get(key)) is not dict:
            refuse("missing or nonobject pull_request field")
        return container[key]

    def exact(container, key, value):
        if type(container.get(key)) is not type(value) or container[key] != value:
            refuse("pull_request field differs: " + key)

    pr = obj(event, "pull_request")
    number = event.get("number")
    if type(number) is not int or not 1 <= number <= 2147483647:
        refuse("invalid pull_request number")
    exact(pr, "number", number)
    action = event.get("action")
    if type(action) is not str or action not in {"opened", "synchronize", "reopened"}:
        refuse("unsupported pull_request action")
    exact(pr, "draft", True)
    exact(obj(event, "repository"), "full_name", repository)
    for side, sha, branch in (("head", head, BRANCH), ("base", PARENT, BASE_BRANCH)):
        entry = obj(pr, side)
        exact(entry, "sha", sha)
        exact(entry, "ref", branch)
        exact(obj(entry, "repo"), "full_name", repository)
    if ref != "refs/pull/" + str(number) + "/merge":
        refuse("pull_request ref differs from event number")
    return {"action": action, "number": number, "draft": True,
            "head": head, "head_ref": BRANCH, "base": PARENT,
            "base_ref": BASE_BRANCH, "repository": repository,
            "event_sha256": source.digest(raw)}


def hosted_event(root: Path, head: str) -> dict:
    """Read actual hosted metadata and event file; never accept approval flags."""
    workspace = os.environ.get("GITHUB_WORKSPACE", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Windows"
            or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_EVENT_NAME") != "pull_request"
            or not workspace or not Path(workspace).is_absolute()
            or Path(workspace).absolute() != root
            or not event_path or not Path(event_path).is_absolute()):
        refuse("exact disposable hosted Windows pull_request context required")
    # Reuse the full P245 bounded physical reader (regular, single-link,
    # no reparse/alias, stable path/descriptor metadata). Never log the body.
    raw, _ = source.bounded_file(Path(event_path), MAX_EVENT_BYTES)
    return parse_pull_request_event(raw, repository=os.environ["GITHUB_REPOSITORY"],
                                    ref=os.environ.get("GITHUB_REF", ""), head=head)


def live_head() -> str:
    raw = source.git("rev-parse", "HEAD")
    if re.fullmatch(rb"[0-9a-f]{40}\n", raw) is None:
        refuse("malformed live HEAD")
    return raw[:-1].decode()


def require_domain(root: Path, *, hosted: bool = False) -> str:
    root = Path(root).absolute()
    if os.name != "nt" or sys.version_info[:2] != (3, 12):
        refuse("Windows Python 3.12 required")
    if root != source.ROOT or Path(__file__).absolute() != root / "scripts/p273_p76_current_admission.py":
        refuse("explicit root/module origin differs")
    if Path(source.__file__).absolute() != root / "scripts/p245_p76_current_source.py":
        refuse("P245 module origin differs")
    source.checked_node(root)
    for key, value in os.environ.items():
        name = key.upper()
        if (name.startswith("P134_") or (name.startswith("GIT_")
                and (name not in READ_ONLY_GIT_ENV or value != READ_ONLY_GIT_ENV[name]))):
            refuse("unsupported Git/P134 environment")
    is_hosted = os.environ.get("GITHUB_ACTIONS") == "true"
    if hosted or is_hosted:
        hosted_event(root, live_head())
        domain = "GITHUB_HOSTED_WINDOWS_PULL_REQUEST"
    else:
        if root.as_posix() != LOCAL_ROOT:
            refuse("wrong isolated local root")
        domain = "AUTHORIZED_LOCAL_READ_ONLY"
    if source.git("rev-parse", "--show-toplevel") != (root.as_posix() + "\n").encode():
        refuse("Git top-level differs from explicit physical root")
    return domain


def _topology(root: Path) -> dict:
    domain = require_domain(root)
    head = live_head()
    if head == PARENT:
        refuse("uncommitted parent/draft cannot produce current-source evidence")
    event = (hosted_event(root, head)
             if domain == "GITHUB_HOSTED_WINDOWS_PULL_REQUEST" else None)
    identity = source.git_identity(branch=BRANCH, head=head)
    if source.git("status", "--porcelain=v1", "-uall", "--ignored=matching") != b"":
        refuse("dirty, untracked or ignored checkout")
    # SHA-1 reconstruction authenticates all 1099 parent entries without
    # trusting a selected-file manifest or issuing 1099 Git show subprocesses.
    parent = parse_parent_tree(source.git("ls-tree", "-r", "-z", "--full-tree", PARENT))
    parent_raw = source.git("cat-file", "commit", PARENT)
    validate_commit(PARENT, parent_raw, PARENT_TREE, [PARENT_PARENT])
    if source.git("merge-base", source.TAG_TARGET, PARENT) != (source.TAG_TARGET + "\n").encode():
        refuse("historical tag target is not an actual parent ancestor")
    tree = source.head_entries()
    if {rel: entry[:2] for rel, entry in source.index_entries().items()} != tree:
        refuse("topology index differs from actual child tree")
    raw = source.git("cat-file", "commit", head)
    delta = source.git("diff-tree", "--no-commit-id", "--raw", "--no-abbrev",
                       "--no-renames", "-r", "-z", PARENT, head, "--")
    validate_child(head, raw, delta, tree, parent)
    if source.tree_oid(tree) != identity["tree_oid"]:
        refuse("child inventory differs from raw commit tree")
    proof = {"domain": domain, "identity": identity, "parent_tree": parent,
            "tree": tree, "parent_commit_sha256": source.digest(parent_raw),
            "child_commit_sha256": source.digest(raw), "raw_delta_sha256": source.digest(delta)}
    if event is not None:
        proof["pull_request"] = event
    return proof


def prove_authenticated_current_source(root: Path) -> dict:
    """Fresh bounded C proof of actual source only. Any uncertainty raises HOLD.

    Never called by an existing public route. An uncommitted/staged candidate, merge,
    later descendant or modified parent is ineligible, even with green tests.
    Two complete physical scans and repeated full topology proofs are required.
    """
    first = _topology(root)
    complete = source.complete_source()
    if complete["tree"] != first["tree"]:
        refuse("first scan differs from authenticated topology")
    frozen = {}
    for rel, pin in sorted(source.FROZEN.items()):
        parent_oid = first["parent_tree"][rel][1]
        baseline = source.git("cat-file", "blob", parent_oid)
        historical = source.git("show", source.HISTORICAL + ":" + rel)
        if (source.blob_oid(baseline) != parent_oid or source.digest(baseline) != pin
                or source.digest(historical) != pin or complete["disk"][rel]["sha256"] != pin):
            refuse("six-pin historical/current witness differs: " + rel)
        frozen[rel] = pin
    if source.historical_branch_literal(source.git(
            "cat-file", "blob", first["parent_tree"]["tests/phase8_byok_c1_p76_scope.py"][1])) != source.HISTORICAL_P76_BRANCH:
        refuse("original archival branch literal differs")
    # Fresh raw reads, not cached proof reuse. A second-read corruption must
    # reach the real scanner and fail before this function can return evidence.
    if source.complete_source() != complete:
        refuse("complete second source scan differs")
    if _topology(root) != first:
        refuse("source domain or Git topology drift")
    return {"schema": "P273-CURRENT-SOURCE-EVIDENCE-V1", "provenance": "C",
            "result": "AUTHENTICATED_CURRENT_SOURCE_EVIDENCE", "topology": first,
            "complete_source": complete, "complete_scans": 2,
            "historical_parent_count": PARENT_COUNT, "frozen_six": frozen,
            "archival_provenance": "H: unchanged original public route",
            "original_failures_unwaived": list(source.ORIGINAL_FAILURE_IDS),
            "original_fail_stderr_sha256": list(ORIGINAL_FAIL_STDERR),
            "independent_source_approval": None, "GOV-01": "PENDING",
            "REL-06": "PENDING", "P76_governance": "HOLD", "P96_production": "HOLD",
            "real_keys": "NO-GO", "full_product_accepted_native_regressions": "0/3"}
