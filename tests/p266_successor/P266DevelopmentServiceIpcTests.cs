#if !C1_P266_DEVELOPMENT_ONLY
#error P266_TESTS_REQUIRE_DEVELOPMENT_BUILD
#endif
#if !C1_P265_DEVELOPMENT_ONLY
#error P266_TESTS_REQUIRE_P265_DEVELOPMENT_BUILD
#endif
#if !DEBUG
#error P266_TESTS_NO_RELEASE_BUILD
#endif
// Hosted ephemeral Windows only. Same service source/methods, never SCM dispatch.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using Nayeon.ByokC1.P266Development;
using Nayeon.ByokC1.P265Development;

internal static class P266DevelopmentServiceIpcTests
{
    private static int assertions;
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static void Need(bool value)
    { int index = Interlocked.Increment(ref assertions); if (!value) throw new InvalidOperationException("P266_ASSERTION_" + index); }
    private static object Field(object value, string name)
    { return value.GetType().GetField(name, Hidden).GetValue(value); }
    private static void Denied(Disposition view)
    {
        Need(view != null); Need(!view.CredentialAllowed); Need(!view.StoreAllowed);
        Need(!view.PrivilegedAllowed); Need(!view.ProductionEligible);
        if (view.Stopped || view.Revoked || view.Faulted || view.Disposed)
        { Need(view.Marker == 0); Need(view.Endpoint == null); }
    }
    private static void Exited(DevelopmentServiceIpc service)
    {
        Disposition view = service.Observe(); Denied(view);
        Need(view.WorkerExited); Need(view.Marker == 0); Need(view.Endpoint == null);
        Thread worker = (Thread)Field(service, "worker");
        Need(worker == null || worker.Join(1000));
        Need(worker == null || !worker.IsAlive);
        var adapter = (DevelopmentPipeAdapter)Field(service, "adapter");
        if (adapter != null)
        {
            try { Need(((NamedPipeServerStream)Field(adapter, "pipe")).SafePipeHandle.IsClosed); }
            catch (ObjectDisposedException) { Need(true); } // disposed stream may reject its handle getter
        }
    }
    private static void WaitFor(DevelopmentServiceIpc service, int requests, bool fault)
    {
        Stopwatch watch = Stopwatch.StartNew();
        while (watch.ElapsedMilliseconds < 3500)
        {
            Disposition view = service.Observe();
            if (fault ? view.Faulted && view.WorkerExited : view.Requests >= requests) return;
            Thread.Sleep(1);
        }
        throw new TimeoutException("P266_TEST_WAIT");
    }
    private static byte[] Frame(byte operation, Guid id)
    {
        byte[] frame = new byte[28];
        frame[0] = 24; frame[4] = 67; frame[5] = 49; frame[6] = 80; frame[7] = 53;
        frame[8] = 1; frame[9] = operation;
        Buffer.BlockCopy(id.ToByteArray(), 0, frame, 12, 16); return frame;
    }
    private static void Complete(NamedPipeClientStream client, IAsyncResult pending, Action finish)
    {
        using (WaitHandle handle = pending.AsyncWaitHandle)
        {
            bool ready = false;
            try { ready = handle.WaitOne(2500); if (!ready) client.Dispose(); Need(ready); }
            catch { client.Dispose(); throw; }
            finally
            {
                try { finish(); }
                catch (IOException) { if (ready) throw; }
                catch (ObjectDisposedException) { if (ready) throw; }
            }
        }
    }
    private static void Write(NamedPipeClientStream client, byte[] frame)
    {
        IAsyncResult write = client.BeginWrite(frame, 0, frame.Length, null, null);
        Complete(client, write, delegate { client.EndWrite(write); });
    }
    private static NamedPipeClientStream Connect(string endpoint)
    {
        var client = new NamedPipeClientStream(".", endpoint, PipeDirection.InOut,
            PipeOptions.Asynchronous, TokenImpersonationLevel.Impersonation);
        try { client.Connect(1000); return client; }
        catch { client.Dispose(); throw; }
    }
    private static void Exchange(DevelopmentServiceIpc service, byte operation, Guid id)
    {
        int next = service.Observe().Requests + 1;
        using (var client = Connect(service.Observe().Endpoint))
        {
            Write(client, Frame(operation, id));
            byte[] reply = new byte[8]; int offset = 0;
            while (offset < reply.Length)
            {
                int count = 0;
                IAsyncResult read = client.BeginRead(reply, offset, reply.Length - offset, null, null);
                Complete(client, read, delegate { count = client.EndRead(read); });
                Need(count > 0); offset += count;
            }
            Need(BitConverter.ToString(reply) == "43-31-44-4E-01-01-00-00");
            Write(client, new byte[] { 165 });
            WaitFor(service, next, false);
        }
        Denied(service.Observe());
    }
    private static void KernelIdentity(DevelopmentServiceIpc service)
    {
        var adapter = (DevelopmentPipeAdapter)Field(service, "adapter");
        var pipe = (NamedPipeServerStream)Field(adapter, "pipe");
        PipeSecurity acl = pipe.GetAccessControl(); Need(acl.AreAccessRulesProtected);
        using (WindowsIdentity current = WindowsIdentity.GetCurrent())
        {
            Need(acl.GetOwner(typeof(SecurityIdentifier)).Equals(current.User));
            Need(((SecurityIdentifier)Field(adapter, "expectedSid")).Equals(current.User));
            AuthorizationRuleCollection rules = acl.GetAccessRules(true, true, typeof(SecurityIdentifier));
            Need(rules.Count == 2); int allows = 0, denies = 0;
            foreach (PipeAccessRule rule in rules)
            {
                Need(!rule.IsInherited);
                if (rule.AccessControlType == AccessControlType.Allow)
                {
                    allows++; Need(rule.IdentityReference.Equals(current.User));
                    Need(rule.PipeAccessRights == (PipeAccessRights.ReadWrite | PipeAccessRights.Synchronize));
                }
                else
                {
                    denies++; Need(rule.IdentityReference.Equals(new SecurityIdentifier(WellKnownSidType.NetworkSid, null)));
                    Need(rule.PipeAccessRights == PipeAccessRights.FullControl);
                }
            }
            Need(allows == 1 && denies == 1);
        }
    }
    private static void SyntheticAndWire()
    {
        using (var service = new DevelopmentServiceIpc())
        {
            Denied(service.StageSynthetic()); Need(service.Observe().Stages == 0);
            Disposition start = service.StartDevelopment(); Denied(start);
            Need(start.Started && !start.Faulted && !start.WorkerExited && start.Endpoint != null);
            KernelIdentity(service);
            Need(service.ReplaceSynthetic().Replacements == 0);
            Need(service.StageSynthetic().Marker == 266);
            Need(service.StageSynthetic().Stages == 1);
            Need(service.ReplaceSynthetic().Replacements == 1);
            Guid replay = Guid.NewGuid();
            foreach (byte operation in new byte[] { 1, 2, 3, 4 })
            {
                Exchange(service, operation, replay);
                Need(service.Observe().LastReason == (operation == 1 ? DenialReason.DevelopmentHold : DenialReason.Replay));
                Need(service.Observe().Marker == 266); Need(service.Observe().Stages == 1);
                Need(service.Observe().Replacements == 1); Need(service.Observe().Deletes == 0);
            }
            foreach (byte operation in new byte[] { 1, 2, 3, 4 }) Exchange(service, operation, Guid.NewGuid());
            Need(service.DeleteSynthetic().Marker == 0); Need(service.DeleteSynthetic().Deletes == 1);
            Exchange(service, 2, Guid.NewGuid());
            Need(service.Observe().Marker == 0 && service.Observe().Stages == 1);
            Need(service.StageSynthetic().Stages == 2);
            Denied(service.Revoke()); Need(service.Observe().Revoked); Exited(service);
            Need(service.Observe().Deletes == 2);
            NoResurrection(service);
        }
    }
    private static void NoResurrection(DevelopmentServiceIpc service)
    {
        Disposition before = service.Observe();
        Denied(service.StageSynthetic()); Denied(service.ReplaceSynthetic()); Denied(service.DeleteSynthetic());
        Denied(service.StartDevelopment()); Denied(service.StopDevelopment());
        Disposition after = service.Observe();
        Need(after.Stages == before.Stages && after.Replacements == before.Replacements && after.Deletes == before.Deletes);
        Need(after.Faulted); Exited(service);
    }
    private static void TerminalsAndScmCallbacks()
    {
        using (var service = new DevelopmentServiceIpc())
        {
            using (WindowsIdentity current = WindowsIdentity.GetCurrent())
            using (WindowsImpersonationContext context = current.Impersonate())
            {
                using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true)) Need(thread != null);
                Disposition denied = service.StartDevelopment();
                Denied(denied); Need(denied.Faulted && !denied.Started);
            }
            using (WindowsIdentity thread = WindowsIdentity.GetCurrent(true)) Need(thread == null);
            Exited(service); NoResurrection(service);
        }
        foreach (string terminal in new[] { "StopDevelopment", "Revoke", "Fault", "Dispose", "OnStop", "OnShutdown" })
        {
            foreach (bool beforeStart in new[] { true, false })
            {
                var service = new DevelopmentServiceIpc();
                try
                {
                    if (!beforeStart)
                    {
                        typeof(DevelopmentServiceIpc).GetMethod("OnStart", Hidden).Invoke(service, new object[] { new string[0] });
                        Need(service.Observe().Started); service.StageSynthetic();
                        typeof(DevelopmentServiceIpc).GetMethod("OnCustomCommand", Hidden).Invoke(service, new object[] { 266 });
                        Need(service.Observe().Stages == 1);
                    }
                    if (terminal == "Dispose") service.Dispose();
                    else typeof(DevelopmentServiceIpc).GetMethod(terminal, Hidden).Invoke(service, null);
                    Exited(service); NoResurrection(service);
                }
                finally { service.Dispose(); }
                Need(service.Observe().Disposed); Exited(service);
            }
        }
        using (var service = new DevelopmentServiceIpc())
        {
            service.StartDevelopment(); service.StageSynthetic();
            Denied(service.StartDevelopment()); Need(service.Observe().Faulted); Exited(service);
        }
    }
    private static void TimeoutAndTransportFault()
    {
        foreach (int partial in new[] { -1, 2, 10 })
        {
            using (var service = new DevelopmentServiceIpc())
            {
                service.StartDevelopment(); service.StageSynthetic();
                if (partial < 0) WaitFor(service, 0, true);
                else using (var client = Connect(service.Observe().Endpoint))
                {
                    byte[] frame = Frame(1, Guid.NewGuid()); byte[] fragment = new byte[partial];
                    Buffer.BlockCopy(frame, 0, fragment, 0, partial); Write(client, fragment);
                    WaitFor(service, 0, true);
                }
                Need(service.Observe().LastReason == DenialReason.Timeout);
                Need(service.Observe().Deletes == 1); Exited(service); NoResurrection(service);
            }
        }
        using (var service = new DevelopmentServiceIpc())
        {
            service.StartDevelopment(); service.StageSynthetic();
            using (var client = Connect(service.Observe().Endpoint)) Write(client, new byte[] { 255, 0, 0, 0 });
            WaitFor(service, 0, true); Need(service.Observe().LastReason == DenialReason.InvalidFrame);
            Exited(service); NoResurrection(service);
        }
    }
    private static void BoundedLoop()
    {
        using (var service = new DevelopmentServiceIpc())
        {
            service.StartDevelopment(); service.StageSynthetic();
            for (int index = 0; index < DevelopmentServiceIpc.MaximumRequests; index++)
                Exchange(service, 4, Guid.NewGuid());
            WaitFor(service, 0, true); Need(service.Observe().Requests == 128);
            Need(service.Observe().Deletes == 1); Exited(service); NoResurrection(service);
        }
    }
    private static void ContentionAndIsolation()
    {
        using (var service = new DevelopmentServiceIpc())
        {
            service.StartDevelopment(); service.StageSynthetic();
            Exception[] failures = new Exception[2]; Thread[] clients = new Thread[2];
            for (int index = 0; index < clients.Length; index++)
            {
                int slot = index;
                clients[index] = new Thread(delegate()
                { try { Exchange(service, 4, Guid.NewGuid()); } catch (Exception error) { failures[slot] = error; } });
                clients[index].IsBackground = true; clients[index].Start();
            }
            foreach (Thread client in clients) Need(client.Join(4000));
            foreach (Exception failure in failures) Need(failure == null);
            WaitFor(service, 2, false); Need(service.Observe().Requests == 2);
            Need(service.Observe().Marker == 266 && service.Observe().Stages == 1);
            service.StopDevelopment(); Exited(service);
        }
        using (var first = new DevelopmentServiceIpc())
        using (var second = new DevelopmentServiceIpc())
        {
            first.StartDevelopment(); second.StartDevelopment();
            Need(first.Observe().Endpoint != second.Observe().Endpoint);
            first.StageSynthetic(); Need(second.Observe().Marker == 0);
            first.Revoke(); Exchange(second, 4, Guid.NewGuid());
            Need(second.Observe().Stages == 0); Denied(second.Observe()); second.StopDevelopment();
        }
        for (int iteration = 0; iteration < 16; iteration++)
        {
            using (var service = new DevelopmentServiceIpc())
            using (var gate = new ManualResetEvent(false))
            {
                Exception[] errors = new Exception[4]; Thread[] contenders = new Thread[4];
                for (int index = 0; index < contenders.Length; index++)
                {
                    int slot = index;
                    contenders[index] = new Thread(delegate()
                    {
                        try
                        {
                            if (!gate.WaitOne(1500)) throw new TimeoutException();
                            if (slot == 0) Denied(service.StartDevelopment());
                            else if (slot == 1) { Denied(service.StageSynthetic()); Denied(service.ReplaceSynthetic()); }
                            else if (slot == 2) Denied(service.StopDevelopment());
                            else Denied(service.Revoke());
                        }
                        catch (Exception error) { errors[slot] = error; }
                    });
                    contenders[index].IsBackground = true; contenders[index].Start();
                }
                gate.Set();
                foreach (Thread contender in contenders) Need(contender.Join(4000));
                foreach (Exception error in errors) Need(error == null);
                Need(service.Observe().Stopped && service.Observe().Revoked); Exited(service); NoResurrection(service);
            }
        }
        // Stop while a real connected client withholds the body; cancellation must join.
        foreach (int terminal in new[] { 0, 1, 2 })
        using (var service = new DevelopmentServiceIpc())
        {
            service.StartDevelopment(); service.StageSynthetic();
            using (var client = Connect(service.Observe().Endpoint))
            {
                Write(client, new byte[] { 24, 0 });
                Stopwatch watch = Stopwatch.StartNew();
                if (terminal == 0) service.StopDevelopment();
                else if (terminal == 1) service.Revoke();
                else service.Fault();
                Need(watch.ElapsedMilliseconds <= 3000); Exited(service);
            }
        }
    }
    private static int Main(string[] arguments)
    {
        if (arguments.Length != 1 || arguments[0] != "--permitted-disposable-runner") return 64;
        try
        {
            Need(Environment.OSVersion.Platform == PlatformID.Win32NT);
            MethodInfo entry = typeof(DevelopmentServiceIpc).GetMethod("Main", BindingFlags.Static | BindingFlags.NonPublic);
            foreach (string[] invalid in new[] { null, new string[0], new[] { "wrong" },
                new[] { "--development-only-no-effects", "extra" } })
                Need((int)entry.Invoke(null, new object[] { invalid }) == 64);
            SyntheticAndWire(); TerminalsAndScmCallbacks(); TimeoutAndTransportFault(); BoundedLoop(); ContentionAndIsolation();
            Console.WriteLine("P266_NATIVE_TESTS=PASS ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P266_SAME_SID_APP_TRUST=UNTRUSTED P96=HOLD P76=HOLD REAL_KEY=NO_GO PRODUCTION=HOLD");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
