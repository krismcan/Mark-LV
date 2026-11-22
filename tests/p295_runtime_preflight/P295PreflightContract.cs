#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P295_OFFLINE_ONLY && !RELEASE
using System;
using System.Collections.Generic;

// NONDEPLOYABLE, OFFLINE SYNTHETIC PLAN CHECKLIST. No runtime evidence admission.
namespace P295Offline
{
    internal enum PrecheckOutcome { PRECHECK, HOLD, PLAN_ONLY }
    internal enum EvidenceSource
    {
        Unknown, SelfReport, StartupObserver, NativeScmObserver, KernelTokenObserver,
        RetainedProcessObserver, ImageCustodyReviewer, CimObserver, ChildObserver,
        ExternalDeadlineObserver
    }
    internal enum EvidenceKind
    {
        PreCreateAbsence, Configuration, DispatcherRegistration, OnStartEntry,
        LookupAndDisposal, OnStartCompletion, FrameworkReturn, ManagedTimerControl,
        IndependentDeadline, RunningStatus, ProcessBirthAndHandle, KernelTokenOne,
        KernelTokenTwo, ActualRestrictedSids, ImageProvenance, StoppedStatus,
        DeleteResponse, ClosedScmHandles, NativePostDeleteAbsence, CimAbsence,
        RetainedProcessExit, ChildExit, LateChildSweep
    }
    internal enum ApprovalRole { GOV01, GOV02, SEC03, SEC04, REL05, REL06, REL07 }

    // All strings below are inert fixture labels, never OS identities or handles.
    internal sealed class PlannedEvidence
    {
        internal readonly EvidenceKind Kind;
        internal readonly EvidenceSource Source;
        internal readonly string Collector, Run, Instance, Capture;
        internal readonly int Ordinal;
        internal readonly bool Synthetic, CompleteReceiptRequired, RequiredOnFailure;
        internal PlannedEvidence(EvidenceKind kind, EvidenceSource source, string collector,
            string run, string instance, string capture, int ordinal, bool synthetic,
            bool completeReceiptRequired, bool requiredOnFailure)
        {
            Kind=kind; Source=source; Collector=collector; Run=run; Instance=instance;
            Capture=capture; Ordinal=ordinal; Synthetic=synthetic;
            CompleteReceiptRequired=completeReceiptRequired; RequiredOnFailure=requiredOnFailure;
        }
    }
    internal sealed class RequiredApproval
    {
        internal readonly ApprovalRole Role;
        internal readonly string ExternalDecisionSource;
        internal readonly bool ExactSourceBound, MandatoryBeforeAnyRuntime;
        // This declares an obligation. It has no "approved" or authority-bearing field.
        internal RequiredApproval(ApprovalRole role, string externalDecisionSource,
            bool exactSourceBound, bool mandatoryBeforeAnyRuntime)
        {
            Role=role; ExternalDecisionSource=externalDecisionSource;
            ExactSourceBound=exactSourceBound; MandatoryBeforeAnyRuntime=mandatoryBeforeAnyRuntime;
        }
    }
    internal sealed class SourceExpectation
    {
        internal readonly string Path, Sha256;
        internal SourceExpectation(string path, string sha256) { Path=path; Sha256=sha256; }
    }
    internal sealed class StartupFixture
    {
        internal readonly bool DispatcherRegistered, OnStartEntered, OnStartCompleted,
            LookupSucceeded, IdentityDisposed, FrameworkSwallowedFailure, FlagSetBeforeOnStart,
            VerifiedFlagAfterDisposal, ManagedTimerFiredInFaultControl, ExternalDeadlineExit;
        internal readonly int FrameworkExit, ManagedDeadlineMs;
        internal StartupFixture(bool dispatcher, bool entered, bool completed, bool lookup,
            bool disposed, bool swallowed, bool preFlag, bool verifiedFlag, int frameworkExit,
            int deadlineMs, bool timerFiredInFaultControl, bool externalExit)
        {
            DispatcherRegistered=dispatcher; OnStartEntered=entered; OnStartCompleted=completed;
            LookupSucceeded=lookup; IdentityDisposed=disposed; FrameworkSwallowedFailure=swallowed;
            FlagSetBeforeOnStart=preFlag; VerifiedFlagAfterDisposal=verifiedFlag;
            FrameworkExit=frameworkExit; ManagedDeadlineMs=deadlineMs;
            ManagedTimerFiredInFaultControl=timerFiredInFaultControl; ExternalDeadlineExit=externalExit;
        }
    }
    internal sealed class TokenFixture
    {
        internal readonly string ExpectedPrincipal, Principal, RestrictedSid, ImageBefore,
            ImageAfter, TokenBefore, TokenAfter, HandleBefore, HandleAfter,
            AuthenticationBefore, AuthenticationAfter, ModifiedBefore, ModifiedAfter, RunnerPrincipal;
        internal readonly int PidBefore, PidAfter, Session;
        internal readonly long BirthBefore, BirthAfter;
        internal readonly bool Primary, Impersonated, Restricted, ImmutableImage, ProvenanceReviewed,
            ObserverImpersonated;
        internal TokenFixture(string expected, string principal, string restrictedSid,
            string imageBefore, string imageAfter, string tokenBefore, string tokenAfter,
            string handleBefore, string handleAfter, int pidBefore, int pidAfter,
            long birthBefore, long birthAfter, int session, bool primary, bool impersonated,
            bool restricted, bool immutableImage, bool provenanceReviewed, string authenticationBefore,
            string authenticationAfter, string modifiedBefore, string modifiedAfter,
            string runnerPrincipal, bool observerImpersonated)
        {
            ExpectedPrincipal=expected; Principal=principal; RestrictedSid=restrictedSid;
            ImageBefore=imageBefore; ImageAfter=imageAfter; TokenBefore=tokenBefore; TokenAfter=tokenAfter;
            HandleBefore=handleBefore; HandleAfter=handleAfter; PidBefore=pidBefore; PidAfter=pidAfter;
            BirthBefore=birthBefore; BirthAfter=birthAfter; Session=session; Primary=primary;
            Impersonated=impersonated; Restricted=restricted; ImmutableImage=immutableImage;
            ProvenanceReviewed=provenanceReviewed;
            AuthenticationBefore=authenticationBefore; AuthenticationAfter=authenticationAfter;
            ModifiedBefore=modifiedBefore; ModifiedAfter=modifiedAfter; RunnerPrincipal=runnerPrincipal;
            ObserverImpersonated=observerImpersonated;
        }
    }
    internal sealed class CleanupFixture
    {
        internal readonly int PreNativeCode, StartReturn, RunningState, StopState,
            DeleteReturn, PostNativeCode;
        internal readonly bool NativeCimAgree, HandlesClosed, RetainedExit, ChildrenAbsent,
            LateChild, CompleteReceipts, EarlierFailure;
        internal CleanupFixture(int preCode, int startReturn, int running, int stopped,
            int deleteReturn, int postCode, bool agree, bool handlesClosed, bool retainedExit,
            bool childrenAbsent, bool lateChild, bool receipts, bool earlierFailure)
        {
            PreNativeCode=preCode; StartReturn=startReturn; RunningState=running; StopState=stopped;
            DeleteReturn=deleteReturn; PostNativeCode=postCode; NativeCimAgree=agree;
            HandlesClosed=handlesClosed; RetainedExit=retainedExit; ChildrenAbsent=childrenAbsent;
            LateChild=lateChild; CompleteReceipts=receipts; EarlierFailure=earlierFailure;
        }
    }
    internal sealed class ProposedPlan
    {
        internal readonly string Parent, Run, Instance;
        internal readonly int InstanceCount;
        internal readonly bool OfflineSyntheticOnly, RequestsRuntimeAuthority, MutationRetry;
        internal readonly StartupFixture Startup;
        internal readonly TokenFixture Token;
        internal readonly CleanupFixture Cleanup;
        private readonly PlannedEvidence[] evidence;
        private readonly RequiredApproval[] approvals;
        private readonly SourceExpectation[] sources;
        internal ProposedPlan(string parent, string run, string instance, int instanceCount,
            bool offline, bool requestsAuthority, bool retry, StartupFixture startup,
            TokenFixture token, CleanupFixture cleanup, PlannedEvidence[] evidence,
            RequiredApproval[] approvals, SourceExpectation[] sources)
        {
            Parent=parent; Run=run; Instance=instance; InstanceCount=instanceCount;
            OfflineSyntheticOnly=offline; RequestsRuntimeAuthority=requestsAuthority; MutationRetry=retry;
            Startup=startup; Token=token; Cleanup=cleanup;
            this.evidence=evidence==null ? null : (PlannedEvidence[])evidence.Clone();
            this.approvals=approvals==null ? null : (RequiredApproval[])approvals.Clone();
            this.sources=sources==null ? null : (SourceExpectation[])sources.Clone();
        }
        internal int EvidenceCount { get { return evidence==null ? -1 : evidence.Length; } }
        internal int ApprovalCount { get { return approvals==null ? -1 : approvals.Length; } }
        internal int SourceCount { get { return sources==null ? -1 : sources.Length; } }
        internal PlannedEvidence EvidenceAt(int i) { return evidence[i]; }
        internal RequiredApproval ApprovalAt(int i) { return approvals[i]; }
        internal SourceExpectation SourceAt(int i) { return sources[i]; }
    }

    internal sealed class P295PreflightContract
    {
        internal const string InheritedParent="fc45574cb513f82af7d127846fd0b96b41129a4d";
        internal const string CandidatePath="tests/p294_dispatcher_first/P294DispatcherFirstDisposableService.cs";
        internal const string ContractPath="tests/p295_runtime_preflight/P295PreflightContract.cs";
        internal const string TestsPath="tests/p295_runtime_preflight/P295PreflightContractTests.cs";
        // Bounded, process-local reservation only; never durable/runtime replay protection.
        private static readonly HashSet<string> runs=new HashSet<string>(StringComparer.Ordinal);
        private static readonly object sync=new object();
        private PrecheckOutcome result=PrecheckOutcome.PRECHECK;
        internal PrecheckOutcome Result { get { return result; } }
        internal bool RuntimeAuthorized { get { return false; } }
        internal bool RealKeyAllowed { get { return false; } }
        internal bool ProductionAllowed { get { return false; } }
        internal bool ApprovedProvenance { get { return false; } }
        internal int AcceptedExternalApprovals { get { return 0; } }
        internal int AcceptedProductRegressions { get { return 0; } }

        internal static EvidenceSource RequiredSource(EvidenceKind kind)
        {
            switch (kind)
            {
                case EvidenceKind.DispatcherRegistration: case EvidenceKind.OnStartEntry:
                case EvidenceKind.LookupAndDisposal: case EvidenceKind.OnStartCompletion:
                case EvidenceKind.FrameworkReturn: case EvidenceKind.ManagedTimerControl:
                    return EvidenceSource.StartupObserver;
                case EvidenceKind.KernelTokenOne: case EvidenceKind.KernelTokenTwo:
                case EvidenceKind.ActualRestrictedSids: return EvidenceSource.KernelTokenObserver;
                case EvidenceKind.ProcessBirthAndHandle: case EvidenceKind.RetainedProcessExit:
                    return EvidenceSource.RetainedProcessObserver;
                case EvidenceKind.ImageProvenance: return EvidenceSource.ImageCustodyReviewer;
                case EvidenceKind.CimAbsence: return EvidenceSource.CimObserver;
                case EvidenceKind.ChildExit: case EvidenceKind.LateChildSweep: return EvidenceSource.ChildObserver;
                case EvidenceKind.IndependentDeadline: return EvidenceSource.ExternalDeadlineObserver;
                case EvidenceKind.PreCreateAbsence: case EvidenceKind.Configuration:
                case EvidenceKind.RunningStatus: case EvidenceKind.StoppedStatus:
                case EvidenceKind.DeleteResponse: case EvidenceKind.ClosedScmHandles:
                case EvidenceKind.NativePostDeleteAbsence: return EvidenceSource.NativeScmObserver;
                default: return EvidenceSource.Unknown;
            }
        }
        private static bool Label(string s) { return !String.IsNullOrWhiteSpace(s) && s.Length<=160; }
        private static bool Digest(string s)
        {
            if (s==null || s.Length!=64) return false;
            bool nonzero=false;
            foreach (char c in s)
            {
                if (!((c>='0' && c<='9') || (c>='a' && c<='f'))) return false;
                if (c!='0') nonzero=true;
            }
            return nonzero;
        }
        internal PrecheckOutcome Review(ProposedPlan p)
        {
            lock (sync)
            {
                // Reuse invalidates even a prior PLAN_ONLY. HOLD can never become PLAN_ONLY.
                if (result!=PrecheckOutcome.PRECHECK) return result=PrecheckOutcome.HOLD;
                result=PrecheckOutcome.HOLD;
                if (p==null || !Label(p.Run) || runs.Count>=4096 || !runs.Add(p.Run)) return result;
                if (Valid(p)) result=PrecheckOutcome.PLAN_ONLY;
                return result;
            }
        }
        private static bool Valid(ProposedPlan p)
        {
            if (p.Parent!=InheritedParent || !Label(p.Instance) || p.InstanceCount!=1 ||
                !p.OfflineSyntheticOnly || p.RequestsRuntimeAuthority || p.MutationRetry ||
                p.Startup==null || p.Token==null || p.Cleanup==null) return false;
            string[] paths={CandidatePath,ContractPath,TestsPath};
            if (p.SourceCount!=paths.Length) return false;
            for (int i=0;i<paths.Length;i++)
            {
                SourceExpectation pin=p.SourceAt(i);
                if (pin==null || pin.Path!=paths[i] || !Digest(pin.Sha256)) return false;
            }
            if (p.ApprovalCount!=7) return false;
            for (int i=0;i<7;i++)
            {
                RequiredApproval a=p.ApprovalAt(i);
                if (a==null || a.Role!=(ApprovalRole)i || !Label(a.ExternalDecisionSource) ||
                    !a.ExactSourceBound || !a.MandatoryBeforeAnyRuntime) return false;
            }
            int count=Enum.GetValues(typeof(EvidenceKind)).Length;
            if (p.EvidenceCount!=count) return false;
            var captures=new HashSet<string>(StringComparer.Ordinal);
            var collectors=new Dictionary<EvidenceSource,string>();
            var owners=new HashSet<string>(StringComparer.Ordinal);
            for (int i=0;i<count;i++)
            {
                PlannedEvidence e=p.EvidenceAt(i);
                if (e==null || e.Kind!=(EvidenceKind)i || e.Source!=RequiredSource(e.Kind) ||
                    !Label(e.Collector) || e.Run!=p.Run || e.Instance!=p.Instance ||
                    !Label(e.Capture) || !captures.Add(e.Capture) || e.Ordinal!=i+1 ||
                    !e.Synthetic || !e.CompleteReceiptRequired || !e.RequiredOnFailure) return false;
                string collector;
                if (collectors.TryGetValue(e.Source,out collector))
                { if (collector!=e.Collector) return false; }
                else
                {
                    if (!owners.Add(e.Collector)) return false;
                    collectors.Add(e.Source,e.Collector);
                }
            }
            StartupFixture s=p.Startup;
            if (!s.DispatcherRegistered || !s.OnStartEntered || !s.OnStartCompleted ||
                !s.LookupSucceeded || !s.IdentityDisposed || s.FrameworkSwallowedFailure ||
                s.FlagSetBeforeOnStart || !s.VerifiedFlagAfterDisposal || s.FrameworkExit!=0 ||
                s.ManagedDeadlineMs!=55000 || !s.ManagedTimerFiredInFaultControl ||
                !s.ExternalDeadlineExit) return false;
            TokenFixture t=p.Token;
            if (!Label(t.ExpectedPrincipal) || t.ExpectedPrincipal=="LocalSystem" ||
                t.ExpectedPrincipal=="S-1-5-18" || t.Principal!=t.ExpectedPrincipal ||
                !t.Primary || t.Impersonated || t.Session!=0 || !t.Restricted ||
                t.RestrictedSid!=t.ExpectedPrincipal || !Digest(t.ImageBefore) ||
                t.ImageAfter!=t.ImageBefore || !t.ImmutableImage || !t.ProvenanceReviewed ||
                t.PidBefore<=0 || t.PidAfter!=t.PidBefore || t.BirthBefore<=0 ||
                t.BirthAfter!=t.BirthBefore || !Label(t.TokenBefore) || t.TokenAfter!=t.TokenBefore ||
                !Label(t.HandleBefore) || t.HandleAfter!=t.HandleBefore) return false;
            if (!Label(t.AuthenticationBefore) || t.AuthenticationAfter!=t.AuthenticationBefore ||
                !Label(t.ModifiedBefore) || t.ModifiedAfter!=t.ModifiedBefore ||
                !Label(t.RunnerPrincipal) || t.RunnerPrincipal==t.Principal || t.ObserverImpersonated) return false;
            CleanupFixture c=p.Cleanup;
            // 1072 may be recorded but NEVER supplies absence. Only independent 1060 does.
            return c.PreNativeCode==1060 && c.StartReturn==0 && c.RunningState==4 &&
                c.StopState==1 && (c.DeleteReturn==0 || c.DeleteReturn==1072) &&
                c.PostNativeCode==1060 && c.NativeCimAgree && c.HandlesClosed && c.RetainedExit &&
                c.ChildrenAbsent && !c.LateChild && c.CompleteReceipts && !c.EarlierFailure;
        }
    }
}
#else
#error P295_DEBUG_ISOLATED_OFFLINE_ONLY_REQUIRED_RELEASE_FORBIDDEN
#endif
