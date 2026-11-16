"""P255 effect-free source regression. Every assessment blocks acceptance.

Run with Python -B -m tools.byok_c1_p255_effect_boundary from this checkout.
Reuses P251's fixed raw-byte pins, bounded reader and scoped AST inspection.
OPEN records lexical source exposure, without asserting runtime reachability.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tools import byok_c1_effect_exposure_gate as p251


ROOT = Path(__file__).absolute().parents[1]
INTENDED_ROOT = Path(r"D:\Nayeon\CODEX_P255_SECURITY_BOUNDARY_20261116")
BLOCKED_EXIT = 3

# Route obligations use P251's exact path/scope/call witnesses. A partial
# inventory, even with no recognized mutation, cannot establish exclusivity.
ROUTE_SITES = {
    "direct_python_native_write": ("native_credential_write",),
    "direct_python_native_delete": ("native_credential_delete",),
    "direct_python_backend_put": (
        "adapter_write", "lazy_native_adapter", "native_library_setup",
        "native_library_load", "native_credential_write",
    ),
    "direct_python_backend_delete": (
        "adapter_delete", "lazy_native_adapter", "native_library_setup",
        "native_library_load", "native_credential_delete",
    ),
    "interactive_user_controller": (
        "backend_construction", "save_or_replace", "remove", "adapter_write",
        "adapter_delete", "native_credential_write", "native_credential_delete",
    ),
    "source_child_window": (
        "child_process", "composition", "approval_dispatch",
        "backend_construction", "save_or_replace", "remove", "adapter_write",
        "adapter_delete", "native_credential_write", "native_credential_delete",
    ),
}
LIMITATIONS = (
    "Fixed reviewed source witnesses only. Static inspection is incomplete evidence.",
    "OPEN means lexical sites remain present. Control/data flow and actual execution are unproved.",
    "Missing, changed, indirect or unresolved source remains UNKNOWN/BLOCKED.",
    "A safe lexical fixture or absence of recognized sites grants no PASS or exclusion credit.",
    "No installed artifact, loaded-code closure, OS store isolation or native-effect telemetry is established.",
    "Trusted interpreter/tool imports and a quiescent checkout are prerequisites. Filesystem sampling cannot prevent replacement races.",
)


def assess(root: Path) -> dict:
    """Read the fixed source inventory without importing any product module.

    The explicit root parameter is an internal synthetic-test seam. The CLI
    accepts no root, manifest, approval or admission override.
    """
    observed = p251._assess(root)
    issues = list(observed["issues"])
    sites = {}
    required_kinds = dict.fromkeys(kind for kinds in ROUTE_SITES.values() for kind in kinds)
    for kind in required_kinds:
        definitions = [site for site in p251.CALL_SITES if site[3] == kind]
        matches = [item for item in observed["evidence"] if item["kind"] == kind]
        if len(definitions) != 1 or len(matches) != 1:
            issues.append({"reason": "unresolved_route_site", "site": kind})
            continue
        path, scope, call, _ = definitions[0]
        item = matches[0]
        if (item["path"], item.get("scope"), item.get("call")) != (path, scope, call):
            issues.append({"reason": "unexpected_route_site", "site": kind})
            continue
        sites[kind] = item
    if not observed["sources"] or not all(
        source.get("matches_reviewed_snapshot") is True for source in observed["sources"]
    ):
        issues.append({"reason": "incomplete_reviewed_source_snapshot"})
    if observed["assessment"] != "KNOWN_EFFECT_EXPOSURE" and not issues:
        issues.append({"reason": "unresolved_source_assessment"})
    return _report(observed, sites, issues)


def _report(observed: dict, sites: dict, issues: list) -> dict:
    assessment = "UNKNOWN" if issues else "OPEN"
    return {
        "schema": "byok-c1-p255-v1",
        "status": "BLOCKED",
        "assessment": assessment,
        "effect_owner_exclusivity": "NOT_ESTABLISHED",
        "release_admitted": False,
        "real_key_admitted": False,
        "independently_approved": False,
        "routes": [
            {"route": route, "status": assessment,
             "sites": [sites[kind] for kind in kinds if kind in sites]}
            for route, kinds in ROUTE_SITES.items()
        ],
        "sources": observed.get("sources", []),
        "evidence": observed.get("evidence", []),
        "issues": issues,
        "limitations": [*LIMITATIONS, *p251.LIMITATIONS],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    if os.path.normcase(os.path.abspath(ROOT)) != os.path.normcase(os.path.abspath(INTENDED_ROOT)):
        report = _report({}, {}, [{"reason": "unintended_repository_root"}])
    else:
        report = assess(ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    return BLOCKED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
