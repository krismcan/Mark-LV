using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using System.Web.Script.Serialization;
using Nayeon.ByokC1.Service;
using Owner = Nayeon.ByokC1.Service.HostedDisposableWinCred.ServiceOwnedAdmission;

internal static class P314DurableIntentTests
{
    private static int count, cases;
    private static void Check(bool value)
    { if (!value) throw new InvalidOperationException("P314 assertion; HOLD."); count++; }
    private static void Refuse(Action action)
    {
        bool refused = false;
        try { action(); } catch (InvalidOperationException) { refused = true; }
        Check(refused);
    }
    private static string Fresh() { return Guid.NewGuid().ToString("N"); }
    private static string Root(string id) { return Path.Combine(Path.GetTempPath(), "nayeon-p314-" + id); }
    private static string Leaf(string id) { return Path.Combine(Root(id), "intent.dpapi"); }
    private static T Field<T>(Owner owner, string name)
    { return (T)typeof(Owner).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner); }
    private static void NoEffect(Owner owner)
    { Check(Field<HostedDisposableWinCred>(owner, "vault").State == HostedDisposableWinCred.VaultState.Uninitialized); }
    private static Owner New(string id, bool pause, bool crash)
    { return new Owner(id, pause, crash, false); }
    private static void Absent(string id)
    {
        using (var owner = New(id, false, false)) { NoEffect(owner); Check(!owner.MayHaveEffect); }
    }
    private static void Cleanup(string id)
    {
        // Exact fixture only, nonrecursive, after native absence was independently checked.
        Absent(id);
        string root = Root(id);
        if (!Directory.Exists(root)) { Check(!File.Exists(root)); return; }
        Check(Path.GetDirectoryName(root).TrimEnd('\\') == Path.GetTempPath().TrimEnd('\\'));
        Check((File.GetAttributes(root) & FileAttributes.ReparsePoint) == 0);
        string leaf = Leaf(id);
        if (File.Exists(leaf))
        {
            Check((File.GetAttributes(leaf) & (FileAttributes.Directory | FileAttributes.ReparsePoint)) == 0);
            File.Delete(leaf);
            Check(!File.Exists(leaf));
        }
        Check(Directory.GetFileSystemEntries(root).Length == 0);
        Directory.Delete(root, false);
        Check(!Directory.Exists(root) && !File.Exists(root));
    }
    private static void ReadOnlyNegatives()
    {
        Check(typeof(Owner).Assembly != Assembly.GetExecutingAssembly());
        Check(typeof(Owner).DeclaringType == typeof(HostedDisposableWinCred));
        Check(Assembly.GetExecutingAssembly().GetName().Name == "P314.DurableIntent.Tests");
        foreach (string id in new[] { null, "", "wrong", Guid.Empty.ToString("N"), Guid.NewGuid().ToString("D"), "../" + Fresh() })
            Refuse(delegate { new Owner(id, false, false, false); });
        string brake = Environment.GetEnvironmentVariable("P314_SYNTHETIC_HOSTED_ONLY");
        try
        {
            Environment.SetEnvironmentVariable("P314_SYNTHETIC_HOSTED_ONLY", null);
            Refuse(HostedDisposableWinCred.RequireHostedP314);
            Refuse(delegate { new Owner(Fresh(), false, false, false); });
        }
        finally { Environment.SetEnvironmentVariable("P314_SYNTHETIC_HOSTED_ONLY", brake); }        var env = new Dictionary<string, string> {
            {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"}, {"RUNNER_ENVIRONMENT", "github-hosted"},
            {"GITHUB_EVENT_NAME", "pull_request"}, {"GITHUB_REPOSITORY", "krismcan/Mark-LV"},
            {"GITHUB_HEAD_REF", "byok-c1-p314-hosted-durable-native-intent-20261123"},
            {"GITHUB_BASE_REF", "byok-c1-p313-service-owned-vault-admission-20261123"}, {"P314_SYNTHETIC_HOSTED_ONLY", "1"} };
        string sha = new string('a', 40);
        var repo = new Dictionary<string, object> { {"full_name", "krismcan/Mark-LV"}, {"fork", true}, {"id", 1402212689} };
        var head = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_HEAD_REF"]}, {"sha", sha} };
        var baseSide = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_BASE_REF"]}, {"sha", "4fcf75666f8bd055f940eb5bbee01d154bf43c6b"} };
        var pr = new Dictionary<string, object> { {"draft", true}, {"head", head}, {"base", baseSide} };
        var root = new Dictionary<string, object> { {"repository", repo}, {"pull_request", pr} };
        var serializer = new JavaScriptSerializer();
        Action validate = delegate { HostedDisposableWinCred.ValidateContextP314(env, serializer.Serialize(root), sha); };
        validate(); count++; // Pure predicate: no OS or native access.
        foreach (string key in env.Keys.ToArray())
        { string value = env[key]; env[key] = "denied"; Refuse(validate); env[key] = value; }
        pr["draft"] = false; Refuse(validate); pr["draft"] = true;
        repo["fork"] = false; Refuse(validate); repo["fork"] = true;
        repo["fork"] = "true"; Refuse(validate); repo["fork"] = true;
        foreach (var endpoint in new[] { head, baseSide })
        {
            var endpointRepo = (Dictionary<string, object>)endpoint["repo"];
            endpointRepo["id"] = 456; Refuse(validate); endpointRepo["id"] = 1402212689;
            endpointRepo["fork"] = false; Refuse(validate); endpointRepo["fork"] = true;
            endpointRepo["fork"] = "true"; Refuse(validate); endpointRepo["fork"] = true;
        }
        repo["fork"] = false;
        ((Dictionary<string, object>)head["repo"])["fork"] = false;
        ((Dictionary<string, object>)baseSide["repo"])["fork"] = false;
        Refuse(validate);
        repo["fork"] = true;
        ((Dictionary<string, object>)head["repo"])["fork"] = true;
        ((Dictionary<string, object>)baseSide["repo"])["fork"] = true;
        head["sha"] = new string('b', 40); Refuse(validate); head["sha"] = sha;
        baseSide["sha"] = sha; Refuse(validate); baseSide["sha"] = "4fcf75666f8bd055f940eb5bbee01d154bf43c6b";
        head["repo"] = new Dictionary<string, object> { {"full_name", "other/repo"}, {"fork", false}, {"id", 456} };
        Refuse(validate); head["repo"] = repo;
        foreach (var endpoint in new[] { head, baseSide })
        {
            object saved = endpoint["ref"]; endpoint["ref"] = "wrong"; Refuse(validate); endpoint["ref"] = saved;
            var endpointRepo = (Dictionary<string, object>)endpoint["repo"];
            saved = endpointRepo["full_name"]; endpointRepo["full_name"] = "wrong/repo"; Refuse(validate); endpointRepo["full_name"] = saved;
        }
        var headRepo = (Dictionary<string, object>)head["repo"];
        var baseRepo = (Dictionary<string, object>)baseSide["repo"];
        repo["id"] = 456; headRepo["id"] = 456; baseRepo["id"] = 456;
        Refuse(validate); // Matching foreign IDs must still refuse the fixed authorized repository.
        repo["id"] = 1402212689; headRepo["id"] = 1402212689; baseRepo["id"] = 1402212689;
        Refuse(delegate { HostedDisposableWinCred.ValidateContextP314(env, serializer.Serialize(root), "bad"); });
        Refuse(delegate { HostedDisposableWinCred.ValidateContextP314(env, new string(' ', 65536), sha); });
    }

    private static Owner.ControlResult Control(Owner owner, int kind)
    { return kind == 0 ? owner.Revoke() : kind == 1 ? owner.Stop() : owner.Fault(); }

    private static void ControlFirst()
    {
        for (int kind = 0; kind < 3; kind++)
        {
            string id = Fresh();
            try
            {
                using (var owner = New(id, false, false))
                {
                    object approval = owner.Issue();
                    Check(Control(owner, kind) == (kind == 0 ? Owner.ControlResult.Revoked :
                        kind == 1 ? Owner.ControlResult.Stopped : Owner.ControlResult.Faulted));
                    Refuse(delegate { owner.Dispatch(approval); });
                    NoEffect(owner);
                    Check(!owner.MayHaveEffect && !owner.RecoveryRequired && !Directory.Exists(Root(id)));
                    Refuse(delegate { owner.Issue(); });
                    owner.Dispose(); Check(owner.CleanupVerified);
                }
            }
            finally { Cleanup(id); }
            cases++;
        }
    }
    private static void DispatchFirst(bool crash, int control)
    {
        string id = Fresh();
        try
        {
            using (var owner = New(id, true, crash))
            {
                object approval = owner.Issue();
                Exception failure = null, controlFailure = null;
                Owner.ControlResult late = Owner.ControlResult.HoldUnknown;
                Thread controller = null;
                var thread = new Thread(delegate() {
                    try { owner.Dispatch(approval); } catch (Exception ex) { failure = ex; }
                }) { IsBackground = true };
                thread.Start();
                try
                {
                    Check(owner.WaitBeforeNative());
                    NoEffect(owner); // Actual adapter is still uninitialized at post-flush rendezvous.
                    var journal = Field<DurableIntentJournal>(owner, "journal");
                    Check(journal.InFlight && journal.RecoveryRequired);
                    Check(File.Exists(Leaf(id)));
                    bool exclusive = false;
                    try { using (var ignored = File.OpenRead(Leaf(id))) {} }
                    catch (IOException) { exclusive = true; }
                    Check(exclusive);
                    using (var attempted = new ManualResetEvent(false))
                    {
                        controller = new Thread(delegate() {
                            attempted.Set();
                            try { late = Control(owner, control); } catch (Exception ex) { controlFailure = ex; }
                        }) { IsBackground = true };
                        controller.Start();
                        Check(attempted.WaitOne(5000));
                    }
                }
                finally
                {
                    owner.ReleaseNative();
                    Check(thread.Join(10000));
                }
                Check(controller != null && controller.Join(10000));
                Check(controlFailure == null && late == Owner.ControlResult.TooLate);
                Check(crash ? failure is InvalidOperationException : failure == null);
                Check(owner.MayHaveEffect && owner.RecoveryRequired);
                if (crash) NoEffect(owner);
                else Check(Field<HostedDisposableWinCred>(owner, "vault").State == HostedDisposableWinCred.VaultState.Saved);
                Check(Control(owner, control) == Owner.ControlResult.TooLate);
                Refuse(delegate { owner.Dispatch(approval); });
                Refuse(delegate { owner.Issue(); });
                owner.Dispose(); Check(owner.CleanupVerified);
            }
            Absent(id); // Real native absence, no inspection of any other target.
            byte[] bytes = File.ReadAllBytes(Leaf(id));
            string raw = System.Text.Encoding.UTF8.GetString(bytes);
            Check(bytes.Length <= 16384 && !raw.Contains("P314|IN_FLIGHT|") && !raw.Contains(id));
            Array.Clear(bytes, 0, bytes.Length);
            using (var readOnly = new DurableIntentJournal(id, true))
            {
                Check(readOnly.InFlight && readOnly.RecoveryRequired);
                Refuse(readOnly.RecordInFlightAndFlushVerify);
                Refuse(readOnly.RecordInFlightAndFlushVerify);
            }
            using (var reopened = new Owner(id, false, false, true))
            {
                Check(reopened.RecoveryRequired && !reopened.MayHaveEffect);
                Refuse(delegate { reopened.Issue(); });
                Refuse(delegate { reopened.Dispatch(new object()); });
            }
            // A caller selecting "new" cannot overwrite an existing durable intent.
            using (var second = New(id, false, false))
            {
                object approval = second.Issue();
                Refuse(delegate { second.Dispatch(approval); });
                Check(second.RecoveryRequired);
                NoEffect(second);
            }
            using (var readOnly = new DurableIntentJournal(id, true))
                Check(readOnly.InFlight && readOnly.RecoveryRequired);
        }
        finally { Cleanup(id); }
        cases++;
    }
    private static void JournalFailures()
    {
        // Root collision wins before IDLE or native: never adopt/rewrite an existing root.
        string id = Fresh();
        try
        {
            Directory.CreateDirectory(Root(id));
            using (var owner = New(id, false, false))
            {
                object approval = owner.Issue();
                Refuse(delegate { owner.Dispatch(approval); });
                Check(owner.MayHaveEffect && owner.RecoveryRequired);
                NoEffect(owner);
                Check(!File.Exists(Leaf(id)));
                Refuse(delegate { owner.Dispatch(approval); });
            }
        }
        finally { Cleanup(id); }
        cases++;

        for (int kind = 0; kind < 4; kind++)
        {
            id = Fresh();
            try
            {
                using (var journal = new DurableIntentJournal(id, false))
                {
                    journal.RecordInFlightAndFlushVerify();
                    Check(journal.InFlight && journal.RecoveryRequired);
                    Refuse(journal.RecordInFlightAndFlushVerify);
                }
                if (kind == 0)
                {
                    using (var f = new FileStream(Leaf(id), FileMode.Open, FileAccess.Write, FileShare.None))
                    { f.SetLength(7); f.Flush(true); }
                }
                else if (kind == 1)
                {
                    byte[] bytes = File.ReadAllBytes(Leaf(id));
                    bytes[bytes.Length / 2] ^= 0x40;
                    using (var f = new FileStream(Leaf(id), FileMode.Open, FileAccess.Write, FileShare.None))
                    { f.Write(bytes, 0, bytes.Length); f.Flush(true); }
                }
                else if (kind == 2)
                {
                    var acl = File.GetAccessControl(Leaf(id));
                    acl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier(WellKnownSidType.WorldSid, null),
                        FileSystemRights.Read, AccessControlType.Allow));
                    File.SetAccessControl(Leaf(id), acl);
                }
                else
                {
                    // Valid DPAPI from another ID/root must not authenticate here.
                    string other = Fresh();
                    try
                    {
                        using (var j = new DurableIntentJournal(other, false)) j.RecordInFlightAndFlushVerify();
                        File.WriteAllBytes(Leaf(id), File.ReadAllBytes(Leaf(other)));
                    }
                    finally { Cleanup(other); }
                }
                Refuse(delegate { using (var reopened = new DurableIntentJournal(id, true)) {} });
                using (var owner = New(id, false, false))
                {
                    object approval = owner.Issue();
                    Refuse(delegate { owner.Dispatch(approval); });
                    NoEffect(owner); Check(owner.RecoveryRequired);
                    Refuse(delegate { owner.Dispatch(approval); });
                }
            }
            finally { Cleanup(id); }
            cases++;
        }
    }
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CreateSymbolicLinkW(string link, string target, uint flags);
    private static void ReparseDenied()
    {
        string id = Fresh(), other = Fresh();
        try
        {
            using (var journal = new DurableIntentJournal(id, false)) journal.RecordInFlightAndFlushVerify();
            using (var journal = new DurableIntentJournal(other, false)) journal.RecordInFlightAndFlushVerify();
            File.Delete(Leaf(id));
            Check(CreateSymbolicLinkW(Leaf(id), Leaf(other), 0)); // Required; no skip or fallback.
            try
            {
                Refuse(delegate { using (var reopened = new DurableIntentJournal(id, true)) {} });
                using (var owner = New(id, false, false))
                {
                    object approval = owner.Issue();
                    Refuse(delegate { owner.Dispatch(approval); });
                    NoEffect(owner);
                }
            }
            finally
            {
                Check((File.GetAttributes(Leaf(id)) & FileAttributes.ReparsePoint) != 0);
                Absent(id);
                File.Delete(Leaf(id)); // Delete link itself, never target.
            }
        }
        finally { Cleanup(id); Cleanup(other); }
        cases++;
    }
    public static int Main()
    {
        try
        {
            HostedDisposableWinCred.RequireHostedP314(); // Never local/manual/native execution.
            Check(Environment.GetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY") == null &&
                Environment.GetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY") == null);
            ReadOnlyNegatives();
            foreach (string id in new[] { null, "", "../x", Guid.Empty.ToString("N"),
                Guid.NewGuid().ToString("D"), new string('A', 32) })
                Refuse(delegate { DurableIntentJournal.ValidateId(id); });
            cases += 2; // Predicate and UUID groups.
            ControlFirst();
            for (int kind = 0; kind < 3; kind++) DispatchFirst(false, kind);
            DispatchFirst(true, 0);
            JournalFailures();
            ReparseDenied();
            Check(count > 100 && count < 10000 && cases == 15);
            Console.WriteLine("P314 DURABLE INTENT TESTS PASS cleanup=verified count=15");
            return 0;
        }
        catch
        {
            Console.Error.WriteLine("P314 FAIL; cleanup or durable/native evidence unproven; HOLD.");
            return 1;
        }
    }
}
