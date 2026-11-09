// P116 unprivileged Windows Authenticode negative evidence.
// Native signature validation is observational; there is NO publisher pin,
// trusted consent UI, user click, protected one-use grant or WinCred dispatch.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P116WintrustNativeNegativeTests
{
    private static int passed, failed;
    private static void Need(bool yes,string why)
    { if(!yes)throw new InvalidOperationException("P116 "+why); }
    private static void Run(string name,Action test)
    {
        try {test();++passed;Console.WriteLine("PASS "+name);}
        catch(Exception ex)
        {++failed;Console.WriteLine("FAIL "+name+" "+ex.GetType().Name);}
    }
    private static void NoAuthority(OsWintrustReviewObservation o)
    {
        Need(o!=null,"non-null observation");
        Need(!o.ApprovedPublisherPinConfigured,"no approved signer anchor");
        Need(!o.LoadedProcessImageFileIdentityBound,"no loaded image binding");
        Need(!o.SignedTrustedConsentImageVerified,"no signed installed UI trust");
        Need(!o.TrustedInteractiveDesktopVerified,"no desktop proof");
        Need(!o.ExplicitHumanConsentVerified,"no actual human click");
        Need(!o.ProtectedOneUseGrantIssued,"no durable consumed oneuse");
        Need(!o.NativeCredentialEffectAllowed,"no credential mutation");
        Need(!o.ToString().Contains("S-1-"),"no SID in log");
        Need(!o.ToString().Contains(":\\"),"no file path in log");
    }
    private static string TestExe()
    {return Path.GetFullPath(Assembly.GetExecutingAssembly().Location);}
    private static string NewName()
    {return "nayeon-c1-p116-test-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var identity=WindowsIdentity.GetCurrent())
        {
            Need(identity.User!=null &&
                !identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid),
                "must not run as LocalSystem");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(identity.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }
    private static OsWintrustReviewObservation SameProcess()
    {
        string name=NewName();
        using(var server=Server(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.Out,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                Need(pending.AsyncWaitHandle.WaitOne(5000),"pipe connected");
                server.EndWaitForConnection(pending);
                client.WriteByte(0x43);client.Flush();
                Need(server.ReadByte()==0x43,"nonsecret byte received");
                return WindowsWintrustFilePolicyReview.
                    ObserveConnectedClientFilePolicyOnly(server);
            }
        }
    }
    private static OsWintrustReviewObservation SeparateProcess()
    {
        string name=NewName();
        using(var server=Server(name))
        {
            string exe=TestExe();
            var start=new ProcessStartInfo(exe,"--p116-child "+name);
            start.UseShellExecute=false;start.CreateNoWindow=true;
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var child=Process.Start(start))
            {
                Need(child!=null && child.Id>0,"real child process");
                try
                {
                    Need(pending.AsyncWaitHandle.WaitOne(6000),"child connected");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"child handshake");
                    var result=WindowsWintrustFilePolicyReview.
                        ObserveConnectedClientFilePolicyOnly(server);
                    server.WriteByte(0x42);server.Flush();
                    Need(child.WaitForExit(5000) && child.ExitCode==0,"child exited");
                    using(var self=Process.GetCurrentProcess())
                        Need(child.Id!=self.Id,"different OS process");
                    return result;
                }
                finally{if(!child.HasExited)child.Kill();}
            }
        }
    }
    private static int Child(string name)
    {
        try
        {
            if(String.IsNullOrWhiteSpace(name) ||
                !name.StartsWith("nayeon-c1-p116-test-",
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
    private static string Temp(string ext)
    {return Path.Combine(Path.GetTempPath(),NewName()+ext);}
    private static void WithTempFile(string ext,byte[] bytes,
        Action<string> act)
    {
        string path=Temp(ext);
        try
        {
            File.WriteAllBytes(path,bytes);
            act(path);
        }
        finally{if(File.Exists(path))File.Delete(path);}
    }
    private static void NativeRejected(string path)
    {
        var result=WindowsWintrustFilePolicyReview.
            ObserveFilePolicyOnly(path);
        Need(result.NativePolicyAttempted,"native WinVerifyTrust attempted");
        Need(!result.NativePolicyAccepted &&
            result.State==OsWintrustReviewState.NativePolicyRejected,
            "unsigned content rejected by native Authenticode policy");
        NoAuthority(result);
    }
    public static int Main(string[] args)
    {
        if(args!=null&&args.Length==2&&args[0]=="--p116-child")
            return Child(args[1]);

        Run("null-image-input-fail-closed",()=>
        {
            var o=WindowsWintrustFilePolicyReview.ObserveFilePolicyOnly(null);
            Need(o.State==OsWintrustReviewState.Unavailable,"null");
            NoAuthority(o);
        });
        Run("empty-image-input-fail-closed",()=>
        {
            var o=WindowsWintrustFilePolicyReview.ObserveFilePolicyOnly("");
            Need(o.State==OsWintrustReviewState.Unavailable,"empty");
            NoAuthority(o);
        });
        Run("whitespace-image-input-fail-closed",()=>
        {
            var o=WindowsWintrustFilePolicyReview.ObserveFilePolicyOnly("   ");
            Need(o.State==OsWintrustReviewState.Unavailable,"whitespace");
            NoAuthority(o);
        });
        Run("unrooted-path-fail-closed",()=>
        {
            var o=WindowsWintrustFilePolicyReview.
                ObserveFilePolicyOnly("not-an-authority.exe");
            Need(o.State==OsWintrustReviewState.Unavailable,"relative");
            NoAuthority(o);
        });
        Run("missing-native-file-fail-closed",()=>
        {
            var o=WindowsWintrustFilePolicyReview.
                ObserveFilePolicyOnly(Temp(".missing"));
            Need(o.State==OsWintrustReviewState.Unavailable,"missing");
            NoAuthority(o);
        });
        Run("directory-path-fail-closed",()=>
        {
            var o=WindowsWintrustFilePolicyReview.
                ObserveFilePolicyOnly(Path.GetTempPath());
            Need(o.State==OsWintrustReviewState.Unavailable,"directory");
            NoAuthority(o);
        });
        Run("zero-byte-file-fail-closed",()=>
        {
            WithTempFile(".bin",new byte[0],p=>
            {
                var o=WindowsWintrustFilePolicyReview.ObserveFilePolicyOnly(p);
                Need(o.State==OsWintrustReviewState.Unavailable,"zero length");
                NoAuthority(o);
            });
        });
        Run("real-native-wintrust-rejects-unsigned-data",()=>
        {
            WithTempFile(".bin",new byte[]{1,2,3,4,5,6},NativeRejected);
        });
        Run("exe-extension-does-not-forge-signature",()=>
        {
            WithTempFile(".exe",new byte[]{0x4d,0x5a,0x43,0x31},NativeRejected);
        });
        Run("real-unsigned-compiled-executable-rejected",()=>
        {
            Need(File.Exists(TestExe()),"native test EXE exists");
            NativeRejected(TestExe());
        });
        Run("native-attempt-cannot-configure-publisher-pin",()=>
        {
            var o=WindowsWintrustFilePolicyReview.
                ObserveFilePolicyOnly(TestExe());
            Need(o.NativePolicyAttempted,"native policy called");
            NoAuthority(o);
        });
        Run("null-or-disconnected-pipe-never-establishes-origin",()=>
        {
            var a=WindowsWintrustFilePolicyReview.
                ObserveConnectedClientFilePolicyOnly(null);
            Need(a.State==OsWintrustReviewState.Unavailable,"null pipe");
            NoAuthority(a);
            using(var server=Server(NewName()))
            {
                var b=WindowsWintrustFilePolicyReview.
                    ObserveConnectedClientFilePolicyOnly(server);
                Need(b.State==OsWintrustReviewState.Unavailable,"no client");
                NoAuthority(b);
            }
        });
        Run("real-same-process-pipe-image-WinTrust-no-consent",()=>
        {
            var o=SameProcess();
            Need(o.ConnectedPipeClientObserved &&
                o.NativePolicyAttempted &&
                !o.NativePolicyAccepted,
                "unsigned live image observed, not trusted");
            NoAuthority(o);
        });
        Run("real-cross-process-pipe-image-WinTrust-no-consent",()=>
        {
            var o=SeparateProcess();
            Need(o.ConnectedPipeClientObserved &&
                o.NativePolicyAttempted &&
                !o.NativePolicyAccepted,
                "unsigned child image observed, not trusted");
            NoAuthority(o);
            Need(!ServiceGate.LiveEligible(),"original service still held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "old native effect still disabled");
        });
        Console.WriteLine("P116_REAL_WINDOWS_WINTRUST_NEGATIVE_CASES_PASSED="+passed);
        Console.WriteLine("P116_REAL_WINDOWS_WINTRUST_NEGATIVE_CASES_FAILED="+failed);
        Console.WriteLine("P116_NATIVE_WINVERIFYTRUST=EXECUTED_UNSIGNED_NEGATIVE");
        Console.WriteLine("P116_TRUSTED_PUBLISHER_PIN=NOT_CONFIGURED");
        Console.WriteLine("P116_LOADED_IMAGE_IDENTITY_BINDING=NOT_PROVEN");
        Console.WriteLine("P116_INTERACTIVE_HUMAN_CLICK_ONEUSE=NOT_IMPLEMENTED");
        Console.WriteLine("P116_ORIGINAL_P96_RACE=OPEN");
        Console.WriteLine("P116_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14&&failed==0?0:1;
    }
}
