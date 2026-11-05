"""Test-owned, independently authored positional oracle; no real image proof.

No imports from the generator/redactor. All expected matrices are authored
here, never derived with the redactor's mask/classification helpers.
Public verification returns only a fixed status. Nothing logs or publishes.
"""
from enum import Enum


class OracleStatus(str, Enum):
    VERIFIED = "synthetic_verified"
    DENIED = "synthetic_denied"


# Independent immutable ground truth, including explicit expected positions.
_TRUTH = {
    "single": ((("SECRET_A",),), (("SENSITIVE",),), (("PRIVATE_MASK",),)),
    "small": (
        (("SAFE_A", "SECRET_A", "SAFE_B"), ("SECRET_B", "SAFE_B", "SECRET_A")),
        (("SAFE", "SENSITIVE", "SAFE"), ("SENSITIVE", "SAFE", "SENSITIVE")),
        (("SAFE_A", "PRIVATE_MASK", "SAFE_B"), ("PRIVATE_MASK", "SAFE_B", "PRIVATE_MASK")),
    ),
    "limit": (
        (("SAFE_A", "SECRET_A", "SAFE_B", "SECRET_B") * 4,) * 16,
        (("SAFE", "SENSITIVE", "SAFE", "SENSITIVE") * 4,) * 16,
        (("SAFE_A", "PRIVATE_MASK", "SAFE_B", "PRIVATE_MASK") * 4,) * 16,
    ),
}


def _rectangle(value):
    # Exact types prevent user-defined iteration/equality/formatting callbacks.
    if type(value) is not tuple or not 1 <= len(value) <= 16:
        return False
    if type(value[0]) is not tuple or not 1 <= len(value[0]) <= 16:
        return False
    width = len(value[0])
    if len(value) * width > 256:
        return False
    return all(type(row) is tuple and len(row) == width
               and all(type(cell) is str for cell in row) for row in value)


def verify_fixture(fixture_id, source, classifications, proposed):
    """Inert harness input only. Never return cells, dimensions or identifiers."""
    if type(fixture_id) is not str or fixture_id not in _TRUTH:
        return OracleStatus.DENIED
    if not all(_rectangle(v) for v in (source, classifications, proposed)):
        return OracleStatus.DENIED
    if any(cell not in {"SAFE_A", "SAFE_B", "SECRET_A", "SECRET_B"}
           for row in source for cell in row):
        return OracleStatus.DENIED
    if any(cell not in {"SAFE", "SENSITIVE"}
           for row in classifications for cell in row):
        return OracleStatus.DENIED
    expected_source, expected_classes, expected_output = _TRUTH[fixture_id]
    # Complete matrix equality binds shape AND every individual position.
    # A safe literal in a sensitive position cannot satisfy this proof.
    if (source != expected_source or classifications != expected_classes
            or proposed != expected_output):
        return OracleStatus.DENIED
    return OracleStatus.VERIFIED
