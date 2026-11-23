using System;
using System.Diagnostics;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Nayeon.ByokC1.Service;
using Owner = Nayeon.ByokC1.Service.HostedDisposableWinCred.ServiceOwnedAdmission;

internal static class P315CrashRecoveryTests
{
    private const string Ready = "P315_CHILD_READY";
    private static void Check(bool value)
    { if (!value) throw new InvalidOperationException("P315 HOLD"); }
    private static void Refuse(Action action)
    {
        bool denied = false;
        try { action(); } catch (InvalidOperationException) { denied = true; }
        Check(denied);
    }
    private static string Fresh() { return Guid.NewGuid().ToString("N"); }
    // Preserve P314's exact journal format, entropy and disposable namespace.
    private static string Root(string id) { return Path.Combine(Path.GetTempPath(), "nayeon-p314-" + id); }
    private static string Leaf(string id) { return Path.Combine(Root(id), "intent.dpapi"); }
    private static Owner New(string id, bool reopen)
    { return new Owner(id, true, true, reopen, Owner.P315Mode.HostedCrashOnly); }
    private static T Field<T>(Owner owner, string name)
    { return (T)typeof(Owner).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner); }
    private static void NoEffect(Owner owner)
    { Check(Field<HostedDisposableWinCred>(owner, "vault").State == HostedDisposableWinCred.VaultState.Uninitialized); }
    private static void Absent(string id)
    { using (var owner = New(id, false)) { NoEffect(owner); Check(!owner.MayHaveEffect); } }
    private static void Regular(string path, bool directory)
    {
        var attributes = File.GetAttributes(path);
        Check((attributes & FileAttributes.ReparsePoint) == 0 &&
            ((attributes & FileAttributes.Directory) != 0) == directory);
    }
    private static void Cleanup(string id)
    {
        DurableIntentJournal.ValidateId(id);
        Absent(id);
        string root = Root(id), leaf = Leaf(id);
        Check(Path.GetDirectoryName(root).TrimEnd('\\') == Path.GetTempPath().TrimEnd('\\'));
        for (string ancestor = Path.GetDirectoryName(root); ancestor != null; ancestor = Path.GetDirectoryName(ancestor))
            Regular(ancestor, true);
        if (!Directory.Exists(root)) { Check(!File.Exists(root)); return; }
        Regular(root, true);
        string[] entries = Directory.GetFileSystemEntries(root);
        Check(entries.Length <= 1 && (entries.Length == 0 || entries[0] == leaf));
        if (entries.Length == 1) { Regular(leaf, false); File.Delete(leaf); Check(!File.Exists(leaf)); }
        Directory.Delete(root, false);
        Check(!Directory.Exists(root) && !File.Exists(root));
        Absent(id);
    }
    private static int Child(string id)
    {
        HostedDisposableWinCred.RequireHostedP315();
        DurableIntentJournal.ValidateId(id);
        Check(!Directory.Exists(Root(id)) && !File.Exists(Root(id)));
        using (var owner = New(id, false))
        {
            object approval = owner.Issue();
            var dispatch = new Thread(delegate() {
                try { owner.Dispatch(approval); }
                catch (InvalidOperationException) { } // Expected safe timeout; never native.
            }) { IsBackground = true };
            dispatch.Start();
            Check(owner.WaitBeforeNative());
            // Event acquire follows WriteVerify/Flush(true)/readback while dispatch owns monitor.
            var journal = Field<DurableIntentJournal>(owner, "journal");
            Check(journal.InFlight && journal.RecoveryRequired);
            NoEffect(owner);
            Check(File.Exists(Leaf(id)) && dispatch.IsAlive);
            Console.Out.WriteLine(Ready);
            Console.Out.Flush();
            // No release signal. Timeout AND simulateCrash each independently deny Add.
            Thread.Sleep(15000);
            Check(dispatch.Join(1000));
        }
        throw new InvalidOperationException("P315 child survived; HOLD.");
    }
    private static void SameBytes(string id, byte[] witness)
    { Check(witness.SequenceEqual(ReadWitness(id))); }
    private static byte[] ReadWitness(string id)
    {
        Regular(Root(id), true); Regular(Leaf(id), false);
        using (var stream = new FileStream(Leaf(id), FileMode.Open, FileAccess.Read, FileShare.None))
        {
            Check(stream.Length > 4 && stream.Length <= 16384);
            byte[] bytes = new byte[(int)stream.Length];
            int offset = 0;
            while (offset < bytes.Length)
            {
                int count = stream.Read(bytes, offset, bytes.Length - offset);
                Check(count > 0); offset += count;
            }
            Check(stream.ReadByte() == -1);
            return bytes;
        }
    }
    private static void CrossProcess()
    {
        string id = Fresh();
        Process child = null;
        Task<string> stdout = null, stderr = null;
        try
        {
            Absent(id);
            Check(!Directory.Exists(Root(id)) && !File.Exists(Root(id)));
            string exe = Assembly.GetExecutingAssembly().Location;
            Check(Path.GetFullPath(exe) == Process.GetCurrentProcess().MainModule.FileName);
            var start = new ProcessStartInfo(exe, "--child-before-native " + id) {
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true };
            child = Process.Start(start); // Only this exact process object is ever terminated.
            stdout = ReadBounded(child.StandardOutput, Ready + Environment.NewLine);
            stderr = ReadBounded(child.StandardError, "");
            var watch = Stopwatch.StartNew();
            // ReadBounded reports marker separately; no unbounded ReadLine/ReadToEnd.
            while (Volatile.Read(ref markerSeen) == 0)
            {
                Check(watch.ElapsedMilliseconds < 10000 && !child.HasExited && !stdout.IsCompleted);
                Thread.Sleep(10);
            }
            Check(!child.HasExited && !stderr.IsFaulted && !stdout.IsFaulted);
            child.Kill();
            Check(child.WaitForExit(5000));
            Check(Task.WaitAll(new Task[] { stdout, stderr }, 5000));
            Check(stdout.Result == Ready + Environment.NewLine && stderr.Result == "");
            byte[] witness = ReadWitness(id);
            try
            {
                Check(witness.Length > 4 && witness.Length <= 16384);
                // First reopen is in the surviving parent, after killed child's handles are gone.
                using (var readOnly = new DurableIntentJournal(id, true))
                    Check(readOnly.InFlight && readOnly.RecoveryRequired);
                SameBytes(id, witness);
                Absent(id);
                using (var owner = New(id, true))
                {
                    Check(owner.RecoveryRequired && !owner.MayHaveEffect);
                    Refuse(delegate { owner.Issue(); });
                    Refuse(delegate { owner.Dispatch(new object()); });
                }
                SameBytes(id, witness);
                using (var owner = New(id, false))
                {
                    object approval = owner.Issue();
                    Refuse(delegate { owner.Dispatch(approval); });
                    Check(owner.RecoveryRequired); NoEffect(owner);
                    Refuse(delegate { owner.Dispatch(approval); });
                    Refuse(delegate { owner.Issue(); });
                }
                SameBytes(id, witness);
                using (var readOnly = new DurableIntentJournal(id, true))
                    Check(readOnly.InFlight && readOnly.RecoveryRequired);
                SameBytes(id, witness);
            }
            finally { Array.Clear(witness, 0, witness.Length); }
        }
        finally
        {
            // Failure cleanup never uses a process name, PID lookup, shell or another process.
            try
            {
                if (child != null && !child.HasExited) { child.Kill(); Check(child.WaitForExit(5000)); }
                if (stdout != null && stderr != null)
                    Check(Task.WaitAll(new Task[] { stdout, stderr }, 5000));
            }
            finally { if (child != null) child.Dispose(); Cleanup(id); }
        }
    }
    private static int markerSeen;
    private static async Task<string> ReadBounded(StreamReader reader, string expected)
    {
        char[] buffer = new char[1];
        int count = 0;
        while (await reader.ReadAsync(buffer, 0, 1).ConfigureAwait(false) != 0)
        {
            Check(count < expected.Length && buffer[0] == expected[count]);
            count++;
            if (expected.Length != 0 && count == expected.Length) Interlocked.Exchange(ref markerSeen, 1);
        }
        Check(count == expected.Length);
        return expected;
    }
    private static void PureContexts()
    {
        var env = new Dictionary<string, string> {
            {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"}, {"RUNNER_ENVIRONMENT", "github-hosted"},
            {"GITHUB_EVENT_NAME", "pull_request"}, {"GITHUB_REPOSITORY", "krismcan/Mark-LV"},
            {"GITHUB_HEAD_REF", "byok-c1-p315-hosted-crash-recovery-20261123"},
            {"GITHUB_BASE_REF", "byok-c1-p314-hosted-durable-native-intent-20261123"}, {"P315_SYNTHETIC_HOSTED_ONLY", "1"} };
        string sha = new string('a', 40);
        var repo = new Dictionary<string, object> { {"full_name", "krismcan/Mark-LV"}, {"fork", true}, {"id", 1402212689} };
        var head = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_HEAD_REF"]}, {"sha", sha} };
        var baseSide = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_BASE_REF"]}, {"sha", "8ea85bc2682183a95845c5b14a7986bb7200f5ec"} };
        var pr = new Dictionary<string, object> { {"draft", true}, {"head", head}, {"base", baseSide} };
        var root = new Dictionary<string, object> { {"repository", repo}, {"pull_request", pr} };
        var serializer = new JavaScriptSerializer();
        Action validate = delegate { HostedDisposableWinCred.ValidateContextP315(env, serializer.Serialize(root), sha); };
        validate(); Check(true); // Pure predicate: no OS or native access.
        foreach (string flag in new[] { "P312_SYNTHETIC_HOSTED_ONLY", "P313_SYNTHETIC_HOSTED_ONLY", "P314_SYNTHETIC_HOSTED_ONLY" })
        { env[flag] = "1"; Refuse(validate); env.Remove(flag); }
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
        baseSide["sha"] = sha; Refuse(validate); baseSide["sha"] = "8ea85bc2682183a95845c5b14a7986bb7200f5ec";
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
        Refuse(delegate { HostedDisposableWinCred.ValidateContextP315(env, serializer.Serialize(root), "bad"); });
        Refuse(delegate { HostedDisposableWinCred.ValidateContextP315(env, new string(' ', 65536), sha); });
    }

    private static void Negatives()
    {
        Check(typeof(Owner).Assembly != Assembly.GetExecutingAssembly());
        Check(Assembly.GetExecutingAssembly().GetName().Name == "P315.CrashRecovery.Tests");
        foreach (string id in new[] { null, "", "../x", Guid.Empty.ToString("N"), Guid.NewGuid().ToString("D") })
            Refuse(delegate { New(id, false); });
        Refuse(delegate { new Owner(Fresh(), false, true, false, Owner.P315Mode.HostedCrashOnly); });
        Refuse(delegate { new Owner(Fresh(), true, false, false, Owner.P315Mode.HostedCrashOnly); });
        Refuse(delegate { new Owner(Fresh(), true, true, false, (Owner.P315Mode)1); });
        foreach (string flag in new[] { "P313_SYNTHETIC_HOSTED_ONLY", "P314_SYNTHETIC_HOSTED_ONLY" })
        {
            try { Environment.SetEnvironmentVariable(flag, "1"); Refuse(HostedDisposableWinCred.RequireHostedP315); }
            finally { Environment.SetEnvironmentVariable(flag, null); }
        }
        string brake = Environment.GetEnvironmentVariable("P315_SYNTHETIC_HOSTED_ONLY");
        try
        {
            Environment.SetEnvironmentVariable("P315_SYNTHETIC_HOSTED_ONLY", null);
            Refuse(delegate { New(Fresh(), false); });
        }
        finally { Environment.SetEnvironmentVariable("P315_SYNTHETIC_HOSTED_ONLY", brake); }
        for (int control = 0; control < 3; control++)
        {
            string id = Fresh();
            try
            {
                using (var owner = New(id, false))
                {
                    object approval = owner.Issue();
                    var result = control == 0 ? owner.Revoke() : control == 1 ? owner.Stop() : owner.Fault();
                    Check(result == (control == 0 ? Owner.ControlResult.Revoked : control == 1 ? Owner.ControlResult.Stopped : Owner.ControlResult.Faulted));
                    Refuse(delegate { owner.Dispatch(approval); });
                    NoEffect(owner); Check(!Directory.Exists(Root(id)));
                }
            }
            finally { Cleanup(id); }
        }
        // Corruption and foreign-ID DPAPI witness must refuse both reopen and fresh dispatch.
        for (int kind = 0; kind < 2; kind++)
        {
            string id = Fresh(), other = Fresh();
            try
            {
                using (var journal = new DurableIntentJournal(id, false)) journal.RecordInFlightAndFlushVerify();
                if (kind == 0) File.WriteAllBytes(Leaf(id), new byte[7]);
                else
                {
                    using (var journal = new DurableIntentJournal(other, false)) journal.RecordInFlightAndFlushVerify();
                    File.WriteAllBytes(Leaf(id), ReadWitness(other));
                }
                byte[] witness = ReadWitness(id);
                Refuse(delegate { using (var owner = New(id, true)) {} });
                using (var owner = New(id, false))
                {
                    object approval = owner.Issue();
                    Refuse(delegate { owner.Dispatch(approval); }); NoEffect(owner);
                }
                SameBytes(id, witness); Array.Clear(witness, 0, witness.Length);
            }
            finally { Cleanup(id); Cleanup(other); }
        }
    }
    public static int Main(string[] args)
    {
        try
        {
            HostedDisposableWinCred.RequireHostedP315();
            if (args.Length == 2 && args[0] == "--child-before-native") return Child(args[1]);
            Check(args.Length == 0);
            PureContexts(); Negatives(); CrossProcess();
            Console.WriteLine("P315 CROSS PROCESS TESTS PASS cleanup=verified");
            return 0;
        }
        catch { Console.Error.WriteLine("P315 HOLD; crash or cleanup evidence unproven."); return 1; }
    }
}
