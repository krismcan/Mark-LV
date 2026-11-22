using System;
using System.Runtime.CompilerServices;

[assembly: InternalsVisibleTo("P306.ProductService.Tests")]

namespace Nayeon.ByokC1.Service
{
    internal enum SyntheticOperation { Add = 1, Replace = 2, Delete = 3 }
    internal enum TransactionOwnerState { ActiveDenied, Stopped, Shutdown, Faulted, Disposed }
    internal enum TransactionDisposition
    { Denied, Cancelled, InvalidRequest, InvalidOperation, WrongOwner, StaleEpoch, Replay, OwnerTerminated }

    // Metadata only. Identity is an owner-scoped, strictly increasing nonzero number.
    // There is deliberately no payload, endpoint, callback, policy or execution port.
    internal sealed class SyntheticTransactionRequest
    {
        internal readonly Guid Owner;
        internal readonly long Epoch;
        internal readonly ulong RequestId;
        internal readonly SyntheticOperation Operation;

        internal SyntheticTransactionRequest(Guid owner, long epoch, ulong requestId, SyntheticOperation operation)
        { Owner = owner; Epoch = epoch; RequestId = requestId; Operation = operation; }
    }

    internal sealed class SyntheticTransactionResult
    {
        internal readonly SyntheticTransactionRequest Request;
        internal readonly Guid Owner;
        internal readonly long Epoch;
        internal readonly TransactionOwnerState State;
        internal readonly TransactionDisposition Disposition;
        internal bool Allowed { get { return false; } }
        internal SyntheticTransactionResult(SyntheticTransactionRequest request, Guid owner, long epoch,
            TransactionOwnerState state, TransactionDisposition disposition)
        { Request = request; Owner = owner; Epoch = epoch; State = state; Disposition = disposition; }
    }

    // Fixed-size state; no pending work, queue, history, handles, timers or external calls.
    // Every attempt linearizes to a terminal denial under the same gate as cancellation.
    internal sealed class SyntheticTransactionOwner : IDisposable
    {
        private readonly object gate = new object();
        private readonly Guid owner = Guid.NewGuid();
        private long epoch = 1;
        private ulong highWater;
        private TransactionOwnerState state = TransactionOwnerState.ActiveDenied;

        internal SyntheticTransactionResult Observe()
        { lock (gate) { return Result(null, TransactionDisposition.Denied); } }

        internal SyntheticTransactionResult Deny(SyntheticTransactionRequest request)
        { lock (gate) { return Evaluate(request, false); } }

        internal SyntheticTransactionResult Cancel(SyntheticTransactionRequest request)
        { lock (gate) { return Evaluate(request, true); } }

        private SyntheticTransactionResult Evaluate(SyntheticTransactionRequest request, bool cancel)
        {
            // Terminal owner takes precedence, including malformed or replayed attempts.
            if (state != TransactionOwnerState.ActiveDenied) return Result(request, TransactionDisposition.OwnerTerminated);
            if (request == null || request.RequestId == 0) return Result(request, TransactionDisposition.InvalidRequest);
            if (request.Owner != owner) return Result(request, TransactionDisposition.WrongOwner);
            if (request.Epoch != epoch) return Result(request, TransactionDisposition.StaleEpoch);
            if (request.Operation != SyntheticOperation.Add && request.Operation != SyntheticOperation.Replace &&
                request.Operation != SyntheticOperation.Delete) return Result(request, TransactionDisposition.InvalidOperation);
            if (request.RequestId <= highWater) return Result(request, TransactionDisposition.Replay);
            highWater = request.RequestId; // Reserve once for both cancellation and denial. Never evict or wrap.
            return Result(request, cancel ? TransactionDisposition.Cancelled : TransactionDisposition.Denied);
        }

        private SyntheticTransactionResult Result(SyntheticTransactionRequest request, TransactionDisposition disposition)
        { return new SyntheticTransactionResult(request, owner, epoch, state, disposition); }

        private void Terminate(TransactionOwnerState reason)
        {
            lock (gate)
            {
                if (state == TransactionOwnerState.ActiveDenied) { epoch = 2; state = reason; }
                // Disposal cannot revive or increment the epoch again.
                if (reason == TransactionOwnerState.Disposed) state = TransactionOwnerState.Disposed;
            }
        }

        internal void Stop() { Terminate(TransactionOwnerState.Stopped); }
        internal void Shutdown() { Terminate(TransactionOwnerState.Shutdown); }
        internal void Fault() { Terminate(TransactionOwnerState.Faulted); }
        public void Dispose() { Terminate(TransactionOwnerState.Disposed); }
    }
}
