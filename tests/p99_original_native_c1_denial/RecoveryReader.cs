// Nayeon BYOK C1 P49 — strict read-only recovery metadata interpreter.
// It is NOT an authority or persistent store. Both journal/anchor must be
// independently protected by the reviewed LocalSystem service installation.
// The SHA256 is a structural checksum, NOT authentication or anti-rollback.
using System;
using System.Text;
using System.Text.RegularExpressions;
using System.Security.Cryptography;
using System.Globalization;

namespace Nayeon.ByokC1
{
    internal enum RecoveryDisposition
    {
        Unavailable, Uninitialized, Absent, StoredUnverified, RecoveryRequired
    }

    internal static class RecoveryReader
    {
        private static readonly Regex Nonce = new Regex(
            "^[0-9a-f]{32}$", RegexOptions.CultureInvariant);
        private static readonly Regex Digest = new Regex(
            "^[0-9a-f]{64}$", RegexOptions.CultureInvariant);
        private const int MaxFrameLength = 512;

        private static bool ParseGeneration(string text, out long generation)
        {
            generation = 0;
            if (String.IsNullOrEmpty(text) || text.Length > 16 ||
                (text.Length > 1 && text[0] == '0'))
                return false;
            for (int i=0; i<text.Length; i++)
                if (text[i] < '0' || text[i] > '9') return false;
            return Int64.TryParse(text, NumberStyles.None,
                CultureInfo.InvariantCulture, out generation) &&
                generation >= 0 && generation <= 1000000000000L;
        }

        private static string Hash(string text)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] input = Encoding.ASCII.GetBytes(text);
                byte[] hash = sha.ComputeHash(input);
                StringBuilder builder = new StringBuilder(hash.Length * 2);
                foreach (byte b in hash) builder.Append(b.ToString("x2"));
                return builder.ToString();
            }
        }

        internal static string StructuralAnchorForSyntheticTest(string frame)
        {
            // Bounded deterministic test fixture only, NOT an authority.
            if (String.IsNullOrEmpty(frame)) throw new ArgumentException("frame");
            string[] pieces = frame.Split('|');
            if (pieces.Length != 5) throw new ArgumentException("frame");
            return "A1|" + pieces[1] + "|" + Hash(frame);
        }

        internal static RecoveryDisposition Assess(
            string journal, string anchor, bool pendingPresent,
            bool trustedOsNamespaceVerified)
        {
            if (!trustedOsNamespaceVerified)
                return RecoveryDisposition.Unavailable;
            if (journal == null && anchor == null)
                return pendingPresent ? RecoveryDisposition.RecoveryRequired :
                    RecoveryDisposition.Uninitialized;
            if (journal == null || anchor == null ||
                journal.Length == 0 || anchor.Length == 0 ||
                journal.Length > MaxFrameLength || anchor.Length > 128)
                return RecoveryDisposition.RecoveryRequired;
            // Strict canonical ASCII, no whitespace, nulls, Unicode or newlines.
            foreach (char c in journal + anchor)
                if (c < 33 || c > 126)
                    return RecoveryDisposition.RecoveryRequired;
            string[] fields = journal.Split('|');
            string[] pin = anchor.Split('|');
            long generation, anchoredGeneration;
            if (fields.Length != 5 || pin.Length != 3 ||
                fields[0] != "J1" || pin[0] != "A1" ||
                !ParseGeneration(fields[1], out generation) ||
                !ParseGeneration(pin[1], out anchoredGeneration) ||
                generation != anchoredGeneration ||
                !Nonce.IsMatch(fields[2]) ||
                !Digest.IsMatch(pin[2]) ||
                !String.Equals(Hash(journal), pin[2], StringComparison.Ordinal))
                return RecoveryDisposition.RecoveryRequired;
            if (fields[3] != "SAVE" && fields[3] != "REPLACE" &&
                fields[3] != "DELETE" && fields[3] != "INITIAL")
                return RecoveryDisposition.RecoveryRequired;
            if (fields[4] == "IN_FLIGHT" || fields[4] == "BLOCKED")
                return RecoveryDisposition.RecoveryRequired;
            if (fields[4] == "INITIAL" && fields[3] == "INITIAL")
                return pendingPresent ? RecoveryDisposition.RecoveryRequired :
                    RecoveryDisposition.Uninitialized;
            if (fields[4] == "COMMITTED_UNVERIFIED" &&
                (fields[3] == "SAVE" || fields[3] == "REPLACE"))
                return pendingPresent ? RecoveryDisposition.StoredUnverified :
                    RecoveryDisposition.RecoveryRequired;
            if (fields[4] == "COMMITTED_ABSENT" && fields[3] == "DELETE")
                return pendingPresent ? RecoveryDisposition.RecoveryRequired :
                    RecoveryDisposition.Absent;
            return RecoveryDisposition.RecoveryRequired;
        }
    }
}
