#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P284_DURABLE_OPERATION_REVIEW_ONLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY || !C1_P270_DEVELOPMENT_ONLY || !C1_P271_DEVELOPMENT_ONLY || !C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY
#error P284_TEST_ONLY_ALL_DURABLE_FLAGS_REQUIRED
#endif
using System;
using System.Security.Cryptography;
using System.Threading;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P269Development;
using Nayeon.ByokC1.P271Development;

namespace Nayeon.ByokC1.P284Development
{
    // TEST ONLY. One private P271 durable bridge, never a production factory.
    // Neither this issuer nor its ticket is human consent or serializable authority.
    internal sealed class DurableOperationAdmission : IDisposable
    {
        internal sealed class TestOnlyIssuer { internal TestOnlyIssuer() { } }
        internal sealed class TestOnlyTicket { internal TestOnlyTicket() { }
            public override string ToString() { return "<P284 TEST ONLY nontransferable>"; } }
        private readonly TestOnlyIssuer issuer = new TestOnlyIssuer();
        private readonly DurableDevelopmentBridge service;
        private readonly P282ExecutingServiceCustody.SyntheticRunnerBinding runnerIdentity;
        private readonly LedgerOperation operation;
        private ServiceBoundRequestIdentity bound;
        private ServiceOwnedPendingTransaction.Approval approval;
        private TestOnlyTicket ticket;
        // 0 unused, 1 preparing, 2 issued, 3 submitting, 4 terminal/cancelled.
        private int state;
        private int controlUncertain;
        internal Action<string> TestProbe;

        private DurableOperationAdmission(string root, LedgerOperation op, bool fresh)
        {
            if (op != LedgerOperation.Save && op != LedgerOperation.Replace && op != LedgerOperation.Delete)
                throw new ArgumentException("operation");
            // Capture actual executing synthetic runner identity; no claimed SID or
            // request field supplies it. P271 independently retains its own binding.
            runnerIdentity = P282ExecutingServiceCustody.BindSyntheticRunner();
            runnerIdentity.DemandUnchanged();
            operation = op;
            service = new DurableDevelopmentBridge(root, op, fresh);
            service.TestProbe = ProbeInsidePendingGate;
        }
        internal static DurableOperationAdmission TestOnlyCreate(string root, LedgerOperation op, bool fresh,
            out TestOnlyIssuer fixtureIssuer)
        {
            var owner = new DurableOperationAdmission(root, op, fresh);
            fixtureIssuer = owner.issuer; return owner;
        }
        internal static bool ProductionEligible { get { return false; } }
        internal static bool HumanConsentEstablished { get { return false; } }
        internal bool Start()
        {
            try
            {
                runnerIdentity.DemandUnchanged();
                bool started = service.Start();
                if (!started) Interlocked.Exchange(ref controlUncertain, 1);
                return started;
            }
            catch { Interlocked.Exchange(ref controlUncertain, 1); throw; }
        }

        // Hash the ONLY P268-permitted ephemeral marker. Caller digests prove nothing.
        internal static string TestMarkerDigest()
        {
            using (SHA256 hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(new byte[] { 0x31, 0x32, 0x33, 0x34 }))
                    .Replace("-", "").ToLowerInvariant();
        }
        private bool Valid(ServiceBoundRequestIdentity request, byte[] marker)
        {
            return request != null && request.Operation == operation &&
                request.HasSafeClockWindow(DateTime.UtcNow.Ticks) &&
                (operation == LedgerOperation.Delete ? marker == null && request.CandidateSha256 == null &&
                    request.DestructiveAcknowledgement : DevelopmentPendingState.Synthetic(marker) &&
                    request.CandidateSha256 == TestMarkerDigest() && !request.DestructiveAcknowledgement);
        }
        private bool Same(ServiceBoundRequestIdentity request)
        {
            return request != null && bound != null && request.Operation == bound.Operation &&
                request.SessionId == bound.SessionId && request.RequestId == bound.RequestId &&
                request.CandidateSha256 == bound.CandidateSha256 && request.ExpiresUtcTicks == bound.ExpiresUtcTicks &&
                request.DestructiveAcknowledgement == bound.DestructiveAcknowledgement;
        }
        internal TestOnlyTicket Issue(TestOnlyIssuer fixtureIssuer, ServiceBoundRequestIdentity request, byte[] marker)
        {
            if (!Object.ReferenceEquals(fixtureIssuer, issuer)) return null;
            // Reserve before hashing/preparing; no callback can mint a second approval.
            if (Interlocked.CompareExchange(ref state, 1, 0) != 0) return null;
            try
            {
                runnerIdentity.DemandUnchanged();
                if (Volatile.Read(ref controlUncertain) != 0) return null;
                if (!Valid(request, marker)) return null;
                bound = request;
                approval = service.Prepare();
                if (approval == null) return null;
                ticket = new TestOnlyTicket();
                if (Interlocked.CompareExchange(ref state, 2, 1) != 1) return null;
                return ticket;
            }
            catch { Interlocked.Exchange(ref controlUncertain, 1); throw; }
            finally
            {
                if (Interlocked.CompareExchange(ref state, 4, 1) == 1) Revoke();
            }
        }
        internal CustodyOutcome Submit(TestOnlyTicket offered, ServiceBoundRequestIdentity request, byte[] marker)
        {
            // A malformed/fabricated first attempt also consumes/cancels this session.
            if (Interlocked.CompareExchange(ref state, 3, 2) != 2) return CustodyOutcome.Denied;
            try
            {
                runnerIdentity.DemandUnchanged();
                if (Volatile.Read(ref controlUncertain) != 0)
                { Fault(); return CustodyOutcome.RecoveryRequired; }
                if (!Object.ReferenceEquals(offered, ticket) || !Same(request) || !Valid(request, marker))
                { Revoke(); return CustodyOutcome.Denied; }
                // No caller buffer crosses this boundary: P269 supplies its fixed marker.
                return service.Submit(approval);
            }
            catch { Interlocked.Exchange(ref controlUncertain, 1); throw; }
            finally { Interlocked.Exchange(ref state, 4); }
        }
        private void ProbeInsidePendingGate(string point)
        {
            // Only P271 installs this delegate. Calling a diagnostic callback is
            // never submission/consent. No bridge or private approval escapes.
            Action<string> adversary = TestProbe;
            if (adversary != null) adversary(point);
            runnerIdentity.DemandUnchanged();
            // Runs INSIDE P268's existing gate, including effect-enter immediately
            // before the actual P96 fixture call. No parallel revocation/effect gate.
            // An expired final check throws into P268's recovery/cleanup path.
            if (Volatile.Read(ref controlUncertain) != 0 || Volatile.Read(ref state) != 3 || bound == null ||
                !bound.HasSafeClockWindow(DateTime.UtcNow.Ticks)) throw new LedgerBlocked();
        }
        private ControlResult Control(int reason)
        {
            try { return reason == 0 ? service.Revoke() :
                reason == 1 ? service.Stop() : service.Fault(); }
            catch
            {
                // A callback may swallow a reentrant/uncertain P268 control error.
                // Latch it before returning to that callback, then reject INSIDE
                // the same pending probe before its fixture effect can continue.
                Interlocked.Exchange(ref controlUncertain, 1); throw;
            }
        }
        internal ControlResult Revoke() { return Control(0); }
        internal ControlResult Stop() { return Control(1); }
        internal ControlResult Fault() { return Control(2); }
        internal CompositionObservation Observe()
        {
            var observation = service.Observe();
            if (observation.Closed) Interlocked.Exchange(ref controlUncertain, 1);
            return observation;
        }
        internal int TestEffects { get { return service.TestEffects; } }
        internal bool TestConsistent() { return service.TestConsistent(); }
        internal bool TestTerminal { get { return service.TestTerminal; } }
        internal void TestFailEffect() { service.TestEffectFailure(); }
        internal void TestCloseWitness() { service.TestCloseWitness(); }
        internal LedgerPhase TestPhase() { return service.TestPhase(); }
        public void Dispose()
        {
            try { service.Dispose(); }
            catch { Interlocked.Exchange(ref controlUncertain, 1); throw; }
        }
    }
}
