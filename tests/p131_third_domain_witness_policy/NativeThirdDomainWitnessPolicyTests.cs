// P131 — native Windows review-only independent receipt policy tests.
// All "external" counter, issuer, signature and enrolment fields are
// SYNTHETIC CALLER CLAIMS. This driver never provisions TPM, HKLM,
// protected files, credentials, real WinCred, consent or installed service.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P131 native tests require isolated review and synthetic flags
#endif
using System;
using System.IO;
using System.Security.Cryptography;
using System.Threading;
using Nayeon.ByokC1;

internal static class P131ThirdDomainNativeReviewTests
{
    private static int passed,failed;
    private static readonly string Issuer=new string('a',32);
    private static readonly string Enrolled=new string('b',32);
    private static readonly string OtherIssuer=new string('c',32);
    private static readonly string OtherEnrollment=new string('d',32);
    private const long Generation=4;
    private const long Counter=10;

    private static void Need(bool ok,string why)
    {if(!ok)throw new InvalidOperationException("P131 "+why);}
    private static void Run(string label,Action action)
    {
        try{action();passed++;Console.WriteLine("PASS "+label);}
        catch(Exception e)
        {failed++;Console.WriteLine("FAIL "+label+" "+e.GetType().Name+" "+e.Message);}
    }
    private static void WithLocal(Action<WindowsG3UnprotectedWitnessReview> test)
    {
        var r=new WindowsG3UnprotectedWitnessReview(Guid.NewGuid().ToString("N"));
        try{test(r);}
        finally
        {
            try{File.Delete(r.JournalForSyntheticTests.IsolatedTestFilePath);}
            catch(IOException){}
            catch(UnauthorizedAccessException){}
            try{File.Delete(r.UntrustedWitnessPathForTests);}
            catch(IOException){}
            catch(UnauthorizedAccessException){}
        }
    }
    private static void Stage(WindowsG3UnprotectedWitnessReview r,int n)
    {
        Need(r.JournalForSyntheticTests.AppendSynthetic((G3ReviewStage)n),
            "synthetic file stage "+n);
    }
    private static void History(WindowsG3UnprotectedWitnessReview r,int stages)
    {
        for(int n=1;n<=stages;n++)Stage(r,n);
        Need(r.WriteUntrustedWitnessSnapshotForTest(),
            "nonsecret unprotected witness wrote");
    }
    private static byte[] Digest(WindowsG3UnprotectedWitnessReview r)
    {
        byte[] bytes=File.ReadAllBytes(
            r.JournalForSyntheticTests.IsolatedTestFilePath);
        using(var sha=SHA256.Create())
            return sha.ComputeHash(bytes);
    }
    private static G3SyntheticExternalReceipt Receipt(
        WindowsG3UnprotectedWitnessReview r,
        int stage=1,long counter=Counter,
        string issuer=null,string enrollment=null,
        long generation=Generation,byte[] digest=null,bool fakeSigned=true)
    {
        return new G3SyntheticExternalReceipt(
            issuer??Issuer,enrollment??Enrolled,generation,counter,stage,
            digest??Digest(r),fakeSigned);
    }
    private static G3ThirdDomainReviewObservation Assess(
        WindowsG3UnprotectedWitnessReview r,
        G3SyntheticExternalReceipt receipt,
        string issuer=null,string enrollment=null,
        long generation=Generation,long floor=Counter)
    {
        return G3ThirdDomainWitnessReviewPolicy.CompareUntrusted(
            r,receipt,issuer??Issuer,enrollment??Enrolled,generation,floor);
    }
    private static void ZeroRealAuthority(G3ThirdDomainReviewObservation o)
    {
        Need(o!=null,"non-null observation");
        Need(!o.ActuallyIndependentWitnessAuthenticated,
            "no authenticated external counter");
        Need(!o.ActuallyProtectedHistoryVerified,
            "no protected journal");
        Need(!o.GenuineRollbackResistanceEstablished,
            "no antirollback trust root");
        Need(!o.ApprovedHistoricalEnrollmentVerified,
            "no independently approved enrollment");
        Need(!o.SignedServiceOrHumanAuthenticated,
            "no signed service or human");
        Need(!o.DurableOneUseGrantVerified,"no durable grant");
        Need(!o.NativeCredentialEffectAllowed,"no real WinCred");
        Need(!o.ProductionAdmissionAllowed,"no production admission");
        Need(!o.ToString().Contains("Local\\")&&
            !o.ToString().Contains("S-1-"),
            "no mutex, path or account SID leaked");
    }
    private static void Expect(
        WindowsG3UnprotectedWitnessReview r,
        G3SyntheticExternalReceipt receipt,G3ThirdDomainReviewState result,
        string issuer=null,string enrollment=null,
        long generation=Generation,long floor=Counter)
    {
        var obs=Assess(r,receipt,issuer,enrollment,generation,floor);
        Need(obs.State==result,
            "state expected "+result+" actual "+obs.State);
        ZeroRealAuthority(obs);
    }
    private static void Consistent(WindowsG3UnprotectedWitnessReview r,int stages,
        long counter=Counter,bool fakeSigned=true)
    {
        Expect(r,Receipt(r,stages,counter,fakeSigned:fakeSigned),
            G3ThirdDomainReviewState.ConsistentButEntirelyUntrusted,
            floor:counter);
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)return 25;

        Run("missing-issuer-trust-root-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r),
                G3ThirdDomainReviewState.MissingEnrollmentOrTrustRoot,
                issuer:"");
        }));
        Run("missing-enrollment-trust-root-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r),
                G3ThirdDomainReviewState.MissingEnrollmentOrTrustRoot,
                enrollment:"");
        }));
        Run("zero-service-generation-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r),
                G3ThirdDomainReviewState.MissingEnrollmentOrTrustRoot,
                generation:0);
        }));
        Run("missing-counter-floor-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r),
                G3ThirdDomainReviewState.MissingEnrollmentOrTrustRoot,
                floor:0);
        }));
        Run("null-local-history-refused",()=>{
            var o=Assess(null,new G3SyntheticExternalReceipt(
                Issuer,Enrolled,Generation,Counter,1,new byte[32],true));
            Need(o.State==G3ThirdDomainReviewState.LocalHistoryInvalid,
                "null local");
            ZeroRealAuthority(o);
        });
        Run("both-unprotected-local-files-missing-refused",()=>WithLocal(r=>{
            Expect(r,null,G3ThirdDomainReviewState.LocalHistoryInvalid);
        }));
        Run("journal-without-local-witness-refused",()=>WithLocal(r=>{
            Stage(r,1);
            Expect(r,Receipt(r),
                G3ThirdDomainReviewState.LocalHistoryInvalid);
        }));
        Run("witness-without-journal-refused",()=>WithLocal(r=>{
            History(r,1);
            File.Delete(r.JournalForSyntheticTests.IsolatedTestFilePath);
            Expect(r,null,G3ThirdDomainReviewState.LocalHistoryInvalid);
        }));
        Run("corrupted-local-journal-refused-before-external",()=>WithLocal(r=>{
            History(r,1);
            byte[] bytes=File.ReadAllBytes(
                r.JournalForSyntheticTests.IsolatedTestFilePath);
            bytes[14]^=0x01;
            File.WriteAllBytes(
                r.JournalForSyntheticTests.IsolatedTestFilePath,bytes);
            Expect(r,null,G3ThirdDomainReviewState.LocalHistoryInvalid);
        }));
        Run("local-hash-witness-mismatch-refused-before-external",()=>WithLocal(r=>{
            History(r,1);
            Stage(r,2);
            Expect(r,null,G3ThirdDomainReviewState.LocalHistoryInvalid);
        }));
        Run("no-external-receipt-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,null,G3ThirdDomainReviewState.ExternalReceiptMissing);
        }));
        Run("null-external-digest-refused",()=>WithLocal(r=>{
            History(r,1);
            var receipt=new G3SyntheticExternalReceipt(
                Issuer,Enrolled,Generation,Counter,1,null,true);
            Expect(r,receipt,G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("short-external-digest-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,digest:new byte[31]),
                G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("external-stage-zero-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,stage:0),
                G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("external-stage-over-three-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,stage:4),
                G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("invalid-external-issuer-format-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,issuer:"not-a-canonical-issuer"),
                G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("invalid-external-enrollment-format-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,enrollment:"bad"),
                G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("negative-external-counter-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,counter:-1),
                G3ThirdDomainReviewState.ExternalReceiptMalformed);
        }));
        Run("different-enrollment-denied",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,enrollment:OtherEnrollment),
                G3ThirdDomainReviewState.WrongEnrollment);
        }));
        Run("different-issuer-denied",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,issuer:OtherIssuer),
                G3ThirdDomainReviewState.WrongIssuer);
        }));
        Run("wrong-service-generation-denied",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,generation:Generation+1),
                G3ThirdDomainReviewState.WrongServiceGeneration);
        }));
        Run("counter-rollback-denied",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,counter:Counter-1),
                G3ThirdDomainReviewState.ExternalCounterRollback);
        }));
        Run("unexpected-counter-ahead-refused-pending-review",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,counter:Counter+1),
                G3ThirdDomainReviewState.ExternalCounterUnexpectedFuture);
        }));
        Run("external-checkpoint-behind-local-stages-refused",()=>WithLocal(r=>{
            History(r,2);
            Expect(r,Receipt(r,stage:1),
                G3ThirdDomainReviewState.ExternalCheckpointBehind);
        }));
        Run("local-checkpoint-behind-external-stages-refused",()=>WithLocal(r=>{
            History(r,1);
            Expect(r,Receipt(r,stage:2),
                G3ThirdDomainReviewState.LocalCheckpointBehind);
        }));
        Run("same-count-different-history-digest-refused",()=>WithLocal(r=>{
            History(r,2);
            byte[] wrong=Digest(r);wrong[0]^=0x34;
            Expect(r,Receipt(r,stage:2,digest:wrong),
                G3ThirdDomainReviewState.HistoryForkOrDigestMismatch);
        }));
        Run("matching-claims-without-signature-never-authorize",()=>WithLocal(r=>{
            History(r,3);
            Consistent(r,3,fakeSigned:false);
        }));
        Run("matching-claimed-signature-never-authorizes",()=>WithLocal(r=>{
            History(r,3);
            Consistent(r,3,fakeSigned:true);
        }));
        Run("caller-mutating-receipt-input-digest-cannot-change-snapshot",()=>
            WithLocal(r=>{
                History(r,1);
                byte[] original=Digest(r);
                var receipt=Receipt(r,digest:original);
                original[0]^=0xff;
                Expect(r,receipt,
                    G3ThirdDomainReviewState.ConsistentButEntirelyUntrusted);
            }));
        Run("caller-mutating-receipt-output-clone-cannot-change-snapshot",()=>
            WithLocal(r=>{
                History(r,1);
                var receipt=Receipt(r);
                byte[] exposed=receipt.GetReviewDigestClone();
                exposed[0]^=0xff;
                Expect(r,receipt,
                    G3ThirdDomainReviewState.ConsistentButEntirelyUntrusted);
            }));
        Run("both-local-files-rolled-back-external-receipt-intact-denied",()=>
            WithLocal(r=>{
                History(r,1);
                byte[] oldJ=File.ReadAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath);
                byte[] oldW=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
                Stage(r,2);Stage(r,3);
                Need(r.WriteUntrustedWitnessSnapshotForTest(),
                    "higher review snapshot");
                var newer=Receipt(r,stage:3,counter:Counter);
                File.WriteAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath,oldJ);
                File.WriteAllBytes(r.UntrustedWitnessPathForTests,oldW);
                Expect(r,newer,G3ThirdDomainReviewState.LocalCheckpointBehind);
            }));
        Run("both-local-and-external-counter-claims-replayed-floor-intact-denied",()=>
            WithLocal(r=>{
                History(r,1);
                byte[] oldJ=File.ReadAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath);
                byte[] oldW=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
                var old=Receipt(r,stage:1,counter:Counter-1);
                Stage(r,2);Stage(r,3);
                Need(r.WriteUntrustedWitnessSnapshotForTest(),"advanced");
                File.WriteAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath,oldJ);
                File.WriteAllBytes(r.UntrustedWitnessPathForTests,oldW);
                Expect(r,old,G3ThirdDomainReviewState.ExternalCounterRollback,
                    floor:Counter);
            }));
        Run("all-three-untrusted-claims-replayed-together-still-no-authority",()=>
            WithLocal(r=>{
                History(r,1);
                byte[] oldJ=File.ReadAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath);
                byte[] oldW=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
                var old=Receipt(r,stage:1,counter:Counter-1);
                Stage(r,2);Stage(r,3);
                Need(r.WriteUntrustedWitnessSnapshotForTest(),"advanced");
                File.WriteAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath,oldJ);
                File.WriteAllBytes(r.UntrustedWitnessPathForTests,oldW);
                Expect(r,old,
                    G3ThirdDomainReviewState.ConsistentButEntirelyUntrusted,
                    floor:Counter-1);
            }));
        Run("native-original-service-effect-gates-remain-closed",()=>WithLocal(r=>{
            History(r,3);
            Need(!ServiceGate.LiveEligible(),"P49 live gate disabled");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled()&&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 native WinCred and old effect excluded");
            Consistent(r,3);
        }));

        Console.WriteLine("P131_THIRD_DOMAIN_NATIVE_POLICY_CASES_PASSED="+passed);
        Console.WriteLine("P131_THIRD_DOMAIN_NATIVE_POLICY_CASES_FAILED="+failed);
        Console.WriteLine("P131_EXTERNAL_RECEIPT=CALLER_SUPPLIED_SYNTHETIC_CLAIM_ONLY");
        Console.WriteLine("P131_SAME_PRINCIPAL_THREE_RECORD_ROLLBACK=UNTRUSTED");
        Console.WriteLine("P131_WITNESS_COUNTER_FORK_AND_EPOCH_REVIEW_NEGATIVES=TESTED");
        Console.WriteLine("P131_TPM_OR_EXTERNAL_TRUST_ROOT_VERIFIED=FALSE");
        Console.WriteLine("P131_REAL_SIGNED_CONSENT_WINCRED=NONE");
        Console.WriteLine("P131_G0_QUALIFIED_SECURITY_REVIEW=NOT_OBTAINED");
        Console.WriteLine("P131_ORIGINAL_P96_RACE=OPEN");
        Console.WriteLine("P131_C1_PRODUCTION_RELEASE=HOLD");
        return passed==34&&failed==0?0:1;
    }
}
