#if !C1_P264_DEVELOPMENT_ONLY
#error P264_TESTS_REQUIRE_DEVELOPMENT_BUILD
#endif
#if !DEBUG
#error P264_TESTS_NO_RELEASE_BUILD
#endif
// Review harness only. Never invokes ServiceBase.Run or installs/controls a service.
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.InteropServices;
using System.ServiceProcess;
using System.Threading;

internal static class P264DevelopmentServiceTests
{
    private const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
    private static Type serviceType;
    private static int assertions;

    private static void Need(bool condition)
    {
        assertions++;
        if (!condition) throw new InvalidOperationException("P264_TEST_FAILED");
    }

    private static object Call(object service, string method, params object[] arguments)
    { return serviceType.GetMethod(method, Hidden).Invoke(service, arguments); }

    private static string Field(object receipt, string name)
    { return receipt.GetType().GetField(name, Hidden).GetValue(receipt).ToString(); }

    private static bool Flag(object receipt, string name)
    { return (bool)receipt.GetType().GetField(name, Hidden).GetValue(receipt); }

    private static void Denied(object receipt, string reason)
    {
        Need(Field(receipt, "Reason") == reason);
        foreach (string property in new[] { "CredentialAllowed", "IpcAllowed", "StoreAllowed", "ProductionEligible" })
            Need(!(bool)receipt.GetType().GetProperty(property, Hidden).GetValue(receipt, null));
    }

    private static object NewService()
    { return Activator.CreateInstance(serviceType, true); }

    private static void Start(object service) { Call(service, "OnStart", new object[] { new string[0] }); }
    private static void Close(object service) { ((IDisposable)service).Dispose(); }

    private static void RefusedStart(object service, string reason)
    {
        try { Start(service); Need(false); }
        catch (TargetInvocationException error) { Need(error.InnerException is InvalidOperationException); }
        Denied(Call(service, "ObserveDenial"), reason);
    }

    private static void LifecycleTests()
    {
        object service = NewService();
        try
        {
            var windowsService = (ServiceBase)service;
            Need(windowsService.ServiceName == "NayeonV1ByokCustody");
            Need(windowsService.CanStop && windowsService.CanShutdown && !windowsService.CanPauseAndContinue);
            Need(!windowsService.AutoLog);
            foreach (string method in new[] { "RejectCredential", "RejectIpc", "RejectStore" })
                Denied(Call(service, method), "NotStarted");
            Start(service);
            Need(Field(Call(service, "ObserveDenial"), "State") == "RunningDenied");
            foreach (string method in new[] { "RejectCredential", "RejectIpc", "RejectStore" })
                Denied(Call(service, method), "DevelopmentHold");
            foreach (int command in new[] { 0, 1, 128, 255, Int32.MaxValue })
            {
                Call(service, "OnCustomCommand", command);
                Denied(Call(service, "ObserveDenial"), "DevelopmentHold");
            }
            Denied(Call(service, "Revoke"), "Revoked");
            Denied(Call(service, "Revoke"), "Revoked");
            Need(Flag(Call(service, "ObserveDenial"), "RevokeRecorded"));
            Call(service, "OnStop"); Call(service, "OnStop"); Call(service, "OnShutdown");
            object stopped = Call(service, "ObserveDenial");
            Denied(stopped, "Stopped"); Need(Flag(stopped, "StopRecorded") && Flag(stopped, "RevokeRecorded"));
            Denied(Call(service, "Fault"), "Faulted");
            Denied(Call(service, "Fault"), "Faulted");
            Call(service, "OnStop");
            Need(Flag(Call(service, "ObserveDenial"), "FaultRecorded"));
            RefusedStart(service, "Faulted");
        }
        finally { Close(service); }
        Close(service);
        Denied(Call(service, "RejectStore"), "Disposed");
        Need(Flag(Call(service, "ObserveDenial"), "FaultRecorded"));
        RefusedStart(service, "Disposed");

        // Stop/revoke/fault/dispose before Start never creates a running lifetime.
        foreach (string method in new[] { "OnStop", "Revoke", "Fault", "Dispose" })
        {
            object stale = NewService();
            try
            {
                if (method == "Dispose") Close(stale); else Call(stale, method);
                RefusedStart(stale, method == "Dispose" ? "Disposed" : "Faulted");
            }
            finally { Close(stale); }
        }
        object duplicate = NewService();
        try { Start(duplicate); RefusedStart(duplicate, "Faulted"); }
        finally { Close(duplicate); }
        object fresh = NewService();
        try { Denied(Call(fresh, "RejectCredential"), "NotStarted"); Start(fresh); Denied(Call(fresh, "RejectStore"), "DevelopmentHold"); }
        finally { Close(fresh); }
    }

    private static void OrderedPair(string terminal, string expected, string admission, bool terminalFirst)
    {
        object service = NewService();
        Start(service);
        using (var firstDone = new ManualResetEvent(false))
        {
            Exception firstError = null, secondError = null;
            ThreadStart close = delegate { if (terminal == "Dispose") Close(service); else Call(service, terminal); };
            ThreadStart reject = delegate { Denied(Call(service, admission), terminalFirst ? expected : "DevelopmentHold"); };
            var first = new Thread(delegate()
            {
                try { if (terminalFirst) close(); else reject(); }
                catch (Exception error) { firstError = error; }
                finally { firstDone.Set(); }
            });
            var second = new Thread(delegate()
            {
                try
                {
                    if (!firstDone.WaitOne(3000)) throw new InvalidOperationException("P264_ORDER_TIMEOUT");
                    if (terminalFirst) reject(); else close();
                }
                catch (Exception error) { secondError = error; }
            });
            first.IsBackground = true; second.IsBackground = true;
            try
            {
                second.Start(); first.Start();
                bool firstJoined = first.Join(5000), secondJoined = second.Join(5000);
                Need(firstJoined && secondJoined && firstError == null && secondError == null);
                Denied(Call(service, admission), expected);
            }
            finally { Close(service); }
        }
    }

    private static void ReentrantTests()
    {
        object service = NewService();
        Start(service);
        object owner = serviceType.GetField("owner", Hidden).GetValue(service);
        object sync = owner.GetType().GetField("sync", Hidden).GetValue(owner);
        try
        {
            // Adversarial reflection is confined to this harness, not an owner hook.
            lock (sync) { Denied(Call(service, "Revoke"), "Reentrant"); }
            object receipt = Call(service, "ObserveDenial");
            Denied(receipt, "Faulted");
            Need(!Flag(receipt, "RevokeRecorded") && Flag(receipt, "FaultRecorded"));
            RefusedStart(service, "Faulted");
        }
        finally { Close(service); }
    }

    private static void ContendedLifecycleTests()
    {
        string[] methods = { "OnStop", "Revoke", "Fault" };
        string[] reasons = { "Stopped", "Revoked", "Faulted" };
        for (int index = 0; index < methods.Length; index++)
        {
            object service = NewService();
            Start(service);
            object owner = serviceType.GetField("owner", Hidden).GetValue(service);
            object sync = owner.GetType().GetField("sync", Hidden).GetValue(owner);
            using (var attempted = new ManualResetEvent(false))
            using (var finished = new ManualResetEvent(false))
            {
                Exception failure = null;
                string method = methods[index];
                var worker = new Thread(delegate()
                {
                    attempted.Set();
                    try { Call(service, method); }
                    catch (Exception error) { failure = error; }
                    finally { finished.Set(); }
                });
                worker.IsBackground = true;
                try
                {
                    lock (sync)
                    {
                        worker.Start();
                        Need(attempted.WaitOne(3000));
                        Need(!finished.WaitOne(100));
                        foreach (string flag in new[] { "stopped", "revoked", "faulted", "disposed" })
                            Need(!(bool)owner.GetType().GetField(flag, Hidden).GetValue(owner));
                    }
                    Need(worker.Join(3000) && failure == null);
                    Denied(Call(service, "ObserveDenial"), reasons[index]);
                }
                finally { Close(service); }
            }
        }
    }

    private static void AuditAssembly(Assembly candidate)
    {
        MethodInfo entry = candidate.EntryPoint;
        Need(entry != null && entry.DeclaringType == serviceType && entry.Name == "Main" && entry.ReturnType == typeof(int));
        var codes = new Dictionary<ushort, OpCode>();
        foreach (FieldInfo field in typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static))
            if (field.FieldType == typeof(OpCode))
            { OpCode code = (OpCode)field.GetValue(null); codes[unchecked((ushort)code.Value)] = code; }
        int runCalls = 0;
        foreach (AssemblyName reference in candidate.GetReferencedAssemblies())
            Need(reference.Name == "mscorlib" || reference.Name == "System" || reference.Name == "System.ServiceProcess");
        foreach (Type type in candidate.GetTypes())
        {
            var methods = new List<MethodBase>(type.GetMethods(BindingFlags.DeclaredOnly | Hidden | BindingFlags.Public | BindingFlags.Static));
            methods.AddRange(type.GetConstructors(BindingFlags.DeclaredOnly | Hidden | BindingFlags.Public | BindingFlags.Static));
            foreach (MethodBase method in methods)
            {
                Need((method.Attributes & MethodAttributes.PinvokeImpl) == 0);
                Need(!method.IsDefined(typeof(DllImportAttribute), false));
                Need((method.GetMethodImplementationFlags() & (MethodImplAttributes.CodeTypeMask |
                    MethodImplAttributes.ManagedMask | MethodImplAttributes.InternalCall)) == MethodImplAttributes.IL);
                MethodBody body = method.GetMethodBody();
                Need(body != null);
                byte[] il = body.GetILAsByteArray();
                for (int cursor = 0; cursor < il.Length; )
                {
                    ushort key = il[cursor++];
                    if (key == 0xfe) key = (ushort)(0xfe00 | il[cursor++]);
                    OpCode code = codes[key];
                    Need(code != OpCodes.Calli);
                    int size;
                    switch (code.OperandType)
                    {
                        case OperandType.InlineNone: size = 0; break;
                        case OperandType.ShortInlineBrTarget: case OperandType.ShortInlineI: case OperandType.ShortInlineVar: size = 1; break;
                        case OperandType.InlineVar: size = 2; break;
                        case OperandType.InlineI8: case OperandType.InlineR: size = 8; break;
                        case OperandType.InlineSwitch: size = 4 + 4 * BitConverter.ToInt32(il, cursor); break;
                        default: size = 4; break;
                    }
                    if (code.OperandType == OperandType.InlineMethod)
                    {
                        MethodBase called = candidate.ManifestModule.ResolveMethod(BitConverter.ToInt32(il, cursor));
                        Type declaring = called.DeclaringType;
                        if (declaring.Assembly != candidate)
                        {
                            string name = declaring.FullName;
                            Need(name == "System.Object" || name == "System.String" ||
                                name == "System.Threading.Monitor" || name.StartsWith("System.Nullable`1", StringComparison.Ordinal) ||
                                name == "System.InvalidOperationException" || name == "System.IDisposable" ||
                                name == "System.ServiceProcess.ServiceBase");
                            if (declaring == typeof(ServiceBase))
                            {
                                Need(called.Name == ".ctor" || called.Name == "Run" || called.Name == "Dispose" ||
                                    called.Name == "set_ServiceName" || called.Name == "set_CanStop" ||
                                    called.Name == "set_CanShutdown" || called.Name == "set_CanPauseAndContinue" || called.Name == "set_AutoLog");
                                if (called.Name == "Run") { Need(method == entry); runCalls++; }
                            }
                        }
                    }
                    cursor += size;
                }
            }
        }
        Need(runCalls == 1);
        // Audit all declared IL before executing ANY candidate method. Invalid/default
        // command lines must return before service construction/Run; never test opt-in.
        foreach (string[] arguments in new[] { null, new string[0], new[] { "--production" },
            new[] { "--development-only-no-effects", "extra" }, new[] { "--DEVELOPMENT-ONLY-NO-EFFECTS" } })
            Need((int)entry.Invoke(null, new object[] { arguments }) == 64);
    }

    private static int Main(string[] arguments)
    {
        if (arguments.Length != 1) return 64;
        // Only an unblocked, locally review-built candidate may be supplied. Stop
        // on policy refusal; this is never an alternate loader for a blocked image.
        Assembly candidate = Assembly.LoadFrom(arguments[0]);
        serviceType = candidate.GetType("Nayeon.ByokC1.P264Development.DevelopmentCustodyService", true);
        AuditAssembly(candidate);
        LifecycleTests();
        string[] terminals = { "OnStop", "Revoke", "Fault", "Dispose" };
        string[] reasons = { "Stopped", "Revoked", "Faulted", "Disposed" };
        for (int index = 0; index < terminals.Length; index++)
            foreach (string admission in new[] { "RejectCredential", "RejectIpc", "RejectStore" })
                foreach (bool first in new[] { true, false })
                    OrderedPair(terminals[index], reasons[index], admission, first);
        ReentrantTests();
        ContendedLifecycleTests();
        Console.WriteLine("P264_DEVELOPMENT_TESTS=PASS ASSERTIONS=" + assertions);
        Console.WriteLine("P264_BITS=" + (IntPtr.Size * 8));
        Console.WriteLine("P264_REAL_KEY=HOLD PRODUCTION=HOLD SCM_EXECUTION=NOT_TESTED");
        return 0;
    }
}
