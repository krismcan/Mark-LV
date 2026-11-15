// P230 isolated C# service-actor *shape* under independent security review.
// Critically this is NOT a Windows service, credential store, or production fix.
// The original P96 review wrapper calls the vulnerable coordinator; this actor
// instead owns its own single terminal critical section and NO effect adapter.
// Its only "effect" is an internal integer test marker. No key byte, principal,
// caller callback, WinCred, IPC, provider, signer, filesystem or registry access.
// DO NOT include this test-only file in any signed install/build. SEC-03/04 HOLD.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P230 native single-owner effect actor NONDEPLOYABLE TEST-ONLY
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class P230SingleOwnerSyntheticActor
    {
        private readonly object gate = new object();
        private readonly string initialNonce = new string('a',32);
        private string journal;
        private string anchor;
        private bool syntheticPresent;
        private bool armed;
        private bool attempted;
        private bool revoked;
        private bool stopped;
        private bool faulted;
        private bool recoveryRequired;
        private LedgerOperation operation;
        private int fakeEffectCount;
        private int fakeEffectAfterCommittedRevoke;
        private int tooLateTransitions;
        private int unknownFakeEffectCount;

        internal P230SingleOwnerSyntheticActor(bool seededSyntheticPending = false)
        {
            journal = CustodyLedger.CreateInitial(initialNonce);
            if (seededSyntheticPending)
            {
                // Historical P95 in-memory ledger format. No disk durability.
                string intent = CustodyLedger.AppendIntent(
                    journal,LedgerOperation.Save,new string('b',32));
                journal = CustodyLedger.AppendTerminal(intent);
                syntheticPresent = true;
            }
            anchor = CustodyLedger.Anchor(journal);
        }

        internal bool ArmFakeOnly(LedgerOperation op,bool deleteAcknowledged)
        {
            lock(gate)
            {
                if(armed || attempted || revoked || stopped || faulted
                   || recoveryRequired)
                    return false;
                bool shape=(op==LedgerOperation.Delete && deleteAcknowledged)
                    || ((op==LedgerOperation.Save
                    || op==LedgerOperation.Replace) && !deleteAcknowledged);
                if(!shape) return false;
                armed=true;
                operation=op;
                return true;
            }
        }

        internal CustodyOutcome AttemptFakeOnly(
            ManualResetEvent testEntered=null,
            ManualResetEvent testRelease=null,
            bool syntheticEffectResultUnknown=false,
            bool syntheticJournalFaultBeforeEffect=false)
        {
            // This monitor is the actor's OWN final effect lock; not an outer
            // wrapper around old P96 or a caller-injected effect implementation.
            // Every actor-owned revoke, stop and fault transition also owns it.
            lock(gate)
            {
                if(attempted) return CustodyOutcome.Denied;
                if(faulted || recoveryRequired) return CustodyOutcome.RecoveryRequired;
                if(revoked || stopped || !armed) return CustodyOutcome.Denied;
                attempted=true; // one use BEFORE ledger or fake effect attempt
                armed=false;
                try
                {
                    LedgerPhase before=CustodyLedger.Verify(journal,anchor);
                    if((operation==LedgerOperation.Save && syntheticPresent)
                       || (operation!=LedgerOperation.Save && !syntheticPresent))
                        return CustodyOutcome.Denied;
                    if((before!=LedgerPhase.Initial && !syntheticPresent)
                       || (before!=LedgerPhase.CommittedUnverified && syntheticPresent))
                        return CustodyOutcome.RecoveryRequired;
                    string intent=CustodyLedger.AppendIntent(
                        journal,operation,CustodyLedger.NewNonce());
                    // In MEMORY, not durable! True native service must replace
                    // with independent verified durable journal/anchor design.
                    journal=intent;
                    anchor=CustodyLedger.Anchor(journal);
                    if(CustodyLedger.Verify(journal,anchor)!=LedgerPhase.InFlight)
                        return CustodyOutcome.RecoveryRequired;
                    if(syntheticJournalFaultBeforeEffect)
                        throw new LedgerBlocked();
                    if(testEntered!=null) testEntered.Set();
                    if(testRelease!=null && !testRelease.WaitOne(1200))
                        return CustodyOutcome.RecoveryRequired;
                    // The ONLY terminal marker is internal, fixed and typed.
                    // Absolutely no callback, interface or native effect port.
                    ++fakeEffectCount;
                    if(revoked) ++fakeEffectAfterCommittedRevoke;
                    syntheticPresent=operation!=LedgerOperation.Delete;
                    if(syntheticEffectResultUnknown)
                    {
                        ++unknownFakeEffectCount;
                        throw new LedgerBlocked();
                    }
                    journal=CustodyLedger.AppendTerminal(intent);
                    anchor=CustodyLedger.Anchor(journal);
                    LedgerPhase done=CustodyLedger.Verify(journal,anchor);
                    if((operation==LedgerOperation.Delete &&
                        done!=LedgerPhase.CommittedAbsent)
                       || (operation!=LedgerOperation.Delete &&
                        done!=LedgerPhase.CommittedUnverified))
                        return CustodyOutcome.RecoveryRequired;
                    // Even the in-memory "success" is RECOVERY, never a
                    // credential success, durable state or trusted GO.
                    return CustodyOutcome.RecoveryRequired;
                }
                catch(Exception)
                {
                    return CustodyOutcome.RecoveryRequired;
                }
                finally
                {
                    recoveryRequired=true; // no retry, incl. fake success
                }
            }
        }

        internal void Revoke()
        {
            lock(gate)
            {
                if(fakeEffectCount>0) ++tooLateTransitions;
                revoked=true;
            }
        }
        internal void Stop()
        {
            lock(gate)
            {
                if(fakeEffectCount>0) ++tooLateTransitions;
                revoked=true;
                stopped=true;
            }
        }
        internal void Fault()
        {
            lock(gate)
            {
                if(fakeEffectCount>0) ++tooLateTransitions;
                faulted=true;
                recoveryRequired=true;
            }
        }

        internal int FakeEffects {get {lock(gate){return fakeEffectCount;}}}
        internal int FakeEffectsAfterCommittedRevoke
        {get {lock(gate){return fakeEffectAfterCommittedRevoke;}}}
        internal int TooLateTransitions {get {lock(gate){return tooLateTransitions;}}}
        internal int UnknownFakeEffects {get {lock(gate){return unknownFakeEffectCount;}}}
        internal bool RecoveryRequired {get {lock(gate){return recoveryRequired;}}}
        internal bool IsRevoked {get {lock(gate){return revoked;}}}
        internal bool IsStopped {get {lock(gate){return stopped;}}}
        internal bool IsFaulted {get {lock(gate){return faulted;}}}
        internal bool NativeWindowsCredentialEffectEnabled {get {return false;}}
        internal bool ActualServicePrincipalStoreVerified {get {return false;}}
        internal bool AuthenticatedHumanConsentIssuerAvailable {get {return false;}}
        internal bool DurableJournalAnchorVerified {get {return false;}}
        internal bool SignedInstalledRuntimeApproved {get {return false;}}
        internal bool ProductionReleaseEligible {get {return false;}}
        internal bool OriginalP96ProductionSourceFixed {get {return false;}}
    }
}
