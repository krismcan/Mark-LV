#if !DEBUG || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY
#error P282_IDENTITY_CUSTODY_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal enum P282CustodyStatus
    {
        Unverified, MissingService, ConfigurationRejected, NotExecutingService,
        TokenRejected, Changed, IdentityObservedStoreNotProven
    }

    // Diagnostic evidence is NEVER a capability. No consumer accepts this as admission.
    internal sealed class P282CustodyEvidence
    {
        internal readonly P282CustodyStatus Status;
        internal readonly bool ProcessTokenObserved;
        internal P282CustodyEvidence(P282CustodyStatus status, bool observed)
        { Status = status; ProcessTokenObserved = observed; }
        internal bool ProfileOwnershipEstablished { get { return false; } }
        internal bool CurrentUserProtectedStoreEstablished { get { return false; } }
        internal bool QualifiedSec0304Approved { get { return false; } }
        internal bool ProtectedCustodyAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
        public override string ToString() { return "<P282 DENY; service store NOT PROVEN>"; }
    }

    internal static class P282ExecutingServiceCustody
    {
        [StructLayout(LayoutKind.Sequential)]
        internal struct Luid
        {
            internal uint Low;
            internal int High;
        }
        [StructLayout(LayoutKind.Sequential)]
        internal struct Statistics
        {
            internal Luid TokenId, AuthenticationId;
            internal long ExpirationTime;
            internal uint TokenType, ImpersonationLevel, DynamicCharged, DynamicAvailable,
                GroupCount, PrivilegeCount;
            internal Luid ModifiedId;
        }
        private sealed class Snapshot
        {
            internal readonly SecurityIdentifier User;
            internal readonly Statistics Stats;
            internal readonly uint Session;
            internal Snapshot(SecurityIdentifier user, Statistics stats, uint session)
            { User = user; Stats = stats; Session = session; }
        }
        [DllImport("kernel32.dll", ExactSpelling = true)]
        private static extern IntPtr GetCurrentProcess();
        [DllImport("kernel32.dll", ExactSpelling = true)]
        private static extern uint GetCurrentProcessId();
        [DllImport("kernel32.dll", ExactSpelling = true)]
        private static extern IntPtr GetCurrentThread();
        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenThreadToken(IntPtr thread, uint access,
            [MarshalAs(UnmanagedType.Bool)] bool openAsSelf, out IntPtr token);
        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetTokenInformation(IntPtr token, int kind,
            IntPtr buffer, uint size, out uint returned);
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

        private static bool SameLuid(Luid a, Luid b) { return a.Low == b.Low && a.High == b.High; }
        // Pure comparison only; synthetic values cannot create a live binding.
        internal static bool SameStatistics(Statistics a, Statistics b)
        {
            return a.TokenType == 1 && b.TokenType == 1 && SameLuid(a.TokenId, b.TokenId) &&
                SameLuid(a.AuthenticationId, b.AuthenticationId) && SameLuid(a.ModifiedId, b.ModifiedId);
        }
        private static bool Same(Snapshot a, Snapshot b)
        {
            return a != null && b != null && a.User.Equals(b.User) &&
                a.Session == b.Session && SameStatistics(a.Stats, b.Stats);
        }
        private static bool NoImpersonation()
        {
            IntPtr token = IntPtr.Zero;
            bool absent = false;
            try
            {
                // ERROR_NO_TOKEN alone is acceptable. Anonymous/denied/inaccessible
                // impersonation MUST NOT fall back to process identity.
                bool opened = OpenThreadToken(GetCurrentThread(), 8, true, out token);
                absent = !opened && Marshal.GetLastWin32Error() == 1008 && token == IntPtr.Zero;
            }
            finally { if (token != IntPtr.Zero && !CloseHandle(token)) absent = false; }
            return absent;
        }
        private static Snapshot Capture()
        {
            IntPtr token = IntPtr.Zero, buffer = IntPtr.Zero;
            Snapshot result = null;
            try
            {
                if (Environment.OSVersion.Platform != PlatformID.Win32NT || !NoImpersonation()) return null;
                // Always our executing process, never an SCM-selected remote process.
                if (!OpenProcessToken(GetCurrentProcess(), 8, out token) || token == IntPtr.Zero) return null;
                if (Marshal.SizeOf(typeof(Statistics)) != 56) return null;
                buffer = Marshal.AllocHGlobal(56);
                uint returned;
                if (!GetTokenInformation(token, 10, buffer, 56, out returned) || returned != 56) return null;
                Statistics stats = (Statistics)Marshal.PtrToStructure(buffer, typeof(Statistics));
                if (stats.TokenType != 1) return null;
                if (!GetTokenInformation(token, 12, buffer, 4, out returned) || returned != 4) return null;
                uint session = unchecked((uint)Marshal.ReadInt32(buffer));
                using (WindowsIdentity identity = new WindowsIdentity(token))
                {
                    SecurityIdentifier user = identity.User;
                    if (user != null && NoImpersonation()) result = new Snapshot(user, stats, session);
                }
            }
            catch (Exception) { result = null; }
            finally
            {
                if (buffer != IntPtr.Zero) Marshal.FreeHGlobal(buffer);
                if (token != IntPtr.Zero && !CloseHandle(token)) result = null;
            }
            return result;
        }
        // This is a restriction of the existing DISPOSABLE RUNNER fixture, not a
        // positive service grant. TokenUser comes only from Capture, not a claim.
        internal static bool IsSyntheticRunnerUser(SecurityIdentifier user, uint session)
        {
            return user != null && session != 0 &&
                !user.IsWellKnown(WellKnownSidType.LocalSystemSid) &&
                !user.Value.StartsWith("S-1-5-80-", StringComparison.Ordinal);
        }
        private static bool IsSyntheticRunner(Snapshot value)
        { return value != null && IsSyntheticRunnerUser(value.User, value.Session); }
        internal sealed class SyntheticRunnerBinding
        {
            private readonly Snapshot initial;
            private int poisoned;
            private SyntheticRunnerBinding(Snapshot value) { initial = value; }
            internal static SyntheticRunnerBinding CaptureRunner()
            {
                if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
                    Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
                    Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
                    (Environment.GetEnvironmentVariable("P270_HOSTED_DISPOSABLE") != "1" &&
                     Environment.GetEnvironmentVariable("P271_HOSTED_DISPOSABLE") != "1")) throw new LedgerBlocked();
                Snapshot value = Capture();
                if (!IsSyntheticRunner(value)) throw new LedgerBlocked();
                return new SyntheticRunnerBinding(value);
            }
            internal SecurityIdentifier TokenUser { get { return initial.User; } }
            internal void DemandUnchanged()
            {
                Snapshot current = Capture();
                if (Volatile.Read(ref poisoned) != 0 || !IsSyntheticRunner(current) || !Same(initial, current))
                { Interlocked.Exchange(ref poisoned, 1); throw new LedgerBlocked(); }
            }
        }
        internal static SyntheticRunnerBinding BindSyntheticRunner()
        { return SyntheticRunnerBinding.CaptureRunner(); }

        // This classifier is used after actual kernel/SCM queries. Its synthetic
        // tests prove state transitions only, never installed service isolation.
        internal static P282CustodyStatus ClassifyExecutingService(
            P279RunningServiceTokenReadOnly.ServiceStatusProcess before,
            P279RunningServiceTokenReadOnly.ServiceStatusProcess after, uint actualPid,
            bool actualUserMatches, uint actualSession, bool tokenUnchanged)
        {
            if (!P279RunningServiceTokenReadOnly.SameRunningProcess(before, after) || !tokenUnchanged)
                return P282CustodyStatus.Changed;
            if (actualPid == 0 || before.ProcessId != actualPid) return P282CustodyStatus.NotExecutingService;
            if (!actualUserMatches || actualSession != 0) return P282CustodyStatus.TokenRejected;
            return P282CustodyStatus.IdentityObservedStoreNotProven;
        }
        private static bool ReadStatus(IntPtr service, IntPtr buffer,
            out P279RunningServiceTokenReadOnly.ServiceStatusProcess status)
        {
            status = new P279RunningServiceTokenReadOnly.ServiceStatusProcess();
            uint needed;
            return QueryServiceStatusEx(service, 0, buffer, 36, out needed) &&
                P279RunningServiceTokenReadOnly.TryParseStatus(buffer, 36, out status);
        }
        internal static P282CustodyEvidence ObserveProtectedService()
        {
            Snapshot caller = Capture(); // Obtain caller token even when SCM service is absent.
            P282CustodyStatus status = P282CustodyStatus.Unverified;
            IntPtr manager = IntPtr.Zero, service = IntPtr.Zero, buffer = IntPtr.Zero;
            try
            {
                do
                {
                    if (caller == null) { status = P282CustodyStatus.TokenRejected; break; }
                    P261ScmEvidence config = P261ScmReadOnlyAdmission.Observe();
                    if (config.Status == P261ScmStatus.Missing) { status = P282CustodyStatus.MissingService; break; }
                    // Includes LocalSystem and wrong/restricted-SID configuration.
                    if (config.Status != P261ScmStatus.ConfigObserved)
                    { status = P282CustodyStatus.ConfigurationRejected; break; }
                    manager = OpenSCManagerW(null, null, 1);
                    if (manager == IntPtr.Zero) break;
                    service = OpenServiceW(manager, ServiceGate.ServiceName, 4);
                    if (service == IntPtr.Zero) break;
                    buffer = Marshal.AllocHGlobal(36);
                    P279RunningServiceTokenReadOnly.ServiceStatusProcess before, after;
                    if (!ReadStatus(service, buffer, out before)) break;
                    // Resolve ONLY the canonical local virtual-service principal.
                    // An account string match by itself cannot satisfy this SID comparison.
                    SecurityIdentifier expected = (SecurityIdentifier)new NTAccount("NT SERVICE",
                        ServiceGate.ServiceName).Translate(typeof(SecurityIdentifier));
                    Snapshot current = Capture();
                    if (current == null) { status = P282CustodyStatus.TokenRejected; break; }
                    if (!ReadStatus(service, buffer, out after)) break;
                    if (P261ScmReadOnlyAdmission.Observe().Status != P261ScmStatus.ConfigObserved)
                    { status = P282CustodyStatus.Changed; break; }
                    status = ClassifyExecutingService(before, after, GetCurrentProcessId(),
                        !caller.User.IsWellKnown(WellKnownSidType.LocalSystemSid) && caller.User.Equals(expected),
                        caller.Session, Same(caller, current) && Same(caller, Capture()));
                    // Snapshot equality is NOT continuous SCM/DPAPI/store custody.
                } while (false);
            }
            catch (Exception) { status = P282CustodyStatus.Unverified; }
            finally
            {
                if (buffer != IntPtr.Zero) Marshal.FreeHGlobal(buffer);
                bool clean = true;
                if (service != IntPtr.Zero) clean &= CloseServiceHandle(service);
                if (manager != IntPtr.Zero) clean &= CloseServiceHandle(manager);
                if (!clean) status = P282CustodyStatus.Unverified;
            }
            return new P282CustodyEvidence(status, caller != null);
        }
        internal static void DemandProtectedStore()
        {
            ObserveProtectedService();
            // No approved profile/DPAPI owner, store ACL/handle scope, monotonic
            // recovery or SEC03/04 proof exists. No caller can substitute one.
            throw new LedgerBlocked();
        }
    }
}
