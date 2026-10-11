"""Pure, stable, non-secret typed recovery evidence (never a capability).

Digest inputs are canonical document fields, conservative filesystem stamps and
bounded observation identifiers. No secrets, raw candidates or arbitrary repr().
"""
import hashlib
import json

from nayeon.brain.connection_document import (
    ProviderConnectionDocumentV1, provider_connection_document_to_mapping,
)


def canonical_evidence_digest(*, kind: str,
                              before: ProviderConnectionDocumentV1 | None,
                              after: ProviderConnectionDocumentV1 | None,
                              identity: tuple | None,
                              observation: str | None = None) -> str:
    if type(kind) is not str or kind not in {
        "save_metadata", "clear_metadata", "connect", "replace", "remove",
        "review", "test_candidate", "test_stored"
    }:
        raise ValueError("Unknown journal operation")
    if before is not None and type(before) is not ProviderConnectionDocumentV1:
        raise TypeError("Exact before document required")
    if after is not None and type(after) is not ProviderConnectionDocumentV1:
        raise TypeError("Exact after document required")
    if identity is not None and (
        type(identity) is not tuple or len(identity) != 5 or
        any(type(part) is not int or part < 0 for part in identity)
    ):
        raise TypeError("Exact nonsecret file identity required")
    if observation is not None and (
        type(observation) is not str or observation not in {
            "setup_required", "credential_required", "unconfigured_credential_present",
            "validation_required", "unsupported_configuration", "ready", "unknown", "changed_during_observation",
            "configured", "unconfigured", "invalid", "absent", "present"
        }
    ):
        raise ValueError("Unexpected observation identifier")
    payload = {
        "schema": 1, "kind": kind,
        "before": None if before is None else provider_connection_document_to_mapping(before),
        "after": None if after is None else provider_connection_document_to_mapping(after),
        "identity": identity,
        "observation": observation,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                     separators=(",", ":"), allow_nan=False).encode("ascii")
    if len(raw) > 8192:
        raise ValueError("Oversized evidence")
    return hashlib.sha256(raw).hexdigest()
