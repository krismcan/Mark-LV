#if !DEBUG
#error P272_NO_RELEASE_BUILD
#endif
#if !C1_P272_DEVELOPMENT_ONLY || !C1_REVIEW_ISOLATED_ASSEMBLY
#error P272_ISOLATED_DEVELOPMENT_REQUIRED
#endif
using System;
using System.ComponentModel;
using System.ServiceProcess;
using Nayeon.ByokC1.P271Development;

namespace Nayeon.ByokC1.P272Development
{
    public enum DependencyState { NotWired, NotValidated }
    public enum AdmissionDecision { DeniedDevelopmentAssembly, DeniedUnknownOperation }
    public enum CustodyOperation { Save, Replace, Delete }
    public enum ScmSampleState { Missing, Denied, Unverified, UnsupportedOs, Changed, Sampled }

    // A requirement contract, deliberately NOT an injectable approval provider.
    // A future independent authority must bind a protected monotonic epoch to
    // exact operation, custody history and service instance across restarts.
    // Consent must authenticate the human and exact one-use operation/revocation.
    public sealed class ProductionDependencies
    {
        internal ProductionDependencies() { }
        public DependencyState IndependentMonotonicAuthority { get { return DependencyState.NotWired; } }
        public DependencyState AuthenticatedExactOperationConsent { get { return DependencyState.NotWired; } }
        public DependencyState QualifiedPrincipalDecision { get { return DependencyState.NotValidated; } }
        public DependencyState IsolatedRunningTokenAndSigner { get { return DependencyState.NotValidated; } }
        public DependencyState ProtectedStoreRoot { get { return DependencyState.NotValidated; } }
        public DependencyState CustodyFreshness { get { return DependencyState.NotValidated; } }
    }

    // SCM configuration/status are samples, NOT token, image or consent proof.
    // Even two identical samples cannot exclude change-and-revert/ABA races.
    public sealed class OsCustodyObservation
    {
        private readonly P261ScmEvidence first, last;
        public readonly ScmSampleState Status;
        public readonly ServiceControllerStatus? FirstStatus, LastStatus;
        public string ServiceName { get { return ServiceGate.ServiceName; } }
        public string DerivedVirtualAccount { get { return "NT SERVICE\\" + ServiceGate.ServiceName; } }
        public bool RestrictedConfigurationObserved
        {
            get { return first.Status == P261ScmStatus.ConfigObserved &&
                last.Status == P261ScmStatus.ConfigObserved && SameConfiguration(first, last); }
        }
        public bool ServiceAbsentInBothConfigurationSamples
        { get { return first.Status == P261ScmStatus.Missing && last.Status == P261ScmStatus.Missing; } }
        public DependencyState RunningIdentityProof { get { return DependencyState.NotValidated; } }
        private OsCustodyObservation(P261ScmEvidence before, P261ScmEvidence after,
            ScmSampleState state, ServiceControllerStatus? start, ServiceControllerStatus? end)
        { first = before; last = after; Status = state; FirstStatus = start; LastStatus = end; }
        private static bool SameConfiguration(P261ScmEvidence a, P261ScmEvidence b)
        {
            return a.Status == b.Status && a.ServiceOpened == b.ServiceOpened &&
                a.AccountQueried == b.AccountQueried &&
                a.VirtualAccountMatchesServiceName == b.VirtualAccountMatchesServiceName &&
                a.ServiceSidType == b.ServiceSidType;
        }
        internal static ScmSampleState ClassifyError(int code)
        {
            return code == 1060 ? ScmSampleState.Missing :
                code == 5 ? ScmSampleState.Denied : ScmSampleState.Unverified;
        }
        internal static ScmSampleState ClassifySamples(P261ScmEvidence a, P261ScmEvidence b,
            ScmSampleState status, ServiceControllerStatus? start, ServiceControllerStatus? end)
        {
            if (!SameConfiguration(a, b) || start != end) return ScmSampleState.Changed;
            if (a.Status == P261ScmStatus.Missing && status == ScmSampleState.Missing) return status;
            if (a.Status == P261ScmStatus.Denied || status == ScmSampleState.Denied) return ScmSampleState.Denied;
            if (a.Status != P261ScmStatus.ConfigObserved) return ScmSampleState.Unverified;
            if (!start.HasValue || !Enum.IsDefined(typeof(ServiceControllerStatus), start.Value))
                return ScmSampleState.Unverified;
            return status;
        }
        internal static OsCustodyObservation Observe()
        {
            // Reuse P261's bounded buffer parsing, restricted SID semantics,
            // least-rights configuration query and fail-closed handle cleanup.
            P261ScmEvidence before = P261ScmReadOnlyAdmission.Observe();
            ServiceControllerStatus? start = null, end = null;
            ScmSampleState state = ScmSampleState.Unverified;
            if (Environment.OSVersion.Platform != PlatformID.Win32NT)
                state = ScmSampleState.UnsupportedOs;
            else
            {
                try
                {
                    // Framework ServiceController uses read-only QUERY_STATUS.
                    // No PID-to-token inference, process opening or service control.
                    using (ServiceController service = new ServiceController(ServiceGate.ServiceName, "."))
                    {
                        service.Refresh(); start = service.Status;
                        service.Refresh(); end = service.Status;
                        state = ScmSampleState.Sampled;
                    }
                }
                catch (InvalidOperationException e)
                {
                    Win32Exception win32 = e.InnerException as Win32Exception;
                    state = win32 == null ? ScmSampleState.Unverified : ClassifyError(win32.NativeErrorCode);
                }
                catch (Win32Exception e) { state = ClassifyError(e.NativeErrorCode); }
                catch (System.Security.SecurityException) { state = ScmSampleState.Denied; }
            }
            P261ScmEvidence after = P261ScmReadOnlyAdmission.Observe();
            if (state != ScmSampleState.UnsupportedOs)
                state = ClassifySamples(before, after, state, start, end);
            return new OsCustodyObservation(before, after, state, start, end);
        }
    }

    public sealed class CustodyAdmissionResult
    {
        public readonly AdmissionDecision Decision;
        public readonly CustodyOperation Operation;
        public readonly OsCustodyObservation Observation;
        public readonly ProductionDependencies Required = new ProductionDependencies();
        internal CustodyAdmissionResult(CustodyOperation operation)
        {
            Operation = operation;
            Observation = OsCustodyObservation.Observe();
            Decision = Enum.IsDefined(typeof(CustodyOperation), operation) ?
                AdmissionDecision.DeniedDevelopmentAssembly : AdmissionDecision.DeniedUnknownOperation;
        }
        public bool ProductionEligible { get { return false; } }
        public bool RealKeyEligible { get { return false; } }
        public bool MayInvokeWinCred { get { return false; } }
    }

    // Actual P271 composition seam. Public production attempts cannot construct,
    // start, prepare or submit the bridge. No secret/root/SID/consent input port.
    public sealed class OsBoundCustodyAdmission : IDisposable
    {
        private readonly object gate = new object();
        private readonly DurableDevelopmentBridge bridge;
        private bool disposed;
        private OsBoundCustodyAdmission(DurableDevelopmentBridge owned) { bridge = owned; }
        public static OsBoundCustodyAdmission CreateReadOnly()
        { return new OsBoundCustodyAdmission(null); }
        public CustodyAdmissionResult AttemptProduction(CustodyOperation operation)
        { return new CustodyAdmissionResult(operation); }

        // No public factory or environment value can select this path.
        // These accident barriers are P271's existing hosted-test constraints,
        // NEVER authenticated service identity or production authorization.
        internal static void RequireHostedTests()
        {
            DurableDevelopmentBridge.RequireHosted();
            if (Environment.GetEnvironmentVariable("P272_HOSTED_DISPOSABLE") != "1")
                throw new LedgerBlocked();
        }
        internal static OsBoundCustodyAdmission TestOnlyCreate(string root, LedgerOperation operation)
        {
            RequireHostedTests();
            return new OsBoundCustodyAdmission(new DurableDevelopmentBridge(root, operation, true));
        }
        internal CustodyOutcome TestOnlySubmit()
        {
            RequireHostedTests();
            lock (gate)
            {
                if (disposed || bridge == null || !bridge.Start()) return CustodyOutcome.Denied;
                return bridge.Submit(bridge.Prepare());
            }
        }
        internal int TestEffects { get { lock (gate) { return bridge == null ? 0 : bridge.TestEffects; } } }
        internal void TestUntrust() { lock (gate) { bridge.TestUntrust(); } }
        public void Dispose()
        {
            lock (gate)
            {
                if (disposed) return;
                // P271 retains custody on failed stop. Do not mask that failure.
                if (bridge != null) bridge.Dispose();
                disposed = true;
            }
        }
    }
}
