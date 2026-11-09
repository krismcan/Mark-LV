// P127 REAL native Windows unprivileged fixed-transaction sequence tests.
// No WinCred, protected journal, real consent, service install or credentials.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P127 native driver is isolated synthetic Windows review ONLY
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P127WindowsUnifiedActorTests
{
    private static int passed,failed;
    private static string Name()
    {return "Local\\Nayeon-C1-P127-"+Guid.NewGuid().ToString("N");}
    private static string Exe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}
    private static void Need(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("P127 "+why);}
    private static void Run(string title,Action action)
    {
        try{action();++passed;Console.WriteLine("PASS "+title);}
        catch(Exception ex)
        {++failed;Console.WriteLine("FAIL "+title+" "+ex.GetType().Name+" "+ex.Message);}
    }
    private static void Held(WindowsG2UnifiedReviewTransaction c)
    {
        Need(c!=null&&!c.TrustVerified&&
            !c.DurableJournalVerified&&
            !c.ProtectedAnchorVerified&&
            !c.HumanConsentVerified&&
            !c.NativeCredentialEffectAllowed&&
            !c.ProductionReleaseEligible,
            "no actual trust, durability, WinCred or release");
        Need(!c.ToString().Contains("Local\\Nayeon"),
            "never reveal OS custody mutex name in review status");
    }
    private static void Prepared(WindowsG2UnifiedReviewTransaction c,
        LedgerOperation op=LedgerOperation.Save,bool ack=false)
    {Need(c.PrepareSyntheticOnly(op,ack),"review-only prepared");}
    private static CustodyOutcome TryFake(
        WindowsG2UnifiedReviewTransaction c,LedgerOperation op=LedgerOperation.Save,
        ManualResetEvent entered=null,ManualResetEvent release=null,
        bool before=false,bool unknown=false,bool terminal=false)
    {return c.AttemptSyntheticOnly(op,entered,release,before,unknown,terminal);}
    private static void One(WindowsG2UnifiedReviewTransaction c,
        int intents,int effects,int terminals)
    {
        Need(c.SyntheticIntents==intents&&
            c.SyntheticEffects==effects&&
            c.SyntheticTerminals==terminals,
            "integer-only (intent,effect,terminal) expected "+
            intents+","+effects+","+terminals+" observed "+
            c.SyntheticIntents+","+c.SyntheticEffects+","+c.SyntheticTerminals);
        Held(c);
    }

    // All child modes use genuine OS process-shared named Mutexes under
    // unprivileged GitHub Windows runner. No other effects or persistence.
    private static int Child(string[] args)
    {
        try
        {
            if(args.Length!=3||args[0]!="--p127-child"||
                !args[2].StartsWith("Local\\Nayeon-C1-P127-",
                    StringComparison.Ordinal))return 21;
            using(var mutex=new Mutex(false,args[2]))
            {
                if(args[1]=="probe")
                {
                    bool acquired=false;
                    try
                    {
                        acquired=mutex.WaitOne(160);
                        Console.WriteLine(acquired?"P127_FREE":"P127_BUSY");
                        return 0;
                    }
                    catch(AbandonedMutexException)
                    {acquired=true;Console.WriteLine("P127_ABANDONED");return 0;}
                    finally
                    {if(acquired)mutex.ReleaseMutex();}
                }
                if(args[1]!="hold"&&args[1]!="abandon")return 22;
                if(!mutex.WaitOne(4500))return 23;
                Console.WriteLine("P127_HELD");Console.Out.Flush();
                if(args[1]=="abandon")
                {
                    Environment.Exit(0);
                    return 0;
                }
                using(var signal=new EventWaitHandle(false,
                    EventResetMode.ManualReset,args[2]+"-release"))
                {
                    if(!signal.WaitOne(4500))return 24;
                }
                mutex.ReleaseMutex();
                return 0;
            }
        }
        catch(Exception){return 25;}
    }
    private sealed class Owner : IDisposable
    {
        internal readonly Process ChildProcess;
        private readonly EventWaitHandle signal;
        internal Owner(Process p,EventWaitHandle e)
        {ChildProcess=p;signal=e;}
        internal void Release()
        {
            Need(signal.Set(),"native event release signal");
            Need(ChildProcess.WaitForExit(5000),"external child joined");
            Need(ChildProcess.ExitCode==0,"external child exited clean");
        }
        public void Dispose()
        {
            if(!ChildProcess.HasExited)ChildProcess.Kill();
            ChildProcess.Dispose();
            signal.Dispose();
        }
    }
    private static Owner StartOwner(string name,string mode)
    {
        var signal=new EventWaitHandle(false,
            EventResetMode.ManualReset,name+"-release");
        var start=new ProcessStartInfo(Exe(),
            "--p127-child "+mode+" "+name);
        start.UseShellExecute=false;
        start.CreateNoWindow=true;
        start.RedirectStandardOutput=true;
        var p=Process.Start(start);
        Need(p!=null&&p.Id>0,"actual Windows child started");
        using(var self=Process.GetCurrentProcess())
            Need(self.Id!=p.Id,"genuinely separate OS process");
        Need(p.StandardOutput.ReadLine()=="P127_HELD",
            "child has OS named mutex");
        return new Owner(p,signal);
    }
    private static string Probe(string name)
    {
        var info=new ProcessStartInfo(Exe(),
            "--p127-child probe "+name);
        info.UseShellExecute=false;info.CreateNoWindow=true;
        info.RedirectStandardOutput=true;
        using(var p=Process.Start(info))
        {
            Need(p!=null&&p.Id>0,"probe child launched");
            string first=p.StandardOutput.ReadLine();
            Need(p.WaitForExit(5000)&&p.ExitCode==0,
                "cross-process probe completed");
            return first;
        }
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p127-child")return Child(args);
            return 27;
        }
        Run("production-mutex-name-is-not-review-admissible",()=>{
            bool denied=false;
            try{new WindowsG2UnifiedReviewTransaction(
                "Global\\NayeonActualCustody");}
            catch(ArgumentException){denied=true;}
            Need(denied,"only local ephemeral test mutex");
        });
        Run("short-and-noncanonical-mutex-names-refused",()=>{
            bool a=false,b=false;
            try{new WindowsG2UnifiedReviewTransaction(
                "Local\\Nayeon-C1-P127-1");}
            catch(ArgumentException){a=true;}
            try{new WindowsG2UnifiedReviewTransaction(
                "Local\\Nayeon-C1-P127-"+new string('A',32));}
            catch(ArgumentException){b=true;}
            Need(a&&b,"both rejected");
        });
        Run("fresh-instance-never-contains-trust-or-durability",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {One(c,0,0,0);}
        });
        Run("fake-SAVE-intent-effect-terminal-still-recovery",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,
                    "never claim persisted success");
                Need(c.RecoveryRequired,"sticky after attempt");
                One(c,1,1,1);
            }
        });
        Run("fake-REPLACE-intent-effect-terminal-still-recovery",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c,LedgerOperation.Replace);
                Need(TryFake(c,LedgerOperation.Replace)==
                    CustodyOutcome.RecoveryRequired,"never real replacement");
                One(c,1,1,1);
            }
        });
        Run("fake-DELETE-requires-exact-destructive-ack",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Delete,false),
                    "missing delete acknowledgement");
                Prepared(c,LedgerOperation.Delete,true);
                Need(TryFake(c,LedgerOperation.Delete)==
                    CustodyOutcome.RecoveryRequired,"fake DELETE recovery");
                One(c,1,1,1);
            }
        });
        Run("save-with-delete-ack-refused-before-intent",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Save,true),
                    "invalid acknowledgement");
                One(c,0,0,0);
            }
        });
        Run("unknown-operation-cannot-bind-fake-custody",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Need(!c.PrepareSyntheticOnly((LedgerOperation)700,false),
                    "unknown op denied");
                One(c,0,0,0);
            }
        });
        Run("wrong-bound-operation-burns-before-intent",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);
                Need(TryFake(c,LedgerOperation.Delete)==CustodyOutcome.Denied,
                    "shape mismatch denied");
                Need(c.RecoveryRequired,"sticky no retry");
                One(c,0,0,0);
            }
        });
        Run("pre-intent-failure-no-fake-effect-and-recovery",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);
                Need(TryFake(c,before:true)==CustodyOutcome.RecoveryRequired,
                    "failure before integer intent");
                One(c,0,0,0);
            }
        });
        Run("uncertain-fake-effect-leaves-inflight-not-terminal",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);
                Need(TryFake(c,unknown:true)==CustodyOutcome.RecoveryRequired,
                    "possible attempt never successful");
                Need(c.UnknownOutcomes==1,"uncertain detected");
                One(c,1,1,0);
            }
        });
        Run("terminal-witness-failure-does-not-clear-unknown",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);
                Need(TryFake(c,terminal:true)==CustodyOutcome.RecoveryRequired,
                    "no fake terminal witness");
                Need(c.UnknownOutcomes==1,"uncertainty preserved");
                One(c,1,1,0);
            }
        });
        Run("no-rearm-after-completed-synthetic-stages",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);TryFake(c);
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Replace,false),
                    "replay blocked");
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,
                    "effect not retried");
                One(c,1,1,1);
            }
        });
        Run("no-rearm-after-inflight-unknown-outcome",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);TryFake(c,unknown:true);
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Save,false),
                    "unknown not replayable");
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,
                    "unverified cannot be resent");
                One(c,1,1,0);
            }
        });
        Run("revocation-wins-before-both-locks-no-effects",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);c.Revoke();
                Need(TryFake(c)==CustodyOutcome.Denied,"revoke wins");
                One(c,0,0,0);
            }
        });
        Run("stop-wins-before-both-locks-no-effects",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);c.Stop();
                Need(TryFake(c)==CustodyOutcome.Denied,"stop wins");
                One(c,0,0,0);
            }
        });
        Run("fault-wins-before-both-locks-no-effects",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);c.MarkFault();
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,"fault wins");
                One(c,0,0,0);
            }
        });
        Run("one-fake-effect-under-twelve-native-threads",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            using(var start=new ManualResetEvent(false))
            {
                Prepared(c);
                int unexpected=0;var threads=new Thread[12];
                for(int i=0;i<threads.Length;i++)
                {
                    threads[i]=new Thread(()=>{
                        start.WaitOne();
                        if(TryFake(c)!=CustodyOutcome.RecoveryRequired)
                            Interlocked.Increment(ref unexpected);
                    });threads[i].Start();
                }
                start.Set();
                foreach(var thread in threads)
                    Need(thread.Join(5000),"threads joined");
                Need(unexpected==0,"no false success");
                One(c,1,1,1);
            }
        });
        Run("revoke-during-OS-lease-is-late-not-cancellation",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            using(var entered=new ManualResetEvent(false))
            using(var release=new ManualResetEvent(false))
            {
                Prepared(c);
                var effect=new Thread(()=>TryFake(c,entered:entered,release:release));
                var revoke=new Thread(()=>c.Revoke());
                effect.Start();
                Need(entered.WaitOne(2000),"fake intent + effect inside OS lease");
                revoke.Start();release.Set();
                Need(effect.Join(5000)&&revoke.Join(5000),"threads joined");
                Need(c.TooLateRevocations==1,
                    "late revoke never cancels prior fake effect");
                One(c,1,1,1);
            }
        });
        Run("external-OS-process-holds-lease-no-intent",()=>{
            string name=Name();
            using(var c=new WindowsG2UnifiedReviewTransaction(name))
            using(var owner=StartOwner(name,"hold"))
            {
                Prepared(c);
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,
                    "busy kernel custody lock forces recovery");
                One(c,0,0,0);
                owner.Release();
            }
        });
        Run("abandoned-OS-mutex-owner-no-intent-effect",()=>{
            string name=Name();
            using(var c=new WindowsG2UnifiedReviewTransaction(name))
            using(var owner=StartOwner(name,"abandon"))
            {
                Need(owner.ChildProcess.WaitForExit(4500)&&
                    owner.ChildProcess.ExitCode==0,"actual OS owner died");
                Prepared(c);
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,
                    "abandoned OS lease not trustworthy");
                Need(c.AbandonedAcquisitions==1,
                    "native abandoned ownership observed");
                One(c,0,0,0);
            }
        });
        Run("separate-OS-process-sees-busy-during-fake-effect",()=>{
            string name=Name();
            using(var c=new WindowsG2UnifiedReviewTransaction(name))
            using(var entered=new ManualResetEvent(false))
            using(var release=new ManualResetEvent(false))
            {
                Prepared(c);
                var writer=new Thread(()=>TryFake(c,entered:entered,release:release));
                writer.Start();
                Need(entered.WaitOne(2200),"fake effect entered real kernel lease");
                string occupied=Probe(name);
                release.Set();
                Need(writer.Join(5000),"writer left kernel lease");
                string freed=Probe(name);
                Need(occupied=="P127_BUSY"&&freed=="P127_FREE",
                    "real OS process-shared lease blocks during attempt");
                One(c,1,1,1);
            }
        });
        Run("new-instance-same-mutex-does-NOT-inherit-fake-history",()=>{
            string name=Name();
            using(var a=new WindowsG2UnifiedReviewTransaction(name))
            {
                Prepared(a);
                TryFake(a,terminal:true);
                One(a,1,1,0);
            }
            using(var b=new WindowsG2UnifiedReviewTransaction(name))
            {
                // Explicit negative G3 proof: new instance sees NO
                // durable witness. This is NOT safe for production.
                One(b,0,0,0);
                Need(!b.DurableJournalVerified,
                    "cannot misreport protected crash recovery");
            }
        });
        Run("same-actor-fake-phase-order-never-success",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Prepared(c);
                Need(TryFake(c)==CustodyOutcome.RecoveryRequired,
                    "even three stage markers are no durability proof");
                Need(c.SyntheticIntents==c.SyntheticEffects&&
                    c.SyntheticEffects==c.SyntheticTerminals,
                    "integer-only normal stage count");
                Held(c);
            }
        });
        Run("original-P49-P112-real-effect-admission-remains-closed",()=>{
            using(var c=new WindowsG2UnifiedReviewTransaction(Name()))
            {
                Need(!ServiceGate.LiveEligible(),"P49 live gate denied");
                Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled()&&
                    CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                    "P112 native effect/old coordinator disabled");
                Held(c);
            }
        });

        Console.WriteLine("P127_UNIFIED_NATIVE_ACTOR_CASES_PASSED="+passed);
        Console.WriteLine("P127_UNIFIED_NATIVE_ACTOR_CASES_FAILED="+failed);
        Console.WriteLine("P127_REAL_WINDOWS_OS_MUTEX_PLUS_ONE_REVOCATION_MONITOR=TESTED");
        Console.WriteLine("P127_INTENT_EFFECT_TERMINAL_PHASES=IN_MEMORY_INTEGERS_ONLY");
        Console.WriteLine("P127_RESTART_HISTORY_LOSS_NEGATIVE=REPRODUCED");
        Console.WriteLine("P127_SIGNED_HUMAN_CONSENT_PROTECTED_DURABILITY=ABSENT");
        Console.WriteLine("P127_REAL_NATIVE_WINCRED_EFFECTS=ZERO");
        Console.WriteLine("P127_OLD_P96_EFFECT_RACE=OPEN");
        Console.WriteLine("P127_G2_G3_PRODUCTION_SUCCESSOR=NOT_IMPLEMENTED");
        Console.WriteLine("P127_C1_PRODUCTION_RELEASE=HOLD");
        return passed==25&&failed==0?0:1;
    }
}
