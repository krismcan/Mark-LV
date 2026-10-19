"""Phase 8.36 exact successor admission; preserves immutable 8.30–8.34 seals.

Only 19 independently approved paths, exact raw bytes, one protected parent.
No generic descendants, rebase, source wildcard, user-given skip or writes.
Synthetic historical fixtures must invoke the private historical 8.34 body.
"""
from __future__ import annotations

import hashlib
import re
import stat
from tests import phase_8_34_scope_migration as prior
from tests import phase_8_31_scope_migration as source_guard

ROOT = prior.ROOT
PROTECTED = "b0490cd9e72104a74a32dc5315cbc55bc4034676"
PROTECTED_TREE = "7100ad22930b954ab7f07ee382fec5f6afc4a014"
PROTECTED_TAG = "nayeon-v1-phase-8-34-fake-reply-lifecycle-01"
PROTECTED_TAG_OBJECT = "b503ce088ee4a787990534ea862be2936fa55767"
ADDED = frozenset({
    "nayeon/desktop_alpha/offline_request_review.py",
    "tests/test_phase_836_offline_request_review.py",
    "tests/test_phase_836_tk_request_review.py",
    "tests/test_phase_836_application_review.py",
    "tests/phase_8_36_scope_migration.py",
    "tests/test_phase_836_scope_integrity.py",
    "docs/phase_8_36_offline_request_review_rfc.md",
    "docs/phase_8_36_offline_request_review_review.md",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/phase_8_34_scope_migration.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
    "tests/test_phase_834_scope_integrity.py",
    ".codex/CURRENT_STATE.md",
    "docs/pre_829_shutdown_ownership_failure_ledger.md",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase_8_36_scope_migration.py"
CANDIDATE_SHA256 = {
    ".codex/CURRENT_STATE.md": "161437c48c9f9c21d7f540791f9b963692623d424ff8aeff06933472af6426bf",
    "docs/phase_8_36_offline_request_review_review.md": "95e506a11337731e5654e448f15c5ccf9c9dab912706a3811a2dab70cd440381",
    "docs/phase_8_36_offline_request_review_rfc.md": "bc1a589152646126be3ccc94fc0245f90ba5de8fc20fb40dc269cec74b3c62ce",
    "docs/pre_829_shutdown_ownership_failure_ledger.md": "deec2c18965afcc9eb40cadfd63caf88daac2fba692959fcd648e741dc29fefb",
    "nayeon/desktop_alpha/application.py": "aadbd471f58d9d1e212e0d67b7e788e63a9f0eaf8d257c041733c910a229387b",
    "nayeon/desktop_alpha/offline_request_review.py": "5b4fb379d9f907cd14cd2711e651d58445834c01c4ddf067376176ae5fb98884",
    "nayeon/desktop_alpha/workspace_window.py": "400d1dd3df829d9354d02dbf8de47f5373ea4cc7e26c0303cf380ac58d757fb5",
    "tests/phase_8_30_scope_migration.py": "7aaa31f0c32825fa2ee6cc463c66b6a9a00165bdbb5b1509bf3dae598af2ed48",
    "tests/phase_8_34_scope_migration.py": "59442121254b42949640161fb7dbd47e90f3e77e6045f258a1da130b640c8d43",
    "tests/phase_8_36_scope_migration.py": "9929aa9686275ba0bc3ebfad5e6dbe82dc7ee3954451388ff1a3dda5bca407f2",
    "tests/test_phase_830_scope_integrity.py": "62335a22c7045ffcb85c9412b5c55c1dc8bb17155dfcb7fab528b85855a10464",
    "tests/test_phase_831_scope_integrity.py": "5163816aa3647c074f4ef434dff63891d877f54ad3af02b42f98c6903d933da1",
    "tests/test_phase_832_scope_integrity.py": "861a1a19dce7e38a38c1c8a02deb4d971e813df4dfbfdd8150e8aa0f3e694e70",
    "tests/test_phase_833_scope_integrity.py": "9b22ed97005807933e36e8fa69e7d1f66c45013888e0f37a5dcb8c034ad70264",
    "tests/test_phase_834_scope_integrity.py": "a19dba9f9be0f89ff59e5a659be0196aa0f3d4f50b0d96c904e06d87edee2924",
    "tests/test_phase_836_application_review.py": "f2d71381b3f02f455148c38ce03bf8aa56d8b727391b57af8c26e8ec69f28e4c",
    "tests/test_phase_836_offline_request_review.py": "fe94785b754bcbffa26f66d5201ed9b97154d9b2bf8425634ac842c1ec0367da",
    "tests/test_phase_836_scope_integrity.py": "220cba032f0ab448a1235c1be6c58161b438d3a74e981b4c4a5ae6b33b83224f",
    "tests/test_phase_836_tk_request_review.py": "e2e415e8a8eb9caac7c1bdd9b16f0bac5fc275ab69141a9362d263a147f12b64",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SELF_PIN = re.compile(rb'("tests/phase_8_36_scope_migration.py": ")[0-9a-f]{64}(",)')


def _git(*args):
    return prior._git(*args)


def _inventory(raw, *, index=False):
    return prior._inventory(raw, index=index)


def _tree(commit):
    return _inventory(_git("ls-tree", "-r", "-z", "--full-tree", commit))


def _index():
    return _inventory(_git("ls-files", "--stage", "-z"), index=True)


def _blob(data):
    return prior._blob_oid(data)


def _digest(path, data):
    if path == SELF:
        data, count = SELF_PIN.subn(
            lambda m: m[1] + b"0" * 64 + m[2], data)
        if count != 1:
            raise AssertionError("Malformed 8.36 self pin")
    return hashlib.sha256(data).hexdigest()


def _paths(raw):
    if type(raw) is not bytes or raw and not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.36 path inventory")
    out = set()
    for row in raw.split(b"\0")[:-1]:
        path = row.decode("utf-8", "strict")
        prior._path(path)
        if path in out:
            raise AssertionError("Duplicate 8.36 path")
        out.add(path)
    return out


def _others(*flags):
    return _paths(_git("ls-files", "--others", *flags, "-z"))


def _disk(path):
    return prior._disk(path)


def _frozen(path):
    return prior._raw_frozen_disk(path)


def _raw_delta(raw, *, baseline, new):
    if type(raw) is not bytes or not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.36 raw delta")
    records = raw.split(b"\0")
    if records[-1:] != [b""] or len(records) != 2 * len(ENVELOPE) + 1:
        raise AssertionError("Incomplete 8.36 exact raw delta")
    touched = set()
    for metadata, pathname in zip(records[:-1:2], records[1:-1:2]):
        try:
            path = pathname.decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Malformed 8.36 delta pathname") from None
        prior._path(path)
        if path not in ENVELOPE or path in touched:
            raise AssertionError("Unauthorized 8.36 delta pathname")
        old_mode, old_oid = baseline.get(path, ("000000", "0" * 40))
        new_mode, new_oid = new[path]
        target = (f":{old_mode} {new_mode} {old_oid} {new_oid} "
                  + ("A" if path in ADDED else "M")).encode("ascii")
        if metadata != target:
            raise AssertionError("Wrong 8.36 status/mode/blob")
        touched.add(path)
    if touched != ENVELOPE:
        raise AssertionError("Incomplete 8.36 delta paths")


def _raw_work(raw, index, *, changed):
    if raw == b"" and not changed:
        return
    if type(raw) is not bytes or not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.36 disk delta")
    records = raw.split(b"\0")
    if records[-1:] != [b""] or len(records) != 2 * len(changed) + 1:
        raise AssertionError("Wrong 8.36 disk delta")
    found = set()
    for meta, path_bytes in zip(records[:-1:2], records[1:-1:2]):
        path = path_bytes.decode("utf-8", "strict")
        prior._path(path)
        if path not in changed or path in found:
            raise AssertionError("Unauthorized 8.36 disk delta")
        mode, oid = index[path]
        desired = f":{mode} {mode} {oid} {'0'*40} M".encode("ascii")
        if meta != desired:
            raise AssertionError("Untrusted 8.36 disk delta")
        found.add(path)


def _seal():
    # Existing history verifier retains original 8.29/8.33 guards and tags.
    prior._history()
    if _git("rev-parse", PROTECTED + "^{tree}").decode("ascii").strip() != PROTECTED_TREE:
        raise AssertionError("8.34 protected tree mismatch")
    if (_git("show-ref", "--verify", "--hash", "--", "refs/tags/" + PROTECTED_TAG).decode("ascii").strip() != PROTECTED_TAG_OBJECT
            or _git("cat-file", "-t", PROTECTED_TAG_OBJECT) != b"tag\n"
            or _git("rev-parse", "--verify", "--end-of-options",
                    PROTECTED_TAG_OBJECT + "^{}").decode("ascii").strip() != PROTECTED
            or _git("cat-file", "-t", PROTECTED) != b"commit\n"):
        raise AssertionError("8.34 annotated seal mismatch")
    tree = _tree(PROTECTED)
    if "tests/phase_8_34_scope_migration.py" not in tree:
        raise AssertionError("Missing protected 8.34 helper")
    for path, hash_expected in prior.CANDIDATE_SHA256.items():
        data = _git("show", PROTECTED + ":" + path)
        if prior._digest(path, data) != hash_expected or tree[path] != ("100644", _blob(data)):
            raise AssertionError("Unapproved sealed 8.34 bytes")
    return tree


def assert_836_integrity():
    """Prove exact 8.36 candidate: COMPLETE_UNSTAGED, EXACT_STAGED, EXACT_CHILD.

    Historical refusal remains available explicitly, never as runtime fallback.
    """
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported 8.36 Git object format")
    head = _git("rev-parse", "HEAD").decode("ascii").strip()
    if not HEX40.fullmatch(head):
        raise AssertionError("Invalid 8.36 HEAD")
    if _git("branch", "--show-current").decode("utf-8").strip() != "nayeon-v1":
        raise AssertionError("Wrong 8.36 product branch")
    _git("merge-base", "--is-ancestor", PROTECTED, head)
    baseline = _seal()
    committed = _tree(head)
    index = _index()
    prior._index_flags(index)
    untracked = _others("--exclude-standard")
    ignored = _others("--ignored", "--exclude-standard")
    disk_raw = _git("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
    # A sealed checkout must not contain ANY ignored untracked path.
    # Bytecode (.pyc), native loaders (.pyd/.dll/.so), sitecustomize,
    # and DLL search-path payloads can execute despite valid source hashes.
    # An allowlist of suffixes would miss a new loader type; fail closed.
    if ignored:
        raise AssertionError("Ignored 8.36 executable or source")
    if (not ENVELOPE or len(ENVELOPE) != 19
            or len(ADDED) != 8 or len(MODIFIED) != 11
            or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("Unapproved 8.36 file allowlist")
    if any(type(h) is not str or not re.fullmatch(r"[0-9a-f]{64}", h)
           or h == "0" * 64 for h in CANDIDATE_SHA256.values()):
        raise AssertionError("Unfinalized 8.36 source pins")
    for path in ADDED:
        if path in baseline:
            raise AssertionError("8.36 added path exists in frozen history")
    for path in MODIFIED:
        if baseline.get(path, ("",))[0] != "100644":
            raise AssertionError("Unapproved modified file type")
    expected = dict(baseline)
    for path in ENVELOPE:
        data = _disk(path)
        if _digest(path, data) != CANDIDATE_SHA256[path]:
            raise AssertionError("Unapproved 8.36 candidate bytes: " + path)
        if path.startswith("nayeon/"):
            source_guard._no_unsafe_imports(path, data)
        expected[path] = ("100644", _blob(data))
    for path, ref in baseline.items():
        if path not in MODIFIED:
            if committed.get(path) != ref or index.get(path) != ref:
                raise AssertionError("Frozen 8.36 historical file modified")
            data = _frozen(path)
            if _blob(data) != ref[1]:
                raise AssertionError("Frozen historical worktree bytes modified")
    if head == PROTECTED:
        if committed != baseline:
            raise AssertionError("Wrong 8.36 protected HEAD")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("Missing or extra untracked 8.36 paths")
            _raw_work(disk_raw, index, changed=MODIFIED)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            raise AssertionError("Partial 8.36 stage refused")
        _raw_work(disk_raw, index, changed=set())
        _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                        "--cached"), baseline=baseline, new=expected)
        return "EXACT_STAGED"
    # Exactly one product commit from sealed 8.34; no accidental merge or
    # successor acceptance just because it is a descendant.
    parents = _git("rev-list", "--parents", "-n", "1", head).decode("ascii").split()
    if parents != [head, PROTECTED]:
        raise AssertionError("8.36 unexpected product parent")
    if committed != expected or index != expected or untracked:
        raise AssertionError("Unapproved 8.36 committed/index snapshot")
    _raw_work(disk_raw, index, changed=set())
    _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                    PROTECTED, head), baseline=baseline, new=expected)
    return "EXACT_CHILD"
