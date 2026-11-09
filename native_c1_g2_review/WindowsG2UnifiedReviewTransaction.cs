// P127: one review-only actor integrates SAME local consent/revoke monitor,
// genuine Windows process-shared Mutex tenure, and three SYNTHETIC INTEGER
// transaction stages: intent, fixed fake attempt, terminal witness.
// ABSOLUTELY NO persistent journal, protected anchor, WinCred, key, UI, IPC,
// service install, arbitrary effect callback or successful custody result.
// Old P49/P96 legacy effect coordinator remains frozen and disabled.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P127 unified native actor is for isolated synthetic Windows tests only
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class WindowsG2UnifiedReviewTransaction : IDisposable
    {
        private enum Phase { Empty, Prepared, SyntheticInFlight, Recovery, Revoked }
        private const string Prefix="Local\\Nayeon-C1-P127-";
        private readonly object gate=new object();
        private readonly Mutex custodyMutex;
        private Phase phase=Phase.Empty;
        private LedgerOperation operation;
        private bool revoked,stopped,faulted,disposed,effectPossiblyAttempted;
        private int fakeIntentMarkers,fakeEffects,fakeTerminals,unknownCount;
        private int abandonedCount,lateRevocations;

        internal WindowsG2UnifiedReviewTransaction(string name)
        {
            if(name==null||!name.StartsWith(Prefix,StringComparison.Ordinal)||
                name.Length!=Prefix.Length+32)
                throw new ArgumentException("Invalid isolated test mutex name");
            for(int i=Prefix.Length;i<name.Length;i++)
            {
                char c=name[i];
                if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))
                    throw new ArgumentException("Only a canonical test UUID is allowed");
            }
            custodyMutex=new Mutex(false,name);
        }

        internal bool PrepareSyntheticOnly(
            LedgerOperation candidate,bool destructiveAcknowledgement)
        {
            lock(gate)
            {
                if(disposed||faulted||stopped||revoked||phase!=Phase.Empty)
                    return false;
                bool allowed=(candidate==LedgerOperation.Delete&&
                    destructiveAcknowledgement)||
                    ((candidate==LedgerOperation.Save||
                      candidate==LedgerOperation.Replace)&&
                      !destructiveAcknowledgement);
                if(!allowed)return false;
                operation=candidate;
                phase=Phase.Prepared;
                return true;
            }
        }

        // This is NOT a protected transactional journal. All 'writes' below
        // increment local integers under one lock. They are not persisted
        // or authenticated. Every path terminates DENIED or RECOVERY.
        // The kernel Mutex acquisition AND final fake effect decision are
        // within the SAME gate as Revoke/Stop/MarkFault, unlike P96.
        internal CustodyOutcome AttemptSyntheticOnly(
            LedgerOperation candidate,
            ManualResetEvent entered=null,ManualResetEvent release=null,
            bool failBeforeIntent=false,bool uncertainEffect=false,
            bool failTerminal=false)
        {
            lock(gate)
            {
                if(disposed||faulted)return CustodyOutcome.RecoveryRequired;
                if(revoked||stopped||phase==Phase.Revoked)
                    return CustodyOutcome.Denied;
                if(phase!=Phase.Prepared||candidate!=operation)
                {
                    faulted=true;phase=Phase.Recovery;
                    return CustodyOutcome.Denied;
                }
                bool owned=false;
                try
                {
                    try
                    {
                        if(!custodyMutex.WaitOne(0))
                        {
                            faulted=true;phase=Phase.Recovery;
                            return CustodyOutcome.RecoveryRequired;
                        }
                        owned=true;
                    }
                    catch(AbandonedMutexException)
                    {
                        // .NET already transferred mutex ownership to
                        // this SAME thread on abandonment. Never treat it
                        // as safe state. Release in finally, zero effect.
                        owned=true;
                        ++abandonedCount;
                        faulted=true;phase=Phase.Recovery;
                        return CustodyOutcome.RecoveryRequired;
                    }

                    if(failBeforeIntent)
                    {
                        faulted=true;phase=Phase.Recovery;
                        return CustodyOutcome.RecoveryRequired;
                    }

                    phase=Phase.SyntheticInFlight;
                    ++fakeIntentMarkers; // purely in-memory, never G3

                    // Fixed operation-bound fake dispatch, no callback and
                    // no credential bytes. The only effect is an integer.
                    ++fakeEffects;
                    effectPossiblyAttempted=true;
                    if(entered!=null)entered.Set();
                    if(release!=null&&!release.WaitOne(2500))
                    {
                        ++unknownCount;
                        faulted=true;phase=Phase.Recovery;
                        return CustodyOutcome.RecoveryRequired;
                    }
                    if(uncertainEffect)
                    {
                        ++unknownCount;
                        faulted=true;phase=Phase.Recovery;
                        return CustodyOutcome.RecoveryRequired;
                    }
                    if(failTerminal)
                    {
                        ++unknownCount;
                        faulted=true;phase=Phase.Recovery;
                        return CustodyOutcome.RecoveryRequired;
                    }

                    ++fakeTerminals; // NOT durable/protected evidence
                    faulted=true;phase=Phase.Recovery;
                    return CustodyOutcome.RecoveryRequired;
                }
                catch(Exception)
                {
                    ++unknownCount;
                    faulted=true;phase=Phase.Recovery;
                    return CustodyOutcome.RecoveryRequired;
                }
                finally
                {
                    if(owned)
                    {
                        try{custodyMutex.ReleaseMutex();}
                        catch(Exception)
                        {
                            ++unknownCount;
                            faulted=true;phase=Phase.Recovery;
                        }
                    }
                }
            }
        }

        internal void Revoke()
        {
            lock(gate)
            {
                if(disposed)return;
                if(!revoked&&effectPossiblyAttempted)++lateRevocations;
                revoked=true;
                if(phase==Phase.Prepared)phase=Phase.Revoked;
            }
        }
        internal void Stop()
        {
            lock(gate)
            {
                if(disposed)return;
                stopped=true;revoked=true;
                if(effectPossiblyAttempted)
                {
                    faulted=true;phase=Phase.Recovery;
                }
                else phase=Phase.Revoked;
            }
        }
        internal void MarkFault()
        {
            lock(gate)
            {
                if(disposed)return;
                faulted=true;phase=Phase.Recovery;
            }
        }
        internal int SyntheticIntents
        {get{lock(gate){return fakeIntentMarkers;}}}
        internal int SyntheticEffects
        {get{lock(gate){return fakeEffects;}}}
        internal int SyntheticTerminals
        {get{lock(gate){return fakeTerminals;}}}
        internal int UnknownOutcomes
        {get{lock(gate){return unknownCount;}}}
        internal int AbandonedAcquisitions
        {get{lock(gate){return abandonedCount;}}}
        internal int TooLateRevocations
        {get{lock(gate){return lateRevocations;}}}
        internal bool RecoveryRequired
        {get{lock(gate){return faulted;}}}
        internal bool TrustVerified {get{return false;}}
        internal bool DurableJournalVerified {get{return false;}}
        internal bool ProtectedAnchorVerified {get{return false;}}
        internal bool HumanConsentVerified {get{return false;}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}
        internal bool ProductionReleaseEligible {get{return false;}}
        public override string ToString()
        {return "<P127 synthetic journal/OS mutex review; NO G1/G2/G3 authority>";}

        public void Dispose()
        {
            lock(gate)
            {
                if(disposed)return;
                disposed=true;faulted=true;phase=Phase.Recovery;
                custodyMutex.Dispose();
            }
        }
    }
}
