// BYOK C1 — LocalSystem-owned protected HKLM custody anchor.
// Production-target read/write adapter. Does NOT provision/create a registry
// key, modify permissions, hold an API key, call WinCred, or permit providers.
// Before use, service owner + protected registry parent/child DACL MUST pass.
// It is an independent freshness witness ONLY when protected from the same
// non-elevated user that could otherwise modify the custody journal.
using System;
using System.Globalization;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using Microsoft.Win32.SafeHandles;

namespace Nayeon.ByokC1
{
    internal sealed class CustodyRegistryAnchor
    {
        private const string KeyName=@"SOFTWARE\Nayeon\BYOK-C1";
        private const string ParentName=@"SOFTWARE\Nayeon";
        private const string AnchorValue="CustodyAnchorV2";
        private const string FaultValue="CustodyFaultV1";
        private const string MutexNonceValue="MutexNonceV1";
        [DllImport("advapi32.dll", EntryPoint="RegFlushKey", ExactSpelling=true)]
        private static extern int NativeRegFlushKey(SafeRegistryHandle handle);

        internal static bool NativeFlushSucceeded(int code)
        {
            return code==0;
        }

        private static void FlushChecked(RegistryKey key)
        {
            // RegistryKey.Flush() on .NET Framework ignores RegFlushKey
            // native status; a cached readback does not prove flush success.
            int code=NativeRegFlushKey(key.Handle);
            if(!NativeFlushSucceeded(code))throw new LedgerBlocked();
        }
        private const string TrustedInstaller=
            "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464";

        private static bool TrustedSid(SecurityIdentifier sid)
        {
            return sid!=null &&
                (sid.IsWellKnown(WellKnownSidType.LocalSystemSid) ||
                 sid.IsWellKnown(WellKnownSidType.BuiltinAdministratorsSid) ||
                 String.Equals(sid.Value,TrustedInstaller,
                    StringComparison.OrdinalIgnoreCase));
        }

        internal static bool ApprovedDacl(RegistrySecurity security)
        {
            try
            {
                if(security==null)return false;
                SecurityIdentifier owner=security.GetOwner(
                    typeof(SecurityIdentifier)) as SecurityIdentifier;
                if(!TrustedSid(owner))return false;
                AuthorizationRuleCollection rules=security.GetAccessRules(
                    true,true,typeof(SecurityIdentifier));
                if(rules.Count==0)return false;
                // This anchor KEY also stores an unguessable private mutex
                // namespace nonce. Ordinary user READ is not authorised.
                // The privileged installer must disable inherited Users read
                // ACLs; unknown grants fail closed, including QueryValues.
                foreach(RegistryAccessRule rule in rules)
                {
                    if(rule.AccessControlType!=AccessControlType.Allow)
                        continue;
                    SecurityIdentifier sid=rule.IdentityReference as SecurityIdentifier;
                    if(!TrustedSid(sid))
                        return false;
                }
                return true;
            }
            catch(Exception){return false;}
        }

        private static bool NativeServiceToken()
        {
            try
            {
                WindowsIdentity id=WindowsIdentity.GetCurrent();
                return id!=null && id.User!=null &&
                    id.User.IsWellKnown(WellKnownSidType.LocalSystemSid);
            }
            catch(Exception){return false;}
        }

        private static RegistryKey OpenFixed(bool write)
        {
            if(!NativeServiceToken() ||
                !ProtectedAcl.VerifyInstalledCustodyDirectory())
                throw new LedgerBlocked();
            try
            {
                RegistryKey root=RegistryKey.OpenBaseKey(
                    RegistryHive.LocalMachine,RegistryView.Registry64);
                try
                {
                    using(RegistryKey parent=root.OpenSubKey(ParentName,false))
                    {
                        if(parent==null || !ApprovedDacl(parent.GetAccessControl()))
                            throw new LedgerBlocked();
                    }
                    RegistryKey child=root.OpenSubKey(KeyName,write);
                    if(child==null)throw new LedgerBlocked();
                    try
                    {
                        if(!ApprovedDacl(child.GetAccessControl()))
                            throw new LedgerBlocked();
                        return child;
                    }
                    catch(Exception)
                    {
                        child.Dispose();throw;
                    }
                }
                finally{root.Dispose();}
            }
            catch(Exception){throw new LedgerBlocked();}
        }

        private static bool CanonicalAnchor(string value)
        {
            if(String.IsNullOrEmpty(value) || value.Length>128)return false;
            string[] fields=value.Split('|');
            if(fields.Length!=4 || fields[0]!="A2" ||
                fields[1].Length<1 || fields[1].Length>3 ||
                fields[2].Length<1 || fields[2].Length>16 ||
                fields[3].Length!=64)
                return false;
            foreach(char ch in value)
                if(ch<33 || ch>126)return false;
            foreach(char ch in fields[1]+fields[2])
                if(ch<'0'||ch>'9')return false;
            if(fields[1].Length>1 && fields[1][0]=='0' ||
                fields[2].Length>1 && fields[2][0]=='0')
                return false;
            foreach(char ch in fields[3])
                if(!((ch>='0'&&ch<='9')||(ch>='a'&&ch<='f')))
                    return false;
            long seq,gen;
            return Int64.TryParse(fields[1],NumberStyles.None,
                CultureInfo.InvariantCulture,out seq) && seq>=1 && seq<=128 &&
                Int64.TryParse(fields[2],NumberStyles.None,
                CultureInfo.InvariantCulture,out gen) &&
                gen>=0 && gen<=1000000000000L;
        }

        private static string ReadFrom(RegistryKey key)
        {
            object current=key.GetValue(AnchorValue,null,
                RegistryValueOptions.DoNotExpandEnvironmentNames);
            if(current==null)return null;
            if(key.GetValueKind(AnchorValue)!=RegistryValueKind.String ||
               !(current is string) || !CanonicalAnchor((string)current))
                throw new LedgerBlocked();
            return (string)current;
        }

        internal string ReadAnchor()
        {
            try
            {
                using(RegistryKey key=OpenFixed(false))
                    return ReadFrom(key);
            }
            catch(Exception){throw new LedgerBlocked();}
        }

        internal string ReadMutexNonce()
        {
            try
            {
                using(RegistryKey key=OpenFixed(false))
                {
                    object observed=key.GetValue(MutexNonceValue,null,
                        RegistryValueOptions.DoNotExpandEnvironmentNames);
                    if(key.GetValueKind(MutexNonceValue)!=RegistryValueKind.String ||
                        !(observed is string))
                        throw new LedgerBlocked();
                    string nonce=(string)observed;
                    if(nonce.Length!=32)throw new LedgerBlocked();
                    foreach(char ch in nonce)
                        if(!((ch>='0'&&ch<='9')||(ch>='a'&&ch<='f')))
                            throw new LedgerBlocked();
                    return nonce;
                }
            }
            catch(Exception){throw new LedgerBlocked();}
        }

        internal bool RecoveryFaulted()
        {
            try
            {
                using(RegistryKey key=OpenFixed(false))
                {
                    object observed=key.GetValue(FaultValue,null,
                        RegistryValueOptions.DoNotExpandEnvironmentNames);
                    // On every new installed service start, a missing fault
                    // marker MUST deny, not silently bootstrap as healthy.
                    if(observed==null ||
                       key.GetValueKind(FaultValue)!=RegistryValueKind.String)
                        return true;
                    return !String.Equals(observed as string,"CLEAR",
                        StringComparison.Ordinal);
                }
            }
            catch(Exception){return true;}
        }

        internal void WriteAnchor(string expected,string replacement)
        {
            if(!CanonicalAnchor(replacement) ||
                (expected!=null && !CanonicalAnchor(expected)))
                throw new LedgerBlocked();
            // No user-controlled value names, paths or dynamic provider.
            try
            {
                using(RegistryKey key=OpenFixed(true))
                {
                    string current=ReadFrom(key);
                    if(!String.Equals(current,expected,StringComparison.Ordinal))
                        throw new LedgerBlocked();
                    key.SetValue(AnchorValue,replacement,RegistryValueKind.String);
                    FlushChecked(key);
                    if(!String.Equals(ReadFrom(key),replacement,
                        StringComparison.Ordinal))
                        throw new LedgerBlocked();
                }
                if(!String.Equals(ReadAnchor(),replacement,
                    StringComparison.Ordinal))
                    throw new LedgerBlocked();
            }
            catch(Exception){throw new LedgerBlocked();}
        }
    }
}
