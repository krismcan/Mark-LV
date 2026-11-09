// P126 — REAL Windows named Mutex custody lease, SYNTHETIC INTEGER ONLY.
// Separate from the frozen P49 credential coordinator and P110 in-process
// fake-effect actor. Does NOT bind trusted consent or invoke WinCred.
// C1 native effects and real privileged service remain permanently held.
// This source must be compiled only for unprivileged hosted Windows review.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P126 real Windows named mutex review requires BOTH isolated+synthetic flags
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class WindowsG2SyntheticMutexCustody : IDisposable
    {
        private enum Phase { Empty, Prepared, Committed, Recovery, Revoked }
        private const string TestPrefix="Local\\Nayeon-C1-P126-";
        private readonly object gate=new object();
        private readonly Mutex osMutex;
        private Phase phase=Phase.Empty;
        private LedgerOperation boundOperation;
        private bool revoked,stopped,faulted,disposed,everCommitted;
        private int fakeEffectMarkers,unknownResults;
        private int abandonedAcquisitions,tooLateRevocations;
        private bool reviewOwnerAcquired;

        internal WindowsG2SyntheticMutexCustody(string testOnlyName)
        {
            if(testOnlyName==null ||
                !testOnlyName.StartsWith(TestPrefix,StringComparison.Ordinal) ||
                testOnlyName.Length!=TestPrefix.Length+32)
                throw new ArgumentException("Invalid isolated Windows test mutex name");
            for(int i=TestPrefix.Length;i<testOnlyName.Length;i++)
            {
                char c=testOnlyName[i];
                if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))
                    throw new ArgumentException("Noncanonical test mutex name");
            }
            // No protected DACL or real production name; this is ONLY
            // a runner-owned synthetic OS mutex, not custody authority.
            osMutex=new Mutex(false,testOnlyName);
        }

        internal bool PrepareSyntheticOnly(
            LedgerOperation operation,bool destructiveAcknowledgement)
        {
            lock(gate)
            {
                if(disposed||revoked||stopped||faulted||
                    phase!=Phase.Empty)return false;
                bool valid=operation==LedgerOperation.Delete?
                    destructiveAcknowledgement:
                    (operation==LedgerOperation.Save||
                     operation==LedgerOperation.Replace)&&
                    !destructiveAcknowledgement;
                if(!valid)return false;
                boundOperation=operation;
                phase=Phase.Prepared;
                return true;
            }
        }

        // The private OS mutex is acquired and released on the SAME
        // real Windows thread. No callback, credential, protected state,
        // native effect API or injected effect interface is reachable.
        // Fake effect is one INTEGER increment under the service-shaped
        // monitor AND a real OS named mutex; never a successful outcome.
        internal CustodyOutcome AttemptFakeOnly(
            LedgerOperation operation,ManualResetEvent entered,
            ManualResetEvent release,bool simulatedUnknown=false)
        {
            lock(gate)
            {
                if(disposed||faulted)return CustodyOutcome.RecoveryRequired;
                if(revoked||stopped||phase==Phase.Revoked)
                    return CustodyOutcome.Denied;
                if(phase!=Phase.Prepared||operation!=boundOperation)
                {
                    // Any erroneous attempted dispatch burns admission.
                    faulted=true;phase=Phase.Recovery;
                    return CustodyOutcome.Denied;
                }

                bool owned=false;
                try
                {
                    try
                    {
                        if(!osMutex.WaitOne(0))
                        {
                            faulted=true;phase=Phase.Recovery;
                            return CustodyOutcome.RecoveryRequired;
                        }
                        owned=true;
                    }
                    catch(AbandonedMutexException)
                    {
                        // .NET grants ownership on abandonment, but
                        // protected state could be inconsistent. RELEASE
                        // the acquired mutex on this thread, never proceed.
                        owned=true;
                        ++abandonedAcquisitions;
                        faulted=true;phase=Phase.Recovery;
                        return CustodyOutcome.RecoveryRequired;
                    }

                    reviewOwnerAcquired=true;
                    phase=Phase.Committed;
                    everCommitted=true;
                    ++fakeEffectMarkers;
                    if(entered!=null)entered.Set();
                    if(release!=null&&!release.WaitOne(2500))
                        ++unknownResults;
                    if(simulatedUnknown)
                        ++unknownResults;
                    // No protected durable witness exists. Recovery is
                    // mandatory even when fake integer work 'succeeded'.
                    faulted=true;phase=Phase.Recovery;
                    return CustodyOutcome.RecoveryRequired;
                }
                catch(Exception)
                {
                    ++unknownResults;
                    faulted=true;phase=Phase.Recovery;
                    return CustodyOutcome.RecoveryRequired;
                }
                finally
                {
                    if(owned)
                    {
                        try{osMutex.ReleaseMutex();}
                        catch(Exception)
                        {
                            ++unknownResults;
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
                if(!revoked&&everCommitted)++tooLateRevocations;
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
                if(everCommitted)
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
        internal int FakeEffectMarkers
        {get{lock(gate){return fakeEffectMarkers;}}}
        internal int AbandonedAcquisitions
        {get{lock(gate){return abandonedAcquisitions;}}}
        internal int UnknownResults
        {get{lock(gate){return unknownResults;}}}
        internal int TooLateRevocations
        {get{lock(gate){return tooLateRevocations;}}}
        internal bool ReviewOsMutexAcquired
        {get{lock(gate){return reviewOwnerAcquired;}}}
        internal bool RecoveryRequired
        {get{lock(gate){return faulted;}}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}
        internal bool ActualHumanConsentVerified {get{return false;}}
        internal bool ProtectedDurableGrantIssued {get{return false;}}
        internal bool ReleaseEligible {get{return false;}}

        public override string ToString()
        {return "<P126 named Windows mutex review; fake integer only; G2 HOLD>";}

        public void Dispose()
        {
            lock(gate)
            {
                if(disposed)return;
                disposed=true;faulted=true;phase=Phase.Recovery;
                osMutex.Dispose();
            }
        }
    }
}
