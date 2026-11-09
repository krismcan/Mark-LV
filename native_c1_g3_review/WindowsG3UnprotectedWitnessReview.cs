// P130 — TWO UNPROTECTED Windows TEMP review files: staged journal + a
// separate, UNKEYED witness snapshot. Real OS file persistence / restart
// tests only. The witness is NOT independently trusted: same-user actors
// can tamper with, delete, replace, or roll back BOTH files together.
// No signed service, HKLM, protected DACL, monotonic hardware witness,
// credential, secret, grant, production authority or actual WinCred.
// This source cannot compile in a normal desktop/service build.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P130 unprotected witness review requires BOTH isolated and synthetic flags
#endif
using System;
using System.IO;
using System.Security.Cryptography;

namespace Nayeon.ByokC1
{
    internal enum G3ReviewWitnessState
    {
        BothMissingUnsafe,
        JournalWithoutWitness,
        WitnessWithoutJournal,
        JournalMalformed,
        WitnessMalformed,
        HistoryMismatch,
        ConsistentButUntrusted
    }

    internal sealed class G3ReviewWitnessObservation
    {
        internal readonly G3ReviewWitnessState State;
        internal readonly int JournalCount;
        internal readonly int WitnessCount;

        internal G3ReviewWitnessObservation(
            G3ReviewWitnessState state,int journalCount,int witnessCount)
        {
            State=state;
            JournalCount=journalCount;
            WitnessCount=witnessCount;
        }
        internal bool MatchedForDiagnosticOnly
        {get{return State==G3ReviewWitnessState.ConsistentButUntrusted;}}
        internal bool IndependentProtectionProven {get{return false;}}
        internal bool HistoricalEnrollmentVerified {get{return false;}}
        internal bool AntiRollbackEstablished {get{return false;}}
        internal bool SignedServiceAuthenticated {get{return false;}}
        internal bool ProtectedJournalVerified {get{return false;}}
        internal bool HumanConsentVerified {get{return false;}}
        internal bool DurableOneUseGrantVerified {get{return false;}}
        internal bool NativeCredentialEffectAllowed {get{return false;}}
        internal bool ProductionAdmissionAllowed {get{return false;}}
        public override string ToString()
        {return "<P130 two unprotected OS files; no independent trust, no credential effect>";}
    }

    internal sealed class WindowsG3UnprotectedWitnessReview
    {
        private const int WitnessSize=70;
        private const int PreimageSize=38;
        private const int HashSize=32;
        private const int MaxStages=3;
        private readonly WindowsG3EphemeralReviewJournal journal;
        private readonly string witnessPath;

        internal WindowsG3UnprotectedWitnessReview(string isolatedId)
        {
            // Constructor of P128 validates 32 canonical lowercase hex
            // characters, which prevents arbitrary paths/targets.
            journal=new WindowsG3EphemeralReviewJournal(isolatedId);
            witnessPath=Path.Combine(Path.GetTempPath(),
                "nayeon-c1-p130-"+isolatedId+".witness");
        }
        internal WindowsG3EphemeralReviewJournal JournalForSyntheticTests
        {get{return journal;}}
        internal string UntrustedWitnessPathForTests
        {get{return witnessPath;}}

        private static bool Equal32(byte[] a,int aOffset,byte[] b)
        {
            if(a==null||b==null||b.Length!=HashSize ||
                aOffset<0||a.Length-aOffset<HashSize)
                return false;
            int differences=0;
            for(int i=0;i<HashSize;i++)
                differences|=a[aOffset+i]^b[i];
            return differences==0;
        }
        private static byte[] Digest(byte[] bytes,int length)
        {
            using(var sha=SHA256.Create())
                return sha.ComputeHash(bytes,0,length);
        }
        private static byte[] BoundedRead(string path,int max)
        {
            using(var fs=new FileStream(path,FileMode.Open,
                FileAccess.Read,FileShare.ReadWrite))
            {
                long length=fs.Length;
                if(length<0||length>max)return null;
                byte[] bytes=new byte[(int)length];
                int offset=0;
                while(offset<bytes.Length)
                {
                    int read=fs.Read(bytes,offset,bytes.Length-offset);
                    if(read<=0)return null;
                    offset+=read;
                }
                return bytes;
            }
        }
        private static bool DecodeWitness(byte[] bytes,
            out int stages,out byte[] journalHash)
        {
            stages=0;journalHash=null;
            if(bytes==null||bytes.Length!=WitnessSize ||
                bytes[0]!=(byte)'W'||bytes[1]!=(byte)'1'||
                bytes[2]!=(byte)'3'||bytes[3]!=(byte)'0'||
                bytes[4]!=1||bytes[5]<1||bytes[5]>MaxStages)
                return false;
            byte[] checksum=Digest(bytes,PreimageSize);
            if(!Equal32(bytes,PreimageSize,checksum))
                return false;
            journalHash=new byte[HashSize];
            Buffer.BlockCopy(bytes,6,journalHash,0,HashSize);
            stages=bytes[5];
            return true;
        }
        private static G3ReviewWitnessObservation Result(
            G3ReviewWitnessState state,int journalCount,int witnessCount)
        {return new G3ReviewWitnessObservation(state,journalCount,witnessCount);}

        internal G3ReviewWitnessObservation CompareUntrustedFiles()
        {
            // This snapshots TWO ORDINARY files separately. It is not an
            // atomic OS transaction or proof against concurrent tampering.
            // Even a matching pair ALWAYS means only a review diagnostic.
            try
            {
                bool hasJournal=File.Exists(journal.IsolatedTestFilePath);
                bool hasWitness=File.Exists(witnessPath);
                if(!hasJournal&&!hasWitness)
                    return Result(G3ReviewWitnessState.BothMissingUnsafe,0,0);
                if(!hasJournal)
                    return Result(G3ReviewWitnessState.WitnessWithoutJournal,0,0);
                if(!hasWitness)
                    return Result(G3ReviewWitnessState.JournalWithoutWitness,0,0);

                byte[] journalBytes=BoundedRead(
                    journal.IsolatedTestFilePath,
                    MaxStages*WindowsG3EphemeralReviewJournal.FrameSize);
                if(journalBytes==null)
                    return Result(G3ReviewWitnessState.JournalMalformed,0,0);
                G3ReviewObservation journalState=journal.InspectUntrusted();
                if(!journalState.SequenceStructurallyValid ||
                    journalState.RecordCount<1 ||
                    journalBytes.Length!=journalState.RecordCount*
                        WindowsG3EphemeralReviewJournal.FrameSize)
                    return Result(G3ReviewWitnessState.JournalMalformed,0,0);

                byte[] witnessBytes=BoundedRead(witnessPath,WitnessSize);
                int witnessedCount;byte[] witnessedHash;
                if(!DecodeWitness(witnessBytes,out witnessedCount,
                    out witnessedHash))
                    return Result(G3ReviewWitnessState.WitnessMalformed,
                        journalState.RecordCount,0);

                byte[] current=Digest(journalBytes,journalBytes.Length);
                if(witnessedCount!=journalState.RecordCount ||
                    !Equal32(witnessedHash,0,current))
                    return Result(G3ReviewWitnessState.HistoryMismatch,
                        journalState.RecordCount,witnessedCount);

                return Result(G3ReviewWitnessState.ConsistentButUntrusted,
                    journalState.RecordCount,witnessedCount);
            }
            catch(Exception)
            {return Result(G3ReviewWitnessState.WitnessMalformed,0,0);}
        }

        // TEST-ONLY, UNPROTECTED, non-atomic two-file snapshot.
        // No "enrollment" can be trusted if a witness is absent. The
        // same-user attacker can replace BOTH files with old valid bytes.
        // The monotonic check below is merely local structural hygiene.
        internal bool WriteUntrustedWitnessSnapshotForTest()
        {
            try
            {
                G3ReviewObservation j=journal.InspectUntrusted();
                if(!j.SequenceStructurallyValid ||
                    j.RecordCount<1||j.RecordCount>MaxStages)
                    return false;
                byte[] journalBytes=BoundedRead(
                    journal.IsolatedTestFilePath,
                    MaxStages*WindowsG3EphemeralReviewJournal.FrameSize);
                if(journalBytes==null ||
                    journalBytes.Length!=j.RecordCount*
                        WindowsG3EphemeralReviewJournal.FrameSize)
                    return false;
                byte[] journalHash=Digest(journalBytes,journalBytes.Length);

                if(File.Exists(witnessPath))
                {
                    int oldCount;byte[] oldHash;
                    byte[] earlier=BoundedRead(witnessPath,WitnessSize);
                    if(!DecodeWitness(earlier,out oldCount,out oldHash))
                        return false;
                    if(oldCount>j.RecordCount ||
                        (oldCount==j.RecordCount &&
                         !Equal32(oldHash,0,journalHash)))
                        return false;
                }

                byte[] record=new byte[WitnessSize];
                record[0]=(byte)'W';record[1]=(byte)'1';
                record[2]=(byte)'3';record[3]=(byte)'0';
                record[4]=1;record[5]=(byte)j.RecordCount;
                Buffer.BlockCopy(journalHash,0,record,6,HashSize);
                byte[] checksum=Digest(record,PreimageSize);
                Buffer.BlockCopy(checksum,0,record,PreimageSize,HashSize);
                using(var fs=new FileStream(witnessPath,FileMode.Create,
                    FileAccess.Write,FileShare.None,4096,
                    FileOptions.WriteThrough))
                {
                    fs.Write(record,0,record.Length);
                    fs.Flush(true);
                }
                return true;
            }
            catch(Exception)
            {return false;}
        }
    }
}
