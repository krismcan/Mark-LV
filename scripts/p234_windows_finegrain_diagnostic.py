"""External P234 controller: 54 unchanged methods, never a release regression.

Run this file OUTSIDE the authentic P233 checkout. No source import occurs in
the parent; children put only the authenticated source first on sys.path.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import traceback
import unittest

SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
P233 = "scripts/p233_windows_unittest_lifetime_recovery.py"
P233_SHA256 = "4B29DE93CBA11971A00AF00F2C6E62D27B287FF53CBF5B08E905311258301FCB"
TARGETS = {"tests.test_phase8_byok_b_scope_integrity": 19,
           "tests.test_phase_834_scope_integrity": 35}
GROUP_SIZE = 6
GROUPS = 9
SECONDS = 180
HOOKS = {"setUp", "tearDown", "setUpClass", "tearDownClass",
         "setUpModule", "tearDownModule", "load_tests"}
RELEASE = "HOLD; independent review pending; full unfiltered regressions 0/3"


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf8")


def write_json(path, value):
    path.write_bytes(canonical(value))


def environment():
    env = os.environ.copy()
    # Never grant P233's ephemeral credential authority to this diagnostic.
    for key in list(env):
        if (key.startswith(("P134_", "GIT_CONFIG_")) or key in {
            "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "PYTHONPATH",
            "PYTHONHOME", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
            "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"}):
            env.pop(key)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          stdin=subprocess.DEVNULL, timeout=45,
                          env=environment()).stdout


def literals(path):
    return {node.targets[0].id: node.value for node in ast.parse(path.read_bytes()).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)}


def historical_tags(root):
    """Read immutable literal tag pins, not current refs as trust anchors."""
    pins = {}
    for path in sorted((root / "tests").glob("*scope_migration.py")):
        values = literals(path)
        for name, node in values.items():
            if name.endswith("_TAG"):
                prefix = name[:-4]
                tag = ast.literal_eval(node)
                obj = ast.literal_eval(values[name + "_OBJECT"])
                commit = ast.literal_eval(values[prefix])
                require(tag not in pins or pins[tag] == (obj, commit), "conflicting tag pins")
                pins[tag] = (obj, commit)
    # Original 8.32 SEALS also bind 8.30/8.31 tag objects. Resolve only the
    # literal references used in this exact authenticated source, never eval.
    old = literals(root / "tests/phase_8_31_scope_migration.py")
    values = literals(root / "tests/phase_8_32_scope_migration.py")
    seals = values["SEALS"]
    for key, value in zip(seals.keys, seals.values):
        obj, commit_node = value.elts
        if isinstance(commit_node, ast.Attribute):
            require(isinstance(commit_node.value, ast.Name)
                    and commit_node.value.id == "old", "unknown seal reference")
            commit_node = old[commit_node.attr]
        elif isinstance(commit_node, ast.Name):
            commit_node = values[commit_node.id]
        pins[ast.literal_eval(key)] = (ast.literal_eval(obj), ast.literal_eval(commit_node))
    require(len(pins) == 15, "historical tag inventory changed")
    for tag, (obj, commit) in sorted(pins.items()):
        require(git(root, "show-ref", "--verify", "--hash", "--", "refs/tags/" + tag)
                .decode().strip() == obj, "missing or forged annotated tag: " + tag)
        require(git(root, "cat-file", "-t", obj) == b"tag\n", "not an annotated tag")
        require(git(root, "rev-parse", "--verify", "--end-of-options", obj + "^{}")
                .decode().strip() == commit, "wrong historical tag peel")
        require(git(root, "cat-file", "-t", commit) == b"commit\n", "missing historical commit")
        git(root, "merge-base", "--is-ancestor", commit, SOURCE)
    return pins


def audit_hooks(root):
    proof = {}
    for module, count in TARGETS.items():
        path = root / (module.replace(".", "/") + ".py")
        tree = ast.parse(path.read_bytes())
        require(not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.name in HOOKS for n in ast.walk(tree)), "lifecycle hook present")
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        require(classes and all(len(n.bases) == 1 and ast.unparse(n.bases[0])
                                == "unittest.TestCase" and not n.decorator_list
                                for n in classes), "nontrivial TestCase lifecycle")
        methods = [module + "." + c.name + "." + n.name for c in classes
                   for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        require(len(methods) == count and len(set(methods)) == count, "target AST count changed")
        proof[module] = sorted(methods)
    return proof


def verify_source(root):
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.getenv("P234_DIAGNOSTICS_ONLY") == "54_UNCHANGED_METHODS", "host guard refused")
    root = root.resolve()
    require(not Path(__file__).resolve().is_relative_to(root), "controller inside tested root")
    require(git(root, "rev-parse", "--show-toplevel").decode().strip().casefold()
            == root.as_posix().casefold(), "wrong source root")
    require(git(root, "rev-parse", "HEAD").decode().strip() == SOURCE, "wrong source HEAD")
    require(git(root, "rev-parse", "--is-shallow-repository") == b"false\n", "shallow history")
    require(git(root, "config", "--get", "core.autocrlf").strip() == b"false", "autocrlf must be false")
    require(not git(root, "status", "--porcelain=v1", "-uall", "--ignored=matching").strip(),
            "dirty, ignored or untracked source")
    require(not git(root, "for-each-ref", "refs/replace").strip(), "replacement Git objects")
    object_dir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    require(not (object_dir / "info/grafts").exists(), "Git graft history")
    witnesses = {}
    for row in git(root, "ls-tree", "-r", "-z", SOURCE).split(b"\0")[:-1]:
        meta, name = row.split(b"\t")
        mode, kind, oid = meta.split()
        rel = name.decode("utf8")
        path = root / rel
        attrs = path.lstat()
        require(mode in (b"100644", b"100755") and kind == b"blob"
                and stat.S_ISREG(attrs.st_mode) and not path.is_symlink()
                and not getattr(attrs, "st_file_attributes", 0) & 0x400, "nonregular source: " + rel)
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == oid.decode(), "raw source bytes differ: " + rel)
        witnesses[rel] = sha(raw)
    require(witnesses[P233] == P233_SHA256, "P233 lifetime recovery hash differs")
    return {"head": SOURCE, "raw_tracked_sha256": witnesses,
            "historical_tags": historical_tags(root), "hook_free_methods": audit_hooks(root)}


def partition(rows, targets=TARGETS, total=3629, group_size=GROUP_SIZE):
    """Rows come only from original P233 unittest discovery, in original order."""
    require(len(rows) == total, "incomplete discovery")
    ids = [r[0] for r in rows]
    require(len(set(ids)) == total, "duplicate discovery IDs")
    counts = {m: 0 for m in targets}
    entries = []
    single = 0
    for tid, module, shard in rows:
        require(isinstance(tid, str) and tid.startswith(module + ".")
                and module.startswith("tests.") and "_FailedTest" not in tid, "invalid discovered ID")
        expected_shard = int.from_bytes(hashlib.sha256(module.encode()).digest()[:4], "big") % 6
        require(shard == expected_shard, "P233 assignment differs")
        entry = {"id": tid, "module": module, "historical_p233_shard": shard}
        if module in targets:
            counts[module] += 1
            entry.update(owner="p234_single", group=single // group_size)
            single += 1
        else:
            entry.update(owner="historical_p233_not_executed_by_p234")
        entries.append(entry)
    require(counts == targets, "wrong eligible module counts")
    return entries


def make_manifest(run_id, rows, source):
    require(re.fullmatch(r"[0-9]+-[0-9]+", run_id) is not None, "invalid stable run ID")
    entries = partition(rows)
    ids = [r[0] for r in rows]
    eligible = [e["id"] for e in entries if e["owner"] == "p234_single"]
    require(set(eligible) == {t for ids in source["hook_free_methods"].values() for t in ids},
            "discovery and lifecycle audit differ")
    return {"schema": "P234-v1", "run_id": run_id, "source": source,
            "inventory_order_sha256": sha(("\n".join(ids) + "\n").encode()),
            "discovered": 3629, "p234_assigned": 54, "p233_assigned_not_run": 3575,
            "group_size": GROUP_SIZE, "groups": GROUPS, "entries": entries, "release": RELEASE}


def run_process(command, cwd, folder, stem, seconds=SECONDS):
    log = folder / (stem + ".log")
    timed_out = False
    tree_cleanup = "NOT_NEEDED"
    with log.open("wb") as sink:
        proc = subprocess.Popen(command, cwd=cwd, env=environment(), stdin=subprocess.DEVNULL,
                                stdout=sink, stderr=subprocess.STDOUT)
        try:
            proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                if sys.platform == "win32":
                    # Only the just-created diagnostic worker and descendants.
                    tree_cleanup = "UNCERTAIN"
                    killed = subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                                            stdout=sink, stderr=subprocess.STDOUT, timeout=30, check=False)
                    if killed.returncode == 0:
                        tree_cleanup = "TREE_TERMINATED"
                else:
                    tree_cleanup = "SYNTHETIC_NONWINDOWS_ROOT_ONLY"
            except (OSError, subprocess.TimeoutExpired):
                tree_cleanup = "UNCERTAIN"
            finally:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=30)
    return {"actual_process_exit": proc.returncode, "timed_out": timed_out,
            "diagnostic_exit": 124 if timed_out else proc.returncode, "tree_cleanup": tree_cleanup,
            "raw_log": log.name, "raw_log_sha256": sha(log.read_bytes())}


class JournalResult(unittest.TextTestResult):
    """Observe stdlib result callbacks; never alter outcomes or test bodies."""
    journal = None

    def event(self, kind, test):
        self.journal.write(json.dumps({"event": kind, "id": test.id()}) + "\n")
        self.journal.flush()

    def startTest(self, test):
        self.event("start", test)
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.event("stop", test)


def classify(process, result, events, tid):
    starts = [e["id"] for e in events if e["event"] == "start"]
    stops = [e["id"] for e in events if e["event"] == "stop"]
    require(all(e["event"] in {"start", "stop"} and e["id"] == tid for e in events),
            "foreign journal event")
    require([e["event"] for e in events] in ([], ["start"], ["start", "stop"]),
            "duplicate or impossible lifecycle events")
    summary = {"assigned": [tid], "executed": starts, "completed": stops,
               "setup_blocked": [], "original_unittest_exit": None, "status": "INCOMPLETE"}
    if process["timed_out"]:
        summary["status"] = "TIMEOUT"
        return summary, 125 if process.get("tree_cleanup") == "UNCERTAIN" else 124
    if result is None:
        return summary, 125
    require(result["assigned"] == [tid] and result["tests_run"] == len(starts), "worker inventory differs")
    original = result["original_unittest_exit"]
    require(original in (0, 1), "invalid original unittest exit")
    summary["original_unittest_exit"] = original
    require(process["actual_process_exit"] == original, "worker exit and original result differ")
    holders = {"setUpClass (" + tid.rsplit(".", 1)[0] + ")",
               "setUpModule (" + tid.rsplit(".", 2)[0] + ")"}
    blocked = not starts and any(x in holders for x in result["errors"] + result["skips"])
    summary["setup_blocked"] = [tid] if blocked else []
    summary["original_result"] = result
    require(stops == starts and (starts == [tid] or blocked), "original method did not complete")
    bad = result["failures"] or result["errors"] or result["unexpected_successes"]
    require(original == (1 if bad else 0), "original outcome and exit disagree")
    summary["status"] = ("SETUP_BLOCKED" if blocked else "FAIL_OR_ERROR" if bad
                         else "SKIP" if result["skips"] else "EXPECTED_FAILURE"
                         if result["expected_failures"] else "PASS")
    return summary, 1 if original or blocked else 0


def child(args):
    require(not args.output.resolve().is_relative_to(args.source.resolve()), "child evidence inside source")
    before = verify_source(args.source)
    sys.path.insert(0, str(args.source.resolve()))
    if args.mode == "inventory":
        p233 = importlib.import_module("scripts.p233_windows_unittest_lifetime_recovery")
        items, digest = p233.discover()  # authentic unchanged discovery; no tests executed
        rows = [[tid, module, shard] for tid, module, shard, test in items]
        del items  # P233: never retain additional TestCase owners
        require(digest == sha(("\n".join(r[0] for r in rows) + "\n").encode()), "inventory digest differs")
        require(verify_source(args.source) == before, "discovery changed source")
        write_json(args.output, rows)
        return 0
    tid = args.test_id
    require(tid in {t for ids in before["hook_free_methods"].values() for t in ids}, "ineligible single")
    module = importlib.import_module(tid.rsplit(".", 2)[0])
    cls = getattr(module, tid.rsplit(".", 2)[1])
    require(cls.__bases__ == (unittest.TestCase,) and not any(h in cls.__dict__ for h in HOOKS)
            and not any(hasattr(module, h) for h in HOOKS), "runtime lifecycle changed")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(tid)
    require(not loader.errors and suite.countTestCases() == 1, "single method load failed")
    # Only stdlib suite owns the case, preserving P233 lifetime recovery.
    with args.output.with_suffix(".events.jsonl").open("w", encoding="utf8") as stream:
        JournalResult.journal = stream
        result = unittest.TextTestRunner(verbosity=2, resultclass=JournalResult).run(suite)
    code = 0 if result.wasSuccessful() else 1
    status = {"assigned": [tid], "tests_run": result.testsRun, "original_unittest_exit": code,
              "failures": [t.id() for t, _ in result.failures],
              "errors": [t.id() for t, _ in result.errors],
              "skips": [t.id() for t, _ in result.skipped],
              "expected_failures": [t.id() for t, _ in result.expectedFailures],
              "unexpected_successes": [t.id() for t in result.unexpectedSuccesses]}
    write_json(args.output, status)
    require(verify_source(args.source) == before, "test changed source")
    return code


def command(args, mode, output, tid=None):
    cmd = [sys.executable, "-B", str(Path(__file__).resolve()), mode,
           "--source", str(args.source.resolve()), "--output", str(output.resolve())]
    return cmd + (["--test-id", tid] if tid else [])


def receipts(folder):
    (folder / "SHA256SUMS.txt").write_text("".join(
        sha(p.read_bytes()) + "  " + p.name + "\n" for p in sorted(folder.iterdir())
        if p.is_file() and p.name != "SHA256SUMS.txt"), encoding="ascii")


def verify_receipts(folder):
    expected = "".join(sha(p.read_bytes()) + "  " + p.name + "\n"
                       for p in sorted(folder.iterdir())
                       if p.is_file() and p.name != "SHA256SUMS.txt")
    require((folder / "SHA256SUMS.txt").read_text("ascii") == expected, "artifact receipts differ")


def aggregate(args):
    """Reconcile downloaded same-run artifacts; absence is an error, never PASS."""
    folder = args.output.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    report = {"release": RELEASE, "driver_exit": 125, "coverage_complete": False}
    try:
        verify_receipts(args.manifest.parent)
        manifest = json.loads(args.manifest.read_bytes())
        require(manifest["run_id"] == args.run_id and manifest["source"]["head"] == SOURCE,
                "wrong aggregate run or source")
        rows = [[e["id"], e["module"], e["historical_p233_shard"]] for e in manifest["entries"]]
        require(canonical(make_manifest(args.run_id, rows, manifest["source"]))
                == args.manifest.read_bytes(), "malformed aggregate manifest")
        plan = json.loads((args.manifest.parent / "driver.json").read_bytes())
        identity = sha(canonical(manifest["source"]))
        require(plan["driver_exit"] == 0 and plan["methods_executed"] == 0
                and plan["source_identity_sha256"] == identity, "plan did not complete")
        methods = []
        code = 0
        collection = True
        for group in range(GROUPS):
            group_folder = args.artifacts / ("p234-group-" + str(group)
                                             + getattr(args, "artifact_suffix", ""))
            verify_receipts(group_folder)
            require((group_folder / "manifest.json").read_bytes() == args.manifest.read_bytes(),
                    "cross-group manifest differs")
            driver = json.loads((group_folder / "driver.json").read_bytes())
            selected = [e["id"] for e in manifest["entries"] if e.get("group") == group]
            require(driver["run_id"] == args.run_id and driver["group"] == group
                    and driver["assigned"] == selected and len(driver["methods"]) == GROUP_SIZE
                    and driver["source_identity_sha256"] == identity,
                    "missing, duplicate or foreign group")
            group_code = 0
            for index, method in enumerate(driver["methods"]):
                output = group_folder / ("single-" + str(index) + ".json")
                journal = output.with_suffix(".events.jsonl")
                events = [json.loads(line) for line in journal.read_text("utf8").splitlines()] if journal.exists() else []
                result = json.loads(output.read_bytes()) if output.exists() else None
                process = method["process"]
                require(process["raw_log"] == "single-" + str(index) + ".log", "foreign raw log path")
                require(sha((group_folder / process["raw_log"]).read_bytes()) == process["raw_log_sha256"],
                        "raw log receipt differs")
                summary, method_code = classify(process, result, events, selected[index])
                require(dict(summary, process=process) == method, "method certificate differs")
                methods.append(method)
                group_code = max(group_code, method_code)
            require(driver["driver_exit"] == group_code, "false green group driver")
            require(driver["diagnostic_collection_complete"] == all(
                m["status"] not in {"TIMEOUT", "INCOMPLETE"} for m in driver["methods"]),
                "false collection status")
            code = max(code, group_code)
            collection = collection and driver["diagnostic_collection_complete"]
        assigned = [tid for m in methods for tid in m["assigned"]]
        eligible = [e["id"] for e in manifest["entries"] if e["owner"] == "p234_single"]
        require(assigned == eligible and len(set(assigned)) == 54, "single coverage is not exact/disjoint")
        report.update(run_id=args.run_id, discovered=3629, assigned=assigned,
                      historical_p233_assigned_not_executed=3575,
                      manifest_sha256=sha(args.manifest.read_bytes()), methods=methods,
                      coverage_complete=True, diagnostic_collection_complete=collection,
                      driver_exit=code)
        for field in ("executed", "completed", "setup_blocked"):
            report[field] = [tid for m in methods for tid in m[field]]
        report["unexecuted"] = sorted(set(assigned) - set(report["executed"]))
        report["uncompleted"] = sorted(set(assigned) - set(report["completed"]))
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        write_json(folder / "coverage-certificate.json", report)
        receipts(folder)
        print(json.dumps({k: report[k] for k in ("driver_exit", "coverage_complete", "release")}))
    return report["driver_exit"]


def parent(args):
    folder = args.output.resolve()
    require(not folder.is_relative_to(args.source.resolve()), "evidence inside source")
    folder.mkdir(parents=True, exist_ok=False)  # stale results must never be reused
    report = {"release": RELEASE, "driver_exit": 125, "diagnostic_collection_complete": False}
    try:
        source = verify_source(args.source)
        report["source_identity_sha256"] = sha(canonical(source))
        inventory = folder / "discovery.json"
        proc = run_process(command(args, "inventory", inventory), args.source, folder, "discovery", 180)
        report["discovery_process"] = proc
        if proc["timed_out"]:
            report["driver_exit"] = 125 if proc["tree_cleanup"] == "UNCERTAIN" else 124
            return report["driver_exit"]
        require(proc["diagnostic_exit"] == 0 and inventory.is_file(), "authentic discovery failed")
        manifest = make_manifest(args.run_id, json.loads(inventory.read_bytes()), source)
        write_json(folder / "manifest.json", manifest)
        report.update(run_id=args.run_id, manifest_sha256=sha(canonical(manifest)))
        if args.mode == "plan":
            report.update(diagnostic_collection_complete=True, driver_exit=0,
                          methods_executed=0, status="INVENTORY_ONLY_NOT_A_TEST_PASS")
        else:
            require(args.group in range(GROUPS), "invalid bounded group")
            require(args.manifest.read_bytes() == canonical(manifest), "manifest or source identity differs")
            require(args.manifest.with_name("SHA256SUMS.txt").is_file(), "missing plan receipts")
            expected_receipt = sha(canonical(manifest)) + "  manifest.json"
            require(expected_receipt in args.manifest.with_name("SHA256SUMS.txt").read_text("ascii").splitlines(),
                    "plan manifest receipt differs")
            selected = [e["id"] for e in manifest["entries"] if e.get("group") == args.group]
            require(len(selected) == GROUP_SIZE, "empty or unbounded group")
            report.update(group=args.group, assigned=selected, methods=[], driver_exit=0)
            for index, tid in enumerate(selected):
                stem = "single-" + str(index)
                output = folder / (stem + ".json")
                proc = run_process(command(args, "single", output, tid), args.source, folder, stem)
                write_json(folder / (stem + "-process.json"), proc)
                event_file = output.with_suffix(".events.jsonl")
                events = [json.loads(line) for line in event_file.read_text("utf8").splitlines()] if event_file.exists() else []
                observed = json.loads(output.read_bytes()) if output.exists() else None
                summary, code = classify(proc, observed, events, tid)
                report["methods"].append(dict(summary, process=proc))
                report["driver_exit"] = max(report["driver_exit"], code)
                write_json(folder / "driver.json", report)  # preserve incremental evidence
            for field in ("executed", "completed", "setup_blocked"):
                report[field] = [tid for m in report["methods"] for tid in m[field]]
            report["diagnostic_collection_complete"] = all(m["status"] not in {"TIMEOUT", "INCOMPLETE"}
                                                          for m in report["methods"])
        require(verify_source(args.source) == source, "source identity changed during group")
    except Exception:
        report.update(driver_exit=125, diagnostic_collection_complete=False, error=traceback.format_exc())
    finally:
        write_json(folder / "driver.json", report)
        receipts(folder)
        print(json.dumps({k: v for k, v in report.items() if k in {
            "driver_exit", "diagnostic_collection_complete", "release", "group", "status"}}, sort_keys=True))
    return report["driver_exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "group", "inventory", "single", "aggregate"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--group", type=int)
    parser.add_argument("--test-id")
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--artifact-suffix", default="")
    args = parser.parse_args()
    if args.mode == "aggregate":
        return aggregate(args)
    if args.source is None:
        parser.error("--source required")
    if args.mode in {"inventory", "single"}:
        try:
            return child(args)
        except Exception:
            traceback.print_exc()
            return 125  # never confuse infrastructure failure with original FAIL
    return parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
