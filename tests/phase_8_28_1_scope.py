"""Exact new production additions authorised by Phase 8.28.1.

Historical sealed sources and their Git blob hashes remain frozen. This
allowlist is intentionally exact; it does not wildcard changed directories.
"""
APPROVED_RECOVERY_ADDITIONS = frozenset({
    "nayeon/brain/onboarding_recovery.py",
    "nayeon/brain/onboarding_recovery_document.py",
    "nayeon/brain/onboarding_recovery_evidence.py",
    "nayeon/brain/onboarding_recovery_store.py",
    "nayeon/desktop_alpha/first_run_onboarding_recovery_window.py",
})
