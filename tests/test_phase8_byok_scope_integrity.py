"""Adversarial BYOK exact-descendant admission; all test cases read-only."""
import ast
from pathlib import Path
import re
import unittest
from unittest import mock

from tests import phase8_byok_scope_migration as gate
from tests import phase_8_37_scope_migration as old


class ExactBYOKScopeTests(unittest.TestCase):
    def test_nine_paths_and_immutable_parent_identity(self):
        self.assertEqual(len(gate.ADDED), 6)
        self.assertEqual(len(gate.MODIFIED), 5)
        self.assertTrue(gate.ADDED.isdisjoint(gate.MODIFIED))
        self.assertEqual(set(gate.CANDIDATE_SHA256), gate.ENVELOPE)
        self.assertEqual(gate.SELF, "tests/phase8_byok_scope_migration.py")
        self.assertEqual(gate.PARENT, "87208af710bac90c440f2e0851854318b22e9b88")
        self.assertEqual(gate.PARENT_TREE, "417d4c88c76d542ee109d49a53fe522780bcebb3")
        self.assertEqual(gate.PARENT_TAG_OBJECT, "ee8ffc208be5626aecbb1b6c4955ad2a0cbdac63")
        self.assertIn("tests/phase_8_37_scope_migration.py", gate.MODIFIED)
        self.assertIn("tests/test_phase_837_scope_integrity.py", gate.MODIFIED)
        self.assertIn("tests/phase_8_30_scope_migration.py", gate.MODIFIED)
        self.assertIn("tests/test_phase_836_scope_integrity.py", gate.MODIFIED)
        self.assertIn(".codex/CURRENT_STATE.md", gate.MODIFIED)

    def test_original_guard_source_and_history_are_still_real(self):
        # Frozen old 8.37 code can be inspected through immutable Git, not
        # runtime HEAD and not a weakened current-state fallback.
        protected = gate._git("show", gate.PARENT+":tests/phase_8_37_scope_migration.py")
        current = (gate.ROOT/"tests/phase_8_37_scope_migration.py").read_bytes()
        self.assertTrue(current.startswith(protected))
        self.assertIs(old._assert_837_historical, old.__dict__["_assert_837_historical"])
        self.assertIsNot(old.assert_837_integrity, old._assert_837_historical)
        self.assertEqual(gate._parent_tree(), old._tree(gate.PARENT))

    def test_exact_current_unstaged_source_scope(self):
        self.assertIn(gate.assert_byok_integrity(),
                      {"COMPLETE_UNSTAGED", "EXACT_STAGED", "EXACT_CHILD"})

    def test_original_836_live_method_only_update_and_admission_canaries(self):
        # Keep every historic synthetic refusal identical to sealed 8.37;
        # this exact live method alone binds the newer sealed BYOK parent.
        from tests.test_phase_836_scope_integrity import Phase836IntegrityTests
        old_source = gate._git("show", gate.PARENT + ":tests/test_phase_836_scope_integrity.py")
        new_source = (gate.ROOT/"tests/test_phase_836_scope_integrity.py").read_bytes()
        start=b"    def test_live_candidate_requires_exact_current_topology(self):"
        end=b"    def test_historical_tag_cannot_be_replaced(self):"
        self.assertEqual(old_source.count(start), 1)
        self.assertEqual(new_source.count(start), 1)
        old_head,old_body=old_source.split(start,1)
        new_head,new_body=new_source.split(start,1)
        self.assertEqual(old_head,new_head)
        self.assertEqual(old_body.split(end,1)[1],new_body.split(end,1)[1])
        test=Phase836IntegrityTests("test_live_candidate_requires_exact_current_topology")
        test.setUp()
        try:
            test.test_live_candidate_requires_exact_current_topology()
            raw=old._git
            for wanted,replacement,message in (
                (("branch","--show-current"),b"untrusted-branch\n","Wrong 8.37 product branch"),
                (("show-ref","--verify","--hash","--","refs/tags/"+gate.PARENT_TAG),
                 b"0"*40+b"\n","BYOK protected annotated tag mismatch"),
            ):
                def tampered(*a,w=wanted,b=replacement):
                    return b if a==w else raw(*a)
                with self.subTest(injected=wanted),mock.patch.object(old,"_git",side_effect=tampered):
                    with self.assertRaisesRegex(AssertionError,message):
                        test.test_live_candidate_requires_exact_current_topology()
        finally:
            test.doCleanups()

    def test_each_byte_pin_refuses_tamper(self):
        real = gate._disk
        for target in sorted(gate.ENVELOPE):
            with self.subTest(target=target):
                with mock.patch.object(gate, "_disk",
                    side_effect=lambda path, t=target: real(path)+b"tamper"
                        if path == t else real(path)):
                    with self.assertRaisesRegex(AssertionError, "BYOK candidate byte mismatch"):
                        gate.assert_byok_integrity()

    def test_invalid_pin_refuses_before_disk_access(self):
        with mock.patch.dict(gate.CANDIDATE_SHA256,
                             {"tests/test_first_run_connection_owner.py": "0"*64}):
            with self.assertRaisesRegex(AssertionError, "BYOK unfinalized source pin"):
                gate.assert_byok_integrity()
        without = gate.CANDIDATE_SHA256.copy()
        without.pop("tests/test_first_run_connection_owner.py")
        with mock.patch.object(gate, "CANDIDATE_SHA256", without):
            with self.assertRaisesRegex(AssertionError, "BYOK unapproved manifest"):
                gate.assert_byok_integrity()

    def test_forbid_unknown_or_ignored_loader(self):
        original = old._git
        topology = gate.assert_byok_integrity()
        # Every topology must reject the injected file; refusal wording differs.
        unexpected = {
            "COMPLETE_UNSTAGED": "BYOK unexpected untracked path",
            "EXACT_STAGED": "BYOK partial stage",
            "EXACT_CHILD": "BYOK unapproved committed or staged inventory",
        }[topology]
        for arg, data, reason in (
            (("ls-files","--others","--exclude-standard","-z"),
             b"evil.py\0", unexpected),
            (("ls-files","--others","--ignored","--exclude-standard","-z"),
             b"tests/__pycache__/fake.pyc\0", "BYOK ignored executable"),
        ):
            def injected(*args, wanted=arg, payload=data):
                found = original(*args)
                return found+payload if args==wanted else found
            with self.subTest(args=arg), mock.patch.object(old,"_git",side_effect=injected):
                with self.assertRaisesRegex(AssertionError,reason):
                    gate.assert_byok_integrity()

    def test_wrong_branch_and_untrusted_parent_tag_refused(self):
        original = old._git
        args_list = (
            (("branch","--show-current"),b"another-branch\n","Wrong 8.37 product branch"),
            (("show-ref","--verify","--hash","--","refs/tags/"+gate.PARENT_TAG),
             b"1"*40+b"\n","BYOK protected annotated tag mismatch"),
        )
        for wanted,payload,reason in args_list:
            def modified(*args, w=wanted, p=payload):
                return p if args == w else original(*args)
            with self.subTest(args=wanted),mock.patch.object(old,"_git",side_effect=modified):
                with self.assertRaisesRegex(AssertionError,reason):
                    gate.assert_byok_integrity()

    def test_root_has_no_fake_success_or_generic_stage_waiver(self):
        source=(gate.ROOT/gate.SELF).read_text(encoding="utf-8")
        tree=ast.parse(source)
        self.assertNotIn("skipIf",source)
        self.assertNotIn("pytest.mark.skip",source)
        calls=[node for node in ast.walk(tree)
               if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
        self.assertNotIn("eval",{c.func.id for c in calls})
        self.assertNotIn("exec",{c.func.id for c in calls})

    def _synthetic(self, mode, *, partial=False, merge=False):
        """Raw Git-shaped proof; immutable old-chain integrity tested separately."""
        baseline = gate._parent_tree()
        expected = dict(baseline)
        for path in gate.ENVELOPE:
            expected[path] = ("100644", old._blob(gate._disk(path)))
        if partial:
            selected = {"nayeon/desktop_alpha/first_run_connection_owner.py"}
            staged = {**baseline, **{p: expected[p] for p in selected}}
        else:
            staged = baseline if mode == "COMPLETE_UNSTAGED" else expected
        commit = expected if mode == "EXACT_CHILD" else baseline
        head = "e"*40 if mode == "EXACT_CHILD" else gate.PARENT
        untracked = gate.ADDED - set(staged)
        def raw_delta(paths, oldmap, newmap):
            result = b""
            for p in sorted(paths):
                om, oi = oldmap.get(p, ("000000","0"*40))
                nm, ni = newmap[p]
                status = "A" if p not in oldmap else "M"
                result += (f":{om} {nm} {oi} {ni} {status}".encode()
                           + b"\0" + p.encode() + b"\0")
            return result
        def flags(index):
            return b"".join(b"H "+p.encode()+b"\0" for p in sorted(index))
        def fake_git(*args):
            if args == ("rev-parse","--show-object-format"):return b"sha1\n"
            if args == ("rev-parse","HEAD"):return (head+"\n").encode()
            if args == ("branch","--show-current"):return b"nayeon-v1\n"
            if args[:2] == ("merge-base","--is-ancestor"):return b""
            if args == ("ls-files","-v","--sparse","-z"):return flags(staged)
            if args == ("ls-files","--others","--exclude-standard","-z"):
                return b"".join(p.encode()+b"\0" for p in sorted(untracked))
            if args == ("ls-files","--others","--ignored","--exclude-standard","-z"):return b""
            if args == ("diff","--no-renames","--raw","--no-abbrev","-z"):
                return raw_delta(gate.MODIFIED,staged,expected) if mode=="COMPLETE_UNSTAGED" else b""
            if args == ("diff","--no-renames","--raw","--no-abbrev","-z","--cached"):
                return raw_delta(gate.ENVELOPE,baseline,staged)
            if args == ("diff","--no-renames","--raw","--no-abbrev","-z",gate.PARENT,head):
                return raw_delta(gate.ENVELOPE,baseline,commit)
            if args == ("rev-list","--parents","-n","1",head):
                return (head+" "+gate.PARENT+(" "+"d"*40 if merge else "")+"\n").encode()
            raise AssertionError("Unexpected synthetic Git command: "+str(args))
        return baseline,expected,commit,staged,head,fake_git

    def test_simulated_exact_staged_and_child_topology(self):
        for state in ("EXACT_STAGED","EXACT_CHILD"):
            baseline,expected,committed,index,head,git = self._synthetic(state)
            with self.subTest(state=state),mock.patch.object(old,"_git",side_effect=git),\
                 mock.patch.object(gate,"_parent_tree",return_value=baseline),\
                 mock.patch.object(old,"_tree",return_value=committed),\
                 mock.patch.object(old,"_index",return_value=index):
                self.assertEqual(gate.assert_byok_integrity(),state)

    def test_simulated_partial_stage_and_merged_child_refused(self):
        cases=(("EXACT_STAGED",True,False,"BYOK partial stage"),
               ("EXACT_CHILD",False,True,"BYOK unexpected commit parent"))
        for state,partial,merge,reason in cases:
            baseline,expected,committed,index,head,git = self._synthetic(
                state,partial=partial,merge=merge)
            with self.subTest(state=state,partial=partial,merge=merge),\
                 mock.patch.object(old,"_git",side_effect=git),\
                 mock.patch.object(gate,"_parent_tree",return_value=baseline),\
                 mock.patch.object(old,"_tree",return_value=committed),\
                 mock.patch.object(old,"_index",return_value=index):
                with self.assertRaisesRegex(AssertionError,reason):
                    gate.assert_byok_integrity()


    def test_exact_byok_owner_projection_and_unknown_path_kept(self):
        from tests import phase_8_30_scope_migration as legacy
        from unittest import mock
        from tests.phase8_byok_scope_migration import assert_byok_integrity
        owner="nayeon/desktop_alpha/first_run_connection_owner.py"
        draft={"nayeon/desktop_alpha/offline_request_draft.py",
               "nayeon/desktop_alpha/offline_draft_consent.py"}
        unknown="nayeon/desktop_alpha/another_owner.py"
        with mock.patch.object(legacy,"_project_837_draft_sources",
                               wraps=legacy._project_837_draft_sources) as projection, (
             mock.patch("tests.phase8_byok_scope_migration.assert_byok_integrity",
                        wraps=assert_byok_integrity)) as owner_guard, (
             mock.patch("tests.phase_8_37_scope_migration.assert_837_integrity",
                        return_value="COMPLETE_UNSTAGED")):
            self.assertEqual(legacy._project_837_draft_sources({owner,unknown}),{unknown})
            self.assertEqual(legacy._project_837_draft_sources(draft|{owner,unknown}),
                             {unknown})
            self.assertEqual(owner_guard.call_count,2)
            self.assertEqual(projection.call_count,2)

    def test_byok_owner_projection_rejects_forged_or_absent_admission(self):
        from tests import phase_8_30_scope_migration as legacy
        from unittest import mock
        owner="nayeon/desktop_alpha/first_run_connection_owner.py"
        for bad in (None, True, "UNVERIFIED", "EXACT_CHILD "):
            with self.subTest(bad=bad), mock.patch(
                "tests.phase8_byok_scope_migration.assert_byok_integrity",
                return_value=bad):
                with self.assertRaisesRegex(AssertionError,"Unadmitted BYOK owner"):
                    legacy._project_837_draft_sources({owner})
        with mock.patch(
            "tests.phase8_byok_scope_migration.assert_byok_integrity",
            side_effect=AssertionError("BYPASS_REFUSED")):
            with self.assertRaisesRegex(AssertionError,"BYPASS_REFUSED"):
                legacy._project_837_draft_sources({owner})
        # No owner path: do not invoke new gate or suppress unknown names.
        with mock.patch(
            "tests.phase8_byok_scope_migration.assert_byok_integrity",
            side_effect=AssertionError("SHOULD_NOT_BE_CALLED")):
            self.assertEqual(legacy._project_837_draft_sources({"other.py"}),
                             {"other.py"})


if __name__ == "__main__":
    unittest.main()
