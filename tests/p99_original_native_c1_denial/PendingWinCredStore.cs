// Nayeon BYOK C1: strictly pending-only, service-vault WinCred adapter.
// Production-target native implementation. NOT wired to an IPC route,
// IProtectedPendingState, installer, or executable entrypoint at this stage.
// Every native call requires the still-disabled exact Windows service gate.
// No keys, active credentials, provider connection, logs or mutable target.
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class PendingWinCredStore
    {
        // Not a name derived from external request or existing active aliases.
        // LocalSystem has its OWN Windows credential vault; test that vault's
        // actual profile and reboot persistence before any production rollout.
        internal const string FixedTarget =
            "nayeon-v1/byok-c1/pending/openai";
        private const string FixedUser = "nayeon-v1-pending";
        private const uint GenericCredential = 1;
        private const uint LocalMachinePersistence = 2;
        private const int MaxCredentialBytes = 2560;
#if BYOK_TEST
        // Instrumented ONLY in fake-only test binaries. No permission
        // bypass and no native API substitution in production.
        private static int attemptedNativeCalls;
        internal static int SyntheticNativeAttempts
        {
            get { return Interlocked.CompareExchange(
                ref attemptedNativeCalls,0,0); }
        }
#endif
        private static void RecordNativeAttempt()
        {
#if BYOK_TEST
            Interlocked.Increment(ref attemptedNativeCalls);
#endif
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeFileTime
        {
            internal uint LowDateTime;
            internal uint HighDateTime;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct NativeCredential
        {
            internal uint Flags;
            internal uint Type;
            internal IntPtr TargetName;
            internal IntPtr Comment;
            internal NativeFileTime LastWritten;
            internal uint CredentialBlobSize;
            internal IntPtr CredentialBlob;
            internal uint Persist;
            internal uint AttributeCount;
            internal IntPtr Attributes;
            internal IntPtr TargetAlias;
            internal IntPtr UserName;
        }

        [DllImport("advapi32.dll", EntryPoint="CredReadW",
            CharSet=CharSet.Unicode, ExactSpelling=true, SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredRead(
            [MarshalAs(UnmanagedType.LPWStr)] string target,
            uint credentialType, uint flags, out IntPtr credential);

        [DllImport("advapi32.dll", EntryPoint="CredWriteW",
            CharSet=CharSet.Unicode, ExactSpelling=true, SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredWrite(
            ref NativeCredential credential, uint flags);

        [DllImport("advapi32.dll", EntryPoint="CredDeleteW",
            CharSet=CharSet.Unicode, ExactSpelling=true, SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredDelete(
            [MarshalAs(UnmanagedType.LPWStr)] string target,
            uint credentialType, uint flags);

        [DllImport("advapi32.dll", EntryPoint="CredFree",
            ExactSpelling=true)]
        private static extern void CredFree(IntPtr buffer);

        internal static bool IsFixedPendingTarget(string candidate)
        {
            return String.Equals(candidate,FixedTarget,
                StringComparison.Ordinal);
        }

        internal static bool CandidateShape(byte[] value)
        {
            return value!=null && value.Length>=1 &&
                value.Length<=MaxCredentialBytes;
        }

        // Enforce the reviewed native CREDENTIALW packing at runtime.
        // These checks never access Windows credentials.
        internal static bool NativeAbiMatchesExpected()
        {
            try
            {
                int expectedSize=IntPtr.Size==8?80:52;
                int expectedBlob=IntPtr.Size==8?40:28;
                int expectedUser=IntPtr.Size==8?72:48;
                return (IntPtr.Size==8 || IntPtr.Size==4) &&
                    Marshal.SizeOf(typeof(NativeCredential))==expectedSize &&
                    Marshal.OffsetOf(typeof(NativeCredential),
                        "CredentialBlob").ToInt32()==expectedBlob &&
                    Marshal.OffsetOf(typeof(NativeCredential),
                        "UserName").ToInt32()==expectedUser;
            }
            catch(Exception){return false;}
        }

        // No caller-provided proof or test switch can arm this gate.
        // A negative is expected until installation and review.
        private static void DemandTrustedService()
        {
            try
            {
                using(WindowsIdentity current=WindowsIdentity.GetCurrent())
                {
                    if(!NativeAbiMatchesExpected() ||
                        current==null || current.User==null ||
                        !current.User.IsWellKnown(
                            WellKnownSidType.LocalSystemSid) ||
                        !ServiceGate.LiveEligible() ||
                        !ProtectedAcl.VerifyInstalledCustodyDirectory())
                        throw new LedgerBlocked();
                }
            }
            catch(Exception){throw new LedgerBlocked();}
        }

        private static void ClearReadNativeAllocation(IntPtr pointer)
        {
            // Best-effort clearing before freeing the provider allocation.
            // If native metadata is invalid, fail closed; CredFree still runs.
            if(pointer==IntPtr.Zero)return;
            try
            {
                NativeCredential observed=(NativeCredential)
                    Marshal.PtrToStructure(pointer,typeof(NativeCredential));
                if(observed.CredentialBlobSize>MaxCredentialBytes)
                    throw new LedgerBlocked();
                if(observed.CredentialBlobSize>0)
                {
                    if(observed.CredentialBlob==IntPtr.Zero)
                        throw new LedgerBlocked();
                    for(int i=0;i<(int)observed.CredentialBlobSize;i++)
                        Marshal.WriteByte(observed.CredentialBlob,i,0);
                }
            }
            finally{CredFree(pointer);}
        }

        internal bool PendingPresent()
        {
            DemandTrustedService();
            IntPtr credential=IntPtr.Zero;
            try
            {
                RecordNativeAttempt();
                if(CredRead(FixedTarget,GenericCredential,0,out credential))
                {
                    if(credential==IntPtr.Zero)throw new LedgerBlocked();
                    return true;
                }
                int error=Marshal.GetLastWin32Error();
                // A missing record is the ONLY ordinary absence result.
                // Every other native error is an unknown/recovery state.
                if(error==1168) return false; // ERROR_NOT_FOUND
                throw new LedgerBlocked();
            }
            catch(Exception){throw new LedgerBlocked();}
            finally
            {
                // CredRead materialises a secret-bearing native allocation.
                // Never copy the blob into managed memory or expose it.
                if(credential!=IntPtr.Zero)
                    ClearReadNativeAllocation(credential);
            }
        }

        // The P61 service-owned revocation+dispatch actor is not yet
        // implemented. Even another same-assembly caller MUST NOT reach
        // WinCred merely because ServiceGate is later enabled.
        internal static bool NativeMutationAdmissionPending()
        {
            return true;
        }

        internal void SaveOrReplace(byte[] exactCandidate)
        {
            if(NativeMutationAdmissionPending())throw new LedgerBlocked();
            DemandTrustedService();
            if(!CandidateShape(exactCandidate))throw new LedgerBlocked();
            IntPtr name=IntPtr.Zero, user=IntPtr.Zero, blob=IntPtr.Zero;
            try
            {
                name=Marshal.StringToHGlobalUni(FixedTarget);
                user=Marshal.StringToHGlobalUni(FixedUser);
                blob=Marshal.AllocHGlobal(exactCandidate.Length);
                Marshal.Copy(exactCandidate,0,blob,exactCandidate.Length);
                NativeCredential request=new NativeCredential();
                request.Type=GenericCredential;
                request.TargetName=name;
                request.UserName=user;
                request.CredentialBlob=blob;
                request.CredentialBlobSize=(uint)exactCandidate.Length;
                request.Persist=LocalMachinePersistence;
                // Single native effect. Unknown/failed result must be
                // handled as recovery by the transaction coordinator.
                // Never retry or call provider validation here.
                RecordNativeAttempt();
                if(!CredWrite(ref request,0))throw new LedgerBlocked();
            }
            catch(Exception){throw new LedgerBlocked();}
            finally
            {
                try
                {
                    if(blob!=IntPtr.Zero)
                    {
                        try
                        {
                            // Input byte[] is owned/cleared by coordinator.
                            for(int i=0;i<exactCandidate.Length;i++)
                                Marshal.WriteByte(blob,i,0);
                        }
                        finally{Marshal.FreeHGlobal(blob);}
                    }
                }
                finally
                {
                    try
                    {
                        if(user!=IntPtr.Zero)Marshal.FreeHGlobal(user);
                    }
                    finally
                    {
                        if(name!=IntPtr.Zero)Marshal.FreeHGlobal(name);
                    }
                }
            }
        }

        internal void DeletePending()
        {
            if(NativeMutationAdmissionPending())throw new LedgerBlocked();
            DemandTrustedService();
            try
            {
                RecordNativeAttempt();
                if(!CredDelete(FixedTarget,GenericCredential,0))
                    throw new LedgerBlocked();
            }
            catch(Exception){throw new LedgerBlocked();}
        }
    }
}
