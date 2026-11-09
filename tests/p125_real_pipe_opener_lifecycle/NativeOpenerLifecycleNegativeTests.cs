// P125 — ACTUAL native Windows pipe-opener exit/close + transferred writer negative tests.
// A different process owns a DUPLICATE of an unprivileged connected pipe.
// The kernel's pipe-opener PID is NOT proof of the author of a reply.
// All frames and reports are NONSECRET, in ephemeral runner test context only.
// This test must NEVER run as an installed service or on Kristian unsigned.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P125 hostile lifecycle native driver is restricted to isolated Windows review tests
#endif
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;

internal static class P125ActualTransferredOpenerLifecycleTests
{
    private const uint ProcessDupHandle=0x0040;
    private const uint ProcessSynchronize=0x00100000;
    private const uint DuplicateSameAccess=0x00000002;
    private const uint WaitObject0=0;
    private static int passed,failed;

    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    private static extern IntPtr OpenProcess(uint access,
        [MarshalAs(UnmanagedType.Bool)]bool inherit,uint pid);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    private static extern bool DuplicateHandle(IntPtr srcProcess,
        IntPtr srcHandle,IntPtr targetProcess,out IntPtr targetHandle,
        uint access,[MarshalAs(UnmanagedType.Bool)]bool inherit,uint options);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    private static extern bool WriteFile(IntPtr handle,byte[] buffer,
        uint count,out uint written,IntPtr overlapped);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    private static extern uint WaitForSingleObject(IntPtr handle,uint timeoutMs);
    [DllImport("kernel32.dll",SetLastError=true,ExactSpelling=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr handle);

    private static void Need(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("P125 "+why);}
    private static void Run(string label,Action act)
    {
        try{act();passed++;Console.WriteLine("PASS "+label);}
        catch(Exception e){failed++;Console.WriteLine("FAIL "+label+" "+e.GetType().Name);}
    }
    private static void NoAuthority(OsReviewOnlyExchangeObservation o)
    {
        Need(o!=null,"observation exists");
        Need(!o.ActualSignedInstalledBrokerAuthenticated,"no installed signed broker");
        Need(!o.TrueHumanConsentVerified,"no authentic user click");
        Need(!o.DurableOneUseGrantIssued,"no protected persisted grant");
        Need(!o.PrivilegedServiceListenerInstalled,"no privileged listener");
        Need(!o.NativeCredentialEffectAllowed,"no WinCred effect");
        Need(!o.ToString().Contains("S-1-"),"no account token leaked");
    }
    private static ServiceBoundRequestIdentity HostRequest()
    {
        return new ServiceBoundRequestIdentity(
            LedgerOperation.Save,new string('a',32),
            new string('b',32),new string('c',64),
            DateTime.UtcNow.Ticks+TimeSpan.TicksPerSecond*35,false);
    }
    private static string PipeName()
    {return "nayeon-p125-exit-"+Guid.NewGuid().ToString("N");}
    private static string ReportPath(string name)
    {return Path.Combine(Path.GetTempPath(),"p125_"+name+".txt");}
    private static string LocalExe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}
    private static NamedPipeServerStream Server(string name)
    {
        using(var identity=WindowsIdentity.GetCurrent())
        {
            Need(identity.User!=null&&!identity.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"unprivileged hosted Windows");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(identity.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }
    private static void ReadExact(Stream stream,byte[] frame)
    {
        int offset=0;
        while(offset<frame.Length)
        {
            int count=stream.Read(frame,offset,frame.Length-offset);
            if(count<=0)throw new EndOfStreamException();
            offset+=count;
        }
    }
    private static byte[] ParseNonce(string hex)
    {
        Need(hex!=null&&hex.Length==64,"nonsecret 32-byte nonce");
        byte[] bytes=new byte[32];
        for(int i=0;i<32;i++)
            bytes[i]=Convert.ToByte(hex.Substring(i*2,2),16);
        return bytes;
    }

    // Separate unprivileged Windows process duplicates pipe into ITSELF.
    // Exiting connecting process is signaled through its opened process
    // HANDLE (SYNCHRONIZE). It waits for actual termination before writing
    // the reply, so this is NOT a synthetic PID claim or swapped string.
    private static int Writer(string[] args)
    {
        IntPtr opener=IntPtr.Zero,copy=IntPtr.Zero;
        try
        {
            if(args.Length!=6||args[0]!="--p125-writer")return 20;
            uint openerPid=UInt32.Parse(args[1]);
            long rawHandle=Convert.ToInt64(args[2],16);
            byte[] response=ParseNonce(args[3]);
            string mode=args[4],name=args[5];
            if(!name.StartsWith("nayeon-p125-exit-",
                StringComparison.Ordinal))return 21;
            opener=OpenProcess(ProcessDupHandle|ProcessSynchronize,
                false,openerPid);
            if(opener==IntPtr.Zero||opener==new IntPtr(-1))return 22;
            if(!DuplicateHandle(opener,new IntPtr(rawHandle),
                GetCurrentProcess(),out copy,0,false,DuplicateSameAccess)||
                copy==IntPtr.Zero||copy==new IntPtr(-1))return 23;
            Console.WriteLine("P125_DUPLICATE_READY");
            Console.Out.Flush();
            if(mode.StartsWith("exit",StringComparison.Ordinal))
            {
                if(WaitForSingleObject(opener,5000)!=WaitObject0)return 24;
            }
            else if(mode.StartsWith("close",StringComparison.Ordinal))
            {
                if(!String.Equals(Console.ReadLine(),"GO",
                    StringComparison.Ordinal))return 25;
            }
            else if(!String.Equals(mode,"alive",
                    StringComparison.Ordinal))return 26;

            if(mode.EndsWith("bad",StringComparison.Ordinal))
                response[0]^=0xff;
            int length=mode.EndsWith("short",StringComparison.Ordinal)?3:32;
            uint written;
            if(!WriteFile(copy,response,(uint)length,out written,
                IntPtr.Zero)||written!=(uint)length)return 27;

            // Nonsecret evidence file on isolated hosted runner TEMP only.
            // Never contains any nonce, SID, key, pipe handle or credential.
            File.WriteAllText(ReportPath(name),
                Process.GetCurrentProcess().Id+":"+written);
            return 0;
        }
        catch(Exception){return 28;}
        finally
        {
            if(copy!=IntPtr.Zero&&copy!=new IntPtr(-1))CloseHandle(copy);
            if(opener!=IntPtr.Zero&&opener!=new IntPtr(-1))CloseHandle(opener);
        }
    }

    // This process actually OPENS the pipe, so Windows will identify it
    // as the original client. It NEVER writes response bytes itself.
    private static int Opener(string[] args)
    {
        try
        {
            if(args.Length!=3||args[0]!="--p125-opener"||
                !args[1].StartsWith("nayeon-p125-exit-",
                    StringComparison.Ordinal))return 30;
            string name=args[1],mode=args[2];
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                client.WriteByte(0x43);client.Flush();
                byte[] frame=new byte[64];
                ReadExact(client,frame);
                byte[] nonce=new byte[32];
                Buffer.BlockCopy(frame,0,nonce,0,32);

                var start=new ProcessStartInfo(LocalExe(),
                    "--p125-writer "+Process.GetCurrentProcess().Id+" "+
                    client.SafePipeHandle.DangerousGetHandle().ToInt64().
                        ToString("X")+" "+
                    BitConverter.ToString(nonce).Replace("-","")+" "+
                    mode+" "+name);
                start.UseShellExecute=false;
                start.CreateNoWindow=true;
                start.RedirectStandardOutput=true;
                start.RedirectStandardInput=true;
                using(var child=Process.Start(start))
                {
                    if(child==null||child.Id<=0||
                        child.Id==Process.GetCurrentProcess().Id)return 31;
                    string ready=child.StandardOutput.ReadLine();
                    if(!String.Equals(ready,"P125_DUPLICATE_READY",
                        StringComparison.Ordinal))return 32;

                    if(mode.StartsWith("exit",StringComparison.Ordinal))
                    {
                        // No reply from this opener. Its process genuinely
                        // terminates before writer's WaitForSingleObject
                        // permits the child to write on the duplicated handle.
                        return 0;
                    }
                    if(mode.StartsWith("close",StringComparison.Ordinal))
                    {
                        // Dispose original handle but LEAVE opener process
                        // alive. Another process can still write to its dup.
                        client.Dispose();
                        child.StandardInput.WriteLine("GO");
                        child.StandardInput.Flush();
                        if(!child.WaitForExit(5000)||child.ExitCode!=0)
                            return 33;
                        Thread.Sleep(750);
                        return 0;
                    }
                    if(mode=="alive")
                    {
                        if(!child.WaitForExit(5000)||child.ExitCode!=0)
                            return 34;
                        client.ReadByte(); // keep connecting client alive
                        return 0;
                    }
                    return 35;
                }
            }
        }
        catch(Exception){return 36;}
    }

    private sealed class Outcome
    {
        internal OsReviewOnlyExchangeObservation Observation;
        internal int OpenerPid;
        internal int WriterPid;
        internal int NativeWrittenBytes;
        internal bool OpenerExited;
    }

    private static Outcome Actual(string mode)
    {
        string name=PipeName(),report=ReportPath(name);
        using(var server=Server(name))
        {
            IAsyncResult accept=server.BeginWaitForConnection(null,null);
            Process opener=null;
            try
            {
                var start=new ProcessStartInfo(LocalExe(),
                    "--p125-opener "+name+" "+mode);
                start.UseShellExecute=false;
                start.CreateNoWindow=true;
                opener=Process.Start(start);
                Need(opener!=null&&opener.Id>0,
                    "real Windows opener started");
                int openerPid=opener.Id;
                using(var self=Process.GetCurrentProcess())
                    Need(self.Id!=openerPid,"separate original opener");

                Need(accept.AsyncWaitHandle.WaitOne(5500),
                    "real Windows OS pipe connected");
                server.EndWaitForConnection(accept);
                Need(server.ReadByte()==0x43,"real client byte received");
                OsReviewOnlyExchangeObservation result=
                    WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(server,HostRequest());
                try
                {
                    if(server.IsConnected){server.WriteByte(0x42);server.Flush();}
                }
                catch(IOException){}
                catch(ObjectDisposedException){}

                Need(opener.WaitForExit(5500),
                    "opening process terminated");
                Need(opener.ExitCode==0,"opening process clean");
                bool exited=opener.HasExited;

                string resultData=null;
                for(int retry=0;retry<180;retry++)
                {
                    if(File.Exists(report))
                    {
                        try {resultData=File.ReadAllText(report);break;}
                        catch(IOException){}
                    }
                    Thread.Sleep(20);
                }
                Need(!String.IsNullOrWhiteSpace(resultData),
                    "other actual Windows writer successfully wrote");
                string[] parts=resultData.Trim().Split(':');
                Need(parts.Length==2,"native proof format");
                int writerPid=Int32.Parse(parts[0]);
                int count=Int32.Parse(parts[1]);
                Need(writerPid>0&&writerPid!=openerPid,
                    "different native OS process authored response");
                return new Outcome{
                    Observation=result,
                    OpenerPid=openerPid,
                    WriterPid=writerPid,
                    NativeWrittenBytes=count,
                    OpenerExited=exited
                };
            }
            finally
            {
                if(opener!=null)
                {
                    if(!opener.HasExited)opener.Kill();
                    opener.Dispose();
                }
                try{if(File.Exists(report))File.Delete(report);}
                catch(IOException){}
                accept.AsyncWaitHandle.Close();
            }
        }
    }

    private static Outcome ExitAndRefuse(string mode)
    {
        Outcome x=Actual(mode);
        Need(x.OpenerExited,"opener actually exited");
        Need(x.WriterPid!=x.OpenerPid,
            "reply from distinct native process");
        Need(x.NativeWrittenBytes==
            (mode.EndsWith("short",StringComparison.Ordinal)?3:32),
            "writer actually sent requested count");
        Need(x.Observation.State!=
            OsReviewOnlyExchangeState.EchoObservedWithoutConsent,
            "original client exit MUST NOT produce diagnostic author match");
        NoAuthority(x.Observation);
        return x;
    }
    private static void CloseAndNoApproval()
    {
        Outcome x=Actual("close");
        Need(x.OpenerExited,"opener completes eventually");
        Need(x.WriterPid!=x.OpenerPid&&x.NativeWrittenBytes==32,
            "other native OS process sent full echo after original handle closed");
        NoAuthority(x.Observation);
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length>0)
        {
            if(args[0]=="--p125-opener")return Opener(args);
            if(args[0]=="--p125-writer")return Writer(args);
        }

        Run("null-IPC-boundary-still-denies",()=>{
            var o=WindowsReviewOnlyPipeChallengeExchange.
                RunAfterHandshake(null,HostRequest());
            Need(o.State==OsReviewOnlyExchangeState.Unavailable,
                "null denied");NoAuthority(o);
        });
        Run("unconnected-IPC-boundary-still-denies",()=>{
            using(var server=Server(PipeName()))
            {
                var o=WindowsReviewOnlyPipeChallengeExchange.
                    RunAfterHandshake(server,HostRequest());
                Need(o.State==OsReviewOnlyExchangeState.Unavailable,
                    "not connected");NoAuthority(o);
            }
        });
        Run("normal-handle-duplication-echo-not-authorship-proof",()=>{
            Outcome x=Actual("alive");
            Need(x.OpenerExited&&x.WriterPid!=x.OpenerPid &&
                x.NativeWrittenBytes==32 &&
                x.Observation.DiagnosticEchoOnly &&
                x.Observation.OsObservedClientPid==(uint)x.OpenerPid,
                "OS process remains client opener, writer different");
            NoAuthority(x.Observation);
        });
        Run("opener-exits-after-handle-copy-host-refuses",()=>{
            ExitAndRefuse("exit");
        });
        Run("opener-death-before-native-write-refuses-despite-full-nonce",()=>{
            ExitAndRefuse("exit");
        });
        Run("opener-death-repeated-real-native-lifecycle",()=>{
            ExitAndRefuse("exit");ExitAndRefuse("exit");
        });
        Run("opener-death-plus-wrong-nonce-remains-refused",()=>{
            ExitAndRefuse("exit-bad");
        });
        Run("opener-death-plus-short-reply-remains-refused",()=>{
            ExitAndRefuse("exit-short");
        });
        Run("original-client-handle-closed-other-process-can-write",()=>{
            CloseAndNoApproval();
        });
        Run("opener-still-alive-but-original-handle-closed-is-not-consent",()=>{
            CloseAndNoApproval();
        });
        Run("repeated-close-and-transfer-never-proves-human-click",()=>{
            CloseAndNoApproval();CloseAndNoApproval();
        });
        Run("P49-P112-real-native-effects-still-locked",()=>{
            Need(!ServiceGate.LiveEligible(),"P49 service held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 native WinCred admission blocked");
            ExitAndRefuse("exit");
        });

        Console.WriteLine("P125_ACTUAL_NATIVE_OPENER_LIFECYCLE_CASES_PASSED="+passed);
        Console.WriteLine("P125_ACTUAL_NATIVE_OPENER_LIFECYCLE_CASES_FAILED="+failed);
        Console.WriteLine("P125_EXITED_ORIGINAL_CLIENT_TRANSFERRED_WRITER=REAL_NATIVE");
        Console.WriteLine("P125_EXITED_CLIENT_POST_REPLY_OS_ADMISSION=REFUSED");
        Console.WriteLine("P125_LIVE_OPENER_CLOSED_HANDLE_STILL_NOT_AUTHORITY=TRUE");
        Console.WriteLine("P125_SIGNED_INSTALLED_BROKER_HUMAN_CLICK=ABSENT");
        Console.WriteLine("P125_G1_TRANSFERRED_HANDLE_TRUST_GAP=STILL_OPEN");
        Console.WriteLine("P125_PROTECTED_NATIVE_WINCRED_EFFECTS=ZERO");
        Console.WriteLine("P125_OLD_P96_RACE=OPEN");
        Console.WriteLine("P125_C1_PRODUCTION_RELEASE=HOLD");
        return passed==12&&failed==0?0:1;
    }
}
