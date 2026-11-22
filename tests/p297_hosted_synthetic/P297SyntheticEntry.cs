#if DEBUG && C1_REVIEW_ISOLATED_ASSEMBLY && C1_P296_SOURCE_ONLY && C1_P297_HOSTED_SYNTHETIC_ONLY && !RELEASE
using System;
using System.Globalization;

// Hosted synthetic entry only. No arguments, environment, file, process or native API.
// P296's inert launch boundary and asynchronous drain helper are never invoked.
namespace P296SourceOnly
{
    internal static class P297SyntheticEntry
    {
        private static int Main()
        {
            int count=0;
            bool passed=false;
            try
            {
                count=LaunchCustodyDiagnosticTests.RunAll();
                passed=count==56;
            }
            catch (Exception)
            {
                // No partial completion count is available if RunAll throws.
                // Deliberately omit exception messages, names, paths and inner exceptions.
                count=0;
            }
            Console.WriteLine("P297 SYNTHETIC "+(passed ? "PASS" : "HOLD")+
                " COUNT="+count.ToString(CultureInfo.InvariantCulture));
            return passed ? 0 : 1;
        }
    }
}
#else
#error P297_DEBUG_ISOLATED_HOSTED_SYNTHETIC_ONLY_REQUIRED
#endif
