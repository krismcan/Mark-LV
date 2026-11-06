"""P85 exact P84-source read-only review admission; NEVER credential authority.

Authenticates sealed Phase10.3 ancestry, exact P80 commit/source, exact P84
commit/source and an additive two-file P85 review delta. This is *not* a
replacement for independently reviewed release-integrity admission.
"""
from __future__ import annotations

import hashlib
import re

from tests import phase8_byok_c1_p76_scope as old

ROOT = old.ROOT
_git = old._git
_disk = old._disk
_sealed = old.sealed
_blob = _sealed.prior._blob

BRANCH = "byok-c1-p85-source-integrity-20261106"
P80 = "24da07345c67566d2e79f442aabfba36a1ebddb4"
P80_TREE = "1795b59895b7fd52da525d237eb4282d5d10851f"
P84 = "c53b761ea4329ef395a0126097a5949d9a9947a5"
P84_TREE = "7a446c59ca077ecf177ad0906eedff6910ce5141"
SELF = "tests/phase8_byok_c1_p85_scope.py"
TEST = "tests/test_phase8_byok_c1_p85_scope.py"
ADDED = frozenset({SELF, TEST})
SELF_PIN = re.compile(
    rb'("tests/phase8_byok_c1_p85_scope.py":\s*")[A-F0-9]{64}(",)'
)
P84_ADDITIONS = {
    "nayeon/brain/pending_custody_status_view.py":
        "C9A707198A287E518E57B54FA662EC974151DCA9DAE913348CB01C55A677942D",
    "tests/test_pending_custody_status_view.py":
        "0D7ECE8B536219AC5037AF6FC93C8BA06A2297987448C49D764A7181578B017A",
}
P85_ADDITIONS = {
    "tests/phase8_byok_c1_p85_scope.py":
        "C102CBA1191846509B422C56808AC5FA818084DFDE93D61F4641C817BB262BF5",
    "tests/test_phase8_byok_c1_p85_scope.py":
        "C32949C33F38B230BAC963FC86E87E09CC055D0C5F4149B6D9E7B0FE3D0576E7",
}


class P85ScopeRefused(AssertionError):
    """Read-only source denial: never UI/secret/credential permission."""


def _fail(message):
    raise P85ScopeRefused("P85 offline source refused: " + message)


def _digest(path, data):
    if type(data) is not bytes:
        _fail("non-byte input")
    if path == SELF:
        found = tuple(SELF_PIN.finditer(data))
        if len(found) != 1:
            _fail("ambiguous or missing normalized self pin")
        data = SELF_PIN.sub(lambda m: m[1] + b"0" * 64 + m[2], data)
    return hashlib.sha256(data).hexdigest().upper()


def _oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or re.fullmatch(rb"[0-9a-f]{40}\n", raw) is None:
        _fail("malformed Git OID")
    return raw[:-1].decode("ascii")


def _p84_baseline():
    # Reuse ONLY the private sealed reference/source readers. The prior
    # public guard intentionally rejects this distinct review branch.
    sealed = old._baseline()
    if (_sealed._commit(P80) != (P80_TREE, [old.PARENT])
            or _oid("rev-parse", P80 + "^{tree}") != P80_TREE):
        _fail("P80 source ancestor changed")
    p80 = _sealed._tree(P80)
    reconstructed = dict(sealed)
    if len(old.ENVELOPE) != 10:
        _fail("original P80 review manifest changed")
    for path, literal_pin in old.CANDIDATE_SHA256.items():
        b = _git("show", P80 + ":" + path)
        if (old._digest(path, b) != literal_pin
                or p80.get(path) != ("100644", _blob(b))):
            _fail("P80 pinned source mismatch: " + path)
        reconstructed[path] = ("100644", _blob(b))
    if reconstructed != p80:
        _fail("P80 complete source inventory differs from sealed ancestry")
    if (_sealed._commit(P84) != (P84_TREE, [P80])
            or _oid("rev-parse", P84 + "^{tree}") != P84_TREE):
        _fail("P84 exact child or tree differs")
    p84 = _sealed._tree(P84)
    expected = dict(p80)
    for path, pin in P84_ADDITIONS.items():
        b = _git("show", P84 + ":" + path)
        if _digest(path, b) != pin or p84.get(path) != ("100644", _blob(b)):
            _fail("P84 pinned new source mismatch: " + path)
        if path in p80:
            _fail("P84 unexpectedly overwrote prior source")
        expected[path] = ("100644", _blob(b))
    if expected != p84:
        _fail("P84 contains unreviewed changes")
    return p84


def _expected(p84):
    if (len(ADDED) != 2 or set(P85_ADDITIONS) != ADDED
            or any(path in p84 for path in ADDED)):
        _fail("P85 exact additive source manifest differs")
    expected = dict(p84)
    for path, pin in P85_ADDITIONS.items():
        raw = _disk(path)
        if (re.fullmatch(r"[A-F0-9]{64}", pin) is None
                or pin == "0" * 64):
            _fail("unreviewed P85 SHA256 literal")
        if path == SELF:
            found = tuple(SELF_PIN.finditer(raw))
            if len(found) != 1 or pin.encode("ascii") not in found[0].group(0):
                _fail("P85 self pin literal mismatch")
        if _digest(path, raw) != pin:
            _fail("P85 source bytes changed: " + path)
        expected[path] = ("100644", _blob(raw))
    for path, (_, oid) in p84.items():
        if _blob(_disk(path)) != oid:
            _fail("P84 frozen source changed: " + path)
    return expected


def _prove(head, p84, expected, committed, index, untracked):
    raw_cached = _git(*old.RAW, "--cached")
    raw_work = _git(*old.RAW)
    if head == P84:
        if committed != p84:
            _fail("P84 parent inventory changed")
        if index == p84:
            if untracked != ADDED:
                _fail("P85 missing or extra untracked source")
            _sealed._delta(raw_cached, p84, index, set())
            _sealed._delta(raw_work, index, expected, set(), work=True)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            _fail("partial stage or extra path")
        _sealed._delta(raw_cached, p84, expected, ADDED)
        _sealed._delta(raw_work, index, expected, set(), work=True)
        return "EXACT_STAGED"
    tree, parents = _sealed._commit(head)
    if (parents != [P84]
            or _git("rev-list", "--parents", "-n", "1", head)
            != (head + " " + P84 + "\n").encode("ascii")):
        _fail("not an exact one-commit P84 child")
    if (committed != expected or index != expected or untracked
            or tree != _sealed.prior._tree_oid(expected)):
        _fail("P85 exact child inventory or tree changed")
    _sealed._delta(raw_cached, committed, index, set())
    _sealed._delta(raw_work, index, expected, set(), work=True)
    _sealed._delta(_git(*old.RAW, P84, head), p84, expected, ADDED)
    return "EXACT_CHILD"


def assert_p85_offline_source_integrity():
    """Verify pinned Git+disk views; no permission for any effect or secret."""
    if _git("branch", "--show-current") != (BRANCH + "\n").encode("ascii"):
        _fail("wrong exact P85 review branch")
    head = _oid("rev-parse", "HEAD")
    p84 = _p84_baseline()
    expected = _expected(p84)
    committed = _sealed._tree(head)
    index, untracked = _sealed._working_inventory(committed)
    state = _prove(head, p84, expected, committed, index, untracked)
    if (_expected(p84) != expected
            or _sealed._tree(head) != committed
            or _sealed._working_inventory(committed) != (index, untracked)
            or _prove(head, p84, expected, committed, index, untracked) != state):
        _fail("TOCTOU source/index/inventory drift")
    if (_oid("rev-parse", "HEAD") != head
            or _git("branch", "--show-current") != (BRANCH + "\n").encode("ascii")):
        _fail("branch/HEAD drift")
    # Verify BOTH original annotated ancestor tags following live reads.
    old._tag()
    _sealed._tag()
    return state
