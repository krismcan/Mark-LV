#if !DEBUG
#error P269_NO_RELEASE_BUILD
#endif
#if !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY
#error P269_ALL_DEVELOPMENT_OPT_INS_REQUIRED
#endif
using System;
using System.ServiceProcess;
using System.Threading;
using Nayeon.ByokC1.P267Development;
using Nayeon.ByokC1.P268Development;

namespace Nayeon.ByokC1.P269Development
{
    internal sealed class CompositionObservation
    {
        internal readonly Disposition Transport;
        internal readonly bool Closed, PendingMayHaveEffect, PendingRecoveryRequired;
        internal bool CredentialAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
        internal CompositionObservation(Disposition transport, bool closed, bool effect, bool recovery)
        { Transport = transport; Closed = closed; PendingMayHaveEffect = effect; PendingRecoveryRequired = recovery; }
    }

    // Test-only SCM-shaped owner. Transport and pending coordinator retain SEPARATE locks.
    internal sealed class ComposedDevelopmentService : ServiceBase
    {
        private readonly object lifecycle = new object();
        private readonly DevelopmentAtomicService transport;
        private readonly ServiceOwnedPendingTransaction pending;
        private readonly bool fresh;
        private int started, closed;
        internal readonly P96ApprovalFixture TestApproval;
        internal readonly P96StateFixture TestState;
        internal readonly P96GuardFixture TestGuard;
        internal readonly DevelopmentPendingState TestAdapter;
        private ComposedDevelopmentService(LedgerOperation operation, bool freshSession)
        {
            fresh = freshSession;
            TestApproval = new P96ApprovalFixture();
            TestState = new P96StateFixture(TestApproval);
            TestGuard = new P96GuardFixture(TestApproval);
            if (operation != LedgerOperation.Save)
            {
                TestState.Journal = CustodyLedger.AppendTerminal(CustodyLedger.AppendIntent(
                    TestState.Journal, LedgerOperation.Save, new string('b', 32)));
                TestState.Anchor = CustodyLedger.Anchor(TestState.Journal); TestState.Present = true;
            }
            TestAdapter = new DevelopmentPendingState(TestState);
            pending = ServiceOwnedPendingTransaction.DevelopmentOnlyHost(TestAdapter, TestGuard, freshSession);
            transport = new DevelopmentAtomicService(freshSession);
            ServiceName = "NayeonP269DevelopmentOnly";
            AutoLog = false; CanStop = true; CanShutdown = true;
        }
        internal static ComposedDevelopmentService TestOnlyCreate(LedgerOperation operation, bool fresh)
        { return new ComposedDevelopmentService(operation, fresh); }
        internal bool AdmissionClosed { get { return Volatile.Read(ref closed) != 0; } }
        internal bool StartDevelopment()
        {
            bool ok = false;
            lock (lifecycle)
            {
                if (!fresh || AdmissionClosed || Interlocked.CompareExchange(ref started, 1, 0) != 0)
                    Interlocked.Exchange(ref closed, 1);
                else
                {
                    Disposition view = transport.StartDevelopment();
                    ok = view.Started && !view.Faulted && !view.Stopped && !view.Revoked && !view.Disposed && !AdmissionClosed;
                    if (!ok) Interlocked.Exchange(ref closed, 1);
                }
            }
            if (!ok) FaultDevelopment(); // outside lifecycle, including rejected restart
            return ok;
        }
        private bool Admitted()
        {
            if (Volatile.Read(ref started) == 0 || AdmissionClosed) return false;
            Disposition view = transport.Observe();
            if (view.Faulted || view.Stopped || view.Revoked || view.Disposed || view.WorkerExited)
            { FaultDevelopment(); return false; }
            return !AdmissionClosed;
        }
        internal ServiceOwnedPendingTransaction.Approval TestPrepare(LedgerOperation operation)
        { return Admitted() ? pending.IssueDevelopmentApproval(operation) : null; }
        internal CustodyOutcome TestSubmit(ServiceOwnedPendingTransaction.Approval ticket, LedgerOperation operation)
        {
            if (!Admitted()) return CustodyOutcome.Denied;
            byte[] marker = operation == LedgerOperation.Delete ? null : new byte[] { 0x31, 0x32, 0x33, 0x34 };
            try { return pending.Apply(ticket, operation, marker, operation == LedgerOperation.Delete); }
            finally { if (marker != null) Array.Clear(marker, 0, marker.Length); }
        }
        private ControlResult Close(int reason)
        {
            Interlocked.Exchange(ref closed, 1); // admission latch BEFORE pending control
            // Never hold lifecycle while calling P268, and never call back from P268.
            try { return reason == 0 ? pending.Revoke() : reason == 1 ? pending.Stop() : pending.Fault(); }
            finally
            {
                lock (lifecycle)
                {
                    if (reason == 0) transport.Revoke();
                    else if (reason == 1) transport.StopDevelopment();
                    else transport.Fault();
                }
            }
        }
        internal ControlResult RevokeDevelopment() { return Close(0); }
        internal ControlResult StopDevelopment() { return Close(1); }
        internal ControlResult FaultDevelopment() { return Close(2); }
        internal CompositionObservation Observe()
        {
            bool effect = true, recovery = true;
            try { effect = pending.MayHaveEffect; recovery = pending.RecoveryRequired; }
            catch (InvalidOperationException) { Interlocked.Exchange(ref closed, 1); }
            return new CompositionObservation(transport.Observe(), AdmissionClosed, effect, recovery);
        }
        protected override void OnStart(string[] arguments)
        { if (!StartDevelopment()) throw new InvalidOperationException("P269_START_REFUSED"); }
        protected override void OnStop() { StopDevelopment(); }
        protected override void OnShutdown() { StopDevelopment(); }
        protected override void Dispose(bool disposing)
        { try { StopDevelopment(); } finally { try { transport.Dispose(); } finally { base.Dispose(disposing); } } }
        private static int Main(string[] arguments) { return 64; }
    }
}
