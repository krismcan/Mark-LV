"""Deterministic post-execution verification coordination; no execution path."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from nayeon.capabilities.structured import StructuredCapabilityRequest
from nayeon.verification.contract import VerificationProvider, VerificationResult


class VerificationService:
    """Isolate observer inputs/results and fail inconclusive without retrying."""

    def verify(
        self, implementation: object, *, request: str | StructuredCapabilityRequest,
        output: Any,
    ) -> VerificationResult:
        try:
            if not isinstance(implementation, VerificationProvider):
                return VerificationResult(reason="No verification provider is available.")
            result = implementation.verify_result(
                request=deepcopy(request), output=deepcopy(output),
            )
            if not isinstance(result, VerificationResult):
                return VerificationResult(reason="The verifier returned an invalid result.")
            # Revalidate and copy even if provider-owned evidence changed after construction.
            return VerificationResult(result.status, result.reason, result.evidence)
        except Exception:
            # Exceptions can contain request data or credentials. Do not echo them.
            return VerificationResult(reason="Verification could not be completed.")
