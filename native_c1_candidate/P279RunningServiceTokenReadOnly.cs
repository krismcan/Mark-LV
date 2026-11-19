// P279 isolated observation only; never admission or a deployable service.
// Prior-issues review (2026-11-19): HIGH P261 config != runtime token;
// P215 observes its reviewer only. This new route contains that evidence gap.
// HIGH LocalSystem/virtual-account conflict, SEC03/04 and 0/7 approvals OPEN.
// Original P96/P76/P216/native-adapter failures remain OPEN, unchanged.
// GO bounded source review only; HOLD all effects, seals and production.
// Hosted absence tests and independent Nayeon review remain required.
// No image/FileId/signer, protected vault, IPC or consent proof is supplied.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P279_RUNTIME_TOKEN_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;

namespace Nayeon.ByokC1
{
    internal enum P279RuntimeTokenStatus
    {
        Missing, ConfigUnverified, NotRunning, SharedProcess, TokenDenied,
        TokenMismatch, Unverified, RuntimeTokenObserved
    }

    internal sealed class P279RuntimeTokenEvidence
    {
        internal readonly P279RuntimeTokenStatus Status;
        internal readonly bool ConfigObserved, ServiceOpened, ProcessOpened,
            TokenOpened, TokenUserMatchesServiceSid, RuntimeStatusRechecked;

        internal P279RuntimeTokenEvidence(P279RuntimeTokenStatus status,
            bool config, bool service, bool process, bool token, bool matches, bool rechecked)
        {
            Status = status; ConfigObserved = config; ServiceOpened = service;
            ProcessOpened = process; TokenOpened = token;
            TokenUserMatchesServiceSid = matches; RuntimeStatusRechecked = rechecked;
        }
        internal bool QualifiedSecurityDecisionApproved { get { return false; } }
        internal bool ApprovedServicePrincipal { get { return false; } }
        internal bool ProtectedCredentialOwner { get { return false; } }
        internal bool TrustedConsent { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }
        internal bool RealKeyEligible { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }
        public override string ToString() { return "<P279 observation only; DENY; HOLD>"; }
    }

    internal static class P279RunningServiceTokenReadOnly
    {
        private const int StatusBytes = 36, MaximumSidBytes = 68, MaximumDomainChars = 256;
        private const uint SC_MANAGER_CONNECT = 1, SERVICE_QUERY_STATUS = 4;
        private const uint PROCESS_QUERY_LIMITED_INFORMATION = 0x1000, TOKEN_QUERY = 8;

        [StructLayout(LayoutKind.Sequential, Pack = 4)]
        internal struct ServiceStatusProcess
        {
            internal uint ServiceType, CurrentState, ControlsAccepted, Win32ExitCode,
                ServiceSpecificExitCode, CheckPoint, WaitHint, ProcessId, ServiceFlags;
        }
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        private static extern IntPtr OpenSCManagerW(string machine, string database, uint access);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        private static extern IntPtr OpenServiceW(IntPtr manager, string name, uint access);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool QueryServiceStatusEx(IntPtr service, uint level,
            IntPtr buffer, uint size, out uint needed);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseServiceHandle(IntPtr handle);
        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
        private static extern IntPtr OpenProcess(uint access,
            [MarshalAs(UnmanagedType.Bool)] bool inherit, uint processId);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool LookupAccountNameW(string system, string account,
            IntPtr sid, ref uint sidBytes, IntPtr domain, ref uint domainChars, out uint use);

        // Pure parser/classifier. A true result permits only a read-only probe.
        // QueryServiceStatusEx docs: pending/stopped PIDs cannot be relied on.
        internal static bool TryParseStatus(IntPtr buffer, int size, out ServiceStatusProcess value)
        {
            value = new ServiceStatusProcess();
            if (buffer == IntPtr.Zero || size != StatusBytes ||
                Marshal.SizeOf(typeof(ServiceStatusProcess)) != StatusBytes) return false;
            value = (ServiceStatusProcess)Marshal.PtrToStructure(buffer, typeof(ServiceStatusProcess));
            return true;
        }
        internal static bool CanQueryProcess(ServiceStatusProcess value)
        {
            return value.ServiceType == 0x10 && value.CurrentState == 4 && value.ProcessId != 0;
        }
        internal static bool SameRunningProcess(ServiceStatusProcess first, ServiceStatusProcess second)
        {
            return CanQueryProcess(first) && CanQueryProcess(second) &&
                first.ServiceType == second.ServiceType && first.CurrentState == second.CurrentState &&
                first.ProcessId == second.ProcessId;
        }
        private static bool ReadStatus(IntPtr service, IntPtr buffer, out ServiceStatusProcess value)
        {
            value = new ServiceStatusProcess();
            uint needed;
            // pcbBytesNeeded is specified only on insufficient-buffer failure;
            // never treat its success value as a returned buffer length.
            return QueryServiceStatusEx(service, 0, buffer, StatusBytes, out needed) &&
                TryParseStatus(buffer, StatusBytes, out value);
        }
        private static P279RuntimeTokenStatus Failure()
        {
            return Marshal.GetLastWin32Error() == 5 ? P279RuntimeTokenStatus.TokenDenied :
                P279RuntimeTokenStatus.Unverified;
        }
        private static bool Release(IntPtr handle, bool scm)
        {
            try { return handle == IntPtr.Zero || (scm ? CloseServiceHandle(handle) : CloseHandle(handle)); }
            catch (Exception) { return false; }
        }
        private static bool Free(IntPtr buffer)
        {
            try { if (buffer != IntPtr.Zero) Marshal.FreeHGlobal(buffer); return true; }
            catch (Exception) { return false; }
        }
        internal static P279RuntimeTokenEvidence RefuseUntrustedClaim(string account, bool approval)
        {
            // Neither claim participates in observation or authority.
            return Observe();
        }
        internal static P279RuntimeTokenEvidence Observe()
        {
            P279RuntimeTokenStatus status = P279RuntimeTokenStatus.Unverified;
            bool config = false, opened = false, processOpened = false, tokenOpened = false,
                matches = false, rechecked = false;
            IntPtr manager = IntPtr.Zero, service = IntPtr.Zero, process = IntPtr.Zero,
                token = IntPtr.Zero, buffer = IntPtr.Zero, sid = IntPtr.Zero, domain = IntPtr.Zero;
            WindowsIdentity identity = null;
            try
            {
                // Frozen actual SCM configuration observation MUST come first.
                P261ScmEvidence prior = P261ScmReadOnlyAdmission.Observe();
                do
                {
                    if (prior.Status == P261ScmStatus.Missing)
                    { status = P279RuntimeTokenStatus.Missing; break; }
                    if (prior.Status != P261ScmStatus.ConfigObserved)
                    { status = P279RuntimeTokenStatus.ConfigUnverified; break; }
                    config = true;
                    if (Environment.OSVersion.Platform != PlatformID.Win32NT ||
                        Environment.OSVersion.Version < new Version(6, 1)) break;
                    manager = OpenSCManagerW(null, null, SC_MANAGER_CONNECT);
                    if (manager == IntPtr.Zero) { status = Failure(); break; }
                    service = OpenServiceW(manager, ServiceGate.ServiceName, SERVICE_QUERY_STATUS);
                    if (service == IntPtr.Zero) { status = Failure(); break; }
                    opened = true;
                    buffer = Marshal.AllocHGlobal(StatusBytes);
                    ServiceStatusProcess before, after;
                    if (!ReadStatus(service, buffer, out before)) break;
                    if (!CanQueryProcess(before))
                    {
                        status = (before.ServiceType & 0x20) != 0 ? P279RuntimeTokenStatus.SharedProcess :
                            (before.CurrentState != 4 || before.ProcessId == 0 ?
                                P279RuntimeTokenStatus.NotRunning : P279RuntimeTokenStatus.Unverified);
                        break;
                    }
                    process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, before.ProcessId);
                    if (process == IntPtr.Zero) { status = Failure(); break; }
                    processOpened = true;
                    if (!OpenProcessToken(process, TOKEN_QUERY, out token)) { status = Failure(); break; }
                    tokenOpened = true;
                    identity = new WindowsIdentity(token);
                    SecurityIdentifier actual = identity.User;
                    if (actual == null) break;
                    uint sidBytes = 0, domainChars = 0, use;
                    string fixedName = "NT SERVICE\\" + ServiceGate.ServiceName;
                    bool sizing = LookupAccountNameW(null, fixedName, IntPtr.Zero, ref sidBytes,
                        IntPtr.Zero, ref domainChars, out use);
                    if (sizing || Marshal.GetLastWin32Error() != 122 || sidBytes < 8 ||
                        sidBytes > MaximumSidBytes || domainChars == 0 || domainChars > MaximumDomainChars) break;
                    uint sidCapacity = sidBytes, domainCapacity = domainChars;
                    sid = Marshal.AllocHGlobal((int)sidCapacity);
                    domain = Marshal.AllocHGlobal(checked((int)domainCapacity * 2));
                    if (!LookupAccountNameW(null, fixedName, sid, ref sidBytes,
                        domain, ref domainChars, out use)) { status = Failure(); break; }
                    if (sidBytes < 8 || sidBytes > sidCapacity || domainChars > domainCapacity ||
                        Marshal.ReadByte(sid) != 1 || Marshal.ReadByte(sid, 1) > 15 ||
                        8 + 4 * Marshal.ReadByte(sid, 1) != sidBytes) break;
                    // Compare SID objects, never account text or SID strings.
                    matches = actual.Equals(new SecurityIdentifier(sid));
                    // Keep process/token handles alive across the second SCM snapshot.
                    if (!ReadStatus(service, buffer, out after) || !SameRunningProcess(before, after)) break;
                    rechecked = true;
                    status = matches ? P279RuntimeTokenStatus.RuntimeTokenObserved : P279RuntimeTokenStatus.TokenMismatch;
                    // SCM snapshots cannot eliminate TOCTOU. Even a match grants NO authority.
                } while (false);
            }
            catch (UnauthorizedAccessException) { status = P279RuntimeTokenStatus.TokenDenied; }
            catch (System.Security.SecurityException) { status = P279RuntimeTokenStatus.TokenDenied; }
            catch (Exception) { status = P279RuntimeTokenStatus.Unverified; }
            finally
            {
                bool clean = true;
                try { if (identity != null) identity.Dispose(); }
                catch (Exception) { clean = false; }
                // Non-short-circuit accumulation attempts EVERY cleanup even after a failure.
                clean &= Free(domain); clean &= Free(sid); clean &= Free(buffer);
                clean &= Release(token, false); clean &= Release(process, false);
                clean &= Release(service, true); clean &= Release(manager, true);
                if (!clean) status = P279RuntimeTokenStatus.Unverified;
            }
            return new P279RuntimeTokenEvidence(status, config, opened, processOpened,
                tokenOpened, matches, rechecked);
        }
    }
}
