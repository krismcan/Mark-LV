// P210: TEST-ONLY fixed synthetic Python->native subprocess negative integration.
// No installer, trusted service, IPC/pipe, credential, caller-selected target,
// real consent or WinCred. Uses the unchanged P208/P209 synthetic actors.
// This entire entrypoint is excluded from ordinary builds.
#if C1_SYNTHETIC_TEST
using System;
using System.IO;
using Nayeon.ByokC1;

internal static class P210SyntheticBoundaryExecutable
{
    private static bool Holds(P208SyntheticTerminalOwner owner)
    {
        return owner != null && !owner.NativeEffectEnabled &&
               !owner.AuthenticatedConsentAvailable &&
               !owner.ProductionReleaseEligible;
    }

    private static bool JournalHolds(P209SyntheticDurableCustody journal)
    {
        return journal != null && !journal.RealCredentialEffectAllowed &&
               !journal.AutomaticRetryAllowed &&
               !journal.ExternalAntirollbackWitnessAvailable;
    }

    private static string ExecuteFixedScenario(string mode, string file)
    {
        var owner=new P208SyntheticTerminalOwner();
        var journal=new P209SyntheticDurableCustody(file);
        if (!Holds(owner) || !JournalHolds(journal) || ServiceGate.LiveEligible())
            return "DENIED";

        if (mode=="missing-owner")
        {
            bool denied=owner.AttemptForTestOnly(null,LedgerOperation.Save,false)
                ==CustodyOutcome.Denied;
            return denied && owner.SyntheticEffectAttempts==0
                ? "MISSING_OWNER_REFUSED" : "DENIED";
        }
        if (mode=="forged-review")
        {
            var pending=owner.PrepareForTestOnly(LedgerOperation.Save,false);
            var forged=new P208SyntheticTerminalOwner.SyntheticReview();
            bool denied=pending!=null && owner.AttemptForTestOnly(
                forged,LedgerOperation.Save,false)==CustodyOutcome.Denied;
            return denied && owner.Revoked && owner.SyntheticEffectAttempts==0
                ? "FORGED_REVIEW_REFUSED" : "DENIED";
        }
        if (mode=="replay")
        {
            var review=owner.PrepareForTestOnly(LedgerOperation.Save,false);
            bool once=review!=null && owner.AttemptForTestOnly(
                review,LedgerOperation.Save,false)==CustodyOutcome.RecoveryRequired;
            bool replay=owner.AttemptForTestOnly(
                review,LedgerOperation.Save,false)==CustodyOutcome.RecoveryRequired;
            return once && replay && owner.SyntheticEffectAttempts==1 &&
                owner.AttemptCount==1 ? "REPLAY_RECOVERY_REQUIRED" : "DENIED";
        }
        if (mode=="crash-after-intent")
        {
            bool first=journal.InitializeSyntheticForTestOnly(LedgerOperation.Save,false)
                && journal.EnterSyntheticInflightForTestOnly();
            var restarted=new P209SyntheticDurableCustody(file);
            bool refused=restarted.Observe()==P209ObservedPhase.RecoveryRequired &&
                !restarted.EnterSyntheticInflightForTestOnly();
            return first && refused && owner.SyntheticEffectAttempts==0
                ? "CRASH_RECOVERY_REQUIRED" : "DENIED";
        }
        if (mode=="uncertain-effect")
        {
            bool before=journal.InitializeSyntheticForTestOnly(LedgerOperation.Save,false);
            var review=owner.PrepareForTestOnly(LedgerOperation.Save,false);
            bool intent=before && review!=null && journal.EnterSyntheticInflightForTestOnly();
            bool effect=intent && owner.AttemptForTestOnly(
                review,LedgerOperation.Save,true)==CustodyOutcome.RecoveryRequired;
            bool record=effect && journal.RecordSyntheticUncertaintyForTestOnly();
            var restarted=new P209SyntheticDurableCustody(file);
            return record && owner.SyntheticEffectAttempts==1 &&
                owner.SyntheticUnknownOutcomes==1 &&
                restarted.Observe()==P209ObservedPhase.RecoveryRequired &&
                !restarted.EnterSyntheticInflightForTestOnly()
                ? "UNCERTAIN_RECOVERY_REQUIRED" : "DENIED";
        }
        if (mode=="rollback-valid")
        {
            bool before=journal.InitializeSyntheticForTestOnly(LedgerOperation.Save,false);
            if(!before) return "DENIED";
            byte[] historical=File.ReadAllBytes(file);
            bool intent=journal.EnterSyntheticInflightForTestOnly();
            bool recorded=intent && journal.RecordSyntheticUncertaintyForTestOnly();
            if(!recorded) return "DENIED";
            // The same-user attacker can restore valid DPAPI ciphertext.
            // This is a documented *failure of independent antirollback*,
            // never permission to execute an effect.
            File.WriteAllBytes(file,historical);
            var restarted=new P209SyntheticDurableCustody(file);
            return restarted.Observe()==P209ObservedPhase.PreparedUntrusted &&
                !restarted.EnterSyntheticInflightForTestOnly() &&
                owner.SyntheticEffectAttempts==0
                ? "VALID_ROLLBACK_REFUSED" : "DENIED";
        }
        if (mode=="tamper")
        {
            if(!journal.InitializeSyntheticForTestOnly(LedgerOperation.Save,false))
                return "DENIED";
            byte[] cipher=File.ReadAllBytes(file);
            cipher[cipher.Length/2]^=0x55;
            File.WriteAllBytes(file,cipher);
            var after=new P209SyntheticDurableCustody(file);
            return after.Observe()==P209ObservedPhase.CorruptRefuse &&
                !after.EnterSyntheticInflightForTestOnly() &&
                owner.SyntheticEffectAttempts==0
                ? "TAMPER_REFUSED" : "DENIED";
        }
        if (mode=="revoke")
        {
            var review=owner.PrepareForTestOnly(LedgerOperation.Save,false);
            owner.Revoke();
            bool denied=review!=null && owner.AttemptForTestOnly(
                review,LedgerOperation.Save,false)==CustodyOutcome.Denied;
            return denied && owner.SyntheticEffectAttempts==0
                ? "REVOKED_REFUSED" : "DENIED";
        }
        if (mode=="delete-ack")
        {
            bool denied=owner.PrepareForTestOnly(LedgerOperation.Delete,false)==null;
            return denied && owner.SyntheticEffectAttempts==0
                ? "DELETE_ACK_REQUIRED" : "DENIED";
        }
        if (mode=="missing-journal")
        {
            return journal.Observe()==P209ObservedPhase.MissingRefuse &&
                !journal.EnterSyntheticInflightForTestOnly() &&
                owner.SyntheticEffectAttempts==0
                ? "MISSING_JOURNAL_REFUSED" : "DENIED";
        }
        return "DENIED";
    }

    public static int Main(string[] args)
    {
        // A fixed scenario name is not a credential request, IPC, approval,
        // secret, target path, review credential or provenance identity.
        // Unknown/extra arguments are simply refused.
        if(args==null || args.Length!=1 || args[0]==null ||
           args[0].Length>32)
        {
            Console.WriteLine("P210_STATUS=DENIED");
            return 0;
        }
        string root=Environment.GetEnvironmentVariable("RUNNER_TEMP");
        if(String.IsNullOrEmpty(root) || !Path.IsPathRooted(root) ||
           !Directory.Exists(root))
        {
            Console.WriteLine("P210_STATUS=DENIED");
            return 0;
        }
        string dir=Path.Combine(root,"nayeon-p210-"+Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(dir);
            string file=Path.Combine(dir,"synthetic-protected.journal");
            string result=ExecuteFixedScenario(args[0],file);
            Console.WriteLine("P210_STATUS="+result);
            Console.WriteLine("P210_REAL_EFFECT=NEVER_ENABLED");
            return result=="DENIED" ? 2 : 0;
        }
        catch(Exception)
        {
            Console.WriteLine("P210_STATUS=DENIED");
            return 2;
        }
        finally
        {
            try {Directory.Delete(dir,true);}catch(Exception){}
        }
    }
}
#endif
