#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P281_DPAPI_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Security.Cryptography;
using System.Security.Principal;

namespace Nayeon.ByokC1
{
    internal enum P281DpapiReviewStatus
    {
        Unavailable,
        Unproven,
        SyntheticUserDpapiValidated
    }

    // Ephemeral CURRENT GITHUB RUNNER USER evidence only. This does not test an
    // NT SERVICE profile, cross-principal isolation, protected vault, signed
    // installed service, restart persistence, ACLs or protected antirollback.
    internal sealed class P281DpapiReviewEvidence
    {
        internal readonly P281DpapiReviewStatus Status;
        internal readonly bool SyntheticCurrentUserRoundtrip;
        internal readonly bool WrongEntropyRejected;
        internal readonly bool TamperedCiphertextRejected;

        internal P281DpapiReviewEvidence(P281DpapiReviewStatus status,
            bool roundtrip, bool wrongEntropy, bool tampered)
        {
            Status = status;
            SyntheticCurrentUserRoundtrip = roundtrip;
            WrongEntropyRejected = wrongEntropy;
            TamperedCiphertextRejected = tampered;
        }

        // Qualified external approvals cannot be supplied by this observation.
        internal bool Gov01Approved { get { return false; } }
        internal bool Gov02Approved { get { return false; } }
        internal bool Sec03Approved { get { return false; } }
        internal bool Sec04Approved { get { return false; } }
        internal bool Rel05Approved { get { return false; } }
        internal bool Rel06Approved { get { return false; } }
        internal bool Rel07Approved { get { return false; } }
        internal bool QualifiedSecurityDecisionApproved { get { return false; } }
        internal bool ApprovedServicePrincipal { get { return false; } }
        internal bool ServicePrincipalOwnerProven { get { return false; } }
        internal bool ServiceProfileValidated { get { return false; } }
        internal bool CrossPrincipalIsolationProven { get { return false; } }
        internal bool ProtectedCredentialOwner { get { return false; } }
        internal bool ProtectedStoreImplemented { get { return false; } }
        internal bool ProtectedAntirollbackProven { get { return false; } }
        internal bool CredentialStoreAccessAllowed { get { return false; } }
        internal bool AuthenticatedIpc { get { return false; } }
        internal bool TrustedUserConsent { get { return false; } }
        internal bool SignedServiceInstalled { get { return false; } }
        internal bool NativeCredentialEffectAllowed { get { return false; } }
        internal bool RealKeyEligible { get { return false; } }
        internal bool ProductionReleaseEligible { get { return false; } }

        // Environment variables are an interlock, never host attestation or
        // service-owner identity. Identity is inspected only after this check.
        internal static bool HostedWindowsOnly()
        {
            return Environment.OSVersion.Platform == PlatformID.Win32NT &&
                String.Equals(Environment.GetEnvironmentVariable("GITHUB_ACTIONS"),
                    "true", StringComparison.Ordinal) &&
                String.Equals(Environment.GetEnvironmentVariable("RUNNER_OS"),
                    "Windows", StringComparison.Ordinal) &&
                String.Equals(Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT"),
                    "github-hosted", StringComparison.Ordinal);
        }

        private static bool SameBytes(byte[] first, byte[] second)
        {
            if (first == null || second == null || first.Length != second.Length)
                return false;
            // Fixed-length comparison without data-dependent early exit.
            int difference = 0;
            for (int i = 0; i < first.Length; i++)
                difference |= first[i] ^ second[i];
            return difference == 0;
        }

        private static void Clear(byte[] value)
        {
            if (value != null) Array.Clear(value, 0, value.Length);
        }

        internal static P281DpapiReviewEvidence ObserveSyntheticOnly()
        {
            byte[] payload = null, entropy = null, ciphertext = null;
            byte[] decrypted = null, wrongEntropy = null, wrongOutput = null;
            byte[] damaged = null, damagedOutput = null;
            try
            {
                if (!HostedWindowsOnly())
                    return Empty(P281DpapiReviewStatus.Unavailable);
                using (WindowsIdentity current = WindowsIdentity.GetCurrent())
                {
                    if (current == null || current.User == null ||
                        current.User.IsWellKnown(WellKnownSidType.LocalSystemSid))
                        return Empty(P281DpapiReviewStatus.Unproven);
                }

                payload = new byte[32];
                entropy = new byte[32];
                using (RandomNumberGenerator random = RandomNumberGenerator.Create())
                {
                    random.GetBytes(payload);
                    random.GetBytes(entropy);
                }
                ciphertext = ProtectedData.Protect(payload, entropy,
                    DataProtectionScope.CurrentUser);
                decrypted = ProtectedData.Unprotect(ciphertext, entropy,
                    DataProtectionScope.CurrentUser);
                if (ciphertext == null || ciphertext.Length == 0 ||
                    !SameBytes(payload, decrypted))
                    return Empty(P281DpapiReviewStatus.Unproven);

                wrongEntropy = (byte[])entropy.Clone();
                wrongEntropy[0] ^= 1;
                bool wrongRejected = false;
                try
                {
                    wrongOutput = ProtectedData.Unprotect(ciphertext, wrongEntropy,
                        DataProtectionScope.CurrentUser);
                }
                catch (CryptographicException) { wrongRejected = true; }
                // Wrong entropy must throw and recover no plaintext at all.
                if (!wrongRejected || wrongOutput != null)
                    return Empty(P281DpapiReviewStatus.Unproven);

                damaged = (byte[])ciphertext.Clone();
                damaged[damaged.Length / 2] ^= 1;
                bool tamperRejected = false;
                try
                {
                    damagedOutput = ProtectedData.Unprotect(damaged, entropy,
                        DataProtectionScope.CurrentUser);
                    tamperRejected = damagedOutput != null &&
                        !SameBytes(payload, damagedOutput);
                }
                catch (CryptographicException) { tamperRejected = true; }
                if (!tamperRejected)
                    return Empty(P281DpapiReviewStatus.Unproven);

                return new P281DpapiReviewEvidence(
                    P281DpapiReviewStatus.SyntheticUserDpapiValidated, true, true, true);
            }
            catch (Exception)
            {
                // Any OS/crypto/interlock failure is unproven, never a grant.
                // Exception text may contain account details; do not emit it.
                return Empty(P281DpapiReviewStatus.Unproven);
            }
            finally
            {
                Clear(payload);
                Clear(entropy);
                Clear(ciphertext);
                Clear(decrypted);
                Clear(wrongEntropy);
                Clear(wrongOutput);
                Clear(damaged);
                Clear(damagedOutput);
            }
        }

        private static P281DpapiReviewEvidence Empty(P281DpapiReviewStatus status)
        {
            return new P281DpapiReviewEvidence(status, false, false, false);
        }
    }
}
