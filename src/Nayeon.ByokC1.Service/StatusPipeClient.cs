using System;
using System.IO;
using System.IO.Pipes;
using System.Security.Principal;
using System.Text;
using System.Threading.Tasks;

namespace Nayeon.ByokC1.Service
{
    internal sealed class StatusObservation
    {
        internal bool ExactReplyObserved { get; private set; }
        internal string Disposition { get { return "UNTRUSTED_HOLD"; } }
        internal StatusObservation(bool exact) { ExactReplyObserved = exact; }
    }

    internal static class StatusPipeClient
    {
        internal static Task<StatusObservation> QueryAsync()
        { return QueryAsync(StatusPipeServer.Endpoint, 1000); }

        // Internal friend-test seam only. No caller-defined bytes or operation payload.
        internal static async Task<StatusObservation> QueryAsync(string isolatedEndpoint, int timeoutMilliseconds)
        {
            if (timeoutMilliseconds < 1 || timeoutMilliseconds > 2000)
                throw new ArgumentOutOfRangeException("timeoutMilliseconds");
            try
            {
                CustodyService.RequireNoImpersonation();
                using (var pipe = new NamedPipeClientStream(".", isolatedEndpoint, PipeDirection.InOut,
                    PipeOptions.Asynchronous, TokenImpersonationLevel.Anonymous, HandleInheritability.None))
                {
                    await pipe.ConnectAsync(timeoutMilliseconds).ConfigureAwait(false);
                    pipe.ReadMode = PipeTransmissionMode.Message;
                    CustodyService.RequireNoImpersonation();
                    byte[] query = { 67, 49, 83, 49 }; // C1S1, sole supported request.
                    await StatusPipeServer.WithDeadline(pipe.WriteAsync(query, 0, query.Length),
                        pipe, timeoutMilliseconds).ConfigureAwait(false);
                    byte[] expected = Encoding.ASCII.GetBytes(StatusPipeServer.Reply);
                    byte[] reply = new byte[expected.Length];
                    Task<int> read = pipe.ReadAsync(reply, 0, reply.Length);
                    await StatusPipeServer.WithDeadline(read, pipe, timeoutMilliseconds).ConfigureAwait(false);
                    CustodyService.RequireNoImpersonation();
                    bool exact = read.Result == expected.Length && pipe.IsMessageComplete;
                    for (int i = 0; i < reply.Length; i++) exact &= reply[i] == expected[i];
                    // Exact bytes are only an observation: no production peer attestation.
                    return new StatusObservation(exact);
                }
            }
            catch (Exception) { return new StatusObservation(false); }
            finally { CustodyService.RequireNoImpersonation(); }
        }
    }
}
