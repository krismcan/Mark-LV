#if !DEBUG || RELEASE || !C1_REVIEW_ISOLATED_ASSEMBLY || !C1_P287_SERVICE_CLIENT_REVIEW_ONLY
#error P287_TEST_ONLY_DEBUG_ISOLATED_AND_OPT_IN_REQUIRED
#endif
using System;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;

namespace Nayeon.ByokC1.P287Review
{
    internal enum PrincipalRole { ExecutingService, InteractiveClient }
    internal enum BoundaryStatus
    {
        MissingTrustedLiveProvenance, Missing, Untrusted, RoleMismatch, SharedIdentity,
        InvalidPrincipal, ScmMismatch, TokenRejected, IdentityChanged, Impersonating,
        Expired, Revoked, Cancelled, WrongThread, SyntheticAclModelOnly
    }
    internal enum FixtureChange
    {
        None, NullService, NullClient, SameSid, SwapRoles, SwapSids, SubstituteService,
        SubstituteClient, WrongExpectedService, WrongScmPid, RestartService,
        ReuseClientPid, ClientTokenChanged, ClientLogonChanged, ClientModified, ClientSessionChanged,
        ServiceSessionChanged, ImpersonateService, ImpersonateClient, ImpersonationToken,
        LocalSystemService, NetworkService, LocalService, EveryoneClient,
        AuthenticatedUsersClient, AnonymousClient, SystemClient, NetworkServiceClient,
        AdminGroupClient, ServiceAsClient, UserAsService, TruncatedServiceSid, NullSid,
        Expire, Revoke, Cancel
    }

    // Immutable modeled OS observations. No public/production observation issuer exists.
    // The private fixture issuer prevents caller-created snapshots becoming trusted input.
    internal sealed class PrincipalObservation
    {
        private readonly object issuer;
        internal readonly PrincipalRole Role;
        internal readonly SecurityIdentifier User, VerifiedServiceSid;
        internal readonly uint ProcessId, ScmProcessId, Session;
        internal readonly long ProcessBirth, TokenId, AuthenticationId, ModifiedId;
        internal readonly bool PrimaryToken, ThreadTokenPresent;
        internal PrincipalObservation(object source, PrincipalRole role, SecurityIdentifier user,
            SecurityIdentifier verifiedServiceSid, uint pid, uint scmPid, uint session,
            long birth, long token, long logon, long modified, bool primary, bool impersonating)
        {
            issuer = source; Role = role; User = user; VerifiedServiceSid = verifiedServiceSid;
            ProcessId = pid; ScmProcessId = scmPid; Session = session; ProcessBirth = birth;
            TokenId = token; AuthenticationId = logon; ModifiedId = modified;
            PrimaryToken = primary; ThreadTokenPresent = impersonating;
        }
        internal bool IssuedBy(object source) { return source != null && Object.ReferenceEquals(issuer, source); }
        internal bool SameToken(PrincipalObservation other)
        {
            return other != null && Role == other.Role && Equal(User, other.User) &&
                Equal(VerifiedServiceSid, other.VerifiedServiceSid) && ProcessId == other.ProcessId &&
                ScmProcessId == other.ScmProcessId && Session == other.Session &&
                ProcessBirth == other.ProcessBirth && TokenId == other.TokenId &&
                AuthenticationId == other.AuthenticationId && ModifiedId == other.ModifiedId &&
                PrimaryToken == other.PrimaryToken && ThreadTokenPresent == other.ThreadTokenPresent;
        }
        private static bool Equal(SecurityIdentifier a, SecurityIdentifier b)
        { return a == null ? b == null : a.Equals(b); }
    }

    internal sealed class BoundaryEvidence
    {
        internal readonly BoundaryStatus Status;
        internal BoundaryEvidence(BoundaryStatus status) { Status = status; }
        internal bool CredentialAllowed { get { return false; } }
        internal bool StoreAllowed { get { return false; } }
        internal bool ProtectedStoreAllowed { get { return false; } }
        internal bool ProductionEligible { get { return false; } }
    }

    internal static class ServiceClientPipeBoundary
    {
        // P282's diagnostic status is not a transferable role capability. In particular,
        // no caller SID, SCM display name, GUI, wire, environment or bool can admit here.
        internal static BoundaryEvidence ObserveLiveAdmission()
        { return new BoundaryEvidence(BoundaryStatus.MissingTrustedLiveProvenance); }

        internal static void DemandBeforeRealPipeCreation()
        { throw new InvalidOperationException("P287_TRUSTED_LIVE_ROLE_ISSUERS_UNAVAILABLE"); }

        private static bool IsServiceSid(SecurityIdentifier sid)
        {
            // Exact virtual-service SID shape, not a prefix-only match or name lookup.
            if (sid == null || sid.BinaryLength != 32) return false;
            byte[] bytes = new byte[sid.BinaryLength]; sid.GetBinaryForm(bytes, 0);
            return bytes[0] == 1 && bytes[1] == 6 && bytes[2] == 0 && bytes[3] == 0 &&
                bytes[4] == 0 && bytes[5] == 0 && bytes[6] == 0 && bytes[7] == 5 &&
                BitConverter.ToUInt32(bytes, 8) == 80;
        }
        private static bool IsUserSid(SecurityIdentifier sid)
        {
            // Bounded synthetic account shape only. Shape is never trusted provenance.
            return sid != null && sid.AccountDomainSid != null && sid.BinaryLength == 28;
        }
        private static bool HasNoAmbientThreadIdentity()
        {
            // Read-only OS query. Never impersonate/revert, enable privileges or fall
            // back to the process identity when the thread query fails.
            try { using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true)) { return thread == null; } }
            catch (System.Security.SecurityException) { return false; }
            catch (UnauthorizedAccessException) { return false; }
        }

        // Fixed OS SecurityIdentifier fixtures; no claim these are installed principals.
        // This is the ONLY positive issuer, and it can produce only a TEST ACL model.
        internal sealed class SyntheticFixture
        {
            private readonly object serviceIssuer = new object(), clientIssuer = new object(), gate = new object();
            private readonly int ownerThread = Thread.CurrentThread.ManagedThreadId;
            private readonly PrincipalObservation initialService, initialClient;
            private PrincipalObservation service, client;
            private long tick;
            private bool revoked, cancelled;
            private SyntheticFixture()
            {
                SecurityIdentifier serviceSid = new SecurityIdentifier("S-1-5-80-101-202-303-404-505");
                SecurityIdentifier userSid = new SecurityIdentifier("S-1-5-21-111-222-333-1001");
                initialService = service = new PrincipalObservation(serviceIssuer, PrincipalRole.ExecutingService,
                    serviceSid, serviceSid, 100, 100, 0, 10, 11, 12, 13, true, false);
                initialClient = client = new PrincipalObservation(clientIssuer, PrincipalRole.InteractiveClient,
                    userSid, null, 200, 0, 1, 20, 21, 22, 23, true, false);
            }
            internal static SyntheticFixture Create() { return new SyntheticFixture(); }
            internal PrincipalObservation Service { get { lock (gate) { return service; } } }
            internal PrincipalObservation Client { get { lock (gate) { return client; } } }

            private BoundaryStatus Classify(PrincipalObservation s, PrincipalObservation c)
            {
                if (Thread.CurrentThread.ManagedThreadId != ownerThread) return BoundaryStatus.WrongThread;
                if (!HasNoAmbientThreadIdentity()) return BoundaryStatus.Impersonating;
                if (cancelled) return BoundaryStatus.Cancelled;
                if (revoked) return BoundaryStatus.Revoked;
                if (tick >= 10) return BoundaryStatus.Expired;
                if (s == null || c == null) return BoundaryStatus.Missing;
                if (s.Role != PrincipalRole.ExecutingService || c.Role != PrincipalRole.InteractiveClient)
                    return BoundaryStatus.RoleMismatch;
                if (!s.IssuedBy(serviceIssuer) || !c.IssuedBy(clientIssuer)) return BoundaryStatus.Untrusted;
                if (s.User == null || c.User == null) return BoundaryStatus.InvalidPrincipal;
                if (s.User.Equals(c.User)) return BoundaryStatus.SharedIdentity;
                if (!IsServiceSid(s.User) || !IsServiceSid(s.VerifiedServiceSid) || !IsUserSid(c.User))
                    return BoundaryStatus.InvalidPrincipal;
                if (!s.User.Equals(s.VerifiedServiceSid) || s.ProcessId == 0 || s.ProcessId != s.ScmProcessId)
                    return BoundaryStatus.ScmMismatch;
                if (s.ThreadTokenPresent || c.ThreadTokenPresent) return BoundaryStatus.Impersonating;
                if (!s.PrimaryToken || !c.PrimaryToken || s.Session != 0 || c.Session == 0 ||
                    s.ProcessBirth <= 0 || c.ProcessBirth <= 0 || c.ProcessId == 0 ||
                    s.ProcessId == c.ProcessId || s.TokenId == c.TokenId || s.AuthenticationId == c.AuthenticationId)
                    return BoundaryStatus.TokenRejected;
                if (!s.SameToken(initialService) || !c.SameToken(initialClient)) return BoundaryStatus.IdentityChanged;
                return BoundaryStatus.SyntheticAclModelOnly;
            }
            internal BoundaryEvidence Observe()
            { lock (gate) { return new BoundaryEvidence(Classify(service, client)); } }
            // Read-only adversarial intake. It cannot replace the fixture's observations.
            internal BoundaryEvidence CompareUntrusted(PrincipalObservation s, PrincipalObservation c)
            {
                lock (gate)
                {
                    BoundaryStatus current = Classify(service, client);
                    return new BoundaryEvidence(current == BoundaryStatus.SyntheticAclModelOnly ? Classify(s, c) : current);
                }
            }

            internal PipeSecurity BuildTestOnlySecurity()
            {
                lock (gate)
                {
                    if (Classify(service, client) != BoundaryStatus.SyntheticAclModelOnly)
                        throw new InvalidOperationException("P287_SYNTHETIC_ROLES_REFUSED");
                    PipeSecurity acl = new PipeSecurity();
                    acl.SetAccessRuleProtection(true, false);
                    acl.SetOwner(service.User);
                    acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
                        PipeAccessRights.FullControl, AccessControlType.Deny));
                    acl.AddAccessRule(new PipeAccessRule(service.User, PipeAccessRights.FullControl, AccessControlType.Allow));
                    acl.AddAccessRule(new PipeAccessRule(client.User, PipeAccessRights.ReadWrite, AccessControlType.Allow));
                    if (Classify(service, client) != BoundaryStatus.SyntheticAclModelOnly || !MatchesExactAcl(acl))
                        throw new InvalidOperationException("P287_SYNTHETIC_ACL_REFUSED");
                    // Detached mutable model only. It is never supplied to a pipe constructor.
                    return acl;
                }
            }
            internal bool MatchesExactAcl(PipeSecurity acl)
            {
                lock (gate)
                {
                    if (Classify(service, client) != BoundaryStatus.SyntheticAclModelOnly || acl == null ||
                        !acl.AreAccessRulesProtected || !service.User.Equals(acl.GetOwner(typeof(SecurityIdentifier)))) return false;
                    // Compare OS-normalized DACL bytes including flags, ACE masks and order.
                    // No broad/inherited/extra ACE or changed owner can pass this equality.
                    PipeSecurity expected = new PipeSecurity();
                    expected.SetAccessRuleProtection(true, false);
                    expected.SetOwner(service.User);
                    expected.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
                        PipeAccessRights.FullControl, AccessControlType.Deny));
                    expected.AddAccessRule(new PipeAccessRule(service.User, PipeAccessRights.FullControl, AccessControlType.Allow));
                    expected.AddAccessRule(new PipeAccessRule(client.User, PipeAccessRights.ReadWrite, AccessControlType.Allow));
                    return acl.GetSecurityDescriptorSddlForm(AccessControlSections.Owner | AccessControlSections.Access) ==
                        expected.GetSecurityDescriptorSddlForm(AccessControlSections.Owner | AccessControlSections.Access);
                }
            }

            // Finite test perturbations, not a live observation/provenance API.
            internal void Change(FixtureChange change)
            {
                lock (gate)
                {
                    switch (change)
                    {
                        case FixtureChange.None: return;
                        case FixtureChange.Expire: tick = 10; return;
                        case FixtureChange.Revoke: revoked = true; return;
                        case FixtureChange.Cancel: cancelled = true; return;
                        case FixtureChange.NullService: service = null; return;
                        case FixtureChange.NullClient: client = null; return;
                        case FixtureChange.SwapRoles: service = initialClient; client = initialService; return;
                    }
                    PrincipalObservation s = initialService, c = initialClient;
                    SecurityIdentifier su = s.User, cu = c.User, expected = s.VerifiedServiceSid;
                    uint scm = s.ScmProcessId, ss = s.Session, cs = c.Session;
                    long sb = s.ProcessBirth, cb = c.ProcessBirth, ct = c.TokenId, ca = c.AuthenticationId, cm = c.ModifiedId;
                    bool si = false, ci = false, primary = true;
                    object sourceS = serviceIssuer, sourceC = clientIssuer;
                    switch (change)
                    {
                        case FixtureChange.SameSid: cu = su; break;
                        case FixtureChange.SwapSids: su = c.User; cu = s.User; break;
                        case FixtureChange.SubstituteService: sourceS = new object(); break;
                        case FixtureChange.SubstituteClient: sourceC = new object(); break;
                        case FixtureChange.WrongExpectedService: expected = new SecurityIdentifier("S-1-5-80-9-8-7-6-5"); break;
                        case FixtureChange.WrongScmPid: scm++; break;
                        case FixtureChange.RestartService: sb++; break;
                        case FixtureChange.ReuseClientPid: cb++; break;
                        case FixtureChange.ClientTokenChanged: ct++; break;
                        case FixtureChange.ClientLogonChanged: ca++; break;
                        case FixtureChange.ClientModified: cm++; break;
                        case FixtureChange.ClientSessionChanged: cs++; break;
                        case FixtureChange.ServiceSessionChanged: ss++; break;
                        case FixtureChange.ImpersonateService: si = true; break;
                        case FixtureChange.ImpersonateClient: ci = true; break;
                        case FixtureChange.ImpersonationToken: primary = false; break;
                        case FixtureChange.LocalSystemService: su = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null); break;
                        case FixtureChange.NetworkService: su = new SecurityIdentifier(WellKnownSidType.NetworkServiceSid, null); break;
                        case FixtureChange.LocalService: su = new SecurityIdentifier(WellKnownSidType.LocalServiceSid, null); break;
                        case FixtureChange.EveryoneClient: cu = new SecurityIdentifier(WellKnownSidType.WorldSid, null); break;
                        case FixtureChange.AuthenticatedUsersClient: cu = new SecurityIdentifier(WellKnownSidType.AuthenticatedUserSid, null); break;
                        case FixtureChange.AnonymousClient: cu = new SecurityIdentifier(WellKnownSidType.AnonymousSid, null); break;
                        case FixtureChange.SystemClient: cu = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null); break;
                        case FixtureChange.NetworkServiceClient: cu = new SecurityIdentifier(WellKnownSidType.NetworkServiceSid, null); break;
                        case FixtureChange.AdminGroupClient: cu = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null); break;
                        case FixtureChange.ServiceAsClient: cu = new SecurityIdentifier("S-1-5-80-9-8-7-6-5"); break;
                        case FixtureChange.UserAsService: su = c.User; cu = new SecurityIdentifier("S-1-5-21-111-222-333-1002"); break;
                        case FixtureChange.TruncatedServiceSid: su = new SecurityIdentifier("S-1-5-80-1"); break;
                        case FixtureChange.NullSid: cu = null; break;
                        default: throw new ArgumentOutOfRangeException("change");
                    }
                    service = new PrincipalObservation(sourceS, s.Role, su, expected, s.ProcessId, scm, ss,
                        sb, s.TokenId, s.AuthenticationId, s.ModifiedId, primary, si);
                    client = new PrincipalObservation(sourceC, c.Role, cu, null, c.ProcessId, c.ScmProcessId, cs,
                        cb, ct, ca, cm, true, ci);
                }
            }
        }
    }
}
