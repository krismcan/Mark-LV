#if !DEBUG || RELEASE || !C1_P286_ASYNC_PIPE_REVIEW_ONLY
#error P286_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED
#endif
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

        // TEST ONLY source substitution for P265. The Framework owns its APM
        // event until signaling finishes and invokes our user callback.
        // Only the user callback calls End*, after Framework completion signaling.
        // Close the completed event even when End* rejects an already disposed pipe.
        private sealed class Completion
        {
            private readonly object gate = new object();
            private readonly Func<IAsyncResult, int> end;
            private bool complete;
            private int count;
            private System.Runtime.ExceptionServices.ExceptionDispatchInfo failure;

            internal Completion(Func<IAsyncResult, int> endOperation) { end = endOperation; }

            internal void Callback(IAsyncResult result)
            {
                int value = 0;
                System.Runtime.ExceptionServices.ExceptionDispatchInfo error = null;
                try
                {
                    // Framework invokes this callback AFTER Set(). End* normally
                    // closes this event; explicit callback-side ownership also
                    // closes it when End* fails its disposed-stream precheck.
                    using (WaitHandle completedHandle = result.AsyncWaitHandle)
                        value = end(result);
                }
                catch (Exception caught)
                {
                    // Transfer End* failures to the serving thread, never let an
                    // expected cancellation escape on the IO completion thread.
                    error = System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(caught);
                }
                lock (gate)
                {
                    count = value; failure = error; complete = true;
                    Monitor.PulseAll(gate);
                }
            }

            internal int Wait(Stopwatch elapsed, int timeoutMs)
            {
                lock (gate)
                {
                    int remaining = Remaining(elapsed, timeoutMs);
                    while (!complete)
                    {
                        if (!Monitor.Wait(gate, remaining)) throw new TimeoutException();
                        if (!complete) remaining = Remaining(elapsed, timeoutMs);
                    }
                    if (failure != null) failure.Throw();
                    return count;
                }
            }
        }

        private int Wait(Completion completion, Stopwatch elapsed, int timeoutMs)
        {
            try { return completion.Wait(elapsed, timeoutMs); }
            // Cancel outside the monitor. A late callback still owns End* and its
            // cleanup; the waiter owns no native event to dispose prematurely.
            catch { Dispose(); throw; }
        }

        private void ReadExact(byte[] buffer, Stopwatch elapsed, int timeoutMs)
        {
            int offset = 0;
            while (offset < buffer.Length)
            {
                Remaining(elapsed, timeoutMs);
                var read = new Completion(pipe.EndRead);
                pipe.BeginRead(buffer, offset, buffer.Length - offset, read.Callback, null);
                int count = Wait(read, elapsed, timeoutMs);
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
                var connect = new Completion(delegate(IAsyncResult result) { pipe.EndWaitForConnection(result); return 0; });
                pipe.BeginWaitForConnection(connect.Callback, null);
                Wait(connect, elapsed, timeoutMs);
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
                var write = new Completion(delegate(IAsyncResult result) { pipe.EndWrite(result); return 0; });
                pipe.BeginWrite(denial, 0, denial.Length, write.Callback, null);
                Wait(write, elapsed, timeoutMs);
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
