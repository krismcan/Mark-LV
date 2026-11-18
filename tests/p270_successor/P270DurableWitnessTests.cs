using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using Nayeon.ByokC1;
using Nayeon.ByokC1.P270Development;

internal static class P270DurableWitnessTests
{
    private static int cases, assertions;
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateSymbolicLink(string link, string target, uint flags);
    private static void Assert(bool value) { assertions++; if (!value) throw new Exception("P270 assertion " + assertions); }
    private static void Block(Action action)
    { bool blocked = false; try { action(); } catch (LedgerBlocked) { blocked = true; } Assert(blocked); }
    private sealed class Scope : IDisposable
    {
        internal readonly string Root;
        internal Scope()
        {
            Root = Path.Combine(Path.GetTempPath(), "nayeon-p270-" + Guid.NewGuid().ToString("N"));
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
            // No recursive deletion, no link traversal: only this exact generated root.
            Assert(Path.GetDirectoryName(Root).TrimEnd('\\') == Path.GetTempPath().TrimEnd('\\'));
            Assert((File.GetAttributes(Root) & FileAttributes.ReparsePoint) == 0);
            foreach (string path in Directory.GetFiles(Root)) File.Delete(path);
            Directory.Delete(Root, false);
        }
    }
    private static void Run(string name, Action test)
    { test(); cases++; Console.WriteLine("PASS " + name); }
    private static void ReopenDenied(Scope scope, bool consistent)
    {
        using (DurableWitness witness = new DurableWitness(scope.Root, false))
        {
            Assert(witness.RecoveryRequired); Assert(witness.InspectConsistent() == consistent);
            string j = witness.ReadJournal();
            Block(delegate { witness.WriteJournal(j, CustodyLedger.AppendIntent(j, LedgerOperation.Save, CustodyLedger.NewNonce())); });
            Assert(witness.RecoveryRequired);
            Block(delegate { witness.WriteAnchor(witness.ReadAnchor(), witness.ReadAnchor()); });
        }
    }
    private static void Damaged(string name, Action<Scope> damage)
    {
        Run(name, delegate
        {
            using (Scope scope = new Scope())
            {
                using (DurableWitness witness = new DurableWitness(scope.Root, true)) Assert(witness.InspectConsistent());
                damage(scope);
                Block(delegate { using (DurableWitness ignored = new DurableWitness(scope.Root, false)) {} });
                Block(delegate { using (DurableWitness ignored = new DurableWitness(scope.Root, true)) {} });
            }
        });
    }
    public static int Main()
    {
        try
        {
            // Refuse local/manual execution, including Kristian and SCM. The CI
            // environment gate is an accident barrier, NOT authenticated authority.
            Assert(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Assert(Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Environment.GetEnvironmentVariable("P270_HOSTED_DISPOSABLE") == "1");
            Assert(!WindowsIdentity.GetCurrent().IsSystem);
            Run("initial-dpapi-codec-and-restart-denial", delegate
            {
                using (Scope scope = new Scope())
                {
                    string j, a;
                    using (DurableWitness witness = new DurableWitness(scope.Root, true))
                    {
                        Assert(!witness.RecoveryRequired && witness.InspectConsistent());
                        j = witness.ReadJournal(); a = witness.ReadAnchor();
                        Assert(CustodyLedger.Verify(j, a) == LedgerPhase.Initial);
                        Block(delegate { using (DurableWitness ignored = new DurableWitness(scope.Root, true)) {} });
                        // Both files are exclusive; read after disposal below.
                    }
                    foreach (string name in new string[] { DurableWitness.JournalName, DurableWitness.AnchorName })
                    {
                        byte[] blob = File.ReadAllBytes(scope.FilePath(name));
                        string raw = Encoding.UTF8.GetString(blob);
                        Assert(!raw.Contains(j) && !raw.Contains(a) && !raw.Contains("J2|") && !raw.Contains("A2|"));
                        bool wrongEntropy = false;
                        byte[] protectedBytes = new byte[blob.Length - 4]; Buffer.BlockCopy(blob, 4, protectedBytes, 0, protectedBytes.Length);
                        try { ProtectedData.Unprotect(protectedBytes, new byte[] { 9, 8, 7 }, DataProtectionScope.CurrentUser); }
                        catch (CryptographicException) { wrongEntropy = true; }
                        Assert(wrongEntropy);
                    }
                    ReopenDenied(scope, true);
                }
            });
            Run("sequential-inflight-terminal", delegate
            {
                using (Scope scope = new Scope())
                {
                    using (DurableWitness w = new DurableWitness(scope.Root, true))
                    {
                        foreach (LedgerOperation op in new LedgerOperation[] { LedgerOperation.Save, LedgerOperation.Replace, LedgerOperation.Delete })
                        {
                            string before = w.ReadJournal(), a = w.ReadAnchor();
                            string intent = CustodyLedger.AppendIntent(before, op, CustodyLedger.NewNonce());
                            w.WriteJournal(before, intent); Assert(w.RecoveryRequired);
                            Assert(w.ReadJournal() == intent && w.ReadAnchor() == a);
                            w.WriteAnchor(a, CustodyLedger.Anchor(intent));
                            Assert(w.InspectConsistent());
                            Assert(CustodyLedger.Verify(w.ReadJournal(), w.ReadAnchor()) == LedgerPhase.InFlight);
                            string terminal = CustodyLedger.AppendTerminal(intent);
                            w.WriteJournal(intent, terminal); w.WriteAnchor(CustodyLedger.Anchor(intent), CustodyLedger.Anchor(terminal));
                            Assert(w.InspectConsistent() && !w.RecoveryRequired);
                            Assert(CustodyLedger.Verify(w.ReadJournal(), w.ReadAnchor()) ==
                                (op == LedgerOperation.Delete ? LedgerPhase.CommittedAbsent : LedgerPhase.CommittedUnverified));
                        }
                    }
                    ReopenDenied(scope, true);
                }
            });
            Run("journal-only-crash", delegate
            {
                using (Scope s = new Scope())
                {
                    using (DurableWitness w = new DurableWitness(s.Root, true))
                    { string j = w.ReadJournal(); w.WriteJournal(j, CustodyLedger.AppendIntent(j, LedgerOperation.Save, CustodyLedger.NewNonce())); Assert(w.RecoveryRequired); }
                    Block(delegate { using (DurableWitness ignored = new DurableWitness(s.Root, false)) {} });
                }
            });
            Damaged("torn-half-journal-flushed", delegate(Scope s)
            {
                string path = s.FilePath(DurableWitness.JournalName); byte[] blob = File.ReadAllBytes(path);
                using (FileStream f = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.None))
                { f.Write(blob, 0, blob.Length / 2); f.Flush(true); }
            });
            Run("same-sid-replay-never-restarts", delegate
            {
                using (Scope s = new Scope())
                {
                    using (DurableWitness w = new DurableWitness(s.Root, true)) Assert(w.InspectConsistent());
                    byte[] j = File.ReadAllBytes(s.FilePath(DurableWitness.JournalName));
                    byte[] a = File.ReadAllBytes(s.FilePath(DurableWitness.AnchorName));
                    // Same SID can replay both protected bytes: explicitly no antirollback claim.
                    File.WriteAllBytes(s.FilePath(DurableWitness.JournalName), j);
                    File.WriteAllBytes(s.FilePath(DurableWitness.AnchorName), a);
                    ReopenDenied(s, true);
                }
            });
            Run("same-process-stale-cas-latches", delegate
            {
                using (Scope s = new Scope()) using (DurableWitness w = new DurableWitness(s.Root, true))
                {
                    string old = w.ReadJournal(), oldA = w.ReadAnchor();
                    string next = CustodyLedger.AppendIntent(old, LedgerOperation.Save, CustodyLedger.NewNonce());
                    w.WriteJournal(old, next); w.WriteAnchor(oldA, CustodyLedger.Anchor(next));
                    Block(delegate { w.WriteJournal(old, next); }); Assert(w.RecoveryRequired);
                    Block(delegate { w.WriteJournal(next, CustodyLedger.AppendTerminal(next)); });
                }
            });
            Run("anchor-cas-and-no-repair", delegate
            {
                using (Scope s = new Scope()) using (DurableWitness w = new DurableWitness(s.Root, true))
                {
                    string j = w.ReadJournal(); w.WriteJournal(j, CustodyLedger.AppendIntent(j, LedgerOperation.Save, CustodyLedger.NewNonce()));
                    Block(delegate { w.WriteAnchor("wrong", "wrong"); }); Assert(w.RecoveryRequired);
                    Block(delegate { w.WriteAnchor(w.ReadAnchor(), CustodyLedger.Anchor(w.ReadJournal())); });
                }
            });
            Run("invalid-transition-and-bound", delegate
            {
                using (Scope s = new Scope()) using (DurableWitness w = new DurableWitness(s.Root, true))
                { string j = w.ReadJournal(); Block(delegate { w.WriteJournal(j, new string('x', 32769)); }); Assert(w.RecoveryRequired); }
            });
            Run("unexpected-file-live-inspection", delegate
            {
                using (Scope s = new Scope()) using (DurableWitness w = new DurableWitness(s.Root, true))
                { File.WriteAllText(s.FilePath("extra"), "synthetic"); Assert(!w.InspectConsistent() && w.RecoveryRequired); }
            });
            Damaged("missing-anchor", delegate(Scope s) { File.Delete(s.FilePath(DurableWitness.AnchorName)); });
            Damaged("missing-journal", delegate(Scope s) { File.Delete(s.FilePath(DurableWitness.JournalName)); });
            Damaged("truncated-journal", delegate(Scope s) { File.WriteAllBytes(s.FilePath(DurableWitness.JournalName), new byte[] { 1 }); });
            Damaged("corrupt-anchor", delegate(Scope s) { byte[] b = File.ReadAllBytes(s.FilePath(DurableWitness.AnchorName)); b[b.Length / 2] ^= 0xff; File.WriteAllBytes(s.FilePath(DurableWitness.AnchorName), b); });
            Damaged("appended-journal", delegate(Scope s) { using (FileStream f = new FileStream(s.FilePath(DurableWitness.JournalName), FileMode.Append)) { f.WriteByte(7); f.Flush(true); } });
            Damaged("oversize", delegate(Scope s) { File.WriteAllBytes(s.FilePath(DurableWitness.AnchorName), new byte[65537]); });
            Damaged("unexpected-entry", delegate(Scope s) { File.WriteAllText(s.FilePath("extra"), "synthetic"); });
            Damaged("cross-file-replay", delegate(Scope s) { File.Copy(s.FilePath(DurableWitness.JournalName), s.FilePath(DurableWitness.AnchorName), true); });
            Run("cross-root-entropy", delegate
            {
                using (Scope a = new Scope()) using (Scope b = new Scope())
                {
                    using (DurableWitness w = new DurableWitness(a.Root, true)) Assert(w.InspectConsistent());
                    File.Copy(a.FilePath(DurableWitness.JournalName), b.FilePath(DurableWitness.JournalName));
                    File.Copy(a.FilePath(DurableWitness.AnchorName), b.FilePath(DurableWitness.AnchorName));
                    Block(delegate { using (DurableWitness ignored = new DurableWitness(b.Root, false)) {} });
                }
            });
            Run("repeat-enrollment", delegate
            {
                using (Scope s = new Scope())
                { using (DurableWitness w = new DurableWitness(s.Root, true)) Assert(w.InspectConsistent());
                  Block(delegate { using (DurableWitness ignored = new DurableWitness(s.Root, true)) {} }); ReopenDenied(s, true); }
            });
            Run("arbitrary-path-denied", delegate
            { Block(delegate { using (DurableWitness ignored = new DurableWitness(Path.GetTempPath(), true)) {} }); });
            Run("unprotected-acl-denied", delegate
            {
                using (Scope s = new Scope())
                {
                    DirectorySecurity acl = Directory.GetAccessControl(s.Root); acl.SetAccessRuleProtection(false, true); Directory.SetAccessControl(s.Root, acl);
                    Block(delegate { using (DurableWitness ignored = new DurableWitness(s.Root, true)) {} });
                }
            });
            Run("file-reparse-denied-if-supported", delegate
            {
                using (Scope s = new Scope())
                {
                    using (DurableWitness w = new DurableWitness(s.Root, true)) Assert(w.InspectConsistent());
                    File.Delete(s.FilePath(DurableWitness.AnchorName));
                    if (CreateSymbolicLink(s.FilePath(DurableWitness.AnchorName), s.FilePath(DurableWitness.JournalName), 2))
                    {
                        Assert((File.GetAttributes(s.FilePath(DurableWitness.AnchorName)) & FileAttributes.ReparsePoint) != 0);
                        Block(delegate { using (DurableWitness ignored = new DurableWitness(s.Root, false)) {} });
                    }
                    else { int error = Marshal.GetLastWin32Error(); Assert(error == 1314 || error == 87 || error == 50); Console.WriteLine("REPARSE_TEST=UNAVAILABLE ERROR=" + error); }
                }
            });
            Console.WriteLine("P270_DURABLE=PASS CASES=" + cases + " ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P270_SCOPE=DEVELOPMENT_ONLY SYNTHETIC_ONLY PRODUCTION=HOLD");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine("P270_HOLD " + error.GetType().Name + " " + error.Message); return 1; }
    }
}
