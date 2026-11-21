#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P293_FAKE_WITNESS_ONLY && !RELEASE
using System;
using P293FakeDevelopment;

internal static class P293WitnessTests
{
    private static int serial, cases, assertions;
    private sealed class Builder
    {
        internal Episode Episode;
        internal Phase Kind;
        internal int Ordinal, Code, Pid;
        internal long Tick, Birth;
        internal Origin Origin;
        internal ServiceState State;
        internal string Name, Account, Image, Principal, Sid, Handle, Token, Capture;
        internal bool Restricted, Impersonating, Retained, Signaled, ScmClosed, ChildAbsent,
            TimedOut, AlternateEffectRoute, Revoked;
        internal Builder(Episode e, int i)
        {
            Episode=e; Kind=(Phase)i; Ordinal=i+1; Tick=100+i; Origin=Origin.FakeNative;
            Code=(i==0 || i==12) ? 1060 : 0;
            State=i>=9 ? ServiceState.Stopped : ServiceState.Running;
            Pid=i==9 ? 0 : 4242; Birth=700; Name=e.Name; Account=e.Account; Image=e.Image;
            Principal=e.Principal; Sid=e.Sid; Handle="fake-retained-handle";
            Token="fake-kernel-token"; Capture="fake-capture-"+i;
            Restricted=true; Impersonating=false; Retained=true; Signaled=i>=13;
            ScmClosed=i>=11; ChildAbsent=i>=14; TimedOut=false;
            AlternateEffectRoute=false; Revoked=false;
        }
        internal FakeObservation Build()
        {
            return new FakeObservation(Episode,Kind,Ordinal,Tick,Origin,Code,State,Pid,Birth,
                Name,Account,Image,Principal,Sid,Handle,Token,Capture,Restricted,Impersonating,
                Retained,Signaled,ScmClosed,ChildAbsent,TimedOut,AlternateEffectRoute,Revoked);
        }
    }
    private static Episode Identity()
    {
        serial++;
        return new Episode("fake-session-"+serial,"FakeP293","fake-boot",serial,"fake-source",
            "fake-nonce-"+serial,@"C:\FakeProtected\P293.exe",@"NT SERVICE\FakeP293",
            "S-1-5-80-123-456-789-101-112","S-1-5-80-123-456-789-101-112");
    }
    private static Episode Copy(Episode e, string session, string name, string boot, long gen,
        string source, string nonce)
    {
        return new Episode(session,name,boot,gen,source,nonce,e.Image,e.Account,e.Principal,e.Sid);
    }
    private static void Assert(bool condition)
    {
        assertions++; if (!condition) throw new InvalidOperationException("FAKE_ASSERTION");
    }
    private static void Denied(P293NonDeployableScmWitnessGate g)
    {
        Assert(!g.ClientAdmissionAllowed()); Assert(!g.CredentialEffectAllowed());
        Assert(!g.ApprovedServiceProvenance()); Assert(!g.ProductionReleaseAllowed());
    }
    private static void Prefix(P293NonDeployableScmWitnessGate g, Episode e, int count)
    {
        for (int i=0;i<count;i++)
        {
            Assert(g.NextPhase==(Phase)i);
            Assert(g.Observe(new Builder(e,i).Build())==Outcome.InProgress);
            Denied(g);
        }
    }
    private static void Refused(P293NonDeployableScmWitnessGate g, Outcome expected)
    {
        Assert(g.Result==expected); Denied(g);
        Assert(g.Finish()==expected);
        Assert(g.Observe(null)==expected); Denied(g);
    }
    private static void Case(string name, Action body)
    {
        body(); cases++; Console.WriteLine("CASE="+name+" RESULT=PASS");
    }
    private static void Mutation(string name, int index, Action<Builder> change)
    {
        Case(name,delegate {
            Episode e=Identity(); var g=new P293NonDeployableScmWitnessGate(e);
            Prefix(g,e,index); var b=new Builder(e,index); change(b);
            Outcome expected=index>=1 ? Outcome.RecoveryRequired : Outcome.Hold;
            Assert(g.Observe(b.Build())==expected); Refused(g,expected);
            // A later fully matching event cannot erase the original failure.
            Assert(g.Observe(new Builder(e,index).Build())==expected); Denied(g);
        });
    }
    private static void Missing(string name, int count)
    {
        Case(name,delegate {
            Episode e=Identity(); var g=new P293NonDeployableScmWitnessGate(e);
            Prefix(g,e,count);
            Assert(g.Finish()==(count>=2 ? Outcome.RecoveryRequired : Outcome.Hold));
            Refused(g,count>=2 ? Outcome.RecoveryRequired : Outcome.Hold);
        });
    }
    private static int Main()
    {
        // Author may compile on Kristian, but this entrypoint runs ONLY on disposable hosted jobs.
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS")!="true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT")!="github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS")!="Windows" ||
            Environment.GetEnvironmentVariable("ImageOS")!="win22" ||
            Environment.GetEnvironmentVariable("P293_FAKE_WITNESS_ONLY")!="1" ||
            Environment.GetEnvironmentVariable("REVIEW_ARCH")!=(IntPtr.Size==8 ? "x64" : "x86")) return 9;
        try
        {
            Case("COHERENT_FAKE_SEQUENCE",delegate {
                Episode e=Identity(); var g=new P293NonDeployableScmWitnessGate(e);
                Prefix(g,e,14); Assert(g.NextPhase==Phase.ExactImageChildAbsent);
                Assert(g.Observe(new Builder(e,14).Build())==Outcome.FakeDevelopmentSequenceCoherent);
                Assert(g.NextPhase==Phase.Complete); Denied(g);
                Assert(g.Finish()==Outcome.FakeDevelopmentSequenceCoherent); Denied(g);
            });
            Mutation("PRE_ABSENCE_1072",0,b=>b.Code=1072);
            Mutation("PRE_ABSENCE_ZERO",0,b=>b.Code=0);
            Mutation("PRE_ABSENCE_ACCESS_DENIED",0,b=>b.Code=5);
            Mutation("PRE_ABSENCE_CIM",0,b=>b.Origin=Origin.FakeCim);
            Mutation("PRE_ABSENCE_UNKNOWN_SOURCE",0,b=>b.Origin=Origin.Unknown);
            Mutation("PRE_ABSENCE_TIMEOUT",0,b=>b.TimedOut=true);
            Mutation("CREATE_ERROR",1,b=>b.Code=5);
            Mutation("CREATE_TIMEOUT",1,b=>b.TimedOut=true);
            Mutation("CONFIG_QUERY_ERROR",2,b=>b.Code=5);
            Mutation("CONFIG_WRONG_NAME",2,b=>b.Name="other");
            Mutation("CONFIG_LOCAL_SYSTEM",2,b=>b.Account="LocalSystem");
            Mutation("CONFIG_NEXT_RUN_IMAGE",2,b=>b.Image="next-run.exe");
            Mutation("CONFIG_UNRESTRICTED",2,b=>b.Restricted=false);
            Mutation("START_1053",3,b=>b.Code=1053);
            Mutation("START_1069",3,b=>b.Code=1069);
            Mutation("START_TIMEOUT",3,b=>b.TimedOut=true);
            Mutation("RUNNING_QUERY_ERROR",4,b=>b.Code=5);
            Mutation("RUNNING_PID_ZERO",4,b=>b.Pid=0);
            Mutation("RUNNING_PID_NEGATIVE",4,b=>b.Pid=-1);
            Mutation("RUNNING_START_PENDING",4,b=>b.State=ServiceState.StartPending);
            Mutation("RUNNING_STOP_PENDING",4,b=>b.State=ServiceState.StopPending);
            Mutation("RUNNING_STOPPED",4,b=>b.State=ServiceState.Stopped);
            Mutation("RUNNING_UNKNOWN",4,b=>b.State=ServiceState.Unknown);
            Mutation("HANDLE_PID_ABA",5,b=>b.Pid=4243);
            Mutation("HANDLE_MISSING",5,b=>b.Handle=null);
            Mutation("HANDLE_NOT_RETAINED",5,b=>b.Retained=false);
            Mutation("HANDLE_MISSING_BIRTH",5,b=>b.Birth=0);
            Mutation("HANDLE_ALREADY_SIGNALED",5,b=>b.Signaled=true);
            Mutation("TOKEN_ONE_NEW_BIRTH",6,b=>b.Birth=701);
            Mutation("TOKEN_ONE_WRONG_IMAGE",6,b=>b.Image="wrong.exe");
            Mutation("TOKEN_ONE_WRONG_PRINCIPAL",6,b=>b.Principal="S-1-5-18");
            Mutation("TOKEN_ONE_WRONG_SID",6,b=>b.Sid="other");
            Mutation("TOKEN_ONE_UNRESTRICTED",6,b=>b.Restricted=false);
            Mutation("TOKEN_ONE_IMPERSONATING",6,b=>b.Impersonating=true);
            Mutation("TOKEN_ONE_NO_KERNEL_TOKEN",6,b=>b.Token=null);
            Mutation("TOKEN_ONE_NO_CAPTURE",6,b=>b.Capture=null);
            Mutation("TOKEN_TWO_NEW_BIRTH",7,b=>b.Birth=701);
            Mutation("TOKEN_TWO_NEW_PID",7,b=>b.Pid=4243);
            Mutation("TOKEN_TWO_NEW_HANDLE",7,b=>b.Handle="reopened");
            Mutation("TOKEN_TWO_MIXED_TOKEN",7,b=>b.Token="other-instance-token");
            Mutation("TOKEN_TWO_DUPLICATE_CAPTURE",7,b=>b.Capture="fake-capture-6");
            Mutation("TOKEN_TWO_IMPERSONATING",7,b=>b.Impersonating=true);
            Mutation("TOKEN_TWO_UNRESTRICTED",7,b=>b.Restricted=false);
            Mutation("TOKEN_TWO_WRONG_PRINCIPAL",7,b=>b.Principal="S-1-5-18");
            Mutation("TOKEN_TWO_WRONG_IMAGE",7,b=>b.Image="next-run.exe");
            Mutation("TOKEN_TWO_LOST_HANDLE",7,b=>b.Retained=false);
            Mutation("STOP_ERROR",8,b=>b.Code=1062);
            Mutation("STOP_NEW_BIRTH",8,b=>b.Birth=701);
            Mutation("STOPPED_STILL_PENDING",9,b=>b.State=ServiceState.StopPending);
            Mutation("STOPPED_PID_USED",9,b=>b.Pid=4242);
            Mutation("STOPPED_LOST_HANDLE",9,b=>b.Retained=false);
            Mutation("DELETE_1072",10,b=>b.Code=1072);
            Mutation("DELETE_QUERY_ERROR",10,b=>b.Code=5);
            Mutation("SCM_HANDLES_OPEN",11,b=>b.ScmClosed=false);
            Mutation("POST_ABSENCE_1072",12,b=>b.Code=1072);
            Mutation("POST_ABSENCE_ZERO",12,b=>b.Code=0);
            Mutation("POST_ABSENCE_CIM_ONLY",12,b=>b.Origin=Origin.FakeCim);
            Mutation("POST_NATIVE_QUERY_TIMEOUT",12,b=>b.TimedOut=true);
            Mutation("POST_NATIVE_QUERY_ERROR",12,b=>b.Code=5);
            Mutation("POST_ABSENCE_NO_RETAINED_HANDLE",12,b=>b.Retained=false);
            Mutation("RETAINED_PROCESS_ALIVE",13,b=>b.Signaled=false);
            Mutation("RETAINED_PROCESS_NEW_BIRTH",13,b=>b.Birth=701);
            Mutation("RETAINED_PROCESS_NEW_HANDLE",13,b=>b.Handle="reopened");
            Mutation("CHILD_ALIVE_AFTER_DELETE",14,b=>b.ChildAbsent=false);
            Mutation("NEW_PROCESS_FOUND",14,b=>b.Pid=4243);
            Mutation("CHILD_QUERY_TIMEOUT",14,b=>b.TimedOut=true);
            Mutation("CHILD_WRONG_IMAGE_SCOPE",14,b=>b.Image="different.exe");
            Mutation("CHILD_NO_EXACT_HANDLE",14,b=>b.Handle=null);
            Mutation("STALE_TICK",7,b=>b.Tick=106);
            Mutation("BACKWARDS_TICK",7,b=>b.Tick=1);
            Mutation("ZERO_TICK",0,b=>b.Tick=0);
            Mutation("OBSERVATION_GAP",7,b=>b.Tick=117);
            Mutation("ORDINAL_DUPLICATE",7,b=>b.Ordinal=7);
            Mutation("ORDINAL_GAP",7,b=>b.Ordinal=9);
            Mutation("WRONG_PHASE_REPLAY",7,b=>b.Kind=Phase.KernelTokenOne);
            Mutation("UNKNOWN_PHASE",7,b=>b.Kind=(Phase)999);
            Mutation("NULL_EPISODE",7,b=>b.Episode=null);
            Mutation("SESSION_DRIFT",7,b=>b.Episode=Copy(b.Episode,"other",b.Episode.Name,b.Episode.Boot,b.Episode.Generation,b.Episode.Source,b.Episode.Nonce));
            Mutation("NAME_DRIFT",7,b=>b.Episode=Copy(b.Episode,b.Episode.Session,"other",b.Episode.Boot,b.Episode.Generation,b.Episode.Source,b.Episode.Nonce));
            Mutation("BOOT_DRIFT",7,b=>b.Episode=Copy(b.Episode,b.Episode.Session,b.Episode.Name,"other",b.Episode.Generation,b.Episode.Source,b.Episode.Nonce));
            Mutation("GENERATION_DRIFT",7,b=>b.Episode=Copy(b.Episode,b.Episode.Session,b.Episode.Name,b.Episode.Boot,9999,b.Episode.Source,b.Episode.Nonce));
            Mutation("SOURCE_DRIFT",7,b=>b.Episode=Copy(b.Episode,b.Episode.Session,b.Episode.Name,b.Episode.Boot,b.Episode.Generation,"other",b.Episode.Nonce));
            Mutation("NONCE_DRIFT",7,b=>b.Episode=Copy(b.Episode,b.Episode.Session,b.Episode.Name,b.Episode.Boot,b.Episode.Generation,b.Episode.Source,"other"));
            Mutation("ALTERNATE_LIVE_EFFECT_ROUTE",7,b=>b.AlternateEffectRoute=true);
            Mutation("REVOCATION_EFFECT_RACE",7,b=>b.Revoked=true);
            Mutation("LATE_REVOCATION",14,b=>b.Revoked=true);
            Missing("MISSING_ALL",0);
            Missing("MISSING_CREATE",1);
            Missing("MISSING_CONFIG",2);
            Missing("MISSING_START",3);
            Missing("MISSING_RUNNING",4);
            Missing("MISSING_HANDLE",5);
            Missing("MISSING_TOKEN_ONE",6);
            Missing("MISSING_TOKEN_TWO",7);
            Missing("MISSING_STOP",8);
            Missing("MISSING_STOPPED",9);
            Missing("MISSING_DELETE",10);
            Missing("DELETE_ZERO_IS_NOT_ABSENCE",11);
            Missing("MISSING_NATIVE_POST_ABSENCE",12);
            Missing("MISSING_SIGNALED_HANDLE",13);
            Missing("MISSING_CHILD_ABSENCE",14);
            Case("CROSS_INSTANCE_EPISODE_REPLAY",delegate {
                Episode e=Identity(); var first=new P293NonDeployableScmWitnessGate(e);
                Prefix(first,e,7); var replay=new P293NonDeployableScmWitnessGate(e);
                Refused(replay,Outcome.Hold); Denied(first);
            });
            Case("CROSS_INSTANCE_NONCE_REPLAY",delegate {
                Episode e=Identity(); var first=new P293NonDeployableScmWitnessGate(e);
                Episode other=Copy(e,"different",e.Name,e.Boot,9999,e.Source,e.Nonce);
                Refused(new P293NonDeployableScmWitnessGate(other),Outcome.Hold); Denied(first);
            });
            Case("CROSS_INSTANCE_EPISODE_NEW_NONCE",delegate {
                Episode e=Identity(); var first=new P293NonDeployableScmWitnessGate(e);
                Episode other=Copy(e,e.Session,e.Name,e.Boot,e.Generation,e.Source,"fresh-nonce");
                Refused(new P293NonDeployableScmWitnessGate(other),Outcome.Hold); Denied(first);
            });
            Case("TOTAL_OBSERVATION_BUDGET",delegate {
                Episode e=Identity(); var g=new P293NonDeployableScmWitnessGate(e);
                for (int i=0;i<15;i++)
                {
                    var b=new Builder(e,i); b.Tick=100+i*9;
                    Assert(g.Observe(b.Build())==(i==14 ? Outcome.RecoveryRequired : Outcome.InProgress));
                    Denied(g);
                }
                Refused(g,Outcome.RecoveryRequired);
            });
            Case("CROSS_INSTANCE_MIXED_EVENTS",delegate {
                Episode a=Identity(), b=Identity(); var g=new P293NonDeployableScmWitnessGate(a);
                Prefix(g,a,7); Assert(g.Observe(new Builder(b,7).Build())==Outcome.RecoveryRequired);
                Refused(g,Outcome.RecoveryRequired);
            });
            Case("NULL_IDENTITY",delegate { Refused(new P293NonDeployableScmWitnessGate(null),Outcome.Hold); });
            Case("NULL_EVENT",delegate {
                var g=new P293NonDeployableScmWitnessGate(Identity());
                Assert(g.Observe(null)==Outcome.Hold); Refused(g,Outcome.Hold);
            });
            Case("INVALID_IDENTITY",delegate {
                Episode e=Identity(); Episode bad=Copy(e,"",e.Name,e.Boot,0,e.Source,e.Nonce);
                Refused(new P293NonDeployableScmWitnessGate(bad),Outcome.Hold);
            });
            Case("REPLAY_AFTER_COHERENCE",delegate {
                Episode e=Identity(); var g=new P293NonDeployableScmWitnessGate(e);
                Prefix(g,e,14); Assert(g.Observe(new Builder(e,14).Build())==Outcome.FakeDevelopmentSequenceCoherent);
                Denied(g); Assert(g.Observe(new Builder(e,14).Build())==Outcome.RecoveryRequired);
                Refused(g,Outcome.RecoveryRequired);
            });
            Assert(cases>=40); Assert(assertions>=1000);
            Console.WriteLine("SUMMARY CASES="+cases+" ASSERTIONS="+assertions+" FAKE_ONLY=1 PRODUCTION_ALLOWED=0");
            return 0;
        }
        catch { Console.WriteLine("FAKE_TEST_FAILURE"); return 1; }
    }
}
#else
#error P293_DEBUG_ISOLATED_FAKE_WITNESS_ONLY_REQUIRED
#endif
