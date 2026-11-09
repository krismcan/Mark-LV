// P123 — actual Windows IPC P121+P122 integration test, isolated only.
// No signed consent, human approval, grant or native credential effect.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P123 integration test only in unprivileged review assembly
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

internal static class P123IntegratedPipeDeadlineTests
{
    private static int passed,failed;
    private static void Need(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("P123 "+why);}
    private static void Run(string label,Action act)
    {
        try{act();passed++;Console.WriteLine("PASS "+label);}
        catch(Exception ex){failed++;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name);}
    }
    private static ServiceBoundRequestIdentity Request()
    {
        return new ServiceBoundRequestIdentity(
            LedgerOperation.Save,
            new string('b',32),new string('c',32),new string('d',64),
            DateTime.UtcNow.Ticks+TimeSpan.TicksPerSecond*35,false);
    }
    private static void NoAuthority(OsReviewOnlyExchangeObservation o)
    {
        Need(o!=null,"result available");
        Need(!o.ActualSignedInstalledBrokerAuthenticated,
            "signed UI not authenticated");
        Need(!o.TrueHumanConsentVerified,"no human intent");
        Need(!o.DurableOneUseGrantIssued,"no protected grant");
        Need(!o.PrivilegedServiceListenerInstalled,"no privileged service");
        Need(!o.NativeCredentialEffectAllowed,"no real WinCred");
        Need(!o.ToString().Contains("S-1-"),"no account SID in status");
    }
    private static string PipeName()
    {return "nayeon-p123-hardened-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var identity=WindowsIdentity.GetCurrent())
        {
            Need(identity.User!=null &&
                !identity.User.IsWellKnown(
                    WellKnownSidType.LocalSystemSid),"no system privileges");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(identity.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(
                name,PipeDirection.InOut,1,PipeTransmissionMode.Byte,
                PipeOptions.Asynchronous,1024,1024,acl);
        }
    }
    private static void ReadExact(Stream stream,byte[] buffer)
    {
        int n=0;
        while(n<buffer.Length)
        {
            int count=stream.Read(buffer,n,buffer.Length-n);
            if(count<=0)throw new EndOfStreamException();
            n+=count;
        }
    }
    private static void Client(string name,string mode)
    {
        using(var pipe=new NamedPipeClientStream(".",name,
            PipeDirection.InOut,PipeOptions.None,
            TokenImpersonationLevel.Impersonation))
        {
            pipe.Connect(5000);
            pipe.WriteByte(0x43);
            pipe.Flush();
            byte[] frame=new byte[64];
            ReadExact(pipe,frame);
            byte[] response=new byte[32];
            Buffer.BlockCopy(frame,0,response,0,32);
            if(mode=="wrong")response[0]^=0xff;

            if(mode=="full" || mode=="wrong")
            {
                pipe.Write(response,0,32);pipe.Flush();
                pipe.ReadByte(); // keep process alive through host OS reobservation
            }
            else if(mode=="split")
            {
                pipe.Write(response,0,7);pipe.Flush();
                Thread.Sleep(35);
                pipe.Write(response,7,25);pipe.Flush();
                pipe.ReadByte();
            }
            else if(mode=="short")
            {
                pipe.Write(response,0,3);pipe.Flush();
            }
            else if(mode=="disconnect")
            {
                return;
            }
            else if(mode=="silent")
            {
                Thread.Sleep(1100);
            }
            else if(mode=="partial")
            {
                pipe.Write(response,0,2);pipe.Flush();
                Thread.Sleep(1100);
            }
            else if(mode=="slow")
            {
                for(int i=0;i<8;i++)
                {
                    try{pipe.Write(response,i,1);pipe.Flush();}
                    catch(IOException){break;}
                    Thread.Sleep(215);
                }
            }
            else if(mode=="late")
            {
                Thread.Sleep(1100);
                try{pipe.Write(response,0,32);pipe.Flush();}
                catch(IOException){}
            }
        }
    }
    private sealed class Actual
    {
        internal OsReviewOnlyExchangeObservation Result;
        internal long DurationMilliseconds;
        internal bool Quarantined;
    }
    private static Actual Exchange(string mode,bool crossProcess=false)
    {
        string name=PipeName();
        using(var server=Server(name))
        {
            IAsyncResult waiting=server.BeginWaitForConnection(null,null);
            Thread thread=null;
            Process child=null;
            Exception childException=null;
            try
            {
                if(crossProcess)
                {
                    string exe=Path.GetFullPath(
                        Assembly.GetExecutingAssembly().Location);
                    var info=new ProcessStartInfo(
                        exe,"--p123-child "+name+" "+mode);
                    info.UseShellExecute=false;
                    info.CreateNoWindow=true;
                    child=Process.Start(info);
                    Need(child!=null&&child.Id>0,
                        "real native separate Windows child");
                    using(var me=Process.GetCurrentProcess())
                        Need(child.Id!=me.Id,"different OS PID");
                }
                else
                {
                    thread=new Thread(()=>{
                        try{Client(name,mode);}
                        catch(IOException){}
                        catch(ObjectDisposedException){}
                        catch(Exception ex){childException=ex;}
                    });
                    thread.IsBackground=true;
                    thread.Start();
                }

                Need(waiting.AsyncWaitHandle.WaitOne(5000),"real pipe connected");
                server.EndWaitForConnection(waiting);
                Need(server.ReadByte()==0x43,"inert client byte");
                var timer=Stopwatch.StartNew();
                var obs=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(server,Request());
                timer.Stop();

                bool disconnected=false;
                try
                {
                    disconnected=!server.IsConnected;
                    if(!disconnected)
                    {
                        server.WriteByte(0x42);
                        server.Flush();
                    }
                }
                catch(IOException){disconnected=true;}
                catch(ObjectDisposedException){disconnected=true;}

                if(thread!=null)
                {
                    Need(thread.Join(4500),"thread completed");
                    Need(childException==null,"unprivileged client completed");
                }
                if(child!=null)
                    Need(child.WaitForExit(4500)&&child.ExitCode==0,
                        "unprivileged child completed");
                return new Actual{
                    Result=obs,
                    DurationMilliseconds=timer.ElapsedMilliseconds,
                    Quarantined=disconnected
                };
            }
            finally
            {
                if(child!=null)
                {
                    if(!child.HasExited)child.Kill();
                    child.Dispose();
                }
                waiting.AsyncWaitHandle.Close();
            }
        }
    }
    private static void MustObserveDiagnostic(string mode,bool cross=false)
    {
        var a=Exchange(mode,cross);
        Need(a.Result.State==
            OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
            "OS exchange frame diagnostic only");
        Need(a.Result.NativeChallengeFrameSent &&
            a.Result.NativeOsProcessAndSessionObserved &&
            a.Result.OsObservedClientPid>0,
            "OS-derived client evidence");
        Need(!a.Quarantined,"valid exchange not closed early");
        NoAuthority(a.Result);
    }
    private static void MustRefuseLate(string mode)
    {
        var a=Exchange(mode);
        Need(a.Result.State!=
            OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
            "late/stalled frame never diagnostic");
        Need(a.DurationMilliseconds<3900,"bounded absolute deadline");
        Need(a.Quarantined,"timeout pipe disposed/quarantined");
        NoAuthority(a.Result);
    }
    public static int Main(string[] args)
    {
        if(args!=null&&args.Length==3&&args[0]=="--p123-child")
        {
            try
            {
                if(!args[1].StartsWith("nayeon-p123-hardened-",
                    StringComparison.Ordinal))return 12;
                Client(args[1],args[2]);return 0;
            }
            catch(Exception){return 13;}
        }
        Run("null-pipe-denied-by-integrated-boundary",()=>{
            var o=WindowsReviewOnlyPipeChallengeExchange.
                RunAfterHandshake(null,Request());
            Need(o.State==OsReviewOnlyExchangeState.Unavailable,"null");
            NoAuthority(o);
        });
        Run("null-host-request-denied",()=>{
            var o=WindowsReviewOnlyPipeChallengeExchange.
                RunAfterHandshake(null,null);
            Need(o.State==OsReviewOnlyExchangeState.Unavailable,"null");
            NoAuthority(o);
        });
        Run("unconnected-pipe-refused",()=>{
            using(var p=Server(PipeName()))
            {
                var o=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(p,Request());
                Need(o.State==OsReviewOnlyExchangeState.Unavailable,
                    "unconnected");NoAuthority(o);
            }
        });
        Run("integrated-real-Windows-32-byte-echo-only",()=>{
            MustObserveDiagnostic("full");
        });
        Run("integrated-split-7-plus-25-within-one-deadline",()=>{
            MustObserveDiagnostic("split");
        });
        Run("integrated-real-separate-Windows-client-echo-only",()=>{
            MustObserveDiagnostic("full",true);
        });
        Run("integrated-tampered-nonce-denied",()=>{
            var a=Exchange("wrong");
            Need(a.Result.State==OsReviewOnlyExchangeState.Refused,
                "wrong echo denied");
            NoAuthority(a.Result);
        });
        Run("integrated-truncated-reply-denied",()=>{
            var a=Exchange("short");
            Need(a.Result.State==OsReviewOnlyExchangeState.Refused,
                "short echo denied");
            NoAuthority(a.Result);
        });
        Run("integrated-early-disconnect-denied",()=>{
            var a=Exchange("disconnect");
            Need(a.Result.State!=
                OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
                "disconnected never success");
            NoAuthority(a.Result);
        });
        Run("integrated-silent-OS-client-timeout-quarantined",()=>{
            MustRefuseLate("silent");
        });
        Run("integrated-partial-2-byte-client-timeout-quarantined",()=>{
            MustRefuseLate("partial");
        });
        Run("integrated-slowloris-clients-cannot-reset-frame-deadline",()=>{
            MustRefuseLate("slow");
        });
        Run("integrated-late-32-byte-frame-no-revival",()=>{
            MustRefuseLate("late");
        });
        Run("integrated-failure-does-not-contaminate-new-connection",()=>{
            MustRefuseLate("silent");
            MustObserveDiagnostic("full");
        });
        Run("integrated-native-effects-still-denied",()=>{
            var a=Exchange("full",true);
            Need(a.Result.DiagnosticEchoOnly &&
                !a.Result.NativeCredentialEffectAllowed,
                "no effect after diagnostic");
            Need(!ServiceGate.LiveEligible(),"P49 remains held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 still held");
            NoAuthority(a.Result);
        });
        Run("integrated-source-only-review-flag-always-false",()=>{
            var a=Exchange("full");
            Need(a.Result.DiagnosticEchoOnly &&
                !a.Result.TrueHumanConsentVerified &&
                !a.Result.DurableOneUseGrantIssued,
                "no privileged human grant");
            NoAuthority(a.Result);
        });
        Console.WriteLine("P123_REAL_WINDOWS_INTEGRATED_CASES_PASSED="+passed);
        Console.WriteLine("P123_REAL_WINDOWS_INTEGRATED_CASES_FAILED="+failed);
        Console.WriteLine("P123_P121_REVIEW_EXCHANGE_NOW_USES_P122_ABSOLUTE_READ=TRUE");
        Console.WriteLine("P123_OS_PIPE_STALL_DISCONNECT_DEADLINE=REAL_NATIVE");
        Console.WriteLine("P123_SIGNED_INSTALLED_UI_HUMAN_CONSENT=ABSENT");
        Console.WriteLine("P123_PROTECTED_WINCRED_EFFECT=ZERO");
        Console.WriteLine("P123_ORIGINAL_P96_RACE=STILL_OPEN");
        Console.WriteLine("P123_C1_PRODUCTION_RELEASE=HOLD");
        return passed==16&&failed==0?0:1;
    }
}
