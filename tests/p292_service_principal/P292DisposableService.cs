#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P292_EPHEMERAL_SCM_ONLY
#error P292_DEBUG_ISOLATED_EPHEMERAL_ONLY
#endif
using System;
using System.Diagnostics;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text.RegularExpressions;
using System.Threading;

// TEST ONLY. SCM supplies its own environment, not the workflow job environment.
// The guarded orchestrator supplies these fixed mode arguments in ImagePath.
// Arguments are accident barriers, NOT authentication or installation provenance.
// No IPC, files, network, credential/store API, product code or user payload.
internal sealed class P292DisposableService : ServiceBase
{
    private P292DisposableService(string name)
    {
        ServiceName = name;
        AutoLog = false;
        CanStop = true;
        CanShutdown = false;
    }
    protected override void OnStart(string[] args) { /* No protected work. */ }
    protected override void OnStop() { /* Run returns and Main disposes. */ }
    private static int Main(string[] args)
    {
        try
        {
            if (args.Length != 4 || args[0] != "P292_DISPOSABLE_SCM_WITNESS=1" ||
                !Regex.IsMatch(args[1], "\\ANayeonP292_[0-9a-f]{12}\\z") ||
                args[2] != "4f4f4fe4d2c0afb5afc1acec48dae1b463fb4d9f" ||
                !Regex.IsMatch(args[3], "\\A[0-9a-f]{40}\\z") ||
                Environment.OSVersion.Platform != PlatformID.Win32NT || Environment.UserInteractive ||
                Process.GetCurrentProcess().SessionId != 0) return 1;
            // Hard lifetime covers identity lookup and dispatcher startup too.
            using (Timer deadline = new Timer(delegate { Environment.Exit(1); }, null, 55000, Timeout.Infinite))
            {
                using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
                {
                    SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE", args[1])
                        .Translate(typeof(SecurityIdentifier));
                    if (identity.ImpersonationLevel != TokenImpersonationLevel.None || identity.User == null ||
                        identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                        !identity.User.Equals(expected)) return 1;
                }
                using (P292DisposableService service = new P292DisposableService(args[1]))
                    ServiceBase.Run(service);
            }
            return 0;
        }
        catch (Exception) { return 1; } // No identity-bearing exception output/event log.
    }
}
