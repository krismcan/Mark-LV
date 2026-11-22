using System;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Nayeon.ByokC1.Service;

internal static class P306ServiceTransactionTests
{
    private static int checks;
    private static void Check(bool value)
    { int n = Interlocked.Increment(ref checks); if (!value) throw new Exception("P306 assertion " + n); }

    private static SyntheticTransactionRequest Request(SyntheticTransactionOwner owner, ulong id, SyntheticOperation op)
    {
        SyntheticTransactionResult snapshot = owner.Observe();
        return new SyntheticTransactionRequest(snapshot.Owner, snapshot.Epoch, id, op);
    }
    private static void Is(SyntheticTransactionResult result, TransactionDisposition disposition)
    { Check(!result.Allowed && result.Disposition == disposition); }
    private static void Join(Task[] tasks) { Check(Task.WaitAll(tasks, 5000)); }

    private static void Sequential()
    {
        using (var owner = new SyntheticTransactionOwner())
        using (var other = new SyntheticTransactionOwner())
        {
            SyntheticTransactionResult original = owner.Observe();
            Check(original.Owner != Guid.Empty && original.Owner != other.Observe().Owner);
            Check(original.Epoch == 1 && original.State == TransactionOwnerState.ActiveDenied);
            Is(owner.Deny(null), TransactionDisposition.InvalidRequest);
            Is(owner.Cancel(null), TransactionDisposition.InvalidRequest);
            Is(owner.Deny(Request(owner, 0, SyntheticOperation.Add)), TransactionDisposition.InvalidRequest);
            foreach (int invalid in new[] { int.MinValue, -1, 0, 4, int.MaxValue })
            {
                Is(owner.Deny(Request(owner, 100, (SyntheticOperation)invalid)), TransactionDisposition.InvalidOperation);
                Is(owner.Cancel(Request(owner, 100, (SyntheticOperation)invalid)), TransactionDisposition.InvalidOperation);
            }
            Is(owner.Deny(Request(other, 100, SyntheticOperation.Add)), TransactionDisposition.WrongOwner);
            Is(owner.Deny(new SyntheticTransactionRequest(Guid.Empty, 1, 100, SyntheticOperation.Add)), TransactionDisposition.WrongOwner);
            foreach (long stale in new[] { long.MinValue, -1L, 0L, 2L, long.MaxValue })
                Is(owner.Deny(new SyntheticTransactionRequest(original.Owner, stale, 100, SyntheticOperation.Add)), TransactionDisposition.StaleEpoch);
            // Invalid metadata must not poison the valid owner's sequence.
            ulong id = 1;
            foreach (SyntheticOperation op in new[] { SyntheticOperation.Add, SyntheticOperation.Replace, SyntheticOperation.Delete })
            {
                SyntheticTransactionRequest request = Request(owner, id++, op);
                SyntheticTransactionResult denied = owner.Deny(request);
                Is(denied, TransactionDisposition.Denied); Check(object.ReferenceEquals(denied.Request, request));
                Is(owner.Cancel(request), TransactionDisposition.Replay);
                Is(owner.Deny(request), TransactionDisposition.Replay);
                request = Request(owner, id++, op);
                Is(owner.Cancel(request), TransactionDisposition.Cancelled);
                Is(owner.Deny(request), TransactionDisposition.Replay);
                Is(owner.Cancel(request), TransactionDisposition.Replay);
            }
            Is(owner.Deny(Request(owner, 100, SyntheticOperation.Add)), TransactionDisposition.Denied);
            Is(owner.Cancel(Request(owner, 99, SyntheticOperation.Delete)), TransactionDisposition.Replay);
            Is(owner.Deny(Request(owner, ulong.MaxValue, SyntheticOperation.Replace)), TransactionDisposition.Denied);
            Is(owner.Cancel(Request(owner, ulong.MaxValue, SyntheticOperation.Add)), TransactionDisposition.Replay);
            Is(owner.Deny(Request(owner, 1, SyntheticOperation.Delete)), TransactionDisposition.Replay);
            owner.Stop();
            Check(original.Epoch == 1 && original.State == TransactionOwnerState.ActiveDenied);
            Is(owner.Deny(null), TransactionDisposition.OwnerTerminated);
            Is(owner.Cancel(Request(owner, 1, (SyntheticOperation)0)), TransactionDisposition.OwnerTerminated);
            Check(owner.Observe().Epoch == 2 && owner.Observe().State == TransactionOwnerState.Stopped);
            owner.Fault(); owner.Shutdown(); owner.Stop();
            Check(owner.Observe().State == TransactionOwnerState.Stopped);
            owner.Dispose(); owner.Dispose(); owner.Stop(); owner.Fault(); owner.Shutdown();
            Check(owner.Observe().Epoch == 2 && owner.Observe().State == TransactionOwnerState.Disposed);
            // A new lifetime rejects all old identities, even though it begins at epoch 1.
            Is(other.Deny(new SyntheticTransactionRequest(original.Owner, 1, 1, SyntheticOperation.Add)), TransactionDisposition.WrongOwner);
            Is(other.Deny(Request(other, 1, SyntheticOperation.Add)), TransactionDisposition.Denied);
        }
    }

    private static void Terminal(SyntheticTransactionOwner owner, int mode)
    {
        if (mode == 0) owner.Stop();
        else if (mode == 1) owner.Shutdown();
        else if (mode == 2) owner.Fault();
        else owner.Dispose();
    }

    private static void Races()
    {
        for (int mode = 0; mode < 4; mode++)
        for (int round = 0; round < 40; round++)
        using (var owner = new SyntheticTransactionOwner())
        using (var start = new ManualResetEventSlim(false))
        {
            int terminalMode = mode;
            SyntheticTransactionRequest request = Request(owner, 1, SyntheticOperation.Add);
            SyntheticTransactionResult deny = null, cancel = null;
            Task a = Task.Run(delegate { Check(start.Wait(2000)); deny = owner.Deny(request); });
            Task b = Task.Run(delegate { Check(start.Wait(2000)); cancel = owner.Cancel(request); });
            Task c = Task.Run(delegate { Check(start.Wait(2000)); Terminal(owner, terminalMode); });
            start.Set(); Join(new[] { a, b, c });
            Check(!deny.Allowed && !cancel.Allowed);
            Check(deny.Disposition == TransactionDisposition.Denied || deny.Disposition == TransactionDisposition.Replay ||
                deny.Disposition == TransactionDisposition.OwnerTerminated);
            Check(cancel.Disposition == TransactionDisposition.Cancelled || cancel.Disposition == TransactionDisposition.Replay ||
                cancel.Disposition == TransactionDisposition.OwnerTerminated);
            Check(!(deny.Disposition == TransactionDisposition.Denied && cancel.Disposition == TransactionDisposition.Cancelled));
            Check(deny.Epoch == (deny.Disposition == TransactionDisposition.OwnerTerminated ? 2 : 1));
            Check(cancel.Epoch == (cancel.Disposition == TransactionDisposition.OwnerTerminated ? 2 : 1));
            Is(owner.Deny(request), TransactionDisposition.OwnerTerminated);
            Is(owner.Cancel(null), TransactionDisposition.OwnerTerminated);
            Check(owner.Observe().Epoch == 2);
        }

        for (int round = 0; round < 40; round++)
        using (var owner = new SyntheticTransactionOwner())
        using (var start = new ManualResetEventSlim(false))
        {
            SyntheticTransactionRequest request = Request(owner, 1, SyntheticOperation.Delete);
            int first = 0;
            Task[] contenders = new Task[12];
            for (int i = 0; i < contenders.Length; i++)
            {
                int index = i;
                contenders[i] = Task.Run(delegate {
                    Check(start.Wait(2000));
                    SyntheticTransactionResult result = index % 2 == 0 ? owner.Deny(request) : owner.Cancel(request);
                    Check(!result.Allowed);
                    if (result.Disposition == TransactionDisposition.Denied || result.Disposition == TransactionDisposition.Cancelled)
                        Interlocked.Increment(ref first);
                    else Is(result, TransactionDisposition.Replay);
                });
            }
            start.Set(); Join(contenders); Check(first == 1);
            // Concurrent terminal causes, including repeated disposal, cannot advance twice.
            Join(new[] { Task.Run(delegate { owner.Stop(); }), Task.Run(delegate { owner.Shutdown(); }),
                Task.Run(delegate { owner.Fault(); }), Task.Run(delegate { owner.Dispose(); }),
                Task.Run(delegate { owner.Dispose(); }) });
            Check(owner.Observe().State == TransactionOwnerState.Disposed && owner.Observe().Epoch == 2);
        }

        // Invalid-operation floods race fresh valid identities and closure; all remain denials.
        using (var owner = new SyntheticTransactionOwner())
        {
            Join(new[] {
                Task.Run(delegate { for (ulong i = 1; i <= 2000; i++) {
                    SyntheticTransactionResult r = owner.Deny(Request(owner, i, SyntheticOperation.Replace));
                    Check(!r.Allowed && (r.Disposition == TransactionDisposition.Denied || r.Disposition == TransactionDisposition.OwnerTerminated));
                } }),
                Task.Run(delegate { for (ulong i = 1; i <= 2000; i++) {
                    SyntheticTransactionResult r = owner.Cancel(Request(owner, ulong.MaxValue, (SyntheticOperation)4));
                    Check(!r.Allowed && (r.Disposition == TransactionDisposition.InvalidOperation || r.Disposition == TransactionDisposition.OwnerTerminated));
                } }),
                Task.Run(delegate { owner.Dispose(); }) });
            Check(owner.Observe().Epoch == 2);
        }
    }

    private static void HostClosure()
    {
        Type host = typeof(CustodyService);
        FieldInfo field = host.GetField("transactions", BindingFlags.Instance | BindingFlags.NonPublic);
        Check(field != null && field.IsPrivate && field.FieldType == typeof(SyntheticTransactionOwner));
        // Test-only reflection places an effect-free owner into an UNSTARTED ServiceBase.
        // Never call SCM/valid OnStart or bypass identity to operate a service.
        for (int mode = 0; mode < 5; mode++)
        {
            var service = (CustodyService)Activator.CreateInstance(host, true);
            Check(field.GetValue(service) == null); // No pre-identity composition.
            var owner = new SyntheticTransactionOwner();
            field.SetValue(service, owner);
            try
            {
                if (mode == 3)
                {
                    try
                    {
                        host.GetMethod("OnStart", BindingFlags.Instance | BindingFlags.NonPublic)
                            .Invoke(service, new object[] { new[] { "refuse-before-native-checks" } });
                        Check(false);
                    }
                    catch (TargetInvocationException error) { Check(error.InnerException is InvalidOperationException); }
                    Check(owner.Observe().State == TransactionOwnerState.Faulted);
                }
                else if (mode == 2) service.Dispose();
                else if (mode == 4) host.GetMethod("Dispose", BindingFlags.Instance | BindingFlags.NonPublic,
                    null, new[] { typeof(bool) }, null).Invoke(service, new object[] { false });
                else host.GetMethod(mode == 0 ? "OnStop" : "OnShutdown", BindingFlags.Instance | BindingFlags.NonPublic)
                    .Invoke(service, null);
                Check(owner.Observe().Epoch == 2);
                if (mode == 4) Check(owner.Observe().State == TransactionOwnerState.Disposed);
                if (mode < 3) Check(owner.Observe().State == (mode == 0 ? TransactionOwnerState.Stopped :
                    mode == 1 ? TransactionOwnerState.Shutdown : TransactionOwnerState.Disposed));
                Is(owner.Deny(Request(owner, 1, SyntheticOperation.Add)), TransactionDisposition.OwnerTerminated);
            }
            finally { service.Dispose(); }
            Check(owner.Observe().State == TransactionOwnerState.Disposed && owner.Observe().Epoch == 2);
        }
    }

    private static int Main(string[] args)
    {
        try
        {
            Check(Environment.OSVersion.Platform == PlatformID.Win32NT);
            Check(args.Length == 1 && IntPtr.Size * 8 == int.Parse(args[0]));
            Check(typeof(SyntheticTransactionOwner).Assembly != typeof(P306ServiceTransactionTests).Assembly);
            Check(typeof(SyntheticTransactionOwner).Assembly.Location == System.IO.Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory, "Nayeon.ByokC1.Service.exe"));
            foreach (FieldInfo field in typeof(SyntheticTransactionRequest).GetFields(BindingFlags.Instance | BindingFlags.NonPublic))
                Check(field.IsInitOnly && (field.FieldType == typeof(Guid) || field.FieldType == typeof(long) ||
                    field.FieldType == typeof(ulong) || field.FieldType == typeof(SyntheticOperation)));
            Sequential(); Races(); HostClosure();
            Console.WriteLine("P306 PASS checks=" + checks + " bits=" + IntPtr.Size * 8 + "; synthetic denial only; HOLD");
            return 0;
        }
        catch (Exception error)
        { Console.Error.WriteLine("P306 FAIL " + error.GetType().Name + ": " + error.Message + "; HOLD"); return 1; }
    }
}
