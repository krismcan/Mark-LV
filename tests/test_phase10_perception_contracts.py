"""Phase 10.1 offline perception evidence: positive, privacy and adversarial tests."""
import ast
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
import unittest

from nayeon.perception.contracts import (
    MAX_CLOCK_MS, MAX_EVIDENCE_AGE_MS, MAX_FRAME_DIMENSION,
    AssessmentCode, ObservationAssessment, ObservationCandidate,
    ObservationPurpose, ObservationRequest, ObservationSource,
    RedactionClaim, assess_observation,
)


_UNSET = object()


class PerceptionFoundationTests(unittest.TestCase):
    def setUp(self):
        self.request = ObservationRequest(
            "req-001", "session-001", ObservationSource.SCREEN,
            ObservationPurpose.VERIFY_RESULT,
        )
        self.candidate = ObservationCandidate(
            "observation-001", "req-001", "session-001",
            ObservationSource.SCREEN, ObservationPurpose.VERIFY_RESULT,
            10_000, "a" * 64, RedactionClaim.REDACTED, 1920, 1080,
        )

    def assess(self, candidate=_UNSET, request=_UNSET, **kw):
        return assess_observation(
            self.request if request is _UNSET else request,
            self.candidate if candidate is _UNSET else candidate,
            now_ms=kw.pop("now_ms", 10_100), **kw,
        )

    def test_fresh_redacted_metadata_is_candidate_not_success(self):
        result = self.assess()
        self.assertEqual(result.code, AssessmentCode.CANDIDATE)
        self.assertTrue(result.candidate_only)
        self.assertEqual(result.observation_id, "observation-001")
        self.assertFalse(hasattr(result, "authorized"))
        self.assertFalse(hasattr(result, "verified"))
        self.assertFalse(hasattr(result, "execute"))

    def test_source_and_purpose_are_exact_enums(self):
        for value in ("screen", 1, None, True, object()):
            with self.subTest(value=value), self.assertRaises(TypeError):
                replace(self.request, source=value)
        for value in ("verify_result", None, object()):
            with self.subTest(value=value), self.assertRaises(TypeError):
                replace(self.request, purpose=value)
        for field, value in (("source", "screen"), ("purpose", "verify_result"),
                             ("redaction", "redacted")):
            with self.subTest(field=field), self.assertRaises(TypeError):
                replace(self.candidate, **{field: value})

    def test_request_and_observation_ids_reject_unbounded_or_pathlike_values(self):
        for invalid in ("", "a" * 65, "../etc", "a b", "tab\tvalue",
                        "é", "\n", None, 42, True):
            with self.subTest(value=repr(invalid)):
                with self.assertRaises(ValueError):
                    replace(self.request, request_id=invalid)
                with self.assertRaises(ValueError):
                    replace(self.candidate, observation_id=invalid)
        self.assertEqual(replace(self.request, session_id="A_-:2.9").session_id, "A_-:2.9")

    def test_exact_binding_rejects_cross_session_cross_request_source_purpose(self):
        for field, value in (
            ("request_id", "req-002"), ("session_id", "session-002"),
            ("source", ObservationSource.CAMERA),
            ("purpose", ObservationPurpose.DESCRIBE_CONTEXT),
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    self.assess(replace(self.candidate, **{field: value})).code,
                    AssessmentCode.BINDING_MISMATCH)

    def test_request_type_cannot_be_forged(self):
        for value in ({}, None, object()):
            with self.subTest(value=repr(value)), self.assertRaises(TypeError):
                self.assess(request=value)

    def test_candidate_type_cannot_be_forged(self):
        for value in ({}, None, object()):
            with self.subTest(value=repr(value)), self.assertRaises(TypeError):
                self.assess(candidate=value)

    def test_future_clock_is_refused(self):
        self.assertEqual(self.assess(now_ms=9_999).code,
                         AssessmentCode.FUTURE_TIMESTAMP)
        self.assertFalse(self.assess(now_ms=9_999).candidate_only)

    def test_stale_observation_is_refused_at_boundary(self):
        self.assertEqual(self.assess(now_ms=10_000 + MAX_EVIDENCE_AGE_MS).code,
                         AssessmentCode.CANDIDATE)
        result = self.assess(now_ms=10_001 + MAX_EVIDENCE_AGE_MS)
        self.assertEqual(result.code, AssessmentCode.STALE)
        self.assertFalse(result.candidate_only)
        self.assertIsNone(result.observation_id)

    def test_age_limit_cannot_be_bypassed(self):
        for value in (0, -1, MAX_EVIDENCE_AGE_MS + 1, True, False, 1.0, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.assess(max_age_ms=value)
        self.assertEqual(self.assess(now_ms=10_500, max_age_ms=500).code,
                         AssessmentCode.CANDIDATE)
        self.assertEqual(self.assess(now_ms=10_501, max_age_ms=500).code,
                         AssessmentCode.STALE)

    def test_raw_or_unverified_redaction_claim_fails_closed(self):
        for status in (RedactionClaim.UNKNOWN, RedactionClaim.UNREDACTED):
            with self.subTest(status=status):
                result = self.assess(replace(self.candidate, redaction=status))
                self.assertEqual(result.code, AssessmentCode.UNREDACTED)
                self.assertIsNone(result.observation_id)

    def test_mismatch_refuses_even_when_redaction_and_clock_are_wrong(self):
        candidate = replace(self.candidate, request_id="other",
                            redaction=RedactionClaim.UNREDACTED,
                            observed_at_ms=MAX_CLOCK_MS)
        self.assertEqual(self.assess(candidate).code,
                         AssessmentCode.BINDING_MISMATCH)

    def test_no_raw_content_exists_in_the_contract(self):
        names = {f.name for f in fields(ObservationCandidate)}
        self.assertEqual(names, {
            "observation_id", "request_id", "session_id", "source", "purpose",
            "observed_at_ms", "content_sha256", "redaction", "width", "height",
        })
        for forbidden in ("pixels", "image", "audio", "prompt", "ocr", "text",
                          "secret", "credential", "frame", "payload"):
            self.assertNotIn(forbidden, names)

    def test_all_dataclasses_are_immutable(self):
        for instance, attr in ((self.request, "request_id"),
                               (self.candidate, "observation_id"),
                               (self.assess(), "code")):
            with self.subTest(attr=attr), self.assertRaises(FrozenInstanceError):
                setattr(instance, attr, "forged")

    def test_digest_is_exact_lowercase_sha256_not_content(self):
        for invalid in ("", "a" * 63, "a" * 65, "A" * 64, "g" * 64,
                        "f" * 63 + "\n", None, 1, b"a" * 64):
            with self.subTest(value=repr(invalid)), self.assertRaises(ValueError):
                replace(self.candidate, content_sha256=invalid)

    def test_source_specific_dimensions_are_bounded(self):
        camera = replace(self.candidate, source=ObservationSource.CAMERA,
                         width=2048, height=1536)
        request = replace(self.request, source=ObservationSource.CAMERA)
        self.assertEqual(self.assess(camera, request).code, AssessmentCode.CANDIDATE)
        meta = replace(self.candidate, source=ObservationSource.UI_METADATA,
                       width=0, height=0)
        request = replace(self.request, source=ObservationSource.UI_METADATA)
        self.assertEqual(self.assess(meta, request).code, AssessmentCode.CANDIDATE)
        with self.assertRaises(ValueError):
            replace(meta, width=100)
        for x, y in ((0, 100), (100, 0), (-1, 100), (9000, 9000),
                     (MAX_FRAME_DIMENSION + 1, 1), (True, 2), (1.0, 1)):
            with self.subTest(dimensions=(x, y)), self.assertRaises(ValueError):
                replace(self.candidate, width=x, height=y)

    def test_clock_exact_types_and_ranges(self):
        for invalid in (-1, MAX_CLOCK_MS + 1, True, 0.5, "10000", None):
            with self.subTest(value=repr(invalid)):
                with self.assertRaises(ValueError):
                    replace(self.candidate, observed_at_ms=invalid)
                with self.assertRaises(ValueError):
                    self.assess(now_ms=invalid)
        self.assertEqual(self.assess(now_ms=10_000).code, AssessmentCode.CANDIDATE)

    def test_assessment_cannot_promote_a_string_into_a_code(self):
        with self.assertRaises(TypeError):
            ObservationAssessment("candidate", "observation-001")
        with self.assertRaises(ValueError):
            ObservationAssessment(AssessmentCode.CANDIDATE, "x/../y")

    def test_hostile_subclasses_are_not_promoted(self):
        class DerivedRequest(ObservationRequest):
            pass

        class DerivedCandidate(ObservationCandidate):
            pass

        class HostileObject:
            def __eq__(self, other):
                raise RuntimeError("An unexpected equality check ran")

        untrusted_request = DerivedRequest(
            self.request.request_id, self.request.session_id,
            self.request.source, self.request.purpose,
        )
        untrusted_candidate = DerivedCandidate(
            self.candidate.observation_id, self.candidate.request_id,
            self.candidate.session_id, self.candidate.source,
            self.candidate.purpose, self.candidate.observed_at_ms,
            self.candidate.content_sha256, self.candidate.redaction,
            self.candidate.width, self.candidate.height,
        )
        for bad in (untrusted_request, HostileObject()):
            with self.subTest(kind="request", type=type(bad)), self.assertRaises(TypeError):
                self.assess(request=bad)
        for bad in (untrusted_candidate, HostileObject()):
            with self.subTest(kind="candidate", type=type(bad)), self.assertRaises(TypeError):
                self.assess(candidate=bad)

    def test_no_local_capture_or_provider_imports(self):
        root = Path(__file__).resolve().parents[1] / "nayeon" / "perception"
        for filename in ("contracts.py", "__init__.py"):
            source = (root / filename).read_text(encoding="utf-8")
            tree = ast.parse(source)
            allowed = ({"__future__", "dataclasses", "enum", "re"}
                       if filename == "contracts.py" else {"contracts"})
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        with self.subTest(file=filename, imported=alias.name):
                            self.assertIn(alias.name, allowed)
                elif isinstance(node, ast.ImportFrom):
                    with self.subTest(file=filename, imported=node.module):
                        self.assertIn(node.module, allowed)
                        if filename == "__init__.py":
                            self.assertEqual(node.level, 1)
            for forbidden in ("open(", "ImageGrab", "VideoCapture",
                              "subprocess.", "CredentialManager"):
                with self.subTest(file=filename, forbidden=forbidden):
                    self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
