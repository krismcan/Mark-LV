"""OM v2.1 auxiliary fail-closed Git-state canary; NOT release authority.

Re-derives actual Git state, exact changed paths and filesystem byte pins and
runs full named unittest modules itself. Manifests remain reviewable input, not
a cryptographic independent attestation or a substitute for full release gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


class PreflightHold(RuntimeError):
    pass


SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
MODULE = re.compile(r"^tests\.test_[a-zA-Z0-9_]+$")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", timeout=45, check=False,
    )
    if completed.returncode != 0:
        raise PreflightHold("Git evidence unavailable")
    return completed.stdout.rstrip("\r\n")


def _names(raw: str) -> set[str]:
    return {name for name in raw.split("\x00") if name}


def _git_raw(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45, check=False,
    )
    if proc.returncode:
        raise PreflightHold("Git byte evidence unavailable")
    return proc.stdout


def _source_path(name: object) -> str:
    if type(name) is not str or "\\" in name or "\x00" in name or ":" in name:
        raise PreflightHold("Invalid expected path")
    p = PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(x in {".", ".."} for x in p.parts):
        raise PreflightHold("Invalid expected path")
    if p.as_posix() != name or name.startswith(".git/"):
        raise PreflightHold("Invalid expected path")
    return name


def _pin_sha(raw: object, length: int) -> str:
    pattern = SHA if length == 40 else DIGEST
    if type(raw) is not str or not pattern.fullmatch(raw):
        raise PreflightHold("Invalid hash pin")
    return raw


def verify(repo: Path, manifest: dict, state: str) -> tuple[list[str], list[str]]:
    if type(manifest) is not dict or set(manifest) != {
        "schema", "baseline_commit", "baseline_tag", "baseline_tag_object", "paths_sha256", "modules"
    } or type(manifest["schema"]) is not int or manifest["schema"] != 1:
        raise PreflightHold("Invalid census schema")
    baseline = _pin_sha(manifest["baseline_commit"], 40)
    tag = manifest["baseline_tag"]
    if type(tag) is not str or not re.fullmatch(r"nayeon-v1-[a-zA-Z0-9_.-]{1,90}", tag):
        raise PreflightHold("Invalid baseline tag")
    if _git(repo, "rev-parse", f"refs/tags/{tag}") != _pin_sha(manifest["baseline_tag_object"], 40):
        raise PreflightHold("Annotated baseline tag object drift")
    if _git(repo, "cat-file", "-t", f"refs/tags/{tag}") != "tag":
        raise PreflightHold("Baseline must be an annotated tag")
    if _git(repo, "rev-parse", f"refs/tags/{tag}^{{}}") != baseline:
        raise PreflightHold("Baseline tag commit drift")
    rawpins = manifest["paths_sha256"]
    rawmods = manifest["modules"]
    if (type(rawpins) is not dict or not rawpins or type(rawmods) is not list
            or not rawmods or len(rawmods) != len(set(map(str, rawmods)))):
        raise PreflightHold("Empty or ambiguous impact census")
    pins = {_source_path(k): _pin_sha(v, 64) for k, v in rawpins.items()}
    if type(rawmods) is not list or not all(type(m) is str and MODULE.fullmatch(m) for m in rawmods):
        raise PreflightHold("Module must be a full tests.test_* module")
    current = _git(repo, "rev-parse", "HEAD")
    if _git(repo, "branch", "--show-current") == "":
        raise PreflightHold("Detached Git checkout")
    status = _git(repo, "-c", "core.quotePath=false", "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [part for part in status.split("\x00") if part]
    if state in {"complete_unstaged", "exact_staged"}:
        if current != baseline or not entries:
            raise PreflightHold("Wrong predecessor or empty candidate")
        got = set()
        for line in entries:
            if len(line) < 4 or line[2] != " " or line[:2] == "!!":
                raise PreflightHold("Ignored or unparseable status")
            if line[:2] == "??" and state == "complete_unstaged":
                got.add(_source_path(line[3:]))
                continue
            if line[:2] == "??":
                raise PreflightHold("Untracked path in staged candidate")
            x, y = line[0], line[1]
            if state == "complete_unstaged" and (x != " " or y not in "MA"):
                raise PreflightHold("Not exactly unstaged")
            if state == "exact_staged" and (x not in "MA" or y != " "):
                raise PreflightHold("Not exactly staged")
            got.add(_source_path(line[3:]))
    elif state == "exact_child":
        if entries or len(_git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()) != 2:
            raise PreflightHold("Child unclean or non-linear")
        if _git(repo, "rev-parse", "HEAD^") != baseline:
            raise PreflightHold("Child not direct descendant")
        got = _names(_git(repo, "diff", "--name-only", "-z", baseline, "HEAD"))
    else:
        raise PreflightHold("Unknown topology")
    if got != set(pins):
        raise PreflightHold("Changed path census does not match actual Git state")
    ignored = _names(_git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "-z"))
    if any(name.lower().endswith((".py", ".pyw", ".pyc", ".pyd", ".dll", ".so", ".exe")) for name in ignored):
        raise PreflightHold("Ignored source path present")
    for rel, digest in pins.items():
        item = repo / Path(*PurePosixPath(rel).parts)
        if not item.is_file() or item.is_symlink():
            raise PreflightHold("Missing, linked or non-file source")
        if hashlib.sha256(item.read_bytes()).hexdigest() != digest:
            raise PreflightHold("Candidate byte pin mismatch")
        if state in {"exact_staged", "exact_child"}:
            spec = f":{rel}" if state == "exact_staged" else f"HEAD:{rel}"
            if hashlib.sha256(_git_raw(repo, "show", spec)).hexdigest() != digest:
                raise PreflightHold("Index or committed blob differs from reviewed disk bytes")
    return sorted(got), list(rawmods)


def execute(repo: Path, modules: list[str], python: Path, logdir: Path) -> None:
    if not python.is_file() or not logdir.is_dir() or logdir.resolve().is_relative_to(repo.resolve()):
        raise PreflightHold("Python or external evidence directory invalid")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for i, mod in enumerate(modules):
        log = logdir / f"om21_canary_{i:02}_{mod.split('.')[-1]}.log"
        if log.exists():
            raise PreflightHold("Pre-existing native test log destination")
        proc = subprocess.run(
            [str(python), "-B", "-m", "unittest", "-v", mod],
            cwd=repo, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=2400, env=env,
        )
        payload = proc.stdout
        with log.open("xb") as handle:
            handle.write(payload)
        count = re.findall(rb"(?m)^Ran ([1-9][0-9]*) tests? in [0-9.]+s\r?$", payload)
        ok = re.findall(rb"(?m)^OK\r?$", payload)
        if proc.returncode != 0 or len(count) != 1 or len(ok) != 1:
            raise PreflightHold("Native test module red, zero tests, or ambiguous evidence")
        print(f"MODULE_NATIVE_PASS {mod} sha256={hashlib.sha256(payload).hexdigest()}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--state", choices=("complete_unstaged", "exact_staged", "exact_child"), required=True)
    ap.add_argument("--python", type=Path, required=True)
    ap.add_argument("--logdir", type=Path, required=True)
    args = ap.parse_args()
    try:
        repo = args.repo.resolve(strict=True)
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        names, modules = verify(repo, manifest, args.state)
        print(f"TOPOLOGY_MATCH {args.state} {len(names)} changed paths")
        execute(repo, modules, args.python.resolve(strict=True), args.logdir.resolve(strict=True))
        print("OM21_TOPOLOGY_MODULE_CANARY_PASS — NOT A COMPLETE RELEASE GATE")
        return 0
    except (PreflightHold, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"OM21_CANARY_HOLD: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
