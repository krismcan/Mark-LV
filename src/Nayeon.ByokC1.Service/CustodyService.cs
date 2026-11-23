using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.ServiceProcess;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1.Service
{
    internal sealed class CustodyService : ServiceBase
    {
        internal const string ProductServiceName = "NayeonV1ByokCustody";
        private readonly object lifecycle = new object();
        private readonly LifecycleCoordinator coordinator = new LifecycleCoordinator();
        private bool terminal;
        private StatusPipeServer statusPipe;
        private SyntheticTransactionOwner transactions;

        private CustodyService()
        {
            ServiceName = ProductServiceName;
            AutoLog = false;
            CanStop = true;
            CanShutdown = true;
            ExitCode = 1;
        }

        private sealed class TokenHandle : SafeHandleZeroOrMinusOneIsInvalid
        {
            public TokenHandle() : base(true) { }
            protected override bool ReleaseHandle() { return CloseHandle(handle); }
        }

        [DllImport("kernel32.dll", ExactSpelling = true)]
        private static extern IntPtr GetCurrentProcess();
        [DllImport("kernel32.dll", ExactSpelling = true)]
        private static extern IntPtr GetCurrentThread();
        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenProcessToken(IntPtr process, uint access, out TokenHandle token);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenThreadToken(IntPtr thread, uint access,
            [MarshalAs(UnmanagedType.Bool)] bool openAsSelf, out TokenHandle token);
        [DllImport("advapi32.dll", ExactSpelling = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool IsTokenRestricted(TokenHandle token);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetTokenInformation(TokenHandle token, int kind,
            out int value, uint length, out uint returned);

        internal static void RequireNoImpersonation()
        {
            TokenHandle thread;
            bool opened = OpenThreadToken(GetCurrentThread(), 8, true, out thread);
            int error = Marshal.GetLastWin32Error();
            using (thread)
            {
                // Only ERROR_NO_TOKEN passes. Anonymous/denied tokens cannot fall back.
                if (opened || error != 1008 || (thread != null && !thread.IsInvalid))
                    throw new InvalidOperationException("Service identity denied.");
            }
        }

        internal static SecurityIdentifier ReadProcessSid()
        {
            RequireNoImpersonation();
            TokenHandle token;
            if (!OpenProcessToken(GetCurrentProcess(), 8, out token))
            {
                if (token != null) token.Dispose();
                throw new InvalidOperationException("Process identity unavailable.");
            }
            using (token)
            using (WindowsIdentity identity = new WindowsIdentity(token.DangerousGetHandle()))
            {
                if (identity.User == null) throw new InvalidOperationException("Process identity denied.");
                SecurityIdentifier sid = identity.User;
                RequireNoImpersonation();
                return sid;
            }
        }

        private static void RequireSessionZero()
        {
            if (Environment.OSVersion.Platform != PlatformID.Win32NT || Environment.UserInteractive)
                throw new InvalidOperationException("Service dispatch required.");
            using (Process process = Process.GetCurrentProcess())
                if (process.SessionId != 0) throw new InvalidOperationException("Session zero required.");
        }

        private static void VerifyExecutingIdentity()
        {
            RequireSessionZero();
            RequireNoImpersonation();
            TokenHandle token;
            if (!OpenProcessToken(GetCurrentProcess(), 8, out token))
            {
                if (token != null) token.Dispose();
                throw new InvalidOperationException("Process token unavailable.");
            }
            using (token)
            {
                if (token == null || token.IsInvalid) throw new InvalidOperationException("Process token denied.");
                int session, type;
                uint returned;
                if (!GetTokenInformation(token, 12, out session, 4, out returned) || returned != 4 || session != 0 ||
                    !GetTokenInformation(token, 8, out type, 4, out returned) || returned != 4 || type != 1)
                    throw new InvalidOperationException("Primary session-zero token required.");
                // TokenUser is read from our process token, never the effective thread identity.
                using (WindowsIdentity identity = new WindowsIdentity(token.DangerousGetHandle()))
                {
                    SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE", ProductServiceName)
                        .Translate(typeof(SecurityIdentifier));
                    if (identity.User == null || identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                        !identity.User.Equals(expected) || !IsTokenRestricted(token))
                        throw new InvalidOperationException("Restricted product service identity required.");
                }
                RequireNoImpersonation();
            }
        }

        protected override void OnStart(string[] args)
        {
            lock (lifecycle)
            {
                try
                {
                    if (terminal || args == null || args.Length != 0 || ServiceHandle == IntPtr.Zero)
                        throw new InvalidOperationException("Service startup denied.");
                    VerifyExecutingIdentity();
                    VerifyExecutingIdentity(); // Reopen and verify before any domain transition.
                    coordinator.BeginStart();
                    transactions = new SyntheticTransactionOwner(); // Identity-validated service ownership only.
                    statusPipe = new StatusPipeServer(); // Only after both executing-identity checks.
                    coordinator.CompleteStart(); // IPC reports denial only, never readiness authority.
                    ExitCode = 0; // Only after the SCM callback and OS checks, never readiness approval.
                }
                catch (Exception)
                {
                    terminal = true;
                    if (transactions != null) transactions.Fault();
                    coordinator.Fault();
                    ExitCode = 1;
                    if (statusPipe != null) statusPipe.Dispose();
                    throw new InvalidOperationException("Service startup denied; release HOLD.");
                }
            }
        }

        internal SyntheticTransactionResult RefuseSyntheticRequest(SyntheticTransactionRequest request)
        {
            lock (lifecycle)
            {
                if (!terminal && coordinator.Observe().State == LifecycleState.ActiveDenied && transactions != null)
                    return transactions.Deny(request);
                // No owner access or sequence reservation when the service gate refuses.
                return new SyntheticTransactionResult(request, Guid.Empty, 0,
                    TransactionOwnerState.Stopped, TransactionDisposition.OwnerTerminated);
            }
        }

        internal SyntheticTransactionResult CancelSyntheticRequest(SyntheticTransactionRequest request)
        {
            lock (lifecycle)
            {
                if (!terminal && coordinator.Observe().State == LifecycleState.ActiveDenied && transactions != null)
                    return transactions.Cancel(request);
                return new SyntheticTransactionResult(request, Guid.Empty, 0,
                    TransactionOwnerState.Stopped, TransactionDisposition.OwnerTerminated);
            }
        }

        private void Close(bool disposing, bool shutdown)
        {
            lock (lifecycle)
            {
                terminal = true;
                // Cancel before pipe cleanup, even if that cleanup throws or times out.
                if (transactions != null)
                {
                    if (disposing) transactions.Dispose();
                    else if (shutdown) transactions.Shutdown();
                    else transactions.Stop();
                }
                try { if (statusPipe != null) statusPipe.Dispose(); }
                finally
                {
                    coordinator.Stop();
                    if (disposing) coordinator.Dispose();
                }
            }
        }

        protected override void OnStop() { Close(false, false); }
        protected override void OnShutdown() { Close(false, true); }
        protected override void Dispose(bool disposing)
        {
            lock (lifecycle)
            {
                // The metadata owner also closes on the non-managed disposal path.
                terminal = true;
                if (transactions != null) transactions.Dispose();
                try { if (disposing) Close(true, false); } finally { base.Dispose(disposing); }
            }
        }

        private static int Main(string[] args)
        {
            try
            {
                if (args == null || args.Length != 0) return 1;
                RequireSessionZero();
                using (CustodyService service = new CustodyService()) ServiceBase.Run(service);
                return 1; // Dispatch returning is never release acceptance or authorization.
            }
            catch (Exception) { return 1; } // No logger, identity output or credential material.
        }
    }
}
