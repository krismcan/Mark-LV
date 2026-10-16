"""Phase 8.30 candidate: real Windows owner checks in disposable synthetic storage only."""
from __future__ import annotations

import ctypes
from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import shutil
import subprocess
import sys
import uuid

from nayeon.config.document import PresentationConfigurationDocumentV1
from nayeon.config.presentation import AssistantPresentationIdentity
from nayeon.desktop_alpha.presentation_profile_owner import (
    ProfileBusy,
    ProfileConflict,
    ProfileStorageError,
    ProfileUnverified,
    TemporaryPresentationProfileOwner,
    _Win32,
)


@unittest.skipUnless(os.name == "nt", "Windows native storage only")
class Phase830TemporaryProfileTests(unittest.TestCase):
    def setUp(self):
        # On this Windows host both the default Temp and Python's mkdtemp
        # inherit a foreign full-control ACE. A normal test parent is therefore
        # correctly refused by the production guard. Construct TWO directories
        # atomically with a private Windows security descriptor instead.
        local_base = Path(os.environ["LOCALAPPDATA"])
        native = _Win32()
        create = ctypes.WinDLL("kernel32", use_last_error=True).CreateDirectoryW
        create.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
        create.restype = ctypes.c_int
        test_parent = local_base / ("nayeon_830_profile_test_" + uuid.uuid4().hex)
        with native.private_security() as security:
            if not create(str(test_parent), ctypes.byref(security)):
                raise RuntimeError("Could not create private disposable test parent")
        self.addCleanup(shutil.rmtree, test_parent)
        self.directory = test_parent / "Presentation"
        with native.private_security() as security:
            if not create(str(self.directory), ctypes.byref(security)):
                raise RuntimeError("Could not create synthetic private directory")
        self.alive = True
        self.owner = TemporaryPresentationProfileOwner(
            self.directory, owner_is_current=lambda: self.alive
        )
        self.profile = self.directory / "presentation.v1.json"
        self.lock = self.directory / "presentation.v1.lock"

    @staticmethod
    def document(name):
        return PresentationConfigurationDocumentV1(
            assistant=AssistantPresentationIdentity(
                display_name=name, wake_name=name
            )
        )

    def test_load_and_review_are_read_only_and_explicit_save_persists(self):
        edit = self.owner.load_for_edit()
        self.assertFalse(edit.snapshot.present)
        self.assertEqual(edit.document.assistant.display_name, "Nayeon")
        self.assertEqual(list(self.directory.iterdir()), [])
        next_doc = self.document("Synthetic Assistant")
        review = self.owner.review_save(edit, next_doc)
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.lock.exists())
        result = self.owner.save(review)
        self.assertEqual(result, next_doc)
        self.assertTrue(self.profile.exists())
        self.assertTrue(self.lock.exists())
        fresh = self.owner.load_for_edit()
        self.assertTrue(fresh.snapshot.present)
        self.assertEqual(fresh.document, next_doc)

    def test_surrogate_draft_refused_before_sidecar_creation(self):
        edit = self.owner.load_for_edit()
        bad = self.document(chr(0xD800))
        with self.assertRaisesRegex(ProfileStorageError, "Invalid presentation draft"):
            self.owner.review_save(edit, bad)
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.lock.exists())

    def test_revoked_human_owner_does_not_create_or_write(self):
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("Synthetic Only"))
        self.alive = False
        with self.assertRaises(ProfileStorageError):
            self.owner.save(review)
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.lock.exists())

    def test_review_replay_is_refused_without_second_write(self):
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("One Time"))
        self.assertEqual(self.owner.save(review).assistant.display_name, "One Time")
        before = self.profile.read_bytes()
        with self.assertRaises(ProfileConflict):
            self.owner.save(review)
        self.assertEqual(self.profile.read_bytes(), before)

    def test_corrupt_existing_document_is_not_overwritten(self):
        original = b'{"unparseable":true'
        self.profile.write_bytes(original)
        # Prove the actual opened ACL is accepted: this refusal must reach
        # the sealed strict JSON parser rather than stopping at ownership.
        native = _Win32()
        handle = native.open(self.profile)
        try:
            native.inspect(handle, self.profile)
            native.security(handle, private=True,
                            admin_created_profile_leaf=True)
        finally:
            native.close(handle)
        with self.assertRaisesRegex(
            ProfileStorageError, "Cannot load trusted presentation profile"
        ):
            self.owner.load_for_edit()
        self.assertEqual(self.profile.read_bytes(), original)
        self.assertFalse(self.lock.exists())

    def test_external_stale_write_fails_without_overwrite(self):
        first = self.owner.load_for_edit()
        stale_review = self.owner.review_save(first, self.document("Stale"))
        replacement = self.document("Other Writer")
        from nayeon.config.persistence import PresentationConfigurationFileStore
        PresentationConfigurationFileStore(self.profile).save(replacement)
        try:
            with self.assertRaises(ProfileConflict):
                self.owner.save(stale_review)
            self.assertEqual(
                PresentationConfigurationFileStore(self.profile).load(), replacement
            )
        except ProfileUnverified:
            self.fail("Conflicting edit never entered the replacement stage")

    def test_invalid_draft_never_writes(self):
        edit = self.owner.load_for_edit()
        with self.assertRaises(TypeError):
            self.owner.review_save(edit, object())
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.lock.exists())

    def test_foreign_read_only_ace_on_profile_is_refused(self):
        # The extra principal gets only READ on disposable synthetic bytes.
        from nayeon.config.persistence import PresentationConfigurationFileStore
        PresentationConfigurationFileStore(self.profile).save(self.document("Synthetic"))
        before = self.profile.read_bytes()
        action = subprocess.run(
            ["icacls", str(self.profile), "/grant", "*S-1-5-32-545:(R)"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(action.returncode, 0, "Owned test ACL setup failed")
        with self.assertRaisesRegex(ProfileStorageError, "Private storage DACL refused"):
            self.owner.load_for_edit()
        self.assertEqual(self.profile.read_bytes(), before)
        self.assertFalse(self.lock.exists())

    def test_administrators_owned_lock_is_refused(self):
        # Strict lock ownership is NOT subject to the profile-leaf exception.
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("Synthetic"))
        native = _Win32()
        descriptor = ctypes.c_void_p()
        sddl = ("O:BAD:P(A;OICI;FA;;;" + native.user_sid
                + ")(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)")
        self.assertTrue(native.sddl(sddl, 1, ctypes.byref(descriptor), None))
        try:
            from nayeon.desktop_alpha.presentation_profile_owner import _SecurityAttributes
            attrs = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
            handle = native.create(str(self.lock), 0xC0000000 | 0x20000, 3,
                                   ctypes.byref(attrs), 1, 0x00200000, None)
            self.assertNotEqual(handle, ctypes.c_void_p(-1).value,
                                "Could not create synthetic group-owned lock")
            native.close(handle)
        finally:
            self.assertFalse(bool(native.local_free(descriptor)))
        with self.assertRaisesRegex(ProfileStorageError, "Storage owner refused"):
            self.owner.save(review)
        self.assertFalse(self.profile.exists())

    def test_administrators_owned_child_directory_is_refused(self):
        native = _Win32()
        descriptor = ctypes.c_void_p()
        sddl = ("O:BAD:P(A;OICI;FA;;;" + native.user_sid
                + ")(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)")
        self.assertTrue(native.sddl(sddl, 1, ctypes.byref(descriptor), None))
        path = self.directory.parent / "GroupOwned"
        try:
            from nayeon.desktop_alpha.presentation_profile_owner import _SecurityAttributes
            attrs = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
            create = ctypes.WinDLL("kernel32", use_last_error=True).CreateDirectoryW
            create.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
            create.restype = ctypes.c_int
            self.assertTrue(create(str(path), ctypes.byref(attrs)),
                            "Could not create synthetic group-owned directory")
        finally:
            self.assertFalse(bool(native.local_free(descriptor)))
        candidate = TemporaryPresentationProfileOwner(
            path, owner_is_current=lambda: True
        )
        with self.assertRaisesRegex(ProfileStorageError, "Storage owner refused"):
            candidate.load_for_edit()
        self.assertEqual(list(path.iterdir()), [])

    def test_unexpected_prewrite_native_error_is_sanitized(self):
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("Synthetic"))
        marker = "SYNTHETIC_DISPOSABLE_PATH_MUST_NOT_ESCAPE"
        with mock.patch(
            "nayeon.desktop_alpha.presentation_profile_owner._Pins.inventory",
            side_effect=OSError(marker),
        ):
            with self.assertRaises(ProfileStorageError) as caught:
                self.owner.save(review)
        self.assertEqual(str(caught.exception), "Presentation profile save refused")
        self.assertNotIn(marker, str(caught.exception))
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.lock.exists())

    def test_descriptor_cleanup_failure_closes_actual_opened_handle(self):
        native = _Win32()
        original_security = native.private_security

        @contextmanager
        def cleanup_failure():
            with original_security() as attributes:
                yield attributes
            raise ProfileUnverified("Synthetic security descriptor cleanup failure")

        with mock.patch.object(native, "private_security", cleanup_failure):
            with mock.patch.object(native, "close", wraps=native.close) as closer:
                with self.assertRaises(ProfileUnverified):
                    native.open(self.lock, lock=True)
                closer.assert_called_once()
        # Reopen through real Win32; the failure must not poison the fixture.
        handle = native.open(self.lock, lock=True)
        native.close(handle)

    def test_hardlinked_profile_is_refused_without_rewriting(self):
        from nayeon.config.persistence import PresentationConfigurationFileStore
        original = self.document("Synthetic")
        PresentationConfigurationFileStore(self.profile).save(original)
        before = self.profile.read_bytes()
        # The second link is inside the same disposable, owned test parent.
        extra_link = self.directory.parent / "SyntheticHardlink"
        os.link(self.profile, extra_link)
        self.assertEqual(extra_link.read_bytes(), before)
        with self.assertRaisesRegex(ProfileStorageError, "Hard-linked profile object refused"):
            self.owner.load_for_edit()
        self.assertEqual(self.profile.read_bytes(), before)
        self.assertFalse(self.lock.exists())

    def test_exclusive_lock_contention_has_no_credential_or_profile_effect(self):
        from nayeon.desktop_alpha.presentation_profile_owner import _Overlapped
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("Synthetic"))
        native = _Win32()
        handle = native.open(self.lock, lock=True)
        overlap = _Overlapped()
        locked = False
        try:
            self.assertTrue(native.lock_file(handle, 3, 0, 1, 0,
                                             ctypes.byref(overlap)))
            locked = True
            with self.assertRaises(ProfileBusy):
                self.owner.save(review)
            self.assertFalse(self.profile.exists())
        finally:
            if locked:
                self.assertTrue(native.unlock_file(handle, 0, 1, 0,
                                                   ctypes.byref(overlap)))
            native.close(handle)
        # Contention consumed the old consent. A fresh review is required.
        new_edit = self.owner.load_for_edit()
        new_review = self.owner.review_save(new_edit, self.document("New Review"))
        self.assertEqual(self.owner.save(new_review).assistant.display_name,
                         "New Review")


    def test_second_process_cannot_acquire_first_process_lock(self):
        # Real separate Windows Python process against a disposable lock.
        from nayeon.desktop_alpha.presentation_profile_owner import _Overlapped
        native = _Win32()
        handle = native.open(self.lock, lock=True)
        overlapped = _Overlapped()
        script = (
            "import ctypes,sys\n"
            "from pathlib import Path\n"
            "from nayeon.desktop_alpha.presentation_profile_owner import _Win32,_Overlapped\n"
            "n=_Win32(); h=n.open(Path(sys.argv[1]),lock=True)\n"
            "o=_Overlapped()\n"
            "ok=bool(n.lock_file(h,3,0,1,0,ctypes.byref(o)))\n"
            "print('ACQUIRED' if ok else 'BUSY')\n"
            "if ok: n.unlock_file(h,0,1,0,ctypes.byref(o))\n"
            "n.close(h)\n"
        )
        def check():
            child = subprocess.run(
                [sys.executable, "-c", script, str(self.lock)],
                capture_output=True, text=True, timeout=12,
                env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            )
            self.assertEqual(child.returncode, 0, child.stderr)
            return child.stdout.strip()
        try:
            self.assertTrue(native.lock_file(handle, 3, 0, 1, 0,
                                             ctypes.byref(overlapped)))
            self.assertEqual(check(), "BUSY")
        finally:
            native.unlock_file(handle, 0, 1, 0, ctypes.byref(overlapped))
            native.close(handle)
        self.assertEqual(check(), "ACQUIRED")

    def test_caught_reentrant_callback_invalidates_outer_save(self):
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("Reentrant"))
        calls = []
        def guarded_callback():
            if not calls:
                calls.append(True)
                try:
                    self.owner.load_for_edit()
                except ProfileBusy:
                    pass
            return True
        self.owner._owner_is_current = guarded_callback
        with self.assertRaises(ProfileStorageError):
            self.owner.save(review)
        self.assertEqual(calls, [True])
        self.assertFalse(self.profile.exists())
        self.assertFalse(self.lock.exists())

    def test_postreplace_error_marks_result_unverified(self):
        from nayeon.config.service import PresentationConfigurationService
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("Interrupted"))
        original = PresentationConfigurationService.replace
        def postreplace_fault(service, document):
            original(service, document)
            raise OSError("SYNTHETIC_PRIVATE_FILE_NAME")
        with mock.patch.object(PresentationConfigurationService, "replace", postreplace_fault):
            with self.assertRaisesRegex(ProfileUnverified, "Storage may have changed; unverified"):
                self.owner.save(review)
        self.assertTrue(self.profile.exists())
        self.assertIsNone(self.owner._review)

    def test_abrupt_second_process_exit_releases_native_lock(self):
        # Child holds a real kernel lock and exits without UnlockFileEx,
        # simulating process interruption on a disposable lock file.
        script = (
            "import ctypes,os,sys\n"
            "from pathlib import Path\n"
            "from nayeon.desktop_alpha.presentation_profile_owner import _Win32,_Overlapped\n"
            "n=_Win32(); h=n.open(Path(sys.argv[1]),lock=True)\n"
            "o=_Overlapped()\n"
            "assert n.lock_file(h,3,0,1,0,ctypes.byref(o))\n"
            "os._exit(77)\n"
        )
        child = subprocess.run(
            [sys.executable, "-c", script, str(self.lock)],
            capture_output=True, text=True, timeout=12,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        )
        self.assertEqual(child.returncode, 77, child.stderr)
        edit = self.owner.load_for_edit()
        review = self.owner.review_save(edit, self.document("After Interruption"))
        self.assertEqual(
            self.owner.save(review).assistant.display_name, "After Interruption"
        )

    def test_source_guard_real_git_untracked_staged_committed_and_tamper(self):
        # Isolated synthetic Git history; this project checkout is not changed.
        import hashlib
        from tests import phase_8_30_scope_migration as scope
        repo = self.directory.parent / "SyntheticGit"
        def restore_test_git_file_attributes():
            import stat
            for temporary_file in repo.rglob("*"):
                if temporary_file.is_file():
                    temporary_file.chmod(stat.S_IREAD | stat.S_IWRITE)
        self.addCleanup(restore_test_git_file_attributes)
        (repo / "nayeon" / "config").mkdir(parents=True)
        frozen = repo / "nayeon" / "config" / "sealed.py"
        frozen.write_bytes(b"frozen_value = 1\n")
        window = repo / "nayeon" / "desktop_alpha" / "window.py"
        window.parent.mkdir(parents=True)
        old_window = b"def main():\n    return 'old'\n"
        approved_window = b"def main():\n    return 'new'\n"
        window.write_bytes(old_window)
        def git(*args):
            proc = subprocess.run(
                ["git", *args], cwd=repo, capture_output=True,
                text=True, timeout=15
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return proc.stdout.strip()
        git("init", "-b", "nayeon-v1")
        git("config", "--local", "user.name", "Synthetic Test")
        git("config", "--local", "user.email", "synthetic@example.invalid")
        git("add", "nayeon/config/sealed.py", "nayeon/desktop_alpha/window.py")
        git("commit", "-m", "Synthetic approved baseline")
        baseline = git("rev-parse", "HEAD")
        new_source = repo / scope.OWNER
        new_source.parent.mkdir(parents=True, exist_ok=True)
        good = b"def synthetic_only():\n    return True\n"
        bad = b"def synthetic_only():\n    return False\n"
        new_source.write_bytes(good)
        new_pins = {scope.OWNER: hashlib.sha256(good).hexdigest()}
        for relative in set(scope.APPROVED_NEW_SHA256) - {scope.OWNER}:
            candidate = repo / relative
            candidate.parent.mkdir(parents=True, exist_ok=True)
            synthetic = ("# disposable " + relative + "\n").encode("utf-8")
            candidate.write_bytes(synthetic)
            new_pins[relative] = hashlib.sha256(synthetic).hexdigest()
        window.write_bytes(approved_window)
        modified_pins = {
            "nayeon/desktop_alpha/window.py":
                hashlib.sha256(approved_window).hexdigest(),
        }
        with (mock.patch.object(scope, "ROOT", repo),
              mock.patch.object(scope, "PROTECTED", baseline),
              mock.patch.object(scope, "APPROVED_NEW_SHA256", new_pins),
              mock.patch.object(scope, "APPROVED_MODIFIED_SHA256", modified_pins),
              mock.patch.object(scope, "APPROVED_SOURCE_SHA256",
                                {**new_pins, **modified_pins}),
              mock.patch.object(scope, "OWNER_SHA256", new_pins[scope.OWNER])):
            scope.assert_830_integrity()  # Exact untracked UI and owner.
            new_source.write_bytes(bad)
            with self.assertRaises(AssertionError):
                scope.assert_830_integrity()
            new_source.write_bytes(good)
            git("add", scope.OWNER)
            scope.assert_830_integrity()  # Exact staged candidate.
            new_source.write_bytes(bad)
            git("add", scope.OWNER)  # Wrong index bytes.
            new_source.write_bytes(good)  # Disk looks approved.
            with self.assertRaises(AssertionError):
                scope.assert_830_integrity()
            git("add", scope.OWNER)
            scope.assert_830_integrity()
            git("add", *sorted(set(new_pins) | set(modified_pins)))
            scope.assert_830_integrity()  # All approved UI staged exactly.
            git("commit", "-m", "Synthetic approved candidate")
            scope.assert_830_integrity()  # Exact committed full UI candidate.
            window.write_bytes(old_window)
            git("add", "nayeon/desktop_alpha/window.py")
            window.write_bytes(approved_window)
            with self.assertRaisesRegex(AssertionError, "Postcommit entrypoint rollback"):
                scope.assert_830_integrity()
            git("add", "nayeon/desktop_alpha/window.py")
            scope.assert_830_integrity()  # Recovered original approved index.
            frozen.write_bytes(b"frozen_value = 2\n")
            with self.assertRaises(AssertionError):
                scope.assert_830_integrity()
            frozen.write_bytes(b"frozen_value = 1\n")
            extra = repo / "nayeon" / "unknown.py"
            extra.write_bytes(b"unexpected = True\n")
            with self.assertRaises(AssertionError):
                scope.assert_830_integrity()
            extra.unlink()
            scope.assert_830_integrity()
            # Unauthorized HEAD with an approved *staged* and disk copy.
            new_source.write_bytes(bad)
            git("add", scope.OWNER)
            git("commit", "-m", "Synthetic malicious committed blob")
            new_source.write_bytes(good)
            git("add", scope.OWNER)
            with self.assertRaises(AssertionError):
                scope.assert_830_integrity()
            git("commit", "-m", "Restore exact synthetic owner")
            scope.assert_830_integrity()
            # A required product file remains on disk, but its index entry
            # is absent: neither staging nor committing this omission is GO.
            missing_ui = "nayeon/desktop_alpha/application.py"
            git("rm", "--cached", missing_ui)
            self.assertTrue((repo / missing_ui).exists())
            with self.assertRaisesRegex(
                    AssertionError, "Missing or unapproved staged 8.30 source"):
                scope.assert_830_integrity()
            git("commit", "-m", "Synthetic incomplete product tree")
            with self.assertRaisesRegex(
                    AssertionError, "Missing or unapproved committed 8.30 source"):
                scope.assert_830_integrity()

@unittest.skipUnless(os.name == "nt", "Windows native storage only")
class Phase830ProductionAdmissionTests(unittest.TestCase):
    """Production factory exercised ONLY with a patched disposable folder."""

    document = staticmethod(Phase830TemporaryProfileTests.document)

    def setUp(self):
        Phase830TemporaryProfileTests.setUp(self)
        from nayeon.desktop_alpha.presentation_profile_owner import (
            create_production_presentation_profile_owner,
        )
        self.synthetic_local = self.directory.parent / "SyntheticLocalAppData"
        native = _Win32()
        create = ctypes.WinDLL("kernel32", use_last_error=True).CreateDirectoryW
        create.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
        create.restype = ctypes.c_int
        with native.private_security() as attrs:
            if not create(str(self.synthetic_local), ctypes.byref(attrs)):
                raise RuntimeError("Disposable known-folder fixture refused")
        self.app_dir = self.synthetic_local / "Nayeon"
        self.profile_dir = self.app_dir / "Presentation"
        self.profile_leaf = self.profile_dir / "presentation.v1.json"
        self.sidecar = self.profile_dir / "presentation.v1.lock"
        patcher = mock.patch(
            "nayeon.desktop_alpha.presentation_profile_owner._resolve_local_app_data",
            return_value=self.synthetic_local,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.production = create_production_presentation_profile_owner(
            owner_is_current=lambda: self.alive
        )

    def _private_directory(self, path):
        native = _Win32()
        create = ctypes.WinDLL("kernel32", use_last_error=True).CreateDirectoryW
        create.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
        create.restype = ctypes.c_int
        with native.private_security() as attrs:
            self.assertTrue(create(str(path), ctypes.byref(attrs)))

    def test_construction_and_missing_load_create_nothing(self):
        self.assertFalse(self.app_dir.exists())
        edit = self.production.load_for_edit()
        self.assertFalse(edit.snapshot.present)
        self.assertEqual(edit.document.assistant.display_name, "Nayeon")
        self.assertFalse(self.app_dir.exists())
        self.production.review_save(edit, self.document("Synthetic Production"))
        self.assertFalse(self.app_dir.exists())

    def test_reviewed_save_creates_only_fixed_private_children(self):
        edit = self.production.load_for_edit()
        review = self.production.review_save(edit, self.document("Synthetic Production"))
        self.assertEqual(self.production.save(review), review.document)
        self.assertEqual(set(self.synthetic_local.iterdir()), {self.app_dir})
        self.assertEqual(set(self.app_dir.iterdir()), {self.profile_dir})
        self.assertEqual(set(self.profile_dir.iterdir()), {self.profile_leaf, self.sidecar})
        native = _Win32()
        for path in (self.app_dir, self.profile_dir):
            handle = native.open(path, directory=True)
            try:
                native.inspect(handle, path, directory=True)
                native.security(handle, private=True, protected=True)
            finally:
                native.close(handle)
        reopened = self.production.load_for_edit()
        self.assertEqual(reopened.document, review.document)

    def test_preexisting_first_private_child_allows_missing_second(self):
        self._private_directory(self.app_dir)
        before = set(self.app_dir.iterdir())
        self.assertFalse(before)
        edit = self.production.load_for_edit()
        self.assertFalse(self.profile_dir.exists())
        review = self.production.review_save(edit, self.document("Test Existing"))
        self.assertEqual(self.production.save(review), review.document)
        self.assertTrue(self.profile_leaf.exists())

    def test_revoked_review_never_creates_children(self):
        edit = self.production.load_for_edit()
        review = self.production.review_save(edit, self.document("Synthetic Production"))
        self.alive = False
        with self.assertRaises(ProfileStorageError):
            self.production.save(review)
        self.assertFalse(self.app_dir.exists())

    def test_existing_foreign_owned_application_child_is_refused(self):
        # Synthetic group-owned child, never any real Nayeon profile.
        from nayeon.desktop_alpha.presentation_profile_owner import _SecurityAttributes
        native = _Win32()
        descriptor = ctypes.c_void_p()
        sddl = ("O:BAD:P(A;OICI;FA;;;" + native.user_sid
                + ")(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)")
        self.assertTrue(native.sddl(sddl, 1, ctypes.byref(descriptor), None))
        try:
            create = ctypes.WinDLL("kernel32", use_last_error=True).CreateDirectoryW
            create.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
            create.restype = ctypes.c_int
            attrs = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
            self.assertTrue(create(str(self.app_dir), ctypes.byref(attrs)))
        finally:
            self.assertFalse(bool(native.local_free(descriptor)))
        with self.assertRaisesRegex(ProfileStorageError, "Storage owner refused"):
            self.production.load_for_edit()
        self.assertFalse(self.profile_dir.exists())

    def test_invalid_existing_profile_inventory_is_refused(self):
        self._private_directory(self.app_dir)
        self._private_directory(self.profile_dir)
        stray = self.profile_dir / "foreign.tmp"
        stray.write_bytes(b"disposable")
        with self.assertRaisesRegex(ProfileStorageError, "Unexpected profile directory entry"):
            self.production.load_for_edit()
        self.assertEqual(stray.read_bytes(), b"disposable")

    def test_missing_known_folder_is_refused_without_creation(self):
        import nayeon.desktop_alpha.presentation_profile_owner as module
        missing = self.directory.parent / "MissingDisposableKnownFolder"
        with mock.patch.object(module, "_resolve_local_app_data", return_value=missing):
            with self.assertRaises(ProfileStorageError):
                self.production.load_for_edit()
        self.assertFalse(missing.exists())

    def test_surrogate_draft_refused_before_fixed_directory_creation(self):
        edit = self.production.load_for_edit()
        bad = self.document(chr(0xD800))
        with self.assertRaisesRegex(ProfileStorageError, "Invalid presentation draft"):
            self.production.review_save(edit, bad)
        self.assertFalse(self.app_dir.exists())

    def test_invalid_draft_and_review_does_not_create_storage(self):
        edit = self.production.load_for_edit()
        with self.assertRaises(TypeError):
            self.production.review_save(edit, object())
        self.assertFalse(self.app_dir.exists())

    def test_absent_to_present_after_edit_is_conflict(self):
        from nayeon.config.persistence import PresentationConfigurationFileStore
        edit = self.production.load_for_edit()
        review = self.production.review_save(edit, self.document("Original Reviewer"))
        self._private_directory(self.app_dir)
        self._private_directory(self.profile_dir)
        existing = self.document("Separate Writer")
        PresentationConfigurationFileStore(self.profile_leaf).save(existing)
        before = self.profile_leaf.read_bytes()
        with self.assertRaises(ProfileConflict):
            self.production.save(review)
        self.assertEqual(self.profile_leaf.read_bytes(), before)
        self.assertEqual(self.production.load_for_edit().document, existing)

    def _synthetic_junction(self, link, target):
        import stat
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(
            getattr(link.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            "Native fixture must be a genuine Windows reparse junction",
        )
        self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)

    def test_native_known_folder_junction_refuses_read_and_reviewed_save(self):
        from nayeon.desktop_alpha.presentation_profile_owner import (
            create_production_presentation_profile_owner,
        )
        # Issue real review against the original trusted known-folder path,
        # then replace that SAME pathname with a native junction. A different
        # resolver path could fail only because the root changed.
        edit = self.production.load_for_edit()
        review = self.production.review_save(
            edit, self.document("Known Folder Junction Synthetic"))
        original = self.directory.parent / "OriginalSyntheticKnownFolder"
        target = self.directory.parent / "ExternalSyntheticKnownFolder"
        self._private_directory(target)
        os.rename(self.synthetic_local, original)
        self.addCleanup(
            lambda: os.rename(original, self.synthetic_local)
            if original.exists() and not os.path.lexists(self.synthetic_local) else None
        )
        self._synthetic_junction(self.synthetic_local, target)
        reader = create_production_presentation_profile_owner(
            owner_is_current=lambda: self.alive
        )
        with self.assertRaises(ProfileStorageError):
            reader.load_for_edit()
        with self.assertRaises(ProfileStorageError):
            self.production.save(review)
        self.assertFalse((target / "Nayeon").exists())
        self.assertFalse((target / "Presentation").exists())
        self.assertFalse((target / "presentation.v1.json").exists())
        self.assertFalse((target / "presentation.v1.lock").exists())

    def test_native_app_junction_refuses_read_and_reviewed_save(self):
        external = self.directory.parent / "JunctionTargetApp"
        self._private_directory(external)
        edit = self.production.load_for_edit()
        self._synthetic_junction(self.app_dir, external)
        from nayeon.desktop_alpha.presentation_profile_owner import (
            create_production_presentation_profile_owner,
        )
        separate_reader = create_production_presentation_profile_owner(
            owner_is_current=lambda: self.alive
        )
        with self.assertRaises(ProfileStorageError):
            separate_reader.load_for_edit()
        review = self.production.review_save(edit, self.document("Synthetic Junction"))
        with self.assertRaises(ProfileStorageError):
            self.production.save(review)
        self.assertFalse((external / "Presentation").exists())
        self.assertFalse(self.sidecar.exists())

    def test_native_profile_child_junction_refuses_read_and_reviewed_save(self):
        self._private_directory(self.app_dir)
        external = self.directory.parent / "JunctionTargetProfile"
        self._private_directory(external)
        edit = self.production.load_for_edit()
        self._synthetic_junction(self.profile_dir, external)
        from nayeon.desktop_alpha.presentation_profile_owner import (
            create_production_presentation_profile_owner,
        )
        separate_reader = create_production_presentation_profile_owner(
            owner_is_current=lambda: self.alive
        )
        with self.assertRaises(ProfileStorageError):
            separate_reader.load_for_edit()
        review = self.production.review_save(edit, self.document("Synthetic Junction"))
        with self.assertRaises(ProfileStorageError):
            self.production.save(review)
        self.assertFalse((external / "presentation.v1.json").exists())
        self.assertFalse((external / "presentation.v1.lock").exists())

    def test_postreplace_native_unlock_failure_is_unverified(self):
        edit = self.production.load_for_edit()
        review = self.production.review_save(edit, self.document("Unlock Synthetic"))
        original_init = _Win32.__init__
        calls = []
        def init_with_failed_unlock(native):
            original_init(native)
            def report_failure(*args):
                calls.append(args)
                return False
            native.unlock_file = report_failure
        with mock.patch.object(_Win32, "__init__", init_with_failed_unlock):
            with self.assertRaises(ProfileUnverified):
                self.production.save(review)
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.profile_leaf.exists())
        # A failed Save itself consumes the one-use receipt; do not use load()
        # first, because a reload would independently invalidate it.
        with self.assertRaises(ProfileConflict):
            self.production.save(review)
        self.assertEqual(self.production.load_for_edit().document, review.document)

    def test_postreplace_native_handle_close_report_is_unverified(self):
        from nayeon.config.service import PresentationConfigurationService
        edit = self.production.load_for_edit()
        review = self.production.review_save(edit, self.document("Close Synthetic"))
        original_replace = PresentationConfigurationService.replace
        original_close = _Win32.close
        state = {"after_replace": False, "injected": False}
        def replacing(service, document):
            result = original_replace(service, document)
            state["after_replace"] = True
            return result
        def close_then_report(native, handle):
            result = original_close(native, handle)
            if state["after_replace"] and not state["injected"]:
                state["injected"] = True
                raise ProfileStorageError("Synthetic handle release report")
            return result
        with (mock.patch.object(PresentationConfigurationService, "replace", replacing),
              mock.patch.object(_Win32, "close", close_then_report)):
            with self.assertRaises(ProfileUnverified):
                self.production.save(review)
        self.assertTrue(state["after_replace"])
        self.assertTrue(state["injected"])
        self.assertTrue(self.profile_leaf.exists())
        # A failed Save itself consumes the one-use receipt; do not use load()
        # first, because a reload would independently invalidate it.
        with self.assertRaises(ProfileConflict):
            self.production.save(review)
        self.assertEqual(self.production.load_for_edit().document, review.document)

    def test_stray_file_after_replacement_never_claims_success(self):
        from nayeon.config.service import PresentationConfigurationService
        edit = self.production.load_for_edit()
        review = self.production.review_save(edit, self.document("Synthetic Check"))
        original = PresentationConfigurationService.replace
        def replaced_with_residue(service, document):
            original(service, document)
            (self.profile_dir / "stray_test.tmp").write_bytes(b"synthetic")
        with mock.patch.object(PresentationConfigurationService, "replace",
                               replaced_with_residue):
            with self.assertRaises(ProfileUnverified):
                self.production.save(review)
        self.assertTrue((self.profile_dir / "stray_test.tmp").exists())
        self.assertTrue(self.profile_leaf.exists())

if __name__ == "__main__":
    unittest.main()
