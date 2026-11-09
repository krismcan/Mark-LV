// P118 — OS provenance: ONE open file handle used for BOTH 128-bit
// FILE_ID_INFO before/after and WinVerifyTrust policy inspection.
// An OS process handle is held while observing the named-pipe client.
// Never identifies a process's actual loaded image section or gives consent.
// No privileged service, trusted publisher anchor, real key or effects.
using System;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1
{
    internal enum OsSameHandleReviewState
    {
        Unavailable,
        NativeFileAndPolicyObserved
    }

    internal sealed class OsSameHandleReviewObservation
    {
        internal readonly OsSameHandleReviewState State;
        internal readonly bool NativePolicyAttempted;
        internal readonly bool NativePolicyAccepted;
        internal readonly bool SameFileHandleIdStable;
        internal readonly ulong OsVolumeSerialNumber;
        internal readonly string OsFileId128Hex;
        internal readonly bool OsConnectedClientObserved;

        internal OsSameHandleReviewObservation(
            OsSameHandleReviewState state, bool attempted, bool accepted,
            bool stable, ulong volume, string id, bool clientObserved)
        {
            State=state;
            NativePolicyAttempted=attempted;
            NativePolicyAccepted=accepted;
            SameFileHandleIdStable=stable;
            OsVolumeSerialNumber=volume;
            OsFileId128Hex=id;
            OsConnectedClientObserved=clientObserved;
        }

        internal bool ApprovedPublisherTrustAnchorConfigured {get{return false;}}
        internal bool RunningMappedImageIdentityProven {get{return false;}}
        internal bool TrustedConsentApplicationVerified {get{return false;}}
        internal bool TrustedInteractiveDesktopVerified {get{return false;}}
        internal bool HumanApprovalVerified {get{return false;}}
        internal bool ProtectedOneUseGrantIssued {get{return false;}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}

        internal static OsSameHandleReviewObservation Unavailable()
        {
            return new OsSameHandleReviewObservation(
                OsSameHandleReviewState.Unavailable,
                false,false,false,0,null,false);
        }
        public override string ToString()
        {
            return "<P118 same opened file for OS ID and signature policy; NO live image/consent trust>";
        }
    }

    internal static class WindowsSameHandleFilePolicyReview
    {
        private const int FileIdInfoClass=18;
        private const int FileIdInfoBytes=24;
        private const uint ProcessQueryLimitedInformation=0x1000;
        private const uint WtdUiNone=2;
        private const uint WtdChoiceFile=1;
        private const uint WtdStateVerify=1;
        private const uint WtdStateClose=2;
        private const uint WtdRevokeWholeChain=1;
        private const uint WtdCacheOnlyUrl=0x1000;
        private static readonly Guid VerifyV2=
            new Guid("00AAC56B-CD44-11D0-8CC2-00C04FC295EE");

        [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)]
        private struct WintrustFileInfo
        {
            public uint cbStruct;
            [MarshalAs(UnmanagedType.LPWStr)]
            public string pcwszFilePath;
            public IntPtr hFile;
            public IntPtr pgKnownSubject;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct WintrustData
        {
            public uint cbStruct;
            public IntPtr pPolicyCallbackData;
            public IntPtr pSIPClientData;
            public uint dwUIChoice;
            public uint fdwRevocationChecks;
            public uint dwUnionChoice;
            public IntPtr pFile;
            public uint dwStateAction;
            public IntPtr hWVTStateData;
            public IntPtr pwszURLReference;
            public uint dwProvFlags;
            public uint dwUIContext;
            public IntPtr pSignatureSettings;
        }

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        [return:MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetFileInformationByHandleEx(
            SafeFileHandle file,int infoClass,IntPtr info,uint infoBytes);

        [DllImport("wintrust.dll",ExactSpelling=true,CharSet=CharSet.Unicode,
            PreserveSig=true)]
        private static extern uint WinVerifyTrust(
            IntPtr hwnd,ref Guid action,ref WintrustData data);

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        [return:MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetNamedPipeClientProcessId(
            SafePipeHandle pipe,out uint pid);

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        private static extern IntPtr OpenProcess(
            uint desiredAccess,[MarshalAs(UnmanagedType.Bool)]bool inherit,
            uint pid);

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        private static extern uint GetProcessId(IntPtr process);

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        [return:MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetProcessTimes(
            IntPtr process,out long creation,out long exit,
            out long kernel,out long user);

        [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
        [return:MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);

        private static bool ValidHandle(IntPtr h)
        {return h!=IntPtr.Zero && h!=new IntPtr(-1);}

        private static bool ReadId(SafeFileHandle h,
            out ulong volume,out string id)
        {
            volume=0;
            id=null;
            IntPtr data=IntPtr.Zero;
            try
            {
                data=Marshal.AllocHGlobal(FileIdInfoBytes);
                if(!GetFileInformationByHandleEx(h,FileIdInfoClass,
                    data,FileIdInfoBytes)) return false;
                volume=unchecked((ulong)Marshal.ReadInt64(data));
                byte[] bytes=new byte[16];
                Marshal.Copy(IntPtr.Add(data,8),bytes,0,bytes.Length);
                bool any=false;
                foreach(byte b in bytes)if(b!=0)any=true;
                if(!any)return false;
                id=BitConverter.ToString(bytes).Replace("-","");
                return true;
            }
            finally
            {
                if(data!=IntPtr.Zero)Marshal.FreeHGlobal(data);
            }
        }

        // The input path is untrusted. A native success (if any) is an
        // UNPINNED file policy result, not trusted signed UI provenance.
        internal static OsSameHandleReviewObservation ObserveFileOnly(
            string untrustedPath)
        {
            if(String.IsNullOrWhiteSpace(untrustedPath) ||
                !Path.IsPathRooted(untrustedPath))
                return OsSameHandleReviewObservation.Unavailable();

            IntPtr fileInfo=IntPtr.Zero;
            bool fileInfoMarshaled=false;
            try
            {
                using(var stream=new FileStream(untrustedPath,
                    FileMode.Open,FileAccess.Read,FileShare.Read))
                {
                    if(stream.SafeFileHandle.IsInvalid || stream.Length==0)
                        return OsSameHandleReviewObservation.Unavailable();

                    ulong volumeBefore,volumeAfter;
                    string idBefore,idAfter;
                    if(!ReadId(stream.SafeFileHandle,
                        out volumeBefore,out idBefore))
                        return OsSameHandleReviewObservation.Unavailable();

                    WintrustFileInfo info=new WintrustFileInfo();
                    info.cbStruct=(uint)Marshal.SizeOf(typeof(WintrustFileInfo));
                    info.pcwszFilePath=untrustedPath;
                    info.hFile=stream.SafeFileHandle.DangerousGetHandle();
                    info.pgKnownSubject=IntPtr.Zero;
                    fileInfo=Marshal.AllocHGlobal(Marshal.SizeOf(
                        typeof(WintrustFileInfo)));
                    Marshal.StructureToPtr(info,fileInfo,false);
                    fileInfoMarshaled=true;

                    WintrustData trust=new WintrustData();
                    trust.cbStruct=(uint)Marshal.SizeOf(typeof(WintrustData));
                    trust.dwUIChoice=WtdUiNone;
                    trust.fdwRevocationChecks=WtdRevokeWholeChain;
                    trust.dwUnionChoice=WtdChoiceFile;
                    trust.dwStateAction=WtdStateVerify;
                    trust.dwProvFlags=WtdCacheOnlyUrl;
                    trust.pFile=fileInfo;
                    Guid action=VerifyV2;
                    uint status;
                    try
                    {
                        status=WinVerifyTrust(IntPtr.Zero,ref action,ref trust);
                    }
                    finally
                    {
                        if(trust.hWVTStateData!=IntPtr.Zero)
                        {
                            trust.dwStateAction=WtdStateClose;
                            try{WinVerifyTrust(IntPtr.Zero,ref action,ref trust);}
                            catch(Exception){/* state cleanup, never authority */}
                        }
                    }

                    if(!ReadId(stream.SafeFileHandle,
                        out volumeAfter,out idAfter) ||
                        volumeBefore!=volumeAfter ||
                        !String.Equals(idBefore,idAfter,
                            StringComparison.Ordinal))
                        return OsSameHandleReviewObservation.Unavailable();

                    return new OsSameHandleReviewObservation(
                        OsSameHandleReviewState.NativeFileAndPolicyObserved,
                        true,status==0,true,volumeBefore,idBefore,false);
                }
            }
            catch(Exception)
            {return OsSameHandleReviewObservation.Unavailable();}
            finally
            {
                if(fileInfo!=IntPtr.Zero)
                {
                    if(fileInfoMarshaled)
                        Marshal.DestroyStructure(fileInfo,
                            typeof(WintrustFileInfo));
                    Marshal.FreeHGlobal(fileInfo);
                }
            }
        }

        // Review-only process-held observation. A process handle held
        // throughout narrows PID-reuse ambiguity, but does NOT bind the
        // signed file to the kernel's executing image-section object.
        internal static OsSameHandleReviewObservation ObserveConnectedClient(
            NamedPipeServerStream connectedPipe)
        {
            if(connectedPipe==null)
                return OsSameHandleReviewObservation.Unavailable();

            IntPtr process=IntPtr.Zero;
            try
            {
                if(!connectedPipe.IsConnected)
                    return OsSameHandleReviewObservation.Unavailable();

                OsPipeClientProcessProvenance origin=
                    WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(
                        connectedPipe);
                OsPipeClientSessionIntegrity session=
                    WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(
                        connectedPipe);
                if(origin==null || !origin.KernelProcessObserved ||
                    session==null || !session.SessionIntegrityObserved ||
                    origin.OsClientProcessId!=session.OsClientProcessId ||
                    origin.OsProcessCreatedUtcFileTime!=
                        session.OsProcessCreatedUtcFileTime ||
                    String.IsNullOrWhiteSpace(origin.OsImagePath))
                    return OsSameHandleReviewObservation.Unavailable();

                uint pid;
                if(!GetNamedPipeClientProcessId(connectedPipe.SafePipeHandle,
                    out pid) || pid==0 || pid!=origin.OsClientProcessId)
                    return OsSameHandleReviewObservation.Unavailable();

                process=OpenProcess(ProcessQueryLimitedInformation,false,pid);
                if(!ValidHandle(process) || GetProcessId(process)!=pid)
                    return OsSameHandleReviewObservation.Unavailable();

                long creation,exit,kernel,user;
                if(!GetProcessTimes(process,out creation,out exit,
                    out kernel,out user) ||
                    creation!=origin.OsProcessCreatedUtcFileTime)
                    return OsSameHandleReviewObservation.Unavailable();

                OsSameHandleReviewObservation file=
                    ObserveFileOnly(origin.OsImagePath);
                if(!file.SameFileHandleIdStable || !file.NativePolicyAttempted)
                    return OsSameHandleReviewObservation.Unavailable();

                uint endPid;
                long endCreation,endExit,endKernel,endUser;
                if(!connectedPipe.IsConnected ||
                    !GetNamedPipeClientProcessId(connectedPipe.SafePipeHandle,
                        out endPid) || endPid!=pid ||
                    GetProcessId(process)!=pid ||
                    !GetProcessTimes(process,out endCreation,out endExit,
                        out endKernel,out endUser) ||
                    endCreation!=creation)
                    return OsSameHandleReviewObservation.Unavailable();

                return new OsSameHandleReviewObservation(
                    file.State,true,file.NativePolicyAccepted,
                    true,file.OsVolumeSerialNumber,file.OsFileId128Hex,true);
            }
            catch(Exception)
            {return OsSameHandleReviewObservation.Unavailable();}
            finally
            {
                if(ValidHandle(process))CloseHandle(process);
            }
        }
    }
}
