"""Exact BYOK Phase 8 fake-only descendant admission, without a new phase number.

Pinned immutable parent, all prior seals, exact nine-file delta, all filesystem
bytes, index and Git commit objects. No provider/credential authority.
"""
from __future__ import annotations
import ast
import hashlib
import re
from tests import phase_8_37_scope_migration as prior

ROOT = prior.ROOT
PARENT = "87208af710bac90c440f2e0851854318b22e9b88"
PARENT_TREE = "417d4c88c76d542ee109d49a53fe522780bcebb3"
PARENT_TAG = "nayeon-v1-phase-8-37-local-provider-request-draft-01"
PARENT_TAG_OBJECT = "ee8ffc208be5626aecbb1b6c4955ad2a0cbdac63"
PARENT_PARENT = "a12565b9be070684e1d7d801ded4833d13121f94"
ADDED = frozenset({
    "nayeon/desktop_alpha/first_run_connection_owner.py",
    "tests/test_first_run_connection_owner.py",
    "tests/test_first_run_connection_effect_isolation.py",
    "tests/phase8_byok_scope_migration.py",
    "tests/test_phase8_byok_scope_integrity.py",
    "docs/phase8_first_run_connection_design.md",
})
MODIFIED = frozenset({
    "tests/phase_8_37_scope_migration.py",
    "tests/test_phase_837_scope_integrity.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/test_phase_836_scope_integrity.py",
    ".codex/CURRENT_STATE.md",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase8_byok_scope_migration.py"
SELF_PIN = re.compile(rb'("tests/phase8_byok_scope_migration.py": ")[0-9a-f]{64}(",)')
CANDIDATE_SHA256 = {
    ".codex/CURRENT_STATE.md": "9a81ed97ce49c524acd48bc5f3d3ad3fdf73e3b9493d227be61d26690817b8fa",
    "docs/phase8_first_run_connection_design.md": "e7f98bf248441db30f7a1d1177432285253d4ed0f8d7d9e690602fc40352fcc3",
    "nayeon/desktop_alpha/first_run_connection_owner.py": "704b968ad65368cde2ae2b6d7c73083c4a68219ba7436c4dee7eccde85493eca",
    "tests/phase8_byok_scope_migration.py": "d9d2dcaaa238b09013065c01bbe0228c850af05047c7381759b9869908ec9ac4",
    "tests/phase_8_30_scope_migration.py": "23d5b1a0a9e4f83ffd870f6b72693bb8878c85f94d8d7c142ca2a57fa0aeb218",
    "tests/phase_8_37_scope_migration.py": "79cbfffb932aea28321f017b76d26185774747a3d30cc0a7455530b6d01188cd",
    "tests/test_first_run_connection_effect_isolation.py": "1dc16125889467087fd0372fd8d3ec4e304ba8a5aa34bf844bed26c5aed665f4",
    "tests/test_first_run_connection_owner.py": "8dcead976d8b0e7f9a43ba955e6b69544a117d0d721ed7314f5823deb8dcf667",
    "tests/test_phase8_byok_scope_integrity.py": "2a6f888cd7a1059c0870a604541f9259d32243b37afea9038309f505b396e8e5",
    "tests/test_phase_836_scope_integrity.py": "2b7f0d1a14a57455ffd06e051e5ac076b4f2361902119fe58834f3a85fc7577b",
    "tests/test_phase_837_scope_integrity.py": "1110bcc403b96a47f6d29c4445a6e6419b69fd4f21c931bbd25ecb5ed415f2d8",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def _git(*args):
    return prior._git(*args)


def _oid(*args):
    data = _git(*args)
    if type(data) is not bytes or not re.fullmatch(rb"[0-9a-f]{40}\n?", data):
        raise AssertionError("Malformed BYOK object ID")
    return data.decode("ascii").rstrip("\n")


def _disk(path):
    return prior._disk(path)


def _no_effect_imports(path, data):
    """New strict BYOK bridge imports; old 8.31 guard stays unchanged."""
    try:
        tree = ast.parse(data.decode("utf-8", "strict"), filename=path)
    except (UnicodeError, SyntaxError):
        raise AssertionError("Invalid BYOK Python source") from None
    allowed = frozenset({
        "__future__", "dataclasses", "threading", "collections.abc",
        "nayeon.brain.onboarding_coordination",
        "nayeon.brain.onboarding_operation_advice",
        "nayeon.secrets.contracts",
    })
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        if any(name not in allowed for name in names):
            raise AssertionError("Unreviewed BYOK owner import")
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in {"eval", "exec", "__import__", "open"}):
            raise AssertionError("Dynamic BYOK import or IO")
    return True


def _raw_delta(raw, *, baseline, new):
    """Exact nine-file non-renamed Git delta; no older 20-path shortcut."""
    if type(raw) is not bytes or not raw.endswith(b"\0"):
        raise AssertionError("Malformed BYOK raw delta")
    records = raw.split(b"\0")
    if records[-1:] != [b""] or len(records) != 2*len(ENVELOPE)+1:
        raise AssertionError("Incomplete BYOK raw delta")
    touched = set()
    for metadata, path_bytes in zip(records[:-1:2], records[1:-1:2]):
        try:
            path = path_bytes.decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Malformed BYOK delta pathname") from None
        prior._path(path)
        if path not in ENVELOPE or path in touched:
            raise AssertionError("Unauthorized BYOK delta pathname")
        oldmode, oldoid = baseline.get(path, ("000000", "0"*40))
        newmode, newoid = new[path]
        expected = (f":{oldmode} {newmode} {oldoid} {newoid} "
                    + ("A" if path in ADDED else "M")).encode("ascii")
        if metadata != expected:
            raise AssertionError("Wrong BYOK Git delta status or identity")
        touched.add(path)
    if touched != ENVELOPE:
        raise AssertionError("Missing BYOK Git delta")


def _digest(path, data):
    if path == SELF:
        matches = list(SELF_PIN.finditer(data))
        if len(matches) != 1:
            raise AssertionError("Unbound BYOK self-pin")
        data = SELF_PIN.sub(rb'\g<1>' + b"0"*64 + rb'\g<2>', data)
    return hashlib.sha256(data).hexdigest()


def _parent_tree():
    # The *frozen* prior guard validates the complete 8.36 history.
    frozen = prior._seal()
    if _oid("rev-parse", PARENT + "^{tree}") != PARENT_TREE:
        raise AssertionError("BYOK parent tree mismatch")
    if _git("rev-list", "--parents", "-n", "1", PARENT).decode("ascii").split() != [
        PARENT, PARENT_PARENT
    ]:
        raise AssertionError("BYOK parent ancestry mismatch")
    if (_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PARENT_TAG)
            != PARENT_TAG_OBJECT
            or _git("cat-file", "-t", PARENT_TAG_OBJECT) != b"tag\n"
            or _oid("rev-parse", "--verify", "--end-of-options", PARENT_TAG_OBJECT+"^{}")
            != PARENT
            or _git("cat-file", "-t", PARENT) != b"commit\n"):
        raise AssertionError("BYOK protected annotated tag mismatch")
    parent = prior._tree(PARENT)
    expected = dict(frozen)
    if len(prior.ENVELOPE) != 20 or set(prior.CANDIDATE_SHA256) != prior.ENVELOPE:
        raise AssertionError("BYOK incomplete frozen 8.37 pins")
    for path, pin in prior.CANDIDATE_SHA256.items():
        data = _git("show", PARENT + ":" + path)
        if prior._digest(path, data) != pin or parent.get(path) != ("100644", prior._blob(data)):
            raise AssertionError("BYOK changed sealed 8.37 bytes: " + path)
        expected[path] = ("100644", prior._blob(data))
    if expected != parent:
        raise AssertionError("BYOK changed frozen inventory")
    return parent


def assert_byok_integrity():
    """Prove an exact unstaged/staged/one-child BYOK descendant, no bypass."""
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("BYOK unsupported Git format")
    head = _oid("rev-parse", "HEAD")
    if not HEX40.fullmatch(head):
        raise AssertionError("BYOK malformed HEAD")
    if _git("branch", "--show-current").decode().strip() != "nayeon-v1":
        raise AssertionError("Wrong 8.37 product branch")
    # Preserve the *existing* 8.31 ancestry-injection canary unchanged.
    _git("merge-base", "--is-ancestor", prior.PROTECTED, head)
    _git("merge-base", "--is-ancestor", PARENT, head)
    baseline = _parent_tree()
    committed = prior._tree(head)
    index = prior._index()
    prior._index_flags(index)
    untracked = prior._others("--exclude-standard")
    ignored = prior._others("--ignored", "--exclude-standard")
    disk_raw = _git("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
    prior._canonical_paths(set(committed) | set(index) | untracked | ignored)
    if ignored:
        raise AssertionError("BYOK ignored executable or source")
    if (len(ENVELOPE) != 11 or len(ADDED) != 6 or len(MODIFIED) != 5
            or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("BYOK unapproved manifest")
    if any(type(pin) is not str or not re.fullmatch(r"[a-f0-9]{64}", pin)
           or pin == "0"*64 for pin in CANDIDATE_SHA256.values()):
        raise AssertionError("BYOK unfinalized source pin")
    if any(path in baseline for path in ADDED):
        raise AssertionError("BYOK added path in prior seal")
    if any(baseline.get(path, ("",))[0] != "100644" for path in MODIFIED):
        raise AssertionError("BYOK invalid modified type")
    expected = dict(baseline)
    for path, pin in CANDIDATE_SHA256.items():
        data = _disk(path)
        if _digest(path, data) != pin:
            raise AssertionError("BYOK candidate byte mismatch: " + path)
        if path == "nayeon/desktop_alpha/first_run_connection_owner.py":
            _no_effect_imports(path, data)
        expected[path] = ("100644", prior._blob(data))
    for path, ref in baseline.items():
        if path not in MODIFIED:
            if committed.get(path) != ref or index.get(path) != ref:
                raise AssertionError("Frozen 8.37 historical file modified")
            if prior._blob(prior._frozen(path)) != ref[1]:
                raise AssertionError("BYOK frozen disk bytes modified")
    if head == PARENT:
        if committed != baseline:
            raise AssertionError("BYOK protected commit changed")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("BYOK unexpected untracked path")
            prior._raw_work(disk_raw, index, changed=MODIFIED)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            raise AssertionError("BYOK partial stage")
        prior._raw_work(disk_raw, index, changed=set())
        _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                    "--cached"), baseline=baseline, new=expected)
        return "EXACT_STAGED"
    if _git("rev-list", "--parents", "-n", "1", head).decode().split() != [head, PARENT]:
        raise AssertionError("BYOK unexpected commit parent")
    if committed != expected or index != expected or untracked:
        raise AssertionError("BYOK unapproved committed or staged inventory")
    prior._raw_work(disk_raw, index, changed=set())
    _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                PARENT, head), baseline=baseline, new=expected)
    return "EXACT_CHILD"


# Historical A body/pins above are immutable witnesses, never a LIVE fallback.
_assert_byok_historical = assert_byok_integrity


def assert_byok_integrity():
    """Public LIVE admission requires the exact twenty-path B successor."""
    from tests.phase8_byok_b_scope_migration import (
        assert_byok_a_current_source, assert_byok_b_integrity,
    )
    assert_byok_a_current_source()
    return assert_byok_b_integrity()
