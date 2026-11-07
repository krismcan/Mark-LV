// Nayeon BYOK C1: fixed service-owned protected state composition.
// Wires native pending-only vault to the EXISTING transaction interface,
// but no service entrypoint, IPC or UI can instantiate it while the
// service's independently reviewed LiveEligible checks remain FALSE.
// It does NOT provision first-run state or attempt automatic recovery.
using System;

namespace Nayeon.ByokC1
{
    internal sealed class PendingServiceState : IProtectedPendingState
    {
        private readonly CustodyJournalFile journal;
        private readonly CustodyRegistryAnchor registry;
        private readonly PendingWinCredStore pending;

        private PendingServiceState(CustodyJournalFile journal,
            CustodyRegistryAnchor registry, PendingWinCredStore pending)
        {
            if(journal==null || registry==null || pending==null)
                throw new LedgerBlocked();
            this.journal=journal;
            this.registry=registry;
            this.pending=pending;
        }

        internal static PendingServiceState ForInstalledService()
        {
            // No caller-supplied root, provider, credential target, account,
            // approval callback, storage key, or synthetic bypass.
            // The actual product service and manifest proofs are PENDING,
            // so ServiceGate.LiveEligible() remains false on Kristian.
            try
            {
                if(!ServiceGate.LiveEligible() ||
                    !ProtectedAcl.VerifyInstalledCustodyDirectory())
                    throw new LedgerBlocked();
                CustodyJournalFile file=CustodyJournalFile.ForInstalledService();
                CustodyRegistryAnchor anchor=new CustodyRegistryAnchor();
                if(anchor.RecoveryFaulted())throw new LedgerBlocked();
                return new PendingServiceState(file,anchor,
                    new PendingWinCredStore());
            }
            catch(Exception){throw new LedgerBlocked();}
        }

        public bool TrustVerified
        {
            get
            {
                try
                {
                    return ServiceGate.LiveEligible() &&
                        ProtectedAcl.VerifyInstalledCustodyDirectory() &&
                        !registry.RecoveryFaulted();
                }
                catch(Exception){return false;}
            }
        }

        private void Demand()
        {
            if(!TrustVerified)throw new LedgerBlocked();
        }

        public string ReadJournal()
        {
            Demand();
            return journal.ReadJournal();
        }
        public string ReadAnchor()
        {
            Demand();
            return registry.ReadAnchor();
        }
        public bool PendingPresent()
        {
            Demand();
            return pending.PendingPresent();
        }
        public void WriteJournal(string expected,string next)
        {
            Demand();
            journal.Append(expected,next);
        }
        public void WriteAnchor(string expected,string next)
        {
            Demand();
            registry.WriteAnchor(expected,next);
        }
        // The existing P55 transaction interface has no synchronised
        // service-owned revocation/dispatch permit. Never allow this
        // composition to reach native effects merely by enabling the SCM
        // service. Only a separately reviewed P61 successor can replace it.
        internal static bool LegacyEffectEntryDisabled()
        {
            return true;
        }

        public void SaveOrReplace(byte[] candidate)
        {
            if(LegacyEffectEntryDisabled())throw new LedgerBlocked();
            Demand();
            pending.SaveOrReplace(candidate);
        }
        public void DeletePending()
        {
            if(LegacyEffectEntryDisabled())throw new LedgerBlocked();
            Demand();
            pending.DeletePending();
        }
    }
}
