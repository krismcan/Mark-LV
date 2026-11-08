// P114 — real Windows pipe CLIENT PROCESS provenance (review-only).
// OS process ID and loaded executable image name are obtained from kernel32,
// NOT caller-supplied PID/SID/path/session/digest/approval. A kernel process
// handle is held across PID, image, token SID and creation-time observation.
// Distinct from P113's Windows impersonated pipe client token signal.
// NEITHER signal attests a signed consent UI, a human click or a one-use grant.
// No WinCred, effect adapter, service listener or local installation here.
using System;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1
{
    internal enum OsPipeClientProcessState
    {
        Unavailable,
        OsKernelProcessObserved
    }

    internal sealed class OsPipeClientProcessProvenance
    {
        internal readonly OsPipeClientProcessState State;
        internal readonly uint OsClientProcessId;
        internal readonly string OsImagePath;
        internal readonly long OsProcessCreatedUtcFileTime;
        internal readonly string OsProcessTokenSid;

        internal OsPipeClientProcessProvenance(
            OsPipeClientProcessState state, uint pid, string imagePath,
            long createdUtcFileTime, string processTokenSid)
        {
            State = state;
            OsClientProcessId = pid;
            OsImagePath = imagePath;
            OsProcessCreatedUtcFileTime = createdUtcFileTime;
            OsProcessTokenSid = processTokenSid;
        }

        internal bool KernelProcessObserved
        { get { return State == OsPipeClientProcessState.OsKernelProcessObserved; } }

        // These always remain false, even for a real OS client process.
        internal bool SignedTrustedConsentImageVerified { get { return false; } }
        internal bool InteractiveUserSessionVerified { get { return false; } }
        internal bool ExplicitHumanConsentVerified { get { return false; } }
        internal bool ProtectedOneUseGrantIssued { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }

        public override string ToString()
        { return "<P114 OS process provenance only; trusted consent unavailable>"; }

        internal static OsPipeClientProcessProvenance Unavailable()
        {
            return new OsPipeClientProcessProvenance(
                OsPipeClientProcessState.Unavailable, 0, null, 0, null);
        }
    }

    internal static class WindowsPipeClientProcessProvenance
    {
        // Windows PROCESS_QUERY_LIMITED_INFORMATION, NOT VM_READ/WRITE,
        // DUP_HANDLE, CREATE_THREAD, PROCESS_ALL_ACCESS or privilege enable.
        private const uint ProcessQueryLimitedInformation = 0x1000;
        private const uint TokenQuery = 0x0008;
        private const int MaxImageChars = 32768;

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetNamedPipeClientProcessId(
            SafePipeHandle pipeHandle, out uint clientProcessId);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        private static extern IntPtr OpenProcess(
            uint desiredAccess, [MarshalAs(UnmanagedType.Bool)] bool inherit,
            uint processId);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        private static extern uint GetProcessId(IntPtr processHandle);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true,
            CharSet=CharSet.Unicode, EntryPoint="QueryFullProcessImageNameW")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool QueryFullProcessImageName(
            IntPtr processHandle, uint flags,
            StringBuilder imageName, ref uint imageNameLength);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetProcessTimes(
            IntPtr processHandle, out long creationTime,
            out long exitTime, out long kernelTime, out long userTime);

        [DllImport("advapi32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenProcessToken(
            IntPtr processHandle, uint desiredAccess, out IntPtr tokenHandle);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);

        // This review helper MUST NOT become a production authority:
        // an image's path is mutable on disk; no WinVerifyTrust, publisher
        // pin, signed installation, handle-to-file identity, session/user
        // interaction, or durable grant is established.
        internal static OsPipeClientProcessProvenance ObserveAfterClientWrite(
            NamedPipeServerStream connectedServerPipe)
        {
            if (connectedServerPipe == null)
                return OsPipeClientProcessProvenance.Unavailable();

            IntPtr processHandle = IntPtr.Zero;
            IntPtr tokenHandle = IntPtr.Zero;
            try
            {
                if (!connectedServerPipe.IsConnected)
                    return OsPipeClientProcessProvenance.Unavailable();

                OsPipePeerObservation peer =
                    WindowsPipePeerObservation.ObserveAfterClientWrite(
                        connectedServerPipe);
                if (peer == null || !peer.OsClientTokenObserved ||
                    String.IsNullOrWhiteSpace(peer.OsClientSid))
                    return OsPipeClientProcessProvenance.Unavailable();

                uint pipeClientPid;
                if (!GetNamedPipeClientProcessId(
                    connectedServerPipe.SafePipeHandle, out pipeClientPid) ||
                    pipeClientPid == 0)
                    return OsPipeClientProcessProvenance.Unavailable();

                processHandle = OpenProcess(
                    ProcessQueryLimitedInformation, false, pipeClientPid);
                if (processHandle == IntPtr.Zero ||
                    processHandle == new IntPtr(-1))
                    return OsPipeClientProcessProvenance.Unavailable();

                // Holding a real process HANDLE prevents PID reuse while
                // validating this particular live process instance.
                if (GetProcessId(processHandle) != pipeClientPid)
                    return OsPipeClientProcessProvenance.Unavailable();

                if (!OpenProcessToken(
                    processHandle, TokenQuery, out tokenHandle) ||
                    tokenHandle == IntPtr.Zero ||
                    tokenHandle == new IntPtr(-1))
                    return OsPipeClientProcessProvenance.Unavailable();

                using (WindowsIdentity processToken =
                    new WindowsIdentity(tokenHandle))
                {
                    if (processToken.User == null ||
                        !String.Equals(processToken.User.Value,
                            peer.OsClientSid, StringComparison.Ordinal))
                        return OsPipeClientProcessProvenance.Unavailable();
                }

                uint length = MaxImageChars;
                StringBuilder path = new StringBuilder(MaxImageChars);
                if (!QueryFullProcessImageName(processHandle, 0, path,
                    ref length) || length == 0 || length >= MaxImageChars)
                    return OsPipeClientProcessProvenance.Unavailable();
                string image = path.ToString();
                if (String.IsNullOrWhiteSpace(image) ||
                    !Path.IsPathRooted(image))
                    return OsPipeClientProcessProvenance.Unavailable();

                long created, exited, kernel, user;
                if (!GetProcessTimes(processHandle, out created, out exited,
                    out kernel, out user) || created <= 0)
                    return OsPipeClientProcessProvenance.Unavailable();
                // Validate creation file time without trusting a caller clock.
                DateTime.FromFileTimeUtc(created);

                uint finalPipePid;
                if (!connectedServerPipe.IsConnected ||
                    !GetNamedPipeClientProcessId(
                        connectedServerPipe.SafePipeHandle, out finalPipePid) ||
                    finalPipePid != pipeClientPid ||
                    GetProcessId(processHandle) != pipeClientPid)
                    return OsPipeClientProcessProvenance.Unavailable();

                return new OsPipeClientProcessProvenance(
                    OsPipeClientProcessState.OsKernelProcessObserved,
                    pipeClientPid, image, created, peer.OsClientSid);
            }
            catch (Exception)
            {
                return OsPipeClientProcessProvenance.Unavailable();
            }
            finally
            {
                if (tokenHandle != IntPtr.Zero &&
                    tokenHandle != new IntPtr(-1))
                    CloseHandle(tokenHandle);
                if (processHandle != IntPtr.Zero &&
                    processHandle != new IntPtr(-1))
                    CloseHandle(processHandle);
            }
        }
    }
}
