#if !C1_P266_DEVELOPMENT_ONLY
#error P266_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED
#endif
#if !C1_P265_DEVELOPMENT_ONLY
#error P266_REQUIRES_P265_DEVELOPMENT_ONLY
#endif
#if !DEBUG
#error P266_NO_RELEASE_BUILD
#endif
// DEVELOPMENT ONLY: owns the unchanged P265 adapter; no credential backend exists.
using System;
using System.Security.Principal;
using System.ServiceProcess;
using System.Threading;
using Nayeon.ByokC1.P265Development;

namespace Nayeon.ByokC1.P266Development
{
    internal sealed class Disposition
    {
        internal readonly bool Started, Stopped, Revoked, Faulted, Disposed, WorkerExited;
        internal readonly int Marker, Stages, Replacements, Deletes, Requests;
        internal readonly string Endpoint;
        internal readonly DenialReason LastReason;
        internal bool CredentialAllowed { get { return false; } }
        internal bool StoreAllowed { get { return false; } }
        internal bool PrivilegedAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
        internal Disposition(bool started, bool stopped, bool revoked, bool faulted, bool disposed,
            bool exited, int marker, int stages, int replacements, int deletes, int requests,
            string endpoint, DenialReason reason)
        {
            Started = started; Stopped = stopped; Revoked = revoked; Faulted = faulted;
            Disposed = disposed; WorkerExited = exited; Marker = marker; Stages = stages;
            Replacements = replacements; Deletes = deletes; Requests = requests;
            Endpoint = endpoint; LastReason = reason;
        }
    }

    internal sealed class DevelopmentServiceIpc : ServiceBase
    {
        internal const int ServeTimeoutMs = 2000, JoinTimeoutMs = 2500, MaximumRequests = 128;
        private readonly object sync = new object();
        private DevelopmentPipeAdapter adapter;
        private Thread worker;
        private bool started, stopped, revoked, faulted, disposed, workerExited = true;
        private string endpoint;
        private int requests;
        private DenialReason lastReason = DenialReason.Closed;
        private Exception cleanupFailure;
        private readonly SyntheticFixture fixture = new SyntheticFixture();

        // Fixed integer marker/counters only. Never receives a payload or authorizes work.
        private sealed class SyntheticFixture
        {
            internal int Marker, Stages, Replacements, Deletes;
            internal void Stage() { if (Marker == 0) { Marker = 266; Stages++; } }
            internal void Replace() { if (Marker == 266) Replacements++; }
            internal void Delete() { if (Marker == 266) { Marker = 0; Deletes++; } }
        }

        internal DevelopmentServiceIpc()
        {
            ServiceName = "NayeonP266DevelopmentOnly";
            CanStop = true; CanShutdown = true; CanPauseAndContinue = false; AutoLog = false;
        }

        private bool Closed { get { return stopped || revoked || faulted || disposed; } }
        private Disposition View()
        {
            return new Disposition(started, stopped, revoked, faulted, disposed, workerExited,
                fixture.Marker, fixture.Stages, fixture.Replacements, fixture.Deletes, requests,
                Closed ? null : endpoint, lastReason);
        }
        internal Disposition Observe() { lock (sync) { return View(); } }

        internal Disposition StartDevelopment()
        {
            bool failed = false;
            lock (sync)
            {
                if (started || Closed) { faulted = true; failed = true; }
                else
                {
                    try
                    {
                        // Capture anew at startup; neither SCM name nor a configured SID is approval.
                        using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true))
                            if (thread != null) throw new InvalidOperationException("P266_THREAD_IDENTITY");
                        using (WindowsIdentity current = WindowsIdentity.GetCurrent())
                        {
                            if (current.User == null || current.IsAnonymous || current.IsSystem ||
                                current.User.IsWellKnown(WellKnownSidType.LocalServiceSid) ||
                                current.User.IsWellKnown(WellKnownSidType.NetworkServiceSid) ||
                                current.User.Value.StartsWith("S-1-5-80-", StringComparison.Ordinal))
                                throw new InvalidOperationException("P266_DEVELOPER_PRINCIPAL_REQUIRED");
                            adapter = new DevelopmentPipeAdapter(current);
                        }
                        endpoint = adapter.Endpoint;
                        worker = new Thread(ServeLoop);
                        worker.IsBackground = true;
                        workerExited = false;
                        worker.Start();
                        started = true;
                    }
                    catch
                    {
                        faulted = true;
                        workerExited = worker == null || !worker.IsAlive;
                        failed = true;
                    }
                }
                if (!failed) return View();
                CloseLocked();
            }
            return Terminate(2); // closes partially created resources; never retries startup
        }

        private void CloseLocked()
        {
            fixture.Delete();
            if (adapter != null)
            {
                try { adapter.Dispose(); }
                catch (Exception error)
                {
                    faulted = true;
                    if (cleanupFailure == null) cleanupFailure = error;
                }
            }
        }

        private void ServeLoop()
        {
            try
            {
                for (int index = 0; index < MaximumRequests; index++)
                {
                    DevelopmentPipeAdapter serving;
                    lock (sync) { if (Closed) return; serving = adapter; }
                    DenialEvidence evidence = serving.ServeOnce(ServeTimeoutMs);
                    lock (sync)
                    {
                        if (Closed) return;
                        requests++;
                        lastReason = evidence.Reason;
                        if (!evidence.ThreadRestored || !evidence.ReplyWritten ||
                            (evidence.Reason != DenialReason.DevelopmentHold &&
                             evidence.Reason != DenialReason.Replay && evidence.Reason != DenialReason.Capacity))
                        { faulted = true; CloseLocked(); return; }
                    }
                }
                lock (sync) { faulted = true; CloseLocked(); }
            }
            catch
            {
                // No retry or success receipt: unexpected worker failure is sticky evidence.
                lock (sync) { faulted = true; lastReason = DenialReason.Fault; CloseLocked(); }
            }
            finally
            {
                lock (sync)
                {
                    try { CloseLocked(); }
                    finally { workerExited = true; }
                }
            }
        }

        // Latch and close atomically, then join outside sync so worker cleanup can acquire it.
        private Disposition Terminate(int kind)
        {
            Thread joining;
            lock (sync)
            {
                if (kind == 0) stopped = true;
                else if (kind == 1) revoked = true;
                else if (kind == 2) faulted = true;
                else { stopped = true; disposed = true; }
                CloseLocked();
                joining = worker;
            }
            if (joining != null && joining.IsAlive && !joining.Join(JoinTimeoutMs))
            {
                lock (sync) { faulted = true; }
                throw new System.TimeoutException("P266_WORKER_JOIN_FAILED");
            }
            lock (sync)
            {
                if (cleanupFailure != null)
                    throw new InvalidOperationException("P266_CLEANUP_FAILED", cleanupFailure);
                return View();
            }
        }

        internal Disposition StopDevelopment() { return Terminate(0); }
        internal Disposition Revoke() { return Terminate(1); }
        internal Disposition Fault() { return Terminate(2); }
        // Local, no-argument fixture ingress is never referenced by ServeLoop or P265.
        internal Disposition StageSynthetic() { lock (sync) { if (started && !Closed) fixture.Stage(); return View(); } }
        internal Disposition ReplaceSynthetic() { lock (sync) { if (started && !Closed) fixture.Replace(); return View(); } }
        internal Disposition DeleteSynthetic() { lock (sync) { if (started && !Closed) fixture.Delete(); return View(); } }

        protected override void OnStart(string[] arguments)
        {
            Disposition result = StartDevelopment();
            if (!result.Started || result.Faulted || result.Stopped || result.Revoked || result.Disposed)
                throw new InvalidOperationException("P266_START_REFUSED");
        }
        protected override void OnStop() { StopDevelopment(); }
        protected override void OnShutdown() { StopDevelopment(); }
        protected override void OnCustomCommand(int command) { Observe(); }
        protected override void Dispose(bool disposing)
        {
            try { Terminate(3); }
            finally { base.Dispose(disposing); }
        }

        private static int Main(string[] arguments)
        {
            if (arguments == null || arguments.Length != 1 ||
                !String.Equals(arguments[0], "--development-only-no-effects", StringComparison.Ordinal)) return 64;
            using (var service = new DevelopmentServiceIpc())
            {
                try { ServiceBase.Run(service); }
                catch { service.Fault(); throw; }
            }
            return 0;
        }
    }
}
