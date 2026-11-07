// P103 genuine Windows local named-pipe OS identity observation tests.
// All pipes disposable/random and access-controlled to current owner,
// LocalSystem and admins. The ONLY wire response is "DENIED".
// No server installation, privileged service, auth ticket or WinCred effects.
using System;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;
using Nayeon.ByokC1;

internal static class P103WindowsReadOnlyPeerObservationTests
{
    private static int passed, failed;
    private static void Need(bool ok, string message)
    { if (!ok) throw new InvalidOperationException("P103: " + message); }

    private static void Case(string name, Action action)
    {
        try { action(); passed++; Console.WriteLine("PASS " + name); }
        catch(Exception e)
        { failed++; Console.WriteLine("FAIL " + name + " " + e.GetType().Name); }
    }

    private static void ExpectRejected(string invalidName)
    {
        bool refused=false;
        try { ReadOnlyWindowsPipeObserver.ObserveOneForTest(invalidName); }
        catch(ArgumentException) { refused=true; }
        Need(refused,"reject unsafe pipe name before OS listener creation");
    }

    private static ReadOnlyWindowsPeerObservation RoundTrip()
    {
        string pipeName=ReadOnlyWindowsPipeObserver.Prefix+
            Guid.NewGuid().ToString("N");
        ReadOnlyWindowsPeerObservation evidence=null;
        Exception serverError=null;
        Thread server=new Thread(new ThreadStart(delegate
        {
            try {
                evidence=ReadOnlyWindowsPipeObserver.ObserveOneForTest(pipeName);
            } catch(Exception ex) { serverError=ex; }
        }));
        server.IsBackground=true;
        server.Start();
        string answer;
        using (NamedPipeClientStream client = new NamedPipeClientStream(
            ".", pipeName, PipeDirection.InOut, PipeOptions.None,
            TokenImpersonationLevel.Impersonation))
        {
            client.Connect(5000);
            byte[] payload=new byte[6];
            int count=0;
            while(count<payload.Length)
            {
                int got=client.Read(payload,count,payload.Length-count);
                Need(got>0,"response stream unexpectedly closed");
                count+=got;
            }
            answer=Encoding.ASCII.GetString(payload);
        }
        Need(server.Join(5000),"disposable pipe server finished");
        if (serverError != null)
            throw new InvalidOperationException("P103 OS pipe failed",serverError);
        Need(evidence!=null,"OS peer result present");
        Need(answer==ReadOnlyWindowsPipeObserver.Denial,
            "client always receives DENIED");
        Need(evidence.Response==ReadOnlyWindowsPipeObserver.Denial,
            "server only emits DENIED");
        Need(!evidence.TrustedUserConsent &&
             !evidence.CredentialOperationAllowed &&
             !evidence.ProductionEligible,"OS observation never authorizes");
        return evidence;
    }

    private static void InspectAccessControls()
    {
        PipeSecurity security=ReadOnlyWindowsPipeObserver.LimitedAccessForTest();
        var rules=security.GetAccessRules(
            true,false,typeof(SecurityIdentifier));
        Need(rules.Count == 3,"exactly three deliberately scoped allow entries");
        string owner=ReadOnlyWindowsPipeObserver.CurrentServerSidForTest();
        string sys=new SecurityIdentifier(
            WellKnownSidType.LocalSystemSid,null).Value;
        string admins=new SecurityIdentifier(
            WellKnownSidType.BuiltinAdministratorsSid,null).Value;
        bool ownerSeen=false,sysSeen=false,adminsSeen=false;
        foreach(AuthorizationRule rule in rules)
        {
            PipeAccessRule allowed=rule as PipeAccessRule;
            Need(allowed!=null,"native PipeAccessRule only");
            Need(allowed.AccessControlType==AccessControlType.Allow,
                "explicit allow only");
            string sid=allowed.IdentityReference.Value;
            Need(sid!=new SecurityIdentifier(
                    WellKnownSidType.WorldSid,null).Value,"no Everyone");
            Need(sid!=new SecurityIdentifier(
                    WellKnownSidType.AuthenticatedUserSid,null).Value,
                    "no broad AuthenticatedUsers");
            if (sid==owner) ownerSeen=true;
            else if (sid==sys) sysSeen=true;
            else if (sid==admins) adminsSeen=true;
            else throw new InvalidOperationException("Unexpected SID in ACL");
        }
        Need(ownerSeen&&sysSeen&&adminsSeen,"exact Windows SIDs present");
    }

    private static void HostStillRefuses(ReadOnlyWindowsPeerObservation observation)
    {
        Need(observation.OsPeerWasObserved,
            "test client Windows SID captured via named-pipe impersonation");
        Need(observation.PeerSid==
            ReadOnlyWindowsPipeObserver.CurrentServerSidForTest(),
            "OS-observed test identity matches current user");
        using(CustodyService candidate=new CustodyService())
        {
            var fake=new ServiceBoundRequestIdentity(LedgerOperation.Save,
                new string('a',32),new string('b',32),new string('c',64),
                DateTime.UtcNow.AddMinutes(1).Ticks,false);
            Need(candidate.RefuseBoundPendingOperation(fake)==
                CustodyOutcome.Denied,"Windows-observed peer still denied");
            Need(!candidate.NativeEffectEnabled &&
                !candidate.AuthenticatedConsentAvailable &&
                !candidate.ProductionReleaseEligible,
                "observation never becomes consent");
        }
    }

    public static int Main()
    {
        Case("native-windows-ACL-no-everyone-or-authenticatedusers",
            InspectAccessControls);
        Case("invalid-null-name-refused",()=>ExpectRejected(null));
        Case("invalid-empty-name-refused",()=>ExpectRejected(""));
        Case("invalid-cross-namespace-name-refused",()=>
            ExpectRejected(@"\\.\pipe\NayeonP103ReadOnly_fake"));
        Case("invalid-wrong-prefix-refused",()=>
            ExpectRejected("OtherP103_"+Guid.NewGuid().ToString("N")));
        Case("invalid-very-short-random-suffix-refused",()=>
            ExpectRejected(ReadOnlyWindowsPipeObserver.Prefix+"a"));
        Case("invalid-uppercase-suffix-refused",()=>
            ExpectRejected(ReadOnlyWindowsPipeObserver.Prefix+
                new string('A',32)));
        Case("invalid-non-hex-suffix-refused",()=>
            ExpectRejected(ReadOnlyWindowsPipeObserver.Prefix+
                new string('z',32)));
        Case("live-windows-named-pipe-real-OS-peer-SID-denied",()=>
            HostStillRefuses(RoundTrip()));
        Case("second-fresh-named-pipe-peer-denied",()=>
            HostStillRefuses(RoundTrip()));
        Case("third-fresh-named-pipe-peer-denied",()=>
            HostStillRefuses(RoundTrip()));
        Case("fourth-fresh-named-pipe-peer-denied",()=>
            HostStillRefuses(RoundTrip()));
        Case("fifth-fresh-named-pipe-peer-denied",()=>
            HostStillRefuses(RoundTrip()));
        Case("no-identity-details-logged",()=>{
            var evidence=RoundTrip();
            Need(!evidence.ToString().Contains(evidence.PeerSid),
                "no identity SID in log string");
            Need(evidence.ToString()=="P103_PEER_OBSERVATION_ONLY_DENIED",
                "redacted summary only");
        });
        Case("original-three-native-release-switches-remain-denial",()=>{
            Need(!ServiceGate.LiveEligible(),"native service disabled");
            Need(PendingServiceState.LegacyEffectEntryDisabled(),
                "legacy native effect disabled");
            Need(PendingWinCredStore.NativeMutationAdmissionPending(),
                "original WinCred adapter disabled");
        });
        Case("no-production-pipe-service-main-or-ipc-wiring",()=>{
            Need(typeof(CustodyService).GetMethod("Main",
                System.Reflection.BindingFlags.Static|
                System.Reflection.BindingFlags.Public|
                System.Reflection.BindingFlags.NonPublic)==null,
                "candidate host has no service main");
            Need(typeof(PendingCustodyTransaction).Assembly==
                typeof(ReadOnlyWindowsPipeObserver).Assembly,
                "original coordinator only linked, never dispatched");
        });
        Console.WriteLine("P103_REAL_WINDOWS_NAMED_PIPE_NATIVE_CASES_PASSED="+passed);
        Console.WriteLine("P103_REAL_WINDOWS_NAMED_PIPE_NATIVE_CASES_FAILED="+failed);
        Console.WriteLine("P103_OS_PEER_SID_OBSERVED_NOT_USER_CONSENT=TRUE");
        Console.WriteLine("P103_WIRE_RESPONSE_DENIED_ONLY=TRUE");
        Console.WriteLine("P103_NATIVE_WIN_CRED_EFFECTS=NONE");
        Console.WriteLine("P103_PRODUCTION_PIPE_LISTENER_INSTALLED=FALSE");
        Console.WriteLine("P103_P61_NATIVE_EFFECT_RACE=OPEN");
        Console.WriteLine("P103_C1_PRODUCTION_RELEASE=HOLD");
        return failed==0 && passed==16?0:1;
    }
}
