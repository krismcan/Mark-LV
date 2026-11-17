#if !C1_REVIEW_ISOLATED_ASSEMBLY
#error P261_REVIEW_ONLY_NONDEPLOYABLE
#endif
using System;
using System.Runtime.InteropServices;
using Nayeon.ByokC1;

internal static class ScmReadOnlyTests
{
    private static void Need(bool condition)
    {
        if (!condition) throw new InvalidOperationException("P261_ASSERTION_FAILED");
    }

    private static void Denied(P261ScmEvidence evidence)
    {
        Need(!evidence.QualifiedDecisionApproved && !evidence.ApprovedServiceOwner &&
            !evidence.EffectAllowed && !evidence.RealKeyEligible &&
            !evidence.CredentialAuthority);
    }

    private static void ParserTests()
    {
        int header = Marshal.SizeOf(typeof(P261ScmReadOnlyAdmission.QueryServiceConfig));
        Need(header == (IntPtr.Size == 8 ? 64 : 36));
        const int size = 512;
        IntPtr buffer = Marshal.AllocHGlobal(size);
        try
        {
            bool matches;
            Need(!P261ScmReadOnlyAdmission.TryReadAccountMatch(IntPtr.Zero, size, out matches));
            Need(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, header - 1, out matches));
            Need(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, 8193, out matches));
            var config = new P261ScmReadOnlyAdmission.QueryServiceConfig();
            foreach (string account in new string[] {
                "NT SERVICE\\" + ServiceGate.ServiceName,
                "nt service\\" + ServiceGate.ServiceName.ToLowerInvariant(),
                "NT SERVICE\\NayeonByokCustody", "LocalSystem", "spoof", "" })
            {
                config.ServiceStartName = IntPtr.Add(buffer, header);
                Marshal.StructureToPtr(config, buffer, false);
                for (int index = 0; index < account.Length; index++)
                    Marshal.WriteInt16(buffer, header + index * 2, (short)account[index]);
                Marshal.WriteInt16(buffer, header + account.Length * 2, 0);
                bool valid = P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, size, out matches);
                Need(valid == (account.Length != 0));
                bool expected = account.Equals("NT SERVICE\\" + ServiceGate.ServiceName,
                    StringComparison.OrdinalIgnoreCase);
                Need(matches == expected);
                Need(P261ScmReadOnlyAdmission.ClassifyConfiguration(matches, 3) ==
                    (expected ? P261ScmStatus.ConfigObserved : P261ScmStatus.Mismatch));
            }
            foreach (IntPtr pointer in new IntPtr[] { IntPtr.Zero, buffer,
                IntPtr.Add(buffer, -2), IntPtr.Add(buffer, size),
                IntPtr.Add(buffer, header + 1), IntPtr.Add(buffer, size - 1) })
            {
                config.ServiceStartName = pointer;
                Marshal.StructureToPtr(config, buffer, false);
                Need(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, size, out matches));
            }
            config.ServiceStartName = IntPtr.Add(buffer, header);
            Marshal.StructureToPtr(config, buffer, false);
            for (int offset = header; offset < size; offset += 2)
                Marshal.WriteInt16(buffer, offset, 65);
            Need(!P261ScmReadOnlyAdmission.TryReadAccountMatch(buffer, size, out matches));
            foreach (uint sidType in new uint[] { 0, 1, 2, 3, UInt32.MaxValue })
            {
                P261ScmStatus status = P261ScmReadOnlyAdmission.ClassifyConfiguration(true, sidType);
                Need(status == (sidType == 3 ? P261ScmStatus.ConfigObserved :
                    (sidType == 0 || sidType == 1 ? P261ScmStatus.Mismatch :
                        P261ScmStatus.MalformedBuffer)));
                Denied(new P261ScmEvidence(status, true, true, true, sidType));
            }
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }

    public static int Main()
    {
        try
        {
            ParserTests();
            Console.WriteLine("P261_PARSER_NEGATIVES=PASS");
            P261ScmEvidence actual = P261ScmReadOnlyAdmission.Observe();
            Denied(actual);
            Console.WriteLine("P261_POINTER_BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P261_SCM_STATUS=" + actual.Status);
            Console.WriteLine("P261_SERVICE_OPENED=" + actual.ServiceOpened);
            Console.WriteLine("P261_ACCOUNT_QUERIED=" + actual.AccountQueried);
            Console.WriteLine("P261_ACCOUNT_MATCH=" + actual.VirtualAccountMatchesServiceName);
            Console.WriteLine("P261_SERVICE_SID_TYPE=" + (actual.ServiceSidType.HasValue ?
                actual.ServiceSidType.Value.ToString(System.Globalization.CultureInfo.InvariantCulture) :
                "Unverified"));
            bool allMissing = actual.Status == P261ScmStatus.Missing && !actual.ServiceOpened;
            foreach (string claimant in new string[] { null, "LocalSystem",
                "NT SERVICE\\NayeonByokCustody", "NT SERVICE\\" + ServiceGate.ServiceName,
                "spoof" })
            {
                foreach (bool approval in new bool[] { false, true })
                {
                    P261ScmEvidence claimed = P261ScmReadOnlyAdmission.RefuseUntrustedClaim(
                        claimant, approval);
                    Denied(claimed);
                    allMissing &= claimed.Status == P261ScmStatus.Missing && !claimed.ServiceOpened;
                }
            }
            Console.WriteLine("P261_SPOOF_CLAIMS=REJECT");
            Console.WriteLine("P261_SERVICE_STORE_AUTHORITY=REJECT");
            Console.WriteLine("P261_APPROVED_SERVICE_OWNER=False");
            Console.WriteLine("P261_EFFECT_ALLOWED=False");
            Console.WriteLine("P261_REAL_KEY_ELIGIBLE=False");
            Console.WriteLine("P261_QUALIFIED_APPROVALS=0/7");
            Console.WriteLine("P261_PRODUCTION_RELEASE=HOLD");
            if (!allMissing)
            {
                Console.WriteLine("P261_ENGINEERING=HOLD");
                return 2;
            }
            Console.WriteLine("P261_REAL_SCM_MISSING_DENIAL=PASS");
            return 0;
        }
        catch (Exception)
        {
            // No exception text, account, path, SID or system message escapes.
            Console.WriteLine("P261_ENGINEERING=FAILED");
            return 1;
        }
    }
}
