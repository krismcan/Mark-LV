// P111: nondeployable candidate credential-effect isolation fence.
// Do not import, call or link legacy PendingServiceState/WinCred into a
// read-only candidate assembly just to establish that they are disabled.
// The original P49 guards remain frozen and are checked independently in
// their own original-source regression suite.
namespace Nayeon.ByokC1
{
    internal static class CandidateCredentialEffectHold
    {
        // Permanent candidate holds, not configuration flags, UI claims or
        // a production authorization switch. There is NO unarm operation.
        internal static bool LegacyEffectEntryDisabled() { return true; }
        internal static bool NativeMutationAdmissionPending() { return true; }
    }
}
