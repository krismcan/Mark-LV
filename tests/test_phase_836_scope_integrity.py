"""Phase 8.36 current exact-scope security and frozen-history adversaries.

No Git mutations: fake records / candidate bytes are patched in memory.
Live positive checks use the dedicated private candidate checkout.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import unittest
from unittest import mock

from tests import phase_8_36_scope_migration as scope


class Phase836IntegrityTests(unittest.TestCase):

    def test_allowlist_is_exact_no_unknown_or_unspecified_hash(self):
        self.assertEqual(len(scope.ADDED), 8)
        self.assertEqual(len(scope.MODIFIED), 11)
        self.assertEqual(len(scope.ENVELOPE), 19)
        self.assertEqual(set(scope.CANDIDATE_SHA256), scope.ENVELOPE)
        self.assertTrue(scope.ADDED.isdisjoint(scope.MODIFIED))
        self.assertEqual(scope.PROTECTED,
            "b0490cd9e72104a74a32dc5315cbc55bc4034676")
        self.assertEqual(scope.PROTECTED_TREE,
            "7100ad22930b954ab7f07ee382fec5f6afc4a014")
        self.assertEqual(scope.PROTECTED_TAG_OBJECT,
            "b503ce088ee4a787990534ea862be2936fa55767")
        self.assertNotIn("nayeon/desktop_alpha/reply_owner.py", scope.ENVELOPE)
        self.assertNotIn("nayeon/brain/connection_service.py", scope.ENVELOPE)
        for name, value in scope.CANDIDATE_SHA256.items():
            self.assertEqual(len(value), 64, name)
            self.assertNotEqual(value, "0" * 64, name)

    def test_local_unstaged_candidate_requires_exact_original_scope(self):
        self.assertEqual(scope.assert_836_integrity(), "COMPLETE_UNSTAGED")

    def test_historical_tag_cannot_be_replaced(self):
        actual=scope._git
        def tamper(*args):
            if args[:4] == ("show-ref","--verify","--hash","--"):
                return b"1"*40+b"\n"
            return actual(*args)
        with mock.patch.object(scope,"_git",side_effect=tamper):
            with self.assertRaisesRegex(AssertionError,"8.34 annotated seal mismatch"):
                scope.assert_836_integrity()

    def test_any_unpinned_byte_causes_refusal(self):
        path="nayeon/desktop_alpha/offline_request_review.py"
        with mock.patch.dict(scope.CANDIDATE_SHA256,{path:"1"*64}):
            with self.assertRaisesRegex(AssertionError,"Unapproved 8.36 candidate bytes"):
                scope.assert_836_integrity()

    def test_untracked_extra_ignored_is_refused(self):
        actual=scope._others
        def injected(*args):
            value=actual(*args)
            if args == ("--exclude-standard",):
                return value | {"nayeon/desktop_alpha/offline_request_review.py.bak"}
            return value
        with mock.patch.object(scope,"_others",side_effect=injected):
            with self.assertRaisesRegex(AssertionError,"Missing or extra untracked"):
                scope.assert_836_integrity()

    def test_ignored_bytecode_must_never_authorize_importable_code(self):
        # -B only stops bytecode writes; Python may still read existing pyc.
        # Production source and test caches cannot bypass raw SHA256 pins.
        real=scope._others
        for path in (
            "nayeon/desktop_alpha/__pycache__/offline_request_review.cpython-312.pyc",
            "tests/__pycache__/test_phase_836_scope_integrity.cpython-312.pyc",
            "core/__pycache__/llm_client.cpython-312.pyc",
        ):
            def inject(*args):
                existing=real(*args)
                if args == ("--ignored", "--exclude-standard"):
                    return existing | {path}
                return existing
            with self.subTest(path=path), mock.patch.object(
                scope, "_others", side_effect=inject):
                with self.assertRaisesRegex(
                    AssertionError, "Ignored 8.36 executable or source"):
                    scope.assert_836_integrity()

    def test_wrong_branch_refused_before_expensive_seal(self):
        actual=scope._git
        def fake(*args):
            if args == ("branch","--show-current"):
                return b"review-only\n"
            return actual(*args)
        with mock.patch.object(scope,"_git",side_effect=fake):
            with self.assertRaisesRegex(AssertionError,"Wrong 8.36 product branch"):
                scope.assert_836_integrity()

    def test_frozen_historical_disk_tamper_refused(self):
        actual=scope._frozen
        target="nayeon/desktop_alpha/reply_owner.py"
        def stale(path):
            value=actual(path)
            return value+b"tamper" if path==target else value
        with mock.patch.object(scope,"_frozen",side_effect=stale):
            with self.assertRaisesRegex(AssertionError,"Frozen historical worktree"):
                scope.assert_836_integrity()

    def test_aliased_scope_and_bad_raw_status_refused(self):
        base={p:("100644","a"*40) for p in scope.MODIFIED}
        accepted={p:("100644","b"*40) for p in scope.ENVELOPE}
        touched=sorted(scope.ENVELOPE)
        raw=b"".join(
            (f":{base.get(p,('000000','0'*40))[0]} 100644 "
             f"{base.get(p,('000000','0'*40))[1]} {'b'*40} "
             f"{'A' if p in scope.ADDED else 'M'}").encode()+b"\0"+p.encode()+b"\0"
            for p in touched)
        self.assertIsNone(scope._raw_delta(raw,baseline=base,new=accepted))
        with self.assertRaises(AssertionError):
            scope._raw_delta(raw.replace(b" M\0",b" D\0",1),
                baseline=base,new=accepted)
        with self.assertRaises(AssertionError):
            scope._raw_delta(raw.replace(b"nayeon/desktop_alpha/application.py",
                b"NAYEON/desktop_alpha/application.py"),baseline=base,new=accepted)
        with self.assertRaises(AssertionError):
            scope._raw_delta(raw+raw.split(b"\0")[0]+b"\0",baseline=base,new=accepted)

    def test_helper_self_digest_zeros_only_its_own_entry(self):
        head=b'"tests/phase_8_36_scope_migration.py": "'
        other=b'"tests/test_phase_836_scope_integrity.py": "'
        data=head+b"1"*64+b'",\n'+other+b"2"*64+b'",\n'
        expected=head+b"0"*64+b'",\n'+other+b"2"*64+b'",\n'
        self.assertEqual(scope._digest(scope.SELF,data),
            hashlib.sha256(expected).hexdigest())
        self.assertNotEqual(scope._digest(scope.SELF,data),
            scope._digest(scope.SELF,data+b"X"))
        with self.assertRaisesRegex(AssertionError,"Malformed 8.36 self pin"):
            scope._digest(scope.SELF,other+b"1"*64)

    def test_old_834_guard_is_preserved_private_and_public_routes_forward(self):
        from tests import phase_8_34_scope_migration as previous
        self.assertIsNot(previous._assert_834_historical,
                         previous.assert_834_integrity)
        self.assertEqual(previous.assert_834_integrity(),
                         scope.assert_836_integrity())


if __name__ == "__main__":
    unittest.main()
