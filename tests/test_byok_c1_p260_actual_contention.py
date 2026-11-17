"""Source-only P260 contracts and in-memory negative mutations.

Only stdlib source reads. No product imports, native loading, processes or keys.
These bounded lexical checks supplement the Windows compiler/thread evidence.
"""

import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = "tests/p259_owned_pending_transaction/OwnedPendingTransactionTests.cs"
WORKFLOW = ".github/workflows/p260-windows-p96-actual-contention.yml"
BASE = "f9833383177e4c76f7997ad6041434c52c401c05"
PINS = {
    "tests/p95_native_custody_preflight/CustodyLedger.cs":
        "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs":
        "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs":
        "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
    "native_c1_g2_review/P259OwnedPendingTransaction.cs":
        "80F69495177C22C7A0F80B733CC88DE764A48D7D4BE91C0897621408870A41C8",
    DRIVER: "10058CD0D20BCE6C9662C2E863C34BEFB9447E32E132F289A015A50E859F2BF4",
    "native_c1_candidate/CustodyService.cs":
        "876E3006BA26966BE93BA033C97779B6FBB41E8656869A462535B1CF4B12D95E",
    "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs":
        "1FA108C18F228F83FE4BBDE0F682025BD23E864B23DDC24EA4D4F70F27382DD5",
}
MAIN_SHA256 = "77036FF2A79690F014BD8C3C1399E342C9B3CBAD3EBDD1196D6B35DEC4AFD75F"


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def code(source):
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.S)


def compact(source):
    return re.sub(r"\s+", "", code(source))


def body(source, signature):
    # Bounded to the checked-in C# subset, whose string literals contain no braces.
    require(source.count(signature) == 1, "unique method declaration")
    start = source.index("{", source.index(signature))
    depth = 1
    for index in range(start + 1, len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            return source[start + 1:index]
    raise AssertionError("balanced method required")


def check_contention(source):
    wait = compact(body(source, "internal void WaitForBlockedGate()"))
    require(wait == compact('''
        var timer = System.Diagnostics.Stopwatch.StartNew();
        while ((thread.ThreadState & ThreadState.WaitSleepJoin) == 0)
        {
            Need(thread.IsAlive && timer.ElapsedMilliseconds < 2000,
                "contender did not block on owned gate");
            Thread.Yield();
        }
    '''), "actual bounded worker WaitSleepJoin required")
    effect = compact(body(source, "private static void EffectFirst("))
    require("using(varpublicationReturned=newManualResetEventSlim())" in effect,
            "independent publication return flag required")
    require('publisher=newWorker(()=>{Publicationresult=owner.Publish(signal);'
            'publicationReturned.Set();Need(result==Publication.TooLatePossibleEffect,'
            '"publicationfalselyclaimedzeroeffects");SnapshotatReturn=owner.Read();' in effect,
            "return flag immediately follows Publish before assertions and Read")
    require('Need(entered.Wait(2000),"effectdidnotenterownedgate");publisher=' in effect,
            "dispatch pause precedes publisher start")
    require('Need(waiting.Wait(2000),"publicationdidnotcontend");'
            'publisher.WaitForBlockedGate();Need((int)typeof(P259OwnedPendingTransaction)'
            '.GetField("attempts",PrivateInstance).GetValue(owner)==0,'
            '"dispatchpauseoccurredtoolate");Need(!publicationReturned.IsSet,'
            '"publicationreturnedwhiledispatchownedgate");Need(!completed.IsSet,'
            '"publicationobservationcompletedwhiledispatchownedgate");}finally{release.Set();'
            in effect, "blocked publisher and no return asserted before release")
    require(effect.count("release.Set();") == 1 and
            'SetProbe(owner,"dispatchEntered",entered);'
            'SetProbe(owner,"dispatchContinue",release);'
            'SetProbe(owner,"publicationWaiting",waiting);' in effect,
            "private dispatch pause remains connected")
    require('atReturn.PublicationOrder>atReturn.DispatchOrder' in effect and
            'Need(publicationReturned.IsSet&&completed.IsSet,"publicationcompletionmissing");'
            in effect, "post-release return and ordering evidence required")
    require(compact(body(source, "internal void InterruptBlockedGateWait()")) ==
            "WaitForBlockedGate();thread.Interrupt();", "interruption still waits for gate")
    main = source[source.index("public static int Main()"):]
    require(hashlib.sha256(main.encode("utf-8")).hexdigest().upper() == MAIN_SHA256,
            "all original 49 case registrations and exit checks preserved")


def check_workflow(source):
    require("on:\n  pull_request:\n    branches:\n"
            "      - byok-c1-p259-p96-owned-effect-ordering-20261117\n\npermissions:\n"
            "  contents: read\n" in source and
            not re.search(r"^\s*(?:push|pull_request_target|workflow_dispatch|schedule|paths):",
                          source, re.M), "review-only PR base and read-only permission")
    require("runs-on: windows-latest" in source and
            "fail-fast: false" in source and
            "- arch: x64\n            bits: 64" in source and
            "- arch: x86\n            bits: 32" in source,
            "both Windows architectures required")
    require("$expectedBase = '" + BASE + "'" in source and
            "$head -cne $env:REVIEW_HEAD" in source and
            "$env:REVIEW_BASE -cne $expectedBase" in source and
            "git merge-base --is-ancestor $expectedBase HEAD" in source and
            "git diff --name-only $expectedBase HEAD" in source and
            "@(Compare-Object ($expected | Sort-Object) ($actual | Sort-Object)).Count -ne 0"
            in source, "exact source topology and scope required")
    require(re.findall(r"uses: (\S+)", source) == [
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ] and "persist-credentials: false" in source and
        "ref: ${{ github.event.pull_request.head.sha }}" in source,
        "pinned review actions and exact head required")
    pins = dict(re.findall(r"'([^'\n]+)' = '([A-F0-9]{64})'", source))
    require(pins == PINS and
            "(Get-FileHash -LiteralPath $pin.Key -Algorithm SHA256).Hash -cne $pin.Value"
            in source, "exact raw source pins required")
    original = re.search(r"\$original = @\((.*?)\)\n", source, re.S)
    comparator = re.search(r"\$comparator = @\((.*?)\)\n", source, re.S)
    require(original is not None and comparator is not None and
            re.findall(r"'([^']+)'", original[1]) == list(PINS)[:3] and
            re.findall(r"'([^']+)'", comparator[1]) == [list(PINS)[3], DRIVER],
            "only original fake proof and isolated comparator compiled")
    for statement in (
        "@('none', 'isolated-only', 'synthetic-only')",
        "([regex]::Matches($guardText, 'error CS1029')).Count -ne 2",
        "/define:C1_REVIEW_ISOLATED_ASSEMBLY,C1_SYNTHETIC_TEST",
        "@('P96-original', 'P259')",
        "$rawExit = $LASTEXITCODE",
        "$rawExit = $process.ExitCode",
        "if ($null -eq $rawExit -or $rawExit -ne 0)",
        "$process.WaitForExit(60000)",
        "Stop-Process -Id $process.Id",
        "P259_PASSED=49", "P259_FAILED=0", "P259_POINTER_BITS=",
        "P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=15",
        "P96_NATIVE_ACTUAL_COORDINATOR_TESTS_FAILED=0",
        "P96_LEGACY_POST_CHECK_REVOCATION_RACE=REPRODUCED_IN_FAKE_ONLY",
        "P96_REAL_NATIVE_EFFECTS=NONE", "P96_SECURITY_FINDING=OPEN",
        "P96_C1_PRODUCTION_RELEASE=HOLD",
        "ORIGINAL_FAILURES_UNWAIVED; SECURITY_HOLD; REAL_KEY_NO_GO; PRODUCTION_RELEASE_HOLD",
        "if: always()",
    ):
        require(statement in source, "native exits, receipts and holds required")
    require(source.endswith(
        "        with:\n"
        "          name: p260-review-only-${{ matrix.arch }}\n"
        "          path: |\n"
        "            ${{ runner.temp }}/p260-${{ matrix.arch }}/*.log\n"
        "            ${{ runner.temp }}/p260-${{ matrix.arch }}/*.exit\n"
        "            ${{ runner.temp }}/p260-${{ matrix.arch }}/*.json\n"
        "          if-no-files-found: error\n"),
        "artifact whitelist requires only log, exit and json globs")
    require(not re.search(r"ExecutionPolicy|\bBypass\b|EncodedCommand|Invoke-Expression|"
                          r"Add-Type|DllImport|CredWrite|CredRead|CredDelete|secrets\.|"
                          r"continue-on-error|exit\s+0|git\s+(?:push|commit)|"
                          r"Set-MpPreference|CiTool|Unblock-File", source, re.I),
            "policy bypass, credentials or release authority forbidden")


class P260ActualContentionSourceTests(unittest.TestCase):
    def test_actual_thread_wait_and_immediate_return_flag(self):
        check_contention((ROOT / DRIVER).read_text(encoding="utf-8"))

    def test_exact_source_pins(self):
        for path, expected in PINS.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(),
                                 expected)

    def test_review_only_windows_workflow(self):
        check_workflow((ROOT / WORKFLOW).read_text(encoding="utf-8"))

    def test_contention_mutations_fail_for_specific_reasons(self):
        source = (ROOT / DRIVER).read_text(encoding="utf-8")
        mutations = (
            ("ThreadState.WaitSleepJoin", "ThreadState.Running", "actual bounded worker"),
            ("thread.IsAlive && timer.ElapsedMilliseconds < 2000", "true",
             "actual bounded worker"),
            ("publisher.WaitForBlockedGate();", "", "blocked publisher and no return"),
            ("publicationReturned.Set();", "", "return flag immediately"),
            ("publicationReturned.Set();", "Snapshot hidden = owner.Read();\n"
             "                    publicationReturned.Set();", "return flag immediately"),
            ("!publicationReturned.IsSet", "!completed.IsSet", "blocked publisher and no return"),
            ("SetProbe(owner, \"dispatchContinue\", release);", "",
             "private dispatch pause remains connected"),
            ("passed == 49", "passed == 48", "all original 49"),
        )
        self.check_mutations(source, mutations, check_contention)

    def test_workflow_mutations_fail_for_specific_reasons(self):
        source = (ROOT / WORKFLOW).read_text(encoding="utf-8")
        mutations = (
            ("  pull_request:", "  pull_request_target:", "review-only PR"),
            ("contents: read", "contents: write", "review-only PR"),
            ("- arch: x86", "- arch: arm64", "both Windows architectures"),
            (BASE, "0" * 40, "exact source topology"),
            (PINS[DRIVER], "0" * 64, "exact raw source pins"),
            ("$rawExit = $process.ExitCode", "$rawExit = 0", "native exits"),
            ("P259_PASSED=49", "P259_PASSED=48", "native exits"),
            ("P96_SECURITY_FINDING=OPEN", "P96_SECURITY_FINDING=CLOSED", "native exits"),
            ("$original = @(", "$original = @('native_c1_candidate/CustodyService.cs',",
             "only original fake proof"),
            ("$process = Start-Process", "Set-ExecutionPolicy Bypass\n          "
             "$process = Start-Process", "policy bypass"),
            ("path: |\n"
             "            ${{ runner.temp }}/p260-${{ matrix.arch }}/*.log\n"
             "            ${{ runner.temp }}/p260-${{ matrix.arch }}/*.exit\n"
             "            ${{ runner.temp }}/p260-${{ matrix.arch }}/*.json",
             "path: ${{ runner.temp }}/p260-${{ matrix.arch }}", "artifact whitelist"),
            ("/*.log", "/*", "artifact whitelist"),
            ("/*.log", "/*.exe", "artifact whitelist"),
            ("/*.log", "/*.dll", "artifact whitelist"),
        )
        self.check_mutations(source, mutations, check_workflow)

    def check_mutations(self, source, mutations, checker):
        for before, after, reason in mutations:
            with self.subTest(reason=reason):
                self.assertEqual(source.count(before), 1, "unique mutation site required")
                with self.assertRaisesRegex(AssertionError, reason):
                    checker(source.replace(before, after))


if __name__ == "__main__":
    unittest.main()
