"""Exact twenty-path 8.34 successor; immutable 8.30/8.31 history remains proof.

Pins describe a candidate, not independent approval. The helper's self entry is
SHA256 with ONLY its own literal value zeroed (avoids a self-hash fixed point).
The externally reported raw twenty-file manifest must be reviewed separately.
No Git writes, environmental approval switch, descendant wildcard or live effects.
"""
from __future__ import annotations

import hashlib
import re
import stat
import unicodedata

from tests import phase_8_30_scope_migration as prior
from tests import phase_8_31_scope_migration as old
from tests import phase_8_32_scope_migration as legacy
from tests import phase_8_33_scope_migration as frozen

ROOT = prior.ROOT
PROTECTED = "1a972d1d292597239c938d53437218c536b5bf3f"
PROTECTED_TREE = "aab665d0eaa6421928725bea4df747eb37fd96ac"
PROTECTED_TAG = "nayeon-v1-phase-8-33-offline-delayed-completion-01"
PROTECTED_TAG_OBJECT = "0b5bb13d0ea8847ead6e05d4cd12af57a891d5a0"
ADDED = frozenset({
    "nayeon/desktop_alpha/reply_contracts.py",
    "nayeon/desktop_alpha/reply_owner.py",
    "nayeon/desktop_alpha/reply_worker.py",
    "tests/test_phase_834_reply_owner.py",
    "tests/test_phase_834_reply_worker.py",
    "tests/test_phase_834_tk_reply.py",
    "tests/phase_8_34_scope_migration.py",
    "tests/test_phase_834_scope_integrity.py",
    "docs/phase_8_34_text_reply_rfc.md",
    "docs/phase_8_34_text_reply_review.md",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_30_scope_migration.py",
    "tests/phase_8_33_scope_migration.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_833_scope_integrity.py",
    ".codex/CURRENT_STATE.md",
    "docs/pre_829_shutdown_ownership_failure_ledger.md",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase_8_34_scope_migration.py"
# Raw SHA256 candidate evidence, not independent approval. Reserved context pin
# stays ZERO after ACL denial: host must write/review context and repin explicitly.
CANDIDATE_SHA256 = {
    "nayeon/desktop_alpha/reply_contracts.py": "43499034bbd6f49892b46bb5ff6209a7ceea85cb4392013ce0c2f718a6f208a4",
    "nayeon/desktop_alpha/reply_owner.py": "ed3910a2499a0a8f8bf0e56ea26fe5fbdbb9bfeea2a256f57adf1302d4580dbc",
    "nayeon/desktop_alpha/reply_worker.py": "68c39289b3920e105912f3ee5e063b584692458d48274f5dade18f782c6b8059",
    "tests/test_phase_834_reply_owner.py": "f2925b5ea3eda73f542b1574fb20f6538da2fb3c149f482d89c2effa022bd8ee",
    "tests/test_phase_834_reply_worker.py": "152cc95d5b2260069e2364ff983d69b75213dbcec6b43ba0f57fe85739fa9783",
    "tests/test_phase_834_tk_reply.py": "d0971f1e6ff6d5ae6444f10e2da0903e6a1f02b51f8d677f34b0e427394dce94",
    "tests/phase_8_34_scope_migration.py": "1cb447df709925f41605c5816b3fa03178625120ba7999b6d70335c0f541f176",
    "tests/test_phase_834_scope_integrity.py": "a18e50f3519c93ebbc1fe40470fcddca79784bda67733f580617aef41c731c53",
    "docs/phase_8_34_text_reply_rfc.md": "41f156cba8518feffc76ccaa4bfbd54f46452e461f687359eef65c47a1d0c9ab",
    "docs/phase_8_34_text_reply_review.md": "fdf290bc3b87e63e1f02bf99affb76b5ab7ef11547e3c9e11fc455751032a0f6",
    "nayeon/desktop_alpha/application.py": "035f5c8d6ea131b1dd4bb3aa061ff96662d1b926c4321e9a1bfe2eef700181e7",
    "nayeon/desktop_alpha/workspace_window.py": "6d216a4c8ee5e4fae1afca6a10a9298702562f2bec8ad2bb91bd9bebcd4f29b0",
    "tests/phase_8_30_scope_migration.py": "9d82107ff78f8d3765b0f746e5cc7208ec38e05fba55590e54cdbc3a8d42ff78",
    "tests/phase_8_33_scope_migration.py": "9af98a6fd435fea19f30ce00d03fb4f47a23ca64e9278fd9b4e06daaf53872bd",
    "tests/test_phase_830_scope_integrity.py": "2c51136d2c0d4db40dac933114a26e4eaca97dcc76cc7d7a0ff667fae7444cdc",
    "tests/test_phase_831_scope_integrity.py": "d2f930f8bd090b52a6e38295d6e2539e8b287d5bd40cec9db7f68dd655450c86",
    "tests/test_phase_832_scope_integrity.py": "4d545739340644c76afff001f369e3740a4c1f623f259564f91482fd72f15cda",
    "tests/test_phase_833_scope_integrity.py": "d0e3a4dc7cbc7cd4840cb65f66e2ae3b769bd0cbc258ca0501588d9bd7939542",
    ".codex/CURRENT_STATE.md": "b8bf243847c6958626c218490ebbe4a33220cdc019a3f6ddeeeef117d8ec6a55",
    "docs/pre_829_shutdown_ownership_failure_ledger.md": "5963c9b9e5b9af67ced957de1da6e2e8c4558da72141eaae4bde6b181ff07e2b",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SELF_PIN = re.compile(rb'("tests/phase_8_34_scope_migration.py": ")[0-9a-f]{64}(",)')


def _git(*args):
    return prior._git(*args)


def _path(path):
    # Validate every raw record before filtering. Preserve original production
    # alias rejection text and apply equivalent rules to tests/docs/config too.
    production = prior._production_git_path(path)
    if (unicodedata.normalize("NFC", path) != path or "\\" in path
            or path.startswith("/") or any(
                not p or p in {".", ".."} or p != p.rstrip(" .") or ":" in p
                for p in path.split("/"))):
        raise AssertionError("Noncanonical 8.34 Git pathname")
    for root in ("tests", "docs", ".codex"):
        first = path.split("/", 1)[0]
        if first.casefold() == root and first != root:
            raise AssertionError("Aliased 8.34 scope root")
    return production


def _inventory(raw, *, index=False):
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.34 Git inventory")
    result, aliases = {}, set()
    for row in raw.split(b"\0")[:-1]:
        try:
            meta, pathname = row.split(b"\t", 1)
            fields = meta.decode("ascii", "strict").split(" ")
            if len(fields) != 3:
                raise ValueError()
            mode, middle, last = fields
            oid = middle if index else last
            if (mode not in {"100644", "100755", "120000", "160000"}
                    or not HEX40.fullmatch(oid)
                    or (last != "0" if index else
                        middle != ("commit" if mode == "160000" else "blob"))):
                raise ValueError()
            path = pathname.decode("utf-8", "strict")
            _path(path)
        except (ValueError, UnicodeError):
            raise AssertionError("Malformed 8.34 Git inventory") from None
        alias = path.casefold()
        if path in result or alias in aliases:
            raise AssertionError("Repeated or aliased 8.34 Git path")
        aliases.add(alias)
        result[path] = (mode, oid)
    return result


def _tree(commit):
    return _inventory(_git("ls-tree", "-r", "-z", "--full-tree", commit))


def _index():
    return _inventory(_git("ls-files", "--stage", "-z"), index=True)


def _index_flags(index):
    # -v exposes assume-unchanged (lowercase); --sparse exposes sparse directory
    # entries instead of silently expanding them. Only ordinary cached H rows
    # are supported. A separate full stage inventory still binds mode/OID/stage.
    raw = _git("ls-files", "-v", "--sparse", "-z")
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.34 index flags")
    seen = set()
    for row in raw.split(b"\0")[:-1]:
        if not row.startswith(b"H "):
            raise AssertionError("Unsupported 8.34 index flags")
        try:
            path = row[2:].decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Malformed 8.34 index flags") from None
        _path(path)
        if path in seen or path not in index:
            raise AssertionError("Repeated or unbound 8.34 index flags")
        seen.add(path)
    if seen != set(index):
        raise AssertionError("Incomplete 8.34 index flags")


def _disk(path):
    candidate = ROOT / path
    prior._reject_linked_parents(candidate)
    try:
        info = candidate.lstat()
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
                or info.st_nlink != 1):
            raise AssertionError("Linked or nonregular 8.34 candidate")
        return candidate.read_bytes()
    except OSError:
        raise AssertionError("Missing 8.34 candidate") from None


def _raw_frozen_disk(path):
    # Git blob identity binds original bytes, including CRLF and binary data.
    # All 8.34 candidate and frozen bytes are raw; no newline normalization.
    _path(path)
    candidate = ROOT / path
    prior._reject_linked_parents(candidate)
    try:
        info = candidate.lstat()
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
                or info.st_nlink != 1):
            raise AssertionError("Linked or nonregular 8.34 frozen file")
        return candidate.read_bytes()
    except OSError:
        raise AssertionError("Missing 8.34 frozen file") from None


def _digest(path, data):
    if path == SELF:
        data, count = SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], data)
        if count != 1:
            raise AssertionError("Malformed 8.34 self pin")
    return hashlib.sha256(data).hexdigest()


def _historical_tree(commit):
    # One raw read, strictly validated BEFORE the old production projection.
    # Replacing prior._tree's filter-first parsing avoids a second fetch whose
    # contents could differ from the validated evidence. No extra ls-tree call
    # precedes the historical second-read injection seam.
    complete = _inventory(_git("ls-tree", "-r", "-z", "--full-tree", commit))
    return {p: ref for p, ref in complete.items() if prior._production_git_path(p)}


def _seal_oid(*args):
    raw = _git(*args)
    if type(raw) is not bytes or not re.fullmatch(rb"[0-9a-f]{40}\n?", raw):
        raise AssertionError("Frozen seal changed: malformed OID")
    return raw.decode("ascii").rstrip("\n")


def _history():
    # Older exact historical pins, ordered read seams and annotated seals remain
    # authoritative. The new sealed H proof is additional, never a replacement.
    frozen._history()
    if _seal_oid("rev-parse", PROTECTED + "^{tree}") != PROTECTED_TREE:
        raise AssertionError("Frozen 8.33 full tree changed")
    if _git("rev-list", "--parents", "-n", "1", PROTECTED).decode("ascii").split() != [PROTECTED, frozen.PROTECTED]:
        raise AssertionError("Wrong protected parent")
    if (_seal_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PROTECTED_TAG) != PROTECTED_TAG_OBJECT
            or _git("cat-file", "-t", PROTECTED_TAG_OBJECT) != b"tag\n"
            or _seal_oid("rev-parse", "--verify", "--end-of-options", PROTECTED_TAG_OBJECT + "^{}") != PROTECTED
            or _git("cat-file", "-t", PROTECTED) != b"commit\n"):
        raise AssertionError("Frozen seal changed")
    tree = _tree(PROTECTED)
    for path, expected in frozen.CANDIDATE_SHA256.items():
        data = _git("show", PROTECTED + ":" + path)
        if (frozen._digest(path, data) != expected
                or tree.get(path) != ("100644", _blob_oid(data))):
            raise AssertionError("Unapproved sealed 8.33 bytes")
    return {p: ref for p, ref in tree.items() if prior._production_git_path(p)}


def _blob_oid(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _others(*args):
    raw = _git("ls-files", "--others", *args, "-z")
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.34 untracked inventory")
    result = set()
    for record in raw.split(b"\0")[:-1]:
        path = record.decode("utf-8", "strict")
        _path(path)
        if path in result:
            raise AssertionError("Repeated 8.34 untracked path")
        result.add(path)
    return result


def assert_834_integrity():
    """Return LEGACY / COMPLETE_UNSTAGED / EXACT_STAGED / EXACT_CHILD.

    This proves candidate shape and pinned bytes only; independent GO and full
    authoritative Windows results are separate human gates.
    """
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported Git object format")
    head = _git("rev-parse", "HEAD").decode("ascii").strip()
    if not HEX40.fullmatch(head):
        raise AssertionError("Malformed 8.34 HEAD")
    branch = _git("branch", "--show-current").decode("utf-8").strip()
    if branch != "nayeon-v1":
        raise AssertionError("Wrong production branch")
    _git("merge-base", "--is-ancestor", PROTECTED, head)
    production = _history()
    baseline = _tree(PROTECTED)
    committed = _tree(head)
    index = _index()
    # Enumerate raw HEAD/index/untracked/ignored before state classification.
    untracked = _others("--exclude-standard")
    ignored = _others("--ignored", "--exclude-standard")
    raw_disk = _git("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
    _index_flags(index)
    for path in ignored:
        if (prior._production_git_path(path) or path.startswith(("tests/", "docs/", ".codex/"))):
            # Normal interpreter caches carry no source authority.
            if "/__pycache__/" not in path or not path.endswith(".pyc"):
                raise AssertionError("Ignored 8.34 source refused")
    if untracked - ADDED:
        raise AssertionError("Unauthorized untracked 8.34 path")
    if head != PROTECTED:
        parents = _git("rev-list", "--parents", "-n", "1", head).decode("ascii").split()
        if parents != [head, PROTECTED]:
            raise AssertionError("8.34 wrong immediate product parent")
    actual_delta = {p for p in set(committed) | set(baseline) if committed.get(p) != baseline.get(p)}
    staged_delta = {p for p in set(index) | set(committed) if index.get(p) != committed.get(p)}
    if (head == PROTECTED and committed != baseline) or (head != PROTECTED and actual_delta != ENVELOPE):
        raise AssertionError("Unauthorized committed 8.34 scope")
    for path, ref in baseline.items():
        if path not in MODIFIED:
            if committed.get(path) != ref or index.get(path) != ref:
                if path == "nayeon/desktop_alpha/window.py":
                    raise AssertionError("Postcommit entrypoint rollback refused")
                raise AssertionError("Frozen committed or staged production modified")
            # Bind every frozen tracked regular file to actual disk bytes;
            # diff cleanliness cannot prove bytes hidden by index flags. Keep
            # the historical production check/error, including nonregulars.
            if path in production or ref[0] in {"100644", "100755"}:
                data = _raw_frozen_disk(path)
                prefix = b"blob " + str(len(data)).encode("ascii") + b"\0"
                if hashlib.sha1(prefix + data).hexdigest() != ref[1]:
                    if path in production:
                        raise AssertionError("Frozen production worktree bytes modified")
                    raise AssertionError("Frozen tracked worktree bytes modified")
    if staged_delta and (head != PROTECTED or staged_delta != ENVELOPE):
        raise AssertionError("Partial 8.34 staged snapshot refused")
    rows = raw_disk.split(b"\0")
    if rows[-1:] != [b""] or len(rows) % 2 != 1:
        raise AssertionError("Malformed 8.34 worktree delta")
    disk_changed = set()
    for meta, name in zip(rows[:-1:2], rows[1:-1:2]):
        path = name.decode("utf-8", "strict")
        _path(path)
        if path not in MODIFIED or path in disk_changed:
            raise AssertionError("Unauthorized 8.34 worktree delta")
        fields = meta.split()
        if (len(fields) != 5 or fields[0] != b":100644"
                or fields[1] != b"100644" or fields[4] != b"M"
                or fields[2].decode("ascii") != index[path][1]
                or fields[3] != b"0" * 40):
            raise AssertionError("Wrong 8.34 worktree status/mode/blob")
        disk_changed.add(path)
    legacy = (head == PROTECTED and not staged_delta and not untracked
              and not any((ROOT / p).exists() for p in ADDED)
              and all(_blob_oid(_disk(p)) == baseline[p][1] for p in MODIFIED))
    if legacy:
        return "LEGACY"
    if set(CANDIDATE_SHA256) != ENVELOPE:
        raise AssertionError("Incomplete 8.34 pin manifest")
    if any(type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value)
           or value == "0" * 64 for value in CANDIDATE_SHA256.values()):
        raise AssertionError("Unfinalised 8.34 candidate pins")
    expected = dict(baseline)
    for path in ENVELOPE:
        data = _disk(path)
        if _digest(path, data) != CANDIDATE_SHA256[path]:
            raise AssertionError("PARTIAL or unapproved 8.34 candidate bytes: " + path)
        if path.startswith("nayeon/"):
            old._no_unsafe_imports(path, data)
        expected[path] = ("100644", _blob_oid(data))
    for path in MODIFIED:
        if baseline.get(path, (None,))[0] != "100644":
            raise AssertionError("Wrong protected 8.34 file mode")
        if expected[path] == baseline[path]:
            raise AssertionError("Incomplete 8.34 modified scope")
    if any(p in baseline for p in ADDED):
        raise AssertionError("8.34 addition already in protected history")
    if head == PROTECTED:
        if staged_delta:
            if index != expected or untracked or disk_changed:
                raise AssertionError("8.34 index/disk disagreement")
            state = "EXACT_STAGED"
        else:
            if index != baseline or untracked != ADDED or disk_changed != MODIFIED:
                raise AssertionError("PARTIAL 8.34 preparation")
            state = "COMPLETE_UNSTAGED"
    else:
        if committed != expected or index != expected or untracked or disk_changed:
            raise AssertionError("8.34 committed/index/disk disagreement")
        state = "EXACT_CHILD"
    # Raw full diff, no rename hiding, checks mode/type/status/parent as well as
    # inventories. Exact source blobs are already bound by expected above.
    if staged_delta or head != PROTECTED:
        args = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
        raw = _git(*args, "--cached") if staged_delta else _git(*args, PROTECTED, head)
        rows = raw.split(b"\0")
        if rows[-1:] != [b""] or len(rows) != 2 * len(ENVELOPE) + 1:
            raise AssertionError("Malformed 8.34 raw delta")
        seen = set()
        for meta, name in zip(rows[:-1:2], rows[1:-1:2]):
            path = name.decode("utf-8", "strict")
            _path(path)
            if path not in ENVELOPE or path in seen:
                raise AssertionError("Unauthorized 8.34 raw delta")
            oldref = baseline.get(path, ("000000", "0" * 40))
            mode, oid = expected[path]
            wanted = f":{oldref[0]} {mode} {oldref[1]} {oid} {'A' if path in ADDED else 'M'}".encode()
            if meta != wanted:
                raise AssertionError("Wrong 8.34 raw status/mode/blob")
            seen.add(path)
    return state


def current_source_oid(path):
    """Current bytes require full successor proof; old literal pins stay frozen."""
    assert_834_integrity()
    if path not in prior.APPROVED_SOURCE_SHA256:
        raise AssertionError("Unlisted 8.30 source")
    return _blob_oid(_disk(path))


# Frozen 8.34 implementation is not weakened. Synthetic 8.34 history tests
# must select it explicitly; every ordinary current admission is routed to the
# exact independent 8.36 successor, never a HEAD-dependent fallback.
_assert_834_historical = assert_834_integrity


def assert_834_integrity():
    from tests.phase_8_36_scope_migration import assert_836_integrity
    return assert_836_integrity()
