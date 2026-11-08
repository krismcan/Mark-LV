// P113: genuine Windows local named-pipe impersonation observation tests.
// Unprivileged ephemeral runner only. Exact one-byte nonsecret handshake.
// Real OS-authenticated token is observed; it NEVER proves a human click,
// signed UI image, session provenance or durable one-use consent.
// No API key, WinCred, LocalSystem service, registry/file write or provider.
using System;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using Nayeon.ByokC1;

internal static class P113RealWindowsPeerIdentityTests
{
    private static int passed, failed;
    private static void Need(bool ok,string reason)
    { if (!ok) throw new InvalidOperationException("P113 "+reason); }
    private static void Run(string name,Action test)
    {
        try { test(); passed++; Console.WriteLine("PASS "+name); }
        catch (Exception e)
        {
            failed++;
            Console.WriteLine("FAIL "+name+" "+e.GetType().Name);
        }
    }

    // This server is created ONLY by this test executable on the separate
    // hosted Windows runner, NEVER in the candidate review/production DLL.
    // Test-only pipe name, never an authorization credential.
    private static string latestTestName;

    private static NamedPipeServerStream NewServerWithPublishedTestName()
    {
        using (WindowsIdentity user=WindowsIdentity.GetCurrent())
        {
            Need(user.User!=null &&
                !user.User.IsWellKnown(WellKnownSidType.LocalSystemSid),
                "not LocalSystem");
            var access=new PipeSecurity();
            access.SetAccessRuleProtection(true,false);
            access.AddAccessRule(new PipeAccessRule(user.User,
                PipeAccessRights.ReadWrite,AccessControlType.Allow));
            latestTestName="nayeon-c1-p113-unprivileged-"+
                Guid.NewGuid().ToString("N");
            return new NamedPipeServerStream(latestTestName,PipeDirection.In,1,
                PipeTransmissionMode.Byte,PipeOptions.Asynchronous,1024,1024,access);
        }
    }

    private static OsPipePeerObservation ConnectAndObserve(
        TokenImpersonationLevel level)
    {
        using (var server=NewServerWithPublishedTestName())
        {
            IAsyncResult pending=server.BeginWaitForConnection(null,null);
            using (var client=new NamedPipeClientStream(
                ".",latestTestName,PipeDirection.Out,PipeOptions.None,level))
            {
                client.Connect(5000);
                Need(pending.AsyncWaitHandle.WaitOne(5000),"connection accepted");
                server.EndWaitForConnection(pending);
                client.WriteByte(0x43);
                client.Flush();
                Need(server.ReadByte()==0x43,"nonsecret handshake");
                return WindowsPipePeerObservation.ObserveAfterClientWrite(server);
            }
        }
    }

    private static void NoAuthority(OsPipePeerObservation o)
    {
        Need(!o.TrustedClientImageVerified,"signed application NOT established");
        Need(!o.HumanConsentVerified,"human clicked approve NOT established");
        Need(!o.OneUseGrantIssued,"no one-use grant");
        Need(!o.CanAuthorizeCredentialEffect,"no WinCred permission");
        Need(!o.ToString().Contains("S-1-"),"no SID leak in diagnostics");
    }

    public static int Main()
    {
        Run("null-server-fails-closed",() =>
        {
            var o=WindowsPipePeerObservation.ObserveAfterClientWrite(null);
            Need(o.State==OsPipePeerState.Unavailable,"null denied");
            NoAuthority(o);
        });
        Run("disconnected-server-fails-closed",() =>
        {
            using(var p=NewServerWithPublishedTestName())
            {
                var o=WindowsPipePeerObservation.ObserveAfterClientWrite(p);
                Need(o.State==OsPipePeerState.Unavailable,"not connected");
                NoAuthority(o);
            }
        });
        Run("actual-Windows-impersonated-client-SID-observed",() =>
        {
            var o=ConnectAndObserve(TokenImpersonationLevel.Impersonation);
            Need(o.OsClientTokenObserved,"real named pipe client token observed");
            using(var current=WindowsIdentity.GetCurrent())
                Need(String.Equals(o.OsClientSid,current.User.Value,
                    StringComparison.Ordinal),"OS SID compared, not caller claim");
            NoAuthority(o);
        });
        Run("OS-peer-does-not-attest-signed-UI",() =>
        {
            var o=ConnectAndObserve(TokenImpersonationLevel.Impersonation);
            Need(o.OsClientTokenObserved,"real token");
            Need(!o.TrustedClientImageVerified,"no image verification");
        });
        Run("OS-peer-does-not-attest-human-confirmation",() =>
        {
            var o=ConnectAndObserve(TokenImpersonationLevel.Impersonation);
            Need(o.OsClientTokenObserved,"real token");
            Need(!o.HumanConsentVerified,"no user click");
        });
        Run("OS-peer-does-not-mint-reusable-or-oneuse-grants",() =>
        {
            var o=ConnectAndObserve(TokenImpersonationLevel.Impersonation);
            Need(o.OsClientTokenObserved,"real token");
            Need(!o.OneUseGrantIssued && !o.CanAuthorizeCredentialEffect,
                "identity not authorization");
        });
        Run("identification-level-peer-never-elevates-to-approval",() =>
        {
            // Some Windows configurations cannot impersonate an
            // Identification-level client. Either explicit denial or an
            // OS-token observation still must have ZERO consent authority.
            var o=ConnectAndObserve(TokenImpersonationLevel.Identification);
            NoAuthority(o);
        });
        Run("peer-observation-accepts-no-caller-supplied-SID",() =>
        {
            var method=typeof(WindowsPipePeerObservation).GetMethod(
                "ObserveAfterClientWrite",BindingFlags.Static|
                BindingFlags.NonPublic);
            Need(method!=null,"method exists");
            var ps=method.GetParameters();
            Need(ps.Length==1 &&
                ps[0].ParameterType==typeof(NamedPipeServerStream),
                "cannot pass forged PID/SID/approval boolean");
        });
        Run("peer-observation-has-no-privileged-API-entrypoint",() =>
        {
            var t=typeof(WindowsPipePeerObservation);
            foreach(var m in t.GetMethods(BindingFlags.Static|
                BindingFlags.NonPublic|BindingFlags.Public|
                BindingFlags.DeclaredOnly))
            {
                Need(m.Name!="CredWrite" && m.Name!="CredDelete" &&
                    m.Name!="SaveOrReplace" &&
                    m.Name!="IssueApproval" &&
                    m.Name!="InstallService","no effect API");
            }
        });
        Run("peer-observation-class-does-not-create-listener",() =>
        {
            foreach(var method in typeof(WindowsPipePeerObservation).GetMethods(
                BindingFlags.Static|BindingFlags.Public|
                BindingFlags.NonPublic|BindingFlags.DeclaredOnly))
            {
                Need(method.Name!="CreateServer" &&
                    method.Name!="StartListener" &&
                    method.Name!="Main","not a deployable listener");
            }
        });
        Run("original-custody-service-eligibility-still-false",() =>
            Need(!ServiceGate.LiveEligible(),"native gate remains held"));
        Run("C1-candidate-effect-hold-is-hardcoded-closed",() =>
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "no credential effect"));
        Run("C1-candidate-service-still-refuses-humanless-requests",() =>
        {
            using(var host=new CustodyService())
            {
                Need(!host.AuthenticatedConsentAvailable &&
                    !host.NativeEffectEnabled &&
                    !host.ProductionReleaseEligible,"review host held");
                Need(host.RefusePendingOperation(LedgerOperation.Delete,0,true)==
                    CustodyOutcome.Denied,"untrusted delete denied");
            }
        });
        Run("G1-os-peer-data-not-a-service-request-identity",() =>
        {
            var o=ConnectAndObserve(TokenImpersonationLevel.Impersonation);
            Need(o.OsClientTokenObserved,"OS token available");
            Need(typeof(OsPipePeerObservation)!=
                typeof(ServiceBoundRequestIdentity),
                "peer token is not caller metadata or grant");
            NoAuthority(o);
        });

        Console.WriteLine("P113_NATIVE_WINDOWS_PIPE_PEER_CASES_PASSED="+passed);
        Console.WriteLine("P113_NATIVE_WINDOWS_PIPE_PEER_CASES_FAILED="+failed);
        Console.WriteLine("P113_OS_PIPE_PEER_TOKEN_OBSERVATION=REAL_WINDOWS_API");
        Console.WriteLine("P113_TRUSTED_SIGNED_USER_INTERFACE=NOT_VERIFIED");
        Console.WriteLine("P113_EXPLICIT_HUMAN_APPROVAL=NOT_PROVEN");
        Console.WriteLine("P113_PROTECTED_ONEUSE_CONSENT=NOT_IMPLEMENTED");
        Console.WriteLine("P113_WINCRED_EFFECT_AUTHORITY=NONE");
        Console.WriteLine("P113_G1_PRODUCTION_TRUST=HOLD");
        Console.WriteLine("P113_C1_PRODUCTION_RELEASE=HOLD");
        return passed==14 && failed==0 ?0:1;
    }
}
