// P130 — genuine Windows unprivileged two-file witness audit tests.
// A journal + witness under one OS user's TEMP are NOT independent
// protected trust roots, despite SHA-256 checksums. No real credentials,
// WinCred, protected registry, signer, privileged service or installation.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P130 two-file witness native tests require isolated synthetic flags
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using Nayeon.ByokC1;

internal static class P130NativeUnprotectedWitnessTests
{
    private static int passed,failed;
    private static void Need(bool good,string why)
    {if(!good)throw new InvalidOperationException("P130 "+why);}
    private static void Run(string name,Action body)
    {
        try{body();passed++;Console.WriteLine("PASS "+name);}
        catch(Exception ex)
        {failed++;Console.WriteLine("FAIL "+name+" "+ex.GetType().Name+" "+ex.Message);}
    }
    private static string Id(){return Guid.NewGuid().ToString("N");}
    private static void WithReview(Action<WindowsG3UnprotectedWitnessReview> body)
    {
        var r=new WindowsG3UnprotectedWitnessReview(Id());
        try{body(r);}
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
    private static void Stage(WindowsG3UnprotectedWitnessReview r,int next)
    {
        Need(r.JournalForSyntheticTests.AppendSynthetic((G3ReviewStage)next),
            "synthetic nonsecret stage "+next+" appended");
    }
    private static void Until(WindowsG3UnprotectedWitnessReview r,int count)
    {for(int i=1;i<=count;i++)Stage(r,i);}
    private static void Snapshot(WindowsG3UnprotectedWitnessReview r)
    {
        Need(r.WriteUntrustedWitnessSnapshotForTest(),
            "nonsecret review witness snapshot written");
    }
    private static void NoAuthority(G3ReviewWitnessObservation o)
    {
        Need(o!=null,"review observation returned");
        Need(!o.IndependentProtectionProven&&
            !o.HistoricalEnrollmentVerified &&
            !o.AntiRollbackEstablished &&
            !o.SignedServiceAuthenticated &&
            !o.ProtectedJournalVerified &&
            !o.HumanConsentVerified &&
            !o.DurableOneUseGrantVerified &&
            !o.NativeCredentialEffectAllowed &&
            !o.ProductionAdmissionAllowed,
            "ordinary two-file history never becomes protected consent");
        Need(!o.ToString().Contains("nayeon-c1-p130"),
            "no file path exposed in status");
    }
    private static void Expect(
        WindowsG3UnprotectedWitnessReview r,
        G3ReviewWitnessState state,int journalCount,int witnessCount)
    {
        G3ReviewWitnessObservation o=r.CompareUntrustedFiles();
        Need(o.State==state &&
            o.JournalCount==journalCount &&
            o.WitnessCount==witnessCount,
            "review state "+o.State+" journal="+o.JournalCount+
            " witness="+o.WitnessCount);
        NoAuthority(o);
    }
    private static void Matched(WindowsG3UnprotectedWitnessReview r,int n)
    {
        Expect(r,G3ReviewWitnessState.ConsistentButUntrusted,n,n);
        Need(r.CompareUntrustedFiles().MatchedForDiagnosticOnly,
            "match is a diagnostic only");
    }
    private static string Exe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}

    private static int Child(string[] args)
    {
        try
        {
            if(args.Length!=3||args[0]!="--p130-child")
                return 11;
            var r=new WindowsG3UnprotectedWitnessReview(args[1]);
            if(args[2]=="write2")
            {
                Until(r,2);
                Snapshot(r);
            }
            else if(args[2]=="append3")
                Stage(r,3);
            else
                return 12;
            // Genuine OS child terminates after actual Flush(true) in
            // journal and witness. No in-memory state passed to parent.
            Environment.Exit(0);
            return 0;
        }
        catch(Exception){return 13;}
    }

    private static void RealChild(
        WindowsG3UnprotectedWitnessReview r,string mode)
    {
        string full=Path.GetFileNameWithoutExtension(
            r.JournalForSyntheticTests.IsolatedTestFilePath);
        const string prefix="nayeon-c1-p128-";
        Need(full.StartsWith(prefix,StringComparison.Ordinal),
            "only canonical disposable review file ID");
        string id=full.Substring(prefix.Length);
        var info=new ProcessStartInfo(Exe(),
            "--p130-child "+id+" "+mode);
        info.UseShellExecute=false;
        info.CreateNoWindow=true;
        using(var process=Process.Start(info))
        {
            Need(process!=null&&process.Id>0,"real Windows process exists");
            using(var me=Process.GetCurrentProcess())
                Need(me.Id!=process.Id,"genuinely different OS PID");
            Need(process.WaitForExit(5000) && process.ExitCode==0,
                "real OS child flushed and exited cleanly");
        }
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p130-child")return Child(args);
            return 14;
        }

        Run("short-test-identifier-cannot-select-arbitrary-path",()=>{
            bool rejected=false;
            try{new WindowsG3UnprotectedWitnessReview("123");}
            catch(ArgumentException){rejected=true;}
            Need(rejected,"no arbitrary Windows path");
        });
        Run("uppercase-test-identifier-rejected",()=>{
            bool rejected=false;
            try{new WindowsG3UnprotectedWitnessReview(new string('A',32));}
            catch(ArgumentException){rejected=true;}
            Need(rejected,"review filenames must be canonical");
        });
        Run("both-files-missing-denied",()=>WithReview(r=>
            Expect(r,G3ReviewWitnessState.BothMissingUnsafe,0,0)));

        Run("journal-without-separate-witness-denied",()=>WithReview(r=>{
            Until(r,1);
            Expect(r,G3ReviewWitnessState.JournalWithoutWitness,0,0);
        }));

        Run("orphan-witness-after-journal-deletion-denied",()=>WithReview(r=>{
            Until(r,1);Snapshot(r);
            File.Delete(r.JournalForSyntheticTests.IsolatedTestFilePath);
            Expect(r,G3ReviewWitnessState.WitnessWithoutJournal,0,0);
        }));

        Run("matching-one-stage-intent-is-only-diagnostic",()=>WithReview(r=>{
            Until(r,1);Snapshot(r);Matched(r,1);
        }));

        Run("matching-two-stage-possible-effect-is-only-diagnostic",()=>
            WithReview(r=>{Until(r,2);Snapshot(r);Matched(r,2);}));

        Run("matching-three-stage-terminal-is-only-diagnostic",()=>
            WithReview(r=>{Until(r,3);Snapshot(r);Matched(r,3);}));

        Run("rollback-just-the-journal-valid-prefix-detected",()=>WithReview(r=>{
            Until(r,1);
            byte[] old=File.ReadAllBytes(
                r.JournalForSyntheticTests.IsolatedTestFilePath);
            Stage(r,2);Stage(r,3);Snapshot(r);Matched(r,3);
            File.WriteAllBytes(
                r.JournalForSyntheticTests.IsolatedTestFilePath,old);
            Expect(r,G3ReviewWitnessState.HistoryMismatch,1,3);
        }));

        Run("append-new-journal-stage-without-witness-detected",()=>
            WithReview(r=>{
                Until(r,1);Snapshot(r);Stage(r,2);
                Expect(r,G3ReviewWitnessState.HistoryMismatch,2,1);
            }));

        Run("tampered-witness-hash-refused",()=>WithReview(r=>{
            Until(r,2);Snapshot(r);
            byte[] bytes=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
            bytes[7]^=0x01;
            File.WriteAllBytes(r.UntrustedWitnessPathForTests,bytes);
            Expect(r,G3ReviewWitnessState.WitnessMalformed,2,0);
        }));

        Run("truncated-witness-refused",()=>WithReview(r=>{
            Until(r,1);Snapshot(r);
            byte[] bytes=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
            Array.Resize(ref bytes,bytes.Length-3);
            File.WriteAllBytes(r.UntrustedWitnessPathForTests,bytes);
            Expect(r,G3ReviewWitnessState.WitnessMalformed,1,0);
        }));

        Run("witness-trailing-bytes-refused",()=>WithReview(r=>{
            Until(r,3);Snapshot(r);
            using(var stream=new FileStream(r.UntrustedWitnessPathForTests,
                FileMode.Append,FileAccess.Write))
                stream.WriteByte(0x7e);
            Expect(r,G3ReviewWitnessState.WitnessMalformed,3,0);
        }));

        Run("witness-stage-count-tamper-refused",()=>WithReview(r=>{
            Until(r,3);Snapshot(r);
            byte[] bytes=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
            bytes[5]=2;
            File.WriteAllBytes(r.UntrustedWitnessPathForTests,bytes);
            Expect(r,G3ReviewWitnessState.WitnessMalformed,3,0);
        }));

        Run("tampered-journal-digest-refused-even-with-witness",()=>
            WithReview(r=>{
                Until(r,2);Snapshot(r);
                byte[] bytes=File.ReadAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath);
                bytes[13]^=0x4e;
                File.WriteAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath,bytes);
                Expect(r,G3ReviewWitnessState.JournalMalformed,0,0);
            }));

        Run("journal-deletion-with-intact-witness-denied",()=>WithReview(r=>{
            Until(r,3);Snapshot(r);
            File.Delete(r.JournalForSyntheticTests.IsolatedTestFilePath);
            Expect(r,G3ReviewWitnessState.WitnessWithoutJournal,0,0);
        }));

        Run("witness-deletion-with-intact-journal-denied",()=>WithReview(r=>{
            Until(r,3);Snapshot(r);
            File.Delete(r.UntrustedWitnessPathForTests);
            Expect(r,G3ReviewWitnessState.JournalWithoutWitness,0,0);
        }));

        Run("test-witness-writer-does-not-downgrade-live-count",()=>
            WithReview(r=>{
                Until(r,1);
                byte[] old=File.ReadAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath);
                Stage(r,2);Stage(r,3);Snapshot(r);
                File.WriteAllBytes(
                    r.JournalForSyntheticTests.IsolatedTestFilePath,old);
                Need(!r.WriteUntrustedWitnessSnapshotForTest(),
                    "test writer cannot downgrade existing count");
                Expect(r,G3ReviewWitnessState.HistoryMismatch,1,3);
            }));

        Run("both-files-rolled-back-together-undetectable",()=>WithReview(r=>{
            Until(r,1);Snapshot(r);
            byte[] oldJournal=File.ReadAllBytes(
                r.JournalForSyntheticTests.IsolatedTestFilePath);
            byte[] oldWitness=File.ReadAllBytes(r.UntrustedWitnessPathForTests);
            Stage(r,2);Stage(r,3);Snapshot(r);Matched(r,3);
            // A same-user attacker can restore BOTH unprotected files.
            // The detector sees matching old history and CANNOT know
            // whether an irreversible effect occurred in the meantime.
            File.WriteAllBytes(
                r.JournalForSyntheticTests.IsolatedTestFilePath,oldJournal);
            File.WriteAllBytes(r.UntrustedWitnessPathForTests,oldWitness);
            Matched(r,1);
            Need(!r.CompareUntrustedFiles().AntiRollbackEstablished,
                "dual-file rollback negative does not pass G3");
        }));

        Run("genuine-other-Windows-process-writes-both-then-exits",()=>
            WithReview(r=>{
                RealChild(r,"write2");
                Matched(r,2);
            }));

        Run("genuine-other-process-advances-journal-without-witness",()=>
            WithReview(r=>{
                RealChild(r,"write2");
                Matched(r,2);
                RealChild(r,"append3");
                Expect(r,G3ReviewWitnessState.HistoryMismatch,3,2);
            }));

        Run("witness-deletion-allows-untrusted-reenrollment-negative",()=>
            WithReview(r=>{
                Until(r,3);Snapshot(r);Matched(r,3);
                File.Delete(r.UntrustedWitnessPathForTests);
                Expect(r,G3ReviewWitnessState.JournalWithoutWitness,0,0);
                // An ordinary writer can re-create the missing witness.
                // That is explicitly NOT secure enrollment.
                Snapshot(r);
                Matched(r,3);
                Need(!r.CompareUntrustedFiles().HistoricalEnrollmentVerified,
                    "recreated TEMP witness is NOT protected history");
            }));

        Run("present-but-empty-witness-file-is-corrupt",()=>WithReview(r=>{
            Until(r,2);
            File.WriteAllBytes(r.UntrustedWitnessPathForTests,new byte[0]);
            Expect(r,G3ReviewWitnessState.WitnessMalformed,2,0);
        }));

        Run("original-native-effect-admission-still-held",()=>WithReview(r=>{
            Until(r,3);Snapshot(r);
            Need(!ServiceGate.LiveEligible(),
                "frozen P49 live service remains held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled()&&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 real WinCred/old effect still disabled");
            Matched(r,3);
        }));

        Console.WriteLine("P130_NATIVE_DUAL_FILE_WITNESS_CASES_PASSED="+passed);
        Console.WriteLine("P130_NATIVE_DUAL_FILE_WITNESS_CASES_FAILED="+failed);
        Console.WriteLine("P130_ONE_FILE_JOURNAL_ROLLBACK=DETECTED_BY_UNTRUSTED_WITNESS");
        Console.WriteLine("P130_BOTH_FILES_SAME_USER_ROLLBACK=UNDETECTABLE");
        Console.WriteLine("P130_CROSS_PROCESS_FILE_HISTORY=GENUINE_WINDOWS_DIAGNOSTIC");
        Console.WriteLine("P130_INDEPENDENT_PROTECTED_ANCHOR=ABSENT");
        Console.WriteLine("P130_SIGNED_BROKER_HUMAN_CONSENT=ABSENT");
        Console.WriteLine("P130_REAL_NATIVE_WINCRED_EFFECT=NONE");
        Console.WriteLine("P130_ORIGINAL_P96_RACE=OPEN");
        Console.WriteLine("P130_C1_PRODUCTION_RELEASE=HOLD");
        return passed==24&&failed==0?0:1;
    }
}
