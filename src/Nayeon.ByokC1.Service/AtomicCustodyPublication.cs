using System.Threading;

namespace Nayeon.ByokC1.Service
{
    internal enum CoreOutcome
    { None, Denied, Cancelled, Revoked, Stopped, Faulted, StoredUnverified, RemovedUnverified, RecoveryRequired }

    // Extracted P320 publication algorithm. Nonsecret ordering only: no authorization,
    // storage, execution callback, test rendezvous, reset or recovery-clear operation.
    // A commitment is conservative metadata, never a permit to invoke an effect.
    internal sealed class AtomicCustodyPublication
    {
        private const int Unknown = 1, Committed = 2, OutcomeShift = 2;
        private int publication;

        internal int Read() { return Volatile.Read(ref publication); }
        internal static bool IsUncertain(int state) { return (state & Unknown) != 0; }
        internal static bool MayHaveEffect(int state) { return (state & Committed) != 0; }
        internal static CoreOutcome Outcome(int state)
        { return IsUncertain(state) ? CoreOutcome.RecoveryRequired : (CoreOutcome)(state >> OutcomeShift); }

        internal void PublishUnknown()
        {
            int seen;
            do { seen = Read(); }
            while (Interlocked.CompareExchange(ref publication, seen | Unknown, seen) != seen);
        }

        internal bool TryCommitPossibleEffect()
        { return Interlocked.CompareExchange(ref publication, Committed, 0) == 0; }

        internal void Finish(CoreOutcome value)
        {
            int seen, next;
            do
            {
                seen = Read();
                CoreOutcome terminal = Outcome(seen);
                if (value == CoreOutcome.RecoveryRequired) terminal = value;
                else if (terminal == CoreOutcome.None) terminal = value;
                next = (seen & (Unknown | Committed)) | ((int)terminal << OutcomeShift);
            } while (Interlocked.CompareExchange(ref publication, next, seen) != seen);
        }
    }
}
