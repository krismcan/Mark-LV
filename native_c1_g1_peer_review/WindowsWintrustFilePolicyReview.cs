// P116 — Windows WinVerifyTrust native code-signing POLICY OBSERVATION ONLY.
// G1 review-only: a signed file is not a trusted installed consent broker.
// No approved service-owned publisher pin/trust anchor exists. This module
// deliberately cannot issue consent, trust a UI, or permit credential effects.
// WinVerifyTrust checks the opened file handle with cache-only URL retrieval.
// Loaded process image <-> inspected file mapping is NOT proven.
using System;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;

namespace Nayeon.ByokC1
{
    internal enum OsWintrustReviewState
    {
        Unavailable,
        NativePolicyRejected,
        NativePolicyAcceptedButUnpinned
    }

    internal sealed class OsWintrustReviewObservation
    {
        internal readonly OsWintrustReviewState State;
        internal readonly bool NativePolicyAttempted;
        internal readonly bool NativePolicyAccepted;
        internal readonly bool ConnectedPipeClientObserved;

        internal OsWintrustReviewObservation(
            OsWintrustReviewState state, bool attempted, bool accepted,
            bool connectedClient)
        {
            State = state;
            NativePolicyAttempted = attempted;
            NativePolicyAccepted = accepted;
            ConnectedPipeClientObserved = connectedClient;
        }

        internal bool ApprovedPublisherPinConfigured { get { return false; } }
        internal bool LoadedProcessImageFileIdentityBound { get { return false; } }
        internal bool SignedTrustedConsentImageVerified { get { return false; } }
        internal bool TrustedInteractiveDesktopVerified { get { return false; } }
        internal bool ExplicitHumanConsentVerified { get { return false; } }
        internal bool ProtectedOneUseGrantIssued { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }

        internal static OsWintrustReviewObservation Unavailable()
        {
            return new OsWintrustReviewObservation(
                OsWintrustReviewState.Unavailable, false, false, false);
        }

        public override string ToString()
        { return "<P116 OS WinVerifyTrust file policy observation only; G1 consent unavailable>"; }
    }

    internal static class WindowsWintrustFilePolicyReview
    {
        private const uint WtdUiNone = 2;
        private const uint WtdChoiceFile = 1;
        private const uint WtdStateActionVerify = 1;
        private const uint WtdStateActionClose = 2;
        private const uint WtdRevokeWholeChain = 1;
        private const uint WtdCacheOnlyUrlRetrieval = 0x00001000;
        private const uint WtdUiContextExecute = 0;
        private static readonly Guid GenericVerifyV2 =
            new Guid("00AAC56B-CD44-11D0-8CC2-00C04FC295EE");

        [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
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

        // The return value is a native Win32 trust status: only EXACT zero
        // indicates OS policy success; do not use HRESULT sign checks.
        [DllImport("wintrust.dll", CharSet=CharSet.Unicode,
            ExactSpelling=true, PreserveSig=true)]
        private static extern uint WinVerifyTrust(
            IntPtr hwnd, ref Guid action, ref WintrustData data);

        // This deliberately accepts a path only for negative testing or
        // NON-AUTHORITATIVE file policy inspection. It never compares a signer
        // against a service-owned anchor, loaded image section, or user click.
        internal static OsWintrustReviewObservation ObserveFilePolicyOnly(
            string untrustedPath)
        {
            if (String.IsNullOrWhiteSpace(untrustedPath) ||
                !Path.IsPathRooted(untrustedPath))
                return OsWintrustReviewObservation.Unavailable();

            IntPtr fileInfoPtr = IntPtr.Zero;
            bool fileInfoMarshaled = false;
            try
            {
                // Open a read-only handle and give that SAME handle to WinTrust.
                // Sharing only read also prevents most ordinary concurrent
                // writable opens during inspection. It does not authenticate
                // the memory-mapped image that the pipe client actually ran.
                using (FileStream file = new FileStream(untrustedPath,
                    FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    if (file.Length <= 0 || file.SafeFileHandle.IsInvalid)
                        return OsWintrustReviewObservation.Unavailable();
                    WintrustFileInfo input = new WintrustFileInfo();
                    input.cbStruct = (uint)Marshal.SizeOf(typeof(WintrustFileInfo));
                    input.pcwszFilePath = untrustedPath;
                    input.hFile = file.SafeFileHandle.DangerousGetHandle();
                    input.pgKnownSubject = IntPtr.Zero;
                    fileInfoPtr = Marshal.AllocHGlobal(Marshal.SizeOf(
                        typeof(WintrustFileInfo)));
                    Marshal.StructureToPtr(input, fileInfoPtr, false);
                    fileInfoMarshaled = true;

                    WintrustData data = new WintrustData();
                    data.cbStruct = (uint)Marshal.SizeOf(typeof(WintrustData));
                    data.dwUIChoice = WtdUiNone;
                    data.fdwRevocationChecks = WtdRevokeWholeChain;
                    data.dwUnionChoice = WtdChoiceFile;
                    data.pFile = fileInfoPtr;
                    data.dwStateAction = WtdStateActionVerify;
                    data.dwProvFlags = WtdCacheOnlyUrlRetrieval;
                    data.dwUIContext = WtdUiContextExecute;

                    Guid action = GenericVerifyV2;
                    uint result;
                    try
                    {
                        result = WinVerifyTrust(IntPtr.Zero, ref action, ref data);
                    }
                    finally
                    {
                        // Explicitly close any native provider state if created.
                        if (data.hWVTStateData != IntPtr.Zero)
                        {
                            data.dwStateAction = WtdStateActionClose;
                            try { WinVerifyTrust(IntPtr.Zero, ref action, ref data); }
                            catch (Exception) { /* no grant; cleanup best effort */ }
                        }
                    }
                    bool accepted = result == 0;
                    return new OsWintrustReviewObservation(
                        accepted ? OsWintrustReviewState.NativePolicyAcceptedButUnpinned
                                 : OsWintrustReviewState.NativePolicyRejected,
                        true, accepted, false);
                }
            }
            catch (Exception)
            {
                return OsWintrustReviewObservation.Unavailable();
            }
            finally
            {
                if (fileInfoPtr != IntPtr.Zero)
                {
                    if (fileInfoMarshaled)
                        Marshal.DestroyStructure(fileInfoPtr,
                            typeof(WintrustFileInfo));
                    Marshal.FreeHGlobal(fileInfoPtr);
                }
            }
        }

        internal static OsWintrustReviewObservation ObserveConnectedClientFilePolicyOnly(
            NamedPipeServerStream alreadyConnectedServerPipe)
        {
            try
            {
                if (alreadyConnectedServerPipe == null ||
                    !alreadyConnectedServerPipe.IsConnected)
                    return OsWintrustReviewObservation.Unavailable();

                OsPipeClientProcessProvenance process =
                    WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(
                        alreadyConnectedServerPipe);
                OsPipeClientSessionIntegrity session =
                    WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(
                        alreadyConnectedServerPipe);
                if (process == null || !process.KernelProcessObserved ||
                    session == null || !session.SessionIntegrityObserved ||
                    process.OsClientProcessId != session.OsClientProcessId ||
                    process.OsProcessCreatedUtcFileTime !=
                        session.OsProcessCreatedUtcFileTime ||
                    String.IsNullOrWhiteSpace(process.OsImagePath))
                    return OsWintrustReviewObservation.Unavailable();

                OsWintrustReviewObservation file =
                    ObserveFilePolicyOnly(process.OsImagePath);
                if (!alreadyConnectedServerPipe.IsConnected ||
                    !file.NativePolicyAttempted)
                    return OsWintrustReviewObservation.Unavailable();

                // This is a transient file signature observation tied to
                // an OS-observed path, not a durable peer image attestation.
                return new OsWintrustReviewObservation(
                    file.State, true, file.NativePolicyAccepted, true);
            }
            catch (Exception)
            {
                return OsWintrustReviewObservation.Unavailable();
            }
        }
    }
}
