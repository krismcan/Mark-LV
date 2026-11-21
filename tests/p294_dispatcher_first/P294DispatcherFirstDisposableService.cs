#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P294_DISPATCHER_FIRST_ONLY
#error P294_DEBUG_ISOLATED_DISPATCHER_FIRST_ONLY_REQUIRED
#endif
using System;
using System.Diagnostics;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text.RegularExpressions;
using System.Threading;

// NONDEPLOYABLE REVIEW CANDIDATE. No installer, product integration or self-test.
// Retain the frozen P292 ImagePath argument contract for equivalence review.
// Arguments/session are accident barriers, NOT SCM or installation authentication.
internal sealed class P294DispatcherFirstDisposableService : ServiceBase
{
    private readonly string expectedServiceName;
    private bool startIdentityVerified;

    private P294DispatcherFirstDisposableService(string name)
    {
        expectedServiceName = name;
        ServiceName = name;
        AutoLog = false;
        CanStop = true;
        CanShutdown = false;
    }

    protected override void OnStart(string[] args)
    {
        try
        {
            // Synchronous, after dispatcher registration, before successful OnStart.
            // Same virtual-account SID, non-LocalSystem and impersonation guards.
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE", expectedServiceName)
                    .Translate(typeof(SecurityIdentifier));
                if (identity.ImpersonationLevel != TokenImpersonationLevel.None || identity.User == null ||
                    identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                    !identity.User.Equals(expected)) throw new InvalidOperationException("P294_START_DENIED");
            }
            startIdentityVerified = true;
        }
        catch (Exception)
        {
            // Do not propagate identity-bearing exception messages or inner exceptions.
            throw new InvalidOperationException("P294_START_DENIED");
        }
        // No protected work, admission token, callback or identity-bearing output.
    }

    protected override void OnStop() { /* Run returns and Main disposes. */ }

    private static int Main(string[] args)
    {
        try
        {
            if (args == null || args.Length != 4 || args[0] != "P292_DISPOSABLE_SCM_WITNESS=1" ||
                args[1] == null || args[1].Length != 23 ||
                !Regex.IsMatch(args[1], "\\ANayeonP292_[0-9a-f]{12}\\z") ||
                args[2] != "4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f" ||
                args[3] == null || args[3].Length != 40 ||
                !Regex.IsMatch(args[3], "\\A[0-9a-f]{40}\\z") ||
                Environment.OSVersion.Platform != PlatformID.Win32NT || Environment.UserInteractive) return 1;
            using (Process current = Process.GetCurrentProcess())
                if (current.SessionId != 0) return 1;
            // Unchanged 55s deadline includes constructor, dispatcher and OnStart lookup.
            // A managed timer is not an OS kill-proof guarantee.
            using (Timer deadline = new Timer(delegate { Environment.Exit(1); }, null, 55000, Timeout.Infinite))
            using (P294DispatcherFirstDisposableService service = new P294DispatcherFirstDisposableService(args[1]))
            {
                // Only SCM dispatcher registration may cause OnStart; never call it here.
                ServiceBase.Run(service);
                return service.startIdentityVerified ? 0 : 1;
            }
        }
        catch (Exception) { return 1; } // No exception output/event log.
    }
}
