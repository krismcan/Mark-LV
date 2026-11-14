// P209 genuine Windows DPAPI + DACL test executable. No real credentials.
// Original P49/P96/native C1 test-only source identities remain untouched.
#if C1_SYNTHETIC_TEST
using System;
using System.IO;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using Nayeon.ByokC1;

internal static class P209SyntheticDurableCustodyTests
{
    private static int passed,failed;
    private static string root;

    private static void Check(bool value,string reason)
    { if(!value) throw new InvalidOperationException("P209 "+reason); }

    private static void Run(string label,Action body)
    {
        try {body();++passed;Console.WriteLine("PASS "+label);}
        catch(Exception e)
        {++failed;Console.WriteLine("FAIL "+label+" "+e.GetType().Name);}
    }

    private static string NewPath()
    { return Path.Combine(root,Guid.NewGuid().ToString("N")+".journal"); }

    private static P209SyntheticDurableCustody Journal(string path)
    { return new P209SyntheticDurableCustody(path); }

    private static P209SyntheticDurableCustody FreshPrepared(out string path)
    {
        path=NewPath();
        var journal=Journal(path);
        Check(journal.InitializeSyntheticForTestOnly(LedgerOperation.Save,false),
            "must write synthetic prepared");
        return journal;
    }

    public static int Main()
    {
        string runner=Environment.GetEnvironmentVariable("RUNNER_TEMP");
        if(String.IsNullOrEmpty(runner) || !Path.IsPathRooted(runner))
            throw new InvalidOperationException("P209 requires isolated Windows RUNNER_TEMP");
        root=Path.Combine(runner,"nayeon-p209-synthetic-"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        Run("missing-file-is-permanent-denial-observation",delegate {
            var j=Journal(NewPath());
            Check(j.Observe()==P209ObservedPhase.MissingRefuse,"no journal");
            Check(!j.RealCredentialEffectAllowed && !j.AutomaticRetryAllowed,
                  "no effect or retry");
        });
        Run("malformed-operation-refuses-initialization",delegate {
            string p=NewPath();
            Check(!Journal(p).InitializeSyntheticForTestOnly((LedgerOperation)999,false),
                  "invalid enum");
            Check(!File.Exists(p),"no file");
        });
        Run("wrong-delete-ack-refused",delegate {
            string p=NewPath();
            Check(!Journal(p).InitializeSyntheticForTestOnly(LedgerOperation.Delete,false),
                "delete ack required");
            Check(!File.Exists(p),"no file");
        });
        Run("prepared-synthetic-written-not-authoritative",delegate {
            string path;var j=FreshPrepared(out path);
            Check(File.Exists(path),"written");
            Check(j.Observe()==P209ObservedPhase.PreparedUntrusted,"prepared untrusted");
            Check(!j.RealCredentialEffectAllowed && !j.ExternalAntirollbackWitnessAvailable,
                "never authority");
        });
        Run("on-disk-journal-is-real-Windows-DPAPI-encrypted",delegate {
            string path;var j=FreshPrepared(out path);
            byte[] data=File.ReadAllBytes(path);
            string text=Encoding.UTF8.GetString(data);
            Check(data.Length>32 && data.Length<4096,"bounded DPAPI envelope");
            Check(!text.Contains("P209SYNTHETIC1") &&
                  !text.Contains("nayeon-v1/secret/openai.api_key"),
                  "not plaintext");
            Check(j.Observe()==P209ObservedPhase.PreparedUntrusted,"DPAPI decrypt");
        });
        Run("on-disk-file-has-current-user-explicit-owner-ACL",delegate {
            string path;FreshPrepared(out path);
            var owner=File.GetAccessControl(path).GetOwner(typeof(SecurityIdentifier));
            var me=WindowsIdentity.GetCurrent().User;
            Check(owner.Equals(me),"actual DACL file owner");
        });
        Run("duplicate-creation-on-original-path-refused",delegate {
            string path;var j=FreshPrepared(out path);
            Check(!j.InitializeSyntheticForTestOnly(LedgerOperation.Save,false),
                "same instance no reissue");
            Check(!Journal(path).InitializeSyntheticForTestOnly(LedgerOperation.Save,false),
                "fresh owner cannot overwrite");
        });
        Run("inflight-state-is-durably-written-before-any-fake-effect",delegate {
            string path;var j=FreshPrepared(out path);
            Check(j.EnterSyntheticInflightForTestOnly(),"intent write");
            Check(j.Observe()==P209ObservedPhase.RecoveryRequired,"uncertain inflight");
            Check(!j.RealCredentialEffectAllowed,"no effect");
        });
        Run("restart-after-INFLIGHT-returns-recovery-only",delegate {
            string path;var first=FreshPrepared(out path);
            Check(first.EnterSyntheticInflightForTestOnly(),"intent");
            var after=Journal(path);
            Check(after.Observe()==P209ObservedPhase.RecoveryRequired,
                "reload with actual Windows DPAPI");
            Check(!after.RealCredentialEffectAllowed && !after.AutomaticRetryAllowed,
                "never rearm");
        });
        Run("restarted-owner-cannot-resubmit-old-intent",delegate {
            string path;var first=FreshPrepared(out path);
            Check(first.EnterSyntheticInflightForTestOnly(),"intent");
            var after=Journal(path);
            Check(!after.EnterSyntheticInflightForTestOnly(),"fresh owner no permit");
            Check(!after.RecordSyntheticUncertaintyForTestOnly(),"no forged terminal");
        });
        Run("recovery-record-is-durable-and-sticky",delegate {
            string path;var j=FreshPrepared(out path);
            Check(j.EnterSyntheticInflightForTestOnly(),"intent");
            Check(j.RecordSyntheticUncertaintyForTestOnly(),"record unknown");
            var after=Journal(path);
            Check(after.Observe()==P209ObservedPhase.RecoveryRequired,"reload unknown");
            Check(!after.EnterSyntheticInflightForTestOnly(),"no retry");
        });
        Run("DPAPI-tamper-cannot-be-admitted",delegate {
            string path;var j=FreshPrepared(out path);
            byte[] b=File.ReadAllBytes(path);
            b[b.Length/2]^=0x5A;
            File.WriteAllBytes(path,b);
            Check(j.Observe()==P209ObservedPhase.CorruptRefuse,"tamper deny");
            Check(!j.EnterSyntheticInflightForTestOnly(),"no transition");
        });
        Run("torn-DRAM-truncated-record-refused",delegate {
            string path;var j=FreshPrepared(out path);
            File.WriteAllBytes(path,new byte[]{1,2,3,4,5});
            Check(j.Observe()==P209ObservedPhase.CorruptRefuse,"truncated");
            Check(!j.EnterSyntheticInflightForTestOnly(),"no advance");
        });
        Run("rolled-back-valid-prepared-record-is-not-effect-authority",delegate {
            string path;var j=FreshPrepared(out path);
            byte[] old=File.ReadAllBytes(path);
            Check(j.EnterSyntheticInflightForTestOnly(),"first");
            Check(j.RecordSyntheticUncertaintyForTestOnly(),"terminal");
            File.WriteAllBytes(path,old);
            var after=Journal(path);
            Check(after.Observe()==P209ObservedPhase.PreparedUntrusted,
                "valid historical DPAPI still decrypts");
            Check(!after.RealCredentialEffectAllowed &&
                  !after.EnterSyntheticInflightForTestOnly(),
                "valid rollback must not mint effect");
            // This reveals absent independent antirollback witness, NOT G3 GO.
        });
        Run("deleted-journal-after-known-inflight-never-grants",delegate {
            string path;var j=FreshPrepared(out path);
            Check(j.EnterSyntheticInflightForTestOnly(),"intent");
            File.Delete(path);
            var after=Journal(path);
            Check(after.Observe()==P209ObservedPhase.MissingRefuse,"missing");
            Check(!after.EnterSyntheticInflightForTestOnly(),"no auto reissue");
        });
        Run("same-user-forged-Windows-DPAPI-wrong-target-is-refused",delegate {
            string path;var j=FreshPrepared(out path);
            string wrong="P209SYNTHETIC1|1|1|1|"+
                Guid.NewGuid().ToString("N")+"|nayeon-v1/secret/other.key";
            byte[] encrypted=ProtectedData.Protect(Encoding.UTF8.GetBytes(wrong),
                null,DataProtectionScope.CurrentUser);
            File.WriteAllBytes(path,encrypted);
            Check(j.Observe()==P209ObservedPhase.CorruptRefuse,"wrong target");
        });
        Run("test-only-P208-one-fake-effect-after-durable-intent",delegate {
            string path;var journal=FreshPrepared(out path);
            var actor=new P208SyntheticTerminalOwner();
            var review=actor.PrepareForTestOnly(LedgerOperation.Save,false);
            Check(review!=null,"synthetic review");
            Check(journal.EnterSyntheticInflightForTestOnly(),"durable intent FIRST");
            Check(actor.AttemptForTestOnly(review,LedgerOperation.Save,false)
                ==CustodyOutcome.RecoveryRequired,"unknown outcome");
            Check(journal.RecordSyntheticUncertaintyForTestOnly(),"persist recovery");
            Check(actor.SyntheticEffectAttempts==1,"one integer fake");
            Check(Journal(path).Observe()==P209ObservedPhase.RecoveryRequired,
                "reopen recovery only");
            Check(!actor.NativeEffectEnabled,"real native effect disabled");
        });
        Run("no-actual-WinCred-no-retry-no-independent-authority",delegate {
            string path;var j=FreshPrepared(out path);
            Check(!j.RealCredentialEffectAllowed && !j.AutomaticRetryAllowed &&
                  !j.ExternalAntirollbackWitnessAvailable,"strict holds");
            Check(!ServiceGate.LiveEligible(),"original native service hold");
        });
        Console.WriteLine("P209_WINDOWS_PROTECTED_SYNTHETIC_PASSED="+passed);
        Console.WriteLine("P209_WINDOWS_PROTECTED_SYNTHETIC_FAILED="+failed);
        Console.WriteLine("P209_REAL_WIN_CRED_EFFECTS=ZERO|G3_EXTERNAL_ANTIROLLBACK=OPEN");
        try{ Directory.Delete(root,true); }catch(Exception){}
        return failed==0 && passed==18?0:1;
    }
}
#endif
