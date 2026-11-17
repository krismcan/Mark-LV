#if !C1_P265_DEVELOPMENT_ONLY
#error P265_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED
#endif
#if !DEBUG
#error P265_NO_RELEASE_BUILD
#endif
// Standalone DEVELOPMENT adapter. Never compose with the P264 service/effect graph.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Security;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

namespace Nayeon.ByokC1.P265Development
{
    internal enum DenialOperation : byte
    { ObserveDenial = 1, RejectCredential = 2, RejectStore = 3, RejectPrivileged = 4 }

    internal enum DenialReason
    { DevelopmentHold, InvalidFrame, PeerRejected, Replay, Capacity, Timeout, Disconnected, Closed, Busy, Fault }

    // Local evidence only. Neither observed identity nor a well-formed request grants authority.
    internal sealed class DenialEvidence
    {
        internal readonly DenialReason Reason;
        internal readonly bool PeerObserved, SidMatched, ThreadRestored, ReplyWritten;
        internal bool CredentialAllowed { get { return false; } }
        internal bool StoreAllowed { get { return false; } }
        internal bool PrivilegedAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
        internal DenialEvidence(DenialReason reason, bool observed, bool matched, bool restored, bool replied)
        { Reason = reason; PeerObserved = observed; SidMatched = matched; ThreadRestored = restored; ReplyWritten = replied; }
    }

    internal sealed class DevelopmentPipeAdapter : IDisposable
    {
        internal const int BodyLength = 24, FrameLength = 28, ReplyLength = 8, ReplayCapacity = 128;
        internal const int MinimumTimeoutMs = 50, MaximumTimeoutMs = 2000;
        private readonly SecurityIdentifier expectedSid;
        private readonly NamedPipeServerStream pipe;
        private readonly HashSet<Guid> consumed = new HashSet<Guid>();
        private int serving, closed;
        internal readonly string Endpoint;

        // Only trusted test-side provisioning supplies this OS identity; no wire identity input exists.
        // This deliberately selects the CURRENT developer principal, never an assumed service SID.
        internal DevelopmentPipeAdapter(WindowsIdentity trustedExpected)
        {
            if (Environment.OSVersion.Platform != PlatformID.Win32NT)
                throw new PlatformNotSupportedException();
            if (trustedExpected == null || trustedExpected.User == null)
                throw new ArgumentException("P265_EXPECTED_IDENTITY_REQUIRED");
            RequireNoThreadIdentity();
            using (WindowsIdentity current = WindowsIdentity.GetCurrent())
            {
                if (!SameSid(trustedExpected.User, current.User))
                    throw new ArgumentException("P265_CURRENT_DEVELOPER_ONLY");
            }
            expectedSid = trustedExpected.User;
            Endpoint = "Nayeon-P265-dev-" + Guid.NewGuid().ToString("N");
            var security = new PipeSecurity();
            security.SetAccessRuleProtection(true, false);
            security.SetOwner(expectedSid);
            security.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
                PipeAccessRights.FullControl, AccessControlType.Deny));
            security.AddAccessRule(new PipeAccessRule(expectedSid,
                PipeAccessRights.ReadWrite, AccessControlType.Allow));
            // Client rights only (.NET adds Synchronize). Creation failure propagates;
            // never retry with server-instance rights granted to same-SID callers.
            pipe = new NamedPipeServerStream(Endpoint, PipeDirection.InOut, 1,
                PipeTransmissionMode.Message, PipeOptions.Asynchronous, FrameLength, ReplyLength, security,
                HandleInheritability.None, (PipeAccessRights)0);
        }

        internal static bool SameSid(SecurityIdentifier observed, SecurityIdentifier expected)
        { return observed != null && expected != null && observed.Equals(expected); }

        private static void RequireNoThreadIdentity()
        {
            using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true))
                if (thread != null) throw new SecurityException("P265_THREAD_IDENTITY_PRESENT");
        }

        // A single total deadline covers connect, partial reads, peer capture and reply.
        // RunAsClient is an OS call, not arbitrary caller work. A runner watchdog additionally
        // bounds the process if the OS itself fails to return (no in-process guarantee of that).
        private static int Remaining(Stopwatch elapsed, int timeoutMs)
        {
            long remaining = timeoutMs - elapsed.ElapsedMilliseconds;
            if (remaining <= 0) throw new TimeoutException();
            return (int)remaining;
        }

        // The caller owns the wait handle through End*, including cancellation cleanup.
        private void Wait(WaitHandle handle, Stopwatch elapsed, int timeoutMs)
        {
            try
            {
                if (!handle.WaitOne(Remaining(elapsed, timeoutMs)))
                    throw new TimeoutException();
            }
            catch { Dispose(); throw; } // also cancel if Remaining expires before WaitOne
        }

        private void ReadExact(byte[] buffer, Stopwatch elapsed, int timeoutMs)
        {
            int offset = 0;
            while (offset < buffer.Length)
            {
                Remaining(elapsed, timeoutMs);
                IAsyncResult read = pipe.BeginRead(buffer, offset, buffer.Length - offset, null, null);
                int count = 0;
                using (WaitHandle handle = read.AsyncWaitHandle)
                {
                    bool ready = false;
                    try { Wait(handle, elapsed, timeoutMs); ready = true; }
                    finally
                    {
                        // End exactly once before releasing the handle. Preserve a wait failure
                        // when End reports the expected pipe cancellation/disposal exception.
                        try { count = pipe.EndRead(read); }
                        catch (IOException) { if (ready) throw; }
                        catch (ObjectDisposedException) { if (ready) throw; }
                    }
                }
                if (count == 0) throw new EndOfStreamException();
                offset += count;
            }
        }

        // Fixed little-endian length=24; C1P5, version=1, operation, zero flags, nonzero 16-byte ID.
        // There is no text field, SID/PID claim, secret/candidate body, extensible opcode or callback.
        private bool ReadRequest(Stopwatch elapsed, int timeoutMs, out Guid requestId)
        {
            requestId = Guid.Empty;
            byte[] header = new byte[4];
            ReadExact(header, elapsed, timeoutMs);
            if (header[0] != BodyLength || header[1] != 0 || header[2] != 0 || header[3] != 0)
                return false; // reject before allocating/reading any claimed payload
            byte[] body = new byte[BodyLength];
            ReadExact(body, elapsed, timeoutMs);
            if (!pipe.IsMessageComplete || body[0] != 67 || body[1] != 49 || body[2] != 80 || body[3] != 53 ||
                body[4] != 1 || body[6] != 0 || body[7] != 0)
                return false;
            switch ((DenialOperation)body[5])
            {
                case DenialOperation.ObserveDenial:
                case DenialOperation.RejectCredential:
                case DenialOperation.RejectStore:
                case DenialOperation.RejectPrivileged:
                    break; // all four are explicit denials; never forward or perform an operation
                default: return false;
            }
            byte[] id = new byte[16];
            Buffer.BlockCopy(body, 8, id, 0, id.Length);
            requestId = new Guid(id);
            return requestId != Guid.Empty;
        }

        internal DenialEvidence ServeOnce(int timeoutMs)
        {
            if (timeoutMs < MinimumTimeoutMs || timeoutMs > MaximumTimeoutMs)
                throw new ArgumentOutOfRangeException("timeoutMs");
            if (Interlocked.CompareExchange(ref serving, 1, 0) != 0)
                return new DenialEvidence(DenialReason.Busy, false, false, false, false);
            bool observed = false, matched = false, restored = false, replied = false;
            DenialReason reason = DenialReason.Fault;
            try
            {
                if (Interlocked.CompareExchange(ref closed, 0, 0) != 0)
                    return new DenialEvidence(DenialReason.Closed, false, false, false, false);
                RequireNoThreadIdentity();
                Stopwatch elapsed = Stopwatch.StartNew();
                IAsyncResult connect = pipe.BeginWaitForConnection(null, null);
                using (WaitHandle handle = connect.AsyncWaitHandle)
                {
                    bool ready = false;
                    try { Wait(handle, elapsed, timeoutMs); ready = true; }
                    finally
                    {
                        try { pipe.EndWaitForConnection(connect); }
                        catch (IOException) { if (ready) throw; }
                        catch (ObjectDisposedException) { if (ready) throw; }
                    }
                }
                Guid requestId;
                if (!ReadRequest(elapsed, timeoutMs, out requestId))
                    return new DenialEvidence(DenialReason.InvalidFrame, false, false, false, false);
                else
                {
                    // Read first: Windows named-pipe impersonation uses the last message read.
                    // Capture only OS token data; never use a string from the client as identity.
                    try
                    {
                        pipe.RunAsClient(delegate
                        {
                            using (WindowsIdentity peer = WindowsIdentity.GetCurrent(true))
                            {
                                observed = peer != null && peer.User != null && !peer.IsAnonymous &&
                                    peer.ImpersonationLevel == TokenImpersonationLevel.Impersonation;
                                matched = observed && SameSid(peer.User, expectedSid);
                            }
                        });
                    }
                    finally
                    {
                        RequireNoThreadIdentity(); // failed revert faults/closes; no reply or protected work
                        restored = true;
                    }
                    Remaining(elapsed, timeoutMs);
                    // No eviction. Reservations span reconnects for this adapter lifetime only.
                    if (consumed.Contains(requestId)) reason = DenialReason.Replay;
                    else if (consumed.Count >= ReplayCapacity) reason = DenialReason.Capacity;
                    else
                    {
                        consumed.Add(requestId);
                        reason = matched ? DenialReason.DevelopmentHold : DenialReason.PeerRejected;
                    }
                }
                // Identical non-secret reply for all framed refusals. No receipt/ID/token reflection.
                byte[] denial = new byte[] { 67, 49, 68, 78, 1, 1, 0, 0 };
                Remaining(elapsed, timeoutMs);
                IAsyncResult write = pipe.BeginWrite(denial, 0, denial.Length, null, null);
                using (WaitHandle handle = write.AsyncWaitHandle)
                {
                    bool ready = false;
                    try { Wait(handle, elapsed, timeoutMs); ready = true; }
                    finally
                    {
                        try { pipe.EndWrite(write); }
                        catch (IOException) { if (ready) throw; }
                        catch (ObjectDisposedException) { if (ready) throw; }
                    }
                }
                Remaining(elapsed, timeoutMs);
                replied = true;
                // A bounded one-byte delivery marker avoids Disconnect discarding a buffered
                // reply. It is NOT consent or authorization. No WaitForPipeDrain is used.
                byte[] delivery = new byte[1];
                ReadExact(delivery, elapsed, timeoutMs);
                if (delivery[0] != 165 || !pipe.IsMessageComplete) reason = DenialReason.InvalidFrame;
                Remaining(elapsed, timeoutMs);
            }
            catch (TimeoutException) { reason = DenialReason.Timeout; Dispose(); }
            catch (EndOfStreamException) { reason = DenialReason.Disconnected; Dispose(); }
            catch (IOException) { reason = DenialReason.Disconnected; Dispose(); }
            catch (UnauthorizedAccessException) { reason = DenialReason.PeerRejected; Dispose(); }
            catch (SecurityException) { reason = DenialReason.Fault; Dispose(); }
            catch (ObjectDisposedException) { reason = DenialReason.Closed; Dispose(); }
            catch (InvalidOperationException) { reason = DenialReason.Fault; Dispose(); }
            finally
            {
                try
                {
                    if (Interlocked.CompareExchange(ref closed, 0, 0) == 0 && pipe.IsConnected)
                        pipe.Disconnect();
                }
                catch (IOException) { reason = DenialReason.Fault; Dispose(); }
                catch (ObjectDisposedException) { reason = DenialReason.Closed; }
                catch (InvalidOperationException) { reason = DenialReason.Fault; Dispose(); }
                Interlocked.Exchange(ref serving, 0);
            }
            return new DenialEvidence(reason, observed, matched, restored, replied);
        }

        public void Dispose()
        {
            if (Interlocked.Exchange(ref closed, 1) == 0) pipe.Dispose();
        }
    }
}
