"""Phase 8.37 exact successor admission; preserves immutable 8.30–8.36 seals.

Only 20 explicitly authorized paths, exact raw bytes, one protected parent.
No generic descendants, rebase, source wildcard, user-given skip or writes.
Synthetic historical fixtures must invoke the private historical 8.36 body.
"""
from __future__ import annotations

import hashlib
import re
from tests import phase_8_36_scope_migration as prior
from tests import phase_8_34_scope_migration as canonical
from tests import phase_8_31_scope_migration as source_guard

ROOT = prior.ROOT
PROTECTED = "a12565b9be070684e1d7d801ded4833d13121f94"
PROTECTED_TREE = "f2d35fef90add1bb3b14ab9a1b26b0235334bfbb"
PROTECTED_TAG = "nayeon-v1-phase-8-36-offline-request-review-01"
PROTECTED_TAG_OBJECT = "aca0de5a873cf41454fe1fa144d12f34d44418a4"
ADDED = frozenset({
    "nayeon/desktop_alpha/offline_request_draft.py",
    "nayeon/desktop_alpha/offline_draft_consent.py",
    "tests/test_phase_837_offline_request_draft.py",
    "tests/test_phase_837_draft_consent.py",
    "tests/test_phase_837_draft_tk.py",
    "tests/test_phase_837_draft_application.py",
    "tests/phase_8_37_scope_migration.py",
    "tests/test_phase_837_scope_integrity.py",
    "docs/phase_8_37_provider_request_draft_rfc.md",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_36_scope_migration.py",
    "tests/test_phase_836_scope_integrity.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    "tests/test_pre_829_a02_fake_isolation.py",
    "tests/test_phase_834_scope_integrity.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase_8_37_scope_migration.py"
# SHA256 of raw bytes, except SELF: zero only its own literal pin.
CANDIDATE_SHA256 = {
    "docs/phase_8_37_provider_request_draft_rfc.md": "05f39c622a5772598c48aeaa567dff94339a1e7fdb8634606a0d5d9fefca0301",
    "nayeon/desktop_alpha/application.py": "4aac135178e4e9f0df9b0f0e46a580d6aff02694dfb1a6677ec65319162cecb0",
    "nayeon/desktop_alpha/offline_draft_consent.py": "40d78b7949056dceb337204e8b7ff4e0e6ee18a1e2208de1a00e8b957e4e26e2",
    "nayeon/desktop_alpha/offline_request_draft.py": "c4d39810d6cb220d3ca9e38e3c9ceab8554ae2b662732ebb24bbc9fe98f24cb3",
    "nayeon/desktop_alpha/workspace_window.py": "dbbaa691cc5caf0f9f1dfc611342a61ecbc5fdc11514c8cd1acfa8cd09c7b63b",
    "tests/phase_8_30_scope_migration.py": "778bf425e0d3ceb69ae9d4a3bf06d627ece1c29bb5f7816722039ed10fd38f40",
    "tests/phase_8_36_scope_migration.py": "d63b58a03a00f573c6474a514f4f4e545b4a5ea3c85478fd824e1276862413e6",
    "tests/phase_8_37_scope_migration.py": "a53ebfd97a7696ca2255918736cd6e6929b1770eaec6318742f509dcb5b99692",
    "tests/test_phase_830_scope_integrity.py": "50376cdb904700911bcb78b6a1d5b4298fa9fa3c6b7ea2bb18e2635ab41af454",
    "tests/test_phase_831_scope_integrity.py": "70c2c1654d978168c3c58be337cab12e87499d6f2113903ff1c97b957a863f12",
    "tests/test_phase_836_scope_integrity.py": "062980db3522ee9ce5c3d939e50adda426f53fa8c772917ba53d25b142d0dd3d",
    "tests/test_phase_837_draft_application.py": "f17301a47a8467d3406659f87f4807816e11d9fc889aa3afb50539c2fb12ee28",
    "tests/test_phase_837_draft_consent.py": "2f976063dea225da1b7c08a232fb7e139d05b032a405d350433fc9a97adeab40",
    "tests/test_phase_837_draft_tk.py": "b4a0cb835953edeed884619d94482b8c40757b225bcc88fbb323d65b64f16753",
    "tests/test_phase_837_offline_request_draft.py": "86b7d86931e924f9d830faa14c9a34ca738ba14ee881e8f12294b0e48b96b452",
    "tests/test_phase_837_scope_integrity.py": "129679f8cdf674c156bf871959e8187ecc541f33fb8c5c5ed2863437fb162d08",
    "tests/test_phase_834_scope_integrity.py": "c91f4823b705f04bd73b3183734b2368690797ec850cc70416298156627061ef",
    "tests/test_phase_832_scope_integrity.py": "1e4369684ad1b3641367cb8f2a8cce26942a4904bea89b01af79df4c855f9ed0",
    "tests/test_phase_833_scope_integrity.py": "0bbd24ac3408a862a91d3cb831b17193e5f01a97422ac1c2f2e8403edb157b37",
    "tests/test_pre_829_a02_fake_isolation.py": "ac3c47aa9d37a2afc354f354e50bd6380273a21e095b69f1a6334e2057cd5f69",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SELF_PIN = re.compile(rb'("tests/phase_8_37_scope_migration.py": ")[0-9a-f]{64}(",)')


def _git(*args):
    return prior._git(*args)


def _oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or not re.fullmatch(rb"[0-9a-f]{40}\n?", raw):
        raise AssertionError("Malformed 8.37 seal OID")
    return raw.decode("ascii").rstrip("\n")


def _path(path):
    canonical._path(path)
    for part in path.split("/"):
        if (any(ord(c) < 32 or c in '<>"|?*' for c in part)
                or part.split(".", 1)[0].casefold() in {
                    "con", "prn", "aux", "nul", *("com" + str(i) for i in range(1, 10)),
                    *("lpt" + str(i) for i in range(1, 10))}):
            raise AssertionError("Noncanonical 8.37 Windows path")


def _canonical_paths(paths):
    # Bind component spelling too: A/x and a/y alias the same Windows folder.
    prefixes = {}
    for path in paths:
        _path(path)
        parts = path.split("/")
        for i in range(1, len(parts) + 1):
            prefix = "/".join(parts[:i])
            folded = prefix.casefold()
            if folded in prefixes and prefixes[folded] != prefix:
                raise AssertionError("Aliased 8.37 Git path")
            prefixes[folded] = prefix


def _index_flags(index):
    raw = _git("ls-files", "-v", "--sparse", "-z")
    if type(raw) is not bytes or raw and not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.37 index flags")
    seen = set()
    for row in raw.split(b"\0")[:-1]:
        if not row.startswith(b"H "):
            raise AssertionError("Unsupported 8.37 index flags")
        path = row[2:].decode("utf-8", "strict")
        _path(path)
        if path in seen or path not in index:
            raise AssertionError("Repeated or unbound 8.37 index flags")
        seen.add(path)
    if seen != set(index):
        raise AssertionError("Incomplete 8.37 index flags")


def _inventory(raw, *, index=False):
    result = canonical._inventory(raw, index=index)
    _canonical_paths(result)
    if any(mode not in {"100644", "100755"} for mode, oid in result.values()):
        raise AssertionError("Linked or nonregular 8.37 Git entry")
    return result


def _tree(commit):
    return _inventory(_git("ls-tree", "-r", "-z", "--full-tree", commit))


def _index():
    return _inventory(_git("ls-files", "--stage", "-z"), index=True)


def _blob(data):
    return canonical._blob_oid(data)


def _digest(path, data):
    if path == SELF:
        data, count = SELF_PIN.subn(
            lambda m: m[1] + b"0" * 64 + m[2], data)
        if count != 1:
            raise AssertionError("Malformed 8.37 self pin")
    return hashlib.sha256(data).hexdigest()


def _paths(raw):
    if type(raw) is not bytes or raw and not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.37 path inventory")
    out = set()
    for row in raw.split(b"\0")[:-1]:
        path = row.decode("utf-8", "strict")
        _path(path)
        if path in out:
            raise AssertionError("Duplicate 8.37 path")
        out.add(path)
    return out


def _others(*flags):
    return _paths(_git("ls-files", "--others", *flags, "-z"))


def _disk(path):
    return prior._disk(path)


def _frozen(path):
    return canonical._raw_frozen_disk(path)


def _raw_delta(raw, *, baseline, new):
    if type(raw) is not bytes or not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.37 raw delta")
    records = raw.split(b"\0")
    if records[-1:] != [b""] or len(records) != 2 * len(ENVELOPE) + 1:
        raise AssertionError("Incomplete 8.37 exact raw delta")
    touched = set()
    for metadata, pathname in zip(records[:-1:2], records[1:-1:2]):
        try:
            path = pathname.decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Malformed 8.37 delta pathname") from None
        _path(path)
        if path not in ENVELOPE or path in touched:
            raise AssertionError("Unauthorized 8.37 delta pathname")
        old_mode, old_oid = baseline.get(path, ("000000", "0" * 40))
        new_mode, new_oid = new[path]
        target = (f":{old_mode} {new_mode} {old_oid} {new_oid} "
                  + ("A" if path in ADDED else "M")).encode("ascii")
        if metadata != target:
            raise AssertionError("Wrong 8.37 status/mode/blob")
        touched.add(path)
    if touched != ENVELOPE:
        raise AssertionError("Incomplete 8.37 delta paths")


def _raw_work(raw, index, *, changed):
    if raw == b"" and not changed:
        return
    if type(raw) is not bytes or not raw.endswith(b"\0"):
        raise AssertionError("Malformed 8.37 disk delta")
    records = raw.split(b"\0")
    if records[-1:] != [b""] or len(records) != 2 * len(changed) + 1:
        raise AssertionError("Wrong 8.37 disk delta")
    found = set()
    for meta, path_bytes in zip(records[:-1:2], records[1:-1:2]):
        path = path_bytes.decode("utf-8", "strict")
        _path(path)
        if path not in changed or path in found:
            raise AssertionError("Unauthorized 8.37 disk delta")
        mode, oid = index[path]
        desired = f":{mode} {mode} {oid} {'0'*40} M".encode("ascii")
        if meta != desired:
            raise AssertionError("Untrusted 8.37 disk delta")
        found.add(path)


def _seal():
    # Verify all older seals before the complete immutable 8.36 snapshot.
    older = prior._seal()
    if _oid("rev-parse", PROTECTED + "^{tree}") != PROTECTED_TREE:
        raise AssertionError("8.36 protected tree mismatch")
    if _git("rev-list", "--parents", "-n", "1", PROTECTED).decode("ascii").split() != [PROTECTED, prior.PROTECTED]:
        raise AssertionError("8.36 protected parent mismatch")
    if (_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PROTECTED_TAG) != PROTECTED_TAG_OBJECT
            or _git("cat-file", "-t", PROTECTED_TAG_OBJECT) != b"tag\n"
            or _oid("rev-parse", "--verify", "--end-of-options", PROTECTED_TAG_OBJECT + "^{}") != PROTECTED
            or _git("cat-file", "-t", PROTECTED) != b"commit\n"):
        raise AssertionError("8.36 annotated seal mismatch")
    tree = _tree(PROTECTED)
    expected = dict(older)
    if set(prior.CANDIDATE_SHA256) != prior.ENVELOPE or len(prior.ENVELOPE) != 19:
        raise AssertionError("Incomplete frozen 8.36 manifest")
    for path, pin in prior.CANDIDATE_SHA256.items():
        data = _git("show", PROTECTED + ":" + path)
        if (prior._digest(path, data) != pin
                or tree.get(path) != ("100644", _blob(data))):
            raise AssertionError("Unapproved sealed 8.36 bytes: " + path)
        expected[path] = ("100644", _blob(data))
    if tree != expected:
        raise AssertionError("8.36 full inventory mismatch")
    return tree


def assert_837_integrity():
    """Prove exact 8.37 candidate: COMPLETE_UNSTAGED, EXACT_STAGED, EXACT_CHILD.

    Historical refusal remains available explicitly, never as runtime fallback.
    """
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported 8.37 Git object format")
    head = _git("rev-parse", "HEAD").decode("ascii").strip()
    if not HEX40.fullmatch(head):
        raise AssertionError("Invalid 8.37 HEAD")
    if _git("branch", "--show-current").decode("utf-8").strip() != "nayeon-v1":
        raise AssertionError("Wrong 8.37 product branch")
    _git("merge-base", "--is-ancestor", PROTECTED, head)
    baseline = _seal()
    committed = _tree(head)
    index = _index()
    _index_flags(index)
    untracked = _others("--exclude-standard")
    ignored = _others("--ignored", "--exclude-standard")
    disk_raw = _git("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
    _canonical_paths(set(committed) | set(index) | untracked | ignored)
    # A sealed checkout must not contain ANY ignored untracked path.
    # Bytecode (.pyc), native loaders (.pyd/.dll/.so), sitecustomize,
    # and DLL search-path payloads can execute despite valid source hashes.
    # An allowlist of suffixes would miss a new loader type; fail closed.
    if ignored:
        raise AssertionError("Ignored 8.37 executable or source")
    if (not ENVELOPE or len(ENVELOPE) != 20
            or len(ADDED) != 9 or len(MODIFIED) != 11
            or set(CANDIDATE_SHA256) != ENVELOPE):
        raise AssertionError("Unapproved 8.37 file allowlist")
    if any(type(h) is not str or not re.fullmatch(r"[0-9a-f]{64}", h)
           or h == "0" * 64 for h in CANDIDATE_SHA256.values()):
        raise AssertionError("Unfinalized 8.37 source pins")
    for path in ADDED:
        if path in baseline:
            raise AssertionError("8.37 added path exists in frozen history")
    for path in MODIFIED:
        if baseline.get(path, ("",))[0] != "100644":
            raise AssertionError("Unapproved modified file type")
    expected = dict(baseline)
    for path in ENVELOPE:
        data = _disk(path)
        if _digest(path, data) != CANDIDATE_SHA256[path]:
            raise AssertionError("Unapproved 8.37 candidate bytes: " + path)
        if path.startswith("nayeon/"):
            source_guard._no_unsafe_imports(path, data)
        expected[path] = ("100644", _blob(data))
        if path in MODIFIED and expected[path] == baseline[path]:
            raise AssertionError("Incomplete 8.37 modified scope")
    for path, ref in baseline.items():
        if path not in MODIFIED:
            if committed.get(path) != ref or index.get(path) != ref:
                raise AssertionError("Frozen 8.37 historical file modified")
            data = _frozen(path)
            if _blob(data) != ref[1]:
                raise AssertionError("Frozen historical worktree bytes modified")
    if head == PROTECTED:
        if committed != baseline:
            raise AssertionError("Wrong 8.37 protected HEAD")
        if index == baseline:
            if untracked != ADDED:
                raise AssertionError("Missing or extra untracked 8.37 paths")
            _raw_work(disk_raw, index, changed=MODIFIED)
            return "COMPLETE_UNSTAGED"
        if index != expected or untracked:
            raise AssertionError("Partial 8.37 stage refused")
        _raw_work(disk_raw, index, changed=set())
        _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                        "--cached"), baseline=baseline, new=expected)
        return "EXACT_STAGED"
    # Exactly one product commit from sealed 8.36; no accidental merge or
    # successor acceptance just because it is a descendant.
    parents = _git("rev-list", "--parents", "-n", "1", head).decode("ascii").split()
    if parents != [head, PROTECTED]:
        raise AssertionError("8.37 unexpected product parent")
    if committed != expected or index != expected or untracked:
        raise AssertionError("Unapproved 8.37 committed/index snapshot")
    _raw_work(disk_raw, index, changed=set())
    _raw_delta(_git("diff", "--no-renames", "--raw", "--no-abbrev", "-z",
                    PROTECTED, head), baseline=baseline, new=expected)
    return "EXACT_CHILD"


# Preserve the exact immutable historical 8.37 implementation above for
# pinned synthetic fixtures. LIVE admissions require full BYOK successor.
_assert_837_historical = assert_837_integrity


def assert_837_integrity():
    from tests.phase8_byok_scope_migration import assert_byok_integrity
    return assert_byok_integrity()
