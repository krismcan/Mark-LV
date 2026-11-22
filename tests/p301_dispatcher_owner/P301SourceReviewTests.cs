#if !DEBUG || RELEASE || !TEST_ONLY || !C1_P301_DISPATCHER_OWNER_ONLY || !C1_REVIEW_ISOLATED_ASSEMBLY
#error P301_TEST_ONLY_DEBUG_ISOLATED_OWNER_GUARDS_REQUIRED
#endif
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.InteropServices;
using System.ServiceProcess;
using System.Text.RegularExpressions;
using Nayeon.ByokC1.P269Development;
using Nayeon.ByokC1.P301Development;

// Offline compiled-source review; no construction, OnStart invocation, IPC or service control.
// Compile with the P269 frozen fixture dependencies and /main:P301SourceReviewTests.
// Optional --hosted-nonscm-refusal is ONLY for an independent GitHub-hosted runner.
// For a separate hosted process refusal, compile /main:Nayeon.ByokC1.P301Development.P301DispatcherOwnedSyntheticService.
// Missing C1_P301_DISPATCHER_OWNER_ONLY must be a hard compiler negative in a later workflow.
internal static class P301SourceReviewTests
{
    private const BindingFlags Declared = BindingFlags.DeclaredOnly | BindingFlags.Public |
        BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance;
    private static readonly Type Host = typeof(P301DispatcherOwnedSyntheticService);
    private static readonly Dictionary<short, OpCode> Codes = typeof(OpCodes).GetFields()
        .Where(f => f.FieldType == typeof(OpCode)).Select(f => (OpCode)f.GetValue(null))
        .ToDictionary(c => c.Value);
    private static int checks;
    private static void Check(bool ok, string label)
    { if (!ok) throw new InvalidOperationException(label); checks++; }
    private static MethodInfo Method(string name) { return Host.GetMethod(name, Declared); }

    private static bool IsRestrictedTokenImport(MethodBase method)
    {
        var info = method as MethodInfo;
        var import = (DllImportAttribute)Attribute.GetCustomAttribute(method, typeof(DllImportAttribute));
        return info != null && info.DeclaringType == Host && info.IsPrivate && info.IsStatic &&
            info.Name == "IsTokenRestricted" && info.ReturnType == typeof(bool) &&
            info.GetParameters().Length == 1 && info.GetParameters()[0].ParameterType == typeof(IntPtr) &&
            import != null && import.Value == "advapi32.dll" && import.EntryPoint == "IsTokenRestricted" &&
            import.ExactSpelling && import.SetLastError;
    }

    // Decode instructions, never search arbitrary operand bytes for call opcodes.
    private static List<MethodBase> Calls(MethodBase method)
    {
        var result = new List<MethodBase>();
        MethodBody body = method.GetMethodBody();
        if (body == null)
        {
            if (IsRestrictedTokenImport(method)) return result;
            throw new InvalidOperationException("unknown missing IL body");
        }
        byte[] il = body.GetILAsByteArray();
        for (int i = 0; i < il.Length; )
        {
            short code = il[i++];
            if (code == 0xfe) code = (short)(0xfe00 | il[i++]);
            OpCode op = Codes[code];
            int size;
            switch (op.OperandType)
            {
                case OperandType.InlineNone: size = 0; break;
                case OperandType.ShortInlineBrTarget:
                case OperandType.ShortInlineI:
                case OperandType.ShortInlineVar: size = 1; break;
                case OperandType.InlineVar: size = 2; break;
                case OperandType.InlineI8:
                case OperandType.InlineR: size = 8; break;
                case OperandType.InlineSwitch: size = checked(4 + 4 * BitConverter.ToInt32(il, i)); break;
                default: size = 4; break;
            }
            if (i + size > il.Length) throw new InvalidOperationException("invalid IL bounds");
            if (op.OperandType == OperandType.InlineMethod)
                result.Add(method.Module.ResolveMethod(BitConverter.ToInt32(il, i)));
            i += size;
        }
        return result;
    }
    private static bool Ordered(List<MethodBase> calls, params string[] names)
    {
        int cursor = -1;
        foreach (string name in names)
        {
            cursor = calls.FindIndex(cursor + 1, m => m.Name == name);
            if (cursor < 0) return false;
        }
        return true;
    }
    private static bool HostedRefusal(string[] args)
    {
        if (args.Length == 1) return true; // Default review does not invoke the service entrypoint.
        if (args.Length != 2 || args[1] != "--hosted-nonscm-refusal" ||
            Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted") return false;
        using (Process current = Process.GetCurrentProcess())
            if (!Environment.UserInteractive && current.SessionId == 0) return false;
        // Normal nonSCM context is established BEFORE invoking even the valid argument contract.
        string[][] vectors = { null, new string[0], new[] { "invalid" },
            new[] { "P292_DISPOSABLE_SCM_WITNESS=1", "NayeonP292_012345abcdef",
                "4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f", new string('a', 40) } };
        return vectors.All(v => (int)Method("Main").Invoke(null, new object[] { v }) == 1);
    }
    private static int Main(string[] args)
    {
        try
        {
            if (args.Length < 1 || args.Length > 2) return 1;
            string source = File.ReadAllText(Path.Combine(args[0], "native_c1_successor/P301DispatcherOwnedSyntheticService.cs"));
            string old = File.ReadAllText(Path.Combine(args[0], "native_c1_successor/P269ComposedDevelopmentService.cs"));
            string[] guards = { "!DEBUG", "RELEASE", "!C1_REVIEW_ISOLATED_ASSEMBLY", "!C1_P265_DEVELOPMENT_ONLY",
                "!C1_P267_DEVELOPMENT_ONLY", "!C1_P268_DEVELOPMENT_ONLY", "!C1_P269_DEVELOPMENT_ONLY",
                "!C1_P301_DISPATCHER_OWNER_ONLY" };
            Check(source.StartsWith("#if " + string.Join(" || ", guards) + "\n#error P301_", StringComparison.Ordinal) ||
                source.StartsWith("#if " + string.Join(" || ", guards) + "\r\n#error P301_", StringComparison.Ordinal), "01 build guards");
            Check(Host.IsSealed && Host.IsNotPublic && Host.BaseType == typeof(ServiceBase) &&
                Host.GetConstructors(Declared).All(c => c.IsPrivate), "02 sealed private construction");
            FieldInfo[] owners = Host.GetFields(Declared).Where(f => f.FieldType == typeof(ComposedDevelopmentService)).ToArray();
            Check(owners.Length == 1 && owners[0].IsPrivate && !owners[0].IsStatic &&
                Host.GetFields(Declared).All(f => f.IsPrivate), "03 private ownership");
            Check(Host.GetMethods(Declared).All(m => !m.IsPublic &&
                m.ReturnType != typeof(ComposedDevelopmentService) &&
                !Regex.IsMatch(m.Name, "(?i)auth|submit|prepare|ticket")), "04 no admission surface");
            Check(new[] { "ClientAdmissionAllowed", "CredentialEffectAllowed", "ProductionEligible" }.All(n =>
                Host.GetProperty(n, Declared).GetGetMethod(true).IsStatic &&
                !(bool)Host.GetProperty(n, Declared).GetValue(null, null)), "05 false authority getters");
            string allowedImport = "[DllImport(\"advapi32.dll\", ExactSpelling = true, SetLastError = true)]";
            Check(source.Split(new[] { allowedImport }, StringSplitOptions.None).Length == 2 &&
                !Regex.IsMatch(source.Replace(allowedImport, ""), "(?i)DllImport|LibraryImport|WinCred|DPAPI|CredWrite|CredDelete|ProtectedData|" +
                "TestPrepare|TestSubmit|\\.Apply\\s*\\(|IssueDevelopmentApproval|Process\\.Start|ServiceInstaller|ServiceController"),
                "06 only read-only restricted-token import/no effect/request path");
            Check(Regex.IsMatch(old, @"private static int Main\(string\[\] arguments\)\s*\{ return 64; \}") &&
                !old.Contains("ServiceBase.Run"), "07 P269 entry remains disabled");
            Check(source.Contains("args.Length != 4") && source.Contains("P292_DISPOSABLE_SCM_WITNESS=1") &&
                source.Contains("args[1].Length != 23") && source.Contains(@"\\ANayeonP292_[0-9a-f]{12}\\z") &&
                source.Contains("4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f") &&
                source.Contains("args[3].Length != 40") && source.Contains(@"\\A[0-9a-f]{40}\\z"), "08 exact ImagePath contract");
            List<MethodBase> main = Calls(Method("Main")), start = Calls(Method("OnStart"));
            Check(Ordered(main, "get_OSVersion", "get_UserInteractive", "GetCurrentProcess", "get_SessionId", ".ctor", "Run") &&
                source.Contains("PlatformID.Win32NT") && source.Contains("current.SessionId != 0") &&
                source.Contains("55000, Timeout.Infinite"), "09 context then bounded dispatcher");
            Check(main.Count(m => m.DeclaringType == typeof(ServiceBase) && m.Name == "Run") == 1 &&
                !main.Any(m => m.Name == "VerifyIdentity" || m.Name == "OnStart" ||
                    m.DeclaringType == typeof(ComposedDevelopmentService) || m.DeclaringType == typeof(System.Security.Principal.WindowsIdentity)) &&
                !Calls(Host.GetConstructors(Declared).Single()).Any(m => m.Name == "VerifyIdentity" ||
                    m.DeclaringType == typeof(ComposedDevelopmentService)), "10 dispatcher before identity/owner");
            Check(Ordered(start, "VerifyIdentity", "TestOnlyCreate", "StartDevelopment") &&
                start.Count(m => m.Name == "TestOnlyCreate") == 1 &&
                source.Contains("TestOnlyCreate(LedgerOperation.Save, true)"), "11 synchronous identity before ownership/start");
            Check(Ordered(Calls(Method("VerifyIdentity")), "GetCurrent", "Translate", "get_ImpersonationLevel", "get_User", "IsWellKnown", "Equals") &&
                source.Contains("TokenImpersonationLevel.None") && source.Contains("WellKnownSidType.LocalSystemSid") &&
                source.Contains("new NTAccount(\"NT SERVICE\", expectedServiceName)"), "12 exact nonimpersonated virtual identity");
            MethodInfo[] methods = Host.GetMethods(Declared);
            MethodInfo[] imports = methods.Where(m => m.IsDefined(typeof(DllImportAttribute), false)).ToArray();
            Check(imports.Length == 1 && IsRestrictedTokenImport(imports[0]) &&
                methods.SelectMany(m => Calls(m)).Where(m => m.DeclaringType == typeof(ComposedDevelopmentService))
                .All(m => new[] { "TestOnlyCreate", "StartDevelopment", "StopDevelopment" }.Contains(m.Name)), "13 owner call allowlist");
            Check(new[] { "OnStop", "OnShutdown", "Dispose" }.All(n => Calls(Method(n)).Any(m => m.Name == "Close")) &&
                Ordered(Calls(Method("Close")), "StopDevelopment", "Dispose") &&
                Method("Close").GetMethodBody().ExceptionHandlingClauses.Any(c => c.Flags == ExceptionHandlingClauseOptions.Finally) &&
                source.Contains("terminal = true; ExitCode = 1;") && source.Contains("owner = null;") &&
                source.Contains("if (terminal || started)"), "14 terminal cleanup/no rearm");
            Check(Method("Main").IsPrivate && Method("Main").IsStatic &&
                !methods.Where(m => m.Name != "Main").SelectMany(m => Calls(m)).Any(m => m == Method("Main")) &&
                methods.Where(m => m.Name != "OnStart").SelectMany(m => Calls(m)).All(m => m.Name != "StartDevelopment"),
                "15 private entry/no alternate worker start");
            Check(HostedRefusal(args), "16 hosted-only normal-context entry refuses 1");
            Check(Ordered(Calls(Method("VerifyIdentity")), "Equals", "get_Token", "IsTokenRestricted") &&
                Calls(Method("VerifyIdentity")).Count(m => m == Method("IsTokenRestricted")) == 1 &&
                source.Contains("if (!IsTokenRestricted(identity.Token))") &&
                Regex.IsMatch(source, @"if \(!IsTokenRestricted\(identity.Token\)\)\s*throw new InvalidOperationException\(""P301_START_DENIED""\);") &&
                Ordered(start, "VerifyIdentity", "TestOnlyCreate", "StartDevelopment"),
                "17 restricted token required before ownership/start");
            Console.WriteLine("P301_SOURCE_CHECKS=" + checks + "; runtime refusal=" + (args.Length == 2 ? "hosted" : "NOT RUN"));
            return 0;
        }
        catch (Exception) { Console.WriteLine("P301_SOURCE_REVIEW_FAILED_AFTER=" + checks); return 1; }
    }
}
