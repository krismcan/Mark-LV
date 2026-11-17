// Review-only real SCM observation. Qualified principal/store decisions remain open.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P261_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Runtime.InteropServices;

namespace Nayeon.ByokC1
{
    internal enum P261ScmStatus
    {
        Missing, Denied, Mismatch, Unverified, UnsupportedOs, MalformedBuffer,
        ConfigObserved
    }

    internal sealed class P261ScmEvidence
    {
        internal readonly P261ScmStatus Status;
        internal readonly bool ServiceOpened;
        internal readonly bool AccountQueried;
        internal readonly bool VirtualAccountMatchesServiceName;
        // Actual queried SERVICE_SID_INFO.dwServiceSidType, null if unobserved.
        internal readonly uint? ServiceSidType;

        internal P261ScmEvidence(P261ScmStatus status, bool opened,
            bool accountQueried, bool accountMatches, uint? sidType)
        {
            Status = status;
            ServiceOpened = opened;
            AccountQueried = accountQueried;
            VirtualAccountMatchesServiceName = accountMatches;
            ServiceSidType = sidType;
        }

        internal bool QualifiedDecisionApproved { get { return false; } }
        internal bool ApprovedServiceOwner { get { return false; } }
        internal bool EffectAllowed { get { return false; } }
        internal bool RealKeyEligible { get { return false; } }
        internal bool CredentialAuthority { get { return false; } }
    }

    internal static class P261ScmReadOnlyAdmission
    {
        private const uint SC_MANAGER_CONNECT = 0x0001;
        private const uint SERVICE_QUERY_CONFIG = 0x0001;
        private const uint SERVICE_CONFIG_SERVICE_SID_INFO = 5;
        internal const uint SERVICE_SID_TYPE_RESTRICTED = 3;
        private const int ERROR_ACCESS_DENIED = 5;
        private const int ERROR_INSUFFICIENT_BUFFER = 122;
        private const int ERROR_SERVICE_DOES_NOT_EXIST = 1060;
        private const int MaximumConfigBytes = 8192;

        [StructLayout(LayoutKind.Sequential)]
        internal struct QueryServiceConfig
        {
            internal uint ServiceType;
            internal uint StartType;
            internal uint ErrorControl;
            internal IntPtr BinaryPathName;
            internal IntPtr LoadOrderGroup;
            internal uint TagId;
            internal IntPtr Dependencies;
            internal IntPtr ServiceStartName;
            internal IntPtr DisplayName;
        }

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true,
            SetLastError = true)]
        private static extern IntPtr OpenSCManagerW(string machineName,
            string databaseName, uint desiredAccess);

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true,
            SetLastError = true)]
        private static extern IntPtr OpenServiceW(IntPtr manager,
            string serviceName, uint desiredAccess);

        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool QueryServiceConfigW(IntPtr service,
            IntPtr buffer, uint bufferSize, out uint bytesNeeded);

        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool QueryServiceConfig2W(IntPtr service,
            uint infoLevel, IntPtr buffer, uint bufferSize, out uint bytesNeeded);

        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseServiceHandle(IntPtr handle);

        private static P261ScmStatus FailureStatus(int error)
        {
            return error == ERROR_ACCESS_DENIED ? P261ScmStatus.Denied :
                P261ScmStatus.Unverified;
        }

        // This compares the SCM-owned string in place. It creates no managed
        // account string and never dereferences the other returned pointers.
        internal static bool TryReadAccountMatch(IntPtr buffer, int size,
            out bool matches)
        {
            matches = false;
            int headerSize = Marshal.SizeOf(typeof(QueryServiceConfig));
            if (buffer == IntPtr.Zero || size < headerSize || size > MaximumConfigBytes)
                return false;
            QueryServiceConfig config = (QueryServiceConfig)Marshal.PtrToStructure(
                buffer, typeof(QueryServiceConfig));
            ulong start = unchecked((ulong)buffer.ToInt64());
            ulong account = unchecked((ulong)config.ServiceStartName.ToInt64());
            if (account < start || account - start < (ulong)headerSize ||
                account - start >= (ulong)size || (account & 1) != 0)
                return false;
            int offset = (int)(account - start);
            string expected = "NT SERVICE\\" + ServiceGate.ServiceName;
            bool equal = true;
            int length = 0;
            for (; offset + 1 < size; offset += 2)
            {
                char value = (char)(ushort)Marshal.ReadInt16(buffer, offset);
                if (value == '\0')
                {
                    matches = equal && length == expected.Length;
                    return length > 0;
                }
                if (length >= expected.Length || Char.ToUpperInvariant(value) !=
                    Char.ToUpperInvariant(expected[length]))
                    equal = false;
                length++;
            }
            return false;
        }

        internal static P261ScmStatus ClassifyConfiguration(bool accountMatches,
            uint sidType)
        {
            if (sidType != 0 && sidType != 1 && sidType != SERVICE_SID_TYPE_RESTRICTED)
                return P261ScmStatus.MalformedBuffer;
            if (!accountMatches || sidType != SERVICE_SID_TYPE_RESTRICTED)
                return P261ScmStatus.Mismatch;
            return P261ScmStatus.ConfigObserved;
        }

        // Claims are deliberately discarded. Only the parameterless observer
        // supplies evidence, and every result denies authority unconditionally.
        internal static P261ScmEvidence RefuseUntrustedClaim(
            string untrustedAccount, bool untrustedQualifiedApproval)
        {
            return Observe();
        }

        internal static P261ScmEvidence Observe()
        {
            if (Environment.OSVersion.Platform != PlatformID.Win32NT ||
                Environment.OSVersion.Version < new Version(6, 1))
                return new P261ScmEvidence(P261ScmStatus.UnsupportedOs,
                    false, false, false, null);

            IntPtr manager = IntPtr.Zero;
            IntPtr service = IntPtr.Zero;
            IntPtr configBuffer = IntPtr.Zero;
            IntPtr sidBuffer = IntPtr.Zero;
            P261ScmStatus status = P261ScmStatus.Unverified;
            bool opened = false;
            bool queried = false;
            bool matches = false;
            uint? sidType = null;
            try
            {
                manager = OpenSCManagerW(null, null, SC_MANAGER_CONNECT);
                if (manager == IntPtr.Zero)
                    status = FailureStatus(Marshal.GetLastWin32Error());
                else
                {
                    // Actual frozen source constant, also used by CustodyService.
                    service = OpenServiceW(manager, ServiceGate.ServiceName,
                        SERVICE_QUERY_CONFIG);
                    if (service == IntPtr.Zero)
                    {
                        int error = Marshal.GetLastWin32Error();
                        status = error == ERROR_SERVICE_DOES_NOT_EXIST ?
                            P261ScmStatus.Missing : FailureStatus(error);
                    }
                    else
                    {
                        opened = true;
                        uint required;
                        bool sizing = QueryServiceConfigW(service, IntPtr.Zero, 0,
                            out required);
                        int error = Marshal.GetLastWin32Error();
                        if (sizing || error != ERROR_INSUFFICIENT_BUFFER)
                            status = sizing ? P261ScmStatus.MalformedBuffer : FailureStatus(error);
                        else if (required < Marshal.SizeOf(typeof(QueryServiceConfig)) ||
                            required > MaximumConfigBytes)
                            status = P261ScmStatus.MalformedBuffer;
                        else
                        {
                            configBuffer = Marshal.AllocHGlobal((int)required);
                            uint ignored;
                            if (!QueryServiceConfigW(service, configBuffer, required, out ignored))
                                status = FailureStatus(Marshal.GetLastWin32Error());
                            else if (!TryReadAccountMatch(configBuffer, (int)required, out matches))
                                status = P261ScmStatus.MalformedBuffer;
                            else
                            {
                                queried = true;
                                // SERVICE_SID_INFO is exactly one DWORD. A larger
                                // required buffer fails closed without a retry.
                                sidBuffer = Marshal.AllocHGlobal(4);
                                if (!QueryServiceConfig2W(service,
                                    SERVICE_CONFIG_SERVICE_SID_INFO, sidBuffer, 4, out ignored))
                                    status = FailureStatus(Marshal.GetLastWin32Error());
                                else
                                {
                                    sidType = unchecked((uint)Marshal.ReadInt32(sidBuffer));
                                    status = ClassifyConfiguration(matches, sidType.Value);
                                }
                            }
                        }
                    }
                }
            }
            catch (DllNotFoundException) { status = P261ScmStatus.UnsupportedOs; }
            catch (EntryPointNotFoundException) { status = P261ScmStatus.UnsupportedOs; }
            catch (BadImageFormatException) { status = P261ScmStatus.UnsupportedOs; }
            catch (System.Security.SecurityException) { status = P261ScmStatus.Denied; }
            finally
            {
                if (sidBuffer != IntPtr.Zero) Marshal.FreeHGlobal(sidBuffer);
                if (configBuffer != IntPtr.Zero) Marshal.FreeHGlobal(configBuffer);
                if (service != IntPtr.Zero && !CloseServiceHandle(service))
                    status = P261ScmStatus.Unverified;
                if (manager != IntPtr.Zero && !CloseServiceHandle(manager))
                    status = P261ScmStatus.Unverified;
            }
            return new P261ScmEvidence(status, opened, queried, matches, sidType);
        }
    }
}
