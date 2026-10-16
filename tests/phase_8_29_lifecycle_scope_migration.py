"""Phase 8.29 migration for two exactly pinned historical production files.

The pre-8.29 bytes remain protected by their original immutable Git tags.
Old source-scope tests continue to enforce their exact original allowed delta,
except for this explicitly approved and SHA-256-pinned security repair.
This is NOT permission for other changes to legacy files.
"""
from hashlib import sha256
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVOCABLE_LIFECYCLE = "nayeon/secrets/lifecycle.py"
REVOCABLE_ONBOARDING = "nayeon/brain/credential_onboarding.py"
PROTECTED_HEAD = "240d95f88eea9564db3b65e194085768101ef9e8"
PINNED_BASELINE_SHA256 = {
    REVOCABLE_LIFECYCLE:
        "15db201228093949db3868c126d94e7cc75b22b2c15bf219d001c24bd80f772b",
    REVOCABLE_ONBOARDING:
        "54160b2055de3f119ddcc486fef151b5f0042b0c4e4a17f12a0adb712dcf7d11",
}
PINNED_SHA256 = {
    REVOCABLE_LIFECYCLE:
        "0eeee437a84064c74b9c584c4813ce828a2eeb2a310eeeeff4135df430c8c551",
    REVOCABLE_ONBOARDING:
        "076e5dfbdffacfe99d6c19fe29c7672f691471d60a20f36a7480fece7554404f",
}


def _normalized(source: bytes | str) -> bytes:
    if type(source) is str:
        source = source.encode("utf-8")
    if type(source) is not bytes:
        raise AssertionError("Unexpected historical source representation")
    return source.replace(b"\r\n", b"\n")


def _assert_exact_migration(path: str) -> None:
    if path not in PINNED_SHA256:
        raise AssertionError("Unlisted historical source migration")
    current = _normalized((ROOT / path).read_bytes())
    if sha256(current).hexdigest() != PINNED_SHA256[path]:
        raise AssertionError("Unapproved historical source change")
    # Verify the index unconditionally: an empty cached diff only means
    # index==HEAD, which could be an unauthorized committed snapshot.
    # The one prestaging exception is the exact protected Q4 baseline.
    try:
        index_blob = _normalized(subprocess.check_output(
            ["git", "show", ":" + path], cwd=ROOT,
            stderr=subprocess.DEVNULL,
        ))
        index_hash = sha256(index_blob).hexdigest()
        if index_hash == PINNED_SHA256[path] and index_blob == current:
            return
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            stderr=subprocess.DEVNULL,
        ).decode("ascii").strip()
        if (head == PROTECTED_HEAD and
                index_hash == PINNED_BASELINE_SHA256[path]):
            return
        raise AssertionError("Staged historical source differs from approved repair")
    except (OSError, UnicodeError, subprocess.CalledProcessError):
        raise AssertionError("Unable to verify staged historical source") from None


def migrated_scope(actual: set[str], *, include_onboarding: bool = False) -> set[str]:
    """Allow only exact pinned deltas absent from a specific historical baseline."""
    if type(actual) is not set or any(type(path) is not str for path in actual):
        raise AssertionError("Unexpected legacy source inventory")
    allowed = {REVOCABLE_LIFECYCLE}
    if include_onboarding is True:
        allowed.add(REVOCABLE_ONBOARDING)
    elif include_onboarding is not False:
        raise AssertionError("Exact migration scope flag required")
    present = actual & allowed
    for path in present:
        _assert_exact_migration(path)
    return actual - present


def assert_frozen_or_revocable(testcase, path: str,
                               current: bytes | str, baseline: bytes | str,
                               *original_message: str) -> None:
    """Preserve original source freeze except two exact separately pinned edits."""
    if len(original_message) > 1 or any(type(m) is not str for m in original_message):
        raise AssertionError("Unexpected legacy assertion message arguments")
    message = original_message[0] if original_message else path
    if path in PINNED_SHA256:
        _assert_exact_migration(path)
        testcase.assertEqual(_normalized(current),
                             _normalized((ROOT / path).read_bytes()), message)
    else:
        testcase.assertEqual(_normalized(current), _normalized(baseline), message)
