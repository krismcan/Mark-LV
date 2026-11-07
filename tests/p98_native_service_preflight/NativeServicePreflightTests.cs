// P98: genuine disabled P49 ServiceGate/CustodyService/ProtectedAcl sources.
// No ServiceBase.Run, installation, SCM, WinCred, provider or stored secrets.
// Testing OnStart via reflection as a method, never starting an OS service.
using System;
using System.Reflection;
using System.Threading;
using Nayeon.ByokC1;

internal static class P98PreflightTests
{
    private static int passes, fails;
    private static void Require(bool predicate, string name)
    { if (!predicate) throw new Exception("P98 denied boundary mismatch: " + name); }
    private static void Run(string name, Action action)
    {
        try { action(); passes++; Console.WriteLine("PASS " + name); }
        catch (Exception e) { fails++; Console.WriteLine("FAIL " + name + " " + e.GetType().Name); }
    }

    private static void NoAuthority(DisabledServiceCompositionFence fence)
    {
        Require(!fence.NativeEffectEnabled, "native effect blocked");
        Require(!fence.CredentialVerified, "not verified");
        Require(!fence.TrustedConsentPresent, "no authenticated user");
        Require(!fence.ServiceInstalled, "not installed");
        Require(!fence.RetryPermitted, "no retry");
        Require(!fence.ProductionEligible, "no release");
    }

    public static int Main()
    {
        Run("exact-p49-service-name", () =>
            Require(ServiceGate.ServiceName == "NayeonV1ByokCustody", "service name"));
        Run("exact-p49-service-image", () =>
            Require(ServiceGate.ExecutableName == "Nayeon.ByokC1.CustodyService.exe", "binary name"));
        Run("real-release-gate-always-false-current-source", () =>
            Require(!ServiceGate.LiveEligible(), "P49 release false even on local host"));
        Run("real-release-gate-repeated-still-false", () =>
        {
            for (int i=0; i<10; i++) Require(!ServiceGate.LiveEligible(), "repeat");
        });
        Run("untrusted-null-request-refused", () =>
            Require(ServiceGate.HandleUntrustedRequest(null) == ServiceGate.Unavailable, "null"));
        Run("untrusted-empty-request-refused", () =>
            Require(ServiceGate.HandleUntrustedRequest("") == ServiceGate.Unavailable, "empty"));
        Run("untrusted-fake-key-payload-refused", () =>
            Require(ServiceGate.HandleUntrustedRequest("PLACEHOLDER_NOT_A_KEY") ==
                ServiceGate.Unavailable, "request denied"));
        Run("untrusted-oversized-request-refused", () =>
            Require(ServiceGate.HandleUntrustedRequest(new string('a', 32768)) ==
                ServiceGate.Unavailable, "oversize denied"));
        Run("helper-refuses-unverified-image-integrity", () =>
        {
            string image=ServiceGate.ExpectedImage();
            Require(!ServiceGate.EligibleForService(image,image,true,true,false,true), "binary proof");
        });
        Run("helper-refuses-unreviewed-release", () =>
        {
            string image=ServiceGate.ExpectedImage();
            Require(!ServiceGate.EligibleForService(image,image,true,true,true,false), "manifest proof");
        });
        Run("helper-refuses-untrusted-install-descriptor", () =>
        {
            string image=ServiceGate.ExpectedImage();
            Require(!ServiceGate.EligibleForService(image,image,true,false,true,true), "install proof");
        });
        Run("helper-refuses-wrong-principal", () =>
        {
            string image=ServiceGate.ExpectedImage();
            Require(!ServiceGate.EligibleForService(image,image,false,true,true,true), "principal");
        });
        Run("helper-refuses-wrong-image-path", () =>
            Require(!ServiceGate.EligibleForService(@"C:\temp\fake.exe",
                ServiceGate.ExpectedImage(),true,true,true,true), "wrong image"));
        Run("helper-refuses-missing-image-path", () =>
            Require(!ServiceGate.EligibleForService(null,
                ServiceGate.ExpectedImage(),true,true,true,true), "missing image"));
        Run("helper-is-conditional-not-a-production-release-permit", () =>
        {
            string image=ServiceGate.ExpectedImage();
            Require(ServiceGate.EligibleForService(image,image,true,true,true,true),
                "pure helper known all-true synthetic inputs");
            Require(!ServiceGate.LiveEligible(), "actual hardcoded false overrides synthetic");
        });
        Run("real-p49-service-start-guard-throws-without-SCM", () =>
        {
            // OnStart is invoked as an ordinary protected method. Do NOT
            // call ServiceBase.Run or install/start a real SCM service.
            var host = new CustodyService();
            MethodInfo start=typeof(CustodyService).GetMethod(
                "OnStart",BindingFlags.NonPublic|BindingFlags.Instance);
            Require(start!=null, "onstart method present");
            bool denied=false;
            try { start.Invoke(host,new object[] { new string[0] }); }
            catch (TargetInvocationException e)
            {
                denied=e.InnerException is InvalidOperationException &&
                    e.InnerException.Message == "Custody service is unavailable";
            }
            finally { host.Dispose(); }
            Require(denied, "real P49 startup remained blocked");
        });
        Run("disabled-fence-null-request-refused", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            Require(fence.RefuseOpaqueRequest(null)==ServiceAdmissionDisposition.Unavailable,
                "null denied");
            NoAuthority(fence);
        });
        Run("disabled-fence-opaque-key-refused", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            Require(fence.RefuseOpaqueRequest("FAKE_KEY_NOT_REAL") ==
                ServiceAdmissionDisposition.Unavailable, "opaque denied");
            NoAuthority(fence);
        });
        Run("disabled-fence-no-effect-admission", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            Require(fence.RefuseEffectAdmission()==ServiceAdmissionDisposition.Unavailable,
                "effect always unavailable");
            NoAuthority(fence);
        });
        Run("disabled-fence-revocation-never-authorizes", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            fence.Revoke();
            Require(fence.IsRevoked, "revocation");
            Require(fence.RefuseEffectAdmission()==ServiceAdmissionDisposition.Unavailable,
                "revoked still unavailable");
            NoAuthority(fence);
        });
        Run("disabled-fence-fault-persists", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            fence.Fault();
            Require(fence.RecoveryFaulted, "fault latched");
            Require(fence.RefuseEffectAdmission()==ServiceAdmissionDisposition.RecoveryRequired,
                "fault recovery");
            Require(fence.RefuseOpaqueRequest(null)==ServiceAdmissionDisposition.RecoveryRequired,
                "opaque recovery");
            NoAuthority(fence);
        });
        Run("disabled-fence-revocation-plus-fault-never-rearms", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            fence.Revoke(); fence.Fault();
            for(int i=0; i<10; i++)
                Require(fence.RefuseEffectAdmission()==ServiceAdmissionDisposition.RecoveryRequired,
                    "recovery sticky");
            NoAuthority(fence);
        });
        Run("disabled-fence-many-real-threads-cannot-admit", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            int invalid=0;
            Thread[] workers=new Thread[8];
            for(int j=0;j<workers.Length;j++)
                workers[j]=new Thread(() =>
                {
                    for(int i=0;i<20;i++)
                    {
                        if(fence.RefuseEffectAdmission()!=ServiceAdmissionDisposition.Unavailable &&
                           fence.RefuseEffectAdmission()!=ServiceAdmissionDisposition.RecoveryRequired)
                            Interlocked.Increment(ref invalid);
                        if(fence.NativeEffectEnabled) Interlocked.Increment(ref invalid);
                    }
                });
            foreach(Thread t in workers) t.Start();
            foreach(Thread t in workers) Require(t.Join(3000),"thread complete");
            Require(invalid==0, "no thread authorizes");
            Require(fence.RefusalCount>=160,"all requests rejected");
            NoAuthority(fence);
        });
        Run("disabled-fence-concurrent-fault-and-revoke-denies", () =>
        {
            var fence=new DisabledServiceCompositionFence();
            Thread a=new Thread(fence.Fault);
            Thread b=new Thread(fence.Revoke);
            a.Start();b.Start();
            Require(a.Join(3000)&&b.Join(3000), "both commits");
            Require(fence.RecoveryFaulted && fence.IsRevoked, "both states");
            Require(fence.RefuseEffectAdmission()==ServiceAdmissionDisposition.RecoveryRequired,
                "permanent recovery");
            NoAuthority(fence);
        });

        Console.WriteLine("P98_ACTUAL_NATIVE_SERVICE_GATE_TESTS_PASSED="+passes);
        Console.WriteLine("P98_ACTUAL_NATIVE_SERVICE_GATE_TESTS_FAILED="+fails);
        Console.WriteLine("P98_REAL_P49_ONSTART=DENIED");
        Console.WriteLine("P98_NATIVE_SERVICE_INSTALLATION=NONE");
        Console.WriteLine("P98_CREDENTIAL_EFFECTS=NONE");
        Console.WriteLine("P98_P61_LEGACY_RACE=STILL_OPEN");
        Console.WriteLine("P98_X86_WINDOWS_APP_CONTROL=BLOCKED_NOT_RETRIED");
        Console.WriteLine("P98_BYOK_C1_PRODUCTION_RELEASE=HOLD");
        return fails==0 && passes==24 ? 0 : 1;
    }
}
