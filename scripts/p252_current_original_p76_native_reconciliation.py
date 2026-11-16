"""P252 source-preserving Windows diagnostic. Always HOLD; no admission token.

Safety assessment is exact-source scoped, not a general Python sandbox. The
reviewed four methods hit the original P76 branch refusal before fixture replay.
No production module is imported by this runner or its synthetic tests.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

ROOT = Path(r"D:\Nayeon\CODEX_P252_P76_NATIVE_RECONCILIATION_20261116")
HEAD = "6e2717f13da253fddbb3c9cbcfdf55e124d6f8ac"
TREE = "0fb23ea5758c925cda403b231f419ca8f799d0c9"
BRANCH = "byok-c1-p252-original-p76-current-native-reconciliation-20261116"
PYTHON = Path(r"C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe")
EVIDENCE = Path(r"D:\Nayeon\P252_SECURITY_EVIDENCE_20261116")
ADDED = frozenset({
    "scripts/p252_current_original_p76_native_reconciliation.py",
    "tests/test_p252_current_original_p76_native_reconciliation.py",
    "docs/byok-c1-p252-original-p76-current-native-reconciliation.md",
})
IDS = (
    "tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay",
    "tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected",
    "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission",
    "tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route",
)
P76 = "tests/phase8_byok_c1_p76_scope.py"
HISTORICAL_BRANCH = "byok-c1-p80-sealed-historical-fixture-20261106"
MARKER = b"P76 offline source refused: wrong exact P76 prototype branch"
TIMEOUT = 60
# Raw SHA256 pins of the reviewed import/route closure and historical witnesses.
PINS = {
    "tests/__init__.py": "f0d5cf0fe23082c064f7f0175764940e7270697c9f68f766973c2f040314cf95",
    "tests/test_phase8_byok_b_scope_integrity.py": "65dad89298a587d6bb5dde5455df4d701bb1a1fd9a7a96cecf3e647800e3ae8b",
    "tests/test_phase_834_scope_integrity.py": "8dc69ec770ea008dff9cd13e15299a73e38044f1671fd4fe78fbe2a431ccf57a",
    "tests/test_phase_832_scope_integrity.py": "0a25f898ccb374b63b6cd68b0a3488c6f0d8656ec6ea6bae1fd225cabcf9a689",
    "tests/test_phase_833_scope_integrity.py": "8bdeecc1d14ffdcffa2b05b7e3e7409b00e0f211db5810fefb9ec96865a7531d",
    "tests/test_phase_830_scope_integrity.py": "433a34a48af83de3353b2f08ed9ec6b710806e01ec0be096b082abd6272c946f",
    "tests/phase_8_29_lifecycle_scope_migration.py": "bdd9724aff4beb2045d1143acb4e1c3ffd2a0b3c2871b4e3d764c6a456d69c41",
    "tests/phase_8_30_scope_migration.py": "f9aa8c8df0144c83baa4edc8cc8d5f99ce5221c8c1263b13378feaeb87060487",
    "tests/phase_8_31_scope_migration.py": "f1a0772533803b69719ad5af1d8ad1f84946b194259e682cbf809bcff83a5c99",
    "tests/phase_8_32_scope_migration.py": "d658f8442c97225ac9ed1ddef187e25a6d423e6b2eeda3fcd6771fe47e11be02",
    "tests/phase_8_33_scope_migration.py": "9af98a6fd435fea19f30ce00d03fb4f47a23ca64e9278fd9b4e06daaf53872bd",
    "tests/phase_8_34_scope_migration.py": "59442121254b42949640161fb7dbd47e90f3e77e6045f258a1da130b640c8d43",
    "tests/phase_8_36_scope_migration.py": "d63b58a03a00f573c6474a514f4f4e545b4a5ea3c85478fd824e1276862413e6",
    "tests/phase_8_37_scope_migration.py": "3f0ef3592754734e1050e5ce57aef50ce48de4b768019d72f6590ea3f73ddcaa",
    "tests/phase8_byok_scope_migration.py": "7eaa989e141e17c7303ede283b3a979dc77680fa5b74d86a75dc8233ea4324b1",
    "tests/phase8_byok_b_scope_migration.py": "84ced2f31f5daf985de462c384abdfe47f8b705425f8bdefb8cf1e04e56ee010",
    "tests/phase10_perception_scope_migration.py": "6999b151dcf634ed589df6b774b5a84c4252e77f38975f4f87af1a5b56efc9f0",
    "tests/phase10_2_privacy_scope_migration.py": "3d54aa0e57baa5076fa8b6f167e3a906a1ebf7afd87f08e30752cb96b8a1522a",
    "tests/phase10_3_scope_migration.py": "540a1be7c6ff23929b17e8a2f8272083829a65c35a76d1755a5284c958afbeff",
    "tests/phase8_byok_c1_p76_scope.py": "1c42912d9fc550dea56c9ba9bb70d9568f298223b5514af8d03c1723aaad3327",
    "scripts/p234_windows_finegrain_diagnostic.py": "e4cdde2bbcd60ba54fd57cebfd335adcb5e13b6d72de1a6fb844574de4c6604c",
    "scripts/p245_p76_current_source.py": "ad7b400c65db1d2dde1114ea43114d0e5564f1aa489ddbe004916d789885b62f",
    "scripts/p248_p76_properties.py": "8f40efcf6737d566f8e07b4d8f704fc5371d9b341fd0c2ba419018378b782449",
}


class Refused(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path):
    """Reject links/reparse aliases, including ancestors and hardlinked files."""
    for node in (*reversed(path.parents), path):
        info = node.lstat()
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, "st_file_attributes", 0) & 0x400, "linked path")
    require(path.resolve() == path.absolute(), "aliased path")
    return info


def environment(source):
    # Do not print environment values, including when refusing.
    for key in source:
        upper = key.upper()
        require(not upper.startswith(("P134_", "GIT_", "PYTHON")), "unsafe environment")
    allowed = {"SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH",
               "PATHEXT", "SYSTEMDRIVE"}
    env = {k: v for k, v in source.items() if k.upper() in allowed}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
               GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    return env


def git(root, env, *args):
    child = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
         "-c", "core.untrackedCache=false", "-C", str(root), *args],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=30,
        env=env, check=False, shell=False)
    require(child.returncode == 0, "Git read failed")
    require(len(child.stdout) <= 16 * 1024 * 1024, "oversized Git reply")
    return child.stdout


def inventory(raws):
    """AST identity only: never import source merely to enumerate tests."""
    for tid in IDS:
        module, cls, method = tid.rsplit(".", 2)
        path = module.replace(".", "/") + ".py"
        tree = ast.parse(raws[path])
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls]
        require(len(classes) == 1, "missing/duplicate test class")
        methods = [n for n in classes[0].body
                   if isinstance(n, ast.FunctionDef) and n.name == method]
        require(len(methods) == 1 and not methods[0].decorator_list,
                "missing/altered test inventory")
        require(not any(isinstance(n, ast.FunctionDef) and n.name in
                        {"setUp", "tearDown", "setUpClass", "tearDownClass"}
                        for n in classes[0].body), "test lifecycle ambiguity")


def assess(raws, pins=PINS):
    require(bool(pins) and set(raws) == set(pins), "incomplete source closure")
    for path, expected in pins.items():
        require(sha(raws[path]) == expected, "reviewed source drift")
    inventory(raws)
    tree = ast.parse(raws[P76])
    branches = [n.value.value for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "BRANCH" for t in n.targets)
                and isinstance(n.value, ast.Constant)]
    require(branches == [HISTORICAL_BRANCH], "historical branch drift")
    return {p: sha(b) for p, b in raws.items()}


def preflight(root, env):
    require(root == ROOT and Path(__file__).absolute() == root / sorted(ADDED)[1],
            "wrong checkout/runner path")
    checked(root)
    require(git(root, env, "rev-parse", "--show-toplevel").strip().decode().replace("/", "\\").casefold()
            == str(root).casefold(), "wrong Git root")
    head = git(root, env, "rev-parse", "HEAD").strip().decode()
    tree = git(root, env, "rev-parse", "HEAD^{tree}").strip().decode()
    require(bool(re.fullmatch(r"[0-9a-f]{40}", head)) and
            bool(re.fullmatch(r"[0-9a-f]{40}", tree)), "wrong HEAD/tree/branch")
    require(git(root, env, "branch", "--show-current").strip().decode() == BRANCH,
            "wrong HEAD/tree/branch")
    require(git(root, env, "rev-parse", HEAD + "^{tree}").strip().decode() == TREE,
            "wrong parent tree")
    lineage = git(root, env, "rev-list", "--parents", "-n", "1", "HEAD").strip().decode().split()
    require(lineage and lineage[0] == head, "wrong HEAD lineage")
    if head == HEAD:
        require(tree == TREE, "wrong HEAD/tree/branch")
        mode = "original_parent_untracked"
    else:
        require(lineage == [head, HEAD], "wrong HEAD parent")
        delta = git(root, env, "diff-tree", "--no-commit-id", "--name-status",
                    "--no-renames", "-r", "-z", HEAD, head)
        expected = b"".join(b"A\0" + p.encode() + b"\0" for p in sorted(ADDED))
        require(delta == expected, "wrong additive child delta")
        mode = "committed_child"
    require(not git(root, env, "for-each-ref", "refs/replace").strip(), "replacement refs")
    require(git(root, env, "rev-parse", "--is-shallow-repository") == b"false\n", "shallow history")
    for arg in ("--absolute-git-dir", "--git-common-dir"):
        directory = Path(git(root, env, "rev-parse", arg).strip().decode())
        if not directory.is_absolute():
            directory = root / directory
        require(not os.path.lexists(directory / "info/grafts"), "history graft")
    status = git(root, env, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored")
    require(not status or status.endswith(b"\0"), "malformed status")
    rows = status.split(b"\0")[:-1]
    if mode == "committed_child":
        require(status == b"", "dirty/ignored checkout")
    else:
        require(all(row.startswith(b"?? ") and row[3:].decode() in ADDED for row in rows),
                "dirty/ignored checkout")
        require(len(rows) == len(ADDED) and {row[3:].decode() for row in rows} == ADDED,
                "incomplete add-only envelope")
    raw_flags = git(root, env, "ls-files", "-v", "-z")
    require(raw_flags.endswith(b"\0"), "malformed index flags")
    flags = raw_flags.split(b"\0")[:-1]
    require(all(row.startswith(b"H ") for row in flags), "hidden index flags")
    # Parse complete tree/index records; never trust Git's stat cache/attributes.
    def records(raw):
        require(bool(raw) and raw.endswith(b"\0"), "malformed Git inventory")
        return raw.split(b"\0")[:-1]
    tracked = {}
    for row in records(git(root, env, "ls-tree", "-r", "-z", "HEAD")):
        meta, rel = row.split(b"\t")
        mode, kind, oid = meta.split()
        require(mode in (b"100644", b"100755") and kind == b"blob", "unsupported tree path")
        require(re.fullmatch(b"[0-9a-f]{40}", oid) and rel not in tracked,
                "malformed tree identity")
        require(rel and not rel.startswith(b"/") and b"\\" not in rel and b":" not in rel
                and all(p not in (b"", b".", b"..") for p in rel.split(b"/")), "unsafe tree path")
        tracked[rel] = (mode, oid)
        path = root / rel.decode()
        info = checked(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size < 8*1024*1024,
                "unsafe tracked file")
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == oid.decode(), "tracked source drift")
    index = {}
    for row in records(git(root, env, "ls-files", "--stage", "-z")):
        meta, rel = row.split(b"\t")
        filemode, oid, stage = meta.split()
        require(stage == b"0" and rel not in index, "ambiguous index")
        index[rel] = (filemode, oid)
    require(index == tracked, "index/tree closure mismatch")
    require(flags == [b"H " + rel for rel in sorted(tracked)], "index/path closure mismatch")
    additions = {}
    for rel in sorted(ADDED):
        path = root / rel
        info = checked(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size < 8*1024*1024,
                "unsafe added file")
        additions[rel] = sha(path.read_bytes())
    return {"head": head, "tree": tree, "parents": lineage[1:],
            "mode": "original_parent_untracked" if head == HEAD else "committed_child",
            "source_sha256": assess({p: (root / p).read_bytes() for p in PINS}),
            "addition_sha256": additions}


def original_failure(tid, stdout, stderr):
    """Recognize one verbose unittest failure, rejecting extra outcome markers."""
    method = tid.rsplit(".", 1)[1].encode()
    identity = tid.rsplit(".", 1)[0].encode()
    text = stderr.replace(b"\r\n", b"\n")
    title = method + b" (" + identity + b"." + method + b")"
    return (stdout == b"" and
            text.startswith(title + b" ... FAIL\n") and
            re.findall(rb"^FAIL: (.*)$", text, re.M) == [title] and
            len(re.findall(rb"^Ran .*?$", text, re.M)) == 1 and
            len(re.findall(rb"^Ran 1 test in [0-9.]+s$", text, re.M)) == 1 and
            text.endswith(b"FAILED (failures=1)\n") and
            len(re.findall(rb"\bFAIL\b", text)) == 2 and
            len(re.findall(rb"\bFAILED\b", text)) == 1 and
            not re.search(rb"\b(?:ERROR|SKIP|skipped|OK|expected failure|unexpected success)\b", text, re.I) and
            text.count(MARKER) == 1)


def run_one(tid, index, directory, env, run=subprocess.run):
    require(tid in IDS, "unapproved test ID")
    out = directory / f"m{index}.stdout.raw"
    err = directory / f"m{index}.stderr.raw"
    start = time.monotonic()
    code, timed_out = None, False
    with out.open("xb") as stdout, err.open("xb") as stderr:
        try:
            child = run([str(PYTHON), "-B", "-m", "unittest", tid, "-v"],
                        cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                        stdout=stdout, stderr=stderr, timeout=TIMEOUT,
                        shell=False, check=False)
            code = child.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    raw_out, raw_err = out.read_bytes(), err.read_bytes()
    combined = raw_out + raw_err
    complete = original_failure(tid, raw_out, raw_err)
    return {"test_id": tid, "child_exit": code, "timed_out": timed_out,
            "duration_seconds": time.monotonic() - start,
            "stdout_sha256": sha(raw_out), "stderr_sha256": sha(raw_err),
            "stdout_file": out.name, "stderr_file": err.name,
            "failure_markers": {"FAIL": b"FAIL" in combined,
                                "ERROR": b"ERROR" in combined,
                                "original_branch_refusal": MARKER in combined},
            "complete_original_failure": complete and code == 1 and not timed_out,
            "result": "FAIL" if code == 1 and complete and not timed_out else "HOLD"}


def disposition(results):
    # Even four successes would require governance; there is no GO option.
    return "HOLD", 1 if tuple(r["test_id"] for r in results) == IDS and all(
        r["complete_original_failure"] for r in results) else 2


def main():
    require(len(sys.argv) == 1, "no runtime overrides permitted")
    require(os.name == "nt" and sys.version_info[:3] == (3, 12, 10)
            and Path(sys.executable) == PYTHON, "native Python identity")
    env = environment(os.environ)
    source = preflight(ROOT, env)
    checked(EVIDENCE.parent)
    require(not EVIDENCE.is_relative_to(ROOT), "evidence inside checkout")
    EVIDENCE.mkdir(exist_ok=True)
    checked(EVIDENCE)
    directory = EVIDENCE / ("original-" + time.strftime("%Y%m%dT%H%M%S") + "-" + str(os.getpid()))
    directory.mkdir()
    results = []
    for index, tid in enumerate(IDS, 1):
        require(preflight(ROOT, env) == source, "pre-child source drift")
        result = run_one(tid, index, directory, env)
        results.append(result)
        print(json.dumps({k: result[k] for k in
                          ("test_id", "child_exit", "stdout_sha256", "stderr_sha256")}))
    require(preflight(ROOT, env) == source, "post-child source drift")
    status, code = disposition(results)
    receipt = {"status": status, "runner_exit": code, **source,
               "branch": BRANCH, "python": sys.version,
               "runner_sha256": sha(Path(__file__).read_bytes()), "results": results,
               "effects_authorized": False, "original_failures_waived": False}
    write_receipt(directory / "receipt.json", receipt)
    return code


def write_receipt(path, receipt):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Refused, OSError, ValueError, subprocess.SubprocessError):
        print("P252 HOLD: incomplete evidence or preflight refusal", file=sys.stderr)
        sys.exit(2)
