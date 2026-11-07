// P97: TEST-ONLY DISABLED C# ADMISSION COORDINATOR (never native custody).
// Corrected lock-order target for P96's reproducible consent-to-effect gap.
// No WinCred, protected service, IPC, credential value, journal I/O, OS mutex,
// arbitrary effect delegates, provider, installer or production entrypoint.
using System;
using System.Threading;

namespace Nayeon.ByokC1.P97.DisabledOnly
{
    internal enum FakeAdmissionStage
    {
        Prepared, FakeIntentReadback, PossibleEffect, ClosedUnverified,
        RecoveryOnly
    }

    internal sealed class FakeExactBinding
    {
        internal readonly LedgerOperation Operation;
        internal readonly string Session;
        internal readonly string Candidate;

        internal FakeExactBinding(LedgerOperation operation, string session, string candidate)
        {
            if ((operation != LedgerOperation.Save &&
                 operation != LedgerOperation.Replace &&
                 operation != LedgerOperation.Delete) ||
                !IsFakeId(session) || !IsFakeId(candidate))
                throw new InvalidOperationException("Invalid fake fixture identity");
            Operation = operation; Session = session; Candidate = candidate;
        }

        private static bool IsFakeId(string text)
        {
            if (text == null || text.Length != 32) return false;
            foreach (char ch in text)
                if (!((ch >= '0' && ch <= '9') ||
                    (ch >= 'a' && ch <= 'f'))) return false;
            return true;
        }

        internal bool Same(FakeExactBinding candidate)
        {
            return candidate != null &&
                candidate.GetType() == typeof(FakeExactBinding) &&
                candidate.Operation == Operation &&
                String.Equals(candidate.Session, Session, StringComparison.Ordinal) &&
                String.Equals(candidate.Candidate, Candidate, StringComparison.Ordinal);
        }

        public override string ToString() { return "<P97 synthetic identity only>"; }
    }

    internal sealed class FakeAdmissionSnapshot
    {
        internal readonly FakeAdmissionStage Stage;
        internal readonly int PossibleAttempts;
        internal readonly bool Revoked;
        internal readonly bool Faulted;
        internal readonly bool RevocationCommittedAfterAttempt;
        internal bool CredentialVerified { get { return false; } }
        internal bool NativeEffectPermitted { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
        internal bool RetryAllowed { get { return false; } }

        internal FakeAdmissionSnapshot(FakeAdmissionStage stage, int possibleAttempts,
            bool revoked, bool faulted, bool afterAttempt)
        {
            Stage = stage; PossibleAttempts = possibleAttempts; Revoked = revoked;
            Faulted = faulted; RevocationCommittedAfterAttempt = afterAttempt;
        }

        public override string ToString()
        { return "<P97 disabled native-admission fixture, no authority>"; }
    }

    // NOT to be included in any native service or production build.
    // All user consent and protected storage statements here are UNTRUSTED
    // fixture data and cannot be promoted to native user authority.
    internal sealed class DisabledNativeAdmissionCoordinator
    {
        private readonly object admissionGate = new object();
        private readonly int ownerThread = Thread.CurrentThread.ManagedThreadId;
        private readonly FakeExactBinding ownedBinding;
        private bool entered, fakeApproved, revoked, faulted;
        private bool afterAttemptRevocation;
        private FakeAdmissionStage stage = FakeAdmissionStage.Prepared;
        private int possibleAttempts;
        private string fakeJournal, fakeAnchor;
        private bool fakePendingPresent;

        internal DisabledNativeAdmissionCoordinator(FakeExactBinding binding)
        {
            if (binding == null || binding.GetType() != typeof(FakeExactBinding))
                throw new InvalidOperationException("Missing synthetic identity");
            // Bind a fresh, private copy. Never retain mutable caller authority.
            ownedBinding = new FakeExactBinding(
                binding.Operation, binding.Session, binding.Candidate);
            fakeJournal = CustodyLedger.CreateInitial(new String('a', 32));
            if (ownedBinding.Operation != LedgerOperation.Save)
            {
                // Existing stored state is only a deterministic in-memory fixture.
                fakeJournal = CustodyLedger.AppendTerminal(
                    CustodyLedger.AppendIntent(fakeJournal, LedgerOperation.Save,
                        new String('b', 32)));
                fakePendingPresent = true;
            }
            fakeAnchor = CustodyLedger.Anchor(fakeJournal);
        }

        private static void Deny()
        {
            throw new InvalidOperationException("P97 synthetic-only admission denied");
        }

        private void RequireOwner()
        {
            if (Thread.CurrentThread.ManagedThreadId != ownerThread ||
                entered) Deny();
        }

        internal void FakeApprove(FakeExactBinding proposal)
        {
            lock (admissionGate)
            {
                RequireOwner(); entered = true;
                try
                {
                    if (!ownedBinding.Same(proposal) || stage != FakeAdmissionStage.Prepared ||
                        fakeApproved || revoked || faulted) Deny();
                    fakeApproved = true;
                }
                finally { entered = false; }
            }
        }

        // This is the actual C# ledger codec with IN-MEMORY strings, not
        // durable journal, service identity, or protected anchor readback.
        internal void FakePersistAndReadbackIntent(FakeExactBinding proposal)
        {
            lock (admissionGate)
            {
                RequireOwner(); entered = true;
                try
                {
                    if (!ownedBinding.Same(proposal) ||
                        stage != FakeAdmissionStage.Prepared ||
                        !fakeApproved || revoked || faulted ||
                        possibleAttempts != 0) Deny();
                    LedgerPhase phase = CustodyLedger.Verify(fakeJournal, fakeAnchor);
                    bool initial = phase == LedgerPhase.Initial;
                    if (phase == LedgerPhase.InFlight ||
                        initial != (ownedBinding.Operation == LedgerOperation.Save) ||
                        fakePendingPresent == initial)
                    {
                        faulted = true; stage = FakeAdmissionStage.RecoveryOnly;
                        Deny();
                    }
                    string next = CustodyLedger.AppendIntent(
                        fakeJournal, ownedBinding.Operation, CustodyLedger.NewNonce());
                    string nextAnchor = CustodyLedger.Anchor(next);
                    if (CustodyLedger.Verify(next, nextAnchor) != LedgerPhase.InFlight)
                    {
                        faulted = true; stage = FakeAdmissionStage.RecoveryOnly;
                        Deny();
                    }
                    fakeJournal = next;
                    fakeAnchor = nextAnchor;
                    stage = FakeAdmissionStage.FakeIntentReadback;
                }
                catch (Exception)
                {
                    faulted = true;
                    stage = FakeAdmissionStage.RecoveryOnly;
                    throw;
                }
                finally { entered = false; }
            }
        }

        // Precise TEST linearisation point: possibleAttempts changes 0 -> 1
        // under the SAME monitor as Revoke and Fault. No arbitrary callback
        // executes here. The two Events are disposable test barriers only.
        // There is absolutely no WinCred/real native effect.
        internal string FakeDispatch(FakeExactBinding proposal,
            ManualResetEventSlim dispatchEntered, ManualResetEventSlim release)
        {
            lock (admissionGate)
            {
                RequireOwner(); entered = true;
                try
                {
                    if (!ownedBinding.Same(proposal) ||
                        dispatchEntered == null || release == null ||
                        stage != FakeAdmissionStage.FakeIntentReadback ||
                        !fakeApproved || revoked || faulted ||
                        possibleAttempts != 0 ||
                        CustodyLedger.Verify(fakeJournal, fakeAnchor) !=
                            LedgerPhase.InFlight)
                        Deny();
                    possibleAttempts = 1; // The one fake effect marker.
                    stage = FakeAdmissionStage.PossibleEffect;
                    dispatchEntered.Set();
                    if (!release.Wait(3000))
                    {
                        faulted = true; stage = FakeAdmissionStage.RecoveryOnly;
                        Deny();
                    }
                    return "P97_FAKE_ATTEMPT_ONLY__NO_NATIVE_OPERATION";
                }
                catch (Exception)
                {
                    faulted = true;
                    stage = FakeAdmissionStage.RecoveryOnly;
                    throw;
                }
                finally { entered = false; }
            }
        }

        // Only revocation COMMIT (under the same monitor) changes authority.
        // An attempted revocation which waits behind a dispatch is NOT a
        // committed cancellation of an already dispatched operation.
        internal void Revoke()
        {
            lock (admissionGate)
            {
                if (possibleAttempts != 0) afterAttemptRevocation = true;
                revoked = true;
                fakeApproved = false;
                if (stage != FakeAdmissionStage.ClosedUnverified)
                    stage = FakeAdmissionStage.RecoveryOnly;
            }
        }

        internal void Fault()
        {
            lock (admissionGate)
            {
                faulted = true;
                if (stage != FakeAdmissionStage.ClosedUnverified)
                    stage = FakeAdmissionStage.RecoveryOnly;
            }
        }

        internal void FakeCompleteEffectAndTerminal(bool reportedSuccess,
            bool terminalReadbackSucceeded)
        {
            lock (admissionGate)
            {
                RequireOwner(); entered = true;
                try
                {
                    if (stage != FakeAdmissionStage.PossibleEffect ||
                        possibleAttempts != 1) Deny();
                    if (!reportedSuccess || !terminalReadbackSucceeded ||
                        revoked || faulted)
                    {
                        faulted = true;
                        stage = FakeAdmissionStage.RecoveryOnly;
                        return;
                    }
                    string terminal = CustodyLedger.AppendTerminal(fakeJournal);
                    string terminalAnchor = CustodyLedger.Anchor(terminal);
                    LedgerPhase expected = ownedBinding.Operation == LedgerOperation.Delete
                        ? LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified;
                    if (CustodyLedger.Verify(terminal, terminalAnchor) != expected)
                    {
                        faulted = true; stage = FakeAdmissionStage.RecoveryOnly;
                        Deny();
                    }
                    fakeJournal = terminal;
                    fakeAnchor = terminalAnchor;
                    fakePendingPresent = ownedBinding.Operation != LedgerOperation.Delete;
                    stage = FakeAdmissionStage.ClosedUnverified;
                }
                catch (Exception)
                {
                    faulted = true;
                    stage = FakeAdmissionStage.RecoveryOnly;
                    throw;
                }
                finally { entered = false; }
            }
        }

        internal void FakeRestart()
        {
            lock (admissionGate)
            {
                faulted = true;
                fakeApproved = false;
                stage = FakeAdmissionStage.RecoveryOnly;
            }
        }

        internal FakeAdmissionSnapshot ReadOnlySnapshot()
        {
            lock (admissionGate)
                return new FakeAdmissionSnapshot(stage, possibleAttempts,
                    revoked, faulted, afterAttemptRevocation);
        }

        // For tamper tests only; no protected storage exists.
        internal void CorruptFakeAnchorForTest()
        {
            lock (admissionGate)
            {
                RequireOwner(); entered = true;
                try { fakeAnchor = "untrusted fake anchor"; }
                finally { entered = false; }
            }
        }
    }
}
