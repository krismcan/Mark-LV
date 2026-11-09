// P124 real Windows pipe HANDLE DUPLICATION red-team proof.
// Test-only synthetic nonce, no keys, credentials, native service or effects.
// A writer in a different Windows process may reuse the established client's
// connected pipe handle. GetNamedPipeClientProcessId reports the opener,
// NOT a cryptographic authentication of who wrote each reply.
// This is a deliberately REPRODUCED G1 trust gap, not its resolution.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P124 handle-transfer red-team may only run on isolated native Windows tests
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using Microsoft.Win32.SafeHandles;
using Nayeon.ByokC1;

internal static class P124ActualTransferredPipeWriterTests
{
    private const uint ProcessDupHandle=0x0040;
    private const uint DuplicateSameAccess=0x00000002;
    private static int passed,failed;

    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    private static extern IntPtr OpenProcess(uint rights,
        [MarshalAs(UnmanagedType.Bool)]bool inherit,uint pid);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    private static extern bool DuplicateHandle(IntPtr sourceProcess,
        IntPtr sourceHandle,IntPtr targetProcess,out IntPtr targetHandle,
        uint desiredAccess,[MarshalAs(UnmanagedType.Bool)]bool inherit,
        uint options);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    private static extern bool WriteFile(IntPtr handle,
        byte[] buffer,uint count,out uint written,IntPtr overlapped);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr handle);

    private static void Need(bool b,string why)
    {if(!b)throw new InvalidOperationException("P124 "+why);}
    private static void Run(string label,Action action)
    {
        try{action();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception e)
        {++failed;Console.WriteLine("FAIL "+label+" "+e.GetType().Name);}
    }
    private static void NoApproval(OsReviewOnlyExchangeObservation o)
    {
        Need(o!=null,"observation present");
        Need(!o.ActualSignedInstalledBrokerAuthenticated,
            "not approved signed broker");
        Need(!o.TrueHumanConsentVerified,"not actual human approval");
        Need(!o.DurableOneUseGrantIssued,"no protected grant");
        Need(!o.PrivilegedServiceListenerInstalled,"no installed service");
        Need(!o.NativeCredentialEffectAllowed,"no actual WinCred effect");
        Need(!o.ToString().Contains("S-1-"),"no SID status leak");
    }
    private static ServiceBoundRequestIdentity Request()
    {
        return new ServiceBoundRequestIdentity(LedgerOperation.Save,
            new string('a',32),new string('b',32),new string('c',64),
            DateTime.UtcNow.Ticks+TimeSpan.TicksPerSecond*35,false);
    }
    private static string Name()
    {return "nayeon-p124-handle-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var me=WindowsIdentity.GetCurrent())
        {
            Need(me.User!=null&&!me.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"unprivileged runner only");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(me.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
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
    private static byte[] FromHex(string hex)
    {
        Need(hex!=null&&hex.Length==64,"32-byte nonsecret challenge");
        byte[] bytes=new byte[32];
        for(int i=0;i<bytes.Length;i++)
            bytes[i]=Convert.ToByte(hex.Substring(i*2,2),16);
        return bytes;
    }
    private static string ToHex(byte[] bytes)
    {return BitConverter.ToString(bytes).Replace("-","");}
    private static string LocalExe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}

    // Executed as a separate genuine unprivileged Windows process.
    // Opens a query-only PROCESS_DUP_HANDLE to its parent, duplicates the
    // parent's already-connected named-pipe CLIENT handle into itself,
    // and writes the response via native Win32 WriteFile. The opener
    // NEVER calls Write on the reply. No credentials or impersonation.
    private static int Writer(string[] args)
    {
        IntPtr parent=IntPtr.Zero,shared=IntPtr.Zero;
        try
        {
            if(args.Length!=5 || args[0]!="--p124-writer")return 20;
            uint openerPid=UInt32.Parse(args[1]);
            long raw=Convert.ToInt64(args[2],16);
            string mode=args[4];
            byte[] bytes=FromHex(args[3]);
            if(mode=="bad")bytes[0]^=0xff;
            int length=mode=="short"?3:32;
            parent=OpenProcess(ProcessDupHandle,false,openerPid);
            if(parent==IntPtr.Zero||parent==new IntPtr(-1))return 21;
            if(!DuplicateHandle(parent,new IntPtr(raw),GetCurrentProcess(),
                out shared,0,false,DuplicateSameAccess) ||
                shared==IntPtr.Zero||shared==new IntPtr(-1))return 22;
            uint written=0;
            if(!WriteFile(shared,bytes,(uint)length,out written,
                IntPtr.Zero) || written!=(uint)length)return 23;
            Console.WriteLine("P124_WRITER_USED_DUPLICATE_HANDLE=TRUE");
            return 0;
        }
        catch(Exception){return 24;}
        finally
        {
            if(shared!=IntPtr.Zero&&shared!=new IntPtr(-1))
                CloseHandle(shared);
            if(parent!=IntPtr.Zero&&parent!=new IntPtr(-1))
                CloseHandle(parent);
        }
    }

    // This is the pipe-connecting process. Its handle is the one whose
    // creator PID/session/token the server observes. In transfer mode
    // ONLY its grandchild writes response bytes.
    private static int Opener(string[] args)
    {
        try
        {
            if(args.Length!=3||args[0]!="--p124-opener"||
               !args[1].StartsWith("nayeon-p124-handle-",
                    StringComparison.Ordinal))return 30;
            using(var client=new NamedPipeClientStream(".",args[1],
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                client.WriteByte(0x43);client.Flush();
                var frame=new byte[64];
                ReadExact(client,frame);
                byte[] nonce=new byte[32];
                Buffer.BlockCopy(frame,0,nonce,0,32);
                string mode=args[2];
                if(mode=="self")
                {
                    client.Write(nonce,0,32);
                    client.Flush();
                }
                else
                {
                    string writerMode=mode=="bad"?"bad":
                        mode=="short"?"short":"valid";
                    string handle=client.SafePipeHandle.
                        DangerousGetHandle().ToInt64().ToString("X");
                    var start=new ProcessStartInfo(LocalExe(),
                        "--p124-writer "+
                        Process.GetCurrentProcess().Id+" "+
                        handle+" "+ToHex(nonce)+" "+writerMode);
                    start.UseShellExecute=false;
                    start.CreateNoWindow=true;
                    using(var child=Process.Start(start))
                    {
                        if(child==null||child.Id<=0)return 31;
                        using(var self=Process.GetCurrentProcess())
                        {
                            if(child.Id==self.Id)return 32;
                            Console.WriteLine("P124_WRITER_DIFFERENT_OS_PROCESS_PID="+
                                child.Id);
                        }
                        if(!child.WaitForExit(4500)||child.ExitCode!=0)
                            return 33;
                    }
                }
                // Keep CONNECTING process alive until server re-observes
                // pipe client OS process and sends acknowledgement.
                try{client.ReadByte();}
                catch(IOException){}
                return 0;
            }
        }
        catch(Exception){return 34;}
    }

    private sealed class Exchange
    {
        internal OsReviewOnlyExchangeObservation Observation;
        internal int OpenerPid;
        internal int WriterPid;
    }

    private static Exchange Actual(string mode)
    {
        string name=Name();
        using(var server=Server(name))
        {
            IAsyncResult accept=server.BeginWaitForConnection(null,null);
            Process opener=null;
            try
            {
                var start=new ProcessStartInfo(LocalExe(),
                    "--p124-opener "+name+" "+mode);
                start.UseShellExecute=false;
                start.CreateNoWindow=true;
                start.RedirectStandardOutput=true;
                opener=Process.Start(start);
                Need(opener!=null&&opener.Id>0,"real opener started");
                int clientPid=opener.Id;
                using(var self=Process.GetCurrentProcess())
                    Need(self.Id!=clientPid,"real separate opener process");
                Need(accept.AsyncWaitHandle.WaitOne(6000),"pipe connection");
                server.EndWaitForConnection(accept);
                Need(server.ReadByte()==0x43,"actual OS pipe handshake");
                var observed=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(server,Request());
                try
                {
                    if(server.IsConnected){server.WriteByte(0x42);server.Flush();}
                }
                catch(IOException){}
                catch(ObjectDisposedException){}

                Need(opener.WaitForExit(5500),"opener must complete");
                Need(opener.ExitCode==0,"opener and writer success");
                string output=opener.StandardOutput.ReadToEnd();
                int writerPid=0;
                foreach(string line in output.Split('\n'))
                {
                    string t=line.Trim();
                    if(t.StartsWith(
                        "P124_WRITER_DIFFERENT_OS_PROCESS_PID=",
                        StringComparison.Ordinal))
                        writerPid=Int32.Parse(t.Substring(
                            "P124_WRITER_DIFFERENT_OS_PROCESS_PID=".Length));
                }
                return new Exchange{
                    Observation=observed,
                    OpenerPid=clientPid,
                    WriterPid=writerPid
                };
            }
            finally
            {
                if(opener!=null)
                {
                    if(!opener.HasExited)opener.Kill();
                    opener.Dispose();
                }
                accept.AsyncWaitHandle.Close();
            }
        }
    }

    private static void ReproduceTransfer()
    {
        var e=Actual("transfer");
        Need(e.WriterPid>0&&e.WriterPid!=e.OpenerPid,
            "writer truly another Windows process");
        Need(e.Observation.OsObservedClientPid==(uint)e.OpenerPid,
            "OS reports opener, despite child writing response");
        Need(e.Observation.State==
            OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
            "diagnostic echo remains possible under handle transfer");
        Need(e.Observation.NativeOsProcessAndSessionObserved,
            "real Windows source PID/session observed");
        NoApproval(e.Observation);
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p124-writer")return Writer(args);
            if(args[0]=="--p124-opener")return Opener(args);
        }

        Run("null-connected-pipe-cannot-create-approval",()=>{
            var obs=WindowsReviewOnlyPipeChallengeExchange.
                RunAfterHandshake(null,Request());
            Need(obs.State==OsReviewOnlyExchangeState.Unavailable,
                "null unavailable");NoApproval(obs);
        });
        Run("unconnected-native-pipe-refuses",()=>{
            using(var pipe=Server(Name()))
            {
                var obs=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(pipe,Request());
                Need(obs.State==OsReviewOnlyExchangeState.Unavailable,
                    "not connected");NoApproval(obs);
            }
        });
        Run("native-original-separate-process-control-echo",()=>{
            var e=Actual("self");
            Need(e.Observation.DiagnosticEchoOnly &&
                e.Observation.OsObservedClientPid==(uint)e.OpenerPid &&
                e.WriterPid==0,"normal OS opener control");
            NoApproval(e.Observation);
        });
        Run("native-child-duplicated-client-handle-echo-reproduced",()=>{
            ReproduceTransfer();
        });
        Run("native-getnamedpipeclientprocessid-reports-opener-not-writer",()=>{
            ReproduceTransfer();
        });
        Run("native-process-token-session-observations-do-not-prove-writer",()=>{
            var e=Actual("transfer");
            Need(e.WriterPid>0&&e.WriterPid!=e.OpenerPid &&
                e.Observation.NativeOsProcessAndSessionObserved &&
                e.Observation.DiagnosticEchoOnly,
                "OS process/session still observed, wrong author inference");
            NoApproval(e.Observation);
        });
        Run("duplicated-handle-wrong-nonce-refused",()=>{
            var e=Actual("bad");
            Need(e.WriterPid>0&&e.WriterPid!=e.OpenerPid &&
                e.Observation.State==OsReviewOnlyExchangeState.Refused,
                "different writer wrong echo");
            NoApproval(e.Observation);
        });
        Run("duplicated-handle-truncated-nonce-refused",()=>{
            var e=Actual("short");
            Need(e.WriterPid>0&&e.WriterPid!=e.OpenerPid &&
                e.Observation.State!=
                    OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
                "different writer short echo");
            NoApproval(e.Observation);
        });
        Run("distinct-fresh-connection-repeats-reproducible-OS-gap",()=>{
            ReproduceTransfer();ReproduceTransfer();
        });
        Run("duplicated-handle-success-never-signed-human-consent",()=>{
            var e=Actual("transfer");
            Need(e.Observation.DiagnosticEchoOnly &&
                !e.Observation.TrueHumanConsentVerified &&
                !e.Observation.DurableOneUseGrantIssued,
                "no consent even with echoed nonce");
            NoApproval(e.Observation);
        });
        Run("native-effects-original-service-still-disabled",()=>{
            Need(!ServiceGate.LiveEligible(),"P49 service held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "no native WinCred effect");
            ReproduceTransfer();
        });
        Run("repeat-handoff-contains-no-production-grant",()=>{
            for(int i=0;i<3;i++)ReproduceTransfer();
        });

        Console.WriteLine("P124_TRANSFERRED_PIPE_WRITER_CASES_PASSED="+passed);
        Console.WriteLine("P124_TRANSFERRED_PIPE_WRITER_CASES_FAILED="+failed);
        Console.WriteLine("P124_OTHER_PROCESS_WRITE_WITH_DUPLICATED_PIPE=REPRODUCED");
        Console.WriteLine("P124_PIPE_CLIENT_PID_IDENTIFIES_OPENER_NOT_REPLY_AUTHOR=REPRODUCED");
        Console.WriteLine("P124_ECHO_IS_NOT_AUTHENTICATED_SIGNED_CONSENT=TRUE");
        Console.WriteLine("P124_G1_HANDLE_TRANSFER_THREAT=OPEN");
        Console.WriteLine("P124_REAL_CREDENTIAL_EFFECTS=ZERO");
        Console.WriteLine("P124_ORIGINAL_P96_RACE=OPEN");
        Console.WriteLine("P124_C1_PRODUCTION_RELEASE=HOLD");
        return passed==12&&failed==0?0:1;
    }
}
