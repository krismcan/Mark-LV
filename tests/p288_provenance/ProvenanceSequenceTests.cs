#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P288_SYNTHETIC_PROVENANCE_REVIEW_ONLY
#error P288_SYNTHETIC_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED
#endif
using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Threading;
using Nayeon.ByokC1.P288Review;
using Fixture = Nayeon.ByokC1.P288Review.ProvenanceSequence.SyntheticFixture;

internal static class ProvenanceSequenceTests
{
    private static int assertions, cases;
    private static string group = "START";
    private static readonly SyntheticEvent[] order = { SyntheticEvent.ServiceObserved, SyntheticEvent.ConnectCompleted,
        SyntheticEvent.MessageReadCompleted, SyntheticEvent.PeerAuthenticatedAfterRevert, SyntheticEvent.FinalRevalidation };
    private static void Check(bool value)
    { assertions++; if (!value) throw new InvalidOperationException("P288_ASSERT"); }
    private static void NoAuthority(SequenceEvidence value)
    { Check(!value.LiveIpcAllowed && !value.CredentialAllowed && !value.StoreAllowed && !value.ProductionEligible); }
    private static void Status(SequenceEvidence value, SequenceStatus expected)
    { Check(value.Status == expected); NoAuthority(value); }
    private static Fixture Prefix(int count)
    {
        Fixture fixture = Fixture.Create();
        Status(fixture.Observe(), SequenceStatus.AwaitingSyntheticEvents);
        Check(fixture.Ticket == null);
        for (int i = 0; i < count; i++)
            Status(fixture.Send(order[i]), i == 4 ? SequenceStatus.SyntheticRevalidated : SequenceStatus.AwaitingSyntheticEvents);
        Check((fixture.Ticket != null) == (count == 5));
        return fixture;
    }
    private static string Hash(string path)
    {
        using (SHA256 sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-", "");
    }
    private static void SourceAndInherited()
    {
        Check(Hash("native_c1_successor/P286SafeDevelopmentPipeAdapter.cs") ==
            "15D05B5F577DFD25BDD0551CE37480D10C62FFC7BC034784E781E242B72A0AF9");
        // P287's complete unchanged harness includes the unchanged P286 managed
        // completion schedules: connect/read/write, early timeout and late cleanup.
        Check(ServiceClientBoundaryTests.Main() == 0);
        string source = File.ReadAllText("native_c1_successor/P288SyntheticProvenanceSequence.cs");
        foreach (string forbidden in new[] { "DllImport", "NamedPipeServerStream", "NamedPipeClientStream",
            "WindowsIdentity", "GetEnvironmentVariable", "Process.Start", "RunAsClient", "Func<", "Action<" })
            Check(!source.Contains(forbidden));
        foreach (FieldInfo field in typeof(SyntheticTicket).GetFields(BindingFlags.Instance | BindingFlags.NonPublic))
            Check(field.IsInitOnly);
        cases++;
    }
    private static void LiveDenied()
    {
        Status(ProvenanceSequence.ObserveLiveAdmission(), SequenceStatus.MissingTrustedLiveProvenance);
        foreach (bool afterSynthetic in new[] { false, true })
        {
            if (afterSynthetic) { Fixture f = Prefix(5); Status(f.ConsumeSynthetic(f.Ticket), SequenceStatus.SyntheticStepOnly); }
            bool refused = false;
            try { ProvenanceSequence.DemandBeforeRealPipeCreation(); }
            catch (InvalidOperationException error) { refused = error.Message == "P288_NO_AUTHENTICATED_LIVE_ISSUER"; }
            Check(refused);
            Status(ProvenanceSequence.ObserveLiveAdmission(), SequenceStatus.MissingTrustedLiveProvenance);
            cases++;
        }
        // Caller-forged evidence/ticket labels do not alter any admission route.
        NoAuthority(new SequenceEvidence(SequenceStatus.SyntheticStepOnly));
        Fixture forged = Prefix(5);
        Status(forged.ConsumeSynthetic(new SyntheticTicket(new object(), new object(), 5)), SequenceStatus.InvalidTicket);
        cases++;
    }
    private static SequenceStatus Expected(SyntheticChange value)
    {
        switch (value)
        {
            case SyntheticChange.ServiceHandleReplacement: case SyntheticChange.ClientHandleReplacement:
            case SyntheticChange.PipeHandleReplacement: case SyntheticChange.EndpointReplacement:
            case SyntheticChange.ClosedServiceHandle: case SyntheticChange.ClosedClientHandle:
            case SyntheticChange.ClosedPipeHandle: return SequenceStatus.HandleChanged;
            case SyntheticChange.PipePeerPid: case SyntheticChange.PipePeerSession:
            case SyntheticChange.MessageUser: case SyntheticChange.MessageLogon: return SequenceStatus.PeerMismatch;
            case SyntheticChange.AmbientThreadToken: return SequenceStatus.Impersonating;
            case SyntheticChange.ThreadQueryFailure: case SyntheticChange.PeerQueryFailure: return SequenceStatus.QueryFailed;
            default: return SequenceStatus.IdentityChanged;
        }
    }
    private static void FaultsAtEveryBoundary()
    {
        foreach (SyntheticChange change in Enum.GetValues(typeof(SyntheticChange)))
        {
            if (change == SyntheticChange.None || change == SyntheticChange.RestoreFixtureValues) continue;
            for (int prefix = 0; prefix <= 5; prefix++)
            {
                Fixture fixture = Prefix(prefix); SyntheticTicket old = fixture.Ticket;
                fixture.Change(change);
                SequenceStatus expected = Expected(change);
                Status(fixture.Observe(), expected); Check(fixture.Ticket == null);
                Status(fixture.ConsumeSynthetic(old), expected);
                fixture.Change(SyntheticChange.RestoreFixtureValues);
                fixture.Change(SyntheticChange.None);
                Status(fixture.Observe(), expected); // no resurrection even on exact old values
                foreach (SyntheticEvent next in order) Status(fixture.Send(next), expected);
                Status(fixture.ConsumeSynthetic(old), expected);
                cases++;
            }
        }
    }
    private static SequenceStatus StopReason(SyntheticEvent value)
    {
        switch (value)
        {
            case SyntheticEvent.Cancel: return SequenceStatus.Cancelled;
            case SyntheticEvent.Revoke: return SequenceStatus.Revoked;
            case SyntheticEvent.Expire: return SequenceStatus.Expired;
            case SyntheticEvent.Disconnect: case SyntheticEvent.Reconnect: return SequenceStatus.Disconnected;
            default: return SequenceStatus.InvalidOrder;
        }
    }
    private static void EventOrderAndTerminalStates()
    {
        for (int prefix = 0; prefix <= 5; prefix++)
        {
            foreach (SyntheticEvent next in Enum.GetValues(typeof(SyntheticEvent)))
            {
                Fixture fixture = Prefix(prefix);
                if (prefix < 5 && next == order[prefix])
                {
                    Status(fixture.Send(next), prefix == 4 ? SequenceStatus.SyntheticRevalidated : SequenceStatus.AwaitingSyntheticEvents);
                }
                else
                {
                    SyntheticTicket old = fixture.Ticket;
                    SequenceStatus expected = StopReason(next);
                    Status(fixture.Send(next), expected);
                    fixture.Change(SyntheticChange.RestoreFixtureValues);
                    foreach (SyntheticEvent retry in order) Status(fixture.Send(retry), expected);
                    Check(fixture.Ticket == null); Status(fixture.ConsumeSynthetic(old), expected);
                }
                cases++;
            }
            Fixture unknown = Prefix(prefix);
            Status(unknown.Send((SyntheticEvent)999), SequenceStatus.InvalidOrder); cases++;
            Fixture early = Prefix(prefix);
            Status(early.ConsumeSynthetic(null), SequenceStatus.InvalidTicket); cases++;
        }
        Fixture unknownChange = Prefix(5);
        unknownChange.Change((SyntheticChange)999);
        Status(unknownChange.Observe(), SequenceStatus.InvalidOrder); cases++;
    }
    private static void TicketsAndReconnect()
    {
        Fixture first = Prefix(5), second = Prefix(5);
        SyntheticTicket ticket = first.Ticket;
        Check(Object.ReferenceEquals(ticket, first.Ticket));
        Status(second.ConsumeSynthetic(ticket), SequenceStatus.InvalidTicket);
        Status(first.ConsumeSynthetic(ticket), SequenceStatus.SyntheticStepOnly);
        Status(first.ConsumeSynthetic(ticket), SequenceStatus.AlreadyConsumed);
        Check(first.Ticket == null);
        first.Change(SyntheticChange.RestoreFixtureValues);
        Status(first.Send(SyntheticEvent.ConnectCompleted), SequenceStatus.AlreadyConsumed); cases++;

        Fixture oldConnection = Prefix(5); SyntheticTicket oldTicket = oldConnection.Ticket;
        Status(oldConnection.Send(SyntheticEvent.Disconnect), SequenceStatus.Disconnected);
        Status(oldConnection.Send(SyntheticEvent.Reconnect), SequenceStatus.Disconnected);
        Fixture newConnection = Prefix(5);
        Status(newConnection.ConsumeSynthetic(oldTicket), SequenceStatus.InvalidTicket);
        // A new fixture needs the entire event sequence and its own one-use ticket.
        Fixture fresh = Prefix(5); Status(fresh.ConsumeSynthetic(fresh.Ticket), SequenceStatus.SyntheticStepOnly); cases++;
    }
    private static void CallbackAndCancelSchedules()
    {
        // Model both serialized outcomes at the consume/cancel boundary. This
        // proves monitor ordering only; it cannot prove a kernel-side use lease.
        for (int i = 0; i < 128; i++)
        {
            Fixture fixture = Prefix(5); SyntheticTicket old = fixture.Ticket;
            if ((i & 1) == 0)
            {
                Status(fixture.Send(SyntheticEvent.Cancel), SequenceStatus.Cancelled);
                Status(fixture.ConsumeSynthetic(old), SequenceStatus.Cancelled);
            }
            else
            {
                Status(fixture.ConsumeSynthetic(old), SequenceStatus.SyntheticStepOnly);
                Status(fixture.Send(SyntheticEvent.Cancel), SequenceStatus.AlreadyConsumed);
            }
            cases++;
        }
        // A callback can finish End*/cleanup (P286) without gaining owner-thread
        // provenance authority. An attempted P288 transfer permanently poisons it.
        for (int prefix = 0; prefix <= 5; prefix++)
        {
            Fixture fixture = Prefix(prefix); SyntheticTicket old = fixture.Ticket;
            SequenceEvidence result = null; Exception error = null;
            Thread callback = new Thread(delegate() {
                try { result = fixture.ConsumeSynthetic(old); } catch (Exception caught) { error = caught; }
            });
            callback.IsBackground = true; callback.Start();
            Check(callback.Join(2000)); Check(error == null);
            Status(result, SequenceStatus.WrongThread);
            Status(fixture.Observe(), SequenceStatus.WrongThread);
            fixture.Change(SyntheticChange.RestoreFixtureValues);
            Status(fixture.ConsumeSynthetic(old), SequenceStatus.WrongThread); cases++;
        }
        // Actual managed-thread ordering: cancellation is revocation-only and may
        // arrive off-owner. Both cancel-before-consume and consume-before-cancel
        // are bounded with events, without sleeps or OS pipe activity.
        for (int schedule = 0; schedule < 2; schedule++)
        using (var release = new ManualResetEvent(false))
        using (var done = new ManualResetEvent(false))
        {
            Fixture fixture = Prefix(5); SyntheticTicket old = fixture.Ticket;
            SequenceEvidence cancellation = null; Exception failure = null;
            Thread canceller = new Thread(delegate() {
                try
                {
                    if (!release.WaitOne(2000)) throw new TimeoutException();
                    cancellation = fixture.Send(SyntheticEvent.Cancel);
                }
                catch (Exception error) { failure = error; }
                finally { done.Set(); }
            });
            canceller.IsBackground = true; canceller.Start();
            try
            {
                if (schedule == 0)
                {
                    release.Set(); Check(done.WaitOne(2000));
                    Status(fixture.ConsumeSynthetic(old), SequenceStatus.Cancelled);
                }
                else
                {
                    Status(fixture.ConsumeSynthetic(old), SequenceStatus.SyntheticStepOnly);
                    release.Set(); Check(done.WaitOne(2000));
                }
            }
            finally { release.Set(); Check(canceller.Join(2000)); }
            Check(failure == null);
            Status(cancellation, schedule == 0 ? SequenceStatus.Cancelled : SequenceStatus.AlreadyConsumed);
            Status(fixture.ConsumeSynthetic(old), schedule == 0 ? SequenceStatus.Cancelled : SequenceStatus.AlreadyConsumed);
            cases++;
        }
    }
    public static int Main()
    {
        // Accident barriers only; these flags are never role proof or authorization.
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
            Environment.GetEnvironmentVariable("ImageOS") != "win22" ||
            String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) ||
            String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase)) return 2;
        try
        {
            group = "INHERITED"; SourceAndInherited();
            group = "LIVE_DENIAL"; LiveDenied();
            group = "FAULTS"; FaultsAtEveryBoundary();
            group = "EVENT_ORDER"; EventOrderAndTerminalStates();
            group = "TICKETS"; TicketsAndReconnect();
            group = "CALLBACK_CANCEL"; CallbackAndCancelSchedules();
            Console.WriteLine("P288_FOCUSED=PASS CASES=" + cases + " ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P288_LIVE=HOLD PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=HIGH_OPEN"); return 0;
        }
        catch (Exception error)
        {
            Console.WriteLine("P288_FOCUSED=HOLD GROUP=" + group + " CASES=" + cases + " ASSERTIONS=" + assertions + " ERROR=" + error.GetType().Name);
            return 1;
        }
    }
}
