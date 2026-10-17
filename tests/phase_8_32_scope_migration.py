"""Exact fourteen-path 8.32 successor; immutable 8.30/8.31 history remains proof.

Pins describe a candidate, not independent approval. The helper's self entry is
SHA256 with ONLY its own literal value zeroed (avoids a self-hash fixed point).
The externally reported raw fourteen-file manifest must be reviewed separately.
No Git writes, environmental approval switch, descendant wildcard or live effects.
"""
from __future__ import annotations

import hashlib
import re
import stat
import unicodedata

from tests import phase_8_30_scope_migration as prior
from tests import phase_8_31_scope_migration as old

ROOT = prior.ROOT
PROTECTED = "c9d1b012b79b01897439775fb344819a9cf5367a"
PROTECTED_PRODUCT_TREE = "20094cd82e13be48c6cfca34dbac0a2725de2a10"
ADDED = frozenset({
    "docs/phase_8_32_reply_admission_rfc.md",
    "docs/phase_8_32_lifecycle_assurance_review.md",
    "tests/test_phase_832_lifecycle_assurance.py",
    "tests/phase_8_32_scope_migration.py",
    "tests/test_phase_832_scope_integrity.py",
})
MODIFIED = frozenset({
    "nayeon/desktop_alpha/application.py",
    "nayeon/desktop_alpha/workspace_window.py",
    "nayeon/desktop_alpha/presentation_window.py",
    "tests/test_phase_831_workspace.py",
    "tests/phase_8_31_scope_migration.py",
    "tests/test_phase_830_scope_integrity.py",
    "tests/test_phase_831_scope_integrity.py",
    ".codex/CURRENT_STATE.md",
    "docs/pre_829_shutdown_ownership_failure_ledger.md",
})
ENVELOPE = ADDED | MODIFIED
SELF = "tests/phase_8_32_scope_migration.py"
# Literal final candidate pins; ZERO placeholders are fail-closed until finalised.
CANDIDATE_SHA256 = {
    "docs/phase_8_32_reply_admission_rfc.md": "8d464121d27914d0f7d52b24578767d05ad0c72625b93cbdfd0a90c34f0c152d",
    "docs/phase_8_32_lifecycle_assurance_review.md": "f9dea6c87a790c748a0283aff25e4f84051de23f99ec0c9ca7bbbd181ca8656c",
    "tests/test_phase_832_lifecycle_assurance.py": "99b7ab4c9cbcb22d44ab4ddd734345e681b54fa317b1f0e1951683b10830dd54",
    "tests/phase_8_32_scope_migration.py": "e79b338eeb7d79e73b887c94a2245e1f11d2d7cdfb04e7b0bdadb6d81249598f",
    "tests/test_phase_832_scope_integrity.py": "e185b0a144293cd37072a6b299e56feb13de5ea3409930e985b900437bfc46b3",
    "nayeon/desktop_alpha/application.py": "389e67caf1851cb95d6b3cca7b120d21d6724d9d514e952445311eb7ecee97be",
    "nayeon/desktop_alpha/workspace_window.py": "85a2227e07921b88bacc6719ff62aa6107b83a0e0882ccc89e2cdb9d35cda1a0",
    "nayeon/desktop_alpha/presentation_window.py": "fd19160fc76a8334b9447c0ef3307cb8211c71efa679eafaf31d3289208ab9b0",
    "tests/test_phase_831_workspace.py": "33a5a624b3242ef95f0a52572cb2fe4c224bcd9a048bb94b1b7a29b4f45c1125",
    "tests/phase_8_31_scope_migration.py": "f1a0772533803b69719ad5af1d8ad1f84946b194259e682cbf809bcff83a5c99",
    "tests/test_phase_830_scope_integrity.py": "760ef3f881f3acc214a0419e5691cb17552e745d3fbc9f3f98245c7e7eadf532",
    "tests/test_phase_831_scope_integrity.py": "082dcd64ecf11ae3507be3db0c63a69d32ee92f41196f25c9b99f3aa7bb73a5c",
    ".codex/CURRENT_STATE.md": "6f1432c27a13e0c37bba707881d766899148a9e14a937b95317f8b3ac164c58f",
    "docs/pre_829_shutdown_ownership_failure_ledger.md": "4827b5be8bfd2d5a125cc680a4964f1ce65c0f0e2862c2c7dc9c21b3e973a872",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SELF_PIN = re.compile(rb'("tests/phase_8_32_scope_migration.py": ")[0-9a-f]{64}(",)')
SEALS = {
    "nayeon-v1-phase-8-30-offline-workspace-product-01":
        ("3f9e236a2cecec90cb5302df2e4348e6f96611a2", old.PRODUCT_830),
    "nayeon-v1-phase-8-30-handover-documentation-01":
        ("4e2554d30bc49f4b788b8998dd8326ae2fd15c80", "8b2fecf00d48324a187d931156cfa463bbd0aa67"),
    "nayeon-v1-phase-8-30-offline-workspace-rfc-go-01":
        ("0c986ea1bf859c710a6d4cb7fe92f7e0f29658a2", "058c622a04a26a882c773533c568371c53b9b140"),
    "nayeon-v1-phase-8-31-offline-conversation-session-product-01":
        ("2db31d688c12f9a845d903a2d1db14a9d2aa7a5e", old.PRODUCT_COMMIT_831),
    "nayeon-v1-phase-8-31-offline-conversation-handover-01":
        ("2d74f06ceac02781edee5a0bd15c4361cc5ec03c", old.DOC_COMMIT_831),
    "nayeon-v1-phase-8-31-postdocs-guard-maintenance-01":
        ("48907e80d9c69916d521b18f2f4f8c1bfab76e00", PROTECTED),
}


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
        raise AssertionError("Noncanonical 8.32 Git pathname")
    for root in ("tests", "docs", ".codex"):
        first = path.split("/", 1)[0]
        if first.casefold() == root and first != root:
            raise AssertionError("Aliased 8.32 scope root")
    return production


def _inventory(raw, *, index=False):
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.32 Git inventory")
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
            raise AssertionError("Malformed 8.32 Git inventory") from None
        alias = path.casefold()
        if path in result or alias in aliases:
            raise AssertionError("Repeated or aliased 8.32 Git path")
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
        raise AssertionError("Malformed 8.32 index flags")
    seen = set()
    for row in raw.split(b"\0")[:-1]:
        if not row.startswith(b"H "):
            raise AssertionError("Unsupported 8.32 index flags")
        try:
            path = row[2:].decode("utf-8", "strict")
        except UnicodeError:
            raise AssertionError("Malformed 8.32 index flags") from None
        _path(path)
        if path in seen or path not in index:
            raise AssertionError("Repeated or unbound 8.32 index flags")
        seen.add(path)
    if seen != set(index):
        raise AssertionError("Incomplete 8.32 index flags")


def _disk(path):
    candidate = ROOT / path
    prior._reject_linked_parents(candidate)
    try:
        info = candidate.lstat()
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
                or info.st_nlink != 1):
            raise AssertionError("Linked or nonregular 8.32 candidate")
        return prior._normal(candidate.read_bytes())
    except OSError:
        raise AssertionError("Missing 8.32 candidate") from None


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
            raise AssertionError("Linked or nonregular 8.32 frozen file")
        return candidate.read_bytes()
    except OSError:
        raise AssertionError("Missing 8.32 frozen file") from None


def _digest(path, data):
    if path == SELF:
        data, count = SELF_PIN.subn(lambda m: m[1] + b"0" * 64 + m[2], data)
        if count != 1:
            raise AssertionError("Malformed 8.32 self pin")
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
    # Preserve the original historical read order and production comparisons.
    base = _historical_tree(prior.PROTECTED)
    product830 = _historical_tree(old.PRODUCT_830)
    if set(product830) != set(base) | set(prior.APPROVED_NEW_SHA256):
        raise AssertionError("Missing or unapproved committed 8.30 source")
    for path, ref in base.items():
        if path not in prior.APPROVED_MODIFIED_SHA256 and product830.get(path) != ref:
            raise AssertionError("Frozen historical 8.29 source changed")
    for path, expected in prior.APPROVED_SOURCE_SHA256.items():
        data = _git("show", old.PRODUCT_830 + ":" + path)
        if old._sha(data) != expected:
            raise AssertionError("Unapproved 8.30 source bytes")
        if product830.get(path) != ("100644", prior._oid(data)):
            raise AssertionError("Missing or unapproved committed 8.30 source")
    product831 = _historical_tree(old.PRODUCT_COMMIT_831)
    if set(product831) != set(product830) | set(old.NEW):
        raise AssertionError("Unauthorized historical 8.31 inventory")
    for path, expected in old.ALL_831.items():
        data = _git("show", old.PRODUCT_COMMIT_831 + ":" + path)
        if old._sha(data) != expected:
            raise AssertionError("Unapproved 8.31 source bytes")
        if product831.get(path) != ("100644", prior._oid(data)):
            raise AssertionError("Unapproved committed 8.31 source")
    for path, ref in product830.items():
        if path not in old.MODIFIED and product831.get(path) != ref:
            raise AssertionError("Frozen historical 8.30 source changed")
    protected = _historical_tree(PROTECTED)
    if protected != product831 or _historical_tree(old.DOC_COMMIT_831) != product831:
        raise AssertionError("Maintenance descendant modified production")
    if _git("rev-parse", PROTECTED + ":nayeon").decode("ascii").strip() != PROTECTED_PRODUCT_TREE:
        raise AssertionError("Protected product tree changed")
    ancestry = ((PROTECTED, old.DOC_COMMIT_831),
                (old.DOC_COMMIT_831, old.PRODUCT_COMMIT_831),
                (old.PRODUCT_COMMIT_831, old.PARENT_831))
    for child, parent in ancestry:
        if _git("rev-list", "--parents", "-n", "1", child).decode("ascii").split() != [child, parent]:
            raise AssertionError("Wrong protected parent")
    for tag, (obj, commit) in SEALS.items():
        ref = "refs/tags/" + tag
        # Exact ref existence cannot be proved with revision-name resolution:
        # even refs/tags/name can fall back to refs/refs/tags/name. Bind the
        # annotated object first, then use only immutable OIDs for type/peel.
        if (_seal_oid("show-ref", "--verify", "--hash", "--", ref) != obj
                or _git("cat-file", "-t", obj) != b"tag\n"
                or _seal_oid("rev-parse", "--verify", "--end-of-options", obj + "^{}") != commit
                or _git("cat-file", "-t", commit) != b"commit\n"):
            raise AssertionError("Frozen seal changed")
    return protected


def _others(*args):
    raw = _git("ls-files", "--others", *args, "-z")
    if type(raw) is not bytes or (raw and not raw.endswith(b"\0")):
        raise AssertionError("Malformed 8.32 untracked inventory")
    result = set()
    for record in raw.split(b"\0")[:-1]:
        path = record.decode("utf-8", "strict")
        _path(path)
        if path in result:
            raise AssertionError("Repeated 8.32 untracked path")
        result.add(path)
    return result


def assert_832_integrity():
    """Return LEGACY / COMPLETE_UNSTAGED / EXACT_STAGED / EXACT_CHILD.

    This proves candidate shape and pinned bytes only; independent GO and full
    authoritative Windows results are separate human gates.
    """
    if _git("rev-parse", "--show-object-format").decode("ascii").strip() != "sha1":
        raise AssertionError("Unsupported Git object format")
    head = _git("rev-parse", "HEAD").decode("ascii").strip()
    if not HEX40.fullmatch(head):
        raise AssertionError("Malformed 8.32 HEAD")
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
                raise AssertionError("Ignored 8.32 source refused")
    if untracked - ADDED:
        raise AssertionError("Unauthorized untracked 8.32 path")
    if head != PROTECTED:
        parents = _git("rev-list", "--parents", "-n", "1", head).decode("ascii").split()
        if parents != [head, PROTECTED]:
            raise AssertionError("8.32 wrong immediate product parent")
    actual_delta = {p for p in set(committed) | set(baseline) if committed.get(p) != baseline.get(p)}
    staged_delta = {p for p in set(index) | set(committed) if index.get(p) != committed.get(p)}
    if (head == PROTECTED and committed != baseline) or (head != PROTECTED and actual_delta != ENVELOPE):
        raise AssertionError("Unauthorized committed 8.32 scope")
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
        raise AssertionError("Partial 8.32 staged snapshot refused")
    rows = raw_disk.split(b"\0")
    if rows[-1:] != [b""] or len(rows) % 2 != 1:
        raise AssertionError("Malformed 8.32 worktree delta")
    disk_changed = set()
    for meta, name in zip(rows[:-1:2], rows[1:-1:2]):
        path = name.decode("utf-8", "strict")
        _path(path)
        if path not in MODIFIED or path in disk_changed:
            raise AssertionError("Unauthorized 8.32 worktree delta")
        fields = meta.split()
        if (len(fields) != 5 or fields[0] != b":100644"
                or fields[1] != b"100644" or fields[4] != b"M"
                or fields[2].decode("ascii") != index[path][1]
                or fields[3] != b"0" * 40):
            raise AssertionError("Wrong 8.32 worktree status/mode/blob")
        disk_changed.add(path)
    legacy = (head == PROTECTED and not staged_delta and not untracked
              and not any((ROOT / p).exists() for p in ADDED)
              and all(prior._oid(_disk(p)) == baseline[p][1] for p in MODIFIED))
    if legacy:
        return "LEGACY"
    if set(CANDIDATE_SHA256) != ENVELOPE:
        raise AssertionError("Incomplete 8.32 pin manifest")
    expected = dict(baseline)
    for path in ENVELOPE:
        data = _disk(path)
        if _digest(path, data) != CANDIDATE_SHA256[path]:
            raise AssertionError("PARTIAL or unapproved 8.32 candidate bytes: " + path)
        if path.startswith("nayeon/"):
            old._no_unsafe_imports(path, data)
        expected[path] = ("100644", prior._oid(data))
    for path in MODIFIED:
        if baseline.get(path, (None,))[0] != "100644":
            raise AssertionError("Wrong protected 8.32 file mode")
        if expected[path] == baseline[path]:
            raise AssertionError("Incomplete 8.32 modified scope")
    if any(p in baseline for p in ADDED):
        raise AssertionError("8.32 addition already in protected history")
    if head == PROTECTED:
        if staged_delta:
            if index != expected or untracked or disk_changed:
                raise AssertionError("8.32 index/disk disagreement")
            state = "EXACT_STAGED"
        else:
            if index != baseline or untracked != ADDED or disk_changed != MODIFIED:
                raise AssertionError("PARTIAL 8.32 preparation")
            state = "COMPLETE_UNSTAGED"
    else:
        if committed != expected or index != expected or untracked or disk_changed:
            raise AssertionError("8.32 committed/index/disk disagreement")
        state = "EXACT_CHILD"
    # Raw full diff, no rename hiding, checks mode/type/status/parent as well as
    # inventories. Exact source blobs are already bound by expected above.
    if staged_delta or head != PROTECTED:
        args = ("diff", "--no-renames", "--raw", "--no-abbrev", "-z")
        raw = _git(*args, "--cached") if staged_delta else _git(*args, PROTECTED, head)
        rows = raw.split(b"\0")
        if rows[-1:] != [b""] or len(rows) != 2 * len(ENVELOPE) + 1:
            raise AssertionError("Malformed 8.32 raw delta")
        seen = set()
        for meta, name in zip(rows[:-1:2], rows[1:-1:2]):
            path = name.decode("utf-8", "strict")
            _path(path)
            if path not in ENVELOPE or path in seen:
                raise AssertionError("Unauthorized 8.32 raw delta")
            oldref = baseline.get(path, ("000000", "0" * 40))
            mode, oid = expected[path]
            wanted = f":{oldref[0]} {mode} {oldref[1]} {oid} {'A' if path in ADDED else 'M'}".encode()
            if meta != wanted:
                raise AssertionError("Wrong 8.32 raw status/mode/blob")
            seen.add(path)
    return state


def current_source_oid(path):
    """Current-reader accessor; never replaces the historical literal pins."""
    assert_832_integrity()
    if path not in prior.APPROVED_SOURCE_SHA256:
        raise AssertionError("Unlisted 8.30 source")
    return prior._oid(_disk(path))
