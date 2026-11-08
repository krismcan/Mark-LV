// P111: supply only the nonsecret status enum when the strict candidate
// source allowlist EXCLUDES old PendingCustodyTransaction.cs entirely.
// In legacy regression builds the original P49 source still owns the enum.
// This is not an independent consent issuer or authorization record.
#if C1_REVIEW_ISOLATED_ASSEMBLY
namespace Nayeon.ByokC1
{
    internal enum CustodyOutcome
    {
        Denied, RecoveryRequired, StoredUnverified, RemovedUnverified
    }
}
#endif
