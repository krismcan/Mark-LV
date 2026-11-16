"""Synthetic P252 runner tests; no production imports or native effects."""
from pathlib import Path
import hashlib
import os
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from scripts import p252_current_original_p76_native_reconciliation as r


def sources():
    result = {r.P76: ('BRANCH = ' + repr(r.HISTORICAL_BRANCH)).encode()}
    for tid in r.IDS:
        module, cls, method = tid.rsplit('.', 2)
        p = module.replace('.', '/') + '.py'
        result[p] = result.get(p, b'') + (
            f'class {cls}:\n    def {method}(self): pass\n').encode()
    # Coalesce repeated synthetic class definitions.
    p = r.IDS[0].rsplit('.', 2)[0].replace('.', '/') + '.py'
    result[p] = ('class BYOKBHistoricalFixtureProjectionTests:\n' + ''.join(
        '    def ' + tid.rsplit('.', 1)[1] + '(self): pass\n' for tid in r.IDS[:2]) +
        'class ExactBYOKBTests:\n    def ' + r.IDS[2].rsplit('.', 1)[1] + '(self): pass\n').encode()
    return result


class SourceTests(unittest.TestCase):
    def test_exact_ids_and_source_inventory(self):
        self.assertEqual(r.IDS, (
            'tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_live_brain_reader_tamper_remains_rejected_after_historical_replay',
            'tests.test_phase8_byok_b_scope_integrity.BYOKBHistoricalFixtureProjectionTests.test_projected_historical_brain_corruption_is_causally_rejected',
            'tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_literal_exact23_parent_manifest_and_live_admission',
            'tests.test_phase_834_scope_integrity.Phase834CandidateTests.test_real_candidate_exact_bytes_and_live_predecessor_route',
        ))
        self.assertEqual(len(set(r.IDS)), 4)
        self.assertEqual(r.IDS[0].split('.')[:2], ['tests', 'test_phase8_byok_b_scope_integrity'])
        self.assertEqual(r.IDS[3].split('.')[:2], ['tests', 'test_phase_834_scope_integrity'])
        raws = sources()
        self.assertEqual(r.assess(raws, {p: r.sha(v) for p, v in raws.items()}),
                         {p: r.sha(v) for p, v in raws.items()})

    def test_source_drift(self):
        raws = sources()
        pins = {p: r.sha(v) for p, v in raws.items()}
        raws[r.P76] += b'\n# drift'
        with self.assertRaisesRegex(r.Refused, 'source drift'):
            r.assess(raws, pins)

    def test_missing_inventory_even_if_bytes_pinned(self):
        raws = sources()
        p = r.IDS[3].rsplit('.', 2)[0].replace('.', '/') + '.py'
        raws[p] = b'class Phase834CandidateTests: pass'
        with self.assertRaisesRegex(r.Refused, 'test inventory'):
            r.assess(raws, {p: r.sha(v) for p, v in raws.items()})

    def test_missing_source_closure(self):
        with self.assertRaises(r.Refused):
            r.assess({}, {'missing.py': '0'*64})

    def test_branch_pin_cannot_be_spoofed(self):
        raws = sources()
        raws[r.P76] = b'BRANCH = "current"'
        with self.assertRaisesRegex(r.Refused, 'historical branch'):
            r.assess(raws, {p: r.sha(v) for p, v in raws.items()})

    def test_effect_authorization_env_rejected(self):
        for key in ('P134_NATIVE_EFFECTS_AUTH', 'p134_any', 'GIT_DIR', 'PYTHONPATH'):
            with self.subTest(key=key), self.assertRaises(r.Refused):
                r.environment({key: 'synthetic'})

    def test_credentials_never_forwarded(self):
        env = r.environment({'PATH': 'synthetic', 'OPENAI_API_KEY': 'fake',
                             'CUSTOM_EFFECT_AUTH': 'fake', 'GH_TOKEN': 'fake'})
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('CUSTOM_EFFECT_AUTH', env)
        self.assertNotIn('GH_TOKEN', env)


class CheckoutTests(unittest.TestCase):
    def reply(self, root, env, *args):
        values = {
            ('rev-parse', '--show-toplevel'): str(r.ROOT).encode()+b'\n',
            ('rev-parse', 'HEAD'): r.HEAD.encode()+b'\n',
            ('rev-parse', 'HEAD^{tree}'): r.TREE.encode()+b'\n',
            ('rev-parse', r.HEAD + '^{tree}'): r.TREE.encode()+b'\n',
            ('rev-list', '--parents', '-n', '1', 'HEAD'): (r.HEAD+' '+'1'*40+'\n').encode(),
            ('branch', '--show-current'): r.BRANCH.encode()+b'\n',
            ('rev-parse', '--is-shallow-repository'): b'false\n',
            ('rev-parse', '--absolute-git-dir'): b'.git\n',
            ('rev-parse', '--git-common-dir'): b'.git\n',
            ('status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignored'):
                b''.join(b'?? '+p.encode()+b'\0' for p in sorted(r.ADDED)),
        }
        return values.get(args, b'')

    def check_rejection(self, change, message):
        def git(root, env, *args):
            return change(args, self.reply(root, env, *args))
        with (mock.patch.object(r, 'git', side_effect=git),
              mock.patch.object(r, 'checked'),
              mock.patch.object(r.os.path, 'lexists', return_value=False)):
            with self.assertRaisesRegex(r.Refused, message):
                r.preflight(r.ROOT, {})

    def test_wrong_head(self):
        self.check_rejection(lambda a,b: b'0'*40+b'\n' if a == ('rev-parse','HEAD') else b,
                             'wrong HEAD')

    def test_wrong_tree_and_branch(self):
        for query in (('rev-parse','HEAD^{tree}'), ('branch','--show-current')):
            self.check_rejection(lambda a,b: b'wrong\n' if a == query else b, 'wrong HEAD')

    def test_dirty_checkout_and_missing_envelope(self):
        for payload, reason in ((b' M product.py\0', 'dirty'),
                                (b'!! ignored.py\0', 'dirty'), (b'', 'incomplete')):
            self.check_rejection(lambda a,b: payload if a[0] == 'status' else b, reason)

    def test_wrong_path(self):
        with self.assertRaisesRegex(r.Refused, 'wrong checkout'):
            r.preflight(Path('wrong'), {})


class ChildTests(unittest.TestCase):
    def execute(self, code=1, timeout=False, complete=True):
        def fake(command, **kwargs):
            self.assertEqual(command, [str(r.PYTHON), '-B', '-m', 'unittest', r.IDS[0], '-v'])
            self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
            self.assertFalse(kwargs['shell'])
            self.assertEqual(kwargs['timeout'], 60)
            if complete:
                kwargs['stderr'].write(failure_output(r.IDS[0]))
            if timeout:
                raise subprocess.TimeoutExpired(command, 60)
            return subprocess.CompletedProcess(command, code)
        with tempfile.TemporaryDirectory() as directory:
            result = r.run_one(r.IDS[0], 1, Path(directory), {}, run=fake)
            self.assertEqual(result['stdout_sha256'], r.sha(b''))
            self.assertEqual(result['stderr_sha256'], r.sha((Path(directory)/'m1.stderr.raw').read_bytes()))
            return result

    def test_exit_one_preserved_as_failure(self):
        result = self.execute()
        self.assertEqual(result['child_exit'], 1)
        self.assertEqual(result['result'], 'FAIL')
        self.assertEqual(r.disposition([dict(result, test_id=tid) for tid in r.IDS]), ('HOLD', 1))

    def test_timeout_preserves_partial_logs_and_is_incomplete(self):
        result = self.execute(timeout=True)
        self.assertTrue(result['timed_out'])
        self.assertIsNone(result['child_exit'])
        self.assertFalse(result['complete_original_failure'])

    def test_other_exit_never_normalized(self):
        for code in (0, 2, 17):
            result = self.execute(code=code)
            self.assertEqual(result['child_exit'], code)
            self.assertEqual(result['result'], 'HOLD')

    def test_missing_method_output_is_not_original_failure(self):
        self.assertFalse(self.execute(complete=False)['complete_original_failure'])

    def test_no_false_go(self):
        for results in ([], [self.execute(code=0)]*4, [self.execute()]*3):
            self.assertEqual(r.disposition(results), ('HOLD', 2))

    def test_unknown_id_never_launched(self):
        run = mock.Mock()
        with self.assertRaises(r.Refused):
            r.run_one('unknown', 1, Path('unused'), {}, run)
        run.assert_not_called()




def failure_output(tid):
    method = tid.rsplit('.', 1)[1]
    title = (method + ' (' + tid + ')').encode()
    return (title + b' ... FAIL\r\n\r\n' + b'='*70 + b'\r\nFAIL: ' + title +
            b'\r\n' + b'-'*70 + b'\r\nTraceback (most recent call last):\r\nAssertionError: ' +
            r.MARKER + b'\r\n\r\n' + b'-'*70 + b'\r\nRan 1 test in 0.123s\r\n\r\nFAILED (failures=1)\r\n')


class StrictEvidenceTests(unittest.TestCase):
    def test_ordered_four_only(self):
        rows = [dict(test_id=t, complete_original_failure=True) for t in r.IDS]
        self.assertEqual(r.disposition(rows), ('HOLD', 1))
        for bad in ([rows[0]]*4, rows[::-1], rows + rows[:1]):
            self.assertEqual(r.disposition(bad), ('HOLD', 2))

    def test_misleading_child_output(self):
        raw = failure_output(r.IDS[0])
        self.assertTrue(r.original_failure(r.IDS[0], b'', raw))
        for bad in (raw + b'ERROR\n', raw.replace(b'failures=1', b'failures=2'),
                    raw + raw, raw.replace(b'Ran 1 test', b'Ran 2 tests'),
                    raw.replace(b'Traceback', b'Ran 2 tests in 0.1s\nTraceback'),
                    raw.replace(b'Traceback', b'SKIP\nTraceback'),
                    raw.replace(r.IDS[0].encode(), r.IDS[1].encode()),
                    b'misleading\n' + raw, raw.replace(b'FAIL:', b'ERROR:')):
            with self.subTest(raw=bad):
                self.assertFalse(r.original_failure(r.IDS[0], b'', bad))
        self.assertFalse(r.original_failure(r.IDS[0], b'ERROR', raw))

    def test_receipt_exclusive_create(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'receipt.json'
            r.write_receipt(path, {'historical': True})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                r.write_receipt(path, {'historical': False})
            self.assertEqual(path.read_bytes(), before)


class FullPreflightTests(unittest.TestCase):
    """Real temporary bytes and lstat; simulated read-only Git protocol."""
    def traverse(self, committed=False, change=None, mutate=None):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            raws = sources()
            raws.update({p: b'# synthetic source witness\n' for p in r.PINS if p not in raws})
            disk = dict(raws)
            disk.update({p: b'# additive diagnostic\n' for p in r.ADDED})
            for p, raw in disk.items():
                path = root/p
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            tracked = disk if committed else raws
            def oid(raw):
                return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest().encode()
            tree = b''.join(b'100644 blob '+oid(v)+b'\t'+p.encode()+b'\0'
                            for p,v in sorted(tracked.items()))
            index = b''.join(b'100644 '+oid(v)+b' 0\t'+p.encode()+b'\0'
                             for p,v in sorted(tracked.items()))
            head = 'a'*40 if committed else r.HEAD
            values = {
                ('rev-parse','--show-toplevel'): str(root).encode()+b'\n',
                ('rev-parse','HEAD'): head.encode()+b'\n',
                ('rev-parse','HEAD^{tree}'): (('b'*40) if committed else r.TREE).encode()+b'\n',
                ('rev-parse',r.HEAD+'^{tree}'): r.TREE.encode()+b'\n',
                ('branch','--show-current'): r.BRANCH.encode()+b'\n',
                ('rev-list','--parents','-n','1','HEAD'): (head+' '+(r.HEAD if committed else 'c'*40)).encode()+b'\n',
                ('for-each-ref','refs/replace'): b'',
                ('rev-parse','--is-shallow-repository'): b'false\n',
                ('rev-parse','--absolute-git-dir'): str(root/'.git').encode()+b'\n',
                ('rev-parse','--git-common-dir'): str(root/'.git').encode()+b'\n',
                ('status','--porcelain=v1','-z','--untracked-files=all','--ignored'):
                    b'' if committed else b''.join(b'?? '+p.encode()+b'\0' for p in sorted(r.ADDED)),
                ('ls-files','-v','-z'): b''.join(b'H '+p.encode()+b'\0' for p in sorted(tracked)),
                ('ls-files','--stage','-z'): index,
                ('ls-tree','-r','-z','HEAD'): tree,
                ('diff-tree','--no-commit-id','--name-status','--no-renames','-r','-z',r.HEAD,head):
                    b''.join(b'A\0'+p.encode()+b'\0' for p in sorted(r.ADDED)),
            }
            def fake_git(_root, _env, *args):
                value = values[args]  # Unexpected Git operations fail the test.
                return change(args, value) if change else value
            if mutate:
                mutate(root)
            with (mock.patch.object(r, 'ROOT', root),
                  mock.patch.object(r, '__file__', str(root/sorted(r.ADDED)[1])),
                  mock.patch.object(r, 'PINS', {p:r.sha(v) for p,v in raws.items()}),
                  mock.patch.object(r, 'assess', wraps=lambda rs: r_assess(rs, {p:r.sha(v) for p,v in raws.items()})),
                  mock.patch.object(r, 'git', side_effect=fake_git)):
                return r.preflight(root, {})

    def test_complete_parent_preflight(self):
        result = self.traverse()
        self.assertEqual(result['head'], r.HEAD)
        self.assertEqual(result['mode'], 'original_parent_untracked')
        self.assertEqual(set(result['addition_sha256']), r.ADDED)

    def test_complete_committed_preflight(self):
        result = self.traverse(True)
        self.assertEqual(result['head'], 'a'*40)
        self.assertEqual(result['tree'], 'b'*40)
        self.assertEqual(result['parents'], [r.HEAD])
        self.assertEqual(result['mode'], 'committed_child')

    def test_wrong_parent_and_merge(self):
        for parents in ('d'*40, r.HEAD+' '+'d'*40):
            with self.subTest(parents=parents), self.assertRaisesRegex(r.Refused, 'parent'):
                self.traverse(True, lambda a,v: ('a'*40+' '+parents).encode()
                              if a[0]=='rev-list' else v)

    def test_extra_changed_path(self):
        with self.assertRaisesRegex(r.Refused, 'delta'):
            self.traverse(True, lambda a,v: v+b'M\0original.py\0' if a[0]=='diff-tree' else v)

    def test_dirty_committed_tree(self):
        for status in (b' M original.py\0', b'A  staged.py\0', b'?? extra\0', b'!! ignored\0'):
            with self.subTest(status=status), self.assertRaisesRegex(r.Refused, 'dirty'):
                self.traverse(True, lambda a,v: status if a[0]=='status' else v)

    def test_hostile_tracked_bytes(self):
        with self.assertRaisesRegex(r.Refused, 'source drift'):
            self.traverse(mutate=lambda root: (root/r.P76).write_bytes(b'hostile'))

    def test_committed_runner_tamper(self):
        with self.assertRaisesRegex(r.Refused, 'source drift'):
            self.traverse(True, mutate=lambda root: (root/sorted(r.ADDED)[1]).write_bytes(b'hostile'))

    def test_index_and_flags_closure(self):
        for query in (('ls-files','--stage','-z'), ('ls-files','-v','-z')):
            with self.subTest(query=query), self.assertRaises(r.Refused):
                self.traverse(True, lambda a,v: v.split(b'\0',1)[1] if a==query else v)

    def test_hardlinked_tracked_and_added_files(self):
        for rel in (r.P76, sorted(r.ADDED)[1]):
            def link(root):
                os.link(root/rel, root/'alias')
            with self.subTest(rel=rel), self.assertRaisesRegex(r.Refused, 'unsafe'):
                self.traverse(mutate=link)

    def test_reparse_check_for_tracked_and_added(self):
        original = r.checked
        for rel in (r.P76, sorted(r.ADDED)[1]):
            def check(path):
                info = original(path)
                if path.as_posix().endswith(rel):
                    r.require(False, 'linked path')
                return info
            with mock.patch.object(r, 'checked', side_effect=check):
                with self.subTest(rel=rel), self.assertRaisesRegex(r.Refused, 'linked'):
                    self.traverse()

    def test_checked_rejects_reparse_and_symlink_metadata(self):
        for mode, attrs in ((0o100644, 0x400), (0o120777, 0)):
            info = SimpleNamespace(st_mode=mode, st_file_attributes=attrs)
            with mock.patch.object(Path, 'lstat', return_value=info):
                with self.subTest(mode=mode), self.assertRaisesRegex(r.Refused, 'linked path'):
                    r.checked(Path('synthetic'))


r_assess = r.assess


if __name__ == '__main__':
    unittest.main()
