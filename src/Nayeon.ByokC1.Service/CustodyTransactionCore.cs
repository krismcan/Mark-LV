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
        internal bool ProductionEligible { get { return false; } }
        internal CoreSnapshot(SyntheticTransactionRequest request, CustodyStage stage, CoreOutcome outcome,
            bool possible, bool recovery, int attempts)
        { Request = request; Stage = stage; Outcome = outcome; MayHaveEffect = possible;
            RecoveryRequired = recovery; Attempts = attempts; }
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
        private CoreOutcome outcome;
        private bool possible, recovery;
        private int attempts, uncertain;
        private object review;
        // Fixed test rendezvous, installed through reflection within the synthetic assembly only.
        // No callback can run inside the owner gate. The pause itself is bounded.
        private ManualResetEventSlim dispatchEntered = null;
        private ManualResetEventSlim dispatchContinue = null;
        private ManualResetEventSlim controlWaiting = null;

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
            { Interlocked.Exchange(ref uncertain, 1); return false; }
            if (Monitor.TryEnter(gate, 2000)) return true;
            Interlocked.Exchange(ref uncertain, 1); return false;
        }
        private void Barrier()
        { if (Volatile.Read(ref uncertain) != 0) throw new LedgerBlocked(); }
        private void Exit()
        {
            try { if (Volatile.Read(ref uncertain) != 0 && outcome == CoreOutcome.None) Hold(); }
            finally { Monitor.Exit(gate); }
        }
        private void Finish(CoreOutcome value)
        { stage = CustodyStage.Terminal; outcome = value; review = null; }
        private void Hold() { recovery = true; Finish(CoreOutcome.RecoveryRequired); }
        private void CrashAt(SyntheticCrash point)
        { Barrier(); if (crash == point) throw new LedgerBlocked(); }
        private CoreSnapshot Snapshot()
        { return new CoreSnapshot(request, stage, outcome, possible, recovery, attempts); }

        internal CoreSnapshot Observe()
        {
            if (!Enter()) return new CoreSnapshot(request, CustodyStage.Terminal,
                CoreOutcome.RecoveryRequired, true, true, 0);
            try { if (Volatile.Read(ref uncertain) != 0 && outcome == CoreOutcome.None) Hold(); return Snapshot(); }
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
            catch (LedgerBlocked) { if (outcome == CoreOutcome.None) Hold(); return null; }
            finally { Exit(); }
        }

        internal CoreControlResult Control(CoreControl control)
        {
            if (controlWaiting != null) controlWaiting.Set();
            if (!Enter()) return CoreControlResult.HoldUnknown;
            try
            {
                if (possible) return CoreControlResult.TooLatePossibleEffect;
                if (outcome != CoreOutcome.None) return CoreControlResult.AlreadyTerminal;
                if (Volatile.Read(ref uncertain) != 0 || !Enum.IsDefined(typeof(CoreControl), control))
                { Hold(); return CoreControlResult.HoldUnknown; }
                Finish(control == CoreControl.Cancel ? CoreOutcome.Cancelled : control == CoreControl.Revoke ?
                    CoreOutcome.Revoked : control == CoreControl.Stop ? CoreOutcome.Stopped : CoreOutcome.Faulted);
                return CoreControlResult.Applied;
            }
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
                possible = true; stage = CustodyStage.PossibleEffect; attempts++;
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
                Finish(request.Operation == SyntheticOperation.Delete ? CoreOutcome.RemovedUnverified : CoreOutcome.StoredUnverified);
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
