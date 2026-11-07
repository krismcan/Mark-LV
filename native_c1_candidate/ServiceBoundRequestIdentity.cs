// P102: review-only immutable operation identity, never an approval ticket.
// No secret, API key, caller-authority, IPC token or WinCred target.
// Digests, session IDs and expirations are caller claims, NOT authenticated.
// A real privileged consent issuer and trusted IPC are still absent (G1 HIGH).
using System;

namespace Nayeon.ByokC1
{
    internal sealed class ServiceBoundRequestIdentity
    {
        internal readonly LedgerOperation Operation;
        internal readonly string SessionId;
        internal readonly string RequestId;
        internal readonly string CandidateSha256;
        internal readonly long ExpiresUtcTicks;
        internal readonly bool DestructiveAcknowledgement;

        private static bool LowerHex(string s, int count)
        {
            if (s == null || s.Length != count) return false;
            for (int i = 0; i < s.Length; i++)
            {
                char ch = s[i];
                if (!((ch >= '0' && ch <= '9') ||
                    (ch >= 'a' && ch <= 'f'))) return false;
            }
            return true;
        }

        internal ServiceBoundRequestIdentity(
            LedgerOperation operation, string sessionId, string requestId,
            string candidateSha256, long expiresUtcTicks,
            bool destructiveAcknowledgement)
        {
            bool isDelete = operation == LedgerOperation.Delete;
            bool isWrite = operation == LedgerOperation.Save ||
                operation == LedgerOperation.Replace;
            if ((!isDelete && !isWrite) ||
                !LowerHex(sessionId, 32) || !LowerHex(requestId, 32) ||
                (isDelete && (candidateSha256 != null ||
                    !destructiveAcknowledgement)) ||
                (isWrite && (!LowerHex(candidateSha256, 64) ||
                    destructiveAcknowledgement)) ||
                expiresUtcTicks <= 0 ||
                expiresUtcTicks > DateTime.MaxValue.Ticks)
                throw new ArgumentException("Invalid untrusted request metadata");

            // Immutable by construction. These are NOT secrets or privileges.
            Operation = operation;
            SessionId = sessionId;
            RequestId = requestId;
            CandidateSha256 = candidateSha256;
            ExpiresUtcTicks = expiresUtcTicks;
            DestructiveAcknowledgement = destructiveAcknowledgement;
        }

        internal bool HasSafeClockWindow(long authoritativeUtcTicks)
        {
            // Uses the service's own UTC read, not a caller-provided clock.
            // A sane expiry window is necessary but NEVER sufficient for
            // trusted approval. No clock proves user identity or consent.
            const long MaxWindowTicks = TimeSpan.TicksPerMinute * 5;
            return authoritativeUtcTicks >= DateTime.MinValue.Ticks &&
                authoritativeUtcTicks <= DateTime.MaxValue.Ticks &&
                ExpiresUtcTicks > authoritativeUtcTicks &&
                ExpiresUtcTicks - authoritativeUtcTicks <= MaxWindowTicks;
        }

        internal string NonSecretReplayKey
        {
            get { return SessionId + ":" + RequestId; }
        }

        // Opaque to logs and user-facing status. Never print metadata digest.
        public override string ToString()
        { return "<P102 untrusted nonsecret request identity, no authority>"; }
    }
}
