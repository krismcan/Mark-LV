"""P245 read-only current-source diagnostic; never an effect or release authority.

Original P76 and historical test outcomes remain unchanged and unwaived.
This diagnostic does not replace historical admission or approve current production.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import tempfile

ROOT = Path(os.path.abspath(__file__)).parents[1]
BASE = "da9c436a177b3ec68db0eff2b610180b745bfb2b"
HISTORICAL = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
BRANCH = "byok-c1-p245-p76-current-source-20261115"
HISTORICAL_P76_BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
TAG = "nayeon-v1-phase-10-3-synthetic-provenance-redaction-01"
TAG_OID = "ed68953eaacee301592c6349a590a17be9638be5"
TAG_TARGET = "cacb5c320d26ffa28faf1f15a5e088029ee1453b"
ADDED = frozenset({
    "scripts/p245_p76_current_source.py",
    "tests/test_p245_p76_current_source.py",
    ".github/workflows/p245-p76-current-source.yml",
    "docs/byok-c1-p245-p76-current-source.md",
})
FROZEN = {
    "tests/phase8_byok_c1_p76_scope.py": "1C42912D9FC550DEA56C9BA9BB70D9568F298223B5514AF8D03C1723AAAD3327",
    "tests/test_phase8_byok_b_scope_integrity.py": "65DAD89298A587D6BB5DDE5455DF4D701BB1A1FD9A7A96CECF3E647800E3AE8B",
    "tests/test_phase_834_scope_integrity.py": "8DC69EC770EA008DFF9CD13E15299A73E38044F1671FD4FE78FBE2A431CCF57A",
    "tests/phase10_3_scope_migration.py": "540A1BE7C6FF23929B17E8A2F8272083829A65C35A76D1755A5284C958AFBEFF",
    "tests/phase8_byok_b_scope_migration.py": "84CED2F31F5DAF985DE462C384ABDFE47F8B705425F8BDEFB8CF1E04E56EE010",
    "tests/phase_8_34_scope_migration.py": "59442121254B42949640161FB7DBD47E90F3E77E6045F258A1DA130B640C8D43",
}
ORIGINAL_FAILURE_IDS = (
    "tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay",
    "tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected",
    "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission",
    "tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route",
)
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_GIT_BYTES = 16 * 1024 * 1024
MAX_PATHS = 20000


class CurrentSourceRefused(AssertionError):
    """Non-privileged diagnostic refusal; never returns an admission token."""


def refuse(reason: str) -> None:
    raise CurrentSourceRefused("P245 current-source diagnostic refused: " + reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in tuple(env):
        if key.upper().startswith(("GIT_", "P134_")):
            env.pop(key, None)
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0",
               GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1")
    return env


def git(*args: str) -> bytes:
    try:
        # Spool output so hostile Git replies cannot grow Python's heap unboundedly.
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            child = subprocess.run(
                ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                 "-C", str(ROOT), *args], shell=False,
                stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                timeout=35, check=False, env=environment()
            )
            if child.returncode != 0:
                refuse("immutable Git operation failed")
            if output.tell() > MAX_GIT_BYTES or errors.tell() > MAX_GIT_BYTES:
                refuse("oversized Git reply")
            output.seek(0)
            return output.read(MAX_GIT_BYTES + 1)
    except (OSError, subprocess.TimeoutExpired):
        refuse("immutable Git operation unavailable")


def canonical_path(rel: str) -> None:
    if (not isinstance(rel, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", rel)
            or any(part in ("", ".", "..") for part in rel.split("/"))
            or any(part.casefold() == ".git" for part in rel.split("/"))):
        refuse("noncanonical source path")
    for part in rel.split("/"):
        if (part.endswith(".") or re.fullmatch(
                r"(?i)(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?", part)):
            refuse("Windows source alias")


def checked_node(node: Path) -> os.stat_result:
    """Check every ancestor, including ancestors above the checkout root."""
    for part in (*reversed(node.parents), node):
        try:
            meta = part.lstat()
        except OSError:
            refuse("source path missing")
        if stat.S_ISLNK(meta.st_mode) or getattr(meta, "st_file_attributes", 0) & 0x400:
            refuse("linked or reparse source path")
    if node.resolve(strict=True) != node.absolute():
        refuse("aliased source path")
    return meta


def bounded_file(node: Path, limit: int) -> tuple[bytes, list[int]]:
    try:
        before = checked_node(node)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            refuse("nonregular or hardlinked source")
        if before.st_size > limit:
            refuse("oversized source")
        with node.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        final = checked_node(node)
    except (OSError, ValueError):
        refuse("source read unavailable")
    # Windows lstat and descriptor fstat can expose different ctime values
    # for the same stable file. Require ctime continuity within each API,
    # while binding all four observations through the remaining metadata.
    stamps = [(s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns,
               s.st_nlink, s.st_mode) for s in (before, opened, after, final)]
    if (any(stamp != stamps[0] for stamp in stamps)
            or before.st_ctime_ns != final.st_ctime_ns
            or opened.st_ctime_ns != after.st_ctime_ns
            or any(getattr(s, "st_file_attributes", 0) & 0x400
                   for s in (before, opened, after, final))
            or len(raw) != before.st_size
            or len(raw) > limit):
        refuse("source changed during bounded raw read")
    return raw, [before.st_dev, before.st_ino]


def raw_source(rel: str) -> tuple[bytes, list[int]]:
    canonical_path(rel)
    return bounded_file(ROOT / rel, MAX_FILE_BYTES)


def source_file(rel: str) -> Path:
    """Reject traversal, noncanonical path, link and Windows reparse aliases."""
    if rel not in FROZEN and rel not in ADDED:
        refuse("unapproved source path")
    canonical_path(rel)
    node = ROOT / rel
    meta = checked_node(node)
    if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1 or meta.st_size > MAX_FILE_BYTES:
        refuse("nonregular source")
    return node


def blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def tree_oid(entries: dict[str, list[str]]) -> str:
    """Rebuild Git's complete tree hash to bind inventory completeness."""
    root = {}
    for rel, entry in entries.items():
        canonical_path(rel)
        parts = rel.split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                refuse("conflicting tree path")
        if parts[-1] in node:
            refuse("conflicting tree entry")
        node[parts[-1]] = entry

    def encode(node: dict) -> str:
        raw = bytearray()
        for name, value in sorted(node.items(), key=lambda item:
                                  item[0] + ("/" if isinstance(item[1], dict) else "")):
            if isinstance(value, dict):
                mode, oid = "40000", encode(value)
            else:
                mode, oid = value
            raw.extend(mode.encode("ascii") + b" " + name.encode("ascii") + b"\0" + bytes.fromhex(oid))
        return hashlib.sha1(b"tree " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

    return encode(root)


def head_entries() -> dict[str, list[str]]:
    raw = git("ls-tree", "-r", "-z", "--full-tree", "HEAD")
    if not raw.endswith(b"\0"):
        refuse("incomplete HEAD tree")
    entries = {}
    folded = set()
    prefixes = {}
    for record in raw[:-1].split(b"\0"):
        match = re.fullmatch(rb"(100644|100755) blob ([0-9a-f]{40})\t([^\0]+)", record)
        if match is None:
            refuse("unsupported HEAD tree entry")
        try:
            rel = match[3].decode("ascii")
        except UnicodeError:
            refuse("noncanonical HEAD path")
        canonical_path(rel)
        if rel.casefold() in folded:
            refuse("duplicate or aliased HEAD path")
        parts = rel.split("/")
        for length in range(1, len(parts) + 1):
            prefix = "/".join(parts[:length])
            previous = prefixes.setdefault(prefix.casefold(), prefix)
            if previous != prefix:
                refuse("aliased HEAD directory spelling")
        folded.add(rel.casefold())
        entries[rel] = [match[1].decode(), match[2].decode()]
    if not entries or len(entries) > MAX_PATHS:
        refuse("unsupported HEAD tree size")
    return entries


def index_entries() -> dict[str, list[str]]:
    # -v detects assume-unchanged/skip-worktree. --debug exposes every other
    # entry flag, including intent-to-add, fsmonitor-valid and extended flags.
    raw = git("ls-files", "--stage", "--debug", "-v", "-z")
    entries = {}
    while raw:
        header, separator, remainder = raw.partition(b"\0")
        match = re.fullmatch(rb"H (100644|100755) ([0-9a-f]{40}) 0\t([^\0]+)", header)
        debug = re.match(
            rb"  ctime: [0-9]+:[0-9]+\n  mtime: [0-9]+:[0-9]+\n"
            rb"  dev: [0-9]+\tino: [0-9]+\n  uid: [0-9]+\tgid: [0-9]+\n"
            rb"  size: [0-9]+\tflags: 0\n", remainder)
        if not separator or match is None or debug is None:
            refuse("unsupported index flags, stage or entry")
        try:
            rel = match[3].decode("ascii")
        except UnicodeError:
            refuse("noncanonical index path")
        canonical_path(rel)
        if rel in entries or len(entries) >= MAX_PATHS:
            refuse("duplicate or oversized index")
        entries[rel] = [match[1].decode(), match[2].decode(), "0"]
        raw = remainder[debug.end():]
    index_path = Path(git("rev-parse", "--git-path", "index").strip().decode())
    if not index_path.is_absolute():
        index_path = ROOT / index_path
    raw_index, _ = bounded_file(index_path, MAX_GIT_BYTES)
    if parse_raw_index(raw_index) != entries:
        refuse("raw index and Git inventory differ")
    return entries


def parse_raw_index(raw: bytes) -> dict[str, list[str]]:
    """Authenticate v2/v3 index bytes before Git can normalize entry flags."""
    if (len(raw) < 32 or len(raw) > MAX_GIT_BYTES or raw[:4] != b"DIRC"
            or hashlib.sha1(raw[:-20]).digest() != raw[-20:]):
        refuse("malformed raw index checksum or header")
    version, count = struct.unpack_from(">II", raw, 4)
    if version not in {2, 3} or count > MAX_PATHS:
        refuse("unsupported raw index format")
    offset, end = 12, len(raw) - 20
    entries = {}
    for _ in range(count):
        start = offset
        if offset + 62 > end:
            refuse("truncated raw index entry")
        fields = struct.unpack_from(">10I20sH", raw, offset)
        flags = fields[11]
        if flags & 0xF000:
            refuse("unsupported raw index flags or stage")
        name_end = raw.find(b"\0", offset + 62, end)
        if name_end < 0 or flags != min(name_end - offset - 62, 0xFFF):
            refuse("malformed raw index path length")
        try:
            rel = raw[offset + 62:name_end].decode("ascii")
        except UnicodeError:
            refuse("noncanonical raw index path")
        canonical_path(rel)
        offset = start + ((name_end + 1 - start + 7) // 8) * 8
        if offset > end or any(raw[name_end:offset]):
            refuse("malformed raw index padding")
        mode = format(fields[6], "o")
        if mode not in {"100644", "100755"} or rel in entries:
            refuse("unsupported raw index mode or duplicate")
        entries[rel] = [mode, fields[10].hex(), "0"]
    while offset < end:
        if offset + 8 > end:
            refuse("truncated raw index extension")
        signature, size = struct.unpack_from(">4sI", raw, offset)
        # Fsmonitor, split and sparse indexes carry additional authority/state.
        # Only ordinary optional cache/ordering extensions are supported here.
        if signature not in {b"TREE", b"REUC", b"EOIE", b"IEOT"}:
            refuse("unsupported raw index extension")
        offset += 8 + size
        if offset > end:
            refuse("truncated raw index extension body")
    return entries


def complete_source() -> dict:
    tree = head_entries()
    if tree_oid(tree) != git("rev-parse", "HEAD^{tree}").strip().decode():
        refuse("complete inventory differs from HEAD tree object")
    index = index_entries()
    if {rel: value[:2] for rel, value in index.items()} != tree:
        refuse("complete index differs from HEAD tree")
    disk = {}
    identities = set()
    total = 0
    for rel, (mode, oid) in sorted(tree.items()):
        raw, identity = raw_source(rel)
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            refuse("oversized complete source")
        if tuple(identity) in identities:
            refuse("aliased source identity")
        identities.add(tuple(identity))
        if blob_oid(raw) != oid:
            refuse("tracked raw Git-byte mismatch: " + rel)
        if os.name != "nt":
            executable = bool((ROOT / rel).stat().st_mode & 0o111)
            if executable != (mode == "100755"):
                refuse("tracked disk mode mismatch")
        disk[rel] = {"blob_oid": oid, "sha256": digest(raw),
                     "size": len(raw), "identity": identity}
    if head_entries() != tree or index_entries() != index:
        refuse("tree or index changed during complete proof")
    return {"tree": tree, "index": index, "disk": disk}


def historical_branch_literal(raw: bytes) -> str:
    """Read AST literal only; never execute an archived source module."""
    nodes = ast.parse(raw).body
    matches = [node.value.value for node in nodes
               if isinstance(node, ast.Assign) and len(node.targets) == 1
               and isinstance(node.targets[0], ast.Name)
               and node.targets[0].id == "BRANCH"
               and isinstance(node.value, ast.Constant)
               and isinstance(node.value.value, str)]
    if len(matches) != 1:
        refuse("missing original P76 branch literal")
    return matches[0]


def validate_event(*, branch: str, head: str, ancestor: str = BASE) -> None:
    if (os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Windows"
            or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.environ.get("GITHUB_REPOSITORY") != "krismcan/Mark-LV"
            or os.environ.get("GITHUB_EVENT_NAME") != "push"):
        refuse("genuine hosted Windows event required")
    if (branch != BRANCH or ancestor != BASE or
            not isinstance(head, str) or HEX40.fullmatch(head) is None
            or os.environ.get("GITHUB_REF_NAME") != BRANCH
            or os.environ.get("GITHUB_SHA") != head):
        refuse("unapproved current branch, ancestry or signed event head")


def validate_historical_tag(expected: str = TAG_OID) -> None:
    if expected != TAG_OID:
        refuse("altered historical tag authority")
    oid = git("show-ref", "--verify", "--hash", "--", "refs/tags/" + TAG).strip().decode()
    if oid != TAG_OID or git("cat-file", "-t", oid) != b"tag\n":
        refuse("wrong immutable annotated tag object")
    if git("rev-parse", "--verify", "--end-of-options", oid + "^{}").strip().decode() != TAG_TARGET:
        refuse("wrong original tag target")
    raw = git("cat-file", "tag", oid)
    tag_blob = b"tag " + str(len(raw)).encode("ascii") + b"\0" + raw
    if hashlib.sha1(tag_blob).hexdigest() != TAG_OID:
        refuse("raw annotated tag object hash mismatch")
    if raw.split(b"\n")[:3] != [
        ("object " + TAG_TARGET).encode(), b"type commit", ("tag " + TAG).encode()
    ]:
        refuse("wrong raw annotated tag body")


def git_identity(*, branch: str, head: str) -> dict:
    if (git("rev-parse", "HEAD").strip().decode() != head or
            git("branch", "--show-current").strip().decode() != branch):
        refuse("live HEAD or branch differs")
    if (git("rev-parse", "--is-shallow-repository") != b"false\n" or
            git("rev-parse", "--show-object-format=storage") != b"sha1\n" or
            git("rev-parse", "--show-object-format=input") != b"sha1\n"):
        refuse("unexpected Git history or object format")
    if git("for-each-ref", "refs/replace").strip():
        refuse("Git object replacement refs")
    gitdir = Path(git("rev-parse", "--absolute-git-dir").strip().decode())
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").strip().decode())
    for directory in {gitdir, common}:
        # lexists also refuses a dangling graft alias. Linked worktrees can
        # use the common directory's graft file, so both locations matter.
        if os.path.lexists(directory / "info" / "grafts"):
            refuse("untrusted Git history grafts")
    validate_historical_tag()
    tree_oid = git("rev-parse", "HEAD^{tree}").strip().decode()
    if HEX40.fullmatch(tree_oid) is None:
        refuse("invalid HEAD tree identity")
    root_meta = checked_node(ROOT)
    return {"root": ROOT.as_posix(), "root_identity": [root_meta.st_dev, root_meta.st_ino],
            "git_dir": gitdir.as_posix(), "common_dir": common.as_posix(),
            "head": head, "branch": branch, "tree_oid": tree_oid,
            "object_format": "sha1", "replacements": [], "grafts": [],
            "tag": {"name": TAG, "oid": TAG_OID, "target": TAG_TARGET,
                    "raw_sha256": digest(git("cat-file", "tag", TAG_OID))}}


def verify_current(*, branch: str, head: str,
                   ancestor: str = BASE,
                   digest_override: dict[str, str] | None = None) -> dict:
    """Source-preserving C diagnostic only: no imported old tests or side effects."""
    validate_event(branch=branch, head=head, ancestor=ancestor)
    if git("rev-parse", "--show-toplevel").decode().strip().casefold() != ROOT.as_posix().casefold():
        refuse("wrong checkout root")
    identity = git_identity(branch=branch, head=head)
    if git("status", "--porcelain=v1", "-uall", "--ignored=matching").strip():
        refuse("dirty, ignored or untracked source")
    if git("merge-base", BASE, "HEAD").strip().decode() != BASE:
        refuse("not descendant of immutable P244")
    changed = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    if changed != ADDED:
        refuse("unapproved historical or product edits in P245")
    complete = complete_source()
    for rel in sorted(ADDED):
        if git("ls-tree", "--name-only", BASE, "--", rel).strip():
            refuse("claimed additive file already existed")
        raw, _ = raw_source(rel)
        if git("show", "HEAD:" + rel) != raw:
            refuse("new candidate Git/disk divergence")
    overrides = digest_override or {}
    if set(overrides) - set(FROZEN):
        refuse("unapproved source override path")
    witnesses = {}
    for rel, expected in sorted(FROZEN.items()):
        historic = git("show", HISTORICAL + ":" + rel)
        baseline = git("show", BASE + ":" + rel)
        live_git = git("show", "HEAD:" + rel)
        disk, _ = raw_source(rel)
        if (digest(historic) != expected or disk != historic or
                baseline != historic or live_git != historic or
                digest(disk) != overrides.get(rel, expected)):
            refuse("historical source/test byte witness mismatch: " + rel)
        witnesses[rel] = expected
    if historical_branch_literal(raw_source("tests/phase8_byok_c1_p76_scope.py")[0]) != HISTORICAL_P76_BRANCH:
        refuse("original P76 exact branch assertion modified")
    validate_historical_tag()
    if (complete_source() != complete or git_identity(branch=branch, head=head) != identity
            or git("status", "--porcelain=v1", "-uall", "--ignored=matching").strip()):
        refuse("Git branch or worktree changed during source proof")
    return {
        "schema": "P245-COMPLETE-SOURCE-V2", "candidate_source_pass": True,
        "real_key_admission": "NO-GO", "production_release": "HOLD",
        "head": head, "branch": branch, "parent": BASE,
        "source_identity": identity, "complete_source": complete,
        "candidate_files": {rel: complete["disk"][rel] for rel in sorted(ADDED)},
        "original_immutable_source": HISTORICAL,
        "frozen_sha256": witnesses, "historical_P76_wrong_branch_refusal_preserved": True,
        "four_original_P234_failures_unwaived": list(ORIGINAL_FAILURE_IDS),
        "qualified_approvals": "0/7", "full_product_regressions": "0/3",
    }


def canonical_witness(proof: dict) -> bytes:
    """Require a complete proof before comparison or any candidate PASS receipt."""
    try:
        if (proof["schema"] != "P245-COMPLETE-SOURCE-V2"
                or proof["candidate_source_pass"] is not True
                or proof["branch"] != BRANCH or proof["parent"] != BASE
                or HEX40.fullmatch(proof["head"]) is None
                or proof["original_immutable_source"] != HISTORICAL
                or proof["frozen_sha256"] != FROZEN
                or proof["four_original_P234_failures_unwaived"] != list(ORIGINAL_FAILURE_IDS)
                or proof["historical_P76_wrong_branch_refusal_preserved"] is not True
                or proof["real_key_admission"] != "NO-GO"
                or proof["production_release"] != "HOLD"
                or proof["qualified_approvals"] != "0/7"
                or proof["full_product_regressions"] != "0/3"):
            refuse("incomplete source witness")
        identity = proof["source_identity"]
        if (identity["head"] != proof["head"] or identity["branch"] != BRANCH
                or identity["object_format"] != "sha1"
                or identity["replacements"] != [] or identity["grafts"] != []
                or HEX40.fullmatch(identity["tree_oid"]) is None
                or identity["tag"]["name"] != TAG or identity["tag"]["oid"] != TAG_OID
                or identity["tag"]["target"] != TAG_TARGET
                or re.fullmatch(r"[0-9A-F]{64}", identity["tag"]["raw_sha256"]) is None
                or len(identity["root_identity"]) != 2
                or any(type(value) is not int for value in identity["root_identity"])
                or not all(identity[key] for key in ("root", "root_identity", "git_dir", "common_dir"))):
            refuse("incomplete source identity")
        complete = proof["complete_source"]
        tree, index, disk = complete["tree"], complete["index"], complete["disk"]
        if (not (set(FROZEN) | ADDED) <= set(tree) or set(tree) != set(index)
                or set(tree) != set(disk) or len(tree) > MAX_PATHS
                or set(proof["candidate_files"]) != ADDED):
            refuse("incomplete tracked source witness")
        if tree_oid(tree) != identity["tree_oid"]:
            refuse("incomplete authenticated tree witness")
        identities = set()
        total = 0
        for rel, entry in tree.items():
            canonical_path(rel)
            record = disk[rel]
            if (len(entry) != 2 or entry[0] not in {"100644", "100755"}
                    or HEX40.fullmatch(entry[1]) is None
                    or index[rel] != [*entry, "0"] or record["blob_oid"] != entry[1]
                    or re.fullmatch(r"[0-9A-F]{64}", record["sha256"]) is None
                    or type(record["size"]) is not int
                    or not 0 <= record["size"] <= MAX_FILE_BYTES
                    or len(record["identity"]) != 2
                    or any(type(value) is not int for value in record["identity"])):
                refuse("incomplete tracked entry witness")
            total += record["size"]
            key = tuple(record["identity"])
            if key in identities or total > MAX_TOTAL_BYTES:
                refuse("aliased or oversized tracked witness")
            identities.add(key)
        if proof["candidate_files"] != {rel: disk[rel] for rel in sorted(ADDED)}:
            refuse("incomplete candidate byte witness")
        if any(disk[rel]["sha256"] != expected for rel, expected in FROZEN.items()):
            refuse("incomplete frozen byte witness")
        return json.dumps(proof, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")
    except (KeyError, TypeError, ValueError, AttributeError):
        refuse("missing or malformed complete witness")


def compare_witnesses(before: dict, after: dict) -> str:
    first = canonical_witness(before)
    if first != canonical_witness(after):
        refuse("before/after complete source witness mismatch")
    return digest(first)


SUITES = {
    "pure-negative": ("P245PureNegativeTests", "P245CompleteProofTests", "P245SuiteReceiptTests"),
    "live-candidate": ("P245GenuineHostedWindowsCandidateTests",),
}


def expected_tests(classes: tuple[str, ...]) -> int:
    tree = ast.parse(raw_source("tests/test_p245_p76_current_source.py")[0])
    counts = {node.name: sum(isinstance(method, ast.FunctionDef) and method.name.startswith("test_")
                             for method in node.body)
              for node in tree.body if isinstance(node, ast.ClassDef) and node.name in classes}
    if set(counts) != set(classes) or not all(counts.values()):
        refuse("missing suite inventory")
    return sum(counts.values())


def suite_log_complete(raw: bytes, count: int) -> bool:
    summaries = re.findall(rb"^Ran ([0-9]+) tests? in [^\r\n]+\r?$", raw, re.MULTILINE)
    return (summaries == [str(count).encode("ascii")]
            and re.search(rb"\r?\nOK\r?\n?\Z", raw) is not None)


def run_hosted_suite(output: Path) -> int:
    """Bracket unchanged unittest entrypoints with fresh complete live proofs."""
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        refuse("evidence must be outside tracked checkout")
    output.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "P245-BRACKETED-SUITE-V2", "candidate_suite_pass": False,
               "before": {"attempted": False, "complete": False},
               "after": {"attempted": False, "complete": False}, "suites": {},
               "qualified_approvals": "0/7", "full_product_regressions": "0/3",
               "real_key_admission": "NO-GO", "production_release": "HOLD"}

    def save() -> None:
        (output / "suite-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def attempt(label: str) -> dict:
        receipt[label]["attempted"] = True
        save()
        proof = verify_current(branch=BRANCH, head=os.environ.get("GITHUB_SHA", ""))
        canonical = canonical_witness(proof)
        if proof["head"] != os.environ.get("GITHUB_SHA", ""):
            refuse("source witness differs from hosted event")
        (output / (label + "-source.json")).write_bytes(canonical + b"\n")
        receipt[label].update(complete=True, witness_sha256=digest(canonical))
        save()
        return proof

    before = after = None
    save()
    try:
        before = attempt("before")
        for label, classes in SUITES.items():
            count = expected_tests(classes)
            command = [sys.executable, "-B", "-m", "unittest", "-v",
                       *("tests.test_p245_p76_current_source." + name for name in classes)]
            result = {"attempted": True, "complete": False, "native_exit": None,
                      "expected_tests": count}
            receipt["suites"][label] = result
            save()
            log = output / (label + ".log")
            try:
                with log.open("wb") as stream:
                    child = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                           stdout=stream, stderr=subprocess.STDOUT,
                                           timeout=240, check=False, shell=False)
                result["native_exit"] = child.returncode
                with log.open("rb") as stream:
                    raw = stream.read(MAX_GIT_BYTES + 1)
                if len(raw) > MAX_GIT_BYTES:
                    with log.open("rb") as stream:
                        result["log_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest().upper()
                    refuse("oversized native test log")
                result.update(log_sha256=digest(raw),
                              complete=suite_log_complete(raw, count))
            except (OSError, subprocess.TimeoutExpired):
                result["error"] = "native test attempt unavailable or timed out"
                if log.exists():
                    with log.open("rb") as stream:
                        result["log_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest().upper()
            save()
    except (CurrentSourceRefused, OSError, ValueError):
        receipt["before_or_suite_error"] = "source proof or suite orchestration refused"
    finally:
        try:
            after = attempt("after")
        except (CurrentSourceRefused, OSError, ValueError):
            receipt["after_error"] = "fresh final source proof refused"
        save()
    try:
        receipt["complete_witness_sha256"] = compare_witnesses(before, after)
        if (not all(receipt[label]["attempted"] and receipt[label]["complete"]
                    for label in ("before", "after"))
                or set(receipt["suites"]) != set(SUITES)
                or not all(result["complete"] and result["native_exit"] == 0
                           for result in receipt["suites"].values())):
            refuse("missing, incomplete or failed native suite attempt")
        receipt["candidate_suite_pass"] = True
    except CurrentSourceRefused:
        receipt["comparison_error"] = "complete proof equality and native suite success required"
    save()
    return 0 if receipt["candidate_suite_pass"] else 1


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--hosted-suite":
        refuse("expected --hosted-suite and external evidence directory")
    sys.exit(run_hosted_suite(Path(sys.argv[2])))
