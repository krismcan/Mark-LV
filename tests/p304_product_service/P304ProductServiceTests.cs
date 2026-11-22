using System;
using System.Diagnostics;
using System.Reflection;
using System.Threading.Tasks;
using Nayeon.ByokC1.Service;

internal static class P304ProductServiceTests
{
    private static int checks;
    private static void Check(bool value)
    { checks++; if (!value) throw new Exception("P304 assertion " + checks); }

    private static void Denied(LifecycleCoordinator core)
    {
        ServiceReadiness report = core.Observe();
        Check(!core.DenyClientAdmission() && !core.DenyCredentialOperation());
        Check(!report.ClientAdmissionAllowed && !report.CredentialOperationsAllowed);
        Check(report.Authorization == "NOT AUTHORIZED" && report.ReleaseDisposition == "HOLD" &&
            report.Reason.StartsWith("Not safe:", StringComparison.Ordinal));
    }

    private static void Reject(Action transition)
    {
        bool rejected = false;
        try { transition(); } catch (InvalidOperationException) { rejected = true; }
        Check(rejected);
    }

    private static void TerminalReplay(LifecycleCoordinator core, LifecycleState expected)
    {
        Reject(core.BeginStart);
        Reject(core.CompleteStart);
        core.Stop(); core.Fault();
        Check(core.Observe().State == expected);
        Denied(core);
        core.Dispose(); core.Dispose(); core.Stop(); core.Fault();
        Reject(core.BeginStart);
        Check(core.Observe().State == LifecycleState.Disposed);
        Denied(core);
    }

    private static int Main(string[] args)
    {
        try
        {
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Check(args.Length == 1 && IntPtr.Size * 8 == int.Parse(args[0]));
            using (var core = new LifecycleCoordinator())
            {
                ServiceReadiness original = core.Observe();
                Check(original.State == LifecycleState.Created); Denied(core);
                core.BeginStart(); Check(core.Observe().State == LifecycleState.Starting); Denied(core);
                core.CompleteStart(); Check(core.Observe().State == LifecycleState.ActiveDenied); Denied(core);
                Check(original.State == LifecycleState.Created); // Snapshot cannot change with owner.
                core.Stop(); TerminalReplay(core, LifecycleState.Stopped);
            }
            using (var core = new LifecycleCoordinator())
            { Reject(core.CompleteStart); TerminalReplay(core, LifecycleState.Faulted); }
            using (var core = new LifecycleCoordinator())
            { core.BeginStart(); Reject(core.BeginStart); TerminalReplay(core, LifecycleState.Faulted); }
            using (var core = new LifecycleCoordinator())
            { core.BeginStart(); core.CompleteStart(); Reject(core.CompleteStart); TerminalReplay(core, LifecycleState.Faulted); }
            using (var core = new LifecycleCoordinator())
            { core.Stop(); TerminalReplay(core, LifecycleState.Stopped); }
            using (var core = new LifecycleCoordinator())
            { core.BeginStart(); core.Fault(); TerminalReplay(core, LifecycleState.Faulted); }

            // Exercise the real product assembly, not a copied synthetic coordinator.
            for (int round = 0; round < 20; round++)
            using (var core = new LifecycleCoordinator())
            {
                core.BeginStart(); core.CompleteStart();
                Task deny = Task.Run(delegate {
                    for (int i = 0; i < 1000; i++)
                        if (core.DenyClientAdmission() || core.DenyCredentialOperation())
                            throw new Exception("Positive operation forbidden.");
                });
                Task stop = Task.Run(delegate { core.Stop(); });
                Task fault = Task.Run(delegate { core.Fault(); });
                Task dispose = Task.Run(delegate { core.Dispose(); });
                Check(Task.WaitAll(new[] { deny, stop, fault, dispose }, 5000));
                Check(core.Observe().State == LifecycleState.Disposed);
                Reject(core.BeginStart); Denied(core);
            }

            // No instance, OnStart or SCM invocation. Require a genuine negative OS context
            // before invoking the product Main with no arguments. No env flags grant access.
            using (Process self = Process.GetCurrentProcess())
                Check(Environment.UserInteractive || self.SessionId != 0);
            Type host = typeof(LifecycleCoordinator).Assembly.GetType("Nayeon.ByokC1.Service.CustodyService", true);
            MethodInfo main = host.GetMethod("Main", BindingFlags.NonPublic | BindingFlags.Static);
            Check(main != null);
            Check((int)main.Invoke(null, new object[] { new string[0] }) == 1);
            Check((int)main.Invoke(null, new object[] { new[] { "unauthorized" } }) == 1);
            Check((int)main.Invoke(null, new object[] { null }) == 1);
            Console.WriteLine("P304 PASS checks=" + checks + " bits=" + IntPtr.Size * 8 +
                "; compile + isolated runtime denial only; release HOLD");
            return 0;
        }
        catch (Exception) { Console.Error.WriteLine("P304 FAIL; release HOLD"); return 1; }
    }
}
