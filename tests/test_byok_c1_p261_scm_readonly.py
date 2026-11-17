"""Source-only SCM denial contracts. Stdlib reads only, no product/native imports."""

import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = "native_c1_candidate/P261ScmReadOnlyAdmission.cs"
DRIVER = "tests/p261_scm_readonly/ScmReadOnlyTests.cs"
SELF = "tests/test_byok_c1_p261_scm_readonly.py"
WORKFLOW = ".github/workflows/p261-windows-scm-readonly.yml"
NOTE = "docs/byok-c1-p261-real-service-boundary.md"
BASE = "0e1171cdf6c542c08a087b8cd7f1fd1b86baec83"
BRANCH = "byok-c1-p261-real-service-boundary-20261117"
PINS = {
    NATIVE: "FBBC4AAF4B65D6C4B49DD0EE8B99C391A2E4AC08E1E6454CD10AF26C68804193",
    DRIVER: "F1755BDEBF1B1E44ABA6E47B5A4A4DC9BC36FF39D31A4CCE6C796A3716613A3B",
    "tests/p99_original_native_c1_denial/ServiceGate.cs":
        "F65EF9F04283B6CA82D42B8D61B6B99B23262DE62E248DC575C0CEF1B3D96B8D",
    "tests/p99_original_native_c1_denial/ProtectedAcl.cs":
        "7152A0DB081EE9627B0F8E4D0D0230168FBF194752F3180DC884C694199AEC61",
    "native_c1_candidate/CustodyService.cs":
        "876E3006BA26966BE93BA033C97779B6FBB41E8656869A462535B1CF4B12D95E",
    "native_c1_candidate/ServiceOwnedAdmissionBoundary.cs":
        "1FA108C18F228F83FE4BBDE0F682025BD23E864B23DDC24EA4D4F70F27382DD5",
    "native_c1_candidate/P215WindowsStorePrincipalReadOnlyAdmission.cs":
        "A02A71481939A90C5F6380CCA7C3F078EAC9E75CCDA9603792D8216A6F3467C8",
    "tests/p95_native_custody_preflight/CustodyLedger.cs":
        "93A5EEEC6EE6CC4F6FFF5146B5709F57CBDD37559D62DE0BD4691BF678D5CE0B",
    "tests/p96_native_transaction_negative/PendingCustodyTransaction.cs":
        "D8B8E4C6D5EA5E035B58C6AD73DD758C16640167C804CCF3305969B12BDF81AB",
    "tests/p96_native_transaction_negative/NativeTransactionRaceProof.cs":
        "2AEEAA8BA97396216B32D1894C8B8EA3AF7FACE44FB3562FF1C4DDE5E7DC582F",
    "native_c1_g2_review/P259OwnedPendingTransaction.cs":
        "80F69495177C22C7A0F80B733CC88DE764A48D7D4BE91C0897621408870A41C8",
    "tests/p259_owned_pending_transaction/OwnedPendingTransactionTests.cs":
        "10058CD0D20BCE6C9662C2E863C34BEFB9447E32E132F289A015A50E859F2BF4",
    "tests/test_byok_c1_p259_owned_pending_transaction.py":
        "EA3602A5124F53B7282258FC21893B201828FD6D7B5742F3D195D486058F75C8",
    "tests/test_byok_c1_p260_actual_contention.py":
        "5DA83AC50D8B70F3B036D1C21DD009DF7380C893412D4975C8B01DFB9BE88A0A",
    "docs/byok-c1-p216-service-owned-store-r3-external-decision.md":
        "897C98B85F5EF2CB40D9FCCDC0D0D6FCB727D941CCFD597036E81391B68EAA85",
}
COMPILED = [NATIVE, DRIVER, "tests/p99_original_native_c1_denial/ServiceGate.cs",
            "tests/p99_original_native_c1_denial/ProtectedAcl.cs"]


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def compact(source):
    return re.sub(r"\s+", "", re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.S))


def check_native(source):
    text = compact(source)
    require(source.startswith("// Review-only real SCM observation.") and
            "#if !C1_REVIEW_ISOLATED_ASSEMBLY\n#error P261_REVIEW_ONLY_NONDEPLOYABLE\n#endif"
            in source, "isolated compiler guard required")
    require(re.findall(r"private static extern \w+ (\w+)\(", source) == [
        "OpenSCManagerW", "OpenServiceW", "QueryServiceConfigW", "QueryServiceConfig2W",
        "CloseServiceHandle"], "exact read-only native allowlist required")
    require(re.findall(r'DllImport\("([^"\n]+)"', source) == ["advapi32.dll"] * 5,
            "only read-only SCM imports permitted")
    require("SC_MANAGER_CONNECT=0x0001;" in text and
            "SERVICE_QUERY_CONFIG=0x0001;" in text and
            "manager=OpenSCManagerW(null,null,SC_MANAGER_CONNECT);" in text and
            "service=OpenServiceW(manager,ServiceGate.ServiceName,SERVICE_QUERY_CONFIG);" in text,
            "local exact frozen name and minimum SCM rights required")
    require('stringexpected="NTSERVICE\\\\"+ServiceGate.ServiceName;' in text,
            "virtual account must derive from actual frozen service name")
    for name in ("QualifiedDecisionApproved", "ApprovedServiceOwner", "EffectAllowed",
                 "RealKeyEligible", "CredentialAuthority"):
        require("bool" + name + "{get{returnfalse;}}" in text,
                "unconditional denial property required " + name)
    require("internalstaticP261ScmEvidenceRefuseUntrustedClaim(stringuntrustedAccount,"
            "booluntrustedQualifiedApproval){returnObserve();}" in text,
            "claimants must have no influence on observation or authority")
    for token in (
        "MaximumConfigBytes=8192;", "required>MaximumConfigBytes",
        "size<headerSize||size>MaximumConfigBytes", "account<start",
        "account-start<(ulong)headerSize", "account-start>=(ulong)size",
        "(account&1)!=0", "offset+1<size", "returnlength>0;",
        "SERVICE_CONFIG_SERVICE_SID_INFO=5;", "SERVICE_SID_TYPE_RESTRICTED=3;",
        "sidType=unchecked((uint)Marshal.ReadInt32(sidBuffer));",
        "status=ClassifyConfiguration(matches,sidType.Value);",
        "Environment.OSVersion.Platform!=PlatformID.Win32NT",
        "Environment.OSVersion.Version<newVersion(6,1)",
        "error==ERROR_SERVICE_DOES_NOT_EXIST?P261ScmStatus.Missing",
        "error==ERROR_ACCESS_DENIED?P261ScmStatus.Denied",
        "finally{if(sidBuffer!=IntPtr.Zero)Marshal.FreeHGlobal(sidBuffer);"
        "if(configBuffer!=IntPtr.Zero)Marshal.FreeHGlobal(configBuffer);",
        "!CloseServiceHandle(service)", "!CloseServiceHandle(manager)",
    ):
        require(token in text, "bounded native evidence and cleanup required " + token)
    require("Console." not in text and "PtrToString" not in text,
            "account stays within native comparison, with no logging")
    require(not re.search(r"\b(?:Cred(?:Read|Write|Delete|Enumerate|GetSessionTypes)\w*|"
                          r"CreateService\w*|ChangeService\w*|StartService\w*|"
                          r"ControlService\w*|DeleteService\w*|Impersonate\w*|Registry\w*|"
                          r"Process|Assembly|ServiceBase)\b|\bMain\s*\(", source),
            "SCM mutation, credential, impersonation and deployment APIs forbidden")


def check_workflow(source):
    require("on:\n  pull_request:\n    branches:\n"
            "      - byok-c1-p260-p96-contention-ci-20261117\n" in source and
            "permissions:\n  contents: read\n" in source and
            not re.search(r"^\s*(?:push|pull_request_target|workflow_dispatch|schedule|paths):",
                          source, re.M), "draft PR only with fixed P260 base")
    for token in (
        "$expectedBase = '" + BASE + "'", "$env:REVIEW_BRANCH -cne '" + BRANCH + "'",
        "$env:REVIEW_DRAFT -cne 'true'", "$env:REVIEW_REPO -cne $env:GITHUB_REPOSITORY",
        "$head -cne $env:REVIEW_HEAD", "$env:REVIEW_BASE -cne $expectedBase",
        "git merge-base --is-ancestor $expectedBase HEAD", "git diff --name-only $expectedBase HEAD",
        "git diff --diff-filter=ACDMRTUXB --name-status $expectedBase HEAD",
        r"$_ -cnotmatch '^A\t'", "persist-credentials: false",
        "ref: ${{ github.event.pull_request.head.sha }}", "runs-on: windows-latest",
        "- arch: x64\n            bits: 64", "- arch: x86\n            bits: 32",
        "$rawExit = $LASTEXITCODE", "$rawExit = $process.ExitCode", "$null = $process.Handle",
        "$process.WaitForExit(60000)", "Stop-Process -Id $process.Id",
        "$null -eq $rawExit -or $rawExit -ne 0", "if: always()",
        "([regex]::Matches($guardText, 'error CS1029')).Count -ne 2",
        "P261_REAL_SCM_MISSING_DENIAL=PASS", "P261_SERVICE_STORE_AUTHORITY=REJECT",
        "P261_PRODUCTION_RELEASE=HOLD", "P261_QUALIFIED_APPROVALS=0/7",
    ):
        require(token in source, "source-bound Windows receipts required " + token)
    expected_pins = dict(PINS)
    expected_pins[SELF] = hashlib.sha256((ROOT / SELF).read_bytes()).hexdigest().upper()
    require(dict(re.findall(r"'([^'\n]+)' = '([A-F0-9]{64})'", source)) == expected_pins,
            "exact native and preserved source pins required")
    inventory = re.search(r"\$sourcePaths = @\((.*?)\)\n", source, re.S)
    require(inventory is not None and re.findall(r"'([^']+)'", inventory[1]) == COMPILED and
            "$sources = @($sourcePaths | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })"
            in source, "four exact compiler inputs require absolute native paths")
    require(source.count("@sources *>") == 2 and
            "/define:C1_REVIEW_ISOLATED_ASSEMBLY" in source,
            "both guarded and positive compiler paths required")
    require(re.findall(r"uses: (\S+)", source) == [
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"],
        "pinned review actions required")
    require(source.endswith("          path: |\n"
                            "            ${{ runner.temp }}/p261-${{ matrix.arch }}/*.log\n"
                            "            ${{ runner.temp }}/p261-${{ matrix.arch }}/*.exit\n"
                            "            ${{ runner.temp }}/p261-${{ matrix.arch }}/*.json\n"
                            "          if-no-files-found: error\n"),
            "text-only exact artifact whitelist required")
    require(not re.search(r"ExecutionPolicy|\bBypass\b|EncodedCommand|Invoke-Expression|"
                          r"Add-Type|CredRead|CredWrite|CredDelete|secrets\.|continue-on-error|"
                          r"exit\s+0|git\s+(?:push|commit)|Unblock-File|Set-MpPreference|CiTool",
                          source, re.I), "policy bypass and live authority forbidden")


class P261ScmReadOnlySourceTests(unittest.TestCase):
    def test_frozen_sources_before_and_after(self):
        for path, expected in PINS.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(),
                                 expected)

    def test_service_identity_mismatch_is_architecture_blocker(self):
        gate = (ROOT / COMPILED[2]).read_text(encoding="utf-8")
        service = (ROOT / "native_c1_candidate/CustodyService.cs").read_text(encoding="utf-8")
        proposal = (ROOT / "docs/byok-c1-p216-service-owned-store-r3-external-decision.md").read_text(
            encoding="utf-8")
        self.assertIn('const string ServiceName = "NayeonV1ByokCustody";', gate)
        self.assertIn("this.ServiceName = ServiceGate.ServiceName;", service)
        self.assertIn("NT SERVICE\\NayeonByokCustody", proposal)
        self.assertNotEqual("NT SERVICE\\NayeonByokCustody",
                            "NT SERVICE\\NayeonV1ByokCustody")
        self.assertIn("bool accountIsLocalSystem,", gate)
        self.assertIn("if (!accountIsLocalSystem ||", gate)
        self.assertIn("WindowsIdentity.GetCurrent()", gate)
        self.assertIn("WellKnownSidType.LocalSystemSid", gate)
        self.assertIn("EligibleForService(path,ExpectedImage(),system,", gate)
        self.assertIn("dedicated least-privilege Windows virtual service account", proposal)
        self.assertIn("with restricted service SID", proposal)
        self.assertIn("Why avoid LocalSystem as the default", proposal)
        note = (ROOT / NOTE).read_text(encoding="utf-8")
        self.assertIn("P261-IDENTITY / HIGH / OPEN / HOLD", note)
        self.assertIn("P261-LOCAL_SYSTEM_GATE / HIGH / OPEN / HOLD", note)

    def test_read_only_native_contract(self):
        check_native((ROOT / NATIVE).read_text(encoding="utf-8"))

    def test_native_harness_invokes_real_observer_and_holds_on_existing_service(self):
        source = compact((ROOT / DRIVER).read_text(encoding="utf-8"))
        for token in ("ParserTests();", "P261ScmReadOnlyAdmission.Observe();", "Denied(actual);",
                      "P261ScmReadOnlyAdmission.RefuseUntrustedClaim(claimant,approval);",
                      "Denied(claimed);", "claimed.Status==P261ScmStatus.Missing",
                      "if(!allMissing){Console.WriteLine(\"P261_ENGINEERING=HOLD\");return2;}",
                      '"NTSERVICE\\\\NayeonByokCustody"', '"LocalSystem"',
                      "header==(IntPtr.Size==8?64:36)", "finally{Marshal.FreeHGlobal(buffer);}"):
            self.assertIn(token, source)

    def test_windows_workflow(self):
        check_workflow((ROOT / WORKFLOW).read_text(encoding="utf-8"))

    def test_native_mutations_rejected(self):
        source = (ROOT / NATIVE).read_text(encoding="utf-8")
        for before, after in (
            ("SC_MANAGER_CONNECT = 0x0001", "SC_MANAGER_CONNECT = 0xF003F"),
            ("ServiceGate.ServiceName,", '"NayeonByokCustody",'),
            ("bool EffectAllowed { get { return false; } }", "bool EffectAllowed { get { return true; } }"),
            ("account - start >= (ulong)size", "false"),
            ("SERVICE_SID_TYPE_RESTRICTED = 3", "SERVICE_SID_TYPE_RESTRICTED = 1"),
            ("Marshal.FreeHGlobal(configBuffer);", ""),
            ("OpenServiceW", "CreateServiceW"),
            ("#error P261_REVIEW_ONLY_NONDEPLOYABLE", ""),
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_native(source.replace(before, after))

    def test_workflow_mutations_rejected(self):
        source = (ROOT / WORKFLOW).read_text(encoding="utf-8")
        for before, after in (
            ("  pull_request:", "  pull_request_target:"),
            ("contents: read", "contents: write"),
            (BASE, "0" * 40),
            (PINS[NATIVE], "0" * 64),
            ("$rawExit = $process.ExitCode", "$rawExit = 0"),
            ("$env:REVIEW_DRAFT -cne 'true'", "$false"),
            ("(Resolve-Path -LiteralPath $_).Path", "$_"),
            ("/*.log", "/*.exe"),
            ("$process = Start-Process", "Set-ExecutionPolicy Bypass\n          $process = Start-Process"),
        ):
            with self.subTest(before=before):
                self.assertIn(before, source)
                with self.assertRaises(AssertionError):
                    check_workflow(source.replace(before, after))


if __name__ == "__main__":
    unittest.main()
