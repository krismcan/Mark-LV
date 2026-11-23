using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;

[assembly: InternalsVisibleTo("P312.ProductVault.Tests")]

namespace Nayeon.ByokC1.Service
{
    // Inert product-assembly foundation. No service/IPC factory or production caller.
    // Unsigned friend identity and hosted environment are test brakes, NOT authentication.
    internal sealed partial class HostedDisposableWinCred : IDisposable
    {
        private const string Prefix = "Nayeon.P312.Disposable.";
        private const string Repo = "krismcan/Mark-LV";
        private const string HeadRef = "byok-c1-p312-service-hosted-windows-vault-20261123";
        private const string BaseRef = "byok-c1-p311-crosslanguage-synthetic-20261123";
        private const string BaseSha = "c430fafba1dc5890e59ade3f96c5cba13e5797c5";
        private const string Alpha = "P312-SYNTHETIC-TEST-ALPHA";
        private const string Beta = "P312-SYNTHETIC-TEST-BETA";
        // All instances share a writer lock. Dispose cannot overlap an effect.
        private static readonly object Writer = new object();
        internal enum VaultState { Uninitialized, Saved, Replaced, Deleted, Faulted, Disposed }
        private VaultState state;
        private readonly string target;
        private readonly SecurityIdentifier owner;
        private bool attempted;
        private readonly bool p313Session;
        private readonly bool p314Session;
        private readonly bool p315Session;

        private static void Need(bool condition)
        { if (!condition) throw new InvalidOperationException("P312 refused; HOLD."); }

        internal static void ValidateId(string id)
        {
            Guid value;
            Need(id != null && Guid.TryParseExact(id, "N", out value));
            Need(Guid.TryParseExact(id, "N", out value) && value != Guid.Empty && id == value.ToString("N"));
        }

        private static object Field(IDictionary<string, object> map, string key)
        { object value; Need(map != null && map.ContainsKey(key)); map.TryGetValue(key, out value); return value; }
        private static IDictionary<string, object> Map(object value)
        { var map = value as IDictionary<string, object>; Need(map != null); return map; }
        private static string Env(IDictionary<string, string> env, string key)
        { string value; return env.TryGetValue(key, out value) ? value : null; }
        private static bool Sha(string value)
        {
            if (value == null || value.Length != 40) return false;
            foreach (char c in value) if (!(c >= '0' && c <= '9') && !(c >= 'a' && c <= 'f')) return false;
            return true;
        }

        // Pure predicate only. No injected environment reaches a native-effect constructor.
        internal static void ValidateContext(IDictionary<string, string> env, string json, string checkout)
        {
            Need(env != null && Sha(checkout) && checkout != BaseSha);
            foreach (var pair in new Dictionary<string, string> {
                {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"},
                {"RUNNER_ENVIRONMENT", "github-hosted"}, {"GITHUB_EVENT_NAME", "pull_request"},
                {"GITHUB_REPOSITORY", Repo}, {"GITHUB_HEAD_REF", HeadRef},
                {"GITHUB_BASE_REF", BaseRef}, {"P312_SYNTHETIC_HOSTED_ONLY", "1"} })
                Need(Env(env, pair.Key) == pair.Value);
            Need(json != null && json.Length > 0 && json.Length < 65536);
            var parser = new JavaScriptSerializer { MaxJsonLength = 65535, RecursionLimit = 32 };
            var root = Map(parser.DeserializeObject(json));
            var pr = Map(Field(root, "pull_request"));
            Need(Object.Equals(Field(pr, "draft"), true));
            var repository = Map(Field(root, "repository"));
            Need((string)Field(repository, "full_name") == Repo);
            var rootFork = Field(repository, "fork");
            Need(rootFork is bool);
            foreach (string side in new[] { "head", "base" })
            {
                var endpoint = Map(Field(pr, side));
                var repo = Map(Field(endpoint, "repo"));
                Need((string)Field(repo, "full_name") == Repo);
                Need(Object.Equals(Field(repo, "fork"), rootFork));
                Need(Object.Equals(Field(repo, "id"), Field(repository, "id")));
                Need((string)Field(endpoint, "ref") == (side == "head" ? HeadRef : BaseRef));
                Need((string)Field(endpoint, "sha") == (side == "head" ? checkout : BaseSha));
            }
        }

        private static void RegularPath(string path, string root)
        {
            Need(path.StartsWith(root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar,
                StringComparison.OrdinalIgnoreCase));
            for (string current = path; current != null; current = Path.GetDirectoryName(current))
            {
                FileAttributes attributes = File.GetAttributes(current);
                Need((attributes & FileAttributes.ReparsePoint) == 0);
                if (String.Equals(current.TrimEnd('\\'), root.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase)) return;
            }
            Need(false);
        }

        internal static void RequireHosted()
        {
            // All cheap environment checks precede file, process, identity and native access.
            var env = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (var pair in new Dictionary<string, string> {
                {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"},
                {"RUNNER_ENVIRONMENT", "github-hosted"}, {"GITHUB_EVENT_NAME", "pull_request"},
                {"GITHUB_REPOSITORY", Repo}, {"GITHUB_HEAD_REF", HeadRef},
                {"GITHUB_BASE_REF", BaseRef}, {"P312_SYNTHETIC_HOSTED_ONLY", "1"} })
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
            ValidateContext(env, json, checkout);
        }

        [MethodImpl(MethodImplOptions.NoInlining)]
        internal HostedDisposableWinCred(string id)
        {
            ValidateId(id); // Before ANY OS access, including on a non-hosted machine.
            Need(Assembly.GetCallingAssembly().GetName().Name == "P312.ProductVault.Tests");
            RequireHosted();
            target = Prefix + id;
            owner = Identity();
            Need(Marshal.SizeOf(typeof(Credential)) == (IntPtr.Size == 8 ? 80 : 52));
            lock (Writer) { Need(!Read(null)); } // Collision never grants cleanup ownership.
        }

        private static SecurityIdentifier Identity()
        {
            SecurityIdentifier sid = CustodyService.ReadProcessSid();
            Need(sid != null && !sid.IsWellKnown(WellKnownSidType.LocalSystemSid)); return sid;
        }
        private void Gate()
        { if (p315Session) RequireHostedP315(); else if (p314Session) RequireHostedP314(); else if (p313Session) RequireHostedP313(); else RequireHosted(); Need(owner.Equals(Identity())); }
        internal VaultState State { get { lock (Writer) return state; } }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct Credential
        {
            internal uint Flags, Type;
            [MarshalAs(UnmanagedType.LPWStr)] internal string TargetName;
            [MarshalAs(UnmanagedType.LPWStr)] internal string Comment;
            internal System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
            internal uint BlobSize;
            internal IntPtr Blob;
            internal uint Persist, AttributeCount;
            internal IntPtr Attributes;
            [MarshalAs(UnmanagedType.LPWStr)] internal string TargetAlias;
            [MarshalAs(UnmanagedType.LPWStr)] internal string UserName;
        }
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredWriteW(ref Credential credential, uint flags);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredReadW(string target, uint type, uint flags, out IntPtr credential);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredDeleteW(string target, uint type, uint flags);
        [DllImport("advapi32.dll", ExactSpelling = true)]
        private static extern void CredFree(IntPtr buffer);

        // expected == null is presence-only preflight: never copies a collided blob.
        private bool Read(string expected)
        {
            IntPtr pointer = IntPtr.Zero;
            IntPtr copiedBlob = IntPtr.Zero;
            int copiedLength = 0;
            bool found = CredReadW(target, 1, 0, out pointer);
            int error = Marshal.GetLastWin32Error();
            try
            {
                if (!found) { Need(error == 1168 && pointer == IntPtr.Zero); return false; }
                Need(pointer != IntPtr.Zero);
                if (expected == null) return true;
                var value = (Credential)Marshal.PtrToStructure(pointer, typeof(Credential));
                Need(value.Type == 1 && value.Flags == 0 && value.Persist == 1 &&
                    value.TargetName == target && value.UserName == target && value.AttributeCount == 0 &&
                    value.BlobSize == Encoding.UTF8.GetByteCount(expected) && value.Blob != IntPtr.Zero);
                byte[] bytes = new byte[(int)value.BlobSize];
                byte[] wanted = Encoding.UTF8.GetBytes(expected);
                copiedBlob = value.Blob; copiedLength = bytes.Length;
                try
                {
                    Marshal.Copy(value.Blob, bytes, 0, bytes.Length);
                    for (int i = 0; i < bytes.Length; i++) Need(bytes[i] == wanted[i]);
                }
                finally { Array.Clear(bytes, 0, bytes.Length); Array.Clear(wanted, 0, wanted.Length); }
                return true;
            }
            finally
            {
                // Only a structurally bounded synthetic read is touched; preflight copies nothing.
                try { for (int i = 0; i < copiedLength; i++) Marshal.WriteByte(copiedBlob, i, 0); }
                finally { if (pointer != IntPtr.Zero) CredFree(pointer); }
            }
        }

        private void Write(string value)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(value);
            IntPtr blob = IntPtr.Zero;
            try
            {
                blob = Marshal.AllocHGlobal(bytes.Length);
                Marshal.Copy(bytes, 0, blob, bytes.Length);
                var credential = new Credential { Type = 1, TargetName = target, UserName = target,
                    Persist = 1, BlobSize = (uint)bytes.Length, Blob = blob };
                attempted = true; // Even a failed native write has uncertain outcome.
                Need(CredWriteW(ref credential, 0));
            }
            finally
            {
                if (blob != IntPtr.Zero)
                { for (int i = 0; i < bytes.Length; i++) Marshal.WriteByte(blob, i, 0); Marshal.FreeHGlobal(blob); }
                Array.Clear(bytes, 0, bytes.Length);
            }
        }

        private void Cleanup()
        {
            if (!attempted) return;
            Gate();
            if (Read(null))
            {
                // On an uncertain replace either of OUR fixed values is valid; anything else refuses deletion.
                bool ours;
                try { ours = Read(Alpha); }
                catch (InvalidOperationException) { ours = Read(Beta); }
                Need(ours); Need(CredDeleteW(target, 1, 0));
            }
            Need(!Read(null)); attempted = false;
        }

        private void Effect(VaultState required, VaultState next, Action action)
        {
            lock (Writer)
            {
                Need(state == required);
                try { Gate(); action(); state = next; }
                catch
                {
                    state = VaultState.Faulted;
                    try { Cleanup(); }
                    catch { throw new InvalidOperationException("P312 cleanup incident; HOLD."); }
                    throw new InvalidOperationException("P312 effect refused; HOLD.");
                }
            }
        }
        internal void Add()
        { Effect(VaultState.Uninitialized, VaultState.Saved, delegate { Need(!Read(null)); Write(Alpha); Need(Read(Alpha)); }); }
        internal void Replace()
        { Effect(VaultState.Saved, VaultState.Replaced, delegate { Need(Read(Alpha)); Write(Beta); Need(Read(Beta)); }); }
        internal void Delete()
        { Effect(VaultState.Replaced, VaultState.Deleted, delegate { Need(Read(Beta)); Need(CredDeleteW(target, 1, 0)); Need(!Read(null)); attempted = false; }); }
        internal void Verify()
        {
            lock (Writer)
            {
                Need(state == VaultState.Saved || state == VaultState.Replaced || state == VaultState.Deleted);
                try { Gate(); Need(state == VaultState.Deleted ? !Read(null) : Read(state == VaultState.Saved ? Alpha : Beta)); }
                catch { state = VaultState.Faulted; try { Cleanup(); } catch { throw new InvalidOperationException("P312 cleanup incident; HOLD."); } throw; }
            }
        }
        public void Dispose()
        {
            lock (Writer)
            {
                if (state == VaultState.Disposed) return;
                try { Cleanup(); state = VaultState.Disposed; }
                catch { state = VaultState.Faulted; throw new InvalidOperationException("P312 cleanup incident; HOLD."); }
            }
        }
    }
}
