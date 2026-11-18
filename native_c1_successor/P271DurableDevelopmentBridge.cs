#if !DEBUG
#error P271_NO_RELEASE_BUILD
#endif
#if !C1_P271_DEVELOPMENT_ONLY
#error P271_DEVELOPMENT_OPT_IN_REQUIRED
#endif
using System;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P269Development;
using Nayeon.ByokC1.P270Development;

namespace Nayeon.ByokC1.P271Development
{
    // Owns BOTH dependencies privately. Only fixed synthetic P269 submissions exist.
    // Inject runs synchronously inside P268's gate; no second admission/effect gate.
    internal sealed class DurableDevelopmentBridge : IDisposable
    {
        private readonly DurableWitness witness;
        private readonly ComposedDevelopmentService service;
        private readonly LedgerOperation operation;
        private string knownJournal, knownAnchor;
        private bool awaitingAnchor, expectedPresent;
        private int failed, disposed;
        // Trusted harness adversaries only; always run BEFORE the relevant checks.
        internal Action<string> TestProbe;
        internal static void RequireHosted()
        {
            Require(Environment.OSVersion.Platform == PlatformID.Win32NT &&
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Environment.GetEnvironmentVariable("P271_HOSTED_DISPOSABLE") == "1");
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent()) Require(!identity.IsSystem);
        }
        private static void Require(bool value) { if (!value) throw new LedgerBlocked(); }
        internal DurableDevelopmentBridge(string root, LedgerOperation op, bool fresh)
        {
            RequireHosted();
            Require(op == LedgerOperation.Save || op == LedgerOperation.Replace || op == LedgerOperation.Delete);
            operation = op;
            try
            {
                witness = new DurableWitness(root, fresh);
                Require(!witness.RecoveryRequired && witness.InspectConsistent());
                // Provision a synthetic prior Save through real sequential durable writes.
                // No fake history or P269 non-Save constructor bootstrap is trusted.
                if (op != LedgerOperation.Save)
                {
                    string j = witness.ReadJournal();
                    PersistPrior(CustodyLedger.AppendIntent(j, LedgerOperation.Save, CustodyLedger.NewNonce()));
                    PersistPrior(CustodyLedger.AppendTerminal(witness.ReadJournal()));
                }
                knownJournal = witness.ReadJournal(); knownAnchor = witness.ReadAnchor();
                expectedPresent = op != LedgerOperation.Save;
                Require(CustodyLedger.Verify(knownJournal, knownAnchor) ==
                    (expectedPresent ? LedgerPhase.CommittedUnverified : LedgerPhase.Initial));
                service = ComposedDevelopmentService.TestOnlyCreate(LedgerOperation.Save, true);
                service.TestState.Journal = knownJournal; service.TestState.Anchor = knownAnchor;
                service.TestState.Present = expectedPresent;
                service.TestAdapter.Inject = Probe;
                CheckComplete();
            }
            catch
            {
                Interlocked.Exchange(ref failed, 1);
                try { if (service != null) service.Dispose(); }
                finally { if (witness != null) witness.Dispose(); }
                throw;
            }
        }
        private void PersistPrior(string next)
        {
            witness.WriteJournal(witness.ReadJournal(), next);
            witness.WriteAnchor(witness.ReadAnchor(), CustodyLedger.Anchor(next));
            Require(!witness.RecoveryRequired && witness.InspectConsistent());
        }
        private void CheckSnapshots()
        {
            Require(Volatile.Read(ref failed) == 0 && Volatile.Read(ref disposed) == 0);
            Require(service.TestAdapter.Enrolled && service.TestState.Trusted);
            Require(service.TestState.Journal == knownJournal && service.TestState.Anchor == knownAnchor);
            Require(witness.ReadJournal() == knownJournal && witness.ReadAnchor() == knownAnchor);
            Require(service.TestState.Present == expectedPresent);
            // Only our uninterrupted journal->anchor continuation may be partial.
            Require(awaitingAnchor || !witness.RecoveryRequired);
        }
        private void CheckComplete()
        {
            CheckSnapshots();
            Require(!awaitingAnchor && !witness.RecoveryRequired && witness.InspectConsistent());
        }
        private void Probe(string point)
        {
            try
            {
                Action<string> inject = TestProbe; if (inject != null) inject(point);
                Require(Volatile.Read(ref failed) == 0 && Volatile.Read(ref disposed) == 0);
                Require(service.TestAdapter.Enrolled && service.TestState.Trusted);
                if (point == "after-journal")
                {
                    Require(!awaitingAnchor && service.TestState.Anchor == knownAnchor &&
                        service.TestState.Present == expectedPresent);
                    string next = service.TestState.Journal;
                    // Latch uncertainty before the real synchronous write. Exceptions
                    // never return to P268, so no fixture effect follows mirror failure.
                    awaitingAnchor = true;
                    witness.WriteJournal(knownJournal, next);
                    Require(witness.ReadJournal() == next && witness.ReadAnchor() == knownAnchor);
                    knownJournal = next;
                }
                else if (point == "after-anchor")
                {
                    Require(awaitingAnchor && service.TestState.Journal == knownJournal &&
                        service.TestState.Present == expectedPresent);
                    string next = service.TestState.Anchor;
                    Require(next == CustodyLedger.Anchor(knownJournal));
                    witness.WriteAnchor(knownAnchor, next);
                    Require(witness.ReadJournal() == knownJournal && witness.ReadAnchor() == next);
                    knownAnchor = next; awaitingAnchor = false;
                    CheckComplete();
                }
                else if (point == "effect-return")
                {
                    Require(service.TestState.Present == (operation != LedgerOperation.Delete));
                    expectedPresent = operation != LedgerOperation.Delete;
                    CheckComplete();
                }
                else
                {
                    CheckSnapshots();
                    if (point == "effect-enter")
                    {
                        CheckComplete();
                        Require(CustodyLedger.Verify(knownJournal, knownAnchor) == LedgerPhase.InFlight &&
                            CustodyLedger.LastOperation(knownJournal) == operation);
                    }
                    else if (point == "write-journal") CheckComplete();
                    else if (point == "write-anchor") Require(awaitingAnchor);
                }
            }
            catch { Interlocked.Exchange(ref failed, 1); throw new LedgerBlocked(); }
        }
        internal bool Start() { return service.StartDevelopment(); }
        internal ServiceOwnedPendingTransaction.Approval Prepare() { return service.TestPrepare(operation); }
        internal CustodyOutcome Submit(ServiceOwnedPendingTransaction.Approval ticket)
        { return service.TestSubmit(ticket, operation); }
        internal ControlResult Revoke() { return service.RevokeDevelopment(); }
        internal ControlResult Stop() { return service.StopDevelopment(); }
        internal ControlResult Fault() { return service.FaultDevelopment(); }
        internal CompositionObservation Observe() { return service.Observe(); }
        internal bool TestAdmissionClosed { get { return service.AdmissionClosed; } }
        internal int TestEffects { get { return service.TestState.PossibleEffects; } }
        internal bool TestTerminal { get { return service.TestGuard.TerminalMarked && service.TestGuard.LeaseDisposed; } }
        internal bool TestConsistent() { return witness.InspectConsistent(); }
        internal LedgerPhase TestPhase() { return CustodyLedger.Verify(witness.ReadJournal(), witness.ReadAnchor()); }
        internal void TestCloseWitness() { witness.Dispose(); }
        internal void TestSkew(bool journal)
        { if (journal) service.TestState.Journal = "skew"; else service.TestState.Anchor = "skew"; }
        internal void TestUntrust() { service.TestState.Trusted = false; }
        internal void TestEffectFailure() { service.TestState.ThrowDuringEffect = true; }
        internal void TestPoisonWitness()
        { witness.WriteJournal("stale", witness.ReadJournal()); }
        public void Dispose()
        {
            // Wait for P268 gate/transport cleanup BEFORE releasing durable handles.
            try { service.Dispose(); }
            catch { Interlocked.Exchange(ref failed, 1); throw; }
            // A failed stop can mean the transaction still owns P268's gate.
            // Retain custody on that path; a later successful Dispose may release it.
            Interlocked.Exchange(ref disposed, 1); witness.Dispose();
        }
    }
}
