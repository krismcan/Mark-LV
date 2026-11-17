"""Bounded lexical contracts and mutation negatives, separate from C# runtime proof.

Reads source only. No product imports, C# loading, native APIs or network.
"""

import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "native_c1_g2_review/P259OwnedPendingTransaction.cs"
DRIVER = ROOT / "tests/p259_owned_pending_transaction/OwnedPendingTransactionTests.cs"
GUARD = "#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST"
ERROR = "#error P259 requires isolated synthetic review and is NONDEPLOYABLE"
FROZEN = {
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs":
        "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs":
        "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
    "native_c1_candidate/CustodyService.cs":
        "876E3006BA26966BE93BA033C97779B6FBB41E8656869A462535B1CF4B12D95E",
    "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs":
        "1FA108C18F228F83FE4BBDE0F682025BD23E864B23DDC24EA4D4F70F27382DD5",
}


def code(source):
    # This checker supports this source's bounded C# subset, not arbitrary C#.
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.S)


def compact(source):
    return re.sub(r"\s+", "", code(source))


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def body(source, signature):
    require(source.count(signature) == 1, "unique method declaration")
    start = source.index("{", source.index(signature))
    depth = 1
    for index in range(start + 1, len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            return source[start + 1:index]
    raise AssertionError("balanced source required")


def check_guard(source):
    directives = [line.strip() for line in code(source).splitlines()
                  if line.lstrip().startswith("#")]
    require(directives == [GUARD, ERROR, "#endif"], "two-flag compile guard")
    require(code(source).lstrip().startswith(GUARD + "\n" + ERROR + "\n#endif"),
            "compile guard precedes declarations")


def check_owner(source):
    check_guard(source)
    source = code(source)
    text = compact(source)
    require(re.findall(r"^using\s+([^;]+);", source, re.M) == ["System", "System.Threading"],
            "owner import allowlist")
    forbidden = (r"\b(?:public|protected|delegate|event|Action|Func|Delegate|dynamic|extern|"
                 r"unsafe|DllImport|LibraryImport|Marshal|IntPtr|UIntPtr|byte|IProtectedPendingState|"
                 r"SaveOrReplace|DeletePending|CustodyService|PendingCustodyTransaction|File|"
                 r"Registry|Console|Assembly|Activator|Task|ServiceBase)\b")
    require(not re.search(forbidden, source) and "=>" not in source and "[" not in source,
            "external authority or callback surface")
    require(text.count("privatereadonlySemaphoreSlimgate=newSemaphoreSlim(1,1);") == 1 and
            source.count("SemaphoreSlim") == 2 and "Monitor" not in source and
            not re.search(r"\block\s*\(", source), "one private nonreentrant gate")
    require("privatereadonlyFakeOperationoperation;" in text and
            "internalOutcomeApply()" in text and
            "internalPublicationPublish(Lifecyclesignal)" in text,
            "bound request and closed entrypoint signatures")
    require("internalenumOutcome{Denied,RecoveryRequired}" in text and
            "internalenumPublication{ZeroFakeEffects,TooLatePossibleEffect,RecoveryRequired}" in text,
            "no stored success or approval outcome")

    enter = compact(body(source, "private bool EnterGate()"))
    require("if(Volatile.Read(refownerThread)==current){consumed=true;recovery=true;"
            "faulted=true;returnfalse;}" in enter, "reentry poisons request under owned gate")
    require("catch(ThreadInterruptedException){interrupted=true;}" in enter and
            "if(interrupted){consumed=true;recovery=true;faulted=true;ExitGate();returnfalse;}"
            in enter, "interrupted admission must finish fault publication")
    require(compact(body(source, "private void ExitGate()")) ==
            "Volatile.Write(refownerThread,0);gate.Release();", "single gate release")
    require(source.count("gate.Wait()") == 1 and source.count("gate.Release()") == 1,
            "private gate ownership")

    for signature, result in (("internal Outcome Apply()", "Outcome.RecoveryRequired"),
                              ("internal Publication Publish(Lifecycle signal)",
                               "Publication.RecoveryRequired")):
        method = body(source, signature)
        critical = body(method, "try")
        method_text = compact(method)
        require("if(!EnterGate())return" + result + ";try{" in method_text,
                "entry must acquire gate before work")
        require(method_text.endswith("finally{ExitGate();}") and
                "ExitGate" not in critical and "gate." not in critical,
                "gate release must follow entire critical section")

    apply = body(source, "internal Outcome Apply()")
    critical = compact(body(apply, "try"))
    require(source.count("DispatchFixedIntegerEffect();") == 1 and
            critical.count("DispatchFixedIntegerEffect();") == 1,
            "fixed dispatch stays inside acquired gate")
    require("consumed=true;" in critical and
            critical.index("consumed=true;") < critical.index("DispatchFixedIntegerEffect();"),
            "one-use reservation precedes dispatch")
    require("recovery=true;" in critical and
            critical.index("recovery=true;") < critical.index("DispatchFixedIntegerEffect();"),
            "sticky recovery precedes dispatch")
    require(compact(body(apply, "catch (Exception)")) ==
            "faulted=true;recovery=true;returnOutcome.RecoveryRequired;",
            "failed work remains recovery required")
    dispatch = compact(body(source, "private void DispatchFixedIntegerEffect()"))
    for statement in ("dispatchOrder=++order;", "++attempts;",
                      "caseFakeOperation.Save:marker=17;++saves;break;",
                      "caseFakeOperation.Replace:marker=23;++replacements;break;",
                      "caseFakeOperation.Delete:marker=0;++deletes;break;"):
        require(statement in dispatch, "three fixed integer operation classes")
    publish = compact(body(body(source, "internal Publication Publish(Lifecycle signal)"), "try"))
    require(publish.startswith("consumed=true;switch(signal)") and
            "caseLifecycle.Stop:stopped=true;revoked=true;break;" in publish and
            "caseLifecycle.Fault:faulted=true;recovery=true;break;" in publish and
            "if(attempts!=0){recovery=true;returnPublication.TooLatePossibleEffect;}" in publish,
            "atomic lifecycle publication preserves possible-effect evidence")


class P259SourceContractTests(unittest.TestCase):
    def test_actual_owner_contract(self):
        check_owner(OWNER.read_text(encoding="utf-8"))

    def test_driver_requires_both_compile_flags(self):
        check_guard(DRIVER.read_text(encoding="utf-8"))

    def test_frozen_originals_and_denial_only_candidate_bytes(self):
        for path, expected in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(),
                                 expected)

    def test_in_memory_boundary_mutations_rejected_for_specific_reason(self):
        original = OWNER.read_text(encoding="utf-8")
        mutations = (
            (GUARD, GUARD.replace("||", "&&"), "two-flag compile guard"),
            ("SemaphoreSlim(1, 1)", "SemaphoreSlim(2, 2)", "one private nonreentrant gate"),
            ("Volatile.Read(ref ownerThread) == current", "false", "reentry poisons request"),
            ("if (interrupted)", "if (false)", "interrupted admission"),
            ("internal Outcome Apply()", "internal Outcome Apply(bool approved)",
             "closed entrypoint signatures"),
            ("Denied, RecoveryRequired }", "Denied, RecoveryRequired, Stored }",
             "no stored success"),
            ("                consumed = true;\n                if (recovery || faulted)",
             "                if (recovery || faulted)", "one-use reservation"),
            ("                recovery = true;\n                if (dispatchEntered",
             "                if (dispatchEntered", "sticky recovery"),
            ("                DispatchFixedIntegerEffect();",
             "                ExitGate(); DispatchFixedIntegerEffect();", "gate release"),
            ("marker = 23;", "marker = 17;", "three fixed integer"),
            ("if (attempts != 0)", "if (false)", "atomic lifecycle publication"),
            ("using System.Threading;", "using System.Threading;\nusing System.IO;",
             "import allowlist"),
            ("        internal Outcome Apply()", "        internal Action Effect;\n"
             "        internal Outcome Apply()", "external authority or callback"),
        )
        for before, after, reason in mutations:
            with self.subTest(reason=reason):
                self.assertEqual(original.count(before), 1, "mutation must hit its intended site")
                with self.assertRaisesRegex(AssertionError, reason):
                    check_owner(original.replace(before, after))


if __name__ == "__main__":
    unittest.main()
