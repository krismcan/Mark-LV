#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY || !C1_P301_DISPATCHER_OWNER_ONLY
#error P301_DEBUG_ISOLATED_DEVELOPMENT_DISPATCHER_OWNER_ONLY_REQUIRED
#endif
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text.RegularExpressions;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P269Development;

namespace Nayeon.ByokC1.P301Development
{
    // NONDEPLOYABLE synthetic owner. Compile /main:Nayeon.ByokC1.P301Development.P301DispatcherOwnedSyntheticService.
    // Runtime barriers are neither privilege nor code-provenance proof. No request/admission surface.
    internal sealed class P301DispatcherOwnedSyntheticService : ServiceBase
    {
        private readonly object lifecycle = new object();
        private readonly string expectedServiceName;
        private ComposedDevelopmentService owner;
        private bool started, terminal;
        internal static bool ClientAdmissionAllowed { get { return false; } }
        internal static bool CredentialEffectAllowed { get { return false; } }
        internal static bool ProductionEligible { get { return false; } }

        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        private static extern bool IsTokenRestricted(IntPtr token);

        private P301DispatcherOwnedSyntheticService(string name)
        {
            expectedServiceName = name;
            ServiceName = name;
            AutoLog = false; CanStop = true; CanShutdown = true;
            // A single ServiceBase.Run(service) supplies the own-process dispatcher shape.
            ExitCode = 1;
        }
        private void VerifyIdentity()
        {
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE", expectedServiceName)
                    .Translate(typeof(SecurityIdentifier));
                if (identity.ImpersonationLevel != TokenImpersonationLevel.None || identity.User == null ||
                    identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid) || !identity.User.Equals(expected))
                    throw new InvalidOperationException("P301_START_DENIED");
                if (!IsTokenRestricted(identity.Token))
                    throw new InvalidOperationException("P301_START_DENIED");
            }
        }
        protected override void OnStart(string[] args)
        {
            lock (lifecycle)
            {
                try
                {
                    if (terminal || started) throw new InvalidOperationException("P301_START_DENIED");
                    VerifyIdentity(); // Synchronous; no construction/worker before exact identity verification.
                    owner = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, true);
                    owner.TestAdapter.Inject = null;
                    if (!owner.StartDevelopment()) throw new InvalidOperationException("P301_START_DENIED");
                    started = true;
                }
                catch (Exception)
                {
                    Close();
                    throw new InvalidOperationException("P301_START_DENIED");
                }
            }
        }
        private void Close()
        {
            lock (lifecycle)
            {
                terminal = true; ExitCode = 1;
                ComposedDevelopmentService closing = owner;
                owner = null; // Single ownership transfer; no retry/rearm even if cleanup throws.
                if (closing != null)
                    try { closing.StopDevelopment(); }
                    finally { closing.Dispose(); }
            }
        }
        protected override void OnStop() { Close(); }
        protected override void OnShutdown() { Close(); }
        protected override void Dispose(bool disposing)
        { try { if (disposing) Close(); } finally { base.Dispose(disposing); } }

        // No test-call entry or externally supplied synthetic operation. Only the dispatcher invokes OnStart.
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
                // Includes dispatcher/identity/worker startup. Managed deadline is not OS kill-proof evidence.
                using (Timer deadline = new Timer(delegate { Environment.Exit(1); }, null, 55000, Timeout.Infinite))
                using (var service = new P301DispatcherOwnedSyntheticService(args[1]))
                {
                    ServiceBase.Run(service);
                    return 1; // Terminal synthetic witness always fails closed; never productive success.
                }
            }
            catch (Exception) { return 1; } // No identity-bearing output or event logging.
        }
    }
}
