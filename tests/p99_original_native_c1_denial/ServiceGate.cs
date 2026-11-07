// P49 Nayeon v1 BYOK C1 — fail-closed, production-target Windows service chassis.
// NO native key operations, no IPC listener, no journal writes and no installation.
// A service with privileged credentials MUST NOT expose the existing Python host
// until privileged storage, Win32 ACLs and elevated UI provenance pass review.
using System;
using System.IO;
using System.Reflection;
using System.Security.Principal;

namespace Nayeon.ByokC1
{
    internal static class ServiceGate
    {
        internal const string ServiceName = "NayeonV1ByokCustody";
        internal const string ExecutableName = "Nayeon.ByokC1.CustodyService.exe";
        internal const string Unavailable = "UNAVAILABLE";

        internal static string ExpectedImage()
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
                "Nayeon", "Custody", ExecutableName);
        }

        // This only validates the basic shell; approved OS-owned install
        // provenance additionally needs exact owner, ACL, ancestor and code
        // identity. Keep that unresolved prerequisite set to FALSE.
        internal static bool EligibleForService(
            string imagePath, string expectedImagePath,
            bool accountIsLocalSystem,
            bool trustedInstallDescriptorsVerified,
            bool binaryIntegrityVerified,
            bool approvedReleaseManifestVerified)
        {
            if (!accountIsLocalSystem ||
                !trustedInstallDescriptorsVerified ||
                !binaryIntegrityVerified ||
                !approvedReleaseManifestVerified)
                return false;
            if (String.IsNullOrWhiteSpace(imagePath) ||
                String.IsNullOrWhiteSpace(expectedImagePath))
                return false;
            try
            {
                return String.Equals(
                    Path.GetFullPath(imagePath),
                    Path.GetFullPath(expectedImagePath),
                    StringComparison.OrdinalIgnoreCase);
            }
            catch (Exception)
            {
                return false;
            }
        }

        internal static bool LiveEligible()
        {
            try
            {
                using(WindowsIdentity identity=WindowsIdentity.GetCurrent())
                {
                    bool system=identity!=null && identity.User!=null &&
                        identity.User.IsWellKnown(
                            WellKnownSidType.LocalSystemSid);
                    string path=Assembly.GetExecutingAssembly().Location;
                    return EligibleForService(path,ExpectedImage(),system,
                        ProtectedAcl.VerifyInstalledImage(path,ExpectedImage()),
                        false, // immutable binary release proof PENDING
                        false  // independently reviewed release PENDING
                    );
                }
            }
            catch (Exception)
            {
                return false;
            }
        }

        internal static string HandleUntrustedRequest(string request)
        {
            // All requests are DENIED until an independently reviewed IPC
            // protocol and peer-proof are implemented. No secret reflection.
            return Unavailable;
        }
    }
}
