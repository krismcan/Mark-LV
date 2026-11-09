// P120 — ISOLATED REVIEW-ASSEMBLY ONLY synthetic operation challenge.
// This is NOT installed in a privileged service or authenticated consent UI.
// The challenge and peer evidence are NOT trusted approval credentials.
// Echo matches can only produce a non-authoritative diagnostic, never a grant.
#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P120 challenge review may not be built into an ordinary production assembly
#endif
using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace Nayeon.ByokC1
{
    internal enum ReviewOnlyChallengeVerdict
    {
        Refused,
        EchoMatchedWithoutConsentAuthority
    }

    internal sealed class ReviewOnlyOperationChallenge
    {
        private const long MaxTtlTicks = TimeSpan.TicksPerMinute;
        private readonly object gate = new object();
        private readonly byte[] nonce;
        private readonly byte[] requestDigest;
        private readonly string peerObservationClaim;
        private readonly long issuedTicks;
        private readonly long terminalDeadlineTicks;
        private readonly Func<long> syntheticHostClock;
        private bool terminal;
        private bool diagnosticEchoObserved;

        private ReviewOnlyOperationChallenge(
            byte[] freshNonce, byte[] canonicalRequestDigest,
            string untrustedPeerClaim, long issuedAt,
            long expiry, Func<long> reviewClock)
        {
            nonce = freshNonce;
            requestDigest = canonicalRequestDigest;
            peerObservationClaim = untrustedPeerClaim;
            issuedTicks = issuedAt;
            terminalDeadlineTicks = expiry;
            syntheticHostClock = reviewClock;
        }

        // These booleans are deliberately NOT derived from the echo result.
        internal bool AuthenticatedServiceListenerInstalled { get { return false; } }
        internal bool ApprovedSignedConsentBrokerVerified { get { return false; } }
        internal bool TrustedHumanInteractionVerified { get { return false; } }
        internal bool ProtectedDurableGrantIssued { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }

        internal bool Terminal
        {
            get { lock (gate) { return terminal; } }
        }
        internal bool DiagnosticEchoObserved
        {
            get { lock (gate) { return diagnosticEchoObserved; } }
        }

        private static bool LowerHex(string value, int length)
        {
            if (value == null || value.Length != length) return false;
            for (int i = 0; i < length; i++)
            {
                char c = value[i];
                if (!((c >= '0' && c <= '9') ||
                      (c >= 'a' && c <= 'f'))) return false;
            }
            return true;
        }

        // Canonical digest is a comparison aid only. P102 input is NOT an
        // OS-authenticated request. Length-prefixed binary writer eliminates
        // concatenation ambiguities in this review transcript.
        private static byte[] CanonicalDigest(
            ServiceBoundRequestIdentity identity, string untrustedPeerClaim)
        {
            using (var buffer = new MemoryStream())
            using (var writer = new BinaryWriter(buffer, Encoding.UTF8))
            {
                writer.Write((byte)2);
                writer.Write((int)identity.Operation);
                writer.Write(identity.SessionId);
                writer.Write(identity.RequestId);
                writer.Write(identity.CandidateSha256 ?? "");
                writer.Write(identity.ExpiresUtcTicks);
                writer.Write(identity.DestructiveAcknowledgement);
                writer.Write(untrustedPeerClaim);
                writer.Flush();
                using (var hash = SHA256.Create())
                    return hash.ComputeHash(buffer.ToArray());
            }
        }

        private static bool Same32Bytes(byte[] expected, byte[] received)
        {
            if (expected == null || received == null ||
                expected.Length != 32 || received.Length != 32)
                return false;
            int different = 0;
            for (int i = 0; i < expected.Length; i++)
                different |= expected[i] ^ received[i];
            return different == 0;
        }

        private static byte[] Copy(byte[] source)
        {
            if (source == null) return null;
            var copy = new byte[source.Length];
            Buffer.BlockCopy(source, 0, copy, 0, source.Length);
            return copy;
        }

        // The clock is deliberately injectable ONLY in this compile-gated
        // isolated review harness. Do NOT model it as a real service clock.
        internal static ReviewOnlyOperationChallenge TryIssue(
            ServiceBoundRequestIdentity untrustedIdentity,
            string untrustedPeerObservationHex,
            Func<long> isolatedReviewClock)
        {
            if (untrustedIdentity == null ||
                !LowerHex(untrustedPeerObservationHex, 64) ||
                isolatedReviewClock == null) return null;
            try
            {
                long now = isolatedReviewClock();
                if (!untrustedIdentity.HasSafeClockWindow(now) ||
                    now > DateTime.MaxValue.Ticks - MaxTtlTicks)
                    return null;
                long deadline = Math.Min(untrustedIdentity.ExpiresUtcTicks,
                    now + MaxTtlTicks);
                if (deadline <= now) return null;
                byte[] random = new byte[32];
                using (var rng = RandomNumberGenerator.Create())
                    rng.GetBytes(random);
                byte[] digest = CanonicalDigest(
                    untrustedIdentity, untrustedPeerObservationHex);
                return new ReviewOnlyOperationChallenge(
                    random, digest, untrustedPeerObservationHex,
                    now, deadline, isolatedReviewClock);
            }
            catch (Exception)
            { return null; }
        }

        internal byte[] GetChallengeCopy()
        {
            lock (gate) return terminal ? null : Copy(nonce);
        }

        internal byte[] GetBindingDigestCopy()
        {
            lock (gate) return terminal ? null : Copy(requestDigest);
        }

        // First attempted reply consumes the in-memory review transcript,
        // including malformed, mismatched, expired or faulted replies.
        // A matched echo is just an echo; it does NOT assert actual consent.
        internal ReviewOnlyChallengeVerdict ObserveEchoAndTerminate(
            ServiceBoundRequestIdentity candidateIdentity,
            string candidatePeerObservationHex,
            byte[] echoedChallenge)
        {
            lock (gate)
            {
                if (terminal) return ReviewOnlyChallengeVerdict.Refused;
                terminal = true;
                long observed;
                try { observed = syntheticHostClock(); }
                catch (Exception) { return ReviewOnlyChallengeVerdict.Refused; }
                if (observed < issuedTicks ||
                    observed >= terminalDeadlineTicks ||
                    !String.Equals(candidatePeerObservationHex,
                        peerObservationClaim, StringComparison.Ordinal) ||
                    candidateIdentity == null ||
                    !Same32Bytes(nonce, echoedChallenge))
                    return ReviewOnlyChallengeVerdict.Refused;
                byte[] candidate;
                try
                {
                    candidate = CanonicalDigest(
                        candidateIdentity, candidatePeerObservationHex);
                }
                catch (Exception)
                { return ReviewOnlyChallengeVerdict.Refused; }
                if (!Same32Bytes(requestDigest, candidate))
                    return ReviewOnlyChallengeVerdict.Refused;

                diagnosticEchoObserved = true;
                return ReviewOnlyChallengeVerdict.EchoMatchedWithoutConsentAuthority;
            }
        }

        internal bool RevokeBeforeEcho()
        {
            lock (gate)
            {
                if (terminal) return false;
                terminal = true;
                return true;
            }
        }

        internal bool FailClosedFault()
        {
            lock (gate)
            {
                if (terminal) return false;
                terminal = true;
                return true;
            }
        }

        public override string ToString()
        {
            return "<P120 isolated in-memory challenge; echo is not consent; no effect>";
        }
    }
}
