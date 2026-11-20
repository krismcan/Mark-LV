#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P288_SYNTHETIC_PROVENANCE_REVIEW_ONLY
#error P288_SYNTHETIC_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED
#endif
using System;
using System.Threading;

namespace Nayeon.ByokC1.P288Review
{
    internal enum SequenceStatus
    {
        MissingTrustedLiveProvenance, AwaitingSyntheticEvents, SyntheticRevalidated,
        SyntheticStepOnly, InvalidOrder, IdentityChanged, HandleChanged, PeerMismatch,
        Impersonating, QueryFailed, Disconnected, Cancelled, Revoked, Expired,
        WrongThread, InvalidTicket, AlreadyConsumed
    }
    internal enum SyntheticEvent
    {
        ServiceObserved, ConnectCompleted, MessageReadCompleted,
        PeerAuthenticatedAfterRevert, FinalRevalidation,
        Disconnect, Reconnect, Cancel, Revoke, Expire
    }
    internal enum SyntheticChange
    {
        None, SwapRoles, SameSid, ScmPid, ServicePid, ServiceBirth, ClientBirth,
        ServiceToken, ClientToken, ServiceLogon, ClientLogon, ServiceModified,
        ClientModified, ServiceSession, ClientSession, ServiceSid, ClientSid,
        NonPrimaryService, NonPrimaryClient, ServiceHandleReplacement,
        ClientHandleReplacement, PipeHandleReplacement, ClosedServiceHandle,
        ClosedClientHandle, ClosedPipeHandle, ServiceExited, ClientExited,
        PipePeerPid, PipePeerSession, MessageUser, MessageLogon, EndpointReplacement,
        AmbientThreadToken, ThreadQueryFailure, PeerQueryFailure, RestoreFixtureValues
    }
    internal sealed class SequenceEvidence
    {
        internal readonly SequenceStatus Status;
        internal SequenceEvidence(SequenceStatus status) { Status = status; }
        internal bool LiveIpcAllowed { get { return false; } }
        internal bool CredentialAllowed { get { return false; } }
        internal bool StoreAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
    }
    // An opaque synthetic receipt, not a token accepted by any live consumer.
    // Caller-created/equal-looking receipts cannot replace the exact pending object.
    internal sealed class SyntheticTicket
    {
        private readonly object issuer, connection;
        private readonly long revision;
        internal SyntheticTicket(object source, object epoch, long value)
        { issuer = source; connection = epoch; revision = value; }
        internal bool Matches(object source, object epoch, long value)
        { return Object.ReferenceEquals(issuer, source) && Object.ReferenceEquals(connection, epoch) && revision == value; }
    }
    internal static class ProvenanceSequence
    {
        internal static SequenceEvidence ObserveLiveAdmission()
        { return new SequenceEvidence(SequenceStatus.MissingTrustedLiveProvenance); }
        internal static void DemandBeforeRealPipeCreation()
        { throw new InvalidOperationException("P288_NO_AUTHENTICATED_LIVE_ISSUER"); }

        // This entire world is a private fixed fixture. No OS queries, live handles,
        // caller snapshots, callbacks, wire fields, clocks or production issuers exist.
        // Its monitor demonstrates synthetic ordering ONLY, not OS-atomic custody.
        internal sealed class SyntheticFixture
        {
            private sealed class Actor
            {
                internal readonly bool Service, Primary;
                internal readonly string Sid;
                internal readonly uint Pid, Session;
                internal readonly long Birth, Token, Logon, Modified;
                internal readonly object Handle;
                internal Actor(bool service, string sid, uint pid, uint session, long birth,
                    long token, long logon, long modified, bool primary, object handle)
                {
                    Service = service; Sid = sid; Pid = pid; Session = session; Birth = birth;
                    Token = token; Logon = logon; Modified = modified; Primary = primary; Handle = handle;
                }
                internal bool Same(Actor other)
                {
                    return other != null && Service == other.Service && Sid == other.Sid && Pid == other.Pid &&
                        Session == other.Session && Birth == other.Birth && Token == other.Token &&
                        Logon == other.Logon && Modified == other.Modified && Primary && other.Primary;
                }
            }
            private readonly object gate = new object(), issuer = new object(), connection = new object();
            private readonly object originalPipe = new object(), originalEndpoint = new object();
            private readonly Thread ownerThread = Thread.CurrentThread;
            private readonly Actor initialService, initialClient;
            private Actor service, client;
            private object pipe, endpoint;
            private bool serviceHandleOpen, clientHandleOpen, pipeHandleOpen, serviceAlive, clientAlive;
            private bool ambientThreadToken, threadQueryFailed, peerQueryFailed;
            private uint scmPid, pipePeerPid, pipePeerSession;
            private string messageUser;
            private long messageLogon, revision;
            private int stage;
            private SequenceStatus? terminal;
            private SyntheticTicket pending;

            private SyntheticFixture()
            {
                initialService = new Actor(true, "S-1-5-80-101-202-303-404-505", 100, 0, 10, 11, 12, 13, true, new object());
                initialClient = new Actor(false, "S-1-5-21-111-222-333-1001", 200, 1, 20, 21, 22, 23, true, new object());
                Restore();
            }
            internal static SyntheticFixture Create() { return new SyntheticFixture(); }
            private void Restore()
            {
                service = initialService; client = initialClient;
                pipe = originalPipe; endpoint = originalEndpoint;
                serviceHandleOpen = clientHandleOpen = pipeHandleOpen = serviceAlive = clientAlive = true;
                ambientThreadToken = threadQueryFailed = peerQueryFailed = false;
                scmPid = service.Pid; pipePeerPid = client.Pid; pipePeerSession = client.Session;
                messageUser = client.Sid; messageLogon = client.Logon;
                // Never resets stage, revision, pending ticket or terminal refusal.
            }
            private SequenceEvidence Fail(SequenceStatus reason)
            {
                if (!terminal.HasValue) terminal = reason;
                pending = null;
                return new SequenceEvidence(terminal.Value);
            }
            private SequenceStatus? CurrentFailure()
            {
                if (terminal.HasValue) return terminal;
                if (!Object.ReferenceEquals(Thread.CurrentThread, ownerThread)) return SequenceStatus.WrongThread;
                if (threadQueryFailed || peerQueryFailed) return SequenceStatus.QueryFailed;
                if (ambientThreadToken) return SequenceStatus.Impersonating;
                if (!serviceAlive || !clientAlive || !service.Same(initialService) || !client.Same(initialClient) ||
                    !service.Service || client.Service || service.Sid == client.Sid || scmPid != service.Pid)
                    return SequenceStatus.IdentityChanged;
                if (!serviceHandleOpen || !clientHandleOpen || !pipeHandleOpen ||
                    !Object.ReferenceEquals(service.Handle, initialService.Handle) ||
                    !Object.ReferenceEquals(client.Handle, initialClient.Handle) ||
                    !Object.ReferenceEquals(pipe, originalPipe) || !Object.ReferenceEquals(endpoint, originalEndpoint))
                    return SequenceStatus.HandleChanged;
                if (pipePeerPid != client.Pid || pipePeerSession != client.Session ||
                    messageUser != client.Sid || messageLogon != client.Logon) return SequenceStatus.PeerMismatch;
                return null;
            }
            internal SequenceEvidence Observe()
            {
                lock (gate)
                {
                    SequenceStatus? failure = CurrentFailure();
                    if (failure.HasValue) return Fail(failure.Value);
                    return new SequenceEvidence(stage == 5 ? SequenceStatus.SyntheticRevalidated : SequenceStatus.AwaitingSyntheticEvents);
                }
            }
            internal SequenceEvidence Send(SyntheticEvent value)
            {
                lock (gate)
                {
                    // Terminal-only signals may revoke from another thread; they
                    // cannot bind a role, advance the sequence or mint a ticket.
                    switch (value)
                    {
                        case SyntheticEvent.Cancel: return Fail(SequenceStatus.Cancelled);
                        case SyntheticEvent.Revoke: return Fail(SequenceStatus.Revoked);
                        case SyntheticEvent.Expire: return Fail(SequenceStatus.Expired);
                        case SyntheticEvent.Disconnect: case SyntheticEvent.Reconnect: return Fail(SequenceStatus.Disconnected);
                    }
                    SequenceStatus? failure = CurrentFailure();
                    if (failure.HasValue) return Fail(failure.Value);
                    // Explicit mapping: undefined enum values and duplicate/skipped events deny.
                    SyntheticEvent[] expected = { SyntheticEvent.ServiceObserved, SyntheticEvent.ConnectCompleted,
                        SyntheticEvent.MessageReadCompleted, SyntheticEvent.PeerAuthenticatedAfterRevert, SyntheticEvent.FinalRevalidation };
                    if (stage >= expected.Length || value != expected[stage]) return Fail(SequenceStatus.InvalidOrder);
                    stage++; revision++;
                    if (stage == 5) pending = new SyntheticTicket(issuer, connection, revision);
                    return Observe();
                }
            }
            internal SyntheticTicket Ticket
            {
                get
                {
                    lock (gate)
                    {
                        SequenceStatus? failure = CurrentFailure();
                        if (failure.HasValue) { Fail(failure.Value); return null; }
                        return stage == 5 ? pending : null;
                    }
                }
            }
            internal SequenceEvidence ConsumeSynthetic(SyntheticTicket ticket)
            {
                lock (gate)
                {
                    SequenceStatus? failure = CurrentFailure();
                    if (failure.HasValue) return Fail(failure.Value);
                    if (stage != 5 || pending == null || !Object.ReferenceEquals(ticket, pending) ||
                        !ticket.Matches(issuer, connection, revision)) return Fail(SequenceStatus.InvalidTicket);
                    // One-use reservation precedes the only result: an in-memory enum.
                    // No delegate, service, pipe or effect operation is dispatched.
                    pending = null; terminal = SequenceStatus.AlreadyConsumed;
                    return new SequenceEvidence(SequenceStatus.SyntheticStepOnly);
                }
            }
            // Finite faults control this synthetic world; they cannot issue live provenance.
            internal void Change(SyntheticChange value)
            {
                lock (gate)
                {
                    Actor s = service, c = client;
                    switch (value)
                    {
                        case SyntheticChange.None: return;
                        case SyntheticChange.RestoreFixtureValues: Restore(); return;
                        case SyntheticChange.SwapRoles: service = c; client = s; break;
                        case SyntheticChange.SameSid: client = Copy(c.Service, s.Sid, c.Pid, c.Session, c.Birth, c.Token, c.Logon, c.Modified, c.Primary, c.Handle); break;
                        case SyntheticChange.ScmPid: scmPid++; break;
                        case SyntheticChange.ServicePid: service = Copy(s.Service, s.Sid, s.Pid + 1, s.Session, s.Birth, s.Token, s.Logon, s.Modified, s.Primary, s.Handle); break;
                        case SyntheticChange.ServiceBirth: case SyntheticChange.ClientBirth:
                        case SyntheticChange.ServiceToken: case SyntheticChange.ClientToken:
                        case SyntheticChange.ServiceLogon: case SyntheticChange.ClientLogon:
                        case SyntheticChange.ServiceModified: case SyntheticChange.ClientModified:
                        case SyntheticChange.ServiceSession: case SyntheticChange.ClientSession:
                        case SyntheticChange.ServiceSid: case SyntheticChange.ClientSid:
                        case SyntheticChange.NonPrimaryService: case SyntheticChange.NonPrimaryClient:
                        case SyntheticChange.ServiceHandleReplacement: case SyntheticChange.ClientHandleReplacement:
                            bool targetService = value == SyntheticChange.ServiceBirth || value == SyntheticChange.ServiceToken ||
                                value == SyntheticChange.ServiceLogon || value == SyntheticChange.ServiceModified ||
                                value == SyntheticChange.ServiceSession || value == SyntheticChange.ServiceSid ||
                                value == SyntheticChange.NonPrimaryService || value == SyntheticChange.ServiceHandleReplacement;
                            Actor a = targetService ? s : c;
                            Actor changed = Copy(a.Service,
                                value == SyntheticChange.ServiceSid || value == SyntheticChange.ClientSid ? a.Sid + "-9" : a.Sid,
                                a.Pid, a.Session + (value == SyntheticChange.ServiceSession || value == SyntheticChange.ClientSession ? 1u : 0u),
                                a.Birth + (value == SyntheticChange.ServiceBirth || value == SyntheticChange.ClientBirth ? 1 : 0),
                                a.Token + (value == SyntheticChange.ServiceToken || value == SyntheticChange.ClientToken ? 1 : 0),
                                a.Logon + (value == SyntheticChange.ServiceLogon || value == SyntheticChange.ClientLogon ? 1 : 0),
                                a.Modified + (value == SyntheticChange.ServiceModified || value == SyntheticChange.ClientModified ? 1 : 0),
                                value == SyntheticChange.NonPrimaryService || value == SyntheticChange.NonPrimaryClient ? false : a.Primary,
                                value == SyntheticChange.ServiceHandleReplacement || value == SyntheticChange.ClientHandleReplacement ? new object() : a.Handle);
                            if (targetService) service = changed; else client = changed;
                            break;
                        case SyntheticChange.PipeHandleReplacement: pipe = new object(); break;
                        case SyntheticChange.EndpointReplacement: endpoint = new object(); break;
                        case SyntheticChange.ClosedServiceHandle: serviceHandleOpen = false; break;
                        case SyntheticChange.ClosedClientHandle: clientHandleOpen = false; break;
                        case SyntheticChange.ClosedPipeHandle: pipeHandleOpen = false; break;
                        case SyntheticChange.ServiceExited: serviceAlive = false; break;
                        case SyntheticChange.ClientExited: clientAlive = false; break;
                        case SyntheticChange.PipePeerPid: pipePeerPid++; break;
                        case SyntheticChange.PipePeerSession: pipePeerSession++; break;
                        case SyntheticChange.MessageUser: messageUser = s.Sid; break;
                        case SyntheticChange.MessageLogon: messageLogon++; break;
                        case SyntheticChange.AmbientThreadToken: ambientThreadToken = true; break;
                        case SyntheticChange.ThreadQueryFailure: threadQueryFailed = true; break;
                        case SyntheticChange.PeerQueryFailure: peerQueryFailed = true; break;
                        default: Fail(SequenceStatus.InvalidOrder); break;
                    }
                    // Observe mutations immediately, so even fixture-value restoration
                    // cannot hide a modeled close/replacement/change between uses.
                    SequenceStatus? failure = CurrentFailure();
                    if (failure.HasValue) Fail(failure.Value);
                }
            }
            private static Actor Copy(bool service, string sid, uint pid, uint session,
                long birth, long token, long logon, long modified, bool primary, object handle)
            { return new Actor(service, sid, pid, session, birth, token, logon, modified, primary, handle); }
        }
    }
}
