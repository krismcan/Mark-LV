#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P287_SERVICE_CLIENT_REVIEW_ONLY
#error P287_FOCUSED_TEST_ONLY_DEBUG_ISOLATED_AND_OPT_IN_REQUIRED
#endif
using System;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1.P287Review;
using Fixture = Nayeon.ByokC1.P287Review.ServiceClientPipeBoundary.SyntheticFixture;

internal static class ServiceClientBoundaryTests
{
    private static int assertions, cases;
    private static void Check(bool value)
    {
        Interlocked.Increment(ref assertions);
        if (!value) throw new InvalidOperationException("P287_ASSERT");
    }
    private static void NoAuthority(BoundaryEvidence evidence)
    {
        Check(!evidence.CredentialAllowed && !evidence.StoreAllowed &&
            !evidence.ProtectedStoreAllowed && !evidence.ProductionEligible);
    }
    private static void Refused(Action action)
    {
        bool denied = false;
        try { action(); } catch (InvalidOperationException) { denied = true; }
        Check(denied);
    }
    private static string Hash(byte[] bytes)
    {
        using (SHA256 sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "");
    }
    private static void SourceContracts()
    {
        const string path = "native_c1_successor/P286SafeDevelopmentPipeAdapter.cs";
        byte[] frozen = File.ReadAllBytes(path);
        const string pin = "15D05B5F577DFD25BDD0551CE37480D10C62FFC7BC034784E781E242B72A0AF9";
        Check(Hash(frozen) == pin);
        frozen[0] ^= 1; Check(Hash(frozen) != pin);
        string text = File.ReadAllText(path);
        Check(text.Contains("using (WaitHandle completedHandle = result.AsyncWaitHandle)"));
        Check(text.Contains("pipe.BeginWaitForConnection(connect.Callback, null)"));
        Check(text.Contains("pipe.BeginRead(buffer, offset, buffer.Length - offset, read.Callback, null)"));
        Check(text.Contains("pipe.BeginWrite(denial, 0, denial.Length, write.Callback, null)"));
        // Original P286 source and tests compiled verbatim. Managed completion fakes
        // cover connect/read/write, cancellation, late callback and stalled End*.
        Check(AsyncPipeLifetimeTests.Main() == 0);
        string boundary = File.ReadAllText("native_c1_successor/P287ServiceClientPipeBoundary.cs");
        foreach (string forbidden in new[] { "new NamedPipeServerStream", "new NamedPipeClientStream",
            "DllImport", "NTAccount", "GetEnvironmentVariable", "CredentialManager", ".Impersonate(", "AdjustTokenPrivileges" })
            Check(!boundary.Contains(forbidden));
        cases++;
    }
    private static void LiveIsAlwaysDenied()
    {
        BoundaryEvidence evidence = ServiceClientPipeBoundary.ObserveLiveAdmission();
        Check(evidence.Status == BoundaryStatus.MissingTrustedLiveProvenance); NoAuthority(evidence);
        Refused(ServiceClientPipeBoundary.DemandBeforeRealPipeCreation);
        // Even a successful synthetic model cannot change live admission.
        Fixture model = Fixture.Create(); model.BuildTestOnlySecurity();
        Refused(ServiceClientPipeBoundary.DemandBeforeRealPipeCreation);
        NoAuthority(new BoundaryEvidence(BoundaryStatus.SyntheticAclModelOnly));
        cases++;
    }
    private static void RolesAndContinuity()
    {
        Fixture good = Fixture.Create();
        Check(good.Observe().Status == BoundaryStatus.SyntheticAclModelOnly); NoAuthority(good.Observe());
        Check(!good.Service.User.Equals(good.Client.User));
        Check(good.Service.User.Equals(good.Service.VerifiedServiceSid));
        Check(good.Service.ProcessId == good.Service.ScmProcessId && good.Service.Session == 0 && good.Client.Session != 0);
        PipeSecurity model = good.BuildTestOnlySecurity(); Check(good.MatchesExactAcl(model));
        foreach (FieldInfo field in typeof(PrincipalObservation).GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
            Check(field.IsInitOnly);
        byte[] sidBytes = new byte[good.Service.User.BinaryLength]; good.Service.User.GetBinaryForm(sidBytes, 0);
        Check(new SecurityIdentifier(sidBytes, 0).Equals(good.Service.User));
        Check(typeof(Fixture).GetMethod("BuildTestOnlySecurity", BindingFlags.Instance | BindingFlags.NonPublic).GetParameters().Length == 0);
        cases++;
        foreach (FixtureChange change in Enum.GetValues(typeof(FixtureChange)))
        {
            if (change == FixtureChange.None) continue;
            Fixture fixture = Fixture.Create();
            PipeSecurity prior = fixture.BuildTestOnlySecurity();
            PrincipalObservation previousService = fixture.Service, previousClient = fixture.Client;
            fixture.Change(change);
            BoundaryEvidence denied = fixture.Observe(); NoAuthority(denied);
            Check(denied.Status == Expected(change));
            Refused(delegate { fixture.BuildTestOnlySecurity(); });
            Check(!fixture.MatchesExactAcl(prior)); // stale detached ACL grants no authority
            Check(fixture.CompareUntrusted(previousService, previousClient).Status == denied.Status);
            fixture.Change(FixtureChange.None);
            Check(fixture.Observe().Status == denied.Status);
            cases++;
        }
        Fixture other = Fixture.Create();
        Check(good.CompareUntrusted(other.Service, other.Client).Status == BoundaryStatus.Untrusted);
        Check(good.CompareUntrusted(good.Client, good.Service).Status == BoundaryStatus.RoleMismatch);
        Check(good.CompareUntrusted(good.Service, good.Service).Status == BoundaryStatus.RoleMismatch);
        PrincipalObservation original = good.Service;
        PrincipalObservation forged = new PrincipalObservation(new object(), original.Role, original.User,
            original.VerifiedServiceSid, original.ProcessId, original.ScmProcessId, original.Session,
            original.ProcessBirth, original.TokenId, original.AuthenticationId, original.ModifiedId, true, false);
        Check(good.CompareUntrusted(forged, good.Client).Status == BoundaryStatus.Untrusted);
        // SID/PID equality and role strings cannot substitute for the private issuer.
        Check(good.CompareUntrusted(null, good.Client).Status == BoundaryStatus.Missing);
        cases++;
    }
    private static BoundaryStatus Expected(FixtureChange change)
    {
        switch (change)
        {
            case FixtureChange.NullService: case FixtureChange.NullClient: return BoundaryStatus.Missing;
            case FixtureChange.SameSid: return BoundaryStatus.SharedIdentity;
            case FixtureChange.SwapRoles: return BoundaryStatus.RoleMismatch;
            case FixtureChange.SubstituteService: case FixtureChange.SubstituteClient: return BoundaryStatus.Untrusted;
            case FixtureChange.WrongExpectedService: case FixtureChange.WrongScmPid: return BoundaryStatus.ScmMismatch;
            case FixtureChange.RestartService: case FixtureChange.ReuseClientPid:
            case FixtureChange.ClientTokenChanged: case FixtureChange.ClientLogonChanged:
            case FixtureChange.ClientModified: case FixtureChange.ClientSessionChanged: return BoundaryStatus.IdentityChanged;
            case FixtureChange.ImpersonateService: case FixtureChange.ImpersonateClient: return BoundaryStatus.Impersonating;
            case FixtureChange.ImpersonationToken: case FixtureChange.ServiceSessionChanged: return BoundaryStatus.TokenRejected;
            case FixtureChange.Expire: return BoundaryStatus.Expired;
            case FixtureChange.Revoke: return BoundaryStatus.Revoked;
            case FixtureChange.Cancel: return BoundaryStatus.Cancelled;
            default: return BoundaryStatus.InvalidPrincipal;
        }
    }
    private static void AclAdversaries()
    {
        Fixture fixture = Fixture.Create();
        PipeSecurity acl = fixture.BuildTestOnlySecurity();
        Check(acl.AreAccessRulesProtected && fixture.Service.User.Equals(acl.GetOwner(typeof(SecurityIdentifier))));
        AuthorizationRuleCollection rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
        Check(rules.Count == 3);
        foreach (PipeAccessRule rule in rules)
        {
            Check(!rule.IsInherited && rule.InheritanceFlags == InheritanceFlags.None && rule.PropagationFlags == PropagationFlags.None);
            SecurityIdentifier sid = (SecurityIdentifier)rule.IdentityReference;
            if (sid.Equals(fixture.Client.User))
            {
                Check(rule.AccessControlType == AccessControlType.Allow);
                Check(rule.PipeAccessRights == (PipeAccessRights.ReadWrite | PipeAccessRights.Synchronize));
                Check((rule.PipeAccessRights & PipeAccessRights.CreateNewInstance) == 0);
                Check((rule.PipeAccessRights & (PipeAccessRights.ChangePermissions | PipeAccessRights.TakeOwnership)) == 0);
            }
            else if (sid.Equals(fixture.Service.User)) Check(rule.PipeAccessRights == PipeAccessRights.FullControl);
            else Check(sid.IsWellKnown(WellKnownSidType.NetworkSid) && rule.AccessControlType == AccessControlType.Deny &&
                rule.PipeAccessRights == PipeAccessRights.FullControl);
        }
        cases++;
        foreach (WellKnownSidType broad in new[] { WellKnownSidType.WorldSid, WellKnownSidType.AuthenticatedUserSid,
            WellKnownSidType.BuiltinUsersSid, WellKnownSidType.LocalSystemSid, WellKnownSidType.NetworkServiceSid })
        {
            PipeSecurity tampered = fixture.BuildTestOnlySecurity();
            tampered.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(broad, null), PipeAccessRights.ReadWrite, AccessControlType.Allow));
            Check(!fixture.MatchesExactAcl(tampered)); cases++;
        }
        acl = fixture.BuildTestOnlySecurity(); acl.SetOwner(fixture.Client.User);
        Check(!fixture.MatchesExactAcl(acl)); cases++;
        acl = fixture.BuildTestOnlySecurity(); acl.SetAccessRuleProtection(false, true);
        Check(!fixture.MatchesExactAcl(acl)); cases++;
        acl = fixture.BuildTestOnlySecurity();
        acl.AddAccessRule(new PipeAccessRule(fixture.Client.User, PipeAccessRights.FullControl, AccessControlType.Allow));
        Check(!fixture.MatchesExactAcl(acl)); cases++;
        acl = fixture.BuildTestOnlySecurity();
        acl.RemoveAccessRuleSpecific(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
            PipeAccessRights.FullControl, AccessControlType.Deny));
        Check(!fixture.MatchesExactAcl(acl)); Check(!fixture.MatchesExactAcl(null)); cases++;
    }
    private static void CallbackAndCancellation()
    {
        for (int i = 0; i < 128; i++)
        {
            Fixture fixture = Fixture.Create();
            BoundaryStatus status = BoundaryStatus.Missing;
            Exception failure = null;
            Thread callback = new Thread(delegate() {
                try
                {
                    status = fixture.Observe().Status; NoAuthority(fixture.Observe());
                    Refused(delegate { fixture.BuildTestOnlySecurity(); });
                }
                catch (Exception error) { failure = error; }
            });
            callback.IsBackground = true; callback.Start();
            Check(callback.Join(2000)); Check(failure == null && status == BoundaryStatus.WrongThread);
            Check(fixture.Observe().Status == BoundaryStatus.SyntheticAclModelOnly);
            PrincipalObservation before = fixture.Service, peer = fixture.Client;
            fixture.Change(FixtureChange.Cancel);
            Check(fixture.CompareUntrusted(before, peer).Status == BoundaryStatus.Cancelled);
            Refused(delegate { fixture.BuildTestOnlySecurity(); });
        }
        cases++;
    }
    public static int Main()
    {
        // Accident barrier only, never identity/provenance authority.
        if (Environment.GetEnvironmentVariable("GITHUB_ACTIONS") != "true" ||
            Environment.GetEnvironmentVariable("RUNNER_ENVIRONMENT") != "github-hosted" ||
            Environment.GetEnvironmentVariable("RUNNER_OS") != "Windows" ||
            Environment.GetEnvironmentVariable("ImageOS") != "win22" ||
            String.Equals(Environment.UserName, "krist", StringComparison.OrdinalIgnoreCase) ||
            String.Equals(Environment.UserName, "Kristian", StringComparison.OrdinalIgnoreCase)) return 2;
        try
        {
            SourceContracts(); LiveIsAlwaysDenied(); RolesAndContinuity(); AclAdversaries(); CallbackAndCancellation();
            Console.WriteLine("P287_FOCUSED=PASS CASES=" + cases + " ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("PRODUCTION=HOLD APPROVALS=0/7 FULL_REGRESSIONS=0/3 P96_ORIGINAL=HIGH_OPEN"); return 0;
        }
        catch (Exception error)
        {
            Console.WriteLine("P287_FOCUSED=HOLD CASES=" + cases + " ASSERTIONS=" + assertions + " ERROR=" + error.GetType().Name);
            return 1;
        }
    }
}
