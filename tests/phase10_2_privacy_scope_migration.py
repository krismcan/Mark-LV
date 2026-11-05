"""Phase 10.2 exact-source successor, not production capture authority.

The sealed Phase 10.1 tag/tree/complete inventory remain authenticated.
Every live admission re-reads Git refs, raw objects, index, disk and ignored
paths. No generated pins, cached success, historical fallback, or wildcard.
CANDIDATE_SHA256 is a static literal manifest; live admission never re-pins.
"""
from __future__ import annotations

import hashlib
import re

from tests import phase10_perception_scope_migration as prior

ROOT = prior.ROOT
BRANCH = "phase10-2-trusted-perception-20261102"
PARENT = "be6c126dc5f3a6814925bb95009ef2b2e6be80b7"
PARENT_TREE = "e6898712f51a070509929e4f40afe92f06a70b62"
PARENT_PARENT = "e3612279cb972e68e2487702183d5bf5b8f6c4a1"
PARENT_TAG = "nayeon-v1-phase-10-1-offline-perception-foundation-01"
PARENT_TAG_OBJECT = "c96dcea845bbab00a142d69341378d0f07f4b47f"
ADDED = frozenset({
    "docs/phase10_2_trusted_perception_privacy_rfc.md",
    "nayeon/perception/permissions.py",
    "tests/test_phase10_2_permission_ledger.py",
    "tests/phase10_2_privacy_scope_migration.py",
    "tests/test_phase10_2_privacy_scope_integrity.py",
})
MODIFIED = frozenset({
    ".codex/CURRENT_STATE.md",
    "tests/phase10_perception_scope_migration.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/test_phase10_perception_scope_integrity.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_836_scope_integrity.py",
    "tests/test_phase_837_scope_integrity.py",
    "tests/test_phase8_byok_scope_integrity.py",
    "tests/test_phase8_byok_b_scope_integrity.py",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase10_2_privacy_scope_migration.py"
SELF_PIN = re.compile(rb'("tests/phase10_2_privacy_scope_migration.py": ")[0-9a-f]{64}(",)')
CANDIDATE_SHA256 = {
    ".codex/CURRENT_STATE.md": "5775c68f8d0428004de85c9a2695fd7d06ea8bb98d3e8dbbfdf2fe647e8373a1",
    "docs/phase10_2_trusted_perception_privacy_rfc.md": "4ba9cc03af2480a9f9a21968698b3428ca1ce8cf83926c372edab29635f0078a",
    "nayeon/perception/permissions.py": "33b9cbdb6964276fe0e196e63bfdb7b355917a284ea809513200d856e16634fb",
    "tests/test_phase10_2_permission_ledger.py": "d9c0b477b3c257e9afa93a2ad119edf3177988d01195d3d50fab43360af085af",
    "tests/phase10_2_privacy_scope_migration.py": "7711c35432107723b64f980a4b7bc76f29075ae1ab1d066b137991601b6af88c",
    "tests/test_phase10_2_privacy_scope_integrity.py": "c4ca43d74f49f4766fd7d0b2914563a5d97afe5d2000d933c0baa0a521b31fdb",
    "tests/phase10_perception_scope_migration.py": "6999b151dcf634ed589df6b774b5a84c4252e77f38975f4f87af1a5b56efc9f0",
    "tests/phase_8_30_scope_migration.py": "f9aa8c8df0144c83baa4edc8cc8d5f99ce5221c8c1263b13378feaeb87060487",
    "tests/test_phase10_perception_scope_integrity.py": "ee02c1713679906b1b2d35e91d975bcca9be687fdfc105c45a59dccd7520638d",
    "tests/test_phase_830_scope_integrity.py": "433a34a48af83de3353b2f08ed9ec6b710806e01ec0be096b082abd6272c946f",
    "tests/test_phase_836_scope_integrity.py": "eb44fb008edb406f7236d2a0b62b992d02654c2c3cc4f1fe98d6c2091c281092",
    "tests/test_phase_837_scope_integrity.py": "794fec93c9293450f7219f2256441cdcfebfd2cef0106de152bf9f46028f5286",
    "tests/test_phase8_byok_scope_integrity.py": "f93004189789b0a820fca51bdcfd867543e1d41ee1cdfaa21ddb2b5d1518d4ff",
    "tests/test_phase8_byok_b_scope_integrity.py": "65dad89298a587d6bb5dde5455df4d701bb1a1fd9a7a96cecf3e647800e3ae8b",
}
RAW = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")


def _git(*args):
    return prior._git(*args)


def _disk(path):
    return prior._disk(path)


def _oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or not re.fullmatch(rb"[0-9a-f]{40}\n", raw):
        raise AssertionError("Phase10.2 malformed Git object ID")
    return raw[:-1].decode("ascii")


def _digest(path, raw):
    if type(raw) is not bytes:
        raise AssertionError("Phase10.2 source not bytes")
    if path == SELF:
        raw, count = SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], raw)
        if count != 1:
            raise AssertionError("Phase10.2 bad self-pin count")
    return hashlib.sha256(raw).hexdigest()


def _commit(oid):
    if _git("cat-file", "-t", oid) != b"commit\n":
        raise AssertionError("Phase10.2 wrong commit object kind")
    raw = _git("cat-file", "commit", oid)
    if prior._object("commit", raw) != oid or b"\n\n" not in raw:
        raise AssertionError("Phase10.2 forged raw commit")
    headers = raw.split(b"\n\n", 1)[0].split(b"\n")
    trees = [row[5:] for row in headers if row.startswith(b"tree ")]
    parents = [row[7:] for row in headers if row.startswith(b"parent ")]
    if (len(trees) != 1 or headers[0] != b"tree " + trees[0]
            or any(not re.fullmatch(rb"[0-9a-f]{40}", v) for v in trees + parents)):
        raise AssertionError("Phase10.2 malformed raw commit headers")
    return trees[0].decode("ascii"), [v.decode("ascii") for v in parents]


def _tree(commit):
    entries = prior.historical.prior._inventory(
        _git("ls-tree", "-r", "-z", "--full-tree", commit))
    tree, _ = _commit(commit)
    if prior._tree_oid(entries) != tree:
        raise AssertionError("Phase10.2 unauthenticated complete Git tree")
    return entries


def _baseline():
    if (_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PARENT_TAG)
            != PARENT_TAG_OBJECT
            or _git("cat-file", "-t", PARENT_TAG_OBJECT) != b"tag\n"
            or _oid("rev-parse", "--verify", "--end-of-options",
                    PARENT_TAG_OBJECT + "^{}") != PARENT):
        raise AssertionError("Phase10.2 sealed parent tag mismatch")
    raw_tag = _git("cat-file", "tag", PARENT_TAG_OBJECT)
    if (prior._object("tag", raw_tag) != PARENT_TAG_OBJECT
            or raw_tag.split(b"\n")[:3] != [
                ("object " + PARENT).encode(), b"type commit",
                ("tag " + PARENT_TAG).encode()]):
        raise AssertionError("Phase10.2 forged raw parent tag")
    if (_commit(PARENT) != (PARENT_TREE, [PARENT_PARENT])
            or _oid("rev-parse", PARENT + "^{tree}") != PARENT_TREE):
        raise AssertionError("Phase10.2 sealed parent commit/tree mismatch")
    baseline = _tree(PARENT)
    if prior._tree_oid(baseline) != PARENT_TREE:
        raise AssertionError("Phase10.2 parent inventory mismatch")

    # Reconstruct all Phase10.1 source from the authenticated older B tree
    # and the STATIC Phase10.1 source manifest. This reads sealed blobs, never
    # current disk metadata, and does not call the old live branch guard.
    expected = dict(prior._baseline())
    if (len(prior.ENVELOPE) != 32 or len(prior.ADDED) != 6
            or len(prior.MODIFIED) != 26
            or set(prior.CANDIDATE_SHA256) != prior.ENVELOPE):
        raise AssertionError("Phase10.2 frozen 10.1 manifest drift")
    for path, pin in prior.CANDIDATE_SHA256.items():
        raw = _git("show", PARENT + ":" + path)
        if (prior._digest(path, raw) != pin
                or baseline.get(path) != ("100644", prior._blob(raw))):
            raise AssertionError("Phase10.2 frozen parent path mismatch: " + path)
        expected[path] = ("100644", prior._blob(raw))
    if expected != baseline:
        raise AssertionError("Phase10.2 frozen parent inventory drift")
    return baseline


def _manifest(baseline):
    if (len(ADDED) != 5 or len(MODIFIED) != 9 or len(ENVELOPE) != 14
            or ADDED & MODIFIED or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("Phase10.2 wrong exact manifest")
    if any(type(p) is not str or not re.fullmatch(r"[0-9a-f]{64}", p)
           or p == "0" * 64 for p in CANDIDATE_SHA256.values()):
        raise AssertionError("Phase10.2 unfinalized source pins")
    if (any(p in baseline for p in ADDED)
            or any(baseline.get(p, (None,))[0] != "100644"
                   for p in MODIFIED)):
        raise AssertionError("Phase10.2 baseline path/mode mismatch")


def _expected(baseline):
    _manifest(baseline)
    expected = dict(baseline)
    for path, pin in CANDIDATE_SHA256.items():
        raw = _disk(path)
        if _digest(path, raw) != pin:
            raise AssertionError("Phase10.2 candidate byte mismatch: " + path)
        expected[path] = ("100644", prior._blob(raw))
        if path in MODIFIED and expected[path] == baseline[path]:
            raise AssertionError("Phase10.2 undeclared unchanged modification: " + path)
        if path == ".codex/CURRENT_STATE.md":
            sealed = _git("show", PARENT + ":" + path)
            if (len(raw) <= len(sealed) or not raw.endswith(sealed)
                    or prior._blob(sealed) != baseline[path][1]):
                raise AssertionError("Phase10.2 history must preserve 10.1 suffix")
        if path in {
                "tests/phase10_perception_scope_migration.py",
                "tests/phase_8_30_scope_migration.py"}:
            sealed = _git("show", PARENT + ":" + path)
            if not raw.startswith(sealed) or len(raw) <= len(sealed):
                raise AssertionError("Phase10.2 historical guard must be append-only")
    for path, (_, blob) in baseline.items():
        if path not in MODIFIED and prior._blob(_disk(path)) != blob:
            raise AssertionError("Phase10.2 frozen source modified: " + path)
    return expected


def _working_inventory(committed, *, git=None):
    # Use one uncached source for every live index, untracked and ignored query.
    call = _git if git is None else git
    index = prior.historical.prior._inventory(
        call("ls-files", "--stage", "-z"), index=True)
    flags = call("ls-files", "-v", "--sparse", "-z")
    if type(flags) is not bytes or flags and not flags.endswith(b"\0"):
        raise AssertionError("Phase10.2 malformed index flags")
    entries = flags.split(b"\0")[:-1]
    if any(not row.startswith(b"H ") for row in entries):
        raise AssertionError("Phase10.2 hidden Git index flags")
    observed = prior.historical.prior._paths(
        b"".join(row[2:] + b"\0" for row in entries))
    if observed != set(index):
        raise AssertionError("Phase10.2 index flags mismatch")
    others = prior.historical.prior._paths(
        call("ls-files", "--others", "--exclude-standard", "-z"))
    ignored = prior.historical.prior._paths(
        call("ls-files", "--others", "--ignored", "--exclude-standard", "-z"))
    prior.historical.prior._canonical_paths(
        set(committed) | set(index) | others | ignored)
    if ignored:
        raise AssertionError("Phase10.2 ignored source present")
    return index, others


def _delta(raw, before, after, paths, *, work=False):
    prior._delta(raw, before, after, paths, work=work)


def _prove_topology(head, baseline, expected, committed, index,
                    untracked, raw_work):
    cached = _git(*RAW, "--cached")
    if head == PARENT:
        if committed != baseline:
            raise AssertionError("Phase10.2 parent changed")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("Phase10.2 missing/extra untracked source")
            _delta(cached, baseline, index, set())
            _delta(raw_work, index, expected, MODIFIED, work=True)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            raise AssertionError("Phase10.2 partial stage")
        _delta(cached, baseline, expected, ENVELOPE)
        _delta(raw_work, index, expected, set(), work=True)
        return "EXACT_STAGED"
    _, parents = _commit(head)
    if (parents != [PARENT]
            or _git("rev-list", "--parents", "-n", "1", head) !=
            (head + " " + PARENT + "\n").encode()):
        raise AssertionError("Phase10.2 requires immediate sealed child")
    if committed != expected or index != expected or untracked:
        raise AssertionError("Phase10.2 unapproved child inventory")
    _delta(cached, committed, index, set())
    _delta(raw_work, index, expected, set(), work=True)
    _delta(_git(*RAW, PARENT, head), baseline, expected, ENVELOPE)
    return "EXACT_CHILD"


def assert_phase10_2_privacy_integrity():
    """Unconditional fresh live branch admission; no historical fallbacks."""
    if _git("rev-parse", "--show-object-format") != b"sha1\n":
        raise AssertionError("Phase10.2 unsupported Git object format")
    if _git("branch", "--show-current") != (BRANCH + "\n").encode():
        raise AssertionError("Phase10 wrong exact branch")
    head = _oid("rev-parse", "HEAD")
    baseline = _baseline()
    expected = _expected(baseline)
    committed = _tree(head)
    index, untracked = _working_inventory(committed)
    result = _prove_topology(head, baseline, expected, committed, index,
                             untracked, _git(*RAW))
    if (head != _oid("rev-parse", "HEAD")
            or _git("branch", "--show-current") != (BRANCH + "\n").encode()):
        raise AssertionError("Phase10.2 ref changed during live admission")
    if _git("show-ref", "--verify", "--hash", "--",
            "refs/tags/" + PARENT_TAG) != (PARENT_TAG_OBJECT + "\n").encode():
        raise AssertionError("Phase10.2 sealed parent tag changed during admission")
    return result


# Phase10.3 successor: retain the complete sealed guard above as history.
_phase10_2_historical_assert = assert_phase10_2_privacy_integrity


def assert_phase10_2_privacy_integrity():
    """Unconditional current source route; no historical fallback."""
    from tests.phase10_3_scope_migration import assert_phase10_3_integrity
    return assert_phase10_3_integrity()
