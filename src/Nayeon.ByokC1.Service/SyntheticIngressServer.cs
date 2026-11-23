using System;
using System.IO;
using System.IO.Pipes;
using System.Runtime.CompilerServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

[assembly: InternalsVisibleTo("P309.ProductService.Tests")]

namespace Nayeon.ByokC1.Service
{
    // Denial-only metadata ingress. No client-selected owner, epoch, payload or dispatch.
    internal sealed class SyntheticIngressServer : IDisposable
    {
        internal const string Endpoint = "NayeonV1ByokCustody.SyntheticDenied.v1";
        internal const string Reply = "C1|DENIED|HOLD|NO_CREDENTIALS";
        private readonly SyntheticTransactionOwner owner;
        private readonly NamedPipeServerStream pipe;
        private readonly Task worker;
        private readonly CancellationTokenSource acceptCancellation = new CancellationTokenSource();
        private int disposed;
        private int outcome; // 0 waiting, 1 denial written, 2 refused. Never authorization.

        internal SyntheticIngressServer(SyntheticTransactionOwner owner) : this(Endpoint, owner) { }

        // Friend-test seam only; arbitrary paths and the product endpoint are refused.
        internal SyntheticIngressServer(SyntheticTransactionOwner owner, string isolatedEndpoint)
            : this(TestEndpoint(isolatedEndpoint), owner) { }

        private static string TestEndpoint(string name)
        {
            const string prefix = "P309.Disposable.";
            Guid id;
            if (name == null || !name.StartsWith(prefix, StringComparison.Ordinal) ||
                !Guid.TryParseExact(name.Substring(prefix.Length), "N", out id) || id == Guid.Empty ||
                name != prefix + id.ToString("N"))
                throw new ArgumentException("Isolated synthetic endpoint required.");
            return name;
        }

        private SyntheticIngressServer(string endpoint, SyntheticTransactionOwner owner)
        {
            if (owner == null) throw new ArgumentNullException("owner");
            this.owner = owner;
            try
            {
                if (owner.Observe().State != TransactionOwnerState.ActiveDenied)
                    throw new InvalidOperationException("Synthetic owner retired.");
                // Same protected owner-SID DACL as P305, including NETWORK deny.
                SecurityIdentifier sid = CustodyService.ReadProcessSid();
                var security = new PipeSecurity();
                security.SetAccessRuleProtection(true, false);
                security.SetOwner(sid);
                security.AddAccessRule(new PipeAccessRule(
                    new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
                    PipeAccessRights.FullControl, AccessControlType.Deny));
                security.AddAccessRule(new PipeAccessRule(sid,
                    PipeAccessRights.ReadWrite, AccessControlType.Allow));
                pipe = new NamedPipeServerStream(endpoint, PipeDirection.InOut, 1,
                    PipeTransmissionMode.Message, PipeOptions.Asynchronous, 14, 128,
                    security, HandleInheritability.None);
                worker = RunAsync();
            }
            catch
            {
                owner.Fault();
                if (pipe != null) pipe.Dispose();
                acceptCancellation.Dispose();
                throw;
            }
        }

        internal Task Completion { get { return worker; } }
        internal bool Refused { get { return Volatile.Read(ref outcome) == 2; } }

        // Dispose cancels actual overlapped I/O; always observe its completion before
        // releasing buffers. No abandoned Task.Run, retries or blocking pipe drains.
        private async Task WithDeadline(Task operation, int milliseconds)
        {
            using (var timer = new CancellationTokenSource())
            {
                Task delay = Task.Delay(milliseconds, timer.Token);
                try
                {
                    if (await Task.WhenAny(operation, delay).ConfigureAwait(false) != operation)
                    {
                        owner.Fault(); // Connected-peer deadline only; quiet startup is valid.
                        pipe.Dispose();
                        try { await operation.ConfigureAwait(false); }
                        catch (IOException) { }
                        catch (ObjectDisposedException) { }
                        catch (OperationCanceledException) { }
                        throw new TimeoutException("Synthetic ingress deadline; HOLD.");
                    }
                    await operation.ConfigureAwait(false);
                }
                finally { timer.Cancel(); }
            }
        }

        private void RequireActiveIdentity()
        {
            CustodyService.RequireNoImpersonation();
            if (Volatile.Read(ref disposed) != 0 || owner.Observe().State != TransactionOwnerState.ActiveDenied)
                throw new InvalidOperationException("Synthetic ingress retired.");
        }

        private async Task RunAsync()
        {
            try
            {
                RequireActiveIdentity();
                // No idle timeout. Cancellation targets the kernel overlapped accept
                // when the service retires, even if no client has ever connected.
                await pipe.WaitForConnectionAsync(acceptCancellation.Token).ConfigureAwait(false);
                RequireActiveIdentity();
                // Extra byte plus message completeness rejects oversized messages without
                // a continuation read. Partial messages never accumulate into a request.
                byte[] frame = new byte[14];
                Task<int> read = pipe.ReadAsync(frame, 0, frame.Length);
                await WithDeadline(read, 1000).ConfigureAwait(false);
                RequireActiveIdentity();
                if (read.Result != 13 || !pipe.IsMessageComplete ||
                    frame[0] != 67 || frame[1] != 49 || frame[2] != 84 || frame[3] != 49 ||
                    frame[12] < 1 || frame[12] > 3)
                    throw new InvalidDataException("Synthetic frame refused.");
                ulong id = 0;
                for (int i = 0; i < 8; i++) id |= (ulong)frame[4 + i] << (8 * i);
                if (id == 0) throw new InvalidDataException("Synthetic identity refused.");
                SyntheticTransactionResult observed = owner.Observe();
                var request = new SyntheticTransactionRequest(observed.Owner, observed.Epoch,
                    id, (SyntheticOperation)frame[12]);
                SyntheticTransactionResult result = owner.Deny(request);
                if (result == null || result.Allowed || result.Disposition != TransactionDisposition.Denied)
                    throw new InvalidOperationException("Synthetic denial required.");
                RequireActiveIdentity();
                byte[] reply = Encoding.ASCII.GetBytes(Reply);
                await WithDeadline(pipe.WriteAsync(reply, 0, reply.Length), 1000).ConfigureAwait(false);
                RequireActiveIdentity();
                Interlocked.Exchange(ref outcome, 1);
            }
            catch (Exception)
            {
                owner.Fault();
                Interlocked.Exchange(ref outcome, 2);
            }
            finally
            {
                // Retain a buffered denial until disposal so closure cannot discard it.
                // No second read, connection, retry or request task exists.
                if (Volatile.Read(ref outcome) != 1) pipe.Dispose();
                try { CustodyService.RequireNoImpersonation(); }
                catch (Exception)
                {
                    owner.Fault();
                    Interlocked.Exchange(ref outcome, 2);
                    pipe.Dispose();
                }
            }
        }

        public void Dispose()
        {
            owner.Stop(); // Owner always retires before handle closure or worker join.
            bool closing = Interlocked.Exchange(ref disposed, 1) == 0;
            if (closing)
            {
                try { acceptCancellation.Cancel(); }
                finally { pipe.Dispose(); }
            }
            // Worker calls only the owner's independent lock, never the service lock.
            if (!worker.Wait(3000)) throw new TimeoutException("Synthetic cleanup incomplete; HOLD.");
            // Only the closing caller uses/disposes the source; concurrent callers
            // join the same worker without racing Cancel against source disposal.
            if (closing) acceptCancellation.Dispose();
        }
    }
}
