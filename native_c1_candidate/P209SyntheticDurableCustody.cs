// P209: Windows DPAPI CurrentUser + DACL synthetic custody ONLY.
// This is not a production journal, WinCred adapter, service, signer, IPC,
// antirollback anchor or credential effect permission. No real secrets.
// Compiles away unless C1_SYNTHETIC_TEST is explicitly defined.
#if C1_SYNTHETIC_TEST
using System;
using System.Globalization;
using System.IO;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;

namespace Nayeon.ByokC1
{
    internal enum P209ObservedPhase
    {
        MissingRefuse,
        PreparedUntrusted,
        RecoveryRequired,
        CorruptRefuse
    }

    internal sealed class P209SyntheticDurableCustody
    {
        private enum RecordPhase { Prepared=1, InFlight=2, Recovery=3 }
        private const string Version = "P209SYNTHETIC1";
        private const string Target = "nayeon-v1/secret/openai.api_key";
        private readonly object gate = new object();
        private readonly string path;
        private Guid epoch = Guid.Empty;
        private LedgerOperation operation;
        private bool initializationAttempted;
        private bool canAdvance;
        private bool canFinalize;
        private bool uncertain;

        internal P209SyntheticDurableCustody(string originalPath)
        {
            if (String.IsNullOrEmpty(originalPath) ||
                !Path.IsPathRooted(originalPath))
                throw new ArgumentException("P209 test-only absolute path required");
            path=Path.GetFullPath(originalPath);
        }

        internal bool RealCredentialEffectAllowed { get { return false; } }
        internal bool AutomaticRetryAllowed { get { return false; } }
        internal bool ExternalAntirollbackWitnessAvailable { get { return false; } }

        private static bool Valid(LedgerOperation op, bool deleteAck)
        {
            return ((op==LedgerOperation.Save || op==LedgerOperation.Replace)
                && !deleteAck) || (op==LedgerOperation.Delete && deleteAck);
        }

        private static FileSecurity UserOnlyAcl()
        {
            SecurityIdentifier user=WindowsIdentity.GetCurrent().User;
            if (user==null) throw new UnauthorizedAccessException("No user SID");
            var acl=new FileSecurity();
            acl.SetAccessRuleProtection(true,false);
            acl.SetOwner(user);
            acl.AddAccessRule(new FileSystemAccessRule(user,
                FileSystemRights.FullControl,AccessControlType.Allow));
            return acl;
        }

        private byte[] ProtectedRecord(RecordPhase phase, int generation)
        {
            // Pure metadata, not a credential. DPAPI is a real Windows API
            // for a nonprivileged disposable synthetic test file only.
            string plain=Version+"|"+((int)phase).ToString(CultureInfo.InvariantCulture)+
                "|"+((int)operation).ToString(CultureInfo.InvariantCulture)+
                "|"+generation.ToString(CultureInfo.InvariantCulture)+
                "|"+epoch.ToString("N")+"|"+Target;
            return ProtectedData.Protect(Encoding.UTF8.GetBytes(plain),
                null,DataProtectionScope.CurrentUser);
        }

        private static bool TryDecode(byte[] bytes, out RecordPhase phase,
            out LedgerOperation op, out int generation, out Guid id)
        {
            phase=RecordPhase.Recovery;op=(LedgerOperation)0;
            generation=0;id=Guid.Empty;
            try
            {
                if (bytes==null || bytes.Length<32 || bytes.Length>4096)
                    return false;
                string text=Encoding.UTF8.GetString(ProtectedData.Unprotect(
                    bytes,null,DataProtectionScope.CurrentUser));
                string[] x=text.Split('|');
                int p,o,g;
                Guid parsed;
                if (x.Length!=6 || x[0]!=Version || x[5]!=Target ||
                    !Int32.TryParse(x[1],NumberStyles.None,
                        CultureInfo.InvariantCulture,out p) ||
                    !Int32.TryParse(x[2],NumberStyles.None,
                        CultureInfo.InvariantCulture,out o) ||
                    !Int32.TryParse(x[3],NumberStyles.None,
                        CultureInfo.InvariantCulture,out g) ||
                    !Guid.TryParseExact(x[4],"N",out parsed) ||
                    g<1 || parsed==Guid.Empty ||
                    (o!=(int)LedgerOperation.Save &&
                     o!=(int)LedgerOperation.Replace &&
                     o!=(int)LedgerOperation.Delete) ||
                    (p!=(int)RecordPhase.Prepared &&
                     p!=(int)RecordPhase.InFlight &&
                     p!=(int)RecordPhase.Recovery))
                    return false;
                phase=(RecordPhase)p; op=(LedgerOperation)o;
                generation=g;id=parsed;
                return true;
            }
            catch(Exception) { return false; }
        }

        private bool TryRead(out RecordPhase phase, out LedgerOperation op,
            out int generation, out Guid id)
        {
            phase=RecordPhase.Recovery;op=(LedgerOperation)0;
            generation=0;id=Guid.Empty;
            try
            {
                if(!File.Exists(path)) return false;
                return TryDecode(File.ReadAllBytes(path),out phase,out op,
                    out generation,out id);
            }
            catch(Exception) { return false; }
        }

        internal P209ObservedPhase Observe()
        {
            lock(gate)
            {
                // Missing, corrupt or unreadable files are NEVER effect grants.
                // DPAPI cannot distinguish valid same-user historic rollback.
                try
                {
                    if (!File.Exists(path)) return P209ObservedPhase.MissingRefuse;
                    RecordPhase p;LedgerOperation op;int gen;Guid id;
                    if(!TryRead(out p,out op,out gen,out id))
                        return P209ObservedPhase.CorruptRefuse;
                    if(p==RecordPhase.Prepared)
                        return P209ObservedPhase.PreparedUntrusted;
                    return P209ObservedPhase.RecoveryRequired;
                }
                catch(Exception) { return P209ObservedPhase.CorruptRefuse; }
            }
        }

        private bool Persist(RecordPhase phase, int generation)
        {
            string temporary=null;
            try
            {
                string directory=Path.GetDirectoryName(path);
                if(!Directory.Exists(directory) ||
                    (File.GetAttributes(directory)&FileAttributes.ReparsePoint)!=0)
                    return false;
                temporary=path+"."+Guid.NewGuid().ToString("N")+".tmp";
                byte[] bytes=ProtectedRecord(phase,generation);
                using(var file=new FileStream(temporary,FileMode.CreateNew,
                    FileSystemRights.Write,FileShare.None,4096,
                    FileOptions.WriteThrough,UserOnlyAcl()))
                {
                    file.Write(bytes,0,bytes.Length);
                    file.Flush(true);
                }
                if(File.Exists(path))
                    File.Replace(temporary,path,null,true);
                else
                    File.Move(temporary,path);
                temporary=null;
                return true;
            }
            catch(Exception) { return false; }
            finally
            {
                if(temporary!=null)
                    try { File.Delete(temporary); } catch(Exception) { }
            }
        }

        // TEST-ONLY fixture writer, not authority issuance. No effects exist.
        internal bool InitializeSyntheticForTestOnly(
            LedgerOperation op,bool destructiveAcknowledged)
        {
            lock(gate)
            {
                if(initializationAttempted || uncertain || !Valid(op,destructiveAcknowledged))
                    return false;
                initializationAttempted=true;
                if(File.Exists(path)) { uncertain=true; return false; }
                epoch=Guid.NewGuid();operation=op;
                if(!Persist(RecordPhase.Prepared,1))
                { uncertain=true;return false; }
                canAdvance=true;
                return true;
            }
        }

        // Transition to durable IN_FLIGHT *before* any possible fake actor
        // attempt. New/restarted instances are NEVER armed by disk content.
        internal bool EnterSyntheticInflightForTestOnly()
        {
            lock(gate)
            {
                if(!canAdvance || uncertain) return false;
                canAdvance=false; // no retry on uncertain write
                RecordPhase p;LedgerOperation op;int gen;Guid id;
                if(!TryRead(out p,out op,out gen,out id) ||
                   p!=RecordPhase.Prepared || gen!=1 ||
                   op!=operation || id!=epoch ||
                   !Persist(RecordPhase.InFlight,2))
                { uncertain=true;return false; }
                canFinalize=true;
                return true;
            }
        }

        internal bool RecordSyntheticUncertaintyForTestOnly()
        {
            lock(gate)
            {
                if(!canFinalize || uncertain) return false;
                canFinalize=false;
                RecordPhase p;LedgerOperation op;int gen;Guid id;
                if(!TryRead(out p,out op,out gen,out id) ||
                   p!=RecordPhase.InFlight || gen!=2 ||
                   op!=operation || id!=epoch ||
                   !Persist(RecordPhase.Recovery,3))
                { uncertain=true;return false; }
                uncertain=true; // never permit rearm
                return true;
            }
        }
    }
}
#endif
