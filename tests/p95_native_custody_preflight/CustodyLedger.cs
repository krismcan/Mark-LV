// Nayeon BYOK C1: native production-target nonsecret append-only custody ledger.
// Codec only. Not an install, storage authority, approval, or credential API.
// Its SHA-256 chain and separate anchor are NOT authenticated: protection must
// be established by a reviewed Windows service-owned OS trust boundary.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;

namespace Nayeon.ByokC1
{
    internal enum LedgerPhase
    {
        Initial, InFlight, CommittedUnverified, CommittedAbsent
    }

    internal enum LedgerOperation
    {
        Initial, Save, Replace, Delete
    }

    internal sealed class LedgerBlocked : Exception
    {
        internal LedgerBlocked() : base("Pending custody recovery required") {}
    }

    internal sealed class CustodyFrame
    {
        internal readonly int Sequence;
        internal readonly long Generation;
        internal readonly string Nonce;
        internal readonly LedgerOperation Operation;
        internal readonly LedgerPhase Phase;
        internal readonly string Predecessor;

        internal CustodyFrame(int sequence, long generation, string nonce,
            LedgerOperation operation, LedgerPhase phase, string predecessor)
        {
            Sequence=sequence; Generation=generation; Nonce=nonce;
            Operation=operation; Phase=phase; Predecessor=predecessor;
        }
    }

    internal static class CustodyLedger
    {
        private const int MaxRecords=128;
        private const int MaxJournal=32768;
        private const int MaxLine=256;
        private const long MaxGeneration=1000000000000L;
        private const string Domain="NAYEON-C1-CUSTODY-LEDGER-V2:";
        private static readonly string Genesis=new String('0',64);

        private static bool LowerHex(string text, int length)
        {
            if (text==null || text.Length!=length) return false;
            foreach(char ch in text)
                if (!((ch>='0'&&ch<='9')||(ch>='a'&&ch<='f'))) return false;
            return true;
        }

        private static bool Number(string input, long upper, out long n)
        {
            n=0;
            if (String.IsNullOrEmpty(input) || input.Length>16 ||
                (input.Length>1 && input[0]=='0')) return false;
            foreach(char ch in input)
                if (ch<'0' || ch>'9') return false;
            return Int64.TryParse(input, NumberStyles.None,
                CultureInfo.InvariantCulture, out n) && n>=0 && n<=upper;
        }

        private static string Hash(string input)
        {
            using (SHA256 sha=SHA256.Create())
            {
                byte[] bytes=Encoding.ASCII.GetBytes(input);
                byte[] digest=sha.ComputeHash(bytes);
                StringBuilder result=new StringBuilder(64);
                foreach(byte b in digest)
                    result.Append(b.ToString("x2", CultureInfo.InvariantCulture));
                return result.ToString();
            }
        }

        internal static string NewNonce()
        {
            byte[] bytes=new byte[16];
            using (RandomNumberGenerator rng=RandomNumberGenerator.Create())
                rng.GetBytes(bytes);
            StringBuilder result=new StringBuilder(32);
            foreach(byte b in bytes)
                result.Append(b.ToString("x2",CultureInfo.InvariantCulture));
            return result.ToString();
        }

        private static string Token(LedgerPhase phase)
        {
            switch(phase)
            {
                case LedgerPhase.Initial: return "INITIAL";
                case LedgerPhase.InFlight: return "IN_FLIGHT";
                case LedgerPhase.CommittedUnverified: return "COMMITTED_UNVERIFIED";
                case LedgerPhase.CommittedAbsent: return "COMMITTED_ABSENT";
                default: throw new LedgerBlocked();
            }
        }

        private static string Token(LedgerOperation op)
        {
            switch(op)
            {
                case LedgerOperation.Initial: return "INITIAL";
                case LedgerOperation.Save: return "SAVE";
                case LedgerOperation.Replace: return "REPLACE";
                case LedgerOperation.Delete: return "DELETE";
                default: throw new LedgerBlocked();
            }
        }

        private static LedgerOperation Operation(string raw)
        {
            if(raw=="INITIAL") return LedgerOperation.Initial;
            if(raw=="SAVE") return LedgerOperation.Save;
            if(raw=="REPLACE") return LedgerOperation.Replace;
            if(raw=="DELETE") return LedgerOperation.Delete;
            throw new LedgerBlocked();
        }

        private static LedgerPhase Phase(string raw)
        {
            if(raw=="INITIAL") return LedgerPhase.Initial;
            if(raw=="IN_FLIGHT") return LedgerPhase.InFlight;
            if(raw=="COMMITTED_UNVERIFIED") return LedgerPhase.CommittedUnverified;
            if(raw=="COMMITTED_ABSENT") return LedgerPhase.CommittedAbsent;
            throw new LedgerBlocked();
        }

        private static string FrameText(CustodyFrame frame)
        {
            if (frame==null || frame.Sequence<1 || frame.Sequence>MaxRecords ||
                frame.Generation<0 || frame.Generation>MaxGeneration ||
                !LowerHex(frame.Nonce,32) || !LowerHex(frame.Predecessor,64))
                throw new LedgerBlocked();
            return "J2|"+frame.Sequence.ToString(CultureInfo.InvariantCulture)+"|"+
                frame.Generation.ToString(CultureInfo.InvariantCulture)+"|"+
                frame.Nonce+"|"+Token(frame.Operation)+"|"+Token(frame.Phase)+"|"+
                frame.Predecessor+"\n";
        }

        private static CustodyFrame ParseLine(string line)
        {
            if (String.IsNullOrEmpty(line) || line.Length>MaxLine ||
                line[line.Length-1]!='\n')
                throw new LedgerBlocked();
            foreach(char ch in line)
                if (ch>126 || ch<32 && ch!='\n') throw new LedgerBlocked();
            string[] chunks=line.Substring(0,line.Length-1).Split('|');
            if (chunks.Length!=7 || chunks[0]!="J2")
                throw new LedgerBlocked();
            long sequence, generation;
            if(!Number(chunks[1],MaxRecords,out sequence) || sequence<1 ||
                !Number(chunks[2],MaxGeneration,out generation) ||
                !LowerHex(chunks[3],32) || !LowerHex(chunks[6],64))
                throw new LedgerBlocked();
            CustodyFrame frame=new CustodyFrame((int)sequence,generation,chunks[3],
                Operation(chunks[4]),Phase(chunks[5]),chunks[6]);
            if(FrameText(frame)!=line) throw new LedgerBlocked();
            return frame;
        }

        private static void Transition(CustodyFrame before, CustodyFrame after,
            HashSet<string> seen)
        {
            if (after.Sequence != before.Sequence+1 ||
                after.Predecessor!=Hash(Domain+FrameText(before)) ||
                (seen.Contains(after.Nonce) && after.Nonce!=before.Nonce))
                throw new LedgerBlocked();
            if(after.Phase==LedgerPhase.InFlight)
            {
                if (before.Phase!=LedgerPhase.Initial &&
                    before.Phase!=LedgerPhase.CommittedUnverified &&
                    before.Phase!=LedgerPhase.CommittedAbsent)
                    throw new LedgerBlocked();
                if(after.Generation != before.Generation+1 ||
                    after.Nonce==before.Nonce || seen.Contains(after.Nonce))
                    throw new LedgerBlocked();
                bool absent=(before.Phase==LedgerPhase.Initial ||
                             before.Phase==LedgerPhase.CommittedAbsent);
                if (absent && after.Operation!=LedgerOperation.Save ||
                    !absent && after.Operation!=LedgerOperation.Replace &&
                               after.Operation!=LedgerOperation.Delete)
                    throw new LedgerBlocked();
                return;
            }
            if(after.Phase==LedgerPhase.CommittedUnverified ||
               after.Phase==LedgerPhase.CommittedAbsent)
            {
                if(before.Phase!=LedgerPhase.InFlight ||
                   after.Generation!=before.Generation ||
                   after.Nonce!=before.Nonce ||
                   after.Operation!=before.Operation)
                    throw new LedgerBlocked();
                bool deletion=after.Operation==LedgerOperation.Delete;
                if (deletion!=(after.Phase==LedgerPhase.CommittedAbsent))
                    throw new LedgerBlocked();
                return;
            }
            throw new LedgerBlocked();
        }

        internal static CustodyFrame[] Decode(string ledger)
        {
            if(String.IsNullOrEmpty(ledger) || ledger.Length>MaxJournal ||
                ledger[ledger.Length-1]!='\n')
                throw new LedgerBlocked();
            string[] lines=ledger.Split('\n');
            if(lines.Length<2 || lines.Length>MaxRecords+1 ||
                lines[lines.Length-1]!="")
                throw new LedgerBlocked();
            List<CustodyFrame> result=new List<CustodyFrame>();
            HashSet<string> used=new HashSet<string>(StringComparer.Ordinal);
            for(int i=0;i<lines.Length-1;i++)
            {
                CustodyFrame current=ParseLine(lines[i]+"\n");
                if(i==0)
                {
                    if(current.Sequence!=1 || current.Generation!=0 ||
                       current.Phase!=LedgerPhase.Initial ||
                       current.Operation!=LedgerOperation.Initial ||
                       current.Predecessor!=Genesis)
                        throw new LedgerBlocked();
                }
                else Transition(result[result.Count-1],current,used);
                used.Add(current.Nonce);
                result.Add(current);
            }
            return result.ToArray();
        }

        internal static string CreateInitial(string nonce)
        {
            return FrameText(new CustodyFrame(1,0,nonce,LedgerOperation.Initial,
                LedgerPhase.Initial,Genesis));
        }

        internal static string AppendIntent(string existing,
            LedgerOperation operation, string nonce)
        {
            CustodyFrame[] records=Decode(existing);
            CustodyFrame last=records[records.Length-1];
            if(records.Length+2>MaxRecords || last.Generation>=MaxGeneration)
                throw new LedgerBlocked(); // reserve terminal record
            CustodyFrame next=new CustodyFrame(last.Sequence+1,
                last.Generation+1,nonce,operation,LedgerPhase.InFlight,
                Hash(Domain+FrameText(last)));
            Transition(last,next,new HashSet<string>(Seen(records),StringComparer.Ordinal));
            string updated=existing+FrameText(next);
            Decode(updated);
            return updated;
        }

        private static IEnumerable<string> Seen(CustodyFrame[] frames)
        {
            foreach(CustodyFrame frame in frames) yield return frame.Nonce;
        }

        internal static string AppendTerminal(string existing)
        {
            CustodyFrame[] records=Decode(existing);
            CustodyFrame last=records[records.Length-1];
            if(records.Length>=MaxRecords || last.Phase!=LedgerPhase.InFlight)
                throw new LedgerBlocked();
            LedgerPhase terminal=last.Operation==LedgerOperation.Delete?
                LedgerPhase.CommittedAbsent:LedgerPhase.CommittedUnverified;
            CustodyFrame next=new CustodyFrame(last.Sequence+1,
                last.Generation,last.Nonce,last.Operation,terminal,
                Hash(Domain+FrameText(last)));
            string updated=existing+FrameText(next);
            Decode(updated);
            return updated;
        }

        internal static string Anchor(string ledger)
        {
            CustodyFrame[] records=Decode(ledger);
            CustodyFrame last=records[records.Length-1];
            return "A2|"+last.Sequence.ToString(CultureInfo.InvariantCulture)+
                "|"+last.Generation.ToString(CultureInfo.InvariantCulture)+
                "|"+Hash("NAYEON-C1-ANCHOR-V2:"+ledger);
        }

        internal static LedgerPhase Verify(string ledger, string anchor)
        {
            CustodyFrame[] records=Decode(ledger);
            string expected=Anchor(ledger);
            if (anchor==null || !String.Equals(anchor,expected,
                StringComparison.Ordinal))
                throw new LedgerBlocked();
            return records[records.Length-1].Phase;
        }

        internal static LedgerOperation LastOperation(string ledger)
        {
            CustodyFrame[] records=Decode(ledger);
            return records[records.Length-1].Operation;
        }
    }
}
