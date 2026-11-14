// P215 genuine Windows current-token + credential session persistence
// CAPABILITY (CredGetSessionTypes), calling actual P214->CustodyService
// terminal refusal. 16 native tests, no credentials, WinCred CRUD,
// service installation, impersonation for writes or key migration.
#if C1_REVIEW_ISOLATED_ASSEMBLY
using System;
using System.Diagnostics;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P215RealWindowsStorePrincipalTests
{
    private static int passed;
    private static int failed;
    private static void Need(bool ok,string reason)
    { if(!ok)throw new InvalidOperationException("P215 "+reason); }

    private static void Run(string label,Action action)
    {
        try {action();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception error)
        {
            ++failed;
            Console.WriteLine("FAIL "+label+" "+error.GetType().Name);
        }
    }

    private static string Name()
    { return "nayeon-c1-p215-test-"+Guid.NewGuid().ToString("N"); }

    private static NamedPipeServerStream Server(string name)
    {
        using(WindowsIdentity me=WindowsIdentity.GetCurrent())
        {
            Need(me.User!=null&&!me.User.IsWellKnown(
                WellKnownSidType.LocalSystemSid),"run unprivileged");
            PipeSecurity acl=new PipeSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.AddAccessRule(new PipeAccessRule(me.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            return new NamedPipeServerStream(name,PipeDirection.InOut,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,
                1024,1024,acl);
        }
    }

    private static ServiceBoundRequestIdentity ClaimedConsent()
    {
        return new ServiceBoundRequestIdentity(
            LedgerOperation.Save,new string('1',32),new string('2',32),
            new string('a',64),DateTime.UtcNow.AddMinutes(1).Ticks,false);
    }

    private static void Denied(P215StorePrincipalObservation observation)
    {
        Need(observation!=null,"receipt");
        Need(!observation.ApprovedServiceStorePrincipal,"unapproved service principal");
        Need(!observation.OwnProtectedServiceCredentialTarget,"no protected store");
        Need(!observation.AuthorizedCrossPrincipalMigration,"no migration");
        Need(!observation.LegacyPythonWinCredRouteRetired,"P132 reachable");
        Need(!observation.AuthorizedStoreReadWrite,"no credential effect");
        Need(!observation.SignedServiceInstalled,"no signed install");
        Need(!observation.AuthenticatedHumanConsent,"no human consent");
        Need(!observation.ProtectedOneUseGrant,"no protected ticket");
        Need(!observation.WindowsMachinePolicyApproved,"no machine policy");
        Need(!observation.RealKeyPilotAuthorized,"real key no go");
        Need(!observation.ProductionReleaseAuthorized,"production hold");
        Need(!observation.ToString().Contains("S-1-"),"no SID exposed");
        Need(!observation.ToString().Contains("openai.api_key"),"no target exposed");
    }

    private static P215StorePrincipalObservation Same(
        CustodyService host,ServiceBoundRequestIdentity claim)
    {
        string name=Name();
        using(var server=Server(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                Need(pending.AsyncWaitHandle.WaitOne(5000),"same connected");
                server.EndWaitForConnection(pending);
                client.WriteByte(0x43);client.Flush();
                Need(server.ReadByte()==0x43,"same non-secret handshake");
                return P215WindowsStorePrincipalReadOnlyAdmission.
                    ObserveAndRefuse(server,host,claim);
            }
        }
    }

    private static int Child(string name)
    {
        if(String.IsNullOrWhiteSpace(name) || !name.StartsWith(
            "nayeon-c1-p215-test-",StringComparison.Ordinal))return 11;
        try
        {
            using(var client=new NamedPipeClientStream(".",name,
                PipeDirection.InOut,PipeOptions.None,
                TokenImpersonationLevel.Impersonation))
            {
                client.Connect(5000);
                client.WriteByte(0x43);client.Flush();
                return client.ReadByte()==0x42?0:12;
            }
        }
        catch(Exception){return 13;}
    }

    private static P215StorePrincipalObservation Cross(
        CustodyService host,ServiceBoundRequestIdentity claim)
    {
        string name=Name();
        using(var server=Server(name))
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            var info=new ProcessStartInfo(Assembly.GetExecutingAssembly().Location,
                "--p215-child "+name);
            info.UseShellExecute=false;info.CreateNoWindow=true;
            using(Process child=Process.Start(info))
            {
                Need(child!=null&&child.Id>0,"child started");
                try
                {
                    Need(pending.AsyncWaitHandle.WaitOne(6000),"child connected");
                    server.EndWaitForConnection(pending);
                    Need(server.ReadByte()==0x43,"child non-secret handshake");
                    var o=P215WindowsStorePrincipalReadOnlyAdmission.
                        ObserveAndRefuse(server,host,claim);
                    server.WriteByte(0x42);server.Flush();
                    Need(child.WaitForExit(5000)&&child.ExitCode==0,"child finished");
                    using(var current=Process.GetCurrentProcess())
                        Need(child.Id!=current.Id,"two actual Windows processes");
                    return o;
                }
                finally {if(!child.HasExited)child.Kill();}
            }
        }
    }

    public static int Main(string[] args)
    {
        if(args!=null&&args.Length==2&&args[0]=="--p215-child")
            return Child(args[1]);
        if(args!=null&&args.Length>0)return 23;

        Run("01-Windows-current-token-is-real-unprivileged-principal",delegate
        {
            var o=P215WindowsStorePrincipalReadOnlyAdmission.
                ObserveAndRefuse(null,null,null);
            Need(o.OsCurrentTokenRead,"real Windows current token observed");
            Need(o.CurrentHostDiffersFromLocalSystem,"this is not LocalSystem");
            Need(!o.CurrentHostIsLocalSystem,"not privileged host");
            Denied(o);
        });
        Run("02-WinCred-session-type-readonly-OS-observation",delegate
        {
            var o=P215WindowsStorePrincipalReadOnlyAdmission.
                ObserveAndRefuse(null,null,null);
            Need(o.GenericPersistenceQueried,
                 "real CredGetSessionTypes OS capability query succeeded");
            Denied(o);
        });
        Run("03-generic-credential-persistence-is-capability-not-ownership",delegate
        {
            var o=P215WindowsStorePrincipalReadOnlyAdmission.
                ObserveAndRefuse(null,null,null);
            Need(o.GenericPersistenceQueried &&
                 o.GenericCredentialMaxPersistence<=3,
                 "Windows generic max persistence bounded");
            Need(!o.OwnProtectedServiceCredentialTarget,"no vault");
            Denied(o);
        });
        Run("04-no-connected-client-denies-original-service-host",delegate
        {
            var h=new CustodyService();
            using(var server=Server(Name()))
            {
                var o=P215WindowsStorePrincipalReadOnlyAdmission.
                    ObserveAndRefuse(server,h,null);
                Need(!o.ConnectedPeerSidMatchesCurrentHost,"no connected client");
                Need(o.CurrentServiceTerminalResult==CustodyOutcome.Denied,
                     "real host refused");
                Need(h.TerminalEffectRefusals==1,"original host invoked");
                Denied(o);
            }
        });
        Run("05-same-process-real-Windows-account-SID-matches",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(o.OsPeerSignalsAgree,"OS process/session/token peer signals");
            Need(o.ConnectedPeerSidMatchesCurrentHost,"same user as host observed");
            Need(o.CurrentHostDiffersFromLocalSystem,"normal user != SYSTEM");
            Denied(o);
        });
        Run("06-same-principal-equality-cannot-mint-store-owner",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(o.ConnectedPeerSidMatchesCurrentHost,"SID matching");
            Need(!o.ApprovedServiceStorePrincipal,"SID matching not authorisation");
            Need(!o.AuthorizedStoreReadWrite,"no effect");
            Denied(o);
        });
        Run("07-cross-process-real-Windows-account-identity",delegate
        {
            var o=Cross(new CustodyService(),null);
            Need(o.OsPeerSignalsAgree,"cross-process OS identity agrees");
            Need(o.ConnectedPeerSidMatchesCurrentHost,"different process same user");
            Need(o.GenericPersistenceQueried,"OS read-only capability");
            Denied(o);
        });
        Run("08-cross-process-user-vault-not-shared-machine-store",delegate
        {
            var o=Cross(new CustodyService(),null);
            Need(o.CurrentHostDiffersFromLocalSystem,"not elevated service");
            Need(!o.OwnProtectedServiceCredentialTarget,"no service-owned target");
            Need(!o.AuthorizedCrossPrincipalMigration,"no cross-principal custody");
            Denied(o);
        });
        Run("09-valid-looking-approval-from-actual-OS-peer-denied",delegate
        {
            var host=new CustodyService();
            var o=Cross(host,ClaimedConsent());
            Need(o.OsPeerSignalsAgree,"genuine peer observation");
            Need(o.CurrentServiceTerminalResult==CustodyOutcome.Denied,
                 "terminal denial invoked");
            Need(o.CurrentServiceRequestResult==CustodyOutcome.Denied,
                 "untrusted metadata rejected");
            Need(!host.NativeEffectEnabled,"native effect remains closed");
            Denied(o);
        });
        Run("10-user-and-admin-migration-claims-cannot-authorize",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(!P215WindowsStorePrincipalReadOnlyAdmission.
                AuthorizeLegacyUserVaultMigration(o,"S-1-5-18",true,true),
                "claimed user/admin approval denied");
            Denied(o);
        });
        Run("11-matching-user-SID-claimed-migration-still-denied",delegate
        {
            var o=Same(new CustodyService(),null);
            using(WindowsIdentity me=WindowsIdentity.GetCurrent())
                Need(!P215WindowsStorePrincipalReadOnlyAdmission.
                    AuthorizeLegacyUserVaultMigration(o,me.User.Value,true,true),
                    "actual matching SID never grants migration");
            Denied(o);
        });
        Run("12-claimed-signer-LocalSystem-CodeIntegrity-false-permit",delegate
        {
            var o=Same(new CustodyService(),null);
            Need(!P215WindowsStorePrincipalReadOnlyAdmission.
                AuthorizeServiceCredentialEffect(o,true,true,true,true),
                "all booleans forged");
            Denied(o);
        });
        Run("13-original-host-replay-shaped-metadata-no-credential-effect",delegate
        {
            var host=new CustodyService();
            var claim=ClaimedConsent();
            Need(host.RefuseBoundPendingOperation(claim)==CustodyOutcome.Denied,
                 "first refusal");
            Need(host.RefuseBoundPendingOperation(claim)==CustodyOutcome.Denied,
                 "replay refusal");
            Need(host.StructurallyRepeatedRequestCount>=1,"replay counted");
            Need(!host.NativeEffectEnabled,"no effect");
        });
        Run("14-revoked-original-C1-host-SID-match-cannot-rearm",delegate
        {
            var host=new CustodyService();
            host.RevokePendingAdmission();
            var o=Same(host,ClaimedConsent());
            Need(o.ConnectedPeerSidMatchesCurrentHost,"OS peer observed");
            Need(o.CurrentServiceTerminalResult==CustodyOutcome.Denied,
                 "host revoked");
            Need(host.PendingAdmissionRevoked,"revoked sticky");
            Denied(o);
        });
        Run("15-faulted-original-C1-host-sticky-recovery",delegate
        {
            var host=new CustodyService();
            host.FaultPendingAdmission();
            var o=Same(host,ClaimedConsent());
            Need(o.CurrentServiceTerminalResult==CustodyOutcome.RecoveryRequired,
                 "faulted terminal");
            Need(o.CurrentServiceRequestResult==CustodyOutcome.RecoveryRequired,
                 "faulted request");
            Need(host.PendingAdmissionFaulted,"fault sticky");
            Denied(o);
        });
        Run("16-actual-host-effect-remains-denied-with-real-Windows-persistence",delegate
        {
            var host=new CustodyService();
            var o=Same(host,ClaimedConsent());
            Need(o.GenericPersistenceQueried,"real OS persistence observation");
            Need(o.CurrentServiceTerminalResult==CustodyOutcome.Denied,
                 "old service denies");
            Need(o.CurrentServiceRequestResult==CustodyOutcome.Denied,
                 "old service refuses");
            Need(!host.AuthenticatedConsentAvailable,"no trusted consent");
            Need(!host.ProductionReleaseEligible,"no production");
            Denied(o);
        });

        Console.WriteLine("P215_REAL_WINDOWS_PRINCIPAL_C1_HOST_PASS="+passed);
        Console.WriteLine("P215_REAL_WINDOWS_PRINCIPAL_C1_HOST_FAIL="+failed);
        Console.WriteLine("P215_WIN32_CRED_GET_SESSION_TYPES=READ_ONLY_NO_SECRETS");
        Console.WriteLine("P215_LOCAL_MACHINE_PERSISTENCE_IS_SAME_USER_NOT_SHARED_VAULT");
        Console.WriteLine("P215_EXISTING_CUSTODY_SERVICE_REAL_EFFECT=DENIED");
        Console.WriteLine("P215_SIGNED_PROTECTED_SERVICE_STORE=NOT_ENROLLED");
        Console.WriteLine("P215_REAL_KEY=NO_GO|PRODUCTION=HOLD");
        return passed==16&&failed==0?0:1;
    }
}
#endif
