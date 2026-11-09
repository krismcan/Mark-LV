// P117 — read-only Windows FILE OBJECT identity behind an OS-observed
// pipe-client executable path. This is review-only metadata, NEVER a
// live process mapped-section attestation or signing/consent authority.
// Uses FileIdInfo (128-bit file ID) rather than truncated 64-bit IDs.
using System;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1
{
    internal enum OsFileIdentityReviewState
    {
        Unavailable,
        OpenedFileObjectObserved
    }

    internal sealed class OsFileIdentityReviewObservation
    {
        internal readonly OsFileIdentityReviewState State;
        internal readonly ulong OsVolumeSerialNumber;
        internal readonly string OsFileId128Hex;
        internal readonly bool OsResolvedHandlePathObserved;
        internal readonly bool ConnectedPipeClientObserved;

        internal OsFileIdentityReviewObservation(
            OsFileIdentityReviewState state, ulong volume,
            string fileId, bool resolved, bool connected)
        {
            State = state;
            OsVolumeSerialNumber = volume;
            OsFileId128Hex = fileId;
            OsResolvedHandlePathObserved = resolved;
            ConnectedPipeClientObserved = connected;
        }
        internal bool NativeFileObjectObserved
        { get { return State == OsFileIdentityReviewState.OpenedFileObjectObserved; } }

        // Even if an actual Windows file ID was observed, the mapped image
        // of the process has not been bound to the inspected file handle.
        internal bool MappedImageSectionBoundToInspectedFile { get { return false; } }
        internal bool ApprovedPublisherTrustAnchorConfigured { get { return false; } }
        internal bool SignedTrustedConsentImageVerified { get { return false; } }
        internal bool ExplicitHumanConsentVerified { get { return false; } }
        internal bool ProtectedOneUseGrantIssued { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }

        internal static OsFileIdentityReviewObservation Unavailable()
        {
            return new OsFileIdentityReviewObservation(
                OsFileIdentityReviewState.Unavailable, 0, null, false, false);
        }
        public override string ToString()
        { return "<P117 Windows file-object ID observed only; no mapped-image or consent trust>"; }
    }

    internal static class WindowsPipeClientFileIdentityReview
    {
        private const int FileIdInfoClass = 18; // FILE_INFO_BY_HANDLE_CLASS.FileIdInfo
        private const int FileIdInfoBytes = 24; // 8-byte volume + FILE_ID_128
        private const int MaxPathChars = 32768;

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetFileInformationByHandleEx(
            SafeFileHandle handle, int informationClass, IntPtr fileInfo,
            uint bufferBytes);

        [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true,
            EntryPoint="GetFinalPathNameByHandleW", CharSet=CharSet.Unicode)]
        private static extern uint GetFinalPathNameByHandle(
            SafeFileHandle handle, StringBuilder resolvedPath,
            uint bufferCharacters, uint flags);

        // A caller-supplied path here is only a NON-AUTHORITATIVE file probe.
        // The file ID is never a publisher pin or image-section proof.
        internal static OsFileIdentityReviewObservation ObserveFilePathOnly(
            string untrustedPath)
        {
            if (String.IsNullOrWhiteSpace(untrustedPath) ||
                !Path.IsPathRooted(untrustedPath))
                return OsFileIdentityReviewObservation.Unavailable();

            IntPtr info = IntPtr.Zero;
            try
            {
                using(FileStream file=new FileStream(untrustedPath,
                    FileMode.Open,FileAccess.Read,FileShare.Read))
                {
                    if(file.SafeFileHandle.IsInvalid)
                        return OsFileIdentityReviewObservation.Unavailable();
                    info=Marshal.AllocHGlobal(FileIdInfoBytes);
                    if(!GetFileInformationByHandleEx(file.SafeFileHandle,
                        FileIdInfoClass, info, FileIdInfoBytes))
                        return OsFileIdentityReviewObservation.Unavailable();

                    ulong volume=unchecked((ulong)Marshal.ReadInt64(info));
                    byte[] fileId=new byte[16];
                    Marshal.Copy(IntPtr.Add(info, 8),fileId,0,fileId.Length);
                    bool anyNonZero=false;
                    foreach(byte value in fileId) if(value!=0) anyNonZero=true;
                    if(!anyNonZero)
                        return OsFileIdentityReviewObservation.Unavailable();

                    StringBuilder finalPath=new StringBuilder(MaxPathChars);
                    uint length=GetFinalPathNameByHandle(
                        file.SafeFileHandle,finalPath,MaxPathChars,0);
                    if(length==0 || length>=MaxPathChars ||
                        String.IsNullOrWhiteSpace(finalPath.ToString()))
                        return OsFileIdentityReviewObservation.Unavailable();

                    // Never return or print the full path; it may contain
                    // account-specific local paths. Hashing is not attestation.
                    return new OsFileIdentityReviewObservation(
                        OsFileIdentityReviewState.OpenedFileObjectObserved,
                        volume,BitConverter.ToString(fileId).Replace("-",""),
                        true,false);
                }
            }
            catch(Exception)
            { return OsFileIdentityReviewObservation.Unavailable(); }
            finally
            { if(info!=IntPtr.Zero)Marshal.FreeHGlobal(info); }
        }

        internal static OsFileIdentityReviewObservation ObserveConnectedClientFileOnly(
            NamedPipeServerStream alreadyConnectedServerPipe)
        {
            try
            {
                if(alreadyConnectedServerPipe==null ||
                    !alreadyConnectedServerPipe.IsConnected)
                    return OsFileIdentityReviewObservation.Unavailable();

                OsPipeClientProcessProvenance process=
                    WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(
                        alreadyConnectedServerPipe);
                OsPipeClientSessionIntegrity session=
                    WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(
                        alreadyConnectedServerPipe);
                if(process==null || !process.KernelProcessObserved ||
                    session==null || !session.SessionIntegrityObserved ||
                    process.OsClientProcessId!=session.OsClientProcessId ||
                    process.OsProcessCreatedUtcFileTime!=
                        session.OsProcessCreatedUtcFileTime ||
                    String.IsNullOrWhiteSpace(process.OsImagePath))
                    return OsFileIdentityReviewObservation.Unavailable();

                OsFileIdentityReviewObservation file=
                    ObserveFilePathOnly(process.OsImagePath);
                if(!alreadyConnectedServerPipe.IsConnected ||
                    !file.NativeFileObjectObserved)
                    return OsFileIdentityReviewObservation.Unavailable();

                return new OsFileIdentityReviewObservation(
                    file.State,file.OsVolumeSerialNumber,file.OsFileId128Hex,
                    file.OsResolvedHandlePathObserved,true);
            }
            catch(Exception)
            { return OsFileIdentityReviewObservation.Unavailable(); }
        }
    }
}
