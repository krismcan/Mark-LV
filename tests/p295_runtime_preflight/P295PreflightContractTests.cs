#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P295_OFFLINE_ONLY && !RELEASE
using System;
using P295Offline;

// The only executable entrypoint is a deterministic, in-memory synthetic test runner.
internal static class P295PreflightContractTests
{
    private static int serial, cases, assertions;
    private sealed class Builder
    {
        internal string Parent=P295PreflightContract.InheritedParent, Run, Instance="synthetic-instance";
        internal int InstanceCount=1;
        internal bool Offline=true, Authority=false, Retry=false;
        internal bool Dispatcher=true, Entered=true, Completed=true, Lookup=true, Disposed=true,
            Swallowed=false, PreFlag=false, Verified=true, TimerFired=true, ExternalExit=true;
        internal int FrameworkExit=0, DeadlineMs=55000;
        internal string Expected="synthetic-virtual-principal", Principal="synthetic-virtual-principal",
            Sid="synthetic-virtual-principal", ImageBefore=new string('a',64), ImageAfter=new string('a',64),
            TokenBefore="synthetic-token", TokenAfter="synthetic-token",
            HandleBefore="synthetic-retained", HandleAfter="synthetic-retained",
            AuthenticationBefore="synthetic-auth", AuthenticationAfter="synthetic-auth",
            ModifiedBefore="synthetic-modified", ModifiedAfter="synthetic-modified",
            RunnerPrincipal="synthetic-runner";
        internal int PidBefore=4242, PidAfter=4242, Session=0;
        internal long BirthBefore=700, BirthAfter=700;
        internal bool Primary=true, Impersonated=false, Restricted=true, Immutable=true, Provenance=true,
            ObserverImpersonated=false;
        internal int PreCode=1060, StartReturn=0, Running=4, Stopped=1, DeleteReturn=0, PostCode=1060;
        internal bool Agree=true, Closed=true, Exited=true, ChildrenAbsent=true, Late=false,
            Receipts=true, EarlierFailure=false;
        internal PlannedEvidence[] Evidence;
        internal RequiredApproval[] Approvals;
        internal SourceExpectation[] Sources;
        internal Builder()
        {
            Run="synthetic-run-"+(++serial);
            int count=Enum.GetValues(typeof(EvidenceKind)).Length;
            Evidence=new PlannedEvidence[count];
            for (int i=0;i<count;i++) Evidence[i]=MakeEvidence(i);
            Approvals=new RequiredApproval[7];
            for (int i=0;i<7;i++)
                Approvals[i]=new RequiredApproval((ApprovalRole)i,"external-decision-required-"+i,true,true);
            Sources=new[] {
                new SourceExpectation(P295PreflightContract.CandidatePath,new string('b',64)),
                new SourceExpectation(P295PreflightContract.ContractPath,new string('c',64)),
                new SourceExpectation(P295PreflightContract.TestsPath,new string('d',64)) };
        }
        internal PlannedEvidence MakeEvidence(int i, EvidenceSource? source=null,
            string collector=null, string run=null, string instance=null, string capture=null,
            int? ordinal=null, bool synthetic=true, bool receipt=true, bool onFailure=true)
        {
            EvidenceSource origin=source ?? P295PreflightContract.RequiredSource((EvidenceKind)i);
            return new PlannedEvidence((EvidenceKind)i,origin,collector ?? "collector-"+origin,
                run ?? Run,instance ?? Instance,capture ?? "synthetic-capture-"+i,
                ordinal ?? i+1,synthetic,receipt,onFailure);
        }
        internal ProposedPlan Build()
        {
            return new ProposedPlan(Parent,Run,Instance,InstanceCount,Offline,Authority,Retry,
                new StartupFixture(Dispatcher,Entered,Completed,Lookup,Disposed,Swallowed,PreFlag,
                    Verified,FrameworkExit,DeadlineMs,TimerFired,ExternalExit),
                new TokenFixture(Expected,Principal,Sid,ImageBefore,ImageAfter,TokenBefore,TokenAfter,
                    HandleBefore,HandleAfter,PidBefore,PidAfter,BirthBefore,BirthAfter,Session,
                    Primary,Impersonated,Restricted,Immutable,Provenance,AuthenticationBefore,
                    AuthenticationAfter,ModifiedBefore,ModifiedAfter,RunnerPrincipal,ObserverImpersonated),
                new CleanupFixture(PreCode,StartReturn,Running,Stopped,DeleteReturn,PostCode,
                    Agree,Closed,Exited,ChildrenAbsent,Late,Receipts,EarlierFailure),
                Evidence,Approvals,Sources);
        }
    }
    private static void Assert(bool value)
    {
        assertions++;
        if (!value) throw new InvalidOperationException("SYNTHETIC_ASSERTION_FAILED");
    }
    private static void Denials(P295PreflightContract g)
    {
        Assert(!g.RuntimeAuthorized); Assert(!g.RealKeyAllowed); Assert(!g.ProductionAllowed);
        Assert(!g.ApprovedProvenance); Assert(g.AcceptedExternalApprovals==0);
        Assert(g.AcceptedProductRegressions==0);
    }
    private static void Case(string name, Action test)
    {
        test(); cases++; Console.WriteLine("CASE="+name+" SYNTHETIC_CHECK=PASS");
    }
    private static void Reject(string name, Action<Builder> mutate)
    {
        Case(name,delegate {
            var b=new Builder(); var g=new P295PreflightContract();
            Assert(g.Result==PrecheckOutcome.PRECHECK); Denials(g);
            mutate(b); Assert(g.Review(b.Build())==PrecheckOutcome.HOLD); Denials(g);
            // A complete later fixture cannot clear the first failure, even on another checker.
            var repaired=new Builder(); repaired.Run=b.Run;
            for (int i=0;i<repaired.Evidence.Length;i++) repaired.Evidence[i]=repaired.MakeEvidence(i);
            Assert(g.Review(repaired.Build())==PrecheckOutcome.HOLD); Denials(g);
            var other=new P295PreflightContract();
            Assert(other.Review(repaired.Build())==PrecheckOutcome.HOLD); Denials(other);
        });
    }
    private static void Missing(string name, EvidenceKind kind)
    {
        Reject(name,b=>b.Evidence[(int)kind]=null);
    }
    private static int Main()
    {
        try
        {
            Case("COHERENT_SYNTHETIC_PLAN_ONLY",delegate {
                var b=new Builder(); var g=new P295PreflightContract();
                Assert(g.Result==PrecheckOutcome.PRECHECK); Denials(g);
                ProposedPlan snapshot=b.Build();
                // Constructor snapshots arrays; mutating the builder cannot rewrite the plan.
                b.Evidence[0]=null; b.Approvals[0]=null; b.Sources[0]=null;
                Assert(g.Review(snapshot)==PrecheckOutcome.PLAN_ONLY); Denials(g);
                Assert(g.Result==PrecheckOutcome.PLAN_ONLY);
                Assert(g.Review(snapshot)==PrecheckOutcome.HOLD); Denials(g);
                var replay=new P295PreflightContract();
                Assert(replay.Review(snapshot)==PrecheckOutcome.HOLD); Denials(replay);
            });
            Reject("FAILED_ONSTART",b=>b.Completed=false);
            Reject("MISSING_ONSTART",b=>b.Entered=false);
            Reject("FRAMEWORK_SWALLOWED_START_ERROR",b=> { b.Swallowed=true; b.FrameworkExit=0; });
            Reject("FALSE_PRE_ONSTART_FLAG",b=>b.PreFlag=true);
            Reject("NO_VERIFIED_POST_DISPOSAL_FLAG",b=>b.Verified=false);
            Reject("LSA_LOOKUP_FAILURE",b=>b.Lookup=false);
            Reject("IDENTITY_DISPOSAL_FAILURE",b=>b.Disposed=false);
            Reject("MANAGED_TIMER_NOT_FIRED",b=>b.TimerFired=false);
            Reject("NO_INDEPENDENT_DEADLINE_EXIT",b=>b.ExternalExit=false);
            Reject("EXTENDED_55_SECOND_TIMER",b=>b.DeadlineMs=55001);
            Reject("NO_DISPATCHER_REGISTRATION",b=>b.Dispatcher=false);
            Reject("NONZERO_FRAMEWORK_EXIT",b=>b.FrameworkExit=1);
            Reject("WRONG_TOKEN_PRINCIPAL",b=>b.Principal="other");
            Reject("LOCALSYSTEM_TOKEN",b=> { b.Expected="S-1-5-18"; b.Principal=b.Expected; b.Sid=b.Expected; });
            Reject("LOCALSYSTEM_ALIAS",b=> { b.Expected="LocalSystem"; b.Principal=b.Expected; b.Sid=b.Expected; });
            Reject("IMPERSONATED_TOKEN",b=>b.Impersonated=true);
            Reject("NONPRIMARY_TOKEN",b=>b.Primary=false);
            Reject("NONZERO_TOKEN_SESSION",b=>b.Session=1);
            Reject("MISSING_ACTUAL_RESTRICTED_SID_PROOF",b=>b.Restricted=false);
            Reject("RESTRICTED_SID_MISMATCH",b=>b.Sid="other");
            Reject("MUTABLE_IMAGE",b=>b.Immutable=false);
            Reject("MISSING_INSTALLED_PROVENANCE_REVIEW",b=>b.Provenance=false);
            Reject("IMAGE_HASH_DRIFT",b=>b.ImageAfter=new string('e',64));
            Reject("PID_DRIFT",b=>b.PidAfter++);
            Reject("ZERO_PID",b=> { b.PidBefore=0; b.PidAfter=0; });
            Reject("BIRTH_DRIFT",b=>b.BirthAfter++);
            Reject("MISSING_BIRTH",b=> { b.BirthBefore=0; b.BirthAfter=0; });
            Reject("TOKEN_DRIFT",b=>b.TokenAfter="other");
            Reject("AUTHENTICATION_ID_DRIFT",b=>b.AuthenticationAfter="other");
            Reject("TOKEN_MODIFIED_ID_DRIFT",b=>b.ModifiedAfter="other");
            Reject("RUNNER_TOKEN_SUBSTITUTION",b=>b.RunnerPrincipal=b.Principal);
            Reject("IMPERSONATED_INDEPENDENT_OBSERVER",b=>b.ObserverImpersonated=true);
            Reject("REOPENED_RETAINED_HANDLE",b=>b.HandleAfter="other");
            Reject("SPOOFED_SELF_REPORTED_EVIDENCE",b=>b.Evidence[0]=b.MakeEvidence(0,EvidenceSource.SelfReport));
            Reject("WRONG_EVIDENCE_SOURCE",b=>b.Evidence[0]=b.MakeEvidence(0,EvidenceSource.CimObserver));
            Reject("SHARED_TOKEN_AND_STARTUP_COLLECTOR",b=>b.Evidence[11]=b.MakeEvidence(11,
                collector:"collector-StartupObserver"));
            Reject("COLLECTOR_DRIFT",b=>b.Evidence[1]=b.MakeEvidence(1,collector:"other"));
            Reject("DUPLICATE_CAPTURE_REPLAY",b=>b.Evidence[12]=b.MakeEvidence(12,capture:"synthetic-capture-11"));
            Reject("WRONG_INSTANCE_BINDING",b=>b.Evidence[11]=b.MakeEvidence(11,instance:"other"));
            Reject("WRONG_RUN_BINDING",b=>b.Evidence[11]=b.MakeEvidence(11,run:"other"));
            Reject("OUT_OF_ORDER_RECEIPT",b=>b.Evidence[3]=b.MakeEvidence(3,ordinal:3));
            Reject("NON_SYNTHETIC_INPUT",b=>b.Evidence[0]=b.MakeEvidence(0,synthetic:false));
            Reject("CIM_NATIVE_DISAGREEMENT",b=>b.Agree=false);
            Reject("DELETE_ZERO_WITHOUT_NATIVE_1060",b=>b.PostCode=0);
            Reject("DELETE_1072_WITHOUT_NATIVE_1060",b=> { b.DeleteReturn=1072; b.PostCode=1072; });
            Reject("DELETE_ZERO_WITH_OPEN_HANDLES",b=>b.Closed=false);
            Reject("DELETE_1072_WITH_OPEN_HANDLES",b=> { b.DeleteReturn=1072; b.Closed=false; });
            Reject("NATIVE_1060_WITH_SURVIVING_RETAINED_CHILD",b=>b.Exited=false);
            Reject("SURVIVING_CHILD",b=>b.ChildrenAbsent=false);
            Reject("LATE_CHILD",b=>b.Late=true);
            Reject("INCOMPLETE_RECEIPTS",b=>b.Receipts=false);
            Reject("FAILURE_THEN_SUCCESS_REPLAY",b=>b.EarlierFailure=true);
            Reject("START_TIMEOUT_UNAVAILABLE",b=>b.StartReturn=-1);
            Reject("RUNNING_PID_FROM_PENDING_STATUS",b=>b.Running=2);
            Reject("STOP_NOT_CONFIRMED",b=>b.Stopped=3);
            Reject("DELETE_ACCESS_DENIED",b=>b.DeleteReturn=5);
            Reject("PRECREATE_NOT_ABSENT",b=>b.PreCode=1072);
            Reject("NATIVE_ABSENCE_QUERY_FAILURE",b=>b.PostCode=5);
            Reject("OPTIONAL_FAILURE_CLEANUP",b=>b.Evidence[18]=b.MakeEvidence(18,onFailure:false));
            Reject("OPTIONAL_RECEIPT",b=>b.Evidence[18]=b.MakeEvidence(18,receipt:false));
            Reject("INCOMPLETE_APPROVALS",b=>b.Approvals=new RequiredApproval[0]);
            Reject("DUPLICATE_APPROVAL_ROLE",b=>b.Approvals[6]=b.Approvals[0]);
            Reject("MISSING_EXTERNAL_SIGNOFF_SOURCE",b=>b.Approvals[2]=new RequiredApproval(ApprovalRole.SEC03,"",true,true));
            Reject("UNBOUND_APPROVAL_REQUIREMENT",b=>b.Approvals[2]=new RequiredApproval(ApprovalRole.SEC03,"external",false,true));
            Reject("RUNTIME_BEFORE_QUALIFIED_APPROVAL",b=>b.Approvals[2]=new RequiredApproval(ApprovalRole.SEC03,"external",true,false));
            Reject("TWO_INSTANCE_PLAN",b=>b.InstanceCount=2);
            Reject("MUTATION_RETRY_PLAN",b=>b.Retry=true);
            Reject("REQUESTED_RUNTIME_AUTHORITY",b=>b.Authority=true);
            Reject("NOT_OFFLINE_ONLY",b=>b.Offline=false);
            Reject("WRONG_PARENT",b=>b.Parent=new string('0',40));
            Reject("MISSING_SOURCE_EXPECTATIONS",b=>b.Sources=null);
            Reject("ZERO_SOURCE_HASH",b=>b.Sources[0]=new SourceExpectation(P295PreflightContract.CandidatePath,new string('0',64)));
            Reject("MALFORMED_SOURCE_HASH",b=>b.Sources[1]=new SourceExpectation(P295PreflightContract.ContractPath,"not-a-hash"));
            Reject("WRONG_SOURCE_PATH",b=>b.Sources[1]=new SourceExpectation("other",new string('c',64)));
            Missing("NO_STARTUP_EVIDENCE_SOURCE",EvidenceKind.OnStartCompletion);
            Missing("NO_TOKEN_EVIDENCE_SOURCE",EvidenceKind.KernelTokenOne);
            Missing("NO_SECOND_TOKEN_CAPTURE",EvidenceKind.KernelTokenTwo);
            Missing("NO_RESTRICTED_SID_SOURCE",EvidenceKind.ActualRestrictedSids);
            Missing("NO_IMAGE_PROVENANCE_SOURCE",EvidenceKind.ImageProvenance);
            Missing("NO_NATIVE_ABSENCE_SOURCE",EvidenceKind.NativePostDeleteAbsence);
            Missing("NO_CHILD_EXIT_SOURCE",EvidenceKind.ChildExit);
            Missing("NO_LATE_CHILD_SWEEP_SOURCE",EvidenceKind.LateChildSweep);
            Missing("NO_EXTERNAL_DEADLINE_SOURCE",EvidenceKind.IndependentDeadline);
            Case("NULL_PLAN_FAILS_CLOSED",delegate {
                var g=new P295PreflightContract();
                Assert(g.Review(null)==PrecheckOutcome.HOLD); Denials(g);
                Assert(g.Review(new Builder().Build())==PrecheckOutcome.HOLD); Denials(g);
            });
            Console.WriteLine("SYNTHETIC_CASES="+cases+" ASSERTIONS="+assertions+" RUNTIME_AUTHORIZED=0 APPROVALS=0/7 REGRESSIONS=0/3 DISPOSITION=HOLD");
            return 0;
        }
        catch (Exception)
        {
            Console.WriteLine("SYNTHETIC_TEST_FAILURE COMPLETED_CASES="+cases+" ASSERTIONS="+assertions+" DISPOSITION=HOLD");
            return 1;
        }
    }
}
#else
#error P295_DEBUG_ISOLATED_OFFLINE_ONLY_REQUIRED_RELEASE_FORBIDDEN
#endif
