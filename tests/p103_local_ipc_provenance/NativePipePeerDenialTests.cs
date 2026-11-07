// P103 genuine Windows local named pipe peer observation and mandatory DENY.
// No secret, elevation, SCM installation, WinCred, provider, key or registry.
// No authority from SID equality, text claiming trusted UI or pipe ACL.
using System;
using System.Threading;
using Nayeon.ByokC1;

internal static class P103NativePipePeerDenialTests
{
    private static int passed, failed;

    private static void Require(bool ok, string reason)
    { if (!ok) throw new InvalidOperationException(reason); }

    private static void Run(string name, Action action)
    {
        try { action(); passed++; Console.WriteLine("PASS "+name); }
        catch (Exception e)
        { failed++; Console.WriteLine("FAIL "+name+" "+e.GetType().Name); }
    }

    private static void NoAuthority(DisposablePeerObservation obs)
    {
        Require(!obs.VerifiedTrustedUi, "same-user Windows token is NOT UI auth");
        Require(!obs.ElevatedConsentGranted, "no genuine interactive consent");
        Require(!obs.CanDispatchNativeEffect, "never authorize WinCred");
        Require(!obs.ProductionEligible, "never production");
        Require(!obs.SecurityExceptionObserved, "OS identity observation failed");
        Require(obs.PeerSidObservable, "Windows peer SID not observable");
        Require(obs.PeerSameWindowsUser, "disposable same-user peer mismatch");
        Require(!obs.ToString().Contains("S-1-"), "no sid string leak");
    }

    public static int Main()
    {
        Run("real-windows-named-pipe-roundtrip-denied",()=>{
            var o=DisposablePipePeerProbe.Observe(0x01);
            NoAuthority(o);
            Require(!o.ProtocolClaimedTrusted, "normal synthetic value");
        });
        Run("same-windows-user-cannot-authenticate-trusted-ui",()=>{
            var o=DisposablePipePeerProbe.Observe(0x44);
            Require(o.PeerSameWindowsUser, "same user should be observable");
            NoAuthority(o);
        });
        Run("forged-trusted-ui-byte-cannot-grant-consent",()=>{
            var o=DisposablePipePeerProbe.Observe(0x54);
            Require(o.ProtocolClaimedTrusted, "untrusted client sent fake trusted text");
            NoAuthority(o);
        });
        Run("all-zero-pipe-message-still-denied",()=>{
            NoAuthority(DisposablePipePeerProbe.Observe(0));
        });
        Run("maximum-byte-pipe-message-still-denied",()=>{
            NoAuthority(DisposablePipePeerProbe.Observe(255));
        });
        Run("same-user-observation-never-key-permission",()=>{
            var o=DisposablePipePeerProbe.Observe(0x54);
            Require(o.PeerSidObservable && o.PeerSameWindowsUser,"peer matched");
            Require(!o.ElevatedConsentGranted && !o.VerifiedTrustedUi &&
                !o.CanDispatchNativeEffect,"SID cannot become credential permit");
        });
        Run("new-pipe-name-every-time-no-replay-privilege",()=>{
            for(int i=0;i<3;i++){
                var o=DisposablePipePeerProbe.Observe(0x54);
                NoAuthority(o);
            }
        });
        Run("real-native-service-still-disabled",()=>{
            Require(!ServiceGate.LiveEligible(),"live service denied");
            Require(PendingServiceState.LegacyEffectEntryDisabled(),"legacy effect disabled");
            Require(PendingWinCredStore.NativeMutationAdmissionPending(),"WinCred disabled");
        });
        Run("review-host-still-denies-bound-claim",()=>{
            using(var host=new CustodyService()){
                var claim=new ServiceBoundRequestIdentity(
                    LedgerOperation.Save,new string('a',32),new string('b',32),
                    new string('c',64),DateTime.UtcNow.AddMinutes(1).Ticks,false);
                CustodyOutcome outcome=host.RefuseBoundPendingOperation(claim);
                Require(outcome==CustodyOutcome.Denied,"review host refused");
                Require(!host.AuthenticatedConsentAvailable && !host.NativeEffectEnabled &&
                    !host.ProductionReleaseEligible,"host cannot authorize");
            }
        });
        Run("same-user-two-independent-pipes-cannot-authorize",()=>{
            var a=DisposablePipePeerProbe.Observe(0x01);
            var b=DisposablePipePeerProbe.Observe(0x54);
            NoAuthority(a);NoAuthority(b);
            Require(a.PeerSameWindowsUser && b.PeerSameWindowsUser,
                "both have OS same-user provenance, neither trusted");
        });
        Run("real-parallel-peer-sessions-no-authority",()=>{
            Exception threadFailure=null;
            int denied=0;
            Thread[] peers=new Thread[4];
            for(int i=0;i<peers.Length;i++) {
                int index=i;
                peers[i]=new Thread(()=>{
                    try{
                        var o=DisposablePipePeerProbe.Observe(index%2==0?0x01:0x54);
                        NoAuthority(o);
                        Interlocked.Increment(ref denied);
                    }catch(Exception e){
                        Interlocked.CompareExchange(ref threadFailure,e,null);
                    }
                });
            }
            foreach(Thread t in peers)t.Start();
            foreach(Thread t in peers)Require(t.Join(6000),"peer must terminate");
            Require(threadFailure==null && denied==4,
                "no privileged outcome from concurrent pipes");
        });
        Run("no-window-service-main-installed",()=>{
            Require(typeof(CustodyService).GetMethod("Main",
                System.Reflection.BindingFlags.Static |
                System.Reflection.BindingFlags.NonPublic |
                System.Reflection.BindingFlags.Public)==null,
                "review host has no service start entry");
        });

        Console.WriteLine("P103_GENUINE_WINDOWS_PIPE_TESTS_PASSED="+passed);
        Console.WriteLine("P103_GENUINE_WINDOWS_PIPE_TESTS_FAILED="+failed);
        Console.WriteLine("P103_WINDOWS_SAME_USER_PEER_AUTHENTICATED_TRUSTED_UI=FALSE");
        Console.WriteLine("P103_UNPRIVILEGED_PIPE_EFFECTS=NONE");
        Console.WriteLine("P103_ORIGINAL_P61_NATIVE_RACE=OPEN");
        Console.WriteLine("P103_X86_POLICY=BLOCKED_NOT_ATTEMPTED");
        Console.WriteLine("P103_C1_PRODUCTION_RELEASE=HOLD");
        return failed==0 && passed==12 ? 0 : 1;
    }
}
