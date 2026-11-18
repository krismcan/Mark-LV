#if !DEBUG || !C1_P271_DEVELOPMENT_ONLY
#error P271_TESTS_DEVELOPMENT_ONLY_REQUIRED
#endif
using System;
using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P268Development;
using Nayeon.ByokC1.P270Development;
using Nayeon.ByokC1.P271Development;

internal static class P271DurableBridgeTests
{
    private static int cases, assertions;
    private static string currentCase = "hosted-entry";
    private static void Check(bool value)
    { Interlocked.Increment(ref assertions); if (!value) throw new Exception("P271_ASSERT"); }
    private static void Block(Action action)
    { bool blocked = false; try { action(); } catch (LedgerBlocked) { blocked = true; } Check(blocked); }
    private sealed class Scope : IDisposable
    {
        internal readonly string Root;
        internal Scope()
        {
            // Same strict provisioning model and required prefix as frozen P270.
            Root = Path.Combine(Path.GetTempPath(), "nayeon-p270-" + Guid.NewGuid().ToString("N"));
            Check(!Directory.Exists(Root));
            DirectorySecurity acl = new DirectorySecurity();
            SecurityIdentifier sid = WindowsIdentity.GetCurrent().User;
            acl.SetOwner(sid); acl.SetAccessRuleProtection(true, false);
            acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None, AccessControlType.Allow));
            Directory.CreateDirectory(Root, acl);
        }
        internal string FilePath(string name) { return Path.Combine(Root, name); }
        public void Dispose()
        {
            Check(Path.GetDirectoryName(Root).TrimEnd('\\') == Path.GetTempPath().TrimEnd('\\'));
            Check((File.GetAttributes(Root) & FileAttributes.ReparsePoint) == 0);
            // Only our generated immediate files; no recursive traversal or deletion.
            foreach (string path in Directory.GetFiles(Root)) File.Delete(path);
            Directory.Delete(Root, false);
        }
    }
    private static void Run(string name, Action test)
    { currentCase = name; test(); cases++; Console.WriteLine("PASS " + name); }
    private static void Fresh(LedgerOperation op, Action<DurableDevelopmentBridge> test)
    {
        using (Scope scope = new Scope())
        using (DurableDevelopmentBridge bridge = new DurableDevelopmentBridge(scope.Root, op, true))
        { Check(bridge.Start()); test(bridge); }
    }
    private static void NoReplay(DurableDevelopmentBridge b, ServiceOwnedPendingTransaction.Approval ticket)
    {
        int effects = b.TestEffects;
        b.Submit(ticket); Check(b.TestEffects == effects && b.Prepare() == null);
    }
    private static Thread Worker(Action action, Action<Exception> fail)
    {
        Thread thread = new Thread(delegate() { try { action(); } catch (Exception e) { fail(e); } });
        thread.IsBackground = true; return thread;
    }
    private static void Join(Thread thread) { Check(thread.Join(3000)); }
    private static void EffectFirst(DurableDevelopmentBridge b, int control)
    {
        var ticket = b.Prepare(); Check(ticket != null);
        using (var entered = new ManualResetEvent(false))
        using (var release = new ManualResetEvent(false))
        {
            b.TestProbe = point => { if (point == "effect-enter")
                { entered.Set(); Check(release.WaitOne(1500)); } };
            CustodyOutcome outcome = CustodyOutcome.Denied;
            ControlResult result = ControlResult.Revoked;
            Exception writeError = null, controlError = null;
            Thread writer = Worker(() => { outcome = b.Submit(ticket); }, e => writeError = e);
            Thread closer = Worker(() => { result = control == 0 ? b.Revoke() : control == 1 ? b.Stop() : b.Fault(); }, e => controlError = e);
            writer.Start();
            try
            {
                Check(entered.WaitOne(1500)); closer.Start();
                Check(SpinWait.SpinUntil(() => b.TestAdmissionClosed, 250));
                Check(closer.IsAlive); // cannot report successful revoke across gate
            }
            finally { release.Set(); }
            Join(writer); Join(closer);
            Check(writeError == null && controlError == null && result == ControlResult.TooLate);
            Check(outcome == CustodyOutcome.StoredUnverified || outcome == CustodyOutcome.RemovedUnverified);
            Check(b.TestEffects == 1 && b.TestConsistent() && b.TestTerminal);
            Check(b.Observe().PendingMayHaveEffect && b.Observe().PendingRecoveryRequired);
            NoReplay(b, ticket);
        }
    }
    private static void Refuse(DurableDevelopmentBridge b)
    {
        var ticket = b.Prepare(); Check(ticket != null);
        Check(b.Submit(ticket) == CustodyOutcome.RecoveryRequired && b.TestEffects == 0);
        Check(b.Observe().PendingRecoveryRequired); NoReplay(b, ticket);
    }
    private static void Damaged(string name, Action<Scope> damage)
    {
        Run(name, delegate
        {
            using (Scope s = new Scope())
            {
                using (var b = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true))
                {
                    Check(b.Start()); var ticket = b.Prepare();
                    // Exclusive P270 handles prevent external live modification.
                    // Model crash/release, damage disk, then prove old dispatch AND
                    // restart refuse; never reopen/rebind a witness into this owner.
                    b.TestCloseWitness(); damage(s);
                    Check(b.Submit(ticket) == CustodyOutcome.RecoveryRequired && b.TestEffects == 0);
                    Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, false)) {} });
                    Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true)) {} });
                }
            }
        });
    }
    public static int Main()
    {
        try
        {
            DurableDevelopmentBridge.RequireHosted(); // refuse manual/Kristian/LocalSystem
            using (var deadline = new Timer(delegate(object ignored) {
                Console.Error.WriteLine("P271_HOLD DEADLINE"); Environment.Exit(124);
            }, null, 55000, Timeout.Infinite))
            {
                foreach (LedgerOperation op in new[] { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete })
                {
                    LedgerOperation selected = op;
                    Run("fresh-" + op, () => Fresh(selected, b => {
                        Check(b.TestPhase() == (selected == LedgerOperation.Save ? LedgerPhase.Initial : LedgerPhase.CommittedUnverified));
                        var ticket = b.Prepare(); Check(ticket != null && b.Prepare() == null);
                        Check(b.Submit(ticket) == (selected == LedgerOperation.Delete ? CustodyOutcome.RemovedUnverified : CustodyOutcome.StoredUnverified));
                        Check(b.TestEffects == 1 && b.TestConsistent() && b.TestTerminal);
                        Check(b.TestPhase() == (selected == LedgerOperation.Delete ? LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified));
                        Check(b.Observe().PendingMayHaveEffect && b.Observe().PendingRecoveryRequired);
                        NoReplay(b, ticket);
                    }));
                    Run("revoke-first-" + op, () => Fresh(selected, b => {
                        var ticket = b.Prepare(); Check(b.Revoke() == ControlResult.Revoked);
                        Check(b.Submit(ticket) == CustodyOutcome.Denied && b.TestEffects == 0); NoReplay(b, ticket);
                    }));
                    Run("effect-first-" + op, () => Fresh(selected, b => EffectFirst(b, 0)));
                }
                for (int kind = 1; kind <= 2; kind++)
                {
                    int selected = kind;
                    Run("control-first-" + kind, () => Fresh(LedgerOperation.Save, b => {
                        var ticket = b.Prepare();
                        Check((selected == 1 ? b.Stop() : b.Fault()) == (selected == 1 ? ControlResult.Stopped : ControlResult.RecoveryRequired));
                        Check(b.Submit(ticket) == CustodyOutcome.Denied && b.TestEffects == 0);
                    }));
                    Run("control-effect-first-" + kind, () => Fresh(LedgerOperation.Save, b => EffectFirst(b, selected)));
                }
                Run("simultaneous-revoke", () => Fresh(LedgerOperation.Save, b => {
                    var ticket = b.Prepare(); Exception a = null, c = null;
                    Thread first = Worker(() => Check(b.Revoke() == ControlResult.Revoked), e => a = e);
                    Thread second = Worker(() => Check(b.Revoke() == ControlResult.Revoked), e => c = e);
                    first.Start(); second.Start(); Join(first); Join(second);
                    Check(a == null && c == null && b.Submit(ticket) == CustodyOutcome.Denied && b.TestEffects == 0);
                }));
                Run("duplicate-submission", () => Fresh(LedgerOperation.Save, b => {
                    var ticket = b.Prepare(); Exception a = null, c = null;
                    CustodyOutcome x = CustodyOutcome.Denied, y = CustodyOutcome.Denied;
                    using (var go = new ManualResetEvent(false))
                    {
                        Thread first = Worker(() => { Check(go.WaitOne(1500)); x = b.Submit(ticket); }, e => a = e);
                        Thread second = Worker(() => { Check(go.WaitOne(1500)); y = b.Submit(ticket); }, e => c = e);
                        first.Start(); second.Start(); go.Set(); Join(first); Join(second);
                    }
                    Check(a == null && c == null && b.TestEffects == 1);
                    Check((x == CustodyOutcome.StoredUnverified) != (y == CustodyOutcome.StoredUnverified)); NoReplay(b, ticket);
                }));
                Run("dispose-timeout-retains-custody", () => Fresh(LedgerOperation.Save, b => {
                    var ticket = b.Prepare(); Exception writeError = null;
                    CustodyOutcome outcome = CustodyOutcome.Denied;
                    using (var entered = new ManualResetEvent(false))
                    using (var release = new ManualResetEvent(false))
                    {
                        b.TestProbe = p => { if (p == "effect-enter") { entered.Set(); Check(release.WaitOne(4000)); } };
                        Thread writer = Worker(() => { outcome = b.Submit(ticket); }, e => writeError = e);
                        writer.Start();
                        try
                        {
                            Check(entered.WaitOne(1500));
                            bool failed = false;
                            try { b.Dispose(); } catch (InvalidOperationException) { failed = true; }
                            Check(failed && b.TestAdmissionClosed);
                            Check(b.TestConsistent()); // old finally-release would fail
                        }
                        finally { release.Set(); }
                        Join(writer);
                    }
                    Check(writeError == null && outcome == CustodyOutcome.RecoveryRequired && b.TestEffects == 0);
                    Check(b.Observe().PendingMayHaveEffect && b.Observe().PendingRecoveryRequired);
                    NoReplay(b, ticket); // Fresh's final Dispose retries after the gate exits
                }));
                foreach (string edge in new[] { "after-journal", "after-anchor" })
                {
                    string selected = edge;
                    Run("durable-write-failure-" + edge, () => Fresh(LedgerOperation.Save, b => {
                        b.TestProbe = p => { if (p == selected) b.TestCloseWitness(); };
                        Refuse(b); Check(!b.Observe().PendingMayHaveEffect);
                    }));
                }
                Run("injected-read-failure", () => Fresh(LedgerOperation.Save, b => {
                    b.TestProbe = p => { if (p == "read-journal") throw new LedgerBlocked(); }; Refuse(b);
                }));
                foreach (string edge in new[] { "read-journal", "read-anchor", "present", "effect-enter" })
                {
                    string selected = edge;
                    Run("snapshot-skew-" + edge, () => Fresh(LedgerOperation.Save, b => {
                        b.TestProbe = p => { if (p == selected) b.TestSkew(selected != "read-anchor"); }; Refuse(b);
                    }));
                }
                Run("critical-edge-untrusted", () => Fresh(LedgerOperation.Save, b => {
                    b.TestProbe = p => { if (p == "effect-enter") b.TestUntrust(); }; Refuse(b);
                }));
                Run("recovery-latch-refusal", () => Fresh(LedgerOperation.Save, b => {
                    Block(b.TestPoisonWitness); Refuse(b);
                }));
                Run("injected-effect-failure", () => Fresh(LedgerOperation.Save, b => {
                    var ticket = b.Prepare(); b.TestEffectFailure();
                    Check(b.Submit(ticket) == CustodyOutcome.RecoveryRequired && b.TestEffects == 1);
                    Check(b.Revoke() == ControlResult.TooLate && b.TestPhase() == LedgerPhase.InFlight); NoReplay(b, ticket);
                }));
                Run("live-extra-root-entry", delegate {
                    using (Scope s = new Scope()) using (var b = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true))
                    { Check(b.Start()); File.WriteAllText(s.FilePath("extra"), "synthetic"); Refuse(b); }
                });
                Run("exclusive-ownership-refusal", delegate {
                    using (Scope s = new Scope()) using (var b = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true))
                    { Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, false)) {} }); Check(b.TestConsistent()); }
                });
                Run("root-acl-refusal", delegate {
                    using (Scope s = new Scope()) {
                        DirectorySecurity acl = Directory.GetAccessControl(s.Root); acl.SetAccessRuleProtection(false, true);
                        Directory.SetAccessControl(s.Root, acl);
                        Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true)) {} });
                    }
                });
                Run("crash-consistent-restart-no-rearm", delegate {
                    using (Scope s = new Scope()) {
                        using (var b = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true)) Check(b.TestConsistent());
                        Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, false)) {} });
                        Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, true)) {} });
                    }
                });
                foreach (string name in new[] { DurableWitness.JournalName, DurableWitness.AnchorName })
                {
                    string selected = name;
                    Damaged("missing-" + name, s => File.Delete(s.FilePath(selected)));
                    Damaged("torn-" + name, s => {
                        string path = s.FilePath(selected); byte[] blob = File.ReadAllBytes(path);
                        using (var f = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.None))
                        { f.Write(blob, 0, blob.Length / 2); f.Flush(true); }
                    });
                    Damaged("corrupt-" + name, s => {
                        string path = s.FilePath(selected); byte[] blob = File.ReadAllBytes(path);
                        blob[blob.Length / 2] ^= 0xff; File.WriteAllBytes(path, blob);
                    });
                }
                Run("journal-only-crash-no-repair", delegate {
                    using (Scope s = new Scope()) {
                        using (var w = new DurableWitness(s.Root, true)) {
                            string j = w.ReadJournal(); w.WriteJournal(j, CustodyLedger.AppendIntent(j, LedgerOperation.Save, CustodyLedger.NewNonce()));
                            Check(w.RecoveryRequired);
                        }
                        Block(() => { using (var ignored = new DurableDevelopmentBridge(s.Root, LedgerOperation.Save, false)) {} });
                    }
                });
                Run("hosted-gate-refusal", delegate {
                    string prior = Environment.GetEnvironmentVariable("P271_HOSTED_DISPOSABLE");
                    try { Environment.SetEnvironmentVariable("P271_HOSTED_DISPOSABLE", null); Block(DurableDevelopmentBridge.RequireHosted); }
                    finally { Environment.SetEnvironmentVariable("P271_HOSTED_DISPOSABLE", prior); }
                });
                Console.WriteLine("P271_INTEGRATION=PASS CASES=" + cases + " ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
                Console.WriteLine("P271_SCOPE=DEVELOPMENT_ONLY SYNTHETIC_ONLY PRODUCTION=HOLD");
                return 0;
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("P271_HOLD=" + error.GetType().Name);
            Console.Error.WriteLine("P271_FAIL_CASE=" + currentCase);
            Console.Error.WriteLine("P271_FAIL_STAGE=" + DurableWitness.TestStage);
            return 1;
        }
    }
}
