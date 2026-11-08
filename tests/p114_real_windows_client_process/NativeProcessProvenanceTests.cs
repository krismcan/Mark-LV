// P114 genuine Windows pipe CLIENT process provenance, unprivileged CI.
// Source creates only random local TEST pipes and ephemeral same-EXE child.
// An OS PID/image/token is NOT an approved signed UI or human consent.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P114NativeProcessProvenanceTests
{
    private static int passed, failed;
    private static void Need(bool b,string s)
    { if(!b)throw new InvalidOperationException("P114 "+s); }
    private static void Run(string name,Action test)
    {
        try{test();++passed;Console.WriteLine("PASS "+name);}
        catch(Exception e){++failed;Console.WriteLine("FAIL "+name+" "+e.GetType().Name);}
    }
    private static void NoAuthority(OsPipeClientProcessProvenance o)
    {
        Need(!o.SignedTrustedConsentImageVerified,"no verified publisher");
        Need(!o.InteractiveUserSessionVerified,"no interactive session");
        Need(!o.ExplicitHumanConsentVerified,"no human click");
        Need(!o.ProtectedOneUseGrantIssued,"no one-use ticket");
        Need(!o.NativeCredentialEffectAllowed,"no native effect");
        Need(!o.ToString().Contains("S-1-"),"SID never printed");
        Need(!o.ToString().Contains(":\\"),"image never printed");
    }
    private static string NewName()
    {return "nayeon-c1-p114-test-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var id=WindowsIdentity.GetCurrent())
        {
            Need(id.User!=null &&
                !id.User.IsWellKnown(WellKnownSidType.LocalSystemSid),
                "test must not be LocalSystem");
            var rules=new PipeSecurity();
            rules.SetAccessRuleProtection(true,false);
            rules.AddAccessRule(new PipeAccessRule(id.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,rules);
        }
    }
    private static OsPipeClientProcessProvenance SameProcess(
        TokenImpersonationLevel level)
    {
        var name=NewName();
        using(var server=Server(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.Out,PipeOptions.None,level))
            {
                client.Connect(5000);
                Need(pending.AsyncWaitHandle.WaitOne(5000),"connected");
                server.EndWaitForConnection(pending);
                client.WriteByte(0x43);client.Flush();
                Need(server.ReadByte()==0x43,"client byte read");
                return WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(server);
            }
        }
    }
    private sealed class CrossProcess
    {
        internal uint ExpectedPid;
        internal string ExpectedImage;
        internal OsPipeClientProcessProvenance Result;
    }
    private static CrossProcess SeparateClient()
    {
        var name=NewName();
        using(var server=Server(name))
        {
            string testExe=Path.GetFullPath(
                Assembly.GetExecutingAssembly().Location);
            Need(File.Exists(testExe),"genuine compiled test EXE");
            var start=new ProcessStartInfo(testExe,"--p114-child "+name);
            start.UseShellExecute=false;
            start.CreateNoWindow=true;
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var client=Process.Start(start))
            {
                Need(client!=null && client.Id>0,"actual child process");
                try
                {
                    Need(pending.AsyncWaitHandle.WaitOne(6000),
                        "child connected");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"child handshake");
                    var result=WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(
                        server);
                    server.WriteByte(0x42);server.Flush();
                    Need(client.WaitForExit(5000) && client.ExitCode==0,
                        "test child exits");
                    return new CrossProcess {
                        ExpectedPid=(uint)client.Id,
                        ExpectedImage=testExe,
                        Result=result
                    };
                }
                finally{if(!client.HasExited)client.Kill();}
            }
        }
    }
    private static int Child(string name)
    {
        try
        {
            if(name==null || !name.StartsWith("nayeon-c1-p114-test-",
                StringComparison.Ordinal))return 12;
            using(var pipe=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                pipe.Connect(5000);
                pipe.WriteByte(0x43);pipe.Flush();
                return pipe.ReadByte()==0x42?0:13;
            }
        }
        catch(Exception){return 14;}
    }
    public static int Main(string[] args)
    {
        if(args!=null && args.Length==2 && args[0]=="--p114-child")
            return Child(args[1]);

        Run("null-connected-pipe-fail-closed",()=>
        {
            var o=WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(null);
            Need(o.State==OsPipeClientProcessState.Unavailable,"null denied");
            NoAuthority(o);
        });
        Run("disconnected-pipe-fail-closed",()=>
        {
            using(var p=Server(NewName()))
            {
                var o=WindowsPipeClientProcessProvenance.ObserveAfterClientWrite(p);
                Need(o.State==OsPipeClientProcessState.Unavailable,"disconnected");
                NoAuthority(o);
            }
        });
        Run("actual-OS-same-process-client-PID",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.KernelProcessObserved,"OS PID observed");
            using(var current=Process.GetCurrentProcess())
                Need(o.OsClientProcessId==(uint)current.Id,"same PID");
            NoAuthority(o);
        });
        Run("actual-different-process-kernel-pipe-client-PID",()=>
        {
            var c=SeparateClient();
            Need(c.Result.KernelProcessObserved,"OS process observed");
            Need(c.Result.OsClientProcessId==c.ExpectedPid,
                "OS PID matches spawned client");
            using(var self=Process.GetCurrentProcess())
                Need(c.ExpectedPid!=(uint)self.Id,"separate client process");
            NoAuthority(c.Result);
        });
        Run("different-process-kernel-executable-image-path",()=>
        {
            var c=SeparateClient();
            Need(c.Result.KernelProcessObserved,"OS image observed");
            Need(String.Equals(Path.GetFullPath(c.Result.OsImagePath),
                c.ExpectedImage,StringComparison.OrdinalIgnoreCase),
                "real child loaded image path");
            NoAuthority(c.Result);
        });
        Run("different-process-real-creation-time",()=>
        {
            var c=SeparateClient();
            Need(c.Result.KernelProcessObserved,"OS create-time observed");
            DateTime t=DateTime.FromFileTimeUtc(
                c.Result.OsProcessCreatedUtcFileTime);
            Need(t<=DateTime.UtcNow.AddMinutes(1) &&
                t>DateTime.UtcNow.AddMinutes(-5),"kernel creation-time");
            NoAuthority(c.Result);
        });
        Run("different-process-OS-token-SID-matches-connecting-client",()=>
        {
            var c=SeparateClient();
            Need(c.Result.KernelProcessObserved,"OS client observed");
            using(var local=WindowsIdentity.GetCurrent())
                Need(String.Equals(c.Result.OsProcessTokenSid,
                    local.User.Value,StringComparison.Ordinal),
                    "kernel process user identity");
            NoAuthority(c.Result);
        });
        Run("identification-only-never-grants-consent",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Identification);
            NoAuthority(o);
        });
        Run("caller-cannot-supply-PID-or-image-path",()=>
        {
            var m=typeof(WindowsPipeClientProcessProvenance).GetMethod(
                "ObserveAfterClientWrite",BindingFlags.Static|
                BindingFlags.NonPublic);
            Need(m!=null,"OS observer exists");
            var p=m.GetParameters();
            Need(p.Length==1 &&
                p[0].ParameterType==typeof(NamedPipeServerStream),
                "no user-supplied PID path signer boolean");
        });
        Run("real-OS-image-path-is-not-code-signing",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.KernelProcessObserved,"real image");
            Need(!o.SignedTrustedConsentImageVerified,"signature unverified");
        });
        Run("real-OS-process-does-not-prove-human-click",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.KernelProcessObserved,"real process");
            Need(!o.ExplicitHumanConsentVerified,"no clicked approval");
        });
        Run("no-durable-oneuse-grant-or-effect-authority",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.KernelProcessObserved,"real process");
            Need(!o.ProtectedOneUseGrantIssued &&
                !o.NativeCredentialEffectAllowed,"no grant or effect");
        });
        Run("native-interop-only-queries-process-not-WinCred",()=>
        {
            foreach(var m in typeof(WindowsPipeClientProcessProvenance).
                GetMethods(BindingFlags.Static|BindingFlags.Public|
                    BindingFlags.NonPublic|BindingFlags.DeclaredOnly))
            {
                var d=(DllImportAttribute)Attribute.GetCustomAttribute(
                    m,typeof(DllImportAttribute));
                if(d==null)continue;
                string n=String.IsNullOrWhiteSpace(d.EntryPoint)?
                    m.Name:d.EntryPoint;
                Need(n!="CredWriteW" && n!="CredReadW" &&
                    n!="CredDeleteW" && n!="WinVerifyTrust" &&
                    n!="CreateServiceW" && n!="WriteFile" &&
                    n!="RegSetValueExW","query-only native interop");
            }
        });
        Run("P112-candidate-and-original-service-release-held",()=>
        {
            Need(!ServiceGate.LiveEligible(),"installed source release hold");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "old WinCred/effect disabled");
            using(var host=new CustodyService())
                Need(!host.AuthenticatedConsentAvailable &&
                    !host.NativeEffectEnabled &&
                    !host.ProductionReleaseEligible,"no live consent");
        });

        Console.WriteLine("P114_REAL_WINDOWS_PROCESS_PROVENANCE_CASES_PASSED="+passed);
        Console.WriteLine("P114_REAL_WINDOWS_PROCESS_PROVENANCE_CASES_FAILED="+failed);
        Console.WriteLine("P114_CROSS_PROCESS_KERNEL_PID_IMAGE_TOKEN=REAL_WINDOWS_APIS");
        Console.WriteLine("P114_SIGNED_CONSENT_IMAGE=NOT_VERIFIED");
        Console.WriteLine("P114_TRUSTED_PUBLISHER_AND_FILE_HANDLE_BINDING=NOT_IMPLEMENTED");
        Console.WriteLine("P114_HUMAN_APPROVAL_AND_ONEUSE_GRANT=NOT_IMPLEMENTED");
        Console.WriteLine("P114_WIN_CRED_EFFECT_AUTHORITY=NONE");
        Console.WriteLine("P114_P96_LEGACY_RACE=STILL_OPEN");
        Console.WriteLine("P114_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14 && failed==0?0:1;
    }
}
