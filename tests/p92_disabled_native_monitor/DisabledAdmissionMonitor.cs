// P92 FAKE-ONLY C# concurrency contract in tests/. NEVER a credential service.
// No WinCred, IPC, OS mutex, protected persistence, real keys or approval.
using System;
using System.Threading;

namespace Nayeon.P92.FakeOnly
{
    public enum FakeOperation { SavePending, ReplacePending, DeletePending }
    public enum FakePhase { Empty, Prepared, IntentFixture, PossibleAttempt,
        NativeFixtureSuccess, ClosedUnverified, RecoveryOnly }

    public sealed class FakeBinding
    {
        public readonly FakeOperation Operation;
        public readonly string Session;
        public readonly string Candidate;
        public FakeBinding(FakeOperation op, string session, string candidate)
        {
            if (!Enum.IsDefined(typeof(FakeOperation), op) ||
                !ValidId(session) || !ValidId(candidate))
                throw new InvalidOperationException("Invalid synthetic fixture");
            Operation = op; Session = session; Candidate = candidate;
        }
        private static bool ValidId(string s)
        {
            if (s == null || s.Length != 32) return false;
            foreach (char c in s)
                if (!((c >= 'a' && c <= 'f') || (c >= '0' && c <= '9')))
                    return false;
            return true;
        }
        public bool Matches(FakeBinding b)
        {
            return b != null && b.GetType() == typeof(FakeBinding) &&
                Operation == b.Operation && Session == b.Session &&
                Candidate == b.Candidate;
        }
        public override string ToString() { return "<synthetic fixture only>"; }
    }

    public sealed class FakeView
    {
        public readonly FakePhase Phase;
        public readonly int Attempts;
        public readonly bool Revoked;
        public readonly bool Faulted;
        public bool ProductVerified { get { return false; } }
        public bool ProductionEligible { get { return false; } }
        internal FakeView(FakePhase p, int a, bool r, bool f)
        { Phase = p; Attempts = a; Revoked = r; Faulted = f; }
    }

    // Purely in-process monitor: this DOES NOT implement the native C1
    // actor, authenticated consent, journal, mutex, or privileged operation.
    public sealed class DisabledFakeAdmissionMonitor
    {
        private readonly object gate = new object();
        private readonly int owner = Thread.CurrentThread.ManagedThreadId;
        private bool entered, approved, revoked, faulted;
        private FakePhase phase = FakePhase.Empty;
        private FakeBinding stored;
        private int attempts;

        private static void Deny()
        { throw new InvalidOperationException("Synthetic admission refused"); }
        private void DemandOwner()
        { if (Thread.CurrentThread.ManagedThreadId != owner || entered) Deny(); }

        public void Prepare(FakeBinding b)
        {
            lock (gate) {
                DemandOwner(); entered = true;
                try {
                    if (phase != FakePhase.Empty || b == null) Deny();
                    stored = new FakeBinding(b.Operation, b.Session, b.Candidate);
                    phase = FakePhase.Prepared;
                } finally { entered = false; }
            }
        }
        public void FakeApprove(FakeBinding b)
        {
            lock (gate) {
                DemandOwner(); entered = true;
                try {
                    if (phase != FakePhase.Prepared || approved || revoked ||
                        faulted || stored == null || !stored.Matches(b)) Deny();
                    approved = true;
                } finally { entered = false; }
            }
        }
        public void FakeIntentAck()
        {
            lock (gate) {
                DemandOwner(); entered = true;
                try {
                    if (phase != FakePhase.Prepared || !approved ||
                        revoked || faulted) Deny();
                    phase = FakePhase.IntentFixture;
                } finally { entered = false; }
            }
        }
        // The only "dispatch" is setting one integer and signalling
        // disposable test barriers under the lock; zero native calls.
        public void FakeDispatchBarrier(FakeBinding b,
            ManualResetEventSlim enteredFixture, ManualResetEventSlim releaseFixture)
        {
            lock (gate) {
                DemandOwner(); entered = true;
                try {
                    if (phase != FakePhase.IntentFixture || !approved ||
                        revoked || faulted || attempts != 0 ||
                        !stored.Matches(b) || enteredFixture == null ||
                        releaseFixture == null) Deny();
                    attempts = 1;
                    phase = FakePhase.PossibleAttempt;
                    enteredFixture.Set();
                    if (!releaseFixture.Wait(3000)) {
                        faulted = true; phase = FakePhase.RecoveryOnly;
                        Deny();
                    }
                } finally { entered = false; }
            }
        }
        // Revocation waits for the same gate. If dispatch wins first, it
        // cannot be retroactively claimed cancelled.
        public void Revoke()
        {
            lock (gate) {
                revoked = true; approved = false;
                if (phase != FakePhase.Empty &&
                    phase != FakePhase.ClosedUnverified)
                    phase = FakePhase.RecoveryOnly;
            }
        }
        public void Fault()
        {
            lock (gate) {
                faulted = true;
                if (phase != FakePhase.Empty) phase = FakePhase.RecoveryOnly;
            }
        }
        public void FakeNativeResult(bool success)
        {
            lock (gate) {
                DemandOwner(); entered = true;
                try {
                    if (phase != FakePhase.PossibleAttempt) Deny();
                    if (success && !faulted && !revoked)
                        phase = FakePhase.NativeFixtureSuccess;
                    else { faulted = true; phase = FakePhase.RecoveryOnly; }
                } finally { entered = false; }
            }
        }
        public void FakeTerminalCommit(bool success)
        {
            lock (gate) {
                DemandOwner(); entered = true;
                try {
                    if (phase != FakePhase.NativeFixtureSuccess) Deny();
                    if (success && !faulted && !revoked)
                        phase = FakePhase.ClosedUnverified;
                    else { faulted = true; phase = FakePhase.RecoveryOnly; }
                } finally { entered = false; }
            }
        }
        public void FakeRestart()
        {
            lock (gate) {
                if (phase != FakePhase.Empty) {
                    faulted = true; approved = false;
                    phase = FakePhase.RecoveryOnly;
                }
            }
        }
        public FakeView Snapshot()
        {
            lock (gate) { return new FakeView(phase, attempts, revoked, faulted); }
        }
    }
}
