// P223: exact ACTUAL native CustodyService source-backed no-effect port.
// Genuine Windows native C# assembly, not a detached fake-effect test.
// Does NOT remediate the old P96 coordinator, implement consent or provide
// protected storage. No API keys, WinCred P/Invoke, service or installer.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P223 no-effect actual host review requires explicit review assembly
#endif
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P223ActualHostNoEffectTests
{
    private static int passed, failed;
    private static void Assert(bool condition, string reason)
    {
        if (!condition) throw new InvalidOperationException(reason);
    }
    private static void Run(string name, Action test)
    {
        try { test(); ++passed; Console.WriteLine("PASS "+name); }
        catch (Exception e)
        {
            ++failed;
            Console.WriteLine("FAIL "+name+" "+e.GetType().Name);
        }
    }
    private static ServiceBoundRequestIdentity NewUntrustedRequest()
    {
        return new ServiceBoundRequestIdentity(
            LedgerOperation.Save, new string('a', 32),
            new string('b', 32), new string('c', 64),
            DateTime.UtcNow.AddMinutes(1).Ticks, false);
    }
    private static void NoNewAuthority(P223ActualHostNoEffectPort port,
        CustodyService host)
    {
        Assert(!port.ActualWindowsServicePrincipalApproved, "no service principal");
        Assert(!port.ProtectedStoreVerified, "no protected store proof");
        Assert(!port.TrustedConsentIssued, "no trusted consent");
        Assert(!port.LoadedSignedImageEnforced, "no Code Integrity policy proof");
        Assert(!port.ActualP96RemediationImplemented, "original P96 remains unfixed");
        Assert(!port.NativeCredentialEffectAllowed, "no effect");
        Assert(!port.RealKeyAdmissible, "no real key");
        Assert(!port.ProductionReleaseEligible, "no release");
        Assert(!host.NativeEffectEnabled, "real host denies native effect");
        Assert(!host.AuthenticatedConsentAvailable, "real host denies consent");
        Assert(!host.ProductionReleaseEligible, "real host denies release");
        Assert(port.LocalReleaseHolds(), "all actual host release guards");
    }
    private static void StopActual(CustodyService h)
    {
        typeof(CustodyService).GetMethod("OnStop",
            BindingFlags.NonPublic | BindingFlags.Instance).Invoke(h, null);
    }
    public static int Main()
    {
        Run("exact-host-null-constructor-rejected", () =>
        {
            bool denied = false;
            try { new P223ActualHostNoEffectPort(null); }
            catch (ArgumentException) { denied = true; }
            Assert(denied, "null is not actual service host");
        });
        Run("original-CustodyService-refusal-not-an-effect-owner", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                NoNewAuthority(port, host);
                Assert(host.ServiceName == ServiceGate.ServiceName, "exact host name");
            }
        });
        Run("valid-structure-untrusted-claim-always-denied", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                Assert(port.RefuseUntrustedRequest(NewUntrustedRequest()) ==
                    CustodyOutcome.Denied, "untrusted claim became a grant");
                Assert(host.TerminalEffectRefusals == 1,
                    "exact existing terminal refusal was invoked");
                Assert(port.RefusedRequests == 1, "review count");
                NoNewAuthority(port, host);
            }
        });
        Run("untrusted-replay-has-no-credential-capability", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                var same = NewUntrustedRequest();
                for (int i = 0; i < 25; ++i)
                {
                    var o = port.RefuseUntrustedRequest(same);
                    Assert(o == CustodyOutcome.Denied ||
                        o == CustodyOutcome.RecoveryRequired, "replay accepted");
                }
                Assert(port.RefusedRequests == 25, "count 25 requests");
                NoNewAuthority(port, host);
            }
        });
        Run("null-claim-does-not-provide-approval", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                Assert(port.RefuseUntrustedRequest(null) ==
                    CustodyOutcome.Denied, "null claim must deny");
                NoNewAuthority(port, host);
            }
        });
        Run("revoke-before-request-denies-with-existing-service-monitor", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                port.RevokeWithoutGrant();
                Assert(host.PendingAdmissionRevoked, "actual host revoke");
                Assert(port.RefuseUntrustedRequest(NewUntrustedRequest()) ==
                    CustodyOutcome.Denied, "revoke no effect");
                NoNewAuthority(port, host);
            }
        });
        Run("fault-before-request-sticky-recovery", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                port.FaultWithoutRetry();
                Assert(host.PendingAdmissionFaulted, "actual host fault");
                Assert(port.RefuseUntrustedRequest(NewUntrustedRequest()) ==
                    CustodyOutcome.RecoveryRequired, "fault must recover");
                NoNewAuthority(port, host);
            }
        });
        Run("review-stop-never-starts-native-service", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                port.StopReviewWithoutStartingService();
                Assert(host.PendingAdmissionRevoked, "stop latches revoke");
                Assert(port.RefuseUntrustedRequest(NewUntrustedRequest()) ==
                    CustodyOutcome.Denied, "stopped request");
                NoNewAuthority(port, host);
            }
        });
        Run("actual-original-service-OnStart-throws-no-entrypoint", () =>
        {
            using (var host = new CustodyService())
            {
                var m = typeof(CustodyService).GetMethod("OnStart",
                    BindingFlags.NonPublic | BindingFlags.Instance);
                Assert(m != null, "actual OnStart");
                bool refused = false;
                try { m.Invoke(host, new object[]{new string[0]}); }
                catch (TargetInvocationException e)
                {
                    refused = e.InnerException is InvalidOperationException;
                }
                Assert(refused, "actual OnStart must refuse");
                Assert(typeof(CustodyService).GetMethod("Main",
                    BindingFlags.NonPublic | BindingFlags.Public |
                    BindingFlags.Static) == null, "not a service process");
                NoNewAuthority(new P223ActualHostNoEffectPort(host), host);
            }
        });
        Run("actual-original-service-OnStop-keeps-native-effect-disabled", () =>
        {
            using (var host = new CustodyService())
            {
                StopActual(host);
                Assert(host.PendingAdmissionStopped, "actual stop callback");
                var port = new P223ActualHostNoEffectPort(host);
                Assert(port.RefuseUntrustedRequest(NewUntrustedRequest()) ==
                    CustodyOutcome.Denied, "actual stopped host");
                NoNewAuthority(port, host);
            }
        });
        Run("two-thread-request-and-revoke-cannot-authorise-native-effect", () =>
        {
            using (var host = new CustodyService())
            {
                var port = new P223ActualHostNoEffectPort(host);
                CustodyOutcome result = CustodyOutcome.StoredUnverified;
                Exception thrown = null;
                var go = new ManualResetEvent(false);
                var worker = new Thread(() =>
                {
                    try
                    {
                        go.WaitOne();
                        result = port.RefuseUntrustedRequest(NewUntrustedRequest());
                    }
                    catch (Exception e) { thrown = e; }
                });
                worker.Start();
                port.RevokeWithoutGrant();
                go.Set();
                Assert(worker.Join(3000), "native denial worker timed out");
                Assert(thrown == null, "unexpected native request exception");
                Assert(result == CustodyOutcome.Denied ||
                    result == CustodyOutcome.RecoveryRequired, "native effect authorised");
                Assert(host.PendingAdmissionRevoked, "actual revoke present");
                NoNewAuthority(port, host);
                go.Dispose();
            }
        });
        Run("port-has-no-arbitrary-effect-callback-or-secret-parameter", () =>
        {
            var port = typeof(P223ActualHostNoEffectPort);
            var methods = port.GetMethods(BindingFlags.NonPublic |
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
            foreach (var method in methods)
            {
                foreach (var p in method.GetParameters())
                {
                    Assert(p.ParameterType != typeof(byte[]) &&
                        !typeof(Delegate).IsAssignableFrom(p.ParameterType),
                        "unexpected credential bytes or arbitrary callback");
                }
            }
            Assert(CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "original native mutation admission hold must remain true");
        });
        Console.WriteLine("P223_ACTUAL_NATIVE_CUSTODYSERVICE_DENIAL_TESTS_PASSED="+passed);
        Console.WriteLine("P223_ACTUAL_NATIVE_CUSTODYSERVICE_DENIAL_TESTS_FAILED="+failed);
        Console.WriteLine("P223_ACTUAL_HOST_USED=YES_DENIAL_ONLY");
        Console.WriteLine("P223_ORIGINAL_P96_RACE=OPEN_NOT_FIXED");
        Console.WriteLine("P223_NATIVE_WINCRED_EFFECTS=NONE");
        Console.WriteLine("P223_EXTERNAL_SEC03_SEC04_OWNER_DECISION=NOT_RECEIVED");
        Console.WriteLine("P223_REAL_KEY=NO_GO");
        Console.WriteLine("P223_PRODUCTION_RELEASE=HOLD");
        return passed == 12 && failed == 0 ? 0 : 1;
    }
}
