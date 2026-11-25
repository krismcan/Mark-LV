using System;
using System.Threading;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Nayeon.ByokC1;

namespace Nayeon.ByokC1.Service
{
    internal enum CustodyStage
    { ReviewPending, Reviewed, IntentWriting, IntentDurable, PossibleEffect, Terminal }
    internal enum CoreOutcome
    { None, Denied, Cancelled, Revoked, Stopped, Faulted, StoredUnverified, RemovedUnverified, RecoveryRequired }
    internal enum CoreControl { Cancel, Revoke, Stop, Fault }
    internal enum CoreControlResult { Applied, AlreadyTerminal, TooLatePossibleEffect, HoldUnknown }
    internal enum SyntheticSeed { Absent, Present }
    internal enum SyntheticCrash
    {
        None, BeforeIntent, AfterIdentity, AfterIntentJournal, AfterIntentAnchor,
        BeforeEffect, AfterAttempt, AfterMutation, AfterTerminalJournal,
        AfterTerminalAnchor, AfterTerminalVerify
    }
    internal enum RestartAssessment { Uncertain, Malformed, InFlight, TerminalUnverified, InitialUnqualified }

    internal sealed class CoreSnapshot
    {
        internal readonly SyntheticTransactionRequest Request;
        internal readonly CustodyStage Stage;
        internal readonly CoreOutcome Outcome;
        internal readonly bool MayHaveEffect, RecoveryRequired;
        internal readonly int Attempts;
        internal readonly bool AttemptsKnown;
        internal bool ProductionEligible { get { return false; } }
        internal CoreSnapshot(SyntheticTransactionRequest request, CustodyStage stage, CoreOutcome outcome,
            bool possible, bool recovery, int attempts, bool attemptsKnown = true)
        { Request = request; Stage = stage; Outcome = outcome; MayHaveEffect = possible;
            RecoveryRequired = recovery; Attempts = attempts; AttemptsKnown = attemptsKnown; }
    }

    // Untrusted immutable crash image. Neither a hash chain nor these fields authenticate storage.
    // It contains only a request identity, ledger metadata and a fixed synthetic integer.
    internal sealed class SyntheticCustodyImage
    {
        internal readonly string Journal, Anchor;
        internal readonly SyntheticTransactionRequest Request;
        internal readonly int Marker;
        internal SyntheticCustodyImage(string journal, string anchor, SyntheticTransactionRequest request, int marker)
        { Journal = journal; Anchor = anchor; Request = request; Marker = marker; }
    }

    // The storage contract for this increment is deliberately a sealed memory fixture, not
    // an injectable port. No filesystem, secret bytes, effect delegate or production adapter.
    internal sealed class InMemoryCustodyFixture
    {
        private int claimed;
        private readonly SyntheticCustodyImage image;
        internal InMemoryCustodyFixture(SyntheticSeed seed)
        {
            if (seed != SyntheticSeed.Absent && seed != SyntheticSeed.Present)
                throw new ArgumentException("synthetic seed");
            string journal = CustodyLedger.CreateInitial(new string('0', 32));
            if (seed == SyntheticSeed.Present)
                journal = CustodyLedger.AppendTerminal(CustodyLedger.AppendIntent(journal,
                    LedgerOperation.Save, new string('1', 32)));
            image = new SyntheticCustodyImage(journal, CustodyLedger.Anchor(journal), null,
                seed == SyntheticSeed.Present ? 1 : 0);
        }
        internal SyntheticCustodyImage Claim()
        {
            if (Interlocked.CompareExchange(ref claimed, 1, 0) != 0) throw new InvalidOperationException("fixture already owned");
            return image;
        }
    }

    // One request, one owner, one gate, no queue or replay. This is compiled into the
    // synthetic-only test assembly, excluded from the service project. Synthetic review is not consent.
    internal sealed class CustodyTransactionCore
    {
        private readonly object gate = new object();
        private string journal, anchor;
        private SyntheticTransactionRequest persistedRequest;
        private int marker;
        private readonly SyntheticTransactionRequest request;
        private readonly SyntheticCrash crash;
        private CustodyStage stage = CustodyStage.ReviewPending;
        // A single CAS word orders uncertainty, commitment and terminal publication.
        // Uncertainty is sticky, including after a previously published terminal result.
        private const int Unknown = 1, Committed = 2, OutcomeShift = 2;
        private int publication;
        private CoreOutcome outcome { get { return Outcome(Volatile.Read(ref publication)); } }
        private bool possible { get { return (Volatile.Read(ref publication) & Committed) != 0; } }
        private bool recovery;
        private int attempts;
        private object review;
        // Fixed test rendezvous, installed through reflection within the synthetic assembly only.
        // No callback can run inside the owner gate. The pause itself is bounded.
        private ManualResetEventSlim dispatchEntered = null;
        private ManualResetEventSlim dispatchContinue = null;
        private ManualResetEventSlim controlWaiting = null;
        // 1/2: before/after commitment; 3/4: before/after dispatch terminal;
        // 5/6: before/after control terminal. Fixed events only, never delegates.
        private int pauseAt = 0;
        private ManualResetEventSlim transitionEntered = null;
        private ManualResetEventSlim transitionContinue = null;

        internal CustodyTransactionCore(InMemoryCustodyFixture state, SyntheticTransactionRequest identity,
            SyntheticCrash crashPoint)
        {
            if (state == null) throw new ArgumentNullException("state");
            SyntheticCustodyImage initial = state.Claim();
            journal = initial.Journal; anchor = initial.Anchor; marker = initial.Marker;
            persistedRequest = initial.Request;
            request = identity; crash = crashPoint;
            if (!Valid(identity) || !Enum.IsDefined(typeof(SyntheticCrash), crashPoint))
            { Finish(CoreOutcome.Denied); return; }
            try
            {
                LedgerPhase phase = CustodyLedger.Verify(journal, anchor);
                bool present = phase == LedgerPhase.CommittedUnverified;
                if (persistedRequest != null || phase == LedgerPhase.InFlight ||
                    (marker != 0 && marker != 1) || (marker == 1) != present)
                    throw new LedgerBlocked();
                if (present != (request.Operation != SyntheticOperation.Add)) Finish(CoreOutcome.Denied);
            }
            catch (Exception) { Hold(); }
        }

        private static bool Valid(SyntheticTransactionRequest value)
        {
            return value != null && value.Owner != Guid.Empty && value.Epoch == 1 && value.RequestId != 0 &&
                (value.Operation == SyntheticOperation.Add || value.Operation == SyntheticOperation.Replace ||
                 value.Operation == SyntheticOperation.Delete);
        }
        private static bool Same(SyntheticTransactionRequest left, SyntheticTransactionRequest right)
        {
            return Valid(left) && Valid(right) && left.Owner == right.Owner && left.Epoch == right.Epoch &&
                left.RequestId == right.RequestId && left.Operation == right.Operation;
        }
        private static LedgerOperation Operation(SyntheticOperation value)
        {
            switch (value)
            {
                case SyntheticOperation.Add: return LedgerOperation.Save;
                case SyntheticOperation.Replace: return LedgerOperation.Replace;
                case SyntheticOperation.Delete: return LedgerOperation.Delete;
                default: throw new LedgerBlocked();
            }
        }
        private static string RequestNonce(SyntheticTransactionRequest value)
        {
            string metadata = "P320|" + value.Owner.ToString("N") + "|" +
                value.Epoch.ToString(CultureInfo.InvariantCulture) + "|" +
                value.RequestId.ToString(CultureInfo.InvariantCulture) + "|" +
                ((int)value.Operation).ToString(CultureInfo.InvariantCulture);
            using (SHA256 hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(Encoding.ASCII.GetBytes(metadata)), 0, 16)
                    .Replace("-", "").ToLowerInvariant();
        }
        private bool Enter()
        {
            if (Monitor.IsEntered(gate))
            { PublishUnknown(); return false; }
            if (Monitor.TryEnter(gate, 2000)) return true;
            PublishUnknown(); return false;
        }
        private static CoreOutcome Outcome(int state)
        { return (state & Unknown) != 0 ? CoreOutcome.RecoveryRequired : (CoreOutcome)(state >> OutcomeShift); }
        private void PublishUnknown()
        {
            int seen;
            do { seen = Volatile.Read(ref publication); }
            while (Interlocked.CompareExchange(ref publication, seen | Unknown, seen) != seen);
        }
        private void Barrier()
        { if ((Volatile.Read(ref publication) & Unknown) != 0) throw new LedgerBlocked(); }
        private void Exit() { Monitor.Exit(gate); }
        private void Pause(int point)
        {
            if (pauseAt != point) return;
            if (transitionEntered != null) transitionEntered.Set();
            if (transitionContinue != null && !transitionContinue.Wait(5000)) throw new LedgerBlocked();
        }
        private void CommitPossibleEffect()
        {
            // If uncertainty wins this CAS, no commitment or attempt can follow.
            // If commitment wins, MayHaveEffect stays true even if the next barrier
            // prevents an attempt. Uncertainty after that barrier cannot retract commitment.
            if (Interlocked.CompareExchange(ref publication, Committed, 0) != 0) throw new LedgerBlocked();
            stage = CustodyStage.PossibleEffect;
        }
        private void Finish(CoreOutcome value)
        {
            int seen, next;
            do
            {
                seen = Volatile.Read(ref publication);
                CoreOutcome terminal = Outcome(seen);
                if (value == CoreOutcome.RecoveryRequired) terminal = value;
                else if (terminal == CoreOutcome.None) terminal = value;
                next = (seen & (Unknown | Committed)) | ((int)terminal << OutcomeShift);
            } while (Interlocked.CompareExchange(ref publication, next, seen) != seen);
            stage = CustodyStage.Terminal; review = null;
        }
        private void Hold() { recovery = true; Finish(CoreOutcome.RecoveryRequired); }
        private void CrashAt(SyntheticCrash point)
        { Barrier(); if (crash == point) throw new LedgerBlocked(); }
        private CoreSnapshot Snapshot()
        {
            int state = Volatile.Read(ref publication);
            CoreOutcome result = Outcome(state);
            return new CoreSnapshot(request, result == CoreOutcome.None ? stage : CustodyStage.Terminal,
                result, (state & Committed) != 0, recovery || (state & Unknown) != 0, attempts);
        }

        internal CoreSnapshot Observe()
        {
            if (!Enter())
            {
                int state = Volatile.Read(ref publication);
                bool committed = (state & Committed) != 0;
                // Gate failure cannot read the gate-owned attempt counter. Zero is
                // known only if commitment was prevented; otherwise it is unknown.
                return new CoreSnapshot(request, CustodyStage.Terminal,
                    CoreOutcome.RecoveryRequired, committed, true, 0, !committed);
            }
            try { return Snapshot(); }
            finally { Exit(); }
        }

        // An opaque service-owned synthetic review identity. Not transferable, serializable,
        // human approval, policy or a production authorization result.
        internal object ReviewSynthetic(SyntheticTransactionRequest offered)
        {
            if (!Enter()) return null;
            try
            {
                Barrier();
                if (stage != CustodyStage.ReviewPending) return null;
                if (!Same(request, offered)) { Finish(CoreOutcome.Denied); return null; }
                review = new object(); stage = CustodyStage.Reviewed; return review;
            }
            catch (LedgerBlocked) { Hold(); return null; }
            finally { Exit(); }
        }

        internal CoreControlResult Control(CoreControl control)
        {
            if (controlWaiting != null) controlWaiting.Set();
            if (!Enter()) return CoreControlResult.HoldUnknown;
            try
            {
                int state = Volatile.Read(ref publication);
                if ((state & Unknown) != 0) return CoreControlResult.HoldUnknown;
                if ((state & Committed) != 0) return CoreControlResult.TooLatePossibleEffect;
                if (Outcome(state) != CoreOutcome.None) return CoreControlResult.AlreadyTerminal;
                if (!Enum.IsDefined(typeof(CoreControl), control))
                { Hold(); return CoreControlResult.HoldUnknown; }
                Pause(5);
                Finish(control == CoreControl.Cancel ? CoreOutcome.Cancelled : control == CoreControl.Revoke ?
                    CoreOutcome.Revoked : control == CoreControl.Stop ? CoreOutcome.Stopped : CoreOutcome.Faulted);
                Pause(6);
                return outcome == CoreOutcome.RecoveryRequired ? CoreControlResult.HoldUnknown : CoreControlResult.Applied;
            }
            catch (LedgerBlocked) { Hold(); return CoreControlResult.HoldUnknown; }
            finally { Exit(); }
        }

        // Whole intent/effect/terminal sequence shares the review/control gate. The ONLY
        // effect here is this fixture's fixed integer mutation. No production effect port.
        internal CoreOutcome DispatchSynthetic(object offeredReview, SyntheticTransactionRequest offeredRequest)
        {
            if (!Enter()) return CoreOutcome.RecoveryRequired;
            try
            {
                if (outcome != CoreOutcome.None) return outcome;
                Barrier();
                if (stage != CustodyStage.Reviewed || offeredReview == null ||
                    !Object.ReferenceEquals(review, offeredReview) || !Same(request, offeredRequest))
                { Finish(CoreOutcome.Denied); return outcome; }
                review = null; // one-use BEFORE any possible storage/effect attempt
                CrashAt(SyntheticCrash.BeforeIntent);
                stage = CustodyStage.IntentWriting; recovery = true;
                persistedRequest = request;
                CrashAt(SyntheticCrash.AfterIdentity);
                string intent = CustodyLedger.AppendIntent(journal, Operation(request.Operation), RequestNonce(request));
                journal = intent;
                CrashAt(SyntheticCrash.AfterIntentJournal);
                anchor = CustodyLedger.Anchor(intent);
                CrashAt(SyntheticCrash.AfterIntentAnchor);
                // Memory stand-in for persist+flush+readback+identity verification.
                // This is a contract checkpoint, NEVER a physical durability claim.
                if (CustodyLedger.Verify(journal, anchor) != LedgerPhase.InFlight ||
                    !Same(persistedRequest, request)) throw new LedgerBlocked();
                stage = CustodyStage.IntentDurable;
                if (dispatchEntered != null) dispatchEntered.Set();
                if (dispatchContinue != null && !dispatchContinue.Wait(5000)) throw new LedgerBlocked();
                CrashAt(SyntheticCrash.BeforeEffect);
                Pause(1);
                CommitPossibleEffect();
                Pause(2);
                Barrier();
                attempts++;
                CrashAt(SyntheticCrash.AfterAttempt);
                marker = request.Operation == SyntheticOperation.Delete ? 0 : 1;
                CrashAt(SyntheticCrash.AfterMutation);
                string terminal = CustodyLedger.AppendTerminal(intent);
                journal = terminal;
                CrashAt(SyntheticCrash.AfterTerminalJournal);
                anchor = CustodyLedger.Anchor(terminal);
                CrashAt(SyntheticCrash.AfterTerminalAnchor);
                LedgerPhase expected = request.Operation == SyntheticOperation.Delete ?
                    LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified;
                if (CustodyLedger.Verify(journal, anchor) != expected ||
                    marker != (request.Operation == SyntheticOperation.Delete ? 0 : 1) ||
                    !Same(persistedRequest, request)) throw new LedgerBlocked();
                CrashAt(SyntheticCrash.AfterTerminalVerify);
                Pause(3);
                Finish(request.Operation == SyntheticOperation.Delete ? CoreOutcome.RemovedUnverified : CoreOutcome.StoredUnverified);
                Pause(4);
            }
            catch (Exception) { Hold(); }
            finally { Exit(); }
            return outcome;
        }

        internal SyntheticCustodyImage CaptureSyntheticCrashImage()
        {
            if (!Enter()) return null;
            try { return new SyntheticCustodyImage(journal, anchor, persistedRequest, marker); }
            finally { Exit(); }
        }

        // Read-only classification only. There is intentionally no restore/resume/retry/clear.
        internal static RestartAssessment AssessRestart(SyntheticCustodyImage image)
        {
            if (image == null) return RestartAssessment.Uncertain;
            try
            {
                LedgerPhase phase = CustodyLedger.Verify(image.Journal, image.Anchor);
                if (image.Marker != 0 && image.Marker != 1) return RestartAssessment.Malformed;
                if (phase == LedgerPhase.Initial)
                    return image.Request == null && image.Marker == 0 ?
                        RestartAssessment.InitialUnqualified : RestartAssessment.Malformed;
                if (!Valid(image.Request) || CustodyLedger.LastOperation(image.Journal) != Operation(image.Request.Operation))
                    return RestartAssessment.Malformed;
                CustodyFrame[] frames = CustodyLedger.Decode(image.Journal);
                if (frames[frames.Length - 1].Nonce != RequestNonce(image.Request)) return RestartAssessment.Malformed;
                if (phase == LedgerPhase.InFlight) return RestartAssessment.InFlight;
                if ((phase == LedgerPhase.CommittedUnverified) != (image.Marker == 1)) return RestartAssessment.Malformed;
                return RestartAssessment.TerminalUnverified;
            }
            catch (LedgerBlocked) { return RestartAssessment.Malformed; }
        }
    }
}
