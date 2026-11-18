#if !DEBUG
#error P270_NO_RELEASE_BUILD
#endif
#if !C1_P270_DEVELOPMENT_ONLY
#error P270_DEVELOPMENT_OPT_IN_REQUIRED
#endif
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1.P270Development
{
    // Service-owned TEST FIXTURE only. Never implements a credential effect port.
    internal sealed class DurableWitness : IDisposable
    {
        // TEST-ONLY fixed diagnostic state; never authority or exception payload.
        internal static string TestStage = "not-started";
        internal const string JournalName = "journal.dpapi";
        internal const string AnchorName = "anchor.dpapi";
        private const int MaxBlob = 65536;
        private readonly object gate = new object();
        private readonly List<SafeFileHandle> directories = new List<SafeFileHandle>();
        private readonly SecurityIdentifier sid = WindowsIdentity.GetCurrent().User;
        private readonly string root;
        private FileStream journal, anchor;
        private string knownJournal, knownAnchor, awaitingAnchor;
        private bool recovery = true, disposed;
        private readonly bool fresh;
        [StructLayout(LayoutKind.Sequential)]
        private struct Info
        {
            internal uint Attributes;
            internal System.Runtime.InteropServices.ComTypes.FILETIME Creation, Access, Write;
            internal uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
        }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFile(string name, uint access, uint share,
            IntPtr security, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetFileInformationByHandle(SafeFileHandle handle, out Info info);
        private static void Require(bool value) { if (!value) throw new LedgerBlocked(); }
        private static void CheckHandle(SafeFileHandle handle, bool directory)
        {
            Info info = new Info();
            Require(!handle.IsInvalid && GetFileInformationByHandle(handle, out info));
            Require((info.Attributes & 0x400) == 0 && ((info.Attributes & 0x10) != 0) == directory);
            if (!directory) Require(info.Links == 1);
        }
        internal DurableWitness(string protectedTestRoot, bool freshEnrollment)
        {
            TestStage = "constructor-platform";
            Require(Environment.OSVersion.Platform == PlatformID.Win32NT);
            // Only a direct, uniquely named OS-temp fixture provisioned by the host.
            TestStage = "constructor-root";
            string temp = Path.GetFullPath(Path.GetTempPath()).TrimEnd(Path.DirectorySeparatorChar);
            root = Path.GetFullPath(protectedTestRoot).TrimEnd(Path.DirectorySeparatorChar);
            Require(new DriveInfo(Path.GetPathRoot(root)).DriveType == DriveType.Fixed);
            Guid id;
            Require(String.Equals(Path.GetDirectoryName(root), temp, StringComparison.OrdinalIgnoreCase) &&
                Path.GetFileName(root).StartsWith("nayeon-p270-", StringComparison.Ordinal) &&
                Guid.TryParseExact(Path.GetFileName(root).Substring(12), "N", out id));
            fresh = freshEnrollment;
            try
            {
                // Pin every ancestor against rename/deletion; inspect opened handles,
                // not only pre-open path attributes. No reparse traversal accepted.
                List<string> chain = new List<string>();
                for (string p = root; p != null; p = Path.GetDirectoryName(p)) chain.Add(p);
                chain.Reverse();
                foreach (string p in chain)
                {
                    TestStage = "ancestor-open";
                    SafeFileHandle h = CreateFile(p, 0x80, 3, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
                    TestStage = "ancestor-handle";
                    directories.Add(h); CheckHandle(h, true);
                }
                TestStage = "root-acl-read";
                DirectorySecurity acl = Directory.GetAccessControl(root);
                TestStage = "root-acl-owner-protection";
                Require(acl.GetOwner(typeof(SecurityIdentifier)).Equals(sid) && acl.AreAccessRulesProtected);
                AuthorizationRuleCollection rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
                TestStage = "root-acl-rule-count";
                Require(rules.Count == 1);
                FileSystemAccessRule rule = (FileSystemAccessRule)rules[0];
                TestStage = "root-acl-rule-shape";
                Require(rule.IdentityReference.Equals(sid) && rule.AccessControlType == AccessControlType.Allow &&
                    rule.FileSystemRights == FileSystemRights.FullControl &&
                    rule.InheritanceFlags == (InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit));
                if (freshEnrollment)
                {
                    TestStage = "fresh-empty-root";
                    Require(Directory.GetFileSystemEntries(root).Length == 0);
                    journal = Open(JournalName, FileMode.CreateNew);
                    anchor = Open(AnchorName, FileMode.CreateNew);
                    TestStage = "initial-ledger";
                    knownJournal = CustodyLedger.CreateInitial(CustodyLedger.NewNonce());
                    knownAnchor = CustodyLedger.Anchor(knownJournal);
                    Persist(journal, JournalName, knownJournal);
                    Persist(anchor, AnchorName, knownAnchor);
                    TestStage = "initial-layout-codec";
                    CheckLayout(); CustodyLedger.Verify(Read(journal, JournalName), Read(anchor, AnchorName));
                    recovery = false;
                }
                else
                {
                    CheckLayout();
                    journal = Open(JournalName, FileMode.Open);
                    anchor = Open(AnchorName, FileMode.Open);
                    // Inspection can prove bytes consistent, never restart authority.
                    knownJournal = Read(journal, JournalName); knownAnchor = Read(anchor, AnchorName);
                    CustodyLedger.Verify(knownJournal, knownAnchor);
                }
            }
            catch { recovery = true; Dispose(); throw new LedgerBlocked(); }
        }
        private FileStream Open(string name, FileMode mode)
        {
            string path = Path.Combine(root, name);
            if (mode == FileMode.Open) Require((File.GetAttributes(path) & FileAttributes.ReparsePoint) == 0);
            TestStage = "file-open";
            SafeFileHandle handle = CreateFile(path, 0xC0000000, 0, IntPtr.Zero,
                mode == FileMode.CreateNew ? 1u : 3u, 0x80200000, IntPtr.Zero);
            if (handle.IsInvalid) { handle.Dispose(); throw new LedgerBlocked(); }
            FileStream stream;
            TestStage = "file-handle-stream";
            try
            {
                CheckHandle(handle, false);
                TestStage = "file-stream-wrap";
                stream = new FileStream(handle, FileAccess.ReadWrite, 4096, false);
            }
            catch { handle.Dispose(); throw; }
            try
            {
                CheckHandle(stream.SafeFileHandle, false);
                TestStage = "file-owner";
                Require(stream.GetAccessControl().GetOwner(typeof(SecurityIdentifier)).Equals(sid));
                return stream;
            }
            catch { stream.Dispose(); throw; }
        }
        private void CheckLayout()
        {
            TestStage = "layout";
            string[] entries = Directory.GetFileSystemEntries(root);
            Require(entries.Length == 2);
            foreach (string entry in entries)
                Require((Path.GetFileName(entry) == JournalName || Path.GetFileName(entry) == AnchorName) &&
                    (File.GetAttributes(entry) & (FileAttributes.ReparsePoint | FileAttributes.Directory)) == 0);
        }
        private byte[] Entropy(string name)
        { return Encoding.UTF8.GetBytes("NAYEON:P270:DISPOSABLE-CUSTODY:V1:" + sid.Value + ":" + root + ":" + name); }
        private string Read(FileStream stream, string name)
        {
            CheckHandle(stream.SafeFileHandle, false);
            TestStage = "read-length";
            Require(stream.Length > 0 && stream.Length <= MaxBlob);
            byte[] blob = new byte[(int)stream.Length]; stream.Position = 0;
            int offset = 0;
            while (offset < blob.Length)
            { int n = stream.Read(blob, offset, blob.Length - offset); Require(n > 0); offset += n; }
            TestStage = "read-framing";
            Require(blob.Length > 4 && BitConverter.ToInt32(blob, 0) == blob.Length - 4);
            byte[] protectedBytes = new byte[blob.Length - 4];
            Buffer.BlockCopy(blob, 4, protectedBytes, 0, protectedBytes.Length);
            TestStage = "dpapi-unprotect";
            byte[] plain = ProtectedData.Unprotect(protectedBytes, Entropy(name), DataProtectionScope.CurrentUser);
            TestStage = "read-utf8";
            try { Require(plain.Length > 0 && plain.Length <= 32768); return new UTF8Encoding(false, true).GetString(plain); }
            finally { Array.Clear(plain, 0, plain.Length); }
        }
        private void Persist(FileStream stream, string name, string text)
        {
            TestStage = "persist-bound";
            Require(text != null && text.Length > 0 && text.Length <= 32768);
            byte[] plain = Encoding.UTF8.GetBytes(text);
            byte[] blob;
            try
            {
                TestStage = "dpapi-protect";
                byte[] protectedBytes = ProtectedData.Protect(plain, Entropy(name), DataProtectionScope.CurrentUser);
                blob = new byte[protectedBytes.Length + 4];
                Buffer.BlockCopy(BitConverter.GetBytes(protectedBytes.Length), 0, blob, 0, 4);
                Buffer.BlockCopy(protectedBytes, 0, blob, 4, protectedBytes.Length);
            }
            finally { Array.Clear(plain, 0, plain.Length); }
            Require(blob.Length > 0 && blob.Length <= MaxBlob);
            // Intentionally no replacement-atomicity claim: any interruption holds.
            CheckHandle(stream.SafeFileHandle, false);
            TestStage = "persist-write";
            stream.Position = 0; stream.Write(blob, 0, blob.Length); stream.SetLength(blob.Length);
            TestStage = "persist-flush";
            stream.Flush(true);
            TestStage = "persist-readback";
            Require(String.Equals(Read(stream, name), text, StringComparison.Ordinal));
        }
        internal bool RecoveryRequired { get { lock (gate) { return recovery || disposed || awaitingAnchor != null; } } }
        internal bool InspectConsistent()
        {
            lock (gate)
            {
                try
                {
                    Require(!disposed); CheckLayout();
                    string j = Read(journal, JournalName), a = Read(anchor, AnchorName);
                    Require(j == knownJournal && a == knownAnchor);
                    CustodyLedger.Verify(j, a); return true;
                }
                catch { recovery = true; return false; }
            }
        }
        internal string ReadJournal() { lock (gate) { return Snapshot(true); } }
        internal string ReadAnchor() { lock (gate) { return Snapshot(false); } }
        private string Snapshot(bool isJournal)
        {
            try
            {
                Require(!disposed); CheckLayout();
                string value = Read(isJournal ? journal : anchor, isJournal ? JournalName : AnchorName);
                Require(value == (isJournal ? knownJournal : knownAnchor)); return value;
            }
            catch { recovery = true; throw new LedgerBlocked(); }
        }
        internal void WriteJournal(string expected, string replacement)
        {
            lock (gate)
            {
                try
                {
                    Require(fresh && !recovery && !disposed && awaitingAnchor == null);
                    Require(expected == Snapshot(true) && Snapshot(false) == CustodyLedger.Anchor(expected));
                    CustodyFrame[] before = CustodyLedger.Decode(expected), after = CustodyLedger.Decode(replacement);
                    Require(replacement.StartsWith(expected, StringComparison.Ordinal) && after.Length == before.Length + 1);
                    recovery = true; // uncertainty BEFORE first byte; exception never clears it
                    Persist(journal, JournalName, replacement); CheckLayout();
                    knownJournal = replacement; awaitingAnchor = CustodyLedger.Anchor(replacement);
                    recovery = false;
                }
                catch { recovery = true; throw new LedgerBlocked(); }
            }
        }
        internal void WriteAnchor(string expected, string replacement)
        {
            lock (gate)
            {
                try
                {
                    Require(fresh && !recovery && !disposed && awaitingAnchor != null);
                    Require(expected == Snapshot(false) && replacement == awaitingAnchor && Snapshot(true) == knownJournal);
                    recovery = true;
                    Persist(anchor, AnchorName, replacement); CheckLayout();
                    knownAnchor = replacement;
                    CustodyLedger.Verify(Snapshot(true), Snapshot(false));
                    awaitingAnchor = null; recovery = false;
                }
                catch { recovery = true; throw new LedgerBlocked(); }
            }
        }
        public void Dispose()
        {
            lock (gate)
            {
                disposed = true; recovery = true;
                if (journal != null) journal.Dispose(); if (anchor != null) anchor.Dispose();
                foreach (SafeFileHandle h in directories) h.Dispose();
            }
        }
    }
}
