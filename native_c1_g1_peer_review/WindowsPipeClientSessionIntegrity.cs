// P115 review-only Windows pipe-client SESSION + token INTEGRITY observation.
// Only accepts an already-connected pipe. Reuses P113/P114 OS observations,
// then independently compares kernel pipe session to process token session.
// PID+creation-time+SID are reverified after reopening a query-only handle.
// These signals NEVER establish an installed signed consent UI, a click,
// trusted desktop state, a one-use grant, or credential-effect authority.
using System;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.Principal;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1
{
    internal enum OsPipeClientSessionIntegrityState
    {
        Unavailable,
        OsTokenSessionIntegrityObserved
    }

    internal sealed class OsPipeClientSessionIntegrity
    {
        internal readonly OsPipeClientSessionIntegrityState State;
        internal readonly uint OsClientProcessId;
        internal readonly uint OsPipeSessionId;
        internal readonly uint OsTokenSessionId;
        internal readonly uint OsTokenIntegrityRid;
        internal readonly long OsProcessCreatedUtcFileTime;

        internal OsPipeClientSessionIntegrity(
            OsPipeClientSessionIntegrityState state, uint pid,
            uint pipeSession, uint tokenSession, uint integrityRid,
            long createdUtcFileTime)
        {
            State = state;
            OsClientProcessId = pid;
            OsPipeSessionId = pipeSession;
            OsTokenSessionId = tokenSession;
            OsTokenIntegrityRid = integrityRid;
            OsProcessCreatedUtcFileTime = createdUtcFileTime;
        }

        internal bool SessionIntegrityObserved
        { get { return State == OsPipeClientSessionIntegrityState.OsTokenSessionIntegrityObserved; } }

        // Observing a session and integrity label is NOT a trust decision.
        internal bool TrustedInteractiveDesktopVerified { get { return false; } }
        internal bool SignedTrustedConsentImageVerified { get { return false; } }
        internal bool ExplicitHumanConsentVerified { get { return false; } }
        internal bool ProtectedOneUseGrantIssued { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }

        internal static OsPipeClientSessionIntegrity Unavailable()
        {
            return new OsPipeClientSessionIntegrity(
                OsPipeClientSessionIntegrityState.Unavailable, 0, 0, 0, 0, 0);
        }

        public override string ToString()
        { return "<P115 Windows process session/integrity observed only; no consent authority>"; }
    }

    internal static class WindowsPipeClientSessionIntegrity
    {
        private const uint ProcessQueryLimitedInformation = 0x1000;
        private const uint TokenQuery = 0x0008;
        // Windows TOKEN_INFORMATION_CLASS values.
        private const int TokenSessionId = 12;
        private const int TokenIntegrityLevel = 25;
        private const int MaxIntegrityInfoSize = 4096;

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetNamedPipeClientProcessId(
            SafePipeHandle pipeHandle, out uint clientProcessId);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetNamedPipeClientSessionId(
            SafePipeHandle pipeHandle, out uint clientSessionId);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        private static extern IntPtr OpenProcess(
            uint desiredAccess, [MarshalAs(UnmanagedType.Bool)] bool inherit,
            uint processId);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        private static extern uint GetProcessId(IntPtr processHandle);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetProcessTimes(
            IntPtr processHandle, out long creationTime,
            out long exitTime, out long kernelTime, out long userTime);

        [DllImport("advapi32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenProcessToken(
            IntPtr processHandle, uint access, out IntPtr tokenHandle);

        [DllImport("advapi32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetTokenInformation(
            IntPtr tokenHandle, int informationClass, IntPtr information,
            int informationLength, out int returnedLength);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);

        private static bool IsHandle(IntPtr h)
        { return h != IntPtr.Zero && h != new IntPtr(-1); }

        private static bool TryReadSession(IntPtr token, out uint session)
        {
            session = 0;
            IntPtr data = IntPtr.Zero;
            try
            {
                data = Marshal.AllocHGlobal(sizeof(int));
                int returned;
                if (!GetTokenInformation(token, TokenSessionId, data,
                    sizeof(int), out returned) || returned != sizeof(int))
                    return false;
                session = unchecked((uint)Marshal.ReadInt32(data));
                return true; // Session zero is valid on Windows.
            }
            finally
            {
                if (data != IntPtr.Zero) Marshal.FreeHGlobal(data);
            }
        }

        private static bool TryReadIntegrity(IntPtr token, out uint rid)
        {
            rid = 0;
            int needed;
            // First call retrieves required size, not a positive result.
            GetTokenInformation(token, TokenIntegrityLevel, IntPtr.Zero,
                0, out needed);
            if (needed < IntPtr.Size + sizeof(int) ||
                needed > MaxIntegrityInfoSize)
                return false;
            IntPtr data = IntPtr.Zero;
            try
            {
                data = Marshal.AllocHGlobal(needed);
                int returned;
                if (!GetTokenInformation(token, TokenIntegrityLevel, data,
                    needed, out returned) || returned < IntPtr.Size + sizeof(int) ||
                    returned > needed)
                    return false;
                // TOKEN_MANDATORY_LABEL begins with SID_AND_ATTRIBUTES;
                // its first field is an OS-owned pointer to the integrity SID.
                IntPtr sidPtr = Marshal.ReadIntPtr(data);
                if (sidPtr == IntPtr.Zero) return false;
                string sid = new SecurityIdentifier(sidPtr).Value;
                if (!sid.StartsWith("S-1-16-", StringComparison.Ordinal))
                    return false;
                string last = sid.Substring("S-1-16-".Length);
                if (!UInt32.TryParse(last, out rid) || rid > 32768)
                    return false;
                return true;
            }
            finally
            {
                if (data != IntPtr.Zero) Marshal.FreeHGlobal(data);
            }
        }

        internal static OsPipeClientSessionIntegrity ObserveAfterClientWrite(
            NamedPipeServerStream connectedServerPipe)
        {
            if (connectedServerPipe == null)
                return OsPipeClientSessionIntegrity.Unavailable();

            IntPtr process = IntPtr.Zero;
            IntPtr token = IntPtr.Zero;
            try
            {
                if (!connectedServerPipe.IsConnected)
                    return OsPipeClientSessionIntegrity.Unavailable();

                OsPipeClientProcessProvenance baseIdentity =
                    WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(
                        connectedServerPipe);
                if (baseIdentity == null || !baseIdentity.KernelProcessObserved ||
                    String.IsNullOrWhiteSpace(baseIdentity.OsProcessTokenSid))
                    return OsPipeClientSessionIntegrity.Unavailable();

                uint pipeSession, pipePid;
                if (!GetNamedPipeClientSessionId(
                    connectedServerPipe.SafePipeHandle, out pipeSession) ||
                    !GetNamedPipeClientProcessId(
                    connectedServerPipe.SafePipeHandle, out pipePid) ||
                    pipePid == 0 || pipePid != baseIdentity.OsClientProcessId)
                    return OsPipeClientSessionIntegrity.Unavailable();

                process = OpenProcess(ProcessQueryLimitedInformation, false, pipePid);
                if (!IsHandle(process) || GetProcessId(process) != pipePid)
                    return OsPipeClientSessionIntegrity.Unavailable();

                long created, exited, kernel, user;
                if (!GetProcessTimes(process, out created, out exited,
                    out kernel, out user) ||
                    created != baseIdentity.OsProcessCreatedUtcFileTime)
                    return OsPipeClientSessionIntegrity.Unavailable();

                if (!OpenProcessToken(process, TokenQuery, out token) ||
                    !IsHandle(token))
                    return OsPipeClientSessionIntegrity.Unavailable();

                using (WindowsIdentity identity = new WindowsIdentity(token))
                {
                    if (identity.User == null ||
                        !String.Equals(identity.User.Value,
                            baseIdentity.OsProcessTokenSid, StringComparison.Ordinal))
                        return OsPipeClientSessionIntegrity.Unavailable();
                }

                uint tokenSession, integrityRid;
                if (!TryReadSession(token, out tokenSession) ||
                    !TryReadIntegrity(token, out integrityRid) ||
                    pipeSession != tokenSession)
                    return OsPipeClientSessionIntegrity.Unavailable();

                uint finalPid, finalSession;
                if (!connectedServerPipe.IsConnected ||
                    !GetNamedPipeClientProcessId(
                        connectedServerPipe.SafePipeHandle, out finalPid) ||
                    !GetNamedPipeClientSessionId(
                        connectedServerPipe.SafePipeHandle, out finalSession) ||
                    finalPid != pipePid || finalSession != pipeSession ||
                    GetProcessId(process) != pipePid)
                    return OsPipeClientSessionIntegrity.Unavailable();

                return new OsPipeClientSessionIntegrity(
                    OsPipeClientSessionIntegrityState.OsTokenSessionIntegrityObserved,
                    pipePid, pipeSession, tokenSession, integrityRid, created);
            }
            catch (Exception)
            {
                return OsPipeClientSessionIntegrity.Unavailable();
            }
            finally
            {
                if (IsHandle(token)) CloseHandle(token);
                if (IsHandle(process)) CloseHandle(process);
            }
        }
    }
}
