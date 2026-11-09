// P115 REAL Windows OS pipe session and process-token integrity readback.
// A native signal is NOT a signed installed consent window or human approval.
// Only random, ACL-restricted, unprivileged local test pipes are created here.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P115NativePipeSessionIntegrityTests
{
    private static int passed, failed;
    private static void Need(bool ok,string reason)
    { if(!ok)throw new InvalidOperationException("P115 "+reason); }
    private static void Run(string name,Action test)
    {
        try { test(); ++passed; Console.WriteLine("PASS "+name); }
        catch(Exception ex)
        { ++failed; Console.WriteLine("FAIL "+name+" "+ex.GetType().Name); }
    }
    private static void NoAuthority(OsPipeClientSessionIntegrity value)
    {
        Need(!value.TrustedInteractiveDesktopVerified,"desktop never trusted");
        Need(!value.SignedTrustedConsentImageVerified,"signer never verified");
        Need(!value.ExplicitHumanConsentVerified,"human never verified");
        Need(!value.ProtectedOneUseGrantIssued,"one-use not issued");
        Need(!value.NativeCredentialEffectAllowed,"WinCred effect not allowed");
        Need(!value.ToString().Contains("S-1-"),"no SID in string");
    }
    private static string NewPipe()
    { return "nayeon-c1-p115-test-"+Guid.NewGuid().ToString("N"); }
    private static NamedPipeServerStream Server(string name)
    {
        using(var identity=WindowsIdentity.GetCurrent())
        {
            Need(identity.User!=null &&
                !identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid),
                "native tests must not be LocalSystem");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(identity.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }
    private static OsPipeClientSessionIntegrity SameProcess(
        TokenImpersonationLevel level)
    {
        var name=NewPipe();
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
                Need(server.ReadByte()==0x43,"handshake");
                return WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(server);
            }
        }
    }
    private sealed class CrossProcess
    {
        internal uint Pid;
        internal uint Session;
        internal OsPipeClientSessionIntegrity Observation;
    }
    private static CrossProcess DifferentProcess()
    {
        string name=NewPipe();
        using(var server=Server(name))
        {
            string exe=Path.GetFullPath(Assembly.GetExecutingAssembly().Location);
            Need(File.Exists(exe),"compiled child exe");
            var info=new ProcessStartInfo(exe,"--p115-child "+name);
            info.UseShellExecute=false;
            info.CreateNoWindow=true;
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var child=Process.Start(info))
            {
                Need(child!=null && child.Id>0,"child started");
                try
                {
                    uint pid=(uint)child.Id;
                    uint session=(uint)child.SessionId;
                    Need(pending.AsyncWaitHandle.WaitOne(6000),"child connected");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"child handshake");
                    var observed=
                        WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(server);
                    server.WriteByte(0x42);server.Flush();
                    Need(child.WaitForExit(5000) && child.ExitCode==0,
                        "child clean exit");
                    return new CrossProcess {
                        Pid=pid, Session=session, Observation=observed
                    };
                }
                finally { if(!child.HasExited)child.Kill(); }
            }
        }
    }
    private static int Child(string name)
    {
        try
        {
            if(String.IsNullOrWhiteSpace(name) ||
                !name.StartsWith("nayeon-c1-p115-test-",StringComparison.Ordinal))
                return 12;
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                client.WriteByte(0x43);client.Flush();
                return client.ReadByte()==0x42?0:13;
            }
        }
        catch(Exception) { return 14; }
    }
    public static int Main(string[] args)
    {
        if(args!=null && args.Length==2 && args[0]=="--p115-child")
            return Child(args[1]);

        Run("null-pipe-fail-closed",()=>
        {
            var o=WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(null);
            Need(!o.SessionIntegrityObserved,"null denied");
            NoAuthority(o);
        });
        Run("disconnected-pipe-fail-closed",()=>
        {
            using(var server=Server(NewPipe()))
            {
                var o=WindowsPipeClientSessionIntegrity.ObserveAfterClientWrite(server);
                Need(!o.SessionIntegrityObserved,"disconnected denied");
                NoAuthority(o);
            }
        });
        Run("real-Windows-same-process-token-session",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.SessionIntegrityObserved,"real session observed");
            NoAuthority(o);
        });
        Run("real-pipe-session-equals-process-token-session",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.SessionIntegrityObserved &&
                o.OsPipeSessionId==o.OsTokenSessionId,"OS session agreement");
            NoAuthority(o);
        });
        Run("real-Windows-client-session-equals-runner-session",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            using(var process=Process.GetCurrentProcess())
                Need(o.SessionIntegrityObserved &&
                    o.OsPipeSessionId==(uint)process.SessionId,
                    "Windows runner actual session");
            NoAuthority(o);
        });
        Run("real-Windows-token-integrity-RID",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.SessionIntegrityObserved &&
                o.OsTokenIntegrityRid<=32768,
                "valid Windows mandatory label RID");
            NoAuthority(o);
        });
        Run("actual-child-client-is-separate-process",()=>
        {
            var c=DifferentProcess();
            using(var self=Process.GetCurrentProcess())
                Need(c.Observation.SessionIntegrityObserved &&
                    c.Pid!=(uint)self.Id &&
                    c.Observation.OsClientProcessId==c.Pid,
                    "kernel client PID separate");
            NoAuthority(c.Observation);
        });
        Run("real-child-pipe-session-equals-token-session",()=>
        {
            var c=DifferentProcess();
            Need(c.Observation.SessionIntegrityObserved &&
                c.Observation.OsPipeSessionId==c.Observation.OsTokenSessionId,
                "cross-process session sources agree");
            NoAuthority(c.Observation);
        });
        Run("real-child-session-equals-OS-process-session",()=>
        {
            var c=DifferentProcess();
            Need(c.Observation.SessionIntegrityObserved &&
                c.Observation.OsPipeSessionId==c.Session,
                "cross-process actual session");
            NoAuthority(c.Observation);
        });
        Run("identification-only-cannot-approve",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Identification);
            NoAuthority(o);
        });
        Run("caller-cannot-submit-session-integrity-or-PID",()=>
        {
            var m=typeof(WindowsPipeClientSessionIntegrity).GetMethod(
                "ObserveAfterClientWrite",BindingFlags.Static|
                BindingFlags.NonPublic);
            Need(m!=null && m.GetParameters().Length==1 &&
                m.GetParameters()[0].ParameterType==typeof(NamedPipeServerStream),
                "only OS-backed pipe input");
        });
        Run("session-observation-never-becomes-interactive-desktop",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            Need(o.SessionIntegrityObserved &&
                !o.TrustedInteractiveDesktopVerified &&
                !o.SignedTrustedConsentImageVerified,"no trusted signer/desktop");
        });
        Run("no-oneuse-consent-native-effect-or-privileged-writes",()=>
        {
            var o=SameProcess(TokenImpersonationLevel.Impersonation);
            NoAuthority(o);
            foreach(var m in typeof(WindowsPipeClientSessionIntegrity).
                GetMethods(BindingFlags.Static|BindingFlags.Public|
                    BindingFlags.NonPublic|BindingFlags.DeclaredOnly))
            {
                var d=(DllImportAttribute)Attribute.GetCustomAttribute(
                    m,typeof(DllImportAttribute));
                if(d==null)continue;
                string name=String.IsNullOrWhiteSpace(d.EntryPoint)?m.Name:d.EntryPoint;
                Need(name!="CredWriteW" && name!="CredReadW" &&
                    name!="CredDeleteW" && name!="WinVerifyTrust" &&
                    name!="CreateServiceW" && name!="RegSetValueExW" &&
                    name!="WriteFile","query-only PInvoke");
            }
        });
        Run("original-native-and-P112-candidate-release-held",()=>
        {
            Need(!ServiceGate.LiveEligible(),"original service held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "native effect still disabled");
            using(var host=new CustodyService())
                Need(!host.AuthenticatedConsentAvailable &&
                    !host.NativeEffectEnabled &&
                    !host.ProductionReleaseEligible,"candidate held");
        });

        Console.WriteLine("P115_OS_PIPE_SESSION_INTEGRITY_CASES_PASSED="+passed);
        Console.WriteLine("P115_OS_PIPE_SESSION_INTEGRITY_CASES_FAILED="+failed);
        Console.WriteLine("P115_WINDOWS_KERNEL_PIPE_AND_TOKEN_SESSION=ACTUAL_OS");
        Console.WriteLine("P115_WINDOWS_PROCESS_TOKEN_INTEGRITY=ACTUAL_OS");
        Console.WriteLine("P115_SIGNED_INSTALLED_UI_AND_DESKTOP=NOT_VERIFIED");
        Console.WriteLine("P115_HUMAN_CONSENT_ONEUSE_GRANT=NOT_IMPLEMENTED");
        Console.WriteLine("P115_LEGACY_P96_RACE=STILL_OPEN");
        Console.WriteLine("P115_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14 && failed==0?0:1;
    }
}
