using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

[assembly: InternalsVisibleTo("P313.ProductAdmission.Tests")]

namespace Nayeon.ByokC1.Service
{
    internal sealed partial class HostedDisposableWinCred
    {
        private const string P313HeadRef = "byok-c1-p313-service-owned-vault-admission-20261123";
        private const string P313BaseRef = "byok-c1-p312-service-hosted-windows-vault-20261123";
        private const string P313BaseSha = "d980c4ef7de118a685c245e4dd915d1d9fe8ca1a";
        private sealed class P313Marker { }

        // Only the nested owner calls this overload. No caller-supplied environment authorizes it.
        private HostedDisposableWinCred(string id, P313Marker marker)
        {
            ValidateId(id); // Before all OS calls.
            Need(marker != null);
            RequireHostedP313();
            p313Session = true;
            target = Prefix + id;
            owner = Identity();
            Need(Marshal.SizeOf(typeof(Credential)) == (IntPtr.Size == 8 ? 80 : 52));
            lock (Writer) { Need(!Read(null)); }
        }
        // Pure predicate only. No injected environment reaches a native-effect constructor.
        internal static void ValidateContextP313(IDictionary<string, string> env, string json, string checkout)
        {
            Need(env != null && Sha(checkout) && checkout != P313BaseSha);
            foreach (var pair in new Dictionary<string, string> {
                {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"},
                {"RUNNER_ENVIRONMENT", "github-hosted"}, {"GITHUB_EVENT_NAME", "pull_request"},
                {"GITHUB_REPOSITORY", Repo}, {"GITHUB_HEAD_REF", P313HeadRef},
                {"GITHUB_BASE_REF", P313BaseRef}, {"P313_SYNTHETIC_HOSTED_ONLY", "1"} })
                Need(Env(env, pair.Key) == pair.Value);
            Need(json != null && json.Length > 0 && json.Length < 65536);
            var parser = new JavaScriptSerializer { MaxJsonLength = 65535, RecursionLimit = 32 };
            var root = Map(parser.DeserializeObject(json));
            var pr = Map(Field(root, "pull_request"));
            Need(Object.Equals(Field(pr, "draft"), true));
            var repository = Map(Field(root, "repository"));
            Need((string)Field(repository, "full_name") == Repo);
            Need(Object.Equals(Field(repository, "id"), 1402212689));
            var rootFork = Field(repository, "fork");
            Need(rootFork is bool);
            foreach (string side in new[] { "head", "base" })
            {
                var endpoint = Map(Field(pr, side));
                var repo = Map(Field(endpoint, "repo"));
                Need((string)Field(repo, "full_name") == Repo);
                Need(Object.Equals(Field(repo, "fork"), rootFork));
                Need(Object.Equals(Field(repo, "id"), Field(repository, "id")));
                Need((string)Field(endpoint, "ref") == (side == "head" ? P313HeadRef : P313BaseRef));
                Need((string)Field(endpoint, "sha") == (side == "head" ? checkout : P313BaseSha));
            }
        }

        internal static void RequireHostedP313()
        {
            // All cheap environment checks precede file, process, identity and native access.
            var env = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (var pair in new Dictionary<string, string> {
                {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"},
                {"RUNNER_ENVIRONMENT", "github-hosted"}, {"GITHUB_EVENT_NAME", "pull_request"},
                {"GITHUB_REPOSITORY", Repo}, {"GITHUB_HEAD_REF", P313HeadRef},
                {"GITHUB_BASE_REF", P313BaseRef}, {"P313_SYNTHETIC_HOSTED_ONLY", "1"} })
            {
                string value = Environment.GetEnvironmentVariable(pair.Key);
                Need(value == pair.Value); env.Add(pair.Key, value);
            }
            Need(Environment.OSVersion.Platform == PlatformID.Win32NT);
            string temp = Path.GetFullPath(Environment.GetEnvironmentVariable("RUNNER_TEMP") ?? "");
            string path = Path.GetFullPath(Environment.GetEnvironmentVariable("GITHUB_EVENT_PATH") ?? "");
            RegularPath(path, temp);
            Need((File.GetAttributes(path) & FileAttributes.Directory) == 0);
            string json;
            using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                Need(stream.Length > 0 && stream.Length < 65536);
                using (var reader = new StreamReader(stream, new UTF8Encoding(false, true), true)) json = reader.ReadToEnd();
            }
            // Read-only local Git witness; no remotes, shell, network or caller-injected executor.
            var start = new ProcessStartInfo("git.exe", "rev-parse --verify HEAD") {
                WorkingDirectory = Path.GetFullPath(Environment.GetEnvironmentVariable("GITHUB_WORKSPACE") ?? ""),
                UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true,
                RedirectStandardError = true };
            string checkout;
            using (var process = Process.Start(start))
            {
                if (!process.WaitForExit(5000)) { process.Kill(); Need(process.WaitForExit(5000)); Need(false); }
                Need(process.ExitCode == 0);
                char[] buffer = new char[43];
                int count = process.StandardOutput.ReadBlock(buffer, 0, buffer.Length);
                Need(count < buffer.Length); checkout = new string(buffer, 0, count).TrimEnd('\r', '\n');
            }
            ValidateContextP313(env, json, checkout);
            Identity(); // Process SID and no-impersonation validation before any WinCred access.
        }

        // This owner is test-only composition, never trusted human consent or durable admission.
        internal sealed class ServiceOwnedAdmission : IDisposable
        {
            internal enum ControlResult { Revoked, Stopped, Faulted, TooLate, HoldUnknown }
            private readonly object gate = new object();
            private readonly HostedDisposableWinCred vault;
            private readonly ManualResetEvent beforeNative;
            private readonly ManualResetEvent releaseNative;
            private readonly bool pauseBeforeNative;
            private object approval;
            private bool issued, terminal, disposed, mayHaveEffect, recoveryRequired;
            private int faultRequested;
            private const int GateWait = 2000;

            internal ServiceOwnedAdmission(string id, bool pause)
            {
                ValidateId(id);
                RequireHostedP313();
                pauseBeforeNative = pause;
                vault = new HostedDisposableWinCred(id, new P313Marker());
                beforeNative = new ManualResetEvent(false);
                releaseNative = new ManualResetEvent(false);
            }

            // Monitor itself permits recursion. Explicitly reject it and latch a terminal fault.
            private bool Enter()
            {
                if (Monitor.IsEntered(gate))
                {
                    Interlocked.Exchange(ref faultRequested, 1);
                    throw new InvalidOperationException("P313 reentry; HOLD.");
                }
                if (Monitor.TryEnter(gate, GateWait)) return true;
                Interlocked.Exchange(ref faultRequested, 1);
                return false; // No claim that a waiting control cancelled the native operation.
            }
            private void EnterRequired() { Need(Enter()); }
            internal object Issue()
            {
                EnterRequired();
                try
                {
                    Need(!disposed && !terminal && !issued && Volatile.Read(ref faultRequested) == 0);
                    issued = true;
                    approval = new object(); // Exact opaque identity, bound to this one Add lifetime.
                    return approval;
                }
                finally { Monitor.Exit(gate); }
            }
            private ControlResult Control(ControlResult result)
            {
                if (!Enter()) return ControlResult.HoldUnknown;
                try
                {
                    if (mayHaveEffect) return ControlResult.TooLate;
                    if (disposed || terminal || Volatile.Read(ref faultRequested) != 0) return ControlResult.HoldUnknown;
                    terminal = true; approval = null;
                    return result;
                }
                finally { Monitor.Exit(gate); }
            }
            internal ControlResult Revoke() { return Control(ControlResult.Revoked); }
            internal ControlResult Stop() { return Control(ControlResult.Stopped); }
            internal ControlResult Fault() { return Control(ControlResult.Faulted); }

            internal void Dispatch(object supplied)
            {
                EnterRequired();
                try
                {
                    Need(!disposed && !terminal && issued && approval != null &&
                        Object.ReferenceEquals(approval, supplied) && Volatile.Read(ref faultRequested) == 0);
                    terminal = true; approval = null;
                    // Linearization: all controls use this same monitor. Sticky BEFORE native entry.
                    mayHaveEffect = true; recoveryRequired = true;
                    if (pauseBeforeNative)
                    {
                        beforeNative.Set();
                        Need(releaseNative.WaitOne(5000)); // Fixed test rendezvous, no arbitrary callback.
                    }
                    Need(Volatile.Read(ref faultRequested) == 0);
                    vault.Add(); // Actual P312 ALPHA CredWriteW + readback, still INSIDE gate.
                    vault.Verify();
                }
                catch { terminal = true; approval = null; throw; }
                finally { Monitor.Exit(gate); }
            }
            internal bool MayHaveEffect
            { get { EnterRequired(); try { return mayHaveEffect; } finally { Monitor.Exit(gate); } } }
            internal bool RecoveryRequired
            { get { EnterRequired(); try { return recoveryRequired; } finally { Monitor.Exit(gate); } } }
            internal bool CleanupVerified
            { get { EnterRequired(); try { return disposed; } finally { Monitor.Exit(gate); } } }

            // Fixed test-only signals. Never an action/payload/adapter injection surface.
            internal bool WaitBeforeNative() { return beforeNative.WaitOne(5000); }
            internal void ReleaseNative() { releaseNative.Set(); }
            public void Dispose()
            {
                EnterRequired();
                try
                {
                    if (disposed) return;
                    terminal = true; approval = null;
                    vault.Dispose(); // Verified deletion/absence, same owner monitor.
                    disposed = true;
                    beforeNative.Dispose(); releaseNative.Dispose();
                }
                finally { Monitor.Exit(gate); }
            }
        }
    }
}
