"""P76 exact offline C1 source successor PROTOTYPE; not release authority.

Authenticates a single one-commit child of sealed Phase10.3 across full
Git source/index/disk/tag views. This does not permit credentials, service,
provider access or provider validation. Independent security review required.
"""
from __future__ import annotations

import hashlib
import re
from tests import phase10_3_scope_migration as sealed

ROOT = sealed.ROOT
BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
PARENT = "cacb5c320d26ffa28faf1f15a5e088029ee1453b"
PARENT_TREE = "0773c02397b96de1ad4080017e6c8f58ed192a91"
PARENT_PARENT = "4aff3459ee127b0a7a124073aac2a9317e467301"
PARENT_TAG = "nayeon-v1-phase-10-3-synthetic-provenance-redaction-01"
PARENT_TAG_OBJECT = "ed68953eaacee301592c6349a590a17be9638be5"
PARENT_COUNT = 462
SELF = "tests/phase8_byok_c1_p76_scope.py"
TEST = "tests/test_phase8_byok_c1_p76_scope.py"
ROUTE = "tests/phase10_3_scope_migration.py"
HISTORICAL_TEST = "tests/test_phase10_3_scope_integrity.py"
ADDED = frozenset({
    "nayeon/brain/pending_credential_policy.py",
    "nayeon/brain/pending_credential_recovery_document.py",
    "tests/test_pending_credential_policy.py",
    "tests/test_pending_credential_recovery_document.py",
    "tests/test_byok_c1_p73_offline_boundary.py",
    "tests/test_phase8_byok_c1_p77_historical_compat.py",
    SELF,
    TEST,
})
MODIFIED = frozenset({ROUTE, HISTORICAL_TEST})
ENVELOPE = ADDED | MODIFIED
RAW = sealed.RAW
SELF_PIN = re.compile(
    rb'("tests/phase8_byok_c1_p76_scope.py":\s*")[A-F0-9]{64}(",)'
)
CANDIDATE_SHA256 = {
    "nayeon/brain/pending_credential_policy.py":
        "747DA9F31633F0A76BD559ADF01CA9E5338154ADD4E380C3A80758BD3D18AFCD",
    "nayeon/brain/pending_credential_recovery_document.py":
        "9B4E98E2C8B39910E1D8A510F421FCB350C32D6FE2BFB6A54C4C34E1063F1DE9",
    "tests/test_pending_credential_policy.py":
        "62D33BCD5FD9AA85B0EC64419B3232755828FE1DFC21B18278848DD35EA105D0",
    "tests/test_pending_credential_recovery_document.py":
        "5DC21BBA0AF8383CD3754193191FC3ED67E3EC9C3699D98847D3CB889122EFCA",
    "tests/test_byok_c1_p73_offline_boundary.py":
        "B458CBA7022C46A0221B32FD3D6E6BA152BC698C26E79B09AF724457FA1AFAFE",
    "tests/phase8_byok_c1_p76_scope.py":
        "87353B0ED0B51A37B578681343C39626829877348A90EBA7F6F86014F1FEF740",
    "tests/test_phase8_byok_c1_p76_scope.py":
        "EE6BB4CECC5D8A388623B635B8172CA7C526D87F284FEB6B09A5E3E74F651E2D",
    "tests/phase10_3_scope_migration.py":
        "540A1BE7C6FF23929B17E8A2F8272083829A65C35A76D1755A5284C958AFBEFF",
    "tests/test_phase8_byok_c1_p77_historical_compat.py":
        "16B93E6D31E0CEAB629BE191E65870218E3F68455E2B8054EEA74388794ABD6A",
    "tests/test_phase10_3_scope_integrity.py":
        "546E5C34D5CEAEAB62571B7A0B6EEC84C4442014F0A37A483235FE8A632C7A82",
}


class P76ScopeRefused(AssertionError):
    """Nonsecret source gate denial; never a consent or effect capability."""


def _fail(cause):
    raise P76ScopeRefused("P76 offline source refused: " + cause)


def _git(*args):
    return sealed._git(*args)


def _disk(path):
    return sealed._disk(path)


def _oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or re.fullmatch(rb"[0-9a-f]{40}\n", raw) is None:
        _fail("malformed Git object identifier")
    return raw[:-1].decode("ascii")


def _digest(path, raw):
    if type(raw) is not bytes:
        _fail("non-byte source")
    if path == SELF:
        matches = tuple(SELF_PIN.finditer(raw))
        if len(matches) != 1:
            _fail("wrong normalized self pin syntax")
        raw, count = SELF_PIN.subn(
            lambda m: m[1] + b"0" * 64 + m[2], raw
        )
        if count != 1:
            _fail("wrong normalized self pin count")
    return hashlib.sha256(raw).hexdigest().upper()


def _tag():
    oid = _oid("show-ref", "--verify", "--hash", "--",
               "refs/tags/" + PARENT_TAG)
    if oid != PARENT_TAG_OBJECT or _git("cat-file", "-t", oid) != b"tag\n":
        _fail("sealed Phase10.3 annotated tag reference changed")
    raw = _git("cat-file", "tag", oid)
    if (sealed.prior._object("tag", raw) != oid
            or raw.split(b"\n")[:3] != [
                ("object " + PARENT).encode("ascii"),
                b"type commit",
                ("tag " + PARENT_TAG).encode("ascii"),
            ]
            or _oid("rev-parse", "--verify", "--end-of-options", oid + "^{}")
            != PARENT):
        _fail("sealed Phase10.3 raw tag mismatch")


def _baseline():
    # Authenticated full Phase10.2 ancestor chain, including its original
    # tag/raw-object/tree checks. This is source provenance, not a fallback
    # to a historical LIVE branch verifier.
    prior_tree = sealed._baseline()
    sealed._manifest(prior_tree)
    _tag()
    if (_git("rev-parse", "--show-object-format") != b"sha1\n"
            or sealed._commit(PARENT) != (PARENT_TREE, [PARENT_PARENT])
            or _oid("rev-parse", PARENT + "^{tree}") != PARENT_TREE):
        _fail("sealed Phase10.3 parent commit/tree drift")
    base = sealed._tree(PARENT)
    if len(base) != PARENT_COUNT:
        _fail("sealed Phase10.3 frozen file-count drift")
    # Reconstruct the complete sealed Phase10.3 parent from authenticated
    # Phase10.2 history and its original immutable Phase10.3 source pins.
    reconstructed = dict(prior_tree)
    for p, pin in sealed.CANDIDATE_SHA256.items():
        original = _git("show", PARENT + ":" + p)
        if (sealed._digest(p, original) != pin
                or base.get(p) != ("100644", sealed.prior._blob(original))):
            _fail("sealed Phase10.3 historical manifest drift: " + p)
        reconstructed[p] = ("100644", sealed.prior._blob(original))
    if reconstructed != base:
        _fail("sealed Phase10.3 complete historical tree drift")
    return base


def _expected(base):
    if (len(ADDED) != 8 or len(MODIFIED) != 2
            or len(ENVELOPE) != 10
            or set(CANDIDATE_SHA256) != ENVELOPE
            or ADDED & MODIFIED or SELF not in ADDED
            or TEST not in ADDED
            or any(path in base for path in ADDED)
            or any(base.get(path, (None,))[0] != "100644" for path in MODIFIED)):
        _fail("unapproved exact successor manifest")
    # The old sealed route is authenticated from the original Git blob,
    # NOT inferred from untrusted live worktree bytes. Its historical self
    # pin remains an independent test contract even after an append-only
    # current-route successor has been installed.
    original = _git("show", PARENT + ":" + ROUTE)
    routed = _disk(ROUTE)
    old_pins = tuple(sealed.SELF_PIN.finditer(original))
    live_pins = tuple(sealed.SELF_PIN.finditer(routed))
    if (len(old_pins) != 1 or len(live_pins) != 1
            or live_pins[0].group(0) != old_pins[0].group(0)):
        raise AssertionError("Phase10.3 self-pin literal mismatch")
    if (not routed.startswith(original) or len(routed) <= len(original)
            or base[ROUTE][1] != sealed.prior._blob(original)):
        raise AssertionError("Phase10.2 candidate byte mismatch: " + ROUTE)
    result = dict(base)
    for path, pin in CANDIDATE_SHA256.items():
        if (type(pin) is not str or
                re.fullmatch(r"[A-F0-9]{64}", pin) is None or
                pin == "0" * 64):
            _fail("unreviewed candidate SHA256")
        raw = routed if path == ROUTE else _disk(path)
        if path == SELF:
            matches = tuple(SELF_PIN.finditer(raw))
            if (len(matches) != 1
                    or pin.encode("ascii") not in matches[0].group(0)):
                _fail("self literal pin mismatch")
        if _digest(path, raw) != pin:
            # Preserve the original refusal contract for the historical
            # Phase10.3 candidate route. No success fallback is allowed.
            if path == ROUTE:
                raise AssertionError("Phase10.2 candidate byte mismatch: " + path)
            _fail("candidate byte mismatch: " + path)
        result[path] = ("100644", sealed.prior._blob(raw))
    # Old source is still frozen. Preserve precise historical failure causes
    # for its original candidate set, distinct from older frozen sources.
    for path, (_, blob) in base.items():
        if path in MODIFIED:
            continue
        if sealed.prior._blob(_disk(path)) != blob:
            if path in sealed.ENVELOPE:
                raise AssertionError("Phase10.2 candidate byte mismatch: " + path)
            raise AssertionError("Phase10.2 frozen source modified: " + path)
    return result


def _proof(head, base, expected, committed, index, untracked):
    cached = _git(*RAW, "--cached")
    working = _git(*RAW)
    if head == PARENT:
        if committed != base:
            _fail("parent commit inventory mismatch")
        if index == base:
            if untracked != ADDED:
                _fail("missing/extra untracked source")
            sealed._delta(cached, base, index, set())
            sealed._delta(working, index, expected, MODIFIED, work=True)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            _fail("partial staged or extra path")
        sealed._delta(cached, base, expected, ENVELOPE)
        sealed._delta(working, index, expected, set(), work=True)
        return "EXACT_STAGED"
    tree, parents = sealed._commit(head)
    if (parents != [PARENT] or
            _git("rev-list", "--parents", "-n", "1", head) !=
            (head + " " + PARENT + "\n").encode("ascii")):
        _fail("not exact one-commit Phase10.3 child")
    if committed != expected or index != expected or untracked:
        # Historical exact-child negative fixtures require the original
        # causal refusal, with no relaxation of the topology check.
        raise AssertionError("Phase10.2 unapproved child inventory")
    sealed._delta(cached, committed, index, set())
    sealed._delta(working, index, expected, set(), work=True)
    sealed._delta(_git(*RAW, PARENT, head), base, expected, ENVELOPE)
    return "EXACT_CHILD"


def assert_p76_offline_integrity():
    """Pure read-only offline source admission; NO credential authority."""
    if _git("branch", "--show-current") != (BRANCH + "\n").encode("ascii"):
        _fail("wrong exact P76 prototype branch")
    head = _oid("rev-parse", "HEAD")
    baseline = _baseline()
    expected = _expected(baseline)
    committed = sealed._tree(head)
    index, untracked = sealed._working_inventory(committed)
    result = _proof(head, baseline, expected, committed, index, untracked)
    if (_expected(baseline) != expected
            or sealed._tree(head) != committed
            or sealed._working_inventory(committed) != (index, untracked)
            or _proof(head, baseline, expected, committed, index, untracked)
            != result):
        _fail("source or Git metadata drift during admission")
    if (_oid("rev-parse", "HEAD") != head
            or _git("branch", "--show-current") !=
            (BRANCH + "\n").encode("ascii")):
        _fail("branch or head drift")
    _tag()
    # P77: revalidate the original Phase10.2 annotated tag as well as the
    # Phase10.3 tag AFTER the live source/index/ref read window. This is
    # a second actual Git ref and raw tag proof, never a cached approval.
    sealed._tag()
    return result
