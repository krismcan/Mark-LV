// Nayeon BYOK C1: service-owned append-only nonsecret journal file adapter.
// Requires protected Windows service installation. Never creates parent folders.
// NO credential values, provider calls, ACL changes, registry edits or key I/O.
// The second protected HKLM generation anchor is a SEPARATE mandatory adapter.
using System;
using System.IO;
using System.Text;

namespace Nayeon.ByokC1
{
    internal sealed class CustodyJournalFile
    {
        private const int MaxBytes=32768;
        private const string Name="pending-custody-v2.journal";
        private static readonly Encoding StrictAscii=Encoding.GetEncoding(
            "us-ascii", EncoderFallback.ExceptionFallback,
            DecoderFallback.ExceptionFallback);

        private readonly string path;
        private readonly bool testOnly;

        private CustodyJournalFile(string exactPath, bool testOnly)
        {
            path=exactPath;
            this.testOnly=testOnly;
        }

        internal static CustodyJournalFile ForInstalledService()
        {
            if (!ProtectedAcl.VerifyInstalledCustodyDirectory())
                throw new LedgerBlocked();
            return new CustodyJournalFile(Path.Combine(
                ProtectedAcl.ExpectedCustodyDirectory(),Name),false);
        }

#if BYOK_TEST
        internal static CustodyJournalFile ForSyntheticTest(string directory)
        {
            // ONLY present in test-compiled binaries, never production builds.
            if (String.IsNullOrWhiteSpace(directory) ||
                !Path.IsPathRooted(directory) ||
                !Path.GetFileName(directory).StartsWith(
                    "nayeon-c1-test-",StringComparison.Ordinal) ||
                !Directory.Exists(directory))
                throw new LedgerBlocked();
            return new CustodyJournalFile(Path.Combine(directory,Name),true);
        }
#endif

        private void Verify()
        {
            try
            {
                if (!testOnly && !ProtectedAcl.VerifyInstalledCustodyDirectory())
                    throw new LedgerBlocked();
                if (String.IsNullOrEmpty(path) || !Path.IsPathRooted(path))
                    throw new LedgerBlocked();
                DirectoryInfo parent=new DirectoryInfo(Path.GetDirectoryName(path));
                if(!parent.Exists || (parent.Attributes & FileAttributes.ReparsePoint)!=0)
                    throw new LedgerBlocked();
                FileInfo file=new FileInfo(path);
                if(file.Exists && (file.Attributes & FileAttributes.ReparsePoint)!=0)
                    throw new LedgerBlocked();
                if(!testOnly && file.Exists && !ProtectedAcl.VerifyCustodyEvidenceFile(path))
                    throw new LedgerBlocked();
            }
            catch(Exception) {throw new LedgerBlocked();}
        }

        private string ReadFromStream(FileStream stream)
        {
            if(stream.Length<1 || stream.Length>MaxBytes)
                throw new LedgerBlocked();
            stream.Position=0;
            byte[] bytes=new byte[(int)stream.Length];
            int offset=0;
            while(offset<bytes.Length)
            {
                int n=stream.Read(bytes,offset,bytes.Length-offset);
                if(n<=0)throw new LedgerBlocked();
                offset+=n;
            }
            if(stream.Length!=bytes.Length)throw new LedgerBlocked();
            string data;
            try{data=StrictAscii.GetString(bytes);}
            catch(Exception){throw new LedgerBlocked();}
            CustodyLedger.Decode(data);
            return data;
        }

        internal string ReadJournal()
        {
            Verify();
            try
            {
                using(FileStream stream=new FileStream(path, FileMode.Open,
                    FileAccess.Read,FileShare.None,4096,FileOptions.SequentialScan))
                {
                    string ledger=ReadFromStream(stream);
                    Verify();
                    return ledger;
                }
            }
            catch(FileNotFoundException)
            {
                Verify(); return null;
            }
            catch(DirectoryNotFoundException) {throw new LedgerBlocked();}
            catch(Exception) {throw new LedgerBlocked();}
        }

        internal void Append(string expected,string replacement)
        {
            // This adapter is only called under retained service-exclusive
            // tenure by a trusted controller. No auto retries after errors.
            Verify();
            if(String.IsNullOrEmpty(replacement) || replacement.Length>MaxBytes)
                throw new LedgerBlocked();
            CustodyLedger.Decode(replacement);
            bool create=expected==null;
            if(create && CustodyLedger.Decode(replacement).Length!=1)
                throw new LedgerBlocked();
            if(!create && (expected.Length>=replacement.Length ||
                !replacement.StartsWith(expected,StringComparison.Ordinal)))
                throw new LedgerBlocked();
            string suffix=create? replacement: replacement.Substring(expected.Length);
            if(suffix.Length<1 || suffix.Length>256 ||
                suffix[suffix.Length-1]!='\n')
                throw new LedgerBlocked();
            byte[] append=StrictAscii.GetBytes(suffix);
            try
            {
                if(create)
                {
                    using(FileStream stream=new FileStream(path,FileMode.CreateNew,
                        FileAccess.Write,FileShare.None,4096,FileOptions.WriteThrough))
                    {
                        Verify();
                        stream.Write(append,0,append.Length);
                        stream.Flush(true);
                    }
                }
                else
                {
                    using(FileStream stream=new FileStream(path,FileMode.Open,
                        FileAccess.ReadWrite,FileShare.None,4096,
                        FileOptions.WriteThrough))
                    {
                        Verify();
                        string old=ReadFromStream(stream);
                        if(!String.Equals(old,expected,StringComparison.Ordinal))
                            throw new LedgerBlocked();
                        stream.Seek(0,SeekOrigin.End);
                        stream.Write(append,0,append.Length);
                        stream.Flush(true);
                    }
                }
                Verify();
                if(!String.Equals(ReadJournal(),replacement,
                    StringComparison.Ordinal))
                    throw new LedgerBlocked();
            }
            catch(Exception) {throw new LedgerBlocked();}
        }
    }
}
