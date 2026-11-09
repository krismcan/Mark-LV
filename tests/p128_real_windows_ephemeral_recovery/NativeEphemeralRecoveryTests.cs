// P128: genuine unprivileged hosted-Windows file/restart recovery tests.
// No real key, protected journal/registry, WinCred, consent, installer or
// privileged service. All files are synthetic under runner-local TEMP.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P128 native journal driver requires isolated synthetic test guards
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using Nayeon.ByokC1;

internal static class P128WindowsEphemeralJournalTests
{
    private static int passed,failed;
    private static void Need(bool condition,string reason)
    {if(!condition)throw new InvalidOperationException("P128 "+reason);}
    private static void Run(string label,Action action)
    {
        try{action();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception ex)
        {++failed;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name+" "+ex.Message);}
    }
    private static string NewId(){return Guid.NewGuid().ToString("N");}
    private static WindowsG3EphemeralReviewJournal New()
    {return new WindowsG3EphemeralReviewJournal(NewId());}
    private static void WithFile(Action<WindowsG3EphemeralReviewJournal> action)
    {
        var journal=New();
        try{action(journal);}
        finally
        {
            try{File.Delete(journal.IsolatedTestFilePath);}
            catch(IOException){}
            catch(UnauthorizedAccessException){}
        }
    }
    private static void NoAuthority(G3ReviewObservation o)
    {
        Need(o!=null,"observation not null");
        Need(!o.SignedServiceAuthenticated,
            "not signed/protected service");
        Need(!o.ProtectedJournalVerified,"unprotected TEMP file");
        Need(!o.IndependentlyAnchoredHistoryVerified,
            "no separate historical anchor");
        Need(!o.AntiRollbackVerified,
            "hash chain is NOT an antirollback trust root");
        Need(!o.DurableOneUseConsentVerified,"no human consent");
        Need(!o.NativeWinCredEffectAllowed,"no credential effect");
        Need(!o.ProductionAdmissionAllowed,"no production admission");
        Need(!o.ToString().Contains("nayeon-c1-p128"),
            "path not included in status");
    }
    private static void Stage(WindowsG3EphemeralReviewJournal j,int through)
    {
        for(int n=1;n<=through;n++)
            Need(j.AppendSynthetic((G3ReviewStage)n),
                "synthetic stage "+n+" append+Flush(true)");
    }
    private static void Observe(
        WindowsG3EphemeralReviewJournal j,
        G3ReviewRecovery expected,int count,bool valid)
    {
        var o=j.InspectUntrusted();
        Need(o.Recovery==expected&&o.RecordCount==count&&
            o.SequenceStructurallyValid==valid,
            "review recovery state "+o.Recovery+" records="+o.RecordCount);
        NoAuthority(o);
    }
    private static string Exe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}
    private static int Child(string[] args)
    {
        try
        {
            if(args.Length!=3||args[0]!="--p128-child")return 12;
            string id=args[1];
            int stages=Int32.Parse(args[2]);
            if(stages<1||stages>3)return 13;
            var j=new WindowsG3EphemeralReviewJournal(id);
            Stage(j,stages);
            // Every stage was explicitly Flush(true)'d and disposed.
            // Exit without handing in-memory state to the parent. This
            // is NOT a simulated power failure during Flush(true).
            Environment.Exit(0);
            return 0;
        }
        catch(Exception){return 14;}
    }
    private static void RealChild(WindowsG3EphemeralReviewJournal j,int stages)
    {
        string name=Path.GetFileNameWithoutExtension(
            j.IsolatedTestFilePath);
        const string prefix="nayeon-c1-p128-";
        Need(name.StartsWith(prefix,StringComparison.Ordinal),
            "only nonsecret runner-local ID");
        string id=name.Substring(prefix.Length);
        var info=new ProcessStartInfo(Exe(),
            "--p128-child "+id+" "+stages);
        info.UseShellExecute=false;info.CreateNoWindow=true;
        using(var process=Process.Start(info))
        {
            Need(process!=null&&process.Id>0,"child Windows process");
            using(var self=Process.GetCurrentProcess())
                Need(process.Id!=self.Id,
                    "different genuine Windows process");
            Need(process.WaitForExit(5000),"child exit observed");
            Need(process.ExitCode==0,"child flushed and exited cleanly");
        }
    }
    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p128-child")return Child(args);
            return 15;
        }
        Run("test-file-ID-short-rejected",()=>{
            bool refused=false;
            try{new WindowsG3EphemeralReviewJournal("123");}
            catch(ArgumentException){refused=true;}
            Need(refused,"no arbitrary filename");
        });
        Run("test-file-ID-uppercase-rejected",()=>{
            bool refused=false;
            try{new WindowsG3EphemeralReviewJournal(new string('A',32));}
            catch(ArgumentException){refused=true;}
            Need(refused,"strict lowercase");
        });
        Run("path-separator-and-nonhex-rejected",()=>{
            bool refused=false;
            try{new WindowsG3EphemeralReviewJournal(
                "1234567890abcdef1234567890abcde/");}
            catch(ArgumentException){refused=true;}
            Need(refused,"no arbitrary path");
        });
        Run("missing-history-fails-closed",()=>
            WithFile(j=>Observe(j,
                G3ReviewRecovery.MissingOrEmptyUnsafe,0,false)));
        Run("empty-file-fails-closed",()=>
            WithFile(j=>{
                File.WriteAllBytes(j.IsolatedTestFilePath,new byte[0]);
                Observe(j,G3ReviewRecovery.MissingOrEmptyUnsafe,0,false);
            }));
        Run("intent-only-on-disk-classified-for-recovery",()=>
            WithFile(j=>{
                Stage(j,1);
                Observe(j,G3ReviewRecovery.IntentOnlyRecoveryRequired,1,true);
            }));
        Run("intent-plus-fake-attempt-still-recovery",()=>
            WithFile(j=>{
                Stage(j,2);
                Observe(j,G3ReviewRecovery.PossiblyAttemptedRecoveryRequired,
                    2,true);
            }));
        Run("all-three-file-markers-not-security-authority",()=>
            WithFile(j=>{
                Stage(j,3);
                Observe(j,G3ReviewRecovery.TerminalDiagnosticOnly,3,true);
            }));
        Run("cannot-skip-intent-and-write-terminal",()=>
            WithFile(j=>{
                Need(!j.AppendSynthetic(G3ReviewStage.TerminalDiagnostic),
                    "must start with intent");
                Observe(j,G3ReviewRecovery.MissingOrEmptyUnsafe,0,false);
            }));
        Run("cannot-append-terminal-before-fake-attempt",()=>
            WithFile(j=>{
                Stage(j,1);
                Need(!j.AppendSynthetic(G3ReviewStage.TerminalDiagnostic),
                    "terminal requires attempt");
                Observe(j,G3ReviewRecovery.IntentOnlyRecoveryRequired,1,true);
            }));
        Run("cannot-replay-intent-on-same-file",()=>
            WithFile(j=>{
                Stage(j,1);
                Need(!j.AppendSynthetic(G3ReviewStage.Intent),
                    "no duplicate intent");
                Observe(j,G3ReviewRecovery.IntentOnlyRecoveryRequired,1,true);
            }));
        Run("cannot-append-after-terminal",()=>
            WithFile(j=>{
                Stage(j,3);
                Need(!j.AppendSynthetic(G3ReviewStage.TerminalDiagnostic),
                    "cannot add 4th record");
                Observe(j,G3ReviewRecovery.TerminalDiagnosticOnly,3,true);
            }));
        Run("flipped-record-digest-is-invalid",()=>
            WithFile(j=>{
                Stage(j,2);
                byte[] raw=File.ReadAllBytes(j.IsolatedTestFilePath);
                raw[20]^=0x55;
                File.WriteAllBytes(j.IsolatedTestFilePath,raw);
                Observe(j,G3ReviewRecovery.CorruptOrUntrusted,0,false);
                Need(!j.AppendSynthetic(G3ReviewStage.TerminalDiagnostic),
                    "do not extend corrupt ledger");
            }));
        Run("truncated-mid-frame-refuses",()=>
            WithFile(j=>{
                Stage(j,2);
                byte[] raw=File.ReadAllBytes(j.IsolatedTestFilePath);
                Array.Resize(ref raw,raw.Length-8);
                File.WriteAllBytes(j.IsolatedTestFilePath,raw);
                Observe(j,G3ReviewRecovery.CorruptOrUntrusted,0,false);
            }));
        Run("sequence-counter-tamper-refuses",()=>
            WithFile(j=>{
                Stage(j,3);
                byte[] raw=File.ReadAllBytes(j.IsolatedTestFilePath);
                raw[6]^=0x01;
                File.WriteAllBytes(j.IsolatedTestFilePath,raw);
                Observe(j,G3ReviewRecovery.CorruptOrUntrusted,0,false);
            }));
        Run("trailing-junk-refuses",()=>
            WithFile(j=>{
                Stage(j,3);
                using(var file=new FileStream(j.IsolatedTestFilePath,
                    FileMode.Append,FileAccess.Write))
                    file.WriteByte(0x70);
                Observe(j,G3ReviewRecovery.CorruptOrUntrusted,0,false);
            }));
        Run("genuine-Windows-child-flushes-intent-then-exits",()=>
            WithFile(j=>{
                RealChild(j,1);
                Observe(j,G3ReviewRecovery.IntentOnlyRecoveryRequired,1,true);
            }));
        Run("genuine-Windows-child-flushes-attempt-then-exits",()=>
            WithFile(j=>{
                RealChild(j,2);
                Observe(j,G3ReviewRecovery.PossiblyAttemptedRecoveryRequired,
                    2,true);
            }));
        Run("genuine-Windows-child-flushes-terminal-then-exits",()=>
            WithFile(j=>{
                RealChild(j,3);
                Observe(j,G3ReviewRecovery.TerminalDiagnosticOnly,3,true);
            }));
        Run("prior-valid-file-rollback-undetectable-without-anchor",()=>
            WithFile(j=>{
                Stage(j,1);
                byte[] prior=File.ReadAllBytes(j.IsolatedTestFilePath);
                Stage(j,3);
                Observe(j,G3ReviewRecovery.TerminalDiagnosticOnly,3,true);
                // Same-user TEST rollback can restore an old, correctly
                // hashed prefix. This is a NEGATIVE G3 finding.
                File.WriteAllBytes(j.IsolatedTestFilePath,prior);
                var stale=j.InspectUntrusted();
                Need(stale.SequenceStructurallyValid&&
                    stale.Recovery==
                        G3ReviewRecovery.IntentOnlyRecoveryRequired,
                    "untrusted chain cannot identify rollback");
                NoAuthority(stale);
            }));
        Console.WriteLine("P128_EPHEMERAL_NATIVE_JOURNAL_CASES_PASSED="+passed);
        Console.WriteLine("P128_EPHEMERAL_NATIVE_JOURNAL_CASES_FAILED="+failed);
        Console.WriteLine("P128_REAL_WINDOWS_CROSS_PROCESS_FLUSH_AND_EXIT=TESTED");
        Console.WriteLine("P128_TRUNCATION_CORRUPTION=FAIL_CLOSED");
        Console.WriteLine("P128_ROLLBACK_OLD_VALID_PREFIX=UNDETECTABLE_WITHOUT_PROTECTED_ANCHOR");
        Console.WriteLine("P128_PROTECTED_FILE_HKLM_OR_DURABLE_GRANT=ABSENT");
        Console.WriteLine("P128_SIGNED_HUMAN_CONSENT_REAL_WINCRED=ABSENT");
        Console.WriteLine("P128_P96_OLD_RACE=OPEN");
        Console.WriteLine("P128_C1_PRODUCTION_RELEASE=HOLD");
        return passed==20&&failed==0?0:1;
    }
}
