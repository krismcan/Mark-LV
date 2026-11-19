#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P281_DPAPI_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Reflection;
using Nayeon.ByokC1;

// Standalone hosted Windows reviewer; no service, IPC, file or credential API.
// A PASS proves ephemeral CURRENT GITHUB RUNNER USER DPAPI only, never an
// NT SERVICE profile, cross-principal isolation, vault or signed installed service.
internal static class SyntheticDpapiReviewTests
{
    private sealed class AssertionFault : Exception { }
    private static void Need(bool condition)
    {
        if (!condition) throw new AssertionFault();
    }

    private static void Denied(P281DpapiReviewEvidence value)
    {
        Need(!value.Gov01Approved && !value.Gov02Approved && !value.Sec03Approved &&
            !value.Sec04Approved && !value.Rel05Approved && !value.Rel06Approved &&
            !value.Rel07Approved && !value.QualifiedSecurityDecisionApproved &&
            !value.ApprovedServicePrincipal && !value.ServicePrincipalOwnerProven &&
            !value.ServiceProfileValidated && !value.CrossPrincipalIsolationProven &&
            !value.ProtectedCredentialOwner && !value.ProtectedStoreImplemented &&
            !value.ProtectedAntirollbackProven && !value.CredentialStoreAccessAllowed &&
            !value.AuthenticatedIpc && !value.TrustedUserConsent &&
            !value.SignedServiceInstalled && !value.NativeCredentialEffectAllowed &&
            !value.RealKeyEligible && !value.ProductionReleaseEligible);
        foreach (PropertyInfo property in typeof(P281DpapiReviewEvidence).GetProperties(
            BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public))
        {
            Need(property.PropertyType == typeof(bool));
            Need(property.GetSetMethod(true) == null);
            Need(!(bool)property.GetValue(value, null));
        }
    }

    private static void PureTests()
    {
        string candidate = "NT SERVICE\\" + ServiceGate.ServiceName;
        Need(candidate == "NT SERVICE\\NayeonV1ByokCustody");
        Need(candidate != "NT SERVICE\\NayeonByokCustody");
        Need(!ServiceGate.EligibleForService(null, null, false, true, true, true));
        // Non-null identical image paths also cannot admit a virtual principal
        // as LocalSystem. This pure gate call performs no OS observation.
        Need(!ServiceGate.EligibleForService("candidate.exe", "candidate.exe",
            false, true, true, true));

        Type evidence = typeof(P281DpapiReviewEvidence);
        Need(evidence.IsSealed && !evidence.IsPublic);
        FieldInfo[] fields = evidence.GetFields(BindingFlags.Instance |
            BindingFlags.NonPublic | BindingFlags.Public);
        Need(fields.Length == 4);
        foreach (FieldInfo field in fields)
            Need(field.IsInitOnly && (field.FieldType == typeof(bool) ||
                field.FieldType == typeof(P281DpapiReviewStatus)));
        Need(evidence.GetProperties(BindingFlags.Instance | BindingFlags.NonPublic |
            BindingFlags.Public).Length == 22);
        // Every status and all synthetic proof combinations retain zero authority.
        foreach (P281DpapiReviewStatus status in Enum.GetValues(typeof(P281DpapiReviewStatus)))
            for (int bits = 0; bits < 8; bits++)
                Denied(new P281DpapiReviewEvidence(status, (bits & 1) != 0,
                    (bits & 2) != 0, (bits & 4) != 0));
    }

    private static int Main()
    {
        try
        {
            if (!P281DpapiReviewEvidence.HostedWindowsOnly()) return 2;
            PureTests();
            P281DpapiReviewEvidence observed =
                P281DpapiReviewEvidence.ObserveSyntheticOnly();
            Denied(observed);
            if (observed.Status != P281DpapiReviewStatus.SyntheticUserDpapiValidated ||
                !observed.SyntheticCurrentUserRoundtrip || !observed.WrongEntropyRejected ||
                !observed.TamperedCiphertextRejected)
                return 2;

            Console.WriteLine("P281_SYNTHETIC_DPAPI=PASS");
            Console.WriteLine("P281_SCOPE=CurrentUser");
            Console.WriteLine("P281_VIRTUAL_NAME=UNAPPROVED_CANDIDATE");
            Console.WriteLine("P281_LOCAL_SYSTEM_CONFLICT=OPEN");
            Console.WriteLine("P281_SERVICE_PROFILE=UNTESTED");
            Console.WriteLine("P281_PROTECTED_STORE=NOT_IMPLEMENTED");
            Console.WriteLine("P281_QUALIFIED_APPROVALS=0/7");
            Console.WriteLine("P281_REAL_KEYS=NO_GO");
            Console.WriteLine("P281_PRODUCTION=HOLD");
            Console.WriteLine(IntPtr.Size == 8 ? "P281_NATIVE_BITS=64" : "P281_NATIVE_BITS=32");
            return 0;
        }
        catch (Exception)
        {
            // Fixed silent HOLD: no exception, SID, account or payload output.
            return 2;
        }
    }
}
