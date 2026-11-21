#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P293_FAKE_WITNESS_ONLY && !RELEASE
using System;
using System.Collections.Generic;

namespace P293FakeDevelopment
{
    internal enum Outcome { Hold, InProgress, RecoveryRequired, FakeDevelopmentSequenceCoherent }
    internal enum Phase
    {
        NativeAbsentBefore, CreateReturned, Configuration, StartReturned, RunningStatus,
        IndependentProcessHandle, KernelTokenOne, KernelTokenTwo, StopReturned, StoppedStatus,
        DeleteReturned, ScmHandlesClosed, NativeAbsentAfter, RetainedProcessSignaled,
        ExactImageChildAbsent, Complete
    }
    internal enum Origin { Unknown, FakeNative, FakeCim }
    internal enum ServiceState { Unknown, StartPending, Running, StopPending, Stopped }

    // All strings and numbers are synthetic claims. No field is an OS handle or authority.
    internal sealed class Episode
    {
        internal readonly string Session, Name, Boot, Source, Nonce, Image, Account, Principal, Sid;
        internal readonly long Generation;
        internal Episode(string session, string name, string boot, long generation, string source,
            string nonce, string image, string account, string principal, string sid)
        {
            Session=session; Name=name; Boot=boot; Generation=generation; Source=source;
            Nonce=nonce; Image=image; Account=account; Principal=principal; Sid=sid;
        }
        internal bool Valid()
        {
            foreach (string s in new[] {Session,Name,Boot,Source,Nonce,Image,Account,Principal,Sid})
                if (String.IsNullOrWhiteSpace(s) || s.Length > 256 || s.IndexOf('|') >= 0) return false;
            return Generation > 0 && Account == "NT SERVICE\\" + Name && Principal == Sid &&
                Sid.StartsWith("S-1-5-80-", StringComparison.Ordinal);
        }
        internal string Key { get { return Session+"|"+Name+"|"+Boot+"|"+Generation+"|"+Source; } }
        internal bool Same(Episode e)
        {
            return e != null && Session==e.Session && Name==e.Name && Boot==e.Boot &&
                Generation==e.Generation && Source==e.Source && Nonce==e.Nonce && Image==e.Image &&
                Account==e.Account && Principal==e.Principal && Sid==e.Sid;
        }
    }

    // Explicit constructor: zero/default values never silently supply missing evidence.
    internal sealed class FakeObservation
    {
        internal readonly Episode Episode;
        internal readonly Phase Kind;
        internal readonly int Ordinal, Code, Pid;
        internal readonly long Tick, Birth;
        internal readonly Origin Origin;
        internal readonly ServiceState State;
        internal readonly string Name, Account, Image, Principal, Sid, Handle, Token, Capture;
        internal readonly bool Restricted, Impersonating, Retained, Signaled, ScmClosed,
            ChildAbsent, TimedOut, AlternateEffectRoute, Revoked;
        internal FakeObservation(Episode episode, Phase kind, int ordinal, long tick, Origin origin,
            int code, ServiceState state, int pid, long birth, string name, string account,
            string image, string principal, string sid, string handle, string token, string capture,
            bool restricted, bool impersonating, bool retained, bool signaled, bool scmClosed,
            bool childAbsent, bool timedOut, bool alternateEffectRoute, bool revoked)
        {
            Episode=episode; Kind=kind; Ordinal=ordinal; Tick=tick; Origin=origin; Code=code;
            State=state; Pid=pid; Birth=birth; Name=name; Account=account; Image=image;
            Principal=principal; Sid=sid; Handle=handle; Token=token; Capture=capture;
            Restricted=restricted; Impersonating=impersonating; Retained=retained; Signaled=signaled;
            ScmClosed=scmClosed; ChildAbsent=childAbsent; TimedOut=timedOut;
            AlternateEffectRoute=alternateEffectRoute; Revoked=revoked;
        }
    }

    internal sealed class P293NonDeployableScmWitnessGate
    {
        // Bounded, never evicted, process-local replay reservations. A restart proves nothing.
        private static readonly object ReservationsLock = new object();
        private static readonly HashSet<string> Episodes = new HashSet<string>(StringComparer.Ordinal);
        private static readonly HashSet<string> Nonces = new HashSet<string>(StringComparer.Ordinal);
        private readonly object sync = new object();
        private readonly Episode episode;
        private Phase next = Phase.NativeAbsentBefore;
        private Outcome result = Outcome.Hold;
        private bool terminal, mayExist;
        private int ordinal, pid;
        private long firstTick, lastTick, birth;
        private string handle, token, capture;

        internal P293NonDeployableScmWitnessGate(Episode identity)
        {
            episode=identity;
            if (identity == null || !identity.Valid()) { terminal=true; return; }
            lock (ReservationsLock)
            {
                if (Episodes.Count >= 4096 || Episodes.Contains(identity.Key) || Nonces.Contains(identity.Nonce))
                { terminal=true; return; }
                Episodes.Add(identity.Key); Nonces.Add(identity.Nonce);
            }
            result=Outcome.InProgress;
        }
        internal Outcome Result { get { lock(sync) { return result; } } }
        internal Phase NextPhase { get { lock(sync) { return next; } } }
        internal bool ClientAdmissionAllowed() { return false; }
        internal bool CredentialEffectAllowed() { return false; }
        internal bool ApprovedServiceProvenance() { return false; }
        internal bool ProductionReleaseAllowed() { return false; }
        private Outcome Refuse()
        {
            terminal=true; result=mayExist ? Outcome.RecoveryRequired : Outcome.Hold; return result;
        }
        internal Outcome Finish()
        {
            lock(sync)
            {
                if (!terminal || result != Outcome.FakeDevelopmentSequenceCoherent) return Refuse();
                return result;
            }
        }
        internal Outcome Observe(FakeObservation e)
        {
            lock(sync)
            {
                if (terminal) return Refuse();
                // Even a failed/uncertain create response may leave resources: retain recovery duty.
                if (next == Phase.CreateReturned) mayExist=true;
                if (e == null || !episode.Same(e.Episode) || e.Kind != next ||
                    e.Ordinal != ordinal+1 || e.Tick <= 0 || e.Origin != Origin.FakeNative ||
                    e.TimedOut || e.AlternateEffectRoute || e.Revoked || e.Impersonating ||
                    (ordinal > 0 && (e.Tick <= lastTick || e.Tick-lastTick > 10 || e.Tick-firstTick > 120)))
                    return Refuse();
                bool absent=next==Phase.NativeAbsentBefore || next==Phase.NativeAbsentAfter;
                if (e.Code != (absent ? 1060 : 0)) return Refuse();
                // Exact bounded subject on every event, including absence and child observations.
                if (e.Name!=episode.Name || e.Account!=episode.Account || e.Image!=episode.Image ||
                    e.Principal!=episode.Principal || e.Sid!=episode.Sid) return Refuse();
                switch(next)
                {
                    case Phase.Configuration:
                        if (!e.Restricted) return Refuse();
                        break;
                    case Phase.RunningStatus:
                        if (e.State!=ServiceState.Running || e.Pid<=0) return Refuse();
                        pid=e.Pid;
                        break;
                    case Phase.IndependentProcessHandle:
                        if (e.State!=ServiceState.Running || e.Pid!=pid || e.Birth<=0 ||
                            String.IsNullOrWhiteSpace(e.Handle) || !e.Retained || e.Signaled) return Refuse();
                        birth=e.Birth; handle=e.Handle;
                        break;
                    case Phase.KernelTokenOne:
                    case Phase.KernelTokenTwo:
                        if (!ExactProcess(e) || e.State!=ServiceState.Running || !e.Restricted || e.Signaled ||
                            String.IsNullOrWhiteSpace(e.Token) || String.IsNullOrWhiteSpace(e.Capture)) return Refuse();
                        if (next==Phase.KernelTokenOne) { token=e.Token; capture=e.Capture; }
                        else if (e.Token!=token || e.Capture==capture) return Refuse();
                        break;
                    case Phase.StopReturned:
                        if (!ExactProcess(e)) return Refuse();
                        break;
                    case Phase.StoppedStatus:
                        // The SCM PID is deliberately unusable when STOPPED; retained birth/handle persist.
                        if (e.State!=ServiceState.Stopped || e.Pid!=0 || !e.Retained ||
                            e.Handle!=handle || e.Birth!=birth) return Refuse();
                        break;
                    case Phase.DeleteReturned:
                    case Phase.ScmHandlesClosed:
                    case Phase.NativeAbsentAfter:
                    case Phase.RetainedProcessSignaled:
                    case Phase.ExactImageChildAbsent:
                        if (!ExactProcess(e)) return Refuse();
                        if (next>=Phase.ScmHandlesClosed && !e.ScmClosed) return Refuse();
                        if (next>=Phase.RetainedProcessSignaled && !e.Signaled) return Refuse();
                        if (next==Phase.ExactImageChildAbsent && !e.ChildAbsent) return Refuse();
                        break;
                }
                ordinal=e.Ordinal;
                if (ordinal==1) firstTick=e.Tick;
                lastTick=e.Tick;
                next=(Phase)((int)next+1);
                if (next==Phase.Complete) { terminal=true; result=Outcome.FakeDevelopmentSequenceCoherent; }
                return result;
            }
        }
        private bool ExactProcess(FakeObservation e)
        {
            return e.Pid==pid && e.Birth==birth && e.Handle==handle && e.Retained;
        }
    }
}
#else
#error P293_DEBUG_ISOLATED_FAKE_WITNESS_ONLY_REQUIRED
#endif
