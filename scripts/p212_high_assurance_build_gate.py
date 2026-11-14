"""P212: actual executable high-assurance build entrypoint, permanently DENY.

The P211 package-intake result is an unconditional pre-build block, not a
permission service. This entrypoint refuses ALL product bundle/installer
attempts, even when only review text is in the plan. No PyInstaller, native
service, credential backend, user key, signed release or installer is built.

The only positive artifact operation is fixed non-executable review TEXT on
a disposable test Windows runner. It is not a distribution or release.
Run with --attempt-ha-release to see real nonzero OS exit 41.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys

from nayeon.brain.p211_high_assurance_package_quarantine import (
    P211Refusal, P211PackageRefusalReceipt, review_high_assurance_package_plan,
)

_FIXED_UNSAFE_BUNDLE = (
    "nayeon/secrets/windows_credential.py",
    "nayeon/brain/local_byok_user_scope.py",
    "nayeon/desktop_alpha/local_byok_launch_bridge.py",
    "native_c1_candidate/CustodyService.cs",
)
_REVIEW_NAME = "P212_QUARANTINE_REVIEW_NO_GO.txt"
_REVIEW_PLAN = ("P211_QUARANTINE_README.txt",)
_REVIEW_BODY = (
    "NAYEON_V1_P212_REVIEW_ONLY\n"
    "SOURCE_RISK=PYTHON_WINCRED_LEGACY_PATH_REACHABLE\n"
    "HIGH_ASSURANCE_RELEASE=NO_GO\n"
    "REAL_KEY=NO_GO\n"
    "PRODUCTION=HOLD\n"
    "SIGNED_NATIVE_SERVICE=ABSENT\n"
    "WINDOWS_MACHINE_POLICY=NOT_APPROVED\n"
    "ARTIFACT_CLASS=NONEXECUTABLE_REVIEW_TEXT_ONLY\n"
    "FULL_WINDOWS_PRODUCT_REGRESSIONS=0/3\n"
    "NO_RELEASE_AUTHORITY_GRANTED\n"
)


@dataclass(frozen=True, slots=True)
class P212BuildRefusal:
    reason: P211Refusal
    count: int
    release_eligible: bool = False
    product_bundle_written: bool = False
    installed_service_activated: bool = False
    credential_effect_permitted: bool = False

    def __post_init__(self) -> None:
        if any((self.release_eligible, self.product_bundle_written,
                self.installed_service_activated,
                self.credential_effect_permitted)):
            raise ValueError("P212 cannot issue high-assurance build authority")


def refuse_high_assurance_build(
    source_root: Path, proposed_payload: tuple[str, ...] | list[str],
) -> P212BuildRefusal:
    """MANDATORY candidate production-build entry, no output side effects.

    Every plan returns denial, including any hypothetically safe plan.
    Source substitution/unknown file is NOT a security or isolation success.
    """
    review: P211PackageRefusalReceipt = review_high_assurance_package_plan(
        source_root, proposed_payload
    )
    return P212BuildRefusal(review.reason, review.manifest_entries)


def _can_emit_review_note(out_dir: Path) -> bool:
    if not isinstance(out_dir, Path) or not out_dir.is_absolute():
        return False
    # No creation of arbitrary directory trees or existing-file overwrite.
    # This is local disposable test evidence only, not Win32 opened-handle
    # authority against races / reparse substitution / remote policy.
    try:
        if not out_dir.is_dir() or out_dir.is_symlink():
            return False
        if getattr(out_dir.lstat(), "st_file_attributes", 0) & 0x400:
            return False
        note=out_dir/_REVIEW_NAME
        if note.exists() or note.is_symlink():
            return False
        return True
    except (OSError, ValueError):
        return False


def emit_nonexecutable_review_only(
    source_root: Path, out_dir: Path,
) -> Path | None:
    """Fixed review TEXT only, never a product package or high-assurance GO."""
    verdict=review_high_assurance_package_plan(source_root, _REVIEW_PLAN)
    if (verdict.reason is not P211Refusal.ABSENT_RELEASE_AUTHORITY
        or verdict.source_witness is None
        or not verdict.source_witness.high_assurance_legacy_risk_present
        or not verdict.source_witness.native_c1_service_denial_only
        or not _can_emit_review_note(out_dir)):
        return None
    note=out_dir/_REVIEW_NAME
    try:
        # Exclusive creation: never overwrite another receipt.
        with note.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(_REVIEW_BODY)
        return note
    except (OSError, UnicodeError, ValueError):
        return None


def _ci_review_dir() -> Path | None:
    """Only a disposable hosted Windows *push* can emit the review receipt.

    Environmental checks are additional *test hygiene*, not trusted source
    or signed image provenance and cannot authorise a real package.
    """
    if (sys.platform!="win32"
        or os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("RUNNER_OS")!="Windows"
        or os.environ.get("GITHUB_EVENT_NAME")!="push"
        or os.environ.get("GITHUB_REPOSITORY")!="krismcan/Mark-LV"
        or os.environ.get("GITHUB_REF_NAME")
            !="byok-c1-p212-build-pipeline-denial-integration-20261114"):
        return None
    temp=os.environ.get("RUNNER_TEMP", "")
    if not temp:
        return None
    p=Path(temp)
    if not p.is_absolute():
        return None
    return p/"nayeon-p212-build-preflight"


def main(argv: list[str] | None=None) -> int:
    values=sys.argv[1:] if argv is None else argv
    if type(values) is not list or len(values)!=1:
        print("P212_BUILD=DENIED_INVALID_COMMAND",flush=True)
        return 64

    source=Path(__file__).resolve().parents[1]
    if values[0]=="--attempt-ha-release":
        receipt=refuse_high_assurance_build(source,_FIXED_UNSAFE_BUNDLE)
        print("P212_BUILD=DENIED_"+receipt.reason.value,flush=True)
        print("P212_OUTPUT_PRODUCT_COUNT=0",flush=True)
        print("P212_REAL_KEY=NO_GO|PRODUCTION=HOLD",flush=True)
        return 41

    if values[0]=="--emit-review-only":
        folder=_ci_review_dir()
        if folder is None:
            print("P212_REVIEW=DENIED_ENVIRONMENT",flush=True)
            return 64
        # A parent directory is made by the independently source-checked
        # evidence collector, not by the package-attempt path.
        note=emit_nonexecutable_review_only(source,folder)
        if note is None:
            print("P212_REVIEW=DENIED",flush=True)
            return 42
        print("P212_REVIEW=NONEXECUTABLE_TEXT_CREATED",flush=True)
        print("P212_PRODUCT_PACKAGE=NONE|RELEASE=HOLD",flush=True)
        return 0

    print("P212_BUILD=DENIED_INVALID_COMMAND",flush=True)
    return 64


if __name__=="__main__":
    raise SystemExit(main())
