"""P279 deterministic source-only witnesses; never import or execute product code.

These checks are bounded text/hash review, not Windows runtime verification or
production admission. P216 historical test02/test06 remain red and unwaived;
qualified G0/R3, SEC03/04 and 0/7 approvals remain unresolved, with 0/3 full
native product regressions. Production HOLD; real keys NO-GO. The future P279
CI workflow is deliberately not a prerequisite for this authoring checkpoint.
"""

import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "native_c1_candidate/P279RunningServiceTokenReadOnly.cs"
HARNESS = "tests/p279_service_runtime/RuntimeServiceTokenTests.cs"
FROZEN = {
    "native_c1_candidate/P261ScmReadOnlyAdmission.cs":
        "FBBC4AAF4B65D6C4B49DD0EE8B99C391A2E4AC08E1E6454CD10AF26C68804193",
    "tests/p261_scm_readonly/ScmReadOnlyTests.cs":
        "F1755BDEBF1B1E44ABA6E47B5A4A4DC9BC36FF39D31A4CCE6C796A3716613A3B",
    "tests/p99_original_native_c1_denial/ServiceGate.cs":
        "F65EF9F04283B6CA82D42B8D61B6B99B23262DE62E248DC575C0CEF1B3D96B8D",
    "tests/p99_original_native_c1_denial/ProtectedAcl.cs":
        "7152A0DB081EE9627B0F8E4D0D0230168FBF194752F3180DC884C694199AEC61",
    "native_c1_candidate/CustodyService.cs":
        "876E3006BA26966BE93BA033C97779B6FBB41E8656869A462535B1CF4B12D95E",
    "native_c1_candidate/P215WindowsStorePrincipalReadOnlyAdmission.cs":
        "A02A71481939A90C5F6380CCA7C3F078EAC9E75CCDA9603792D8216A6F3467C8",
    "tests/test_p216_service_store_decision_inventory.py":
        "FF077BB4959A0EB5D33D95397649C772F395FE89143C5A8643589E5CB9B4A1F5",
    "nayeon/secrets/windows_credential.py":
        "9FFB136A73E4277B966FAE025A3962123433745B6BA8907AB3B8C4137F4A21B3",
}
CANDIDATE = {
    SOURCE: "6CB05A5DB96D83D61387CE90237358C7DF5C10ED7FBFFFB146D4C1E50A8602BB",
    HARNESS: "4CDCB93EC91DD9EF343C1CA5579FEA0272F8AAC88EFFDC99F9CC74BB8889ECA9",
}
AUTHORITY = (
    "QualifiedSecurityDecisionApproved", "ApprovedServicePrincipal",
    "ProtectedCredentialOwner", "TrustedConsent", "NativeCredentialEffectAllowed",
    "RealKeyEligible", "ProductionReleaseEligible",
)
OBSERVATIONS = (
    "ConfigObserved", "ServiceOpened", "ProcessOpened", "TokenOpened",
    "TokenUserMatchesServiceSid", "RuntimeStatusRechecked",
)


def _code(text):
    # Preserve C# literals so comments cannot satisfy a required code fragment.
    pattern = r'@"(?:""|[^"])*"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\r\n]*|/\*[\s\S]*?\*/'
    return re.sub(pattern, lambda m: "" if m[0].startswith(("//", "/*")) else m[0], text)


def _compact(text):
    return re.sub(r"\s+", "", _code(text))


def _need(condition, reason):
    if not condition:
        raise AssertionError(reason)


def _has(text, *fragments):
    for fragment in fragments:
        _need(_compact(fragment) in _compact(text), "missing source contract: " + fragment)


def _body(text, signature):
    # Bounded brace extraction for these pinned sources, not a C# parser.
    text = _code(text)
    start = text.find(signature)
    _need(start >= 0, "missing signature: " + signature)
    start = text.index("{", start)
    depth = 1
    for end in range(start + 1, len(text)):
        depth += (text[end] == "{") - (text[end] == "}")
        if depth == 0:
            return text[start + 1:end]
    raise AssertionError("unclosed source block")


def _guards_and_native(source, harness):
    directives = ["#if !C1_REVIEW_ISOLATED_ASSEMBLY",
                  "#error P279_RUNTIME_TOKEN_REVIEW_ONLY_NONDEPLOYABLE", "#endif"]
    for text in (source, harness):
        _need([line.strip() for line in _code(text).splitlines()
               if line.strip().startswith("#")] == directives, "isolated review guard")
        _need(_code(text).lstrip().startswith("\n".join(directives)), "guard precedes code")
    imports = re.findall(
        r'\[DllImport\("([^"]+)"[^\]]*\)\]\s*'
        r'(?:\[return:[^\]]+\]\s*)?private static extern \w+ (\w+)\(', _code(source))
    expected = [("advapi32.dll", name) for name in (
        "OpenSCManagerW", "OpenServiceW", "QueryServiceStatusEx", "CloseServiceHandle")]
    expected += [("kernel32.dll", "OpenProcess"), ("advapi32.dll", "OpenProcessToken"),
                 ("kernel32.dll", "CloseHandle"), ("advapi32.dll", "LookupAccountNameW")]
    _need(imports == expected and _code(source).count("[DllImport(") == 8,
          "exact eight native declarations")
    _need("DllImport" not in _code(harness), "harness has no native declarations")
    for text, allowed in ((source, {"System", "System.Runtime.InteropServices",
                                   "System.Security.Principal"}),
                          (harness, {"System", "System.Reflection",
                                     "System.Runtime.InteropServices", "Nayeon.ByokC1"})):
        _need(set(re.findall(r"^using ([\w.]+);", text, re.M)) == allowed, "bounded namespaces")
        _need(not re.search(
            r"\b(?:Cred(?:Read|Write|Delete|Enumerate|Rename|Protect|Unprotect)\w*|"
            r"CreateService\w*|ChangeServiceConfig\w*|StartService\w*|ControlService\w*|"
            r"DeleteService\w*|HttpClient|WebRequest|Socket|TcpClient|UdpClient|"
            r"Impersonate\w*|RevertToSelf|LogonUser\w*|AdjustTokenPrivileges|"
            r"DuplicateToken\w*|ShellExecute\w*|LoadLibrary\w*|GetProcAddress|"
            r"NativeLibrary|CreateProcess\w*)\b|System\.(?:Net|Diagnostics)|"
            r"Process\.Start|Assembly\.Load|WindowsIdentity\.GetCurrent|runas|https?://",
            _code(text), re.I), "credential/network/provider/elevation/impersonation surface")


def _status(source):
    _has(source, "StatusBytes = 36", "[StructLayout(LayoutKind.Sequential, Pack = 4)]")
    fields = _body(source, "internal struct ServiceStatusProcess")
    _need(_compact(fields) == _compact("internal uint ServiceType, CurrentState, ControlsAccepted, "
          "Win32ExitCode, ServiceSpecificExitCode, CheckPoint, WaitHint, ProcessId, ServiceFlags;"),
          "nine DWORD status fields")
    _has(_body(source, "internal static bool TryParseStatus("),
         "value = new ServiceStatusProcess();",
         "if (buffer == IntPtr.Zero || size != StatusBytes || "
         "Marshal.SizeOf(typeof(ServiceStatusProcess)) != StatusBytes) return false;",
         "Marshal.PtrToStructure(buffer, typeof(ServiceStatusProcess))")
    _need(_compact(_body(source, "internal static bool CanQueryProcess(")) == _compact(
        "return value.ServiceType == 0x10 && value.CurrentState == 4 && value.ProcessId != 0;"),
        "own-process running nonzero PID only")
    _has(_body(source, "internal static bool SameRunningProcess("),
         "return CanQueryProcess(first) && CanQueryProcess(second) && "
         "first.ServiceType == second.ServiceType && first.CurrentState == second.CurrentState && "
         "first.ProcessId == second.ProcessId;")
    _has(_body(source, "private static bool ReadStatus("),
         "return QueryServiceStatusEx(service, 0, buffer, StatusBytes, out needed) && "
         "TryParseStatus(buffer, StatusBytes, out value);")


def _configuration(source):
    observe = _body(source, "internal static P279RuntimeTokenEvidence Observe()")
    # Constants live outside Observe; ordering is checked on the executable body.
    _has(source, "SC_MANAGER_CONNECT = 1, SERVICE_QUERY_STATUS = 4",
         "PROCESS_QUERY_LIMITED_INFORMATION = 0x1000, TOKEN_QUERY = 8")
    ordered = ["P261ScmEvidence prior = P261ScmReadOnlyAdmission.Observe();",
               "if (prior.Status == P261ScmStatus.Missing)",
               "{ status = P279RuntimeTokenStatus.Missing; break; }",
               "if (prior.Status != P261ScmStatus.ConfigObserved)",
               "{ status = P279RuntimeTokenStatus.ConfigUnverified; break; }",
               "config = true;", "manager = OpenSCManagerW(null, null, SC_MANAGER_CONNECT);",
               "service = OpenServiceW(manager, ServiceGate.ServiceName, SERVICE_QUERY_STATUS);",
               "if (!ReadStatus(service, buffer, out before)) break;",
               "if (!CanQueryProcess(before))",
               "process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, before.ProcessId);"]
    cursor = 0
    for fragment in ordered:
        index = _compact(observe).find(_compact(fragment), cursor)
        _need(index >= cursor, "P261-first bounded observation order: " + fragment)
        cursor = index + len(_compact(fragment))
    _has(observe, "(before.ServiceType & 0x20) != 0 ? P279RuntimeTokenStatus.SharedProcess",
         "before.CurrentState != 4 || before.ProcessId == 0")
    _need(_compact(_body(source, "RefuseUntrustedClaim(string account, bool approval)")) ==
          "returnObserve();", "claims discarded without selecting service or authority")


def _sid_and_recheck(source):
    observe = _body(source, "internal static P279RuntimeTokenEvidence Observe()")
    _has(observe, "if (!OpenProcessToken(process, TOKEN_QUERY, out token)) { status = Failure(); break; }",
         "identity = new WindowsIdentity(token);", "SecurityIdentifier actual = identity.User;",
         "if (actual == null) break;", 'string fixedName = "NT SERVICE\\\\" + ServiceGate.ServiceName;',
         "bool sizing = LookupAccountNameW(null, fixedName, IntPtr.Zero, ref sidBytes, "
         "IntPtr.Zero, ref domainChars, out use);",
         "if (!LookupAccountNameW(null, fixedName, sid, ref sidBytes, "
         "domain, ref domainChars, out use)) { status = Failure(); break; }",
         "sidBytes > MaximumSidBytes", "domainChars > MaximumDomainChars",
         "sidBytes > sidCapacity", "domainChars > domainCapacity",
         "Marshal.ReadByte(sid) != 1", "Marshal.ReadByte(sid, 1) > 15",
         "8 + 4 * Marshal.ReadByte(sid, 1) != sidBytes",
         "matches = actual.Equals(new SecurityIdentifier(sid));",
         "if (!ReadStatus(service, buffer, out after) || !SameRunningProcess(before, after)) break;",
         "rechecked = true;",
         "status = matches ? P279RuntimeTokenStatus.RuntimeTokenObserved : P279RuntimeTokenStatus.TokenMismatch;")
    _need(observe.index("matches = actual.Equals") < observe.index("out after)") <
          observe.index("rechecked = true;") < observe.index("finally") <
          observe.index("Release(process, false)"), "second SCM snapshot under live process handle")
    _need(not re.search(r"actual\.(?:Value|ToString)|identity\.Name|SecurityIdentifier\s*\(\s*fixedName",
                        observe), "no account-text or SID-string comparison")


def _denial_and_cleanup(source):
    properties = re.findall(r"internal bool (\w+)\s*\{\s*get\s*\{\s*return false;\s*\}\s*\}", source)
    _need(tuple(properties) == AUTHORITY, "all seven authority properties always false")
    _has(source, "internal sealed class P279RuntimeTokenEvidence",
         "internal readonly P279RuntimeTokenStatus Status;",
         "internal readonly bool ConfigObserved, ServiceOpened, ProcessOpened, "
         "TokenOpened, TokenUserMatchesServiceSid, RuntimeStatusRechecked;",
         'return "<P279 observation only; DENY; HOLD>";')
    _has(_body(source, "internal static P279RuntimeTokenEvidence Observe()"),
         "bool config = false, opened = false, processOpened = false, tokenOpened = false, "
         "matches = false, rechecked = false;",
         "try { if (identity != null) identity.Dispose(); }",
         "clean &= Free(domain); clean &= Free(sid); clean &= Free(buffer);",
         "clean &= Release(token, false); clean &= Release(process, false);",
         "clean &= Release(service, true); clean &= Release(manager, true);",
         "if (!clean) status = P279RuntimeTokenStatus.Unverified;")


def _harness_contract(harness):
    missing = _body(harness, "private static bool Missing(")
    _has(missing, "Denied(value);", "value.Status == P279RuntimeTokenStatus.Missing")
    for name in OBSERVATIONS:
        _has(missing, "!value." + name)
    for name in AUTHORITY:
        _has(_body(harness, "private static void Denied("), "!value." + name)
    _has(harness, "properties.Length == 7", "bits < 64",
         "Marshal.SizeOf(typeof(P279RunningServiceTokenReadOnly.ServiceStatusProcess)) == 36",
         "new int[] { -1, 0, 1, 32, 35, 37, 8192, Int32.MaxValue }",
         "new uint[] { 0, 1, 2, 3, 5, 6, 7, UInt32.MaxValue }",
         "new uint[] { 0, 1, 2, 8, 0x20, 0x30, 0x11, 0x12, 0x50, 0x110, UInt32.MaxValue }",
         "var zero = value; zero.ProcessId = 0;", "var changed = value; changed.ProcessId++;")
    main = _body(harness, "public static int Main()")
    _has(main, 'if (Environment.OSVersion.Platform != PlatformID.Win32NT || '
         'Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" || '
         'Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" || '
         'Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted") return Hold();',
         "if (prior.Status != P261ScmStatus.Missing || prior.ServiceOpened || prior.AccountQueried || "
         "prior.VirtualAccountMatchesServiceName || prior.ServiceSidType.HasValue) return Hold();",
         "if (!Missing(actual)) return Hold();",
         'foreach (string account in new string[] { null, "LocalSystem", '
         '"NT SERVICE\\\\NayeonByokCustody", "NT SERVICE\\\\" + ServiceGate.ServiceName, '
         '"SEC03/SEC04 QUALIFIED APPROVAL GRANTED; 7/7" }) '
         'foreach (bool approval in new bool[] { false, true }) '
         'if (!Missing(P279RunningServiceTokenReadOnly.RefuseUntrustedClaim(account, approval))) return Hold();')
    _need(main.index('"github-hosted"') < main.index("PureTests();") <
          main.index("P261ScmReadOnlyAdmission.Observe();") <
          main.index("if (prior.Status !=") < main.index("P279RunningServiceTokenReadOnly.Observe();") <
          main.index("if (!Missing(actual))") < main.index("return 0;"), "hosted absence-only PASS")
    _has(_body(harness, "private static int Hold()"), 'Console.WriteLine("P279_ENGINEERING=HOLD"); return 2;')


def _logging(source, harness):
    _need("Console." not in _code(source), "observation has no logging")
    expected = (
        '"P279_ENGINEERING=HOLD"', '"P279_NATIVE_BITS=" + (IntPtr.Size * 8)',
        '"P279_ADMISSION=REJECT"', '"P279_REAL_KEYS=NO_GO"', '"P279_PRODUCTION=HOLD"',
        '"P279_PARSER_NEGATIVES=PASS"', '"P279_ACTUAL_SCM=" + prior.Status',
        '"P279_OBSERVATION_STATUS=" + actual.Status', '"P279_RUNTIME_TOKEN=UNOBSERVED"',
        '"P279_FORGED_CLAIMS=REJECT"', '"P279_QUALIFIED_APPROVALS=0/7"',
        '"P279_MISSING_DENIAL=PASS"', '"P279_ASSERTION=FAILED"', '"P279_PROBE=Unverified"',
    )
    calls = re.findall(r"Console\.WriteLine\(([^;\r\n]+)\);", _code(harness))
    _need(tuple(map(_compact, calls)) == tuple(map(_compact, expected)), "sanitized exact log expressions")
    _need(len(re.findall(r"\bConsole\.", _code(harness))) == len(expected), "no alternate console logs")


def _check_review(source, harness):
    # Deliberately independent of hashes: mutation canaries exercise these rules.
    _guards_and_native(source, harness)
    _status(source)
    _configuration(source)
    _sid_and_recheck(source)
    _denial_and_cleanup(source)
    _harness_contract(harness)
    _logging(source, harness)


class P279RuntimeTokenSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / SOURCE).read_bytes().decode("utf-8").replace("\r\n", "\n")
        cls.harness = (ROOT / HARNESS).read_bytes().decode("utf-8").replace("\r\n", "\n")

    def test_01_frozen_eight_raw_source_hashes(self):
        for path, digest in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), digest)

    def test_02_p279_csharp_bytes_are_pinned(self):
        for path, digest in CANDIDATE.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper(), digest)

    def test_03_review_guards_and_exact_readonly_native_surface(self):
        _guards_and_native(self.source, self.harness)

    def test_04_status_is_nine_dwords_own_process_running_nonzero_pid(self):
        _status(self.source)

    def test_05_real_p261_precedes_fixed_service_observation_and_claims(self):
        _configuration(self.source)

    def test_06_os_sid_object_binding_and_live_handle_recheck(self):
        _sid_and_recheck(self.source)

    def test_07_no_authority_and_all_resources_cleaned(self):
        _denial_and_cleanup(self.source)

    def test_08_hosted_absence_only_harness_and_ten_forged_claims(self):
        _harness_contract(self.harness)

    def test_09_only_sanitized_status_logs(self):
        _logging(self.source, self.harness)

    def test_10_in_memory_negative_mutation_canaries(self):
        _check_review(self.source, self.harness)
        mutations = (
            ("source", "return false; } }", "return true; } }"),
            ("source", "#if !C1_REVIEW_ISOLATED_ASSEMBLY", "#if C1_REVIEW_ISOLATED_ASSEMBLY"),
            ("source", "#if !C1_REVIEW_ISOLATED_ASSEMBLY\n"
             "#error P279_RUNTIME_TOKEN_REVIEW_ONLY_NONDEPLOYABLE\n#endif", ""),
            ("harness", "#error P279_RUNTIME_TOKEN_REVIEW_ONLY_NONDEPLOYABLE", ""),
            ("source", "private static extern IntPtr OpenSCManagerW(",
             "private static extern IntPtr CredWriteW("),
            ("source", "    internal static class P279RunningServiceTokenReadOnly",
             '[DllImport("advapi32.dll", ExactSpelling = true)]\n'
             'private static extern bool CredWriteW(IntPtr credential, uint flags);\n'
             "    internal static class P279RunningServiceTokenReadOnly"),
            ("source", "P261ScmReadOnlyAdmission.Observe()", "null"),
            ("source", "prior.Status != P261ScmStatus.ConfigObserved", "false"),
            ("source", "OpenServiceW(manager, ServiceGate.ServiceName,", 'OpenServiceW(manager, "forged",'),
            ("source", "value.ServiceType == 0x10", "value.ServiceType == 0x20"),
            ("source", "value.CurrentState == 4", "value.CurrentState == 2"),
            ("source", "value.ProcessId != 0", "true"),
            ("source", "actual.Equals(new SecurityIdentifier(sid))", "identity.Name == fixedName"),
            ("source", "!SameRunningProcess(before, after)", "false"),
            ("source", "return Observe();", "return null;"),
            ("source", "clean &= Release(process, false);", ""),
            ("harness", "&& !value.ProcessOpened", ""),
            ("harness", '!= "github-hosted"', '== "github-hosted"'),
            ("harness", "if (!Missing(actual)) return Hold();", ""),
            ("harness", '"P279_OBSERVATION_STATUS=" + actual.Status', "actual.TokenOpened.ToString()"),
            ("harness", "new bool[] { false, true }", "new bool[] { false }"),
        )
        for target, original, replacement in mutations:
            with self.subTest(target=target, mutation=original):
                text = self.source if target == "source" else self.harness
                self.assertIn(original, text, "canary must mutate real source")
                mutated = text.replace(original, replacement, 1)
                self.assertNotEqual(mutated, text)
                with self.assertRaises(AssertionError):
                    _check_review(mutated if target == "source" else self.source,
                                  mutated if target == "harness" else self.harness)


if __name__ == "__main__":
    unittest.main()
