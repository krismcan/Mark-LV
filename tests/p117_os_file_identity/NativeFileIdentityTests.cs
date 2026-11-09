// P117 real Windows FILE_ID_INFO (128-bit) and resolved handle path
// review-only native tests. All file writes occur only in isolated
// unprivileged GitHub-hosted Windows temporary test directory.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P117NativeFileIdentityReviewTests
{
    private static int passed, failed;
    private static void Need(bool b,string message)
    {if(!b)throw new InvalidOperationException("P117 "+message);}
    private static void Run(string name,Action test)
    {
        try{test();++passed;Console.WriteLine("PASS "+name);}
        catch(Exception e){++failed;Console.WriteLine("FAIL "+name+" "+e.GetType().Name);}
    }
    private static void NoAuthority(OsFileIdentityReviewObservation o)
    {
        Need(o!=null,"observation exists");
        Need(!o.MappedImageSectionBoundToInspectedFile,"no mapped section link");
        Need(!o.ApprovedPublisherTrustAnchorConfigured,"no signer anchor");
        Need(!o.SignedTrustedConsentImageVerified,"no trusted consent UI");
        Need(!o.ExplicitHumanConsentVerified,"no user click");
        Need(!o.ProtectedOneUseGrantIssued,"no durable one-use");
        Need(!o.NativeCredentialEffectAllowed,"no WinCred effect");
        Need(!o.ToString().Contains("S-1-"),"no identity in log");
        Need(!o.ToString().Contains(":\\"),"no path in log");
    }
    private static string TemporaryName()
    {return Path.Combine(Path.GetTempPath(),
        "nayeon-c1-p117-file-"+Guid.NewGuid().ToString("N")+".tmp");}
    private static void WithTempFile(byte[] contents,Action<string> test)
    {
        var path=TemporaryName();
        try{File.WriteAllBytes(path,contents);test(path);}
        finally{if(File.Exists(path))File.Delete(path);}
    }
    private static string NewPipe()
    {return "nayeon-c1-p117-pipe-"+Guid.NewGuid().ToString("N");}
    private static NamedPipeServerStream Server(string name)
    {
        using(var id=WindowsIdentity.GetCurrent())
        {
            Need(id.User!=null && !id.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"test not LocalSystem");
            var rules=new PipeSecurity();
            rules.SetAccessRuleProtection(true,false);
            rules.AddAccessRule(new PipeAccessRule(id.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,rules);
        }
    }
    private static OsFileIdentityReviewObservation SameProcess()
    {
        string name=NewPipe();
        using(var server=Server(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.Out,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                Need(pending.AsyncWaitHandle.WaitOne(5000),"connected");
                server.EndWaitForConnection(pending);
                client.WriteByte(0x43);client.Flush();
                Need(server.ReadByte()==0x43,"handshake");
                return WindowsPipeClientFileIdentityReview.
                    ObserveConnectedClientFileOnly(server);
            }
        }
    }
    private static OsFileIdentityReviewObservation SeparateProcess()
    {
        string name=NewPipe();
        using(var server=Server(name))
        {
            string exe=Path.GetFullPath(Assembly.GetExecutingAssembly().Location);
            var start=new ProcessStartInfo(exe,"--p117-child "+name);
            start.UseShellExecute=false;start.CreateNoWindow=true;
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var child=Process.Start(start))
            {
                Need(child!=null&&child.Id>0,"real child");
                try
                {
                    Need(pending.AsyncWaitHandle.WaitOne(6000),"child connected");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"child byte");
                    var o=WindowsPipeClientFileIdentityReview.
                        ObserveConnectedClientFileOnly(server);
                    server.WriteByte(0x42);server.Flush();
                    Need(child.WaitForExit(5000)&&child.ExitCode==0,
                        "child clean exit");
                    using(var self=Process.GetCurrentProcess())
                        Need(child.Id!=self.Id,"different process");
                    return o;
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
                !name.StartsWith("nayeon-c1-p117-pipe-",
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
        if(args!=null && args.Length==2 && args[0]=="--p117-child")
            return Child(args[1]);

        Run("null-file-path-fail-closed",()=>
        {
            var o=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(null);
            Need(!o.NativeFileObjectObserved,"null");
            NoAuthority(o);
        });
        Run("empty-file-path-fail-closed",()=>
        {
            var o=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly("");
            Need(!o.NativeFileObjectObserved,"empty");
            NoAuthority(o);
        });
        Run("whitespace-file-path-fail-closed",()=>
        {
            var o=WindowsPipeClientFileIdentityReview.
                ObserveFilePathOnly("    ");
            Need(!o.NativeFileObjectObserved,"whitespace");
            NoAuthority(o);
        });
        Run("relative-file-path-fail-closed",()=>
        {
            var o=WindowsPipeClientFileIdentityReview.
                ObserveFilePathOnly("forged-consent.exe");
            Need(!o.NativeFileObjectObserved,"relative");
            NoAuthority(o);
        });
        Run("missing-file-fail-closed",()=>
        {
            var o=WindowsPipeClientFileIdentityReview.
                ObserveFilePathOnly(TemporaryName());
            Need(!o.NativeFileObjectObserved,"missing");
            NoAuthority(o);
        });
        Run("directory-path-not-an-executable-file-object",()=>
        {
            var o=WindowsPipeClientFileIdentityReview.
                ObserveFilePathOnly(Path.GetTempPath());
            Need(!o.NativeFileObjectObserved,"directory");
            NoAuthority(o);
        });
        Run("real-Windows-128-bit-file-id-observed",()=>
        {
            WithTempFile(new byte[]{1,2,3},p=>
            {
                var o=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p);
                Need(o.NativeFileObjectObserved &&
                    o.OsFileId128Hex!=null&&o.OsFileId128Hex.Length==32,
                    "native 16-byte ID");
                NoAuthority(o);
            });
        });
        Run("same-file-opened-twice-has-stable-volume-id",()=>
        {
            WithTempFile(new byte[]{9,8,7},p=>
            {
                var a=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p);
                var b=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p);
                Need(a.NativeFileObjectObserved&&b.NativeFileObjectObserved &&
                    a.OsVolumeSerialNumber==b.OsVolumeSerialNumber &&
                    String.Equals(a.OsFileId128Hex,b.OsFileId128Hex,
                        StringComparison.Ordinal),"same OS file identity");
                NoAuthority(a);NoAuthority(b);
            });
        });
        Run("two-live-distinct-files-have-different-IDs",()=>
        {
            WithTempFile(new byte[]{0x43},p1=>
                WithTempFile(new byte[]{0x42},p2=>
                {
                    var a=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p1);
                    var b=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p2);
                    Need(a.NativeFileObjectObserved&&b.NativeFileObjectObserved,
                        "both OS files");
                    Need(a.OsVolumeSerialNumber!=b.OsVolumeSerialNumber ||
                        !String.Equals(a.OsFileId128Hex,b.OsFileId128Hex,
                            StringComparison.Ordinal),"different file object IDs");
                    NoAuthority(a);NoAuthority(b);
                }));
        });
        Run("zero-byte-file-identity-does-not-mean-signer",()=>
        {
            WithTempFile(new byte[0],p=>
            {
                var o=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p);
                Need(o.NativeFileObjectObserved,"zero length file object");
                NoAuthority(o);
            });
        });
        Run("native-resolved-file-path-flag-not-consent",()=>
        {
            WithTempFile(new byte[]{0x01},p=>
            {
                var o=WindowsPipeClientFileIdentityReview.ObserveFilePathOnly(p);
                Need(o.NativeFileObjectObserved &&
                    o.OsResolvedHandlePathObserved,"native handle path");
                NoAuthority(o);
            });
        });
        Run("null-and-disconnected-pipe-fail-closed",()=>
        {
            var a=WindowsPipeClientFileIdentityReview.
                ObserveConnectedClientFileOnly(null);
            Need(!a.NativeFileObjectObserved,"null pipe");
            NoAuthority(a);
            using(var server=Server(NewPipe()))
            {
                var b=WindowsPipeClientFileIdentityReview.
                    ObserveConnectedClientFileOnly(server);
                Need(!b.NativeFileObjectObserved,"no connected client");
                NoAuthority(b);
            }
        });
        Run("real-same-process-pipe-executable-file-ID",()=>
        {
            var o=SameProcess();
            Need(o.NativeFileObjectObserved &&
                o.ConnectedPipeClientObserved,"same process image file");
            NoAuthority(o);
        });
        Run("real-different-process-pipe-file-ID-no-approval",()=>
        {
            var o=SeparateProcess();
            Need(o.NativeFileObjectObserved &&
                o.ConnectedPipeClientObserved,"actual child OS file");
            NoAuthority(o);
            Need(!ServiceGate.LiveEligible(),"original disabled");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "native effect disabled");
        });

        Console.WriteLine("P117_REAL_WINDOWS_FILE_ID_CASES_PASSED="+passed);
        Console.WriteLine("P117_REAL_WINDOWS_FILE_ID_CASES_FAILED="+failed);
        Console.WriteLine("P117_OS_FILE_ID_INFO_128=REAL_WINDOWS_API");
        Console.WriteLine("P117_MAPPED_IMAGE_TO_FILE_ID_BINDING=NOT_PROVEN");
        Console.WriteLine("P117_APPROVED_SIGNED_CONSENT_PUBLISHER=ABSENT");
        Console.WriteLine("P117_HUMAN_APPROVAL_ONEUSE_NATIVE_EFFECT=ABSENT");
        Console.WriteLine("P117_ORIGINAL_P96_RACE=OPEN");
        Console.WriteLine("P117_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14&&failed==0?0:1;
    }
}
