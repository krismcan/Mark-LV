using System;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Nayeon.ByokC1.Service;

internal static class P305StatusPipeTests
{
    private static int checks;
    private static void Check(bool value)
    { int check = Interlocked.Increment(ref checks); if (!value) throw new Exception("P305 assertion " + check); }
    private static string Name() { return "p305-" + Guid.NewGuid().ToString("N"); }
    private static void Done(Task task) { Check(task.Wait(4000)); }
    private static void Hold(Task<StatusObservation> query, bool exact)
    {
        Done(query);
        Check(query.Result.Disposition == "UNTRUSTED_HOLD");
        Check(query.Result.ExactReplyObserved == exact);
        CustodyService.RequireNoImpersonation();
    }
    private static NamedPipeClientStream Raw(string name)
    {
        var pipe = new NamedPipeClientStream(".", name, PipeDirection.InOut,
            PipeOptions.Asynchronous, TokenImpersonationLevel.Anonymous);
        try { pipe.Connect(1000); return pipe; }
        catch { pipe.Dispose(); throw; }
    }
    private static void CheckAcl(PipeSecurity security)
    {
        SecurityIdentifier sid = CustodyService.ReadProcessSid();
        Check(security.AreAccessRulesProtected);
        Check(security.GetOwner(typeof(SecurityIdentifier)).Equals(sid));
        AuthorizationRuleCollection rules = security.GetAccessRules(true, true, typeof(SecurityIdentifier));
        Check(rules.Count == 2);
        bool allow = false, deny = false;
        foreach (PipeAccessRule rule in rules)
        {
            Check(!rule.IsInherited);
            if (rule.AccessControlType == AccessControlType.Allow)
            {
                Check(rule.IdentityReference.Equals(sid));
                Check((rule.PipeAccessRights & ~PipeAccessRights.Synchronize) == PipeAccessRights.ReadWrite);
                allow = true;
            }
            else
            {
                Check(rule.IdentityReference.Equals(new SecurityIdentifier(WellKnownSidType.NetworkSid, null)));
                Check(rule.PipeAccessRights == PipeAccessRights.FullControl);
                deny = true;
            }
        }
        Check(allow && deny);
    }
    private static void Malformed(byte[] bytes)
    {
        string name = Name();
        using (var server = new StatusPipeServer(name))
        {
            using (var client = Raw(name))
            {
                client.Write(bytes, 0, bytes.Length);
                Done(server.Completion);
                Check(server.Refused);
                // No reply to an invalid frame; closure is terminal, never restart.
                byte[] response = new byte[1];
                Task<int> read = client.ReadAsync(response, 0, 1);
                try { Done(read); Check(read.Result == 0); }
                catch (AggregateException error)
                { Check(error.InnerException is IOException || error.InnerException is ObjectDisposedException); }
            }
            Hold(StatusPipeClient.QueryAsync(name, 100), false);
            server.Dispose(); server.Dispose();
        }
    }
    private static NamedPipeServerStream Squatter(string name)
    {
        // Disposable ordinary-user endpoint, no service or machine configuration.
        var acl = new PipeSecurity();
        SecurityIdentifier sid = CustodyService.ReadProcessSid();
        acl.SetAccessRuleProtection(true, false); acl.SetOwner(sid);
        acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.NetworkSid, null),
            PipeAccessRights.FullControl, AccessControlType.Deny));
        acl.AddAccessRule(new PipeAccessRule(sid, PipeAccessRights.ReadWrite, AccessControlType.Allow));
        return new NamedPipeServerStream(name, PipeDirection.InOut, 1, PipeTransmissionMode.Message,
            PipeOptions.Asynchronous, 4, 128, acl, HandleInheritability.None);
    }
    private static void Fabricated(string response, bool exact)
    {
        string name = Name();
        using (var fake = Squatter(name))
        {
            Task peer = ReplyAsync(fake, response);
            Hold(StatusPipeClient.QueryAsync(name, 500), exact);
            Done(peer);
        }
    }
    private static async Task ReplyAsync(NamedPipeServerStream pipe, string response)
    {
        await pipe.WaitForConnectionAsync();
        byte[] request = new byte[4];
        Check(await pipe.ReadAsync(request, 0, 4) == 4);
        Check(Encoding.ASCII.GetString(request) == "C1S1" && pipe.IsMessageComplete);
        byte[] bytes = Encoding.ASCII.GetBytes(response);
        await pipe.WriteAsync(bytes, 0, bytes.Length);
        // Client owns disconnect; no drain call that could block indefinitely.
    }
    private static int Main(string[] args)
    {
        try
        {
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Check(args.Length == 1 && IntPtr.Size * 8 == int.Parse(args[0]));
            Check(typeof(StatusPipeServer).Assembly != typeof(P305StatusPipeTests).Assembly);
            CustodyService.RequireNoImpersonation();
            string name = Name();
            using (var server = new StatusPipeServer(name))
            {
                // Actual kernel DACL readback through the connected client handle.
                using (var client = Raw(name))
                {
                    CheckAcl(client.GetAccessControl());
                    byte[] request = Encoding.ASCII.GetBytes("C1S1");
                    client.Write(request, 0, request.Length);
                    client.ReadMode = PipeTransmissionMode.Message;
                    byte[] bytes = new byte[128];
                    Task<int> read = client.ReadAsync(bytes, 0, bytes.Length);
                    Done(read);
                    Check(Encoding.ASCII.GetString(bytes, 0, read.Result) == StatusPipeServer.Reply);
                    Check(client.IsMessageComplete);
                    Done(server.Completion); Check(!server.Refused);
                }
                Hold(StatusPipeClient.QueryAsync(name, 100), false); // replay after closure
            }
            name = Name();
            using (var server = new StatusPipeServer(name))
            {
                Hold(StatusPipeClient.QueryAsync(name, 500), true);
                Done(server.Completion); Check(!server.Refused);
            }
            Malformed(Encoding.ASCII.GetBytes("C1S0"));
            Malformed(Encoding.ASCII.GetBytes("C1"));
            Malformed(Encoding.ASCII.GetBytes("C1S1X"));
            Hold(StatusPipeClient.QueryAsync(Name(), 100), false); // absent server
            for (int i = 0; i < 12; i++)
            {
                using (var server = new StatusPipeServer(Name()))
                {
                    Task first = Task.Run(delegate { server.Dispose(); });
                    Task second = Task.Run(delegate { server.Dispose(); });
                    Done(first); Done(second); Done(server.Completion); Check(server.Refused);
                }
            }
            name = Name();
            using (var server = new StatusPipeServer(name))
            {
                using (var client = Raw(name)) { } // disconnect before request
                Done(server.Completion); Check(server.Refused);
            }
            name = Name();
            using (var server = new StatusPipeServer(name))
            using (var client = Raw(name))
            {
                Done(server.Completion); Check(server.Refused); // silent connected peer deadline
            }
            name = Name();
            using (var server = new StatusPipeServer(name))
            using (var client = Raw(name))
            { server.Dispose(); Done(server.Completion); Check(server.Refused); }
            Fabricated(StatusPipeServer.Reply, true); // squatted exact reply still UNTRUSTED_HOLD
            Fabricated("C1|AUTHORIZED", false);
            Fabricated(StatusPipeServer.Reply + "X", false);
            name = Name();
            using (var fake = Squatter(name))
            {
                Task connected = fake.WaitForConnectionAsync();
                Task<StatusObservation> query = StatusPipeClient.QueryAsync(name, 100);
                Done(connected); Hold(query, false); // peer never replies
            }
            name = Name();
            using (var fake = Squatter(name))
            {
                Task connected = fake.WaitForConnectionAsync();
                Task<StatusObservation> query = StatusPipeClient.QueryAsync(name, 100);
                Done(connected); fake.Dispose(); Hold(query, false);
            }
            CustodyService.RequireNoImpersonation();
            Console.WriteLine("P305 PASS checks=" + checks + " bits=" + IntPtr.Size * 8 +
                "; real nonsecret pipe; UNTRUSTED_HOLD; release HOLD");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("P305 FAIL " + error.GetType().Name + ": " + error.Message + "; HOLD");
            return 1;
        }
    }
}
