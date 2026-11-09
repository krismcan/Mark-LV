// P129 — actual unprivileged Windows Process.Kill during disposable
// NONSECRET ephemeral file states. This is NOT a native WinCred crash,
// protected journal, reliable power-cut simulation, or consent authority.
// Requires P128 review writer and BOTH isolated+synthetic flags.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P129 forced-process-death driver must not compile in production
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P129NativeAbruptDeathTests
{
    private static int passed,failed;
    private static readonly string Prefix="nayeon-c1-p128-";
    private static void Need(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("P129 "+why);}
    private static void Run(string label,Action test)
    {
        try{test();passed++;Console.WriteLine("PASS "+label);}
        catch(Exception ex)
        {failed++;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name+" "+ex.Message);}
    }
    private static string Id(WindowsG3EphemeralReviewJournal j)
    {
        string name=Path.GetFileNameWithoutExtension(
            j.IsolatedTestFilePath);
        Need(name.StartsWith(Prefix,StringComparison.Ordinal),
            "random review-only filename");
        return name.Substring(Prefix.Length);
    }
    private static WindowsG3EphemeralReviewJournal New()
    {return new WindowsG3EphemeralReviewJournal(Guid.NewGuid().ToString("N"));}
    private static void WithJournal(Action<WindowsG3EphemeralReviewJournal> act)
    {
        var j=New();
        try{act(j);}
        finally
        {
            try{File.Delete(j.IsolatedTestFilePath);}
            catch(IOException){}
            catch(UnauthorizedAccessException){}
        }
    }
    private static void NoAuthority(G3ReviewObservation o)
    {
        Need(o!=null && !o.SignedServiceAuthenticated &&
            !o.ProtectedJournalVerified &&
            !o.IndependentlyAnchoredHistoryVerified &&
            !o.AntiRollbackVerified &&
            !o.DurableOneUseConsentVerified &&
            !o.NativeWinCredEffectAllowed &&
            !o.ProductionAdmissionAllowed,
            "no recovered diagnostic can become credential authority");
    }
    private static void Expect(WindowsG3EphemeralReviewJournal j,
        G3ReviewRecovery state,int rows,bool structural)
    {
        var o=j.InspectUntrusted();
        Need(o.Recovery==state &&
            o.RecordCount==rows &&
            o.SequenceStructurallyValid==structural,
            "actual OS postdeath file classification "+o.Recovery);
        NoAuthority(o);
    }

    // Child does not handle a kill or execute any production API. It
    // writes only synthetic bytes to an isolated OS TEMP file, flushes,
    // then holds the process alive. Parent uses REAL Process.Kill and
    // WaitForExit, rather than merely calling Environment.Exit.
    private static int Child(string[] args)
    {
        try
        {
            if(args.Length!=3||args[0]!="--p129-child")return 21;
            var journal=new WindowsG3EphemeralReviewJournal(args[1]);
            string mode=args[2],path=journal.IsolatedTestFilePath;
            FileStream held=null;
            try
            {
                if(mode=="empty"||mode=="partial7"||
                    mode=="partial41"||mode=="full42invalid")
                {
                    held=new FileStream(path,FileMode.Create,
                        FileAccess.Write,FileShare.None,4096,
                        FileOptions.WriteThrough);
                    int bytes=mode=="empty"?0:mode=="partial7"?7:
                        mode=="partial41"?41:42;
                    byte[] invalid=new byte[bytes];
                    for(int i=0;i<bytes;i++)invalid[i]=(byte)(i+1);
                    if(bytes>0)held.Write(invalid,0,bytes);
                    held.Flush(true);
                }
                else if(mode=="intent" || mode=="attempt"||
                    mode=="terminal"||mode=="exclusive"||
                    mode=="intent-trailing"||mode=="attempt-trailing")
                {
                    int stages=mode=="intent"?1:
                        (mode=="attempt"||mode=="attempt-trailing")?2:
                        (mode=="terminal")?3:1;
                    for(int n=1;n<=stages;n++)
                        if(!journal.AppendSynthetic((G3ReviewStage)n))
                            return 22;
                    if(mode=="exclusive")
                    {
                        // Observe real OS release of a still-open
                        // FileShare.None HANDLE after process kill.
                        held=new FileStream(path,FileMode.Open,
                            FileAccess.Read,FileShare.None);
                    }
                    if(mode.EndsWith("-trailing",StringComparison.Ordinal))
                    {
                        held=new FileStream(path,FileMode.Append,
                            FileAccess.Write,FileShare.None,4096,
                            FileOptions.WriteThrough);
                        byte[] suffix=new byte[]{9,8,7};
                        held.Write(suffix,0,suffix.Length);
                        held.Flush(true);
                    }
                }
                else return 23;

                Console.WriteLine("P129_KILL_READY");
                Console.Out.Flush();
                Thread.Sleep(12000);
                return 24; // unexpected lack of parent kill
            }
            finally
            {if(held!=null)held.Dispose();}
        }
        catch(Exception){return 25;}
    }

    private static void KillRealChild(
        WindowsG3EphemeralReviewJournal journal,string mode)
    {
        string exe=Path.GetFullPath(
            Assembly.GetExecutingAssembly().Location);
        var info=new ProcessStartInfo(exe,
            "--p129-child "+Id(journal)+" "+mode);
        info.UseShellExecute=false;
        info.CreateNoWindow=true;
        info.RedirectStandardOutput=true;
        using(var child=Process.Start(info))
        {
            Need(child!=null&&child.Id>0,"real native Windows child");
            using(var self=Process.GetCurrentProcess())
                Need(child.Id!=self.Id,"different true OS process ID");
            Need(child.StandardOutput.ReadLine()=="P129_KILL_READY",
                "child flushed nonsecret data and is still live");
            Need(!child.HasExited,"must kill a running OS process");
            child.Kill();
            Need(child.WaitForExit(5000),
                "Windows kernel confirmed process termination");
            Need(child.HasExited,"forced death completed before recovery");
        }
    }
    private static void Killed(
        string mode,G3ReviewRecovery recovery,int count,bool valid)
    {
        WithJournal(j=>{
            KillRealChild(j,mode);
            Expect(j,recovery,count,valid);
        });
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p129-child")return Child(args);
            return 27;
        }

        Run("missing-file-before-any-kill-is-never-authority",()=>
            WithJournal(j=>Expect(j,
                G3ReviewRecovery.MissingOrEmptyUnsafe,0,false)));

        Run("kill-live-Windows-writer-after-empty-file",()=>
            Killed("empty",G3ReviewRecovery.MissingOrEmptyUnsafe,0,false));

        Run("kill-live-Windows-writer-with-seven-invalid-bytes",()=>
            Killed("partial7",G3ReviewRecovery.CorruptOrUntrusted,0,false));

        Run("kill-live-Windows-writer-with-fortyone-byte-torn-frame",()=>
            Killed("partial41",G3ReviewRecovery.CorruptOrUntrusted,0,false));

        Run("kill-live-Windows-writer-with-invalid-full-frame",()=>
            Killed("full42invalid",G3ReviewRecovery.CorruptOrUntrusted,0,false));

        Run("kill-after-flushed-intent-only-never-retries",()=>
            Killed("intent",G3ReviewRecovery.IntentOnlyRecoveryRequired,1,true));

        Run("kill-after-flushed-possible-attempt-never-retries",()=>
            Killed("attempt",G3ReviewRecovery.PossiblyAttemptedRecoveryRequired,
                2,true));

        Run("kill-after-flushed-terminal-still-not-protected",()=>
            Killed("terminal",G3ReviewRecovery.TerminalDiagnosticOnly,3,true));

        Run("kill-original-holder-releases-exclusive-Windows-file-handle",()=>
            Killed("exclusive",G3ReviewRecovery.IntentOnlyRecoveryRequired,
                1,true));

        Run("kill-after-intent-plus-trailing-torn-record-refuses",()=>
            Killed("intent-trailing",
                G3ReviewRecovery.CorruptOrUntrusted,0,false));

        Run("kill-after-attempt-plus-trailing-torn-record-refuses",()=>
            Killed("attempt-trailing",
                G3ReviewRecovery.CorruptOrUntrusted,0,false));

        Run("four-real-process-deaths-have-no-positive-recovery",()=>
        {
            Killed("partial7",G3ReviewRecovery.CorruptOrUntrusted,0,false);
            Killed("intent",G3ReviewRecovery.IntentOnlyRecoveryRequired,
                1,true);
            Killed("attempt",
                G3ReviewRecovery.PossiblyAttemptedRecoveryRequired,2,true);
            Killed("terminal",
                G3ReviewRecovery.TerminalDiagnosticOnly,3,true);
        });

        Run("old-native-P49-P112-effect-gates-remain-closed",()=>
        {
            Need(!ServiceGate.LiveEligible(),"P49 live service gate held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 actual native WinCred paths still disabled");
            Killed("attempt",
                G3ReviewRecovery.PossiblyAttemptedRecoveryRequired,2,true);
        });

        Run("post-kill-no-state-can-claim-independent-anchor",()=>
        {
            WithJournal(j=>{
                KillRealChild(j,"terminal");
                var o=j.InspectUntrusted();
                Need(o.SequenceStructurallyValid &&
                    o.Recovery==G3ReviewRecovery.TerminalDiagnosticOnly &&
                    !o.AntiRollbackVerified &&
                    !o.IndependentlyAnchoredHistoryVerified,
                    "flushed 3-record diagnostic is not trusted history");
                NoAuthority(o);
            });
        });

        Console.WriteLine("P129_REAL_WINDOWS_FORCED_DEATH_CASES_PASSED="+passed);
        Console.WriteLine("P129_REAL_WINDOWS_FORCED_DEATH_CASES_FAILED="+failed);
        Console.WriteLine("P129_PROCESS_KILL_WAIT_FOREXIT=GENUINE_WINDOWS");
        Console.WriteLine("P129_MID_FRAME_AND_STAGED_WRITE=FAIL_CLOSED_DIAGNOSTIC");
        Console.WriteLine("P129_OS_FILE_HANDLE_RELEASE_AFTER_DEATH=TESTED");
        Console.WriteLine("P129_PROTECTED_JOURNAL_HKLM_ANTIROLLBACK=ABSENT");
        Console.WriteLine("P129_SIGNED_BROKER_HUMAN_WINCRED=ABSENT");
        Console.WriteLine("P129_P96_ORIGINAL_RACE=OPEN");
        Console.WriteLine("P129_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14&&failed==0?0:1;
    }
}
