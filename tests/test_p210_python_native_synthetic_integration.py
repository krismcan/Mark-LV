"""P210 genuine Windows Python -> native C# controlled synthetic integration.

The compiled native executable is TEST-ONLY with C1_SYNTHETIC_TEST.
No real provider, API key, WinCred calls, service, installer or production IPC.
The original P132 direct Python credential path remains source-reachable and
is NOT governed by these tests; that is an explicit unresolved HIGH risk.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest

from nayeon.brain.p206_legacy_effect_hold_candidate import P206LegacyEffectHoldCandidate
from nayeon.secrets.contracts import SecretIdentifier, SecretValue, SecretStorageError

ROOT=Path(__file__).resolve().parents[1]
FIXED="openai.api_key"
EXPECTED={
  "missing-owner":"MISSING_OWNER_REFUSED",
  "forged-review":"FORGED_REVIEW_REFUSED",
  "replay":"REPLAY_RECOVERY_REQUIRED",
  "crash-after-intent":"CRASH_RECOVERY_REQUIRED",
  "uncertain-effect":"UNCERTAIN_RECOVERY_REQUIRED",
  "rollback-valid":"VALID_ROLLBACK_REFUSED",
  "tamper":"TAMPER_REFUSED",
  "revoke":"REVOKED_REFUSED",
  "delete-ack":"DELETE_ACK_REQUIRED",
  "missing-journal":"MISSING_JOURNAL_REFUSED",
}


class P210OriginalPythonNativeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.getenv("P210_NATIVE_EXE", "")
        if sys.platform!="win32" or os.getenv("RUNNER_OS")!="Windows" or not path:
            raise RuntimeError("P210 requires source-custodied Windows native executable")
        cls.executable=Path(path)
        if not cls.executable.is_file() or cls.executable.suffix.lower()!=".exe":
            raise RuntimeError("P210 test-only native compiler output absent")

    def _run(self,*args):
        # This executable is a test fixture, not a native service or secure IPC.
        env={k:v for k,v in os.environ.items()
             if k.upper() in {"RUNNER_TEMP","SYSTEMROOT","WINDIR","TEMP","TMP",
                             "PATH","COMSPEC","USERPROFILE"} and type(v) is str}
        result=subprocess.run([str(self.executable),*args],cwd=ROOT,
            env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=20,check=False)
        output=result.stdout.decode("utf-8","strict").replace("\r\n","\n").strip()
        self.assertFalse(result.stderr, "Unexpected native process diagnostic")
        self.assertNotIn("P210-SYNTHETIC-CREDENTIAL",output)
        self.assertNotIn("CredWriteW",output)
        return result.returncode,output

    def _scenario(self,name):
        os_exit,output=self._run(name)
        self.assertEqual(os_exit,0)
        self.assertEqual(output,
            "P210_STATUS="+EXPECTED[name]+"\nP210_REAL_EFFECT=NEVER_ENABLED")

    def test_01_missing_owner_denied(self):self._scenario("missing-owner")
    def test_02_forged_approval_denied(self):self._scenario("forged-review")
    def test_03_replay_one_fake_attempt_and_recovery(self):self._scenario("replay")
    def test_04_restart_after_durable_intent_no_effect(self):self._scenario("crash-after-intent")
    def test_05_uncertain_effect_survives_restart(self):self._scenario("uncertain-effect")
    def test_06_historic_rollback_cannot_rearm(self):self._scenario("rollback-valid")
    def test_07_tampered_dpapi_refused(self):self._scenario("tamper")
    def test_08_revocation_before_fake_attempt(self):self._scenario("revoke")
    def test_09_delete_ack_is_mandatory(self):self._scenario("delete-ack")
    def test_10_missing_journal_never_grants(self):self._scenario("missing-journal")

    def test_11_unknown_target_and_extra_approval_arguments_refused(self):
        # Unlike a production IPC message, this test process has no authority;
        # arbitrary namespace, forged flags, extra CLI fields are rejected.
        for args in [
          ("--target=other.provider",),
          ("uncertain-effect","--approved"),
          ("replay","nayeon-v1/secret/other.api_key"),
          tuple(),
        ]:
            with self.subTest(args=args):
                os_exit,output=self._run(*args)
                self.assertIn("P210_STATUS=DENIED",output)
                self.assertNotIn("P210_STATUS=UNCERTAIN_RECOVERY_REQUIRED",output)
                self.assertEqual(os_exit,2 if len(args)==1 else 0)

    def test_12_original_Python_hold_refuses_all_effect_entries(self):
        identifier=SecretIdentifier(FIXED)
        fake=SecretValue("P210-SYNTHETIC-CREDENTIAL")
        hold=P206LegacyEffectHoldCandidate()
        for action in (
            lambda:hold.get(identifier),
            lambda:hold.is_available(identifier),
            lambda:hold.put(identifier,fake),
            lambda:hold.delete(identifier),
        ):
            with self.assertRaises(SecretStorageError):
                action()
        # Still an ungoverned P132 mutation entrypoint in the original
        # product source. Testing this risk is NOT a retrofit of authority.
        code=(ROOT/"nayeon/brain/local_byok_user_scope.py").read_text("utf8")
        self.assertIn("self._backend.put(_FIXED_IDENTIFIER, candidate)",code)
        self.assertIn("self._backend.delete(_FIXED_IDENTIFIER)",code)

    def test_13_native_test_symbol_does_not_create_signed_service_authority(self):
        code=(ROOT/"native_c1_candidate/P210SyntheticBoundaryExecutable.cs").read_text("utf8")
        self.assertIn("#if C1_SYNTHETIC_TEST",code)
        self.assertNotIn("CredWriteW(",code)
        self.assertNotIn("CredDeleteW(",code)
        self.assertNotIn("ServiceBase.Run(",code)
        original=(ROOT/"native_c1_candidate/CustodyService.cs").read_text("utf8")
        self.assertIn("throw new InvalidOperationException",original)
        self.assertNotIn("ServiceBase.Run(",original)

if __name__=="__main__":
    unittest.main()
