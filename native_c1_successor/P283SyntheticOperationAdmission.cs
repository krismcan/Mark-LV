#if !DEBUG || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P283_SYNTHETIC_OPERATION_REVIEW_ONLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY
#error P283_TEST_ONLY_ALL_DEVELOPMENT_FLAGS_REQUIRED
#endif
using System;
using System.Security.Cryptography;
using System.Threading;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P269Development;

namespace Nayeon.ByokC1.P283Development
{
    // TEST ONLY. One private in-memory P269 fixture, never a production factory.
    // Neither this issuer nor its ticket is human consent or serializable authority.
    internal sealed class SyntheticOperationAdmission : IDisposable
    {
        internal sealed class TestOnlyIssuer { internal TestOnlyIssuer() { } }
        internal sealed class TestOnlyTicket { internal TestOnlyTicket() { }
            public override string ToString() { return "<P283 TEST ONLY nontransferable>"; } }
        private readonly TestOnlyIssuer issuer = new TestOnlyIssuer();
        private readonly ComposedDevelopmentService service;
        private readonly LedgerOperation operation;
        private ServiceBoundRequestIdentity bound;
        private ServiceOwnedPendingTransaction.Approval approval;
        private TestOnlyTicket ticket;
        // 0 unused, 1 preparing, 2 issued, 3 submitting, 4 terminal/cancelled.
        private int state;
        private int controlUncertain;
        internal Action<string> TestProbe;

        private SyntheticOperationAdmission(LedgerOperation op, bool fresh)
        {
            if (op != LedgerOperation.Save && op != LedgerOperation.Replace && op != LedgerOperation.Delete)
                throw new ArgumentException("operation");
            operation = op;
            service = ComposedDevelopmentService.TestOnlyCreate(op, fresh);
            service.TestAdapter.Inject = ProbeInsidePendingGate;
        }
        internal static SyntheticOperationAdmission TestOnlyCreate(LedgerOperation op, bool fresh,
            out TestOnlyIssuer fixtureIssuer)
        {
            var owner = new SyntheticOperationAdmission(op, fresh);
            fixtureIssuer = owner.issuer; return owner;
        }
        internal static bool ProductionEligible { get { return false; } }
        internal static bool HumanConsentEstablished { get { return false; } }
        internal bool Start()
        {
            try { return service.StartDevelopment(); }
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
                if (!Valid(request, marker)) return null;
                bound = request;
                approval = service.TestPrepare(operation);
                if (approval == null) return null;
                ticket = new TestOnlyTicket();
                if (Interlocked.CompareExchange(ref state, 2, 1) != 1) return null;
                return ticket;
            }
            finally
            {
                if (Interlocked.CompareExchange(ref state, 4, 1) == 1) service.RevokeDevelopment();
            }
        }
        internal CustodyOutcome Submit(TestOnlyTicket offered, ServiceBoundRequestIdentity request, byte[] marker)
        {
            // A malformed/fabricated first attempt also consumes/cancels this session.
            if (Interlocked.CompareExchange(ref state, 3, 2) != 2) return CustodyOutcome.Denied;
            try
            {
                if (!Object.ReferenceEquals(offered, ticket) || !Same(request) || !Valid(request, marker))
                { service.RevokeDevelopment(); return CustodyOutcome.Denied; }
                // No caller buffer crosses this boundary: P269 supplies its fixed marker.
                return service.TestSubmit(approval, operation);
            }
            finally { Interlocked.Exchange(ref state, 4); }
        }
        private void ProbeInsidePendingGate(string point)
        {
            Action<string> adversary = TestProbe;
            if (adversary != null) adversary(point);
            // Runs INSIDE P268's existing gate, including effect-enter immediately
            // before the actual P96 fixture call. No parallel revocation/effect gate.
            // An expired final check throws into P268's recovery/cleanup path.
            if (Volatile.Read(ref controlUncertain) != 0 || Volatile.Read(ref state) != 3 || bound == null ||
                !bound.HasSafeClockWindow(DateTime.UtcNow.Ticks)) throw new LedgerBlocked();
        }
        private ControlResult Control(int reason)
        {
            try { return reason == 0 ? service.RevokeDevelopment() :
                reason == 1 ? service.StopDevelopment() : service.FaultDevelopment(); }
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
        internal int TestEffects { get { return service.TestState.PossibleEffects; } }
        internal int TestCallerApprovalConsumes { get { return service.TestApproval.ConsumeCount; } }
        internal bool TestTerminal { get { return service.TestGuard.TerminalMarked && service.TestGuard.LeaseDisposed; } }
        internal void TestFailEffect() { service.TestState.ThrowDuringEffect = true; }
        public void Dispose()
        {
            try { service.Dispose(); }
            catch { Interlocked.Exchange(ref controlUncertain, 1); throw; }
        }
    }
}
