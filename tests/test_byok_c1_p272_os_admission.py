"""P272 source contracts only. No product import or native execution."""
import importlib.util
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'bff6895f5f0b4f086f0c4ed97f5f46a44f8d2762'
BRANCH = 'byok-c1-p272-os-bound-custody-admission-20261118'
SOURCE = 'native_c1_successor/P272OsBoundCustodyAdmission.cs'
DRIVER = 'tests/p272_successor/P272OsCustodyAdmissionTests.cs'
WORKFLOW = '.github/workflows/p272-windows-os-custody-admission.yml'
PATHS = {SOURCE, DRIVER, WORKFLOW, 'tests/test_byok_c1_p272_os_admission.py',
         'docs/byok-c1-p272-os-custody-admission.md'}
REQUIRED = (
    '#if !DEBUG\n#error P272_NO_RELEASE_BUILD',
    '#if !C1_P272_DEVELOPMENT_ONLY || !C1_REVIEW_ISOLATED_ASSEMBLY',
    '#error P272_ISOLATED_DEVELOPMENT_REQUIRED',
    'IndependentMonotonicAuthority { get { return DependencyState.NotWired; } }',
    'AuthenticatedExactOperationConsent { get { return DependencyState.NotWired; } }',
    'QualifiedPrincipalDecision { get { return DependencyState.NotValidated; } }',
    'IsolatedRunningTokenAndSigner { get { return DependencyState.NotValidated; } }',
    'ProtectedStoreRoot { get { return DependencyState.NotValidated; } }',
    'CustodyFreshness { get { return DependencyState.NotValidated; } }',
    'RunningIdentityProof { get { return DependencyState.NotValidated; } }',
    'return ServiceGate.ServiceName;',
    'return "NT SERVICE\\\\" + ServiceGate.ServiceName;',
    'new ServiceController(ServiceGate.ServiceName, ".")',
    'service.Refresh(); start = service.Status;', 'service.Refresh(); end = service.Status;',
    'P261ScmEvidence before = P261ScmReadOnlyAdmission.Observe();',
    'P261ScmEvidence after = P261ScmReadOnlyAdmission.Observe();',
    'if (!SameConfiguration(a, b) || start != end) return ScmSampleState.Changed;',
    'Win32Exception win32 = e.InnerException as Win32Exception;',
    'ClassifyError(win32.NativeErrorCode)', 'code == 1060', 'code == 5',
    'private readonly DurableDevelopmentBridge bridge;',
    'private OsBoundCustodyAdmission(DurableDevelopmentBridge owned)',
    'return new OsBoundCustodyAdmission(null);',
    'DurableDevelopmentBridge.RequireHosted();',
    'Environment.GetEnvironmentVariable("P272_HOSTED_DISPOSABLE") != "1"',
    'RequireHostedTests();\n            return new OsBoundCustodyAdmission(new DurableDevelopmentBridge(root, operation, true));',
    'return bridge.Submit(bridge.Prepare());',
    'if (bridge != null) bridge.Dispose();\n                disposed = true;',
)


def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def require(value, reason):
    if not value:
        raise AssertionError(reason)


def contract(source):
    for token in REQUIRED:
        require(token in source, token)
    for name in ('ProductionEligible', 'RealKeyEligible', 'MayInvokeWinCred'):
        require('public bool ' + name + ' { get { return false; } }' in source, name)
    require(re.findall(r'public\s+(?:static\s+)?\w+\s+(\w+)\s*\(', source) ==
            ['CreateReadOnly', 'AttemptProduction', 'Dispose'], 'exact public callable seam')
    body = re.search(r'public CustodyAdmissionResult AttemptProduction\(CustodyOperation operation\)\s*\{([^{}]*)\}', source)
    require(body is not None and body[1].strip() == 'return new CustodyAdmissionResult(operation);',
            'production attempt must have no bridge effect path')
    require(not re.search(r'\b(?:DllImport|CredRead\w*|CredWrite\w*|CredDelete\w*|'
                          r'CreateService\w*|StartService\w*|ChangeService\w*|DeleteService\w*|'
                          r'PendingCustodyTransaction|P96Fixture|ActualCoordinator|Process|'
                          r'Assembly|Impersonate\w*|Registry\w*)\b', source), 'forbidden authority')
    require('e.Message' not in source and 'Console.' not in source, 'no system detail logging')
    require(re.findall(r'service\.(\w+)', source) == ['Refresh', 'Status', 'Refresh', 'Status'],
            'read-only status sampling')


def workflow_contract(source):
    for token in (PARENT, BRANCH, 'windows-2022', 'arch: x64', 'arch: x86', 'fetch-depth: 2',
                  'permissions:\n  contents: read', 'persist-credentials: false',
                  '11bd71901bbe5b1630ceea73d27597364c9af683',
                  'ece7cb06caefa5fff74198d8649806c4678c61a1', "python-version: '3.12.8'",
                  "$env:REVIEW_REPO -cne $env:GITHUB_REPOSITORY", "$_ -cnotmatch '^A\\t'",
                  '/warnaserror+', "(@('ALL') + $flags)", 'C1_P272_DEVELOPMENT_ONLY',
                  'C1_REVIEW_ISOLATED_ASSEMBLY', 'P271DurableBridgeTests.cs', 'ScmReadOnlyTests.cs',
                  'P96NegativeProof', 'github-hosted', 'P271_HOSTED_DISPOSABLE', 'P272_HOSTED_DISPOSABLE',
                  'CASES=17', 'CASES=38', 'TESTS_PASSED=15', '60000', 'Stop-Process -Id $process.Id',
                  '$null = $process.Handle', '$code = $process.ExitCode', '$code = $LASTEXITCODE',
                  '$code -ne 0', '$timedOut', '-runtime.exit', '.exit', 'Get-FileHash', 'SHA256=',
                  'source-pins.json', 'Source bytes changed', 'if: always()', 'NO_RAW_PROCESS_EXIT'):
        require(token in source, token)
    require(not re.search(r'^\s*(?:push|pull_request_target|workflow_dispatch|schedule):', source, re.M),
            'PR only')
    require(not re.search(r'self-hosted|ExecutionPolicy|Unblock-File|continue-on-error|secrets\.|'
                          r'CredRead|CredWrite|CredDelete|Invoke-Expression|upload-artifact', source, re.I),
            'hosted text receipts only')
    require(source.count('uses: ') == 2, 'only pinned dependencies')


class P272SourceTests(unittest.TestCase):
    def test_native_contract(self):
        contract(read(SOURCE))

    def test_native_mutations_rejected(self):
        source = read(SOURCE)
        for token in REQUIRED:
            with self.subTest(token=token), self.assertRaises(AssertionError):
                contract(source.replace(token, ''))
        for name in ('ProductionEligible', 'RealKeyEligible', 'MayInvokeWinCred'):
            before = 'public bool ' + name + ' { get { return false; } }'
            with self.subTest(name=name), self.assertRaises(AssertionError):
                contract(source.replace(before, before.replace('false', 'true')))
        for added in ('CredWrite();', 'new PendingCustodyTransaction();',
                      'public void Promote(bool approved) {}', 'service.Start();'):
            with self.subTest(added=added), self.assertRaises(AssertionError):
                contract(source + '\n' + added)
        with self.assertRaises(AssertionError):
            contract(source.replace('{ return new CustodyAdmissionResult(operation); }',
                                    '{ bridge.Start(); return new CustodyAdmissionResult(operation); }'))

    def test_exact_scope_and_parent_bytes(self):
        head = git('rev-parse', 'HEAD')
        if head == PARENT:
            self.assertEqual(git('branch', '--show-current'), BRANCH)
        else:
            self.assertEqual(git('rev-list', '--parents', '-n', '1', 'HEAD').split(), [head, PARENT])
        changes = git('diff', '--name-status', '--no-renames', PARENT).splitlines()
        self.assertTrue(all(line.startswith('A\t') for line in changes), changes)
        delta = {line.split('\t', 1)[1] for line in changes}
        self.assertEqual(delta | set(git('ls-files', '--others', '--exclude-standard').splitlines()), PATHS)
        # Every historical tracked byte, not only selected P261/P268-P271 files.
        entries = [line.split('\t', 1) for line in git('ls-tree', '-r', PARENT).splitlines()]
        paths = [path for _, path in entries]
        hashes = subprocess.check_output(['git', 'hash-object', '--no-filters', '--stdin-paths'],
                                         input='\n'.join(paths) + '\n', cwd=ROOT, text=True).splitlines()
        self.assertEqual(len(hashes), len(entries))
        for (metadata, path), actual in zip(entries, hashes):
            self.assertEqual(metadata.split()[2], actual, path)

    def test_preserved_p271_source_and_adversaries(self):
        # P271's exact five-path topology test is specific to its own increment.
        # Do not weaken/edit it. This successor proves a stronger whole-parent
        # byte boundary above, and reuses all four topology-independent tests.
        spec = importlib.util.spec_from_file_location('p271_frozen', ROOT / 'tests/test_byok_c1_p271_durable_integration.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in ('test_contract', 'test_mutations_red', 'test_hosted_harness', 'test_pinned_workflow'):
            module.P271SourceTests(name).debug()

    def test_runtime_adversary_inventory(self):
        source = read(DRIVER)
        for token in ('RequireHostedTests();', 'real-scm-missing-no-service-created', 'operation-denied-',
                      'wrong-service-name', 'LocalSystem-conflict', 'derived-name-missing-isolated-token',
                      'restricted-SID-semantics-malformed-config', 'query-denied-resize-delete-races',
                      'parallel-claimants-cannot-promote', 'consent-provenance-environment-no-opt-in',
                      'actual-P271-owned-production-denial-zero-effects', 'uncertain-custody-zero-effects',
                      'same-user-rollback-equivocation-stale-restart', 'hosted-synthetic-factory-refusal',
                      'final-missing-no-created-service', 'DataProtectionScope.CurrentUser',
                      'reopened.InspectConsistent() && reopened.RecoveryRequired',
                      'live.TestEffects == 0', 'live.TestEffects == 1', 'thread.Join(5000)',
                      '55000', 'Environment.Exit(124)', 'Directory.Delete(Root, false)'):
            self.assertIn(token, source)
        self.assertNotRegex(source, r'error\.Message|Directory.Delete\(Root, true\)|Cred(Read|Write|Delete)')

    def test_workflow_and_red_mutations(self):
        source = read(WORKFLOW)
        workflow_contract(source)
        for before, after in ((PARENT, '0' * 40), ('/warnaserror+', ''), ('github-hosted', 'spoof'),
                              ('$code = $process.ExitCode', '$code = 0'), ('CASES=38', 'CASES=37'),
                              ('contents: read', 'contents: write'), ('arch: x86', 'arch: arm64'),
                              ('Get-FileHash', 'Get-Item'), ('3.12.8', '3.12')):
            with self.subTest(before=before), self.assertRaises(AssertionError):
                workflow_contract(source.replace(before, after))


if __name__ == '__main__':
    unittest.main()
