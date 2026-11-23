using System;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Nayeon.ByokC1.Service;

internal static class P307ServiceDenialTests
{
    private static int checks;
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static void Check(bool value)
    { int n = Interlocked.Increment(ref checks); if (!value) throw new Exception("P307 assertion " + n); }
    private static FieldInfo Field(Type type, string name)
    {
        FieldInfo field = type.GetField(name, Hidden);
        Check(field != null && field.IsPrivate);
        return field;
    }
    private static void Join(Task[] tasks) { Check(Task.WaitAll(tasks, 5000)); }
    private static SyntheticTransactionRequest Request(SyntheticTransactionOwner owner, ulong id, SyntheticOperation op)
    {
        SyntheticTransactionResult snapshot = owner.Observe();
        return new SyntheticTransactionRequest(snapshot.Owner, snapshot.Epoch, id, op);
    }
    private static void Is(SyntheticTransactionResult result, TransactionDisposition disposition)
    { Check(result != null && !result.Allowed && result.Disposition == disposition); }
    private static void Inert(SyntheticTransactionResult result, SyntheticTransactionRequest request)
    {
        Is(result, TransactionDisposition.OwnerTerminated);
        Check(object.ReferenceEquals(result.Request, request));
        Check(result.Owner == Guid.Empty && result.Epoch == 0 && result.State == TransactionOwnerState.Stopped);
    }

    // Reflection composes metadata in an UNSTARTED ServiceBase only. ActiveDenied
    // here is a synthetic fixture, never evidence of OS dispatch or valid startup.
    private sealed class Fixture : IDisposable
    {
        internal readonly CustodyService Service;
        internal readonly LifecycleCoordinator Coordinator;
        internal readonly SyntheticTransactionOwner Owner;
        internal readonly object Lifecycle;
        internal Fixture(LifecycleState state, bool withOwner, bool terminal)
        {
            Service = (CustodyService)Activator.CreateInstance(typeof(CustodyService), true);
            Check(Field(typeof(CustodyService), "transactions").GetValue(Service) == null);
            Coordinator = (LifecycleCoordinator)Field(typeof(CustodyService), "coordinator").GetValue(Service);
            Lifecycle = Field(typeof(CustodyService), "lifecycle").GetValue(Service);
            Check(Coordinator.Observe().State == LifecycleState.Created);
            if (state == LifecycleState.Starting || state == LifecycleState.ActiveDenied) Coordinator.BeginStart();
            if (state == LifecycleState.ActiveDenied) Coordinator.CompleteStart();
            if (state == LifecycleState.Stopped) Coordinator.Stop();
            if (state == LifecycleState.Faulted) Coordinator.Fault();
            if (state == LifecycleState.Disposed) Coordinator.Dispose();
            if (!Enum.IsDefined(typeof(LifecycleState), state))
                Field(typeof(LifecycleCoordinator), "state").SetValue(Coordinator, state);
            if (withOwner)
            {
                Owner = new SyntheticTransactionOwner();
                Field(typeof(CustodyService), "transactions").SetValue(Service, Owner);
            }
            Field(typeof(CustodyService), "terminal").SetValue(Service, terminal);
        }
        public void Dispose() { Service.Dispose(); }
    }

    private static void GateNegatives()
    {
        LifecycleState[] states = { LifecycleState.Created, LifecycleState.Starting, LifecycleState.ActiveDenied,
            LifecycleState.Stopped, LifecycleState.Faulted, LifecycleState.Disposed,
            (LifecycleState)int.MinValue, (LifecycleState)int.MaxValue };
        foreach (LifecycleState state in states)
        foreach (bool present in new[] { false, true })
        foreach (bool terminal in new[] { false, true })
        {
            if (state == LifecycleState.ActiveDenied && present && !terminal) continue;
            using (var fixture = new Fixture(state, present, terminal))
            {
                SyntheticTransactionResult before = null;
                if (present)
                {
                    Is(fixture.Owner.Deny(Request(fixture.Owner, 7, SyntheticOperation.Add)), TransactionDisposition.Denied);
                    before = fixture.Owner.Observe();
                }
                SyntheticTransactionRequest request = present ? Request(fixture.Owner, ulong.MaxValue, SyntheticOperation.Delete) :
                    new SyntheticTransactionRequest(Guid.NewGuid(), 1, ulong.MaxValue, SyntheticOperation.Delete);
                foreach (SyntheticTransactionRequest attempt in new[] { request, null,
                    new SyntheticTransactionRequest(Guid.Empty, -1, 0, (SyntheticOperation)0) })
                {
                    Inert(fixture.Service.RefuseSyntheticRequest(attempt), attempt);
                    Inert(fixture.Service.CancelSyntheticRequest(attempt), attempt);
                }
                Check(fixture.Coordinator.Observe().State == state);
                Check((bool)Field(typeof(CustodyService), "terminal").GetValue(fixture.Service) == terminal);
                if (present)
                {
                    SyntheticTransactionResult after = fixture.Owner.Observe();
                    Check(after.Owner == before.Owner && after.Epoch == before.Epoch && after.State == before.State);
                    Check((ulong)Field(typeof(SyntheticTransactionOwner), "highWater").GetValue(fixture.Owner) == 7);
                    // The refused max-ID attempt must not reserve or poison the owner.
                    Is(fixture.Owner.Deny(Request(fixture.Owner, 8, SyntheticOperation.Add)), TransactionDisposition.Denied);
                }
            }
        }
    }

    private static void Sequential()
    {
        using (var fixture = new Fixture(LifecycleState.ActiveDenied, true, false))
        using (var other = new Fixture(LifecycleState.ActiveDenied, true, false))
        {
            CustodyService service = fixture.Service;
            SyntheticTransactionOwner owner = fixture.Owner;
            SyntheticTransactionResult original = owner.Observe();
            Is(service.RefuseSyntheticRequest(null), TransactionDisposition.InvalidRequest);
            Is(service.CancelSyntheticRequest(null), TransactionDisposition.InvalidRequest);
            Is(service.RefuseSyntheticRequest(Request(owner, 0, SyntheticOperation.Add)), TransactionDisposition.InvalidRequest);
            Is(service.CancelSyntheticRequest(Request(owner, 0, SyntheticOperation.Add)), TransactionDisposition.InvalidRequest);
            foreach (int invalid in new[] { int.MinValue, -1, 0, 4, int.MaxValue })
            {
                SyntheticTransactionRequest request = Request(owner, ulong.MaxValue, (SyntheticOperation)invalid);
                Is(service.RefuseSyntheticRequest(request), TransactionDisposition.InvalidOperation);
                Is(service.CancelSyntheticRequest(request), TransactionDisposition.InvalidOperation);
            }
            foreach (Guid identity in new[] { Guid.Empty, other.Owner.Observe().Owner })
            {
                var request = new SyntheticTransactionRequest(identity, 1, ulong.MaxValue, SyntheticOperation.Add);
                Is(service.RefuseSyntheticRequest(request), TransactionDisposition.WrongOwner);
                Is(service.CancelSyntheticRequest(request), TransactionDisposition.WrongOwner);
            }
            foreach (long epoch in new[] { long.MinValue, -1L, 0L, 2L, long.MaxValue })
            {
                var request = new SyntheticTransactionRequest(original.Owner, epoch, ulong.MaxValue, SyntheticOperation.Add);
                Is(service.RefuseSyntheticRequest(request), TransactionDisposition.StaleEpoch);
                Is(service.CancelSyntheticRequest(request), TransactionDisposition.StaleEpoch);
            }
            ulong id = 1;
            foreach (SyntheticOperation operation in new[] { SyntheticOperation.Add, SyntheticOperation.Replace, SyntheticOperation.Delete })
            foreach (bool cancel in new[] { false, true })
            {
                SyntheticTransactionRequest request = Request(owner, id, operation);
                SyntheticTransactionResult result = cancel ? service.CancelSyntheticRequest(request) : service.RefuseSyntheticRequest(request);
                Is(result, cancel ? TransactionDisposition.Cancelled : TransactionDisposition.Denied);
                Check(object.ReferenceEquals(result.Request, request) && result.Owner == original.Owner &&
                    result.Epoch == 1 && result.State == TransactionOwnerState.ActiveDenied);
                foreach (SyntheticOperation replayOperation in new[] { SyntheticOperation.Add, SyntheticOperation.Replace, SyntheticOperation.Delete })
                {
                    SyntheticTransactionRequest replay = Request(owner, id, replayOperation);
                    Is(service.RefuseSyntheticRequest(replay), TransactionDisposition.Replay);
                    Is(service.CancelSyntheticRequest(replay), TransactionDisposition.Replay);
                }
                Is(other.Service.RefuseSyntheticRequest(request), TransactionDisposition.WrongOwner);
                Is(other.Service.CancelSyntheticRequest(request), TransactionDisposition.WrongOwner);
                id++;
            }
            Is(service.CancelSyntheticRequest(Request(owner, 100, SyntheticOperation.Replace)), TransactionDisposition.Cancelled);
            Is(service.RefuseSyntheticRequest(Request(owner, 99, SyntheticOperation.Delete)), TransactionDisposition.Replay);
            Is(service.RefuseSyntheticRequest(Request(owner, ulong.MaxValue, SyntheticOperation.Add)), TransactionDisposition.Denied);
            Is(service.CancelSyntheticRequest(Request(owner, ulong.MaxValue, SyntheticOperation.Replace)), TransactionDisposition.Replay);
            Is(service.RefuseSyntheticRequest(Request(owner, 1, SyntheticOperation.Delete)), TransactionDisposition.Replay);
            Check(fixture.Coordinator.Observe().State == LifecycleState.ActiveDenied);
            Check(owner.Observe().State == TransactionOwnerState.ActiveDenied && owner.Observe().Epoch == 1);
        }
    }

    private static void Close(CustodyService service, int mode)
    {
        if (mode == 2) { service.Dispose(); return; }
        if (mode == 3)
        {
            typeof(CustodyService).GetMethod("Dispose", Hidden, null, new[] { typeof(bool) }, null)
                .Invoke(service, new object[] { false });
            return;
        }
        if (mode == 4)
        {
            // Invalid args short-circuit before ServiceHandle and native identity checks.
            try
            {
                typeof(CustodyService).GetMethod("OnStart", Hidden).Invoke(service,
                    new object[] { new[] { "synthetic-refuse-before-native-checks" } });
                Check(false);
            }
            catch (TargetInvocationException error) { Check(error.InnerException is InvalidOperationException); }
            return;
        }
        typeof(CustodyService).GetMethod(mode == 0 ? "OnStop" : "OnShutdown", Hidden).Invoke(service, null);
    }

    private static void ClosedOwner()
    {
        for (int mode = 0; mode < 4; mode++)
        using (var fixture = new Fixture(LifecycleState.ActiveDenied, true, false))
        {
            if (mode == 0) fixture.Owner.Stop();
            if (mode == 1) fixture.Owner.Shutdown();
            if (mode == 2) fixture.Owner.Fault();
            if (mode == 3) fixture.Owner.Dispose();
            SyntheticTransactionResult before = fixture.Owner.Observe();
            foreach (SyntheticTransactionRequest request in new[] { Request(fixture.Owner, 1, SyntheticOperation.Add), null })
            {
                SyntheticTransactionResult deny = fixture.Service.RefuseSyntheticRequest(request);
                SyntheticTransactionResult cancel = fixture.Service.CancelSyntheticRequest(request);
                Is(deny, TransactionDisposition.OwnerTerminated); Is(cancel, TransactionDisposition.OwnerTerminated);
                Check(deny.Owner == before.Owner && cancel.Owner == before.Owner &&
                    deny.Epoch == 2 && cancel.Epoch == 2 && deny.State == before.State && cancel.State == before.State);
            }
            Check((ulong)Field(typeof(SyntheticTransactionOwner), "highWater").GetValue(fixture.Owner) == 0);
        }
    }

    private static void Races()
    {
        for (int mode = 0; mode < 5; mode++)
        for (int round = 0; round < 12; round++)
        using (var fixture = new Fixture(LifecycleState.ActiveDenied, true, false))
        using (var start = new ManualResetEventSlim(false))
        {
            int closeMode = mode;
            SyntheticTransactionRequest request = Request(fixture.Owner, 1, SyntheticOperation.Add);
            SyntheticTransactionResult deny = null, cancel = null;
            Task a = Task.Run(delegate { Check(start.Wait(2000)); deny = fixture.Service.RefuseSyntheticRequest(request); });
            Task b = Task.Run(delegate { Check(start.Wait(2000)); cancel = fixture.Service.CancelSyntheticRequest(request); });
            Task c = Task.Run(delegate { Check(start.Wait(2000)); Close(fixture.Service, closeMode); });
            start.Set(); Join(new[] { a, b, c });
            Check(!deny.Allowed && !cancel.Allowed);
            Check(deny.Disposition == TransactionDisposition.Denied || deny.Disposition == TransactionDisposition.Replay ||
                deny.Disposition == TransactionDisposition.OwnerTerminated);
            Check(cancel.Disposition == TransactionDisposition.Cancelled || cancel.Disposition == TransactionDisposition.Replay ||
                cancel.Disposition == TransactionDisposition.OwnerTerminated);
            Check(!(deny.Disposition == TransactionDisposition.Denied && cancel.Disposition == TransactionDisposition.Cancelled));
            if (deny.Disposition == TransactionDisposition.OwnerTerminated) Inert(deny, request);
            else Check(deny.Owner == request.Owner && deny.Epoch == 1);
            if (cancel.Disposition == TransactionDisposition.OwnerTerminated) Inert(cancel, request);
            else Check(cancel.Owner == request.Owner && cancel.Epoch == 1);
            Inert(fixture.Service.RefuseSyntheticRequest(request), request);
            Inert(fixture.Service.CancelSyntheticRequest(null), null);
            Check(fixture.Owner.Observe().Epoch == 2);
        }

        for (int mode = 0; mode < 5; mode++)
        using (var fixture = new Fixture(LifecycleState.ActiveDenied, true, false))
        using (var arrived = new CountdownEvent(2))
        {
            SyntheticTransactionRequest request = Request(fixture.Owner, ulong.MaxValue, SyntheticOperation.Delete);
            Task a, b;
            // Force closure to win while contenders wait on the actual private lock.
            lock (fixture.Lifecycle)
            {
                a = Task.Run(delegate { arrived.Signal(); Inert(fixture.Service.RefuseSyntheticRequest(request), request); });
                b = Task.Run(delegate { arrived.Signal(); Inert(fixture.Service.CancelSyntheticRequest(request), request); });
                Check(arrived.Wait(2000));
                Close(fixture.Service, mode);
            }
            Join(new[] { a, b });
            Check((ulong)Field(typeof(SyntheticTransactionOwner), "highWater").GetValue(fixture.Owner) == 0);
            Check(fixture.Owner.Observe().Epoch == 2);
        }

        for (int round = 0; round < 12; round++)
        using (var fixture = new Fixture(LifecycleState.ActiveDenied, true, false))
        using (var start = new ManualResetEventSlim(false))
        {
            SyntheticTransactionRequest request = Request(fixture.Owner, 1, SyntheticOperation.Replace);
            int first = 0;
            Task[] contenders = new Task[12];
            for (int i = 0; i < contenders.Length; i++)
            {
                int index = i;
                contenders[i] = Task.Run(delegate {
                    Check(start.Wait(2000));
                    SyntheticTransactionResult result = index % 2 == 0 ? fixture.Service.RefuseSyntheticRequest(request) :
                        fixture.Service.CancelSyntheticRequest(request);
                    Check(!result.Allowed);
                    if (result.Disposition == TransactionDisposition.Denied || result.Disposition == TransactionDisposition.Cancelled)
                        Interlocked.Increment(ref first);
                    else Is(result, TransactionDisposition.Replay);
                });
            }
            start.Set(); Join(contenders); Check(first == 1);
            Join(new[] { Task.Run(delegate { Close(fixture.Service, 0); }), Task.Run(delegate { Close(fixture.Service, 1); }),
                Task.Run(delegate { fixture.Service.Dispose(); }), Task.Run(delegate { fixture.Service.Dispose(); }) });
            Check(fixture.Owner.Observe().Epoch == 2 && fixture.Owner.Observe().State == TransactionOwnerState.Disposed);
            Inert(fixture.Service.RefuseSyntheticRequest(request), request);
            Inert(fixture.Service.CancelSyntheticRequest(request), request);
        }
    }

    private static int Main(string[] args)
    {
        try
        {
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Check(args.Length == 1 && IntPtr.Size * 8 == int.Parse(args[0]));
            Check(typeof(CustodyService).Assembly != typeof(P307ServiceDenialTests).Assembly);
            Check(typeof(CustodyService).Assembly.Location == System.IO.Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory, "Nayeon.ByokC1.Service.exe"));
            foreach (string name in new[] { "RefuseSyntheticRequest", "CancelSyntheticRequest" })
            {
                MethodInfo method = typeof(CustodyService).GetMethod(name, Hidden, null,
                    new[] { typeof(SyntheticTransactionRequest) }, null);
                Check(method != null && method.IsAssembly && !method.IsStatic &&
                    method.DeclaringType == typeof(CustodyService) && method.ReturnType == typeof(SyntheticTransactionResult));
            }
            GateNegatives(); Sequential(); ClosedOwner(); Races();
            Console.WriteLine("P307 PASS checks=" + checks + " bits=" + IntPtr.Size * 8 +
                "; UNSTARTED synthetic fixtures only; no valid OS startup; HOLD");
            return 0;
        }
        catch (Exception error)
        { Console.Error.WriteLine("P307 FAIL " + error.GetType().Name + ": " + error.Message + "; HOLD"); return 1; }
    }
}
