#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P279_RUNTIME_TOKEN_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Reflection;
using System.Runtime.InteropServices;
using Nayeon.ByokC1;

// Hosted disposable Windows only. Environment checks are an execution interlock,
// not attestation or an approval mechanism. Never install/start/stop a service.
internal static class RuntimeServiceTokenTests
{
    private sealed class AssertionFault : Exception { }
    private static void Need(bool condition) { if (!condition) throw new AssertionFault(); }
    private static void Denied(P279RuntimeTokenEvidence value)
    {
        Need(!value.QualifiedSecurityDecisionApproved && !value.ApprovedServicePrincipal &&
            !value.ProtectedCredentialOwner && !value.TrustedConsent &&
            !value.NativeCredentialEffectAllowed && !value.RealKeyEligible &&
            !value.ProductionReleaseEligible);
        Need(value.ToString() == "<P279 observation only; DENY; HOLD>");
    }
    private static bool Missing(P279RuntimeTokenEvidence value)
    {
        Denied(value);
        return value.Status == P279RuntimeTokenStatus.Missing && !value.ConfigObserved &&
            !value.ServiceOpened && !value.ProcessOpened && !value.TokenOpened &&
            !value.TokenUserMatchesServiceSid && !value.RuntimeStatusRechecked;
    }
    private static void PureTests()
    {
        Type evidence = typeof(P279RuntimeTokenEvidence);
        Need(evidence.IsSealed && !evidence.IsPublic);
        foreach (FieldInfo field in evidence.GetFields(BindingFlags.Instance |
            BindingFlags.NonPublic | BindingFlags.Public))
            Need(field.IsInitOnly && (field.FieldType == typeof(bool) ||
                field.FieldType == typeof(P279RuntimeTokenStatus)));
        PropertyInfo[] properties = evidence.GetProperties(BindingFlags.Instance |
            BindingFlags.NonPublic | BindingFlags.Public);
        Need(properties.Length == 7);
        foreach (PropertyInfo property in properties)
            Need(property.PropertyType == typeof(bool) && property.GetSetMethod(true) == null);
        foreach (P279RuntimeTokenStatus status in Enum.GetValues(typeof(P279RuntimeTokenStatus)))
            for (int bits = 0; bits < 64; bits++)
                Denied(new P279RuntimeTokenEvidence(status, (bits & 1) != 0, (bits & 2) != 0,
                    (bits & 4) != 0, (bits & 8) != 0, (bits & 16) != 0, (bits & 32) != 0));

        Need(Marshal.SizeOf(typeof(P279RunningServiceTokenReadOnly.ServiceStatusProcess)) == 36);
        IntPtr buffer = Marshal.AllocHGlobal(36);
        try
        {
            var value = new P279RunningServiceTokenReadOnly.ServiceStatusProcess();
            value.ServiceType = 0x10; value.CurrentState = 4; value.ProcessId = 42;
            Marshal.StructureToPtr(value, buffer, false);
            P279RunningServiceTokenReadOnly.ServiceStatusProcess parsed;
            Need(P279RunningServiceTokenReadOnly.TryParseStatus(buffer, 36, out parsed));
            Need(parsed.ServiceType == 0x10 && parsed.CurrentState == 4 && parsed.ProcessId == 42);
            Need(P279RunningServiceTokenReadOnly.CanQueryProcess(parsed));
            Need(P279RunningServiceTokenReadOnly.SameRunningProcess(value, parsed));
            Need(!P279RunningServiceTokenReadOnly.TryParseStatus(IntPtr.Zero, 36, out parsed));
            foreach (int size in new int[] { -1, 0, 1, 32, 35, 37, 8192, Int32.MaxValue })
                Need(!P279RunningServiceTokenReadOnly.TryParseStatus(buffer, size, out parsed));
            foreach (uint state in new uint[] { 0, 1, 2, 3, 5, 6, 7, UInt32.MaxValue })
            {
                var other = value; other.CurrentState = state;
                Marshal.StructureToPtr(other, buffer, false);
                Need(P279RunningServiceTokenReadOnly.TryParseStatus(buffer, 36, out parsed));
                Need(!P279RunningServiceTokenReadOnly.CanQueryProcess(parsed));
                Need(!P279RunningServiceTokenReadOnly.SameRunningProcess(value, parsed));
            }
            foreach (uint type in new uint[] { 0, 1, 2, 8, 0x20, 0x30, 0x11, 0x12, 0x50, 0x110, UInt32.MaxValue })
            {
                var other = value; other.ServiceType = type;
                Marshal.StructureToPtr(other, buffer, false);
                Need(P279RunningServiceTokenReadOnly.TryParseStatus(buffer, 36, out parsed));
                Need(!P279RunningServiceTokenReadOnly.CanQueryProcess(parsed));
                Need(!P279RunningServiceTokenReadOnly.SameRunningProcess(value, parsed));
            }
            var zero = value; zero.ProcessId = 0;
            Need(!P279RunningServiceTokenReadOnly.CanQueryProcess(zero));
            Need(!P279RunningServiceTokenReadOnly.SameRunningProcess(value, zero));
            var changed = value; changed.ProcessId++;
            Need(!P279RunningServiceTokenReadOnly.SameRunningProcess(value, changed));
            Need(!P279RunningServiceTokenReadOnly.SameRunningProcess(zero, zero));
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }
    private static int Hold()
    {
        Console.WriteLine("P279_ENGINEERING=HOLD");
        return 2;
    }
    public static int Main()
    {
        Console.WriteLine("P279_NATIVE_BITS=" + (IntPtr.Size * 8));
        Console.WriteLine("P279_ADMISSION=REJECT");
        Console.WriteLine("P279_REAL_KEYS=NO_GO");
        Console.WriteLine("P279_PRODUCTION=HOLD");
        try
        {
            if (Environment.OSVersion.Platform != PlatformID.Win32NT ||
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
                Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted") return Hold();
            PureTests();
            Console.WriteLine("P279_PARSER_NEGATIVES=PASS");
            P261ScmEvidence prior = P261ScmReadOnlyAdmission.Observe();
            Need(!prior.QualifiedDecisionApproved && !prior.ApprovedServiceOwner &&
                !prior.EffectAllowed && !prior.RealKeyEligible && !prior.CredentialAuthority);
            Console.WriteLine("P279_ACTUAL_SCM=" + prior.Status);
            if (prior.Status != P261ScmStatus.Missing || prior.ServiceOpened || prior.AccountQueried ||
                prior.VirtualAccountMatchesServiceName || prior.ServiceSidType.HasValue) return Hold();
            P279RuntimeTokenEvidence actual = P279RunningServiceTokenReadOnly.Observe();
            Console.WriteLine("P279_OBSERVATION_STATUS=" + actual.Status);
            if (!Missing(actual)) return Hold();
            Console.WriteLine("P279_RUNTIME_TOKEN=UNOBSERVED");
            // Five forged names x two approval claims = ten discarded inputs.
            foreach (string account in new string[] { null, "LocalSystem",
                "NT SERVICE\\NayeonByokCustody", "NT SERVICE\\" + ServiceGate.ServiceName,
                "SEC03/SEC04 QUALIFIED APPROVAL GRANTED; 7/7" })
                foreach (bool approval in new bool[] { false, true })
                    if (!Missing(P279RunningServiceTokenReadOnly.RefuseUntrustedClaim(account, approval)))
                        return Hold();
            Console.WriteLine("P279_FORGED_CLAIMS=REJECT");
            Console.WriteLine("P279_QUALIFIED_APPROVALS=0/7");
            Console.WriteLine("P279_MISSING_DENIAL=PASS");
            return 0;
        }
        catch (AssertionFault)
        {
            Console.WriteLine("P279_ASSERTION=FAILED");
            return 1;
        }
        catch (Exception)
        {
            // No exception messages, identifiers, account text, paths or native error text.
            Console.WriteLine("P279_PROBE=Unverified");
            return Hold();
        }
    }
}
