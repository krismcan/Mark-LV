using System;
using System.IO;
using System.Collections.Generic;
using Microsoft.Win32.SafeHandles;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;

namespace Nayeon.ByokC1.Service
{
    // Disposable hosted-user evidence only. No production custody or restart authority.
    internal sealed class DurableIntentJournal : IDisposable
    {
        private const string Leaf = "intent.dpapi";
        private readonly string id;
        private readonly bool readOnly;
        private string root, path;
        private SecurityIdentifier sid;
        private FileStream stream;
        private readonly List<SafeFileHandle> directories = new List<SafeFileHandle>();
        private FileIdentity identity;
        private bool identityBound;

        [StructLayout(LayoutKind.Sequential)]
        private struct FileIdentity
        {
            internal uint Attributes;
            internal System.Runtime.InteropServices.ComTypes.FILETIME Creation, Access, Write;
            internal uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
        }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        private static extern SafeFileHandle CreateFileW(string name, uint access, uint share,
            IntPtr security, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetFileInformationByHandle(SafeFileHandle handle, out FileIdentity info);

        private static FileIdentity Inspect(SafeFileHandle handle, bool directory)
        {
            FileIdentity info;
            Need(!handle.IsInvalid && !handle.IsClosed);
            Need(GetFileInformationByHandle(handle, out info));
            Need((info.Attributes & 0x400) == 0 && ((info.Attributes & 0x10) != 0) == directory);
            Need(directory || info.Links == 1);
            return info;
        }
        private void PinDirectory(string directory)
        {
            var handle = CreateFileW(directory, 0x80, 3, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
            directories.Add(handle); // No FILE_SHARE_DELETE: pin against rename/replacement.
            Inspect(handle, true);
        }
        private void CheckFileIdentity()
        {
            foreach (var handle in directories) Inspect(handle, true);
            FileIdentity now = Inspect(stream.SafeFileHandle, false);
            if (identityBound)
                Need(now.Volume == identity.Volume && now.IndexHigh == identity.IndexHigh &&
                    now.IndexLow == identity.IndexLow);
            else { identity = now; identityBound = true; }
            Need(stream.CanRead && stream.CanWrite == !readOnly);
        }
        private byte[] entropy;
        private bool attempted, disposed, recoveryRequired, inFlight;
        private static readonly UTF8Encoding Utf8 = new UTF8Encoding(false, true);

        [StructLayout(LayoutKind.Sequential)]
        private struct SecurityAttributes
        {
            internal int Length;
            internal IntPtr Descriptor;
            [MarshalAs(UnmanagedType.Bool)] internal bool Inherit;
        }
        // Atomic fail-if-root-exists creation, with protected DACL at creation.
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CreateDirectoryW(string name, ref SecurityAttributes attributes);

        private static void Need(bool value)
        { if (!value) throw new InvalidOperationException("P314 RecoveryRequired; HOLD."); }
        internal static void ValidateId(string value)
        {
            Guid parsed;
            Need(value != null && Guid.TryParseExact(value, "N", out parsed));
            Need(Guid.TryParseExact(value, "N", out parsed) && parsed != Guid.Empty && value == parsed.ToString("N"));
        }
        internal DurableIntentJournal(string value, bool reopen)
        {
            ValidateId(value); id = value; readOnly = reopen;
            if (!reopen) return; // Pure allocation: control-first creates no journal.
            recoveryRequired = true;
            try
            {
                Locate();
                PinDirectory(root);
                CheckPaths(true);
                CheckAcl(Directory.GetAccessControl(root), true);
                var handle = CreateFileW(path, 0x80000000u, 0, IntPtr.Zero, 3, 0x00200000, IntPtr.Zero);
                try
                {
                    Inspect(handle, false); // OPEN_REPARSE_POINT, never follow a leaf link.
                    stream = new FileStream(handle, FileAccess.Read, 4096, false);
                }
                catch { handle.Dispose(); throw; }
                CheckAcl(stream.GetAccessControl(), false);
                string state = Read();
                Need(state == "IDLE" || state == "IN_FLIGHT");
                inFlight = state == "IN_FLIGHT";
                // Even IDLE reopen cannot acquire new effect authority.
            }
            catch { Dispose(); throw new InvalidOperationException("P314 RecoveryRequired; HOLD."); }
        }
        private void Locate()
        {
            Need(Environment.OSVersion.Platform == PlatformID.Win32NT &&
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" &&
                Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") == "github-hosted" &&
                ((Environment.GetEnvironmentVariable("P314_SYNTHETIC_HOSTED_ONLY") == "1" &&
                  Environment.GetEnvironmentVariable("P315_SYNTHETIC_HOSTED_ONLY") == null) ||
                 (Environment.GetEnvironmentVariable("P315_SYNTHETIC_HOSTED_ONLY") == "1" &&
                  Environment.GetEnvironmentVariable("P314_SYNTHETIC_HOSTED_ONLY") == null &&
                  Environment.GetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY") == null &&
                  Environment.GetEnvironmentVariable("P312_SYNTHETIC_HOSTED_ONLY") == null &&
                  Environment.GetEnvironmentVariable("RUNNER_OS") == "Windows" &&
                  Environment.GetEnvironmentVariable("GITHUB_EVENT_NAME") == "pull_request" &&
                  Environment.GetEnvironmentVariable("GITHUB_REPOSITORY") == "krismcan/Mark-LV" &&
                  Environment.GetEnvironmentVariable("GITHUB_HEAD_REF") == "byok-c1-p315-hosted-crash-recovery-20261123" &&
                  Environment.GetEnvironmentVariable("GITHUB_BASE_REF") == "byok-c1-p314-hosted-durable-native-intent-20261123")));
            sid = CustodyService.ReadProcessSid(); // Also rejects thread impersonation.
            Need(sid != null && !sid.IsWellKnown(WellKnownSidType.LocalSystemSid));
            string temp = Path.GetFullPath(Path.GetTempPath()).TrimEnd(Path.DirectorySeparatorChar);
            string drive = Path.GetPathRoot(temp);
            Need(drive != null && drive.Length == 3 && drive[1] == ':' &&
                new DriveInfo(drive).DriveType == DriveType.Fixed);
            root = Path.Combine(temp, "nayeon-p314-" + id);
            path = Path.Combine(root, Leaf);
            entropy = Utf8.GetBytes(root + "|" + sid.Value + "|" + Leaf);
            CheckAncestors(temp);
            var chain = new List<string>();
            for (string current = temp; current != null; current = Path.GetDirectoryName(current)) chain.Add(current);
            chain.Reverse();
            foreach (string current in chain) PinDirectory(current);
        }
        private static void CheckAncestors(string start)
        {
            for (string current = start; current != null; current = Path.GetDirectoryName(current))
            {
                var attributes = File.GetAttributes(current);
                Need((attributes & FileAttributes.ReparsePoint) == 0 &&
                    (attributes & FileAttributes.Directory) != 0);
            }
        }
        private void CheckPaths(bool leaf)
        {
            CheckAncestors(root);
            Need(Path.GetDirectoryName(root) == Path.GetFullPath(Path.GetTempPath()).TrimEnd('\\'));
            if (leaf) Need((File.GetAttributes(path) &
                (FileAttributes.ReparsePoint | FileAttributes.Directory)) == 0);
        }
        private DirectorySecurity DirectoryAcl()
        {
            var acl = new DirectorySecurity();
            acl.SetOwner(sid);
            acl.SetAccessRuleProtection(true, false);
            acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None, AccessControlType.Allow));
            return acl;
        }
        private FileSecurity FileAcl()
        {
            var acl = new FileSecurity();
            acl.SetOwner(sid);
            acl.SetAccessRuleProtection(true, false);
            acl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.FullControl, AccessControlType.Allow));
            return acl;
        }
        private void CheckAcl(FileSystemSecurity acl, bool directory)
        {
            Need(acl.AreAccessRulesProtected && acl.GetOwner(typeof(SecurityIdentifier)).Equals(sid));
            var rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
            Need(rules.Count == 1);
            var rule = rules[0] as FileSystemAccessRule;
            Need(rule != null && !rule.IsInherited && rule.IdentityReference.Equals(sid) &&
                rule.AccessControlType == AccessControlType.Allow && rule.FileSystemRights == FileSystemRights.FullControl &&
                rule.PropagationFlags == PropagationFlags.None &&
                rule.InheritanceFlags == (directory ?
                    InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit : InheritanceFlags.None));
        }
        private void Create()
        {
            Locate();
            byte[] descriptor = DirectoryAcl().GetSecurityDescriptorBinaryForm();
            var pin = GCHandle.Alloc(descriptor, GCHandleType.Pinned);
            try
            {
                var attributes = new SecurityAttributes { Length = Marshal.SizeOf(typeof(SecurityAttributes)),
                    Descriptor = pin.AddrOfPinnedObject(), Inherit = false };
                Need(CreateDirectoryW(root, ref attributes)); // Existing root is NEVER adopted.
            }
            finally { pin.Free(); Array.Clear(descriptor, 0, descriptor.Length); }
            PinDirectory(root);
            CheckPaths(false);
            CheckAcl(Directory.GetAccessControl(root), true);
            stream = new FileStream(path, FileMode.CreateNew, FileSystemRights.FullControl,
                FileShare.None, 4096, FileOptions.WriteThrough, FileAcl());
            CheckPaths(true);
            CheckFileIdentity();
            CheckAcl(stream.GetAccessControl(), false);
            WriteVerify("IDLE");
        }
        private byte[] Frame(string state)
        {
            byte[] payload = Utf8.GetBytes("P314|" + state + "|" + id);
            byte[] frame = new byte[4 + payload.Length];
            Buffer.BlockCopy(BitConverter.GetBytes(payload.Length), 0, frame, 0, 4);
            Buffer.BlockCopy(payload, 0, frame, 4, payload.Length);
            Array.Clear(payload, 0, payload.Length);
            return frame;
        }
        private string Read()
        {
            Need(stream != null && stream.CanRead && stream.Length > 4 && stream.Length <= 16384);
            CheckPaths(true);
            CheckFileIdentity();
            string[] entries = Directory.GetFileSystemEntries(root);
            Need(entries.Length == 1 && String.Equals(entries[0], path, StringComparison.OrdinalIgnoreCase));
            CheckAcl(Directory.GetAccessControl(root), true);
            CheckAcl(stream.GetAccessControl(), false);
            Need(sid.Equals(CustodyService.ReadProcessSid()));
            byte[] blob = new byte[(int)stream.Length], clear = null;
            try
            {
                stream.Position = 0;
                int offset = 0;
                while (offset < blob.Length)
                {
                    int count = stream.Read(blob, offset, blob.Length - offset);
                    Need(count > 0); offset += count;
                }
                Need(stream.ReadByte() == -1);
                clear = ProtectedData.Unprotect(blob, entropy, DataProtectionScope.CurrentUser);
                Need(clear.Length > 4 && clear.Length <= 16384);
                int length = BitConverter.ToInt32(clear, 0);
                Need(length == clear.Length - 4);
                string text = Utf8.GetString(clear, 4, length);
                if (text == "P314|IDLE|" + id) return "IDLE";
                Need(text == "P314|IN_FLIGHT|" + id);
                return "IN_FLIGHT";
            }
            finally
            {
                Array.Clear(blob, 0, blob.Length);
                if (clear != null) Array.Clear(clear, 0, clear.Length);
            }
        }
        private void WriteVerify(string state)
        {
            Need(!readOnly && !disposed && stream != null && stream.CanWrite);
            byte[] clear = Frame(state), blob = null;
            try
            {
                blob = ProtectedData.Protect(clear, entropy, DataProtectionScope.CurrentUser);
                Need(blob.Length > 4 && blob.Length <= 16384);
                stream.Position = 0;
                stream.Write(blob, 0, blob.Length);
                stream.SetLength(blob.Length);
                stream.Flush(true);
                Need(Read() == state); // Same exclusive OS handle, after disk flush.
            }
            finally
            {
                Array.Clear(clear, 0, clear.Length);
                if (blob != null) Array.Clear(blob, 0, blob.Length);
            }
        }
        internal void RecordInFlightAndFlushVerify()
        {
            bool permitted = !readOnly && !attempted && !disposed && !recoveryRequired;
            recoveryRequired = true;
            Need(permitted);
            attempted = true;
            // RecoveryRequired remains sticky on every partial/failure path.
            try
            {
                Create();
                Need(Read() == "IDLE");
                WriteVerify("IN_FLIGHT");
                inFlight = true;
            }
            catch { throw new InvalidOperationException("P314 RecoveryRequired; HOLD."); }
        }
        internal bool RecoveryRequired { get { return recoveryRequired; } }
        internal bool InFlight { get { return inFlight; } }
        public void Dispose()
        {
            if (disposed) return;
            try { if (stream != null) stream.Dispose(); }
            finally
            {
                foreach (var handle in directories) handle.Dispose();
                directories.Clear();
                disposed = true;
                if (entropy != null) Array.Clear(entropy, 0, entropy.Length);
            }
            // Evidence retained. Only the hosted fixture removes its verified exact path.
        }
    }
}
