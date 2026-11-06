"""Exact Phase10.3 source admission. UNTESTED; no execution/release authority.

Only private historical parsers/readers are reused. No public predecessor
admission is invoked. Legacy refusal text remains a historical test contract.
Pins are literal source approval inputs, never learned during admission.
"""
from __future__ import annotations

import hashlib
import re

from tests import phase10_2_privacy_scope_migration as historical

prior = historical.prior
ROOT = historical.ROOT
BRANCH = "phase10-3-synthetic-provenance-redaction-20261104"
PARENT = "4aff3459ee127b0a7a124073aac2a9317e467301"
PARENT_TREE = "8f2054624120816d435b2cb567ef770759a3669f"
PARENT_PARENT = "be6c126dc5f3a6814925bb95009ef2b2e6be80b7"
PARENT_TAG = "nayeon-v1-phase-10-2-trusted-perception-privacy-01"
PARENT_TAG_OBJECT = "443b247b89b7fb5b749b0f938b98070339018863"
HISTORICAL_GUARD_SHA256 = "d628780e3f50bfb067febb1f3c838620da62906d50413a9d03f69d9950835416"
ADDED = frozenset({
    "tests/phase10_3_synthetic_provenance_fixture.py",
    "tests/phase10_3_independent_redaction_oracle.py",
    "tests/test_phase10_3_synthetic_provenance_redaction.py",
    "tests/phase10_3_scope_migration.py",
    "tests/test_phase10_3_scope_integrity.py",
    "docs/phase10_3_synthetic_provenance_redaction_rfc.md",
})
MODIFIED = frozenset({
    "tests/phase10_2_privacy_scope_migration.py",
    "tests/test_phase10_2_privacy_scope_integrity.py",
    "tests/test_phase10_perception_scope_integrity.py",
    "tests/test_phase_836_scope_integrity.py",
    "tests/test_phase_837_scope_integrity.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
    "tests/test_phase_834_scope_integrity.py",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase10_3_scope_migration.py"
SELF_PIN = re.compile(rb'("tests/phase10_3_scope_migration.py": ")[0-9a-f]{64}(",)')
CANDIDATE_SHA256 = {
    "tests/phase10_2_privacy_scope_migration.py": "3d54aa0e57baa5076fa8b6f167e3a906a1ebf7afd87f08e30752cb96b8a1522a",
    "tests/test_phase10_2_privacy_scope_integrity.py": "17619e875f49701259aa8018b11670824ac68e0b5edd4177e2e680ab89b16822",
    "tests/test_phase10_perception_scope_integrity.py": "2bb539600d6a88761dadd9b5da9ee1e6ce5a12fc03bf614705c33a480872867a",
    "tests/test_phase_836_scope_integrity.py": "ce75ba52401031cd871f902bdda191e6ea9e242408ffd07817b99e6c19724026",
    "tests/test_phase_837_scope_integrity.py": "a95a967ba892fecadf0811b38c51ae61cd268159766a91b1dc448cf4b1b5c426",
    "tests/test_phase_832_scope_integrity.py": "0a25f898ccb374b63b6cd68b0a3488c6f0d8656ec6ea6bae1fd225cabcf9a689",
    "tests/test_phase_833_scope_integrity.py": "8bdeecc1d14ffdcffa2b05b7e3e7409b00e0f211db5810fefb9ec96865a7531d",
    "tests/test_phase_834_scope_integrity.py": "8dc69ec770ea008dff9cd13e15299a73e38044f1671fd4fe78fbe2a431ccf57a",
    "tests/phase10_3_synthetic_provenance_fixture.py": "7bde88c71a18c8b4abb5972197df7c9e17c702554ef2d7bebec19b9930117230",
    "tests/phase10_3_independent_redaction_oracle.py": "33716444b753c94e3d489ec2b1f8d8459a4ef2a8245775960c64d732bc1635e6",
    "tests/test_phase10_3_synthetic_provenance_redaction.py": "5f1a70c2b0b031b49e140f81de34a8e4cd4f5b7232955d739505a9fddc8f3396",
    "tests/phase10_3_scope_migration.py": "3024d8d02a8c65fcfa626e1565649442c8943cb690442e8a7ac2a6453694fadc",
    "tests/test_phase10_3_scope_integrity.py": "ffe0de5a4dc08b42599faa4b4f546a4a9896270bb7e238e9b279dd6a98baaec6",
    "docs/phase10_3_synthetic_provenance_redaction_rfc.md": "bb576d18f64ada17759c7739b13392ff61b4ec4d88bdb43e9bdab9eaee286290",
}
RAW = historical.RAW


def _git(*args):
    return historical._git(*args)


def _disk(path):
    return historical._disk(path)


def _oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or not re.fullmatch(rb"[0-9a-f]{40}\n", raw):
        raise AssertionError("Phase10.3 malformed Git object ID")
    return raw[:-1].decode("ascii")


def _digest(path, raw):
    if type(raw) is not bytes:
        raise AssertionError("Phase10.3 source not bytes")
    if path == SELF:
        raw, count = SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], raw)
        if count != 1:
            raise AssertionError("Phase10.3 bad self-pin count")
    return hashlib.sha256(raw).hexdigest()


def _commit(oid):
    if _git("cat-file", "-t", oid) != b"commit\n":
        raise AssertionError("Phase10.3 wrong commit object kind")
    raw = _git("cat-file", "commit", oid)
    if prior._object("commit", raw) != oid or b"\n\n" not in raw:
        raise AssertionError("Phase10.3 forged raw commit")
    headers = raw.split(b"\n\n", 1)[0].split(b"\n")
    trees = [row[5:] for row in headers if row.startswith(b"tree ")]
    parents = [row[7:] for row in headers if row.startswith(b"parent ")]
    if (len(trees) != 1 or headers[0] != b"tree " + trees[0]
            or any(not re.fullmatch(rb"[0-9a-f]{40}", v) for v in trees + parents)):
        raise AssertionError("Phase10.3 malformed raw commit headers")
    return trees[0].decode("ascii"), [v.decode("ascii") for v in parents]


def _tree(commit):
    entries = prior.historical.prior._inventory(
        _git("ls-tree", "-r", "-z", "--full-tree", commit))
    tree, _ = _commit(commit)
    if prior._tree_oid(entries) != tree:
        raise AssertionError("Phase10.3 unauthenticated complete Git tree")
    return entries


def _tag():
    if (_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PARENT_TAG)
            != PARENT_TAG_OBJECT
            or _git("cat-file", "-t", PARENT_TAG_OBJECT) != b"tag\n"
            or _oid("rev-parse", "--verify", "--end-of-options",
                    PARENT_TAG_OBJECT + "^{}") != PARENT):
        raise AssertionError("Phase10.3 sealed parent tag mismatch")
    raw = _git("cat-file", "tag", PARENT_TAG_OBJECT)
    if (prior._object("tag", raw) != PARENT_TAG_OBJECT
            or raw.split(b"\n")[:3] != [
                ("object " + PARENT).encode(), b"type commit",
                ("tag " + PARENT_TAG).encode()]):
        raise AssertionError("Phase10.3 forged raw parent tag")


def _baseline():
    # Preserve the older historical query order, including the frozen 8.29
    # second-tree adversary. These helpers have no public-admission calls.
    before = historical._baseline()
    _tag()
    if (_commit(PARENT) != (PARENT_TREE, [PARENT_PARENT])
            or _oid("rev-parse", PARENT + "^{tree}") != PARENT_TREE):
        raise AssertionError("Phase10.3 sealed parent commit/tree mismatch")
    baseline = _tree(PARENT)
    if len(baseline) != 456 or prior._tree_oid(baseline) != PARENT_TREE:
        raise AssertionError("Phase10.3 historical 456-file inventory mismatch")
    original = _git("show", PARENT + ":" + historical.SELF)
    if hashlib.sha256(original).hexdigest() != HISTORICAL_GUARD_SHA256:
        raise AssertionError("Phase10.3 original historical guard changed")
    historical._manifest(before)
    expected = dict(before)
    for path, pin in historical.CANDIDATE_SHA256.items():
        raw = _git("show", PARENT + ":" + path)
        if (historical._digest(path, raw) != pin
                or baseline.get(path) != ("100644", prior._blob(raw))):
            raise AssertionError("Phase10.3 historical source pin mismatch: " + path)
        expected[path] = ("100644", prior._blob(raw))
    if expected != baseline:
        raise AssertionError("Phase10.3 historical full inventory drift")
    return baseline


def _manifest(baseline):
    if (len(ADDED) != 6 or len(MODIFIED) != 8 or len(ENVELOPE) != 14
            or ADDED & MODIFIED or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("Phase10.3 wrong exact manifest")
    if any(type(pin) is not str or not re.fullmatch(r"[0-9a-f]{64}", pin)
           or pin == "0" * 64 for pin in CANDIDATE_SHA256.values()):
        raise AssertionError("Phase10.3 unfinalized source pins")
    if (any(p in baseline for p in ADDED)
            or any(baseline.get(p, (None,))[0] != "100644" for p in MODIFIED)):
        raise AssertionError("Phase10.3 baseline path/mode mismatch")


def _expected(baseline):
    _manifest(baseline)
    expected = dict(baseline)
    for path, pin in CANDIDATE_SHA256.items():
        raw = _disk(path)
        if path == SELF:
            matches = tuple(SELF_PIN.finditer(raw))
            if (len(matches) != 1
                    or raw[matches[0].end(1):matches[0].start(2)] != pin.encode("ascii")):
                raise AssertionError("Phase10.3 self-pin literal mismatch")
        if _digest(path, raw) != pin:
            # Frozen older negative tests require this exact causal wording.
            raise AssertionError("Phase10.2 candidate byte mismatch: " + path)
        expected[path] = ("100644", prior._blob(raw))
        if path in MODIFIED and expected[path] == baseline[path]:
            raise AssertionError("Phase10.3 unchanged declared modification")
        if path == historical.SELF:
            sealed = _git("show", PARENT + ":" + path)
            if (len(raw) <= len(sealed) or not raw.startswith(sealed)
                    or prior._blob(sealed) != baseline[path][1]):
                raise AssertionError("Phase10.3 historical bytes not preserved")
    for path, (_, blob) in baseline.items():
        if path not in MODIFIED and prior._blob(_disk(path)) != blob:
            raise AssertionError("Phase10.2 frozen source modified: " + path)
    return expected


def _working_inventory(committed):
    return historical._working_inventory(committed, git=_git)


def _delta(raw, before, after, paths, *, work=False):
    return historical._delta(raw, before, after, paths, work=work)


def _prove_topology(head, baseline, expected, committed, index, untracked, raw_work):
    cached = _git(*RAW, "--cached")
    if head == PARENT:
        if committed != baseline:
            raise AssertionError("Phase10.3 parent changed")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("Phase10.3 missing/extra untracked source")
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
        raise AssertionError("Phase10.3 requires immediate sealed child")
    if committed != expected or index != expected or untracked:
        raise AssertionError("Phase10.2 unapproved child inventory")
    _delta(cached, committed, index, set())
    _delta(raw_work, index, expected, set(), work=True)
    _delta(_git(*RAW, PARENT, head), baseline, expected, ENVELOPE)
    return "EXACT_CHILD"


def assert_phase10_3_integrity():
    """Fresh admission; never fallback, mutate source, stage or execute it."""
    if _git("rev-parse", "--show-object-format") != b"sha1\n":
        raise AssertionError("Phase10.3 unsupported Git object format")
    if _git("branch", "--show-current") != (BRANCH + "\n").encode():
        raise AssertionError("Phase10 wrong exact branch")
    head = _oid("rev-parse", "HEAD")
    baseline = _baseline()
    expected = _expected(baseline)
    committed = _tree(head)
    index, untracked = _working_inventory(committed)
    result = _prove_topology(head, baseline, expected, committed, index,
                             untracked, _git(*RAW))
    # A second disk/index/raw proof detects changes across the read window.
    if (_expected(baseline) != expected
            or _tree(head) != committed
            or _working_inventory(committed) != (index, untracked)
            or _prove_topology(head, baseline, expected, committed, index,
                               untracked, _git(*RAW)) != result):
        raise AssertionError("Phase10.3 source changed during admission")
    if (head != _oid("rev-parse", "HEAD")
            or _git("branch", "--show-current") != (BRANCH + "\n").encode()):
        raise AssertionError("Phase10.3 ref changed during admission")
    if _git("show-ref", "--verify", "--hash", "--", "refs/tags/" +
            historical.PARENT_TAG) != (historical.PARENT_TAG_OBJECT + "\n").encode():
        raise AssertionError("Phase10.2 sealed parent tag changed during admission")
    _tag()
    return result


# P76 isolated offline successor experiment only. The original Phase10.3
# admission implementation above remains byte-for-byte preserved as a private
# historical witness. This prototype grants NO privileged effect authority.
_phase10_3_sealed_historical_assert = assert_phase10_3_integrity


def assert_phase10_3_integrity():
    """Current P76 offline source proof; no fallback after any denial."""
    from tests.phase8_byok_c1_p76_scope import assert_p76_offline_integrity
    return assert_p76_offline_integrity()
