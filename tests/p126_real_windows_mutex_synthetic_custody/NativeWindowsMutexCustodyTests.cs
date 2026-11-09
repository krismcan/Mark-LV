// P126 real, unprivileged, Windows interprocess named-Mutex test driver.
// Only local integer markers; no service install, protected journal, WinCred,
// secrets, consent issuer, arbitrary effect callback or release eligibility.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P126 only within isolated synthetic native Windows test compilation
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P126NativeWindowsMutexTests
{
    private static int passed,failed;
    private static string Name()
    {return "Local\\Nayeon-C1-P126-"+Guid.NewGuid().ToString("N");}
    private static void Need(bool yes,string msg)
    {if(!yes)throw new InvalidOperationException("P126 "+msg);}
    private static void Run(string label,Action action)
    {
        try{action();passed++;Console.WriteLine("PASS "+label);}
        catch(Exception ex){failed++;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name+" "+ex.Message);}
    }
    private static void NoAuthority(WindowsG2SyntheticMutexCustody c)
    {
        Need(c!=null,"candidate exists");
        Need(!c.NativeCredentialEffectAllowed,"no real WinCred effect");
        Need(!c.ActualHumanConsentVerified,"no signed user presence");
        Need(!c.ProtectedDurableGrantIssued,"no one-use durable grant");
        Need(!c.ReleaseEligible,"production release still held");
        Need(!c.ToString().Contains("Local\\Nayeon-"),
            "no OS mutex name in status");
    }
    private static void Prepare(
        WindowsG2SyntheticMutexCustody c,
        LedgerOperation op,bool ack=false)
    {
        Need(c.PrepareSyntheticOnly(op,ack),"test-only prepare");
    }
    private static CustodyOutcome Fake(
        WindowsG2SyntheticMutexCustody c,LedgerOperation op,
        ManualResetEvent entered=null,ManualResetEvent release=null,
        bool unknown=false)
    {return c.AttemptFakeOnly(op,entered,release,unknown);}

    private static string Exe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}

    // Child is a REAL distinct unprivileged Windows process. The first
    // mode holds the named kernel mutex; the second ABANDONS it by exiting
    // while owning it. The third probes interprocess contention.
    private static int Child(string[] args)
    {
        try
        {
            if(args.Length!=3 || args[0]!="--p126-child" ||
                !args[2].StartsWith("Local\\Nayeon-C1-P126-",
                    StringComparison.Ordinal))return 20;
            string mode=args[1],name=args[2];
            using(var mutex=new Mutex(false,name))
            {
                if(mode=="probe")
                {
                    bool owned=false;
                    try
                    {
                        owned=mutex.WaitOne(250);
                        Console.WriteLine(owned?"P126_PROBE_ACQUIRED":"P126_PROBE_BUSY");
                        Console.Out.Flush();
                        return 0;
                    }
                    catch(AbandonedMutexException)
                    {
                        owned=true;
                        Console.WriteLine("P126_PROBE_ABANDONED");
                        Console.Out.Flush();
                        return 0;
                    }
                    finally
                    {if(owned)mutex.ReleaseMutex();}
                }
                if(mode!="hold" && mode!="abandon")return 21;
                if(!mutex.WaitOne(5000))return 22;
                Console.WriteLine("P126_MUTEX_HELD");
                Console.Out.Flush();
                if(mode=="abandon")
                {
                    // This is deliberately an unprivileged runner-only
                    // process exit. NO protected shared state is touched.
                    Environment.Exit(0);
                    return 0;
                }
                using(var signal=new EventWaitHandle(false,EventResetMode.ManualReset,
                    name+"-release"))
                {
                    if(!signal.WaitOne(5000))return 23;
                }
                mutex.ReleaseMutex();
                return 0;
            }
        }
        catch(Exception){return 24;}
    }

    private sealed class External : IDisposable
    {
        internal readonly Process Process;
        private readonly EventWaitHandle releaseSignal;
        internal External(Process p,EventWaitHandle signal)
        {Process=p;releaseSignal=signal;}
        public void Release()
        {
            if(Process.HasExited)return;
            Need(releaseSignal.Set(),
                "native Windows release event signalled");
            Need(Process.WaitForExit(5000),
                "external native owner did not exit after release event");
            Need(Process.ExitCode==0,
                "external native owner exit code="+Process.ExitCode);
        }
        public void Dispose()
        {
            if(!Process.HasExited)Process.Kill();
            Process.Dispose();
            releaseSignal.Dispose();
        }
    }
    private static External StartOwner(string mode,string name)
    {
        // Use a real named Windows event instead of redirected stdin,
        // since console input is not reliable for the child under CI.
        var releaseSignal=new EventWaitHandle(false,
            EventResetMode.ManualReset,name+"-release");
        var info=new ProcessStartInfo(Exe(),
            "--p126-child "+mode+" "+name);
        info.UseShellExecute=false;
        info.CreateNoWindow=true;
        info.RedirectStandardOutput=true;
        var process=Process.Start(info);
        Need(process!=null&&process.Id>0,"real OS child process launched");
        using(var me=Process.GetCurrentProcess())
            Need(me.Id!=process.Id,"different Windows OS PID");
        string ready=process.StandardOutput.ReadLine();
        Need(ready=="P126_MUTEX_HELD","child owns OS mutex");
        return new External(process,releaseSignal);
    }
    private static string Probe(string name)
    {
        var start=new ProcessStartInfo(Exe(),
            "--p126-child probe "+name);
        start.UseShellExecute=false;
        start.CreateNoWindow=true;
        start.RedirectStandardOutput=true;
        using(var p=Process.Start(start))
        {
            Need(p!=null&&p.Id>0,"probe OS child started");
            string answer=p.StandardOutput.ReadLine();
            Need(p.WaitForExit(4000) && p.ExitCode==0,
                "native probe child terminated");
            return answer;
        }
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p126-child")return Child(args);
            return 25;
        }

        Run("invalid-test-only-kernel-mutex-name-refused",()=>{
            bool rejected=false;
            try{new WindowsG2SyntheticMutexCustody("Global\\LiveCredentialMutex");}
            catch(ArgumentException){rejected=true;}
            Need(rejected,"no production Global name accepted");
        });
        Run("upper-case-test-mutex-name-rejected",()=>{
            bool rejected=false;
            try{new WindowsG2SyntheticMutexCustody(
                "Local\\Nayeon-C1-P126-"+new string('A',32));}
            catch(ArgumentException){rejected=true;}
            Need(rejected,"only canonical review name");
        });
        Run("short-test-mutex-name-rejected",()=>{
            bool rejected=false;
            try{new WindowsG2SyntheticMutexCustody(
                "Local\\Nayeon-C1-P126-1234");}
            catch(ArgumentException){rejected=true;}
            Need(rejected,"no shorter name");
        });
        Run("ordinary-fresh-unprivileged-OS-lease-no-approval",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {NoAuthority(c);Need(c.FakeEffectMarkers==0,"zero");}
        });
        Run("real-OS-mutex-single-fake-save-sticky-recovery",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Save);
                Need(Fake(c,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "fake must return recovery");
                Need(c.ReviewOsMutexAcquired && c.FakeEffectMarkers==1 &&
                    c.RecoveryRequired,"real OS lease and one integer");
                NoAuthority(c);
            }
        });
        Run("real-OS-mutex-single-fake-replace-sticky-recovery",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Replace);
                Need(Fake(c,LedgerOperation.Replace)==
                    CustodyOutcome.RecoveryRequired,"replace fake");
                Need(c.FakeEffectMarkers==1 && c.RecoveryRequired,"once only");
                NoAuthority(c);
            }
        });
        Run("real-OS-mutex-fake-delete-needs-acknowledgement",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Delete,false),
                    "unacknowledged delete refuses");
                Prepare(c,LedgerOperation.Delete,true);
                Need(Fake(c,LedgerOperation.Delete)==
                    CustodyOutcome.RecoveryRequired,"delete fake");
                Need(c.FakeEffectMarkers==1,"one fake marker");
                NoAuthority(c);
            }
        });
        Run("invalid-effect-shape-never-prepares",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Save,true),
                    "write with delete ack invalid");
                Need(!c.PrepareSyntheticOnly((LedgerOperation)900,false),
                    "unknown operation invalid");
                Need(c.FakeEffectMarkers==0,"no fake effect");
                NoAuthority(c);
            }
        });
        Run("wrong-operation-burns-test-only-attempt",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Save);
                Need(Fake(c,LedgerOperation.Replace)==CustodyOutcome.Denied,
                    "operation mismatch refused");
                Need(c.RecoveryRequired && c.FakeEffectMarkers==0,
                    "sticky unknown and zero marker");
                Need(Fake(c,LedgerOperation.Save)==CustodyOutcome.RecoveryRequired,
                    "cannot retry after mismatch");
                NoAuthority(c);
            }
        });
        Run("revocation-before-native-fake-attempt-zero-marker",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Save);c.Revoke();
                Need(Fake(c,LedgerOperation.Save)==CustodyOutcome.Denied,
                    "prior revocation wins");
                Need(c.FakeEffectMarkers==0,"no effect under revoke");
                NoAuthority(c);
            }
        });
        Run("stop-before-native-fake-attempt-zero-marker",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Save);c.Stop();
                Need(Fake(c,LedgerOperation.Save)==CustodyOutcome.Denied,
                    "prior stop wins");
                Need(c.FakeEffectMarkers==0,"no marker");
                NoAuthority(c);
            }
        });
        Run("fault-before-native-fake-attempt-zero-marker",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Save);c.MarkFault();
                Need(Fake(c,LedgerOperation.Save)==
                    CustodyOutcome.RecoveryRequired,"faulted host recovery");
                Need(c.FakeEffectMarkers==0,"no marker");
                NoAuthority(c);
            }
        });
        Run("exactly-one-synthetic-effect-attempt-no-replay",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Save);
                Fake(c,LedgerOperation.Save);
                Need(Fake(c,LedgerOperation.Save)==
                    CustodyOutcome.RecoveryRequired,"no fake retry");
                Need(!c.PrepareSyntheticOnly(LedgerOperation.Save,false),
                    "no rearm");
                Need(c.FakeEffectMarkers==1,"one marker");
                NoAuthority(c);
            }
        });
        Run("native-twelve-concurrent-fake-dispatchers-one-integer",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            using(var ready=new ManualResetEvent(false))
            {
                Prepare(c,LedgerOperation.Replace);
                int bad=0;
                var threads=new Thread[12];
                for(int i=0;i<threads.Length;i++)
                {
                    threads[i]=new Thread(()=>{
                        ready.WaitOne();
                        if(Fake(c,LedgerOperation.Replace)!=
                            CustodyOutcome.RecoveryRequired)
                            Interlocked.Increment(ref bad);
                    });
                    threads[i].Start();
                }
                ready.Set();
                foreach(var t in threads)
                    Need(t.Join(5000),"fake worker joined");
                Need(bad==0&&c.FakeEffectMarkers==1,
                    "single fake marker under process lock");
                NoAuthority(c);
            }
        });
        Run("revocation-during-OS-lease-is-too-late-not-cancelled",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            using(var entered=new ManualResetEvent(false))
            using(var release=new ManualResetEvent(false))
            {
                Prepare(c,LedgerOperation.Save);
                CustodyOutcome outcome=CustodyOutcome.Denied;
                var effect=new Thread(()=>{
                    outcome=Fake(c,LedgerOperation.Save,entered,release);
                });
                var revoke=new Thread(()=>c.Revoke());
                effect.Start();
                Need(entered.WaitOne(2000),"OS mutex + fake marker entered");
                revoke.Start();
                release.Set();
                Need(effect.Join(5000)&&revoke.Join(5000),"threads finished");
                Need(outcome==CustodyOutcome.RecoveryRequired &&
                    c.FakeEffectMarkers==1 && c.TooLateRevocations==1,
                    "late revoke cannot erase possible fake effect");
                NoAuthority(c);
            }
        });
        Run("real-other-OS-process-holds-mutex-fake-attempt-denied",()=>{
            string name=Name();
            using(var c=new WindowsG2SyntheticMutexCustody(name))
            using(var owner=StartOwner("hold",name))
            {
                Prepare(c,LedgerOperation.Save);
                Need(Fake(c,LedgerOperation.Save)==
                    CustodyOutcome.RecoveryRequired,
                    "kernel lease busy needs recovery, zero attempt");
                Need(c.FakeEffectMarkers==0&&!c.ReviewOsMutexAcquired &&
                    c.RecoveryRequired,"no fake effect under other OS owner");
                owner.Release();
                NoAuthority(c);
            }
        });
        Run("real-child-abandons-OS-mutex-sticky-recovery-no-effect",()=>{
            string name=Name();
            using(var c=new WindowsG2SyntheticMutexCustody(name))
            using(var owner=StartOwner("abandon",name))
            {
                Need(owner.Process.WaitForExit(4000)&&owner.Process.ExitCode==0,
                    "child exited without releasing OS lease");
                Prepare(c,LedgerOperation.Save);
                Need(Fake(c,LedgerOperation.Save)==
                    CustodyOutcome.RecoveryRequired,
                    "abandoned kernel lease cannot be admitted");
                Need(c.AbandonedAcquisitions==1&&
                    c.FakeEffectMarkers==0&&c.RecoveryRequired,
                    "zero synthetic effects on abandoned mutex");
                NoAuthority(c);
            }
        });
        Run("real-cross-process-observes-lease-while-fake-held",()=>{
            string name=Name();
            using(var c=new WindowsG2SyntheticMutexCustody(name))
            using(var entered=new ManualResetEvent(false))
            using(var release=new ManualResetEvent(false))
            {
                Prepare(c,LedgerOperation.Save);
                var effect=new Thread(()=>{
                    Fake(c,LedgerOperation.Save,entered,release);
                });
                effect.Start();
                Need(entered.WaitOne(2000),"real OS mutex acquired");
                string occupied=Probe(name);
                release.Set();
                Need(effect.Join(5000),"fake thread finished");
                string freed=Probe(name);
                Need(occupied=="P126_PROBE_BUSY"&&
                    freed=="P126_PROBE_ACQUIRED",
                    "other OS process blocked during lease and can access after");
                Need(c.FakeEffectMarkers==1 && c.RecoveryRequired,
                    "one sticky fake attempt");
                NoAuthority(c);
            }
        });
        Run("unknown-synthetic-effect-outcome-is-recovery-not-success",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Prepare(c,LedgerOperation.Delete,true);
                Need(Fake(c,LedgerOperation.Delete,null,null,true)==
                    CustodyOutcome.RecoveryRequired,"unknown outcome recovery");
                Need(c.FakeEffectMarkers==1&&c.UnknownResults>=1,
                    "one possible fake effect, no retry");
                NoAuthority(c);
            }
        });
        Run("original-service-effect-security-gates-remain-held",()=>{
            using(var c=new WindowsG2SyntheticMutexCustody(Name()))
            {
                Need(!ServiceGate.LiveEligible(),"P49 live service guard closed");
                Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled()&&
                    CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                    "P112 native effect and old adapter blocked");
                NoAuthority(c);
                Need(c.FakeEffectMarkers==0,"no native credential effect");
            }
        });

        Console.WriteLine("P126_ACTUAL_NATIVE_OS_MUTEX_CASES_PASSED="+passed);
        Console.WriteLine("P126_ACTUAL_NATIVE_OS_MUTEX_CASES_FAILED="+failed);
        Console.WriteLine("P126_PROCESS_SHARED_OS_CUSTODY_LEASE=REAL_WINDOWS_TEST_ONLY");
        Console.WriteLine("P126_ABANDONED_OWNER=STICKY_RECOVERY_ZERO_EFFECT");
        Console.WriteLine("P126_FAKE_EFFECT_IS_INTEGER_ONLY=TRUE");
        Console.WriteLine("P126_SYNTHETIC_COMMIT_REQUIRES_TWO_PREPROCESSOR_GUARDS=TRUE");
        Console.WriteLine("P126_SIGNED_HUMAN_CONSENT_DURABLE_GRANT=ABSENT");
        Console.WriteLine("P126_NATIVE_WINCRED_CALLS=ZERO");
        Console.WriteLine("P126_OLD_P96_RACE=OPEN");
        Console.WriteLine("P126_G2_REAL_DISPATCH_REPLACEMENT=NOT_IMPLEMENTED");
        Console.WriteLine("P126_C1_PRODUCTION_RELEASE=HOLD");
        return passed==20&&failed==0?0:1;
    }
}
