// P122 Windows-native unprivileged deadline/cancellation review tests.
// The standalone read primitive is not yet wired into P121; G1 HOLD.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P122 native test requires isolated review-only compilation
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;

internal static class P122AbsolutePipeDeadlineTests
{
    private static int passed,failed;
    private static void Need(bool ok,string why)
    {if(!ok)throw new InvalidOperationException("P122 "+why);}
    private static void Run(string name,Action test)
    {
        try{test();passed++;Console.WriteLine("PASS "+name);}
        catch(Exception ex){failed++;Console.WriteLine("FAIL "+name+" "+ex.GetType().Name);}
    }

    private static string PipeName()
    {return "nayeon-p122-read-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var id=WindowsIdentity.GetCurrent())
        {
            Need(id.User!=null&&!id.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"no LocalSystem");
            var security=new PipeSecurity();
            security.SetAccessRuleProtection(true,false);
            security.AddAccessRule(new PipeAccessRule(
                id.User,PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,security);
        }
    }
    private static void NoAuthority(OsPipeDeadlineReadObservation o)
    {
        Need(o!=null,"observation exists");
        Need(!o.RealSignedBrokerAuthenticated,"no signed consent broker");
        Need(!o.HumanConsentVerified,"no human intent");
        Need(!o.ProtectedDurableGrantIssued,"no one-use grant");
        Need(!o.NativeCredentialEffectAllowed,"no native WinCred");
        Need(!o.ToString().Contains(":\\"),"no file path in log");
        Need(!o.ToString().Contains("S-1-"),"no SID in log");
    }

    // All client activity below uses ephemeral localhost IPC in a
    // GitHub-hosted Windows runner. No service credentials or effects.
    private static void Client(string name,string mode)
    {
        using(var pipe=new NamedPipeClientStream(".",name,
            PipeDirection.InOut,PipeOptions.None,
            TokenImpersonationLevel.Impersonation))
        {
            pipe.Connect(5000);
            pipe.WriteByte(0x43);pipe.Flush();
            byte[] payload=new byte[32];
            for(int i=0;i<payload.Length;i++)payload[i]=(byte)(i+1);
            if(mode=="full")
            {
                pipe.Write(payload,0,32);pipe.Flush();
            }
            else if(mode=="split")
            {
                pipe.Write(payload,0,7);pipe.Flush();
                Thread.Sleep(20);
                pipe.Write(payload,7,25);pipe.Flush();
            }
            else if(mode=="short")
            {
                pipe.Write(payload,0,3);pipe.Flush();
            }
            else if(mode=="partial")
            {
                pipe.Write(payload,0,3);pipe.Flush();
                Thread.Sleep(650);
            }
            else if(mode=="slow")
            {
                for(int i=0;i<8;i++)
                {
                    try{pipe.Write(payload,i,1);pipe.Flush();}
                    catch(IOException){break;}
                    Thread.Sleep(95);
                }
            }
            else if(mode=="late")
            {
                Thread.Sleep(650);
                try{pipe.Write(payload,0,32);pipe.Flush();}
                catch(IOException){}
            }
            else if(mode=="silent")
                Thread.Sleep(650);
        }
    }

    private static OsPipeDeadlineReadObservation Exchange(
        string mode,int deadline,bool child=false)
    {
        string name=PipeName();
        using(var server=Server(name))
        {
            var waiting=server.BeginWaitForConnection(null,null);
            Thread clientThread=null;
            Process childProcess=null;
            Exception clientError=null;
            try
            {
                if(child)
                {
                    string exe=Path.GetFullPath(
                        Assembly.GetExecutingAssembly().Location);
                    var start=new ProcessStartInfo(exe,
                        "--p122-child "+name+" "+mode);
                    start.UseShellExecute=false;
                    start.CreateNoWindow=true;
                    childProcess=Process.Start(start);
                    Need(childProcess!=null && childProcess.Id>0,
                        "OS child process exists");
                    using(var current=Process.GetCurrentProcess())
                        Need(childProcess.Id!=current.Id,
                            "genuine distinct OS process");
                }
                else
                {
                    clientThread=new Thread(()=>{
                        try{Client(name,mode);}
                        catch(IOException){} // expected on server timeout disposal
                        catch(ObjectDisposedException){}
                        catch(Exception ex){clientError=ex;}
                    });
                    clientThread.IsBackground=true;
                    clientThread.Start();
                }

                Need(waiting.AsyncWaitHandle.WaitOne(5000),"connected");
                server.EndWaitForConnection(waiting);
                Need(server.ReadByte()==0x43,"OS client handshake");
                var result=WindowsReviewOnlyAbsolutePipeDeadline.
                    ReadExactFrame(server,new byte[32],deadline);

                if(clientThread!=null)
                {
                    Need(clientThread.Join(4000),"test client ended");
                    Need(clientError==null,"unprivileged test client clean");
                }
                if(childProcess!=null)
                    Need(childProcess.WaitForExit(4000) &&
                        childProcess.ExitCode==0,"native test child clean");
                return result;
            }
            finally
            {
                if(childProcess!=null)
                {
                    if(!childProcess.HasExited)childProcess.Kill();
                    childProcess.Dispose();
                }
                waiting.AsyncWaitHandle.Close();
            }
        }
    }

    private static void MustTimeoutAndDrain(string mode,int ms)
    {
        var clock=Stopwatch.StartNew();
        var result=Exchange(mode,ms);
        clock.Stop();
        Need(result.State==
            OsPipeDeadlineReadState.DeadlineExpiredAndDrained,
            "actual Windows cancelled read must report completed drain");
        Need(result.CancelIoExAttempted,
            "native CancelIoEx requested on timeout");
        Need(result.EndReadCompletionObserved,
            "EndRead completion observed after cancel");
        Need(result.HandleQuarantinedOnFailure,
            "failed pipe permanently quarantined");
        Need(!result.ExactReviewFrameObserved,
            "no late native response can be admitted");
        Need(clock.ElapsedMilliseconds<4500,"bounded test operation");
        NoAuthority(result);
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length==3&&args[0]=="--p122-child")
        {
            try
            {
                if(!args[1].StartsWith("nayeon-p122-read-",
                    StringComparison.Ordinal))return 12;
                Client(args[1],args[2]);
                return 0;
            }
            catch(Exception){return 13;}
        }

        Run("null-pipe-unavailable",()=>{
            var r=WindowsReviewOnlyAbsolutePipeDeadline.
                ReadExactFrame(null,new byte[32],250);
            Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                "null rejected");NoAuthority(r);
        });
        Run("null-output-unavailable",()=>{
            var r=WindowsReviewOnlyAbsolutePipeDeadline.
                ReadExactFrame(null,null,250);
            Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                "null buffer rejected");NoAuthority(r);
        });
        Run("underlength-frame-guard",()=>{
            using(var p=Server(PipeName()))
            {
                var r=WindowsReviewOnlyAbsolutePipeDeadline.
                    ReadExactFrame(p,new byte[31],250);
                Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                    "undersize rejected");NoAuthority(r);
            }
        });
        Run("oversize-frame-guard",()=>{
            using(var p=Server(PipeName()))
            {
                var r=WindowsReviewOnlyAbsolutePipeDeadline.
                    ReadExactFrame(p,new byte[33],250);
                Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                    "oversize rejected");NoAuthority(r);
            }
        });
        Run("zero-deadline-guard",()=>{
            using(var p=Server(PipeName()))
            {
                var r=WindowsReviewOnlyAbsolutePipeDeadline.
                    ReadExactFrame(p,new byte[32],0);
                Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                    "zero denied");NoAuthority(r);
            }
        });
        Run("overlong-deadline-guard",()=>{
            using(var p=Server(PipeName()))
            {
                var r=WindowsReviewOnlyAbsolutePipeDeadline.
                    ReadExactFrame(p,new byte[32],2001);
                Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                    "deadline > 2 seconds denied");NoAuthority(r);
            }
        });
        Run("unconnected-native-pipe-refused",()=>{
            using(var p=Server(PipeName()))
            {
                var r=WindowsReviewOnlyAbsolutePipeDeadline.
                    ReadExactFrame(p,new byte[32],250);
                Need(r.State==OsPipeDeadlineReadState.InvalidOrUnavailable,
                    "not connected");NoAuthority(r);
            }
        });
        Run("actual-native-complete-32-byte-response",()=>{
            var r=Exchange("full",500);
            Need(r.State==OsPipeDeadlineReadState.ExactFrameObserved &&
                r.ActualReceivedBytes==32 && !r.CancelIoExAttempted,
                "complete read");NoAuthority(r);
        });
        Run("actual-native-split-7-plus-25-byte-response",()=>{
            var r=Exchange("split",600);
            Need(r.State==OsPipeDeadlineReadState.ExactFrameObserved &&
                r.ActualReceivedBytes==32,"partial completed");
            NoAuthority(r);
        });
        Run("native-short-frame-truncated-not-accepted",()=>{
            var r=Exchange("short",300);
            Need(r.State==OsPipeDeadlineReadState.ClosedOrTruncated &&
                !r.ExactReviewFrameObserved,"3 bytes not 32");
            NoAuthority(r);
        });
        Run("native-silent-client-CancelIoEx-drained",()=>{
            MustTimeoutAndDrain("silent",180);
        });
        Run("native-partial-then-stall-CancelIoEx-drained",()=>{
            MustTimeoutAndDrain("partial",180);
        });
        Run("native-slowloris-absolute-deadline-not-reset",()=>{
            MustTimeoutAndDrain("slow",230);
        });
        Run("native-late-32-byte-reply-not-resurrected",()=>{
            MustTimeoutAndDrain("late",180);
        });
        Run("native-child-process-complete-frame",()=>{
            var r=Exchange("full",550,true);
            Need(r.State==OsPipeDeadlineReadState.ExactFrameObserved &&
                !r.NativeCredentialEffectAllowed,
                "real separate OS child test");
            NoAuthority(r);
        });
        Run("original-native-credential-service-remains-held",()=>{
            var r=Exchange("full",550);
            Need(r.ExactReviewFrameObserved,"diagnostic only");
            Need(!ServiceGate.LiveEligible(),"P49 real service disabled");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 no actual effect");
            NoAuthority(r);
        });

        Console.WriteLine("P122_REAL_WINDOWS_DEADLINE_CASES_PASSED="+passed);
        Console.WriteLine("P122_REAL_WINDOWS_DEADLINE_CASES_FAILED="+failed);
        Console.WriteLine("P122_ABSOLUTE_MONOTONIC_FRAME_BUDGET=TESTED");
        Console.WriteLine("P122_WIN32_CANCELIOEX_ENDREAD_DRAIN=TESTED");
        Console.WriteLine("P122_STANDALONE_PRIMITIVE_NOT_WIRED_TO_P121=TRUE");
        Console.WriteLine("P122_TRUSTED_SIGNED_USER_CONSENT=ABSENT");
        Console.WriteLine("P122_DURABLE_GRANT_WINCRED_EFFECT=NONE");
        Console.WriteLine("P122_P96_ORIGINAL_RACE=OPEN");
        Console.WriteLine("P122_C1_PRODUCTION_RELEASE=HOLD");
        return passed==16 && failed==0?0:1;
    }
}
