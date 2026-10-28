"""Exact BYOK Phase 8 fake-only descendant admission, without a new phase number.

Pinned immutable parent, all prior seals, exact twenty-three-file delta, all filesystem
bytes, index and Git commit objects. No provider/credential authority.
"""
from __future__ import annotations
import ast
import hashlib
import re
from tests import phase8_byok_scope_migration as historical

prior = historical.prior

ROOT = prior.ROOT
PARENT = "4110fa69849f8127a325f9a9001284cd1bd3a59c"
PARENT_TREE = "747f172144794d687251545ca923d5ebb5b1551b"
PARENT_TAG = "nayeon-v1-phase8-byok-first-run-owner-fake-only-01"
PARENT_TAG_OBJECT = "7496961c83de9607402dcdabff25917674d6688a"
PARENT_PARENT = "87208af710bac90c440f2e0851854318b22e9b88"
ADDED = frozenset({
    "docs/phase8_first_run_connection_ui_design.md",
    "nayeon/desktop_alpha/first_run_connection_window.py",
    "tests/phase8_byok_b_scope_migration.py",
    "tests/test_first_run_connection_application.py",
    "tests/test_first_run_connection_cancelled_effect.py",
    "tests/test_first_run_connection_window.py",
    "tests/test_phase8_byok_b_scope_integrity.py",
})
MODIFIED = frozenset({
    ".codex/CURRENT_STATE.md",
    "nayeon/brain/onboarding_coordination.py",
    "nayeon/brain/onboarding_recovery.py",
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/first_run_connection_owner.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/phase_8_37_scope_migration.py",
    "tests/phase8_byok_scope_migration.py",
    "tests/test_first_run_connection_effect_isolation.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
    "tests/test_phase_834_scope_integrity.py",
    "tests/test_phase_836_scope_integrity.py",
    "tests/test_phase_837_scope_integrity.py",
    "tests/test_phase8_byok_scope_integrity.py",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase8_byok_b_scope_migration.py"
SELF_PIN = re.compile(rb'("tests/phase8_byok_b_scope_migration.py": ")[0-9a-f]{64}(",)')
CANDIDATE_SHA256 = {
    ".codex/CURRENT_STATE.md": "ecb30dd2d59a33cc34ea79b0c9f5350fe10c2bb4e43cac2b3d07e8dad3cdba65",
    "docs/phase8_first_run_connection_ui_design.md": "04b37aee29abbfb350e80ccec65458556adaa4e1d3b3878d50597105a5098327",
    "nayeon/brain/onboarding_coordination.py": "af479aa7597e036b84a5f21644182ea3bae2ba584d4c310c070aafb70ffddf15",
    "nayeon/brain/onboarding_recovery.py": "dbb2963de50326422c08ce0d46fec5920b6548d1210e0772429ea36c6d4a0738",
    "nayeon/desktop_alpha/application.py": "af9bb617b67e56d2a71ae796af0f0846670303d0e192187a0ed6706127f73a82",
    "nayeon/desktop_alpha/first_run_connection_owner.py": "d3fb11f2c0095bb4e98d2a5339bb04f1ba73b286159083d32e6ccd07c2ee3e04",
    "nayeon/desktop_alpha/first_run_connection_window.py": "865fa15854591f151b2a6c17ef392636a0ea9950441c531b463c931e72bc1b32",
    "nayeon/desktop_alpha/workspace_window.py": "b7e78df7b0a786c0b4c5b19ec3a91f003f0995e496069e718c7389ff5871111c",
    "tests/phase8_byok_b_scope_migration.py": "7aa013c3400b4032087ad6f769d5ce0cb727d628586bb4f4cc4fdbca5c6f246c",
    "tests/phase8_byok_scope_migration.py": "7eaa989e141e17c7303ede283b3a979dc77680fa5b74d86a75dc8233ea4324b1",
    "tests/phase_8_30_scope_migration.py": "7fab9ace158264bdbf1c40838218576314649249ae8c89ecb5b52522c81562f3",
    "tests/phase_8_37_scope_migration.py": "3f0ef3592754734e1050e5ce57aef50ce48de4b768019d72f6590ea3f73ddcaa",
    "tests/test_first_run_connection_application.py": "3c32da2c334dbda0acfe6911aee200d27648d4d71fb08ba5c665acfac11d2849",
    "tests/test_first_run_connection_cancelled_effect.py": "26aa5cd65647316e9878b3ac2a0f89e739823923bee20cc0c9a0ce54c02c375a",
    "tests/test_first_run_connection_effect_isolation.py": "26b78138366ee6ec4cb8115c36e03d4dfa90a541ff5b9b3505a7f59c244cada7",
    "tests/test_first_run_connection_window.py": "5c1fce9f76ba1d255ba3f4432da9ccef5edeb16717d3bf3709f512c3a8554757",
    "tests/test_phase8_byok_b_scope_integrity.py": "149cdf40c30ef4183ae41e6775d3a1950e09bb47d849eae1e90fa5b8b80e784a",
    "tests/test_phase8_byok_scope_integrity.py": "5c369d3a04e5254b2205049b44ea3ef661ff32870d20ce14d8f26cf2ca143cc3",
    "tests/test_phase_832_scope_integrity.py": "cc3d83397be376cce1fd1a005483e6576dea111da276a048685caf787d4058c8",
    "tests/test_phase_833_scope_integrity.py": "4bdcd395b00a4d4e3ffd104ff17cc923f75075c20e457a090c045754700b5590",
    "tests/test_phase_834_scope_integrity.py": "142d05496a0a0d75a9d5a078b9e5144b4ab56821fd329b126903bd80e1a0e754",
    "tests/test_phase_836_scope_integrity.py": "6ecb8d3ac9e970ef42d12855f81f406961cb82fcd71ef8bc26ed7e10ca822b8a",
    "tests/test_phase_837_scope_integrity.py": "827678f7e01e8fe92b56045189fa7f97e363987b688c638bfcedb1abd99767e7",
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
    """Exact twenty-three-file non-renamed Git delta."""
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
    # A's eleven original pins remain immutable, including its canonical self.
    frozen = historical._parent_tree()
    if _oid("rev-parse", PARENT + "^{tree}") != PARENT_TREE:
        raise AssertionError("BYOK B parent tree mismatch")
    if _git("rev-list", "--parents", "-n", "1", PARENT).decode("ascii").split() != [
        PARENT, PARENT_PARENT
    ]:
        raise AssertionError("BYOK B parent ancestry mismatch")
    if (_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PARENT_TAG)
            != PARENT_TAG_OBJECT
            or _git("cat-file", "-t", PARENT_TAG_OBJECT) != b"tag\n"
            or _oid("rev-parse", "--verify", "--end-of-options", PARENT_TAG_OBJECT+"^{}")
            != PARENT
            or _git("cat-file", "-t", PARENT) != b"commit\n"):
        raise AssertionError("BYOK B protected annotated tag mismatch")
    parent = prior._tree(PARENT)
    expected = dict(frozen)
    if (len(historical.ENVELOPE) != 11
            or set(historical.CANDIDATE_SHA256) != historical.ENVELOPE):
        raise AssertionError("BYOK B incomplete historical A pins")
    for path, pin in historical.CANDIDATE_SHA256.items():
        data = _git("show", PARENT + ":" + path)
        if (historical._digest(path, data) != pin
                or parent.get(path) != ("100644", prior._blob(data))):
            raise AssertionError("BYOK B changed sealed A bytes: " + path)
        expected[path] = ("100644", prior._blob(data))
    if expected != parent:
        raise AssertionError("BYOK B changed frozen inventory")
    return parent

def assert_byok_b_integrity():
    """Prove an exact unstaged/staged/one-child BYOK descendant, no bypass."""
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("BYOK B unsupported Git format")
    head = _oid("rev-parse", "HEAD")
    if not HEX40.fullmatch(head):
        raise AssertionError("BYOK B malformed HEAD")
    if _git("branch", "--show-current").decode().strip() != "nayeon-v1":
        raise AssertionError("Wrong BYOK B product branch")
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
        raise AssertionError("BYOK B ignored executable or source")
    if (len(ENVELOPE) != 23 or len(ADDED) != 7 or len(MODIFIED) != 16
            or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("BYOK B unapproved manifest")
    if any(type(pin) is not str or not re.fullmatch(r"[a-f0-9]{64}", pin)
           or pin == "0"*64 for pin in CANDIDATE_SHA256.values()):
        raise AssertionError("BYOK B unfinalized source pin")
    if any(path in baseline for path in ADDED):
        raise AssertionError("BYOK B added path in prior seal")
    if any(baseline.get(path, ("",))[0] != "100644" for path in MODIFIED):
        raise AssertionError("BYOK B invalid modified type")
    expected = dict(baseline)
    for path, pin in CANDIDATE_SHA256.items():
        data = _disk(path)
        if _digest(path, data) != pin:
            raise AssertionError("BYOK B candidate byte mismatch: " + path)
        if path == "nayeon/desktop_alpha/first_run_connection_owner.py":
            _no_effect_imports(path, data)
        expected[path] = ("100644", prior._blob(data))
        if path in MODIFIED and expected[path] == baseline[path]:
            raise AssertionError("BYOK B incomplete modified scope")
    for path, ref in baseline.items():
        if path not in MODIFIED:
            if committed.get(path) != ref or index.get(path) != ref:
                raise AssertionError("Frozen BYOK A historical file modified")
            if prior._blob(prior._frozen(path)) != ref[1]:
                raise AssertionError("BYOK B frozen disk bytes modified")
    if head == PARENT:
        if committed != baseline:
            raise AssertionError("BYOK B protected commit changed")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("BYOK B unexpected untracked path")
            prior._raw_work(disk_raw, index, changed=MODIFIED)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            raise AssertionError("BYOK B partial stage")
        prior._raw_work(disk_raw, index, changed=set())
        _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                    "--cached"), baseline=baseline, new=expected)
        return "EXACT_STAGED"
    if _git("rev-list", "--parents", "-n", "1", head).decode().split() != [head, PARENT]:
        raise AssertionError("BYOK B unexpected commit parent")
    if committed != expected or index != expected or untracked:
        raise AssertionError("BYOK B unapproved committed or staged inventory")
    prior._raw_work(disk_raw, index, changed=set())
    _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                PARENT, head), baseline=baseline, new=expected)
    return "EXACT_CHILD"


def assert_byok_a_current_source():
    """Bind the appended A adapter to B's reviewed full raw-source pin."""
    path = "tests/phase8_byok_scope_migration.py"
    if _digest(path, _disk(path)) != CANDIDATE_SHA256[path]:
        raise AssertionError("BYOK B changed live A adapter bytes")
    return True
