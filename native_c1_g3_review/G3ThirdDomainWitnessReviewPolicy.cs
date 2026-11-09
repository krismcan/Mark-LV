// P131 — service-shaped G3 independent historical witness ADMISSION
// CONTRACT, negative-only and test-only. No trust root is installed or
// verified. A caller-supplied "external receipt" and expected counter
// remain UNTRUSTED SYNTHETIC DATA and can be forged/rolled back together.
// It models required fail-closed states for qualified security review;
// it does NOT authorize a real operation, protected storage or WinCred.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P131 witness contract must never compile for real service or user consent
#endif
using System;
using System.IO;
using System.Security.Cryptography;

namespace Nayeon.ByokC1
{
    internal enum G3ThirdDomainReviewState
    {
        MissingEnrollmentOrTrustRoot,
        LocalHistoryInvalid,
        ExternalReceiptMissing,
        ExternalReceiptMalformed,
        WrongEnrollment,
        WrongIssuer,
        WrongServiceGeneration,
        ExternalCounterRollback,
        ExternalCounterUnexpectedFuture,
        ExternalCheckpointBehind,
        LocalCheckpointBehind,
        HistoryForkOrDigestMismatch,
        ConsistentButEntirelyUntrusted
    }

    internal sealed class G3SyntheticExternalReceipt
    {
        internal readonly string IssuerClaim;
        internal readonly string EnrollmentClaim;
        internal readonly long ServiceGeneration;
        internal readonly long CounterClaim;
        internal readonly int StageClaim;
        private readonly byte[] digestCopy;
        internal readonly bool ClaimedSignatureVerified;

        internal G3SyntheticExternalReceipt(
            string issuer,string enrollment,long generation,long counter,
            int stage,byte[] claimedJournalSha256,bool fakeSignatureClaim)
        {
            IssuerClaim=issuer;
            EnrollmentClaim=enrollment;
            ServiceGeneration=generation;
            CounterClaim=counter;
            StageClaim=stage;
            digestCopy=claimedJournalSha256==null?null:
                (byte[])claimedJournalSha256.Clone();
            ClaimedSignatureVerified=fakeSignatureClaim;
        }

        internal byte[] GetReviewDigestClone()
        {return digestCopy==null?null:(byte[])digestCopy.Clone();}
    }

    internal sealed class G3ThirdDomainReviewObservation
    {
        internal readonly G3ThirdDomainReviewState State;
        internal readonly int LocalStages;
        internal readonly int ExternalStages;
        internal readonly bool StructuralSnapshotConsistent;
        internal G3ThirdDomainReviewObservation(
            G3ThirdDomainReviewState state,int local,int external,bool consistent)
        {
            State=state;
            LocalStages=local;
            ExternalStages=external;
            StructuralSnapshotConsistent=consistent;
        }

        internal bool ActuallyIndependentWitnessAuthenticated {get{return false;}}
        internal bool ActuallyProtectedHistoryVerified {get{return false;}}
        internal bool GenuineRollbackResistanceEstablished {get{return false;}}
        internal bool ApprovedHistoricalEnrollmentVerified {get{return false;}}
        internal bool SignedServiceOrHumanAuthenticated {get{return false;}}
        internal bool DurableOneUseGrantVerified {get{return false;}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}
        internal bool ProductionAdmissionAllowed {get{return false;}}

        public override string ToString()
        {return "<P131 synthetic third-domain claim; G0-G6 HOLD; no consent or WinCred>";}
    }

    internal static class G3ThirdDomainWitnessReviewPolicy
    {
        private const int Sha256Bytes=32;
        private static bool CanonicalTestId(string value)
        {
            if(value==null||value.Length!=32)return false;
            for(int i=0;i<value.Length;i++)
            {
                char c=value[i];
                if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))
                    return false;
            }
            return true;
        }
        private static G3ThirdDomainReviewObservation Result(
            G3ThirdDomainReviewState state,int local,int external,
            bool consistent=false)
        {return new G3ThirdDomainReviewObservation(state,local,external,consistent);}

        // For the isolated test, caller-supplied prior counter/issuer/
        // enrollment are NOT actually obtained from independent hardware
        // or a signed external audit service. A well-formed result can
        // NEVER be elevated to trust or release.
        internal static G3ThirdDomainReviewObservation CompareUntrusted(
            WindowsG3UnprotectedWitnessReview local,
            G3SyntheticExternalReceipt external,
            string expectedIssuerClaim,
            string expectedEnrollmentClaim,
            long expectedServiceGeneration,
            long expectedIndependentCounterClaim)
        {
            if(!CanonicalTestId(expectedIssuerClaim)||
                !CanonicalTestId(expectedEnrollmentClaim)||
                expectedServiceGeneration<=0||
                expectedIndependentCounterClaim<=0)
                return Result(
                    G3ThirdDomainReviewState.MissingEnrollmentOrTrustRoot,0,0);
            if(local==null)
                return Result(G3ThirdDomainReviewState.LocalHistoryInvalid,0,0);

            // P130 already refuses inconsistent, missing, corrupt and
            // rolled-back-in-isolation journal/witness files. It is NOT
            // an atomic snapshot, so any apparent validity is diagnostic.
            G3ReviewWitnessObservation localReview=local.CompareUntrustedFiles();
            if(!localReview.MatchedForDiagnosticOnly)
                return Result(G3ThirdDomainReviewState.LocalHistoryInvalid,
                    localReview.JournalCount,0);

            if(external==null)
                return Result(G3ThirdDomainReviewState.ExternalReceiptMissing,
                    localReview.JournalCount,0);

            byte[] expectedDigest=external.GetReviewDigestClone();
            if(expectedDigest==null||expectedDigest.Length!=Sha256Bytes ||
                external.StageClaim<1||external.StageClaim>3||
                external.CounterClaim<=0||
                !CanonicalTestId(external.IssuerClaim)||
                !CanonicalTestId(external.EnrollmentClaim))
                return Result(G3ThirdDomainReviewState.ExternalReceiptMalformed,
                    localReview.JournalCount,external.StageClaim);

            if(!String.Equals(external.EnrollmentClaim,
                expectedEnrollmentClaim,StringComparison.Ordinal))
                return Result(G3ThirdDomainReviewState.WrongEnrollment,
                    localReview.JournalCount,external.StageClaim);

            if(!String.Equals(external.IssuerClaim,
                expectedIssuerClaim,StringComparison.Ordinal))
                return Result(G3ThirdDomainReviewState.WrongIssuer,
                    localReview.JournalCount,external.StageClaim);

            if(external.ServiceGeneration!=expectedServiceGeneration)
                return Result(G3ThirdDomainReviewState.WrongServiceGeneration,
                    localReview.JournalCount,external.StageClaim);

            if(external.CounterClaim<expectedIndependentCounterClaim)
                return Result(G3ThirdDomainReviewState.ExternalCounterRollback,
                    localReview.JournalCount,external.StageClaim);
            if(external.CounterClaim>expectedIndependentCounterClaim)
                return Result(
                    G3ThirdDomainReviewState.ExternalCounterUnexpectedFuture,
                    localReview.JournalCount,external.StageClaim);

            if(external.StageClaim<localReview.JournalCount)
                return Result(G3ThirdDomainReviewState.ExternalCheckpointBehind,
                    localReview.JournalCount,external.StageClaim);

            if(external.StageClaim>localReview.JournalCount)
                return Result(G3ThirdDomainReviewState.LocalCheckpointBehind,
                    localReview.JournalCount,external.StageClaim);

            // A genuine independent service/TPM should attest history.
            // This SHA256 is only data comparison: no signature, no
            // trusted counter, no hardware root. No WinCred unlock.
            byte[] current;
            try
            {
                string file=local.JournalForSyntheticTests.IsolatedTestFilePath;
                using(var stream=new FileStream(file,FileMode.Open,
                    FileAccess.Read,FileShare.ReadWrite))
                {
                    long length=stream.Length;
                    if(length!=localReview.JournalCount*
                        WindowsG3EphemeralReviewJournal.FrameSize)
                        return Result(
                            G3ThirdDomainReviewState.LocalHistoryInvalid,
                            localReview.JournalCount,external.StageClaim);
                    byte[] bytes=new byte[(int)length];
                    int n=0;
                    while(n<bytes.Length)
                    {
                        int got=stream.Read(bytes,n,bytes.Length-n);
                        if(got<=0)
                            return Result(
                                G3ThirdDomainReviewState.LocalHistoryInvalid,
                                localReview.JournalCount,external.StageClaim);
                        n+=got;
                    }
                    using(var sha=SHA256.Create())
                        current=sha.ComputeHash(bytes);
                }
            }
            catch(Exception)
            {return Result(G3ThirdDomainReviewState.LocalHistoryInvalid,
                localReview.JournalCount,external.StageClaim);}

            int different=0;
            for(int i=0;i<Sha256Bytes;i++)
                different|=current[i]^expectedDigest[i];
            if(different!=0)
                return Result(
                    G3ThirdDomainReviewState.HistoryForkOrDigestMismatch,
                    localReview.JournalCount,external.StageClaim);

            // Test-only claims can ALL be replayed together. No
            // "permission" state exists even if claimed signature=true.
            return Result(
                G3ThirdDomainReviewState.ConsistentButEntirelyUntrusted,
                localReview.JournalCount,external.StageClaim,true);
        }
    }
}
