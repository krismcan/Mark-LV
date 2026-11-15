"""P248 local draft source evidence. No public admission or effect authority.

Run from the repository with native Python -B -m unittest. P245's hosted
contract is unchanged. Only the exact draft or clean one-child topology is read.
"""
from __future__ import annotations

import hashlib
import os

from scripts import p245_p76_current_source as source

HEAD = "39dbb445fc08a1ef03c73f4a13c6f344be8dfa07"
BRANCH = "byok-c1-p248-p76-property-equivalence-20261115"
ROOT = "D:/Nayeon/CODEX_P248_P76_EQUIVALENCE_20261115"
ADDED = frozenset({
    "scripts/p248_p76_properties.py",
    "tests/test_p248_p76_properties.py",
    "docs/byok-c1-p248-p76-property-mapping.md",
})


def _validate_child(head: str, raw: bytes, delta: bytes, tree: dict) -> None:
    """Authenticate the raw commit and exact raw Git addition records."""
    oid = hashlib.sha1(b"commit " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    headers, separator, _ = raw.partition(b"\n\n")
    lines = headers.split(b"\n")
    if (not separator or oid != head
            or [line for line in lines if line.startswith(b"parent ")]
            != [b"parent " + HEAD.encode()]
            or [line for line in lines if line.startswith(b"tree ")]
            != [b"tree " + source.tree_oid(tree).encode()]):
        source.refuse("P248 requires authenticated one-child P247 commit")
    expected = bytearray()
    for rel in sorted(ADDED):
        entry = tree.get(rel)
        if (entry is None or len(entry) != 2 or entry[0] != "100644"
                or source.HEX40.fullmatch(entry[1]) is None):
            source.refuse("P248 requires regular 100644 additions")
        expected.extend(b":000000 100644 " + b"0" * 40 + b" "
                        + entry[1].encode() + b" A\0" + rel.encode() + b"\0")
    if delta != bytes(expected):
        source.refuse("P248 requires exact three-path raw addition delta")


def _topology() -> tuple[str, str, dict, bytes]:
    # Reject overrides instead of silently relying on P245's sanitized Git env.
    if any(key.upper().startswith(("GIT_", "P134_")) for key in os.environ):
        source.refuse("P248 unsupported Git environment")
    head_raw = source.git("rev-parse", "HEAD")
    if (len(head_raw) != 41 or not head_raw.endswith(b"\n")
            or source.HEX40.fullmatch(head_raw[:-1].decode("ascii")) is None):
        source.refuse("P248 invalid HEAD identity")
    head = head_raw[:-1].decode("ascii")
    identity = source.git_identity(branch=BRANCH, head=head)
    status = source.git("status", "--porcelain=v1", "-uall", "--ignored=matching")
    draft_status = b"".join(b"?? " + rel.encode() + b"\n" for rel in sorted(ADDED))
    if head == HEAD and status == draft_status:
        return "EXACT_UNSTAGED_DRAFT", head, identity, status
    if head != HEAD and status == b"":
        return "CLEAN_ONE_CHILD_CANDIDATE", head, identity, status
    source.refuse("P248 requires exact draft or clean one-child candidate")


def _child_evidence(head: str, tree: dict) -> dict:
    raw = source.git("cat-file", "commit", head)
    delta = source.git("diff-tree", "--no-commit-id", "--raw", "--no-abbrev",
                       "--no-renames", "-r", "-z", HEAD, head, "--")
    _validate_child(head, raw, delta, tree)
    return {"parent": HEAD, "raw_commit_sha256": source.digest(raw),
            "raw_delta_sha256": source.digest(delta)}


def source_snapshot() -> dict:
    """Observe exact draft or one-child HEAD/index/raw disk; never approve it.

    Draft additions receive observed hashes, without a reviewed-source claim.
    All ignored paths, extra additions, staged changes and tracked edits refuse.
    Committed source hashes bind to Git but still require independent approval.
    """
    if source.ROOT.as_posix() != ROOT:
        source.refuse("P248 wrong assigned root")
    if source.git("rev-parse", "--show-toplevel").decode().strip() != ROOT:
        source.refuse("P248 wrong Git root")
    for module, rel in ((source, "scripts/p245_p76_current_source.py"),
                        (None, "scripts/p248_p76_properties.py")):
        filename = __file__ if module is None else module.__file__
        if os.path.abspath(filename) != str(source.ROOT / rel):
            source.refuse("P248 wrong source module location")
        source.checked_node(source.ROOT / rel)
    topology, head, identity, status = _topology()
    complete = source.complete_source()
    child = (_child_evidence(head, complete["tree"])
             if topology == "CLEAN_ONE_CHILD_CANDIDATE" else None)
    additions = {}
    identities = {tuple(item["identity"]) for item in complete["disk"].values()}
    for rel in sorted(ADDED):
        if child is not None:
            additions[rel] = complete["disk"][rel]
            continue
        if rel in complete["tree"]:
            source.refuse("P248 addition already tracked")
        raw, file_identity = source.raw_source(rel)
        if tuple(file_identity) in identities:
            source.refuse("P248 aliased draft source")
        identities.add(tuple(file_identity))
        additions[rel] = {"sha256": source.digest(raw), "size": len(raw),
                          "identity": file_identity}
    for rel, expected in source.FROZEN.items():
        if complete["disk"][rel]["sha256"] != expected:
            source.refuse("P248 frozen witness mismatch: " + rel)
    # A second full proof prevents zero-scan/cached-proof admission and closes
    # observed index/disk drift; bounded readers reject links and hardlinks.
    if source.complete_source() != complete:
        source.refuse("P248 complete source drift")
    if child is None:
        for rel, observed in additions.items():
            raw, file_identity = source.raw_source(rel)
            if {"sha256": source.digest(raw), "size": len(raw),
                    "identity": file_identity} != observed:
                source.refuse("P248 draft source drift")
    elif _child_evidence(head, complete["tree"]) != child:
        source.refuse("P248 committed source drift")
    if _topology() != (topology, head, identity, status):
        source.refuse("P248 source identity drift")
    return {"schema": "P248-LOCAL-SOURCE-OBSERVATION-V2", "identity": identity,
            "topology": topology, "head": head, "child_evidence": child,
            "complete_source_scans": 2,
            "complete_source": complete, "candidate_additions": additions,
            "independently_approved_sha": None,
            "historical_failures_unwaived": list(source.ORIGINAL_FAILURE_IDS),
            "acceptance": "HOLD", "real_key": "NO-GO"}


def current_read_pair() -> dict:
    """Exercise two fresh complete current-source scans with exact equality."""
    before = source.complete_source()
    after = source.complete_source()
    if before != after:
        source.refuse("P248 current scan observations differ")
    return before
