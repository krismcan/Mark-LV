// P121 actual unprivileged Windows OS pipe-client exchange focused tests.
// No real consent app, API key, installed privileged listener or WinCred.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P121 review-only test driver forbidden in production assembly
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

internal static class P121NativePipeChallengeTests
{
    private static int passed,failed;
    private static void Need(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("P121 "+why);}
    private static void Run(string label,Action test)
    {
        try{test();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception ex){++failed;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name);}
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
        Need(o!=null,"observation exists");
        Need(!o.ActualSignedInstalledBrokerAuthenticated,
            "no approved signer");
        Need(!o.TrueHumanConsentVerified,"no user click");
        Need(!o.DurableOneUseGrantIssued,"no persistent grant");
        Need(!o.PrivilegedServiceListenerInstalled,"no privileged service");
        Need(!o.NativeCredentialEffectAllowed,"no native WinCred");
        Need(!o.ToString().Contains("S-1-"),"no token SID log");
        Need(!o.ToString().Contains(":\\"),"no private path log");
    }
    private static string NewPipe()
    {return "nayeon-c1-p121-review-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var id=WindowsIdentity.GetCurrent())
        {
            Need(id.User!=null&&!id.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"not LocalSystem");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(id.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }
    private static bool EqualBytes(byte[] x,byte[] y)
    {
        if(x==null||y==null||x.Length!=y.Length)return false;
        for(int i=0;i<x.Length;i++)if(x[i]!=y[i])return false;
        return true;
    }
    private static void ReadExactly(Stream stream,byte[] buffer)
    {
        int n=0;
        while(n<buffer.Length)
        {
            int more=stream.Read(buffer,n,buffer.Length-n);
            if(more<=0)throw new EndOfStreamException();
            n+=more;
        }
    }
    // Client is an UNTRUSTED application; only a byte echo can be observed.
    // Modes are synthetic negatives, not forged OS credentials.
    private static byte[] UnprivilegedClient(
        string name,string mode,byte[] priorNonce)
    {
        using(var client=new NamedPipeClientStream(".",name,
            PipeDirection.InOut,PipeOptions.None,
            TokenImpersonationLevel.Impersonation))
        {
            client.Connect(5000);
            client.WriteByte(0x43);client.Flush();
            if(mode=="close")return null;
            byte[] frame=new byte[64];
            ReadExactly(client,frame);
            byte[] answer=new byte[32];
            if(mode=="replay" && priorNonce!=null && priorNonce.Length==32)
                Buffer.BlockCopy(priorNonce,0,answer,0,32);
            else
                Buffer.BlockCopy(frame,0,answer,0,32);
            if(mode=="wrong")answer[0]^=0xff;
            if(mode=="claim")
                for(int i=0;i<32;i++)answer[i]=(byte)'P';
            int n=mode=="short"?3:answer.Length;
            client.Write(answer,0,n);client.Flush();
            if(mode=="short")return frame;
            if(client.ReadByte()!=0x42)
                throw new InvalidOperationException("no host ack");
            return frame;
        }
    }
    private sealed class ExchangeRun
    {
        internal OsReviewOnlyExchangeObservation Observation;
        internal byte[] Frame;
    }
    private static ExchangeRun Execute(
        bool crossProcess,string mode,byte[] priorNonce=null)
    {
        string name=NewPipe();
        using(var server=Server(name))
        {
            IAsyncResult wait=server.BeginWaitForConnection(null,null);
            Thread thread=null;
            Process child=null;
            Exception threadFailure=null;
            byte[] frame=null;
            try
            {
                if(crossProcess)
                {
                    string exe=Path.GetFullPath(
                        Assembly.GetExecutingAssembly().Location);
                    var info=new ProcessStartInfo(
                        exe,"--p121-child "+name+" "+mode);
                    info.UseShellExecute=false;
                    info.CreateNoWindow=true;
                    child=Process.Start(info);
                    Need(child!=null&&child.Id>0,"OS child started");
                }
                else
                {
                    thread=new Thread(()=>{
                        try{frame=UnprivilegedClient(name,mode,priorNonce);}
                        catch(Exception e){threadFailure=e;}
                    });
                    thread.IsBackground=true;
                    thread.Start();
                }

                Need(wait.AsyncWaitHandle.WaitOne(6000),"real OS connection");
                server.EndWaitForConnection(wait);
                Need(server.ReadByte()==0x43,"actual client handshake");
                var observation=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(server,Request());
                try
                {
                    if(server.IsConnected){server.WriteByte(0x42);server.Flush();}
                }
                catch(IOException) { /* disconnection is never approval */ }
                if(child!=null)
                {
                    Need(child.WaitForExit(5000)&&child.ExitCode==0,
                        "unprivileged child exited");
                }
                if(thread!=null)
                {
                    Need(thread.Join(5000),"client thread exited");
                    Need(threadFailure==null,"inert client completed");
                }
                return new ExchangeRun{Observation=observation,Frame=frame};
            }
            finally
            {
                if(child!=null)
                {
                    if(!child.HasExited)child.Kill();
                    child.Dispose();
                }
                if(wait!=null)wait.AsyncWaitHandle.Close();
            }
        }
    }
    private static int Child(string[] args)
    {
        try
        {
            if(args.Length!=3 ||
                !args[1].StartsWith("nayeon-c1-p121-review-",
                    StringComparison.Ordinal))return 12;
            UnprivilegedClient(args[1],args[2],null);
            return 0;
        }
        catch(Exception){return 13;}
    }
    private static void ActualEcho(bool crossProcess)
    {
        var result=Execute(crossProcess,"valid");
        Need(result.Observation.State==
            OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
            "actual pipe echo, never approval");
        Need(result.Observation.NativeOsProcessAndSessionObserved &&
            result.Observation.NativeChallengeFrameSent &&
            result.Observation.OsObservedClientPid>0,
            "real Windows peer, frame and PID");
        if(crossProcess)
        {
            using(var self=Process.GetCurrentProcess())
                Need(result.Observation.OsObservedClientPid!=(uint)self.Id,
                    "genuine separate process");
        }
        else Need(result.Frame!=null&&result.Frame.Length==64,
            "same process received actual challenge frame");
        NoAuthority(result.Observation);
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>=1&&args[0]=="--p121-child")
            return Child(args);
        Run("null-pipe-sticky-no-trust",()=>
        {
            var o=WindowsReviewOnlyPipeChallengeExchange.
                RunAfterHandshake(null,Request());
            Need(o.State==OsReviewOnlyExchangeState.Unavailable,"null denied");
            NoAuthority(o);
        });
        Run("unconnected-pipe-no-trust",()=>
        {
            using(var s=Server(NewPipe()))
            {
                var o=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(s,Request());
                Need(o.State==OsReviewOnlyExchangeState.Unavailable,
                    "disconnected");
                NoAuthority(o);
            }
        });
        Run("missing-host-operation-no-trust",()=>
        {
            var o=WindowsReviewOnlyPipeChallengeExchange.
                RunAfterHandshake(null,null);
            Need(o.State==OsReviewOnlyExchangeState.Unavailable,"null request");
            NoAuthority(o);
        });
        Run("actual-Windows-same-process-echo-is-not-consent",()=>
        { ActualEcho(false); });
        Run("actual-Windows-separate-process-echo-is-not-consent",()=>
        { ActualEcho(true); });
        Run("same-process-invalid-echo-sticky-refused",()=>
        {
            var r=Execute(false,"wrong");
            Need(r.Observation.State==OsReviewOnlyExchangeState.Refused,
                "wrong echo");
            NoAuthority(r.Observation);
        });
        Run("separate-process-invalid-echo-sticky-refused",()=>
        {
            var r=Execute(true,"wrong");
            Need(r.Observation.State==OsReviewOnlyExchangeState.Refused,
                "child bad echo");
            NoAuthority(r.Observation);
        });
        Run("same-process-truncated-response-refused",()=>
        {
            var r=Execute(false,"short");
            Need(r.Observation.State==OsReviewOnlyExchangeState.Refused,
                "partial response");
            NoAuthority(r.Observation);
        });
        Run("separate-process-truncated-response-refused",()=>
        {
            var r=Execute(true,"short");
            Need(r.Observation.State==OsReviewOnlyExchangeState.Refused,
                "partial child response");
            NoAuthority(r.Observation);
        });
        Run("disconnect-after-handshake-never-approves",()=>
        {
            var r=Execute(false,"close");
            Need(r.Observation.State!=
                OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
                "early disconnect never echo");
            NoAuthority(r.Observation);
        });
        Run("caller-supplied-fake-PID-claim-is-not-authority",()=>
        {
            var r=Execute(false,"claim");
            Need(r.Observation.State==OsReviewOnlyExchangeState.Refused,
                "fake claim not authenticated");
            NoAuthority(r.Observation);
        });
        Run("replay-previous-pipe-challenge-refused",()=>
        {
            var first=Execute(false,"valid");
            Need(first.Observation.DiagnosticEchoOnly && first.Frame!=null,
                "first transcript received");
            var previous=new byte[32];
            Buffer.BlockCopy(first.Frame,0,previous,0,32);
            var second=Execute(false,"replay",previous);
            Need(second.Observation.State==OsReviewOnlyExchangeState.Refused,
                "another pipe/nonce not replayed");
            NoAuthority(second.Observation);
        });
        Run("two-actual-pipe-sessions-use-distinct-challenges",()=>
        {
            var a=Execute(false,"valid");
            var b=Execute(false,"valid");
            Need(a.Frame!=null && b.Frame!=null &&
                !EqualBytes(a.Frame,b.Frame),
                "fresh challenge frame per OS pipe");
            NoAuthority(a.Observation);NoAuthority(b.Observation);
        });
        Run("actual-OS-client-observation-never-enables-WinCred",()=>
        {
            var r=Execute(true,"valid");
            Need(r.Observation.NativeOsProcessAndSessionObserved &&
                r.Observation.DiagnosticEchoOnly &&
                !r.Observation.TrueHumanConsentVerified &&
                !r.Observation.NativeCredentialEffectAllowed,
                "OS process + echo is not consent");
            Need(!ServiceGate.LiveEligible(),"original P49 held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 live effects disabled");
            NoAuthority(r.Observation);
        });
        Console.WriteLine("P121_REAL_WINDOWS_PIPE_CHALLENGE_CASES_PASSED="+passed);
        Console.WriteLine("P121_REAL_WINDOWS_PIPE_CHALLENGE_CASES_FAILED="+failed);
        Console.WriteLine("P121_OS_DERIVED_PROCESS_SESSION_PEER_BINDING=OBSERVED");
        Console.WriteLine("P121_CHALLENGE_ECHO=NON_AUTHORITATIVE");
        Console.WriteLine("P121_INSTALLED_SIGNED_BROKER_HUMAN_CLICK=ABSENT");
        Console.WriteLine("P121_PROTECTED_GRANT_WINCRED=ZERO");
        Console.WriteLine("P121_OLD_P96_RACE=OPEN");
        Console.WriteLine("P121_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14&&failed==0?0:1;
    }
}
