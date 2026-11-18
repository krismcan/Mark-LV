#if !DEBUG
#error P274_NO_RELEASE_BUILD
#endif
#if !C1_P268_DEVELOPMENT_ONLY
#error P274_REQUIRES_P268_DEVELOPMENT_ONLY
#endif
#if !C1_P274_EPHEMERAL_WINCRED_ONLY
#error P274_EPHEMERAL_OPT_IN_REQUIRED
#endif
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using Nayeon.ByokC1;

namespace Nayeon.ByokC1.P274Development
{
    // Test assembly only. No caller-selected target, payload, native adapter or factory.
    internal sealed class P274EphemeralWinCredEffect : IDisposable
    {
        internal const string BaseSha = "9546228e5c726a46a3bf91ba05793f38c23d686f";
        internal const string HeadBranch = "byok-c1-p274-real-os-effect-gate-20261118";
        internal const string BaseBranch = "byok-c1-p273-current-p76-admission-20261118";
        private const string Repo = "krismcan/Mark-LV";
        private const string Prefix = "Nayeon.P274.Disposable.";
        private readonly string target;
        private bool owned, disposed, seeded, submitted;
        internal int TerminalCalls { get; private set; }

        private static void Require(bool condition)
        { if (!condition) throw new InvalidOperationException("P274_REFUSED"); }
        private static string Env(IDictionary<string, string> env, string key)
        { string value; return env.TryGetValue(key, out value) ? value : null; }
        private static object Field(IDictionary<string, object> value, string key)
        { object result; Require(value != null && value.TryGetValue(key, out result)); return value[key]; }
        private static IDictionary<string, object> Map(object value)
        { var result = value as IDictionary<string, object>; Require(result != null); return result; }

        // Pure predicate seam for negative tests; it never invokes WinCred.
        internal static void ValidateContext(IDictionary<string, string> env, string json,
            bool windows, bool localSystem)
        {
            Require(windows && !localSystem && env != null);
            Require(Env(env, "GITHUB_ACTIONS") == "true" && Env(env, "RUNNER_OS") == "Windows" &&
                Env(env, "RUNNER_ENVIRONMENT") == "github-hosted" &&
                Env(env, "GITHUB_REPOSITORY") == Repo && Env(env, "GITHUB_EVENT_NAME") == "pull_request" &&
                Env(env, "P274_NATIVE_AUTH") == "DISPOSABLE_HOSTED_SYNTHETIC_ONLY" &&
                Env(env, "P274_BASE_SHA") == BaseSha &&
                Regex.IsMatch(Env(env, "P274_HEAD_SHA") ?? "", "\\A[0-9a-f]{40}\\z") &&
                Env(env, "P274_HEAD_SHA") != BaseSha &&
                Env(env, "GITHUB_HEAD_REF") == HeadBranch && Env(env, "GITHUB_BASE_REF") == BaseBranch);
            Require(json != null && json.Length > 0 && json.Length <= 262144);
            var parser = new JavaScriptSerializer { MaxJsonLength = 262144, RecursionLimit = 32 };
            var root = Map(parser.DeserializeObject(json));
            var pr = Map(Field(root, "pull_request"));
            Require(Object.Equals(Field(pr, "draft"), true));
            Require((string)Field(Map(Field(root, "repository")), "full_name") == Repo);
            foreach (string side in new[] { "head", "base" })
            {
                var endpoint = Map(Field(pr, side));
                Require((string)Field(Map(Field(endpoint, "repo")), "full_name") == Repo);
                Require((string)Field(endpoint, "ref") == (side == "head" ? HeadBranch : BaseBranch));
                Require((string)Field(endpoint, "sha") == (side == "head" ? Env(env, "P274_HEAD_SHA") : BaseSha));
            }
            string number = Convert.ToString(Field(pr, "number"), System.Globalization.CultureInfo.InvariantCulture);
            Require(Regex.IsMatch(number, "\\A[1-9][0-9]{0,9}\\z") &&
                Env(env, "GITHUB_REF") == "refs/pull/" + number + "/merge");
        }

        internal static void RequireHosted()
        {
            // Fail before reading the event, identity or loading any WinCred entrypoint locally.
            Require(Environment.OSVersion.Platform == PlatformID.Win32NT &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                Environment.GetEnvironmentVariable("P274_NATIVE_AUTH") == "DISPOSABLE_HOSTED_SYNTHETIC_ONLY");
            var env = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (string key in new[] { "GITHUB_ACTIONS", "RUNNER_OS", "RUNNER_ENVIRONMENT",
                "GITHUB_REPOSITORY", "GITHUB_EVENT_NAME", "P274_NATIVE_AUTH", "P274_HEAD_SHA",
                "P274_BASE_SHA", "GITHUB_HEAD_REF", "GITHUB_BASE_REF", "GITHUB_REF" })
                env[key] = Environment.GetEnvironmentVariable(key);
            string temp = Path.GetFullPath(Environment.GetEnvironmentVariable("RUNNER_TEMP") ?? "");
            string path = Path.GetFullPath(Environment.GetEnvironmentVariable("GITHUB_EVENT_PATH") ?? "");
            Require(Directory.Exists(temp) && path.StartsWith(temp.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase));
            Require((File.GetAttributes(path) & FileAttributes.ReparsePoint) == 0);
            string json;
            using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                Require(stream.Length > 0 && stream.Length <= 262144);
                using (var reader = new StreamReader(stream))
                {
                    char[] buffer = new char[262145];
                    int count = 0, read;
                    while (count < buffer.Length && (read = reader.Read(buffer, count, buffer.Length - count)) > 0) count += read;
                    Require(count <= 262144); json = new string(buffer, 0, count);
                }
            }
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                Require(identity != null && identity.User != null && !identity.IsAnonymous &&
                    identity.ImpersonationLevel != TokenImpersonationLevel.Impersonation &&
                    identity.ImpersonationLevel != TokenImpersonationLevel.Delegation);
                ValidateContext(env, json, true, identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid));
            }
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct CREDENTIALW
        {
            internal uint Flags, Type;
            [MarshalAs(UnmanagedType.LPWStr)] internal string TargetName;
            [MarshalAs(UnmanagedType.LPWStr)] internal string Comment;
            internal System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
            internal uint CredentialBlobSize;
            internal IntPtr CredentialBlob;
            internal uint Persist, AttributeCount;
            internal IntPtr Attributes;
            [MarshalAs(UnmanagedType.LPWStr)] internal string TargetAlias;
            [MarshalAs(UnmanagedType.LPWStr)] internal string UserName;
        }
        [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredWriteW(ref CREDENTIALW credential, uint flags);
        [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredReadW(string target, uint type, uint flags, out IntPtr credential);
        [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CredDeleteW(string target, uint type, uint flags);
        [DllImport("advapi32.dll", EntryPoint = "CredFree", ExactSpelling = true)]
        private static extern void CredFree(IntPtr buffer);

        internal P274EphemeralWinCredEffect()
        {
            RequireHosted();
            Require(Marshal.SizeOf(typeof(CREDENTIALW)) == (IntPtr.Size == 8 ? 80 : 52));
            target = Prefix + Guid.NewGuid().ToString("N");
            Require(Regex.IsMatch(target, "\\ANayeon\\.P274\\.Disposable\\.[0-9a-f]{32}\\z"));
            // Collision is rejected before ownership: no finally-delete on this path.
            Require(!ReadOwned()); owned = true;
            Console.WriteLine("P274_INITIAL_ABSENT=" + target);
        }
        private void CheckOwner()
        { Require(owned && !disposed); RequireHosted(); }
        private bool ReadOwned()
        {
            IntPtr buffer = IntPtr.Zero;
            bool found = CredReadW(target, 1, 0, out buffer);
            int error = Marshal.GetLastWin32Error();
            try
            {
                if (!found) { Require(error == 1168 && buffer == IntPtr.Zero); return false; }
                Require(buffer != IntPtr.Zero);
                var value = (CREDENTIALW)Marshal.PtrToStructure(buffer, typeof(CREDENTIALW));
                Require(value.Type == 1 && value.TargetName == target && value.UserName == target &&
                    value.Persist == 1 && value.CredentialBlobSize == 4 && value.CredentialBlob != IntPtr.Zero);
                byte[] bytes = new byte[4]; Marshal.Copy(value.CredentialBlob, bytes, 0, 4);
                try { Require(ValidCandidate(LedgerOperation.Save, bytes)); }
                finally { Array.Clear(bytes, 0, bytes.Length); }
                return true;
            }
            finally { if (buffer != IntPtr.Zero) CredFree(buffer); }
        }
        internal static bool ValidCandidate(LedgerOperation op, byte[] bytes)
        {
            if (op == LedgerOperation.Delete) return bytes == null;
            return (op == LedgerOperation.Save || op == LedgerOperation.Replace) && bytes != null &&
                bytes.Length == 4 && bytes[0] == 0x31 && bytes[1] == 0x32 && bytes[2] == 0x33 && bytes[3] == 0x34;
        }
        private void WriteSynthetic()
        {
            byte[] bytes = new byte[] { 0x31, 0x32, 0x33, 0x34 };
            IntPtr blob = Marshal.AllocHGlobal(4);
            try
            {
                Marshal.Copy(bytes, 0, blob, 4);
                var value = new CREDENTIALW { Type = 1, TargetName = target, UserName = target,
                    CredentialBlobSize = 4, CredentialBlob = blob, Persist = 1 };
                Require(CredWriteW(ref value, 0));
            }
            finally { Marshal.Copy(new byte[4], 0, blob, 4); Marshal.FreeHGlobal(blob); Array.Clear(bytes, 0, 4); }
        }
        internal void SeedFor(LedgerOperation op)
        {
            CheckOwner(); Require(!seeded && !submitted && (op == LedgerOperation.Replace || op == LedgerOperation.Delete));
            Require(!ReadOwned()); seeded = true;
            Console.WriteLine("P274_SETUP_SEED_NOT_TERMINAL=" + op + " " + target);
            WriteSynthetic(); Require(ReadOwned());
        }
        internal void Execute(LedgerOperation op, byte[] candidate)
        {
            CheckOwner(); Require(ValidCandidate(op, candidate) && !submitted);
            Require(seeded == (op != LedgerOperation.Save));
            Require(ReadOwned() == (op != LedgerOperation.Save));
            submitted = true; TerminalCalls++;
            if (op == LedgerOperation.Delete) Require(CredDeleteW(target, 1, 0));
            else WriteSynthetic();
            Require(ReadOwned() == (op != LedgerOperation.Delete));
            Console.WriteLine("P274_GATED_NATIVE_READBACK=" + op + " " + target);
        }
        internal void Verify(bool present)
        { CheckOwner(); Require(ReadOwned() == present); }
        public void Dispose()
        {
            if (disposed) return;
            CheckOwner();
            try
            {
                // A mismatched credential is never deleted. Any read/delete/cleanup error fails.
                try { if (ReadOwned()) Require(CredDeleteW(target, 1, 0)); }
                finally { Require(!ReadOwned()); }
                Console.WriteLine("P274_CLEANUP_ABSENT=" + target);
            }
            finally { disposed = true; owned = false; }
        }
    }
}
