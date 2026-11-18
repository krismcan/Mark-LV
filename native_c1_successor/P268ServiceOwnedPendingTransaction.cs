#if !DEBUG
#error P268_NO_RELEASE_BUILD
#endif
#if !C1_P268_DEVELOPMENT_ONLY
#error P268_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1.P268Development
{
    // No production factory, IPC route, service installation or native adapter.
    // Only the exact sealed P96 in-memory fixture can back this development host.
    internal sealed class DevelopmentPendingState : IProtectedPendingState
    {
        private readonly P96StateFixture fixture;
        private int claimed;
        internal bool Enrolled = true;
        internal Action<string> Inject;
        internal int JournalWrites, AnchorWrites, SaveCalls, DeleteCalls;
        internal DevelopmentPendingState(P96StateFixture value)
        { if (value == null) throw new ArgumentNullException("value"); fixture = value; }
        internal void Claim()
        { if (Interlocked.CompareExchange(ref claimed, 1, 0) != 0) throw new LedgerBlocked(); }
        private void Probe(string point) { if (Inject != null) Inject(point); }
        public bool TrustVerified { get { Probe("trust"); return fixture.TrustVerified; } }
        public string ReadJournal() { Probe("read-journal"); return fixture.ReadJournal(); }
        public string ReadAnchor() { Probe("read-anchor"); return fixture.ReadAnchor(); }
        public bool PendingPresent() { Probe("present"); return fixture.PendingPresent(); }
        public void WriteJournal(string expected, string replacement)
        { JournalWrites++; Probe("write-journal"); fixture.WriteJournal(expected, replacement); Probe("after-journal"); }
        public void WriteAnchor(string expected, string replacement)
        { AnchorWrites++; Probe("write-anchor"); fixture.WriteAnchor(expected, replacement); Probe("after-anchor"); }
        public void SaveOrReplace(byte[] value)
        {
            if (!Synthetic(value)) throw new LedgerBlocked();
            SaveCalls++; Probe("effect-enter"); fixture.SaveOrReplace(value); Probe("effect-return");
        }
        public void DeletePending()
        { DeleteCalls++; Probe("effect-enter"); fixture.DeletePending(); Probe("effect-return"); }
        internal static bool Synthetic(byte[] value)
        { return value != null && value.Length == 4 && value[0] == 0x31 &&
            value[1] == 0x32 && value[2] == 0x33 && value[3] == 0x34; }
    }

    internal enum ControlResult { Revoked, Stopped, Faulted, TooLate, RecoveryRequired }
    internal sealed class ServiceOwnedPendingTransaction
    {
        private readonly object gate = new object();
        private readonly DevelopmentPendingState development;
        private readonly IProtectedPendingState state;
        private readonly IExclusiveCustodyLock custody;
        private bool closed, faulted, used, mayHaveEffect, recoveryRequired;
        // Atomic request only, never a successful revocation outside the gate.
        // A callback waiting on another thread cannot deadlock gate ownership.
        private int admissionFailure;
        private Approval prepared;
        internal sealed class Approval
        {
            internal readonly LedgerOperation Operation;
            internal Approval(LedgerOperation operation) { Operation = operation; }
        }
        private ServiceOwnedPendingTransaction(DevelopmentPendingState value,
            IExclusiveCustodyLock lease, bool freshSyntheticSession)
        {
            if (value == null || lease == null) throw new ArgumentNullException("dependencies");
            value.Claim(); development = value; state = value; custody = lease;
            recoveryRequired = !freshSyntheticSession;
        }
        internal static ServiceOwnedPendingTransaction DevelopmentOnlyHost(
            DevelopmentPendingState value, IExclusiveCustodyLock lease, bool freshSyntheticSession)
        { return new ServiceOwnedPendingTransaction(value, lease, freshSyntheticSession); }
        internal static bool ProductionEligible { get { return false; } }
        internal static bool TrustedIssuerConnected { get { return false; } }
        // Production requires independently reviewed service principal, authenticated
        // IPC consent provenance, durable enrollment/journal/anchor and recovery.
        // No such adapter or admission factory is present in this assembly.
        private void Enter()
        {
            if (Monitor.IsEntered(gate))
            {
                faulted = true; recoveryRequired = true; closed = true;
                throw new InvalidOperationException("P268_NONREENTRANT");
            }
            if (!Monitor.TryEnter(gate, 500))
            {
                Interlocked.Exchange(ref admissionFailure, 1);
                throw new InvalidOperationException("P268_GATE_UNCERTAIN");
            }
        }
        private void Barrier()
        {
            if (Volatile.Read(ref admissionFailure) != 0) faulted = true;
            if (faulted) { closed = true; recoveryRequired = true; throw new LedgerBlocked(); }
        }
        private void Exit() { try { if (Volatile.Read(ref admissionFailure) != 0)
            { faulted = true; closed = true; recoveryRequired = true; } }
            finally { Monitor.Exit(gate); } }
        internal Approval IssueDevelopmentApproval(LedgerOperation op)
        {
            Enter();
            try
            {
                Barrier();
                if (closed || recoveryRequired || used || prepared != null ||
                    (op != LedgerOperation.Save && op != LedgerOperation.Replace && op != LedgerOperation.Delete))
                    return null;
                // This service-owned one-use identity binds operation and the ONLY
                // permitted candidate, literal 31 32 33 34 (or null for Delete).
                prepared = new Approval(op); return prepared;
            }
            catch (LedgerBlocked) { return null; }
            finally { Exit(); }
        }
        private ControlResult Close(int reason)
        {
            Enter();
            try
            {
                closed = true; prepared = null;
                if (reason == 2) { faulted = true; recoveryRequired = true; }
                if (Volatile.Read(ref admissionFailure) != 0)
                { faulted = true; recoveryRequired = true; }
                if (mayHaveEffect) return ControlResult.TooLate;
                if (recoveryRequired) return ControlResult.RecoveryRequired;
                return reason == 0 ? ControlResult.Revoked : ControlResult.Stopped;
            }
            finally { Exit(); }
        }
        internal ControlResult Revoke() { return Close(0); }
        internal ControlResult Stop() { return Close(1); }
        internal ControlResult Fault() { return Close(2); }
        internal bool MayHaveEffect { get { Enter(); try { return mayHaveEffect; } finally { Exit(); } } }
        internal bool RecoveryRequired { get { Enter(); try { return recoveryRequired; } finally { Exit(); } } }
        private bool Owned(IContinuousCustodyLease lease)
        { bool result = lease.IsOwned; Barrier(); return result; }
        private string Journal() { string result = state.ReadJournal(); Barrier(); return result; }
        private string Anchor() { string result = state.ReadAnchor(); Barrier(); return result; }
        private bool Present() { bool result = state.PendingPresent(); Barrier(); return result; }
        private bool SamePair(string journal, string anchor)
        { return String.Equals(Journal(), journal, StringComparison.Ordinal) &&
            String.Equals(Anchor(), anchor, StringComparison.Ordinal); }
        private void Persist(string before, string anchor, string next)
        {
            string nextAnchor = CustodyLedger.Anchor(next);
            state.WriteJournal(before, next); Barrier();
            if (!String.Equals(Journal(), next, StringComparison.Ordinal)) throw new LedgerBlocked();
            state.WriteAnchor(anchor, nextAnchor); Barrier();
            if (!SamePair(next, nextAnchor)) throw new LedgerBlocked();
        }
        internal CustodyOutcome Apply(Approval approval, LedgerOperation op, byte[] candidate,
            bool destructiveAcknowledgement)
        {
            Enter();
            byte[] owned = null;
            IContinuousCustodyLease lease = null;
            bool reading = false, writing = false;
            CustodyOutcome result = CustodyOutcome.Denied;
            try
            {
                Barrier();
                if (closed || recoveryRequired || used || approval == null ||
                    !Object.ReferenceEquals(approval, prepared) || approval.Operation != op)
                    return recoveryRequired ? CustodyOutcome.RecoveryRequired : CustodyOutcome.Denied;
                used = true; prepared = null; // consume even malformed attempts
                if (op == LedgerOperation.Delete ? candidate != null || !destructiveAcknowledgement :
                    !DevelopmentPendingState.Synthetic(candidate) || destructiveAcknowledgement)
                    return CustodyOutcome.Denied;
                owned = candidate == null ? null : (byte[])candidate.Clone();
                if (custody.RecoveryFaulted) { recoveryRequired = true; return CustodyOutcome.RecoveryRequired; }
                Barrier();
                lease = custody.Acquire(); Barrier();
                if (lease == null || !Owned(lease)) throw new LedgerBlocked();
                bool trusted = state.TrustVerified; Barrier();
                if (!trusted) throw new LedgerBlocked();
                reading = true;
                if (!development.Enrolled) throw new LedgerBlocked();
                string before = Journal(), anchor = Anchor();
                if (before == null || anchor == null || !SamePair(before, anchor) || !Owned(lease))
                    throw new LedgerBlocked();
                bool present = Present();
                LedgerPhase phase = CustodyLedger.Verify(before, anchor);
                if (phase == LedgerPhase.InFlight ||
                    (phase == LedgerPhase.CommittedUnverified) != present) throw new LedgerBlocked();
                if (present != (op != LedgerOperation.Save)) throw new LedgerBlocked();
                if (!SamePair(before, anchor) || Present() != present || !Owned(lease)) throw new LedgerBlocked();
                string intent = CustodyLedger.AppendIntent(before, op, CustodyLedger.NewNonce());
                writing = true; recoveryRequired = true; // uncertainty BEFORE first write
                Persist(before, anchor, intent);
                string intentAnchor = CustodyLedger.Anchor(intent);
                if (CustodyLedger.Verify(intent, intentAnchor) != LedgerPhase.InFlight ||
                    !SamePair(intent, intentAnchor) || Present() != present || !Owned(lease))
                    throw new LedgerBlocked();
                Barrier();
                // Linearization point: service consent and the identical P96 effect
                // invocation share THIS gate, including all real managed fixture calls.
                // Verified InFlight pair is the durable-adapter contract's pending marker.
                // The fake stores model it only; no production durability is claimed.
                mayHaveEffect = true;
                if (op == LedgerOperation.Delete) state.DeletePending();
                else state.SaveOrReplace(owned);
                Barrier();
                if (!Owned(lease)) throw new LedgerBlocked();
                string terminal = CustodyLedger.AppendTerminal(intent);
                Persist(intent, intentAnchor, terminal);
                lease.MarkTerminalVerified(); Barrier();
                result = op == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified;
            }
            catch (Exception)
            {
                faulted = true; closed = true; recoveryRequired = true;
                result = CustodyOutcome.RecoveryRequired;
            }
            finally
            {
                // Dispose BEFORE releasing the admission gate, including failures.
                try { if (lease != null) { lease.Dispose(); Barrier(); } }
                catch (Exception) { faulted = true; closed = true; recoveryRequired = true;
                    result = CustodyOutcome.RecoveryRequired; }
                if (reading || writing) recoveryRequired = true;
                if (owned != null) Array.Clear(owned, 0, owned.Length);
                Exit();
            }
            return result;
        }
    }
}
