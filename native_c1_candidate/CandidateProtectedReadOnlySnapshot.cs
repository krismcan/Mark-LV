// P112: exact-path READ-ONLY native J2/A2 observation for the disabled
// candidate C1 service. This source contains no create/write/flush/ACL
// mutation, WinCred API, service installation or caller-controlled path.
// Historical P49 writable source stays untouched and is excluded from the
// strictly allowlisted review assembly. ALL statuses are NON-AUTHORITY.
// Do not claim historic freshness from a pair of equal snapshots.
using System;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32;

namespace Nayeon.ByokC1
{
    internal static class CandidateProtectedReadOnlySnapshot
    {
        private const string JournalName = "pending-custody-v2.journal";
        private const int MaxJournalBytes = 32768;
        private const string ParentRegistry = @"SOFTWARE\Nayeon";
        private const string ChildRegistry = @"SOFTWARE\Nayeon\BYOK-C1";
        private const string AnchorValue = "CustodyAnchorV2";
        private const string FaultValue = "CustodyFaultV1";
        private const string TrustedInstaller =
            "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464";

        private static readonly Encoding StrictAscii = Encoding.GetEncoding(
            "us-ascii", EncoderFallback.ExceptionFallback,
            DecoderFallback.ExceptionFallback);

        private static bool ActualLocalSystem()
        {
            try
            {
                using (WindowsIdentity id = WindowsIdentity.GetCurrent())
                    return id != null && id.User != null &&
                        id.User.IsWellKnown(WellKnownSidType.LocalSystemSid);
            }
            catch (Exception) { return false; }
        }

        private static string FixedJournalPath()
        {
            return Path.Combine(ProtectedAcl.ExpectedCustodyDirectory(),
                JournalName);
        }

        private static bool JournalFileSafe(string fixedPath)
        {
            try
            {
                if (!ProtectedAcl.VerifyInstalledCustodyDirectory() ||
                    !ProtectedAcl.VerifyCustodyEvidenceFile(fixedPath))
                    return false;
                DirectoryInfo parent = new DirectoryInfo(
                    Path.GetDirectoryName(fixedPath));
                FileInfo file = new FileInfo(fixedPath);
                return parent.Exists && file.Exists &&
                    (parent.Attributes & FileAttributes.ReparsePoint) == 0 &&
                    (file.Attributes & FileAttributes.ReparsePoint) == 0;
            }
            catch (Exception) { return false; }
        }

        private static string ReadJournal()
        {
            // Never accept a path or file handle from IPC or caller. Never
            // open a file for writing and never create missing evidence.
            string path = FixedJournalPath();
            if (!JournalFileSafe(path)) throw new LedgerBlocked();
            try
            {
                using (FileStream stream = new FileStream(path, FileMode.Open,
                    FileAccess.Read, FileShare.None, 4096,
                    FileOptions.SequentialScan))
                {
                    if (stream.Length < 1 || stream.Length > MaxJournalBytes)
                        throw new LedgerBlocked();
                    byte[] bytes = new byte[(int)stream.Length];
                    int offset = 0;
                    while (offset < bytes.Length)
                    {
                        int next = stream.Read(bytes, offset,
                            bytes.Length - offset);
                        if (next <= 0) throw new LedgerBlocked();
                        offset += next;
                    }
                    if (stream.Length != bytes.Length)
                        throw new LedgerBlocked();
                    string result = StrictAscii.GetString(bytes);
                    CustodyLedger.Decode(result);
                    if (!JournalFileSafe(path)) throw new LedgerBlocked();
                    return result;
                }
            }
            catch (Exception) { throw new LedgerBlocked(); }
        }

        private static bool TrustedSid(SecurityIdentifier sid)
        {
            return sid != null && (
                sid.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                sid.IsWellKnown(WellKnownSidType.BuiltinAdministratorsSid) ||
                String.Equals(sid.Value, TrustedInstaller,
                    StringComparison.OrdinalIgnoreCase));
        }

        private static bool RegistryAclSafe(RegistrySecurity security)
        {
            try
            {
                if (security == null) return false;
                SecurityIdentifier owner = security.GetOwner(
                    typeof(SecurityIdentifier)) as SecurityIdentifier;
                if (!TrustedSid(owner)) return false;
                AuthorizationRuleCollection rules = security.GetAccessRules(
                    true, true, typeof(SecurityIdentifier));
                if (rules.Count == 0) return false;
                // Exact original anchor rule: ANY unknown ALLOW on this
                // private key disqualifies the read, even read-only rights.
                foreach (RegistryAccessRule rule in rules)
                {
                    if (rule.AccessControlType != AccessControlType.Allow)
                        continue;
                    if (!TrustedSid(rule.IdentityReference as SecurityIdentifier))
                        return false;
                }
                return true;
            }
            catch (Exception) { return false; }
        }

        private static string FixedRegistryString(RegistryKey key,
            string valueName)
        {
            object observed = key.GetValue(valueName, null,
                RegistryValueOptions.DoNotExpandEnvironmentNames);
            if (observed == null ||
                key.GetValueKind(valueName) != RegistryValueKind.String ||
                !(observed is string)) throw new LedgerBlocked();
            return (string)observed;
        }

        private static string ReadAnchor()
        {
            // LocalSystem only; fixed HKLM 64-bit view; read-only handles;
            // no RegCreate, SetValue, DeleteValue or RegFlushKey.
            if (!ActualLocalSystem() ||
                !ProtectedAcl.VerifyInstalledCustodyDirectory())
                throw new LedgerBlocked();
            try
            {
                using (RegistryKey root = RegistryKey.OpenBaseKey(
                    RegistryHive.LocalMachine, RegistryView.Registry64))
                {
                    using (RegistryKey parent = root.OpenSubKey(
                        ParentRegistry, false))
                    {
                        if (parent == null ||
                            !RegistryAclSafe(parent.GetAccessControl()))
                            throw new LedgerBlocked();
                    }
                    using (RegistryKey child = root.OpenSubKey(
                        ChildRegistry, false))
                    {
                        if (child == null ||
                            !RegistryAclSafe(child.GetAccessControl()))
                            throw new LedgerBlocked();
                        if (!String.Equals(FixedRegistryString(child,
                            FaultValue), "CLEAR", StringComparison.Ordinal))
                            throw new LedgerBlocked();
                        string anchor = FixedRegistryString(child, AnchorValue);
                        if (String.IsNullOrEmpty(anchor) ||
                            anchor.Length > 128)
                            throw new LedgerBlocked();
                        // Native J2/A2 verification below rejects malformed
                        // values, but only trusted fixed registry paths used.
                        return anchor;
                    }
                }
            }
            catch (Exception) { throw new LedgerBlocked(); }
        }

        internal static NativeJ2ReadOnlyResult ObserveInstalledService()
        {
            // ServiceGate's binary/manifest proofs are permanently false
            // until reviewed production installation. This always exits
            // UNAVAILABLE on Kristian and on unprivileged CI Windows.
            if (!ServiceGate.LiveEligible())
                return NativeJ2ReadOnlyResult.Unavailable();

            if (!CandidateCredentialEffectHold.LegacyEffectEntryDisabled() ||
                !CandidateCredentialEffectHold.NativeMutationAdmissionPending())
                return NativeJ2ReadOnlyResult.Recovery();

            if (!ActualLocalSystem() ||
                !ProtectedAcl.VerifyInstalledCustodyDirectory())
                return NativeJ2ReadOnlyResult.Recovery();

            try
            {
                string journal = ReadJournal();
                string anchor = ReadAnchor();
                LedgerPhase phase = CustodyLedger.Verify(journal, anchor);
                // Two independently persisted stores cannot be snapshotted
                // atomically here. Require repeat identity, but never treat
                // identical snapshots as an anti-rollback or G1 witness.
                if (!String.Equals(journal, ReadJournal(),
                    StringComparison.Ordinal) ||
                    !String.Equals(anchor, ReadAnchor(),
                    StringComparison.Ordinal))
                    return NativeJ2ReadOnlyResult.Recovery();

                return NativeJ2ReadOnlyResult.Structural(phase);
            }
            catch (Exception)
            {
                return NativeJ2ReadOnlyResult.Recovery();
            }
        }
    }
}
