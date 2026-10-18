"""Exact sixteen-path 8.33 successor; immutable 8.30/8.31 history remains proof.

Pins describe a candidate, not independent approval. The helper's self entry is
SHA256 with ONLY its own literal value zeroed (avoids a self-hash fixed point).
The externally reported raw sixteen-file manifest must be reviewed separately.
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

ROOT = prior.ROOT
PROTECTED = "03f247d8627bf1c51105f73b9de5c6bbdf389cf9"
PROTECTED_TREE = "4caa8a65b22041b6e1abc2fdf4d249d181082431"
PROTECTED_TAG = "nayeon-v1-phase-8-32-lifecycle-assurance-01"
PROTECTED_TAG_OBJECT = "9fb0f2da5d0e3666fad0c1534fe80fc3b6086c34"
ADDED = frozenset({
    "docs/phase_8_33_offline_delayed_completion_rfc.md",
    "docs/phase_8_33_offline_delayed_completion_review.md",
    "nayeon/desktop_alpha/offline_completion_admission.py",
    "tests/test_phase_833_offline_completion.py",
    "tests/test_phase_833_tk_completion.py",
    "tests/phase_8_33_scope_migration.py",
    "tests/test_phase_833_scope_integrity.py",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "tests/phase_8_32_scope_migration.py",
    "tests/test_phase_832_scope_integrity.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    "tests/phase_8_30_scope_migration.py",
    ".codex/CURRENT_STATE.md",
    "docs/pre_829_shutdown_ownership_failure_ledger.md",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase_8_33_scope_migration.py"
# Candidate evidence only. Host must reconcile the reserved context path and
# finalise all pins/self pin before this exact sixteen-path guard can admit it.
CANDIDATE_SHA256 = {
    "docs/phase_8_33_offline_delayed_completion_rfc.md": "a9280400e87594e3cb634c1ed5dacf7e07cd9ed205db29899f529934a6be2191",
    "docs/phase_8_33_offline_delayed_completion_review.md": "061d0f82716ac39a00c5408798e0aed82b8c56a1dc42fa5ffc3b1da4e9617ea4",
    "nayeon/desktop_alpha/offline_completion_admission.py": "e2471a0dbc226959a609d21e90c26891cab81a172323b2afada364fe856c7bf4",
    "tests/test_phase_833_offline_completion.py": "9e4a0ae706de22f85307714801f0bbcd63f343571dbc37fd83d5bfdf45b0897f",
    "tests/test_phase_833_tk_completion.py": "4144e3efa6a753e27b3f5a2fb0713b72d401ee947254068e721109017a443f2f",
    "tests/phase_8_33_scope_migration.py": "f0766e2c6dc91f007ea3d9dea22a1ef22e8f2d1a46d8282f90e6b419b5c69a01",
    "tests/test_phase_833_scope_integrity.py": "d2cdef4307fb1bce62f50855282b47f4e85348b2f1efb9f15cf1ff9cff1b216f",
    "nayeon/desktop_alpha/application.py": "f68ca2cbdb00da8722a040d9877829ec3eae98a0c72fc3f86e034703e00d0a26",
    "nayeon/desktop_alpha/workspace_window.py": "240423f7423b77ffc80ea22568af93963b0d2cf09b6938a5917f19b5682d72c4",
    "tests/phase_8_32_scope_migration.py": "d658f8442c97225ac9ed1ddef187e25a6d423e6b2eeda3fcd6771fe47e11be02",
    "tests/test_phase_832_scope_integrity.py": "1892597e8469aa715ef73ff267bebb6edc99be091a4735abd04f44742ab355dc",
    "tests/test_phase_830_scope_integrity.py": "173c9fbce0d7844cdf50ee3c76580df71904960f43c68205dc98bf8ce103ed89",
    "tests/test_phase_831_scope_integrity.py": "7b91541715158410673eb63ade7987ad0a56a41cb60d2d695c23cfa0bc6f8846",
    "tests/phase_8_30_scope_migration.py": "8661cc9f5901c7f25a71f8ef64f273dcda718b108f44f78f91037c533861780d",
    ".codex/CURRENT_STATE.md": "32a534729a0d536c506a6e76ebbdbe11c3c7bb337b7b5b936dfbfed98e8f747d",
    "docs/pre_829_shutdown_ownership_failure_ledger.md": "295b5fcddc4e66870fa031464f6d169d4291b85952db167844fa4850fb44c7f8",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SELF_PIN = re.compile(rb'("tests/phase_8_33_scope_migration.py": ")[0-9a-f]{64}(",)')


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
        raise AssertionError("Noncanonical 8.33 Git pathname")
    for root in ("tests", "docs", ".codex"):
        first = path.split("/", 1)[0]
        if first.casefold() == root and first != root:
            raise AssertionError("Aliased 8.33 scope root")
    return production


def _inventory(raw, *, index=False):
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.33 Git inventory")
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
            raise AssertionError("Malformed 8.33 Git inventory") from None
        alias = path.casefold()
        if path in result or alias in aliases:
            raise AssertionError("Repeated or aliased 8.33 Git path")
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
        raise AssertionError("Malformed 8.33 index flags")
    seen = set()
    for row in raw.split(b"\0")[:-1]:
        if not row.startswith(b"H "):
            raise AssertionError("Unsupported 8.33 index flags")
        try:
            path = row[2:].decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Malformed 8.33 index flags") from None
        _path(path)
        if path in seen or path not in index:
            raise AssertionError("Repeated or unbound 8.33 index flags")
        seen.add(path)
    if seen != set(index):
        raise AssertionError("Incomplete 8.33 index flags")


def _disk(path):
    candidate = ROOT / path
    prior._reject_linked_parents(candidate)
    try:
        info = candidate.lstat()
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
                or info.st_nlink != 1):
            raise AssertionError("Linked or nonregular 8.33 candidate")
        return candidate.read_bytes()
    except OSError:
        raise AssertionError("Missing 8.33 candidate") from None


def _raw_frozen_disk(path):
    # Git blob identity binds original bytes, including CRLF and binary data.
    # Candidate source pins deliberately retain _disk's historical normal form.
    _path(path)
    candidate = ROOT / path
    prior._reject_linked_parents(candidate)
    try:
        info = candidate.lstat()
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
                or info.st_nlink != 1):
            raise AssertionError("Linked or nonregular 8.33 frozen file")
        return candidate.read_bytes()
    except OSError:
        raise AssertionError("Missing 8.33 frozen file") from None


def _digest(path, data):
    if path == SELF:
        data, count = SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], data)
        if count != 1:
            raise AssertionError("Malformed 8.33 self pin")
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
    legacy._history()
    if _seal_oid("rev-parse", PROTECTED + "^{tree}") != PROTECTED_TREE:
        raise AssertionError("Frozen 8.32 full tree changed")
    if _git("rev-list", "--parents", "-n", "1", PROTECTED).decode("ascii").split() != [PROTECTED, legacy.PROTECTED]:
        raise AssertionError("Wrong protected parent")
    if (_seal_oid("show-ref", "--verify", "--hash", "--", "refs/tags/" + PROTECTED_TAG) != PROTECTED_TAG_OBJECT
            or _git("cat-file", "-t", PROTECTED_TAG_OBJECT) != b"tag\n"
            or _seal_oid("rev-parse", "--verify", "--end-of-options", PROTECTED_TAG_OBJECT + "^{}") != PROTECTED
            or _git("cat-file", "-t", PROTECTED) != b"commit\n"):
        raise AssertionError("Frozen seal changed")
    tree = _tree(PROTECTED)
    for path, expected in legacy.CANDIDATE_SHA256.items():
        data = _git("show", PROTECTED + ":" + path)
        if (legacy._digest(path, prior._normal(data)) != expected
                or tree.get(path) != ("100644", _blob_oid(data))):
            raise AssertionError("Unapproved sealed 8.32 bytes")
    return {p: ref for p, ref in tree.items() if prior._production_git_path(p)}


def _blob_oid(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _others(*args):
    raw = _git("ls-files", "--others", *args, "-z")
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.33 untracked inventory")
    result = set()
    for record in raw.split(b"\0")[:-1]:
        path = record.decode("utf-8", "strict")
        _path(path)
        if path in result:
            raise AssertionError("Repeated 8.33 untracked path")
        result.add(path)
    return result


def assert_833_integrity():
    """Return LEGACY / COMPLETE_UNSTAGED / EXACT_STAGED / EXACT_CHILD.

    This proves candidate shape and pinned bytes only; independent GO and full
    authoritative Windows results are separate human gates.
    """
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported Git object format")
    head = _git("rev-parse", "HEAD").decode("ascii").strip()
    if not HEX40.fullmatch(head):
        raise AssertionError("Malformed 8.33 HEAD")
    branch = _git("branch", "--show-current").decode("utf-8").strip()
    if branch not in {"", "nayeon-v1"}:
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
                raise AssertionError("Ignored 8.33 source refused")
    if untracked - ADDED:
        raise AssertionError("Unauthorized untracked 8.33 path")
    if head != PROTECTED:
        parents = _git("rev-list", "--parents", "-n", "1", head).decode("ascii").split()
        if parents != [head, PROTECTED]:
            raise AssertionError("8.33 wrong immediate product parent")
    actual_delta = {p for p in set(committed) | set(baseline) if committed.get(p) != baseline.get(p)}
    staged_delta = {p for p in set(index) | set(committed) if index.get(p) != committed.get(p)}
    if (head == PROTECTED and committed != baseline) or (head != PROTECTED and actual_delta != ENVELOPE):
        raise AssertionError("Unauthorized committed 8.33 scope")
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
        raise AssertionError("Partial 8.33 staged snapshot refused")
    rows = raw_disk.split(b"\0")
    if rows[-1:] != [b""] or len(rows) % 2 != 1:
        raise AssertionError("Malformed 8.33 worktree delta")
    disk_changed = set()
    for meta, name in zip(rows[:-1:2], rows[1:-1:2]):
        path = name.decode("utf-8", "strict")
        _path(path)
        if path not in MODIFIED or path in disk_changed:
            raise AssertionError("Unauthorized 8.33 worktree delta")
        fields = meta.split()
        if (len(fields) != 5 or fields[0] != b":100644"
                or fields[1] != b"100644" or fields[4] != b"M"
                or fields[2].decode("ascii") != index[path][1]
                or fields[3] != b"0" * 40):
            raise AssertionError("Wrong 8.33 worktree status/mode/blob")
        disk_changed.add(path)
    legacy = (head == PROTECTED and not staged_delta and not untracked
              and not any((ROOT / p).exists() for p in ADDED)
              and all(prior._oid(_disk(p)) == baseline[p][1] for p in MODIFIED))
    if legacy:
        return "LEGACY"
    if set(CANDIDATE_SHA256) != ENVELOPE:
        raise AssertionError("Incomplete 8.33 pin manifest")
    if any(type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value)
           or value == "0" * 64 for value in CANDIDATE_SHA256.values()):
        raise AssertionError("Unfinalised 8.33 candidate pins")
    expected = dict(baseline)
    for path in ENVELOPE:
        data = _disk(path)
        if _digest(path, data) != CANDIDATE_SHA256[path]:
            raise AssertionError("PARTIAL or unapproved 8.33 candidate bytes: " + path)
        if path.startswith("nayeon/"):
            old._no_unsafe_imports(path, data)
        expected[path] = ("100644", prior._oid(data))
    for path in MODIFIED:
        if baseline.get(path, (None,))[0] != "100644":
            raise AssertionError("Wrong protected 8.33 file mode")
        if expected[path] == baseline[path]:
            raise AssertionError("Incomplete 8.33 modified scope")
    if any(p in baseline for p in ADDED):
        raise AssertionError("8.33 addition already in protected history")
    if head == PROTECTED:
        if staged_delta:
            if index != expected or untracked or disk_changed:
                raise AssertionError("8.33 index/disk disagreement")
            state = "EXACT_STAGED"
        else:
            if index != baseline or untracked != ADDED or disk_changed != MODIFIED:
                raise AssertionError("PARTIAL 8.33 preparation")
            state = "COMPLETE_UNSTAGED"
    else:
        if committed != expected or index != expected or untracked or disk_changed:
            raise AssertionError("8.33 committed/index/disk disagreement")
        state = "EXACT_CHILD"
    # Raw full diff, no rename hiding, checks mode/type/status/parent as well as
    # inventories. Exact source blobs are already bound by expected above.
    if staged_delta or head != PROTECTED:
        args = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
        raw = _git(*args, "--cached") if staged_delta else _git(*args, PROTECTED, head)
        rows = raw.split(b"\0")
        if rows[-1:] != [b""] or len(rows) != 2 * len(ENVELOPE) + 1:
            raise AssertionError("Malformed 8.33 raw delta")
        seen = set()
        for meta, name in zip(rows[:-1:2], rows[1:-1:2]):
            path = name.decode("utf-8", "strict")
            _path(path)
            if path not in ENVELOPE or path in seen:
                raise AssertionError("Unauthorized 8.33 raw delta")
            oldref = baseline.get(path, ("000000", "0" * 40))
            mode, oid = expected[path]
            wanted = f":{oldref[0]} {mode} {oldref[1]} {oid} {'A' if path in ADDED else 'M'}".encode()
            if meta != wanted:
                raise AssertionError("Wrong 8.33 raw status/mode/blob")
            seen.add(path)
    return state
