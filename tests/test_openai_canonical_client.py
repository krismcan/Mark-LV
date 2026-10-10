"""Canonical client security tests; synthetic secrets and public SDK fakes only."""

import ast
import inspect
from pathlib import Path
import subprocess
import traceback
import unittest
from unittest.mock import Mock, patch

from nayeon.brain.providers import openai_client as m
from nayeon.secrets.contracts import SecretValue


ROOT = Path(__file__).resolve().parents[1]
START = "35c0246362fbecc3df8532b63d42087b32b22646"
SEALED = "94e0c2896c8df87421c80edcfc4fd3de48fd8ac7"
TAG = "nayeon-v1-openai-credential-validation-canonical-routing-01"
NEW = {"nayeon/brain/connection_document.py", "nayeon/brain/connection_persistence.py",
       "nayeon/brain/connection_service.py", "nayeon/brain/connection_bootstrap.py",
         "nayeon/brain/connection_composition.py", "nayeon/brain/connection_readiness.py",
         "nayeon/brain/connection_startup.py",
         "nayeon/brain/credential_onboarding.py",
         "nayeon/brain/credential_onboarding_composition.py",
         "nayeon/brain/connection_reconciliation.py",
         "nayeon/brain/connection_recovery_advice.py",
         "nayeon/brain/onboarding_status_view.py",
         "nayeon/brain/onboarding_configuration_proposal.py",
         "nayeon/brain/onboarding_metadata_document.py",
         "nayeon/brain/onboarding_metadata_review.py",
         "nayeon/brain/onboarding_metadata_change_preview.py",
         "nayeon/brain/onboarding_operation_advice.py",
         "nayeon/desktop_alpha/__init__.py",
         "nayeon/desktop_alpha/__main__.py",
         "nayeon/desktop_alpha/controller.py",
         "nayeon/desktop_alpha/window.py",
         "nayeon/desktop_alpha/notepad.py"}
DELTA = NEW


class SecretSubclass(SecretValue):
    pass


class IntSubclass(int):
    pass


class FloatSubclass(float):
    pass


class CanonicalClientTests(unittest.TestCase):
    def setUp(self):
        self.plaintext = " synthetic-key-\u2603 "
        self.secret = SecretValue(self.plaintext)
        self.sdk = Mock()
        self.http = Mock()
        loader_patch = patch.object(m, "_load_openai_sdk", return_value=(self.sdk, self.http))
        self.loader = loader_patch.start()
        self.addCleanup(loader_patch.stop)

    def test_signature_has_only_bounded_inputs(self):
        signature = inspect.signature(m.create_openai_client)
        self.assertEqual(list(signature.parameters), ["api_key", "timeout_seconds", "max_retries"])
        for name in ("timeout_seconds", "max_retries"):
            self.assertIs(signature.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIsNone(signature.parameters[name].default)

    def test_invalid_keys_fail_before_loading_or_revealing(self):
        duck = Mock(reveal=Mock(side_effect=AssertionError("no reveal")))
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            for value in (SecretSubclass("synthetic"), duck, None, {}, "synthetic", 1):
                with self.subTest(value=type(value)), self.assertRaises(TypeError):
                    m.create_openai_client(value)
            reveal.assert_not_called()
        duck.reveal.assert_not_called()
        self.loader.assert_not_called()

    def test_invalid_timeouts_fail_before_loading_or_revealing(self):
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            for value in (True, False, "5", IntSubclass(5), FloatSubclass(5), object(),
                          0, -1, 0.0, -0.1, float("nan"), float("inf"), -float("inf")):
                with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                    m.create_openai_client(self.secret, timeout_seconds=value)
            reveal.assert_not_called()
        self.loader.assert_not_called()

    def test_invalid_retries_fail_before_loading_or_revealing(self):
        with patch.object(SecretValue, "reveal", side_effect=AssertionError("no reveal")) as reveal:
            for value in (True, False, 0.0, "0", IntSubclass(0), -1, object()):
                with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                    m.create_openai_client(self.secret, max_retries=value)
            reveal.assert_not_called()
        self.loader.assert_not_called()

    def test_exact_routing_auth_and_omitted_defaults(self):
        with patch.object(SecretValue, "reveal", autospec=True, return_value=self.plaintext) as reveal:
            client = m.create_openai_client(self.secret)
            reveal.assert_called_once_with(self.secret)
        self.assertIs(client, self.sdk.return_value)
        self.loader.assert_called_once_with()
        self.http.assert_called_once_with(trust_env=False, follow_redirects=False)
        self.assertEqual(m.OPENAI_API_BASE_URL, "https://api.openai.com/v1")
        self.assertEqual(m.OPENAI_AUTHORIZATION_HEADER, "Authorization")
        self.sdk.assert_called_once_with(api_key=self.plaintext, base_url=m.OPENAI_API_BASE_URL,
            default_headers={"Authorization": "Bearer " + self.plaintext}, http_client=self.http.return_value)
        self.assertIs(self.sdk.call_args.kwargs["api_key"], self.plaintext)
        self.http.return_value.close.assert_not_called()

    def test_supplied_options_are_preserved(self):
        for timeout in (1, 5.0, 0.01, 10**400):
            for retries in (0, 2):
                with self.subTest(timeout=timeout, retries=retries):
                    m.create_openai_client(self.secret, timeout_seconds=timeout, max_retries=retries)
                    self.assertIs(self.sdk.call_args.kwargs["timeout"], timeout)
                    self.assertIs(self.sdk.call_args.kwargs["max_retries"], retries)

    def assert_safe_failure(self):
        try:
            m.create_openai_client(self.secret)
        except m.OpenAIClientConstructionError as error:
            self.assertEqual(str(error), "OpenAI client construction failed")
            self.assertIsNone(error.__cause__)
            self.assertTrue(error.__suppress_context__)
            self.assertNotIn(self.plaintext, traceback.format_exc())
        else:
            self.fail("expected construction failure")

    def test_sdk_load_failure_is_safe(self):
        self.loader.side_effect = ImportError(self.plaintext)
        self.assert_safe_failure()
        self.http.assert_not_called()

    def test_reveal_failure_is_safe_and_prevents_sdk_load(self):
        with patch.object(SecretValue, "reveal", side_effect=RuntimeError(self.plaintext)):
            self.assert_safe_failure()
        self.loader.assert_not_called()
        self.http.assert_not_called()
        self.sdk.assert_not_called()

    def test_http_constructor_failure_is_safe(self):
        self.http.side_effect = RuntimeError(self.plaintext)
        self.assert_safe_failure()
        self.sdk.assert_not_called()
        self.http.return_value.close.assert_not_called()

    def test_sdk_constructor_failure_closes_once(self):
        self.sdk.side_effect = RuntimeError(self.plaintext)
        self.assert_safe_failure()
        self.http.return_value.close.assert_called_once_with()

    def test_cleanup_failure_does_not_escape(self):
        self.sdk.side_effect = RuntimeError(self.plaintext)
        self.http.return_value.close.side_effect = RuntimeError(self.plaintext)
        self.assert_safe_failure()
        self.http.return_value.close.assert_called_once_with()

    def test_process_control_propagates(self):
        for target in (self.loader, self.http, self.sdk, self.http.return_value.close):
            for error_type in (KeyboardInterrupt, SystemExit):
                with self.subTest(target=target, error_type=error_type):
                    self.http.return_value.close.reset_mock()
                    self.loader.side_effect = self.http.side_effect = self.sdk.side_effect = None
                    self.http.return_value.close.side_effect = None
                    if target is self.http.return_value.close:
                        self.sdk.side_effect = RuntimeError("synthetic")
                    error = error_type()
                    target.side_effect = error
                    with self.assertRaises(error_type) as caught:
                        m.create_openai_client(self.secret)
                    self.assertIs(caught.exception, error)
                    if target is self.sdk or target is self.http.return_value.close:
                        self.http.return_value.close.assert_called_once_with()
                    else:
                        self.http.return_value.close.assert_not_called()

    def test_lazy_public_sdk_import_and_exact_dependencies(self):
        tree = ast.parse(inspect.getsource(m))
        top_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertEqual([n.module for n in top_imports], ["math", "nayeon.secrets.contracts"])
        loader = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_load_openai_sdk")
        sdk_imports = [n for n in ast.walk(loader) if isinstance(n, ast.ImportFrom)]
        self.assertEqual([(n.module, [a.name for a in n.names]) for n in sdk_imports],
                         [("openai", ["OpenAI", "DefaultHttpxClient"])])
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.Attribute)):
                self.assertNotIn(node.id if isinstance(node, ast.Name) else node.attr,
                                 {"os", "environ", "getenv", "print", "logging", "BaseException"})


class Phase84ScopeGuards(unittest.TestCase):
    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")

    def test_checkpoint_exact_scope_and_frozen_production(self):
        self.assertEqual(self.git("branch", "--show-current").strip(), "nayeon-v1")
        # Keep the protected start in ancestry after local milestone commits.
        self.assertEqual(self.git("merge-base", START, "HEAD").strip(), START)
        self.assertEqual(self.git("cat-file", "-t", TAG).strip(), "tag")
        self.assertEqual(self.git("rev-parse", TAG + "^{commit}").strip(), SEALED)
        for baseline in (START, SEALED):
            tracked = set(self.git("ls-tree", "-r", "--name-only", baseline).splitlines())
            production = {p for p in tracked if p.startswith("nayeon/") or p == "requirements.txt"}
            changed = set(self.git("diff", "--name-only", baseline, "--", "nayeon", "requirements.txt").splitlines())
            untracked = set(self.git("ls-files", "--others", "--exclude-standard", "--", "nayeon").splitlines())
            self.assertEqual(changed | untracked, DELTA)
            actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "nayeon").rglob("*.py")}
            self.assertEqual(actual, {p for p in production if p.endswith(".py")} | NEW)
            for path in production - DELTA:
                with self.subTest(path=path, baseline=baseline):
                    self.assertEqual((ROOT / path).read_text(encoding="utf-8"),
                                     self.git("show", baseline + ":" + path).replace("\r\n", "\n"))

    def test_requirements_exact_pin_and_no_unrelated_change(self):
        current = (ROOT / "requirements.txt").read_bytes()
        active = [line.strip() for line in current.decode("utf-8").splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual([line for line in active if line.lower().startswith("openai")], ["openai==3.26.0"])
        for checkpoint in (START, SEALED):
            baseline = subprocess.check_output(["git", "show", checkpoint + ":requirements.txt"], cwd=ROOT)
            # The sealed pin and every other dependency are now frozen.
            self.assertEqual(current.replace(b"\r\n", b"\n"), baseline.replace(b"\r\n", b"\n"))

    def test_exact_factory_and_validator_consumers(self):
        targets = {"create_openai_client": set(), "OpenAICredentialValidator": set()}
        for path in (ROOT / "nayeon").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name in targets:
                            targets[alias.name].add(path.relative_to(ROOT).as_posix())
        self.assertEqual(targets, {"create_openai_client": {
            "nayeon/brain/providers/openai.py", "nayeon/brain/providers/openai_validation.py"},
            "OpenAICredentialValidator": {
                "nayeon/brain/credential_onboarding_composition.py"}})


if __name__ == "__main__":
    unittest.main()
