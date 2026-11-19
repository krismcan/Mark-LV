#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P284_DURABLE_OPERATION_REVIEW_ONLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY || !C1_P270_DEVELOPMENT_ONLY || !C1_P271_DEVELOPMENT_ONLY || !C1_P282_IDENTITY_CUSTODY_REVIEW_ONLY
#error P284_TEST_ONLY_ALL_DURABLE_FLAGS_REQUIRED
#endif
using System;
using System.Security.Principal;
using System.IO;
using System.Collections.Generic;
using Nayeon.ByokC1.P270Development;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P284Development;

internal static class DurableOperationAdmissionTests
{
    // No provisioning, ACL changes, deletion, or root reuse in this harness.
    // An independently reviewed host must provide one empty P270-compatible
    // ACL-isolated root per owner. This program is compile-only in this task.
    private static readonly HashSet<string> usedRoots = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    private static int rootIndex;
    private static string lastRoot;
    private static DurableOperationAdmission Create(LedgerOperation op, bool fresh,
        out DurableOperationAdmission.TestOnlyIssuer issuer)
    {
        string list = Environment.GetEnvironmentVariable("P284_PREPROVISIONED_ROOTS");
        Check(!String.IsNullOrEmpty(list), "separately provisioned roots required");
        string[] roots = list.Split('|');
        Check(rootIndex < roots.Length, "one disposable root per owner");
        string root = Path.GetFullPath(roots[rootIndex++]);
        Check(usedRoots.Add(root) && Directory.Exists(root), "unique existing disposable root");
        lastRoot = root;
        return DurableOperationAdmission.TestOnlyCreate(root, op, fresh, out issuer);
    }
    private static int checks, cases;
    private static void Check(bool value, string reason)
    { Interlocked.Increment(ref checks); if (!value) throw new Exception(reason); }
    private static void Run(string name, Action test)
    { test(); cases++; Console.WriteLine("PASS " + name); }
    private static byte[] Marker(LedgerOperation op)
    { return op == LedgerOperation.Delete ? null : new byte[] { 0x31, 0x32, 0x33, 0x34 }; }
    private static ServiceBoundRequestIdentity Request(LedgerOperation op, long expiry)
    { return new ServiceBoundRequestIdentity(op, new string('a', 32), new string('b', 32),
        op == LedgerOperation.Delete ? null : DurableOperationAdmission.TestMarkerDigest(), expiry,
        op == LedgerOperation.Delete); }
    private static long Later() { return DateTime.UtcNow.AddMinutes(2).Ticks; }
    private static CustodyOutcome Success(LedgerOperation op)
    { return op == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified; }
    private static ControlResult Control(DurableOperationAdmission owner, int reason)
    { return reason == 0 ? owner.Revoke() : reason == 1 ? owner.Stop() : owner.Fault(); }
    private static void Join(Thread thread) { Check(thread.Join(3500), "thread deadline"); }
    private static void NoReplay(DurableOperationAdmission owner, DurableOperationAdmission.TestOnlyIssuer issuer,
        DurableOperationAdmission.TestOnlyTicket ticket, ServiceBoundRequestIdentity request)
    {
        int before = owner.TestEffects;
        Check(owner.Submit(ticket, request, Marker(request.Operation)) == CustodyOutcome.Denied, "replay denied");
        Check(owner.Issue(issuer, request, Marker(request.Operation)) == null, "cannot mint second approval");
        Check(owner.TestEffects == before, "no caller-consent authority");
        Check(!owner.Observe().ProductionEligible && !owner.Observe().CredentialAllowed &&
            !DurableOperationAdmission.ProductionEligible && !DurableOperationAdmission.HumanConsentEstablished,
            "all production/consent grants remain false");
    }
    private static void MetadataOnly(LedgerOperation op)
    {
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(op, true, out issuer))
        {
            Check(owner.Start(), "start");
            var request = Request(op, Later());
            Check(owner.Issue(null, request, Marker(op)) == null, "claims alone cannot issue");
            Check(owner.Issue(new DurableOperationAdmission.TestOnlyIssuer(), request, Marker(op)) == null,
                "fabricated issuer rejected");
            Check(owner.Submit(new DurableOperationAdmission.TestOnlyTicket(), request, Marker(op)) == CustodyOutcome.Denied,
                "fabricated ticket without issuance rejected");
            Check(owner.TestEffects == 0, "metadata-only zero effects");
            var ticket = owner.Issue(issuer, request, Marker(op));
            Check(ticket != null, "private synthetic issuer still usable");
            Check(owner.Submit(ticket, request, Marker(op)) == Success(op), "actual managed fixture effect");
            Check(owner.TestEffects == 1 && owner.TestTerminal, "one terminal effect with cleanup");
            Check(owner.TestConsistent() && owner.TestPhase() == (op == LedgerOperation.Delete ?
                LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified), "actual durable terminal pair");
            Check(owner.Observe().PendingRecoveryRequired, "stored/removed remains unverified");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void Mismatch(int kind)
    {
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
            Check(owner.Submit(kind == 7 ? new DurableOperationAdmission.TestOnlyTicket() : ticket,
                altered, marker) == CustodyOutcome.Denied, "bound mismatch denied");
            Check(owner.TestEffects == 0, "mismatch zero effects");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void InvalidIssue(int kind)
    {
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer aIssuer, bIssuer;
        using (var a = Create(LedgerOperation.Save, true, out aIssuer))
        using (var b = Create(LedgerOperation.Save, true, out bIssuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(op, true, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        if (!fresh)
        {
            // P271 refuses recovery/restart at construction, before any ticket.
            bool blocked = false;
            try { using (var ignored = Create(LedgerOperation.Save, false, out issuer)) {} }
            catch (LedgerBlocked) { blocked = true; }
            Check(blocked, "nonfresh cannot construct an admitted durable session");
            return;
        }
        using (var owner = Create(LedgerOperation.Save, fresh, out issuer))
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
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
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
    private static void AtPoint(string point, int kind)
    {
        DurableOperationAdmission.TestOnlyIssuer issuer;
        using (var owner = Create(LedgerOperation.Save, true, out issuer))
        {
            Check(owner.Start(), "critical point start");
            var request = Request(LedgerOperation.Save, kind == 0 ? DateTime.UtcNow.AddSeconds(2).Ticks : Later());
            var ticket = owner.Issue(issuer, request, Marker(request.Operation));
            Check(ticket != null, "critical point ticket");
            bool visited = false;
            WindowsImpersonationContext impersonation = null;
            owner.TestProbe = p => {
                if (p != point || visited) return;
                visited = true;
                if (kind == 0) Check(SpinWait.SpinUntil(() => DateTime.UtcNow.Ticks >= request.ExpiresUtcTicks, 3500), "expiry reached");
                else if (kind == 1)
                {
                    // Same user impersonation is still a thread token: P282 must
                    // reject it instead of silently falling back to process identity.
                    using (WindowsIdentity actual = WindowsIdentity.GetCurrent()) impersonation = actual.Impersonate();
                }
                else if (kind == 2) owner.TestCloseWitness();
                else
                {
                    try { if (kind == 3) owner.Revoke(); else if (kind == 4) owner.Stop();
                        else if (kind == 5) owner.Fault(); else owner.Dispose(); }
                    catch (InvalidOperationException) { } // adversary swallows reentry
                }
            };
            CustodyOutcome result;
            try { result = owner.Submit(ticket, request, Marker(request.Operation)); }
            finally { if (impersonation != null) impersonation.Dispose(); }
            Check(visited && result == CustodyOutcome.RecoveryRequired, "in-gate critical check refuses");
            Check(owner.TestEffects == (point == "effect-return" ? 1 : 0), "no premature or second effect");
            Check(owner.Observe().PendingRecoveryRequired, "fault remains uncertain");
            if (point == "effect-return") Check(owner.Revoke() == ControlResult.TooLate, "in-flight never safe cancellation");
            NoReplay(owner, issuer, ticket, request);
        }
    }
    private static void ExtraCases()
    {
        foreach (string edge in new[] { "trust", "read-journal", "read-anchor", "present",
            "write-journal", "after-journal", "write-anchor", "after-anchor", "effect-enter", "effect-return" })
        {
            string selected = edge;
            for (int kind = 0; kind <= 6; kind++)
            {
                int attack = kind;
                Run("in-gate-" + selected + "-attack-" + attack, () => AtPoint(selected, attack));
            }
        }
        Run("callback-is-not-consent", delegate {
            DurableOperationAdmission.TestOnlyIssuer issuer;
            using (var owner = Create(LedgerOperation.Save, true, out issuer))
            {
                Check(owner.Start(), "callback-only start");
                var request = Request(LedgerOperation.Save, Later());
                int visits = 0;
                owner.TestProbe = p => visits++;
                owner.TestProbe("effect-enter"); // fabricated notification does nothing
                Check(visits == 1 && owner.TestEffects == 0, "notification cannot execute");
                Check(owner.Submit(new DurableOperationAdmission.TestOnlyTicket(), request, Marker(request.Operation)) ==
                    CustodyOutcome.Denied, "callback cannot authorize metadata");
                var ticket = owner.Issue(issuer, request, Marker(request.Operation));
                Check(ticket != null && owner.Submit(ticket, request, Marker(request.Operation)) == Success(request.Operation),
                    "genuine private bridge still composes positively");
                Check(owner.TestEffects == 1 && owner.TestConsistent(), "one durable effect");
            }
        });
        for (int kind = 0; kind < 5; kind++)
        {
            int selected = kind;
            Run("missing-or-delete-mismatch-" + kind, delegate {
                DurableOperationAdmission.TestOnlyIssuer issuer;
                using (var owner = Create(LedgerOperation.Delete, true, out issuer))
                {
                    Check(owner.Start(), "delete mismatch start");
                    var request = Request(LedgerOperation.Delete, Later());
                    if (selected == 0)
                        Check(owner.Issue(issuer, null, null) == null, "missing request cannot issue");
                    else
                    {
                        var ticket = owner.Issue(issuer, request, null);
                        Check(ticket != null, "delete issued");
                        var changed = selected == 4 ? Request(LedgerOperation.Save, request.ExpiresUtcTicks) : request;
                        Check(owner.Submit(selected == 1 ? null : ticket, selected == 2 ? null : changed,
                            selected == 3 ? Marker(LedgerOperation.Save) : null) == CustodyOutcome.Denied,
                            "missing ticket/request or changed delete semantics deny");
                    }
                    Check(owner.TestEffects == 0, "invalid delete no effect");
                    NoReplay(owner, issuer, null, request);
                }
            });
        }
        Run("syntactically-valid-wrong-digest", delegate {
            DurableOperationAdmission.TestOnlyIssuer issuer;
            using (var owner = Create(LedgerOperation.Save, true, out issuer))
            {
                Check(owner.Start(), "wrong digest start");
                var claimed = new ServiceBoundRequestIdentity(LedgerOperation.Save, new string('a', 32),
                    new string('b', 32), new string('0', 64), Later(), false);
                Check(owner.Issue(issuer, claimed, Marker(claimed.Operation)) == null && owner.TestEffects == 0,
                    "genuine P102 object and claimed hash are metadata only");
            }
        });
        Run("disposed-session", delegate {
            DurableOperationAdmission.TestOnlyIssuer issuer;
            using (var owner = Create(LedgerOperation.Save, true, out issuer))
            {
                Check(owner.Start(), "dispose start");
                var request = Request(LedgerOperation.Save, Later());
                var ticket = owner.Issue(issuer, request, Marker(request.Operation));
                owner.Dispose();
                Check(owner.Submit(ticket, request, Marker(request.Operation)) == CustodyOutcome.Denied && owner.TestEffects == 0,
                    "disposed session cannot use its ticket");
            }
        });
        Run("durable-restart-never-rearms", delegate {
            DurableOperationAdmission.TestOnlyIssuer issuer;
            string root;
            using (var owner = Create(LedgerOperation.Save, true, out issuer))
            {
                root = lastRoot;
                Check(owner.Start(), "restart initial start");
                var request = Request(LedgerOperation.Save, Later());
                var ticket = owner.Issue(issuer, request, Marker(request.Operation));
                Check(owner.Submit(ticket, request, Marker(request.Operation)) == Success(request.Operation), "restart initial effect");
            }
            foreach (bool fresh in new[] { false, true })
            {
                bool blocked = false;
                try { using (var ignored = DurableOperationAdmission.TestOnlyCreate(root, LedgerOperation.Save, fresh, out issuer)) {} }
                catch (LedgerBlocked) { blocked = true; }
                Check(blocked, "neither fresh nor recovery mode rearms used durable root");
            }
        });
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
                Environment.GetEnvironmentVariable("P284_REVIEWED_DURABLE_RUNTIME") == "1", "hosted fixture required");
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent()) Check(!identity.IsSystem, "no SYSTEM tests");
            Check(!String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) &&
                !String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase), "never Kristian");
            Check(Environment.GetEnvironmentVariable("P271_HOSTED_DISPOSABLE") == "1",
                "P271 hosted fixture restrictions required");
            using (var deadline = new Timer(delegate(object ignored) {
                Console.Error.WriteLine("P284_HOLD DEADLINE"); Environment.Exit(124);
            }, null, 120000, Timeout.Infinite))
            {
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
            ExtraCases();
            Console.WriteLine("P284_SYNTHETIC_ONLY=PASS CASES=" + cases + " ASSERTIONS=" + checks + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=OPEN P76_P216=UNWAIVED");
            return 0;
            }
        }
        catch (Exception error) { Console.WriteLine("P284_FAIL=" + error); return 1; }
    }
}

// Separate entrypoint: only missing-host-claim denials before P270 construction.
// No root argument, environment provisioning, durable positive call or ACL work.
internal static class P284ReadOnlyNegativeTests
{
    private static void Check(bool value) { if (!value) throw new Exception("P284_READ_ONLY_ASSERT"); }
    private static int Main()
    {
        try
        {
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT &&
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Environment.GetEnvironmentVariable("RUNNER_OS") == "Windows" &&
                Environment.GetEnvironmentVariable("P284_READ_ONLY_NEGATIVES") == "1");
            Check(!String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) &&
                !String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase));
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent()) Check(!identity.IsSystem);
            string[] keys = { "GITHUB_ACTIONS", "RUNNER_ENVIRONMENT", "RUNNER_OS",
                "P270_HOSTED_DISPOSABLE", "P271_HOSTED_DISPOSABLE" };
            string[] values = new string[keys.Length];
            for (int i = 0; i < keys.Length; i++) values[i] = Environment.GetEnvironmentVariable(keys[i]);
            int cases = 0;
            try
            {
                for (int missing = 0; missing < 4; missing++)
                {
                    for (int i = 0; i < keys.Length; i++) Environment.SetEnvironmentVariable(keys[i], values[i]);
                    Environment.SetEnvironmentVariable("P270_HOSTED_DISPOSABLE", null);
                    Environment.SetEnvironmentVariable("P271_HOSTED_DISPOSABLE", missing == 3 ? null : "1");
                    if (missing < 3) Environment.SetEnvironmentVariable(keys[missing], "rejected");
                    foreach (bool fresh in new[] { false, true })
                    {
                        string stage = DurableWitness.TestStage;
                        bool blocked = false;
                        DurableOperationAdmission.TestOnlyIssuer issuer;
                        try { using (var ignored = DurableOperationAdmission.TestOnlyCreate(null, LedgerOperation.Save, fresh, out issuer)) {} }
                        catch (LedgerBlocked) { blocked = true; }
                        Check(blocked && DurableWitness.TestStage == stage);
                        cases++;
                    }
                }
            }
            finally { for (int i = 0; i < keys.Length; i++) Environment.SetEnvironmentVariable(keys[i], values[i]); }
            Check(!DurableOperationAdmission.ProductionEligible && !DurableOperationAdmission.HumanConsentEstablished);
            // Valid P102 syntax remains a claim, with no ticket/issuer conversion.
            var metadata = new ServiceBoundRequestIdentity(LedgerOperation.Save, new string('a', 32),
                new string('b', 32), DurableOperationAdmission.TestMarkerDigest(), DateTime.UtcNow.AddMinutes(1).Ticks, false);
            Check(metadata.HasSafeClockWindow(DateTime.UtcNow.Ticks));
            Console.WriteLine("P284_READ_ONLY_NEGATIVES=PASS CASES=" + cases + " DURABLE_RUNTIME=NOT_RUN PRODUCTION=HOLD");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine("P284_READ_ONLY_HOLD=" + error.GetType().Name); return 1; }
    }
}
