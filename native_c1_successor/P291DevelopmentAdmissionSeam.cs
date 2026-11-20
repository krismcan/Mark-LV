#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P291_BOUNDARY_EXPERIMENT_ONLY || !C1_P265_DEVELOPMENT_ONLY || !C1_P267_DEVELOPMENT_ONLY || !C1_P268_DEVELOPMENT_ONLY || !C1_P269_DEVELOPMENT_ONLY
#error P291_TEST_ONLY_DEBUG_ISOLATED_OPT_IN_REQUIRED
#endif
using Nayeon.ByokC1;
using Nayeon.ByokC1.P269Development;

namespace Nayeon.ByokC1.P291Development
{
    internal enum PeerAdmission { Denied }

    // NONDEPLOYABLE refusal experiment. No live token/receipt is an issuer.
    // The companion test file supplies ONLY private fixture operations.
    internal sealed partial class P291DevelopmentAdmissionSeam
    {
        private readonly ComposedDevelopmentService host;
        private P291DevelopmentAdmissionSeam(LedgerOperation operation)
        { host = ComposedDevelopmentService.TestOnlyCreate(operation, true); }

        // No inspection, callbacks, host calls, caching, preparation or effect.
        // Even a borrowed genuine development ticket is merely peer data here.
        internal PeerAdmission RefusePeer(object observation, object request, object borrowedTicket)
        { return PeerAdmission.Denied; }
    }
}
