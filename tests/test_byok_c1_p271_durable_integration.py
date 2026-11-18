"""P271 static contracts and red mutations; never executes a native binary."""
import re
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PARENT = '1b9c3d56a942930d059065a05b84b127cf671bfb'
SOURCE = 'native_c1_successor/P271DurableDevelopmentBridge.cs'
RUNNER = 'tests/p271_successor/P271DurableBridgeTests.cs'
WORKFLOW = '.github/workflows/p271-windows-durable-service-integration.yml'
PATHS = {SOURCE, RUNNER, WORKFLOW, 'tests/test_byok_c1_p271_durable_integration.py',
         'docs/byok-c1-p271-durable-service-integration.md'}
REQUIRED = (
    '#if !DEBUG', '#error P271_NO_RELEASE_BUILD', '#if !C1_P271_DEVELOPMENT_ONLY',
    '#error P271_DEVELOPMENT_OPT_IN_REQUIRED',
    'private readonly DurableWitness witness;',
    'private readonly ComposedDevelopmentService service;',
    'Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true"',
    'Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted"',
    'Environment.GetEnvironmentVariable("P271_HOSTED_DISPOSABLE") == "1"',
    'Require(!identity.IsSystem)', 'RequireHosted();',
    'witness = new DurableWitness(root, fresh);',
    'Require(!witness.RecoveryRequired && witness.InspectConsistent());',
    'PersistPrior(CustodyLedger.AppendIntent(j, LedgerOperation.Save, CustodyLedger.NewNonce()));',
    'PersistPrior(CustodyLedger.AppendTerminal(witness.ReadJournal()));',
    'service = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, true);',
    'service.TestState.Journal = knownJournal; service.TestState.Anchor = knownAnchor;',
    'service.TestAdapter.Inject = Probe;',
    'Require(service.TestAdapter.Enrolled && service.TestState.Trusted);',
    'Require(service.TestState.Journal == knownJournal && service.TestState.Anchor == knownAnchor);',
    'Require(witness.ReadJournal() == knownJournal && witness.ReadAnchor() == knownAnchor);',
    'Require(service.TestState.Present == expectedPresent);',
    'Require(awaitingAnchor || !witness.RecoveryRequired);',
    'Require(!awaitingAnchor && !witness.RecoveryRequired && witness.InspectConsistent());',
    'witness.WriteJournal(knownJournal, next);', 'witness.WriteAnchor(knownAnchor, next);',
    'Require(witness.ReadJournal() == next && witness.ReadAnchor() == knownAnchor);',
    'Require(witness.ReadJournal() == knownJournal && witness.ReadAnchor() == next);',
    'Require(next == CustodyLedger.Anchor(knownJournal));',
    'Require(CustodyLedger.Verify(knownJournal, knownAnchor) == LedgerPhase.InFlight &&',
    'CustodyLedger.LastOperation(knownJournal) == operation);',
    'catch { Interlocked.Exchange(ref failed, 1); throw new LedgerBlocked(); }',
    'return service.TestSubmit(ticket, operation);',
    'return service.RevokeDevelopment();', 'return service.StopDevelopment();',
    'return service.FaultDevelopment();',
    'try { service.Dispose(); }',
    'catch { Interlocked.Exchange(ref failed, 1); throw; }',
    'Interlocked.Exchange(ref disposed, 1); witness.Dispose();',
)


def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def contract(source):
    for token in REQUIRED:
        if token not in source:
            raise ValueError('Missing protection: ' + token)
    code = re.sub(r'//[^\n]*', '', source)
    for forbidden in (r'\bPendingCustodyTransaction\b', r'\bP96Fixture\b', r'\bActualCoordinator\b',
                      r'\bCred(Read|Write|Delete)\b', r'\bDllImport\b', r'\bReflection\b',
                      r'\bSaveOrReplace\s*\(', r'\bDeletePending\s*\('):
        if re.search(forbidden, code):
            raise ValueError('Authority expansion: ' + forbidden)
    start = source.index('private void Probe(')
    hook = source.index('if (inject != null) inject(point);', start)
    check = source.index('Require(Volatile.Read(ref failed)', start)
    journal = source.index('witness.WriteJournal(knownJournal, next);', start)
    latch = source.index('awaitingAnchor = true;', start)
    if not hook < check < latch < journal:
        raise ValueError('Hook or uncertainty ordering')
    edge = source.index('if (point == "effect-enter")', start)
    complete = source.index('CheckComplete();', edge)
    verify = source.index('CustodyLedger.Verify(knownJournal, knownAnchor)', edge)
    if not edge < complete < verify:
        raise ValueError('Final edge must verify durable pair')
    cleanup = source.index('public void Dispose()')
    stop = source.index('try { service.Dispose(); }', cleanup)
    retain = source.index('catch { Interlocked.Exchange(ref failed, 1); throw; }', stop)
    release = source.index('Interlocked.Exchange(ref disposed, 1); witness.Dispose();', retain)
    if not stop < retain < release or 'finally' in source[stop:release]:
        raise ValueError('Failed stop must retain custody')


class P271SourceTests(unittest.TestCase):
    def test_contract(self):
        contract(read(SOURCE))
        # Freeze the callback/effect call ordering relied on by the new bridge.
        p268 = read('native_c1_successor/P268ServiceOwnedPendingTransaction.cs')
        self.assertIn('SaveCalls++; Probe("effect-enter"); fixture.SaveOrReplace(value); Probe("effect-return");', p268)
        self.assertIn('DeleteCalls++; Probe("effect-enter"); fixture.DeletePending(); Probe("effect-return");', p268)
        self.assertIn('Monitor.TryEnter(gate, 500)', p268)
        self.assertNotRegex(p268, r'\bPendingCustodyTransaction\b|\bP96Fixture\b|\bActualCoordinator\b')
        p269 = read('native_c1_successor/P269ComposedDevelopmentService.cs')
        self.assertIn('pending = ServiceOwnedPendingTransaction.DevelopmentOnlyHost(', p269)
        self.assertNotRegex(p269, r'\bPendingCustodyTransaction\b|\bP96Fixture\b|\bActualCoordinator\b')

    def test_mutations_red(self):
        source = read(SOURCE)
        # Each protection must be independently observed; no weakening for a pass.
        for token in REQUIRED:
            with self.subTest(removed=token):
                self.assertIn(token, source)
                with self.assertRaises(ValueError):
                    contract(source.replace(token, '', 1) if source.count(token) == 1 else source.replace(token, ''))
        for added in ('PendingCustodyTransaction old;', 'P96Fixture old;', 'ActualCoordinator.Apply();',
                      'CredWrite();', 'SaveOrReplace(value);', 'DeletePending();', 'DllImport("x");'):
            with self.subTest(added=added), self.assertRaises(ValueError):
                contract(source + '\n' + added)
        for old, new in (('awaitingAnchor = true;', ''),
                         ('if (inject != null) inject(point);', ''),
                         ('catch { Interlocked.Exchange(ref failed, 1); throw; }',
                          'finally { Interlocked.Exchange(ref failed, 1); }'),
                         ('if (point == "effect-enter")\n                    {\n                        CheckComplete();',
                          'if (point == "effect-enter")\n                    {')):
            with self.subTest(order=old), self.assertRaises(ValueError):
                contract(source.replace(old, new, 1))

    def test_exact_additive_scope_and_frozen_history(self):
        head = git('rev-parse', 'HEAD')
        if head != PARENT:
            self.assertEqual(git('rev-list', '--parents', '-n', '1', 'HEAD').split(),
                             [head, PARENT])
        else:
            self.assertEqual(git('branch', '--show-current'),
                             'byok-c1-p271-service-owned-durable-custody-20261118')
        changes = git('diff', '--name-status', '--no-renames', PARENT).splitlines()
        for line in changes:
            self.assertTrue(line.startswith('A\t'), line)
        changed = {line.split('\t', 1)[1] for line in changes}
        untracked = set(git('ls-files', '--others', '--exclude-standard').splitlines())
        self.assertEqual(changed | untracked, PATHS)
        # Exact delta forbids ALL edits to P95/P96, historical negatives, P268-P270.
        self.assertEqual(git('diff', PARENT, '--', 'tests/p96_native_transaction_negative',
                             'tests/p95_native_custody_preflight',
                             'native_c1_successor/P268ServiceOwnedPendingTransaction.cs',
                             'native_c1_successor/P269ComposedDevelopmentService.cs',
                             'native_c1_successor/P270DevelopmentDurableWitness.cs'), '')

    def test_hosted_harness(self):
        source = read(RUNNER)
        for token in ('DurableDevelopmentBridge.RequireHosted();', 'Directory.Delete(Root, false)',
                      'acl.SetOwner(sid); acl.SetAccessRuleProtection(true, false);',
                      'FileSystemRights.FullControl', 'Guid.NewGuid().ToString("N")',
                      'fresh-', 'revoke-first-', 'effect-first-', 'simultaneous-revoke',
                      'duplicate-submission', 'durable-write-failure-', 'b.TestCloseWitness();',
                      'dispose-timeout-retains-custody', 'Check(b.TestConsistent()); // old finally-release would fail',
                      'snapshot-skew-', 'critical-edge-untrusted', 'recovery-latch-refusal',
                      'injected-effect-failure', 'live-extra-root-entry', 'exclusive-ownership-refusal',
                      'root-acl-refusal', 'crash-consistent-restart-no-rearm', 'journal-only-crash-no-repair',
                      'missing-', 'torn-', 'corrupt-', 'f.Flush(true)', 'hosted-gate-refusal',
                      '55000', 'Environment.Exit(124)', 'P271_FAIL_CASE=', 'P271_FAIL_STAGE='):
            self.assertIn(token, source)
        self.assertNotIn('Directory.Delete(Root, true)', source)
        self.assertNotIn('error.Message', source)
        self.assertNotRegex(source, r'\bPendingCustodyTransaction\b|\bActualCoordinator\b')

    def test_pinned_workflow(self):
        source = read(WORKFLOW)
        for token in (PARENT, 'windows-latest', 'arch: x64', 'arch: x86', 'fetch-depth: 2',
                      '11bd71901bbe5b1630ceea73d27597364c9af683',
                      'ece7cb06caefa5fff74198d8649806c4678c61a1',
                      '/main:P271DurableBridgeTests', '/warnaserror+', 'System.Security.dll',
                      'System.ServiceProcess.dll', "(@('ALL') + $flags)",
                      'C1_P271_DEVELOPMENT_ONLY', 'C1_P270_DEVELOPMENT_ONLY',
                      'github-hosted', 'P271_HOSTED_DISPOSABLE', '60000', 'CASES=38',
                      'runtime.exit', 'python.exit', 'compile.exit', 'Get-FileHash',
                      '$code -ne 0', '$timedOut', 'Missing runtime receipt'):
            self.assertIn(token, source)
        self.assertNotIn('self-hosted', source)
        self.assertNotIn('ExecutionPolicy', source)
        self.assertNotIn('upload-artifact', source)


if __name__ == '__main__':
    unittest.main()
