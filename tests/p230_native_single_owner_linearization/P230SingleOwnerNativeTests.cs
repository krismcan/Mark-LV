// P230 deterministic original P95/P96 byte-identical source-linked Windows
// threads, one owner of synthetic marker AND revoke/stop/fault. No real keys.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P230 native test suite NONDEPLOYABLE TEST-ONLY
#endif
using System;
using System.Threading;
using System.Reflection;

namespace Nayeon.ByokC1
{
    internal static class P230SingleOwnerNativeTests
    {
        private static int passed,failed;
        private static void Need(bool ok,string why)
        {if(!ok) throw new InvalidOperationException(why);}
        private static void Run(string name,Action action)
        {
            try{action();++passed;Console.WriteLine("PASS "+name);}
            catch(Exception ex)
            {++failed;Console.WriteLine("FAIL "+name+" "+ex.GetType().Name);}
        }
        private static P230SingleOwnerSyntheticActor Armed(
            LedgerOperation op,bool present=false)
        {
            var actor=new P230SingleOwnerSyntheticActor(present);
            Need(actor.ArmFakeOnly(op,op==LedgerOperation.Delete),"not armed");
            return actor;
        }
        private static void Race(string label,LedgerOperation op,Action<P230SingleOwnerSyntheticActor> transition)
        {
            Run(label,()=>
            {
                var a=Armed(op,op!=LedgerOperation.Save);
                using(var entered=new ManualResetEvent(false))
                using(var release=new ManualResetEvent(false))
                using(var started=new ManualResetEvent(false))
                using(var committed=new ManualResetEvent(false))
                {
                    CustodyOutcome operationOutcome=CustodyOutcome.Denied;
                    Exception operationException=null,transitionException=null;
                    var operationThread=new Thread(()=>
                    {
                        try{operationOutcome=a.AttemptFakeOnly(entered,release);}
                        catch(Exception ex){operationException=ex;}
                    });
                    var transitionThread=new Thread(()=>
                    {
                        started.Set();
                        try{transition(a);committed.Set();}
                        catch(Exception ex){transitionException=ex;}
                    });
                    operationThread.IsBackground=true;
                    transitionThread.IsBackground=true;
                    operationThread.Start();
                    if(!entered.WaitOne(2000))
                    {
                        release.Set();operationThread.Join(3000);
                        throw new InvalidOperationException("effect not entered");
                    }
                    transitionThread.Start();
                    bool didStart=started.WaitOne(2000);
                    bool transitionTooEarly=committed.WaitOne(80);
                    release.Set();
                    Need(operationThread.Join(3000),"effect thread hang");
                    Need(transitionThread.Join(3000),"transition thread hang");
                    Need(didStart && !transitionTooEarly,
                         "revoke/stop/fault committed during terminal gate");
                    Need(operationException==null && transitionException==null,
                         "native test thread failure");
                    Need(operationOutcome==CustodyOutcome.RecoveryRequired,
                         "synthetic terminal cannot become trusted success");
                    Need(a.FakeEffects==1 && a.FakeEffectsAfterCommittedRevoke==0,
                         "fake effect after committed transition");
                    Need(a.TooLateTransitions==1,
                         "transition after dispatch must report too-late");
                    Need(a.RecoveryRequired,"sticky no-retry after dispatch");
                    Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,
                         "second fake effect or replay");
                    Need(a.FakeEffects==1,"more than one marker effect");
                }
            });
        }

        public static int Main()
        {
            Run("P230-no-arm-default-denied",()=>
            {
                var a=new P230SingleOwnerSyntheticActor();
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"unarmed");
                Need(a.FakeEffects==0,"unarmed effect");
            });
            Run("P230-invalid-typed-operation-shapes-denied",()=>
            {
                var a=new P230SingleOwnerSyntheticActor();
                Need(!a.ArmFakeOnly(LedgerOperation.Initial,false),"initial");
                Need(!a.ArmFakeOnly(LedgerOperation.Save,true),"save-ack");
                Need(!a.ArmFakeOnly(LedgerOperation.Replace,true),"replace-ack");
                Need(!a.ArmFakeOnly(LedgerOperation.Delete,false),"delete-unack");
                Need(a.FakeEffects==0,"invalid effect");
            });
            Run("P230-new-save-one-fixed-marker-recovery",()=>
            {
                var a=Armed(LedgerOperation.Save);
                Need(a.AttemptFakeOnly()==CustodyOutcome.RecoveryRequired,
                     "in-memory journal is not durable");
                Need(a.FakeEffects==1 && a.RecoveryRequired,"one fake marker");
            });
            Run("P230-seeded-replace-one-fixed-marker-recovery",()=>
            {
                var a=Armed(LedgerOperation.Replace,true);
                Need(a.AttemptFakeOnly()==CustodyOutcome.RecoveryRequired,"replace");
                Need(a.FakeEffects==1,"replace exact once");
            });
            Run("P230-seeded-delete-one-fixed-marker-recovery",()=>
            {
                var a=Armed(LedgerOperation.Delete,true);
                Need(a.AttemptFakeOnly()==CustodyOutcome.RecoveryRequired,"delete");
                Need(a.FakeEffects==1,"delete exact once");
            });
            Run("P230-unseeded-replace-no-effect",()=>
            {
                var a=Armed(LedgerOperation.Replace);
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"replace absent");
                Need(a.FakeEffects==0 && a.RecoveryRequired,"absence no retry");
            });
            Run("P230-unseeded-delete-no-effect",()=>
            {
                var a=Armed(LedgerOperation.Delete);
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"delete absent");
                Need(a.FakeEffects==0 && a.RecoveryRequired,"no effect");
            });
            Run("P230-seeded-save-no-effect",()=>
            {
                var a=Armed(LedgerOperation.Save,true);
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"save present");
                Need(a.FakeEffects==0 && a.RecoveryRequired,"no effect");
            });
            Run("P230-revoke-before-dispatch-zero-effect",()=>
            {
                var a=Armed(LedgerOperation.Save);
                a.Revoke();
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"revoke");
                Need(a.FakeEffects==0 && a.IsRevoked,"zero");
            });
            Run("P230-stop-before-dispatch-zero-effect",()=>
            {
                var a=Armed(LedgerOperation.Save);
                a.Stop();
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"stop");
                Need(a.FakeEffects==0 && a.IsStopped && a.IsRevoked,"zero");
            });
            Run("P230-fault-before-dispatch-zero-effect",()=>
            {
                var a=Armed(LedgerOperation.Save);
                a.Fault();
                Need(a.AttemptFakeOnly()==CustodyOutcome.RecoveryRequired,"fault");
                Need(a.FakeEffects==0 && a.IsFaulted && a.RecoveryRequired,"zero");
            });
            Run("P230-uncertain-result-one-marker-no-retry",()=>
            {
                var a=Armed(LedgerOperation.Save);
                Need(a.AttemptFakeOnly(null,null,true)==CustodyOutcome.RecoveryRequired,
                     "unknown");
                Need(a.UnknownFakeEffects==1 && a.FakeEffects==1,"unknown count");
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"no retry");
            });
            Run("P230-journal-fault-before-dispatch-zero-marker",()=>
            {
                var a=Armed(LedgerOperation.Save);
                Need(a.AttemptFakeOnly(null,null,false,true)==CustodyOutcome.RecoveryRequired,
                     "in-memory uncertain journal");
                Need(a.FakeEffects==0 && a.RecoveryRequired,"zero and sticky");
            });
            Run("P230-wait-timeout-before-effect-zero-marker-no-retry",()=>
            {
                var a=Armed(LedgerOperation.Save);
                using(var never=new ManualResetEvent(false))
                {
                    Need(a.AttemptFakeOnly(null,never)==CustodyOutcome.RecoveryRequired,
                         "synthetic fake terminal timeout");
                }
                Need(a.FakeEffects==0 && a.RecoveryRequired,"timed out zero");
                Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"stale retry");
            });
            Run("P230-one-use-after-success-no-second-effect",()=>
            {
                var a=Armed(LedgerOperation.Save);
                a.AttemptFakeOnly();
                for(int i=0;i<12;++i)
                    Need(a.AttemptFakeOnly()==CustodyOutcome.Denied,"replay");
                Need(a.FakeEffects==1,"one");
            });
            Run("P230-double-arm-refused-even-before-effect",()=>
            {
                var a=Armed(LedgerOperation.Save);
                Need(!a.ArmFakeOnly(LedgerOperation.Save,false),"duplicate");
                Need(a.AttemptFakeOnly()==CustodyOutcome.RecoveryRequired,"original arm");
                Need(!a.ArmFakeOnly(LedgerOperation.Save,false),"after");
            });
            Run("P230-original-P96-source-flaw-still-reproduced",()=>
            {
                var f=new P96Fixture();
                f.Guard.InjectRevocationAtFinalOwnershipCheck=true;
                CustodyOutcome outcome=f.ActualCoordinator.Apply(
                    LedgerOperation.Save,P96Fixture.Dummy());
                Need(f.Guard.RevokedOnSeparateThread && !f.Approval.Current,
                     "old race injection not reached");
                Need(f.State.EffectsAfterRevoke==1 && f.State.PossibleEffects==1,
                     "original P96 defect must remain evidenced");
                Need(outcome==CustodyOutcome.StoredUnverified,
                     "original vulnerable source unexpectedly changed");
            });
            Race("P230-revoke-during-save-fixed-marker-serialized",
                 LedgerOperation.Save,a=>a.Revoke());
            Race("P230-stop-during-replace-fixed-marker-serialized",
                 LedgerOperation.Replace,a=>a.Stop());
            Race("P230-fault-during-delete-fixed-marker-serialized",
                 LedgerOperation.Delete,a=>a.Fault());
            Run("P230-no-credential-byte-or-delegate-param-in-native-review-actor",()=>
            {
                var methods=typeof(P230SingleOwnerSyntheticActor).GetMethods(
                    BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Public);
                foreach(var m in methods)
                    foreach(var p in m.GetParameters())
                    {
                        Type t=p.ParameterType;
                        Need(t!=typeof(byte[]) && t!=typeof(string) &&
                             !typeof(Delegate).IsAssignableFrom(t),
                             "credential/effect callback imported");
                    }
            });
            Run("P230-no-service-store-or-issuer-release-authority",()=>
            {
                var a=new P230SingleOwnerSyntheticActor();
                Need(!a.NativeWindowsCredentialEffectEnabled &&
                     !a.ActualServicePrincipalStoreVerified &&
                     !a.AuthenticatedHumanConsentIssuerAvailable &&
                     !a.DurableJournalAnchorVerified &&
                     !a.SignedInstalledRuntimeApproved &&
                     !a.ProductionReleaseEligible &&
                     !a.OriginalP96ProductionSourceFixed,
                     "test-only actor self-authorized production");
            });
            Console.WriteLine("P230_NATIVE_SERVICE_ACTOR_REVIEW_PASSED="+passed);
            Console.WriteLine("P230_NATIVE_SERVICE_ACTOR_REVIEW_FAILED="+failed);
            Console.WriteLine("P230_ISOLATED_SYNTHETIC_EFFECT_ACTOR=NOT_PRODUCTION_SOURCE");
            Console.WriteLine("P230_ORIGINAL_P96_REVOCATION_RACE=STILL_OPEN");
            Console.WriteLine("P230_WINDOWS_CREDENTIAL_EFFECTS=NONE");
            Console.WriteLine("P230_REAL_KEYS=NO_GO");
            Console.WriteLine("P230_PRODUCTION_RELEASE=HOLD");
            return passed==22 && failed==0 ? 0:1;
        }
    }
}
