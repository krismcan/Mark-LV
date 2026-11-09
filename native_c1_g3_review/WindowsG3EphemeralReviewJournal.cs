// P128 — NONSECRET, UNPROTECTED, EPHEMERAL hosted-Windows file journal.
// Purpose: expose what process restart/crash stage recovery can and cannot
// establish. NOT G3 protected journal, antirollback, consent or WinCred.
// Both compile guards required; isolated GitHub Windows runner only.
// No arbitrary paths: name restricted to generated 32-char lowercase hex.
#if !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_SYNTHETIC_TEST
#error P128 ephemeral journal must never compile in ordinary product/service
#endif
using System;
using System.IO;
using System.Security.Cryptography;

namespace Nayeon.ByokC1
{
    internal enum G3ReviewStage : byte
    {
        Intent=1,
        FakeAttemptStarted=2,
        TerminalDiagnostic=3
    }

    internal enum G3ReviewRecovery
    {
        MissingOrEmptyUnsafe,
        IntentOnlyRecoveryRequired,
        PossiblyAttemptedRecoveryRequired,
        TerminalDiagnosticOnly,
        CorruptOrUntrusted
    }

    internal sealed class G3ReviewObservation
    {
        internal readonly G3ReviewRecovery Recovery;
        internal readonly int RecordCount;
        internal readonly bool SequenceStructurallyValid;

        internal G3ReviewObservation(G3ReviewRecovery recovery,
            int count,bool valid)
        {
            Recovery=recovery;
            RecordCount=count;
            SequenceStructurallyValid=valid;
        }
        internal bool SignedServiceAuthenticated {get{return false;}}
        internal bool ProtectedJournalVerified {get{return false;}}
        internal bool IndependentlyAnchoredHistoryVerified {get{return false;}}
        internal bool AntiRollbackVerified {get{return false;}}
        internal bool DurableOneUseConsentVerified {get{return false;}}
        internal bool NativeWinCredEffectAllowed {get{return false;}}
        internal bool ProductionAdmissionAllowed {get{return false;}}
        public override string ToString()
        {
            return "<P128 ephemeral unprotected journal; no trusted recovery or WinCred>";
        }
    }

    internal sealed class WindowsG3EphemeralReviewJournal
    {
        private const string Prefix="nayeon-c1-p128-";
        private const int HeaderSize=10;
        internal const int FrameSize=42;
        private const int DigestSize=32;
        private const int MaxRecords=3;
        private readonly string path;

        internal WindowsG3EphemeralReviewJournal(string isolatedName)
        {
            if(isolatedName==null||isolatedName.Length!=32)
                throw new ArgumentException("P128 requires random test ID");
            for(int i=0;i<isolatedName.Length;i++)
            {
                char c=isolatedName[i];
                if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))
                    throw new ArgumentException("Noncanonical P128 test ID");
            }
            // Only the OS TEMP directory in a disposable Windows runner.
            // This DACL is *not* protected service custody. Any same-user
            // process can alter, delete, copy or roll back the records.
            path=Path.Combine(Path.GetTempPath(),
                Prefix+isolatedName+".review");
        }

        internal string IsolatedTestFilePath {get{return path;}}

        private static G3ReviewObservation Unsafe()
        {
            return new G3ReviewObservation(
                G3ReviewRecovery.CorruptOrUntrusted,0,false);
        }

        private static byte[] ExpectedHash(byte[] prior,byte[] frame)
        {
            byte[] material=new byte[DigestSize+HeaderSize];
            Buffer.BlockCopy(prior,0,material,0,DigestSize);
            Buffer.BlockCopy(frame,0,material,DigestSize,HeaderSize);
            using(var sha=SHA256.Create())
                return sha.ComputeHash(material);
        }

        private static bool Equal32(byte[] expected,byte[] frame)
        {
            if(expected==null||expected.Length!=DigestSize)
                return false;
            int difference=0;
            for(int i=0;i<DigestSize;i++)
                difference|=expected[i]^frame[HeaderSize+i];
            return difference==0;
        }

        private static G3ReviewObservation ObserveBytes(byte[] bytes)
        {
            if(bytes==null||bytes.Length==0)
                return new G3ReviewObservation(
                    G3ReviewRecovery.MissingOrEmptyUnsafe,0,false);
            if(bytes.Length>MaxRecords*FrameSize||
                bytes.Length%FrameSize!=0)
                return Unsafe();

            int count=bytes.Length/FrameSize;
            byte[] prior=new byte[DigestSize];
            for(int index=0;index<count;index++)
            {
                byte[] frame=new byte[FrameSize];
                Buffer.BlockCopy(bytes,index*FrameSize,frame,0,FrameSize);
                if(frame[0]!='P'||frame[1]!='1'||
                    frame[2]!='2'||frame[3]!='8'||
                    frame[4]!=1||frame[5]!=(byte)(index+1)||
                    BitConverter.ToInt32(frame,6)!=index+1)
                    return Unsafe();
                byte[] digest=ExpectedHash(prior,frame);
                if(!Equal32(digest,frame))
                    return Unsafe();
                prior=digest;
            }
            G3ReviewRecovery stage=count==1?
                G3ReviewRecovery.IntentOnlyRecoveryRequired:
                count==2?
                    G3ReviewRecovery.PossiblyAttemptedRecoveryRequired:
                    G3ReviewRecovery.TerminalDiagnosticOnly;
            // A syntactically valid chain is NEVER authenticated to
            // a service, protected anchor or historical enrollment.
            return new G3ReviewObservation(stage,count,true);
        }

        private static byte[] ReadBounded(FileStream stream)
        {
            long size=stream.Length;
            if(size<0||size>MaxRecords*FrameSize)
                return null;
            stream.Position=0;
            byte[] data=new byte[(int)size];
            int offset=0;
            while(offset<data.Length)
            {
                int received=stream.Read(data,offset,data.Length-offset);
                if(received<=0)return null;
                offset+=received;
            }
            return data;
        }

        internal G3ReviewObservation InspectUntrusted()
        {
            try
            {
                if(!File.Exists(path))
                    return new G3ReviewObservation(
                        G3ReviewRecovery.MissingOrEmptyUnsafe,0,false);
                using(var fs=new FileStream(path,FileMode.Open,
                    FileAccess.Read,FileShare.ReadWrite))
                {
                    byte[] data=ReadBounded(fs);
                    return data==null?Unsafe():ObserveBytes(data);
                }
            }
            catch(Exception)
            {return Unsafe();}
        }

        // This is a synthetic staged append with FileStream.Flush(true)
        // on actual hosted Windows; it is NOT evidence of guaranteed
        // power-loss persistence, filesystem trust or antirollback.
        internal bool AppendSynthetic(G3ReviewStage next)
        {
            try
            {
                using(var fs=new FileStream(path,FileMode.OpenOrCreate,
                    FileAccess.ReadWrite,FileShare.None,4096,
                    FileOptions.WriteThrough))
                {
                    byte[] history=ReadBounded(fs);
                    var state=ObserveBytes(history);
                    int expectedNext=history==null?0:history.Length/FrameSize+1;
                    if(expectedNext<1||expectedNext>MaxRecords ||
                        (int)next!=expectedNext)
                        return false;
                    if(expectedNext==1)
                    {
                        if(history.Length!=0||
                            state.Recovery!=G3ReviewRecovery.MissingOrEmptyUnsafe)
                            return false;
                    }
                    else if(!state.SequenceStructurallyValid||
                        state.RecordCount!=expectedNext-1)
                        return false;

                    byte[] frame=new byte[FrameSize];
                    frame[0]=(byte)'P';frame[1]=(byte)'1';
                    frame[2]=(byte)'2';frame[3]=(byte)'8';
                    frame[4]=1;frame[5]=(byte)next;
                    byte[] seq=BitConverter.GetBytes(expectedNext);
                    Buffer.BlockCopy(seq,0,frame,6,4);
                    byte[] previous=new byte[DigestSize];
                    if(expectedNext>1)
                        Buffer.BlockCopy(history,
                            history.Length-DigestSize,
                            previous,0,DigestSize);
                    byte[] hash=ExpectedHash(previous,frame);
                    Buffer.BlockCopy(hash,0,frame,HeaderSize,DigestSize);
                    fs.Position=fs.Length;
                    fs.Write(frame,0,frame.Length);
                    fs.Flush(true);
                    return true;
                }
            }
            catch(Exception)
            {return false;}
        }
    }
}
