// Read-only Windows DACL / owner preflight for the protected C1 service.
// No chmod, ACL, registry, process or credential mutation is performed.
using System;
using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;

namespace Nayeon.ByokC1
{
    internal static class ProtectedAcl
    {
        // NT SERVICE\\TrustedInstaller SID. Administrators and SYSTEM are
        // the only other principals accepted for write-capable allow ACEs.
        private const string TrustedInstaller =
            "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464";

        private static bool IsTrusted(SecurityIdentifier identity)
        {
            if (identity == null) return false;
            return identity.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                identity.IsWellKnown(WellKnownSidType.BuiltinAdministratorsSid) ||
                String.Equals(identity.Value, TrustedInstaller,
                              StringComparison.OrdinalIgnoreCase);
        }

        private static bool Hardened(FileSystemSecurity security)
        {
            try
            {
                SecurityIdentifier owner =
                    security.GetOwner(typeof(SecurityIdentifier)) as SecurityIdentifier;
                if (!IsTrusted(owner)) return false;
                AuthorizationRuleCollection rules = security.GetAccessRules(
                    true, true, typeof(SecurityIdentifier));
                // Refuse both null/ambiguous and empty DACL representations.
                // Do not mistake the absence of ACEs for verified protection.
                if (rules.Count == 0) return false;
                // Use ONLY individual mutation bits. Composite Modify and
                // FullControl include READ bits and would falsely refuse
                // harmless Users/Everyone read/execute ACEs.
                FileSystemRights dangerous = (
                    FileSystemRights.WriteData | FileSystemRights.AppendData |
                    FileSystemRights.WriteExtendedAttributes | FileSystemRights.WriteAttributes |
                    FileSystemRights.Delete | FileSystemRights.DeleteSubdirectoriesAndFiles |
                    FileSystemRights.ChangePermissions | FileSystemRights.TakeOwnership);
                foreach (FileSystemAccessRule rule in rules)
                {
                    if (rule.AccessControlType != AccessControlType.Allow)
                        continue;
                    SecurityIdentifier sid = rule.IdentityReference as SecurityIdentifier;
                    if (!IsTrusted(sid) && (rule.FileSystemRights & dangerous) != 0)
                        return false;
                }
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        private static bool PathIsSafeDirectory(string name)
        {
            try
            {
                DirectoryInfo folder = new DirectoryInfo(name);
                if (!folder.Exists ||
                    (folder.Attributes & FileAttributes.ReparsePoint) != 0)
                    return false;
                return Hardened(folder.GetAccessControl(AccessControlSections.Owner |
                     AccessControlSections.Access));
            }
            catch (Exception) { return false; }
        }

        private static bool PathIsSafeFile(string name)
        {
            try
            {
                FileInfo file = new FileInfo(name);
                if (!file.Exists || (file.Attributes & FileAttributes.ReparsePoint) != 0)
                    return false;
                return Hardened(file.GetAccessControl(AccessControlSections.Owner |
                     AccessControlSections.Access));
            }
            catch (Exception) { return false; }
        }

        internal static bool VerifyInstalledImage(string path, string expected)
        {
            if (String.IsNullOrWhiteSpace(path) || String.IsNullOrWhiteSpace(expected))
                return false;
            try
            {
                string root = Path.GetFullPath(
                    Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)
                ).TrimEnd(Path.DirectorySeparatorChar);
                string actual = Path.GetFullPath(path);
                string fixedImage = Path.GetFullPath(expected);
                if (!String.Equals(actual, fixedImage,
                    StringComparison.OrdinalIgnoreCase)) return false;

                DirectoryInfo folder = Directory.GetParent(actual);
                if (folder == null) return false;
                // Verify every directory from installed executable up through
                // Program Files, rejecting any missing/reparse/writable ancestor.
                while (folder != null)
                {
                    if (!PathIsSafeDirectory(folder.FullName)) return false;
                    if (String.Equals(folder.FullName.TrimEnd(Path.DirectorySeparatorChar),
                         root, StringComparison.OrdinalIgnoreCase))
                        return PathIsSafeFile(actual);
                    if (!folder.FullName.StartsWith(
                        root + Path.DirectorySeparatorChar,
                        StringComparison.OrdinalIgnoreCase)) return false;
                    folder = folder.Parent;
                }
            }
            catch (Exception) { return false; }
            return false;
        }

        internal static string ExpectedCustodyDirectory()
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
                "Nayeon", "BYOK-C1-Custody");
        }

        internal static bool VerifyCustodyEvidenceFile(string path)
        {
            try
            {
                string expected=Path.Combine(ExpectedCustodyDirectory(),
                    "pending-custody-v2.journal");
                return String.Equals(Path.GetFullPath(path),
                    Path.GetFullPath(expected),StringComparison.OrdinalIgnoreCase)
                    && VerifyInstalledCustodyDirectory()
                    && PathIsSafeFile(path);
            }
            catch(Exception) {return false;}
        }

        private static bool ProtectedRootDacl(FileSystemSecurity security)
        {
            try
            {
                SecurityIdentifier owner=security.GetOwner(
                    typeof(SecurityIdentifier)) as SecurityIdentifier;
                if(!IsTrusted(owner))return false;
                AuthorizationRuleCollection rules=security.GetAccessRules(
                    true,true,typeof(SecurityIdentifier));
                if(rules.Count==0)return false;
                // ProgramData may let Users CREATE unrelated directories.
                // It must NOT let them delete/replace established descendants
                // or alter the ancestor's security/ownership or attributes.
                FileSystemRights harmful=FileSystemRights.Delete |
                    FileSystemRights.DeleteSubdirectoriesAndFiles |
                    FileSystemRights.ChangePermissions |
                    FileSystemRights.TakeOwnership |
                    FileSystemRights.WriteAttributes |
                    FileSystemRights.WriteExtendedAttributes;
                foreach(FileSystemAccessRule rule in rules)
                {
                    if(rule.AccessControlType!=AccessControlType.Allow)continue;
                    SecurityIdentifier sid=rule.IdentityReference as SecurityIdentifier;
                    if(!IsTrusted(sid) && (rule.FileSystemRights&harmful)!=0)
                        return false;
                }
                return true;
            }
            catch(Exception){return false;}
        }

        internal static bool VerifyInstalledCustodyDirectory()
        {
            try
            {
                string root=Path.GetFullPath(
                    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData));
                DirectoryInfo baseFolder=new DirectoryInfo(root);
                if(!baseFolder.Exists ||
                    (baseFolder.Attributes & FileAttributes.ReparsePoint)!=0)
                    return false;
                if(!ProtectedRootDacl(baseFolder.GetAccessControl(
                    AccessControlSections.Owner|AccessControlSections.Access)))
                    return false;
                // ProgramData itself may permit users to CREATE unrelated
                // siblings. The dedicated parent and custody folder cannot.
                string parent=Path.Combine(root,"Nayeon");
                string custody=ExpectedCustodyDirectory();
                return PathIsSafeDirectory(parent) &&
                    PathIsSafeDirectory(custody) &&
                    String.Equals(Path.GetFullPath(custody),
                        Path.Combine(parent,"BYOK-C1-Custody"),
                        StringComparison.OrdinalIgnoreCase);
            }
            catch(Exception) {return false;}
        }
    }
}
