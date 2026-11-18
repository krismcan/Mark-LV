"""Bounded P270 source contract and red mutation tests; no credential effects."""
import hashlib
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'native_c1_successor/P270DevelopmentDurableWitness.cs'
PATHS = {
    SOURCE,
    'tests/p270_successor/P270DurableWitnessTests.cs',
    'tests/test_byok_c1_p270_durable_witness.py',
    '.github/workflows/p270-windows-durable-custody.yml',
    'docs/byok-c1-p270-durable-custody.md',
}
PARENT = 'b160244c26dda096e86ec03ca0bd23b10ed29679'
FROZEN = {
    'tests/p95_native_custody_preflight/CustodyLedger.cs': '93a5eeec6ee6cc4f6fff5146b5709f57cbdd37559d62de0bd4691bf678d5ce0b',
    'tests/p96_native_transaction_negative/PendingCustodyTransaction.cs': 'd8b8e4c6d5ea5e035b58c6ad73dd758c16640167c804ccf3305969b12bdf81ab',
    'native_c1_successor/P269ComposedDevelopmentService.cs': 'cf4550d3bcc14e0a88ee4f2d6af2082eb666fdae19d6567b9a133fc48a39a0d7',
    '.github/workflows/p269-windows-service-p96-composition.yml': '81ea9bfc0fc3b829579eda605ce65ee903c134f7404f4268622d4a7cd8e30b75',
}


def contract(source):
    required = (
        '#if !DEBUG', '#error P270_NO_RELEASE_BUILD',
        '#if !C1_P270_DEVELOPMENT_ONLY', '#error P270_DEVELOPMENT_OPT_IN_REQUIRED',
        'internal sealed class DurableWitness : IDisposable',
        'Environment.OSVersion.Platform == PlatformID.Win32NT',
        'Path.GetDirectoryName(root), temp, StringComparison.OrdinalIgnoreCase',
        'DriveType == DriveType.Fixed', 'Guid.TryParseExact', 'Directory.GetFileSystemEntries(root).Length == 0',
        'acl.GetOwner(typeof(SecurityIdentifier)).Equals(sid) && acl.AreAccessRulesProtected',
        'Require(rules.Count == 1)', 'rule.IdentityReference.Equals(sid)',
        'FileSystemRights.FullControl', 'CheckHandle(h, true)',
        '0x02200000', '0x80200000', 'Require(info.Links == 1)',
        'stream.GetAccessControl().GetOwner(typeof(SecurityIdentifier)).Equals(sid)',
        'Require(entries.Length == 2)', 'FileAttributes.ReparsePoint | FileAttributes.Directory',
        'stream.Length > 0 && stream.Length <= MaxBlob',
        'BitConverter.ToInt32(blob, 0) == blob.Length - 4',
        'ProtectedData.Protect(plain, Entropy(name), DataProtectionScope.CurrentUser)',
        'ProtectedData.Unprotect(protectedBytes, Entropy(name), DataProtectionScope.CurrentUser)',
        'NAYEON:P270:DISPOSABLE-CUSTODY:V1:', 'sid.Value + ":" + root + ":" + name',
        'stream.Flush(true)', 'String.Equals(Read(stream, name), text, StringComparison.Ordinal)',
        'private bool recovery = true', 'private readonly bool fresh',
        'fresh && !recovery && !disposed && awaitingAnchor == null',
        'expected == Snapshot(true) && Snapshot(false) == CustodyLedger.Anchor(expected)',
        'replacement.StartsWith(expected, StringComparison.Ordinal) && after.Length == before.Length + 1',
        'fresh && !recovery && !disposed && awaitingAnchor != null',
        'expected == Snapshot(false) && replacement == awaitingAnchor',
        'value == (isJournal ? knownJournal : knownAnchor)',
        'catch { recovery = true; throw new LedgerBlocked(); }',
    )
    for token in required:
        if token not in source:
            raise ValueError('Missing protection: ' + token)
    for forbidden in ('CredRead', 'CredWrite', 'CredDelete', 'IProtectedPendingState',
                      'SaveOrReplace', 'DeletePending', 'ProductionFactory'):
        if forbidden in source:
            raise ValueError('Authority expansion: ' + forbidden)
    for stream in ('journal', 'anchor'):
        start = source.index('recovery = true;', source.index('internal void Write' + stream.title()))
        persist = source.index('Persist(' + stream, start)
        if persist <= start:
            raise ValueError('Missing prewrite uncertainty latch')


class P270SourceTests(unittest.TestCase):
    def test_contract(self):
        contract((ROOT / SOURCE).read_text(encoding='utf-8-sig'))

    def test_mutations_red(self):
        original = (ROOT / SOURCE).read_text(encoding='utf-8-sig')
        for old, new in (
            ('stream.Flush(true)', 'stream.Flush()'),
            ('0x80200000', '0x80000000'),
            ('Require(info.Links == 1)', 'Require(true)'),
            ('Require(entries.Length == 2)', 'Require(entries.Length >= 2)'),
            ('stream.Length <= MaxBlob', 'stream.Length <= Int32.MaxValue'),
            ('BitConverter.ToInt32(blob, 0) == blob.Length - 4', 'true'),
            ('expected == Snapshot(true)', 'true'),
            ('expected == Snapshot(false)', 'true'),
            ('private bool recovery = true', 'private bool recovery = false'),
            ('fresh && !recovery && !disposed', '!disposed'),
            ('DataProtectionScope.CurrentUser', 'DataProtectionScope.LocalMachine'),
            ('#if !DEBUG', '#if RELEASE'),
            ('acl.AreAccessRulesProtected', 'true'),
            ('sid.Value + ":" + root + ":" + name', 'name'),
            ('String.Equals(Read(stream, name), text, StringComparison.Ordinal)', 'true'),
            ('value == (isJournal ? knownJournal : knownAnchor)', 'true'),
        ):
            with self.subTest(mutation=old):
                self.assertIn(old, original)
                with self.assertRaises(ValueError):
                    contract(original.replace(old, new))
        for effect in ('CredRead', 'CredWrite', 'CredDelete', 'IProtectedPendingState'):
            with self.assertRaises(ValueError):
                contract(original + '\n' + effect)

    def test_frozen_and_exact_scope(self):
        for path, expected in FROZEN.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
        head = git('rev-parse', 'HEAD')
        if head != PARENT:
            self.assertEqual(git('rev-parse', 'HEAD^'), PARENT)
        changed = set(filter(None, git('diff', '--name-only', PARENT).splitlines()))
        untracked = set(filter(None, git('ls-files', '--others', '--exclude-standard').splitlines()))
        self.assertEqual(changed | untracked, PATHS)
        for line in git('diff', '--name-status', '--no-renames', PARENT).splitlines():
            self.assertTrue(line.startswith('A\t'), line)

    def test_hosted_runner_safety_and_cases(self):
        text = (ROOT / 'tests/p270_successor/P270DurableWitnessTests.cs').read_text(encoding='utf-8-sig')
        for token in ('github-hosted', 'P270_HOSTED_DISPOSABLE', 'WindowsIdentity.GetCurrent().IsSystem',
                      'Directory.Delete(Root, false)', 'File.Delete(path)', 'torn-half-journal-flushed',
                      'journal-only-crash', 'same-process-stale-cas-latches', 'repeat-enrollment',
                      'cross-root-entropy', 'file-reparse-denied-if-supported', 'same-sid-replay-never-restarts'):
            self.assertIn(token, text)
        self.assertNotIn('Directory.Delete(Root, true)', text)
        self.assertNotIn('CredWrite', text)

    def test_workflow_pins_guards_and_watchdog(self):
        text = (ROOT / '.github/workflows/p270-windows-durable-custody.yml').read_text(encoding='utf-8-sig')
        for token in (PARENT, 'windows-latest', 'arch: x64', 'arch: x86', '/warnaserror+',
                      'System.Security.dll', '40000', 'runtime.exit', 'Get-FileHash',
                      'P270_NO_RELEASE_BUILD', 'P270_DEVELOPMENT_OPT_IN_REQUIRED', 'P270_HOSTED_DISPOSABLE',
                      '11bd71901bbe5b1630ceea73d27597364c9af683',
                      'ece7cb06caefa5fff74198d8649806c4678c61a1'):
            self.assertIn(token, text)
        self.assertNotIn('ExecutionPolicy', text)
        self.assertNotIn('upload-artifact', text)  # Text evidence stays in job logs; no binaries.


if __name__ == '__main__':
    unittest.main()
