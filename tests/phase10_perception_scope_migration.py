"""Phase 10.1 exact source admission; no execution or release authority.

SOURCE STATUS: the user-approved successor migration includes 32 exact paths
(six additions and 26 modifications) following a separate independent 30-file
review. Re-pin every final path after changing the candidate; a prior source
review remains HOLD until the complete 32-file evidence is independently cleared.
This guard never learns or updates source pins during live admission.

Open Failures & Prior-Issues Review (2026-11-01, design review + CURRENT_STATE):
- P10-BRANCH: original sealed B guard preserved byte-for-byte as a private
  historical witness. Public current admission routes unconditionally to this
  exact successor. Original branch-only assumptions are obsolete for live use.
- P10-REPLAY: authenticated sealed historical blobs and local synthetic branch
  context now exercise original 8.x fixtures. No bypass of immutable guards.
- P10-PROJECTION: exact two-source production projection and fourteen current
  live-branch assertions require this fresh admission; no inferred authority.
- P10-PINS: first 30-path candidate was pinned and passed 98/98 focused tests,
  but independent review identified seven obsolete legacy test expectations
  and issued SOURCE HOLD. User approved two additional bounded historical
  test paths. These 32 paths require fresh pins, causal negative tests and a
  new independent full-source review before any staging or release.
- Prior Tk/isolated-child incidents: preserve sealed thread/lifetime and -B
  controls; no source change, rerun cross-phase on host. Previous 82/82 is not
  full regression. Independent design approval is not final source review.
Affected current route: older public guards -> BYOK A -> BYOK B -> Phase10.
The provenance route calls private _parent_tree/_seal helpers only, preventing
public-admission recursion. Independent final source/security review, focused
adversaries, affected suites and native three-topology regressions are OPEN.
Disposition: HOLD; no product authority, source GO or release claim.
"""
from __future__ import annotations

import hashlib
import re
from tests import phase8_byok_b_scope_migration as historical

ROOT = historical.ROOT
BRANCH = "phase10-perception-foundation-20261101"
PARENT = "e3612279cb972e68e2487702183d5bf5b8f6c4a1"
PARENT_TREE = "99624a766e864addf5d096bb1a907c85d11401dc"
PARENT_PARENT = "4110fa69849f8127a325f9a9001284cd1bd3a59c"
PARENT_TAG = "nayeon-v1-phase8-byok-first-run-connection-ui-fake-only-01"
PARENT_TAG_OBJECT = "dab895740b3ab87aeb979a95f84151a9b2c7fe59"
ADDED = frozenset({
    "docs/phase10_perception_foundation_rfc.md",
    "nayeon/perception/__init__.py",
    "nayeon/perception/contracts.py",
    "tests/test_phase10_perception_contracts.py",
    "tests/phase10_perception_scope_migration.py",
    "tests/test_phase10_perception_scope_integrity.py",
})
MODIFIED = frozenset({
    ".codex/CURRENT_STATE.md",
    "tests/phase8_byok_b_scope_migration.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/test_phase8_byok_b_scope_integrity.py",
    "tests/test_phase8_byok_scope_integrity.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
    "tests/test_phase_834_scope_integrity.py",
    "tests/test_phase_836_scope_integrity.py",
    "tests/test_phase_837_scope_integrity.py",
    "tests/test_bound_credential_lifecycle.py",
    "tests/test_computer_control_v1_freeze.py",
    "tests/test_connection_reconciliation.py",
    "tests/test_credential_onboarding_composition.py",
    "tests/test_openai_canonical_client.py",
    "tests/test_presentation_configuration_bootstrap.py",
    "tests/test_presentation_configuration_persistence.py",
    "tests/test_presentation_configuration_service.py",
    "tests/test_presentation_configuration_view.py",
    "tests/test_presentation_identity_contracts.py",
    "tests/test_provider_connection_composition.py",
    "tests/test_provider_connection_service.py",
    "tests/test_provider_connection_startup.py",
    "tests/test_windows_credential_backend.py",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase10_perception_scope_migration.py"
SELF_PIN = re.compile(rb'("tests/phase10_perception_scope_migration.py": ")[0-9a-f]{64}(",)')
# Candidate approval pins, NOT the immutable historical B pins.
CANDIDATE_SHA256 = {
    ".codex/CURRENT_STATE.md": "4c4d36205cda2bd342e4ca5a0700ed6c207f086202ba64f4cc7f71af43712986",
    "docs/phase10_perception_foundation_rfc.md": "2dd74df3b8a6d23f27205f2fbb3baf524970b9a03305924a2fff69c95bfa939a",
    "nayeon/perception/__init__.py": "3b856b291d402f4178ce57f3d264ab6108c21c994630450ff0c3f8fb1446f964",
    "nayeon/perception/contracts.py": "22e157ecb066e6011ac92ed46110479ca5ca9044964602629973f87ce26d1c8e",
    "tests/test_phase10_perception_contracts.py": "053183377223bb117603df686c4eb2df05ff9028d817765672b0d59e64edea6a",
    "tests/phase10_perception_scope_migration.py": "c631500f1098980b7f523f8221c5b77f2cd8266293fc0831e4f4beac9b276b3d",
    "tests/test_phase10_perception_scope_integrity.py": "b29d715c502fa7e8d1e18bbff23f58abc7ec0ca21dd7900fd484ce4308dedd98",
    "tests/phase8_byok_b_scope_migration.py": "84ced2f31f5daf985de462c384abdfe47f8b705425f8bdefb8cf1e04e56ee010",
    "tests/phase_8_30_scope_migration.py": "330c21469d4879ae4a17ffdf39ed80a6789936910fd48cbd933dd5634fba580e",
    "tests/test_phase8_byok_b_scope_integrity.py": "7e6f8f0f1abac47962853b1654f0e97957c2a2b4c893e8461c07f823102e0b70",
    "tests/test_phase8_byok_scope_integrity.py": "9d5dcabce713706de0d77932675e3958d445502aaece31090f32a6123418dcb2",
    "tests/test_phase_830_scope_integrity.py": "7180e5ab84fde02c0cd21b91546b1c384c3b62497aa55e2cc4860bb8dcd5ee5f",
    "tests/test_phase_831_scope_integrity.py": "41e23e31d06f699129bd274a29de103a1917c7e1754b3b0edda9658be15ad20c",
    "tests/test_phase_832_scope_integrity.py": "64f6f464251821ff7ea0bc5c9cea8d76e32d53250790425bebfc907f78e84074",
    "tests/test_phase_833_scope_integrity.py": "cc1d0931ccc1887f1c17c1d4a502fd42118464c6924a5d372d9438e4ba893d36",
    "tests/test_phase_834_scope_integrity.py": "69b72831bf0e3025a68197c2cb1ce1217c69e8dcec5d3d95e69199f4998c1d04",
    "tests/test_phase_836_scope_integrity.py": "b57710e4ad3975fa82d4e97b207393dafd722a34313a241bee4a1c3191ccec22",
    "tests/test_phase_837_scope_integrity.py": "5685628080b058e30c0e7cd22e7c6dbd518682b45a0ff2405f75e4c1f1974fc2",
    "tests/test_bound_credential_lifecycle.py": "b8d6377f4850e5b4725969ce7c22ff5477d6e75b00d17bf315df1a857e27f6f1",
    "tests/test_computer_control_v1_freeze.py": "92596592874cd03be4378bece51200f57e1dded199c2d1832f599ea45d5d5c55",
    "tests/test_connection_reconciliation.py": "ceda6ba8bb73d604d194ad1ecf91a91e519316817d24dee04e1b21dd0367a7fa",
    "tests/test_credential_onboarding_composition.py": "55b89fb8fb1c9a86045dea34c8905aefe40bd7477086519c1be7629eaee9a88d",
    "tests/test_openai_canonical_client.py": "d3a4ba14ef21efd8438ddc9af6c1bbad502ee09acccb68549d531f8e0ce57092",
    "tests/test_presentation_configuration_bootstrap.py": "c0ab30e8e20cfc63f3599158f5cf7cca97bb66ef17f8aa05dc3c63561982c4dc",
    "tests/test_presentation_configuration_persistence.py": "4a5c7b9fbc0fc0e0a4abba32adeeef3da41734401c05f947651d2ec7d7625aa3",
    "tests/test_presentation_configuration_service.py": "78d7aa2812221d167beef7ce94dca6536a2430fe09e789074e11a46177556e3a",
    "tests/test_presentation_configuration_view.py": "b6c2aa54c8bdb828631a74c1151027ad07bdd61212be24ad5894aebd36b5cde5",
    "tests/test_presentation_identity_contracts.py": "c12cc9fc43c99528b06c92b7e5ec6b59105f973e043b3de8c6e388761d03c969",
    "tests/test_provider_connection_composition.py": "b687599646ce0d6dbb9fc349a9d0ecf3bb7b31133b76ee6f8e51e284ca29f8c6",
    "tests/test_provider_connection_service.py": "9ad3ec32da9ff684ec5ca7d08ef06cb3b81bf1f16e9b7473b20f86dd4c626e44",
    "tests/test_provider_connection_startup.py": "dabe1e857e51f1a81f53b8decffee5d42bac9e8dc42b7a2a7c6929c230c68624",
    "tests/test_windows_credential_backend.py": "49c9ba8ceb25db721dbf91ebdbcad30eed498be63273436bc194de7b069cc731",
}
RAW = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")


def _git(*args):
    return historical._git(*args)


def _oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or not re.fullmatch(rb"[0-9a-f]{40}\n", raw):
        raise AssertionError("Phase10 malformed object ID")
    return raw[:-1].decode("ascii")


def _object(kind, raw):
    if type(raw) is not bytes:
        raise AssertionError("Phase10 non-byte Git object")
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(raw)).encode("ascii")
                        + b"\0" + raw).hexdigest()


def _blob(raw):
    return _object("blob", raw)


def _disk(path):
    # Both frozen and candidate bytes use the SAME real no-link raw reader.
    historical.prior._path(path)
    return historical.prior._disk(path)


def _digest(path, raw):
    if type(raw) is not bytes:
        raise AssertionError("Phase10 non-byte source")
    if path == SELF:
        raw, count = SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], raw)
        if count != 1:
            raise AssertionError("Phase10 self-pin must occur exactly once")
    return hashlib.sha256(raw).hexdigest()


def _tree_oid(entries):
    """Reconstruct real raw tree objects, binding the complete flat inventory."""
    historical.prior._canonical_paths(entries)
    root = {}
    for path, (mode, oid) in entries.items():
        if mode not in {"100644", "100755"} or not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise AssertionError("Phase10 invalid tree entry")
        parts = path.split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if type(node) is not dict:
                raise AssertionError("Phase10 file/directory alias")
        if parts[-1] in node:
            raise AssertionError("Phase10 file/directory alias")
        node[parts[-1]] = (mode, oid)

    def tree(node):
        rows = []
        for name, value in node.items():
            directory = type(value) is dict
            mode, oid = ("40000", tree(value)) if directory else value
            encoded = name.encode("utf-8", "strict")
            rows.append((encoded + (b"/" if directory else b""),
                         mode.encode("ascii") + b" " + encoded + b"\0"
                         + bytes.fromhex(oid)))
        return _object("tree", b"".join(row for _, row in sorted(rows)))
    return tree(root)


def _commit(oid):
    if _git("cat-file", "-t", oid) != b"commit\n":
        raise AssertionError("Phase10 wrong commit object type")
    raw = _git("cat-file", "commit", oid)
    if _object("commit", raw) != oid or b"\n\n" not in raw:
        raise AssertionError("Phase10 forged raw commit")
    headers = raw.split(b"\n\n", 1)[0].split(b"\n")
    trees = [row[5:] for row in headers if row.startswith(b"tree ")]
    parents = [row[7:] for row in headers if row.startswith(b"parent ")]
    if len(trees) != 1 or headers[0] != b"tree " + trees[0] or any(
            not re.fullmatch(rb"[0-9a-f]{40}", value) for value in trees + parents):
        raise AssertionError("Phase10 malformed commit headers")
    return trees[0].decode("ascii"), [p.decode("ascii") for p in parents]


def _tree(commit):
    entries = historical.prior._inventory(
        _git("ls-tree", "-r", "-z", "--full-tree", commit))
    tree, _ = _commit(commit)
    if _tree_oid(entries) != tree:
        raise AssertionError("Phase10 unauthenticated complete tree")
    return entries


def _baseline():
    if (_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PARENT_TAG)
            != PARENT_TAG_OBJECT
            or _git("cat-file", "-t", PARENT_TAG_OBJECT) != b"tag\n"
            or _oid("rev-parse", "--verify", "--end-of-options", PARENT_TAG_OBJECT + "^{}")
            != PARENT):
        raise AssertionError("Phase10 B annotated tag mismatch")
    tag = _git("cat-file", "tag", PARENT_TAG_OBJECT)
    if (_object("tag", tag) != PARENT_TAG_OBJECT or tag.split(b"\n")[:3] != [
            ("object " + PARENT).encode(), b"type commit", ("tag " + PARENT_TAG).encode()]):
        raise AssertionError("Phase10 forged raw B tag")
    if (_commit(PARENT) != (PARENT_TREE, [PARENT_PARENT])
            or _oid("rev-parse", PARENT + "^{tree}") != PARENT_TREE):
        raise AssertionError("Phase10 B commit/tree/parent mismatch")
    # Only private historical provenance helpers, NEVER public live admission.
    before_b = historical._parent_tree()
    baseline = _tree(PARENT)
    expected = dict(before_b)
    if (len(historical.ENVELOPE) != 23
            or set(historical.CANDIDATE_SHA256) != historical.ENVELOPE):
        raise AssertionError("Phase10 incomplete historical B pins")
    for path, pin in historical.CANDIDATE_SHA256.items():
        raw = _git("show", PARENT + ":" + path)
        if (historical._digest(path, raw) != pin
                or baseline.get(path) != ("100644", _blob(raw))):
            raise AssertionError("Phase10 altered sealed B file: " + path)
        expected[path] = ("100644", _blob(raw))
    if baseline != expected:
        raise AssertionError("Phase10 altered frozen B inventory")
    return baseline


def _manifest(baseline):
    if (len(ADDED) != 6 or len(MODIFIED) != 26 or len(ENVELOPE) != 32
            or not ADDED.isdisjoint(MODIFIED) or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("Phase10 unapproved thirty-two-path manifest")
    if any(type(pin) is not str or not re.fullmatch(r"[0-9a-f]{64}", pin)
           or pin == "0" * 64 for pin in CANDIDATE_SHA256.values()):
        raise AssertionError("Phase10 source-open: unfinalized candidate pins")
    if any(p in baseline for p in ADDED) or any(
            baseline.get(p, (None,))[0] != "100644" for p in MODIFIED):
        raise AssertionError("Phase10 wrong baseline path or mode")


def _expected(baseline):
    _manifest(baseline)
    expected = dict(baseline)
    for path, pin in CANDIDATE_SHA256.items():
        raw = _disk(path)
        if _digest(path, raw) != pin:
            raise AssertionError("Phase10 candidate byte mismatch: " + path)
        expected[path] = ("100644", _blob(raw))
        if path in MODIFIED and expected[path] == baseline[path]:
            raise AssertionError("Phase10 incomplete modified scope: " + path)
        if path == ".codex/CURRENT_STATE.md":
            suffix = _git("show", PARENT + ":" + path)
            if (hashlib.sha256(suffix).hexdigest() != historical.CANDIDATE_SHA256[path]
                    or _blob(suffix) != baseline[path][1]
                    or len(raw) <= len(suffix) or not raw.endswith(suffix)):
                raise AssertionError("Phase10 context must preserve sealed B suffix")
    for path, (_, oid) in baseline.items():
        if path not in MODIFIED and _blob(_disk(path)) != oid:
            raise AssertionError("Phase10 frozen B disk bytes modified: " + path)
    return expected


def _delta(raw, before, after, paths, *, work=False):
    if raw == b"" and not paths:
        return
    if type(raw) is not bytes or not raw.endswith(b"\0"):
        raise AssertionError("Phase10 malformed raw delta")
    rows = raw.split(b"\0")
    if len(rows) != 2 * len(paths) + 1:
        raise AssertionError("Phase10 incomplete raw delta")
    seen = set()
    for meta, encoded in zip(rows[:-1:2], rows[1:-1:2]):
        try:
            path = encoded.decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Phase10 malformed raw path") from None
        historical.prior._path(path)
        if path not in paths or path in seen:
            raise AssertionError("Phase10 undeclared or repeated raw path")
        om, oi = before.get(path, ("000000", "0" * 40))
        nm, ni = (om, "0" * 40) if work else after[path]
        status = "A" if path not in before else "M"
        if meta != f":{om} {nm} {oi} {ni} {status}".encode("ascii"):
            raise AssertionError("Phase10 wrong raw mode/status/blob")
        seen.add(path)
    if seen != set(paths):
        raise AssertionError("Phase10 missing raw path")


def _prove_topology(head, baseline, expected, committed, index, untracked, disk_raw):
    # Call only after full source/manifest proof. Kept separate for parser tests.
    cached = _git(*RAW, "--cached")
    if head == PARENT:
        if committed != baseline:
            raise AssertionError("Phase10 changed B HEAD inventory")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("Phase10 wrong untracked additions")
            _delta(cached, baseline, index, set())
            _delta(disk_raw, index, expected, MODIFIED, work=True)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            raise AssertionError("Phase10 partial stage")
        _delta(cached, baseline, expected, ENVELOPE)
        _delta(disk_raw, index, expected, set(), work=True)
        return "EXACT_STAGED"
    _, parents = _commit(head)
    if parents != [PARENT] or _git("rev-list", "--parents", "-n", "1", head) != (
            head + " " + PARENT + "\n").encode("ascii"):
        raise AssertionError("Phase10 requires immediate single B child")
    if committed != expected or index != expected or untracked:
        raise AssertionError("Phase10 unapproved child/index inventory")
    _delta(cached, committed, index, set())
    _delta(disk_raw, index, expected, set(), work=True)
    _delta(_git(*RAW, PARENT, head), baseline, expected, ENVELOPE)
    return "EXACT_CHILD"


def _working_inventory(committed):
    """Validate every raw index/other pathname before any scope comparison."""
    index = historical.prior._inventory(_git("ls-files", "--stage", "-z"), index=True)
    # Reuse pure parsers, but keep ALL live reads at this successor's _git seam.
    flags = _git("ls-files", "-v", "--sparse", "-z")
    if type(flags) is not bytes or flags and not flags.endswith(b"\0"):
        raise AssertionError("Phase10 malformed index flags")
    rows = flags.split(b"\0")[:-1]
    if any(not row.startswith(b"H ") for row in rows):
        raise AssertionError("Phase10 hidden index flags")
    names = historical.prior._paths(b"".join(row[2:] + b"\0" for row in rows))
    if names != set(index):
        raise AssertionError("Phase10 incomplete index flags")
    untracked = historical.prior._paths(
        _git("ls-files", "--others", "--exclude-standard", "-z"))
    ignored = historical.prior._paths(
        _git("ls-files", "--others", "--ignored", "--exclude-standard", "-z"))
    historical.prior._canonical_paths(set(committed) | set(index) | untracked | ignored)
    if ignored:
        raise AssertionError("Phase10 ignored source or executable")
    return index, untracked


def assert_phase10_integrity():
    """Fresh full admission; historical refusal is never a fallback."""
    if _git("rev-parse", "--show-object-format") != b"sha1\n":
        raise AssertionError("Phase10 unsupported object format")
    if _git("branch", "--show-current") != (BRANCH + "\n").encode("ascii"):
        raise AssertionError("Phase10 wrong exact branch")
    head = _oid("rev-parse", "HEAD")
    baseline = _baseline()
    expected = _expected(baseline)
    committed = _tree(head)
    index, untracked = _working_inventory(committed)
    result = _prove_topology(head, baseline, expected, committed, index, untracked,
                             _git(*RAW))
    # Detect ref drift across this read-only proof; no cached success.
    if (_oid("rev-parse", "HEAD") != head
            or _git("branch", "--show-current") != (BRANCH + "\n").encode("ascii")):
        raise AssertionError("Phase10 ref changed during admission")
    return result
