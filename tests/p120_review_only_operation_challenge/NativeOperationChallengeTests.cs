// P120 isolated review-only proof of one-use operation-bound CSPRNG
// echo transcript semantics. Echo is not actual human approval.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P120 test driver is never valid in an ordinary product build
#endif
using System;
using System.Threading;
using Nayeon.ByokC1;

internal static class P120NativeOperationChallengeTests
{
    private static int passed, failed;
    private static readonly long Now =
        new DateTime(2026,11,9,13,0,0,DateTimeKind.Utc).Ticks;
    private static readonly string Peer = new string('b',64);
    private static readonly string Sid = new string('a',32);
    private static readonly string Rid = new string('c',32);
    private static readonly string Digest = new string('d',64);

    private static void Need(bool result,string why)
    {if(!result)throw new InvalidOperationException("P120 "+why);}
    private static void Run(string label,Action test)
    {
        try{test();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception ex)
        {++failed;Console.WriteLine("FAIL "+label+" "+ex.GetType().Name);}
    }
    private static ServiceBoundRequestIdentity Req(
        LedgerOperation op=LedgerOperation.Save,
        string sid=null,string rid=null,string digest=null,long exp=0)
    {
        bool delete=op==LedgerOperation.Delete;
        return new ServiceBoundRequestIdentity(op,sid??Sid,rid??Rid,
            delete?null:(digest??Digest),
            exp==0?Now+TimeSpan.TicksPerSecond*45:exp,delete);
    }
    private static ReviewOnlyOperationChallenge Issue(
        ServiceBoundRequestIdentity request=null,
        string peer=null,Func<long> now=null)
    {
        var ch=ReviewOnlyOperationChallenge.TryIssue(
            request??Req(),peer??Peer,now??(()=>Now));
        Need(ch!=null,"review-only challenge issued");
        return ch;
    }
    private static void NoAuthority(ReviewOnlyOperationChallenge c)
    {
        Need(c!=null,"model exists");
        Need(!c.AuthenticatedServiceListenerInstalled,
            "no installed authenticated service");
        Need(!c.ApprovedSignedConsentBrokerVerified,
            "no signed approved consent app");
        Need(!c.TrustedHumanInteractionVerified,"no human approval");
        Need(!c.ProtectedDurableGrantIssued,"no durable grant");
        Need(!c.NativeCredentialEffectAllowed,"no native credential effect");
        Need(!c.ToString().Contains(Sid),"no account-like id leak");
        Need(!c.ToString().Contains(Rid),"no request id leak");
        Need(!c.ToString().Contains(Digest),"no request digest leak");
        Need(!c.ToString().Contains(Peer),"no peer fingerprint leak");
    }
    private static void MustEchoOnly(ReviewOnlyOperationChallenge c,
        ServiceBoundRequestIdentity request)
    {
        byte[] nonce=c.GetChallengeCopy();
        Need(nonce!=null&&nonce.Length==32,"fresh challenge");
        var outcome=c.ObserveEchoAndTerminate(request,Peer,nonce);
        Need(outcome==ReviewOnlyChallengeVerdict.EchoMatchedWithoutConsentAuthority,
            "echo is matched but not approved");
        Need(c.DiagnosticEchoObserved&&c.Terminal,"one observation terminal");
        Need(c.GetChallengeCopy()==null && c.GetBindingDigestCopy()==null,
            "no challenge after terminal");
        NoAuthority(c);
    }
    private static void WrongBindingSticky(
        ServiceBoundRequestIdentity bad,string peer=null,byte[] nonce=null)
    {
        var req=Req();
        var ch=Issue(req);
        var value=nonce??ch.GetChallengeCopy();
        Need(ch.ObserveEchoAndTerminate(bad,peer??Peer,value)==
            ReviewOnlyChallengeVerdict.Refused,"wrong binding denied");
        Need(ch.Terminal&&!ch.DiagnosticEchoObserved,"sticky denial");
        Need(ch.ObserveEchoAndTerminate(req,Peer,value)==
            ReviewOnlyChallengeVerdict.Refused,"no retry after refusal");
        NoAuthority(ch);
    }
    private static bool Same(byte[] a,byte[] b)
    {
        if(a==null||b==null||a.Length!=b.Length)return false;
        for(int i=0;i<a.Length;i++)if(a[i]!=b[i])return false;
        return true;
    }

    public static int Main()
    {
        Run("null-untrusted-request-refused",()=>
        {
            Need(ReviewOnlyOperationChallenge.TryIssue(null,Peer,()=>Now)==null,
                "null input");
        });
        Run("bad-untrusted-peer-claim-refused",()=>
        {
            Need(ReviewOnlyOperationChallenge.TryIssue(
                Req(),"claimed-pid",()=>Now)==null,"invalid peer encoding");
        });
        Run("expired-request-refused-at-issue",()=>
        {
            Need(ReviewOnlyOperationChallenge.TryIssue(
                Req(exp:Now-TimeSpan.TicksPerSecond),Peer,()=>Now)==null,
                "stale request");
        });
        Run("overlong-request-window-refused-at-issue",()=>
        {
            Need(ReviewOnlyOperationChallenge.TryIssue(
                Req(exp:Now+TimeSpan.TicksPerMinute*6),
                Peer,()=>Now)==null,"overlong TTL");
        });
        Run("missing-synthetic-clock-refused",()=>
        {
            Need(ReviewOnlyOperationChallenge.TryIssue(
                Req(),Peer,null)==null,"clock required");
        });
        Run("throwing-clock-refused-at-issue",()=>
        {
            Need(ReviewOnlyOperationChallenge.TryIssue(
                Req(),Peer,()=>{throw new InvalidOperationException();})==null,
                "clock fault");
        });
        Run("fresh-256-bit-cryptographic-nonces-distinct",()=>
        {
            var a=Issue();var b=Issue();
            Need(a.GetChallengeCopy().Length==32 &&
                b.GetChallengeCopy().Length==32 &&
                !Same(a.GetChallengeCopy(),b.GetChallengeCopy()),
                "CSPRNG outputs distinct");
            NoAuthority(a);NoAuthority(b);
        });
        Run("nonce-exposure-is-defensive-copy",()=>
        {
            var req=Req();var c=Issue(req);
            byte[] exposed=c.GetChallengeCopy();
            exposed[0]^=0xff;
            Need(!Same(exposed,c.GetChallengeCopy()),
                "cannot change internal nonce");
            MustEchoOnly(c,req);
        });
        Run("digest-exposure-is-defensive-copy",()=>
        {
            var c=Issue();
            byte[] exposed=c.GetBindingDigestCopy();
            Need(exposed.Length==32,"SHA256 digest");
            exposed[0]^=0xff;
            Need(!Same(exposed,c.GetBindingDigestCopy()),
                "immutable canonical digest");
            NoAuthority(c);
        });
        Run("valid-echo-is-diagnostic-NOT-human-consent",()=>
        {
            var req=Req();MustEchoOnly(Issue(req),req);
        });
        Run("exact-echo-replay-rejected",()=>
        {
            var req=Req();var c=Issue(req);var bytes=c.GetChallengeCopy();
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.EchoMatchedWithoutConsentAuthority,
                "first echo observed");
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.Refused,"second refused");
            NoAuthority(c);
        });
        Run("incorrect-nonce-burns-attempt",()=>
        {
            var req=Req();var c=Issue(req);var bytes=c.GetChallengeCopy();
            bytes[0]^=0xff;
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.Refused,"bad nonce");
            Need(c.Terminal&&!c.DiagnosticEchoObserved,"sticky");
            NoAuthority(c);
        });
        Run("incorrect-peer-claim-burns-attempt",()=>
        {
            WrongBindingSticky(Req(),new string('e',64));
        });
        Run("changed-session-ID-burns-attempt",()=>
        {
            WrongBindingSticky(Req(sid:new string('e',32)));
        });
        Run("changed-request-ID-burns-attempt",()=>
        {
            WrongBindingSticky(Req(rid:new string('e',32)));
        });
        Run("changed-candidate-hash-burns-attempt",()=>
        {
            WrongBindingSticky(Req(digest:new string('f',64)));
        });
        Run("changed-operation-burns-attempt",()=>
        {
            WrongBindingSticky(Req(op:LedgerOperation.Replace));
        });
        Run("changed-expiry-burns-attempt",()=>
        {
            WrongBindingSticky(Req(exp:Now+TimeSpan.TicksPerSecond*40));
        });
        Run("expired-echo-terminally-refused",()=>
        {
            long current=Now;
            var req=Req(exp:Now+TimeSpan.TicksPerSecond);
            var c=Issue(req,Peer,()=>current);
            var bytes=c.GetChallengeCopy();
            current=Now+TimeSpan.TicksPerSecond;
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.Refused,"expiry precise");
            Need(c.Terminal&&!c.DiagnosticEchoObserved,"not approvable");
            NoAuthority(c);
        });
        Run("clock-rollback-refused",()=>
        {
            long current=Now;var req=Req();var c=Issue(req,Peer,()=>current);
            current=Now-TimeSpan.TicksPerSecond;
            Need(c.ObserveEchoAndTerminate(req,Peer,c.GetChallengeCopy())==
                ReviewOnlyChallengeVerdict.Refused,"time rollback");
            NoAuthority(c);
        });
        Run("revocation-before-echo-sticky",()=>
        {
            var req=Req();var c=Issue(req);var bytes=c.GetChallengeCopy();
            Need(c.RevokeBeforeEcho(),"initial revoke");
            Need(!c.RevokeBeforeEcho(),"no duplicate revoke");
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.Refused,"revoke beats echo");
            NoAuthority(c);
        });
        Run("fault-before-echo-sticky",()=>
        {
            var req=Req();var c=Issue(req);var bytes=c.GetChallengeCopy();
            Need(c.FailClosedFault(),"fault first");
            Need(!c.FailClosedFault(),"no second transition");
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.Refused,"fault prohibits echo");
            NoAuthority(c);
        });
        Run("clock-exception-at-echo-burns-attempt",()=>
        {
            bool shouldThrow=false;
            var req=Req();var c=Issue(req,Peer,()=>{
                if(shouldThrow)throw new InvalidOperationException();
                return Now;
            });
            var bytes=c.GetChallengeCopy();
            shouldThrow=true;
            Need(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                ReviewOnlyChallengeVerdict.Refused,"clock fault denied");
            Need(c.Terminal,"failure terminal");
            NoAuthority(c);
        });
        Run("sixteen-simultaneous-echoes-one-diagnostic",()=>
        {
            var req=Req();var c=Issue(req);var bytes=c.GetChallengeCopy();
            using(var ready=new ManualResetEvent(false))
            {
                var workers=new Thread[16];int winners=0;int errors=0;
                for(int i=0;i<workers.Length;i++)
                {
                    workers[i]=new Thread(()=>{
                        try
                        {
                            ready.WaitOne();
                            if(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                                ReviewOnlyChallengeVerdict.EchoMatchedWithoutConsentAuthority)
                                Interlocked.Increment(ref winners);
                        }
                        catch(Exception){Interlocked.Increment(ref errors);}
                    });
                    workers[i].Start();
                }
                ready.Set();
                foreach(var worker in workers)
                    Need(worker.Join(5000),"all native worker threads joined");
                Need(errors==0&&winners==1&&c.DiagnosticEchoObserved,
                    "exactly one in-memory diagnostic echo");
                NoAuthority(c);
            }
        });
        Run("concurrent-revocation-versus-echo-linearizes",()=>
        {
            for(int i=0;i<64;i++)
            {
                var req=Req();var c=Issue(req);var bytes=c.GetChallengeCopy();
                using(var ready=new ManualResetEvent(false))
                {
                    int echoWon=0,revokeWon=0,errors=0;
                    var echo=new Thread(()=>{
                        try
                        {
                            ready.WaitOne();
                            if(c.ObserveEchoAndTerminate(req,Peer,bytes)==
                                ReviewOnlyChallengeVerdict.EchoMatchedWithoutConsentAuthority)
                                Interlocked.Increment(ref echoWon);
                        }
                        catch(Exception){Interlocked.Increment(ref errors);}
                    });
                    var revoke=new Thread(()=>{
                        try
                        {
                            ready.WaitOne();
                            if(c.RevokeBeforeEcho())
                                Interlocked.Increment(ref revokeWon);
                        }
                        catch(Exception){Interlocked.Increment(ref errors);}
                    });
                    echo.Start();revoke.Start();ready.Set();
                    Need(echo.Join(5000)&&revoke.Join(5000),"workers join");
                    Need(errors==0&&echoWon+revokeWon==1 &&
                        c.DiagnosticEchoObserved==(echoWon==1),
                        "one terminal outcome");
                    NoAuthority(c);
                }
            }
        });
        Run("delete-operation-cannot-be-reinterpreted-as-save",()=>
        {
            var req=Req(op:LedgerOperation.Delete);
            var c=Issue(req);
            Need(c.ObserveEchoAndTerminate(Req(),Peer,c.GetChallengeCopy())==
                ReviewOnlyChallengeVerdict.Refused,"delete vs save");
            NoAuthority(c);
            var valid=Issue(req);MustEchoOnly(valid,req);
        });
        Run("no-service-WinCred-or-release-eligibility",()=>
        {
            var req=Req();var c=Issue(req);
            Need(!ServiceGate.LiveEligible(),"original P49 service held");
            Need(CandidateCredentialEffectHold.LegacyEffectEntryDisabled() &&
                CandidateCredentialEffectHold.NativeMutationAdmissionPending(),
                "P112 native effect still disabled");
            MustEchoOnly(c,req);
            Need(!c.NativeCredentialEffectAllowed,
                "even matched echo cannot dispatch");
        });

        Console.WriteLine("P120_REVIEW_ONLY_CHALLENGE_CASES_PASSED="+passed);
        Console.WriteLine("P120_REVIEW_ONLY_CHALLENGE_CASES_FAILED="+failed);
        Console.WriteLine("P120_CSPRNG_256_BIT_NONCE=TRUE");
        Console.WriteLine("P120_ONE_USE_CANONICAL_OPERATION_ECHO=REVIEW_ONLY");
        Console.WriteLine("P120_AUTHENTICATED_SERVICE_ISSUER=NOT_IMPLEMENTED");
        Console.WriteLine("P120_SIGNED_UI_HUMAN_CONSENT=NOT_PROVEN");
        Console.WriteLine("P120_DURABLE_GRANT_OR_CREDENTIAL_EFFECT=ABSENT");
        Console.WriteLine("P120_OLD_P96_RACE=STILL_OPEN");
        Console.WriteLine("P120_C1_PRODUCTION_RELEASE=HOLD");
        return passed==27 && failed==0?0:1;
    }
}
