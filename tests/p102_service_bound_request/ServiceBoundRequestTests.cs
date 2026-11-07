// P102: native Windows C# tests of review-only immutable request metadata.
// Compile 10 unchanged original P49 C# units + P101 candidate host,
// updated service-owned DENIAL boundary, and P102 immutable request identity.
// No real key, elevated user, IPC, service Main, P/Invoke or native mutation.
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P102ServiceBoundRequestTests
{
    private static int passed, failed;
    private static readonly string Session = new string('a', 32);
    private static readonly string RequestId = new string('b', 32);
    private static readonly string Digest = new string('c', 64);

    private static void Need(bool ok, string message)
    { if (!ok) throw new InvalidOperationException("P102 failed: " + message); }

    private static void Test(string name, Action run)
    {
        try { run(); passed++; Console.WriteLine("PASS " + name); }
        catch (Exception e) { failed++; Console.WriteLine("FAIL " + name + " " + e.GetType().Name); }
    }

    private static void Rejected(Action fn)
    {
        bool rejected=false;
        try { fn(); } catch (ArgumentException) { rejected=true; }
        Need(rejected,"untrusted metadata must be rejected");
    }

    private static ServiceBoundRequestIdentity Draft(
        LedgerOperation op, string session=null, string id=null,
        string digest=null, long expiry=0, bool? acknowledgement=null)
    {
        bool del=op==LedgerOperation.Delete;
        return new ServiceBoundRequestIdentity(
            op,session??Session,id??RequestId,
            del ? digest : (digest??Digest),
            expiry==0 ? DateTime.UtcNow.AddMinutes(1).Ticks : expiry,
            acknowledgement.HasValue ? acknowledgement.Value : del);
    }

    private static void Denial(CustodyService host, ServiceBoundRequestIdentity request)
    {
        CustodyOutcome answer=host.RefuseBoundPendingOperation(request);
        Need(answer==CustodyOutcome.Denied ||
            answer==CustodyOutcome.RecoveryRequired,"must not admit credential effect");
        Need(!host.AuthenticatedConsentAvailable,"never claims trusted consent");
        Need(!host.NativeEffectEnabled,"no WinCred dispatch");
        Need(!host.ProductionReleaseEligible,"no production release");
    }

    public static int Main()
    {
        Test("valid-write-identity-save-denied",()=>{
            using(var h=new CustodyService()){Denial(h,Draft(LedgerOperation.Save));
                Need(h.TrackedNonSecretRequestCount==1,"one structural identity");}
        });
        Test("valid-write-identity-replace-denied",()=>{
            using(var h=new CustodyService()){Denial(h,Draft(LedgerOperation.Replace));}
        });
        Test("valid-delete-with-ack-denied",()=>{
            using(var h=new CustodyService()){Denial(h,Draft(LedgerOperation.Delete));}
        });
        Test("null-identity-denied",()=>{
            using(var h=new CustodyService()){
                Denial(h,null);Need(h.TrackedNonSecretRequestCount==0,"null not tracked");}
        });
        Test("request-expired-not-tracked",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save,expiry:DateTime.UtcNow.AddMinutes(-1).Ticks));
                Need(h.TrackedNonSecretRequestCount==0,"expired not tracked");}
        });
        Test("request-far-future-not-tracked",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save,expiry:DateTime.UtcNow.AddHours(3).Ticks));
                Need(h.TrackedNonSecretRequestCount==0,"unbounded expiry");}
        });
        Test("request-near-future-tracked",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save,expiry:DateTime.UtcNow.AddSeconds(5).Ticks));
                Need(h.TrackedNonSecretRequestCount==1,"short future structural only");}
        });
        Test("request-same-session-same-id-replay-denied",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save));
                Denial(h,Draft(LedgerOperation.Save));
                Need(h.TrackedNonSecretRequestCount==1,"duplicate never registered twice");
                Need(h.StructurallyRepeatedRequestCount==1,"duplicate seen");}
        });
        Test("request-same-nonce-changed-operation-still-denied",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save));
                Denial(h,Draft(LedgerOperation.Replace));
                Need(h.TrackedNonSecretRequestCount==1,"same identity cannot rearm");
                Need(h.StructurallyRepeatedRequestCount==1,"changed op cannot reset replay");}
        });
        Test("request-same-id-different-session-distinct-structure",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save));
                Denial(h,Draft(LedgerOperation.Save,session:new string('d',32)));
                Need(h.TrackedNonSecretRequestCount==2,"two structural records");
                Need(h.StructurallyRepeatedRequestCount==0,"not a collision");}
        });
        Test("request-different-id-same-session-distinct-structure",()=>{
            using(var h=new CustodyService()){
                Denial(h,Draft(LedgerOperation.Save));
                Denial(h,Draft(LedgerOperation.Save,id:new string('e',32)));
                Need(h.TrackedNonSecretRequestCount==2,"two distinct requests");}
        });
        Test("invalid-session-length-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,session:"short")));
        Test("invalid-session-uppercase-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,session:new string('A',32))));
        Test("invalid-request-id-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,id:"not-hex")));
        Test("invalid-request-upper-hex-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,id:new string('B',32))));
        Test("invalid-digest-length-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,digest:"abc")));
        Test("invalid-digest-uppercase-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,digest:new string('C',64))));
        Test("delete-with-digest-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Delete,digest:Digest)));
        Test("delete-without-ack-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Delete,acknowledgement:false)));
        Test("save-with-delete-ack-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,acknowledgement:true)));
        Test("initial-op-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Initial)));
        Test("invalid-op-refused",()=>Rejected(()=>
            Draft((LedgerOperation)1000)));
        Test("expired-underlying-ticks-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,expiry:-1)));
        Test("out-of-range-expiry-refused",()=>Rejected(()=>
            Draft(LedgerOperation.Save,expiry:long.MaxValue)));
        Test("untrusted-request-no-authority-in-string",()=>{
            var q=Draft(LedgerOperation.Save);
            Need(!q.ToString().Contains(Session),"redacts session");
            Need(!q.ToString().Contains(Digest),"redacts digest");
            Need(q.Operation==LedgerOperation.Save && q.CandidateSha256==Digest,
                "exact synthetic binding");
        });
        Test("all-binding-fields-immutable",()=>{
            FieldInfo[] fields=typeof(ServiceBoundRequestIdentity).GetFields(
                BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public);
            Need(fields.Length==6,"expected fixed field surface");
            foreach(FieldInfo f in fields)
                Need(f.IsInitOnly,"no mutable request binding");
        });
        Test("replay-tracking-bounded-at-128",()=>{
            using(var h=new CustodyService()){
                for(int i=0;i<180;i++){
                    string id=i.ToString("x32");
                    Denial(h,Draft(LedgerOperation.Save,id:id));
                }
                Need(h.TrackedNonSecretRequestCount==128,"bounded metadata");
                Need(h.StructurallyRepeatedRequestCount==0,"no false duplicate");
                Need(!h.PendingAdmissionFaulted,"untrusted capacity not global fault");
            }
        });
        Test("revoke-before-claim-cannot-register",()=>{
            using(var h=new CustodyService()){
                h.RevokePendingAdmission();
                Denial(h,Draft(LedgerOperation.Save));
                Need(h.TrackedNonSecretRequestCount==0,"revoked no tracking");
                Need(h.PendingAdmissionRevoked,"commit");
            }
        });
        Test("fault-before-claim-recovery-required",()=>{
            using(var h=new CustodyService()){
                h.FaultPendingAdmission();
                Need(h.RefuseBoundPendingOperation(Draft(LedgerOperation.Save))==
                    CustodyOutcome.RecoveryRequired,"fault cannot be denied-only");
                Need(h.TrackedNonSecretRequestCount==0,"fault no registration");
            }
        });
        Test("stop-before-claim-cannot-register",()=>{
            using(var h=new CustodyService()){
                var stop=typeof(CustodyService).GetMethod("OnStop",
                    BindingFlags.NonPublic|BindingFlags.Instance);
                stop.Invoke(h,null);
                Denial(h,Draft(LedgerOperation.Save));
                Need(h.PendingAdmissionStopped,"stop latched");
                Need(h.TrackedNonSecretRequestCount==0,"stop no registration");
            }
        });
        Test("eight-real-threads-same-identity-never-authorise",()=>{
            using(var h=new CustodyService()){
                int bad=0;
                var threads=new Thread[8];
                for(int i=0;i<threads.Length;i++) threads[i]=new Thread(()=>{
                    for(int j=0;j<12;j++){
                        try{
                            CustodyOutcome o=h.RefuseBoundPendingOperation(
                                Draft(LedgerOperation.Save));
                            if(o!=CustodyOutcome.Denied) Interlocked.Increment(ref bad);
                        }catch(Exception){Interlocked.Increment(ref bad);}
                    }
                });
                foreach(Thread t in threads) t.Start();
                foreach(Thread t in threads) Need(t.Join(3000),"worker joins");
                Need(bad==0,"no thread approval");
                Need(h.TrackedNonSecretRequestCount==1,"exactly one structural record");
                Need(h.StructurallyRepeatedRequestCount==95,"95 structural replays refused");
                Need(!h.NativeEffectEnabled,"no real effect");
            }
        });
        Test("concurrent-stop-versus-request-no-authority",()=>{
            using(var h=new CustodyService()){
                int invalid=0;
                var worker=new Thread(()=>{
                    for(int j=0;j<30;j++){
                        var o=h.RefuseBoundPendingOperation(
                            Draft(LedgerOperation.Replace,id:j.ToString("x32")));
                        if(o!=CustodyOutcome.Denied)Interlocked.Increment(ref invalid);
                    }
                });
                var stopper=new Thread(()=>{
                    try{
                        typeof(CustodyService).GetMethod("OnStop",
                            BindingFlags.NonPublic|BindingFlags.Instance).Invoke(h,null);
                    }catch(Exception){Interlocked.Increment(ref invalid);}
                });
                worker.Start();stopper.Start();
                Need(worker.Join(3000)&&stopper.Join(3000),"workers complete");
                Need(invalid==0 && h.PendingAdmissionStopped,"stop and refusal serialized");
            }
        });
        Test("original-native-three-deny-gates-unchanged",()=>{
            Need(!ServiceGate.LiveEligible(),"service denied");
            Need(PendingServiceState.LegacyEffectEntryDisabled(),"legacy disabled");
            Need(PendingWinCredStore.NativeMutationAdmissionPending(),"wincred disabled");
        });
        Test("no-actual-native-transaction-invocation",()=>{
            using(var h=new CustodyService()){
                Need(typeof(PendingCustodyTransaction).Assembly==
                    typeof(CustodyService).Assembly,"original native coordinator only linked");
                Denial(h,Draft(LedgerOperation.Save));
                Need(!h.ProductionReleaseEligible,"candidate nondeployable");
            }
        });

        Console.WriteLine("P102_BOUND_REQUEST_NATIVE_TESTS_PASSED="+passed);
        Console.WriteLine("P102_BOUND_REQUEST_NATIVE_TESTS_FAILED="+failed);
        Console.WriteLine("P102_STRUCTURAL_DUPLICATE_RECORD=NOT_AUTHENTICATED_CONSENT");
        Console.WriteLine("P102_NATIVE_EFFECT_AND_REAL_WIN_CRED=NONE");
        Console.WriteLine("P102_ORIGINAL_P61_RACE=OPEN");
        Console.WriteLine("P102_C1_PRODUCTION_RELEASE=HOLD");
        return failed==0 && passed==34 ? 0 : 1;
    }
}
