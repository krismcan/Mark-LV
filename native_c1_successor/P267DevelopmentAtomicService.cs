#if !C1_P267_DEVELOPMENT_ONLY
#error P267_DEVELOPMENT_ONLY_EXPLICIT_OPT_IN_REQUIRED
#endif
#if !C1_P265_DEVELOPMENT_ONLY
#error P267_REQUIRES_P265_DEVELOPMENT_ONLY
#endif
#if !DEBUG
#error P267_NO_RELEASE_BUILD
#endif
// DEVELOPMENT ONLY: owns the unchanged P265 adapter; no credential backend exists.
using System;
using System.Security.Principal;
using System.ServiceProcess;
using System.Threading;
using Nayeon.ByokC1.P265Development;

namespace Nayeon.ByokC1.P267Development
{
    internal sealed class Disposition
    {
        internal readonly bool Started, Stopped, Revoked, Faulted, Disposed, WorkerExited;
        internal readonly bool MayHaveEffect, RecoveryRequired;
        internal readonly int Submissions, Requests;
        internal readonly string Endpoint;
        internal readonly DenialReason LastReason;
        internal bool TooLate { get { return MayHaveEffect; } }
        internal bool CredentialAllowed { get { return false; } }
        internal bool StoreAllowed { get { return false; } }
        internal bool PrivilegedAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
        internal Disposition(bool started, bool stopped, bool revoked, bool faulted, bool disposed,
            bool exited, int submits, bool possible, bool recovery, int requests,
            string endpoint, DenialReason reason)
        {
            Started = started; Stopped = stopped; Revoked = revoked; Faulted = faulted;
            Disposed = disposed; WorkerExited = exited; Submissions = submits;
            MayHaveEffect = possible; RecoveryRequired = recovery; Requests = requests;
            Endpoint = endpoint; LastReason = reason;
        }
    }
    internal sealed class DevelopmentAtomicService : ServiceBase
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


        // One process-local fixture, no service actual WinCred effect and no durable recovery.
        internal sealed class Attempt { internal Attempt() { } }
        private Attempt prepared;
        private bool used, mayHaveEffect, recoveryRequired, reentryPending;
        private int submissions;
        private sealed class GateLease : IDisposable
        {
            private readonly DevelopmentAtomicService owner;
            internal GateLease(DevelopmentAtomicService value) { owner = value; }
            public void Dispose() { owner.Exit(); }
        }
        private void RejectReentry()
        {
            if (Monitor.IsEntered(sync))
            {
                reentryPending = true; // outer exit alone publishes the fault
                throw new InvalidOperationException("P267_NONREENTRANT");
            }
        }
        private GateLease Enter()
        {
            RejectReentry();
            Monitor.Enter(sync);
            return new GateLease(this);
        }
        private void Exit()
        {
            try
            {
                if (reentryPending)
                {
                    reentryPending = false; faulted = true; recoveryRequired = true;
                    CloseLocked();
                }
            }
            finally { Monitor.Exit(sync); }
        }
        internal Attempt PrepareSynthetic()
        {
            using (Enter())
            {
                if (!started || Closed || recoveryRequired || prepared != null || used) return null;
                prepared = new Attempt(); return prepared;
            }
        }
        internal Disposition DispatchSynthetic(Attempt attempt) { return Dispatch(attempt, false); }
        internal Disposition DispatchSyntheticFailure(Attempt attempt) { return Dispatch(attempt, true); }
        private Disposition Dispatch(Attempt attempt, bool fail)
        {
            using (Enter())
            {
                if (!started || Closed || recoveryRequired || used || attempt == null ||
                    !Object.ReferenceEquals(attempt, prepared)) return View();
                used = true;
                mayHaveEffect = true;
                recoveryRequired = true; // commitment BEFORE the only fixed integer submission
                try
                {
                    submissions++;
                    if (fail) throw new InvalidOperationException("P267_FIXED_SYNTHETIC_FAILURE");
                }
                catch (InvalidOperationException) { faulted = true; CloseLocked(); }
                return View();
            }
        }
        internal DevelopmentAtomicService(bool freshSyntheticFixture)
        {
            recoveryRequired = !freshSyntheticFixture;
            ServiceName = "NayeonP267DevelopmentOnly";
            CanStop = true; CanShutdown = true; CanPauseAndContinue = false; AutoLog = false;
        }

        private bool Closed { get { return stopped || revoked || faulted || disposed; } }
        private Disposition View()
        {
            return new Disposition(started, stopped, revoked, faulted, disposed, workerExited,
                submissions, mayHaveEffect, recoveryRequired, requests,
                Closed ? null : endpoint, lastReason);
        }
        internal Disposition Observe() { using (Enter()) { return View(); } }

        internal Disposition StartDevelopment()
        {
            bool failed = false;
            using (Enter())
            {
                if (started || Closed) { faulted = true; failed = true; }
                else
                {
                    try
                    {
                        // Capture anew at startup; neither SCM name nor a configured SID is approval.
                        using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true))
                            if (thread != null) throw new InvalidOperationException("P267_THREAD_IDENTITY");
                        using (WindowsIdentity current = WindowsIdentity.GetCurrent())
                        {
                            if (current.User == null || current.IsAnonymous || current.IsSystem ||
                                current.User.IsWellKnown(WellKnownSidType.LocalServiceSid) ||
                                current.User.IsWellKnown(WellKnownSidType.NetworkServiceSid) ||
                                current.User.Value.StartsWith("S-1-5-80-", StringComparison.Ordinal))
                                throw new InvalidOperationException("P267_DEVELOPER_PRINCIPAL_REQUIRED");
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
            if (faulted) recoveryRequired = true;
            prepared = null;
            if (adapter != null)
            {
                try { adapter.Dispose(); }
                catch (Exception error)
                {
                    faulted = true; recoveryRequired = true;
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
                    using (Enter()) { if (Closed) return; serving = adapter; }
                    DenialEvidence evidence = serving.ServeOnce(ServeTimeoutMs);
                    using (Enter())
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
                using (Enter()) { faulted = true; CloseLocked(); }
            }
            catch
            {
                // No retry or success receipt: unexpected worker failure is sticky evidence.
                using (Enter()) { faulted = true; lastReason = DenialReason.Fault; CloseLocked(); }
            }
            finally
            {
                using (Enter())
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
            using (Enter())
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
                using (Enter()) { faulted = true; recoveryRequired = true; }
                throw new System.TimeoutException("P267_WORKER_JOIN_FAILED");
            }
            using (Enter())
            {
                if (cleanupFailure != null)
                    throw new InvalidOperationException("P267_CLEANUP_FAILED", cleanupFailure);
                return View();
            }
        }

        internal Disposition StopDevelopment() { return Terminate(0); }
        internal Disposition Revoke() { return Terminate(1); }
        internal Disposition Fault() { return Terminate(2); }
        protected override void OnStart(string[] arguments)
        {
            Disposition result = StartDevelopment();
            if (!result.Started || result.Faulted || result.Stopped || result.Revoked || result.Disposed)
                throw new InvalidOperationException("P267_START_REFUSED");
        }
        protected override void OnStop() { StopDevelopment(); }
        protected override void OnShutdown() { StopDevelopment(); }
        protected override void OnCustomCommand(int command) { Observe(); }
        protected override void Dispose(bool disposing)
        {
            RejectReentry(); // refuse before inherited resource disposal on nested entry
            try { Terminate(3); }
            finally { base.Dispose(disposing); }
        }

        // No SCM dispatcher entry exists, including with development flags.
        private static int Main(string[] arguments) { return 64; }
    }
}
