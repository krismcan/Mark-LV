"""P240 source-equality-only correction. Additional transport NOT ADMITTED.

Architecture decision precedes code in docs/byok-c1-p240-g1-reconciliation.md.
Do not intercept Git or cache integrity results: old fixture mocks and causal
negative assertions are observable behavior. There is deliberately no G1 mode.
P239 evidence/exits, 180s budget, 20s reads and Job supervision are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import types

PARENT = "d8173c3f3345e17389cc3cb646b320abe3610ef3"
SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
BRANCH = "byok-c1-p240-g1-bounded-immutable-transport-20261115"
ADDITIONS = (
    ".github/workflows/p240-g1-safe-transport.yml",
    "docs/byok-c1-p240-g1-reconciliation.md",
    "scripts/p240_g1_safe_transport.py",
    "scripts/p240_g1_safe_transport_selftest.py",
)
# Exact parent Git blob bytes, never normalized working-tree text.
PINS = {
    "scripts/p239_g1_progress_observer.py":
        "9189fa9def1208039dce1a09c48265973eaf0b0e25d242b91a15ce74ab0c398f",
    "scripts/p238_g1_immutable_batch_candidate.py":
        "9f481c75764415fb4f829b3229d4989daf574b01ea7aa82241747a7cf4ff0eb7",
    "scripts/p234_windows_finegrain_diagnostic.py":
        "e4cdde2bbcd60ba54fd57cebfd335adcb5e13b6d72de1a6fb844574de4c6604c",
}
ORIGINAL = "scripts/p234_windows_finegrain_diagnostic.py"
LIMIT = 4 * 1024 * 1024
WITNESS_KEYS = {"head", "raw_tracked_sha256", "historical_tags", "hook_free_methods"}


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not getattr(info, "st_file_attributes", 0) & 0x400, "NONREGULAR")
    require(info.st_size <= LIMIT, "FILE_CAP")
    with path.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT, "FILE_CAP")
    return raw


def authenticate(path, raw):
    require(path in PINS and sha(raw) == PINS[path], "RAW_SOURCE_PIN")
    return raw


def load_original(root):
    # Authenticate all dependencies before executing only the original verifier.
    raws = {path: authenticate(path, read(root / path)) for path in PINS}
    original = types.ModuleType("p240_pinned_original_p234")
    original.__file__ = str(root / ORIGINAL)
    exec(compile(raws[ORIGINAL], original.__file__, "exec"), original.__dict__)
    require(original.SOURCE == SOURCE and original.SECONDS == 180, "ORIGINAL_CONSTANTS")
    return original


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "DUPLICATE_KEY")
        value[key] = item
    return value


def validate_before(original, raw, expected_sha):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT, "MISSING_OR_OVERSIZED_WITNESS")
    require(type(expected_sha) is str and re.fullmatch(r"[0-9a-f]{64}", expected_sha)
            and sha(raw) == expected_sha, "BEFORE_SHA256")
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(type(value) is dict and set(value) == WITNESS_KEYS
            and value["head"] == SOURCE, "WITNESS_SOURCE_IDENTITY")
    # JSON parsing only rejects noncanonical/tampered input. It NEVER decides
    # equality with the fresh Python witness (which legitimately has tuples).
    require(original.canonical(value) == raw, "NONCANONICAL_WITNESS")


def compare_witness(original, before_raw, expected_sha, fresh_after):
    """Exact original canonical bytes AND independent SHA-256; no stored verdict."""
    validate_before(original, before_raw, expected_sha)
    after_raw = original.canonical(fresh_after)
    require(before_raw == after_raw, "SOURCE_WITNESS_BYTES_CHANGED")
    after_sha = sha(after_raw)
    require(after_sha == expected_sha, "SOURCE_WITNESS_SHA_CHANGED")
    return {"schema": 240, "scope": "SOURCE WITNESS ONLY", "source": SOURCE,
            "canonical_bytes_equal": True, "before_sha256": expected_sha,
            "after_sha256": after_sha, "release": "HOLD",
            "g1_executed": False, "additional_transport_admitted": False}


def revalidate_source(original, source, before_raw, expected_sha):
    # bytes is immutable. Never decode it into a mutable baseline or consult a
    # previous success. Every valid invocation runs the full original verifier.
    validate_before(original, before_raw, expected_sha)
    fresh_after = original.verify_source(source)
    return compare_witness(original, before_raw, expected_sha, fresh_after)


def reconcile_file(original, source, before_path, expected_sha):
    before_raw = read(before_path)
    report = revalidate_source(original, source, before_raw, expected_sha)
    require(read(before_path) == before_raw, "BEFORE_FILE_CHANGED_DURING_REVALIDATION")
    return report  # no positive escapes before the original witness reread


def capture_before(original, source, path):
    raw = original.canonical(original.verify_source(source))
    digest = sha(raw)
    validate_before(original, raw, digest)
    with path.open("xb") as stream:
        require(stream.write(raw) == len(raw), "SHORT_WITNESS_WRITE")
    require(read(path) == raw, "BEFORE_CAPTURE_CHANGED")
    return digest


def environment():
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if (upper.startswith(("GIT_", "P134_", "ACTIONS_", "INPUT_"))
                or any(word in upper for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))
                or upper in {"PYTHONPATH", "PYTHONHOME", "SSH_AUTH_SOCK", "SSH_AGENT_PID"}):
            del env[key]
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], env=environment(),
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=45, check=True).stdout


def check_delta(parents, rows):
    require(parents == [PARENT], "EXACT_PARENT")
    require(sorted(rows) == sorted("A\t" + path for path in ADDITIONS), "EXACT_ADDITIONS")


def provenance(root):
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.getenv("GITHUB_EVENT_NAME") == "push"
            and os.getenv("GITHUB_REF_NAME") == BRANCH, "HOST_IDENTITY")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    require(head == os.getenv("GITHUB_SHA"), "CONTROLLER_HEAD")
    require(git(root, "rev-parse", "--is-shallow-repository") == b"false\n", "FULL_HISTORY")
    require(git(root, "rev-parse", "--show-object-format") == b"sha1\n", "OBJECT_FORMAT")
    require(git(root, "config", "--get", "core.autocrlf").strip() == b"false", "RAW_CHECKOUT")
    require(not git(root, "status", "--porcelain=v1", "-uall", "--ignored=matching"), "DIRTY")
    require(not git(root, "for-each-ref", "refs/replace"), "REPLACE")
    objdir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    require(not (objdir / "info/grafts").exists(), "GRAFT")
    check_delta(git(root, "rev-list", "--parents", "-n", "1", head).decode().split()[1:],
                git(root, "diff-tree", "--no-commit-id", "--name-status", "-r", "--no-renames",
                    PARENT, head).decode().splitlines())
    hashes = []
    for path in ADDITIONS:
        row = git(root, "ls-tree", head, "--", path)
        require(row.startswith(b"100644 blob ") and row.count(b"\n") == 1, "ADDITION_MODE")
        raw = read(root / path)
        require(raw == git(root, "show", head + ":" + path), "CONTROLLER_BYTES")
        hashes.append(sha(raw))
    for path in PINS:
        raw = authenticate(path, read(root / path))
        require(raw == git(root, "show", head + ":" + path), "DEPENDENCY_DISK")
        require(raw == git(root, "show", PARENT + ":" + path), "DEPENDENCY_PARENT")
    return {"schema": 240, "head": head, "parent": PARENT,
            "additions_sha256_in_fixed_order": hashes,
            "dependency_sha256_in_fixed_order": list(PINS.values())}


def run(mode, source, output, before_path=None, expected_sha=None):
    root = Path(__file__).resolve().parents[1]
    report = {"schema": 240, "scope": "SOURCE EQUALITY ONLY", "release": "HOLD",
              "mode": mode, "source": SOURCE, "exit": 125,
              "g1_executed": False, "additional_transport_admitted": False,
              "full_unfiltered_regressions": "0/3"}
    try:
        source = source.resolve(strict=True)
        runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
        output = output.resolve()
        require(output.is_relative_to(runner_temp) and output != runner_temp
                and not output.is_relative_to(root) and not output.is_relative_to(source)
                and not root.is_relative_to(source) and not source.is_relative_to(root), "PATH_SEPARATION")
        output.mkdir(exist_ok=True)
    except Exception:
        print("P240_SOURCE_ONLY_EXIT=125|OUTPUT_SEPARATION_REFUSED|ALL_C1_GATES_HOLD")
        return 125  # cannot safely create a receipt at an unvalidated output path
    try:
        controller = provenance(root)
        original = load_original(root)
        if mode == "guard":
            raw = original.canonical(original.verify_source(source))
            validate_before(original, raw, sha(raw))
            report["source_witness_sha256"] = sha(raw)
        elif mode == "source-check":
            # No test body/child: independent source-only producer and consumer.
            with tempfile.TemporaryDirectory(prefix="p240-private-", dir=runner_temp) as directory:
                private = Path(directory).resolve(strict=True)
                require(not private.is_relative_to(root) and not private.is_relative_to(source),
                        "PRIVATE_SEPARATION")
                before = Path(directory) / "source-before.json"
                digest = capture_before(original, source, before)
                report["witness"] = reconcile_file(original, source, before, digest)
        else:
            require(mode == "reconcile" and before_path is not None
                    and expected_sha is not None, "RECONCILE_INPUT")
            report["witness"] = reconcile_file(original, source, before_path, expected_sha)
        require(provenance(root) == controller, "CONTROLLER_CHANGED")
        report.update(controller=controller, exit=0)
    except Exception:
        # Never publish exceptions, raw JSON, Git argv, tracebacks or user paths.
        report.update(exit=125, error="SOURCE_OR_WITNESS_REFUSED")
        report.pop("witness", None)
    output.mkdir(exist_ok=True)
    (output / (mode + ".json")).write_bytes(
        (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf8"))
    print("P240_SOURCE_ONLY_EXIT=" + str(report["exit"]) + "|ALL_C1_GATES_HOLD")
    return report["exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("guard", "source-check", "reconcile"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--before-sha256")
    args = parser.parse_args()
    return run(args.mode, args.source, args.output, args.before, args.before_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
