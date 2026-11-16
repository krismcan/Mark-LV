"""Read-only P257 source contracts and adversarial in-memory source mutations.

These checks do not compile, load or execute C#, or establish OS custody.
Only Python's standard library is imported. No product module is imported.
"""

import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "tests/p257_private_host_refusal/P257PrivateHostRefusalOwner.cs"
FIXTURE = OWNER.with_name("P257PrivateHostRefusalChecks.cs")
GUARD = "#if !C1_REVIEW_ISOLATED_ASSEMBLY || !P257_EFFECT_FREE_REVIEW || C1_SYNTHETIC_TEST"
ERROR = "#error P257 requires isolated effect-free review without synthetic dispatch"


def code(source):
    # Bounded C# subset checker for this exact review source, not a general parser.
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.S)


def compact(source):
    return re.sub(r"\s+", "", code(source))


def body(source, signature):
    text = code(source)
    if text.count(signature) != 1:
        raise AssertionError("missing or repeated declaration " + signature)
    start = text.index("{", text.index(signature))
    depth = 1
    for index in range(start + 1, len(text)):
        depth += (text[index] == "{") - (text[index] == "}")
        if depth == 0:
            return text[start + 1:index]
    raise AssertionError("unbalanced source")


def check_guard(source):
    directives = [line.strip() for line in code(source).splitlines()
                  if line.lstrip().startswith("#")]
    if directives != [GUARD, ERROR, "#endif"]:
        raise AssertionError("explicit fail-closed compile guard changed")
    if not code(source).lstrip().startswith(GUARD + "\n" + ERROR + "\n#endif"):
        raise AssertionError("compile guard must precede all declarations")


def check_owner(source):
    check_guard(source)
    text = code(source)
    imports = re.findall(r"^using\s+([^;]+);", text, re.M)
    if imports != ["System", "System.Threading"]:
        raise AssertionError("owner import allowlist changed")
    forbidden = r"\b(?:public|protected|delegate|event|extern|unsafe|dynamic|Action|Func|Delegate|DllImport|LibraryImport|Marshal|IntPtr|UIntPtr|byte|CredReadW?|CredWriteW?|CredDeleteW?|SaveOrReplace|DeletePending|ProtectedData|File|Registry|Assembly|Type|Thread|Task|ServiceBase)\b"
    # IDisposable's sole public member is cleanup, with its body pinned below.
    surface = text.replace("public void Dispose()", "void Dispose()")
    if re.search(forbidden, surface) or "=>" in surface or "[" in surface:
        raise AssertionError("new authority, native binding, payload or callback surface")

    prefix = "\n".join((GUARD, ERROR, "#endif", "using System;",
                        "using System.Threading;", "namespace Nayeon.ByokC1", "{"))
    declaration = "internal sealed class P257PrivateHostRefusalOwner : IDisposable"
    if not compact(text).startswith(compact(prefix + declaration)):
        raise AssertionError("exact sealed internal owner required")

    expected = [
        "private readonly object gate = new object();",
        "private readonly CustodyService actualHost = new CustodyService();",
        "private bool disposed;",
        "internal P257PrivateHostRefusalOwner() { }",
    ]
    for name, argument, publication in (
        ("RefuseRequest", "ServiceBoundRequestIdentity claim", ""),
        ("Revoke", "", "actualHost.RevokePendingAdmission();"),
        ("Stop", "", "actualHost.RevokePendingAdmission();"),
        ("Fault", "", "actualHost.FaultPendingAdmission();"),
    ):
        claim = "claim" if name == "RefuseRequest" else "null"
        expected.append(
            "internal CustodyOutcome " + name + "(" + argument + ") {"
            "RejectReentry(); lock (gate) { RequireOpenLifetime(); " + publication +
            "return RefuseUnderGate(" + claim + "); } }")

    expected.extend((
        """private CustodyOutcome RefuseUnderGate(ServiceBoundRequestIdentity claim) {
            CustodyOutcome request = actualHost.RefuseBoundPendingOperation(claim);
            CustodyOutcome terminal = actualHost.RefuseUnreviewedTerminalEffect();
            if (request != CustodyOutcome.Denied || terminal != CustodyOutcome.Denied ||
                actualHost.PendingAdmissionFaulted || actualHost.NativeEffectEnabled ||
                actualHost.AuthenticatedConsentAvailable || actualHost.ProductionReleaseEligible ||
                ServiceGate.LiveEligible() ||
                !CandidateCredentialEffectHold.LegacyEffectEntryDisabled() ||
                !CandidateCredentialEffectHold.NativeMutationAdmissionPending())
                return CustodyOutcome.RecoveryRequired;
            return CustodyOutcome.Denied;
        }""",
        """private void RejectReentry() {
            if (Monitor.IsEntered(gate))
                throw new InvalidOperationException("Recursive review owner entry refused");
        }""",
        """private void RequireOpenLifetime() {
            if (disposed)
                throw new ObjectDisposedException("P257PrivateHostRefusalOwner");
        }""",
        """public void Dispose() {
            RejectReentry(); lock (gate) {
                if (disposed) return;
                disposed = true;
                try {
                    actualHost.RevokePendingAdmission();
                    actualHost.RefuseUnreviewedTerminalEffect();
                } finally { actualHost.Dispose(); }
            }
        }""",
        "internal bool RealKeyAdmissible { get { return false; } }",
        "internal bool ProductionReleaseEligible { get { return false; } }",
        "internal bool OsCustodyEstablished { get { return false; } }",
    ))
    if compact(body(text, declaration)) != compact("\n".join(expected)):
        raise AssertionError("private ownership, refusal ordering or lifetime contract changed")
    if compact(text) != compact(prefix + declaration + "{" + "\n".join(expected) + "}}"):
        raise AssertionError("unexpected sibling, trailing code or preprocessor surface")


class P257SourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = OWNER.read_text(encoding="ascii")
        cls.fixture = FIXTURE.read_text(encoding="ascii")

    def reject_change(self, old, new):
        self.assertIn(old, self.source)
        changed = self.source.replace(old, new, 1)
        self.assertNotEqual(changed, self.source)
        with self.assertRaises(AssertionError):
            check_owner(changed)

    def test_exact_owner_source_contract(self):
        check_owner(self.source)

    def test_review_source_bytes_pinned(self):
        for path, digest in (
            (OWNER, "5228831e890a26e864ae6d5d32ad497b729f63573af92fbf0183d06fd18bb568"),
            (FIXTURE, "3f1fd1489626eb6e01eeca4591480c6768ccfa694492fba78ab27c09714f6d2b"),
        ):
            with self.subTest(path=path.name):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_private_host_has_no_injected_or_returned_alias(self):
        self.assertEqual(self.source.count("new CustodyService()"), 1)
        self.reject_change("internal P257PrivateHostRefusalOwner() { }",
                           "internal P257PrivateHostRefusalOwner(CustodyService host) { }")

    def test_public_permit_rejected(self):
        self.reject_change("private bool disposed;", "private bool disposed; public object Permit;")

    def test_internal_transferable_permit_rejected(self):
        self.reject_change("private bool disposed;", "private bool disposed; internal object Permit;")

    def test_native_binding_rejected(self):
        self.reject_change("private bool disposed;",
                           'private bool disposed; [DllImport("advapi32.dll")] static extern bool CredWriteW();')

    def test_callback_rejected(self):
        self.reject_change("ServiceBoundRequestIdentity claim)",
                           "ServiceBoundRequestIdentity claim, Action callback)")

    def test_custom_delegate_rejected(self):
        self.reject_change("private bool disposed;", "private bool disposed; internal delegate void Effect();")

    def test_secret_payload_rejected(self):
        self.reject_change("ServiceBoundRequestIdentity claim)", "byte[] claim)")

    def test_missing_owner_terminal_refusal_rejected(self):
        self.reject_change("CustodyOutcome terminal = actualHost.RefuseUnreviewedTerminalEffect();",
                           "CustodyOutcome terminal = CustodyOutcome.Denied;")

    def test_terminal_call_moved_out_of_gate_rejected(self):
        self.reject_change("return RefuseUnderGate(claim);",
                           "} return RefuseUnderGate(claim); {")

    def test_lifecycle_early_return_rejected(self):
        self.reject_change("actualHost.RevokePendingAdmission();\n                return RefuseUnderGate(null);",
                           "actualHost.RevokePendingAdmission(); return CustodyOutcome.Denied;")

    def test_missing_fault_publication_rejected(self):
        self.reject_change("actualHost.FaultPendingAdmission();", "actualHost.RevokePendingAdmission();")

    def test_fault_downgrade_rejected(self):
        self.reject_change("return CustodyOutcome.RecoveryRequired;", "return CustodyOutcome.Denied;")

    def test_positive_result_rejected(self):
        self.reject_change("return CustodyOutcome.Denied;", "return CustodyOutcome.StoredUnverified;")

    def test_removed_reentry_barrier_rejected(self):
        self.reject_change("RejectReentry();", "")

    def test_removed_disposal_barrier_rejected(self):
        self.reject_change("RequireOpenLifetime();", "")

    def test_release_and_real_key_holds_cannot_flip(self):
        for name in ("RealKeyAdmissible", "ProductionReleaseEligible", "OsCustodyEstablished"):
            with self.subTest(name=name):
                self.reject_change(name + " { get { return false; } }",
                                   name + " { get { return true; } }")

    def test_compile_guard_each_symbol_and_operator_fail_closed(self):
        for changed in (GUARD.replace("!P257_EFFECT_FREE_REVIEW", "P257_EFFECT_FREE_REVIEW"),
                        GUARD.replace(" || ", " && ", 1),
                        GUARD.replace(" || C1_SYNTHETIC_TEST", ""),
                        "#if false", "#if !C1_REVIEW_ISOLATED_ASSEMBLY"):
            with self.subTest(guard=changed):
                self.reject_change(GUARD, changed)

    def test_missing_error_or_commented_guard_rejected(self):
        self.reject_change(ERROR, "// " + ERROR)
        self.reject_change(GUARD, "// " + GUARD)

    def test_extra_preprocessor_or_sibling_type_rejected(self):
        for addition in ("\n#if OTHER\n#endif\n", "\ninternal class Permit { }\n"):
            with self.subTest(addition=addition):
                with self.assertRaises(AssertionError):
                    check_owner(self.source + addition)

    def test_native_fixture_is_guarded_library_only(self):
        check_guard(self.fixture)
        text = code(self.fixture)
        self.assertNotRegex(text, r"\bMain\s*\(|DllImport|CredWrite|CredDelete|ProtectedData|ServiceBase\.Run")
        self.assertIn("internal static void VerifyAll()", text)
        for witness in ("Pair(signal, true, false);", "Pair(signal, false, false);",
                        "Pair(signal, false, true);", "thread.Join(2500)",
                        "host.TerminalEffectRefusals == 2", "host.DeniedPendingRequestCount == 2",
                        "owner.Stop() == CustodyOutcome.RecoveryRequired",
                        "owner.Revoke() == CustodyOutcome.RecoveryRequired",
                        "recursive.Failure is InvalidOperationException"):
            self.assertIn(witness, text)

    def test_actual_host_dependency_bytes_pinned(self):
        # Exact raw bytes from this checkout, independently inspected at intake.
        pins = {
            "tests/p99_original_native_c1_denial/ServiceGate.cs": "f65ef9f04283b6ca82d42b8d61b6b99b23262de62e248dc575c0cef1b3d96b8d",
            "tests/p99_original_native_c1_denial/ProtectedAcl.cs": "7152a0db081ee9627b0f8e4d0d0230168fbf194752f3180dc884c694199aec61",
            "tests/p99_original_native_c1_denial/CustodyLedger.cs": "93a5eeec6ee6cc4f6fff5146b5709f57cbdd37559d62de0bd4691bf678d5ce0b",
            "native_c1_candidate/CustodyService.cs": "876e3006ba26966be93ba033c97779b6fbb41e8656869a462535b1cf4b12d95e",
            "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs": "1fa108c18f228f83fe4bbde0f682025bd23e864b23ddc24ea4d4f70f27382dd5",
            "native_c1_candidate/ServiceBoundRequestIdentity.cs": "d426d888998d748371ff65ac4af690046498bcb422373a1b30abbf00f85f3d62",
            "native_c1_candidate/NativeJ2ProtectedReadOnlyPreflight.cs": "0578037f88a36d6c12dbd2cc3ac82ad40a36aa4aba3ae9ba32c9901bcafe9d60",
            "native_c1_candidate/CandidateCredentialEffectHold.cs": "0a368d6b06aee10a17e0b035d962019b219efdf251ba109815f4b1a71294447b",
            "native_c1_candidate/IsolatedCandidateContracts.cs": "77d510ad90d8112e9865cd77441112bf66daedf8919598c09c8bd4fc9e7dfb16",
            "native_c1_candidate/CandidateProtectedReadOnlySnapshot.cs": "49185d6f39a450efeda29dbff7dd72cc04a4ff08f0d2e50fc97ab4d9f2ecd961",
        }
        for relative, digest in pins.items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
