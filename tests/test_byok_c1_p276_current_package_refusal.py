"""P276 source-only refusal tests. Never import or execute the WinCred backend.

Temporary trees contain text copies only. Mutants execute only the standalone
deny-only P211 policy, never copied product modules or executable payloads.
Same-user alternate Advapi32 access remains a real OS threat.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
import hashlib
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
import unittest

from nayeon.brain import p211_high_assurance_package_quarantine as policy
from scripts.p275_product_effect_entrypoint_inventory import check_backend


ROOT = Path(__file__).resolve().parents[1]
POLICY = "nayeon/brain/p211_high_assurance_package_quarantine.py"
BACKEND = "nayeon/secrets/windows_credential.py"
CONTROLLER = "nayeon/brain/local_byok_user_scope.py"
LAUNCHER = "nayeon/desktop_alpha/local_byok_launch_bridge.py"
COMPANION = "nayeon/desktop_alpha/frozen_signed_byok_companion.py"
BENIGN = "P211_QUARANTINE_README.txt"
BACKEND_SHA256 = "9FFB136A73E4277B966FAE025A3962123433745B6BA8907AB3B8C4137F4A21B3"
AUTHORITY_FIELDS = (
    "release_eligible", "credential_mutation_authorised",
    "signed_installer_authorised", "trusted_runtime_isolation_proven",
    "real_key_pilot_authorised",
)


@contextmanager
def source_copy():
    with TemporaryDirectory(prefix="p276-source-only-") as directory:
        root = Path(directory)
        for relative in policy._FIXED_LEGACY_FILES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        yield root


def replace_source(root, relative, before, after):
    path = root / relative
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise AssertionError("Synthetic mutation must hit exactly once: " + before)
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


@contextmanager
def mutant_policy(tree):
    # Dataclasses need their own registered module. No original module/test
    # is replaced, and the mutant is removed even if a canary fails.
    name = "_p276_isolated_policy_mutant"
    if name in sys.modules:
        raise AssertionError("Mutant module collision")
    module = ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(ast.fix_missing_locations(tree), "<p276-policy-mutant>", "exec"), module.__dict__)
        yield module
    finally:
        del sys.modules[name]


class CurrentPackageRefusalTests(unittest.TestCase):
    def assert_denied(self, receipt, reason=None):
        if reason is not None:
            self.assertEqual(receipt.reason, reason)
        for field in AUTHORITY_FIELDS:
            self.assertIs(getattr(receipt, field), False, field)

    def assert_route_contract(self, module, root, risk, reason):
        witness = module.inspect_current_source_tree(root)
        self.assertTrue(witness.exact_legacy_source_readable)
        self.assertIs(witness.python_direct_native_credential_effect, False)
        self.assertIs(witness.high_assurance_legacy_risk_present, False)
        self.assertIs(witness.source_mode_runtime_risk_present, risk)
        self.assert_denied(module.review_high_assurance_package_plan(root, [BACKEND]), reason)

    def test_01_actual_p275_witness_distinguishes_runtime_from_retired_native_effect(self):
        witness = policy.inspect_current_source_tree(ROOT)
        self.assertTrue(witness.p132_product_constructor_and_effect)
        self.assertTrue(witness.p133_source_mode_launcher)
        self.assert_route_contract(policy, ROOT, True, policy.P211Refusal.LEGACY_EFFECT_PATH)
        # Historical property retains the exact original triple, including
        # direct native effects; no reinterpretation of the old witness.
        for direct in (False, True):
            for controller in (False, True):
                for launcher in (False, True):
                    synthetic = policy.P211SourceWitness(True, direct, controller, launcher, True, True)
                    self.assertEqual(synthetic.high_assurance_legacy_risk_present,
                                     direct and controller and launcher)
                    self.assertEqual(synthetic.source_mode_runtime_risk_present,
                                     controller and launcher)

    def test_02_known_routes_executable_extensions_and_mixed_readme_refuse_specifically(self):
        payloads = [
            BACKEND, CONTROLLER, LAUNCHER,
            "nayeon/desktop_alpha/local_byok_window.py",
            "native_c1_candidate/CustodyService.cs", "core/installer.py",
            "scripts/unknown", "tests/unknown", "build/unknown", "dist/unknown",
            "NayeonLocalByokOffline.exe",
            *("untrusted" + suffix for suffix in (
                ".py", ".PY", ".pyc", ".pyd", ".dll", ".DLL", ".whl",
                ".zip", ".msi", ".msix", ".ps1", ".pyw", ".bat", ".cmd",
                ".vbs", ".js", ".sh")),
        ]
        for payload in payloads:
            for names in ([payload], [BENIGN, payload]):
                with self.subTest(names=names):
                    receipt = policy.review_high_assurance_package_plan(ROOT, names)
                    self.assert_denied(receipt, policy.P211Refusal.LEGACY_EFFECT_PATH)
                    self.assertEqual(receipt.manifest_entries, len(names))

    def test_03_read_only_default_is_not_packaging_authority_and_unknown_text_stays_unknown(self):
        self.assert_denied(policy.review_high_assurance_package_plan(ROOT, [BENIGN]),
                           policy.P211Refusal.ABSENT_RELEASE_AUTHORITY)
        self.assert_denied(policy.review_high_assurance_package_plan(ROOT, ["README.md"]),
                           policy.P211Refusal.UNRECOGNISED_PAYLOAD)
        self.assert_denied(policy.review_high_assurance_package_plan(ROOT, [BENIGN.lower()]),
                           policy.P211Refusal.UNRECOGNISED_PAYLOAD)

    def test_04_missing_unreadable_and_malformed_source_never_becomes_safe(self):
        for relative in policy._FIXED_LEGACY_FILES:
            with self.subTest(missing=relative), source_copy() as root:
                (root / relative).unlink()
                for names in ([BACKEND], [BENIGN]):
                    self.assert_denied(policy.review_high_assurance_package_plan(root, names),
                                       policy.P211Refusal.SOURCE_UNPROVEN)
        with source_copy() as root:
            (root / BACKEND).write_bytes(b"\xff\xfe")
            self.assert_denied(policy.review_high_assurance_package_plan(root, [BACKEND]),
                               policy.P211Refusal.SOURCE_UNPROVEN)
        python_sources = (
            BACKEND, CONTROLLER, LAUNCHER,
            "nayeon/desktop_alpha/local_byok_window.py",
            "nayeon/desktop_alpha/application.py",
            "nayeon/desktop_alpha/workspace_window.py", COMPANION,
        )
        self.assertEqual(set(python_sources),
                         {path for path in policy._FIXED_LEGACY_FILES if path.endswith(".py")})
        malformed = {"syntax": "def broken(:", "NUL": "\x00",
                     "parse_valid_compile_invalid": "return\n"}
        # A top-level return parses successfully but must fail compilation.
        tree = ast.parse(malformed["parse_valid_compile_invalid"])
        with self.assertRaises(SyntaxError):
            compile(tree, "<p276-compile-invalid-source>", "exec")
        for relative in python_sources:
            for kind, suffix in malformed.items():
                with self.subTest(malformed=relative, kind=kind), source_copy() as root:
                    path = root / relative
                    path.write_text(path.read_text(encoding="utf-8") + "\n" + suffix,
                                    encoding="utf-8")
                    self.assertFalse(policy.inspect_current_source_tree(root).exact_legacy_source_readable)
                    for names in ([BACKEND], [BENIGN], ["README.md"]):
                        receipt = policy.review_high_assurance_package_plan(root, names)
                        self.assert_denied(receipt, policy.P211Refusal.SOURCE_UNPROVEN)
                        self.assertFalse(receipt.source_witness.exact_legacy_source_readable)
                    self.assert_denied(policy.review_high_assurance_package_plan(root, ["../x.py"]),
                                       policy.P211Refusal.UNTRUSTED_PATH)

    def test_05_original_test18_factory_mutation_preserves_unrecognised_reason(self):
        with source_copy() as root:
            replace_source(root, CONTROLLER, "WindowsCredentialBackend()", "None")
            self.assertFalse(policy.inspect_current_source_tree(root).p132_product_constructor_and_effect)
            self.assert_route_contract(policy, root, False, policy.P211Refusal.UNRECOGNISED_PAYLOAD)
            self.assert_denied(policy.review_high_assurance_package_plan(root, ["nayeon/brain/new_safe.py"]),
                               policy.P211Refusal.UNRECOGNISED_PAYLOAD)

    def test_06_each_controller_put_delete_call_is_required_for_known_route_evidence(self):
        for call in ("_mutation_backend.put(_FIXED_IDENTIFIER, candidate)",
                     "_mutation_backend.delete(_FIXED_IDENTIFIER)"):
            with self.subTest(call=call), source_copy() as root:
                replace_source(root, CONTROLLER, call, "_mutation_backend.no_effect()")
                self.assertFalse(policy.inspect_current_source_tree(root).p132_product_constructor_and_effect)
                self.assert_route_contract(policy, root, False, policy.P211Refusal.UNRECOGNISED_PAYLOAD)

    def test_07_changed_fixed_module_or_python_launcher_still_refuses_code(self):
        for before, after in (
            ('"nayeon.desktop_alpha.local_byok_window"', '"synthetic.other_module"'),
            ('command = [sys.executable, "-B", "-m", _CHILD_MODULE]', 'command = []'),
        ):
            with self.subTest(before=before), source_copy() as root:
                replace_source(root, LAUNCHER, before, after)
                self.assertFalse(policy.inspect_current_source_tree(root).p133_source_mode_launcher)
                self.assert_route_contract(policy, root, False, policy.P211Refusal.UNRECOGNISED_PAYLOAD)

    def test_08_forged_approval_and_filled_companion_pins_cannot_grant_release(self):
        with source_copy() as root:
            for field in ("MAIN", "COMPANION", "SIGNER_CERT"):
                replace_source(root, COMPANION, '_APPROVED_' + field + '_SHA256 = ""',
                               '_APPROVED_' + field + '_SHA256 = "' + "f" * 64 + '"')
            replace_source(root, COMPANION, "_APPROVED_CODE_INTEGRITY_RELEASE = False",
                           "_APPROVED_CODE_INTEGRITY_RELEASE = True")
            self.assertFalse(policy.inspect_current_source_tree(root).frozen_companion_pins_absent)
            for names, reason in (([BENIGN], policy.P211Refusal.ABSENT_RELEASE_AUTHORITY),
                                  ([BACKEND], policy.P211Refusal.LEGACY_EFFECT_PATH)):
                self.assert_denied(policy.review_high_assurance_package_plan(
                    root, names, claimed_signer="f" * 64,
                    claimed_policy_approval={"GOV": "GO", "WDAC": True, "signed": True}), reason)

    def test_09_invalid_aliases_ads_collisions_and_malformed_plans_precede_classification(self):
        invalid = ("../x.py", "safe/../x.py", "./x.py", "x./payload", "x /payload",
                   "C:x.py", "C:/x.py", "x.py:stream", "safe\\x.py", "//host/x.py",
                   "/x.py", "safe//x.py", "x.py ", "x.py.", "\x00.py", None)
        # Even with unreadable source these must be path refusals first.
        with TemporaryDirectory(prefix="p276-empty-") as directory:
            for root in (ROOT, Path(directory)):
                for name in invalid:
                    with self.subTest(name=name, root=root):
                        self.assert_denied(policy.review_high_assurance_package_plan(root, [name]),
                                           policy.P211Refusal.UNTRUSTED_PATH)
                self.assert_denied(policy.review_high_assurance_package_plan(root, ["x.dll", "X.DLL"]),
                                   policy.P211Refusal.UNTRUSTED_PATH)
        for names in ([], [BENIGN] * 129, (n for n in [BENIGN]), BENIGN):
            self.assert_denied(policy.review_high_assurance_package_plan(ROOT, names),
                               policy.P211Refusal.INVALID_PLAN)

    def test_10_all_authority_fields_are_frozen_and_positive_construction_is_rejected(self):
        receipt = policy.review_high_assurance_package_plan(ROOT, [BENIGN])
        for field in AUTHORITY_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(FrozenInstanceError):
                    setattr(receipt, field, True)
                with self.assertRaises(ValueError):
                    policy.P211PackageRefusalReceipt(policy.P211Refusal.ABSENT_RELEASE_AUTHORITY,
                                                     1, None, **{field: True})

    def test_11_branch_removal_and_false_or_true_risk_mutants_are_caught(self):
        source = (ROOT / POLICY).read_text(encoding="utf-8")
        branch = "or source.source_mode_runtime_risk_present"
        self.assertEqual(source.count(branch), 1)
        removed = ast.parse(source.replace(branch, "or False", 1))
        with mutant_policy(removed) as mutant, self.assertRaises(AssertionError):
            self.assert_route_contract(mutant, ROOT, True, mutant.P211Refusal.LEGACY_EFFECT_PATH)
        for value in (False, True):
            with self.subTest(constant_risk=value), source_copy() as root:
                if value:
                    replace_source(root, CONTROLLER, "WindowsCredentialBackend()", "None")
                tree = ast.parse(source)
                method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                              and node.name == "source_mode_runtime_risk_present")
                self.assertIsInstance(method.body[-1], ast.Return)
                method.body[-1].value = ast.Constant(value=value)
                with mutant_policy(tree) as mutant, self.assertRaises(AssertionError):
                    self.assert_route_contract(mutant, root, not value,
                        mutant.P211Refusal.UNRECOGNISED_PAYLOAD if value else mutant.P211Refusal.LEGACY_EFFECT_PATH)

    def test_12_exact_p275_backend_has_no_native_effect_or_plaintext_return_and_policy_is_inert(self):
        raw = (ROOT / BACKEND).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest().upper(), BACKEND_SHA256)
        # P275's original AST contract checks exact read/free ownership,
        # denial-only read, boolean-only native returns, no native mutators,
        # no pointer escape and no plaintext extraction. It executes no IO.
        check_backend(raw.decode("utf-8"))
        tree = ast.parse((ROOT / POLICY).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree)
                    if isinstance(node, ast.Import) for alias in node.names}
        imported.update(node.module.split(".")[0] for node in ast.walk(tree)
                        if isinstance(node, ast.ImportFrom) and node.module)
        self.assertEqual(imported, {"__future__", "ast", "dataclasses", "enum", "pathlib", "typing"})
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {"WinDLL", "CredWriteW", "CredDeleteW", "Popen", "run",
                                  "write_text", "write_bytes", "copy", "unlink"})


if __name__ == "__main__":
    unittest.main()
