// P214 — REAL hosted Windows unprivileged process+pipe to original native
// CustodyService denial. 14 cases; no keys, signer enrolment, installs,
// provider, WinCred API, service Main or Code Integrity policy changes.
#if C1_REVIEW_ISOLATED_ASSEMBLY
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P214RealWindowsHostIntegrationTests
{
    private static int passed;
    private static int failed;

    private static void Need(bool ok,string code)
    {
        if(!ok)throw new InvalidOperationException("P214 "+code);
    }

    private static void Run(string name,Action body)
    {
        try
        {
            body();
            ++passed;
            Console.WriteLine("PASS "+name);
        }
        catch(Exception ex)
        {
            ++failed;
            Console.WriteLine("FAIL "+name+" "+ex.GetType().Name);
        }
    }

    private static string Name()
    { return "nayeon-c1-p214-test-"+Guid.NewGuid().ToString("N"); }

    private static NamedPipeServerStream NewServer(string name)
    {
        using(WindowsIdentity user=WindowsIdentity.GetCurrent())
        {
            Need(user.User!=null && !user.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"not LocalSystem");
            PipeSecurity acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(user.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }

    private static ServiceBoundRequestIdentity Claim()
    {
        // Structurally valid but COMPLETELY UNTRUSTED metadata.
        // The SHA string is a static fixture, NOT an API credential.
        return new ServiceBoundRequestIdentity(
            LedgerOperation.Save,new string('a',32),new string('b',32),
            new string('c',64),DateTime.UtcNow.AddMinutes(1).Ticks,false);
    }

    private static void NoAuthority(P214ActualWindowsHostRefusalObservation o)
    {
        Need(o!=null,"non-null");
        Need(!o.ApprovedInstalledServiceSigner,"no issuer");
        Need(!o.TrustedClientImageSectionAttested,"no loaded image proof");
        Need(!o.TrustedInteractiveHumanConsent,"no user presence");
        Need(!o.ProtectedOneUseApprovalIssued,"no grant");
        Need(!o.MachineCodeIntegrityAdmitted,"no machine policy");
        Need(!o.LegacyP132PythonEffectEliminated,"P132 bypass remains");
        Need(!o.CredentialEffectAuthorized,"no effect");
        Need(!o.RealKeyEligible,"real-key NO GO");
        Need(!o.ProductionReleaseEligible,"production HOLD");
        Need(!o.ToString().Contains("S-1-"),"no SID in logs");
    }

    private static P214ActualWindowsHostRefusalObservation Same(
        CustodyService host,ServiceBoundRequestIdentity untrusted)
    {
        string name=Name();
        using(var server=NewServer(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                Need(pending.AsyncWaitHandle.WaitOne(5000),"same connect");
                server.EndWaitForConnection(pending);
                client.WriteByte(0x43);client.Flush();
                Need(server.ReadByte()==0x43,"same test byte");
                return P214ActualWindowsHostReadOnlyIntegration.
                    ObserveAndRefuse(server,host,untrusted);
            }
        }
    }

    private static int Child(string name)
    {
        if(String.IsNullOrWhiteSpace(name) ||
           !name.StartsWith("nayeon-c1-p214-test-",
             StringComparison.Ordinal))return 18;
        try
        {
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                client.WriteByte(0x43);client.Flush();
                return client.ReadByte()==0x42 ? 0 : 19;
            }
        }
        catch(Exception){return 20;}
    }

    private static P214ActualWindowsHostRefusalObservation Cross(
        CustodyService host,ServiceBoundRequestIdentity claim)
    {
        string name=Name();
        using(var server=NewServer(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            string exe=Assembly.GetExecutingAssembly().Location;
            var start=new ProcessStartInfo(exe,"--p214-child "+name);
            start.UseShellExecute=false;
            start.CreateNoWindow=true;
            using(var child=Process.Start(start))
            {
                Need(child!=null && child.Id>0,"child start");
                try
                {
                    Need(pending.AsyncWaitHandle.WaitOne(6000),"cross connect");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"cross test byte");
                    var observed=P214ActualWindowsHostReadOnlyIntegration.
                        ObserveAndRefuse(server,host,claim);
                    server.WriteByte(0x42);server.Flush();
                    Need(child.WaitForExit(5000) && child.ExitCode==0,
                         "child end");
                    using(var self=Process.GetCurrentProcess())
                        Need(self.Id!=child.Id,"independent real OS process");
                    return observed;
                }
                finally
                {
                    if(!child.HasExited)child.Kill();
                }
            }
        }
    }

    public static int Main(string[] args)
    {
        if(args!=null && args.Length==2 && args[0]=="--p214-child")
            return Child(args[1]);
        if(args!=null && args.Length>0)return 30;

        Run("01-no-service-and-no-pipe-no-grant",delegate
        {
            var x=P214ActualWindowsHostReadOnlyIntegration.
                ObserveAndRefuse(null,null,null);
            Need(!x.OsPeerIdentitySignalsAgree,"no peer");
            Need(x.TerminalResult==CustodyOutcome.Denied,"no actor");
            NoAuthority(x);
        });
        Run("02-unconnected-pipe-real-host-denied",delegate
        {
            using(var server=NewServer(Name()))
            {
                var host=new CustodyService();
                var x=P214ActualWindowsHostReadOnlyIntegration.
                    ObserveAndRefuse(server,host,null);
                Need(!x.OsImpersonatedPeerObserved,"no connected client");
                Need(x.TerminalResult==CustodyOutcome.Denied,"denied");
                Need(host.TerminalEffectRefusals==1,"real host invoked");
                NoAuthority(x);
            }
        });
        Run("03-original-service-start-and-effect-holds",delegate
        {
            var host=new CustodyService();
            Need(!ServiceGate.LiveEligible(),"live service hold");
            Need(!host.NativeEffectEnabled,"native effect hold");
            Need(!host.AuthenticatedConsentAvailable,"no issued consent");
            Need(!host.ProductionReleaseEligible,"release hold");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled(),
                 "legacy native effect unavailable");
        });
        Run("04-real-same-process-pipe-token-observed",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(o.OsImpersonatedPeerObserved,"OS impersonation");
            Need(o.OsClientProcessObserved,"OS process provenance");
            NoAuthority(o);
        });
        Run("05-real-same-process-session-integrity-agree",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(o.OsSessionAndIntegrityObserved,"session");
            Need(o.OsPeerIdentitySignalsAgree,"OS signals aligned");
            NoAuthority(o);
        });
        Run("06-real-native-WinTrust-file-policy-attempted",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(o.OsFileSignaturePolicyAttempted,"native WinVerifyTrust");
            Need(!o.OsFileSignaturePolicyAccepted,
                 "unsigned review binary rejected");
            NoAuthority(o);
        });
        Run("07-real-cross-process-pipe-OS-evidence",delegate
        {
            var o=Cross(new CustodyService(),null);
            Need(o.OsImpersonatedPeerObserved &&
                 o.OsClientProcessObserved &&
                 o.OsSessionAndIntegrityObserved &&
                 o.OsPeerIdentitySignalsAgree,"real cross-process OS signals");
            NoAuthority(o);
        });
        Run("08-cross-process-unsigned-image-never-consent",delegate
        {
            var o=Cross(new CustodyService(),null);
            Need(o.OsFileSignaturePolicyAttempted,"real cross-image WinTrust");
            Need(!o.OsFileSignaturePolicyAccepted,"no signed broker");
            Need(o.TerminalResult==CustodyOutcome.Denied,
                 "original service refused terminal");
            NoAuthority(o);
        });
        Run("09-forged-structurally-valid-claim-from-real-peer-denied",delegate
        {
            var host=new CustodyService();
            var o=Cross(host,Claim());
            Need(o.OsPeerIdentitySignalsAgree,"OS peer observed");
            Need(o.TerminalResult==CustodyOutcome.Denied,"terminal refused");
            Need(o.ClaimedRequestResult==CustodyOutcome.Denied,
                 "claimed approval always denied");
            Need(!host.NativeEffectEnabled,"no actor switch");
            NoAuthority(o);
        });
        Run("10-replay-shaped-metadata-never-grants",delegate
        {
            var host=new CustodyService();
            ServiceBoundRequestIdentity c=Claim();
            Need(host.RefuseBoundPendingOperation(c)==CustodyOutcome.Denied,
                 "first refusal");
            Need(host.RefuseBoundPendingOperation(c)==CustodyOutcome.Denied,
                 "second refusal");
            Need(host.StructurallyRepeatedRequestCount>=1,
                 "original replay observation");
            Need(!host.NativeEffectEnabled,"no effect");
        });
        Run("11-invalid-untrusted-request-does-not-issue-ticket",delegate
        {
            bool refused=false;
            try
            {
                new ServiceBoundRequestIdentity(LedgerOperation.Save,
                    "not-a-session",new string('b',32),
                    new string('c',64),DateTime.UtcNow.AddMinutes(1).Ticks,
                    false);
            }
            catch(ArgumentException){refused=true;}
            Need(refused,"malformed input");
            Need(!new CustodyService().NativeEffectEnabled,"no effect");
        });
        Run("12-revoked-real-host-refuses-even-observed-OS-peer",delegate
        {
            var host=new CustodyService();
            host.RevokePendingAdmission();
            var o=Same(host,null);
            Need(o.OsPeerIdentitySignalsAgree,"OS evidence not authority");
            Need(o.TerminalResult==CustodyOutcome.Denied,"revoked");
            Need(host.PendingAdmissionRevoked,"still revoked");
            NoAuthority(o);
        });
        Run("13-faulted-real-host-requires-recovery",delegate
        {
            var host=new CustodyService();
            host.FaultPendingAdmission();
            var o=Same(host,Claim());
            Need(o.TerminalResult==CustodyOutcome.RecoveryRequired,
                 "sticky recovery");
            Need(o.ClaimedRequestResult==CustodyOutcome.RecoveryRequired,
                 "untrusted claim cannot clear recovery");
            Need(host.PendingAdmissionFaulted,"faulted");
            NoAuthority(o);
        });
        Run("14-observed-OS-consent-does-not-enable-real-WinCred",delegate
        {
            var host=new CustodyService();
            var o=Same(host,Claim());
            Need(o.OsPeerIdentitySignalsAgree,"genuine Windows identity");
            Need(o.OsFileSignaturePolicyAttempted,"genuine Windows file policy");
            Need(o.TerminalResult==CustodyOutcome.Denied,
                 "actual C1 host denies terminal");
            Need(o.ClaimedRequestResult==CustodyOutcome.Denied,
                 "actual C1 host denies request");
            Need(host.TerminalEffectRefusals>=1,"host method actually executed");
            Need(host.DeniedPendingRequestCount>=1,"host request actually executed");
            NoAuthority(o);
        });

        Console.WriteLine("P214_REAL_WINDOWS_OS_TO_ACTUAL_NATIVE_C1_HOST_PASS="+passed);
        Console.WriteLine("P214_REAL_WINDOWS_OS_TO_ACTUAL_NATIVE_C1_HOST_FAIL="+failed);
        Console.WriteLine("P214_ACTUAL_CUSTODY_SERVICE_REFUSAL=EXECUTED");
        Console.WriteLine("P214_REAL_WINDOWS_PEER_PROCESS_SESSION_WinTrust=OBSERVED");
        Console.WriteLine("P214_P132_DIRECT_WINCRED=UNMODIFIED");
        Console.WriteLine("P214_TRUSTED_SIGNED_LOCAL_CONSENT=NOT_IMPLEMENTED");
        Console.WriteLine("P214_REAL_KEY=NO_GO|PRODUCTION=HOLD");
        return passed==14&&failed==0 ? 0 : 1;
    }
}
#endif
