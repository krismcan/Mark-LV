using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Web.Script.Serialization;
using Nayeon.ByokC1.Service;
using Owner = Nayeon.ByokC1.Service.HostedDisposableWinCred.ServiceOwnedAdmission;

internal static class P313ProductAdmissionTests
{
    private static int count;
    private static void Check(bool value) { if (!value) throw new Exception("P313 assertion; HOLD."); count++; }
    private static void Refuse(Action action)
    {
        bool refused = false;
        try { action(); } catch (InvalidOperationException) { refused = true; }
        Check(refused);
    }
    private static string Fresh() { return Guid.NewGuid().ToString("N"); }
    private static void ReadOnlyNegatives()
    {
        Check(typeof(Owner).Assembly != Assembly.GetExecutingAssembly());
        Check(typeof(Owner).DeclaringType == typeof(HostedDisposableWinCred));
        Check(Assembly.GetExecutingAssembly().GetName().Name == "P313.ProductAdmission.Tests");
        foreach (string id in new[] { null, "", "wrong", Guid.Empty.ToString("N"), Guid.NewGuid().ToString("D"), "../" + Fresh() })
            Refuse(delegate { new Owner(id, false); });
        string brake = Environment.GetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY");
        try
        {
            Environment.SetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY", null);
            Refuse(HostedDisposableWinCred.RequireHostedP313);
            Refuse(delegate { new Owner(Fresh(), false); });
        }
        finally { Environment.SetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY", brake); }        var env = new Dictionary<string, string> {
            {"GITHUB_ACTIONS", "true"}, {"RUNNER_OS", "Windows"}, {"RUNNER_ENVIRONMENT", "github-hosted"},
            {"GITHUB_EVENT_NAME", "pull_request"}, {"GITHUB_REPOSITORY", "krismcan/Mark-LV"},
            {"GITHUB_HEAD_REF", "byok-c1-p313-service-owned-vault-admission-20261123"},
            {"GITHUB_BASE_REF", "byok-c1-p312-service-hosted-windows-vault-20261123"}, {"P313_SYNTHETIC_HOSTED_ONLY", "1"} };
        string sha = new string('a', 40);
        var repo = new Dictionary<string, object> { {"full_name", "krismcan/Mark-LV"}, {"fork", true}, {"id", 1402212689} };
        var head = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_HEAD_REF"]}, {"sha", sha} };
        var baseSide = new Dictionary<string, object> { {"repo", new Dictionary<string, object>(repo)}, {"ref", env["GITHUB_BASE_REF"]}, {"sha", "d980c4ef7de118a685c245e4dd915d1d9fe8ca1a"} };
        var pr = new Dictionary<string, object> { {"draft", true}, {"head", head}, {"base", baseSide} };
        var root = new Dictionary<string, object> { {"repository", repo}, {"pull_request", pr} };
        var serializer = new JavaScriptSerializer();
        Action validate = delegate { HostedDisposableWinCred.ValidateContextP313(env, serializer.Serialize(root), sha); };
        validate(); count++; // Pure predicate: no OS or native access.
        foreach (string key in env.Keys.ToArray())
        { string value = env[key]; env[key] = "denied"; Refuse(validate); env[key] = value; }
        pr["draft"] = false; Refuse(validate); pr["draft"] = true;
        repo["fork"] = false; Refuse(validate); repo["fork"] = true;
        repo["fork"] = "true"; Refuse(validate); repo["fork"] = true;
        foreach (var endpoint in new[] { head, baseSide })
        {
            var endpointRepo = (Dictionary<string, object>)endpoint["repo"];
            endpointRepo["id"] = 456; Refuse(validate); endpointRepo["id"] = 1402212689;
            endpointRepo["fork"] = false; Refuse(validate); endpointRepo["fork"] = true;
            endpointRepo["fork"] = "true"; Refuse(validate); endpointRepo["fork"] = true;
        }
        head["sha"] = new string('b', 40); Refuse(validate); head["sha"] = sha;
        baseSide["sha"] = sha; Refuse(validate); baseSide["sha"] = "d980c4ef7de118a685c245e4dd915d1d9fe8ca1a";
        head["repo"] = new Dictionary<string, object> { {"full_name", "other/repo"}, {"fork", false}, {"id", 456} };
        Refuse(validate); head["repo"] = repo;
        foreach (var endpoint in new[] { head, baseSide })
        {
            object saved = endpoint["ref"]; endpoint["ref"] = "wrong"; Refuse(validate); endpoint["ref"] = saved;
            var endpointRepo = (Dictionary<string, object>)endpoint["repo"];
            saved = endpointRepo["full_name"]; endpointRepo["full_name"] = "wrong/repo"; Refuse(validate); endpointRepo["full_name"] = saved;
        }
        var headRepo = (Dictionary<string, object>)head["repo"];
        var baseRepo = (Dictionary<string, object>)baseSide["repo"];
        repo["id"] = 456; headRepo["id"] = 456; baseRepo["id"] = 456;
        Refuse(validate); // Matching foreign IDs must still refuse the fixed authorized repository.
        repo["id"] = 1402212689; headRepo["id"] = 1402212689; baseRepo["id"] = 1402212689;
        Refuse(delegate { HostedDisposableWinCred.ValidateContextP313(env, serializer.Serialize(root), "bad"); });
        Refuse(delegate { HostedDisposableWinCred.ValidateContextP313(env, new string(' ', 65536), sha); });
    }

    private static void Absent(string id)
    {
        // A new owner invokes the private outer constructor's real absence preflight.
        using (var fresh = new Owner(id, false)) Check(!fresh.MayHaveEffect);
    }
    private static Owner.ControlResult Control(Owner owner, int kind)
    { return kind == 0 ? owner.Revoke() : kind == 1 ? owner.Stop() : owner.Fault(); }
    private static void NativeCases()
    {
        HostedDisposableWinCred.RequireHostedP313();
        for (int kind = 0; kind < 3; kind++)
        {
            string id = Fresh();
            using (var owner = new Owner(id, false))
            {
                object approval = owner.Issue();
                Refuse(delegate { owner.Issue(); });
                Check(Control(owner, kind) == (kind == 0 ? Owner.ControlResult.Revoked :
                    kind == 1 ? Owner.ControlResult.Stopped : Owner.ControlResult.Faulted));
                Refuse(delegate { owner.Dispatch(approval); });
                Check(!owner.MayHaveEffect && !owner.RecoveryRequired);
                Refuse(delegate { owner.Issue(); });
                owner.Dispose(); Check(owner.CleanupVerified);
            }
            Absent(id);
        }
        foreach (int invalidKind in new[] { 0, 1, 2 })
        {
            string id = Fresh(), otherId = Fresh();
            using (var owner = new Owner(id, false))
            using (var other = new Owner(otherId, false))
            {
                object approval = owner.Issue();
                object invalid = invalidKind == 0 ? null : invalidKind == 1 ? new object() : other.Issue();
                Refuse(delegate { owner.Dispatch(invalid); });
                Refuse(delegate { owner.Dispatch(approval); });
                Check(!owner.MayHaveEffect);
            }
            Absent(id); Absent(otherId);
        }
        // A recursive monitor entry is denied and latches a fault even if the caller catches it.
        string reentryId = Fresh();
        using (var owner = new Owner(reentryId, false))
        {
            object approval = owner.Issue();
            object gate = typeof(Owner).GetField("gate", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(owner);
            lock (gate) Refuse(delegate { owner.Dispatch(approval); });
            Refuse(delegate { owner.Dispatch(approval); });
            Check(!owner.MayHaveEffect);
        }
        Absent(reentryId);

        for (int kind = 0; kind < 3; kind++) DispatchFirst(kind, false);
        DispatchFirst(0, true); // Waiting control must say HoldUnknown, never successful revocation.

        string faultId = Fresh();
        using (var owner = new Owner(faultId, false))
        {
            object approval = owner.Issue(); owner.Dispatch(approval);
            string brake = Environment.GetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY");
            try
            {
                Environment.SetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY", null);
                Refuse(owner.Dispose); Check(!owner.CleanupVerified);
            }
            finally { Environment.SetEnvironmentVariable("P313_SYNTHETIC_HOSTED_ONLY", brake); }
            Check(owner.MayHaveEffect && owner.RecoveryRequired);
            Refuse(delegate { owner.Dispatch(approval); });
            Check(owner.Fault() == Owner.ControlResult.TooLate);
            owner.Dispose(); Check(owner.CleanupVerified);
            Refuse(delegate { owner.Issue(); });
        }
        Absent(faultId);
    }
    private static void DispatchFirst(int kind, bool timeout)
    {
        string id = Fresh();
        using (var owner = new Owner(id, true))
        using (var attempted = new ManualResetEvent(false))
        {
            object approval = owner.Issue();
            Exception dispatchFailure = null, controlFailure = null;
            Owner.ControlResult result = Owner.ControlResult.HoldUnknown;
            var dispatch = new Thread(delegate() {
                try { owner.Dispatch(approval); } catch (Exception ex) { dispatchFailure = ex; }
            }) { IsBackground = true };
            var revoker = new Thread(delegate() {
                attempted.Set();
                try { result = Control(owner, kind); } catch (Exception ex) { controlFailure = ex; }
            }) { IsBackground = true };
            bool revokerStarted = false;
            dispatch.Start();
            try
            {
                Check(owner.WaitBeforeNative()); // Inside the owner monitor, before actual native Add.
                revoker.Start(); revokerStarted = true; Check(attempted.WaitOne(1000));
                if (timeout) Check(revoker.Join(3500));
                else Check(!revoker.Join(100)); // Cannot publish successful cancellation while dispatch owns gate.
            }
            finally
            {
                owner.ReleaseNative();
                Check(dispatch.Join(15000));
                if (revokerStarted) Check(revoker.Join(3000));
            }
            Check(controlFailure == null);
            Check(result == (timeout ? Owner.ControlResult.HoldUnknown : Owner.ControlResult.TooLate));
            Check(owner.MayHaveEffect && owner.RecoveryRequired);
            if (timeout) Check(dispatchFailure is InvalidOperationException);
            else
            {
                Check(dispatchFailure == null);
                // Actual native Add/readback left a credential: another constructor must refuse collision.
                Refuse(delegate { new Owner(id, false); });
            }
            Refuse(delegate { owner.Dispatch(approval); });
            Refuse(delegate { owner.Issue(); });
            Check(owner.Revoke() == Owner.ControlResult.TooLate);
            Check(owner.Stop() == Owner.ControlResult.TooLate);
            Check(owner.Fault() == Owner.ControlResult.TooLate);
            owner.Dispose(); owner.Dispose(); Check(owner.CleanupVerified);
        }
        Absent(id); // Required for PASS, also after timeout/fault paths.
    }
    private static int Main(string[] args)
    {
        try
        {
            Check(args.Length == 0); // Hosted workflow cannot silently skip actual native cases.
            ReadOnlyNegatives(); NativeCases();
            Check(count > 0 && count < 1000);
            Console.WriteLine("P313 PRODUCT ADMISSION TESTS PASS cleanup=verified count=" + count); return 0;
        }
        catch { Console.Error.WriteLine("P313 PRODUCT ADMISSION TESTS FAIL; cleanup unproven; HOLD."); return 1; }
    }
}
