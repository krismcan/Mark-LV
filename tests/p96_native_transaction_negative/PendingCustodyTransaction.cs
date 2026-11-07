// Nayeon BYOK C1 P50 — pending-only privileged transaction coordinator.
// Service-private, NOT exposed by an IPC route or Nayeon's normal UI.
// This is the actual write-ahead algorithm; production consent provenance,
// protected storage adapter and OS lock implementation remain independent gates.
// No native key API is composed in the disabled service at this checkpoint.
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal enum CustodyOutcome
    {
        Denied, RecoveryRequired, StoredUnverified, RemovedUnverified
    }

    internal interface IProtectedPendingState
    {
        bool TrustVerified { get; }
        string ReadJournal();
        string ReadAnchor();
        bool PendingPresent();
        void WriteJournal(string expected, string replacement);
        void WriteAnchor(string expected, string replacement);
        void SaveOrReplace(byte[] exactCandidate);
        void DeletePending();
    }

    internal interface ITrustedPendingApproval
    {
        bool Consume(LedgerOperation operation, byte[] exactCandidate,
            bool destructiveAcknowledgement);
        bool StillCurrent(LedgerOperation operation, byte[] exactCandidate);
    }

    internal interface IContinuousCustodyLease : IDisposable
    {
        bool IsOwned { get; }
        // May be called only after BOTH terminal writes and exact readback.
        // Dispose must atomically mark the manager faulted before allowing
        // another Acquire when this was not called, or release is uncertain.
        void MarkTerminalVerified();
    }

    internal interface IExclusiveCustodyLock
    {
        // Manager must preserve a fault barrier across the entire release,
        // never exposing a release-to-latch interleaving to a new contender.
        // Production restart MUST default to recovery until independently
        // protected service session admission has been verified.
        bool RecoveryFaulted { get; }
        IContinuousCustodyLease Acquire();
    }

    internal sealed class PendingCustodyTransaction
    {
        private readonly IProtectedPendingState state;
        private readonly ITrustedPendingApproval approval;
        private readonly IExclusiveCustodyLock guard;
        private int attempted;

        internal PendingCustodyTransaction(IProtectedPendingState state,
            ITrustedPendingApproval approval, IExclusiveCustodyLock guard)
        {
            if(state==null || approval==null || guard==null)
                throw new ArgumentNullException("Custody dependencies required");
            this.state=state; this.approval=approval; this.guard=guard;
            attempted=0;
        }

        private bool SamePair(string journal, string anchor)
        {
            return String.Equals(state.ReadJournal(),journal,StringComparison.Ordinal) &&
                String.Equals(state.ReadAnchor(),anchor,StringComparison.Ordinal);
        }

        private void Persist(string priorJournal,string priorAnchor,string nextJournal)
        {
            // Two physically separate stores: never claim atomicity. ANY
            // exception before both writes and exact readback = recovery.
            string nextAnchor=CustodyLedger.Anchor(nextJournal);
            state.WriteJournal(priorJournal,nextJournal);
            if (!String.Equals(state.ReadJournal(),nextJournal,StringComparison.Ordinal))
                throw new LedgerBlocked();
            state.WriteAnchor(priorAnchor,nextAnchor);
            if (!SamePair(nextJournal,nextAnchor))
                throw new LedgerBlocked();
        }

        private static bool Valid(LedgerOperation op,byte[] value,bool ack)
        {
            if (op==LedgerOperation.Delete)
                return value==null && ack;
            if (op==LedgerOperation.Save || op==LedgerOperation.Replace)
                return value!=null && value.Length>0 && value.Length<=2560 && !ack;
            return false;
        }

        private static bool EqualBytes(byte[] expected,byte[] candidate)
        {
            if (expected==null || candidate==null)
                return expected==null && candidate==null;
            if (expected.Length!=candidate.Length) return false;
            int difference=0;
            for(int i=0;i<expected.Length;i++)
                difference |= expected[i] ^ candidate[i];
            return difference==0;
        }

        private bool ConsumeApproval(LedgerOperation op,byte[] snapshot,bool ack)
        {
            byte[] proof=snapshot==null?null:(byte[])snapshot.Clone();
            try{return approval.Consume(op,proof,ack)==true;}
            finally{if(proof!=null)Array.Clear(proof,0,proof.Length);}
        }

        private bool ApprovalCurrent(LedgerOperation op,byte[] snapshot)
        {
            byte[] proof=snapshot==null?null:(byte[])snapshot.Clone();
            try{return approval.StillCurrent(op,proof)==true;}
            finally{if(proof!=null)Array.Clear(proof,0,proof.Length);}
        }

        internal CustodyOutcome Apply(LedgerOperation op, byte[] candidate,
            bool destructiveAcknowledgement=false)
        {
            // Atomic one-use claim, BEFORE validation, approval or lock calls.
            if (Interlocked.CompareExchange(ref attempted,1,0)!=0)
                return CustodyOutcome.Denied;
            byte[] owned=null;
            bool attemptedStateWrite=false;
            bool custodyReadStarted=false;
            try
            {
                if(!Valid(op,candidate,destructiveAcknowledgement))
                    return CustodyOutcome.Denied;
                // Snapshot privately; the elevated UI/input owner still owns
                // its original memory. Never give callbacks the effect buffer.
                owned=candidate==null?null:(byte[])candidate.Clone();
                if(!Valid(op,owned,destructiveAcknowledgement) ||
                    !EqualBytes(owned,candidate))
                    return CustodyOutcome.Denied;
                if(guard.RecoveryFaulted)
                    return CustodyOutcome.RecoveryRequired;
                // An actual trusted elevated UI must own this implementation.
                // No generic caller-supplied boolean is accepted here.
                if(ConsumeApproval(op,owned,destructiveAcknowledgement)!=true)
                    return CustodyOutcome.Denied;
                if(ApprovalCurrent(op,owned)!=true || !EqualBytes(owned,candidate))
                    return CustodyOutcome.Denied;

                using(IContinuousCustodyLease lease=guard.Acquire())
                {
                    if(lease==null || lease.IsOwned!=true || state.TrustVerified!=true)
                        return CustodyOutcome.Denied;
                    // Once a trusted lease begins custody reads, corrupt or
                    // unreadable history is recovery-required, not a denial.
                    custodyReadStarted=true;
                    string beforeJournal=state.ReadJournal();
                    string beforeAnchor=state.ReadAnchor();
                    if(!SamePair(beforeJournal,beforeAnchor) ||
                       lease.IsOwned!=true)
                        return CustodyOutcome.RecoveryRequired;
                    bool present=state.PendingPresent();
                    // A normal Save must NEVER bootstrap or reenrol the
                    // service. Both records missing can mean lost history;
                    // it is indistinguishable from first installation here.
                    // The reviewed installer/recovery authority alone must
                    // provision and persist the initial journal + anchor +
                    // independent historical enrollment witness. Ordinary
                    // credential operations cannot repair that witness.
                    if(beforeJournal==null || beforeAnchor==null)
                        return CustodyOutcome.RecoveryRequired;

                    LedgerPhase phase=CustodyLedger.Verify(beforeJournal,beforeAnchor);
                    LedgerOperation prior=CustodyLedger.LastOperation(beforeJournal);
                    if (phase==LedgerPhase.InFlight ||
                        (phase==LedgerPhase.CommittedUnverified && !present) ||
                        (phase==LedgerPhase.CommittedAbsent && present) ||
                        (phase==LedgerPhase.Initial && present))
                        return CustodyOutcome.RecoveryRequired;
                    bool expectStored=phase==LedgerPhase.CommittedUnverified;
                    if (expectStored!=(op!=LedgerOperation.Save) ||
                        (expectStored && op==LedgerOperation.Save) ||
                        (!expectStored && op!=LedgerOperation.Save))
                        return CustodyOutcome.Denied;
                    if(phase==LedgerPhase.Initial && prior!=LedgerOperation.Initial)
                        return CustodyOutcome.RecoveryRequired;

                    if (!SamePair(beforeJournal,beforeAnchor) ||
                        state.PendingPresent()!=present ||
                        (ApprovalCurrent(op,owned)!=true || !EqualBytes(owned,candidate)) ||
                        lease.IsOwned!=true)
                        return CustodyOutcome.RecoveryRequired;

                    string inFlight=CustodyLedger.AppendIntent(beforeJournal,op,
                        CustodyLedger.NewNonce());
                    attemptedStateWrite=true;
                    Persist(beforeJournal,beforeAnchor,inFlight);
                    string inFlightAnchor=CustodyLedger.Anchor(inFlight);
                    if (CustodyLedger.Verify(inFlight,inFlightAnchor)!=
                        LedgerPhase.InFlight || !SamePair(inFlight,inFlightAnchor) ||
                        state.PendingPresent()!=present ||
                        (ApprovalCurrent(op,owned)!=true || !EqualBytes(owned,candidate)) ||
                        lease.IsOwned!=true)
                        return CustodyOutcome.RecoveryRequired;

                    // Only possible key effect: exactly once, fixed pending
                    // interface. No provider, active key, readback or retry.
                    if(op==LedgerOperation.Delete)
                        state.DeletePending();
                    else
                        state.SaveOrReplace(owned);

                    if(lease.IsOwned!=true)
                        return CustodyOutcome.RecoveryRequired;
                    string done=CustodyLedger.AppendTerminal(inFlight);
                    Persist(inFlight,inFlightAnchor,done);
                    lease.MarkTerminalVerified();
                    // Final metadata is NOT key validation or physical
                    // durability proof; even success is UNVERIFIED.
                    return op==LedgerOperation.Delete?
                        CustodyOutcome.RemovedUnverified :
                        CustodyOutcome.StoredUnverified;
                }
            }
            catch(Exception)
            {
                // Disposal after a terminal write can also fail: mark the
                // shared service manager faulted, never silently rearm.
                return attemptedStateWrite || custodyReadStarted?
                    CustodyOutcome.RecoveryRequired:CustodyOutcome.Denied;
            }
            finally
            {
                // If a lease was acquired, its Dispose handles fault
                // publication and release atomically inside the manager.
                // No post-release fallback LatchFault callback is permitted.
                if(owned!=null)Array.Clear(owned,0,owned.Length);
            }
        }
    }
}
