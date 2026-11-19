#if !DEBUG || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY
#error P282_TESTS_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Principal;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P271Development;
using Nayeon.ByokC1.P270Development;

// Read-only Windows negatives + pure synthetic transitions. NO file fixtures,
// DPAPI calls, credential effects, service changes, token mutation or privileges.
internal static class ExecutingServiceCustodyTests
{
    private sealed class AssertionFault : Exception { }
    private static int checks;
    private static void Need(bool value) { checks++; if (!value) throw new AssertionFault(); }
    private static void Denied(P282CustodyEvidence value)
    {
        Need(!value.ProfileOwnershipEstablished && !value.CurrentUserProtectedStoreEstablished &&
            !value.QualifiedSec0304Approved && !value.ProtectedCustodyAllowed && !value.ProductionEligible);
    }
    private static void PureTests()
    {
        Need(ServiceGate.ServiceName == "NayeonV1ByokCustody");
        Need(Marshal.SizeOf(typeof(P282ExecutingServiceCustody.Statistics)) == 56);
        Need(Marshal.OffsetOf(typeof(P282ExecutingServiceCustody.Statistics), "ModifiedId").ToInt32() == 48);
        foreach (P282CustodyStatus status in Enum.GetValues(typeof(P282CustodyStatus)))
            foreach (bool observed in new[] { false, true }) Denied(new P282CustodyEvidence(status, observed));
        // Forged observation objects/roundtrip claims cannot enter the API.
        MethodInfo[] methods = typeof(DurableDevelopmentBridge).GetMethods(BindingFlags.Static | BindingFlags.NonPublic);
        int protectedEntries = 0;
        foreach (MethodInfo method in methods)
            if (method.Name == "OpenProtectedService")
            {
                protectedEntries++;
                ParameterInfo[] args = method.GetParameters();
                Need(args.Length == 3 && args[0].ParameterType == typeof(string) &&
                    args[1].ParameterType == typeof(LedgerOperation) && args[2].ParameterType == typeof(bool));
            }
        Need(protectedEntries == 1);
        Need(P261ScmReadOnlyAdmission.ClassifyConfiguration(false, 3) == P261ScmStatus.Mismatch);
        Need(P261ScmReadOnlyAdmission.ClassifyConfiguration(true, 0) == P261ScmStatus.Mismatch);
        Need(P261ScmReadOnlyAdmission.ClassifyConfiguration(true, 1) == P261ScmStatus.Mismatch);
        // Pure fabricated SID fixtures: these NEVER create a live identity binding.
        Need(!P282ExecutingServiceCustody.IsSyntheticRunnerUser(null, 1));
        Need(!P282ExecutingServiceCustody.IsSyntheticRunnerUser(new SecurityIdentifier("S-1-5-18"), 1));
        Need(!P282ExecutingServiceCustody.IsSyntheticRunnerUser(new SecurityIdentifier("S-1-5-80-1-2-3-4-5"), 1));
        var ordinary = new SecurityIdentifier("S-1-5-21-1-2-3-1000");
        Need(!P282ExecutingServiceCustody.IsSyntheticRunnerUser(ordinary, 0));
        Need(P282ExecutingServiceCustody.IsSyntheticRunnerUser(ordinary, 1));
        var stats = new P282ExecutingServiceCustody.Statistics(); stats.TokenType = 1;
        Need(P282ExecutingServiceCustody.SameStatistics(stats, stats));
        for (int i = 0; i < 8; i++)
        {
            var changed = stats;
            if (i == 0) changed.TokenId.Low++;
            if (i == 1) changed.TokenId.High++;
            if (i == 2) changed.AuthenticationId.Low++;
            if (i == 3) changed.AuthenticationId.High++;
            if (i == 4) changed.ModifiedId.Low++;
            if (i == 5) changed.ModifiedId.High++;
            if (i == 6) changed.TokenType = 2;
            if (i == 7) changed.TokenType = 0;
            Need(!P282ExecutingServiceCustody.SameStatistics(stats, changed));
            Need(!P282ExecutingServiceCustody.SameStatistics(changed, stats));
        }
        var before = new P279RunningServiceTokenReadOnly.ServiceStatusProcess();
        before.ServiceType = 0x10; before.CurrentState = 4; before.ProcessId = 42;
        for (int i = 0; i < 9; i++)
        {
            var after = before;
            uint pid = 42, session = 0; bool match = true, unchanged = true;
            P282CustodyStatus expected = P282CustodyStatus.IdentityObservedStoreNotProven;
            if (i == 1) { after.ProcessId++; expected = P282CustodyStatus.Changed; }
            if (i == 2) { after.CurrentState = 3; expected = P282CustodyStatus.Changed; }
            if (i == 3) { after.ServiceType = 0x20; expected = P282CustodyStatus.Changed; }
            if (i == 4) { unchanged = false; expected = P282CustodyStatus.Changed; }
            if (i == 5) { pid = 43; expected = P282CustodyStatus.NotExecutingService; }
            if (i == 6) { pid = 0; expected = P282CustodyStatus.NotExecutingService; }
            if (i == 7) { match = false; expected = P282CustodyStatus.TokenRejected; }
            if (i == 8) { session = 1; expected = P282CustodyStatus.TokenRejected; }
            P282CustodyStatus actual = P282ExecutingServiceCustody.ClassifyExecutingService(
                before, after, pid, match, session, unchanged);
            Need(actual == expected); Denied(new P282CustodyEvidence(actual, true));
        }
        // Review the actual new native import surface, without invoking mutators.
        string[] allowed = { "GetCurrentProcess", "GetCurrentProcessId", "GetCurrentThread", "CloseHandle",
            "OpenProcessToken", "OpenThreadToken", "GetTokenInformation", "OpenSCManagerW",
            "OpenServiceW", "QueryServiceStatusEx", "CloseServiceHandle" };
        int imports = 0;
        foreach (MethodInfo method in typeof(P282ExecutingServiceCustody).GetMethods(BindingFlags.Static | BindingFlags.NonPublic))
        {
            var import = (DllImportAttribute)Attribute.GetCustomAttribute(method, typeof(DllImportAttribute));
            if (import == null) continue;
            imports++; Need(Array.IndexOf(allowed, method.Name) >= 0);
            Need(import.Value == "kernel32.dll" || import.Value == "advapi32.dll");
        }
        Need(imports == allowed.Length);
    }
    private static void ProtectedEntryNegatives()
    {
        string stage = DurableWitness.TestStage;
        foreach (string claim in new[] { null, "LocalSystem", "NT SERVICE\\NayeonByokCustody",
            "NT SERVICE\\" + ServiceGate.ServiceName, "DPAPI_OK;REMOTE_TOKEN_OK;SEC03_APPROVED=true" })
            foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace,
                LedgerOperation.Delete, (LedgerOperation)999 })
                foreach (bool fresh in new[] { false, true })
                {
                    bool blocked = false;
                    try { DurableDevelopmentBridge.OpenProtectedService(claim, op, fresh); }
                    catch (LedgerBlocked) { blocked = true; }
                    Need(blocked && DurableWitness.TestStage == stage);
                }
    }
    private static void SyntheticBridgeBindingNegatives()
    {
        string p270 = Environment.GetEnvironmentVariable("P270_HOSTED_DISPOSABLE");
        string p271 = Environment.GetEnvironmentVariable("P271_HOSTED_DISPOSABLE");
        string runnerOs = Environment.GetEnvironmentVariable("RUNNER_OS");
        string stage = DurableWitness.TestStage;
        try
        {
            Environment.SetEnvironmentVariable("P270_HOSTED_DISPOSABLE", null);
            Environment.SetEnvironmentVariable("P271_HOSTED_DISPOSABLE", "1");
            // Main establishes the other hosted prerequisites. A rejected RUNNER_OS
            // reaches the P282 binding restriction beyond P271's older hosted gate.
            foreach (string rejectedOs in new[] { null, "Linux", "Windows-claimed" })
            {
                Environment.SetEnvironmentVariable("RUNNER_OS", rejectedOs);
                bool blocked = false;
                try { P282ExecutingServiceCustody.BindSyntheticRunner(); }
                catch (LedgerBlocked) { blocked = true; }
                Need(blocked && DurableWitness.TestStage == stage);
                foreach (bool fresh in new[] { false, true })
                {
                    blocked = false;
                    // Null root exposes an ordering regression without a file fixture:
                    // P270 path processing would throw a different exception and
                    // change TestStage if the P282-bound P271 gate were bypassed.
                    try { using (var bridge = new DurableDevelopmentBridge(null, LedgerOperation.Save, fresh)) { Need(false); } }
                    catch (LedgerBlocked) { blocked = true; }
                    Need(blocked && DurableWitness.TestStage == stage);
                }
            }
        }
        finally
        {
            Environment.SetEnvironmentVariable("P270_HOSTED_DISPOSABLE", p270);
            Environment.SetEnvironmentVariable("P271_HOSTED_DISPOSABLE", p271);
            Environment.SetEnvironmentVariable("RUNNER_OS", runnerOs);
        }
    }
    private static int Main()
    {
        Console.WriteLine("P282_PRODUCTION=HOLD REAL_KEYS=NO_GO SERVICE_ISOLATION=NOT_PROVEN");
        try
        {
            if (Environment.OSVersion.Platform != PlatformID.Win32NT ||
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
                Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows") return 2;
            PureTests();
            P282CustodyEvidence actual = P282ExecutingServiceCustody.ObserveProtectedService();
            Denied(actual);
            Console.WriteLine("P282_CALLER_TOKEN_OBSERVED=" + actual.ProcessTokenObserved);
            Console.WriteLine("P282_ACTUAL_STATUS=" + actual.Status);
            // A service unexpectedly installed on the evidence runner is HOLD.
            if (!actual.ProcessTokenObserved || actual.Status != P282CustodyStatus.MissingService) return 2;
            ProtectedEntryNegatives();
            SyntheticBridgeBindingNegatives();
            // Session-zero/virtual-service runners cannot use the ordinary-user
            // synthetic fixture route. A successful binding proves only that route.
            try
            {
                var binding = P282ExecutingServiceCustody.BindSyntheticRunner();
                binding.DemandUnchanged();
                Console.WriteLine("P282_SYNTHETIC_RUNNER_BINDING=OBSERVED_NOT_SERVICE_APPROVAL");
            }
            catch (LedgerBlocked) { Console.WriteLine("P282_SYNTHETIC_RUNNER_BINDING=REFUSED"); }
            Console.WriteLine("P282_READONLY_AND_SYNTHETIC_NEGATIVES=PASS CHECKS=" + checks);
            return 0;
        }
        catch (AssertionFault) { Console.WriteLine("P282_ASSERTION=FAILED"); return 1; }
        catch (Exception) { Console.WriteLine("P282_EVIDENCE=UNVERIFIED"); return 2; }
    }
}
