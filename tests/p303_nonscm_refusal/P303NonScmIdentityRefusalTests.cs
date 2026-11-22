#if !DEBUG || RELEASE || !TEST_ONLY || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY || !C1_P301_DISPATCHER_OWNER_ONLY || !C1_P303_NONSCM_NEGATIVE_ONLY
#error P303_DEBUG_TEST_ONLY_ISOLATED_NONSCM_NEGATIVE_GUARDS_REQUIRED
#endif
using System;
using System.Reflection;
using System.Security.Principal;
using System.ServiceProcess;
using Nayeon.ByokC1.P301Development;

// Hosted Windows denial only; compile /main:P303NonScmIdentityRefusalTests.
// Add to the frozen nine-source P301 assembly; never execute locally.
// REQUIRED BEFORE EXECUTION: hosted workflow must pin P301 source SHA256 to
// 5D129C8FB908A281B493587F850E2A4012078EA03B4A4948C66AACE8E380B48D
// and validate the P301 17/17 source call-order baseline (without hosted mode).
// Owner-null/terminal observations prove no surviving owned worker, not zero
// transient allocation. No pipe observation or semantic success claim is made.
// Translation failure supplies mismatch evidence only, never service authority.
// P96 HIGH unwaived; P292 x86 deletion absence UNKNOWN; approvals 0/7;
// full product regressions 0/3; real-key NO-GO; production HOLD.
internal static class P303NonScmIdentityRefusalTests
{
    private const string Name = "NayeonP292_012345abcdef";
    private const string Sentinel = "P292_DISPOSABLE_SCM_WITNESS=1";
    private const string Parent = "4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f";
    private const BindingFlags PrivateInstance = BindingFlags.NonPublic | BindingFlags.Instance |
        BindingFlags.DeclaredOnly;
    private static int checks;

    private static void Check(bool condition, string label)
    {
        if (!condition) throw new InvalidOperationException(label);
        checks++;
    }

    private static bool TrustedNegativeRunner()
    {
        string arch = Environment.GetEnvironmentVariable("REVIEW_ARCH");
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
            Environment.GetEnvironmentVariable("ImageOS") != "win22" ||
            Environment.OSVersion.Platform != PlatformID.Win32NT ||
            !((arch == "x64" && IntPtr.Size == 8) || (arch == "x86" && IntPtr.Size == 4)))
            return false;
        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
        {
            SecurityIdentifier user = identity.User;
            if (user == null || identity.ImpersonationLevel != TokenImpersonationLevel.None ||
                user.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                user.Value.StartsWith("S-1-5-80-", StringComparison.Ordinal)) return false;
            try
            {
                SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE", Name)
                    .Translate(typeof(SecurityIdentifier));
                if (user.Equals(expected)) return false;
            }
            catch (IdentityNotMappedException)
            {
                // Expected account unresolved; non-System/non-service SID evidence above still required.
            }
        }
        return true;
    }

    private static bool State(Type host, ServiceBase service, bool terminal)
    {
        return host.GetField("owner", PrivateInstance).GetValue(service) == null &&
            !(bool)host.GetField("started", PrivateInstance).GetValue(service) &&
            (bool)host.GetField("terminal", PrivateInstance).GetValue(service) == terminal &&
            service.ExitCode == 1;
    }

    private static bool Denied(MethodInfo start, ServiceBase service, string[] arguments)
    {
        try { start.Invoke(service, new object[] { arguments }); return false; }
        catch (TargetInvocationException error)
        {
            return error.InnerException != null &&
                error.InnerException.GetType() == typeof(InvalidOperationException) &&
                error.InnerException.Message == "P301_START_DENIED";
        }
    }

    private static void Scenario(Type host, ConstructorInfo constructor, MethodInfo start, bool nullArgs)
    {
        ServiceBase service = (ServiceBase)constructor.Invoke(new object[] { Name });
        try
        {
            Check(State(host, service, false), nullArgs ? "15 null initial" : "11 initial");
            Check(Denied(start, service, nullArgs ? null : new string[0]) && State(host, service, true),
                nullArgs ? "16 null start denied terminal" : "12 start denied terminal");
            if (!nullArgs)
                Check(Denied(start, service, new string[0]) && State(host, service, true),
                    "13 repeated start denied no rearm");
        }
        finally { service.Dispose(); service.Dispose(); }
        Check(State(host, service, true), nullArgs ? "17 null double dispose" : "14 double dispose");
    }

    private static int Main()
    {
        try
        {
            Check(TrustedNegativeRunner(), "01 hosted negative identity preflight");
            Type host = typeof(P301DispatcherOwnedSyntheticService);
            ConstructorInfo constructor = host.GetConstructor(PrivateInstance, null, new[] { typeof(string) }, null);
            MethodInfo main = host.GetMethod("Main", BindingFlags.NonPublic | BindingFlags.Static |
                BindingFlags.DeclaredOnly);
            MethodInfo start = host.GetMethod("OnStart", PrivateInstance);
            Check(constructor != null && constructor.IsPrivate && main != null && main.IsPrivate &&
                main.ReturnType == typeof(int) && start != null && start.IsFamily &&
                host.GetField("owner", PrivateInstance) != null &&
                host.GetField("started", PrivateInstance) != null &&
                host.GetField("terminal", PrivateInstance) != null, "02 private reflection contract");
            // Each vector fails the first argument guard, independent of session/interactivity.
            // NEVER supply the complete valid four-argument contract, even on hosted runners.
            string[][] vectors = {
                null, new string[0], new[] { "invalid" }, new[] { Sentinel, Name, Parent },
                new[] { "invalid", Name, Parent, new string('a', 40) },
                new[] { Sentinel, "invalid", Parent, new string('a', 40) },
                new[] { Sentinel, Name, "invalid", new string('a', 40) },
                new[] { Sentinel, Name, Parent, new string('g', 40) }
            };
            string[] labels = { "03 main null", "04 main empty", "05 main single invalid",
                "06 main three", "07 main invalid sentinel", "08 main invalid name",
                "09 main wrong parent", "10 main invalid child hash" };
            for (int i = 0; i < vectors.Length; i++)
                Check((int)main.Invoke(null, new object[] { vectors[i] }) == 1, labels[i]);
            Scenario(host, constructor, start, false);
            Scenario(host, constructor, start, true);
            if (checks != 17) throw new InvalidOperationException();
            Console.WriteLine("P303_NONSCM_REFUSAL=PASS CHECKS=" + checks + " BITS=" + (IntPtr.Size * 8) +
                " OWNER_CREATED=NO SCM_USED=NO PRODUCTION=HOLD");
            return 0;
        }
        catch (Exception) { Console.WriteLine("P303_HOLD"); return 1; }
    }
}
