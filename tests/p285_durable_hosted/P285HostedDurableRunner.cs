#if !DEBUG || RELEASE || !C1_P285_HOSTED_ROOT_REVIEW_ONLY
#error P285_HOSTED_TEST_ONLY_DEBUG_AND_OPT_IN_REQUIRED
#endif
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

// Disposable development test host. Environment claims are accident barriers,
// not authenticated authority. The exact draft-PR workflow supplies custody.
internal static class P285HostedDurableRunner
{
    private const string Holds = "ALL_SECURITY_GATES=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=OPEN P76_P216=UNWAIVED";
    private static readonly List<string> roots = new List<string>();
    private static readonly List<string> expected = CaseNames();
    private static readonly object outputGate = new object();
    private static readonly StringBuilder stdout = new StringBuilder(), stderr = new StringBuilder();
    private static int passed, aggregates, holds, outputChars;
    private static bool invalidOutput;
    private static bool childException, redactedStderr;
    private static readonly List<string> childStack = new List<string>(2);
    private static string temp, evidence;
    private static SecurityIdentifier sid;
    private static void Require(bool value) { if (!value) throw new InvalidOperationException(); }
    private static string Env(string key) { return Environment.GetEnvironmentVariable(key); }
    private static void RequireAbsent(string path)
    {
        // Exists() suppresses some errors and can miss dangling reparse entries.
        try { File.GetAttributes(path); }
        catch (FileNotFoundException) { return; }
        catch (DirectoryNotFoundException) { return; }
        throw new InvalidOperationException();
    }
    private static string Full(string path)
    {
        Require(!String.IsNullOrEmpty(path) && Path.IsPathRooted(path) &&
            path.Length > 3 && path[1] == ':' && path[2] == '\\' && path.IndexOf('"') < 0);
        string result = Path.GetFullPath(path).TrimEnd('\\');
        Require(String.Equals(path.TrimEnd('\\'), result, StringComparison.OrdinalIgnoreCase));
        return result;
    }
    private static void NoLinks(string path)
    {
        for (string p = path; p != null; p = Path.GetDirectoryName(p))
            Require((File.GetAttributes(p) & FileAttributes.ReparsePoint) == 0);
        Require(new DriveInfo(Path.GetPathRoot(path)).DriveType == DriveType.Fixed);
    }
    private static void RootShape(string root)
    {
        Require(String.Equals(Path.GetDirectoryName(root), temp, StringComparison.OrdinalIgnoreCase));
        string name = Path.GetFileName(root); Guid id;
        Require(name.StartsWith("nayeon-p270-", StringComparison.Ordinal) &&
            Guid.TryParseExact(name.Substring(12), "N", out id));
        NoLinks(root);
        Require((File.GetAttributes(root) & FileAttributes.Directory) != 0);
        DirectorySecurity acl = Directory.GetAccessControl(root);
        Require(acl.AreAccessRulesProtected && acl.GetOwner(typeof(SecurityIdentifier)).Equals(sid));
        AuthorizationRuleCollection rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
        Require(rules.Count == 1);
        FileSystemAccessRule rule = (FileSystemAccessRule)rules[0];
        Require(!rule.IsInherited && rule.IdentityReference.Equals(sid) &&
            rule.AccessControlType == AccessControlType.Allow && rule.FileSystemRights == FileSystemRights.FullControl &&
            rule.InheritanceFlags == (InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit) &&
            rule.PropagationFlags == PropagationFlags.None);
    }
    private static void Prepare()
    {
        for (int i = 0; i < 129; i++)
        {
            string root = Path.Combine(temp, "nayeon-p270-" + Guid.NewGuid().ToString("N"));
            RequireAbsent(root); Require(!roots.Contains(root));
            // Exact proven P270 Scope() pattern; applies only at new creation.
            DirectorySecurity acl = new DirectorySecurity();
            acl.SetOwner(sid); acl.SetAccessRuleProtection(true, false);
            acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None, AccessControlType.Allow));
            Directory.CreateDirectory(root, acl);
            roots.Add(root); // Only successfully created roots enter cleanup custody.
            RootShape(root);
            Require(Directory.GetFileSystemEntries(root).Length == 0);
        }
        Require(roots.Count == 129);
    }
    private static bool Cleanup()
    {
        bool ok = true;
        foreach (string root in roots)
        {
            try
            {
                RootShape(root);
                string[] entries = Directory.GetFileSystemEntries(root);
                Require(entries.Length <= 2);
                // Validate the entire layout before deleting any leaf. Unknown
                // entries/links remain untouched and force HOLD; never recurse.
                foreach (string entry in entries)
                {
                    string name = Path.GetFileName(entry);
                    Require(name == "journal.dpapi" || name == "anchor.dpapi");
                    Require((File.GetAttributes(entry) & (FileAttributes.ReparsePoint | FileAttributes.Directory)) == 0);
                    Require(File.GetAccessControl(entry).GetOwner(typeof(SecurityIdentifier)).Equals(sid));
                }
                foreach (string entry in entries)
                {
                    RootShape(root);
                    Require((File.GetAttributes(entry) & (FileAttributes.ReparsePoint | FileAttributes.Directory)) == 0);
                    File.Delete(entry);
                }
                RootShape(root);
                Require(Directory.GetFileSystemEntries(root).Length == 0);
                Directory.Delete(root, false);
                Require(!Directory.Exists(root) && !File.Exists(root));
            }
            catch (Exception) { ok = false; } // Continue cleanup; never turn failure into PASS.
        }
        return ok;
    }
    private static List<string> CaseNames()
    {
        List<string> names = new List<string>();
        foreach (string op in new[] { "Save", "Replace", "Delete" })
        {
            names.Add("metadata-only-then-explicit-fixture-" + op);
            for (int reason = 0; reason < 3; reason++)
                foreach (string first in new[] { "False", "True" }) names.Add("ordering-" + op + "-" + reason + "-" + first);
        }
        for (int i = 0; i < 8; i++) names.Add("mismatch-" + i);
        for (int i = 0; i < 4; i++) names.Add("invalid-issue-" + i);
        names.AddRange(new[] { "nontransferable", "expiry-before-submit", "expiry-inside-final-gate" });
        for (int i = 0; i < 8; i++) names.Add("malicious-callback-" + i);
        names.AddRange(new[] { "concurrent-submit", "callback-control-timeout", "unstarted", "nonfresh-restart", "uncertain-effect" });
        foreach (string edge in new[] { "trust", "read-journal", "read-anchor", "present", "write-journal",
            "after-journal", "write-anchor", "after-anchor", "effect-enter", "effect-return" })
            for (int i = 0; i <= 6; i++) names.Add("in-gate-" + edge + "-attack-" + i);
        names.Add("callback-is-not-consent");
        for (int i = 0; i < 5; i++) names.Add("missing-or-delete-mismatch-" + i);
        names.AddRange(new[] { "syntactically-valid-wrong-digest", "disposed-session", "durable-restart-never-rearms" });
        return names;
    }
    private static void Capture(string line, bool error)
    {
        if (line == null) return;
        lock (outputGate)
        {
            outputChars += Math.Min(line.Length, 65537) + 1;
            if (outputChars > 65536) { invalidOutput = true; return; }
            if (error)
            {
                invalidOutput = true;
                if (line == "P284_HOLD DEADLINE") stderr.AppendLine(line);
                else
                {
                    // Never retain messages, arguments or source locations. One type
                    // and two distinct literal-allowlisted methods bound diagnostics.
                    Match exception = Regex.Match(line,
                        @"\A(?:Unhandled Exception: |Unhandled exception\. )(System\.[A-Za-z][A-Za-z0-9.]{0,100}Exception):");
                    Match frame = childException ? Regex.Match(line,
                        @"\A[ \t]*at ((?:Nayeon\.ByokC1\.(?:" +
                        @"P270Development\.DurableWitness\.(?:Require|CheckHandle|Open|CheckLayout|Entropy|Read|Persist|InspectConsistent|ReadJournal|ReadAnchor|Snapshot|WriteJournal|WriteAnchor|Dispose)|" +
                        @"P271Development\.DurableDevelopmentBridge\.(?:Require|PersistPrior|CheckSnapshots|CheckComplete|Probe|Start|Prepare|Submit|Revoke|Stop|Fault|Observe|TestConsistent|TestPhase|TestCloseWitness|TestSkew|TestUntrust|TestEffectFailure|TestPoisonWitness|Dispose)|" +
                        @"P284Development\.DurableOperationAdmission\.(?:TestOnlyCreate|Start|TestMarkerDigest|Valid|Same|Issue|Submit|ProbeInsidePendingGate|Control|Revoke|Stop|Fault|Observe|TestConsistent|TestFailEffect|TestCloseWitness|TestPhase|Dispose)|" +
                        @"P282ExecutingServiceCustody\.(?:NoImpersonation|Capture|IsSyntheticRunnerUser|IsSyntheticRunner|BindSyntheticRunner))|" +
                        @"DurableOperationAdmissionTests\.(?:Create|Check|Run|Marker|Request|Later|Success|Control|Join|NoReplay|MetadataOnly|Mismatch|InvalidIssue|Foreign|Ordering|Expiry|Callback|DoubleSubmit|CallbackControlTimeout|Lifecycle|UncertainEffect|AtPoint|ExtraCases|Main)|" +
                        @"System\.(?:Threading\.(?:ThreadHelper\.(?:ThreadStart|ThreadStart_Context)|ExecutionContext\.(?:Run|RunInternal))|Security\.Principal\.(?:WindowsIdentity\.Impersonate|WindowsImpersonationContext\.(?:Undo|Dispose)))))\(") : Match.Empty;
                    if (exception.Success)
                    {
                        if (!childException) stderr.AppendLine("P285_CHILD_EXCEPTION_TYPE=" + exception.Groups[1].Value);
                        childException = true;
                    }
                    else if (frame.Success)
                    {
                        string method = frame.Groups[1].Value;
                        method = method.Substring(0, Math.Min(method.Length, 120));
                        if (childStack.Count < 2 && !childStack.Contains(method))
                        { childStack.Add(method); stderr.AppendLine("P285_CHILD_STACK_METHOD=" + method); }
                    }
                    else if (!redactedStderr)
                    { stderr.AppendLine("P285_REDACTED_STDERR=HOLD"); redactedStderr = true; }
                }
                return;
            }
            if (passed < expected.Count && line == "PASS " + expected[passed] && aggregates == 0 && holds == 0)
            { passed++; stdout.AppendLine(line); return; }
            Match aggregate = Regex.Match(line, "\\AP284_SYNTHETIC_ONLY=PASS CASES=128 ASSERTIONS=([1-9][0-9]{0,8}) BITS=(32|64)\\z");
            if (aggregate.Success && aggregate.Groups[2].Value == (IntPtr.Size * 8).ToString() &&
                passed == 128 && aggregates == 0 && holds == 0)
            { aggregates++; stdout.AppendLine(line); return; }
            if (line == Holds && passed == 128 && aggregates == 1 && holds == 0)
            { holds++; stdout.AppendLine(line); return; }
            invalidOutput = true;
            // P284's inherited failure prints an exception/stack with paths.
            // Retain only its type; never persist or forward the raw payload.
            Match failure = Regex.Match(line, "\\AP284_FAIL=(System\\.[A-Za-z][A-Za-z0-9.]*Exception)(?=:|$)");
            if (failure.Success) stdout.AppendLine("P284_FAIL_TYPE=" + failure.Groups[1].Value);
            else if (stdout.ToString().IndexOf("P285_REDACTED_STDOUT=HOLD", StringComparison.Ordinal) < 0)
                stdout.AppendLine("P285_REDACTED_STDOUT=HOLD");
        }
    }
    private static void Write(string name, string value)
    { File.WriteAllText(Path.Combine(evidence, name), value, new UTF8Encoding(false)); }
    private static string Hash(string path)
    {
        using (SHA256 sha = SHA256.Create()) using (FileStream file = File.OpenRead(path))
            return BitConverter.ToString(sha.ComputeHash(file)).Replace("-", "");
    }
    public static int Main(string[] args)
    {
        bool success = false, clean = false, childStopped = true, childStarted = false;
        Process child = null;
        string rawExit = "NOT_STARTED", failure = "NONE", stage = "host-claims", holdStage = null;
        try
        {
            stage = "host-claims";
            Require(args.Length == 0 && expected.Count == 128 && Environment.OSVersion.Platform == PlatformID.Win32NT &&
                Env("GITHUB_ACTIONS") == "true" && Env("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Env("RUNNER_OS") == "Windows" && Env("ImageOS") == "win22" && Env("P285_HOSTED_ROOTS_REVIEW_ONLY") == "1");
            stage = "process-identity";
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                Require(!identity.IsSystem && identity.User != null && identity.ImpersonationLevel == TokenImpersonationLevel.None);
                sid = identity.User;
            }
            Require(!String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) &&
                !String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase));
            stage = "temp-shape";
            temp = Full(Path.GetTempPath()); NoLinks(temp);
            // Existing OS TEMP may have an administrative/system owner. Only
            // require an existing directory on a fixed drive with no links;
            // never change its ACL. Prepare/RootShape enforce actual-user owner,
            // protected single ACE and emptiness on each new direct GUID child.
            Require((File.GetAttributes(temp) & FileAttributes.Directory) != 0);
            stage = "runner-temp";
            string runnerTemp = Full(Env("RUNNER_TEMP")); NoLinks(runnerTemp);
            string arch = IntPtr.Size == 8 ? "x64" : "x86";
            stage = "build-path";
            string build = Path.Combine(runnerTemp, "p285-build-" + arch); NoLinks(build);
            stage = "exe-identity";
            NoLinks(Assembly.GetExecutingAssembly().Location);
            string exe = Full(Env("P285_DURABLE_EXE")); NoLinks(exe);
            Require(String.Equals(exe, Path.Combine(build, "P284Durable.exe"), StringComparison.OrdinalIgnoreCase) &&
                String.Equals(Assembly.GetExecutingAssembly().Location, Path.Combine(build, "P285Host.exe"), StringComparison.OrdinalIgnoreCase));
            stage = "exe-sha";
            string pin = Env("P285_DURABLE_SHA256");
            Require(pin != null && Regex.IsMatch(pin, "\\A[A-F0-9]{64}\\z") && Hash(exe) == pin);
            stage = "evidence-root";
            string destination = Path.Combine(runnerTemp, "p285-evidence-" + arch); NoLinks(destination);
            foreach (string name in new[] { "runtime.stdout.log", "runtime.stderr.log", "runtime.exit", "host.log" })
                RequireAbsent(Path.Combine(destination, name));
            evidence = destination;
            stage = "root-create";
            Prepare();
            stage = "child-launch";
            ProcessStartInfo start = new ProcessStartInfo(exe);
            start.UseShellExecute = false; start.CreateNoWindow = true;
            start.RedirectStandardOutput = true; start.RedirectStandardError = true;
            start.WorkingDirectory = build;
            start.EnvironmentVariables.Clear();
            string windows = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
            start.EnvironmentVariables["SystemRoot"] = windows; start.EnvironmentVariables["WINDIR"] = windows;
            start.EnvironmentVariables["PATH"] = Path.Combine(windows, "System32");
            start.EnvironmentVariables["TEMP"] = temp; start.EnvironmentVariables["TMP"] = temp;
            start.EnvironmentVariables["GITHUB_ACTIONS"] = "true";
            start.EnvironmentVariables["RUNNER_ENVIRONMENT"] = "github-hosted";
            start.EnvironmentVariables["RUNNER_OS"] = "Windows";
            start.EnvironmentVariables["P284_REVIEWED_DURABLE_RUNTIME"] = "1";
            start.EnvironmentVariables["P271_HOSTED_DISPOSABLE"] = "1";
            start.EnvironmentVariables["P284_PREPROVISIONED_ROOTS"] = String.Join("|", roots.ToArray());
            Require(Hash(exe) == pin);
            child = new Process(); child.StartInfo = start;
            int outDone = 0, errDone = 0;
            {
                child.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data == null) Interlocked.Exchange(ref outDone, 1); else Capture(e.Data, false); };
                child.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data == null) Interlocked.Exchange(ref errDone, 1); else Capture(e.Data, true); };
                childStarted = child.Start(); Require(childStarted); childStopped = false;
                child.BeginOutputReadLine(); child.BeginErrorReadLine();
                stage = "child-completion";
                Require(child.WaitForExit(145000)); childStopped = true;
                rawExit = child.ExitCode.ToString(System.Globalization.CultureInfo.InvariantCulture);
                Require(SpinWait.SpinUntil(() => Volatile.Read(ref outDone) == 1 && Volatile.Read(ref errDone) == 1, 5000));
                lock (outputGate) Require(child.ExitCode == 0 && !invalidOutput && passed == 128 && aggregates == 1 && holds == 1);
            }
            success = true;
        }
        catch (Exception error) { failure = error.GetType().Name; holdStage = stage; }
        finally
        {
            if (child != null)
            {
                try
                {
                    if (childStarted)
                    {
                        if (!childStopped) { if (!child.HasExited) child.Kill(); childStopped = child.WaitForExit(5000); }
                        if (childStopped) rawExit = child.ExitCode.ToString(System.Globalization.CultureInfo.InvariantCulture);
                    }
                }
                catch (Exception) { success = false; childStopped = false; if (holdStage == null) holdStage = "child-completion"; }
                child.Dispose();
            }
            // Never touch a root while a failed-to-terminate writer may own it.
            stage = "cleanup";
            clean = childStopped && Cleanup();
            if (!clean && holdStage == null) holdStage = stage;
            success = success && clean;
            if (evidence != null)
            {
                stage = "evidence-write";
                try
                {
                    lock (outputGate) { Write("runtime.stdout.log", stdout.ToString()); Write("runtime.stderr.log", stderr.ToString()); }
                    Write("runtime.exit", rawExit + "\n");
                    Write("host.log", "P285_HOST=" + (success ? "PASS" : "HOLD") + " ROOTS_CREATED=" + roots.Count +
                        " CLEANUP=" + (clean ? "PASS" : "HOLD") + " ERROR_TYPE=" + failure + "\n" + Holds + "\n");
                }
                catch (Exception) { success = false; if (holdStage == null) holdStage = stage; }
            }
        }
        Console.WriteLine("P285_HOST=" + (success ? "PASS" : "HOLD") + " BITS=" + (IntPtr.Size * 8));
        Console.WriteLine(Holds);
        if (!success) Console.WriteLine("P285_HOST_HOLD_STAGE=" + (holdStage ?? stage));
        return success ? 0 : 1;
    }
}
