// P213: actual Windows WinVerifyTrust read-only image policy observation.
// Test-only. Compiled ONLY with C1_REVIEW_ISOLATED_ASSEMBLY, which is not
// a production service, signed app, installer, loaded image attestation or
// credential actor. Reuses frozen P116 native WinTrust opened-file-handle
// implementation without altering original source or performing WinCred IO.
#if C1_REVIEW_ISOLATED_ASSEMBLY
using System;
using System.IO;
using Nayeon.ByokC1;

internal static class P213NativeWintrustObservation
{
    public static int Main(string[] arguments)
    {
        if(arguments==null || arguments.Length!=1 ||
           String.IsNullOrWhiteSpace(arguments[0]) ||
           !Path.IsPathRooted(arguments[0]))
        {
            Console.WriteLine("P213_NATIVE_WINTRUST=UNAVAILABLE");
            return 2;
        }
        // Do not promote a valid signature to Nayeon publisher authority.
        // P116 uses read-only FileStream and actual WinVerifyTrust with
        // WTD_CACHE_ONLY_URL_RETRIEVAL; no unbounded network retrieval.
        OsWintrustReviewObservation result=
            WindowsWintrustFilePolicyReview.ObserveFilePolicyOnly(arguments[0]);
        if(result==null || !result.NativePolicyAttempted)
        {
            Console.WriteLine("P213_NATIVE_WINTRUST=UNAVAILABLE");
            return 2;
        }
        Console.WriteLine("P213_NATIVE_WINTRUST="+result.State.ToString());
        Console.WriteLine("P213_APPROVED_PUBLISHER=false");
        Console.WriteLine("P213_SERVICE_IMAGE_BOUND=false");
        Console.WriteLine("P213_HUMAN_CONSENT=false");
        Console.WriteLine("P213_REAL_KEY=false");
        Console.WriteLine("P213_RELEASE=false");
        return 0;
    }
}
#endif
