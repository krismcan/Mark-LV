#if !DEBUG || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P283_SYNTHETIC_OPERATION_REVIEW_ONLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY
#error P283_TEST_ONLY_ALL_DEVELOPMENT_FLAGS_REQUIRED
#endif
using System;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P283Development;

internal static class SyntheticOperationAdmissionTests
{
    private static int checks, cases;
    private static void Check(bool value, string reason)
    { Interlocked.Increment(ref checks); if (!value) throw new Exception(reason); }
    private static void Run(string name, Action test)
    { test(); cases++; Console.WriteLine("PASS " + name); }
    private static byte[] Marker(LedgerOperation op)
    { return op == LedgerOperation.Delete ? null : new byte[] { 0x31, 0x32, 0x33, 0x34 }; }
    private static ServiceBoundRequestIdentity Request(LedgerOperation op, long expiry)
    { return new ServiceBoundRequestIdentity(op, new string('a', 32), new string('b', 32),
        op == LedgerOperation.Delete ? null : SyntheticOperationAdmission.TestMarkerDigest(), expiry,
        op == LedgerOperation.Delete); }
    private static long Later() { return DateTime.UtcNow.AddMinutes(2).Ticks; }
    private static CustodyOutcome Success(LedgerOperation op)
    { return op == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified; }
    private static ControlResult Control(SyntheticOperationAdmission owner, int reason)
    { return reason == 0 ? owner.Revoke() : reason == 1 ? owner.Stop() : owner.Fault(); }
    private static void Join(Thread thread) { Check(thread.Join(3500), "thread deadline"); }
    private static void NoReplay(SyntheticOperationAdmission owner, SyntheticOperationAdmission.TestOnlyIssuer issuer,
        SyntheticOperationAdmission.TestOnlyTicket ticket, ServiceBoundRequestIdentity request)
    {
        int before = owner.TestEffects;
        Check(owner.Submit(ticket, request, Marker(request.Operation)) == CustodyOutcome.Denied, "replay denied");
        Check(owner.Issue(issuer, request, Marker(request.Operation)) == null, "cannot mint second approval");
        Check(owner.TestEffects == before && owner.TestCallerApprovalConsumes == 0, "no caller-consent authority");
        Check(!owner.Observe().ProductionEligible && !owner.Observe().CredentialAllowed &&
            !SyntheticOperationAdmission.ProductionEligible && !SyntheticOperationAdmission.HumanConsentEstablished,
            "all production/consent grants remain false");
    }
    private static void MetadataOnly(LedgerOperation op)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(op, true, out issuer))
        {
            Check(owner.Start(), "start");
            var request = Request(op, Later());
            Check(owner.Issue(null, request, Marker(op)) == null, "claims alone cannot issue");
            Check(owner.Issue(new SyntheticOperationAdmission.TestOnlyIssuer(), request, Marker(op)) == null,
                "fabricated issuer rejected");
            Check(owner.Submit(new SyntheticOperationAdmission.TestOnlyTicket(), request, Marker(op)) == CustodyOutcome.Denied,
                "fabricated ticket without issuance rejected");
            Check(owner.TestEffects == 0, "metadata-only zero effects");
            var ticket = owner.Issue(issuer, request, Marker(op));
            Check(ticket != null, "private synthetic issuer still usable");
            Check(owner.Submit(ticket, request, Marker(op)) == Success(op), "actual managed fixture effect");
            Check(owner.TestEffects == 1 && owner.TestTerminal, "one terminal effect with cleanup");
            Check(owner.Observe().PendingRecoveryRequired, "stored/removed remains unverified");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void Mismatch(int kind)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "start mismatch");
            var request = Request(LedgerOperation.Save, Later());
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            Check(ticket != null, "issue mismatch");
            var altered = new ServiceBoundRequestIdentity(kind == 0 ? LedgerOperation.Replace : LedgerOperation.Save,
                new string(kind == 1 ? 'c' : 'a', 32), new string(kind == 2 ? 'c' : 'b', 32),
                kind == 3 ? new string('0', 64) : request.CandidateSha256,
                request.ExpiresUtcTicks + (kind == 4 ? 1 : 0), false);
            byte[] marker = kind == 5 ? new byte[] { 0, 0, 0, 0 } : kind == 6 ? null : Marker(request.Operation);
            Check(owner.Submit(kind == 7 ? new SyntheticOperationAdmission.TestOnlyTicket() : ticket,
                altered, marker) == CustodyOutcome.Denied, "bound mismatch denied");
            Check(owner.TestEffects == 0, "mismatch zero effects");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void InvalidIssue(int kind)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "invalid issue start");
            var request = Request(kind == 0 ? LedgerOperation.Delete : LedgerOperation.Save,
                kind == 1 ? DateTime.UtcNow.AddSeconds(-1).Ticks : kind == 2 ? DateTime.UtcNow.AddMinutes(6).Ticks : Later());
            Check(owner.Issue(issuer, request, kind == 3 ? new byte[4] : Marker(request.Operation)) == null,
                "invalid issuance denied");
            Check(owner.Issue(issuer, Request(LedgerOperation.Save, Later()), Marker(LedgerOperation.Save)) == null,
                "failed issuance cancels session");
            Check(owner.TestEffects == 0 && owner.Observe().Closed, "invalid issue closes without effect");
        }
    }
    private static void Foreign()
    {
        SyntheticOperationAdmission.TestOnlyIssuer aIssuer, bIssuer;
        using (var a = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out aIssuer))
        using (var b = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out bIssuer))
        {
            Check(a.Start() && b.Start(), "two owners start");
            var request = Request(LedgerOperation.Save, Later());
            Check(b.Issue(aIssuer, request, Marker(request.Operation)) == null, "issuer nontransferable");
            var aTicket = a.Issue(aIssuer, request, Marker(request.Operation));
            var bTicket = b.Issue(bIssuer, request, Marker(request.Operation));
            Check(aTicket != null && bTicket != null, "two explicit independent issuances");
            Check(b.Submit(aTicket, request, Marker(request.Operation)) == CustodyOutcome.Denied,
                "ticket nontransferable even with identical metadata");
            Check(b.Submit(bTicket, request, Marker(request.Operation)) == CustodyOutcome.Denied && b.TestEffects == 0,
                "foreign attempt cancels recipient");
            Check(a.Submit(aTicket, request, Marker(request.Operation)) == Success(request.Operation), "source owner unaffected");
        }
    }
    private static void Ordering(LedgerOperation op, int reason, bool effectFirst)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(op, true, out issuer))
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        {
            Check(owner.Start(), "ordering start");
            var request = Request(op, Later());
            var ticket = owner.Issue(issuer, request, Marker(op));
            Check(ticket != null, "ordering issue");
            if (!effectFirst)
            {
                Check(Control(owner, reason) == (reason == 0 ? ControlResult.Revoked :
                    reason == 1 ? ControlResult.Stopped : ControlResult.RecoveryRequired), "control first disposition");
                Check(owner.Submit(ticket, request, Marker(op)) == CustodyOutcome.Denied && owner.TestEffects == 0,
                    "revoke/stop/fault before final prevents effect");
            }
            else
            {
                owner.TestProbe = point => { if (point == "effect-enter")
                    { entered.Set(); if (!release.WaitOne(1800)) throw new Exception("release deadline"); } };
                CustodyOutcome result = CustodyOutcome.Denied;
                ControlResult control = ControlResult.Revoked;
                Exception writerError = null, controlError = null;
                var writer = new Thread(() => { try { result = owner.Submit(ticket, request, Marker(op)); }
                    catch (Exception e) { writerError = e; } });
                var revoker = new Thread(() => { try { control = Control(owner, reason); }
                    catch (Exception e) { controlError = e; } });
                writer.Start();
                try
                {
                    Check(entered.WaitOne(1500), "inside actual P268 effect interface");
                    revoker.Start();
                    // Do not call Observe here: it acquires the pending gate.
                    Check(!revoker.Join(40), "control cannot complete across owned final gate");
                }
                finally { release.Set(); }
                Join(writer); Join(revoker);
                Check(writerError == null && controlError == null, "race threads completed");
                Check(result == Success(op) && control == ControlResult.TooLate, "effect first cannot claim revocation success");
                Check(owner.TestEffects == 1 && owner.TestTerminal, "single actual fixture effect and cleanup");
            }
            NoReplay(owner, issuer, ticket, request);
            Check(!owner.Start(), "restart denied");
        }
    }
    private static void Expiry(bool duringFinal)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "expiry start");
            var request = Request(LedgerOperation.Save, DateTime.UtcNow.AddMilliseconds(750).Ticks);
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            Check(ticket != null, "expiry ticket");
            Action expire = () => { Check(SpinWait.SpinUntil(() => DateTime.UtcNow.Ticks >= request.ExpiresUtcTicks, 1800),
                "real service clock reached expiry"); };
            if (duringFinal) owner.TestProbe = point => { if (point == "effect-enter") expire(); };
            else expire();
            Check(owner.Submit(ticket, request, Marker(request.Operation)) ==
                (duringFinal ? CustodyOutcome.RecoveryRequired : CustodyOutcome.Denied), "expiry final disposition");
            Check(owner.TestEffects == 0, "expiry prevents identical fixture effect");
            if (duringFinal) Check(owner.Observe().PendingRecoveryRequired && owner.Observe().PendingMayHaveEffect,
                "P268 conservatively reports uncertainty after intent/effect entry");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void Callback(int kind)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "callback start");
            var request = Request(LedgerOperation.Save, Later());
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            bool visited = false;
            owner.TestProbe = point =>
            {
                if (visited || point != "effect-enter") return;
                visited = true;
                Check(owner.Issue(issuer, request, Marker(request.Operation)) == null, "callback cannot reissue");
                Check(owner.Submit(ticket, request, Marker(request.Operation)) == CustodyOutcome.Denied, "callback cannot resubmit");
                if (kind >= 1 && kind <= 5)
                {
                    try
                    {
                        if (kind <= 3) Control(owner, kind - 1);
                        else if (kind == 4) owner.Start();
                        else owner.Dispose();
                    }
                    catch (InvalidOperationException) { }
                }
                if (kind == 6) owner.Observe(); // P269 catches its own reentry error.
                if (kind == 7) throw new Exception("synthetic callback fault");
            };
            Check(owner.Submit(ticket, request, Marker(request.Operation)) ==
                (kind == 0 ? Success(request.Operation) : CustodyOutcome.RecoveryRequired), "callback outcome");
            Check(visited && owner.TestEffects == (kind == 0 ? 1 : 0), "callback no second effect");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void DoubleSubmit()
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        using (var go = new ManualResetEvent(false))
        {
            Check(owner.Start(), "double submit start");
            var request = Request(LedgerOperation.Save, Later());
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            CustodyOutcome a = CustodyOutcome.Denied, b = CustodyOutcome.Denied;
            Exception errorA = null, errorB = null;
            var first = new Thread(() => { try { if (!go.WaitOne(1500)) throw new Exception("go");
                a = owner.Submit(ticket, request, Marker(request.Operation)); } catch (Exception e) { errorA = e; } });
            var second = new Thread(() => { try { if (!go.WaitOne(1500)) throw new Exception("go");
                b = owner.Submit(ticket, request, Marker(request.Operation)); } catch (Exception e) { errorB = e; } });
            first.Start(); second.Start(); go.Set(); Join(first); Join(second);
            Check(errorA == null && errorB == null && (a == Success(request.Operation)) != (b == Success(request.Operation)),
                "exactly one concurrent submit wins");
            Check(owner.TestEffects == 1, "double submit one effect");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void CallbackControlTimeout()
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "callback timeout start");
            var request = Request(LedgerOperation.Save, Later());
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            Exception controlError = null;
            owner.TestProbe = point =>
            {
                if (point != "effect-enter") return;
                var controller = new Thread(() => { try { owner.Revoke(); } catch (Exception e) { controlError = e; } });
                controller.Start(); Join(controller); // exercise P268's bounded 500ms gate failure
            };
            Check(owner.Submit(ticket, request, Marker(request.Operation)) == CustodyOutcome.RecoveryRequired,
                "callback control timeout poisons submission");
            Check(controlError is InvalidOperationException && owner.TestEffects == 0,
                "uncertain control is never reported as revocation and prevents fixture entry");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void Lifecycle(bool fresh, bool start)
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, fresh, out issuer))
        {
            if (start) Check(!owner.Start(), "nonfresh start denied");
            var request = Request(LedgerOperation.Save, Later());
            Check(owner.Issue(issuer, request, Marker(request.Operation)) == null && owner.TestEffects == 0,
                "unstarted/nonfresh cannot approve");
            if (!fresh) Check(owner.Observe().PendingRecoveryRequired, "nonfresh recovery required");
        }
    }
    private static void UncertainEffect()
    {
        SyntheticOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = SyntheticOperationAdmission.TestOnlyCreate(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "uncertain start");
            var request = Request(LedgerOperation.Save, Later());
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            owner.TestFailEffect();
            Check(owner.Submit(ticket, request, Marker(request.Operation)) == CustodyOutcome.RecoveryRequired,
                "actual fixture fault reports recovery");
            Check(owner.TestEffects == 1 && owner.Fault() == ControlResult.TooLate && owner.Observe().PendingRecoveryRequired,
                "uncertain effect cannot become cancellation");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static int Main()
    {
        try
        {
            // Execution is for a separately reviewed, disposable hosted Windows job ONLY.
            // These claims restrict tests; they confer no production/service authority.
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT &&
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Environment.GetEnvironmentVariable("RUNNER_OS") == "Windows" &&
                Environment.GetEnvironmentVariable("P283_HOSTED_SYNTHETIC_ONLY") == "1", "hosted fixture required");
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent()) Check(!identity.IsSystem, "no SYSTEM tests");
            foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete })
            {
                Run("metadata-only-then-explicit-fixture-" + op, () => MetadataOnly(op));
                for (int reason = 0; reason < 3; reason++)
                    foreach (bool effectFirst in new[] { false, true })
                        Run("ordering-" + op + "-" + reason + "-" + effectFirst, () => Ordering(op, reason, effectFirst));
            }
            for (int kind = 0; kind < 8; kind++) Run("mismatch-" + kind, () => Mismatch(kind));
            for (int kind = 0; kind < 4; kind++) Run("invalid-issue-" + kind, () => InvalidIssue(kind));
            Run("nontransferable", Foreign);
            Run("expiry-before-submit", () => Expiry(false)); Run("expiry-inside-final-gate", () => Expiry(true));
            for (int kind = 0; kind < 8; kind++) Run("malicious-callback-" + kind, () => Callback(kind));
            Run("concurrent-submit", DoubleSubmit);
            Run("callback-control-timeout", CallbackControlTimeout);
            Run("unstarted", () => Lifecycle(true, false)); Run("nonfresh-restart", () => Lifecycle(false, true));
            Run("uncertain-effect", UncertainEffect);
            Console.WriteLine("P283_SYNTHETIC_ONLY=PASS CASES=" + cases + " ASSERTIONS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=OPEN P76_P216=UNWAIVED");
            return 0;
        }
        catch (Exception error) { Console.WriteLine("P283_FAIL=" + error); return 1; }
    }
}
