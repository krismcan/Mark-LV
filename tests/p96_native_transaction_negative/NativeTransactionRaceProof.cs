// P96: genuine, byte-unchanged P49 transaction coordinator + genuine P95 ledger.
// All dependencies below are disposable IN-MEMORY FAKES, not native adapters.
// This is a deterministic security NEGATIVE TEST, never production consent.
using System;
using System.Threading;

namespace Nayeon.ByokC1
{
    internal sealed class P96ApprovalFixture : ITrustedPendingApproval
    {
        internal volatile bool Current = true;
        internal int Checks;
        internal int ConsumeCount;
        public bool Consume(LedgerOperation operation, byte[] candidate,
            bool destructiveAcknowledgement)
        {
            Interlocked.Increment(ref ConsumeCount);
            return Current;
        }
        public bool StillCurrent(LedgerOperation operation, byte[] candidate)
        {
            Interlocked.Increment(ref Checks);
            return Current;
        }
        internal void Revoke() { Current = false; }
    }

    internal sealed class P96StateFixture : IProtectedPendingState
    {
        internal string Journal = CustodyLedger.CreateInitial(new string('a', 32));
        internal string Anchor;
        internal bool Trusted = true;
        internal bool Present;
        internal bool ThrowDuringEffect;
        internal int PossibleEffects, EffectsAfterRevoke;
        internal readonly P96ApprovalFixture Approval;

        internal P96StateFixture(P96ApprovalFixture approval)
        {
            Approval = approval;
            Anchor = CustodyLedger.Anchor(Journal);
        }
        public bool TrustVerified { get { return Trusted; } }
        public string ReadJournal() { return Journal; }
        public string ReadAnchor() { return Anchor; }
        public bool PendingPresent() { return Present; }
        public void WriteJournal(string expected, string replacement)
        {
            if (!String.Equals(Journal, expected, StringComparison.Ordinal))
                throw new LedgerBlocked();
            Journal = replacement;
        }
        public void WriteAnchor(string expected, string replacement)
        {
            if (!String.Equals(Anchor, expected, StringComparison.Ordinal))
                throw new LedgerBlocked();
            Anchor = replacement;
        }
        public void SaveOrReplace(byte[] candidate)
        {
            if (candidate == null || candidate.Length == 0)
                throw new LedgerBlocked();
            // This is an integer marker only, NOT a Windows effect or key.
            Interlocked.Increment(ref PossibleEffects);
            if (!Approval.Current) Interlocked.Increment(ref EffectsAfterRevoke);
            if (ThrowDuringEffect) throw new LedgerBlocked();
            Present = true;
        }
        public void DeletePending()
        {
            Interlocked.Increment(ref PossibleEffects);
            if (!Approval.Current) Interlocked.Increment(ref EffectsAfterRevoke);
            if (ThrowDuringEffect) throw new LedgerBlocked();
            Present = false;
        }
    }

    internal sealed class P96GuardFixture : IExclusiveCustodyLock
    {
        internal bool Fault;
        internal bool InjectRevocationAtFinalOwnershipCheck;
        internal readonly P96ApprovalFixture Approval;
        internal int OwnerChecks;
        internal bool RevokedOnSeparateThread;
        internal bool TerminalMarked;
        internal bool LeaseDisposed;
        internal P96GuardFixture(P96ApprovalFixture approval) { Approval = approval; }
        public bool RecoveryFaulted { get { return Fault; } }
        public IContinuousCustodyLease Acquire()
        {
            if (Fault) throw new LedgerBlocked();
            return new P96LeaseFixture(this);
        }

        private sealed class P96LeaseFixture : IContinuousCustodyLease
        {
            private readonly P96GuardFixture guard;
            private bool disposed;
            internal P96LeaseFixture(P96GuardFixture guard) { this.guard = guard; }
            public bool IsOwned
            {
                get
                {
                    if (disposed) return false;
                    int count = ++guard.OwnerChecks;
                    // Exact coordinator ordering:
                    // 1 initial lease check, 2 pair readback, 3 pre-intent,
                    // 4 post-intent CHECK AFTER the final StillCurrent.
                    // A separate Windows thread revokes authorization during
                    // the fourth IsOwned getter. No real native operation.
                    if (guard.InjectRevocationAtFinalOwnershipCheck && count == 4)
                    {
                        var revoker = new Thread(guard.Approval.Revoke);
                        revoker.Start();
                        if (!revoker.Join(3000))
                            throw new InvalidOperationException("fixture revoker did not finish");
                        guard.RevokedOnSeparateThread = true;
                    }
                    return true;
                }
            }
            public void MarkTerminalVerified()
            {
                if (disposed || guard.TerminalMarked) throw new LedgerBlocked();
                guard.TerminalMarked = true;
            }
            public void Dispose()
            {
                if (disposed) return;
                disposed = true;
                guard.LeaseDisposed = true;
                if (!guard.TerminalMarked) guard.Fault = true;
            }
        }
    }

    internal sealed class P96Fixture
    {
        internal readonly P96ApprovalFixture Approval = new P96ApprovalFixture();
        internal readonly P96StateFixture State;
        internal readonly P96GuardFixture Guard;
        internal readonly PendingCustodyTransaction ActualCoordinator;
        internal P96Fixture()
        {
            State = new P96StateFixture(Approval);
            Guard = new P96GuardFixture(Approval);
            ActualCoordinator = new PendingCustodyTransaction(State, Approval, Guard);
        }
        internal static byte[] Dummy()
        {
            // Never an API key: deterministic 4-byte test-only marker.
            return new byte[] { 0x31, 0x32, 0x33, 0x34 };
        }
    }

    internal static class P96NegativeProof
    {
        private static int passed, failed;
        private static void Demand(bool condition, string reason)
        { if (!condition) throw new Exception("P96 proof failed: " + reason); }
        private static void Run(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS " + name); }
            catch (Exception error)
            { failed++; Console.WriteLine("FAIL " + name + " " + error.GetType().Name); }
        }

        internal static int Main()
        {
            Run("unmodified-coordinator-baseline-save", () =>
            {
                var f = new P96Fixture();
                var outcome = f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy());
                Demand(outcome == CustodyOutcome.StoredUnverified, "baseline outcome");
                Demand(f.State.PossibleEffects == 1, "one fake marker");
                Demand(f.State.EffectsAfterRevoke == 0, "consent current");
                Demand(f.Approval.Checks == 3, "three approval probes");
                Demand(f.Guard.TerminalMarked && f.Guard.LeaseDisposed, "terminal");
            });

            Run("actual-code-post-check-revocation-negative-proof", () =>
            {
                var f = new P96Fixture();
                f.Guard.InjectRevocationAtFinalOwnershipCheck = true;
                var outcome = f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy());
                // This is the EXPECTED FAILURE OF THE OLD DESIGN: its final
                // consent check returned true, then a separate Windows thread
                // revoked, then the coordinator invoked its fake effect.
                // The test PASS means the flaw was REPRODUCED, not fixed.
                Demand(f.Guard.RevokedOnSeparateThread, "real revoker thread ran");
                Demand(!f.Approval.Current, "consent no longer current");
                Demand(f.Approval.Checks == 3, "last approval check happened earlier");
                Demand(f.State.PossibleEffects == 1, "fake dispatch AFTER revocation");
                Demand(f.State.EffectsAfterRevoke == 1, "deterministic check-to-effect gap");
                Demand(outcome == CustodyOutcome.StoredUnverified,
                       "old coordinator falsely treats late revocation as permitted");
            });

            Run("actual-code-replace-after-revocation-negative-proof", () =>
            {
                var f = new P96Fixture();
                f.State.Journal = CustodyLedger.AppendTerminal(
                    CustodyLedger.AppendIntent(f.State.Journal,
                        LedgerOperation.Save, new string('b', 32)));
                f.State.Anchor = CustodyLedger.Anchor(f.State.Journal);
                f.State.Present = true;
                f.Guard.InjectRevocationAtFinalOwnershipCheck = true;
                var outcome = f.ActualCoordinator.Apply(
                    LedgerOperation.Replace, P96Fixture.Dummy());
                Demand(f.Guard.RevokedOnSeparateThread && !f.Approval.Current,
                       "revocation completed on separate thread");
                Demand(f.State.PossibleEffects == 1 && f.State.EffectsAfterRevoke == 1,
                       "fake replace effect after revocation");
                Demand(outcome == CustodyOutcome.StoredUnverified,
                       "old coordinator does not serialise replacement");
            });

            Run("actual-code-delete-after-revocation-negative-proof", () =>
            {
                var f = new P96Fixture();
                f.State.Journal = CustodyLedger.AppendTerminal(
                    CustodyLedger.AppendIntent(f.State.Journal,
                        LedgerOperation.Save, new string('b', 32)));
                f.State.Anchor = CustodyLedger.Anchor(f.State.Journal);
                f.State.Present = true;
                f.Guard.InjectRevocationAtFinalOwnershipCheck = true;
                var outcome = f.ActualCoordinator.Apply(
                    LedgerOperation.Delete, null, true);
                Demand(f.Guard.RevokedOnSeparateThread && !f.Approval.Current,
                       "revocation completed on separate thread");
                Demand(f.State.PossibleEffects == 1 && f.State.EffectsAfterRevoke == 1,
                       "fake deletion effect after revocation");
                Demand(outcome == CustodyOutcome.RemovedUnverified,
                       "old coordinator does not serialise deletion");
            });

            Run("revocation-before-consume-fails-closed", () =>
            {
                var f = new P96Fixture();
                f.Approval.Revoke();
                var outcome = f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy());
                Demand(outcome == CustodyOutcome.Denied, "early deny");
                Demand(f.State.PossibleEffects == 0, "no effect");
            });

            Run("invalid-candidate-does-not-run-effect", () =>
            {
                var f = new P96Fixture();
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, new byte[0]) ==
                       CustodyOutcome.Denied, "shape rejection");
                Demand(f.State.PossibleEffects == 0, "zero effects");
            });

            Run("unknown-principal-declines-effect", () =>
            {
                var f = new P96Fixture();
                f.State.Trusted = false;
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.Denied, "no service trust");
                Demand(f.State.PossibleEffects == 0, "zero effects");
            });

            Run("faulted-lease-declines-effect", () =>
            {
                var f = new P96Fixture();
                f.Guard.Fault = true;
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.RecoveryRequired, "recovery-only");
                Demand(f.State.PossibleEffects == 0, "zero effects");
            });

            Run("inflight-history-recovery-no-effect", () =>
            {
                var f = new P96Fixture();
                f.State.Journal = CustodyLedger.AppendIntent(f.State.Journal,
                    LedgerOperation.Save, new string('b', 32));
                f.State.Anchor = CustodyLedger.Anchor(f.State.Journal);
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.RecoveryRequired, "inflight must recover");
                Demand(f.State.PossibleEffects == 0, "no retry");
            });

            Run("missing-historical-history-never-bootstrap", () =>
            {
                var f = new P96Fixture();
                f.State.Journal = null; f.State.Anchor = null;
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.RecoveryRequired, "missing witness");
                Demand(f.State.PossibleEffects == 0, "no attempt");
            });

            Run("unmatched-anchor-no-effect", () =>
            {
                var f = new P96Fixture();
                f.State.Anchor = "A2|1|0|" + new string('0', 64);
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.RecoveryRequired, "wrong anchor");
                Demand(f.State.PossibleEffects == 0, "no native attempt");
            });

            Run("unknown-prior-pending-no-effect", () =>
            {
                var f = new P96Fixture();
                f.State.Present = true;
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.RecoveryRequired, "presence mismatch");
                Demand(f.State.PossibleEffects == 0, "no effect");
            });

            Run("failed-fake-effect-never-retried", () =>
            {
                var f = new P96Fixture();
                f.State.ThrowDuringEffect = true;
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.RecoveryRequired, "failed attempt recovery");
                Demand(f.State.PossibleEffects == 1, "one possible attempt");
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.Denied, "second apply claim refused");
                Demand(f.State.PossibleEffects == 1, "no second effect");
            });

            Run("success-one-shot-replay-refused", () =>
            {
                var f = new P96Fixture();
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.StoredUnverified, "initial fake save");
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.Denied, "second attempt denied");
                Demand(f.State.PossibleEffects == 1, "exactly one effect");
            });

            Run("empty-secret-free-result-even-when-claims-true", () =>
            {
                var f = new P96Fixture();
                Demand(f.ActualCoordinator.Apply(LedgerOperation.Save, P96Fixture.Dummy()) ==
                       CustodyOutcome.StoredUnverified, "unverified only");
                Demand(!f.Guard.Fault, "terminal no fault");
                Demand(f.State.PossibleEffects == 1, "one fake effect");
            });

            Console.WriteLine("P96_NATIVE_ACTUAL_COORDINATOR_TESTS_PASSED=" + passed);
            Console.WriteLine("P96_NATIVE_ACTUAL_COORDINATOR_TESTS_FAILED=" + failed);
            Console.WriteLine("P96_LEGACY_POST_CHECK_REVOCATION_RACE=REPRODUCED_IN_FAKE_ONLY");
            Console.WriteLine("P96_REAL_NATIVE_EFFECTS=NONE");
            Console.WriteLine("P96_SECURITY_FINDING=OPEN");
            Console.WriteLine("P96_C1_PRODUCTION_RELEASE=HOLD");
            return failed == 0 && passed == 15 ? 0 : 1;
        }
    }
}
