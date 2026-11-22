using System;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Nayeon.ByokC1.Service
{
    // One connection and one fixed query per lifetime. No operation dispatcher exists.
    // The default constructor is the product seam; the friend-test overload isolates names.
    internal sealed class StatusPipeServer : IDisposable
    {
        internal const string Endpoint = "NayeonV1ByokCustody.Status.v1";
        internal const string Reply = "C1|NOT_AUTHORIZED|HOLD|NO_CREDENTIALS";
        private readonly NamedPipeServerStream pipe;
        private readonly Task worker;
        private int disposed;
        private int outcome; // 0 waiting; 1 fixed reply sent; 2 refusal/fault. Never authority.

        internal StatusPipeServer() : this(Endpoint) { }

        internal StatusPipeServer(string isolatedEndpoint)
        {
            SecurityIdentifier sid = CustodyService.ReadProcessSid();
            var security = new PipeSecurity();
            security.SetAccessRuleProtection(true, false);
            security.SetOwner(sid);
            security.AddAccessRule(new PipeAccessRule(
                new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
                PipeAccessRights.FullControl, AccessControlType.Deny));
            security.AddAccessRule(new PipeAccessRule(sid,
                PipeAccessRights.ReadWrite, AccessControlType.Allow));
            pipe = new NamedPipeServerStream(isolatedEndpoint, PipeDirection.InOut, 1,
                PipeTransmissionMode.Message, PipeOptions.Asynchronous, 4, 128,
                security, HandleInheritability.None);
            try { worker = RunAsync(); }
            catch { pipe.Dispose(); throw; }
        }

        internal Task Completion { get { return worker; } }
        internal bool Refused { get { return Volatile.Read(ref outcome) == 2; } }

        // A deadline disposes the actual handle, then observes completion of its OS I/O.
        // No abandoned Task.Run threads, impersonation, callbacks or injected effects.
        internal static async Task WithDeadline(Task operation, IDisposable stream, int milliseconds)
        {
            using (var timer = new CancellationTokenSource())
            {
                Task delay = Task.Delay(milliseconds, timer.Token);
                if (await Task.WhenAny(operation, delay).ConfigureAwait(false) != operation)
                {
                    stream.Dispose();
                    try { await operation.ConfigureAwait(false); }
                    catch (IOException) { }
                    catch (ObjectDisposedException) { }
                    catch (OperationCanceledException) { }
                    throw new TimeoutException("Status deadline; HOLD.");
                }
                timer.Cancel();
                await operation.ConfigureAwait(false);
            }
        }

        private async Task RunAsync()
        {
            try
            {
                CustodyService.RequireNoImpersonation();
                await pipe.WaitForConnectionAsync().ConfigureAwait(false);
                CustodyService.RequireNoImpersonation();
                byte[] frame = new byte[4];
                Task<int> read = pipe.ReadAsync(frame, 0, frame.Length);
                await WithDeadline(read, pipe, 1000).ConfigureAwait(false);
                CustodyService.RequireNoImpersonation();
                if (read.Result != 4 || !pipe.IsMessageComplete ||
                    frame[0] != 67 || frame[1] != 49 || frame[2] != 83 || frame[3] != 49)
                    throw new InvalidDataException("Status frame refused.");
                byte[] reply = Encoding.ASCII.GetBytes(Reply);
                await WithDeadline(pipe.WriteAsync(reply, 0, reply.Length), pipe, 1000).ConfigureAwait(false);
                CustodyService.RequireNoImpersonation();
                Interlocked.Exchange(ref outcome, 1);
            }
            catch (Exception)
            {
                // A terminal nonsecret refusal; exceptions never trigger retry or privilege.
                Interlocked.Exchange(ref outcome, 2);
            }
            finally
            {
                // Retain a successful instance until owner disposal: closing immediately
                // after buffered WriteAsync could discard a reply before the client reads.
                // No re-listen, worker, retry or further request processing follows.
                if (Volatile.Read(ref outcome) != 1) pipe.Dispose();
                try { CustodyService.RequireNoImpersonation(); }
                catch (Exception) { Interlocked.Exchange(ref outcome, 2); pipe.Dispose(); }
            }
        }

        public void Dispose()
        {
            if (Interlocked.Exchange(ref disposed, 1) == 0) pipe.Dispose();
            // Worker never needs a host lock or caller continuation to finish.
            if (!worker.Wait(3000)) throw new TimeoutException("Status cleanup incomplete; HOLD.");
        }
    }
}
