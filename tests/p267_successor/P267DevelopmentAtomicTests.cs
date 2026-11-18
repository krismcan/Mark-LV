#if !C1_P267_DEVELOPMENT_ONLY
#error P267_TESTS_REQUIRE_DEVELOPMENT_BUILD
#endif
#if !C1_P265_DEVELOPMENT_ONLY
#error P267_TESTS_REQUIRE_P265_DEVELOPMENT_BUILD
#endif
#if !DEBUG
#error P267_TESTS_NO_RELEASE_BUILD
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
using Nayeon.ByokC1.P267Development;
using Nayeon.ByokC1.P265Development;

internal static class P267DevelopmentAtomicTests
{
    private static int assertions;
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static void Need(bool value)
    { int index = Interlocked.Increment(ref assertions); if (!value) throw new InvalidOperationException("P267_ASSERTION_" + index); }
    private static object Field(object value, string name)
    { return value.GetType().GetField(name, Hidden).GetValue(value); }
    private static void Denied(Disposition view)
    {
        Need(!view.CredentialAllowed && !view.StoreAllowed && !view.PrivilegedAllowed && !view.ProductionEligible);
        Need(view.Submissions >= 0 && view.Submissions <= 1);
        if (view.Submissions == 1) Need(view.MayHaveEffect && view.RecoveryRequired && view.TooLate);
        if (view.Stopped || view.Revoked || view.Faulted || view.Disposed) Need(view.Endpoint == null);
    }
    private static void Exited(DevelopmentAtomicService service)
    {
        Denied(service.Observe()); Need(service.Observe().WorkerExited);
        Thread worker = (Thread)Field(service, "worker");
        Need(worker == null || worker.Join(1000));
    }    private static void WaitFor(DevelopmentAtomicService service, int requests, bool fault)
    {
        Stopwatch watch = Stopwatch.StartNew();
        while (watch.ElapsedMilliseconds < 3500)
        {
            Disposition view = service.Observe();
            if (fault ? view.Faulted && view.WorkerExited : view.Requests >= requests) return;
            Thread.Sleep(1);
        }
        throw new TimeoutException("P267_TEST_WAIT");
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
    private static void Exchange(DevelopmentAtomicService service, byte operation, Guid id)
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
    private static Disposition Terminal(DevelopmentAtomicService service, int kind)
    {
        if (kind == 0) return service.Revoke();
        else if (kind == 1) return service.StopDevelopment();
        else return service.Fault();
    }
    private static void LaterDenied(DevelopmentAtomicService service, DevelopmentAtomicService.Attempt attempt)
    {
        int before = service.Observe().Submissions;
        Need(service.PrepareSynthetic() == null);
        Denied(service.DispatchSynthetic(attempt));
        Denied(service.DispatchSyntheticFailure(attempt));
        Need(service.Observe().Submissions == before);
    }
    // Deterministic state-phase winners. Coordination stays entirely outside the owner.
    private static void OrderedWinners()
    {
        foreach (int kind in new[] { 0, 1, 2 })
        foreach (bool dispatchFirst in new[] { false, true })
        using (var service = new DevelopmentAtomicService(true))
        using (var firstDone = new ManualResetEvent(false))
        {
            Need(service.StartDevelopment().Started);
            var attempt = service.PrepareSynthetic(); Need(attempt != null);
            Exception error = null;
            Thread first = new Thread(delegate()
            {
                try
                {
                    if (dispatchFirst) service.DispatchSynthetic(attempt);
                    else Terminal(service, kind);
                }
                catch (Exception failure) { error = failure; }
                finally { firstDone.Set(); }
            });
            first.IsBackground = true; first.Start();
            Need(firstDone.WaitOne(4000)); Need(first.Join(1000)); Need(error == null);
            if (dispatchFirst) Terminal(service, kind); else service.DispatchSynthetic(attempt);
            var view = service.Observe(); Denied(view);
            Need(view.Submissions == (dispatchFirst ? 1 : 0));
            Need(view.TooLate == dispatchFirst && view.MayHaveEffect == dispatchFirst);
            LaterDenied(service, attempt); Exited(service);
        }
    }
    private static void ContendedGate()
    {
        foreach (int kind in new[] { 0, 1, 2 })
        for (int iteration = 0; iteration < 12; iteration++)
        using (var service = new DevelopmentAtomicService(true))
        using (var ready = new CountdownEvent(2))
        using (var atCall = new CountdownEvent(2))
        using (var go = new ManualResetEvent(false))
        {
            service.StartDevelopment(); var attempt = service.PrepareSynthetic();
            object gate = Field(service, "sync");
            Exception[] errors = new Exception[2]; Thread[] threads = new Thread[2];
            Disposition terminalResult = null;
            Monitor.Enter(gate); // driver only: force both contenders to queue on the real gate
            try
            {
                for (int index = 0; index < 2; index++)
                {
                    int slot = index;
                    threads[index] = new Thread(delegate()
                    {
                        try
                        {
                            ready.Signal();
                            if (!go.WaitOne(2000)) throw new TimeoutException();
                            atCall.Signal();
                            if (slot == 0) service.DispatchSynthetic(attempt); else terminalResult = Terminal(service, kind);
                        }
                        catch (Exception failure) { errors[slot] = failure; }
                    });
                    threads[index].IsBackground = true; threads[index].Start();
                }
                Need(ready.Wait(2000)); go.Set();
                Need(atCall.Wait(2000));
                Need(SpinWait.SpinUntil(delegate { return
                    (threads[0].ThreadState & System.Threading.ThreadState.WaitSleepJoin) != 0 &&
                    (threads[1].ThreadState & System.Threading.ThreadState.WaitSleepJoin) != 0; }, 1000));
                // Monitor has no FIFO guarantee; never assert a scheduler-specific winner.
            }
            finally { Monitor.Exit(gate); }
            foreach (Thread thread in threads) Need(thread.Join(4000));
            foreach (Exception error in errors) Need(error == null);
            var view = service.Observe(); Denied(view);
            Need(view.Submissions == 0 || (view.Submissions == 1 && view.TooLate && view.RecoveryRequired));
            Need(terminalResult != null && terminalResult.Submissions == view.Submissions);
            Need(terminalResult.TooLate == view.TooLate);
            LaterDenied(service, attempt); Exited(service);
        }
    }
    private static void ReentryAndFailure()
    {
        foreach (string name in new[] { "PrepareSynthetic", "Revoke", "StopDevelopment", "Fault", "StartDevelopment", "Observe", "DispatchSynthetic", "DispatchSyntheticFailure", "Dispose" })
        using (var service = new DevelopmentAtomicService(true))
        {
            service.StartDevelopment(); var attempt = service.PrepareSynthetic();
            var outer = (IDisposable)typeof(DevelopmentAtomicService).GetMethod("Enter", Hidden).Invoke(service, null);
            try
            {
                try
                {
                    typeof(DevelopmentAtomicService).GetMethod(name, Hidden).Invoke(service,
                        name == "Dispose" ? new object[] { true } :
                        name.StartsWith("DispatchSynthetic", StringComparison.Ordinal) ? new object[] { attempt } : null);
                    Need(false);
                }
                catch (TargetInvocationException error)
                { Need(error.InnerException is InvalidOperationException && error.InnerException.Message == "P267_NONREENTRANT"); }
            }
            finally { outer.Dispose(); }
            Need(service.Observe().Faulted && service.Observe().RecoveryRequired);
            Need(service.Observe().Submissions == 0); LaterDenied(service, attempt);
            service.StopDevelopment(); Exited(service);
        }
        using (var service = new DevelopmentAtomicService(true))
        {
            service.StartDevelopment(); var attempt = service.PrepareSynthetic();
            Need(service.PrepareSynthetic() == null);
            Need(service.DispatchSynthetic(null).Submissions == 0);
            Need(service.DispatchSynthetic(new DevelopmentAtomicService.Attempt()).Submissions == 0);
            var failed = service.DispatchSyntheticFailure(attempt);
            Need(failed.Faulted && failed.Submissions == 1 && failed.TooLate && failed.RecoveryRequired);
            LaterDenied(service, attempt); service.StopDevelopment(); Exited(service);
            using (var restart = new DevelopmentAtomicService(false))
            {
                restart.StartDevelopment(); Need(restart.Observe().RecoveryRequired);
                Need(restart.PrepareSynthetic() == null);
                Need(restart.DispatchSynthetic(attempt).Submissions == 0);
                restart.StopDevelopment(); Exited(restart);
            }
            using (var independent = new DevelopmentAtomicService(true))
            {
                independent.StartDevelopment(); independent.PrepareSynthetic();
                Need(independent.DispatchSynthetic(attempt).Submissions == 0);
                independent.StopDevelopment(); Exited(independent);
            }
        }
    }
    private static void WireAndLifecycle()
    {
        using (var service = new DevelopmentAtomicService(true))
        {
            service.StartDevelopment(); var attempt = service.PrepareSynthetic();
            Guid id = Guid.NewGuid();
            for (byte operation = 1; operation <= 4; operation++) Exchange(service, operation, id);
            Need(service.Observe().LastReason == DenialReason.Replay);
            Need(service.Observe().Submissions == 0 && !service.Observe().MayHaveEffect);
            service.DispatchSynthetic(attempt); Exchange(service, 4, Guid.NewGuid());
            Need(service.Observe().Submissions == 1);
            typeof(DevelopmentAtomicService).GetMethod("OnStop", Hidden).Invoke(service, null);
            Exited(service); LaterDenied(service, attempt);
        }
        foreach (int kind in new[] { 0, 1, 2 })
        using (var service = new DevelopmentAtomicService(true))
        {
            service.StartDevelopment();
            using (var client = Connect(service.Observe().Endpoint))
            {
                Write(client, new byte[] { 24, 0 });
                Terminal(service, kind); Exited(service); Need(service.Observe().Submissions == 0);
            }
        }
        using (var service = new DevelopmentAtomicService(true))
        {
            service.StartDevelopment();
            using (var client = Connect(service.Observe().Endpoint)) Write(client, new byte[] { 255, 0, 0, 0 });
            WaitFor(service, 0, true); Need(service.Observe().Faulted);
            LaterDenied(service, null); Exited(service);
        }
        using (var service = new DevelopmentAtomicService(true))
        {
            service.StartDevelopment(); WaitFor(service, 0, true);
            LaterDenied(service, null); Exited(service);
        }
    }
    private static int Main(string[] arguments)
    {
        if (arguments.Length != 1 || arguments[0] != "--permitted-disposable-runner") return 64;
        try
        {
            Need(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Need((int)typeof(DevelopmentAtomicService).GetMethod("Main", BindingFlags.Static | BindingFlags.NonPublic)
                .Invoke(null, new object[] { new[] { "--development-only-no-effects" } }) == 64);
            OrderedWinners(); ContendedGate(); ReentryAndFailure(); WireAndLifecycle();
            Console.WriteLine("P267_NATIVE_TESTS=PASS ASSERTIONS=" + assertions + " BITS=" + (IntPtr.Size * 8));
            Console.WriteLine("P267_SAME_SID_APP_TRUST=UNTRUSTED P96=HOLD P76=HOLD REAL_KEY=NO_GO PRODUCTION=HOLD");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
