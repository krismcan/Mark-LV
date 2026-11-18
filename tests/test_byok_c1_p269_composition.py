"""Bounded P269 source custody and deliberately red source mutations; no execution."""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOST = 'native_c1_successor/P269ComposedDevelopmentService.cs'
FROZEN = {
    'tests/p95_native_custody_preflight/CustodyLedger.cs': '93a5eeec6ee6cc4f6fff5146b5709f57cbdd37559d62de0bd4691bf678d5ce0b',
    'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs': 'd8b8e4c6d5ea5e035b58c6ad73dd758c16640167c804ccf3305969b12bdf81ab',
    'tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs': '2aeeaa8ba97396216b32d1894c8b8ea3af7face44fb3562ff1c4dde5e7dc582f',
    'native_c1_successor/P265DevelopmentPipeAdapter.cs': 'cc4065a40e8f7c8dd296ee913533e5aa611edd2bbbe0d830da8196a74a440636',
    'native_c1_successor/P267DevelopmentAtomicService.cs': 'f6d26d51de87e81156c0f4f4e335b125603c59188c823b013f7c1de18de48b5f',
    'native_c1_successor/P268ServiceOwnedPendingTransaction.cs': '964af496e72c5510823809e4ebb74e045d2f01e7f0a9fabe7dbae4625b172cfc',
}

def violations(source):
    failures = []
    code = re.sub(r'//[^\n]*', '', source)
    for symbol in ('DEBUG', 'C1_P265_DEVELOPMENT_ONLY', 'C1_P267_DEVELOPMENT_ONLY',
                   'C1_P268_DEVELOPMENT_ONLY', 'C1_P269_DEVELOPMENT_ONLY'):
        if '!' + symbol not in code:
            failures.append('guard')
    for forbidden in ('PrepareSynthetic', 'DispatchSynthetic', 'PendingCustodyTransaction',
                      'ServiceBase.Run', 'WinCred', 'CredWrite', 'public static', 'DllImport'):
        if forbidden in code:
            failures.append('forbidden:' + forbidden)
    for required in ('new DevelopmentAtomicService(freshSession)',
                     'new P96ApprovalFixture()', 'new P96StateFixture(TestApproval)',
                     'new P96GuardFixture(TestApproval)',
                     'ServiceOwnedPendingTransaction.DevelopmentOnlyHost(TestAdapter, TestGuard, freshSession)',
                     'new byte[] { 0x31, 0x32, 0x33, 0x34 }',
                     'private static int Main(string[] arguments) { return 64; }',
                     'if (!fresh || AdmissionClosed', 'if (!Admitted()) return CustodyOutcome.Denied;',
                     'finally { if (marker != null) Array.Clear(marker, 0, marker.Length); }'):
        if required not in code:
            failures.append('missing:' + required)
    close = code.split('private ControlResult Close(int reason)', 1)[-1].split('internal ControlResult RevokeDevelopment', 1)[0]
    if not re.search(r'Interlocked.Exchange\(ref closed, 1\);\s*try \{ return reason == 0 \? pending.Revoke\(\)', close):
        failures.append('close-order')
    if 'finally' not in close or close.find('lock (lifecycle)') < close.find('pending.Revoke()'):
        failures.append('cleanup-order')
    if 'effect = true, recovery = true' not in code or 'PendingMayHaveEffect, PendingRecoveryRequired' not in code:
        failures.append('uncertainty')
    return failures

class CompositionSourceTests(unittest.TestCase):
    def test_source_contract(self):
        self.assertEqual([], violations((ROOT / HOST).read_text(encoding='utf-8-sig')))

    def test_frozen_original_bytes(self):
        for path, expected in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(expected, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

    def test_negative_mutations(self):
        source = (ROOT / HOST).read_text(encoding='utf-8-sig')
        mutations = [source + '\n' + text for text in
                     ('PrepareSynthetic()', 'DispatchSynthetic()', 'PendingCustodyTransaction',
                      'ServiceBase.Run(null)', 'WinCred', 'public static void Factory() {}')]
        for old, new in [
            ('!C1_P269_DEVELOPMENT_ONLY', 'false'), ('!DEBUG', 'false'),
            ('new DevelopmentAtomicService(freshSession)', 'null'),
            ('0x31, 0x32, 0x33, 0x34', '0x30, 0x32, 0x33, 0x34'),
            ('return 64;', 'return 0;'), ('if (!fresh || AdmissionClosed', 'if (AdmissionClosed'),
            ('Interlocked.Exchange(ref closed, 1); // admission latch BEFORE pending control', '// missing latch'),
            ('effect = true, recovery = true', 'effect = false, recovery = false'),
            ('if (!Admitted()) return CustodyOutcome.Denied;', ''),
            ('finally { if (marker != null) Array.Clear(marker, 0, marker.Length); }', 'finally {}')]:
            self.assertIn(old, source)
            mutations.append(source.replace(old, new))
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(violations(mutation))

    def test_hosted_runner_contract(self):
        runner = (ROOT / 'tests/p269_successor/P269ComposedServiceTests.cs').read_text(encoding='utf-8-sig')
        for required in ('NamedPipeClientStream', 'TokenImpersonationLevel.Impersonation',
                         'ControlResult.TooLate', 'PendingRecoveryRequired', 'Transport.Submissions == 0',
                         'ThrowDuringEffect = true', 'BrokenTransport()', 'Restart()', 'NoReplay(',
                         'Traffic(endpoint, 3', 'controller.IsAlive', 'WaitOne(2000)', 'thread.Join(3000)'):
            self.assertIn(required, runner)
        self.assertNotIn('ServiceBase.Run', runner)

if __name__ == '__main__':
    unittest.main()
