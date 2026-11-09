// P118 — actual Windows same-file-handle native OS ID and WinTrust
// denial evidence; unprivileged GitHub-hosted Windows only.
// This is NOT an approved signed app, image-section binding or consent.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P118NativeSameHandleReviewTests
{
    private static int passed,failed;
    private static void Need(bool b,string why)
    {if(!b)throw new InvalidOperationException("P118 "+why);}
    private static void Run(string name,Action test)
    {
        try{test();++passed;Console.WriteLine("PASS "+name);}
        catch(Exception ex)
        {++failed;Console.WriteLine("FAIL "+name+" "+ex.GetType().Name);}
    }
    private static void NoAuthority(OsSameHandleReviewObservation o)
    {
        Need(o!=null,"observation exists");
        Need(!o.ApprovedPublisherTrustAnchorConfigured,"no publisher trust anchor");
        Need(!o.RunningMappedImageIdentityProven,"mapped image not proven");
        Need(!o.TrustedConsentApplicationVerified,"no consent app approval");
        Need(!o.TrustedInteractiveDesktopVerified,"no trusted desktop");
        Need(!o.HumanApprovalVerified,"no human click");
        Need(!o.ProtectedOneUseGrantIssued,"no oneuse permission");
        Need(!o.NativeCredentialEffectAllowed,"no WinCred effect");
        Need(!o.ToString().Contains("S-1-"),"no SID log");
        Need(!o.ToString().Contains(":\\"),"no source path log");
    }
    private static string Temp(string ext)
    {
        return Path.Combine(Path.GetTempPath(),
            "nayeon-p118-"+Guid.NewGuid().ToString("N")+ext);
    }
    private static void WithFile(string extension,byte[] contents,
        Action<string> body)
    {
        string path=Temp(extension);
        try{File.WriteAllBytes(path,contents);body(path);}
        finally{if(File.Exists(path))File.Delete(path);}
    }
    private static OsSameHandleReviewObservation Native(string path)
    {return WindowsSameHandleFilePolicyReview.ObserveFileOnly(path);}

    private static void RealUnsignedFile(string path)
    {
        var o=Native(path);
        Need(o.State==OsSameHandleReviewState.NativeFileAndPolicyObserved &&
            o.NativePolicyAttempted && !o.NativePolicyAccepted &&
            o.SameFileHandleIdStable &&
            o.OsFileId128Hex!=null && o.OsFileId128Hex.Length==32,
            "same physical read-only file handle, real OS unsigned policy");
        NoAuthority(o);
    }

    private static string NewPipe()
    {return "nayeon-p118-pipe-"+Guid.NewGuid().ToString("N");}

    private static NamedPipeServerStream Server(string name)
    {
        using(var id=WindowsIdentity.GetCurrent())
        {
            Need(id.User!=null && !id.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"runner must not be system");
            var acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(
                id.User,PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }

    private static OsSameHandleReviewObservation SameProcess()
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
                return WindowsSameHandleFilePolicyReview.
                    ObserveConnectedClient(server);
            }
        }
    }

    private static OsSameHandleReviewObservation SeparateProcess()
    {
        string name=NewPipe();
        using(var server=Server(name))
        {
            string path=Path.GetFullPath(
                Assembly.GetExecutingAssembly().Location);
            var start=new ProcessStartInfo(path,"--p118-child "+name);
            start.UseShellExecute=false;
            start.CreateNoWindow=true;
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var child=Process.Start(start))
            {
                Need(child!=null && child.Id>0,"child created");
                try
                {
                    Need(pending.AsyncWaitHandle.WaitOne(6000),"child pipe");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"child handshake");
                    var observation=WindowsSameHandleFilePolicyReview.
                        ObserveConnectedClient(server);
                    server.WriteByte(0x42);server.Flush();
                    Need(child.WaitForExit(5000) && child.ExitCode==0,
                        "child exit");
                    using(var self=Process.GetCurrentProcess())
                        Need(child.Id!=self.Id,"real different OS process");
                    return observation;
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
                !name.StartsWith("nayeon-p118-pipe-",
                    StringComparison.Ordinal))return 12;
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                client.WriteByte(0x43);client.Flush();
                return client.ReadByte()==0x42?0:13;
            }
        }
        catch(Exception){return 14;}
    }

    public static int Main(string[] args)
    {
        if(args!=null && args.Length==2 && args[0]=="--p118-child")
            return Child(args[1]);

        Run("null-file-input-fail-closed",()=>
        {
            var o=Native(null);
            Need(o.State==OsSameHandleReviewState.Unavailable,"null denied");
            NoAuthority(o);
        });
        Run("whitespace-file-input-fail-closed",()=>
        {
            var o=Native("  ");
            Need(o.State==OsSameHandleReviewState.Unavailable,"blank denied");
            NoAuthority(o);
        });
        Run("relative-forged-binary-input-fail-closed",()=>
        {
            var o=Native("untrusted-consent-broker.exe");
            Need(o.State==OsSameHandleReviewState.Unavailable,"relative denied");
            NoAuthority(o);
        });
        Run("missing-file-input-fail-closed",()=>
        {
            var o=Native(Temp(".missing"));
            Need(o.State==OsSameHandleReviewState.Unavailable,"missing denied");
            NoAuthority(o);
        });
        Run("directory-not-an-executable-file-fail-closed",()=>
        {
            var o=Native(Path.GetTempPath());
            Need(o.State==OsSameHandleReviewState.Unavailable,"directory denied");
            NoAuthority(o);
        });
        Run("zero-length-file-fail-closed",()=>
        {
            WithFile(".bin",new byte[0],p=>
            {
                var o=Native(p);
                Need(o.State==OsSameHandleReviewState.Unavailable,"empty");
                NoAuthority(o);
            });
        });
        Run("real-Windows-same-handle-ID-and-WinTrust-unsigned-data",()=>
        {
            WithFile(".bin",new byte[]{1,2,3,4,5},RealUnsignedFile);
        });
        Run("forged-EXE-extension-remains-native-policy-rejected",()=>
        {
            WithFile(".exe",new byte[]{0x4d,0x5a,0x43,0x31},
                RealUnsignedFile);
        });
        Run("real-unsigned-compiled-executable-still-rejected",()=>
        {
            string path=Path.GetFullPath(
                Assembly.GetExecutingAssembly().Location);
            Need(File.Exists(path),"native compiled unsigned EXE");
            RealUnsignedFile(path);
        });
        Run("same-OS-file-stable-across-separate-handle-probes",()=>
        {
            WithFile(".bin",new byte[]{0x12,0x13},p=>
            {
                var a=Native(p);
                var b=Native(p);
                Need(a.SameFileHandleIdStable && b.SameFileHandleIdStable &&
                    a.OsVolumeSerialNumber==b.OsVolumeSerialNumber &&
                    String.Equals(a.OsFileId128Hex,b.OsFileId128Hex,
                        StringComparison.Ordinal),"stable same OS file");
                NoAuthority(a);NoAuthority(b);
            });
        });
        Run("two-concurrent-files-have-different-OS-file-IDs",()=>
        {
            WithFile(".bin",new byte[]{0x01},p1=>
                WithFile(".bin",new byte[]{0x02},p2=>
                {
                    var a=Native(p1);var b=Native(p2);
                    Need(a.SameFileHandleIdStable && b.SameFileHandleIdStable &&
                        (a.OsVolumeSerialNumber!=b.OsVolumeSerialNumber ||
                        !String.Equals(a.OsFileId128Hex,b.OsFileId128Hex,
                            StringComparison.Ordinal)),"different OS files");
                    NoAuthority(a);NoAuthority(b);
                }));
        });
        Run("null-and-disconnected-client-pipe-denied",()=>
        {
            var n=WindowsSameHandleFilePolicyReview.
                ObserveConnectedClient(null);
            Need(n.State==OsSameHandleReviewState.Unavailable,"null pipe");
            NoAuthority(n);
            using(var server=Server(NewPipe()))
            {
                var d=WindowsSameHandleFilePolicyReview.
                    ObserveConnectedClient(server);
                Need(d.State==OsSameHandleReviewState.Unavailable,
                    "disconnected pipe");
                NoAuthority(d);
            }
        });
        Run("actual-same-process-OS-peer-and-file-policy-held",()=>
        {
            var o=SameProcess();
            Need(o.OsConnectedClientObserved &&
                o.NativePolicyAttempted && !o.NativePolicyAccepted &&
                o.SameFileHandleIdStable,
                "actual OS same-process file probe");
            NoAuthority(o);
        });
        Run("actual-cross-process-OS-peer-and-file-policy-held",()=>
        {
            var o=SeparateProcess();
            Need(o.OsConnectedClientObserved &&
                o.NativePolicyAttempted && !o.NativePolicyAccepted &&
                o.SameFileHandleIdStable,
                "different OS process native unsigned file observation");
            NoAuthority(o);
            Need(!ServiceGate.LiveEligible(),"P49 service held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 native effects excluded");
        });

        Console.WriteLine("P118_REAL_WINDOWS_SAME_HANDLE_CASES_PASSED="+passed);
        Console.WriteLine("P118_REAL_WINDOWS_SAME_HANDLE_CASES_FAILED="+failed);
        Console.WriteLine("P118_ONE_READ_HANDLE_FILE_ID_AND_WINTRUST=REAL_OS");
        Console.WriteLine("P118_PROCESS_HANDLE_HELD_DURING_FILE_QUERY=REAL_OS");
        Console.WriteLine("P118_MAPPED_IMAGE_FILE_TRUST=NOT_PROVEN");
        Console.WriteLine("P118_APPROVED_PUBLISHER_HUMAN_CONSENT_ONEUSE=ABSENT");
        Console.WriteLine("P118_OLD_P96_RACE=OPEN");
        Console.WriteLine("P118_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14 && failed==0?0:1;
    }
}
