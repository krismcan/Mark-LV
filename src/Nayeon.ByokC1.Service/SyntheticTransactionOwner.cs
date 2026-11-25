using System;
using System.Runtime.CompilerServices;
using System.Threading;

[assembly: InternalsVisibleTo("P306.ProductService.Tests")]
[assembly: InternalsVisibleTo("P307.ProductService.Tests")]

namespace Nayeon.ByokC1.Service
{
    internal enum SyntheticOperation { Add = 1, Replace = 2, Delete = 3 }
    internal enum TransactionOwnerState { ActiveDenied, Stopped, Shutdown, Faulted, Disposed, RecoveryHeld }
    internal enum TransactionDisposition
    { Denied, Cancelled, InvalidRequest, InvalidOperation, WrongOwner, StaleEpoch, Replay, OwnerTerminated, RecoveryRequired }

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
        internal readonly bool RecoveryRequired;
        internal readonly CoreOutcome OrderingOutcome;
        internal readonly DurableIntentAdmission RecoveryAdmission;
        internal bool Allowed { get { return false; } }
        internal bool MayHaveEffect { get { return false; } }
        internal bool DurableIntentQualified { get { return false; } }
        internal int Attempts { get { return 0; } }
        internal SyntheticTransactionResult(SyntheticTransactionRequest request, Guid owner, long epoch,
            TransactionOwnerState state, TransactionDisposition disposition, bool recoveryRequired = false,
            CoreOutcome orderingOutcome = CoreOutcome.None,
            DurableIntentAdmission recoveryAdmission = DurableIntentAdmission.Unqualified)
        { Request = request; Owner = owner; Epoch = epoch; State = state; Disposition = disposition;
            RecoveryRequired = recoveryRequired; OrderingOutcome = orderingOutcome; RecoveryAdmission = recoveryAdmission; }
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
        private readonly AtomicCustodyPublication admission = new AtomicCustodyPublication();
        private readonly DurableIntentAdmission recoveryAdmission;
        private AtomicCustodyPublication lastPublication;
        private SyntheticTransactionRequest lastRequest;

        // Pure standalone denial remains available to the historical callers/tests.
        // Neither constructor admits durable intent, recovery resume or effects.
        internal SyntheticTransactionOwner() { recoveryAdmission = DurableIntentAdmission.Unqualified; }
        internal SyntheticTransactionOwner(DenialOnlyRecoveryAdmission recovery)
        {
            recoveryAdmission = recovery == null ? DurableIntentAdmission.RecoveryHold : recovery.Claim();
            if (recoveryAdmission != DurableIntentAdmission.DenialOnlyMissingLeaf) admission.PublishUnknown();
        }

        private bool Enter()
        {
            if (Monitor.IsEntered(gate)) { admission.PublishUnknown(); return false; }
            if (Monitor.TryEnter(gate, 2000)) return true;
            admission.PublishUnknown(); return false;
        }

        private SyntheticTransactionResult Unknown(SyntheticTransactionRequest request)
        {
            return new SyntheticTransactionResult(request, owner, Interlocked.Read(ref epoch),
                TransactionOwnerState.RecoveryHeld, TransactionDisposition.RecoveryRequired, true,
                CoreOutcome.RecoveryRequired, recoveryAdmission);
        }

        internal SyntheticTransactionResult Observe()
        {
            if (!Enter()) return Unknown(null);
            try { return Result(null, TransactionDisposition.Denied); }
            finally { Monitor.Exit(gate); }
        }

        internal SyntheticTransactionResult Deny(SyntheticTransactionRequest request)
        { return EvaluateBounded(request, false); }

        internal SyntheticTransactionResult Cancel(SyntheticTransactionRequest request)
        { return EvaluateBounded(request, true); }

        private SyntheticTransactionResult EvaluateBounded(SyntheticTransactionRequest request, bool cancel)
        {
            if (!Enter()) return Unknown(request);
            try { return Evaluate(request, cancel); }
            finally { Monitor.Exit(gate); }
        }

        private SyntheticTransactionResult Evaluate(SyntheticTransactionRequest request, bool cancel)
        {
            // Retirement precedes request validation; sticky uncertainty dominates observations.
            if (state != TransactionOwnerState.ActiveDenied) return Result(request, TransactionDisposition.OwnerTerminated);
            if (AtomicCustodyPublication.IsUncertain(admission.Read())) return Unknown(request);
            if (request == null || request.RequestId == 0) return Result(request, TransactionDisposition.InvalidRequest);
            if (request.Owner != owner) return Result(request, TransactionDisposition.WrongOwner);
            if (request.Epoch != epoch) return Result(request, TransactionDisposition.StaleEpoch);
            if (request.Operation != SyntheticOperation.Add && request.Operation != SyntheticOperation.Replace &&
                request.Operation != SyntheticOperation.Delete) return Result(request, TransactionDisposition.InvalidOperation);
            if (request.RequestId <= highWater) return Result(request, TransactionDisposition.Replay);
            highWater = request.RequestId; // Reserve once for both cancellation and denial. Never evict or wrap.
            lastRequest = request; // Immutable identity, retained with its single terminal publication.
            lastPublication = new AtomicCustodyPublication();
            lastPublication.Finish(cancel ? CoreOutcome.Cancelled : CoreOutcome.Denied);
            return Result(request, cancel ? TransactionDisposition.Cancelled : TransactionDisposition.Denied);
        }

        private SyntheticTransactionResult Result(SyntheticTransactionRequest request, TransactionDisposition disposition)
        {
            int ownerPublication = admission.Read();
            bool uncertain = AtomicCustodyPublication.IsUncertain(ownerPublication);
            if (uncertain) return Unknown(request);
            CoreOutcome outcome = lastPublication != null && Object.ReferenceEquals(lastRequest, request) ?
                AtomicCustodyPublication.Outcome(lastPublication.Read()) : AtomicCustodyPublication.Outcome(ownerPublication);
            return new SyntheticTransactionResult(request, owner, epoch, state, disposition, false, outcome, recoveryAdmission);
        }

        private void Terminate(TransactionOwnerState reason)
        {
            // Sticky unknown closes admission. Propagate failed retirement so the
            // service cleanup path cannot report a successful stop/disposal.
            if (!Enter()) throw new InvalidOperationException("Transaction owner retirement uncertain; HOLD.");
            try
            {
                if (state == TransactionOwnerState.ActiveDenied) { Interlocked.Exchange(ref epoch, 2); state = reason; }
                // Disposal cannot revive or increment the epoch again.
                if (reason == TransactionOwnerState.Disposed) state = TransactionOwnerState.Disposed;
                admission.Finish(reason == TransactionOwnerState.Faulted ? CoreOutcome.Faulted : CoreOutcome.Stopped);
            }
            finally { Monitor.Exit(gate); }
        }

        internal void Stop() { Terminate(TransactionOwnerState.Stopped); }
        internal void Shutdown() { Terminate(TransactionOwnerState.Shutdown); }
        internal void Fault() { Terminate(TransactionOwnerState.Faulted); }
        public void Dispose() { Terminate(TransactionOwnerState.Disposed); }
    }
}
