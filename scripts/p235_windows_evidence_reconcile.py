"""Bounded, offline P234 ZIP consistency reconciliation. Release always HOLD.

No extraction, source imports, test execution, network access or credential use.
Internal receipts establish consistency only. See the P235 review document.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import struct
import sys
import zipfile
import zlib


CONTROLLER = "bc02f95f9dd241c5dace3129e918324e55dd6ee6"
TEST_SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
RUN_ID = "43696205057-1"
P233 = "scripts/p233_windows_unittest_lifetime_recovery.py"
P233_SHA = "4B29DE93CBA11971A00AF00F2C6E62D27B287FF53CBF5B08E905311258301FCB"
RELEASE = "HOLD; independent review pending; full unfiltered regressions 0/3"
TARGETS = {"tests.test_phase8_byok_b_scope_integrity": 19,
           "tests.test_phase_834_scope_integrity": 35}
MAX_ZIP = 32 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_MEMBERS = 64
MAX_RATIO = 200
HEX256 = re.compile(r"[0-9A-F]{64}\Z")
METHOD_ID = re.compile(r"tests(?:\.[A-Za-z_][A-Za-z_0-9]*){3,}\Z")


class EvidenceError(ValueError):
    """Untrusted evidence failed a deterministic consistency check."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf8")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def invalid_constant(value):
    raise EvidenceError("nonfinite JSON value")


def parse_json(raw):
    # Reject nesting before the decoder allocates a recursive object graph.
    depth = 0
    quoted = escaped = False
    for char in raw.decode("utf8"):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            require(depth <= 64, "JSON nesting bound exceeded")
        elif char in "]}":
            depth -= 1
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def regular_file(path):
    attrs = path.lstat()
    require(stat.S_ISREG(attrs.st_mode) and not path.is_symlink()
            and not getattr(attrs, "st_file_attributes", 0) & 0x400,
            "input must be a regular, non-reparse file")


def read_bounded(path, limit):
    regular_file(path)
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "input size bound exceeded")
    return raw


def allowed_members(role):
    names = {"SHA256SUMS.txt", "manifest.json", "driver.json",
             "discovery.json", "discovery.log"}
    if role == "certificate":
        return {"SHA256SUMS.txt", "coverage-certificate.json"}
    if role == "group":
        for index in range(6):
            stem = "single-" + str(index)
            names.update({stem + suffix for suffix in
                          (".json", ".events.jsonl", ".log", "-process.json")})
    return names


def read_artifact(path, role):
    raw = read_bounded(path, MAX_ZIP)
    # Bound central-directory allocation before ZipFile constructs ZipInfo objects.
    # These small P234 archives need neither multi-disk nor ZIP64 containers.
    end = raw.rfind(b"PK\x05\x06", max(0, len(raw) - 65557))
    require(end >= 0 and len(raw) >= end + 22, "missing ZIP end record")
    _, disk, directory_disk, disk_count, count, size, offset, comment = struct.unpack(
        "<4s4H2LH", raw[end:end + 22])
    require(disk == directory_disk == 0 and disk_count == count
            and 0 < count <= MAX_MEMBERS and size <= 64 * 1024
            and offset + size == end and end + 22 + comment == len(raw),
            "ZIP central directory bound or layout mismatch")
    members = {}
    # Read the bounded archive into memory once to avoid inconsistent rereads.
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        require(len(infos) == count, "ZIP member count mismatch")
        require(sum(info.file_size for info in infos) <= MAX_TOTAL,
                "ZIP expanded size bound exceeded")
        seen = set()
        for info in infos:
            name = info.filename
            require(name == info.orig_filename and name in allowed_members(role),
                    "unexpected or unsafe ZIP member")
            require(name.casefold() not in seen, "duplicate ZIP filename")
            seen.add(name.casefold())
            mode = info.external_attr >> 16
            require(stat.S_IFMT(mode) in (0, stat.S_IFREG)
                    and not info.is_dir() and not info.external_attr & 0x10
                    and not info.flag_bits & 1,
                    "nonregular or encrypted ZIP member")
            require(info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                    "unsupported ZIP compression")
            require(0 <= info.file_size <= MAX_MEMBER
                    and info.file_size <= max(1, info.compress_size) * MAX_RATIO,
                    "ZIP member size or compression ratio bound exceeded")
            with archive.open(info) as stream:
                content = stream.read(MAX_MEMBER + 1)
            require(len(content) == info.file_size and len(content) <= MAX_MEMBER,
                    "ZIP member expanded size mismatch")
            members[name] = content  # ZipFile also checks CRC on read.
    require("SHA256SUMS.txt" in members, "missing SHA256SUMS.txt")
    receipts = "".join(sha(members[name]) + "  " + name + "\n"
                       for name in sorted(members) if name != "SHA256SUMS.txt")
    # Windows Path.write_text creates CRLF receipts. P234 read_text normalizes it.
    normalized = members["SHA256SUMS.txt"].decode("ascii").replace("\r\n", "\n")
    require(normalized == receipts,
            "SHA256SUMS inventory or digest mismatch")
    return members, sha(raw)


def integer(value):
    return type(value) is int


def exact(actual, expected, message):
    # Python equality conflates True/1 and False/0. Canonical JSON does not.
    require(canonical(actual) == canonical(expected), message)


def source_path(value):
    require(isinstance(value, str) and len(value) <= 512
            and re.fullmatch(r"[A-Za-z0-9_./-]+", value) is not None
            and all(part not in ("", ".", "..") for part in value.split("/")),
            "unsafe source witness path")


def verify_manifest(raw, run_id):
    manifest = parse_json(raw)
    require(manifest["schema"] == "P234-v1" and manifest["run_id"] == run_id,
            "manifest schema or run identity mismatch")
    source = manifest["source"]
    require(set(source) == {"head", "raw_tracked_sha256", "historical_tags", "hook_free_methods"}
            and source["head"] == TEST_SOURCE, "tested source identity mismatch")
    witnesses = source["raw_tracked_sha256"]
    require(isinstance(witnesses, dict) and 0 < len(witnesses) <= 10000,
            "source witness inventory bound exceeded")
    for path, digest in witnesses.items():
        source_path(path)
        require(isinstance(digest, str) and HEX256.fullmatch(digest), "invalid source SHA256")
    require(witnesses[P233] == P233_SHA, "P233 source witness mismatch")
    tags = source["historical_tags"]
    require(isinstance(tags, dict) and len(tags) == 15, "historical tag inventory mismatch")
    for name, pair in tags.items():
        require(isinstance(name, str) and len(name) <= 200
                and re.fullmatch(r"[A-Za-z0-9_.-]+", name)
                and isinstance(pair, list) and len(pair) == 2
                and all(isinstance(oid, str) and re.fullmatch(r"[0-9a-f]{40}", oid)
                        for oid in pair), "malformed historical tag witness")
    entries = manifest["entries"]
    require(isinstance(entries, list) and len(entries) == 3629, "incomplete discovery")
    ids = []
    expected_entries = []
    hooks = {module: [] for module in TARGETS}
    singles = 0
    for entry in entries:
        tid, module = entry["id"], entry["module"]
        require(isinstance(tid, str) and len(tid) <= 512 and METHOD_ID.fullmatch(tid)
                and isinstance(module, str) and tid.rsplit(".", 2)[0] == module
                and "_FailedTest" not in tid, "invalid discovered method")
        shard = int.from_bytes(hashlib.sha256(module.encode()).digest()[:4], "big") % 6
        expected = {"id": tid, "module": module, "historical_p233_shard": shard}
        if module in TARGETS:
            expected.update(owner="p234_single", group=singles // 6)
            hooks[module].append(tid)
            singles += 1
        else:
            expected["owner"] = "historical_p233_not_executed_by_p234"
        expected_entries.append(expected)
        ids.append(tid)
    require(len(set(ids)) == 3629 and singles == 54, "duplicate or wrong assigned methods")
    require({module: len(tids) for module, tids in hooks.items()} == TARGETS,
            "eligible module counts mismatch")
    exact(source["hook_free_methods"], {module: sorted(tids) for module, tids in hooks.items()},
          "hook audit and discovery mismatch")
    expected = {"schema": "P234-v1", "run_id": run_id, "source": source,
                "inventory_order_sha256": sha(("\n".join(ids) + "\n").encode()),
                "discovered": 3629, "p234_assigned": 54, "p233_assigned_not_run": 3575,
                "group_size": 6, "groups": 9, "entries": expected_entries, "release": RELEASE}
    require(raw == canonical(expected), "manifest bytes, assignment or inventory hash mismatch")
    return manifest


def verify_process(process, files, stem):
    require(set(process) == {"actual_process_exit", "timed_out", "diagnostic_exit",
                             "tree_cleanup", "raw_log", "raw_log_sha256"},
            "process receipt fields mismatch")
    require(integer(process["actual_process_exit"]) and integer(process["diagnostic_exit"])
            and type(process["timed_out"]) is bool, "invalid process exit types")
    require(process["raw_log"] == stem + ".log"
            and process["raw_log_sha256"] == sha(files[stem + ".log"]),
            "raw process log receipt mismatch")
    if process["timed_out"]:
        require(process["diagnostic_exit"] == 124
                and process["tree_cleanup"] in {"UNCERTAIN", "TREE_TERMINATED"},
                "timeout process receipt mismatch")
    else:
        require(process["diagnostic_exit"] == process["actual_process_exit"]
                and process["tree_cleanup"] == "NOT_NEEDED", "process exit or cleanup mismatch")


def verify_discovery(files, driver, manifest):
    process = driver["discovery_process"]
    verify_process(process, files, "discovery")
    require(not process["timed_out"] and process["actual_process_exit"] == 0,
            "original discovery process failed")
    rows = [[e["id"], e["module"], e["historical_p233_shard"]] for e in manifest["entries"]]
    exact(parse_json(files["discovery.json"]), rows, "original discovery receipt differs")


def classify(process, result, events, tid):
    """Reconstruct P234 summary and separately retain finer original outcomes."""
    expected_events = [{"event": event, "id": tid} for event in ("start", "stop")]
    require(any(canonical(events) == canonical(candidate) for candidate in
                ([], expected_events[:1], expected_events)), "impossible or foreign lifecycle journal")
    starts = [tid] if events else []
    stops = [tid] if len(events) == 2 else []
    summary = {"assigned": [tid], "executed": starts, "completed": stops,
               "setup_blocked": [], "original_unittest_exit": None, "status": "INCOMPLETE"}
    if process["timed_out"]:
        # A footer written just before teardown hangs does not turn timeout green.
        summary["status"] = "TIMEOUT"
        return summary, 125 if process["tree_cleanup"] == "UNCERTAIN" else 124, "TIMEOUT"
    if result is None:
        kind = "INTERRUPTED" if starts else "INFRASTRUCTURE_ERROR"
        return summary, 125, kind
    require(set(result) == {"assigned", "tests_run", "original_unittest_exit", "failures",
                            "errors", "skips", "expected_failures", "unexpected_successes"},
            "original result fields mismatch")
    exact(result["assigned"], [tid], "original result assignment mismatch")
    require(integer(result["tests_run"]) and result["tests_run"] == len(starts)
            and integer(result["original_unittest_exit"])
            and result["original_unittest_exit"] in (0, 1), "invalid original result counts or exit")
    holders = {"setUpClass (" + tid.rsplit(".", 1)[0] + ")",
               "setUpModule (" + tid.rsplit(".", 2)[0] + ")"}
    for field in ("failures", "errors", "skips", "expected_failures", "unexpected_successes"):
        values = result[field]
        require(isinstance(values, list) and len(values) <= 64
                and all(isinstance(value, str) and len(value) <= 1024 for value in values),
                "invalid original outcome list")
        # unittest subtest IDs extend the original method ID with parameters.
        require(all(value == tid or value.startswith(tid + " (")
                    or (field in {"errors", "skips"} and value in holders)
                    for value in values), "foreign original outcome ID")
    blocked = not starts and any(value in holders for value in result["errors"] + result["skips"])
    require(stops == starts and (starts == [tid] or blocked), "original method completion mismatch")
    original = result["original_unittest_exit"]
    bad = bool(result["failures"] or result["errors"] or result["unexpected_successes"])
    require(original == int(bad) and process["actual_process_exit"] == original,
            "original outcome and actual exit mismatch")
    summary.update(setup_blocked=[tid] if blocked else [], original_unittest_exit=original,
                   original_result=result)
    summary["status"] = ("SETUP_BLOCKED" if blocked else "FAIL_OR_ERROR" if bad else
                         "SKIP" if result["skips"] else "EXPECTED_FAILURE" if
                         result["expected_failures"] else "PASS")
    if blocked:
        outcome = "SETUP_BLOCKED"
    elif result["failures"] and result["errors"]:
        outcome = "FAILURE_AND_ERROR"
    elif result["failures"]:
        outcome = "FAILURE"
    elif result["errors"]:
        outcome = "ERROR"
    elif result["unexpected_successes"]:
        outcome = "UNEXPECTED_SUCCESS"
    else:
        outcome = summary["status"]
    return summary, 1 if original or blocked else 0, outcome


def verify_group(files, manifest_raw, manifest, group, identity):
    require(files["manifest.json"] == manifest_raw, "cross-group manifest mismatch")
    driver = parse_json(files["driver.json"])
    selected = [e["id"] for e in manifest["entries"] if e.get("group") == group]
    require(driver["run_id"] == manifest["run_id"] and integer(driver["group"])
            and driver["group"] == group and driver["source_identity_sha256"] == identity
            and driver["manifest_sha256"] == sha(manifest_raw) and driver["release"] == RELEASE
            and "error" not in driver, "group identity or driver infrastructure error")
    exact(driver["assigned"], selected, "group assignment mismatch")
    require(isinstance(driver["methods"], list) and len(driver["methods"]) == 6,
            "missing or extra group method receipt")
    verify_discovery(files, driver, manifest)
    code = 0
    outcomes = []
    for index, method in enumerate(driver["methods"]):
        stem = "single-" + str(index)
        process = parse_json(files[stem + "-process.json"])
        verify_process(process, files, stem)
        exact(method["process"], process, "separate process receipt mismatch")
        events = [parse_json(line) for line in files.get(stem + ".events.jsonl", b"").splitlines()]
        result = parse_json(files[stem + ".json"]) if stem + ".json" in files else None
        summary, method_code, outcome = classify(process, result, events, selected[index])
        exact(method, dict(summary, process=process), "method summary and original receipts mismatch")
        outcomes.append({"id": selected[index], "group": group, "index": index,
                         "outcome": outcome, "process": process,
                         "original_unittest_exit": summary["original_unittest_exit"]})
        code = max(code, method_code)
    require(integer(driver["driver_exit"]) and driver["driver_exit"] == code,
            "group driver exit mismatch")
    collection = all(method["status"] not in {"TIMEOUT", "INCOMPLETE"} for method in driver["methods"])
    exact(driver["diagnostic_collection_complete"], collection, "group collection status mismatch")
    for field in ("executed", "completed", "setup_blocked"):
        exact(driver[field], [tid for method in driver["methods"] for tid in method[field]],
              "group lifecycle coverage mismatch")
    return driver["methods"], outcomes, code, collection


def external_digests(raw, actual):
    """Optional filename -> GitHub ZIP digest claims. Malformation is absence."""
    if raw is None:
        metadata = {}
    else:
        try:
            metadata = parse_json(raw)
        except (ValueError, UnicodeError, RecursionError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
    result = {}
    for name, digest in actual.items():
        claim = metadata.get(name)
        if isinstance(claim, str) and re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", claim):
            expected = claim.removeprefix("sha256:").upper()
            result[name] = "MATCH" if expected == digest else "MISMATCH"
        else:
            result[name] = "UNAVAILABLE_OR_MALFORMED"
    return result


def reconcile(directory, run_id=RUN_ID, metadata_raw=None):
    report = {"schema": "P235-v1", "run_id": run_id, "release_gate": "HOLD",
              "release_gate_passed": False, "full_product_regressions": "0/3",
              "controller_commit_expected": CONTROLLER, "tested_source_commit_expected": TEST_SOURCE,
              "full_provenance_approved": False, "independent_evidence_verified": False,
              "evidence_consistent": False, "reconciler_exit": 125,
              "coverage_complete": False, "diagnostic_collection_complete": False,
              "unresolved_holds": ["INDEPENDENT_PROVENANCE_AND_SECURITY_REVIEW_OPEN",
                                   "FULL_PRODUCT_REGRESSIONS_0_OF_3", "P96_REVOCATION_EFFECT_RACE_OPEN",
                                   "SEC_03_OWNERSHIP_OPEN", "SEC_04_BROKER_OPEN"],
              "artifact_zip_sha256": {}, "evidence_errors": []}
    stage = "RUN_ID"
    try:
        require(re.fullmatch(r"[0-9]+-1", run_id) is not None,
                "artifact naming supports attempt 1 only")
        hashes = report["artifact_zip_sha256"]
        name = "p234-plan-1.zip"
        stage = "PLAN"
        plan, hashes[name] = read_artifact(directory / name, "plan")
        manifest_raw = plan["manifest.json"]
        manifest = verify_manifest(manifest_raw, run_id)
        identity = sha(canonical(manifest["source"]))
        driver = parse_json(plan["driver.json"])
        require(driver["run_id"] == run_id and driver["release"] == RELEASE
                and driver["manifest_sha256"] == sha(manifest_raw)
                and driver["source_identity_sha256"] == identity and "error" not in driver,
                "plan identity mismatch or infrastructure error")
        exact([driver["driver_exit"], driver["methods_executed"],
               driver["diagnostic_collection_complete"], driver["status"]],
              [0, 0, True, "INVENTORY_ONLY_NOT_A_TEST_PASS"], "plan result mismatch")
        verify_discovery(plan, driver, manifest)
        methods, outcomes = [], []
        code, collection = 0, True
        for group in range(9):
            stage = "GROUP_" + str(group)
            name = "p234-group-" + str(group) + "-1.zip"
            files, hashes[name] = read_artifact(directory / name, "group")
            group_methods, group_outcomes, group_code, complete = verify_group(
                files, manifest_raw, manifest, group, identity)
            methods.extend(group_methods)
            outcomes.extend(group_outcomes)
            code = max(code, group_code)
            collection = collection and complete
        assigned = [tid for method in methods for tid in method["assigned"]]
        eligible = [e["id"] for e in manifest["entries"] if e["owner"] == "p234_single"]
        exact(assigned, eligible, "aggregate assignment coverage mismatch")
        expected = {"release": RELEASE, "driver_exit": code, "coverage_complete": True,
                    "run_id": run_id, "discovered": 3629, "assigned": assigned,
                    "historical_p233_assigned_not_executed": 3575,
                    "manifest_sha256": sha(manifest_raw), "methods": methods,
                    "diagnostic_collection_complete": collection}
        for field in ("executed", "completed", "setup_blocked"):
            expected[field] = [tid for method in methods for tid in method[field]]
        expected["unexecuted"] = sorted(set(assigned) - set(expected["executed"]))
        expected["uncompleted"] = sorted(set(assigned) - set(expected["completed"]))
        candidates = [directory / name for name in
                      ("p234-certificate-HOLD-1.zip", "p234-certificate-HOLD.zip")
                      if (directory / name).exists()]
        stage = "CERTIFICATE"
        require(len(candidates) == 1, "missing or ambiguous certificate ZIP")
        certificate, hashes[candidates[0].name] = read_artifact(candidates[0], "certificate")
        exact(parse_json(certificate["coverage-certificate.json"]), expected,
              "certificate differs from independently reconstructed exact coverage")
        digest_status = external_digests(metadata_raw, hashes)
        stage = "EXTERNAL_ZIP_DIGESTS"
        report["github_zip_digest_status"] = digest_status
        require("MISMATCH" not in digest_status.values(), "external ZIP digest mismatch")
        report.update(evidence_consistent=True, coverage_complete=True,
                      diagnostic_collection_complete=collection, original_driver_exit=code,
                      manifest_sha256=sha(manifest_raw), source_identity_sha256=identity,
                      discovered=3629, p234_assigned=54, retained_not_executed=3575,
                      original_status_counts=dict(Counter(m["status"] for m in methods)),
                      outcome_counts=dict(Counter(m["outcome"] for m in outcomes)), methods=outcomes,
                      discovery_classification=[dict(entry, p235_execution_classification=(
                          "P234_SINGLE_RECEIPT" if entry["owner"] == "p234_single"
                          else "RETAINED_NOT_EXECUTED")) for entry in manifest["entries"]])
        for field in ("executed", "completed", "setup_blocked", "unexecuted", "uncompleted"):
            report[field] = expected[field]
        if any(item["outcome"] != "PASS" for item in outcomes):
            report["unresolved_holds"].append("ORIGINAL_NON_PASS_RESULTS_UNWAIVED")
        if any(item["outcome"] == "TIMEOUT" for item in outcomes):
            report["unresolved_holds"].append("TIMEOUT_ROOT_CAUSES_OPEN")
        if any(item["process"]["tree_cleanup"] == "UNCERTAIN" for item in outcomes):
            report["unresolved_holds"].append("PROCESS_TREE_CLEANUP_UNCERTAIN")
        # A consistent held diagnostic is still a failing qualified-release gate.
        report["reconciler_exit"] = code or 1
    except (EvidenceError, OSError, ValueError, KeyError, TypeError, AttributeError,
            RecursionError, OverflowError, zipfile.BadZipFile, EOFError, RuntimeError,
            zlib.error, struct.error) as error:
        # Do not echo untrusted paths, log contents or exception text into reports.
        report["evidence_errors"].append("INFRASTRUCTURE_OR_EVIDENCE_ERROR")
        report["evidence_error_stage"] = stage
        if isinstance(error, EvidenceError):
            report["evidence_check_failed"] = str(error)  # Only fixed application messages.
        report["unresolved_holds"].append("EVIDENCE_RECONCILIATION_INCOMPLETE")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="new JSON report path, existing files are refused")
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--github-digests", type=Path,
                        help="optional JSON filename-to-ZIP-digest metadata")
    args = parser.parse_args(argv)
    try:
        metadata = read_bounded(args.github_digests, 64 * 1024) if args.github_digests else None
        report = reconcile(args.artifacts, args.run_id, metadata)
        # Exclusive creation preserves existing evidence and prevents symlink overwrite.
        # The report is data only. Its bytes grant no release or execution authority.
        with args.output.open("xb") as stream:
            stream.write(canonical(report))
        args.output.chmod(stat.S_IREAD)
    except (OSError, EvidenceError):
        print("P235 HOLD. Report input/output unavailable.", file=sys.stderr)
        return 125
    print("P235 HOLD. Reconciler exit " + str(report["reconciler_exit"]))
    return report["reconciler_exit"]


if __name__ == "__main__":
    raise SystemExit(main())
